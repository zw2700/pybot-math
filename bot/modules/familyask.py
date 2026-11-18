"""A question about the bot's own family: there is no family to ask about.

People ask the bot about a life of its own the way they would ask a friend - "were your mum and
dad there", "have you got any brothers", "what did your dad say", "are your aunt and uncle
coming". The bot already has an honest answer for the singular shapes ("do you have kids" gets
"No family and no friends of my own - I'm a program"), because those are the shapes an ask was
written for. The plural, the past tense and the extended relations were read as questions about
the world instead, and went to the search hedge:

    > were your mum and dad there
    < I don't know enough to answer that honestly. A search should sort you out quickly
    > have you got any brothers
    < That's beyond what I know well, sorry. Searching for it will turn up better sources
    > what did your dad say
    < I'm not sure about that one, sorry - I'd rather not guess. A quick search online

No search engine knows whether the bot's parents were at anything, and a person being friendly
is the last moment to answer with a placeholder.

The rule is the one the rest of the bot's own life is read by, said the other way round: a
relation is a fact of a life and never a thing of the world, so "your" in front of one is the
ask, whatever the verb is and whatever follows it. What keeps the person's own family out is
the question: an ask has a question word or an auxiliary at the front, or a question mark at the
end. "give your mum a ring", "ask your dad about it" and "i rang your mum yesterday" are about
their family and keep their own reading, and so does anything that names a thing of the world
("does your gran want a curry" is the curry's turn, at a priority above this one).

The reply names the relation that was asked about, says plainly there is none, and hands the
turn back to their family, because that is what the person wanted to talk about (STYLE.md,
"Not knowing, honestly": say what you can't do in a few words, then keep going).
"""
import re

from ..compose import fallback

# Above the topic entries and above small talk, below loss (2000), grief (2100), the memory
# store's recall (7000) and safety (9000). The band says what the reading says: a relation of the
# bot's own is not a fact of the world, so no entry about the world is the specialist on the line
# ("does your sister know you talk to strangers" was answered with advice about strangers), and
# an honest answer about the bot's own life is the one thing nobody else can give.
#
# Overlap with the module that answers the bot's own life (`chat`, 300): it reads the possession
# shapes too, and here this one is in front of it. That is a choice about which honest answer a
# family question gets - this one says the same thing and hands the turn back - not a claim that
# `chat` was wrong. Every other question about the bot (its memory, its doings) is still `chat`'s:
# the patterns here are built from relations of a life, not from the word "you".
PRIORITY = 1100
ANSWERS = ("about-the-bot",)  # the reader's topic for a question about the bot itself

# The relations people ask a program about. Longest first inside the pattern so "grandad" is not
# read as "dad".
_PARENTS = ("mum", "mums", "mam", "mams", "mom", "moms", "mother", "mothers", "dad", "dads",
            "father", "fathers", "parent", "parents", "mummy", "daddy")
_GRANDPARENTS = ("gran", "grans", "granny", "grannies", "grandma", "grandmas", "grandad",
                 "grandads", "grandpa", "grandpas", "nana", "nanas", "nan", "nans", "grandparent",
                 "grandparents")
_SIBLINGS = ("brother", "brothers", "sister", "sisters", "sibling", "siblings", "half brother",
             "half sister", "stepbrother", "stepsister", "step brother", "step sister")
_CHILDREN = ("kid", "kids", "child", "children", "son", "sons", "daughter", "daughters",
             "baby", "babies", "grandchild", "grandchildren", "grandson", "granddaughter")
_PARTNER = ("wife", "wives", "husband", "husbands", "partner", "partners", "girlfriend",
            "boyfriend", "fiance", "fiancee", "other half")
_EXTENDED = ("aunt", "aunts", "auntie", "aunties", "uncle", "uncles", "cousin", "cousins",
             "nephew", "nephews", "niece", "nieces", "in law", "in laws", "mother in law",
             "father in law", "brother in law", "sister in law")
_FAMILY = ("family", "families", "relatives", "relations", "folks", "kin")

# The class of relation decides what the reply says: the bot has none of any of them, but the
# answer names the one that was asked about.
CLASSES = (
    ("grandparent", _GRANDPARENTS),
    ("parent", _PARENTS),
    ("sibling", _SIBLINGS),
    ("child", _CHILDREN),
    ("partner", _PARTNER),
    ("extended", _EXTENDED),
    ("family", _FAMILY),
)
RELATION = {}
for _class, _words in CLASSES:
    for _word in _words:
        RELATION[_word] = _class
# What a class is called when the reply names it back: the words a person used are echoed, so
# these are only for the plural-or-class cases.
_ALL_RELATIONS = sorted(RELATION, key=len, reverse=True)
THE_RELATION = re.compile(r"\b(?:your|ur|yours|you're|youre)\s+(?:\w+\s+){0,2}?(?:"
                          + "|".join(re.escape(w) for w in _ALL_RELATIONS) + r")\b", re.I)
