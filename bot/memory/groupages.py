"""The ages of a group of people, kept as the list the person said.

    my parents are 66 and 70
    how old are they            ->  Your parents are 66 and 70.

    my two kids theyre 4 and 7
    how old are they again      ->  Your kids are 4 and 7.
    how old is my youngest      ->  Your youngest is 4.

The store keeps one age for the person in the chat (`memory["their_age"]`), which is right for
"how old is she" and wrong the moment a line gives two: `my two kids theyre 4 and 7` kept the 4
and dropped the 7, `how old are they again` answered "They are 4.", and `how old are my kids`
answered "You haven't told me how old they are." - a list of two is not one number, and it is not
nothing either. Every plural group fails the same way, not just children, so the reading here is
the group word and the list beside it rather than another branch about kids.

The list is kept under `memory["group_ages"]`:

    {"word": "kids", "ages": [4, 7], "line": "my two kids theyre 4 and 7"}

The last line that gives a list for a word wins, so a correction ("my kids are 5 and 8" after
"my kids are 4 and 7") is the list the answers are written from. What the reply may claim is only
what was said: the plural ask is answered from the list, the singular ask about the store's one
person is left alone, and a chat with no list in it gets nothing at all from here.
"""
import re

GROUP_WORDS = (
    "kids", "children", "sons", "daughters", "boys", "girls", "parents", "grandparents",
    "grandchildren", "grandkids", "brothers", "sisters", "twins", "cousins", "nieces",
    "nephews", "aunts", "uncles", "stepchildren", "stepkids", "in-laws", "flatmates",
    "housemates", "neighbours",
)

# The one word people use for each other that has no plural of its own in the list above.
_THE_SAME_GROUP = {
    "children": "children", "child": "children",
    "kid": "kids", "kids": "kids",
    "grandchild": "grandchildren", "grandkids": "grandchildren",
    "stepchild": "stepchildren", "stepkid": "stepkids",
}

_GROUPS = "|".join(sorted(GROUP_WORDS, key=len, reverse=True))

# An age is a plain number, and the two are joined the way a list of ages is said: "4 and 7".
_AGE = r"\d{1,3}(?![\d.])"
_A_LIST_OF_AGES = _AGE + r"(?:\s*(?:,|and|&)\s*" + _AGE + r"){1,3}"

# What may not come after a list of ages for it to be a list of ages: "my cousins 3 and 4 times",
# "the boys 2 and 3 days ago" are counts of events. "years old" is the one unit that is an age.
_NOT_A_UNIT = (r"(?!\s*(?:times|days|weeks|months|hours|minutes|miles|metres|kilometres|km|"
               r"kilos|kilograms|kg|pounds|quid|per\b|a\s+(?:week|month|year|day))"
               r"|\s*years(?!\s+old))")

# "my parents are 66 and 70", "my two kids theyre 4 and 7", "the boys are 4 and 7", "my kids
# aged 4 and 7". The copula can be left out ("my kids 4 and 7"), which is how it is said quickly.
GIVES_A_LIST = re.compile(
    r"\b(?:my|our|the|his|her)\s+(?:\w+\s+){0,2}?(?P<word>" + _GROUPS + r")\b"
    r"(?:\s+(?:are|were|is|was|aged|both))?[,\s]+(?P<ages>" + _A_LIST_OF_AGES + r")"
    r"(?![\d,.])" + _NOT_A_UNIT, re.I)

# The same list with no "my" in front, which is how it is said when the group is the subject:
# "i have 2 kids aged 4 and 7", "kids are 4 and 7 here". The copula is required with no
# determiner, because two bare numbers after a group word are a list and nothing else.
GIVES_A_LIST_BARE = re.compile(
    r"\b(?P<word>" + _GROUPS + r")\s+(?:are|were|aged|both\s+aged)\s+"
    r"(?P<ages>" + _A_LIST_OF_AGES + r")(?![\d,.])" + _NOT_A_UNIT, re.I)

# The same line with the ages attached by "theyre": "with my two kids theyre 4 and 7".
THEYRE_A_LIST = re.compile(
    r"\b(?:my|our|the)?\s*(?:\w+\s+){0,2}?(?P<word>" + _GROUPS + r")\b[^.!?]{0,20}?"
    r"\b(?:they'?re|they\s+are|both\s+aged)\s+(?P<ages>" + _A_LIST_OF_AGES + r")"
    + _NOT_A_UNIT, re.I)

# The plural ask: "how old are they", "what are their ages", "how old are the kids".
ASKS_THE_LIST = re.compile(
    r"\bhow\s+old\s+(?:are|were|is)\s+(?:they|their|(?:\w+\s+){0,2}?(?:" + _GROUPS + r"))\b"
    r"|\b(?:what|whats|what\s+are|what\s+were)\s+(?:are\s+|were\s+)?"
    r"(?:their|the|my|our)\s+(?:\w+\s+){0,2}?(?:" + _GROUPS + r"|ages)\b"
    r"|\bhow\s+old\s+are\s+(?:my|our|the)\s+(?:\w+\s+){0,2}?(?:" + _GROUPS + r")\b"
    r"|\b(?:their|the\s+kids'?|my\s+kids'?)\s+ages\b"
    r"|\bwhat\s+(?:were|are)\s+my\s+(?:\w+\s+){0,2}?(?:" + _GROUPS + r")\s+ages\b", re.I)

# The ask that picks one of the list by position: "how old is my youngest", "how old is the
# oldest one". The list is what makes these answerable; without one they are advice questions.
ASKS_THE_END_ONE = re.compile(
    r"\bhow\s+old\s+(?:is|was)\s+(?:your\s+|the\s+|my\s+|our\s+)?"
    r"(?P<which>youngest|oldest|elder|eldest|older|younger|little|big|little\s+one|big\s+one)\b",
    re.I)


