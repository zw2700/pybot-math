"""A plan with something still missing is the question the person did not ask.

People announce the occasion and the gap in one breath, and the store files both:

    ive got a wedding in 3 weeks and i still havent got an outfit
      -> "Noted: you've got a wedding in 3 weeks and you still haven't got an outfit."

Filing it is right - the follow-up turns need the wedding and the deadline - but it is not an
answer, and the ask they left out is one the knowledge base already has:

    what should i wear to a wedding in 3 weeks
      -> "White and cream are the one thing to avoid at a wedding ..."
    what should i get for a wedding
      -> "About fifty pounds is the usual gift from a friend ..."

So a line that names what it has not got, and names an occasion it is for, is read as that
question and answered from the entry it reaches. Three rules keep it honest: the line has to say
in its own words that the thing is not got yet (not that it is wanted, not that it is lost), the
thing has to be one of the kinds an occasion actually raises - something worn, or something given
- and the rewritten question has to reach an entry, because a plan the knowledge base has nothing
for is left to the reply that files it, exactly as before.
"""
import re

from ..knowledge import lookup
from ..understanding import understand
from . import plans

# What is not got yet, said the way people say it: "still havent got an outfit", "havent sorted a
# suit", "dont have a present yet", "no outfit yet".
_NOT_GOT = (
    re.compile(r"\b(?:still\s+)?(?:havent|haven't|hasnt|hasn't|aint|ain't)\s+"
               r"(?:got|gotten|had|bought|sorted|ordered|found|booked|chosen|picked)\s+"
               r"(?P<thing>[a-z][a-z' -]*)$", re.I),
    re.compile(r"\b(?:dont|don't|do\s+not|doesnt|doesn't)\s+have\s+(?P<thing>[a-z][a-z' -]*)$",
               re.I),
    re.compile(r"\b(?:not|n't)\s+(?:got|gotten)\s+(?P<thing>[a-z][a-z' -]*)$", re.I),
    re.compile(r"\b(?:no|without)\s+(?P<thing>[a-z][a-z' -]*?)\s+yet\b", re.I),
    # "im going to a wedding in june and i need an outfit" names the same gap as "havent got an
    # outfit": the occasion is what makes it a requirement rather than a want.
    re.compile(r"\b(?:need|needs|needed)\s+(?P<thing>[a-z][a-z' -]*)$", re.I),
)
# The occasion the rest of the line names: "ive got a wedding in 3 weeks", "we're going to a
# christening", "for my sister's wedding". The phrase is kept as it was said, so the deadline the
# person gave is part of the question.
_OCCASION = re.compile(
    r"\b(?:got|have|having|going\s+to|off\s+to|invited\s+to|for|at)\s+"
    r"(?P<occ>(?:a|an|the|my|our|his|her|their)\s+[a-z0-9][a-z0-9' -]{2,40})",
    re.I)

# The same occasion named as the subject of the clause: "the wedding is in 3 weeks", "my sister's
# wedding is next month".
_OCCASION_HEAD = re.compile(
    r"^(?P<occ>(?:a|an|the|my|our|his|her|their)\s+[a-z][a-z0-9' -]{1,30}?)"
    r"(?:\s+(?:is|are|was|will\s+be|'s)\b.*)?$", re.I)

# The kinds of missing thing an occasion raises, and the question that asks about it. A missing
# thing outside these is not read: "i still havent got my exam results" is not an ask about what
# to wear, and the entry the rewrite would reach could be about anything.
WORN = frozenset("""
outfit outfits dress dresses suit suits shirt shirts blouse blouses top tops skirt skirts
trousers pants shoes heels hat hats coat coats jacket jackets tie ties frock frocks jumpsuit
clothes clothing gown gowns boots sandals something
""".split())
GIVEN = frozenset("""
present presents gift gifts pressie card cards flowers bouquet wrapping paper
""".split())
# Nothing is started at all: "i still havent booked anything" for a wedding in three weeks is the
# plan's own question ("how do i plan a wedding"), not a thing to wear or give.
GENERIC = frozenset("""
anything everything much sorted sorted organised organized booked arranged planned done
started chosen picked
""".split())


def _clauses(text):
    return [part.strip(" .!?,") for part in re.split(
        r"\s*(?:,|;|\band\b|\bbut\b|\bso\b|\bbecause\b)\s*", str(text or "").lower()) if part.strip()]


# The words that carry meaning, for asking whether two phrases are the same thing.
STOP = frozenset("a an the my our your his her their for to of in on at with and yet".split())


def _content(text):
    return {word for word in re.findall(r"[a-z']+", str(text or "").lower()) if word not in STOP}


def _what_is_missing(text):
    """The thing not got yet and the phrase it was said in, or None."""
    for clause in _clauses(text):
        for frame in _NOT_GOT:
            found = frame.search(clause)
            if found:
                phrase = found.group("thing").strip()
                thing = re.sub(r"^(?:a|an|the|my|our|any|some|another)\s+", "", phrase)
                # The thing ends where the preposition for the occasion starts: "a present for
                # the wedding" is a present, and the wedding is what it is for.
                thing = re.split(r"\s+(?:for|to|in|at|on|from)\s+|\s+yet\b", thing)[0].strip()
                if thing:
                    return thing, phrase
    return None


def _the_occasion(text, missing):
    """The occasion the missing thing is for, as the person said it, or None."""
    found_all = []
    for clause in _clauses(text):
        # Every phrase the clause offers is tried: "i havent got a present for the wedding" names
        # the present first, and the wedding after it is the occasion the present is for.
        found_all.extend(_OCCASION.finditer(clause))
        head = _OCCASION_HEAD.match(clause)
        if head:
            found_all.append(head)
    for found in found_all:
        occ = found.group("occ").strip(" -")
        # The phrase can begin with the thing rather than the occasion - "a present for the
        # wedding" - so what follows the preposition is the occasion.
        after = re.split(r"\s+(?:for|to)\s+", occ)
        if len(after) > 1:
            occ = after[-1]
        # A trailing preposition is where the phrase was cut, not part of the occasion: "a wedding
        # in 3 weeks" keeps its deadline, and "a wedding in" does not name one at all.
        occ = re.sub(r"\s+(?:in|on|at|for|to|next|this|the|with|of|yet)$", "", occ).strip(" -")
        if not occ or _content(occ) & _content(missing):
            continue  # the thing itself, not the occasion it is for
        if len(occ.split()) > 7:
            continue  # a whole sentence is not an occasion
        return occ[2:] if occ.lower().startswith("a ") else occ
    return None


def as_question(text):
    """The question the line left out, or None when it left out nothing the base can answer."""
    if not isinstance(text, str) or not text.strip():
        return None
    said = " ".join(text.lower().split())
    if "?" in said:
        return None
    missing = _what_is_missing(said)
    if not missing:
        return None
    thing, phrase = missing
    words = _content(phrase) | _content(thing)
    occasion = _the_occasion(said, thing)
    if not occasion:
        return None
    if words & GIVEN:
        return "what should i get for " + occasion
    if words & WORN or "wear" in words:
        return "what should i wear to " + occasion
    if words & GENERIC:
        return "how do i plan " + occasion
    return None


def answer(text, memory=None):
    """The entry's answer to the question the line left out, or None to leave the line as it is."""
    question = as_question(text)
    if not question:
        return None
    store = memory if isinstance(memory, dict) else {}
    try:
        entry = lookup.find(understand(question, store))
    except Exception:
        return None
    if entry is None:
        return None
    reply = plans._the_reply(entry, question, store)
    if not isinstance(reply, str) or not reply.strip() or reply[:1].islower():
        return None
    return reply.strip()
