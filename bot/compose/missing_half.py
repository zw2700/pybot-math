"""A comparison of two ages where only one of the ages was ever given.

    I'm 34 and my wife is 32.
    Am I older than my brother?
      "I'm not sure about that one, sorry - I'd rather not guess. A quick search online will get
       you a solid answer, and I can help you make sense of what you find."

The store is right to keep the turn free - the wife's age is no answer to a brother whose age was
never given - but the search hedge is not true here either. Nobody's brother's age is on the web,
and the person is not asking the web: they are asking whether the numbers in front of them can be
put together, and one of the two was never said. The honest half is short and worth saying: which
ages the bot has, which one it has not got, and what would settle it.

It is asked from `bot/modules/greeting.py`, last, and only in place of a hedge, so every
comparison the store can do with two real ages is answered by the store before this is consulted.

What it keeps off, because a confident wrong line is worse than the hedge it replaces:

- a group ("who is the oldest in my family", "who is older in my class"): three or more people,
  and no line here fits;
- one made thing and a person ("am i older than my car"): the two halves are a birth and a year of
  manufacture, which is not a sum, and "when the two were made" is false about the person;
- a line whose other half is somebody else's ("is he older than his cousin"): the missing age
  belongs to the cousin, and pointing at the son would be pointing at the wrong person;
- a pair of made things where the line names the year itself.
"""
import re

# The lines that put two ages against each other. One phrase is not a family and one regex per
# phrase is a family full of holes, so this reads the comparison itself: who is older, am I older
# than, is she older than me, how much older is she, which of us is younger.
A_COMPARISON = re.compile(
    r"\bwho(?:'s|s| is| was)?\s+(?:the\s+)?(?:older|younger|eldest|oldest|youngest)\b|"
    r"\b(?:am|is|are|was|were)\b[^.!?]{0,40}\b(?:older|younger|eldest|oldest)\b|"
    r"\bhow (?:much|many years)\s+(?:older|younger)\b|"
    r"\b(?:older|younger) (?:than )?(?:me|him|her|them)\b", re.I)

# A gap rather than a verdict: "how much older is my mum". The answer to that is a number, and
# half a number is no answer at all, so `tests/test_age_compare.py` keeps this turn free and so
# does this module - the hedge that was there speaks for itself.
A_GAP = re.compile(r"\bhow\s+(?:much|many\s+years)\s+(?:older|younger)\b", re.I)

# Three or more people, or people only some of whom the bot has an age for. "Who is the oldest in
# my family" is not two things to put side by side, and the module has no line for a group.
A_GROUP = re.compile(
    r"\b(?:family|families|class|team|group|household|siblings|relatives|relations|kids|"
    r"children|brothers|sisters|friends|everyone|everybody|all of them|the rest)\b", re.I)

# The people the bot can be told an age for. A person named in the line with no age beside them is
# the half that is missing, which is the whole reason for saying anything here.
KIN = ("mum", "mam", "mom", "mother", "dad", "father", "parent", "parents", "brother", "sister",
        "son", "daughter", "child", "kid", "wife", "husband", "partner", "girlfriend",
        "boyfriend", "fiance", "fiancee", "gran", "granny", "nan", "nana", "grandma",
        "grandad", "grandpa", "grandfather", "aunt", "auntie", "uncle", "cousin", "nephew",
        "niece", "stepson", "stepdaughter", "stepdad", "stepmum", "mate", "friend", "boss",
        "colleague", "neighbour", "landlord", "flatmate", "housemate", "boy", "girl", "baby")
A_PERSON_NAMED = re.compile(r"\b(?:my|our)\s+(" + "|".join(KIN) + r")(?:'s|s')?\b", re.I)
# Something made rather than a person: "is my laptop older than my phone" is two made things, and
# a made thing's age is the year it was made, which nobody has told the bot.
A_THING_NAMED = re.compile(r"\bmy\s+([a-z][a-z'-]+)\b", re.I)
# A pronoun standing where a person would be named: "am i older than him", "is she older than me".
A_SOMEONE = re.compile(r"\b(?:him|her|them|they|he|she)\b", re.I)
# The half that is missing is somebody the line reaches through another person: "is he older than
# his cousin" is a cousin's age, and "her sister" is a sister's. The son's age is not the answer,
# so the module has nothing to point at and keeps quiet.
A_THROUGH_SOMEONE = re.compile(r"\b(?:his|hers|her|their|theirs|its)\s+[a-z][a-z'-]+", re.I)
# The person asking, as one side of the comparison.
A_MYSELF = re.compile(r"\b(?:i|i'm|im|me|my|mine|myself|we|us|our)\b", re.I)

