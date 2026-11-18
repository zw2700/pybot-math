"""The night the person described: two ends of it, and the hours between them.

People give a night one end at a time. "i go to bed at about 11" is answered from the bedtime
arithmetic with a seven o'clock start assumed, and then "and wake at 6" - the other end of the
same night - was read on its own and answered as a night that went wrong:

```
i feel knackered all the time / i go to bed at about 11 / and wake at 6
  before: Waking at the same time every night is common and it passes. Don't watch the clock...
```

That is advice for somebody who cannot stay asleep, and the person had just said what their night
is. The two times are one night when the chat gives both, and the answer is the length between
them read against the seven to nine hours most adults need - which is the whole of what the
person is asking about when they say their bedtime and their alarm in the same breath.

The rule is narrow on purpose:
* a line that gives both ends answers on its own; a line that gives only the wake time has to be
  the other end of the night the turn before described, so "wake at 6" after a bedtime is the
  night, and "wake at 6" after anything else is left to the module that reads it;
* a fragment is recognised by its opening ("and", "also", "then", "but", "plus") or by having no
  subject of its own ("wake at 6", "up at 6.30"), or by being nothing but the person's own wake
  marker and the hour in a line of six words or fewer ("i wake at 5", "i get up at 6"); a whole
  sentence about waking is a different thing, and "i wake at 6 every night and cant get back"
  stays the night-waking answer;
* nobody else's night is read: a child, a baby, a pet or a partner named in the line or in the
  line the time came from keeps its own answer;
* a wake time has to be a morning one (4am to 11am), so "i wake at 3" is the broken night it
  sounds like and not a six-hour night;
* a pair of times that gives less than two hours or more than fourteen is not a night's sleep,
  so nothing is said about the person's health off a pair of times that do not add up.
"""
import re

from ..compose import pick

# Somebody else's night. A line naming one of these is about them, not the person typing.
SOMEONE_ELSE = re.compile(
    r"\b(?:my|our|her|his|their|the)\s+(?:son|daughter|baby|boy|girl|child|children|kid|kids|"
    r"toddler|teenager|teen|mum|mom|mother|dad|father|partner|husband|wife|boyfriend|"
    r"girlfriend|dog|cat|puppy|kitten|pet|flatmate|housemate|roommate)\b", re.I)
# A pronoun subject with no person of the line's own: "he wakes at 6", "she goes to bed late".
THEY_NOT_ME = re.compile(r"^\s*(?:he|she|they|it)\b", re.I)
NIGHT_WAKING = re.compile(
    r"\b(?:keep|keeps|keeping|always|still|constantly|often)\s+wak(?:e|es|ing)\b"
    r"|\bwak(?:e|es|ing)\s+up\s+(?:in the night|during the night|several times|a few times)\b"
    r"|\b(?:in|during) the night\b|\bget back to sleep\b|\bcant sleep\b|\bcan't sleep\b"
    r"|\binsomnia\b", re.I)
# A fragment that carries on the line before it: no subject of its own, and often a joining word.
CARRIES_ON = re.compile(r"^\s*(?:and|also|then|but|plus|oh and|,\s*and)\b", re.I)
HAS_A_SUBJECT = re.compile(r"\b(?:i|we|you|he|she|they|it)\b|'m\b|\bim\b|\bmy\b|\bour\b", re.I)
# A line that is nothing but the person's own wake marker and the hour: "i wake at 5", "i woke at
# 5.30", "i get up at 6", "im up at 6". Said after the bedtime, this is the other end of the same
# night, and it is how most people say it - with the "i" in front. The short cap keeps out a
# second clause ("i wake at 5 and cant get back") and the fences above keep out a broken night.
I_WAKE = re.compile(
    r"^\s*(?:i|im|i'm|ive|i've|we|we're|were|weve|we've)\s+"
    r"(?:usually\s+|normally\s+|often\s+|just\s+|then\s+|still\s+)?"
    r"(?:wake|wakes|waking|woke|woken|waked|waken|"
    r"get\s+up|gets\s+up|got\s+up|getting\s+up|get|got|am|up)\b", re.I)

_WORD_HOURS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
               "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
