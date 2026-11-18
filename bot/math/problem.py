"""A small common input record; skills may add their own semantic readers."""
import re
from dataclasses import dataclass

from .numbers import read_numbers
from ._number_syntax import _MIXED_PARTS


_HOW = r'how\s+(?:many|much|long|old|tall|far|big|heavy|wide|high|deep|fast)'
_MEASURE = (r'(?:percent(?:age)?|total|sum|combined|number|average|grade|score|mark|'
            r'weight|mass|height|length|width|size|angle|lifespan|population|left|remaining|'
            r'ages?|distance|speed|area|volume|perimeter|intake|duration|rate|ratio|fraction|proportion)')
_MONEY = r'(?:price|cost|salary|income|earnings|profit|bill|discount)'
_COMMAND = (r'(?:calculate|(?:find|determine)\s+'
            r'(?:(?:the|a|an|my|your|her|his|its|our|their)\s+)?'
            r'(?:(?:annual|yearly|total|combined|original|final)\s+)?'
            r'(?:' + _MEASURE + '|' + _MONEY + r'|value))')
ASK = re.compile(r'\b(?:' + _HOW + r'|what\s+(?:the\s+)?(?:' + _MEASURE + '|' + _MONEY +
                 r"|year|is|are|was|were|will|would|does|did|do)|what's|" + _COMMAND + r')\b', re.I)
_QUANTITATIVE = re.compile(r'\b' + _MEASURE + r'\b', re.I)
_FINANCIAL = re.compile(r'\b(?:' + _MONEY + r'|amount\s+of\s+money|amount[^?]*paid)\b', re.I)
_SINGULAR_INTERVAL = re.compile(r'\b(?:a|an)\s+[a-z]+(?:[ -]+[a-z]+)*\s+every\s*$', re.I)


@dataclass
class Problem:
    text: str
    body: str
    question: str
    numbers: list

    @classmethod
    def read(cls, text):
        text = str(text).replace('\u2019', "'").replace('\u2013', '-').replace('\u2014', '-')
        asks = list(ASK.finditer(text))
        if not asks:
            return None
        ask = asks[-1]
        numbers = read_numbers(text)
        # An implicit comparison factor (e.g. twice) also supplies a quantity.
        # Require a quantitative question and a narrative with multiple quantities.
        # In particular, a numerical personal statement is never enough to trigger.
        question = text[ask.start():]
        quantitative = re.match(_HOW + '|' + _COMMAND, question, re.I) or _QUANTITATIVE.search(question)
        quantitative = quantitative or re.search(r'^what year\b.*\bborn\b', question, re.I)
        kinds = {n.kind for n in numbers}
        quantitative = quantitative or (bool(kinds & {'money', 'percent'}) and _FINANCIAL.search(question))
        quantitative = quantitative or ('percent' in kinds and re.search(r'\bnow\b', question, re.I))
        implicit_factor = bool(re.search(r'\b(?:twice|thrice|double[ds]?|triple[ds]?)\b', text, re.I))
        implicit_factor = implicit_factor or bool(re.search(r'\bquarterly\b', text, re.I))
        # Any singular event at an explicit interval supplies an implicit one.
        # Use the parsed number span, so written and fractional intervals work
        # with arbitrary event nouns and interval units.
        implicit_factor = implicit_factor or any(
            _SINGULAR_INTERVAL.search(text[:n.start]) and re.match(r'\s+[a-z]+\b', text[n.end:], re.I)
            for n in numbers)
        # Combining a mixed amount into one exact record must not discard its
        # explicit components when deciding whether this is a numeric narrative.
        mixed_amount = any(_MIXED_PARTS.fullmatch(n.raw.lower()) for n in numbers)
        enough_numbers = len(numbers) >= 2 or (bool(numbers) and (implicit_factor or mixed_amount))
        if (not quantitative or not enough_numbers or len(text.split()) < 12
                or len(text[:ask.start()].split()) < 6):
            return None
        return cls(text, text[:ask.start()].lower(), question.lower(), numbers)

    @property
    def values(self):
        return [number.value for number in self.numbers]