# What the bot says. Every line gives the same two things - which ages it has, and what would
# settle the comparison - because a line that only apologised would be the hedge in a longer coat.
WITH_MINE = (
    "I've got you at {mine}, but nothing on {theirs}, so there's no two numbers to put together. "
    "Tell me that one and I'll say which of you is older.",
    "You're {mine} in what you've told me and {theirs} has no age beside it. Give me that and the "
    "comparison takes one line.",
)
WITHOUT_MINE = (
    "There's nothing beside {theirs}: I have no age of yours either. Give me both and I'll say "
    "which of you is older.",
    "The only age here would be {theirs}, and yours is the other half. Tell me yours and I'll do "
    "the rest.",
)
BOTH_MISSING = (
    "I have {known} and no age of yours, and nothing on {theirs} either. Those two numbers and the "
    "comparison takes one line.",
    "What I have is {known}; what is missing is your own age and {theirs}. Give me those and I'll "
    "say which of you is older.",
)
# One age in the store and nobody named. The number itself is not said: `tests/test_age_compare.py`
# keeps this turn free, because half an age is no answer, and it is not the half that was asked
# about. What is said is the truth about the two halves and the one thing that would finish it.
NOBODY_ELSE = (
    "Nothing beside your own age is here to put it against. Give me theirs and I'll say which of "
    "you is older.",
    "One number is not a comparison, and yours is the only one here. Tell me theirs and the answer "
    "is one line.",
)
# Two made things, with no person in the line. Their ages are years of manufacture, and where a
# year is written is the same kind of place for a fridge and for a guitar - so the line says that
# much and no more. It used to name a laptop and a phone, which is a wrong instruction for every
# other pair in the world.
TWO_THINGS = (
    "Those are two made things, so what settles it is the year each one was made - on the thing "
    "itself, on its rating label, or in its manual. Give me the two years and I'll say which is "
    "older.",
    "The age of a made thing is the year it was made, and nothing you've told me has either one. "
    "The label or the manual will have it; two years and the comparison takes one line.",
)
# One person it can only be, and their age in hand, but no age of the person's own.
THEIR_AGE_ONLY = (
    "I've got {theirs} at {their_age}, but never your age, so there is one number where there "
    "should be two. Tell me yours and I'll say which of you is older.",
    "{theirs} is {their_age} in what you've told me and your own age is not there. Give me that "
    "and the comparison takes one line.",
)
# A pronoun where a person would be named. The store points a pronoun at the person it fits and
# answers with their age, so a pronoun that reached here points at somebody whose age was never
# given - or at one of two people, which is a question rather than a sum.
# The ages in the store are not repeated here either: a wife at 32 is not an answer to a question
# about "him", and saying her age back reads as if the bot thought it was. What the bot says is
# that it cannot tell who the line means, which is the true half.
HIM_OR_HER = (
    "I've an age here and no way to tell who you mean. Say who it is and I'll put the two side by "
    "side.",
    "Nothing in the line says who that is, so there's no second age for me to reach. Name the "
    "person and the comparison takes one line.",
)
# A pronoun and one person it can only mean: the sum is the sum the store does, and saying it beats
# asking again. "am i older than her" with a mum at 70 in the store is not a question. The line
# names the two numbers the way the store's own answer does, so the shape is the one a person has
# already seen.
THEY_ARE_OLDER = ("{Theirs} is older - {their_age} to your {mine}.",)
I_AM_OLDER = ("You're older - {mine} to {theirs}'s {their_age}.",)
SAME_AGE = ("Neither of you - you're both {mine}.",)


def _choose(pool, text):
    """The same line for the same words, so a chat is not a slot machine."""
    return pool[sum(ord(one) for one in text) % len(pool)]


def _a_sentence(line):
    """A line that may open on a lower-case name ("your mum is 70 ...") said as a sentence."""
    return line[0].upper() + line[1:] if line else line


FEMALE = frozenset("mum mam mom mother sister wife gran granny nan nana grandma daughter aunt "
                    "auntie niece stepmum stepdaughter girlfriend fiancee".split())
MALE = frozenset("dad father brother husband grandad grandpa grandfather son uncle nephew stepdad "
                 "stepson boyfriend fiance".split())


def _fits(low, who):
    """Whether a pronoun in the line can only be the person the store holds under `who`."""
    if re.search(r"\b(?:them|they)\b", low):
        return True
    she = re.search(r"\bher\b|\bshe\b", low) is not None
    he = re.search(r"\bhim\b|\bhis\b|\bhe\b", low) is not None
    if she and not he:
        return who in FEMALE
    if he and not she:
        return who in MALE
    return True


def _given_beside(low, who):
    """Whether the line puts an age on this person itself ("my brother who is 40").

    A line that does has no missing half to point out, while a line that gives somebody else's age
    ("my wife is 32, am i older than my brother") still leaves the brother's missing.
    """
    return re.search(r"\bmy\s+" + who + r"\b[^.!?,]{0,16}?\b\d{1,3}\b", low) is not None


