"""The family name a person gives, and the ask that wants it back.

The store keeps one name for a person, and it is the name they want to be called: "my name is
sam" and "call me sam" both file `Sam`. A family name is a second name and not that one, so it is
kept on its own. Without it, "my last name is okafor" was filed as nothing at all and the ask a
turn later, "whats my surname", came back "What's your surname? You've not said, so only you know"

- a fact the chat had just been given, said back as a fact it never had.

Two rules hold the reading together:

* a surname is filed only when the line says the word is one - "my last name is okafor",
  "surname: okafor", "our family name is nguyen". A bare word after "i am" is a first name, and
  the store already reads those; guessing here would move a first name into the wrong slot.
* the ask is answered only when the line asks for their own family name and is not a how-to.
  "how do i change my surname" is a question about the world (a deed poll, a marriage, a form)
  and belongs to whoever answers those, so a verb of that kind takes the line away from here.

Everything else returns None and leaves the line exactly as it was.
"""
import random
import re

# The words people use for the name that is not their first one.
A_SURNAME_WORD = re.compile(
    r"\b(?:surname|sur-name|last\s*-?\s*name|family\s*-?\s*name|second\s*-?\s*name)\b", re.I)

# The line that gives it: the word, then the name, with or without "is" and a colon. "my last
# name is spelt wrong" and "my surname is hard to say" are about the name, not a name, so the
# words people use to describe one are read before the value is taken.
# The connector is not optional: without it "how do i change my surname after marriage" reads
# "after marriage" as the family name. A family name is always introduced by one of these.
SAYS_A_SURNAME = re.compile(
    r"\b(?:(?:my|our|the)\s+)?(?:surname|sur-name|last\s*-?\s*name|family\s*-?\s*name|"
    r"second\s*-?\s*name)\s*(?:is|was|'s|s|:|=)\s*"
    r"(?P<name>[A-Za-z][A-Za-z'\u2019\-]{1,30}(?:\s+[A-Za-z][A-Za-z'\u2019\-]{1,30}){0,3})", re.I)
# The parts a family name of several words is made of: "van der Berg", "Mc Donald", "De Souza".
# A second word that is none of these is the start of what the line says next, not the name.
NAME_PARTS = frozenset("van von der den de da di du dos das del della bin ibn al el la le mc mac "
                       "st saint o o' ap".split())

# A word that describes a name rather than being one. Taken from the phrases people actually
# type about the name itself: "my last name is hard to spell", "my surname is spelt wrong".
DESCRIBES_A_NAME = frozenset("""
hard difficult easy long short weird strange common rare unusual foreign hyphenated double
spelled spelt misspelled misspelt mispelled changed change changing wrong right same different
pronounced unpronounceable tricky silly complicated confusing correct incorrect spelled okay ok
also really actually just still not now too boring ugly nice lovely beautiful awful terrible funny
embarrassing stupid odd plain old big small
""".split())

# A word that can never be a family name, however the line is shaped. "my last name is on the
# form" and "my surname is in the post" say where the name is written, and the word after the
# connector is the preposition: filed as the name it answers "whats my surname" with "It's On."
NEVER_A_NAME = frozenset("""
on in at from of for to with about under over after before by into onto near above below
and or but if so that this it there when how why the a an
""".split())

# The particles a name of several words keeps in lower case: "van der Berg", "de la Cruz".
LOWER_PARTS = frozenset("van von der den de da di du dos das del della bin ibn al el la le "
                        "st saint".split())

# The shapes of the ask for it, in the words people use. The ask wants *which name it is*, so a
# line about the name is not one: "what does my surname mean", "why is my surname important", "is
# that a common surname", "is my surname common in nigeria" and "do you like my surname" all talk
# about it and none of them asks for it back. A patterened list of asks keeps those out without
# having to guess at every verb that might follow the word.
THE_NAME_WORD = r"(?:surname|sur-name|last\s*-?\s*name|family\s*-?\s*name|second\s*-?\s*name)"
ASKS_THE_SURNAME = tuple(re.compile(pattern, re.I) for pattern in (
    # "what's my surname", "what is my last name", "whats our family name", "which surname is mine"
    r"\b(?:what|whats|what's|which)\s+(?:is\s+|was\s+|were\s+)?(?:my|our|the)?\s*"
    + THE_NAME_WORD + r"\b",
    r"\b(?:which|what)\s+" + THE_NAME_WORD + r"\s+(?:is|was)\s+(?:mine|ours)\b",
    # "do you know my surname", "can you remember my last name"
    r"\b(?:do|did|can|could)\s+(?:you|u|ya)\s+(?:still\s+)?(?:know|remember)\s+(?:what\s+)?"
    r"(?:my|our)\s+" + THE_NAME_WORD + r"\b",
    # "tell me my surname", "remind me what my surname is"
    r"\b(?:tell|remind)\s+(?:me|us)\s+(?:what\s+)?(?:my|our)\s+" + THE_NAME_WORD + r"\b",
    # "my surname again", "what was my surname again"
    r"\b(?:my|our)\s+" + THE_NAME_WORD + r"\s+again\b",
    # "what did i say my surname was"
    r"\bwhat\s+(?:did|do)\s+i\s+(?:say|tell\s+you)\s+(?:my|our)\s+" + THE_NAME_WORD + r"\b",
    # the word and nothing else: "and my surname", "my surname?"
    r"^(?:and\s+|so\s+)?(?:my|our)?\s*" + THE_NAME_WORD + r"\s*\??$",
))
NOT_THE_ASK = re.compile(
    r"\b(?:how|change|changing|changed|deed\s+poll|register|registering|certificate|passport|"
    r"marri(?:ed|age|ying)|divorce|spell|spelt|spelled|pronounce|website|domain|form|online)\b",
    re.I)
