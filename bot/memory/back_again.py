"""A trouble the chat already had, said to be back.

Four chats, one shape:

    i have a headache              / its back                -> "Got it. Is there anything you'd like a hand with?"
    how do i get rid of slugs      / the slugs are back      -> "Got it - the slugs are back."
    my boiler is making a banging noise / the banging is back -> "Thanks for telling me - I'm here if you want to dig into any of that."
    i think ive got a cold         / its come back           -> the nod, or the cough card by luck

The person is not opening a subject or changing one: they are reporting that the thing the chat
was working on has returned, and that says something the bot should pick up - the advice it gave
did not hold, or the thing never really went. The reply has to reach the thing and say so. The nod
("Got it. Is there anything you'd like a hand with?") is the reply nobody wants, and the echo
("Got it - the slugs are back.") tells them what they just said.

What is left alone:

* a line that asks instead of reporting ("is it back?", "will it come back?") - that is a question
  about the thing, and the cards answer it;
* a person or an animal said to be back ("my mum is back", "the cat is back") - good news or a
  separate subject, never a returning trouble;
* a thing the chat never had (nothing to be back from);
* "im back" and "we're back", which are the person, not the thing.
"""

import random
import re

from . import facts, history, topics

# The words a line may carry after "back" and still be only the report. "its back and its worse
# than last time" is the same report with the comparison added; "its back on the shelf" is a place
# and stops being this shape.
AFTER_BACK = re.compile(
    r"^(?:\s*(?:again|already|now|too|so soon|as well|for the (?:\w+ )?time|"
    r"and (?:its|it is|its worse|worse|its back|the \w+ is|its the same|same as before)|"
    r"its worse|it is worse|worse than (?:before|last time)|same as before))*\s*[.!]*$", re.I)

# "its back", "theyre back", "its come back", "that's back again". The referent is the thing the
# chat is about, so the record in hand is the thing itself.
PRONOUN_BACK = re.compile(
    r"^(?:and|so|well|oh|ok|okay|right)?\s*(?:its|it's|it is|theyre|they're|they are|"
    r"thats|that's|that is|these are|those are)\s+(?:come\s+|came\s+)?back\b(?P<tail>.*)$",
    re.I)

# What can come after the thing and still be the report: "is back", "are back again", "has come
# back", "came back", "returned". The copula carries the number for the first of these; a main verb
# ("the slugs came back") has none, so the thing's own last word decides.
VERB_BACK = re.compile(
    r"^(?:(?P<cop>is|are|was|were|s|'s|has|have|had)\s+(?:come\s+)?back|"
    r"(?P<main>came|come|comes|returned|returns)\s+back|(?P<alone>returned|returns))"
    r"\b(?P<tail>.*)$", re.I)

# How a line names the thing: a determiner and up to two words. The words are tried longest first
# and the rest of the line has to be a coming back, because "the slugs are back" reads as a thing
# called "the slugs are" if the words are taken greedily.
DETERMINERS = ("the", "my", "our", "his", "her", "their", "this", "that")

# "back again" on its own, after a chat that was about something.
BARE_BACK = re.compile(r"^(?:and|so|well|oh|ok|okay)?\s*back (?:again|already|now)\s*[.!]*$", re.I)

# The words that make a thing a person or an animal. A person back from somewhere is not a trouble
# coming back, and neither is a cat: "the cat is back" is good news, and "my mum is back" is
# another subject.
A_PERSON_OR_PET = re.compile(
    r"\b(?:" + "|".join(sorted(facts.RELATIONS)) + r"|dog|puppy|cat|kitten|rabbit|hamster|"
    r"parrot|goldfish|horse|tortoise|guinea)\b", re.I)

# What the report means, said back to them. The thing is named in front when the line named it,
# because "it" is the thing in hand and a friend says the word.
NAMED = (
    "{The thing}, back again - did {they} pass at all in between, or {has} {they} just been quiet?",
    "{The thing} came back. Same as before, or worse this time?",
    "{The thing} again. What did you do for {them} the first time, and how long did that hold?",
    "{The thing} being back usually means whatever set it off is still there - has anything "
    "changed since?",
)

# The same without a word to name: the thing was "it" in the chat too.
UNNAMED = (
    "Back again - did it pass at all in between, or has it been there under the surface?",
    "So it eased off and came back. Is it the same as before, or worse this time?",
    "Back so soon. What did you do for it the first time, and how long did that hold?",
    "Something coming back usually means whatever set it off is still there - has anything "
    "changed since?",
)


# A thing that went away and came back is good news, not a trouble returning: "my car is at the
# garage" / "my car is back", "my coat is at the dry cleaners" / "my coat is back", "the plumber
# came out tuesday" / "the plumber is back" read as "did it pass at all in between", which is a
# machine talking about itself. A trouble is the thing being wrong where it is ("my boiler is
# making a banging noise", "i have a headache"), so an earlier line that places the thing somewhere
# else, or says somebody came out to it, has said the thing is out of this reader's hands.
AWAY_FROM_HOME = re.compile(
    r"\b(?:is|was|are|were|been|being|stayed|sent|took|taken|gone|went|dropped|left)\s+"
    r"(?:at|in|to|with|into|off to|round to)\s+(?:the|a|an|my|our|his|her|their|its)\b|"
    r"\b(?:came out|came round|coming out|booked in|in for a service|"
    r"getting (?:fixed|repaired|serviced|cleaned|mended|done))\b", re.I)

