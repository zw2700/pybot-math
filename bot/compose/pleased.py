"""A pleased remark is answered as pleasure, not as something to look up.

"What a lovely day", "what a beautiful morning", "what a brilliant day" and "what a gorgeous day"
all reach the composer's search hedge on main - "A quick search online will get you a solid
answer" - and so do the short ones that carry the same feeling with no thing in them: "what a
relief", "what a result". Nothing about the weather is being asked and nothing needs looking up;
the person has said that something is good, and the reply a friend gives says so back in a few
words and gives them somewhere to go with it.

The bad half of the same shape already reads well ("what a nightmare" gets "Ouch is right. Go
on.", "what a shame" gets "What happened, then?"), which is the whole reading this file needs: the
feeling is in the words "what a" and in whether the word after them is one of pleasure. The pool
that follows is the one thing the bot can honestly do with a good moment it cannot see - say it
sounds good and ask one light question about it - and the outside words (a day, a morning, a
window) get the pool that talks about being out in it, because that is what people say next.

Two things are deliberately left alone. A thing that is not good however the adjective reads
("what a fine mess", "a great shame") is a complaint, and it stands down here. And a remark that
names nothing of its own and has no adjective ("what a day") is already read as a rough one by
`bot/modules/chat.py`; if this file took it, a hard day would be congratulated.

This is a last resort and it is written to be one: `bot/modules/greeting.py` asks it where the
other readers of a hedge are asked, and only a hedge is replaced.
"""
import re

from . import pick

# The words of pleasure that can sit between "what a" and the thing. "fine" is not here: "what a
# fine mess" is the commonest use of it, and it is a complaint.
GOOD = (r"lovely|beautiful|gorgeous|brilliant|great|wonderful|fantastic|perfect|cracking|"
        r"smashing|nice|amazing|glorious|grand|super|fab|stunning|lush|decent")

# A thing that can follow "what a": short, because a long line has a subject of its own.
THING = r"[a-z][a-z' -]{0,24}"

# The thing itself, when the pleasure is about being out in it.
OUTSIDE = frozenset(("day", "morning", "afternoon", "evening", "weather", "sun", "sunshine",
                     "sky", "view", "sunset", "sunrise", "night", "light", "breeze"))

# A thing that is not good however the adjective reads: "what a great shame" is not pleasure.
NOT_GOOD = frozenset("""
mess shame pity nightmare waste disaster worry state pain fuss palaver joke
""".split())

WHAT_A = re.compile(r"^(?:oh|ah|wow|ooh)[,\s]+what a\s+(?:" + GOOD + r")\s+(?P<thing>" + THING +
                    r")$|^(?:what|such) a\s+(?:" + GOOD + r")\s+(?P<thing2>" + THING + r")$")
RELIEF_LINE = re.compile(r"^(?:what|such) a (?:relief|weight off|load off)$|^that'?s? a relief$")
RESULT_LINE = re.compile(r"^(?:what|such) a (?:result|win|good result|great result)$")
NEWS_LINE = re.compile(r"^(?:lovely|great|wonderful|brilliant|smashing|nice) news$")

PLEASED = (
    "Good to hear. What are you up to today?",
    "Nice one. Make the most of it - what's the plan?",
    "That's good. Tell me about it.",
)
OUT_IN_IT = (
    "Good to hear. Are you getting out in it?",
    "Lovely. What are you up to today?",
    "That's the kind of day to be outside. What's the plan?",
)
RELIEF = (
    "That's a weight off. What was it about?",
    "Good - that's the end of it, then. What changed?",
    "Phew. What was it in the end?",
)
NEWS = (
    "Good news. What is it?",
    "Nice one. Tell me.",
    "Lovely. What's happened?",
)
RESULT = (
    "Good result. What was it for?",
    "Nice one. Tell me how it went.",
    "That's a good one. What happened?",
)


def _thing(match):
    return (match.group("thing") or match.group("thing2") or "").strip()


def answer_for(text, memory=None):
    line = " ".join((text or "").lower().split()).rstrip(" .!,;:")
    if not line or len(line.split()) > 6:
        return None
    if "?" in line:
        return None
    if RELIEF_LINE.match(line):
        return pick(list(RELIEF), memory or {}, line)
    if RESULT_LINE.match(line):
        return pick(list(RESULT), memory or {}, line)
    if NEWS_LINE.match(line):
        return pick(list(NEWS), memory or {}, line)
    match = WHAT_A.match(line)
    if not match:
        return None
    thing = _thing(match)
    words = set(thing.split())
    if not thing or words & NOT_GOOD:
        return None
    pool = OUT_IN_IT if words & OUTSIDE else PLEASED
    return pick(list(pool), memory or {}, line)
