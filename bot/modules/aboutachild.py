"""A question about a child is asked with the age the store has for that child.

"my son is 5" then "how much sleep does he need" is a line with no age in it, and the sleep
answer a pronoun reaches is the adult one - seven to nine hours, coffee at three - while the
five year old's is ten to thirteen. The store kept the age a turn ago, so the line is written
out as "how much sleep does a five year old need" and answered from the child's own row.

It passes on everything else: no child in the store, no pronoun in the line, or a written ask
that reaches no row. The line then goes on to the module it went to before this one existed.
"""
import copy

from ..memory import aboutthem
from ..understanding import understand
from . import answers

# The general helpful band (1000-3999, README "Routing"), so a line this module read whole is
# answered from the child's own row rather than from the general entry the same words reach, and
# below the loss, the grief and the safety bands, which must lead on a hard line.
PRIORITY = 1100


def TAKES_AS_IT_COMES(text, memory):
    """This line is the one to answer as it comes: it asks about the child the store keeps."""
    return bool(aboutthem.with_the_age(text, memory))


def respond(text, memory):
    if not isinstance(memory, dict):
        return None
    written = aboutthem.with_the_age(text, memory)
    if not written:
        return None
    seen = copy.deepcopy(memory)
    seen["understood"] = understand(written, seen)
    reply = answers._answer(written, seen)  # noqa: SLF001 - its own reader, one answer
    if not reply:
        return None
    return str(reply).strip() or None
