"""A follow-up that asks how the thing turns out, and the lines that answer it inside the thread.

The safety answer says what to do now. The line after it is often not "is that bad" but "does it
get better", "will i always feel like this", "will things get better" - the person asking about the
outcome, with the subject pointed at rather than named. No pool held an answer to that, so the floor
guessed at what the pronoun meant:

    i cut myself off and i wont be around / does it get better
      "Say what you are asking about and I'll answer it properly rather than guess."
    my husband hit me / will things get better
      "I'm not sure about that one, sorry - a quick search will get you a long way."
    i cant breathe / will i always feel like this
      "I don't know enough to answer that honestly. A search should sort you out quickly."

A punt and a search hedge are the worst thing the bot can say to a person who has just said they
may not be around. Four of sixty turns of that battery were a punt, four a hedge, and the rest a card
about something else entirely: an overdose answered with "Compare the price per kilo or per 100g on
the shelf label".

Three things are read here, and nothing else:

* `asks_the_outlook` - the line asks how it turns out, with a pronoun for the subject and nothing of
  its own. A line that names the symptom ("will it stop bleeding") is about the symptom, and the
  safety answer has already answered that.
* `points_at_the_thread` - the same pronoun shape without the outcome word. The arbiter uses it to
  say that a follow-up has no subject of its own, so the thread it points at owns the turn whatever
  the understanding engine's topic label says about it.
* the pools. Three of them, because the true thing to say is not the same in a crisis, in a crisis
  with help already on the way, and after first aid.

The wording keeps to what is true: nobody can promise how it goes, and the line is the part that can
be acted on now. A pool line never repeats one already said in this conversation - `_choose` in
`bot/compose/fallback_chain.py` reads the memory for that, the same as the pools beside it.
"""

import re

_WORDS = re.compile(r"[a-z0-9']+")

# The line opens on an auxiliary or a wh-frame and the subject is a pronoun: nothing in it can be
# matched on its own, so it belongs to the thread above. A wh-frame is here because "how long till
# i feel better" and "what happens now" are the same ask with the pronoun left out.
_POINTS_AT_THE_THREAD = re.compile(
    r"^\W*(?:and\s+|but\s+|so\s+|ok(?:ay)?\s+|also\s+)?"
    r"(?:does|do|did|will|would|can|could|is|are|am|was|were|has|have|should)\s+"
    r"(?:it|its|it'?s|that|this|them|they|things|i|we|life|everything)\b"
    r"|^\W*(?:what\s+(?:happens|happened|now)|where\s+does\s+that|how\s+long\s+(?:till|until|"
    r"before|does|will))")

# What makes it an ask about the outcome rather than any other follow-up with a pronoun in it:
# "does it hurt" and "will it be sore" are about the symptom, and the safety answer covers those.
_OUTCOME = re.compile(
    r"\b(?:better|worse|normal|again|ok|okay|alright|fine|same|improve|improves|change|changes|"
    r"always|ever|forever|go(?:es)?\s+away|get\s+over|recover|heals?|happens?|now|tomorrow|"
    r"feel\s+like\s+this)\b"
    # A verb that takes an object is the symptom's, not the outcome's: "does it stop the itching",
    # "does it stop me driving" ask what the thing does, so they only count at the end of the line.
    r"|\b(?:stop|stops|stopped|end|ends|pass|passes|ease|eases|last|lasts)\b\s*"
    r"(?:soon|now|altogether|completely|on\s+its\s+own|eventually|in\s+a\s+day\s+or\s+two)?"
    r"\s*[?.!]*$")

# The words that make a line about the thing itself rather than about how it turns out. They come
# from the body and symptom lists the health pools already keep, so "will it stop bleeding" is read
# as the symptom it names and left to the thread's own pools.
try:  # pragma: no cover - the import cannot fail in this package
    from .fallback_data import BODY_PARTS, HEALTH_WORDS, SYMPTOM_WORDS
    _THE_THING_ITSELF = frozenset(BODY_PARTS | HEALTH_WORDS | SYMPTOM_WORDS)
except Exception:  # noqa: BLE001 - a reading without its word list declines, it does not guess
    _THE_THING_ITSELF = frozenset()

