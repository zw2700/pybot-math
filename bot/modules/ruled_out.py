"""A thing the person rules out is answered against the answer they just got.

After "what should i watch tonight" the bot offered three films, and "not a series" got a fresh
list with two series in it; after "how do i sleep better", "not tablets" reached the repeat
prescription card; after "what car should i buy", "not a diesel" got the misfuelling paragraph.
Those are the plainest form of "the bot did not listen to itself": the person is steering the
answer they have, and what they ruled out was never in it.

`bot/compose/ruledout.py` holds the reading and the wording; this module is here so the claim has
a band of its own. The hook is the one this shape needs: the line has nothing in it that a topic
entry can match, so every module that proposes on it is guessing, and the entry that answered the
thing in the first place is the one that gets it wrong - "not a diesel" is a car line, and the
answer to it is not the card about putting petrol in a diesel tank.

A line whose thing the answer does name is left to the entry that gave the answer, and a line that
names no thing at all (`nothing that needs much water`, `not really`) is left alone: `respond`
returns None on every other line.
"""
from ..compose import ruledout

# Under the specialists, because a rule-out is only ever a reply about an answer that has already
# been given: nothing else is being asked. No PRIORITY moves for this module.
PRIORITY = -450


def respond(text, memory):
    """The thing ruled out, said back against the answer, or None."""
    try:
        return ruledout.reply_for(text, memory) or None
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None


def takes_as_it_comes(text, memory):
    """Only on a line that is nothing but the rejection of something the answer never offered."""
    try:
        return bool(ruledout.takes_as_it_comes(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


TAKES_AS_IT_COMES = takes_as_it_comes
