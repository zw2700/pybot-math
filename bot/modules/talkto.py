"""Somebody asks this bot for its ear and names the thing: an answer, not a shrug.

"can you talk to me about my anxiety" was answered with the search hedge ("I don't know enough to
answer that honestly. A search should sort you out quickly") and "can you help me think about my
options" with "I'm not sure about that one, sorry - I'd rather not guess": two ways of telling a
person to go and look it up, when what they asked for was to talk it through. The bot cannot know
their anxiety, but it can do the one thing asked for, so the reply is a yes in a few words and the
question that starts it (bot/compose/talkto.py, STYLE.md "Not knowing, honestly" and its one short
question).

Nothing that answers the line is displaced, and that is declared rather than hoped for (the routing
contract, tests/test_routing_contract.py). `ANSWERS_INSTEAD` says the line read whole is small talk
- somebody asking for the bot's ear - so the small-talk entries do not answer it on a word of their
key. `DEFERS_TO` says the rest: every entry that answers the thing named keeps the turn, because a
card knows more than an opener does - "can we talk about my mum" is the carers card, "can you help
me think about my options for childcare" the cost of nursery. And the composer's own route to a
person is a better answer than an opener too: "can you help me think about my tax" already names
Citizens Advice, and that survives (see `_the_composer_says_a_route`).
"""
import re

from ..compose import talkto, urgent
from ..compose.fallback_data import WHO_TO_ASK
from ..knowledge.lookup import find as find_entry

# Below `answers` (0) and below the store: only the line nothing else answers.
PRIORITY = -500

# The line this module reads whole is somebody asking for the bot's ear, which is small talk: it
# answers in place of the small-talk entries rather than on a word of them.
ANSWERS_INSTEAD = ("small-talk",)

# The one row that is not an answer to the thing named: the small-talk opener. Its key holds the
# bare words "conversation", "chat" and "about", so a line that names a thing of the person's
# ("i want to talk about my job") scores on it while the row's advice - ask the stranger in the
# queue an open question - is about somebody else's conversation. Every other row that answers is
# a card about the thing the person named, and those keep the turn.
_A_GENERIC_OPENER = frozenset(("conversation-openers",))

# The composer's own routes to a person, read from the table it builds them from rather than
# copied: "can you help me think about my tax" is answered with "Citizens Advice covers this free,
# and a call beats searching", which is what a person wants - a named place to ask, not an opener
# about it. A line that already gets one of these keeps it. Only the opening of the reply is
# checked, because the composer puts its own tail on the route ("...that's the quickest route to a
# straight answer").
_ROUTES = tuple(sorted({who for _, who in WHO_TO_ASK}, key=len, reverse=True))


def _the_entry_for(text):
    """The entry the line's own words reach, or None when nothing fits.

    Asked about the line `bot/compose/talkto.py` read, with the named day taken out, because the
    lookup has to see the thing named and nothing else: "can we talk tomorrow about my mum" reaches
    the carers card only once "tomorrow" is out of the way, and with it in the lookup found the
    small-talk opener instead and this module took a turn the card answers better.
    """
    try:
        text = talkto.the_line_as_read(text)
    except Exception:  # noqa: BLE001 - a reading that fails is the line as typed
        text = text
    words = " ".join((text or "").lower().split())
    if not words:
        return None
    try:
        return find_entry({"clean": words, "words": words.split()})
    except Exception:  # noqa: BLE001 - a lookup that raises finds nothing
        return None


def DEFERS_TO(reply, text):
    """Yes for every entry that answers the line: the opener row is the one exception.

    A card about the thing named is a better answer than an opener about it, so it keeps the turn.
    The small-talk opener is not: it matched the word "about", and its advice is for somebody
    standing in a queue next to a stranger. That row alone does not keep the turn, or the yes never
    reaches the person who asked for it.
    """
    found = _the_entry_for(text)
    return found is None or found.id not in _A_GENERIC_OPENER


# A life in trouble is not an ask for the ear. "can i talk to you about my suicidal thoughts" is a
# crisis line: whichever part of the bot answers it, this opener must not be the one that does, so
# the words that carry it stand this module down and the crisis reply keeps the turn.
_A_LIFE_AT_RISK = re.compile(
    r"suicid|kill(?:ing)?\s+myself|self[\s-]?harm|hurt(?:ing)?\s+myself|end(?:ing)?\s+my\s+life|"
    r"end(?:ing)?\s+it\s+all|take\s+my\s+own\s+life|want(?:ing|ed)?\s+to\s+die|"
    r"(?:not\s+want(?:ing)?|do(?:n'?t|\s+not)\s+want(?:ing)?)\s+to\s+"
    r"(?:be\s+here|live|go\s+on|carry\s+on)|better\s+off\s+dead|no\s+reason\s+to\s+live", re.I)


def _the_entry_the_line_reached(memory):
    """The entry the understanding engine's reading reaches, or None."""
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        return None
    try:
        return find_entry(understood)
    except Exception:  # noqa: BLE001 - a lookup that raises reaches nothing
        return None


def _is_the_opener(entry):
    """True when the only thing the line reached is the small-talk opener row."""
    return entry is not None and entry.id in _A_GENERIC_OPENER


def _a_route_is_named(reply):
    said = (reply or "").strip()
    return bool(said) and any(said.startswith(who) for who in _ROUTES)


def _the_composer_says_a_route(text, memory):
    """True when the composer's own reply to this line names somebody to ask."""
    from . import greeting

    try:
        said = greeting.respond(text, dict(memory))
    except Exception:  # noqa: BLE001 - a composer that raises names no route
        return False
    return _a_route_is_named(said)


def respond(text, memory):
    """The yes and the one question, or None for every other line."""
    if not isinstance(memory, dict):
        memory = {}
    # A body in trouble is not an ask for the bot's ear, and that module sits below this one:
    # "can i talk to you about my son swallowing a battery" is a 999 line, not an opener.
    if urgent.reply_for(text, memory):
        return None
    if _A_LIFE_AT_RISK.search(text):
        return None
    entry = _the_entry_the_line_reached(memory)
    # A card that answers the thing named is the better answer, and this module only ever fills
    # the gap where nothing does: the childcare card, the tenants' advice, the carers card.
    if entry is not None and not _is_the_opener(entry):
        return None
    # The understanding engine's reading loses a line with a day in it ("can we talk tomorrow about
    # my mum" is read as asking for the ear and nothing else), so where it reached nothing the
    # knowledge base is asked about the line this module read - the same line, with the day taken
    # out - and a card that answers the thing named keeps the turn. Only asked where the reading
    # reached nothing: on every other line this module behaves exactly as it did.
    if entry is None:
        found = _the_entry_for(text)
        if found is not None and not _is_the_opener(found):
            return None
    # And a route to somebody who does know beats an opener as well: Citizens Advice for the tax or
    # the landlord, MoneyHelper for the money. The composer has already said it, so there is
    # nothing to add. The opener row is the exception, because a route is not what was asked for
    # on a line read as somebody asking for the bot's ear: "can i talk to you about my medication"
    # was "a pharmacist or your GP can answer that today", which is the shrug in a better suit.
    if not _is_the_opener(entry) and _the_composer_says_a_route(text, memory):
        return None
    # The understanding engine's own reading of the line, because a person types "i wana talk
    # about my job" and the ask is the same ask: the engine has already made it "want".
    understood = memory.get("understood")
    clean = understood.get("clean") if isinstance(understood, dict) else ""
    return talkto.answer_for(clean or text, memory) or None
