"""A taste named on the next line is a request for more of it, in the thing on the table.

    what should i watch tonight / i like sci fi      -> the science fiction films
    any good books / i like crime                    -> the crime books

Both used to be acknowledged and dropped ("Got it - you like sci fi."), because "i like sci fi" on
its own names no medium: the knowledge base knows science fiction films and science fiction books,
and nothing in the line says which. The medium is in the answer just given, so the line carries it
along and the entry that answered the first turn answers this one too.

Three things keep it from firing where it should not:

  * the answer before it has to have offered choices (two named things to pick between) - "any
    good books for my son" is answered with how to read with him, and a taste said next to that is
    not asking for a list of books;
  * a taste with nothing on the table is a fact about the person ("i like crime" on its own), and
    stays one;
  * a taste said twice running is served once (the second one would hand the same list back);
  * the answer it reaches has to say something new, which is checked where the answer is made
    (`bot/modules/answers.py`, `_same_as_the_last_answer`), because an entry with no picks for
    that taste hands the same list back and the person hears what they have just heard.
"""

import re

# The line as a whole is the taste, and nothing else: "i like crime", "i really love sci fi",
# "im into whodunnits". A line that also asks something ("what crime books should i try") has its
# own ask already and is not this reader's.
# The pronoun is optional because "im into crime" writes it into the verb: with `(?:i|we)\s+` in
# front, "im into" could only match after another "i ", so the shape this docstring gives as an
# example never reached the reader.
TASTE = re.compile(
    r"^(?:(?:i|we)\s+)?(?:really\s+|do\s+|just\s+)?"
    r"(?:like|love|enjoy|prefer|am into|'m into|im into|am a fan of|'m a fan of|im a fan of)\s+"
    r"(.+)$"
)
# The other way round: not what they like, but what they want off the list in front of them. It is
# the same request read from the other side - "i like crime" and "im in the mood for crime" both
# name one thing out of the picks just offered, and both are questions about it.
# "want" and "feel like" are deliberately not here: what follows them is as often a verb or a
# state ("i want to give up", "i feel like crying") as it is a thing.
WANTS = re.compile(
    r"^(?:(?:i|we)\s*)?(?:'?m|'?re|am|are)?\s*"
    r"(?:in\s+the\s+mood\s+for|in\s+the\s+humou?r\s+for|keen\s+on|up\s+for|"
    r"in\s+the\s+market\s+for|fancy|fancied|fancying|'?d\s+go\s+for|would\s+go\s+for)\s+(.+)$",
    re.I)
# A taste with nothing in front of it at all: "something funny", "anything light". Nobody says
# this about themselves out of the blue - it points at the list they have just been given - so it
# is only ever read with the same guards the loaded shapes get (an answer that offered choices, a
# medium to put it in, and no second helping of the same list).
SOMETHING = re.compile(r"^(?:something|anything)\s+(\S.*)$", re.I)
# The words that make the taste a thing rather than a lead-in: "in the mood for something light"
# is a taste for "light", and "any good something light films" is not a sentence anyone says.
_VAGUE_LEAD = re.compile(r"^(?:something|anything|some|any|a|an|the)\s+", re.I)
_ASKS_SOMETHING = re.compile(r"\?|^(?:what|how|why|when|where|which|who|can|could|should|do|does)\b")
# A taste the line turns down or weighs against another is not the taste to carry: "i like comedy
# not horror" and "i prefer comedy to horror" both name horror, and serving the horror list is the
# one reply that must not be given to someone who has just said they would rather not. The words
# that rule a taste out are read off the line, and a ruled-out taste is left to the answer it got
# before this reader existed ("Got it - you prefer comedy to horror.").
REFUSED = re.compile(
    r"\b(?:not|no|never|none|nope|hate|hates|dislike|dislikes|instead|rather|except|apart|prefer|prefers|"
    r"can'?t stand|cannot stand|stood|sick of|bored of|tired of|over|without|anything but)\b"
)
# The medium, read off what was asked and what was answered. The first group in each pattern is
# the word an entry keys on.
MEDIUM = (
    ("books", re.compile(r"\b(?:book|books|novel|novels|read|reading|author|paperback)\b")),
    ("films", re.compile(r"\b(?:film|films|movie|movies|watch|watching|series|tv|cinema)\b")),
)
_TITLE = re.compile(r"\*[^*\n]{2,}\*")
# "any good a good mystery books" is not a question anyone asks, so the words around the taste are
# not part of it.
_LEAD = re.compile(r"^(?:a|an|the|good|nice|great)\s+")
POINTS_BACK = ("you", "me", "it", "that", "this", "them", "him", "her")
MOST_WORDS = 4


