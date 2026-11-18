"""Whether the answer already on the table is the amount the person asked about.

"is that enough", "how much more do i need", "is 300 too much" - the figure in the answer and the
figure the person said have to be put side by side before anything can be said about them, and the
units have to match (a week of something is not a month of it). No other reader in the store needs
any of it: `enough_reply` is the whole surface, and it returns None for every other line.

Moved out of `memory_store` whole, constants and all, because that file is over the 1 MB the Hub
will accept in a pull request: see `bot/memory/times.py` for the first move of this kind.
"""
import re

from ..knowledge import units
from ..memory.spoken import _spoken_as_numbers
from ..memory.store_lines import (NUMBER_WORDS, _AMOUNTS, _AMOUNT_WORDS, _COUNT_WORD, _CONVERT,
                                  _UNIT_SAID, _WEEKLY)


ENOUGH_ASK = re.compile(
    r"\bis (?:that|this|it) (?:enough|too much|too little|too often|about right|alright|ok|okay"
    r"|fine|any good)\b"
    r"|\bam i (?:doing|getting|eating|drinking|having|sleeping) enough\b"
    r"|\bis that (?:a )?(?:good|healthy|normal|right) amount\b"
    r"|\b(?:will|would|does) that (?:be )?(?:enough|work|do|help)\b"
    # The figure they are asking about can be in the ask itself - "is 5 hours enough", "is 1200
    # enough" - and this is one of the ways people ask it.
    r"|\bis\s+(?:\d[\d,]*(?:\.\d+)?|once|twice|one|two|three|four|five|six|seven|eight"
    r"|nine|ten|eleven|twelve)(?:[ -][a-z]{2,12}){0,2}\s+(?:enough|too much|too often"
    r"|too little|about right|alright|ok|okay|fine)\b",
    re.I,
)
# The same pair of figures answers "how much more do i need?": the gap between what they do and
# what the answer named.
HOW_MORE = re.compile(
    r"\bhow (?:much|many) (?:more|extra)\b|\bwhat (?:else|more) (?:do|should) i (?:need|add)\b",
    re.I,
)
# An answer whose advice is to see someone about it is not naming a figure to reach: "if you are
# drinking far more than usual and still thirsty, see a GP" answered "that is more than the 1.5 to
# 2 litres that answer named, so trim it back towards that", which is advice against a doctor's.
_A_DOCTOR = re.compile(r"\b(?:see|talk to|speak to|ask|call)\s+(?:a|your|the|nhs|111)?\s*"
                       r"(?:gp|doctor|nurse|pharmacist|midwife|dentist|111)\b"
                       r"|\bworth (?:a |an |the )?(?:gp|doctor|nurse|check|visit|test|"
                       r"blood test|check-up|checking|seeing|getting|mentioning)\b"
                       r"|\bget (?:it|them|this) checked\b", re.I)
# A range the answer frames as a limit is a ceiling - "the limit for an adult is 6g", "no more than
# two litres" - so a figure over it is worth trimming. A range that is only a plateau is not: the
# 7,000 to 8,000 steps answer says the benefit levels off there, and "trim it back towards that"
# told a person walking 12,000 steps to walk less.
_A_LIMIT = re.compile(r"\blimits?\b|\bno more than\b|\bnot (?:more|much more) than\b"
                      r"|\bat most\b|\bcap(?:ped)?\b|\bcut (?:back|down)\b"
                      r"|\bkeep (?:it|them) (?:under|below)\b", re.I)
# A time that comes with a temperature test is a doneness, not a figure to reach: "a 2kg bird
# takes roughly 1 hour 40 minutes, or until the juices run clear at 75C" was compared with the two
# hours someone typed next, and the doneness check was dropped from the reply.
_A_TEMPERATURE = re.compile(r"\b\d{2,3}\s*(?:\u00b0\s*)?(?:c|degrees?|gas mark)\b"
                            r"|\buntil (?:the juices|it is cooked|browned|piping hot)\b", re.I)
# "is that enough" is a follow-up about the amount the person just gave, and it was answered with
# a sign-off that fits any message: "i run 5k twice a week" / "is that enough" got "Alright then -
# good luck with it." The answer a turn earlier already named the figure to aim at, so the store
# reads the two numbers together: what they do, and what the answer said to aim for.
def _a_value(word):
    """The number a word stands for, from a digit or a word, or 0 when it is neither."""
    word = (word or "").strip().lower()
    if re.fullmatch(r"\d+(?:,\d{3})*(?:\.\d+)?", word):
        return float(word.replace(",", ""))
    return float(_AMOUNT_WORDS.get(word, 0))


def _amount_family(unit):
    """The family a unit word belongs to, or "" when it is not one we can compare."""
    for family, pattern in _AMOUNTS:
        if re.fullmatch(pattern, unit.strip(), re.I):
            return family
    return ""


# "1 hour 40 minutes" is one figure of a hundred minutes. Both the reading of a line and the
# reading of an answer have to see it that way, or "an hour and forty" answers "past the 1 hour
# that answer named".
_HOURS_AND_MINUTES = re.compile(r"(" + _COUNT_WORD + r")\s*(?:hours?|hrs?)\s+(" + _COUNT_WORD
                                + r")\s*(?:minutes?|mins?)\b", re.I)


