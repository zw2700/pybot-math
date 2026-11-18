"""The thing a line says it cannot follow: "the instructions are confusing".

Read once per turn for every module, from `bot/understanding/__init__.py`. It is a reading of its
own with its own words and shapes - which thing the line names, and how it says it - so it lives
here rather than at the end of kinds.py.
"""

# ---------------------------------------------------------------------------
# "im confused" is the speaker's state (the `confused` key above) and the reply asks which part is
# foggy. "the instructions are confusing" is the *thing's* state, and there the person has already
# said where the missing bit is: in the instructions. On main that line got "I'm listening - say
# more if it helps", which asks them to start again, and "i dont understand the instructions" got
# "Thanks for telling me" - the line the bot gives a message it heard nothing in. A friend asks
# about the instructions.
#
# The words are the ones the mood keys already use ("confusing", "baffled", "a nightmare"), so
# what makes a line this reading's is the grammar, not the word: a named thing in front of the
# adjective ("the instructions are confusing", "the wording is impossible"), a named thing after a
# verb of following ("i cant follow the recipe", "i dont understand the instructions"), a feeling
# with the thing after "by" ("im baffled by my payslip"), or a picture of a head that will not
# take it in ("my head is spinning with all this"). The thing is what the reply needs, so a line
# that names only "it" or "this" is read with `thing` None rather than guessed at.

import re

from .kinds import DENY_BEFORE


# The words a thing is named with. A clause that opens on one of these names something; "why shes
# angry" and "what i did" are questions about a clause, not a thing to ask about.
CONFUSION_A_THING = (r"(?:the|this|that|these|those|my|our|your|his|her|their|its|a|an)"
                     r"\s+(?:[a-z'-]+\s+){0,8}?[a-z'-]+")
# Where a long thing stops: "the instructions for the new boiler in my flat are confusing" names
# the instructions, and the words after them are not what to ask about. The words that join one
# thing to the next cut the thing there, and what is left is trimmed of the little words a
# capture drags in at its end.
CONFUSION_CUT = frozenset("""
of for with and in at to from about by on that which but so because when if as while
""".split())
CONFUSION_TRAILING = frozenset("""
the a an it its is are was were this these those my our me i we you
""".split())
CONFUSION_SAID_OF_A_THING = re.compile(
    r"\b(?P<thing>" + CONFUSION_A_THING + r")\s+"
    r"(?:is|are|was|were|looks?|seems?|reads?|sounds?)\s+"
    r"(?:(?:so|really|very|totally|just|completely|properly|bloody|dead|too|all)\s+)?"
    r"(?P<cue>confusing|baffling|impossible|incomprehensible|unreadable|a nightmare|double dutch|"
    r"gobbledygook)\b")
CONFUSION_POINTS_AT_NOTHING = re.compile(
    r"\b(?:this|that|it|all this|all of this|everything|the whole thing)\s+(?:is|are|was)\s+"
    r"(?:(?:so|really|very|totally|just|completely|properly)\s+)?"
    r"(?P<cue>confusing|baffling|impossible|incomprehensible|a nightmare|double dutch)\b")
CONFUSION_CANNOT_FOLLOW = re.compile(
    r"\b(?:i|we)\s+(?:just\s+|still\s+|really\s+|honestly\s+|literally\s+|even\s+)?"
    r"(?:can not|cannot|cant|could not|couldnt|do not|dont|did not|didnt)\s+"
    r"(?P<cue>follow|understand|make\s+sense\s+of|figure\s+out|work\s+out|get)\s+"
    r"(?P<thing>" + CONFUSION_A_THING + r")")
CONFUSION_BY_A_THING = re.compile(
    r"\b(?:i am|im|i feel|i felt|i was|i get|i got|we are|we got|were|feeling)\s+"
    r"(?:(?:so|really|totally|completely|properly|just|a bit)\s+)?"
    r"(?P<cue>baffled|lost|stumped|puzzled|confused|flummoxed)\s+"
    r"(?:by|with|on|at)\s+(?P<thing>" + CONFUSION_A_THING + r")")
CONFUSION_HARD_TO = re.compile(
    r"\b(?P<thing>" + CONFUSION_A_THING + r")\s+"
    r"(?:is|are|was|were)\s+"
    r"(?:(?:so|really|very|too|just|almost)\s+)?"
    r"(?:impossible|hard|difficult|tough|not\s+easy|awkward)\s+to\s+"
    r"(?P<cue>read|follow|understand|fill\s+in|make\s+sense\s+of|work\s+out|get\s+through)\b")
CONFUSION_HEAD_NOR_TAIL = re.compile(
    r"\b(?:i|we)\s+(?:(?:just|still|really)\s+)?"
    r"(?:can not|cannot|cant|could not|couldnt|do not|dont|did not|didnt)\s+"
    r"(?P<cue>make|tell)\s+(?:head|heads)\s+(?:nor|or)\s+tail\s+of\s+"
    r"(?P<thing>" + CONFUSION_A_THING + r")")
