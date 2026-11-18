"""A figure with a unit on it is an amount, not a code.

A degree class is written with a dot or a colon in it, and a phone writes "2:1" as "2 1", so the
knowledge base has to hold "2.1" and "2.2" as words of their own. A joint of meat weighing 2.2
kilos is then the same two characters: "the lamb is 2.2 kilos not 2" was answered with what a
degree passes at, in the middle of a slow roast.

The understanding engine already reads a number and the unit it is counted in - "2.2 kilos" comes
back as a number of 2.2 with a unit of kg - so a card keyed on the digits alone can ask here and
stand down when a unit is on them.
"""
import re

# The units a person says an amount in. A class of degree is never counted in one of these.
UNITS = frozenset("""
kg kgs kilo kilos g gram grams gm gms lb lbs pound pounds st stone stones
l litre litres liter liters ml cl cm mm m metre metres meter meters km
""".split())

# The unit as it is written after the figure, for a reading that did not fill the number in:
# "2.2kg", "2.2 kilos", "2lb".
AFTER_A_FIGURE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kg|kgs|kilo|kilos|g|gram|grams|gm|gms|lb|lbs|pound|pounds|st|stone"
    r"|stones|l|litre|litres|ml|cl|cm|mm|metre|metres|km)\b", re.I)


def a_figure_with_a_unit(understood=None, text=""):
    """True when the line counts something in a unit, so a figure is an amount, not a code."""
    numbers = (understood or {}).get("numbers") or []
    for number in numbers:
        if not isinstance(number, dict):
            continue
        unit = str(number.get("unit") or "").strip().lower()
        if unit in UNITS:
            return True
    body = text or str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return bool(AFTER_A_FIGURE.search(body))