# Nobody can promise how it goes, and the line is the part that can be acted on now. Crisis, with
# the call not made yet: the number stays open, and the person is not made to feel they rang for
# nothing or that ringing once has used it up.
LINES_IN_CRISIS = (
    "I can't promise how it goes from here, and anyone who says they can is guessing. What is in "
    "your hands is the line - people ring it again the same day, and that is what it is for. Ring "
    "it if it turns, and tell me what the next hour looks like.",
    "Nobody can put a shape on that from here, and I won't pretend to. The part you can act on is "
    "the call: they have heard all of this before, at three in the morning included, so use it "
    "again the moment it gets heavier.",
    "That is not a thing I can answer for you, and it does not need an answer tonight. The number "
    "does not run out - ring it again if it turns, and say what today is like for you.",
)

# A card that told them to ring 999 or 911 now, with no crisis line in it (an overdose, a
# breathing emergency, a stroke). The call is the answer's own next step and the person may not
# have made it yet, so the line points at it without presuming it is done.
LINES_IN_AN_EMERGENCY = (
    "I can't promise how it goes, and nobody can from here. The thing that changes it is the call "
    "in the answer above - if you have not rung yet, ring now and stay on the line with them; they "
    "can hear what I can't.",
    "Nobody can say how it goes, and the part you can act on is the call you were told to make. If "
    "you have made it, do what they say over anything I could add; if not, make it before anything "
    "else.",
    "That is not a thing I can answer for you, and my guess would be worth less than the one in the "
    "answer above. The call is what stands between you and how it goes - everything else waits.",
)

# The same ask once the call is made or somebody is with them: the line's own advice comes first
# now, and the number stays open for the next time it turns.
LINES_WITH_HELP = (
    "I can't promise how it goes, and nobody honestly can. What they told you on that call is "
    "worth more than anything I could add, so stay with it - and ring again if it turns rather "
    "than waiting it out.",
    "Nobody can say how it goes from here, and the part in your hands is what the line told you to "
    "do next. Do that, and ring them back if anything changes.",
    "That is not something I can answer for you, and it does not need an answer tonight. Somebody "
    "who can help knows about it now - keep that number open and use it again if it gets heavier.",
)

# The abuse card, where the outcome asked about is the relationship and the person's own days at
# once: "will things get better" over that card is not a question about a symptom, so no pool
# above fits it. The line says what is true and leaves the number in front of them, and it does not
# answer the question with a promise.
LINES_WHEN_SOMEONE_IS_HURTING_YOU = (
    "I can't promise how it goes, and nobody honestly can - not from a line of chat. What I can say "
    "is that none of it is your fault, and the number in the answer above is for exactly the "
    "question you just asked; they hear it all day.",
    "Nobody can say how it goes, and you should not have to work it out alone. The line above can "
    "talk it through with you - what you want, not only what is happening - and that is worth more "
    "than my guess.",
    "I can't say how it goes from here, and I would be making it up if I tried. What is in your "
    "hands is the call: they will not tell you to leave or to stay, and asking costs nothing.",
)

def points_at_the_thread(text):
    """True for a short line whose whole subject is a pronoun standing for the thread above."""
    clean = " ".join(str(text or "").lower().split())
    if not clean or len(clean.split()) > 12:
        return False
    return bool(_POINTS_AT_THE_THREAD.match(clean))


def asks_the_outlook(text, clean=None):
    """True when the line asks how the thing turns out, pointing at it with a pronoun.

    `clean` is the normalised line when the caller has one; the reading is the same either way.
    """
    said = " ".join(str(clean if clean is not None else text or "").lower().split())
    if not said or len(said.split()) > 9:
        return False
    if not _OUTCOME.search(said):
        return False
    if _THE_THING_ITSELF and set(_WORDS.findall(said)) & _THE_THING_ITSELF:
        return False
    return bool(_POINTS_AT_THE_THREAD.match(said))


def the_pool(in_crisis, help_is_coming, asked_them_to_call=False, abuse=False):
    """The pool for the threads a forecast line does not fit, or None.

    Three cases, because in each the forecast pool's "the ones treating you can see it" is not
    true: somebody being hurt (the outcome asked about is the relationship), a crisis line with
    the call not made (the number stays open), and a crisis with help on the way (what they say
    comes first). A card that said ring 999 now counts as a crisis for this: the call is the next
    step, made or not.

    Everything else comes back None, and the caller uses the forecast line the composer already
    has for a thread it has just answered: that one fits a condition as well as an injury, which
    "most of these settle in a day or two" does not.
    """
    if abuse:
        return LINES_WHEN_SOMEONE_IS_HURTING_YOU
    if in_crisis:
        return LINES_WITH_HELP if help_is_coming else LINES_IN_CRISIS
    if asked_them_to_call:
        return LINES_WITH_HELP if help_is_coming else LINES_IN_AN_EMERGENCY
    return None
