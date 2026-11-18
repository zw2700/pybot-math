"""A doneness ask names a state and no dish, so it is read against the dish the chat is on.

    im cooking a roast chicken for six on sunday
      About 20 minutes per 500g plus 20 minutes at 190C ... check the thigh juices run clear.
    its about two kilos
      About two kilos, then. ...
    and how do i know its cooked
      Chicken is cooked when the thickest part reaches 75C on a digital thermometer ...

The last line asks about a state ("cooked") and names nothing, so on its own words it reaches
no entry and the person is told the bot would rather not guess - about the roast it has just
given the timings for. The dish is in the chat, so its own word goes in front of the line
("chicken how do i know its cooked") and the reading in memory carries that.

The fill is written to `memory["understood"]` by an observer, because that is the reading every
module below answers from: the answers, the composer and the store's own recall all read it, so
a fill-in written anywhere else would only move one of them. The module answers nothing itself
- it has no `respond` - so it can only ever change how a line is read, never take a turn.

The rule is general, not a list of dishes. A word from the chat's own topic counts only when all
three hold:

1. the entry it reaches is keyed to the word;
2. that key is the entry's *first* group, the thing the entry is about, not the words it is
   asked by, so "oven how will I know when it's done" does not reach the when-to-buy entry
   through "when";
3. the entry is keyed to a done state ("done", "cooked", "ready", "temperature", ...).

A line that names its own dish needs nothing filled in, so it is left exactly as it came in,
and a chat with no such dish ("we are out all day" / "is it ready yet") keeps the answer it
already had.
"""
import re

from ..memory import topics as _topics

# The reading is written by the store's observer, which runs at 7000, and every reader below
# this one answers from what is in memory when it runs: this has to be the next observer after
# the store's, not one that happens to sort near it.
PRIORITY = 6900

# How a doneness ask is put: "how will I know when it's done", "when is it ready", "is it
# cooked yet". The state is what the line asks about and the thing is what it leaves out.
A_DONENESS_ASK = re.compile(
    r"\b(?:how (?:will|would|do|can|should) (?:i|you) (?:know|tell)|when (?:will|do) (?:i|you) know|"
    r"when (?:is|will) it(?: be)?|is it|are they|will it be|how long (?:do|should) (?:i|you) "
    r"(?:cook|leave|bake|roast|boil|fry|grill|simmer))", re.I)
# The state itself, said as a past participle or as "ready": the word that makes the line a
# question about how the thing turned out rather than about what to do with it.
DONENESS_WORDS = re.compile(
    r"\b(?:done|dones|cooked|uncooked|overdone|undercooked|overcooked|ready)\b", re.I)
# What an entry has to be keyed to be the answer to a doneness ask. "oven how will I know when
# it's done" reaches the when-to-buy entry through "when", which is how the ask is put and not
# what it asks: only an entry that says how the thing has turned out is the one to widen to.
DONENESS_KEYS = ("done", "cooked", "cooked through", "ready", "how can i tell",
                 "how do i tell", "how do you tell", "when is it done", "when its done",
                 "temperature", "temp", "thermometer")


def _entry(text):
    """The knowledge entry a line reaches, or None (the knowledge base is read, not changed)."""
    from ..knowledge.lookup import find  # lazy: this module only needs it when a state is asked
    said = " ".join(str(text or "").lower().split())
    if not said:
        return None
    return find({"clean": said, "words": _topics.words(said)})


def _the_answer_to_lean_on(memory):
    """The bot's last reply, or ''."""
    for one in reversed((memory or {}).get("turns") or ()):
        said = str((one or {}).get("bot") or "")
        if said:
            return said
    return ""


def _the_topics_on_the_chat(memory):
    """The topic in hand first, then the ones the chat has been on, newest first."""
    out = []
    for one in reversed((memory or {}).get("topics") or ()):
        said = str((one or {}).get("text") or "")
        if said and said not in out:
            out.append(said)
    record = (memory or {}).get("topic")
    said = str(record.get("text") or "") if isinstance(record, dict) else ""
    if said in out:
        out.remove(said)
    if said:
        out.insert(0, said)
    return out


def _key_groups(item):
    """The groups of phrases an entry is keyed by, in the order the entry says them."""
    groups = []
    for part in getattr(item, "key", ()) or ():
        if isinstance(part, str):
            groups.append((part,))
        elif isinstance(part, (tuple, list)):
            groups.append(tuple(one for one in part if isinstance(one, str)))
    return groups


