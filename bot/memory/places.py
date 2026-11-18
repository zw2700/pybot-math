"""Where somebody lives, read out of what they said - and said back.

These are the readers the store answers "where does my sister live" from: the town a line gave
("my sister lives in cork"), the pronoun that stands for the person the chat has just been about
("she moved to york"), the correction that moves somebody's town ("no, york"), and the say-back
line built from them.

They live here rather than in `bot/modules/memory_store.py` because that module had grown past the
size the world accepts a change to. Nothing changed in the move: the store imports every name
back, so the readers and their callers are the same objects they were.
"""
import re

from ..memory import facts as extract
from ..memory import others
from ..memory.store_lines import WHERE_ASK



# "my sister lives in cork", "my parents moved to spain": someone else's place, not the user's.
# The town can sit a clause away from the person - "my sister is called ana and she lives in
# leeds" puts the name first and the town after it - so the gap is a whole clause. The verb
# still has to say where somebody is, with a place after it, so nothing else is read as one.
OTHER_PLACE = re.compile(
    r"\bmy (\w+)s?\b[^.!?]{0,60}?\b(?:live|lives|living|moved|moves|moving|settled|based|"
    r"staying|relocated)\s+(?:in|to|near|at)\s+([A-Za-z][A-Za-z'-]{1,}"
    r"(?:[ -][A-Za-z][A-Za-z'-]{1,})?)", re.I)
# A line whose subject is a pronoun - "she moved to york last month" - is about the person the
# line before it was about, so the pronoun is read against that person. Without this the store
# keeps the town from the older line and says it back after the move.
OTHER_PLACE_PRONOUN = re.compile(
    r"\b(?:she|he|they)\s+(?:has\s+|had\s+|just\s+|now\s+)?(?:live[sd]?|lives|living|"
    r"moved|moves|moving|settled|relocated|is\s+based|are\s+based)\s+(?:in|to|near|at)\s+"
    r"([A-Za-z][A-Za-z'-]{1,}(?:[ -][A-Za-z][A-Za-z'-]{1,})?)", re.I)
# The words that end a place: "my dad moved to bristol last year" is Bristol, and saying
# "Bristol Last" back is not a place anyone lives in.
PLACE_ENDS = frozenset("""last next this that year years month months week weeks ago previously
before then soon now already after""".split())
# The people a line can name without giving them a place: "my sister is called priya" says who
# the chat is about, and the pronoun after it - "she lives in bristol" - is about her. Without
# this only a line that already gave a town named the person, so her town had nobody to hang on
# and the ask two lines later was answered "You haven't said where your sister lives."
OTHER_PERSON_NAMED = re.compile(
    r"\bmy (\w+)s?\b(?:[^.!?]{0,40}?\b(?:is|are|was|were)\s+(?:called|named|known as)\b|"
    r"[^.!?]{0,12}$)", re.I)
# A line that asks something is not a line that says where somebody lives, whether or not it
# carries a question mark: "does she live in york" is the question, not the answer to it.
A_QUESTION_ASKED = re.compile(
    r"^\W*(?:and\s+|but\s+|so\s+)?(?:do|does|did|is|are|was|were|has|have|had|can|could|"
    r"will|would|should|shall|may|might|am)\b", re.I)


def _a_place(value):
    """The place in a phrase of words, or None when the words are not one."""
    words = []
    for word in re.split(r"[ -]", value):
        low = word.lower()
        if low in PLACE_ENDS or low in extract.NOT_PLACES or low in extract.HOME_STOP:
            break
        words.append(word)
        if len(words) == 2:
            break
    if not words:
        return None
    first = words[0].lower()
    if first in extract.HOME_STOP or first in extract.NOT_PLACES or first in PLACE_ENDS:
        return None
    return " ".join(w[:1].upper() + w[1:] if w.islower() else w for w in words)


# The words that make a short value something other than a town: a pronoun, a number, a unit.
# "no, she" and "no, seven" take something back but name no place, and reading either as one put
# a person's address down as "She".
NOT_A_PLACE_VALUE = frozenset("""
i me my we us our you your he him his she her it its they them their
one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen
sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety
hundred thousand million first second third last next again too either neither
""".split())


def _the_place_alone(text):
    """The place a line names with no frame around it: "no, york", "sorry, in york", "i meant york".

    A correction that names only the new value leaves the frame to the line it corrects, and a
    place for somebody else is read out of the whole conversation rather than out of one line, so
    "my sister lives in perth" then "no, york" had nothing to move: the walk below only ever read
    a place out of a line with a person and a live verb in it. Only a line that opens with a
    take-back and carries a single place is read this way - "no, tree nuts" and "no, seven" name
    no town, and a line that states a fact of its own is left to the readers that claim it.
    """
    low = " ".join(str(text or "").strip().lower().rstrip(".!,").split())
    if not low or low.endswith("?"):
        return None
    opener = extract.CORRECTION_OPENER.match(low)
    if not opener:
        # "not perth, york" names the value it takes back first, the same way the marked forms
        # name it last: the frame is still the line before's.
        opener = re.match(r"not\s+[a-z'-]+[, ]+", low)
        if not opener:
            return None
    rest = low[opener.end():].strip(" .,!-")
    rest = re.sub(r"^(?:in|to|at|from|near)\s+", "", rest)
    words = rest.split()
    if not words or len(words) > 2 or any(word in NOT_A_PLACE_VALUE for word in words):
        return None
    return extract.place_value(rest) or None


