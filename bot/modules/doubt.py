"""A line that takes issue with the bot's own answer is answered about that answer.

"that makes no sense", "that cant be right", "youre confusing me" name nothing of their own: the
thing they are about is the paragraph the bot has just printed. On main every one of them was read
as a shrug or as bad news about the person ("Fair enough.", "Thanks for telling me - I'm here if
you want to dig into any of that"), which is the bot saying it heard nothing at the one moment the
person is telling it the answer failed.

The reading and the wording live in `bot/memory/doubt.py`, next to the store it reads; this module
is here so the claim has a band of its own. It sits above the small talk (`chat.py`, 300), which is
what answered these lines with a stock nod, and below the safety band: a line in a crisis is never
this module's, however it is phrased. Nothing is claimed from any other module's real answer -
`respond` returns None on every line that is not a doubt about the bot's own last sentence.
"""
from ..memory import doubt

# Above the small talk (chat, 300) - it is that module's stock nod these lines were getting - and
# below the store (7000) and the safety band (9000 and up).
PRIORITY = 400

# The reading could not settle which thing the word means: "the bank was closed" was answered
# with how to close a bank account and "the seal is broken" with "Ugh, those are fiddly". The
# knowledge base stands down on these lines (bot/modules/answers.py), and this asks which one is
# meant. See TWO_LIVES in bot/understanding/topics.py for the words and the cues that settle them.
SUBJECT_UNCLEAR = (
    "I'm not sure which {word} you mean - a word or two about it and I'll answer the right one.",
    "Which {word} do you mean? Tell me a bit more and I'll take it from there.",
    "There's more than one thing '{word}' could mean. What's the one you're asking about?",
)


def _the_question(text, word):
    """One of the lines above, chosen by the line so the same chat does not repeat one."""
    at = sum(ord(letter) for letter in (text or "")) % len(SUBJECT_UNCLEAR)
    return SUBJECT_UNCLEAR[at].format(word=word)


def respond(text, memory):
    """The reply to a doubt about the bot's own last answer, or None for every other line."""
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(understood, dict) and understood.get("subject_unclear"):
        return _the_question(text, understood["subject_unclear"])
    return doubt.reply_for(text, memory)