# "30 minutes a day" against "150 minutes a week" are two ways of saying the same rate, and 30 a
# day is 210 a week - above the figure, not short of it. The number alone is no comparison, so the
# period said beside each figure is read with it, and two figures said on different periods are
# left to the modules that can say which rate they are on.
_A_PERIOD = re.compile(r"\s*(?:a|an|per|each|every|most)\s+(day|week|night|month)\b", re.I)


def _period_after(text, at):
    """The period said right after the figure ending at `at`, as 'a day' or 'a week'."""
    match = _A_PERIOD.match(text or "", at)
    if not match:
        return None
    return _WEEKLY if match.group(1).lower() == "week" else "a day"


def _a_period_near(text, phrase):
    """The period said after `phrase` in `text`, as 'a day' or 'a week'."""
    at = (text or "").lower().find((phrase or "").lower())
    if at < 0 or not phrase:
        return None
    return _period_after(text, at + len(phrase))


def _the_period_of_the_answer(answer):
    """The period an answer is written on, when it says one: 'a day' or 'a week'."""
    for match in re.finditer(r"(?:a|per|each|every)\s+(day|week|night)\b", answer or "", re.I):
        return _WEEKLY if match.group(1).lower() == "week" else "a day"
    return None


def _the_periods_the_answer_says(answer):
    """Every period an answer is written on: {'a day', 'a week'} for a guideline that says both.

    A month is kept as a month: "give it six weeks before you judge it" and "in a month" are not
    the person's day, and reading one as a day let a weekly answer slide past the period check -
    "20 mins a day" against "Three half-hour sessions a week is enough ... a walk for ten minutes
    to warm up" was answered "20 mins is past the ten minutes that answer named".
    """
    out = set()
    for match in re.finditer(r"(?:a|an|per|each|every)\s+(day|week|night|month|year)\b",
                             answer or "", re.I):
        word = match.group(1).lower()
        out.add({"week": _WEEKLY, "day": "a day", "night": "a day"}.get(word, "a " + word))
    return out


def _periods_disagree(mine, theirs, also=()):
    """True when the two figures are said on periods that cannot be read against each other.

    A weekly figure and a daily one are not the same amount, and a weekly total against a figure
    with no period at all ("50 hours a week" against "seven to nine hours") is a rate nobody
    stated. A figure said per night is a figure said per day for every count in this module.
    """
    if mine is None:
        return False
    # A guideline often gives the same aim in two periods - "150 minutes a week, which is around
    # 20 minutes a day" - and the person's own period is then one of them, not a disagreement.
    if mine in also:
        return False
    if theirs is None:
        return mine == _WEEKLY
    return mine != theirs


# A figure in the answer that is not about the amount they gave: a minute's rest against the 48
# hours between sessions is another quantity, not a target. An answer more than twenty times their
# figure, or one they are three and a half times past, is about something else. The margins are
# wide on purpose - a real shortfall (30 minutes a week against 150) is inside them.
_TOO_FAR_ABOVE = 3.5
_TOO_FAR_BELOW = 20.0


def _too_far_to_compare(value, low, high):
    """True when the answer's figure and theirs are the same unit but not the same quantity."""
    if not (value and low and high):
        return False
    if value > high and value > _TOO_FAR_ABOVE * high:
        return True
    if value < low and low > _TOO_FAR_BELOW * value:
        return True
    return False


def _amounts(text):
    """Every figure with a unit in the line: (value, family, as it was said)."""
    text = _spoken_as_numbers(text)
    found = []
    # "1 hour 40 minutes" is one figure of a hundred minutes, not an hour and then forty minutes:
    # read as its first number, an answer of "an hour and forty" answered "2 hours is past the 1
    # hour that answer named". The words stay as the answer said them, so the reply is worded
    # with the answer's own phrasing.
    spans = []
    for match in _HOURS_AND_MINUTES.finditer(text):
        hours, minutes = _a_value(match.group(1)), _a_value(match.group(2))
        if not (hours or minutes):
            continue
        found.append((hours * 60 + minutes, "minutes", match.group(0).strip(" .,!?")))
        spans.append((match.start(), match.end()))
    pattern = (r"(" + _COUNT_WORD + r")\s*(?:x\s*)?" + r"(" + "|".join(p for _, p in _AMOUNTS)
               + r")")
    for match in re.finditer(pattern, text, re.I):
        value = _a_value(match.group(1))
        if not value:
            continue
        if any(start <= match.start() and match.end() <= end for start, end in spans):
            continue
        found.append((value, _amount_family(match.group(2)), match.group(0).strip(" .,!?")))
    # "5k twice a week" gives both a distance and a frequency: the frequency is what a "three
    # sessions a week" answer is about, so it is tried first.
    found.sort(key=lambda item: 0 if item[1] in ("a week", "a day") else 1)
    return found


