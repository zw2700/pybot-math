"""A line that takes the chat back to something said earlier, and asks about it.

    im going to lisbon in may
    my son starts school in september
    back to lisbon, what should i see

The last line names the thing it returns to and then asks about it. Read whole, it reached the
back-pain entry: "back" is the return in "back to", not the body part, and the thing the person
named - Lisbon - never got to the question. So `find()` answered "A back like that: give it two
to six weeks". The same shape is a hedge when the thing does have an entry but the question no
longer names it: "so about the washing machine, what should i get" reached nothing at all.

What this reads is the two parts separately: the opener is the return, the thing after it is what
the question is about, and the ask is the rest. The ask is then put back together with the thing
in it - after the first question word when the ask has one ("what should i get" / "washing
machine" -> "what washing machine should i get", which is how English asks it), and at the end
otherwise ("what should i see" + "lisbon") - and only a version that reaches a real entry, that
names the thing, and that is not the entry the whole line already reached, is handed on.

Nothing is invented: the ask is the person's words and the reply comes from the entry. A line
with no ask ("back to lisbon" alone), a thing the chat never mentioned, or no entry for it all
leave the turn exactly as it was.
"""
import re

from . import topics

# The ways a person takes the chat back. Each one is an opener only: a word that says the return
# ("back to", "as for", "anyway about") and then the thing they are going back to. A bare "about"
# is here because people type "about the washing machine, what should i get", but it is only ever
# taken with a comma in the line, so a line that opens on "about 20 minutes" is somebody else's.
OPENERS = re.compile(
    r"^\W*(?:(?:and|but|so|ok|okay|right|alright|well|now)\s+)*"
    r"(?P<opener>back\s+to|back\s+on|returning\s+to|as\s+for|(?:anyway|so)\s+about|about)"
    r"\s+(?P<rest>[^.?!]+.*)$",
    re.I,
)

# The store frames a line it has carried as a question before the modules see it ("what about back
# to lisbon" for "back to lisbon"), so a return can arrive under that lead-in. It is the same
# return: the framing is the store's, not the person's, and both readers take it off first.
STORE_FRAME = re.compile(
    r"^(?:and\s+|so\s+)?(?:what|how)\s+about\s+"
    r"(?=(?:back\s+(?:to|on)|returning\s+to|as\s+for|(?:anyway|so)\s+about|about)\b)",
    re.I,
)


# The words that make the thing a thing rather than a name: "the dog", "my washing machine".
# They stay in the line the person reads but are not what the entry is keyed on.
POINTER = frozenset("""the a an my our your his her its their this that these those some any""".split())

# The first word of an ask is the question word, and the thing goes straight after it: "what
# washing machine should i get" is the ask, "what should i get washing machine" is not.
# The ask's own opener: the question word, or the verb of a line that asks without one.
ASK_OPENS = re.compile(r"^(?:what|which|whose|how\s+much|how\s+many|where|when|who|why|should|"
                       r"can|could|do|does|did|is|are|will|would)\b", re.I)

# A pronoun names nothing: "back to it" is the thing the chat is already on, and the ask alone is
# what the store's own follow-up readers are for.
NOTHING_NAMED = frozenset("""it its that this these those they them there their one ones
he she him her his anything something everything""".split())


def _the_chat_has(words, memory):
    """True when the chat has said one of these words, so the return points at something real."""
    if isinstance(memory, dict):
        for turn in memory.get("turns") or ():
            if not isinstance(turn, dict):
                continue
            said = set(topics.words(turn.get("user") or "")) | set(topics.words(turn.get("bot") or ""))
            if said.intersection(words):
                return True
    return False


def _the_parts(text):
    """The thing the line goes back to, and the ask after it, or None.

    Both orders people use are here: the comma ("back to lisbon, what should i see") and the ask
    straight after the thing ("back to lisbon what should i see"), where the split is at the
    first question word.
    """
    match = OPENERS.match(STORE_FRAME.sub("", str(text or "")))
    if not match:
        return None
    rest = match.group("rest").strip()
    if not rest:
        return None
    thing, ask = None, ""
    if "," in rest:
        thing, ask = rest.split(",", 1)
    else:
        found = re.search(r"\s+(?=(?:what|which|where|when|who|why|how|should|can|could|do|does|is|"
                          r"are|will|would)\b)", rest, re.I)
        if found:
            thing, ask = rest[:found.start()], rest[found.start():]
    if thing is None:
        return None
    thing = thing.strip(" ,.:;?!")
    ask = ask.strip(" ,.:;?!")
    if not thing or not ask:
        return None
    if match.group("opener").lower().strip() == "about" and "," not in rest:
        # A bare "about" is only a return when the thing and the ask are split off from it.
        return None
    named = [word for word in topics.words(thing) if word not in POINTER]
    if not named or set(named) <= NOTHING_NAMED:
        return None
    return named, ask


