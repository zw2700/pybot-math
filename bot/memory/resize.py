"""A follow-up that only changes a figure: the same question, with the new figure in it.

"how long do i cook a 2kg chicken for" ... "what about a 3kg one" is one question asked twice.
The ask is the same and only the weight has changed, but read on its own the second line names
nothing ("a 3kg one"), so no entry fits it and the bot shrugs at a question it has just answered
in full for the smaller bird. Said again with the figure the earlier line had and the new one in
its place, it reaches the same entry, and the knowledge base works the new weight out from its
own rule ("20 minutes per 500g plus 20").

A headcount works the same way: "how much rice for 4 people" then "actually only 3 people" is
that question for three, and the portion answer gives 225 g rather than the 300 g for four it
had just given. The count is a figure of the same kind as the weight, and the one people correct
most often.

Only a line that names a figure of its own is rewritten, only when the earlier line named a
figure of the same kind, and only when nothing else the line says is a subject of its own. The
rewritten line still has to reach an entry, which is the caller's check: this module offers a
reading, it does not answer.
"""
import re

# A figure with the unit that says what it is a figure of: "3kg", "1.5 kilos", "2 litres". A bare
# count ("and for 4", "what about 6") is left alone, because a line with no unit says nothing
# about what the figure counts.
QUANTITY = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*"
    r"(kg|kilos?|kilograms?|g|grams?|lb|lbs|pounds?|oz|litres?|liters?)\b", re.I)
# A headcount, with the word that makes it one: "3 people", "four of us", "2 guests". A number
# with no unit says nothing about what it counts, which is why the table below is read only when
# the line says the word - or when the line is nothing but a new figure (see `headcount`).
COUNT = (r"(?:\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)")
HEADCOUNT = re.compile(
    r"(?<![\w.])(" + COUNT + r")\s+"
    r"(?:people|persons?|adults?|kids|children|guests?|lads|mates|friends|of us|of them|of you)\b", re.I)
# What the words of a line can be and still leave only a new headcount: "make it for 3", "only
# 3", "3 instead", "we're 6 now". Anything else in the line is a subject of its own, and a line
# with one is not this question.
ONLY_A_COUNT = frozenset("""
    a about actually and are for instead it it's its just make no not now of only please so
    sorry that the there too us wait we we're were
""".split())
_A_PORTION_ASK = re.compile(r"\bhow (?:much|many)\b", re.I)
# A rate of money: "50 a month", "£75 each week", "200 per month". It is a figure with a unit
# in its own right, like a weight, and the unit is the period. "5 km a week" is not one: the
# money is what makes it a rate, so nothing but a sum, a pound sign or the word pounds can sit
# between the figure and the period.
RATE = re.compile(
    r"(?<![\w.])£?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:pounds?|quid)?\s*"
    r"(a|per|each|every|/)\s*(month|week|fortnight|year)\b", re.I)
RATE_UNIT = {"month": "a month", "week": "a week", "fortnight": "a fortnight",
             "year": "a year"}
# What a line can say around a bare figure and still be only that figure: "what if i do 100",
# "and if i could do 150", "what about 200", "make it 75". A line with any other word in it names
# a subject of its own, and a figure with a subject of its own is not a corrected rate.
# The words a rate is corrected in are frame words too: "actually i think i can do 200", "i can
# only manage 150 now", "lets say 250 instead", "i can stretch to 300". Leaving them out read the
# figure as a pot of its own - "For £200: £100 a month is 2 months" - for a chat whose rate the
# person was trying to change.
ONLY_A_RATE = frozenset("""
    a about actually afford and at be bump can could do for guess i if instead it just let lets
    make maybe manage more much now of only or please rather really say so still stretch that
    think to up want was we what would you
""".split())
# A bare figure is a correction of the figure on the table only when the line says so - "make it
# 3", "3 instead", "only 3", "actually 3". "and for 4" after the timing for a 2kg bird asks
# for four of something else, and swapping the weight for it would answer a question nobody
# asked, so a bare figure with no word like these behind it is left alone.
A_REPLACEMENT = re.compile(r"\b(?:make|instead|actually|only|just|no|not|wait|sorry|now)\b", re.I)
# Somebody is not at the table. "one of them isnt coming", "two of them cant make it", "one of
# them doesnt eat rice": the figure is how many are out, and the table is the earlier total with
# them taken off it. Without a total on the table there is nothing to take them off, so the line
# is answered by whatever else it says, never with a portion for the people who are out.
SOMEONE_OUT = re.compile(
    r"\b(?:is|are|was|were|isn'?t|aren'?t|isnt|arent)\s+not\b"
    r"|\b(?:isn'?t|aren'?t|not)\s+(?:coming|eating|having|joining)\b"
    r"|\bcan'?t\b|\bcannot\b|\bwont\b|\bwon'?t\b|\bca\s*n'?t\b"
    r"|\b(?:doesn'?t|does not|dont|do not)\s+(?:eat|want|like|come)\b"
    r"|\bpulled out\b|\bdropped out\b|\bflaked\b|\bcancelled\b|\bcanceled\b"
    r"|\b(?:is|are)\s+(?:ill|unwell|sick|away)\b|\b(?:isnt|isn'?t)\s+(?:well|free)\b",
    re.I)
