"""What happens if it is left on: the boiler, the things that heat, and the ones that run.

"Is it safe to leave the boiler on all night" was answered with "Use the habits that work in any
city after dark: stay on the busy, lit streets...". The word `safe` was doing the routing and the
subject underneath it was dropped, so a line about a boiler went to the personal-safety-at-night
card. The same thing happened the other way: "is it safe to leave the washing machine on
overnight" got the dark-marks-in-the-drum answer, because `overnight` and `washing machine` are
that row's own words too.

Two rows live here rather than in home.py or travel.py, for the reason house_odds.py gives: a new
row beside the competing ones is where the question is decided, and this file costs one discovery
pass and nothing on a line it does not know.

The answers are split by what actually goes wrong. Cooking and candles are where most house fires
start; a tumble dryer is the fluff in its own filter; a boiler is built to run overnight and what
it wants is a flue that is checked and an alarm that works; a fridge left shut for a fortnight
grows mould.
"""

import re

from .lookup import entry

ANSWERS = ("home-and-diy", "safety")

FIRE_TEXT = (
    "Switch it off and stay with it while it is on: cooking and candles are where most house "
    "fires start, and a grill pan or a chip pan catching is the one that kills people. If it is "
    "already burning, get everyone out and call 999 rather than throwing water on fat. If you are "
    "out of the house and it is still on, do not go back in for it - call 999 and stay out.")

LAUNDRY_TEXT = (
    "A tumble dryer is the one to think about and a washer is mostly a flood: the fluff that "
    "collects in the filter and the vent is what burns, so clean the filter after every load, "
    "keep the vent clear, and run it while you are up and about rather than overnight or out. A "
    "washer left running is fine while the hoses are sound; turn the water off at the valve if "
    "you are leaving the house for long.")

DISHWASHER_TEXT = (
    "A dishwasher left running is mostly a water question, not a fire one: what goes wrong is the "
    "inlet hose, the door seal or the pump, and the damage is a flood, which matters most in a flat "
    "above someone else's ceiling. Look at the hose for bulges and the seal for grit, and if you "
    "want it to run overnight put it on the delay timer after checking those rather than starting "
    "it as you go to bed. An old machine with a hose you have never looked at is the one to run "
    "while you are still up.")


CHARGE_TEXT = (
    "Unplug it: a charger with nothing on the end of it stays warm for no reason, and a damaged "
    "cable or a cheap plug is the part that fails. An electric blanket is only meant to warm the "
    "bed before you get in, so put it on for half an hour and switch it off rather than leaving "
    "it on all night, and anything with a frayed lead goes in the bin.")

LIGHTS_TEXT = (
    "LED sets run cool and a set left on overnight is not the same risk as a candle, but the "
    "cheap ones are the ones that fail: unplug them if the plug is warm, the cable is frayed or "
    "the set is older than you can remember buying it, and a plug-in timer costs a few pounds "
    "and takes the decision away. Nothing that runs off a battery should be left on while you "
    "are out.")

COLD_TEXT = (
    "Leave the freezer running: a full freezer holds its temperature for hours in a power cut and "
    "costs very little. An empty fridge is better emptied, switched off and left with the door "
    "propped open for a fortnight away, because a fridge left shut and empty grows mould; if you "
    "leave either running, turn the water off at the valve if it has an ice maker.")

BOILER_TEXT = (
    "Leave it on: a modern boiler is built to run overnight, and its frost setting fires it only "
    "when the house gets cold. What matters is not the hours but the flue and the alarm - a "
    "carbon monoxide alarm on the same floor as the boiler, the flue checked at the yearly "
    "service, and nothing stacked against the vents or the air brick. An old back boiler or an "
    "open flue is the one to ask a Gas Safe engineer about before you sleep with it on. If you "
    "mean the heating rather than the hot water, it costs more than switching it off and back on, "
    "which is the money question and not this one.")

