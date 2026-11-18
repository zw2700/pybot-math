"""The name on record, taken back by the person who gave it.

    my name is kay
    im not kay                     ->  Sorry — I had you as Kay. What should I call you?
    dave                           ->  Hi Dave — good to meet you.
    whats my name                  ->  You're Dave.

Three things went wrong on main `bc4425e`, and the store was the last of them. The line was
answered with nothing at all ("I'm listening — say more if it helps"), or with the person's own
words said back ("Got it — that's not your name.", "Got it — your names not ok."), and the name
stayed on record, so every turn after it called them by the name they had just said was wrong. A
person who says the bot has their name wrong is asking it to stop using it; the reply that does
that is an apology and one question, and the next bare word is the answer to it.

The reading is `bot/memory/facts.py:the_name_they_take_back`, because it is the same reader for
the store's own name (pets, and the names of people they mention) and it belongs beside them. It
fires only against the name the store holds, so "im not sure" and "im not hungry" - the commonest
openings of any line - are never read as a denial of a name nobody gave.

This module exists rather than a branch inside `bot/modules/memory_store.py` because that file is
past the world's size cap and cannot be uploaded (the same reason as
`bot/modules/trip_date_said_again.py`). It keeps the store's own record up to date and asks for
nothing else: `memory["asked_for"]` is the store's marker for a name question the bot has just
asked, which is what makes the bare "dave" on the next line read as a name rather than as noise.
"""

from ..compose import pick
from ..memory import facts as extract
from ..memory import user

PRIORITY = 6600  # the store's own record, corrected: under the store (7000), over every reply

# The apology says the name the bot had, because the person is checking it heard which name was
# wrong - and then asks, because nothing has replaced it yet.
NAME_TAKEN_BACK_SAY = (
    "Sorry — I had you as {name}. What should I call you?",
    "My mistake on {name}. What should I call you?",
    "Sorry about that — {name} was wrong. What do you go by?",
    "Ah, sorry. Not {name}, then — what should I call you?",
)
# The line denies the name without saying which ("thats not my name", "my name is wrong"), and
# there is nothing to say back but the apology and the question.
NAME_TAKEN_BACK_BARE = (
    "Sorry about that — what should I call you?",
    "My mistake. What should I call you?",
    "Sorry — what do you go by?",
)


def _the_name_i_had(memory):
    """The name the store holds for the person, or "" when it holds none."""
    if not isinstance(memory, dict):
        return ""
    return str(user(memory).get("name") or "").strip()


def _note(text):
    """The line as the store keeps it for comparing one turn with the next."""
    return " ".join(str(text or "").lower().split())


def observe(text, memory):
    """Take the name off the record, and leave the note the reply is written from.

    The name goes here rather than in `respond` because the store keeps what a line says whatever
    its own reply is: left in place, the next turn calls the person by the name they have just
    said is wrong, and that is the fault this module is for.
    """
    if not isinstance(memory, dict):
        return
    known = _the_name_i_had(memory)
    taken = extract.the_name_they_take_back(text, known)
    if taken is None:
        return
    user(memory).pop("name", None)
    memory["name_taken_back"] = {"name": str(taken), "said": _note(text)}
    # The bot is about to ask for the name, so the store has to know it asked: a bare word on the
    # next line is the answer to this question and nothing else.
    memory["asked_for"] = "name"


def _this_line(memory, text):
    """The note left by `observe` when it was made on this line, else None."""
    if not isinstance(memory, dict):
        return None
    held = memory.get("name_taken_back")
    if not isinstance(held, dict) or held.get("said") != _note(text):
        return None
    return held


def respond(text, memory):
    held = _this_line(memory, text)
    if held is None:
        return None
    name = str(held.get("name") or "").strip()
    if not name:
        return pick(NAME_TAKEN_BACK_BARE, memory)
    return pick([line.format(name=name) for line in NAME_TAKEN_BACK_SAY], memory)


def takes_as_it_comes(text, memory):
    """True only on a line that denies the name on record: nothing else has this answer."""
    return _this_line(memory, text) is not None


TAKES_AS_IT_COMES = takes_as_it_comes
