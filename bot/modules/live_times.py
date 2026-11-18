"""A bus or train time is live, and the bot should say where the next one is.

"When is the next bus into town" and "has the 2 oclock train been cancelled" are not plans the
person told us about: the answer is a departure board, which the bot cannot see. The memory store
read the first as a thing coming up and said "Nothing so far - you haven't mentioned anything
coming up", and the knowledge base read the second as a delay-repay claim. Both are the wrong
subject for a question about a live service.

So this module answers only a line that names a scheduled service and asks for its time or
state, and it says the two things a friend can: I cannot see it from here, and the operator's own
app or the board at the stop has it. A line with "my" or "our" in it is their own plan and stays
with the memory store, and a line about the price or the worth of a ticket is not a time.
"""
import re

PRIORITY = 7001  # above the memory store (7000): a departure board is not a plan of theirs
# The knowledge cards for travel are specialists on this topic, and the arbiter prefers a
# specialist over a higher PRIORITY: "when is the next flight" was answered with the airport
# arrival card. This module is the one that read the line as a live time, so it says so.
ANSWERS = ("geography-and-travel",)

VEHICLE = re.compile(
    r"\b(?:bus|buses|train|trains|tube|tram|trams|coach|coaches|ferry|ferries|flight|flights)\b",
    re.I)
TIME = re.compile(
    r"\b(?:when|what\s+time|how\s+soon|next|on\s+time|delayed|cancelled|canceled|running|due|"
    r"leaves?|departs?|comes?|arrives?|platform|replacement|engineering\s+works?)\b", re.I)
STATUS = re.compile(
    r"\b(?:on\s+time|delayed|cancelled|canceled|running|due|replacement|engineering\s+works?)\b",
    re.I)
# A service of their own is the store's only when they have already given us its time:
# "train at 7.15 tomorrow" then "when is my train" is a callback, while the same line on its
# own is the departure board's. `_their_own_time` makes that call below.
PLATFORM = re.compile(r"\b(?:platform|station|stop|interchange|departure\s+board)\b", re.I)
# A station or a stop can be open or shut, and that is its opening hours, not a departure. The
# platform and the board are live; the building's own times are the knowledge base's.
PLACE_OPENING = re.compile(
    r"\b(?:train|bus|coach|tram|tube)\s+(?:station|stop)\b[^?.]{0,25}"
    r"\b(?:open|opens|opening|close|closes|closed|shut|shuts|hours)\b", re.I)
MONEY = re.compile(
    r"\b(?:worth|cost|costs|price|prices|fare|fares|cheap|cheaper|expensive|refund|refunds|"
    r"compensation|money|claim|claims|insurance|voucher|rebook|rebooking|delay\s+repay|pass|"
    r"rights?|entitled|entitlement|owed)\b",
    re.I)
# A line that asks what to do, not when the service is: "what time should i leave", "what if the
# flight is cancelled", "how do i claim a delayed flight" are planning and claims, and the travel
# cards answer them. The direct ask ("what time is the flight", "is it cancelled") has no such
# word.
ADVICE = re.compile(
    r"\b(?:what\s+if|should\s+(?:i|we)|what\s+time\s+should|how\s+(?:do|can|should)\s+(?:i|we)|"
    r"how\s+early|how\s+long\s+before|what\s+happens\s+if|do\s+(?:i|we)\s+need)\b", re.I)
# A delay or a disruption is what the travel cards are for: they say what the delay is worth and
# what to do about it, and a live board cannot tell the person either. "is my flight delayed" was
# answered by main with the 220-to-520-pound card, and this module's live line replaced it. Only
# a line that also asks for the next one, a time or a platform is still the board's.
DELAYED = re.compile(
    r"\b(?:delayed|delays?|running|on\s+time|disruption|disrupted)\b", re.I)
BOARD_ASK = re.compile(
    r"\b(?:next|last|first|when|what\s+time|how\s+soon|platform|departure\s+board|"
    r"station|stop|leaves?|departs?)\b", re.I)
# A flight's boarding cut-off, gate and landing time are published once and are on the ticket,
# not a live board: "what time is boarding for an 8pm flight" is a rule ("the gate shuts about
# 7.35pm"), and "what time is the flight" is their booking. The same line with a live word in it
# ("next", "delayed", "cancelled", "running", "platform", "leaves") is the board's.
FLIGHT_LIVE = re.compile(
    r"\b(?:next|last|first|running|on\s+time|delayed|cancelled|canceled|platform|leaves?|"
    r"departs?|replacement|engineering\s+works?)\b", re.I)
ASK = re.compile(
    r"^(?:when|what|how|is|are|was|were|has|have|did|does|do|can|could|will|would|any|next|"
    r"which)\b", re.I)
# "when is the train" with no time of their own is the departure board, not a plan. The shape
# keeps a story that starts "when i was young ..." out of the live answer.
WHEN_ASK = re.compile(
    r"^\s*when\s+(?:is|are|was|were|does|do|did|will|would|should|can|could)\b", re.I)