# What is on decides what the answer is, so the line is read for the thing and not for the words
# around it. The understanding gives single words and most of these are two ("washing machine"),
# so the line itself is read as well.
_GROUPS = (
    (("fridge", "freezer", "freezers", "fridge freezer"), COLD_TEXT),
    (("washing machine", "tumble dryer", "tumble drier", "the dryer", "my dryer"),
     LAUNDRY_TEXT),
    # The thing named is the thing answered: a dishwasher's risk is water, not fluff, and the
    # line "can i leave the dishwasher on overnight" was told about the filter in a tumble dryer.
    (("dishwasher", "dishwashers"), DISHWASHER_TEXT),
    (("charger", "on charge", "extension lead", "electric blanket", "straighteners"), CHARGE_TEXT),
    (("lights", "light", "fairy lights", "christmas lights", "tree lights"), LIGHTS_TEXT),
)

_FIRE_WORDS = frozenset((
    "oven", "ovens", "hob", "hobs", "cooker", "cookers", "grill", "grills", "stove", "stoves",
    "chip pan", "deep fat fryer", "deep fryer", "fryer", "air fryer", "candle", "candles",
    "iron", "ironing", "heater", "fan heater", "electric heater", "toaster", "microwave",
    "burner", "woodburner", "fire"))


# "can i leave rice in the fridge for 2 days" and "can i leave it in the fridge overnight" are
# keeping questions, and the keeping rows answer both: this row is about the appliance being left
# on, so a thing left *in* one stands it down. A fridge or a freezer is also left for a reason -
# a holiday, a fortnight away, a door propped open - and without one of those the line is food.
_IN_THE_THING = ("in the oven", "in the fridge", "in the freezer", "in the microwave",
                 "in the dishwasher", "in the washer", "in the tumble dryer", "in the air fryer")
_AWAY = ("while im away", "while i am away", "while we are away", "while we're away",
         "on holiday", "fortnight", "two weeks", "a week away", "for a week", "for the weekend",
         "turn it off", "turning it off", "switch it off", "switched it off", "switching it off",
         "switched off", "switch off", "unplug", "empty it", "emptied", "left running",
         "left on", "leave it on", "leave the fridge on", "leave the freezer on",
         "leave both on", "running while", "keep it on", "keeping it on", "propped open")


# "My dishwasher leaves white marks" is a complaint about the water, and the key above takes it
# on "leaves" - the same word as "leaves it on", with the thing being left unstated. Third-person
# "leaves" with a plain object after it is the machine doing something to whatever follows, not a
# machine still running, so those lines are not this question. "leaves it on", "leaves the oven
# on" and "leaves on" are, and are let through.
_LEAVES_AN_OBJECT = re.compile(
    r"\bleaves\s+(?!it\b|them\b|on\b|everything\s+on\b|the\s+[\w']+\s+on\b|a\s+[\w']+\s+on\b"
    r"|all\b)\w+")


def _left_on_answers_this(understood):
    """False for the keeping questions that name an appliance but are not about it."""
    line = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if any(phrase in line for phrase in _IN_THE_THING):
        return False
    if _LEAVES_AN_OBJECT.search(line):
        return False
    if ("fridge" in line or "freezer" in line) and not any(w in line for w in _AWAY):
        return False
    return True


_RISK = ("safe", "unsafe", "dangerous", "risky", "risk", "carbon monoxide", "flue", "fumes",
         "fire", "leak", "leaking", "the alarm", "smell", "smells", "smoke", "worried", "worry")
_ONLY_HEATING = ("heating", "hot water")


def _a_heating_habit_is_not_a_risk(understood):
    """False for "should i leave the heating on overnight", which is the timer's question.

    The boiler card is the answer to a risk question about a boiler. `heating` and `hot water`
    are in the subject list because "is it safe to leave the heating on all night" is a real
    line, but they are also how people ask what the timer should do - and that question has the
    cost answer, which says the timer wins. So when `heating` is the only subject in the line
    and nothing in it is a risk word, this row stands down.
    """
    line = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    if any(word in line for word in _RISK):
        return True
    return not any(word in line for word in _ONLY_HEATING)


