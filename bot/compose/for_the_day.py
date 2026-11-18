"""A question about today's weather that is really a decision: what decides it, then the figure.

`is it too hot to run` is not a forecast - the bot cannot see today's sky and never will - but it
is not unanswerable either: what is too hot is the same in every case, and that part is worth
saying before naming the place that has the number. The search hedge, which was the reply, says
nothing about heat at all. A laundry pool was written beside it and cut, because on today's main
every washing line is answered by a card before this is reached and the pool could never fire.

It only stands in for the hedge: it is consulted where nothing else claimed the line, and it says
nothing at all unless the line names an activity the day is being weighed against.
"""
import re

# The activity, and the weather word being weighed against it. Kept to the things people actually
# say, and to a line that names no other subject: "is it too hot to run" is a question about today,
# "is it too hot to bake a cake in this oven" is not.
A_DAY_WEIGHED = re.compile(
    r"\b(?:too|warm enough|mild enough|dry enough|cold enough|good enough)\s+"
    r"(?:hot|cold|wet|windy|warm|cool|dry|muggy|humid)?\s*(?:to|for)\s+"
    r"(?:go\s+)?(?:run|running|walk|walking|cycle|cycling|jog|jogging|hike|hiking|"
    r"play|playing|gardening|garden|barbecue|bbq|swim|swimming|paint|painting|"
    r"the\s+dog|a\s+run|a\s+walk|the\s+wash)\b", re.I)
# A question about the day, with no subject but the day: "is it too hot out", "will it be too cold
# later", "is it warm enough out there".
A_DAY_ASKED = re.compile(
    r"\b(?:is|will|would|should)\s+it\s+(?:be\s+)?(?:too\s+|warm\s+enough|dry\s+enough|"
    r"cold\s+enough|nice\s+enough\s+)?(?:hot|cold|wet|windy|warm|muggy|cool|dry)\b"
    r"(?:\s+(?:out|outside|today|tomorrow|later|this\s+\w+))?\s*\??\s*$", re.I)

TOO_HOT = (
    "What is too hot is personal, but the thing that catches people out is the muggy air rather "
    "than the number: above the mid twenties with no breeze, go early or go shorter, and take water "
    "even if you do not feel like it. A weather app has today's figure and the humidity - what time "
    "were you thinking of going?",
    "Heat is judged on the air as well as the temperature: still, humid and in the sun is a lot "
    "harder than the same number with a breeze. If it is close or over about 25 the answer is "
    "early, shorter, and water. The app will have the figure for today - morning or evening for "
    "you?",
)

TOO_COLD = (
    "Cold is the easier one to get wrong: it is wind and wet that turn a cold day into a bad one, "
    "and a dry still frost is fine walking weather once you are moving. Two thin layers and "
    "something for your ears beat one thick coat. The app will have today's wind chill - how long "
    "are you out for?",
    "What decides a cold day is the wind, not the number: the same 3 degrees is fine in a still "
    "street and bitter on a hill. Layers you can open when you warm up, and gloves even when it "
    "does not look like it. A weather app has the wind chill for today.",
)

# The weather word decides which of the two the day is being weighed on. Cold is its own answer
# because "what is too hot is personal" is no reply to somebody asking about a frost.
A_COLD_DAY = re.compile(r"\b(?:cold|freezing|chilly|frost\w*|ice|icy|snow\w*|wind\w*|gale\w*|blowing)\b", re.I)

POOLS = (TOO_HOT, TOO_COLD)


def for_the_ask(clean, repaired=None):
    """The pool of lines for a day weighed against an activity, or None."""
    for line in (clean, repaired):
        said = str(line or "")
        if not said:
            continue
        if A_DAY_WEIGHED.search(said) or A_DAY_ASKED.search(said.strip()):
            return TOO_COLD if A_COLD_DAY.search(said) else TOO_HOT
    return None
