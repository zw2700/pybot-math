"""Maths and numbers: fixed facts as entries, and computed answers for real questions.

Most maths questions carry their own numbers ("what's 15% of 80", "120 miles at 60 miles an
hour", "how many days in February"), so a canned entry cannot answer them. This domain has
two halves:

- ENTRIES for facts that never change (weeks in a year, a prime number, pi).
- solve(text, understood, memory) for questions that need arithmetic. It only answers when
  the line clearly contains a calculation, and returns None otherwise, so ordinary lines with
  a number in them are left to the other domains.

bot/modules/answers.py calls solve() before looking for a static entry.
"""
import ast
import operator
import re
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

from ..memory.saving import a_rate_put_right, the_money_already_held, the_pot_said_alone
from ..memory.topics import in_a_safety_thread
from . import units
from .lookup import entry

ANSWERS = ("maths-and-numbers",)

MONTHS = {
    "january": 31, "february": 28, "march": 31, "april": 30, "may": 31, "june": 30,
    "july": 31, "august": 31, "september": 30, "october": 31, "november": 30, "december": 31,
}

_NUMBER = r"-?\d+(?:[.,]\d+)?"


def _number(value):
    """A number the way a person writes it: 12, 2.5, 1,081."""
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}"
    # the extra place only when it makes the number exact: 3 divided by 8 is 0.375, not 0.38,
    # while a third stays 0.33 because no short decimal will ever be right.
    shown = f"{value:.2f}"
    for places in (2, 3, 4):
        if abs(float(f"{value:.{places}f}") - value) < 1e-9:
            shown = f"{value:.{places}f}"
            break
    return shown.rstrip("0").rstrip(".")


def _parse(text):
    """The numbers in a line, in order."""
    found = []
    for raw in re.findall(r"\d+(?:\.\d+)?", text.replace(",", "")):
        try:
            found.append(float(raw))
        except ValueError:
            continue
    return found


# --- arithmetic -----------------------------------------------------------

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 64:
            raise ValueError("exponent too large")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    raise ValueError("not arithmetic")


def _expression(clean):
    """The arithmetic expression in a line, or None. Only digits and operators survive."""
    text = clean
    text = re.sub(r"\b(?:what's|whats|what is|calculate|work out|how much is|how much does|"
                  r"please|tell me|the answer to)\b", " ", text)
    # "how do i divide 3 by 8" is the same sum as "3 divided by 8": the asking words carry no
    # number and no operator, so they go before the operator words are read.
    text = re.sub(r"\b(?:how do i|how do you|how can i|how would i|how to|can you|could you|"
                  r"whats the answer to|what is the answer to)\b", " ", text)
    text = text.replace(",", "")
    text = re.sub(r"\bmultiplied by\b|\btimes\b|\bx\b", "*", text)
    # "divide 3 by 8" is a sum with its instruction in front: the numbers say which way round.
    text = re.sub(r"\bdivide\b\s+(\d[\d.]*)\s+by\s+(\d[\d.]*)", r"\1/\2", text)
    text = re.sub(r"\bdivided by\b|\bover\b", "/", text)
    text = re.sub(r"\bplus\b|\band\b", "+", text)
    text = re.sub(r"\bminus\b|\btake away\b|\bsubtract\b", "-", text)
    text = re.sub(r"\bsquared\b", "**2", text)
    text = re.sub(r"\bcubed\b", "**3", text)
    text = re.sub(
        r"\b(?:to the power of|to the power|raised to the power of|raised to the|raised to)\b",
        "**", text)
    text = text.replace("^", "**")
    text = text.replace("?", " ").strip()
    if not re.fullmatch(r"[0-9+\-*/().\s]+", text or ""):
        return None
    if not re.search(r"\d", text) or not re.search(r"[+\-*/]", text):
        return None
    if len(text) > 80:
        return None
    return text


def _calc(clean):
    expression = _expression(clean)
    if expression is None:
        return None
    try:
        value = _eval(ast.parse(expression, mode="eval"))
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return None
    if not isinstance(value, (int, float)) or value != value or abs(value) == float("inf"):
        return None
    return f"That's {_number(value)}."


# --- roots, fractions and simple equations --------------------------------

def _root(clean):
    """A square root: "what's the square root of 144", "sqrt 81"."""
    if "cube root" in clean or "fourth root" in clean:
        return None
    match = re.search(r"(?:square root(?: of)?|sqrt|root(?: of)?)\s*([\d,.]+)", clean)
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    if value < 0:
        return "A negative number has no real square root."
    root = value ** 0.5
    if abs(root - round(root)) < 1e-9:
        return f"The square root of {_number(value)} is {_number(root)}."
    return f"The square root of {_number(value)} is about {_number(root)}."


def _roots(clean):
    """A root asked for in words: "the square root of 144", "cube root of 27"."""
    match = re.search(r"(square root|cube root)\s*(?:of|is)?\s*(-?[\d,.]+)", clean)
    if not match:
        return None
    value = float(match.group(2).replace(",", ""))
    if match.group(1) == "cube root":
        root = (-1 if value < 0 else 1) * abs(value) ** (1 / 3)
        exact = round(root) ** 3 == value
        name = "cube root"
    else:
        if value < 0:
            return None
        root = value ** 0.5
        exact = round(root) ** 2 == value
        name = "square root"
    if exact:
        return f"The {name} of {_number(value)} is {_number(round(root))}."
    return f"The {name} of {_number(value)} is about {_number(round(root, 4))}."


def _prime(clean):
    """"Is 91 a prime number?": a yes or no answer with the reason, since 91 looks prime."""
    match = re.search(r"is\s+(\d+)\s+(?:a\s+)?prime", clean)
    if not match:
        return None
    number = int(match.group(1))
    if number < 2:
        return f"{number} is not prime: primes start at 2."
    divisor = next((d for d in range(2, int(number ** 0.5) + 1) if number % d == 0), None)
    if divisor:
        return f"No: {number} is {divisor} × {number // divisor}, so it is not prime."
    return f"Yes: nothing but 1 and {number} divides {number}, so it is prime."


_FRACTIONS = {
    "half": (1, 2), "halves": (1, 2), "third": (1, 3), "thirds": (1, 3),
    "quarter": (1, 4), "quarters": (1, 4), "fifth": (1, 5), "fifths": (1, 5),
    "sixth": (1, 6), "sixths": (1, 6), "eighth": (1, 8), "eighths": (1, 8),
    "tenth": (1, 10), "tenths": (1, 10),
}
_COUNTS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


# A fraction of a fraction is the question that catches more people than any other in a kitchen:
# "half of 3/4 cup". The plain fraction-of-a-number reader below took the "3" of "3/4" and said
# "half of 3 is 1.5", which is a confident answer to a question nobody asked. These helpers read
# the fraction as a fraction and keep the unit the person used.
_COUNT = r"(a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)"
_PART = (r"(half|halves|third|thirds|quarter|quarters|fifth|fifths|sixth|sixths|eighth|eighths|"
         r"tenth|tenths|\d+\s*/\s*\d+)")
_AMOUNT = r"(\d+(?:\s+\d+)?\s*/\s*\d+|\d+(?:\.\d+)?)"
_FRACTION_UNITS = (r"(cups?|tbsp|tablespoons?|tsp|teaspoons?|grams?|g|kg|ml|litres?|liters?|"
                   r"ounces?|oz|pounds?|pints?|sticks?)")
_SINGULAR = {
    "cups": "cup", "tablespoons": "tablespoon", "teaspoons": "teaspoon", "grams": "gram",
    "litres": "litre", "liters": "liter", "ounces": "ounce", "pounds": "pound", "pints": "pint",
    "sticks": "stick",
}
_CUP_IN_TBSP = 16
_CUP_IN_ML = 240

# "half of 3/4 cup", "three quarters of 200 grams", "2/3 of 3/4 cup", "half of 3/4 of a cup",
# "half of 1/2 a teaspoon", "half of 1.5 cups". The count ("three quarters"), the "of a" and the
# "a" are all how people say it.
_FRACTION_OF_FRACTION = re.compile(
    r"\b(?:(?:" + _COUNT + r")\s+)?" + _PART + r"\s+of\s+(?:a\s+|an\s+)?" + _AMOUNT +
    r"(?:\s+of)?\s+(?:a\s+|an\s+)?" + _FRACTION_UNITS + r"\b")
# The same question with no unit at all: "2/3 of 3/8" used to read the 3 of the 3/8 and answer
# "2/3 of 3 is 2". Only a fraction amount matches here, so "2/3 of 60" keeps its own row.
_FRACTION_OF_A_FRACTION = re.compile(
    r"\b(?:(?:" + _COUNT + r")\s+)?" + _PART + r"\s+of\s+\d+\s*/\s*\d+\b")


def _as_fraction(text):
    """'3/4', '1 1/2' or '1.5' as a Fraction, or None."""
    text = " ".join(str(text).split())
    whole, _, part = text.rpartition(" ")
    if "/" in part:
        top, _, bottom = part.partition("/")
        try:
            value = Fraction(int(top), int(bottom))
        except (ValueError, ZeroDivisionError):
            return None
        if whole.strip():
            try:
                value += int(whole)
            except ValueError:
                return None
        return value
    try:
        return Fraction(part)
    except (ValueError, ZeroDivisionError):
        return None


def _fraction_text(value):
    """A Fraction the way a recipe reads it: 3/8, 1 1/2, 2."""
    value = Fraction(value).limit_denominator(64)
    if value.denominator == 1:
        return str(value.numerator)
    whole, rest = divmod(value.numerator, value.denominator)
    if whole:
        return "%d %d/%d" % (whole, rest, value.denominator)
    return "%d/%d" % (rest, value.denominator)


def _fraction_of_a_fraction(clean):
    """A part of a fraction, or of a mixed number: "half of 3/4 cup", "2/3 of 3/8"."""
    match = _FRACTION_OF_FRACTION.search(clean)
    bare = not match
    if bare:
        match = _FRACTION_OF_A_FRACTION.search(clean)
    if not match:
        return None
    count_word, part_word = match.group(1), match.group(2)
    part = (Fraction(*_FRACTIONS[part_word]) if part_word in _FRACTIONS
            else _as_fraction(part_word))
    if not part:
        return None
    if count_word:
        count = int(count_word) if count_word.isdigit() else _COUNTS.get(count_word, 1)
        part = part * count
    amount_text = match.group(3) if not bare else match.group(0).split(" of ")[-1]
    amount = _as_fraction(amount_text)
    if amount is None:
        return None
    value = part * amount
    unit = "" if bare else match.group(4)
    # a quantity of one or less is singular whatever the person typed: half of 1 1/2 cups is
    # 3/4 cup, not 3/4 cups
    if value <= 1:
        unit = _SINGULAR.get(unit, unit)
    said = " ".join(word for word in (count_word, part_word) if word)
    said = said[0].upper() + said[1:]
    said_amount = _fraction_text(amount) + ((" " + match.group(4)) if not bare else "")
    answer = "%s of %s is %s%s" % (said, said_amount, _fraction_text(value),
                                   (" " + unit) if unit else "")
    if unit.startswith("cup"):
        spoons = value * _CUP_IN_TBSP
        millilitres = value * _CUP_IN_ML
        # a third of a third of a cup is not a spoon anybody measures, so the spoons are rounded
        spoon_text = (_fraction_text(spoons) if spoons.denominator == 1
                      else "about %d" % round(float(spoons)))
        answer += ", which is %s tablespoons (%d ml)" % (spoon_text, round(millilitres))
    if bare or "/" in amount_text:
        # the rule only makes sense when the amount is a fraction of something
        if part == Fraction(1, 2):
            answer += ": halve the top number and keep the bottom one."
        else:
            answer += ": multiply the tops and the bottoms."
    else:
        answer += "."
    return answer


def _fraction_of(clean):
    """A simple fraction of an amount: "half of 96", "three quarters of 200", "2/5 of 60"."""
    kitchen = _fraction_of_a_fraction(clean)
    if kitchen:
        return kitchen
    match = re.search(r"\b(\d+)\s*/\s*(\d+)\s+of\s+([\d,.]+)", clean)
    if match:
        top, bottom = float(match.group(1)), float(match.group(2))
        amount = float(match.group(3).replace(",", ""))
        label = f"{_number(top)}/{_number(bottom)}"
    else:
        match = re.search(r"\b(a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                          r"\d+)?\s*"
                          r"(half|halves|third|thirds|quarter|quarters|fifth|fifths|sixth|sixths|"
                          r"eighth|eighths|tenth|tenths)\s+of\s+([\d,.]+)", clean)
        if not match:
            return None
        said = match.group(1) or "a"
        count = int(said) if said.isdigit() else _COUNTS.get(said, 1)
        if said.isdigit():
            said = next((word for word, number in _COUNTS.items() if number == count), said)
        part, whole = _FRACTIONS[match.group(2)]
        top, bottom = part * count, whole
        amount = float(match.group(3).replace(",", ""))
        label = " ".join(word for word in match.group(1, 2) if word)
        if said.isdigit() or (match.group(1) or "").isdigit():
            label = f"{said} {match.group(2)}"  # "3 quarters" is said "three quarters"
    if not bottom or not top:
        return None
    value = amount * top / bottom
    # Keep the unit the person used: "three quarters of 60 grams" is 45 grams, not 45.
    unit = re.match(r"\s*(?:g|grams?|kg|kilograms?|ml|litres?|liters?|pounds?|oz|ounces?|"
                    r"minutes?|hours?|miles?|km|metres?|meters?)\b", clean[match.end():])
    said = f" {unit.group(0).strip()}" if unit else ""
    return (f"{label[0].upper() + label[1:]} of {_number(amount)}{said} is "
            f"{_number(round(value, 4))}{said}.")


def _share_reply(total, people, clean):
    if people < 2:
        return None
    money = next((sign for sign in ("£", "$", "€") if sign in clean), "")
    share = total / people
    return (f"That's {money}{_number(round(share, 2))} each: {money}{_number(total)} split "
            f"{people} ways.")


# A count of people as people write it: "between the three of us" is the same question as
# "between 3 of us", and the split row answered only the second one.
_A_COUNT = r"(?:\d+|two|three|four|five|six|seven|eight|nine|ten)"
_COUNT_VALUE = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10}


def _count_value(text):
    text = str(text or "").strip().lower()
    return int(text) if text.isdigit() else _COUNT_VALUE.get(text)


def _share(clean):
    """"Split 84 pounds between 6 people": a sum divided among a number of people.

    The ways round people say it differ only in where the count is ("between 6 people",
    "4 ways", "5 of us"), so the sum and the count are found separately rather than with
    one pattern per phrasing.
    """
    match = re.search(r"[£$€]?\s*([\d,.]+)\s*(?:pounds?|quid|euros?|dollars?)?\s*"
                      r"(?:split|shared|divided|share)\s+(?:it\s+)?(?:equally\s+)?"
                      r"(?:between|among|across)\s+(?:the\s+)?(" + _A_COUNT + r")\b", clean)
    if not match:
        match = re.search(r"(?:split|share|divide)\s+(?:the bill of\s+|the\s+|it\s+)?[£$€]?\s*"
                          r"([\d,.]+)\s*"
                          r"(?:pounds?|quid|euros?|dollars?)?\s*(?:equally\s+)?"
                          r"(?:between|among|across)\s+(\d+)", clean)
    if not match:
        # "96 between the three of us": no split verb at all, just the sum and who paid it.
        # Nothing else in this family puts the count straight after "between", so the shape
        # is narrow on purpose - "the difference between 84 and 96" is another row's.
        between = re.search(r"[£$€]?\s*([\d,.]+)\s*(?:pounds?|quid|euros?|dollars?|bucks?)?\s+"
                            r"between\s+(?:the\s+)?(" + _A_COUNT + r")\s+"
                            r"(?:of\s+us|of\s+them|people|friends|adults|ways)\b", clean)
        if between:
            total = float(between.group(1).replace(",", ""))
            people = _count_value(between.group(2))
            if people and people >= 2:
                return _share_reply(total, people, clean)
    if not match:
        # "we split the bill 4 ways on 86 pounds": the verb and the count, then the sum.
        if not re.search(r"\b(?:split|splitting|share|sharing|divide|dividing)\b", clean):
            return None
        ways = re.search(r"(" + _A_COUNT + r")\s*(?:ways?|people|of us|friends|adults)", clean)
        if not ways:
            return None
        money_word = re.search(r"([\d,.]+)\s*(?:pounds?|quid|euros?|dollars?|bucks?)", clean)
        if money_word:
            total_text = money_word.group(1)
        else:
            sign_sum = re.search(r"[£$€]\s*([\d,.]+)", clean)
            if sign_sum:
                total_text = sign_sum.group(1)
            else:
                left = [n for n in re.findall(r"\d+(?:\.\d+)?", clean)
                        if n != ways.group(1)]
                if not left:
                    return None
                total_text = max(left, key=float)
        match = None
        total = float(total_text.replace(",", ""))
        people = _count_value(ways.group(1))
        if not people:
            return None
        return _share_reply(total, people, clean)
    total = float(match.group(1).replace(",", ""))
    people = _count_value(match.group(2))
    if not people or people < 2:
        return None
    return _share_reply(total, people, clean)


def _dec(value, places=6):
    """A decimal the way a person writes it: 0.125, 0.75, 12."""
    text = f"{value:.{places}f}".rstrip("0").rstrip(".")
    return text or "0"


def _fraction_decimal(clean):
    """Both directions: "3/4 as a decimal" and "0.25 as a fraction".

    The number in the answer is the one the person wrote, so "0.375 as a fraction" says
    0.375 and not a rounded 0.38, and "1/8 as a decimal" says 0.125 rather than 0.12.

    A share said as "1 in 10" is one part in ten, so it is 10% and not 1000%: the number before
    "in" is the top of the fraction and the one after it is the bottom. Without this the line
    was read as "10 as a percentage" and the answer was wrong by a factor of a hundred. A
    percentage asked as a fraction or a decimal is the same sum the other way round, so
    "25% as a fraction" is 1/4 and "25% as a decimal" is 0.25 rather than a lecture on fractions.
    """
    match = re.search(r"(\d+)\s*in\s*(\d+)\s*(?:as|to|into)\s*(?:a\s+)?"
                      r"(fraction|decimal|percentage|percent)", clean)
    if match:
        top, bottom, kind = int(match.group(1)), int(match.group(2)), match.group(3)
        if not bottom:
            return None
        if kind.startswith("percent"):
            return f"{top} in {bottom} is {_dec(top / bottom * 100, 2)}%."
        if kind == "decimal":
            return f"{top} in {bottom} as a decimal is {_exact_decimal(top, bottom)}."
        part = Fraction(top, bottom).limit_denominator(1000)
        return f"{top} in {bottom} as a fraction is {part.numerator}/{part.denominator}."
    match = re.search(r"([\d,.]+)\s*(%|percent|per cent)\s*(?:as|to|into)\s*(?:a\s+)?"
                      r"(fraction|decimal)", clean)
    if match:
        written = match.group(1).rstrip(".")
        # The person's own sign: "25 percent as a fraction" is answered with "percent" in it.
        sign = "%" if match.group(2) == "%" else " percent"
        value = float(written.replace(",", ""))
        if match.group(3) == "decimal":
            return f"{written}{sign} as a decimal is {_dec(value / 100, 6)}."
        part = Fraction(value / 100).limit_denominator(1000)
        if part.denominator == 1:
            return f"{written}{sign} as a fraction is {part.numerator}."
        return f"{written}{sign} as a fraction is {part.numerator}/{part.denominator}."
    match = re.search(r"(\d+)\s*/\s*(\d+)\s*(?:as|in|to)\s*(?:a\s+)?(decimal|percentage|percent)",
                      clean)
    if match:
        top, bottom = int(match.group(1)), int(match.group(2))
        if not bottom:
            return None
        if match.group(3).startswith("percent"):
            return f"{top}/{bottom} is {_dec(top / bottom * 100, 2)}%."
        return f"{top}/{bottom} as a decimal is {_exact_decimal(top, bottom)}."
    match = re.search(r"([\d,.]+)\s*(?:as|in|to)\s*(?:a\s+)?(fraction|percentage|percent)", clean)
    if not match:
        return None
    if re.match(r"\s+of\s+[\d,.]+", clean[match.end():]):
        return None  # "15 as a percentage of 80" is a share of a whole: _what_percent has it
    written = match.group(1).rstrip(".")
    value = float(written.replace(",", ""))
    if match.group(2) == "fraction":
        part = Fraction(value).limit_denominator(1000)
        if part.denominator == 1:
            return f"{written} is a whole number: {part.numerator}."
        return f"{written} is {part.numerator}/{part.denominator}."
    return f"{written} as a percentage is {_dec(value * 100, 2)}%."


def _exact_decimal(top, bottom):
    """A fraction as a decimal: 3/8 is 0.375, not 0.38, and 1/3 is 0.33 recurring.

    A decimal that stops is written out in full, because "as a decimal" asks for the number
    itself; one that never stops is rounded to two places and marked as recurring, so it does
    not read as exact.
    """
    left = bottom
    for prime in (2, 5):
        while left % prime == 0:
            left //= prime
    if left == 1:
        return f"{top / bottom:.6f}".rstrip("0").rstrip(".")
    # "0.33" on its own reads as exact, so a value that never stops says so.
    return f"{_number(top / bottom)} recurring"


def _fraction(clean):
    """A fraction as a decimal or percentage, or a fraction of a number."""
    match = re.search(r"(-?\d+)\s*/\s*(\d+)", clean)
    if not match:
        # "3 over 8" is the same fraction said out loud
        match = re.search(r"(-?\d+)\s+(?:over|upon)\s+(\d+)", clean)
    if not match:
        return None
    top, bottom = int(match.group(1)), int(match.group(2))
    if bottom == 0:
        return None
    if "decimal" in clean:
        return f"{top}/{bottom} as a decimal is {_exact_decimal(top, bottom)}."
    if "percent" in clean:
        return f"{top}/{bottom} is {_number(top / bottom * 100)}%."
    # not a second fraction: "2/3 of 3/8" is a fraction of a fraction, and the 3 of the 3/8 is
    # not the amount being taken a share of
    of = re.search(r"/\s*\d+\s*of\s*([\d,.]+)(?!\s*/\s*\d)", clean)
    if of:
        total = float(of.group(1).replace(",", ""))
        return f"{top}/{bottom} of {_number(total)} is {_number(top / bottom * total)}."
    return None


# --- school arithmetic that carries its own numbers -----------------------
#
# A pupil writes the sum into the question - "simplify 6 over 8", "add 1/2 and 1/3", "round
# 3.456 to two decimal places", "the circumference of a circle with radius 5" - so a canned
# reply cannot answer it. Each of these reads the numbers off the line and works the answer
# out. The entries below answer the general "how do I do this" question, which has no numbers.
_FRACTION = r"(\d+)\s*(?:/|over|upon)\s*(\d+)"
_PLACES = {"one": 1, "two": 2, "three": 3, "1": 1, "2": 2, "3": 3, "a": 1}


def _reduced(top, bottom):
    """The same fraction with the common factors divided out, and what was divided out."""
    a, b = abs(top), abs(bottom)
    while b:
        a, b = b, a % b
    if not a:
        return top, bottom, 1
    return top // a, bottom // a, a


def _simplify(clean):
    """\"simplify 6 over 8\": the same fraction with no common factor left."""
    match = re.search(r"simplif(?:y|ies|ied)\s+(?:the\s+)?(?:fraction\s+)?" + _FRACTION, clean)
    if not match:
        match = re.search(_FRACTION + r"\s*(?:in|to)\s+(?:its\s+)?(?:simplest form|lowest terms)",
                          clean)
    if not match:
        return None
    top, bottom = int(match.group(1)), int(match.group(2))
    if not bottom or not top:
        return None
    simple_top, simple_bottom, by = _reduced(top, bottom)
    if by == 1:
        return (f"{top}/{bottom} is already as simple as it goes: nothing divides both "
                f"numbers.")
    return (f"{top}/{bottom} simplifies to {simple_top}/{simple_bottom}: divide the top and the "
            f"bottom by {by}.")


def _add_fractions(clean):
    """\"add 1/2 and 1/3\": a common bottom, then the tops."""
    match = re.search(_FRACTION + r"\s*(\+|plus|and|minus|-)\s*" + _FRACTION, clean)
    sentence = r"(?:add|subtract|take away)\s+(?:the fractions\s+)?" + _FRACTION + \
               r"\s+(?:and|from|to)\s+" + _FRACTION
    other = re.search(sentence, clean)
    if match:
        top_a, bottom_a = int(match.group(1)), int(match.group(2))
        sign = "-" if match.group(3) in ("-", "minus") else "+"
        top_b, bottom_b = int(match.group(4)), int(match.group(5))
    elif other:
        top_a, bottom_a = int(other.group(1)), int(other.group(2))
        top_b, bottom_b = int(other.group(3)), int(other.group(4))
        sign = "-" if clean.startswith("subtract") or "take away" in clean else "+"
    else:
        return None
    if not (bottom_a and bottom_b):
        return None
    # The common bottom is the lowest one, not the two multiplied: 1/2 + 1/4 is over 4, the way
    # it is taught, so the gcd of the bottoms is what is divided out of the product.
    _, _, shared = _reduced(bottom_a, bottom_b)
    bottom = bottom_a * bottom_b // (shared or 1)
    left, right = bottom // bottom_a, bottom // bottom_b
    top = top_a * left + (top_b * right if sign == "+" else -top_b * right)
    simple_top, simple_bottom, _ = _reduced(top, bottom)
    way = "add the tops" if sign == "+" else "subtract the tops"
    if bottom_a == bottom_b:
        return (f"{top_a}/{bottom_a} {sign} {top_b}/{bottom_b} = {simple_top}/{simple_bottom}: "
                f"the bottoms are the same, so just {way}.")
    return (f"{top_a}/{bottom_a} {sign} {top_b}/{bottom_b} = {simple_top}/{simple_bottom}. Put both "
            f"over {bottom} ({top_a * left}/{bottom} and {top_b * right}/{bottom}), {way}, "
            f"then cancel down.")


def _factors_in_list(words):
    """The whole-number factors of one number, smallest first."""
    out = []
    step = 1
    while step * step <= words:
        if words % step == 0:
            out.append(step)
            if step != words // step:
                out.append(words // step)
        step += 1
    return sorted(out)


def _said_list(numbers):
    """1, 2, 3 and 6 - the way a list of numbers is written out loud."""
    said = [str(number) for number in numbers]
    if len(said) <= 1:
        return "".join(said)
    return ", ".join(said[:-1]) + " and " + said[-1]


def _the_factors(clean):
    """\"the factors of 12\", \"what are the factors of 36\", \"list the factors of 24\".

    A factor is a number that divides in with nothing left over, and people ask for the list far
    more often than they ask what the word means: "the factors of 12" reached nothing at all and
    "what are the factors of 36" was answered with the definition of a factor. The definition is
    kept as the second sentence, where it belongs.
    """
    if re.search(r"common factor|common multiple|prime factor|factorise|factorize|factor tree|"
                 r"factor the|factor out|scale factor|conversion factor|factor of safety",
                 clean):
        return None
    # "is 3 a factor of 12" and "is 15 or 20 a factor of 30": the answer is a yes or a no with the
    # sum behind it, and both numbers have to be answered when the line names two.
    found = re.search(r"\bis\s+(\d+)\s*(?:,|\bor\b|\band\b|/)?\s*(?:and\s+)?(\d+)?\s+"
                      r"a\s+factor\s+of\s+(\d+)\b", clean)
    if found:
        asked = [int(found.group(1))]
        if found.group(2):
            asked.append(int(found.group(2)))
        whole = int(found.group(3))
        if whole < 1 or max(asked) > 1000000:
            return None
        said = []
        for number in asked:
            if number > whole:
                said.append(f"{number} is bigger than {whole}, so no: it cannot divide into it "
                            f"even once.")
            elif whole % number == 0:
                said.append(f"{number} is a factor of {whole}: {whole} divided by {number} is "
                            f"{whole // number}.")
            else:
                times = whole // number
                left = whole - times * number
                said.append(f"{number} is not a factor of {whole}: {number} goes in {times} "
                            f"time{'s' if times != 1 else ''} with {left} left over.")
        if len(said) == 1:
            return said[0]
        return " ".join(said)
    # "is 12 a multiple of 3" is the same question the other way round
    found = re.search(r"\bis\s+(\d+)\s+a\s+multiple\s+of\s+(\d+)\b", clean)
    if found:
        number, base = int(found.group(1)), int(found.group(2))
        if not base or max(number, base) > 1000000:
            return None
        if number % base == 0:
            return (f"Yes: {number} is {base} x {number // base}, so it is in the {base} times "
                    f"table.")
        return (f"No: {base} x {number // base} is {base * (number // base)}, and {base} x "
                f"{number // base + 1} is {base * (number // base + 1)}, so {number} is not in "
                f"the {base} times table.")
    # the list, when the line asks for the factors rather than whether one is a factor
    found = re.search(r"\bfactors? of\s+(\d+)\b(?!\s*(?:and|&)\b)", clean)
    if found:
        number = int(found.group(1))
        if number < 1 or number > 100000:
            return None
        factors = _factors_in_list(number)
        pairs = []
        for small in factors:
            if small * small > number:
                break
            pairs.append(f"{small} x {number // small}")
        said = (f"The factors of {number} are {_said_list(factors)}: those are the numbers that "
                f"divide into {number} with nothing left over, counting 1 and {number} itself.")
        if len(factors) == 2:
            return said + f" That makes {number} a prime number."
        said += f" You only have to try up to {int(number ** 0.5)} - the square root - because "
        said += "the pairs do the rest: " + ", ".join(pairs) + "."
        return said
    return None


def _common_factors(clean):
    """\"highest common factor of 12 and 18\", \"lowest common multiple of 4 and 6\"."""
    asked = None
    if re.search(r"highest common factor|greatest common (?:factor|divisor)|\bhcf\b|\bgcd\b",
                 clean):
        asked = "highest common factor"
    elif re.search(r"lowest common multiple|least common multiple|\blcm\b", clean):
        asked = "lowest common multiple"
    if not asked:
        return None
    numbers = re.findall(r"\b(\d+)\b", clean)
    if len(numbers) < 2:
        return None
    first, second = int(numbers[0]), int(numbers[1])
    if not first or not second:
        return None
    a, b = first, second
    while b:
        a, b = b, a % b
    if asked == "highest common factor":
        return f"The highest common factor of {first} and {second} is {a}."
    return (f"The lowest common multiple of {first} and {second} is "
            f"{first // a * second}.")


_NEAREST = {"whole": 0, "unit": 0, "units": 0, "one": 0, "ten": -1, "tens": -1, "10": -1,
            "hundred": -2, "hundreds": -2, "100": -2, "thousand": -3, "thousands": -3,
            "1000": -3}


def _round_to(clean):
    """\"round 3.456 to two decimal places\", \"round 2.5 to the nearest whole number\"."""
    match = re.search(r"round\s+(-?\d+(?:\.\d+)?)\s*(?:to|at)\s*(?:the\s+)?(\w+)\s*"
                      r"(decimal places?|places?|dp|significant figures?)", clean)
    if not match:
        # "round 2.5 to the nearest whole number" is the commonest way of saying it, and the
        # counting word carries the place: whole number, ten, hundred, thousand.
        near = re.search(r"round\s+(-?\d+(?:\.\d+)?)\s*(?:up|down|off)?\s*(?:to|at)\s*"
                         r"(?:the\s+)?nearest\s+(\w+)", clean)
        if not near or near.group(2) not in _NEAREST:
            # "how do i round 4.6" names a number and no place, which almost always means the
            # whole number. The card that explains the rule answered it without ever rounding
            # the number they gave, so the rule is said and applied in one line. A decimal point
            # is required: "round 3" on its own is a sports line as often as a sum.
            bare = re.search(r"\bround\s+(-?\d+\.\d+)\s*$", clean)
            if not bare:
                return None
            written = bare.group(1)
            kept = _places(written, 0)
            value = Decimal(str(written))
            why = "up" if value.quantize(Decimal(1), rounding=ROUND_HALF_UP) > value else "down"
            return (f"{written} is {kept} to the nearest whole number: the digit after the "
                    f"point decides it, so the whole number goes {why}.")
        written, word = near.group(1), near.group(2)
        below = _NEAREST[word]
        if below:
            stepped = Decimal(str(written)).quantize(Decimal(1).scaleb(-below),
                                                     rounding=ROUND_HALF_UP)
            return f"{written} is {stepped:f} to the nearest {word}."
        what = "whole number" if _NEAREST[word] == 0 else word
        return f"{written} is {_places(written, 0)} to the nearest {what}."
    written = match.group(1)
    value = float(written)
    places = _PLACES.get(match.group(2))
    if places is None:
        return None
    plural = "s" if places != 1 else ""
    if "figure" in match.group(3):
        if not value:
            return None
        from math import floor, log10
        digits = places - int(floor(log10(abs(value)))) - 1
        rounded = round(value, digits)
        return (f"{written} is {_number(rounded)} to {match.group(2)} significant "
                f"figure{plural}.")
    return (f"{written} is {_places(written, places)} to {match.group(2)} "
            f"decimal place{plural}.")


def _places(written, places):
    """A decimal rounded by the hand rule, so 2.675 is 2.68.

    `round(2.675, 2)` gives 2.67, because 2.675 is stored just under itself in binary and the
    half never arrives; a school answer has to round a half up, which is what Decimal does on
    the digits as written.
    """
    kept = Decimal(str(written)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    text = f"{kept:f}"
    if "." not in text:
        return text
    return text.rstrip("0").rstrip(".") or "0"


def _circle_measure(clean):
    """The circumference of a circle, from its radius or its diameter."""
    if "circumference" not in clean:
        return None
    match = re.search(r"radius\s*(?:of\s*)?(\d+(?:\.\d+)?)", clean)
    if match:
        radius = float(match.group(1))
    else:
        match = re.search(r"diameter\s*(?:of\s*)?(\d+(?:\.\d+)?)", clean)
        if not match:
            return None
        radius = float(match.group(1)) / 2
    around = 2 * 3.141592653589793 * radius
    return (f"The circumference is 2 x pi x radius, so about {_number(round(around, 2))} "
            f"(3.14 x {_number(round(2 * radius, 2))}).")


def _box_volume(clean):
    """\"volume of a box 10cm by 5cm by 2cm\": length x width x height."""
    if "volume" not in clean:
        return None
    numbers = re.findall(r"(\d+(?:\.\d+)?)\s*(?:cm|m|mm|metres?|centimetres?|inches?|in\b)?"
                         r"\s*(?:by|x|\*)\s*(\d+(?:\.\d+)?)\s*(?:cm|m|mm)?\s*"
                         r"(?:by|x|\*)\s*(\d+(?:\.\d+)?)", clean)
    if not numbers:
        return None
    length, width, height = (float(size) for size in numbers[0])
    volume = length * width * height
    unit = "cm" if "cm" in clean else "m" if re.search(r"\bmetres?\b|\bm\b", clean) else ""
    return (f"{_number(length)} x {_number(width)} x {_number(height)} is "
            f"{_number(round(volume, 2))}{(' ' + unit + '3') if unit else ''}.")
# --- quadratics -----------------------------------------------------------
#
# "Solve x squared plus 5x plus 6 equals 0" is a school question with a real answer, and the
# solver below could only do ax + b = c, so it shrugged. The words are turned into the signs
# they mean, the three numbers are read off, and the answer comes from the formula every
# time - which also covers the ones that do not factor, and the ones with no real root.

_MATHS_WORDS = (
    (r"(?<![a-z])x\s*squared\b|\bxsquared\b", "x^2"),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\bequals\b|\bequal\s+to\b", "="),
    (r"\bzero\b", "0"),
    (r"\bnegative\s+", "-"),
    (r"\b(?:find|work\s+out|solve\s+for)\s+x\b", "solve"),
)

# A quadratic nobody asked to solve is not a question: "x squared plus 5x plus 6" on its own
# is a phrase, and only these words make it the school task.
_QUADRATIC_ASK = ("solve", "solves", "root", "roots", "zero", "zeros", "factorise", "factorize",
                  "factor", "factors", "find", "work", "value")


# The asks that want the brackets rather than the roots.
_FACTOR_ASK = ("factorise", "factorize", "factor", "factors", "brackets")


def _factorised(a, b, c):
    """(m, (p, q, r, s)) for m(px + q)(rx + s) in whole numbers, or None.

    The common factor comes out first: 2x squared minus 8 is 2(x - 2)(x + 2), and searching
    the brackets alone found (x - 2)(2x + 4), which is right but not the way it is written.
    """
    if a != int(a) or b != int(b) or c != int(c) or a < 1:
        return None
    a, b, c = int(a), int(b), int(c)
    common = 0
    for number in (a, b, c):
        common = _gcd(common, number)
    if common < 1:
        common = 1
    a, b, c = a // common, b // common, c // common
    reach = abs(b) + abs(c) + 1
    for p in range(1, a + 1):
        if a % p:
            continue
        r = a // p
        # s follows from p*s + r*q = b, so only q has to be tried: 3x squared plus 6x is
        # 3x(x + 2), and searching the pairs of the constant alone missed it because the
        # constant is zero.
        for q in range(-reach, reach + 1):
            top = b - r * q
            if top % p:
                continue
            s = top // p
            if q * s == c:
                return (common, (p, q, r, s))
    return None


def _gcd(one, other):
    while other:
        one, other = other, one % other
    return abs(one)


def _said(found):
    """(1, 3, 1, 4) said as (x + 3)(x + 4), and twice the same bracket as (x + 1)^2."""
    common, (p, q, r, s) = found

    def bracket(lead, tail):
        left = "x" if lead == 1 else f"{lead}x"
        if not tail:
            return f"({left})"
        return f"({left} + {tail})" if tail > 0 else f"({left} - {abs(tail)})"

    first, second = bracket(p, q), bracket(r, s)
    if common != 1 and first == "(x)":
        # 3x squared plus 6x is 3x(x + 2): the common factor and the bare x are one word
        return f"{common}x{second}"
    said = f"{first}^2" if first == second else first + second
    return said if common == 1 else f"{common}{said}"


def _quadratic(clean):
    """A quadratic equation with x squared in it, worked out: "x squared + 5x + 6 = 0"."""
    text = clean
    for pattern, swap in _MATHS_WORDS:
        text = re.sub(pattern, swap, text)
    text = re.sub(r"\s+", " ", text).strip()
    lead = re.search(r"(?:^|\s)([+-]?\d*\.?\d*)\s*\*?\s*x\s*\^\s*2", text)
    if not lead:
        return None
    rest = text[lead.end():].strip()
    # the linear term, if there is one
    b = 0.0
    linear = re.match(r"([+-])\s*(\d*\.?\d*)\s*\*?\s*x(?![\w^])", rest)
    if linear:
        size = float(linear.group(2)) if linear.group(2) else 1.0
        b = size if linear.group(1) == "+" else -size
        rest = rest[linear.end():].strip()
    # the constant, if there is one
    c = 0.0
    constant = re.match(r"([+-])\s*(\d*\.?\d*)", rest)
    if constant:
        size = float(constant.group(2)) if constant.group(2) else 1.0
        c = size if constant.group(1) == "+" else -size
        rest = rest[constant.end():].strip()
    # the right-hand side, which is usually zero
    right = 0.0
    if rest.startswith("="):
        side = rest[1:].strip()
        if not re.fullmatch(r"[+-]?\d+\.?\d*", side):
            return None
        right = float(side)
        rest = ""
    if rest:
        return None
    raw = lead.group(1)
    a = 1.0 if raw in ("", "+") else -1.0 if raw == "-" else float(raw)
    if not a:
        return None
    asked = clean.replace("^2", " ").split()
    if right == 0 and not any(word in asked for word in _QUADRATIC_ASK):
        return None
    c -= right
    discriminant = b * b - 4 * a * c
    factorised = _factorised(a, b, c)
    wants_brackets = any(word in asked for word in _FACTOR_ASK)
    if discriminant < -1e-9:
        if wants_brackets:
            return (f"It does not factorise with whole numbers, and no real number solves it "
                    f"either: the square of a number is never negative, so the formula stops "
                    f"at the square root of a negative number.")
        return (f"No real number solves that: the square of a number is never negative, so "
                f"there is no real answer. (The formula gives the square root of a negative "
                f"number here.)")
    if abs(discriminant) < 1e-9:
        root = -b / (2 * a)
        if wants_brackets and factorised:
            return (f"It factorises as {_said(factorised)}, so x = {_number(root)} is the only "
                    f"answer: both brackets are the same, which is why there is one root, not "
                    f"two.")
        said = (f"x = {_number(root)}. There is one answer, not two, because both roots of the "
                f"formula are the same.")
        if factorised:
            said += f" The factorised form is {_said(factorised)}."
        return said
    roots = sorted(((-b + discriminant ** 0.5) / (2 * a), (-b - discriminant ** 0.5) / (2 * a)))
    whole = all(abs(root - round(root)) < 1e-9 for root in roots)
    # "factorise x squared plus 7x plus 12" asks for the brackets, not for the roots: the
    # roots are how you check it. The brackets come out in whole numbers whenever the
    # equation has them, and 2x squared plus 3x minus 2 gives (2x - 1)(x + 2), which the
    # roots alone would have printed as 0.5 and -2 with an apology that it does not factor.
    if wants_brackets:
        if factorised:
            said = (f"It factorises as {_said(factorised)}, so x = "
                    f"{_number(roots[0])} or x = {_number(roots[1])}.")
            if abs(roots[0] - roots[1]) > 1e-9:
                return said + " Multiply the brackets out to check you get the equation back."
            return said
        return (f"It does not factorise with whole numbers, so put a = {_number(a)}, "
                f"b = {_number(b)} and c = {_number(c)} into x = (-b +/- the square root of "
                f"b squared - 4ac) / 2a: that gives x = {_number(round(roots[0], 2))} or "
                f"x = {_number(round(roots[1], 2))}.")
    if whole:
        left, high = int(round(roots[0])), int(round(roots[1]))
        said = (f"x = {left} or x = {high}. Put either one back in and the equation comes to "
                f"zero, which is the check.")
        if factorised:
            said += f" The factorised form is {_said(factorised)}."
        return said
    # 2x squared plus 3x minus 2 has the exact roots -2 and 0.5 and the brackets (2x - 1)(x + 2),
    # so "to two decimal places" and "it does not factor" were both untrue of it. A root that
    # stops at two decimals is printed as it is, and the formula is only named when the roots
    # really do run on.
    exact = all(abs(root - round(root, 2)) < 1e-9 for root in roots)
    if factorised:
        return (f"x = {_number(roots[0])} or x = {_number(roots[1])}, and both are exact: the "
                f"factorised form is {_said(factorised)}. Put either one back in and the "
                f"equation comes to zero.")
    if exact:
        return (f"x = {_number(roots[0])} or x = {_number(roots[1])}. Put either one back in "
                f"and the equation comes to zero, which is the check.")
    return (f"x = {_number(round(roots[0], 2))} or x = {_number(round(roots[1], 2))}, to two "
            f"decimal places: it does not factor with whole numbers, so use the formula "
            f"x = (-b +/- the square root of b squared - 4ac) / 2a.")


def _equation(clean):
    """A one-variable equation with x: "solve 2x + 3 = 11"."""
    if "=" not in clean or not re.search(r"(?<![a-z])x(?![a-z])", clean):
        return None
    if not (any(word in clean for word in ("solve", "find x", "value of x", "what is x"))
            or re.fullmatch(r"[\s0-9x+\-=*.]*", clean)):
        return None
    match = re.search(r"([+-]?\d*)\*?x(?![a-z])\s*([+-]\s*\d+(?:\.\d+)?)?\s*=\s*"
                      r"([+-]?\d+(?:\.\d+)?)", clean)
    if not match:
        return None
    coefficient = float(match.group(1)) if match.group(1) not in ("", "+", "-") else 1.0
    if match.group(1) == "-":
        coefficient = -1.0
    add = float(match.group(2).replace(" ", "")) if match.group(2) else 0.0
    right = float(match.group(3).replace(" ", ""))
    if not coefficient:
        return None
    x = (right - add) / coefficient
    return f"x = {_number(x)}."


# --- percentages ----------------------------------------------------------

def _percent(clean):
    # A tip line wants the tip and the total, which _tip gives below. Only a "what is 20
    # percent of 60" line is a plain share and belongs here.
    if re.search(r"(?:%|percent|per cent)\s*(?:tip|gratuity)\b", clean):
        return None
    after = re.search(r"(?:costs?|priced at|is|are|was)\s+(?:£|\$)?([\d,.]+)\D.*?"
                      r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)\s*off", clean)
    if after:
        total, part = _amount(after.group(1)), _amount(after.group(2))
        amount = total * part / 100
        return (f"{_number(part)}% off {_number(total)} leaves {_number(total - amount)} "
                f"(you save {_number(amount)}).")
    # A named share of a bill is the same sum: "20 percent service charge on 85" is 17.
    # A tip is not here: a tip question wants the tip and the total, which _tip gives.
    # "off" keeps its own wording below.
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)\s*"
                      r"(?:service(?:\s+charge)?|tax|charge|vat)?\s*"
                      r"(of|off|on(?:\s+top\s+of)?)\s*"
                      r"(?:(?:my|our|the|a|an)\s+)?"
                      r"(?:(?:bill|total|check|tab)\s+of\s+)?([\d,.]+)", clean)
    if not match:
        match = re.search(r"what(?:'s| is)\s*(\d+(?:\.\d+)?)\s*(of|off)\s*([\d,.]+)\s*%", clean)
        if not match:
            return None
        part, kind, total = float(match.group(1)), match.group(2), float(match.group(3).replace(",", ""))
    else:
        part, kind, total = float(match.group(1)), match.group(2), float(match.group(3).replace(",", ""))
    amount = total * part / 100
    if kind == "off":
        return (f"{_number(part)}% off {_number(total)} leaves {_number(total - amount)} "
                f"(you save {_number(amount)}).")
    return f"{_number(part)}% of {_number(total)} is {_number(amount)}."