# How people open the same ask: a conjunction, an interjection, a laugh, or the "ok," they put in
# front of a change of subject. The comma is optional, because "ok do you have a sister then" and
# "ok, do you have a sister then" are the same line.
_LEAD_IN = (r"(?:(?:and|so|but|oh|well|ok|okay|right|hey|hi|yeah|yes|no|nah|actually|honestly|"
            r"just|quick|sorry|lol|haha|ha|eh|ah|hmm|huh|then|now)\b[,!.]?\s+)*")
# The same ask said from the front: "have you got any brothers", "do you have a sister". People
# put the possession first as often as they put "your" in front of the relation, and this shape
# names no relation of anybody else's, so it is read the same way.
A_HAVE_RELATION = re.compile(
    r"^" + _LEAD_IN +
    r"(?:(?:have|has|do|does|did)\s+(?:you|u|ya)\s+(?:have\s+|got\s+|ever\s+)*"
    r"|got\s+|any\s+)"
    r"(?:any\s+|a\s+|an\s+|some\s+)?(?:"
    + "|".join(re.escape(w) for w in _ALL_RELATIONS) + r")\b", re.I)
A_RELATION = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in _ALL_RELATIONS) + r")\b", re.I)
# The count said with the relation first: "how many brothers have you got", "how many sisters do
# you have". Neither pattern above reaches it, because the relation comes before the possession,
# and it was still the search hedge on main after the possession-first shapes were taken.
HOW_MANY_RELATION = re.compile(
    r"^" + _LEAD_IN + r"how many\s+(?:\w+\s+){0,2}?(?:"
    + "|".join(re.escape(w) for w in _ALL_RELATIONS) + r")\b[\w\s,']*\b(?:you|u|ya)\b", re.I)

# An ask has a question word or an auxiliary at the front. Nothing else is taken: "i rang your
# mum yesterday" and "give your mum a ring" are about their family, not the bot's.
A_QUESTION = re.compile(
    r"^" + _LEAD_IN +
    # An ask can be an invitation to say something instead of a question word: "tell me about your
    # family", "say something about your mum", "knew much about your dad". Same ask, same reply.
    r"(?:(?:can|could|would|will)\s+you\s+)?(?:tell|told|say|talk|chat)\s+(?:me\s+)?"
    r"(?:something\s+|a\s+bit\s+|more\s+|anything\s+)?about\s+|"
    r"(?:is|are|was|were|do|does|did|have|has|had|will|would|can|could|should|shall|"
    r"who|whos|whose|what|whats|what's|where|wheres|when|whens|why|whys|how|hows|which|"
    r"any|anyone|ever|doesnt|didnt|isnt|arent|wasnt|werent)\b",
    re.I)
# "your mum and dad" is one ask about two people, and the reply echoes both.
AND_ANOTHER = re.compile(r"\band\b\s+(?:your|ur)\s+\w+", re.I)
# A question about somebody else's family that happens to use "your" is about the thing named.
# A relation somebody else has: "my mum and your dad were at it" is about their mum too. The
# articles are not in this list on purpose - "do you have a sister" and "have you got a brother"
# are the ask itself - and neither is "the", which people use for their own family ("the wife").
NOT_ABOUT_THE_BOT = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:"
    + "|".join(re.escape(w) for w in _ALL_RELATIONS) + r")\b", re.I)

# The honest part, by class. Every line says what the bot is (a program) as well as what it has
# not got: a list of missing things with no self in it reads as a machine being evasive.
NO_ONE = {
    "parent": (
        "No mum and dad of my own - I'm a program, so there's no one who brought me up to be "
        "anywhere.",
        "None on my side: I'm a program, so no parents and no childhood to have them in.",
        "I haven't got parents - I'm a program, so there's no mum and dad at the end of a phone.",
    ),
    "grandparent": (
        "No grandparents of mine - I'm a program, so nothing like that on my side.",
        "None, no: I'm a program, so no nan and grandad to go and see.",
        "I haven't got grandparents - I'm a program, so there's no family of mine at all.",
    ),
    "sibling": (
        "No brothers and no sisters - I'm a program, so no family of my own.",
        "None, no: I'm a program, so there's nobody to fall out with at Christmas.",
        "I haven't got siblings - I'm a program, so nobody grew up alongside me.",
    ),
    "child": (
        "No children of my own - I'm a program, so nobody calls me anything but the bot.",
        "None, no: I'm a program, so no kids and no school run.",
        "I haven't got any - I'm a program, so there's no family of mine to bring up.",
    ),
    "partner": (
        "Nobody like that - I'm a program, so no partner and no one to ring on the way home.",
        "None, no: I'm a program, so there's no other half on my side.",
        "I haven't got one - I'm a program, so nobody's waiting up for me.",
    ),
    "extended": (
        "None of those on my side - I'm a program, so no aunts, uncles or cousins.",
        "Nobody like that: I'm a program, so there's no family of mine to be an aunt or uncle to.",
        "I haven't got any - I'm a program, so no relatives at all.",
    ),
    "family": (
        "No family of my own - I'm a program, so there is nobody on my side of it.",
        "None, no: I'm a program, so no family, no birthday list, nobody to ask after.",
        "I haven't got any - I'm a program, so there's no family of mine at all.",
    ),
}
# The hand back to their side: the person was being friendly, so the turn goes to what they
# wanted to talk about. A past-tense ask gets a question about how it went; anything else gets
# one about the people themselves.
_HOW_IT_WENT = (
    "Tell me about yours - how did it go?",
    "How did it go with yours?",
    "What about your lot - how did it go?",
)
_THE_PEOPLE = (
    "Tell me about yours though - do you see much of them?",
    "What about your lot?",
    "How are yours doing?",
)
A_PAST_ASK = re.compile(
    r"\b(?:was|were|did|said|had|went|wore|told|thought|felt|been|there|at it|come)\b", re.I)
