"""Somebody asks this bot for room to talk about a thing of theirs, and names the thing.

"can you talk to me about my anxiety" got the search hedge ("I don't know enough to answer that
honestly. A search should sort you out quickly") - which is no answer at all: nobody wants a search
engine for that. The bot can do the one thing asked for, which is talk with them, and the honest
reply is a yes in a few words and the one question that starts it: STYLE.md's "Not knowing,
honestly" and its one short question in the same breath.

The ask is read, not listed: "can you talk to me about X", "can we talk about X", "can i talk to
you about X", "i want / need / would like to talk about X", "talk to me about X", and the same
frames with "think" and "work" ("can you help me think about my options"). The thing named is said
back in the person's own words with the possessive turned round ("my job" is "your job"), because
the thing named is the thing they want to talk about.

Narrow on purpose. It wants the bot addressed - a person in the line asking for the bot's ear - so
"he wont talk to me about it" and "my daughter wont talk about it" are somebody else's refusal and
keep the reply they had. It only ever replaces one of the composer's own shrugs, so a card that
answers the line stands, and a crisis line never reaches here.
"""
import re

from . import pick

# The ask, as a whole line, in the frames people use.
_LEAD = r"(?:(?:ok|okay|so|right|hi|hey|well)\s+)?"
_POLITE = r"(?:(?:please|just)\s+)?"
_TALK = r"(?:talk|chat|speak)"
_VERB = (r"(?:want|wanna|need|needed|would\s+like|'?d\s+like|have\s+to|got\s+to|gotta|"
         r"have|got)")

TALK_ASKS = tuple(re.compile(_LEAD + pattern) for pattern in (
    # "can you talk to me about my anxiety", "could you talk with me about it"
    r"(?:can|could|would|will)\s+you\s+" + _POLITE + _TALK +
    r"\s+(?:to|with)\s+me\s+(?:about|through)\s+(?P<subject>.+)$",
    # "can we talk about what happened", "can i talk to you about my debt"
    r"(?:can|could|may)\s+(?:i|we)\s+(?:please\s+)?" + _TALK +
    r"(?:\s+(?:to|with)\s+you)?\s+(?:about|through)\s+(?P<subject>.+)$",
    # "i want to talk about my job", "we need to talk about us"
    r"(?:i|we)\s+(?:just\s+|really\s+|honestly\s+)?" + _VERB +
    r"\s+(?:to\s+)?" + _TALK +
    r"(?:\s+(?:to|with)\s+you)?\s+(?:about|through)\s+(?P<subject>.+)$",
    # "talk to me about grief"
    _POLITE + _TALK + r"\s+to\s+me\s+(?:about|through)\s+(?P<subject>.+)$",
    # "can you help me think about my options", "help me talk it through"
    r"(?:can|could|would|will)\s+you\s+" + _POLITE +
    r"help\s+me\s+(?:think|talk|work)\s+(?:about|through|out)\s+(?P<subject>.+)$",
    # "i need to think about my options", "i want to work through what happened"
    r"(?:i|we)\s+(?:just\s+|really\s+)?" + _VERB +
    r"\s+(?:to\s+)?(?:think|work)\s+(?:about|through|out)\s+(?P<subject>.+)$",
))

# A name that stands for the thing they have not said yet is not a subject: "can i talk to you
# about something" is already answered well by the opener pool ("Ask away, I'm listening").
BLANK_SUBJECTS = frozenset((
    "it", "this", "that", "them", "something", "somethin", "anything", "everything",
    "stuff", "a thing", "one thing", "it all", "something else",
))
# The words that are not part of the thing named: "i want to talk about my job with you".
_SUBJECT_TAIL = re.compile(
    r"\s+(?:with|to)\s+(?:you|me)\s*$|\s+(?:again|please|now|today|tonight|later|tomorrow|"
    r"sometime|soon|this\s+(?:evening|afternoon|morning|weekend)|next\s+week)\s*$")
# A time said between the verb and the thing is not part of the thing: "can we talk tomorrow about
# the rent" is the same ask as "can we talk about the rent", said by somebody with a day in mind.
# It is dropped before the frames are matched, because every frame wants the preposition straight
# after the verb and the whole line is matched as one pattern.
# The times people name, in one place: a day, a part of a day, or "when you have a minute". Both
# the reader below and the bare-invitation frame are built from it, so a time added here is read in
# both places rather than in one.
_WHEN = (r"(?:again|now|today|tonight|tomorrow|later|sometime|soon|"
         r"this\s+(?:evening|afternoon|morning|weekend)|next\s+week|"
         r"when\s+(?:you\s+)?(?:have|get|'ve\s+got)\s+a\s+(?:minute|mo|moment))")
