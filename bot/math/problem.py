"""A small common input record; skills may add their own semantic readers."""
import re
from dataclasses import dataclass

from .numbers import read_numbers


ASK = re.compile(
    r'\b(?:how (?:many|much|long|old)|what (?:is|are|was|will|would|grade|score|mark|number)|'
    r"what's|calculate|find the (?:total|number|combined))\b", re.I)


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
        quantitative = re.match(r'how (?:many|much|long|old)|calculate|find the', question, re.I)
        quantitative = quantitative or re.search(
            r'\b(?:total|combined|number|average|grade|score|mark|weight|height|population|left|remaining|age|ages)\b',
            question, re.I)
        implicit_factor = bool(re.search(r'\b(?:twice|thrice|double|triple)\b', text, re.I))
        enough_numbers = len(numbers) >= 2 or (bool(numbers) and implicit_factor)
        if (not quantitative or not enough_numbers or len(text.split()) < 12
                or len(text[:ask.start()].split()) < 6):
            return None
        return cls(text, text[:ask.start()].lower(), question.lower(), numbers)

    @property
    def values(self):
        return [number.value for number in self.numbers]
