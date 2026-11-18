"""A day that is not their best is not a good one, and it is not a search.

Three shapes reached the wrong pool on main, and both pools are wrong in the same way - they read
the words and missed that the person was reporting a bad time:

    not my best day           -> "That sounds like a good time - what was the best of it?"
    morning / could be better -> "A quick search online will get you a solid answer"
    ive had better weeks      -> "I'd rather not guess... a search will sort you out"

The first congratulates somebody on the bad day they had just reported, because "best day" is a good
word in a good-time pool that cannot see the "not" in front of it. The other two are a day graded low
by comparison rather than named bad - no BAD_STRETCH word in the line at all - so nothing in the
composer recognised them, and the understanding engine read the shape as a request and sent them to
the search hedge. Nobody looks up how their own week is going.

The reply is the warm pool a bad week already gets (`BAD_STRETCH_REPLIES`): one question back about
what has made it like that. Nothing is invented and no fact is added, and only a reply that is a
congratulation, a neutral ack or a hedge is replaced, so a line with an answer of its own keeps it.
"""
import re

from . import pick
from .fallback_data import BAD_STRETCH_REPLIES

# A good word for a day with a negator in front of it: "not my best day", "not the best day ive
# had", "not a great week". One or two words between the two, which is the widest that stays
# honest ("never had a better day" is left alone: there the negator sits in front of a comparison
# and the person is reporting the good one).
A_DAY_DENIED = re.compile(
    r"\b(?:not|never|hardly|isnt|isn't|wasnt|wasn't|arent|aren't|aint|ain't)\s+"
    r"(?:\w+\s+){0,2}"
    r"(?:the\s+)?(?:best|good|great|nice|fine|brilliant|amazing|alright|lush|smashing)\s+"
    r"(?:day|week|weekend|night|morning|evening|afternoon|shift|start|time)\b")

# The same thing said as a comparison: "ive had better days", "weve had better weeks".
A_HAD_BETTER = re.compile(
    r"\b(?:ive|i've|weve|we've|i)\s+had\s+better\s+(?:day|days|week|weeks|weekend|weekends|"
    r"night|nights|morning|mornings|evening|evenings|afternoon|shift|shifts)\b")

# "could be better" is the person's own stretch only when the line says whose it is, or when it is
# the whole line. "things could be better", "work could be better" and "i could be better" are a
# week going badly, but "could be better wifi in here", "my wifi could be better" and "the traffic
# could be better" grade a thing, and a line about how hard somebody's week has been is not an
# answer to a slow router.
A_DAY_OWNS_THE_GRADE = re.compile(
    r"(?:\b(?:i|im|i'm|we|we're|things|everything|life|work|today)\b"
    r"|\b(?:my|our)\s+(?:day|week|weekend|night|morning|evening|afternoon|shift|start|time|"
    r"life|mood|year)\b"
    r"|\bthe\s+(?:day|week|weekend|morning|night)\b)"
    r"\s+(?:could|would|can)\s+(?:have\s+been|of\s+been|be\s+going|be)\s+"
    r"(?:a\s+lot\s+|much\s+|alright\s+|ok\s+)?better\b"
    r"|\b(?:could|would)\s+be\s+going\s+better\b")
# The whole line, or the whole line and a shrug: "could be better", "could be better tbh",
# "could have been better honestly". Nothing follows it but the sort of noise a person adds after
# a flat answer, so there is no thing for the grade to belong to.
A_DAY_GRADED_ALONE = re.compile(
    r"^\W*(?:(?:it|so|well|yeah|yea|aye|oh|hi)\s+){0,2}"
    r"(?:could|would|can|might)\s+(?:have\s+been|of\s+been|be\s+going|be)\s+"
    r"(?:a\s+lot\s+|much\s+|alright\s+|ok\s+)?better\b"
    r"(?:\s+(?:tbh|honestly|today|now|so\s+far|though|i\s+guess|i\s+suppose|lately|"
    r"at\s+the\s+moment|right\s+now|this\s+week|this\s+morning|thanks|cheers)\b)*\W*$")

# A question is not a report: "is today not the best day for a bbq?" is asking about the plan, and
# the ask door is the reading that answers a question.
QUESTION_OPENERS = frozenset("""
is isnt isn't was wasnt wasn't are arent aren't do does did will would should could can may might
have has had who what when where why how
""".split())

# The replies this reading may replace, because they say the wrong thing about a bad day: a
# congratulation ("That sounds like a good time - what was the best of it?", "Nice one. How did
# the rest of it go?"), a shrug of an ack that hears the line as a fact ("Got it. Is there
# anything you'd like a hand with?", "I'm listening — say more if it helps."), and the search hedge.
A_CHEER = re.compile(
    r"\bgood time\b|\bbest of it\b|\bnice one\b|\bpleased\b|\bwhat happened\b|"
    r"\bthe best bit\b|\bhow did the rest of it go\b|\blovely\b|\bhappy for you\b|"
    r"\bgreat news\b|\bwell done\b|\bcongratulat", re.I)
A_SHRUG = re.compile(
    r"\bthanks for telling me\b|\bis there anything you'?d like a hand with\b|"
    r"\bsay more if it helps\b|\bgot it\b|\bnoted\b", re.I)


def reads_as_a_low_day(text):
    """True when the line is the person's own day or week, denied or graded low by comparison."""
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return False
    graded = bool(A_DAY_GRADED_ALONE.search(clean)) or bool(
        (A_DAY_DENIED.search(clean) or A_HAD_BETTER.search(clean)
         or A_DAY_OWNS_THE_GRADE.search(clean))
        and (clean.split() or [""])[0] not in QUESTION_OPENERS)
    return graded


def _may_replace(reply):
    """True when the composer's line says the wrong thing about a day like this.

    Only the three kinds are replaced - a congratulation, a shrug of an ack, and a hedge - so a
    card's own answer to a line that happens to carry the shape keeps the turn.
    """
    if not reply:
        return False
    from .fallback import is_a_hedge
    if is_a_hedge(reply):
        return True
    if reply.startswith("Noted:"):
        return True
    return bool(A_CHEER.search(reply) or A_SHRUG.search(reply))


def answer_for(text, reply, memory=None):
    """The bad-week pool for a day denied or graded low, or None."""
    if not reads_as_a_low_day(text):
        return None
    if not _may_replace(reply):
        return None
    return pick(BAD_STRETCH_REPLIES, memory if isinstance(memory, dict) else {}, text)