# A strike is news about the service, not its next departure: the answer is the operator's
# announcement, and a departure board cannot say whether the trains are running at all.
NEWS = re.compile(
    r"\b(?:strike|strikes|striking|walkout|walk\s*out|industrial\s+action|union|ballot|"
    r"announcement|news)\b", re.I)
# The service asked about, so two bus questions do not get the same words twice: the arbiter
# passes over a reply that repeats the last turn word for word, and "when is the next bus into
# town" after "when is the next bus" then fell to the memory store's empty "nothing coming up".
SERVICE = re.compile(
    r"\b(?:(?P<clock>[0-9]{1,2}(?::[0-9]{2})?\s*(?:o'?clock)?)\s+)?"
    r"(?:(?P<qual>next|night|last|first|early|late|morning|evening|midnight)\s+)?"
    r"(?P<vehicle>bus|train|tube|tram|coach|ferry|flight)\b"
    r"(?:\s+(?P<via>to|into|from)\s+"
    r"(?P<dest>[a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,4}))?", re.I)


def _service_named(clean):
    match = SERVICE.search(clean)
    if not match:
        return None
    words = [part for part in (match.group("clock"), match.group("qual"),
                               match.group("vehicle")) if part]
    name = " ".join(words)
    if match.group("dest"):
        dest = re.split(r"\b(?:cancelled|canceled|delayed|running|tomorrow|today|tonight|"
                        r"please|leave|leaves|go|goes|departs?|arrives?)\b",
                        match.group("dest"))[0]
        # The service name is a lead-in, so a destination that stops on a joining word is
        # worse than no destination: "ferry to the isle of" cut "wight" off. Four words
        # covers "the isle of wight"; a dangling "of" or "the" is dropped instead.
        dest = re.sub(r"(?:\s*\b(?:of|the|and|a|an|to|from|in|on|at|for|by)\b)+$", "",
                      dest.strip(), flags=re.I).strip()
        if dest:
            name += " " + match.group("via") + " " + dest
    return name


# A clock or a part of the day in something they said, which is their own plan's time. A bare
# count is not a clock: "theres 4 of us and we want the bus" is not a time they gave, and reading
# it as one stood the next "what time is the bus" down to the store's empty line.
CLOCK = re.compile(
    r"\b\d{1,2}[:.]\d{2}\s*(?:am|pm)?\b|"
    r"\b\d{1,2}\s*(?:am|pm|o'?clock)\b|"
    r"\b(?:at|by|around|about|before|after|from|until|till)\s+\d{1,2}\b|"
    r"\b\d{1,2}\s+(?:tomorrow|today|tonight)\b|"
    r"\b(?:this\s+)?(?:morning|afternoon|evening|noon|midnight)\b", re.I)
VEHICLE_STEM = {"buses": "bus", "trains": "train", "trams": "tram", "coaches": "coach",
                "ferries": "ferry", "flights": "flight"}
