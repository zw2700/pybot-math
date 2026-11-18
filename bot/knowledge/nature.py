"""Nature and weather: what happens outside, and what to do about it.

The answers lane owns this domain. One Entry per everyday phenomenon or outdoors problem,
keyed by the words that identify it ("leaves", "autumn", "colour" rather than one sentence),
so the same fact answers "why do leaves change colour", "why do the leaves go brown in
autumn" and "when do leaves turn". Facts stay at school level and explain the cause in one
line, then add the practical part when there is one.
"""
import datetime as _dt
import re

from .lookup import A_WHAT_TO_WEAR, entry

ANSWERS = ("nature-and-weather",)

# "what makes it snow" asks exactly what "why does it snow" asks, and the row's second group held
# the second verb only: "snow" plus "makes" scored 3, under the four two words have to reach, so
# the plainest way of asking a weather question fell through every row to a search punt. The same
# shape was missing from fog, wind, clouds, rain and rainbows. A shape belongs beside the other
# shapes in the group, not in the subject, so it is written once here.
WHAT_MAKES = ("what makes", "what causes", "what cause", "what made", "what makes it",
              "what causes it", "makes it", "causes it", "how come")

# A line about a bad night is a sleep question, not an astronomy one. "i cant sleep when theres a
# full moon" and "the full moon keeps me awake" were both answered with the length of a lunar
# cycle: the person was telling you they cannot sleep, and the moon was the reason they offered.
# The sleep cards answer it ("same wake-up time, no caffeine after early afternoon, not much
# alcohol"), so the two moon rows stand down for the words below. `bot/knowledge/work.py` keeps
# the same family of words as SLEEP_TALK; this row cannot import that module (its answers import
# this one), so the words are written here too.
A_BAD_NIGHT = ("cant sleep", "can't sleep", "cannot sleep", "couldnt sleep", "couldn't sleep",
               "wont sleep", "won't sleep", "not sleeping", "sleep badly", "sleeping badly",
               "slept badly", "keeps me awake", "keep me awake", "kept me awake",
               "awake all night", "toss and turn", "tossing and turning", "insomnia")


# A new moon, and the length of one full cycle of phases, for the next-full-moon answer.
NEW_MOON = _dt.datetime(2000, 1, 6, 18, 14)
SYNODIC_MONTH = 29.530588853


def _next_full_moon(memory, understood):
    """The date of the next full moon, worked out from a known new moon.

    The phases repeat every 29.53 days, so one reference date plus the date today is
    enough; no table and no network. The answer rounds to the day, which is all that is
    useful for "when is the next full moon".
    """
    now = _dt.datetime.now()
    cycles = (now - NEW_MOON).total_seconds() / 86400.0 / SYNODIC_MONTH
    full = int(cycles - 0.5) + 1
    when = NEW_MOON + _dt.timedelta(days=(full + 0.5) * SYNODIC_MONTH)
    days = (when.date() - now.date()).days
    when_text = f"{when.strftime('%A')} {when.day} {when.strftime('%B')}"
    if days == 0:
        lead = "Tonight is a full moon"
    elif days == 1:
        lead = f"The next full moon is tomorrow, {when_text}"
    else:
        lead = f"The next full moon is on {when_text}, in {days} days"
    return (lead + ". Full moons come round every 29.5 days, so the one after is about "
            "four weeks later; the moon looks biggest when it is low in the sky, which is "
            "an illusion rather than the moon being closer.")

# A named plant has its own care in garden.py, so a generic leaf answer must not swallow it.
# Tomato, potato and chilli are not here on purpose: an overwatered tomato leaf is the same water
# question as a houseplant's, and grow-tomatoes keeps out of a yellow leaf, so leaving them out
# means a yellowing tomato gets the general answer instead of a bare ack.
NAMED_PLANTS = ("basil", "hydrangea", "lavender", "tulip", "garlic", "monstera", "orchid",
                "peace lily", "snake plant", "spider plant", "ficus", "weeping fig",
                "fern", "succulent", "cactus", "cheese plant")

# A tree losing its leaves is the autumn answer; an indoor plant going yellow is not.
TREES = ("tree", "trees", "oak", "maple", "birch", "beech", "ash", "willow", "hedge",
         "shrub", "garden", "outside", "orchard", "woods", "woodland", "forest")



# --- fruit or vegetable, as a table -----------------------------------------
# "is a tomato a fruit", "are bananas berries" and "is a strawberry a berry" are one
# question with one answer shape: where the part comes from, and what cooks call it.
# The produce is data, so a new one is one row.
BOTANICAL_FRUITS = {
    "tomato": "fruit that grows from the flower and holds its seeds",
    "cucumber": "fruit that grows from the flower and holds its seeds",
    "courgette": "fruit that grows from the flower and holds its seeds",
    "zucchini": "fruit that grows from the flower and holds its seeds",
    "aubergine": "fruit that grows from the flower and holds its seeds",
    "eggplant": "fruit that grows from the flower and holds its seeds",
    "pepper": "fruit that grows from the flower and holds its seeds",
    "chilli": "fruit that grows from the flower and holds its seeds",
    "chili": "fruit that grows from the flower and holds its seeds",
    "pumpkin": "fruit that grows from the flower and holds its seeds",
    "squash": "fruit that grows from the flower and holds its seeds",
    "avocado": "fruit that grows from the flower and holds its seeds",
}
TRUE_BERRIES = frozenset(("banana", "tomato", "grape", "blueberry", "cucumber", "pepper",
                          "chilli", "chili", "aubergine", "eggplant", "courgette", "zucchini",
                          "pumpkin", "squash", "avocado", "lemon", "lime", "kiwi"))
AGGREGATE_BERRIES = frozenset(("strawberry", "raspberry", "blackberry"))
KITCHEN_FRUITS = frozenset(("banana", "grape", "blueberry", "lemon", "lime", "kiwi",
                            "cherry"))
PLANT_PARTS = {
    "carrot": "a root", "potato": "a tuber", "onion": "a bulb", "garlic": "a bulb",
    "lettuce": "leaves", "celery": "a stem", "rhubarb": "a stem", "broccoli": "a flower",
    "cauliflower": "a flower",
}
PRODUCE = tuple(sorted(set(BOTANICAL_FRUITS) | TRUE_BERRIES | AGGREGATE_BERRIES
                        | KITCHEN_FRUITS | set(PLANT_PARTS)))


# A crop that will not set, is dropping its flowers or has come out small is the growing
# question, not the botanical one: "why wont my peppers fruit" was told that a pepper is
# botanically a fruit. The definition stands down whenever the line names one of these crops and
# says something about what the plant is doing, which is the same split the garden rows make.
_SETTING_CROPS = frozenset((
    "pepper", "peppers", "chilli", "chillies", "chili", "tomato", "tomatoes", "aubergine",
    "aubergines", "eggplant", "eggplants", "courgette", "courgettes", "zucchini", "cucumber",
    "cucumbers", "squash", "pumpkin", "pumpkins", "strawberry", "strawberries", "bean", "beans",
    "pea", "peas", "melon", "melons", "raspberry", "raspberries", "blackberry", "blackberries",
))
_PLANT_TROUBLE = re.compile(
    r"\b(?:not|never|no|none|nothing|wont|won't|arent|aren't|isnt|isn't|hasnt|hasn't|havent|"
    r"haven't|didnt|didn't|cant|can't|will not|drop|drops|dropping|dropped|fall|falls|falling|"
    r"fell|small|tiny|shrivelled|bitter|yellow|brown|wilting|rot|rotten|split)\b")


