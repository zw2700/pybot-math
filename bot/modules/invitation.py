"""An invitation to the bot, answered as a friend who cannot come answers it.

"do you fancy a walk" is a person asking for company. Every module that could have answered it
read it as a question about the world: the composer's last resort sent it to the search hedge
("that's beyond what I know well, sorry") and the other wording of it to the intake form ("Got
it. Is there anything you'd like a hand with?"). This module proposes the reply that fits - the
refusal said plainly, then the next question about the thing itself (bot/compose/invitation.py).

The PRIORITY is below the knowledge base on purpose. An invitation that names something the
answers know is still that thing's turn: "shall we get a takeaway" keeps the fish and chips and
"you up for a curry on friday" keeps the quick curry, because those replies are better than
anything about the invitation would be. What is left here is the invitation nothing else answers.

That rule is declared, not implied. A module that proposes from the fallback band has to say
what it answers and when it stands aside (the routing contract, `tests/test_routing_contract.py`),
otherwise the band is a place to hide a catch-all in: `ANSWERS_INSTEAD` says the invitation
reading takes the line in place of the small-talk entries, and `DEFERS_TO` says the standing
aside - every answer at a real priority keeps its turn, which is the knowledge base's turn on the
line that names a thing. So this module is the floor of one shape of line, not a competitor for
any topic.
"""
from ..compose import invitation

PRIORITY = -500  # below `answers` (0): a thing the knowledge base knows keeps its answer
# The line this module reads whole is small talk - somebody asking for company - so it answers in
# place of the small-talk entries rather than on a word of them (a topic entry that matched "walk"
# or "brew" would otherwise answer a different question).
ANSWERS_INSTEAD = ("small-talk",)


def DEFERS_TO(reply, text):
    """Yes for every answer at a real priority: the invitation is the floor of its shape.

    The arbiter asks this of the candidates that are not in the fallback band (see
    `arbiter._defers`), so an answer that a lane stands behind keeps the turn and the refusal is
    left for the line nobody else answered: "shall we get a takeaway" keeps the fish and chips.
    The wording is the composer's and the bands are the arbiter's; this only says out loud what
    the PRIORITY already meant, so that a module in the fallback band cannot quietly become the
    answer to everything.
    """
    return True


def respond(text, memory):
    """The line an invitation to the bot gets; None for every other line."""
    if not isinstance(memory, dict):
        memory = {}
    return invitation.reply_for(text, memory)
