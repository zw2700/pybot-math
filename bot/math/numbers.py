"""Read quantities without floating point or rewriting their source offsets."""
import re
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction

from ._number_syntax import (SMALL, TENS, SCALES, FRACTIONS, _WORD_NUMBER,
                             _DIGIT, TOKEN as _TOKEN, parse_number, _ORDINAL_LABEL)


@dataclass(frozen=True)
class Number:
    value: Fraction
    start: int
    end: int
    raw: str
    kind: str = 'number'


def read_numbers(text):
    """Return Number records, with offsets into the original text.

    Numeric and compound ordinals label events rather than count things.
    Ambiguous bare fraction words are left for skills to interpret in context.
    """
    found = []
    for match in _TOKEN.finditer(text):
        raw = match.group()
        suffix = text[match.end():]
        if raw[-1].isalpha() and suffix[:1].isalnum():
            continue
        if raw[-1].isdigit() and re.match(r'(?:st|nd|rd|th)\b', suffix, re.I):
            continue
        # An article and singular ordinal before a noun can label that noun.
        # Fractions instead stand alone or take an of/as/the complement.
        if (re.fullmatch(r'an?[ -]+' + _ORDINAL_LABEL, raw, re.I)
                and re.match(r'\s+(?!(?:of|as|the|is|are|was|were|has|have|had|will|would|can|could)\b)[a-z]', suffix, re.I)):
            continue
        kind = 'percent' if re.search(r'%|percent|per\s+cent', raw, re.I) else (
            'money' if re.search(r'[$£€]', raw) else 'number')
        try:
            found.append(Number(parse_number(raw), match.start(), match.end(), raw, kind))
        except (ValueError, ZeroDivisionError):
            continue
    return found


def format_number(value):
    """Whole numbers stay whole; decimals are calculated from exact fractions."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    with localcontext() as context:
        context.prec = 16
        return format(Decimal(value.numerator) / Decimal(value.denominator), 'f').rstrip('0').rstrip('.')
