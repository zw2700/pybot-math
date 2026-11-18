"""The composer's reply to a line, asked before a module answers over it.

A module that sits just above the composer floor (the greeting pool, -1000) takes every turn
nobody else claims. Most of those turns deserve taking: the echo of the person's own words, the
nod, the search hedge. Some do not, because the composer's floor is not only those three - it
answers a dog with what a dog needs, a school label with the SENCO card, a form nobody can read
with the three things to look for. A module that answered over those would be trading a real
answer for its own.

So a module asks the composer first, in the same way `bot/memory/cause.py` does
(`_the_bot_would_only_shrug`): copy the memory, put the random state back afterwards, and read
what `fallback.reply_for` says for the line on its own (`verdict=False`, the words rather than
this turn).
"""
import copy
import random
import re

from . import fallback

# The composer's own lines that answer nothing: its echo of the person's words, its nod, and the
# search hedge. `bot/memory/cause.py` keeps the same set (`NOTHING_SAID`) for the same question.
NOTHING_SAID = re.compile(
    r"\b(?:i'?m listening|say more|not sure about that one|don'?t know enough|"
    r"beyond what i know|rather not guess|everything i have on that one|"
    r"not much (?:i can add|to go on)|which bit do you|tell me more|"
    r"i'?m here if you want|anything you'?d like a hand with|thanks for telling me)\b"
    r"|\u2014\s*noted\.|\s-\s*noted\."
    # The store's own echoes: "Noted: you're not sure about your mum", "You don't know if you've
    # done something, good to know."
    r"|^noted[:.]|,\s*good to know\.?\s*$", re.I)

# "Then it's out of your hands now - when do you find out?" is the composer's answer to a doubt it
# reads as a wait. It is the right answer to "im not sure i got the place", and the wrong one to a
# choice the person is still holding, or to a form nobody can follow.
OUT_OF_THEIR_HANDS = re.compile(r"out of your hands|when do you find out", re.I)

# A line that says a thing will not go in cannot be good news, so the composer congratulating the
# person on it is a misreading rather than an answer: "im baffled by my payslip" got "Good to
# hear. What was the best bit?".
MISREAD_AS_GOOD_NEWS = re.compile(
    r"\b(?:good to hear|glad to hear|best bit|nice one|sounds alright|sounds good|"
    r"lovely|how lovely|brilliant)\b", re.I)


def what_the_composer_would_say(text, memory):
    """The composer's own reply to this line, or "" when it has none."""
    probe = copy.deepcopy(memory)
    state = random.getstate()
    try:
        # `verdict=False` is the words on their own rather than this turn, which is what the floor
        # answers: the verdict pool is the answer to a turn and would report an answer where the
        # composer would only have filled in (bot/compose/fallback.py, `reply_for`).
        return fallback.reply_for(text, probe, verdict=False) or ""
    except Exception:  # noqa: BLE001 - no composer to ask is not a reason to answer over it
        return ""
    finally:
        random.setstate(state)


def only_a_shrug(text, memory, misreads=None):
    """True when the composer has no answer of its own for this line.

    `misreads` is a pattern for the answers that are worse than nothing on this kind of line (a
    congratulation where the person said something would not go in). A reply matching it counts
    as the composer having nothing, because the line cannot mean what it read.
    """
    said = what_the_composer_would_say(text, memory)
    if not said:
        return True
    if NOTHING_SAID.search(said) or OUT_OF_THEIR_HANDS.search(said):
        return True
    if misreads is not None and misreads.search(said):
        return True
    return False
