"""Is it too late - answered by the answer already on the screen.

"i never learned to swim im 45" is answered with the adult-lessons card, which says in as many
words that instructors teach adults who are frightened of the water. The next line, "is it too
late", is the person asking whether that card still applies to them, and it was answered with a
search hedge - as if nothing on the screen had been about it.

The line names no thing of its own, so no entry is reached and the knowledge base cannot see it.
What can answer it is the answer itself: the sentence in it that says people like them do the
thing.

The rules are narrow on purpose:

* the line is only the doubt and nothing else, so "is it too late to plant tulips" - a question
  with a thing of its own - never comes here;
* the answer one or two turns back has to hold a sentence that says anybody can (beginners,
  adults, any age, most people, nobody is watching), so an answer about a deadline, a closing
  date or a cutting is never told it is not too late: nothing in it says that;
* a hedge is never answered from itself, and a hand-back already made is not made again.
"""
import re

from ..compose import pick
from . import meant

# The lines that are only the doubt, with the filler words people put in front of it.
DOUBT = re.compile(
    r"^\s*(?:and\s+|so\s+|but\s+|ok\s+|okay\s+|well\s+|right\s+|hmm+\s+|ah\s+|oh\s+)*"
    r"(?:"
    # "is it too late", "would that be too late", "is it still worth it"
    r"(?:is|isnt|isn'?t|would|will|was|does)\s+(?:it|that|this|there)\s+(?:be\s+)?"
    r"(?:too\s+(?:late|old|young)|"
    r"still\s+(?:worth\s+(?:it|doing|a\s+go)|possible|an?\s+option|on|fine|alright|ok|okay|"
    r"any\s+good)|"
    r"worth\s+(?:it|doing|a\s+go))|"
    # "am i too old", "are we too late", "am i too late to get any good"
    r"(?:am|are|was|were)\s+(?:i|we|you)\s+too\s+(?:old|late|young|far\s+gone)|"
    # The doubt said as what it would cost them: "am i too late to get any good", "am i too
    # old to get better". It is the same question as "is it too late", and without this shape
    # it reached the coursework deadline answer on the word "late".
    r"(?:am|are|is|was|were)\s+(?:i|we|you|it|that|this)\s+too\s+(?:old|late|young)\s+to\s+"
    r"(?:get|be|become|do|learn|start)\s+(?:any\s+)?(?:good|better|decent|anywhere)"
    r"(?:\s+(?:at|with)\s+(?:it|that|this|[a-z'-]+))?\b|"
    # "im too late to get any good": the same doubt without the question turned round.
    r"(?:im|i'?m)\s+too\s+(?:old|late|young)\s+to\s+"
    r"(?:get|be|become|do|learn|start)\s+(?:any\s+)?(?:good|better|decent|anywhere)"
    r"(?:\s+(?:at|with)\s+(?:it|that|this|[a-z'-]+))?\b|"
    # "can i still learn", "can you still join"
    r"(?:can|could)\s+(?:i|we|you|she|he|they)\s+still\s+"
    r"(?:do|learn|start|join|try|manage|cope|go|take\s+it\s+up|get\s+into)\b(?:\s+(?:it|that|this))?|"
    # "is there still time", "is there any point"
    r"(?:is|isnt|isn'?t)\s+there\s+(?:still\s+)?(?:time|a\s+chance|any\s+point|a\s+point)|"
    # "too late", "too late for me", "whats the point now"
    r"too\s+late(?:\s+(?:for\s+me|now|isnt\s+it|right))?|"
    r"(?:what|whats|what'?s)\s+the\s+point(?:\s+(?:now|of\s+it|in\s+(?:it|trying)))?|"
    r"any\s+point(?:\s+(?:now|in\s+(?:it|trying)))"
    r")"
    # The doubt can be said about the thing in hand without naming it: "is it too late to learn",
    # "am i too late to get any good". Only the generic doings - the thing itself ("to plant
    # tulips", "to put the turkey in") is a question the knowledge base can answer, and it never
    # comes here.
    r"(?:\s+to\s+(?:learn|start|begin|try|catch\s+up|get\s+any\s+good|get\s+going|improve|"
    r"take\s+it\s+up|change|retrain|study|practise|practice|go\s+back))?"
    r"\s*[?.!]*\s*$", re.I)