def _percentage_change(clean):
    match = re.search(r"(?:percentage|percent)\s+(?:increase|change|difference)\s+from\s+"
                      r"([\d,.]+)\s+to\s+([\d,.]+)", clean)
    if not match:
        return None
    start = float(match.group(1).replace(",", ""))
    end = float(match.group(2).replace(",", ""))
    if not start:
        return None
    change = (end - start) / start * 100
    word = "increase" if change >= 0 else "decrease"
    return f"That's a {_number(abs(change))}% {word}."


# --- one number worked out from another -----------------------------------
#
# A share of a whole, and an amount with a percentage added on. The fraction of an amount
# and the bill split among people already live above with the rest of the arithmetic, so
# each shape is worked out in one place only.


def _amount(text):
    """The number a short phrase gives, as a float."""
    return float(text.replace(",", ""))


def _what_percent(clean):
    """One number as a percentage of another: "what percentage is 15 of 80"."""
    part = total = None
    match = re.search(r"what (?:percentage|percent) of ([\d,.]+) is ([\d,.]+)", clean)
    if match:
        total, part = _amount(match.group(1)), _amount(match.group(2))
    if part is None:
        match = re.search(r"what (?:percentage|percent) (?:is )?([\d,.]+) (?:of|out of) "
                          r"([\d,.]+)", clean)
        if match:
            part, total = _amount(match.group(1)), _amount(match.group(2))
    if part is None:
        # The same sum the other way round: "20 is what percent of 80" puts the part first and
        # the question in the middle, which nothing read, so the line got an ack.
        match = re.search(r"([\d,.]+)\s+(?:is\s+)?what\s+(?:percentage|percent)\s+of\s+([\d,.]+)",
                          clean)
        if match:
            part, total = _amount(match.group(1)), _amount(match.group(2))
    if part is None:
        match = re.search(r"([\d,.]+) (?:out of|of) ([\d,.]+) (?:as a |in )?"
                          r"(?:percentage|percent)", clean)
        if match:
            part, total = _amount(match.group(1)), _amount(match.group(2))
    if part is None:
        match = re.search(r"([\d,.]+) as a (?:percentage|percent) of ([\d,.]+)", clean)
        if match:
            part, total = _amount(match.group(1)), _amount(match.group(2))
    if part is None or not total:
        return None
    share = part / total * 100
    said = _number(round(share, 1))
    exact = abs(share - round(share)) < 1e-9
    return f"{_number(part)} is {'exactly ' if exact else 'about '}{said}% of {_number(total)}."


def _a_share_of_a_group(clean):
    """A share scaled to a bigger group: "1 in 5 of 200" is 40 people.

    "if 1 in 5 people do it how many in 200" is the commonest way this turns up, and nothing
    answered it: the line was only noted back to the person. The share can be said in words
    ("one in five people") and the group can come before the question ("out of 200 people how
    many if 1 in 5"), so the two numbers are read separately: first the share, then the size of
    the group, from whatever wording carries it.
    """
    bare = _COUNT.strip("()")  # the alternation without its own group, so the two
    # numbers land in groups 1 and 2
    share = re.search(r"\b(%s)\s+in\s+(%s)\b" % (bare, bare), clean)
    if not share:
        return None
    top = _COUNTS.get(share.group(1))
    bottom = _COUNTS.get(share.group(2))
    if top is None or bottom is None:
        try:
            top, bottom = int(share.group(1)), int(share.group(2))
        except ValueError:
            return None
    if not bottom or top > bottom:
        return None
    rest = clean[:share.start()] + " " + clean[share.end():]
    # The size of the group, in any of the shapes people put it in, and never the share itself
    # (the share is cut out of the line first, so "1 in 5" cannot be read as a group of 5).
    size = None
    for pattern in (r"how many (?:people |of them |would that be )?(?:are |is )?"
                    r"(?:in|of|out of|from|out of a)\s+(\d+)",
                    r"\b(?:in|of|out of|from)\s+(\d+)\s+(?:people|persons|students|"
                    r"adults|children|kids|men|women|workers|drivers|homes|households)",
                    r"\b(?:out of|of|from)\s+(\d+)\b"):
        match = re.search(pattern, rest)
        if match:
            size = int(match.group(1))
            break
    if not size or size < 2:
        return None
    count = top * size / bottom
    if abs(count - round(count)) < 1e-9:
        answer = _number(int(round(count)))
    else:
        answer = "about " + _number(round(count, 1))
    said = "%s in %s" % (_number(top), _number(bottom))
    if top == 1:
        said = "1 in %s" % _number(bottom)
    return (f"{said} of {_number(size)} is {answer}. That is the share times the group: "
            f"{_number(size)} divided by {_number(bottom)}"
            + (f", times {_number(top)}." if top > 1 else "."))


def _percent_on(clean):
    """A percentage added to an amount: "add 20% to 40", "40 plus VAT", "add VAT to 240"."""
    # The school shape: "increase 40 by 25%" and "decrease 60 by 10%" name the amount first and
    # the change after it. A sum said that way had no row, so the line got an ack.
    match = re.search(r"\b(increase|decrease|raise|reduce|lower|go up|go down|goes up|goes down)"
                      r"\s+(?:of\s+)?(?:£|\$)?([\d,.]+)\s+by\s+(\d+(?:\.\d+)?)\s*"
                      r"(?:%|percent|per cent)", clean)
    if match:
        total, part = _amount(match.group(2)), _amount(match.group(3))
        going_down = match.group(1) in ("decrease", "reduce", "lower", "go down", "goes down")
        changed = total * (1 - part / 100 if going_down else 1 + part / 100)
        return (f"{_number(total)} {'decreased' if going_down else 'increased'} by "
                f"{_number(part)}% is {_number(round(changed, 2))}.")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)\s+"
                      r"(?:on(?:\s+top\s+of)?|onto|added\s+to)\s+"
                      r"(?:£|\$)?([\d,.]+)", clean)
    if match:
        part, total = _amount(match.group(1)), _amount(match.group(2))
        return f"{_number(total)} plus {_number(part)}% is {_number(total * (1 + part / 100))}."
    # "20 percent more than 45" and "20 percent less than 45" put the comparison in words, and
    # the answer is the new amount, not the percentage on its own - which is all the definition
    # of a percentage could give.
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)\s+"
                      r"(more|less|fewer|higher|lower)\s+than\s+(?:£|\$|€)?\s*([\d,.]+)", clean)
    if match:
        part, way, total = _amount(match.group(1)), match.group(2), _amount(match.group(3))
        if way in ("more", "higher"):
            return f"{_number(total)} plus {_number(part)}% is {_number(total * (1 + part / 100))}."
        return (f"{_number(total)} less {_number(part)}% is "
                f"{_number(total * (1 - part / 100))}.")
    # "a 45 pound thing with 20 percent off": the amount comes first and the discount after it.
    # The currency word is required, so "3 things with 20 percent off" is not read as a sum, and
    # a line that already says what the thing is or costs - "a coat is 60 pounds with 25 percent
    # off" - keeps the "off" row's wording below, which also says what is saved.
    if re.search(r"(?:costs?|priced at|is|are|was)\s+(?:£|\$|€)?\s*[\d,.]+\D.*?"
                 r"(?:\d+(?:\.\d+)?)\s*(?:%|percent|per cent)\s*off", clean):
        return None
    match = re.search(r"(?:£|\$|€)?\s*([\d,.]+)\s*(?:pounds?|quid|euros?|dollars?|bucks?)\s+"
                      r"(?:[a-z]+\s+){0,3}?(?:with|at|minus|less)\s+(\d+(?:\.\d+)?)\s*"
                      r"(?:%|percent|per cent)\s*off\b", clean)
    if match:
        total, part = _amount(match.group(1)), _amount(match.group(2))
        return (f"{_number(total)} less {_number(part)}% is "
                f"{_number(total * (1 - part / 100))}.")
    match = re.search(r"(?:add|increase)\s+(?:a\s+)?(\d+(?:\.\d+)?)\s*"
                      r"(?:%|percent|per cent)\s*(?:tip|service|tax|charge)?\s*"
                      r"(?:on|to|onto)\s+(?:£|\$)?([\d,.]+)", clean)
    if match:
        part, total = _amount(match.group(1)), _amount(match.group(2))
        return f"{_number(total)} plus {_number(part)}% is {_number(total * (1 + part / 100))}."
    # The same sum taken away: "subtract 10 percent from 55", "55 minus 10 percent", "knock
    # 15% off 80". The words are the only difference from the rows above, and a line that says
    # the amount is going down is asking for a smaller number, not a bigger one.
    # "knock 15% off 80" is the plain "15% off 80" line with a verb in front, and _percent
    # already answers it in its own words ("15% off 80 leaves 68 (you save 12)"). Only the
    # lines nothing answered change here.
    if re.search(r"\d+(?:\.\d+)?\s*(?:%|percent|per cent)\s*off\s+(?:£|\$)?[\d,.]+", clean):
        return None
    match = re.search(r"(?:subtract|deduct|minus|take|taking|remove|knock|strip)\s+(?:a\s+|off\s+)?"
                      r"(?:the\s+)?(\d+(?:\.\d+)?)\s*(?:%|percent|per cent|per cent)\s*"
                      r"(?:off|from|of)\s+(?:£|\$)?([\d,.]+)", clean)
    if match:
        part, total = _amount(match.group(1)), _amount(match.group(2))
        return (f"{_number(total)} less {_number(part)}% is "
                f"{_number(total * (1 - part / 100))}.")
    match = re.search(r"([\d,.]+)\s*(?:minus|less|without)\s*(\d+(?:\.\d+)?)\s*"
                      r"(?:%|percent|per cent)", clean)
    if match:
        total, part = _amount(match.group(1)), _amount(match.group(2))
        return (f"{_number(total)} less {_number(part)}% is "
                f"{_number(total * (1 - part / 100))}.")
    match = re.search(r"([\d,.]+)\s*(?:plus|and)\s*(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)",
                      clean)
    if match:
        total, part = _amount(match.group(1)), _amount(match.group(2))
        return f"{_number(total)} plus {_number(part)}% is {_number(total * (1 + part / 100))}."
    match = re.search(r"([\d,.]+)\s*(?:plus|with|including|before)\s+vat", clean)
    if match:
        total = _amount(match.group(1))
        return (f"{_number(total)} plus VAT at 20% is {_number(total * 1.2)}.")
    # The same sum the other way round in the sentence: "add VAT to 240". People put the
    # amount after the word as often as before it, and "add 20% VAT to 240" is the same line.
    match = re.search(r"(?:add|plus)\s+(?:(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)\s+)?"
                      r"(?:the\s+)?vat\s+(?:on|to|onto)\s*(?:£|\$)?([\d,.]+)", clean)
    if match:
        part = _amount(match.group(1)) if match.group(1) else 20.0
        total = _amount(match.group(2))
        return f"{_number(total)} plus VAT at {_number(part)}% is {_number(total * (1 + part / 100))}."
    # And the price with the VAT taken back off it, which is what a receipt asks for.
    match = re.search(r"(?:take|takes|taking|remove|removing|strip|knock)\s+(?:the\s+)?vat\s+"
                      r"(?:off|from|out of)\s*(?:£|\$)?([\d,.]+)", clean)
    if not match:
        match = re.search(r"([\d,.]+)\s*(?:minus|less|without|excluding|ex)\s+vat", clean)
    if match:
        total = _amount(match.group(1))
        return (f"{_number(total)} with VAT taken off is {_number(total / 1.2)}, "
                f"and the VAT in it is {_number(total - total / 1.2)}.")
    return None


# A price, a rent or a wage that gains or loses a percentage: "my rent is 800 and is going up
# 5 percent", "a 3 percent rise on 24000". The line names what the money is for, but what it
# asks for is still a sum - the tenancy row and the pay-rise row would answer the advice and
# never give the number - so the arithmetic is done here, ahead of the entries.
_PERCENT_UP = (r"(?:going|goes|went|gone|is|are)\s+up|up\s+by|rise|rises|rising|rose|"
               r"increase|increases|increased|more|higher|extra|hike|hikes|hiked|"
               r"jump|jumps|jumped|on\s+top|raise|raises|raised")
_PERCENT_DOWN = (r"(?:going|goes|went|gone|is|are)\s+down|down\s+by|drop|drops|dropped|"
                 r"fall|falls|fell|cut|cuts|slashed|reduce|reduced|less|cheaper|lower")
_PERCENT_ADVICE = ("should i", "fair", "legal", "allowed", "normal", "refuse", "worth it",
                   "can they", "can my landlord", "too much", "right", "negotiate", "accept")
_MONEY_WORD = re.compile(r"\b(?:rent|bill|price|salary|wage|wages|pay|cost|quote|fare|"
                         r"mortgage|charge|rate|total|fee|premium|budget|balance|"
                         r"deposit|pension|tax|income|earnings)\b")


def _percent_rise(clean):
    """The money a percentage adds to or takes off: "rent 800 going up 5 percent"."""
    percents = re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)", clean)
    if len(percents) != 1:
        return None
    part = float(percents[0])
    if not 0 < part <= 100:
        return None
    # The amount is the other number in the line, and it has to read as money: a currency
    # sign, three figures or more, or a word that says whose money it is. One of those keeps
    # "my pace went up 10 percent" out of here.
    money_word = bool(_MONEY_WORD.search(clean))
    amount = None
    for raw in re.finditer(r"(?:£|\$|€)?\s*(\d[\d,]*(?:\.\d+)?)", clean):
        number = _amount(raw.group(1))
        if abs(number - part) < 1e-9:
            continue
        if raw.group(0).strip()[:1] in "£$€" or number >= 100 or money_word:
            amount = number
            break
    if amount is None:
        return None
    if any(phrase in clean for phrase in _PERCENT_ADVICE):
        return None
    up = re.search(r"\b(?:%s)\b" % _PERCENT_UP, clean)
    down = re.search(r"\b(?:%s)\b" % _PERCENT_DOWN, clean)
    if bool(up) == bool(down):
        # nothing said about direction, or both said: leave it to the rows that read the line.
        return None
    change = amount * part / 100
    if up:
        return (f"{_number(part)}% of {_number(amount)} is {_number(change)}, so it goes up to "
                f"{_number(amount + change)}.")
    return (f"{_number(part)}% of {_number(amount)} is {_number(change)}, so it comes down to "
            f"{_number(amount - change)}.")


# The follow-up: "and 20 percent of that", "what would 5 percent be". The amount is not in the
# line because it was in the chat a turn or two ago, so the sum is worked out on that figure.
# A bare "my rent went up 5 percent" is not this - it has no ask and no "of that" - and stays
# with the rows that read the whole line.
_PERCENT_ASK_TAIL = re.compile(
    r"\b(?:of|off|on)\s+(?:that|it|this|those|them|the\s+(?:rent|bill|price|salary|total|"
    r"figure|number|amount|money))\b|\b(?:be|come\s+to|work\s+out\s+to)\b[\s?.!]*$")
_PERCENT_ASK_WORD = re.compile(r"\b(?:what|whats|what's|how\s+much|how\s+many|would|"
                               r"will|could|should|does|is|was)\b")


def _amount_in_the_chat(memory):
    """The last amount the person said, skipping the percentages in what they said."""
    for said in reversed((memory.get("turns") or [])[-3:]):
        if not isinstance(said, dict):
            continue
        text = re.sub(r"\d+(?:\.\d+)?\s*(?:%|percent|per cent)", " ",
                      str(said.get("user") or "").lower())
        numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", text)
        if not numbers:
            continue
        value = _amount(numbers[-1])
        if value >= 10:
            return value
    return None


def _percent_of_the_figure_in_the_chat(clean, memory):
    """A percentage of the amount the chat already holds: "and 20 percent of that"."""
    percents = re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)", clean)
    if len(percents) != 1:
        return None
    if re.search(r"\d", re.sub(r"\d+(?:\.\d+)?\s*(?:%|percent|per cent)", " ", clean)):
        return None  # the line carries an amount of its own, so this is another row's sum
    reference = re.search(r"\b(?:of|on)\s+(?:that|it|this|those|them|the\s+(?:rent|bill|"
                         r"price|salary|total|figure|number|amount|money))\b", clean)
    off_reference = re.search(r"\b(?:off)\s+(?:that|it|this|those|them)\b", clean)
    asked = (_PERCENT_ASK_WORD.search(clean)
             and re.search(r"\b(?:be|come\s+to|work\s+out\s+to)\b[\s?.!]*$", clean))
    if not (reference or off_reference or asked):
        return None
    amount = _amount_in_the_chat(memory)
    if amount is None:
        return None
    part = float(percents[0])
    if not 0 < part <= 100:
        return None
    change = amount * part / 100
    if off_reference:
        return (f"{_number(part)}% off {_number(amount)} leaves {_number(amount - change)} "
                f"(you save {_number(change)}).")
    return f"{_number(part)}% of {_number(amount)} is {_number(change)}."


# --- tips and saving goals ------------------------------------------------
def _tip(clean):
    """A tip on a bill: "15% tip on 45", "tip on 80 at 15 percent"."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)\s*(?:tip|service|gratuity)"
                      r"\s*(?:on(?:\s+top\s+of)?|for|of)\s*(?:(?:a|an|the|my|our)\s+)?"
                      r"(?:(?:bill|total|check|tab)\s+of\s+)?(?:£|\$|€)?\s*([\d,.]+)", clean)
    if match:
        part, total = _amount(match.group(1)), _amount(match.group(2))
    else:
        match = re.search(r"(?:tip|service|gratuity)\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*"
                          r"(?:%|percent|per cent)\s*(?:on|for|of)\s*(?:£|\$|€)?\s*([\d,.]+)",
                          clean)
        if match:
            part, total = _amount(match.group(1)), _amount(match.group(2))
        else:
            match = re.search(r"(?:tip|service|gratuity)\s*(?:on|for)\s*(?:£|\$|€)?\s*"
                              r"([\d,.]+)\s*(?:at|of)\s*(\d+(?:\.\d+)?)\s*"
                              r"(?:%|percent|per cent)", clean)
            if not match:
                return None
            total, part = _amount(match.group(1)), _amount(match.group(2))
    tip = total * part / 100
    return (f"A {_number(part)}% tip on {_number(total)} is {_number(tip)}, so "
            f"{_number(total + tip)} in total.")


# What somebody left on a bill, and whether it is enough: "we left 60 on a 48 bill" is a sum
# about the tip, and the laundry row read the 60 as a wash temperature and answered about towels.
_YOU_LEFT = re.compile(
    r"(?:left|leave|leaving|gave|give|put down|tipped|tip)\s+"
    r"(?:£|\$|€)?\s*(?P<left>\d[\d,]*(?:\.\d+)?|a tenner|a fiver|a twenty)\s*"
    r"(?:pounds?|quid|euros?|dollars?|bucks?)?\s*"
    r"(?:on|for|towards)\s+(?:a|an|the|our|my)?\s*(?:£|\$|€)?\s*"
    r"(?P<bill>\d[\d,]*(?:\.\d+)?)\s*(?:pounds?|quid|euros?|dollars?|bucks?)?\s*"
    r"(?P<what>bill|check|tab|meal|dinner|lunch|round)\b")
# The same sum with the bill word elsewhere: "i left 5 on 40 for the meal".
_YOU_LEFT_ANYWHERE = re.compile(
    r"(?:left|leave|leaving|gave|put down|tipped)\s+(?:£|\$|€)?\s*"
    r"(\d[\d,]*(?:\.\d+)?|a tenner|a fiver|a twenty)\s*"
    r"(?:pounds?|quid|euros?|dollars?|bucks?)?\s+"
    r"(?:on|for|towards)\s+(?:a|an|the|our|my)?\s*(?:£|\$|€)?\s*"
    r"(\d[\d,]*(?:\.\d+)?)")
_BILL_WORD = re.compile(r"\b(?:bill|tip|meal|dinner|lunch|check|tab|round|service)\b")
_A_NOTE = {"a tenner": 10, "a fiver": 5, "a twenty": 20}


def _two_places(value):
    """Money in a card's shape: 4.80 rather than 4.8, and 6 rather than 6.00."""
    text = f"{value:.2f}"
    return text[:-3] if text.endswith(".00") else text


def _left_on_the_bill(clean):
    """The percentage somebody left on a bill, and the usual tip on that bill."""
    match = _YOU_LEFT.search(clean)
    if match:
        left_text, bill_text = match.group("left"), match.group("bill")
    else:
        loose = _YOU_LEFT_ANYWHERE.search(clean)
        if not (loose and _BILL_WORD.search(clean)):
            return None
        left_text, bill_text = loose.group(1), loose.group(2)
    left = _A_NOTE.get(left_text) or _amount(left_text)
    bill = _amount(bill_text)
    if not left or not bill or left <= 0 or bill <= 0:
        return None
    percent = left / bill * 100
    money = next((sign for sign in ("£", "$", "€") if sign in clean), "£")
    usual = (f"{money}{_two_places(round(bill * 0.10, 2))} to "
             f"{money}{_two_places(round(bill * 0.125, 2))}")
    said = _number(round(percent, 1))
    if percent >= 10:
        return (f"That's {said}% of the {money}{_number(bill)} - the usual tip is ten to twelve "
                f"and a half ({usual}), so it's enough.")
    return (f"That's {said}% of the {money}{_number(bill)}, under the usual ten to twelve and a "
            f"half ({usual}). Check the bill for a service charge first, since that is the tip "
            f"already on it.")


def _save_time(clean):
    """How long a regular amount takes to reach a goal: "save 50 a month for 1000"."""
    if not re.search(r"how long|how many (?:months|weeks|years)|when will", clean):
        return None
    per = re.search(r"(?:save|saving|put away|putting away|set aside|setting aside)\s+"
                    r"(?:£|\$|€)?\s*([\d,.]+)\s*(?:a|per|each)\s*(month|week|year)", clean)
    goal = re.search(r"(?:to save|save up|reach|get to|hit|for)\s+(?:£|\$|€)?\s*([\d,.]+)",
                     clean)
    if not per or not goal:
        return None
    amount = _amount(per.group(1))
    total = _amount(goal.group(1))
    unit = per.group(2)
    if amount <= 0 or total <= 0:
        return None
    count = total / amount
    whole = int(count)
    if abs(count - whole) < 1e-9:
        length = f"{whole} {unit}{'' if whole == 1 else 's'}"
    else:
        length = f"about {_number(round(count, 1))} {unit}s"
    return f"Saving {_number(amount)} a {unit}, you get to {_number(total)} in {length}."


# --- speed, distance, time ------------------------------------------------

_PAY_WORDS = re.compile(r"\b(?:earn|earns|earning|wage|wages|salary|salaried|paid|pay|income|"
                        r"come to|comes to|coming to)\b")
_NOT_PAY = re.compile(r"\b(?:after tax|take home|take-home|national insurance|pension|"
                      r"student loan|miles? an hour|mph)\b")
_RATE = re.compile(r"(?:£|\$|€)?\s*(\d+(?:\.\d+)?)\s*"
                   r"(?:pounds?|quid|euros?|dollars?|bucks?)?\s*"
                   r"(?:an hour|a hour|per hour|hourly|/\s*hours?|/\s*hr|p/h)\b")
_HOURS_WEEK = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*"
                         r"(?:a|per|each|/)\s*(?:week|wk)\b")
_ANNUAL = re.compile(r"(?:£|\$|€)?\s*(\d+(?:[.,]\d+)?)\s*(k)?\s*"
                     r"(?:pounds?|quid|euros?|dollars?|bucks?)?\s*"
                     r"(?:a|per|/)?\s*(?:year|annum|yr)\b(?!\s+olds?\b)")
# The word that tells a yearly figure from a length of time: a currency, a unit, or the language
# of pay itself. Without one, "3 year" is an age and "5 years" is how long something has been
# going on, and neither is a salary: "is an hour of cartoons a day too much for a 3 year old" was
# read as 3 pounds a year and answered with "£3 a year at 40 hours a week is about £0 an hour
# before tax" instead of the screen-time advice.
_MONEY_BESIDE = re.compile(
    r"£|\$|€|\b(?:pounds?|quid|euros?|dollars?|bucks?|salary|salaried|wage|wages|income|"
    r"earn|earns|earning|paid|pay|annum|per annum|pa)\b", re.I)


def _money(clean, amount):
    """The amount with the currency the person used, so a dollar question stays in dollars."""
    if "€" in clean or "euro" in clean:
        sign = "€"
    elif "$" in clean or "dollar" in clean:
        sign = "$"
    else:
        sign = "£"
    text = f"{amount:,.2f}"
    if text.endswith(".00"):
        text = text[:-3]
    return f"{sign}{text}"


def _annual_pay(clean):
    """The yearly figure in the line, or None when the number is an age or a length of time.

    Every part of _ANNUAL is optional, which is what lets "30000 a year" and "30k a year" both
    read as a salary; the price is that a bare "3 year" reads as one too. So a figure with no
    currency, no unit, no "k" and fewer than four digits has to be carried by the language of pay
    somewhere in the line ("i earn 40 a year" is odd but it is a wage question; "my 3 year old"
    is not).
    """
    match = _ANNUAL.search(clean)
    if not match:
        return None
    if match.group(2):
        return match  # "30k"
    digits = re.sub(r"[.,]", "", match.group(1))
    if len(digits) >= 4:
        return match  # "30000"
    if _MONEY_BESIDE.search(clean):
        return match
    return None


def _wage(clean):
    """Pay worked out from an hourly rate, or an hourly rate from a yearly salary.

    The line has to be about pay: "120 miles at 60 miles an hour" is travel, not a wage.
    Hours default to 40 a week because that is the assumption most people mean, and it is
    said in the reply. Tax is deliberately left out: the answer is the gross figure, and a
    question that asks for take-home is passed on rather than answered with a guess.
    """
    if _NOT_PAY.search(clean):
        return None
    hours_match = _HOURS_WEEK.search(clean)
    hours = float(hours_match.group(1)) if hours_match else 40.0
    if hours <= 0 or hours > 100:
        return None
    rate = _RATE.search(clean)
    annual = _annual_pay(clean)
    # The "a week" in "37 hours a week" says how much they work, not that they want the
    # answer weekly, so it comes out before the asked-for period is read.
    asked = _HOURS_WEEK.sub(" ", clean)
    asks_year = re.search(r"\b(?:a|per|each|/)\s*(?:year|annum)|\bannual(?:ly)?\b", asked)
    asks_month = re.search(r"\b(?:a|per|each|/)\s*month|\bmonthly\b", asked)
    asks_week = re.search(r"\b(?:a|per|each|/)\s*week|\bweekly\b", asked)
    asks_hour = re.search(r"\b(?:an|a|per|each|/)\s*hour|\bhourly\b", asked)
    # A rate with a unit of time is a pay question even when the line never says earn or
    # wage: "12 pounds an hour a year" is the same ask as "I earn 12 an hour".
    if not (_PAY_WORDS.search(clean)
            or (rate and (hours_match or asks_year or asks_month or asks_week))
            or (annual and asks_hour)):
        return None
    if rate and not annual:
        hourly = float(rate.group(1))
        weekly = hourly * hours
        yearly = weekly * 52
        if asks_month and not asks_year:
            return (f"{_money(clean, hourly)} an hour at {_number(hours)} hours a week is "
                    f"about {_money(clean, yearly / 12)} a month before tax.")
        if asks_week and not (asks_year or asks_month):
            return (f"{_money(clean, hourly)} an hour at {_number(hours)} hours a week is "
                    f"{_money(clean, weekly)} a week.")
        if asks_year:
            return (f"{_money(clean, hourly)} an hour at {_number(hours)} hours a week is "
                    f"about {_money(clean, yearly)} a year before tax.")
        # A rate and a pay word are enough to be a wage question: "what do i earn at 12
        # pounds an hour" asks for the same sum as "how much do i earn at 12 an hour".
        if _PAY_WORDS.search(clean):
            return (f"{_money(clean, hourly)} an hour at {_number(hours)} hours a week is "
                    f"{_money(clean, weekly)} a week, about {_money(clean, yearly)} a year "
                    f"before tax.")
        if hours_match:
            return (f"{_money(clean, hourly)} an hour at {_number(hours)} hours a week is "
                    f"{_money(clean, weekly)} a week, about {_money(clean, yearly)} a year "
                    f"before tax.")
        return None
    if annual and (asks_hour or "hourly rate" in clean):
        value = float(annual.group(1).replace(",", ""))
        if annual.group(2):
            value *= 1000
        per_hour = value / (hours * 52)
        return (f"{_money(clean, value)} a year at {_number(hours)} hours a week is about "
                f"{_money(clean, per_hour)} an hour before tax.")
    if "hourly rate" in clean and ("salary" in clean or "annual" in clean) and not _parse(clean):
        return ("Divide your yearly salary by the hours you work in a year. At 40 hours a "
                "week that is 2,080 hours, so £30,000 is about £14.42 an hour.")
    return None


