"""Is there a line of theirs that carries what this turn is about? One check, every reply.

Two failures look different and are the same fault. `shes 7 going on 8` was answered "Got it", and
the next turn `how old did i say she was` was answered **"You haven't told me how old she is"** -
the chat said it, and the store's own reader for that slot found nothing, so the store wrote a
denial over the top of it. On the other side `what size did i say` after `its a 2kg chicken`,
`when did i say we fly` after `we fly on the 14th` and `how often did i say i go` after `i go to
the gym three times a week` were handed the search hedge, with the answer in the line above.

One question decides all of them: **which of their lines carries a value of the kind being asked
about?** It lives in `bot/memory/earlier.py`, once, and the kinds it knows are data rather than
rules in each reader: an age, a name, a day, a size, a sum, how often, a length, a count, a place.

`bot/modules/said_back.py` (priority 350) already asks the same question of the shapes people use
to ask for something said earlier (`bot/memory/lineback.py`). This module is the same check at the
funnel, where it can also see the reply the store was about to send:

* a reply that claims the person never said a thing, while a line of theirs carries it, is
  replaced by their line handed back: "You told me: \\"shes 7 going on 8\\".";
* a recall ask with nothing behind it ("what size did i say") is answered from the line that
  carried the value;
* anything else is a pass (None): the store's own answer stands word for word, and a line it
  answers stays with whichever module answers it today.

The reply speaks for the store, so it declares the store's own topics (`ANSWERS`, read from
`bot/memory/store_lines.py`): on a line about the family or a pet the routing lane would otherwise
lift the store's candidate over this one by its topic, and the store's candidate is the denial
this module exists to replace.

Nothing is claimed that the chat does not hold: when no line carries the value, the store's reply
stands exactly as it was, denial included, because then the denial is true.
"""

from ..memory import earlier
from ..memory import lineback
from ..memory.store_lines import ANSWERS  # the store's own declared topics, so no card lifts over

PRIORITY = 7050


def observe(text, memory):
    """Nothing is kept here: the check reads the turns, it does not add to them."""
    return None


def _the_store_would_say(text, memory):
    """What the memory store answers this line, on this module's memory (so its notes are kept)."""
    from . import memory_store
    try:
        return memory_store.respond(text, memory)
    except Exception:  # noqa: BLE001 - this module must never lose the turn
        return None


def _nothing_to_give(reply):
    """True for the two replies that carry no answer: the search hedge and the hand-off."""
    from ..compose import fallback
    from ..compose import fit
    try:
        return bool(fallback.is_a_hedge(reply) or fit.is_a_punt(reply))
    except Exception:  # noqa: BLE001 - a check that fails must not change the reply
        return False


def _someone_answers_it(text, memory):
    """Whether the knowledge base has a reply of its own for this line.

    The store this module reads is only the pets-and-family one, so it has nothing to say about
    most lines - and a module that took that silence as "nobody can answer this" talked over the
    knowledge base on every question that carried a value of some kind: "how often should i be
    checking the gauge" was told "You told me: \"our boiler keeps dropping to zero on the gauge\""
    instead of the boiler answer, and "how many portions do i need for 6 people" was handed the
    guest line instead of the 1.8 kg. A real answer always outranks a quotation of an earlier line,
    so this module only speaks where the knowledge base has nothing (a search hedge, a hand-off,
    or a false "you never said").
    """
    from . import answers
    try:
        said = answers.respond(text, memory)
    except Exception:  # noqa: BLE001 - a check that fails must not change the reply
        return False
    return bool(isinstance(said, str) and said.strip())


def _another_module_gives_the_value(text, memory):
    """Whether a module that answers these shapes with the value itself already has an answer.

    `attribute_said_again` answers "did i say when we were going" with "You said October." - the
    value alone, which is the answer a person wants. (`memory_store` said "No - that's on the
    Saturday.", reading the ask's "when" off the wrong line.) Where that module has the value, its
    answer is better than a quotation of the whole line, so this one passes.
    """
    try:
        from . import attribute_said_again
        said = attribute_said_again.respond(text, memory)
    except Exception:  # noqa: BLE001 - a check that fails must not change the reply
        return False
    if not (isinstance(said, str) and said.strip()):
        return False
    # Only the value the ask names counts: `how often did i say i go` was answered "You said every
    # day." - the dog walk - and that is a wrong answer of its own, not this module standing down.
    return bool(earlier.gives_the_named_value(text, memory, said))


def _said_back_already(text, memory):
    """Whether the module that owns the ask-for-it-again shapes has an answer for this line.

    It is below this one (350 against 7050), so its reply is not in the running when this module
    speaks. Asking it first keeps every line it answers today answering exactly the same way.
    """
    try:
        return bool(lineback.reply_for(text, memory))
    except Exception:  # noqa: BLE001 - a check that fails must not change the reply
        return False


def TAKES_AS_IT_COMES(text, memory):
    """The store claims a recall ask as its own, which is right until it denies their own line.

    `memory_store` declares that it answers a recall ask as it comes ("what did i say her names
    age was"), and on a line like that the arbiter hands it the turn before PRIORITY is read: the
    store's reader is the one that knows the line is a recall at all. So a reply that hands their
    line back still lost the turn, and the denial was what the person got. This module takes the
    turn only where it has read the whole line against their own words: the ask is a recall ask
    (`did i say`, `remind me`, `what was`) and the store's own answer to it contradicts a line of
    theirs. Everywhere else it says no, and the store's answer stands as it always did.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return False
    if not earlier.RECALL.search(" ".join(text.lower().split())):
        return False
    theirs = _the_store_would_say(text, memory)
    if not (isinstance(theirs, str) and theirs.strip()):
        return False
    put = earlier.put_right(theirs, memory) or earlier.a_misquoted_line(theirs, memory, text)
    if put and put != theirs:
        return True
    return earlier.another_line_was_asked_for(text, memory, theirs)


def respond(text, memory):
    """Their line handed back where the reply would deny it or miss it, else None."""
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    theirs = _the_store_would_say(text, memory)
    if isinstance(theirs, str) and theirs.strip():
        put = earlier.put_right(theirs, memory) or earlier.a_misquoted_line(theirs, memory, text)
        if put:
            return put
        if earlier.another_line_was_asked_for(text, memory, theirs) and not _another_module_gives_the_value(text, memory):
            # The ask named the line it means and the store answered with another of that kind:
            # `how often did i say i go` was told "You also walk the dog every day." while the gym
            # was three times a week two lines up. The named line is the answer.
            pass
        elif not _nothing_to_give(theirs):
            # The store's own answer stands, and it stands as the store's reply: a pass here
            # leaves the store's own candidate in the running, so no specialist loses its slot
            # to a copy of the words it would have got anyway.
            return None
        # A search hedge or a hand-off is the store saying it has nothing, so a recall ask is
        # still answered from their own line: "back to the bedroom, what size was it again" was
        # told the bot would rather not guess while the size was in the chat.
    if _said_back_already(text, memory):
        return None
    if not earlier.their_own_words(text) and _someone_answers_it(text, memory):
        # Unless the person is asking what they themselves said or do: then their own line is the
        # answer and a general card about the subject is not.
        return None
    # The store had nothing for the line, so nothing is denied and something may still be there:
    # a recall ask ("what size did i say") and a plain one ("how old is she") both have an answer
    # when a line of theirs carries the value.
    return earlier.answer_for(text, memory) or earlier.from_the_line(text, memory)