# The sentence in the answer that says the thing is open to somebody like them. Every one of these
# is about who does it, not about when: an answer that gives a date ("the deadline is 31 January")
# has nothing here, which is what keeps "is it too late" from being told "not too late" about a
# deadline.
ANYONE = re.compile(
    r"\b(?:complete\s+beginners?|beginners?|any\s+age|no\s+age|never\s+too\s+late|"
    r"at\s+your\s+own\s+pace|whatever\s+your\s+age|whatever\s+age|all\s+ages|"
    r"people\s+start|"
    # The same answer for every age, said as a comparison: "six months at 40 just as at 18",
    # "the same at 50 as at 20". The age is what it is compared at, so "just as good as" - a
    # quality comparison - is not one of these.
    r"just\s+as\s+at\s+\w+|the\s+same\s+at\s+\w+\s+as\s+at\s+\w+|"
    # Only an "adult" doing the thing counts: "an adult rescue is easier than a puppy" and "an
    # adult cat is fine with a working day" are about the animal, and the dog card answered a
    # doubt about the cost with the cost.
    r"adults?\s+(?:who|pick|learn|learns|starting|start|started|take|took|can|could|are|do|"
    r"in\s+their|of\s+any|taught|like)\b)", re.I)

LEADS = (
    "Not too late — {said}",
    "Never too late: {said}",
    "It is not too late — {said}",
)

# A doubt about getting good at something needs no subject of its own: what decides it is a
# regular slot in the week, not the year somebody starts. The bare "is that too late" is still
# left alone, because a train or a deadline is a fact this bot cannot see (LEADS needs an answer
# on the screen); only the "get any good" shape has a truth to say without one.
GET_ANY_GOOD = re.compile(
    r"\btoo\s+(?:old|late|young)\s+to\s+(?:get|be|become|do|learn|start)\s+"
    r"(?:any\s+)?(?:good|better|decent|anywhere)\b", re.I)
WITHOUT_A_SUBJECT = (
    "Not too late — what decides it is a regular slot in the week, not the year you start in",
    "Never too late: a short practice most days does more than a long one now and then",
    "It is not too late — adults who start later tend to know what they want from it",
)

# A sentence that says the verdict itself needs no lead: "Not too late — not too late at all:
# adults pick up the theory faster than children" says it twice and reads as a stutter.
SAYS_IT = re.compile(r"\b(?:not\s+too\s+late|never\s+too\s+late|no\s+age\s+limit|any\s+age)\b",
                     re.I)


def _the_sentence(said):
    """The sentence of the answer that says anybody can, cut down to its gist, or None."""
    for sentence in meant._sentences(said):  # noqa: SLF001 - same package
        if sentence.strip().endswith("?"):
            continue
        if not ANYONE.search(sentence):
            continue
        gist = meant._gist(sentence)  # noqa: SLF001
        if not ANYONE.search(gist):
            # The sentence says it in a clause the gist cut away: "... before they pass, so two
            # lessons a week gets you there in about six months at 40 just as at 18" is the part
            # that answers the doubt, and the opening clause alone ("most people need around 45
            # hours of lessons") handed back under "not too late" is the bot putting a verdict
            # on words that never carried it. Two clauses keep both: the one that says anybody
            # can, and the one before it that says what about.
            gist = _two_clauses(sentence) or gist
        if len(gist.split()) < 4:
            continue
        return gist
    return None


def _two_clauses(sentence):
    """A sentence cut after its second clause, as a sentence: the one that says it, and what
    it is said about."""
    cuts = [match.start() for match in meant.CLAUSE.finditer(sentence)]  # noqa: SLF001
    if len(cuts) >= 2:
        return sentence[:cuts[1]].strip(" ,;:-.") + "."
    if len(cuts) == 1 and len(sentence.split()) <= 40:
        # One clause break and no more: the sentence is one line already, and both of its parts
        # are needed ("most people need around 45 hours of lessons before they pass, so two
        # lessons a week gets you there in six months at 40 just as at 18").
        return sentence.strip().rstrip(" ,;:-.") + "."
    return ""


def _the_reply(sentence, memory, clean):
    """The sentence handed back under a plain lead, or on its own when it says it already."""
    body = sentence.rstrip(".!?")
    if SAYS_IT.search(body):
        return body[0].upper() + body[1:] + (sentence[len(body):] or ".")
    said = body[0].lower() + body[1:] + (sentence[len(body):] or ".")
    return pick(LEADS, memory, clean).format(said=said)


def answer_for(text, memory):
    """The sentence that answers the doubt, or None when this is not that turn."""
    if not isinstance(memory, dict):
        return None
    clean = (text or "").strip()
    if not DOUBT.match(clean):
        return None
    answers = meant._answers(memory)  # noqa: SLF001 - same package
    # A hedge is never answered from itself: once the bot has said it does not know, the next
    # doubt is not the moment to reassure about the thing it just disowned.
    if answers and meant.repeat.HEDGE.search(answers[0][0]):  # noqa: SLF001
        return None
    for said, _asked in answers:
        if meant.repeat.HEDGE.search(said):  # noqa: SLF001
            continue
        sentence = _the_sentence(said)
        if sentence:
            return _the_reply(sentence, memory, clean)
    if GET_ANY_GOOD.search(clean):
        return pick(WITHOUT_A_SUBJECT, memory, clean)
    return None