def _travel(clean):
    match = re.search(r"([\d,.]+)\s*(miles?|km|kilometres?|kilometers?)\b.*?"
                      r"(?:at|of)\s*([\d,.]+)\s*(?:miles?|km|kilometres?|kilometers?)?\s*"
                      r"(?:an hour|per hour|/hour|mph|kmh|km/h)", clean)
    if not match:
        return None
    distance = float(match.group(1).replace(",", ""))
    speed = float(match.group(3).replace(",", ""))
    if not speed:
        return None
    hours = distance / speed
    if hours < 1:
        return f"About {_number(hours * 60)} minutes at {_number(speed)} miles an hour."
    return f"About {_number(hours)} hours at {_number(speed)} miles an hour."


# A journey that names its distance and how it is made, but no speed, is the way people actually
# ask this: "how long does it take to walk three miles", "how long to cycle 3 miles", "how far can
# you walk in an hour". Walking pace, cycling pace and running pace are common knowledge, so the
# missing speed comes from the mode word and the line's own distance answers it.
_PACES = (
    (r"\bwalk(?:s|ed|ing)?\b|\bon foot\b|\bby foot\b|\bpedestrian\b", 3.0,
     "at walking pace", "20 minutes a mile", "on foot", "Allow a bit more for hills and a stop.",
     "A brisk one gets a little more, and hills and a bag take it back."),
    (r"\bcycl(?:e|es|ed|ing)\b|\bbikes?\b|\bbicycles?\b|\bpushbike\b|\bby bike\b", 12.0,
     "on a bike", "five minutes a mile", "on a bike",
     "Allow a bit more for hills and a stop.",
     "A good day with the wind behind you gets a little more."),
    (r"\brun(?:s|ning)?\b|\bjog(?:s|ging)?\b", 6.0,
     "at running pace", "10 minutes a mile", "running",
     "Allow a bit more for hills and a stop.",
     "A brisk one gets a little more, and hills take it back."),
    (r"\bdriv(?:e|es|ing)\b|\bby car\b|\bin the car\b|\bcar journey\b", 50.0,
     "in the car", "a bit over a minute a mile", "in the car",
     "Motorway miles are quicker, A roads and a town slower, so treat it as the middle.",
     "Motorway miles get you further, a town and its traffic get you less."),
)
# Any of the way-words in the pace table, for a line that carries only the distance and gets the
# way of doing it from the turn before.
_A_PACE_WORD = re.compile("|".join(pattern for pattern, *_ in _PACES))
_DISTANCE = re.compile(
    r"(?P<num>\d+(?:\.\d+)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|half)\s*(?P<unit>miles?|mile|km|kms|kilometres?|kilometers?|metres?|meters?)\b")
_AFTER_HALF = re.compile(r"\bhalf (?:a|an|one)\s*(?:mile|km|kilometre|kilometer)\b")


def _distance_in_miles(match, clean):
    """The distance in the line as miles. "half a mile" and "a mile and a half" are both said."""
    word = match.group("num")
    units = match.group("unit")
    if _AFTER_HALF.search(clean):
        value = 0.5
    elif word == "half":
        value = 0.5
    else:
        value = float(word) if word[0].isdigit() else float(_COUNTS.get(word, 0))
    if re.search(r"\band a half\b", clean):
        value += 0.5
    if units.startswith(("km", "kilomet")):
        return value * 0.621371
    if units.startswith("met"):
        return value / 1609.34
    return value


def _duration(hours):
    """An hour and a bit the way a person says it: 75 minutes, or two hours 15 minutes."""
    minutes = int(round(hours * 60))
    if minutes < 60:
        return f"{minutes} minutes"
    hours_, mins = divmod(minutes, 60)
    if mins <= 2:
        return "an hour" if hours_ == 1 else f"{hours_} hours"
    if mins >= 58:
        hours_ += 1
        return "an hour" if hours_ == 1 else f"{hours_} hours"
    hour_word = "an hour" if hours_ == 1 else f"{hours_} hours"
    return f"{hour_word} {mins} minutes"


# A distance to work said on its own names no way of getting there, and it is the one place where
# the way is not in doubt enough to ask: "its 4 miles each way to the office" is a car or a bike
# for most people, and the two figures side by side are what says which is worth it.
_TO_WORK = re.compile(r"\b(?:to work|to the office|to my office|to the job|commute|commuting|"
                      r"into work|to the workplace)\b")
# A distance stated rather than asked about, in a chat that is already about getting somewhere
# under your own steam: "its about 4 miles each way" after the cycling-to-work answer. The line
# asks nothing on its own, but the minutes are what decide whether the number is a lot, and
# saying them keeps the journey and its length in one place instead of leaving the next line with
# nothing to stand on. Only the shape below counts: a count of miles and at most a few words
# around it, with no verb of its own.
_A_DISTANCE_STATED = re.compile(
    r"^(?:(?:and|but|so|well|ok|okay|its|it'?s|it is|thats|that is|about|roughly|around|"
    r"approximately|maybe|probably|just|only)\s+){0,5}"
    r"(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|half|\d+(?:\.\d+)?)"
    r"(?:\s+and a half)?\s*(?:miles?|km|kms|kilometres?|kilometers?)\b[^.?!]{0,26}$")


# "is that too far" straight after a distance said out loud asks for the verdict on it, and the
# number it is about is in the turn before: the minutes are the whole answer, so they are said
# again with the verdict on them.
_IS_THAT_TOO_MUCH = re.compile(
    r"\bis (?:that|this|it) (?:too far|too much|too long|a lot|alright|ok|okay|doable)\b|"
    r"\b(?:is|would) that be (?:too far|too much|a lot)\b")


def _the_size_of_the_trip(minutes_there_and_back):
    """What a friend says about a trip of that length - the verdict, not the arithmetic."""
    if minutes_there_and_back <= 45:
        return "That is a short trip - easy to do every day."
    if minutes_there_and_back <= 100:
        return "That is a real part of the day, but plenty of people do it."
    return "That is a long way to do every day - fine now and then, hard as a routine."


def _the_way_it_is_done(memory, back=4):
    """What the person said on the last few turns, newest first: the way they mean to travel.

    Only the person's own lines count. The bot's answer names every way it can think of - the
    running plan says "one minute of easy jogging, two minutes of walking" - and a distance said
    after it would be timed at the bot's walking pace rather than the running the person asked
    about. Newest first, because the last way named is the one the chat is on.
    """
    said = []
    for turn in reversed(((memory or {}).get("turns") or [])[-back:]):
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or ""))
    return said


def _at_a_pace(clean, memory=None, a_verdict=False):
    """How long a walk, a ride or a run takes when the line gives the distance, not the speed."""
    asked_time = re.search(r"\bhow long\b|\bhow many (?:minutes|hours)\b|\bhow much longer\b",
                           clean)
    asked_far = re.search(r"\bhow far\b", clean)
    # A distance said on its own, in a chat already about a way of getting there: the way is in
    # this line ("4 miles each way on the bike") or in the turn before it (the ride to work).
    stated = bool(_A_DISTANCE_STATED.match(clean)) and bool(
        re.search(_A_PACE_WORD, clean + " " + " ".join(_the_way_it_is_done(memory)))
        or _TO_WORK.search(clean))
    if not (asked_time or asked_far or stated):
        # "is that too far" about a distance said last turn: the number is the answer, so it is
        # read back out of the chat and the verdict is put on it.
        if _IS_THAT_TOO_MUCH.search(clean):
            said_before = _the_way_it_is_done(memory)
            for line in said_before:
                if _A_DISTANCE_STATED.match(line.strip()):
                    # the way of getting there came from the chat, so it is read from there too
                    return _at_a_pace(line.strip(), memory, a_verdict=True)
        return None
    pace = None
    for pattern, speed, said, per_mile, far_said, tail, far_tail in _PACES:
        if re.search(pattern, clean):
            pace = (speed, said, per_mile, far_said, tail, far_tail)
            break
    if not pace and stated and _TO_WORK.search(clean):
        # the trip to work, with no way of getting there named: the two ways most people take it
        match = _DISTANCE.search(clean)
        miles = _distance_in_miles(match, clean) if match else 0
        if miles and miles > 0:
            each_way = bool(re.search(r"\beach way\b|\bboth ways\b", clean))
            car = miles / 50.0 * 60
            bike = miles / 12.0 * 60
            if each_way:
                return (f"About {_duration(car / 60)} in the car and {_duration(bike / 60)} on a "
                        f"bike, each way - so around {_duration(2 * car / 60)} to "
                        f"{_duration(2 * bike / 60)} there and back. "
                        + (_the_size_of_the_trip(2 * car) if a_verdict
                           else "A ride that short is well within reach, and it is the cheaper "
                                "of the two."))
            return (f"About {_duration(car / 60)} in the car and {_duration(bike / 60)} on a bike "
                    f"- the ride is the one that saves the money at that distance.")
    if not pace and stated:
        # the way of getting there is in what was said before, newest turn first
        for line in _the_way_it_is_done(memory):
            for pattern, speed, said, per_mile, far_said, tail, far_tail in _PACES:
                if re.search(pattern, line):
                    pace = (speed, said, per_mile, far_said, tail, far_tail)
                    break
            if pace:
                break
    if not pace:
        return None
    speed, said, per_mile, far_said, tail, far_tail = pace
    match = _DISTANCE.search(clean)
    if match:
        miles = _distance_in_miles(match, clean)
        if not miles or miles <= 0:
            return None
        minutes = miles / speed * 60
        if asked_far and not asked_time:
            return None
        if stated:
            # "its about 4 miles each way" is half of a day's travel each way, so the round trip
            # is the figure that decides whether the number is a lot - and it is what the person
            # is telling the bot they have taken on.
            if re.search(r"\beach way\b|\bboth ways\b", clean):
                tail_said = (" " + _the_size_of_the_trip(2 * minutes) if a_verdict else "")
                return (f"About {_duration(minutes / 60)} {said}, so roughly "
                        f"{_duration(2 * minutes / 60)} there and back - {speed:g} miles an hour, "
                        f"so {per_mile}.{tail_said}")
            return (f"About {_duration(minutes / 60)} {said} - {speed:g} miles an hour, so "
                    f"{per_mile}. {tail}")
        return (f"About {_duration(miles / speed)} {said} - {speed:g} miles an hour, so "
                f"{per_mile}. {tail}")
    # "how far can you walk in an hour" is the same pace asked the other way round: the hour is
    # the distance, so the answer is the miles that fit in it.
    hour = re.search(r"\b(?:in|within|for)\s+(?:an?|one|1)\s+hour\b|\ban hour\b", clean)
    if hour and asked_far:
        return (f"About {speed:g} miles in an hour {far_said} - {per_mile}. {far_tail}")
    return None


# --- unit conversions -----------------------------------------------------

def _convert(clean, memory=None):
    """A unit conversion, from the one table of units (bot/knowledge/units.py).

    A plain pair of units may already have a hand-written fact in _unit_fact() with a
    second useful measure in it ("16 ounces in a pound, and 14 pounds in a stone"), and
    that wording is kept. Everything else - a named food's cups and grams, an oven heat,
    every pair nobody wrote a fact for - comes from the table.
    """
    fact = _unit_fact(clean)
    table = units.convert(clean, memory)
    if fact and not units.answers_more_than_a_pair(clean):
        return fact
    return table or fact


# --- numbers the chat already holds ---------------------------------------

# A line like "how long will that take?" carries no numbers of its own: the numbers were in
# earlier turns ("hoping to spend about 5000", "i can put away 250 a month"). Those two add up to
# a real answer, so this reads the chat the way a friend would.
TIME_ASKED = re.compile(
    r"\bhow long\b|\bhow many (?:months|weeks|years|fortnights)\b|\bhow soon\b|"
    r"\bwhen (?:will|would|should|do|can|am) (?:i|we)\b|\bwhen do i\b")
# The times of day, cooking and travel are answered from entries or from the line's own numbers.
# "what if we do 700?" right after the bot said how long it takes: the question is implied.
# "what about 300 a week?" and "how about 400?" ask the same thing, as long as the line is about
# money and not about a time of day ("how about 2 o'clock").
WHAT_IF = re.compile(r"\bwhat if (?:i|we)\b|\band if (?:i|we)\b")
ABOUT_ASK = re.compile(r"\b(?:what|how) about\b")
CLOCK = re.compile(r"\bo'?\s?clock\b|\b\d{1,2}\s*(?:am|pm)\b|"
                   r"\b(?:morning|afternoon|evening|tonight|tuesday|wednesday|thursday|friday|"
                   r"saturday|sunday|monday)\b")
# The bot's own sentence, hedge included: a count that is not whole comes back as
# "takes about 12 months", and the turn after that still has to be able to read it.
TAKES = re.compile(r"takes (?:about |roughly |around )?(?P<amount>[\d,.]+) "
                   r"(?P<period>days?|weeks?|fortnights?|months?|years?)\b")
# A number with a period after it and no "a" or "per" between them is a deadline the person
# named ("in 18 months", "in two years"), not a rate: "18 months" is not "18 a month".
A_HORIZON = re.compile(r"\b(?:in|within|by|after)\s+(?:\d+|an?|[a-z-]+)\s+"
                       r"(?:days?|weeks?|fortnights?|months?|years?)\b|"
                       r"\b\d+\s*(?:months?|years?|weeks?)\s+(?:from now|time)\b")
TIME_ELSEWHERE = re.compile(
    r"\b(?:cook|roast|boil|bake|fry|grill|simmer|rest|leave|marinate|drive|walk|fly|cycle|"
    r"ride|run|swim|wait|queue|charge|download|install)\b")
# A figure with a period on it. The saving verb often sits between the two words - "i put 20 by
# every week", "i put 50 aside each month", "putting 100 away a week" - and the phrase
# "20 by every week" matched nothing, so the whole chat below (how long until i can buy it) had
# no rate to work with and punted.
RATE = re.compile(r"(?P<amount>\d[\d,]*(?:\.\d+)?)\s*"
                  r"(?:pounds?|quid|euros?|dollars?|grand|k\b)?\s*"
                  r"(?:(?:by|aside|away|back|to (?:one|the) side)\s+)?"
                  r"(?:a|an|per|each|every|/)\s*(?P<period>day|week|fortnight|month|year)\b")
MONEY = re.compile(r"\b(?:save|saves|saving|saved|spend|spends|spending|cost|costs|afford|"
                   r"budget|need|needs|want|wants|goal|target|total|price|deposit|pay|paying|"
                   r"put away|putting away|put by|putting by|earn|earning|owe|owing)\b")
# The money has to be going towards the thing, not just leaving the account every month: rent and
# bills are not savings, so "my rent is 800 a month" never becomes the rate for a car fund.
TOWARDS = re.compile(r"\b(?:save|saves|saving|saved|put away|putting away|put by|putting by|"
                     r"set aside|setting aside|towards|toward|pay off|paying off|paid off|"
                     r"pay towards|paying towards|pay down|paying down|pay back|paying back|"
                     r"afford|spare|extra|repay|repaying|return)\b")
# ...and the direction has to be in the same clause as the rate itself. "i spend 100 a month on
# coffee" and "i pay 800 a month rent" both have a monthly figure and a saving word later in the
# line, and neither of them is money being put by.
CLAUSE_SPLIT = re.compile(r"[,;.]|\band\b|\bbut\b|\bthen\b|\bso\b")
SAVING_CLAUSE = re.compile(
    r"\b(?:save|saves|saving|saved|savings|put|puts|putting|put away|putting away|put by|"
    r"putting aside|set aside|setting aside|stash|stashing|squirrel|towards|toward|into|"
    r"pay off|paying off|paid off|pay towards|paying towards|paid towards|pay down|paying down|"
    r"pay back|paying back|paid back|overpay|overpaying|give|gives|giving|gave|send|sends|"
    r"sending|transfer|transfers|transferred|repay|repays|repaying|return|returning)\b")
SPENDING_CLAUSE = re.compile(
    r"\b(?:spend|spends|spending|spent|cost|costs|costing|rent|bills?|charges?|wage|wages|"
    r"salary|earn|earns|earning|lose|losing|lost|burn|burns|burning|waste|wasting)\b")
# Money the person is carrying, not money they are putting by: "theres 4000 left on a loan", "i
# owe 3000 on the card", "my overdraft is 1200". A saving chat often holds both figures - what they
# are saving towards and what they already owe - and the debt is usually the bigger of the two, so
# read as a pot it answered "how long will that take" with the loan paid off at the saving rate
# (4,000 at 150 a month is 27 months) and never reached the car they had just priced.
OWED = re.compile(r"\b(?:owe|owes|owed|owing|debt|debts|loan|loans|overdraft|mortgage|"
                  r"finance|financed|borrow|borrowed|borrowing|credit\s*card|left\s+on)\b", re.I)
# The same sum said as the thing they are clearing is a goal: "i owe 3000 on the card and want it
# gone", "how long to pay off 3000". Reads the money going the other way.
A_DEBT_CLEARED = re.compile(r"\b(?:pay(?:ing)?\s+(?:it\s+|them\s+)?off|clear(?:ing)?|"
                            r"repay(?:ing)?|gone|off|rid)\b", re.I)


def _rate_clause(line, match):
    """The part of the line the rate sits in, so its direction can be read on its own."""
    start = 0
    for part in CLAUSE_SPLIT.split(line):
        end = start + len(part)
        if start <= match.start() and match.end() <= end + 1:
            return part
        start = end + 1
    return line
# how many months one of each period is, for the "about a year and eight months" aside
PERIODS = {"day": 1 / 30.44, "week": 1 / 4.345, "fortnight": 1 / 2.17, "month": 1, "year": 12}


def _user_lines(memory, back=8):
    """What the user said on the last few turns, oldest first."""
    lines = []
    for turn in (memory.get("turns") or [])[-back:]:
        if not isinstance(turn, dict):
            continue
        text = turn.get("user")
        if isinstance(text, str) and text.strip():
            lines.append(" ".join(text.lower().split()))
    return lines


def _a_rate_was_said(lines):
    """True when one of these lines puts money by at a rate ("put away 250 a month")."""
    for line in lines:
        for match in RATE.finditer(line):
            clause = _rate_clause(line, match)
            if SAVING_CLAUSE.search(clause) and not SPENDING_CLAUSE.search(clause):
                return True
    return False


def _rate_in_chat(memory):
    """The most recent rate per period in the chat, when the money is going towards something.

    A rate put right counts as the most recent one. "i can put away 250 a month" and then
    "actually i can do 300 now ive paid the car off" is one rate written twice, and the second
    line has no "a month" on it because the month never changed - so it matched nothing here, and
    the length of the saving was worked out at the rate the person had already left behind.
    """
    lines = _user_lines(memory)
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index]
        put_right = a_rate_put_right(line, lines[index - 1] if index else "")
        if put_right and _a_rate_was_said(lines[:index]):
            return float(put_right), "month"
        for match in RATE.finditer(line):
            clause = _rate_clause(line, match)
            if not SAVING_CLAUSE.search(clause) or SPENDING_CLAUSE.search(clause):
                continue
            amount = float(match.group("amount").replace(",", ""))
            if amount > 0:
                return amount, match.group("period")
    return None, None


# A figure with a period on it is a rate, not a pot: "i want to save 200 a month" names no goal at
# all. Read as one it became the total behind the next question - "what would that get me in a
# year" answered "200 in a year is 17 a month", which is the rate divided out as if it were a sum
# to be reached. The rate is taken out before the figures of the line are read, so a line that
# names both keeps its goal: "i want to save 200 a month towards 3000" still has the 3000.
SAID_A_RATE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*(?:k|grand|thousand)?\s*(?:pounds?\s+)?"
                         r"(?:a|per|each|every|/)\s*(?:month|week|fortnight|year|day)\b", re.I)
# A reply that divided a total by a rate and said how long it takes: "£20,000 at £200 a month is
# 100 months, about 8 years and 4 months". The total and the rate are both in it.
# The count is part of the division and not just the verb: a reply that says what a rate comes to
# in a month ("£1,400 at £1,800 a month is a single month at that rate") did no division at all,
# and reading its figure as the total made a spend into a goal - "how much could i put away each
# month" answered "£1,400 by next summer ... about £184 a month". So a figure has to follow the
# verb that says the sum is worked.
WORKED = re.compile(
    r"£([\d,]+)\s+at\s+£?[\d,.]+\s*(?:a|per|each)\s+(?:month|week|fortnight|year)s?\s+"
    r"(?:is|takes|gives|comes to)\s+(?:about\s+|around\s+|roughly\s+)?\d"
    r"|\bat\s+£?[\d,.]+\s*(?:a|per|each)\s+(?:month|week|fortnight|year)s?\s*,\s*"
    r"(?:about\s+)?£?([\d,]+)\s+takes\s+(?:about\s+|around\s+|roughly\s+)?\d",
    re.IGNORECASE)


def _worked_in_chat(memory, rate=None):
    """The total this chat has already worked a time for, read from the bot's own answer.

    "we can put away 400 a month" is answered "£20,000 at £400 a month is 50 months", so the
    "how long would that take" that follows is a question about the 20,000 the chat itself
    divided - and a total named beside a rate is the plan's own figure, not an example or an
    aim. Only a reply that did the division counts: the one before it says what to aim for and
    no rate, so its figure is never taken as the plan.
    """
    total = None
    for turn in (memory.get("turns") or [])[-8:]:
        if not isinstance(turn, dict):
            continue
        text = turn.get("bot")
        if not isinstance(text, str):
            continue
        for found in WORKED.findall(" ".join(text.split())):
            raw = next((part for part in found if part), "")
            try:
                value = int(raw.replace(",", ""))
            except ValueError:
                continue
            if rate and value < rate * 2:
                continue
            if value >= 50:
                total = value
    return total


# A sum said the way people say sums: "20 grand", "twenty thousand", "20k". `_parse` reads the
# digits of a line and nothing else, so "i need 20 grand" came back as twenty pounds - under the
# fifty a goal has to clear - and the chat that had both the target and the rate was asked for the
# target again: "i need 20 grand" / "im putting away 400 a month" / "how long will that take me"
# was answered "At 400 a month that's about 4,800 a year. Tell me the figure you are saving
# towards", one turn after the same entry had worked with the £20,000 it can no longer see.
# Only the words that are always money scale the figure: a bare "5k" is a run, so a k needs a
# money word on the same line before it counts as thousands.
_TENS_WORDS = {"ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
               "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
               "eighty": 80, "ninety": 90}
_WORD_THOUSANDS = re.compile(r"\b(" + "|".join(_TENS_WORDS) + r")\s+(?:grand|thousand)\b", re.I)
_NUMBER_THOUSANDS = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:grand|thousand)\b", re.I)
_K_THOUSANDS_HERE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*k\b", re.I)
_MONEY_HERE = re.compile(r"£|\bpounds?\b|\bquid\b|\beuros?\b|\bdollars?\b|\bsav(?:e|ing|ings)\b|"
                         r"\bcost(?:s|ing)?\b|\bpay(?:ing|s|day)?\b|\bmoney\b|\bbudget\b|"
                         r"\bprice\b|\bafford\b|\bdeposit\b|\bspen[dt]\b|\bowe[sd]?\b", re.I)


def _sums(text):
    """The sums in a line, with a scale word read as thousands: "20 grand" is 20,000."""
    text = str(text or "")
    text = _WORD_THOUSANDS.sub(lambda m: str(_TENS_WORDS[m.group(1).lower()] * 1000), text)
    text = _NUMBER_THOUSANDS.sub(lambda m: str(int(float(m.group(1)) * 1000)), text)
    if _MONEY_HERE.search(text):
        text = _K_THOUSANDS_HERE.sub(lambda m: str(int(float(m.group(1)) * 1000)), text)
    return _parse(text)


def _goal_in_chat(memory, rate=None):
    """The biggest figure earlier in the chat that is a goal rather than a bill or a wage."""
    lines = _user_lines(memory)
    total = None
    # What the money is for can be said on a different line from the sum: "im trying to save up
    # for a car" / "i can put by 150 a month" / "the car is 2500". A reader that wanted a goal
    # word on the same line as the figure answered "how long will that take" by asking for the
    # figure again - the one the person had just given two turns earlier - so a plain sum in a
    # chat that already named a goal and a rate is the total being saved towards.
    a_goal_is_named = rate is not None and any(GOAL.search(line) for line in lines)
    owed = None
    for line in lines:
        if not GOAL.search(line) and not a_goal_is_named:
            continue
        if not GOAL.search(line) and SPENDING_CLAUSE.search(line):
            continue  # a bill or a wage, not what is being saved towards
        if the_pot_said_alone(line):
            # Money already in the pot is not the total being saved towards. A chat that said
            # "we need 8000 for a new kitchen" and then "weve got 3000 in savings" was told
            # "£3,000 at £250 a month is 12 months": the pot was read as the goal, and the
            # length it gave was for the money they already hold.
            continue
        if OWED.search(line) and not A_DEBT_CLEARED.search(line):
            # Money they are carrying, kept aside until nothing better is named: a chat about a
            # car that also mentions a loan saves towards the car.
            for value in _sums(SAID_A_RATE.sub(" ", line)):
                if rate and value < rate * 2:
                    continue
                if value >= 50 and (owed is None or value > owed):
                    owed = value
            continue
        for value in _sums(SAID_A_RATE.sub(" ", line)):
            # a total the rate has to work through is worth many of its payments
            if rate and value < rate * 2:
                continue
            if value >= 50 and (total is None or value > total):
                total = value
    if total is None:
        # "we can put away 400 a month" was answered "£20,000 at £400 a month is 50 months", so the
        # "how long would that take" after it is about the 20,000 the chat has already divided.
        total = _worked_in_chat(memory, rate)
    return total if total is not None else owed


def _rate_and_total(memory):
    """A rate per period and a total to reach, both stated in the chat, or (None, None, None)."""
    rate, period = _rate_in_chat(memory)
    if rate is None:
        return None, None, None
    total = _goal_in_chat(memory, rate)
    held = the_money_already_held(memory)
    if total and 0 < held < total:
        # The pot is not the goal: "im saving for a 15000 deposit" / "i have 4200 saved" /
        # "i put by 400 a month" / "when will i have enough" was answered "at 400 a month, 15,000
        # takes about 38 months", while the answer two turns earlier had worked out "£10,800
        # still to find ... 22 months". The chat had the figure and the arithmetic both, and the
        # last turn gave back the whole goal. What is still to find is the goal less the pot, the
        # same sum `bot/memory/saving.py` works out.
        total = total - held
    return rate, period, total


def _in_months(count, period):
    """A count of one period said in months, for the parenthesis in the reply."""
    return count * PERIODS[period]


def _duration_reply(rate, period, total):
    """The sentence for "X a month for Y": the count, and how long that is in years."""
    count = total / rate
    if count < 1 or count > 1200:
        return None  # not a sum anyone asks about, or not a rate at all
    # A part payment is another payment, which is the rule the rate card itself follows ("£900
    # at £200 a month is 5 months" - saving.py works the count out with a ceiling), so a half is
    # never rounded down here: the same chat said "5 months" and then, on the next line, "about 4
    # months" for the same rate and the same goal.
    nearest = int(count + 0.5)
    if abs(count - nearest) < 0.05:
        said_count, about = _number(nearest), ""
    else:
        said_count, about = _number(round(count, 1) if count < 3 else nearest), "about "
    name = period if count == 1 else period + "s"
    reply = f"At {_number(rate)} a {period}, {_number(total)} takes {about}{said_count} {name}"
    months = _in_months(count, period)
    if period != "year" and months >= 12:
        years, rest = divmod(int(round(months)), 12)
        said = f"{years} year" + ("" if years == 1 else "s")
        if rest:
            said += f" and {rest} month" + ("" if rest == 1 else "s")
        # the aside gets "about" only when it is not the exact count itself
        loose = "about " if about or abs(months - round(months)) >= 0.05 else ""
        reply += f" ({loose}{said})"
    return reply + "."


def _time_to_reach(clean, memory):
    """How long it takes to reach a total at a rate, when the chat said both and the line asks."""
    if not TIME_ASKED.search(clean) or TIME_ELSEWHERE.search(clean):
        return None
    if _parse(clean):
        return None  # the line brings its own numbers: the other forms answer those
    rate, period, total = _rate_and_total(memory)
    if not rate or not total:
        return None
    return _duration_reply(rate, period, total)


def _asks_a_new_sum(clean):
    """A line that proposes its own numbers for the sum the chat already holds."""
    if WHAT_IF.search(clean):
        return True
    return bool(ABOUT_ASK.search(clean)) and not CLOCK.search(clean)


def _last_takes(memory):
    """The rate and period the bot worked out on the turn before, when it worked one out."""
    turns = memory.get("turns") or []
    if not turns or not isinstance(turns[-1], dict):
        return None
    found = TAKES.search(turns[-1].get("bot") or "")
    if not found:
        return None
    return float(found.group("amount").replace(",", "")), found.group("period").rstrip("s")


def _time_at_a_new_rate(clean, memory):
    """A rate the line itself proposes for the same total: "what if we do 700?"

    The question is implied, the way people ask it straight after an answer: the chat holds the
    total, the bot has just said how long it takes, and this line changes the rate.
    """
    if not _asks_a_new_sum(clean) or TIME_ELSEWHERE.search(clean):
        return None
    before = _last_takes(memory)
    if before is None:
        return None
    rate, period, total = _rate_and_total(memory)
    if not total:
        return None
    match = RATE.search(clean)
    numbers = _parse(clean)
    if match:
        rate, period = float(match.group("amount").replace(",", "")), match.group("period")
    elif len(numbers) == 1 and numbers[0] < total:
        if A_HORIZON.search(clean):
            return None  # "what if we want it done in 18 months" is a deadline, not a rate
        rate, period = numbers[0], before[1]
    else:
        return None  # a number bigger than the total is a different total, not a rate
    if not rate or not period:
        return None
    return _duration_reply(rate, period, total)


def _time_at_a_new_total(clean, memory):
    """A bigger price for the same saving rate: "and what if i find one for 6000, is that daft?"

    Same shape as the rate change, the other way round: the person keeps the money they can put
    away and asks about a dearer thing, which is a question about how much longer it takes.
    """
    if not _asks_a_new_sum(clean) or TIME_ELSEWHERE.search(clean):
        return None
    before = _last_takes(memory)
    if before is None:
        return None
    rate, period, total = _rate_and_total(memory)
    if not rate or not total:
        return None
    numbers = _parse(clean)
    if len(numbers) != 1 or numbers[0] <= total:
        return None
    dearer = numbers[0]
    count = dearer / rate
    old = total / rate
    nearest = round(count)
    said = _number(nearest if abs(count - nearest) < 0.05 else round(count, 1))
    name = period if count == 1 else period + "s"
    extra = round(count - old)
    more = f", so {_number(extra)} {name} more than {_number(total)}" if extra >= 1 else ""
    return (f"At {_number(rate)} a {period}, {_number(dearer)} takes {said} {name}{more}. "
            f"Only you know if the dearer one is worth the wait.")

def _time_without_a_goal(clean, memory):
    """A rate without a figure to reach yet: "how long would that take?"

    There is nothing to divide, so the answer says what the rate comes to in a year, what one
    hundred of the price costs in weeks at that rate, and asks for the one number that is missing.
    Better than a shrug, and it is the question they will ask next: "i put 20 by every week
    towards a bike" then "so how many weeks until i can buy it" was a search hedge, when 20 a
    week is five weeks for every 100 of the bike.
    """
    if not TIME_ASKED.search(clean) or TIME_ELSEWHERE.search(clean) or _parse(clean):
        return None
    rate, period = _rate_in_chat(memory)
    if not rate:
        return None
    if _goal_in_chat(memory, rate):
        return None  # there is a figure to reach, so _time_to_reach answers this
    yearly = rate * 12 / PERIODS[period]
    said = f"At {_number(rate)} a {period} that's about {_number(round(yearly))} a year"
    each_hundred = _each_hundred(rate, period)
    if each_hundred:
        said += f", so every 100 of the price takes {each_hundred}"
    return (said + ". Tell me the figure you are saving towards and I will work out how long "
            "it takes.")


# The next unit down and how many of it make one of the larger: a hundred of the price at 300 a
# month is a third of a month, which nobody says, and "eight days" is the same figure said plainly.
_SMALLER_PERIOD = {"year": ("month", 12), "month": ("week", 4.345), "fortnight": ("week", 2),
                   "week": ("day", 7), "day": ("hour", 24)}


def _each_hundred(rate, period):
    """How long 100 of the price takes at a rate: "five weeks", "eight days", "2.5 months".

    The figure that makes an empty sum useful without inventing a price: it is the rate read the
    other way round, and a price can then be done in the head in steps of one hundred. The unit
    follows the count down, so a rate of 300 a month answers in days rather than in "a third of a
    month", and the count is rounded to the half that a person would say.
    """
    if not rate or rate <= 0:
        return None
    count = 100.0 / rate
    while count < 1 and period in _SMALLER_PERIOD:
        period, many = _SMALLER_PERIOD[period]
        count *= many
    if count < 1:
        return None  # 100 of the price in under an hour is not a rate anyone is saving at
    while count >= 13 and period in ("day", "week", "fortnight"):
        period, many = _SMALLER_PERIOD[period]
        count /= many
    if period == "hour" and count >= 12:
        return None  # the yearly figure above says this better than hours do
    if count < 3:
        value = round(count * 2) / 2
        said = _number(int(value) if value == int(value) else value)
    else:
        value = round(count)
        said = _number(int(value))
        if abs(count - value) >= 0.5:
            said = f"about {said}"
    name = period if abs(value - 1) < 0.05 else period + "s"
    return f"{said} {name}"


# The figure has to be money being put by, not any number with a goal word beside it. "i want to
# run 100 miles" / "how long will it take" was answered "Getting to 100 depends on what you can put
# by", because GOAL counts "want" and the plan is a figure like any other.
MONEY_GOAL = re.compile(
    r"\b(?:save|saves|saving|saved|put by|put aside|set aside|put away|deposit|afford|owe|owes|"
    r"owed|debt|debts|repay|repaying|pay off|paying off|towards|toward)\b")


def _a_saving_goal_in_chat(memory):
    """The biggest figure on a line that says money is being put by."""
    best = None
    for line in _user_lines(memory):
        if not MONEY_GOAL.search(line) or SPENDING_CLAUSE.search(line):
            continue
        for value in _sums(SAID_A_RATE.sub(" ", line)):
            if value >= 50 and (best is None or value > best):
                best = value
    return best


def _the_plan_figure(memory):
    """The figure the **newest** plan names, if that plan is about money.

    "im trying to save 2000 for a used car" then "actually its 3000" leaves the plan reading
    "Save 3000 for a used car" (bot/memory/topics.py writes the correction), while the old sum is
    still on the first line of the chat. Reading the lines alone answered a later ask with 2,000.

    Only the newest plan, because a later plan is a new subject: "i want to run 100 miles" after the
    car leaves the store holding both, and the goal in hand is the run. A plan with no money word in
    it is not money at all, so this is also the fence that keeps 100 miles from being read as £100.
    """
    user = memory.get("user") or {}
    if not isinstance(user, dict):
        return None
    plans = [plan for plan in list(user.get("plans") or []) if plan]
    newest = plans[-1] if plans else user.get("plan")
    if not newest or not MONEY_GOAL.search(str(newest).lower()):
        return None
    sums = [value for value in _sums(str(newest)) if value >= 50]
    return max(sums) if sums else None


# The fallback when the sums at the rates people save at have already been said: the missing half
# of the sum is the rate, so that is what is asked for. Kept as words of its own so a test can hold
# on to it.
ASKED_FOR_RATE = "how much could you set aside each month?"


