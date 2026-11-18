"""How slowly or how fast to go at the plan in hand: "how slowly should i build up".

The answer above already carries the rate - "run-walk to start, one minute of easy jogging to two
of walking, twenty minutes, three times a week, and add a minute of running a week" - and the next
line asks how fast to go at it. The knowledge base read the line's own words and answered from an
entry about fuelling a long run, so a person building back up to running was told what to eat
before an hour of it: a reply about a different question, on the same subject.

The reading and the wording live in `bot/compose/pace.py`: the reply hands back the answer's own
step ("add a minute of running a week for six weeks") and then the answer's own test ("keep every
run slow enough to talk"), because that is what a friend says when asked how fast to go at the
plan they just gave.

It sits above the knowledge base (0) and returns None on every line that names a thing of its own
("how fast should i run a 5k" has an entry of its own) and on every line with no rate in the
answer above it.
"""
from ..compose import pace

PRIORITY = 1300  # above the knowledge base, below loss (2000), grief (2100) and safety (9000)


def respond(text, memory):
    """The pace of the answer just given, or None for every other line."""
    try:
        return pace.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a module that raises claims nothing
        return None


def takes_as_it_comes(text, memory):
    """Only on a rate asked about the plan just given, and nowhere else.

    The knowledge base reads "running" in "how fast should i be running" as a subject of its own
    and answers it from the fuelling entry, which is a reply about a different question - so on
    this line the module that read the whole line takes the turn.
    """
    try:
        return pace.the_pace_line(text, memory) or pace.the_keep_up_line(text, memory)
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


# The arbiter reads the declaration by this name (`bot/modules/arbiter.py: DECLARED_AS_IT_COMES`).
TAKES_AS_IT_COMES = takes_as_it_comes