def _target(answer, family, mine=None, bare_ok=False, period=None):
    """The figure the last answer named in the same family: (low, high, as it was said).

    A guideline often opens by saying the person's own figure back - "Five hours is on the short
    side: most adults need seven to nine" - and that opening is not the figure to aim at, it is
    the answer measuring them against it. When the first figure in the answer is the number they
    gave, the range the answer names is the target, unit or no unit.

    `period` is the period the person's own figure is said on ("a week" for "two and a half hours
    a week"). An answer often says the same aim twice in two periods - "Aim for about 150 minutes
    a week, which is around 20 minutes a day" - and read as one family that is two figures, which
    is no figure to aim at, so the ones said on the person's own period are the ones to read.
    """
    answer = _spoken_as_numbers(answer)
    units = "|".join(p for _, p in _AMOUNTS)
    ranges, singles = [], []
    # A figure said as hours and minutes is read whole, so the minutes in it are not a second one.
    long_spans = [match.span() for match in _HOURS_AND_MINUTES.finditer(answer)]
    # A range first: "1.5 to 2 litres", "six to eight glasses", "seven to nine hours".
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(?:to|-|\u2013|and)\s*(" + _COUNT_WORD
                             + r")\s*(?:-\s*)?(" + units + r")", answer, re.I):
        if _amount_family(match.group(3)) != family:
            continue
        low, high = _a_value(match.group(1)), _a_value(match.group(2))
        if low and high and not _a_rate(answer, match.end()):
            ranges.append((match.start(), (low, high, match.group(0).strip(" .,!?"))))
    spans = [(match.start(), match.end()) for match, _ in
             ((m, None) for m in re.finditer(
                 r"(" + _COUNT_WORD + r")\s*(?:to|-|\u2013|and)\s*(" + _COUNT_WORD + r")\s*"
                 r"(?:-\s*)?(" + units + r")", answer, re.I))]
    # A range written in two units is one range: "30 minutes to an hour a day" is 30 to 60, and
    # reading only its minute end made half an hour answer "short of the 1 hour minutes".
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(" + units + r")\s*(?:to|-|\u2013|and)\s*"
                             r"(" + _COUNT_WORD + r")\s*(" + units + r")", answer, re.I):
        low_family, high_family = (_amount_family(match.group(2)),
                                   _amount_family(match.group(4)))
        if low_family == high_family:
            continue
        low, high = _a_value(match.group(1)), _a_value(match.group(3))
        if not (low and high):
            continue
        if family not in (low_family, high_family):
            continue
        low_in = low * _CONVERT.get((family, low_family), 1.0 if low_family == family else 0)
        high_in = high * _CONVERT.get((family, high_family),
                                      1.0 if high_family == family else 0)
        if not (low_in and high_in):
            continue
        said = "%s to %s %s" % (_the_number(int(low_in) if float(low_in).is_integer() else low_in),
                                 _the_number(int(high_in) if float(high_in).is_integer()
                                             else high_in),
                                 _UNIT_SAID.get(family, (family, family))[1])
        ranges.append((match.start(), (low_in, high_in, said)))
        spans.append((match.start(), match.end()))
    # Then a plain figure: "30 minutes most days", "three sessions a week".
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(?:-\s*)?(" + units + r")", answer,
                             re.I):
        if _amount_family(match.group(2)) != family:
            continue
        # "two ten-minute walks" and "three 50-minute sessions" are shapes of thing, not figures
        # to reach, and the "2 litres" in "1.5 to 2 litres" is half of the range read above.
        if "-" in match.group(0):
            continue
        if any(start <= match.start() and match.end() <= end for start, end in spans + long_spans):
            continue
        value = _a_value(match.group(1))
        if value and not _a_rate(answer, match.end()):
            singles.append((match.start(), (value, value, match.group(0).strip(" .,!?"))))
    # "1 hour 30 minutes" is one figure of ninety minutes, read whole so the minutes inside it are
    # not counted a second time as a figure of their own.
    for match in _HOURS_AND_MINUTES.finditer(answer):
        hours, minutes = _a_value(match.group(1)), _a_value(match.group(2))
        if hours or minutes:
            total = hours * 60 + minutes
            singles.append((match.start(), (total, total, match.group(0).strip(" .,!?"))))
    ranges.sort(key=lambda item: item[0])
    singles.sort(key=lambda item: item[0])

    def is_their_number(figure):
        return mine is not None and figure[0] == figure[1] == mine

    # A range in the answer is the figure it aims at, so a single figure that is the person's own
    # number said back ("Five hours is on the short side: ... seven to nine hours") is the answer
    # measuring them, not a second target.
    useful = [(at, figure) for at, figure in singles if not (ranges and is_their_number(figure))]
    figures = [figure for _, figure in ranges] + [figure for _, figure in useful]
    # An answer that names more than one figure of this kind ("add a daily twenty minutes", "two
    # ten-minute walks") is not naming one figure to aim at, so which of them is the target would
    # be a guess - and a guess is answered as though the person had reached a number the answer
    # never set. Nothing is read from it.
    if period and len({figure[:2] for figure in figures}) > 1:
        # Only two figures said on two different periods are a thing the period settles: two aims
        # on the same one ("Aim for 30 minutes a day, and 60 if you can manage it") are still two
        # aims, and picking one of them would be the guess this rule is here to stop. Every list a
        # figure is read from is narrowed, not only the count: "Aim for about 150 minutes a week,
        # which is around 20 minutes a day" is one aim for somebody doing half an hour a day.
        ranges_on = _the_periods_of(answer, ranges)
        useful_on = _the_periods_of(answer, useful)
        said_on = ranges_on + useful_on
        if (any(each == period for each in said_on)
                and any(each and each != period for each in said_on)):
            ranges = [pair for pair, each in zip(ranges, ranges_on) if each == period]
            useful = [pair for pair, each in zip(useful, useful_on) if each == period]
            figures = [figure for _, figure in ranges] + [figure for _, figure in useful]
    if len({figure[:2] for figure in figures}) > 1:
        # Unless the answer named a range at all: a guideline is written as a range ("seven to
        # nine hours"), and a lone figure beside it is usually the answer giving an example
        # ("six hours means you are short"), not a second figure to aim at. One range is one
        # aim even when the answer also says a single number in passing.
        if len({figure[:2] for figure in ranges}) == 1:
            best = ranges[0][1]
            if not is_their_number(best):
                return _with_its_period(answer, best, period)
        return None
    best = ranges[0][1] if ranges else (useful[0][1] if useful else None)
    if best is not None and not is_their_number(best):
        return _with_its_period(answer, best, period)
    # An answer can name its range without repeating the unit ("most adults need seven to nine"),
    # and an answer that opens with the person's own number back - "Five hours is on the short
    # side" - is measuring them against that range rather than aiming at the number.
    # The range without its unit is read only for the person's own kind of amount: a unit-less
    # range in another family, reached through the conversion below, is a guess with nothing
    # behind it ("7,000 to 8,000 steps" for someone asking about 30 minutes).
    bare = _near_bare_range(answer, mine, family) if bare_ok else None
    if bare is not None:
        return bare
    return _with_its_period(answer, best, period) if best is not None else None


