"""A line that says it does not want advice is heard, not answered with the thing it declined.

Nobody types "and i dont want advice" to a machine unless they have had advice they did not ask
for, and the one reply they cannot have is the card for the thing they have just said no to. Yet
that is what every one of these got:

    my son was in an accident and i dont want advice   -> "A search should sort you out quickly"
    i dont want advice, i just want to talk            -> "That's beyond what I know well"
    not looking for a solution, just want to know...   -> the chemistry definition of a solution
    i dont need advice, just someone to listen         -> a card on listening to people
    i dont want medical advice                         -> a search hedge
    dont tell me what to do, just listen               -> a list of albums to listen to
    i just wanted to say it out loud                   -> a card on asking a neighbour to be quiet

The line names the thing it refuses, so a lookup finds exactly the wrong entry: nothing here is a
question about the world. `bot/compose/no_advice.py` holds the reading and the wording; this
module is here so the claim has a band of its own.

The claim is the whole of what this module has: the words of the line are the words of a card, so
the specialist rule would hand the turn back to it every time (`_a_declaring_specialist_besides`),
which is what `TAKES_AS_IT_COMES` is for. The band sits above the knowledge base and the small talk
and below the loss and safety bands, and the guards below keep a death and an emergency out of it:
a line that also carries a question of its own keeps that question's answer.
"""
from ..compose import no_advice

# Above the knowledge base (0) and the small talk (300), because the card for the thing refused is
# the answer this line must not have; below loss (2000) and safety (9000), which read a turn of
# their own in the same line. It is also above the arbiter's `CHATTER` line (1000) on purpose: a
# candidate under it gives way to a module that declares the topic this line was read as, and every
# line this module answers is read as the topic of the thing it just refused ("i lost my job and i
# dont want any advice" is read as money). The claim on the line is the whole of what this module
# has, so it is made from above that line.
PRIORITY = 1050


def respond(text, memory):
    """The listening line, or None on every other line."""
    try:
        pool = no_advice.pool_name(text)
    except Exception:  # noqa: BLE001 - a reading that raises answers the line as it did before
        return None
    if not pool:
        return None
    if not TAKES_AS_IT_COMES(text, memory):
        return None
    try:
        return no_advice.reply_for(pool, text, memory)
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None


def TAKES_AS_IT_COMES(text, memory=None):
    """The lines this module read whole and no entry has any business answering."""
    try:
        if not no_advice.says_no_advice(text):
            return False
        # A death in the line is a death however the rest of it is put: "my mum died and i dont
        # want advice" is the loss module's turn, and taking it would answer a bereavement with
        # "go on, I'm listening". The claim is given up rather than answered differently, because
        # the module that reads the loss has the better line. Read narrowly, so a job or a person
        # missed rather than lost stays this module's.
        return not no_advice.says_a_death(text)
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False
