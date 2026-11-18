"""A line that takes issue with the answer just given is answered about that answer.

A person who says the bot's own last sentence makes no sense is not shrugging at the weather and
is not upset about something of their own: they are asking for it again, or they think it is
wrong. Nothing in the line names a thing of its own, so no knowledge entry can answer it, and
every fallback pool on main read it as a shrug or as bad news about the person:

    that makes no sense        -> "Fair enough."
    that doesnt make sense     -> "I'm listening - say more if it helps."
    youre not making sense     -> "Thanks for telling me - I'm here if you want to dig into any
                                  of that."
    that cant be right         -> "Got it. Is there anything you'd like a hand with?"
    youre confusing me         -> "Got it. Is there anything you'd like a hand with?"

Each one says the bot heard nothing, when the person has just said the bot's paragraph did not
land. The reading here is deliberately narrow, because the same words are ordinary inside a
sentence about something else: "it doesnt make sense to buy new" is a line about buying new and
"that makes no sense, the council said they would ring" is a line about the council. Only a doubt
that is *what the line says*, bar a little chatter after it, is read here.

Two things are told apart, because they want different answers. A line that says the answer is
*wrong* ("that cant be right", "are you sure") is conceding nothing of the person's: the bot says
where it got it, since the person has already pointed at what they doubt. A line that says it is
*unclear* ("i dont follow", "youre confusing me") is the bot's paragraph failing, so the bot owns
that ("That is on me") rather than sending the person away to say it better - the fault is the
sentence the bot chose, not the person's words.

Where the bot has a real answer it can hand back plainer, it does that instead of asking which
bit: "i dont follow" after the egg card wants the first move again in fewer words, and
`bot/memory/meant.py` already knows how to do that. Its "nothing of mine to go back over yet" is
not a hand-back, so that is left to the pool.
"""
import re

from ..compose import pick
from . import meant

# A line that takes issue with the answer just given. It names nothing of its own - the thing it
# is about is the bot's own last line - so no knowledge entry can answer it, and every fallback
# pool reads it as a shrug or as the person being upset.
DOUBTS_THE_ANSWER = re.compile(
    r"\b(?:that|this|it|you|youre|you're)\s+(?:makes?|made|making|doesnt|doesn't|isnt|isn't|are|"
    r"arent|aren't)\s+(?:no|not|any)\s+(?:sense|sensible)\b"
    r"|\b(?:not|never) making (?:any )?sense\b"
    r"|\b(?:doesnt|doesn't|didnt|didn't|wouldnt|wouldn't|wont|won't)\s+(?:make|makes|made)\s+"
    r"(?:any\s+)?sense\b"
    r"|\bare you (?:sure|certain)\b|\byou sure\b"
    r"|\b(?:that|this|it) (?:cant|can't|cannot|doesnt|doesn't|wont|won't) be right\b"
    r"|\b(?:thats|that's|this is) (?:nonsense|rubbish|wrong|not right|a load of)\b"
    r"|\b(?:youre|you're|you are|u r) (?:confusing|confused) me\b"
    r"|\bi (?:dont|don't) follow\b|\bi (?:dont|don't) get (?:that|this|it)\b",
    re.I)

# The doubt that says the answer is wrong rather than unclear, which is answered by saying where
# it came from rather than by asking which bit: the person has already said which bit is wrong,
# and being asked to repeat it reads as stalling.
SAYS_THE_ANSWER_IS_WRONG = re.compile(
    r"\b(?:cant|can't|cannot|doesnt|doesn't|wont|won't) be right\b"
    r"|\b(?:nonsense|rubbish|not right|wrong|a load of)\b"
    r"|\bare you (?:sure|certain)\b|\byou sure\b", re.I)

# The chatter a doubt can end on and still be the whole of the line: "that makes no sense tbh".
DOUBT_TAIL = frozenset("""at all though tho tbh really sorry mate love god no way innit like
    ok okay then haha lol""".split())

