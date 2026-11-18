"""A bare doubt said on top of a safety answer is about the emergency itself.

The safety card is the bot's own answer, and a bare verdict ask after it ("is that bad") is the
person checking that the thing is as serious as it sounded. Three different voices answered that
instead, each of them written for a different thread:

    i cant breathe / is that bad       "It is worth having it seen to, and that answer already
                                        said by whom. Get that booked" - an ambulance turned into
                                        a clinic appointment
    i hit my wife / is that bad        "Keep an eye on it and tell me if anything changes; being
                                        seen early beats waiting" - an admission of violence
                                        answered as a symptom
    my husband hit me / is that bad    "Keep someone with you tonight, and ring back if it gets
                                        heavier" - somebody else's crisis, said to a person who is
                                        being hit, by the person they live with

The continuations in `bot/compose/fallback.py` (`_after_safety`) are written for lines *inside* an
emergency - "ok i rang them", "the ambulance is here", "i feel a bit better" - and a verdict ask
matches none of them, so it reaches the care pool of a symptom or the crisis pool of somebody else.
The yes here is the answer's own, said back, with the call still the next thing to do.

Not every answer from `bot/modules/safety.py` is an emergency. The same module hands out the
first-aid cards - ice on a swollen ankle, a burn under the tap, pinch a nosebleed - and the triage
cards, which name 999 or A&E as the *test* for how bad a thing is, not as the thing to do now. A
bare doubt after those is a different question, and one the floor already answers ("Ordinary on its
own, yes. It stops being ordinary if..."), so this reading only fires when the card itself says an
emergency: the case the safety module recorded is one it only records for emergencies, and the
card names somebody to ring now.
"""

import random
import re

from . import fallback

YES_LINES = (
    "Yes - it is serious, and that is why ringing is the thing to do now rather than something to "
    "sleep on. Tell me how it goes.",
    "Yes. Ringing is not an overreaction here: it is the whole point of the line I gave you. Do "
    "that first, and come back to me after.",
    "Yes it is, and the number I gave you is what it is for. Make the call, and we can go through "
    "the rest after.",
    "Yes - this is not one to wait and see about. Do the call now, and come back to me when you "
    "have.",
)

# The turn that has to be behind the doubt. A continuation of the bot's own ("yes", "thanks",
# "what happens now") leaves the safety answer in place behind it - `_after_safety` reads past
# them too - so the thread is still the emergency when the doubt comes. `already` answers a report
# that the call was made ("ok i rang them" -> "Good. Have they said anything back yet?"), which is
# the same thread carrying on, and the turn after it is still the doubt about the card.
_CONTINUATION = ("greeting", "already")

# The cases `bot/modules/safety.py` records in `memory["safety_case"]` for an emergency. The
# first-aid cards record none, and the triage cards record `fall_check` and `child_fever`, which
# name 999 and A&E as what decides whether the thing is serious - the doubt after those is the
# question "how bad does this have to get", not "is this an emergency". A case this reading has
# not been taught is left alone, and `tests/test_a_doubt_in_a_safety_thread.py` fails when the
# safety module grows a case that is missing here.
_EMERGENCY_CASES = frozenset((
    "abuse", "bleeding", "breathing", "chest", "chest_slow", "dog_attack", "dog_bite", "fire",
    "gas", "general", "hanging", "head_injury", "heat", "overdose", "poison", "seizure",
    "self_harm", "stroke", "swallowed_thing", "unconscious",
))

# The same doubt said after the call is already made, or with help on the way: the yes still holds,
# but "do the call now" is the one thing that cannot be said to a person whose crew is outside.
AFTER_THE_CALL_LINES = (
    "Still yes - and you have made the call, which was the part that mattered. Stay with what they "
    "tell you, and say if anything changes.",
    "Still yes, and it is with people who can do something about it now. Do what they say over "
    "anything I could offer, and tell me how it goes.",
    "Yes it is, and the call was the thing to do - you have done it. Whatever they told you to do "
    "next is what matters now.",
)

# Somebody to ring now: the emergency services, or the helpline a crisis and an abuse card give.
# The card has to say it, because the recorded case is the last one the module set and a first-aid
# card that follows an emergency leaves it standing.
_CALLS_SOMEBODY = re.compile(
    r"\b(?:999|911|112|ambulance|paramedics|emergency\s+services|116\s?123|988|0808|0800|1-?800)\b")