THEIR_OWN = re.compile(r"\b(?:my|our|mine|ours|i|we|me)\b", re.I)


def _vary(options, memory):
    """A choice that does not repeat the last thing the bot said."""
    turns = memory.get("turns") or []
    recent = {turn.get("bot") for turn in turns[-5:] if isinstance(turn, dict)}
    fresh = [option for option in options if option not in recent] or list(options)
    return random.Random(len(turns)).choice(fresh)


def _the_name_they_said(word):
    """The name the way it is written: "okafor" -> "Okafor", "van der berg" -> "van der Berg",
    "o'brien" -> "O'Brien". A particle stays in lower case unless it is the first word, and the
    letter after an apostrophe is a name's own capital."""
    parts = " ".join(str(word or "").split()).split()
    if not parts:
        return ""
    # A particle stays in lower case when a name follows it: "van der berg" is "van der Berg",
    # and "van" on its own is "Van".
    written = []
    for index, part in enumerate(parts):
        if part.lower() in LOWER_PARTS and index < len(parts) - 1:
            written.append(part.lower())
        else:
            written.append(part[:1].upper() + part[1:])
    said = " ".join(written)
    return re.sub(r"(['\u2019])([a-z])", lambda m: m.group(1) + m.group(2).upper(), said)


def the_surname(memory):
    """The family name this chat was told, or ""."""
    held = memory.get("user") if isinstance(memory, dict) else None
    if not isinstance(held, dict):
        return ""
    said = held.get("surname")
    return said.strip() if isinstance(said, str) else ""


def _given_one(text):
    """The family name the line gives, or "" when the line gives none."""
    for match in SAYS_A_SURNAME.finditer(str(text or "")):
        name = match.group("name")
        first = name.split()[0]
        low = first.strip().lower()
        if not low or low in DESCRIBES_A_NAME or low in NEVER_A_NAME or len(low) < 2:
            continue
        parts = [first]
        for word in name.split()[1:]:
            # Only a part of a name joins the name: "my last name is okafor and my first name is
            # sam" gives Okafor, "van der berg" keeps all three words, and "de la cruz" its four.
            if word.lower() in NAME_PARTS or word[:1].isupper() \
                    or (parts[-1].lower() in NAME_PARTS and word.isalpha()):
                parts.append(word)
                continue
            break
        return _the_name_they_said(" ".join(parts))
    return ""


def observe(text, memory):
    """File a family name the line gives. True when one was kept."""
    if not isinstance(memory, dict) or not isinstance(text, str):
        return False
    said = _given_one(text)
    if not said:
        return False
    held = memory.setdefault("user", {})
    if not isinstance(held, dict):  # a store written by something else keeps its shape
        return False
    held["surname"] = said
    return True


def _asks_for_it(text):
    """True when the line is the person asking for their own family name."""
    said = " ".join(str(text or "").split())
    if not said or not A_SURNAME_WORD.search(said):
        return False
    if len(said.split()) > 12:
        return False
    if NOT_THE_ASK.search(said):
        return False
    return any(pattern.search(said) for pattern in ASKS_THE_SURNAME)


# The ask for the name of the other part: "do you know my first name", "whats my first name". The
# store keeps a first name and a family name in two places, so the two asks read them apart, and a
# full-name ask wants both.
ASKS_THE_FIRST = re.compile(
    r"\b(?:what|whats|what's|which|do|does|did|know|remember|again|tell)\b[^?.!]*"
    r"\b(?:first\s*-?\s*name|given\s*-?\s*name)\b", re.I)
ASKS_THE_FULL = re.compile(
    r"\b(?:what|whats|what's|which|do|does|did|know|remember|again|tell)\b[^?.!]*"
    r"\bfull\s*-?\s*name\b", re.I)


def _the_first_name(memory):
    from . import name as their_name
    return their_name(memory) or ""