# The words an answer uses when it is naming a figure to aim at rather than saying theirs back.
# "Aim for about 150 minutes a week" is the figure; "Got it - you have 150 minutes a week" is the
# store handing their own number back, and answering that with "you are there already" is the echo
# this module exists to stop. Only the words that make a figure an aim, never a hedge: "about 150
# minutes" is as likely a rough figure as an aim, and reading one as the other tells somebody they
# have already hit a number the answer never set.
_AIM_CUE = re.compile(r"\b(?:aim (?:for|at)|aims? (?:for|at)|target(?:s|ing)?\b|guideline|"
                      r"should (?:be|get|do|have)|try (?:for|to)|recommended|the idea is)\b", re.I)


def _the_aim_that_is_their_number(answer, family, mine):
    """The figure the answer aims at when it is the number they gave: (low, high, said) or None.

    A guideline is often written as the figure they already do - "Aim for about 150 minutes a
    week" to somebody who has just said "i do two and a half hours a week" - and `_target` passes
    over it, because a short answer that repeats their number is a receipt. Read as an aim, the
    same figure is the answer: their 150 minutes a week is the 150 minutes a week it named.
    """
    if not mine:
        return None
    units = "|".join(p for _, p in _AMOUNTS)
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(?:-\s*)?(" + units + r")", answer or "",
                             re.I):
        if _amount_family(match.group(2)) != family:
            continue
        if _a_value(match.group(1)) != mine:
            continue
        before = (answer or "")[max(0, match.start() - 40):match.start()]
        if not _AIM_CUE.search(before):
            continue
        said = match.group(0).strip(" .,!?")
        # The period is part of the figure: "the 150 minutes a week that answer named" is what a
        # weekly guideline says, and "150 minutes" alone leaves out the thing it is per.
        period = _period_after(answer or "", match.end())
        if period:
            said += " " + ("a week" if period == _WEEKLY else "a day")
        return (mine, mine, said)
    return None


def _with_its_period(answer, figure, period):
    """The figure with the period it is said on, when the answer says it on the person's own.

    "150 minutes" is read off "Aim for about 150 minutes a week", and said back without the "a
    week" it leaves out what the figure is per: "2.5 hours is at the 150 minutes that answer
    named" against "at the 150 minutes a week that answer named".
    """
    if not (period and figure):
        return figure
    at = (answer or "").find(figure[2])
    if at < 0:
        return figure
    match = _A_PERIOD.match(answer, at + len(figure[2]))
    if not match:
        return figure
    said = _WEEKLY if match.group(1).lower() == "week" else "a day"
    if said != period:
        return figure
    return (figure[0], figure[1], figure[2] + " " + match.group(0).strip(" .,!?"))


def _the_periods_of(answer, figures):
    """The period each figure in `figures` (start, (low, high, said)) is said on, or None.

    The period is written right after the figure - "150 minutes **a week**" - and a figure with
    none is a figure on no stated period, which is not the same as one said on another.
    """
    out = []
    for at, figure in figures:
        match = _A_PERIOD.search(answer or "", at)
        if not match or match.start() > at + len(figure[2]) + 12:
            out.append(None)
            continue
        out.append(_WEEKLY if match.group(1).lower() == "week" else "a day")
    return out