def _said_places(memory):
    """Every place the user gave for somebody else, in the order they gave them.

    The person is named in the line ("my sister lives in cork") or left to the pronoun that
    stands for the last person named ("she moved to york"), so the walk carries the two
    together: what the chat says last about somebody is what the store says back. A correction
    that names only the new town ("no, york") is the same thing said again, so it moves the town
    of the person the line before it gave one for - and only there, so a bare "no, york" about
    their own city never moves somebody else's.
    """
    found = []
    last = ""
    fresh = False
    for turn in memory.get("turns") or []:
        text = turn.get("user") or ""
        if not text or text.rstrip().endswith("?") or A_QUESTION_ASKED.search(text):
            # A question is not a place they gave: "does she live in leeds" asks, it does not
            # say, and reading it as the answer turns their question into a fact.
            fresh = False
            continue
        named = ""
        gave = False
        for match in OTHER_PLACE.finditer(text):
            place = _a_place(match.group(2))
            named = match.group(1)
            if place:
                found.append((named, place))
                gave = True
        if not named:
            # "my sister is called priya" names her and gives her no place, and the next line's
            # pronoun is about her, so she is who the chat is about from here on.
            asked = OTHER_PERSON_NAMED.search(text.rstrip())
            if asked:
                named = asked.group(1)
        if named:
            last = named
        elif last and not OTHER_PLACE_PRONOUN.search(text) and fresh:
            # The line names no person and no verb, so the frame is the line it corrects, and
            # only that line: "my sister lives in perth" then "no, york" is York.
            alone = _the_place_alone(text)
            if alone:
                found.append((last, alone))
                gave = True
        if last and not gave:
            for match in OTHER_PLACE_PRONOUN.finditer(text):
                place = _a_place(match.group(1))
                if place:
                    found.append((last, place))
                    gave = True
        fresh = gave
    return found


def _a_town_moved(memory, text):
    """The place a correction names for somebody else, said back as a line.

    "my sister lives in perth" then "no, york" was a shrug and the store still said Perth, so the
    correction is answered where it is made and not only a turn later when they ask about her.
    """
    alone = _the_place_alone(text)
    if not alone:
        # "no, she lives in york" names the person only by the pronoun, and the line is a
        # correction, so it moves her town the same way and says it back the same way.
        low = " ".join(str(text or "").strip().lower().split())
        frame = OTHER_PLACE_PRONOUN.search(low) if extract.CORRECTION_OPENER.match(low) else None
        if not frame:
            return None
        alone = _a_place(frame.group(1))
        if not alone:
            return None
    turns = [turn.get("user") or "" for turn in (memory.get("turns") or [])]
    before = turns[-1] if turns else ""
    if not before or not (OTHER_PLACE.search(before) or OTHER_PLACE_PRONOUN.search(before)):
        # The frame is the line before this one, so the town they gave has to be on it: a bare
        # "no, york" after a line about their holiday is not their sister's address.
        return None
    said = _said_places(memory)
    if not said or said[-1][1].lower() == alone.lower():
        return None
    who = str(said[-1][0]).lower()
    plural = who.endswith("s")
    return ("Got it — your " + who + (" live in " if plural else " lives in ") + alone + ".")


def _other_place(memory, who):
    """The last place the user gave for this person, said back as a line."""
    want = (who or "").lower().rstrip("s")
    found = [(said, place) for said, place in _said_places(memory)
             if not want or said.lower().rstrip("s") == want]
    if not found:
        return None
    said, place = found[-1]
    plural = said.lower().endswith("s")
    return "Your " + said.lower() + (" live in " if plural else " lives in ") + place + "."


def _asked_person(memory, low):
    """Who a place ask is about, when it is about somebody other than the user.

    "where does my sister live" names her, "and where does she live" leaves her to the pronoun
    the chat has just been about, and "where does jane live" names her rather than her relation.
    All three ask the same thing, so all three are read here and answered from the chat.
    """
    named = re.search(r"\b" + WHERE_ASK + r" (?:does|do) my (\w+) (?:live|come from)\b|\b"
                      + WHERE_ASK + r" is my (\w+) (?:living|based)\b", low)
    if named:
        return named.group(1) or named.group(2) or ""
    if re.search(r"\b" + WHERE_ASK + r" (?:does|do) (?:he|she|they) (?:live|come from)\b|\b"
                 + WHERE_ASK + r" is (?:he|she|they) (?:living|based)\b", low):
        person = memory.get("person")
        who = person.get("who") if isinstance(person, dict) else ""
        if who:
            return str(who).lower()
        # "my parents live in cork" then "where do they live": the plural is a group, so the
        # store keeps no single person for the pronoun. The last person the chat gave a place
        # for is the one it is about.
        said = _said_places(memory)
        return str(said[-1][0]).lower() if said else ""
    # "wheres my brother" is the same ask as "where does my brother live": the spoken form fuses
    # the where-word and the verb, and without this it was a search hedge about a person the chat
    # had just been told a place for. Only a person is read this way - "wheres my phone" is not a
    # place ask about anybody, and gets the line it got before.
    plain = re.search(r"\b" + WHERE_ASK + r" (?:is|are|was|were) (?:my|our) ([a-z]+)\b", low)
    if plain:
        word = plain.group(1).lower()
        if word.endswith("s") and word[:-1] in extract.KIN_WORDS:
            word = word[:-1]
        if (word in extract.KIN_WORDS or word in extract.RELATIONS
                or any(str(one.get("who") or "").lower() == word for one in others(memory))):
            return word
    by_name = re.search(r"\b" + WHERE_ASK + r" (?:does|do) ([a-z][a-z'-]{1,}) (?:live|"
                        r"come from)\b", low)
    if by_name:
        word = by_name.group(1).lower()
        if word in ("he", "she", "they", "my", "your", "i", "we", "it", "the", "a"):
            return ""
        for entry in others(memory):
            if str(entry.get("name") or "").lower() == word:
                return str(entry.get("who") or "").lower()
    return ""
