"""A short nudge after an answer is not the end of the conversation.

These are the replies on the whole bot after "my knee is sore when i run":

    and                    "Alright then - good luck with it."
    go on                  "Thanks for telling me - I'm here if you want to dig into any of that."
    and then               "You've got it: Cut the distance and the speed for a week or two: ..."

The first two close a conversation the person is still in, and the third hands back the answer's
opening sentence - the part they have already had. A nudge names nothing of its own, so nothing in
the line says the person is finished; what it says is "keep going". This module repeats nothing and
closes nothing: it says the answer is finished and offers the way back in.

The reading and the wording live in `bot/compose/still.py`, next to the answer they read; this
module is here so the claim has a PRIORITY of its own. That is the point of a module rather than a
branch inside the composer's own hook: a nudge has to be answered before the chat module's goodbye
and after every module that has a real answer for the line, and that is what a band says. The hook
is declared as well, because the claim is narrow - it is true only on a line that is a nudge and
only when there is an answer behind it - and a claim that narrow should not be a band at all.

A module that answers only the lines it is good at passes on everything else: `respond` returns
None on every other line and the bot answers it as it did before.
"""
from ..compose import still

# Under the specialists (a module that has a real answer for the line keeps the turn) and above
# the greeting fallback (a goodbye must not close a conversation the person is still in).
#
# It is also **under `urgent.py` (-900)**, which is the follow-up band for a live emergency: an
# emergency's own follow-up line is a real answer for a nudge, and an end line is not. The band was
# -400 when this file was first written and happy-beaver was right that it sat one step too high -
# the module stood down on an emergency by reading the turn above, and a band should say the same
# thing without needing that reading. No PRIORITY moves: the band is where this module's own lines
# put it.
PRIORITY = -950


def respond(text, memory):
    """The honest end of the last answer, for a nudge that names nothing of its own. Else None."""
    try:
        return still.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None


def takes_as_it_comes(text, memory):
    """Only on a nudge with an answer behind it: the line is read whole, and nowhere else."""
    try:
        return bool(still.takes_as_it_comes(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


# The arbiter reads the declaration by this name (`bot/modules/arbiter.py: DECLARED_AS_IT_COMES`),
# the way every other module declares it. A lowercase function alone is a hook nobody asks.
TAKES_AS_IT_COMES = takes_as_it_comes