def _aims_named(answer, mine, family):
    """The distinct figures of this kind the answer names, a range counting as one figure.

    "Lower eggs into already boiling water: 6 minutes for a runny yolk, 7 for jammy, 9 to 10 for
    hard boiled" names three timings, and reading one of them as the figure to aim at answered
    "is 6 minutes enough" with "short of the 9 to 10 minutes". A guideline names one figure or one
    range - "seven to nine hours", "2,000 to 2,500 calories" - and not a list of choices.
    """
    units = "|".join(p for _f, p in _AMOUNTS)
    found, spans = set(), []
    # A range, with its unit or without: "1.5 to 2 litres", "seven to nine".
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(?:to|and|or|\u2013|-)\s*(" + _COUNT_WORD
                             + r")\s*(?:-\s*)?(" + units + r")?", answer, re.I):
        low, high = _a_value(match.group(1)), _a_value(match.group(2))
        if not (low and high and low < high):
            continue
        spans.append(match.span())
        said = match.group(3)
        if said and _amount_family(said) != family:
            continue
        found.add((low, high))
    # Every figure said with a unit of any kind, so a figure of another kind is not counted here.
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(?:-\s*)?(" + units + r")", answer,
                             re.I):
        if any(start <= match.start() and match.end() <= end for start, end in spans):
            continue
        spans.append(match.span())
        if _amount_family(match.group(2)) != family:
            continue
        value = _a_value(match.group(1))
        if value:
            found.add((value, value))
    # A figure on its own, with no unit beside it at all: "7 for jammy", "9 to 10 for hard boiled".
    for match in re.finditer(r"(" + _COUNT_WORD + r")", answer, re.I):
        if any(start <= match.start() and match.end() <= end for start, end in spans):
            continue
        value = _a_value(match.group(1))
        if not value or not (mine and mine / 3 <= value <= mine * 3):
            continue
        # Unless it counts things: "five half-hours, or three twenty-minute sessions and some
        # walking, plus two short strength sessions" is one guideline with its examples, and
        # counted as figures it made three "aims" of an answer that names one - which then read as
        # a list and was answered with nothing at all.
        if _counts_things(answer, match.end()):
            continue
        found.add((value, value))
    return found


# A period is what an amount is per, not the things a count counts: "twice a week".
_PERIOD_WORDS = {"day", "days", "week", "weeks", "night", "nights", "month", "months", "year",
                 "years", "time", "times"}

# The words a count is a count of ("three sessions", "two walks"), which are not units of amount.
# A number in front of one of these is how many of something, not how much of it, and the thing
# counted can have a shape word in front of it: "three twenty-minute sessions".
_A_WORD_AFTER = re.compile(r"(?:\s+[a-z]+(?:-[a-z]+)?){1,4}")


def _counts_things(answer, at):
    """True when the number ending at `at` counts things rather than measuring an amount.

    A count of things is an example in a list ("three twenty-minute sessions") and not an aim,
    unless it is said as a rate: "Three half-hour sessions a week is enough to feel different in a
    month" is the answer's aim, and read past it the store answered "20 mins is past the ten
    minutes that answer named" from the warm-up in the sentence after it.
    """
    match = _A_WORD_AFTER.match(answer or "", at)
    if not match:
        return False
    words = match.group(0).split()
    for at_word, word in enumerate(words):
        # A unit of amount ("20 minutes", "1.5 litres") and a period ("twice a week") are the
        # amount itself, whatever the word looks like, so the count stops there.
        if _amount_family(word) is not None or word in _PERIOD_WORDS:
            return False
        if len(word) > 3 and word.endswith("s"):
            # Said per something, this count is a rate and so an aim of the answer's own kind.
            return not any(other in _PERIOD_WORDS or _amount_family(other) == "a week"
                           for other in words[at_word + 1:] + [""])
    return False


def _figures_in(answer):
    """Every number in the answer, with or without a unit: "20 minutes", "seven to nine".

    Used to tell an answer that is only saying the person's own figure back from one that names
    another figure for them to reach.
    """
    found = [value for value, _family, _said in _amounts(answer)]
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(?:to|and|or|\u2013|-)\s*("
                             + _COUNT_WORD + r")\b", answer, re.I):
        low, high = _a_value(match.group(1)), _a_value(match.group(2))
        if low and high and low < high:
            found += [low, high]
    return found


def _a_rate(answer, end):
    """The figure is a rate rather than an amount: "0.75g per kilo of body weight", "2% of it".

    "how much protein should i eat" answered "0.75g per kilo ... roughly 50g for a 65kg adult",
    and 60g of protein was called "past the 0.75g that answer named". A rate is not a figure to be
    over or under; the worked example beside it is, and this reading does not pick it out.
    """
    return bool(re.match(r"\s*(?:%|per cent\b|percent\b|per (?:kilo|kg|kilogram|kilo of|pound|"
                         r"lb|100|head|person|day per)\b|g\s?/\s?kg\b|mg\s?/\s?kg\b)",
                         answer[end:end + 24], re.I))