CONFUSION_MAKES_NO_SENSE = re.compile(
    r"\b(?P<thing>" + CONFUSION_A_THING + r")\s+"
    r"(?P<cue>makes|made|does not make|doesnt make|did not make|didnt make)\s+"
    r"(?:any\s+|no\s+|much\s+)?sense\b")
CONFUSION_HEAD_SPINNING = re.compile(
    r"\bmy\s+head\s+(?:is|was|'s)\s+(?:spinning|swimming|in a spin|all over the place)\b"
    # A head that spins *with* something is taking in too much of it; a head that spins *after*
    # the news, or on its own, is how the person feels, which is the mood pools' turn.
    r"\s+(?:with|from|over)\s+"
    r"(?P<thing>(?:(?:all|both)\s+(?:of\s+)?)?" + CONFUSION_A_THING +
    r"|all\s+(?:this|that|it)|everything|it)\b")


# The "not" that belongs to the verb is not a denial of it: "i cant follow" is normalised to "i
# can not follow", and the negator check below reads that "not" as a person saying they do follow.
CONFUSION_HELPER_NOT = re.compile(
    r"\b(?:can\s+not|cannot|do\s+not|dont|does\s+not|doesnt|did\s+not|didnt|could\s+not|"
    r"couldnt|would\s+not|wouldnt|will\s+not|wont|shall\s+not|should\s+not|shouldnt|"
    r"is\s+not|isnt|are\s+not|arent|was\s+not|wasnt|were\s+not|werent|have\s+not|havent|"
    r"has\s+not|hasnt|had\s+not|hadnt|must\s+not)\s*$")


def _a_confusion_ruled_out(before_cue):
    """True when the words in front of the cue rule it out ("im not confused about the manual")."""
    return bool(DENY_BEFORE.search(CONFUSION_HELPER_NOT.sub("", before_cue)))


def _a_thing_trimmed(thing):
    """The thing itself: up to where it is joined to something else, then trimmed of little words.

    "the instructions for the new boiler" is the instructions, and "this" or "it" on its own names
    nothing to ask about.
    """
    words = []
    for word in (thing or "").split():
        if word in CONFUSION_CUT:
            break
        words.append(word)
    while words and words[-1] in CONFUSION_TRAILING:
        words.pop()
    if len(words) < 2 or not any(word not in CONFUSION_TRAILING for word in words[1:]):
        return None
    return " ".join(words)


def confusion_of(line):
    """The thing the line says it cannot follow, as {"shape", "thing"}, or None.

    `shape` says how the line said it - `said_of_a_thing` ("the instructions are confusing"),
    `cannot_follow` ("i cant follow the recipe"), `by_a_thing` ("im baffled by my payslip"),
    `head_spinning` ("my head is spinning with all this") or `nothing_named` ("this is so
    confusing") - and `thing` is the thing itself, or None when the line named none.

    None for a line that rules it out ("im not confused", "the instructions are not confusing"),
    for someone else's trouble ("my son cant follow the instructions"), and for every line with no
    thing that will not go in, which is what keeps "i dont understand why shes angry" (a question
    about her) and "im confused" (the state, nothing named) where they were.
    """
    for clause in [part.strip() for part in str(line.get("norm_text") or "").split("|")]:
        if not clause:
            continue
        found = CONFUSION_POINTS_AT_NOTHING.search(clause)
        if found:
            return {"shape": "nothing_named", "thing": None}
        # "the leaflet is impossible to read" is read as hard_to, so the "to read" shape is tried
        # before the plain one; both are the same thing said with a different word.
        for pattern, shape in ((CONFUSION_HARD_TO, "hard_to"),
                               (CONFUSION_SAID_OF_A_THING, "said_of_a_thing"),
                               (CONFUSION_MAKES_NO_SENSE, "said_of_a_thing"),
                               (CONFUSION_CANNOT_FOLLOW, "cannot_follow"),
                               (CONFUSION_HEAD_NOR_TAIL, "cannot_follow"),
                               (CONFUSION_BY_A_THING, "by_a_thing"),
                               (CONFUSION_HEAD_SPINNING, "head_spinning")):
            found = pattern.search(clause)
            if not found:
                continue
            # "im not confused about the manual" and "the instructions are not confusing" rule the
            # state out, so there is nothing to ask about. The check is on the words in front of
            # the cue, because the cue can be said with its own no in it ("the manual makes no
            # sense") without being ruled out.
            before_cue = clause[:found.start("cue")] if "cue" in found.groupdict() else clause[:found.start()]
            if _a_confusion_ruled_out(before_cue):
                continue
            thing = _a_thing_trimmed(found.groupdict().get("thing"))
            return {"shape": shape, "thing": thing}
    return None