# The words that say the thing itself is wrong, which is what makes it a trouble even when the
# earlier line also says where it went ("my car is at the garage and its making a noise").
A_SYMPTOM = re.compile(
    r"\b(?:noise|noisy|banging|rumbling|knocking|squeaking|whistling|rattling|humming|buzzing|"
    r"grinding|clicking|dripping|hissing|scraping|leak|leaking|damp|mould|"
    r"mold|smell|smells|reek|sore|ache|aches|aching|pain|painful|hurts?|hurting|bleeding|rash|"
    r"cough|fever|swollen|broken|cracked|fault|faulty|stuck|jammed|stopped working|"
    r"not working|isnt working|wont work|wont start|slugs?|mice|rats|ants|flies|aphids|weeds?|"
    r"worse|chest|throat|head|stomach|back|knee|shoulder|ankle|ear|tooth|toothache)\b", re.I)


def _the_earlier_line(memory, thing, text=""):
    """The person's own earlier line about the thing, or "" when there is none."""
    wanted = topics.keywords(thing) if thing else []
    record = topics.current(memory)
    words = list(wanted) or list((record or {}).get("words") or [])
    if not words:
        return ""
    now = " ".join(str(text or "").lower().split())
    for turn in reversed(list(memory.get("turns") or [])):
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("user") or "")
        if " ".join(line.lower().split()) == now:
            continue  # the line being answered is not an earlier turn
        have = topics.keywords(line)
        if any(topics.alike(word, other) for word in words for other in have):
            return line
    return ""


def _the_thing_went_away(memory, thing, text=""):
    """True when the earlier line about the thing puts it somewhere else, or a caller came out."""
    earlier = _the_earlier_line(memory, thing, text)
    if not earlier:
        return False
    if A_SYMPTOM.search(earlier):
        return False
    return bool(AWAY_FROM_HOME.search(earlier))


def _the_words(plural):
    """The pronouns a reply needs for one thing or for several."""
    if plural:
        return {"they": "they", "them": "them", "has": "have"}
    return {"they": "it", "them": "it", "has": "has"}


def _filled(line, thing, plural):
    words = _the_words(plural)
    if thing:
        words["the thing"] = thing[0].upper() + thing[1:]
    else:
        words["the thing"] = "It"
    out = line
    for key, value in words.items():
        out = out.replace("{" + key + "}", value)
        out = out.replace("{" + key[0].upper() + key[1:] + "}", value[0].upper() + value[1:])
    if thing:
        return out
    # The first word of the unnamed line is the thing itself, and with no word for it the line
    # reads as a sentence about nothing ("It back again"). Every unnamed line above is written to
    # stand without one.
    return out[0].upper() + out[1:]


def _an_earlier_topic(memory, thing):
    """Whether a turn before this one was about the thing: "the slugs" after the slug question."""
    wanted = topics.keywords(thing)
    if not wanted:
        return False
    here = len(memory.get("turns") or [])
    for record in reversed(memory.get("topics") or []):
        if record.get("turn") == here:
            continue
        have = record.get("words") or []
        if any(topics.alike(word, other) for word in wanted for other in have):
            return True
    return False


def _from_this_line(record, memory):
    """True when the topic record was written for the line being answered right now."""
    return record.get("turn") == len(memory.get("turns") or [])


def _the_thing(text, memory):
    """The thing said to be back: (the words for it, is it plural), or None."""
    line = " ".join(str(text or "").lower().split())
    if not line or "?" in line:
        return None
    words = line.split()
    if words and words[0] in ("and", "so", "well", "oh", "ok", "okay", "right"):
        words = words[1:]
    found = []
    numbers = {}
    if words and words[0] in DETERMINERS:
        for count in range(min(3, len(words) - 1), 0, -1):
            thing = " ".join(words[:count])
            said = VERB_BACK.match(" ".join(words[count:]))
            if not said or not AFTER_BACK.match(said.group("tail") or ""):
                continue
            if A_PERSON_OR_PET.search(thing):
                return None
            # A thing the chat never had cannot be back: there has to be an earlier turn about it
            # and not about something else. The record for the line being answered is not that
            # turn - it is written from the line itself, so "my knee is back" after a chat about a
            # headache found its own words and read as a knee the chat already had.
            if not _an_earlier_topic(memory, thing):
                continue
            # A copula ("is back") is the report; a main verb ("came back") is the same report
            # said shorter, and both are tried so "the slugs have come back" keeps "the slugs"
            # rather than reading "the slugs have" as the thing.
            if said.group("cop"):
                found.append((0, -count, thing))
            else:
                found.append((1, -count, thing))
            if said.group("cop"):
                number = said.group("cop").lower() in ("are", "were", "have")
            else:
                number = thing.split()[-1].endswith("s")
            numbers[thing] = number
        if found:
            found.sort()
            thing = found[0][2]
            return thing, numbers[thing]
        return None
    spoken = PRONOUN_BACK.match(line)
    if spoken:
        if not AFTER_BACK.match(spoken.group("tail") or ""):
            return None
        record = topics.current(memory)
        if not record or _from_this_line(record, memory):
            return None
        if A_PERSON_OR_PET.search(" ".join(record.get("words") or [])):
            return None
        plural = line.startswith(("theyre", "they're", "they are", "these", "those"))
        return None, plural
    if BARE_BACK.match(line):
        record = topics.current(memory)
        if not record or _from_this_line(record, memory):
            return None
        return None, False
    return None


def reply_for(text, memory):
    """The reply to a trouble said to be back, or None when the line is something else."""
    if not history.an_earlier_turn(memory, text):
        return None
    found = _the_thing(text, memory)
    if not found:
        return None
    thing, plural = found
    if _the_thing_went_away(memory, thing, text):
        # "my car is at the garage" / "my car is back" is good news about a thing that was away,
        # not a trouble that has returned, and the returning-trouble question is nonsense for it.
        return None
    line = random.choice(NAMED if thing else UNNAMED)
    return _filled(line, thing, plural)
