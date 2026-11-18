"""The energy a person has, which is not the energy they buy.

The answers lane owns this domain. Everything here is data: the row is keyed by meaning (the
dip after lunch, and the tiredness that comes with it) and phrased the way a sensible friend
would answer.

Why the row is here rather than in `sleep` or `home`: the tariff answer (`cheapest-hours`) keys
the word `energy` beside the hours of the day, because on a two-rate tariff the night is
cheaper and people ask when to run a machine. So "how do i keep my energy up in the afternoon"
and "i have no energy in the afternoons" were answered with Economy 7 and a tumble dryer - the
single most confident wrong answer in the knowledge base. `sleep` has `afternoon-slump` and it
says the right thing, but no line carrying the word `energy` could reach it while the tariff
row scored on the same afternoon.

So this row takes the body's energy as its own subject, and the guard keeps the tariff, the
bill, the meter and the appliances out of it.
"""
import re

from .lookup import entry

# The topics this domain answers, as ids from bot/understanding/topics.py.
ANSWERS = ("sleep", "health")

# The energy a body has, rather than the energy a house buys: "no energy" and "keep my energy
# up" are how people say it, and the meter never is. Only the word `energy` is here, because a
# line about being sleepy after lunch is answered well already, by `sleep`'s `afternoon-slump`,
# and taking it would be a change of words rather than a change of answer.
_A_BODYS_ENERGY = (
    "no energy", "energy up", "keep my energy", "keep energy", "my energy", "energy levels",
    "energy level", "more energy", "less energy", "low energy", "lack of energy",
    "energy crash", "energy dip", "energy slump", "energy drops", "energy goes",
    "energy down", "energy left", "energy back", "energy all day",
)

# The time of day the dip is about. The tariff row is asking about hours too, which is why the
# guard, and not this list, is what separates them.
_IN_THE_DAY = (
    "afternoon", "afternoons", "after lunch", "after my lunch", "after eating lunch",
    "midday", "mid-afternoon", "middle of the day", "in the day", "daytime", "after work",
    "2pm", "3pm", "4pm", "3 o'clock", "2 o'clock", "4 o'clock", "post-lunch", "lunchtime",
    "every afternoon", "most afternoons", "all afternoon",
)

# The house's energy: a tariff, a bill, a meter, an appliance, a radiator. Any of these and the
# line is about money or machinery, whatever else it says.
_THE_HOUSE = re.compile(
    r"\b(?:tariff|tariffs|economy\s*7|off-?peak|peak|kwh|kilowatt|meter|metre|reading|"
    r"bill|bills|billed|standing charge|direct debit|supplier|switch|tariffs|"
    r"electric|electricity|gas|heating|boiler|radiator|immersion|"
    r"washing machine|washer|tumble dryer|dryer|dishwasher|immersion|charge|charging|"
    r"battery|car|van|cheapest|cheaper|cheap|price|prices|cost|costs|unit rate)\b",
    re.IGNORECASE)


def _the_energy_is_the_bodys(understood):
    """Whether the energy in the line is the person's, not the house's.

    True means this row may answer. A line about a tariff, a bill, a meter, an appliance or a
    cheaper hour stands down here and keeps the answer it had, and so does a line about charging
    a car or a phone.
    """
    reading = understood or {}
    words = " ".join(str(one) for one in (reading.get("words") or ()))
    text = str(reading.get("clean") or reading.get("text") or "") or words
    return not _THE_HOUSE.search(text)


ENTRIES = [
    entry("the-afternoon-dip",
          (_A_BODYS_ENERGY, _IN_THE_DAY),
          "That dip after lunch is your body clock, not laziness or a lack of willpower, and it "
          "passes. Eat a lunch with protein and fibre rather than a big plate of white carbs, "
          "then get ten minutes of daylight and a short walk at the low point instead of another "
          "coffee. Drink water, keep the caffeine to before 2pm so it does not cost you tonight, "
          "and if you can, take a 15-minute nap rather than a long one.",
          bias=2,
          guard=_the_energy_is_the_bodys),
]
