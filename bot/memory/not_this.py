"""A line that only rules a place out is not a line about that place.

```
we want to go to italy / not rome   -> "In Rome: the Colosseum with a timed ticket, the Pantheon..."
im going to spain / not portugal    -> "Portugal: Lisbon for trams, tarts and the river..."
```

The person took the place back and the bot answered with the card for the place they had just
ruled out. It reads as if it had not heard them, and it is the one reply that cannot help: what
they want is somewhere else.

`bot/compose/ruledout.py` reads the shape of a rule-out a thing arrives in - "not a series",
"not the chemical stuff", "its not the trap" - and every arm of it needs a determiner or a plural,
so a bare name slips through: "not portugal" and "not rome" name a place with no article and no
plural, and were read as a fresh mention of it. A name is the one kind of thing that needs no
determiner, so it is read here, where the store already knows which words are places
(`bot.memory.facts.place_value`, and the towns and countries the knowledge base has a card for).

The reply says what is left standing: the other place the chat is on ("Spain, then - no Portugal"),
and when nothing else is on the table it says the place is out and asks where instead. A line that
names a thing that is not a place is left to the readers that know about it.
"""
import re

from ..compose import pick
from ..knowledge import travel
from . import facts
from . import user

# A line that is nothing but the rejection of a name: "not portugal", "no rome, then",
# "definitely not portugal", "i said not rome", "we arent going to portugal". The name is the
# whole rest of the line, so a line with anything else after it ("not portugal in june, spain")
# is not this reader's.
# The words that can follow the name without adding anything: "no rome, then", "not france,
# though". The comment above promises "no rome, then" and the shape used to fail it, so the
# trailing word is part of the shape rather than a thing the reader hopes will not turn up.
_AFTER_THE_NAME = r"(?:\s*,?\s*(?:then|though|after all|actually|really))?"

NOT_A_PLACE = (
    re.compile(r"^(?:and\s+|but\s+|so\s+|ok\s+|okay\s+)?(?:no,?\s+|nope,?\s+|nah,?\s+)?"
               r"(?:definitely\s+|absolutely\s+|really\s+|probably\s+|actually\s+)?not\s+"
               r"(?:to\s+)?(?P<place>[a-z][a-z' -]{1,24}?)" + _AFTER_THE_NAME + r"$"),
    # "no rome, then", "nah portugal": the rejection with no "not" in it at all. The comment
    # above names this shape and no arm used to read it, so "no rome, then" after "we want to go
    # to italy" got the Rome card back. A word that is not a place in the knowledge base is no
    # rule-out ("no idea", "no worries"), so the arm costs nothing.
    re.compile(r"^(?:and\s+|but\s+|so\s+|ok\s+|okay\s+)?(?:no|nope|nah),?\s+"
               r"(?:definitely\s+|absolutely\s+|really\s+|probably\s+|actually\s+)?"
               r"(?P<place>[a-z][a-z' -]{1,24}?)" + _AFTER_THE_NAME + r"$"),
    re.compile(r"^(?:and\s+|but\s+)?i\s+(?:said|meant|told you)\s+not\s+"
               r"(?P<place>[a-z][a-z' -]{1,24}?)" + _AFTER_THE_NAME + r"$"),
    # "we arent going to portugal", "im not going to spain", "we are not going to rome anymore":
    # the trip itself is denied, which is the plainest way a place gets ruled out. The words are
    # put in their long form first, so the contractions the typist writes without an apostrophe
    # need no arm of their own.
    re.compile(r"^(?:and\s+|but\s+)?(?:we|i|they|he|she)\s+"
               r"(?:am|are|is|was|were|will|would|re|m|s)?\s*not\s+"
               r"(?:going|heading|off|flying|driving)\s+(?:to|into)\s+"
               r"(?P<place>[a-z][a-z' -]{0,24}?)\s*"
               r"(?:anymore|any\s+more|now|then|after\s+all|this\s+time)?$"),
    re.compile(r"^(?:and\s+|but\s+)?(?:we|i)\s+(?:dont|don't|do not)\s+(?:want|fancy)\s+"
               r"(?:to go to\s+)?(?P<place>[a-z][a-z' -]{1,24}?)" + _AFTER_THE_NAME + r"$"),
)

# The contractions put in their long form, so a rule-out written "arent" and one written "are not"
# are the same line to the shapes below. The "not" has to survive the rewrite: "we dont want to go"
# turned into "we do want to go" would read as the opposite of what they said.
_BE_WILL = "are|is|were|was|do|does|did|could|would|should|will|can|must"
_CONTRACTIONS = (
    (re.compile(r"\b(we|i|they|he|she|it|you)(?:'re|re)\b"), r"\1 are"),
    (re.compile(r"\b(i)(?:'m|m)\b"), r"\1 am"),
    (re.compile(r"\b(we|i|they|he|she|it)(?:'s|s)\b"), r"\1 is"),
    (re.compile(r"\b(" + _BE_WILL + r")n'?t\b"), r"\1 not"),
    (re.compile(r"\baint\b"), "is not"),
    (re.compile(r"\bim\b"), "i am"),
)

# Where the chat is going instead, said as the thing that stands.
STANDS = (
    "{place}, then - no {gone}.",
    "Right - {place}, not {gone}.",
    "So {place} it is, without {gone}.",
    "{place} on its own, then.",
)
# Nothing else is on the table: say the place is out and ask where to look instead.
OUT = (
    "No {gone}, then. Where are you thinking instead?",
    "Fair enough - not {gone}. What are you after instead?",
    "{gone} is out, then. Where else are you looking?",
)
# ...unless the bot asked something on the line before, in which case the reply carries the one
# question of the exchange: a bot that asks twice running is the one that read nothing.
OUT_AFTER_A_QUESTION = (
    "No {gone}, then - say where instead and I will go with that.",
    "Fair enough - not {gone}. Tell me where you are looking and I will help from there.",
    "{gone} is out, then. Point me at somewhere else when you know it.",
)