def _not_the_definition(understood):
    """True while the line asks what the produce is, not what its plant is doing."""
    line = ((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    words = set(re.findall(r"[a-z']+", line))
    return not (words & _SETTING_CROPS and _PLANT_TROUBLE.search(line))


# The harvest is the other question the word "fruit" is asked in: "will my tomatoes still fruit
# this year" was told "Botanically a tomato is a fruit that grows from the flower and holds its
# seeds. Cooks call it a vegetable ...", which answers a question nobody asked. The produce word
# is the same word; the ask is about the crop, and garden.py's ripening rows answer it.
THE_HARVEST_ASK = (
    "still fruit", "will it fruit", "will they fruit", "will my fruit", "fruit this year",
    "still crop", "will it crop", "will they crop", "crop this year", "still produce",
    "more fruit", "set fruit", "setting fruit", "fruiting", "yield", "harvest",
    "how much fruit", "any fruit", "still get fruit", "get fruit this",
)


def _fruiting_of_a_crop(line):
    """True when the line asks whether a plant will crop, not what kind of thing the crop is."""
    return any(word in line for word in THE_HARVEST_ASK)



def _fruit_or_berry(memory, understood):
    """Whether the produce in the line is a fruit, a berry or a root, and why."""
    line = (understood.get("text") or understood.get("clean") or "").lower()
    if _fruiting_of_a_crop(line):
        return None
    word = ""
    for name in PRODUCE:
        if name.endswith("y"):
            stem, plural = name[:-1], "(?:y|ies)"
        elif name.endswith("o"):
            stem, plural = name[:-1], "(?:o|os|oes)"
        elif name.endswith(("ch", "sh", "s", "x")):
            stem, plural = name, "(?:es)?"
        else:
            stem, plural = name, "s?"
        if re.search(r"\b" + re.escape(stem) + plural + r"\b", line):
            word = name
            break
    if not word:
        return ("Botanically a fruit is the part that grows from the flower and holds the seeds, "
                "so tomatoes, cucumbers and peppers are fruits. A berry is a fruit from one ovary "
                "with seeds in the flesh, which makes bananas berries but strawberries not.")
    art = "an" if word[:1] in "aeiou" else "a"
    asks_berry = "berr" in line
    asks_vegetable = "vegetable" in line and not asks_berry
    if word in PLANT_PARTS:
        part = PLANT_PARTS[word]
        if asks_vegetable:
            return (f"Yes - in the kitchen {art} {word} is a vegetable, but botanically it is {part}, "
                    f"not a fruit: the fruit is the part that holds the seeds.")
        return (f"No - {art} {word} is {part}, not a fruit. The fruit is the part that holds the "
                f"seeds, so {art} {word} is a vegetable in the kitchen and {part} in the ground.")
    if asks_berry:
        if word in AGGREGATE_BERRIES:
            return (f"No - {art} {word} is not a true berry: its seeds are on the outside and each "
                    f"one is its own tiny fruit, so botanists call it an aggregate. A banana or "
                    f"a tomato really is a berry, which is where the rule surprises people.")
        if word == "cherry":
            return ("No - a cherry is a drupe: one seed inside a hard stone, not a berry. A "
                    "banana or a tomato really is a berry, which is where the rule surprises "
                    "people.")
        return (f"Yes - {art} {word} is a berry, botanically: it grows from one ovary and has its "
                f"seeds inside the flesh. A strawberry is not, because its seeds sit on the "
                f"outside.")
    if word in BOTANICAL_FRUITS:
        return (f"Botanically {art} {word} is a {BOTANICAL_FRUITS[word]}. Cooks call it a vegetable "
                f"because it is savoury and goes in mains, but that is a kitchen word, not a "
                f"plant one.")
    if word in KITCHEN_FRUITS:
        return (f"Botanically {art} {word} is a fruit, and in the kitchen too: it grows from the "
                f"flower and holds its seeds. A vegetable is a different part of the plant - a "
                f"root, a leaf or a stem.")
    return (f"Botanically {art} {word} is a fruit, because it grows from the flower and holds its "
            f"seeds. A vegetable is the other parts of the plant, such as roots, leaves and "
            f"stems.")

def _the_wet_day(memory, reading):
    """What the rain does to the plan, and what to do when it is set in for the week."""
    line = str((reading or {}).get("clean") or (reading or {}).get("text") or "").lower()
    said = ("Rain rearranges a day out rather than cancelling it: keep the outdoor parts loose - "
            "a walk, a beach, a garden - and put one indoor thing into each day, a museum, a pool, "
            "a long lunch or a castle you can go round under cover. Book only what you can move "
            "and decide on the morning, when you can see the sky.")
    if any(word in line for word in ("all week", "every day", "a lot", "pours", "turns",
                                     "weather is bad")):
        said += (" If it is set in for the week, pick one proper indoor day rather than a wet walk "
                 "every day, and keep the evenings for the things that need no weather at all.")
    return said


# A plant the person is looking after is a plant of theirs going wrong, and the season is not the
# question. The line "and should i take the yellow leaves off" names no plant at all - it names the
# leaf - so the leaf word alone reached this card and the person was told why trees drop their
# leaves in autumn, three turns after asking about their tomatoes. Any plant they own in the last
# few turns is enough to stand this card down; a tree is not on the list, because a tree's leaves
# in autumn are exactly this question.
_PLANTS_IN_HAND = (
    "tomato", "tomatoes", "pepper", "peppers", "courgette", "courgettes", "cucumber",
    "cucumbers", "chilli", "chillies", "chili", "potato", "potatoes", "aubergine", "aubergines",
    "strawberry", "strawberries", "raspberry", "raspberries", "blueberry", "blueberries",
    "basil", "mint", "parsley", "coriander", "thyme", "rosemary", "sage", "chives", "oregano",
    "houseplant", "houseplants", "house plant", "house plants", "monstera", "orchid",
    "peace lily", "spider plant", "snake plant", "pothos", "aloe", "cactus", "succulent",
    "bonsai", "ficus", "fern", "seedling", "seedlings", "cutting", "cuttings", "my plant",
    "my plants", "veg", "vegetables", "allotment",
)


def _the_older_turns(memory, keep=3):
    """What the last few turns said, for a follow-up that names only the part."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    said = " ".join(str(turn.get("user") or "") for turn in turns[-keep:]
                    if isinstance(turn, dict))
    return " " + re.sub(r"[^a-z0-9' ]+", " ", said.lower()) + " "


def _a_plant_they_own_is_the_subject(memory):
    """True when the conversation is about a plant the person is looking after."""
    said = _the_older_turns(memory)
    return any(" %s " % word in said or " %ss " % word in said
               for word in _PLANTS_IN_HAND)


def _the_autumn_leaves(memory, reading):
    """Why leaves turn, unless the leaves are a plant of theirs going wrong."""
    if _a_plant_they_own_is_the_subject(memory):
        return None
    return (
        "Shorter days tell trees to stop making chlorophyll, the green stuff, and as it fades "
        "the yellow and orange pigments underneath show through; some trees also make red "
        "pigments. The tree then seals off each leaf and lets it drop, so it loses less water "
        "over winter.")


def _the_tide(memory, reading):
    """The tide at the place the person is going: a table for one port, not the sea's physics.

    "what time is high tide", "how high is the tide" and "is the tide coming in" are one shape of
    question - a number for one port on one day - and the answer a person acts on is that port's
    own table. What the bot can add is how to read it, how much later it comes each day, and how
    much water to leave behind on flat sand. The why of the bulge stays with the `tides` row.
    """
    line = str((reading or {}).get("clean") or (reading or {}).get("text") or "").lower()
    if any(word in line for word in ("in or out", "coming in", "going out", "tide doing",
                                     "rising", "falling", "dropping", "state of the tide")):
        return ("Watch it rather than guess: on a flooding tide the water climbs a few inches "
                "every ten minutes and the weed floats past in one direction; on the ebb the wet "
                "sand shows above the water line and the rocks come out. The nearest port's table "
                "tells you the turn of it, and the turn is what the times are.")
    if any(word in line for word in ("causeway", "cross the sand", "crossing the sand",
                                     "walk across", "mudflat", "quicksand", "tidal road")):
        return ("Do not cross on a guess, and never on another port's table: the bay's own "
                "crossing times are published by the coastguard or the local guides, and they are "
                "the only ones that count. Tell somebody where you are going and when you will be "
                "back, and never park below the high-water mark - cars are lost that way every "
                "year.")
    if any(word in line for word in ("swim", "swimming", "paddle", "paddling", "in the water")):
        return ("Swim near the turn of the tide rather than on a big spring ebb, keep to a "
                "lifeguarded beach, and stay off flat sand where the flood gets behind you: the "
                "water comes back faster than it left. The nearest port's table gives you the "
                "turn, and aim to be out of it well before.")
    return ("A tide time is local, so the nearest port's table is the only one that counts - the "
            "harbour, the coastguard, or the tide page for that port - and high water comes about "
            "50 minutes later each day, so yesterday's table is no use. The sea slacks for a few "
            "minutes either side of the turn, and on flat sand the flood comes in faster than it "
            "looks: be off the beach an hour before the table says.")



# The row's key holds "summer", "june", "longer" and "longest" beside the winter words, and a
# winter paragraph answered all of them with December: "how many hours of daylight in june"
# was told "the day is short". Daylight is one tilt read two ways, so the reply reads the line
# and gives the half that was asked about.
# The short half is the sharper signal: a line with a short word, a December date or an early
# dark in it wants the winter figure even when it names the summer for comparison. Everything
# else that names the summer or the long days wants the June one.
# "winter" is not on this list on purpose: "why are the days longer in summer than winter" names
# the winter only to compare with it, and the short words are what make the line a short-day one.
_DAYLIGHT_SHORT_WORDS = ("december", "shorter", "shortest", "shorter days",
                         "short days", "the days are short", "dark at", "4pm", "5pm",
                         "21 december")
_DAYLIGHT_LONG_WORDS = ("summer", "june", "july", "august", "longer", "longest",
                        "longer days", "midsummer", "solstice", "light nights",
                        "never gets dark")
_DAYLIGHT_WINTER = (
    "Daylight hours swing with the Earth's tilt: your half leans away from the Sun in "
    "winter, so it rises later, climbs less high and sets earlier, and the day is short. In "
    "the UK that is about 7 hours 45 minutes of daylight around 21 December, against 16 "
    "hours 45 minutes in June.")
_DAYLIGHT_SUMMER = (
    "The same tilt the other way: your half leans towards the Sun in summer, so it rises "
    "earlier, climbs higher and sets later, and the day is long. In the UK that is about 16 "
    "hours 45 minutes of daylight around 21 June, against 7 hours 45 minutes in December.")
# The north of Scotland is the line people are actually after when they say the summer
# evening is still light: the sun only dips just below the horizon there.
_DAYLIGHT_SCOTLAND = (
    " In the far north of Scotland around midsummer the sun only dips just below the horizon, "
    "so it never gets properly dark - the simmer dim - and Shetland's longest day is over 18 "
    "hours of light.")

# A line that names a month other than December or June is asking about that month, and neither
# card is about it: "when does it get dark in october" was given the 21 December figure. A table
# of the hours of daylight around the middle of each month, for the UK, answers the month the
# line named; the two solstice months keep their own cards, which say why.
_DAYLIGHT_BY_MONTH = (
    ("january", 8, 10), ("february", 9, 55), ("march", 11, 55), ("april", 14, 0),
    ("may", 15, 55), ("september", 12, 30), ("october", 10, 30), ("november", 8, 40),
)

def _month_daylight(said):
    """The month's own figure, or None when the line named no month we answer for."""
    said = " " + str(said or "").strip() + " "
    for name, hours, minutes in _DAYLIGHT_BY_MONTH:
        # "may" is a modal verb as often as a month, so it needs the words people put round it
        if name == "may":
            if " in may " in said or " of may " in said or " during may " in said \
                    or said.rstrip().endswith(" may"):
                return (name, hours, minutes)
            continue
        if " " + name + " " in said:
            return (name, hours, minutes)
    return None

def _daylight(memory, reading):
    """The long day or the short one, whichever the line is asking about."""
    said = " ".join(str((reading or {}).get("clean") or (reading or {}).get("text") or "")
                    .split()).lower()
    if any(word in said for word in _DAYLIGHT_SHORT_WORDS):
        return _DAYLIGHT_WINTER
    if any(word in said for word in _DAYLIGHT_LONG_WORDS):
        if "scotland" in said or "scottish" in said or "shetland" in said:
            return _DAYLIGHT_SUMMER + _DAYLIGHT_SCOTLAND
        return _DAYLIGHT_SUMMER
    if " december " not in said:
        month = _month_daylight(said)
        if month is not None:
            name, hours, minutes = month
            return ("In the UK, about the middle of %s gives roughly %d hours %d minutes of "
                    "daylight, and it is still changing fastest around the equinoxes - a week "
                    "either side of one moves the sunset by several minutes." % (name, hours, minutes))
    return _DAYLIGHT_WINTER


ENTRIES = [
    # A weather front is school science and it is asked as "what is a weather front", a plain
    # "what is" line: the weathering row used to take it (and "weather" alone), so the boundary
    # between two air masses was explained as rock breaking up.
    entry("weather-front-what",
          (("front", "fronts"),
           ("weather", "warm", "cold", "occluded", "stationary")),
          "A front is the boundary where a warm air mass meets a cold one. On a cold front the "
          "cold air pushes under the warm: heavy rain in a narrow band, then a sharp drop in "
          "temperature. On a warm front the warm air climbs over the cold: thickening cloud, "
          "drizzle, and it turns milder. The rain comes at the front and the clearing is behind "
          "it.",
          avoid=("garden", "shed", "door", "window", "battle", "war", "beach", "shop", "queue",
                 "house", "car", "row", "seat")),

    entry("storm-distance", (("thunder", "lightning", "storm"), ("far", "distance", "away", "how",
                                                                 "count", "hear", "close")),
          "Count the seconds between the lightning and the thunder: every 3 seconds is about 1 km "
          "(5 seconds per mile). If the gap is under 30 seconds, the storm is close enough to be "
          "dangerous, so get indoors."),
    # A school comparison of two storms: nothing held "hurricane", so the line got a search
    # hedge. One row per pair of things people mix up, keyed on both names.
    entry("hurricane-or-tornado", (("hurricane", "hurricanes", "typhoon", "cyclone", "tornado",
                                    "tornadoes", "twister"),
                                   ("difference", "differ", "different", "vs", "versus", "worse",
                                    "stronger", "same", "which", "what", "how", "compare")),
          "A hurricane is a whole storm system hundreds of kilometres across, born over warm sea "
          "and lasting days, with winds over 119 km/h. A tornado is a narrow funnel of spinning "
          "air under a thunderstorm, usually tens of metres wide and gone in minutes. Hurricanes "
          "are forecast days ahead; tornadoes give minutes."),
    entry("thunderstorm-outside", (("thunderstorm", "storm"),
                                   ("outside", "caught", "open", "safe", "shelter", "should", "what", "do")),
          "Get into a building or a hard-topped car, away from windows, and stay there 30 minutes "
          "after the last thunder. If you're caught in the open, move off high ground and away "
          "from lone trees, water and metal fences, and crouch low on the balls of your feet."),
    entry("flood-warning", (("flood", "flooding"), ("warning", "what", "should", "do", "home",
                                                    "safe", "water")),
          "Move valuables and medicines upstairs, unplug what you can safely reach and stay out of "
          "the water: 30 cm of moving water can float a car. Follow your local flood service, and "
          "if they tell you to leave, go early rather than wait to see how high it gets.",
          # "how do i stop the flood of emails" is an inbox question, and a flood of post or of
          # news is not water either: the count of a thing is the card for that thing's overload.
          avoid=("email", "emails", "inbox", "newsletter", "newsletters", "post", "letters",
                 "messages", "notifications", "comments")),
    entry("heatwave", (("heatwave", "heat wave"), ("what", "do", "safe", "hot", "keep", "cool")),
          "Keep the sun out during the day, open windows at night, drink water before you feel "
          "thirsty and check on anyone elderly or unwell nearby. Avoid heavy work between 11am and "
          "3pm, when the sun is strongest."),
    entry("forecast-wrong", (("forecast", "weather forecast", "forecasts"),
                             ("wrong", "often", "why", "accurate", "reliable", "right")),
          "Weather is chaotic: a tiny error in today's readings grows over days, so a forecast a "
          "week ahead is a good guess and tomorrow's is usually close. Showers are also small "
          "enough to miss your street while soaking the next town, which is why a 30% chance of "
          "rain still means a wet walk sometimes."),
    # The most common worry there is about a day out, and it was answered with a search hedge:
    # "what if it rains" wants to know what the rain does to the plan, not why the sky does it.
    # Keyed on the worry shape rather than the word "rain", because the rain lines that are not a
    # plan already have their own answers - a rainy Sunday in, a wet walk, the washing on the line
    # - and they are all named in the avoid list below.
    entry("wet-day-on-a-plan",
          (("if it rains", "if it rains all week", "if it rains every day", "if its raining",
            "if it's raining", "if it rains a lot", "if it pours", "if the weather turns",
            "if the weather is bad", "rains all week", "raining all week", "wet all week"),
           ("what", "should", "shall", "can", "could", "do", "will", "if", "and", "plan")),
          _the_wet_day,
          avoid=("washing", "laundry", "washing line", "pegs", "tumble dryer", "dryer",
                 "leak", "leaks", "leaking", "damp", "roof", "gutter", "guttering", "flood",
                 "garden", "watering", "water the", "plants", "hose", "lawn", "grass seed",
                 "flight", "flights", "airport", "match", "cricket", "football", "rugby",
                 "tennis", "cancelled", "called off", "school", "kids", "children", "toddler",
                 "baby", "bored", "drive", "driving", "car", "bike", "cycle", "commute",
                 # a step target and a walk are the setting the weather is mentioned in, not the
                 # plan the rain is about: "how many steps a day if its raining" was answered
                 # with a wet day out.
                 "step", "steps", "how many", "walking", "steps a day")),
    entry("rain-why", (("rain", "rains", "raining", "raining so much"),
                       ("why", "does", "form", "forms", "falls", "come", "cloud", "what",
                        "what is") + WHAT_MAKES),
          "The sun evaporates water, it rises and cools into cloud droplets, and the droplets "
          "bump together until they're heavy enough to fall. Rain is just that water coming back "
          "down, usually after a cloud has grown thick and tall.",
          # what to wear in it is a clothes question, and the clothes rows answer it
          avoid=A_WHAT_TO_WEAR),
    entry("sunset-orange", ("sunset", ("orange", "red", "sky", "why", "sunrise", "evening")),
          "Low sun sends its light through far more atmosphere, which scatters the blues away and "
          "leaves the reds and oranges to reach you. Dust and cloud make it stronger, which is why "
          "the best sunsets come after a clear, dusty day."),
    entry("rainbow", ("rainbow", ("why", "form", "forms", "make", "makes", "made", "appear",
                                     "how come", "happen", "see", "colour", "colours", "cause",
                                     "causes", "what")),
          "Sunlight bends as it enters raindrops, reflects off the back and bends again on the way "
          "out, which splits it into colours. You only see one with the sun behind you and rain in "
          "front, and the red band is always on the outside of the arc."),
    # "why do my glasses fog up" is a lens question, and the weather answer sent that person out
    # in dipped headlights; the wearing words take it out of the running.
    entry("fog", (("fog", "foggy", "mist", "misty"),
                  ("why", "form", "forms", "does", "drive", "driving", "safe", "thick",
                   "what", "what is") + WHAT_MAKES),
          "Fog forms when damp air cools to the point where its water vapour condenses into "
          "droplets near the ground. Driving in it, slow down and use dipped headlights or fog "
          "lights, not full beam: full beam bounces off the fog and makes it worse.",
          avoid=("glasses", "spectacles", "specs", "goggles", "lenses", "lens", "visor", "mask",
                 "mirror", "windscreen", "windshield", "bathroom")),
    entry("clouds", ("cloud", ("what", "made", "form", "forms", "why", "white", "fluffy")
                              + WHAT_MAKES),
          "Clouds are tiny water droplets or ice crystals hanging on specks of dust, formed when "
          "rising damp air cools. They look white because the droplets scatter all colours of "
          "sunlight equally; they turn grey when they're thick enough to block the light."),
    entry("snow", (("snow", "snows", "snowing"),
                   ("why", "form", "forms", "does", "made", "fall", "falls", "happen", "flake",
                    "what", "what is") + WHAT_MAKES),
          "Snow forms when water vapour freezes straight into ice crystals high in a cloud, and the "
          "crystals stick together as they fall. It only reaches the ground as snow if the air "
          "stays cold all the way down, which is why a cold snap often brings sleet instead.",
          avoid=A_WHAT_TO_WEAR),
    entry("wind", (("wind", "winds", "windy", "breezy", "gale", "gales"),
                   ("why", "blow", "blows", "does", "form", "cause", "windy", "so windy",
                    "what", "what is") + WHAT_MAKES),
          "Wind is air moving from an area of high pressure to one of low pressure, and the sun "
          "creates those differences by heating land and sea unevenly. The bigger the pressure "
          "gap, the stronger the wind.",
          # "why do i feel windy" is gas, and the science card answered it about the weather the
          # moment "windy" joined the subject. The feeling words are the fence; the bloating row
          # keeps those lines exactly as it had them.
          avoid=("feel windy", "feeling windy", "felt windy", "bloated", "bloating", "trapped wind",
                 "fart", "farting", "gas", "my gut", "stomach", "tummy", "how windy")
                 # and what to put on against it is a clothes question, not a science one
                 + A_WHAT_TO_WEAR),
    # "why do we have seasons" put the ask before the subject, and the two parts of a key are
    # read in the order they are written, so the row scored nothing and the baby-food spice
    # table answered it. The subject-first phrasings go in the first part beside the words.
    entry("seasons", (("season", "seasons", "why do we have seasons",
                       "why does the earth have seasons", "what causes the seasons",
                       "explain the seasons", "why do we get seasons"),
                      ("why", "change", "summer", "winter", "cause", "earth", "tilt", "have",
                       "happen", "seasons")),
          "Seasons come from the Earth's 23.5-degree tilt, not from how close it is to the sun. "
          "When your half of the planet leans towards the sun you get summer: longer days and more "
          "direct light."),
    # A tide asked about as a time, a height or a crossing is a local table, and answering it with
    # why the sea bulges is no use to somebody standing on a beach. This row takes the number
    # questions; the why words stand it down so "how do tides work" and "what causes tides" keep
    # the explanation below. "how high" and "how low" are the same question as "what time".
    entry("tide-times", (("tide", "tides", "tidal", "high water", "low water",
                          # The causeway is the tide's question even when the line never says
                          # "tide": "when can i walk across the causeway" is the crossing times.
                          "causeway", "tidal road", "tidal causeway"),
                         ("time", "times", "table", "tables", "timetable", "when", "today",
                          "tomorrow", "tonight", "high tide", "low tide", "height", "how high",
                          "how low", "across the causeway", "now", "walk", "crossing",
                          "cross", "safe",
                          # The state of it: "is the tide in or out", "is the tide coming in",
                          # "whats the tide doing" - one state, told by watching the water.
                          "in or out", "coming in", "going out", "doing", "up or down",
                          "high or low", "turn")),
          _the_tide,
          avoid=("why", "cause", "causes", "work", "works", "working", "moon", "sun", "gravity",
                 "explain", "neap", "spring tide", "spring tides", "planet", "affect",
                 # a rock pool is a place to look in, and "low tide is best for rock pools" is
                 # not asking for a table.
                 "rock pool", "rock pools", "rockpool", "rockpools", "fishing", "fish"),
          bias=1),
    # "why are the days shorter in winter", "why is it dark at 4pm" and "how many hours
    # of daylight in december" all got a search hedge, and "why does it get dark so
    # early" was answered with the washing machine's 30C card, because "light" and
    # "dark" are how a wash is sorted. The row is the short days, so it asks for the
    # length words and stands aside for the wash.
    entry("winter-daylight", (("daylight", "days", "day", "dark", "light", "sunlight",
                               "hours of light"),
                             ("shorter", "short", "shortest", "longest", "longer",
                              "hours", "early", "earlier", "get dark", "dark at", "sunset",
                              "sunrise", "4pm", "5pm", "6pm", "december", "june", "winter",
                              "summer")),
          _daylight,
          bias=2,
          avoid=("wash", "washing", "laundry", "load", "loads", "whites", "colours", "colors",
                 "dark colours", "towels", "bedding", "sheets", "machine", "programme", "shirts",
                 "denim", "wool", "silk", "bleach", "iron", "tumble", "dryer", "light bulb",
                 "bulb", "lamp", "traffic light", "beer", "lager", "stout", "spice", "spices",
                 "mars", "jupiter", "saturn", "venus", "mercury", "neptune", "uranus", "planet",
                 "planets", "moon", "year", "years", "movie", "film", "book", "shift", "work",
                 "here", "room", "rooms", "kitchen", "bedroom", "hallway", "outside", "screen",
                 "phone", "camera", "photo", "photo is", "hair", "skin", "nail", "nails",
                 # "hours" is this row's word for the length of the day, and "how many hours of
                 # revision a day" and "how many hours should i study a day" are asking how long
                 # to work, not when the sun goes down: the activity is the subject of the line.
                 "revision", "revise", "revising", "study", "studying", "studied", "coursework",
                 "homework", "exam", "exams", "revised",
                 "earth", "night", "nights", "tonight", "today", "tomorrow", "sky", "stars",
                 "eclipse", "horizon", "eyes", "sleep", "blind", "circles", "bags", "under my eyes",
                 "spots", "patches", "stains", "roots", "hair dye", "boiler", "radiator",
                 "radiators", "thermostat", "central heating", "heating", "hot water", "bill",
                 "bills", "gas bill", "electricity", "tariff", "immersion", "energy", "cheaper",
                 "cost", "supplier", "meter", "standing charge", "double", "insulation", "loft",
                 "draught", "draughts", "damp", "condensation", "mould", "thermals")),
    # "how long is a day on earth" was answered with the Earth's diameter, because the size
    # row and this one share the word "earth". A day is 24 hours; the length of daylight is
    # the row above.
    entry("length-of-a-day", (("day", "days", "earth day"),
                             ("how long", "length", "how many hours", "hours long", "24 hours")),
          "A day is 24 hours - the time from one noon to the next. One full turn against the "
          "stars takes 23 hours 56 minutes; the extra four minutes are because the Earth has "
          "moved on along its orbit as it turned.",
          avoid=("daylight", "dark", "shorter", "shortest", "longer", "longest", "sun",
                 "sunlight", "winter", "summer", "december", "june", "mars", "moon", "planet",
                 "planets", "jupiter", "saturn", "venus", "mercury", "work", "shift", "school",
                 "off", "holiday", "bad day", "good day", "one day", "someday", "birthday",
                 "mothers day", "valentines", "pay", "sick", "feed", "walk",
                 # A day somewhere other than Earth is not this row's 24 hours: "how long is a
                 # day at the north pole", "in space" and "in hospital" are a different question
                 # each, and a confident answer from the wrong one is worse than the punt.
                 "hospital", "pole", "poles", "north pole", "south pole", "arctic", "antarctic",
                 "desert", "space", "in space", "orbit", "station", "iss")),
    # "why is it colder in winter" and "why is it so cold in winter" got a hedge and the
    # summer card. The winter question is the same tilt, read the other way.
    entry("winter-cold", (("winter", "colder", "cold", "coldest"),
                          ("why", "so cold", "colder", "coldest", "than summer", "than june",
                           "more", "cause", "explain", "feels")),
          "Winter is cold because your half of the Earth leans away from the Sun: the sunlight "
          "comes in at a low angle and is spread over more ground, and the shorter days give the "
          "ground less time to warm up. That is also why the winter sun feels weak even on a "
          "clear day.",
          avoid=("boiler", "radiator", "radiators", "thermostat", "central heating", "heating",
                 "hot water", "plumber", "radiator", "thermals", "coat", "dressing", "dress",
                 "wear", "what should i", "i have a cold", "cold sore", "sore throat", "flu",
                 "chest", "cough", "shiver", "chills", "freezing pipes", "frozen pipe",
                 "fridge", "freezer", "cold brew", "cold water", "beer", "summer", "all the time",
                 "always", "feel cold", "feeling cold", "feel the cold", "get cold", "getting cold",
                 "hands", "feet", "toes", "fingers", "shivery", "shiver", "i am cold", "im cold",
                 "i'm cold", "in bed", "bedroom", "house", "flat", "office", "coat", "jumper",
                 # a building that is cold is a heating question, not the tilt: the house rows
                 # answer it, and a shed, a cellar and a basement were all told that winter is
                 # cold because the Earth leans away from the Sun, which is true of the season
                 # and not of the room the person is standing in.
                 "shed", "sheds", "cellar", "cellars", "basement", "basements", "workshop",
                 "workshops", "garage", "garages", "conservatory", "loft", "attic", "hallway",
                 "hall", "porch", "caravan", "bungalow", "cottage", "kitchen", "living room",
                 "sitting room", "lounge", "room", "rooms", "home", "homes", "housemate",
                 "outbuilding", "outbuildings", "greenhouse", "tent", "car", "van", "classroom",
                 # "why is it cold in the morning" and "at night in the desert" are forecast
                 # lines and a desert night is a different physics: neither is the tilt.
                 "morning", "mornings", "at night", "night", "nights", "desert", "the desert",
                 "north pole", "south pole", "arctic", "antarctic", "so long", "how long",
                 # a mountain answers "why is it colder at the top of a mountain" with the
                 # lapse rate, the sea has its own warmth, and today's weather is a forecast:
                 # the tilt is right for none of the three, so this row stands down for them
                 "mountain", "mountains", "mountain top", "hill", "hills", "altitude",
                 "higher up", "at the top of", "summit", "sea", "ocean", "the sea", "the ocean",
                 "seawater", "sea water", "today", "tomorrow", "tonight", "this week",
                 "this morning", "right now", "at the moment", "forecast", "weather")),
    entry("tides", (("tide", "tides"), ("why", "moon", "sun", "cause", "causes", "high", "low",
                                   "rise", "work", "works", "how", "what")),
          "The Moon's gravity pulls the sea towards it, making a bulge on the near side and a "
          "matching one on the far side, and the Earth turns through both. That gives two high "
          "tides roughly 12 hours 25 minutes apart, and the Sun's pull makes spring tides bigger "
          "at full and new moon.",
          # The time and the height are the tide-times row above: this one is the why, and
          # standing down on them is what stops it answering "what time is high tide" with the
          # bulge on both sides of the planet.
          # "coming in" is not here: read loosely it meets "why does the tide come in", which is
          # the question this row is for.
          avoid=("time", "times", "table", "timetable", "when", "today", "tomorrow", "tonight",
                 "height", "causeway", "doing", "swim", "swimming", "crossing")),
    entry("northern-lights", (("northern lights", "aurora", "aurora borealis"),
                              ("why", "what", "cause", "see", "where", "when", "happen")),
          "Charged particles from the sun hit gases high in the atmosphere and make them glow: "
          "green from oxygen, reds and purples from nitrogen. You need a dark, clear night and a "
          "high latitude, so northern Scotland, Iceland and Scandinavia are the usual spots."),

    # --- plants and animals --------------------------------------------------
    entry("leaves-autumn", (("leaf", "leaves"), ("change", "colour", "color", "autumn", "fall",
                                                 "turn", "brown", "red", "yellow", "lose", "drop",
                                                 "tree")),
          _the_autumn_leaves,
          avoid=("plant", "houseplant", "basil", "pot", "indoor", "tips", "house", "sick",
                 # a named tree in a pot losing leaves is the bonsai card's question: "my bonsai
                 # is dropping leaves" was told why leaves fall in autumn
                 "bonsai", "bonsais", "bonsai tree", "ficus",
                 # a leaf the asker owns is a plant of theirs going wrong, not the season
                 "my leaves", "my leaf", "my plant",
                 "wrong", "mint", "herb", "herbs", "parsley", "coriander", "tomato",
                 "spots", "curling", "wilting", "drooping", "not looking",
                 # a named houseplant with brown or crispy leaves is an indoor question, and
                 # garden.py's houseplants entry answers it
                 "monstera", "orchid", "peace lily", "spider plant", "snake plant",
                 "pothos", "aloe", "cactus", "succulent", "fiddle leaf", "potted",
                 # a leaf in a bag is food, not a season: "can i eat a yellow spinach leaf" was
                 # told why trees drop their leaves
                 "spinach", "kale", "lettuce", "rocket", "greens", "cabbage", "chard",
                 "eat", "eating", "ate", "bag of", "salad")
                 + NAMED_PLANTS,
          # "why do leaves turn yellow in autumn" also fits garden's yellow-leaf triage, and
          # the season fact is the one asked for. One point of bias wins it on the merits,
          # without standing the plant-care entry down for "my plant is dying this autumn".
          bias=1),
    entry("pests-eating-plants", (("my plant", "my plants", "my leaves", "the leaves",
                                   "my veg", "my vegetables", "my crops", "my flowers",
                                   "seedlings", "the plants", "the veg",
                                   # the same line with the plant named instead of "plants":
                                   # "something is eating my basil leaves" was the herb-pot
                                   # answer, because "basil" is in no row here
                                   "my basil", "my mint", "my parsley", "my coriander",
                                   "my chives", "my rosemary", "my thyme", "my tomatoes",
                                   "my tomato", "my lettuce", "my strawberries", "my herbs",
                                   "my herb", "my rose", "my roses", "my shrub", "my shrubs",
                                   "my tree", "my seedlings", "my cabbage", "my kale",
                                   "my courgettes", "my courgette", "my beans", "my peas",
                                   "my potatoes", "my carrots", "my hostas", "my hosta",
                                   "my lupins", "my sunflower", "my sunflowers"),
                                  ("eating", "eaten", "nibbled", "nibbling", "chewed", "holes",
                                   "bites", "destroyed", "vanished")),
          "Look at when and how it is eaten. Ragged holes and slime trails, worst overnight, are "
          "slugs and snails: go out with a torch after dark and pick them off, or set a beer trap, "
          "and put copper tape round pots. Clean holes in the middle of leaves with the edges left "
          "alone are caterpillars - look under the leaves in daylight and pick them off. Tops "
          "nibbled to a stump with a clean cut are pigeons or rabbits, so net or cage it. Seedlings "
          "cut off at soil level are cutworms or mice.",
          # a line that names the pest has its own answer in garden.py, so this one is only for
          # "something is eating my plants" - the line that names nothing.
          avoid=("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "pet", "pets",
                 "bird", "birds", "chicken", "chickens",
                 "slug", "slugs", "snail", "snails", "caterpillar", "caterpillars", "aphid",
                 "aphids", "pigeon", "pigeons", "rabbit", "rabbits", "deer", "mice", "mouse",
                 "ants", "weevil", "beetle", "food", "photosynthesis", "sunlight", "drink",
                 "eat them", "eat it",
                 "toddler", "child", "children", "kids", "baby", "son", "daughter",
                 "dinner", "lunch", "tea", "fussy", "appetite")),
    entry("city-birds-winter", ("bird", ("winter", "park", "city", "outside")),
          "In a British city park in winter you'll usually see robins, blackbirds, blue tits, "
          "great tits, pigeons, crows and magpies, with gulls and starlings on the grass. Look in "
          "the bushes and bare trees rather than the open lawn, and early morning is the busiest "
          "time.", avoid=("feed", "feeder", "food", "feeding")),
    entry("feed-birds-winter", ("bird", ("feed", "feeder", "food", "feeding", "seed", "seeds",
                                        "fat balls", "mealworms", "bird table")),
          "Feed birds seeds, fat balls and mealworms, and put out water too; skip bread, which "
          "fills them up without much goodness. Once you start in winter, keep going, because "
          "they come to rely on that spot.",
          # a pet budgie or parrot is the pets' question, and it won a tie on "birds" + "feed":
          # a garden bird and its seed is what this row is for, so it speaks first when both fit.
          # What you might see in a park stays with `city-birds-winter`, so "see" is fenced.
          bias=2, avoid=("see", "seen", "might i see", "which birds", "what birds", "spot",
                         "spotted", "identify", "park", "city", "in the park")),
    # "how do i stop squirrels eating the bird food" was answered with parrot food, then, once
    # that row stood down, with what to put out for the birds. A squirrel on the feeder is its
    # own question and the answer is a piece of kit, not a different menu.
    entry("squirrels-on-the-feeder",
          (("squirrel", "squirrels", "grey squirrel", "grey squirrels"),
           ("bird food", "bird seed", "bird feeder", "feeder", "feeders", "bird table", "keep off",
            "keep them off", "stop", "stopping", "eating", "steal", "stealing", "get into",
            "get at", "raiding", "peanuts", "seed", "fat balls", "nuts")),
          "A baffle is the whole answer: one on the pole under the feeder, or a set of four plastic "
          "baffles on the pole, which a squirrel cannot get past because it climbs with a grip. "
          "Then give it nowhere to launch from - 2m from a fence, a tree or a shed and 2m off the "
          "ground, because a grey squirrel jumps about 2m across and drops further. A caged feeder "
          "lets tits in and keeps the rest out, a weight-triggered one shuts under a squirrel, and "
          "chilli powder mixed into the seed is ignored by birds and hated by squirrels.",
          bias=2,
          # "what does a squirrel eat" is the diet table's question, and it was answered with a
          # baffle because the second half of the key has "eating" and "seed" in it
          avoid=("what does a squirrel eat", "what do squirrels eat",
                 "what does a grey squirrel eat", "diet", "what to feed", "what should i feed")),
    entry("dogs-thunder", ("dog", ("thunder", "thunderstorms", "storms")),
          "Dogs hear thunder much more loudly than we do and feel the pressure change, so the fear "
          "is real. Give them a small den to hide in, stay calm and don't force them out; "
          "background noise and closing the curtains help, and a vet can suggest calming options "
          "before the next storm.",
          # Two dog-and-weather entries in this domain mean "dog" is no longer a word only one of
          # them uses, and without that specificity bonus the science entry that explains thunder
          # won the tie: "why do dogs get scared of thunder" asked about the dog, not the physics.
          bias=1),
    # A fireworks question is not a thunder one: thunder arrives unannounced, fireworks are a date
    # you can plan for, and "my dog hates bonfire night" was reaching the night-cough answer
    # because "bonfire night" carries the word night.
    entry("dogs-fireworks", ("dog", ("firework", "fireworks", "bonfire", "bonfire night",
                                     "guy fawkes", "sparklers", "bangs", "bang", "loud noises",
                                     "loud noise", "loud bangs", "explosions")),
          "Dogs hear bangs far louder than we do and can't tell they are harmless, so plan the "
          "night instead of waiting for the first one: walk him before dark, then shut the windows "
          "and curtains, put the radio on and let him hide where he likes with something to chew. "
          "Stay in with him, don't take him to a display and never tell a frightened dog off; if he "
          "panics badly, ask the vet about a calming plan a few weeks ahead and check his microchip "
          "details are up to date in case he bolts.", bias=2),
    entry("bees-important", ("bee", ("important", "why", "do", "disappear", "dying", "pollinate")),
          "Bees pollinate a large share of the fruit, vegetables and nuts we eat, so losing them "
          "would make food scarcer and dearer. You can help with bee-friendly flowers, a shallow "
          "dish of water and a corner of garden left a bit wild.",
          avoid=("sting", "stung", "swell", "swelling", "throat", "allergic")),
    entry("tick-bite", ("tick", ("bite", "remove", "lyme", "safe", "found", "stuck")),
          "Grip the tick as close to your skin as you can with fine tweezers and pull steadily "
          "upwards without twisting or squeezing. Then watch the spot: a spreading rash or a "
          "fever in the next few weeks means see a doctor and mention the bite."),
    entry("sting", (("sting", "stung",
                     # A phone writes "beesting" as one word, and it is the same noun as "bee
                     # sting": "a beesting swell" was a listening line because no key held it.
                     "beesting", "beestings", "waspsting", "waspstings"),
                    ("wasp", "bee", "swell", "swelling", "allergic", "throat",
                     # The sting is on a body, and the line says which: "my hand is swelling
                     # after a bee sting" and "a bee sting on my hand is swelling" name the hand
                     # as the subject, and an entry that never mentions the part a line names is
                     # not its answer. The part is the sting's place, not a second subject.
                     "hand", "hands", "foot", "feet", "leg", "legs", "arm", "arms", "finger",
                     "fingers", "thumb", "wrist", "ankle", "toe", "toes", "palm", "cheek",
                     "chin", "face", "neck", "shoulder", "ear", "ears", "lip", "lips", "eye",
                     "eyelid", "head", "skin", "back", "knee", "knees", "tummy", "stomach")),
          "Scrape the sting out sideways with a fingernail or card, wash it and put something cold "
          "on it; an antihistamine helps the itch. Get help fast if the person swells away from "
          "the sting, struggles to breathe or feels faint."),
    # --- the garden and the sky people ask about ------------------------------
    entry("dawn-chorus", (("bird", "birds", "blackbird", "thrush", "robin"),
                          ("sing", "sings", "singing", "song", "chorus", "dawn", "morning",
                           "4am", "4 am", "5am", "5 am", "early", "wake", "woken")),
          "That is the dawn chorus: the blackbird starts about an hour before sunrise, then the "
          "robin and song thrush, then blue tits and the rest. The males are claiming territory "
          "and calling for a mate, and the still morning air carries the song further. It fades "
          "by about 7am, once they stop defending and start feeding.",
          # A bird a cat has brought in is not a bird that is singing: "the cat brings a bird in
          # most mornings" was answered with the dawn chorus, because "bird" and "morning" are the
          # entry's own two keys. The words below are the hunting, and the cat-prey entry answers
          # those instead.
          avoid=("feed", "feeder", "food", "feeding", "park", "city",
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies",
                 "brings in", "brings a", "bringing in", "brought in", "brought a", "keeps bringing",
                 "prey", "dead", "mouse", "mice", "rat", "rats", "killed", "kills", "caught",
                 "carcass", "carcasses")),
    entry("swallows-migrate", (("swallow", "swallows", "swift", "swifts", "martin", "martins"),
                               ("arrive", "arriving", "arrived", "come", "back", "leave", "left",
                                "gone", "when", "migrate", "migration", "nest")),
          "Swallows come back to Britain from mid-April, a few as early as March, and leave "
          "between late September and early October; swifts arrive in early May and are gone by "
          "mid-August. They winter in southern Africa. So an empty nest in early October is "
          "normal, not a sign that something went wrong.",
          avoid=("throat", "sore throat", "lump", "clicks", "clicking", "hurts to swallow",
                 "trouble swallowing", "hard to swallow", "difficulty swallowing",
                 "cannot swallow", "cant swallow", "can't swallow", "swallow food",
                 "when i swallow", "painful to swallow", "tonsils")),
    entry("wasps-autumn", (("wasp", "wasps", "hornet", "hornets"),
                           ("autumn", "september", "october", "everywhere", "bothering", "mean",
                            "aggressive", "swarming", "nest", "many")),
          "In autumn the colony is winding down: the queen stops laying, so the workers have no "
          "grubs to feed and go looking for sugar instead, which is why they crowd round jam, "
          "fruit and bins in September. They are not nastier, just hungry and idle. They die at "
          "the first hard frosts, only the new queen survives, and the old nest is never reused.",
          avoid=("sting", "stung", "swell", "swelling", "allergic", "throat")),
    entry("wasp-in-the-room", (("wasp", "wasps", "hornet", "hornets"),
                               ("in the room", "in my room", "in here", "in the kitchen",
                                "in the bedroom", "in the house", "in the bathroom",
                                "in the living room", "indoors", "inside", "in the car",
                                # A phrase matches only the words that stand next to each
                                # other, so "in the bedroom" does not reach "in my bedroom":
                                # the possessive has to be said. "theres a wasp in my bedroom"
                                # was the greeting echo while "in the kitchen" answered, and it
                                # is the same wasp in the same kind of room.
                                "in my kitchen", "in my bedroom", "in my house",
                                "in my bathroom", "in my living room", "in my lounge",
                                "in my bath", "in my car", "in the lounge", "in my office",
                                "in the office", "out of my bathroom", "out of my bedroom",
                                "out of my kitchen", "out of my house", "out of my car",
                                "out of the lounge", "out of my lounge",
                                "on me", "on my arm", "on my leg", "in the bath",
                                "buzzing", "flying around", "trapped", "got in",
                                "out of the bathroom", "out of the bedroom",
                                "out of the kitchen", "out of the house", "out of my room",
                                "out of the car", "out of here", "flew in", "came in",
                                "in the window", "through the window")),
          "A wasp or a hornet in a room: open a window wide and step back - it flies to the "
          "light and goes out on its own, and it will not chase you. Do not swat it - a squashed wasp is what stings, and the "
          "ones in late summer are only after sugar, so leave a jam jar away from you and it will "
          "go there instead. If it is in the car, pull over somewhere safe, open every window and "
          "step out until it leaves; a wasp in a moving car is how people crash.",
          # A nest, an autumn swarm and a sting are three other answers, and an allergy is a red
          # flag: the wasp in the room is the one that wants the window.
          avoid=("nest", "nests", "loft", "attic", "autumn", "september", "october", "swarm",
                 "everywhere", "sting", "stung", "swell", "swelling", "allergic", "throat",
                 "anaphyla", "epipen", "get rid of", "remove", "pest control", "queen")),
    entry("spring-blossom", (("blossom", "tree", "hedge"),
                             ("white", "pink", "march", "april", "spring", "blackthorn")),
          "Blackthorn is the first: white blossom on bare, spiny hedgerow twigs in March, before "
          "its leaves. Cherry plum and wild cherry come next, then apple and hawthorn in May. "
          "White flowers on a leafless hedge in early spring is almost always blackthorn; "
          "blackthorn has thorny twigs and hawthorn flowers after its leaves are out.",
          # "spring" and "tree" are also a planting date: "should i plant a tree now or wait till
          # spring" was this answer, and the question is the month to plant, not the blossom.
          avoid=("plant", "planting", "planted", "sow", "sowing", "seed", "seeds", "soil",
                 "compost", "prune")),
    entry("spiders-indoors", (("spider", "spiders"),
                              ("autumn", "indoors", "inside", "house", "come in", "coming in",
                               "everywhere", "bath", "big", "huge", "rid", "stop", "keep out",
                               "keeping out", "coming back", "afraid", "scared")),
          "Autumn is when the male house spiders wander about looking for a mate, and a warm room "
          "is where the insects are. British house spiders are harmless: a glass and a piece of "
          "card is the kindest way to move one out. The cobwebs up in the ceiling corners are "
          "worth leaving, since they catch flies and midges.", report=True),
    entry("clocks-change", (("clocks", "clock", "daylight saving", "daylight savings",
                             "summer time", "bst"),
                            ("change", "back", "forward", "darker", "lighter", "daylight saving",
                             "daylight savings", "summer time", "bst", "nights",
                             # "whats the point of daylight saving" names no clock at all, and a
                             # bare "saving" sent it to the how-to-save-money card
                             "point", "whats the point", "what is the point", "why", "reason",
                             "still", "why bother", "who decides", "history")),
          "The clocks go back an hour at 2am on the last Sunday in October and forward an hour at "
          "2am on the last Sunday in March. The point of it is the light: the hour is moved to the "
          "part of the day when most people are up and out, so summer evenings stay light and "
          "winter mornings are not dark until nine. Late October buys an extra hour in bed, and "
          "the evenings close in by about 5pm; late March hands the hour back."),
    entry("garden-birds-gone", (("bird", "birds"),
                                ("gone", "no birds", "missing", "disappeared", "empty", "stopped",
                                 "not coming", "vanished", "none", "quiet")),
          "The usual reasons are timing and cover. Birds go quiet and hide in late summer while "
          "they moult, and a garden with no shrubs or trees has nowhere safe to wait. A cat, or a "
          "sparrowhawk that has found your feeders, will clear a garden for a few weeks. Keep the "
          "feeders topped up with water nearby, add a leafy shrub or two, and give it a fortnight.",
          avoid=("park", "city", "winter", "feed", "feeder", "food")),
    entry("butterflies-garden", (("butterfly", "butterflies"),
                                 ("garden", "attract", "bring", "plant", "flowers", "help")),
          "Plant for the whole season rather than one week: lavender, oregano and marjoram in "
          "summer, buddleia for July and August, sedum and ivy flowers for September. Leave a "
          "sunny corner of long grass and a patch of nettles, because that is where they lay, and "
          "put out a shallow dish of water with a few stones in it."),
    entry("hedgehog-food", (("hedgehog", "hedgehogs"),
                            ("eat", "feed", "food", "visiting", "garden", "hungry", "what")),
          "Hedgehogs eat beetles, caterpillars, earthworms and slugs, and by autumn they need to "
          "put on weight before hibernation. To feed one, put out cat or dog food (chicken or "
          "turkey, not fish), chopped unsalted nuts and a shallow dish of water, after dark. "
          "Never milk or bread, and feed under a slate or in a box so cats cannot get at it."),
    entry("plant-breathe", (("plant", "plants", "stomata", "leaf", "leaves"),
                            ("breathe", "breathing", "breath", "respiration", "oxygen")),
          "Plants breathe through tiny holes called stomata, mostly on the underside of leaves, "
          "which open to take in carbon dioxide and let out oxygen and water vapour. Roots take "
          "oxygen from air pockets in the soil, which is why a plant in soggy, airless compost "
          "can drown. They do it day and night; in daylight photosynthesis makes more oxygen than "
          "respiration uses."),
    # "how far" is a phrase, not just "far": the expenses entry reads a bare "far" as a slip
    # of "fare", and it was winning the tie on "how far is the moon" and answering with a
    # expenses deadline.
    entry("moon-distance", ("moon", ("far", "how far", "how far away", "away", "distance",
                                     "miles", "km", "kilometres")),
          "About 384,400 km (238,900 miles) away on average, which is roughly 30 Earths side by "
          "side, and light takes 1.3 seconds to reach us from it. It is drifting about 4cm "
          "further away each year.",
          # the camera entry also keys "moon" and "how"; a distance line is this table's
          bias=2),
    entry("moon-daytime", ("moon", ("daytime", "daylight", "afternoon", "morning", "visible",
                                    "day")),
          "The Moon is above the horizon in daylight most days: it is lit by the sun and simply "
          "looks pale against a blue sky. It is easiest to spot in the morning or late afternoon, "
          "when the blue is deeper. Around new moon it sits too close to the sun in the sky to "
          "see at all."),
    entry("full-moon-next", (("full moon", "moon"), ("next", "when", "coming", "due")),
          _next_full_moon,
          # a night that would not come is the sleep rows' answer, not the date of the full moon
          avoid=A_BAD_NIGHT),
    entry("moon-phases", ("moon", ("phases", "phase", "shape", "crescent", "change",
                                                            "different", "full")),
          "The Moon doesn't change shape; half of it is always lit by the sun, and we see a "
          "different slice of that lit half as it orbits the Earth. A full moon takes about 29.5 "
          "days to come round again.",
          # the same fence: "does a full moon affect sleep" is about the night, not the phases
          avoid=A_BAD_NIGHT),
    entry("fruit-or-berry", (PRODUCE,
                             ("fruit", "fruits", "berry", "berries", "vegetable", "vegetables",
                              "botanically", "really")),
          _fruit_or_berry,
          # A recipe, a nutrition question and a shopping question are other entries: this one is
          # the botanical "what is it" question, not "is it good for me".
          avoid=("recipe", "recipes", "healthy", "healthier", "good for me", "bad for me",
                 "calories", "carb", "carbs", "sugar", "diet", "weight", "buy", "shop",
                 "shopping", "grow", "growing", "plant", "plants", "allergy", "allergic",
                 # "why wont my peppers fruit" was told that botanically a pepper is a fruit:
                 # the word that made it a definition question is the word in the complaint.
                 # A crop that will not set is the growing question, whatever noun it names.
                 "wont fruit", "wont flower", "will not fruit", "will not flower",
                 "not fruiting", "arent fruiting", "aren't fruiting", "not setting",
                 "arent setting", "aren't setting", "not producing fruit", "no fruit",
                 "havent set", "hasnt set", "didnt set", "set nothing", "setting nothing",
                 "flowers drop", "flowers keep dropping", "flower drop", "flowers fall off",
                 "dropping its flowers", "dropping their flowers", "flowers but no",
                 "flowering but", "no flowers"),
          guard=_not_the_definition),
]