def _the_word(word):
    """The group word as the answer says it, or "" for a word that is not a group."""
    found = str(word or "").lower().strip()
    found = _THE_SAME_GROUP.get(found, found)
    return found if found in GROUP_WORDS else ""


def _ages_in(value):
    """The ages a match holds, as integers, in the order they were said."""
    return [int(number) for number in re.findall(r"\d{1,3}", str(value or ""))]


def the_list_given(text):
    """The group word and the ages the line gives, or None.

    Two ages at least: a line with one age is a single person and belongs to the store's own
    reading, which is what `memory["their_age"]` already is.
    """
    line = str(text or "")
    for pattern in (GIVES_A_LIST, GIVES_A_LIST_BARE, THEYRE_A_LIST):
        found = pattern.search(line)
        if found is None:
            continue
        word = _the_word(found.group("word"))
        ages = _ages_in(found.group("ages"))
        if word and len(ages) >= 2:
            return word, ages
    return None


def watch(text, memory):
    """Keep the list a line gives, so the ask a turn later is answered from it."""
    if not isinstance(memory, dict):
        return
    given = the_list_given(text)
    if not given:
        return
    word, ages = given
    memory["group_ages"] = {"word": word, "ages": ages, "line": " ".join(str(text).split())}


def _the_kept(memory):
    """The group and the ages the chat holds, or ("" , []) when it holds none."""
    if not isinstance(memory, dict):
        return "", []
    kept = memory.get("group_ages")
    if not isinstance(kept, dict):
        return "", []
    word = _the_word(kept.get("word"))
    ages = [age for age in kept.get("ages") or [] if isinstance(age, int)]
    if not word or len(ages) < 2:
        return "", []
    return word, ages


def _a_list(ages):
    """The ages as a person says them: "4 and 7", "4, 7 and 9"."""
    said = [str(age) for age in ages]
    if len(said) == 1:
        return said[0]
    return "%s and %s" % (", ".join(said[:-1]), said[-1])


# A group word is a plural, and the singular of the one the chat holds is often a different
# word: "my children" is a child, "my parents" a parent.
_THE_SINGULARS = {
    "children": ("child",), "kids": ("kid", "child"), "parents": ("parent",),
    "people": ("person",), "men": ("man",), "women": ("woman",),
    "twins": ("twin",), "boys": ("boy",), "girls": ("girl",),
    "sisters": ("sister",), "brothers": ("brother",),
    "sons": ("son",), "daughters": ("daughter",),
    "grandchildren": ("grandchild",), "grandparents": ("grandparent",),
    "aunts": ("aunt",), "uncles": ("uncle",), "nieces": ("niece",), "nephews": ("nephew",),
    "cousins": ("cousin",), "flatmates": ("flatmate",), "roommates": ("roommate",),
    "friends": ("friend",), "neighbours": ("neighbour",), "grandkids": ("grandkid",),
}


def _the_singulars(word):
    """The singular of the group word the chat holds, in the words a ask may put after it."""
    word = str(word or "")
    out = set(_THE_SINGULARS.get(word, ()))
    if word.endswith("s"):
        out.add(word[:-1])
    return {one for one in out if one}


def _the_end_one_is_the_group(text, end_one, word):
    """Whether the end-of-the-list ask is about the group the chat holds.

    "how old is my oldest", "how old is my oldest one" and "how old is my oldest kid" leave the
    group to the chat or name it; "how old is my oldest cat" names a cat, and a list of the
    kids' ages is not a cat's. A noun after the end-one word that is not the group's own
    singular is not this reader's line.
    """
    after = str(text or "")[end_one.end():]
    words = [said for said in re.split(r"[^a-z']+", after.lower()) if said]
    if not words:
        return True
    first = words[0]
    if first in ("one", "ones", "of"):
        return True
    return first in _the_singulars(word)


def _the_group_asked(text, word):
    """The group word the ask names, "" when it names no group, or None when it names another.

    A line that names a group the chat has no list for gets nothing: "how old are the girls"
    after a line about the parents is a question about people nobody has described.
    """
    line = str(text or "").lower()
    named = [found for found in GROUP_WORDS if re.search(r"\b%s\b" % re.escape(found), line)]
    named = [_the_word(found) for found in named]
    if not named:
        return ""
    return word if word in named else None


def reply_for(text, memory):
    """The reply to an ask about the ages the chat holds, or "" for every other line."""
    word, ages = _the_kept(memory)
    if not word or not ages:
        return ""
    line = str(text or "")
    asked = _the_group_asked(line, word)
    if asked is None:
        return ""
    end_one = ASKS_THE_END_ONE.search(line)
    if end_one is not None and not _the_end_one_is_the_group(line, end_one, word):
        return ""
    if end_one is not None and asked == "":
        which = end_one.group("which").lower()
        if which in ("youngest", "younger", "little", "little one"):
            return "Your youngest is %d." % min(ages)
        return "Your oldest is %d." % max(ages)
    if end_one is not None:
        # The group is named as well as the end of it: "how old is my youngest kid".
        which = end_one.group("which").lower()
        if which in ("youngest", "younger", "little", "little one"):
            return "Your youngest %s is %d." % (word[:-1] if word.endswith("s") else word,
                                                min(ages))
        return "Your oldest %s is %d." % (word[:-1] if word.endswith("s") else word, max(ages))
    if not ASKS_THE_LIST.search(line):
        return ""
    return "Your %s are %s." % (word, _a_list(ages))


def asks_for_the_list(text, memory):
    """True when the line asks for the ages of the group the chat holds."""
    return bool(reply_for(text, memory))