_A_TIME_BEFORE_THE_THING = re.compile(
    r"\b(talk|chat|speak|think|work)\s+(?:to\s+(?:you|me)\s+)?"
    r"(?:" + _WHEN + r"\s+)+(?=(?:about|through|out)\b)")
_SUBJECT_HEAD = re.compile(r"^(?:the|that|this)\s+thing\s+(?:about|with)\s+")
# "can we talk about something else, films maybe" names the new thing after the one it is not: the
# person has said what they want to talk about, and saying "something else" back to them is the
# same shrug in their own words.
_SOMETHING_ELSE = re.compile(
    r"^(?:something|anything|somebody|anybody|a\s+different\s+thing|something\s+different|"
    r"another\s+thing|anything\s+else\s+at\s+all)\s+else\s*[,;:\-\u2013\u2014]?\s*")
# The thing named stops at the first clause that is about it rather than part of it: "i want to
# talk about my job its getting on top of me" names the job, and the rest is why.
_SUBJECT_END = re.compile(
    r"\s+(?:its|it's|it is|it was|it's|and|but|because|cos|cuz|coz|so|which|that|who|"
    r"i|ive|i've|we|were|we're|he|she|they|my|our)\b.*$")
# A subject that is a clause rather than a name - "how much i drink", "what i should do about my
# sister", "whether i should move" - is not cut at the pronoun inside it: the " i" in "how much i
# drink" is the person speaking, which is the whole clause, and cutting there left the reply naming
# "how much" and "whether". The conjunction at the end of a clause is still a cut.
_CLAUSE_START = re.compile(
    r"^(?:how|what|why|whether|if|when|where|which|who|whoever|whatever)\b")
# "so" is left out here even though it joins clauses: "why i am so tired" is one clause, and cutting
# at it named "why i am".
_SUBJECT_END_CLAUSE = re.compile(
    r"\s+(?:its|it's|it is|it was|and|but|because|cos|cuz|coz|which|that)\b.*$")
_HEDGED_END = re.compile(r"\s*,?\s*(?:maybe|perhaps|i\s+think|i\s+reckon|if\s+that\s+is\s+ok)\s*$")

# "my job" is "your job" when the bot says it back; "our" is "your" too, and a name stays as it is.
_OWNERS = (("my", "your"), ("our", "your"))

# An ask for the bot's ear with a time on it and no thing named - "can we talk tomorrow", "can i
# talk to you later" - is an invitation, and the only answer it wants is a yes and the question.
# Nothing else in the bot reads it: the frames below want a thing after "about", so the line fell
# to the search hedge, which tells somebody who asked for a conversation to go and search for one.
_A_BARE_INVITATION = re.compile(
    _LEAD + r"(?:(?:can|could|may|shall|should)\s+(?:i|we)\s+" + _POLITE +
    r"|(?:i|we)\s+" + _VERB + r"\s+(?:to\s+)?|" + _POLITE + r")"
    r"(?:talk|chat|speak)(?:\s+(?:to|with)\s+(?:you|me))?"
    r"(?:\s+" + _WHEN + r")+\s*[?.!]*$")
# The same words have to carry an ask: a modal or a "want" in front of the verb, or a question mark
# at the end. "chat to you soon", "talk later", "speak tomorrow" are how a person ends a
# conversation, and answering one with "what do you want to talk about?" is talking over a goodbye.
_A_LEAD_IN_FRONT = re.compile(
    _LEAD + r"(?:(?:can|could|may|shall|should)\s+(?:i|we)\s+" + _POLITE +
    r"|(?:i|we)\s+" + _VERB + r"\s+(?:to\s+)?)"
    r"(?:talk|chat|speak)")
# Each one is a yes and the question that starts it - STYLE.md's one short question - so a person
# who asked whether they can talk gets to talk.
INVITED = (
    "Yes - I'm here whenever you are. What's on your mind?",
    "Any time. What is it you want to talk about?",
    "Of course. What's going on, and where do you want to start?",
)