_WORD = "|".join(_WORD_HOURS)
# One time, said the way people say it: "11", "6.30", "half eleven", "midnight", "one".
_ATOM = (r"(?:(?:at|around|about|by|till|until)\s+)?"
         r"(?P<atom>midnight|noon|half\s+(?P<half>" + _WORD + r")|"
         r"(?P<clock>[01]?\d|2[0-3])(?:[:.](?P<minutes>[0-5]\d))?\s*"
         r"(?P<when>am|pm|a\.m\.|p\.m\.)?|(?P<word>" + _WORD + r")(?=\b))")
BED_MARKER = re.compile(
    r"\b(?:go(?:es|ing)?\s+(?:off\s+)?to\s+(?:bed|sleep)|went\s+to\s+(?:bed|sleep)|"
    r"to\s+bed|in\s+bed|bedtime|bed|asleep|sleep(?:s|ing)?|slept)\b", re.I)
WAKE_MARKER = re.compile(
    r"\b(?:wake|wakes|waking|woke)(?:\s+up)?\b"
    r"|\b(?:get|gets|getting|got)\s+up\b|\b(?:am|are|be|im|i'm)\s+up\b"
    r"|\bup\b(?=\s*(?:at|around|about|by)\b)", re.I)


# A line that asks what time to go to bed is a question, not a night the person has described.
# "what time should i go to bed to wake at 6" names both a bedtime and a get-up time, and the
# wake hour sits inside the window after the word "bed", so it was read as the bedtime too and a
# seven-hour night came out as twelve. The answer to that line is the count-back arithmetic, which
# belongs to the bedtime module; a night whose length is known is not what was said.
ASKS_A_BEDTIME = re.compile(
    r"\b(?:what\s+time|when|what\s+hour|how\s+long\s+before|what\s+sort\s+of\s+time)\b"
    r"[^.!?]{0,40}?\b(?:go|going|be|get|getting)\s+(?:off\s+)?to\s+(?:bed|sleep)\b"
    r"|\b(?:go|going)\s+to\s+bed\s+(?:to|if|so\s+that|before)\b"
    r"|\bshould\s+i\s+(?:go\s+to\s+bed|be\s+in\s+bed|be\s+going\s+to\s+bed)\b", re.I)


def _hour_from(atom):
    """The hour an atom names, or None when the atom cannot be read on its own."""
    if atom is None:
        return None
    said = atom.group("atom").strip().lower()
    if said.startswith("midnight"):
        return 0
    if said.startswith("noon"):
        return 12
    if atom.group("half"):
        hour = _WORD_HOURS.get(atom.group("half").lower())
        if hour is None:
            return None
        return float(hour) + 0.5 if 12 <= hour <= 23 else float(hour) + 12.5
    if atom.group("word"):
        # A word hour is the time only when the line says it as one: "bed at eleven", "up at
        # seven". Read on its own "one" is a count and "six" can be a number of anything.
        return _WORD_HOURS.get(atom.group("word").lower())
    hour = int(atom.group("clock"))
    when = (atom.group("when") or "").lower().replace(".", "")
    if when.startswith("p"):
        return hour + 12 if hour < 12 else hour
    if when.startswith("a"):
        return 0 if hour == 12 else hour
    return hour


def _end(marker, text, after_bed, limit=26):
    """The time said just after the word that names one end of the night, or None."""
    for found in marker.finditer(text):
        window = text[found.end():found.end() + limit]
        atom = re.search(_ATOM, window, re.I)
        if atom is None:
            continue
        if after_bed and WAKE_MARKER.search(window[:atom.start()]):
            # The hour after the word "bed" is the time they get *up* when the line says so
            # ("go to bed to wake at 6"), and reading it as the bedtime counts the same night
            # twice: one end of it becomes both ends.
            continue
        hour = _hour_from(atom)
        if hour is None:
            continue
        if atom.group("when"):
            return hour
        if atom.group("clock"):
            minutes = float(atom.group("minutes") or 0) / 60.0
            if after_bed and not atom.group("when"):
                if hour == 12:
                    return minutes
                return hour + 12 + minutes if 6 <= hour <= 11 else None
            if not after_bed and not atom.group("when"):
                return hour + minutes if 4 <= hour <= 11 else None
            return hour + minutes
        # A word hour or a half hour is a bedtime when it is one and a morning when it is one.
        if after_bed:
            return hour + 12 if 6 <= hour <= 11 else hour
        return hour if 4 <= hour <= 11 else None
    return None