def _the_place_the_chat_is_on(memory, gone):
    """The place the chat holds that is not the one they ruled out, or "".

    What the store keeps is the line they typed ("Go to italy"), not a name, and a name is what
    the reply has a slot for: "So Go to italy it is, without Rome." puts a capital mid-sentence and
    a whole sentence where "Italy" belongs. The place is named the way the knowledge base holds
    it, and a stored line with no place in it is no place to say.
    """
    held = []
    for place in reversed(user(memory).get("places") or ()):
        if isinstance(place, str) and place.strip():
            held.append(place.strip())
    plan = user(memory).get("plan")
    if isinstance(plan, str) and plan.strip():
        held.append(plan.strip())
    for place in held:
        if place.lower() == gone.lower():
            continue
        named = _the_name_in(place, gone)
        if named:
            return named
    return ""


def _the_name_in(said, gone):
    """The place the knowledge base knows inside a stored line, or ""."""
    whole = _a_place_the_chat_knows(said)
    if whole and whole.lower() != gone.lower():
        return whole
    found = ""
    for word in re.findall(r"[a-z][a-z']*", said.lower()):
        if word == gone.lower():
            continue
        named = _a_place_the_chat_knows(word)
        if named:
            found = named
    return found


def _a_place_in_play(memory, place):
    """True when the chat is on a place, so a ruled-out place is a place they were going to.

    "im going to spain" / "not portugal" is a person narrowing a trip, and the store holds Spain.
    "i watched a film last night" / "not rome" is a place name out of nowhere: nothing in the ~chat
    is about somewhere, and a wire reply about Rome would be about a conversation that never
    happened, so the line is left to the readers that know what it is about.
    """
    if not isinstance(memory, dict):
        return False
    held = user(memory)
    if held.get("places") or held.get("plan") or held.get("city"):
        return True
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return False
    for turn in turns[-6:]:
        if not isinstance(turn, dict):
            continue
        for said in (turn.get("user"), turn.get("bot")):
            if not isinstance(said, str):
                continue
            for word in re.findall(r"[a-z][a-z']*", said.lower()):
                if word != place.lower() and _a_place_the_chat_knows(word):
                    return True
    return False


def _asked_last(memory):
    """True when the bot's own last line asked something."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1]
    said = last.get("bot") if isinstance(last, dict) else None
    return isinstance(said, str) and said.strip().endswith("?")


def _a_place_the_chat_knows(place):
    """The name written as the knowledge base holds it, or "" for a word that is no place."""
    word = str(place or "").strip().lower()
    if not word:
        return ""
    if word in travel.CITIES or word in travel.CITY_COUNTRY:
        return facts.place_value(word) or word.capitalize()
    if word in set(travel.CITY_COUNTRY.values()) or word in travel.CAPITALS:
        return word.capitalize()
    return ""


def _in_plain_words(text):
    """The line in long form, lower case, single-spaced and with its end stop taken off."""
    line = str(text or "").strip().lower().replace("\u2019", "'")
    for shape, long_form in _CONTRACTIONS:
        line = shape.sub(long_form, line)
    return " ".join(line.split()).rstrip(".!,")


def the_place_ruled_out(text, memory):
    """The place a line of nothing but its rejection names, or ""."""
    if not isinstance(text, str):
        return ""
    line = _in_plain_words(text)
    line = line.rstrip(".!,")
    for shape in NOT_A_PLACE:
        found = shape.match(line)
        if not found:
            continue
        place = _a_place_the_chat_knows(found.group("place"))
        if place:
            return place
    return ""


def _the_place_ruled_out(text, memory):
    """The reply to a line that only rules a place out, or None."""
    gone = the_place_ruled_out(text, memory)
    if not gone or not isinstance(memory, dict):
        return None
    stands = _the_place_the_chat_is_on(memory, gone)
    if not stands and not _a_place_in_play(memory, gone):
        return None
    if stands:
        pool = STANDS
    elif _asked_last(memory):
        pool = OUT_AFTER_A_QUESTION
    else:
        pool = OUT
    # The reply just given is dropped first: the turn being answered is already in the history, so
    # a hand-back that leaned on `bot.compose.pick`'s own "never the last line" found the current
    # turn there and put two identical replies in a row.
    lines = [shape.format(place=stands, gone=gone) for shape in pool]
    turns = memory.get("turns") if isinstance(memory.get("turns"), list) else []
    said_lately = {turn.get("bot") for turn in turns[-4:]
                   if isinstance(turn, dict) and isinstance(turn.get("bot"), str)}
    fresh = [line for line in lines if line not in said_lately] or lines
    return pick(fresh, memory, str(text or ""))


def reply_for(text, memory):
    """The reply to a line that only rules a place out, or a thing said again with "still", or None.

    Both readings are the store's before any card is opened, and the store asks this reader first,
    so they are answered here in one call. The still reading is `bot.memory.tried`'s: it is a
    follow-up on the chat's own thing, and the one word the line carries ("cold", "freezing")
    must not open a card about something else.
    """
    ruled_out = _the_place_ruled_out(text, memory)
    if ruled_out:
        return ruled_out
    from . import tried

    return tried.reply_for(text, memory)