def _the_lines(named, ask):
    """The ask with the thing written into it, in the orders worth trying.

    Only the orders English uses. "what" and "which" take the thing straight after them ("what
    washing machine should i get"), "how much" and "how many" the same ("how much paint will the
    front room need"), and any other ask takes the thing at its end ("where should i eat" +
    "lisbon"). A length ask is not written at all: "how long will it take" + "weight" is no
    question anyone asks, and the entry it would reach answers how to lose weight rather than how
    long it takes.
    """
    thing = " ".join(named)
    measure = re.match(r"^(how\s+(?:much|many))\s+(.+)$", ask, re.I)
    if measure:
        return [(measure.group(1) + " " + thing + " " + measure.group(2)).strip()]
    first, space, after = ask.partition(" ")
    if first.lower() in ("what", "which", "whose"):
        return [(first + " " + thing + " " + after).strip(), (ask + " " + thing).strip()]
    if re.match(r"^how\b", ask, re.I):
        return []
    return [(ask + " " + thing).strip()]


def _the_domain_of_the_chat(named, memory):
    """The domain of the entry the chat's own line about this thing reached, or "".

    A thing is not always a thing. "back to the house, what should we offer" was written into
    "what should we offer house", and the entry that names a house is the one on house music: the
    person buying a house was handed a Daft Punk album. What the chat already knows about the
    thing is the line that named it, and the entry that line reached is filed under a domain -
    the house was `money`, the music is `entertainment`. A return stays in the domain of the line
    that named the thing; where that line reached nothing there is nothing to check against and
    the line is left to stand on its own words.
    """
    if not isinstance(memory, dict):
        return ""
    said = set(named)
    for turn in reversed(list(memory.get("turns") or ())):
        if not isinstance(turn, dict):
            continue
        line = turn.get("user") or ""
        if not said.intersection(topics.words(line)):
            continue
        try:
            item = topics._entry(line)
        except Exception:  # noqa: BLE001 - a line that cannot be read tells us nothing
            return ""
        return str(getattr(item, "domain", "") or "") if item is not None else ""
    return ""


def a_return_to_the_topic(text, memory):
    """The ask with the thing the line goes back to written into it, or "".

    One line only: the first version that reaches an entry which the whole line does not, and
    which the thing brought with it. Everything else leaves the turn exactly as it was.
    """
    parts = _the_parts(text)
    if not parts:
        return ""
    named, ask = parts
    if not _the_chat_has(set(named), memory):
        return ""
    try:
        whole = topics._entry(text)
        without = topics._entry(ask)
    except Exception:  # noqa: BLE001 - a line the knowledge base cannot read is not answered
        return ""
    domain = _the_domain_of_the_chat(named, memory)
    for line in _the_lines(named, ask):
        try:
            item = topics._entry(line)
        except Exception:  # noqa: BLE001
            continue
        if item is None:
            continue
        if whole is not None and item is whole:
            # The line already reached this entry, so the thing was never what it was about:
            # "back to the dog, how much is a rescue" is answered about the rescue already.
            continue
        if not topics._names_it(line, item) and without is not None and without is item:
            # The entry is the one the ask reaches without the thing in it, and the line does not
            # name it: the thing was carried along and did no work, so nothing was asked about it.
            continue
        if domain and str(getattr(item, "domain", "") or "") != domain:
            # Another sense of the thing's word: the chat is about a house you buy, and this entry
            # is about house music.
            continue
        return line
    return ""


def the_thing_named(text):
    """The thing the line goes back to, as the person typed it, or ""."""
    match = OPENERS.match(str(text or ""))
    if not match:
        return ""
    rest = match.group("rest").strip()
    if "," not in rest:
        return ""
    return rest.split(",", 1)[0].strip(" ,.:;?!")