def _keys_the_word(phrases, word):
    """Whether a key group holds the word, in any of the forms it takes ("cooked" for "cook")."""
    word = str(word or "")
    if not word:
        return False
    said = set()
    for phrase in phrases:
        said.update(_topics.words(phrase))
    if word in said:
        return True
    for one in said:
        try:
            if word in _topics.forms(one) or one in _topics.forms(word):
                return True
        except Exception:  # noqa: BLE001 - a word the stemmer does not like simply does not match
            continue
    return False


def _about_the_thing(item, word):
    """True when the entry's first key group is the word as the thing it is about.

    An entry's first group is the thing and the groups after it are how the thing is asked
    about, so "roast how will I know when it's done" reaches the general roasting entry through
    a word of its ask group, where the dish is a word it happens to mention. Only the first
    group says the entry is about the word.
    """
    groups = _key_groups(item)
    return bool(groups) and _keys_the_word(groups[0], word)


def _says_how_it_turns_out(item):
    """True when the entry is keyed to a done state, not only to the thing.

    A group holds the state as it is written ("cooked through", "how can i tell"), so every
    word of the state has to be in one group: a "cook" somewhere and a "through" somewhere else
    is not the entry that says how the thing turns out.
    """
    for group in _key_groups(item):
        said = set()
        for phrase in group:
            said.update(_topics.words(phrase))
        for one in DONENESS_KEYS:
            if set(_topics.words(one)) <= said:
                return True
    return False


def _the_thing_words(memory, said_words):
    """The words of the things the chat has been on, newest first, that the line does not say."""
    out = []
    for topic in _the_topics_on_the_chat(memory):
        for word in _topics.keywords(topic):
            if word in said_words or word in _topics.MEASURE_WORDS or word in out:
                continue
            out.append(word)
    return out


def _the_chat_has_moved_on(found, memory):
    """True when the last thing the chat was about reaches an entry in another domain.

    The search walks every topic the chat has been on, so after the subject has changed an old
    dish comes back: "im doing a roast chicken for six on sunday" / "how long do i cook it" /
    "also my car needs a service" / "is it ready yet" has the car's "it", and a temperature for
    the chicken is a confident answer about a thing the person has left. A wrong subject is worse
    than the hedge it replaces.

    The test is the newest topic that reaches an entry at all - the ask itself reaches none, and
    neither does a line that only says how the oven is running, so neither of those is a move: in
    a lamb roast, "my oven runs a bit cool" leaves the roast as what the chat is on.
    """
    said = " ".join(str((memory or {}).get("understood", {}).get("clean") or "").split())
    mine = str(getattr(found, "domain", "") or "")
    if not mine:
        return False
    for topic in _the_topics_on_the_chat(memory):
        topic = " ".join(str(topic or "").split())
        if not topic or topic == said:
            continue
        here = _entry(topic)
        if here is None:
            continue
        theirs = str(getattr(here, "domain", "") or "")
        return bool(theirs) and theirs != mine
    return False


def the_done_state_of_the_thing_in_hand(line, memory):
    """The doneness ask with the word of the thing the chat is on in it, or "".

    "and how will I know when it's done" after "a slow roast shoulder of lamb" names a state
    and no dish, so it reached nothing and the person was told the bot would rather not guess
    about its own roast answer. The dish is in the chat, so its own word is put in front of the
    line: "lamb how will i know when its done" is the lamb temperature entry.
    """
    said = " ".join(str(line or "").lower().split())
    if not said or not A_DONENESS_ASK.search(said) or not DONENESS_WORDS.search(said):
        return ""
    if not _the_answer_to_lean_on(memory):
        # Nothing has been answered yet, so there is no dish in the chat to read the line
        # against: a first message is answered from its own words.
        return ""
    said_words = set(_topics.words(said))
    for word in _the_thing_words(memory, said_words):
        for filled in (word + " " + said, said.rstrip("?.! ") + " " + word):
            found = _entry(filled)
            if found is None:
                continue
            if not _about_the_thing(found, word):
                continue
            if not _says_how_it_turns_out(found):
                continue
            if _the_chat_has_moved_on(found, memory):
                return ""
            return filled
    return ""


def observe(line, memory):
    """Read a doneness ask against the dish the chat is on, and write that reading down."""
    if not isinstance(memory, dict):
        return
    read = memory.get("understood")
    if not isinstance(read, dict):
        return
    said = str(read.get("clean") or read.get("text") or line or "")
    filled = the_done_state_of_the_thing_in_hand(said, memory)
    if not filled:
        return
    reading = dict(read)
    reading["clean"] = filled
    reading["words"] = _topics.words(filled)
    if "norm_text" in reading:
        reading["norm_text"] = filled
    memory["understood"] = reading