def _another_kind_follows(answer, end, family):
    """A unit of another kind sits right after the figure, so the figure is not this kind's.

    "three or four runs a week" is a count of runs; read as kilometres it turned "i run 10k every
    day" into "more than the three or four km that answer named".
    """
    following = re.match(r"\s*(" + "|".join(p for _f, p in _AMOUNTS) + r")\b", answer[end:], re.I)
    return bool(following) and _amount_family(following.group(1)) != family


def _near_bare_range(answer, mine, family=None):
    """A range of numbers said without a unit, near enough their own figure to be about it.

    "most adults need seven to nine" is the range a line about five hours is measured against.
    "7,000 to 8,000 steps" in an answer about walking is a range in another unit entirely, and a
    range that far from their own number is not the figure they are being compared with.
    """
    for match in re.finditer(r"(" + _COUNT_WORD + r")\s*(?:to|and|or|\u2013|-)\s*("
                             + _COUNT_WORD + r")\b", answer, re.I):
        low, high = _a_value(match.group(1)), _a_value(match.group(2))
        if not (low and high and low < high):
            continue
        if mine is not None and not (low <= mine * 3 and mine <= high * 3):
            continue
        if family and _another_kind_follows(answer, match.end(), family):
            continue
        if _a_rate(answer, match.end()):
            continue
        return low, high, match.group(0).strip(" .,!?")
    return None


def _with_its_unit(aim, family, high, answer=""):
    """The aim with its unit said, when the answer named the range without one.

    "most adults need seven to nine" is a range about hours, and answering "you are short of the
    seven to nine that answer named" leaves out the thing that is counted. A range that is
    followed by a unit of another kind is that other kind's range: "three or four runs a week" is
    a count of runs, and saying it in kilometres turned a 10k a day into "more than the three or
    four km that answer named".
    """
    pattern = dict(_AMOUNTS).get(family)
    if not pattern or re.search(pattern, aim, re.I):
        return aim
    # A figure that already says a length of time is a length of time, whichever of the two time
    # units it was read in: a target converted from hours into the person's minutes ("1 hour"
    # against half an hour) was written out as "the 1 hour minutes that answer named".
    if family in ("minutes", "hours") and re.search(r"\b(?:minutes?|mins?|hours?|hrs?)\b",
                                                    aim, re.I):
        return aim
    at = answer.find(aim)
    if at >= 0 and _another_kind_follows(answer, at + len(aim), family):
        return aim
    units = _UNIT_SAID.get(family)
    if not units:
        return aim
    return aim + " " + (units[0] if high == 1 else units[1])


def _the_number(value):
    whole = int(value) if float(value).is_integer() else value
    return str(whole)


def enough_reply(text, memory):
    """Where the amount they gave stands against the figure the last answer named, or None."""
    if not isinstance(text, str):
        return None
    more = bool(HOW_MORE.search(text))
    if not more and not ENOUGH_ASK.search(text):
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return None
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    if not (last.get("bot") or ""):
        return None
    too_much = bool(re.search(r"\btoo (?:much|often|many)\b", text, re.I))
    # Money is read on its own, before the amounts: a price band is what a price answer names, and
    # the band their money falls in is the reply (bot/memory/purse.py).
    from ..memory import purse  # noqa: PLC0415 - bot.memory imports this module

    purse_reply = purse.against_the_bands(text, turns)
    if purse_reply:
        return purse_reply
    # The figure they are asking about. The ask itself often names it - "is 5 hours enough",
    # "is 1200 enough" - and when it does not ("is that enough") it is the last line they typed
    # that gave one. Reading the ask's own figure is what makes the shape work when the answer
    # to "how much sleep do i need" was two lines ago rather than the last thing said.
    said = ""
    given = []
    for line_text in [text] + [str(t.get("user") or "") for t in reversed(turns)]:
        found = [item for item in _amounts(line_text) if item[1]]
        if found:
            given = found
            # The period said beside the figure ("twenty minutes **a day**") is looked for by the
            # phrase the reader produced, so a spelled-out figure left the period unread.
            said = _spoken_as_numbers(line_text)
            break
    if not given:
        # A figure said without a unit - "i eat 1200", "i walk 10000" - is still the amount they
        # are asking about when the answer names a range in the same breath ("roughly 2,000 to
        # 2,500 calories a day"). Only a large bare number is read: "i have 2" or "we are 4" is
        # as likely a count of people as an amount, and a wrong reading is worse than no reading.
        return _enough_bare(turns, text, more, too_much)
    # The figures the person themself gave. An answer whose only figures are those is answering
    # with the number it was told ("With 20 minutes, do a circuit ...", "Got it - you have 9
    # grams a day"), so there is no figure to aim at in it and reading one back at them is the
    # echo this module exists to stop.
    mine_values = {value for value, _family, _said in given}
    reply = _enough_against(_candidate_answers(turns, mine_values), given, mine_values, said,
                            more, too_much)
    return reply


