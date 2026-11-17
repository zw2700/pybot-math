"""A small common input record; skills may add their own semantic readers."""
import re
from dataclasses import dataclass

from .numbers import read_numbers


ASK = re.compile(
    r'\b(?:how (?:many|much|long|old|tall|far)|what (?:percent(?:age)?|is|are|was|will|would|does|did|do|grade|score|mark|number)|'
    r"what's|what (?:distance|speed)|calculate|determine (?:the |her |his |their )?(?:annual |yearly |total )?(?:salary|earnings|cost|price)|find the (?:total|number|combined))\b", re.I)


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
        quantitative = re.match(r'how (?:many|much|long|old|tall|far)|what percent(?:age)?|calculate|find the', question, re.I)
        quantitative = quantitative or re.search(
            r'\b(?:percent(?:age)?|total|combined|number|average|grade|score|mark|weight|height|population|left|remaining|age|ages|distance|speed|area|volume|perimeter)\b',
            question, re.I)
        # A percentage price relation is quantitative even when phrased as
        # "What was the original price?" rather than "How much ...?".
        quantitative = quantitative or (any(n.kind == 'percent' for n in numbers)
                                        and re.search(r'\b(?:price|cost|salary|income|now)\b', question, re.I))
        quantitative = quantitative or (any(n.kind == 'money' for n in numbers)
                                        and re.search(r'\b(?:price|cost|salary|earnings|profit|bill|amount of money)\b', question, re.I))
        implicit_factor = bool(re.search(r'\b(?:twice|thrice|double|triple)\b', text, re.I))
        # A singular event at an explicit interval supplies an implicit one:
        # "takes a tablet every 8 hours ... how many tablets per week?"
        implicit_factor = implicit_factor or bool(re.search(
            r'\b(?:a|an)\s+[a-z]+\s+every\s+\d+\s+(?:seconds?|minutes?|hours?|days?|weeks?)\b', text, re.I))
        enough_numbers = len(numbers) >= 2 or (bool(numbers) and implicit_factor)
        if (not quantitative or not enough_numbers or len(text.split()) < 12
                or len(text[:ask.start()].split()) < 6):
            return None
        return cls(text, text[:ask.start()].lower(), question.lower(), numbers)

    @property
    def values(self):
        return [number.value for number in self.numbers]