# A "how much" or "how many" ask is answered by the sentence that carries a quantity, and in a
# card about a job that sentence is often the second one: the paint card opens on the tools and
# keeps "One litre of emulsion covers about 12 square metres" for its second sentence, so the
# opening sentence, handed back as the answer, gave the amount nowhere.
QUANTITY_ASK = re.compile(r"^\s*(?:how\s+(?:much|many)|what\s+(?:weight|size|length|price|"
                          r"quantity))\b", re.I)
A_NUMBER = re.compile(r"\b(?:\d|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                      r"half|a couple|a few)\b", re.I)


def _the_sentence_with_the_amount(answer):
    """The sentence of `answer` that gives the amount, or "" when none of them does."""
    for sentence in re.split(r"(?<=[.!?])\s+", str(answer or "")):
        if sentence.strip() and A_NUMBER.search(sentence):
            return sentence.strip()
    return ""


def as_the_same_answer(reply, text, short=None):
    """The answer framed as the same one, for a return that lands on what is already on screen.

    A return can reach the very answer the person already has, and handing it back word for word
    is not a second answer (STYLE.md). The lead-in says the answer has not changed and keeps the
    thing named, and `bot/memory/again.py` already carries both wordings - the one that says the
    answer covers the thing, and the one that says the entry has nothing separate for it.
    """
    from . import again as same_again

    thing = the_thing_named(text) or "that"
    # The answer may already carry a lead-in from the module that wrote it, and a second one on
    # top reads as a stutter ("Same answer, and it covers this: Same as before: ...").
    #
    # `short` is the sentence the rewritten ask is answered by, when the caller can work it out.
    # The opening sentence of an answer is not always the one the ask is about: asked "back to the
    # paint, how much will i need", the paint card opens on the tools and its coverage sentence is
    # the second one, so the opening handed back said "it covers this" and gave the amount nowhere.
    ask = (_the_parts(text) or ("", ""))[1]
    if ask and QUANTITY_ASK.match(ask) and not A_NUMBER.search(str(short or "")):
        # Whatever sentence the caller picked, a "how much" ask is not answered by one without a
        # number in it. The paint card's opening is the tools, and it is the sentence a picker
        # that matches words hands back, because "paint" is in the line and "emulsion" is not.
        short = _the_sentence_with_the_amount(reply) or short
    short = same_again._short(short or same_again.unframed(reply) or str(reply or ""))
    # The lead-in may only name what the answer names, and the answer decides how much of the
    # line's phrase is a name: "back to the scratching post help" names "the scratching post".
    # The dictionary is the whole answer, not only the sentence handed back: a "how much" ask
    # takes the amount sentence, which can say "emulsion" and never "paint" while the card's
    # opening names the paint. Naming the person's own word back is what the lead-in is for.
    named = same_again.the_name_the_answer_says(short, thing, card=reply)
    if not named or named.lower() in short.lower():
        # The answer already names the thing, so the lead-in does not name it again: "Same for
        # lisbon: In Lisbon: ..." says the same word twice in nine. And where the answer names
        # none of the thing, there is nothing the lead-in could name.
        return same_again.AGAIN[0].format(reply=short)
    return same_again.DETAIL_AGAIN[1].format(detail=named, reply=short)


def a_bare_return(text, memory=None):
    """True when the line only takes the chat back to a thing and asks nothing about it.

    "back to lisbon" on its own names the thing and stops. There is no ask for the thing to be
    written into, so nothing of the answer is being asked about either: read for a detail, the
    line found the word "back" and said "Nothing separate for back - it is the same advice: In
    Lisbon: ..." to a person who had only said which thing they meant, and "about the boiler"
    was read for the word "about". A return with no ask names no part of an answer.
    """
    match = OPENERS.match(STORE_FRAME.sub("", str(text or "")))
    if not match:
        return False
    rest = match.group("rest").strip()
    if not rest or "," in rest:
        return False
    if re.search(r"\b(?:what|which|where|when|who|why|how|should|can|could|do|does|did|is|are|"
                 r"will|would)\b", rest, re.I):
        return False
    named = [word for word in topics.words(rest) if word not in POINTER]
    if not named or set(named) <= NOTHING_NAMED:
        return False
    return bool(memory is None or _the_chat_has(set(named), memory))