def _a_goal_without_a_rate(clean, memory):
    """A figure to reach but no rate to reach it at: "im trying to save 2000 for a used car" then
    "how long will it take".

    _time_without_a_goal is the same sum the other way round: with a rate and no figure, the answer
    says what the rate comes to in a year and asks for the figure. With a figure and no rate there
    is nothing to divide either, and the missing half is the one a friend asks for. Nothing said it,
    so the question was answered from the card for the thing being saved for - "ask how long they've
    owned it and why they're selling" - which is a question to put to a stranger about the car,
    not an answer about time.
    """
    if not TIME_ASKED.search(clean) or TIME_ELSEWHERE.search(clean) or _parse(clean):
        return None
    rate, _period = _rate_in_chat(memory)
    if rate:
        return None  # both halves are in the chat, so _time_to_reach divides them
    total = _the_plan_figure(memory)
    if total is None:
        user = memory.get("user") or {}
        if isinstance(user, dict) and (user.get("plan") or user.get("plans")):
            return None  # the plan in hand is not money, so this is a new subject
        total = _a_saving_goal_in_chat(memory)
    if not total:
        return None
    # The sums at the rates people save at are the answer money.py already gives a line that names
    # its own goal ("i need a deposit of 15000" / "how long will that take"), and it gives the same
    # one for a goal the chat named a turn earlier when the entry that carries it is reached. This
    # is the door for the bare follow-up, so the wording is theirs, not a second table.
    from .money import _time_to_save
    return (_time_to_save(memory, {"clean": clean, "text": clean})
            or f"Getting to {_number(total)} depends on what you can put by - {ASKED_FOR_RATE}")


# the exact words _time_without_a_goal uses, so the figure it asked for can be answered next turn
ASKED_FOR_FIGURE = "the figure you are saving towards"

# A line that does nothing but put a new total into the plan: "say i need 12000", "make it 15000".
# The words before the figure are the ones people say when they swap a number, and nothing else
# in the line, so the reply can only be about that number.
JUST_A_TOTAL = re.compile(
    r"^\s*(?:no[, ]+|actually[, ]+|okay[, ]+|ok[, ]+|well[, ]+)?"
    r"(?:say|lets say|let's say|make it|make that|call it|change it to|put it at)\s+"
    r"(?:i|we)?\s*(?:need|needs|want|wants)?\s*(?:about\s+|around\s+)?"
    r"£?([\d,.]+)\s*(k|thousand|pounds?|quid)?\s*[.!]*\s*$")


def _a_new_total_only(clean):
    """True when the whole line is a swap of the total: "say i need 12000"."""
    return bool(JUST_A_TOTAL.search((clean or "").strip()))


def _figure_just_given(clean, memory):
    """The total, given on the next line: "say i need 12000".

    _time_without_a_goal asked for one number, and when it arrives the question it stood in for
    ("how long will that take") is answered now that both numbers are in the chat. A chat that
    worked a time for its own total ("£20,000 at £200 a month is 100 months, about 8 years and
    4 months") is the same case without the asking: "say i need 12000" is that question again
    about 12,000, and asking for a figure the chat is already holding would be the worse answer.
    """
    turns = memory.get("turns") or []
    if not turns or not isinstance(turns[-1], dict):
        return None
    if TIME_ELSEWHERE.search(clean):
        return None
    said = turns[-1].get("bot") or ""
    if ASKED_FOR_FIGURE not in said and not (_a_new_total_only(clean)
                                             and WORKED.search(" ".join(said.split()))):
        # Either the bot asked for the figure, or it has just worked a time for the plan's own
        # total ("£20,000 at £200 a month is 100 months") and this line only puts another total
        # in its place: "say i need 12000" is the same question about 12,000. A line with more
        # in it than the total is not this one - "and what if i find one for 6000, is that daft"
        # asks how much worse off the dearer one leaves them, and has its own answer.
        return None
    numbers = _parse(clean)
    rate, period = _rate_in_chat(memory)
    if len(numbers) != 1 or not rate or numbers[0] < rate * 2:
        return None
    return _duration_reply(rate, period, numbers[0])


HOW_MUCH_EACH = re.compile(
    r"how much (?:should|do|would|will|can|need|have) (?:i|we)\b[^?]*\b(?:day|week|month)\b|"
    r"how much\b[^?]*\b(?:put away|put by|set aside|put aside|save each|save per)\b")
# The same question with no verb left in it: "how much a month", "how much would that be a week".
# The person has the total in front of them - they gave it a turn or two ago - and what they want is
# the one figure that comes out of a pay packet, not the card about the thing they are saving for.
# "im saving for a car" / "i need about 4000" / "how much a month" came back as a car-buying card
# about dealer targets. Only the whole line counts, so a real question that carries a rate word
# ("what is a gym a month") is somebody else's.
A_BARE_RATE_ASK = re.compile(
    r"^\s*(?:(?:and|so|ok|okay|right|but|then|well)\b[\s,]*)*"
    r"(?:how\s+much|what)\b"
    r"(?:\s+(?:would|will|do|should|could|does|did)\b"
    r"(?:[\s,]+(?:that|it|i|we|you)\b)?(?:[\s,]+(?:need|have|be|take|come\s+to)\b)?)?"
    r"\s+(?:a|per|each|every|once\s+a)\s+(?P<period>day|week|fortnight|month)\b"
    r"(?:\s+(?:would|will|could|should)\s+(?:that|it|this)\s+be\b)?"
    r"[\s?.!]*$", re.I)
# The period the person is asking about: "each week" wants a weekly figure, and answering it in
# months is answering a different question.
EACH_PERIOD = re.compile(r"\b(?:each|a|per|every|once a)\s+(day|week|fortnight|month)\b")
PERIODS_IN_A_YEAR = {"day": 365, "week": 52, "fortnight": 26, "month": 12}
# A deadline the person named and we cannot count to ("by december", "before christmas") makes
# any figure per week a guess about how much of the year is left, so this line stays quiet.
# A day of the month is a deadline too, and it is the one the store writes when a person puts a
# date right: "save 500 by june" / "no, the 4th of july" leaves "Save 500 by the 4th of July", and
# a reader that only knew month names counted to the first of the month or gave up and repeated
# the older answer with its older figure.
# "the end of december" is a deadline the same way "the end of the month" is, and it was the one
# form of it that did not match: the month names stood bare in the pattern, so the days left were
# counted nowhere and the goal fell back to whatever else the line said.
DEADLINE_NAMED = re.compile(
    r"\b(?:by|before|until|till|in time for|ready for)\s+(?:(?:the\s+)?\d{1,2}"
    r"(?:st|nd|rd|th)(?:\s+of)?\s+)?(?:christmas|easter|summer|the summer|"
    r"winter|the winter|next (?:week|month|year|summer|christmas|easter)|"
    r"the end of (?:the |next |this )?(?:month|year|week|january|february|march|april|may"
    r"|june|july|august|september|october|november|december)|"
    r"january|february|march|april|may|june|july|august|september|october|november|december)\b"
    r"|\bfor (?:christmas|the summer|summer|the holiday|our holiday)\b")
GOAL = re.compile(r"\b(?:save|saves|saving|saved|deposit|need|needs|want|wants|afford|"
                  r"cost|costs|price|budget|goal|target|towards|toward|for a|for the|owe|owes|"
                  r"owing|owed|debt|debts|repay|repaying|pay off|paying off)\b")


def _each_month_for_a_goal(clean, memory):
    """A figure to reach but no date: how much to put by each month."""
    bare = A_BARE_RATE_ASK.search(clean)
    if not (HOW_MUCH_EACH.search(clean) or bare):
        return None
    if _parse(clean) or TIME_ELSEWHERE.search(clean):
        return None
    total = _goal_in_chat(memory)
    if not total:
        return None
    if DEADLINE_NAMED.search(clean) or _a_deadline_in_chat(memory):
        # how much a week depends on how much of the time is left, and the chat named the time, so
        # the figure is worked out to the date rather than over a year the person never said.
        dated = _a_month_for_the_deadline_in_chat(total, memory)
        if not dated:
            return None
        return dated
    period = _asked_period(clean)
    per_year = PERIODS_IN_A_YEAR[period]
    year, two = total / per_year, total / (per_year * 2)
    return (f"Saving {_number(total)} over a year is about {_number(round(year))} a {period}; "
            f"over two years, about {_number(round(two))} a {period}.")


# A date the person names for a figure the chat already holds, said in months or years:
# "i want it in a year", "in six months", "within 2 years", "18 months from now".
HORIZON_SAID = re.compile(
    r"\b(?:in|within|inside|over|after)\s+(?P<count>\d+|an?|one|two|three|four|five|six|seven|"
    r"eight|nine|ten|eleven|twelve|couple\s+of|few)\s*(?P<unit>days?|weeks?|fortnights?|"
    r"months?|years?)\b(?:\s*(?:from now|time))?")
HORIZON_COUNTS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                  "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
                  "twelve": 12, "couple of": 2, "few": 3}
# "I saved 200 in 3 months" is a report of what happened, not a plan: the past tense means the
# time has already gone. The money the person still has to find is what these replies are for.
PAST_REPORT = re.compile(
    r"\b(?:saved|spent|paid|lent|borrowed|bought|earned|received|got|took|have had|ago)\b")


# A named date is a deadline the arithmetic can use: the time left between today and the date
# is what the monthly figure divides the goal by. "how do i save 3000 by christmas" was answered
# as a Christmas shopping budget on main, and "i want to save 5000 by next summer" not at all.
DEADLINE_DAYS = {"christmas": (12, 25), "the end of the year": (12, 31), "the end of the month": None,
                 "the end of the week": None, "next year": (1, 1), "next month": None,
                 "next week": None, "easter": None, "summer": (7, 1), "the summer": (7, 1),
                 "winter": (12, 1), "the winter": (12, 1)}
MONTH_NUMBERS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                 "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
                 "december": 12}
# "save 10k in 6 months" is money with a shorthand on it, not a race: the entries answer a
# distance when the line is about running, and this only reads a k as a thousand when the line
# also has a goal word in it.
K_THOUSANDS = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*k\b")
# The line itself has to be about putting money by, not just carry a date: "how do i budget for
# christmas" after a saving goal in the chat was answered with the goal's arithmetic instead of
# the Christmas shopping budget, and that is a different question.
# A date put on the thing already in the chat, with no saving word in it: "i want it by next
# summer", "we need it before june", "i have to have it by august". The figure is on the turn
# before, so this is the other half of one sum - and without it the line was read as a new plan
# and said back to the person ("It by next summer - fair enough. What's stopped it happening so
# far?"), which answers a question they did not ask.
A_DATE_FOR_THE_THING = re.compile(
    r"^\s*(?:(?:and|but|so|ok|okay|right|well|then)\b[\s,]*)*"
    r"(?:i|we)\s+(?:want|need|would\s+like|have\s+to\s+have|must\s+have|'d\s+like)\s+"
    r"(?:it|that|them|this)\b[^0-9]*\b(?:by|before|in\s+time\s+for)\b", re.I)
SAVE_VERB = re.compile(r"\b(?:save|saves|saving|saved|put by|put aside|set aside|put away|"
                       r"pay in|paying in)\b")
SAVING_CUE = re.compile(r"\b(?:save|saves|saving|saved|put by|put aside|set aside|put away|"
                        r"need|want|afford|goal|target|towards|toward|budget)\b")


def _k_as_money(clean):
    """The figure in a line that writes 10k, read as 10,000 when the line is about money.

    Only used by the goal arithmetic below, so a race stays a race: "how far is a 10k" has no
    goal word in it and is never read here.
    """
    found = K_THOUSANDS.search(clean)
    if not found or not SAVING_CUE.search(clean):
        return None
    amount = float(found.group(1)) * 1000
    return amount if amount >= 100 else None


def _easter_day(year):
    """The date of Easter Sunday, so "save 3000 by easter" has a date to count back from.

    The Gregorian rule in eight lines rather than a table: Easter is the first Sunday after the
    first full moon on or after 21 March, and the arithmetic below is the standard way to get
    that without a calendar lookup.
    """
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return month, day


A_DEADLINE_DAY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\s+(?:of\s+)?([a-z]+)\b", re.I)


def _the_last_day_of(month, today):
    """The day the month ends on: 31 for December, 30 for June, 28 or 29 for February."""
    import calendar

    year = today.year + (1 if month < today.month else 0)
    return calendar.monthrange(year, month)[1]


def _a_named_deadline(clean, today=None):
    """The date a line names for the money already in it: ("christmas", date) or None.

    The months and days left are what a per-month figure is for, so a date that can be read
    exactly is taken; a movable feast like Easter is left alone rather than guessed at.
    """
    import datetime
    today = today or datetime.date.today()
    found = DEADLINE_NAMED.search(clean)
    if not found:
        return None
    said = found.group(0).lower()
    name = said.split()[-1]
    a_day = A_DEADLINE_DAY.search(said)
    for phrase in ("the end of next month", "the end of this month", "the end of next week",
                   "the end of this week", "the end of next year", "the end of this year",
                   "the end of the year", "the end of the month",
                   "the end of the week",
                   "next summer", "next christmas", "next year", "next month", "next week",
                   "the summer", "the winter"):
        if phrase in said:
            name = phrase
            break
    if a_day and a_day.group(2) in MONTH_NUMBERS:
        month, day = MONTH_NUMBERS[a_day.group(2)], int(a_day.group(1))
        name = "the " + a_day.group(0).lower()
        if not 1 <= day <= 31:
            return None
    elif name in MONTH_NUMBERS:
        month = MONTH_NUMBERS[name]
        # "by december" is the month from its first day, but "by the end of december" is the last
        # one, and it was read as the first: said in mid-November, "i need to save 3000 by the end
        # of december" got "by december is 21 days away, so it is one pay packet" when there were
        # 51 days left. The words "end of" are the whole of what was dropped.
        at_the_end = "end of" in (said + " " + clean[max(0, found.start() - 12):found.start()])
        day = _the_last_day_of(month, today) if at_the_end else 1
        name = "the end of " + name if at_the_end else name
    elif name in ("next summer", "next christmas"):
        month, day = DEADLINE_DAYS[name.replace("next ", "")] or (7, 1)
    elif name == "easter":
        month, day = _easter_day(today.year)
    elif name in DEADLINE_DAYS and DEADLINE_DAYS[name]:
        month, day = DEADLINE_DAYS[name]
    elif name == "next month":
        year, month = (today.year + (today.month == 12), today.month % 12 + 1)
        return name, datetime.date(year, month, 1)
    elif name == "next week":
        return name, today + datetime.timedelta(days=7)
    elif name in ("the end of the month",):
        # The last day of this month, not the first of the next: "by the end of the month" said on
        # the 10th is 20 days away, and the first of next month is a day late and reads as a date
        # nobody named.
        return name, datetime.date(today.year, today.month, _the_last_day_of(today.month, today))
    elif name in ("the end of the week",):
        return name, today + datetime.timedelta(days=7 - today.weekday())
    elif name in ("the end of next month", "the end of this month"):
        # Counted from today, because the line names no month: the last day of next month, or of
        # this one. December needs the year moved on, which _the_last_day_of does not do.
        import calendar

        step = 1 if "next" in name else 0
        month = today.month + step
        year, month = today.year + (month - 1) // 12, (month - 1) % 12 + 1
        return name, datetime.date(year, month, calendar.monthrange(year, month)[1])
    elif name in ("the end of next year", "the end of this year", "the end of the year"):
        # The last day of the year rather than the first day of the next one: "i want it gone by
        # the end of next year" said in November is 415 days, and the phrase loop took "next
        # year" out of it and answered 51 - a year early, on a sum the person is paying interest
        # on. The year words have to be tested before "next year" for that reason.
        return name, datetime.date(today.year + (1 if "next" in name else 0), 12, 31)
    elif name in ("the end of next week", "the end of this week"):
        # The Sunday of the week in hand, and a week on when the person says next.
        return name, today + datetime.timedelta(days=7 - today.weekday() + (7 if "next" in name else 0))
    else:
        return None
    try:
        when = datetime.date(today.year, month, day)
        if when <= today:  # the date has gone this year, so it is next year's
            when = datetime.date(today.year + 1, month, day)
    except ValueError:  # "the 31st of february" is not a date, and a day that is not one is no
        return None  # deadline to count to
    return name, when


def _save_by_a_date(clean, memory):
    """A goal and a named date: what has to go by each month, and each week when it is close."""
    import datetime
    today = datetime.date.today()
    dated = _a_named_deadline(clean, today)
    if not dated:
        return None
    name, when = dated
    if PAST_REPORT.search(clean):
        return None
    total = _k_as_money(clean)
    if not total:
        numbers = [number for number in _parse(clean) if number >= 50]
        total = numbers[0] if len(numbers) == 1 else None
    if not total:
        if not SAVE_VERB.search(clean) and not A_DATE_FOR_THE_THING.search(clean):
            return None  # a date with no figure and no saving in it is someone else's question
        total = _goal_in_chat(memory)
    if not total:
        return None
    return _a_total_by_a_date(total, name, when, today)


