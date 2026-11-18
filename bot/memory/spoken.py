"""A figure said out loud, written as the same figure in digits.

People say the figure in words as often as in digits, and the amount reader in `memory_store`
knew only a digit or a word up to twelve: "half an hour" was not a figure at all, so "is that
enough" had nothing to measure against the answer. This module has no imports but `re`, and
`memory_store` reads every line through it before it looks for an amount.
"""
import re

# People say the figure in words as often as in digits, and the reader below knew only a digit or
# a word up to twelve: "half an hour" was not a figure at all, so "is that enough" had nothing to
# measure against the answer. A spoken figure is written in digits before anything reads the line.
_SPOKEN_UNIT = (r"(?:minutes?|mins?|hours?|hrs?|days?|weeks?|nights?|miles?|km|kilometres?"
                r"|kilometers?|litres?|liters?|glasses?|steps?|grams?|grammes?|calories|cals?"
                r"|micrograms?|milligrams?)")
# A fraction of a unit, said the way it is spoken: "half an hour", "a couple of miles".
_A_SPOKEN_FRACTION = re.compile(
    r"\b(half|a half|a quarter|quarter|three quarters?|a couple of|a couple|a dozen|a few)"
    r"\s+(?:of\s+)?(?:a\b|an\b)?\s*(" + _SPOKEN_UNIT + r")\b", re.I)
_SPOKEN_FRACTION_VALUE = {"half": 0.5, "a half": 0.5, "a quarter": 0.25, "quarter": 0.25,
                          "three quarters": 0.75, "three quarter": 0.75, "a couple of": 2.0,
                          "a couple": 2.0, "a dozen": 12.0}
# "an hour and a half" is one length, not an hour. The unit comes before the count as often as
# after it - "a litre and a half" - and reading that as the unit alone made a litre and a half a
# litre, which told a person inside a range that they were short of it.
_A_SPOKEN_HALF_HOUR = re.compile(
    r"\b(?:(an?|one|two|three|four|five|six|seven|eight|nine)\s+)?(" + _SPOKEN_UNIT + r")"
    r"\s+and\s+(?:a\s+)?(half|quarter)\b", re.I)
_SPOKEN_NUMBER = {"thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
                  "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
                  "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
                  "eighty": 80, "ninety": 90, "a hundred": 100, "hundred": 100}
# A bare "a" is a *rate* here: writing "twice a week" in digits takes the rate out of the line.
_A_RATE_UNIT = re.compile(r"^(?:days?|weeks?|nights?)$", re.I)
# "two and a half litres" is one figure, not two: read as the half alone it is half a litre.
_A_COUNT_AND_A_HALF = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|a|an|\d+)\s+and\s+a\s+(half|quarter)\s+"
    r"(" + _SPOKEN_UNIT + r")\b", re.I)
_SPOKEN_TENS = r"(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
# A figure in words in front of the unit it counts. Only a figure in front of a unit is
# rewritten, so "twenty years ago" and a count of people are left as they were said.
_A_WORDED_FIGURE = re.compile(
    r"\b(" + _SPOKEN_TENS + r"(?:[-\s](?:one|two|three|four|five|six|seven|eight|nine))?"
    r"|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|a hundred|an?)\s+"
    r"(" + _SPOKEN_UNIT + r")\b", re.I)
# A count in words that runs straight into the tens: "twenty five" is 25, not 20 and then 5.
_A_TENS_AND_UNITS = re.compile(
    r"\b(" + _SPOKEN_TENS + r")[-\s](one|two|three|four|five|six|seven|eight|nine)\b", re.I)
_ONE_TO_NINE = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                "seven": 7, "eight": 8, "nine": 9}


# Past three hours a length is said in hours, not minutes, or a figure in minutes is measured
# against a range in hours ("330 minutes is short of the seven to nine hours"). Three hours is the
# longest length people still give in minutes.
_MINUTES_CEILING = 180


_UNIT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
               "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "a": 1.0,
               "an": 1.0, "once": 1, "twice": 2}


def _the_number(value):
    """A figure as digits, whole numbers without a trailing '.0'."""
    whole = int(value) if float(value).is_integer() else value
    return str(whole)


def _is_hours(unit):
    return unit.strip().lower().rstrip("s") in ("hour", "hr")


def _in_digits(amount, unit):
    """One spoken figure as the same figure in digits: '30 minutes'."""
    if _is_hours(unit) and not float(amount).is_integer():
        minutes = amount * 60
        if minutes <= _MINUTES_CEILING:
            word = int(minutes) if float(minutes).is_integer() else minutes
            return "%s minutes" % _the_number(word)
        return "%s hours" % _the_number(round(amount, 2))
    word = int(amount) if float(amount).is_integer() else amount
    plural = "s" if (float(amount) != 1.0 and not unit.endswith("s")) else ""
    return "%s %s%s" % (_the_number(word), unit, plural)


def _spoken_as_numbers(text):
    """The line with every figure said out loud written in digits, or the line unchanged."""
    if not isinstance(text, str) or not text:
        return text or ""

    def half_hours(match):
        word = (match.group(1) or "").strip().lower()
        count = float(_UNIT_WORDS.get(word, 0)) or 1.0
        part = 0.5 if match.group(3).lower() == "half" else 0.25
        return _in_digits(count + part, match.group(2).lower())

    def fractions(match):
        word = match.group(1).lower()
        amount = _SPOKEN_FRACTION_VALUE.get(word)
        if amount is None:
            return match.group(0)
        return _in_digits(amount, match.group(2).lower())

    def tens_and_units(match):
        tens = _SPOKEN_NUMBER.get(match.group(1).lower(), 0)
        return str(tens + _ONE_TO_NINE.get(match.group(2).lower(), 0))

    def count_and_a_half(match):
        word = match.group(1).lower()
        count = float(_UNIT_WORDS.get(word, 0))
        if not count:
            return match.group(0)
        part = 0.5 if match.group(2).lower() == "half" else 0.25
        return _in_digits(count + part, match.group(3).lower())

    def worded(match):
        word = match.group(1).lower()
        if word in ("a", "an"):
            if _A_RATE_UNIT.match(match.group(2)):
                return match.group(0)
            amount = 1.0
        else:
            amount = float(_SPOKEN_NUMBER.get(word, 0) or 0)
        if not amount:
            return match.group(0)
        return _in_digits(amount, match.group(2).lower())

    text = _A_COUNT_AND_A_HALF.sub(count_and_a_half, text)
    text = _A_SPOKEN_HALF_HOUR.sub(half_hours, text)
    text = _A_SPOKEN_FRACTION.sub(fractions, text)
    text = _A_TENS_AND_UNITS.sub(tens_and_units, text)
    text = _A_WORDED_FIGURE.sub(worded, text)
    return text


spoken_as_numbers = _spoken_as_numbers
