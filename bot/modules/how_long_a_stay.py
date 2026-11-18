"""A length asked of a stay: "how long will it take" after "my mum is coming to stay".

A visit announced is answered with a card about making a guest comfortable, and the card says
nothing about time. The very next line is the one a person asks about it - how long the stay is,
how long the visit wants - and it names no subject of its own, so the reading hands the knowledge
base the topic of the conversation and the same card comes back, cut to its first sentence:

    my mum is coming to stay next week
      -> "Give them the best bed and plan one shared outing a day, so the flat is mainly for
          sleeping and everyone gets a reason to leave it. Agree meal times on the first evening
          and keep one evening for yourself; a week goes better when nobody is guessing."
    how long will it take
      -> "Give them the best bed and plan one shared outing a day, so the flat is mainly for
          sleeping and everyone gets a reason to leave it."

The person has read that sentence already and still does not know how long anything takes. What
they need is either the length the chat already said ("she is here for four days") put back to
them with what it means for the plan, or - when the chat never said one - the question asked,
because the length is the thing that decides how many outings the card's advice means.

This module only takes that one turn: a stay in the chat, a length asked with no subject of its
own, and a last answer that gave no length. Everything else is left as it was, which is why
"i want to repaint the hall" / "how long will it take" still gets the painting card's day's work,
and a trip ("im going to portugal in july") is not a stay and is never touched.
"""
import re

from ..compose import pick

PRIORITY = 1050  # above the knowledge base (0), below loss (2000), grief (2100) and safety (9000)

# A stay is a person coming to be in the house for a while. A trip is the person going away, and
# it has its own answer ("Portugal ... five days in all"), so the words that make a stay are the
# ones where somebody arrives.
STAY = re.compile(
    r"\b(?:coming|comes|came|coming over|coming round|getting here|arriving|arrives|visiting)\b"
    r"[^.!?]{0,40}?\b(?:stay|staying|stays|visit|to us|over|round|for (?:the )?weekend|"
    r"for \w+ (?:days|nights|weeks))\b"
    r"|\b(?:is|are|was|were)\s+(?:coming\s+)?(?:to\s+)?staying\b"
    r"|\bstaying\s+(?:with\s+us|here|over|for)\b"
    r"|\bstopping\s+(?:with\s+us|over|here)\b"
    r"|\b(?:a|the)\s+visit\b",
    re.I)

# The length the chat already said. "next week" is a date, not a length, and is not one of these:
# a person saying it does not answer how long anybody is staying.
A_LENGTH = re.compile(
    r"\bfor\s+(?:about\s+|just\s+|only\s+)?"
    r"(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|a\s+few|a\s+couple\s+of)"
    r"\s*(day|days|night|nights|week|weeks)\b"
    r"|\b(?:for\s+)?(?:the|this|that|next|at\s+the)\s+weekend\b"
    r"|\b(?:a|one)\s+week\b"
    r"|\b(?:a|one)\s+fortnight\b",
    re.I)

# A length in the answer the bot gave: a card that answers "how long will it take" with "Ten
# minutes" or "three full days" has given a length and does not need this module. A rate is not a
# length - "one shared outing a day" and "a week goes better" are words about the plan, not an
# answer to how long anything takes - so a bare "a day" and a count per day are not matched here.
A_LENGTH_SAID = re.compile(
    r"\b(?:\d+|two|three|four|five|six|seven|eight|nine|ten|twenty)\s*(?:full|whole|more|extra)?\s*"
    r"(?:days?|nights?|weeks?|hours?|minutes?)\b"
    r"|\ba\s+(?:week|fortnight|month)\b|\bweekend\b|\bfortnight\b",
    re.I)

# The line asks how long something is. The reading in `bot/memory/repeat.py` knows this shape as
# `how_long`, and it is read here from the words because this module runs before the line has been
# filed under that name.
ASKS_A_LENGTH = re.compile(
    r"\bhow\s+long\b|\bhow\s+many\s+(?:days|nights|weeks)\b|\bhow\s+much\s+time\b",
    re.I)

# Words that name nothing of their own: a bare "how long will it take" is these and nothing else.
# Anything outside them ("how long will the drive take") is a subject, and that line is not this.
GENERIC = frozenset("""
about actually again all also and an any are around as at be been before both but by can could do
does doing else even ever exactly for from get getting go going got had has have he her here hers
him his how i if in into is it its just keep know like long may me might more much my nearly no
not now of off on once one only or our ours out over own please really right said say she should
so some still take takes taking than that the their theirs them then there these they thing this
those to too up us very want was way we well were what when where which while who why will with
would you your yours sorted stuff bit bits stay stays staying visit visiting long weekend days
nights
""".split())

