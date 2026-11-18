"""A line that asks to be reminded of the thing they told us about, and not about the world.

"my boiler keeps losing pressure" then "what was wrong with my boiler again" is the person
going back over what they said: the past tense and the "again" are the reminder, and the answer
they want is their own line. Read as a question about the world it is a fault to diagnose, so
the answers lane took it and handed back the flow-temperature card, and the store - which had
the boiler on file - was never asked.

The reading is a shape, not a phrase. What makes a line this ask is all three of:

  * a past-tense ask ("what was", "what did", "remind me what was"),
  * an ask about a thing's state rather than its price or its recipe ("wrong", "up", "the
    problem", "happening", "keep doing"), and
  * a thing named after "with" - "with my boiler", "with the car", "with it" - where the thing
    is one they really did say something about earlier. A boiler they only heard the bot
    mention is not theirs to be reminded of, and a present-tense "what's wrong with my boiler"
    is a fault to diagnose, not a reminder: only the past tense and the reminding frames below
    (with "again", with "remind me") make it about the chat.

A pronoun is the thing the understanding engine resolved it to (`memory["understood"]["ref"]`),
which is how "what was wrong with it again" reaches the boiler and not the last line said.
"""
import re

from . import recent
from .topics import content, forms, stem

# The thing, named after "with": "my boiler", "the car", "our kitchen". Three words at most, so
# a whole clause after "with" is not the thing ("what was wrong with the way they spoke to me").
WITH_THE_THING = re.compile(
    r"\bwith\s+(?:((?:my|our|the)\s+[a-z][a-z'\-]*(?:\s+[a-z][a-z'\-]*){0,2})|"
    r"(it|that|this|them|those))\b", re.I)
# The words the thing carries that say nothing about which thing it is, or that point at the
# remembering rather than the thing: "with the boiler again" names the boiler.
TRAILING = frozenset("""again before earlier already then yesterday today please so far
until up now one ones thing things stuff lot""".split())
EMPTY = frozenset("one ones thing things stuff lot".split())
# The ask is about the state of the thing. "what was wrong with", "what was up with", "what was
# the problem with", "what was happening with", "what the boiler kept doing". A price, a colour
# or a recipe is a question about the world and is left to the entries.
STATE_ASKS = re.compile(
    r"\b(?:wrong|up|(?:the\s+)?(?:problem|matter|issue|fault|trouble|deal)|happen\w*|going\s+on|"
    r"doing|keep\s+doing|kept\s+doing|said\s+about)\b", re.I)
# The same for the telling: the words a line uses when something is wrong with the thing. A
# reminder asks what was wrong, so the line quoted back has to be one that says something was.
# The words are the ones people use about a fault, a part that has gone and a body that hurts.
STATE_SAID = re.compile(
    r"\b(?:keep\w*|kept|won'?t|wont|stopped|stopping|not\s+work\w*|doesnt\s+work\w*|"
    r"hurts?|hurting|sore|pain\w*|aches?|aching|swell\w*|swollen|stiff|"
    r"broken|broke|breaks?|cracked|leak\w*|drip\w*|dripping|slip\w*|slipped|jammed|stuck|"
    r"went|gone|dying|dead|failed|failing|crash\w*|dragging|drains?|drained|"
    r"struggl\w*|worr\w*|sort\w*|sorted|fault\w*|wrong|issue\w*|problem\w*|trouble|"
    r"stinks?|stink\w*|smell\w*|noise\w*|noisy|squeak\w*|rattle\w*|vibrat\w*|"
    r"slow\w*|weak\w*|blocked|clogged|mould\w*|damp)\b", re.I)
# The ask in the tense of the telling. "was"/"were"/"did"/"has" and not "is"/"does": a fault
# asked about in the present ("what's wrong with my boiler") is a diagnosis, which the answers
# lane answers better than a quote of the line does.
IN_THE_PAST = re.compile(
    r"^(?:and |so |but |also |ok |okay )?(?:what|whats|which)\s+(?:was|were|did|has|have|had)\b"
    r"|\b(?:what|whats)\s+(?:was|were)\b", re.I)
# The words that make it a reminder rather than a first question. "again" is how people ask for
# a thing a second time, and the reminder is what they want when they cannot place it.
AGAIN = re.compile(r"\b(?:again|before|earlier|remind me|remind me again|"
                   r"(?:cant|can not|cannot|dont|do not) remember|"
                   r"what did i say|what did i tell you)\b", re.I)
REMINDING = re.compile(r"\b(?:remind me|(?:cant|can not|cannot|dont|do not) remember)\b", re.I)
# The thing named as theirs, straight after the ask: "remind me what my bike problem was",
# "what was my boiler issue again". People say it this way when the thing is theirs and the ask
# is a reminder, so the "with" shape never turns up and the reading above never sees it: "remind
# me what my bike problem was" after "my bike chain keeps slipping" was answered "No hands on
# this end, so the job itself can't be mine" - a punt, with their own line four turns back. The
# phrase stops at the word that says which state is asked about, because that word is the ask's
# rather than the thing's.
THEIR_THING = re.compile(
    r"\b(?:what|whats|which)\s+(?:was|were|is|are|did|does|has|have|had|d)\s*"
    r"((?:my|our)\s+[a-z][a-z'\-]*(?:\s+[a-z][a-z'\-]*){0,3})\b"
    r"|\b(?:what|whats|which)\s+((?:my|our)\s+[a-z][a-z'\-]*(?:\s+[a-z][a-z'\-]*){0,3})\b",
    re.I)