def _a_total_by_a_date(total, name, when, today=None):
    """A total and a date: the figure that comes out of each pay packet, or None."""
    import datetime
    today = today or datetime.date.today()
    days = (when - today).days
    if days < 1:
        return None
    months = days / 30.44
    if months < 1.2:
        said = (f"\u00a3{_number(total)} by {name} is {days} days away, so it is one pay packet: "
                f"put the \u00a3{_number(round(total))} aside on payday before anything else")
    else:
        said = (f"\u00a3{_number(total)} by {name} is {days} days away, so about "
                f"\u00a3{_number(round(total / months))} a month")
        if days <= 120:
            # the week is what comes out of a pay packet, and rounding it up is what makes the
            # sum add up: the money entry's own weekly figure is worded the same way.
            weeks = -(-days // 7)
            a_week = -(-int(round(total)) // weeks)
            said += (f" - about \u00a3{_number(a_week)} a week over the {weeks} weeks left, which "
                     "is the number that actually comes out of a pay packet")
    return said + ". Take it off the top on payday rather than saving what is left at the end."


def _a_month_for_the_deadline_in_chat(total, memory):
    """The figure to the date the chat named: "how much a month" after a goal with a deadline.

    "im saving for a car" / "i need about 4000" / "i want it by next summer" / "how much a
    month" is one sum, and every number of it is already in the chat. The date is worked out the
    same way as when the person says it on the same line, so the two routes cannot disagree.
    """
    import datetime
    today = datetime.date.today()
    for line in reversed(_user_lines(memory)):
        dated = _a_named_deadline(line, today)
        if not dated:
            continue
        if PAST_REPORT.search(line):
            return None
        name, when = dated
        return _a_total_by_a_date(total, name, when, today)
    return None


def _deadline_for_a_goal(clean, memory):
    """A date on its own for a figure already in the chat: "i want it in a year".

    When both the goal and the time to reach it are known, the one number left is what it
    takes each month: 5,000 in a year is 417 a month. Without this the follow-up after "im
    saving for a car hoping to spend about 5000" was answered as small talk, and the person
    still had to do the division themselves. The line has to carry the date and nothing else:
    a line with its own figure or rate is a different sum, and the forms above answer it.
    """
    said = HORIZON_SAID.search(clean)
    if not said or TIME_ELSEWHERE.search(clean) or DEADLINE_NAMED.search(clean):
        # "by christmas", "by june", "by next summer": the date is read from the calendar and
        # the monthly figure worked out from the days left.
        return None if not DEADLINE_NAMED.search(clean) else _save_by_a_date(clean, memory)
    raw = said.group("count")
    count = float(raw) if raw.isdigit() else HORIZON_COUNTS.get(" ".join(raw.split()))
    if not count or RATE.search(clean):
        return None
    rest = (clean[:said.start()] + " " + clean[said.end():]).strip()
    numbers = _parse(rest)
    short_hand = _k_as_money(clean)
    if short_hand:
        # "10k" is read by _parse as 10, so the k has to win outright or the goal looks like
        # ten pounds and the line is passed on.
        numbers = [short_hand]
    if numbers:
        # a figure on the same line is the goal when it is one ("im saving 4000 and i want it
        # in 18 months"); anything else is a different question and stays out of this
        if len(numbers) != 1 or not GOAL.search(rest) or numbers[0] < 50:
            return None
        if PAST_REPORT.search(rest):
            return None  # a sum that has already happened is not a plan
        total = numbers[0]
    else:
        total = _goal_in_chat(memory)
    if not total:
        return None
    unit = said.group("unit").rstrip("s")
    months = count * PERIODS[unit]
    if months < 1 or months > 600:
        return None
    per = total / months
    if per < 1:
        return None
    when = ("a " + unit) if count == 1 else f"{_number(count)} {unit}s"
    return (f"{_number(total)} in {when} is {_number(round(per))} a month. "
            "Set the transfer for the day after payday so the money goes before you can spend it.")


def _asked_period(clean):
    """The period the line asks about, month when it names none."""
    asked = EACH_PERIOD.search(clean or "")
    return asked.group(1) if asked else "month"


def _a_deadline_in_chat(memory):
    """Whether the chat named a deadline ("by december") that a per-month figure would ignore."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    return any(DEADLINE_NAMED.search(turn.get("user") or "")
               for turn in turns[-4:] if isinstance(turn, dict))

def _saving(clean):
    """A monthly or weekly amount from "save 480 pounds in 6 months"."""
    if not any(word in clean for word in ("need", "want", "should", "how much", "each", "per",
                                          "plan")):
        return None
    amount = re.search(r"(?:save|saving|saved)\s+(?:up\s+)?[£$€]?\s*([\d,.]+)", clean)
    when = re.search(r"(?:in|over|within)\s+(\d+)\s*(month|week|year)s?", clean)
    if not amount or not when:
        return None
    total = float(amount.group(1).replace(",", ""))
    count = int(when.group(1))
    unit = when.group(2)
    if unit == "year":
        count, unit = count * 12, "month"
    if count < 1:
        return None
    per = total / count
    return f"Saving {_number(total)} over {count} {unit}s is {_number(per)} a {unit}."


def _average(clean):
    match = re.search(r"average(?: of)?\s+(.+)", clean)
    if not match:
        return None
    numbers = _parse(match.group(1))
    if len(numbers) < 2 or any(word in match.group(1) for word in ("speed", "month", "year")):
        return None
    mean = sum(numbers) / len(numbers)
    return f"The average is {_number(mean)}."


# --- the size of a floor, a wall, a garden ---------------------------------
#
# "what is the area of a 4m by 3m room" was a shrug: the shape rows below ask for the word
# "rectangle" and a bare list of numbers, and a room is neither. A person giving a size writes
# the two sides with the unit on them - "4m by 3m", "12ft x 10ft", "4 metres by 3 metres" - so
# the sizes are read as a pair, the unit is carried into the answer, and area and perimeter
# come out of the same pair. The unit is optional on the second side because "4m by 3" says it.

_LENGTH_UNIT = {
    "m": "m", "metre": "m", "metres": "m", "meter": "m", "meters": "m",
    "cm": "cm", "centimetre": "cm", "centimetres": "cm", "centimeter": "cm",
    "centimeters": "cm",
    "mm": "mm", "millimetre": "mm", "millimetres": "mm", "millimeter": "mm",
    "millimeters": "mm",
    "ft": "ft", "foot": "ft", "feet": "ft",
    "in": "in", "inch": "in", "inches": "in",
    "yd": "yd", "yard": "yd", "yards": "yd",
    "km": "km", "kilometre": "km", "kilometres": "km", "kilometer": "km",
    "kilometers": "km",
}

_LENGTH = (r"(?:m|cm|mm|km|ft|feet|foot|in|inch|inches|yd|yard|yards|metres?|meters?|"
           r"centimetres?|centimeters?|millimetres?|millimeters?|kilometres?|kilometers?)")

# one side, with a unit that may be missing on every side but the first
_SIDE = rf"(\d+(?:\.\d+)?)\s*({_LENGTH})?"

_SIDE_BY_SIDE = re.compile(
    rf"{_SIDE}\s*(?:by|x|×|\*)\s*(\d+(?:\.\d+)?)\s*({_LENGTH})?"
    rf"(?:\s*(?:by|x|×|\*)\s*(\d+(?:\.\d+)?)\s*({_LENGTH})?)?"
)

# "12 square metres" as a whole: the answer is in the unit the question was asked in
_SQUARE_WORD = {"m": "square metres", "cm": "square centimetres", "mm": "square millimetres",
                "ft": "square feet", "in": "square inches", "yd": "square yards",
                "km": "square kilometres"}

# The ask that wants a measurement of a surface, rather than a fact about shape words.
# The asks that want a measurement of a surface. The materials that are bought by area are in
# the list too: "how much carpet for a 4m by 3m room" is a question whose first number is the
# area, and 12 square metres is the answer that gets somebody to the shop counter.
_AREA_ASK = ("area", "how big", "how much space", "square metres", "square meters",
             "square feet", "square foot", "m2", "sqm", "floor area",
             "carpet", "flooring", "laminate", "lino", "tiles", "tiling", "turf", "lawn",
             "patio", "decking", "shed base", "gravel", "bark", "chippings")
_PERIMETER_ASK = ("perimeter", "skirting", "edging", "border", "how much fence", "fencing",
                  "how much beading", "trim for the edge", "goes all the way round")


def _sides(clean):
    """The side lengths named in a line as (value, unit, unit_from_the_line), or None.

    "a 4m by 3m room" gives 4m and 3m; "12ft x 10ft" gives 12ft and 10ft; "a 4 by 3"
    gives two bare numbers and no unit at all, which is still a rectangle somebody drew.
    """
    found = _SIDE_BY_SIDE.search(clean)
    if not found:
        return None
    sizes = []
    for value_at, unit_at in ((1, 2), (3, 4), (5, 6)):
        raw = found.group(value_at)
        if raw is None:
            continue
        unit = _LENGTH_UNIT.get(found.group(unit_at) or "", None)
        sizes.append((float(raw), unit))
    if len(sizes) < 2:
        return None
    # A unit given once carries down the line: "4m by 3" is 4 metres by 3 metres. With no
    # unit at all - "a 5 by 4 room" - the two numbers are still the two sides of something
    # real, so the pair comes back with no unit and the answer names both readings.
    named = next((unit for _, unit in sizes if unit), None)
    if named is None:
        return sizes, None
    return [(value, unit or named) for value, unit in sizes], named


# A shape named in the line is a shape, not a floor: "a 2 by 2 square has what area" and
# "area of a 6 by 4 rectangle" already have their own rows, which say "That rectangle's area is
# 24" - naming the shape back is the right answer, and "A 6 by 4 floor is 24 square metres if
# those are metres" is not. "square" is only a shape when it is not the unit ("square metres").
_SHAPE = re.compile(r"\b(?:rectangle|rectangular|oblong|triangle|triangular|circle|circular|"
                    r"square)\b(?!\s*(?:metres?|meters?|m|cm|mm|km|ft|feet|foot|inches?|"
                    r"yards?|yd)\b)")

# The unit the answer is wanted in, when the line asks for a different one from the sides:
# "what is 4m x 3m in square feet" is a square-feet question with metres in it.
_AREA_TARGET = (("square feet", "ft"), ("square foot", "ft"), ("sq ft", "ft"),
                ("square metres", "m"), ("square meters", "m"), ("square metre", "m"),
                ("square meter", "m"), ("m2", "m"), ("sqm", "m"),
                ("square yards", "yd"), ("square inches", "in"),
                ("square centimetres", "cm"), ("square centimeters", "cm"))

# one square metre, in the unit
_METRES_SQUARED = {"m": 1.0, "cm": 0.0001, "mm": 0.000001, "km": 1000000.0,
                   "ft": 0.09290304, "in": 0.00064516, "yd": 0.83612736}

# The thing being measured, named the way the line named it: "how much turf for a 5m by 4m
# lawn" is a lawn and not a floor. The first word found wins, and "floor" is the fallback.
_SURFACES = (("lawn", "lawn"), ("garden", "garden"), ("patio", "patio"), ("decking", "deck"),
             ("driveway", "driveway"), ("wall", "wall"), ("ceiling", "ceiling"),
             ("roof", "roof"), ("floor", "floor"), ("room", "room"), ("table", "table"),
             ("field", "field"), ("greenhouse", "greenhouse"), ("shed", "shed"),
             ("pond", "pond"), ("border", "border"))


def _surface(clean):
    """The word for the thing whose size was asked, or "floor" when the line names none."""
    for word, label in _SURFACES:
        if re.search(rf"\b{word}\b", clean):
            return label
    return "floor"


def _square_text(value, unit):
    word = _SQUARE_WORD.get(unit, "square units")
    return f"{_number(round(value, 2))} {word}"


# A count asked for by number is not an area: "how many tiles for a 3m by 2m wall" wants the
# tile count, which needs the size of a tile, so that line is left to the row that lays them.
# The thing counted is often named with a word in front of it - "how many decking boards",
# "how many skirting boards", "how many paving slabs for a 4 by 3 patio" - so up to three words
# may sit between "how many" and the noun; the noun still has to be the counted thing.
# The material does not have to follow "how many" at once - "how many paving slabs" and "how many
# plasterboard sheets" are counts - but the words in between are the material's own description,
# never a pronoun or a verb: a gap that took any three words read "how many rooms should we block"
# as a count of concrete blocks.
_COUNTED_GAP = (r"(?:(?!\b(?:i|we|you|they|he|she|it|to|do|does|did|should|could|would|can|"
                r"will|may|might|must|shall|is|are|was|were|be|am|have|has|had|not)\b)\w+\s+){0,3}")
_COUNTED = re.compile(r"\bhow many\s+" + _COUNTED_GAP + r"(?:tiles?|rolls?|packs?|bags?|cans?|tins?|"
                      r"boards?|planks?|squares|lengths?|coats?|slabs?|bricks?|blocks?|"
                      r"panels?|posts?|sheets?)\b")


# A material that is bought by the bag, the roll or the tonne is the materials table's
# question: "how much gravel for a 4m by 3m drive" wants the bags of gravel, and on main it got
# 12 square metres and went off to work out the rest itself. Asking the unit is still this row's
# question, so only the buying words hand the line over.
# Concrete, the ballast and the cement it is mixed from are bought the same way as gravel, by
# the cubic metre and the bag: "how much concrete do i need for a 2m by 2m shed base" was this
# row's 2 x 2 = 4 square metres instead of 0.4 cubic metres of concrete.
_BOUGHT_BY_THE_BAG = ("gravel", "shingle", "chippings", "bark", "mulch", "woodchip", "topsoil",
                      "soil", "compost", "manure", "sand", "slabs", "paving", "turf", "underlay",
                      "grout", "tile adhesive", "adhesive",
                      "concrete", "postcrete", "post mix", "ballast", "cement", "mortar")
_BUYING = re.compile(r"\bhow (?:much|many)\b")


def _floor_area(clean):
    """"a 4m by 3m room": the two sides of a surface, multiplied."""
    if not any(phrase in clean for phrase in _AREA_ASK):
        return None
    if _BUYING.search(clean) and any(word in clean for word in _BOUGHT_BY_THE_BAG):
        return None
    if _COUNTED.search(clean) or _SHAPE.search(clean):
        return None
    found = _sides(clean)
    if not found:
        return None
    sizes, unit = found
    area = sizes[0][0] * sizes[1][0]
    thing = _surface(clean)
    if unit is None:
        # no unit named: the number is right either way, so say which units give which answer
        return (f"A {_number(sizes[0][0])} by {_number(sizes[1][0])} {thing} is "
                f"{_number(round(area, 2))} square metres if those are metres, "
                f"{_number(round(area, 2))} square feet if they are feet.")
    sides = " by ".join(f"{_number(value)}{unit}" for value, _ in sizes[:2])
    # The answer is in the unit the question asked for, when the line names one that the
    # sides are not in: "what is 4m x 3m in square feet" wants square feet.
    target = next((to for word, to in _AREA_TARGET if word in clean), unit)
    if target != unit and target in _METRES_SQUARED and unit in _METRES_SQUARED:
        wanted = round(area * _METRES_SQUARED[unit] / _METRES_SQUARED[target], 2)
        return (f"A {sides} {thing} is {_square_text(wanted, target)}, which is "
                f"{_square_text(area, unit)}. That is the two sides multiplied: "
                f"{_number(sizes[0][0])} x {_number(sizes[1][0])}.")
    return (f"A {sides} {thing} is {_square_text(area, unit)}. "
            f"That is the two sides multiplied: {_number(sizes[0][0])} x "
            f"{_number(sizes[1][0])}.")


def _perimeter_of_a_room(clean):
    """"the skirting for a 4m by 3m room": the two sides added, then doubled."""
    if not any(phrase in clean for phrase in _PERIMETER_ASK):
        return None
    found = _sides(clean)
    if not found:
        return None
    sizes, unit = found
    length, width = sizes[0][0], sizes[1][0]
    if _SHAPE.search(clean):
        return None
    # "how much skirting for a 4m by 3m room" stops one step short with the perimeter alone: the
    # skirting is sold in 2.4m lengths, so the home row counts the lengths as well. Anything else
    # that asks how much edging or border a size takes still has its answer here.
    if re.search(r"\b(?:how many|how much)\s+(?:\w+\s+){0,2}skirting\b", clean):
        return None
    around = 2 * (length + width)
    thing = _surface(clean)
    if unit is None:
        return (f"A {_number(length)} by {_number(width)} {thing} has a perimeter of "
                f"{_number(round(around, 2))} metres if those are metres: twice "
                f"({_number(length)} + {_number(width)}).")
    return (f"A {_number(length)}{unit} by {_number(width)}{unit} {thing} has a perimeter of "
            f"{_number(round(around, 2))}{unit}: twice "
            f"({_number(length)} + {_number(width)}). That is how much skirting, edging or "
            f"border it takes.")


def _area(clean):
    sized = _floor_area(clean)
    if sized:
        return sized
    if not any(phrase in clean for phrase in ("area", "how big", "how much space")):
        return None
    if "circle" in clean:
        radius = re.search(r"radius(?: of| is)?\s*([\d,.]+)", clean)
        if radius:
            r = float(radius.group(1).replace(",", ""))
            return f"A circle with radius {_number(r)} has an area of {_number(3.14159265 * r * r)}."
        diameter = re.search(r"diameter(?: of| is)?\s*([\d,.]+)", clean)
        if diameter:
            r = float(diameter.group(1).replace(",", "")) / 2
            return f"A circle with diameter {_number(r * 2)} has an area of {_number(3.14159265 * r * r)}."
        return "The area of a circle is π × radius²: square the radius, then multiply by 3.14."
    if "triangle" in clean:
        numbers = _parse(clean)
        if len(numbers) >= 2:
            return f"That triangle's area is {_number(numbers[0] * numbers[1] / 2)}."
        return "The area of a triangle is ½ × base × height."
    if "rectangle" in clean or "square" in clean:
        numbers = _parse(clean)
        if len(numbers) >= 2:
            return f"That rectangle's area is {_number(numbers[0] * numbers[1])}."
        return "The area of a rectangle is length × width."
    return None


# Words that may trail a month question without changing it: "how many days in june this year",
# "how many days does august have again". The year itself is read off the same tail.
_MONTH_TAIL = (r"(?:\s+(?:this year|next year|this time|again|now|already|exactly|in total|"
               r"left|to go|please|though|then|anyway)|\s+(?:19|20)\d\d|"
               r"\s*,\s*[^.?!]{0,60}|"
               r"\s+(?:i|we)\s+(?:always\s+|never\s+|keep\s+)?(?:forget(?:ting)?|mix(?:ing)? "
               r"(?:it|them) up|get\s+(?:it|them)\s+mixed up))*")


def _month_year(text):
    """The year a month question names, if it names one ("this year" is the current one)."""
    import datetime
    today = datetime.date.today()
    if re.search(r"\bnext year\b", text):
        return today.year + 1
    if re.search(r"\b(?:this year|this time)\b", text):
        return today.year
    found = re.search(r"\b(?:in |of )?((?:19|20)\d\d)\b", text)
    if found:
        return int(found.group(1))
    return None


def _leap(year):
    """Whether February has 29 days in that year (the rule, not a table)."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(clean):
    """How long one month is, when that is the whole question.

    The month has to be the thing asked about: "how many days in February" and "how
    many days does August have" are questions about a month, while "how many days
    should I take off in August" is a question about leave that happens to name a
    month, and "August has 31 days" would be a wrong answer to it.
    """
    text = _plain(clean)
    for month, days in MONTHS.items():
        if re.fullmatch(rf"(?:how many days (?:are there )?in (?:the month of )?{month}|"
                        rf"how many days (?:does|do) {month} have|"
                        rf"how many days (?:do i have|have i got|are left) in {month}|"
                        rf"{month} has how many days)" + _MONTH_TAIL, text):
            year = _month_year(text)
            if month == "february":
                if year is not None:
                    longer = _leap(year)
                    return (f"February {year} has {29 if longer else 28} days: "
                            f"{year} is {'a leap year' if longer else 'not a leap year'}.")
                return ("February has 28 days in an ordinary year and 29 in a leap year. Leap "
                        "years are divisible by 4, except centuries unless they divide by 400.")
            if year is not None:
                return f"{month.capitalize()} {year} has {days} days."
            return f"{month.capitalize()} has {days} days."
    # "how many days in a leap year": no month named, and the answer is the length of the
    # year rather than of February, which is what the February row above explains.
    if re.fullmatch(rf"(?:how many |how long )(?:days? )?(?:are there |does |is |has )?"
                    rf"(?:in )?(?:a |one |the )?leap year"
                    rf"(?: have| last| long| then| again)?{_MONTH_TAIL}",
                    text):
        return ("A leap year has 366 days: 29 February, and the rest of the year as usual. "
                "The rule is every four years, except centuries unless they divide by 400.")
    return None


# Words that may trail the ask without changing it: "how many days till christmas this year".
_CHRISTMAS_TAIL = (r"(?:\s+(?:this year|next year|this christmas|next christmas|now|again|yet|"
                   r"already|exactly|left|to go|from now|from today|at the moment|please|then))*"
                   # the unit asked for at the end: "how long till christmas in weeks"
                   r"(?:\s+(?:in|as) (?P<unit2>days?|weeks?|sleeps?))?"
                   # a named year: "how many days till christmas 2027"
                   r"(?:\s+(?P<year>\d{4}))?")

# Words for the day itself, so "'til xmas" and "till crimbo" count. Christmas Eve is the day
# before, so it is counted from 24 December and named back the way it was asked about.
_CHRISTMAS_DAY = r"(?:christmas(?: day| eve)?|xmas(?: day| eve)?|crimbo)"


def _christmas_name(text):
    """The day the line asked about: "Christmas Eve" when it said eve, else Christmas."""
    said = str(text or "")
    return "Christmas Eve" if re.search(r"\b(?:christmas|xmas) eve\b", said) else "Christmas"


def _christmas_date_of(text, year):
    """Christmas Day or Christmas Eve in `year`, whichever the line named."""
    import datetime
    return datetime.date(year, 12, 24 if _christmas_name(text) == "Christmas Eve" else 25)

# The countdown, spelled out: every way of asking how long the wait is (#385 kept the whole
# line match; this widens it to the shapes people actually type). The unit is captured, so
# "how many weeks until christmas" comes back in weeks rather than always in days.
_CHRISTMAS_COUNTDOWN = (
    r"(?:"
    r"(?:how many |how much longer |how long )?"
    # "how many **more** days till christmas": the word people add sits between the ask and
    # the unit, and a whole-line match is unforgiving about it.
    r"(?:shopping )?(?:more |still )?(?P<unit>days?|weeks?|months?|sleeps?) "
    # "how many days are left until", "days there left", "days do we have left": a short
    # phrase may sit between the unit and "until", and missing it sent the line to the
    # search shrug or, with "shopping", to the roast-timing entry (#general 3830).
    r"(?:is it |are there |are left |left |to go |still |have i got left |have i got )?"
    r"(?:(?:are|is|there|left|to go|still|do we have|have we got|is it|was it|are they)\s+){0,3}"
    r"(?:until|'?till?|to|before) " + _CHRISTMAS_DAY +
    r"|(?:days|weeks) (?:until|'?till?|to|before) " + _CHRISTMAS_DAY +
    r"|how long (?:is it |have i got |has it been )?(?:until|'?till?|to|before) "
    + _CHRISTMAS_DAY +
    r"|how long (?:is it )?to go until " + _CHRISTMAS_DAY +
    r"|countdown to " + _CHRISTMAS_DAY +
    # "shopping days are left", "shopping days to go": no "until christmas", the words
    # themselves are the question.
    r"|(?:how many )?shopping days (?:are )?(?:left|to go)" +
    # "is it nearly christmas", "is it christmas day today": the date, not the count.
    r"|is it (?:almost|nearly|close to) " + _CHRISTMAS_DAY + r"(?: yet)?"
    r"|is it " + _CHRISTMAS_DAY + r"(?: (?:today|yet|this year))?"
    # "christmas countdown" is the same ask with the words the other way round.
    r"|(?:the )?" + _CHRISTMAS_DAY + r" countdown"
    r")")

# The plainest way to ask for the date itself: "when is christmas", "what date is xmas".
_CHRISTMAS_DATE = (
    r"(?:whens|when(?:'s| is| will it be)|what date is|what day is|which day is|"
    r"whats the date of)"
    r"(?: christmas| xmas| christmas day|xmas day| christmas eve|xmas eve"
    r"| christmas this year)?")

# "is christmas on a friday this year", "what day of the week is christmas": the day of the
# week comes from the calendar, so the line is answered from the date rather than a table.
_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_CHRISTMAS_WEEKDAY = (
    r"(?:what day of the week (?:is|does) |what weekday (?:is|does) "
    r"|which day of the week (?:is|does) )?" + _CHRISTMAS_DAY +
    r"(?: fall| falls| land| lands)?(?: on)?(?: this year| this christmas)?"
    r"|is " + _CHRISTMAS_DAY + r"(?: this year| this christmas)? on a "
    r"(?P<guess>" + "|".join(_WEEKDAYS) + r")")

# "is it christmas today" is a yes-or-no, so it gets the answer and the count, not just one.
_CHRISTMAS_TODAY = r"(?:is it|is) (?:christmas|xmas)(?: day)?(?: today| yet| this year)?"

# "is christmas early or late this year": asking a fixed date to be early or late is the same
# question as asking its date, so the answer says the date does not move.
_CHRISTMAS_FIXED = (
    r"(?:is|was|is it|was it) (?:christmas|xmas)(?: day)?(?: this year| next year| this christmas)?"
    r"\s+(?:(?:early|late)\s+or\s+(?:early|late)|early|late)"
    r"(?: this year| next year| this christmas)?"
)


def _christmas_day(text=""):
    """The Christmas Day the line means, and how many days away it is (negative once past).

    A word that names the year decides which Christmas is meant: "until christmas next year"
    is twelve months after the one "until christmas" counts, so answering it with this year's
    number is a year out and said with confidence. "this year" in late December has already
    gone, and the countdown says so instead of quietly counting next year's.
    """
    import datetime
    today = datetime.date.today()
    said = str(text or "")
    if re.search(r"\bnext (?:year|christmas)\b", said):
        christmas = _christmas_date_of(said, today.year + 1)
    else:
        christmas = _christmas_date_of(said, today.year)
        if christmas < today and not re.search(r"\bthis (?:year|christmas)\b", said):
            christmas = _christmas_date_of(said, today.year + 1)
    return christmas, (christmas - today).days


def _wait_text(days, name="Christmas"):
    """How the wait reads: ahead of us, today, or already gone this year."""
    if days == 0:
        return f"{name} is today."
    if days < 0:
        ago = -days
        return f"{name} this year was {ago} day{'' if ago == 1 else 's'} ago."
    return f"{days} days until {name}."


def _months_between(start, when):
    """Whole months from one day to another on the calendar, and the days left over.

    A month is a calendar month, not thirty days: from 9 November to 25 December is one month
    and sixteen days, and thirty-day arithmetic would call it one month and two weeks. The
    month is taken with the day clamped (`_month_on`), so 31 January plus a month is the end of
    February rather than something that does not exist.
    """
    months = (when.year - start.year) * 12 + (when.month - start.month)
    if months > 0 and _month_on(start, months) > when:
        months -= 1
    return months, (when - _month_on(start, months)).days


def _count_in(unit, days, when=None):
    """The count in the unit the line asked for, so "in weeks" comes back in weeks.

    `when` is the date being counted to, when the line asked for months: that unit is counted
    on the calendar, so the answer says how many months and days away it is rather than
    dividing by thirty.
    """
    import datetime
    unit = (unit or "days").lower()
    if unit.startswith("sleep"):
        return f"{days} sleeps"
    if unit.startswith("week"):
        weeks, spare = divmod(days, 7)
        if not spare:
            return f"{weeks} weeks"
        return f"{weeks} weeks and {spare} day" + ("" if spare == 1 else "s")
    if unit.startswith("month"):
        if when is not None and days > 0:
            # The start is taken from the count itself, so the two arguments always agree even
            # if a caller works the days out differently.
            start = when - datetime.timedelta(days=days)
            months, spare = _months_between(start, when)
        else:
            months, spare = divmod(days, 30)
        if months and spare:
            return (f"{months} month{'' if months == 1 else 's'} and "
                    f"{spare} day{'' if spare == 1 else 's'}")
        if months:
            return f"{months} month{'' if months == 1 else 's'}"
        return f"{spare} day{'' if spare == 1 else 's'}"
    return f"{days} days"


def _shopping_days(days):
    """How many of the days before Christmas are days the shops are open.

    Sundays do not count: the big shops in Britain are shut or on short hours, so the number
    people mean by "shopping days" is the count without them. It is always given with the
    plain number of days, because the two are different and both are useful.
    """
    import datetime
    today = datetime.date.today()
    sundays = 0
    for step in range(1, days):
        if (today + datetime.timedelta(days=step)).weekday() == 6:
            sundays += 1
    return days - sundays


def _countdown_text(found, text):
    """The countdown in the unit that was asked for, and for the year that was named."""
    import datetime
    groups = found.groupdict()
    unit = groups.get("unit2") or groups.get("unit")
    year = groups.get("year")
    name = _christmas_name(text)
    christmas, days = _christmas_day(text)
    if year:
        christmas = _christmas_date_of(text, int(year))
        days = (christmas - datetime.date.today()).days
        if days < 0:
            ago = -days
            return f"{name} {year} was {ago} day{'' if ago == 1 else 's'} ago."
        if days == 0:
            return f"{name} {year} is today."
        return f"{_count_in(unit, days, christmas)} until {name} {year}."
    if days < 0:
        return _wait_text(days, name)
    if days == 0:
        return f"{name} is today."
    if re.match(r"is it\b", text):
        # "is it nearly christmas" is a yes/no question: answer it and then say how far off.
        return f"Not yet - {_count_in(unit, days, christmas)} until {name}."
    if "shopping day" in text:
        return (f"{days} days until {name} - {_shopping_days(days)} of them shopping days.")
    return f"{_count_in(unit, days, christmas)} until {name}."


def _days_until(clean):
    """A countdown to Christmas, only when the line asks for one.

    "How many days until Christmas" is a countdown; "what should I buy my sister for
    Christmas" is a shopping question that must not be answered with a number. The whole
    cleaned line has to be that question, so a mention in passing never counts, and the ask
    is spelled out in the pattern rather than guessed at with a second list of phrases.
    """
    text = _plain(clean)
    if re.fullmatch(_CHRISTMAS_TODAY, text):
        _, days = _christmas_day("")
        if days == 0:
            return "Yes - it's Christmas Day today."
        # The wording main already uses for "is it christmas day today", so the two shapes of
        # the same question answer alike.
        return f"Not yet - {days} days until Christmas."
    # Christmas Day does not move, so "is christmas early or late this year" has an answer
    # rather than a hedge: the question only makes sense about a date that moves, and saying so
    # is more use than "I'd rather not guess". It sits after the countdown forms so it can never
    # take "is it nearly christmas" or "is christmas on a friday".
    if re.fullmatch(_CHRISTMAS_FIXED, text):
        name = _christmas_name(text)
        when, days = _christmas_day(text)
        if days == 0:
            return f"{name} is today, 25 December, the same date every year."
        if days < 0:
            return (f"{name} is always 25 December, so it is neither early nor late: "
                    f"it was on {when.day} {_MONTH_NAMES[when.month - 1]} {when.year}.")
        return (f"{name} is always 25 December, so it is neither early nor late: it is "
                f"{days} days away.")
    found = re.fullmatch(_CHRISTMAS_COUNTDOWN + _CHRISTMAS_TAIL, text)
    if found:
        return _countdown_text(found, text)
    guessing = re.fullmatch(_CHRISTMAS_WEEKDAY + _CHRISTMAS_TAIL, text)
    if guessing:
        return _weekday_text(text, guessing.groupdict().get("guess"))
    found = re.fullmatch(_CHRISTMAS_DATE + _CHRISTMAS_TAIL, text)
    if found:
        when, days = _christmas_day(text)
        name = _christmas_name(text)
        # The date is said in full: "Christmas Day", not "Christmas", which would leave the
        # person to work out which day of it.
        named = name if name == "Christmas Eve" else "Christmas Day"
        # A named year is the date they asked about, so it is said rather than the count of
        # the wait: "when is christmas 2027" wants the day, not "56 days away".
        if found.group("year"):
            return (f"{named} is on {when.day} December {found.group('year')}.")
        if days < 0:
            return _wait_text(days, named)
        day = "today" if days == 0 else f"on {when.day} December, {days} days away"
        return f"{named} is {day}."
    return None


def _weekday_text(text, guess=None):
    """"Is christmas on a friday this year", "what day of the week is christmas", answered
    from the calendar. A guess in the line is answered yes or no rather than repeated."""
    when, days = _christmas_day(text)
    name = _christmas_name(text)
    weekday = when.strftime("%A")
    date = f"{when.day} December {when.year}"
    if guess:
        if guess.lower() == weekday.lower():
            return f"Yes - {name} is on a {weekday} this year, {date}."
        return (f"No - {name} is on a {weekday} this year, {date}, "
                f"not a {guess.capitalize()}.")
    return f"{name} is on a {weekday} this year, {date}. That is {days} days away."


# --- Easter and the feasts that hang off it --------------------------------

# Easter Sunday is the first Sunday after the first full moon on or after 21 March, which
# is computable rather than a table: one rule gives every year. These are the days counted
# from Easter that people ask about by name, and the words that name each one.
_EASTER_OFFSETS = (
    (r"easter(?:\s+(?:sunday|day))?", 0, "Easter Sunday"),
    (r"good friday", -2, "Good Friday"),
    (r"easter monday", 1, "Easter Monday"),
    (r"palm sunday", -7, "Palm Sunday"),
    (r"maundy thursday", -3, "Maundy Thursday"),
    (r"(?:ash wednesday|lent)", -46, "Ash Wednesday"),
    (r"(?:shrove tuesday|pancake day)", -47, "Shrove Tuesday"),
    (r"ascension day", 39, "Ascension Day"),
    (r"(?:whit sunday|pentecost)", 49, "Pentecost"),
)
_MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December")

# The ways people ask for a date, then whatever trails the ask without changing it.
# "what day is it the day before christmas" and "what day is it on the 24th" put an "it"
# between the question and the thing asked about, and without it here they were a punt. The
# "it" is optional and only ever read as part of a longer fullmatch, so "what day is it" is
# still the clock's own line.
_ASK_DATE = (r"(?:when(?:'s| is| will it be| does)|what (?:date|day|days) (?:is|are)(?: it)?|"
             r"which (?:date|day) (?:is|are)|whats the date of)")
_DATE_TAIL = (r"(?:(?:\s+(?:in\s+)?20\d{2})|\s+(?:this year|next year|this easter|"
              r"next easter|now|again|yet|exactly|left|to go))*")


def _easter_sunday(year):
    """Easter Sunday in the Gregorian calendar: the computus, in ten lines, no table."""
    import datetime
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return datetime.date(year, month, day + 1)


def _feast_year(text):
    """The year the line means, and whether it named one itself."""
    import datetime
    today = datetime.date.today()
    four_digits = re.search(r"\b(20\d{2})\b", text)
    if four_digits and 2000 <= int(four_digits.group(1)) <= 2100:
        return int(four_digits.group(1)), True, today
    if re.search(r"\bnext (?:year|easter)\b", text):
        return today.year + 1, False, today
    return today.year, False, today


# A countdown to a date the bot cannot know: "how many sleeps until my birthday" is a count of
# nights, not an adult's sleep needs, and not something it can answer without the date. The
# answer a friend gives is "tell me the day and I'll count it", so that is what this says. The
# words after "until" have to be a named event ("my birthday", "our holiday", "the wedding") or
# a date, and the unit has to be a count of time, so no sleep question can land here.
_COUNT_ASK = (
    r"(?:how many|how much longer|how long)?\s*"
    r"(?:more\s+|still\s+)?"
    r"(?P<unit>days?|weeks?|months?|sleeps?|nights?)\s+"
    r"(?:is it\s+|are there\s+|are left\s+|left\s+|to go\s+|have i got left\s+)?"
    r"(?:until|'?till?|to|before)\s+"
    r"(?P<rest>.+)"
    # "how long until my due date", "countdown to my holiday": no unit word at all, so the
    # answer comes in days.
    r"|(?:how long(?:\s+(?:is it|have i got))?|countdown)\s+(?:to go\s+)?"
    r"(?:until|'?till?|to|before)\s+(?P<rest2>.+)"
)
_COUNTED_EVENT = (
    r"(?:(?:my|his|her|their|our|the)\s+)?(?:little\s+|big\s+)?"
    r"(?:birthday|holiday|holidays|wedding|anniversary|exam|exams|test|results day|due date|"
    r"operation|op|flight|trip|cruise|driving test|interview|retirement|graduation|move|"
    r"house move|scan|appointment|payday|pay day)"
    # A destination or a date may follow the event: "my holiday to spain" is the same wait as
    # "my holiday", and the count still needs the day, so the tail is allowed but not read here.
    r"(?:\s+(?:on|in|to|for)\s+(?P<when>.+))?"
)
_MONTHS_SAID = ("january", "february", "march", "april", "may", "june", "july", "august",
                "september", "october", "november", "december")
# The short spellings people type. "how many days until dec 5" and "how many weeks till sept 1"
# were a punt and a shrug while "5 december" was counted, which is the same question written the
# other way round. Only the spellings that cannot be an ordinary word are here; "may" is already
# a month name and is never read as the verb by a line with a date in it.
_MONTH_SHORT = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
                "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12}
_MONTH_WORD = ("(?:january|february|march|april|may|june|july|august|september|october|november|"
               "december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)")
_DAY_MONTH = (
    r"\b(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<month>" + _MONTH_WORD + r")\b"
    # The day after the month takes its ordinal too: "december 5th" was not read at all, because
    # the boundary after the figure has to sit after the "th".
    r"|\b(?P<month2>" + _MONTH_WORD + r")\s+(?P<day2>\d{1,2})(?:st|nd|rd|th)?\b"
)


def _month_number(word):
    """The month a name or short spelling stands for, or None."""
    word = (word or "").strip().lower()
    if word in _MONTHS_SAID:
        return _MONTHS_SAID.index(word) + 1
    return _MONTH_SHORT.get(word)
# "How many sleeps until the 25th": the month is the one coming, because the 25th of a month
# that has gone is not a countdown. The ordinal has to end the line, so "the 2nd interview" and
# "the 1st class ticket" are not read as dates.
_DAY_ONLY = re.compile(
    r"(?:^|\bthe\s+|\bof\s+)(?P<day>\d{1,2})(?:st|nd|rd|th)\b"
    r"(?:\s+(?:now|please|thanks|again|yet))*\s*$",
    re.I,
)


def _day_in_a_month(day, month_number, today):
    """That day in that month, the next time it comes round.

    Trying the years in turn is what makes "how many days until 29 february" countable: the date
    is not on the calendar this year or next, and answering "I do not know" for a date that
    exists every fourth year is the wrong kind of honesty.
    """
    import datetime
    for year in range(today.year, today.year + 9):
        try:
            when = datetime.date(year, month_number, day)
        except ValueError:
            continue
        if when >= today:
            return when
    return None


def _date_the_line_gave(text):
    """The day and month the line names, as the next date it falls, and how to say it."""
    import datetime
    today = datetime.date.today()
    found = re.search(_DAY_MONTH, text, re.I)
    if found:
        day = found.group("day") or found.group("day2")
        month = (found.group("month") or found.group("month2") or "").lower()
        try:
            when = _day_in_a_month(int(day), _month_number(month), today)
        except (ValueError, TypeError):
            return None, None
        return (when, f"{when.day} {when.strftime('%B')}") if when else (None, None)
    bare_day = _DAY_ONLY.search(text)
    if not bare_day:
        return None, None
    day = int(bare_day.group("day"))
    for step in range(13):
        month_index = today.month - 1 + step
        try:
            when = datetime.date(today.year + month_index // 12, month_index % 12 + 1, day)
        except ValueError:
            continue
        if when >= today:
            return when, f"{when.day} {when.strftime('%B')}"
    return None, None


# --- a day counted from today, not from a date on the calendar -----------------
# "how many days until tomorrow", "what date is it in two weeks": the line names no date and no
# event, so nothing above can count it, and the arithmetic is the whole answer. A relative day is
# a small closed set in English, so each phrase is turned into the date it means and then the
# same count is done on it; that keeps one countdown voice for every shape of the question.
_SMALL_NUMBER = {"a": 1, "an": 1, "one": 1, "couple of": 2, "a couple of": 2,
                 "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                 "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
_HOW_FAR = re.compile(
    r"(?:in\s+)?(?P<num>\d{1,3}|a couple of|couple of|a|an|one|two|three|four|five|six|"
    r"seven|eight|nine|ten|eleven|twelve)\s+"
    r"(?P<unit>days?|weeks?|months?|years?)"
    r"(?:\s*'?s?\s*time|\s+from\s+(?:now|today|tomorrow))?",
    re.I,
)


def _month_on(day, months_ahead):
    """The same day that many months on, in the month that has it."""
    import calendar
    import datetime
    month_index = day.month - 1 + months_ahead
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(day.day, last))


def _first_of_the_month(day, months_ahead):
    """The 1st of the month that many months on: the turn of the month, not a day inside it."""
    import datetime
    month_index = day.month - 1 + months_ahead
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return datetime.date(year, month, 1)


def _relative_day(text):
    """The date a phrase counted from today points at, and how to say it.

    The phrase is turned into a date rather than into a rule about adding days, so every way of
    saying the same day lands on one date: "tomorrow", "in a day" and "a day from now" are the
    same count, and a month is a month on the calendar rather than thirty days.
    """
    import datetime
    today = datetime.date.today()
    said = " ".join(str(text or "").lower().split()).strip(" .!?")
    if re.fullmatch(r"(?:today|tonight|this day)", said):
        return today, "today"
    if re.fullmatch(r"tomorrow", said):
        return today + datetime.timedelta(days=1), "tomorrow"
    if re.fullmatch(r"(?:the )?day after tomorrow", said):
        return today + datetime.timedelta(days=2), "the day after tomorrow"
    # Saturday is the weekend people mean: on a Saturday the weekend has started, so the count
    # is nothing rather than a week.
    if re.fullmatch(r"(?:the|this) weekend", said):
        return today + datetime.timedelta(days=(5 - today.weekday()) % 7), "the weekend"
    if re.fullmatch(r"next weekend", said):
        return today + datetime.timedelta(days=(5 - today.weekday()) % 7 + 7), "next weekend"
    if re.fullmatch(r"next week", said):
        return today + datetime.timedelta(days=(7 - today.weekday()) % 7 or 7), "next week"
    # "next month" and "next year" are when the calendar turns, not this day next month: the turn
    # of the month is the 1st, the same way "next week" is the Monday. A countdown is where the
    # difference shows - "365 days until next year" on the 6th of November is a year nobody meant.
    if re.fullmatch(r"next month", said):
        return _first_of_the_month(today, 1), "next month"
    if re.fullmatch(r"next year", said):
        return datetime.date(today.year + 1, 1, 1), "next year"
    found = _HOW_FAR.fullmatch(said)
    if not found:
        return None, None
    raw = found.group("num").lower()
    count = int(raw) if raw.isdigit() else _SMALL_NUMBER.get(raw)
    if not count or count > 999:
        return None, None
    unit = found.group("unit").lower()
    if unit.startswith("day"):
        return today + datetime.timedelta(days=count), None
    if unit.startswith("week"):
        return today + datetime.timedelta(days=7 * count), None
    if unit.startswith("month"):
        return _month_on(today, count), None
    return _month_on(today, 12 * count), None


def _relative_count_text(unit, days):
    """The count in the unit the line asked for, in the singular when it is one."""
    unit = (unit or "days").lower()
    counted = "sleeps" if unit.startswith(("sleep", "night")) else unit
    if days == 1:
        return counted[:-1] if counted.endswith("s") else counted
    return counted


def _days_until_a_relative_day(clean):
    """A countdown to a day counted from today: "how many sleeps until the weekend"."""
    import datetime
    text = _plain(clean)
    found = re.fullmatch(_COUNT_ASK, text, re.I)
    if not found:
        return None
    rest = (found.groupdict().get("rest") or found.groupdict().get("rest2") or "").strip()
    if not rest:
        return None
    when, said = _relative_day(rest)
    if when is None:
        return None
    days = (when - datetime.date.today()).days
    unit = (found.groupdict().get("unit") or "days").lower()
    one = _relative_count_text(unit, days)
    if days <= 0:
        return f"That is today - no {_relative_count_text(unit, 2)} left to wait."
    if days == 1:
        if said == "tomorrow":
            return f"Tomorrow, so one {one}."
        return f"One {one} until {said}."
    return f"{_count_in(unit, days, when)} until {said or _short_date(when)}."


def _date_counted_from_today(clean):
    """"what date is it in two weeks": the calendar arithmetic, said as a date."""
    import datetime
    text = _plain(clean)
    rest = None
    # "the date" needs no connector before a day word: "whats the date tomorrow" and "what's the
    # day tomorrow" are the same question as "what date is it tomorrow", and the "in|of" that made
    # the pattern work for "the date in two weeks" made them reach nothing at all.
    for pattern in (r"what(?:'s|s| is)? the (?:date|day) (?:(?:in|of) )?(?P<rest>.+)",
                    r"what date (?:is it|is|will it be) (?P<rest>.+)",
                    r"what day (?:is it|will it be) (?P<rest>.+)",
                    r"what date is it on (?P<rest>.+)"):
        found = re.fullmatch(pattern, text)
        if found:
            rest = found.group("rest").strip()
            break
    if not rest:
        return None
    when, _ = _relative_day(rest)
    if when is None:
        return None
    if when == datetime.date.today():
        return f"That is today, {_short_date(when)}."
    return f"That is {_day_text(when)}."


def _days_until_a_named_day(clean):
    """A countdown to an event whose date the bot cannot know: ask for the day, then count.

    "How many sleeps until my birthday" used to reach the sleep-needs entry and come back with
    seven to nine hours a night (#1519), which is a different question about a different thing.
    "How many sleeps till christmas" works because Christmas is a known date; a birthday, a
    holiday or a wedding is not, so the honest answer is to ask for it and say how the count
    works. A date said in the line is counted rather than asked for again.
    """
    import datetime
    text = _plain(clean)
    if re.search(_CHRISTMAS_DAY + r"\b", text) or re.search(r"\beaster\b", text):
        return None
    found = re.fullmatch(_COUNT_ASK, text, re.I)
    if not found:
        return None
    rest = (found.groupdict().get("rest") or found.groupdict().get("rest2") or "").strip()
    # "how many days until i go on holiday": the going is part of the event, not a
    # determiner, so the same words answer as "how many days until my holiday".
    rest = re.sub(r"^(?:i|we)\s+(?:go|am going|are going|'m going|'re going|leave)\s+(?:on\s+)?",
                 "", rest, flags=re.I)
    if not rest:
        return None
    unit = (found.groupdict().get("unit") or "days").lower()
    counted = "sleeps" if unit.startswith("sleep") or unit.startswith("night") else unit
    event = re.fullmatch(_COUNTED_EVENT + r"(?:\s+(?:please|thanks|now|yet))?", rest, re.I)
    named = bool(event)
    if not named and not _date_the_line_gave(rest)[0]:
        return None
    when, said = _date_the_line_gave(rest)
    if when is not None:
        days = (when - datetime.date.today()).days
        if days == 0:
            return f"That is today - no {counted} left to wait."
        return f"{_count_in(unit, days, when)} until {said}."
    if re.search(r"\bpay ?day\b", rest):
        # A payday is a date only the person's own payslip knows, and the child-waiting tail
        # below is a strange thing to say about it.
        return ("I can't see your payday from here, so tell me the date it lands on and I'll "
                f"count the {counted} to it.")
    asked = ("I can't see a calendar from here, so tell me the date - the day and the month - and "
             f"I'll count it: how many {counted} from today.")
    if counted.startswith("month"):
        # A paper chain counts nights, so it is no help to somebody counting in months, and a
        # birthday, a payday or a holiday already has a date the person can give.
        return asked
    return (asked + " If it is a child waiting, a paper "
            "chain or a row of crosses on the calendar is the same count, and they can do one a "
            "night, which does more for the waiting than the number does.")


# --- the rest of a period, and how long ago a day was -----------------------
# "how many days left in the month", "how many weeks left in the year": the line names no date
# and no event, only the stretch of calendar it is standing in, so nothing above counts it and
# the answer people want is a number. The cue word ("left", "to go", "the end of") is what makes
# it a count rather than "how many days in a year", which is a fact about the calendar.
_REST_OF_A_PERIOD_WORDS = frozenset("""
how many much long day days week weeks are is left to go remaining remain in of until till the
this end month year tax now already exactly please today january february march april may june july
august september october november december jan feb mar apr jun jul aug sep sept oct nov dec
""".split())

_REST_OF_A_PERIOD = re.compile(
    r"\b(?:month|year|tax year|january|february|march|april|may|june|july|august|september|october|"
    r"november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b", re.I)


def _days_left_in_the_month_or_the_year(clean):
    """How much of the month or the year is still to come, counted from today.

    The count starts tomorrow, because that is what "left" means to someone looking at a
    calendar, and the answer says both numbers: "21 days left in November after today, 22
    counting today". Saying only the first would be short by one for anyone counting today in.
    A month that has not begun yet is counted to its last day instead, because "how many days
    left in December" said in November is a wait, not the length of a month that is not here.
    """
    import datetime
    text = _plain(clean)
    if not _REST_OF_A_PERIOD.search(text) or "how" not in text.split():
        return None
    words = re.findall(r"[a-z0-9]+", text)
    if any(word not in _REST_OF_A_PERIOD_WORDS for word in words):
        return None
    if not ({"left", "go", "remaining", "remain", "end"} & set(words)):
        return None
    today = datetime.date.today()
    unit = "weeks" if "weeks" in words or "week" in words else "days"
    month = None
    for number, name in enumerate(_MONTH_NAMES, start=1):
        if name.lower() in words or name[:3].lower() in words:
            month = number
    waiting = False
    extra = ""
    if "tax" in words:
        # The tax year runs from 6 April to 5 April, so it is a period of its own that the
        # calendar already knows: "how many days left in the tax year" is a count, not the
        # P60 card it used to get.
        end = datetime.date(today.year, 4, 5)
        if end < today:
            end = datetime.date(today.year + 1, 4, 5)
        said = "the tax year"
        extra = f" It ends on {_said_with_a_weekday(end)}."
    elif "year" in words:
        end = datetime.date(today.year, 12, 31)
        said = f"{today.year}"
    elif month is not None and month != today.month:
        year = today.year + (1 if month < today.month else 0)
        end = datetime.date(year + (month // 12), month % 12 + 1, 1) - datetime.timedelta(days=1)
        said = (f"{_MONTH_NAMES[end.month - 1]}: the last day of it is "
                f"{_said_with_a_weekday(end)}")
        waiting = True
    else:
        end = datetime.date(today.year + (today.month // 12), today.month % 12 + 1, 1)
        end -= datetime.timedelta(days=1)
        said = f"{_MONTH_NAMES[end.month - 1]}"
    days = (end - today).days
    if days <= 0:
        return (f"That is today - nothing left of {said} after today, and {_count_in(unit, 1)} "
                f"in all if you count it.")
    if waiting:
        return (f"{_count_in(unit, days)} until the end of {said}. "
                f"That is {_count_in(unit, days + 1)} counting today.")
    return (f"{_count_in(unit, days)} left in {said} after today, "
            f"{_count_in(unit, days + 1)} counting today." + extra)


# "how many days since 3 march", "how long ago was the 3rd": the count runs backwards, to the
# last time the day came round, which is the opposite of every count above.
_SINCE_ASK = re.compile(
    r"(?:how many\s+(?P<unit>days?|weeks?)\s+(?:has it been\s+|have passed\s+)?"
    r"(?:since|ago\s+was)"
    r"|how long\s+(?:has it been\s+)?(?:since|ago\s+was))", re.I)
_SINCE_FILLER = re.compile(r"\b(?:was|is|it|the|on|of|now|already|today|date|day)\b", re.I)
_A_YEAR_IN_THE_LINE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")


def _year_the_line_gave(text):
    """"How long ago was 3 March 2020" names a year, and the year is half the question.

    Without it the count runs back to the last time the day came round, which for a date years
    back is a confident number about the wrong year - worse than saying nothing. So a year in
    the line is read, used, and put in the answer.
    """
    found = _A_YEAR_IN_THE_LINE.search(text or "")
    return int(found.group(1)) if found else None


def _how_long_ago(clean):
    """The days between a date the line gives and today, counting backwards.

    "How long ago was 3 March" is the same arithmetic as a countdown with the sign turned
    round, and the answer says which weekday it was, because that is how people place a date
    they half remember.
    """
    import datetime
    text = _plain(clean)
    found = _SINCE_ASK.search(text)
    if not found:
        return None
    rest = (text[:found.start()] + " " + text[found.end():]).strip()
    rest = " ".join(_SINCE_FILLER.sub(" ", rest).split())
    if not rest:
        return None
    year = _year_the_line_gave(rest)
    when, said = _date_the_line_gave(rest)
    if when is None:
        when, said = _a_known_day_that_has_gone(rest, year)
    elif year is not None:
        try:
            when = when.replace(year=year)
        except ValueError:  # 29 February in a year that has none
            return None
        said = f"{said} {year}"
    if when is None:
        return None
    today = datetime.date.today()
    if when > today:
        if year is not None:  # a year that has not happened yet is not a time ago
            return None
        try:
            when = when.replace(year=when.year - 1)
        except ValueError:
            return None
    days = (today - when).days
    unit = (found.groupdict().get("unit") or "days").lower()
    if days == 0:
        return f"That was today - {said} is today, so no days ago at all."
    count = _count_in(unit, days)
    if days >= 1000 and unit.startswith("day"):
        count = f"{days:,} days"
    return f"{count} since {said} - that was a {_WEEKDAYS[when.weekday()]}."


# --- working days, and weekends, between today and a day ---------------------
# "how many working days until christmas" is the count a person does when they are planing a
# job, a move or a handover: the days that are not weekends and not bank holidays. "How many
# weekends until christmas" is the same idea the other way round, and both need a date, which
# the line either gives or the bot already knows.
_WORKING_ASK = re.compile(
    r"(?P<count>how many\s+(?:(?:working|work|business)\s+days?|weekends?))\s+"
    r"(?:are there\s+|are left\s+|is it\s+|do i have\s+|left\s+|to go\s+)?"
    r"(?:until|till|to|before)\s+(?P<rest>.+)", re.I)
_WORKING_LEFT = re.compile(
    r"(?P<count>how many\s+(?:(?:working|work|business)\s+days?|weekends?))\s+"
    r"(?:are\s+|is\s+|have i got\s+)?(?:left|to go)\s+(?:in\s+|of\s+)?"
    r"(?:the\s+|this\s+)?(?P<period>year|month)", re.I)


def _a_known_day_the_line_names_next(text):
    """The next time the day the line names comes round, as a date and how to say it."""
    import datetime
    today = datetime.date.today()
    if re.search(_CHRISTMAS_DAY + r"\b", text):
        eve = bool(re.search(r"\beve\b", text))
        when = datetime.date(today.year, 12, 24 if eve else 25)
        if when < today:
            when = datetime.date(today.year + 1, 12, 24 if eve else 25)
        return when, ("Christmas Eve" if eve else "Christmas")
    if re.search(r"\bnew year(?:'s|s')? (?:day|eve)\b|\bnew year\b", text):
        when = datetime.date(today.year, 1, 1)
        if when < today:
            when = datetime.date(today.year + 1, 1, 1)
        return when, "New Year's Day"
    if re.search(r"\beaster\b", text):
        when = _easter_sunday(today.year)
        if when < today:
            when = _easter_sunday(today.year + 1)
        return when, "Easter Sunday"
    return _date_the_line_gave(text)


# "how many working hours in a week" is the job's week, not the calendar's: 37.5 or 40 hours.
# The plain unit rows answer "how many hours in a week" with 168 and "how many days in a week"
# with 7, and they are right to; the word "working" is what makes it a question about work.
# `_plain` drops that word as filler, so this reads the line before the filler goes.
_WORKING_SHAPE = re.compile(
    r"(?:how many|what is|whats|what's|what are) (?:the )?(?P<which>working|work) "
    r"(?P<unit>hours?|days?)(?: in| per| to| into| a| of)?(?: a| the| one)? (?P<week>week|day|month)"
    r"(?: is (?:full|normal) time)?(?: of work)?", re.I)


def _a_working_week(clean):
    said = " ".join(str(clean or "").lower().strip().strip("?.!").split())
    found = _WORKING_SHAPE.fullmatch(said)
    if not found:
        return None
    unit, span = found.group("unit"), found.group("week")
    if unit.startswith("hour") and span == "week":
        return ("A full-time week is usually 37.5 to 40 hours - 7.5 or 8 hours a day over five "
                "days. The law caps the average at 48 hours a week over 17 weeks unless the "
                "person signs to opt out, and part-time hours are usually written as a share of "
                "that full-time week.")
    if unit.startswith("hour") and span == "day":
        return ("A full-time day is usually 7.5 or 8 hours, and a break of 20 minutes after six "
                "hours is the legal minimum in the UK. Contracted hours are the ones that count "
                "for pay, so check the contract rather than the rota.")
    if unit.startswith("day") and span == "week":
        return ("Five, for a full-time job - Monday to Friday - which is why a week off is five "
                "days of leave, not seven. Shift work and four-day weeks are the usual "
                "exceptions, and the contract says which one you are on.")
    return None


def _working_days_or_weekends_until(clean):
    """The weekdays, or the whole weekends, between tomorrow and the day the line names.

    A bank holiday is not a working day, so the England and Wales calendar comes out of it (the
    line can say Scotland or Northern Ireland, and then that list is used). Weekends are counted
    whole: a Saturday whose Sunday is the day itself is not a weekend off before it.
    """
    import datetime
    text = _plain(clean)
    today = datetime.date.today()
    if re.fullmatch(r"how many (?:working|work|business) days? (?:in|per) a year", text):
        return ("About 253 working days in a year: 261 weekdays, less the 8 bank holidays in "
                "England and Wales. Leap years add one.")
    # "how many working hours in a week" is 37.5 or 40, not the 168 hours a week has: the
    # plain hours row answers the calendar question and this one the job.
    if re.fullmatch(r"how many (?:working|work) hours? (?:in|per|to) (?:a|the) week", text):
        return ("A full-time week is usually 37.5 to 40 hours - 7.5 or 8 hours a day, five days. "
                "The law caps the average at 48 hours a week over 17 weeks unless the person "
                "signs to opt out, and part-time hours are usually written as a share of the "
                "full-time week.")
    if re.fullmatch(r"how many weekends (?:in|per) a year", text):
        return ("104 weekend days in a year - 52 Saturdays and 52 Sundays - plus a day or two "
                "in most years, because 365 is not a whole number of weeks.")
    found = _WORKING_ASK.fullmatch(text) or _WORKING_LEFT.fullmatch(text)
    if not found:
        return None
    weekends = "weekend" in found.group("count").lower()
    rest = (found.groupdict().get("rest") or "").strip()
    period = found.groupdict().get("period") or ""
    if rest:
        end, said = _a_known_day_the_line_names_next(rest)
        if end is None:
            # "until the end of the year" is a stretch of calendar, not a day; anything else
            # ("until my holiday", "until payday") is a date only the person has, so it passes.
            if not re.search(r"\b(?:the\s+|this\s+)?(year|month)\b", rest, re.I):
                return None
            period = "month" if re.search(r"\bmonth\b", rest, re.I) else "year"
    if not rest or end is None and period:
        if period == "month":
            end = datetime.date(today.year + (today.month // 12), today.month % 12 + 1, 1)
            end -= datetime.timedelta(days=1)
            said = f"the end of {_MONTH_NAMES[end.month - 1]}"
        else:
            end = datetime.date(today.year, 12, 31)
            said = f"the end of {today.year}"
    days = (end - today).days
    if days <= 0:
        return None
    span = [today + datetime.timedelta(days=step) for step in range(1, days + 1)]
    if weekends:
        count = sum(1 for day in span
                    if day.weekday() == 5 and day + datetime.timedelta(days=1) < end)
        if not count:
            return (f"There is no whole weekend between today and {said} - the next Saturday "
                    f"falls on {_said_with_a_weekday(end)} or later.")
        first = next(day for day in span if day.weekday() == 5)
        return (f"{count} weekend{'' if count == 1 else 's'} until {said}, the first starting "
                f"on {_said_with_a_weekday(first)}.")
    where, _ = _bank_where(rest or text)
    holidays = set()
    for year in {day.year for day in span} | {end.year}:
        holidays |= {day for _name, day in _bank_holidays(year, where)}
    count = sum(1 for day in span if day.weekday() < 5 and day not in holidays)
    return f"{count} working days until {said}, out of {days} days in all."




def _a_known_day_that_has_gone(text, year=None):
    """The last time a day the bot knows came round, for a count backwards.

    "How long ago was Christmas" names a fixed date, so it can be counted the same way as a date
    the line gives. Easter moves, so it is worked out from its own rule. A year in the line
    ("Christmas 2019") is that year's Christmas, not the last one.
    """
    import datetime
    today = datetime.date.today()
    tail = f" {year}" if year else ""
    named = re.search(_CHRISTMAS_DAY + r"\b", text)
    if named:
        when = datetime.date(year or today.year, 12, 25)
        if year is None and when > today:
            when = datetime.date(today.year - 1, 12, 25)
        return when, f"Christmas Day{tail}"
    if re.search(r"\bnew year(?:'s|s')? (?:day|eve)\b|\bnew year\b", text):
        when = datetime.date(year or today.year, 1, 1)
        if year is None and when > today:
            when = datetime.date(today.year - 1, 1, 1)
        return when, f"New Year's Day{tail}"
    if re.search(r"\beaster (?:sunday|day)\b|\beaster\b", text):
        when = _easter_sunday(year or today.year)
        if year is None and when > today:
            when = _easter_sunday(today.year - 1)
        return when, f"Easter Sunday{tail}"
    return None, None


def _days_until_easter(clean):
    """When Easter and the days around it fall, only when the line asks for the date.

    "When is Easter" is a date question; "what should I cook for Easter" is a cooking one.
    "Is Easter late this year" asks where the date falls rather than for the day itself, so it
    gets the day and the judgement together: Easter can fall anywhere from 22 March to 25 April,
    and "late" means nothing without that range. The whole cleaned line has to be the date
    question, so a mention in passing never counts. Because the day moves, it is worked out from
    the rule each time rather than typed in.
    """
    import datetime
    text = _plain(clean)
    for subject, offset, name in _EASTER_OFFSETS:
        asked = (rf"(?:(?:{_ASK_DATE})\s+(?:the\s+)?(?:{subject})"
                 rf"(?:\s+(?:start|starts|begin|begins))?"
                 rf"|(?:{subject})\s+(?:date|dates|20\d{{2}}))")
        # "how many days until easter" is the same day, asked as a wait.
        waiting = (rf"(?:how many |how long |how much longer )?(?:days?|weeks?|sleeps?) "
                   rf"(?:is it |are there |left |to go |still )?"
                   rf"(?:until|till|to|before) (?:the\s+)?(?:{subject})")
        # "is easter early or late this year", "is easter late this year": the ends of one scale
        # about the date, which the calendar can place inside the range Easter falls in.
        # The year can come before the judgement ("is easter next year late") or after it
        # ("is easter late this year"), so it is allowed in both places.
        judging = (rf"(?:(?:is|was|will)|(?:{_ASK_DATE}))\s*(?:the\s+)?(?:{subject})\s+"
                   rf"(?:going to be\s+)?"
                   rf"(?:(?:next year|this year|next easter|this easter|(?:in )?20\d{{2}})\s+)?"
                   rf"(?:(?:early|late)\s+or\s+(?:early|late)"
                   rf"|early|late|on the early side|on the late side)")
        counting = bool(re.fullmatch(waiting + _DATE_TAIL, text))
        where = bool(re.fullmatch(judging + _DATE_TAIL, text))
        if not counting and not where and not re.fullmatch(asked + _DATE_TAIL, text):
            continue
        year, named, today = _feast_year(text)
        day = _easter_sunday(year) + datetime.timedelta(days=offset)
        if day < today and not named and not re.search(r"\bthis (?:year|easter)\b", text):
            day = _easter_sunday(year + 1) + datetime.timedelta(days=offset)
        said = f"{day.day} {_MONTH_NAMES[day.month - 1]}"
        if where:
            # Easter Sunday can fall on any Sunday from 22 March to 25 April, so each feast has
            # the same range shifted by its own distance from Easter.
            # The range belongs to the year the answer is in: asked in November, Easter has
            # gone, so the answer is next year's date and next year's range.
            first = datetime.date(day.year, 3, 22) + datetime.timedelta(days=offset)
            last = datetime.date(day.year, 4, 25) + datetime.timedelta(days=offset)
            span = f"{first.day} {_MONTH_NAMES[first.month - 1]} to {last.day} {_MONTH_NAMES[last.month - 1]}"
            tense = "was" if day < today else "is"
            if day <= first + datetime.timedelta(days=9):
                sense = "early"
            elif day >= last - datetime.timedelta(days=9):
                sense = "late"
            else:
                return (f"{name} {tense} on {said}, which is about the middle of the range it can "
                        f"fall in ({span}) - neither early nor late.")
            return (f"{name} {tense} on {said}, which is {sense}: it can fall anywhere from {span}.")
        if counting and not named and day >= today:
            days = (day - today).days
            if days == 0:
                return f"{name} is today."
            return f"{days} days until {name}."
        if named:
            return f"{name} is on {said} {day.year}."
        days = (day - today).days
        if days == 0:
            return f"{name} is today."
        if days < 0:
            ago = -days
            return f"{name} this year was on {said}, {ago} day{'' if ago == 1 else 's'} ago."
        return f"{name} is on {said}, {days} days away."
    return None


# --- the days people ask the date of, by name ------------------------------


def _nth_weekday(year, month, weekday, nth):
    """The nth weekday of a month: Father's Day is the third Sunday in June."""
    import datetime
    day = datetime.date(year, month, 1)
    day += datetime.timedelta(days=(weekday - day.weekday()) % 7)
    return day + datetime.timedelta(days=7 * (nth - 1))


# The named days whose date the calendar knows, in the words people use for them, with the rule
# that gives the date. Before this, "when is mothers day" was answered with a present suggestion
# (the gift entry owns the words and nothing else answered the ask) and "when is valentines day"
# with "I don't know enough to answer that honestly" - both are dates a friend knows.
#   ("fixed", month, day)             never moves
#   ("easter", offset)                hangs off Easter Sunday
#   ("nth", month, weekday, n)        the nth weekday of a month
_NAMED_DAYS = (
    (("valentines day", "valentine's day", "valentines"), ("fixed", 2, 14), "Valentine's Day", ""),
    (("halloween", "hallowe'en"), ("fixed", 10, 31), "Halloween", ""),
    (("bonfire night", "guy fawkes night", "guy fawkes"), ("fixed", 11, 5), "Bonfire Night", ""),
    # "the day before christmas" and "the day after christmas" are the same two days said the
    # long way, and they were a punt and a Christmas film respectively.
    (("christmas eve", "xmas eve", "day before christmas"), ("fixed", 12, 24), "Christmas Eve",
     ""),
    (("boxing day", "day after christmas"), ("fixed", 12, 26), "Boxing Day", ""),
    (("new years eve", "new year's eve", "hogmanay", "day before new year",
      "day before new years day", "day before new year's day"), ("fixed", 12, 31),
     "New Year's Eve", ""),
    (("new years day", "new year's day"), ("fixed", 1, 1), "New Year's Day", ""),
    # Mothering Sunday is the fourth Sunday of Lent, which is three weeks before Easter Sunday;
    # "mothers day" is what most people type for it here.
    (("mothering sunday", "mothers day", "mother's day"), ("easter", -21), "Mothering Sunday",
     " That is the UK date; the American Mother's Day is a Sunday in May."),
    (("fathers day", "father's day"), ("nth", 6, 6, 3), "Father's Day", ""),
)


def _named_day_date(clean):
    """When one of the days above falls: "when is mothers day", "how many days until halloween".

    The whole cleaned line has to be the date question for that day, so "what do i write in a
    mothers day card" and "do bank holidays count towards my holiday" never land here. A year in
    the line is answered with that year's date; without one, a day that has already gone this year
    is answered as next year's, the way the Christmas countdown does it.
    """
    import datetime
    text = _plain(clean)
    for words, rule, name, extra in _NAMED_DAYS:
        subject = "|".join(words)
        asked = rf"(?:{_ASK_DATE})\s+(?:the\s+)?(?:{subject})"
        waiting = (rf"(?:how many |how long )?(?:days?|weeks?|sleeps?) "
                   rf"(?:is it |are there |left |to go )?(?:until|till|to|before) "
                   rf"(?:the\s+)?(?:{subject})")
        counting = bool(re.fullmatch(waiting + _DATE_TAIL, text))
        if not counting and not re.fullmatch(asked + _DATE_TAIL, text):
            continue
        year, named_year, today = _feast_year(text)
        if rule[0] == "fixed":
            when = datetime.date(year, rule[1], rule[2])
        elif rule[0] == "easter":
            when = _easter_sunday(year) + datetime.timedelta(days=rule[1])
        else:
            when = _nth_weekday(year, rule[1], rule[2], rule[3])
        if when < today and not named_year and "this year" not in text:
            if rule[0] == "fixed":
                when = datetime.date(year + 1, rule[1], rule[2])
            elif rule[0] == "easter":
                when = _easter_sunday(year + 1) + datetime.timedelta(days=rule[1])
            else:
                when = _nth_weekday(year + 1, rule[1], rule[2], rule[3])
        said = f"{when.day} {_MONTH_NAMES[when.month - 1]}"
        if named_year:
            return f"{name} is on {said} {when.year}.{extra}"
        days = (when - today).days
        if days == 0:
            return f"{name} is today.{extra}"
        if counting:
            return f"{days} days until {name}."
        if days < 0:
            return f"{name} this year was on {said}, {-days} days ago.{extra}"
        return f"{name} is on {said}, {days} days away.{extra}"
    return None


# --- a count to a month, a season, or the turn of the year -------------------
#
# "how many days until december", "how long till the summer", "how long until new year": the
# wait is the whole question and the calendar already knows the day it ends, so the answer is
# arithmetic rather than a fact to look up. None of these lines holds a date, which is why the
# counts above leave them alone: a bare month is not a day, and a season is a stretch of the year
# rather than one date. Before this they got "That's beyond what I know well", or - for new year -
# a plan to make a resolution, which answers a different question.
#
# Narrow on purpose: the whole line has to be the countdown, and the thing waited for has to be
# one of these words with nothing else said about it, so "how long until june exams", "how many
# days until december payday" and "how long until the summer holidays" are left to whatever else
# answers them: a school holiday, a payday or an exam season moves by council, employer and
# school, and nothing here knows those dates.
_SEASONS = (
    # the words people use, the first day of the season, its last month, and that month's name
    (("spring",), (3, 1), 5),
    (("summer",), (6, 1), 8),
    (("autumn", "fall"), (9, 1), 11),
    (("winter",), (12, 1), 2),
)

# A month named on its own, or the turn of the year, with the only words that can sit around it
# without turning the line into a different question.
_COUNTED_SUBJECT_TAIL = r"(?:\s+(?:now|again|yet|please|roughly|this year|next year|20\d{2}))*"
_THE_TURN_OF_THE_YEAR = ("new year", "new years", "new year's", "the new year",
                         "new year's day", "new years day", "new year's eve", "new years eve",
                         "hogmanay")


def _days_until_a_month_or_season(clean):
    """The countdown to a bare month, a season, or New Year, or None.

    The count is to the first day of what was named - December starts on 1 December, summer on
    1 June - and it is said in the unit the line asked for, the same way the Christmas countdown
    replies in weeks when it is asked in weeks. A month or season that has already started this
    year counts to the next turn of it, because "how many days until december" asked on the 4th
    of December is about the next December and not about a date three days behind.
    """
    import datetime
    text = _plain(clean)
    found = re.fullmatch(_COUNT_ASK, text, re.I)
    if not found:
        return None
    rest = (found.groupdict().get("rest") or found.groupdict().get("rest2") or "").strip()
    rest = re.sub(r"^(?:the|my|our)\s+", "", rest, flags=re.I)
    rest = re.sub(r"\s+(?:please|then|now|exactly|roughly|again|yet)$", "", rest, flags=re.I)
    # "how long until september starts" is the same wait as "how long until september".
    rest = re.sub(r"\s+(?:start|starts|begin|begins|come|comes|arrive|arrives|get here)$", "",
                  rest, flags=re.I)
    if not rest or re.search(r"\b(?:holiday|holidays|break|term|half term|exam|exams|payday|pay "
                             r"day|deadline|due|start|starts|begin|begins|end|ends)\b", rest,
                            re.I):
        return None
    today = datetime.date.today()
    unit = (found.groupdict().get("unit") or "days").lower()
    # The turn of the year, asked as a wait: the next 1 January, or the eve of it.
    if rest in _THE_TURN_OF_THE_YEAR:
        eve = "eve" in rest
        when = datetime.date(today.year, 12, 31) if eve else datetime.date(today.year, 1, 1)
        if when < today:
            when = datetime.date(when.year + 1, when.month, when.day)
        days = (when - today).days
        name = "New Year's Eve" if eve else "New Year's Day"
        said = f"{when.day} {_MONTH_NAMES[when.month - 1]}"
        if days == 0:
            return f"{name} is today, {said}."
        # New year is said as the day people mean - the 1st - with the eve named where it is
        # the night people are counting to.
        after = " New Year's Eve is the night before it." if not eve else ""
        return f"{_count_in(unit, days, when)} until {name} - it is {said}.{after}"
    # A season is a stretch of the year, so a season already running is answered as running
    # rather than counted down to: "how long till summer" in July is not "338 days".
    for words, (month, day), last_month in _SEASONS:
        if rest not in words:
            continue
        start = datetime.date(today.year, month, day)
        end = datetime.date(today.year, last_month, MONTHS[_MONTH_NAMES[last_month - 1].lower()])
        if end < start:  # winter runs over the turn of the year
            end = datetime.date(today.year + 1, last_month,
                                MONTHS[_MONTH_NAMES[last_month - 1].lower()])
        name = rest.capitalize()
        if start <= today <= end:
            return (f"{name} is here now - it runs to the end of "
                    f"{_MONTH_NAMES[end.month - 1]}. "
                    f"The next one starts on {start.day} {_MONTH_NAMES[start.month - 1]} "
                    f"next year.")
        if start < today:
            start = datetime.date(today.year + 1, month, day)
        days = (start - today).days
        return (f"{_count_in(unit, days, start)} until {name} - it starts on "
                f"{start.day} {_MONTH_NAMES[start.month - 1]}.")
    # A year on its own is a date too: "how many days until 2027" is the count to 1 January,
    # which the calendar knows, and it was a punt before. A year that has already started is not
    # a countdown at all, so it stands down rather than answering with a negative number.
    year_said = re.fullmatch(r"(?:(?:the\s+)?year\s+)?(20\d{2}|21\d{2})", rest)
    if year_said:
        year = int(year_said.group(1))
        when = datetime.date(year, 1, 1)
        if when <= today:
            return None
        days = (when - today).days
        return (f"{_count_in(unit, days, when)} until {year} - it starts on "
                f"{when.day} {_MONTH_NAMES[when.month - 1]} {year}.")
    # A month on its own: the turn of it, not a day inside it.
    month = _month_number(rest)
    if month is None and rest in [name[:3] for name in _MONTHS_SAID]:
        month = [name[:3] for name in _MONTHS_SAID].index(rest) + 1
    if month is None:
        return None
    when = datetime.date(today.year, month, 1)
    next_year = False
    if when < today:
        when = datetime.date(today.year + 1, month, 1)
        next_year = True
    days = (when - today).days
    label = _MONTH_NAMES[month - 1] + (" next year" if next_year else "")
    return (f"{_count_in(unit, days, when)} until {label} - it starts on "
            f"{when.day} {_MONTH_NAMES[when.month - 1]}"
            f"{' ' + str(when.year) if next_year else ''}.")


# --- the bank holidays ------------------------------------------------------
#
# Eight days a year in England and Wales, and all eight are computable: two hang off Easter, three
# are the first or last Monday of a month, and three are fixed dates that move to the next weekday
# when they land on a weekend. Before this, "when is the next bank holiday" was answered with
# "Nothing so far - you haven't mentioned anything coming up", which is the wrong kind of reply to
# a question about the calendar, and the countdown "how many days until the next bank holiday" had
# no answer at all. A person asking either of those wants one date, and then the one after it.
_BANK_HOLIDAY_TAIL = (r"(?:\s+(?:in\s+)?(?:england|wales|scotland|scottish|"
                      r"northern ireland|england and wales|the uk|the united kingdom|britain|edinburgh|"
                      r"glasgow|belfast|here|then|now|please|left|to go|coming up|off|in a row|weekend|"
                      r"in\s+20\d\d|this year|next year))*")
_BANK_HOLIDAY_NEXT = re.compile(
    rf"(?:when|what|whats|what's|which)(?:'s| is|s| are| will it be)?\s+(?:the\s+)?"
    rf"(?:next|coming|nearest|first)\s+(?:bank|public)\s+holiday(?:s)?"
    rf"(?:\s+(?:after this one|after that|after|next))?{_BANK_HOLIDAY_TAIL}")
_BANK_HOLIDAY_COUNT = re.compile(
    rf"(?:how many|how long)\s+(?:days?|weeks?|sleeps?)\s+(?:is it |are there |left |to go )?"
    rf"(?:until|till|to|before)\s+(?:the\s+)?(?:next\s+)?(?:bank|public)\s+holiday"
    rf"{_BANK_HOLIDAY_TAIL}")
_BANK_HOLIDAY_LIST = re.compile(
    rf"(?:when|what)(?:'s| are| is)?\s+(?:the\s+|all\s+the\s+)?(?:bank|public)\s+holidays?"
    rf"(?:\s+(?:this year|next year|in\s+20\d\d|left|left this year|this coming year|"
    rf"which are left|are left|coming up))?{_BANK_HOLIDAY_TAIL}")


# "What day is the 24th of December" is a calendar question with the answer in it, and every
# form of it was a punt: "what day is the 24th", "what day is it on the 24th", "what day does the
# 24th fall on", "what day is december 24th". The weekday a date falls on is worked out from the
# calendar, so it is never a guess. The month is optional; without one the answer gives this
# month's day and next month's, so a person's bare "the 24th" is covered either way.
_SAYS_WEEKDAY = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tues|tue|weds|wed|"
    r"thurs|thur|thu|fri|sat|sun)\b", re.I)
_MONTHS_OR = "|".join(sorted(list(_MONTHS_SAID) + list(_MONTH_SHORT), key=len, reverse=True))


def _ordinal(number):
    """24 -> "24th", 1 -> "1st", 22 -> "22nd"."""
    if 11 <= number % 100 <= 13:
        return f"{number}th"
    return f"{number}{('th', 'st', 'nd', 'rd')[min(number % 10, 4) % 4] if number % 10 < 4 else 'th'}"


def _the_weekday_of_a_date(clean):
    """The weekday a date falls on: "what day is the 24th of december".

    Only the whole line counts, so "i get paid on the 24th" stays a plan. A line that names a
    weekday as well ("is the 24th a friday") is a yes or no question and is left alone, as is a
    line asking how many days it is until a date, which the countdown answers.
    """
    import datetime
    text = _plain(clean)
    today = datetime.date.today()
    said = re.match(r"^(?:what|which)\s+(?:day|date|weekday)\s+(?:of\s+the\s+week\s+)?"
                    r"(?:is|was|will)\s+(?:it\s+)?(?:be\s+)?(?:on\s+)?(?:the\s+)?", text)
    if not said:
        said = re.match(r"^what\s+day\s+does\s+(?:the\s+)?", text)
    if not said:
        return None
    # "what day was the 3rd" asks backwards: the most recent one, not the next.
    backwards = bool(re.search(r"\bwas\b", said.group(0)))
    rest = text[said.end():].strip()
    rest = re.sub(r"\s+(?:fall|falls|land|lands)\s+on$", "", rest)
    year_said = None
    year_found = re.search(r"\s+(?:in\s+)?(20\d{2})$", rest)
    if year_found:
        year_said = int(year_found.group(1))
        rest = rest[:year_found.start()].strip()
    rest = re.sub(r"\s+(?:this|next)\s+year$", "", rest)
    if not rest or _SAYS_WEEKDAY.search(rest):
        return None
    found = (re.fullmatch(rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MONTHS_OR})", rest)
             or re.fullmatch(rf"({_MONTHS_OR})\s+(\d{{1,2}})(?:st|nd|rd|th)?", rest))
    if found:
        first, second = found.group(1), found.group(2)
        day, month = (int(first), second) if first.isdigit() else (int(second), first)
        if _month_number(month) is None:
            return None
        if year_said:
            try:
                when = datetime.date(year_said, _month_number(month), day)
            except ValueError:
                return None
            return f"{when.day} {when:%B} {when.year} is a {when:%A}."
        if backwards:
            when = None
            for years_back in range(2):
                try:
                    guess = datetime.date(today.year - years_back, _month_number(month), day)
                except ValueError:
                    continue
                if guess <= today:
                    when = guess
                    break
        else:
            when = _day_in_a_month(day, _month_number(month), today)
        if when is None:
            return None
        days = (when - today).days
        if days < 0:
            ago = -days
            return (f"{when.day} {when:%B} was a {when:%A}, {ago} day"
                    f"{'' if ago == 1 else 's'} ago.")
        if days == 0:
            return f"{when.day} {when:%B} is today, a {when:%A}."
        if days == 1:
            return f"{when.day} {when:%B} is tomorrow, a {when:%A}."
        return f"{when.day} {when:%B} is a {when:%A}, {days} days away."
    bare = re.fullmatch(rf"(\d{{1,2}})(?:st|nd|rd|th)?", rest)
    if not bare:
        return None
    day = int(bare.group(1))
    this_month = None
    for step in range(3):
        # forwards for "what day is the 31st" (past months have gone by), backwards for "what
        # day was the 3rd", which wants the one just gone
        shift = -step if backwards else step
        month = (today.month - 1 + shift) % 12 + 1
        year = today.year + (today.month - 1 + shift) // 12
        try:
            guess = datetime.date(year, month, day)
        except ValueError:
            continue
        if backwards and guess > today:
            continue
        if not backwards and guess < today:
            continue
        this_month = guess
        break
    if this_month is None:
        return None
    next_month = today.month % 12 + 1
    next_year = today.year + (1 if today.month == 12 else 0)
    try:
        following = datetime.date(next_year, next_month, day)
    except ValueError:
        following = None
    if backwards or following is None or (following.month == this_month.month
                                          and following.year == this_month.year):
        said_next = ""
    else:
        said_next = f", and the {_ordinal(day)} of next month is a {following:%A}"
    days = (this_month - today).days
    if days == 0:
        return f"Today is the {_ordinal(day)}, a {this_month:%A}{said_next}."
    month_said = "this month" if this_month.month == today.month else this_month.strftime("%B")
    if days < 0:
        ago = -days
        return (f"The {_ordinal(day)} of {month_said} was a {this_month:%A}, "
                f"{ago} day{'' if ago == 1 else 's'} ago.")
    return (f"The {_ordinal(day)} of {month_said} is a {this_month:%A}, "
            f"{days} days away{said_next}.")


def _the_wider_day(day, taken):
    """A fixed bank holiday that lands at the weekend is taken on the next free weekday."""
    import datetime
    while day.weekday() > 4 or day in taken:
        day += datetime.timedelta(days=1)
    return day


def _last_weekday(year, month, weekday):
    """The last weekday of a month: the summer bank holiday is the last Monday in August."""
    import datetime
    if month == 12:
        last = datetime.date(year, 12, 31)
    else:
        last = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    return last - datetime.timedelta(days=(last.weekday() - weekday) % 7)


def _bank_holidays(year, where="england"):
    """Every bank holiday in one year, as (name, date), in order.

    The three calendars are not the same list: Scotland has 2 January, St Andrew's Day and the
    first Monday of August rather than the last, and Northern Ireland has St Patrick's Day and the
    Battle of the Boyne. All of them are computable from the same pieces: the fixed dates (moved to
    the next free weekday when they land at a weekend), the two that hang off Easter, and the
    Mondays of a named week of a month.
    """
    import datetime
    easter = _easter_sunday(year)
    if where == "scotland":
        fixed_days = (("New Year's Day", 1, 1), ("2 January", 1, 2),
                      ("St Andrew's Day", 11, 30), ("Christmas Day", 12, 25),
                      ("Boxing Day", 12, 26))
    elif where == "northern ireland":
        fixed_days = (("New Year's Day", 1, 1), ("St Patrick's Day", 3, 17),
                      ("the Battle of the Boyne", 7, 12), ("Christmas Day", 12, 25),
                      ("Boxing Day", 12, 26))
    else:
        fixed_days = (("New Year's Day", 1, 1), ("Christmas Day", 12, 25),
                      ("Boxing Day", 12, 26))
    taken = set()
    rows = []
    for name, month, day in fixed_days:
        moved = _the_wider_day(datetime.date(year, month, day), taken)
        taken.add(moved)
        rows.append((name, moved))
    rows.append(("Good Friday", easter - datetime.timedelta(days=2)))
    if where != "scotland":
        rows.append(("Easter Monday", easter + datetime.timedelta(days=1)))
    rows.append(("the early May bank holiday", _nth_weekday(year, 5, 0, 1)))
    rows.append(("the spring bank holiday", _last_weekday(year, 5, 0)))
    if where == "scotland":
        rows.append(("the summer bank holiday", _nth_weekday(year, 8, 0, 1)))
    else:
        rows.append(("the summer bank holiday", _last_weekday(year, 8, 0)))
    return sorted(rows, key=lambda row: row[1])


# The three lists have their own names in the line, and the answer says which list it is reading.
_BANK_WHERE = (
    (re.compile(r"\bscotland\b|\bscottish\b|\bedinburgh\b|\bglasgow\b"), "scotland",
     "in Scotland"),
    (re.compile(r"\bnorthern ireland\b|\bbelfast\b|\bderry\b"), "northern ireland",
     "in Northern Ireland"),
)


def _bank_where(text):
    for pattern, where, said in _BANK_WHERE:
        if pattern.search(text):
            return where, said
    return "england", "in England and Wales"


def _said_with_a_weekday(when):
    import datetime
    return f"{_WEEKDAYS[when.weekday()]} {when.day} {_MONTH_NAMES[when.month - 1]}"


_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _next_bank_holiday(clean):
    """The next bank holiday, its countdown, or the year's list: "when is the next bank holiday"."""
    import datetime
    text = _plain(clean)
    asking = _BANK_HOLIDAY_NEXT.fullmatch(text)
    counting = _BANK_HOLIDAY_COUNT.fullmatch(text)
    listing = _BANK_HOLIDAY_LIST.fullmatch(text)
    if not (asking or counting or listing):
        return None
    year, named_year, today = _feast_year(text)
    where, told_where = _bank_where(text)
    rows = _bank_holidays(year, where)
    ahead = [row for row in rows if row[1] >= today]
    if not ahead:
        year += 1
        rows = _bank_holidays(year, where)
        ahead = rows
    when = ahead[0]
    after = ahead[1] if len(ahead) > 1 else _bank_holidays(year + 1, where)[0]
    days = (when[1] - today).days
    if listing and not asking and not counting:
        left = [row for row in rows if row[1] >= today]
        said = ", ".join(f"{name} on {_said_with_a_weekday(day)}" for name, day in left)
        if where != "england":
            return f"{told_where[:1].upper()}{told_where[1:]} the bank holidays left this year are {said}."
        return (f"In England and Wales the bank holidays left this year are {said}. "
                "Scotland and Northern Ireland keep a few of their own as well.")
    if days == 0:
        return (f"Today is a bank holiday {told_where}: {when[0][:1].upper()}{when[0][1:]}, "
                f"{_said_with_a_weekday(when[1])}. The next one after that is {after[0]} on "
                f"{_said_with_a_weekday(after[1])}.")
    if counting:
        return (f"{days} day{'' if days == 1 else 's'} until the next bank holiday {told_where}: "
                f"{when[0]} on {_said_with_a_weekday(when[1])}.")
    return (f"The next bank holiday {told_where} is {when[0]} on "
            f"{_said_with_a_weekday(when[1])}, {days} day{'' if days == 1 else 's'} away. "
            f"After that it is {after[0]} on {_said_with_a_weekday(after[1])}.")


# --- one unit in another: the fixed facts people ask for by name -----------

_POLITE = (r"(?:ok|okay|so|and|but|right|hi|hey|please|sorry|quick one|quick question|"
           r"can you tell me|do you know|tell me|just wondering|i was wondering|"
           r"wondering|out of interest)")
_FILLER = (r"(?:please|for me|thanks|thank you|exactly|roughly|about|approximately|again|"
           r"then|altogether|in total|by the way|actually)")


# --- Today's date, and the next Monday ---------------------------------------

# The days of the week, and the other ways people name each one.
_WEEKDAY_WORDS = (
    (r"monday|mon", 0, "Monday"),
    (r"tuesday|tues|tue", 1, "Tuesday"),
    (r"wednesday|weds|wed", 2, "Wednesday"),
    (r"thursday|thurs|thur|thu", 3, "Thursday"),
    (r"friday|fri", 4, "Friday"),
    (r"saturday|sat", 5, "Saturday"),
    (r"sunday|sun", 6, "Sunday"),
)
_MONTH_TITLE = ("January", "February", "March", "April", "May", "June", "July", "August",
                "September", "October", "November", "December")

_TODAY_ASK = (
    r"(?:what|whats|what's|which)\s+(?:is\s+)?(?:the\s+)?(?:day|date)"
    r"(?:\s+of\s+the\s+week)?(?:\s+(?:is\s+)?(?:it|today|now))?"
    r"|what\s+day\s+(?:is\s+it|are\s+we)(?:\s+on)?(?:\s+today)?"
    # "today's date" is how most people type it, apostrophe and all, and the curly one too
    r"|(?:what|whats|what's)?\s*(?:is\s+)?today[’']?s\s+(?:date|day)"
    r"|(?:what|whats|what's)\s+is\s+today\b(?:\s+(?:the\s+)?(?:date|day))?"
    r"|the\s+(?:date|day)(?:\s+today)?"
    r"|any\s+idea\s+what\s+day\s+it\s+is"
)


def _day_text(day):
    """A date the way a friend says it: the weekday first, then the day and the month."""
    return f"{day:%A}, {day.day} {_MONTH_TITLE[day.month - 1]}"


def _short_date(day):
    """Just the day and the month, for when the weekday is already in the sentence."""
    return f"{day.day} {_MONTH_TITLE[day.month - 1]}"


def _weekday_of(text, tail):
    """The weekday the line names, its index, and whether it said "next"."""
    for words, index, name in _WEEKDAY_WORDS:
        if re.fullmatch(rf"{tail}(?:(?:the|this|next|coming|on|a week on)\s+)*(?:{words})"
                        rf"(?:\s+(?:today|now|already|yet))*", text):
            return name, index, bool(re.search(r"\bnext\b", text))
    return None, None, False


def _today(clean):
    """Today's date, and when the next Monday is.

    "What day is it today" is arithmetic on the clock, not knowledge, so it is worked out
    rather than guessed: the bot already counts days to Christmas the same way. The whole
    cleaned line has to be the question, so "what day is christmas" stays a date question
    about Christmas and "what day suits you" stays a plan.
    """
    import datetime
    text = _plain(clean)
    today = datetime.date.today()

    if re.fullmatch(_TODAY_ASK, text):
        return f"It's {_day_text(today)}."

    # "is it friday today" asks for a yes or a no, not a date.
    name, index, _ = _weekday_of(text, r"is (?:it|today) (?:still )?")
    if name:
        if index == today.weekday():
            return f"Yes, it's {_day_text(today)}."
        return f"No, it's {_day_text(today)}."

    ask = (r"(?:how many (?:days?|sleeps?) (?:is it |are there |do i have )?"
           r"(?:until|till|til|to go before|before|to) |how long (?:until|till|til|to) "
           r"|what date is |what date is it on |what day is |what day is it on "
           r"|which date is |what day does |what date does "
           r"|what(?:'s|s| is) the date(?: of| on| next| this)? "
           r"|what(?:'s|s| is) the (?:day|date) of "
           r"|when(?:'s|s) |when is |when does )")
    name, index, next_one = _weekday_of(text, ask)
    if name:
        ahead = (index - today.weekday()) % 7
        if ahead == 0 and next_one:
            ahead = 7
        when = today + datetime.timedelta(days=ahead)
        if ahead == 0:
            return f"{name} is today, {_short_date(when)}."
        if ahead == 1:
            return f"{name} is tomorrow, {_short_date(when)}."
        if ahead == 7:
            return f"{name} is a week away, on {_short_date(when)}."
        return f"{name} is {ahead} days away, on {_short_date(when)}."
    return None


def _plain(clean):
    """The line without politeness and filler, so a question can be matched whole."""
    text = str(clean or "").strip().strip("?.!")
    text = re.sub(r"\s*[,;]\s*", " ", text)
    text = re.sub(rf"^(?:{_POLITE}\b[\s]+)+", "", text)
    text = re.sub(rf"\b{_FILLER}\b", " ", text)
    return " ".join(text.split())


_UNITS = {
    "second": ("second", "seconds", "sec", "secs"),
    "minute": ("minute", "minutes", "min", "mins"),
    "hour": ("hour", "hours", "hr", "hrs"),
    "day": ("day", "days"),
    "week": ("week", "weeks"),
    "month": ("month", "months"),
    "year": ("year", "years"),
    "ounce": ("ounce", "ounces", "oz"),
    "pound": ("pound", "pounds", "lb", "lbs"),
    "stone": ("stone", "stones"),
    "gram": ("gram", "grams", "g", "gr"),
    "kilogram": ("kilogram", "kilograms", "kilo", "kilos", "kg"),
    "centimetre": ("centimetre", "centimetres", "centimeter", "centimeters", "cm"),
    "inch": ("inch", "inches"),
    "metre": ("metre", "metres", "meter", "meters"),
    "foot": ("foot", "feet", "ft"),
    "mile": ("mile", "miles"),
    "pint": ("pint", "pints", "pt"),
    "millilitre": ("millilitre", "millilitres", "milliliter", "milliliters", "ml"),
    "litre": ("litre", "litres", "liter", "liters", "l"),
    "cup": ("cup", "cups"),
    "tablespoon": ("tablespoon", "tablespoons", "tbsp"),
    "teaspoon": ("teaspoon", "teaspoons", "tsp"),
}
_UNIT = {alias: name for name, aliases in _UNITS.items() for alias in aliases}

# How many of the first unit go into one of the second. The answer is written out, not
# calculated from a factor, so each one can say the thing a person actually wants to know.
FACTS = {
    ("second", "minute"): "There are 60 seconds in a minute.",
    ("minute", "hour"): "There are 60 minutes in an hour.",
    ("hour", "day"): "There are 24 hours in a day.",
    ("day", "week"): "There are 7 days in a week, so a fortnight is 14.",
    ("hour", "week"): "There are 168 hours in a week: 7 days × 24 hours.",
    ("minute", "day"): "There are 1,440 minutes in a day: 24 hours × 60 minutes.",
    ("second", "day"): "There are 86,400 seconds in a day: 24 × 60 × 60.",
    ("second", "year"): ("There are 31,536,000 seconds in an ordinary year (365 × 24 × 60 × 60), "
                          "and 31,622,400 in a leap year."),
    ("minute", "year"): ("There are 525,600 minutes in an ordinary year, and 527,040 in a leap "
                          "year."),
    ("hour", "year"): "There are 8,760 hours in an ordinary year, and 8,784 in a leap year.",
    ("week", "year"): ("There are 52 weeks and 1 day in an ordinary year (52 weeks and 2 days "
                         "in a leap year), or about 52.14 weeks if you divide 365 by 7."),
    ("day", "year"): ("An ordinary year has 365 days; a leap year has 366, with 29 February. "
                        "Leap years come every four years, except most century years."),
    ("month", "year"): "There are 12 months in a year, from January to December.",
    ("ounce", "pound"): "There are 16 ounces in a pound, and 14 pounds in a stone.",
    ("pound", "stone"): "There are 14 pounds in a stone.",
    ("gram", "kilogram"): ("There are 1,000 grams in a kilogram, and 1,000 kilograms in a "
                            "tonne."),
    ("gram", "ounce"): "There are about 28.35 grams in an ounce, so 100g is about 3.5oz.",
    ("pound", "kilogram"): ("There are about 2.2 pounds in a kilogram, so 70kg is about 154lb "
                             "and 1lb is about 0.45kg."),
    ("centimetre", "metre"): "There are 100 centimetres in a metre, and 1,000 metres in a kilometre.",
    ("centimetre", "inch"): "There are 2.54 centimetres in an inch, so 30cm is just under 12 inches.",
    ("inch", "foot"): "There are 12 inches in a foot, and 3 feet in a yard.",
    ("foot", "mile"): "There are 5,280 feet in a mile, which is 1,760 yards.",
    ("millilitre", "litre"): "There are 1,000 millilitres in a litre.",
    ("millilitre", "cup"): ("A US cup is about 240ml and a UK cup is 250ml, so half a cup is "
                              "around 120ml."),
    ("gram", "cup"): ("It depends what you're measuring: a cup is about 120g of flour, 200g of "
                       "sugar, 225g of butter or 185g of rice."),
    ("millilitre", "tablespoon"): ("A tablespoon is 15ml and a teaspoon is 5ml, so three "
                                    "teaspoons make a tablespoon."),
    ("millilitre", "pint"): "A UK pint is 568ml and a US pint is 473ml, so a UK pint is just over half a litre.",
    ("pint", "litre"): "There are about 1.76 UK pints in a litre, or 2.1 US pints.",
    ("teaspoon", "tablespoon"): ("Three teaspoons make a tablespoon, and a tablespoon is 15ml "
                                  "against a teaspoon's 5ml."),
}


# "how many grams in an ounce": the counted unit, then the unit it goes into.
_AMOUNT = r"(?:how many|number of)\s+([a-z']+)\s+(.*)"
_TAILS = (
    r"(?:are there |is there |are |is )?(?:in|to|per) (?:a |an |one |1 )?([a-z']+)(?: of .*)?",
    r"(?:does|do) (?:a |an |one )?([a-z']+)(?: have| contain| make up)?",
    r"(?:is|are) (?:a |an |one |1 )?([a-z']+)(?: of .*)?",
    r"([a-z']+) (?:has|have)(?: how many)?",
)
# "how much is a kilo in grams", "how much is a cup in ml"
_HOW_MUCH = (r"how much (?:is |are )?(?:a |an |one |1 )?([a-z']+)(?: of [a-z]+)? (?:in|to) "
             r"(?:a |an |one |1 )?([a-z']+)(?: of .*)?")


# "how heavy is a stone", "how much does a pound weigh": the weight of one unit on its own,
# which is not a conversion, so the FACTS table never saw it. On main these were a punt
# ("how heavy is an ounce", "what does a kilogram weigh"), a live-price hedge ("how much does
# a pound weigh", "how much is a stone") and, for "how heavy is a kilo", the lose-weight plan -
# because "kilo" is in the diet row's key. The answer is the unit written out in the others,
# which is the same fact the conversions use, so it lives here beside them.
HOW_HEAVY = {
    "stone": ("A stone is 14 pounds, which is about 6.35kg: 10 stone is 63.5kg and 12 stone is "
              "about 76kg."),
    "stones": ("A stone is 14 pounds, which is about 6.35kg: 10 stone is 63.5kg and 12 stone is "
               "about 76kg."),
    "pound": "A pound is 16 ounces, about 454g, and 14 pounds make a stone.",
    "pounds": "A pound is 16 ounces, about 454g, and 14 pounds make a stone.",
    "lb": "A pound is 16 ounces, about 454g, and 14 pounds make a stone.",
    "lbs": "A pound is 16 ounces, about 454g, and 14 pounds make a stone.",
    "ounce": "An ounce is about 28.35g, and there are 16 ounces in a pound.",
    "ounces": "An ounce is about 28.35g, and there are 16 ounces in a pound.",
    "oz": "An ounce is about 28.35g, and there are 16 ounces in a pound.",
    "kilo": "A kilo is 1,000 grams, which is about 2.2 pounds: 70kg is about 11 stone.",
    "kilos": "A kilo is 1,000 grams, which is about 2.2 pounds: 70kg is about 11 stone.",
    "kilogram": "A kilo is 1,000 grams, which is about 2.2 pounds: 70kg is about 11 stone.",
    "kilograms": "A kilo is 1,000 grams, which is about 2.2 pounds: 70kg is about 11 stone.",
    "kg": "A kilo is 1,000 grams, which is about 2.2 pounds: 70kg is about 11 stone.",
    "gram": "A gram is a thousandth of a kilo. A paperclip or a sachet of sugar is about a gram.",
    "grams": "A gram is a thousandth of a kilo. A paperclip or a sachet of sugar is about a gram.",
    "g": "A gram is a thousandth of a kilo. A paperclip or a sachet of sugar is about a gram.",
    "tonne": "A tonne is 1,000kg, which is about 2,205 pounds.",
    "tonnes": "A tonne is 1,000kg, which is about 2,205 pounds.",
    "ton": ("A ton is 1,016kg in the UK and 907kg in the US; a tonne, spelled with the e, is "
            "1,000kg."),
    "tons": ("A ton is 1,016kg in the UK and 907kg in the US; a tonne, spelled with the e, is "
             "1,000kg."),
}

# The whole line has to be the question, for the same reason as the conversions: "how heavy is
# a bag of sugar" is answered by its own row, and "how much does a share weigh on my mind" is
# not about a unit at all.
_HEAVY = re.compile(r"(?:how (?:heavy|much) (?:is|does|do|are)|what (?:does|is)|"
                    r"how much does)\s+(?:a |an |one |1 )?([a-z']+?)\s*"
                    r"(?:weigh(?:s)?|weigh in at|in weight)?\s*(?:in kilos|in kg|in pounds|"
                    r"in pounds and ounces|in lbs)?")


def _unit_pair(counted, of_unit):
    """The fact for this pair, whichever way round the question asked it."""
    return FACTS.get((counted, of_unit)) or FACTS.get((of_unit, counted))


def _unit_fact(clean):
    """How many of one unit make another, when that is the question asked.

    The question has to be the whole line: "how many hours in a week" is the fact, and
    "how many hours a week should I work out" is a training plan that must not be
    answered with 168. This is why these facts are computed here instead of being
    entries: an entry matches words anywhere in a line, and words like "hours" and
    "week" turn up in questions that are not about arithmetic at all.
    """
    text = _plain(clean)
    match = re.fullmatch(_HEAVY, text)
    if match:
        return HOW_HEAVY.get(match.group(1))
    match = re.fullmatch(_HOW_MUCH, text)
    if match:
        counted, of_unit = _UNIT.get(match.group(1)), _UNIT.get(match.group(2))
        if counted and of_unit:
            return _unit_pair(counted, of_unit)
        return None
    match = re.fullmatch(_AMOUNT, text)
    if not match:
        return None
    counted = _UNIT.get(match.group(1))
    if not counted:
        return None
    for pattern in _TAILS:
        tail = re.fullmatch(pattern, match.group(2))
        if tail:
            of_unit = _UNIT.get(tail.group(1))
            if of_unit:
                return _unit_pair(counted, of_unit)
    return None


# --- a salary in hours, and an hourly rate in a year -------------------------------
#
# "How do I work out my hourly rate from my salary" was a shrug, and so was "15 an hour, what
# is that a year". Neither is advice: each is one sum, the yearly figure over the hours actually
# worked, 52 weeks in a year. Money's own tests leave the first line alone because it is
# arithmetic rather than a money question, so it lives here with the other computed answers.

_WAGE = r"£?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|grand|thousand)?"
_WAGE_UNIT = re.compile(r"\s*(?:a|per|each|every|/)\s*(?:month|week|fortnight|year|day|hour)\b",
                        re.IGNORECASE)
_AN_HOUR = ("an hour", "per hour", "/hour", "/hr", "/h ", "a hour", "hourly rate of")
_HOURS_WORKED = re.compile(r"\b(\d{1,2}(?:\.\d+)?)\s*(?:-|to)?\s*(?:\d{1,2}(?:\.\d+)?\s*)?"
                           r"(?:hours?|hrs?)\b", re.IGNORECASE)


# The cue, then the setting: "an hour" alone is a half hour run, and "32k a year" alone is a
# mortgage question. Both words together are someone asking what their time is paid.
_WAGE_CUE = re.compile(r"\b(?:hourly|hour rate|rate an hour|per hour|an hour)\b")
_WAGE_CONTEXT = re.compile(r"\b(?:salary|wage|wages|pay|paid|earn|earns|earning|get|gets|worth|"
                           r"job|offer|contract|work|year|annual|month)\b")


def _hours_a_week(text):
    """The hours the line says they work: "37.5 hours a week", "40 hours". 0 when it says none."""
    for match in _HOURS_WORKED.finditer(text):
        try:
            value = float(match.group(1))
        except ValueError:
            continue
        if 5 <= value <= 70:
            return value
    return 0.0


def _hourly_named(text):
    """The rate the line states, in pounds and pence: "12.50 an hour" is not £12."""
    for match in re.finditer(_WAGE + r"\s*([^.;!?]{0,18})", text):
        tail = " " + (match.group(3) or "").lower()
        if any(unit in tail for unit in _AN_HOUR):
            try:
                amount = float(match.group(1).replace(",", ""))
            except ValueError:
                continue
            return amount * 1000 if match.group(2) else amount
    return 0.0


def _yearly_named(text):
    """A bare salary: "on 25k", "i earn 45000". A figure with a rate unit after it is not one."""
    best = 0.0
    for match in re.finditer(_WAGE, text):
        try:
            amount = float(match.group(1).replace(",", ""))
        except ValueError:
            continue
        if match.group(2):
            amount *= 1000
        if _WAGE_UNIT.match(text[match.end():match.end() + 16]):
            continue
        if amount >= 1000 and amount > best:
            best = amount
    return best


def _pounds(value):
    return f"{int(round(value)):,}"


def _rate(hours):
    """37.5 stays 37.5 and 12.50 stays 12.50: pence in a rate are not noise."""
    return f"{hours:.2f}" if abs(hours - round(hours)) > 1e-9 else str(int(round(hours)))


def _a_yearline(text):
    """The yearly figure the line names, from "30000 a year", "2200 a month" or a bare "25k"."""
    for pattern, scale in ((_WAGE + r"\s*(?:a|per|each|every)\s*year", 1),
                           (_WAGE + r"\s*(?:a|per|each|every)\s*month", 12)):
        for match in re.finditer(pattern, text):
            try:
                amount = float(match.group(1).replace(",", ""))
            except ValueError:
                continue
            if match.group(2):
                amount *= 1000
            return amount * scale
    return 0.0


def _wage_rate(text):
    """A salary in hours, or an hourly rate in a year. None when the line is not that sum."""
    hours = _hours_a_week(text) or 37.5
    rate = _hourly_named(text)
    yearly = _a_yearline(text) or _yearly_named(text)
    asks_a_year = bool(re.search(r"\b(?:a year|per year|annual|annually|yearly|salary)\b", text))
    if rate and not yearly and rate <= 500:
        year = rate * hours * 52
        return (f"£{_rate(rate)} an hour over {_rate(hours)} hours a week is about £{_pounds(year)} "
                f"a year before tax, £{_pounds(year / 12)} a month. Over 40 hours a week the same "
                f"rate is £{_pounds(rate * 40 * 52)}, and paid holiday is already in the 52 weeks.")
    if yearly >= 1000:
        hourly = yearly / (hours * 52)
        said = (f"£{_pounds(yearly)} a year over {_rate(hours)} hours a week is about "
                f"£{_number(round(hourly, 2))} an hour before tax, £{_pounds(yearly / 12)} a "
                f"month, £{_pounds(yearly / 52)} a week.")
        if abs(hours - 40) > 0.01:
            said += (f" Over 40 hours a week it is £{_number(round(yearly / (40 * 52), 2))}.")
        return said + " Take off any unpaid lunch break first: you are only paid for the hours you work."
    if asks_a_year and re.search(r"\b(?:hourly|hour rate|an hour|per hour)\b", text):
        return ("Take the yearly salary and divide it by the hours you actually work: £30,000 over "
                "37.5 hours a week for 52 weeks is £15.38 an hour, and over 40 hours it is £14.42. "
                "Do it before tax, drop any unpaid lunch break, and divide by 12 for the month.")
    return None


def solve(text, understood, memory):
    """A computed maths reply, or None when the line is not a calculation."""
    clean = (understood or {}).get("clean") or " ".join(str(text).lower().split())
    # Nothing here answers while the bot's last real answer was an emergency: a number said out
    # loud in that thread is not a sum to work out, it is the person still in the emergency.
    if in_a_safety_thread(memory):
        return None
    if _WAGE_CUE.search(clean) and _WAGE_CONTEXT.search(clean):
        # _wage answers the period the person actually asked for ("how much is that a
        # week" gets a week), so it goes first; _wage_rate is the fallback for a line it
        # declines, where the extra monthly and 40-hour figures still help.
        said = _wage(clean) or _wage_rate(clean)
        if said:
            return said
    for answer in (_quadratic(clean), _simplify(clean), _add_fractions(clean),
                   _the_factors(clean), _common_factors(clean), _round_to(clean), _circle_measure(clean),
                   _box_volume(clean), _equation(clean), _root(clean), _roots(clean),
                   _prime(clean),
                   _what_percent(clean), _percent_on(clean), _a_share_of_a_group(clean),
                   _fraction_decimal(clean),
                   _fraction(clean), _fraction_of(clean), _share(clean), _percent(clean),
                   _percentage_change(clean), _percent_rise(clean),
                   _percent_of_the_figure_in_the_chat(clean, memory), _tip(clean),
                   _left_on_the_bill(clean),
                   _wage(clean), _travel(clean),
                   _at_a_pace(clean, memory),
                   _save_by_a_date(clean, memory), _save_time(clean), _saving(clean),
                   _time_to_reach(clean, memory),
                   _a_goal_without_a_rate(clean, memory),
                   _time_at_a_new_rate(clean, memory),
                   _time_at_a_new_total(clean, memory),
                   _time_without_a_goal(clean, memory),
                   _figure_just_given(clean, memory),
                   _deadline_for_a_goal(clean, memory), _save_by_a_date(clean, memory),
                   _each_month_for_a_goal(clean, memory), _a_working_week(clean),
                   _convert(clean, memory), _unit_fact(clean),
                   _average(clean), _area(clean), _perimeter_of_a_room(clean),
                   _days_in_month(clean),
                   _today(clean), _days_until(clean), _date_counted_from_today(clean),
                   _days_until_easter(clean), _named_day_date(clean), _the_weekday_of_a_date(clean),
                   _next_bank_holiday(clean),
                   _days_until_a_relative_day(clean),
                   _days_until_a_named_day(clean),
                   _days_until_a_month_or_season(clean),
                   _days_left_in_the_month_or_the_year(clean),
                   _working_days_or_weekends_until(clean),
                   _how_long_ago(clean)):
        if answer:
            return answer
    return _calc(clean)


# The unit facts people ask for by name ("how many grams in an ounce") are computed in
# _unit_fact() above, because they need the shape of the whole question to answer safely.
# --- averages -----------------------------------------------------------------
# "What is an average" is a definition, but "what is the median of 3, 5 and 10" is a sum
# waiting to be done, so one entry answers both: the line's own numbers are worked out when
# it types two or more, and the three averages are explained when it only asks what they are.
_AVERAGE_FILLER = {
    "what", "whats", "is", "are", "an", "a", "the", "how", "do", "does", "i", "you", "we",
    "work", "worked", "out", "working", "calculate", "find", "workout", "mean", "means",
    "average", "averages", "median", "mode", "difference", "between", "and", "define",
    "explain", "statistics", "vs", "in", "maths", "math", "to", "of", "that", "this", "for",
    "get", "tell", "me", "know", "it", "called", "please", "explanation", "definition",
    "set", "numbers", "number", "data", "list", "values", "value", "group", "series",
    "sequence", "sample", "figures", "bits",
}

_AVERAGE_EXPLAIN = (
    "The mean, which is what most people mean by an average, is the total shared out evenly: "
    "4, 6 and 11 add to 21, and 21 ÷ 3 = 7, so the mean is 7. The median is the middle one "
    "once they are in order (6 above), and the mode is the value that appears most often.")

# A line that asks for the median gets the median in the first sentence, not the mean.
_MEDIAN_EXPLAIN = (
    "The median is the middle one once the numbers are in order: 1, 4 and 11 is 4, and "
    "1, 4, 6 and 11 is halfway between 4 and 6, so 5. It is the one to use when a few big "
    "numbers would drag a mean up, like house prices or wages. The mean is the total shared "
    "out evenly, and the mode is the value that appears most often.")

_MODE_EXPLAIN = (
    "The mode is the value that appears most often: in 2, 3, 3 and 7 it is 3, and if nothing "
    "repeats there is no mode at all. It is the one to use for the commonest answer rather "
    "than a middle one, like the most usual shoe size. The mean is the total shared out "
    "evenly, and the median is the middle one once the numbers are in order.")


def _figures(clean):
    """The numbers the line types out, in order: "the median of 3, 5 and 10" is 3, 5 and 10."""
    found = re.findall(r"(?<![\w.])\d+(?:\.\d+)?", clean)
    return [Fraction(number) for number in found]


def _short(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


# The "mean" that ends "what does the median mean" is the question's verb, not the statistic
# being asked about, so it is taken off before the words are read as keywords. Otherwise a line
# that names the median looked like the comparison "mean and median", and the mean explainer
# answered a question about the median. Anything after the verb is filler too ("what does the
# median mean in maths"), so the words after it are skipped while they are filler and the verb
# is dropped when it is the last real word.
_MEAN_VERB = ("mean", "means", "meaning")


# The statistic the line names is what is being asked about; "that", "it" and "this" are the
# thing meant, so the "mean" after them is the line's verb. "whats that mean" and "what does it
# mean" were answered with the mean explainer - a definition of the mean average for a person
# asking what the bot's last answer meant - because every word of them is filler, "mean"
# included. The same line with "does" in it was read correctly, so the spelling was what decided
# it. A line that names a statistic of its own ("what does the median mean") still answers.
_STATISTIC_WORDS = ("average", "averages", "mean", "means", "median", "mode", "statistics")
_OTHER_STATISTICS = ("average", "averages", "median", "mode")
_POINTS_AT_A_THING = ("that", "this", "it", "these", "those", "you", "me", "we", "they",
                      "he", "she", "them", "what", "whats", "how", "which")


def _names_a_statistic(asked):
    """Whether the line names the statistic it asks about, rather than pointing at a thing."""
    words = [word.strip("?.!,") for word in asked.split()]
    for index, word in enumerate(words):
        if word not in _STATISTIC_WORDS:
            continue
        if word in _MEAN_VERB:
            before = words[index - 1] if index else ""
            if before in _POINTS_AT_A_THING:
                continue
            if any(other in _OTHER_STATISTICS for other in words):
                continue
        return True
    return False


def _about_words(asked):
    words = asked.split()
    i = len(words) - 1
    while i > 0 and words[i].strip("?.!,") in _AVERAGE_FILLER \
            and words[i].strip("?.!,") not in _MEAN_VERB:
        i -= 1
    if i > 0 and words[i].strip("?.!,") in _MEAN_VERB:
        words = words[:i] + words[i + 1:]
    return " ".join(words)


def _averages(memory, understood):
    clean = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    figures = _figures(clean)
    asked = clean.lower()
    about = _about_words(asked)
    if len(figures) < 2:
        # A definition, not a sum: answer only when the line is all ask and no subject
        # ("what is the average rent in london" is a different question, so pass).
        words = [word for word in re.findall(r"[a-z']+", asked)]
        if all(word in _AVERAGE_FILLER for word in words) and _names_a_statistic(asked):
            if ("median" in asked and "mean" in about) or "difference" in asked:
                return _AVERAGE_EXPLAIN  # the comparison is the question, so name them all
            if "median" in asked:
                return _MEDIAN_EXPLAIN
            if "mode" in asked:
                return _MODE_EXPLAIN
            return _AVERAGE_EXPLAIN
        return None
    ordered = sorted(figures)
    listed = ", ".join(_short(figure) for figure in ordered)
    mean = sum(ordered) / len(ordered)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / 2
    counts = {}
    for figure in ordered:
        counts[figure] = counts.get(figure, 0) + 1
    top = max(counts.values())
    if "median" in asked:
        return (f"The median of {listed} is {_short(median)}: in order, that is the middle "
                f"one.")
    if "mode" in asked:
        if top == 1:
            return (f"No number in {listed} repeats, so there is no mode. The mean is "
                    f"{_short(mean)} and the median is {_short(median)}.")
        mode = [figure for figure, count in counts.items() if count == top][0]
        return f"The mode of {listed} is {_short(mode)}, the number that appears most often."
    total = sum(ordered)
    return (f"The mean of {listed} is {_short(mean)}: they add to {_short(total)} and "
            f"{_short(total)} ÷ {len(ordered)} = {_short(mean)}.")



# "round" is a word about people and places far more often than it is the maths verb, and the
# rounding card keyed on it answered all of them: "my friends are coming round what should i
# watch" and "how do i stop my mum coming round" both got the digit rule, and "how many in a
# round of golf" got it too. These phrases name the other subject - someone moving about, a
# place, a thing that comes in rounds - so the card stands down and the family, watching or
# golf entry has the line. Every one of them is a phrase of two or three words on purpose: a
# bare "round" in the avoid list would stand down "how do i round to two decimal places" as
# well, which is the line the card exists for.
ROUND_IS_NOT_THE_VERB = (
    "come round", "came round", "coming over round", "go round", "went round",
    "walk round", "run round", "ran round", "drive round", "drove round", "crawl round",
    "crawling round", "show round", "look round", "turn round", "round the corner",
    "round the house", "round the garden", "round the shops", "round the floor",
    "round the back", "round the world", "round here", "year round", "all year round",
    "round for dinner", "round for tea", "round for lunch", "round to see", "round trip",
    "round of drinks", "round of golf", "round of applause", "rounds of",
    # a round of boxing is three minutes, not a number read to two decimal places
    "boxing", "boxer", "boxers", "boxercise", "round of boxing", "rounds of boxing",
    "a fight", "fights", "sparring",
    # "round the bath", "round the window" and "round the worktop" are places a seal goes, not a
    # number: "how do i reseal round the bath" was told how to round 3.456 to two decimal places
    "round the bath", "round the bath and", "round a bath", "round the shower", "round the sink",
    "round the basin", "round the window", "round the window frame", "round the door",
    "round the worktop", "round the edges", "round the tiles", "round the skirting",
    "round the tiles and", "round the bottom", "round the toilet", "round the outside",
)

# "round" is a preposition more often than it is the maths verb, and it is "around" in every one
# of those lines: "how do i fit the stair gate round the newel post" was told how to round 3.456
# to two decimal places. Listing the places does not work - a list of the ones we thought of is
# always missing the next one - so the shape does it: "round" followed by an article and a noun
# is a place or a thing gone around, unless that noun is one of the number words the card is for.
_ROUND_IS_AROUND = re.compile(
    r"\brounds?\s+(?:the|a|an|my|your|his|her|its|our|their|this|that)\s+"
    r"(?!(?:number|numbers|digit|digits|decimal|decimals|answer|answers|figure|figures|value|"
    r"values|sum|total|result|nearest|whole|next)\b)\w+")


# "round work", "round the kids", "round the traffic", "how do you work round a toddler": the
# preposition, not the verb. `_ROUND_IS_AROUND` above reads the "round the thing" shapes; the one
# it cannot read is the bare noun, and on a line with a "how" and a "work" - "how do i fit the
# studying round work" - the card still answered with the digit rule. Rounding is an answer to a
# line that carries a number or names the thing itself, so that is the second half of the gate.
ROUNDING_NAMED = re.compile(
    r"\bround(?:s|ed|ing)?\s+(?:a\s+|the\s+|off\s+|up\s+|down\s+)?"
    r"(?:number|numbers|decimal|decimals|figure|figures|digit|digits|whole|thousand|thousands"
    r"|hundred|hundreds|ten|tens)\b"
    r"|\b(?:number|numbers|decimal|decimals|figure|figures|digit|digits)\s+(?:is\s+|are\s+)?"
    r"round(?:s|ed|ing)?\b"
    r"|\bround(?:ed|ing)?\s+(?:up|down)\s+(?:the\s+|a\s+|your\s+)?"
    r"(?:price|prices|cost|bill|total|number|figure|amount|sum|pence|penny|pennies|pounds|pound"
    r"|decimal|decimals|digit|digits)\b"
    # A bare "nearest" is not a number: "whats the nearest cashpoint", "where is the nearest
    # chemist", "how do i find my nearest recycling centre" are all place questions, and the card
    # answered them with the digit rule ("Look at the digit just after the place you are keeping")
    # because the word alone was the sign. Rounding is what "nearest" means when a place value
    # follows it - nearest whole, nearest ten, nearest penny - or when it is the end of a line
    # that has already said round ("how do i round to the nearest").
    r"|\brounding\b|\bdecimal places?\b|\bsignificant figures?\b"
    r"|\bnearest\s+(?:whole|ten|tens|hundred|hundreds|thousand|thousands|million|penny|pence"
    r"|pound|pounds|decimal|digit|digits|number|numbers|integer|unit|one|\d)\b"
    r"|\bround(?:s|ed|ing)?\s+(?:it\s+)?(?:to|at)\s+(?:the\s+)?nearest\b"
    # "what does round mean in maths": the word is the subject of the question, and maths is what
    # the line says it is about.
    r"|\bmaths?\b|\bmathematics\b")


def _a_rounding_question(understood):
    """True when the line is about rounding a number, not about working round something.

    A digit anywhere in the line is the plain sign of it - "round 3.456 to two decimal places",
    "what is 2.5 rounded to the nearest whole number", "round 47 to the nearest ten". Without one
    the line has to name the thing: "how do you round numbers", "what are the rules for rounding".
    """
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if re.search(r"\d", line):
        return True
    return ROUNDING_NAMED.search(line) is not None


def _rounding_is_the_ask(understood):
    """The card needs the verb and needs a number or the name: "round work" is neither."""
    return _round_is_the_verb(understood) and _a_rounding_question(understood)


def _round_is_the_verb(understood):
    """True when "round" in the line is the maths verb rather than a way of saying "around"."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    return not _ROUND_IS_AROUND.search(said)


# An hour with nothing to do in it is a free-time question, and the rate row answered it:
# "what can i do for an hour" and "i have an hour to kill, what can i do" were told to divide the
# yearly pay by the hours actually paid for. The word "an hour" is in this row's key because the
# rate is asked that way, so the asking shape is what stands it down - not the hour.
_FREE_TIME_ASK = ("what can i do", "what should i do", "what do i do", "what to do",
                  "shall i do", "should i do", "anything to do", "something to do",
                  "things to do", "to kill", "kill an hour", "keep busy")


# A rate is paid for something. "What should i watch in an hour" and "how many minutes in an hour
# and a half" name a length of time and no money at all, and this row answered both with a salary
# sum - it is keyed on "an hour", and an hour on its own is not a rate. So the row stands down on
# any line that names time and no pay, and the figure being paid, the pay words and the year keep
# the lines that really are about a rate.
_A_LENGTH_OF_TIME = re.compile(r"\bhours?\b|\bminutes?\b|\bseconds?\b")
_A_PAY_WORD = re.compile(r"\b(?:pay|paid|pays|paying|salary|salaries|wage|wages|earn|earns|earning|"
                         r"rate|rates|hourly|take home|contract|overtime|per hour|a year|annual|"
                         r"annually|yearly|a month|monthly)\b|"
                         r"\d+(?:\.\d+)?\s*(?:pounds?|quid|an hour|per hour)|"
                         # "how much do i make an hour" is a rate with no pay word in it: the
                         # verb is what says the money, so it counts only asked that way
                         r"\bhow\s+much\s+(?:do|does|would|will|did)\s+"
                         r"(?:i|you|we|they|it|that|he|she)\s+(?:make|makes|get|take)\b")


def _not_a_spare_hour(understood):
    """False when the line asks what to do with the hour rather than what it pays."""
    said = understood if isinstance(understood, dict) else {}
    line = str(said.get("clean") or said.get("text") or "").lower()
    if any(phrase in line for phrase in _FREE_TIME_ASK):
        return False
    if _A_LENGTH_OF_TIME.search(line) and not _A_PAY_WORD.search(line):
        return False
    return True


PRIME_DEFINITION = (
    "A prime number is a whole number greater than 1 that divides only by 1 and itself: 2, 3, 5, "
    "7, 11 and so on. 1 is not prime, and 2 is the only even prime.")
PRIME_TEST = (
    " To test one, try dividing it by 2, 3, 5, 7, 11 and the rest of the primes up to its square "
    "root: if none of them goes in exactly, it is prime. So 97 needs only a check against 2, 3, 5 "
    "and 7, since 11 squared is past it. Anything that ends in 0, 2, 4, 5, 6 or 8, or whose digits "
    "add up to a multiple of 3, is not prime.")


def _prime_definition(memory, understood):
    """The definition, with the test of a number added only when the line asks how to test one."""
    said = " ".join(str((understood or {}).get("clean")
                       or (understood or {}).get("text") or "").lower().split())
    if re.search(r"\b\d+\b", said):
        # a named number wants a verdict, which the number reader gives
        return None
    if re.search(r"\b(how|work out|check|test|tell|know)\b", said):
        return PRIME_DEFINITION + PRIME_TEST
    return PRIME_DEFINITION


ENTRIES = [
    entry("pi", ("pi", ("what", "value", "number", "3.14", "3.14159")),
          "Pi (π) is about 3.14159: the circumference of any circle divided by its diameter. For "
          "most everyday sums, 3.14 is close enough."),
    # "what is a prime number" wants the definition, and "how do i work out if a number is
    # prime" wants the test: one row, and the test only comes when the line asks how. A line
    # that names a number ("is 51 prime", "how do i check if 51 is prime") wants a verdict, not
    # a definition, so this row stands down and the number reader answers it.
    entry("prime-number", (("prime", "prime number", "prime numbers"),
                           ("what", "number", "definition", "mean", "work out", "how", "check",
                            "test", "tell", "know")),
          _prime_definition,
          ask=("what", "define", "meaning", "explain", "how", "work out", "check", "tell"),
          # "prime" is a verb in the decorating sense, and those lines are all about paint:
          # "how do i prime a wall before painting" wants a primer and a roller
          avoid=("wall", "walls", "wood", "woodwork", "paint", "painting", "painted", "primer",
                 "undercoat", "metal", "gate", "gates", "door", "doors", "skirting", "ceiling",
                 "plaster", "render", "mdf", "bare wood", "filler", "roller", "brush", "minis",
                 "miniature", "prime minister", "amazon prime", "prime video", "prime day")),
    entry("percent-how", (("percentage", "percent", "percentages"),
                          ("work", "calculate", "out", "how", "formula", "explain")),
          "To find a percentage of something, divide the amount by 100 and multiply by the "
          "percentage: 15% of 80 is 80 ÷ 100 × 15 = 12. To turn a fraction into a percentage, "
          "divide the top by the bottom and multiply by 100.",
          ask=("how", "what", "explain", "formula", "calculate", "work out")),
    # The method, for the line that asks how and not for one particular equation. Every
    # "solve x squared ..." line is worked out above by _quadratic(), so this only takes the
    # general question, and the ask words keep it off "quadratic graphs" and "what is a
    # quadratic" - though it answers that too, since it is the same shape of answer.
    entry("quadratic-formula",
          (("quadratic", "quadratics", "quadratic equation", "quadratic equations",
            "quadratic formula"),
           ("solve", "solving", "formula", "method", "roots", "root", "factorise", "factorize",
            "factor", "how", "what", "work out", "explain", "equation", "equations")),
          "Arrange it as ax² + bx + c = 0, then put the numbers into x = (-b ± √(b² - 4ac)) / 2a. "
          "If b² - 4ac is positive there are two answers, zero means one answer, and negative "
          "means none without imaginary numbers. Try factorising first when the numbers are "
          "small: x² + 5x + 6 is (x + 2)(x + 3), so x is -2 or -3.",
          ask=("how", "what", "solve", "method", "explain", "roots", "formula")),
    entry("bodmas", (("bodmas", "bidmas", "order of operations"),
                     ("what", "maths", "mean", "rules")),
          "Work in this order: brackets, then powers or roots, then multiplication and division "
          "left to right, then addition and subtraction left to right. So 2 + 3 × 4 is 14, not "
          "20.", ask=("what", "how", "order", "mean")),
    # "how do i work out square metres" is the same sum in the units people buy carpet and turf
    # in, and it was a shrug: the working is here, in one sentence, so the words are in the key.
    entry("area-formula", (("area", "square metres", "square meters", "square footage",
                            "square foot", "square feet", "m2", "sqm"),
                           ("formula", "work out", "calculate", "how", "what", "many")),
          "For a rectangle, area = length × width; for a triangle, ½ × base × height; for a "
          "circle, π × radius². Keep all the measurements in the same unit. So a room 4m by 3m "
          "is 12 square metres, and an L-shaped floor is two rectangles added together.",
          # the sum, not the thing being bought: a turf, carpet or tile quantity is that
          # product's own card, and "square metres" was pulling it here
          avoid=("turf", "grass", "lawn", "carpet", "carpets", "carpeting", "flooring", "floor",
                 "tiles", "tiling", "gravel", "soil", "decking", "paint", "wallpaper", "border",
                 "grout", "adhesive", "plasterboard"),
          ask=("how", "formula", "calculate", "work")),
    # "how many days in a leap year" is the length of the year (above); this is the reason for
    # it, so the ask words are the question and not the noun.
    entry("leap-year-why", (("leap year", "leap years", "leap day", "february 29", "29 february",
                             "29th of february"),
                            ("why", "reason", "exist", "needed", "needs", "happen", "happens",
                             "extra", "added", "invented", "what is", "whats", "mean")),
          "A leap year is a year with 366 days and a 29th of February, because a year is really "
          "about 365 and a quarter: without the extra day the calendar would slip a day every "
          "four years. One correction keeps it exact, since the year is not quite a quarter "
          "longer - a century is only a leap year if it divides by 400, which is why 1900 was not "
          "one and 2000 was.",
          avoid=("how many days", "how long", "how many weeks", "days in february")),
    entry("fraction-decimal", (("fraction",), ("decimal", "convert", "change")),
          "To turn a fraction into a decimal, divide the top number by the bottom: 3/4 is "
          "3 ÷ 4 = 0.75. Some fractions repeat for ever, like 1/3 = 0.333…", ask=("how", "convert", "change", "decimal")),
    entry("average-mean", (("average", "averages", "mean", "median", "mode", "statistics",
                            "the mean", "the median", "the mode"),
                           ("what", "how", "work out", "calculate", "find", "difference",
                            "define", "explain", "vs")),
          _averages,
          # "what do you mean" and "i mean" are the conversational mean, not the statistic
          # "portrait mode" and "bokeh" are the camera's, not the mode of a set of numbers
          # "whats that mean" and "what does it actually mean" are the same conversational
          # question in a quicker spelling: a line with no subject of its own, or with "that",
          # "it" or "this" as one, is never asking what a mean average is
          avoid=("you mean", "i mean", "does that mean", "what do you",
                 "that mean", "it mean", "this mean", "mean by",
                 "portrait", "portrait mode", "bokeh", "selfie", "camera", "photo", "photos",
                 # "how do i turn him down without being mean" is the refusal, and the only word
                 # it shared with this row was the adjective: a statistic is never asked for
                 # with "without being mean", and no one refuses a date with a formula.
                 "without being mean", "not being mean", "be mean", "being mean", "sound mean",
                 "mean to", "mean about", "turn him down", "turn her down", "turn them down",
                 "let him down", "let her down", "let them down")),
    # The everyday sums people ask how to do rather than what the answer is: VAT added to a
    # price and taken back off it, and an hourly rate from a salary. Both were shrugs, and
    # "how do i work out vat" was worse than a shrug - fitness read "work out" as the verb of a
    # session and answered "three half-hour sessions a week".
    entry("vat-how",
          (("vat", "value added tax"),
           ("how", "work out", "calculate", "add", "take off", "remove", "price", "included",
            "charge", "deduct", "minus")),
          "VAT in the UK is 20%: add it by multiplying the price by 1.2, so £80 becomes £96, and "
          "take it off a VAT-inclusive price by dividing by 1.2, so £96 is £80 plus £16 of VAT. "
          "The VAT on a net price is simply a fifth of it.",
          ask=("how", "work out", "calculate", "add", "take off", "remove", "deduct"),
          # "what is vat" is the definition and money has it; a VAT number, a refund or a
          # registration is another question again
          avoid=("number", "registration", "register", "refund", "return", "rebate",
                 "what is vat", "what's vat")),
    entry("hourly-rate",
          (("hourly rate", "hourly pay", "rate an hour", "rate per hour", "per hour",
            "an hour"),
           ("work out", "calculate", "from my salary", "salary", "annual", "yearly",
            "take home", "contract", "hours")),
          "Divide the yearly pay by the hours you are actually paid for: £30,000 over 37.5 "
          "hours a week is £30,000 ÷ (37.5 × 52) = about £15.40 an hour, and only the paid "
          "weeks count, so unpaid breaks or a term-time contract change the figure. Take-home "
          "hourly pay uses the figure after tax and pension, not the salary.",
          ask=("how", "work out", "calculate", "what"),
          guard=_not_a_spare_hour,
          # "what can i make with half an hour" names an hour, and the rate row took the dinner
          # question: a line that asks what to cook with the time it has names a dish, and a row
          # about a rate cannot answer it. Only the make/cook words - DISH_ASK also holds "do
          # with", which would take "i have half an hour free after work, whats the best thing
          # to do with it" off the answer it has now, and that line is not about money either
          # but it is not this row's to fix.
          avoid=("make with", "made with", "make using", "make from", "make out of",
                 "what can i make", "what can i cook", "what should i make", "cook with",
                 "cooking with",
                 # "what is a quarter of an hour" and "how many minutes in an hour and a half"
                 # name an hour and ask "what", which is this row's key, and neither is about
                 # money: the answer is the span in minutes, and units.py has it. A length of
                 # time is never a rate, so the words that only ever ask for one stand the row
                 # down - a rate is asked about pay, hours worked or a year, and keeps those.
                 "fraction", "of an hour", "of a day", "hour and a half", "minutes", "seconds",
                 "how long", "how many minutes",
                 "electricity", "energy", "gas", "water", "parking", "charge", "charging",
                 "battery", "kilowatt", "kwh", "boiler", "car", "van", "hire", "rent",
                 "babysit", "childcare", "cleaner", "tradesman", "plumber", "electrician",
                 # an hour in the oven is not an hour of pay: "half an hour in the oven, what
                 # temperature for a cake" and "an hour in the oven then what" were both handed
                 # the salary divided down to an hourly rate, because "an hour" is a key here
                 # and "what" is the ask. Anything that says the oven is the cooking clock.
                 "oven", "bake", "baked", "baking", "roast", "roasting", "roasted",
                 "temperature", "gas mark", "fan oven", "simmer", "simmering", "boil",
                 "boiling", "marinate", "marinade", "prove", "proving", "knead", "chill",
                 "chilling", "fridge", "freezer", "recipe", "casserole", "cake", "bread",
                 "biscuits", "pastry", "pasties", "batter", "dough",
                 # "how much is garage labour per hour" is the garage's rate, and the word
                 # "labour" is not the wage of the person asking: a trade or a car in the line
                 # is somebody else's hourly rate, and cars.py prices those.
                 "garage", "garages", "mechanic", "mechanics", "labour", "clutch", "cambelt",
                 "mot", "servicing", "bodywork")),
    entry("compound-interest", (("compound interest", "interest rate", "interest rates",
                                 "compound"),
                                ("what", "how", "work out", "calculate", "means", "works",
                                 "worth", "better")),
          "Compound interest pays interest on the interest as well as on what you put in, so "
          "£1,000 at 5% is £1,050 after a year and £1,102.50 after two, because the second year "
          "pays 5% of £1,050. The rule of 72 is the shortcut: divide 72 by the rate to get the "
          "years it takes to double, so 5% doubles in about 14 years.",
          avoid=("no interest", "not interested", "hobby", "hobbies", "common interest",
                 "in common", "of interest",
                 # "what is a good interest rate for a savings account" asks which account pays
                 # well, not what compounding is: the rate to look for is a different answer
                 "good rate", "good interest", "best rate", "best interest", "decent rate",
                 "decent interest", "what rate", "which rate", "highest rate", "savings")),
    # --- the school questions that ask how ---------------------------------
    # "how do I work out a ratio" has no numbers in it, so nothing can be computed: the answer
    # is the method, with one worked example so it can be followed. Each of these was a shrug.
    # "how do i find half of a number" was a half marathon on main: the word "half" and the word
    # "how" are all `race-distance-half` needed, and nothing held the sum. Halving is the first
    # fraction anybody meets, and it is the one people ask for by name rather than as a fraction.
    entry("half-of-a-number",
          (("half", "halve", "halves", "half of", "half of a number"),
           ("number", "numbers", "amount", "figure", "sum", "of a number", "work out", "find",
            "calculate", "how")),
          "Divide it by 2: half of 46 is 23, and half of 7 is 3.5. For a quarter, halve it twice; "
          "for 10 per cent divide by 10, and for 5 per cent halve that.",
          ask=("how", "what", "find", "work out", "calculate", "of a number"),
          # a half marathon, half an hour, half term and half price are all other answers
          # "how do i use up half a tin of coconut milk" is a leftover question: half of a
          # container is a use-up row, so every container noun and the use-up wording stands down
          avoid=("marathon", "5k", "10k", "race", "run", "running", "ran", "training", "train",
                 "distance", "miles", "km", "kilometres", "kilometers", "an hour", "hour",
                 "past", "term", "price", "half price", "a day", "a week", "pint", "recipe",
                 "cooking", "bottle", "glass", "cup",
                 "use up", "use it up", "using up", "used up", "leftover", "left over",
                 "leftovers", "tin", "tins", "tin of", "can", "cans", "can of", "jar", "jars",
                 "packet", "packets", "packet of", "carton", "carton of", "tub", "pots", "pot",
                 "punnet", "bag", "bags", "bunch", "tray", "half a tin", "half a can",
                 "half a jar", "half a packet",
                 # "im going to halve my dose and see how i go" is a plan about a prescription:
                 # "Divide it by 2: half of 46 is 23" is arithmetic help for a sum nobody asked,
                 # and the medicine is not a number. A medicine word in the line means the sums
                 # row stands down, whatever the words around it.
                 "dose", "doses", "dosage", "tablet", "tablets", "pill", "pills", "capsule",
                 "capsules", "medication", "medicine", "medicines", "insulin", "steroid",
                 "steroids", "inhaler", "inhalers", "antibiotic", "antibiotics", "statins",
                 "painkillers", "antidepressants", "prescription")),
    entry("ratio-how",
          (("ratio", "ratios", "proportion", "proportions", "share in a ratio"),
           ("how", "work", "out", "share", "divide", "simplify", "what", "explain", "split",
            "mean", "means")),
          "Add the parts of the ratio first, then divide the amount by that: sharing £50 in the "
          "ratio 2:3 is 5 parts, so each part is £10 and the shares are £20 and £30. To simplify "
          "a ratio, divide both numbers by the same thing, so 10:15 becomes 2:3.",
          ask=("how", "what", "explain", "mean", "work", "share", "simplify")),
    entry("standard-form",
          (("standard form", "scientific notation", "powers of ten", "powers of 10"),
           ("what", "how", "write", "maths", "explain", "mean", "convert", "big", "small",
            "number", "numbers")),
          "Standard form writes a number as something between 1 and 10 times a power of ten: "
          "4,500 is 4.5 x 10³, and 0.0002 is 2 x 10⁻⁴. Count how many places the decimal point "
          "moves, and make it negative when the number is below 1. To multiply, multiply the "
          "front numbers and add the powers.",
          ask=("what", "how", "write", "explain", "convert", "mean")),
    entry("simultaneous-equations",
          (("simultaneous equations", "simultaneous", "two equations", "equations with two"),
           ("solve", "how", "what", "method", "explain", "work", "find")),
          "Write one equation under the other and add or subtract them to lose a letter: "
          "2x + y = 7 and x + y = 4 gives x = 3 straight away, then y = 1 from either one. If "
          "nothing cancels, multiply one equation until it does. Put both numbers back into both "
          "equations to check.",
          ask=("how", "what", "solve", "explain", "method")),
    entry("factors-and-multiples",
          (("factor", "factors", "multiple", "multiples", "prime factor", "prime factors",
            "hcf", "lcm", "highest common factor", "lowest common multiple"),
           ("what", "difference", "how", "mean", "explain", "find", "vs", "between")),
          "A factor divides into a number exactly - 1, 2, 3, 4, 6 and 12 for 12 - and a multiple "
          "is in its times table: 12, 24, 36. A prime factor is a factor that is also prime, so "
          "12 is 2 x 2 x 3. The highest common factor of two numbers is the biggest one they "
          "share; the lowest common multiple is the smallest one they both divide into.",
          ask=("what", "how", "difference", "mean", "explain", "find")),
    entry("negative-numbers",
          (("negative number", "negative numbers", "minus number", "minus numbers"),
           ("what", "how", "add", "subtract", "multiply", "divide", "explain", "mean", "work")),
          "Use a number line: adding a negative moves you left, subtracting a negative moves you "
          "right, so 5 - (-3) is 8. Multiplying or dividing two negatives gives a positive, and "
          "one negative gives a negative: -2 x -3 is 6, and -6 / 2 is -3.",
          ask=("what", "how", "explain", "mean", "add", "subtract", "multiply", "work")),


    entry("rounding-how",
          (("rounding", "round", "decimal places", "significant figures", "nearest"),
           ("how", "what", "rules", "explain", "mean", "number", "work")),
          "Look at the digit just after the place you are keeping: 5 or more rounds the last "
          "kept digit up, 4 or less leaves it. So 3.456 to two decimal places is 3.46 and to the "
          "nearest whole number it is 3. Round once, at the end of a sum, not at every step.",
          # "round" is also what a cold does in an office and what a dog does at the park, and
          # with "how" in the key every one of those scored four: "how do i stop colds going
          # round the office" was told how to round 3.456 to two decimal places.
          avoid=ROUND_IS_NOT_THE_VERB + (
              "cold", "colds", "flu", "virus", "illness", "office", "park", "dog", "dogs",
              # and a round is a delivery, a drink, a fight and a golf hole: "what age can you
              # get a paper round" and "how much does a paper round pay" were both told how to
              # round 3.456 to two decimal places.
              "paper round", "paper rounds", "newspaper round", "paperboy", "papergirl",
              "paper route", "deliver papers", "round of drinks", "round of golf", "in a round"),
          ask=("how", "what", "rules", "explain", "mean", "work"),
          guard=_rounding_is_the_ask),
    # "what do the angles in a triangle add up to" was a search signpost: the shape entries
    # answer area and perimeter, and no entry knew the one fact every pupil is asked for.
    entry("triangle-angles",
          (("angle", "angles", "degree", "degrees"),
           ("triangle", "triangles", "add up", "add up to", "inside", "corner", "corners",
            "total", "sum", "180")),
          "The three angles inside any triangle add up to 180 degrees, so if you know two of "
          "them, take their total away from 180 for the third: 60 and 70 leaves 50. An "
          "equilateral triangle is 60 degrees each, and a right angle is 90. In a quadrilateral "
          "(a four-sided shape) the four angles add up to 360.",
          ask=("add up", "add up to", "total", "sum", "what", "how many", "inside")),

    entry("reading-a-graph",
          (("graph", "graphs", "line graph", "bar chart", "bar graph", "axis", "axes"),
           ("read", "reading", "how", "what", "plot", "draw", "explain", "mean")),
          "Read what each axis is measured in first, including the units and the step between "
          "the numbers. To read a value, go up from the number you know to the line, then across "
          "to the other axis. A straight line means the same change each time; a curve means it "
          "changes faster or slower.",
          ask=("how", "what", "read", "explain", "mean")),
    entry("fractions-how",
          (("add fractions", "adding fractions", "subtract fractions", "subtracting fractions",
            "common denominator", "fractions with different"),
           ("how", "add", "subtract", "different", "bottom", "denominator", "common", "explain")),
          "Give them the same bottom number first, then add or subtract the tops: 1/2 + 1/3 is "
          "3/6 + 2/6, which is 5/6. Use the lowest bottom both numbers divide into, which is 6 "
          "here and 4 for 1/2 + 1/4, then cancel the answer down.",
          ask=("how", "add", "subtract", "explain", "different")),
    entry("volume-how",
          (("volume", "cubic"),
           ("how", "work out", "calculate", "formula", "box", "cube", "cylinder", "what")),
          "For a box it is length x width x height, so 10cm by 5cm by 2cm is 100cm³. A cylinder "
          "is pi x radius² x height, and a sphere is 4/3 x pi x radius³. Put every measurement in "
          "the same unit before multiplying.",
          ask=("how", "what", "calculate", "formula", "work"),
          # "volume" is also the loudness of a phone, a television and a speaker: this entry is
          # the maths sum, so the sound words hand those lines over (technology's phone-louder)
          # the volume of a room is a sum; the volume of a TV, a phone or a speaker is a sound
          # setting, and "how do i reduce the volume on my tv" was getting the maths answer
          avoid=("phone", "iphone", "android", "mobile", "tv", "television", "speaker",
                 "speakers", "headphones", "airpods", "sound", "louder", "quieter", "quiet",
                 "hear", "music", "podcast", "calls", "ringtone", "laptop", "computer", "telly",
                 "soundbar", "sound bar", "radio", "earbuds", "turn up", "turn down", "mute",
                 "volume up", "volume down", "the volume on")),
    entry("circumference-how",
          (("circumference",),
           ("how", "work out", "calculate", "formula", "what", "circle", "mean")),
          "The circumference is pi times the diameter, or 2 x pi x radius: a circle with a radius "
          "of 5 has one of about 31.4. Pi is 3.14 to two decimal places. The area of the same "
          "circle is pi x radius², which is a different sum.",
          ask=("how", "what", "calculate", "formula", "work", "mean")),
    entry("simplify-fraction-how",
          (("simplify a fraction", "simplifying fractions", "simplify fractions",
            "simplest form", "lowest terms", "cancel down", "cancel a fraction"),
           ("how", "what", "explain", "mean", "simplify", "fraction", "fractions")),
          "Divide the top and the bottom by the same number until nothing goes into both: 6/8 "
          "divides by 2 to give 3/4, and that is as far as it goes. The number to start with is "
          "the highest common factor of the two.",
          ask=("how", "what", "explain", "mean", "simplify")),
    entry("decimals-how",
          (("decimal", "decimals", "decimal point", "decimal places"),
           ("multiply", "multiplying", "divide", "dividing", "how", "work", "explain", "times")),
          "Multiply as if the points were not there, then put the point back with as many "
          "decimal places as the two numbers had between them: 0.3 x 0.4 is 0.12. To divide, "
          "move both points the same number of places until the number you are dividing by is "
          "whole: 1.2 / 0.4 is 12 / 4, which is 3.",
          ask=("how", "explain", "work", "multiply", "divide", "times")),
]


# The words a school maths lesson defines, and the everyday senses that share them: a safe
# area to live, a perimeter fence, a variable mortgage rate. Each key names its own subject;
# the narrow ask keeps "what is the area of a 4m by 3m room" for the sum, not the definition.
_DEFINITION_ASK = ("what is", "what's", "whats", "what are", "what does", "what do",
                   "how does", "define", "definition", "meaning", "mean", "explain")

ENTRIES.append(entry(
    "decimal-what",
    (("decimal", "decimals"),
     ("what", "whats", "is a", "are", "mean", "meaning", "definition", "explain", "number")),
    "A decimal is a way of writing a number using place values for tenths, hundredths and so "
    "on, with a point after the units: 0.75 means seven tenths and five hundredths, which is the "
    "same as 3/4. The digits after the point tell you the place value, so 0.5 is five tenths and "
    "0.05 is five hundredths.",
    avoid=("betting", "odds", "bookmaker", "currency", "exchange rate", "binary", "hexadecimal",
           "hex", "binary code", "timesheet", "invoice"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "percentage-what",
    (("percentage", "percentages", "percent"), ("what", "mean", "meaning", "definition", "explain")),
    "A percentage is a fraction of 100: 25% means 25 out of every 100, or a quarter, and 100% is "
    "the whole thing. To turn a fraction into a percentage, divide the top by the bottom and "
    "multiply by 100, so 3/5 is 60%.",
    avoid=("of", "increase", "decrease", "change", "off", "discount", "tip", "vat", "tax",
           "interest", "raise", "calculator", "how much"),
    ask=_DEFINITION_ASK))

ENTRIES.append(entry(
    "area-what",
    (("area",), ("what", "mean", "meaning", "definition", "explain", "measured", "measure")),
    "Area is the amount of surface inside a shape, measured in square units: a room 4 m by 3 m "
    "has an area of 12 square metres. For a rectangle it is length times width, for a triangle "
    "half base times height, and for a circle pi times the radius squared.",
    avoid=("of", "live", "living", "move", "moving", "neighbourhood", "neighborhood", "postcode",
           "safe", "rough", "nice", "local area", "catchment", "deprived", "crime",
           # "in my area" is a place and not a surface: "what gyms are in my area" was answered
           # with the definition of area, and the areas of a town are the same word
           "in my area", "my area", "in our area", "our area", "in the area", "this area",
           "near me", "near us", "nearby", "nearest", "around here", "round here",
           "where i live", "gyms", "gym",
           # a place name or a dialling code is not the surface inside a shape
           "code", "codes", "dialling", "dialing", "zip", "51", "52", "area 51", "area 52",
           "place", "place name"),
    ask=_DEFINITION_ASK))

ENTRIES.append(entry(
    "perimeter-what",
    (("perimeter",), ("what", "mean", "meaning", "definition", "explain", "measured", "measure")),
    "The perimeter is the distance all the way round the outside of a shape, found by adding the "
    "lengths of its sides: a room 4 m by 3 m has a perimeter of 14 m. Area is the surface inside; "
    "the perimeter is the edge round it.",
    avoid=("of", "fence", "fencing", "security", "alarm", "guard", "patrol", "wall", "boundary",
           "camera", "sensor", "dog"),
    ask=_DEFINITION_ASK))

ENTRIES.append(entry(
    "variable-what",
    (("variable", "variables"),
     ("what", "mean", "meaning", "definition", "explain", "maths", "math", "algebra")),
    "In maths a variable is a letter standing for a number you do not know yet, or one that can "
    "change, such as x in 3x + 4 = 19. You work with it as if it were a number, then solve to "
    "find what it must be.",
    avoid=("weather", "speed", "wind", "temperature", "rate", "mortgage", "interest", "tariff",
           "energy", "salary", "income", "cost", "costs", "price", "prices", "mood", "quality",
           "signal", "power"),
    ask=_DEFINITION_ASK))

ENTRIES.append(entry(
    "probability-what",
    (("probability",), ("what", "mean", "meaning", "definition", "explain")),
    "Probability is how likely something is, written as a number from 0 (impossible) to 1 "
    "(certain): a fair coin landing heads has a probability of 1/2, or 50%. You find it by "
    "dividing the number of ways the thing can happen by the number of equally likely outcomes.",
    avoid=("of", "rain", "weather", "forecast", "rolling", "roll", "dice", "die", "coin",
           "cards", "lottery", "odds", "chance of"),
    ask=_DEFINITION_ASK))

ENTRIES.append(entry(
    "square-number-what",
    (("square number", "square numbers", "perfect square", "perfect squares"),
     ("what", "mean", "meaning", "definition", "explain")),
    "A square number is what you get when a whole number is multiplied by itself: 1, 4, 9, 16, "
    "25 and so on, because 4 × 4 = 16. It is called square because that many dots make a square "
    "grid, and it is always a whole number.",
    avoid=("metre", "meter", "foot", "feet", "mile", "room", "floor", "roof", "garden", "tile",
           "tiles", "root"),
    ask=_DEFINITION_ASK))

ENTRIES.append(entry(
    "numerator-denominator-what",
    (("numerator", "numerators", "denominator", "denominators"),
     ("what", "mean", "meaning", "definition", "explain", "fraction", "top", "bottom")),
    "In a fraction the numerator is the top number, the one being counted, and the denominator is "
    "the bottom number, the one that says how many equal pieces the whole is cut into. In 3/4 the "
    "numerator is 3 and the denominator is 4, so you have three of four equal pieces.",
    avoid=("lowest common denominator", "common denominator", "idiom", "politics", "tv",
           "television", "film", "music", "audience"),
    ask=_DEFINITION_ASK,
    bias=2))
# --- the next definitions a lesson asks for
MATHS_DEFINITION_ASK = ("what is", "what's", "what are", "what does", "what do", "how does",
                       "how do", "how is", "how are", "why is", "why are", "why does",
                       "explain", "tell me about", "define")
# Main shrugged at all eight. The second key part is only there to make the topic score; the
# DEFINITION_ASK frame is what stops "what is the best angle" and "what is my term dates".

ENTRIES.append(entry(
    "angle-what",
    (("angle", "angles"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "number", "degrees", "degrees", "measure")),
    "An angle is the amount of turn between two lines that meet at a point, measured in degrees: a "
    "quarter turn is 90 degrees, a half turn 180 and a full turn 360. A right angle is exactly 90, an "
    "acute angle is less than that and an obtuse one is between 90 and 180.",
    avoid=("camera", "photo", "photos", "photography", "shoot", "shooting", "best",
           "wrong", "fishing", "fish", "park", "parking", "at an angle", "an angle on",
           "of a roof", "roof", "roofs", "roof pitch", "of a wall"),
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "integer-what",
    (("integer", "integers"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "number", "numbers", "whole")),
    "An integer is a whole number - positive, negative or zero - with no fraction or decimal part. "
    "So 4, -7 and 0 are integers, while 2.5 and 1/3 are not; the integers are the counting numbers, "
    "their negatives, and zero.",
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "power-maths-what",
    (("power", "powers", "power of", "exponent", "exponents"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "number", "numbers", "squared", "index")),
    "In maths a power tells you how many times to multiply a number by itself: 3 to the power 4 "
    "means 3 x 3 x 3 x 3, which is 81. The small raised number is the exponent and the number being "
    "multiplied is the base; a square is a power of 2 and a cube is a power of 3.",
    avoid=("electricity", "electric", "electrical", "solar", "nuclear", "wind", "battery",
           "outage", "cut", "cuts", "station", "plant", "political", "government", "prime",
           "minister", "president", "abuse", "corrupt", "money", "bank", "save", "saving"),
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "expression-maths-what",
    (("expression", "expressions", "algebraic expression"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "algebra", "number", "numbers", "equation")),
    "In maths an expression is a group of numbers, letters and operations with no equals sign, such "
    "as 3x + 4 or 2(a - b). It can be simplified or evaluated, but it is not a statement that two "
    "things are equal - that is an equation.",
    avoid=("facial", "face", "faces", "art", "artistic", "creative", "freedom", "gene", "genes",
           "protein", "protein expression", "emotional", "feelings", "yourself", "myself",
           "of interest", "expression of interest", "of concern", "letter"),
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "coefficient-what",
    (("coefficient", "coefficients"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "algebra", "number", "numbers", "letter", "variable")),
    "A coefficient is the number multiplying a letter in an expression: in 3x the coefficient is 3, "
    "and in -5y squared it is -5. If a letter stands alone the coefficient is 1, because x means 1x.",
    avoid=("drag", "lift", "friction", "correlation", "alpha", "beta", "regression"),
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "term-maths-what",
    (("term", "terms", "like terms"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "algebra", "expression", "equation", "number", "numbers", "add")),
    "In maths a term is one part of an expression, separated from the others by plus or minus signs: "
    "in 3x + 4y - 7 there are three terms, 3x, 4y and -7. Terms with the same letter part are like "
    "terms and can be added together, so 2x + 3x becomes 5x.",
    avoid=("school", "school term", "term dates", "dates", "contract", "lease", "insurance",
           "loan", "mortgage", "pregnancy", "pregnant", "fixed term", "long term", "short term",
           "terms and conditions", "conditions", "half term", "autumn", "spring", "summer",
           "of endearment", "endearment", "of office", "of address", "term of"),
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "symmetry-what",
    (("symmetry", "symmetrical", "line of symmetry", "lines of symmetry"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "shape", "shapes", "line", "mirror", "turn")),
    "Symmetry is when a shape or object looks the same after a fold, turn or flip. A line of "
    "symmetry divides a shape into two halves that are mirror images - a square has four, a circle "
    "has infinitely many - and rotational symmetry is how many times it matches in a full turn.",
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "polygon-what",
    (("polygon", "polygons"),
     ("what", "define", "definition", "mean", "meaning", "explain", "called", "maths",
      "mathematics", "shape", "shapes", "sides", "closed")),
    "A polygon is a closed flat shape made only of straight sides that do not cross. A triangle has "
    "3 sides, a quadrilateral 4, a pentagon 5 and a hexagon 6; a circle is not a polygon because its "
    "edge is curved.",
    ask=MATHS_DEFINITION_ASK))

ENTRIES.append(entry(
    "equation-what",
    (("equation", "equations"),
     ("what", "mean", "meaning", "definition", "explain", "difference", "expression")),
    "An equation says two things are equal, and the equals sign is the point: 3x + 4 = 19 is an "
    "equation. An expression such as 3x + 4 has no equals sign, so it can be simplified but not "
    "solved. Solving an equation means finding the number that makes both sides balance.",
    avoid=("solve", "solving", "work out", "find x", "value of x", "simultaneous", "quadratic",
           "rearrange", "balance", "check", "steps"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "algebra-what",
    (("algebra", "algebraic"),
     ("what", "mean", "meaning", "definition", "explain", "used", "use", "basic", "basics")),
    "Algebra is arithmetic with letters standing in for numbers, so a rule works for every number "
    "at once: if a notebook costs n pounds, three cost 3n. The letters are called variables, and "
    "the usual job is to rearrange an equation until the letter is alone.",
    avoid=("solve", "solving", "simplify", "factorise", "factorize", "expand", "rearrange",
           "brackets", "simultaneous", "quadratic", "worksheet", "homework", "test", "exam"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "ratio-what",
    (("ratio", "ratios"),
     ("what", "mean", "meaning", "definition", "explain", "difference", "proportion")),
    "A ratio compares two amounts by division, so a ratio of 2:3 means the second amount is one and "
    "a half times the first. A recipe using 2 cups of flour to 3 of milk is in the ratio 2:3, and "
    "scaling both numbers by the same amount keeps the ratio the same.",
    avoid=("how", "work out", "share", "sharing", "split", "divide", "simplify", "calculate",
           "smoothie", "coffee", "paint", "mortar", "concrete", "cement", "dough", "bread",
           "rice", "porridge"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "parallelogram-what",
    (("parallelogram", "parallelograms"),
     ("what", "mean", "meaning", "definition", "explain", "area", "shape")),
    "A parallelogram is a four-sided shape with both pairs of opposite sides parallel and equal, "
    "so its opposite angles are equal too. A rectangle is a special parallelogram with right "
    "angles. Its area is the base times the perpendicular height, not the slanted side.",
    avoid=("parking", "park", "car", "road", "drive", "space", "space-saving", "shelf"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "rhombus-what",
    (("rhombus", "rhombuses", "rhombi"),
     ("what", "mean", "meaning", "definition", "explain", "area", "shape", "diamond")),
    "A rhombus is a four-sided shape with all four sides the same length and both pairs of opposite "
    "sides parallel; a square is a rhombus with right angles, and a diamond shape is one too. Its "
    "area is half the product of its two diagonals.",
    avoid=("ring", "engagement", "wedding", "jewellery", "jewelry", "diamond", "carat",
           "brilliant", "mine", "stone", "ring size"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "trapezium-what",
    (("trapezium", "trapeziums", "trapezoid", "trapezoids"),
     ("what", "mean", "meaning", "definition", "explain", "area", "shape")),
    "A trapezium is a four-sided shape with exactly one pair of parallel sides; in the US the same "
    "shape is usually called a trapezoid. Its area is half the sum of the two parallel sides times "
    "the height between them.",
    avoid=("bone", "wrist", "hand", "thumb", "carpal", "table", "desk", "garden", "land"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "cube-what",
    (("cube", "cubes"),
     ("what", "mean", "meaning", "definition", "explain", "volume", "surface", "shape")),
    "A cube is a solid with six square faces of the same size, twelve edges and eight corners: a "
    "sugar lump and a die are cubes. Its volume is the side multiplied by itself three times, so a "
    "2 cm cube holds 8 cm³, and its surface area is six times one face.",
    avoid=("ice", "ice cube", "stock", "stock cube", "bouillon", "sugar cube", "rubik",
           "rubik's", "puzzle", "cube steak", "cubicle", "van", "van hire", "storage",
           "packing", "freezer", "whisky", "whiskey", "drink", "number", "numbers"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "cuboid-what",
    (("cuboid", "cuboids"),
     ("what", "mean", "meaning", "definition", "explain", "volume", "surface", "shape")),
    "A cuboid is a box shape with six rectangular faces, like a brick or a cereal box. Its volume "
    "is length times width times height, and a cube is the special cuboid where all three are equal.",
    avoid=("bone", "foot", "feet", "ankle", "toe", "wrist", "fracture", "tarsal"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "sphere-what",
    (("sphere", "spheres"),
     ("what", "mean", "meaning", "definition", "explain", "volume", "surface", "shape")),
    "A sphere is the solid round shape where every point on the surface is the same distance from "
    "the centre, like a ball or a marble. Its volume is 4/3 times pi times the radius cubed, and "
    "its surface area is 4 times pi times the radius squared.",
    avoid=("public", "social", "political", "private", "influence", "sphere of", "work",
           "home", "life", "music", "fashion", "media", "online", "dyson"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "cylinder-what",
    (("cylinder", "cylinders"),
     ("what", "mean", "meaning", "definition", "explain", "volume", "surface", "shape")),
    "A cylinder has two flat circular ends and one curved side, like a tin or a tube. Its volume "
    "is pi times the radius squared times the height, and the curved surface is 2 times pi times "
    "the radius times the height.",
    avoid=("gas", "oxygen", "gas bottle", "bottle", "lock", "brake", "hydraulic", "clutch",
           "engine", "boiler", "hot water", "mower", "car", "van", "propane", "butane",
           "co2", "compressed"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "cone-what",
    (("cone", "cones"),
     ("what", "mean", "meaning", "definition", "explain", "volume", "surface", "shape")),
    "A cone has one circular base and a curved side that comes to a point, like a party hat or a "
    "road cone. Its volume is one third of the cylinder with the same base and height: 1/3 times "
    "pi times the radius squared times the height.",
    avoid=("ice cream", "pine", "waffle", "nose", "hedge", "plant",
           "flower", "evergreen", "fir", "eye", "retina"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "prism-what",
    (("prism", "prisms"),
     ("what", "mean", "meaning", "definition", "explain", "volume", "surface", "shape")),
    "A prism is a solid with the same cross-section all the way along, like a triangular prism or "
    "a long box. Its volume is the area of that cross-section times the length. A cube and a "
    "cuboid are prisms too.",
    avoid=("political", "politics", "politic", "media", "public", "social", "through the prism", "prism of",
           "optics", "rainbow", "light", "camera", "lens", "glasses"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "pyramid-what",
    (("pyramid", "pyramids"),
     ("what", "mean", "meaning", "definition", "explain", "volume", "surface", "shape")),
    "A pyramid has a flat base and triangular faces that meet at a point above it; the base can be "
    "any polygon, and a square-based pyramid is the one people picture. Its volume is one third of "
    "the area of the base times the height.",
    avoid=("scheme", "schemes", "scam", "selling", "food", "diet", "egypt", "giza", "tomb",
           "pharaoh", "saqqara", "maya", "aztec", "chichen", "tour", "ticket", "hotel",
           "great pyramid", "pyramid of giza"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "vertex-what",
    (("vertex", "vertices"),
     ("what", "mean", "meaning", "definition", "explain", "corner", "edge", "edges")),
    "A vertex is a corner where two or more edges meet: a cube has eight vertices and a triangle "
    "has three. The plural is vertices, and in a graph a vertex is a point with lines, called "
    "edges, joining it to other points.",
    avoid=("shader", "graphics", "blender", "3d", "game", "engine", "computer", "software",
           "pharma", "pharmaceutical", "stock", "share", "nasdaq"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "cube-number-what",
    (("cube number", "cube numbers", "cubed number", "cubed numbers"),
     ("what", "mean", "meaning", "definition", "explain")),
    "A cube number is what you get when a whole number is multiplied by itself three times: 1, 8, "
    "27, 64, because 4 × 4 × 4 = 64. It is written 4³ and read as four cubed; a square number is "
    "the same idea with two multiplications.",
    avoid=("solid", "shape", "sugar", "ice", "stock", "dice", "die", "rubik", "box", "volume",
           "faces", "root"),
    ask=_DEFINITION_ASK,
    bias=3))

ENTRIES.append(entry(
    "range-maths-what",
    (("range",), ("what", "mean", "meaning", "definition", "explain", "maths", "math",
                  "statistics", "data", "numbers")),
    "In maths the range is the gap between the smallest and largest number: for 3, 7, 9 and 15 it "
    "is 15 - 3 = 12. Put the numbers in order first, then subtract the smallest from the largest.",
    avoid=("cooker", "oven", "hob", "car", "electric", "driving", "mile", "miles", "mountain",
           "golf", "shooting", "rifle", "archery", "price", "product", "salary", "age",
           "temperature", "tide", "wave", "frequency", "radio", "wifi", "signal", "exercise",
           "motion", "kitchen", "range hood", "free range", "range rover", "long range"),
    ask=_DEFINITION_ASK,
    bias=2))

ENTRIES.append(entry(
    "place-value-what",
    (("place value", "place values"), ("what", "mean", "meaning", "definition", "explain")),
    "Place value is what a digit is worth because of where it sits: in 4,582 the 4 is four "
    "thousands, the 5 is five hundreds, the 8 is eight tens and the 2 is two ones. The same digit "
    "means different things in different columns, which is why 0.5 is five tenths and 0.05 is five "
    "hundredths.",
    avoid=("parking", "park", "house", "market", "asset", "valuation", "property", "invest",
           "estate", "neighbourhood", "neighborhood", "area"),
    ask=_DEFINITION_ASK,
    bias=2))

