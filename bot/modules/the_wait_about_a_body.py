"""A wait about a body is not a bad day at work, and the bot says the wait or it says nothing.

Five lines were answered by the generic pool on main - the same line a person gets for a missed bus:

    they think its cancer         -> "That sounds rough. If you want, I can help you think..."
    theyre testing me for cancer  -> "Ugh, that's a lot to carry."
    my mum might have cancer      -> "I'm sorry - that's frustrating. Want a hand..."
    i have cancer                 -> "That sounds rough. If you want, I can help you think..."
    its not cancer                -> "Sorry to hear that."   (the opposite of the news)

The composer's own answer is asked for first, and this module stands down unless it is one of those
generic families: a card about a symptom, an entry, a pool that names the condition, or an answer
with somebody to ask in it all keep the turn. So the worst case here is that a placeholder is
replaced by one of four lines written for the wait, the news, or the thing ruled out
(bot/compose/a_wait_about_a_body.py) - and none of those states a fact about the world.

It sits above greeting (-1000) and below every card, which is the band a floor module wants. The
`results` half of this (`im worried about my results` gets the driving-test line) is in `chat`, at
CHATTER, and is reported to #conversation rather than reached from here.
"""
import re

from ..compose import fallback
from ..compose import a_wait_about_a_body

PRIORITY = -999  # above greeting (-1000), below every card and pool

# The generic families this module may replace. A reply that is not one of these is somebody's
# answer to the line, and is left alone - that is the whole safety boundary.
GENERIC = (
    "that sounds rough",
    "ugh, that's a lot to carry",
    "i'm sorry \u2014 that's frustrating",
    "i'm sorry - that's frustrating",
    "i'm sorry, that's frustrating",
    "sorry to hear that",
    "i'm sorry to hear that",
    "i'm listening",
    "that's a lot to carry",
)
NOTED = "noted: "
# The same placeholder, said as the person's own line handed back: "Got it - your sister might have
# ms." Nothing was answered in it, and the wait pools are.
GOT_IT = ("got it \u2014 ", "got it - ", "got it, ", "got it: ")


# The chain marks a line said twice in a row - "Same as before: ..." - and that wrapper is the
# chain's, not the pool's, so it is taken off before the pool is recognised.
SAID_AGAIN = "same as before: "


def is_generic(reply):
    """True when the reply is one of the placeholder families this module answers over."""
    said = str(reply or "").strip().lower().replace("\u2019", "'")
    if said.startswith(SAID_AGAIN):
        said = said[len(SAID_AGAIN):].strip()
    if not said:
        return False
    return said.startswith(NOTED) or any(said.startswith(opener) for opener in GENERIC)


def _words(line):
    """The words of a line, with the person's own "my" heard as the bot's "your"."""
    said = str(line or "").lower().replace("\u2019", "'")
    said = re.sub(r"[^a-z0-9' ]+", " ", said)
    words = [w for w in said.split() if w]
    return tuple("your" if w == "my" else "our" if w == "our" else w for w in words)


def said_back(reply, text):
    """True when the reply is the person's own line handed back and nothing else.

    "Got it - your sister might have ms." says that the bot heard it and no more, which is the
    placeholder this module exists for. Only the words are compared, in order, after the one
    wrapper the bot puts in front of an echo, so "Got it - your sister might have ms. When do you
    hear?" is a reply and not an echo.
    """
    said = str(reply or "").strip().lower().replace("\u2019", "'")
    for wrapper in GOT_IT + (NOTED,):
        if said.startswith(wrapper):
            said = said[len(wrapper):]
            break
    else:
        return False
    return bool(_words(said)) and _words(said) == _words(text)


def respond(text, memory):
    """Say the wait, the news or the ruled-out thing, or say nothing and leave the answer alone."""
    memory = memory if isinstance(memory, dict) else {}
    said = fallback.reply_for(text, memory)
    if not (is_generic(said) or said_back(said, text)):
        return None
    return a_wait_about_a_body.reply_for(text, memory)
