"""An ask about how long to do a thing, written out with the thing the chat is about.

    i started learning guitar last month
    my fingers hurt
    how long should i practise          -> "About six weeks for most bones - six for a wrist or
                                            collarbone, six to eight for an arm ..."

The last line is a question about the practice, and the chat is on the guitar: an answer about a
fracture is the wrong answer to a person who has said nothing about a break. The line was read
against the line before it, whose words are a complaint about fingers, and the entry on bone
healing keys both "fingers" and "how long", so it took the turn.

The doing word in the line ("practise") is what the ask is about, and the thing it is done with
("guitar") is what the chat has been doing. Written out with that thing - "how long should i
practise guitar?" - the entry filed for the instrument answers seven words, which is the answer
the person wanted. The module only offers the rewrites: the caller looks each one up and takes the
first that answers with a length, so a line whose thing reaches nothing keeps the turn it had.
"""
import re

from . import topics

# The asks this module has an opinion about: a length, of a thing that is done.
LENGTH_ASK = re.compile(r"\bhow (?:long|many (?:hours|minutes|days|weeks|months|years))\b", re.I)

# The words a length ask is made of. Anything else in the line is a thing it names, and a line
# that names the thing already ("how long should i practise guitar") needs no rewrite from here.
ASK_WORDS = frozenset("""
how long many much hours hour days day weeks week months month years year minutes minute should
shall can could would will do does did is are was i me my we you it that this to for the a an in
on at about each per every and or of time
""".split())

# A thing said as the time it is asked about is not the thing: "last month" in the line that put
# the guitar in the chat is not what the practice is done with.
TIME_WORDS = frozenset("""
day days week weeks month months year years weekend summer winter spring autumn today tomorrow
yesterday morning evening night ago last next this recent lately start started
""".split())

# A body doing that is not a thing the ask is done with: "how long does it take to heal" is the
# question the injury card answers, and it is never about a guitar.
NOT_A_THING_DONE = frozenset("heal recover bleed".split())

# How many things back the chat is searched for the thing the doing is done with. A chat can be
# long and the thing can be several lines back ("i started learning guitar" is not the line before
# the ask), but the oldest line of a chat two hundred lines long is not what a new ask is about.
LOOKBACK = 12


def _is_doing(word):
    """Whether this word is one of the things a person does, in the form it is typed in.

    The list is written in the stem form ("start", "learn", "practise") and people type "started"
    and "learning", so a word counts when a doing word of four letters or more is how it begins.
    Two-letter stems are left out of that: "dog" begins "do" and no one does a dog.
    """
    if word in NOT_A_THING_DONE or topics.stem(word) in NOT_A_THING_DONE:
        return False
    if word in topics.ACTION:
        return True
    for doing in topics.ACTION:
        if len(doing) < 4 or len(word) <= len(doing):
            continue
        if word.startswith(doing):
            return True
        if doing.endswith("e") and word.startswith(doing[:-1]):
            return True  # "practising" is a practice, and "practic" is not a word of its own
    return False


def doing_word(text):
    """The doing word in this line, in the words it is typed in, or None."""
    for word in topics.words(text):
        if _is_doing(word):
            return word
    return None


def asks_about_doing(text):
    """Whether this is a length ask about doing something, in the words it is typed in."""
    line = str(text or "")
    if not LENGTH_ASK.search(line):
        return False
    return doing_word(line) is not None


def _the_things(memory):
    """The things this chat has been about, newest first, as the words a line can be written on.

    A thing is what a doing in the chat is done with: the nouns of an earlier line that names
    something the person does ("started learning guitar" is a practice, and the guitar is what it
    is done with), minus the doing words themselves (the ask has its own), the time words and the
    grammar. A line with no doing in it names a state rather than the thing a practice is done
    with: "my fingers hurt" is what happened to the person, and "how long should i practise
    finger" is the bone-healing card, which is the fault this module exists for.
    """
    out = []
    for record in reversed((memory.get("topics") or [])[-LOOKBACK:]):
        text = record.get("text") if isinstance(record, dict) else None
        if not isinstance(text, str) or not text.strip():
            continue
        if doing_word(text) is None:
            continue  # a state, not a thing the chat has been doing something with
        for word in topics.keywords(text):
            if len(word) < 4 or word in TIME_WORDS or _is_doing(word):
                continue
            if word not in out:
                out.append(word)
    return out


def written_out(text, memory):
    """The line written out with each thing the chat is about, newest thing first.

    Empty when the line is not a length ask about doing something, when it names a thing of its
    own that is not the ask's grammar ("how long should i practise guitar" needs no rewrite), or
    when the chat has done nothing yet.
    """
    said = " ".join(str(text or "").split()).rstrip("?.! ")
    if not asks_about_doing(said):
        return ()
    if any(word not in ASK_WORDS and not _is_doing(word) for word in said.lower().split()):
        # the line names a thing itself, so it is not the bare ask this module writes out
        return ()
    if not isinstance(memory, dict):
        return ()
    out = []
    for thing in _the_things(memory):
        out.append(said + " " + thing + "?")
        out.append(said + " " + thing + " each day?")
    return tuple(out)


# --- a moan about their own doing of a thing -------------------------------------------------
# "i always get rice wrong", "i can never get pastry right", "i keep getting the timing wrong":
# the frame says a thing they do comes out badly, and the thing named is what they want to do
# properly. The ask behind it is the how-to about that thing, which the knowledge base already
# has a card for - "how do i get rice right" gets the rice card - so the moan is written out as
# that ask rather than answered with the intake form. The frame ("i always", "i can never", "i
# keep getting") is what makes it a moan rather than a statement: "i got the timing wrong" is
# news about a day, and is left to its own readers.
A_MOAN = re.compile(
    r"\bi (?:can\s+)?(?:never|always|keep|constantly|usually|often|still)\b"
    r"(?:\s+(?P<verb>getting|get|doing|do|making|make|cooking|cook|picking|pick|"
    r"finding|find|managing|manage))?\b"
    r"(?P<thing>[^?.!,]{1,40}?)"
    r"\s+(?:wrong|right|messed up|ruined|spoiled|spoilt|screwed up|backwards)\b", re.I)

# The verb the rewrite asks with, in the form the ask wants it: "i keep getting the timing wrong"
# is a question about getting the timing right, not about keeping it.
MOAN_VERB = {"getting": "get", "doing": "do", "making": "make", "cooking": "cook",
             "picking": "pick", "finding": "find", "managing": "manage"}


def the_ask_behind_a_moan(text):
    """The how-to ask behind "i always get rice wrong", or "" when the line is not that.

    Only the rewrite is offered; the caller looks it up and takes the answer only when it is
    about the thing the person named, because read loosely the rewrite reaches anything ("how do
    i get the kids to bed right" reaches the frost card, which is none of it).
    """
    said = " ".join(str(text or "").split())
    if not said or len(said.split()) > 12:
        return ""
    match = A_MOAN.search(said)
    if not match:
        return ""
    thing = match.group("thing").strip(" ,")
    if not thing.split() or len(thing.split()) > 4:
        return ""
    if not topics.keywords(thing):
        return ""  # a thing made of grammar only ("it", "that") names nothing to look up
    verb = (match.group("verb") or "get").lower()
    return "how do i " + MOAN_VERB.get(verb, verb) + " " + thing + " right?"
