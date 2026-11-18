"""A thing the person cannot follow is asked about, by name.

"the instructions are confusing", "i cant follow the recipe", "im baffled by my payslip", "my head
is spinning with all this": the person has said that something specific will not go in. What a
friend does with that is ask about the thing - which bit, where it lost them - because the thing
is the only place the answer can come from.

On main every one of those got a reply that asked them to start again: "I'm listening - say more
if it helps", or "Thanks for telling me - I'm here if you want to dig into any of that", and
"im baffled by my payslip" got "Good to hear. What was the best bit?" - a congratulation for a
thing that would not go in.

The reading is the understanding engine's (`memory["understood"]["confusion"]`,
`bot/understanding/kinds.py::confusion_of`): the shape of the line and the thing it named. This
module is the wording, at priority -900, just above the composer floor and below every module that
can answer for itself.

Nothing is taken from a real answer. The composer's floor is not only the shrug: it gives a form
nobody can read the three things to look for, and "im confused about my medication" the medication
row. So the composer is asked first (`bot/compose/hedge.py`), and this module answers only where
it has nothing - or where its answer is a congratulation, which a line about a thing that will not
go in cannot be.
"""
import random
import re

from ..compose import fallback, hedge

# Above the composer floor (-1000), below everything with a real answer for the line (the small
# talk at 300, the health cards, the knowledge base).
PRIORITY = -900

# The thing is named in the line, so the reply can name it back and ask where it goes wrong. The
# two things a page of words usually fails at are its words and its order, which is what the pool
# offers when it offers anything at all.
WITH_A_THING_LINES = (
    "Which bit of {thing} stops making sense? Say the first line that does and we'll take it "
    "from there.",
    "Which part of {thing} loses you - the start, or somewhere in the middle?",
    "What is it about {thing} that isn't going in - the words, or the order of it?",
    "Let's take {thing} one line at a time. Which line is the first one that doesn't land?",
)

# The line named no thing: "this is so confusing", "my head is spinning with all this". Asking
# about "it" asks them to say what it is, which is the one thing they came without, so the pool
# asks for the smallest piece of it that is still a piece.
WITHOUT_A_THING_LINES = (
    "What is the thing itself - a letter, a form, a set of instructions? Even the name helps.",
    "Say the last bit that made sense and I'll take it from there.",
    "Which part is clear and which part is foggy? Start where it stops making sense.",
)

# The words that are part of the thing's name and stay as they are, and the ones said by the
# person that have to be said back to them in the second person ("my payslip" -> "your payslip").
SECOND_PERSON = {"my": "your", "our": "your", "me": "you", "us": "you", "mine": "yours",
                 "ours": "yours"}
SECOND_PERSON_RE = re.compile(r"\b(my|our|me|us|mine|ours)\b")


def _said_back(thing):
    """The thing as it is said to the person: "my payslip" -> "your payslip"."""
    return SECOND_PERSON_RE.sub(lambda m: SECOND_PERSON[m.group(1)], thing or "").strip()


def respond(text, memory):
    """The reply to a thing the person cannot follow, or None for every other line."""
    understood = memory.get("understood") or {}
    confusion = understood.get("confusion") or {}
    if not confusion:
        return None
    clean = fallback._matchable(text)
    # Nothing is taken from an answer the composer has. A form it can help with, a medication row,
    # the foggy question for a bare "im confused": those are answers, and a question in their place
    # is worse. Only the lines it says nothing to - and the congratulation it gives a line about a
    # thing that would not go in - are this module's (bot/compose/hedge.py).
    if not hedge.only_a_shrug(text, memory, misreads=hedge.MISREAD_AS_GOOD_NEWS):
        return None
    thing = _said_back(confusion.get("thing"))
    # The pool is drawn from the one random stream every module shares, so answering here must not
    # spend a draw the next turn would have had: a chat that took this line and then changed the
    # reply to the line after it is worse than a chat this module never touched. So the state is
    # put back the way `bot/compose/hedge.py` puts it back after asking the composer.
    state = random.getstate()
    try:
        if thing:
            return fallback._choose([line.format(thing=thing) for line in WITH_A_THING_LINES],
                                    memory, clean)
        return fallback._choose(WITHOUT_A_THING_LINES, memory, clean)
    finally:
        random.setstate(state)