def _enough_bare(turns, text, more, too_much):
    """The reading for a figure the person gave without a unit, or None.

    Their line says the number and the answer says the kind of amount: "i eat 1200" against
    "roughly 2,000 to 2,500 calories a day". Nothing is read from an answer whose range is not
    near enough their number to be about it, and a small bare number is left alone.
    """
    mine = 0
    for line_text in [text] + [str(t.get("user") or "") for t in reversed(turns)]:
        bare = [value for value in _bare_figures(line_text) if value >= 100]
        if bare:
            mine = bare[0]
            break
    if not mine:
        return None
    for answer in _candidate_answers(turns, {mine}):
        found = _range_near(answer, mine)
        if not found:
            continue
        low, high = found[0], found[1]
        aim = found[2][0].lower() + found[2][1:]
        spoken = _the_number(mine)
        if spoken == "1":
            spoken = "one"
        if more:
            gap = low - mine
            if gap <= 0:
                return "None - %s is already at the %s that answer named." % (spoken, aim)
            return "%s more would put you at the %s that answer named." % (
                _the_number(round(gap, 1)), aim)
        if mine < low:
            return "%s is short of the %s that answer named." % (spoken, aim)
        if mine > high:
            return "%s is past the %s that answer named, so that side is worth watching." % (
                spoken, aim)
        return "No - %s is inside the %s that answer named, so you are fine." % (spoken, aim)


def _range_near(answer, mine):
    """The range in the answer near enough their number to be about it, its unit included.

    "7,000 to 8,000 steps" is not the figure a line about 1,200 calories is measured against, so
    a range three times away from their number either side is passed over. A range said with its
    unit ("2,000 to 2,500 calories") is read before one said without ("seven to nine").
    """
    units = "|".join(pattern for _family, pattern in _AMOUNTS)
    for pattern in (r"(" + _COUNT_WORD + r")\s*(?:to|and|or|\u2013|-)\s*(" + _COUNT_WORD
                    + r")\s*(?:" + units + r")\b",
                    r"(" + _COUNT_WORD + r")\s*(?:to|and|or|\u2013|-)\s*(" + _COUNT_WORD
                    + r")\b"):
        for match in re.finditer(pattern, answer, re.I):
            low, high = _a_value(match.group(1)), _a_value(match.group(2))
            if not (low and high and low < high):
                continue
            if not (low <= mine * 3 and mine <= high * 3):
                continue
            return low, high, match.group(0).strip(" .,!?")
    return None


def _bare_figures(text):
    """Every number in the line that is not part of an amount with a unit."""
    with_unit = [(match.start(), match.end()) for match in re.finditer(
        r"(" + _COUNT_WORD + r")\s*(?:-\s*)?(?:"
        + "|".join(pattern for _family, pattern in _AMOUNTS) + r")", text or "", re.I)]
    out = []
    for match in re.finditer(r"(" + _COUNT_WORD + r")", text or "", re.I):
        if any(start <= match.start() and match.end() <= end for start, end in with_unit):
            continue
        value = _a_value(match.group(1))
        if value:
            out.append(value)
    return out


def _candidate_answers(turns, mine_values):
    """The bot answers to read a figure out of, newest first, up to three turns back.

    The last answer is often the store saying their figure back ("Got it - you have 9 grams a
    day") and the answer that named the range is the one before it, so an answer whose only
    figures are the person's own is a receipt and is stepped over. Reading no further than three
    turns keeps the figure and the range about the same thing.
    """
    out = []
    for turn in reversed(turns[-3:]):
        answer = str(turn.get("bot") or "") if isinstance(turn, dict) else ""
        if not answer:
            continue
        if mine_values and not [figure for figure in _figures_in(answer)
                                if figure not in mine_values]:
            continue
        out.append(answer)
    return out


