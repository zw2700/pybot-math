"""The last resort: the shape of the answer, when the bot has not got the fact itself.

Nothing in the bot knows some lines. "what would you recommend instead", "how much does a
replacement one go for", "when should i start" - no card claims them, no route to a place fits
them, and the reply is one of three search hedges: "I'm not sure about that one, sorry - I'd rather
not guess. A quick search online will get you a solid answer." That is true of every line ever
typed and tells the person nothing about the one they asked. Pointing elsewhere is not a reply.

There is one thing the bot still knows about a line like that, and it is the shape of the answer: a
pick wants the thing that decides a pick, a figure wants the three things that set it, a verdict
wants what deciding one would weigh. That is what a friend says while getting to the detail, and it
is the difference between "go and look it up" and "here is what the answer depends on".

`bot/modules/intent.py` has already written the shape to `memory["understood"]["wants"]`, so this
reads that and never a word list of its own (bot/compose/the_shape_without_the_fact.py holds the
pools and the readings it corrects). It sits one band above `greeting`, which is the module that
says the hedge, so it only ever stands where the reply would have been that hedge or a bare
receipt: a real answer from any module is above this one, and the composer's own line is asked for
and read, so a hedge that already says something about this line keeps its turn.

It replaces the three plain hedges and the receipts only. The composer has its own lines for the
shapes it knows - "That's your call, not mine. Tell me what you're weighing and I'll help you pick"
for a decision - and a general frame over the top of one of those is a step down from it.

Three ways this was worse before the guards went in, each kept as a test:

  - a date printed on a paper is read off the paper, not weighed: "my car insurance is up for
    renewal in march" ... "ok and when does it run out" is on the policy;
  - food that is still good is a fact, not a decision: "the stuffing burnt" ... "is the rest still
    ok" wants the keeping row for a joint, not a test for a decision;
  - a count of the thing just named in the thread is written on the page for that thing, not a sum.

And it stands down on a care, loss or crisis thread and on a question about the body, where a
general frame about how to choose is the wrong thing to say to somebody worried about a person.
"""

from ..compose import fallback
from ..compose.the_shape_without_the_fact import the_shape_without_the_fact

# Below every module that can answer a line about the world, and above `greeting` (-1000), which is
# the module that says the hedge this replaces. The floor is not one band: `where_it_answers` and
# `bulky` sit at -999, `live_source` and `carers_turn` at -998, and a reader that knows the specific
# thing asked about must keep the turn. At -999.5 this frame only speaks when none of them does.
PRIORITY = -999.5

# The three plain hedges, and the receipts that are not answers either. A hedge that already names
# where the answer lives ("the council's site has the collection day") is a better reply than a
# frame about how to choose, and is left alone.
_A_HEADS = 40


def _the_reply_is_only_a_placeholder(reply):
    said = " ".join(str(reply or "").lower().split())
    if not said:
        return False
    if fallback._in_a_pool(reply, (fallback.NEUTRAL,)):
        return True
    return said[:_A_HEADS] in [line.lower()[:_A_HEADS] for line in fallback.UNKNOWN]


def _the_composer_would_hedge(text, memory):
    """True when the composer's own line for this turn is a placeholder, not an answer."""
    try:
        reply = fallback.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a composer that cannot be asked claims the turn
        return False
    return _the_reply_is_only_a_placeholder(reply)


def _the_floor_would_say_a_placeholder(text, memory):
    """True when `greeting` - the module that says the hedge - would say a placeholder this turn.

    The composer is only part of what the floor does: `greeting` also hands back a step of the
    answer above, and a follow-up like "what about the containers" is that step, not a hedge. A
    rule read off the composer alone took the turn from it - twice on a 200-chat sample - so the
    module that would otherwise answer is asked, on a copy of memory, and its own line decides.
    """
    try:
        from . import greeting  # noqa: PLC0415 - imported here: the floor is asked last
        reply = greeting.respond(text, _a_copy_of(memory))
    except Exception:  # noqa: BLE001 - a floor that cannot be asked does not open the turn
        return False
    return _the_reply_is_only_a_placeholder(reply)


def _a_copy_of(memory):
    """Memory as a module may read it: everything copied, the turns shared, as the runtime does."""
    try:
        import copy  # noqa: PLC0415 - only used when the floor is asked
        return {key: value if key == "turns" else copy.deepcopy(value)
                for key, value in memory.items()}
    except Exception:  # noqa: BLE001 - a value that cannot be copied: share memory instead
        return dict(memory)


def _a_thread_with_a_person_in_trouble(memory):
    """A worry about somebody's health, a death, a crisis, or a line about the body.

    A general frame about how to weigh a choice is the wrong thing to say to somebody whose mother
    is in hospital, and the bot has readers of its own for those turns.
    """
    for reader in ("_in_a_care_thread", "_in_a_loss_thread", "_in_a_crisis_thread",
                   "_thread_is_about_the_body"):
        try:
            if getattr(fallback, reader)(memory):
                return True
        except Exception:  # noqa: BLE001 - a reader that cannot be asked does not fence
            continue
    return False


def respond(text, memory):
    if not isinstance(memory, dict):
        return None
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        return None
    # The reader comes first because it is cheap and says no to almost every line: the composer is
    # only asked when this line has a shape the bot could say something true about.
    pool = the_shape_without_the_fact(understood, memory)
    if pool is None:
        return None
    if _a_thread_with_a_person_in_trouble(memory):
        return None
    if not _the_composer_would_hedge(text, memory):
        return None
    if not _the_floor_would_say_a_placeholder(text, memory):
        return None
    clean = understood.get("clean") or " ".join(str(text or "").lower().split())
    return fallback._choose(pool, memory, clean)
