"""A question about this conversation itself is answered plainly, by the bot, in its own words.

"How long can we talk for", "is there a limit to how long we can talk", "have you got all day" and
"how many messages can i send you" ask how long the conversation can run, and "am i boring you",
"am i keeping you up", "am i talking too much", "do you want me to stop" ask whether the person is
being a nuisance. Both are questions only the bot can answer, and both were answered by something
else: the search hedge ("I'd rather not guess - a quick search online will get you a solid
answer"), the identity card ("I'm a chatbot - here to help and chat"), the message template (three
lines to write to your landlord) and, for "am i boring you", the advice to try a jigsaw.

The reading is `bot/understanding/kinds.py`, which says which of the two the line is
(`understood["about_bot_kind"]`, `"while"` or `"keeping"`). Nothing here reads words itself: a line
that asks about a fridge, a bill, a tablet or a lunch break is not one of these, and the reading
says so before this module sees it.

The answer is short and honest. Nobody at this end watches a clock, so there is no limit to give;
the bot is following what the person says, so the answer to "am i boring you" is no, and it says
how it would tell them if it lost the thread. Then it hands the floor back.
"""
import hashlib
import re

from ..understanding.kinds import a_stop_ask

# A count is not a length: "how many messages can i send you" asked how many, and the answer to
# "how long" ("as long as you like") reads as a dodge. Read on the line, in the one place that
# needs it, so the reading keeps one kind for both and nothing else learns a vocabulary of counts.
_A_COUNT = re.compile(r"\bhow\s+many\b", re.I)
COUNT_LINES = (
    "As many as you like - there's no cap on messages here, so send them as they come.",
    "No limit on messages: as many as you want, long or short.",
    "Send as many as you like; there's no count I'm keeping.",
)

# Above the store (7000), because a line like "how long have you got" is answered by the store's
# line about remembering only this conversation, and above the small talk (chat, 300). Below the
# safety band: a line about a real emergency is never this, and the reading has to say so first.
PRIORITY = 7400

# How long this conversation can go. Three phrasings, so a person who asks twice gets a different
# sentence the second time (see `repeat`).
WHILE_LINES = (
    "As long as you like — I'm not watching a clock, and nothing else is waiting on me. Say when "
    "you've had enough and I'll leave it there.",
    "No limit I can see: there's nowhere else I need to be, so take the time you need. If you'd "
    "rather pick it up later, that's fine too.",
    "All the time you want — I'm not counting lines or minutes, and I keep the thread while we "
    "talk. Say the word when you want to stop.",
    "There's no clock on this at my end. Go at your own pace, and if you'd rather stop and come "
    "back to it, that's no trouble.",
)

# Whether the person is keeping the bot too long. The answer is the bot's own, and it is no.
KEEPING_LINES = (
    "Not at all — carry on, I'm following. Say the rest of it.",
    "No, and I'd say so if it got hard to follow. Keep going.",
    "You're not boring me. Take as long as it needs.",
    "Not a bit of it. Nothing else is happening at this end, so go on.",
    "You're fine. I'm reading all of it, and I'll ask if I lose the thread.",
)

# What the bot asks back. It is a question, so the person keeps talking rather than the reply
# ending the exchange.
WHILE_TAILS = (
    "",
    "Where were we?",
    "What were you in the middle of?",
)
# A person asking whether they are a nuisance is mid-sentence, so the answer ends on "keep going"
# and hands the floor back by itself: a second question after it reads as shutting them up.
KEEPING_TAILS = ("",)


def _seed(text):
    """A number that stands for this line, so the same words always get the same reply."""
    return int.from_bytes(hashlib.sha1(str(text or "").encode("utf-8")).digest()[:6], "big")


def _pick(lines, text):
    """One line, chosen by the line itself, so the same words get the same reply."""
    return lines[_seed(text) % len(lines)]


