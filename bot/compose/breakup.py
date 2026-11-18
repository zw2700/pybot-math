"""A break-up is not a broken bone, so the question after it is not about a ward.

`A_MEDICAL_THREAD` counts a body, a bed or a thing that happened to one, and `broke` and `broken`
are in it because a broken leg is a body's. `broke up` is the same two words with the ending of a
relationship on them, so a thread that said it read as an injured body and the ask that follows a
rough patch - "is she going to be ok" - was answered with the pool for somebody ill:

    my mum is having a hard time since her and dad broke up
    is she going to be ok
    >>> I would be guessing, and this is not a thing to guess about. Ask whoever is treating
        them, or ring 111.

Nobody is treating her. `fallback._a_hard_time_and_not_a_body` already keeps the ward pools off a
rough patch, and it asks `A_MEDICAL_THREAD` whether there is a body in the thread - so the one word
`up` decided it. The fix lives here rather than in that regex because `bot/compose/fallback.py` is
over the size a change may be submitted at, and this module only ever replaces a reply already
chosen from the pools that name a patient: no other reply is touched, and no line is answered that
the composer got right.
"""
import random
import re

from . import fallback

# The pools that answer a bare "is she going to be ok" by naming the people treating somebody.
# The pet pool is deliberately not here: a dog's own rough patch is not a person's, and the vet
# answer is the right one for "my dog is having a hard time since we split up".
THE_ILL_POOLS = (fallback.UNKNOWN_HOW_IT_GOES_FOR_SOMEONE
                 + fallback.UNKNOWN_HOW_LONG_IN_HOSPITAL)

# The ending of a relationship, in the words people type it in. "broken up" carries the same
# ending on the participle, and "we broke up" is the usual past tense.
A_BREAK_UP = re.compile(
    r"\b(?:broke|broken|splitting|split|breaking)\s+up\b|\bdivorce\w*\b|\bseparation\b"
    r"|\bseparated\b|\bwalked\s+out\b|\bleft\s+(?:me|him|her|them)\b|\bsplit\b")


def _thread_said(memory, line):
    """The last few turns of the talk, the bot's own included, as one lower-case string."""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)][-3:]
    said = [str(turn.get("user") or "") for turn in turns]
    said += [str(turn.get("bot") or "") for turn in turns[-1:]]
    said.append(str(line or ""))
    return " ".join(said).lower()


def answer_for(text, reply, memory):
    """The hard-patch answer where the ill-somebody pool was reached by a break-up, else None.

    Only a reply from one of those pools is replaced, and only when taking the break-up words out
    of the thread leaves nothing medical behind: `she broke her hip` / `is she going to be ok`
    keeps the ward, and so does a thread that still says hospital or chemo somewhere.
    """
    if not isinstance(memory, dict) or reply not in THE_ILL_POOLS:
        return None
    said = _thread_said(memory, text)
    if not A_BREAK_UP.search(said):
        return None
    if not fallback.A_HARD_TIME.search(said):
        return None      # a break-up on its own is not this reading's line
    without_the_split = A_BREAK_UP.sub(" ", said)
    if fallback.A_MEDICAL_THREAD.search(without_the_split):
        return None
    if fallback.AN_ILLNESS.search(without_the_split):
        return None
    pool = fallback.UNKNOWN_HOW_IT_GOES_FOR_A_HARD_TIME
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    last = str(turns[-1].get("bot") or "") if turns else ""
    fresh = [line for line in pool if line != last] or list(pool)
    # Seeded, not `random.choice`: an unseeded pick made two runs of one conversation differ, and
    # a comparison then reported a change no commit had made. Same turns and same line, same
    # sentence - the rule `bot/compose/pick` already follows for every other pool.
    seed = len(turns) * 7919 + sum(ord(c) for c in str(text or "").lower())
    return random.Random(seed).choice(fresh)