# A figure about part of the company, never the company: "two of them are kids", "one of them is
# a toddler", "one of them is allergic to gluten". The table is still the total the chat asked
# about, so the figure is not a new headcount - reading it as one under-portions for everybody
# ("150 g for two" when six are eating). The people who are out are the other case, above: they
# are taken off the total, and that line says so.
SOME_OF_THEM = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|a couple)"
    r"\s+of\s+(?:them|those|us|you)\s+(?:is|are|was|were|has|have)\b",
    re.I)
# ...unless the figure is who is at the table doing the eating: "actually only 3 of them are
# eating" is the company for this meal, so it stands as the new total.
STILL_AT_THE_TABLE = re.compile(
    r"\bof\s+(?:them|those|us|you)\s+(?:is|are|was|were)\s+(?:still\s+)?"
    r"(?:eating|having|coming|drinking|joining|there|in|here)\b",
    re.I)
# The person words a table is counted in, for a line that counts two groups at once: "3 kids and
# 2 adults" is five people at the table, so the figures are added rather than one of them read.
_GROUP = (r"(?:people|persons?|adults?|kids?|children|guests?|lads?|mates?|friends?|boys?|girls?"
          r"|men|women|veg(?:etarian)?s?|veggies|teenagers?|toddlers?|grown-?ups?|of us|of them"
          r"|of you)")
_TWO_COUNTS = re.compile(
    r"(?<![\w.])(" + COUNT + r")\s+" + _GROUP + r"", re.I)
_WORD_VALUE = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
               "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
FAMILY = {"kg": "weight", "kilo": "weight", "kilos": "weight", "kilogram": "weight",
          "kilograms": "weight", "g": "weight", "gram": "weight", "grams": "weight",
          "lb": "weight", "lbs": "weight", "pound": "weight", "pounds": "weight",
          "oz": "weight", "litre": "volume", "litres": "volume", "liter": "volume",
          "liters": "volume"}


def quantity(text):
    """The figure in a line and what it is a figure of: "a 3kg one" -> (3.0, "kg", span)."""
    said = " ".join(str(text or "").lower().split())
    found = QUANTITY.search(said)
    if not found:
        return None
    try:
        value = float(found.group(1))
    except ValueError:
        return None
    unit = found.group(2)
    return value, unit, found.span(), FAMILY.get(unit, "")


def _earlier_lines(memory, n=4):
    """The person's own lines before this one, newest first."""
    from . import recent

    lines = []
    for turn in recent(memory, n + 1):
        said = (turn.get("user") if isinstance(turn, dict) else "") or ""
        said = " ".join(str(said).split())
        if said:
            lines.append(said)
    return lines[:n]


def rate(text):
    """The money a line puts by each period: "50 a month" -> (50.0, "month", span, "rate")."""
    said = " ".join(str(text or "").lower().split())
    found = RATE.search(said)
    if not found:
        return None
    try:
        value = float(found.group(1).replace(",", ""))
    except ValueError:
        return None
    return value, found.group(3), found.span(), "rate"


# A figure named as what they are going for now, not as the rate: "i actually want 3000
# instead", "actually i need 3500". The aim word makes the sum the pot, and the correction on it
# says it is a new pot. Read as a rate it was "£3,000 a month is £36,000 in a year and £180,000 in
# five", which is arithmetic for a rate nobody said.
AIMS_AT_A_FIGURE = re.compile(r"\b(?:want|wants|need|needs|save|saving|target|aim|aiming)\b",
                             re.I)
