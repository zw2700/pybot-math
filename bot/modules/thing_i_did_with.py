"""A thing the person did with, asked back in their own words.

    i ordered a coat in a medium last tuesday
    its too big across the shoulders
    ...
    which coat was it i ordered    -> the shop's coat-buying guide, the card the chat had
                                      already been given at the top, word for word again
    what coat did i order          -> the same card behind "Same as before:"
    what size coat did i order     -> the clothes size chart

The ask names a thing they told the chat about and asks what they did with it. Nothing in it is a
word the store reads as a question about the conversation ("say", "told", "remember", "again"), so
no reader of what was said claimed the line, and the answers entry that owns the word "coat" - or
"size" - took the turn and printed a card. Their own line is the answer.

The reading is narrow on purpose, and every part of it is needed:

* the shape is the thing **in front of** what they did - `what|which <thing> did i <verb>`, and
  `which <thing> was it i <verb>`. A `say`, `tell` or `mention` in the verb place is the ask for
  their own words, which has its own reader;
* a word in front of the thing that names which part of it is asked about ("what size coat") is
  dropped: no line of theirs says "size", theirs says "in a medium". With only the attribute and
  no thing ("and what size did i say") there is nothing to look a line up by, and the turn is
  left alone;
* **and the thing has to be in one of their own lines.** That is what makes this a recall rather
  than a question about the world: `what car did i buy` with no car said is still the motoring
  card, and it is left to the knowledge base.

The answer is the store's own idiom for their line ("You said: ..."), which is what the store
answers a recall with, and it is the whole line rather than a rewording: what they want back is
the detail they typed - the size, the day, the name - and a rewrite is where a detail goes
missing.
"""
import re

# Above the chatter band, below the memory store: the store's own recall of what was said leads
# the turn, and this answers only on lines it passes. It has to be above `answers`, because a
# specialist card that declares the chat's topic takes a line off a generalist underneath it -
# the coat guide did exactly that on "which coat was it i ordered".
PRIORITY = 6900

LEAD = r"^(?:and |so |but |also |oh |ok |okay )?"

# "what coat did i order", "which coat did i order", "what size coat did i order".
DID_WITH = re.compile(LEAD + r"(?:what|which) (?P<thing>[a-z][a-z' ]{1,24}?)\s*"
                      r"(?:did i|have i)\s+"
                      r"(?!said?\b|tell\b|told\b|mention\b|mentioning\b)(?P<did>[a-z]+)"
                      r"\s*[?.!]*$")

# "which coat was it i ordered", "which coat was it that i ordered".
WAS_IT_I = re.compile(LEAD + r"which (?P<thing>[a-z][a-z' ]{1,24}?)\s*"
                      r"(?:was it|is it|was that)\s+(?:that\s+)?i\s+"
                      r"(?!said?\b|tell\b|told\b|mention\b)(?P<did>[a-z]+)\s*[?.!]*$")

# The word in front of a thing that names which part of it is asked about rather than the thing.
ATTRIBUTE = frozenset("""size colour color brand make model number price cost amount weight
length width height age year month day date time""".split())

# A word that points back at what was said rather than naming a thing: "which one was it i
# ordered" has no thing of its own to look a line up by.
NOT_A_THING = frozenset("""one thing things bit bits part parts point way kind sort time other
else lot lots""".split())


def _thing(low):
    """The thing the ask is about, or "" when the line is not this shape."""
    for pattern in (WAS_IT_I, DID_WITH):
        match = pattern.match(low)
        if not match:
            continue
        words = [word for word in match.group("thing").split() if word]
        while len(words) > 1 and words[0] in ATTRIBUTE:
            words = words[1:]
        thing = " ".join(words).strip()
        if not thing or thing in ATTRIBUTE or thing in NOT_A_THING:
            return ""
        return thing
    return ""


def _did(low):
    """The doing in the ask: "what coat did i order" -> "order"."""
    for pattern in (WAS_IT_I, DID_WITH):
        match = pattern.match(low)
        if match:
            return match.group("did")
    return ""


def _stem(word):
    """The word with a plural or a participle taken off, so "coat" finds "coats"."""
    word = str(word or "").lower().strip("'")
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[:-len(suffix)]
    return word


def _says_it(tokens, thing):
    """True when every word of the thing is one of these tokens, in any of its forms."""
    stems = {_stem(token) for token in tokens}
    return all(_stem(word) in stems for word in thing.split())


def _the_line(thing, did, memory):
    """The line of theirs that names the thing, or "".

    A line that asks something is skipped: it names the thing and states nothing, and reading it
    back would answer the question with a question ("what coat should i get" a turn earlier).

    The line that says what they did is the answer, so a line with the doing in it wins over a
    later line that only names the thing: "i ordered a coat in a medium" over "the coat arrived
    scratched", when the ask is which coat they ordered. The newest line is the fallback - people
    say what they did, then talk about the thing.
    """
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    lines = []
    for turn in reversed(turns or []):
        line = str((turn or {}).get("user") or "").strip()
        if not line:
            continue
        if not _says_it(re.findall(r"[a-z']+", line.lower()), thing):
            continue
        if line.endswith("?") or _thing(" ".join(line.lower().split())):
            continue
        lines.append(line)
    if not lines:
        return ""
    doing = _stem(did)
    for line in lines:
        tokens = {_stem(token) for token in re.findall(r"[a-z']+", line.lower())}
        if doing in tokens:
            return line
    return lines[0]


def _times_said(line, memory):
    """How many of the last few replies already carry this line."""
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    said = line.lower()
    return sum(1 for turn in (turns or [])[-4:]
               if said in str((turn or {}).get("bot") or "").lower())


def _the_recall(text, memory):
    """The reply for a line that asks after what they did with a thing, or None."""
    low = " ".join(str(text or "").lower().split())
    if not low:
        return None
    thing = _thing(low)
    if not thing:
        return None
    line = _the_line(thing, _did(low), memory)
    if not line:
        return None
    quoted = '"' + line + '"'
    # Asking again on the next turn is the same line, not a new one, and the same sentence twice
    # in a row reads like a machine: the frame changes each time it is asked, so the reply is
    # never the one already on the screen.
    times = _times_said(line, memory)
    if times:
        return ("Still the same one: ", "Same line again: ")[times % 2] + quoted
    return "You said: " + quoted


def takes_as_it_comes(text, memory):
    """True on exactly the lines `respond` answers, and nowhere else.

    The coat guide declares the topic a coat chat is read as, and a card that declares the line
    takes it off a module underneath it whatever the bands say (`arbiter._as_it_comes`). On these
    lines the ask is about what the person did, so nothing about the world can answer it: the
    module says so rather than raising `PRIORITY` over every other line it reads.
    """
    return _the_recall(text, memory) is not None


TAKES_AS_IT_COMES = takes_as_it_comes


def respond(text, memory):
    """The thing they did with, when they told the chat about it, else None.

    Never a line the store can already answer. `what phone have i got` after "my phone is a
    pixel" is a recall the store reads better than this does - it says the thing back in the
    chat's own words ("Your phone is a Pixel.") where this hands back the line it was said in
    ("You said: \"my phone is a pixel\""). The ask is the same shape as the coat one that this
    module exists for, so the only difference between them is which reader has the line, and the
    reader that already has it wins.
    """
    from . import memory_store
    low = " ".join(str(text or "").lower().split()).strip(" ,.;:!?")
    if memory_store.respond(low, memory):
        return None
    return _the_recall(text, memory)