def _ends(line, wake_only=False):
    """The bedtime and the wake time a line names, as (bed, wake), either one possibly None."""
    text = " " + str(line or "").lower() + " "
    bed = None if wake_only else _end(BED_MARKER, text, after_bed=True)
    wake = _end(WAKE_MARKER, text, after_bed=False)
    return bed, wake


def _last_night(memory):
    """The bedtime and the wake time the chat has given, newest line first."""
    bed, wake = None, None
    turns = (memory or {}).get("turns") or []
    for turn in reversed(list(turns)[-6:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if not said.strip():
            continue
        low = said.lower()
        if SOMEONE_ELSE.search(low) or THEY_NOT_ME.search(low):
            return None, None
        one_bed, one_wake = _ends(said)
        if bed is None and one_bed is not None:
            bed = one_bed
        if wake is None and one_wake is not None:
            wake = one_wake
        if bed is not None and wake is not None:
            break
    return bed, wake


def _a_length(hours):
    """A length of a night the way a person says it: seven hours, seven and a half hours."""
    whole = int(hours)
    half = int(round((hours - whole) * 60))
    if half == 30:
        return "%s and a half hours" % _a_word(whole)
    if half:
        return "%s hours and %d minutes" % (_a_word(whole), half)
    return "%s hours" % _a_word(whole)


def _a_word(number):
    words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
             9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen"}
    return words.get(number, str(number))


SHORT = (
    "{length} between bed and the alarm is under the seven to nine most adults need, so the end "
    "worth moving is the bedtime.",
    "{length} is short of the seven to nine most adults do best on. The going to bed is the end "
    "that gives, because the wake time is what sets the clock.",
)
FINE = (
    "{length} is inside the seven to nine most adults need, so it is the quality of the night "
    "rather than the length that is worth looking at.",
    "{length} sits in the seven to nine range, so the length is not the problem - a warm room, a "
    "drink, or a phone in bed are what break a night that long.",
)
LONG = (
    "{length} is more than the seven to nine most adults need, and sleeping past that often "
    "leaves a person groggy rather than rested.",
    "{length} is past the seven to nine range. A slightly earlier alarm usually leaves somebody "
    "more awake, not less.",
)


def _seen(memory, reply):
    """The reply, remembered, so the next turn can add to it rather than say it again."""
    if isinstance(memory, dict):
        memory["asleep_said"] = str(reply)[:120]
    return reply


def answer_for(text, memory=None):
    """The hours between the two ends of the night they described, or None."""
    if not isinstance(memory, dict):
        return None
    said = " ".join(str(text or "").split())
    if not said or len(said.split()) > 14:
        return None
    low = said.lower()
    if ASKS_A_BEDTIME.search(low):
        return None
    bed, wake = _ends(said)
    if bed is None and wake is not None:
        # One end given: only the other end of the night the turn before described, and only when
        # the line is that night continued rather than a sentence about waking up.
        if SOMEONE_ELSE.search(low) or THEY_NOT_ME.search(low) or NIGHT_WAKING.search(low):
            return None
        mine_and_short = bool(I_WAKE.match(low)) and len(said.split()) <= 6
        carries_on = (bool(CARRIES_ON.match(low)) or not HAS_A_SUBJECT.search(low)
                      or mine_and_short)
        if not carries_on:
            return None
        was_bed, _was_wake = _last_night(memory)
        bed = was_bed
    if bed is None or wake is None:
        return None
    if SOMEONE_ELSE.search(low):
        return None
    hours = (wake - bed) % 24
    if hours < 2 or hours > 14:
        return None
    if hours < 7:
        shapes = SHORT
    elif hours <= 9:
        shapes = FINE
    else:
        shapes = LONG
    reply = pick(shapes, memory, said).format(length=_a_length(hours))
    return _seen(memory, reply[:1].upper() + reply[1:])