A_CORRECTION = re.compile(r"\b(?:actually|instead|rather|only|just)\b", re.I)


def _a_bare_rate(text):
    """The figure in a line that says nothing but a new figure: "what if i do 100" -> 100.0.

    Allowed only when every other word is a frame word ("what if", "make it", "say"), so a figure
    with a subject of its own ("100 calories a day", "20 press ups") is left alone. What the
    figure is a figure of comes from the earlier line, which is where a correction points.
    """
    said = " ".join(str(text or "").lower().split())
    if not said or len(said.split()) > 8:
        return None
    found = re.search(r"(?<![\w.])£?(\d[\d,]*(?:\.\d+)?)\s*(?:pounds?|quid)?", said)
    if not found:
        return None
    others = [w.strip(".,!?;:\"'") for w in said.split()]
    others = [w for w in others if w and w not in ONLY_A_RATE]
    if others != [found.group(0).strip()]:
        return None
    if AIMS_AT_A_FIGURE.search(said) and A_CORRECTION.search(said):
        return None  # a new pot named with an aim word, not a rate to put on the old one
    try:
        return float(found.group(1).replace(",", ""))
    except ValueError:
        return None


def _with_a_new_rate(said, value, unit, memory):
    """The earlier line's rate swapped for this one, or None.

    "i can put away 50 a month" then "what if i do 100" is that line with a new rate in it: the
    goal is the same one, and the money entry works out how long it takes at 100. The period is
    the new line's own when it names one ("what about 200 a week") and the earlier line's when it
    does not, because that is where a bare figure gets its meaning. A line with no rate in the
    chat before it is not a corrected rate.
    """
    for earlier in _earlier_lines(memory):
        there = rate(earlier)
        if there is None or (unit is None and there[0] == value):
            continue
        period = unit or there[1]
        start, end = there[2]
        low = " ".join(earlier.lower().split())
        candidate = (low[:start] + ("%g " % value) + RATE_UNIT[period] + low[end:]).strip()
        if candidate != said.lower():
            return candidate
    return None


def _value(raw):
    """The number a word or a figure stands for: "three" and "3" are both 3."""
    raw = str(raw or "").strip().lower()
    if raw.isdigit():
        return int(raw)
    return _WORD_VALUE.get(raw)


def headcount(text):
    """The number of people a line gives and where it stands: "only 3 people" -> (3, 5, 6).

    A figure counts as a headcount when the line says what it counts ("3 people", "two of us",
    "4 guests"), or when the line is nothing but a new figure for the table already on the table
    ("make it for 3", "3 instead", "we're 6 now"): the earlier line is where the number of
    people comes from, and a person correcting it says the new number on its own. A bare figure
    in a line with any other subject is left alone, because nothing says what it counts.
    """
    said = " ".join(str(text or "").lower().split())
    if not said:
        return None
    groups = list(_TWO_COUNTS.finditer(said))
    if len(groups) > 1:
        # A table counted in two groups: "3 kids and 2 adults" is five at the table, and taking
        # the first figure would answer for three.
        total = _value(groups[0].group(1)) or 0
        for more in groups[1:]:
            total += _value(more.group(1)) or 0
        if total:
            return (total, groups[0].start(1), groups[-1].end(1))
    found = HEADCOUNT.search(said)
    if found:
        value = _value(found.group(1))
        return (value, found.start(1), found.end(1)) if value else None
    if len(said.split()) > 6:
        return None
    number = re.search(r"(?<![\w.])(" + COUNT + r")\b", said)
    if not number:
        return None
    others = [w.strip(".,!?;:\"'") for w in said.split()]
    others = [w for w in others if w and w not in ONLY_A_COUNT]
    if len(others) != 1:
        return None
    value = _value(number.group(1))
    return (value, number.start(1), number.end(1)) if value else None


def _a_question(earlier):
    """Whether the earlier line asked something, so the rewrite is an answer rather than a fact."""
    said = " ".join(str(earlier or "").lower().split())
    return bool(re.search(r"\b(?:how|what|which)\b", said) or said.endswith("?"))


def _the_ones_left(value, memory):
    """The table with the people who are out taken off it, or None when there is no table.

    "one of them isnt coming" after a question for eight is that question for seven: the figure
    in the line is how many are out, not the new total. Nothing is returned when no earlier line
    names a table, and nothing when the sum leaves nobody, because a portion for one person is
    worse than leaving the earlier answer alone.
    """
    for earlier in _earlier_lines(memory):
        there = headcount(earlier)
        if there is None:
            continue
        left = there[0] - value
        return left if left >= 1 else None
    return None