# The call is made, or help is on the way. Read on what was said *after* the card - the person's
# own report ("ok i rang them") and the bot's answer to it ("the crew are on their way") - because
# that is the turn that changes what the doubt means.
_HELP_IS_COMING = re.compile(
    r"\b(?:i|we|he|she|they)\s+(?:have\s+|had\s+|has\s+)?(?:already\s+)?(?:rang|phoned|called)\b"
    r"|\brang\s+(?:them|999|911|112|an\s+ambulance|the\s+(?:police|line))\b"
    r"|\b(?:on\s+(?:their|its|the)\s+way|are\s+coming|is\s+coming|are\s+here|is\s+here|"
    r"has\s+arrived|have\s+arrived|the\s+crew|paramedics|the\s+operator|the\s+emergency\s+line|"
    r"fire\s+brigade|emergency\s+line\s+says|they\s+said)\b")


def _the_answer_behind(memory):
    """The safety answer the doubt is about and what was said after it, or (None, []).

    Walks back past this bot's own continuations to the turn that started the thread, and stops at
    any other module's answer: once something else has answered, the doubt is about that, and this
    reading has nothing to say. Capped a few turns back so an emergency from earlier in the talk
    cannot colour a line today.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    after = []
    for turn in reversed(turns[-6:]):
        if turn.get("module") == "safety":
            # The line that raised the card counts as said after it: "i called 999" is answered
            # with the abuse card again (the safety module reads the call as the incident), and
            # without this the report of the call is invisible and the doubt is told to make it.
            after.append(str(turn.get("user") or "").lower())
            return str(turn.get("bot") or "").lower(), after
        if turn.get("module") not in _CONTINUATION:
            return None, []
        said = " ".join((str(turn.get("user") or ""), str(turn.get("bot") or "")))
        after.append(said.lower())
    return None, []


# The same doubt said as agreement rather than as a question - "thats bad" over the abuse card was
# answered with the symptom care pool too - and the whole line has to be the agreement, so a line
# with a subject of its own ("thats bad for the baby") is not this ask.
_AGREES_IT_IS_BAD = re.compile(
    r"^\W*(?:that|thats|that'?s|this|it|its|it'?s)\s+(?:is\s+|was\s+)?"
    r"(?:really\s+|pretty\s+|very\s+|so\s+|proper\s+|well\s+)?"
    r"(?:bad|awful|terrible|serious|grim|horrible|scary|frightening)\W*$")


def _a_bare_verdict_ask(text, memory, clean):
    read = memory.get("understood")
    if isinstance(read, dict) and read.get("asks_a_verdict"):
        return True
    # The understanding engine's whole-line test is the read; `reads_as_a_verdict` is the
    # composer's, which also reads "would you say that is bad" as the same ask.
    if _AGREES_IT_IS_BAD.match(clean):
        return True
    return bool(fallback.reads_as_a_verdict(text, memory))


def reply_for(text, memory):
    """The answer's own yes to a bare doubt in a safety thread, or None."""
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return None
    behind, after = _the_answer_behind(memory)
    if not behind:
        return None
    # The card has to be an emergency card, in what the safety module recorded and in what it
    # said: both, because either one on its own is wrong on a real line (see the module docstring).
    if memory.get("safety_case") not in _EMERGENCY_CASES:
        return None
    if memory.get("safety_safe") is True:
        return None
    if not _CALLS_SOMEBODY.search(behind):
        return None
    if not _a_bare_verdict_ask(text, memory, clean):
        return None
    # A call already made takes the "make the call" lines away: they would be telling the person
    # to do the thing they just told us they did.
    pool = AFTER_THE_CALL_LINES if any(_HELP_IS_COMING.search(said) for said in after) else YES_LINES
    options = [line for line in pool
               if line not in [t.get("bot") for t in (memory.get("turns") or [])[-5:]]]
    if not options:
        options = list(pool)
    # Seeded on the card as well as the line: "is that bad" is the same four words every time, and
    # the card is what is different about a fire, a bleed and a partner who hits you.
    seed = len(memory.get("turns") or []) * 7919 + sum(ord(c) for c in clean + behind)
    return random.Random(seed).choice(options)