# The words that end the thing and belong to the ask ("my bike problem", "my boiler issue"): the
# thing is "my bike", and "problem" says what is wanted about it. They are dropped off the end of
# the phrase, longest run first, so a thing that is itself called one of these keeps its name.
ASK_WORDS = frozenset("""problem problems matter issue fault trouble deal going happening doing
wrong up again before earlier then so far please""".split())
# What can end the phrase without being part of the thing: the ask's own words and the copula the
# reminder is built on ("what my bike problem was"). Only the copula, so a thing called "up" keeps
# its name.
THING_TAIL = ASK_WORDS | frozenset("was were is are be been being did does has have had".split())

# The thing done, rather than its state: "what did the boiler keep doing again". The thing is
# named straight after "did", so this shape has no "with" in it.
WHAT_IT_DID = re.compile(
    r"\b(?:what|whats)\s+(?:did|does|has|have)\s+((?:my|our|the)\s+[a-z][a-z'\-]*"
    r"(?:\s+[a-z][a-z'\-]*){0,2}?)\s+(?:keep\s+|kept\s+)?(?:doing|do|say|saying)\b", re.I)


def _trim(words):
    """The named thing without the words that point at the remembering rather than the thing."""
    kept = [word for word in str(words or "").split() if word.lower() not in TRAILING]
    return " ".join(kept).strip(" .,!?")


def _said_before(thing, memory):
    """True when one of their own earlier lines names this thing.

    The guard is what keeps the reading to the chat: a boiler the bot mentioned, or one named
    for the first time in the ask itself ("my boiler is making a noise again" / "what was wrong
    with my boiler again" in the same breath), has no line of theirs to be reminded of.
    """
    words = [word for word in content(thing) if word not in EMPTY]
    if not words:
        return False
    for turn in recent(memory, 12):
        line = turn.get("user") if isinstance(turn, dict) else None
        if not line:
            continue
        said = set(content(line))
        if all(any(word == seen or forms(word) & forms(seen) or stem(word) == stem(seen)
                   for seen in said) for word in words):
            return True
    return False


def the_thing(text, memory=None):
    """The thing a reminder is about ("my boiler", "the car", "it"), or None when the line is
    not a reminder about a thing they named.

    The reading is shared by the gate that says the line is about the chat (the store's
    `_about_this_chat`) and the reply that quotes the line (`_recall_reply`), so the two cannot
    disagree about which lines are reminders.
    """
    line = " ".join(str(text or "").lower().split())
    if not line:
        return None
    if not STATE_ASKS.search(line):
        return None
    if not (IN_THE_PAST.search(line) or REMINDING.search(line)):
        return None
    # "again", "remind me", "i can't remember": the words that ask for a thing a second time.
    # Without one of them the line is the first question about the thing, and a first question
    # about a fault is the answers lane's turn.
    if not AGAIN.search(line):
        return None
    thing = ""
    named = WITH_THE_THING.search(line)
    if named:
        if named.group(1):
            # "again" and the other pointing words are the ask's, not part of the thing, and
            # they would be searched for in the person's lines as if they were.
            thing = _trim(named.group(1))
        else:
            # A pronoun is the thing the understanding engine resolved: "what was wrong with it
            # again" after the boiler is about the boiler.
            thing = _resolved(named.group(2), memory)
    else:
        did = WHAT_IT_DID.search(line)
        if did:
            thing = _trim(did.group(1))
        else:
            theirs = THEIR_THING.search(line)
            if theirs:
                thing = _the_thing_itself(theirs.group(1) or theirs.group(2))
    # The thing named in the ask is not the thing told: "what was wrong with my boiler again"
    # said in the same breath as the news has nothing to be reminded of.
    if not thing or not content(thing):
        return None
    return thing


def _the_thing_itself(phrase):
    """The thing out of "my bike problem": the phrase without the words that ask about its state."""
    words = [word for word in str(phrase or "").split() if word]
    while len(words) > 1 and words[-1].strip(".,!?").lower() in THING_TAIL:
        words = words[:-1]
    return _trim(" ".join(words))


def _resolved(pronoun, memory):
    """The thing a pronoun points at, as the understanding engine read it."""
    if not isinstance(memory, dict):
        return ""
    read = memory.get("understood")
    if not isinstance(read, dict):
        return ""
    ref = read.get("ref")
    if not isinstance(ref, dict):
        return ""
    value = ref.get(str(pronoun or "").lower())
    if isinstance(value, str) and value.strip():
        return _trim(value)
    return ""


def _said_what_was_wrong(thing, memory):
    """True when one of their own lines says something happened to this thing.

    The reminder names a thing and asks for its state, so the chat has to hold the state as well
    as the name. A line that only mentions the thing in passing does not: asking "what was my
    bike problem again" after "my bike is red" was answered `You said: "my bike is red"` - a
    claim the chat does not support, since nothing was said to be wrong with the bike. With no
    line of theirs saying so, the reading is not a reminder at all and the turn goes to whoever
    the words belong to, which is where the ask was answered before.
    """
    words = [word for word in content(thing) if word not in EMPTY]
    if not words:
        return False
    for turn in recent(memory, 12):
        line = turn.get("user") if isinstance(turn, dict) else None
        if not line or not STATE_SAID.search(line):
            continue
        said = set(content(line))
        if all(any(word == seen or forms(word) & forms(seen) or stem(word) == stem(seen)
                   for seen in said) for word in words):
            return True
    return False


def about_a_thing_they_said(text, memory=None):
    """True when the line is a reminder about a thing of theirs, so the chat is what it asks
    about rather than the world."""
    try:
        thing = the_thing(text, memory)
        return bool(thing) and _said_before(thing, memory) and _said_what_was_wrong(thing, memory)
    except Exception:  # noqa: BLE001 - a reading that fails claims nothing
        return False