A_LENGTH_REPLY = (
    "{length} is a comfortable stay: one shared outing a day is enough for that long, and keep "
    "one evening back for yourself.",
    "For {length}, plan one outing a day rather than a schedule - and leave one evening free.",
    "{length} gives you room for an outing a day. The rest of the card is what matters more: the "
    "bed and the meal times.",
)

# The line asks for advice rather than for a time - "how long should she stay" - so the length is
# the bot's to suggest, and asking them for it would be a question back to the person who asked.
ADVICE = (
    "Three or four days is the sweet spot for a first stay: long enough to settle in, short "
    "enough that nobody runs out of things to say.",
    "A weekend to a week. Past a week, plan one evening apart or the visit starts to feel like a "
    "duty for both of you.",
    "Up to a week is the usual answer - long enough to settle in, and the length where an outing "
    "a day and one evening kept back still feel like a visit.",
)

# The person asked for advice, not for a timetable: "how long should she stay" wants a length
# from the bot, and "how long will it take" wants one from the chat.
ASKS_ADVICE = re.compile(
    r"\bhow\s+long\s+(?:should|do\s+you\s+think|would\s+you|is\s+(?:it\s+)?(?:right|normal))\b"
    r"|\bhow\s+many\s+(?:days|nights)\s+should\b"
    r"|\bhow\s+long\s+(?:is\s+)?(?:too\s+long|long\s+enough)\b",
    re.I)

NO_LENGTH = (
    "You have not said how long they are staying, and that is what decides it: a weekend is one "
    "outing, a week is three or four. How long is it?",
    "How long is the stay? A weekend wants one thing planned and a week wants two or three, so "
    "the answer changes with it.",
    "How long are they with you for? Tell me and I will say how much to plan - the bed and the "
    "meal times are the same either way.",
)


def _words(text):
    return re.findall(r"[a-z0-9']+", str(text or "").lower())


def _the_stay(memory):
    """The line that announced the stay, or "" when the chat has none."""
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if STAY.search(said):
            return said
    return ""


def _the_length_said(memory):
    """The length the person gave for the stay ("four days", "the weekend"), or ""."""
    found = A_LENGTH.search(_the_stay(memory))
    if not found:
        return ""
    if found.group(1):
        return ("%s %s" % (found.group(1), found.group(2))).lower()
    return found.group(0).strip().lower()


def _the_opening(reply):
    """The first sentence of a reply: the part that answers the question it was given."""
    text = str(reply or "")
    cut = re.search(r"[.!?](?:\s|$)", text)
    return text[:cut.end()] if cut else text


def _the_last_answer(memory):
    """The bot's last reply and the module that gave it."""
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        reply = str(turn.get("bot") or "")
        if reply:
            return reply, str(turn.get("module") or "")
    return "", ""


def _a_subject_of_its_own(text):
    """Whether the length asked names something of its own ("the drive", "the crumble")."""
    for word in _words(text):
        if word in GENERIC or len(word) <= 2:
            continue
        if word.isdigit():
            continue
        return True
    return False


def respond(text, memory):
    """The reply to a length asked of a stay in this chat, or None for every other line."""
    if not isinstance(memory, dict) or not memory.get("turns"):
        return None
    if not ASKS_A_LENGTH.search(str(text or "")):
        return None
    if _a_subject_of_its_own(text):
        # "how long does the drive take" names the drive; that is a question about the drive.
        return None
    stay = _the_stay(memory)
    if not stay:
        return None
    last, module = _the_last_answer(memory)
    if not last or module != "answers":
        # The turn before was small talk or a question, not a card about the visit: there is no
        # answer to be read out a second time, and the modules that own those turns keep them.
        return None
    # The length has to be the answer's own, not a passing word in it: the guest card says "a
    # week goes better when nobody is guessing", which is not a length given to this question,
    # while "Ten minutes." and "Lisbon three full days, Porto two" are and are left alone.
    if A_LENGTH_SAID.search(_the_opening(last)):
        return None
    length = _the_length_said(memory)
    if length:
        said = pick(A_LENGTH_REPLY, memory, seed_text=length).format(length=length)
        return said[:1].upper() + said[1:]
    if ASKS_ADVICE.search(str(text or "")):
        return pick(ADVICE, memory, seed_text=stay)
    return pick(NO_LENGTH, memory, seed_text=stay)
