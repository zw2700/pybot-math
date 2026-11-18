"""A new baby in the chat is what the next few lines are about.

People tell you the news and then talk about it for a while without naming it again: "my sister
had her baby on tuesday", "a girl, 7lb 2oz", then "what should i get them". The store keeps the
turns, so a line that names no subject can still be read as being about the baby. This answers one
question only - is the chat about a new baby - and leaves what to say to whoever asked.
"""

import re

# The words that say a baby rather than a grown-up: a line with one of these in the last few
# turns is about the baby until something else is named.
BABY_WORDS = frozenset("""
baby babies babydoll newborn babe infant toddler twins nappy nappies pram buggy cot
labour labor midwife caesarean csection breastfeeding bottle-feeding christening
""".split())

# A baby arriving, said in the words people use: "had her baby", "gave birth", "she was born",
# "he arrived on tuesday", "induced on friday".
A_BIRTH = re.compile(
    r"\b(?:had|has|having|gave|give|giving|born|arrived|arrives|delivered|induced|"
    r"in\s+labour|in\s+labor|went\s+into\s+labour|went\s+into\s+labor)\b", re.I)

# "she was born on friday" says a birth with no word about a baby in it at all. A year in the
# line is somebody's own birth, said long afterwards, and not news.
# The store keeps the words that carry meaning, so "she was born on friday" arrives as
# "born friday": the verb to look for is `born` itself.
JUST_BORN = re.compile(r"\bborn\b", re.I)
A_YEAR = re.compile(r"\b(?:19|20)\d\d\b")

# "a girl, 7lb 2oz" says the age a hospital says it, with no word about a baby at all.
A_BIRTH_WEIGHT = re.compile(r"\b\d+\s*(?:lb|lbs|pound|pounds|oz|ounces)\b", re.I)

# A line that is about somebody else's news is not about the baby: "my son starts school",
# "we are getting a puppy".
NOT_THE_BABY = re.compile(
    r"\b(?:puppy|kitten|dog|cat|lamb|calf|chick|seedling|plant)\b", re.I)

HOW_MANY_TURNS = 3


def _the_lines(memory):
    """The last few turns as words, newest first, without the line being answered."""
    lines = []
    current = memory.get("topic") if isinstance(memory, dict) else None
    if isinstance(current, dict):
        lines.append(current)
    for record in reversed((memory.get("topics") or [])[-HOW_MANY_TURNS:]):
        if isinstance(record, dict):
            lines.append(record)
    said = []
    for record in lines:
        words = record.get("words")
        text = record.get("text") or ""
        # The words a topic keeps are the ones that carry meaning, so the verb a birth is said
        # with ("we had a baby girl", "she gave birth") is not among them: the line as it was
        # typed is read beside them, which is what tells "had her baby" from "met a baby".
        said.append(" ".join([text] + list(words) if isinstance(words, list) and words else [text]))
    return said


def the_thread_has_a_new_baby(memory, understood=None):
    """True when the last few turns are about a baby arriving."""
    if not isinstance(memory, dict):
        return False
    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "")
    if line and NOT_THE_BABY.search(line):
        return False
    said = _the_lines(memory)
    if not said:
        return False
    together = " ".join(said)
    if NOT_THE_BABY.search(together):
        # a puppy and a baby in the same chat: the last thing named wins, and it is not a baby.
        return False
    words = set(re.findall(r"[a-z']+", together.lower()))
    if JUST_BORN.search(together) and not A_YEAR.search(together):
        return True
    if words & BABY_WORDS and (A_BIRTH.search(together) or A_BIRTH_WEIGHT.search(together)):
        return True
    if A_BIRTH_WEIGHT.search(together) and A_BIRTH.search(together):
        # "a girl, 7lb 2oz" right after "had her baby": the weight is what says how old it is.
        return True
    return False


def the_baby_is_new(memory, understood=None):
    """True when the baby in the chat is a newborn, so a present is the newborn kind."""
    return the_thread_has_a_new_baby(memory, understood)