# What they have already told us the time of. "train at 7.15 tomorrow" then "what time is the
# train" is a callback to their own plan, which the memory store can quote; the live answer would
# lose the 7.15 they just gave us. A line that says "next", names a platform or asks for the
# status is still the live one.
def _their_own_time(clean, memory):
    if re.search(r"\b(?:next|last|first|night|early|late|platform|station|stop|running|on\s+time|"
                 r"delayed|cancelled|canceled|replacement)\b", clean):
        return False
    found = VEHICLE.search(clean)
    if not found:
        return False
    word = found.group(0).lower()
    stem = VEHICLE_STEM.get(word, word)
    try:
        turns = list(memory.get("turns") or ())
    except AttributeError:
        return False
    for turn in reversed(turns[-3:]):
        said = str(turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        if re.search(r"\b" + re.escape(stem) + r"s?\b", said) and CLOCK.search(said):
            return True
    return False


def _clean(text):
    return " ".join(str(text or "").lower().split())


def respond(text, memory):
    clean = _clean(text)
    if not clean or not VEHICLE.search(clean) or not TIME.search(clean):
        return None
    if MONEY.search(clean) or NEWS.search(clean) or PLACE_OPENING.search(clean) or \
            ADVICE.search(clean) or _their_own_time(clean, memory):
        return None
    if DELAYED.search(clean) and not BOARD_ASK.search(clean):
        return None
    flight = re.search(r"\b(?:flight|flights|plane)\b", clean) or (
        re.search(r"\bairport\b", clean) and not VEHICLE.search(clean))
    if flight and not FLIGHT_LIVE.search(clean):
        return None
    if not ASK.search(clean) and not str(text or "").strip().endswith("?"):
        return None
    if not re.search(r"\bnext\b", clean) and not STATUS.search(clean) and \
            not PLATFORM.search(clean) and not re.search(r"\bwhat\s+time\b", clean) and \
            not WHEN_ASK.search(clean):
        # A bare mention is not a departure ask. A "when is/are ..." question is, and if they
        # already gave us its time `_their_own_time` has stood this down above.
        return None
    service = _service_named(clean)
    lead = "For the " + service + ": " if service else ""
    found = SERVICE.search(clean)
    vehicle = found.group("vehicle").lower() if found else ""
    if re.search(r"\b(?:replacement|engineering\s+works?)\b", clean):
        return ("A replacement is the operator's own announcement: their app or site says where it "
                "leaves from and when, and the station's board carries it on the day.")
    # The vehicle the line names decides the reply: a bus to the airport is a bus, not a flight,
    # and a ferry is not a bus. "Airport" alone is read as a flight only when no service word is
    # there to say otherwise.
    if vehicle == "flight" or (not vehicle and re.search(r"\b(?:flight|flights|plane|airport)\b",
                                                         clean)):
        return lead + _the_wording(memory, FLIGHT)
    if vehicle == "ferry":
        return lead + _the_wording(memory, FERRY)
    if vehicle in ("train", "tube", "tram", "coach") or \
            re.search(r"\b(?:trains|trams|coaches)\b", clean):
        # The vehicle the line names is the one the reply names. A tram was told "I can't see live
        # train times ... the board at the station", and a tube the same, because one pool covered
        # all four. Which board keeps the times is the same question read the other way, so the
        # vehicle picks both the word and the place.
        named = VEHICLE_STEM.get(vehicle, vehicle)
        if not named:
            # "what time do the trams run until" names the plural, which the service pattern's
            # singular arm does not match, so the vehicle is read off the line itself.
            found_plural = re.search(
                r"\b(?:" + "|".join(sorted(VEHICLE_STEM)) + r")\b", clean)
            named = VEHICLE_STEM.get(found_plural.group(0), found_plural.group(0)) \
                if found_plural else "train"
        return lead + _the_wording(memory, RAIL).format(
            vehicle=named, where=THE_BOARD_THAT_KEEPS_THEM.get(named, "the board at the station"))
    return lead + _the_wording(memory, BUS)


# Two wordings of the same honest answer. The arbiter passes over a reply that says the last one
# again word for word, and a second live question in a row ("when is the next bus" then "when is
# the next bus into town") was dropped for the memory store's empty "nothing coming up" line. A
# live line never repeats the wording above it, and the same question twice gets the same answer
# in the other words a friend would use.
BUS = (
    "I can't see live bus times from here. The operator's app, or the timetable at the stop, has "
    "the next one; where the stop has a code, a text to it brings the times back. A journey "
    "planner puts the whole trip together.",
    "The next one is live, so nothing here can see it. The bus operator's app, or the timetable "
    "printed at the stop, has the time - text the stop's code where it has one - and a journey "
    "planner joins the trip up.",
)
# One pool for the rail and road services, filled with the vehicle the line named and the board
# that keeps its times: a tram's times are at the stop, not at the station, and a coach's at the
# coach station.
THE_BOARD_THAT_KEEPS_THEM = {
    "train": "the board at the station",
    "tube": "the board on the platform",
    "tram": "the board at the stop",
    "coach": "the board at the coach station",
}
RAIL = (
    "I can't see live {vehicle} times from here. The operator's app, or {where}, has "
    "the next one and any delay or cancellation; a journey planner puts the whole trip together.",
    "That one is a live departure, so the operator's app, or {where}, is where the "
    "next one and any delay or cancellation show up. A journey planner puts the whole trip together.",
)
# A name some other code or test still reads. `respond` fills `RAIL` now.
TRAIN = tuple(text.format(vehicle="train", where="the board at the station") for text in RAIL)
FLIGHT = (
    "I can't see live flights from here. The airline's app, or the airport's own departures board, "
    "has the gate and any delay; the booking reference brings it up.",
    "The gate and any delay are live, and I can't see them from here. The airline's app, or the "
    "airport's own departures board, has them, and the booking reference brings the booking up.",
)
FERRY = (
    "I can't see live ferry times from here. The operator's app, or the port's own departure board, "
    "has the next sailing and any delay; a journey planner puts the whole crossing together.",
    "That sailing is a live one, and I can't see it from here. The ferry operator's app, or the "
    "board at the port, has the next one and any delay; a journey planner joins the crossing up.",
)


def _the_wording(memory, wordings):
    try:
        turns = memory.get("turns") or ()
    except AttributeError:
        turns = ()
    return wordings[len(turns) % len(wordings)]


def TAKES_AS_IT_COMES(text, memory=None):
    """This module read the line whole as a live service, so it takes it as it comes.

    The travel cards are specialists on the same topic and the arbiter lets the specialist win;
    "has the 2 oclock train been cancelled" was answered with the Delay Repay claim. The hook is
    only true on a line the module already answers.
    """
    return respond(text, memory) is not None
