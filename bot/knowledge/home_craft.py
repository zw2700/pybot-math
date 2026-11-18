"""The rows of the home-and-DIY domain: the list from `home.py`, in a file of its own.

`home.py` went over the publisher's 1 MiB file limit (1,067,285 bytes) and the world then refused
every PR in the swarm, not only the ones that touched that file, because it looks at the clone:
`{"error": "file too large: bot/knowledge/home.py is over 1048576 bytes"}`. The list of entries
is the biggest thing in the file and it is data rather than code, so it moved here.

Nothing about the entries changed. `home.py` calls `entries()` at the end, after every helper,
table and guard this list names is defined, and puts the rows back in front of the ones it
appends itself, so `home.ENTRIES` is the same rows in the same order as before. The import is
inside the function for that reason: this module is imported by `home.py`, not the other way
round, and it has no ENTRIES of its own, so the registry does not read it as a second domain.
"""

import re


_A_DEPOSIT_COMING_BACK = re.compile(
    r"\b(?:tenancy|scheme|landlord|letting agent|deposit protection|moved out|end of tenancy|"
    r"deposit back|deposit returned|deposit return|deposit paid|paid a deposit)\b")


def _a_deposit_coming_back(understood):
    """True when the deposit line is a tenancy one, not somebody saving towards a deposit."""
    read = understood if isinstance(understood, dict) else {}
    said = " ".join(str(read.get("clean") or read.get("text") or "").lower().split())
    return bool(_A_DEPOSIT_COMING_BACK.search(said))


import re

from ..understanding.topics import the_bin_is_on_a_machine
from .costs import A_AGE_OWNED

# A food named with its own smell is the food's question, and the fridge is only where it is:
# "the milk in my fridge smells off but the date is fine" was told to wash out the door seal and
# the drain hole, and "the milk in the fridge smells sour" the same. The bottle has a card of its
# own that says bin it. "The fridge smells of milk" keeps this row, because there the food comes
# after the smell and the fridge is what smells.
_FOOD_OWN_SMELL = re.compile(
    r"\b(?:milk|yoghurt|yogurt|cream|soured cream|sour cream)\b[^.?!]{0,30}?"
    r"\b(?:smells|smell|smelt|smelled|stinks|stink|gone off|went off|is off|has turned|turned|"
    r"curdled|sour)\b")


def _not_the_food_in_the_fridge(understood):
    """False when the line is a food that has turned, with the fridge named as where it is."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not _FOOD_OWN_SMELL.search(text)

# "Can i service my own boiler" and "how often should the boiler be serviced" are two questions,
# and one cost-and-frequency reply answered both: the first wants to know whether the job is
# theirs, and a price never says. They are two rows rather than one row with a reply that changes
# its mind, because an entry whose reply is a function stops carrying the conversation a turn
# later: after "my boiler needs its yearly service" the age in "its 8 years old" reached the
# engineer's-price answer instead of the lifespan one.
# A fixture that has stopped is not an appliance, and the plug-and-door-switch first aid is the
# wrong first thing to try on a shower, a tap or a toilet - no appliance row names any of them.
# Until they had a row of their own these lines were answered by whatever else their words touched:
# "the hot tap stopped working" reached the bank's contactless card ("In the bank's own app there
# is usually an 'Add to Apple Pay'"), "my toilet has stopped working" the fibre answer, "my shower
# isnt working" the extractor fan (that row holds the word shower) and "the plug socket has stopped
# working" the skirting-tape row, while "the shower has stopped working", "the shower broke" and
# "the doorbell has stopped working" got only a listening line back. The fixture named in the line
# says which first check to give, so one row answers them all and no fixture needs a row of its own.
# The fault words are the ones that say the thing is not running at all: a named symptom (leaking,
# blocked, wont drain, wont flush, cold) is the row that knows that symptom, and it keeps the line.
STOPPED_ALTOGETHER = (
    "stopped working", "stops working", "stopped work", "not working", "isnt working",
    "isn't working", "doesnt work", "doesn't work", "wont work", "won't work", "no longer works",
    "broken", "broke", "broken down", "broke down", "packed in", "packed up", "gave up",
    "dead", "no power", "wont come on", "won't come on", "wont turn on", "won't turn on",
    "wont switch on", "won't switch on", "faulty", "gone wrong", "went wrong")

# Longest first, so "power shower" is the shower and not a power cut, and a fixture is found by the
# words the person typed rather than by a list of subjects: "the hot tap stopped working" has the
# subject "tap", and "my shower isnt working" the subject "shower", but a line can reach the reading
# with no subject at all and the fixture is still the thing it names. A dead socket is not here: it
# has its own row, and the paint rows that used to take it were the bug (see `decorating`).
FIXTURE_FIRST_CHECKS = (
    (("power shower", "electric shower", "shower", "showers"),
     "Start at the switch that feeds it: the pull cord or the wall switch, then the fuse in the "
     "unit, because a dead shower is usually that. If the unit lights up but no water runs, it is "
     "the solenoid valve or scale in the head, and on a mixer run the other hot taps first."),
    (("mixer tap", "monobloc", "tap", "taps", "faucet", "faucets"),
     "Look for a small screw slot on the pipe under the sink or the bath, because a tap that will "
     "not run at all is usually an isolator someone turned off or a valve that has seized. If the "
     "water comes but only trickles, unscrew the spout end and soak the aerator in vinegar."),
    (("toilet", "toilets", "loo", "cistern"),
     "Turn the isolation screw off, lift the lid and watch the cistern fill: a float arm stuck or "
     "an inlet valve furred up with scale is the usual reason the loo has stopped. A button with "
     "no resistance is the flush valve or its link, which is a cheap part."),
    # "door bell" and "door chime" are not here: a remembered key with "door" in it is handed to
    # the door group of the trade table, so the follow-up after a dead doorbell sent the person to
    # a joiner. "doorbell" alone is one word, and "chime", "chimes" and "bell push" carry the
    # lines that say it the other way round.
    (("doorbell", "doorbells", "chime", "chimes", "bell push", "bell"),
     "Start with the power to it: a wired bell has a transformer near the consumer unit, and a "
     "wireless one has a battery in the push and another in the chime. A push that is stuck, wet "
     "or corroded is the next thing."),
    (("garage door", "up and over door", "roller door", "sectional door"),
     "Use the manual release first - usually a red cord or a handle on the mechanism - so the car "
     "is not stuck in, then check the power, the remote's battery and the safety sensors at the "
     "bottom of the tracks. A door that opens a foot and stops is the travel limits or a broken "
     "spring, and a spring is not a DIY job."),
    (("heated towel rail", "towel rail", "towel radiator", "ladder rail",
      "radiator", "radiators", "rad", "rads"),
     "Bleed it, then take the head off the thermostatic valve and press the pin: one cold radiator "
     "is air or a pin stuck down. If every radiator is cold it is the boiler, the programmer or a "
     "zone valve, and one that is cold at the bottom wants a flush."),
)


def _the_fixture_that_stopped(understood):
    """The first check for the fixture a line says has stopped, or None.

    The fault words say the thing is not running at all, and the fixture is read from the line's
    own words with the longest phrase first, so "power shower" is not a power cut and "plug
    socket" is not a plug-in appliance.
    """
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(one) for one in (reading.get("words") or ())).lower()
    if not said:
        said = str(reading.get("clean") or reading.get("text") or "").lower()
    if not said or not any(word in said for word in STOPPED_ALTOGETHER):
        return None
    for names, check in FIXTURE_FIRST_CHECKS:
        if any(re.search(r"\b" + re.escape(name) + r"s?\b", said) for name in names):
            return check
    return None


# Every row below answers a fixture that has stopped, so every one of them has to stay out of a
# named symptom, a fixture being bought or rented, a decorating job and a shower enclosure
# whose door or tray has gone. Shared so the rows cannot drift apart.
A_FIXTURE_IS_NOT_A_DECORATING_JOB = ("leak", "leaks", "leaking", "drip", "dripping", "blocked", "blockage",
                     "wont drain", "won't drain", "not draining", "wont flush", "won't flush",
                     "smell", "smells", "smelly", "noise", "noisy", "banging", "rattling",
                     "cold", "hot water", "pressure", "limescale", "scale", "mould", "mold",
                     "buy", "buying", "worth", "cost", "price", "cheaper", "rent", "landlord",
                     "install", "installing", "fit a new", "replace", "replacing", "replacement",
                     "paint", "painting", "tile", "tiling", "decorate", "decorating",
                     "how do i", "how to", "should i",
                     # The door, the tray and the seal are parts of the enclosure, and a broken one
                     # is a glazing or a seal question: "the shower door is broken" is not the supply
                     # and the first check for the supply is the wrong thing to tell them.
                     "shower door", "shower doors", "shower screen", "shower tray", "door seal",
                     # Which radiators are cold is the system's question, and the row that reads
                     # "cold upstairs and warm downstairs" answers it better than one radiator's
                     # first check: "the downstairs radiator is not working" keeps that answer.
                     "upstairs", "downstairs", "top floor", "first floor")

def _a_fixture_that_stopped_was_the_question(understood):
    """The first check for the fixture the line names, or None for a line that names none."""
    return _the_fixture_that_stopped(understood) is not None


def _the_stopped_fixture_entries(entry):
    """One row per fixture, not one row for the family.

    A family key is remembered as one list of words, and the next turn hands that list to the
    trade table: a shower, a tap, a doorbell and a cistern all remembered "radiator", so "my
    shower isnt working" was sent to a Gas Safe engineer. A row whose keys are its own fixture
    is remembered as that fixture, and the trade that turns up is the right one.
    """
    for _names, _check in FIXTURE_FIRST_CHECKS:
        yield entry("a-fixture-that-stopped-" + _names[0].replace(" ", "-"),
                    (_names, STOPPED_ALTOGETHER),
                    lambda memory, reading: _the_fixture_that_stopped(reading),
                    avoid=A_FIXTURE_IS_NOT_A_DECORATING_JOB,
                    # the row that names the fixture the line is about outranks a biased
                    # neighbour, and the guard keeps it to a fixture that has stopped.
                    guard=_a_fixture_that_stopped_was_the_question, bias=3)

BOILER_DIY = ("myself", "own", "diy", "legal", "allowed")

# The permission words are in every other boiler line there is: "my own boiler keeps switching
# itself off" and "is it legal to have my boiler in the loft" are a fault and a siting question,
# and one word of possession was enough for the DIY row to take both - it told them about Gas Safe
# work instead of the reset button, and it took "my own boiler is 15 years old" off the lifespan
# card. The service word is what makes the line the permission question.
SERVICE_WORDS = ("service", "services", "servicing", "serviced", "annual", "yearly", "certificate")


def _an_ask_about_servicing_my_own(understood):
    """True when the line asks whether the yearly service is theirs to do.

    The row is keyed on the permission words because "can i service my own boiler" has no other
    mark in it, so the test that tells the permission question from the fault is the service word
    itself: "can i service it myself" and "is it legal to service the boiler" carry one, and "my
    own boiler is 15 years old" does not.
    """
    words = {str(one).lower() for one in ((understood or {}).get("words") or ())}
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return bool(words & set(SERVICE_WORDS)) or any(one in text for one in SERVICE_WORDS)


# The verb of travelling is a shape, not a list of phrases. Every phrase the fly row's `avoid`
# names ("fly out", "flying home", ...) was added by hand after a travel line got the cider
# vinegar, and the next wording always got through, so the shape is fenced here instead: a
# destination, a place it is done from or to, or a day. "there are flies in my house" and "a fly
# keeps landing on me" are the noun and keep the card.
_A_FLY_THAT_TRAVELS = re.compile(
    r"\b(?:fly|flys|flies|flew|flown|flying)\s+"
    r"(?:"
    # straight at a destination: "fly to spain", "fly into dublin", "fly over the alps"
    r"(?:to|into|over|via)\s+"
    r"|"
    # or it is done from, back to or with somebody: "fly out of heathrow", "fly home",
    # "fly with a baby", "fly at 6am"
    r"(?:out|back|home|abroad|from|off|at|with)\b"
    r"|"
    # or on a day, which no insect is ever on: "fly out on the 3rd of august", "fly next tuesday",
    # "fly somewhere sunny next saturday"
    r"(?:[a-z']+\s+){0,3}(?:on|next|this)\s+"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekend|week|month|"
    r"morning|afternoon|evening|night|\d)"
    r")")


def _the_fly_is_not_a_verb(understood):
    """False when the line's "fly" is the verb of travelling, which is not a fly in the house."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return _A_FLY_THAT_TRAVELS.search(text) is None


# A bar is a unit only when the line makes it one, the same rule the money rows use for a figure:
# "drop bars", "my bars are too low" and "should i get drop bars" are the bar you hold on a
# bicycle, and the boiler gauge was answering all three with "top the pressure up to between 1 and
# 1.5 bar". A figure beside it ("half a bar", "1.5 bar", "two bars") or a word that says what is
# being measured ("pressure", "psi", "gauge") is what makes it a reading.
_A_BAR_WITH_A_FIGURE = re.compile(
    r"\b(?:\d+(?:\.\d+)?|half|quarter|one|two|three)\s+(?:a\s+)?bars?\b")
_PRESSURE_WORDS = frozenset(("pressure", "psi", "gauge", "boiler", "boilers", "combi",
                             "radiator", "radiators", "heating", "central"))


def _a_gauge_reading(understood):
    """False for a bare "bar" that is not a measuring unit."""
    reading = understood or {}
    text = str(reading.get("clean") or reading.get("text") or "").lower()
    words = set(str(one).lower() for one in (reading.get("words") or ()))
    if words & _PRESSURE_WORDS:
        return True
    return _A_BAR_WITH_A_FIGURE.search(text) is not None


# A block-paved drive is not the patio's bed: blocks go down on sharp sand alone, no
# cement, with kiln-dried sand brushed into the joints afterwards - so the row answers
# "how much mortar for 20 square metres of block paving" with sand and a wacker plate
# rather than a 5:1 mix the job does not use. A reviewer caught this on the first head.
# A machine that will not empty is a fault, and "water" or "empty" on its own is not: the
# drain row keys both words, so a bias that lifted it over its neighbours took "how much water
# does a washing machine use", "my washing machine isnt heating the water" and "my washing
# machine smells when it drains" as well as the blocked filter it was written for. Naming the
# words that are *not* the fault is a list with no end - the litres, the heat, the smell, the
# cost, the car's screen wash - so the row asks instead for the fault itself, which is a short
# closed set: a block, a clog, a jam, water that will not go, a drain that is slow.
_WILL_NOT_EMPTY = re.compile(
    r"\b(block|blocks|blocked|blockage|blocking|clog|clogs|clogged|clogging|jam|jams|jammed|"
    r"stuff|stuffed|bunged|plugged)\b"
    r"|\b(backed|backing)\s+up\b"
    r"|\b(water\s+(is\s+)?(sitting|standing|left|stuck|pooling|pooled|trapped)|standing water|"
    r"full of water|water in the drum|water in the bottom|water inside the drum|pool of water|"
    r"water\s+(wont|won't|not)\s+(go|going|leave|leaving|drain|draining))\b"
    # the fault said as a negative about the emptying itself: "it doesnt drain", "i cant get the
    # washing machine to drain", "unable to get the water out", "stopped draining", "drains slowly"
    r"|\b(no|not|n't|cant|can\s+t|cannot|can\s*['\u2019]?\s*t|couldnt|couldn't|could not|"
    r"unable|wont|won't|wouldnt|wouldn't|doesnt|doesn't|didnt|didn't|isnt|isn't|wasnt|wasn't|"
    r"never|stopped|fail|fails|failed|failing|struggling|struggles)\b[^.]{0,45}?"
    r"\b(drain|drains|draining|drained|empty|empties|emptying|emptied|pump|pumps|pumping)\b"
    r"|\b(drain\w*|pump\w*|emptying)\b[^.]{0,18}?\b(blocked|clogged|jammed|stuck|slow|slowly|"
    r"sluggish|not working|broken)\b"
    r"|\b(slow|slowly|sluggish)\b[^.]{0,18}?\b(drain|drains|draining|empty|emptying)\b"
    r"|\b(empty|emptying|drain|draining)\s+(the|my|its|this)\s+(machine|washer|drum|water)\b"
    r"|\b(get|getting|got)\s+(the|my|its|this)\s+(water|machine|washer|drum|washing|clothes)\b"
    r"[^.]{0,22}?\b(out|to drain|to empty)\b"
    r"|\b(to\s+(get\s+it\s+)?(drain|empty))\b")


# The leak row keys the bare word "water", so "my washing machine isnt heating the water" was
# stopped, unplugged and told to turn the water off - the same trap the drain row was in. What a
# leak needs is water leaving: a leak, a puddle, a drip, a flood, or water somewhere it should
# not be. Asking for that also gives "water is coming out of the washing machine" its leak, which
# it never had: that line was the laundry-sorting card.
_WATER_LEAVING = re.compile(
    r"\b(leak|leaks|leaked|leaking|leaky|puddle|puddles|drip|drips|dripping|dribble|"
    r"flood|floods|flooded|flooding|pour|pours|pouring|seep|seeps|seeping|seeped|"
    r"spill|spills|spilling|spilt)\b"
    r"|\b(coming out|came out|running out|spilling out|working its way out|"
    r"water under|water on the|water in the bottom|water all over|underneath|"
    r"under\s+(the\s+|my\s+)?(machine|washing machine|washer|drum)|under it|"
    r"on the floor|all over the floor|wet floor|damp patch)\b")


# What a line that is about a wash says: the machine, the cycle, the load. The temperature row
# holds the bare figures "30" and "40" as key words, so any line with a figure beside a money
# word could reach it - "my phone bill is 30 a month" was the cost of a 30C wash, and it only
# showed once "month" stopped reading as a when question.
A_WASH_NAMED = frozenset((
    "wash", "washes", "washed", "washing", "laundry", "load", "loads", "cycle", "cycles",
    "machine", "washer", "tumble", "drum", "eco"))


# The figures said as a temperature, and the bare figures. "is 30 or 40 cheaper" is the row's own
# comparison and names no wash at all, so two of its temperatures in one line is the row's subject
# as much as the word wash is.
A_TEMPERATURE_SAID = re.compile(
    r"\b(?:20|30|40|60)\s*(?:c|degrees?|deg)\b"
    r"|\b(?:twenty|thirty|forty|sixty)\s+degrees?\b")
A_BARE_TEMPERATURE = re.compile(r"\b(?:20|30|40|60)\b")


def _a_wash_is_named(understood):
    """True when the line is about a wash, which is the subject this row is about.

    A temperature is only the subject of a line that is already about washing: a bill, a battery
    and a bus fare are all said with one figure, and each of them is another question. So the row
    answers a line that names the wash, a line that says a figure as a temperature ("30c",
    "thirty degrees"), or a line that compares two of its temperatures, which is the row's own
    question however it is typed.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    words = text.replace(",", " ").split()
    if any(word in A_WASH_NAMED for word in words):
        return True
    if A_TEMPERATURE_SAID.search(text):
        return True
    return len(set(A_BARE_TEMPERATURE.findall(text))) > 1


def _it_is_water_leaving(understood):
    """True when the line has water somewhere it should not be, which is what this row answers."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return bool(_WATER_LEAVING.search(text))


# The word "washer" is the machine to nearly everyone, and it is also the little rubber ring in a
# tap and the ring under a bolt. The rows that answer the machine read the bare word, which is
# right: on the deck almost every line that says "washer" means the appliance. What they must not
# do is answer a line that names the other one, so a plumbing or fixing word stands them down.
# "what size washer do i need for a 15mm tap" was told how many kilos a drum holds.
_A_WASHER = frozenset(("washer", "washers", "washing machine", "washer dryer"))
_ANOTHER_KIND_OF_WASHER = frozenset((
    "tap", "taps", "faucet", "faucets", "mixer", "monobloc", "ball valve", "ballcock",
    "bolt", "bolts", "nut", "nuts", "screw", "screws", "rawlplug", "rawlplugs", "anchor",
    "anchors", "rivet", "rivets", "dowel", "dowels", "valve", "valves",
    "radiator", "radiators", "banjo"))
_THE_MACHINE_ITSELF = frozenset(("washing machine", "washer dryer", "tumble dryer", "dryer",
                                 "drum", "laundry", "clothes"))


# A person who says they have already changed the washer is not asking how to change one: "my
# kitchen tap was dripping so i changed the washer" was answered with the washing machine's leak
# card, and the tap card would be nearly as wrong. What is left to do is the seat or the cartridge.
_A_WASHER_ALREADY_CHANGED = re.compile(
    r"\b(?:changed|change|replaced|replacing|swapped|swapping|new)\b[^.?!]{0,20}\bwasher\b"
    r"|\bwasher\b[^.?!]{0,20}\b(?:changed|replaced|swapped|done)\b", re.I)
_THE_NEXT_TAP_STEP = (
    "Then it is the seat rather than the washer. Take the head off again and look at the brass "
    "ring the washer presses on: if it is pitted or scored it can be re-ground with a seat tool, "
    "and if the tap turns a quarter turn it has a ceramic cartridge instead, which is replaced "
    "whole and matched by the maker's name stamped on the tap. A cartridge is a ten-minute swap "
    "and stops it for good; until then, turn the water off at the isolating valve when you leave "
    "the house.")
_THE_DRIPPING_TAP = (
    "A dripping tap is nearly always a worn washer or cartridge: turn the water off at the "
    "isolating valve under the sink, take the handle off, and take the old part to a hardware "
    "shop to match it. It's a 20-minute job and saves a lot of water.")


def _a_dripping_tap(memory, understood):
    """The washer is the answer, unless they have already changed it: then it is the seat."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    if _A_WASHER_ALREADY_CHANGED.search(said):
        return _THE_NEXT_TAP_STEP
    return _THE_DRIPPING_TAP


def _not_a_washer_of_another_kind(understood):
    """False for a washer that is a tap's or a bolt's, which no machine row can answer."""
    words = set((understood or {}).get("words") or ())
    if not (_A_WASHER & words):
        return True
    if _THE_MACHINE_ITSELF & words:
        return True
    return not (_ANOTHER_KIND_OF_WASHER & words)


# A report that the washing has been done is a follow-up, not a question about which washer it is:
# "ive changed the washer" is asking what to do next, and this card is the first thing it must not
# get. The past forms are here as words because the key matches word forms, not words.
_A_WASHER_DONE = re.compile(
    r"\b(?:already|changed|changing|replaced|replacing|swapped|swapping|fitted|fitting|"
    r"sorted|done|did|tried|trying)\b", re.I)


def _a_washer_with_no_other_subject(understood):
    """True when "washer" is the whole subject of the line, so the answer has to hold both senses."""
    words = set((understood or {}).get("words") or ())
    if not (_A_WASHER & words):
        return False
    if _THE_MACHINE_ITSELF & words or _ANOTHER_KIND_OF_WASHER & words:
        return False
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return not _A_WASHER_DONE.search(said)


_WASHER_TWO_THINGS = (
    "Two things in a house are called a washer. The ring inside a tap costs pennies: turn the "
    "water off at the isolating valve, take the tap apart and take the old ring to a hardware "
    "shop to match - half an inch fits most taps, three quarters the older big bath taps. If it "
    "is the machine, the fix depends on what it is doing: water on the floor is usually the door "
    "seal or a hose, clothes that come out wet is the spin, and no heat is the element. All three "
    "are cheap parts, so a machine with a sound drum is worth repairing rather than replacing.")
# The same word in a chat that has already been about a tap is not two things at all: the person
# who says "i have a washer and a spanner" beside a dripping tap has the part in their hand and
# wants the next step, and telling them about the machine would be answering nobody.
_THE_TAP_WASHER = (
    "Good - then you have what you need. Turn the water off at the isolating valve under the sink "
    "or the small screw on the pipe, take the handle off and unscrew the head, then pick the old "
    "washer out with a small screwdriver. Match it at a hardware shop: half an inch fits most "
    "taps, three quarters the older big bath taps. A smear of silicone grease on the new one and "
    "it goes back the same way, and the spanner is for the big nut under the handle.")
_A_TAP_TALK = re.compile(r"\b(?:tap|taps|faucet|dripping|drip|drips|spout|cistern)\b", re.I)


def _the_chat_is_about_a_tap(memory, understood):
    """True when the last turn or two named a tap and nothing named the machine."""
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    said_now = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    said_now = said_now.strip().lower()
    seen = 0
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        text = str(turn.get("user") or "").strip().lower()
        if not text or text == said_now:
            continue
        if _THE_MACHINE_ITSELF & set(text.split()):
            return False
        if _A_TAP_TALK.search(text):
            return True
        seen += 1
        if seen >= 2:
            break
    return False


def _a_washer_two_things(memory, understood):
    """The washer that a chat has already identified, or the two senses when it has not."""
    if _the_chat_is_about_a_tap(memory, understood):
        return _THE_TAP_WASHER
    return _WASHER_TWO_THINGS


def _the_leak_is_a_machines(understood):
    """The leak row's guard, plus the other sense of "washer": a tap's, not the machine's."""
    return _it_is_water_leaving(understood) and _not_a_washer_of_another_kind(understood)


def _a_machine_that_will_not_empty(understood):
    """True when the line names a machine that will not empty, which is what this row answers.

    The appliance or the drum is in the key already; this is the fault half, so a question that
    only mentions the water - how much it uses, how hot it gets, what it smells of - stands the
    row aside and keeps its own answer.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return bool(_WILL_NOT_EMPTY.search(text))


def _the_bed_for_paving_or_blocks(memory, reading):
    line = (reading.get("clean") or reading.get("text") or "").lower()
    words = set(reading.get("words") or ())
    if words & {"block", "blocks", "setts", "pavers"} or any(
            phrase in line for phrase in ("block paving", "block paved", "block paver",
                                          "block paving drive", "paved drive",
                                          "paving the drive")):
        return ("Blocks are not bedded on a sand-and-cement mix: they go down on 30 to 40mm "
                "of sharp sand alone, compacted with a wacker plate, and the joints are "
                "brushed full of kiln-dried sand afterwards - so there is no cement to "
                "measure. For 20 square metres reckon on about one tonne of sharp sand for "
                "the bed and two or three 25kg bags of kiln-dried sand for the joints, plus "
                "an edge restraint on any open side, which is what stops the blocks "
                "spreading.")
    return ("Patio slabs go on a full bed of 5:1 sharp sand and cement, 30 to 40mm thick, "
            "never on five dabs: a 25kg bag of cement with five 25kg bags of sharp sand "
            "beds about 2 to 2.5 square metres, so a 20 square metre patio wants nine or "
            "ten bags of cement and two bulk bags of sand. The mix should be crumbly-damp "
            "- squeeze a ball and no water runs - and the joints are pointed afterwards "
            "with a 4:1 mix, not the bed mix.")
# A stool is a chair and a stool is what a person passes, and the reading does not always settle
# which: "my stools are loose" came in with no body part, no own output and no health topic at
# all, so the chair row answered a stomach complaint with the wood glue. When the reading says
# nothing, the words still do: a line that says the looseness of what a body passes, and says
# nothing about a piece of furniture, is the body's.
# The plural is the gut's and the singular is the chair's: "my stool is loose" is the leg, and
# the reading and `tests.test_loose_stools_are_the_stomach` already settle that, while "my stools
# are loose" is one person and the part of them the plural names. "poo" and "bowels" are never
# furniture, so they count in either number.
_LOOSE_STOOL = re.compile(
    r"\b(?:stools|poos?|faeces|feces|bowels?)\b[^.?!]{0,24}?"
    # "bowels" is already plural, so "loose" is the whole of the shape here
    r"\b(?:loose|runny|watery|soft|sloppy)\b"
    r"|\b(?:loose|runny|watery|sloppy)\s+(?:stools|poos?|faeces|feces)\b", re.I)
# Anything that says the line is about a chair or a table instead: the fixing words are in here,
# so "the loose leg on my stool" stays with the glue even though it says loose and stool.
_FURNITURE_WORDS = re.compile(
    r"\b(?:chair|chairs|table|tables|bench|benches|desk|desks|leg|legs|glue|screw|screws|"
    r"tighten|joint|joints|wood|wooden|seat|furniture|varnish|paint|repair|fix|wobbl\w*|"
    r"rock\w*|rickety)\b", re.I)


def _a_chair_and_not_a_body(understood):
    """False when the line is the looseness of what a body passes, rather than a wobbly chair."""
    from .body import the_stomach_is_what_it_is_about

    understood = understood if isinstance(understood, dict) else {}
    if the_stomach_is_what_it_is_about(understood):
        return False
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    if _LOOSE_STOOL.search(text) and not _FURNITURE_WORDS.search(text):
        return False
    return True


def _the_fan_stopped(memory, understood):
    """The answer for the fan that will not sit still, or for a plain appliance that rocks."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if re.search(r"\b(?:fan|fans|blade|blades)\b", text):
        return ("A fan that rocks is usually the base or a bent blade: tighten the nut under the "
                "base, then take the blade off and sight along it, because one blade out of line "
                "is the whole wobble and a new blade is a few pounds. Stand it on a hard, level "
                "floor rather than a rug, and wind out the feet if it has them.")
    return ("A wobble is a loose base or an uneven floor rather than a fault: wind the feet out "
            "until it sits flat on all of them, tighten what holds the base to the body, and take "
            "it off a rug or a soft board, which is what most of them are standing on. If it is "
            "still rocking it wants shimming on one corner.")


# "and the kitchen stuff" is what a person says when the packing is already the chat: the phrase
# names the room with "stuff" and has no verb in it, so on its own it asks nothing. Asked first
# thing in a chat it was a whole plan for the boxes ("Leave the kitchen to the second-to-last
# day..."), answering a house move nobody had mentioned. "stuff" and "the rest" stay keys, but
# only for a line that has a packing word of its own or that is taking up a chat already about
# moving.
_PACKING_VERB = frozenset((
    "pack", "packs", "packing", "packed", "box", "boxes", "boxed", "boxing", "packup"))


def _the_kitchen_stuff_is_a_take_up(understood):
    """The bare "kitchen stuff" line answers only when it takes up a line before it."""
    reading = understood or {}
    said = str(reading.get("clean") or reading.get("text") or "").lower()
    if set(re.findall(r"[a-z]+", said)) & _PACKING_VERB:
        return True
    return bool(reading.get("followup"))


# The heat pump explainer is for the machine in the garden, and the words for the ones in the
# house were what carried a dryer question into it: "is a heat pump dryer any good" was told how a
# heat pump moves heat, and "how do i fix my heat pump tumble dryer" would have been too. A use
# word beside a question about the appliance - what it costs, whether it is any good, a fault - is
# the appliance's row, and this explainer keeps the lines that ask what a heat pump is or how it
# works.
_HEAT_PUMP_USE = ("dryer", "drier", "tumble dryer", "tumble drier", "dehumidifier", "radiator",
                  "radiators", "hot water tank", "cylinder", "shower", "pool", "swimming pool",
                  "air conditioning", "hot tub", "underfloor", "boiler")
_HEAT_PUMP_ASK = ("fix", "fixing", "repair", "repairing", "not working", "broken", "fault",
                  "faulty", "any good", "worth", "worth it", "cost", "costs", "price", "cheap",
                  "cheaper", "run", "running", "buy", "buying", "recommend", "noise", "noisy",
                  "loud", "install", "installed", "installation", "smell", "smells",
                  "efficient", "good")


def _the_explainer_keeps_the_explainer(understood):
    """False when the line is about a heat pump appliance, not about what a heat pump is."""
    text = " " + (understood.get("clean") or understood.get("text") or "").lower() + " "
    if not any(word in text for word in _HEAT_PUMP_USE):
        return True
    return not any(word in text for word in _HEAT_PUMP_ASK)


def _hair_dryer(memory, reading):
    """The grille for a dryer that blows cold, the flex for one that is dead.

    A hair dryer that runs but never warms and one that will not start are two faults with two
    first checks, and the same line shapes carry both ("stopped working", "keeps cutting out").
    STYLE asks for the thing to do first in the first sentence, so the answer is chosen by what
    the person said the machine is doing.
    """
    words = set(str(one).lower() for one in (reading.get("words") or ()))
    dead = {"dead", "stopped", "stop", "wont", "won't", "wont.", "turn", "turns", "start",
            "starts", "switch", "switches", "power", "fuse", "buzzing", "buzzes", "nothing"}
    if words & dead:
        return ("A hair dryer that is completely dead is nearly always the plug or the flex, not "
                "the element: try another socket, check the fuse in the plug, and look at the "
                "point where the flex meets the handle, because a cable that is wound up every "
                "day is what breaks. If a fresh fuse blows again, stop using it - that is a short "
                "in the element, and a new dryer is cheaper than the repair.")
    return ("Check the air intake first: a hair dryer that blows cold usually has the grille at "
            "the back furred up with hair and fluff, and the thermal cut-out trips before the "
            "element ever fails. Unplug it, pull the hair off the grille and out of the vent, let "
            "it cool for ten minutes and try it again on the high setting. If it still runs cold "
            "it is the element or the cut-out, and on a cheap dryer that is a new one rather than "
            "a repair - do not open the case, the element is a live part.")


def _to_a_figure(value):
    """A figure a person would say out loud: 4.46 -> 4.5, 2.0 -> 2, 1 -> 1.

    "a wall 6 ft long and 8 ft high" is 4.46 square metres, and a card whose own numbers are
    "10 to 12" reads as a measurement taken in a laboratory rather than a wall. One decimal is
    as fine as the sums behind it go, and the trailing zero goes.
    """
    return round(float(value), 1)


def _counted(value, unit):
    """The figure with its noun agreed with it: "1 litre", "About 2.5 litres", "1 square metre"."""
    return "%g %s" % (value, unit if _to_a_figure(value) == 1 else unit + "s")


PAINT_WITH_NO_SIZE = (
    "One litre of emulsion covers about 10 to 12 square metres, and you need two coats, so "
    "count the wall area and double it: add the walls up as perimeter times ceiling height "
    "(a 4m by 4m room with 2.4m ceilings is about 38 square metres), take off roughly 1.7 "
    "square metres for a door and 1.2 for a window, and that room wants about 7 litres - two "
    "5 litre tins, or a 10 to leave some for touching up. Ceilings and a second colour are "
    "extra, and a dark colour over a light wall often takes three coats.")


def _paint_for_the_room(memory, understood):
    """The litres for the wall or room in the line, or the method when the line has no size.

    The size the person gave is the answer's raw material: a wall 6 metres long and 2.5 high is
    15 square metres, and 15 square metres at two coats and 10 to 12 to the litre is about 3
    litres. Handing back a worked example of a different room answers the method, not the
    question. A room said as two sides is painted round its walls, so the perimeter times the
    ceiling height is the area - the height the line names, or 2.4m. A line with no size in it
    keeps the method, which is the only thing that can be said without one.
    """
    from .home import _wall_area
    area, ceiling, what = _wall_area(understood, memory)
    if not area:
        return PAINT_WITH_NO_SIZE
    # Rounded up to the next half litre, never down: a person who buys 2.5 litres for a wall
    # that wants 2.7 is one coat short, and the tin sizes are 2.5, 5 and 10 anyway.
    litres = max(1.0, int(area * 2 / 11.0 * 2 + 0.999) / 2.0)
    area = _to_a_figure(area)
    coats = "%g" % _to_a_figure(area * 2)
    if what == "ceiling":
        count = ("A ceiling that size is %s, two coats makes %s, and a litre of "
                 "emulsion covers 10 to 12." % (_counted(area, "square metre"), coats))
    elif ceiling is None:
        count = ("That's %s, two coats makes %s, and a litre of emulsion "
                 "covers 10 to 12." % (_counted(area, "square metre"), coats))
    else:
        count = ("A room that size is %s round and %s to the ceiling, so about %s of wall, and "
                 "two coats makes %s."
                 % (_counted(_to_a_figure(area / ceiling), "metre"), _counted(ceiling, "metre"),
                    _counted(area, "square metre"), coats))
    # A door and a window are a room's business: a single wall of 7 square metres has neither, and
    # the subtraction only muddles the figure it was just given.
    if what == "ceiling":
        tail = ("Give the walls their own sum, and go a coat further when a white ceiling is "
                "going over a colour rather than over white.")
    elif ceiling is None:
        tail = ("Allow a third coat when a dark colour goes over a light one, and give the ceiling "
                "and any second colour their own sum.")
    else:
        tail = ("Take off roughly 1.7 square metres for a door and 1.2 for a window if they are in "
                "it, allow a third coat when a dark colour goes over a light one, and give the "
                "ceiling and any second colour their own sum.")
    return "About %s: %s %s" % (_counted(litres, "litre"), count, tail)


WALLPAPER_WITH_NO_SIZE = (
    "Count drops, not floor: divide the room's perimeter by the 52cm width of a standard roll and "
    "round up (a 4m by 4m room is 16m round, so 31 drops), then divide a roll's 10m by the ceiling "
    "height plus the pattern repeat to see how many drops each gives - usually three - and 31 drops "
    "is about 11 rolls. Buy one extra for a mistake and matching, and keep the batch number the "
    "same on every roll.")


def _wallpaper_for_the_room(memory, understood):
    """The rolls for the room in the line, or the method when the line has no size.

    A room said as two sides is papered round its walls, so the wall area already worked out for
    paint is the starting point: the perimeter is that area divided by the ceiling height, a
    standard roll is 52cm wide, and a 10m roll gives four drops of a plain paper at a 2.4m ceiling
    and three of a paper with a big repeat. A single wall has no perimeter to read the drops from,
    so it keeps the method, which is also what a line with no size gets.
    """
    from .home import _wall_area, _wall_width_and_height
    area, ceiling, what = _wall_area(understood, memory)
    if not area:
        return WALLPAPER_WITH_NO_SIZE
    if what == "wall":
        # A wall with a size in the line is drops along its own width, not a room's perimeter
        # read off an area: "how much wallpaper for a wall 1m by 1m" is one drop of a 52cm roll,
        # and the card's own example is a room, which is what it keeps teaching.
        width, height = _wall_width_and_height(understood, memory)
        if not width or not height:
            return WALLPAPER_WITH_NO_SIZE
        across = int(-(-width / 0.52 // 1))
        plain = max(1, int(10 // height))
        patterned = max(1, int(10 // (height + 0.3)))
        plain_rolls = int(-(-across / plain // 1))
        patterned_rolls = int(-(-across / patterned // 1))
        return ("About %s: a wall %s wide and %s high takes %s at the 52cm width of a standard "
                "roll, and a 10m roll gives %s of a plain paper or %s of one with a big repeat - "
                "so %s plain and %s patterned. Buy one extra for a mistake and matching, and keep "
                "the same batch number on every roll."
                % (_counted(plain_rolls, "roll"), _counted(_to_a_figure(width), "metre"),
                   _counted(_to_a_figure(height), "metre"), _counted(across, "drop"),
                   _counted(plain, "drop"), _counted(patterned, "drop"),
                   _counted(plain_rolls, "roll"), _counted(patterned_rolls, "roll")))
    if what != "room" or not ceiling:
        return WALLPAPER_WITH_NO_SIZE
    round_the_room = area / ceiling
    drops = int(-(-round_the_room / 0.52 // 1))
    plain = max(1, int(10 // ceiling))
    patterned = max(1, int(10 // (ceiling + 0.3)))
    rolls_plain = int(-(-drops / plain // 1))
    rolls_patterned = int(-(-drops / patterned // 1))
    return ("About %d rolls: a room that size is %g metres round and %g metres to the ceiling, so "
            "%d drops at the 52cm width of a standard roll, and a 10m roll gives %d drops of a "
            "plain paper or %d of one with a big repeat - so %d rolls plain and %d patterned. Buy "
            "one extra for a mistake and matching, and keep the same batch number on every roll."
            % (rolls_plain, round_the_room, ceiling, drops, plain, patterned,
               rolls_plain, rolls_patterned))


# A nail in a wall is two jobs: putting one in, and getting an old one out. The two lines share
# every noun they use ("nail", "wall", "picture"), so the row below reads the verb and answers
# the job that was asked for, the way the hair-dryer row reads the fault.
_A_NAIL_COMES_OUT = ("remove", "removing", "removed", "out", "puller", "pincers", "pull",
                     "pulling", "pulled", "old", "stuck", "left", "loose", "snapped", "broke",
                     "broken", "half")


def _a_nail_in_the_wall(memory, reading):
    """How to get an old nail out of a wall, or how to put a new one in so it holds."""
    words = set(str(one).lower() for one in (reading.get("words") or ()))
    if words & set(_A_NAIL_COMES_OUT):
        return ("Grip the head with pincers and slide a scrap of wood under them so the plaster "
                "does not crush, then ease it out with a slight twist rather than levering "
                "against the wall. A nail that turns but will not come has lost its grip: punch "
                "it below the surface with another nail, fill the dent with filler, sand it flat "
                "and touch up the paint.")
    return ("Tap it in at a slight downward angle so the weight hangs on the wall instead of "
            "pulling the head out, and put it into something solid - a stud, found by tapping, "
            "or brick under the plaster. On plasterboard with nothing behind it a bare nail or "
            "a picture hook pulls out: use a plasterboard plug or a self-drilling fixing, and "
            "keep the load light.")


# A nail into wood is two questions: how not to split the board, and what size to buy. The same
# line shapes carry both ("what nail for ...", "how do i stop ... splitting"), so the row reads
# which one was asked, the way the nail-in-a-wall row reads putting in from taking out.
_A_SIZE_ASK = ("size", "sizes", "what size", "which size", "what length", "how long", "how big", "how thick", "which nail",
               "what nail", "what nails", "how many mm", "mm", "gauge", "best nail", "should i use")
_A_SPLIT_ASK = ("split", "splits", "splitting", "crack", "cracks", "cracking", "splinter",
                "splinters", "splintering", "snapped")


def _the_wood_and_the_nail(memory, reading):
    """What size of nail to buy, or how to drive one without splitting the board."""
    words = set(str(one).lower() for one in (reading.get("words") or ()))
    said = " " + " ".join(str(one).lower() for one in (reading.get("words") or ())) + " "
    # the asks are phrases ("what size", "how long"), and `words` holds one word each, so the
    # joined line is what the phrase list is read against
    if (any(ask in said for ask in _A_SIZE_ASK)) and not (words & set(_A_SPLIT_ASK)):
        return ("Size the nail to the job, not to the room: 40mm to 50mm lost-head or oval nails "
                "for skirting and architrave, 50mm to 65mm for a floorboard, 30mm for a 6mm "
                "batten, and thin panel pins for beading and a back panel. As a rule the nail "
                "wants to be about two and a half times as long as the piece it is holding, and "
                "the top third of it has to bite into something solid behind.")
    return ("Drill a pilot hole first, about three quarters as wide as the nail, and keep it at "
            "least 25mm in from the end of the board, because that is where a split starts. "
            "Blunt the point by tapping it once on a hard surface so it cuts the grain instead "
            "of wedging it apart, and clamp a scrap of wood behind the far face when the board "
            "is thin. A split that has already opened wants wood glue worked into it and a "
            "clamp overnight, not another nail.")


# The move-and-a-child card answers one question: how to tell a child about the move. Its key
# carries the feeling words ("upset", "worried", "nervous", "sad", "cope") because a child's feeling
# is often the whole line - "my son is upset about moving" - and with them the card answered the
# person who had moved themselves: "im sad after moving house", "i feel sad about moving house",
# "im worried about moving house" and "we are moving and i feel nervous" all got "Tell them as soon
# as it is certain ... which room is theirs". A feeling in the speaker's own line is not a question
# about telling a child, so the card is a guard rather than a longer avoid list: an avoid phrase only
# covers the wordings someone thought of, and every new feeling word would need another one.
_A_CHILD_IN_A_MOVE = re.compile(
    r"\b(?:kid|kids|child|children|son|sons|daughter|daughters|teenager|teenagers|teen|teens|"
    r"toddler|toddlers|baby|babies|boy|boys|girl|girls|schoolchild|schoolchildren|"
    r"stepson|stepdaughter|stepchildren|little one|little ones|the youngest|the eldest)\b")

# "how do i tell them we are moving" names no child and is still this card's question, so a line
# that asks for the words to say passes too. It is the telling that makes the audience the children,
# not the noun: "how do i tell my mum i'm moving out" is answered by family.py and never reaches
# this row, because "move out" is in the avoid list below.
_A_TELLING_THE_LINE_ASKS_FOR = re.compile(
    r"\b(?:tell|tells|telling|told|explain|explains|explaining|explained|break the news|"
    r"let them know|lets them know|prepare them|preparing them|reassure|reassuring)\b")


def _a_child_or_a_telling(understood):
    """True when the line names a child, or asks for the words to say about the move.

    Used as the `guard` by the moving-with-kids row. Without it the row's feeling words answer the
    person who moved: "im sad after moving house" was told how to tell a child, and so was
    "i feel sad about moving house" and "im worried about moving house". A line with nobody to tell
    in it is not that question.
    """
    said = understood if isinstance(understood, dict) else {}
    text = " ".join(str(said.get("norm_text") or said.get("plain") or said.get("text") or "")
                    .lower().split())
    return bool(_A_CHILD_IN_A_MOVE.search(text) or _A_TELLING_THE_LINE_ASKS_FOR.search(text))
# The outside-drying row answers the weather, and a line that says inside, a bathroom, a
# radiator, a rack or a tumble dryer wants the drying-indoors answer instead. Those words cannot
# be an avoid list: a line with a "without" clause is read twice, and on the reading with the
# clause emptied the words are gone - "how do i dry clothes without a tumble dryer" reached the
# outside row on "dry" and "clothes" alone, once the ironing card had turned the same line down.
# The guard reads the line as it was typed, so the clause's words are still there.
_DRY_IT_INDOORS = (
    "inside", "indoors", "indoor", "in the house", "in the flat", "bathroom", "radiator",
    "airer", "rack", "maiden", "tumble dryer", "tumble drier", "tumbledryer", "dryer",
    "drier", "dehumidifier", "no garden", "no line", "nowhere to hang", "condensation",
)
_DRYING_WORD = re.compile(r"\bdry(?:ing|s|er|d)?\b|\bhang(?:ing)?\b|\bwashing\b|\blaundry\b",
                          re.I)
# A line that names the weather is the outside row's own question even when it says inside:
# "should i bring the washing inside before the rain" is a forecast question, not a rack one.
_THE_WEATHER = re.compile(
    r"\b(?:rain|rains|raining|rainy|showers?|forecast|wind|winds|windy|sun|sunny|sunshine|"
    r"weather|frost|frosty|drizzle|damp|fog|line|outside|out there|today|tomorrow|dry out)\b",
    re.I)


# A load of washing, named. A room being damp is not a load: "how do i dry out a damp room"
# is the damp card's question, and naming a room only says where the washing is.
_A_LOAD_NAMED = re.compile(
    r"\b(?:washing|laundry|clothes|clothing|load|jeans|trousers|shirts|sheets|bedding|"
    r"towels?|duvets?|jumpers?|coats?|jackets?|wool|knitwear|uniform|school uniform)\b", re.I)
# The rooms a person dries a load in. A flat with one room and no garden is the whole reason
# the line is asked: "how do i dry clothes in a damp flat" was told "a dry, breezy day dries a
# normal load outside in two to four hours", which is no help to somebody with no outside.
_A_ROOM = re.compile(
    r"\b(?:room|rooms|bedroom|kitchen|bathroom|cellar|loft|hallway|hall|utility|"
    r"flat|house|home|studio|caravan)\b", re.I)
# "damp" is a room and a day at once, so a named room tells us which one it is here.
_WEATHER_NOT_A_ROOM = re.compile(
    r"\b(?:rain|rains|raining|rainy|showers?|forecast|wind|winds|windy|sun|sunny|sunshine|"
    r"weather|frost|frosty|drizzle|fog|line|outside|out there|today|tomorrow)\b", re.I)


def _not_a_drying_inside_question(understood):
    """False when the line is about drying the washing indoors rather than in the weather."""
    text = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    if not _DRYING_WORD.search(text):
        return True
    if _A_LOAD_NAMED.search(text) and _A_ROOM.search(text):
        # the load and the room are both named: the rack's answer, unless the weather is the
        # question ("should i bring the washing inside before the rain")
        return bool(_WEATHER_NOT_A_ROOM.search(text))
    if not any(word in text for word in _DRY_IT_INDOORS):
        return True
    return bool(_THE_WEATHER.search(text))


def entries():
    """The rows `home.py` builds its list from, in their original order."""
    from .home import not_a_sound
    from .home import (
    APPLIANCE_DOOR_WORDS, BODY_WORDS, COST_WORDS, EXTRACTOR_GREASE_FILTER, FIRST_NIGHT_BOX,
    FITTING_SHARED_STANDDOWN, JOB_GUARD, LANDLORD_JOB_FITTINGS, LANDLORD_REPAIR_LETTER,
    LETTING, LIFE_ASK, LIFE_GUARD, LIFE_NAMES, MACHINE_BURNING, MACHINE_DEAD, MACHINE_LEAKING,
    MACHINE_SOUNDS, NOISE_WORDS, NORMAL_CUTOUT, NOT_A_FENCE_JOB, NOT_A_TRADE_WORDS, RUNNING_WORDS,
    TAKES_THINGS, THING_PARTS, TUMBLE_DRYER_FILTER, WASHING_MACHINE_FILTER, _BATH_CITY,
    _DIY_AVOID, _SMOKING_THING, _TAKING_PAINT_OFF, _a_dryer_is_not_a_washer, _a_fence_is_named,
    _not_a_size_of_a_home, _a_machine_consumable,
    _a_mark_that_is_live, _a_room_being_heated, _a_safety_ask, _a_thing_owns_the_part,
    _alarm_nuisance,
    _appliance_cutting_out, _appliance_noise, _asks_the_ceiling_colour, _bath_length,
    _boiler_noise, _the_boiler_is_not_the_fault, _a_visit_not_a_purchase, _broken_window, _chemical_safety, _colour_advice, _consumer_unit, _diy,
    _door_lock_stiff, _dryer_heat, _fitting_repair, _furniture_upstairs, _going_to_the_loo,
    _heating_goes_cold, _heat_pump_answer, _a_person_not_a_hob, _hob_heat, _iron_fault, _kettle_will_not_stop,
    _lifespan, _lost_keys, _machine_fault,
    _machine_takes, _mould, _not_a_cook_ask, _not_a_machine_that_has_gone, _paint_brush_care,
    _pipes, _place_smell,
    _the_black_is_not_a_body,
    _pressure_weak, _radiator_not_hot, _repair_judgement, _roof_leak, _running,
    _small_appliance_not_heating, _smoking_appliance, _soft_smell, _the_paper_is_in_the_line,
    _washer_price, _washer_sound_fault, _water_off, _where_the_consumable_goes, entry,
    the_fault, the_filter_of,
    the_stomach_is_what_it_is_about, the_trade_to_call,
    )
    # The temperature rows stand aside for the argument sense of "heated" (bot/knowledge/lookup.py).
    from .lookup import not_the_heat_of_an_argument
    # The guard on the night-tariff row below reads the ask (`lookup.asks_where`), and it is
    # imported here rather than re-exported through `home.py` so that this file stays a list of
    # rows with nothing of its own.
    from .lookup import RING_AS_A_CALL, a_sanding_job, asks_where

    # What the two room-temperature rows hold out of their keys, the heat-a-room row and the
    # keep-room-cool row. "why is my fridge not cold", "the oven isnt heating up" and "cheapest
    # way to keep the freezer cold" are questions about the appliance and keep their own
    # answers; a room described AS the appliance is these two rows' question. A bare "fridge",
    # "freezer" or "oven" cannot tell those apart, and on the way it took "this office is like a
    # fridge" and "my bedroom is like an oven" out of the room rows and left them unanswered.
    THE_APPLIANCE_ITSELF = (
        "my fridge", "the fridge", "our fridge", "fridge is", "fridge not", "fridge too",
        "fridge door", "fridge keeps", "in the fridge", "fridge cold",
        "my freezer", "the freezer", "our freezer", "freezer is", "freezer not", "freezer cold",
        "in the freezer", "freezer door",
        "my oven", "the oven", "our oven", "oven is", "oven not", "oven too", "oven on",
        "in the oven", "oven door", "fan oven", "oven cold",
    )

    return [
        # A stair gate had no card at all: "how do i fit a stair gate" and "do i need a stair
        # gate" were both "I don't know enough to answer that honestly", and "how do i fit a stair
        # gate round the newel post" was the rounding rule, because "round" is the maths verb
        # there. The one thing that matters is which way it is fixed.
        entry(
            "stair-gate",
        (("stair gate", "stair gates", "stairgate", "stairgates", "baby gate", "baby gates",
          "safety gate", "safety gates", "child gate", "child gates", "pressure gate"),
         ("fit", "fits", "fitting", "fitted", "install", "installing", "put up", "putting up",
          "fix", "fixing", "mount", "mounting", "buy", "need", "which", "best", "top", "bottom",
          "stairs", "staircase", "newel", "banister", "bannister", "wall", "doorway", "toddler",
          "baby", "measure", "measuring", "remove", "take down")),
        "At the top of the stairs use a screw-fixed gate, never a pressure-fit one: a pressure gate "
        "grips between two surfaces and a determined toddler can push it out of the opening, and the "
        "top of the stairs is the one place that matters. A pressure gate is fine in a doorway or at "
        "the bottom of the stairs, where it needs no drilling, but check it by hand every week or so "
        "as the pads work loose. Measure the opening at its widest and buy a gate whose stated range "
        "covers it, and add a banister or newel-post adaptor, or an extension, when one side is a "
        "post rather than a flat wall. Look for a gate to BS EN 1930, at least 73cm high, with a door "
        "that swings away from the stairs, and no bottom bar across a step because it is a trip.",
        ask=("how", "what", "which", "do i need", "should i", "best", "fit", "install", "buy"),
        avoid=("dog", "dogs", "puppy", "cat", "cats", "pet", "pets", "rabbit", "chicken",
               "chickens", "hens", "goat", "garden", "driveway", "field", "fence", "gate post",
               "gatepost", "wooden gate", "front gate", "back gate", "side gate", "airport",
               "departure", "boarding", "flight", "concierge", "number", "digits", "decimal"),
        bias=2),

        # --- who to call --------------------------------------------------------
        # The trade is the answer, so it is the first thing said. The keys are the asking and the
        # reply is worked out from the thing named, because one row per trade would let the wrong
        # trade answer a line that names two ("a leaking roof" is a roofer, not a plumber).
        # A trade quotes a price for the job, so there is nothing to tip on top of it. The tip table
        # is money's, and a line naming a trade is read as a home question ("plumber" is what the
        # home-and-diy topic is about), so the answer has to live here to be reached at all: the
        # money row was turned down on the topic and "how much do you tip a plumber" fell through to
        # the careers entry about getting into the trades.
        entry("a-trade-is-not-tipped",
              (("tip", "tips", "tipping", "tipped", "gratuity"),
               ("plumber", "electrician", "builder", "decorator", "joiner", "carpenter", "plasterer",
                "tiler", "mechanic", "fitter", "engineer", "gas engineer", "boiler man", "handyman",
                "roofer", "scaffolder", "tradesman", "workman")),
              "No: a plumber, an electrician or a builder quotes a price for the job, and that price "
              "is the whole of it. A tip is not expected and can read as odd, so the thing worth "
              "doing instead is offering a tea and paying on time.",
              # What the trade costs is the price card's question, not this one: a tip word is what
              # makes this row an answer, so the two never meet.
              avoid=("how much does", "how much is", "cost", "costs", "charge", "charges",
                     "quote", "hourly", "day rate"),
              # "how much do you tip a plumber" is this row asked with a price in front of it, and
              # the careers entry (what the trades pay, what you need to get in) fits the same words:
              # the tip row is the one the line is asking.
              bias=4),

        entry("who-to-call",
              (("who", "who to", "which engineer", "which tradesman", "what kind of engineer",
                "anyone i can call", "someone to call",
                "who do i call", "who should i call", "who do i ring", "who should i ring",
                "who do i get"),
               ("call", "ring", "get", "get in", "tradesman", "engineer", "come out", "phone",
                "fix")),
              the_trade_to_call,
              # the reply is the trade, so the line has to be asking for one and naming something a
              # trade owns: where it names a person or an organisation instead, that line has its
              # own answer and this row must not stand in front of it
              avoid=NOT_A_TRADE_WORDS),

        # --- lighting a fire ----------------------------------------------------
        # `the living room is cold` then `how do i start the fire in the wood burner` was the search
        # hedge: `cleaning.py` names the wood burner in its hob entry's `avoid=` so the "wipe a hob"
        # answer does not take the line, and then nothing offered anything at all. Lighting a fire is
        # a job with an order to it, so it gets the steps a careful neighbour would give, and the one
        # thing that turns a stove into a chimney fire is said out loud.
        entry("lighting-a-fire",
              (("wood burner", "woodburner", "wood burning stove", "woodburning stove",
                "log burner", "logburner", "log fire", "open fire", "wood stove", "wood fire",
                "multifuel stove", "multi fuel stove", "fireplace", "woodburner stove",
                "coal fire", "stove"),
               # the asking: lighting it, keeping it in, and what it does when it is wrong. The
               # noun above is what makes a line about a stove at all, so this group holds the verbs
               # and nothing else - bare "log", "wood" and "coal" here made "how much is a log
               # burner", which is a price, a fire, and a bare "how do i" / "how to" every line in
               # the deck carries shifts what is rare and takes other answers' turns.
               ("light", "lighting", "lit", "start", "starting", "kindle", "kindling",
                "get it going", "get going", "get the fire going", "fire going", "light the fire",
                "start the fire", "going out", "goes out", "gone out", "keeps going out",
                "wont light", "won't light", "wont stay in", "smokes", "smoking", "smoulders",
                "damper", "air control", "vent", "going", "get it lit", "burner going",
                "stove going", "fire lit",
                "lay a fire", "lay the fire", "lay it")),
              "Open the air control fully, clear the grate but leave an inch of ash, and lay eight or "
              "ten sticks of kindling in a loose criss-cross with a firelighter or a twist of "
              "newspaper in the middle. Light it low down and leave the door on the latch rather than "
              "shut, so air can get in, and wait until the kindling is properly caught before you add "
              "one or two split logs - a big log laid on a small flame is how a fire goes out. Once "
              "the fire is going and the glass has cleared, shut the door and close the air down to "
              "about a finger's width; that is what stops it burning through a load in an hour. If it "
              "smokes into the room on a cold day the flue is cold, so hold a lit twist of newspaper "
              "up near the throat of the stove for a minute first. Dry wood and a swept flue are the "
              "two things that keep it easy: fit a carbon monoxide alarm in the same room, have the "
              "chimney swept once a year, and never use petrol, meths or barbecue fluid to start it, "
              "because a sooted flue is what turns a stove into a chimney fire.",
              bias=1,
              # a sweep, an installation, a price and the alarm are each their own answer, and a
              # bonfire or a fire pit is not a stove in a room
              avoid=("sweep", "sweeps", "sweeping", "swept", "chimney sweep", "flue liner",
                     "install", "installation", "fitter", "buy", "best one", "which one", "cost",
                     "price", "cheap", "worth it", "how much", "how many", "broken", "not working",
                     "wont work", "no heat",
                     "smoke alarm", "carbon monoxide", "alarm going off", "chimney fire",
                     "caught fire", "on fire", "bonfire", "fire pit", "garden fire", "barbecue",
                     "bbq", "grill", "charcoal", "smoker", "pizza oven", "candle", "hob", "pilot",
                     "boiler", "oven",
                     # a gas fire has no grate, no kindling and no damper: it is a pilot, an
                     # ignition and, if there is a smell of gas, a safety line. "my gas stove wont
                     # light" was given the wood-burner steps, which is a confident answer to a
                     # different appliance - and gas is the one thing in the house nobody should
                     # be told to take apart.
                     "gas", "gas stove", "gas fire", "gas fireplace", "gas hob", "ignition",
                     "clicking", "spark", "electric", "electric fire",
                     "outdoor", "allotment", "campfire", "stove top", "cook on", "cooking",
                     "glass", "paint", "rust", "door seal", "rope seal", "replace the")),

        # --- damp, mould, condensation -----------------------------------------
        # A bare "black" made this the answer to every line with the word in it: "i dropped something
        # on my toe and the nail has gone black" came back as scrub it with mould spray. Black is only
        # mould when it says what it is on, so the phrase is the key and the bare word is gone.
        # "should i use bleach on mould" and "does bleach kill mould" were a "Not mine to decide" and
        # a search hedge: the answer below names no surface, so the mould entry's second group - the
        # rooms and the places - never matched it. What people want is the short verdict, on what it
        # works and what it only paints over.
        entry("bleach-on-mould", (("bleach", "bleach solution", "thin bleach", "milton",
                                   "mould spray", "vinegar"),
                                  ("mould", "mold", "mildew", "kill", "kills", "killing", "dying")),
              # The first sentence has to be the verdict, and it is the one a repeated question gets
              # back (a repeat is answered with the sentence that shares most with the line, shortest
              # on a tie), so it carries bleach, mould, kill and "on" - the words the line uses.
              "Yes: vinegar is the gentler of the two and bleach at about one part to four of water is "
              "the stronger, and either kills the mould it reaches on tiles, grout, glass and the "
              "sealant round a bath - gloves on, window open, never mixed with another cleaner. On "
              "plaster, paint, wood or fabric neither does more than lift the colour, because it "
              "cannot get at mould that has grown in, so those want a mould spray, or the sealant cut "
              "out and replaced. And it is the damp that brings it back, so that is the part to fix.",
              # Bleach on a stain, on fabric, in a wash or down a drain is another entry's question, and
              # so is the mould that has gone into food. A ceiling, a wall or a bit of skirting belongs
              # to the mould entry, which finds the water the mould is living on - the right answer for
              # plaster and paint, and one whose first sentence is about the room, not a tile.
              # "whites" alone kept the bleach-it-whiter lines out, but the form table folds "white"
              # into it, so "does white vinegar kill mould" was zeroed by its own avoid and fell to a
              # shrug. Held as the phrases a person uses for the laundry instead.
              avoid=("stain", "stains", "my whites", "the whites", "in with the whites",
                     "white wash", "colors", "colours",
                     "towels", "washing machine", "in the wash",
                     "drain", "sink", "bin", "bread", "cheese", "food", "jam", "the fridge",
                     "nail", "toe", "finger",
                     "ceiling", "ceilings", "wall", "walls", "wardrobe", "skirting",
                     "behind the", "under the window")),
        entry("mould-bathroom", (("mould", "mold", "mildew", "mouldy", "moldy",
                                  "black mould", "black mold", "black spots", "black patch",
                                  "black patches", "black marks", "black staining", "black on the",
                                  # "the sealant has gone black" names no mould at all: the colour is
                                  # the complaint. Safe to key now that the second group is a surface,
                                  # so a nail that went black cannot reach it.
                                  "gone black", "going black", "turned black", "turning black",
                                  "black in the corner", "black behind the", "black round the",
                                  "black around the",
                                  # "how do i stop my bathroom going mouldy" is the plainest way to
                                  # ask about the wall, and it tied with the bathroom cleaning order
                                  # at two words each, so the cleaning won. The shape people use -
                                  # going, gone, gets, keeps getting - is the mould itself.
                                  "going mouldy", "going moldy", "gone mouldy", "gone moldy",
                                  "gets mouldy", "gets moldy", "getting mouldy", "getting moldy",
                                  "keeps going mouldy", "keeps getting mouldy", "mouldy again",
                                  "moldy again"),
                                 # "my shower has gone mouldy" is this answer, and so is the sealant
                                 # round it: the words below are the surfaces, not the food that molds.
                                 # The bare colour word used to sit here and stood in for a surface too,
                                 # so "black mould in the bedroom" matched on black+black while the room
                                 # named nothing at all; the rooms and the "is it dangerous" ask are
                                 # here now, which is what that word was doing by accident.
                                 ("bathroom", "ceiling", "ceilings", "wall", "walls", "wallpaper",
                                  "remove", "get rid", "stop", "shower", "showers", "shower cubicle",
                                  "sealant", "silicone", "grouting", "tile", "tiles", "window",
                                  "windows", "window frame", "frame", "windowsill", "corner",
                                  "corners", "bedroom", "bedrooms", "kitchen", "hall", "hallway",
                                  "loft", "attic", "cupboard", "wardrobe", "skirting", "paint",
                                  "dangerous", "harmful", "unhealthy", "bad for", "smell", "smells",
                                  "smelly", "damp", "flat", "house", "home", "room", "rooms",
                                  # The follow-up people send after the first wipe-down names no
                                  # surface and asks nothing but "and it is here again": the entry's
                                  # rooms and places never matched it, so it fell to a shrug. These
                                  # are the words a returning patch uses, and the answer already ends
                                  # on them - "if it keeps returning in the same place, that patch is
                                  # a damp problem, not dirt".
                                  "keeps coming back", "keep coming back", "comes back",
                                  "coming back", "keeps returning", "keeps coming",
                                  # "my laptop screen is mouldy" names no wall at all: the device is
                                  # the subject, and the words below let it reach the entry. What the
                                  # answer says is decided in _mould, where a device gets the gentler
                                  # wipe and its own warning about the damp behind it.
                                  "screen", "screens", "monitor", "monitors", "laptop", "laptops",
                                  "phone", "phones", "handset", "keyboard", "keyboards", "headset",
                                  "headsets", "headphones", "earbuds", "earphones", "airpods",
                                  "gasket", "gaskets", "door seal",
                                  "returns", "returning", "again", "spreading", "spread",
                                  "getting worse", "getting bigger", "keeps growing",
                                  # The colour belongs here, not in the key: a line needs a mould
                                  # word to get as far as this group, so "black mould" is mould plus
                                  # black - the plainest way people name it - while a nail that went
                                  # black names no mould at all and never reaches this entry.
                                  "black",
                                  # "mould behind the tv" says mould and a place and no surface, and
                                  # it is the plainest wall question of the lot: the place is the
                                  # surface, named by a preposition. Safe for the same reason the
                                  # colour is - the first group still has to name mould.
                                  "behind", "behind the", "above the", "under the", "underneath",
                                  "under it", "next to", "beside", "around the", "along the",
                                  "behind it", "above it",
                                  # the ask with no surface in it: "what can i do about the mould"
                                  # names no room, so it scored on the mould word alone, fell just
                                  # short and went to the boot with moulded studs. The act of asking
                                  # is enough of a second word here because the first group is already
                                  # a mould word, so none of these can carry a line on its own.
                                  "do about the mould", "do about mould", "deal with the mould",
                                  "deal with mould", "about the mould", "about mould",
                                  "with the mould", "of the mould", "the mould problem",
                                  "handle mould", "sort out mould", "the mould keeps")),
              _mould,
              # "gone black" and "turned black" are how people name mould without the word, and
              # they are how they name a bruise too: `my ankle is sprained` then `its turned black`
              # was told to wipe it with a mould spray. A line naming a body part or a bruise with
              # no mould word and nothing in the house is the body's question.
              guard=_the_black_is_not_a_body,
              # mould on food is a keeping question, not a wall to scrub, and a knock that left a
              # nail or a finger black is body's question. The fruits and vegetables below go black
              # on their own: "how do i stop my avocado going black" was taken by "going black" plus
              # "stop" and told to wipe it with a mould spray.
              avoid=("bread", "food", "cheese", "jam", "fruit", "veg", "vegetables", "milk", "meat",
                     "leftovers", "the fridge", "a fridge",
                     "nail", "nails", "finger", "thumb", "toe", "banged", "slammed", "bruised",
                     "dropped", "knocked", "hit it",
                     "avocado", "avocados", "guacamole", "apple", "apples", "banana", "bananas",
                     "pear", "pears", "potato", "potatoes", "aubergine", "aubergines",
                     # "black on the" is the plainest way to name mould on a wall, and it also reads
                     # "everything went black on the bus": a person's sight going is not a wall, and
                     # the faint it is belongs to the 111 answer, not to a mould spray.
                     "went black", "went dark", "vision", "sight",
                     # A plant that has gone black is the garden's, and the garden rows name the rot
                     # or the fungus: "why are my tomatoes going black at the bottom" matched "going
                     # black" and "bottom" here and was told to wipe it with a mould spray.
                     "tomato", "tomatoes", "tomato plant", "rose", "roses", "plant", "plants",
                     "leaves", "leaf", "blossom end", "courgette", "courgettes", "cucumber",
                     "cucumbers", "seedling", "seedlings", "cutting", "cuttings", "greenhouse",
                     # "my laptop screen keeps going black" was answered with a mould spray, because
                     # "going black" is in the key and a screen names no surface the key knows. The
                     # device words are handled where the line can be read: _mould stands down when a
                     # screen is named and no wall, window or room is, which keeps "the wall behind my
                     # monitor has gone black" as mould. The charger words below are never a wall.
                     "charger", "charging", "windows update", "reboot", "battery",
                     # The grout has its own card, and it already covers the mould in it ("for black
                     # mould in the grout, use a mould spray... sealing the grout keeps it that way").
                     # "the grout in my shower has gone blak, how do i cleen it" reached this entry the
                     # moment the slip was repaired to "black", and was told to run the fan with no
                     # word about grout at all.
                     "grout", "grouting",
                     # A tenant whose landlord will not deal with the mould is asking about the
                     # landlord, not about the scrub: "my landlord wont deal with the mould" and "my
                     # landlord is ignoring me about the mould" both got this wipe because the ask
                     # phrase names the mould, and the repair-letter answer is the one they need.
                     # So the words that make a mould line a tenancy line keep this entry out of it.
                     # Only the phrasings the repair answer can actually take are here: a bare
                     # "landlord" also reads "the mould keeps coming back and my landlord does
                     # nothing", which the repair entry does not match, and standing this one down
                     # there left the line with nothing but "I'm listening".
                     "landlord wont", "landlord won't", "landlords wont", "landlords won't",
                     "landlord refuses", "landlord refused", "landlord is refusing",
                     "landlord ignores", "landlord is ignoring", "landlord not fixing",
                     "landlord hasnt fixed", "landlord hasn't fixed", "landlord does nothing",
                     "letting agent wont", "letting agent won't", "letting agent ignores",
                     "withhold rent", "withholding rent", "rent arrears", "tenancy", "deposit",
                     "housing officer",
                     # A line asking what the law says, or whether it is legal, is a question about
                     # the landlord's duty: the scrub answers a question nobody asked, and main's
                     # hedge is the better of the two until a rights card takes it.
                     "the law", "law say", "law says", "legal", "legally", "am i allowed",
                     "is it legal", "obliged", "duty to")),
        # "Is it damp or is it condensation?" names both and asks for the difference, so neither
        # answer below fired and the line got "a plumber will spot it in minutes" (or, for "rising
        # damp or condensation", "either works, so take the one that's less fuss"). The difference is
        # what people actually want, and there is a test anyone can do at home in three days.
        entry("damp-or-condensation",
              (("damp", "damp patch", "damp wall", "damp walls", "rising damp"),
               ("condensation", "or condensation", "condensation or", "difference between",
                "which one", "what kind")),
              "Condensation is water out of the air landing on a cold surface: the windows and the outer "
              "corners are wet in the morning, it clears when the room is aired, and it comes back on "
              "cold days. A leak is a patch that grows and stays wet whatever the weather, and rising "
              "damp only runs along the bottom metre of a wall, usually with a tide mark. To tell them "
              "apart, dry a patch with a hairdryer, tape a square of cling film over it tight and leave "
              "it three days: water on the room side of the film is condensation, a wall still wet "
              "behind it is water coming through.",
              # A wet cloth, a damp cake and a damp tent are not a wall.
              avoid=("cloth", "cloths", "dishcloth", "washing", "laundry", "clothes", "towel",
                     "towels", "cake", "bread", "tent", "shed")),
        entry("condensation", (("condensation", "damp", "walls are wet", "wet walls", "walls get wet",
                                "windows are wet", "wet windows",
                                # The same complaint with the time of day in the middle of it: "the
                                # walls in my bedroom are wet in the morning" has every word but
                                # never them next to each other, so it fell to the listening reply.
                                "wet in the morning", "wet every morning", "wet each morning",
                                "wet in the mornings",
                                # the way people describe it out loud
                                "steaming up", "steamed up", "steamy", "condensating", "condensing",
                                "misting up", "misted up", "wet inside", "running with water",
                                # "fog" is the other word for it, and it reached no row that answers
                                # the inside of an ordinary window: "how do i stop my windows fogging
                                # up in winter", "my windows fog up in the morning" and "how do i stop
                                # windows fogging up" were all punts. Only the phrases are here and not
                                # the bare "fogging", so a line that names no pane still scores higher
                                # here than at the sealed-unit row.
                                "fogging up", "fogged up", "fog up", "fogs up",
                                "foggy windows", "windows fog", "window fog",
                                # The same water, frozen: "how do i stop frost on my windows" was a
                                # punt, and frost on the inside of a pane is condensation with the
                                # heating off, so it is this row's advice, not a weather forecast.
                                "frost on the windows", "frost on my windows", "frost on windows",
                                "frost on the inside", "frost inside", "frosty windows",
                                "frosted up", "windows are frosted", "windows frosted",
                                "ice on the inside", "ice on the windows", "ice inside the windows",
                                "ice on my windows"),
                               ("window", "windows", "walls", "wall", "bedroom", "stop", "inside",
                                "wet", "winter", "misty", "glass", "running down",
                                # the same water in a room that has no window named in the line:
                                # "my loft has condensation" and "the cupboard smells damp" fell
                                # to the listening reply, because the row wanted a pane or a wall
                                # and got only the word for the water.
                                # Only the places a pane or a wall is never named for: "room",
                                # "flat" and "ceiling" are in the damp-proofing and leak rows'
                                # lines ("how do i dry out a damp room" is the find-the-water
                                # answer) and adding them here took those turns.
                                "loft", "attic", "garage", "shed", "landing", "hall",
                                "hallway", "basement")),
              "Condensation comes from warm wet air hitting cold surfaces, so ventilate and keep the "
              "place a bit warmer: use the extractor fan, open a window for 10 minutes a day, dry "
              "clothes outside or in a vented dryer, and leave the heating on low rather than off and "
              "on. A dehumidifier helps in a bedroom that gets it badly.",
              # a house that mists up, not the things people look through: spectacles, a car and a
              # pan of boiling water are all different questions; a mirror has its own anti-fog trick
              avoid=("glasses", "spectacles", "goggles", "car", "cars", "van", "windscreen",
                     "motorbike", "helmet", "pot", "pan", "saucepan", "kettle", "cooker",
                     "mirror", "mirrors",
                     # A patch that climbs a wall is water coming through, not air landing on a cold
                     # surface: "the damp is spreading up the wall" was the mist-up answer because
                     # "wall" is one of the surfaces below and it scored on the same two words.
                     "spreading up", "spreading across", "up the wall", "up the walls",
                     # a sealed unit that fogs between the panes has lost its seal and the glass row
                     # below answers it: this entry is the room side of the glass
                     # "glazing" on its own is not here: the matcher reads it as the same stem as
                     # "glazed", so a bare "glazed" in the avoid shut out every single-glazed
                     # window - "how do i stop condensation on a single glazed window" was a punt
                     # while the same line with a plain "window" got the answer. The double-glazed
                     # phrases below still fence the units, and a line that says glazing without
                     # them has a failing seal word ("misted", "blown") and is the unit row's.
                     "double glazing", "double glazed", "double-glazed", "window pane",
                     "panes", "the pane", "between the panes", "sealed unit")),
        # A sealed double-glazed unit that mists up between the panes is not condensation on the
        # glass: the seal has gone and the argon and the desiccant with it. "my double glazing has
        # misted up inside" was answered with open a window and dry your washing, which cannot fix
        # it, and "what do i do about misted double glazing" was a shrug.
        entry("misted-double-glazing",
              # A bare "window" is here because a unit is usually described by the window it is in
              # ("the glass in my window is cloudy", "my window has misted up on the inside"). The
              # fog words are not bare, though: "fog" on its own means the inside of an ordinary
              # window as often as a blown unit, and "windows fogging up" and "why do my windows fog
              # up" were both told the seal had gone. Only the fog that is tied to the inside or the
              # space between the panes is this row's.
              (("misted", "misting", "misty", "mist", "misted up", "fogged up inside",
                "fogging up inside", "fogged up between", "fogging between",
                "condensation between", "cloudy", "gone cloudy", "hazy", "blown", "seal has failed",
                "seal failed", "seals have failed", "water between the panes", "wet between",
                "inside the glass", "inside the pane", "inside the panes"),
               ("double glazing", "double glazed", "double-glazed", "glazing", "window pane",
                "window panes", "the pane", "panes", "unit", "units", "window", "windows",
                "conservatory", "door", "doors", "sealed unit")),
              ("That is a failed seal, not condensation: the unit has taken in damp and the "
               "desiccant inside it is full, so no amount of ventilating, heating or a dehumidifier "
               "will clear it. The glass unit is replaced, not repaired - a glazier measures the unit "
               "and swaps it, and the frame and the handles stay, which is why it is a much smaller "
               "job than new windows, usually £80-£200 a pane fitted depending on size and glass. "
               "Some firms now drill and dry a misted unit in place for less; it works on a mild "
               "case, but a unit that has been cloudy for years is a swap. If the mist is on the room "
               "side of the glass and wipes off, that is ordinary condensation and the ventilating "
               "answer is the right one - check with a dry cloth first."),
              # a car windscreen, a bathroom mirror and a pair of spectacles are other rows, and so
              # is the condensation that wipes off the inside of an ordinary window
              # "glasses" is not in this list on purpose: the avoid words are matched loosely, so
              # "glasses" also catches "glass", and every line about the glass mists up. The
              # spectacles row does not need it here either - a pair of glasses naming no window
              # never reaches this entry.
              avoid=("spectacles", "goggles", "windscreen", "car", "cars", "van",
                     "motorbike", "helmet", "mirror", "mirrors", "kettle", "saucepan",
                     "steam", "shower", "bathroom",
                     # a window that fogs while the pans are on is steam on the glass, not a failed
                     # seal: "the windows fog up when i cook" was told the unit had taken in damp
                     "cook", "cooking", "cooked", "kitchen", "boiling", "boil", "pan", "pans",
                     "casserole", "oven", "washing", "drying clothes",
                     # A window that mists up every morning, or asking how to stop it, is the
                     # condensation question however the line is worded: "how do i stop my windows
                     # misting up" and "my bedroom window is always misted up" are not a quote for
                     # a new unit. The failed-seal answer is for mist that will not wipe off, so the
                     # words for the everyday job send those lines back to it.
                     "stop", "stops", "stopping", "prevent", "preventing", "wipe", "wipes",
                     "wiping", "morning", "mornings", "every morning", "always", "every day",
                     "every night", "each morning",
                     # the glass has to be a unit for this to be a failed seal: a single pane, a
                     # skylight and a car are other rows, and "my glasses mist up" is the
                     # spectacles one
                     "single glazed", "single glazing", "skylight", "velux"),
              bias=1),
        # A bare "how do i deal with damp" names no surface and no smell, so neither answer above
        # matched it and the line fell to the "someone qualified will spot it" fallback. Damp is a
        # cause to find, not a person to call, and the first move is the same whatever the room.
        entry("damp",
              (("damp", "damp patch", "damp patches", "damp wall", "damp walls", "damp corner",
                "damp in", "damp problem", "rising damp", "damp proof", "damp course"),
               ("deal", "get rid", "stop", "cure", "fix", "treat", "sort", "coming back", "keeps",
                "why", "how", "cause", "room", "house", "flat", "hallway", "corner", "wall",
                # "do i have rising damp", "what is rising damp", "is it serious": the same hunt for
                # the water answers all of them, and they reached the plumber fallback before.
                "have", "got", "real", "signs", "sign", "what", "mean", "means", "look", "looks",
                "like", "serious", "worry", "worried",
                # A bare "rising damp" names the subject and asks about it in two words, so the same
                # phrase in both parts is what lets the topic reach its own answer.
                "rising damp",
                # "my damp patch is getting bigger" asked the one thing this answer is for - has the
                # water found a way through - and got a shrug, because a patch that grows named none
                # of the verbs above.
                "getting worse", "getting bigger", "bigger", "growing", "spreading", "spread",
                "keeps coming back", "coming back", "returns", "returning")),
              # 110 words was more than twice the bar, and this is the answer for every damp room, so
              # it says the same thing in two moves: find the water, then dry it out.
              "Find the water before you treat the wall: a leaking gutter or downpipe, an overflow "
              "running, ground above the damp course, or a slow leak near the patch. Feel whether the "
              "wall is wet high up (a leak) or only at the bottom (rising damp). Warm it and ventilate "
              "it while you look, don't paint over it, and in a rented flat ask the landlord in "
              "writing.",
              # The cloth, the laundry and the cooking are all "damp" somewhere else, and a room that
              # is damp in winter, or wet round the windows, is the condensation answer below rather
              # than a gutter to go looking for.
              # The furniture is the smell entry's line: a wardrobe or a cupboard that smells damp is
              # about airing it and finding the cold wall behind it, and this answer's gutter, damp
              # course and survey are the outside of a house.
              avoid=("cloth", "cloths", "dishcloth", "washing", "laundry", "clothes", "towel",
                     "towels", "cake", "bread", "tent", "shed",
                     "condensation", "winter", "window", "windows", "bedroom", "steam",
                     "wardrobe", "wardrobes", "cupboard", "cupboards", "drawer", "drawers",
                     "closet", "suitcase", "mattress", "bedding", "sofa", "settee", "armchair",
                     # A car is the car's own diagnosis: "how do i get rid of a damp smell in the
                     # car" got the gutter hunt, and a wet carpet and a pollen filter are not a
                     # leaking gutter. A smell inside a room's own walls is not held out here: a
                     # damp-smelling room is this answer's line, and it is two moves long.
                     "car", "van", "boot", "camper")),
        # The place the smell is in is the key, not a bare "room": "how do i get rid of a musty smell
        # in a room" and "how do i stop my wardrobe smelling" both had an answer already waiting, and
        # the first was taken by the hotel-complaint row because "room" alone was the only word it
        # needed. The car keeps its own smell diagnosis: "my car smells damp" is a wet carpet and a
        # pollen filter, not a cold outside wall.
        # The key is the smell said with the damp: "damp" or "musty" in one group, the smell or the
        # place in the other. It is deliberately not widened to a bare "smell": a key of "smell" beside
        # any place word made this row the answer to "the garage smells" (the place-smell row's own
        # line), "my car smells of wet dog", "how do i make my house smell nice" and "the carpet smells
        # of wee" - four answers it took from rows that know the subject better.
        entry("damp-smell", (("damp", "musty", "mustiness", "mildew", "dampness", "damp and musty",
                              "musty and damp", "musty smell"),
                             ("smell", "smells", "smelling", "smelly", "whiff", "reek", "stinks",
                              "room", "house", "flat", "home", "bedroom", "living room", "spare room",
                              "sitting room", "dining room", "box room", "utility room", "en suite",
                              "wet room", "shower room", "wash room",
                              "loft", "attic", "basement", "cellar", "hallway", "landing", "stairs",
                              "wardrobe", "cupboard", "closet", "drawer", "mattress", "sofa", "settee",
                              "armchair", "carpet", "rug", "garage", "shed")),
              "A musty smell is usually damp rather than dirt: check for a leak or a cold outside wall, "
              "air the room properly and dry it out before covering anything up. Don't paint over damp "
              "patch, because it comes straight back.",
              # a room somebody is paying for is a complaint, not a damp job, and the avoid words
              # below say so by name. This row used bias=2 to outrank the hotel rows, and with the
              # key made narrower that bias only took "the room smells damp" off the hotel answer
              # the main deck expects, so it is gone.
              # a car, a towel and a machine each smell for their own reasons and have their own answers
              avoid=("hotel", "hotels", "hotel room", "guest house", "guesthouse", "bed and breakfast",
                     "b and b", "airbnb", "holiday let", "villa", "cottage", "reception",
                     "check in", "check out", "booking", "the room we booked",
                     "washing", "laundry", "clothes", "shirt", "shirts", "sheets", "towel", "towels",
                     "machine", "dryer", "car", "van", "boot", "fridge", "freezer", "oven", "bin",
                     "bins", "dustbin", "dishwasher", "sink", "drain", "plughole",
                     # every other smell has a subject of its own, and a bare "smell" in this key
                     # would take it: smoke, a pet, cooking, a shoe, a baby and a fuel each have
                     # their own answer, and a musty room is what is left.
                     "shoe", "shoes", "trainer", "trainers", "boots", "dog", "dogs", "cat", "cats",
                     "pet", "pets", "puppy", "puppies", "kitten", "kittens", "urine", "pee", "poo",
                     "sick", "vomit", "smoke", "smoking", "cigarette", "cigarettes", "cigar",
                     "fire", "burnt", "burning", "paint", "painting", "cooking", "curry", "fish",
                     "food", "garlic", "onion", "baby", "nappy", "nappies", "milk", "diesel",
                     "petrol", "exhaust", "fuel", "gas", "sewage", "chemical", "formaldehyde",
                     # what is *on* a soft thing is the soft-thing row's ("the carpet smells of
                     # wee" is the enzyme cleaner), but the soft things themselves are not stood down
                     # here: khaki-key measured that a musty sofa, rug or bathroom then reached no
                     # answer at all, because `soft-thing-smell` stands down for "musty" as well. So
                     # a musty soft thing keeps this answer as its fallback and only the smell that
                     # has a neighbour behind it stands this row down.
                     "wee", "wet patch",
                     # a wet room is the condensation rows' question, and a mould patch is the mould
                     # spray's: naming either is not asking what a musty room needs. The bathroom is
                     # not here - "musty smell in the bathroom" is a musty room, and the fixture
                     # words below are the ones with cards of their own.
                     "shower", "tiles", "grout", "toilet", "loo", "condensation",
                     "mould", "mold", "mouldy", "moldy", "damp patch", "rising damp",
                     "damp course", "landlord", "council", "letting agent", "environmental health",
                     # and the opposite question - making a room smell nicer - was the ventilate
                     # card before this row took it: "how do i make my house smell nice"
                     "nice", "nicer", "good", "better", "fresh", "fresher", "lovely", "pleasant",
                     "smell nice", "smells nice", "smell good", "smells good", "smell fresh",
                     "smells fresh", "smell better", "smells better", "smell lovely")),
        entry("roof-leak",
              # water arriving through the roof or the loft is the one home job where the next hour
              # matters, so it gets its own entry: the ceiling patch above is about a stain that may
              # be weeks old, and this is about the rain that is coming in now.
              (("roof", "roofs", "loft", "attic", "ceiling", "tiles", "slates", "roof tiles",
                "flat roof", "roof space", "chimney", "light fitting", "ceiling light", "lights",
                "landing", "hallway"),
               ("leaking", "leak", "leaks", "coming in", "coming through", "pouring", "dripping",
                "water", "rain", "raining", "wet", "soaked", "damp coming", "buckets",
                "go up", "get up", "getting up there", "get on the roof", "climb", "ladder", "safe",
                "storm", "blew off", "blown off", "missing tiles", "damaged", "tarp", "tarpaulin",
                # a ceiling that is bulging or sagging is water that is already there and heavy:
                # that is a stay-out-of-the-room answer, not the stain one
                "bulging", "sagging", "bowed", "belly")),
              _roof_leak,
              avoid=("boiler", "radiator", "washing machine", "dishwasher", "tap", "taps", "faucet",
                     "toilet", "sink", "shower", "bath", "overflow", "drain", "drains", "gutter",
                     "gutters", "downpipe", "window", "windows", "condensation", "mould", "mold",
                     "musty", "car", "van", "boat", "tent", "sofa", "roof box", "moss", "caravan",
                     # "tiles" and "damaged" are too thin on their own: a damaged bathroom tile or a
                     # kitchen floor is a tiling job, not rain coming in
                     "bathroom", "kitchen", "wall", "walls", "floor", "floors", "grout",
                     "grouting",
                     # A stain is history, not rain that is coming in now: "water stain on the
                     # ceiling" was told to cut the power and get a roofer out the same day, which is
                     # the answer for a live leak. The mark a leak left keeps damp-patch-ceiling,
                     # which says to find where it comes in; the drip keeps this one.
                     "dried", "drying out", "old"),
              guard=_a_mark_that_is_live),
        entry("damp-patch-ceiling",
              # the ceiling first: "damp" on its own is the condensation answer, and a patch that
              # spreads on a ceiling is water coming through, not warm air meeting a cold wall
              (("ceiling", "ceilings", "plaster", "paint", "skirting"),
               ("damp", "patch", "wet", "brown", "yellow", "stain", "stains", "dripping", "peeling",
                "water coming", "coming through", "blistering",
                # a dried "water mark" on a ceiling is the same old patch, and it had no row at all
                "mark", "marks", "water mark", "water marks")),
              "A brown or yellow patch on a ceiling is water, and the first job is to find where it "
              "comes in rather than paint over it. Look at what is above: a bathroom or a radiator "
              "pipe means a leak at the sealant, the trap or the joint, and an outside wall or the "
              "roof means it only grows after rain, so note whether it does. Press it with a finger - "
              "soft, crumbly plaster or a slow drip means it is live and worth turning the water off; "
              "a hard dry ring that has not moved in weeks is an old stain, which you seal with a "
              "stain block and then paint. Photograph it with the date and tell the landlord or your "
              "insurer in writing, because a patch painted over with no record is one you cannot "
              "claim for.",
              avoid=("mould", "mold", "mildew", "smell", "musty", "condensation", "window", "windows",
                     "steam", "damp proof", "rising damp", "basement", "cellar floor",
                     # a stained or painted fence is the fence's question: "should i paint or stain
                     # my fence" was told about a brown patch on a ceiling
                     "fence", "fences", "shed", "decking", "gate", "patio")),

        # --- broken glass ------------------------------------------------------
        # "a pane of glass got broken" was answered "Rotten luck.", "my window pane is cracked"
        # was "Got it. Is there anything you'd like a hand with?" and both "can i replace a broken
        # window pane myself" and "how much does it cost to replace a window pane" got the shrug,
        # so a broken window had no answer at all on main `a2dbea5`.
        entry("broken-window",
              # The window or the glass in it is one group, and what is wrong with it is the other, so
              # "a pane of glass got broken", "my window pane is cracked" and "the glass in my front
              # door is cracked" are all one question. A break word has to be there: "my window glass
              # is streaky" and "how do i stop the draught" are other answers.
              (("window", "windows", "pane", "panes", "pane of glass", "glass", "double glazed",
                "sealed unit", "glazing"),
               ("broken", "broke", "broken glass", "cracked", "crack", "cracks", "cracking", "smashed",
                "shattered", "shatters", "came out", "come out", "fell out", "blown", "gone",
                "replace", "replacing", "repair", "repairing", "fix", "fixing", "cost", "costs",
                "how much", "myself", "diy", "glazier", "board up", "make safe", "what do i do",
                "who do i call", "quote", "reglaze", "reseal", "putty")),
              _broken_window,
              # A car windscreen, a drinking glass, a mirror, a phone screen, the oven door and a pair
              # of spectacles are all their own question and none of them is a window: "my car
              # windscreen is scratched" must not get a glazier's quote, and "my glasses broke" is the
              # optician's answer.
              # A window word has to be there as well, because "glass" on its own is usually
              # something you drink out of or eat off: "how much sugar is in a glass of apple juice",
              # "how much caffeine in a glass of coke" and "what should i do with a cracked glass"
              # all took a glazier's quote (sleek-skunk, #3207).
              ask=("window", "windows", "pane", "panes", "double glazed", "double-glazing",
                   "sealed unit", "glazing", "front door", "back door", "patio door", "sash",
                   "window frame", "french door"),
              avoid=("windscreen", "windshield", "car", "cars", "van", "drinking glass",
                     # what is in the glass, and what a cracked one in the hand wants
                     "juice", "sugar", "caffeine", "calorie", "calories", "coke", "cola", "wine",
                     "beer", "water", "milk", "drink", "drinking", "drank", "pint", "whisky",
                     "whiskey", "gin", "vodka", "tea", "coffee", "glass of", "tumbler", "mug",
                     "wrap it", "bin it", "cut myself", "in my hand", "in the sink", "washer",
                     # "glasses" cannot go here: it is a loose form of "glass", so "a pane of glass"
                     # read as a pair of spectacles and the entry scored nothing at all.
                     "spectacles", "optician", "mirror", "phone", "screen", "shower screen", "shower",
                     "oven", "hob", "cooker", "stove", "log burner", "splashback", "picture",
                     "tv", "telly", "watch", "table", "fish tank", "aquarium", "shelf", "cupboard",
                     # the window that is not broken
                     "draught", "draft", "condensation", "steam", "mould", "mold", "streaky",
                     # A pane that has gone cloudy has lost its seal, not its glass: "what do i do
                     # about misted double glazing" was told to sweep up the glass and tape a bin
                     # bag over the hole. The unit row owns the seal words.
                     "misted", "misting", "misty", "mist", "cloudy", "hazy", "fogged", "fogging",
                     "smear", "smears", "clean", "cleaning", "paint", "painting", "handle", "hinge",
                     "catch", "lock", "latch", "blind", "curtain", "insulation", "double glazing quote",
                     "how much do double glazing", "windows are wet",
                     # and the window that is jammed rather than broken: "how do i fix a sticking
                     # window" carried "window" + "fix" and was answered with a glazier's quote for a
                     # smashed pane, which is the row below
                     "sticking", "sticks", "stuck", "jammed", "jams", "painted shut", "swollen",
                     "swelled", "hard to open", "hard to close", "wont open", "won't open",
                     "wont shut", "won't shut", "wont close", "won't close", "rubs", "dragging"),
              bias=1),
        # --- drains and water ---------------------------------------------------
        # "how much to fix a blocked sink" reached the brick-quantity row, because the car row had
        # stood down on "sink" and "blocked" and the bricks were keyed by "block": a blocked sink
        # is the plunger and the trap, so this row takes the tie.
        # "clog" is the other word for the same fault, and it was the one nobody had: "how do i
        # unclog a sink" was answered with the wipe-the-bowl card, "my sink is clogged" with a
        # nod ("Right. What have you tried so far?"), and "how do i clear a clogged drain" with
        # the once-a-week maintenance card. All three are the plunger and the trap.
        entry("sink-blocked", ("sink", ("blocked", "blockage", "slow", "draining", "drain", "water",
                                         "unblock", "unblocking", "plunger",
                                         "clog", "clogs", "clogged", "clogging", "clogged up",
                                         "unclog", "unclogging", "unclogged")),
              "Start with a plunger over the plughole with a little water in the bowl, then undo the "
              "trap underneath (bucket first) and pull the gunk out. A kettle of hot water with a "
              "spoonful of bicarbonate and vinegar clears the rest; chemical drain cleaner is the last "
              "resort, not the first.",
              # Water that has arrived is a leak, and water that will not leave is a blockage: the
              # same sink and the same word for water, opposite jobs. "theres water under the sink"
              # and "water under the kitchen sink" were both told to reach for the plunger, which
              # fixes nothing on a floor that is wet.
              avoid=("under the sink", "under my sink", "behind the sink", "underneath",
                     "under the unit", "under the cupboard",
                     "wet patch", "damp patch", "puddle", "puddles", "leak", "leaks", "leaking",
                     "dripping", "flood", "flooded", "soaked", "ceiling"),
              bias=1),
        # "loo" and "bog" are the same toilet, and "my loo is blocked" was only a warm
        # acknowledgement because "toilet" was the only name in the key.
        entry("toilet-blocked", (("toilet", "loo", "bog"), ("blocked", "blockage", "unblock", "flush",
                                                           "overflow", "overflowing", "plunger",
                                                           # "how do i unclog a toilet" was read
                                                           # as a blocked bowel and answered with
                                                           # fibre and a walk, which is the wrong
                                                           # end of the same word
                                                           "clog", "clogs", "clogged", "clogging",
                                                           "clogged up", "unclog", "unclogging",
                                                           "unclogged")),
              "Use a plunger with a good seal, and pour a bucket of water in from waist height rather "
              "than flushing again. If the water is rising, turn off the stopcock or lift the ball "
              "valve so it can't overflow, and never pour chemical cleaner into a blocked toilet.",
              bias=2,
              # a cistern that keeps filling after a flush is the running-toilet entry, not a blockage
              avoid=("wont stop", "won't stop", "keeps running", "stop running", "running", "runs",
                     "keeps filling", "trickling", "trickle", "hissing", "keeps topping",
                     "after flushing",
                     # "how much water does a toilet use per flush" is the litres question, and the
                     # bare word "flush" in this key was answering it with a plunger: water-use has
                     # the figure, so an amount of water stands this row down.
                     "how much water", "much water", "litres", "litre", "water use", "per flush",
                     # "after flushing" is the running-cistern tell, above; a bare "flush" stays
                     # here, because a blockage said with a flush is still a blockage - "can i
                     # flush a blocked toilet" and "a nappy has been flushed down the toilet" are
                     # both a plunger job, and standing this row down for the may-it-go question
                     # left them with a nod and no advice. The other sense is settled on the other
                     # row instead: the what-may-go-down list outranks this one on a thing flushed.
                     )),
        # "how do i stop X banging" was a haircut when X was a shutter or a loo seat, a cleaning card
        # when X was a blind, and a shrug when X was a chimney. A rattle is one job with one method,
        # so it is one row: find the part with play in it, then take the play out.
        entry("rattle-stop",
              (("shutter", "shutters", "blind", "blinds", "loo seat", "toilet seat", "window",
                "windows", "pipe", "pipes", "chimney", "flue", "gate", "gates", "fence", "fences",
                "panel", "panels", "vent", "grille"),
               ("banging", "bang", "bangs", "rattling", "rattle", "rattles", "clattering", "knocking",
                "flapping", "vibrating", "buzzing", "humming", "noisy", "noise")),
              "A bang is a part with play in it, so press and shake each end to find what moves before "
              "you buy anything. A loo seat bangs because the rubber bumpers under it have gone hard: "
              "tighten the two bolts through the hinges and fit new bumpers, which cost a couple of "
              "pounds. A blind bangs on the wall or the window when the bottom rail has nothing to "
              "rest against, so shorten the pull cord onto a cleat. A shutter or a gate in the wind "
              "wants a hook and eye or a magnetic catch holding it open. Banging in a chimney is birds "
              "or a flue that has no cowl on top, a banging pipe is water hammer, which wants the "
              "clips tightened and a clip or two more, and a fence or a gate that rattles in the "
              "wind wants the post fixing or a second bolt through the hinge.",
              # the cleaning, the bleeding, the sweeping and the draught answers are their own rows
              avoid=("clean", "cleaning", "wash", "washing", "dust", "dusty", "mould", "damp",
                     "bleed", "bleeding", "cold", "boiler", "sweep", "sweeping",
                     "draught", "draft", "slam", "slamming", "shut", "open", "broken", "cracked",
                     "won't close", "wont close")),
        # A rail is the fitting a household puts up themselves and asks about most, and nothing
        # answered it: "how do i put up a curtain rail" was a punt, while the curtain rows in the
        # cleaning table are about washing one.
        entry("curtain-rail",
              (("curtain rail", "curtain pole", "curtain rod", "curtain track", "rail", "pole"),
               ("put up", "hang", "hanging", "fit", "fitting", "fitted", "install", "fix",
                "how high", "what height", "drill", "bracket", "brackets", "level",
                # A rail that has already come down is the same two fixing points as a rail going
                # up, and it was answered with "A pencil rubber takes most scuffs off a matt
                # emulsion" (the wall-mark card, through "wall" + "off") and with "Blot, do not
                # rub" (a stain card, through "pulled out"). The words a person uses for the rail
                # coming away are the question.
                "coming off", "came off", "come off", "keeps coming off", "coming away",
                "came away", "pulled out", "pulling out", "ripped out", "torn out", "fallen",
                "fell", "fell down", "falling down", "came down", "come down", "sagging",
                "dropping", "loose", "wobbly", "won't stay", "wont stay", "not holding",
                "what fixing", "what fixings", "rawl plug", "rawlplug", "hollow wall")),
              "Mark both ends before you drill: the rail sits 10 to 15cm above the window recess and "
              "15 to 20cm past each side, so the curtains clear the glass, and check it with a spirit "
              "level because a rail two people can see is crooked. Fix into masonry or a timber stud "
              "rather than the plasterboard alone - a rail hangs all its weight on two points and "
              "pulls downwards - so find the studs with a magnet dragged along the wall, which sticks "
              "at the screw heads, or drill and use a masonry plug. Hang the curtains on the rail "
              "before it goes up, and use the last eyelet at each end.",
              # ironing or washing a curtain, a shower curtain and a rail for a towel or a coat are
              # other answers. "fallen"/"fell"/"came down" used to be fenced here too, on the guess
              # that a rail that came down was somebody else's card; it was nobody's, and the two
              # lines that say it were told how to rub a scuff off emulsion and how to blot a stain.
              avoid=("iron", "wash", "washing", "clean", "shower",
                     "broken", "tv", "television", "picture", "shelf", "coat", "towel")),
        # A window curtain that will not slide is its own job: the rod, the rings and the gliders, not
        # the liner in a shower. `shower-curtain-clinging` is the shower's row, and the two sit next to
        # each other because people use one word for both.
        entry("curtains-drag",
              (("curtain", "curtains"),
               ("sticking", "sticks", "stick", "dragging", "drag", "stiff", "jerky", "scraping",
                "wont slide", "won t slide", "wont pull", "won t pull", "hard to pull",
                "hard to open", "hard to close", "squeaking", "squeak")),
              "Rub the rod with a candle end or furniture wax, or spray it with silicone, and the rings "
              "will run again: the squeak is the rod and the ring, not the fabric. Plastic gliders go "
              "chalky and grip after a few years, so replace them, and check the brackets are not "
              "sagging in the middle, which pinches the two curtains against each other. A track gets "
              "the same treatment plus a vacuum along the slot, because fluff in the runners does most "
              "of the sticking.",
              avoid=("shower", "bath", "liner", "iron", "ironing", "wash", "washing", "clean",
                     "cleaning", "mould", "mold", "fade", "fading", "blackout", "put up", "hang",
                     "hanging", "fit", "fitting", "fallen", "fell", "came down", "buy", "length",
                     "shorten", "hem", "sew", "sewing", "blinds"),
              # the shower row beside it holds "curtain sticks" as a phrase and a bias, so a bare
              # "my curtains sticking" reached the shower first; a window curtain on a rod is the
              # commoner reading of the bare plural, so this row is the tie-break
              bias=2),
        # "leaky" is the adjective people use and it is not a form of "leak", so "how do i fix a
        # leaky tap" scored 2 on the tap alone and went to the hedge.
        entry("tap-drip", (("tap", "faucet"), ("drip", "drips", "dripping", "leak", "leaks", "leaky",
                                              "leaking", "washer")),
              _a_dripping_tap),
        # A bare "do i need a new washer" has two subjects and no way to tell them apart, so the
        # answer to both is short: the ring in a tap, or the machine. Every row that owns one of
        # them reads its own words beside the washer, and this one only the washer alone.
        entry("a-washer-two-things",
              (("washer", "washers"),
               ("new", "need", "needs", "replace", "replacing", "change", "changing", "fit",
                "fits", "size", "what size", "which size", "right size",
                # telling you they have one is the same question with half the answer given
                "have", "has", "got", "ive", "i've", "bought", "buy", "buying", "should",
                "which")),
              _a_washer_two_things,
              guard=_a_washer_with_no_other_subject,
              bias=-1),
        # The cistern that never stops filling is the most common plumbing fault in a house, and
        # main answered it with "Got it. Is there anything you'd like a hand with?". The tell is
        # where the water goes, so the answer asks the person to take the lid off and look.
        entry("toilet-running",
              # "the flush button is stuck" names no toilet at all, and the cistern's own parts
              # are the subject when the part is what has gone wrong
              # the words people use for it, in one place: "the lav keeps running" reached
              # nothing, and a toilet is a loo, a lav and a wc before it is ever a cistern
              (("toilet", "loo", "loos", "lav", "lavatory", "wc", "bog", "cistern", "pan",
                "flush button", "flush", "flushes",
                "ball valve", "ballcock", "fill valve", "flush valve", "float valve", "float"),
               ("running", "runs", "keeps running", "wont stop", "wont stop running", "stop running",
                "keeps filling", "filling", "trickling", "trickle", "constantly", "all the time",
                "hissing", "keeps topping", "stuck", "jammed", "wont go down", "wont push",
                "broken", "gone", "seized", "worn")),
              "Turn the water off at the isolation valve under the cistern, take the lid off and "
              "watch where it goes. Trickling down the back of the pan means the flush valve is not "
              "seating: feel the rubber seal for grit, and a new flapper is a couple of pounds and "
              "clips straight on. Water into the overflow or up the side means the fill valve is too "
              "high or its float has gone, so screw the level down and replace the valve if that does "
              "not stop it. A button that stays down or does nothing is the button or the syphon "
              "under it, and those are a few pounds at a hardware shop and clip in without any "
              "plumbing.",
              avoid=("blocked", "blockage", "overflowing", "smell", "clean", "cleaning", "stain",
                     "limescale ring", "brush",
                     # the hot flush is a symptom and the sweats are another card entirely
                     "hot flush", "hot flushes", "flushes at night", "sweats", "menopause",
                     "perimenopause",
                     # "i need the loo all the time" is a symptom, not a cistern: the body's line is
                     # health's uti card, so the loo that is needed rather than running is not here
                     "need the loo", "need a loo", "needing the loo", "need to loo",
                     "need the toilet", "needing the toilet", "keep needing",
                     ),
              # ... and the going half of it: "i keep running to the loo" has both words of this
              # row's key in it, and it is the runs, not the flush valve
              guard=_going_to_the_loo),
        # A toilet that leaks is not the cistern that will not stop filling: the tell is where the
        # water comes out, so this asks for that. It was reaching the constipation answer in health.py,
        # because "toilet" and "fix" were both in its key.
        entry("toilet-leak",
              (("toilet", "loo", "loos", "lav", "lavatory", "wc", "cistern", "pan", "bog"),
               ("leak", "leaks", "leaking", "leaky", "drip", "drips", "dripping", "pool", "puddle",
                "puddles", "floor", "seal", "seals", "joint", "joints", "fix", "repair", "water",
                "wet")),
              "Where the water shows tells you which seal has gone. Water on the floor at the base "
              "means the wax or rubber seal between the pan and the soil pipe - the pan has to come "
              "up, so an hour of a plumber's time. A trickle from under the cistern is the inlet "
              "connection or the coupling washer, a quarter turn with a spanner. Water in the bowl "
              "that will not stop is the flush valve. Turn the water off at the isolation valve "
              "beside the cistern first, dry everything, and watch again - and if you rent, tell the "
              "landlord in writing rather than taking the pan off yourself.",
              # a question about the colour or the smell of the water is not a leak
              avoid=("blocked", "blockage", "unblock", "plunger", "smell", "smells", "smelly", "clean",
                     "cleaning", "stain", "stains", "limescale", "brush", "brown", "brownish", "rusty",
                     "yellow", "yellowish", "green", "cloudy", "murky", "discoloured", "black",
                     "colour", "color", "taste", "tastes", "drink", "drinking", "constipated",
                     "constipation")),
        entry("tap-pressure-low",
              (("tap", "taps", "faucet", "shower", "showers", "shower head", "water"),
               ("low pressure", "no pressure", "pressure is low", "pressure has dropped", "weak",
                "weedy", "trickle", "trickling", "barely", "hardly", "dribble", "slow flow",
                # "the shower pressure is rubbish" and "the pressure is poor" are the same
                # complaint without the word low, and they were the shrug: the key wanted
                # "low pressure" and "pressure is low", never the bare noun beside a rating.
                "pressure", "rubbish", "poor", "useless", "hardly any", "no force")),
              _pressure_weak,
              # the gauge on a boiler has its own answer, and a car tyre is not a tap
              avoid=("boiler pressure", "boiler", "radiator", "tyre", "car", "blood", "oil pressure",
                     "pressure washer", "gas",
                     # drinking is not plumbing: the first arm carries the word "water", and with
                     # "barely" and "weak" in the second, "i drink barely any water" and "i hardly
                     # drink any water" were told to unscrew the aerator on the tap. A water bill
                     # and a watering can are other questions too.
                     "drink", "drinking", "drank", "thirsty", "hydrate", "hydrated", "dehydrated",
                     "bill", "bills", "water the", "cuppa", "brew")),
        # A tap that gives no water had no row at all: "the tap is not working", "the kitchen
        # tap doesnt work" and "the bathroom tap is not working" were the shrug, and before the
        # fence on `card-on-a-phone` they were told to check the phone's screen and its case. The
        # row is the tap itself, so a shower, a loo and a machine keep their own answers.
        entry("tap-no-water",
              # "water" belongs with the thing and not with the fault: the scorer wants two
              # signals from two key groups, and with water on the fault side a line that says
              # "the tap has no water" is one group twice - which is why it was a shrug.
              (("tap", "taps", "faucet", "faucets", "mixer tap", "kitchen tap", "bathroom tap",
                "hot tap", "cold tap", "the water", "water supply", "water"),
               ("not working", "doesnt work", "doesn't work", "stopped working", "no water", "none coming", "nothing comes out", "nothing coming", "wont run",
                "won't run", "wont come on", "wont turn on", "won't turn on", "cant turn on",
                "no flow", "stopped", "stops", "spits", "sputters", "splutters", "airlock",
                "dry", "dry tap", "barely", "suddenly")),
              "If it is one tap and the rest of the house runs, it is that tap's own supply: the "
              "isolation valve on the pipe under the sink is a slot-head screw, and a half turn the "
              "other way is the usual answer. With the valve open, unscrew the spout aerator and "
              "soak it in vinegar - a scaled-up aerator stops a tap dead. If every tap is dry, it is "
              "the stopcock where the mains comes in, or the supply itself, so check the water "
              "company's postcode status before you pay anyone. A tap that runs and then stops is an "
              "airlock: hold your palm over the spout and open it fully for a few seconds, or "
              "back-fill it with a jug from another tap. And if the pipe is in a cold wall in "
              "freezing weather, warm it gently with a hairdryer - never a blowtorch - with the tap "
              "left open.",
              # the other tap rows answer their own complaint, and a shower, a loo, a machine and a
              # boiler are separate faults with separate answers
              avoid=("drip", "drips", "dripping", "leak", "leaks", "leaking", "washer",
                     "pressure", "low pressure", "weak", "trickle", "limescale", "scale",
                     "shower", "showers", "loo", "toilet", "cistern", "boiler", "radiator",
                     "radiators", "washing machine", "dishwasher", "immersion", "cylinder",
                     "hot water", "cold water", "drink", "drinking", "water bill", "meter",
                     # "watering" is not here: the avoid list matches stems, so it also
                     # matched "water" and a dry tap was a shrug all over again
                     "outside tap", "garden tap", "hosepipe", "hose",
                     # "the tap to pay doesnt work" is the phone, not the plumbing: the phrase
                     # names the payment before it names the tap
                     "tap to pay", "tap and pay", "to pay", "apple pay", "google pay",
                     "contactless", "card machine", "phone", "wallet", "debit card",
                     "credit card", "bank card",
                     # a tap that is dry is this row; what the water in it is like is the water
                     # rows' question, and every one of those says "tap water" - safe, cloudy,
                     # hard, where it comes from, why it smells - so the phrase alone separates
                     # them, and the tap has to name a fault to reach this row at all
                     "tap water")),
        entry("limescale", (("kettle", "limescale", "scale", "tap", "shower head", "showerhead"),
                            ("descale", "clean", "white", "fur", "build", "rid", "remove",
                             "blocked", "blocking",
                             # "clogged" is how a scaled-up head or tap is described, and it was in
                             # no part of this row: "the shower head is clogged with limescale" was
                             # a shrug
                             "clogged", "clogging", "spray", "holes", "weak",
                             # the remedy is asked for as an ask, and none of the words above is
                             # in "what can i do about limescale": the row was not reached at all
                             # (the water softener's fault row keys "still limescale", so the bare
                             # word named two rows and the one-word retry withheld it), and the
                             # everyday remedy line went to a search hedge (#6283). A remedy row
                             # answers "what can i do about X" in its own right.
                             "what can i do", "do about", "what can i use", "anything for",
                             "anything to", "how do i stop", "how to stop", "keeps coming",
                             "coming back", "comes back", "get it off", "get rid of it",
                             # the same ask in the other words people use for it: main keys the
                             # first list, and these are what was missing from it
                             "what do i do", "what should i do", "deal with", "get rid",
                             "anything i can do", "do about it", "cope with")),
              "Soak the scaled part in half water, half white vinegar, or a spoonful of citric acid in "
              "water: boil it in the kettle and leave it an hour, or tie a bag of it round a shower "
              "head or tap for an hour. Rinse twice afterwards, and do it again whenever it furs up.",
              # The ask words above are general, so they pair with any subject this row carries,
              # and the tap is one: "what can i do about my dripping tap" and "... leaking tap"
              # got a vinegar soak for a worn washer (#7242 review). Dripping, leaking, a washer
              # and the water-pressure words are the plumbing rows' whatever else the line says.
              # The kettle has its own rows and they say more, so it stands down for those too.
              avoid=("drip", "drips", "dripping", "dripped", "leak", "leaks", "leaking", "leaked",
                     "washer", "washers", "cartridge", "cartridges", "plumber", "valve",
                     "no hot water", "water pressure", "blocked drain", "drains",
                     "kettle", "kettles", "boiler", "boilers", "steam iron", "washing machine",
                     "dishwasher", "coffee machine",
                     # "scale" means scale insects in a garden, and "what can i do about the
                     # scale on my plants" was a vinegar soak for them (@steward-maroon-mink,
                     # #7242). Anything growing stands this row down.
                     "plant", "plants", "garden", "gardening", "insects", "aphids", "leaves",
                     "leaf", "soil", "compost", "lawn", "houseplant", "houseplants",
                     "orchid", "orchids", "fern", "fern fronds")),
        # "why does my kettle get limescale" and "my kettle is scaled up" are asks about the cause,
        # and no key carried "why" or "get", so they were answered with a shrug. This entry is keyed
        # on the scale itself rather than on the remedy, so the cause leads and the descale follows.
        # The kettle has its own answer now (descale-kettle, #820), so it is left out of here: this
        # is the cause for the rest of the scale in a house - taps, the shower head, an iron, stains.
        entry("limescale-why", (("limescale", "scale", "scaled", "scaling", "fur",
                                 "furred", "furry", "white stuff", "white marks", "chalky marks",
                                 "chalky", "hard water",
                                 # the sentence people actually write: "my water is hard and
                                 # leaves marks" had no row at all, because "hard water" is not in it
                                 "water is hard", "water hard", "water is so hard",
                                 "water is very hard", "water tastes hard",
                                # the tap wording without the scale word: "hard water stains on the
                                # taps" is the same question, and the cleaning row hands it on
                                "hard water stain", "hard water stains"),
                                ("tap", "taps", "shower", "shower head", "showerhead",
                                 "iron", "steam iron", "washing machine", "dishwasher", "water",
                                 # "how do i prevent limescale" asks how to keep it away, and the
                                 # remedy card only says how to soak it off; this row ends with
                                 # the filter jug and the scale reducer that cut down how often
                                 # it comes back. "stop" is not here: the remedy card already
                                 # answers "how do i stop limescale".
                                 "prevent")),
              ("Hard water is the reason: it carries dissolved calcium and magnesium, and they are "
               "left behind as a chalky scale whenever the water boils away or dries on a surface. "
               "Soak the scaled part in half water, half white vinegar, or a spoonful of citric acid "
               "in water - boil it in the kettle and leave it an hour, or tie a bag of it round a "
               "shower head or tap for an hour - then rinse twice. A filter jug or a scale reducer "
               "cuts down how often it comes back."),
              # "kettling" is a form of "kettle" as far as the matcher is concerned, so naming it
              # here turned the kettle lines off; the boiler's own entry wins on specificity.
              # Water on hair is a different question with a different answer (a chelating shampoo),
              # and scale on a kettle says nothing about it, so the hair lines keep whatever they had.
              # A question about whether the hardness is bad for a person is not a question about
              # the scale: "is hard water bad for you" was this row's descaling recipe, and the
              # health half is `drinks.hard-water`.
              avoid=("kettle", "kettles", "boiler", "heating", "radiator", "radiators", "fish", "skin",
                     "weigh", "weight", "muscle", "diet", "recipe", "flour", "sugar",
                     "hair", "shampoo", "conditioner", "scalp",
                     "bad for you", "bad for me", "good for you", "safe to drink", "is it safe",
                     "harmful", "dangerous", "kidney", "kidneys", "drink it", "drinking",
                     "health", "healthy", "formula", "baby", "babies", "softener")),
        # Brown marks in a bathroom are iron, not the calcium the scale answer is about, and the leak
        # answer had them until the leak row stood down for the rust words: "how do i get rid of rust
        # stains off the shower" was told to look for a damp patch under the tray. Iron stains are
        # lifted by the same acid and made permanent by the same bleach, so they get their own row
        # rather than a sentence the white-scale lines would have to carry too. The kitchen tools keep
        # their own rust answer, and a rusty bike, nail or gate is none of these words.
        entry("rust-marks",
              (("rust", "rusty", "rusted", "rust stain", "rust stains", "rust marks"),
               # the surfaces the iron sits on, and no word for the wash: "my washing machine has
               # rust marks" is the drum and the seal, and "rust stains on my white shirt" is a stain
               # on a garment. A reviewer found the bathroom card taking both.
               # "tiles" is spelled by "tile" through the word forms, and the bare plural here scored
               # the same point as the grout row on "how do i clean the grout between my tiles"
               # "tile" and "grout" are not here: a key word is counted for rarity across every
               # row, and naming them in this surface group made "grout" common enough that the
               # grout answer lost "how do i whiten grout in the shower" to the leak row. Rust on a
               # joint is still reached by "shower" or "bathroom" in the same line.
               ("shower", "bath", "sink", "basin", "toilet", "glass",
                "screen", "bathroom", "plughole", "plug hole", "patio", "paving", "paving slabs",
                "drive")),
              ("Brown marks are iron rather than the calcium of scale, from a steel screw or fitting, "
               "a chip in the enamel, or iron in the water, and the acid that lifts scale lifts rust "
               "too: white vinegar or a citric acid paste, left ten minutes and rinsed. Never bleach, "
               "because it sets rust into the surface, and never wire wool, which leaves specks of "
               "steel behind to rust again. If it keeps coming back, find the steel that stays wet - "
               "a screw, a shower rose, the frame of the screen - and dry it or replace it."),
              # a rusty baking tray, a rusty bike and a rusty gate are other answers
              avoid=("tray", "trays", "tin", "tins", "knife", "knives", "cutlery", "pan", "pans",
                     "bike", "bicycle", "chain", "car", "van", "gate", "nail", "nails", "screwdriver",
                     "tools", "tool", "garden furniture", "barbecue", "bbq",
                     "washing machine", "washer", "drum", "seal", "laundry", "clothes", "shirt",
                     "shirts", "fabric", "whites", "white shirt")),

        # How long a kettle takes is a different question from what is wrong with one, and nothing
        # answered it: "how long does a kettle take to boil" was a shrug, and "why does my kettle
        # take so long" a shrug too. Two entries, because the first wants a number and the second
        # wants a cause, and the words that belong to the descale and running-cost answers are in
        # both avoids so those lines keep the answer they had.
        entry("kettle-boil-time",
              (("kettle", "kettles"),
               ("how long", "long does", "minutes", "take", "takes", "time", "quick",
                "quickly", "fast", "how many")),
              "About 45 seconds for one mug and around 3 minutes for a full 1.7-litre kettle in a 3kW "
              "one, so boiling only what you are going to drink is both quicker and cheaper. A 2kW "
              "kettle takes roughly half as long again.",
              ask=("how long", "minutes", "take", "takes", "time", "quick", "quickly", "fast",
                   "how many"),
              # "kettling" is a loose form of "kettle" to the matcher (see limescale-why), so the
              # boiler's noise word cannot be named here; "boiler" and "noise" are enough.
              # a kettle's *life* is the appliance-life row: "how long does a kettle last" says
              # "how long" and names a kettle, so without these words this row took it and answered
              # with boiling times. "last" in the sense of duration of boiling ("how long does it
              # last once boiled") has no kettle word, so nothing good is lost here.
              avoid=("last", "lasts", "lasting", "lifespan", "life span", "life expectancy", "years",
                     "descale", "descaleing", "limescale", "scale", "scaled", "fur", "furred",
                     "noise", "noisy", "boiler", "heating", "cost", "costs",
                     "pence", "electricity", "energy", "bill", "cheaper", "leak", "leaking",
                     "broken", "not working", "switch", "element", "fill", "capacity",
                     # how long one lasts, and whether to replace it, is the appliance-life
                     # question rather than a filling one. Main already stands "last" and "years"
                     # down here; the branch's extra words are merged in beside them.
                     "lifetime", "life", "replace", "replacement", "new kettle", "worth it",
                     "how long do they", "how long should", "keep going", "buy") + JOB_GUARD,
              # the "how many minutes" cooking follow-up entry scores the same as this one on the
              # line, and it won the tie: a named appliance outranks it.
              bias=2),
        # A kettle that smells is a different fault from one that is slow: "why does my kettle smell"
        # was a hedge and "my kettle smells of plastic" reached the burning-brakes answer.
        entry("kettle-smell",
              (("kettle", "kettles", "boiled water", "water in the kettle"),
               ("smell", "smells", "smelly", "smelling", "stink", "stinks", "odour", "odor",
                "taste", "tastes", "tasting", "musty", "earthy", "metallic", "plastic",
                "chemical", "fusty")),
              "A smell from a kettle is nearly always scale or water left standing in it: fill it "
              "with equal parts water and white vinegar, boil it, leave it half an hour, then boil "
              "fresh water and tip it away twice. A new kettle's plastic smell fades after a few "
              "boils; a musty one means water has sat in it, so empty it each night. If the taste "
              "still comes through, filter the water.",
              # the timings, the scaling noise, the electricity and the descale method are their own
              # answers, and a boiling-water burn is a safety question
              avoid=("how long", "minutes", "cost", "costs", "electricity", "bill", "noise",
                     "noisy", "boiler", "burn", "burnt", "scald", "spilled", "spilt",
                     "descale", "limescale", "scale", "fur", "leak", "leaking"),
              bias=2),
        entry("kettle-slow",
              (("kettle", "kettles"),
               ("slow", "slowly", "slower", "taking so long", "takes so long", "takes ages",
                "taking ages", "forever", "why")),
              "The element has to heat through limescale before it reaches the water, so a badly "
              "scaled kettle can take twice as long - vinegar or citric acid brings it back to speed. "
              "Past that, a full kettle takes longer than a mugful, a 2kW kettle is about half the "
              "speed of a 3kW one, and very cold water is slower than water that has stood.",
              ask=("why", "slow", "slowly", "slower", "long", "ages", "forever", "takes"),
              avoid=("boiler", "noise", "noisy", "bang", "banging", "rumbling",
                     "broken", "not working", "switch", "element", "cost", "costs", "cheaper",
                     "energy", "bill", "descale", "descaleing", "limescale", "scaled", "scale",
                     "removing", "rid of", "fur", "furred", "furry", "white stuff", "chalky",
                     # a smell and a taste are not speed: "why does my kettle smell" was taking
                     # this answer about limescale slowing it down
                     "smell", "smells", "smelly", "smelling", "stink", "stinks", "odour", "odor",
                     "taste", "tastes", "tasting", "funny", "metallic", "plastic"),
              # A cause word in the line beats the how-long entry, which would otherwise take
              # "why does my kettle take so long" for the 3-minute answer.
              bias=3),
        # A frozen pipe is a job on the pipe, not on the boiler or the heating, and "freezing" is
        # the weather word in "it's freezing out": the pipe has to be named for this answer.
        entry("pipes-freezing", (("pipe", "pipes", "plumbing", "stopcock"),
                                 ("freeze", "frozen", "freezing", "froze", "freeze up",
                                  "froze up", "frozen solid", "thaw", "burst", "lagging",
                                  "lag", "split", "stop tap", "stop valve", "water off")),
              _pipes,
              avoid=("boiler", "radiator", "central heating", "car", "windscreen", "screen wash",
                     "freezer", "food", "vegetable", "veg", "meat", "bread", "cake", "bake",
                     "baking", "shoulder", "fingers", "hands", "feet", "paddling pool")),
        # "how do i drain the pipes" and "where is my stopcock" were the plumber shrug, and the two
        # travel entries took the water-off lines, so this entry names the job rather than the subject:
        # the stopcock, the valve and the words for switching it off. "Water" alone is not a key here -
        # that is the tap-water question and it belongs to travel.
        entry("water-shutoff",
              (("stopcock", "stop tap", "stop valve", "isolating valve", "water main", "mains water",
                "water supply", "water off", "shut the water", "shutting the water",
                "shut off the water", "shutting off the water", "turn the water", "turning the water",
                "turn off the water", "turning off the water", "switch the water off",
                "drain the pipes", "draining the pipes", "drain the system", "draining the system",
                "isolate the water", "stop the water",
                # A bare "keeps running" or "wont stop running" names no subject at all, and one of
                # them was the whole first part of this key, so "my nose keeps running" and "my tap
                # keeps running" reached the stopcock on the verb alone. The supply is named instead,
                # and the verb only counts when the water is the thing that runs: the nose, the tap,
                # the toilet and the cistern all keep their own running lines.
                "water keeps running", "water keeps coming", "water wont stop", "water won't stop",
                "water wont stop running", "water won't stop running", "water is running",
                "water runs", "water running", "running water", "pipes keep running"),
               ("where", "find", "locate", "how", "turn", "turning", "shut", "shutting", "off",
                "on", "drain", "draining", "wont", "won't", "keeps", "still", "stop", "running",
                "leaking", "flood", "flooded", "valve", "mains", "supply", "house", "flat",
                "kitchen", "sink")),
              _water_off,
              bias=3,
              # Drinking it, it not being safe, the water in a boiler and the water in a pool are all
              # different questions, and a fish tank and a garden water butt have their own. A loo that
              # will not stop filling, a dripping tap and a dripping shower are each a washer or a
              # valve, and "the toilet wont stop running" was the complaint this entry would otherwise
              # read as a burst pipe. "Abroad" and "holiday" are not avoided: the key needs the
              # stopcock or the words for turning the water off, which a drinking-water question never
              # has, so "how do i shut the water off before a holiday" is this answer and
              # "is the water safe abroad" stays with travel.
              avoid=("drink", "drinking", "safe to drink", "taste", "tastes", "brown", "smelly",
                     "boiler", "radiator", "heating", "filtr", "filter", "softener", "limescale",
                     # "rinse the rice until the water runs clear" is a cooking instruction, and
                     # the key's "water runs" phrase took it while the rice-rinse row in the
                     # cooking table that answers it lost by one point. Whatever the line is
                     # rinsing is the word that says which water it is, so the food and the verb
                     # name their own rows.
                     "rinse", "rinsing", "rinsed", "rice", "pasta", "lentils", "quinoa",
                     "chickpeas", "beans", "noodles", "spinach", "greens",
                     # "our hot water runs out quickly" is the cylinder emptying, not the stopcock:
                     # the key's "water runs" phrase took it on bias, and the answer was where the
                     # mains tap is. The hot water rows below take it.
                     "hot water", "hot tap", "hot taps", "immersion", "cylinder",
                     # a water heater or an immersion has its own valve or switch, so the mains
                     # stopcock is the wrong tap for it
                     "heater", "immersion", "cylinder", "hot water tank",
                     "pool", "swimming", "paddling", "fish tank", "aquarium", "water butt", "garden",
                     "plants", "lawn",
                     # "keeps running" is the tap that will not stop, but a phone or an app that
                     # "keeps running" has nothing to do with the mains: "i keep running out of
                     # storage on my phone" got the stopcock on main.
                     "phone", "phones", "app", "apps", "storage", "memory", "battery", "laptop",
                     "computer", "tablet", "printer", "software", "update", "download", "wifi",
                     # holding the water back is this entry; letting it go slowly is the trap
                     # under the plug hole: "how do i stop the water draining slowly out of the
                     # sink" was sent to the stopcock, and the answer was which way to turn it.
                     "draining", "drains", "drain", "drainage", "plughole", "plug hole",
                     "u bend", "blocked", "unblock",
                     "internet", "screen", "data", "background",
                     "toilet", "toilets", "loo", "loo", "cistern", "ballcock", "flush", "flushing",
                     "dripping", "drips", "drip", "shower", "bath", "bathroom")),
        # Using less of it. The house is full of answers about water going where it should not - a
        # tap dripping, a loo running, a stopcock, a boiler - and none about using less of it, so
        # "how do i use less water" and "how do i save water at home" had no answer at all once the
        # dry-eye row stopped taking them on the word "water". The two that matter are the shower and
        # the dripping tap, and both are a washer or a timer rather than a new bathroom, so the card
        # leads with those and gives the free habits after them.
        entry("water-less",
              (("use less water", "using less water", "uses less water", "save water", "saving water",
                "water saving", "reduce water", "reduce my water", "reduce our water",
                "cut water use", "cut my water use", "cut our water use", "wasting water",
                "waste water", "water waste", "water use", "water usage", "using so much water",
                # the saving put as waste rather than as saving: "how do i waste less water" had
                # no phrase of its own here, and the bare "waste" in the sink-trap row's key sent
                # it to a bowl under the trap
                "waste less water", "wasting less water", "waste less water at home",
                "use so much water", "less water at home", "save on water"),
               # the ask words, and what the household is: a line naming a shower or a garden already
               # has its own card, so neither is here
               ("how", "ways", "tips", "help", "stop", "much", "home", "house", "household",
                "family", "flat", "ours", "we use", "reduce", "cut", "save", "saving", "less")),
              "A shower of five minutes rather than ten saves about 40 litres a time, and a dripping "
              "tap wastes around 5,500 litres a year - both are a washer or a shorter timer, not a new "
              "bathroom. After those, run the washing machine and the dishwasher only when they are "
              "full (a half load uses nearly the same water as a full one), put a water butt on the "
              "downpipe for the garden instead of a hose, and drop a cistern bag in an old loo, which "
              "saves a litre or two a flush. A water meter is free to have fitted in most of the UK "
              "and usually cuts a bill for one or two people, though a big family can pay more on one.",
              # drinking it, a garden that needs watering, and the water going somewhere it should not
              # are all other answers, and so is a cooking instruction: "use a little less water than
              # the packet says" is the rice, not the meter.
              # "watering" is not in this list even though the garden rows own it: the matcher
              # folds it onto the bare "water", so an avoid word of it denies every line that says
              # "save water" at all.
              avoid=("drink", "drinking", "thirsty", "thirst", "safe to drink", "plants", "plant",
                     "lawn", "water the", "water my", "water butt", "rain barrel",
                     "sprinkler", "irrigation", "hose", "pool", "swimming", "fish tank", "aquarium",
                     # the garden has its own watering card, and it answers "how do i use less water
                     # in the garden" better than a card about the meter does
                     "garden", "gardening", "allotment", "flowerbed", "flower bed", "hanging basket",
                     # and a bath against a shower is the `bath-or-shower` card, which reads "uses
                     # less water" as its own ask: that row sits later in this list, so without the
                     # fence the comparison would come to the household card instead
                     "a bath or a shower", "bath or a shower", "bath or shower", "a shower or a bath",
                     "shower or a bath", "shower or bath", "bathtub", "a bath", "hot bath",
                     "leak", "leaking", "burst", "flood", "flooded", "blocked", "drain", "drains",
                     "boiler", "radiator", "hot water", "softener", "hard water", "limescale",
                     "rice", "pasta", "dough", "bread", "pastry", "baking", "cake", "sauce", "stock",
                     "simmer", "boil", "boiling", "kettle", "recipe", "cook", "cooking", "pan",
                     "washer", "dripping", "drip", "drips", "eye", "eyes",
                     # How much a thing uses against how much a household can save are two
                     # questions. "does a dishwasher use less water than washing up" holds the
                     # phrase "use less water" that this row is keyed on, so it came to the
                     # household card and was told about five-minute showers; the litres table
                     # (water-use, in home.py) answers it with the figures for both sides. The
                     # row is still the answer for the household with no machine named in it.
                     "dishwasher", "dishwashers", "washing machine", "washing machines",
                     "washer", "washers", "tumble dryer", "tumble drier", "toilet", "toilets",
                     "flush", "flushes", "cistern", "shower", "showers", "a shower of",
                     "bathtub", "hose", "hosepipe")),

        # The gas is turned off somewhere else from the water, and it is the one of the three that is
        # also a call to the emergency line, so it gets its own card rather than a corner of the water
        # one: "how do i turn off the gas supply" met a search hedge, and "where is the gas meter"
        # should say where the lever is, not where the meter is.
        entry("gas-shut-off",
              (("gas", "gas meter", "gas supply", "gas valve", "meter box", "gas pipe",
                # the water stopcock row keys "shut off valve" on its own, and "where is the gas
                # shut off valve" was answered with a brass tap under the sink: the gas phrase is
                # this row's, and the water row stands down on it below
                "gas shut off valve", "gas shutoff valve", "gas stop valve", "gas stopcock"),
               # The intent words, and the phrases that name the job. The words that ride along with
               # the thing ("meter", "emergency", "smell", "leak") are not here: "gas meter" is the
               # whole first part, so a clicking or beeping meter reached the shut-off card, which is
               # the wrong subject and buries the "what is it doing" answer the person can use.
               ("turn off", "turn it off", "turning off", "shut off", "shutting off", "isolate",
                "switch off", "turn", "off", "where", "valve", "handle", "emergency switch",
                "leaking gas", "smell gas", "smelling gas", "stop the gas")),
              "The gas shut-off is the lever on the pipe beside the meter, usually in a box outside "
              "or under the stairs: a quarter turn so the lever sits across the pipe rather than "
              "along it turns the gas off. If you can smell gas, do not touch a switch, a light or a "
              "phone indoors - open the windows, get everyone out and ring the gas emergency line "
              "from outside: 0800 111 999 in England, Scotland and Wales, 0800 002 001 in Northern "
              "Ireland, 911 in the US. Only a Gas Safe engineer turns it back on.",
              # Turning it back on is a different job and a different person's: it is the Gas Safe
              # engineer's. A bare "how" in the ask part was enough to win "how do i turn the gas back
              # on", so the ways of asking to put it on are named here instead.
              avoid=("bill", "bills", "price", "tariff", "cheaper", "cost", "usage", "boiler",
                     "cooker", "hob", "oven", "fire", "fireplace", "cylinder", "bottle", "bbq",
                     "barbecue", "car", "central heating", "supplier", "reading", "standing charge",
                     "back on", "turn on", "turning on", "turned on", "switch on", "switching on",
                     "gas on", "gas back on", "turn the gas on", "turning the gas on",
                     "relight", "re-light", "pilot light", "pilot",
                     # "where do i find a gas safe engineer" is a question about the trade, not
                     # about the meter: the find-a-tradesman row answers it, and the word "gas"
                     # plus "where" was enough to hand it the lever card instead
                     "gas safe", "gas safety", "find a", "find me a")),
        entry("boiler-pressure", ("boiler", ("pressure", "low", "drop", "dropped", "bar", "gauge")),
              # "why" after this answer is asked all the time, so the cause is its own sentence
              # after the topping up: the first sentence stays the gauge reading, which is what
              # "what pressure should it be" and "what should i do about it" are answered from.
              "Top the pressure up to between 1 and 1.5 bar using the filling loop, then bleed the "
              "radiators and check it again the next day. The pressure falls because water is escaping "
              "somewhere: a radiator valve, a joint, or the pressure relief pipe outside. If it keeps "
              "dropping, stop topping it up and get a heating engineer out.",
              # "what happens now" after that answer is the engineer, and saying it as its own
              # line adds the one thing the card leaves out: how often it has dropped is what
              # tells the engineer where to look.
              outcomes=(("next",
                         "Get a heating engineer out and tell them how often it has dropped since "
                         "you topped it up: a system that loses pressure twice is losing water at a "
                         "valve, a joint or the relief pipe, and each top-up only hides it."),)),
        # The gauge is the sealed system's, and it is not always called a boiler: "the radiator is
        # down on pressure", "my heating pressure has dropped" and "the heating is down to half a
        # bar" are all the same gauge. The pressure word comes first here so a radiator word in
        # the line cannot make the answer about the radiator - that is the valve card's, and "and
        # how do i bleed a radiator" after this answer must stay the bleed card.
        entry("heating-pressure", (("pressure", "bar", "psi", "gauge"),
                                   ("down", "low", "lowest", "dropped", "drop", "dropping", "half",
                                    "zero", "under", "below", "fallen", "falling", "topped",
                                    "top up", "topping up", "filling loop", "what should",
                                    # "how do i sort the pressure out" is this card, not the bleed
                                    # one: the bleed answer only lets air out. The bleed row names
                                    # that phrasing in its own avoid list, so this row has to take
                                    # it or the line punts.
                                    "sort", "sorts", "sort it out", "sort out",
                                    # the same repair ask written with "fix", which the bleed row
                                    # gives up in its own avoid list ("does that fix" is its
                                    # question, "how do i fix" is this one)
                                    "fix", "fix it", "fixes it", "how do i fix")),
              "Top the pressure up to between 1 and 1.5 bar using the filling loop, then bleed the "
              "radiators and check it again the next day. The pressure falls because water is escaping "
              "somewhere: a radiator valve, a joint, or the pressure relief pipe outside. If it keeps "
              "dropping, stop topping it up and get a heating engineer out.",
              # "i feel under pressure at work" is the same three words as a gauge question and
              # nothing to do with a boiler: the human sense stands this row down.
              # A line that says "boiler" is `boiler-pressure`'s, and that row is the one the
              # follow-up machinery knows: stealing "my boiler pressure keeps dropping" for a
              # card with the same words but a new id turned the next turn's "Same as before"
              # into an echo ("Got it - you have to top it up every week").
              # A bare "bar" is the bar on a bicycle as often as it is a pressure: the guard above
              # is the unit test, so "drop bars" and "my bars are too low" are not gauge lines.
              guard=_a_gauge_reading,
              avoid=("under pressure", "feel the pressure", "feeling the pressure",
                     "peer pressure", "stressed", "stress", "anxious", "anxiety",
                     "pressure at work", "pressure at school",
                     # a line that asks whether a bleed fixes the gauge is the bleed row's:
                     # "Bleeding does not put pressure back in" is the half of the answer that
                     # says why not. With "sort" in this row's key too, "will bleeding them sort
                     # the pressure" came here and lost it. A report that the radiators were bled
                     # and the gauge is still low is the topping-up question, so the fence is the
                     # question and not the word.
                     "will bleeding", "would bleeding", "does bleeding", "do i bleed",
                     "will bleeding them", "bleeding fix", "bleeding sort", "bleeding help",
                     "bleed them", "bleeding the radiators fix",
                     # A gauge that is too high is the opposite job, and a topping-up answer to it
                     # tells someone to put more water into a system that is already over pressure.
                     # The words are the bleed row's list, so both rows of the pair agree on what
                     # a high gauge is.
                     "too high", "high", "higher", "over 2", "over 3", "above 2", "above 3",
                     "rising", "climbing", "2 bar", "2.5 bar", "3 bar", "overpressure",
                     "boiler", "boilers", "combi")),
        entry("bleed-and-pressure", (("pressure", "bar", "gauge", "top up", "top it up"),
                                    ("fix", "fixes", "cure", "cures", "sort", "sorts",
                                     "does that", "will that", "would that", "that fix",
                                     # "does bleeding help the pressure" and "will bleeding do
                                     # anything" ask the same yes/no as "does it fix it", and the
                                     # row passed them, so both were a search hedge. They are
                                     # written as phrases and not as bare "help"/"work", because
                                     # a bare one takes every other sense of the word: "how do i
                                     # help without pressure", from a parent asking about SATs,
                                     # took this row on "help" and got the boiler paragraph.
                                     "help the pressure", "helps the pressure",
                                     "help the gauge", "helps the gauge", "worth it")),
              "Bleeding does not put pressure back in - it lets air out, and it can drop the "
              "gauge a little. Top it up at the filling loop to 1 to 1.5 bar with the system "
              "cold, then check it the next day; if it is low again there is a leak somewhere "
              "and that is an engineer's job.",
              # The same unit test as `heating-pressure`: "my bars are too low" reached this row
              # on "bar" alone and was told about bleeding a radiator.
              guard=_a_gauge_reading,
              # A gauge that is too high is the opposite job and a topping-up answer is the
              # wrong move to hand someone: "the pressure is too high" took this row on "high"
              # being nowhere and "too" being here.
              # What the repair costs is the money card's question, not this one. The row needs a
              # cross-question word to fire at all ("would that", "that fix", "same"), and the
              # boiler is still in memory from the turn before, so "what would that cost to fix"
              # was read as a cross-question and the person asking the price was told how
              # bleeding works and never got a figure. The price words stand the row down.
              #
              # They are the price words and not "how much": an avoid phrase is read loosely, so
              # "how much" as one stood this row down for "how much would that be", which already
              # reached the boiler figures on main, and the turn came back a hedge - a worse
              # answer for a case this change is not about.
              #
              # The feelings sense of the word is the other stand-down, and it is the one a
              # reviewer caught: "how do i help without pressure" is a parent asking about SATs
              # (deck row qmis-year6-01) and it came here on a bare "help" that took every sense
              # of the word. The bare word is gone from the key; these name the sense. "no
              # pressure" and "pressure on" are deliberately not here - "there is no pressure in
              # the boiler" and "the pressure on the gauge" are gauge lines.
              avoid=("too high", "high", "higher", "over 2", "over 3", "above 2", "above 3",
                     "rising", "climbing", "2 bar", "2.5 bar", "3 bar", "overpressure",
                     "under pressure", "peer pressure", "pressure at work", "pressure at school",
                     # "how do i sort the pressure out" and "my boiler pressure is low, how do i
                     # sort it" are repair asks, and the cue is the how-do-i frame, not the verb
                     # "sort": the bleed row owns "does that sort the pressure". The frame is what
                     # separates them, so the frame is the fence.
                     "how do i sort", "how to sort", "how can i sort", "how do you sort",
                     "how do i fix", "how to fix", "how do i top", "what do i do about the pressure",
                     "without pressure", "putting pressure", "pressure myself", "pressure from",
                     "pressure her", "pressure him", "pressure them", "sats", "exams", "revision",
                     "blood pressure", "tyre", "tyres", "tire", "tires",
                     "cost", "costs", "costing", "price", "prices", "priced", "quote", "quotes",
                     "quoted", "charge", "charges", "£")),
        # The noise is in the heating as often as in the boiler: "my heating is making a clanking
        # noise" named no boiler at all and got a shrug, though the answer is the same one. The
        # row is still keyed on a sound, so "how much does heating cost" never reaches it. "hot
        # water" and "the heating" are deliberately not subjects: a two-word phrase also scores
        # its own words, so "only when the hot water comes on" cleared the minimum on the phrase
        # alone and pulled the follow-up into this row.
        # The sounds come from the shared list in wording.py, because this row's own list named
        # some forms of each sound and not others: the answer has a paragraph for a tick or a click
        # ("pipes expanding as they heat"), and "my boiler clicks a lot" and "the boiler is
        # clicking" reached nothing but the greeting, while "the boiler wont stop clicking" got in
        # through "clicking" being spelled out on another row. One list for every row that answers
        # a noise means the next appliance inherits the forms too.
        entry("boiler-noise", (("boiler", "heating", "central heating", "heat pump"),
                               MACHINE_SOUNDS + NOISE_WORDS),
              _boiler_noise),
        # A kettling boiler is a different fault with a different first move: limescale on the heat
        # exchanger, not air. Naming it is the whole question, so it gets its own answer rather than
        # the banging one with a postscript.
        # "combi" is a boiler by another name, and a line that says it is a heating line: "our
        # combi is kettling and the pressure is fine" reached nothing at all, because the row's
        # other half wanted the word "boiler".
        entry("boiler-kettling", (("kettling", "kettle", "kettles", "limescale", "scale", "descale",
                                   "sludge"),
                                  ("boiler", "boilers", "combi", "heating", "central heating",
                                   "hot water", "radiator", "radiators")),
              ("Kettling - a noise like a kettle boiling as it fires - is limescale on the heat "
               "exchanger, not air in the pipes, so bleeding the radiators will not stop it. Get a "
               "heating engineer to power-flush or descale the system and fit a scale reducer or a "
               "magnetic filter; turn the boiler flow temperature down a notch meanwhile, because "
               "kettling gets worse the hotter it runs."),
              # "a noise like a kettle boiling" ties with the banging answer on words, and this is the
              # more specific fault: the line named the sound.
              # A kettle in a line about how long the water takes is the thing in the kitchen: "how
              # long does it take to boil a kettle" was answered with kettling on the boiler.
              avoid=("how long", "how many minutes", "minutes to boil", "take to boil",
                     "does it take", "tea", "coffee", "cup of"),
              bias=1),
        entry("radiator-noise", ("radiator", ("noise", "noisy", "banging", "clicking", "gurgling",
                                              "ticking", "loud")),
              ("Ticking and clicking is the pipes expanding as they heat, which is normal and stops "
               "once the system is warm. Banging or gurgling means air or trapped water: bleed the "
               "radiators and check the boiler pressure sits between 1 and 1.5 bar.")),
        # "bled" and "bledding" are what people type for bleed: a one-letter verb that is also a
        # real word ("bled", "cold") never comes back from the typo reader, so it is listed here.
        # A heated towel rail is a radiator with a bleed valve at the top, and people call it a rail
        # rather than a radiator, so "how do i bleed a towel rail" reached nothing at all.
        # The heating and the hot water "keep going cold" is a shape the fault rows did not read: on
        # main "the heating keeps going cold" got "Got it - is there anything you'd like a hand
        # with?" and "my hot water keeps going cold" was packed for a picnic. The words that matter
        # are the thing that went cold and the verb shape, so this row keys on both and the radiator
        # keeps its bleed and sludge answers.
        entry("heating-goes-cold",
              (("heating", "the heating", "my heating", "our heating", "central heating",
                "hot water", "my hot water", "hot tap", "hot taps", "boiler",
                "immersion", "hot water cylinder", "cylinder", "hot bath", "bath water"),
               ("keeps going cold", "keeps running cold", "keeps coming out cold",
                "goes cold", "going cold", "runs cold", "running cold", "comes out cold",
                "cold after", "goes cold after", "cools down", "keeps cooling", "hot then cold",
                "comes on then goes off", "hot and cold", "lukewarm", "never really hot")),
              _heating_goes_cold,
              bias=2,
              # a radiator that is cold is the bleed and sludge rows' question, and a bill is not a
              # fault at all
              avoid=("radiator", "radiators", "rads", "bill", "bills", "cheaper", "cost", "save",
                     "tariff", "insulation", "energy", "kettle", "shower", "washing machine",
                     "dishwasher", "drink", "drinks", "beer", "wine", "milk", "oven", "microwave",
                     "hob", "air fryer", "toaster", "iron", "food", "bath water")),
        entry("radiator-bleed", (("radiator", "towel rail", "towel radiator", "heated towel rail",
                                  "ladder rail", "ladder radiator", "chrome rail"),
                                 ("bleed", "bled", "bleeding", "bledding", "cold",
                                  "bottom", "noise", "hot",
                                  # the shape of the fault said as a phrase, because a towel in the
                                  # line otherwise reads as washing
                                  "cold at the top", "hot at the bottom", "warm at the top",
                                  "cold at the top of the radiator")),
              "Radiators that are hot at the bottom and cold at the top have air in them: open the bleed "
              "valve at the top with a radiator key, a quarter turn at a time, with a cloth under it, "
              "until water trickles out steadily. Two minutes a radiator is all it takes, and a whole "
              "house takes ten to fifteen minutes. Then check the boiler pressure and top it up if it's "
              "below 1 bar.",
              # A radiator that is hot at the top and cold at the bottom is the other fault (see
              # radiator-cold-bottom), and the bleed answer is the wrong one for it.
              # A line that names the boiler is the boiler's, not the radiator's: "my boiler is
              # banging and the radiators are cold at the top" is about the boiler, and the banging
              # and pressure rows answer it and tell the person to bleed the radiators themselves.
              # Only the words that name the boiler are held out - "pressure" and "pump" are not
              # boiler words (the banging card says a pump set too fast), and holding them out took
              # the bleed card away from "radiator cold at the top and the pressure is low".
              avoid=("cold at the bottom", "cold at the botto", "cold bottom", "hot at the top",
                     "warm at the top", "cold along the bottom", "filling loop",
                     # the same fault said as a denial: "hot at the bottom" is in this row's key,
                     # so "the radiator is not hot at the bottom" (a sludge radiator, cold along
                     # the bottom) read as the air one and was told to bleed it
                     "not hot at the bottom", "not warm at the bottom", "not getting hot at the "
                     "bottom", "isnt hot at the bottom", "isn't hot at the bottom",
                     "lukewarm at the bottom", "cool at the bottom"),
              # #6487 held out the bare word "boiler", which is not the same as the boiler being
              # the fault: people name the boiler to say it is *not* the problem, and then the
              # bleed card is the answer they need. "boiler pressure is fine, radiator cold at the
              # top" was told to top the pressure up through the filling loop, and "my boiler
              # pressure is ok, the radiator is still cold at the top" got the cold-and-flu card.
              # Only a boiler named with something wrong with it stands this row down.
              guard=_the_boiler_is_not_the_fault),
        # The next thing people ask after the bleed card is about the key: "which key do i need",
        # "ok so i bleed them with a key?", "does it need a special key". The bleed row's answer
        # names a radiator key and stops there, and the follow-up was answered "Everything about a
        # key is in what I said above" - a sentence about the conversation rather than about the
        # key you buy. One row for the tool, and the radiator has to be in the line or in the last
        # turn, so a door key or a keyboard keeps its own answer.
        entry("radiator-bleed-key",
              (("radiator key", "bleed key", "bleeding key", "key for the radiator",
                "key for a radiator", "radiator valve key", "special key", "little key", "small key",
                "key", "keys"),
               ("radiator", "radiators", "rad", "rads", "bleed", "bled", "bleeding", "bleed them",
                "bleed it", "valve", "valves", "towel rail")),
              "Yes - a radiator bleed key: a little square or half-moon spanner, about two or three "
              "pounds from a hardware shop or a big supermarket, and a cloth under the valve to catch "
              "the drips. Some newer valves take a small flat screwdriver instead, so look at the slot "
              "before you buy. A quarter turn is enough, and you stop when water runs steadily rather "
              "than hissing air.",
              # a door key, a keyboard, a bike lock and a car key are other questions, and the
              # radiator's own fault cards are the hardware answer, not the tool
              avoid=("door", "doors", "front door", "back door", "lock", "locks", "lockout", "locked",
                     "snapped", "snap", "lost my keys", "lost the key", "spare key", "keyboard",
                     "keyboards", "keypad", "keyring", "key fob", "fob", "car key", "bike lock",
                     "padlock", "ignition", "remote", "opener", "cylinder lock", "euro cylinder",
                     "cold at the bottom", "hot at the top", "sludge", "noise", "banging",
                     "pressure", "thermostat", "trv")),
        # The mirror image of a radiator with air in it: hot at the top, cold at the bottom means the
        # bottom of the radiator is full of sludge, so there is nothing to bleed. Main answered it
        # with the bleed card, which tells someone to open a valve that will not help.
        entry("radiator-cold-bottom",
              ("radiator", ("cold at the bottom", "cold along the bottom", "cold bottom",
                            "hot at the top", "warm at the top", "bottom is cold",
                            "bottom stays cold", "half cold", "never gets hot",
                            # the same thing said as a denial: "my radiator is not getting hot at
                            # the bottom" was a listening reply, because a state word cannot be
                            # keyed and the negation has to be spelled out
                            "not getting hot at the bottom", "not hot at the bottom",
                            "not warm at the bottom", "wont get hot at the bottom",
                            "won't get hot at the bottom", "doesnt get hot at the bottom",
                            "doesn't get hot at the bottom", "getting hot at the bottom",
                            "lukewarm at the bottom", "cool at the bottom",
                            "cold at the bottom of", "cold along the bottom of")),
              "Hot at the top and cold at the bottom is sludge sitting in the radiator, not air, so "
              "bleeding it will not help: the water cannot get round the bottom. Ask a heating engineer "
              "to power-flush the system or add a chemical cleaner, and have a magnetic filter fitted "
              "so it does not come back. Turning the other radiators off to push water through the cold "
              "one is a five-minute test that shows whether it is sludge or a stuck valve."),
        # A radiator that will not heat up at all: the key is the fault phrase rather than the state
        # word, because the denial reader rules a state word out ("is not getting hot" is not a hot
        # radiator) and a key of "radiator" alone scores 0. See RADIATOR_WHOLE_HOUSE above for the two
        # first moves.
        entry("radiator-not-hot",
              (("radiator", "radiators", "rad", "rads", "central heating", "the heating",
                "heating"),
               ("upstairs", "downstairs", "landing", "first floor", "ground floor",
                "not getting", "not warming", "not heating", "isnt getting", "isn't getting",
                "arent getting", "aren't getting", "isnt warming", "isn't warming", "isnt heating",
                "isn't heating", "wont heat", "won't heat", "wont warm", "won't warm",
                "not hot", "not warm", "stays cold", "staying cold", "still cold", "still not hot",
                # "radiator is cold" bare is not here, because a cold radiator with nothing else
                # said is the bleed question and that row keeps it; "in" is what marks the one that
                # named where it is cold
                "radiator is cold in", "rad is cold in",
                # "the radiator in my bedroom is cold" names where the radiator is rather than
                # where the cold is, so it needed its own shape
                "radiator in my", "radiator in the", "rad in my", "rad in the",
                "never gets hot", "never gets warm", "never warms", "cold radiator",
                "one radiator is cold", "rads are cold", "radiators are cold",
                "thermostat is stuck", "thermostat stuck", "valve is stuck", "valve stuck",
                "trv stuck", "stuck on")),
              _radiator_not_hot,
              # It ties the bleed row at 5 words of rank on "bled ... still cold" (radiator + still
              # cold), and a tie is file order, so the bias is what gives the fault card the turn the
              # line is about: someone who has already bled a radiator is not told to bleed it again.
              bias=2,
              # a radiator that is hot at the top and cold at the bottom is the sludge card, and the
              # bill question about the heating is not a fault at all
              avoid=("at the top", "at the bottom", "cold at the top", "hot at the bottom",
                     "top half", "bottom half", "bill", "bills", "cheaper", "cost", "save",
                     "tariff", "insulation", "bleed a radiator", "how do i bleed", "bleed valve",
                     "radiator key",
                     # a heating word is also a hot-water word: "the hot water is not heating up" is
                     # the cylinder or the immersion, not a radiator, and this card talked about
                     # valves and radiators to someone whose hot taps had gone cold
                     "hot water", "shower", "immersion", "cylinder", "hot tap", "hot taps",
                     "tank", "no hot",
                     # and every other thing in a house that heats or warms: the oven, the boiler
                     # and the water were all told about a radiator pin, since "heating" is the
                     # verb in "my oven isnt heating up" as much as the noun in "my heating"
                     "boiler", "oven", "water", "hob", "washing machine", "dishwasher",
                     "tumble dryer", "towel rail", "airing cupboard",
                     # and the small appliances, for the same reason: "heating" is the verb in
                     # "my microwave isnt heating" as much as it is the noun in "my heating", and
                     # a person with a cold microwave was told to take a thermostatic valve head
                     # off a radiator
                     "microwave", "microwaves", "kettle", "kettles", "toaster", "toasters",
                     "iron", "air fryer", "airfryer", "air-fryer", "coffee machine",
                     "washer dryer", "deep fat fryer", "slow cooker", "pressure cooker",
                     # a tumble dryer, a heat pump dryer and a hair dryer heat too, and "my dryer
                     # isnt heating up" and "my heat pump dryer is not heating up" were both told
                     # to take a thermostatic valve head off a radiator. The machine that will
                     # not heat is its own card, and the dryer is the one this row kept missing:
                     # only "tumble dryer" and "washer dryer" were named, and most people type
                     # "my dryer".
                     "dryer", "dryers", "drier", "driers", "tumbler", "heat pump dryer",
                     "heat pump drier", "heat-pump dryer", "hair dryer", "hairdryer",
                     # a garden heap heats up too, and "why is my compost not heating up" was
                     # told to take a thermostatic valve head off a radiator, because "heating"
                     # is the verb in "my compost isnt heating up" as much as the noun in "my
                     # heating"
                     "compost", "composts", "heap", "heaps", "pile", "piles", "allotment",
                     "garden", "gardening", "manure", "muck")),
        # "i have no hot water" names no boiler and boiler-broken needs the word, so the commonest
        # way of saying it got "Got it - is there anything you'd like a hand with?". The line is
        # often three words with no verb phrase at all, so the second group repeats the subject: a
        # key that scores on the phrase alone still needs a second word from the line to answer.
        entry("no-hot-water",
              (("no hot water", "hot water gone", "hot water has gone", "hot water not working",
                "hot water isnt working", "hot water isn't working", "hot water is not working",
                "hot water has stopped", "hot water stopped", "hot water has stopped working",
                "hot water comes and goes", "hot water is cold", "hot water is off",
                "hot water is lukewarm", "only cold water", "no hot water anywhere",
                "no heating and no hot water",
                # "we keep running out of hot water" is the same fault said as a habit, and it had
                # no row of its own: "runs" is a form of "running" and "water" sat in the place part
                # of the holiday row, so a house with no hot water was told to eat where it is busy.
                # The phrase is keyed here, not the bare "running", which is what a nose and a
                # deadline both say.
                "running out of hot water", "run out of hot water", "ran out of hot water",
                "runs out of hot water", "running out of hot water in the mornings",
                "hot water runs out", "hot water runs out fast", "hot water running out",
                # and the ask from the other side: "how do i get hot water back" names no fault at
                # all, so it reached no row and got a punt
                "get hot water back", "hot water back", "hot water working again",
                # and the same habit with the words the other way round
                "keeps running out of hot water", "hot water keeps running out",
                # The supply that is there and cold is the same fault said as a verb, and it had no
                # row at all: "my hot water is not heating up" and "the water isn't getting hot" got
                # a bare nod, because every key above is the water being *absent*. The phrase has to
                # carry the water, or "my microwave is not heating up" and "my food is not hot" would
                # land on a plumber.
                "hot water is not heating up", "hot water isn't heating up",
                "hot water isnt heating up", "hot water not heating up",
                "hot water is not heating", "hot water isn't heating",
                "hot water is not getting hot", "hot water isn't getting hot",
                "hot water isnt getting hot", "hot water not getting hot",
                "hot water is not hot", "hot water isn't hot", "hot water is never hot",
                "hot water is not hot enough", "hot water won't heat up", "hot water wont heat up",
                "hot water won't get hot", "hot water wont get hot",
                "water is not heating up", "water isn't heating up", "water isnt heating up",
                "water not heating up", "water is not heating", "water isn't heating",
                "water is not getting hot", "water isn't getting hot", "water isnt getting hot",
                "water won't heat up", "water wont heat up", "water is not warming up",
                "water isn't warming up", "hot water is not warming up",
                # "not hot enough" says the same fault as an amount rather than as a state, and
                # the hydration row took "water not hot enough" for it
                "water not hot enough", "water is not hot enough", "water isn't hot enough",
                "water isnt hot enough", "the water is not hot enough",
                "water is never hot enough", "why is my water not hot enough",
                "hot water is not hot enough for a bath",
                # the tap named instead of the supply: "the water from the hot tap is not hot" was a
                # shrug too, and it is the same question about the same tank
                "hot tap is not hot", "hot tap isn't hot", "hot tap is cold",
                "hot tap water is cold", "water from the hot tap is not hot",
                "water from the hot tap is cold", "water from the hot tap runs cold",
                # The hyperbaton shapes: every phrase above puts "is" between the water and the
                # temperature, so "why is my hot water cold" - the plainest way to ask - matched
                # none of them and was answered by the science card about why water is wet. The
                # copula is the "why is" at the front, so these carry the words without it.
                "why is my hot water cold", "why is the hot water cold",
                "why is our hot water cold", "why is hot water cold",
                "why is my hot water not hot", "why is the hot water not hot",
                "why is my hot water warm", "why is my hot water lukewarm",
                "why is my hot water tepid", "hot water comes out cold",
                "water comes out of the hot tap cold", "cold water comes out of the hot tap",
                # the water with no "hot" in it: a person with cold taps asks this way, and the
                # science card answered it. The pool, the sea and the glass are fenced out below.
                "why is my water cold", "why is the water cold", "why is my tap water cold",
                "why is the tap water cold", "my tap water is cold", "the tap water is cold",
                "why is my cold water warm", "why is the cold water warm",
                "cold tap runs warm", "cold water is warm", "cold tap is warm",
                # heating on, radiators hot, taps still cold - the same cylinder or diverter,
                # asked by naming the heating
                "why is the heating not warming the water", "heating is not warming the water",
                "not warming the water", "heating works but the water",
                "radiators are hot but the water", "radiators hot but no hot water"),
               ("hot water", "water", "tap", "taps", "shower", "bath", "kitchen", "bathroom",
                "flat", "house", "home", "heating", "morning", "mornings", "why", "fix", "check")),
              ("Start at the programmer: it is usually on a timer that has slipped, or on 'water "
               "only' when you wanted heating too. A combi with no hot water but working heating is "
               "nearly always low pressure or a stuck diverter valve, so look at the gauge (1 to 1.5 "
               "bar cold) and try the reset. If there is a hot water cylinder, look for the immersion "
               "switch and the thermostat on the side, and check the little header tank has water in "
               "it. Anything inside a gas boiler, or gas you can smell, is a Gas Safe engineer."),
              # a line with no hot water and a word about heat ties with the hot-weather card, which
              # then wins on key order; the plumbing answer is the one that helps
              bias=1,
              avoid=("boiler", "boilers", "gas", "cylinder", "immersion", "pressure", "gauge",
                     "error code", "flame", "pilot", "condensate", "gas safe",
                     # a hot water *bottle* and a hot water tap abroad are other questions
                     "bottle", "abroad", "hotel", "camping", "kettle",
                     # "why is my water cold" is a tap or a tank, not a pool, a sea or a glass
                     "pool", "pools", "swimming pool", "swim", "sea", "beach", "lake", "river",
                     "glass of", "glass", "drinking", "ice", "ice cube", "cubes", "freezer",
                     "fridge", "cool box", "cooler", "flask", "gym", "hot tub", "jacuzzi",
                     # A shower that goes cold after a few minutes is `shower-goes-cold`'s question:
                     # this answer is about a supply that is not there at all, so the halfway-through
                     # shapes stand this row down and "no hot water at all" does not.
                     "after one shower", "after a shower", "after two showers", "after a few minutes",
                     "halfway through", "half way through", "mid shower", "mid-shower", "goes cold",
                     "turns cold", "runs cold")),
        # A heat pump is the question people ask twice: what is it doing, and is it worth it. The
        # mechanics come first for "how does it work", and the verdict for "is it worth it".
        # A cold shower with hot taps elsewhere is the shower itself; no-hot-water above owns the
        # whole house, so that entry keeps its lines and this one never takes them.
        entry("shower-cold",
              (("shower", "showers", "power shower", "electric shower", "mixer shower", "shower head",
                # The bare nouns scored 2 against a floor of 4, so "why is my shower cold" was
                # answered by the science card about water being wet rather than by this one. The
                # question shapes carry it over the floor.
                "shower is cold", "shower is not hot", "shower is lukewarm", "shower isnt hot",
                "shower isn't hot", "shower runs cold", "shower running cold",
                "shower goes lukewarm", "why is my shower cold", "why is the shower cold",
                "why is my shower not hot"),
               ("cold", "cool", "lukewarm", "not hot", "warm", "temperature", "running cold",
                "runs cold", "cold water")),
              "If the shower runs cold but the hot taps elsewhere are fine, it is the shower: an "
              "electric shower usually wants the pull cord or a tripped switch in the consumer unit "
              "checked, and a mixer shower is often a stuck thermostatic cartridge, which frees up if "
              "you take the head off and work the temperature knob from cold to hot a few times. If "
              "the hot taps are cold too, the fault is the boiler or the cylinder rather than the "
              "shower.",
              bias=1,
              avoid=("blocked", "drain", "smell", "mould", "clean", "limescale", "buy", "best",
                     "which", "cheapest", "install", "bathroom", "tile", "leak", "boiler", "curtain",
                     "screen", "tray", "no hot water", "hot water", "house", "anywhere", "heating",
                     # A shower that comes hot and then goes cold is the hot water running out, not
                     # the shower giving up: shower-goes-cold already answers it from the boiler side,
                     # and that answer is the better one. These phrases are the words of that question.
                     "goes cold", "going cold", "gone cold", "went cold", "keeps going cold",
                     "kept going cold", "turns cold", "turned cold", "hot then cold",
                     "warm then cold", "cold after a few minutes", "after a few minutes",
                     "cold quickly", "cuts out",
                     # A cold shower somebody chooses is not a fault, and it was a shrug on main:
                     # "is a cold shower good for you" wants a fact, not a plumber. The bare "cold"
                     # in the key means any cold shower reads as a broken one, so the practice words
                     # stand this entry down and the honest shrug comes back.
                     "a cold shower", "cold showers", "cold shower good", "cold shower bad",
                     "have a cold shower", "having a cold shower", "take a cold shower",
                     "taking a cold shower", "cold shower after", "cold shower every",
                     "cold shower in the morning", "cold water therapy", "cold plunge", "ice bath",
                     "sauna", "contrast shower", "bracing")),
        # The dial, as opposed to the fault: "how hot should hot water be" and "how do i make my
        # hot water hotter" were a search hedge, and they are the one question about a cylinder
        # that has a number for an answer. Asking about the setting is not asking why the water
        # is cold, so "why is my hot water cold" stays with no-hot-water above.
        entry("hot-water-temperature",
              (("hot water temperature", "temperature of the hot water", "hot water be",
                "hot water hotter", "make the water hotter", "make my hot water hotter",
                "turn up the hot water", "turn up my hot water", "turn the hot water up",
                "hot water thermostat", "cylinder thermostat", "hot water setting",
                "how hot should hot water", "how hot should the hot water",
                "how hot should my water", "what temperature should the hot water",
                "what temperature should my hot water", "what should the hot water be set to",
                "how hot should the water be", "hot water too hot", "hot water is too hot"),
               ("hot", "hotter", "temperature", "setting", "thermostat", "turn up", "dial",
                "degrees", "how hot", "what", "should", "celsius", "too hot", "scald")),
              "Sixty degrees on the cylinder thermostat is the number to aim for. A stored "
              "cylinder is held at 60 to 65C because below about 50C the bacteria behind "
              "Legionnaires' disease can multiply in the tank, and a thermostatic mixing valve on "
              "the outlet then brings it down to about 48C at the tap so nobody scalds. A combi "
              "has no tank, so set its hot water to 50 to 55C - hotter only burns gas and scales "
              "the plate heat exchanger faster. If the water comes out warm rather than cold, the "
              "setting is the thing to raise; if it starts hot and cools, the setting is fine and "
              "the fault is flow rate or a scaled exchanger.",
              # the cooking temperatures, the baby's bath, the washing machine and the greenhouse
              # are other questions with their own numbers
              avoid=("oven", "chicken", "meat", "pork", "turkey", "beef", "lamb", "sausages",
                     "roast", "bake", "bread", "dough", "sourdough", "yeast", "yoghurt", "yogurt",
                     "baby", "babies", "bath for the baby", "bottle", "formula", "breast milk",
                     "milk", "washing machine", "wash", "washing", "radiator", "radiators",
                     "heating", "kettle", "hot tub", "jacuzzi", "pool", "swimming", "thermometer",
                     "fever", "temperature of my child", "child", "children", "greenhouse",
                     "propagator", "germinate", "seeds", "compost", "room", "bedroom", "bed"),
              bias=1),
        # The other side of the same fault: a cold tap that runs warm. "why is the cold tap warm"
        # was a "a plumber will spot it in minutes", "my cold water runs warm" was the stopcock
        # card and "cold water comes out warm" was a bare nod, because no row owns a cold supply
        # that is hot.
        entry("cold-tap-warm",
              (("cold tap", "cold taps", "cold water", "the cold water", "cold supply",
                "cold water is warm", "cold water runs warm", "cold water comes out warm",
                "cold water goes warm", "cold water is hot", "cold tap is warm",
                "cold tap runs warm", "cold tap is hot", "why is my cold tap warm",
                "why is the cold tap warm", "why is my cold water warm",
                "why is the cold water warm", "why is my cold water hot"),
               ("warm", "hot", "warmish", "lukewarm", "tepid", "not cold", "warm up", "warms up",
                "comes out", "runs", "why", "heating up", "boiling")),
              "A cold tap that runs warm is nearly always warm water getting into the cold pipe: a "
              "mixer tap or shower cartridge letting by, or a non-return valve that has failed, and "
              "in a house with a hot water cylinder a faulty mixing valve does the same. Feel the "
              "pipe under the sink - if it turns cold after a minute or two it is just the pipe run "
              "sitting warm in a cupboard, which is harmless; if it stays warm, have the check valve "
              "or cartridge replaced. If it is only the one tap, that tap is the culprit; if it is "
              "every cold tap, look at the cylinder, the mixing valve or the shared supply.",
              # the shower has its own card, and the rest of these are other questions entirely
              avoid=("shower", "showers", "pool", "swimming", "sea", "beach", "lake", "river",
                     "glass", "drink", "drinking", "bottle", "flask", "kettle", "hot water bottle",
                     "ice", "freezer", "fridge", "cooler", "hot tub", "jacuzzi", "radiator",
                     "radiators", "heating", "boiler", "overflow", "leak", "dripping",
                     "tap is dripping", "no hot water", "hot water", "hot tap", "hot taps",
                     "bath water", "washing"),
              bias=3),
        entry("heat-pump",
              (("heat pump", "heat pumps", "air source", "ground source", "heat pump work",
                "heat pump works", "what is a heat pump", "how do heat pumps work"),
               ("work", "works", "working", "how", "what", "explain", "worth", "idea", "good",
                "cost", "costs", "running", "cheaper", "replace", "boiler", "install", "noise",
                "loud", "cold", "any")),
              _heat_pump_answer,
              # a heat pump dryer, a heat pump dehumidifier or a heat pump hot water tank is
              # that appliance's question, and "is a heat pump dryer any good" was answered here
              # with how the refrigerant works.
              guard=_the_explainer_keeps_the_explainer,
              avoid=("car", "engine", "air conditioning", "fridge", "freezer", "microwave",
                     "washing machine", "dishwasher", "shower pump", "pool")),
        entry("batteries-in-the-bin",
              (("batteries", "battery", "old batteries", "used batteries", "aa", "aaa", "button cell",
                "lithium", "vape", "vapes", "disposable vape", "e-bike battery", "phone battery"),
               # "rubbish" is a verdict as often as it is a bin: "my phone battery is rubbish" was
               # answered with the recycling card, so only the bin sense of the word counts here
               ("bin", "bins", "the rubbish", "rubbish bin", "in the rubbish", "trash",
                "throw", "throw away", "throwing", "dispose",
                "disposal", "recycle", "recycling", "kerbside", "where do i put", "get rid",
                # the rest of the ways people say "I want this gone": the rubbish domain's own RID
                # list has them all and this row had five, so "what do i do with old batteries" and
                # "where do i take old batteries" came back as a shrug while "how do i get rid of
                # old batteries" answered properly.
                "do with", "where do i take", "where can i take", "drop off", "chuck", "toss",
                "the tip", "to the tip", "recycling centre", "scrap")),
              ("Not the bin: batteries are a fire risk in a lorry and in the tip. Most supermarkets and "
               "every council recycling centre have a battery box by the door, and button cells and "
               "lithium ones go in those too, with the ends taped. Vapes, e-bike and scooter batteries "
               "and power banks are the ones that actually start fires, so take them to a shop that "
               "sells them or to the tip, never the kitchen bin."),
              avoid=("car battery", "car", "laptop wont charge", "phone wont charge", "remote",
                     "smoke alarm", "hearing aid", "flat battery")),
        # "where is my stopcock" and "how do i turn the water off" were both punts, and they are the
        # two questions every other plumbing answer assumes have already been answered. The telling
        # words are stopcock/stop tap/stop valve, and the water-off shapes, which stand on their own.
        entry("stopcock", (("stopcock", "stop cock", "stop tap", "stop valve", "shut off valve",
                            "shutoff valve", "water valve", "mains valve", "isolation valve",
                            "water main", "mains water", "water meter", "turn the water off",
                            "turn off the water", "turn the water back on", "shut the water off"),
                           ("where", "find", "located", "how", "what", "turn", "shut", "off", "water",
                            "under the sink", "outside", "emergency", "leak", "leaking")),
              "It is usually under the kitchen sink where the cold main comes up, or in a box near the "
              "boundary outside, and it is a brass tap that closes clockwise: turn it a quarter turn at "
              "a time, run the cold tap to check it has stopped, and turn it back anti-clockwise "
              "afterwards. If it is seized, don't force it with a wrench - a rounded stopcock means "
              "turning the water off at the road, which is the water company's job.",
              # "water meter" is a key word here because the meter sits by the stopcock, and that
              # made every question with the phrase in it ask where the thing is: "is a water meter
              # cheaper", "will a water meter save me money" and "how much does a water meter save"
              # got its location, and a leaking meter got it too. Only the where-is-it shapes are
              # this row's; the money shapes are the water-bill row's.
              avoid=("worth", "worth it", "cheaper", "save", "saves", "saving", "expensive", "cost",
                     "costs", "how much", "should i", "should we", "leak", "leaks", "leaking",
                     # the same money shapes said as an ask for a view: "would you recommend a water
                     # meter" and "do you recommend a water meter" carry the buying words the row
                     # below answers with, and this one answered them with where the stopcock is.
                     # A recommendation is never a where-is-it question, so it stands the row down.
                     "recommend", "recommended", "recommendation", "recommendations",
                     "any point in", "any point to", "waste of money", "worth having",
                     "leaked", "drip", "dripping", "broken", "faulty", "frozen", "read my meter",
                     "meter reading", "smart meter",
                     # the gas has its own lever and its own card, and "where is the gas shut off
                     # valve" was the water stopcock answer for want of these
                     "gas shut off", "gas shutoff", "gas valve", "gas stop", "gas meter",
                     "gas supply", "gas pipe", "gas leak", "smell gas",
                     # "how do i get a water meter" is the meter question, not where the meter is:
                     # the location answer named the sink and said nothing about asking the company
                     "get a water meter", "get a meter", "getting a meter", "have a meter fitted",
                     "fit a meter", "fit a water meter", "install a meter", "free meter",
                     "switch to a meter", "ask for a meter", "water meter save",
                     # a heater, an immersion or a hot water tank has its own valve and its own
                     # answer, and "turn off the water heater" reached this row on the words
                     # "turn off the water" plus "how"
                     "water heater", "water heaters", "immersion", "immersion heater",
                     "hot water tank", "hot water cylinder", "water tank", "heater", "heaters",
                     "cylinder", "hot water"),
              bias=1),
        # Turning a radiator off is not a fault: it is the summer job, the spare room nobody heats,
        # and the radiator that is too hot to sit next to. Nothing on main answered it - the line
        # reached `paint-strip` (bare "off" plus the word radiator) or a plumber punt.
        entry("radiator-off",
              (("radiator", "radiators", "rad", "rads", "trv", "thermostatic valve",
                "radiator valve", "towel rail"),
               ("turn off", "turning off", "switch off", "switching off", "shut off",
                "shutting off", "turn it off", "switch it off", "turn them off",
                # "how do i turn down a radiator" and "my radiator is too hot" are main's own lines -
                # the numbered head, down a notch or two - and turning a radiator DOWN is not turning
                # it off, nor is a room that is too warm asking for the frost setting. The bare
                # "turn down" forms and the "too hot" shape are therefore not in this key at all, and
                # both lines keep the answer they had.
                "off for the summer",
                "off for summer", "off in the summer", "not using that room", "spare room",
                # "how do i turn a radiator off" has no "turn off" in it, because the thing is in
                # the middle: the noun and its off are the phrase people actually type
                "radiator off", "radiators off", "rad off", "rads off",
                "turn a radiator off", "turn the radiator off", "turn my radiator off",
                "switch a radiator off", "switch the radiator off", "shut a radiator off",
                "turn both radiators off")),
              "Turn the thermostatic head on the radiator down to 0 or to the snowflake, which is "
              "frost protection rather than fully off, and leave it there: that closes the valve "
              "against the room and the radiator goes cold the next time the heating runs. If it has "
              "an old wheel valve instead of a numbered head, turn it clockwise until it stops - the "
              "same valve a plumber would close - and turn both ends if you are taking the radiator "
              "off the wall. Don't shut the valves on a radiator in a room that gets damp or near "
              "freezing, because that is the one that needs the frost setting.",
              bias=1,
              # a leak, a cold radiator and a noisy one are faults with their own first move, and
              # paint is the stripping row's
              avoid=("leak", "leaking", "leaked", "drip", "dripping", "puddle", "bleed", "bled",
                     "cold", "noise", "noisy", "banging", "gurgling", "paint", "painting",
                     "strip", "removing", "bill", "bills", "save", "cheaper", "cost", "boiler",
                     "how long", "radiator key", "hot water")),
        entry("radiator-leak",
              (("radiator", "radiators", "rad valve", "trv", "thermostatic valve", "towel rail",
                # the valve is the part that leaks, and "how do i fix a leaky radiator valve" scored
                # nothing at all: "valve" was only reachable as "rad valve" or "trv"
                "valve", "valves", "lockshield", "bleed valve"),
               ("leak", "leaks", "leaking", "leaked", "leaky", "drip", "dripping", "weeping",
                "water", "puddle", "wet", "rusted", "rusty", "seeping")),
              "Turn both radiator valves off and put a towel and a bowl under it, then see whether the "
              "water comes from the valve nut or the radiator itself: a drip at the nut often stops "
              "with a quarter turn of a spanner on the gland, while water from the panel or a rusty "
              "seam means the radiator has gone and wants replacing. Don't overtighten a joint that is "
              "held by plastic pipe, and if the water is coming through the ceiling, turn the heating "
              "off and ring a plumber today.",
              bias=1,
              avoid=("buy", "best", "which", "cheapest", "size", "how many", "bleed", "bled", "cold",
                     "bottom", "noise", "banging", "boiler", "landlord", "tenant",
                     # "where is the valve on the hot water tank" was told to turn both radiator
                     # valves off: a tank's valve is not a radiator's
                     "water heater", "immersion", "immersion heater", "hot water tank",
                     "hot water cylinder", "water tank", "cylinder", "tank",
                     # radiators that heat up whenever the hot water runs are a stuck valve, not a
                     # leak: the word "water" was enough to make this the answer to that line
                     "hot water is on", "hot water comes on", "comes on when", "by itself")),
        entry("outside-drain", (("outside", "gully", "yard", "driveway", "pavement", "garden"),
                                ("drain", "blocked", "smell", "overflowing", "flooding")),
              ("Lift the drain cover and clear the gully of leaves and silt with gloves and a trowel, "
               "then flush it with a bucket of water. If it's still slow or smells after that, or it's "
               "the main sewer, ring your water company: blocked public sewers are usually their job and "
               "free to clear.")),
        # "sink" is in part one because the trap under a kitchen sink is where the hair and the fat
        # go; part two keeps it off the cleaning question ("how do i clean the sink").
        # A pair of scissors that will not cut is not the kitchen-cleaning routine, which was what
        # "how do i sharpen kitchen scissors" got from the word "kitchen" plus "how". A serrated
        # kitchen pair cannot be honed on a steel at all, which is why this has its own answer.
        entry("sharpening-scissors",
              # kitchen scissors only: a pair of garden shears is cut differently, and the answer
              # below is about the serrated edge a kitchen pair has
              (("scissors", "scissor", "kitchen scissors", "paper scissors", "safety scissors"),
               ("sharpen", "sharpening", "sharpened", "blunt", "dull", "wont cut", "won't cut",
                "doesnt cut", "doesn't cut", "dont cut", "don't cut", "not cutting", "cut properly",
                "jamming", "sticks", "tight")),
              "Look at the edge first: a serrated kitchen pair cannot be sharpened at all, and a "
              "smooth pair is done with a fine diamond file or a small whetstone, five or six light "
              "strokes along the bevelled side only, at the angle the bevel already has, then wipe the "
              "burr off with the flat of the stone. A stiff screw is usually the pivot, not the blade: "
              "a drop of oil and a quarter turn on the nut frees it. If the two blades no longer meet "
              "along their length, a repair shop re-grinds them for a few pounds, which is cheaper "
              "than a good new pair.",
              # garden tools are not a kitchen pair: shears, secateurs and hedge trimmers are in the
              # avoid list so "how do i sharpen garden shears" keeps its own answer
              avoid=("hair", "haircut", "cut my hair", "cut my own hair", "fringe", "topiary",
                     "hedge", "hedges", "lawn", "garden", "shears", "secateurs", "burglar",
                     "run with")),

        # A pool in the garden is emptied on purpose, and "how do i drain a paddling pool" was the
        # hair-in-the-trap card: "pool" and "pooling" are loose forms, and the row above read the
        # word without the thing it belongs to.
        entry("paddling-pool",
              # no "kids pool": "kids" is a key word of moving-with-kids and one more row using it in
              # this domain costs that row the rarity bonus it was getting ("how do i tell my kids
              # we're moving house" fell from moving-with-kids to screen-time)
              (("paddling pool", "paddling pools", "inflatable pool",
                "blow up pool", "blow-up pool", "paddling"),
               ("empty", "emptying", "emptied", "drain", "draining", "get rid", "tip", "tip out",
                "pour away", "water", "clean", "cleaning", "clean out", "store", "storing",
                "put away", "chlorine", "chlorinated", "how often", "change the water", "fill",
                "filling", "fill up")),
              "A paddling pool holds 300 to 800 litres, so buckets are the hard way: pull the drain plug "
              "if it has one, or lift one side and let it run into a drain or a big bucket, or hook a "
              "short hose over the lowest edge and syphon it out. Water that has only had children in "
              "it can go on the flower beds rather than the lawn, but water with chlorine or soap in it "
              "should go down a drain, since it scorches grass. Scrub the inside with hot soapy water, "
              "rinse, dry it in the sun and store it folded and dry, because a pool put away wet comes "
              "out black and slimy next summer.",
              # a swimming pool and a hotel pool are other questions, and a pool table is not water
              avoid=("swimming pool", "hotel", "lido", "leisure centre", "pool table", "pool cue",
                     "gene pool", "pool car", "football pool", "car pool")),
        # A hot tub is emptied and refilled on a schedule, and none of that was anywhere: "how do i
        # drain my hot tub" got the kettle-and-bicarbonate drain cleaner, "how often should i change
        # the water in a hot tub" got the garden's watering row, and "how do i clean my hot tub" got
        # the wash-temperature rule for a duvet. The tub is its own thing to keep, so it is its own
        # row: the water change is a schedule, and the way to empty it is a hose to a drain because
        # the chlorine kills the grass.
        entry("hot-tub-care",
              (("hot tub", "hot tubs", "hottub", "jacuzzi", "spa bath"),
               ("empty", "emptying", "emptied", "drain", "draining", "drained", "pump out",
                "pump it out", "siphon", "syphon", "change the water", "changing the water",
                "how often", "clean", "cleaning", "cleaned", "clean out", "flush", "flush out",
                "water out", "get the water out", "wont drain", "won't drain", "not draining",
                # the whole phrase, because "water" alone is the drinking-water rows' and "change" is
                # the bedding's: "how often should i change the water in a hot tub" was a hydration
                # answer about a long run
                "change the water in a hot tub", "change the water in my hot tub",
                "change the water in the hot tub", "change the hot tub water",
                "empty the hot tub", "drain the hot tub")),
              "Change the water every three to four months, or after about thirty uses, whichever "
              "comes first: a 4 to 6 person tub holds 1,000 to 1,500 litres, so check the level weekly "
              "with the hose and the chemicals, and do a full change when the water stops holding "
              "chlorine. To empty, hook a hose on the drain valve at the bottom into a drain, or drop a "
              "sump pump in, because a tub of chlorinated water kills the lawn and burns a border. "
              "Then flush the pipes with a line cleaner, wipe the shell with bicarbonate of soda rather "
              "than a detergent, and refill through the filter.",
              # a bath, a paddling pool and a swimming pool are other answers, and the heat questions
              # about a tub (how hot, is it safe, can a pregnant person use one) are not this one
              avoid=("bath", "baths", "bathtub", "shower", "paddling pool", "swimming pool",
                     "too hot", "how hot", "temperature", "pregnant", "pregnancy", "safe",
                     "safety", "heat rash", "warms up", "warm up time", "electrics", "electric",
                     "buying", "buy a", "worth it", "cost to run", "running cost", "cheap to run",
                     "cover", "lid", "steps", "chemcial", "chlorine level")),
        # "how do i empty a water butt" was a money row about a plan that went wrong, "how do i empty
        # my pond" was no answer at all, and "how do i empty a swimming pool" was told to start with
        # twenty minutes of lengths. All three are the same job - getting a lot of still water out of
        # something in the garden - and the sizes are what decide how, so one row answers all three.
        entry("empty-a-big-container",
              # no bare "pool": "pool" is the swimming pool's, the paddling pool's, the pool table's
              # and a puddle's, and the paddling pool row beside this one keys its own words
              # no bare "water tank": a loft tank, a header tank and a caravan tank are three other
              # jobs, and the garden water is what this row knows
              (("water butt", "water butts", "rain barrel", "rain butt",
                "pond", "ponds", "garden pond", "wildlife pond", "swimming pool", "swimming pools"),
               ("empty", "emptying", "emptied", "drain", "draining", "drained", "get the water out",
                "water out", "tip out", "tip it", "pump out", "pump it out", "siphon", "syphon",
                "get rid of the water", "hose out", "flush out",
                # the whole ask, because the butt's own row (how big a one to buy) keys the two words
                # and reads "empty a water butt" as a question about sizes
                "empty a water butt", "empty the water butt", "empty my water butt",
                "drain a water butt", "drain the water butt", "empty a pond", "empty the pond",
                "empty my pond", "drain a pond", "drain my pond", "empty a swimming pool",
                "empty the swimming pool", "empty my swimming pool", "drain a swimming pool")),
              "Run it to a bed or a drain, never the road, and let the size decide how: a water butt "
              "goes out of the tap at the bottom onto a hose, and a barrel with no tap is tipped on "
              "its side or syphoned with a hose kept full of water. A pond is emptied in autumn, not "
              "spring, when frogs and newts are in it: net the fish into buckets of pond water, keep "
              "the filter media wet in that water, and put the plants in a tray, because it goes back "
              "within a day. A swimming pool is "
              "20,000 litres or more, so it is a hired pump and a drain or a tanker, never the garden "
              "hose, and never the road drain without asking the council first.",
              # water in a garden is the watering row's, the pool for swimming is the stroke row's,
              # and a fish tank indoors is the tank's own answer
              avoid=("watering can", "irrigation", "sprinkler", "hose pipe ban", "fill", "filling",
                     "fill it", "install", "installing", "fit a", "fitting a", "diverter",
                     # no bare "swim" or "swimming" here: "a swimming pool" is the subject, and the
                     # stroke words below are what tell the two apart
                     "lengths", "lanes", "front crawl", "backstroke", "breaststroke", "lessons",
                     "learnt to swim", "learn to swim", "swim for fitness", "times a week",
                     "pool table", "pool cue", "hotel", "lido", "leisure centre", "gene pool",
                     "car pool", "fish tank", "aquarium", "toilet", "cistern", "radiator",
                     "boiler", "central heating", "header tank", "oil tank", "septic tank",
                     # a tank in a van or a boat is drained for the winter, and that is its own
                     # job: the caravan, the motorhome and the boat are named so this garden row
                     # does not answer them with a water butt
                     "caravan", "motorhome", "camper", "boat", "yacht", "narrowboat", "canal",
                     "van", "campervan")),
        entry("drain-blocked", (("drain", "shower", "shower tray", "bath", "plughole", "plug hole",
                                "sink", "basin", "handbasin", "washbasin", "tub", "bathtub"),
                                ("blocked", "blockage", "slow",
                                 # "why is my bath draining so slowly" reached the eat-slowly row,
                                 # because "drains slowly" is a phrase and nothing matched
                                 # "draining ... slowly": the verb and the adverb are own words
                                 "slowly", "draining", "drains", "drain", "clogged", "clog",
                                 # the rest of the clog family, which is how most people say it:
                                 # what main did not have was the verb and its -ed and -ing forms
                                 "clogs", "clogging", "clogged up", "unclog", "unclogging",
                                 "unclogged",
                                 # "why does my bath take so long to drain" and "the sink takes
                                 # ages to drain" are the same slow waste pipe, said with a time
                                 "so long to drain", "long to drain", "takes ages",
                                 "taking ages", "takes ages to drain", "ages to drain",
                                 "smells", "smell", "clear", "unblock",
                                 # a fixture that is choked is blocked, not breathing: "my bath is
                                 # choked" and "the shower is choked" are the hair-in-the-trap fault
                                 "choked", "choking", "chokes",
                                 "backed up", "not draining", "won't drain", "wont drain",
                                 "isnt draining", "isn't draining", "doesnt drain", "doesn't drain",
                                 # a tray of standing water is the same hair-in-the-trap fault as a
                                 # slow drain, and "the shower tray keeps filling with water" was an
                                 # echo because none of the words above are in it
                                 "fills with water", "filling with water", "fills up", "filling up",
                                 "keeps filling", "keeps filling with water", "water sits",
                                 "sits in the", "pooling", "pools", "puddle in", "wont empty",
                                 "won't empty", "not emptying", "goes down slowly",
                                 "drains slowly", "slow to drain", "standing water",
                                # hair is what blocks a plug hole, and saying so is the way most
                                # people describe the job ("how do i get hair out of the plughole")
                                "hair", "hairs",
                                # "what can i put down a smelly drain" named no action the second
                                # group knew, so it fell to the tiredness entry on "drained"
                                "smelly", "stinks", "stink", "put down", "pour down",
                                "drain cleaner", "through the drain", "down the drain")),
              ("Pull the hair and soap out of the trap first (a bent wire or tweezers does it), then "
               "pour a kettle of hot water down with a spoonful of bicarbonate of soda and vinegar; a "
               "plunger over the plughole clears the rest. Skip the chemical cleaner until last, and "
               "fill the trap with a hair collector so it does not come back. The reason is hair, "
               "soap and grease caught in the trap and the bend."),
              # a cistern that will not stop filling, or a tank, is another answer: "keeps filling"
              # belongs to this entry only when the water is going the wrong way, down a waste
              avoid=("outside", "gully", "driveway", "street", "pavement", "machine",
                     "washing machine", "dishwasher", "dryer", "washer", "freezer", "fridge",
                     "toilet", "toilets", "cistern", "ball valve", "ballcock", "tank", "loft",
                     "boiler", "radiator", "radiators", "central heating", "header tank",
                     # "pooling" is a loose form of "pool", so a pool emptied on purpose reached the
                     # hair-in-the-trap card: "how do i drain a paddling pool" wanted the plug or a
                     # hose and a bucket, and nothing here knows that
                     "paddling pool", "swimming pool", "hot tub", "water butt", "garden pond")),
        # Clearing a drain is one question; what may go down it is another, and every "can i put
        # oil down the drain" was answered with the trap and the plunger. The question words are in
        # the key because the fault words are not: a blocked drain is the row above, and this one
        # only ever speaks for a line that asks whether something may go down.
        entry("down-the-drain",
              (("down the drain", "down the sink", "down the plughole", "down the plug hole",
                "down the toilet", "down our drain", "down my drain", "into the drain",
                "into the sink", "flush", "flushed", "flushing", "down the loo"),
               ("can i", "could i", "should i", "is it ok", "is it okay", "ok to", "okay to",
                "safe", "safe to", "allowed", "what can i", "what should i", "what shouldnt i",
                "what should not", "anything", "never", "not to", "which things", "what things")),
              "Four things never go down a drain: fat, oil and grease (they cool, set and make "
              "fatbergs), wet wipes even the ones marked flushable, anything that swells or sets - "
              "rice, pasta, potatoes, flour, eggshells and pastry scraps go down soft and pack hard "
              "a metre along - and paint, thinner and the chemicals that go with them. Fat goes into "
              "a jar or the bin, wipes and grounds into the bin, rice and peelings into the food "
              "waste with a sieve in the plug for the last rinse. A toilet takes the three Ps and "
              "nothing else: pee, poo and paper. Soapy water, tea, milk and small crumbs are fine.",
              # a drain already blocked is the row above, and a machine or a tank is another
              avoid=("blocked", "blockage", "backed up", "wont drain", "won't drain",
                     "not draining", "smells", "smelly", "clear", "unblock", "plunger",
                     "washing machine", "dishwasher", "dryer", "machine", "boiler", "radiator",
                     "freezer", "fridge", "oil out", "pour old", "old oil", "recycle",
                     # bleach and coffee grounds have a card of their own that says more than a
                     # list can: the bleach one names the chlorine gas, and grounds are worth
                     # composting. "anything chemical" in the reply above would deny the bleach
                     # card's "a capful a week is fine", so the list stands down for both.
                     # "coffee ground" and not "coffee": a bare "coffee" fenced the list for
                     # "can i put coffee down the drain" as well, and that line has no card of its
                     # own, so it was left to the blocked-drain plunger.
                     "bleach", "bleaches", "caustic", "coffee ground", "used coffee",
                     "spent coffee", "coffee grouts",
                     # a cistern that will not stop is a fault, not a thing going down: "what
                     # should i do about the toilet flushing all night" got the list of things
                     # that never go down a drain, and the running-toilet row has the valve.
                     "keeps flushing", "constantly", "all night", "all day", "wont stop",
                     "won't stop", "keeps running", "running", "dripping",
                     # the fat in a roasting tin has a card that says how to get rid of it -
                     # wipe it out with kitchen paper while the pan is warm - and the list took
                     # that line away from it
                     "roasting tin", "roasting tray", "roasting pan", "baking tray",
                     "kitchen paper", "wipe the fat", "fat from the"),
              # a thing asked about before it goes down ("can i flush wet wipes down the toilet")
              # is this list, and the toilet row keys the same "flush": this row is the specific
              # one of the two, so it outranks the plunger rather than the plunger being stood down
              bias=3),
        # A cycle that takes hours is the most common thing people ask about a washer after a fault,
        # and it was the honest hedge. The length of a cycle is a fact, not a fault, and the reason it
        # runs long is the same on every machine.
        entry("wash-cycle-time",
              (("washing machine", "washer", "washing", "wash"),
               ("how long", "take so long", "takes so long", "so long", "hours", "an hour",
                "cycle", "cycle time", "wash cycle", "washing cycle", "long cycle", "eco",
                "quick wash", "30 minute", "15 minute", "how many minutes", "duration",
                "length of a cycle", "normal wash", "cotton wash", "eco wash", "express wash",
                "spin", "spin cycle", "rinse cycle", "drain cycle", "programme", "program")),
              "Most cycles are two to three hours on eco and about an hour on a normal 40C cotton "
              "wash, and nothing is wrong: eco runs the drum slowly and heats the water slowly so it "
              "uses less electricity, which is why the eco label says 3 hours plus. The quick washes "
              "are 15 to 30 minutes and are meant for a small, lightly worn load. A cycle that runs "
              "longer than the dial says is usually a cold fill taking ages, a blocked filter, or "
              "extra rinses switched on, so check the filter and the rinse setting before calling "
              "anyone.",
              # "wash" and "cycle" are both ordinary words elsewhere: a wash of a car, a cycle ride
              # to work ("how long does a wash cycle take" was the exercise-after-illness answer).
              # The machine words are what the line has to carry.
              avoid=("dishwasher", "tumble dryer", "dryer", "oven", "last", "lasts", "lasting",
                     "lifespan", "life span", "life expectancy", "replace", "often",
                     "car", "cars", "van", "bike", "bicycle", "motorbike", "dog", "dogs", "pet",
                     "hair", "hands", "face", "dishes", "windows", "walk", "run", "running",
                     "swim", "swimming", "gym", "exercise", "ill", "sick", "cold", "flu",
                     "cycle to work", "cycle ride", "bike ride", "ride to work",
                     # a pan being cooled so it can be washed is not a wash cycle: "how long should i
                     # cool a pan before washing" matched "washing" and "how long" and got the drum
                     "pan", "pans", "wok", "skillet", "saucepan", "pots", "cookware",
                     "washing up", "wash the pan", "before washing",
                     # a repair is a job on the machine, not a wash it runs: "how long does a
                     # washing machine repair take" was the eco cycle times, and the repair clock
                     # - one visit, an hour or two on site, the wait is the part - is the answer
                     # it wanted. The machine and the repair have to be said together: a bare
                     # "a repair" after a fault is the fault row's, which is a separate question
                     "washing machine repair", "washer repair", "machine repair",
                     "repair man", "repairman", "engineer", "call out", "callout",
                     "spare part", "spare parts",
                     # how long the washing takes to DRY is the drying question, not the cycle:
                     # "how long does washing take to dry indoors" was answered with the eco
                     # cycle times, which is a different length of time
                     "to dry", "dry indoors", "dry inside", "drying indoors", "drying inside",
                     "to dry it", "hang out", "hanging out", "on the line", "air dry"),
              ask=("how long", "so long", "hours", "cycle", "take", "takes", "duration"),
              # a machine that stopped part way through is a fault, and its own rows have the
              # door latch and the drain: "my washing machine stopped mid cycle" was answered
              # "most cycles are two to three hours ... and nothing is wrong", which reads like a
              # diagnosis and is not one. The guard is home.py's, so every symptom added to the
              # fault words there stands this row down too.
              guard=_not_a_machine_that_has_gone,
              bias=4),
        # "can i hang washing out today" was the length of a wash cycle, because "washing" and
        # "today" are both in that row's reach and the machine was never mentioned. Hanging it out
        # is a different question with a different answer, and it is the one a washday starts with.
        entry("washing-outside",
              # Not the bare word "bedding": `lookup._forms` un-doubles it to "bed" the way
              # "running" gives "run", so a bed in the line satisfied it and "get out of bed" was
              # answered with the drying weather. Saying it with an article or a possessive is the
              # whole fix - "the bedding", "my bedding", "bedding dry" is the thing that hangs out
              # and never the bed - and the bare word has to go with it or the row loses its own
              # question: "i want to get the bedding dry outside today" then "what time should i
              # put it out" was answered indoors, on a deck row (`intent-putting-out-when`) that
              # main had right. Not "whites" either, for the same reason in the other direction:
              # `_forms("whites")` holds "white", so "my hands go numb and white in the cold"
              # matched on the colour and the weather words finished the row. "the whites" alone
              # then lost the commonest way people say it - "my whites" was named in this comment
              # and not in the key, so "can i put my whites on the line" got a punt - so the
              # possessive forms and two-word ones ("whites dry", "whites out") are in the key
              # beside it. None can be the colour: each carries a word the colour is never said
              # with, and "my hands go numb and white" says none of them.
              (("washing", "washing line", "laundry", "clothes", "wash", "the whites",
                "my whites", "our whites", "whites dry", "whites out", "sheets",
                "towels", "the bedding", "my bedding", "bedding dry"),
               ("hang", "hanging", "out", "outside", "line", "dry", "drying", "dried", "today",
                "tomorrow", "outside today", "put out", "airing", "airer", "weather", "rain",
                "raining", "wind", "windy", "sun", "sunny", "frost", "cold", "winter", "summer",
                "dryer", "tumble")),
              "A dry, breezy day dries a normal load outside in two to four hours, and a cold sunny "
              "day with wind is nearly as good as a warm one, so 8C and breezy beats 20C and still. "
              "Rain, fog and damp evening air put the water back, so bring it in before dusk. In "
              "winter, spin it an extra five minutes, then dry it indoors on an airer with a window "
              "open a crack: the water has to go somewhere, and an open window is cheaper than the "
              "heating.",
              # A spot on one thing is not a load to dry: "how do i get a stain out of a white
              # shirt", "how do i get blood out of a white shirt" and "how do i get red wine out
              # of a white shirt" all reached this row, because "whites" folds to "white" and the
              # line has an "out" in it, and were told the weather for a washday. The stain rows
              # answer those, and the words below are the ones a spot is said with.
              avoid=("stain", "stains", "stained", "staining", "spot", "spots", "marked",
                     "blood", "grass", "red wine", "wine", "coffee", "tea", "ink", "mud",
                     "vomit", "sick", "bleach", "bleached", "yellow", "yellowed", "sweat",
                     "grease", "oil", "curry", "tomato", "chocolate", "pen", "marker",
                     "out of a white", "out of my white", "out of the white", "out of whites",
                     # a fault, a smell, a leak or a cycle length is the machine's question, and
                     # the machine row answers it better than the weather
                     "washing machine", "washer", "not spinning", "wont spin", "won't spin",
                     "smell", "smells", "smelly", "musty", "mould", "mold", "leak", "leaking",
                     "drain", "filter", "cycle", "programme", "program", "eco wash", "spin speed",
                     "broken", "repair", "error code", "fault",
                     # "out" is one of this row's key words, so a load that came out of the
                     # machine wet was answered with the weather, and so was a stain asked as
                     # "how do i get the oil out of clothes". A wet load is the machine's
                     # question; a stain has its own card. The words that say so stand this
                     # row down, and the guard reads a line like "dry clothes without a tumble
                     # dryer" as it was typed.
                     "come out", "comes out", "came out", "coming out", "get out", "got out",
                     "getting out", "remove", "removing", "dirty", "smell out",
                     # A stain is a spot-clean question about one thing, not a question about the
                     # weather: "how do i get sweat stains out of a white shirt" was answered with
                     # "a dry, breezy day dries a normal load outside in two to four hours", because
                     # "whites" and "out" are both in this row's keys and the stain row's own words
                     # scored lower. The stain rows in clothing.py own these lines.
                     "stain", "stains", "stained", "sweat", "sweaty", "ink", "blood", "grass",
                     "grease", "oil", "sauce", "coffee", "tea stain", "wine", "mud", "makeup",
                     "deodorant", "bleach mark"),
              guard=_not_a_drying_inside_question,
              bias=3),
        entry("washing-machine-smell", ("washing machine", ("smell", "musty", "smelly", "clean",
                                                            "smells")),
              # The cause is its own short sentence after the fix, because "why" after this answer
              # is the commonest follow-up and the cause read out of the answer is what it gets: a
              # reply that only names the wash gets the shrug instead. The fix stays the first
              # sentence, so "what should it be" and "tell me more" still find it.
              "Run a hot 60C or 90C service wash with a washing-machine cleaner or a cup of "
              "bicarbonate of soda, and clean the filter and the detergent drawer while it runs. The "
              "smell lives in damp lint and detergent trapped in the seal, the drawer and the filter. "
              "The wash itself is about two hours. Leaving the door and drawer open between washes "
              "is what stops the smell coming back."),
        # Mould in the machine is its own question: the smell answer is a service wash, but the
        # mould lives in the fold of the rubber door seal, the detergent drawer and the filter, and
        # saying "run a hot wash" alone leaves the person with the same black line next month.
        # On main `ca942da` the line reached the football boot that has moulded studs instead.
        entry("washing-machine-mould",
              (("washing machine", "washer", "washing mashine", "washer dryer", "tumble",
                "laundry", "drum", "detergent drawer", "door seal"),
               # no bare "clean": "how do i clean my washing machine properly" is the service wash,
               # and this row is for the mould the wash does not lift out of the seal
               ("mould", "mold", "mouldy", "moldy", "mildew", "black mould", "black mold",
                "smells of mould", "smell of mould", "smells mouldy", "spores", "drawer",
                # not a bare "filter": a machine's filter is the hatch and the bowl, which has its
                # own row, and "how do i clean a washing machine filter" was being answered with the
                # black in the seal. A mould word carries every mould-in-the-filter line on its own.
                "detergent drawer", "seal", "door seal", "rubber",
                # not the smell words "damp" and "musty": "my washing machine smells of damp" is
                # the service wash, and the follow-up about the filter is read out of that answer
                # the plain asking shapes: they are safe here because the first part is the machine,
                # so "how do i get rid of mould" without a machine in it never reaches this row
                # not "how do i": that alone made "how do i clean my washing machine" the mould
                # answer, and the general clean is the service wash
                "get rid", "rid of", "remove", "removing", "kill", "coming back",
                "keeps coming back")),
              ("The black comes back because it lives in the fold of the rubber door seal, so that is "
               "the bit to clean: pull the seal open, wipe the fold with a cloth and a little white "
               "vinegar or a mould spray, and dry it. Then run the hottest empty wash the machine has "
               "with a machine cleaner or a cup of bicarbonate of soda, clean the detergent drawer and "
               "the filter out, and leave the door and the drawer open between washes so the drum "
               "dries. Use liquid detergent rather than powder at low temperatures and stop leaving "
               "wet washing in the drum. A seal that is black right through and slimy will not clean "
               "up: it is a cheap part and an easy swap."),
              # "how do i stop the machine smelling of damp" is the smell row, and a drum that will
              # not drain or leaks is not a mould question
              avoid=("leak", "leaking", "puddles", "wont drain", "won't drain", "not draining",
                     "wont spin", "banging", "noisy", "error code",
                     # "door seal" is in the key above, so a fridge, a freezer or an oven brought its
                     # own door seal here: "my fridge door seal is broken" was told to wipe the fold
                     # with white vinegar. A machine that is not in the key at all is not this row.
                     "fridge", "freezer", "oven", "dishwasher", "microwave", "fridge freezer",
                     # "my washing machine smells of damp" is the service wash: the smell of damp
                     # and a musty machine are the smell row's, and only the word mould is this one's
                     "damp", "musty", "damp smell", "smells of damp", "smells musty",
                     # a machine's filter has its own row and its own job: "how do i clean the
                     # filter" is not the mould in the seal, but "mould in the filter" is
                     "clean the filter", "cleaning the filter", "clean out the filter",
                     "empty the filter", "unblock the filter", "clear the filter"),

              bias=1),
        # A washer that runs the wash stone cold is a real fault and it had no card at all: the
        # line came back as a greeting once the leak row stopped taking the bare word "water",
        # and before that the drain row took it and talked about the filter. The heating half of
        # the machine is the element, the thermostat that reads the water and the relay on the
        # board, in that order of likelihood.
        entry("washing-machine-not-heating",
              (("washing machine", "washer", "washer dryer", "washing mashine", "wash cycle",
                "wash", "machine"),
               ("not heating", "isnt heating", "isn't heating", "not heat", "doesnt heat",
                "doesn't heat", "didnt heat", "didn't heat", "wont heat", "won't heat",
                "not getting hot", "isnt getting hot", "isn't getting hot", "wont get hot",
                "won't get hot", "cold wash", "stays cold", "water stays cold", "stone cold",
                "no hot water", "heat", "heating")),
              "Check the programme first: a 30C or a cold wash never heats much, and many machines "
              "have a cold-only option that stops the element coming on. If it is a hot programme and "
              "the door glass is still cold after twenty minutes, the element is the usual cause - a "
              "cheap part that an engineer swaps in half an hour - and the thermostat that reads the "
              "water or the relay on the board are the next two. A machine that heats on some "
              "programmes but not others is a board fault, not the element.",
              # a dryer that will not heat, a house with no hot water and a machine that will not
              # empty or is full of water are all different questions with their own answers
              avoid=("tumble dryer", "tumble drier", "dryer", "drier", "dishwasher", "dish washer",
                     "radiator", "radiators", "boiler", "central heating", "house", "shower",
                     "tap", "taps", "immersion", "hot tub", "not draining", "wont drain",
                     "won't drain", "blocked", "clogged", "full of water", "smells", "smelly",
                     "buy", "which", "best", "cheapest", "price", "worth it", "filter")),
        entry("washing-machine-leak",
              (("washing machine", "washer", "washer dryer", "washing mashine"),
               # "floor" alone was a leak key, so a machine that bangs and walks across the floor was
               # answered with the leak: it is the water on the floor that is the leak
               ("leak", "leaking", "leaks", "leaked", "puddle", "puddles", "water", "dripping",
                "flooding", "on the floor", "all over the floor", "under the machine",
                "underneath the machine", "under it")),
              "Stop the cycle, unplug it and turn the water off at the valve behind it, and leave it off "
              "until the leak has stopped. Water at the front is usually the door seal or the filter cap, "
              "water underneath is the pump or a loose inlet or drain hose, so check the hose "
              "connections before you call anyone. A leak from inside the machine itself is an "
              "engineer's job.",
              # a drum that will not empty, or one standing full of water, is the drain entry's line:
              # both of those hold the word "water" and this entry would otherwise take them
              guard=_the_leak_is_a_machines,
              # the laundry-sorting row keys "washing" and ranks level with this one, so water on
              # the floor beside the machine was the sorting card: the guard above is what keeps
              # this bias from reaching a line that only mentions the water
              bias=2,
              avoid=("buy", "which", "best", "cheapest", "washing machine buy",
                     "wont drain", "won't drain", "not draining", "empty", "emptying",
                     "wont empty", "won't empty", "full of water", "water in the bottom",
                     "standing water", "sitting in the bottom", "sitting in", "sitting water",
                     "holding water", "holds water", "filter", "pump")),
        # --- how much life a boiler has left ------------------------------------
        # "my boiler is 15 years old" and "the boiler is going to die on us" were both shrugs on main
        # `d310ab7`, and "how long does a boiler last" got the engineer's-call-out answer, which is
        # not the question: an age is a planning question, not a fault.
        entry("boiler-age",
              (("boiler", "boilers", "combi", "central heating"),
               ("how long", "last", "lasts", "how old", "old", "years", "15 years", "age", "die",
                "dying", "on its way out", "end of its life", "replace", "replacing", "replacement",
                "new boiler", "worth", "efficient", "efficiency", "lifespan", "life span",
                "how much longer", "keep going", "go on for")),
              ("A boiler is built for about 10 to 15 years, so at 15 it is at the end of its life even "
               "if it is working today - the useful thing now is to have the money ready rather than "
               "be without heat in January. Get it serviced, keep the service record, and start "
               "collecting two or three quotes in the quieter months, because a combi swap is roughly "
               "2,000 to 3,000 pounds fitted and it is the same job whether you are desperate or not. "
               "A modern condensing boiler is around 90 per cent efficient against 70 to 80 for an "
               "old non-condensing one, which is the part of the bill you get back; a well-kept "
               "boiler that still works does not have to be replaced on age alone, but plan for it "
               "rather than wait for the morning it dies."),
              # a fault is boiler-broken's answer, a service is its own, and the cost of a new one is
              # the quote question: an age is a planning question
              avoid=("broken", "broke", "leak", "leaking", "pressure", "no hot water", "no heating",
                     "noise", "noisy", "kettling", "error", "fault", "reset", "not firing",
                     "wont fire", "service", "serviced", "servicing", "annual", "insurance", "cover",
                     "radiator", "radiators", "thermostat", "timer", "smart",
                     # a heat pump weighed against it is the choice between the two, which is the
                     # heat-pump row's answer: this one is about how long a boiler lasts
                     "heat pump", "heat pumps", "air source", "ground source") + JOB_GUARD,
              bias=1),
        # --- how long the job takes, not how long the machine lasts --------------------------------
        # "how long does a boiler repair take" was answered with a boiler's ten to fifteen years and
        # "how long does a fridge repair take" with four days of cooked food: an appliance and a clock
        # were in the line, so a clock entry took it (urban-orange, quality). JOB_GUARD stands those
        # rows down and this one answers the question that was asked - the visit, the part, the day.
        # --- how long a new one takes to fit, which is a longer job than the repair ---------------
        # "how long does it take to fit a new boiler" was a hedge on main `b7527cf`: the repair-time
        # row is keyed on the job words a visit is asked with (repair, fix, install), and "fit" and
        # "replace" were not among them, so the line reached no row at all. The fitting is the longer
        # job of the two and it is the one people plan a day off for, so it has its own row: the swap,
        # the day, and the gas check the repair row's last sentence only mentions in passing.
        entry("swap-time",
              (("boiler", "boilers", "combi", "central heating", "fridge", "fridge freezer",
                "freezer", "washing machine", "washer dryer", "tumble dryer", "dishwasher",
                "oven", "cooker", "hob", "radiator", "radiators", "shower", "shower pump"),
               ("new", "new one", "fit", "fits", "fitting", "fitted", "swap", "swaps", "swapping",
                "replace", "replaces", "replacing", "replacement", "install", "installs",
                "installed", "installation")),
              "Fitting a new one is the long job, not the short one: an hour or two for a washing "
              "machine or a dishwasher, about an hour a radiator once the system is drained, and a "
              "boiler is the big one - usually a full day plus the gas check at the end. Ask when you "
              "book whether the price includes taking the old one away, the gas safety check and any "
              "making good, because those are the parts that turn a quote into a bigger bill.",
              ask=("how long", "long does", "how many days", "how many hours", "days", "hours",
                   "wait", "time", "take", "takes", "taking", "long will"),
              avoid=("last", "lasts", "lasting", "years", "lifespan", "how old", "cost", "costs",
                     "much", "price", "prices", "quote", "quotes", "cheap", "cheaper", "expensive",
                     "worth", "pay", "broken", "broke", "dead", "leak", "leaking", "no hot water",
                     "no heating", "pressure", "fault", "error", "not working", "stopped", "reset",
                     "noise", "noisy", "kettling", "service", "serviced", "servicing", "annual") ,
              bias=1),
        entry("repair-time",
              (("boiler", "boilers", "combi", "central heating", "fridge", "fridge freezer",
                "freezer", "washing machine", "washer dryer", "tumble dryer", "dishwasher",
                "oven", "cooker", "hob", "radiator", "radiators", "shower", "shower pump",
                "hot water", "heating", "electrics", "electrician", "plumber", "tradesman"),
               ("repair", "repairs", "repaired", "fix", "fixes", "fixed", "fixing", "install",
                "installs", "installed", "installation", "engineer", "plumber", "call out",
                "callout", "call-out", "come out", "coming out", "swap", "swapping", "job")),
              "Most jobs are done in one visit: an hour or two on site for a repair, and the wait is "
              "usually the part, so if something has to be ordered expect a few days between the "
              "first call and the fix. Ask when you book whether the price covers the first hour and "
              "whether the part is included, and get the call-out fee before anyone comes out. A "
              "boiler swap is the long one - usually a full day, plus the gas check afterwards.",
              ask=("how long", "long does", "how many days", "how many hours", "days", "hours",
                   "wait", "time", "take", "takes", "taking", "long will"),
              avoid=("service", "serviced", "servicing", "annual", "cost", "costs", "much", "price",
                     "prices", "quote", "quotes", "cheap", "cheaper", "expensive", "worth", "pay",
                     # a fault line belongs to the fault row: "my boiler is broken, how long will the
                     # repair take" wants the pressure gauge and the reset before the calendar
                     "broken", "broke", "dead", "leak", "leaking", "no hot water", "no heating",
                     "pressure", "fault", "error", "not working", "stopped", "reset", "noise",
                     "noisy", "kettling", "last", "lasts", "lasting", "years", "lifespan"),
              bias=1),
        entry("boiler-broken", ("boiler", ("broken", "break", "breaks", "broke", "dead", "not working",
                                            # the everyday ways of saying a machine has stopped, which
                                            # this row did not name: "my boiler has packed in" got
                                            # "Ugh, those are fiddly" and no help at all
                                            "packed in", "packed up", "packing in", "has packed",
                                            "given up", "gave up", "conked out", "conk out",
                                            "on the blink", "gone wrong", "playing up", "acting up",
                                            "knackered", "has died",
                                            "stopped", "repair", "repairing", "repairs", "fixing",
                                            "no hot water", "no heating", "noise", "noisy",
                                            "kettling", "reset", "not firing", "wont fire", "wont start",
                                            "wont come on", "firing", "cutting out", "cuts out",
                                            "cutting off", "locks out", "lockout", "shutting",
                                            "not responding", "thermostat", "morning", "fault",
                                            "error", "cold",
                                            # "my boiler is not heating the water" named no hot water
                                            # and no leak, so it fell through to boiler-leak on the
                                            # bare word "water" and was told to put a bowl under it
                                            "not heating", "isnt heating", "isn't heating",
                                            "heating the water", "heating water", "not hot",
                                            # a boiler that switches itself off is this answer, not
                                            # the generic appliance card
                                            "switches itself off", "switching itself off",
                                            "turns itself off", "turning itself off",
                                            "keeps switching off", "keeps turning itself off",
                                            # a boiler that is on but not heating the water
                                            "not heating", "isnt heating", "isn't heating",
                                            "not getting hot", "not warming", "heating water",
                                            "heat water",
                                            # "the boiler is on but nothing happens" is the same
                                            # no-heat morning said as an absence: the symptom is that
                                            # nothing happens, and without these two phrases the line
                                            # only had the word "boiler" to go on and fell through
                                            "nothing happens", "does nothing", "nothing at all")),
              "Check the pressure gauge (1 to 1.5 bar), the thermostat and the boiler's reset button, "
              "and make sure the programmer is on the hour you think it is; a pressure top-up or a reset "
              "fixes a lot of no-heat mornings. The checks take ten minutes. In a cold snap, the white "
              "condensate pipe outside can "
              "freeze and stop the boiler, so pour warm water along it. If it locks out twice, or you "
              "smell gas, stop and call a Gas Safe engineer: gas is not a DIY job.",
              # A quote is a price question, not a symptom: "i got a quote for 1,500 to fix the boiler,
              # does that sound right" wants a way to check a price, and the composer has a line for it.
              avoid=("landlord", "tenant", "letting agent", "rent", "deposit",
                     "quote", "quoted", "quotes", "estimate", "estimated", "invoice",
                     # a kettle in the kitchen is not a sick boiler, even straight after a boiler
                     # question: "how long does it take to boil a kettle" was this card
                     "kettle", "kettles", "boil a kettle", "tea", "coffee"),
              ask=("boiler", "heating", "hot water", "radiator", "radiators")),
        # "no heating" and "the heating isnt working" name no boiler at all, so `boiler-broken` (which
        # needs the word) stood down and a cold house got "Great - shout if you need anything else".
        # The same three-word shape as `no-hot-water`: the phrase itself is the key, and the second
        # group repeats the subject so a line with no verb in it still has two words to score on.
        entry("no-heating",
              (("no heating", "heating is off", "heating gone off", "heating has gone off",
                "heating not working", "heating isnt working", "heating isn't working",
                "heating has stopped", "heating stopped", "heating wont come on",
                "heating won't come on", "heating wont fire", "heating won't fire",
                "heating is broke", "heating broke", "radiators are cold", "radiators cold",
                "radiators not hot", "radiators wont heat", "radiators won't heat",
                # "my heating is broken" was the one plain way of saying it that this row missed,
                # and it echoed the line back. "broken" and "dead" alone are too common to key, so
                # the shapes are named whole, and the thermostat gets the same treatment because
                # "my thermostat is not working" is the same cold house with a different subject.
                "heating is broken", "heating broken down", "heating has broken down",
                "heating is dead", "heating has died", "heating is bust",
                "heating is not working", "heating not coming on", "heating is not coming on",
                "heating isnt coming on",
                "heating isn't coming on", "heating wont turn on", "heating won't turn on",
                "central heating is not working", "central heating isnt working",
                "central heating has stopped working", "central heating has packed up",
                "thermostat is not working", "thermostat not working", "thermostat is broken",
                "thermostat broken", "room thermostat is not working",
                "no heat", "heating keeps going off",
                "heating keeps cutting out", "heating cuts out", "heating keeps turning off",
                "heating comes on and off", "heating has packed up",
                # the fault told as a length of time is the commonest way to say it, and the refund
                # ladder used to take it on "broken" plus "weeks": "the heating has been broken for 3
                # weeks", "the hot water has been off for a week", "the heating has been out since
                # tuesday". The goods row stands down for "heating" and "hot water" now, so without
                # these the cold house got "tell me what it does".
                "heating has been broken", "heating has been off", "heating has been out",
                "heating has been dead", "heating has been cut off", "heating has been turned off",
                "heating is off", "heating hasnt worked", "heating hasn't worked",
                "heating has not worked", "heating hasnt been working", "heating hasn't been working",
                "heating has not been working", "heating stopped working", "heating isnt heating",
                "hot water has been off", "hot water has been out", "hot water has gone off",
                "hot water is off", "no hot water for", "no heating for", "no heating since",
                "heating has not come back on", "heating hasn't come back on"),
               # no bare house/flat/cold here: "my house is cold" and "my flat is freezing" are the
               # keep-the-house-warm-for-less answer, and a heating fault is a heating word
               ("heating", "radiator", "radiators", "boiler", "thermostat", "central heating",
                "room thermostat", "winter", "morning", "why", "fix", "check",
                # "the hot water has been off for a week" names the fault and nothing else, so the
                # second word has to be the hot water itself or the line gets an echo back instead
                # of the cold-house card. It only counts with a fault already named above.
                "hot water",
                # "what are my rights" and "what can i do" are the follow-up to a fault that has
                # dragged on, and this card is the one that says who has to put it right
                "rights", "what can i do", "who do i call", "get it sorted", "get it fixed")),
              ("Check the thermostat and the programmer first: a timer slipped to water only, a room "
               "stat turned down, or flat batteries in a wireless one are the commonest cold houses. "
               "Then look at the boiler's pressure gauge (1 to 1.5 bar cold) and top it up at the "
               "filling loop, and press reset once. In a cold snap the condensate pipe outside can "
               "freeze, so pour warm water along it. If it still will not fire, or you smell gas, "
               "that is a Gas Safe engineer."),          bias=1,
              avoid=("food", "reheat", "heatwave", "hot weather", "sun", "sunburn", "hayfever",
                     # the row keys "rights" because a fault that has dragged on is followed by
                     # "what can i do", but this card only says what to check: a line that asks
                     # about rights is the landlord's-repairs letter, which names the reasonable
                     # time and what came with the flat
                     "my rights", "what are my rights", "my legal rights", "am i entitled",
                     "heating bill", "energy bill", "bill", "cost", "price", "cheap", "tariff",
                     "quote", "insulation", "car", "cars", "van", "engine", "microwave", "oven",
                     "saucepan", "water bottle", "hot water bottle", "electric blanket",
                     "microwave",
                     # not every "heating" is a house: a car heater, a heat pad, an office, a
                     # caravan or a greenhouse has no programmer and no pressure gauge, and the
                     # thermostat-first answer would be confidently wrong for them
                     "motorhome", "camper", "caravan", "office", "workplace", "heating pad",
                     "heat pad", "underfloor", "greenhouse", "fish tank", "seat heater", "hot tub",
                     "car heater",
                     # a cold house with a baby, a disabled person or a ninety-year-old in it is not
                     # a boiler question first: the line names the person, and the answer that says
                     # "ring 111 or your health visitor today" is the better one to keep
                     "baby", "babies", "newborn", "months old", "weeks old", "toddler",
                     "disabled", "disability", "carer", "frail", "elderly", "pensioner",
                     "health visitor", "in her 80s", "in his 80s", " is 85", " is 90", " is 95",
                     "over 80", "over 85", "over 90",
                     # "do i need to turn the heating off first", after a radiator answer, is about
                     # the job in hand; the context makes the heating a subject again and this entry
                     # was taking the follow-up
                     "turn off", "turning off", "turn it off", "turning it off", "off first",
                     "bleed", "bleeding", "bleed it", "radiator key",
                     # a radiator that is cold at the top and hot at the bottom is air, and the
                     # bleed answer owns it; a line that names the boiler or its pressure is
                     # `boiler-broken`'s ("my boilar pressure has droped and the heating wont come on"
                     # was taking this answer, thermostat first, over the pressure gauge).
                     "at the top", "at the bottom", "cold at the top", "hot at the bottom",
                     "top half", "boiler", "combi", "pressure", "gauge", "locks out", "lockout",
                     "fault code",
                     # "and how often should i do that", after a bleed answer, asks a frequency this
                     # entry does not have; the context makes radiator and cold the subject again
                     "how often", "how many times")),
        # "Is it worth getting someone out" after a boiler answer is a decision about paying a
        # tradesman, and the leaning line's word ("loft") handed it to the loft-conversion price with
        # its £25,000 figure. The subject has to come from the boiler, so the ask gate holds it to the
        # lines where a boiler or its heating is already the subject; a service is a cost question and
        # belongs to the boiler-service row in costs.py.
        entry("boiler-callout", (("boiler", "heating", "hot water", "radiator", "radiators", "combi"),
                                 ("someone out", "someone in", "get someone", "call someone",
                                  "an engineer", "engineer", "callout", "call out", "tradesman",
                                  "worth getting", "worth paying", "worth a call")),

              "Yes for anything on the gas side, and the pressure gauge (1 to 1.5 bar) and the reset "
              "button are worth trying first. A Gas Safe engineer's callout is usually £60 to £120, "
              "and it is worth paying once a fault repeats rather than for a one-off reset. Note the "
              "make and model, the error code and what happens when it cuts out, because that is what "
              "turns a second visit into a first fix. If you smell gas, or water is leaking near the "
              "electrics, turn it off and call the emergency line.",
              avoid=("quote", "quoted", "estimate", "landlord", "tenant", "deposit", "how much",
                     "cost", "price", "cheapest", "install", "new boiler", "replace", "replace it",
                     "service", "serviced", "servicing", "safety check"),
              # "the boiler is making a noise, is it worth getting someone out" ties the price of a
              # new boiler on score, and the person is asking whether to pay for a visit, not for a
              # boiler, so this one is the more specific of the two.
              bias=2,
              # "worth getting" is this row's question when the line names somebody to come out or
              # something wrong; "is it worth getting a heat pump" is a purchase, not a callout.
              guard=_a_visit_not_a_purchase,
              ask=("boiler", "heating", "hot water", "radiator", "radiators", "combi")),
        entry("landlord-damp",
              (("landlord", "landlady", "letting agent", "housing association", "council", "my fault"),
               ("damp", "damp patch", "damp patches", "damp walls", "mould", "mold", "mouldy", "moldy",
                "black mould", "black mold", "mildew", "condensation")),
              "Put it in writing with photos and dates, and ask them to find the cause rather than paint "
              "over it: a coat of paint is the one repair that makes damp come back. If they will not "
              "act, your council's environmental health team can inspect damp and mould as a hazard to "
              "health and make the landlord deal with it, and Shelter or Citizens Advice will help you "
              "write the letter free. Keep paying the rent and keep copies of everything you send. A "
              "window open for ten minutes a day and a dehumidifier hold it while you wait.",
              # A disbelieving landlord is the same question: the person is asking what they can do
              # about it, not whether it is really damp.
              # A line that asks about being evicted, or about a section 21 notice, is asking about the
              # tenancy and not about the wall: it has its own answer, and this one would bury it under
              # a repair letter.
              avoid=("evict", "evicted", "evicting", "eviction", "evictions", "section 21", "section 8",
                     "s21", "revenge", "kick me out", "kick us out", "throw me out", "throw us out",
                     "get rid of me", "notice to quit"),
              bias=1),
        # A tenant who says they rent, and names no landlord, is the same question: "im renting and my
        # washing machine has been broken for 2 weeks" and "im a tenant and the boiler has been broken
        # for a week" were the appliance checks (ring the retailer) and a Citizens Advice hedge, and
        # the letter above is the answer either way. Its own wording already draws the line the person
        # needs: what came with the flat is the landlord's, what they brought is theirs.
        entry("landlord-repairs", (("landlord", "landlady", "letting agent", "tenant", "tenants",
                                   "i rent", "im renting", "i'm renting", "we rent", "renting",
                                   # The home is named as a place, and the person never says
                                   # "tenant": "the washing machine in my flat has been broken for 2
                                   # weeks", "the oven in my rented flat is broken". `faulty-goods`
                                   # stands down for these lines (its guard), so this row is what
                                   # answers them.
                                   "in my flat", "in the flat", "in our flat", "in my rented",
                                   "rented flat", "rented house", "rented home", "my rented",
                                   # "what are my rights" is in the key because a line can name the
                                   # fault and the right without a flat: "the heating has been
                                   # broken for 3 weeks, what are my rights".
                                   "the flat came with", "my rights", "what are my rights",
                                   "as a tenant", "my tenancy"),
                                   ("fix", "repair", "broken", "boiler", "refuse", "refuses", "ignore",
                                    "ignoring", "rights", "wont", "won't", "not fixing",
                                    # A fixture that came with the flat is still the landlord's, so
                                    # the appliance names are here: "i rent and the oven has been
                                    # broken for weeks" reaches the letter. Time words ("weeks",
                                    # "months") stay out - with them the follow-up "its been 3 weeks"
                                    # lost the letter with the boiler already in it.
                                    "heating", "hot water", "oven", "washing machine", "washer",
                                    "dishwasher", "fridge", "freezer", "shower", "toilet",
                                    # "does nothing" is the plainest way people say a landlord is
                                    # not fixing it, and without it the line matched no answer at
                                    # all: "my landlord does nothing about the mould" came back
                                    # "Got it. Is there anything you'd like a hand with?"
                                    "does nothing", "doesnt do anything", "doesn't do anything",
                                    "not doing anything", "isnt fixing", "isn't fixing",
                                    # Not calling back is the same failure as not fixing: "the letting
                                    # agent still hasnt called me back" reached no row at all and got
                                    # an echo of its own words back.
                                    "called back", "call back", "called me back", "hasnt called",
                                    "hasn't called", "havent called", "haven't called", "never called",
                                    "not called back", "still waiting", "chased", "chasing",
                                    "calls back", "phoned back", "not called", "no reply", "reply",
                                    "replied", "answers", "respond", "responded", "get back to me",
                                    "got back to me", "chase", "emails", "emailed", "email",
                                    "heard nothing", "ignores", "waiting", "keeps saying",
                                    "fobbed off",
                                    # The fault told as a length of time, which is how a repair that
                                    # has not happened is said: "the heating has been broken for 3
                                    # weeks", "it has not been fixed".
                                    "has been broken", "have been broken", "be been broken",
                                    "broken for", "broken since", "broken weeks",
                                    "not been fixed", "hasnt fixed", "hasn't fixed", "not fixed",
                                    "not working", "stopped working",
                                    # the duty itself, asked as a list of what they must do. Without
                                    # these, "what are my landlord's obligations" was a shrug.
                                    "responsibilities", "responsibility", "obligations",
                                    "obligation", "should fix", "has to fix", "have to fix",
                                    "must fix", "supposed to fix", "supposed to repair",
                                    "what must", "what do they have to", "what does he have to",
                                    "what does she have to")),          the_fault(
                  # The letter is quoted at the end of the answer, not its middle: a long answer is
                  # sometimes split across two turns, and a split inside a quoted letter left
                  # "Thanks, [name].\" Landlords have to do most repairs..." as a reply of its own.
                  "Landlords have to do most repairs in a reasonable time, and anything that came with "
                  "the flat counts, appliances included, while something you brought with you is "
                  "yours to fix. Put it in writing, a text or email is fine, and keep a copy: \"Hi - "
                  "I reported the {fault} on [date] and nothing has been done. Please arrange a "
                  "repair within 14 days.\" If they ignore you, your council's environmental health "
                  "team or Shelter can push it along.",
                  "Put it in writing, a text or email is fine, and keep a copy. Name what is wrong "
                  "and when it started, say what you want done and ask for a date, then keep the "
                  "messages: landlords have to do most repairs in a reasonable time, and anything that "
                  "came with the flat, appliances included, counts, while something you brought with "
                  "you is yours to fix. If they ignore you, your council's "
                  "environmental health team or Shelter can push it along."),
              # Money the landlord is holding is a tenancy question, not a repair one: the deposit
              # answer knows the protection scheme and the dispute service, this one does not.
              # A sale is not a repair either: the tenancy carries on, and that has its own answer.
              avoid=("deposit", "deposits", "selling", "sells", "sell", "sale", "sold",
                     "selling up", "on the market", "new owner", "new landlord",
                     # Damp and mould have their own answer: the letter above would tell a landlord
                     # about a boiler the person never mentioned.
                     "damp", "damp patch", "damp patches", "damp walls", "mould", "mold", "mouldy",
                     "moldy", "mildew", "condensation",
                     # "what are my rights" is in the key, and it is how every domain asks its own
                     # question: "my flight was overbooked what are my rights" was answered with a
                     # letter to a landlord about a flat the person never mentioned. The things that
                     # are not a home stand this row down, and their own answers take them.
                     "flight", "flights", "plane", "airline", "airport", "overbooked", "train",
                     "trains", "rail", "railway", "bus", "coach", "hotel", "holiday", "package",
                     "restaurant", "parcel", "delivery", "concert", "festival", "gig", "ticket",
                     "tickets", "mobile contract", "phone contract", "broadband", "insurance",
                     "sacked", "redundancy", "dismissed", "employer", "boss",
                     # the agent in the key is a letting one: a travel agent, an insurance broker
                     # and a recruiter go quiet in their own lanes
                     "travel agent", "travel agents", "holidays", "insurance broker", "recruiter",
                     "recruiters", "interview", "estate agent", "sublet", "subletting", "guest",
                     "guests")),
        # Everyone who is not being repaired asks this next, and main answered it four ways: "can i
        # withhold rent" and "can i stop paying rent" were a Citizens Advice shrug, "can i withhold
        # rent because the boiler is broken" the same shrug, "can i refuse to pay rent until its
        # fixed" the garage-labour hourly rate, "can i pay for a repair and take it off the rent" the
        # how-to-pay-for-a-big-purchase card, and "can i withhold rent until the damp is fixed" the
        # damp-treatment answer. None of them is the yes-or-no the person asked, and the wrong yes is
        # the expensive kind: stopping the rent is what gets a tenant evicted.
        entry("withhold-rent",
              (("withhold", "withholding", "withheld", "hold back", "stop paying", "stopped paying",
                "refuse to pay", "refusing to pay", "not paying", "skip the rent", "skip a payment",
                "take it off the rent", "deduct", "deduct it", "rent reduction", "reduce the rent",
                "pay less rent", "rent free", "rent strike"),
               ("rent", "landlord", "landlady", "letting agent", "tenancy", "tenant", "repair",
                "repairs", "fixed", "fix", "damp", "mould", "boiler", "heating", "hot water")),
              "Not on your own, and not by simply stopping: stopping the rent is a breach of the "
              "tenancy, and the arrears are what gets tenants evicted, whatever the state of the "
              "boiler. Keep paying and do what does work - "
              "report it in writing with dates and photos, and ask the council's environmental health "
              "team to inspect, since for a serious hazard they can order the repair. Shelter or "
              "Citizens Advice will say free whether yours is one of the rare exceptions; get that in "
              "writing before you hold back a penny.",
              # A deposit, a rent rise and a sale are their own questions, and so is a plain "how do
              # i get the landlord to repair it", which has a letter to answer it.
              avoid=("deposit", "deposits", "rent increase", "raise the rent", "raise my rent",
                     "selling", "sell", "sale", "sold", "evict", "evicted", "eviction",
                     "section 21", "section 8", "buying", "mortgage", "car", "van", "garage",
                     "hire", "student loan", "mortgage payment",
                     # A question between the people sharing a flat is not one for the landlord:
                     # "is it fair that my flatmate pays less rent because his room is smaller" was
                     # a shrug and this row would have answered it with an eviction warning.
                     "flatmate", "flatmates", "flat mate", "flat mates", "housemate", "housemates",
                     "house share", "house-share", "houseshare", "roommate", "roommates",
                     # The other direction: a lodger or a tenant who has stopped paying is the
                     # landlord's side of it, and this row only answers the tenant. "my lodger has
                     # stopped paying rent" was being told that withholding rent puts *you* in
                     # breach of the tenancy.
                     "lodger", "lodgers", "my tenant", "my tenants", "tenant", "tenants",
                     "sublet", "subtenant", "subtenant", "room to let"),
              # "how do i get the landlord to fix it" and "can my landlord put the rent up" are not
              # this question: the key word has to be about holding money back, so one of those
              # phrases has to be there.
              ask=("withhold", "withholding", "withheld", "hold back", "stop paying", "stopped paying",
                   "refuse to pay", "refusing to pay", "not paying", "skip the rent",
                   "take it off the rent", "deduct it", "rent reduction", "reduce the rent",
                   "pay less rent", "rent strike"),
              bias=1),
        # A tenant naming a fitting is asking about the tenancy, and the row that knew the word for
        # the fitting answered instead: the shower tray, the tap washer, the window frame, the lock
        # barrel, a cupboard hinge, and for the toilet the constipation card. The landlord word
        # plus one of those fittings is what makes the line this entry's, so it carries the letter
        # and stands a point above the DIY rows, which are where these lines went.
        entry("landlord-says-fix-it-yourself",
              (("landlord", "landlords", "landlady", "letting agent", "letting agents",
                "letting agency", "housing association", "my tenancy"),
               LANDLORD_JOB_FITTINGS),
              LANDLORD_REPAIR_LETTER,
              bias=3,
              # The deposit, the sale and a line about being evicted are their own questions, and a
              # landlord who will not fix it did not ask for a rent rise either.
              avoid=("deposit", "deposits", "selling", "sells", "sell", "sale", "sold", "evict",
                     "evicted", "eviction", "section 21", "notice to quit", "kick me out",
                     "throw me out", "rent increase", "raise the rent", "arrears",
                     # A hole in the glass is made safe before anybody writes a letter, tenant or
                     # not, so that card keeps the line.
                     "glass", "pane", "panes", "smashed", "shattered", "shards",
                     # the same shape `fitting-repair` uses: a window with the glass out is a hole
                     # to make safe, and the letter comes after that
                     "broken window", "window is broken", "window was broken", "broke my window",
                     "broke the window", "put through", "board up", "boarded up"),
              # A sale or a decoration question that happens to name a door is not this: the ask has
              # to be about the fault, so at least one of these words has to be in the line.
              ask=("fix", "fixed", "fixing", "repair", "repairs", "broken", "broke", "wont", "won't",
                   "will not", "refuses", "refusing", "refused", "ignores", "ignoring", "ignore",
                   "not fixing", "does nothing", "deal with", "sort out", "get it sorted")),
        entry("landlord-selling",
              (("landlord", "landlady", "letting agent"),
               ("selling", "sells", "sell", "sale", "sold", "selling up", "on the market",
                "new owner", "new landlord", "move out", "moving out", "leave", "leaving")),
              "A sale does not end your tenancy: the buyer takes the flat with you in it, your "
              "agreement carries on and your deposit stays protected. Keep paying the rent to your "
              "current landlord until they give you the new owner's details in writing, and keep the "
              "receipts. If they want you out for the sale, they still have to give you the notice "
              "your agreement and the law require - a sale is not notice - and a court order if you "
              "do not leave. Do not sign anything or hand back the keys without advice; Shelter or "
              "Citizens Advice will check the notice free.",
              # A repair, a deposit and a rent rise are their own questions. A sale that comes with
              # an eviction or a notice is this question, so those words stay out of the avoid list.
              avoid=("repair", "broken", "boiler", "damp", "mould", "deposit", "rent increase",
                     "raise the rent", "arrears", "buying", "buy", "mortgage", "house price",
                     "should i sell"),
              # A line about a landlord who wants you out is not a sale unless it says so: "leave"
              # and "move out" are in the key, so the sale word has to be present too.
              ask=("selling", "sells", "sell", "sale", "sold", "selling up", "on the market",
                   "new owner", "new landlord"),
              # A rent-arrears line also says "landlord" and "out"; a sale is the narrower subject.
              bias=2),
        # People write the machine as two words as often as one - "my dish washer smells after a
        # wash" reached nothing at all on main, while the same line with "dishwasher" answered.
        entry("dishwasher", (("dishwasher", "dishwashers", "dish washer", "dish washers"),
                             ("smell", "clean", "greasy", "filter", "cloudy", "streaks",
                              "salty", "white film", "white marks", "white spots", "film",
                              "marks")),
              "Clean the filter at the bottom, wipe round the door seal, and run an empty hot cycle "
              "with a dishwasher cleaner or a bowl of white vinegar on the top rack. The problem is "
              "usually food and grease sitting in the filter and the door seal. Check the salt and "
              "rinse aid too: running out of either makes everything come out cloudy.",
              # a pair of spectacles that came out cloudy is the glasses row's line, not the
              # machine's: "glasses" was in the key above and took it
              avoid=("my glasses", "spectacles", "specs", "frames", "lenses", "lens",
                     "prescription", "reading glasses")),

        # --- energy, heating and the boiler ------------------------------------
        entry("energy-use-up", (("energy", "electricity", "gas", "bill", "bills"),
                                 ("used more", "more than", "gone up", "doubled", "higher", "so high",
                                  "increased", "went up", "why so",
                                  # the same question opened with "why", which the size word alone
                                  # does not cover: "why is my gas bill huge" got a shrug while
                                  # "why is my electric bill so high" answered
                                  "why is my", "why has my", "why did my", "why are my",
                                  "why does my", "why is the", "why has the")),
              ("Compare the reading on the bill with the numbers on your meter first: an estimated "
               "reading, often after a supplier change, is the commonest cause of a shock bill, and "
               "sending a real reading puts it right. After that it's usually the season (heating), the "
               "immersion or a heater left on, or a fridge or freezer seal failing, so read the meter "
               "once a day for a week with everything off and see what still ticks up."),
              # the question is why the number moved; if the line asks what to do about it, main's
              # energy-bill answer is the one that helps, so the action phrasings pass
              avoid=("cut", "save", "reduce", "cheaper", "lower", "switch", "tariff", "deal",
                     "what can i do", "what do i do", "what should i do", "how can i", "how do i",
                     "spend less", "keep warm", "help",
                     "council tax", "tax", "water", "phone", "mobile", "broadband", "tv licence",
                     "licence", "rent", "insurance",
                     # a subscription bill has no meter behind it: "my sky bill has gone up" was told
                     # to read the meter once a day. The provider-price row answers it.
                     "sky", "sky tv", "sky bill", "satellite", "tv", "telly", "virgin", "virgin media",
                     "subscription", "subscriptions", "netflix", "spotify", "package",
                     "landline",
                     # "we just moved in and my girlfriend earns way more than me, how should we split
                     # the bills" is a household-income question: the `bills` key plus `more than`
                     # read it as a jump in the energy bill.
                     "split", "splitting", "split the bill", "earns", "earn", "income",
                     "salary", "wage", "wages", "50 50", "60 40", "more than me", "moved in")),
        # Reading the meter is its own job, and nothing answered it: "how do i read my gas meter" got
        # a shrug and "how do i read my electricity meter" got the physics of electric charge.
        entry("read-a-meter",
              (("gas meter", "electricity meter", "electric meter", "meter reading", "meter readings",
                "read the meter", "read my meter", "read our meter",
                # not "smart meter": main has that answer already (press A until kWh shows), and
                # the digits-a-gas-meter answer is the wrong one for a screen with a button
                "prepayment meter", "key meter", "token meter", "meter", "meters"),
               ("read", "reading", "how do i read", "how to read", "take", "taking", "submit",
                "send", "give", "which numbers", "which number", "digits", "numbers", "wrong",
                "estimated", "units", "how much")),
              "Read the black digits only and ignore anything after the decimal point or in red - those "
              "are the fractions of a unit, and a supplier only wants the whole numbers. A gas meter "
              "counts cubic metres if it says m3, or hundreds of cubic feet if it says ft3 on an older "
              "one, and the bill needs to agree which. An electricity meter may show one row of numbers, "
              "or two for day and night if you are on Economy 7: send both. Take a photo on the first of "
              "the month and send it in, because a reading you send beats an estimate.",
              # a bill that has gone up, a moving-house handover and a leaking meter are other answers
              avoid=("gone up", "so high", "higher", "expensive", "tariff", "switch", "cheaper",
                     "moving", "move out", "moving house", "landlord", "leak", "leaking", "smell",
                     "gas leak", "fault", "not working", "broken", "smart", "smart meter", "in credit",
                     "debt", "arrears", "pay", "payment", "how much do i owe", "top up", "topup"),
              ask=("read", "reading", "how", "take", "submit", "send", "which", "numbers", "digits",
                   "wrong", "units", "where"),
              # "read" and "how" are common words in this domain now that the tape and the level have
              # their own rows, and that cost this row its rarity point: "how do i read my electricity
              # meter" started reaching the smart-meter card, which is the answer for a screen with a
              # button rather than for a row of digits. The meter in the line is this row's question,
              # so it starts one point ahead.
              bias=1),
        # --- appliances and small repairs --------------------------------------
        entry("smoke-alarm-number",
              (("smoke alarm", "smoke alarms", "detector", "detectors", "fire alarm"),
               ("how many", "number", "one per", "where", "need", "needed", "fit", "fitted", "install",
                "put up", "floors", "bedroom", "bedrooms", "hallway")),
              "One on every floor, one in the hallway outside the bedrooms, and one in the room with the "
              "boiler or the open fire - the hallway one matters most, because smoke in the stairs is "
              "what cuts off the way out. Fit sealed ten-year alarms so there is no battery to "
              "remember, and check the test button on each once a month.",
              avoid=("beep", "beeping", "chirp", "chirping", "noise", "keeps going off")),

        entry("smoke-alarm-test",
              (("smoke alarm", "smoke alarms", "detector", "detectors", "fire alarm"),
               ("check", "test", "testing", "how often", "monthly", "battery", "batteries", "replace")),
              "Press the test button once a month and change the battery once a year - the easy date is "
              "when the clocks change. Vacuum the dust out of the vents twice a year, and replace the "
              "whole alarm every ten years, because the sensor ages. Fit one on every floor and one in "
              "the hallway outside the bedrooms.",
              # a chirping alarm is its own entry below; this one is the how-to-look-after-it question
              avoid=("beep", "beeping", "chirp", "chirping", "noise", "keeps going off", "smell",
                     "smoke coming", "fire started", "on fire", "burnt", "burning",
                     "how many", "number", "one per", "where should")),
        entry("smoke-alarm-beep", (("smoke alarm", "detector"), ("beep", "beeping", "chirp", "chirping",
                                                                 "noise", "keeps")),
              "A single chirp every minute or so means a low battery: change it now, don't wait. If it's "
              "a sealed ten-year alarm, replace the whole unit, and vacuum the dust out of the vents "
              "either way.",
              # An alarm that goes off while the grill is on is not a flat battery - it is a badly
              # placed sensor - and "keeps" met "smoke alarm keeps going off when i cook" here, so the
              # cooking words stand this answer down and the nuisance entry answers it instead.
              avoid=("cook", "cooking", "cooked", "toast", "toasting", "grill", "grilling",
                     "oven", "hob", "fry", "frying", "roast", "roasting", "bake", "baking",
                     "shower", "steam", "kitchen", "burning", "burnt")),
        entry("machine-takes", (TAKES_THINGS, ("how long", "take", "takes", "taking", "long", "time",
                                                "quick", "quickly")),
              _machine_takes,
              # "how long does a fridge last" is the years, and a repair is neither: this row is the
              # time the machine needs to do a job - to get cold, heat up, boil, or run a cycle.
              # "how long can i keep eggs in the fridge" reached this row on "how long" and "fridge"
              # and turned the shelf life answer down, so the keeping words stand it down before it
              # is scored at all.
              avoid=("last", "lasts", "lasting", "years", "lifespan", "life expectancy", "life span",
                     "repair", "repairing", "replace", "replacing", "broken", "not working", "fixed",
                     "engineer", "cost", "price", "electricity", "energy",
                     # the hour is the tariff row's question: "what is the cheapest time to run the
                     # washing machine" is when to put it on, not how long a cycle takes.
                     "cheapest", "cheaper", "cheap time", "best time", "what time", "off peak",
                     "off-peak", "economy 7", "tariff", "in the morning", "in the evening",
                     "during the day", "time of day",
                     "keep", "keeps", "keeping", "store", "stores", "storing", "stored", "storage",
                     "shelf life", "shelf-life", "go off", "goes off", "gone off", "still ok",
                     "still good"),
              bias=2),
        entry("fridge-not-cold",
              # "working" and a bare "not" were key words here, and a machine that has stopped working is
              # the plug-and-fuse row's question, not this one: "my fridge has stopped working" and "my
              # freezer has stopped working" were told to stand a thermometer in a glass of water. The
              # symptom this row answers has to be said - not cold, not cooling, not freezing.
              (("fridge", "freezer"), ("cold", "not cold", "not very cold", "not that cold",
                                       "wont get cold", "won't get cold", "warm", "freezing",
                                       # a seal that has gone is why a fridge stops holding its
                                       # temperature, and the paper test below is the answer
                                       "door seal", "door seals", "seal", "seals", "rubber seal",
                                                          "cool", "cooling",
                                                          "chill", "chilled", "chilling",
                                                          # "stopped cooling" outranks science.fridge,
                                                          # which keys the bare word "cool" and used
                                                          # to take the fault report as a how-it-works
                                                          # question (deck/chat-misses.jsonl).
                                                          "stopped cooling", "not cooling",
                                                          "stopped getting cold", "not getting cold")),
              "Stand a fridge thermometer in a glass of water on the middle shelf and leave it "
              "overnight: the fridge wants 3 to 5C and the freezer -18C, and the dial's numbers are not "
              "degrees. A fridge that will not reach it wants the door seals checked - close the door "
              "on a sheet of paper and see if it slides out easily - and the coils at the back dusted. "
              "Don't overfill it either, because cold air needs space to move.",
              # A fridge on the blink is this entry; "how does a fridge work" is science.fridge.
              # "how do i keep food cool without a fridge" names a fridge to say it has none, and
              # telling that person to set the fridge to 3 to 5C is no answer at all (cobalt-ivy).
              # a machine with no life in it at all is the plug fuse and the wall socket, one row
              # down from here
              avoid=("how does", "how do fridges", "how it works", "explain",
                     # the phrase, not the verb: "stopped cooling" is a key of this very row, and
                     # a bare "has stopped" stood the row down on its own symptom
                     "stopped working", "not working", "has stopped working", "have stopped working",
                     "stopped altogether", "dead",
                     "wont start", "won't start", "will not start", "not turning on", "no power",
                     "wont turn on", "won't turn on", "keeps tripping", "tripping the",
                     # a pot going into the fridge is the cooling question, not a broken fridge:
                     # "should i let the pot cool right down before it goes in the fridge" was told
                     # to stand a thermometer in a glass of water. The fridge-fault lines name the
                     # machine and no pot, so this fence costs nothing else.
                     "the pot", "a pot", "the pan", "a pan", "the stew", "a stew", "the curry",
                     "the soup", "the casserole", "leftovers", "cool it down", "let it cool",
                     "let the pot", "let the pan", "before it goes in", "before putting it",
                     "cool right down", "cool down before",
                     "without a fridge", "without a freezer", "without refrigeration", "no fridge",
                     "no freezer", "power cut", "power outage", "camping", "cool box", "coolbox",
                     "ice box", "picnic",
                     # "i have mince in the fridge and not much else" is a dinner question: the key
                     # holds "fridge" and "not", so the bare "not" of "not much else" reached the
                     # thermometer card and a person naming the one thing they had to cook was told
                     # to stand a thermometer in a glass of water. A fridge that is not cold is still
                     # this entry - none of these words is how that is said.
                     # a door that will not shut is the seal entry's, and "wont" slips to "not" here
                     "door not shut", "door not shutting", "door not close", "door not closing",
                     "door wont shut", "door wont close", "door wont stay shut", "wont stay shut",
                     "door keeps opening", "door keeps popping open", "door pops open",
                     "door swings open", "door gap",
                     # who pays for the food that went warm is the ruined-food letter in
                     # consumer.py, not the thermometer: "fridge is warm and everything inside is
                     # ruined can i claim" was told to stand a thermometer in a glass of water.
                     "claim", "claims", "refund", "money back", "compensat", "who pays", "insurance",
                     "insured", "money back",
                     "not much else", "nothing else", "nothing much", "only", "dinner", "tea",
                     "supper", "lunch", "recipe", "recipes", "what can i make", "what can i cook",
                     "what should i make", "to cook"), bias=1),
        # A cool box is how you keep food and drink cold when there is no fridge, and the entry
        # above stands these lines down on purpose ("cool box", "coolbox", "ice box" and "picnic"
        # are in its avoid): telling someone with a cool bag to stand a thermometer in the fridge
        # is no answer at all. Before this entry every one of them was a shrug -
        # "how do i keep drinks cold in a cool box" got "That's beyond what I know well" and
        # "how do i keep a cool bag cold" got "I'm not sure about that one".
        entry("cool-box-cold",
              (("cool box", "coolbox", "cooler box", "cool bag", "cooler bag", "ice box",
                "picnic bag", "picnic box", "chiller bag", "chiller box",
                "ice packs", "ice pack", "freezer blocks", "freezer block", "freezer packs",
                "freezer pack", "cool blocks", "cool pack"),
               ("cold", "cool", "keep", "keeps", "keeping", "stay", "stays", "warm", "all day",
                "picnic", "picnics", "drinks", "food", "beers", "milk", "day out", "beach", "trip",
                "car", "camping")),
              "A cool box only holds the cold you put in it. Freeze a couple of water bottles or "
              "ice packs the night before, because they do the work, and pack them around the food "
              "rather than on top. Fill the empty space with more cold drinks or a rolled-up towel: "
              "a half-empty box warms up fastest. Keep it out of the sun, out of a parked boot that "
              "gets hot, and put a towel or a folded blanket over the lid. Open it as little as you "
              "can and shut it straight after. Cold drinks and fruit keep all day like that; cooked "
              "food, milk and anything with mayonnaise is the one to throw away if it has sat warm "
              "for more than about two hours.",
              bias=1,
              # Buying one is a shopping question, and this answer would be the wrong job.
              avoid=("buy", "buying", "best", "which", "cheapest", "cheap", "price", "size",
                     "how big", "electric", "plug in", "recommend", "worth it",
                     # A cool box that smells wants washing out, not ice: "my cool box smells" is
                     # a cleaning line and the cold advice is the wrong job for it.
                     "smell", "smells", "smelly", "stinks", "mould", "mold", "dirty", "wash")),
        # How long the appliance takes to come to temperature is a clock question about the fridge,
        # not a keeping question about the food in it. "how long does a fridge take to get cold" was
        # answered with the cooked-food table ("cooked food keeps 3 to 4 days in the fridge"), and so
        # was "how long should i wait before putting food in a new fridge", because the only words
        # that reached an entry were "fridge" and "how long". The waiting words are the key here, and
        # the keeping row stands down below.
        entry("fridge-first-cold",
              (("fridge", "freezer", "fridge freezer", "refrigerator", "icebox"),
               ("get cold", "gets cold", "get colder", "getting cold", "cool down", "cools down",
                "cooling down", "get to temperature", "get down to temperature",
                "come down to temperature", "come to temperature", "reach temperature",
                "first switched on", "switched on", "switch it on", "putting food in",
                "put food in", "putting things in", "loading it", "how long before",
                "how long should i wait", "how long to wait", "wait before")),
              "A fridge comes down to temperature in about 4 hours empty and is steady at 4C after 24, "
              "so switch it on, let it run empty, then load it - a freezer wants about 24 hours to hold "
              "-18C. A thermometer in a glass of water tells you when it is ready, not the dial.",
              # A fridge that will not get cold at all is the fault card above, and a food question is
              # the keeping rows: only the clock and the waiting belong here.
              avoid=("not cold", "wont get cold", "won't get cold", "stopped getting cold",
                     "not getting cold", "not cooling", "stopped cooling", "broken"),
              # The key carries the fridge's own clock words, so "how long" is what makes the line a
              # question about time: "my new fridge is slow to get cold" is the fault card above.
              ask=("how long", "long to", "how many hours", "how much time", "how long before",
                   "how long should", "how long do i"),
              bias=1),
        entry("oven-heat-up",
              (("oven", "ovens", "fan oven", "range cooker"),
               ("heat up", "heats up", "heating up", "warm up", "warms up", "warming up",
                "preheat", "pre-heat", "preheating", "come up to temperature",
                "get to temperature", "reach temperature", "long to heat", "takes to heat")),
              "Most ovens reach 180C in 10 to 15 minutes from cold, and a fan oven is quicker than a "
              "conventional one, so a 20-minute preheat covers nearly everything. Trust an oven "
              "thermometer over the dial - they are often 10 to 20C out.",
              # the cleaning, the smell and the cooking rows all name an oven and none of them is
              # asking about the clock
              avoid=("clean", "cleaning", "self cleaning", "pyrolytic", "smell", "smells", "smoke",
                     "pizza", "chips", "roast", "bake", "baking", "cake", "air fryer",
                     # "my oven is not heating up" is the element card: a fault is not a clock
                     "not heating", "not heating up", "isnt heating", "isn't heating", "not working",
                     "wont heat", "won't heat", "stopped heating", "broken", "fault", "fuse"),
              # "how do i preheat a fan oven" is the fan-oven dial answer, not the minutes: only a
              # line that asks about time is this row's.
              ask=("how long", "long to", "how many minutes", "how much time", "how long before"),
              bias=1),
        # The job of cleaning the fridge. A smell in it is a separate entry (fridge-smell), so the
        # keys here are the cleaning words only.
        # Water in the bottom of a fridge is the drain hole at the back, and it was answered with a
        # chat echo. The freezer case shares the drain, so one row covers both.
        entry("fridge-water-inside",
              (("fridge", "freezer", "refrigerator", "fridge freezer", "salad drawer", "crisper"),
               ("water", "wet", "puddle", "pools", "pooling", "collecting", "collects", "ice", "icy",
                "dripping", "drips", "leaking", "leak", "drawer", "bottom", "inside")),
              "Water in the bottom of a fridge is nearly always the drain hole at the back: it clogs "
              "with bits of food, so push a pipe cleaner or a piece of stiff wire down it and flush "
              "warm water through. Ice on the back wall means the fridge is running too cold, so turn "
              "the dial up a notch and let it defrost. If the water keeps coming back, check the door "
              "seal by closing the door on a sheet of paper - if it slides out easily, the seal is the "
              "fault.",
              bias=1,
              avoid=("buy", "best", "which", "cheapest", "size", "smells", "smell", "not cold",
                     # "clean" is `fridge-clean`'s question: the drain keys the drawer and the
                     # bottom of the fridge, so "how do i clean the inside of the fridge" was a
                     # blocked drain hole
                     "clean", "cleaning", "cleaned", "clean out", "wipe", "wipe out", "scrub",
                     "shelves", "shelf", "racks", "spills",
                     "not freezing", "noisy", "noise", "defrost", "frost free", "on the floor",
                     "outside", "washing machine", "dishwasher", "boiler", "kettle", "toilet",
                     "hot water bottle", "ice cubes", "ice tray", "drinking",
                     # "i keep water in the fridge" says where the water lives, not that the fridge
                     # is leaking: with the kettle words above it was still sent to the drain hole,
                     # so the row stands down for the drinking water people keep.
                     "keep water", "keeps water", "keep a jug", "jug", "bottle", "bottles",
                     "water bottle", "water bottles", "keep drinks", "keep juice", "cans",
                     # a freezer that ices up is the defrost question, even when the line says ice
                     # and inside: "a layer of ice inside, is that costing me money" is that one
                     "layer of ice", "ices up", "iced up", "ice builds up", "ice build up",
                     "ice build-up",
                     # the same goes for a freezer filling up: "my freezer has ice on the walls" and
                     # "my freezer is full of ice" were sent to the fridge's drain hole, and the
                     # defrost row answers them
                     "ice on the walls", "walls of ice", "full of ice", "lots of ice",
                     "so much ice", "thick ice", "ice everywhere", "ice in the freezer",
                     "freezer has ice", "freezer with ice", "build up of ice",
                     "cost", "costs", "costing", "money", "bill", "bills",
                     "energy", "efficient", "efficiency")),
        # An oven door that is stiff or will not shut was met with a chat echo, and the front-door
        # row used to answer it with a lock and a plane.
        entry("oven-door",
              (("oven", "cooker", "range cooker", "oven door"),
               ("door", "hinge", "hinges", "stiff", "sticking", "sticks", "hard to shut",
                "hard to close", "wont shut", "won't shut", "wont close", "won't close", "not closing",
                "drops", "dropped", "spring", "loose", "rub", "rubbing", "squeak", "squeaks")),
              "An oven door that is stiff or will not shut is nearly always the hinge: open it and "
              "look at the two arms at the bottom, because a bent arm or a hinge that has dropped "
              "makes the door rub on the frame. Check nothing inside has slipped forward first - a "
              "shelf or a tray stops the door a centimetre short - and wipe the burnt grease off the "
              "hinge area. If it still will not sit shut, hinges are a cheap part for most makes: take "
              "the model number off the sticker and order a pair.",
              bias=1,
              # a tenant with a landlord who will not act wants the letter, not the hinges: the
              # tenancy phrasings stand this card down, as they do for `fitting-repair`
              avoid=("clean", "cleaning", "glass", "smell", "burning", "not heating", "temperature",
                     # a hand closed in the oven door is an injury, not a hinge that has dropped:
                     # "i shut my hand in the oven door" was the hinge card
                     "finger", "fingers", "thumb", "my hand", "hand in", "trapped", "caught",
                     "slammed", "burned", "burnt", "scalded",
                     "lock", "childlock", "child lock", "fan", "element", "pizza", "bread", "cake",
                     "how long", "how hot", "what temperature", "shelf position",
                     "landlord", "landlords", "landlady", "letting agent", "letting agency",
                     "my tenancy", "wont fix", "won't fix", "refuses to fix", "refusing to fix",
                     # a door that sticks is not a door with grease on it: "how do i get grease
                     # off the oven door" was the hinge answer, and the glass row owns the grease.
                     "grease", "greasy", "burnt", "burnt on", "food", "spill", "spilled",
                     "splatter", "splatters", "stain", "stains", "smear", "smears",
                     # A loaf that goes up and then drops in the oven has nothing to do with the
                     # door: `drops` is in the key above, and this card answered a bread fault with
                     # a hinge ("it rises then it drops in the oven"). Anything said about the bake
                     # itself stands this row down - the baking rows in cooking.py own those lines,
                     # and a door that drops is still here because none of these words is in it.
                     "rise", "rises", "risen", "rising", "prove", "proves", "proved", "proving",
                     "proof", "proofed", "dough", "sourdough", "loaf", "loaves", "yeast", "sponge",
                     "batter", "souffle", "soufflé", "pastry", "croissant", "meringue", "bake",
                     "bakes", "baked", "baking", "recipe")),
        entry("fridge-clean", (("fridge", "freezer"), ("clean", "cleaning", "cleaned", "wash", "wipe",
                                                      "shelves", "shelf", "scrub", "freshen", "hygiene")),
              "Empty it into a cool bag first, then wipe every shelf, drawer and the door seals with hot "
              "soapy water and dry them. Clear the drain hole at the back with a cotton bud and warm "
              "water, and leave a bowl of bicarbonate of soda on a shelf between cleans: it absorbs "
              "smells instead of covering them. Once or twice a year is enough if nothing has spilled."),
        # A door that will not shut is the seal, and it is the one fridge fault you can test in ten
        # seconds and often fix without a call-out. On main "the seal on my fridge door has gone" and
        # "the rubber on my freezer door is split" were a greeting, and "how do i know if my fridge
        # seal is bad" was a punt: the not-cold entry wanted a temperature complaint, so nothing
        # answered the seal itself.
        entry("fridge-seal",
              # the fridge or the freezer has to be named: "door" alone took the washing machine's
              # seal, the oven's and the car's, which are other entries and other answers
              # A door that will not shut is the same fault and the same ten-second test, and it was
              # answering as three other things: "the fridge door wont shut" got the thermometer card
              # ("wont" is one letter from "not", which keys the not-cold entry, so the slip reader read
              # a door that will not close as a fridge that is not cold), "my fridge door keeps popping
              # open" got the cooked-food keeping card, and "the freezer door wont stay shut" got the
              # power-cut card. The shapes of a door that does not shut or does not stay shut are key
              # words here, so the seal test and the hinge are what answers them.
              (("seal", "seals", "rubber", "gasket", "magnet", "magnetic strip",
                "door not shut", "door not shutting", "door not close", "door not closing",
                "door not shut properly", "door not closing properly", "door doesnt shut",
                "door doesnt close", "door does not shut", "door does not close",
                "door wont shut", "door wont close", "door wont stay shut", "door wont stay closed",
                "door keeps opening", "door keeps popping open", "door pops open", "door swings open",
                "door swings back open", "wont stay shut", "door gap", "gap round the door"),
               ("fridge", "freezer", "refrigerator")),
              "Close the door on a sheet of paper and pull it out: it should drag, and a note that "
              "slides out easily at that spot is a gap. Wipe the seal with hot soapy water and dry it, "
              "because a sticky or crumpled seal often shuts fine once it is clean, then check the door "
              "hinge has not dropped. A split or hardened seal is a part: the model number is on a "
              "sticker inside the fridge, and a new one is usually £20 to £40 and pushes into the "
              "channel by hand.",
              # the fridge without an adjective is not this: cold, cleaning and smell have their own
              # answers, and a fridge door that will not close is in house-doors, not here
              avoid=("clean", "cleaning", "smell", "smells", "smelly", "stink", "ice", "frost",
                     "defrost", "freezing", "not cold", "warm", "noise", "humming", "rattling",
                     "slam", "hinge"),
              # bias=2: a door that will not stay shut was reaching the power-cut card and the
              # cooked-food card on a tie, and both name a door without being about one
              bias=2),

        # appliance noise: the machine is working, it is just audible. A noise word alone is not a
        # fault report, so these sit apart from the smell and not-cold entries.
        entry("fridge-noise", (("fridge", "freezer", "refrigerator"),
                               ("hum", "hums", "humming", "buzz", "buzzing",
                                "rattl", "vibrat", "clunk", "gurgl", "ticking",
                                "clicking", "knock") + NOISE_WORDS),
              "The steady hum is the compressor, which switches on and off to hold the temperature: "
              "it is normal, and it gets louder when the room is warm or the door has just been shut "
              "on warm food. A rattle or a buzz is usually the fridge not sitting level, so wind the "
              "front feet down until it stands firm, and check nothing is touching the back. A clunk "
              "every few minutes, or a fridge that hums but never gets cold, is gas or the compressor "
              "and needs an engineer.",
              bias=1,
              avoid=("smell", "smells", "smelly", "stink", "stinks", "odour", "clean", "ice",
                     "frost", "defrost", "freezing", "food", "chicken")),
        # A machine that hums is working, it is just audible, and the banging answer above is about a
        # load out of balance: "why does my washing machine hum" got the tinnitus explanation, which
        # is advice for an ear, and then the spin-noise answer, which tells you to undo the tangle.
        entry("appliance-hum", (("washing machine", "washer", "dishwasher"),
                                ("hum", "hums", "humming", "whirr", "whirring", "whine", "whining",
                                 "buzz", "buzzing")),
              "A steady hum is the motor or the pump doing its job, and every machine has one. A hum "
              "that is new or louder is usually the machine standing uneven, something loose touching "
              "the case, or a filter or drain pump half blocked: level the feet, take the filter out "
              "and clean it, and check the drum or spray arm turns freely with the power off. A whine "
              "that rises with the speed is a bearing, which is a repair rather than a service.",
              bias=1,
              # the appliance's own fault is the better answer when the line names one: wet dishes,
              # a rattle, a squeal and a boiler all have an entry that knows more than this one
              avoid=("tinnitus", "my ears", "in my ears", "ringing", "hearing", "smell", "smells",
                     "buy", "replace", "best", "worst", "wet", "dirty", "not draining", "wont drain",
                     "won't drain", "squeal", "squeals", "squealing", "rattle", "rattling", "bang",
                     "bangs", "banging", "shaking", "wont spin", "won't spin", "not spinning",
                     "boiler", "radiator", "puddle", "leak", "leaking")),

        entry("washer-noise", (("washing machine", "washer", "washer dryer", "spin"),
                               ("shake", "shakes", "shaking", "bang", "bangs", "banging",
                                "rattl", "vibrat", "walk", "walks", "jump",
                                "jumps", "thump", "thumping", "screech", "squeal",
                                # the stems above are not prefixes the lookup matches, so
                                # "my washing machine rattles on the spin" had no answer at all
                                "rattle", "rattles", "rattling", "vibrate", "vibrates")
                               + NOISE_WORDS),
              "A machine that bangs or walks across the floor is almost always an uneven load: stop "
              "it, undo the tangle, and put a couple of towels in with a single heavy thing like a "
              "duvet. If it does it on every spin, take the transport bolts out of the back (they stay "
              "in on a new machine and must come out), level the feet so it cannot rock, and check it "
              "is not touching a cupboard. A screech or a burning smell means the drum bearings or the "
              "belt, which is a repair.",
              # A named fault sound belongs to the row below, which knows what that sound is: the
              # load answer does not touch a grind, a squeal or a rattle, and given the words as
              # well as this row it took the turn ("my washing machine is scraping" here, the
              # dismantled-drum answer there). "noisy", "loud" and "banging" keep this row, which
              # is the answer to them.
              avoid=("smell", "smells", "smelly", "musty", "drain", "drains", "empty", "water",
                     "filter", "buy", "replace", "worst", "best", "drum",
                     "grind", "grinds", "grinding", "scrap", "scrapes", "scraping",
                     "rumble", "rumbles", "rumbling", "roar", "roaring",
                     "screech", "screeching", "squeal", "squeals", "squealing",
                     "squeak", "squeaks", "squeaking", "rattle", "rattles", "rattling",
                     "clunk", "clunks", "clunking", "shriek", "shrieking")),

        # A washing machine had one answer for every sound it made - the load and the feet - and it
        # was a good answer to a bang and a wrong one to a grind: "my washing machine is making a
        # grinding noise" was told to untangle the washing, when a grind is something metal in the
        # drum or a bearing on its way out. "my washing machine is grinding" and "my washing machine
        # is scraping" matched nothing at all in the row above, and the scrape reached the tip.
        #
        # The sounds a machine makes when it is not the load are here, and this row is only ever
        # these: a bang, a wobble or a plain "noisy" keeps the row above, which answers the load.
        entry("washer-sound",
              (("washing machine", "washer", "washer dryer", "washer-dryer", "drum", "spin"),
               ("grind", "grinds", "grinding", "scrap", "scrapes", "scraping", "rumble", "rumbles",
                "rumbling", "roar", "roaring",
                "squeak", "squeaks", "squeaking", "squeal", "squeals", "squealing", "screech",
                "screeching", "shriek", "shrieking",
                "rattle", "rattles", "rattling", "clunk", "clunks", "clunking")),
              _washer_sound_fault,
              bias=1,
              # a dryer's drum is not a washer's, and the answer here would send someone to a kick
              # plate their machine has not got
              guard=_a_dryer_is_not_a_washer),

        # A fan oven keeps its fan going after the dial is off, and a fan that never stops sounds
        # like a fault. Left alone the line reached the baking advice about dials and gas marks,
        # which tells someone with a broken fan to drop the temperature 20C.
        entry("oven-fan-runs-on", (("oven", "cooker", "fan oven"),
                                   ("fan", "fans")),
              "A fan oven usually runs its cooling fan on after you switch off, sometimes for ten or "
              "twenty minutes, to pull the heat out of the casing: that is normal and it stops by "
              "itself. If it never stops, or starts again while the oven is cold, the thermostat or the "
              "fan switch has failed and it needs an engineer, and it is worth switching off at the "
              "wall until then.",
              bias=4,
              ask=("never", "stops", "stop", "keeps", "keeping", "runs", "running", "all the time",
                   "stays", "wont", "won't", "cold"),
              # "timing" is a loose form of "time", and it blocked "runs all the time"
              avoid=("clean", "cleaning", "gas mark", "bake", "cake", "roast", "bread", "temperature",
                     "dial", "degrees", "how long", "how hot")),

        # The glass in the door is its own job: the paste goes on the glass, not the cavity, and the
        # burnt specks come off with a blade held flat. "how do i clean the oven glass" had the
        # inside-the-oven answer and "my oven glass is dirty" had nothing.
        entry("oven-glass",
              (("oven glass", "oven door glass", "glass door", "oven window", "oven door",
                "the glass on the oven", "inside of the oven door", "door of the oven"),
               ("clean", "cleaning", "cleaned", "greasy", "grease", "dirty", "smear", "smears",
                "streak", "streaks", "marks", "scrub", "wipe", "wash", "filthy", "stained")),
              "Spread a paste of bicarbonate of soda and water on the glass, leave it twenty minutes "
              "and wipe it off with a damp cloth; burnt specks lift with a plastic scraper or a razor "
              "blade held almost flat to the glass. Keep caustic oven cleaner off the rubber seal, and "
              "wipe the inside of the door too, because most of the brown film sits between the panes.",
              # a burnt hand on the oven shelf is the safety module's line, never a cleaning one
              avoid=("hand", "hands", "finger", "fingers", "thumb", "arm", "arms", "wrist", "skin",
                     "scald", "scalded", "blister", "butter", "myself", "shelf", "shelves", "rack",
                     "racks", "stiff", "wont close", "won't close", "wont shut", "hinge", "smoke",
                     "smells", "smoking")),
        # "how do i clean the grill" got the barbecue answer: a grill in a cooker is the oven's, and
        # it is a different job from coals and a wire brush. Anything that says barbecue keeps it.
        entry("oven-grill",
              (("oven grill", "the grill", "grill pan", "grill tray", "grill plate", "grills",
                "grill"),
               ("clean", "cleaning", "cleaned", "grease", "greasy", "scrub", "soak", "wash",
                "burnt", "stuck", "filthy", "dirty")),
              "Soak the grill pan and its rack in hot water with washing-up liquid and a couple of "
              "tablespoons of bicarbonate of soda, then lift the burnt bits with a nylon scourer. "
              "The element above it is not a thing to scrub: switch it off, let it cool, and wipe it "
              "with a damp cloth, and leave the self-clean lever for the whole oven.",
              # a barbecue out in the garden is the barbecue row's question
              avoid=("barbecue", "barbecues", "barbeque", "bbq", "bbqs", "barbie", "charcoal",
                     "coals", "garden", "outdoor", "outside", "steak", "steaks", "burger",
                     "burgers", "sausage", "sausages", "kebab", "halloumi", "how long", "recipe",
                     "marinade", "temperature", "cook", "cooking", "which", "buy", "buying",
                     "dishwasher filter", "oven racks", "oven shelves"),
              ask=("clean", "cleaning", "cleaned", "grease", "greasy", "scrub", "soak", "wash",
                   "burnt", "stuck", "filthy", "dirty"),
              bias=1),
        # The racks are the dirtiest part of an oven and the paste is the wrong shape for them: they
        # lift out, so they can be soaked, and the cavity answer ("coat the inside, not the elements")
        # was what "how do i clean oven racks" got. Same job, one thing named differently.
        entry("oven-racks",
              (("oven racks", "oven rack", "oven shelves", "oven shelf", "wire racks", "wire rack",
                "grill rack", "grill racks", "rack in the oven", "racks in the oven",
                "shelves in the oven", "shelf in the oven"),
               ("clean", "cleaning", "cleaned", "grease", "greasy", "scrub", "wash", "soak",
                "burnt", "stuck", "filthy", "dirty")),
              "Lift them out and soak them in the bath or a big sink in hot water with a good squirt "
              "of washing-up liquid and a couple of tablespoons of bicarbonate of soda, for an hour "
              "or overnight: the burnt-on grease then comes off with a nylon scourer or foil. If they "
              "fit, a dishwasher does most of it, and a bin bag with a splash of ammonia left outside "
              "overnight lifts the worst without scrubbing.",
              # a burnt hand on a rack is the safety module's, and a rack that has snapped, sags or
              # will not sit level is a repair, not a cleaning job
              avoid=("hand", "hands", "finger", "fingers", "thumb", "arm", "wrist", "scald",
                     "blister", "burnt my", "burned my", "wont fit", "won't fit", "broken",
                     "sagging", "wobbly", "wont sit", "won't sit", "fell", "falls", "loose",
                     "dishwasher not draining", "dishwasher filter", "wine", "spice", "spices"),
              ask=("clean", "cleaning", "cleaned", "grease", "greasy", "scrub", "wash", "soak",
                   "burnt", "stuck", "filthy", "dirty"),
              bias=1),
        # The second group is the cleaning sense of the line, and the reader says it as a state as
        # often as a job: "the oven is greasy", "my oven is dirty" and "the oven is disgusting" all
        # reached the greeting module, because the key held only the job words `clean` and `grease`
        # and none of those lines had one. A state word is the same question. The door glass keeps
        # its own row above, which this one stands down for through the `glass` words below.
        entry("oven-clean", ("oven", ("clean", "cleaning", "grease", "greasy", "burnt", "smoke",
                                      "filthy", "dirty", "dirt", "grime", "grimy", "grubby",
                                      "stained", "stains", "scrub", "wipe", "ick", "disgusting")),
              "Make a paste of bicarbonate of soda and water, coat the inside (not the elements), leave "
              "it overnight and wipe it out with a damp cloth and a little vinegar. It takes some "
              "scrubbing but doesn't fill the kitchen with fumes like caustic oven cleaner. The racks "
              "soak in hot water with a dishwasher tablet while the paste works.",
              # A burn is answered by the safety module, and the line that follows it is still about the
              # burn: "i burnt my hand on the oven" then "should i put butter on it" was getting the
              # oven-cleaner paste because "oven" and "burnt" were in the conversation. Cleaning the
              # inside of an appliance is never what someone with a burnt hand or a blister is asking.
              # and "burn" alone is a cooking line, not a cleaning one: "my roast burnt in the oven"
              # wants nothing to do with the paste, so the cleaning sense has to be in the line too.
              avoid=("hand", "hands", "finger", "fingers", "thumb", "arm", "arms", "wrist", "skin",
                     "scald", "scalded", "blister", "butter", "myself",
                     # a line that asks whether the grease is dangerous wants an answer to that, not
                     # the method: "is a dirty oven a fire risk" was handed the paste instead
                     "fire", "fire risk", "catch fire", "dangerous", "danger", "safe", "unsafe",
                     "hazard", "a risk",
                     # the door glass is its own row above, and it names the glass
                     "glass", "panes", "pane", "window", "door glass"),
              ask=("clean", "cleaning", "cleaned", "cleaner", "grease", "greasy", "scrub", "wipe",
                   "smoke", "smokes", "smoking", "smells", "smell", "get off",
                   "burnt bits", "burnt on", "burnt stuff", "burnt grease", "use to clean",
                   # how people describe the state rather than the job: "burnt marks on the oven",
                   # "the bottom of the oven is black and burnt", "my oven door glass is filthy".
                   # Without these the line left the bake entry (which should not have it) and
                   # landed on a shrug.
                   "marks", "stains", "black", "stuck on", "scorched", "charred",
                   "filthy", "dirty", "grime", "filth", "grubby", "ick", "disgusting",
                   # the state said as a sentence rather than a job: "the bottom of my oven is
                   # burnt" named no cleaning word at all and left the bake entry, which answered
                   # with foil over a cake. "is burnt" is the shape; a bare "burnt" stays out, so
                   # "my roast burnt in the oven" keeps its cooking answer.
                   "is burnt", "burnt on the bottom", "burnt bottom", "burnt floor",
                   "oven floor", "inside is burnt", "is black", "burnt inside",
                   # "how do i get burnt off the bottom of my oven" is the same job said as a
                   # removal: the safety module reads "get burnt" as an injury and answered with
                   # twenty minutes under the tap, and this is the entry that takes the line once
                   # the burn word stands in front of an "off".
                   "burnt off", "off the bottom", "off the floor", "get rid of")),
        # "is a dirty oven a fire risk" is a yes-or-no question about the grease, and the cleaning
        # method is not an answer to it: the paste went to a line that asked about danger. It is a
        # question about tonight, so the answer says how it usually starts and what is not needed.
        entry("oven-grease-risk",
              (("oven", "cooker", "grill", "hob", "air fryer", "cooker hood"),
               ("fire", "fire risk", "catch fire", "dangerous", "danger", "risk", "risky",
                "safe", "unsafe", "hazard", "hazardous")),
              "Yes, if it is greasy: a thick layer of grease and burnt crumbs on the base, the "
              "door seal or the grill pan is what catches, and it usually starts when a spill or a bit "
              "of foil drops onto the element the next time the oven is on. It does not go up on its "
              "own, so it is not an emergency tonight: clean the base and the seal when it is cold, "
              "keep the grill pan clear, and never leave a grill or a chip pan unattended. If it does "
              "catch, close the door, switch it off at the wall and smother the pan with a lid or a "
              "fire blanket - never water on a fat fire.",
              bias=2,
              # the grease is what the yes is about, so the line has to say the oven is dirty: "is my
              # oven dangerous" on its own could be a gas smell, and that has no one answer
              ask=("dirty", "grease", "greasy", "greasy bits", "filthy", "grime", "grimy", "grubby",
                   "crumbs", "burnt", "stains", "stained", "disgusting")),
        # An appliance that smokes is a small fire or a greasy one, and the person wants to know what
        # to do tonight. The safety module keeps its fire card for flames and for smoke at room scale
        # (see APPLIANCE_SMOKE in bot/modules/safety.py), so this is the answer for one thing that
        # smokes. It leads with off at the wall, because the card used to be the only thing that said
        # anything and it said "leave the building and ring 999" about a toaster.
        entry("appliance-smoking",
              (_SMOKING_THING, ("smoke", "smokes", "smoking", "smoky", "smokey", "sparks",
                                "sparking", "scorch", "scorched",
                                "smells like burning", "smell of burning", "smells of burning",
                                "burning smell", "smells burning", "smell burning",
                                # The past tense is how people tell you what happened: "my iron
                                # smelt of burning" named nothing this entry held, so it fell
                                # through to a shrug.
                                "smelt of burning", "smelt like burning", "smelt burning",
                                "smelled of burning", "smelled like burning", "smelling of burning")),
              _smoking_appliance,
              # A burn or a scald in the same line is the safety module's: "smoke came out of the oven
              # when i burnt my hand" is about the hand. The room-scale words belong to the fire card,
              # and the non-appliance smoke (a bonnet, a chimney, a barbecue) is not this answer.
              avoid=("hand", "hands", "finger", "fingers", "thumb", "arm", "arms", "wrist",
                     "skin", "scald", "scalded", "blister", "myself", "the house", "the flat",
                     "the kitchen", "hallway", "stairs", "bonnet", "chimney", "exhaust",
                     "barbecue", "bbq", "cigarette", "cigarettes", "joint", "weed",
                     "chiminea", "firepit", "fire pit",
                     # Flames are not smoke, and the advice is not the same: "there are flames coming
                     # out of the plug socket" must not be told to unplug it. The safety module's fire
                     # card is for flame words and for smoke at room scale, so any of them stands this
                     # answer down and leaves the line to that card (or, where nothing matches, to the
                     # same shrug main gave: neither answer is worse than the wrong one).
                     "flames", "on fire", "caught fire", "alight", "ablaze", "blazing",
                     "pouring out", "billowing", "everywhere"),
              # "smells" alone is a musty machine, which has its own answer, so only the burning
              # sense of the word is a key here: "my washing machine smells" is not a fire.
              ask=("smoke", "smokes", "smoking", "smoky", "smokey", "sparks", "sparking",
                   "scorch", "scorched", "smells like burning", "smell of burning",
                   "smells of burning", "burning smell", "smells burning", "smell burning",
                   "smelt of burning", "smelt like burning", "smelt burning",
                   "smelled of burning", "smelled like burning", "smelling of burning"),
              bias=1),
        # A smoke alarm that goes off whenever the grill is on is doing its job from the wrong place,
        # and "how do i stop it going off when i cook" is a weekly question, not a fire. The cooking
        # word is what separates it from a real alarm and from the low-battery chirp, which has its own
        # answer: the same sensor that smells toast does not tell you a battery is flat.
        entry("smoke-alarm-nuisance",
              (("smoke alarm", "smoke detector", "fire alarm", "heat alarm", "alarm"),
               ("going off", "goes off", "keeps going off", "set off", "setting off", "triggered",
                "sounds", "sounding", "stop it", "silence it", "wont stop", "won't stop",
                # "my smoke alarm went off for no reason" is the line this row exists for and the
                # past tense was missing, so it fell through to the stock line
                "went off", "gone off")),
              _alarm_nuisance,
              avoid=("chirp", "chirping", "chirps", "battery", "batteries", "beep every",
                     "every few minutes", "test", "real fire", "flames", "smoke in the",
                     "landlord", "rent",
                     # the key has a bare "alarm" in it and "went off for no reason" is what
                     # anybody says about any alarm, so a burglar alarm, a house alarm, a car alarm
                     # and a phone alarm were all told to vacuum the sensing chamber of a smoke
                     # detector. The other alarms are not smoke alarms.
                     "burglar", "burglary", "house alarm", "car alarm", "vehicle alarm",
                     "phone alarm", "alarm clock", "intruder", "security alarm",
                     "security system", "panic alarm", "shop alarm", "office alarm"),
              # An alarm with nothing going on is the same nuisance alarm and the same answer.
              # "my smoke alarm went off for no reason" names no cooking and no steam, so it missed
              # this row and got the stock line, which is the coldest answer to a thing that woke
              # somebody at three in the morning: dust or an insect in the chamber, steam, and a
              # sensor past ten years are what sets a smoke alarm off when nothing is burning.
              ask=("cook", "cooking", "cooked", "toast", "toasting", "grill", "grilling", "oven",
                   "hob", "fry", "frying", "roast", "roasting", "bake", "baking", "shower",
                   "steam", "kitchen", "burning", "burnt",
                   "for no reason", "for no apparent reason", "for no obvious reason",
                   "no reason", "no reason at all", "nothing burning", "nothing was burning",
                   "nothing is burning", "nothing on fire", "no smoke",
                   "no fire", "was no fire", "nothing caught fire", "nothing cooking",
                   "nothing was cooking", "nothings cooking", "wasnt cooking", "wasn't cooking",
                   "not cooking", "randomly", "out of nowhere", "middle of the night",
                   "at 3am", "at 2am", "last night"),
              bias=1),
        # The inside of a slow cooker is not a pan on the hob, and the pan's answer would put the
        # ceramic pot over a flame it is not made for. Two things matter here: the pot cracks if
        # anything cold touches it hot, and the burnt crust on a stew lifts on its own overnight.
        entry("slow-cooker-clean", (("slow cooker", "slow cookers", "slow cooker pot", "crock pot",
                                     "crockpot", "ceramic pot", "slow cooker bowl"),
                                    ("clean", "cleaning", "cleaned", "wash", "washing", "scrub",
                                     "burnt", "burnt on", "baked on", "stuck", "crusted",
                                     "stained", "inside", "pot", "bowl", "dishwasher")),
              "Scrape it out and let the pot cool before anything cold touches it, because a hot "
              "ceramic pot can crack under cold water, and the pot and lid are then usually "
              "dishwasher safe. A crusted pot lifts clean if you soak it overnight with hot water and "
              "a dishwasher tablet or a tablespoon of bicarbonate of soda and wipe it with a sponge, "
              "with nothing abrasive on the glaze. The base is the part you do not wash: unplug it and "
              "wipe it out with a damp cloth.",
              # a slow cooker meal, a slow cooker to buy and a slow cooker that has stopped working
              # are other answers
              avoid=("recipe", "recipes", "meal", "meals", "curry", "chilli", "stew", "soup",
                     "should i buy", "worth it", "buy", "broken", "not heating", "wont heat",
                     "slow cook", "how long", "what can i make"),
              ask=("clean", "cleaning", "cleaned", "wash", "scrub", "burnt", "stuck", "crusted",
                   "stained", "smells", "smell", "dishwasher")),
        # Bread crumbs, not water: a toaster has live elements in it even when it looks cold, so the
        # answer is to empty it out dry. "How do i clean a toaster" was a shrug on main.
        entry("toaster-clean", (("toaster", "toasters"),
                                ("clean", "cleaning", "cleaned", "wash", "crumbs", "crumb tray",
                                 "burnt", "stuck", "dirty", "greasy")),
              "Unplug it and tip the crumbs out over the bin, then brush the inside with a dry pastry "
              "brush or an old toothbrush: never put water in a toaster. Wipe the outside with a damp "
              "cloth once it is cold, and empty the crumb tray every week or so, since that is what "
              "smells when it burns.",
              # what to buy, why it trips the power and why the toast is pale are other answers. A
              # toaster that smells of burning is the appliance-smoking entry above, which says to
              # pull the plug first; cleaning is the answer only when the line asks to clean it.
              avoid=("buy", "worth it", "best", "tripping", "not working", "broken", "pale",
                     "uneven", "how long", "browns", "fuse", "smells like burning", "smell of burning",
                     "smells of burning", "burning smell", "smells burning", "smoking", "smoke",
                     "sparks", "sparking"),
              ask=("clean", "cleaning", "cleaned", "wash", "crumbs", "crumb", "burnt", "dirty",
                   "greasy", "inside")),
        # An appliance that takes the power out is a different fault from a fuse in a plug, and the
        # appliance name is what tells them apart: "my kettle keeps tripping the electrics" used to
        # get the socket-fuse answer, so the appliance gets its own entry and outranks it.
        entry("appliance-tripping", (("tripping", "trips", "trip", "blowing", "blows", "cuts out",
                                      "knocking off", "keeps going off"),
                                     ("electrics", "electric", "power", "fuse box", "circuit", "rcd",
                                      "breaker", "trip switch", "mains", "socket")),
              "An appliance that trips the power is usually the appliance itself: unplug it, try it in "
              "a socket on another circuit, and if it trips again stop using it and get it repaired. "
              "Anything that takes the RCD out the moment it is plugged in has a fault to earth, so "
              "don't keep resetting the switch to check - that one needs an electrician.",
              ask=("kettle", "washing", "washer", "dryer", "tumble", "oven", "dishwasher", "fridge",
                   "freezer", "appliance", "toaster", "microwave", "hoover", "vacuum", "iron",
                   "heater", "shower", "immersion", "machine", "tv", "lamp", "extension",
                   "air fryer", "airfryer", "slow cooker", "pressure cooker", "rice cooker",
                   "bread maker", "blender", "food processor", "coffee machine", "kettle"),
              bias=2),
        entry("kitchen-machine-fault",
              (("air fryer", "airfryer", "air-fryer", "slow cooker", "pressure cooker", "instant pot",
                "multi cooker", "rice cooker", "bread maker", "bread machine", "blender",
                "food processor", "stand mixer", "kettle", "toaster", "sandwich toaster",
                "microwave", "coffee machine", "soup maker", "waffle maker", "deep fat fryer",
                "griddle", "panini", "machine", "appliance"),
               MACHINE_BURNING + MACHINE_DEAD + MACHINE_LEAKING),
              _machine_fault,
              ask=("my", "our", "the", "is", "wont", "won't", "keeps", "and", "stopped", "stopping",
                   "why", "what", "how", "should", "smoke", "smokes", "smoking", "spark", "sparks",
                   "heating", "heat", "working", "leaking", "dead", "power", "switch", "on"),
              # a fuse, a tripping circuit or a machine that shuts itself off part way has its own
              # answer above; a food that smokes in the pan is not the machine
              avoid=("fuse box", "rcd", "breaker", "circuit", "guilt",
                     # the laundry, the oven, the fridge and the boiler have their own fault entries
                     "washing machine", "washer", "dryer", "tumble dryer", "laundry", "spin",
                     "drum", "dishwasher", "oven", "fridge", "freezer", "boiler", "hoover",
                     "vacuum", "iron", "pan", "oil", "bbq",
                     "barbecue", "smoker", "cigarette", "vape", "candle", "fire alarm", "chimney",
                     "burnt my", "burnt the", "when it boils", "as it boils"),
              bias=1),
        entry("appliance-normal-cutout",
              (("kettle", "microwave", "oven", "washing machine", "washer", "dishwasher", "dryer",
                "tumble dryer", "toaster", "appliance", "boiler"),
               NORMAL_CUTOUT),
              "A kettle cutting out as the water boils, a microwave stopping when the door opens, an "
              "oven stopping when its timer ends or it reaches temperature, a washer or dryer "
              "finishing at the end of the programme: that is the machine working as designed, and "
              "there is nothing to fix. A fault looks different - it gives up part way through a job "
              "with work left to do, or it stops sooner each time it is used.",
              bias=1),
        entry("appliance-cutting-out",
              (("switches off", "switching off", "switches itself off", "switching itself off",
                "turns itself off", "turning itself off", "cuts out", "cutting out", "stops mid",
                "stopping mid", "stops halfway", "stopped mid", "keeps stopping", "keeps cutting out",
                "keeps switching off", "keeps turning itself off", "wont stay on", "won't stay on",
                "switching off before", "pops up", "popping up", "pops", "popping", "pop up",
                "stops after", "stopped after", "stops every", "stops early", "stops suddenly"),
               ("kettle", "microwave", "washing machine", "washer", "dishwasher", "toaster", "oven",
                "dryer", "tumble dryer", "coffee machine", "iron", "appliance", "hoover", "vacuum",
                "boils", "cycle", "mid cycle", "halfway", "toast")),
              _appliance_cutting_out,
              bias=1,
              # tripping the house electrics is its own answer, a laptop shutting down is the
              # machine's, not an appliance's, and an appliance that stops when its job is done is
              # not faulty at all
              avoid=("trip", "trips", "tripping", "fuse", "fuse box", "rcd", "breaker", "mains",
                     "power cut", "laptop", "computer", "pc", "phone", "iphone", "tv", "router",
                     # a hair dryer is not a tumble dryer, and its cut-out is the grille rather
                     # than the lint filter: "my hair dryer keeps cutting out" was told to empty
                     # the dryer's filter and clear its condenser
                     "hair dryer", "hairdryer", "hair drier")
                    + NORMAL_CUTOUT),
        # A kettle that will not stop is the mirror of the row above, and the mirror needs its own
        # words: "switches off" is the cut-out working too early, so none of those shapes are here.
        # The key is the fault shape first and the kettle second, and every phrase is a boil or a
        # switch, so a pan that boils dry, a toaster that will not stay down and a lamp that will not
        # turn off all keep the row they had.
        entry("kettle-will-not-switch-off",
              (("boils dry", "boiled dry", "boiling dry", "boils away", "boiled away",
                "keeps boiling", "kept boiling", "keeps bubbling", "wont stop boiling",
                "won't stop boiling", "doesnt stop boiling", "never stops boiling",
                "wont switch off", "won't switch off", "doesnt switch off", "never switches off",
                "wont switch itself off", "never switches itself off", "wont turn off",
                "won't turn off", "doesnt turn off", "wont shut off", "doesnt shut off",
                "wont stop", "doesnt stop"),
               ("kettle", "kettles", "boil", "boils", "boiling", "spout", "steam switch")),
              _kettle_will_not_stop,
              bias=2,
              # a hob, a pan, an oven and a TV each have their own answer for a thing that will not
              # turn off; "boils over" or "boils too long" is a full kettle rather than a fault with
              # the switch; and a smell after a boil-dry is the smell row's, which is about scale.
              avoid=("pan", "pans", "saucepan", "pot", "pots", "hob", "hobs", "ring",
                     "rings", "oven", "ovens", "grill", "microwave", "toaster", "air fryer",
                     "slow cooker", "washer", "washing machine", "dishwasher", "dryer", "iron",
                     "boiler", "immersion", "radiator", "heating", "tv", "telly", "light", "lights",
                     "lamp", "phone", "laptop", "fan", "heater",
                     # a full kettle boiling up the spout, and a long boil, are not a failed switch
                     "boils over", "boiled over", "boiling over", "overflow", "too full", "too long",
                     "takes ages", "slow to boil", "boils slowly",
                     # a smell afterwards is the scale-and-standing-water answer, which helps more
                     "smell", "smells", "smelt", "smelled", "smelly", "burnt", "burning", "scorch",
                     # a kettle never holds a dinner: a soup, a stew, a sauce or a pan of pasta
                     # that boiled dry was being told to bin its kettle, and the dish's own
                     # rescue (dish-caught-on-the-bottom) is the answer it needs
                     "soup", "soups", "stew", "stews", "casserole", "curry", "chilli", "chili",
                     "bolognese", "sauce", "sauces", "gravy", "stock", "broth", "porridge",
                     "pasta", "rice", "risotto", "lentils", "beans", "chickpeas", "milk",
                     "hotpot", "tagine", "goulash", "daal", "dal", "dhal"),
              ),
        # "Where is my fuse box" and "how do i reset a trip switch" were the plumber shrug, and "how do
        # i turn off the electricity" was answered with the physics of electric charge. The plug-fuse
        # entry next door is a different job (open the plug, change the 13A fuse), so this one names
        # the box and the switches rather than the fuse, and the fall and guilt-tripping guards stay.
        entry("consumer-unit",
              (("fuse box", "fuse board", "consumer unit", "trip switch", "trip switches", "rcd",
                "breaker", "breakers", "mcb", "main switch", "electricity", "power", "power supply",
                "electricity supply"),
               ("where", "find", "locate", "reset", "resetting", "tripped", "trips", "keeps", "kept",
                "turn off", "turn the power", "turn the power off", "turning off", "switch off",
                "switching off", "switch the power off", "switching the power off", "off", "on",
                "the power", "house", "home", "flat", "lights", "everything", "down")),
              _consumer_unit,
              bias=2,
              # a plug fuse, a socket and an appliance that trips are the fuse-tripping answer; a
              # person who keeps tripping over is a falls question; a laptop or a phone on the mains
              # is a battery; and a boiler, a pump or a shower tripping its own circuit is the
              # appliance answer.
              avoid=("plug", "plugs", "appliance", "appliances", "kettle",
                     "washing machine", "washer", "dryer", "dishwasher", "oven", "toaster", "shower",
                     "boiler", "pump", "immersion", "laptop", "macbook", "computer", "phone", "tablet",
                     "charger", "charging", "battery", "tripping over", "trips over", "trip over",
                     "tripped over", "over my feet", "over her feet", "over his feet", "feet", "foot",
                     "stairs", "rug", "carpet", "pavement", "kerb", "fell", "fallen", "falls",
                     "falling", "guilt tripping", "guilt trip", "guilt trips", "guilt-tripping",
                     "guilt-trip", "tripping me",
                     # a power cut, a power of attorney and a power station are not the switch
                     "cut", "cuts", "outage", "blackout", "attorney", "station", "solar", "wind",
                     "nuclear", "horsepower", "powerful", "washing",
                     # a power station, a steel plant and the grid are the electricity supply's
                     # business, not the box in the hall: "the power plant is closing" was
                     # answered with how to turn the big switch off before working on a socket
                     "plant", "plants", "factory", "factories", "grid", "pylon", "pylons",
                     "closure", "power station", "power stations")),
        entry("fuse-tripping", (("fuse", "plug", "socket", "rcd", "trip", "tripping"),
                                ("blown", "change", "keeps", "not working", "keeps tripping", "stopped",
                                 "dead")),
              "If one socket has stopped working, switch it off at the wall, open the plug and replace "
              "the fuse with one of the same rating (13A for most appliances, 3A for lamps). If the RCD "
              "or a breaker keeps tripping, unplug everything on that circuit and get an electrician: "
              "that's not a DIY job.",
              # a laptop on the mains is a battery question, not a blown fuse, and a person who keeps
              # tripping over is a falls question: "my dad keeps tripping over" was being told to
              # change a 13A fuse.
              avoid=("laptop", "macbook", "computer", "phone", "tablet", "charger", "charging",
                     "battery", "mains", "overnight",
                     # A trip is a journey on most lines: "how do i keep the kids occupied on a road
                     # trip" was told to change a 13A fuse. The bare "trip" in the key stays, because
                     # "the fuse keeps tripping" is this row's own line.
                     "road trip", "day trip", "long trip", "on a trip", "school trip",
                     "camping trip", "trip to ", "trip with", "travelling", "traveling",
                     "tripping over", "trips over", "trip over", "tripped over", "over my feet",
                     "over her feet", "over his feet", "feet", "foot", "stairs", "rug", "carpet",
                     "pavement", "kerb", "doorstep", "walking", "fell", "fallen", "falls", "falling",
                     # guilt tripping is not electrics: "keeps" plus "tripping" was enough, so
                     # "my mum keeps guilt tripping me" was told to change a 13A fuse
                     "guilt tripping", "guilt trip", "guilt trips", "guilt-tripping", "guilt-trip",
                     "tripping me")),
        # "how do i reset a tripped switch" and "a switch on the fuse box tripped" had nothing: the
        # plug-fuse card wants a plug, and the appliance card wants the appliance. A switch that has
        # gone down in the consumer unit is its own job.
        entry("fuse-box-trip",
              # The board's own words only: bare "switch", "power", "electric" and "mains" took "how do
              # i switch my phone off", "i can't switch off from work" and "how do i switch off the
              # boiler" away from the answers main already gave them.
              (("fuse box", "fuse board", "fuse", "consumer unit", "trip switch", "breaker",
                "breakers", "rcd", "rcbo", "circuit", "electrics"),
               ("tripped", "trip", "trips", "tripping", "reset", "gone off", "gone down", "off",
                "keeps", "blown", "board", "consumer unit", "circuit")),
              ("Look at which switch is down before you reset it: a single breaker is one circuit, a "
               "wider switch marked RCD or RCBO is a fault to earth. Unplug everything on that circuit, "
               "push the switch fully down and then back up, and if it holds, plug things back one at a "
               "time until it trips again - that appliance is the fault. If it will not reset with "
               "nothing plugged in, or it is the RCD that keeps going, leave it up and get an "
               "electrician. Never tape a breaker up or fit a bigger one."),
              bias=1,
              # an appliance that takes the power out has its own card, and a plug fuse is a plug
              avoid=("kettle", "washing", "washer", "dryer", "tumble", "oven", "dishwasher", "fridge",
                     "freezer", "toaster", "microwave", "hoover", "vacuum", "iron", "heater",
                     "shower", "immersion", "machine", "plug", "13a", "3a", "13 amp", "3 amp")),
        # Loft insulation is the cheapest thing a house can do to its bills and it was answering with
        # the declutter plan ("clear out the loft") and with the loft conversion's £25,000 to £60,000.
        entry("loft-insulation",
              # "roof" on its own is a subject word here as well as a costing word, so "how much does a
              # new roof cost" and "my roof is leaking" were answered with mineral wool: the roof
              # wording has to be the insulation itself.
              (("loft", "attic", "roof space", "roof insulation", "loft insulation",
                "attic insulation"),
               ("insulate", "insulated", "insulation", "lagging", "lag", "wool", "rolls", "roll",
                "cheap", "cheapest", "cost", "much", "how much", "grant", "draught", "draft")),
              ("Lay mineral wool 270mm deep, which is two layers of 100mm plus one of 70mm criss-crossed, "
               "and it costs about £300 to £600 for a typical semi if you do it yourself: it is the "
               "cheapest thing a house can do to its bills and pays back in a few years. Keep the "
               "eaves clear at the edge for ventilation, do not squash the wool down, and leave a gap "
               "round downlights unless they are marked fire-rated. Bigger jobs - a flat roof, a "
               "dormer, spray foam - want someone registered, and there are often grants."),
              # a bit of a clear-out in the loft is the declutter answer, and a roof that leaks or
              # needs replacing is a repair or a roofer's price, not insulation
              avoid=("clear out", "clearout", "declutter", "clear the loft", "tidy", "junk",
                     "conversion", "convert", "dormer", "extension", "storage", "store things",
                     "board out", "floor it",
                     "leak", "leaking", "leaks", "leaked", "replace", "replacing", "replacement",
                     "repair", "repairs", "tile", "tiles", "slate", "slates", "felt", "flat roof",
                     "repoint", "repointing", "fix", "fixing", "damp", "gutter", "gutters",
                     "chimney", "ridge", "moss")),

        # --- how much of it to buy -------------------------------------------------------------
        # `paint-room` answered any "how much paint" line with its shopping list (filler, sandpaper,
        # a dust sheet) and never said how many litres, which is the question. The quantity words
        # stand the shopping list down and this row answers with the sum and a figure.
        entry("paint-quantity",
              (("paint", "emulsion", "paint tin", "undercoat", "gloss"),
               # how many coats is its own answer already ("two coats on bare plaster, two when the
               # colour changes"), so the word is not here: this row is how many litres
               ("how much paint", "much paint", "how many litres", "litres of paint", "liters of paint",
                "how many tins", "tins of paint",
                "enough paint", "quantity of paint", "how much do i need")),
              _paint_for_the_room,
              # a colour question, a mark on the wall and a how-to-prepare line are other answers, and
              # a painted surface that is peeling or bubbling is a repair question
              avoid=("what colour", "what color", "which colour", "which color", "colour scheme",
                     "mark", "marks", "scuff", "stain", "stains", "peeling", "bubbling", "blistering",
                     "damp", "mould", "mold", "woodchip", "wallpaper", "fence", "shed", "door",
                     "radiator", "kitchen cabinet", "cupboard", "car", "bike", "model", "art",
                     "paint a picture", "nails", "makeup",
                     # what a tin costs is a price question and a live price is not something this
                     # bot has: the honest line about not looking prices up is the right answer there
                     "cost", "costs", "price", "prices", "cheap", "cheapest", "expensive",
                     "how much is", "how much does",
                     # a tin being kept is a storage question, and "keep" is how it is asked: "how do
                     # i store a part used tin of paint" was answered with litres. The gap between
                     # coats is the drying row's figure too, and it read as a quantity because the
                     # coats answer lives in this paragraph's last line.
                     "store", "storing", "stored", "part used", "part-used", "partly used",
                     "half a tin", "leftover", "left over", "lid on", "keep it",
                     "between coats", "how long between", "how long after", "wait between",
                     "second coat", "third coat", "recoat", "re-coat")),
        # A roll of wallpaper is a count of drops rather than a litre figure, and people ask it the
        # same way ("how much wallpaper do i need"), which was a shrug.
        entry("wallpaper-quantity",
              (("wallpaper", "wall paper", "wallcovering", "lining paper"),
               ("how much", "much wallpaper", "how many rolls", "many rolls", "rolls of wallpaper",
                "need", "needs", "buy", "quantity", "enough")),
              _wallpaper_for_the_room,
              # stripping, painting over and a wall that is damp or cracked are other answers
              avoid=("strip", "stripping", "remove", "removing", "woodchip", "paint over", "paint",
                     "damp", "mould", "mold", "crack", "cracked", "peel", "peeling", "feature wall",
                     "which wallpaper", "what wallpaper", "choose", "border", "phone", "laptop",
                     "screen", "wallpaper app", "windows wallpaper",
                     # and a roll's price is the same live price the bot cannot know
                     "cost", "costs", "price", "prices", "cheap", "cheapest", "expensive",
                     "how much is", "how much does"),
              bias=1),
        # A bag of it is not a watering, and "how much" on a material is a sum rather than a price.
        # Paint and wallpaper have their rows above; everything you buy by the tonne, the cubic metre
        # or the bag had none: "how much gravel do i need", "how much bark do i need for a border",
        # "how much topsoil do i need", "how much sand do i need for a patio" and "how much concrete
        # do i need for a fence post" were each a search hedge or another row's answer (a border soak,
        # a laid patio's price). One method answers all of them, because it is the same sum: an area
        # times a depth, then a weight per cubic metre. The depths below are the ones that make the
        # answer right, so they are in the one reply rather than in a row per material.
        entry("bulk-quantity",
              (("gravel", "gravels", "shingle", "pea gravel", "pea shingle", "pebbles",
                "slate chippings", "chippings", "bark", "bark chippings", "mulch", "topsoil",
                "top soil", "compost", "soil", "sand", "sharp sand", "builder's sand", "grit",
                "ballast", "hardcore", "sub base", "type 1", "concrete", "postcrete", "turf",
                "grass seed"),
               # the quantity ask, and the depth one, because "how deep should gravel be" is the
               # same question asked the other way round
               ("how much", "how many", "how deep", "how thick", "depth of", "depth should",
                "much do i need", "much will i need", "many bags", "many tonnes", "many tons",
                "bags of", "tonnes of", "tons of", "cubic", "cubic metres", "cubic feet",
                "square metres of", "coverage", "cover the", "need for", "do i need")),
              "Work it out as a volume: length times width times depth, all in metres. Gravel and slate "
              "chippings go down about 5cm deep, or 10cm if a car drives on them, so a 5m by 3m drive "
              "at 5cm is 0.75 cubic metres - about 1.2 tonnes, or fifty 25kg bags. Bark and mulch are "
              "the same sum at 5 to 7cm over the soil. Topsoil is the deep one: 10 to 15cm for a new "
              "bed, and a 20cm fill in a 3m by 1m raised bed wants 0.6 cubic metres. A cubic metre is "
              "roughly 1.5 tonnes of gravel and about a tonne of soil or compost, and a builder's bulk "
              "bag is about 0.8 of a cubic metre, so check which one the price is for. Turf and grass "
              "seed are sold by area instead: measure the lawn and add 5 per cent for the cuts.",
              # a price is a live figure this bot cannot know, and the laying and choosing of it are
              # their own answers: this row is only the quantity
              avoid=("cost", "costs", "price", "prices", "cheap", "cheapest", "expensive",
                     "how much is", "how much does", "how much would", "laid", "fitted", "quote",
                     "quotes", "hire", "rent", "which", "what type", "what sort", "best type",
                     "what kind", "what colour", "what color",
                     "how do i lay", "how to lay", "lay a", "laying a", "laying the", "install",
                     "installing", "membrane", "weed", "weeds", "weeding", "level", "edge",
                     # "sanding" folds back to "sand", so "how long do i need to leave filler before
                     # sanding" was this row's: it read the sanding as a bag of sand and answered the
                     # volume of a drive. Filler before sanding is paint-drying-time's question, and
                     # the phrases are the shape of a decorating line.
                     "leave filler", "before sanding", "sanding down", "sand it", "sanding filler",
                     "wait before sanding", "filler before",
                     # the sand and bark words are written whole: "sanding" and "barks" fold back to
                     # the material and a bare "bark" here stood the row down on its own subject
                     "sand down", "sandpaper", "sand paper", "sand pit", "sandpit", "play sand",
                     "kinetic sand", "sand castle", "sandwich", "sandwiches",
                     "dog", "dogs", "puppy", "bark at", "why does my dog",
                     "neighbour", "neighbor", "boundary", "who owns",
                     "pay half", "who pays", "cake", "potting bench", "houseplant", "indoor",
                     # a pot of compost is litres per pot, not a cubic metre of ground
                     "pot", "pots", "potting", "container", "containers", "tub", "tubs",
                     "window box", "hanging basket", "hanging baskets", "seed tray", "seed trays",
                     "houseplants",
                     # sowing and planting are their own cards, and so is watering: "how deep should
                     # i sow grass seed" and "how much water does grass seed need" were the volume
                     # sum only because "how much" and "how deep" are the ask
                     "water", "watering", "watered", "sow", "sowing", "sowed", "plant", "planting",
                     "planted", "per square metre", "per sq m", "sandbox", "sand box",
                     "chicken", "chickens",
                     # a post hole is the fence-post card's, which names the depth and the one 20kg
                     # bag of Postcrete that does a post - better than a volume sum
                     "fence post", "fence posts", "post hole", "post holes", "posthole", "postholes",
                     "postcrete", "concrete post", "concrete posts",
                     # a mix is bought by the bag and measured per square metre of wall or bed, not
                     # by the tonne of fill: "how much sharp sand and cement for a block paved drive"
                     # was this row's volume of gravel. The mortar rows answer the mix.
                     "mortar", "mortar mix", "sand and cement", "sharp sand and cement",
                     "building sand and cement", "cement mix", "how much cement", "bags of cement"),
              bias=1,
              # "do i need to sand the wall" is in the ask words ("do i need") and has the key word
              # "sand", so standing the bag-of-sand row down was not enough: this row then worked
              # out the volume of a drive, in gravel. The job that rubs a wall down is read off the
              # line, and the sanding row answers it.
              guard=lambda u: not a_sanding_job(u)),

        # "do i need to sand before painting" was the bag of sand on main ("a 25kg bag of play
        # sand covers about 0.6 square metres"), or the two-coats answer, or gravel by volume: the
        # question is whether the job wants sanding at all, and then how coarse. The verdict opens
        # the reply because that is what was asked, and the grit is in the same sentence.
        entry("sanding-before-painting",
              (("sand", "sanding", "sanded", "sandpaper", "sand paper", "sander",
                "rub it down", "rub down", "rubbed down", "key the surface", "key it"),
               ("before paint", "before painting", "before the paint", "before undercoat",
                "before a primer", "before the primer", "before gloss", "before the gloss",
                "do i need to sand", "should i sand", "need to sand", "have to sand",
                "do i need to rub", "should i rub", "do i need to key", "should i key",
                "sand it first", "sand first", "sand it down", "sanding before",
                "is sanding needed", "is it sanded", "does it need sanding",
                "sand the wall", "sand the walls", "sand the door", "sand the doors",
                "sand the woodwork", "sand the ceiling", "sand the trim",
                "do i have to sand", "should i sandpaper", "need sanding",
                "does it need sanding first",
                # the coat is named so a line asked inside a painting talk ("do i need to sand
                # it first", after "how long between coats of gloss") is about the thing the
                # conversation is on, and answers instead of standing down as another subject.
                "before the next coat", "before the second coat", "before a second coat",
                "before another coat", "before recoating", "between coats", "coats")),
              "Yes, give it a sand first: 120 grit on a block for painted woodwork and 80 to 100 on a "
              "filler patch, with the grain and light enough to take the shine off rather than the "
              "paint, then dust it down and wipe it over with a damp cloth. Old gloss has to be "
              "keyed or the new coat slides off it, and a filled patch has to be flatter than the "
              "wall around it or it shows through. Bare wood wants 120 grit, then 180, and the dust "
              "off before the first coat.",
              # the quantity and the price are the material rows' own question, and a time is the
              # filler and paint cards': this row is the yes and the grit. "between" keeps the
              # gym "sets" reading away from "how long does filler take to set".
              avoid=("how much", "how many", "cost", "costs", "price", "prices", "cheap",
                     "expensive", "bags of", "tonnes", "tons", "cubic", "square metres",
                     # new plaster has its own answer (a mist coat after two to four days) and
                     # sanding it first is not the advice: "do i need to sand a new plastered wall
                     # before painting" read as woodwork was worse than the plaster card.
                     "coverage", "between", "how long", "leave filler", "leave it to",
                     "filler take", "filler set", "drying", "wait",
                     "plaster", "plastered", "plastering", "skim", "mist coat",
                     # which of the two jobs comes first is an order, and the ordering card
                     # answers it: "do i sand first or fill first" was this row's yes.
                     "or fill", "fill first", "filler first", "before i fill", "before filling"),
              # Two jobs joined by "or" and the word "first" is a question about which comes
              # first - "varnish or sand first", "primer or sand first", "do i sand first or fill
              # first" - and this row opens with "yes", which is the wrong shape for it. The
              # ordering card in the fallback pool answers those.
              guard=lambda u: not re.search(r"\bor\b[^.?]*\bfirst\b|\bfirst\b[^.?]*\bor\b",
                                            str((u or {}).get("clean") or (u or {}).get("text") or ""),
                                            re.I),
              bias=3),
        # The commonest paint question is which paint to buy, and nothing answered it: "what paint
        # should i get", "which paint should i buy", "what kind of paint for woodwork", "do i need a
        # primer" and "what is eggshell paint for" were all hedges or a colour shrug. The paint rows
        # around it answer litres, coats, drying, the time a room takes and the shopping list, and
        # none of them names the tin.
        entry("which-paint",
              (("paint", "painting", "repaint", "emulsion", "gloss", "eggshell", "satinwood",
                "satin", "silk", "undercoat", "primer", "priming", "matt", "matte"),
               ("what paint", "which paint", "what kind", "what type", "what sort", "kind of paint",
                "type of paint", "sort of paint", "best paint", "best", "should i get",
                "should i buy", "should i use", "do i need", "need for", "for walls", "for wall",
                "for the walls", "for the wall", "for ceilings", "for a ceiling", "for the ceiling",
                "for woodwork", "for the woodwork", "for skirting", "for doors", "for a door",
                "for plaster", "new plaster", "for a bathroom", "for the bathroom",
                "for a kitchen", "for the kitchen", "for a hallway", "for the hallway",
                "for a radiator", "for kids", "kids room", "washable", "what is", "whats",
                "what's", "eggshell paint for", "gloss or", "or satinwood", "matt or", "silk or")),
              "Emulsion for walls and ceilings: matt for a bedroom or a living room, and a washable "
              "matt or eggshell where it has to take scrubbing, such as a hallway, a kitchen or a "
              "kids' room. Woodwork wants eggshell or satinwood rather than gloss, because gloss "
              "shows up every lump and brush mark. Bare wood or metal gets a primer then an "
              "undercoat; plastic, melamine and old gloss need an adhesion primer first or the paint "
              "peels; anything that gets hot, like a radiator or a pipe, wants a heat-resistant "
              "paint made for metal. New plaster wants a mist coat - emulsion thinned by about a "
              "fifth with water, no vinyl - to soak in and seal the dust. Buy a sample pot before the "
              "big tin, because colour on a wall is not colour on a card.",
              # the litre figure, the coats, the drying time, the day a room takes, a colour, a
              # price, a mark on the wall and a surface that is peeling are all other questions
              avoid=("how much paint", "much paint", "how many litres", "litres of paint",
                     "how many tins", "how many coats", "coats of paint", "second coat",
                     "between coats", "how long", "dry", "drying", "how many days", "how much",
                     "how many", "cost", "costs", "price", "prices", "cheap", "expensive",
                     "what colour", "what color", "which colour", "which color", "colour scheme",
                 # a colour is not a tin: "what is a good neutral paint colour" matched this row
                 # on "paint" and "what is" as well as colour-choice's gate, and the tie went to
                 # the tin card. The colour question keeps its own row.
                 "neutral", "good colour", "best colour", "colour choice", "colour to paint",
                 "colour for", "which white",
                     "mark", "marks", "scuff", "stain", "stains", "peeling", "bubbling",
                     "blistering", "wallpaper", "fence", "shed", "car", "bike", "model", "art",
                     "paint a picture", "nails", "makeup", "store", "storing", "leftover",
                     "left over", "dispose", "get rid of", "thin", "white spirit",
                     # a room that is already the subject has its own rows, and each answers the
                     # question it was asked: the steamy room, the kitchen, the radiator, the order
                     # of work and the filler-and-sandpaper list were all better than this card
                     "bathroom", "kitchen", "radiator", "ceiling first",
                     "paint a room", "paint the room", "paint my room", "paint a bedroom",
                     # the order to paint a ceiling in is its own card, and it was better than
                     # the shopping list
                     "ceiling", "ceilings", "ceiling first",
                     "paint the walls", "paint the wall", "paint a wall", "to paint a room",
                     "matt or silk", "silk or matt", "decorate", "decorating", "decorated",
                     # a door, a run of skirting and a metal gate each have a how-to row that says
                     # what to do to that surface, and those answers were better than this card
                     "door", "doors", "front door", "back door", "skirting", "skirting boards",
                     "gate", "gates", "garden gate", "metal gate", "metal", "railings")),
        # Painting over a colour that is already there is a different job from kitting out a room
        # for paint: it is a question about coats and undercoat, and "how do i cover dark paint"
        # was being answered with how to roll a ceiling while "how do i paint a wall over dark
        # paint" got the shopping list.
        entry("paint-over-a-colour",
              # "cover" is not a key word: it is the everyday verb of a lid and a stew, and
              # "ok back to the chicken, should i cover it" was answered with two coats of
              # emulsion. What makes this the painting line is the paint, and the colour under it.
              (("paint", "painting", "repaint", "go over", "going over", "paint over"),
               ("dark", "darker", "darkest", "strong colour", "strong color", "bright colour",
                "bright color", "bright red", "red wall", "dark green", "dark blue",
                "old colour", "old color", "previous colour", "previous color", "dark paint",
                "block the colour", "hide the colour", "cover the wall", "over the top",
                "grimy white", "yellowed")),
              "Two coats of a decent emulsion usually cover a dark wall, and going much lighter "
              "than the old colour can need three; sand and wipe the wall down first and do not "
              "thin the paint. If the old colour is a strong red or a dark green, ask for a "
              "combined primer and undercoat tinted towards the new colour - it saves a coat and "
              "stops the old shade grinning through.",
              bias=1),
        entry("paint-room", (("paint", "painting"), ("room", "wall", "walls", "living", "need",
                                                    "before", "prepare",
                                                    # A room named is a room to paint: "what do i
                                                    # need to paint the front room" and "gonna paint
                                                    # the spare room at the wknd" both want the
                                                    # shopping list before they start. The hall and
                                                    # the landing are left out on purpose: a
                                                    # correction naming one of them ("i want to
                                                    # paint the kitchen" / "i meant the hallway")
                                                    # has to keep the advice already on the screen,
                                                    # and a row keyed on the hall re-answers from
                                                    # the top instead.
                                                    "bedroom", "bedrooms", "lounge", "living room",
                                                    "front room", "dining room", "spare room",
                                                    "nursery", "whole flat", "whole house")),
              "Before paint you need filler for the holes, fine sandpaper, masking tape, a dust sheet, "
              "a roller and tray, a brush for edges and an old screwdriver to open the tin. One litre "
              "of emulsion covers about 12 square metres, so measure the walls and buy two coats' "
              "worth.",
              # "what colour should i paint my living room" is a colour question, and this entry was
              # answering it with the shopping list: `paint-room` keeps the how-to and gives up the
              # choosing.
              avoid=("what colour", "what color", "which colour", "which color", "colour", "colours",
                     "color", "colors",
                     # "marks on the painted wall" and "how do i get a mark off the wall" are not a
                     # shopping list for painting the room, and this entry was answering both
                     "mark", "marks", "marked", "scuff", "scuffs", "stain", "stains",
                     "fingerprint", "fingerprints", "smudge", "smudges",
                     # how much to buy is paint-quantity's question, not the shopping list's
                     "how much paint", "much paint", "how many litres", "litres of paint",
                     "how many coats", "coats of paint",
                     # which tin to buy is the which-paint row's question: "what paint do i need
                     # for the walls" and "washable paint for a kids room" were given the filler and
                     # sandpaper shopping list
                     "what paint", "which paint", "what kind of paint", "what type of paint",
                     "best paint", "washable", "washable paint", "kids room"),
              # No ask here on purpose: a room named is a room to paint, with or without a
              # question word - "gonna paint the spare room at the wknd" wants the shopping list
              # as much as "what do i need to paint the front room" does. A correction
              # ("i meant the hallway") is screened off in the composer instead.
              ),
        # A "how long before I paint over it" line was the shopping list: `paint-room` is keyed on
        # paint beside "before", so "how long should i wait before painting over filler" got a list of
        # sandpaper and dust sheets and never a drying time, which is the whole question. The duration
        # words stand the list down and this row answers with the hours.
        entry("paint-drying-time",
              (("paint", "painting", "repaint", "repainting", "filler", "filling", "undercoat",
                "gloss", "emulsion", "primer", "silicone", "sealant", "caulk", "wood filler"),
               ("how long", "wait", "waiting", "dry", "dries", "drying", "cure", "curing",
                "overnight", "hours", "before painting", "before i paint", "before sanding")),
              # The answer leads with the paint, because "how long does paint take to dry" is the
              # line people send most and it used to be met with the filler timing. Filler and
              # silicone keep their own sentences after it.
              "Emulsion takes a second coat in 2 to 4 hours and is properly hard in about a day; "
              "undercoat and gloss want overnight, 16 to 24 hours, and longer in a cold room. A "
              "small hole of filler is hard in about an hour, so it can be sanded and painted the "
              "same day, but a deep fill wants overnight or it shrinks back and shows. Silicone has "
              "to be a paintable one - most sanitary silicones cannot be painted at all - and it "
              "wants 24 hours to cure before a brush goes near it.",
              # how long the job takes, how much paint, how many coats, a price and a colour are all
              # other questions, and a finish that is coming off is a repair
              avoid=("how long does it take to paint", "how long to paint", "take to paint",
                     "paint a room", "paint the room", "paint my room", "paint the walls",
                     "how many coats", "how much paint", "how many litres", "much paint",
                     "cost", "costs", "price", "prices", "cheap", "expensive", "how much is",
                     "how much does", "what colour", "what color", "which colour", "which color",
                     "peeling", "peeling off", "flaking", "bubbling", "blistering", "strip",
                     "stripping", "wallpaper", "last", "lasts", "goes off", "shelf life",
                     # how often to recoat is the coats row's, and it already gives the hours
                     "between coats", "how many coats", "coats of paint", "recoat", "re-coat",
                     "second coat", "third coat",
                     # and keeping a paint workable is not asking how long it takes: the row below
                     # answers that, and this one answered it with filler times
                     "drying too fast", "drying too quickly", "dries too fast", "dry too fast",
                     "from drying", "keeps drying", "before it dries", "open time", "wet edge")),
        # The same hours, asked from the filler's side: "how long do i need to leave filler before
        # sanding" is the sanding question, and it was read as a bag of sand to buy and then as the
        # paint's drying times, with the filler in the second sentence. The filler's own hour is the
        # answer, so it leads here.
        entry("filler-drying-time",
              (("filler", "wood filler", "polyfilla", "filling", "filled", "skim", "skimming"),
               ("how long", "leave", "wait", "dry", "dries", "drying", "set", "sets", "harden",
                "hardens", "sand", "sanding", "sanded", "rub down", "rubbing down", "before")),
              "A thin skim of filler is hard in about an hour and can be sanded the same day; a deep "
              "fill wants overnight, because it shrinks back if the middle is still soft when you rub "
              "it down. Rub it with 120 grit on a block rather than with your fingers, and stop when "
              "the edge blends into the wall - two thin fills are quicker than one thick one that has "
              "to be dug out. Give it a coat of watered-down emulsion before the paint, or the patch "
              "drinks the first coat and shows as a dull spot.",
              # how much filler or sand to buy is the quantities rows' question, and a pipe, a car
              # or a cake has a filler of its own
              avoid=("how much", "how many", "bags", "cost", "costs", "price", "prices",
                     "quid", "pounds", "£", "fuel", "petrol", "diesel", "radiator",
                     "car", "pipe", "sink", "bath", "cake", "sandwich", "sandpaper",
                     "what is", "what are", "what's", "meaning", "recipe",
                     # which of the two comes first is an order of work, not a drying time:
                     # "do i sand first or fill first" keeps the row that says the step that
                     # would spoil the other goes last
                     "first", "which one first", "before that", "order", "order to"),
              bias=2),
        # The other half of the drying question: not how long it takes but how to keep it workable.
        # "how do i keep my paint from drying too fast" was answered by the leftover-tin card ("stir
        # sand into it and take it to the tip"), which is a worse answer than none, because it sounds
        # like advice. Heat, sun, a draught and a wide tray are what dry a paint too fast, and a wet
        # edge is what the job stands or falls on.
        entry("paint-drying-fast",
              (("paint", "painting", "emulsion", "gloss", "undercoat", "eggshell", "satin",
                "roller", "brush", "wet edge", "paint tin", "tin of paint", "tray"),
               ("drying too fast", "drying too quickly", "dries too fast", "dries too quickly",
                "dry too fast", "dry too quickly", "keeps drying", "from drying", "stop it drying",
                "before it dries", "going off the brush", "drying out", "wet edge", "open time",
                "workable", "flash", "dry so fast", "dries so fast", "dry so quick", "dries so quick",
                "drying so fast", "so fast", "too hot", "in this heat"),),
              "Heat and moving air are what dry a paint too fast, so keep the room cool and out of "
              "direct sun, shut the window and turn any fan off. Lid the tin and decant only what you "
              "will use in ten minutes, because a wide tray is all surface; a smaller tub keeps it "
              "workable. Water-based paint can take a splash of water, no more than one part in ten, "
              "or a paint conditioner from a decorator's shop. Then work to a wet edge: do one wall at "
              "a time in one go, roll into the bit you just did rather than next to it, and do not "
              "stop halfway across. A brush or roller you are coming back to in a few minutes goes in "
              "a damp cloth or a bag, and a skin on the paint in the tin gets lifted off, not stirred "
              "back in.",
              # how long it takes to dry is paint-drying-time, a leftover tin is paint-tins, and a
              # finish that has dried badly is a repair
              avoid=("how long", "how many hours", "overnight", "second coat", "between coats",
                     "how many coats", "get rid", "dispose", "throw", "bin", "tip", "recycle",
                     "leftover", "old paint", "how much paint", "cost", "price", "cheap",
                     "peeling", "flaking", "cracking", "bubbling", "blistering", "strip",
                     "wallpaper", "smell", "smells", "fume", "fumes", "colour", "color",
                     "which paint", "best paint", "nail polish", "spray")),
        # Keeping a part-used tin is the third question about a tin, after how long it takes to dry
        # and what to do with a finished one: "how do i stop my paint going lumpy", "my paint has
        # gone lumpy", "can i use paint that has been frozen", "how do i stop paint skinning over"
        # and "how do i store paint over winter" were a search hedge or the wallpaper card.
        entry("paint-keeping",
              (("paint", "painting", "emulsion", "gloss", "undercoat", "eggshell", "satin",
                "tin of paint", "paint tin", "part used paint", "part-used paint"),
               ("store", "storing", "storage", "keep", "keeping", "kept", "lumpy", "lumps",
                "lumpy paint", "skin", "skinned over", "skinning over", "skin on the paint",
                "gone thick", "gone hard", "thickened", "separated", "frozen", "gone off",
                "between coats", "between jobs", "over winter", "in the garage", "in the shed")),
              ("Paint keeps for years if the lid is sealed: wipe the rim clean, press the lid down "
               "with a block of wood until it clicks, and store the tin upside down so any skin forms "
               "at the bottom rather than on top. Keep it somewhere frost-free, because paint that has "
               "frozen is never right again. A tin that has gone lumpy or thick can often be saved: "
               "lift the skin off, strain it through a pair of tights or a paint strainer into a clean "
               "tub, and stir it well - water-based paint takes a splash of water, oil-based takes "
               "white spirit, no more than one part in ten. When it is full of hard lumps, or it "
               "smells sour, it is past saving and goes to the tip."),
              # a brush or a roller is washed, a tin nobody will open again is dried out for the tip,
              # and how long a coat takes to dry is the drying row's question
              avoid=("brush", "brushes", "paintbrush", "paintbrushes", "roller", "rollers",
                     "get rid", "dispose", "throw", "bin", "the tip", "to the tip", "recycle",
                     "how long does it take", "how long to paint", "how many coats", "how much paint",
                     "second coat", "between coats of", "drying too fast", "dries too fast",
                     # thinning is its own answer and it leads with the ratio: "how do i thin lumpy
                     # emulsion" wants that, not how to keep a tin
                     "thin", "thins", "thinning", "thin it", "thin the", "thinner", "water it down",
                     "wet edge", "peeling", "flaking", "bubbling", "strip", "wallpaper", "smell",
                     "smells", "fumes", "colour", "color", "which paint", "nail polish", "spray"),
              bias=1),
        # A colour that came out darker than the tin promised is the same complaint people make about
        # henna and about a foundation, and the bot had nothing for it here: "my emulsion looks too
        # dark" and "my paint is too bright" got the shrug, "the paint came out darker than the
        # sample" and "my gloss came out too dark" got the stain-removal card, "my wood stain is too
        # dark" got the white-water-ring card, "the colour i painted the wall is too strong" got "are
        # you pleased with it?", and "can i lighten paint that is too dark" got the search hedge. The
        # answer is the same in all of them and it is not "repaint the wall in darker paint": a wet
        # paint reads lighter than it dries, so the first thing to do is let it dry and look again in
        # daylight, and a coat that has dried too dark is not lightened by anything that can be added
        # to it - it is sanded and covered, or left and lived with.
        entry("paint-too-dark",
              (("paint", "painted", "painting", "emulsion", "gloss", "undercoat", "eggshell",
                "satin", "satinwood", "varnish", "lacquer", "wood stain", "stain", "wood dye",
                "fence stain", "decking stain", "paint tin", "tin of paint", "roller"),
               ("too dark", "come out dark", "came out dark", "came up dark", "darker than",
                "much darker", "so dark", "dried dark", "dries dark", "goes dark", "went dark",
                "too strong", "too bright", "too intense", "too deep", "too orange", "too yellow",
                "too red", "lighten", "lightening", "lighter", "pale it down", "palest",
                "hate the colour", "wrong colour", "wrong color", "not the colour", "regret",
                "darker sample", "the sample")),
              "Give it a day before you judge it: paint reads about a shade lighter while it is wet, "
              "so a wall that looks too strong tonight has usually settled by tomorrow, and the light "
              "you look at it in changes it as much as the paint does. If it is still too dark once it "
              "is hard, nothing can be added to a coat to lighten it - so the fix is either one coat "
              "of the colour you wanted over the top (a pale colour covers a dark one in two or three "
              "coats, and a test patch on a scrap of plasterboard or lining paper will tell you how "
              "many before you buy another tin), or a glaze of white emulsion wiped over it while it "
              "is tacky to lift it a shade. If the tin was a match to a sample, take a photo in "
              "daylight and the tin back to the shop: most will retint or exchange one they mixed "
              "wrong. A wood stain that went too dark sands back to bare wood and starts again with a "
              "pale one, since stain sinks in rather than sitting on top.",
              # a streak or a patch is an uneven coat, not the wrong colour; a mark on the wall, a
              # carpet or a shirt is a stain to lift; how much to buy, how long it takes to dry, which
              # paint to choose, stripping it off and what a tin costs are all answered elsewhere
              avoid=("streak", "streaks", "streaky", "patchy", "patchy coverage", "blotchy",
                     "uneven", "roller marks", "brush marks", "lap marks",
                     "mark", "marks", "scuff", "scuffs", "smudge", "spill", "spilled", "drip",
                     "drips", "carpet", "sofa", "shirt", "clothes", "fabric", "curtain", "hands",
                     "skin", "nail", "nails", "hair",
                     "how much", "how many litres", "litres", "tins of", "cost", "costs", "price",
                     "prices", "cheap", "expensive", "how much is", "how much does",
                     "how long", "drying time", "dry between", "second coat", "how many coats",
                     "which paint", "what paint", "best paint", "what colour should",
                     "which colour should", "what color should", "strip", "stripping", "remove",
                     "removing", "peel", "peeling", "flaking", "bubbling", "blistering",
                     "wallpaper", "woodchip", "fence up", "shed", "car", "bike", "model", "canvas",
                     "picture", "art", "nails", "makeup", "printing", "printer", "photo"),
              # a colour that came out wrong is a judgement on the finish, and a card that offers to
              # lift a mark off a carpet must not win it
              bias=2),
        # --- and the paper on the wall --------------------------------------------------------
        # Taking old paper off and painting over it are two different jobs, and the bot had neither:
        # "how do i strip wallpaper", "how do i remove woodchip", "can i paint over wallpaper" and
        # even "do i need to strip it first" after "its got woodchip on it" all got the search hedge.
        # Woodchip is its own entry because it comes off in two goes and wetting it first ruins the
        # top layer; one paragraph about both would have to hedge both.
        entry("woodchip-off",
              (("woodchip", "wood chip", "woodchip paper", "anaglypta", "textured wallpaper"),
               ("strip", "strips", "stripping", "remove", "removing", "off", "get off",
                "come off", "take down", "steam", "steamer", "scrape", "scraping", "soak",
                "soaking", "stuck", "peel", "peeling", "paint", "painting", "over", "cover")),
              "Woodchip comes off in two goes: lift the top layer dry with a wide scraper first (it "
              "comes away in sheets), then score and soak the backing paper for 10 to 15 minutes and "
              "scrape that off. Do not wet it before the top is off, or the chips turn to mush and "
              "smear across the wall.",
              # a line about the paint colour, or about buying the house, is not this job
              avoid=("buy", "buying", "selling", "sell", "price", "cost", "how much is",
                     "wood chip boiler", "boiler", "biomass")),
        entry("wallpaper-peeling",
              (("wallpaper", "wall paper", "lining paper", "paper"),
               ("peel", "peels", "peeled", "peeling", "lifting", "lifts", "loose", "bubble",
                "bubbles", "bubbling", "blister", "blistering", "corner", "corners", "seam",
                "seams", "coming away", "came away", "flapping", "repair")),
              "Paste it back rather than strip it: lift the loose edge with a knife, scrape the old "
              "paste off the wall behind it with a filling knife, spread a thin even coat of overlap "
              "adhesive (border and overlap adhesive) on the wall, press the paper back and smooth it "
              "out from the middle with a damp sponge. A bubble in the middle gets a slit with a "
              "stanley knife, paste, and the same press. Damp patches that keep coming back are not a "
              "paper problem.",
              # how long it stays up, or a colour, is not the repair, and a damp wall is the damp
              # question's.
              avoid=("how long", "strip", "stripping", "remove all", "whole room", "damp", "mould",
                     "mold", "wet", "leak", "what colour", "which colour", "paint over"),
              bias=1),
        entry("paint-over-wallpaper",
              (("paint", "painting", "repaint", "emulsion", "undercoat"),
               ("wallpaper", "wall paper", "lining paper", "paper", "walls", "wall", "over")),
              "Not over woodchip or any textured paper: the pattern shows through, every seam lifts, "
              "and a thinned first coat will not hold it down. Smooth, sound lining paper can be "
              "painted with a mist coat (emulsion thinned by about a tenth) and then two ordinary "
              "coats, and any bubble or lifted seam comes off before the roller comes out.",
              # the paper has to be the thing being painted: the shopping list for a room, a colour,
              # and the stain on the wall are all other answers'.
              ask=("wallpaper", "wall paper", "lining paper", "paper", "over"),
              avoid=("what colour", "what color", "which colour", "which color", "colour",
                     "colours", "color", "colors", "toilet paper", "newspaper", "exam paper",
                     "printer paper", "wrapping paper", "sandpaper", "paint stripper",
                     "paintbrush", "paint brush", "fence", "door", "doors", "radiator",
                     "ceiling")),
        entry("wallpaper-off",
              (("wallpaper", "wall paper", "wallpapers", "lining paper", "paper"),
               ("strip", "strips", "stripping", "remove", "removing", "off", "get off",
                "come off", "comes off", "take down", "steam", "steamer", "scrape", "scraping",
                "soak", "soaking", "stuck", "peel", "peeling", "old")),
              "Score it all over, soak it, then scrape it: a paper tiger (or a fork) gives the water "
              "somewhere to go, warm water with a splash of washing-up liquid needs 10 to 15 minutes "
              "to do its work, and a scraper held almost flat lifts the paper without gouging the "
              "plaster. A steamer is quicker than a sponge for a whole room, and an old papered room "
              "is a weekend's job.",
              # the key word is the paper on a wall, not paper: a phone's wallpaper, printing, an exam
              # and a newspaper are all someone else's answer, and a stain on papered walls is the
              # damp question.
              # a corner that has lifted is the paste-back repair, above, not the whole job.
              avoid=("peel", "peels", "peeled", "peeling", "lifting", "bubble", "bubbles",
                     "bubbling", "corner", "corners", "phone", "iphone", "android", "mobile",
                     "tablet", "ipad", "laptop",
                     "computer", "pc", "desktop", "screen", "lock screen", "home screen",
                     "background", "download", "app", "print", "printer", "printing", "exam",
                     "essay", "newspaper", "toilet paper", "damp", "mould", "mold",
                     "condensation", "woodchip",
                     # A mark on papered wall is a mark, not a paper to come off: "how do i get a
                     # mark off the wallpaper" was told to score it all over and soak it, because
                     # "get off" and "wallpaper" are both in this key. Nothing to strip is being
                     # asked about there, and `wallpaper-mark` answers it.
                     "mark", "marks", "stain", "stains", "dirty", "clean", "cleaning", "wash",
                     "washed", "scuff", "scuffs", "smudge", "smudges", "grease", "greasy",
                     "fingerprints", "fingerprint", "spot", "spots", "wipe")),
        # --- a mark on papered wall -----------------------------------------------------------
        # "marks on the wallpaper", "dirty wallpaper" and "how do i get a mark off the wallpaper"
        # all had no answer on main: the paint and strip cards know the paper, not the mark on it,
        # and the wall card's answer is a pencil rubber on emulsion.
        entry("wallpaper-mark",
              (("wallpaper", "wall paper", "papered wall", "papered walls", "lining paper",
                "vinyl wallpaper", "flocked wallpaper", "woodchip"),
               ("mark", "marks", "stain", "stains", "dirty", "clean", "cleaning", "wash",
                "washable", "scuff", "scuffs", "smudge", "smudges", "grease", "greasy",
                "fingerprints", "fingerprint", "spot", "spots", "wipe")),
              "Go at it dry first and test a hidden corner: a soft pencil rubber or a clean, barely "
              "damp cloth with a drop of washing-up liquid lifts most marks off paper, working from "
              "the bottom up so drips do not streak. Water is what ruins wallpaper, so keep the "
              "cloth as dry as it can be - a washable vinyl paper takes a mild soap, a printed or "
              "flocked one usually will not, and a mark that will not lift is better patched or "
              "covered than scrubbed.",
              # the job of stripping, hanging or painting the paper is each its own card, and a
              # damp patch is the damp question
              avoid=("strip", "stripping", "remove the paper", "remove the wallpaper", "take down",
                     "hang", "hanging", "hanging paper", "paste", "repaste", "put up", "putting up",
                     "put wallpaper", "put the wallpaper", "put paper", "putting paper", "paper the",
                     "paper a wall", "papering", "ceiling", "ceilings", "size", "sizing", "how much",
                     "how much do i need", "choose", "which wallpaper", "what colour", "what color",
                     "border", "borders", "peel", "peeling", "lifting", "bubble", "bubbling",
                     "seam", "seams", "repair", "replace", "paint", "painting", "paint over",
                     "damp", "mould", "mold", "condensation", "phone", "iphone", "laptop",
                     "screen"),
              bias=1),
        # Wallpaper off and over is above; these are the paint jobs people ask for by the thing
        # being painted - woodwork, a ceiling, a door, a radiator, tiles, a table - plus hanging
        # paper. One row per actual question, keyed on the thing painted and what is asked.
        # "what colour should i paint the bathroom" is the colour row's question, so every new
        # decorating row holds the same colour words `paint-room` holds.
        entry("paint-over-gloss", (("paint over", "painting over", "paint on top of", "over gloss",
                                    "over the gloss", "over old paint", "gloss paint",
                                    "paint gloss", "paint a gloss", "undercoat", "primer",
                                    "priming"),
                                   ("gloss", "glossy", "satin", "sheen", "undercoat", "primer",
                                    "cupboard", "cupboards", "kitchen", "door", "doors",
                                    "woodwork", "skirting", "banister", "radiator")),
              "Sand it dull first: new paint needs a key to grip, so take the shine off old gloss with "
              "120 grit, wipe off the dust, then one coat of undercoat and your topcoat. A water-based "
              "satin goes on after the sanding alone and dries in a couple of hours; oil gloss straight "
              "onto old gloss is the way to get peeling in a year.",
              avoid=("what colour", "what color", "which colour", "which color", "colour",
                     "colours", "color", "colors", "peeling off") + _TAKING_PAINT_OFF),
        entry("paint-bathroom", (("paint", "painting", "repaint", "emulsion"),
                                 ("bathroom", "kitchen", "shower room", "steamy", "steam",
                                  "mould resistant", "mould-resistant", "mould proof")),
              "Use a mid-sheen, eggshell or bathroom paint rather than matt emulsion: it shrugs off "
              "steam and can be wiped, where matt goes patchy over a bath. Two coats is a day's work "
              "for a kitchen or bathroom. Paint does not stop mould on its own, so sort the extractor "
              "fan or open a window while you steam.",
              avoid=("what colour", "what color", "which colour", "which color", "colour",
                     "colours", "color", "colors", "mould on", "mould in", "black mould")
                    + _TAKING_PAINT_OFF),
        # How long the job takes is its own question, and it was reaching the row above for the
        # life of a coat: "how long does it take to paint a room" was answered with how many years
        # two coats last, because "how long" was in the keeping row's key and none of the paint
        # rows asked for it (garnet-orca followed "i want to paint the kitchen" with "how long
        # will it take" and got "Five to ten years").
        entry("paint-time", (("paint", "painting", "repaint", "decorate", "decorating",
                               "decorated", "emulsion", "walls"),
                              ("how long", "how many days", "how many hours", "time", "take",
                               "takes", "long", "day", "days", "weekend", "afternoon")),
              "A normal room is a day's work with two coats: an hour or two to cut in and roll, then "
              "about four hours before the second coat, so most people do the first coat in the "
              "evening and the second the next morning. A whole flat or house is roughly a day per "
              "room, plus a day for the ceilings and woodwork. A single door, a run of skirting or a "
              "radiator is a morning: an hour or two a coat, with overnight between the coats.",
              avoid=("how many coats", "coats of paint", "coat of paint", "between coats",
                     "recoat", "drying time", "how long to dry", "how long does paint take",
                     "how long does it last", "how long will it last", "last", "lasts",
                     "mould", "how much", "cost", "price", "pricey",
                     # "how long does it take for paint to dry" is the coats-and-drying row's
                     # question, not the time the job takes
                     "to dry", "dry", "drying",
                     # "where do i take old paint" is a disposal question and it answered the hours
                     # a room takes, because "take" is in the ask and the tin rows said none of the
                     # words below. A tin that has to go is not a tin being painted with.
                     "old paint", "take old paint", "leftover paint", "left over paint",
                     "part used tin", "unused paint", "dispose", "disposal", "get rid of",
                     "getting rid of", "tip", "the tip", "recycling centre", "recycling center",
                     "household waste", "waste centre", "skip", "throw away", "throw out",
                     "throwing out", "goes", "where can i take", "where do i take",
                     # a drying time is the row below's question, and "how long should i wait
                     # before painting over filler" and "how long before i can paint silicone" both
                     # answered how long a whole room takes. The things that are drying name it.
                     "filler", "filling", "filled", "silicone", "sealant", "caulk",
                     "undercoat", "primer", "priming", "before painting", "before i paint",
                     "before sanding", "before i sand", "wait", "waiting", "to dry", "till it dries",
                     "before the second coat", "between coats"),
              ask=("how long", "how many", "time", "take", "takes", "day", "days", "hours",
                   "decorate", "decorating", "decorated"),
              bias=1),
        # How many years a coat lasts is its own question, and it had no answer: the years were a
        # sentence inside the steamy-room card, which is how a follow-up of "how long will it take"
        # was answered with "Five to ten years" (garnet-orca). The fact has a card now, and the
        # steamy card keeps the day the job takes.
        entry("paint-life",
              (("how long", "how many years", "how often", "lifespan", "life of", "last", "lasts",
                "lasted", "recoat"),
               ("paint", "painting", "painted", "repaint", "repainting", "emulsion", "gloss",
                "satin", "eggshell", "walls", "woodwork", "exterior", "outside")),
              "Interior emulsion on a sound wall is good for about five to ten years, and gloss on "
              "woodwork about the same; a steamy bathroom sits at the shorter end because the steam "
              "lifts the edges first. Pale colours fade slowly and dark ones show scuffs, so most "
              "rooms get a refresh coat at five years rather than a full repaint.",
              avoid=("to dry", "drying", "take to", "between coats", "how many coats", "coats",
                     "how long to dry", "mould", "cost", "price", "much does", "how long does it take")),
        entry("paint-coats", (("how many coats", "coats of paint", "coat of paint", "second coat",
                               "two coats", "how long between coats", "between coats", "recoat",
                               "drying time", "how long to dry", "how long does paint take",
                               # "how long does it take for paint to dry" says "to dry" and not
                               # "how long to dry", and with no part-1 match it scored 2 and reached
                               # nothing
                               "to dry", "take to dry", "long to dry"),
                              # The paint is the fence, and "dry" is not a paint word: with it
                              # here the fence held the line on its own, and "i hung my washing
                              # out to dry" and "my hair takes ages to dry" were both answered
                              # "Two coats on bare or patched plaster". Every drying question
                              # about paint says paint, a coat, a wall, a door or the finish it is
                              # going on, so the fence keeps those and "dry" alone stops being
                              # enough.
                              ("paint", "painting", "coat", "coats", "wall",
                               "walls", "emulsion", "door", "woodwork")),
              "Two coats on bare or patched plaster, and two whenever the colour changes; a pale wall "
              "going a pale colour can take one. Leave about two to four hours between coats, and a "
              "full day before you push furniture back against it. Touch the wall first: hard and not "
              "tacky means it is ready."),
        # How long plaster takes to dry is its own question and it had no row of its own: the line
        # reached the bone-healing row, because "plaster" is in that row's parts and "how long" in
        # its time, so "how long does plaster take to dry" was answered "About six weeks for most
        # bones - six for a wrist or collarbone" (found typing at main 8e89c21). A wall that has
        # been plastered, skimmed or soaked is a drying question, and the paint rows above stand
        # down for "to dry" on purpose, so nothing else in the domain answers it.
        entry("plaster-dries", (("plaster", "plasters", "plastering", "plastered", "skim",
                                 "skims", "skimmed", "skimming", "render", "rendering",
                                 "plasterboard", "backing coat"),
                                ("dry", "dries", "drying", "to dry", "dried", "fully dry",
                                 "before i paint", "before painting", "before i can paint",
                                 "paint over it", "paint on it", "paint it", "mist coat",
                                 "when can i paint", "how long before", "wait", "cure",
                                 "curing")),
              "A thin skim is ready for a mist coat after two to four days and painted properly "
              "after about a week. A backing coat, or a wall taken back to brick, is roughly a "
              "week for every 10mm of thickness, so a fortnight or more. The colour is the best "
              "gauge - pale, chalky and the same all over means dry, and a patch that is still "
              "dark and cool has not finished, which wants a day or two more. Painting it before "
              "it has gone pale traps the water and blows the paint within a month.",
              # an arm in plaster, a cast and a fracture are the bone row's questions; a plaster
              # on a cut is the wound answer's; a damp wall, a wet patch and a ceiling that has
              # dried are the damp rows' own questions, with their own answers
              avoid=("in plaster", "plaster on", "plaster cast", "cast", "surgery", "arm", "arms",
                     "leg", "legs", "wrist", "ankle", "knee", "bone", "bones", "broken",
                     "broke", "break", "fracture", "fractured", "hospital", "cut", "cuts",
                     "wound", "graze", "blister", "tooth", "teeth",
                     # a colour, a price or a product is another row's question
                     "what colour", "what color", "which colour", "which color", "colour",
                     "colours", "color", "colors", "how much", "cost", "price", "how many",
                     "wallpaper", "hang", "hanging", "strip", "stripping", "tiles", "tiling",
                     "tile the", "mould", "mold", "black mould", "condensation",
                     # a damp wall, a wet patch and a ceiling that has dried are the damp and
                     # water-stain rows' questions, and this row took all of them on its first
                     # run: "how do i dry out a damp wall" is finding the water, not a mist coat
                     "damp", "dampness", "damp patch", "wet patch", "wet", "water", "leak",
                     "leaking", "stain", "stains", "yellow marks", "brown patch"),
              bias=2),
        # The line that describes the finish rather than the job - "without streaks", "avoid roller
        # marks", "why is my paint patchy", "a smooth finish" - had no answer of its own: the walls
        # went to the shopping list, the roller marks to the search hedge, and "brush marks" to
        # brushing your teeth, because "brush" is a toothbrush word as well. The word that carries
        # the question is the fault, so the fault is the key and the paint is the fence.
        entry("paint-streaks",
              (("paint", "painting", "painted", "repaint", "emulsion", "gloss", "satin", "eggshell",
                "undercoat", "topcoat", "roller", "brush", "decorating", "decorate",
                "the walls", "wall", "walls", "woodwork"),
               ("streak", "streaks", "streaky", "streaking", "patchy", "patchiness",
                "roller marks", "roller mark", "brush marks", "brush mark", "lap marks",
                "lap mark", "lines", "smooth", "smooth finish", "even finish", "finish",
                "uneven", "blotchy", "flashing", "shiny patches", "shiny patch",
                # the denial reader drops a key made of a word inside "without", and "without
                # streaks" is the commonest way people ask for this, so the phrase carries its
                # own "without" and is passed instead
                "without streaks", "without streak", "no streaks", "not streaky",
                "without brush marks", "no brush marks", "without roller marks",
                "no roller marks", "without lap marks", "no lap marks", "without lines",
                "no lines", "not patchy", "no patches", "without patches")),
              "Streaks are an uneven coat, not a bad paint: roll in strips a roller wide and lap the "
              "last strip while it is still wet so no edge dries alone, with a light even load rather "
              "than pressing the roller dry. Brush slowly, one way, and don't go back over paint that "
              "is setting. On a wall already patchy, a second full coat cures it; touching up spots "
              "makes it worse.",
              avoid=_TAKING_PAINT_OFF + (
                     "off", "clean", "cleaning", "wipe", "scrub", "scuff", "scuffs", "fingerprint",
                     "fingerprints", "stain", "stains", "stained", "crayon", "pencil", "pen",
                     "marker", "dirty", "grease",
                     # the pieces of wood and board each have their own card, and it is a better
                     # answer to "how do i paint a door without brush marks" than this one
                     "door", "doors", "ceiling", "ceilings", "skirting", "radiator", "radiators",
                     "tiles", "cupboard", "cupboards", "kitchen unit", "kitchen units", "shed",
                     "fence", "fencing", "deck", "decking", "garden", "furniture", "wardrobe",
                     "table", "chair", "chairs", "bathroom", "wallpaper", "woodchip",
                     # nail polish is a paint that goes on a person, and "brush marks on my nails"
                     # was the nails card's line before this row touched it
                     "nails", "nail", "my nails", "toenails", "fingernails", "manicure",
                     "nail polish", "nail varnish", "polish", "pedicure")),
        # "how do i thin emulsion" and "should i water down gloss" were the search hedge: the paint
        # rows talk about coats and surfaces, and nothing said how much water or spirit to add.
        # A brush is not the wall. "How do i store paintbrushes between coats" was answered with how
        # many coats a wall wants, "what do i do with the brush between coats" went to the charity
        # clothes card, and "can i wrap the brush in cling film overnight", "how do i clean a brush
        # after emulsion" and "my paintbrush has gone hard" reached nothing at all. The tool and its
        # keeping are one question, so the brush words are the key and the keeping is the ask.
        entry("paint-brush-care",
              (("brush", "brushes", "paintbrush", "paintbrushes", "paint brush", "paint brushes",
                "brush bristles", "bristles", "bristle", "roller", "roller sleeve", "paint roller",
                "sleeve", "sleeves"),
               # `store`, `storing`, `stored` are ask words, not key words: with a keeping word in
               # the key the row looks like a shelf-life row, and `lookup._keeps_failing` stands a
               # shelf-life row down when the line says a fault keeps happening - which is exactly
               # "my brush keeps losing bristles", the shape this row exists for.
               ("between coats", "between the coats", "overnight", "over night",
                "keep", "keeps", "keeping", "kept", "clean", "cleaning", "cleaned",
                "wash", "washing", "washed", "wash out", "washing out", "rinsed", "rinse",
                "gone hard", "went hard", "hard", "stiff", "dried out", "drying out", "dry out",
                "wrap", "wrapped", "cling film", "clingfilm", "carrier bag", "plastic bag",
                "save", "saved", "reuse", "re-use", "next coat", "tomorrow", "lunchtime",
                "white spirit", "turps", "brush restorer", "soak", "soaking",
                # "how do i get paint out of a paintbrush" named the brush and a removal and no care
                # verb at all, so the row looked past it and the answer was the search hedge
                "out of", "get out", "got out", "get the paint out", "get paint out", "remove",
                "removing", "cleaned up", "clean up", "after painting", "once i have finished",
                # "how do i get oil paint off a brush" is the same wash with none of the wash words,
                # and it was the search hedge while "how do i clean a brush" was answered
                "off a brush", "off my brush", "off the brush", "off a paintbrush",
                "off my paintbrush", "out of a brush", "out of my brush", "out of the brush",
                "out of my paintbrush", "out of a paintbrush", "out of the bristles",
                "off a roller", "out of a roller", "out of the sleeve", "get it off",
                "get the paint off", "paint off",
                # a brush that sheds is the same tool with a fault, and the line usually says what
                # it does rather than what it wants: "my brush keeps losing bristles"
                "losing bristles", "loses bristles", "lose bristles", "lost bristles",
                "keeps losing", "keep losing", "losing hair", "sheds", "shedding", "shed",
                "falling", "falling out", "coming out", "keeps coming out",
                "bristles falling out", "bristles coming out", "loose bristles", "moulting",
                "falling apart", "falls apart", "coming apart", "comes apart")),
              _paint_brush_care, bias=3,
              # a brush that sheds is stated as a fact rather than asked about: "my brush keeps
              # losing bristles" is the whole question, so the fault words are ask words of their own
              ask=("how do i", "how to", "what do i do", "can i", "should i", "between coats",
                   "overnight", "store", "keeping", "keeping it", "clean", "cleaning", "wash",
                   "washing", "save", "reuse", "gone hard", "went hard", "hard", "stiff",
                   "dried", "dry", "wrap",
                   "losing", "loses", "lose", "lost", "sheds", "shedding", "shed", "moulting",
                   "falling", "coming out", "keeps coming out", "keeps losing", "keep losing",
                   "falling apart", "coming apart"),
              # a hair brush, a toothbrush and a yard brush are other questions, and so is art on a
              # canvas: the paint in this one is on a wall, a door or a skirting board.
              avoid=("hair", "my hair", "hairbrush", "hair brush", "curling", "straighteners",
                     "teeth", "toothbrush", "tooth", "gums", "makeup", "make up", "make-up",
                     "foundation", "blush", "eyebrow", "eyeliner", "nail brush", "nails",
                     "bbq", "barbecue", "grill brush", "chimney", "sweep", "yard", "broom",
                     "snow brush", "dog", "cat", "pet", "grooming", "canvas", "watercolour",
                     "watercolor", "sketch", "draw", "drawing", "brush up", "brush off",
                     "brush past", "brushed off", "paintbrush plant", "shaving brush",
                     "toilet brush", "bottle brush", "bottlebrush", "basting", "pastry brush",
                     # a blind, a curtain and a shirt sleeve are not a paintbrush, and `blind` and
                     # `sleeve` in the key were taking them: "how do i clean roller blinds" and
                     # "how do i clean a shirt sleeve stain" both had good answers before this row
                     "blind", "blinds", "curtain", "curtains", "shirt", "shirts", "jumper",
                     "jumpers", "cardigan", "fabric", "upholstery", "sofa", "settee", "carpet",
                     "carpets", "duvet", "bedding", "stain", "stains", "clothes", "clothing",
                     # "its a shiny patch on the sleeve, can i save it" is a garment that has gone
                     # shiny, and "sleeve" is a key word here because of the roller sleeve, so the
                     # shine is what stands this row down: `shiny`, `shine`, `scorch` and the
                     # garments themselves, which are `clothing.garment-shine`'s line.
                     "shiny", "shine", "shines", "shone", "shininess", "scorch", "scorched",
                     "scotch", "jacket", "jackets", "blazer", "trousers", "skirt", "skirts",
                     "seat of my trousers")),
        # Paint spilt on something soft. The row sits here, beside the brush and the tin, rather
        # than at the end of the table: an append at the very end is where every lane adds, and it
        # is the one place that conflicts with everyone.
        entry("paint-spilt-on-a-soft-thing",
              (("paint", "paints", "emulsion", "gloss", "undercoat", "primer", "varnish",
                "gloss paint", "emulsion paint", "spilt paint", "spilled paint"),
               ("carpet", "carpets", "rug", "rugs", "sofa", "sofas", "settee", "couch", "cushion",
                "cushions", "mattress", "upholstery", "armchair", "stair carpet", "spilt", "spilled",
                "spill", "knocked over", "tipped over", "out of", "remove", "get out", "blot")),
              "Blot what is still wet with kitchen paper and do not rub it, because rubbing pushes the "
              "paint into the pile. Emulsion and the water-based satins lift with cold water and a "
              "little washing-up liquid worked in with your fingertips and blotted out again; oil "
              "gloss and varnish need a cloth damped with white spirit, dabbed from the edge of the "
              "mark inwards so it does not spread. Try white spirit on a corner you cannot see first, "
              "since on a wool carpet it can lift the dye.",
              # a pot of paint on a wall, a door, a floor or a brush is somebody else's line, and so is
              # a colour that came out wrong: "my gloss came out too dark" and "the paint came out
              # darker than the sample" were sent here for the cold-water treatment because they say
              # "came out", and no splashed carpet is the complaint
              avoid=("too dark", "darker", "too strong", "too bright", "too pale", "too orange",
                     "lighten", "lighter",
                     "wall", "walls", "ceiling", "door", "doors", "radiator", "skirting", "banister",
                     "window", "frame", "floor", "floors", "floorboards", "wood", "wooden",
                     "wallpaper", "clothes", "shirt", "jeans", "jumper", "trousers", "fabric",
                     "hand", "hands", "skin", "hair", "brush", "brushes", "paintbrush",
                     "paintbrushes", "paint brush", "paint brushes", "roller", "sleeve", "tray",
                     "thin",
                     "thinning", "dilute", "colour", "what colour", "which colour", "peeling",
                     "bubbling", "drying", "how long", "coats", "two coats",
                     # "old paint tins" is what to do with the tin, which is `paint-tins`' line
                     "old paint", "leftover", "left over", "tin", "tins", "bin", "bins", "tip",
                     "household waste", "recycling", "recycle", "dispose", "disposal", "shed",
                     "garage", "store", "storing", "keeping",
                     # a car's paint is not spilt on the carpet, however the line says "get it
                     # out": "how do i get scratches out of car paint" met this row on "paint"
                     # and "out of" and was told to blot the pile. The cars row answers it.
                     "car", "cars", "van", "vans", "bodywork", "paintwork", "bumper",
                     "bonnet", "scratch", "scratches", "scratched", "scuff", "scuffs",
                     "lacquer", "alloy", "alloys", "wheel", "wheels"),
              bias=2),

        entry("paint-thin",
              (("thin", "thinning", "thinned", "water down", "watering down", "watered down",
                "dilute", "diluting", "diluted", "white spirit", "white spirit in"),
               ("paint", "painting", "emulsion", "gloss", "satin", "eggshell", "undercoat",
                "topcoat", "varnish", "primer", "matt", "matt emulsion", "oil based", "oil-based",
                "water based", "water-based")),
              "Emulsion thins with water, about one part to ten of paint; oil-based gloss thins with "
              "white spirit at much the same rate. Add it a little at a time and stir until the paint "
              "runs off the stick in a steady ribbon. A first mist coat on new plaster is thinner "
              "still, about 20 to 30 per cent water. Don't thin to stretch a tin: it covers less, and "
              "that is where streaks come from.",
              avoid=("hair", "thinning hair", "my hair", "gravy", "sauce", "soup", "blood",
                     "trees", "tree", "apples", "hedge", "hedges", "seedlings", "paint stripper",
                     "stripper", "remove", "stripping")),
        entry("paint-ceiling", (("paint", "painting", "repaint", "mist coat"),
                                ("ceiling", "ceilings", "ceiling rose", "ceiling.", "roller",
                                 "emulsion", "white", "cover", "two coats")),
              "Do the ceiling first and the walls after. Cut in round the edges with a brush and a 2cm "
              "band, then roll in strips about a metre wide with a long-handled roller, overlapping "
              "the last strip while it is still wet so the edges do not dry into lines. Work away from "
              "the window and towards the light so you can see where you have been, and roll the last "
              "metre without reloading to feather it out. Put a dust sheet down because a ceiling "
              "always drips. Matt emulsion, two coats, and a ceiling that is already white may need "
              "only one: if it is a bare or patched ceiling, thin the first coat by about a tenth as a "
              "mist coat.",
              # taking paint OFF a ceiling, a damp patch, a leak, a stain and a crack are their own jobs
              avoid=_TAKING_PAINT_OFF + ("damp", "leak", "leaking", "water", "stain", "stains",
                                         "crack", "cracked", "crumbling", "flaking", "peeling",
                                         "coming off", "coming away", "come off", "comes off",
                                         "fell off", "falling off", "blown",
                                         "mould", "mold", "asbestos", "skim", "plaster",
                                         "insulate", "loft", "bulb", "light", "fan",
                                         "smoke alarm", "dryer", "colour", "color")),
        entry("paint-door", (("paint", "painting", "repaint", "gloss"),
                             ("door", "doors", "front door", "back door", "panelled door")),
              "Take the door off and lay it flat if you can, and paint the top and bottom edges first so "
              "it still fits after. Then the panels, then the frame parts, brushing with the grain. "
              "Lightly sand between coats and give gloss about 16 hours to harden before it goes back "
              "on its hinges.",
              # taking paint OFF a door is the stripping row below, and paint on your hands after
              # painting one is the hands row: this entry was answering "how do i remove paint from a
              # door" with "take the door off and paint the top and bottom edges first", and as a
              # follow-up it repeated itself at a person with paint on their hands
              avoid=("paint a room", "painting a room", "what colour", "which colour", "colour",
                     "sticking", "stiff", "squeak", "squeaking", "lock", "key", "handle",
                     "old paint", "hands", "hand", "fingers", "skin") + _TAKING_PAINT_OFF),
        entry("paint-radiator", (("paint", "painting", "repaint"),
                                 ("radiator", "radiators", "heated towel rail")),
              "Turn the heating off and let it go cold, then brush or roller it with a water-based "
              "satin, painting in the same colour as the wall if you want it to disappear. An old "
              "cast-iron radiator wants a metal primer first. Leave it a day to dry before the heat "
              "goes back on, or the paint softens.",
              avoid=_TAKING_PAINT_OFF),
        # A floor is its own paint and had no row at all: "how do i paint the floor", "...the
        # stairs" and "...floorboards" were punts once the hobby row stood down.
        entry("paint-floor", (("paint", "painting", "repaint", "floor paint", "sand"),
                              ("floor", "floors", "floorboard", "floorboards", "floor boards",
                               "stairs", "staircase", "stair treads", "steps", "wooden floor")),
              "Sand a wooden floor back to bare wood, vacuum the dust off, then a primer and two thin "
              "coats of floor paint, keeping a wet edge so the overlaps do not show. Ordinary "
              "emulsion will scuff off in weeks, so use a paint made for floors, and leave it a full "
              "24 to 48 hours before anything walks on it - a stair run wants that on both sides of "
              "each tread.",
              bias=1,
              # a floor that squeaks, is being tiled, is laminate or has been cleaned is a
              # different job, and tiles over a floor is the tile answer's
              avoid=("squeak", "squeaks", "creak", "creaks", "clean", "cleaning", "mop", "mopping",
                     "laminate", "tile", "tiles", "tiling", "carpet", "underlay",
                     "sanding machine", "hire", "sander") + _TAKING_PAINT_OFF),

        # A concrete floor is a different job from a wooden one, and while it was a sentence in
        # the floor row it was the sentence the repeat composer picked to follow "Same for
        # floorboards", so somebody with boards was told to etch concrete and buy garage paint.
        # One subject per row: this one names itself, and the floor row keeps the boards.
        entry("paint-concrete-floor", (("paint", "painting", "repaint", "floor paint", "etch",
                                        "seal", "epoxy"),
                                       ("concrete floor", "concrete floors", "garage floor",
                                        "garage floors", "concrete slab", "concrete steps",
                                        "concrete stairs")),
              "A concrete floor wants an etch and a paint made for it, not gloss: sweep and degrease "
              "it first, let it dry, then etch it with a weak acid or a floor etch from the paint "
              "shop so the paint has something to grip. Two coats of a garage-floor paint or a "
              "two-pack epoxy, rolled in one direction, with 12 to 24 hours between them, and keep "
              "feet and tyres off it for two or three days. Fresh concrete needs a month to cure "
              "before any of it, and a damp floor needs a damp-proof coat first.",
              bias=1,
              avoid=("squeak", "squeaks", "creak", "laminate", "tile", "tiles", "tiling", "carpet",
                     "floorboard", "floorboards", "wooden floor") + _TAKING_PAINT_OFF),
        # Varnish is not paint: the floor row's key claimed it and answered with "two thin coats
        # of floor paint", which is the wrong tin for somebody asking about varnish.
        entry("varnish-floor", (("varnish", "varnishing", "re-varnish", "revarnish", "lacquer",
                                 "stain", "staining"),
                                ("floor", "floors", "floorboard", "floorboards", "floor boards",
                                 "wooden floor", "stairs", "staircase", "stair treads", "steps")),
              "Sand the boards back to bare wood, vacuum and tack the dust off, then thin the first "
              "coat of varnish as the tin says and brush it with the grain. Three coats, with a "
              "light sand and a dust-off between each, and a full 24 hours between coats. A "
              "water-based varnish dries clear and does not yellow, so it suits pale wood; an "
              "oil-based one stands up better in a hall or on stairs but darkens pine. Keep the "
              "room ventilated and leave it two or three days before anything heavy walks on it.",
              bias=1,
              avoid=("squeak", "squeaks", "creak", "laminate", "tile", "tiles", "tiling", "carpet",
                     "concrete") + _TAKING_PAINT_OFF),
        entry("paint-skirting", (("paint", "painting", "repaint", "gloss", "satin"),
                                 ("skirting", "skirting board", "skirting boards", "architrave",
                                  "door frame", "banister", "banisters",
                                  # the rest of the painted wood in a room is this same job:
                                  # "how do i paint woodwork" and "...a windowsill" were punts
                                  "woodwork", "windowsill", "windowsills", "window sill",
                                  "window sills", "picture rail", "dado rail", "handrail",
                                  # a window frame is the same painted woodwork job and was a shrug:
                                  # "how do i paint a window frame" fell between the painting rows and
                                  # the two window-fault rows, which stand down on the brush
                                  "window frame", "window frames", "sash", "sash window", "window",
                                  "windows", "casement")),
              "Sand them, wipe the dust off and run masking tape along the carpet, then brush with the "
              "grain in long strokes and a light load on the brush so it does not run onto the wall. "
              "Two thin coats beat one thick one, and satin or eggshell is easier to wipe than gloss. "
              "If you are doing the walls too, do the woodwork first.",
              # A line that names the surface and a finish and asks nothing ("its gloss on the
              # woodwork") is a detail of the question already on the table, not a fresh how-to:
              # after "how long do i leave paint before the second coat" the wait was the
              # question, and this row's how-to took the turn. The ask words are ones the key
              # does not hold, because a word the key has already used cannot answer the ask too.
              ask=("how", "what", "which", "should", "can", "best", "way", "sand", "sanding",
                   "prep", "prepare", "method", "start", "need to", "give"),
              avoid=("clean", "cleaning", "dust", "dusty", "wipe") + _TAKING_PAINT_OFF),
        # A window frame is not a skirting board and it is not a picture either: "how do i paint a
        # window frame" and "how do i paint a sash window" were both given "start with acrylics...
        # paint the same simple thing - one mug, one window - five times", which is advice for
        # learning to paint pictures. Masking the glass and opening the window before the paint
        # sets are the two things that decide whether the job went well.
        entry("paint-window", (("paint", "painting", "repaint", "gloss", "satin", "undercoat",
                                "primer"),
                               ("window", "windows", "sash", "sash window", "sash windows",
                                "casement", "casement window", "window frame", "window frames",
                                "frame", "frames", "sill", "window sill", "window sills")),
              "Mask the glass with tape, or cut in at a shallow angle with a 25mm brush and keep the "
              "brush lightly loaded so it does not run onto the pane, and paint the frame before the "
              "sliding parts. On a sash window do the staff beads and the pulley recess first, then "
              "the sashes. Run a knife round the join and open the window a crack while the paint is "
              "still soft, or it dries shut; outside wants an undercoat and two coats of gloss on a "
              "dry day.",
              # a window that will not open, is painted shut, leaks or is being replaced is a
              # fault with its own answer, and so is the picture-painting question and the blind
              # "how do i paint a room with no windows" is a room, not a window, and it was
              # answered with this row's glass and sashes - so the room, the wall and the
              # windowless phrase all stand this one down
              avoid=("room", "rooms", "wall", "walls", "ceiling", "ceilings", "bedroom",
                     "living room", "hallway", "hall", "kitchen", "bathroom", "no window",
                     "no windows", "without windows", "windowless", "no natural light",
                     "clean", "cleaning", "cleaner", "dust", "dusty", "wipe", "condensation",
                     "misted", "leak", "leaks", "leaking", "damp", "draught", "draft", "cold",
                     "broken", "cracked", "crack", "shattered", "replacement", "replace", "tint",
                     "film", "frost", "blind", "blinds", "curtain", "curtains", "shutter",
                     "shutters", "stuck", "painted shut", "wont open", "won't open", "wont close",
                     "won't close", "acrylic", "acrylics", "watercolour", "canvas", "picture",
                     "painting of", "a painting") + _TAKING_PAINT_OFF,
              bias=2),


        entry("wallpaper-hang", (("hang", "hanging", "put up", "how do i paper", "paste the",
                                  # "how do i wallpaper a wall" was the search hedge: the verb is
                                  # the noun in this job, and nothing held it
                                  "wallpaper", "wallpapering", "papering", "paper a", "paper the"),
                                 ("wallpaper", "wall paper", "lining paper", "a wall", "the wall",
                                  "wall", "walls", "ceiling", "ceilings", "room")),
              "Size the wall and let it dry, then cut each drop with an extra 5cm top and bottom, paste "
              "the paper (not the wall) and let it soak for the time the roll says, and hang the first "
              "drop plumb from a pencil line rather than from a corner. Smooth it outwards from the "
              "middle with a paper smoother, and butt the joins rather than overlapping them. A "
              "ceiling is the same paper on a bigger job: paper it before the walls, and work away "
              "from the window.",
              # "hang", "put up" and "a wall" reach every other wall job there is, so the things that
              # get hung and put up are fenced off: a picture, a mirror, a shelf, a telly and a
              # curtain rail each have their own row, and so do plastering a wall and taking paper off
              # one. Nothing here is about papering over a wall. The bare verb is not the job, so
              # the paper itself has to be in the line.
              guard=_the_paper_is_in_the_line,
              avoid=("cheap", "which", "best", "bathroom", "mould", "mold",
                     "picture", "pictures", "frame", "frames", "photo", "photos",
                     "mirror", "mirrors",
                     "shelf", "shelves", "bracket", "brackets", "tv", "television", "telly",
                     "curtain", "curtains", "rail", "pole", "blind", "blinds", "coat", "coats",
                     "coat hook", "hook", "hooks", "light", "lights", "light fitting", "radiator",
                     "door",
                     # a fixing job carries the wall as its object, so the wall itself is the word
                     # that has to hold this row off: "how do i hang a picture on a plasterboard
                     # wall" was given the papering method
                     "plasterboard", "plaster board", "stud", "studs", "rawlplug", "rawplug",
                     "hollow wall", "drill", "drilling", "fixings", "fixing",
                     # not "plastering": avoid words match on the stem, and "a plaster wall" is
                     # the whole point of the row. Paint on paper is the other direction, and
                     # "can i paint over lining paper" is its own answer.
                     "doors", "skim", "skimming", "damp", "stain", "paint", "painting", "painted",
                     "paint over", "paint on top",
                     "stripping", "remove", "removing", "off")),
        entry("paint-tiles", (("paint", "painting", "repaint"),
                              ("tile", "tiles", "tiling", "bathroom tiles", "kitchen tiles")),
              "Tiles take paint if you use a tile-specific primer and two coats of tile paint, and it "
              "holds up well on a splashback or a wall above a bath. Sand the glaze dull and clean off "
              "any grease first, or the paint peels in sheets. Not worth it on a shower floor or "
              "anywhere a foot or a scouring pad goes: re-tiling is the honest fix there.",
              avoid=("grout", "clean", "cleaning", "mould", "black", "cracked", "crack", "loose",
                     "tile a", "how do i tile", "floor") + _TAKING_PAINT_OFF),
        entry("paint-garden-wood", (("paint", "painting", "repaint", "stain", "varnish", "preserve",
                                     "preserver", "treat", "wood stain"),
                                    ("fence", "fences", "shed", "sheds", "gate", "gates", "trellis",
                                     "decking", "pergola", "garden furniture", "garden table",
                                     "garden bench", "greenhouse", "greenhouses")),
              "Wait for two dry days above about 10C and get the surface clean and bone dry before you "
              "start, because paint on damp timber peels within a season. Then two thin coats rather "
              "than one fat one: fence panels want a shed-and-fence stain, a shed or a wooden gate a "
              "preservative and a topcoat, and a metal gate a rust primer and a gloss made for metal. "
              "Brush or spray along the grain on wood.",
              bias=1,
              avoid=("garden table", "weed", "lawn", "grow") + _TAKING_PAINT_OFF),
        # The pieces people name when they mean a thing to paint. Each of these was a punt once
        # the hobby row stood down (snug-parrot on #7159: every word a fence stands down on needs
        # a row behind it), and a chair and a table are the same sanding and priming job.
        entry("paint-furniture", (("paint", "painting", "repaint", "gloss"),
                                  ("cupboard", "cupboards", "wardrobe", "table", "tables", "dresser",
                                   "chest of drawers", "sideboard", "bookcase", "shelves", "shelf",
                                   "furniture", "kitchen cabinets", "kitchen cupboard",
                                   "cabinet", "cabinets", "kitchen unit", "kitchen units",
                                   "unit", "units", "chair", "chairs", "stool", "stools",
                                   "bench", "benches", "desk", "desks", "bed", "beds",
                                   "bed frame", "cot", "cots", "crib", "cribs", "toy", "toys",
                                   "toy box", "chest", "trunk", "picture frame", "photo frame",
                                   "mirror frame", "dressing table", "bedside table", "drawers")),
              "Sand or de-gloss the surface, wipe the dust off, then a stain-blocking primer, then two "
              "thin coats of a water-based satin with a light sand between them. Take the doors and "
              "handles off if it has them, and let it harden a good 24 hours before anything goes back "
              "on: furniture paint that is rushed stays soft and sticks.",
              avoid=("clean", "cleaning", "smell", "musty", "grease", "polish", "wax", "dust",
                     "undercoat", "satin") + _TAKING_PAINT_OFF),
        # Taking paint off is the other half of the job, and it is not painting the thing: the rows
        # above take the thing painted as their key, so without this a person with old paint on a
        # door was told how to add more.
        # "why is my ceiling paint flaking" is a diagnosis, and paint-strip answered it with a heat
        # gun: the removal row keys "flaking" and "peeling" because those are how people say "get it
        # off", so a question about *why* it let go got the tool for taking it off. The two rows are
        # now told apart by the ask: a how-to remove keeps the strip, a why-it-happens gets this.
        entry("paint-flaking",
              (("flaking", "flaky", "flaking off", "flake off", "flakes off", "peeling off",
                "bubble", "bubbles", "bubble up", "bubbles up",
                "peels off", "peeled off", "peeling", "blistering", "blistered", "bubbling",
                "bubbled", "blown plaster", "coming off the wall", "coming off the ceiling",
                "coming away from the wall", "paint is flaking", "paint flaking",
                "paint is peeling", "paint peeling",
                # paint that has let go of the surface is the same question said the other way:
                # "paint coming away from the ceiling" was the painting-order card, and once that
                # card was told to stand down it had no answer at all.
                # The noun rides in the phrase. "fell off", "came off" and "coming off" on their
                # own were the whole subject, and this row's other half already holds wall,
                # walls, ceiling and bathroom, so anything that came off a wall was a paint
                # question: a mirror, a picture and a tile all got "find the reason before you
                # repaint". Said with the paint in it, every tense keeps its answer.
                "paint coming off", "paint is coming off", "paint come off",
                "paint comes off", "paint came off", "paint has come off",
                "paint coming away", "paint is coming away", "paint came away",
                "paint falling off", "paint is falling off", "paint fell off",
                "paint has fallen off"),
               ("paint", "painted", "painting", "emulsion", "gloss", "ceiling", "wall", "walls",
                "woodwork", "wood", "skirting", "door", "doors", "radiator", "plaster", "bathroom",
                "kitchen", "why", "what causes", "cause")),
              ("Find the reason before you repaint, or it comes back: feel the patch for damp (a "
               "bathroom, a kitchen or a ceiling under a cold roof is the usual one), and press the "
               "plaster - if it crunches or sounds hollow it has blown and needs cutting back to "
               "sound plaster and filling. Paint flakes off a ceiling most often because an old "
               "distemper or silk finish was painted over without a primer, or bare plaster was "
               "painted without a mist coat, so scrape back to the firm edge, sand the edge flat, "
               "and prime the bare patch before you paint. Then two coats of the same finish, and "
               "deal with the steam or the leak, because paint cannot hold on a wet wall."),
              # the same four-word score as the broad paint-room row and the soap-bubble row on
              # "why does paint bubble on a wall", so this one has to win the tie: it is the only
              # row about the paint letting go.
              bias=1,
              avoid=("remove", "removing", "removal", "strip", "stripping", "get off", "take off",
                     # paint that came off a hand, a brush or a tin is not paint that let go of a
                     # wall: the hands row and the tins row answer those.
                     "my hands", "hands", "hand", "fingers", "skin", "nails", "brush", "brushes",
                     "roller", "tin", "tins", "clothes", "carpet", "splash", "spilled", "spilt",
                     "sand off", "scrape off", "how do i get", "nail polish", "nail varnish",
                     # "old paint" is the stripper row's phrase, kept so by its own tests: "old paint
                     # is peeling on my door" is a door to take back to bare wood, not a wall to
                     # diagnose.
                     "old paint", "layers of paint", "years of paint",
                     "wallpaper", "wall paper", "skin", "hands", "brush", "nail", "nails",
                     "car", "cars", "metal", "gate", "fence", "shed", "boat", "kerb", "wheel",
                     # a tile that has come off a wall is not paint that let go of it: the tile
                     # repair row answers that, and this row read "a tile has come off the wall in
                     # my bathroom" as a paint diagnosis.
                     "tile", "tiles", "tiling", "grout")),

        entry("paint-strip", (("remove", "removing", "strip", "stripping", "get off", "take off",
                               "sand off", "sanding off", "peel", "peeling", "flaking", "flaky",
                               "old paint", "layers of paint",
                               # "how do i get paint off tiles" has no removal verb but does have the
                               # word off, and it tied with the tile-painting row without this
                               "off"),
                              ("paint", "painted", "gloss", "varnish", "emulsion", "woodwork", "wood",
                               "door", "doors", "skirting", "banister", "door frame",
                               "radiator", "tiles", "stair")),
              "Work out which paint it is first: a heat gun or a chemical stripper lifts old oil gloss "
              "in a few minutes, while a water-based paint softens under a warm damp cloth. Sandpaper "
              "alone clogs in seconds on a thick layer, so strip the bulk and sand only the last film. "
              "Test anything painted before about 1960 for lead - a kit costs a few pounds - and never "
              "sand that one.",
              # paint on skin, on a brush or on a carpet is a different job with a different answer
              avoid=("wallpaper", "wall paper", "stain", "stains", "nail polish", "nail varnish",
                     # why it let go is `paint-flaking`; this row is how to take it off
                     "why is", "why does", "why has", "why are", "what causes", "blistering",
                     "blistered", "bubbling", "bubbled", "keeps flaking", "keeps peeling",
                     "flaking off the wall", "flaking off the ceiling", "peeling off the wall",
                     "brush", "brushes", "roller", "hands", "hand", "fingers", "skin", "carpet",
                     "clothes", "shirt", "washing machine",
                     # a colour, not a job: "how do i paint a wall off white"
                     "off white", "off-white", "white", "colour",
                     # and taking a door off is how you paint one, not a stripping question:
                     # "should i take the door off to paint it" was handed the paint stripper
                     "off to paint", "to paint it", "when painting", "before painting",
                     "before you paint", "to paint the",
                     # a tin nobody is going to open is not a surface: "what do i do with old paint"
                     # and "can i put old paint in the bin" were handed the heat gun, because "old
                     # paint" is in this key and the tin row's own key needs the surface word this
                     # one has. The disposal words belong to `paint-tins`, so they stand this row
                     # down - and a surface word still wins, because "old paint on the door" carries
                     # "the door" and not one of these.
                     "what do i do", "should i do", "what should i do", "do with", "get rid",
                     "in the bin", "put it in the bin", "where do i take", "throw", "throwing",
                     "chuck", "chucking", "bin it",
                     "dispose", "household waste", "recycling centre", "leftover", "tins", "pots",
                     # a tin of paint left over is the disposal row's question, not a stripping job
                     "tin", "tins", "dispose", "disposal", "recycling centre", "tip",
                     # the row keys on "remove" and "wood", so "how do i remove a scratch from wood"
                     # came here and was told about a heat gun; a mark in the finish is not old paint
                     "scratch", "scratches", "scratched", "scratching", "scuff", "scuffs",
                     "scuffed", "mark", "marks", "marked", "dent", "dents", "dented",
                     "chip", "chips", "chipped", "ring", "rings", "water mark", "heat mark",
                     # the bare "off" in the key above is what makes this the answer to a stripping
                     # job, and it also made it the answer to every line that turns something off:
                     # "how do i turn a radiator off" and "how do i switch a radiator off for the
                     # summer" were told how to lift old gloss with a heat gun. A device switched off
                     # is not paint coming off, so the switching verbs stand this row down.
                     "turn off", "turning off", "switch off", "switching off", "shut off",
                     "shutting off", "turn it off", "turn them off", "switch it off",
                     "turn the radiator off", "turn a radiator off", "turn a rad off",
                     "turn the heating off", "turn them down"),
              # "how do i get paint off tiles" is the same job as stripping a door, and it ties with
              # the tile-painting row on score, so the removal row is the one that leans in
              bias=1,
              # A stripping job names the paint, and the paint is this row's own subject, so it is
              # not a word the reading may borrow from the turn before. Without this, "off" from one
              # turn and "door" from the next added up to a removal word and a surface, and a
              # smoke-alarm chat ("the fire alarm goes off when i have a shower" / "its right
              # outside the bathroom door") was handed the paint stripper.
              ask=(("paint", "gloss", "varnish", "woodwork", "wood", "skirting", "banister",
                    "emulsion", "undercoat", "primer", "lacquer",
                    # A person stripping a door often names the finish rather than the paint:
                    # "how do i remove the old finish off my door" was the stripper's line before
                    # the gate went on and a hedge after it. None of these words stands alone in the
                    # key, so a line that says "what finish should i use on oak" still never scores
                    # here; "strip" is deliberately not one of them, because a strip light flickers.
                    "finish", "finishes", "paintwork", "bare wood",
                    # "how do i strip a door" names the job and the surface and no paint at all, and
                    # the gate refused it: main answered it and this row was the answer. The job verbs
                    # belong with the subject words, so the line that says "strip" is a stripping job.
                    "strip", "strips", "stripping", "stripped", "sand", "sanding", "sandpaper"),)),
        entry("paint-on-hands", (("paint", "painting", "painted", "gloss", "emulsion", "varnish",
                                  "undercoat",
                                  # a wood stain on the hands is a paint on the hands, and the wood
                                  # care rows took it because "stain" is their word
                                  "wood stain", "woodstain", "wood dye", "wood stain on"),
                                 ("hands", "hand", "fingers", "skin", "nails", "fingernails",
                                  "arms", "arms and hands")),
              "Warm water and washing-up liquid takes water-based paint off skin while it is still "
              "tacky, and a soft nail brush lifts it out of the ridges. Oil gloss wants a little white "
              "spirit or baby oil on a cloth, then soap, then a moisturiser, because both dry the skin "
              "out. Keep white spirit off your face, a cut or a child, and let the last flecks wear off "
              "rather than scrubbing at them.",
              avoid=("wall", "walls", "car", "furniture", "nails painted", "paint my nails",
                     "paint your nails", "paint a", "painting a"),
              # "how do i get paint off my skin" ties with the row that stores a tin of paint,
              # and the tin won, so a person with paint on their arm was told how to keep a lid
              # tight. A part of a person in the line is this row's subject, not the tin's.
              bias=2),
        entry("red-wine-carpet", (("red wine", "wine"), ("carpet", "stain", "remove", "out", "spill")),
              "Blot it, don't rub, with kitchen paper, then pour on cold water and blot again, repeating "
              "until the water runs clear. A paste of bicarbonate of soda left on it for an hour pulls "
              "the rest out; white wine or salt are the old tricks and both work better than hot water.",
              # "can I open a bottle of red wine and leave it out" is a keeping question: a spill
              # answer needs something that the wine went on.
              ask=("carpet", "rug", "sofa", "couch", "cloth", "shirt", "dress", "tablecloth",
                   "spill", "spilt", "spilled", "stain", "stained"),
              # clothes have their own entry in the clothing domain, a sofa is the cleaning domain's
              # `wine-furniture`, and the cleaning domain's `red-wine-cloth` has the washable cloth, so
              # this one keeps carpets
              avoid=("shirt", "shirts", "dress", "dresses", "blouse", "top", "tops", "jeans", "trousers",
                     "skirt", "sweater", "jumper", "sofa", "couch", "settee", "armchair", "upholstery",
                     "chair", "cushion", "cushions", "rug", "curtain", "curtains", "tablecloth",
                     "napkin", "duvet", "pillow", "bedsheets", "linen")),
        # A carpet or a sofa stain with no substance named is the commonest version of the
        # question ("a stain on the carpet", "marks on the sofa"), and the substance entries -
        # red wine, coffee, nail polish - only answer when the line says what it was.
        # A rug that walks, slides or curls is its own small job, and every shape of it was a shrug or a
        # read-back: "how do i stop a rug from slipping", "my rug keeps sliding on the laminate", "the
        # corners of my rug wont lie flat".
        entry("rug-not-slipping",
              (("rug", "rugs", "mat", "mats", "runner", "runners", "doormat", "doormats",
                "carpet runner", "throw", "throws"),
               ("slip", "slips", "slipping", "slide", "slides", "sliding", "move", "moves", "moving",
                "shift", "shifting", "curl", "curls", "curling", "curled", "bunch", "bunching",
                "crease", "creases", "flat", "stay put", "stays put", "wont stay")),
              "Put a proper anti-slip underlay under it, the open-weave rubber sort, cut a couple of "
              "centimetres smaller than the rug, or run double-sided carpet tape along the edges: on a "
              "shiny floor the sticky corner pads do the job too. A rug that curls wants the curled end "
              "face down on the floor with something heavy on it overnight, or warmed with a hairdryer "
              "while you press it flat.",
              # cleaning a rug, a stain on it and buying one are each their own answer
              avoid=("clean", "cleaning", "wash", "washing", "shampoo", "stain", "stains", "stained",
                     "vacuum", "hoover", "smell", "smells", "smelly", "moth", "moths", "fade",
                     "faded", "colour", "color", "buy", "buying", "which", "best", "how much", "cost",
                     "price", "underlay", "new one", "shed", "sheds", "shedding", "underfloor",
                     "heating", "bath mat", "bathroom", "shower", "place mat", "placemat", "yoga",
                     "gym", "exercise", "mouse mat", "table mat", "towel", "iron", "ironing"),
              bias=1),
        entry("clean-furnishing",
              (("carpet", "carpets", "rug", "rugs", "mat", "mats", "sofa", "sofas", "couch", "settee",
                "armchair", "upholstery"),
               ("clean", "cleaning", "shampoo", "shampooing", "wash", "washing", "vacuum", "hoover",
                "dirty", "dirt", "freshen", "spring clean")),
              "Vacuum it first, then test any shampoo or foam cleaner on a hidden patch: a carpet wants a "
              "carpet shampoo worked in with a brush and rinsed, or a hired machine once or twice a year, "
              "and a sofa wants a foam cleaner and a soft brush with as little water as you can manage. "
              "Open the windows and dry it with the heating low, because anything left damp smells.",
              # a named stain, a named substance and buying or fitting one all have their own answers
              avoid=("red wine", "wine", "coffee", "tea", "cola", "juice", "nail polish", "nail varnish",
                     "blood", "paint", "oil", "petrol", "pet", "dog", "cat", "wee", "urine", "vomit",
                     "ink", "candle", "wax", "mark", "marks", "stain", "stains", "stained", "buy",
                     "buying", "which", "best", "underlay", "fitting", "fitted", "how much", "quote",
                     "leather", "suede", "new one", "cost", "price") + LETTING,
              bias=1),
        entry("carpet-stain",
              (("carpet", "carpets", "rug", "rugs", "mat", "mats"),
               ("stain", "stains", "stained", "mark", "marks", "spill", "spilled", "spillage",
                "remove", "get out", "get off", "mud", "blood")),
              "Blot, don't rub, with kitchen paper, then dab with cool water and a drop of washing-up "
              "liquid from the outside in, and blot dry with a towel; repeat until nothing more comes "
              "up. Work in small patches and never soak it, or the backing and underlay stay damp and "
              "start to smell. Grease wants neat washing-up liquid first, and a stain that survives all "
              "that is a job for a carpet cleaner.",
              # the substances have their own entries, and buying or fitting a carpet is not a stain
              avoid=("red wine", "wine", "coffee", "tea", "cola", "juice", "nail polish", "nail varnish",
                     "paint", "oil", "petrol", "pet", "dog", "cat", "wee", "urine", "vomit",
                     "ink", "candle", "wax", "turmeric", "buy", "buying", "which", "best", "underlay",
                     "fitting", "fitted", "how much", "quote", "vacuum", "hoover") + LETTING,
              bias=1),
        entry("sofa-stain",
              (("sofa", "sofas", "couch", "settee", "armchair", "upholstery", "footstool", "ottoman"),
               ("stain", "stains", "stained", "mark", "marks", "spill", "spilled", "spillage",
                "remove", "get out", "get off", "blood")),
              "Blot, don't rub, then dab with cool water and a drop of washing-up liquid from the "
              "outside in, and dry it with a towel rather than a hairdryer. Use as little water as you "
              "can, because a sofa takes days to dry and a damp one smells. A loose cover that unzips "
              "is better washed on its own; leather wants a barely damp cloth and saddle soap.",
              avoid=("coffee", "tea", "cola", "juice", "red wine", "wine", "nail polish", "nail varnish",
                     "buy", "buying", "which", "best", "new one", "replacement", "leather", "suede",
                     "how much", "cost", "price", "delivery", "second hand") + LETTING,
              bias=1),
        entry("grout-clean", (("grout", "tiles", "tile grout", "grouting"),
                              ("clean", "black", "mould", "dirty", "white", "whiten", "whitening",
                               "brighten", "yellow", "yellowed", "stained", "stain", "grimy", "grime",
                               # "seal" alone belongs to the bath and the shower more than to the
                               # joint, and with it here "how do i seal a bath round the tiles" was
                               # a grout scrub; the sealing this row means names the grout or tiles
                               "grout sealer", "sealer", "seal the grout", "sealing the grout",
                               "seal grout", "seal the tiles", "sealing the tiles", "seal tiles",
                               "seal my tiles", "sealing my tiles", "seal these tiles",
                               "scrub", "scrubbing", "brush", "steam", "steam cleaner",
                               # a room is only part of the thing, never a word of its own: on its
                               # own, "bathroom" made "how do i tile a bathroom" a grout-scrubbing
                               # answer, because "tile" alone satisfied the other half of the key
                               "bathroom grout", "shower grout", "grout in the bathroom",
                               "grout in the shower",
                               # grout that has failed is the same job as grout that is dirty, and
                               # it is the grout that is the subject here: "the grout is cracking in
                               # the corner of the shower" had no answer once the room came out of
                               # this key, because a cleaning word was all it had to offer
                               "cracking", "cracked", "cracks", "crumbling", "crumbly",
                               "missing", "falling out", "falls out", "come out", "coming out")),
              "Scrub the grout with a paste of bicarbonate of soda and water and an old toothbrush, then "
              "rinse. For black mould in the grout, use a mould spray and leave it 10 minutes. To whiten "
              "grey grout, a paste of bicarbonate and a little white vinegar left on for ten minutes "
              "lifts most of it, and an oxygen bleach (the laundry stain remover kind) left overnight "
              "takes the rest. Sealing the grout once it is dry keeps it that way for a year or two, "
              "and a grout pen is the quick fix if it is only the colour that bothers you.",
              # painting or tiling over the lot is a different job, and the tiling row owns those
              # lines. The whitening phrases are NOT here: standing this row down for "whiten tiles"
              # left the line to the tiling row, so somebody asking how to whiten a tile was told
              # how to lay one (broad-door, bronze-whistle and deft-lime all caught it). Whitening a
              # downstairs bathroom's tiles is usually the joint anyway, and this answer is the one
              # main gives.
              # and a cracked tile is the tile repair row's, not this one's: "how do i remove a
              # cracked tile" was a grout-scrubbing answer as soon as "cracked" joined this key
              avoid=("paint tiles", "paint the tiles", "cover the tiles", "tile the",
                     "cracked tile", "cracked tiles", "tile cracked", "tiles cracked",
                     "tile is cracked", "tiles are cracked", "cracked wall tile",
                     "replace a cracked tile", "remove a cracked tile")),

        # A tile that has let go of the wall, or of the floor, is a repair nobody had a card for:
        # "the tiles in my bathroom are coming loose" was a grout scrub before, and once the room
        # came out of the grout key it had no answer at all.
        entry("loose-tile",
              (("tile", "tiles", "wall tile", "wall tiles", "floor tile", "floor tiles"),
               # a tile that has let go of the wall or the floor. The words that mean the joint
               # itself are here too, because "the grout is cracking in a corner" ends in the same
               # repair, but nothing about laying, drilling, cleaning or choosing a tile is.
               ("loose", "loosening", "loosened", "coming loose", "came loose", "comes loose",
                "come off", "came off", "coming off", "falling off", "fell off", "fallen off",
                "lifting", "lifted", "hollow", "drummy", "wobbly", "popping", "popped",
                "move when i press", "moves when i press", "adrift",
                # a cracked tile comes off the same way, so it is the same job
                "cracked", "crack", "cracks", "split", "smashed", "broken tile")),
              "Tap it with the handle of a screwdriver: a hollow ring means the adhesive has let go, "
              "so the tile has to come off and go back properly rather than be patched. Score the "
              "grout round it, ease a thin scraper behind a corner and lift it out, then scrape the "
              "old adhesive off both the tile and the wall, spread flexible tile adhesive over the "
              "whole back with a notched trowel, press it home with a slight twist and tape it in "
              "place overnight before you regrout the joints.",
              # laying, drilling, cleaning, choosing and painting a tile are each another answer
              avoid=("lay", "laying", "tile a", "tiling a", "how do i tile", "start tiling",
                     "drill", "drilling", "screw", "hole", "hang", "hanging", "shelf", "mirror",
                     "clean", "cleaning", "cleaner", "grout pen", "mould", "mold", "black",
                     "whiten", "whitening", "paint", "painting", "cut", "cutting",
                     "chip", "chipped", "choose", "buy", "buying", "which", "best", "cost",
                     "price", "underfloor", "heat mat", "splashback")),
        entry("floor-scratch", (("floor", "wood", "laminate"), ("scratch", "scratched", "scuffs",
                                                                "marks")),
              "Rub a light scratch on a wooden floor with a walnut (really), or use a wax repair stick "
              "in a matching colour for deeper ones. On laminate, a scratch repair pen hides it, but "
              "only replacing the board fixes a deep gouge."),
        entry("hole-in-wall",
              (("hole", "holes", "dent", "dents", "crack", "cracks", "chunk", "gouge"),
               ("wall", "walls", "ceiling", "plaster", "plasterboard", "drywall", "skirting",
                "paper", "paint", "painted", "filler", "fill", "patch", "repair", "fix", "nail",
                "nails", "screw", "screws", "rawplug", "rawl plug")),
              "Push a bit of filler into the hole with a filling knife, leave it a little proud, and "
              "sand it flat once it is hard - two thin coats dry faster and sand better than one thick "
              "one. Anything bigger than a 50p piece, or a hole through plasterboard, wants a plasterboard "
              "patch stuck behind it and filled over before you paint. A crack wider than a couple of "
              "millimetres, or one that keeps coming back, is a builder's job rather than yours.",
              # a hole in a jumper is a darning job, and a crack in the wall is not a fabric repair
              avoid=("jeans", "jumper", "sock", "socks", "shirt", "cardigan", "knee", "tights", "garment",
                     "darn", "sew", "sewing", "stitch", "fabric", "trousers", "pocket", "coat",
                     # a cracked screen is a glass question, not a wall one
                     "phone", "screen", "mobile", "iphone", "laptop", "tablet", "tv", "telly",
                     "windscreen", "window", "glass", "car", "van",
                     "roof", "roofs", "tyre", "tyres", "tube", "inner tube", "bike", "bicycle"),
              bias=1),
        # --- the odd jobs -------------------------------------------------------
        # Small repairs and woodwork: the answers a person wants when something in the house
        # squeaks, wobbles, or will not come clean. Each one is keyed on the thing that is wrong and
        # passes on the neighbours it would otherwise steal (a floor scratch from a floor clean, a
        # wooden spoon from a wooden table).

        # `squeaky-door` in this file was the same job under a second id, and two test files wanted
        # different winners for the same line: one table now, with the sticking and rubbing cases in
        # the key, and the latch and matchstick advice in the reply.
        # The verbs come first and the fittings second, so "my gate creaks" counts two different key
        # words: with both in one part the two readings were the same word and the score was zero.
        # The fitting is the key's first half and the fault the second, so one table answers a door
        # that will not stay shut and a shelf that has snapped without either reaching the creak
        # answer or the meal table. The callable picks the part; the keys only say it is a fitting
        # with something wrong with it.
        entry("fitting-repair",
              (("oven", "cooker", "cupboard", "cupboards", "cabinet", "cabinets", "wardrobe", "unit",
                "units", "shelf", "shelves", "shelving", "drawer", "drawers", "window", "windows",
                "sash", "casement", "tap", "taps", "faucet", "mixer"),
               ("hanging off", "hangs off", "hanging", "hang", "came off", "come off", "came loose",
                "come loose", "loose", "loosely", "wobbly", "wobbles", "rocks", "snapped", "snap",
                "broken", "broke", "cracked", "fell off", "fallen off", "sagging", "sags", "dropped",
                "wont shut", "won't shut", "wont close", "won't close", "doesnt shut", "doesn't shut",
                "wont stay shut", "won't stay shut", "wont stay closed", "won't stay closed",
                "swings open", "pops open", "keeps opening", "crooked", "out of line", "wont slide",
                "won't slide", "doesnt slide", "jammed", "adjust", "fix")),
              _fitting_repair,
              # a door that creaks, sticks or needs oiling is the creak answer's, so its words come
              # out of this one; the meal table, the appliance answers and the body stay theirs too
              bias=2,
              avoid=("squeak", "squeaks", "squeaky", "squeaking", "creak", "creaks", "creaking",
                     "oil", "oiling", "rubbing", "rubs", "rattle", "rattles", "wind", "draught",
                     "draft", "sticking", "sticks",
                     "recipe", "recipes", "dinner", "lunch", "tea", "cook", "cooking", "meal", "meals",
                     "eat", "food", "fridge", "freezer", "microwave", "kettle", "dishwasher",
                     "washing machine", "tumble dryer", "dryer", "car", "van", "wheel", "wheels",
                     "pram", "pushchair", "trolley", "bike", "bicycle", "gate", "garage door",
                     "car door", "shower", "toilet", "bath", "boiler", "radiator", "my back",
                     "my knee", "my shoulder", "my neck", "my tooth", "my wrist", "my ankle",
                     "my hip",
                     # A window with glass out of it is not a fitting that came loose: "how do i
                     # fix a broken window", "is it expensive to fix a broken window" and "someone
                     # broke my window" all reached this card, which opens by saying the window is
                     # out of line rather than broken (early-badge, #4083). The break words stand
                     # this entry down in `avoid`, not only in the callable, because an entry a
                     # callable declines is still the entry the memory reads the line as being
                     # about.
                     "broken window", "window is broken", "window was broken", "broke my window",
                     "broke the window", "someone broke", "somebody broke", "smashed", "shattered",
                     "put through", "pane", "panes", "glass broke", "board up", "boarded up",
                     "expensive",
                     # "it rises then it drops in the oven" is a loaf collapsing, and `dropped` is in
                     # the key above: the bake's own rows in cooking.py answer every one of these, so
                     # anything said about the bake itself stands this card down.
                     "rise", "rises", "risen", "rising", "prove", "proves", "proved", "proving",
                     "proof", "proofed", "dough", "sourdough", "loaf", "loaves", "yeast", "sponge",
                     "batter", "souffle", "soufflé", "pastry", "croissant", "meringue", "bake",
                     "bakes", "baked", "baking") + FITTING_SHARED_STANDDOWN),
        # The noise a drawer makes is its runners rubbing, not a hinge, and there is no oil in
        # this job: grease and oil hold the dust that makes it worse. Before this entry a
        # squeaking or stiff drawer was the door answer, a rattling one was the chesty cough, and
        # "my chest of drawers is stuck" was "What have you tried so far?".
        entry("drawer-runners-rub",
              (("drawer", "drawers", "cutlery drawer", "kitchen drawer", "bedside drawer",
                "chest of drawers", "dresser drawer", "bedroom drawer"),
               ("squeak", "squeaks", "squeaky", "squeaking", "rattle", "rattles", "rattling",
                "stiff", "sticking", "sticky", "sticks", "jammed", "jamming", "jams", "grind",
                "grinds", "grinding", "dragging", "drags", "rough", "wobble", "wobbles",
                "wobbly", "loose", "hard to open", "hard to pull", "hard to push", "wont open",
                "won't open", "stuck")),
              "Rub a candle, a dry bar of soap or a little beeswax along the wooden runners or the "
              "plastic slides, and never oil or grease - those hold the dust that makes it worse. "
              "If it rattles or grinds, tighten the runner screws at the back, one turn past "
              "finger-tight. A drawer that sticks only at the end is usually the side swelling in "
              "damp weather, so sand the top edge of the drawer side lightly and it stops catching.",
              # the runners that have come away are the replace-them answer's, and a drawer with
              # something broken in it, a drawer of a fridge or a washing machine, and a chest as a
              # body part are all other jobs
              # the drawer noun is what keeps the chesty cough and the door out, so the avoid
              # list holds only the fittings and the machines: "my chest of drawers is stuck" is
              # a drawer, and a "chest" in the avoid list stood the whole entry down
              avoid=("off the runner", "off the runners", "off its runner", "come off",
                     "came off", "replace", "replacement", "new runner", "fridge", "freezer",
                     "washing machine", "dishwasher", "microwave", "oven", "lock", "locked",
                     "key", "child lock", "hinge", "hinges"),
              bias=1),
        # The window of a chat is not a window of a house: "what do you do when i shut the chat
        # window" and "when i close the browser tab" are questions about what becomes of the
        # conversation, and once the creaking-door key held "window"+"shut" they were told to oil
        # the hinges. Only the words that make the window the chat's own are here, so "why does
        # this window creak" is still the hinge answer.
        entry("door-creak",
              (("squeak", "squeaks", "squeaky", "squeaking", "creak", "creaks", "creaking",
                "sticking", "sticks", "stiff", "rubbing", "rubs", "drags", "dragging", "jammed",
                "jamming", "shut", "shuts", "closing", "hard to shut", "hard to close",
                # "how do i oil a door hinge" was the one shape of this job the key lost when the
                # two squeaky-door tables were merged: oiling is what the reply says to do, so it
                # belongs in the verbs, not only in the words of a line that is already working.
                "oil", "oils", "oiling", "oiled", "lubricate", "grease"),
               # a drawer was in this list, so "how do i stop a drawer from squeaking" was told
               # to oil the hinges and open and close the door. A drawer has runners, not hinges,
               # and the wax answer below is its own.
               ("door", "doors", "hinge", "hinges", "latch", "window", "windows",
                "cupboard door", "gate", "front door")),
              "Oil the hinges: a drop of 3-in-1 or a spray of silicone on each hinge pin, then open and "
              "close the door a few times so it works in. If it sticks or rubs rather than squeaks it "
              "has usually dropped on its top hinge, so tighten the hinge screws - loose ones let the "
              "door drop - and if they spin, push matchsticks dipped in wood glue into the holes and "
              "screw back in. Rub a candle or a dry bar of soap on the latch plate or the top edge if "
              "that is the part catching.",
              # a creaking floorboard, a creaking bed and a squeaking shoe are other answers
              # "stop" is in the key, so "how do i stop a door banging in the wind" scored here and
              # got hinge oil for a door that bangs. Banging is the latch answer's, not this one's.
              avoid=("chat window", "chat box", "chat pane", "browser", "browser window",
                     "browser tab", "this chat", "the chat", "the app window",
                     "floorboard", "floorboards", "floor", "bed", "beds", "shoe", "shoes", "brake",
                     "brakes", "kettle", "bang", "bangs", "banging", "slam", "slams", "slamming",
                     "rattle", "rattles", "rattling", "wind", "windy", "draught", "trainer",
                     "trainers", "boot", "boots", "sandal", "flip flop", "chair", "chairs", "stairs",
                     "bike", "bicycle", "car", "van", "wheel", "wheels", "trolley", "pram",
                     "pushchair", "voice", "squeaky clean", "toy", "toys", "clean", "cleaning",
                     # "grease" is in the key because greasing a hinge is this job, and it also took
                     # "how do i get grease off a kitchen door" - a cleaning question that was handed
                     # oil for the hinges. A removal phrase and a greasy surface are the cleaning
                     # ones; "how do i grease a door hinge" has neither.
                     "grimy", "sticky", "grease off", "grease from", "grease out",
                     "paint", "painted", "washing machine", "dryer", "fridge", "freezer", "oven",
                     "dishwasher",
                     # a door that will not open, or that has been forced, is a lock job or worse
                     "locked", "lock", "cannot open", "cant open", "can't open", "slammed",
                     "broke in", "burglar", "forced", "off its hinges", "fell off", "get out",
                     "trapped", "inside", "fire", "smoke", "cant get out", "can't get out",
                     # a door or gate that has dropped or come away is a loose hinge, which is
                     # `hinge-sag`'s job: oiling a joint that has pulled out of the wood only hides
                     # it, and "my gate is sagging and it wont shut" was getting this answer
                     "sagging", "sagged", "sags", "sag", "hanging off", "hanging by",
                     "come off its hinge", "came off its hinge", "off its hinge", "loose hinge",
                     "loose hinges", "wont shut", "won't shut",
                     # What comes *through* a door is not the door: junk mail, leaflets and a
                     # takeaway menu are a post question, and oiling the hinges answers none of it.
                     "mail", "junk", "junk mail", "leaflet", "leaflets", "flyer", "flyers",
                     "letter", "letters", "letterbox", "post", "postman", "delivery", "menu",
                     "cold callers", "salesman", "salesmen",
                     # A door that will not stay shut, a cupboard door hanging off and a window that
                     # will not close are a catch, a hinge screw and a sash out of line: oiling the
                     # hinges answers none of them, and `fitting-repair` has each of them.
                     "wont stay shut", "won't stay shut", "wont stay closed", "won't stay closed",
                     "swings open", "hanging off", "hangs off", "cupboard shelf", "shelf has snapped"),
              # a tie with the blister answer on "stop my door rubbing"; the fittings word settles it
              bias=1),
        entry("floorboard-creak",
              (("floorboard", "floorboards", "floor", "stairs", "stair", "step", "landing"),
               ("creak", "creaks", "creaking", "creaky", "squeak", "squeaks", "squeaking",
                "squeaky", "noisy")),
              "Find the noisy board and work talcum powder, french chalk or graphite powder into the "
              "gaps between the boards - it stops the wood rubbing on the nail. If it still creaks, "
              "screw the board down again from above instead of nailing it, and on stairs check the "
              "treads are tight.",
              avoid=("clean", "cleaning", "mop", "scratch", "scratches", "polish", "paint"),
              bias=1),
        entry("carpet-clean",
              (("carpet", "carpets", "rug", "rugs"),
               # main answers "how do i clean a carpet" from its furnishing entry, so this one is for
               # the smell and the stairs lines it leaves, not for the plain clean again
               ("smell", "smells", "smelly", "odour", "odors", "stink", "deep clean",
                "shampoo", "dirty", "stairs", "stair",
                # "what is the best way to clean a carpet" reached the stain card and was told to
                # blot a mark that does not exist. `best way` is the ask, and it is not in any other
                # carpet row's key, so the plain cleaning question comes here without taking "how do
                # i clean a carpet" or "how often should i clean my carpets" off the furnishing row.
                "best way", "steam")),
              "Vacuum it twice, slowly, then work at any mark from the outside in with a little carpet "
              "shampoo on a cloth and blot it dry - a carpet that stays damp is what starts a smell. "
              "For a whole room or a set of stairs, a hired shampoo machine is worth it once a year, and "
              "open the windows while it dries.",
              # a stain and a wooden floor are their own answers
              avoid=("red wine", "wine", "coffee", "vomit", "pet", "dog", "cat", "car", "car mat",
                     "floor", "floorboards",
                     # "my carpet smells musty" is the damp answer main already has
                     "musty", "damp"),
              bias=1),
        entry("wood-polish",
              (("table", "furniture", "sideboard", "cabinet", "chair", "desk", "dresser"),
               ("polish", "wax", "shine", "dull", "dullness", "restore", "oak", "wood", "wooden")),
              "Dust it, then work a hard wax polish or a beeswax-and-oil mix into the grain with a "
              "soft cloth, along the grain, and buff it off after ten minutes. Little and often beats "
              "a thick coat, which goes sticky and picks up dust.",
              # "get the wax OFF a table" is a removal question (cleaning's wax-table), not how to
              # polish it: this entry answered it with "work a hard wax polish into the grain"
              avoid=("floor", "floorboards", "scratch", "wobble", "wobbly", "dent", "dents",
                     "gouge", "gouges", "chip", "chipped", "stain", "stained",
                     "off", "remove", "removing", "spilled", "spilt", "spillage", "marks",
                     # painting a table is home.py's paint-furniture row, not a waxing job
                     "paint", "painting", "painted", "repaint"),
              bias=1),
        # A ring left by a wet glass, or the white bloom a hot plate leaves, is not polishing and not a
        # scratch: `wood-polish` avoids the word stain, so the commonest furniture repairs had no answer
        # of their own and the plain form of the question got "I'm not sure about that one".
        entry("wood-stain",
              (("table", "tables", "tabletop", "furniture", "sideboard", "cabinet", "desk", "dresser",
                "worktop", "wood", "wooden", "oak", "pine", "mahogany", "teak", "veneer"),
               ("stain", "stains", "stained", "water mark", "water marks", "watermark",
                "water ring", "water rings", "white ring", "white rings", "cup ring", "cup mark",
                "heat mark", "heat marks", "heat ring", "ring", "rings", "mark", "marks",
                "bloom", "milky")),
              # Every sentence names its own mark, because the composer can show one of them alone
              # when the earlier ones have been said in the same conversation.
              "A white water ring or a heat bloom lifts with mayonnaise or petroleum jelly left on "
              "overnight, or with a hairdryer held 15 cm away for a few minutes. A cloth laid over a "
              "white ring with a warm iron pressed on it for a few seconds at a time does the same job "
              "when the first try does not. A dark stain has gone into the wood and wants sanding back "
              "and re-oiling, and ink lifts with a little methylated spirit on a cloth, along the "
              "grain, before you polish the whole top so the shine matches.",
              # a scratch, a dent, a wobble and a polish are the neighbouring answers, and so are a
              # wooden floor, a car panel and a stained shirt
              avoid=("floor", "floors", "floorboard", "floorboards", "laminate", "scratch",
                     "scratches", "scratched", "scuff", "scuffs", "scuffed",
                     "dent", "dents", "gouge", "chip", "chipped", "wobble",
                     "wobbly", "loose", "car", "van", "phone", "screen", "shirt", "clothes", "clothing",
                     "carpet", "rug", "sofa", "upholstery", "wall", "paint", "gravy", "wine", "coffee",
                     "tea", "oil", "varnish", "remove the wax", "wax off",
                     # "how do i get wood stain off my hands" is paint-on-hands' line: the table
                     # card was answering it with a ring left by a glass
                     "hands", "hand", "fingers", "skin", "nails", "arms",
                     # the wood answers do not apply to a glass top: "white marks on the glass table"
                     # was told to rub mayonnaise into it, which is a trick for wood, not glass
                     "glass", "glasses", "glass table", "glass top", "glass tabletop", "marble",
                     "stone", "granite", "quartz", "slate"),
              bias=1),
        entry("wood-chip-fill",
              (("chip", "chips", "chipped", "gouge", "gouged", "chunk", "splinter", "splintered"),
               ("wood", "wooden", "woodwork", "table", "tables", "dresser", "sideboard", "desk", "oak",
                "pine", "walnut", "mahogany", "teak", "veneer", "furniture", "door", "worktop")),
              "A chipped edge or a gouge in wood is a filler job: press a two-part wood filler or a wax "
              "repair stick into it, a little proud of the surface, and sand or shave it flat once it is "
              "hard, then colour it with a touch of wax or stain. Keep the sanding to the filler - "
              "sanding the finish around it leaves a pale patch you cannot hide.",
              # the chips you eat, the chip in a tooth, and the chip in a screen are other questions
              avoid=("potato", "potatoes", "fries", "fry", "oven", "pan", "oil", "air fryer", "airfryer",
                     "fish", "supper", "takeaway", "tooth", "teeth", "filling", "dentist", "dental",
                     "phone", "screen", "glasses", "windscreen", "window", "paint", "nail", "nails",
                     "varnish", "paintwork", "car", "cars", "mug", "cup", "plate", "bowl",
                     # the wood chips you buy are burned, not filled: "what wood chips for a bbq" and
                     # "wooden chips for smoking" were a punting shrug and an acknowledgement on main
                     # before this card took them, so the fire words stand it aside
                     "bbq", "barbecue", "barbeque", "smoker", "smoking", "smoked", "smoke",
                     "wood chips", "woodchips", "chips for", "pellet", "pellets", "fire pit",
                     "chiminea", "pizza oven", "grill", "grilling", "burn", "burning"),
              # a repair in the wood is this card's even when a consumer row shares two of the words
              bias=2),
        entry("wood-dent",
              (("dent", "dents", "dinked", "gouge", "gouged"),
               ("wood", "wooden", "woodwork", "table", "dresser", "sideboard", "desk", "oak", "pine",
                "floorboard", "floor")),
              "A shallow dent in bare wood comes back up with water and heat: wet the spot, lay a damp "
              "cloth over it and press a hot iron on for a few seconds at a time, checking as you go. "
              "Once the wood has a finish on it a dent cannot be raised, so the repair is filler, sand "
              "and a matching wax or varnish.",
              # a dented car panel is bodywork, and a dented screen is glass
              avoid=("car", "cars", "van", "bumper", "wing", "bonnet", "door", "panel", "phone",
                     "screen", "fridge", "freezer", "washing machine", "drum")),
        entry("chair-wobble",
              # a desk is a table with drawers and it had no word here, so "my desk wobbles"
              # was an acknowledgement while the same line about a table got the repair
              (("chair", "chairs", "table", "tables", "desk", "desks", "stool", "bench",
                "furniture", "leg"),
               ("wobble", "wobbly", "wobbles", "loose", "rock", "rocks", "rocking", "rickety", "fix")),
              "Turn it over and find the loose joint: usually one leg has worked free of the seat. "
              "Squeeze wood glue into the joint, push it home and clamp it - a strap or a rope round "
              "all four legs works - and leave it overnight. Tighten any screws and add a bracket if "
              "the same joint keeps going.",
              ask=("wobble", "wobbly", "wobbles", "wobbling", "loose", "rock", "rocks",
                   "rocking", "rickety"),
              avoid=("chair for", "garden chair", "high chair", "wheelchair", "office chair"),
              # "loose stools for 3 days" is the same two words as a wobbly chair, and the reading
              # already knows which it is: when it reads the stomach, the chair stands aside. When
              # it reads nothing at all - "my stools are loose" - the words settle it instead, and
              # `_a_chair_and_not_a_body` holds the chair back for that one shape.
              guard=_a_chair_and_not_a_body),
        # A thing that will not sit still is its own job, and the fan had nobody to ask:
        # "my tower fan is wobbly" was an acknowledgement, "the fan wobbles when it runs" was
        # the laptop's cooling answer and "can you stop a fan from wobbling" was told that most
        # shaking is caffeine. A washer and a dryer that shake have their own cards (the transport
        # bolts and the load), so this one is the fan and the appliance with no card of its own.
        entry("a-fan-that-rocks",
              (("fan", "fans", "ceiling fan", "desk fan", "pedestal fan", "floor fan", "tower fan",
                "standing fan", "extractor fan", "heater", "fan heater", "fridge", "freezer",
                "appliance", "appliances"),
               ("wobble", "wobbles", "wobbling", "wobbly", "shakes", "shaking", "shaky", "rocks",
                "rocking", "walks", "walking", "jumps", "jumping", "vibrates", "vibrating",
                "moves about", "not level", "off balance", "uneven", "unsteady", "wonky",
                "tilts", "leaning")),
              _the_fan_stopped,
              ask=("wobble", "wobbles", "wobbling", "wobbly", "shakes", "shaking", "rocks",
                   "rocking", "walking", "jumps", "vibrates", "unsteady", "wonky", "tilts",
                   "stop it", "stop the", "why does", "fix"),
              # a person who is shaking is the shake answer's, a chair is the chair repair's, and
              # the machine with its own card (a washer, a dryer, a fridge that is not cold, a fan
              # that is noisy or grinding) keeps it
              avoid=("hands", "hand", "fingers", "arms", "voice", "feel shaky", "shaky hands",
                     # "desk" is not fenced: a desk fan is one, and the chair row wins a desk
                     # that wobbles on its own words anyway
                     "chair", "chairs", "table", "tables", "stool", "stools", "bench",
                     "sofa", "wardrobe", "door", "gate", "shelf", "shelves", "washing machine",
                     "washer", "dryer", "laptop", "computer", "pc", "phone", "car", "bike",
                     "steering", "baby", "dog", "cat", "puppy", "noise", "noisy", "rattle",
                     "rattles", "rattling", "grind", "grinding", "hum", "humming", "buzz",
                     # a fan that wobbles AND clicks is a noise question, and the noise card
                     # names the guard and the blade nut: "the fan wobbles and clicks" was
                     # answered by it before this row existed
                     "click", "clicks", "clicking", "squeak", "squeaks", "squeaking", "whine",
                     "whirr", "knock", "knocks", "knocking", "bang", "bangs", "banging",
                     "thump", "thumping", "scrape", "scraping",
                     "leak", "leaking", "smell", "smells", "not cold", "no power",
                     "how much", "cost", "electricity", "petrol"),
              bias=1),
        # A chair or a table does not only come loose; it snaps. "the table leg is broken" used to
        # reach the broken-bone answer on the word "leg", and a chair that was simply broken got an
        # echo, so a break in furniture gets the repair it needs and leaves the body table alone.
        entry("chair-broken",
              (("chair", "chairs", "table", "tables", "desk", "desks", "stool", "stools", "bench",
                "benches", "furniture", "bed", "beds", "sofa", "sofas", "couch", "couches",
                "settee", "settees", "shelf", "shelves", "cupboard", "cupboards", "drawer",
                "drawers", "wardrobe", "wardrobes"),
               ("broken", "broke", "snapped", "cracked", "split", "hurts", "hurting", "sore",
                "aching", "aches",
                # the consumer refund key carries the whole phrase "is broken", and a phrase counts
                # for more than the bare word: "my chair is broken" went to the refund ladder on it.
                # The same phrasing here is what makes the two rows weigh the same, and then the
                # bias below says a chair on its own is mended.
                "is broken", "is cracked", "is snapped", "is split", "has broken", "has snapped",
                "has cracked", "has split")),
              "Turn it over or open it up and see what has gone: a leg that has snapped wants the old "
              "glue drilled out, a wooden dowel or a longer screw and wood glue in the joint, clamped "
              "overnight. A cracked seat, back or shelf wants a bracket underneath and a screw through "
              "the split, and a split frame is usually cheaper to replace than to mend. Take the "
              "weight off it until the glue has set.",
              ask=("broken", "broke", "snapped", "cracked", "split", "hurts", "hurting", "sore",
                   "aching", "aches"),
              # a thing's own part is the thing's, and a person's part is not this entry. The
              # person's words are here because "my new chair hurts my back" is a question about
              # their back, not a broken chair.
              avoid=("chair for", "garden chair", "high chair", "wheelchair", "office chair",
                     "my leg", "my back", "my arm", "my wrist", "my ankle", "my knee", "my neck",
                     "my shoulder", "my hip", "hurts my",
                     "refund", "return", "returns", "money back", "shop", "store", "retailer",
                     "receipt", "guarantee", "warranty", "bought", "i paid", "reject",
                     "months old", "weeks old", "under a year", "still under",
                     # a chair that broke in its first week or month is a claim on whoever sold it
                     "after a week", "after a month", "after two weeks", "after 2 weeks",
                     "after a few days", "after 3 weeks", "last week", "last month",
                     # a furniture part that hurts or feels sore is loose at its joint, and
                     # `thing-part-hurts` says that: the bias above is strong enough to take the
                     # line otherwise, and "the chair back hurts" wants the tighten-it card
                     "hurt", "hurts", "hurting", "sore", "aching", "aches",
                     # "we booked a table for friday but the dishwasher broke" booked a restaurant
                     # table, not a piece of furniture, and the thing that broke is the machine
                     "booked a table", "book a table", "booking a table", "reserved a table",
                     "reserve a table", "table for two", "table for four", "table for 4",
                     "table for six", "table for 6", "restaurant", "reservation",
                     "dinner reservation"),
              # "soft stools and stomach ache" reaches this row on `stools` and `ache`
              guard=lambda understood: not the_stomach_is_what_it_is_about(understood),
              bias=4),
        # A part of a thing that hurts or feels stiff is not a part that has snapped. The body
        # tables stand down for a thing's own part, but `chair-broken` only names furniture, so
        # without this row a book's spine, a bottle's neck or a ladder's leg fell through to a
        # feeling or a question. The state the person said is the first thing to answer.
        entry("thing-part-hurts",
              (tuple(sorted(THING_PARTS)),
               ("hurt", "hurts", "hurting", "ache", "aches", "aching", "achy", "sore", "stiff",
                "pain", "pains", "painful", "twinge", "twinges", "throbbing")),
              "A part that hurts rather than has snapped is usually loose at its joint: tighten the "
              "screws or bolts, check the bracket and the glue line, and keep the weight off it until "
              "it feels firm. If it moves when you lean on it, treat it as a break - drill out the old "
              "glue, fit a wooden dowel or longer screw, and clamp it overnight.",
              # the state said is the reason for the answer, so it comes before the general
              # furniture repair when the line says "hurts" or "is sore"
              bias=3,
              # a stomach ache beside the word "stools" is the person's, not a thing's
              guard=lambda understood: (_a_thing_owns_the_part(understood)
                                        and not the_stomach_is_what_it_is_about(understood)),
              # a pipe, a wire or an appliance has its own answer, and the trade or the engineer is
              # the useful next step rather than a screwdriver
              avoid=("pipe", "pipes", "wire", "wires", "wiring", "boiler", "radiator", "radiators",
                     "drain", "drains", "tap", "taps", "socket", "sockets", "toilet", "sink",
                     "washing machine", "fridge", "freezer", "oven", "hob", "shower", "door",
                     "window", "lock", "locks")),
        # A toilet seat that moves is two bolts and a hinge, and main gave it either the falls card
        # ("wobbly" is a balance word) or "say more if it helps".
        # The silicone round a bath is the most-replaced seal in a house and nothing answered it:
        # "how do i seal a bath" was a shrug, and so was "how do i reseal round the bath".
        entry("bath-seal",
              (("bath", "baths", "bathtub", "bath tub", "shower tray", "shower base", "bath panel",
                "bathroom seal", "silicone", "silicon", "sealant", "mastic"),
               ("seal", "sealing", "sealed", "reseal", "re seal", "re-seal", "silicone", "sickaflex",
                "mould", "mold", "black", "gaps", "gap", "water getting behind", "leaking", "leak",
                "coming away", "peeling", "replace", "replacing", "strip", "stripping", "around",
                "along", "edge", "edges")),
              "Cut the old silicone out and scrub the joint back to dry, grease-free tile and bath "
              "before anything else, because fresh silicone will not stick to the old. Fill the bath "
              "with water first, so the bead is made at the weight it has to carry, then run anti-mould "
              "silicone along it and smooth it with a wet finger or a tool. Leave it 24 hours before "
              "you let the water out, and it will not part from the bath in a month.",
              # the bath that will not fill, will not drain or is not hot is another answer
              avoid=("fill", "filling", "filler", "drain", "draining", "slow", "blocked", "hot water",
                     "cold", "not hot", "boiler", "tap", "taps", "shower", "shower not working",
                     "paint", "painting", "bath bomb",
                     # the tiles are where the seal is, not the job: "how do i seal a bath round
                     # the tiles" was a grout scrub because this row stood down for the word
                     # "tile". What it stands down for is tiling the wall itself.
                     "tile the", "tiling the", "tiling a", "how do i tile", "grout the",
                     "regrout", "re-grout", "grouting the")),

        entry("toilet-seat-wobble",
              ("toilet seat", ("wobble", "wobbles", "wobbly", "loose", "loosening", "coming loose",
                               "moves", "moving", "slides", "sliding", "not tight", "fix", "tighten",
                               "broken", "cracked")),
              "Tighten the two bolts under the seat where the hinges meet the pan: they are usually "
              "plastic nuts you can turn by hand from underneath, and a quarter turn each side takes "
              "the movement out. If the seat still slides it is the hinge, and a replacement seat with "
              "a top-fix kit is about £10 to £20 and fits in ten minutes without getting under the "
              "pan. If the holes in the hinge have gone oval, a wipe of plastic wood in them holds the "
              "screws again.",
              bias=1),
        # A washing machine that walks across the floor is not level, and the transport bolts are the
        # thing nobody remembers.
        entry("washer-wobble",
              (("washing machine", "washer"),
               ("wobble", "wobbles", "wobbly", "shaking", "shakes", "vibrating", "vibration",
                "walking", "moves", "moving", "banging", "noisy", "noise", "spinning", "loud")),
              # "tumble dryer" and "dryer" used to be in this key, and a dryer does not have transport
              # bolts or a levelling drum: the noise table above owns a dryer that shakes, and it says
              # the thing that is actually wrong with one (coins, a bra wire, an even load).
              "Level it first: the machine must not rock on the floor, so turn the front feet out until "
              "it sits flat on all four and lock the nuts. If it is new, the four transport bolts at "
              "the back have to come out or the drum is still locked to the frame. After that, an even "
              "load stops most of it - mix towels with lighter things rather than washing one heavy "
              "item - and check the shipping bolts are the right length for a laminate floor.",
              # "the machine moves when it spins" is this row; taking the machine to a new flat is
              # the transport-bolt card, so the removal words stand this one down
              avoid=("tumble dryer", "tumble dryers", "dryer", "dryers", "washer dryer",
                     "washer-dryer", "condenser",
                     "move house", "moving house", "moving flat", "move flat", "new flat",
                     "new house", "new home", "upstairs", "downstairs", "van", "removals",
                     "take it with me", "moving it", "moving the machine", "moving my",
                     # "isnt spinning" is not a wobble: the drum is not turning at all, and
                     # levelling a machine that will not spin does not touch the cause. Levelling
                     # advice is for a machine that shakes, walks or bangs while it spins, which
                     # is what "wobbles", "shaking" and "walks" in the key say.
                     "isnt spinning", "isn t spinning", "not spinning", "no spin", "wont spin",
                     "won t spin", "wont turn", "won t turn", "drum isnt", "drum not")),
        entry("curtain-measure",
              (("curtain", "curtains", "blind", "blinds", "drapes"),
               ("measure", "measuring", "how wide", "how long", "buy", "size", "sized", "fit",
                "hanging", "hang")),
              "Measure the pole or track, not the window, and add 10 to 20cm either side so the "
              "curtains cover the edges when closed. For the length, measure from the pole to where "
              "you want them to finish, then double the width for a full gather: one and a half times "
              "the width looks skimped.",
              bias=1),

        entry("hang-picture", (("picture", "mirror", "shelf", "shelves", "shelf unit",
                                "floating shelf", "brackets",
                                # the same fixing question by its other subjects: a telly, a coat
                                # hook, a framed print
                                "tv", "television", "telly", "coat hook", "coat hooks", "frame",
                                "frames", "picture rail",
                                # a telly on a wall is the same fixing job; the phrases are here as
                                # well so that a telly that will not switch on is not one
                                "tv on the wall", "tv on a wall", "wall mounted tv", "wall-mount tv",
                                "mount a tv", "mount the tv", "tv bracket", "television on the wall",
                                "wall bracket",
                                # the fixing asked for by the thing that holds it: "i need a nail
                                # in the wall" and "what nail for plasterboard" were a chat
                                # module question ("What kind of nail do you usually go for?")
                                # and a fingernail-ridges card
                                "nail", "nails", "rawlplug", "rawlplugs", "rawl plug", "rawl plugs",
                                "rawplug", "rawplugs", "wall plug", "wall plugs", "anchor",
                                "anchors", "fixing", "fixings"),
                               ("hang", "hanging", "wall", "drill", "heavy",
                                "plaster wall", "plaster walls", "plasterboard wall", "brick wall",
                                "brick", "chimney breast", "lath and plaster", "no studs",
                                # "put up a shelf" and "what fixings do i need for a shelf" are the
                                # same job as hanging a picture: something goes on a wall and the
                                # fixing decides whether it stays there. "put up" without a shelf
                                # word is a tent or a curtain rail, and stays out.
                                "put up", "putting up", "fixings", "fixing", "fix", "mount",
                                "attach", "level", "stud", "studs", "plasterboard",
                                # "what bracket do i need", "which bracket should i buy": the
                                # buying words are the ask, and the noun above is the thing. A
                                # bracket that is a mark in a sentence is the writing row's own
                                # question, so every way of saying that is fenced out below.
                                "need", "needs", "needed", "buy", "buying", "should i get",
                                "what size", "which one",
                                # the fixing asked for by what it holds up: "what nails for a
                                # shelf" has the nail in the subject group and nothing else this
                                # row knows, so the for-tail is what says it is a fixing job
                                "for", "into", "in a wall")),
              "It is the fixing that matters, not the drill: find the studs with a stud finder or by "
              "tapping, and screw into one where you can. On plasterboard use proper hollow-wall "
              "fixings, not a bare rawl plug, for anything over a couple of kilos, and a shelf wants a "
              "bracket every 60cm or so. Two hooks 10cm apart keep a picture level far better than "
              "one. Check for pipes and wires before you drill, and check it with a spirit level "
              "before you tighten anything up.",
              # the mark in a sentence, the sum in a bracket and the band a wage falls in are all
              # the same word and none of them is a thing screwed to a wall.
              avoid=("writing", "sentence", "sentences", "sentenced", "essay", "essays", "grammar",
                     "punctuation", "comma", "commas", "paragraph", "paragraphs", "spell",
                     "spelling", "english", "algebra", "algebraic", "maths", "math", "equation",
                     "equations", "expand", "expanding", "simplify", "multiply", "x", "xy",
                     "tax", "taxed", "income", "salary", "wage", "wages", "band", "bands",
                     "percentage", "percent", "40k", "20k", "50k",
                     # the nail on a person, not the one in the wall: the filing, the polish, the
                     # biting and the clippers are the health and routines rows' lines
                     "file", "files", "clippers", "clipper", "polish", "varnish", "manicure",
                     "pedicure", "gel", "acrylic", "bitten", "biting", "cut my", "trim my",
                     "grow", "growing", "grew", "peeling", "ridges", "ridged", "fungus", "fungal",
                     "toenail", "toenails", "fingernail", "fingernails", "thumbnail", "toe", "toes",
                     "finger", "fingers", "nail fold", "ingrown")),
        # A bill question is about the cost, not about the boiler or the gas supply: a gas leak is
        # #safety's line, and "cut the gas to my boiler myself" is a plumbing job.
        entry("energy-bill", (("energy", "electric", "electricity", "gas", "heating", "utility",
                               "fuel",
                               # "my bill is massive" names no fuel at all: the bill itself is the
                               # subject, and the size words sit in the second group so a bare bill
                               # only counts when it is said to be big
                               "bill", "bills",
                               # the other half of a heating bill, asked by name: "how do i save
                               # on my hot water" was answered with the dry-eye card, because
                               # "heating" is in that reply and "hot water" was in no fuel list
                               "hot water", "hot-water",
                               # the dials the heating is turned down with, which people ask
                               # about by name: "how do i lower my boiler temperature",
                               # "how do i turn down my heating" were a plumber hedge and a shrug
                               "boiler", "thermostat", "radiator", "radiators", "flow temperature"),
                              ("bill", "bills", "cheaper", "reduce", "lower", "save", "cost",
                               "expensive", "price", "tariff", "spend less", "keep warm", "warm",
                               # the size of it, which people say instead of a question: "my bill is
                               # massive", "the gas bill was huge this month", "my bill is high".
                               # The words for a number that moved ("doubled", "gone up", "up again")
                               # stay out: that is the why-did-it-move question, and energy-use-up
                               # answers it with the meter and the estimated read.
                               "massive", "huge", "enormous", "sky high", "through the roof",
                               "so big", "big", "bigger", "high",
                               # the same question as a verb: "how do i stop wasting
                               # electricity" was the physics definition of electricity, and
                               # "i am wasting so much gas" was the bin's answer. What is being
                               # wasted is the fuel this row is about, so the verb belongs here.
                               "waste", "wasting", "wasted", "stop wasting",
                               # the same question in the words of the dial rather than the bill
                               "turn down", "turn it down", "turn up", "turn it up", "how low",
                               # "what temperature", "set" and "setting" used to be here, and they
                               # are the thermostat-setting question rather than the bill: with
                               # "thermostat" in the first group they won "what temperature should i
                               # set my thermostat to" and answered it with the flow temperature.
                               # The heating-temperature row says the numbers, so the setting words
                               # are its own now.
                               # the way-to-pay asks: "cheapest way to pay my gas and electricity",
                               # "is it cheaper to pay my bill by direct debit", a payment plan
                               "pay", "paying", "paid", "payment", "direct debit", "instalments",
                               "installments",
                               # the same ask in the words of a saving rather than a bill: "how
                               # do i save on my heating" was answered with the argument card,
                               # because "heating" is read as "heated" there and "save" only
                               # counted once. The turn-down phrases are not here: main's
                               # heating-temperature row owns the dial, and its comment says so.
                               # "save money" on its own was here and took one line back from
                               # the row that owns it: "whats the point of leaving the heating on
                               # all the time, does it save money" asks whether leaving it on
                               # saves anything, and `heating-all-day` says no and why. The bare
                               # phrase is true of that line too, so only the asks that name what
                               # the saving is on stay here.
                               "save on", "save money on", "cut my", "cut the",
                               "cheap to heat", "cheaper to heat", "get it cheaper",
                               "spend less", "spend less on")),
              "Heating and hot water are most of the bill, so start there: on gas, turn the boiler flow "
              "temperature down to 55 to 60C and heat only the rooms someone is in; all electric, put "
              "the immersion and any room heaters on a timer for the hours you actually use. Then "
              "standby and lighting, which is about a quarter, so switch off at the wall. Ask your "
              "supplier in writing for the standing charge and unit rate of their cheapest tariff; a "
              "fixed deal usually beats the standard variable one.",
              avoid=("smell", "leak", "leaking", "fumes", "carbon monoxide", "myself", "baby",
                     # one radiator's valve is its own row, not the boiler's dial
                     "turn down a radiator", "turn down the radiator", "one radiator",
                     "rad valve", "radiator valve", "trv", "thermostatic valve",
                     # and turning the house's own heating down is a setting, not a bill: "how do i
                     # turn down my heating" was the boiler-flow money answer
                     "turn my heating", "turn down my heating", "turn up my heating",
                     "turn our heating", "turn down our heating", "turn up our heating",
                     "toddler", "child", "clammy", "flue", "pilot light",
                     # "electric" is also the first word of things that are not a bill: a car, a
                     # blanket, a shower, a bike. Their running cost is a buying question.
                     "car", "vehicle", "blanket", "shower", "bike", "bicycle", "scooter",
                     "heater to buy", "which",
                     # a hob or an oven is a cooking question even when it names the fuel: "is an
                     # induction hob cheaper to run than gas" was answered with the boiler advice,
                     # which is about heating the house. The cooking-fuel entry below takes it.
                     "hob", "hobs", "induction", "oven", "ovens", "cooker", "cook", "cooking",
                     # a bill that is wrong or unpaid is a different question: money and the supplier,
                     # not how to use less heat
                     "can't pay", "cant pay", "afford", "debt", "arrears", "final notice",
                     "wrong", "mistake", "council tax", "tax", "water", "water bill", "phone",
                     # "why is my electric bill so high" asks what moved the number, and the
                     # energy-use-up row answers that with the meter and the estimated read: this
                     # row is the one that says what to do about it.
                     "why is my", "why has my", "why did my", "why are my", "why does my", "why so",
                     # asking to haggle or to ring them for a better price wants the call itself,
                     # not how to use less heat: that is the ring-about-a-price answer.
                     "haggle", "haggling", "haggled", "better price", "lower price",
                     # whether leaving it on saves anything is the habit row's question, and it
                     # answers yes or no where this row only says how to use less
                     "leaving it on", "leaving the heating on", "leaving the boiler on",
                     "left on all day", "on all the time", "on all day", "does it save",
                     "point of leaving",
                     # the other direction of the same fence: a bill at a table is not the fuel
                     # bill, and "the bill at the restaurant was too high" got the boiler flow
                     # temperature because "bill" and "high" are both in this row's key. The
                     # table's bill is `meal-bill-wrong`, which already names the fuels.
                     "restaurant", "restaurants", "waiter", "waitress", "split the bill",
                     "split bill", "the bill at the", "meal out", "card slip", "takeaway",
                     "cafe", "pub", "bistro", "pizzeria",
                     "mobile", "broadband", "tv licence", "licence", "rent", "insurance",
                     # Which deal to be on is a different question from what to turn down: the
                     # tariff and standing-charge answers live with the bills, and this one used to
                     # win them and talk about the boiler instead.
                     "switch", "switching", "tariff", "tariffs", "standing charge", "fixed deal",
                     "fixed tariff", "fixed rate", "worth",
                     # "is it cheaper to pay my energy bill by direct debit" is about how the
                     # money leaves the account, which money's paying-a-bill answers: the boiler
                     # flow temperature is not an answer to it.
                     "pay", "paying", "paid", "payment", "direct debit", "debit", "payment plan",
                     "how do i pay", "way to pay")),
        # "is it cheaper to leave the heating on all day" is one of the most-asked heating questions
        # there is, and it was answered with the general savings card - the flow temperature, the
        # standby, the standing charge - which never says yes or no. The habit words are the key and
        # the heating is the subject, so a setting, a timer, the hours someone is out and the hour
        # they come back are all the same question.
        # "is it safe to leave the boiler on all night" asks about the flame, not the bill, and it
        # reached the city-after-dark card because "safe" and "night" were the only two words in it
        # that anything knew. The tell is the safety ask in front of a boiler or the heating: what to
        # do about the money is the row below.
                entry("heating-all-day",
              (("heating", "central heating", "boiler", "radiators", "radiator", "hot water",
                "thermostat", "heating system"),
               ("all day", "all evening", "leave it on", "leave on", "leaving on", "left on",
                # "leave the heating on" is not "leave on": the thing being left comes between the
                # two words, so each way of saying it has to be a phrase of its own.
                "leave the heating on", "leaving the heating on", "left the heating on",
                "leave my heating on", "keep the heating on", "keeping the heating on",
                "heating on all day", "heating on all the time", "heating on low", "heating on at night",
                "on low", "all the time", "constant", "always on", "overnight", "timer",
                "programmer", "time clock", "when im out", "when i am out", "out at work",
                "out all day", "turn it off", "turn off", "switch it off", "switching it off",
                "come home", "coming home")),
              "No, it is not cheaper, for the heating or the hot water: keeping a house warm all day "
              "costs more than heating it when you are in it, and it shows on the bill. Every degree "
              "the rooms are held at is heat leaking out through the walls, so the timer wins - on an hour before you get up, off half an hour before bed, 18C in "
              "the living room and 16C in the bedrooms while you are up. Coming home to a cold house "
              "is a comfort problem rather than a cost one, and it is cheaper to warm the room you "
              "sit in for an hour than to keep the whole house up from midday. Hot water is the same "
              "story: heat the cylinder for an hour morning and evening with a jacket on it rather "
              "than leaving the immersion on. The exception is a well-insulated house on a heat "
              "pump, which is cheaper held at a steady low temperature than pushed up and down.",
              avoid=("broken", "not working", "isnt working", "isn't working", "fault", "faulty",
                     "no hot water", "cold water", "pressure", "bleed", "bleeding", "cold at the",
                     "radiator is cold", "radiators are cold", "noise", "noisy", "banging", "kettle",
                     "leak", "leaking", "smell", "carbon monoxide", "frost", "frozen", "condensation",
                     "mould", "damp",
                     # what to set it to is the room-temperature answer, and it is a different
                     # question from whether to leave it running
                     "what temperature", "how warm", "degrees", "what should i set", "set the",
                     "set my", "set it to", "how hot",
                     # the bill, the deal and the meter are the money questions
                     "bill", "bills", "tariff", "supplier", "standing charge", "price cap", "switch",
                     "switching", "smart meter", "can't pay", "cant pay", "afford", "debt",
                     "arrears", "council tax", "which boiler", "new boiler", "buy", "buying",
                     "worth getting", "service", "servicing",
                     # cold as an illness, and cold as the weather
                     "a cold", "my cold", "got a cold", "with a cold", "bad cold", "cold and flu",
                     "sore throat", "sneezing", "cough", "flu", "unwell", "sick", "chesty",
                     # a pet left in the house is its own question (how long a dog can be left,
                     # how warm a room a cat wants), and one sentence about the timer is not it
                     "cat", "cats", "dog", "dogs", "puppy", "kitten", "pet", "pets",
                     # a room for a baby is a safety answer, and "why is my heating always on" is
                     # a stuck programmer, not a habit: neither is this entry's question
                     "baby", "babies", "baby's", "newborn", "toddler", "cot", "nursery",
                     "why is my heating", "why does my heating", "why is the heating",
                     "why does the heating", "comes on by itself", "coming on by itself",
                     "on by itself", "keeps coming on", "wont go off", "won't go off",
                     # the boiler is the same fault in the same words: "why is my boiler always on"
                     # is a programmer that has stuck, and the answer is a plumber rather than an
                     # argument about the timer. The habit question asks whether it is cheaper and
                     # never asks why, so the why-shapes and the boiler's own symptoms stand this
                     # entry down.
                     "why is my boiler", "why does my boiler", "why is the boiler",
                     "why does the boiler", "why has my boiler", "why is my boiler on",
                     "boiler is always on", "boiler is on all", "boiler always on",
                     "boiler keeps", "boiler wont turn off", "boiler won't turn off",
                     "wont turn off", "won't turn off", "wont switch off", "won't switch off",
                     # the understanding layer reads "won't" as "will not" and "can't" as "cannot"
                     # before a key or an avoid word is matched, and a line read that way reaches no
                     # phrase written with the contraction: "my heating wont turn off" came back as
                     # the habit answer through that reading. Each of these is the same fault said
                     # the other way, so both spellings are named.
                     "will not turn off", "will not switch off", "does not turn off",
                     "doesnt turn off", "doesn't turn off", "can not turn", "cannot turn",
                     "cant turn it off", "can't turn it off", "cant turn off", "can't turn off",
                     "cant switch it off", "cant switch it off", "cant switch off",
                     "cant turn the heating off", "cant get it to go off",
                     "stuck on", "is stuck", "has stuck", "programmer is wrong",
                     "wrong time", "wrong times",
                     # A house nobody is in is the away question, and it wants the opposite answer:
                     # "should i leave my heating on when i go on holiday" and "...in an empty
                     # house" are both the same words as the staying-in habit line, and they were
                     # being told that the timer wins, which is advice to turn off the one thing
                     # that stops a hard frost bursting a pipe. The away row below answers them.
                     "go away", "going away", "gone away", "away for", "when im away",
                     "when i am away", "when were away", "while im away", "while i am away",
                     "while were away", "on holiday", "holiday", "empty house", "house is empty",
                     "nobody in", "no one in", "not at home for",
                     # "pipes dont freeze" is read as "pipes do not freeze" before a key is matched,
                     # so the phrase spelling never hits: the noun alone is the frost line, and the
                     # pipe row answers it.
                     "pipe", "pipes")),
        # The away question, said with the same words as the habit question: "should i leave my
        # heating on when i go on holiday" reads as "leave my heating on", which is the all-day row's
        # key, so the person planning a week away was told the timer wins - true of a house someone is
        # in, and the wrong advice for a house that will sit empty through a frost. The reply is the
        # away answer: low rather than off, and the water off as well.
        entry("heating-while-away",
              (("heating", "central heating", "boiler", "radiators", "radiator", "hot water",
                "thermostat", "heating system", "immersion", "pipes"),
               ("go away", "going away", "gone away", "away for", "when im away",
                "when i am away", "when were away", "while im away", "while i am away",
                "while were away", "on holiday", "holiday", "empty house", "house is empty",
                "nobody in", "no one in", "not at home for", "leave it on when",
                "leave the heating on when", "leave my heating on when", "turn it off when",
                # a frost line names the pipe, and the answer below is the one that says why it
                # must not go off
                "pipe", "pipes")),
              "Leave it on low rather than off if it will be cold: 12 to 15C, or the thermostat's "
              "frost setting, costs a few pounds a week and is far cheaper than a burst pipe, which "
              "is what a hard frost does to a cold house. Turn the water off at the stopcock before "
              "you go as well, and hot water can be switched off entirely. For a summer trip, or a "
              "house that will not drop below about 5C, off is fine.",
              avoid=("broken", "not working", "fault", "faulty", "leak", "leaking", "noise",
                     "noisy", "banging", "kettle", "carbon monoxide", "smell", "bleed",
                     "bleeding", "pressure", "condensation", "mould", "damp", "bill", "bills",
                     "tariff", "switch", "supplier", "standing charge", "price cap", "afford",
                     "debt", "arrears", "what temperature", "how warm", "degrees",
                     "what should i set", "how hot", "baby", "babies", "newborn", "toddler",
                     "cat", "cats", "dog", "dogs", "puppy", "kitten", "pet", "pets",
                     "why is my boiler", "why does my boiler", "stuck on", "wont turn off",
                     "will not turn off", "comes on by itself", "on by itself")),
        # "what time is electricity cheapest" was the science definition of electricity, and
        # "is it cheaper to run the washing machine at night" was the cost of one cycle: neither
        # answered the question, which is about the hour of the day and the tariff.
        entry("cheapest-hours", (("electricity", "energy", "power", "electric", "washing machine",
                                  "washer", "washers", "dishwasher", "tumble dryer", "dryer",
                                  "drier", "oven", "cooker", "appliance", "appliances",
                                  "immersion", "hot water", "economy 7", "economy7", "off peak",
                                  "off-peak", "time of use",
                                  # Most people do not say "washing machine" when they mean the
                                  # hour: "whats the cheapest time to do laundry" was a search punt
                                  # and "should i put the washing on overnight" was the overnight
                                  # SOAK (warm water and biological detergent, then wash it in the
                                  # morning), which is a different job with the same words. The
                                  # load and the laundry are what this row is about, so their
                                  # names are here.
                                  "laundry", "washing", "the washing", "put the washing",
                                  "a wash", "the wash", "wash a load", "a load of washing",
                                  "load of laundry", "clothes wash",
                                  # "can i do laundry overnight" was the overnight SOAK by a
                                  # point: the phrase is what puts the hour question in front.
                                  "do laundry", "laundry overnight", "washing overnight"),
                                 ("cheapest", "cheaper", "cheap", "cheaply", "night", "overnight",
                                  "at night", "off peak", "off-peak", "economy 7", "economy7",
                                  "time of use", "best time", "what time", "delay", "timer", "timed",
                                  "low rate",
                                  # the same question the other way round: "can i run a dishwasher
                                  # in the morning" is about the hour as much as the night one, and
                                  # the hour is what this row answers
                                  "morning", "in the morning", "evening", "in the evening",
                                  "afternoon", "in the afternoon", "during the day")),
              "Night is cheaper only on a two-rate tariff such as Economy 7 or an EV one; on a "
              "single rate the hour makes no difference at all, so check the tariff name on your "
              "bill. Where there is a cheap window, usually about half past midnight to half seven "
              "and charged at roughly a third to a half of the day rate, put the washing machine and "
              "the dishwasher on a delay. Whatever the tariff, never leave the tumble dryer running "
              "overnight, because of the fire risk.",
              # This row answers when an appliance is cheap to run, not where to get one: "where
              # can i get a cheap dishwasher" said "get" rather than "buy", so the avoid list
              # below did not catch it and the night tariff answered a question about a shop.
              guard=lambda understood: not asks_where(understood),
              # A tired body also says "energy" and a time of day: "im always low on energy in
              # the afternoons" was told which hours a two-rate tariff is cheap in, because
              # "energy" is in the first arm and "afternoon" in the second. The body words are
              # what say the question is the person's own energy and not the meter's.
              avoid=("tired", "tiredness", "tiring", "exhausted", "drained", "knackered",
                     "sluggish", "flagging", "sleepy", "no energy", "low on energy",
                     "low in energy", "energy levels", "my energy", "afternoon slump",
                     "cant keep my eyes open", "keep falling asleep", "always tired", "so tired",
                     "feel flat", "feeling flat", "run down", "worn out", "burned out",
                     "burnt out",
                     "car", "vehicle", "blanket", "shower", "bike", "bicycle", "buy", "buying",
                     # not the bare "best": "when is the best time to run the dishwasher" is this
                     # row's own question, and the word only says which-machine when it is one with
                     # the noun. The comparison shapes are named instead.
                     "best washing machine", "best dishwasher", "best dryer", "best tumble dryer",
                     "best oven", "best appliance", "best brand", "best buy", "best value",
                     "which washing machine", "which dishwasher", "which dryer", "which appliance",
                     "which", "boiler", "radiator",
                     # "is it cheaper to pay my energy bill by direct debit" is a way-to-pay line,
                     # and the night-hours answer is about when to run an appliance: the payment
                     # words hand it back to energy-bill, which is what answered it before the
                     # cheapest-hours entry existed.
                     # "tariff" is not in this list: "cheap tariff for electric heating" is the
                     # night-hours line itself, and holding it out sent that question to the price cap.
                     "pay", "paying", "paid", "payment", "direct debit", "debit", "standing charge",
                     "how do i pay", "way to pay", "supplier", "bill", "bills",
                     # which fuel is cheaper is a question about the hob, not about the hour: "is it
                     # cheaper to cook with gas or electric" was told about Economy 7. The cooking-fuel
                     # entry below answers it.
                     "hob", "hobs", "induction", "cook with", "cooking with", "gas or electric",
                     "electric or gas", "gas hob", "gas oven", "electric oven",
                     # which fuel is cheaper for the whole house is the heating-fuel row's: the
                     # hour of the day is not what "is gas cheaper than electricity" is asking.
                     "gas or electricity", "electricity or gas", "cheaper than electricity",
                     "cheaper than gas", "cheaper to heat", "cheapest way to heat",
                     "which is cheaper", "compare gas", "gas vs", "gas versus",
                     # "what time should i put a chicken in the oven" is a cooking time, not an hour
                     # of the day to run an appliance: it wants the roasting answer, and the oven in
                     # the key plus "what time" in the second arm held it here. A line that puts food
                     # in the oven is the cooking question, and the food is what says so.
                     "put a chicken", "put the chicken", "chicken in", "turkey", "chicken",
                     "roast", "roasting", "joint of", "casserole", "cake", "baking", "bake",
                     "scones", "biscuits", "pizza", "lasagne", "how long", "how many minutes",
                     "gas mark", "preheat", "at 180", "at 190", "at 200", "at 220",
                     # A complaint about a wash that is sitting in the machine is the wash's
                     # question, not the tariff's: "my washing smells after a night in the
                     # machine" was answered with Economy 7 once the laundry words were in this
                     # row's key, because "a night" is the second signal and "washing" the first.
                     # The dirt, the smell and the colour are what say the hour is not being
                     # asked about.
                     "smell", "smells", "smelling", "smelly", "musty", "stink", "stinks",
                     "stinky", "mouldy", "mildew", "damp wash", "service wash", "fluff", "lint",
                     "stain", "stains", "stained", "shrunk", "shrink", "shrinking", "gone grey",
                     "gone greyish", "went grey", "yellowed", "bobbled", "pilling", "oil stain",
                     "grease stain", "sweat", "blood", "sick", "nappy", "nappies"),
              bias=1),
        # The room question, not the bill one: "cheapest way to heat a room" and "my house is cold"
        # are about what to do tonight. A cold house that is also a sad one stays with the person.
        # "why is my flat so cold even with the heating on" is not the keep-warm answer: the
        # person already has the heating on and wants to know why it is not working. The keep-warm
        # row answered it with a 1kW electric radiator for one room, which is the answer to a
        # different question, and once the mood row and the body-cold row stood aside for a home
        # it was the only card left. Four causes cover nearly every one of these, cheapest
        # first, so the row names them in the order a person can check them.
        entry("cold-house-even-with-the-heating-on",
              (("cold", "colder", "freezing", "chilly", "perishing", "never gets warm",
                "never warms up", "wont get warm", "won't get warm", "not getting warm",
                "not warming up", "wont warm up", "won't warm up", "doesnt get warm",
                "doesn't get warm", "lukewarm"),
               ("house", "home", "flat", "room", "rooms", "bedroom", "living room", "sitting room",
                "kitchen", "heating on", "heating is on", "heatings on", "radiators are on",
                "radiator is on", "the heating", "central heating", "upstairs", "downstairs",
                # an outbuilding is the same four causes, and a cold shed, cellar or basement was
                # answered with the season instead: "why is my shed so cold" got the Earth's tilt.
                "shed", "sheds", "cellar", "cellars", "basement", "basements", "workshop",
                "workshops", "garage", "garages", "conservatory", "loft", "attic", "outbuilding",
                "outbuildings", "hallway", "porch", "caravan", "bungalow", "cottage")),
              ("Usually one of four things, and the cheap checks come first. Feel the radiator in "
               "the cold room: cold at the top is air, so bleed it; hot at the top and cold at the "
               "bottom is sludge; and a thermostatic valve turned right down or stuck shut does the "
               "same. Then look at where the thermostat sits - in a cold hall, or near a radiator "
               "or a window, it reads the wrong room and stops the heating before the bedrooms get "
               "warm. Then the boiler's flow temperature: 55 to 60C suits a condensing boiler, and "
               "set much lower than that the radiators never get hot enough on a cold day. If all "
               "that is right the heat is leaving - draughts under the doors, an open chimney, the "
               "loft hatch, and loft insulation under 270mm - and that is what to spend on next."),
              bias=1,
              # said with the fault already named, these are the fault rows, not the why row
              ask=("even with", "with the heating", "heating is on", "heating on", "heatings on",
                   "heating is running", "heating is going", "radiators are on", "radiator is on",
                   "turned up", "turn it up", "on full", "full blast", "all day", "all the time",
                   "never gets warm", "never warms up", "not getting warm", "why is", "why are",
                   "why does", "why do", "why wont", "why won't", "why am i"),
              # Whether to put the heating on, and what to set it to, is the heating advice
              # row's: "my house is cold should i put the heating on" was answered with the four
              # causes, while "18C is the usual living-room setting" is the answer it can act on.
              avoid=("should i put the heating on", "should i turn the heating on",
                     "shall i put the heating on", "shall i turn the heating on",
                     "do i need to put the heating on", "do i need the heating on",
                     "is it worth putting the heating on", "worth putting the heating on",
                     "what temperature", "what should i set", "how warm should",
                     "no heating", "heating is off", "heating off", "heating not working",
                     "heating isnt working", "heating isn't working", "heating has stopped",
                     "heating stopped", "heating wont come on", "heating won't come on",
                     "heating broken", "heating is broken", "broken boiler", "boiler is broken",
                     "pressure", "gauge", "fault code", "locks out", "wont fire", "won't fire",
                     "cold at the top", "cold at the bottom", "at the top", "at the bottom",
                     "bleed", "bleeding", "radiator key", "thermostatic valve",
                     "insulation", "loft insulation", "cavity wall", "double glazing",
                     "draught", "draughts", "draft", "drafts",
                     # a person, a plate, a pet or a car is not a house
                     "i am", "im ", "i feel", "always cold", "my feet", "my foot", "my hands",
                     "my hand", "fingers", "toes", "baby", "babies", "newborn", "toddler",
                     "disabled", "elderly", "pensioner", "old", "sick", "ill",
                     "car", "cars", "van", "engine", "washing machine", "oven", "microwave",
                     "food", "reheat", "leftovers", "tea", "coffee", "bath", "shower",
                     "pool", "greenhouse", "shed", "caravan", "hot tub",
                     # money and bills are their own rows
                     "bill", "bills", "cost", "cheap", "cheaper", "cheapest", "afford",
                     "price", "quote", "tariff", "energy")),
        entry("heat-a-room", (("heat", "heating", "warm", "warmer", "warmth", "cold", "freezing",
                               "chilly", "perishing",
                               # Cold said as a picture, which is how most people say it that
                               # way: "this office is like a fridge", "its like a freezer in
                               # here", "my flat is an ice box". The same claim as "the office is
                               # cold", and every one of them was falling to the floor because a
                               # cold room is never named in the line.
                               "like a fridge", "like a freezer", "like an ice box", "ice box",
                               "icebox", "like the arctic", "colder than a fridge",
                               "like a cold store",
                               # the heating switched off is said as the thing to do without, and
                               # the boiler rows were taking "keep warm with no heating" to a
                               # thermostat fault. Naming the shape here keeps the night-in answer.
                               "no heating", "heating off", "without heating",
                               "keep warm", "keeping warm", "stay warm", "staying warm"),
                              ("room", "rooms", "one room", "house", "home", "flat", "bedroom",
                               "living room", "sitting room", "tonight",
                               # Every other room a person heats: without these "how do i heat the
                               # kitchen" was the cleaning routine (it keys on "how"), and the
                               # bathroom, the garage and the conservatory had their own rows.
                               "kitchen", "bathroom", "garage", "conservatory", "shed",
                               "hall", "hallway", "spare room", "loft", "attic", "office",
                               # the rooms nobody sits in still get asked about: "why is my
                               # cellar so cold" and "the workshop is freezing" had no answer
                               # of their own and reached the body card's thyroid test
                               "cellar", "basement", "outbuilding", "outbuildings", "workshop",
                               "porch", "caravan",
                               # The room they are in, said without naming it: "its freezing in
                               # here" is the same question about the same room, and it got
                               # "Got it. Is there anything you'd like a hand with?"
                               "in here", "in this room", "this room"),
                              # "keep warm without the heating on" asks for this answer and names
                              # the heating only to leave it out, so the entry has to say the frame
                              # itself: the matcher takes a "without" clause off the line for every
                              # entry that does not (bot/knowledge/lookup.py, _frame_masked).
                              ("without heating", "without the heating", "without central heating",
                               "heating off", "no heating", "without putting the heating on",
                               "keep warm", "keeping warm", "stay warm", "staying warm",
                               # The same question said with the room as the verb's object rather
                               # than as a condition: "how do i heat my flat cheaply" was answered
                               # with the row-with-a-partner card (its "heated" reads as "heat")
                               # and "how do i warm up the flat" with the five-minute exercise
                               # warm-up. Both name the home and ask how to warm it, which is
                               # this row's own question.
                               # not bare "warm up": it is also what you do to soup, leftovers and
                               # a cold body before a run, and on its own it is enough to reach this
                               # row ("how do i warm up leftovers" became the room card). The room
                               # is named in the phrases below, which is what makes it this question.
                               "warm the", "warm my", "warm our", "warm this", "warm a",
                               "warm this room", "warm that room", "warm up the room",
                               "warm up the house", "warm up the flat", "warm up my",
                               "warm up our",
                               # the house as the object of the verb, which is the plainest way
                               # to ask: "how do i heat the house", "how do i heat my house".
                               # The things that heat their own water (a car, a washing machine,
                               # a shower) are held out below by name.
                               "heat the", "heat my", "heat our", "heat a", "heat this",
                               "heating the", "heating my", "heating our", "heating a",
                               "cheaply", "cheaper", "cheapest", "afford")),
              "Heat the room you are sitting in and shut the door: a 1kW electric radiator warms a "
              "small room for about 25p an hour, usually less than running the whole boiler for one "
              "person, and a heated throw costs about 3p an hour. Then stop the losses, a few pounds "
              "each: a brush strip on the door, a chimney balloon, foil behind the radiator. If the "
              "central heating is on, keep the flow at 55 to 60C and heat only the rooms you use.",
              # "cold" is also an illness, and "stuck at home with a cold" is a line about a person,
              # not about a house. The noun phrase is what tells them apart.
              # "on my own" and "by myself" used to be here, and they took the most ordinary way of
              # saying the problem: "i live by myself and the flat is cold" was a nod. They are not
              # needed - a line about being lonely is answered by the loneliness row on its own
              # words, and a line about a cold flat with them in it is this row's question.
              avoid=("lonely", "loneliness", "empty", "miss him", "miss her",
                     "since he", "since she", "passed away", "died", "funeral", "boiler", "radiator",
                     "bill", "bills", "mould", "damp", "carbon monoxide",
                     # the illness, spelled with a verb or a possessive: the bare phrase "a cold"
                     # also read "how do i heat a cold room", a house question, as a person's flu
                     "have a cold", "has a cold", "had a cold", "having a cold", "ive got a cold",
                     "i ve got a cold", "got a cold", "my cold", "his cold", "her cold",
                     "with a cold", "bad cold", "down with a cold", "a cold coming", "cold coming on",
                     "cold and flu",
                     "sore throat", "sneezing", "cough", "flu", "temperature", "unwell", "sick",
                     # a house the person is trying to keep COOL is the other half of the year and
                     # the other question: "how do i keep the house cool in the heat" was told to
                     # buy an electric radiator, because it has "heat" and "house" in it.
                     "cool", "cooler", "cooling", "keep cool", "keep it cool", "stay cool",
                     "heatwave", "heat wave", "hot weather", "hot day", "hot nights",
                     # keeping the heat out of a room is the cooling row's question, and the
                     # words "heat" and "flat" are enough for this one to claim it
                     "keep the heat out", "heat out", "stop the sun", "sun heating", "block the sun",
                     "the sun coming in", "sun comes in", "sun through",
                     # Keeping warm OUT OF DOORS is a clothes question, not a heating one: "how do i
                     # keep warm cycling in winter" and "... at a football match" were both told to
                     # buy an electric radiator. The activity is what tells them apart, and the
                     # clothing notes (keep-warm-moving / keep-warm-standing) answer them.
                     "cycling", "cycle", "bike", "bicycle", "motorbike", "motorcycle",
                     "scooter", "ride", "riding", "commute", "commuting", "run", "running",
                     "jog", "jogging", "walk", "walking", "hike", "hiking", "football",
                     "rugby", "match", "watching", "touchline", "sidelines", "fishing",
                     "golf", "ski", "skiing", "camping", "festival", "outdoors", "outside",
                     "dog walk", "school run",
                     # A thing that heats its own water is not a room: "my washing machine isnt
                     # heating the water" and "no heat in my car" both came here once the home
                     # shapes were in the key, and each has its own answer.
                     "car", "cars", "van", "vehicle", "motorhome", "caravan", "washing machine",
                     "washer", "dishwasher", "tumble dryer", "dryer", "drier", "cooker",
                     "shower", "bath", "hot tub", "pool", "swimming", "greenhouse", "hot water",
                     "immersion", "water", "kettle",
                     # A person or a plate warms up too, and both have their own answer: "how do i
                     # warm up leftovers" and "how do i warm up soup" reached this row on the bare
                     # verb, and "does warming up prevent injury" wants the exercise note.
                     "leftover", "leftovers", "soup", "reheat", "reheating", "microwave",
                     "warm up before", "warming up before", "warm up prevent", "warming up prevent",
                     "before a run", "before exercise", "prevent injury", "prevent injuries",
                     # the bedroom has its own answer, and it is the more specific one: a bedroom at
                     # 16 to 18C for sleep, said there, not the sit-in-one-room answer.
                     "bedroom", "bedrooms", "bed room", "for sleep", "sleeping", "sleep in",
                     # the appliance being asked about, and not the picture of a cold room
                     ) + THE_APPLIANCE_ITSELF,
              # Two stand-downs hold here and both are wanted. A body part being warmed is the
              # compress card's question, not a room's ("heat my back or ice it" was told to buy a
              # 1kW electric radiator for the room it was sitting in). And a row or a discussion
              # that got heated is an argument, not a cold room ("things got heated in the
              # kitchen" was told to buy the same radiator).
              guard=lambda u: _a_room_being_heated(u)
              and not_the_heat_of_an_argument(u)),
        # A squeak or a rub is the hinge, the latch or a door that has dropped: the two fixes are the
        # ---------------------------------------------------------------- doors, locks, hinges
        # People describe these six by the symptom and the part, never by the fix: "the door
        # squeaks", "my key is stiff", "the handle is loose". The part and the symptom are what
        # tell them apart, so each entry keys on both and steps aside for the household ones
        # (a fridge door that will not shut, a washing-machine door that is locked, a car door).
        # "the tap in the bathroom is loose" and "my kitchen cupboard door is hanging off" were both
        # said back to the person as a note. Each is a two-minute job with a screwdriver, so the tell
        # in each line is the part that has come adrift, not the word for the room.
        entry("tap-loose",
              (("tap", "faucet", "mixer tap", "monobloc"),
               ("loose", "wobble", "wobbles", "wobbly", "moves", "moving", "swivels", "spins",
                "spinning", "swinging", "not fixed", "come away", "came away", "lifted")),
              "A tap that wobbles is held by one nut underneath: get under the sink and tighten the "
              "back nut on the threaded shank with a basin wrench or a long spanner, or the fixing "
              "plate on a monobloc. Once it is tight, check the two flexible tails have not started "
              "to weep. If the nut has pulled the thread through a thin worktop, a repair plate costs "
              "a few pounds and spreads the load.",
              avoid=("drip", "dripping", "leak", "leaking", "pressure", "hot water", "cold",
                     "scale", "limescale")),
        entry("cupboard-door-hinge",
              (("cupboard door", "cupboard doors", "cabinet door", "kitchen door", "kitchen doors",
                "hinge", "hinges", "door hanging", "door dropped"),
               ("hanging off", "hang off", "hangs off", "hanging", "loose", "dropped", "sagging",
                "sag", "came off", "come off", "falling off", "screws", "screw", "pulled out",
                "stripped", "wont close", "won't close", "rubbing")),
              "Tighten the screws holding the hinge plate first, and if they spin, take them out and "
              "pack the holes with two broken matchsticks and wood glue before driving them back in. "
              "For a door that has dropped, the two screws nearest the door edge lift it: slacken the "
              "outer ones and turn the inner ones to raise the front. Move the plate 20mm up or down "
              "only if the wood has gone."),
        entry("heating-on-by-itself",
              (("heating", "boiler", "radiators", "radiator", "central heating"),
               ("by itself", "on its own", "comes on", "come on", "came on", "turns on", "turned on",
                "random times", "middle of the night", "at night", "when i havent", "even when its off",
                "when its off",
                # The same fault the other way round: a boiler or a heating system that will not
                # stop is the same valve or programmer as one that starts on its own, and the
                # checks are the same checks. "why is my boiler always on" and "my heating wont
                # turn off" were a plumber suggestion, and "my boiler is running all the time"
                # was answered with the price of gas.
                "always on", "always hot", "always running", "on all the time",
                "running all the time", "wont turn off", "won't turn off", "wont go off",
                "won't go off", "wont switch off", "won't switch off", "wont shut off",
                "never turns off", "never goes off", "not turning off", "keeps running",
                "keeps firing", "keeps going", "stays on", "staying on", "on in the summer",
                "hot in the summer", "stuck on", "jammed on", "still on", "left on",
                "on all day", "on all night",
                "will not turn off", "will not go off", "will not switch off",
                "will not shut off", "will not stop", "doesnt turn off", "doesn't turn off",
                "doesnt go off", "doesn't go off", "never off", "never stops", "non stop")),
              "Check the programmer first: a light on ADVANCE or ON rather than AUTO is a button "
              "pressed by accident, and a room thermostat left high keeps the heating running. If "
              "the radiators heat up when the hot water is on, the diverter valve has stuck and wants "
              "replacing - about 150 to 250 pounds fitted, and worth doing before winter. A frost "
              "stat firing on a cold night is normal.",
              avoid=("not working", "broken", "cold", "no heating", "pressure", "noise", "noisy",
                     "bleed", "banging", "kettling", "thermostat setting", "how much",
                     # a bill question is about what it costs to leave the heating on, not about
                     # why it will not stop
                     "cost", "costs", "expensive", "bill", "bills", "cheaper", "save",
                     "saving", "money", "efficient", "efficiency", "how long", "every day",
                     # "is it safe to leave the boiler on all night" asked whether it is safe, not
                     # why it will not stop, and it had its own card
                     "safe", "safety", "unsafe", "dangerous", "risk", "carbon monoxide",
                     "smell gas", "yellow flame", "leave it on"),
              # "my boiler is running all the time" reached the row that says how long a machine
              # takes to do a job on the word "time", and "my heating stays on all night" reached
              # the hot-night card on "night". Neither is as specific as the valve and programmer
              # this row is about, so it wins the tie.
              bias=3),
        entry("door-rubbing", (("door", "doors", "front door", "back door", "shed door",
                                "bedroom door", "bathroom door", "internal door", "cupboard door"),
                               ("sticking", "sticks", "stuck", "rubbing", "rubs", "dragging", "drags",
                                "scrapes", "swollen", "swelling", "swelled", "warped", "wont close",
                                "won't close", "wont shut", "won't shut", "hard to close", "catching",
                                "jammed", "have to slam", "has to be slammed")),
              "A door that drags or will not shut is usually swollen from damp in winter, or has "
              "dropped on its hinges because a screw pulled out. Give the season a fortnight first, "
              "with the heating on or a dehumidifier in the room, because many free up on their own. "
              "If it has dropped, tighten the top hinge screws, or replace them with longer ones. "
              "Otherwise take a millimetre at a time off the edge where the paint has rubbed bright, "
              "and seal the bare wood afterwards so it does not take in water and swell again.",
              # Main's `squeaky-door` also keys "sticking" and "rubbing" and sits later in the file
              # with bias=1, so on a tie it took every swollen or dragging line. The damp-and-plane
              # answer is the one for those, and the bias is what makes it win; the squeak-only lines
              # still reach `squeaky-door` because no word of this entry's second key is in them.
              bias=3,
              avoid=("lock", "locks", "key", "keys", "car", "cars", "van", "fridge", "freezer",
                     "oven", "microwave", "dishwasher", "washing machine", "washer", "dryer",
                     "drawer", "drawers", "cupboard", "wardrobe", "glass", "window", "windows",
                     # a dog that will not shut up is a noise question, and "shut up" alone was
                     # enough to send "next door's dog wont shut up" to the swollen-door card
                     "dog", "dogs", "puppy", "barking", "bark", "barks", "cat", "cats", "meowing",
                     "neighbour", "neighbours", "neighbor", "neighbors", "next door", "upstairs",
                     "downstairs", "shut up",
                     # a door that will not shut is not a door that swings hard: a stiff key is
                     # the barrel card's, and "oil the hinges" is the wrong answer to it
                     "key", "keys", "lock", "locks", "keyhole", "barrel", "handle", "latch")),
        entry("door-lock-stiff", (("lock", "locks", "door lock", "barrel", "deadlock", "yale",
                                   "latch", "key", "keys", "front door",
                                   # a key that will not go into the keyhole is a dirty or worn
                                   # keyway, and "i cant get my key in the lock" fell through to
                                   # the locked-out card about spares and a locksmith
                                   "key in the lock", "key into the lock", "key in my lock",
                                   "key wont go in", "key won't go in", "key does not go in",
                                   "get my key in", "get the key in"),
                                  ("stiff", "sticky", "stuck", "sticking", "sticks", "jammed",
                                   "hard", "wont turn",
                                   "won't turn", "grinding", "tight", "difficult", "gritty",
                                   "wont go in", "won't go in", "turning",
                                   # "my front door key sticks" is the same barrel as "my lock is
                                   # stiff", and "how do i stop a door key sticking in the lock"
                                   # was reaching `change-a-lock` on "how" and "lock"
                                   "stiffen", "stiffens", "stiffened",
                                   "seizing", "seized", "grates", "grating", "rough",
                                   # a key that will not go into the keyhole is this card, not
                                   # the press-the-door card and not the composer's locked-out
                                   # line: "i cant get my key in the lock" got both
                                   "in the lock", "into the lock", "in my lock", "into my lock",
                                   "get my key in", "get the key in")),
              _door_lock_stiff,
              bias=2,
              avoid=("car", "cars", "van", "bike", "bicycle", "suitcase", "case", "padlock", "safe",
                     "lost", "lost my keys", "locked out", "locked in", "keys locked", "cut a key",
                     "laptop", "keyboard", "password", "account", "windows", "drawer", "lockbox",
                     "post box", "postbox")),
        # A key that has snapped off in the barrel is not a lock to buy and not a lock that is
        # stiff: the piece is still in there and every further turn pushes it deeper. This row
        # owns the line, and `change-a-lock` and `door-lock-stiff` pass on it.
        entry("key-broken-in-lock",
              (("key", "keys", "door key", "front door key", "spare key", "piece of key",
                "half a key", "broken key", "key blade"),
               ("snapped", "snap", "snapped off", "snapped in", "broke off", "broken off",
                "broke in", "broken in", "sheared", "twisted off", "bent", "stuck", "jammed",
                "stuck in the lock", "stuck in my lock", "jammed in", "half in", "get it out",
                "get out", "remove", "removing",
                # "how do i get a broken key out of a lock" scored 3 on the phrase and reached the
                # laptop keyboard card on "keyboard"-like "key" + "broken", so the pulling out is
                # said in the words people use for it
                "out of the lock", "out of my lock", "out of the door", "out of the barrel",
                "pull out", "pull it out", "dig out", "extract", "extracting", "out of")),
              "Stop turning it: the piece in the barrel is what the pins are holding, and every "
              "extra turn pushes it further in. Put a drop of WD-40 or graphite at the keyway, then "
              "grip whatever is proud with needle-nose pliers or thin side cutters, pull straight "
              "out rather than sideways, and jiggling the door handle while you pull helps. A short "
              "piece just inside can be walked out with the thin blade of a jigsaw or a coping saw "
              "slid alongside it. If it is in past the face of the barrel, it is a locksmith: about "
              "\u00a360 to \u00a3120 to drill and replace the cylinder, and keep the door on the "
              "latch until they come. Do not glue anything to it and do not push a second key in.",
              # a key that belongs to a car or a padlock is not this row, and a lost key is the
              # lost-keys card's
              avoid=("car", "cars", "van", "bike", "bicycle", "motorbike", "suitcase", "padlock",
                     "safe", "laptop", "keyboard", "password", "account", "phone", "lost",
                     "lost my keys", "mislaid", "locked out", "locked in", "cut a key", "spare key",
                     "cut a spare", "piano", "map", "answer", "code"),
              bias=3),
        # The keys are lost and there is nothing to open yet, so the way back in comes before any
        # searching. "lost" plus a key word is the key, and every way of being stiff stays with
        # `door-lock-stiff`, which passes on "lost" itself.
        entry("lost-house-keys",
              (("keys", "key", "keyring", "key ring", "house keys", "door key", "front door key",
                "keys to the house", "set of keys"),
               ("lost", "lose", "losing", "mislaid", "misplaced", "missing", "gone",
                "cant find", "cannot find", "can't find", "no idea where", "nowhere",
                # A key nobody has is the same evening as a key that is lost, however it is put:
                # "how do i start my car without the key" and "how do i get in without my keys"
                # are the searching-and-locksmith question, and the line says it without ever
                # using the word lost.
                "without the key", "without a key", "without my keys", "without keys",
                "without the keys", "no key", "dont have the key", "don't have the key",
                "not got the key", "havent got the key", "haven't got the key")),
              _lost_keys,
              # keys lost *inside* the house are a searching question, and the composer already has
              # the retrace-your-steps answer for those
              avoid=("stiff", "sticky", "jammed", "wont turn", "won't turn", "hard to turn",
                     "grinding", "piano", "keyboard", "laptop", "computer", "password",
                     "account", "map", "answer", "code", "locked in", "locked out",
                     "cut a key", "cut a spare", "car battery", "remote", "fob battery",
                     "in the house", "in my house", "in the flat", "in my flat", "at home",
                     "somewhere in", "in my bag", "in my pocket", "in the car", "in the office",
                     "down the back of"),
              bias=2),

        # A lock that will not turn is the stiffness row above; a lock the person wants to change,
        # fit or has broken is this one, and "how do i change the lock on my front door" was getting
        # the phone's screen-timeout setting.
        entry("change-a-lock", (("lock", "locks", "door lock", "cylinder", "euro cylinder",
                                 "barrel", "mortice", "mortise", "deadlock", "night latch", "yale"),
                                ("change", "changing", "replace", "replacing", "fit", "fitting",
                                 "new", "broken", "broke", "snapped", "put on", "install", "myself",
                                 "upgrade", "key", "keys", "how"),
                                # The phone's screen-lock setting keys "how" and "change" too, and a
                                # bare "how do i change a lock" scored one under it. The phrase is
                                # the job itself, so it carries the line.
                                ("change a lock", "change the lock", "change my lock",
                                 "change the lock", "change the locks", "replace a lock",
                                 "replace the lock", "new lock", "fit a lock", "fit a new lock",
                                 "broken lock", "lock broken", "change the barrel",
                                 "change the cylinder")),
              "Measure the old cylinder before you buy one: the length each side of the fixing screw, "
              "and whether it sits flush with the door or sticks out. Undo the retaining screw on the "
              "door edge, put the key in and turn it slightly, and the cylinder slides out; the new one "
              "goes in the same way, with the key in it. Fifteen minutes with a screwdriver, the door "
              "left open while you work, and about fifteen to thirty pounds for a kite-marked one.",
              # A lock the person wants to swap is not a door that will not open, and "how do i change
              # the lock on my front door" was reaching the swollen-door card.
              bias=2,
              avoid=("car", "cars", "van", "bike", "bicycle", "suitcase", "padlock", "safe",
                     "locked out", "locked in", "keys locked", "cut a key", "spare key", "laptop",
                     "phone", "keyboard", "password", "account", "windows", "drawer", "lockbox",
                     "post box", "postbox", "stiff", "jammed", "wont turn", "won't turn",
                     "sticking", "sticks", "stuck", "hard to turn", "gritty", "grinding",
                     "screen", "sim", "pin", "app",
                     # A lock the person cannot get through is not a lock they are buying: "i locked
                     # myself out" and "how do i open a locked door" were both told to measure the
                     # cylinder, and the phrase forms of "locked out" do not inflect.
                     # the phrase is the whole ask: "can i change a lock myself" says "lock myself"
                     # as plainly as "i locked myself out" does, so only the out-phrase stands down
                     "locked myself out", "lock myself out", "locks myself out", "locking myself out",
                     "locked out of", "lost my keys", "lost the keys", "open a locked", "locked door",
                     "wont open", "won't open",
                     # Somebody asking who to call has already decided not to do it themselves:
                     # "who do i call about a broken lock" was told to measure the old cylinder,
                     # and the who-to-call row is the answer, with the locksmith it names.
                     "who do i call", "who should i call", "who can i call", "who could i call",
                     "who do i ring", "who should i ring", "who to call", "who to ring",
                     "who do i get", "someone to call", "someone to ring", "locksmith",
                     # a key that will not turn, and above all a key that has broken off inside,
                     # is not a lock to buy: "how do i get a broken key out of a lock" was told to
                     # measure the old cylinder, and the stuck-key card below is the answer
                     "sticking", "sticks", "stuck in the lock", "stuck in my lock",
                     # "i cant get my key in the lock" was told to measure the old cylinder; a key
                     # that will not go in is the stiff keyway below, not a lock to buy
                     "get my key in", "get the key in", "cant get my key", "can't get my key",
                     "key wont go in", "key won't go in", "key does not go in", "key in",
                     "key stuck", "key snapped", "key broke", "key broke off", "broken key",
                     "snapped off", "snapped in", "broke off in", "broke in the lock",
                     "half a key", "piece of key", "jammed in the lock", "key jammed")),
        # "How do i stop locking myself out" is a habit question, not a lock to change and not a
        # phone setting: the screen-timeout row keys "stop" and "locking" and was taking it.
        entry("stop-locking-yourself-out",
              (("locked myself out", "locking myself out", "lock myself out", "locks myself out",
                "locked out again", "lock myself out again", "keys locked inside",
                "keys locked in the house", "keys locked in my flat", "keys are locked inside",
                "keep locking myself out", "always locking myself out", "keys locked in",
                "leave my keys", "left my keys", "forget my keys", "forgot my keys"),
               ("stop", "again", "keep", "keeps", "always", "how do i", "how can i", "prevent",
                "avoid", "happen", "happening", "trick", "not do it")),
              "Put the key in one place that you walk past on the way out - a hook inside the front "
              "door - and nowhere else, because the pockets, the bag and the coat are what lose it. A "
              "spare with a neighbour or family is free and saves the locksmith, and a key safe by the "
              "door (about twenty pounds, screwed on, with a code) covers the rest. If you rent, ask "
              "the landlord for a second key: yours to pay for, and almost always allowed.",
              bias=1,
              # Asking how to stop it is the habit question; "i locked myself out again" is a person
              # standing outside the door, and the composer has the way-in lines for that, so the
              # entry needs one of these words before it may answer.
              ask=("stop", "stops", "prevent", "avoid", "keep on", "keep", "keeps", "always",
                   "never again", "trick", "habit", "how do i not", "how can i not"),
              avoid=("car", "cars", "van", "vehicle", "boot", "phone", "screen", "sim", "pin",
                     "password", "account", "email", "facebook", "laptop", "change the lock",
                     "new lock", "broken lock", "lost my keys", "lost the keys", "cant find",
                     "can't find")),
        entry("door-handle-loose", (("handle", "handles", "door handle", "knob", "knobs",
                                     "door knob", "latch", "spindle", "grub screw"),
                                    ("loose", "wobbly", "wobbles", "wobble", "rattles", "rattle",
                                     "spins", "spinning", "fallen off", "fell off", "came off",
                                     "come off", "dropped")),
              "The grub screw on the neck of the handle has worked loose: there is a small screw there, "
              "sometimes under a cap you can flick off, and tightening it onto the spindle takes two "
              "minutes with a small screwdriver or an Allen key. If it keeps coming loose, put a dab of "
              "thread-lock on the spindle, or a sliver of tape. A handle that spins without opening the "
              "door has lost or snapped its spindle, and a new handle is about ten pounds.",
              avoid=("suitcase", "bag", "case", "pan", "saucepan", "frying pan", "pot", "cup", "mug",
                     "tap", "taps", "kettle", "oven", "fridge", "freezer", "drawer", "window",
                     "wheelbarrow", "lawnmower", "drill", "tool", "bike", "car", "doorbell",
                     "knife", "saw", "umbrella")),
        entry("window-painted-shut", (("window", "windows", "sash", "sash window", "casement",
                                       "upvc window", "upvc windows"),
                                      ("painted", "stuck", "seized", "jammed", "swollen",
                                       "stiff")),
              "It is paint gluing the sash to the frame: run a sharp knife, held flat, round the join "
              "between the frame and the opening sash to cut the paint film, then work a thin scraper "
              "or a wide chisel gently into the gap and ease the window open rather than forcing the "
              "handle. Once it is open, sand the paint off the meeting faces and rub a candle or "
              "silicone spray along them. Never lever against the glass.",
              bias=1,
              # "how do i paint a room with no windows" is a decorating question: "painted" plus
              # "windows" handed it here, where the answer is about a sash that will not open. The
              # painting rows own those lines, so this one stands down on what a painter says.
              avoid=("car", "cars", "van", "screen", "phone", "laptop", "computer", "software",
                     "browser", "windscreen", "shower", "clean", "cleaning", "curtain", "curtains",
                     "blind", "blinds",
                     # "how do i paint a room with no windows" is a decorating line: the window is
                     # only what the room has not got, and the paint-glued-sash answer is about a
                     # window that will not open. Main answered it with the Windows disk steps.
                     "paint a room", "painting a room", "paint the room", "painting the room",
                     "paint a wall", "paint a ceiling", "decorating", "decorate", "roller",
                     "undercoat", "emulsion", "paint the walls", "no window", "no windows",
                     "without a window", "windowless",
                     # a window frame that wants painting is a painting job, and both window-fault
                     # rows were taking it: "how do i paint a window frame" got the cut-the-paint-
                     # film answer twice over, which never mentions a brush
                     "paint a window", "painting a window", "paint my window", "paint the window",
                     "paint window", "painting the windows", "paint the windows", "repaint",
                     "painting a window frame", "paint a window frame", "brushes", "brush",
                     "paint a sash", "painting a sash", "paint the sash", "paint a casement",
                     "paint the frame")),
        entry("door-slam-wind", (("door", "doors", "front door", "back door", "porch", "gate"),
                                 # no "draught" here: a cold draught under a door is a gap with its
                                 # own answer, and this row is about a door that moves. "how do i stop
                                 # a draught from the front door" got the holder-and-closer card.
                                 ("slam", "slams", "slamming", "bangs", "banging", "bang", "rattles",
                                  "rattling", "wind", "blows")),
              "A door that slams in the wind wants a holder or a closer, not a shut window: a "
              "hook-and-eye or a door holder on the frame keeps it open, and an overhead closer set to "
              "slow the last few inches stops it banging shut. Rubber bumpers on the stop take the "
              "rattle out of the catch, and a wedge under the bottom holds a door that swings. A front "
              "door that rattles is usually the latch plate, and a wrap-around striker plate or a strip "
              "of foam behind it stops that.",
              bias=2,
              avoid=("car", "cars", "van", "garage", "cupboard", "fridge", "oven", "microwave",
                     "washing machine", "dishwasher", "drum", "tumble dryer", "doorbell", "baby",
                     "toddler", "child",
                     # a swollen door is not a windy one: it rubs, and it gets the planing answer
                     "swollen", "swelling", "swelled", "warped", "sticking", "stuck", "rubbing",
                     "drags", "dragging", "have to slam", "has to be slammed",
                     # a draught is the gap round the door, and "how do i stop a draught under a
                     # door" got the holder-and-closer answer: that is the cleaning row's, and this
                     # one keeps the slam, the bang and the rattle.
                     "draught", "draughts", "draft", "drafts", "draughty", "drafty", "cold air",
                     "cold coming", "lets in", "letting in", "coming under the door",
                     "under the door", "around the door", "round the door", "draught excluder",
                     "excluder",
                     # a finger or a toe in the door is an injury, not a door that swings:
                     # "my fingernail is black after i slammed it in the door" was answered with
                     # the holder-and-closer card, because "door" and "slammed" are its two keys
                     "my finger", "my fingers", "my thumb", "my hand", "my toe", "my foot",
                     "fingernail", "fingernails", "toenail", "toenails", "nail", "nails",
                     "black", "bruise", "bruised", "purple", "blood",
                     # someone shutting a door in a temper is not a door that moves in the wind:
                     # "he slammed the door" after a row got the holder-and-closer card, and the
                     # door in it is the person at the end of the row, not a hinge
                     "slammed the door", "slams the door", "door on me", "door in my face")),
        # same whether a person says "squeaks", "creaks" or "keeps sticking". Named things that squeak
        # and are not doors (shoes, a chair, a bike) are kept out.
        entry("door-wont-open", (("wont open", "won't open", "will not open", "wont budge",
                                  "won't budge", "cant open", "can't open", "cannot open",
                                  "stuck", "stuck shut", "jammed", "jammed shut", "locked",
                                  "locked in", "locked in my flat", "locked in my house",
                                  "locked in the house", "locked in my room", "trapped in my flat",
                                  "shut in my room", "swollen", "swelled", "warped",
                                  "cant get out", "can't get out", "wont turn", "won't turn",
                                  "wont close", "won't close",
                                  # "i cant get in my front door" is the same shut door as "my
                                  # door wont open", and it fell through to the composer's
                                  # locked-out line about spares and a locksmith
                                  "cant get in", "can't get in", "cannot get in", "wont let me in",
                                  "won't let me in", "key wont work", "key won't work"),
                                 # No bare place word here: "i cant get out of the house" is the
                                 # going-out line, and this answer must not take it. A flat or a
                                 # room only reaches this entry with a door or a lock in the line.
                                 ("door", "doors", "front door", "back door", "door lock",
                                  "the lock", "latch", "handle", "deadlock", "mortice", "yale",
                                  "shed door", "porch")),
              "Start with the lock: press the door inwards while you turn the handle, and try "
              "lifting the handle up, because plenty of doors lock that way and half a turn frees "
              "them. If the handle turns loosely and nothing clicks, the spindle inside has gone "
              "and that is a locksmith. A door swollen by damp usually frees with a firm push at "
              "shoulder height while someone turns the handle, or with a thin card slid in on the "
              "latch side; if it will not shut at all, plane a millimetre off the edge that rubs. "
              "If it is rented, ring the landlord or a locksmith who quotes on the phone - and if a "
              "child or anyone is shut in, ring 999 rather than fight the door.",
              avoid=("squeak", "squeaks", "squeaky", "squeaking", "creak", "creaks", "creaking",
                     # a key that will not go into the keyhole is the stiff keyway card's, not a
                     # door that will not open: "i cant get my key in the lock" was answered with
                     # the press-the-door-and-lift-the-handle card
                     "key in the", "key into the", "get my key", "getting my key", "keyway",
                     "key wont go", "key won't go", "wont go in", "won't go in",
                     "oil", "oiling", "hinge oil", "draught", "draughts", "draft", "paint",
                     "painting", "painted", "decorate", "decorating", "letterbox", "letter box",
                     "childproof", "child proof", "cat flap", "pet flap", "car door", "van door",
                     "garage door", "keypad", "porch light", "doorbell", "door bell", "camera",
                     "handle a", "difficult", "slam", "slamming", "bang", "bangs",
                     # an oven, a fridge or a washer door is an appliance question with its own
                     # answers, and this row's lock-and-plane advice is wrong for all of them
                     "oven", "cooker", "fridge", "freezer", "microwave", "washing machine",
                     "dishwasher", "tumble dryer", "cupboard", "wardrobe", "cabinet"),
              bias=1),
        # "the gate is hanging off", "the shed door is broken" and "the hinge on my cupboard is
        # loose" are all the same fault in different furniture: a hinge screw has pulled out of soft
        # wood. Nothing answered them (the neutral pool said "Got it"), and `door-rubbing` is the
        # damp-and-plane answer for a door that drags, not this. The fault word and the hinged thing
        # are both in the line, so the answer is the repair, not the diagnosis.
        entry("hinge-sag",
              (("hanging off", "hanging by", "hanging open", "sagging", "sag", "sags",
                "has dropped", "had dropped", "is dropping", "keeps dropping", "drooping", "loose",
                "loosened", "wobbly", "wobbling", "wobble",
                "coming off", "came off", "fallen off", "fell off", "pulled out", "ripped off",
                "blown down", "blew down", "blown off", "knocked down", "snapped", "broken",
                "breaks", "broke", "split"),
               ("gate", "gates", "garden gate", "side gate", "gate post", "shed door", "shed",
                "door", "doors", "cupboard", "cupboards", "cupboard door", "cabinet",
                "cabinet door", "wardrobe", "wardrobe door", "hinge", "hinges", "gate post",
                "gatepost")),
              "Nine times in ten a sagging gate, shed door or cupboard door is a hinge screw that has "
              "pulled out of the wood, not the hinge wearing out. Take the weight off the free "
              "corner, pack the old screw holes with glued matchsticks or a sliver of dowel and screw "
              "back in, or move the hinge 10cm along with longer screws. If the wood round the hinge "
              "is rotten or the hinge is torn, fit a new hinge onto sound timber - and if the post "
              "moves in the ground, brace or replace the post.",
              # the other door answers own their own faults (a lock, a handle, a draught, a squeak, a
              # swollen edge) and a shed or greenhouse roof is a leak, not a hinge
              ask=("hinge", "hinges", "hinged", "gate", "gates", "garden gate", "side gate",
                   "shed door", "shed", "door", "doors", "cupboard", "cabinet", "wardrobe",
                   "gate post", "gatepost"),
              avoid=("roof", "roofs", "leaking", "leak", "leaks", "glass", "glazing", "window",
                     "windows", "lock", "locks", "key", "keys", "handle", "handles", "knob",
                     "latches", "latch", "squeak", "squeaks", "squeaky", "creak", "creaks",
                     "creaking", "draught", "draughts", "draft", "paint", "painted", "paintwork",
                     "swollen", "swelling", "warped", "damp", "garage door", "car door",
                     "van door", "car", "van", "fridge", "freezer", "oven", "drawer", "drawers",
                     "cat flap", "pet flap", "letterbox", "letter box", "doorbell", "door bell",
                     # "dropped" is a fault word only on a hung thing: what people drop is a phone,
                     # keys or a purse, and "i dropped my phone in the shed" was taking this answer
                     "phone", "phones", "mobile", "wallet", "purse", "glasses", "keys", "keyring",
                     "dropped my", "dropped it", "dropped a", "dropped her", "dropped his",
                     # "fence between me and next door is broken" is about the fence: the words of
                     # "next door" are not a door of anyone's
                     "next door", "nextdoor")),
        # A fence is not a hinge: "fence panel blew down" and "the back fence is broken" were both
        # getting the gate-hinge answer, and the how-to lines got a shrug. The fault and the fence
        # part are both in the line, so the answer is the repair. Height, ownership and treating are
        # three other questions about the same object, so each has its own row.
        entry("fence-panel",
              (("blew down", "blown down", "blew out", "blown out", "came off", "come off",
                "came out", "come out", "fell out", "fallen out", "fell down", "fallen down",
                "knocked down", "knocked out", "loose", "loosened", "wobbly", "wobbling",
                "broken", "broke", "snapped", "split", "damaged", "rotten", "rotted",
                "repair", "fix", "mend", "replace", "put back", "falling out",
                "keeps falling", "keeps coming", "blew over", "blown over", "fell over",
                "fallen over", "blowing down", "blowing over", "blow down", "blow over",
                "blew off", "blown off"),
               ("fence panel", "fence panels", "panels", "panel of fence", "panel of the fence",
                "fence", "fencing", "fence boards", "fence board", "feather edge", "closeboard",
                "gravel board", "gravel boards", "arris rail", "fence rail", "picket fence",
                "trellis")),
              "A blown-down panel is usually the panel, not the posts: lift it back between the posts "
              "and screw it to the rails through the post, two 65mm galvanised screws per rail, "
              "rather than just slotting it in - or fit a new panel of the same width. If boards have "
              "come off, feather-edge boards go back on with galvanised nails, each overlapping the "
              "last by about 25mm, and check the gravel board the panel sits on first, because a "
              "rotted one lets the whole panel drop. If panels keep going in wind, leave a 25mm gap "
              "under the panel so the wind passes through instead of pushing.",
              ask=("fence", "fencing", "fence panel", "fence panels", "panel", "panels",
                   "gravel board", "feather edge", "closeboard", "picket", "trellis"),
              # a fence key word here is a fence, so a repair word settles it; the bare "fence"
              # key is shared with the height and ownership rows and a tie went to the wrong one
              bias=1,
              # height, ownership and treating are the other three fence questions, and the cost of
              # one is in costs.py - none of them wants the repair method
              avoid=NOT_A_FENCE_JOB + ("how tall", "how high", "tall can", "high can", "maximum height",
                     "max height", "height limit", "planning", "planning permission",
                     "boundary", "who owns", "whose", "who is responsible", "who pays",
                     "who has to pay", "deeds", "title plan", "my neighbour", "my neighbor",
                     "neighbour says", "neighbor says", "neighbours fence", "neighbor's fence",
                     "neighbour's fence", "neighbours fence", "how much", "cost", "costs",
                     "price", "prices", "quote", "cheapest", "treat", "treating", "treatment",
                     "stain", "staining", "paint", "painting", "painted", "preserver",
                     "preservative", "creosote", "fence spray", "spray",
                     # A panel that keeps going is a question about why, not about this panel: the
                     # windproof row answers it. Without these, "how do i stop my fence blowing
                     # down" and "keeps blowing down" came here and the windproof row could never
                     # win the line it exists for.
                     "stop my fence blowing", "stop the fence blowing", "stop it blowing",
                     "stop blowing down", "keeps blowing down", "keeps blowing over",
                     "blowing down again", "windproof", "wind proof", "keep the fence up",
                     # a prevention question, not a repair one: "how do i stop my fence rotting" is
                     # the treating row, and a bare "rot"/"rotting" is not in this row's key, so it
                     # loses on covered words without an avoid - which would also stand this row
                     # down for "the gravel board has rotted and the panel has dropped", the line
                     # its own answer names the gravel board in
                     "stop my fence rotting", "stop it rotting", "stop the fence rotting",
                     "prevent rot", "rotting again")),
        entry("fence-post",
              (("rotted", "rotten", "rot", "rotting", "wobbly", "wobbling", "leaning",
                "leaned", "loose", "loosened", "sinking", "sunk", "moves", "moving",
                "rocking", "broke", "broken", "snapped", "replace", "repair", "fix",
                "strengthen", "concrete"),
               ("fence post", "fence posts", "gate post", "gatepost", "fence", "fencing",
                "post", "posts")),
              "A post that has rotted or gone loose at the bottom wants replacing, not bracing: dig it "
              "out and set a new 100mm post 600mm into the ground, prop it plumb, and fill the hole "
              "with Postcrete poured dry and watered. If only the bottom has gone, cut the post off "
              "above the rot and bolt a galvanised repair spur onto the sound timber. Line the new "
              "post up with its neighbour before the concrete sets, and stand it on a gravel board or "
              "a slate so the base is not sitting in wet soil.",
              ask=("fence post", "fence posts", "gate post", "gatepost", "fence", "fencing",
                   "post", "posts"),
              bias=1,
              avoid=NOT_A_FENCE_JOB + ("post office", "post a letter", "letter", "parcel", "delivery", "mail",
                     "blog", "logged", "job", "position", "applying", "apply", "instagram",
                     "facebook", "tiktok", "photo", "photos", "comment", "review", "how tall",
                     "how high", "planning", "boundary", "who owns", "whose", "how much",
                     "cost", "costs", "price", "quote", "treat", "treating", "stain",
                     "staining", "paint", "painting", "preserver", "creosote")),
        entry("fence-treat",
              (("treat", "treating", "treatment", "stain", "staining", "paint", "painting",
                "painted", "preserver", "preservative", "creosote", "weatherproof",
                "waterproof", "protect", "protecting", "seal", "sealing", "varnish",
                "oil it", "last", "how often", "how long",
                # "how do i stop my fence rotting" and "the fence is rotting" are treating
                # questions - the rot the treatment prevents, or the board to replace
                "rot", "rotting", "rown", "gone soft", "soggy"),
               ("fence", "fencing", "fence panels", "fence panel", "feather edge", "closeboard",
                "gravel board", "trellis", "shed")),
              "Treat bare fence timber every two or three years, on a dry day with no rain forecast "
              "for 24 hours, and brush it on along the grain rather than flooding it. A water-based "
              "shed-and-fence preserver is fine for most fences and dries in a couple of hours; a "
              "solvent one soaks deeper but smells for days. Do the bottom edge of the boards and the "
              "cut ends, which is where the water gets in, and replace a rotted gravel board instead "
              "of treating it. A stain sinks in and does not peel, which is why it beats paint on a "
              "fence.",
              ask=("fence", "fencing", "fence panel", "fence panels", "trellis", "shed",
                   "feather edge", "closeboard", "gravel board"),
              # a fence that is rotting with no post named is the treating question, and the post
              # row reads "rot" too; naming a post still outranks this on covered words
              bias=2,
              avoid=NOT_A_FENCE_JOB + ("how tall", "how high", "planning", "boundary", "who owns", "whose",
                     "how much", "cost", "costs", "price", "quote", "blew down", "blown down",
                     "blew out", "blown out", "came off", "fell down", "fell out", "rotted post",
                     "fence post", "gate post", "paint a room", "paint the room", "painting a room",
                     "decorating", "wall", "walls", "door", "doors",
                     # a panel that has dropped is the panel answer, which names the rotted gravel
                     # board under it: treating is the question when the timber is still up
                     "gravel board", "dropped", "dropping", "sagging", "fallen", "fell out")),
        entry("fence-height",
              (("how tall", "how high", "tall can", "high can", "tallest", "highest",
                "maximum height", "max height", "height limit", "planning permission",
                "planning", "can i build", "can i put", "can i put up", "put up a fence",
                "put a fence up", "allowed", "legal",
                # the limit said as a measurement: "can i put up a fence 2 metres high" was the
                # build card, and once the build row stood down on the height words it was the
                # post hole. The number is this row's own signal.
                "metres high", "metre high", "metres tall", "metre tall", "feet high",
                "foot high", "2 metres", "2m high", "six foot"),
               # a hedge has its own law (the high-hedges rules), so it is not this row's
               ("fence", "fencing", "fence panels", "fence panel", "wall", "garden wall")),
              "In England and Wales a fence or a garden wall can be 2 metres high without planning "
              "permission, or 1 metre where it is next to a road, footpath or driveway; conservation areas, listed "
              "buildings and some new estates have stricter rules, so ring the council's planning "
              "desk before going higher. On a boundary you also want the neighbour's agreement, "
              "because a fence over 2 metres can be complained about as a nuisance even where the "
              "height itself is allowed.",
              ask=("fence", "fencing", "fence panel", "fence panels", "wall", "garden wall"),
              avoid=NOT_A_FENCE_JOB + ("how much", "cost", "costs", "price", "quote", "blew down", "blown down",
                     "blew out", "blown out", "came off", "fell down", "repair", "fix", "replace",
                     "treat", "treating", "stain", "staining", "paint", "painting", "preserver",
                     "creosote", "rotten", "rotted", "wobbly", "loose", "boundary fence is",
                     "who owns", "whose", "who pays", "who has to pay", "deeds",
                     # A count is the quantity rows' question, whatever height came with it:
                     # "how many blocks for a garden wall 6 metres long and 1 metre high" was
                     # answered with the 2 metre planning limit.
                     "how many blocks", "how many bricks", "how many slabs", "how many tiles",
                     "how many panels", "how many posts", "how many boards", "how many sheets",
                     "how many bags", "how many rolls", "how many metres of")),
        # "what is a gravel board for" was a shrug: the board is the part of a fence that keeps the
        # panel out of the wet, and nobody knows what it is until they have had to replace one.
        entry("fence-gravel-board",
              (("gravel board", "gravel boards", "gravelboard", "gravelboards", "gravel boarding",
                "gravelboard height", "gravel boards keep"),
               ("what", "whats", "why", "for", "need", "use", "useful", "high", "height",
                "ground", "panel", "panels", "post", "posts", "fence", "fences", "sit", "sits",
                "fit", "fitted", "rot", "replace")),
              "A gravel board is the timber along the bottom of the run, and its job is to hold the "
              "panel up out of the wet ground so the bottom rail does not rot: it sits on the soil or "
              "in a slotted concrete board, with the panel fixed above it. Set the top of a timber "
              "board about 25mm above the ground and leave the panel 50mm clear of it, so air gets "
              "between the two. A slotted concrete gravel board lets you slide a rotten board out "
              "without taking the panel down.",
              bias=1,
              avoid=NOT_A_FENCE_JOB + (
                     "how much", "cost", "costs", "price", "quote", "how many", "how long",
                     "who owns", "whose", "deeds", "planning", "how tall", "how high can",
                     "how deep", "depth", "postcrete", "how far apart", "spacing", "how thick",
                     "put up", "build", "install", "treat", "treating", "stain", "paint",
                     "painting", "blew", "blown", "fell", "fallen", "leaning", "wobbly")),
        # "how do i put up a fence", "how do i build a fence" and "where do i start with a new
        # fence" are the build question, and "put up a fence" was in the owner's key: the deeds
        # answer came back for a person who wanted to know where to dig.
        entry("fence-build",
              (("how do i put up a fence", "how to put up a fence", "how do i put up my fence",
                "put up a fence myself", "put a fence up myself", "how do i build a fence",
                "how to build a fence", "how do i fence", "fence my garden", "fencing my garden",
                "how do i fence off",
                # "where do i start" and "how long does it take to build" on their own are not a
                # fence: the bare phrase answered "where do i start with my essay" and the plain
                # "where do i start" with the posts and the string line. The subject has to be in
                # the line, and the whole phrase is what carries it.
                "where do i start with a fence", "where do i start on a fence",
                "where do i start with my fence", "where do i start on my fence",
                "where do i start with the fence", "where do i start on the fence",
                "where do i start with the fencing", "where do i start with fencing",
                "where do i begin with a fence", "where do i begin with my fence",
                "where do i begin with the fence", "where to start with a fence",
                "where to start with my fence", "where do i start with a new fence",
                "where do i start with fence panels",
                # the subject can sit before the where-phrase instead of after it: "i want to put up
                # a fence where do i start" and "i want to build a fence where do i start" have no
                # "how do i" and no "where do i start with", so the where-phrase fence words above
                # missed them and the build card was the plan reply. The verb and the fence are
                # enough, wherever they sit in the line.
                "build a fence", "build my fence", "build the fence", "building a fence",
                "put up a fence", "putting up a fence", "put a fence up", "putting a fence up",
                "erect a fence", "install a fence", "installing a fence", "new fence",
                "want a fence", "put in a fence", "putting in a fence",
                "how long does it take to put up a fence", "how long to put up a fence",
                "how long does it take to build a fence", "how long does building a fence take",
                "what do i need to put up",
                "what do i need for a fence", "can i put up a fence", "can i build a fence",
                "can i put a fence up", "how do i install a fence", "how do i erect a fence",
                "how do i put a fence up", "do it myself", "is it hard to put up a fence",
                "is it hard to build a fence", "is it easy to put up a fence",
                "hard to put up a fence"),
               ("fence", "fences", "fencing", "garden", "panel", "panels", "closeboard",
                "boundary", "posts"),
               # a build line is asked as "how do i", "how long" or "can i": the ask itself is the
               # third part, which is what lifts these over the treating and height rows that share
               # the word "fence" and tied with the whole-fence answer at five
               # "where do i" and "where to" were here and every "where do i start with my
               # garden" matched them on the word garden alone: a bare where-phrase is not a
               # fence, so the fence phrases above carry that half now.
               ("how do i", "how to", "how long", "how much time", "can i", "what do i",
                "is it hard", "is it easy")),
              "Set the posts first: a string line between the two end posts keeps the run straight, "
              "then each post goes 600mm deep and 1.8m apart in concrete, braced for a day. The gravel "
              "boards go on next and the panels screw through their rails into the posts, one post's "
              "worth at a time. Two people with an auger do 20 metres in a weekend; on a boundary, "
              "check the deeds and the 2 metre rule before you dig.",
              bias=1,
              guard=_a_fence_is_named,
              avoid=NOT_A_FENCE_JOB + (
                     "how much", "cost", "costs", "price", "quote", "who owns", "whose", "deeds",
                     "planning permission", "treat", "treating", "stain", "paint", "painting",
                     "how tall", "how high", "blew", "blown", "fell", "fallen", "repair", "replace",
                     "rotten", "rotted", "wobbly", "loose", "leaning", "came off", "panel has",
                     # the post questions have their own rows, and this one only knows the run
                     # a neighbour putting one up is the boundary question, not the build
                     "my neighbour", "my neighbor", "neighbour", "neighbor", "next door",
                     "fence post", "fence posts", "gate post", "post hole", "posts go",
                     # the height limit is the height row's: "can i put up a fence 2 metres high"
                     # was the build card once "put up a fence" was in the key above
                     "metres high", "metre high", "metres tall", "metre tall", "feet high",
                     "foot high", "planning permission", "permission", "allowed", "legal",
                     "how deep", "depth", "how far apart", "spacing", "how thick", "what size",
                     "postcrete", "concrete a post", "concrete it in", "bags of")),
        entry("fence-owner",
              (("who owns", "whose", "who is responsible", "who pays", "who has to pay",
                "who should pay", "my neighbour", "my neighbor", "neighbour says", "neighbor says",
                "neighbours fence", "neighbor's fence", "neighbour's fence", "neighbours fence",
                "next door say", "boundary", "deeds", "title plan", "t mark", "shared fence",
                "pay half", "half the cost", "have to pay", "split the cost", "go halves",
                "shared boundary",
                "took the fence down", "removed the fence", "replaced the fence", "put up a fence"),
               ("fence", "fencing", "fence panels", "fence panel", "boundary fence", "wall")),
              "Who owns a boundary fence is in the deeds, not in who mows the grass: the title plan "
              "marks the owner's side with a T, and where there is no mark it is usually shared, each "
              "side looking after the fence on their own side. Almost no property has to have a fence "
              "at all, so a neighbour taking down one that is theirs is usually within their rights. "
              "If it is theirs you cannot paint it, fix your side of it or hang anything on it without "
              "asking, and if it is shared the fair split is half the cost each.",
              ask=("fence", "fencing", "fence panel", "fence panels", "boundary fence", "hedge",
                   "wall"),
              # "do i have to pay half the fence" is the ownership question, and cost-fence would
              # otherwise answer it with a price per metre
              bias=1,
              avoid=NOT_A_FENCE_JOB + ("how much", "cost", "costs", "price", "quote", "blew down", "blown down",
                     "blew out", "blown out", "came off", "fell down", "repair", "fix it",
                     "replace", "treat", "treating", "stain", "staining", "paint it", "painting",
                     "preserver", "creosote", "rotten", "rotted", "wobbly", "loose",
                     "how tall", "how high", "tall can", "high can", "planning",
                     # the height limit can be said in metres or feet, and "can i put up a fence 2
                     # metres high" was the deeds answer for want of a number
                     "metres high", "metre high", "metres tall", "metre tall", "feet high",
                     "foot high", "ft high", "m high", "2m", "6ft", "planning permission",
                     "can i put up a fence", "can i build a fence", "am i allowed",
                     # the build question ("where do I dig, what order") is the fence-build row's;
                     # these keep the deeds answer for who owns, who pays and who took it down
                     "how do i put up", "how to put up", "how do i build", "how to build",
                     "how do i fence", "fence my garden", "where do i start",
                     "how long does it take", "how long to put up", "what do i need to put up",
                          "put up a fence myself", "put a fence up myself", "erect a fence",
                     "install a fence", "do it myself", "how do i begin", "where do i begin",
                     # "my neighbour's fence is blocking my light" and "his wall is too high" ask
                     # what can be done about it, which is the council route, not the deeds
                     "blocking my light", "blocks my light", "blocking the light", "blocks the light",
                     "my light", "too tall", "too high", "overhanging", "overhangs", "branches")),
        # Light and overhanging branches are the neighbour question people actually have, and it is
        # not a fence: a hedge, a tree or a fence that blocks the light has its own route (the council
        # under the high-hedges rules), and cutting back what overhangs is a right with conditions.
        entry("neighbour-hedge-light",
              (("too tall", "too high", "blocking my light", "blocks my light", "blocking the "
                "light", "blocks the light", "blocking light", "blocks light", "block my light",
                "no light", "my light", "overhanging", "overhangs", "hanging over", "hangs over",
                "branches over", "branch over", "trees over",
                # not a bare "cut back": "the hedge needs cutting back" is the pruning question, and
                # the dispute reading needs a neighbour, a height or the light in the line
                "cut back over my", "cut over my", "cut my branches", "cut back my branches",
                # the commonest shape of the question names the branches and not the position:
                # "can i cut branches off my neighbours tree" was a search hedge
                "cut branches", "cut a branch", "cut back branches", "cut the branches",
                "cut back the branches", "trim branches", "trim the branches", "branches off",
                # not "hedge is": it is a fragment, not a boundary phrase, and it made every line
                # that says what the hedge is like ("my hedge is looking sorry for itself") a
                # neighbour dispute. The boundary reading needs a neighbour, a height or the light.
                "high hedge", "hedges", "complaining about", "complain about",
                "hedge too tall", "hedge too high"),
               ("hedge", "hedges", "tree", "trees", "branches", "branch", "fence", "fencing",
                "wall", "neighbour", "neighbours", "neighbour's", "neighbors", "next door",
                "next-door")),
              "A hedge or a wall that shuts out the light is the council's job, not a court's: if it "
              "is an evergreen hedge over 2 metres and it blocks your light, you can complain to the "
              "council under the high-hedges rules, but only after you have written to the neighbour "
              "and kept a copy, and there is a fee of a few hundred pounds. Branches that overhang "
              "your side you can cut back to the boundary without asking, though you must offer the "
              "cuttings back and you cannot lean into their garden to do it, and you must not cut a "
              "tree under a tree preservation order or in a conservation area without checking with "
              "the council first. Right to light through an old window is a separate legal claim and "
              "a solicitor's job.",
              ask=("hedge", "hedges", "tree", "trees", "branches", "branch", "fence", "fencing",
                   "wall"),
              avoid=NOT_A_FENCE_JOB + ("how much", "cost", "costs", "price", "quote", "blew down", "blown down",
                     "blew out", "blown out", "repair", "fix", "replace", "treat", "treating",
                     "stain", "staining", "paint", "painting", "creosote", "rotten", "rotted",
                     "wobbly", "loose", "how tall can", "how high can", "planning permission for",
                     "who owns", "whose", "deeds", "fell down", "died", "dead", "dying", "diseased",
                     "looks dead", "brown", "not growing", "bare patch",
                     # a plant in a bad way is the hedge-care answer, not the council's: the state
                     # of the hedge is the subject and there is no dispute in the line
                     "patchy", "yellow", "yellowing", "yellowed", "gone brown", "brown at the base",
                     "brown at the bottom", "bare at the bottom", "bare at the base", "thin",
                     "sparse", "gaps", "gap", "looking sorry", "sorry for itself", "looks ill",
                     "looks bad", "looks sad", "bald", "shrubs", "shrub", "feed", "feeding",
                     "fertiliser", "fertilizer", "compost", "mulch", "watering", "water it",
                     "poison", "fruit", "apple", "pear", "plum", "cherry tree", "prune",
                     "pruning", "plant a tree", "plant a hedge", "how do i trim")),
        # "trapped in my job" is a feeling, so the lock is what counts here, not the place.
        entry("locked-in-a-room", (("locked in", "locked inside", "shut in", "stuck inside"),
                                   ("flat", "house", "home", "room", "bedroom", "bathroom",
                                    "toilet", "garage", "shed", "cellar", "loft", "hallway")),
              "If a child is shut in, ring 999 straight away and stay on the line. Otherwise get a "
              "window open and shout to a neighbour, or ring someone who has a spare key - "
              "someone is nearly always in. If nobody is, the landlord or letting agent first, then "
              "a locksmith who quotes on the phone; a stuck lock is worth one firm push with the "
              "handle held up before you pay anyone. If there is fire, smoke or someone unwell, "
              "ring 999 and say you are locked in.",
              bias=1),
        entry("draughts", (("draught", "drafts", "draughts", "cold air", "under the door",
                            "under the front door", "gap under"),
                           ("door", "window", "cold", "stop", "keep", "front")),
              "Stick a brush strip or foam seal round the doors and windows, and put a weighted "
              "draught excluder at the bottom of the front door. A chimney balloon and a letterbox "
              "flap are cheap and stop the worst of it; seal up the gaps before spending money on "
              "heating."),

        entry("door-banging", (("door", "doors", "gate"),
                               ("banging", "bangs", "bang", "slamming", "slams", "slam", "rattling",
                                "rattles", "rattle", "wind", "windy", "shutting", "swinging")),
              "A door that bangs is a latch that isn't holding or a gap that lets the wind push it: "
              "check the strike plate first — a card's thickness of movement is enough, and moving it "
              "2mm further in with a chisel or a file fixes most of them. If it still swings, a hook "
              "and eye or a magnetic catch holds it open or shut, and a foam strip on the stop takes "
              "the noise out.",
              # "a cupboard door" and "the kitchen door" bang too, but not from the wind: the
              # strike plate answer is about a room door in a draught, so a cabinet that will not
              # stay shut goes to whatever cabinet entry fits, and never to the wind.
              # A car door that is frozen shut is a different job with a different answer, and the
              # key word "shutting" alone was enough to take it: cars.py has that entry.
              avoid=("frozen", "freezing", "froze", "iced", "ice", "frost", "car door", "car doors",
                     "stuck shut",
                     "paint", "painting", "sticking", "creaking", "hinge", "hinges", "lock", "key",
                     "keys", "handle", "front door lock", "burglar", "shed", "garage door",
                     "cupboard", "cupboards", "cabinet", "cabinets", "wardrobe", "wardrobes",
                     "kitchen", "kitchen door", "drawer", "drawers",
                     # the door of an appliance is never the door in the wind
                     ) + APPLIANCE_DOOR_WORDS + (

                     # a finger caught in a door is the black-nail answer, not a latch: the nail is
                     # the subject and "slammed" only says how it happened
                     "nail", "nails", "fingernail", "fingernails", "toenail", "toenails", "finger",
                     "fingers", "thumb", "toe", "toes", "hand", "jammed",
                     # a person shutting a door in a temper is the end of a row, and the latch
                     # answer was given to "he slammed the door" two turns after one
                     "slammed the door", "slams the door", "door on me", "door in my face")),

        # --- moving in ----------------------------------------------------------

        # A move that has not happened yet and is about too much stuff is a packing plan, not a
        # question about what the van costs. The clutter words here are chosen so they cannot
        # reshuffle the rest of the base: lookup._rank gives a bonus to a key word only one entry
        # uses, and "stuff" (used only by chicken-stuffed) turned "And if I stuff it?" into the
        # plain chicken answer when I first keyed this with it.
        # The first group is the phrase people say, not the bare verb: "keep moving" and "lifting
        # boxes" are a bad back, and "moving" alone is in every line about a new job, a new city or
        # a new phone. "pack" and "moving house" are the words that only appear in a move.
        # An office, a shop or a studio is a move too: the boxes and the kettle for the first night
        # are the same job, so the workplace phrases are keys and only the bare verb stays out.
        entry("moving-pack", (("move house", "moving house", "moving home", "move home",
                               "moving flat", "move flat", "moving out", "move out",
                               "moving in", "move in", "for moving", "before moving",
                               "moving office", "move office", "moving offices", "move offices",
                               "office move", "moving the office", "moving shop", "moving studio",
                               # "too much stuff to move" names the move after the stuff, with no
                               # "moving" in it: the infinitive is the phrase, and the second key
                               # group still has to be about the load, so "i want to move" passes.
                               "to move", "to be moved", "to move house",
                               "pack", "packing", "packed", "unpack", "unpacking"),
                              ("too much", "so much", "lots", "loads", "plenty", "things",
                               "boxes", "clutter")),
              "Pack what you use least first - books, spare bedding, the cupboard under the stairs - "
              "and keep a 'first night' box out of the van: kettle, mugs, chargers, loo roll, bedding "
              "and a change of clothes. Label boxes by room, do one room an evening for the last "
              "three weeks, and get rid of anything you have not touched in a year rather than "
              "paying to move it.",
              avoid=BODY_WORDS),

        entry("moving-cheap", (("move", "moving", "moved", "removals", "man with a van"),
                               ("cheap", "cheaper", "cheapest", "cheaply", "cost", "costly",
                                "price", "prices", "pricey", "expensive", "budget", "hire", "van",
                                "money", "save", "afford")),
              ("For one sofa and a bed, hire a man with a van for a couple of hours or borrow a van and "
               "two friends; book the van for the whole morning rather than by the hour. Measure the "
               "doorways and the stairwell first, because a sofa that doesn't fit costs you the day."),
              # "house", "flat" and "moving" alone are everyday words: without these avoids the van
              # advice answered "how do I tell my kids we're moving house", "how do I register with a
              # doctor after moving house" and "do I need to tell the council when I move out".
              avoid=("stressed", "stress", "worried", "nervous", "anxious", "sad", "upset", "feeling",
                     "kids", "children", "child", "tell", "doctor", "gp", "dentist", "council",
                     "council tax", "school", "care home", "piano", "landlord", "deposit", "tenancy",
                     "register")),
        entry("moving-admin",
              (("move", "moving", "moved", "moving house", "moving flat", "new address", "new house",
                "new flat", "move house", "move out"),
               ("council", "council tax", "doctor", "gp", "dentist", "school", "register", "utilities",
                "redirect", "meter", "tenancy", "admin", "paperwork", "notify", "need to do",
                "tell", "what do i need", "checklist")),
              ("Do the paper trail in one afternoon: tell the council tax office for the old and the "
               "new address, register with a GP near the new place and ask for your notes to move with "
               "you, and read the meters on the day you leave and arrive. Set up a Royal Mail redirect "
               "for three months, because it catches the accounts you forget, and take photos of the "
               "meters as proof."),
              # "moved" and "move" are in every line about a new phone, a new city or a new job, so
              # this entry only answers when the line names the paperwork as well.
              # "what do i need to buy first" is the first-night box, not the paper trail
              avoid=("buy", "first night", "sofa", "van", "cheap", "cost", "price", "hire", "removal",
                     "phone", "laptop",
                     # telling the landlord is the notice letter, not the paper trail: "when
                     # should i tell my landlord im moving out" got the GP-and-meters list
                     "tell my landlord", "tell the landlord", "my landlord", "the landlord",
                     "landlord", "landlady", "letting agent", "notice period", "give notice",
                     "who do i tell about my new address", "who do i tell about my address",
                     "who do i tell about my new adress", "who do i tell about my new place",
                     # "change the name on my council tax bill after my husband moved out" is the bill,
                     # not the move: the name and the discount are the question, and the paper-trail
                     # list buries them.
                     "change the name", "name on", "in my name", "not on the bill",
                     "computer", "city", "job", "office", "desk", "company", "files", "apps",
                     "contacts", "care home", "piano", "abroad", "country", "kids", "kid",
                     "children", "child", "son", "daughter", "explain", "upset",
                     # a rescheduled appointment is not a house move: "the doctor appointment got
                     # moved" matched "moved" and "doctor", so the paper-trail list came back
                     "appointment", "appointments", "rescheduled", "postponed",
                     "brought forward", "cancelled", "canceled", "moved to", "moved it",
                     # a moved shift is not a moved house: "my boss moved my shifts again and i
                     # cant do the school run" matched "moved" and "school" and got the
                     # paper-trail list, where the rota card is the answer. Work words stand
                     # this entry down.
                     "shift", "shifts", "rota", "boss", "manager", "overtime")),
        # "how do I pack for a house move" was a shrug and "no idea where to begin the packing" got
        # the weekend-away list, because packing-weekend names a weekend and packing. This is the
        # move's own packing: what to put in first, what goes in the first-night box, what to get rid
        # of rather than pay to move. moving-pack already answers the clutter lines ("too much stuff")
        # and a bare date is news, so this one asks for the packing itself.
        # The bare verb is not a key here either: "keep moving" with "boxes" is a bad back, so the
        # first group is the phrases that only appear in a move.
        entry("moving-packing-plan",
              (("move house", "moving house", "moving flat", "move flat", "house move", "moving home",
                "move home", "moving out", "moving in", "removals", "before moving", "when moving",
                "after moving", "moving office", "move office", "moving offices", "move offices",
                "office move", "moving the office", "moving shop", "moving studio",
                # "pack for a move" is the planning question and names the move without a noun after
                # it, so the article forms are keys too. They carry no meaning alone, and the second
                # group still has to be about packing, so "its your move" passes.
                "for a move", "a house move", "the move", "for the move"),
               ("packing", "pack", "packed", "boxes", "box", "declutter", "unpack")),
              # The fuller plan wins a line that fits both: "how do i pack boxes for moving house" is
              # the planning question, not the short "too much stuff" answer.
              bias=1,
              reply=("Start with one room and one deadline: pack the things you use least first, label every "
               "box by room and keep one box for the first night - bedding, toilet roll, kettle, mugs, "
               "chargers, a torch and any medication. Anything you have not used in a year, sell, "
               "donate or bin it now rather than paying to move it; a bag a day from the back of a "
               "cupboard gets rid of most of it. Book the van for the whole morning rather than by the "
               "hour, and measure the doorways and stairwell before the day. As a guide, a one-bed "
               "flat is about twenty boxes and a couple of weekends of packing; a three-bed house is "
               "two or three times that."),
              # "where do I even start" and "how do I plan" belong to plans.move-house-plan, and a
              # feeling about a move is not a packing question.
              avoid=("council", "council tax", "doctor", "gp", "dentist", "register", "tenancy",
                     "deposit", "landlord", "kids", "children", "child", "son", "daughter",
                     "piano", "abroad", "country", "city", "job", "phone", "laptop", "computer",
                     "contacts", "apps", "care home", "pet", "cat", "dog", "trip", "holiday",
                     "flight", "hotel", "camping", "suitcase", "weekend away",
                     "start", "started", "starting", "plan", "planning", "organise", "organize",
                     "organised", "sorted", "checklist", "advice", "break up", "breakup",
                     "girlfriend", "boyfriend", "ex", "stressed", "stress", "worried", "nervous",
                     "anxious", "sad", "upset", "feeling", "overwhelmed", "exhausted", "dreading",
                     "manager", "boss", "meeting",
                     # crockery named in the line wants the box-by-box answer, not the plan:
                     # "how do i pack glasses for a house move" is about the glasses
                     "glasses", "plates", "mugs", "crockery", "glassware", "china", "bowls")
              + BODY_WORDS),
        # The packing lines that never say "move": "how long does it take to pack a 1 bed flat", "any
        # tips for packing a house". moving-packing-plan keys on the move, so these fell to a hedge.
        # Packing plus a home is the same question, and the trip lines (suitcase, holiday, weekend
        # away) stay with the travel packing entries.
        entry("packing-time",
              (("pack", "packing", "packed", "boxes"),
               ("flat", "house", "home", "1 bed", "one bed", "2 bed", "two bed",
                "how long", "how many boxes", "bedsit", "moving day")),
              ("Pack what you use least first and give it a date: a one-bed flat is about twenty boxes "
               "and two weekends if you do it evenings and one weekend if you take a day off; a "
               "three-bed house is two or three times that. Every box labelled by the room it goes to, "
               "one first-night box kept out of the van, and anything you have not used in a year "
               "goes to the charity shop rather than into a box."),
              # A statement about packing ("i'm packing up my flat next week") is news and the chat
              # module acks it, so the advice only comes when the line asks something.
              ask=("how long", "how many", "tips", "advice", "how much", "best way", "how do i",
                   "where do i", "what do i need", "should i"),
              avoid=("suitcase", "holiday", "trip", "flight", "airport", "camping", "abroad",
                     "weekend away", "hand luggage", "carry on", "school bag", "nappy bag",
                     "council", "council tax", "doctor", "gp", "dentist", "register", "tenancy",
                     "deposit", "landlord", "kids", "children", "child", "piano", "van", "cost",
                     "price", "cheap", "removal", "stressed", "stress", "worried", "nervous",
                     "anxious", "sad", "upset", "feeling", "overwhelmed", "dreading",
                     # "flat pack" folds to "flat" + "pack", so building a wardrobe got the
                     # moving-boxes answer: the furniture words are not a house being packed
                     "flat pack", "flat-pack", "furniture", "assemble", "assembling",
                     "wardrobe", "sofa", "mattress", "bookcase", "bed frame", "dining table",
                     # a line that names the breakables wants packing-breakables, not a plan
                     "glasses", "plates", "mugs", "crockery", "glassware", "china", "bowls",
                     "wine glasses", "tumblers", "ornaments", "vases")
              + BODY_WORDS),
        # "how do i pack plates so they dont break" got the weekend-away list, because a box of
        # plates is a packing question and the travel entry also keys on "break". The breakables are
        # the one part of packing with a right answer, so they get their own.
        entry("packing-breakables",
              (("pack", "packing", "packed", "wrap", "wrapping", "box up", "boxes", "box"),
               ("plates", "glasses", "crockery", "mugs", "dishes", "bowls", "china", "fragile",
                "wine glasses", "ornaments", "vases", "picture frames", "mirrors", "tumblers")),
              ("Wrap each plate in paper or a tea towel and stand it on its edge in the box, like "
               "records in a crate, never stacked flat: that is what stops them cracking. A crumpled "
               "paper or towel cushion in the bottom and on top, small boxes that one person can lift, "
               "and FRAGILE written on the sides. Glasses and mugs go upright with paper pushed inside, "
               "a mug handle never takes the weight, and wine glasses travel best one inside a sock. A mirror "
               "or a framed picture travels standing on its edge too, with card on the corners and "
               "tape across the glass in an X so a crack stays put."),
              # A statement ("i'm packing the plates tonight") is news, and a broken plate is not a
              # packing question: the advice only comes when the line asks how.
              ask=("how", "what", "tips", "advice", "best way", "should i", "so they dont break",
                   "so they don't break", "wont break", "won't break", "without breaking",
                   "not break", "safely"),
              # A trip is a suitcase, not a box: "what should i pack for a weekend away with my
              # glasses" was the travel list, and it should stay the travel list.
              avoid=("spectacles", "contact lenses", "contact lens", "lenses", "prescription",
                     "glasses prescription", "eyes", "sight",
                     "weekend", "weekend away", "trip", "holiday", "holidays", "abroad", "flight",
                     "hotel", "suitcase", "carry on", "hand luggage", "days")),
        # The kitchen is the room nobody knows where to start with, and the packing entries had
        # no line for it: "how do i pack the kitchen" was the cleaning routine (the room plus the
        # bare "how"), and in a move chat "and the kitchen stuff" was three quotes and a payment
        # schedule from the renovation plan. Crockery and glasses keep packing-breakables.
        entry("packing-a-kitchen",
              (("kitchen", "kitchens", "kitchen stuff", "kitchen things", "kitchen cupboards",
                "kitchen drawers", "cupboards in the kitchen"),
               # the packing words are the whole key on this side: a looser group ("how",
               # "start", "first", "what about") let the carried words of a move chat pull this
               # card onto "only in the kitchen", "what about the ceiling" and "theyre melamine".
               ("pack", "packs", "packing", "packed", "box", "boxes", "box up", "pack up",
                "packing up",
                # the room named with "stuff" is the kitchen in a move chat: "and the kitchen
                # stuff" after a packing question is what has to go in the boxes, and it was
                # three quotes and a payment schedule from the renovation plan. Shopping for a
                # kitchen is fenced below, and so are the words that name a job instead.
                # "things" is not a key: "what new thing should i try in the kitchen" is a
                # cooking question and the boxes answered it.
                "stuff", "the rest")),
              ("Leave the kitchen to the second-to-last day, because it is the room you still "
               "need, and keep one box open until the morning: kettle, two mugs, tea, a tea towel, "
               "washing-up liquid, a sharp knife, a tin opener and a corkscrew. Do it one cupboard "
               "at a time and set a box down on the counter as you empty it, so nothing gets "
               "carried across the room; plates and glasses go on edge in small boxes with a towel "
               "round them, never stacked flat. Anything out of date or never used goes in the bin "
               "bag rather than the van, the fridge wants emptied, defrosted and dried out a day "
               "before, and it travels upright. Write KITCHEN - OPEN FIRST on the boxes you will "
               "want that night, and put the food and the cleaning stuff in their own two boxes so "
               "you are not hunting for the bin bags."),
              # a kitchen being cleaned, planned, fitted or painted is another row's line, and so
              # is shopping for one: only the packing words reach this one.
              guard=_the_kitchen_stuff_is_a_take_up,
              avoid=("unpack", "unpacking", "unpacked",
                     "clean", "cleaning", "cleaned", "grease", "greasy", "smell", "smells",
                     "oven", "fridge", "freezer", "hob", "cooker", "microwave", "bin", "dishwasher",
                     "leak", "tap", "taps", "mould", "limescale", "floor", "floors", "wall", "walls",
                     "paint", "painting", "decorate", "plan", "planning", "design", "layout",
                     "fit", "fitted", "fitting", "install", "installing", "renovate", "refurb",
                     "quote", "quotes", "builder", "extension", "buy", "buying", "shop", "shopping",
                     "cheap", "cheapest", "price", "prices", "cost", "where can i get",
                     "plates", "glasses", "crockery", "china", "bowls", "mugs", "wine glasses")),
        entry("moving-with-kids",
              (("move", "moving", "moved", "moving house", "house move", "new house", "new home"),
               ("kids", "kid", "children", "child", "son", "daughter", "teenager", "toddler",
                # a baby is a child, and "moving house with a baby" reached nothing at all
                # because the word for the smallest one was not in the group
                "baby", "babies",
                "tell", "explain", "upset", "worried", "nervous", "sad", "cope", "settle")),
              ("Tell them as soon as it is certain, and keep it concrete: which room is theirs, where "
               "the school or nursery is, and what stays the same. Let them pack a box of their own "
               "things and choose the paint or the posters, because control is what they are missing. "
               "Say goodbye to the old place properly on the last day, and expect a wobble a few weeks "
               "in, when the novelty wears off and they miss their friends."),
              # A child who is leaving home is not a household packing up: "my daughter wants to
              # move out" was told "tell them as soon as it is certain... which room is theirs",
              # and "my son has moved out and i am bereft" the same. family.py answers the leaving.
              # A feeling in the speaker's own line is not a question about telling a child, and
              # that is a guard rather than more avoid words: see `_a_child_or_a_telling`.
              guard=_a_child_or_a_telling,
              avoid=("council", "council tax", "gp", "doctor", "dentist", "register", "piano",
                     "van", "cheap", "cost", "price", "abroad", "country", "care home",
                     "move out", "left home", "has left", "wants to move",
                     # the same care home without the word "care": "my mum moved into a home
                     # last month" was told to put a kettle and toilet roll in a box.
                     "a home", "the home", "nursing home", "residential home", "home too")),
        # A piano is the one thing that a hired van and two friends ruins, and its move has its own
        # answer rather than the sofa-and-bed line.
        entry("piano-move",
              (("piano",), ("move", "moving", "moved", "cost", "hire", "removers", "stairs",
                            "upstairs", "quote")),
              ("Hire a piano remover rather than a general removal firm: it takes two people who know "
               "the handholds, a proper trolley and straps, and a knocked soundboard is a repair bill. "
               "Keep it upright and never on its side, take the legs off an upright only if the maker's "
               "instructions say so, and let it settle in the new room for a few weeks before it is "
               "tuned. Stairs and narrow turns are what make a quote go up, so send a photo of the "
               "route when you ask for one."),
              avoid=("learn", "lessons", "practise", "practice", "tune", "buy", "worth", "grade")),
        entry("first-night", (("first night", "moving in", "moving into", "new flat", "first flat"),
                              # "what should i keep out for the first night" asks for this box in
                              # the words of someone standing in a hallway of boxes, and "should"
                              # alone is not the ask: it was the car's night-driving row on that
                              # line, and it pulled the box onto "what should i sort out first"
                              # in the middle of a should-we-move chat. The words below say the
                              # keeping-out, which is what the question is.
                              ("need", "do", "before", "buy", "keep out", "keep aside",
                               "keep back", "put aside", "put by", "pack last", "open first",
                               "have ready", "ready", "get ready")),
              FIRST_NIGHT_BOX,
              # Getting the furniture in is a different job from the first night in it: "how do I move
              # my sofa to my new flat" is a stairs-and-doorways question, and the kettle-and-toilet-roll
              # box cannot help with it. These words send that line to the honest hedge instead, which
              # is what main gives for "how do I move a sofa".
              avoid=("stressed", "stress", "worried", "nervous", "anxious", "sad", "upset", "feeling",
                     "sofa", "couch", "settee", "bed", "mattress", "wardrobe", "table", "chairs",
                     "fridge", "freezer", "piano", "van", "removals", "removal", "hire", "hiring",
                     "stairs", "upstairs", "doorways", "doors", "carry", "carrying", "lifting",
                     "move my", "moving my", "shift my")),
        entry("just-moved-in",
              # "just moved" and nothing looser: "we're moving into our first flat on Saturday" is
              # news - the chat module acks it and the first-night question comes as its own turn -
              # and the loose forms of "moving" and "moved" are the same word, so only the word
              # people say once they are in stays here. It is the same paragraph as first-night, not
              # a second copy of it, so the two cannot drift apart.
              # "we moved in last week" is the same arrival as "we just moved in": people say it in
              # the past tense with no "just", so the verb carries it and the time words below say
              # the move has already happened.
              (("just moved", "moved in", "moved into"),
               ("new flat", "new house", "new home", "new place", "first flat", "our own place",
                "moved in", "moved into", "last week", "last weekend", "last month", "this week",
                "this month")),
              FIRST_NIGHT_BOX,
              # "just moved into a care home, i feel guilty" is about the guilt, and the paperwork
              # lines are moving-admin's: this entry is only the arrival itself.
              # A tie with the paperwork list used to go to the paperwork: the arrival is the
              # question, so it wins the tie.
              bias=1,
              avoid=("guilty", "care home", "nursing home", "a home", "the home", "home too",
                     "residential home", "stressed", "stress", "worried",
                     "nervous", "anxious", "sad", "upset", "feeling", "kids", "children", "child",
                     "council", "council tax", "doctor", "gp", "dentist", "school", "landlord",
                     "deposit", "tenancy", "address", "register", "job", "city", "country", "abroad",
                     # an arrival that already has a problem is that problem's question
                     "damp", "mould", "mold", "leak", "piano", "boiler", "heating", "hot water",
                     "radiator", "broken", "repair", "washing machine", "fridge", "noise", "noisy",
                     "neighbour", "neighbours", "cold",
                     # a move still to come, or one made with someone, is news and a chat, not the
                     # list of what to put in the box tonight
                     "tomorrow", "next week", "next month", "on saturday", "on sunday",
                     "with my", "boyfriend", "girlfriend", "partner", "husband", "wife", "parents",
                     "flatmate", "housemate", "together"),
              # "my bowels havent moved in 4 days" carries `moved in` and was told to buy toilet roll
              # and photograph the meters: a bowel that has not moved is the stomach's line, and the
              # reading says so (see `the_stomach_is_what_it_is_about`)
              guard=lambda understood: not the_stomach_is_what_it_is_about(understood)),
        # --- a home in hot weather ---------------------------------------------
        # Keeping the heat out of a room is one job and sleeping in it is another, so they sit apart
        # from fan-vs-aircon (which is a cost question) and from nature.heatwave (which is the public
        # health line: drink water, check on neighbours). The appliances, pets and people with their
        # own answers are avoided, because a fridge that is not cool and a baby in the heat are not
        # this entry's question.
        entry("keep-room-cool",
              (("house", "home", "flat", "room", "bedroom", "living room", "kitchen", "windows",
                "heatwave", "heat wave", "heat", "summer", "sun", "indoors", "inside", "upstairs",
                "downstairs",
                # The room they are standing in, said without naming it, and the workplace, which
                # is the same question about the same four walls: "its boiling in this office" was
                # a shrug until "office" was here, and "its like a sauna in here" with it.
                "office", "in here", "in this room", "this room", "this place", "my place",
                "our place"),
               ("cool", "cooler", "cooling", "cool down", "keep cool", "hot", "boiling", "stuffy",
                "stifling", "roasting", "shade", "sun", "keep the sun out", "windows",
                # "the flat gets baking in summer" is a home in a heatwave: without "baking" the
                # line reached the flat-bake card, and once that stands down it gets a shrug.
                "baking", "baking hot", "an oven",
                # Heat is a picture as often as it is a word: "its like a sauna in here", "my
                # bedroom is like an oven", "its stifling in here" and "im roasting in here" all
                # fell to the floor because a room is never named in them. The picture is the
                # same claim as "the room is too hot", so the row reads it as one.
                "sauna", "like a sauna", "like an oven", "like a greenhouse", "like a furnace",
                "sweltering", "melting", "boiling hot", "hot as an oven", "stifling hot",
                "a furnace", "furnace",
                # Keeping the heat out is the same job asked from the other side, and it was
                # read as a question about turning the heating ON: "how do i keep the heat out
                # in summer" got the 18C living-room setting and "how do i stop the sun heating
                # my flat" got the electric radiator.
                "keep the heat out", "heat out", "stop the sun", "sun heating", "block the sun",
                "the sun coming in", "sun comes in", "sun through")),
              ("Shut the windows and pull the curtains on the sunny side in the morning, then open "
               "everything wide once it is cooler outside than in, usually after 9pm. A fan in an open "
               "window pulling air through the flat beats one blowing at you. Keep the oven off and "
               "cook early, and put a bowl of water out if the air is dry."),
              # "heating" is not avoided: "heat" is one of its forms, so it would take every
              # heatwave line with it. Only the switched-on phrase goes.
              avoid=THE_APPLIANCE_ITSELF + ("hob", "boiler", "radiator", "heating on",
                     "radiators", "washing machine", "tumble dryer", "laptop", "computer", "pc",
                     "phone", "tablet", "car", "engine", "dog", "cat", "puppy", "kitten", "baby",
                     "babies", "toddler", "pregnant", "fan cheaper", "cheaper", "cost",
                     "electricity", "bill", "keep warm", "keep the house warm", "draught",
                     "draughts", "drink", "beer", "wine", "food", "milk", "leftovers",
                     # "i moved into a new flat and theres no hot water" is a boiler question
                     "hot water", "no water", "cold water", "shower", "bath", "immersion",
                     "heating on", "thermostat",
                     # a room with no window is its own answer, not the heatwave one
                     "no window", "no windows", "without a window", "windowless",
                     # building work on a window is not a way to keep a room cool
                     "bigger", "bigger window", "enlarge", "enlarging", "widen", "widening",
                     "larger", "new window", "window fitter", "glazier")),
        # A room with no window is asked about for the same two things every time - it is dark, and
        # the air sits still - and it was getting the keep-cool answer, because "room" is in that
        # row's key and "window" in its second group.
        entry("room-no-window",
              (("room", "bedroom", "living room", "kitchen", "hallway", "office", "study", "flat",
                "cellar", "basement"),
               ("no window", "no windows", "without a window", "without windows", "windowless",
                "no natural light", "no light", "get light", "air", "ventilation", "ventilate",
                "airflow", "stuffy", "damp")),
              ("Light it in layers and move the air with a fan. One bright lamp in each corner beats a "
               "single ceiling light, an LED around 4000K reads closest to daylight, and a mirror or "
               "pale wall opposite the door bounces it about. For the air, prop the door open with a "
               "fan pulling air through to another room, or run a small dehumidifier: a windowless "
               "room goes damp before it goes stuffy."),
              avoid=("mould", "mold", "mildew", "condensation", "cool", "cooler", "hot", "heatwave",
                     "heat", "radiator", "boiler", "heating", "paint", "curtain",
                     "curtains", "blind", "blinds", "bigger", "enlarge", "widen", "door", "lock",
                     # a room that smells is the damp answer: "my basement smells damp" is not a
                     # question about lamps and airflow, though it carries the word damp
                     "smell", "smells", "smelling", "smelly", "musty", "whiff", "reek", "stinks")),
        # "my living room needs a bigger window" is not a cleaning or a cooling line: it is building
        # work, and the answer is who does it and what it needs before anyone quotes.
        entry("window-bigger",
              (("window", "windows", "window opening"),
               ("bigger", "enlarge", "enlarging", "enlarged", "widen", "widening", "larger",
                "more light", "knock through", "new window", "replace the window",
                "replacement window", "big window")),
              ("Widening a window opening is a builder's job, not a window fitter's: taking out "
               "brickwork under a new lintel is structural, where a swap of the same size is a fitter's "
               "morning. Ask a builder to price it, and a structural engineer if the wall carries the "
               "floor above; in a flat or a conservation area you may need permission too. Cheaper "
               "first: a mirror opposite the window and paler walls."),
              avoid=("curtain", "curtains", "blind", "blinds", "draught", "drafts", "draft",
                     "measure", "measuring", "clean", "cleaner", "cleaning", "wash", "replace the "
                     "glass", "cracked", "broken", "stuck", "leaking", "condensation", "no window")),
        # A window painted shut, an old sash that will not budge and a frame swollen after rain are
        # one question - the window will not open - and nothing answered it: the door row wants a
        # door, so these lines fell to "say more".
        entry("window-wont-open",
              (("window", "windows", "sash window", "sash", "casement", "frame", "upvc"),
               # "sticking" and "hard to open" are how the same fault is described when nothing has
               # jammed yet: "how do i fix a sticking window" scored here on nothing and got a
               # glazier's quote for broken glass, and then a door-hinge card for a creaking door.
               ("wont open", "won't open", "will not open", "cant open", "can't open", "cannot open",
                # "painted shut" and "painted over", but not a bare "painted": painting a window is
                # the painting rows' line, and "how do i paint a sash window" was a sash fault
                "painted shut", "painted over", "stuck", "stuck shut", "jammed", "seized",
                "swollen", "swelled", "warped", "budge", "wont move", "won't move", "wont shut",
                "won't shut", "wont close", "won't close", "sticking", "sticks", "doesnt close",
                "doesn't close", "hard to open", "hard to close", "hard to shut", "easier to open",
                "rubs", "dragging", "stiff")),
              ("Run a knife round the join first, because paint gluing the frame to the sill is the "
               "usual cause: score the line all the way round, then press on the frame and lift the "
               "handle. If it is a sash, check the cords - a snapped cord drops the weights and the "
               "window wedges. A tap with the heel of your hand and a dry bar of soap on the runners "
               "frees most of the rest."),
              avoid=("door", "doors", "windscreen", "car", "clean", "cleaning", "cleaner", "wash",
                     "condensation", "draught", "draft", "drafts", "leaking", "leak", "cost", "price",
                     "replace", "double glazing", "curtain", "curtains", "blind", "blinds", "bigger",
                     "widen", "enlarge", "no window", "no windows", "storage",
                     # and painting a window frame is the painting rows' line, not a sash fault's
                     "paint a window", "painting a window", "paint my window", "paint the window",
                     "paint window", "painting the windows", "paint the windows", "repaint",
                     "painting a window frame", "paint a window frame", "brushes", "brush"),
              # the creaking-door row keys "sticking" and "window" both, so a window that sticks ties
              # it and loses on registry order: a window is this row's, and the hinge card is not.
              bias=2),
        entry("sleep-hot-night",
              (("sleep", "sleeping", "slept", "bed", "bedroom", "night"),
               ("hot", "heat", "heatwave", "heat wave", "warm", "sweating", "sticky", "sweaty",
                "cool", "cooler", "cooling", "cool down", "too hot")),
              ("Cool the room before you get in, not after: windows open and a fan on for half an hour, "
               "then a lukewarm shower and dry off properly. Cotton sheets, one light layer rather "
               "than a duvet, and a damp flannel on your neck or feet. Sweating is how your body dumps "
               "heat, so give it moving air instead of covering up."),
              avoid=("baby", "babies", "toddler", "child", "children", "dog", "cat", "puppy",
                     "kitten", "pregnant", "fridge", "freezer", "boiler", "radiator", "heating on",
                     "laptop", "phone", "computer", "car", "mattress", "buy", "best", "which",
                     "wake up", "waking", "woke", "nap", "nightmare", "dream", "snore",
                     "snoring", "teeth", "grind"),
              # "cool cool. anyway im off to bed" is chit-chat that happens to hold a "cool"
              # and a "bed", so this needs a real ask as well as the heat word.
              ask=("how", "what", "tips", "tip", "advice", "should", "can i", "can you", "help",
                   "too hot", "cant", "can't", "cannot", "struggling", "keep", "cool down")),
        # Half of the "my bed is uncomfortable" lines want a fix for tonight, not a shopping trip,
        # and they used to land on shopping.mattress-buy (which answers "what should i buy") or on
        # nothing at all. The comfort words are the keys and the buying words are in the avoid, so
        # "which mattress should i buy" still gets the buying answer.
        # A lumpy pillow is its own answer: "my pillow is lumpy" was reaching the mattress row on
        # "lumpy" and being told to price up a topper, which is not what a lumpy pillow wants.
        entry("lumpy-pillow",
              # `duvet` and `duvets` were here with bias=2 on the row, so "my duvet is lumpy" and "how
              # do i fluff up a lumpy duvet" got the pillow card, whose first move is "unzip it" -
              # advice for a pillowcase and not for a duvet. A duvet is `cleaning.bedding-life`'s
              # question, and its card has the tumble-on-low-with-dryer-balls answer already.
              (("pillow", "pillows", "pillowcase", "pillow case", "filling"),
               ("lumpy", "lumps", "bunched", "bunched up", "flat", "too flat", "saggy", "sags",
                "gone flat", "worn out", "old", "replace", "uncomfortable")),
              "A lumpy pillow has usually just bunched its filling: unzip it, pull the filling apart "
              "with your hands, shake it down to the corners and bash it flat. If it still lumps, or "
              "it folds in half and stays folded when you lay it on your arm, the filling has gone "
              "and a new one is the fix - hollowfibre costs about £10 to £25 and a pillow over two "
              "years old is usually past it. A duvet that has gone lumpy is the same job, and a wash "
              "on a hot cycle with two tennis balls in the tumble dryer evens the filling out again.",
              bias=2,
              # the bed under the pillow, the way to sleep and the state of the person are their own
              # answers; a hotel, a baby and a shop are other rows too
              avoid=("mattress", "mattresses", "topper", "bed frame", "sprung", "squeak", "hot",
                     "wash", "washing", "dryer", "smell", "smelly",
                     "sweat", "sweaty", "insomnia", "wake up", "waking up", "cant sleep",
                     "hotel", "baby", "babies", "toddler", "cot", "pram", "buy", "which",
                     "should i get", "look for", "best")),
        entry("bed-uncomfortable",
              (("bed", "beds", "mattress", "mattresses", "bedding"),
               ("uncomfortable", "too soft", "too hard", "too firm", "sagging", "sags",
                "sag", "dip", "dipped", "hurts", "hurt", "sore back", "stiff back", "wake up sore",
                "waking up sore", "bad back", "not comfortable", "kill my back", "kills my back",
                "topper", "springs")),
              ("Try a mattress topper before a new mattress. A 5cm memory-foam or latex one costs about "
               "£40 to £100 and softens a firm bed or fills the dip in a soft one. If the mattress is "
               "over eight years old, sagging in the middle or you can feel the springs, it is the "
               "mattress and a topper only postpones it. A slipped pillow under your knees takes the "
               "strain off a sore lower back, and a too-soft bed is worth trying with a board under it "
               "first."),
              # buying questions, cleaning and a hot night are other entries' business.
              # "can i fix it without buying a new one" is the fix question, so the buying words are
              # the phrases that ask what to buy, not the bare verb: bare "buy" also matched "buying"
              # and swallowed this entry's own deck line.
              avoid=("should i buy", "should i get", "to buy", "buy a new mattress", "buy a mattress",
                     "buy a new bed", "new mattress", "new bed", "cost", "price", "how much", "cheap", "cheaper",
                     "budget", "which", "choose", "choosing", "best", "shop", "deal", "sale",
                     # "what should i look for in a mattress" asks what to look for, whatever else
                     # the line says about a bad back: that is the buying answer.
                     "look for", "looking for", "recommend", "recommendation", "worth it", "review",
                     # a sore back is the back's own answer: "my bed is killing my back" asks what
                     # to do about the back first, and the bed card is only the bed half of it
                     "back pain", "my back hurts", "killing my back", "bad back pain",
                     "clean", "cleaning", "stain", "stains", "wash", "washing", "bedbugs", "bed bugs",
                     "hot", "heat", "sweating", "sweaty", "wet", "wee", "accident", "hotel",
                     "breakfast", "holiday", "baby", "babies", "toddler", "child", "my son",
                     "my daughter", "my dog", "the dog", "my cat", "the cat", "sick", "vomit",
                     "hospital", "care home")),
        entry("fan-vs-aircon",
              (("fan", "aircon", "air con", "air conditioning", "air conditioner"),
               ("cheaper", "cheap", "cost", "run", "running", "expensive", "electricity", "worth")),
              "A fan costs a penny or two an hour; a portable air conditioner is more like 30 to 50p, "
              "and a fitted one more again. A fan only cools you, not the room, so put it in front of "
              "an open window at night with another window open across the room. A bowl of ice in front "
              "of a fan helps in dry heat, not in humidity.",
              avoid=("laptop", "computer", "pc", "console", "playstation", "xbox", "car", "engine",
                     "oven", "extractor", "boiler", "server"),
              ask=("cheaper", "cheap", "cost", "expensive", "electricity", "air con", "aircon",
                   "air conditioning", "hot", "cool", "cooling", "heatwave", "summer", "worth")),
        # "Is it cheaper to run the dishwasher or wash by hand": any two things in RUNNING are
        # compared from that one table, and one thing named on its own gets its figure.
        # "how long do washing machines last": the lifespan table above, one row per appliance.
        # "years" on its own is not a key: "my tumble dryer is 9 years old" is the age said as
        # context for a fault, and it was claiming the lifespan answer.
        entry("appliance-life", (LIFE_NAMES, LIFE_ASK),
              _lifespan, ask=LIFE_ASK,
              # "what is the life expectancy of a tumble dryer" ties with explains.explain-tumble-dryer
              # at six: the machine and the ask score the same for both, and a tie goes to the earlier
              # entry, which is the mechanism. How long it lasts is this row's question and the
              # mechanism is not an answer to it, so the tie is broken here rather than by standing
              # every explanation down on the word "lifespan", which would leave a solar panel - not
              # in this table - with nothing. Four, because every explanation carries its own bias and
              # a rarity bonus for a name only it uses ("tumble", "dryer"): the tumble dryer's
              # explanation ranks 9 against this row's 8 at three and 6 at two, so three ties and the
              # registry order hands the line to the explanation. The other appliance-life row used to
              # carry this bias and win the tie; with the duplicate gone, it is this row's job.
              # A pan cooling before the washing-up is not a pan at the end of its life: "how long
              # should i cool a pan before washing" matched "frying pan" and "how long" here as well
              # as on the wash cycle.
              # "worth" on its own is the buying question ("is it worth it"), but it is also half
              # of "is it worth replacing", which is this row's own question: the bare word vetoed
              # the most common way people ask it, so only the buying sense is fenced now.
              avoid=LIFE_GUARD + JOB_GUARD + ("broken", "quote", "worth it", "worth buying",
                                              "worth the money", "worth paying", "cool", "cooling",
                                              "cool it", "cool the pan", "before washing",
                                              "washing it", "wash the pan", "before i wash"), bias=4),
        # "When should I replace my mattress" belongs to the years table above - it has the age
        # and the rule that says when the thing is finished - but its key is the lifespan
        # phrasing, so the replace question fell to shopping's mattress-buy and was told what to
        # look for in a shop. One row for the thing people ask this about: the name plus the
        # replace words, and the buying, cleaning and turning rows keep their own lines.
        entry("bedding-finished", (("mattress", "mattresses"),
                                   ("replace", "replacing", "replacement", "replaced",
                                    "when to replace", "time to replace", "new one",
                                    "need a new", "need a new one")),
              _lifespan, bias=2,
              # a purchase is shopping's, and a stain, a wash or a turn is the rows above
              avoid=("buy", "buying", "bought", "cost", "costs", "price", "prices", "cheap",
                     "cheaper", "budget", "spend", "shop", "shops", "store", "topper",
                     "protector", "clean", "cleaning", "wash", "washing", "stain", "stains",
                     "smell", "smells", "turn", "turning", "flip", "flipping", "rotate",
                     "rotating", "cover", "covers", "sheet", "sheets", "pillow", "pillows",
                     "duvet", "duvets",
                     # "i need a new mattress, how do i choose" was this row's lifespan answer,
                     # because "need a new" is its own ask and the pick was left in the words.
                     # Chosen is shopping's question (mattress-buy), and it reads the line for
                     # which one, so this row stands down for the choosing words.
                     "choose", "choosing", "chose", "pick", "picking", "which one",
                     "what should i look for", "how do i choose", "help me choose"),
              ask=("replace", "replacing", "replacement", "replaced", "when to", "new")),
        entry("running-cost", (RUNNING_WORDS, COST_WORDS), _running,
              avoid=("broken", "break", "repair", "install", "frost", "iced", "ice", "defrost",
                     # a repair is priced by the engineer, not by the unit of electricity: "how much
                     # does it cost to fix a washing machine" got the pence-per-cycle figure.
                     "fix", "fixing", "fixed", "mend", "mending", "engineer", "call out", "spare",
                     "won't", "wont", "doesn't", "doesnt", "does not", "stopped", "spin", "hair",
                     "smell", "smells", "leak", "noise", "noisy", "not working", "cold", "filter",
                     "clean", "car", "engine", "laptop", "phone", "tablet", "pc", "console",
                     "playstation", "xbox", "extractor", "buy", "buying", "getting",
                     # a service or a repair is a price, not a bill
                     "service", "servicing", "serviced", "repair",
                     # a thing swapped for another thing is priced fitted, not by the unit of
                     # electricity: "is replacing a bath with a shower expensive" got the pence
                     # for five minutes of hot water. The same holds for any swap - a boiler, a
                     # window, a shower - so it is one rule here rather than a word in each row.
                     "replace", "replaces", "replacing", "replaced", "replacement",
                     "swap", "swaps", "swap out", "swapping", "swapped", "rip out",
                     "ripping out", "fit a", "fitting a", "fitted a",
                     "get one", "worth getting", "cups", "water for", "fill", "best", "new",
                     # which one to buy is a shopping question: "what is a good cheap slow cooker"
                     # took "cheap" as the cost word and was told the pence per hour, when the
                     # buying row has the £30-against-£100 answer. "cost" and "cheaper" keep their
                     # own lines ("how much does it cost to run a slow cooker").
                     "good", "a good", "good cheap", "good and cheap", "recommend", "recommended",
                     "worth", "worth it", "which one", "which one to", "should i buy",
                     "should i get", "what to buy", "to buy",
                     # a fan against air con is a cooling question, and that entry has the tips
                     "air con", "aircon", "air conditioning", "air conditioner",
                     # the hour is the tariff row's question, not pence per cycle: "what is the
                     # cheapest time to put the washing machine on" was priced as a cycle instead.
                     "what time", "cheapest time", "time of day", "off peak", "off-peak",
                     "in the morning", "in the evening", "during the day",
                     # "is it cheaper to leave the heating on all day" is a habit question, not an
                     # hourly figure, and `heating-all-day` has the timer and the 18C setting.
                     # "leave on" does not catch "leave the heating on", because the thing being
                     # left sits between the two words, so the heating's own phrases are named too.
                     "leave on", "leaving on", "left on", "all day", "all the time", "overnight",
                     "leave the heating on", "leaving the heating on", "left the heating on",
                     "keep the heating on", "keeping the heating on", "heating on all day",
                     "heating on all the time", "heating on low", "heating on at night",
                     "timer", "timed", "thermostat", "flow temperature",
                     # a bath is also a city, a bath bomb and a bath mat, and a shower is weather
                     "hotel", "hotels", "bath bomb", "bath bombs", "bath mat", "bath mats",
                     "bath towel", "bath towels", "bird bath", "swim", "swimming", "baby", "babies",
                     "dog", "dogs", "cat", "cats"),
              ask=COST_WORDS, bias=2),
        entry("freezer-defrost",
              # a fridge that has iced up is the same defrost question: the drain-hole row stands
              # down on `ice on the walls` / `full of ice` now, so the fridge words have to be here
              # or the line falls through to a shrug
              (("freezer", "freezer drawer", "icebox", "fridge", "fridges", "refrigerator"),
               ("defrost", "defrosting", "ice", "icing", "iced", "frost", "frosting", "froze",
                "frozen", "icy", "thick", "needs")),
              "Defrost it when the ice is more than about 5mm thick: switch it off at the wall, move "
              "the food into a cool box, and leave bowls of hot water inside with the door shut. Budget "
              "two to three hours, or overnight leave it with the door open and towels down. Never "
              "chip at the ice with a knife, because a pierced pipe writes the freezer off. The "
              "reason is moist air getting in every time the door opens.",
              # "how do i stop my freezer frosting up" ties with the first aid for a machine that will
              # not start, which takes the word "stop": the ice is the subject of the line, so this
              # card goes first
              # "do you need to keep rice in the fridge" is a keeping question: "needs" matched
              # `needs`, and the food the line was about went out of it, so the answer was how to
              # defrost a freezer. A food *named* in the line stands this row down - named, not
              # the words `food` and `leftovers`, which turn up in the defrost questions themselves
              # ("why is there ice on the food in my freezer", "is my food ruined") and took the
              # ice away from the card that is about the ice.
              avoid=("rice", "pasta", "bread", "milk", "meat", "chicken", "eggs", "butter",
                     "cheese"),
              bias=2),

        # A freezer that needs defrosting is the row above. This is the other question: a fridge that
        # ices up when it is meant to look after itself, which is a fault with a cause. "my fridge is
        # icing up" was "Noted: your fridge is icing up" and "how do i stop my fridge icing up" was
        # the dead-appliance answer, so both shapes had nothing.
        entry("fridge-frost",
              (("fridge", "fridge freezer", "ice box", "freezer box", "freezer compartment"),
               ("frost", "frosts", "frosting", "frosted", "icing", "icing up", "ices up", "iced up",
                "ice", "icy", "ice building up", "build up of ice", "frozen up", "freezing up",
                "thick ice", "snow", "back wall", "back of the fridge", "icicles")),
              "Ice in a fridge that is meant to look after itself comes from one of three things: a "
              "door seal that no longer grips (shut a strip of paper in the door and pull - it should "
              "drag), the drain hole at the back of the fridge blocked so the water freezes there, or "
              "food pushed against the back wall. Fix the seal and clear the drain and the ice stops "
              "coming back. Get rid of what is there by defrosting it properly with the door open "
              "overnight, and never chip at it with a knife.",
              # the defrost row above, the water-in-the-bottom row, the smell and clean rows, and a
              # dead appliance are all other answers
              avoid=("defrost", "defrosting", "not cold", "warm", "noise", "noisy", "smell", "smells",
                     "clean", "cleaning", "repair", "replace", "buy", "cost", "broken", "dead",
                     "leaking", "drain hole", "water", "freezer", "chest freezer", "freezer drawer",
                     "temperature", "setting", "worth"),
              # the water-in-the-bottom row holds the drain hole, and it answered "ice on the back wall
              # of my fridge" first; the cause here is the same fault, so this one leans in
              bias=2),


        # "its a frost free one" and "how often should i defrost it" are the two follow-ups to the
        # defrost answer, and neither names the freezer, so neither reached it. The first was the
        # defrost instructions said back with "For a frost free one, the same:" in front of them,
        # which is the wrong way round - a frost-free freezer does its own defrosting, and one that
        # ices up has a seal or a vent letting warm air in. The second was the refreezing-the-food
        # rule, because the bare word "defrost" is enough for that row. Two rows, because they are
        # two different questions: whether to defrost at all, and how often.
        entry("frost-free-freezer",
              (("frost free", "frost-free", "frostfree", "no frost", "auto defrost", "auto-defrost",
                "self defrosting", "never needs defrosting"),
               ("freezer", "freezers", "icebox", "fridge freezer", "frost", "frosts", "frosting",
                "frosting up", "frosts up", "ice", "ices", "icing", "iced", "one", "it", "that",
                "needs", "defrost", "defrosting")),
              "A frost-free freezer never needs defrosting by hand: it clears its own frost, so ice "
              "building up means the door seal has gone or the vent behind it is blocked. Check the "
              "gasket all round the door with a sheet of paper (it should grip), and a new seal is a "
              "cheap fix.",
              # the buying question is `worth-an-appliance`'s: this row is about the ice in a machine
              # somebody already has
              avoid=("buy", "buying", "worth", "cheaper", "cheapest", "best", "which", "recommend"),
              bias=1),
        entry("how-often-to-defrost",
              # The machine's own defrosting, said any of the ways people say it. The food's
              # defrosting is another row, and the freezer words in the second part are what keep
              # these apart: a bare "needs defrosting" on its own does not reach this row.
              (("defrost a freezer", "defrosting a freezer", "best way to defrost", "way to defrost",
                "should i defrost it", "shall i defrost it", "do i defrost it", "needs defrosting",
                "needs a defrost", "needs defrosting out", "how often should i defrost",
                "how often do i defrost", "how often to defrost", "when should i defrost",
                "defrost the freezer", "defrost my freezer", "defrost it now"),
               ("freezer", "freezers", "icebox", "fridge freezer", "ice", "icing", "frosting",
                "how often", "often", "how many times", "once a year", "twice a year", "yearly",
                "frequency", "every few months")),
              "At about 5mm of ice, switch it off at the wall and move the food into a cool box: "
              "budget two to three hours, or overnight with bowls of hot water inside and the door "
              "shut."
              " Most freezers need this once or twice a year. Never chip at the ice, because a "
              "knife can pierce a pipe and write the freezer off, and a frost-free one never needs "
              "it at all, so ice in one means the door seal has gone.",
              # defrosting the food, not the machine: the thigh, the chicken and the loaf keep their
              # own answers, and so does the fridge's thawing method
              avoid=("chicken", "meat", "mince", "turkey", "fish", "prawns", "sausages", "beef",
                     "pork", "lamb", "bread", "pastry", "cake", "food", "the food", "from frozen",
                     "thaw", "thawing", "thawed", "for dinner", "before cooking", "cook it"),
              # "my freezer needs defrosting shall i do it now" reached the take on whether a freezer
              # is worth buying, which names the same machine and the word "need": the take ties this
              # row even with one point of nudge, so it takes two
              bias=2),
        # An appliance that is simply dead had no answer at all: "my dishwasher is broken, what can i
        # do", "my washing machine wont come on", "my fridge is broken what do i do", "my toaster is
        # broken" all got a shrug or an echo. `repair-or-replace` needs a decision word in the line, so
        # a plain fault was nobody's answer. This is the first-aid half: the cheap checks, then the
        # fault code, then the call. The money rule stays in `repair-or-replace`, which its own `ask`
        # gate keeps, and every named fault (a leak, a smell, a drum that will not turn, a fridge that
        # is warm) keeps the entry that knows it.
        entry("appliance-broken",
              (("washing machine", "washer", "washer dryer", "tumble dryer", "dryer", "dishwasher",
                "fridge", "freezer", "fridge freezer", "oven", "cooker", "hob", "microwave", "kettle",
                "toaster", "vacuum", "hoover", "blender", "extractor fan", "telly", "television",
                "appliance", "white goods"),
               ("broken", "broke", "dead", "died", "has died", "packed in", "packing in", "given up",
                "stopped working", "stopped", "wont come on", "won't come on", "wont turn on",
                "won't turn on", "wont switch on", "won't switch on", "wont start", "won't start",
                "not working", "isnt working", "isn't working", "faulty", "nothing happens",
                "what can i do", "what do i do")),
              "A dead appliance is usually the plug, the fuse or a door switch: swap the fuse, try "
              "another socket, shut the door firmly and look the fault code up in the manual. If it "
              "stays dead, take the model number off the sticker and ask the maker or a local repairer "
              "for a fixed-price quote, because under six years old a repair is usually the cheaper "
              "way.",
              # A named fault is another entry's line: the leak, the smell, the drum that will not
              # turn, the machine that trips the house, and the fridge that runs but is warm.
              avoid=("leak", "leaks", "leaking", "drain", "drains", "draining", "wont drain",
                     "not draining", "smell", "smells", "smelly", "musty", "damp", "tripping",
                     "trips", "trip", "fuse box", "rcd", "cuts out", "cutting out", "keeps stopping",
                     "switches itself off", "switching itself off", "noise", "noisy", "banging",
                     "rumbling", "beep", "beeping", "cold", "not cold", "warm", "freezing", "ice",
                     "frost", "defrost", "condenser", "dry properly", "takes ages",
                     # the heating is a system and a gas boiler is Gas Safe work: both have answers
                     "boiler", "the heating", "central heating", "radiator", "radiators",
                     # a machine someone else owns or wants to buy, and a thing that is not one
                     "landlord", "letting agent", "rent", "worth", "repair", "repairing", "replace",
                     "replacing", "new one", "buy a new one", "buy new", "scrap", "scrapping",
                     "engineer", "phone", "laptop", "computer", "tablet", "console", "car", "van",
                     "bike", "bicycle", "cook it", "recall",
                     # "my freezer is full what can i do" is a full freezer, not a dead one, and the
                     # "what can i do" in the key above was all it needed to take that line
                     "full", "full up", "too full", "packed", "overfull", "no room", "no space",
                     "stuffed"),
              # "what can i do with half a bag of spinach in the fridge" is a cooking question that
              # names a fridge, and the "what can i do" in the key above took it: a line that asks
              # what to make with a food it names belongs to the kitchen, not to this row.
              guard=_not_a_cook_ask),
        # The fixtures that are not appliances, and the first check for each: see
        # `_the_fixture_that_stopped` for the lines this took off the bank card, the fibre answer
        # and the extractor fan. The guard is the row's own reading, so a named symptom keeps its
        # own answer and a fixture the table does not know is passed over to the rows that do.
        *list(_the_stopped_fixture_entries(entry)),
        # A broken appliance is a decision, not a shopping question and not a how-to: "is it worth
        # repairing" needs the money rule, and it is the same rule for a washing machine, a dishwasher
        # and an oven, so it is one entry and the appliance words are the first key.
        entry("repair-or-replace",
              (("washing machine", "washer", "tumble dryer", "dryer", "dishwasher", "fridge", "freezer",
                "oven", "cooker", "hob", "microwave", "vacuum", "hoover", "boiler", "kettle", "toaster",
                "mower", "lawnmower", "strimmer", "hedge trimmer", "leaf blower", "blender",
                "hair dryer", "hairdryer", "appliance", "machine", "white goods"),
               ("worth repairing", "worth fixing", "worth mending", "worth replacing", "repair or replace",
                "replace or repair", "fix it or", "repair it or", "buying new", "buy new", "worth",
                "repair", "repairing", "fix", "fixing", "replace", "replacing", "mend", "mending",
                "scrap", "scrapping", "broken", "broke", "engineer", "call someone",
                # The decision often arrives with the symptom instead of the word "repair": "my dryer
                # isnt heating up should i buy a new one" names the fault and the new machine and
                # never says repair, and with only one key word covered it reached no entry at all.
                "not heating", "isnt heating", "isn't heating", "wont heat", "won't heat", "heat up",
                "not spinning", "wont spin", "won't spin", "not turning", "wont turn", "won't turn",
                "not draining", "wont drain", "won't drain", "not drying", "takes ages", "still wet",
                "new one", "buy a new one",
                # The skill question names no money word, so its own words are what such a line
                # shares with the machine: "can i service my lawnmower myself" is a machine and a
                # skill and nothing else.
                "myself", "my self", "diy", "my own", "on my own", "have a go", "give it a go",
                "can i fix", "can i repair", "can i replace", "can i change", "could i fix",
                # "do i need a new washer" is the plainest way the decision is put, and the line
                # names the machine and nothing else: the phrase is the second position the key
                # needs, and nobody asks whether they need a new one of something they do not own.
                "need a new", "need new", "needs a new")),
              _repair_judgement,
              # A how-to is not a decision: "how do i fix a leaking washing machine" keeps its own answer.
              ask=("worth", "replace", "replacing", "repair or", "or repair", "new one", "buying new",
                   "buy new", "scrap", "scrapping", "mend or", "fix it or", "repair it or", "either",
                   # "my dishwasher is broken should i repair it" asks the same question without the
                   # comma, and it was reaching the landlord letter instead of the rule.
                   "repair it", "fix it", "replace it", "should i repair", "should i fix",
                   "should i replace", "mend it",
                   # The decision said the other way round, which is how most people say it: "is it
                   # worth fixing or should i get a new one", "should i get it fixed or buy a new one".
                   # "get a new one" is the same ask as "a new one", and "fixing"/"fixed" alone is not
                   # enough, because "how do i stop the door fixing" is a how-to.
                   "worth fixing", "worth mending", "fixed or", "fixing or", "get it fixed",
                   "get a new one", "get a replacement",
                   # "should i get a new dishwasher or fix this one": the machine is named and the
                   # repair word comes after the "or", which is the same weighing-up as "repair it
                   # or". Without these the line matched the keys and the ask gate refused it, so it
                   # fell through to a shrug.
                   "fix this one", "repair this one", "mend this one", "or fix this", "or repair this",
                   "or fix that", "or repair that",
                   # Who to call is the same decision, and "should i get an engineer out for my dryer"
                   # was answered with the should-I-buy-one take.
                   "engineer", "engineers", "call someone out", "call someone", "call out",
                   "get someone in", "someone in",
                   # The skill question is asked with its own words and no money words at all:
                   # "can i fix my washing machine myself", "can i change the oven element myself".
                   # The rule answers it with the parts list rather than the quote.
                   "can i fix", "could i fix", "can i repair", "could i repair", "can i replace",
                   "can i change", "myself", "my self", "diy", "diy job", "have a go",
                   "give it a go",
                   # "do i need a new washer" is the plainest way the decision is put, and it was
                   # answered with a drill bit (a washer is a fixing as well as a machine) or with
                   # drum sizes. Nobody asks whether they need a new one of something they do not
                   # own, so the phrase carries both the ask and the owning.
                   "need a new", "need new", "needs a new"),
              # "broken" and "repair" are in every line about a machine, and they are also the two
              # words of the landlord letter and of the shopping entry: the decision has to outrank
              # both, which the bias does, and the ask gate keeps it off every other repair line
              # A thing that is not an appliance is not this decision: a jumper that shrank, a car, a
              # laptop, a rented flat and a landlord are all "worth fixing" questions for other answers.
              avoid=("jumper", "wool", "shrank", "shrink", "clothes", "shirt", "coat", "curtains",
                     "car", "bike", "bicycle", "laptop", "phone", "computer", "rent", "landlord",
                     "flat", "radiator", "boiler service",
                     # the heating is the system, not one machine: "the heating is broken" is the
                     # boiler entry's, while "my dryer is not heating" is this one.
                     "the heating", "central heating",
                     # buying one is a shopping question, and a symptom is a how-to: "is it worth
                     # getting a slow cooker" and "my oven is noisy, is it worth fixing" are not this.
                     # "getting" and "get a" are not here: the decision is asked "should i get it
                     # fixed or get a new one" far more often than "is it worth getting a ...", and a
                     # bare "get" would catch both. "worth getting"/"worth buying" keep the shopping
                     # question out without touching "get it fixed".
                     "worth getting", "worth buying", "shop for", "choose", "choosing", "slow cooker",
                     "pressure cooker", "rice cooker", "air fryer", "dishwasher tablets",
                     "noise", "noisy", "banging", "leak", "leaking", "mould", "musty", "smell",
                     "smells",
                     # nor is a machine that will not drain: "i need my washing machine fixed, it
                     # won't drain" carries "fixed" and "washing machine", and the filter answer is
                     # the one that helps. The decision is for a machine that runs but is not worth
                     # repairing, not for one with a jammed pump.
                     "drain", "drains", "draining", "wont drain", "won't drain", "pump", "filter",
                     "water everywhere", "not emptying",
                     # and a line that names the part is the part's own row: "how do i replace the
                     # drive belt on my tumble dryer" is the belt, not the decision about the dryer.
                     "belt", "belts", "drive belt", "brush bar", "brushbar", "brush roll",
                     "impeller", "beater bar"),
              bias=2),
        entry("extractor-fan-noisy",
              # "hood" alone is a car's bonnet in American English and "vent" alone is a tumble dryer,
              # a loft or a heating duct, so the hill phrases carry the kitchen and the bare words are
              # refused below.
              (("extractor", "cooker hood", "extractor hood", "kitchen hood", "range hood", "hob",
                "grease filter", "filter", "filters"),
               ("noisy", "loud", "noise", "rattling", "rattle", "vibrating", "buzzing", "humming",
                "grinding", "sucking", "suck", "weak", "clean", "filter", "filters", "grease filter",
                "smells")),
              avoid=("bathroom", "loo", "toilet", "shower", "bath", "fan oven", "car", "cars", "engine",
                     "bonnet", "truck", "van", "bike", "loft", "tumble dryer", "dryer", "heating",
                     "radiator", "air vent", "air conditioning", "aircon"),
              reply=the_filter_of(("extractor", "cooker hood", "extractor hood", "kitchen hood",
                                   "range hood", "hob", "grease filter"),
                                  EXTRACTOR_GREASE_FILTER)),
        # A smell in a place is not the thing the place word usually means: "how do i get rid of the
        # smell in the garage" was a decluttering plan, "...in the shed" was weight loss (the verb), and
        # "...in the boot" was the football boots' studs. The subject is the smell; the place only says
        # where to look. The fridge, the bin and the car keep their own answers below and beside this.
        entry("place-smell",
              (("smell", "smells", "smelly", "smelling", "stink", "stinks", "stinking", "reek",
                "reeks", "reeking", "odour", "odor", "smells like",
                # the phrase rather than the bare word: "the smell in the boot" is a place question,
                # and the bare words alone lose to whichever row owns the place word
                "smell in", "smells in", "smell from", "smells from", "smell of", "stink in",
                "stinks in", "get rid of the smell", "how do i get rid of the smell"),
               ("shed", "garage", "loft", "attic", "cellar", "basement", "cupboard",
                "wardrobe", "spare room", "conservatory", "porch", "hall", "hallway", "utility",
                "utility room", "outhouse", "bin store", "storage room", "room", "rooms", "house",
                "flat", "empty house", "holiday let", "under the stairs", "stair cupboard",
                "bathroom", "bedroom", "kitchen", "landing", "cloakroom", "guest room",
                # a wet room and a shower room are rooms like the rest: on main "the wet room smells"
                # was answered by the hotel-complaint row, because "room" was all it needed
                "wet room", "shower room", "en suite", "ensuite", "wash room",
                # "the boot" on its own is footwear far more often than it is the back of a car, and
                # the boots keep the answer that knows them; only the phrase says a car. golden-boar
                # measured "how do i stop the boot smelling" losing its pair-of-boots answer to this
                # row, and "smell in the boot of the car" still needs to land here.
                "car boot", "boot of the car", "boot of my car", "the boot of", "boot of a car")),
              # the reply is picked from what the line says the smell is: a place that smells of wee
              # wants the enzyme cleaner, a loft that smells of mice wants the droppings check, and a
              # kitchen that smells of chips wants the pan of water, while a smell nobody can name is
              # the source hunt below.
              _place_smell,
              avoid=("fridge", "freezer", "bin", "bins", "bin day", "wheelie", "car", "cars", "van",
                     "washing machine", "dishwasher", "drain", "drains", "plughole", "toilet", "loo",
                     "sink", "shower", "bath", "mould", "mold", "mildew", "damp", "condensation",
                     "smoke", "gas", "carbon monoxide",
                     # A smell of a named substance is a hazard, not a mystery: the person already
                     # knows what they are smelling, so the answer is what to do about that and not how
                     # to hunt for a source. The paint row, the petrol-fumes row and the oil row all
                     # keep their lines this way - "the garage smells of petrol" was getting bicarbonate
                     # of soda in a bowl, and "how do i stop the garage smelling of paint" lost the
                     # cure-it-and-air-it answer it already had.
                     "petrol", "petrol fumes", "diesel", "fuel", "oil", "paraffin", "kerosene",
                     "paint", "paint fumes", "painting", "painted", "thinner", "white spirit",
                     "solvent", "bleach", "ammonia", "chlorine", "sewage", "rotten", "rot",
                     # a smell *of* a known thing names its own cause, so the person is not hunting
                     # for a mystery: the laundry answer knows sweat, the cupboard answer knows mice,
                     # and the airing card is what vomit in a bedroom wants. bright-plum found these
                     # three losing their answers to this row, and probed the words as a group:
                     # "my shed smells of mice", "the garage smells of sweat", "my hallway smells of
                     # cabbage", "my basement smells of fish", "my bedroom smells of pee" and "how do
                     # i get rid of the smell of sick in the car" are all unchanged by them.
                     "sweat", "sweaty", "mice", "mouse", "vomit", "sick", "urine", "pee",
                     "curry", "cabbage", "weed", "fish",
                     # a musty smell is a damp question, and the damp answer knows what to look for
                     "musty", "damp smell", "smells of damp", "smell of damp", "dog", "cat", "pet", "my breath", "breath",
                     "feet", "foot", "body", "armpit", "mouth", "kettle", "oven", "microwave",
                     "food", "cooking", "fish", "fridge freezer", "tap", "water", "hoover", "vacuum",
                     "washing", "clothes", "mattress", "sofa", "carpet",
                     # a boot of a car and a pair of boots are one word, and the bare plural in an
                     # avoid list stood this row down on its own lines ("boots" is a loose form of
                     # "boot", so even "the boot" met it), so the boots are named as phrases
                     "my boots", "my shoes", "my trainers", "these boots", "these shoes",
                     "pair of boots", "football boots", "work boots", "walking boots",
                     "hiking boots", "shoes", "shoe", "trainers", "slippers", "sandals",
                     "wellies", "welly",
                     # a smell that is cooking, burning or being made nice has its own answer: this
                     # one is for a smell nobody can name the source of
                     "cabbage", "burnt", "burning", "burn", "fried", "frying", "bacon", "curry",
                     "garlic", "spices", "boiled", "drains smell", "nice", "nicer", "lovely",
                     "fresh", "fresher", "freshen", "pleasant", "good", "better"),
              bias=2),
        # A soft thing that has taken a smell up is not the room it is in, and it is not the pet
        # either: on main `1abf1c69` "my sofa smells of dog" was answered "A dog - how long has it been
        # with you?" and "my car smells of wet dog" got the skid answer. The bare noun keeps its own
        # cleaning card ("my rug smells" is still the carpet shampoo) - it is only this row's when the
        # line names what it smells of.
        entry("soft-thing-smell",
              (("soft furnishing", "carpet", "carpets", "rug", "rugs", "sofa", "sofas", "settee",
                "settees", "armchair", "armchairs", "cushion", "cushions", "curtain", "curtains",
                "car seat", "car seats", "car", "cars", "mattress",
                "carpet smells of", "carpet smells like", "carpets smell of", "rug smells of",
                "rug smells like", "sofa smells of", "sofa smells like", "settee smells of",
                "settee smells like", "armchair smells of", "cushion smells of", "cushions smell of",
                "curtains smell of", "car smells of", "car smells like", "seat smells of",
                "mattress smells of", "mattress smells like"),
               ("smells of", "smells like", "smells", "smell of", "stinks of", "stinks", "stink",
                "reeks of", "reeks", "reeking", "pong", "whiffs", "whiff", "scent")),
              _soft_smell,
              # damp, mould, smoke and fuel are their own answers, and the pet, the bin and the machine
              # each keep the question about the animal or the appliance
              avoid=("damp", "musty", "mould", "mouldy", "mold", "moldy", "mildew", "condensation",
                     "smoke", "smoky", "cigarette", "gas", "petrol", "diesel", "fuel", "paint",
                     "bleach", "bin", "bins", "washing machine", "washer", "dryer", "dishwasher",
                     "fridge", "freezer", "oven", "microwave", "kettle", "drain", "drains",
                     "sink", "toilet", "loo", "new car", "nice", "fresh", "freshen", "clean",
                     "remove", "get out", "how do i clean", "wash", "shampoo", "vacuum",
                     # a stain on a soft thing already has a method on main, and the upholstery and
                     # mattress rows give the scrap-and-rinse-cold and the do-not-soak-the-foam that
                     # the enzyme cleaner drops: "the sofa smells of sick" and "my car seat smells of
                     # milk" were both a fuller answer before this row reached them.
                     "sick", "vomit", "vomited", "vomiting", "milk", "wine", "coffee", "tea",
                     "juice", "spilt", "spilled", "spilling", "stain", "stains", "stained",
                     # a smell of burning in a car, or off a machine, is a fault and not a thing to
                     # clean: "my car smells of burning" and "my car smells like burning rubber" were
                     # both handed the enzyme cleaner for upholstery. The car row knows the brakes.
                     "burning", "burnt", "burn", "scorching", "scorched", "hot smell",
                     "smells hot", "overheating", "overheated", "brakes", "brake pads", "clutch",
                     "exhaust", "burning rubber", "electrical", "smoke", "fumes")),
        entry("fridge-smell",
              (("fridge", "freezer", "fridge freezer"),
               ("smell", "smells", "smelly", "stink", "stinks", "odour", "odor", "reek")),
              "Throw out whatever has gone off, then wash the shelves and drawers with hot soapy water "
              "and dry them. The usual hiding places are the door seal, which needs wiping in the folds, "
              "and the drain hole at the back, which you can clear with a cotton bud or a bit of wire. A "
              "small bowl of bicarbonate of soda on a shelf takes out what's left; change it monthly.",
              guard=_not_the_food_in_the_fridge),

        # --- appliances and the quick jobs round them ---------------------------
        entry("appliance-noise",
              (("fridge", "refrigerator", "freezer", "fridge freezer", "washing machine", "washer",
                "dishwasher", "dish washer", "tumble dryer", "dryer", "oven fan", "oven", "kettle",
                "microwave", "vacuum", "hoover",
                # a plain fan is an appliance that hums, and it was reaching the tinnitus answer
                # before the gate and a shrug after it; the oven fan and the extractor are avoided
                # below because each names a machine with its own answer
                "fan", "fans", "ceiling fan", "desk fan", "pedestal fan", "floor fan"),
               ("hum", "hums", "humming", "buzz", "louder",
                "buzzing", "rattle", "rattles", "rattling", "click", "clicks", "clicking",
                "knock", "knocks", "knocking", "bang", "bangs", "banging", "squeak", "squeaks",
                "squeaking", "squeal", "squeals", "squealing", "grind", "grinds", "grinding",
                # A screech and a shriek are a squeal, and a clunk is a rattle: the washer's own
                # table has read them for a while, so "my washing machine is screeching" was
                # answered while "my tumble dryer is screeching" was met with a nod, which is one
                # sound reaching two answers depending on the machine.
                "screech", "screeches", "screeching", "shriek", "shrieks", "shrieking",
                "scream", "screams", "screaming", "clunk", "clunks", "clunking",
                "clank", "clanks", "clanking",
                "gurgle", "gurgles", "gurgling", "whirr", "whirring", "scrape", "scraping",
                "vibrate", "vibrating", "shaking", "thump", "thumping", "whine", "whining",
                "tick", "ticking", "whistling") + NOISE_WORDS),
              _appliance_noise,
              # a fridge, a washer, a boiler and a laptop fan all have their own answers elsewhere, and an
              # appliance that also smells, smokes or leaks is a fault question, not this one: the
              # noise is the least of it
              avoid=("fridge", "freezer", "refrigerator", "washing machine", "washer", "boiler",
                     "radiators", "radiator", "heating", "laptop", "computer", "pc",
                     # a games console that roars is cooling itself, in `console-noisy`
                     "playstation", "ps5", "ps4", "xbox", "console", "games console", "nintendo",
                     "phone", "car", "engine", "mot", "neighbour", "neighbours", "music", "tv",
                     "radio", "fan heater", "smell", "smells", "smelling", "smelly", "stink",
                     "stinks", "burning", "burnt", "burn", "smoke", "smoking", "smoky", "fire",
                     "spark", "sparks", "sparking", "gas", "fumes", "leak", "leaks", "leaking",
                     "leaked", "flood", "flooding", "wiring", "sockets",
                     # a crowd is not a fan motor: "the fans were shrieking at the ref" is people
                     # in a stand, and it must not be told to oil a bearing
                     "ref", "referee", "crowd", "stadium", "terrace", "sang", "seat", "seats",
                     # a cooker hood has its own entry (`extractor-fan-noisy`), so this table never
                     # claims one: a hood is noisy when it is only greasy, and that entry answers
                     # the filters, the duct and the smell as well
                     "extractor", "extractor fan", "cooker hood", "extractor hood", "range hood",
                     "kitchen hood", "hood", "hoods", "hob", "grease filter",
                     # a fan in a bathroom is that room's extractor and has the timer and cleaning
                     # answers above: this table's "a fan hums because that is what it does" was
                     # answering "why is my bathroom fan so loud" instead of them
                     "bathroom", "loo", "toilet", "shower", "shower room", "wet room", "en suite",
                     "ensuite")),
        # A machine that will not stop is not a laundry-sorting question: "my washing machine keeps
        # running" was answered "sort by colour, not by kind of garment" on main `16d3db7a`, because
        # sorting-wash keys on "washing" and the "running" that means a colour bleeding. Nothing
        # answered the fault itself, and "the washing machine wont stop filling" got the dead-machine
        # card (check the fuse), which is the wrong end of the fault.
        entry("washing-machine-wont-stop",
              (("washing machine", "washer", "washer dryer", "washing mashine", "drum"),
               ("keeps running", "keep running", "kept running", "runs forever", "running forever",
                "running for hours", "wont stop", "won't stop", "wont stop filling", "wont stop beeping",
                "keeps filling", "keep filling", "doesnt stop", "doesn't stop", "never stops",
                "wont turn off", "won't turn off", "keeps going", "stuck on a cycle",
                "stuck on the same cycle")),
              "A machine that will not stop is waiting for something it cannot do: switch it off at the "
              "wall and turn the water off at the valve behind it, then clean the filter behind the kick "
              "plate and check the drain hose is not kinked. Set it to drain or spin only and start it "
              "again. If it fills even with the water off, the water-level pressure switch has failed, "
              "which is an engineer's job.",
              # sorting-wash keys on "washing" and the "running" of a colour, and the two rank level,
              # so the fault only wins on bias: the registry's domain order would hand the line back
              bias=2,
              # a machine that will not drain, will not spin or will not open its door has its own
              # answer; this one is the cycle that never ends
              avoid=("door", "doors", "locked", "lock", "wont open", "won't open", "smell", "smells",
                     "leak", "leaking", "noise", "noisy", "banging", "rattling", "which", "best",
                     "buy", "sort", "colours", "colors", "whites", "darks")),
        entry("washing-machine-wont-drain",
              # "cycle" on its own meant the washing machine to this entry, so "the water cycle"
              # in a school question was a drum that would not empty. The appliance or its cycle
              # has to be named, which every real line does.
              (("washing machine", "washer", "drum", "spin cycle", "wash cycle"),
               ("drain", "draining", "wont drain", "won't drain", "empty", "water", "pump",
                # "blocked" is how most people say it, and the words were not here, so
                # "the washing machine is blocked" was the laundry-sorting card
                "blocked", "blockage", "clogged", "not emptying", "backed up", "backing up")),
              "The filter is the usual culprit, behind the little kick plate at the bottom front: put a "
              "shallow bowl and a towel down, unscrew it slowly and pull out the coins and hair. Then "
              "check the drain hose behind the machine isn't kinked or pushed too far into the standpipe. "
              "If it still won't empty, the pump needs replacing, which is a cheap part and a half-hour "
              "job for an engineer.",
              # the laundry-sorting row keys on "washing" and ranks level with this one, so the
              # fault only wins on bias - "the washing machine is blocked" was the sorting card
              # otherwise, exactly as `washing-machine-wont-stop` says below
              bias=2,
              # "stuck" used to be in the key above, and "the door is stuck" is the door question:
              # the drain entry now passes on a door, a lock or a shut drum. Water *coming out* is the
              # leak entry's line, not a blocked filter, so it passes on that too.
              # the fault has to be named, not just the water: the guard above is what keeps the
              # litres, the heat and the smell out, and this row's bias only wins a tie it reaches
              guard=_a_machine_that_will_not_empty,
              avoid=("buy", "which", "best", "door", "doors", "locked", "lock", "shut", "open",
                     "leak", "leaks", "leaked", "leaking", "coming out", "pouring out", "pouring",
                     "flooded", "flooding", "underneath",
                     # a car's screen wash is a washer too: "my washer jets are blocked" is the
                     # car, so the car's own words go with the guard that asks for a fault
                     "jet", "jets", "nozzle", "nozzles", "windscreen", "windshield",
                     "screen wash", "washer fluid", "washer jet", "washer jets")),
        # The filter is the job people ask about on its own, and the smell entry was taking it. It is
        # a small hatch and a bowl, not a service wash, so it gets its own answer.
        entry("washing-machine-filter",
              # "filter" is a word here as well as the parts, so a follow-up that names only the part
              # is in play; the reply stands down unless the machine is this one
              (("washing machine", "washer", "washer dryer", "washing mashine", "filter", "filters"),
               ("filter", "filters", "filter cap", "pump filter",
                # the pump sits behind the same kick plate, so "how do i clean the drain pump" is this
                # job; a bare "pump" is not here because "my washing machine pump is noisy" is the
                # banging-and-walking row's line
                "drain pump", "pump cap", "clean the pump", "clear the pump")),
              # the extractor hood's grease filter is the other filter a house has, and on a tie it
              # was winning this line: a machine named in the line is this row's question
              bias=3,
              reply=the_filter_of(("washing machine", "washer", "washer dryer", "washing mashine"),
                                  WASHING_MACHINE_FILTER)),
        # The detergent drawer is the third place a machine grows black, and it is the only one a
        # person can take out and scrub, so it is its own job: "how do i clean the washing machine
        # drawer" was the door-seal answer, which is no help with a drawer full of softener.
        entry("washing-machine-drawer",
              (("washing machine", "washer", "washer dryer", "washing mashine", "laundry",
                "detergent drawer", "soap drawer", "powder drawer", "dispenser drawer",
                "fabric softener drawer"),
               # no bare "clean" or "smell" here: "how do i clean my washing machine" and "my washing
               # machine smells" are the service wash, and with those two words in this group the
               # drawer took both, and the filter question with them
               ("drawer", "drawers", "dispenser", "compartment", "detergent", "soap", "powder",
                "trap", "gunk", "slimy", "sticky", "scrub")),
              "Pull the drawer right out until it stops, press the release catch in the middle of the "
              "softener compartment, and take it to the sink. Lift out the cap and the siphon tube, "
              "soak everything in hot water with a little washing-up liquid or a dishwasher tablet for "
              "half an hour, then scrub the corners with an old toothbrush. Reach into the housing left "
              "in the machine and scrub the top and the back of it too, because that is where the black "
              "grows, and run an empty hot rinse before the next load. Use powder now and then and "
              "leave the drawer open between washes: softener is what feeds it.",
              # the black in the rubber seal is the mould row's answer, and a drawer that is a kitchen
              # or a bedside drawer is not this one
              avoid=("door seal", "rubber", "seal", "mould in the seal", "black around the door",
                     "kitchen", "bedside", "desk", "chest of drawers", "cutlery", "sock", "socks",
                     "fridge", "freezer", "wardrobe", "bathroom cabinet",
                     # "where do i put the detergent" is the compartment question, not this job:
                     # taking the drawer out and scrubbing it answers a different ask, and the
                     # consumables row has the three compartments
                     "where do i put", "where do the", "where does", "where should i put",
                     "which compartment", "what compartment", "where do the tablets",
                     # a dishwasher has a detergent drawer too, and its own clean is another job
                     "dishwasher", "dish washer", "tumble dryer", "tumble drier"),
              # the mould row keys "detergent drawer" and "drawer" too and sits earlier in the file,
              # so the drawer needs the higher bias to win the tie "how do i clean the detergent
              # drawer" makes
              bias=3),
        # A machine that is scaled up leaves white flakes on the washing and takes longer to heat, and
        # the question was a punt: nothing in the knowledge base talks about limescale in a washer.
        entry("washing-machine-descale",
              (("washing machine", "washer", "washer dryer", "washing mashine", "washing",
                "laundry", "drum"),
               ("descale", "descaling", "descaler", "limescale", "scale", "scaled", "scaling",
                "calcium", "hard water", "chalky", "white flakes", "flakes on the washing")),
              "Run a descaler through an empty drum on the hottest cycle: a 500g bag of citric acid "
              "from a hardware shop, or a washing-machine descaler, straight into the drum rather than "
              "the drawer, at 60C or 90C, then a rinse cycle with nothing in it. In a hard water area "
              "that is every three months; where the water is soft, once a year is enough. White "
              "flakes on dark washing and a machine that takes longer to heat are the two signs it is "
              "due, and a filter full of grit after the cycle is normal. Skip vinegar: it is hard on "
              "the rubber and the seals, and citric acid does the job better.",
              avoid=("kettle", "coffee machine", "coffee", "dishwasher", "shower head", "shower",
                     "iron", "steam iron", "tap", "taps", "boiler", "dehumidifier", "humidifier",
                     "water softener", "hot tub", "pool", "fish tank", "aquarium", "toilet",
                     "buy", "best", "which", "brand", "price", "cheap", "worth it"),
              # the mould row keys "get rid" and "rid of" for a machine, so "how do i get rid of
              # limescale in my washing machine" tied with it and lost on file order
              bias=3),
        # A dryer's lint filter is the one job nobody does until the load takes two goes, and the
        # line was read back at the person ("Noted: the tumble dryer filter is full of fluff").
        entry("tumble-dryer-filter",
              # "filter" is a word as well as the parts, so a follow-up naming only the part is in play
              (("tumble dryer", "tumble drier", "tumble", "dryer", "drier", "filter", "filters"),
               ("filter", "filters", "fluff", "lint", "blocked", "clogged", "clean", "cleaning",
                "full",
                # pet hair is what a lint filter is full of: "how do i get dog hair out of the tumble
                # dryer" was told a dryer is worth it if you would use it three times a week
                "hair", "pet hair", "dog hair", "cat hair", "fur")),
              # a bare "hair" used to be avoided here so that a "hair dryer" never reached a tumble
              # dryer's filter; the two phrases do that job on their own, and the word itself is now
              # what the row is asked with
              avoid=("hairdryer", "hair dryer", "hair drier", "washing machine", "washer", "dishwasher",
                     # "is a tumble dryer worth it for pet hair" is a buying question that names the
                     # hair, and the filter row now keys the same words
                     "worth", "worth it", "should i", "do i need", "need a",
                     "buy", "which", "best", "price", "repair", "not heating", "wont heat",
                     "not spinning", "makes a noise", "squeak"),
              # the filter is this row's job even when the hair is the subject: "how do i get dog hair
              # out of the tumble dryer" is the same claw-out-the-fluff job with a different noun
              bias=3,
              reply=the_filter_of(("tumble dryer", "tumble drier", "tumble", "dryer", "drier"),
                                  TUMBLE_DRYER_FILTER)),
        entry("washing-machine-door-stuck",
              (("washing machine", "washer", "dryer", "tumble dryer"),
               ("door", "stuck", "wont open", "won't open", "locked", "shut", "open")),
              "Give it three or four minutes: the lock holds until the drum has stopped and the water has "
              "drained. If there's water inside, run a drain or spin cycle first. When it's empty and "
              "still locked, most machines have an emergency release: a small plastic tag or cord behind "
              "the filter hatch that you pull down while pushing the door. Don't force the handle, "
              "because the catch breaks before the door does.",
              avoid=("buy", "which", "best")),
        entry("dishwasher-wont-drain",
              (("dishwasher", "dish washer", "dishdrawer", "dish drawer"),
               # no bare "water", "empty" or "emptying": "the dishwasher is leaking water" is a
               # leak under the machine, "wont fill with water" is the inlet valve, and
               # "how much water does a dishwasher use" is neither, and empty/emptying is what
               # you do to a finished load.
               ("drain", "draining", "wont drain", "won't drain", "not draining", "emptying",
                "not emptying", "wont empty", "won't empty", "full of water", "water in the bottom",
                "water left in", "standing water", "puddle", "left in the bottom",
                "sitting in the bottom",
                # "blocked" is how most people say it
                "blocked", "blocked up", "blockage", "clogged")),
              "Start with the filter: it twists out of the bottom of the drum, and a rinse under the hot "
              "tap with a check for glass or a label in the sump usually fixes it. Then look at the drain "
              "hose where it joins the waste under the sink, because a kink or a blockage there leaves "
              "exactly that water in the bottom. If it hums and still won't empty with both clean, the "
              "drain pump needs swapping, which is a cheap part and a quick job for a repairer.",
              # the cleaning and cloudiness lines belong to the service-wash answer
              avoid=("smell", "smells", "clean", "cleaning", "cloudy", "streaks", "salt", "rinse aid",
                     "buy", "which", "best", "leak", "leaking", "fill", "fills", "filling",
                     "how much water", "uses", "use a lot", "efficient",
                     # "emptying" has to stay in the key for "the dishwasher isnt emptying", and
                     # that one word also reaches the unloading question
                     "empty the dishwasher", "emptied", "unload", "unloading", "quickly")),
        # A dishwasher that has water where water should not be is a fault, not the drain
        # question: the row above keeps "leak" out of its own key on purpose, and nothing else
        # held the line, so "water is coming out of the bottom of my dishwasher" fell to "I'm
        # listening - say more". The mirror of the washing-machine leak row, because the two
        # machines leak in the same places: the door seal and the filter at the front, the inlet
        # and drain hoses underneath.
        entry("dishwasher-leak",
              (("dishwasher", "dish washer", "dishdrawer", "dish drawer"),
               ("leak", "leaking", "leaks", "leaked", "puddle", "puddles", "dripping", "flooding",
                "water coming out", "water coming from", "water coming", "water under",
                "water underneath", "water all over", "water on the floor", "on the floor",
                "all over the floor", "coming out of the bottom", "underneath it", "under it",
                "wont stop leaking", "won't stop leaking")),
              "Turn it off at the wall and shut the water off at the little isolator tap under the "
              "sink, then get the water up - a shallow tray and a towel is enough for a slow one. "
              "Water at the front of the door is usually the door seal or the filter, so twist the "
              "filter out and check the seal for food or a split; water underneath is the inlet or "
              "drain hose where it joins the machine or the waste, so check those joints first. "
              "Leave it off until that seal or joint is fixed: a leak from inside the machine "
              "itself is a repairer's job.",
              # a machine that will not drain, a load that comes out wet, a smell and a box of
              # salt all have their own rows, and a new one to buy is the shopping answer
              avoid=("buy", "which", "best", "cheapest", "price", "cost",
                     "wont drain", "won't drain", "not draining", "not emptying", "wont empty",
                     "won't empty", "full of water", "water in the bottom", "standing water",
                     "left in the bottom", "filter", "pump", "empty", "emptying",
                     "smell", "smells", "smelly", "cloudy", "streaks", "salt", "tablet",
                     "rinse aid", "still wet", "wont dry", "won't dry", "how much water",
                     "uses", "use a lot", "install", "installing", "fit a", "fitting"),
              bias=1),
        entry("machine-consumables",
              (("salt", "tablet", "tablets", "powder", "detergent", "liquid", "pod", "pods",
                "capsule", "capsules", "rinse aid", "rinse-aid", "softener", "conditioner",
                "dishwasher cleaner"),
               ("where do i put", "where do the", "where do i add", "where do i fill",
                "where does", "where should i put", "where to put", "where in the",
                "which compartment", "what compartment", "top up", "topup", "how much",
                "which bit", "run out", "ran out", "refill", "where", "put", "fill", "go",
                "goes",
                # a follow-up that names only the next consumable is the same question about the
                # same machine: "where does the salt go in my dishwasher" then "and the rinse aid?"
                "and the", "what about the", "and what about the", "how about the")),
              _where_the_consumable_goes,
              # a cloudy load, a wet load and a machine that will not drain all have their own rows,
              # and a box of salt to buy is the shopping answer
              avoid=("cloudy", "streaks", "white marks", "film", "smell", "smells", "smelly",
                     "wont dry", "won't dry", "still wet", "wet dishes", "drain", "draining",
                     "leak", "leaking", "buy", "which", "best", "price", "cost", "how often",
                     "repair", "broken", "not working", "error"),
              guard=_a_machine_consumable, bias=1),
        entry("dishwasher-wet",
              (("dishwasher", "dish washer", "dishdrawer", "dish drawer"),
               ("dishes are wet", "dishes still wet", "dishes come out wet", "leaves the dishes wet",
                "leaves everything wet", "not drying", "isnt drying", "isn't drying", "wont dry",
                "won't dry", "still wet", "wet dishes", "wet after", "water on the dishes",
                "water left on", "comes out wet", "everything is wet"),
               # "the dishes" is a third thing the line says, so a drying fault outranks the
               # cooking.fix-dry entry that keys the bare word "dry"; the ask gate keeps a line
               # that only names the load out of it.
               ("dishes", "dish", "plates", "glasses", "crockery")),
              "Rinse aid and salt first: without rinse aid the water clings in drops, so fill the "
              "rinse-aid compartment and set it to 4 or 5, and top up the salt. Use the hottest "
              "programme you have and open the door an inch when it finishes so the steam escapes; "
              "plastic always dries worse than china. If the load is still soaked, clean the filter "
              "and check the spray arms turn freely.",
              # A drain fault, a leak, a smell and a cloudy load all have their own entries; this is
              # only the load that comes out wet from an otherwise working wash.
              ask=("wet", "drying", "dry", "damp", "water", "soaked"),
              avoid=("wont drain", "won't drain", "not draining", "drain", "draining",
                     "full of water", "water in the bottom", "standing water", "leak", "leaking",
                     "smell", "smells", "smelly", "cloudy", "white marks", "streaks", "clean",
                     "cleaning", "worth", "replace", "repair", "quote", "cost", "buy", "which",
                     "best",
                     # A noise named in the same line is the noise table's answer, however wet the
                     # plates are: "my dishwasher is humming but the dishes are wet" is one fault
                     # named twice and the hum is the one the person is worried about. Only the
                     # noise words go here. A smell or a drain word would leave both dishwasher
                     # entries standing aside, and "Got it." is worse than either answer.
                     "hum", "hums", "humming", "hummed", "noise", "noisy", "loud", "louder",
                     "rattle", "rattles", "rattling", "squeak", "squeaks", "squeaking",
                     "bang", "bangs", "banging", "knock", "knocks", "knocking", "grind",
                     "grinding", "vibrate", "vibrating", "clunk", "clunks", "clunking")),
        # The timer on the boiler, in a house where the heating is not on a smart stat. Not the
        # phone's timer and not the thermostat's own schedule: the programmer with the two channels.
        entry("heating-programmer", (("boiler", "heating", "thermostat", "boiler timer",
                                      "timer on the boiler",
                                      "boiler programmer", "heating programmer", "heating timer",
                                      "programmer", "programmer on the boiler", "timer for the "
                                      "heating", "heating times", "heating clock",
                                      # the clock and the schedule live on the programmer, and people
                                      # name whichever box is on the wall: "how do i set a thermostat
                                      # schedule", "how do i change the time on my thermostat"
                                      "thermostat schedule", "thermostat times", "thermostat timer",
                                      "time on the thermostat", "thermostat clock",
                                      "clock on the thermostat", "heating schedule",
                                      "heating programme", "heating program"),
                                     # The clock is on whichever box is on the wall, and the way a
                                     # person asks for it names the thermostat and the time, not the
                                     # word "programmer": "how do i change the time on my thermostat"
                                     # and "my thermostat clock is wrong" were both answered with the
                                     # room temperatures until these phrases were keyed here.
                                     ("timer", "set", "setting", "change", "times", "time",
                                      "programme", "program", "adjust", "clock", "am", "pm")),
              "Set the clock and the day on the programmer first, because every on and off time you "
              "enter is measured from it. Then give each channel two blocks: heating on about half an "
              "hour before you get up and off when you leave, then on again before you come back and "
              "off at bedtime, and the hot water channel set to a morning and an evening block. Put "
              "the room thermostat at 18 to 19C while you are in and 15 to 16C overnight, and let the "
              "thermostat do the switching rather than turning the programmer up and down. A combi "
              "boiler with a smart thermostat wants the heating channel left on constant, because the "
              "thermostat is doing the timing.",
              # A clock, a schedule or a timer is what makes a line this entry's, and the setting of
              # the temperature is not: "how do i set my thermostat" has no clock word, so it keeps
              # the number answer, while "how do i change the time on my thermostat" and "my
              # thermostat clock is wrong" come here. Without the gate, "set" plus "thermostat" was
              # enough for this row to take every thermostat line in the house.
              ask=("time", "times", "clock", "clocks", "schedule", "schedules", "programme",
                   "program", "programmer", "timer", "timing", "am", "pm", "on and off",
                   "what time", "the time", "change the time", "set the time"),
              # the temperature of the flow is energy-bill's dial question, and a boiler that is
              # faulty or leaking is a fault answer
              avoid=("phone", "app", "oven", "washing machine", "dishwasher", "sprinkler", "light",
                      "christmas", "fault", "error", "not working", "broken", "temperature",
                      "flow", "pressure", "leak", "leaking", "noise", "noisy", "smell")),
        # The dial on the boiler has one number on it and no bill in the question: "how do i lower
        # my boiler temperature", "what should the flow temperature be", "how hot should my boiler
        # be" were a plumber hedge on main, because the bill answer wanted a bill word and the
        # programmer answer stands down on "temperature" and "flow" on purpose.
        entry("boiler-flow",
              (("boiler flow", "boiler flow temperature", "flow temperature", "flow temp",
                "boiler temperature", "boiler thermostat", "boiler dial", "boiler setting",
                "temperature on the boiler", "temperature of the water in the boiler",
                # the word order is the person's, and "what temperature should the boiler be" puts
                # the box first: the dial word in the second group is what makes it a dial question
                "boiler", "boilers"),
               ("temperature", "hot", "hotter", "cooler", "lower", "turn down", "turn it down",
                "flow", "what temperature", "how hot", "number", "what number",
                "set", "setting", "should", "what", "how hot", "change", "adjust", "efficient",
                "efficiency", "55", "60", "condensing", "combi")),
              "Set the flow temperature on the boiler dial to 55 to 60C. That is the temperature of "
              "the water going round the radiators, and the lower it is the less gas each hour costs, "
              "because a condensing boiler only recovers its waste heat with a cool return. If the "
              "house is slow to warm, go to 65C and turn the room thermostat down again rather than "
              "going higher than that. A hot water cylinder stays at 60C whatever the heating is set "
              "to, so the two numbers are not the same dial.",
              # a boiler that is not working, or is leaking, noisy or smoking, is a fault answer
              avoid=("pressure", "leak", "leaking", "fault", "error", "not working", "broken",
                     # one radiator's valve is its own row, not the boiler's dial
                     "turn down a radiator", "turn down the radiator", "one radiator",
                     "rad valve", "radiator valve", "trv", "thermostatic valve",
                     "too hot", "very hot", "overheat", "overheating", "scald", "scalding",
                     "noise", "noisy", "smell", "fumes", "carbon monoxide", "pilot light",
                     "service", "serviced", "servicing", "engineer", "install", "replace",
                     "how much", "price", "bill", "tariff", "cost"),
              # a named sound is the noise row's question: "the boiler buzzes when the hot water
              # runs" holds "boiler" and "hot" and was answered with the flow-temperature dial.
              guard=not_a_sound),
        # Where the plate with the model and serial number is. "where is the model number on my
        # boiler" was the flow-temperature card, because the dial row keys "number" and "boiler",
        # and the same question about a washing machine, a fridge and an oven was a search hedge:
        # the place is the answer, and it is a place on every appliance.
        entry("where-is-the-model-number",
              (("model number", "model no", "model num", "serial number", "serial no",
                "rating plate", "data plate", "data badge", "spec plate", "type plate",
                "product number", "benchmark sheet", "benchmark logbook", "benchmark"),
               ("boiler", "boilers", "combi", "washing machine", "washer", "dishwasher",
                "fridge", "freezer", "fridge freezer", "oven", "cooker", "dryer",
                "tumble dryer", "microwave", "vacuum", "hoover", "kettle", "toaster",
                "appliance", "appliances", "the machine", "my machine", "white goods",
                "manual", "user guide", "sticker", "rating plate", "data plate")),
              "It is on a plate or sticker you can read without moving the machine: on a boiler, "
              "under the case near the pipes, behind the drop-down flap or on the side panel, and "
              "the Benchmark sheet in the manual carries the same serial. On a washing machine or "
              "dishwasher it is on the rim inside the door, on a fridge or freezer inside on a "
              "side wall or the inner door, on an oven on the frame or the door edge, and on a "
              "kettle, toaster or microwave underneath. The model number is the short code and "
              "the serial is the longer one - the parts shop or the maker's site wants both, so "
              "photograph the plate once you have found it.",
              # which boiler to buy, and a boiler that is faulty, are other rows
              avoid=("which boiler", "what boiler", "new boiler", "buy", "buying", "replace",
                     "replacing", "price", "cost", "how much", "quote", "efficiency", "size",
                     "kw", "output", "fault", "error", "not working", "broken", "leak",
                     "leaking", "noise", "noisy", "pressure", "service", "serviced")),
        # Turning one radiator down is the valve on that radiator, not the boiler dial: "how do i
        # turn down a radiator" was the bill card on this branch, because "radiator" is in the bill's
        # key and nothing else answers the valve.
        entry("radiator-turn-down",
              (("radiator", "radiators", "rad valve", "radiator valve", "trv", "thermostatic valve",
                "valve on the radiator", "towel rail"),
               ("turn down", "turn it down", "turning down", "lower", "too hot", "hot", "cooler",
                "adjust", "set", "setting", "one radiator", "in the bedroom", "in a bedroom",
                "which way", "number",
                # "how do i turn my bedroom radiator down" puts the room between the verb and "down",
                # so the phrase "turn down" is never there; the word "down" is. The words that say
                # the radiator is too warm are keys too, because that is the same valve.
                "down", "full", "on full", "full blast", "max", "maximum", "on high",
                "roasting", "scorching", "boiling", "overheating", "cant sleep", "cannot sleep",
                # the other positions of the same head, and the words printed on it: "how do i turn
                # a radiator up" and "how do i turn a radiator off" were both a punt, and "what do
                # the numbers on a radiator valve mean" was the physics of how a radiator heats a
                # room. "turn down" is a phrase, so it never matched "turn a radiator down": the
                # single words go here too. Not the bare "switch" - a follow-up is merged with the
                # line before it, and "how do i switch a radiator off for the summer" plus "and the
                # towel rail" then became a line this row took.
                "up", "turn up", "turn it up", "turning up", "turn", "turning", "turned",
                "off", "turn off", "turn it off", "switch off", "switched off", "off position",
                "numbers", "dial", "trv", "thermostatic", "snowflake", "frost setting",
                "frost mark", "what setting")),
              "Turn the numbered head at one end of the radiator down a notch or two - that is the "
              "valve that sets the room, and the numbers are roughly 2 for 16C, 3 for 18C and "
          "4 for 21C. A bedroom "
              "wants 16 to 18C for sleep, so 2 is usually the setting there, and turning it down is "
              "the way to cool a room that a radiator has made too warm. Leave the plain "
              "valve at the other end alone; it is the balance for the whole system. Turn it to the "
              "snowflake - frost protection, about 7C - in a room nobody uses, and give it until "
          "the next morning, because a radiator takes an hour to show a change. If the head does "
          "not click and the radiator stays as "
              "hot, the pin under it is stuck: take the head off and work the pin free with pliers.",
              avoid=("leak", "leaking", "drip", "puddle", "bleed", "bled",
                 # "down" is a word about the system as well as about the valve: "the radiator is
                 # down on pressure" and "the heating is down to half a bar" are the sealed
                 # system's gauge, and the bare key word pulled them onto this card. The pressure
                 # words stand this row down; heating-pressure answers them.
                 "pressure", "bar", "psi", "gauge", "filling loop", "top up", "topping up",
                 "cold at the top",
                     "cold at the bottom", "not heating", "stays cold", "noise", "banging", "kettling",
                     "buy", "which radiator", "which rad", "which boiler", "which one", "which type",
                     "best", "how many", "size", "boiler", "install", "replace")),
        # A thermostat that says low battery is a how-to, and on this branch the science row about
        # what a battery is took it: "how do i change the batteries in my thermostat" was a chemistry
        # lesson. The cells are behind the front, and the whole answer is which ones and what to do
        # after.
        entry("thermostat-battery",
              (("thermostat", "thermostats", "room thermostat", "boiler thermostat", "hive", "nest",
                "tado", "smart thermostat", "heating controls", "thermostat display"),
               ("battery", "batteries", "low battery", "battery low", "battery flat", "change the "
                "batteries", "replace the batteries", "new batteries", "cell", "cells",
                "goes blank", "blank screen", "keeps losing the signal", "flashing")),
              "Take the front off the thermostat and change the cells: most take two AA or AAA, and "
              "the battery cover is either the whole front pulling off its wall plate, as on a Hive, "
              "or a small slide-out tray at the side. Use alkalines rather than rechargeables, because "
              "a rechargeable cell sits at 1.2V and the unit reads that as low. After new cells give "
              "it five minutes to find the hub again, then check the time and schedule, which is what "
              "a dead battery loses.",
              # a battery that is being thrown away is the bin answer, and a phone or a watch is
              # their own
              avoid=("bin", "recycle", "recycling", "dispose", "disposal", "phone", "iphone", "watch",
                     "car", "key fob", "smoke alarm", "doorbell", "camera")),
        entry("heating-temperature",
              (("heating", "radiator", "radiators", "thermostat", "house", "flat", "home", "room",
                "rooms", "bedroom", "bedrooms", "living room", "sitting room"),
               ("temperature", "how warm", "how hot", "warm enough", "too cold", "freezing", "cold",
                "keep it at", "set it at", "set the", "keep the heating", "all day", "overnight",
                "at night", "timer",
                # "when should i put the heating on" was a search hedge: the number answer was here,
                # and the words a person uses for the switch were not in either group. What turns it
                # on is a room below 18C, not a date, so both belong to this entry.
                "put the heating on", "put the heating", "turn the heating on", "turn the heating off",
                "turn the heating", "switch the heating", "heating on yet", "heating off",
                # the possessive forms belong in this group as well as the subject group: group one
                # has already spent the word "heating" by the time this group is read, so the phrase
                # never matched and "how do i turn my heating down" reached no row at all. They are
                # kept whole on purpose - the bare phrase is in the follow-up context of a
                # cold-radiator chat and pulled the next turn onto the room temperature.
                "my heating up", "my heating down", "our heating up", "our heating down",
                "turn my heating up", "turn my heating down", "turn our heating up",
                "turn our heating down", "turn down my heating", "turn up my heating",
                "turn down our heating", "turn up our heating",
                "turn it on", "turn it off", "have the heating",
                # "how do i set my thermostat" and "what temperature should i set my thermostat to"
                # are this row's question, but "set" alone only counted as "set it at"/"set the",
                # so the reset row took them and answered with a pinhole. The ways a person says
                # "put it at a number" go here, and the reset stays the reset.
                "set my thermostat", "set the thermostat", "change my thermostat",
                # "what should i set my bedroom thermostat to at night" was the gym answer, because
                # the question is one bare "what should i set" and nothing else carried it
                "bedroom thermostat", "thermostat at night", "set my bedroom",
                "what should i set my", "what should i set the",
                "change the thermostat", "thermostat setting", "thermostats", "what temperature",
                "what temp", "what should i set", "how should i set", "set it to", "set the heating",
                "set the heating times", "set the heating timer", "heating timer", "heating times",
                "programme the heating", "program the heating")),
              "18C is the usual living-room setting and 16C for bedrooms, with 20C to 21C for a baby's "
              "room, for someone ill or elderly, or for anyone who feels the cold. Go by the room, not "
              "the calendar: put it on when the living room drops below about 18C, or when you are "
              "sitting still and feel cold, and then set it and leave it, turning it down at night or "
              "when you're out rather than running it low all day. If the rooms never get to 18C with "
              "the heating on, that's a boiler or radiator problem rather than a thermostat one.",
              # bleeding, noise, leaks, pressure, bills and feeling the cold are all separate questions
              avoid=("bleed", "bleeding", "bottom", "top", "noise", "noisy", "bang", "banging", "kettle",
                     "leak", "leaking", "drip", "dripping", "pressure", "boiler", "landlord", "bill",
                     "bills", "cheaper", "cost", "price", "money", "saving", "save", "feel", "feeling",
                     "always", "hands", "feet", "shivering", "tired", "thyroid",
                     # "home with a cold" is an illness, "back home from Greece, 30 degrees" is a
                     # holiday report, and "a small flat and i work all day" is about the day
                     "flu", "cough", "stuck", "company", "greece", "spain", "holiday", "raining",
                     "rain", "sun", "heatwave", "work all day", "out all day",
                     # A house left empty wants the away answer (low, and the water off), not a
                     # setting for a room someone is sitting in: "should i leave my heating on when
                     # i go on holiday" and "...so the pipes dont freeze" are the away and frost
                     # questions, and both have their own row.
                     "go away", "going away", "away for", "when im away", "when i am away",
                     "while im away", "on holiday", "empty house", "house is empty", "nobody in",
                     # the cooling row's question: keeping the heat out, not setting a number
                     "keep the heat out", "heat out", "stop the sun", "sun heating", "block the sun",
                     "the sun coming in", "sun comes in", "sun through",
                     "pipes", "pipes freeze", "pipes dont freeze", "pipes from freezing",
                     # a room at 39 is a heat emergency, not a thermostat setting
                     "room temperature is", "39", "40", "41", "42", "fever",
                     # a cooking temperature, a hot bath, a fault code or a thermometer reading is
                     # not the setting for the house
                     "oven", "cook", "cooking", "roast", "bake", "chicken", "meat", "bath", "water",
                     # "room temperature" is a recipe's phrase as well as a thermostat's: "should
                     # eggs be at room temperature" was told the living-room setting, and the
                     # bedroom row hands its own food lines on, so the food words stand this down.
                     "egg", "eggs", "butter", "milk", "cheese", "dough", "yeast", "batter",
                     "chocolate", "cake", "yoghurt", "yogurt", "defrost", "thaw",
                     "not working", "broken", "fault", "error", "thermometer", "sick", "unwell",
                     "garage",
                     # a heating that will not come on is the boiler's answer, not a setting
                     "wont", "won't", "come on", "coming on", "wont come on", "stuck on",
                     "not coming on", "no heating",
                     # the clock, the schedule and the on and off times live on the programmer, and
                     # "how do i change the time on my thermostat" was getting the room temperatures
                     "change the time", "set the time", "the time on", "clock", "clocks",
                     "clock is wrong", "clock wrong", "schedule", "schedules", "set the schedule",
                     "the schedule for", "programmer",
                     # a flat battery has its own row: "how do i change the thermostat battery"
                     # was the room temperatures, because the key holds "change the thermostat"
                     "battery", "batteries", "low battery", "blank screen", "display blank",
                     "keeps losing the signal"),
              # two of the words above are in the key for the ordinary shape of the question, so a
              # line has to say something about the heat as well as the place or the day
              # "freezing" and "at night" are not in the ask list: a person who says "my bedroom is
              # freezing at night" wants the room warm, which is heat-a-room's answer, while "how warm
              # should a bedroom be" is the number question and asks with "how warm"
              ask=("temperature", "how warm", "how hot", "warm enough", "keep it at", "set it at",
                   "keep the heating", "leave the heating", "leave it on", "heating on", "thermostat",
                   "degrees", "timer", "overnight", "too cold",
                   # the switch and the calendar are the same question as the setting: "when should
                   # i put the heating on", "should i put the heating on yet", "should i turn the
                   # heating off at night". "at night" on its own is not here on purpose - "my bedroom
                   # is freezing at night" wants heat-a-room.
                   "put the heating", "turn the heating", "switch the heating", "heating off",
                   "heating on yet", "turn it on", "turn it off", "have the heating",
                   # a possessive is the same question and it was a punt: "how do i turn my heating
                   # down" reached no row at all, because this gate knows only "the heating"
                   "turn my heating", "turn our heating", "my heating up", "my heating down",
                   "our heating up", "our heating down", "turn down my heating", "turn up my heating",
                   "turn down our heating", "turn up our heating")),
        # A bare "water" made "why is my boiler not heating water" a leak: the leak has to be
        # described (a drip, a puddle, water under it), not just mentioned.
        entry("boiler-leak",
              ("boiler", ("drip", "dripping", "drips", "leak", "leaking", "leaks", "puddle",
                          "underneath", "overflow", "water under", "water coming", "water everywhere",
                          "water all over", "spraying", "spurting",
                          # "water is coming out of my boiler" and "how do i get water out of my
                          # boiler" are the same leak with the verb in the middle, so the phrase
                          # "water coming" alone never reached them
                          "water is coming", "water coming out", "water out", "water is dripping",
                          "water leaking", "water pouring", "water is pouring", "water coming from")),
              "Turn the boiler off at the wall switch (not at the fuse board, you want the pump to run on "
              "for a minute first), put a bowl under it and turn the water off at the stopcock if it's "
              "more than a drip. A leak from the boiler casing itself is a Gas Safe engineer's job: don't "
              "take the cover off, and don't keep resetting it. Water running from the pressure relief "
              "pipe outside means the pressure is too high, which needs looking at too.",
              avoid=("buy", "best", "cost", "price", "install", "new", "landlord", "tenant",
                     # a boiler with cold water is not a boiler with a puddle under it
                     "not heating", "isn't heating", "isnt heating", "heating the water", "no hot water",
                     "no heating")),
        entry("leak-under-sink",
              (("sink", "under the sink", "waste", "trap", "u-bend", "ubend", "pipe"),
               # "wet patch" and "puddle" are how a person describes water they found rather
               # than saw fall: "wet patch under the sink" reached the child-wets-bed card, and
               # "the wet patch under the sink is spreading" reached a card about going away.
               # The row that answers a puddle answers a wet patch too.
               # The second key is what the water is doing, never where it is: "sink",
               # "under the sink" and "underneath" are in the first key, so putting the place in
               # both halves made any line that names the place a match with no water word in it
               # at all - "mould under the sink" and "mould in the cupboard under the sink" left the
               # mould card for this one. A line that names where the water is already matches on
               # the first key, so the second key only has to say it is water.
               ("leak", "leaking", "drip", "dripping", "water", "puddle", "fix", "wet patch",
                "wet", "soaked", "pool", "pooling", "spreading", "damp patch", "damp")),
              "Dry everything, put a bowl under the trap and run the tap to see where the water appears. "
              "A drip at a plastic joint is nearly always a hand-tight nut: give it another quarter turn, "
              "no more, because overtightened plastic splits. If it's the trap, unscrew it, clean out the "
              "gunge, check the rubber washer is seated and put it back. Wrapping PTFE tape on a plastic "
              "thread makes it worse, not better.",
              avoid=("blocked", "smell", "slow", "drain",
                     # an ear is not a sink: "water trapped in my ear" is the ear's own answer
                     "ear", "ears",
                     # and "how do i waste less water" is the saving, not the trap: a bare
                     # "waste" is in this row's key, so the saving words have to stand it down
                     "less water", "save water", "saving water", "wasting water", "waste less",
                     "water use", "water usage", "water bill", "use so much water")),
        # A room under water had no card at all: "i flooded the bathroom" and "water everywhere in
        # the kitchen" reached the intake form - "Got it. Is there anything you'd like a hand
        # with?" - because every water row here keys the thing that is leaking (a tap, a trap, a
        # radiator) and the flood has no thing, only a place. The place is what this one keys,
        # with a flood word beside it, so the leak rows keep their own lines.
        entry("flooded-room",
              (("flood", "flooded", "flooding", "under water", "water everywhere",
                "ankle deep", "inches of water", "deep in water", "swimming in water"),
               ("bathroom", "kitchen", "flat", "house", "room", "rooms", "floor", "floors",
                "carpet", "carpets", "hall", "hallway", "cellar", "basement", "bedroom",
                "utility", "downstairs", "upstairs", "everywhere", "lino", "floorboards")),
              "Turn the water off first: the stopcock is usually under the kitchen sink, and if "
              "water is near a socket or a light, switch that circuit off at the consumer unit. "
              "Then stop whatever is running, bail and mop, and get air moving with a fan and an "
              "open window - a floor or skirting that stays wet a day warps and grows mould. "
              "Photograph it before you clear up, and ring the insurer and whoever owns the "
              "building today if it came through the ceiling.",
              # the garden, the road and the car have their own flood rows, and a washing
              # machine or a toilet that has done this is a machine with a fault, not a room
              avoid=("garden", "lawn", "greenhouse", "shed", "car", "van", "road", "street",
                     "village", "river", "field", "fields", "warning", "risk",
                     # a cellar that fills when it rains is water coming in from outside: the
                     # stopcock is no use there, and it is not the same repair. It has a row of
                     # its own now, so the whole of the outside is fenced off here rather than
                     # one word of it.
                     "rain", "rains", "raining", "rainwater", "storm", "storms", "winter",
                     "groundwater", "water table", "cellar", "basement", "outside", "drain",
                     "drains", "back door", "under the door", "doorway",
                     "insurance quote", "washing machine", "dishwasher", "toilet",
                     "loo", "radiator", "boiler", "tap", "taps", "sink")),
        # Water coming in from outside is the other half of the same night: "my cellar is
        # flooding" and "it is raining and the cellar is flooding" were a shrug, and the burst-pipe
        # card above is wrong for them, because the stopcock stops nothing in a storm. The drain,
        # the doorway and the insurer are what a person needs, and not standing in it.
        entry("water-coming-in",
              (("flood", "flooded", "flooding", "floods", "water", "wet", "seeping", "seeps",
                "rising", "inches deep", "ankle deep", "filling", "coming in", "coming under",
                "coming through", "getting in"),
               ("cellar", "basement", "rain", "rains", "raining", "rainwater", "storm", "storms",
                "outside", "groundwater", "water table", "drain", "drains", "back door",
                "under the door", "doorway", "up through the floor")),
              "Water coming in from outside is not a stopcock: it stops taps, not rain or a "
              "rising water table. Stay out of a cellar with sockets in it, or switch the whole "
              "supply off at the consumer unit first, and pump or wet-vac the water out rather "
              "than mopping it about. Sandbags or a flood door across the doorway help tonight, "
              "photographs help the insurer, and a drain that backs up in a storm is the water "
              "company's to clear.",
              # the indoor flood, the garden, the road and the car keep their own rows
              avoid=("stopcock", "washing machine", "dishwasher", "toilet", "loo", "radiator",
                     "boiler", "tap", "taps", "sink", "pipe", "pipes", "burst", "car", "van",
                     "road", "street", "village", "river", "lawn", "greenhouse", "shed",
                     "garden", "yard", "insurance quote", "warning", "risk", "sandbag"),
              # a line that has the outside in it and a flood with it is this card whatever else
              # it also mentions: "my basement fills with water when it storms" and "rain water is
              # coming into my cellar" were a science lecture and a plumbing musing on the score
              bias=2),
        # The fly and smell-nice answers used to exist twice, once here and once in cleaning.py,
        # worded differently; home.py keeps them because it also owns the house facts around them.
        entry("fruit-flies",
              (("fruit fly", "fruit flies", "fruitfly", "gnats", "flies", "fly"),
               ("kitchen", "bin", "get rid", "rid", "stop", "bananas", "everywhere", "plague",
                "sink", "drain", "fruit", "bowl", "traps", "around", "how do i",
                # The noun with no kitchen word in the line: "there are flies in my house",
                # "a fly keeps landing on me", "flies all over the bedroom". The verb is fenced
                # by the guard below, so a place or an annoyance is enough here.
                "house", "home", "flat", "room", "rooms", "bedroom", "landing", "land", "lands",
                "on me", "keep", "keeps", "buzzing", "buzz", "swarming", "swarm", "air",
                "window", "windows", "in here", "indoors", "coming in")),
              "Put a little cider vinegar or red wine in a glass with a drop of washing-up liquid: they "
              "fly in and sink. Then take away what they are breeding in - the ripe fruit (into the "
              "fridge for a week), the bottles and the bin, and the plughole, which gets a kettle of "
              "boiling water at night. The glass catches the rest in a day or two.",
              # a suitcase that comes back damaged is not a fly in the kitchen: "how do i protect
              # my suitcase when flying" was reaching this card on "fly" + "how do i". The phrases
              # say "flying" without the bare word, because the matcher reads "fly" as that form of
              # it and "there is a fly in my kitchen" would lose the card (reviewer fair-orca).
              # A fly tip is a dumped mattress in a lay-by, and the council collects it: "how do i
              # report fly tipping" was told to put cider vinegar in a glass.
              avoid=("fly to", "flight", "flights", "when flying", "by plane", "on a plane",
                     "checked in", "suitcase", "suitcases", "luggage", "checked bag", "hold bag",
                     "holiday", "airport", "insect bite", "butterfly", "butterflies", "dragonfly",
                     "flight home", "fly tip", "fly tipping", "fly-tip", "fly-tipping", "tipping",
                     "tipped", "dumped", "dumping", "mattress", "lay-by", "fly poster",
                     # the fear of it is not a fly in the kitchen either: with the grief row's
                     # "get over" fenced off, "how do i get over a fear of flying" fell to this
                     # card and got cider vinegar, so the phrase is named here.
                     "fear of flying", "scared of flying", "afraid of flying",
                     # a zip fly is not an insect: "how do i put a zip fly in" got cider vinegar
                     # in a glass, because a fly is exactly what this row is about.
                     "zip", "zips", "zipper", "zippers", "zip fly",
                     # A plane, not a gnat, and the matcher reads "flying" as "fly": "im flying
                     # at 6am" got the cider vinegar, and the bare word cannot fence it off
                     # because "there is a fly in my kitchen" would lose its card with it. The
                     # phrase is the signal, so the phrases are what stand the row down.
                     "am flying", "flying at", "flying out", "flying home", "flying back",
                     "flying off", "flying from", "flying into", "flying tomorrow",
                     "flying next", "flying this", "flying in the morning", "flying on",
                     "fly out", "fly back", "fly home", "fly at", "flying with", "flying over",
                     "anxiety about flying", "nervous about flying",
                     # a kite is flown, not caught: the bare noun "fly" in this key answered
                     # "how do i fly a kite" with cider vinegar in a glass. entertainment.py's
                     # fly-a-kite row owns the kite lines.
                     "kite", "kites",
                     # a pet that flies with you is not a fly in the kitchen: "how do i fly with
                     # a dog" was told to put cider vinegar in a glass, and travel.py's
                     # pet-travel row is the answer
                     "dog", "dogs", "cat", "cats", "puppy", "puppies", "kitten", "kittens",
                     "pet", "pets", "rabbit", "ferret", "hamster", "parrot", "budgie"),
              # the verb is a shape, so the list of phrases above is no longer what holds it out
              guard=_the_fly_is_not_a_verb,
              report=True),
        entry("house-smell-nice",
              (("house", "flat", "home", "room", "living room", "hallway", "bedroom"),
               ("smell nice", "smell nicer", "smelling nice", "smell good", "smell fresh",
                "nice smell", "nicer smell", "fresh smell", "smell better", "nice scent", "fresh",
                "freshen", "smells", "smell", "smelly", "stinks")),
              "Open windows at both ends of the flat for ten minutes; that shifts more than anything you "
              "spray. Then wash the things that hold smell: bedding, cushions, the bath mat, the bin lid. "
              "Bicarbonate of soda on the carpet, left an hour and vacuumed, lifts stale air, and a pan "
              "of water with lemon peel and a cinnamon stick simmered for ten minutes does the rest. "
              "Air fresheners mask it; the fix is finding the source, often the bin, the drain or damp.",
              avoid=("damp", "musty", "mould", "mold", "drain", "gas", "burning", "smoke"),
              ask=("nice", "nicer", "fresh", "freshen", "home", "house", "flat", "bedroom")),
        entry("gutters",
              (("gutter", "gutters", "downpipe", "downpipes", "fascia"),
               ("clean", "cleaning", "blocked", "overflowing", "often", "leaves", "sagging", "drip")),
              "Twice a year, after the leaves fall and again in spring: scooped out by hand in gloves "
              "from a stable ladder, with the rubbish into a bag rather than down the drain. Then flush "
              "each downpipe with a hose to check it runs. If water still spills over the edge on a wet "
              "day, the run of the gutter has dropped or the downpipe is blocked at the bottom, not the top.",
              avoid=("buy", "cost", "install", "replace", "quote")),
        # "how do i fix a leaky gutter" was a shrug: the row above answers the cleaning and the
        # overflow, and its words are clean/blocked/overflowing, so a leak on a dry day matched
        # nothing. A leak in one place and water over the edge are two different repairs.
        entry("gutter-leak",
              (("gutter", "gutters", "downpipe", "downpipes", "fascia"),
               ("leak", "leaks", "leaky", "leaking", "drip", "dripping", "drips", "joint", "joints",
                "seal", "sealing", "sealant", "hole", "holes", "crack", "cracked", "fix", "repair",
                "water", "waterfall", "pouring")),
              "A leak is nearly always a joint or a hole, and it is a dry-day job: a leaking joint at "
              "the stop end or between two lengths is cleaned out, dried and sealed with gutter "
              "sealant; a hole or crack is covered with a self-adhesive flashing strip pressed on "
              "over a clean, dry surface, which lasts a few years. Before any of that, check the "
              "downpipe is not blocked - water backing up finds the weakest joint and pours out "
              "there - and re-clip a run that has sagged so it falls towards the downpipe, about "
              "1cm in 3 metres. Never do it off a ladder in the wind or on your own: a ladder on "
              "wet ground is the fall that puts people in hospital.",
              avoid=("clean", "cleaning", "clear", "clear out", "scoop", "leaves", "blocked",
                     "overflowing", "cost", "costs", "price", "quote", "install", "replace",
                     "new gutters")),
        # A fence that came down in the wind is one of the commonest winter questions in the whole
        # home domain and it reached nothing: "my garden fence is falling down" and "my fence post
        # has rotted" both had a shrug, "how do i fix a fence panel that blew down" was turned down
        # honestly, and "how do i stop my fence blowing down again" was read as a letter to a friend.
        # The repair, the windproofing and the rotten post are three answers, so they are three rows.
        entry("fence-repair",
              (("fence is falling down", "fence has fallen down", "fence fell down", "fence blew down",
                "fence has blown down", "fence panel", "fence panels", "broken fence",
                "fence is broken", "fence is leaning", "wobbly fence", "fence is wobbly",
                "fence post", "fence posts", "post has rotted", "posts have rotted",
                "fence is sagging", "fence sagging", "fence has sagged",
                "gate is hanging", "gate has dropped"),
               ("fence", "garden", "wind", "storm", "repair", "fix", "replace", "rotten", "rotted",
                "concrete", "blown", "fell", "leaning", "gate", "put back", "again")),
              "A panel that came out in the wind is usually a post that has moved, not the panel, so "
              "check the posts are upright with a spirit level before you fix it back: a new panel on "
              "a rotten post goes over again. Replace a rotted post base with a concrete repair spur, "
              "or set a new post 600mm into the ground in Postcrete, and brace it until it is solid.",
              avoid=("cost", "quote", "how much", "neighbour", "neighbor", "who owns", "boundary",
                     "fence paint", "paint it", "stain", "creosote",
                     # a depth is a fourth fence question and has its own row below: without these,
                     # "how deep should fence posts go" read as a repair on the words "fence posts"
                     "deep", "depth", "deep enough", "foot down", "feet down")),
        # "how deep should fence posts go" and "ive buried the posts about two foot down, is that deep
        # enough" reached nothing at all: the repair, treating and height rows each answer a fence
        # line, and none of them says how deep the hole is. The line usually has no fault word in it,
        # because nothing has gone wrong yet, so the depth ask is the row's own key.
        entry("fence-post-depth",
              (("how deep", "deep enough", "deep should", "deep do", "deep to", "deep for",
                "depth", "how far down", "how far in", "foot down", "feet down", "two foot",
                "2 foot", "two feet", "2 feet", "three foot", "3 foot", "three feet",
                "buried", "in the ground", "into the ground", "how much of"),
               ("fence post", "fence posts", "gate post", "gatepost", "pergola post",
                "deck post", "deck posts", "posts", "post", "fence", "fencing", "pergola")),
              "About a third of the post in the ground: 600mm (two foot) under a standard 1.8m panel, "
              "and 750 to 900mm on an exposed, windy corner or in sandy soil. Two foot is enough if "
              "the hole is about 250 to 300mm across and set in Postcrete or a 3:1 ballast and cement "
              "mix, with the concrete sloping away from the post so water runs off - check it plumb "
              "before the mix goes off, because a post only 300 to 400mm down leans within a winter.",
              # the depth words are the ask as well as the subject: a line about a post with no depth
              # in it belongs to the repair, treating or height row
              ask=("how deep", "deep enough", "deep should", "deep do", "deep to", "deep for",
                   "depth", "how far down", "how far in", "foot down", "feet down", "buried",
                   "in the ground", "into the ground", "how much of"),
              bias=1,
              avoid=NOT_A_FENCE_JOB + (
                     "post office", "post a letter", "parcel", "delivery", "mail",
                     "letter", "blog", "job", "position", "apply", "applying", "instagram",
                     "facebook", "comment", "review", "how tall", "how high", "planning",
                     "max height", "boundary", "who owns", "whose", "who pays", "my neighbour",
                     "my neighbor", "cost", "costs", "price", "prices", "quote", "cheapest",
                     "treat", "treating", "stain", "staining", "paint", "painting",
                     "preserver", "creosote", "blew down", "blown down", "fell down",
                     "repair", "replace", "rotten", "rotted", "wobbly", "loose", "leaning",
                     "hanging", "plant", "plants", "bulb", "bulbs", "seed", "seeds",
                     "grave", "graves", "coffin", "ashes",
                     # old posts taken to the tip are rubbish, not a hole to get right
                     "the tip", "to the tip", "tip run", "rubbish", "skip", "landfill", "dispose",
                     "disposing", "instead of", "dumping", "get rid")),
        # The other half of a new fence: the depth row above answers "how deep", and the lines about
        # putting the post in the hole at all were reaching the repair answers. "how do i set a fence
        # post straight" and "should i put gravel in the bottom of a fence post hole" were both told
        # that "a panel that came out in the wind is usually a post that has moved", and "how much
        # postcrete do i need per fence post" was quoted the price of a fence.
        entry("fence-post-set",
              (("set a fence post", "set the post", "set a post", "set a new post",
                "set", "setting", "put up", "putting up", "install", "installing", "erect",
                "erecting", "fit", "fitting", "concrete", "concreting", "concreted",
                "concrete a fence post", "concrete it in", "concrete the post",
                "postcrete", "cement", "dig", "digging", "hole", "gravel", "ballast",
                "put gravel", "gravel in the bottom", "gravel in the hole", "bottom of the hole",
                "plumb", "straight", "level", "brace", "bracing", "how many bags",
                "how much postcrete", "how much concrete", "help it stand"),
               ("fence post", "fence posts", "gate post", "gatepost", "deck post", "posts",
                "post", "fence", "fencing", "panel", "panels")),
              "Dig the hole 250 to 300mm across and two foot (600mm) deep, stand the post on about "
              "50mm of gravel so the cut end never sits in water, and get it plumb on two faces with "
              "a spirit level before anything goes in. One 20kg bag of Postcrete does one post: pour "
              "it dry around the post, water it as the bag says, brace the post and leave it a day "
              "before a panel goes on. A 100mm square or 75mm round post is right for a 1.8m panel; "
              "in soft soil, or on a windy corner, go deeper rather than wider.",
              bias=1,
              avoid=NOT_A_FENCE_JOB + (
                     "post office", "post a letter", "parcel", "delivery", "mail", "letter",
                     "blog", "job", "position", "apply", "applying", "instagram", "facebook",
                     # "the neighbour put up a fence and i dont like it" is a boundary row's line
                     "neighbour", "neighbor", "next door",
                     # a lamp post, a sign post and a post box are other things with "post" in them:
                     # "how do i fit a lamp post in the garden" was a hedge on main and got the fence
                     # post's hole here until these were named
                     "lamp post", "lamppost", "lamp", "post box", "postbox", "goal post",
                     "goalpost", "sign post", "signpost", "postcard", "postcard", "postcode",
                     "post code", "carrier", "courier",
                     "comment", "review", "how tall", "how high", "planning", "boundary",
                     # the limit said as a measurement is the height row's: "can i put up a fence 2
                     # metres high" is not a hole to dig
                     "metres high", "metre high", "metres tall", "metre tall", "feet high",
                     "foot high", "2 metres", "2m high", "six foot", "height limit",
                     "who owns", "whose", "who pays", "my neighbour", "my neighbor", "cost",
                     "costs", "price", "prices", "quote", "cheapest", "treat", "treating",
                     "stain", "staining", "paint", "painting", "preserver", "creosote",
                     "blew down", "blown down", "fell down", "repair", "replace", "rotten",
                     "rotted", "rot", "rotting", "wobbly", "loose", "leaning", "sagging",
                     "plant", "plants", "bulb", "bulbs", "ashes",
                     "the tip", "to the tip", "rubbish", "skip", "instead of", "get rid",
                     "how far apart", "spacing", "spaced", "centres", "centers",
                     "how deep", "depth", "deep enough", "foot down", "feet down")),
        # How far apart, which the hole and the depth say nothing about: the answer is the centres.
        entry("fence-post-spacing",
              (("how far apart", "how far between", "spacing", "spaced", "centres", "centers",
                "distance between", "how many posts", "how many panels", "how wide"),
               ("fence post", "fence posts", "posts", "post", "fence", "fencing", "panel",
                "panels", "gate post", "gate")),
              "Fence posts go 1.8m apart, centre to centre, for a standard 1.8m (6ft) panel, and 2.4m "
              "for a 2.4m panel - a gravel board and a panel are sold to that width, so measure the "
              "panel before you dig. On a slope, keep the tops level and let the bottom of each panel "
              "follow the ground, stepped one post at a time rather than raked.",
              bias=1,
              avoid=NOT_A_FENCE_JOB + (
                     "post office", "post a letter", "parcel", "delivery", "mail", "letter",
                     "lamp post", "lamppost", "lamp", "post box", "postbox", "goal post",
                     "goalpost", "sign post", "signpost", "postcard", "postcode", "post code",
                     "blog", "job", "position", "apply", "cost", "costs", "price", "quote",
                     "treat", "treating", "stain", "paint", "painting", "how tall", "how high",
                     "planning", "boundary", "who owns", "whose", "how deep", "depth",
                     "deep enough", "how far down", "buried", "in the ground", "repair",
                     "replace", "rotten", "rotted", "wobbly", "loose", "leaning")),
        # "how thick should a fence post be" and "what size fence post do i need" both came back
        # with the panel-repair answer, because the only thing the fence rows had for a post was
        # something going wrong with one. The size is a fact about a post, not about a repair.
        entry("fence-post-size",
              (("how thick", "how big", "what size", "which size", "what width", "how wide",
                "whats the best fence post", "best fence post", "best post", "what post",
                "which post", "what sort of post", "what kind of post", "what timber",
                "4 inch", "four inch", "3 inch", "three inch", "100mm", "75mm", "125mm",
                "square or round", "round or square", "concrete or wooden post"),
               ("fence post", "fence posts", "gate post", "gatepost", "deck post", "posts",
                "post", "fence", "fencing", "panel", "panels", "gate")),
              "A 100mm (4 inch) square post carries a 1.8m panel, and 75mm round is enough for a "
              "light closeboard fence; a gate wants a 125 to 150mm post of its own, not a panel post "
              "with a gate hung on it. Buy posts marked for ground contact (UC4) rather than plain "
              "treated timber, because a post rots at the soil line, and on an exposed corner a "
              "concrete post outlasts wood.",
              bias=1,
              avoid=NOT_A_FENCE_JOB + (
                     "post office", "post a letter", "parcel", "delivery", "mail", "letter",
                     "lamp post", "lamppost", "lamp", "post box", "postbox", "goal post",
                     "goalpost", "sign post", "signpost", "postcard", "postcode", "post code",
                     "blog", "job", "position", "apply", "applying", "cost", "costs", "price",
                     "prices", "quote", "how many do i need", "how far apart", "spacing",
                     "how deep", "depth", "deep enough", "how far down", "buried",
                     "in the ground", "dig", "digging", "hole", "concrete in", "postcrete",
                     "repair", "replace", "fix", "rotten", "rotted", "wobbly", "loose",
                     "leaning", "blew", "blown", "fell", "fallen", "treat", "treating",
                     "stain", "paint", "painting", "how tall", "how high", "planning",
                     "boundary", "who owns", "whose", "my neighbour", "my neighbor")),
        # "how do i paint a fence" was turned down honestly. The answer is a day's work with one
        # method, and the fence it is asked about is usually the one the row above has just mended.
        entry("fence-paint",
              (("fence", "fences", "fence panels", "shed", "garden gate"),
               ("paint", "painting", "paint it", "stain", "staining", "treat", "treating",
                "treatment", "creosote", "preserver", "preservative", "protect", "weatherproof")),
              "Clean it and let it dry: paint on a dirty or damp fence flakes within a year. Brush or "
              "spray a water-based fence stain rather than a film-forming paint, two coats on a dry day "
              "above 10C, keeping the bottom of the panel clear of the soil. A shed wants an oil or "
              "wood preserver, not a fence stain.",
              avoid=("neighbour", "neighbor", "boundary", "cost", "how much", "blew down", "rotted",
                     "fallen", "leaning", "replace")),
        entry("fence-windproof",
              (("stop my fence blowing down", "fence keeps blowing down", "fence blowing down again",
                "blown down every", "windproof", "wind proof", "keep the fence up"),
               ("fence", "fences", "garden", "wind", "storm", "gale", "again", "strong")),
              "A solid fence is a sail, so the wind pulls on the posts rather than passing through: "
              "slatted panels, or a gap under the gravel board, let it through. Set the posts 600mm "
              "into the ground in concrete, keep the panel out of the soil, and brace the end posts. A "
              "trellis strip along the top takes most of the load off a windy corner."),
        # "my patio slabs are loose" had the "I'm listening" line: a rocking slab is a bedding
        # question with a method, and it is the same answer for paving, setts and a step.
        entry("patio-slab-loose",
              (("patio slab", "patio slabs", "paving slab", "paving slabs", "slab", "slabs",
                "paving", "patio", "paving stones"),
               ("loose", "wobble", "wobbles", "wobbly", "rocking", "rocks", "sunken", "sunk",
                "cracked", "moved", "lift", "relay", "re-lay", "dip", "uneven")),
              "Lift the slab, scrape off the old bedding and re-bed it on 30 to 40mm of 5:1 sharp sand "
              "and cement, tapping it level with its neighbours with a rubber mallet and checking with "
              "a straight edge. A slab that rocks after rain is usually a hollow bed or ants. Point the "
              "joints with dry sand and cement, not soil, and leave it a day."),
        # The mix for a paving bed had no row of its own: "how much sand and cement do i need to lay
        # a patio" was "I don't know enough to answer that honestly", "what mix do i use to lay patio
        # slabs" was the same shrug, "how much mortar do i need for a patio" was the gravel volume
        # sum (a bag of sand read as a tonne of gravel) and "how much sand and cement per square
        # metre of paving" was the area formula. A bagged mix is not a volume of fill, so the
        # quantities are per square metre of bed here and per brick and block next door: same sum,
        # different sums to know.
        entry("bricklaying-mortar",
              (("mortar", "mortar mix", "sand and cement", "building sand and cement",
                "cement", "cement mix", "cement and sand", "what mix", "what ratio", "mix ratio",
                "mix do i use", "mix should i use", "how much sand", "how much cement",
                "how many bags of sand", "how many bags of cement", "bags of sand",
                "bags of cement", "5 to 1", "5:1", "4 to 1", "4:1"),
               ("brick", "bricks", "bricklaying", "brickwork", "block", "blocks", "blockwork",
                "breeze block", "breezeblock", "cinder block", "wall", "walls", "garden wall",
                "render", "rendering", "pointing", "repointing", "re-point", "point the",
                "screed", "floor", "slab of concrete", "concrete base", "footing", "footings")),
              "Bricklaying mortar is 5:1 building sand to cement, or 4:1 for a wall that takes the "
              "weather, mixed soft and buttery rather than wet. A 25kg bag of cement with five bags of "
              "building sand lays roughly 150 bricks or 40 blocks, so measure the wall first - a 10m "
              "single-skin wall 1m high is about 600 bricks. Pointing and rendering are both a 4:1 "
              "mix, and a footing or a small concrete base is 6 parts ballast to 1 of cement.",
              avoid=("cost", "costs", "price", "prices", "cheap", "cheapest", "expensive",
                     "how much is", "how much does", "how much would", "quote", "quotes",
                     "which", "what type", "what sort", "best type", "what colour", "what color",
                     "how many bricks", "how many blocks", "many square metres",
                     "how do i lay", "how to lay", "clean", "cleaner", "stain", "stains",
                     "algae", "moss", "seal", "sealer", "paint", "render crack", "cracked",
                     "patio", "paving", "paving slab", "paving slabs", "flag", "flags",
                     "flagstone", "flagstones", "setts", "joints", "paving joints",
                     "mixer", "hire", "borrow", "wheelbarrow", "shovel", "board",
                     "how long", "how deep", "how thick", "depth", "thickness", "cure", "dry",
                     "damp", "damp proof", "insulation", "cavity", "lintel", "planning",
                     # as above: a set mix that has to come off is a cleaning row's line
                     "get off", "getting off", "off a", "off the", "off my", "off bricks",
                     "off the wall", "off walls", "remove", "removing", "removal", "scrub",
                     "scrubbing", "pressure washer", "jet wash", "stubborn"),
              bias=1),
        # Blocks are not the patio's bed: a block-paved drive or patio goes down on sharp sand
        # alone, compacted, with kiln-dried sand brushed into the joints - no cement in the bed at
        # all. On main "how much mortar for 20 square metres of block paving" was the patio's
        # price card and "how much sharp sand and cement for a block paved drive" was the slab
        # bed, which is the wrong mix for the job by 5 parts sand to 1.
        entry("block-paving-bed",
              (("block paving", "block paved", "block paver", "block pavers", "paving blocks",
                "driveway blocks", "setts", "block paving drive", "paved drive", "paving the drive"),
               ("sand", "cement", "mortar", "mix", "much", "need", "how much", "how many",
                "bed", "bedding", "joint", "joints", "brush in", "kiln dried", "kiln-dried",
                "how deep", "depth", "wacker", "compact")),
              "Blocks are not bedded on sand and cement: they go down on 30 to 40mm of sharp sand "
              "alone, compacted with a wacker plate, and the joints are brushed full of kiln-dried "
              "sand afterwards, so there is no cement to measure at all. For 20 square metres "
              "reckon on about a tonne of sharp sand for the bed and two or three 25kg bags of "
              "kiln-dried sand for the joints, plus an edge restraint on every open side, which is "
              "the part that stops the blocks spreading.",
              # a price, the laying method, a slab, a cleaning job and a wall are other rows
              avoid=("cost", "costs", "price", "prices", "cheap", "cheapest", "expensive",
                     "how much is", "how much does", "how much would", "quote", "quotes",
                     "which", "what type", "what sort", "best type", "what colour", "what color",
                     "how do i lay", "how to lay", "laying", "lay the blocks", "do i lay",
                     "clean", "cleaner", "stain", "stains", "algae", "moss", "weeds", "weed",
                     "seal", "sealer", "slippery", "oil", "paint", "get off", "getting off",
                     "off a", "off the", "off my", "remove", "removing", "removal", "scrub",
                     "patio slab", "paving slab", "paving slabs", "flag", "flags", "flagstone",
                     "wall", "walls", "brick", "bricks", "brickwork", "render", "rendering",
                     "screed", "floor", "concrete base", "footing", "footings", "mixer", "hire"),
              bias=3),
        entry("too-much-rubbish",
              (("bin", "bins", "rubbish", "trash", "garbage", "wheelie", "wheelie bin", "bin bag",
                "bin bags", "recycling", "waste"),
               ("always", "overflowing", "overfull", "too much", "every week", "each week", "full",
                "loads", "so much", "less", "reduce", "cut down", "keep filling")),
              "Most of it is air and packaging: flatten cartons, crush cans and squash bottles with the "
              "lid off, and the same bag holds twice as much. Put a smaller bin by the counter and take "
              "it out every night rather than waiting for the big one to fill, and keep a caddy beside "
              "it for peelings, which is often a third of the weight. Then buy the biggest pack you will "
              "actually use, loose veg instead of trays, and one refill bottle instead of a new one. If "
              "the wheelie bin is full by day five, half of what is in it belongs in the recycling.",
              avoid=("smell", "smells", "smelly", "stink", "stinks", "bin day", "collection",
                     "collected", "council", "where do i take", "tip",
                     "dump", "neighbour", "neighbor", "next door", "compost", "garden", "food caddy",
                     "seagull", "fox", "rat", "mouse", "mice", "broke", "broken", "lid", "lock",
                     "when is", "what day",
                     # "waste" is this row's noun for rubbish, but it is also a verb, and the
                     # thing it is done to decides who answers: "i waste so much money every
                     # month" and "i am wasting so much gas" were both the flatten-the-cartons
                     # answer, because the key holds "waste" and the other half holds "so much".
                     # The object of the verb stands this row down: money is money.py's
                     # question, the fuels are the energy bill's, and food is the food-waste row's.
                     "money", "wages", "cash", "salary", "payday", "food", "groceries",
                     "time", "water", "electricity", "energy", "gas", "fuel", "petrol",
                     "paint", "wood", "ink", "data", "battery", "heat")),
        # "the bin needs emptying" was answered "right-click the Recycle Bin on the desktop": the
        # word `bin` was the whole reading, and the bin in that sentence is the one under the sink.
        # The technology table reads the machine words out of a line before either row answers, and
        # its row stands down on exactly this reading, so this is the everyday bin's answer.
        entry("empty-the-kitchen-bin",
              (("bin", "bins", "wheelie bin", "kitchen bin", "bin bag", "bin bags", "bin liner",
                "rubbish", "trash"),
               ("empty", "emptied", "emptying", "needs emptying", "need emptying",
                "needs taking out", "need taking out", "wants taking out", "clear", "clearing",
                "cleared", "empty it")),
              "Tie the bag at the top and take it straight out to the wheelie bin: a tied bag left "
              "by the door still smells, and the bin is what wants emptying, not the kitchen. While "
              "it is empty, wipe the inside with hot soapy water and a splash of bleach, let it dry, "
              "then fit the liner before anything goes back in - that once-a-week wipe is what keeps "
              "the flies off in summer. A bag that split on the way out wants a rinse in the garden "
              "rather than a scrub, and the wheelie bin gets the same wash twice a year.",
              guard=lambda read: not the_bin_is_on_a_machine(read),
              # The rows that own the bin's other questions keep them: the bins going out, a letter
              # to the council, a missed collection, a bin too small for the kitchen, and the bin on
              # a computer. A chore said as done or handed over ("i put the bins out") is a line to
              # agree with, not a method to explain, so it is fenced too.
              avoid=("row", "rows", "argument", "argue", "arguing", "flatmate", "housemate",
                     "landlord", "neighbour", "neighbors", "council", "collected", "collection",
                     "missed", "write", "letter", "report", "small bin", "tiny", "too small",
                     "put the bins out", "put the bin out", "put them out", "put it out",
                     "i emptied", "ive emptied", "i took the", "ive taken", "already emptied",
                     "already done", "did it")),
        # The visit length is the answer a how-long line asks for, and the service row above answers
        # with the yearly interval and the price: "how long does a boiler service take" got "once a
        # year, £60 to £120", which is the right topic and the wrong shape.
        entry("boiler-service-duration",
              (("boiler", "boilers", "combi", "gas boiler"),
               # The clock asks, not a list of sentences: "how long does it take to service a
               # boiler", "how long to get the boiler serviced" and "how long will the service
               # take" were all reading past the sentence list above to the yearly-interval
               # row, which is the right topic and the wrong shape. The service words have to
               # be in the line too, so a boiler's life and a boiler's price are not this row.
               ("how long", "how many hours", "how much time", "long does", "long will",
                "how long to", "length of")),
              "About an hour for a straightforward boiler, and up to ninety minutes if it is the "
              "first service in a while or the engineer has to check the flue and the safety "
              "devices. It is a set of checks rather than a strip-down: they run the boiler, test "
              "the flue and the gas pressure, clean what they can reach, and leave you the service "
              "record. Book it for late summer if you can, because the wait is longer once the cold "
              "weather starts.",
              # A boiler's life, its price, its yearly interval and a new one going in are all
              # other rows: this one is the length of the visit.
              avoid=("cost", "price", "much", "worth", "worthwhile", "often", "annual", "yearly",
                     "new", "install", "installation", "replace", "fit", "fits", "fitted",
                     "fitting", "life", "lifespan", "good for",
                     "how many years", "years", "bleed", "pressure", "broken", "fault",
                     # a repair has its own row, with the engineer's visit length in it
                     "repair", "repairs", "repairing", "fix", "fixes", "fixing",
                     # a boiler that is doing something is a fault the talk is on, not a visit
                     # to book: "my boiler is making a noise" then "how long will it take" was
                     # told the length of a service
                     "noise", "noisy", "banging", "rumbling", "knocking", "whistling", "hissing",
                     "leak", "leaks", "leaking", "hot water", "not heating")
              # "how long have i had the boiler now" is the age of the boiler, not the length of
              # the visit, so the possession shape stands this row down too.
              + A_AGE_OWNED,
              # "how long does a boiler service last" is the visit and "how long does a boiler
              # last" is its life, so the row asks for the service word as well as the clock:
              # without it, dropping "last" from the avoid list would take the lifespan line.
              ask=("service", "services", "serviced", "servicing"),
              bias=3),

        entry("boiler-service",
              ("boiler", ("service", "servicing", "serviced", "annual", "yearly", "every year",
                          "certificate", "cost", "much", "price", "landlord")),
              "Once a year, yes: a gas boiler service is usually \u00a360 to \u00a3120 depending on "
              "where you are. It keeps the warranty valid, catches a failing part before it strands "
              "you in winter, and landlords are legally required to have one. Book it in late "
              "summer, when engineers are quiet and the price is lower.",
              avoid=("new", "install", "installation", "replace", "replacement", "buy"),
              ask=("service", "servicing", "serviced", "annual", "yearly", "certificate", "cost",
                   "much", "price", "often")),

        # "can i service my own boiler" and "is it legal to service the boiler" are the same job
        # asked as permission, and a price never answers it: the gas side is Gas Safe work, and
        # what is left for the person is the bit around it.
        entry("boiler-service-diy",
              (("boiler", "boilers", "combi", "gas boiler"),
               BOILER_DIY + ("can i service", "service my own", "service it myself",
                             "service the boiler myself", "legal to service")),
              ("Not the service itself: it means opening the case and checking the gas side, and "
               "a gas boiler is Gas Safe work by law, so the annual service is an engineer's job "
               "at about \u00a360 to \u00a3120. Yours is the bit around it: keep the pressure "
               "at 1 to 1.5 bar, keep the flue and the vents clear, bleed the radiators - and the "
               "warranty usually needs the engineer's service anyway."),
              # a price or an interval with no "own" or "legal" in it is the yearly-service row's
              avoid=("new boiler", "install", "buy"),
              bias=4,
              ask=BOILER_DIY + ("service", "servicing", "serviced", "annual", "yearly"),
              guard=_an_ask_about_servicing_my_own),

        # The stain and the money word together, and never one without the other: with only "stain" it
        # is a cleaning question, and with only "letting agent" it is the agent asking about the boiler.
        entry("damage-deduction",
              (("stain", "stains", "stained", "mark", "marks", "damage", "damaged", "scuff", "scuffs",
                "burn", "burns", "chip", "chips"),
               ("letting agent", "landlord", "landlords", "deduct", "deducted", "deducting", "deduction",
                "deductions", "withheld", "withhold", "withholding", "wear and tear", "deposit",
                "refund", "end of tenancy")),
              ("Ask in writing for an itemised list of what was taken and why, and say which deductions "
               "you disagree with. Fair wear and tear - a carpet going thin where you walk, a worktop "
               "faded by sunlight - is not chargeable; a burn or a paint mark is. If the deposit went "
               "into a protection scheme, use its free dispute service rather than arguing with the "
               "agent, and keep the photos from the day you moved in."),
              bias=1),

        entry("deposit-back", (("deposit", "deposits", "deposit scheme", "tenancy deposit",
                                "holding deposit", "security deposit", "damage deposit",
                                "deposit protection", "deposit protection scheme"),
                               ("back", "returned", "return", "not", "unfair", "withheld", "landlord",
                                "landlords", "claim", "getting", "move out", "moved out",
                                "moving out", "end of tenancy", "tenancy", "renting", "rented",
                                "letting agent", "deductions", "deducted", "deducting",
                                # "can i get my money back from a deposit scheme" asks for the
                                # money without the word back, so the money is the second half
                                "money", "money back", "get it", "how do i get")),
              ("Ask in writing for an itemised list of what was taken and why, and say which of the "
               "deductions you disagree with. If your deposit was in a protection scheme, use its free "
               "dispute service rather than arguing with the landlord; you can also raise it with the "
               "council. Photos from the day you moved in are the evidence that wins this."),
              # the scheme's own letter is rent-deposit's question ("a deposit protection
              # scheme says i owe money" was the itemised list), so the things that letter says
              # keep this row off it
              avoid=("flat", "house", "saving", "save", "rent", "buy", "first home",
                     "says i owe", "they say i owe", "say i owe", "owe money", "i owe"),
              # a scheme, a tenancy and a landlord are all this row's words, so when they are
              # there the row answers over the booking deposit and the chargeback
              bias=3),

        # How much laundry a drum takes: a size question, which the fault rows below cannot answer.
        entry("washing-machine-size",
              (("washing machine", "washer", "washer dryer", "tumble dryer", "dryer", "drum",
                "drum size",
                # the figure on the box is the other way people name the thing: "is 7kg enough
                # for two people" has no word for the machine in it at all
                "7kg", "8kg", "9kg", "10kg", "11kg", "12kg"),
               ("size", "sizes", "sized", "capacity", "kg", "kgs", "kilo", "kilos", "kilogram",
                "kilograms", "litre", "litres", "liter", "liters", "big", "bigger", "biggest",
                "big enough", "how big", "what size", "how many kg", "how much can", "enough",
                # choosing between two: "9kg or 10kg washing machine" is the same size question
                "or 7kg", "or 8kg", "or 9kg", "or 10kg", "or 11kg", "or 12kg")),
              "Roughly: 7kg for one or two people, 8kg for three, 9kg for four and 10 to 12kg if you "
              "wash duvets and bedding in it. The figure is the dry weight of a full load, so a 9kg "
              "drum is not gentler, it just holds more; a bigger one costs more to run per wash but "
              "you run it less often. Measure the gap and the doorway first, because depth is what "
              "usually rules a machine out, and match the dryer to the washer or slightly bigger "
              "than it.",
              # a machine that will not spin, or one that has packed in, is a fault and not a size
              avoid=("wont spin", "won't spin", "not spinning", "no spin", "wont turn", "won't turn",
                     "spin cycle", "soaking", "soaking wet", "still wet", "dripping", "wringing",
                     "wont drain", "won't drain", "packed in", "broke", "broken", "faulty",
                     "leaking", "smell", "smells", "smelly", "noise", "noisy", "banging", "hot",
                     "overheating", "not heating", "wont heat", "won't heat", "wont start",
                     "won't start", "error", "door", "locked", "buy", "buying", "worth it",
                     "cheap", "cheapest", "best", "which one", "recommend",
                     # a weight in kilos is only a laundry size when the line is about laundry:
                     # "is a 2kg joint enough for six" is the roast, and a bag of compost is a bag
                     "turkey", "chicken", "lamb", "beef", "pork", "joint", "roast", "compost",
                     "potatoes", "spuds", "dumbbell", "dumbbells", "barbell", "weights",
                     "suitcase", "luggage", "package", "parcel", "barbecue", "bbq"),
              # The other thing a washer is: a tap washer, a bolt's washer. "what size washer do i
              # need for a 15mm tap" is a size question, so it matched "size" and "washer" and
              # was told how many kilos a drum holds. Plumbing and fixing words stand this row
              # down unless the line also names the machine.
              guard=_not_a_washer_of_another_kind),
        # "how long does a tenancy deposit scheme take to return" was answered with the card about
        # arguing with deductions, which is the other deposit question: this one wants the number
        # of days, and where that number comes from.
        entry("deposit-return-days",
              (("deposit", "tenancy deposit", "deposit scheme", "protection scheme",
                "deposit protection"),
               ("how long", "how many days", "how many weeks", "how soon", "take", "takes",
                "wait", "waiting", "when")),
              ("Ten days is the rule: the deposit has to come back within ten days of the day you "
               "and the landlord agree the amount, and interest can come with it. If you have not "
               "agreed, the landlord has to return the undisputed part within those ten days and "
               "put in a claim for the rest, and a disputed amount goes to the protection scheme, "
               "whose free dispute service usually decides within 28 days. So ask the scheme which "
               "one holds your money, and chase the agent in writing, because the deadline is "
               "counted from the agreement and not from the day you moved out."),
              bias=2,
              # "back to the deposit, how long will it take" is a saver asking how long the
              # saving takes, not a tenant waiting for money back, so the line has to name the
              # tenancy, the scheme or the landlord: see _a_deposit_coming_back.
              guard=_a_deposit_coming_back,
              avoid=("save", "saving", "savings", "put away", "towards", "a month",
                     "each month", "per month", "afford", "first home", "first time",
                     "house", "flat", "moving", "move", "mortgage", "buy", "rent",
                     "renting", "damage", "damaged", "unfair", "withheld", "deduct",
                     "deductions", "cleaning", "checkout", "inspection")),

        # --- a machine that will not spin, a hoover with no pull, a pilot light ---
        entry("washing-machine-spin",
              (("washing machine", "washer", "washer dryer",
                # People describe the fault by what comes out of it rather than by the machine: "the
                # clothes come out soaking wet" never says washer at all, and both words below are
                # only this question when the outcome words beside them say "out of a wash".
                "clothes", "washing", "wash load", "laundry"),
               ("wont spin", "won't spin", "not spinning", "no spin", "wont turn", "won't turn",
                # the same fault in the present tense people actually type: "the washing machine
                # isnt spinning" reached the listening turn, and "the drum isnt turning" too,
                # because only the "not"/"won't" forms were keyed here.
                "isnt spinning", "isn t spinning", "aint spinning", "isnt turning",
                "isn t turning", "isnt going round", "drum isnt turning", "drum not turning",
                "drum", "spin cycle", "spin only", "to spin", "get it to spin",
                "clothes are wet", "clothes come out wet", "soaking", "soaking wet",
                # the outcome said a dozen other ways: still wet, wrung out by hand instead, dripping
                # in the basket, and the machine that "leaves" them wet rather than not spinning
                "wringing wet", "wringing", "still wet after", "still wet when", "sopping",
                "sopping wet",
                "dripping wet", "come out wet", "comes out wet", "come out soaking",
                "comes out soaking", "come out dripping", "comes out dripping", "come out wringing",
                "comes out wringing", "wet after the wash", "wet after a wash",
                "wet after washing", "wet after wash", "come out still wet",
                "comes out still wet", "leaves the clothes wet", "leaves clothes wet",
                "leaves them wet", "leaves it wet",
                # "my washing machine is leaving the clothes soaking" is the same outcome said
                # as it happens, and the leaving form is how people put it
                "leaving the clothes", "leaving clothes", "leaving them", "leaving it",
                "leaving my clothes", "left the clothes", "left clothes",
                # A machine that stops mid-cycle is not this row's question: the door latch and
                # the blocked drain are the answer to it, and this key's "stopped halfway" phrases
                # only took it away from that row once the bias below put this one in front.
                )),
              "One heavy thing is the usual cause: a duvet or a bath mat balls up on one side and the "
              "machine refuses to spin, so shake it flat and run a spin only cycle. Still soaked? Clear "
              "the filter behind the kick plate, because a machine that can't drain won't spin. On an "
              "older machine the belt can slip off, which is a cheap part.",
              # a drum that will not turn is a spin fault; a door that will not open is the door entry,
              # a smell is its own entry, and a squeak or a bang under "spins" is the noise question
              # A drum with a *size* is a capacity question, not a fault: "what size drum for a
              # washing machine", "does a bigger drum wash better" and "washing machine drum size
              # for duvets" were all told a duvet had balled up on one side, because the word
              # "drum" is the only thing in them the row knew. The capacity row below answers them.
              avoid=("buy", "which", "best", "door", "doors", "locked", "lock", "wont open",
                     "size", "sizes", "sized", "drum size", "capacity", "kg", "kgs", "kilo",
                     "kilos", "kilogram", "kilograms", "litre", "litres", "liter", "liters",
                     "big", "bigger", "biggest", "big enough", "how big", "how many kg",
                     "7kg", "8kg", "9kg", "10kg", "11kg", "12kg", "how much can",
                     "won't open", "smell", "smells", "smelly", "musty", "leak", "leaking",
                     "noise", "noisy", "loud", "squeak", "squeaks", "squeaking", "squeal",
                     "squeals", "squealing", "grind", "grinds", "grinding", "bang", "bangs",
                     "banging", "rattle", "rattles", "rattling", "knock", "knocks", "knocking",
                     "whine", "whining",
                     # a load hung out in the rain, or a wet room, is not a spin fault: the outcome
                     # words only count when the line is about what the machine did
                     "rain", "rained", "raining", "rainy", "weather", "storm", "puddle", "puddles",
                     "leak", "leaks", "leaking", "wet room", "wet wipes", "wet wipe",
                     "marks", "mark", "stains", "stain", "black marks", "dark marks", "streaks",
                     # a drum that is hot or overheating is the machine-hot row in home.py, not a
                     # spin fault: "the drum of my washer is hot" is not a duvet balled on one side
                     "hot", "warm", "overheating", "overheated", "burning",
                     "smell of burning",
                     # water that will not leave the drum is the filter and the drain, which is a
                     # different check from a load that came out too wet, and its own card answers
                     # it: this row took "water is sitting in the drum of my washing machine" as
                     # soon as the bias below was raised
                     "sitting", "standing", "sitting water", "standing water", "water sitting",
                     "water standing", "wont drain", "won't drain", "not draining", "didnt drain",
                     "didn't drain", "wont empty", "won't empty", "not emptying"),
              # The outcome lines are this row's own question and `dry-inside` was answering them
              # with a drying rack: it keys on the same wet words and carried the same score with
              # bias 2, so "the clothes come out soaking wet" was told how to hang a load. Two
              # points puts the machine's own fault back in front of it, which is what
              # tests/test_a_wet_load_is_not_a_mark.py has been asserting all along.
              bias=2),

        # A dryer that will not heat, or takes three goes to dry a towel, is one fault with one
        # cause in most homes: the air cannot get through or the heat is not being asked for. There
        # was no entry for it at all, so "i cant get my dryer to heat up" fell through to the chat
        # module ("That would bother me too") and "my dryer takes ages to dry" was answered
        # "Is there anything you'd like a hand with?".
        # A hob that is slow, and a ring that has stopped, had no answer: "my hob is slow to heat",
        # "the hob takes ages to warm up" and "the ring takes ages to heat up" were all a "Got it",
        # and "one ring on my hob doesnt work" was "Ugh, those are fiddly". The hob is a different
        # appliance from the oven and the checks are different again on gas, induction and ceramic.
        # A hob ring that has gone is a part you buy, not an appliance you replace, and the price
        # question had no row: "how much is a new hob ring" fell to the composer's live-prices
        # hedge ("I can't look up live prices"), and a solid plate is a tenner. The row is the
        # price of the part only; cleaning one and fitting a gas one stay where they were.
        entry("hob-scratch",
              (("hob", "hobs", "ceramic hob", "induction hob", "cooker top", "cooker plate",
                "hotplate", "electric hob", "gas hob"),
               # "marks" is the burnt-on cleaning question ("my hob has burnt on marks"), so
               # only the words that name damage are here.
               ("scratch", "scratches", "scratched", "scuff", "scuffs", "scuffed", "gouge",
                "gouged", "chipped", "chip")),
              ("Nine times in ten the mark that looks like a scratch is metal, sugar or limescale "
               "burnt onto the glass: scrape the cold hob with a hob scraper held almost flat, then "
               "rub ceramic hob cleaner over it with a cloth, and it comes away. A real scratch - "
               "you feel it catch a fingernail - cannot be polished out of a glass top, so a fine "
               "one is something to live with and a deep one means a new top, which on a built-in "
               "hob is often most of the price of a new one. Never use an abrasive powder or a "
               "scouring pad; they make more of them."),
              # the surfaces that are sanded or repaired rather than scraped: a wooden floor, a
              # worktop, a car, a phone screen, a bath and a pair of glasses all have their own
              # answer, and each of them would otherwise land here on the word "scratched".
              avoid=("floor", "floors", "wood", "laminate", "worktop", "worktops", "table",
                     "tables", "furniture", "desk", "door", "doors", "car", "cars", "van",
                     "windscreen", "screen", "phone", "mobile", "glasses", "spectacles", "watch",
                     "bath", "bathroom", "sink", "shower", "wall", "walls", "paint", "painted",
                     "leather", "sofa", "shoe", "shoes", "boot", "boots", "cd", "dvd", "vinyl",
                     "record", "records", "lens", "camera", "clean", "cleaning", "grease",
                     "burnt on", "burnt", "burned", "burning", "baked on", "limescale",
                     "buy", "best", "which", "worth", "cost", "price", "cheap", "cheapest")),
        entry("hob-ring-price",
              (("hob ring", "hob rings", "ring", "rings", "burner", "burners", "burner cap",
                "solid plate", "hotplate", "element", "cooker ring", "gas ring"),
               ("cost", "costs", "much", "price", "prices", "buy", "replace", "replacement", "new",
                "cheap", "cheapest", "spare", "spares", "part", "parts", "fit")),
              ("About £10 to £25 for a solid plate or a gas burner cap, and £25 to £50 for an "
               "induction zone's part, so it is worth fixing rather than replacing the cooker. Buy "
               "by the cooker's model number rather than by eye - the same size ring is not always "
               "the same fitting. An electric one is usually two screws and a spade connector; a "
               "gas ring has to be fitted by a Gas Safe engineer."),
              bias=1,
              # a ring you wear, a phone ringing, a ring round the bath and a ring-marked hob are
              # other entries' lines
              avoid=("clean", "cleaning", "grease", "stain", "stains", "scrub", "phone", "mobile",
                     "ringtone", "engagement", "wedding", "gold", "silver", "diamond", "jewellery",
                     # a budget question about the rings you wear is the jewellery row's, and
                     # "how much should we spend on rings" was reaching this one on the tie
                     "spend", "spent", "spending", "budget", "afford", "salary", "propose",
                     "proposal", "carat",
                     # "what ring should i buy" is a ring you wear, and the bare noun in the key
                     # plus "buy" in the ask was enough to answer it with a burner cap
                     "what ring", "which ring", "ring should", "rings should", "pick a ring",
                     "rings cost", "ring cost", "much do rings", "much are rings", "ring prices",
                     "choose a ring", "ring shopping", "wear", "wearing", "worn", "rings to wear",
                     "necklace", "earring", "bracelet", "tarnish", "finger", "ear", "ears",
                     # "burner" is a wood burner and a log burner as well as a gas ring, and
                     # "how much does a wood burner cost" and "how much to install a log burner"
                     # were both answered with the price of a hob ring
                     "wood burner", "woodburner", "wood burning", "woodburning", "log burner",
                     "logburner", "multi fuel", "multifuel", "stove", "stoves", "chimney",
                     "flue", "fireplace", "solid fuel",
                     "bath", "bathtub", "sink", "onion", "calamari", "pineapple", "doorbell",
                     "door bell", "curtain", "smoke", "ow", "hurt", "swollen", "sting")),
        # "how do i fit a wood burner" was answered with the price of a hob ring, and with the stove
        # words held out of that row it became "That's beyond what I know well" - which is worse
        # than a wrong price only because it is honest. Nothing had the fitting itself, and it is
        # the one part of a wood burner a person cannot just get on with: the flue and the chimney
        # have to be signed off.
        entry("fitting-a-wood-burner",
              (("wood burner", "woodburner", "wood burning", "woodburning", "wood stove",
                "log burner", "logburner", "log burning", "multi fuel", "multifuel",
                "solid fuel", "stove", "stoves", "fireplace", "flue", "chimney"),
               # the *fitting* words, not "how do i": "how do i light my log burner" and
               # "how do i stop a chimney banging" both name a stove and ask how, and each has
               # its own card - a bare "how do i" in this group took both of them.
               ("fit", "fits", "fitting", "fitted", "install", "installing", "installation",
                "put in", "putting in", "need", "needed", "regulations", "regs",
                "regulation", "building control", "hetas", "legal", "allowed", "sign off",
                "hearth", "clearance", "distance", "ventilation", "liner", "lining", "line it",
                "what size", "how big", "position", "where can i put", "too close")),
              ("Get it signed off rather than doing the flue yourself: a Hetas-registered installer, "
               "or a fitter whose work building control inspects, is what the regs ask for, and an "
               "unsigned stove is a problem when you sell the house as well as a fire risk. Size "
               "the stove to the room - roughly 1kW for every 14 cubic metres, and no more, because "
               "a big stove turned right down smokes and soots the flue. It needs a non-combustible "
               "hearth (12mm of slate or stone is the usual, and 300mm in front of the door), the "
               "flue swept and lined if the chimney is old, and a carbon monoxide alarm in the same "
               "room, which the law has required for a solid-fuel stove since 2022. In a smoke "
               "control area the stove must be DEFRA-exempt, so check that before you buy it."),
              # what one costs and what one saves is the price and running-cost card's line
              avoid=("how much", "much does", "much is", "cost", "costs", "price", "prices",
                     "cheap", "cheapest", "expensive", "worth it", "save", "saving", "savings",
                     "bill", "quote", "budget",
                     # a dirty stove door, a smoky one and a rusted one are the stove's own jobs
                     "clean", "cleaning", "cleaner", "glass", "soot", "sooty", "smoke", "smoky",
                     "dirty", "sweep", "sweeping", "swept", "paint", "painting", "repaint",
                     "rust", "rusty", "not drawing", "wont light", "won't light", "keeps going out",
                     # lighting it is its own card, and a chimney that bangs is a bird or soot
                     "light", "lighting", "light it", "banging", "bang", "noise", "noisy",
                     "bird", "birds", "damper", "stop the", "smell"),
              # the DIY sheet claims "can i install my own ..." with one key word and one ask,
              # and it is right about a tap washer rather than a flue that has to be signed off
              bias=3),
        entry("hob-heat",
              (("hob", "hobs", "ring", "rings", "burner", "burners", "hotplate", "hotplates",
                "cooker plate", "cooker top", "induction", "ceramic hob", "gas ring", "gas hob",
                "electric hob", "solid plate"),
               ("slow", "slower", "slowly", "ages", "forever", "long", "longer", "takes", "taking",
                "heats", "heating", "heat up", "warms", "warming", "warm up", "not heating",
                "isnt heating", "isn't heating", "wont heat", "won't heat", "not hot", "cold",
                "not working", "doesnt work", "doesn't work", "stopped working", "stopped",
                "dead", "gone", "weak", "barely", "packed up", "stopped heating", "one ring",
                # a ring that will not light at all is the same fault as one that will not heat,
                # and "the hob wont light" was "That would bother me too" on its own
                "wont light", "won't light", "wont ignite", "won't ignite", "wont spark",
                "won't spark", "not lighting", "doesnt light", "doesn't light", "clicks but",
                "no flame", "wont stay lit", "won't stay lit", "goes out", "keeps going out")),
              _hob_heat,
              # a dirty hob is a cleaning job, a pan that will not heat on induction is the pan's own
              # question when the line names the pan, and buying or choosing one is a shopping answer
              avoid=("clean", "cleaning", "grease", "greasy", "burnt on", "stain", "stains", "scrub",
                     # A gym, a job and a hospital all have an induction, and only the kitchen one
                     # is a hob: "what should i take to a gym induction" was the ceramic element
                     # ("check the pan before the hob"). None of these words is in this row's key,
                     # and the fitness row answers the gym line.
                     "gym", "gyms", "new job", "first day", "at work", "the office", "staff",
                     "orientation", "hospital", "ward", "antenatal", "new starter", "volunteer",
                     "shiny", "oven", "grill", "microwave", "kettle", "wood burner", "log burner",
                     "buy", "best", "which", "worth", "cost", "price", "cheap", "cheapest",
                     "how do i use", "setting", "simmer", "boil", "wok", "season", "seasoning",
                     "pressure cooker", "slow cooker", "air fryer", "boiler", "pilot",
                     "pilot light", "candle", "candles", "fire", "fireplace", "barbecue", "bbq",
                     # A phone rings and a hob has rings, and "ring"/"rings" is in this key, so
                     # "how do i stop my phone ringing at night" was the ceramic-element answer.
                     # Anything about a phone means the ring in the line is the sound.
                     # The words are the phone's own and never a hob's: "ringing" and "rang" fold
                     # onto "ring", so they would take every hob line with them.
                     "phone", "phones", "mobile", "mobiles", "ringtone", "voicemail", "landline",
                     "missed call", "missed calls",
                     # The same worry one step further out: "how do i stop my ears ringing" and "the
                     # ringing in my ears wont stop" were the ceramic-element answer, because a ring
                     # that will not heat and an ear that will not stop are the same two words. The
                     # tinnitus row holds the ear words below, so any of them means the line is about
                     # a person and not a hob. "ringing" and "rang" still cannot go here - they fold
                     # onto "ring", and they would take every hob line with them.
                     "ear", "ears", "tinnitus", "hearing", "my ears", "in my ears", "in my ear",
                     "ringing in my ears", "ringing in the ears",
                     # and a ring you wear is not a hob ring either: "my ring has gone green" was
                     # this answer, and green is the tarnish on silver, not an element going out
                     "gold", "silver", "jewellery", "jewelry", "necklace", "bracelet", "earring",
                     "earrings", "engagement ring", "wedding band", "diamond", "tarnish",
                     "tarnished", "green", "gone green", "finger green", "clean my ring",
                     # a ring that has gone dull or wants a polish is a jeweller's job as well
                     "dull", "dulled", "polish", "polishing",
                     # and the verb: "i need to ring in tomorrow" was the ceramic element,
                     # because the ring a line is asked about can be a phone call and the two
                     # words it took to say so were not in this list. See `RING_AS_A_CALL`.
                     ) + RING_AS_A_CALL,
              bias=1, guard=_a_person_not_a_hob),
        # An iron that spits water or leaves marks is the commonest thing that goes wrong with one,
        # and it had no answer at all: "my iron spits water" was "Thanks for telling me" and "my iron
        # is leaking water" was "That would bother me too".
        entry("iron-fault",
              (("iron", "irons", "steam iron", "steam generator", "soleplate"),
               ("spits", "spitting", "spit", "spat", "spits out", "spitting out", "spitting water",
                "drips", "dripping", "drips water", "leaks", "leaking", "leaky", "water",
                "wet patches", "wet patch", "marks", "white marks", "brown marks", "streaks",
                "spraying water", "sprays water", "water on the clothes", "damp clothes",
                # a soleplate that stays cold is the other half of the same question
                "wont heat", "won't heat", "wont heat up", "won't heat up", "not heating",
                "isnt heating", "isn't heating", "no heat", "stopped heating", "cold", "dead",
                "wont get hot", "won't get hot", "not hot", "wont turn on", "won't turn on",
                "wont switch on", "won't switch on")),
              _iron_fault,
              # ironing a garment, a scorch on fabric, the crease and the fold, and buying one are
              # other entries: this one is only the iron misbehaving with its own water
              avoid=("crease", "creases", "ironing board",
                     "scorch", "scorched", "burn", "burnt", "buy", "best", "which", "worth",
                     "cost", "price", "cheap", "travel iron", "hair", "hair straighteners",
                     "curling", "fabric", "shiny", "clothes are",
                     # "wont heat" and "won't heat" were in this row's own key group and in
                     # this avoid list at the same time, so the row stood itself down for the
                     # half of its question about a soleplate that stays cold: "the iron wont
                     # heat up" was a shrug while "my iron isnt heating up" was answered. An
                     # avoid word is read through its forms and stands the whole row down, so a
                     # key word of the same row can never be one.
                     "cord", "plug", "fuse", "water tank", "limescale in the kettle"),
              bias=1),

        entry("dryer-not-heating",
              (("tumble dryer", "tumble drier", "dryer", "drier", "tumbler", "washer dryer"),
               ("not heating", "isnt heating", "isn't heating", "no heat", "wont heat", "won't heat",
                "heat up", "heating up", "cold", "takes ages", "takes forever", "not drying",
                "wont dry", "won't dry", "doesn't dry", "doesnt dry", "still wet", "still damp",
                "clothes are damp", "clothes are wet", "long time to dry",
                # "my tumble dryer takes two goes" and "my clothes come out damp after two cycles"
                # are the same slow-drying question, and they were a "Got it" for want of "goes"
                # and "cycles" here.
                "two goes", "two cycles", "goes", "go", "cycles", "cycle", "come out damp",
                "comes out damp", "still damp after", "damp after", "takes two",
                "leaves the clothes damp", "leaves clothes damp", "leaves them damp",
                "clothes damp", "clothes still wet", "clothes are still wet",
                # a slow dryer is the same question as a cold one, and the "taking" forms were the
                # fuse-and-wall-switch card instead: "how do i stop my tumble dryer taking three
                # hours" was answered with the checks for a machine that will not start at all.
                "taking ages", "taking so long", "takes so long", "taking hours", "takes hours",
                "taking three hours", "taking two hours", "taking a long time", "takes a long time",
                "hours to dry", "long to dry", "slow to dry", "drying slowly")),
    _dryer_heat,
              # a dryer that will not turn, or that squeals, is the noise and drum question; a
              # blocked vent in a rented flat is the damp one; and the running cost is its own entry
              avoid=("buy", "which", "best", "worth", "cost", "cheap", "cheapest", "running",
                     "noise", "noisy", "loud", "squeak", "squeaks", "squeaking", "bang", "bangs",
                     "banging", "rattle", "rattles", "grind", "grinds", "grinding", "smell",
                     "smells", "smelly", "fire", "fires", "lint fire", "condensation", "mould",
                     "mold", "damp walls", "hair dryer", "hairdryer")),

        # A drum that will not turn is the same machine with a different part at fault, and the heat
        # answer leads somewhere the person cannot check. The belt slipping off is the usual cause and
        # it is cheap to put right, so it is said first.
        # A dryer that smells of burning is a lint fire waiting to happen, and the answer it got was
        # to simmer a pan of vinegar. Nothing else in the kitchen keys the smell of a dryer, so it
        # fell to the general odour entry, which is advice for a room.
        # A dryer that smells musty or damp is the machine's own trapped moisture, and the only
        # smell row it had was the burning one, so "the heat pump dryer smells" and "my dryer
        # smells musty" were a shrug and "the tumble dryer smells musty" was the washing
        # machine's service wash. The fix is the fluff and the condenser, which is where the
        # water sits.
        entry("dryer-smells",
              (("tumble dryer", "tumble drier", "dryer", "drier", "tumbler", "washer dryer",
                "heat pump dryer", "heat pump drier", "heat pump tumble dryer", "vented dryer",
                "condenser dryer"),
               ("smells", "smell", "smelly", "stinks", "stink", "stinking", "musty", "fusty",
                "damp smell", "damp", "mouldy", "moldy", "mildew", "sour", "whiff", "reek",
                "reeking", "pongs", "pong", "funky", "off smell", "smells off")),
              "Nearly always the fluff and the water: empty the fluff filter and wash it, pull the "
              "condenser out and rinse it under the tap if the machine has one, and tip out the "
              "water tank or check the drain hose. On a heat pump or condenser dryer the smell is "
              "usually the condenser left damp, so run a rinse cycle and leave the door and the "
              "drawer open afterwards. A vented dryer wants the vent hose cleared and the outside "
              "flap checked, and once a year wipe the drum and the seal with a hot damp cloth.",
              # a burning smell is the fire card's, and the ones that are not the machine -
              # cooking, the room, a drain, the fridge - are their own rows' questions.
              avoid=("burning", "burnt", "scorched", "singed", "smoking", "fire", "smells hot",
                     "smells really hot", "too hot", "oven", "kitchen", "room", "fridge",
                     "freezer", "washing machine", "dishwasher", "sink", "drain", "drains",
                     "bin", "bins", "cooker", "hob", "microwave", "hair dryer", "hairdryer",
                     "takes ages", "not drying", "still wet", "not heating", "not working",
                     "buy", "worth", "cost", "running")),

        # "do heat pump dryers need a vent" was answered with the buying advice ("worth it if you
        # would use it three times a week"), which is a different question, and the vent question
        # is the one that decides where the machine can go. It is a fixed fact per kind of dryer,
        # so it is keyed by the kind and the word for the duct.
        # A hair dryer is not a tumble dryer, and once the radiator row stopped taking every
        # "not heating up" the line fell to a shrug: "my hair dryer is not heating up" had been
        # told about a thermostatic valve head, which is the wrong machine as well as the wrong
        # part. The grille is the first thing to check and it is a different job from a dryer's
        # fluff filter, so it is its own row.
        entry("hair-dryer-not-hot",
              (("hair dryer", "hairdryer", "hair drier", "blow dryer", "blowdryer"),
               ("not heating", "isnt heating", "isn't heating", "not heating up", "no heat",
                "no heat coming out", "blowing cold", "blows cold", "cold air", "cold",
                "stopped heating", "wont heat", "won't heat", "wont heat up", "won't heat up",
                "not hot", "isnt hot", "isn't hot", "wont get hot", "won't get hot",
                "keeps cutting out", "cuts out", "cut out", "stopped working", "dead",
                "takes ages", "smells hot", "buzzing")),
              _hair_dryer,
              # how long one lasts, whether to buy one and styling a head of hair are other rows'
              avoid=("buy", "buys", "buying", "best", "which", "worth", "cost", "price", "cheap",
                     "how long", "last", "lasts", "lasting", "curlers", "straighteners",
                     "straightener", "diffuser", "brush", "bristles", "dry my hair", "dry hair",
                     "hairdryer brush", "styling", "frizz", "curly", "curls")),

        entry("dryer-vent",
              (("tumble dryer", "tumble drier", "dryer", "drier", "tumbler", "washer dryer",
                "heat pump dryer", "heat pump drier", "heat pump tumble dryer", "vented dryer",
                "condenser dryer"),
               ("vent", "vents", "vented", "venting", "ventilation", "hose", "hoses", "duct",
                "ducting", "flue", "out of the window", "outdoors", "outside wall", "wall vent",
                "needs a vent", "need a vent", "need venting", "no vent", "without a vent",
                "tumble dryer vent", "dryer vent",
                # a heat pump dryer makes water instead of steam, and "where does the water go
                # in a heat pump dryer" named the water rather than the vent, so it fell to the
                # slow-drying row. The tank and the hose are this row's answer.
                "where does the water go", "where does the water", "water go",
                "water tank", "empty the water", "condenser water", "the water goes")),
              "A heat pump or condenser dryer needs no outside vent at all - the water goes into a "
              "tank you empty, or down a hose to the drain - so it can sit in a cupboard or a "
              "bedroom. Only a vented dryer needs the duct, and then it wants the hose out through "
              "a wall vent or an open window with no kinks and no crushed section behind the "
              "machine; a short straight run to outside is the whole job. Never duct one into a "
              "loft or a chimney: that puts the damp and the lint back into the house, and fluff "
              "round a hot duct is a fire.",
              # a dryer that is not heating, not turning, smelling, cutting out or being chosen in
              # a shop is another row's; this one is only where the air and the water go.
              avoid=("not heating", "isnt heating", "isn't heating", "not drying", "takes ages",
                     "still wet", "still damp", "smells", "smell", "burning", "fire", "sparks",
                     "wont turn", "won't turn", "not spinning", "cuts out", "stopped working",
                     "buy", "best", "which", "worth", "cost", "cheap", "running cost",
                     "hair dryer", "hairdryer", "condensation", "mould", "mold", "damp walls")),

        entry("dryer-smells-of-burning",
              (("tumble dryer", "tumble drier", "dryer", "drier", "tumbler", "washer dryer"),
               ("burning smell", "smells of burning", "smells like burning", "smell of burning",
                "smells burnt", "smells scorched", "smells singed", "smells hot", "burning",
                "scorching", "smoking")),
              "Stop it and unplug it, and do not run another load until you have looked: a dryer fire "
              "starts with lint round the heater or a vent hose full of fluff, and the smell is the "
              "warning. Empty the fluff filter and clear the hose. Still there after that? Get an "
              "engineer out, and never leave a dryer running while you are out.",
              avoid=("buy", "which", "best", "worth", "cost", "running", "noise", "noisy", "heating",
                     "not heating", "takes ages", "hair dryer", "hairdryer", "oven", "room", "kitchen",
                     "fridge", "freezer", "washing machine", "damp", "mould", "mold")),

        entry("dryer-drum-not-turning",
              (("tumble dryer", "tumble drier", "dryer", "drier", "tumbler", "washer dryer"),
               ("wont turn", "won't turn", "not turning", "isnt turning", "isn't turning",
                "drum isnt turning", "drum not turning", "drum wont turn", "drum not moving",
                "wont spin", "won't spin", "not spinning", "no spin", "drum dead")),
              "The belt has almost certainly slipped off or snapped: it is a rubber band round the drum "
              "and the motor pulley, a few pounds, reached through the back panel with a screwdriver. "
              "Turns by hand but not under power? Belt or door switch. Will not turn by hand either? "
              "Something is jammed or the bearings have gone, which usually means a new machine.",
              # the heat, the noise, the running cost and the buying question all have answers of
              # their own, and a dryer that smells of burning is a fire question, not a belt.
              avoid=("buy", "which", "best", "worth", "cost", "cheap", "running", "noise",
                     "noisy", "loud", "squeak", "squeaks", "squeaking", "bang", "bangs",
                     "banging", "rattle", "rattles", "grind", "grinds", "grinding", "smell",
                     "smells", "smelly", "fire", "fires", "heating", "heat up", "not heating",
                     "takes ages", "still wet", "still damp", "hair dryer", "hairdryer")),

        entry("vacuum-suction",
              (("vacuum", "vacuum cleaner", "hoover", "henry", "dyson", "vax"),
               ("suction", "lost suction", "no suction", "not picking up", "wont pick up",
                "won't pick up", "not sucking", "weak", "blocked", "clogged", "full",
                # "picking up" is the way most people say it, and "picking" is the only word that
                # says which part of the air path has failed: "my hoover isnt picking anything up"
                # reached nothing at all, and "the hoover wont pick anything up" was read as the
                # hand habit of picking. The vacuum noun in the first group is what keeps the hand
                # habit out, and `which`/`buy` below keep the shopping question out.
                "picking", "pick", "picked", "picks", "picking up", "pick up", "picks up",
                # "how do i unblock a hoover" is the same air path said the other way round, and it
                # reached nothing at all: unblock is not a form of blocked, and the appliance alone
                # is one word of key
                "unblock", "unblocking", "clearing", "bunged", "bunged up", "jammed", "stuck",
                # "how do i unclog a hoover" reached nothing: unclog is not a form of clogged, and
                # "how do i fix the hoover" named no air word at all. Both are this one job.
                "unclog", "unclogging", "clogging", "fix", "fixing", "stopped picking up")),
              "Follow the air path: take the hose off both ends and drop a coin through it, shake the bag "
              "or empty the bin, wash the filter (most are washable, and it has to be bone dry before it "
              "goes back) and cut the hair off the brush bar. A blocked hose, a full bag or a matted "
              "filter is the answer nearly every time, and all three are free to fix.",
              # A named vacuum with "fix" in the line is this job, not the machine-stopped card's
              # first checks: "how do i fix the hoover" was answered "check the plug fuse ... then
              # ring the retailer", which is consumer law for a machine that will not start. The
              # one point of lift only wins against the cards that also match a vacuum, and the
              # power words below hand a vacuum that really has stopped dead back to them.
              bias=2,
              # "help me pick a hoover" is the shopping question with the fault entry's words in it
              avoid=("buy", "which", "best", "cheapest", "worth", "cordless",
                     # a vacuum that will not start at all is the machine card, not the air path
                     "wont turn on", "won't turn on", "wont switch on", "wont start", "wont come on",
                     "no power", "dead", "fuse", "stopped dead", "smell", "burning",
                     # a robot vacuum that gets stuck is the brushes, the wheels and the map, not the
                     # air path, and the answer here would be the wrong list of things to check
                     "robot",
                     "choose", "choosing", "recommend", "recommendation", "shop", "shopping",
                     "help me pick", "pick a", "pick the", "picking a", "pick one", "pick out")),

        # A toaster that browns one side of the bread is not the pops-early fault: one element has
        # gone or the bread is sitting proud, and either way the timer is fine. It reached the
        # meal rows ("what to have on toast") because "toasts" and "one side" are both food words.
        entry("toaster-one-side",
              (("toaster", "toast", "sandwich toaster"),
               ("one side", "one side only", "only one side", "one end", "uneven", "unevenly",
                "patchy", "halfway", "one half", "half cooked", "not browning")),
              "One side not browning means the element on that side has gone, or the wire that feeds "
              "it: unplug it, and if you look in while it is cold and one element never glows while "
              "the others do, that is the fault. On an ordinary toaster that is a new toaster, not a "
              "repair. If it browns at one END instead, the bread is sitting proud of the slots and "
              "the elements are fine.",
              avoid=("buy", "best", "which", "cheapest", "worth", "recipe", "recipes", "idea",
                     "ideas", "dinner", "lunch", "breakfast", "sandwich", "topping", "toppings")),

        entry("pilot-light",
              (("pilot light", "pilot", "pilot flame"),
               ("going out", "goes out", "gone out", "wont stay lit", "won't stay lit", "keeps going",
                "blows out", "not staying", "wont light", "won't light", "wont stay on",
                "won't stay on", "flame")),
              "Hold the knob in for twenty seconds after the flame catches, then let it go: a pilot that "
              "won't hold is nearly always the thermocouple, a small part a Gas Safe engineer swaps in "
              "ten minutes. A draught or a dirty jet does it too, and both mean taking the case off, so "
              "that is their job as well. If you smell gas, turn it off at the meter, open the windows "
              "and ring the gas emergency line on 0800 111 999.",
              avoid=("buy", "best", "cost", "price")),

        # "can i fix it myself" is asked after a fault far more often than it is typed as a whole
        # question, and it went two ways and neither helped: alone it reached nothing and the person
        # got "I don't know enough to answer that honestly", and in a thread it collected the repair
        # rule ("worth repairing while the quote is under half the price of a new one"), which is a
        # different question. The do-it-yourself words are one key part and the job the other, so the
        # job may come from this line or from the one it leans on; the ask gate is what keeps it off
        # a report ("i fixed it myself this time"), because a report is not a question about whether
        # to have a go. `myself` and `my own` are in half the language - a haircut, a tax return,
        # being on your own - so the avoid list names the things that are not house repairs.
        entry("fix-it-myself",
              (("myself", "my own", "diy", "have a go", "having a go", "have a bash",
                "give it a go", "giving it a go", "by myself", "on my own"),
               ("fix", "fixing", "fixed", "repair", "repairing", "mend", "mending", "install",
                "installing", "fit it", "fitting", "replace", "replacing", "unblock",
                "unblocking", "do it", "go at it", "at it", "sort it", "sort that",
                "take it apart", "take apart", "plumb", "plumbing",
                "wire", "wiring", "rewire", "rewiring", "electric", "electrics", "bleed", "service",
                "seal", "belt",
                # "washer" is the appliance in one line and the little rubber disc in another: a tap
                # washer is a five-minute job, and reading it as the machine loses the question.
                "tap washer", "tap washers", "washer", "part")),
              _diy,
              ask=("can i", "can we", "could i", "should i", "should we", "shall i", "is it worth",
                   "worth", "easy", "easier", "hard", "difficult", "safe", "able to", "dare",
                   "do i need", "possible", "any point"),
              avoid=_DIY_AVOID,
              # "is it easy to replace a tap washer myself" names two things a rule can be keyed on
              # (a tap, a washer) and the rule that owns them is repair-or-replace, which answers a
              # machine that failed, not a person asking whether to have a go. A line that says
              # "myself" is asking the do-it-yourself question, so this entry leans over a job rule.
              bias=2),

        entry("tradesperson-check",
              (("tradesperson", "tradesman", "plumber", "electrician", "builder", "roofer",
                "gas engineer", "handyman", "boiler engineer",
                # the same ask about the other trades people hire: "how do i find a good decorator"
                # was a search hedge while the plumber in the line was answered
                "decorator", "decorators", "painter", "painters", "plasterer", "plasterers",
                "tiler", "tilers", "joiner", "joiners", "carpenter", "carpenters", "glazier",
                # not "window fitter": the fitness card reads "fitter" as someone getting fit
                "locksmith", "gardener", "gardeners", "landscaper", "fencer", "chimney sweep",
                "roof tiler", "bricklayer",
                # "how do i check if a company is legit" was a shrug: the question is the one a
                # person asks about a plumber, so the trade names are not the only door into it.
                # "website", "shop", "garage" and "dealer" are left out on purpose - a fake website,
                # an online shop and a used car each have a row of their own that knows more.
                "company", "companies", "firm", "business", "supplier", "installer",
                "installation company", "contractor", "contractors", "man with a van",
                "removals", "tradesperson", "tradespeople"),
               ("check", "reputable", "trust", "trustworthy", "cowboy", "avoid", "rip off",
                "rip-off", "how do i know", "vet", "choose", "find a good", "insurance", "quote",
                # "how do i find a reliable tradesperson" wanted the word "good" in the line
                "reliable", "careful", "decent", "honest", "find a", "find someone", "who can",
                "good one", "good company", "good firm", "pick a", "picking a",
                # "how do i spot a cowboy builder" is the same question as "how do i avoid" one, and
                # it went to a complaint entry: spotting one is how to pick one.
                "spot a", "how do i spot", "how to spot", "spotting",
                # the same ask about a company rather than a trade
                "legit", "legitimate", "genuine", "registered", "look up", "look them up", "verify",
                "vetted", "references")),
              "Start with Companies House, which is free: search the name or the number on their quote "
              "and you can see whether the company exists, when it was formed and whether the "
              "registered address is a real place rather than a mail drop - a limited company has to "
              "put its number and registered address on its website and its invoices. Then the trade "
              "checks: a written quote rather than a verbal one, proof of insurance, and for gas, oil "
              "or electrical work the registration number you can check yourself on the Gas Safe, "
              "OFTEC or NICEIC register. A neighbour who has used them beats any review site, and pay "
              "by card rather than bank transfer so there is a chargeback if it goes wrong. Never pay "
              "the whole price up front - a deposit for materials is normal, the rest when it is done.",
              # a line that complains is the complaint answer's, and so is a line about your rights:
              # "we got ripped off by a roofer" is money and small claims, not how to pick one.
              avoid=("cheap", "cheapest", "cost", "how much", "price", "hourly", "emergency",
                     "no hot water", "leak", "leaking", "broken",
                     "rip off", "ripped off", "ripping off", "overcharged", "refund",
                     "small claims", "trading standards", "botched", "bad job", "rubbish job",
                     "took my money", "never came back", "complain", "complaint", "guarantee",
                     "warranty", "rights", "did a runner",
                     # a link, a login or an email is the phishing rows' line: "is this website a
                     # scam" and "is an online shop with no reviews safe" both had a better answer
                     # before this entry learned the word "website", so the door stays shut
                     "website", "websites", "online shop", "link", "click", "clicked", "login",
                     "password", "email", "text message", "phishing", "invoice for", "paypal",
                     "bank details", "account details")),

        # Nobody in this tree answered the kit question: "what should i have in a first aid kit" fell to
        # "I don't know enough to answer that honestly". The list is the ordinary one a pharmacist would
        # give, and it is on the house rather than a symptom, so the safety module keeps the injuries.
        entry("first-aid-kit",
              (("first aid kit", "first aid box", "first aid", "medical kit", "first-aid kit",
                "medicine cupboard", "medicine cabinet", "medicine box", "first aid supplies"),
               ("have", "need", "keep", "put", "got", "get", "buy", "stock", "include", "contents",
                "what", "at home", "for the car", "should")),
              ("A home kit is a box you can use one-handed in the dark: plasters in a few sizes, sterile "
               "gauze and tape, a crepe bandage, small scissors, tweezers, disposable gloves, a "
               "thermometer, and children's paracetamol with the dose worked out by weight. Add an ice "
               "pack, antiseptic cream and the 111 number, then check it once a year and replace "
               "anything past its date."),
              # An injury is the safety module's line, not a shopping list: the kit entry is only for
              # the question about what a kit holds.
              avoid=("burn", "burns", "burnt", "scald", "scalded", "cut", "cuts", "bleeding", "bled",
                     "nosebleed", "sprain", "sprained", "choking", "choked", "swallowed", "overdose",
                     "rash", "fever", "temperature", "allergic", "anaphylaxis", "seizure", "fit",
                     # a course or a certificate is a different question from a box of plasters
                     "course", "training", "certificate", "qualification")),

        # What to do with paint is asked at the shed door, and the answer is a legal one: liquid paint
        # is not household waste, so it has to be dried out or taken to the tip.
        entry("paint-smell-curing", (("paint", "painting", "repainted", "paintwork", "gloss", "emulsion",
                                "undercoat"),
                               ("smell", "smells", "smelling", "smelly", "smells of", "smelt",
                                "fumes", "fume", "stink", "stinks", "lingering")),
              "Keep the windows open and let it cure: water-based paint stops smelling within a day or "
              "two, and oil-based gloss takes a week or so to stop off-gassing. A bowl of water with a "
              "chopped onion in the room overnight, or a dish of bicarbonate of soda, takes the edge "
              "off. Don't mask it with candles. If it is still strong after a week, the paint may be "
              "old or the room under-ventilated.",
              bias=1,
              avoid=("tin", "tins", "leftover", "dispose", "bin", "recycle", "tip", "gas",
                     "carbon monoxide", "burning", "smoke")),
        entry("paint-tins",
              (("paint", "paint tin", "paint tins", "tins of paint", "paint pot", "paint pots",
                "leftover paint", "old paint",
                # a tin that is drying out is kept, not thrown away, and the phrases are how that
                # question arrives: "dried out" alone is the tip
                "drying out in the tin", "dries out in the tin", "dried out in the tin",
                "drying out in the can", "gone hard in the tin", "skinned over", "a skin on"),
               # "tips" must not match "the tip": "any tips for painting a small room" is the painting
               # entry, and the forms of the bare word "tip" catch it
               ("old", "leftover", "dispose", "get rid", "throw", "bin", "recycle", "the tip",
                "to the tip", "recycling centre", "tins", "pots", "half a tin", "dried out", "store",
                "keep", "what do i do")),
              "A tin of paint has to dry out before it can go anywhere. Stir sand, sawdust or cat "
              "litter into it, leave the lid off somewhere safe until it is hard, then take it to the "
              "household waste recycling centre, where nearly every site takes paint. To keep a "
              "part-used tin, wipe the rim, press the lid down with a block of wood and store it upside "
              "down so no skin forms. A few inches left is worth offering on Freecycle.",
              # "how do i get rid of the smell of paint" was answered with "dry the tin out": the
              # smell of a room is paint-smell, and only a leftover tin is this row's business.
              avoid=("wall", "walls", "ceiling", "woodwork", "paint the", "repaint", "colour",
                     "nail polish", "spray", "smell", "smells", "smelling", "smelly", "smells of",
                     "fumes", "fume", "stink", "stinks",
                     # "keep" and "store" are how a leftover tin is asked about, and they took "how do
                     # i keep my paint from drying too fast" with them: keeping a paint workable while
                     # you use it is paint-drying-fast's question, and this card is about a tin that
                     # is finished with
                     "drying too fast", "drying too quickly", "dries too fast", "dry too fast",
                     "from drying", "keeps drying", "before it dries", "going off the brush",
                     "wet edge", "open time", "workable")),

        # A second-hand machine is a price question, so the numbers come first and the checks second.
        entry("second-hand-washer",
              (("washing machine", "washer", "tumble dryer", "dishwasher"),
               # the second-hand words carry this one: "what's the best washing machine to buy" is the
               # shopping domain, and a bare "buy" or "worth" would take it
               ("second hand", "second-hand", "used", "refurbished", "reconditioned", "cheap",
                "cheaper", "fair price", "how much", "private sale", "facebook", "gumtree",
                "gum tree", "dealer", "nearly new")),
              _washer_price,
              # A machine being priced is not a machine being cleaned: "how much bleach in the
              # washing machine" was answered with what a second-hand one costs, and a mouldy door
              # seal is the mould answer's question, not this one's.
              avoid=("bleach", "mould", "mold", "mildew",
                     "fix", "repair", "broken", "leaking", "error", "wont spin", "won't spin",
                     "not draining", "smells", "install", "plumbing in")),
        # Furniture up a stairwell is a measuring and lifting question, and the answer that saves the
        # wall (and a back) is the tape measure, not muscle.
        entry("furniture-upstairs",
              (("wardrobe", "chest of drawers", "sideboard", "bookcase", "bookshelf", "sofa",
                "couch", "settee", "armchair", "table", "bed frame", "divan", "furniture", "dresser",
                # a mattress is the classic thing that will not turn the corner, and it was a shrug
                "mattress", "bed"),
               ("upstairs", "up the stairs", "stairwell", "landing", "narrow stairs", "on my own",
                "by myself", "get it up", "move it up", "carry it up", "one person", "two people",
                "up a floor", "second floor", "top floor",
                # Getting the thing into the new place in the first place is the same measuring and
                # lifting job, and the plainest way of asking it names no stairwell at all: "how do
                # i move a sofa" and "how do i move my sofa to my new flat" were both a shrug. The
                # moving words are the second part of the key, so the furniture word still has to be
                # there and "how do i move house" stays with the moving-day plan.
                "move", "moving", "moved", "new flat", "new house", "downstairs", "front door",
                "through the door", "doorway", "doorways", "van", "hire", "hiring", "removals",
                "removal", "too big", "wont fit", "won't fit", "get it to", "get it in")),
              _furniture_upstairs, bias=2,
              # "can i get a sofa up the stairs on my own" was answered by the making-friends row,
              # which keys "on my own" too and outscored this one; the bias settles it, and the two
              # key groups here still have to match, so a lonely line is never this answer.
              avoid=("assemble", "flat pack", "build", "ikea", "squeak", "hinge", "slide", "rail",
                     "mirror", "sell", "buy", "choose", "paint",
                     # A move that names a price is the van-hire row's question, and that row opens
                     # with the numbers; the measuring answer is for the person who has the van.
                     "cheap", "cheaper", "cheapest", "cheaply", "cost", "costs", "price",
                     "how much", "man with a van", "hire a van",
                     # A move that has already hurt somebody is the body's answer: "my backs been
                     # killing me since i moved the sofa" was told to measure the stairwell.
                     "my back", "my backs", "bad back", "sore back", "killing me", "back hurts",
                     "pulled my back", "hurt my back", "done my back", "in agony"),
              # A house's size is not a bed being carried: "its a 3 bed with a garden", said in a
              # chat about moving, reached this row because "bed" is a key and the carried line
              # about the move met the second group. Only a line that is describing the home
              # stands the row down - a carried thing keeps the measuring card, so "a 4 bed
              # mattress", "a 2 bed settee" and "moving a bed into a 3 bedroom house" still fit.
              guard=_not_a_size_of_a_home),
        # Cats in a garden: nobody's table answered it, so the line was a shrug.
        # "is it cheaper to wash at 30" was "I don't know enough to answer that honestly" on main,
        # though the cost table further up this file holds the numbers.
        # This is the COST question only. The dial itself - "what temperature should i wash at",
        # "is 30 degrees enough" - is #3821's entry, so the second group holds cost words and nothing
        # else; "better", "enough" and "temperature" used to be here and took those lines, and also
        # "is it better to wash at night or morning", which is not even a laundry question.
        # The reply must not open with "Yes:": it catches cost questions of every shape, and "how much
        # does a wash cost" is not a yes/no.
        # Anything that names something other than laundry - a car, a dog, a window - is not this.
        entry("wash-at-30",
              (("30", "30c", "30 c", "30 degrees", "thirty", "20c", "40", "40c", "40 degrees",
                "wash", "washing", "laundry", "wash cycle"),
               ("cheaper", "cheap", "cost", "costs", "save", "saves", "saving", "worth",
                "money", "bill", "bills", "pence", "expensive", "add up")),
              "About 15p a wash at 30C in electricity, against 25p at 40C: heating the water is most "
              "of what a wash costs, so 30C is the cheapest cycle that still cleans everyday clothes, "
              "shirts and jeans properly with a modern detergent. Go to 40C for heavily soiled work "
              "clothes and 60C for towels, bedding and anything with a stomach bug or a cold, because "
              "that is about killing germs rather than shifting dirt. A cold or 20C cycle saves a few "
              "pence more but struggles with grease.",
              # "how much should i have in savings at 40" was this row's: "40" is one of its
              # temperatures and "savings" folds to "saving". The money words stand it down.
              avoid=("savings", "in savings", "have saved", "i have saved", "how much saved",
                     "by 40", "at 40", "by 50", "at 50", "by 60", "at 60", "pension", "pensions",
                     "retire", "retirement", "salary", "income", "put by", "put aside",
                     "how much should i have", "by now", "at my age",
                     # an age is not a temperature: "is it worth going to university at 30" was
                     # answered with the cost of a 30C wash
                     "university", "uni", "degree", "college", "college course", "a level",
                     "gcse", "apprenticeship", "masters", "phd", "exam", "exams",
                     "car", "cars", "van", "bike", "bicycle", "motorbike", "vehicle", "car wash",
                     "jet wash", "driveway", "patio", "bin", "bins", "wheelie", "dog", "dogs",
                     "puppy", "cat", "horse", "hair", "face", "hands", "shower", "bath", "window",
                     "windows", "brush", "brushes", "paint", "dishwasher", "dishes", "washing up",
                     "washing-up", "machine not", "not draining", "wont drain", "won't drain",
                     "smell", "smells", "mould", "mold", "drain", "hose", "filter", "wool",
                     "woollen", "woolen", "silk", "cashmere", "dry clean", "dryer", "tumble",
                     "iron", "stain", "stains", "shrink", "shrunk", "bleach", "whites", "darks",
                     # the towels and bedding answer names 60C and is the better one for those lines,
                     # so "what temperature should i wash towels at" must not land here
                     "towel", "towels", "bedding", "sheets", "sheet", "linen", "pillow", "pillows",
                     "duvet", "nappy", "nappies", "gym kit", "sports kit", "dishcloth", "tea towel",
                     "flannel", "blanket", "throws", "curtains", "mop",
                     # The key holds the bare digits "30" and "40" beside the money words, and a
                     # journey is said the same way: "the money one is 40 mins further" is a job
                     # choice, and it was answered with this card. A time or a distance in the line
                     # is the other question, so those words stand this row down - the same shape
                     # as "car" and "dishwasher" above, not a new mechanism.
                     "mins", "minute", "minutes", "miles", "further", "journey", "commute",
                     "commuting", "travel", "travelling"),
              # The key holds the bare figures "30" and "40", and a figure on its own is what a
              # bill, a battery or a bus fare is said with: with "month" no longer read as a when,
              # "my phone bill is 30 a month" and "button battery 30 a month" were both answered
              # with what a wash costs to run. A temperature is only the subject of a line that is
              # already about washing, so the row asks for the wash first. The same shape as the
              # "car" and "dishwasher" words above: a row standing aside for the other question.
              guard=_a_wash_is_named),
        entry("cats-garden", (("cat", "cats", "kitten", "kittens", "neighbours cat", "neighbour's cat"),
                              # The garden words and the ask words are two parts, not one. With the
                              # ask in with the nouns, a cat and "stop" were enough: "how do i stop my
                              # cat knocking the cups off" and "how do i stop my cat getting on the
                              # counters" were level with the right entry and won the tie on registry
                              # order, and both got soil and citrus peel. A garden noun is now
                              # required, and "how do i stop cats pooing in my flowerbed" still finds
                              # it.
                              ("garden", "gardens", "lawn", "flowerbed", "flower bed", "flowerbeds",
                               "borders", "vegetable patch", "sandpit", "poo", "poos", "pooing",
                               "toilet", "dig", "digging", "seedlings")),
              "Cats dig in bare, dry soil, so the reliable fix is to take that away: mulch the beds, lay "
              "chicken wire just under the surface, or plant through a membrane. Citrus peel, coffee "
              "grounds and a scattering of holly leaves or pine cones make the surface unpleasant, and a "
              "water pistol or a motion-triggered sprinkler teaches one cat to go elsewhere fast - "
              "renew it after rain, because scents fade.",
              # the cat's own behaviour is the pet answer's: scratching the sofa, the litter tray,
              # spraying indoors
              # "toilet" stays a key word here: a cat using a flowerbed as a toilet is the question
              avoid=("litter", "litter tray", "toilet training", "my cat is", "my cat wont",
                     "my cat won't", "pregnant", "fleas", "worms", "scratch", "scratching",
                     # A cat that wakes you is a sleep question, not a flowerbed one: "how do i
                     # stop my cat waking me up at 5am" reached this answer on cat + stop alone.
                     # The guard is the waking phrase, so a garden line that happens to say
                     # "stop" still keeps its soil answer.
                     "waking me", "wakes me", "woke me", "woken me", "wake me up", "waking us",
                     "wakes us", "woke us", "waking the baby", "waking my baby", "waking my partner",
                     "waking my husband", "waking my wife", "waking my child", "waking my kids",
                     "keeping me awake", "keeps me awake", "kept me awake", "keeping us awake",
                     "keeps us awake",
                     # a cat that bites or nips a hand is not a cat in the beds: "how do i stop my
                     # cat biting" keyed on cat + stop and got this answer
                     # A bed in a house is where a cat sleeps, and "beds" in this key turned
                     # "my cat sleeps on my bed" into soil advice. The singular is not in the key at
                     # all now, and the sleep words are a guard on the garden plural as well, so a
                     # cat asleep in a flower bed is not a cat digging in it.
                     "sleeps on my bed", "sleeping on my bed", "sleeps in my bed",
                     "sleeping in my bed", "sleeps on the bed", "sleeping on the bed",
                     "sleeps on our bed", "sleeping on our bed", "sleeps with me", "in bed with me",
                     "my pillow", "duvet", "bedroom",
                     # An accident indoors is not a flowerbed, and "poo" is a garden noun in this
                     # key, so "my cat pooed on the bed" was answered with mulch and chicken wire.
                     # A soft thing or a room in the line stands this row down and the pet answer
                     # takes it; a real garden line names the garden, the lawn or the beds.
                     "on the bed", "on my bed", "on our bed", "in the bed", "in my bed",
                     "on the carpet", "on the rug", "on the sofa", "on the settee", "on the couch",
                     "on the floor", "on the mat", "indoors", "in the house", "in the hall",
                     "in the kitchen", "in the bathroom", "in the bath", "litter",
                     "bite", "bites", "biting", "bit", "bit me", "nip", "nips", "nipping",
                     "scratches", "sofa", "couch", "furniture", "curtains", "spraying", "spray",
                     # What a cat carries in is hunting, and that is the pet answer's: with only
                     # "cat" and "stop" needed to reach this one, "my cat keeps leaving dead mice in
                     # my bed, how do i stop it" was a soil-and-citrus answer. A poo-or-digging
                     # line never names the animal it caught.
                     "mouse", "mice", "rat", "rats", "vole", "voles", "prey", "dead", "bird",
                     "birds", "pigeon", "pigeons", "brought", "brings", "bringing", "caught",
                     "dragged", "drops off")),
        # "how do i choose a paint colour" names no colour, so the table cannot answer it: the rule
        # is the answer, and it is its own entry because the pair words are not in the line at all.
        entry("colour-choice",
              (("colour", "colours", "color", "colors", "palette", "scheme"),
               ("choose", "choosing", "pick", "picking", "decide", "deciding", "help me", "stuck",
                "no idea", "go for", "paint", "room", "rooms", "hall", "hallway", "walls",
                "bedroom", "kitchen", "lounge", "living room",
                # "which colour for a small bathroom" was a shrug: a room this row answers for had
                # no word in its own key
                "bathroom", "bathrooms", "nursery")),
              ("Pick the thing you cannot change - the floor, the tiles, the worktop, the sofa - and "
               "take the wall "
               "colour out of it in a paler version of itself. Then add one deeper tone from the same "
               "family for a rug or cushions and a wood or a metal to warm it: three colours, one of "
               "them a near-neutral. Paint a sample patch you can watch in the morning and again under "
               "the lamp before you buy a tin, because a colour on a small card lies."),
              # a bare "what colour" or "which" is in every colour fact question - "what colour is
              # the sky" - so the gate is a choosing word, not the shape of the question.
              ask=("choose", "choosing", "pick", "picking", "decide", "deciding", "help me", "stuck",
                   "no idea", "how do i go for", "what colour should i paint",
                   "which colour should i paint",
                   # the same question without an "i": "what colour to paint a small room" and
                   # "what colour walls for a dark room" call the same row as "what colour should i
                   # paint my kitchen", and both were a shrug. Still no bare "what colour", so
                   # "what colour is the sky" stays out of a decorating answer.
                   "what colour to", "what colour for", "what colour walls", "what colour goes",
                   "colour to paint", "which paint", "which white", "colour for a room",
                   "colour for my",
                   # "which colour for the living room walls" names its choosing word as "which"
                   # and its room in the second half, and no gate above carries that shape
                   "which colour for", "which color for",
                   # the advice-shaped questions put "good", "best" or "neutral" where the choosing
                   # word normally sits, so the key matched and the gate alone said no: "what is a
                   # good neutral paint colour" was a punt with the answer one word away
                   "neutral", "good colour", "good paint", "best colour", "best paint",
                   "what paint colour", "what colour paint", "paint colour for"),
                   # ("paint colour" is left out on purpose: as a gate it also caught the follow-up
                   # "and what about the hallway", and the lead-in that names the new room turned
                   # into "Same as before". "which paint" covers "which paint colour for a room".)
              # a named colour is the table's question, and a spilled or peeling paint job is the
              # painting entry's
              avoid=("blue", "navy", "grey", "gray", "green", "sage", "teal", "black", "brown",
                     "beige", "cream", "white", "yellow", "mustard", "pink", "red", "terracotta",
                     "purple", "orange", "silver", "charcoal", "gold", "peel", "peeling", "bubbling",
                     "stain", "tin", "tins", "brush", "roller", "how do i paint", "spill", "spilled",
                     # a ceiling is its own colour question (see ceiling-colour below): "what colour
                     # should i paint the ceiling" got the floor-tiles-sofa palette for a whole room
                     "ceiling", "ceilings")),
        # A ceiling is not a wall. The palette rule above picks three colours for a room you look at
        # from the door, and it has nothing to say about the one surface over your head that decides
        # how much light comes back into the room.
        entry("ceiling-colour",
              (("ceiling", "ceilings"),
               ("colour", "color", "paint", "painting", "white", "which", "what colour",
                "what color")),
              "Matt white, or the palest tint of the wall colour, and one shade lighter than the walls "
              "if you want a tint at all: a ceiling painted as deep as the walls comes down on you and "
              "makes a small room feel lower. White bounces light back into the room, which is why a "
              "dark hallway or a north-facing room looks better with a warm white than a cool one, "
              "and a sunlit south room can take a cool white. In a kitchen or a bathroom use a "
              "moisture-resistant matt emulsion, because ordinary emulsion flakes over the steamy "
              "half of the room. Two coats of matt, rolled on a pole in strips, and paint the ceiling "
              "before the walls.",
              # a stain, a leak or a crack in the ceiling is its own answer in this file
              avoid=("stain", "stains", "leak", "leaking", "damp", "mould", "mold", "crack",
                     "cracks", "cracked", "peel", "peeling", "flake", "flaking", "spot", "spots",
                     "water", "fan", "fans", "light", "lights", "bulb", "insulation", "height"),
              guard=_asks_the_ceiling_colour,
              bias=1),
        # The whole colour family: what goes with a named colour, whether two colours work, and the
        # rule when the line names none. The colour is data in COLOUR_PARTNERS, so one row adds one.
        entry("colour-pairing",
              (("colour", "colours", "color", "colors", "goes with", "go with", "go together",
                "match", "matches", "matching", "pairs with", "pair with", "compliment", "scheme",
                "together", "clash", "clashes"),
               # the colour names are the second half of the key: "what goes with blue" needs one, and
               # "what colour should i paint the hall" is caught by the words above instead
               ("blue", "navy", "grey", "gray", "green", "sage", "teal", "black", "brown", "beige",
                "cream", "white", "yellow", "mustard", "pink", "red", "terracotta", "purple",
                "orange", "silver", "charcoal", "gold")),
              _colour_advice,
              # a how-to about painting, a tin of paint, tie-dye and a phone case's colour are not
              # this question; the paint it entry and the technology entries answer those.
              # Three neighbours already have their own answers and must keep them: a colour question
              # about food, about clothes, and about a fact ("what colour is the sky"). The words
              # below are the ones those lines use, not the room's.
              avoid=("paint brush", "paintbrush", "roller", "undercoat", "primer", "emulsion",
                     "dulux", "farrow", "tin", "tins", "stain", "mould", "peel", "peeling",
                     "bubbling", "screen", "phone", "nail varnish", "hair dye", "dye",
                     "how do i paint", "how to paint",
                     # food and drink
                     "salad", "plate", "plateful", "cheese", "recipe", "sauce", "cook", "cooking",
                     "eat", "eating", "food", "bread", "dish", "meal", "menu", "cake", "icing",
                     "curry", "pasta", "wine", "cocktail", "smoothie", "cocktail",
                     # clothes and how a person looks
                     "tie", "suit me", "suits me", "a suit", "grey suit", "navy suit", "black suit",
                     "blue suit", "suit jacket", "suit and tie", "dress", "outfit", "shoes", "boots",
                     "shirt", "jacket", "coat", "chinos", "trousers", "skirt", "jumper", "to wear",
                     "wearing", "what colours suit", "what colors suit", "what colour suits",
                     "what colour should i wear"),
              bias=1),
        entry("shower-goes-cold",
              (("shower", "showers", "shower head"),
               ("goes cold", "gone cold", "runs cold", "turns cold", "going cold", "cold after",
                "cold quickly", "not hot", "warm then cold", "hot then cold", "cuts out", "heat up",
                "hot water runs out", "boiler",
                # "my shower is cold" and "the electric shower is cold" name no moment and no
                # boiler, and they were getting an echo or a chat question back
                "is cold", "is lukewarm", "stays cold", "never hot", "never gets hot",
                "wont get hot", "won't get hot", "not getting hot", "runs lukewarm",
                "goes lukewarm", "is freezing", "water is cold", "runs hot")),
              "A shower that goes cold after a few minutes is usually the hot water, not the shower: "
              "a combi boiler only heats what you draw, so check whether the hot tap is still hot. If "
              "the tap is fine, the shower valve is scaled or failing, and cleaning the head in "
              "vinegar is the first free test. If the tap runs cold too, look at the boiler: its "
              "pressure gauge wants 1 to 1.5 bar while cold, and its fault code when it cuts out says "
              "what it is unhappy about.",
              ask=("cold", "hot", "cuts", "heat", "boiler", "gone", "goes", "runs", "turns",
                   "lukewarm", "freezing", "warm", "stays", "never"),
              # a shower that will not get hot at all, a shower that leaks and a shower going mouldy
              # are three other answers
              avoid=("mould", "mold", "leak", "leaking", "drip", "dripping", "smell", "drain",
                     "blocked", "pressure", "weak", "install", "fit a", "buy", "replace")),
        entry("stripped-screw",
              (("screw", "screws", "screw head", "screwdriver", "bolt", "nut"),
               ("stripped", "rounded", "rounded off", "wont come out", "won't come out",
                "stuck", "seized", "sheared", "chewed", "no grip", "spinning", "removed",
                "remove", "undo", "loosen", "stuck screw",
                # "i cant get this screw out" names the job and no state of the screw at all
                "get this screw out", "get the screw out", "get it out", "cant get")),
              "Once the cross is rounded there is no grip, so give it grip or give it something else "
              "to hold: press a wide rubber band or a steel-wool pad into the head and turn slowly "
              "with real downward force, or tap a slightly larger Torx or Phillips bit in with a "
              "hammer for a bite. If the head stands proud, cut a slot with a hacksaw and use a flat "
              "blade. Last resorts are pliers on the head, or drilling it out and using a screw "
              "extractor.",
              ask=("stripped", "rounded", "stuck", "seized", "chewed", "remove", "undo", "out"),
              bias=1,
              # putting a shelf up, a wall plug and a door hinge are other jobs
              avoid=("shelf", "wall plug", "raw plug", "rawlplug", "plasterboard", "stud", "hinge",
                     "drill bit", "anchor")),
        # --- the ordinary machine faults people describe by the noise ------------
        entry("small-appliance-not-heating",
              (("microwave", "microwaves", "microwave oven", "kettle", "kettles", "toaster",
                "toasters", "sandwich toaster"),
               ("not heating", "not heating up", "isnt heating", "isn't heating", "isnt heating up",
                "isn't heating up", "wont heat", "won't heat", "wont heat up", "won't heat up",
                "doesnt heat", "doesn't heat", "doesnt get hot", "stays cold", "stays cold food",
                "food stays cold", "food is cold", "cold food", "no heat", "not getting hot",
                "stopped heating", "heats nothing", "wont warm", "won't warm", "not warm",
                "cold in the middle", "lukewarm", "takes ages", "stone cold")),
              _small_appliance_not_heating,
              # "heating" and "heat" are the verb here and the noun in a hundred other lines, so the
              # row needs the appliance word as well as the fault words, and it stands aside for
              # every appliance that already has its own answer: the oven, the hob, the iron, the
              # tumble dryer, the air fryer and the boiler all have one, and a radiator that will not
              # heat is the plumbing question.
              avoid=("oven", "ovens", "cooker", "hob", "ring", "iron", "irons", "dryer",
                     "tumble dryer", "air fryer", "airfryer", "air-fryer", "boiler", "radiator",
                     "radiators", "immersion", "water", "shower",
                     # a microwave that sparks or smokes is the fire card, and the metal question has
                     # its own answer: neither is a repair question
                     "spark", "sparks", "sparking", "sparked", "smoke", "smokes", "smoking",
                     "flames", "caught fire", "on fire", "smell", "smells", "burning",
                     "metal", "foil", "tinfoil", "tin foil", "cutlery", "fork", "forks",
                     # cleaning is a different answer, and so is how it works
                     "clean", "cleaning", "descale", "limescale", "scale", "furred", "furring",
                     "noisy", "noise", "loud", "rattling", "humming",
                     # a thank-you that mentions the machine is not a fault
                     "thanks", "thank you", "worked", "sorted", "perfect", "glad", "helped",
                     # and the deciding question is the money rule's, not this one's
                     "worth replacing", "worth fixing", "worth repairing", "fix or replace",
                     "cheaper to buy", "should i buy", "which one", "best"),
              # "my kettle isnt heating up" ties this row with the general fault card and with the
              # money rule at five, and a tie is file order - so the appliance's own answer needs the
              # say-so to be the one the person gets.
              bias=1,
              # The answer is about the appliance, so it is the reply a line saying the appliance has
              # gone still gets: without this the line was read as one that needs a working machine.
              fault=True),
        # An oven that bakes one half of the tray and leaves the other pale is not the same fault
        # as an oven that will not heat: "my oven cooks unevenly" was answered with the element
        # test and an engineer, where the person wanted the shelf, the gap round the tin and the
        # thermometer. It comes before the not-heating row so the tie on "oven" goes to the
        # uneven bake.
        entry("oven-bakes-unevenly",
              (("oven", "cooker", "fan oven", "fan"),
               ("uneven", "unevenly", "cooks unevenly", "one side", "one half", "in patches",
                "patchy", "browns unevenly", "burns on one side", "burns on the top",
                "burns at the back", "takes longer", "front of",
                # the bottom catching is the same uneven bake, read from the other side
                "burn the bottom", "burns the bottom", "burning the bottom", "burns on the bottom",
                "burns underneath", "bottom burns", "burnt bottom", "burned bottom",
                "burns the base", "soggy bottom")),
              "Fill the middle of the shelf, not the edges: a fan oven runs hottest near the door "
              "and the sides, so keep tins in the middle third with a gap of two fingers between "
              "them, and turn the tray round halfway through. Give it 15 minutes to preheat and "
              "check the dial with a cheap oven thermometer - most ovens are out by 10 to 20C, and "
              "an oven that reads 20C low browns the back before the front. If it is always the "
              "bottom that catches, the tin is too low or it is a dark one: move it up a shelf, "
              "use a lighter tin and drop the heat 10C. If the same side is always pale while the "
              "other catches, that is the element or the fan, not your baking.",
              avoid=("not heating", "not heating up", "isnt heating", "isn't heating", "not hot",
                     "wont heat up", "won't heat up", "gas", "smell", "smells", "clean",
                     "cleaning", "oven chips", "recipe", "how long", "what temperature",
                     "gas mark", "turkey", "roast"),
              fault=True),
        entry("oven-not-heating",
              (("oven", "cooker"),
               ("not heating", "not heating up", "not hot", "not getting hot", "isnt heating",
                "isn't heating", "takes ages", "slow to heat", "cold", "warm up", "not warming",
                "temperature", "thermostat", "element", "uneven", "unevenly", "isnt getting hot",
                "isnt hot", "wont heat up", "won't heat up")),
              "On an electric oven the heating element is almost always the fault, and it fails in the "
              "way you can see: heat the oven for ten minutes in the dark and look for the element to "
              "glow red - a dull patch or a cold half is a broken element, about £20 to £40 for the part "
              "and £60 to £90 for an engineer. A fan oven that runs cold is often the fan motor or the "
              "thermostat instead. Turn the power off at the wall before you touch anything, and a gas "
              "oven that will not light is a gas-safe job, not a DIY one.",
              avoid=("fan oven", "roast", "roasting", "bake", "baking", "bread", "cake", "chicken",
                     "pizza", "chips", "recipe", "how long", "minutes", "turkey", "yorkshire",
                     "temperature for", "what temperature", "gas mark",
                     # a thank-you that mentions the oven is not a fault: "thanks, the oven
                     # temperature was perfect" was getting the element diagnosis
                     "thanks", "thank you", "perfect", "worked", "sorted", "glad", "helped",
                     "delicious", "came out", "was lovely", "brilliant", "spot on"),
              # The answer is about the oven, so it is the one reply a line saying the oven has
              # gone still gets: "my oven wont heat up" was read as a kitchen with no oven and the
              # element answer was thrown away as one that needs an oven.
              fault=True),
        entry("weak-flow",
              # A weak flow and a slow flow are two faults: one is at the outlet, the other is the
              # wait for the boiler, so the flow entry is checked first and only when the line says
              # the water is not strong. A shower is left to the shower entry (#1148): the same line
              # answered twice would be two entries for one meaning, and a shower has its own first
              # moves (the head, the hose, the mixer).
              (("tap", "taps", "mixer", "hot water", "cold water"),
               ("pressure", "low pressure", "weak", "dribble", "dribbles", "trickle", "low flow",
                "not strong", "losing pressure")),
              "A weak flow is almost always at the outlet, not in the boiler: unscrew the tap nozzle "
              "and soak it in descaler, open the isolator under the sink all the way, and check the "
              "stopcock has not been half shut. A combi only gives full flow at one tap at a time, so "
              "if the pressure drops when a second tap runs that is normal. If it is weak on every tap "
              "in the house, the stopcock or the mains is the place to look, not the plumbing.",
              bias=1,
              avoid=("bar", "gauge", "boiler pressure", "dropping", "radiators", "heating",
                     "shower", "showers", "showerhead", "shower head", "electric shower",
                     "power shower")),
        entry("hot-water-slow",
              # Not every cold shower is a slow pipe: a shower that runs cold or lukewarm is the
              # boiler, the mixer or the immersion, so only waiting-time words open this answer.
              (("hot water", "tap", "shower"),
               ("takes ages", "slow", "slowly", "come through", "waiting", "hot then cold")),
              "On a combi boiler, about 20 to 30 seconds is normal: you are waiting for the boiler to "
              "fire and for the hot water to travel down the pipe from it. If it is minutes, or the "
              "water runs hot then cold, the plate heat exchanger is scaled (a typical 5 to 10 year "
              "service item) or the boiler is undersized for two taps at once. If the flow is weak as "
              "well, check the isolator under the sink is fully open and unscrew the tap nozzle to "
              "clear the scale.",
              # a boiler losing pressure is its own answer; a weak shower or tap is this one
              avoid=("dropping", "bar", "gauge", "radiator", "radiators")),
        entry("floor-gone-dull",
              (("floor", "flooring", "floorboards"),
               ("dull", "dullness", "shiny", "shine", "worn", "wear", "scratched", "grey", "greyish",
                "tired", "restore", "polish")),
              "A dull wooden floor has worn through its finish, not its wood, so clean it with a "
              "diluted wood floor soap rather than a polish or a steam mop, then put a maintenance coat "
              "of the same hard wax oil or lacquer back on - one coat on the traffic lanes every year or "
              "two. Sanding is only for deep scratches; a whole-room sand and re-finish is £20 to £30 "
              "a square metre if you have it done.",
              avoid=("deep scratch", "scratches down", "scuffed", "laminate", "click", "install", "worktop",
                     "worktops", "counter", "countertop", "sink", "bath", "table")),
        entry("mice-in-the-house",
              (("mice", "mouse"),
               ("loft", "attic", "kitchen", "house", "flat", "garage", "shed", "cupboard", "droppings",
                "scratching", "noise", "noises", "get rid", "rid of", "infestation", "coming in",
                # "how do i stop mice getting in" names the way in rather than the room they are in,
                # and it was handed off to a pest controller without an answer.
                "getting in", "get in", "got in", "get into", "getting into", "coming into",
                "keep out", "keep them out", "stopping", "stop")),
              "Find the way in first: mice follow pipes and cables, so check the gap round the pipework "
              "under the sink, the air brick, and any gap wider than a pencil behind kitchen units, and "
              "block those with wire wool and filler. Then bait two or three traps along the wall, "
              "because mice run against edges, and clear the food source - a sealed bin and nothing left "
              "out overnight. Skip poison in a loft if there are pets or children, and the council pest "
              "control team is usually cheaper than a private firm.",
              # rats are a different job: outside they want locked bait stations and no bird seed,
              # and the indoor mouse advice is wrong for a shed, a garden or a compost heap
              avoid=("cat", "cats", "kitten", "dog", "hamster", "pet", "rat", "rats", "rodent",
                     "garden", "outside", "compost", "bird feeder", "bird seed", "field mouse"), report=True),

        # Woodlice are damp, not an infestation: nothing answered them at all, and "how do i get rid
        # of woodlice" was a search hedge.
        entry("woodlice",
              (("woodlice", "woodlouse", "wood lice", "slaters", "sow bugs", "pill bugs", "pillbugs",
                "isopods"),
               ("get rid", "rid of", "kill", "killing", "coming in", "come in", "in the house",
                "in my house", "in the kitchen", "in my kitchen", "in the bathroom", "everywhere",
                "keep finding", "finding", "remove", "stop", "why", "damp", "in the corner")),
              "Woodlice eat rotting wood and need damp, so drying the damp out is the whole job: fix "
              "the leak, clear wet leaves and timber away from the outside walls, and ventilate the "
              "room they keep appearing in. They do not damage anything in a dry house and they die "
              "within days indoors. Find the wet wood or the damp corner they are living under, and a "
              "dehumidifier or a line of salt buys you time while you sort it.",
              # they are not lice, not a bite and not a pest control job
              avoid=("bite", "bites", "bitten", "itch", "itching", "rash", "head lice", "nits",
                     "cat", "dog", "pet", "eat", "eating", "poison", "harmful", "dangerous",
                     "get in my hair"), report=True),

        # The mouse answer stands rats down on purpose - outside, the advice is the opposite one, and
        # there was no row to catch them: "how do i get rid of rats" was a shrug and "rats in the
        # garden" was the same, so a common garden question had nothing behind it.
        entry("rats-outside",
              (("rat", "rats", "rodent", "rodents"),
               ("garden", "shed", "outside", "outdoors", "compost", "bin", "bins", "bird feeder",
                "bird feeders", "bird seed", "decking", "garage", "drive", "greenhouse", "pond",
                "scratching", "droppings", "get rid", "rid of", "house", "loft", "under the",
                "in the day", "daytime", "getting in", "get in", "coming in", "keep out", "stop")),
              "Cut the food and the cover before you bait: take the bird feeders down or use a seed "
              "tray, keep the compost heap closed and stop putting cooked food in it, and clear the "
              "long grass and rubbish they are running behind. Then use two lockable bait stations "
              "along the wall where you have seen them and check them every couple of days - loose "
              "poison is a real risk to cats, dogs and children. If they are in the house, the "
              "council's pest control team is usually cheaper than a private firm.",
              # Somebody else's pet is not a rat, and a rat in the road is not your problem.
              avoid=("cat", "cats", "kitten", "dog", "dogs", "hamster", "pet", "pets", "gerbil",
                     "ferret", "road", "attic"), report=True),

        # "Is the bait safe with a toddler in the house" had no answer at all: the search hedge, or a
        # referral to a pest controller who was never asked. Poison, powder, pellets and cleaner are
        # ordinary things under a sink or in a shed, and the question about them is not what they are
        # for - it is who can reach them. One row reads the hazard and the person, because the rule is
        # the same for all of them: the box, the locked cupboard, the wash, and who to ring.
        entry("chemicals-and-a-child-or-pet",
              # not the bare adjectives "poison" and "poisonous": half the toxicity questions in the
              # house have them ("which plants are poisonous to cats" is the plants answer), so the
              # poison has to be the named product.
              (("bait", "rat bait", "mouse bait", "bait box", "bait station",
                "rat poison", "mouse poison", "rodenticide", "slug pellet", "slug pellets",
                "ant powder", "ant killer", "ant bait", "insect powder", "weedkiller", "weed killer",
                "pesticide", "mouse trap", "mouse traps", "rat trap", "rat traps",
                "flea bomb", "flea bombs", "fogger", "bug bomb", "oven cleaner", "drain cleaner",
                "bleach", "paint thinner", "turps", "turpentine", "antifreeze", "air freshener",
                "air fresheners", "diffuser", "reed diffuser", "plug in air freshener", "chemical",
                "chemicals",
                # A spray is in the room rather than in a cupboard, so the question about it is the
                # air and the person breathing it: "is the spray safe with a cat" was the cat's
                # cystitis card and "is fly spray safe with a baby" was the flying-with-a-baby one.
                "spray", "sprays", "aerosol", "fly spray", "insect spray", "ant spray",
                "wasp spray", "flea spray", "bug spray", "mosquito spray", "room spray",
                "fly killer", "insect killer"),
               ("toddler", "toddlers", "baby", "babies", "newborn", "child", "children", "kid",
                "kids", "grandchild", "grandchildren", "pregnant", "pregnancy", "expecting",
                "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pet",
                "pets", "hamster", "rabbit", "bird", "birds", "parrot", "fish", "safe", "unsafe",
                "dangerous", "harmful", "poisonous", "risky", "ok around", "get at",
                "breathe", "breathing", "breathe in", "breathing in", "fumes", "inhale",
                "in the room", "same room", "the room", "ventilate",
                # "is the spray safe with a cat" was the cat's cystitis card and now ties with
                # the rain-driving row at four, which takes it on order. The way it is asked is
                # "safe with"/"safe around"/"safe for", and a two-word match outweighs the one
                # word that row and this one share.
                "safe with", "safe around", "safe for", "safe to use", "is it safe",
                "ok with", "ok around", "harmful to", "harmful for", "dangerous to",
                "dangerous for", "bad for")),
              _chemical_safety,
              # somebody else's food is a vet question with its own answers (chocolate, onions,
              # grapes, lilies); and bleach on white cotton is the laundry answer, not this one.
              avoid=("chocolate", "onion", "onions", "garlic", "grape", "grapes", "raisin",
                     "raisins", "sultana", "sultanas", "xylitol", "lily", "lilies", "poinsettia",
                     "avocado", "alcohol", "caffeine", "whites", "white cotton", "cotton",
                     "laundry", "washing", "nappies", "nappy", "stain", "stains", "toilet",
                     "mould", "limescale", "descale", "drain", "blocked", "smell in", "how do i clean",
                     "how to clean",
                     # a plant, a bulb and a mushroom are poisonous without anybody putting them
                     # there: "which plants are poisonous to cats" is the houseplants answer.
                     "plant", "plants", "houseplant", "houseplants", "bulb", "bulbs", "flowers",
                     "shrub", "shrubs", "tree", "trees", "mushroom", "mushrooms", "berries",
                     "cat grass", "ivy", "holly", "oak", "acorn", "acorns",
                     # a spray is asked about the room it was used in, and the room's smell and
                     # its stains are other answers. Not "flea": the bomb that is the point of this
                     # row is a flea bomb, and as a bare avoid word it stood the row down on the
                     # one product people ask about most - "are flea bombs safe with a fish tank"
                     # and "can i use a flea bomb with a dog in the house" were the fleas card.
                     # "flea collar" stays: a collar on the animal is the fleas answer.
                     "stain", "stains", "carpet", "carpets", "mattress", "sofa", "odour",
                     "smell", "smells", "stinks", "flea collar", "bite", "bites",
                     "bitten", "itch", "itching", "marking", "litter",
                     # not "spraying": that is the form of "spray" the key wants, and as an avoid
                     # word it stood the whole row down for every line that said spray at all.
                     # A pet that has eaten the spray is a dose question rather than a fumes one,
                     # and the poisoning card asks the three things that matter: "my dog ate some
                     # fly spray" was this card once the spray was keyed here. Only the words that
                     # reach that card are fenced - "licked" and "drank" were tried too, and they
                     # stood the row down with nothing behind it, which lost the weedkiller card
                     # for "my cat licked weedkiller".
                     "ate", "eaten", "eating", "swallowed", "swallowing", "poisoned",
                     "keeps spraying", "is spraying", "spraying indoors", "cat spraying")),

        # A damp bathroom used to reach the fan-cleaning answer, which is the wrong diagnosis: the
        # water is on the walls because the air carries it there, and the fan is only part of the cure.
        entry("damp-bathroom",
              (("bathroom", "shower room", "ensuite", "en suite", "wet room", "loo", "toilet"),
               ("damp", "damper", "damp patch", "steamy", "steam", "condensation", "wet walls",
                "sweating", "always wet", "stays wet")),
              ("Run the extractor while you shower and for twenty minutes after, or open a window, and "
               "keep the door shut so the wet air stays in one room. Wipe the walls down, dry washing "
               "outside rather than over a radiator, and keep the heating on low: warm air holds the "
               "water, a cold bathroom drops it on the walls. If it carries on, the fan is "
               "under-powered or the duct is blocked."),
              # a leak, a dripping fan and mould treatment are other answers; a spray-on mould killer
              # is a step after the damp is fixed, not the fix.
              avoid=("leak", "leaks", "leaking", "dripping", "water coming", "from above", "roof",
                     "pipe", "burst", "remove mould", "get rid of the mould", "black mould", "kill")),
        # A bath or a shower is a choice between two everyday things, and the cleaning card took it
        # because `bath` is in its key. The numbers are the ones a person can act on: a five-minute
        # shower is roughly half the water of a full bath, and a warm bath an hour or two before bed
        # is one of the few home remedies for dropping off that has evidence behind it.
        # Length and frequency, which is a different question from which is nicer and from the water
        # meter: "how long should a bath be" and "do i need to shower every day" were answering the
        # water comparison, whose own second sentence admitted it was guessing at the question.
        entry("bath-length",
              (("bath", "baths", "bathtub", "shower", "showers", "showering", "shower gel"),
               ("how long", "how often", "every day", "daily", "too long", "how many times",
                "need to shower", "need to bathe", "should i shower", "should i bathe",
                "yes or no", "length of", "much time")),
              _bath_length,
              avoid=("clean", "cleaning", "cleaner", "scum", "limescale", "mould", "drain", "blocked",
                     "dog", "dogs", "cat", "cats", "baby", "babies", "newborn", "toddler", "plug",
                     "boiler", "leak", "before bed", "help me sleep",
                     # the comparison keeps its own lines
                     "or a shower", "or a bath", "bath or shower", "shower or a bath",
                     "better than", "which is better",
                     # and the time of day is another card's: "should i shower in the morning or at
                     # night" is a routine question, not a length one
                     "morning", "evening", "at night", "before work", "after work") + _BATH_CITY),

        # How hot the water should be is the first thing anyone asks about a bath, and no card
        # answered it: "what temperature should a bath be for a toddler" was the fever card ("rest,
        # drink plenty and take paracetamol") and "how warm should a baby bath be" was the
        # bottle-warming card ("stand the bottle in a jug of warm water"). The bath word is the
        # subject and a heat word is the question, and the fever and bottle rows stand aside for
        # it rather than the other way round, because a bath is not a body and not a feed.
        entry("bath-water-heat",
              (("bath", "baths", "bathtub", "bath tub", "bath water", "bathwater", "baby bath",
                "baby's bath", "babys bath", "babies bath", "toddler bath", "a bath", "the bath",
                # the compound reads as one thing to the word reader, so the ways people write it
                # are named here rather than left to the two ordinary words
                "baby bath be", "baby bath temperature", "bath be for a toddler",
                "bath be for a baby", "bath for a toddler", "bath for a baby"),
               ("how hot", "how warm", "too hot", "temperature", "degrees", "warm enough",
                "hot enough", "what temperature", "right temperature", "37c", "38c", "40c")),
              "A bath is right at 37 to 38C - the elbow test is the reliable one, because a hand "
              "that has been in the water stops being a judge. Run the cold in first and top it up "
              "with hot, never the other way round, and never add hot water with a child already "
              "in it. For a baby or a toddler it is the same 37 to 38C and only up to the waist "
              "when they are sitting, with the cold tap run last, and a bath above 40C is too hot "
              "for anyone to sit in for long.",
              # the cleaning job, the pet, the sleep bath and the shower comparison are other cards
              avoid=("clean", "cleaning", "cleaner", "scum", "limescale", "stain", "stains",
                     "mould", "drain", "blocked", "dog", "dogs", "cat", "cats", "plug",
                     "boiler", "leak", "hot tub", "jacuzzi", "sitz", "bath salts", "bath bomb",
                     "bath mat", "bathroom", "before bed", "help me sleep",
                     "or a shower", "or a bath", "bath or shower", "shower or a bath",
                     "which is better", "better than", "how long", "how often", "how deep",
                     "swimming", "swim", "pool", "spa") + _BATH_CITY,
              bias=1),

        # A baby in the bath is a safety question and the answer is a temperature and a depth, so it
        # is its own card rather than a comparison with a shower.
        # A bare "washing" was in the subject below and it made this row every "how often should i
        # wash <thing>" line in the language: "washing" matched and "how often" was the second
        # signal, so "how often should i wash my pyjamas" (the pyjamas-often row), "my coat" and "my
        # bra" (clothing) and "bedsheets" (bedsheets-often) all got 5cm of water at 37C. The subject
        # is now the bath itself, or a wash that says whose it is, so the row still answers "how do i
        # wash my newborn" and "how often should i bathe a baby" and leaves the rest of the washing
        # to the rows that keep it.
        entry("baby-bath",
              (("bath", "bathtub", "bathe", "bathing", "top and tail",
                "wash a baby", "wash the baby", "wash my baby", "wash your baby",
                "washing a baby", "washing the baby", "washing my baby", "washing your baby",
                "wash a newborn", "wash the newborn", "wash my newborn", "washing a newborn",
                "washing the newborn", "washing my newborn", "wash babys hair", "wash baby hair",
                "wash the babys hair", "wash the baby's hair", "wash my babys hair",
                "wash my baby's hair"),
               ("baby", "babies", "newborn", "infant", "toddler", "how hot", "temperature",
                "how often", "how deep", "safe", "first bath", "umbilical", "cord")),
              "Fill it to about 5 to 8 cm with water at 37 to 38C - elbow or wrist temperature, which "
              "feels neither warm nor cool - and have the towel, nappy and clean clothes within reach "
              "before you start, because you never leave a baby alone in water, not for a second. "
              "Support the head and shoulders with one forearm, wash with plain water for the first "
              "month or so, and keep the room warm since a wet baby loses heat fast. Twice or three "
              "times a week is enough for a newborn; top and tail in between.",
              avoid=("clean the bath", "cleaning", "scum", "limescale", "mould", "drain", "blocked",
                     "dog", "cat", "hot tub", "jacuzzi", "sitz", "bath salts", "bath bomb",
                     # a bath a pregnant woman is asking about is her own bath, not a baby's: "is a
                     # hot bath safe in pregnancy" was told to fill it 5 to 8 cm deep
                     "pregnant", "pregnancy", "trimester", "weeks pregnant",
                     # a load of washing is not a baby in water: "what temperature should i wash
                     # clothes at" matched "washing" here and "temperature" in the second group,
                     # and got 5cm of water at 37C instead of the washing-machine dial
                     "clothes", "laundry", "wash clothes", "washing clothes", "load of washing",
                     "washing machine", "colours", "colors", "darks", "whites", "lights",
                     "bedding", "sheets", "duvet", "towels",
                     # a bottle to wash and a load of baby clothes are the bottle-feeding and the
                     # baby-clothes rows in family.py: "how do i wash my babys bottles" was getting
                     # 5cm of bath water, and the bath avoids them there but not here
                     "bottle", "bottles", "sterilise", "sterilising", "sterilize", "formula", "pump",
                     "baby clothes", "babygrow", "baby grow", "vest", "muslin", "nappy", "nappies",
                     # and the rest of the washing nobody means as a bath: hands, dishes, a face, a
                     # shower. "what temperature should i wash my hands at" was getting 5cm of water
                     # at 37C because this row reads "washing" and "temperature" and nothing else
                     "hand", "hands", "dishes", "dish", "plates", "pots", "pans", "face", "hair",
                     "shower", "washing up", "car", "car wash",
                     # the rest of the linen: "sheets" and "towels" are above, and a pillow, a
                     # mattress or a bath mat is the same question with another word for it
                     "pillow", "pillows", "pillowcase", "pillowcases", "mattress", "bath towel",
                     "bath towels", "linen", "flannel", "flannels", "face cloth", "bath mat",
                     "curtain", "curtains")
                     + _BATH_CITY),

        entry("bath-or-shower",
              (("bath", "baths", "bathtub", "shower", "showers", "showering"),
               ("better", "best", "worse", "prefer", "rather", "or a bath", "or a shower",
                "bath or shower", "bath or a shower", "shower or bath", "shower or a bath",
                "instead of", "worth it",
                # "what uses less water a bath or a shower" asks about the water, not about which
                # is nicer, so the water words count as the ask too
                "less water", "more water", "uses less")),
              "Showering wins on time and water - five minutes with a normal head is about 40 to 50 "
              "litres against 80 or so for a full bath - so if it is the water you are asking about, "
              "shower and keep it short. Neither is better for your skin; long hot water is what "
              "leaves it tight and itchy, so keep it warm rather than hot and pat dry instead of "
              "rubbing. If a bath leaves you light-headed, get out slowly and drink some water.",
              # cleaning a bath or a screen is the cleaning lane's answer, and a bath for a baby, a
              # dog or a cat belongs to those cards
              avoid=("clean", "cleaning", "cleaner", "scum", "limescale", "stain", "stains", "mould",
                     "drain", "blocked", "dog", "dogs", "cat", "cats", "baby", "babies", "newborn",
                     "toddler", "plug", "water pressure", "boiler", "leak",
                     # a bath for sleep or for aches is the next card, whose answer leads with that
                     "before bed", "help me sleep", "aches", "ache", "relax", "unwind", "sore",
                     "stiff", "muscles",
                     # length and frequency are their own card below: "how long should a bath be"
                     # is not a comparison with a shower
                     "how long", "how often", "every day", "daily", "too long", "how many times")
                     + _BATH_CITY),

        # The same bath, asked about the night rather than the water meter: "is a hot bath good
        # before bed" wants the sleep answer first, not a comparison with a shower.
        entry("bath-for-sleep",
              (("bath", "baths", "bathtub", "hot bath", "warm bath", "long bath", "deep bath",
                "shower", "showers"),
               ("before bed", "before bedtime", "help me sleep", "help you sleep", "to sleep",
                "sleep", "aches", "ache", "aching", "relax", "unwind", "sore", "stiff", "muscles",
                "winding down", "cant sleep", "can't sleep")),
              "Yes - a warm bath 10 to 15 minutes long, an hour or two before bed, is one of the few "
              "home things that reliably helps you drop off: the water warms you and the climb back "
              "down afterwards is what makes you sleepy. Keep it warm rather than hot, which leaves "
              "skin tight and can make you light-headed, and get out slowly if the room spins. The "
              "same bath eases aching muscles for the same reason.",
              # the water comparison, the cleaning job and a bath for a baby or a pet are other cards
              avoid=("clean", "cleaning", "cleaner", "scum", "limescale", "stain", "mould", "drain",
                     "blocked", "dog", "dogs", "cat", "cats", "baby", "babies", "newborn", "toddler",
                     "plug", "boiler", "leak", "less water", "more water", "uses less")
                     + _BATH_CITY),

        # "is it normal to feel dizzy after a hot bath" was a shrug on main: the water comparison is
        # the wrong answer for it, because the question is what the heat does to your blood pressure.
        entry("bath-dizzy",
              (("bath", "hot bath", "bathtub", "shower", "hot shower", "jacuzzi", "hot tub"),
               ("dizzy", "dizziness", "light headed", "light-headed", "faint", "fainted", "spins",
                "spinning", "woozy", "sick", "nausea", "head rush", "stand up", "standing up")),
              "Hot water opens up the blood vessels near the skin, so blood pressure drops and standing "
              "up quickly leaves you light-headed - it is common, and it is not a sign of anything "
              "wrong in a healthy person. Get out slowly, sit down on the edge for a minute, keep the "
              "water warm rather than hot, drink some water and eat beforehand. If you actually faint, "
              "or it happens every time, or it comes with chest pain or palpitations, get it checked.",
              avoid=("clean", "cleaning", "scum", "limescale", "mould", "blocked", "drain", "dog",
                     "cat", "baby", "babies", "newborn", "toddler", "before bed", "help me sleep",
                     "less water", "more water") + _BATH_CITY),

        entry("bathroom-fan-wont-stop",
              (("fan", "extractor", "extractor fan", "ventilation"),
               ("runs all the time", "runs on", "wont turn off", "won't turn off",
                "wont switch off", "won't switch off", "wont go off", "won't go off",
                "never stops", "never turns off", "keeps running", "stays on", "left on",
                "all night", "all the time", "after the light goes off", "timer")),
              "Ten or fifteen minutes of running on after the light goes off is the timer doing its "
              "job, and it is what keeps the damp out. A fan that never stops has an overrun set too "
              "long, a stuck timer, or a humidistat turned up too high: take the cover off and look "
              "for the overrun screw or a dial inside, set the overrun to about fifteen minutes, and "
              "turn the humidistat down to around 60% - if neither is there, or it will not change, "
              "the module is a swap, around £25 to £60. A fan that runs only when nobody is in the "
              "room, or one that is still going after the isolator is off, is a wiring job.",
              # a fan that drips, leaks or drips condensation is a duct and airflow problem, not a
              # timer one, and the noisy entry below owns the noise and the cleaning.
              avoid=("drip", "drips", "dripping", "water", "leak", "leaks", "leaking",
                     "condensation", "cold", "black mould", "bathroom is damp", "steam",
                     # a machine's fan is not a bathroom extractor: "my laptop fan is loud all the
                     # time" was told to look for the overrun screw behind the cover, and a cooling
                     # fan that runs while the machine is on is the ordinary way it behaves
                     "laptop", "lap top", "computer", "pc", "desktop", "macbook", "mac book",
                     "phone", "console", "playstation", "ps4", "ps5", "xbox", "gpu",
                     "graphics card", "car", "van", "motorbike", "engine", "overheating",
                     "overheat", "oven", "fridge", "freezer", "tumble dryer"),
              # "keeps running after the light goes off" also matches the laundry-colour table's
              # "light" and "goes off": a fan that will not stop is this answer.
              bias=3),
        entry("bathroom-fan-noisy",
              (("bathroom", "shower", "loo", "toilet", "wet room", "ensuite"),
               # a damp or steamy bathroom is ventilation and a mould treatment, not a dirty fan:
               # "steam", "steamy", "damp" and "mould" were in this key and took `my bathroom is damp`
               # "not working" is not here: this row answers a fan that is noisy, humming or
               # weak, and with the phrase in the key "the shower is not working" and "the toilet
               # is not working" were both told to wipe the blades of an extractor fan. A fan that
               # is dead is the appliance or the isolator, and both have their own rows.
               ("fan", "extractor", "ventilation", "vent", "humming", "rattling", "buzzing", "whirring",
                "noisy", "loud", "noise", "weak")),
              "Clean the cover and the blades first: a dust-clogged fan in a steamy room is both weak "
              "and loud, and the grille usually comes off with a push and the blades wipe with a damp "
              "cloth once the isolator is off. A rattle is normally the cover or the backdraught flap in "
              "the duct; a buzz or a grind means the bearing has gone, and a new fan is £25 to £60 for "
              "the part with about an hour of an electrician. A fan that runs on for ten or fifteen "
              "minutes after the light goes off is the timer doing its job and is what actually stops "
              "the damp; one that never stops has a stuck timer or a humidistat set too high, and the "
              "module is a swap.",
              # buying, pricing and fitting a fan is a shopping job, and "damp" on its own is the
              # damp answer: this entry is the fan that already exists and is noisy or weak
              avoid=("kitchen", "hob", "cooker", "grease", "oven", "cost", "costs", "price",
                     # a fan that never stops is the timer or the humidistat, not the dust: the
                     # "wont stop" entry above leads with that
                     "runs all the time", "runs on", "wont turn off", "won't turn off",
                     "wont switch off", "won't switch off", "wont go off", "won't go off",
                     "never stops", "keeps running", "stays on", "after the light goes off",
                     # a fan that drips is water in the duct or condensation, not dust on a blade
                     "drip", "drips", "dripping", "water", "leak", "leaks", "leaking",
                     "condensation",
                     "how much", "cheap", "cheapest", "buy", "buying", "which", "best", "install",
                     "installing", "installation", "fitter", "fitted", "fit one", "replace",
                     "replacing", "replacement", "new fan", "new bathroom fan", "quote",
                     # a weak shower is a water fault, not a fan one: the shower entry (#1148)
                     # answers it, and "electric shower + weak" was getting the fan cleaned
                     "electric shower", "power shower", "shower pressure", "shower is weak",
                     "shower dribbles", "shower head", "showerhead")),
    # The radiator's ordinary life had no rows at all: the drain job, the dust between the fins and the
    # foil behind it were punts or another card ("how do i clean a radiator" got "that's beyond what I
    # know well"; "how do i drain a radiator" the plumber fence; "how do i take a radiator off the
    # wall" the pencil-rubber paint card).
    entry(
        "radiator-drain",
        (("drain", "draining", "drained", "empty", "emptying", "take off", "taking off",
          "take out", "remove", "removing", "come off", "swap", "replace",
          # "take a radiator off the wall" is the same job, and "take off" is not in it
          "off the wall", "to decorate", "decorating", "for decorating",
          # and so is putting the water back: "how do i fill a radiator back up" was a punt, and the
          # valve row then took it on the word "up"
          "fill", "filling", "fill up", "fill it up", "refill", "refilling", "top up",
          "topping up", "back up"),
         # not "towel rail": a follow-up "and the towel rail" after a radiator question belongs to
         # the chat, and a towel rail often has no numbered head to answer about
         ("radiator", "radiators", "rad", "rads",
          # the whole system is emptied the same way, only at the lowest drain cock
          "central heating", "the heating", "heating system", "the system")),
        "Turn the heating off and let it go cold, then close the valve at both ends: the wheelhead on "
        "the flow and the lockshield on the return, and count the turns on the lockshield so you can "
        "set it back the same, because that is what balances the house. Put a shallow tray and old "
        "towels under the bottom union and open the bleed valve at the top to let air in - the water "
        "comes out of the nut slowly and it is filthy black, so do it in short goes. Take the bracket "
        "off, and when you refit it open the bleed valve and top the pressure up at the filling loop "
        "to about 1.2 bar, then bleed every radiator once more. If it is a sealed combi system and the "
        "pressure will not hold, that is a plumber's job. For the whole house rather than one "
        "radiator, do the same at the lowest drain cock with every bleed valve open, because one "
        "radiator holds only a bucket or two.",
        # a radiator that is cold, noisy or leaking is a fault with its own row, and an oil-filled one
        # holds no water at all
        avoid=("cold", "colder", "not heating", "not getting hot", "cold at the top", "cold at the "
               "bottom", "bleed", "bleeding", "bleed it", "noisy", "banging", "knocking", "gurgling",
               "leak", "leaking", "dripping", "towel rail not", "boiler", "no pressure",
               "lost pressure", "pressure is low", "electric", "oil filled", "oil-filled",
               "oil radiator",
               "clothes", "dry clothes", "car", "van", "engine", "phone",
               "laptop", "battery", "pasta", "sink", "bath", "pond", "pool", "garden", "account",
               "bank", "pool of water",
               # a mark on the wall next to a radiator is the paint row's, not a plumbing job: "how
               # do i get scuff marks off the wall near the radiator" was told to drain it
               "scuff", "scuffs", "mark", "marks", "crayon", "ink", "stain", "stains", "dirty",
               "clean", "cleaning", "wipe", "wash", "paint", "painting", "repaint", "repainting",
               # rust is a paint-and-prep job on the outside of the metal, not plumbing
               "rust", "rusty", "rusting"),
        bias=3),

    entry(
        "radiator-clean",
        (("clean", "cleaning", "dust", "dusty", "hoover", "hoovering", "vacuum", "vacuuming",
          "wash", "wipe", "wipe down", "fins"),
         ("radiator", "radiators", "rad", "rads", "behind the radiator")),
        "Dust between the fins does more to cut the heat than anything you can do on the outside: run "
        "a vacuum cleaner's crevice tool down each gap with the heating off, and a long flexible "
        "duster gets the space behind without moving the radiator. For the paintwork plain warm water "
        "with a drop of washing-up liquid is enough - skip anything abrasive, which takes the enamel "
        "off - and keep water away from the valves and away from an electric one. Once before the "
        "heating goes on in autumn, and again in mid-winter if a room is slower to warm than it used "
        "to be.",
        avoid=("drain", "draining", "bleed", "bleeding", "leak", "leaking", "dripping", "cold",
               "not heating", "noisy", "banging", "gurgling", "paint", "painting", "decorate",
               "decorating", "rust", "rusty", "clothes", "towel rail", "boiler", "car", "van",
               "engine", "oven", "kitchen", "phone", "laptop", "floor", "carpet", "pond",
               # "how do i clean the wall behind the radiator" is about the wall, and the wall row
               # was answering it well before this row existed
               "wall", "walls", "skirting", "behind the wall", "the wall behind"),
        bias=2),

    entry(
        "radiator-foil",
        (("foil", "tin foil", "reflector", "reflective", "reflect", "insulate", "insulation"),
         ("radiator", "radiators", "rad", "behind")),
        "Worth it only on an outside wall with no cavity insulation: a sheet of radiator foil behind "
        "the radiator, shiny side facing the room, pushed back so it does not touch the brackets, "
        "gives you a few percent rather than the half the adverts claim. Keep the gap under the "
        "radiator clear, because that is where the cold air comes in and the warm air goes out - a "
        "shelf or a curtain hanging over the top cancels the gain. Foil on an inside wall, or over a "
        "cavity, does nothing at all.",
        avoid=("loft", "roof", "cavity wall", "wall insulation", "shed", "greenhouse", "drain",
               "bleed", "bleeding", "leak", "leaking", "cold", "noisy", "boiler", "cooker", "oven",
               "food", "garden", "pond", "cake", "chicken"),
        bias=2),

    # A ruck in a carpet is a room job, and the word is a rugby rule: "how do i stop a carpet from
    # rucking up" and "the carpet is rucking up" were both answered "A maul is a ball carrier held
    # up with teammates bound on to him". The sport row now stands down on the floor words, and
    # the ripple, the baggy edge and the rug that slides all want this answer.
    entry(
        "carpet-ruck",
        (("carpet", "carpets", "rug", "rugs", "carpet tile", "carpet tiles", "underlay",
          "gripper", "grippers", "flooring"),
         ("rucking", "rucked", "ruck", "rucks", "ripple", "ripples", "rippled", "wrinkle",
          "wrinkles", "wrinkled", "bubble", "bubbles", "bubbling", "baggy", "puckered",
          "puckering", "lifting", "come up", "coming up", "creased", "creases", "wavy",
          "sliding", "slides", "slipping", "moves", "moving", "loose")),
        "A carpet that ripples or wrinkles has stretched, and the fix is a re-stretch rather than "
        "an iron: the pile gives over the years, and a wet clean, a hot radiator or a heavy chair "
        "in one spot speeds it up. A fitter lifts the carpet off the gripper along one or two "
        "walls, pulls it tight with a knee kicker or a power stretcher and hooks it back on, which "
        "is an hour or two of work and far cheaper than a new carpet. One small bubble can be "
        "worked towards the nearest wall by hand and taken out the same way, and a bump that comes "
        "back after a day means the underlay has gone, not the carpet. A rug that slides on a "
        "wooden floor is the other problem: a rubber or felt underlay pad, or a strip of double-"
        "sided carpet tape, stops it without marking the boards.",
        bias=1),

        # A workshop edge is not a kitchen knife, a garden shear or a pair of scissors: each of
        # those has its own row and its own angle. A chisel, a plane iron and a masonry bit had
        # nothing at all - "how do i sharpen a chisel" got "that's beyond what I know well, sorry"
        # and "my drill bit is blunt" the shrug.
        entry("workshop-edge",
              (("chisel", "chisels", "wood chisel", "bevel edge chisel", "mortise chisel",
                "plane iron", "plane blade", "hand plane", "block plane",
                "drill bit", "drill bits", "masonry bit", "masonry bits", "hss bit", "spade bit",
                "auger bit", "forstner bit", "hole saw", "utility knife", "stanley knife",
                "craft knife"),
               ("sharpen", "sharpening", "sharpened", "sharper", "blunt", "dulled", "dull",
                "hone", "honing", "whetstone", "oilstone", "grind", "grinding", "file", "filing",
                "wont cut", "won't cut", "doesnt cut", "doesn't cut", "not cutting", "burr",
                "rounded", "chipped", "nicks", "nicked")),
              "Chisel and plane iron: the bevel is 25 degrees off the flat back, so a honing guide "
              "set to 25 and a strip of wet-and-dry on a flat tile does it - 240 grit if the edge "
              "is nicked, then 600 and 1200, ten strokes on the bevel, then lay the back flat on "
              "the finest paper and pull it back a few times to take the burr off. A blunt chisel "
              "crushes the wood and takes more force to steer, so it is the sharp one that is "
              "safer. A masonry bit is blunt when the tip is rounded: a few strokes of a diamond "
              "file on the wings either side of the point, at the angle they already have, brings "
              "it back. An HSS bit filed by hand is slow going and a new one costs a few pounds, so "
              "buy a bit rather than an afternoon; a Drill Doctor type jig, about \u00a330, earns "
              "its place only if you go through a lot of them. In a utility knife, swap the blade: "
              "a snap-off blade is sharper than anything you can dress at home.",
              # the other edges in the house have their own rows, and a sharp word about a picture
              # or a pain is not an edge at all
              avoid=("knife", "knives", "kitchen", "cooking", "chef", "scissors", "shears",
                     "secateurs", "hedge", "hedges", "axe", "chainsaw", "mower", "lawn", "pencil",
                     "pencil sharpener", "image", "photo", "picture quality", "sound", "pain",
                     "eyes", "vision", "glasses", "tooth", "teeth", "sharply"),
              bias=2),
        # A nail is a piece of metal before it is a fingernail. body.py stands its nail rows down
        # when the line has a workshop noun in it, which is why "how do i stop wood splitting when
        # i nail it" no longer gets "Nails grow about 3mm a month"; these two rows are what the
        # line falls to instead.
        entry("wood-splits-when-nailed",
              (("wood", "wooden", "plank", "planks", "timber", "batten", "battens", "board",
                "boards", "mdf", "hardwood", "softwood", "decking", "board end",
                "floorboard", "floorboards", "skirting", "skirting board", "skirting boards",
                "architrave", "beading", "joist", "joists", "stud", "studs", "door frame",
                "doorframe", "fence", "fencing", "shed"),
               ("split", "splits", "splitting", "crack", "cracks", "cracking", "splinter",
                "splinters", "splintering", "nail", "nails", "nailed", "nailing", "hammer",
                "pilot hole", "screw")),
              _the_wood_and_the_nail,
              # the joinery row answers how to fix two pieces together, and the sanding row is a
              # different job on the same board
              avoid=("glue two", "join", "joining", "dowel", "sanding", "sand it", "sandpaper",
                     "firewood", "fire wood", "log", "logs", "log burner", "stove", "season",
                     "seasoned", "kiln",
                     # a fence panel that came down is a post that has moved, and that row says
                     # so: "how do i nail a fence panel back up" is not a pilot hole
                     "fence panel", "fence panels", "panel", "panels", "post", "posts",
                     "gate", "back up"),
              # the firewood row holds "wood" and "when", which is half this line's words
              bias=2),
        entry("a-nail-in-a-wall",
              (("nail", "nails", "nailing", "nailed", "picture hook", "picture hooks",
                "rawlplug", "rawlplugs", "rawl plug", "rawl plugs", "wall plug", "wall plugs"),
               ("wall", "walls", "brick", "plasterboard", "stud", "studs", "picture",
                "pictures", "put up", "putting up", "hang", "hanging", "remove", "removing",
                "out", "pull", "old", "stuck", "left in")),
              _a_nail_in_the_wall,
              avoid=("fingernail", "fingernails", "toenail", "toenails", "my nail", "my nails",
                     "cut my nails", "bite", "biting", "polish", "varnish", "manicure",
                     "tyre", "tyres", "tire", "tires", "puncture", "wood", "plank", "timber",
                     "door", "doors", "decking", "fence", "fencing",
                     # a plasterboard wall already has a fixing card of its own, and it names the
                     # stud finder and the hollow-wall fixing, which is more than this row can
                     "plasterboard", "plaster board", "hollow wall", "hollow walls",
                     "stud finder", "plasterboard fixing", "plasterboard fixings"),
              # the wall-wipe and wall-mark rows hold "wall" and "remove" as well, and each of
              # them answers a mark or a grease film
              bias=2),
    ]