def a_note(text, memory):
    """A short word back when the whole line is the family name and nothing else.

    A line that only gives it was left to the greeting ("Got it. Is there anything you'd like a
    hand with?"), which says nothing about what was heard. Only a whole line: a surname inside a
    longer sentence ("my last name is okafor and im moving to spain") is filed and the rest of the
    line is still the thing to answer.
    """
    said = " ".join(str(text or "").split())
    if not said or not isinstance(memory, dict):
        return None
    match = SAYS_A_SURNAME.match(said)
    if not match or said[match.end():].strip(" .!?,;-"):
        return None
    if not _given_one(said):
        # "my surname is hard for people" is a whole line that reads as a give and is not one:
        # the same reading that files a name is the one that says whether there is a name here.
        return None
    held = the_surname(memory)
    if not held:
        return None
    return _vary([held + " \u2014 noted.",
                  "Got it \u2014 " + held + ".",
                  held + ", I'll remember that."], memory)


# The follow-up that names it only as "it": "and what is it again", "what was it", "tell me again".
# Read only when the turn before it was about the surname, because on its own the line says
# nothing about which fact it wants.
ASKS_AGAIN = re.compile(r"\b(?:what|whats|what's|which|tell|remind|again|said)\b", re.I)
POINTS_BACK = re.compile(r"\b(?:it|that|them|those)\b", re.I)


def _the_lines_before(memory, back=3):
    """What the last few turns said, to see whether the chat is still on the surname."""
    turns = [turn for turn in (memory.get("turns") or [])
             if isinstance(turn, dict) and str(turn.get("user") or "").strip()]
    return " ".join(str(turn.get("user") or "") + " " + str(turn.get("bot") or "")
                    for turn in turns[-back:]).lower()


def a_follow_up(text, memory):
    """The family name for a follow-up that points back at it, or None."""
    said = _plain(text).lower()
    if not said or not the_surname(memory) or len(said.split()) > 7:
        return None
    if NOT_THE_ASK.search(said):
        return None
    if A_SURNAME_WORD.search(said):
        # A line that names it is either the ask for it, which _asks_for_it reads, or a line about
        # the name ("is that a common surname", "do you like my surname"), which is not.
        return None
    if not (ASKS_AGAIN.search(said) and POINTS_BACK.search(said)):
        return None
    if not A_SURNAME_WORD.search(_the_lines_before(memory)):
        return None
    held = the_surname(memory)
    return _vary(["It's " + held + ".", held + " \u2014 as you told me.",
                  "Still " + held + "."], memory)


def there_is_a_chat(memory):
    """True once a turn has been had, which is when the store has anything to read back."""
    from . import there_is_a_chat as any_chat
    return any_chat(memory)


def reply_for(text, memory):
    """The family name said back, or an honest line when the chat never gave one."""
    if not isinstance(memory, dict):
        return None
    note = a_note(text, memory)
    if note:
        return note
    if not there_is_a_chat(memory):
        # A memory reply needs a memory. On the first message there is none, and the line is a
        # person meeting the bot asking it to read back something it has never been told: the reply
        # for that is the question asked in return ("What's your surname? You've not said, so only
        # you know - tell me and I'll remember it"), which is the answer the modules that answer
        # lines give, so this one stands down and lets them.
        return None
    if ASKS_THE_FULL.search(_plain(text)):
        return _the_full_name(memory)
    if ASKS_THE_FIRST.search(_plain(text)):
        return _the_first_name_reply(memory)
    if not _asks_for_it(text):
        return a_follow_up(text, memory)
    if _given_one(text):
        # The line gives the name and asks nothing ("whats my surname, its okafor" is rare but
        # "my surname is okafor" reaching here is not): the give is the answer it belongs to.
        return None
    held = the_surname(memory)
    if not held:
        memory["asked_for"] = "surname"
        return _vary(["You haven't told me your surname yet.",
                      "I don't have it \u2014 you've not said your surname.",
                      "You haven't given me a surname, so I'd only be guessing."], memory)
    return _vary(["It's " + held + ".",
                  held + " \u2014 that's the one you gave me.",
                  "Your surname's " + held + "."], memory)


def _plain(text):
    return " ".join(str(text or "").split())


def _the_full_name(memory):
    """Both names, when the chat holds them: "Sam Okafor"."""
    first, family = _the_first_name(memory), the_surname(memory)
    if first and family:
        return _vary([first + " " + family + ".", "You're " + first + " " + family + ".",
                      first + " " + family + " \u2014 that's both of the names you gave."], memory)
    if first:
        return "I have your first name, " + first + ", but you haven't given me a surname."
    if family:
        return "I have your surname, " + family + ", but you've not told me your first name."
    memory["asked_for"] = "name"
    return _vary(["You haven't told me your name yet.",
                  "I don't have a name from you \u2014 you've not said."], memory)


def _the_first_name_reply(memory):
    first = _the_first_name(memory)
    if first:
        return _vary([first + " \u2014 you told me.", "It's " + first + ".",
                      "Your first name's " + first + "."], memory)
    memory["asked_for"] = "name"
    return _vary(["You haven't told me your first name yet.",
                  "I don't have it \u2014 you've not said your first name."], memory)