def _offered_choices(reply):
    """Whether the answer named things to choose between ("*Groundhog Day*, *Knives Out* ...")."""
    return len(_TITLE.findall(str(reply or ""))) >= 2


def _said_the_medium(said):
    """The medium a line is about ("books", "films"), or "" - the earliest one named."""
    low = " ".join(str(said or "").lower().split())
    if not low:
        return ""
    best, at = "", None
    for medium, pattern in MEDIUM:
        found = pattern.search(low)
        if found and (at is None or found.start() < at):
            best, at = medium, found.start()
    return best


def _last_turn(memory):
    """What was asked and what was answered, which is where the medium is written."""
    turns = [t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)]
    if not turns:
        return "", ""
    return str(turns[-1].get("user") or ""), str(turns[-1].get("bot") or "")


def _taste(text):
    """What they like, in a few words, or "" when the line is not only a taste."""
    said = " ".join(str(text or "").lower().split()).strip(" .,!?")
    if not said or len(said.split()) > 8:
        return ""
    if _ASKS_SOMETHING.search(said):
        return ""
    found = TASTE.match(said) or WANTS.match(said) or SOMETHING.match(said)
    if not found:
        return ""
    taste = found.group(1).strip(" .,!?")
    if REFUSED.search(said):
        return ""
    while _LEAD.match(taste):
        taste = _LEAD.sub("", taste)
    while _VAGUE_LEAD.match(taste):
        taste = _VAGUE_LEAD.sub("", taste)
    words = [w for w in taste.split() if w]
    if not words or len(words) > MOST_WORDS:
        return ""
    for word in words:
        if word in POINTS_BACK:
            return ""
    # "i like crime books" already names the medium, so there is nothing to carry and the line
    # reaches the entry on its own.
    if _said_the_medium(taste):
        return ""
    return taste


# The words a films or books answer uses about its own medium. A picks answer is either titles in
# the asterisks (*Groundhog Day*) or sentences that say what kind of thing it is ("a holiday read",
# "the funniest safe pick"), and an answer with neither is about something else: written as "any
# good light books" the taste for "light" reached the soup, and "any good walk books" the walking
# advice. Both are worse than the note the person got before this reader existed, because they
# answer a question nobody asked.
MEDIUM_WORDS = {
    "books": re.compile(r"\b(?:books?|novels?|read(?:ing|s)?|author|paperback|stor(?:y|ies))\b", re.I),
    "films": re.compile(r"\b(?:films?|movies?|watch(?:ing)?|series|tv|cinema|documentar(?:y|ies))\b",
                        re.I),
}


def about_the_medium(answer, memory):
    """Whether the answer a taste bought is about the medium the taste was put in.

    True when there is no medium to check against, so the caller's own guards decide.
    """
    asked, answered = _last_turn(memory)
    medium = _said_the_medium(asked) or _said_the_medium(answered)
    pattern = MEDIUM_WORDS.get(medium) if medium else None
    if pattern is None:
        return True
    said = str(answer or "")
    return bool(_TITLE.search(said) or pattern.search(said))


def served_already(text, memory):
    """True when this is the same taste as the last turn, which was already answered with picks.

    "i like sci fi" said twice running is one request, served once: asked again it would reach the
    same entry and hand the same list back with a "Same as before" in front of it, which is the
    bot talking at the person. A different taste in the same place ("i like crime" after the sci
    fi films) has not been served and is not this.
    """
    taste = _taste(text)
    if not taste:
        return False
    asked, answered = _last_turn(memory)
    return _taste(asked) == taste and _offered_choices(answered)


def follow_up(text, memory):
    """The ask this line carries ("any good crime books"), or "" when it carries none."""
    taste = _taste(text)
    if not taste:
        return ""
    if served_already(text, memory):
        return ""
    asked, answered = _last_turn(memory)
    if not _offered_choices(answered):
        return ""
    medium = _said_the_medium(asked) or _said_the_medium(answered)
    if not medium:
        return ""
    return "any good " + taste + " " + medium