# A person who says the answer did not add up, and does not say which bit: the bot owns it,
# because it wrote the sentence. Borrowing the "confused" pool here read as a fault in the
# person's own words ("say it the way it is in your head") when the fault is the paragraph the
# bot chose.
UNCLEAR_ANSWER = (
    "That is on me. Which bit was the muddled one?",
    "Fair enough. Say which part and I will put it another way.",
    "Let me try that again, plainer. Which bit lost you?",
)

# A person who thinks the answer is wrong: the bot says where it came from, and does not pretend
# to have been unclear. It names what it can check (a fact can be out of date) without inventing
# a source it does not have.
DOUBTING = (
    "Fair enough to check it. Which bit looks wrong, and I'll say where I got it.",
    "Then I may have it wrong. Say what you were expecting and we'll compare the two.",
    "It could be out of date, that is a real risk with these things. Point at the part and I will "
    "go through it.",
)

# The words the repeat reader puts in front of a line it hands back, so a reply that hands one
# back can be told from the reader saying there is nothing of its own to go back over.
_MEANT_LEADS = tuple(sorted(lead.split("{", 1)[0].strip().lower()
                            for lead in meant.REPEAT_LEADS + meant.LEADS))

# An answer short enough to be a shrug is not a paragraph to doubt, and a line longer than this
# is carrying something of its own ("that makes no sense to me either, my sister is the same").
SHORTEST_ANSWER = 40
MOST_WORDS_IN_A_DOUBT = 9


def _the_answer_just_given(memory):
    """The bot's own last line, or "" when there is none in this conversation yet."""
    if not isinstance(memory, dict):
        return ""
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1]
    return str(last.get("bot") or "") if isinstance(last, dict) else ""


def the_doubt(text, memory):
    """Whether the line doubts the bot's own last answer: "wrong", "unclear", or None.

    Only when the bot has said something to doubt: a first line of "that makes no sense" is a
    person with nothing in front of them, and the pools for that are elsewhere.
    """
    said = _the_answer_just_given(memory)
    if len(said.strip()) < SHORTEST_ANSWER:
        return None
    line = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    words = line.split()
    if not words or len(words) > MOST_WORDS_IN_A_DOUBT:
        # A long line that carries a doubt is a new line about something of theirs ("that makes no
        # sense, the council said they would ring me"), and the things it names are the answer.
        return None
    hit = None
    for found in DOUBTS_THE_ANSWER.finditer(line):
        # The doubt has to be what the line is saying, not a clause of something else: "it doesnt
        # make sense to buy new" is about buying new, and "that makes no sense, the council said
        # they would ring" is about the council. Only the end of the line, bar chatter, counts.
        tail = line[found.end():].strip(" .,!?;:-")
        if all(word in DOUBT_TAIL for word in tail.split()):
            hit = found
    if not hit:
        return None
    if SAYS_THE_ANSWER_IS_WRONG.search(line) and not re.search(r"\bsense\b", line, re.I):
        return "wrong"
    return "unclear"


def reply_for(text, memory):
    """The reply to a line that doubts the bot's own answer, or None for every other line."""
    kind = the_doubt(text, memory)
    if kind is None:
        return None
    line = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if kind == "wrong":
        return pick(DOUBTING, memory, line)
    # Where the bot has a real answer to hand back, the reader that gives it plainer words keeps
    # the turn: "i dont follow" after the egg card wants the first move again in fewer words, and
    # `bot/memory/meant.py` already does that. Handing the same sentence back from here would look
    # identical and lose that reader's bookkeeping for the turn after ("what?" then gets "Said
    # again: ..." only because the repeat module was the one that answered). A pool line here is
    # only for the doubt the bot has no plainer answer for.
    plainer = meant.answer_for(line, memory) if isinstance(memory, dict) else None
    if plainer and plainer.lower().startswith(_MEANT_LEADS):
        return None
    return pick(UNCLEAR_ANSWER, memory, line)