# A line that asked after the bot's feelings about its lot is not a line to hand straight back.
_NO_HAND_BACK = re.compile(r"\b(?:think|feel|felt|mind|care|miss|lonely|sorry|upset)\b", re.I)


def the_relation(text):
    """The relation the line asks about, echoed as the person wrote it, or None.

    "your mum and dad" comes back as "mum and dad" because that is the pair they asked about.
    """
    said = " ".join(str(text or "").split())
    match = (THE_RELATION.search(said) or A_HAVE_RELATION.match(said)
             or HOW_MANY_RELATION.match(said))
    if not match:
        return None
    words = [w.lower().strip(",.'") for w in match.group(0).split()]
    found = [w for w in words if w in RELATION]
    if not found:
        return None
    if AND_ANOTHER.search(said[match.end():]):
        rest = A_RELATION.search(said[match.end():])
        if rest and rest.group(0).lower() != found[0]:
            return found[0] + " and " + rest.group(0).lower()
    return found[0]


def the_class(text):
    """Which class of relation the line named; "family" when it names none in particular."""
    said = " ".join(str(text or "").split())
    match = (THE_RELATION.search(said) or A_HAVE_RELATION.match(said)
             or HOW_MANY_RELATION.match(said))
    if not match:
        return None
    words = [w.lower().strip(",.'") for w in match.group(0).split()]
    for word in words:
        if word in RELATION:
            return RELATION[word]
    return None


# "does your gran want a curry or a chinese" is a choice put to a relation of mine, and the answer
# that helps is the one about the food: the same question asked of a person who does not exist is a
# joke, and a dead end ("I haven't got grandparents") is the worst thing to hand back. So a line that
# offers two things ("or a chinese", but not "or not") is left to whatever knows about the things.
# A pair of relations is not a choice of two things: "have you got any brothers or sisters" is one
# ask about the family, and handing it away for being a choice left it on the search hedge.
A_CHOICE = re.compile(
    r"\bor\b\s+(?!(?:not|no|is|are|was|were|else|anything|something|otherwise)\b|(?:"
    + "|".join(re.escape(w) for w in _ALL_RELATIONS) + r")\b)\w+", re.I)


def is_a_family_ask(text):
    """True when the line asks the bot about a relation of its own, and asks at all."""
    said = " ".join(str(text or "").split())
    if not said:
        return False
    if (not THE_RELATION.search(said) and not A_HAVE_RELATION.match(said)
            and not HOW_MANY_RELATION.match(said)):
        return False
    if NOT_ABOUT_THE_BOT.search(said):
        return False
    if A_CHOICE.search(said):
        return False
    return bool(A_QUESTION.match(said) or A_HAVE_RELATION.match(said)
                or HOW_MANY_RELATION.match(said) or said.endswith("?"))


def reply_for(text, memory=None):
    """The honest answer to a question about the bot's own family, or None."""
    if not is_a_family_ask(text):
        return None
    said = " ".join(str(text or "").split())
    kind = the_class(said) or "family"
    told = NO_ONE[kind]
    said_of = _HOW_IT_WENT if A_PAST_ASK.search(said) else _THE_PEOPLE
    seed = " ".join(str(text or "").lower().split())
    honest = fallback.pick(told, memory or {}, seed)
    if _NO_HAND_BACK.search(said):
        return honest
    return honest + " " + fallback.pick(said_of, memory or {}, seed)


def TAKES_AS_IT_COMES(text, memory):
    """A question about the bot's own family is this module's line whole.

    Nobody else can answer it: the knowledge base has nothing about a program's parents, and its
    topic entries read the words of the line ("strangers", "curry") and answer a different
    question. The reading is the same one `respond` makes, so a line this module would not answer
    is not claimed either.
    """
    return is_a_family_ask(text)


def respond(text, memory):
    """The line a question about the bot's family gets; None for every other line."""
    if not isinstance(memory, dict):
        memory = {}
    return reply_for(text, memory)