def _enough_against(answers, given, mine_values, said, more, too_much, quoted_ok=False):
    """The reply for the best of `answers`, or None when none of them names a figure to aim at."""
    quoted = None
    for answer in answers:
        for value, family, spoken in given:
            if not family:
                continue
            if _periods_disagree(_a_period_near(said, spoken),
                                 _the_period_of_the_answer(answer),
                                 _the_periods_the_answer_says(answer)):
                continue
            if family in ("minutes", "hours") and _A_TEMPERATURE.search(answer):
                continue
            if _A_DOCTOR.search(answer):
                continue
            period = _a_period_near(said, spoken)
            # The family the figure is read in, which is the answer's own when it counts the same
            # thing in another unit: the "names a list" rule below is asked of that family.
            read_family, read_value = family, value
            target = _target(answer, family, value, bare_ok=True, period=period)
            if not target:
                # The answer may name their own number as the figure to aim at: "Aim for about
                # 150 minutes a week" for somebody doing exactly that.
                target = _the_aim_that_is_their_number(answer, family, value)
            if not target:
                # The answer may count the same thing in another unit: "20 minutes a day" against
                # "two hours of study a day".
                for (mine, theirs), factor in _CONVERT.items():
                    if mine != family:
                        continue
                    # The list rule is about the kind of amount being read, so it is asked again
                    # in the answer's own unit: an answer counting things in hours ("five
                    # half-hours, three twenty-minute sessions") names one figure in minutes.
                    other = _target(answer, theirs, period=period)
                    if not other:
                        # Or name their own figure in the other unit as the aim: "150 minutes a
                        # week" is the guideline for somebody who says "i do 2.5 hours a week".
                        other = _the_aim_that_is_their_number(
                            answer, theirs, round(value / factor, 4))
                    if other:
                        # The factor turns their unit into the person's: two hours is 120 minutes.
                        target = (other[0] * factor, other[1] * factor, other[2])
                        read_family, read_value = theirs, round(value / factor, 4)
                        break
            if not target:
                continue
            # The answer may be the bot reading their own figure back - "2.5 hours is at the 150
            # minutes a week that answer named" - and the figure at the front of that line is
            # theirs, not a figure to aim at. Their own number counts as an aim only when the
            # answer says it as one ("Aim for about 150 minutes a week"), which is read above, so
            # a reply that quotes them is stepped over for the answer before it.
            if (not quoted_ok and spoken and spoken.lower() in (target[2] or "").lower()
                    and abs(target[0] - value) < 1e-9 and abs(target[1] - value) < 1e-9
                    and not _AIM_CUE.search(answer)):
                # Their own number read as the aim, from an answer that quotes it back is the last
                # thing tried: an answer that names a real aim is the better reading, and when
                # there is none this is still better than no reply at all.
                if quoted is None:
                    quoted = (answer, [(value, family, spoken)])
                continue
            # An answer that names more than two figures of the kind being read ("add a daily
            # twenty minutes", "two ten-minute walks") is not naming one figure to aim at, so
            # which of them is the target would be a guess. Asked of the kind the figure was read
            # in, not of the person's own kind: "five half-hours, or three twenty-minute sessions"
            # is three counts of things in hours and one figure in minutes.
            if len(_aims_named(answer, read_value, read_family)) > 2:
                continue
            # A short answer often just says their own figure back ("You run 5k twice a week."), and
            # reading that as the figure to aim at would answer the person with what they had just
            # said. A long answer that reaches the same number in its own words is a real target, so
            # only a short line that repeats them is passed over.
            if len(answer.split()) <= 12 and (target[2].lower() in said.lower()
                                             or spoken.lower() in answer.lower()):
                continue
            if mine_values and not [figure for figure in _figures_in(answer)
                                    if figure not in mine_values]:
                continue
            low, high = target[0], target[1]
            if _too_far_to_compare(value, low, high):
                continue
            # The figure is quoted mid-sentence, so its first letter sits inside the line.
            aim = target[2][0].lower() + target[2][1:]
            aim = _with_its_unit(aim, family, high, answer)
            if more:
                # "how much more do i need" is the gap, said as an amount to add rather than as a
                # shortfall: "another 20 minutes would put you at the 30 minutes that answer named."
                gap = low - value
                if gap <= 0:
                    return "None - %s is already %s the %s that answer named." % (
                        spoken, "at" if value <= high else "past", aim)
                units = _UNIT_SAID.get(family)
                if not units:
                    continue
                said_unit = units[0] if gap == 1 else units[1]
                amount = _the_number(round(gap, 1))
                if amount == "1":
                    amount = "one"
                elif amount in ("2", "3", "4", "5", "6", "7", "8", "9", "10"):
                    amount = NUMBER_WORDS.get(int(amount), amount)
                if family in ("a week", "a day"):
                    return "%s more %s would put you at the %s that answer named." % (
                        amount[0].upper() + amount[1:], said_unit, aim)
                return "Another %s %s would put you at the %s that answer named." % (
                    amount, said_unit, aim)
            if too_much:
                if value > high:
                    if _A_LIMIT.search(answer):
                        return ("That is more than the %s that answer named, so trim it back "
                                "towards that." % aim)
                    return "That is more than the %s that answer named." % aim
                if low <= value <= high:
                    return "No - %s is inside the %s that answer named, so you are fine." % (
                        spoken[0].upper() + spoken[1:], aim)
                # Under the range, "is that too much" is not this module's question at all: the
                # answer is "no, it is under", and saying a shortfall is "inside ... fine" is a
                # reassurance the answer never gave. 800 calories against "2,000 to 2,500" was
                # answered "you are fine".
                continue
            if value > high:
                # A figure past the top of the range is over it, not at it: "3 litres is past the
                # 1.5 to 2 litres that answer named".
                return "%s is past the %s that answer named, so that side is worth watching." % (
                    spoken[0].upper() + spoken[1:], aim)
            if value >= high:
                # At the top of a range is worth saying: "2 litres is at the top of the 1.5 to 2
                # litres the answer named" reads like the answer they asked for.
                at = "at the top of" if high > low else "at"
                return "%s is %s the %s that answer named, so you are there already." % (
                    spoken[0].upper() + spoken[1:], at, aim)
            if low <= value < high:
                return "%s is inside the %s that answer named, so you are fine." % (
                    spoken[0].upper() + spoken[1:], aim)
            # Under the figure: a count of sessions is closed by doing one more, a length by adding
            # to it, so the line says which.
            if family in ("a week", "a day"):
                return "%s is under the %s that answer named - one more would put you there." % (
                    spoken[0].upper() + spoken[1:], aim)
            return "%s is short of the %s that answer named." % (
                spoken[0].upper() + spoken[1:], aim)
    if quoted:
        return _enough_against([quoted[0]], quoted[1], mine_values, said, more, too_much,
                               quoted_ok=True)
    return None