def _the_ages(memory):
    """The ages the store holds: the person's own, and the ones they gave for other people."""
    mine = None
    user = memory.get("user") or {}
    try:
        if user.get("age") is not None:
            mine = int(user.get("age"))
    except (TypeError, ValueError):
        mine = None
    others = {}
    for entry in memory.get("others") or []:
        if not isinstance(entry, dict) or entry.get("age") is None:
            continue
        who = str(entry.get("who") or "").strip().lower()
        if not who:
            continue
        try:
            others[who] = int(entry.get("age"))
        except (TypeError, ValueError):
            continue
    return mine, others


def _the_known_list(others):
    """"your wife at 32" out of the ages the store holds, in the order they were given. Said
    mid-sentence, so nothing here is capitalised: a name lifted from the store is not a sentence."""
    parts = []
    for who, age in list(others.items())[:2]:
        parts.append("your " + who + " at " + str(age))
    if len(parts) == 2:
        return parts[0] + " and " + parts[1]
    if not parts:
        return "nothing"
    return parts[0]


def the_missing_half(text, memory):
    """The age comparison said plainly when one of its two ages was never given, else ""."""
    low = " ".join(str(text or "").lower().split())
    if not low or not A_COMPARISON.search(low):
        return ""
    if A_GAP.search(low):
        return ""
    # A group is three people or more, and a comparison of a group is not two numbers.
    if A_GROUP.search(low):
        return ""
    # The half that is missing belongs to somebody the line only reaches through another person:
    # "is he older than his cousin" asks for a cousin's age, and the son's age is not the answer.
    if A_THROUGH_SOMEONE.search(low):
        return ""
    # The kind of line is not read here: this is asked only in place of a hedge, and a comparison
    # the store keeps as a fact ("my wife is older than me") is met with "Noted", not a hedge.
    mine, others = _the_ages(memory)
    named = []
    for one in A_PERSON_NAMED.findall(low):
        one = one.lower()
        if one not in named:
            named.append(one)
    things = []
    for one in A_THING_NAMED.findall(low):
        one = one.lower()
        if one not in KIN and one not in things:
            things.append(one)
    if named:
        unknown = [one for one in named if one not in others and not _given_beside(low, one)]
        if not unknown:
            # Everyone the line names has an age the store holds, so the store's own comparison
            # would have answered: another reason has kept it free, and it is not this one.
            return ""
        theirs = "your " + unknown[0]
        if things:
            # A made thing beside a person ("is my car older than my son") is a year of
            # manufacture against a birth, which is not two ages of the same kind.
            return ""
        if mine is not None:
            return _choose(WITH_MINE, low).format(mine=str(mine), theirs=theirs)
        if others:
            return _choose(BOTH_MISSING, low).format(
                known=_the_known_list(others), theirs=theirs)
        return _a_sentence(_choose(WITHOUT_MINE, low).format(theirs=theirs))
    if things:
        # Made things only when the line names two of them and no person at all.
        if len(things) >= 2 and not A_SOMEONE.search(low):
            if re.search(r"\b\d{4}\b|\b(?:19|20)\d\d\b", low):
                # The line hands over a year itself, so there is nothing missing to point out.
                return ""
            return _a_sentence(_choose(TWO_THINGS, low))
        return ""
    if not A_SOMEONE.search(low):
        if others and mine is not None:
            return ""
        if mine is not None:
            return _a_sentence(_choose(NOBODY_ELSE, low).format(mine=str(mine)))
        return ""
    # A pronoun standing for a person: the store would have pointed at them and answered if their
    # age were held, so what is missing is whoever "he" or "she" is.
    if not others:
        return ""
    # A pronoun with one person it can only be, and both ages in hand: the comparison is a sum,
    # not a question, and the store's own answer shape is what a person expects here.
    fits = [who for who in others if _fits(low, who)]
    if mine is None and len(fits) == 1:
        who = fits[0]
        return _a_sentence(_choose(THEIR_AGE_ONLY, low).format(
            theirs="your " + who, their_age=str(others[who])))
    if mine is not None and len(fits) == 1:
        who = fits[0]
        their_age = others[who]
        theirs = "your " + who
        if their_age == mine:
            return _choose(SAME_AGE, low).format(mine=str(mine))
        if their_age > mine:
            return _choose(THEY_ARE_OLDER, low).format(
                Theirs=theirs[0].upper() + theirs[1:], their_age=str(their_age),
                mine=str(mine))
        return _a_sentence(_choose(I_AM_OLDER, low).format(
            theirs=theirs, their_age=str(their_age), mine=str(mine)))
    return _a_sentence(_choose(HIM_OR_HER, low).format(known=_the_known_list(others)))


__all__ = ["the_missing_half", "A_COMPARISON"]