# A bare "should i stop" is about the thing in hand, not about this conversation. "im trying to
# lose a stone", "i started running last week", "my knee hurts now", "should i stop" - the last
# line asks whether to stop the running, and it was answered "You're not boring me. Take as long as
# it needs.", which answers a question about the chat. The bot is asked whether the person is a
# nuisance only when nothing else is in hand: "am i boring you" and "do you want me to stop" name
# the talk, so they are that whatever the chat is on (the reading in `bot/understanding/kinds.py`
# keeps them, and they never reach the gate below). The bare stop-ask names nothing of its own, so
# the thing the chat is on decides it: when that is a thing the knowledge base answers, the ask is
# a follow-up about the thing and is read with the rest of them.
# The stop the person asks about their own doing: "should i stop", "shall i quit", "should i give
# up". "do you want me to stop" is the other side of it - a question about the bot's wishes, not
# about the running - so it keeps its warm answer whatever the chat is on, and so does "am i
# boring you".
THEIR_OWN_STOP = re.compile(
    r"(?:should|shall|can|could|may)\s+(?:i|we)\s+"
    r"(?:stop|quit|give\s+up|pack\s+it\s+in|leave\s+it|jack\s+it\s+in)"
    r"(?:\s+(?:now|then|it|this|that|doing\s+(?:it|this|that)))?\s*[.!?]*")


def _a_bare_stop_about_a_thing(text, memory):
    """True when a bare "should i stop" is about the thing the chat is on, not about the chat."""
    said = " ".join(str(text or "").lower().split())
    if not THEIR_OWN_STOP.fullmatch(said):
        return False
    # The same reading the rest of the bot uses, on the same normalised line the test above reads:
    # "Should I stop?" with a capital and a question mark is the line the test writes, and reading
    # the raw one as well was two readings of one thing.
    if not a_stop_ask(said):
        return False
    topic = (memory or {}).get("topic") or {}
    # Anything of the person's in hand is a thing the stop could be about, and the knowledge base
    # having a row for it was the wrong test: "i smoke about 20 a day", "im 40", "should i quit" is
    # the smoking, and no entry answers "i smoke about 20 a day", so the line kept "Not at all -
    # carry on, I'm following." The topic is the reading; the entry is one way to have a topic.
    return bool(str(topic.get("text") or "").strip())


def _the_kind(understood):
    if not isinstance(understood, dict):
        return None
    kind = understood.get("about_bot_kind")
    return kind if kind in ("while", "keeping") else None


def _already_said(memory):
    """What the bot said last, so the same sentence is not repeated to a person who asks twice."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1]
    if isinstance(last, dict):
        return str(last.get("bot") or "")
    return ""


def TAKES_AS_IT_COMES(text, memory=None):
    """This line is answered as it comes: nobody else can answer a question about this chat.

    The store takes these lines itself ("do i talk too much" was read as a thing called "too
    much", and answered "There's nothing on too much in what I keep"), and a take is settled by
    PRIORITY: this module sits above the store so the claim is its own.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    return _the_kind(understood) is not None


def respond(text, memory):
    """The reply for a question about how long this chat can go, or whether they are a nuisance."""
    understood = memory.get("understood") if isinstance(memory, dict) else None
    kind = _the_kind(understood)
    if kind is None:
        return None
    if kind == "keeping" and _a_bare_stop_about_a_thing(text, memory):
        return None
    said = _already_said(memory)
    if kind == "while" and _A_COUNT.search(str(text or "")):
        lines, tails = COUNT_LINES, ("",)
    elif kind == "while":
        lines, tails = WHILE_LINES, WHILE_TAILS
    else:
        lines, tails = KEEPING_LINES, KEEPING_TAILS
    order = _rotate(lines, text)
    for line in order:
        if line not in said:
            break
    else:
        line = order[0]
    tail = _pick(tails, text + " tail")
    return (line + (" " + tail if tail else "")).strip()


def _rotate(lines, text):
    """The pool in an order that starts where this line's digest points."""
    at = _seed(text) % len(lines)
    return tuple(lines[at:]) + tuple(lines[:at])
