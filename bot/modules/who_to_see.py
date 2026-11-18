"""The person to see, when the follow-up asks who and not what to do about it.

"my back hurts" is answered with the back paragraph. "who should i see" is a different ask, and
on main it got the paragraph again, "That is everything I have on that one", or a search hedge.

`bot/compose/who.py` holds the reading and the wording, so this module is the claim and nothing
else. The hook is the one this shape needs: a bare "who should i see" matches no topic entry, so
every module that proposes on it is guessing, and the entry that answered the symptom is the one
that has the person in it - it is where the bot wrote "See a GP if it is no better in a
fortnight", or "have the vet look before the skin is broken".

It sits above the generalists (chat, words, the follow-ups about an answer) because what it hands
back is a second reading of the bot's own answer, not a fresh paragraph about it, and stands well
under the specialists: `respond` returns None on every line that is not a bare ask.
"""
from ..compose import who

# Above the chatter band: the take below is not "this line is worth answering now", it is "the
# person the answer named is what was asked for", and a card that repeats the symptom paragraph
# on the same line must not outrank it. Nothing else is being asked on a bare who-ask.
PRIORITY = 1500


def respond(text, memory):
    """The person to see and the condition on them, or None."""
    try:
        return who.reply_for(text, memory) or None
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None


def takes_as_it_comes(text, memory):
    """Only on a line that is nothing but the ask, over a thread that has a person to name."""
    try:
        return bool(who.takes_as_it_comes(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


TAKES_AS_IT_COMES = takes_as_it_comes