def _left_on_reply(memory, understood):
    """The answer for the thing that is on, and the fire answer when it is anything that heats."""
    line = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    words = set((understood or {}).get("words") or ())
    for group, text in _GROUPS:
        if any(word in line for word in group):
            # a candle in front of the fairy lights is still a candle: what heats wins
            if words & _FIRE_WORDS and "lights" not in group:
                return FIRE_TEXT
            return text
    return FIRE_TEXT


ENTRIES = [
    # The subject is the boiler, so the answer is about the boiler. Without this row the line
    # reached the city-at-night card, and the heating-cost rows answered a cost question that
    # nobody asked: "leaving the heating on all night is it safe" got "No, it is not cheaper".
    # The id is `boiler-left-on-overnight`, not `boiler-on-overnight`: `home_craft.py` already
    # carries a row under that id (the safety answer about a boiler left running overnight), and
    # two entries sharing an id is what `tests.test_ids_are_unique` refuses - it took main red when
    # this row landed (#6684), because the older file's row was moved to `home_craft.py` by #7372.
    # Both rows answer a slightly different line and this one wins where they overlap, so the id
    # moves rather than the row.
    entry("boiler-left-on-overnight",
          (("boiler", "boilers", "combi", "central heating", "heating", "hot water", "radiator",
            "radiators"),
           ("leave", "leaves", "left", "leaving", "on all night", "on overnight", "overnight",
            "all night", "at night", "while im out", "while i am out", "while im at work",
            "unattended", "turn it off", "turn off", "switch it off", "switch off")),
          BOILER_TEXT,
          bias=1,
          guard=_a_heating_habit_is_not_a_risk,
          # the cost question has its own answer and it is right about what it answers, and a
          # boiler that is broken, noisy, losing pressure or due a service is that question
          avoid=("cheaper", "cheapest", "cost", "costs", "costly", "expensive",
                 "save money", "saving money", "bill", "bills",
                 # "leave the heating on low" is the energy-saving idiom, and the answer to it
                 # is the cost card, not this one: it now stands down on the thermostat words.
                 "on low", "heating on low", "economy 7", "tariff", "thermostat setting", "what temperature",
                 # A house with nobody in it is a different question, and it is answered better
                 # elsewhere: "should i leave the heating on when i go away" wants the frost
                 # setting (12 to 15C), and "im away next week, should i leave the heating on"
                 # wants the cost answer. This row took both, because "should i leave" is in
                 # its key, and told the person about the flue and the carbon monoxide alarm -
                 # right for a night, wrong for a week. The overnight lines keep it.
                 "away", "go away", "going away", "went away", "while im away",
                 "while i am away", "while we are away", "on holiday", "holidays",
                 "next week", "a week off", "for a week", "for two weeks", "fortnight",
                 "weekend away", "for the weekend", "out all day", "all day",
                 "pressure", "bleed", "bleeding", "noise", "noisy", "kettling", "leak",
                 "leaking", "broken", "not working", "fault", "error code", "service", "serviced",
                 "towel rail", "radiator valve", "trv",
                 # a house nobody is in is the away question, and its answer is the frost
                 # setting and the stopcock, not "leave it on": #6684 took that row's lines
                 # (12 to 15C, turn the water off) and turned seven of its tests red.
                 "away", "holiday", "holidays", "empty house", "nobody in", "for a week",
                 "for a fortnight", "a week away", "go away", "going away", "went away",
                 "frost", "freeze", "freezing", "pipes", "burst pipe",
                 # and a habit question is the cost answer's, not this one: "should i leave the
                 # heating on overnight" is asking what the timer should do, and the same goes
                 # for the working-day framing. Neither is a risk question, which is what the
                 # boiler card answers.
                 "all day", "out at work", "im out at work", "when im out", "timer",
                 "24 hours", "how many hours",
                 # "how do i turn off the hot water cylinder" is the tank's question, not
                 # whether a boiler can be left running overnight
                 "immersion", "hot water cylinder", "hot water tank", "hot cylinder",
                 "where is the valve", "isolation valve", "drain", "draining", "drained",
                 "spur", "fused spur")),
    # An oven, a candle, a dryer, a fridge: four different risks and one question, which is
    # whether it can be left. What is named in the line picks the answer.
    entry("left-on-unattended",
          (("oven", "ovens", "hob", "hobs", "cooker", "cookers", "grill", "grills", "stove",
            "stoves", "chip pan", "deep fat fryer", "deep fryer", "fryer", "air fryer", "candle",
            "candles", "iron", "straighteners", "hair straighteners", "heater", "fan heater",
            "electric heater", "electric blanket", "toaster", "microwave", "burner",
            "woodburner", "gas fire", "open fire", "fireplace", "log fire", "coal fire",
            "fire", "tumble dryer", "tumble drier", "dryer", "washing machine", "washer",
            "dishwasher", "charger", "phone charger", "laptop charger", "extension lead",
            "fridge", "freezer", "fridge freezer", "fairy lights", "christmas lights",
            "tree lights"),
           ("leave", "leaves", "left", "leaving", "on all night", "on overnight", "overnight",
            "all night", "at night", "while im out", "while i go out", "while we are out",
            "while im away", "while we are away", "while im at work", "while i sleep", "asleep",
            "out of the house", "unattended", "forgot", "forgot to turn", "didnt turn",
            "did not turn", "still on", "should i turn", "turn it off", "switch it off")),
          _left_on_reply,
          bias=1,
          guard=_left_on_answers_this,
          # how to cook in it, clean it, fix it or buy one is not this question, and the oven,
          # washing machine and frost rows are right about those
          # a load that came out wet is a drying question and this row was answering it: "my
          # washing machine leaves clothes too wet" is the machine's fault and the answer is how
          # to get the water out, not whether it is safe to leave it on. Only the phrases that say
          # the machine did it are fenced - a bare "wet" would take the "is it safe to leave wet
          # washing in it overnight" line away from here, and that one is this row's question.
          avoid=("how long", "how many minutes", "temperature", "gas mark", "preheat", "recipe",
                 "leaves clothes", "leaves the clothes", "leaves my clothes", "clothes too wet",
                 "clothes are too wet", "clothes still wet", "clothes come out wet",
                 "washing too wet", "washing comes out wet", "comes out too wet", "too wet",
                 "roast", "bake", "clean", "cleaning", "descale", "filter", "smell", "smells",
                 "not heating", "broken", "repair", "fuse", "error code", "buy", "recommend",
                 "which one", "drum", "seal", "dark marks", "wont spin", "not draining",
                 "slow cooker", "crockpot", "crock pot", "air fryer recipe", "defrost", "ice",
                 "frozen", "power cut", "not cold", "freezer not",
                 # Whether it is safe to leave on and what it costs to run are two questions with
                 # the same subject, and "at night" is in the key above, so "is it cheaper to run
                 # the dishwasher at night" was told about the fluff in a dryer's filter. The hour
                 # and the price are the `cheapest-hours` row's and the running-cost table's, so a
                 # line that asks either stands this row down - the same fence the boiler row
                 # above already has for "is it cheaper to leave the heating on".
                 "cheaper", "cheapest", "cheap", "cheaply", "cost", "costs", "costly",
                 "expensive", "electricity", "tariff", "off peak", "off-peak", "economy 7",
                 "economy7", "time of use", "best time", "what time", "low rate", "save money",
                 "saving money", "bill", "bills", "how much does it cost")),
]