def _with_a_new_table(said, value, memory):
    """The portion question on the table, asked for a new number of people, or None.

    "how much rice for 4 people" then "actually only 3 people" is that question for three, and
    the portion tables work out the new total from their own per-person figure. The earlier line
    has to be a question and has to name the table, so a count in a statement is not read as one
    ("we are 4 people" then "make it 6" is not a portion ask).
    """
    for earlier in _earlier_lines(memory):
        if not _a_question(earlier):
            continue
        there = headcount(earlier)
        if there is None or there[0] == value:
            continue
        low = " ".join(earlier.lower().split())
        candidate = (low[:there[1]] + str(value) + low[there[2]:]).strip()
        if candidate != said.lower():
            return candidate
    # The table was named a line earlier than the question ("we are 6 on saturday", "how much
    # rice", "actually only 4 of us"): the question is the line to ask again, with the corrected
    # table in it. Only a portion ask, "how much" or "how many" of a thing, so a question about
    # a time or a size never gets a headcount stuck on the end of it.
    earlier_ask = next((line for line in _earlier_lines(memory)
                        if _a_question(line) and _A_PORTION_ASK.search(line.lower())
                        and headcount(line) is None), None)
    if earlier_ask:
        return "%s for %d people" % (" ".join(earlier_ask.lower().split()).rstrip("?. "), value)
    return None


def _with_a_new_weight(said, value, memory):
    """The earlier question with its figure swapped for this one, or None.

    The figure carries its unit when the line gives one ("what about a 3kg one") and takes the
    earlier line's unit when it does not ("make it 3" after "how long do i cook a 2kg chicken
    for"): the earlier question is where the number gets its meaning. A figure of another kind
    (litres after a weight) is not the same question, and the same figure again is no change.
    """
    now = quantity(said)
    unit = None
    family = None
    if now is not None:
        value, unit, _span, family = now
    for earlier in _earlier_lines(memory):
        there = quantity(earlier)
        if there is None or there[0] == value:
            continue
        if unit is None:
            if not _a_question(earlier):
                continue
            unit, family = there[1], there[3]
        elif there[3] != family:
            continue
        start, end = there[2]
        low = " ".join(earlier.lower().split())
        candidate = (low[:start] + ("%g" % value) + unit + low[end:]).strip()
        if candidate != said.lower():
            return candidate
    return None


def rewritten(text, memory):
    """The line read with the earlier line's figure swapped for this one, or None.

    "what about a 3kg one" after "how long do i cook a 2kg chicken for" is read as "how long do
    i cook a 3kg chicken for". A line whose figure is the same as the earlier one is no change,
    and a figure of another kind (litres after a weight) is not the same question.
    """
    said = " ".join(str(text or "").split())
    if not said or len(said.split()) > 10:
        return None
    now = rate(said)
    if now is not None:
        return _with_a_new_rate(said, now[0], now[1], memory)
    bare = _a_bare_rate(said)
    if bare is not None:
        # "what if i do 100" after "i can put away 50 a month": the figure is a new rate, and the
        # goal it counts towards is the one already in the chat.
        resized = _with_a_new_rate(said, bare, None, memory)
        if resized:
            return resized
    if quantity(said) is not None:
        return _with_a_new_weight(said, None, memory)
    table = headcount(said)
    if table is not None:
        value = table[0]
        if SOMEONE_OUT.search(said):
            left = _the_ones_left(value, memory)
            return _with_a_new_table(said, left, memory) if left else None
        if SOME_OF_THEM.search(said) and not STILL_AT_THE_TABLE.search(said):
            # "two of them are kids" says who is at the table, not how many: the total stands.
            return None
        if HEADCOUNT.search(said.lower()):
            return _with_a_new_table(said, value, memory)
        if not A_REPLACEMENT.search(said):
            return None
        # A bare figure corrects whatever figure is on the table: the table of people when the
        # question was about one ("only 3" after a question for four), and the weight when it
        # was a roast ("make it 3" after the timing for a 2kg bird).
        return (_with_a_new_table(said, value, memory)
                or _with_a_new_weight(said, value, memory)
                or _with_a_new_rate(said, value, None, memory))
    return None