POOL = (
    "Of course. Tell me about {thing} - what's the part that's bothering you most?",
    "{Thing} it is. What's on your mind about it?",
    "Happy to. Where do you want to start with {thing}?",
    "Right, {thing} - go on. What's the bit you want to think out loud about?",
)
# Two of the four read for a clause as well as a name, and only those two are used for one: "How
# much i drink it is." and "Where do you want to start with how much i drink?" are not English.
POOL_CLAUSE = (POOL[0], POOL[3])
# "can you help me think about my options" is the same yes and a narrower question: the options
# are what is being weighed, so asking what they are is the whole opening move.
WEIGHING = (
    "Yes. What are the options you're weighing, as they stand now?",
    "Let's lay them out. What's on each side of it?",
    "Of course. What would you lose with each one?",
)
WEIGHING_WORDS = frozenset("""
options option choice choices decision decisions pros cons
""".split())


# The few spellings the frames themselves are typed in when somebody is typing fast. The
# understanding engine makes most of them the same line and "u" and "ur" it leaves alone, and the
# ask is the same ask either way: "can i talk to u about my debts" is somebody asking for the ear.
_TYPED_SHORT = (("u", "you"), ("ya", "you"), ("ur", "your"), ("yr", "your"),
                ("wana", "want"), ("wanna", "want"), ("wanta", "want"))
_REPEATED_WORD = re.compile(r"\b(\w+)(\s+\1\b)+")


def _as_typed(line):
    """The line with the chat-speak the frames use spelled out and a doubled word collapsed."""
    line = _REPEATED_WORD.sub(r"\1", line)
    words = [_TYPED_SHORT_DICT.get(word, word) for word in line.split()]
    return " ".join(words)


_TYPED_SHORT_DICT = dict(_TYPED_SHORT)


def the_line_as_read(text):
    """The line the frames are matched against: chat-speak spelled out, a named day dropped.

    `bot/modules/talkto.py` looks the line up in the knowledge base to see whether a card answers
    the thing named, and it has to ask about the same line this reader read - otherwise a day in
    the ask ("can we talk tomorrow about my mum") makes the lookup miss the carers card and this
    module takes a turn a card answers better.
    """
    return _A_TIME_BEFORE_THE_THING.sub(r"\1 ", _as_typed(text))


def _subject(text):
    """The thing named after the talk frame, or "" when none is named."""
    text = the_line_as_read(text)
    for pattern in TALK_ASKS:
        found = pattern.match(text)
        if not found:
            continue
        subject = " " + found.group("subject").strip().rstrip(".!?,")
        subject = _SUBJECT_TAIL.sub("", subject).strip()
        subject = _SUBJECT_HEAD.sub("", subject).strip()
        subject = _SOMETHING_ELSE.sub("", subject).strip()
        clause = bool(_CLAUSE_START.match(subject))
        subject = (_SUBJECT_END_CLAUSE if clause else _SUBJECT_END).sub("", subject).strip()
        subject = _HEDGED_END.sub("", subject).strip()
        if subject in BLANK_SUBJECTS:
            return ""
        words = subject.split()
        # A clause is longer than a name - "what i should do about my sister" is seven words - and
        # a clause cut to five words is a fragment. Nine is the same limit with room for the one
        # clause.
        if not words or len(words) > (9 if clause else 5):
            return ""
        for mine, theirs in _OWNERS:
            if words[0] == mine:
                words[0] = theirs
                break
        return " ".join(words)
    return ""


def answer_for(text, memory):
    """A yes and the one question that starts it, or "" when the line is not this ask."""
    line = " ".join((text or "").lower().split())
    if not line:
        return ""
    subject = _subject(line)
    if not subject:
        # A time and nothing else is an invitation rather than a thing to talk about.
        typed = _as_typed(line)
        if _A_BARE_INVITATION.match(typed) and (_A_LEAD_IN_FRONT.match(typed)
                                               or typed.rstrip().endswith("?")):
            return pick(INVITED, memory or {}, text)
        return ""
    if set(subject.split()) & WEIGHING_WORDS:
        return pick(WEIGHING, memory or {}, text)
    frames = POOL_CLAUSE if _CLAUSE_START.match(subject) else POOL
    lines = [one.format(thing=subject, Thing=subject[:1].upper() + subject[1:])
             for one in frames]
    return pick(lines, memory or {}, text)
