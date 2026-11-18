"""Bicycles: the everyday jobs and noises people ask about.

The answers lane owns this domain. Entries are keyed by the part and the problem (the
puncture, the chain skipping, the brakes rubbing) rather than by wording, so the same fact
answers "my bike tyre keeps going flat" and "how do I fix a puncture".

Why its own domain: a bicycle is not a car. A car tyre has a tread minimum and a bike tyre
has not, a car chain is a cam belt, and the pressure numbers are ten times apart, so
cars.py keeps two wheels out with NOT_BIKE and this table answers them. Motorbikes are left
alone: a motorbike is a motor vehicle with a battery, a chain drive and a licence, and the
car answers are closer to it than these are.
"""
import re

from .lookup import entry as _entry

# Bike lines reach the car topic ("my bike brakes rub" is a brakes question), so this domain
# says it answers the car topic as well as the home-and-diy one.
ANSWERS = ("cars", "home-and-diy", "fitness")

# A bicycle has to be in the line for any of these to answer, whatever else it carries. A car
# tyre and a bike tyre both "keep going down", a car's brakes grind and so do a bike's, and
# "how often should i check my tyre pressure" was answered with a bicycle number without this:
# the parts are shared words, so the two wheels are the thing that has to be said.
_IS_A_BIKE = ("bike", "bikes", "bicycle", "bicycles", "pushbike", "push bike", "cycle",
              "cycles", "cycling", "cyclist", "cyclists", "biking", "e-bike", "ebike",
              "two wheels",
              # parts only a bicycle has, for the lines that never say the word
              "handlebars", "handlebar", "cranks", "pedals", "saddle", "pannier", "panniers",
              # the named kinds of bar, because the line that asks about one never says "bike" and
              # a bare "bar" belongs to the boiler as well
              "drop bars", "flat bars", "riser bars", "bar ends", "aerobars", "bullhorn bars",
              "top tube", "chainring", "derailleur",
              # only a bicycle has these, and the line that names one never says "bike"
              "inner tube", "inner tubes", "tubeless", "quick release", "bike rack",
              # "my chain is rusty" never says bike, and a bicycle chain is what a chain is in
              # ordinary talk: the other chains a person owns are cut out below
              "chain", "chains")

# Not the tyre, the tube or the chain, though the line says "flat": a battery that goes flat is
# the motor or the phone, a light that does not work is a bulb, and "my bike battery keeps going
# flat" was pulling the wheel-off answer for a puncture. Only the tyre entries stand down for
# these, because the battery entry below is about exactly this.
# "Charge" in this list means a battery's charge, and a shop's charge is money: a price line
# about a puncture ("how much does a bike shop charge to fix a puncture") must not be read as a
# line about a battery, so the price entries take the list without those three words.
_NOT_A_TYRE = ("battery", "batteries", "charge", "charging", "charger", "motor", "screen",
               "phone", "laptop", "light", "lights", "lamp", "headlight", "headlights", "dynamo")
_NOT_A_TYRE_PRICE = tuple(word for word in _NOT_A_TYRE
                          if word not in ("charge", "charging", "charger"))

# Every reply here is about a bicycle, so a car, van or motorbike line passes: a clutch, an
# MOT and a tread depth have nothing to do with a chain and a puncture.
# A fall or a hurt part is the first-aid question, whoever was on the bike: the sizing and
# carrying rows answer somebody buying or fitting a bike, and none of them is that.
_A_HURT_PART = ("hurt", "hurts", "hurting", "injured", "grazed", "graze", "scraped",
                "scrape", "bleeding")

_NOT_A_BIKE = ("car", "cars", "van", "vans", "motorbike", "motorbikes", "motorcycle",
               "motorcycles", "moped", "mopeds", "scooter", "scooters", "lorry", "truck",
               "engine", "mot", "clutch", "gearbox", "diesel", "petrol", "mph",
               "tread depth", "speedometer", "windscreen", "dashboard", "garage",
               # A child's scooter, a skateboard and a shopping trolley all have wheels
               "skateboard", "scooter for", "trolley", "wheelchair", "pushchair", "pram",
               # the other chains: a saw, a door, a gate and a piece of jewellery are not driven
               "chainsaw", "chain saw", "door chain", "security chain", "gate chain",
               "necklace", "necklaces", "bracelet", "bracelets", "jewellery", "jewelry",
               # the metal says it is jewellery even when the line never names the thing: "how do
               # i clean a silver chain" reached the bicycle chain, because "chain" on its own is
               # read as proof of a bike
               "gold", "silver", "pendant", "locket", "earring", "earrings", "bangle", "brooch",
               "watch chain", "chain of office", "food chain", "chain reaction",
               # ...and the other cycles: a wash cycle, a spin cycle and an eco cycle belong to the
               # machine, and "how much water does a dishwasher use per cycle" was sent to the
               # price of a bicycle because "cycle" alone is read as proof of a bike here.
               "dishwasher", "dishwashers", "washing machine", "washing machines", "washer",
               "washers", "tumble dryer", "tumble drier", "dryer", "dryers", "fridge",
               "freezer", "oven", "cooker", "microwave", "kettle", "toaster",
               "wash cycle", "spin cycle", "eco cycle", "dry cycle", "per cycle")


# The electric bike, which is a bicycle with a motor rather than a motor vehicle: the words a
# person uses for one, and nothing else. "ebike" is written both ways and both are common.
_IS_AN_EBIKE = ("ebike", "ebikes", "e-bike", "e-bikes", "electric bike", "electric bikes",
                "electric bicycle", "electric bicycles", "pedal assist", "pedal-assist",
                "electric cycle", "electric pushbike")

# A moped, a scooter and a motorbike are motor vehicles: the licence, the insurance and the
# speed limit are the car's answer, not this one. A car is deliberately not here - "is it
# cheaper than a car" is exactly the question the worth-it answer is for.
_NOT_AN_EBIKE = ("moped", "mopeds", "motorbike", "motorbikes", "motorcycle", "motorcycles",
                 "scooter", "scooters", "quad bike", "quadbike", "van", "lorry", "truck",
                 "engine", "clutch", "gearbox", "diesel", "mot")


# Carrying a child on a bike is a seat or a trailer, not the size of a child's bike: a child seat
# clamps to the frame and there is an inside-leg answer that is wrong for every one of these.
# The words are here, once, because the row that answers them and the sizing row that stands
# down for them have to agree: one list, two uses.
_CARRYING = ("child seat", "childs seat", "child's seat", "child bike seat", "bike seat",
             "seat for a child", "seat for a toddler", "carrier", "bike carrier",
             "child carrier", "trailer", "bike trailer", "on the back of", "back of my bike",
             "carry a child", "carry my child", "carry a kid", "carry my kid", "carry the kids",
             "carry two", "carrying a child", "carrying children", "carrying two",
             "carrying a toddler", "take my child", "take my kid", "take my toddler",
             "take the kids", "take a child",
             # the child, and the bike, in the words of a parent: nothing here says "seat"
             "child on a bike", "child on my bike", "children on a bike", "children on my bike",
             "kid on a bike", "kids on a bike", "kids on my bike", "toddler on a bike",
             "toddler on my bike", "baby on a bike", "baby on my bike", "ride on the back",
             "go on a bike", "go on my bike", "ride on a bike", "on the back of a bike")


def _bike(needs):
    """The problem's own words. The bicycle itself is the entry's `ask`, which is a hard yes/no."""
    return tuple(needs)


_BIKE_PACK_FAULT = (
    "A battery that keeps going flat is worn or being charged badly: an e-bike pack is good for "
    "roughly 300 to 500 full charges, so a bike that has commuted for four or five years loses "
    "range before the pack fails outright. Charge it indoors at room temperature, leave it between "
    "about 20 and 80 per cent on short trips, and store it over winter at around half charge "
    "rather than empty. A charger that will not start on a freezing pack is normal - let the "
    "battery warm up for an hour - but one that cuts out after a few minutes is usually the "
    "charger, not the battery.")
_BIKE_PACK_PRICE = ("A new e-bike battery is usually £250 to £500, and £400 to £700 for a big brand "
                    "pack, which is often half what the whole bike cost; a specialist rebuild of "
                    "your own pack is cheaper, around £150 to £300.")
_BIKE_PACK_RANGE = ("Range is roughly one mile per 10Wh, so a 400Wh pack goes about 30 to 40 miles "
                    "on mixed assistance and 20 in the hills.")
_BIKE_PACK_LIFE = ("A pack is good for roughly 300 to 500 full charges, which for most riders is 3 "
                   "to 5 years; it is worn when the range has fallen by about a fifth.")
_BIKE_PACK_CARE = ("Charge it in the house rather than the shed, keep it between half and full if "
                   "it is going to sit for months, and use the charger that came with the bike: a "
                   "cheap same-voltage one from a marketplace seller is the fire risk.")

# The words that ask a price, a range or a life. Anything else about a pack - it will not charge,
# it loses range, where to store it - is a fault or a care question, and the fault paragraph
# answers that: the price of a new pack is no help to someone whose charger has stopped.
_PRICE_ASK = ("cost", "price", "how much", "cheapest", "worth", "new battery", "replace",
              "replacement", "rebuild")
_RANGE_ASK = ("how far", "range", "miles", "distance", "go on a charge", "how many miles")
_LIFE_ASK = ("how long", "life", "last", "lasts", "years", "how many charges")


def _bike_battery(memory, understood):
    """The pack answer the line asked for: a price, a range, a life, or what to do about a fault."""
    clean = (understood.get("clean") or "").lower()
    if any(word in clean for word in _PRICE_ASK):
        return " ".join((_BIKE_PACK_PRICE, _BIKE_PACK_RANGE, _BIKE_PACK_CARE))
    if any(word in clean for word in _RANGE_ASK):
        return " ".join((_BIKE_PACK_RANGE, _BIKE_PACK_LIFE, _BIKE_PACK_PRICE))
    if any(word in clean for word in _LIFE_ASK):
        return " ".join((_BIKE_PACK_LIFE, _BIKE_PACK_PRICE, _BIKE_PACK_CARE))
    return _BIKE_PACK_FAULT


def _bike_battery_earlier(memory, understood):
    """The same answers for a follow-up, only while the chat is still about a bicycle.

    The line may name the bike itself ("how long does an ebike battery last") or leave it to the
    turn before ("and how much is a new battery"); either way the bike is the subject. A line
    with no bicycle in it or before it stands the entry down, and the phone keeps its own card.
    """
    said = [str((understood or {}).get("clean") or "")]
    for one in (memory or {}).get("turns") or []:
        if isinstance(one, dict):
            said.append(str(one.get("user") or ""))
    said = " ".join(said).lower()
    if not any(word in said for word in _IS_A_BIKE):
        return ""
    return _bike_battery(memory, understood)


# What to put on, which main answered with the start-cycling card: the route, the lock and
# the shoes, and nothing about clothes. Ordinary clothes are the answer, and the change at
# work is the trick that makes them work. A line that names a hot day gets the hot version:
# "what to wear cycling when its hot" was reaching the washing-machine temperature card, and
# a winter paragraph in answer to a summer question is the same fault in this row.
_BIKE_WEAR_ANY = (
    "Wear what you can sweat in and change at work: an ordinary breathable top, trousers "
    "you can pedal in or shorts, and a thin waterproof that packs into a pocket for the rain. "
    "Flat trainers pedal fine, and you do not need cleats or padded shorts for a commute. In "
    "the cold, gloves, a thin hat under the helmet and a windproof layer beat a thick "
    "coat, and a bright top and a rear light matter more than anything else you can buy.")
_BIKE_WEAR_HOT = (
    "Wear as little as you can get away with and carry the rest: a light breathable top, "
    "shorts or thin trousers, and a cap or a buff under the helmet. Sunglasses, sunscreen on "
    "the back of your neck, arms and knees, and a bottle on the frame. A backpack is the thing "
    "that soaks your back, so a rack and panniers or a bar bag pay for themselves in summer, "
    "and a thin long-sleeved top in a pocket covers the ride home if you burn.")
_HOT_WEATHER = ("summer", "hot", "warm", "heatwave", "heat wave", "sunny", "sun",
                "boiling", "humid")
# Whole words, because "sun" inside "sunday" is a day of the week and not a season: a Sunday
# ride in November was getting mid-July clothes.
_HOT_WEATHER_RE = re.compile(r"\b(?:" + "|".join(_HOT_WEATHER) + r")\b")


def _bike_wear(memory, understood):
    """The clothes for the day: the same answer, with the hot one when the line names one."""
    clean = (understood.get("clean") or "").lower()
    if _HOT_WEATHER_RE.search(clean):
        return _BIKE_WEAR_HOT
    return _BIKE_WEAR_ANY


# What a shop does to a bicycle, what it charges for it and how often it wants doing. Two rows
# and not one, because the first sentence has to be the answer: the person who asks the price
# wants the price first, and the person who asks how often wants the once-a-year first - leading
# a "how often should i service my bike" with a price answers a question nobody asked. Each row
# is plain text for a reason: the answering module reads the figure out of a card to decide which
# card owns a price ask, and a card it cannot read is a card it cannot choose.
BIKE_SERVICE = (
    "A shop service is £50 to £95 for the basic job - the bearings, the gears, the brakes and "
    "the wheels trued - or £120 to £200 for a full strip-down and rebuild. Once a year is the "
    "usual answer, sooner if you ride in the wet or cover a few thousand miles, and it is worth "
    "it when the gears skip or the brakes feel spongy. Check the chain, the cassette, the brake "
    "pads and the tyres yourself, and ask what the price covers before you book.")
BIKE_SERVICE_WHEN = (
    "Once a year is the usual answer, sooner if you ride in the wet or cover a few thousand "
    "miles: a basic service is £50 to £95, which covers the bearings, the gears, the brakes and "
    "the wheels trued, or £120 to £200 for a full strip-down. Check the chain, the cassette, the "
    "brake pads and the tyres yourself with a chain checker and a ruler, and ask what the price "
    "covers before you book.")

# The words a service is asked about by name, shared by the two rows below.
_BIKE_SERVICE_SAID = ("service", "serviced", "servicing", "tune up", "tuneup", "overhaul",
                      "mechanic", "bike shop", "check over",
                      # A bike that has stood for years is the same question - what to have done
                      # to it - and "my bike has been sitting for years what should i get done"
                      # reached the pets domain's neutering card, which takes the phrase "get
                      # done" and needs no animal in the line. These are this row's words; the
                      # bike word is the ask, so a car or a house still cannot reach it.
                      "sitting", "sat", "sat for years", "sitting for years", "been sitting",
                      "stood", "stood for years", "not been used", "hasn't been used", "get done",
                      "getting done", "back on the road", "out of the shed", "in the garage for",
                      "in the shed for", "stored for years", "stored for", "years in the garage",
                      "years in the shed")

# How often it wants doing - the frequency words, which the price row stands down for.
_BIKE_SERVICE_WHEN_SAID = ("how often", "how regularly", "how frequently", "when should",
                           "when do i need", "when does it need", "do i need", "does my bike need",
                           "does it need", "is it due", "how many times a", "annual", "annually",
                           "every year", "each year", "once a year")

# The price, the worth and the list of jobs - the questions the price row answers.
_BIKE_SERVICE_PRICE_SAID = ("cost", "costs", "price", "prices", "how much", "what do they do",
                            "worth", "worth it", "worth getting", "worth paying", "any point",
                            "include", "includes", "included", "cover", "covers", "do they do",
                            "do it", "should", "how", "miles", "again", "what to do", "year",
                            "years",
                            # a bike that has stood for years is this card, and the words it is
                            # said with are the ones in the key above: the pets domain takes the
                            # bare phrase "get done" and answered it with neutering until these
                            # were asked for here too.
                            "get done", "getting done", "should i get done", "not been used",
                            "sat for years", "sitting for years", "stood for years",
                            "back on the road")

# So that a "how often" line lands on the frequency row and not the price row, the frequency
# row carries the higher bias: the words "service" plus "how often" score the same on both.
_BIKE_SERVICE_WHEN_BIAS = 4

# "how should i lock my bike outside the shops" is the lock, not the service.
_BIKE_SERVICE_AVOID = ("lock", "locks", "locking", "locked", "d-lock", "u-lock", "chain lock",
                       "cable lock", "padlock", "secure", "stolen", "theft", "outside the shops",
                       "shops")


# The fit card answered every line with the saddle, while the parts it covers are three: the
# saddle, the bars and the reach. A line that names the bars wants the bars - and it is asking one
# of two things, which bars to get or how to move the ones it has. So the reply is read from the
# line: the choice for "drop bars or flat bars" and "are drop bars comfortable", the stem for
# "my bars are too low" and "the bars feel too far away", and the saddle first only when the line
# is about the seat.
_BAR_WORDS = frozenset(("bars", "bar", "handlebars", "handlebar", "drop bars", "flat bars",
                        "riser bars", "bar ends", "aerobars", "bullhorn bars", "stem",
                        "reach", "tops", "hoods"))
_SEAT_WORDS = frozenset(("saddle", "seat", "seatpost", "seat height", "seat post"))
# "bar" is a substring of "bargain", "barely" and "barbecue", so the whole-word test is what
# decides it: "is a second hand bike a bargain" was read as a question about the bars because
# the bargain had a "bar" in it. A bar named on its own still has to be the word on its own.
_A_BAR_NAMED = re.compile(r"\bbars?\b|\bhandlebars?\b", re.I)
_BAR_CHOICE = re.compile(r"\b(?:or|instead|which|better|best|worth|comfortable|comfort|"
                         r"get|buy|change|swap|switch)\b")
_BAR_MOVE = re.compile(r"\b(?:too\s+(?:low|high|far|long|close|short)|low|high|far|raise|"
                       r"lower|adjust|moving|move|numb|tingl\w*|sore|ache|hurt\w*)\b")

WHICH_BARS = (
    "Drop bars put your hands in three or four positions, which is what makes them comfortable on "
    "a long ride, and they drop your chest for less wind; flat bars give more control and a better "
    "view in traffic, and are the right answer for a town bike. If you ride for an hour or more on "
    "open roads, drops are worth the getting used to; if your rides are short or in traffic, flat "
    "bars with bar ends are the easier choice. Width matters as much as shape: about as wide as "
    "your shoulders, and a little wider for control off road.")

MOVING_BARS = (
    "The height is set at the stem: undo the two bolts on the side and add or remove the spacers "
    "under it, which moves the bars 5 to 10mm at a time - tighten them back to just snug and check "
    "the steering turns freely. Too far away is a shorter stem, 10 or 20mm shorter, or a bar with "
    "less reach; too low for good is more spacers, and if the steerer has none left, a riser bar or "
    "a stem with a steeper angle does the same job. Numb or tingling hands is the bars too far or "
    "too low, or the saddle tipped nose-down, and it is worth fixing before a long ride rather than "
    "riding through.")


def _bike_fit(memory, understood):
    """Which bars to get, how to move the bars you have, or the saddle first."""
    reading = understood or {}
    said = str(reading.get("clean") or reading.get("text") or "").lower()
    if not said:
        said = " ".join(str(one) for one in (reading.get("words") or ())).lower()
    words = set(str(one).lower() for one in (reading.get("words") or ()))
    names_bars = bool(words & _BAR_WORDS) or bool(_A_BAR_NAMED.search(said))
    names_seat = bool(words & _SEAT_WORDS)
    if names_bars and not names_seat:
        # a bar named with a fault of height or reach is the stem; a bar named on its own, or
        # with a choice between two of them, is the choice between them
        if _BAR_MOVE.search(said) and not _BAR_CHOICE.search(said):
            return MOVING_BARS
        return WHICH_BARS
    return SADDLE_FIRST


SADDLE_FIRST = (
           "Set the saddle height first: heel on the pedal at the bottom of the stroke should "
           "straighten the leg, so with the ball of the foot on the pedal the knee keeps a slight "
           "bend. Too low aches the front of the knee, too high rocks the hips and hurts behind "
           "it. Then slide the saddle so the knee sits over the pedal axle, and aching hands or "
           "neck mean the bars are too far away. Numbness in the hands, feet or groin is the one "
           "thing not to ride through.")

ENTRIES = [
    # --- the flat tyre -----------------------------------------------------
    _entry("bike-puncture",
           (("puncture", "punctures", "punctured", "flat tyre", "flat tyres", "tyre flat", "flat",
             "tire flat", "tyre keeps going flat", "keeps going flat", "keeps going down",
             "losing air", "slow puncture", "inner tube", "tube",
             # "how do i change a bike tyre" and "my tubeless tyre wont seal" are the same job
             "tyre change", "change the tyre", "change a tyre", "new tyre", "new tyres",
             "tubeless", "tyre lever", "tyre levers",
             # once the bike gate has passed, a tyre on its own is the flat-tyre job
             "tyre", "tyres", "tire", "tires", "wheel", "wheels"),
            _bike(("fix", "repair", "mend", "patch", "change", "how", "again", "why", "every",
                   "week", "day", "going", "tyre", "tire", "wheel",
                   # a puncture said as a fact rather than as a job: "my bike has a puncture",
                   # "got a flat on my bike" and "i got a puncture on my bike" carried none of
                   # the words above and got nothing at all, so the one thing a person needs to
                   # be told - take the wheel off - was never said.
                   "has", "have", "had", "got", "get", "getting", "today", "yesterday"))),
           "Take the wheel off, unseat one side of the tyre with two levers, pull the tube out "
           "and find the hole by pumping it up and listening or dunking it in water. Patch it or "
           "fit a new tube, then run a finger round the inside of the tyre for the thorn or glass "
           "that made the hole, or the new tube goes the same way. One that keeps going flat "
           "usually still has the sharp thing in it, or a tube pinched under a lever.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE + _NOT_A_TYRE, bias=2),

    # What a tyre or a tube costs, which is the ask the car's price card cannot answer: in a chat
    # about a second-hand bicycle, "how much do tyres cost" was reaching the puncture repair, and
    # with that turned down for holding no price it fell to the car's card - £55 to £80 a corner
    # and a 205/55 R16 sidewall, said to somebody buying a bicycle.
    # The price of the repair itself, which neither the how-to nor the tyre price answers:
    # "how much to fix a bike puncture" was the wheel-off method and "how much does a bike shop
    # charge to fix a puncture" was the e-bike battery, because a shop's *charge* is not a
    # battery's charge. The figure is the whole reason people ask, so it goes first.
    _entry("bike-puncture-price",
           (("puncture", "punctures", "punctured", "flat tyre", "flat tyres", "tyre flat",
             "slow puncture", "inner tube", "inner tubes", "fix a puncture", "mend a puncture",
             "repair a puncture", "patch a puncture", "fitted"),
            # only the words that ask a price: "how do i fix a puncture on my bike" is the
            # method, and a "fix" in the ask list made it the price
            _bike(("how much", "cost", "costs", "price", "prices", "charge", "charges", "pay",
                   "paying", "spend", "worth", "expensive", "cheap", "cheaper", "shop"))),
           "About £10 to £20 at a bike shop for a puncture: most will fit a new inner tube and "
           "check the tyre for the thorn or glass that caused it for that, and a patch on its own "
           "is often cheaper or free if you bought the tube there. Doing it yourself is £5 to £8 "
           "for a tube, and the levers cost £3 to £5 once. A puncture that keeps coming back is "
           "usually the sharp thing still in the tyre, so ask them to run a finger round the "
           "inside, and a tyre with a cut or a thin patch is worth replacing at £15 to £35.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE + _NOT_A_TYRE_PRICE, bias=2),
    _entry("bike-tyre-price",
           (("tyre", "tyres", "tire", "tires", "inner tube", "inner tubes", "tube",
             "puncture resistant", "new tyre", "new tyres"),
            _bike(("how much", "cost", "costs", "price", "prices", "expensive", "cheap",
                   "cheapest", "budget", "pay", "spend", "worth"))),
           "A bicycle tyre is about £15 to £35 for a decent one and an inner tube £5 to £8, with "
           "a shop fitting them for £10 to £20 on top. Puncture-resistant ones - a Schwalbe "
           "Marathon or a Continental Gatorskin - are £50 to £80 the pair and pay for themselves "
           "in fewer flats. Take the size off the sidewall (700x25c, or 26x1.75) and match the "
           "width to your rim and the riding you do.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE + _NOT_A_TYRE, bias=2),
    _entry("bike-tyre-pressure",
           (("tyre pressure", "tire pressure", "how hard", "how much air", "pump my tyres",
             "pressure",
             "pump up my tyre", "psi", "bar", "tyres hard", "tyre soft", "squashy"),
            _bike(("how", "much", "should", "what", "tyre", "tire", "wheel", "pressure"))),
           "Pump to the range printed on the tyre's sidewall, near the top for a heavier rider or "
           "road riding and near the bottom for wet grass or a light rider. Check them with a "
           "gauge once a week, because a tyre loses a little air all the time and a soft one "
           "gives pinch punctures. If you can squash the tyre against the ground with your "
           "thumb, it needs air.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),

    # --- the chain and the gears -------------------------------------------
    # The battery goes flat in two places: the e-bike's own pack, and a light or a phone charged
    # off it. The tyre entries stand down for the word battery, so without this the line that says
    # a bike battery keeps going flat passed to a phone's Low Power Mode instead.
    _entry("bike-battery",
           (("battery", "batteries", "battery flat", "battery going flat",
             # "charge" on its own is what a shop does to your card, and it pulled this card for
             # "how much does a bike shop charge to fix a puncture": the battery's charge is
             # said as a phrase or as the thing being charged.
             "a charge", "on a charge", "one charge", "per charge", "full charge", "one full charge",
             "holds a charge", "hold a charge", "charge it", "charge them", "charging", "charger",
             "range", "motor", "assist", "power"),
            # "keeps dying" is how people say a pack is worn out, and it was reaching the
            # greeting: "dying" reads as a person's news unless the bike is in the keys.
            _bike(("flat", "going flat", "keeps going", "dies", "dying", "keeps dying", "dead",
                   "wont charge",
                   "not charging", "wont hold", "a charge", "on a charge", "charging",
                   "range", "how far",
                   "lose", "losing", "last", "battery", "motor", "power", "winter", "store",
                   "storage", "care", "look after", "replace",
                   # a pack is the one bike part people ask the price of, and the price is an
                   # order of magnitude off a phone battery's: £35 to £70 was the phone's answer
                   "cost", "price", "how much", "new battery", "replacement"))),
           _bike_battery,
           # the follow-up below shares the word battery, which makes it common in this domain
           # and costs this entry the rarity point that put it ahead of the chemistry card
           ask=_IS_A_BIKE,
           # a shop's "charge" is money and a puncture is a repair: the battery card held the
           # price of mending a tyre because the line had the word charge in it
           avoid=_NOT_A_BIKE + ("puncture", "punctures", "punctured", "flat tyre", "flat tyres",
                                "inner tube", "inner tubes", "tyre repair", "mend a puncture"),
           bias=2),

    # The turn after the bike has been named may leave it out: "how far can an ebike go on a
    # charge" then "and how much is a new battery" was answered with the phone battery price.
    # This entry carries the subject over, and it stands down (an empty reply) when the chat has
    # no two-wheeler in it, so a phone asking what a battery costs keeps the phone card. Its key
    # holds only the words that ask a price, a range or a life: a bare "should i get a new
    # battery" is a phone line, and an entry with nothing to say about a phone must not win it.
    _entry("bike-battery-follow-up",
           (("battery", "batteries", "new battery"),
            ("cost", "price", "how much", "range", "miles", "how far", "last", "how long")),
           _bike_battery_earlier,
           avoid=_NOT_A_BIKE, bias=3),

    _entry("bike-chain-slip",
           (("chain", "chains", "chain slipping", "chain skip", "chain keeps slipping",
             "chain jumps", "chain came off", "chain snapped", "chain broken", "skipping",
             "skips", "jumping"),
            _bike(("slipping", "keeps", "skip", "jump", "gear", "gears", "off", "snapped",
                   "broken", "why", "fix", "replace", "how", "chain"))),
           # "how do i remove rust from my bike chain" is a cleaning job, not a worn chain that
           # skips, and the clean entry's key names rust.
           "A chain that skips under pressure is usually worn, and so is the cassette behind it: "
           "a chain checker that drops in at 0.5 percent on 11-speed (0.75 on older setups) means "
           "replace it now. A single stiff link is the other cause, and it feels like one jolt per "
           "turn of the cranks - free it by flexing it sideways. Change the chain before the "
           "cassette, because a new chain on worn teeth skips worse than the old one did.",
           # "my chain is rusty" and "how do i remove rust from my bike chain" are cleaning
           # jobs, and this entry matches the same two groups, so rust stands it down.
           ask=_IS_A_BIKE,
           avoid=_NOT_A_BIKE + ("rust", "rusty", "rusty links", "seized", "seize"),
           bias=2),

    _entry("bike-chain-clean",
           (("chain", "chains", "chain lube", "lubricant", "squeaky chain", "squeaking",
             "squeak", "noisy chain", "rusty chain", "chain noise",
             # rust is a cleaning job and people say it both ways ("rusty chain", "remove rust")
             "rust", "rusty", "remove rust", "rusty links", "seized chain"),
            _bike(("clean", "cleaning", "clear", "lube", "lubricate", "oil", "squeak",
                   "squeaky", "squeaking", "noise",
                   "noisy", "rust", "rusty", "remove", "get rid", "dry", "how", "often",
                   "should", "chain"))),
           "Wipe the chain with a rag, put one drop of chain lube on each link, turn the cranks a "
           "few times and wipe off what has not gone in. Do it every couple of rides in dry "
           "weather and after any wet one, because a squeak is a dry chain and a dry chain wears "
           "the gears out fast. Skip the general-purpose oil and the spray that is mostly "
           "solvent: it picks up grit and makes a black paste.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),

    _entry("bike-gears",
           (("gears", "gear", "derailleur", "shifting", "shift", "chainring", "cassette",
             "rear mech", "indexing",
             # the hill words are not in this key: "how do i cycle uphill" and "how do i go up
             # hills on a bike" are riding questions, and with a hill word here they tied with
             # the hills row and lost on order, so a person asking how to get up a hill was told
             # to turn a barrel adjuster. The ask keeps them, so a line that names the gears and
             # the hill still reaches this repair.
             ),
            _bike(("not shifting", "won t shift", "wont shift", "jumps", "skips", "slipping",
                   "sticking",
                   # a gear that will not move is the same fault said with the other word:
                   # "my bike is stuck in gear" was standing down to the fault shape and then to
                   # the composer, and the barrel adjuster is what fixes it.
                   "stuck", "jammed", "seized", "stiff", "grinding", "changing",
                   "noisy", "adjust", "fix", "index", "how", "gear", "gears",
                   "wont go into", "won t go into", "lowest", "highest", "bottom gear",
                   "top gear", "uphill", "hill", "hills", "easier"))),
           "Turn the barrel adjuster on the gear cable a quarter turn at a time while pedalling: "
           "one way tightens a shift that is slow to climb the cassette, the other way cures one "
           "that jumps past the gear. If that does nothing, the cable has stretched or seized, or "
           "the hanger the derailleur hangs on is bent - a bent hanger is common after the bike "
           "has fallen over, and a shop straightens it in minutes.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),

    # --- the brakes --------------------------------------------------------
    _entry("bike-brakes-rub",
           (("brakes", "brake", "brakes rubbing", "rubbing", "rubs", "squealing", "squeal",
             "scraping", "grinding", "pads", "caliper", "disc rub"),
            _bike(("rub", "rubbing", "rubs", "squeal", "squealing", "scrape", "scraping",
                   "noise", "noisy", "grinding", "sticking", "drag", "how", "fix", "adjust",
                   "brake", "brakes", "when", "replace", "worn", "worn out", "new", "pads"))),
           "Check the wheel is sitting all the way home in the dropouts and the quick release or "
           "through-axle is shut first, because a wheel half in looks exactly like a rubbing "
           "brake. Then loosen the caliper bolts a touch, squeeze the lever to centre the pads on "
           "the rim or disc, and tighten them again with the lever held. On discs, a pad that "
           "drags after a wheel change usually just needs the pistons pushed back with a tyre "
           "lever.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),

    # A snapped brake cable is a stop-and-replace, not a rubbing pad: the lever comes back to the
    # bar with nothing to pull, and the bike has one brake at best. The line is a fault and a job
    # ("my bike brake cable snapped", "is that hard to do"), and the answer is what to do before
    # riding it again plus the job itself. It sits beside the rubbing row because both are brakes,
    # and the row only answers when a brake cable is named.
    _entry("bike-brake-cable",
           (("brake cable", "brake cables", "brakes cable", "brakes cables",
             "brake cable snapped", "cable snapped", "cable broke", "cable broken"),
            _bike(("snapped", "snap", "broke", "broken", "frayed", "loose", "fix", "replace",
                   "adjust", "hard", "difficult", "easy", "how", "cable", "brake", "brakes",
                   "front", "back", "rear"))),
           "Stop riding it until it is fixed: with one cable gone the other brake is all you "
           "have, and a single brake locks the wheel more easily in the wet. A new inner cable "
           "costs a few pounds and a shop will fit one in minutes. It is not hard to do it "
           "yourself with a new inner cable and an Allen key, about twenty minutes of threading "
           "it through the lever and outer and setting the pads a couple of millimetres off the "
           "rim. Tighten the anchor bolt with the barrel adjuster halfway in, pull the brake "
           "firmly before you ride, and check the outer for kinks and the lever for a frayed end.",
           ask=_IS_A_BIKE,
           avoid=_NOT_A_BIKE + ("rub", "rubs", "rubbing", "squeal", "squeals", "squealing",
                                "squeak", "squeaks", "squeaking", "grind", "grinds", "grinding",
                                "pad", "pads", "disc", "discs", "rotor", "rotors", "drag",
                                "drags", "dragging"),
           bias=3),

    # --- the helmet --------------------------------------------------------
    _entry("bike-helmet",
           (("helmet", "helmets", "bike helmet", "cycle helmet", "crash helmet"),
            _bike(("replace", "replacement", "when", "how often", "old", "dropped", "fell",
                   "crashed", "smash", "cracked", "fit", "fits", "size", "buy", "new",
                   "helmet"))),
           "Replace a helmet after any knock that put it between you and the ground, even with no "
           "crack you can see: the foam that absorbs the hit has already done its job once. With "
           "no crash, about five years is the usual advice, because sweat and sun harden the foam "
           "and the straps. It should sit level, two fingers above the eyebrows, with the strap "
           "snug enough that you can open your mouth wide and feel it pull down.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),

    # The decision, not the replacement: "should i wear a helmet" is a line people send, and the
    # replacement entry answered it with "replace a helmet after any knock", which answers a
    # question they had not asked.
    _entry("bike-helmet-wear",
           (("helmet", "helmets", "bike helmet", "cycle helmet"),
            _bike(("should i wear", "do i need", "worth it", "wear one", "need one",
                   "is it worth", "law", "legal", "why bother", "bother"))),
           "Wear one: it is not the law for adults in the UK, but a helmet is the difference "
           "between a bruise and a head injury in the one fall nobody plans for. It does not make "
           "you safe from traffic, so ride as if it were not there: take the lane at junctions and "
           "never go up the left side of a lorry. It should sit level, two fingers above the "
           "eyebrows, with the strap snug enough that you feel it when you open your mouth wide.",
           ask=_IS_A_BIKE,
           # "when should i replace my bike helmet" carries "should i" as well, and that is the
           # replacement entry's question
           avoid=_NOT_A_BIKE + ("replace", "replacement", "old", "cracked", "crashed", "dropped",
                                "smash", "fit", "fits", "size", "when"),
           bias=2),

    # Carrying a child on a bike is a seat that clamps to the frame or a trailer behind it, which
    # is a different question from how big a child's bike should be. Both are here before the
    # sizing row, because "seat" and "bike" are words in that row's key: "child seat for a bike",
    # "is a bike seat safe for a toddler" and "can a child go on the back of my bike" all came
    # back with "Go by the child's inside leg".
    _entry("bike-carry-a-child",
           (_CARRYING,
            _bike(("child", "childs", "child's", "children", "kid", "kids", "son", "daughter",
                   "toddler", "baby", "boy", "girl", "year old", "carrier", "trailer",
                   "on the back", "back of my bike"))),
           "A seat for carrying a child clamps to the frame, not to the seatpost, and it holds "
           "them until about 22kg: 20kg to 22kg is the usual limit, so check the seat's rating "
           "against your child's weight rather than their age. From about nine months, once they "
           "can sit up by themselves, a rear seat is the usual choice: it needs a harness, "
           "footwells and a helmet even for a short trip, a high-back seat gives the head some "
           "support, and it is the frame tubes the brackets bolt to. Never fit one to a bike with "
           "a carbon frame or a rear suspension, and take the child off before you fold or park "
           "the bike. Two children, or one under nine months, want a trailer instead: it sits "
           "behind and low, with a flag and lights on the back.",
           ask=_IS_A_BIKE,
           avoid=_NOT_A_BIKE + ("car seat", "car", "booster", "isofix", "front seat",
                                "child seat for a car"),
           bias=3),

    # A child's bike is set by inside leg, not by the adult heel-on-the-pedal rule: a child stops
    # by putting a foot down, so both feet have to reach the ground.
    _entry("bike-child-seat",
           (("saddle", "seat", "seatpost", "seat height", "bike", "bike size", "bike too big",
             "bike too small", "stabilisers", "balance bike"),
            _bike(("child", "childs", "child's", "kid", "kids", "son", "daughter", "toddler",
                   "boy", "girl", "year old",
                   # not bare "learn to ride": "how do i learn to ride a bike" is the adult
                   # asking how, and this row answered it with how to size a child's saddle.
                   # A parent's line always names the child, and "learning to ride" still
                   # catches the ones that do not.
                   "learning to ride"))),
           "Go by the child's inside leg, not their age: stand them against a wall in shoes and "
           "measure from the floor to the crotch, and the saddle should go low enough that both "
           "feet are flat on the ground when they sit on it, with their hands on the brake levers. "
           "That is different from an adult's bike, where the leg almost straightens on the pedal. "
           "A bike whose saddle will not go low enough is too big, whatever the wheel size says.",
           ask=_IS_A_BIKE,
           # The adult asking how to learn is not buying a child's saddle: "how do i learn to
           # ride a bike" was answered with the inside-leg measurement. A parent's line names
           # the child, so these phrases only catch the learner.
           # "teach" is the parent's word for the lesson, and it was still going to the
           # inside-leg measurement: "how do i teach my kid to ride a bike" and "how do i teach
           # my child to ride a bike without stabilisers" are the teaching answer's lines.
           # The seat a child sits on is not the saddle they sit on: these lines want the row
           # above, and inside leg is the wrong answer to every one of them.
           avoid=_NOT_A_BIKE + _CARRYING + ("how do i learn to ride", "how to learn to ride",
                                "how do you learn to ride", "i want to learn to ride",
                                "im learning to ride", "i'm learning to ride",
                                "adult learning to ride", "teach", "teaches", "teaching",
                                "taught", "learn", "learning", "learnt", "without stabilisers",
                                # teaching is not sizing, whoever is learning: how to teach
                                # belongs to the `learn-to-ride` row
                                "learn to ride", "learning to ride", "learns to ride")
                                # A child who came off the bike is not a sizing question: "my son
                                # fell off his bike but hes ok" and "my son fell off his bike and
                                # hurt his arm" both came back with inside-leg measurement. The
                                # words of the fall are in the line, and they are another row's
                                # question.
                                + _A_HURT_PART,
           bias=2),

    # --- leaving it somewhere ---------------------------------------------
    _entry("bike-lock",
           (("lock", "locking", "locked", "lock it", "d lock", "u lock", "chain lock",
             "bike stolen", "bikes stolen", "stolen bike", "stolen", "stole", "stolen it",
             "steal", "stealing",
             "theft", "thief", "thieves",
             # the lock itself, which people describe rather than name
             "lock cut", "cut lock", "got cut", "snipped", "angle grinder", "lock broken"),
            _bike(("best way", "how", "where", "safe", "secure", "stolen", "stole", "stolen my",
                   "being stolen", "get stolen", "theft", "thief", "thieves", "which", "should",
                   "lock",
                   # a theft in the words people use for it: "someone stole my bike" names the
                   # act once, and a word in both groups only counts once
                   "someone", "somebody", "gone", "last night", "was stolen", "got stolen"))),
           "Lock the frame and one wheel to something fixed in the ground with a D-lock, and take "
           "the front wheel or its quick release with you if it is not also locked. Keep the lock "
           "off the ground and the bike where people pass, since an angle grinder and a quiet "
           "street is how most bikes go. Register the frame number and photograph the bike; it is "
           "what gets it back.",
           ask=_IS_A_BIKE,
           # A bike that has already gone is not a locking question: "my bike was stolen" got
           # this row's "lock the frame and one wheel...", which tells a person who has lost a
           # bike how to keep one. The past theft has its own answer (`lifeadmin`,
           # `a-thing-was-stolen`), and every phrase here is the act already done - "how do i stop
           # my bike getting stolen" is not one of them and keeps this row.
           avoid=_NOT_A_BIKE + ("was stolen", "got stolen", "been stolen", "is stolen",
                                "stolen last night", "stolen yesterday", "stolen from",
                                "someone stole", "someone took", "someone nicked",
                                "theives took", "thieves took", "nicked my", "pinched my",
                                "went missing", "gone missing", "got nicked", "got pinched",
                                "was taken", "worth claiming", "claim on insurance",
                                # naming it as the thing that was stolen, or asking to report it,
                                # is the theft question too - "how do i register my bike as
                                # stolen" was told to lock the frame and one wheel
                                "as stolen", "report my bike", "report it stolen"),
           bias=2),
    # --- the noises that are not the chain --------------------------------
    _entry("bike-clicking",
           (("click", "clicking", "clicks", "creak", "creaking", "creek", "knock", "knocking",
             "tick", "ticking", "rattle", "rattling", "noise", "noisy"),
            _bike(("pedal", "pedals", "pedalling", "when i pedal", "every pedal", "under load",
                   "downstroke", "bottom bracket", "crank", "chainring", "seatpost", "saddle",
                   "headset", "why", "what", "how", "fix", "stop",
                   "making", "makes", "started", "suddenly", "lately", "now"))),
           "Chase it in the order of cheapness: the chainring bolts, the pedal threads (a drop of "
           "grease and a tighten), the seatpost and saddle clamp, then the crank bolts. A click "
           "once per pedal stroke that only happens when you push hard is usually the bottom "
           "bracket, and one that comes when you are out of the saddle is the headset or the "
           "stem bolts. A loose crank or headset wears the frame, so find it this month.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),

    # --- the fit that makes a ride hurt -----------------------------------
    _entry("bike-setup",
           (("saddle", "seat", "seatpost", "seat height", "handlebars", "handlebar", "reach",
             "drop bars", "flat bars", "riser bars", "bar ends", "aerobars", "bars",
             "stem", "bike fit", "position",
             # the weight of a bad position lands on the hands, the neck and the back
             "hands go numb", "hands numb", "numb hands", "fingers go numb", "sore hands",
             "sore wrists", "aching back", "bad back", "sore neck", "aching neck"),
            _bike(("too low", "too high", "height", "hurts", "hurt", "knee", "knees", "back",
                   "neck", "wrist", "wrists", "hands", "numb", "numbness", "sore", "soreness",
                   "ache", "aches", "aching", "pain", "painful", "uncomfortable", "comfortable",
                   "position", "adjust", "how", "should", "right",
                   # "drop bars on a hybrid bike" and "flat bars or riser bars on a hybrid" named
                   # only the bars and the kind of bike, and the row needs two of its own words:
                   # the bar words say which part, so they are keys of this row as well as the
                   # saddle's. The bicycle itself is still the `ask`, so a boiler's "1.5 bar" and
                   # a "pair of bars" cannot reach here.
                   "bars", "bar", "handlebar", "handlebars", "drop bars", "flat bars",
                   "riser bars", "bullhorn bars", "bar ends", "aerobars", "stem", "reach",
                   "tops", "hoods", "hybrid", "gravel", "commuter", "tourer",
                   # reach has its own words, and "my handlebars are too far away" said the bar
                   # twice and nothing else, so the row never scored
                   "far", "too far", "further", "close", "too close", "long", "short",
                   "stretched out", "reaching"))),
           _bike_fit,
           ask=_IS_A_BIKE,
           avoid=_NOT_A_BIKE + ("child", "childs", "child's", "kid", "kids", "son", "daughter",
                                "toddler", "year old", "nursery", "school",
                                # "the saddle area" is the patch of skin between the legs, which
                                # is a red flag with a bad back, not a bike fit; a real bike line
                                # says saddle height, saddle sore, my saddle, saddle too high
                                "saddle area", "saddle region",
                                # a numb saddle is the skin, not the seat: "my saddle feels numb"
                                # and "numbness in my saddle" were both given the bike fit, and
                                # the saddle-numbness answer (bot/knowledge/body.py) is the one
                                # that says when it is the same-day question
                                "numbness in my saddle", "numbness in the saddle",
                                "saddle feels numb", "saddle is numb", "saddle went numb",
                                "numb saddle", "saddle numbness", "numbness of the saddle"),
           bias=2),

    # --- the shop, and what it does ---------------------------------------
    _entry("bike-service",
           (_BIKE_SERVICE_SAID, _bike(_BIKE_SERVICE_PRICE_SAID)),
           BIKE_SERVICE,
           ask=_IS_A_BIKE,
           # "how should i lock my bike outside the shops" is the lock, not the service, and the
           # bare "shop" in the key was enough to take it
           avoid=_NOT_A_BIKE + _BIKE_SERVICE_AVOID,
           bias=2),
    _entry("bike-service-when",
           (_BIKE_SERVICE_SAID, _bike(_BIKE_SERVICE_WHEN_SAID)),
           BIKE_SERVICE_WHEN,
           ask=_IS_A_BIKE,
           avoid=_NOT_A_BIKE + _BIKE_SERVICE_AVOID,
           bias=_BIKE_SERVICE_WHEN_BIAS),

    # --- the ride as exercise ---------------------------------------------
    _entry("bike-exercise",
           (("exercise", "calories", "calorie", "fitness", "fit", "cardio", "weight",
             "good for me", "worth it", "aerobic", "training"),
            _bike(("cycling", "cycle", "bike", "biking", "bicycle", "how much", "how many",
                   "good", "is", "burn", "burning", "lose", "losing", "benefit", "benefits",
                   "healthy", "heart"))),
           "Yes: an easy hour on a bike burns roughly 300 to 400 calories and counts as the "
           "moderate activity the 150-minutes-a-week advice means, and the bike carries your "
           "weight so it is easier on the knees than running. A commute of twenty minutes each "
           "way gets you to the weekly target on its own. Push a little harder on two rides a "
           "week if you want fitness rather than just movement, and eat normally rather than "
           "eating back every calorie the ride burned.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),
    # --- buying one, and the rules that decide what one is -----------------
    _entry("ebike-worth-it",
           (_IS_AN_EBIKE,
            ("worth", "worth it", "worth the money", "worth buying", "should i", "buy",
             "buying", "get one", "cheaper", "cost", "costs", "run", "running", "commute",
             "commuting", "to work", "instead of the car", "instead of a car", "than a car",
             "instead of driving", "normal bike", "or a bike", "vs a bike", "convert",
             "conversion", "kit", "second hand", "secondhand", "sweat", "sweaty", "shower",
             "hills", "hilly", "any good", "good idea", "if i use one",
             # "would you recommend an electric bike" is the same buying question, and the
             # verb is the ask, so the row still needs the bike from its own key.
             "recommend", "recommended", "recommendation", "recommendations",
             # the same buy question as a doubt: "any point in an ebike", "is an ebike a waste
             # of money", both of which were the shrug beside the answer in this row.
             "any point in", "waste of money", "wasting money", "money well spent",
             "bother with", "bother")),
           "Worth it if the alternative is driving: a pedal-assist bike flattens the hills and the "
           "headwind, so a commute you would skip on a bad day still happens, for a few pence of "
           "electricity a charge and no tax or parking. It saves little against a bus pass and "
           "keeps you less fit unless you turn the assist down. Spend on the battery and brakes: "
           "£1,200 to £2,000 in a shop with a two-year warranty beats a £500 one plus a kit.",
           ask=_IS_AN_EBIKE,
           # "is an ebike as good exercise as a normal bike" is the fitness question, not the
           # buying one: the words that ask about effort belong to ebike-exercise below.
           avoid=_NOT_AN_EBIKE + ("exercise", "fitness", "calories", "cheating", "cheat",
                                  "effort", "healthy", "health", "get fit", "keep fit",
                                  "lose weight", "weight loss"),
           bias=3),
    _entry("ebike-rules",
           (_IS_AN_EBIKE,
            ("licence", "license", "legal", "illegal", "law", "insurance", "insured", "tax",
             "train", "trains", "tube", "bus", "path", "cycle path", "pavement", "road",
             "helmet", "fast", "speed", "mph", "throttle", "age", "old", "child",
             "children", "kid", "allowed", "need", "register", "number plate")),
           "In the UK a pedal-assist e-bike up to 250W and 15.5mph is legally an ordinary "
           "bicycle: no licence, no tax, no compulsory insurance, and cycle paths and towpaths are "
           "open to it. A throttle that pulls you without pedalling, or assist past 15.5mph, makes "
           "it a moped, and then the licence, insurance, helmet and number plate do apply. Trains, "
           "ferries and bike racks usually take them but the operator sets the rule, and several "
           "ban them at peak times.",
           # Nothing is compulsory for a pedal-assist e-bike, so a line that asks about insurance
           # belongs to the cover answer below, not to the licence-and-speed one.
           ask=_IS_AN_EBIKE,
           avoid=_NOT_AN_EBIKE + ("insurance", "insured", "insure", "cover", "covered",
                                  "policy", "theft", "stolen"),
           bias=4),
    _entry("ebike-exercise",
           (_IS_AN_EBIKE,
            ("cheating", "cheat", "cheater", "exercise", "fitness", "fit", "workout", "lazy",
             "still exercise", "good for me", "calories", "burn", "effort", "healthy", "health")),
           "No - it is still exercise, just less of it: an hour on an e-bike is roughly half to "
           "two-thirds the effort of the same hour on a normal bike, and because it is easier you "
           "ride further and more often, so the weekly total usually goes up rather than down. "
           "Turn the assist down or off on the flat and you get most of the workout back; leave it "
           "on full and it is a gentle ride, which is a great deal better than the car.",
           ask=_IS_AN_EBIKE, avoid=_NOT_AN_EBIKE, bias=4),
    _entry("ebike-charge-cost",
           (_IS_AN_EBIKE,
            # a shop "charge" is money, so the battery's charge is a phrase here too
            ("a charge", "on a charge", "one charge", "full charge", "charge it", "charging",
             "charger", "electricity", "per charge", "cost to charge",
             "how much electricity", "power", "a year", "annual", "leccy")),
           "About 10p a full charge, so a year of commuting is £15 to £25: a 500Wh battery is "
           "half a unit of electricity, and a unit is around 25p, which is why the electricity "
           "never shows up next to fuel. A 40-mile commute five days a week is roughly 100 charges "
           "a year - call it £10 to £20 - and the battery is the cost that matters, not the plug.",
           ask=_IS_AN_EBIKE,
           # the price of the pack, its range and its life are the battery entries' answers, and a
           # charger that has stopped is a fault, not a running cost
           avoid=_NOT_AN_EBIKE + ("battery", "batteries", "pack", "replace", "replacement",
                                  "range", "how far", "life", "last", "lasts",
                                  "broken", "not working", "stopped working", "wont", "won't",
                                  "fault", "faulty", "dead", "flashing", "red light"),
           bias=4),
    _entry("ebike-price",
           (_IS_AN_EBIKE,
            ("cost", "costs", "price", "how much", "how much is", "how much are", "cheap",
             "cheapest", "budget", "spend", "afford", "expensive", "second hand", "secondhand")),
           "£1,200 to £2,000 buys a dependable new one and £2,500 and up buys a lighter motor and "
           "a bigger battery, with decent second-hand starting around £600 to £900. What the money "
           "pays for is the battery and the motor: a 400Wh or bigger pack and a mid-drive motor are "
           "what separate a £2,000 bike from a £1,000 one, and a hub motor with a small pack is the "
           "one to avoid on hills. Add £50 to £100 for a lock that takes more than a minute to cut.",
           ask=_IS_AN_EBIKE,
           avoid=_NOT_AN_EBIKE + ("charge", "charging", "charger", "electricity", "battery",
                                  "batteries", "pack", "replace", "replacement", "range"),
           bias=4),
    _entry("ebike-charge-time",
           (_IS_AN_EBIKE,
            ("how long to charge", "how long does it take to charge", "takes to charge",
             "how long does charging take", "charge time", "charging time",
             "how long to charge it", "hours to charge", "overnight", "charge overnight")),
           "Three to six hours from empty on the charger that came with the bike, so most people "
           "charge it overnight or over an evening: a 400 to 500Wh pack on a 2A charger puts in "
           "about 100 to 120Wh an hour, and the four-amp fast chargers halve that. You do not have "
           "to run it flat - a charge from half is quicker and easier on the pack - and a pack that "
           "will not take a charge in the cold should be brought indoors for an hour first.",
           ask=_IS_AN_EBIKE,
           avoid=_NOT_AN_EBIKE + ("cost", "price", "how much", "money", "electricity bill",
                                  "a year", "battery", "batteries", "pack", "range", "last"),
           bias=4),
    _entry("ebike-conversion",
           (("convert", "converting", "conversion", "to electric", "electric kit", "motor kit",
             "kit", "front hub", "rear hub", "mid drive", "mid-drive", "friction drive",
             "add a motor", "go electric"),
            _bike(("bike", "bicycle", "cycle", "cycling", "worth", "should i", "buy", "cost",
                   "price", "cheaper", "better", "myself"))),
           "Usually cheaper to buy a whole e-bike than to convert one well: a mid-drive kit with "
           "a battery is £600 to £900, most of the price of a ready-made bike, and the £250 "
           "front-hub kits are heavy, lurch at the front wheel and load the fork. Convert only a "
           "bike you already like, with disc brakes and a steel or solid fork. It must stay a "
           "pedal-assist bicycle - 250W, assist stopping at 15.5mph - or it becomes a moped.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),
    _entry("bike-insurance",
           (("insurance", "insured", "cover", "covered", "contents insurance", "policy",
             "theft cover", "protect"),
            _bike(("bike", "bicycle", "cycle", "cycling", "ebike", "e-bike", "it", "worth",
                   "should i", "need", "get", "do i"))),
           "Nothing is compulsory on a pedal-assist bike, so insure it for theft, not for the law: "
           "home contents insurance usually covers it at home and often away from home too, so "
           "start there and check the single-item limit, because a £1,500 bike is over the typical "
           "£1,000 cap and has to be named. A bike policy is £5 to £15 a month and wants a Sold "
           "Secure lock. Write down the frame number and photograph the bike.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=3),
    _entry("folding-bike-worth-it",
           (("folding bike", "folding bikes", "folding bicycle", "folder", "fold up",
             "folds up", "folding", "brompton", "small wheel", "small wheels",
             "compact bike", "bike that folds"),
            ("worth", "worth it", "worth the money", "should i", "buy", "buying", "get one",
             "good", "any good", "better", "commute", "train", "tubes", "how much", "cost",
             "price", "cheaper", "for the train")),
           "Worth it when the train or the office is the problem: a folder goes on a commuter "
           "train or under a desk where a full-size bike is not allowed, and most fold in about "
           "fifteen seconds. The small wheels make it slower and twitchier in traffic, so it "
           "suits a couple of miles at each end, not ten, and the ones worth buying start around "
           "£500 to £900. Measure the folded size and weight against your train's rules, and fold "
           "it yourself in the shop first.",
           avoid=("folding table", "folding chair", "folding bed", "folding screen", "ironing",
                  "deckchair", "deck chair", "camping chair", "sofa", "laundry"),
           bias=3),
    # --- starting out, and the road itself ---------------------------------
    # "i want to start cycling" and "how do i start cycling to work" were the menstrual-cycle
    # entry: `cycle` is a word the period row owns, and a wanting line skips its ask gate. The
    # bicycle is in these lines, so the bicycle has to be the thing that answers them.
    # What a bike costs is a different question from what is wrong with one: a budget of £400 and
    # "is that enough" reached the used-bike check, which tells a person what to look at, not what
    # to spend, and eight other ways of asking got "I can't look up live prices".
    _entry("bike-price",
           (_IS_A_BIKE,
            ("how much", "cost", "costs", "price", "prices", "spend", "budget", "afford",
             "affordable", "cheap", "cheapest", "decent", "good bike", "enough", "worth",
             "new or used", "new or second hand", "second hand", "secondhand", "used",
             "what does a bike cost", "how much should i spend", "what bike", "which bike",
             "what bike should i", "which bike should i", "recommend a bike", "any good",
             "good value", "value", "£", "for 200",
             "for 300", "for 400", "for 500", "for 600", "for 800", "for 1000")),
           "£400 to £700 buys a dependable new commuter or hybrid from a bike shop, and £150 to "
           "£300 buys a sound second-hand one - a rigid 1990s mountain bike or hybrid with slick "
           "tyres is the best value at the bottom, and about £500 buys nearly new. A new bike "
           "under roughly £250 is the one to avoid: the frame, the gears and the wheels are what "
           "the money went without. Then add £40 to £80 for a lock, £20 for lights and £30 to "
           "£50 for a helmet.",
           ask=_IS_A_BIKE,
           # what to look at on a used one, and what a service costs, are the two rows beside
           # this one: "what should i check on a second hand bike" and "how much does a bike
           # service cost" both reached the price answer while the check and service cards sat
           # there, which is the fault this table exists to avoid.
           avoid=_NOT_A_BIKE + ("electric", "e-bike", "ebike", "motor", "battery", "folding",
                                "brompton", "rent", "hire", "insurance", "insure", "train",
                                "parking", "puncture", "brakes", "gears", "chain", "tyre",
                                "tyres", "saddle", "sizing", "size",
                                # the parts people price one at a time, which have rows of
                                # their own: "how much is a new inner tube" was a new bike
                                "inner tube", "inner tubes", "new tube", "a tube",
                                # a bike that has broken is the rights question, not the price
                                # one: second-hand-private says buyer beware, or the dealer's
                                # 30 days, and a price guide is no answer to a fault you have
                                "broke", "broken", "snapped", "fell apart", "fell off",
                                "stopped working", "doesnt work", "wont work", "faulty",
                                "went wrong", "packed in", "not as described", "refund",
                                "check", "checking", "look at", "look for", "inspect",
                                "condition", "before buying", "before i buy", "before you buy",
                                "what to look", "service", "servicing", "tune up",
                                "convert", "converting", "conversion", "kit",
                                "kid", "kids", "child", "childs", "children", "son",
                                "daughter", "toddler", "year old",
                                # a part and an accessory have their own prices, and £400 to
                                # £700 for a whole bike is no answer to "how much is a bike
                                # frame" - the same for a fit, a box, a rack and a light
                                "frame", "frames", "bike light", "bike lights", "rack", "box",
                                "bike fit", "fitting", "cargo", "helmet",
                                "bike lock", "bike locks",
                                "cycle to work", "salary sacrifice", "tax"),
           bias=3),
    _entry("bike-start",
           (("start cycling", "starting cycling", "begin cycling", "get into cycling",
             "getting into cycling", "take up cycling", "cycling to work", "cycle to work",
             "commute by bike", "commuting by bike", "commute by bicycle", "bike to work",
             "cycling commute", "start biking", "start riding", "get back into cycling",
             "back into cycling", "new to cycling", "cycling beginner", "beginner cyclist",
             # not bare "learn to cycle": learning to ride at all is `learn-to-ride` in
             # shopping.py, and this row's reply is about riding to work ("leave a lock, a spare
             # tube and a pair of shoes at work"), so "i want to learn to cycle" was told how to
             # commute before the person could ride. Road riding keeps its own phrase.
             "learn to ride on the road", "learn to cycle on the road"),
            _bike(("how", "want", "wanted", "wanting", "thinking", "considering", "start",
                   "starting", "begin", "get", "getting", "take", "back", "again", "commute",
                   "commuting", "work", "beginner", "new", "should", "advice", "tips",
                   "easier", "confident"))),
           "Pick a route you already know on quiet streets, ride it once at a weekend so the "
           "turns are not a surprise, and start with two days a week rather than five. Leave a "
           "lock, a spare tube and a pair of shoes at work, so there is nothing to carry and "
           "nothing to forget. The first fortnight is the hard part and after that the ride is "
           "the easy part of the day. A waterproof and a rear light is all the kit you need.",
           ask=_IS_A_BIKE,
           # the kit list and the money are two rows below: "what accessories do i need for
           # commuting by bike" was this row answering with the route tip, and "how much can i
           # save with cycle to work" was too, instead of the scheme
           avoid=_NOT_A_BIKE + ("accessories", "accessory", "kit", "gear", "lights", "light",
                                "pannier", "waterproof", "what do i need", "save", "saving",
                                "savings", "scheme", "salary sacrifice", "through work",
                                "employer", "tax", "how much"),
           bias=2),

    # Pumping a tyre up is not mending a puncture, and it is the first thing a new rider does
    # wrong: a Presta valve has to be unscrewed and tapped before a pump will grip it.
    _entry("bike-pump",
           (("pump", "pumping", "pump up", "pumped", "inflate", "presta", "schrader", "valve",
             "valves", "track pump", "floor pump", "foot pump", "hand pump", "co2", "gauge"),
            _bike(("how", "up", "tyre", "tyres", "tire", "tires", "tube", "which", "what",
                   "pressure", "hard", "soft", "should", "much", "air", "not", "wont"))),
           "Know which valve you have: a Presta valve is the thin one and its little nut has to "
           "be unscrewed and tapped to let air in, while a Schrader is the car-type one a pump "
           "just pushes onto. Pump to the range printed on the sidewall and use a track pump with "
           "a gauge at home, because no thumb can feel 60psi. Top up about once a week: a tyre "
           "loses a little air all the time, and a soft one pinches flat on a kerb.",
           ask=_IS_A_BIKE,
           # "my bike wheel wont stay pumped up" is the hole, not the pump
           avoid=_NOT_A_BIKE + ("keeps going flat", "keeps going down", "losing air", "puncture",
                                "slow puncture", "again", "every week", "every day"),
           bias=2),

    # The hill, rather than the gears being broken: main answered "how do i ride uphill easier"
    # with the barrel-adjuster card, which is a repair for a skipping chain.
    _entry("bike-hills",
           (("hill", "hills", "uphill", "climb", "climbing", "climbs", "big hill", "steep",
             "steep hill", "hilly", "headwind",
             # the phrase, so the row beats the gear-cable repair on a line that names both:
             # "how do i ride a bike uphill easier" tied with bike-gears and lost on order
             "uphill easier", "hills easier", "ride uphill", "up hills", "up the hill",
             "climbing hills", "easier on hills"),
            # the bicycle itself sits in the second group as well as in the ask gate, so a line
            # that names the bike and the hill but neither of them twice ("climbing hills on a
            # bike") still has two words to score with
            _bike(("easier", "how", "ride", "riding", "cycle", "cycling", "get up", "hard",
                   "harder", "struggle", "struggling", "tired", "legs", "out of breath",
                   "breathless", "gear", "gears", "walk", "bike", "bikes", "bicycle",
                   "hills", "uphill", "on a bike"))),
           "Change down before the hill rather than on it, into a gear you can turn at about 70 "
           "to 80 turns of the pedals a minute: that keeps you seated, and standing up costs more "
           "energy than it looks. Sit up with your hands on the tops of the bars so your chest "
           "stays open, and breathe in time with the pedal strokes. If the easiest gear is still "
           "too hard, a cassette with a bigger bottom sprocket is the real fix.",
           # "how do i ride uphill easier" names no bicycle at all, and riding uphill is
           # something only a bicycle and a horse do, so the phrase is the gate rather than the
           # word `hill`: "why is running uphill harder" is a running line and keeps its card.
           ask=_IS_A_BIKE + ("ride uphill", "riding uphill", "rides uphill", "cycle uphill",
                             "climbing hills", "climb hills", "ride up the hill"),
           avoid=_NOT_A_BIKE + ("running", "run ", "walker", "walkers", "hiking", "hiker",
                                "treadmill", "on foot"),
           bias=2),

    # Lights: the law, and the daylight case for them.
    _entry("bike-lights",
           (("light", "lights", "lamps", "lamp", "headlight", "rear light", "front light",
             "be seen", "reflective", "reflector", "reflectors", "hi viz", "hiviz",
             "fluorescent", "dark", "darker", "night", "nighttime", "dusk", "twilight"),
            _bike(("need", "needed", "law", "legal", "illegal", "against the law", "required",
                   "require", "must", "should",
                   "day", "daylight", "night", "dark", "winter", "see", "seen", "visib",
                   "bright", "how", "what", "which", "worth"))),
           "Lights are the law between sunset and sunrise, and worth using in daylight as well: a "
           "flashing rear light is what makes a driver look twice in rain or at dusk. Use a "
           "steady front light bright enough to see the road by - 400 lumens is plenty in town - "
           "and a rear light at saddle height, not on your bag where a coat covers it. Charge "
           "them weekly; the light that dies halfway home is the one nobody sees.",
           ask=_IS_A_BIKE,
           # a bike light that has stopped working is the battery entry's or the bulb's
           avoid=_NOT_A_BIKE + ("not working", "stopped working", "battery", "batteries", "bulb",
                                "flicker", "flickering", "dynamo", "wiring"),
           bias=2),

    # A bicycle light that has stopped working is not a ceiling rose: main answered "my bike
    # light has stopped working" with "turn the lighting circuit off at the consumer unit", and
    # the lights entry above steps down for exactly these lines.
    _entry("bike-light-fault",
           (("light", "lights", "lamp", "lamps", "headlight", "dynamo", "hub dynamo",
             "battery light", "usb light",
             # the phrases, so the row beats the room-light card it ties with on rank and
             # loses to on file order: "my bike light has stopped working" was the consumer unit
             "bike light", "bike lights", "cycle light", "cycle lights", "rear light",
             "rear lights", "front light", "front lights", "lights dont work",
             "light doesnt work", "light not working", "lights not working",
             "light wont work", "lights wont work"),
            _bike(("not working", "stopped working", "wont work", "doesnt work", "not come on",
                   "wont come on", "not turning on", "wont turn on", "dead", "dim", "flicker",
                   "flickering", "blown", "faulty", "broken", "stop", "stopped", "charg",
                   "batter", "bulb", "why", "dont work", "not work", "working"))),
           "Work through it in this order: the battery or the charge, the switch, then the wire "
           "at the lamp. A rear light that flickers over bumps is a tired battery or a loose "
           "contact in the clip, and a dynamo light that dies at low speed is normal until the "
           "standlight takes over. In winter a USB light that will not charge is usually a cold "
           "battery - bring it in and let it warm up - so keep a spare set charged.",
           ask=_IS_A_BIKE,
           # a room light, a car light and a phone torch all say "light" too
           avoid=_NOT_A_BIKE + ("ceiling", "kitchen", "bathroom", "hallway", "landing", "lamp post",
                                "street", "torch", "phone torch", "headlights", "indicator",
                                "brake light", "reversing light"),
           bias=2),

    # The road, rather than the bike: "how do i get confident cycling on roads" was a shrug and
    # "how do i cycle in traffic" was the journey planner's live-times card.
    _entry("bike-confidence",
           (("roads", "the road", "traffic", "busy road", "busy roads", "lorries", "lorry",
             "cars passing", "close pass", "cycle lane", "cycle path", "junction", "junctions",
             "roundabout", "roundabouts", "nervous", "scared", "frightened", "confident",
             "confidence", "safe cycling", "road position", "door"),
            _bike(("cycling", "cycle", "bike", "biking", "bicycle", "how", "get", "getting",
                   "feel", "feels", "scared", "nervous", "afraid", "worried", "confident",
                   "confidence", "safe", "safer", "ride", "riding", "start", "school", "work"))),
           "Confidence comes from the route, not the traffic: ride the quiet-street version at a "
           "weekend, then take it on a weekday at a quieter hour, and repeat until the turns are "
           "automatic. Ride a door's width out from parked cars, take the middle of the lane at "
           "junctions so nobody squeezes past, and look back before you move over. Never go up "
           "the inside of a lorry or a bus: that is where the serious crashes happen.",
           ask=_IS_A_BIKE, avoid=_NOT_A_BIKE, bias=2),

    # A money question about a bicycle, which the money rows cannot answer without the scheme.
    _entry("cycle-to-work",
           # "can i get a bike through work" and "my employer does a bike scheme" named no
           # scheme word, and the row is main's own: the phrasings go on it rather than a second
           # row with the same id
           (("cycle to work scheme", "cycle to work", "bike scheme", "bike to work scheme",
             "salary sacrifice bike", "salary sacrifice scheme", "employer scheme",
             "bike through work", "bicycle through work", "through work", "through my employer",
             "bike to work", "work scheme"),
            _bike(("what", "how", "does", "work", "works", "worth", "worth it", "get", "apply",
                   "cost", "save", "saving", "eligible", "limit", "£1000", "1000"))),
           "The Cycle to Work scheme lets your employer buy a bike and safety kit - usually up to "
           "£1,000, and some employers set a higher limit - and take the cost out of your pay "
           "before tax, so a £1,000 bike costs a basic-rate taxpayer around £680. You pay it over "
           "12 months as a hire fee, then either hand the bike back, pay a small final payment or "
           "keep it by extending the hire. Ask HR whether your employer is signed up.",
           ask=_IS_A_BIKE,
           # the scheme is about money; "what kit do i need to cycle to work" is the kit list
           avoid=_NOT_A_BIKE + ("kit", "gear", "equipment", "accessories", "essentials", "spares",
                                "what do i need"),
           bias=2),

    # "is cycling bad for knees" was a shrug on main, and the answer is the saddle again.
    _entry("cycling-knees",
           (("knee", "knees", "kneecap", "knee joint", "knees hurt", "sore knees"),
            _bike(("cycling", "cycle", "bike", "biking", "bicycle", "bad", "good", "worse",
                   "better", "harm", "damage", "hurt", "pain", "safe", "is", "are"))),
           "Cycling is one of the kinder things for knees: it puts no weight through the joint and "
           "builds the muscle that holds it, and most cycling knee pain is a saddle set too low or "
           "a gear too big rather than wear. Raise the saddle until your leg just straightens with "
           "your heel on the pedal, spin an easier gear, and ease off while a knee is hot or "
           "swollen. Pain at the front is usually the saddle; at the back, too high.",
           ask=_IS_A_BIKE,
           # "my knees hurt when i cycle" is the fit card, which names the saddle and the bars
           avoid=_NOT_A_BIKE + ("saddle", "handlebars", "handlebar", "numb", "tingling",
                                "replacement", "operation", "arthritis", "raynaud"),
           bias=2),



    _entry("bike-what-to-wear",
           (("what to wear", "what should i wear", "wear on a bike", "wear cycling",
             "cycling clothes", "bike clothes", "what do i wear"),
            _bike(("cycling", "cycle", "bike", "bicycle", "to work", "commute", "winter",
                   "summer", "hot", "rain", "raining", "cold", "weather", "how", "what",
                   "should"))),
           _bike_wear,
           ask=_IS_A_BIKE,
           # the helmet is its own row, and the kit question is the accessories list. The
           # garment as a thing to buy or to launder is a different question, and the wear
           # card is no answer to it: "where can i buy cycling clothes" and "how should i
           # wash cycling clothes" both landed here through the bare word "clothes".
           avoid=_NOT_A_BIKE + ("helmet", "hat", "gloves", "glasses", "goggles", "kit",
                                "accessories", "child", "kid", "son", "daughter", "buy",
                                "buying", "shop", "shops", "price", "cheap", "secondhand",
                                "second hand", "wash", "washing", "laundry", "clean", "dryer",
                                # a dark ride is a lights question and a wet ride is a grip and
                                # eyes question: those rows answer them and this card does not,
                                # so the words they own stand this row down
                                "night", "dark", "darkness", "evening", "lights", "lit up",
                                "rain", "raining", "rainy", "wet", "drizzle", "shower",
                                "showers", "storm", "thunder", "snow", "frost", "icy",
                                "freezing", "cold", "coldest", "winter", "windy"),
           bias=2),
    _entry("commute-bike-choice",
           (("commuter", "commuter bike", "commuter bike", "town bike", "hybrid",
             "everyday bike", "which bike", "what bike", "new bike", "what sort of bike",
             "buying a bike", "buy a bike", "buying a new bike"),
            _bike(("should", "get", "buy", "which", "what", "look for", "best", "choice",
                   "recommend", "between", "worth", "work", "five miles", "10 miles"))),
           "A hybrid or gravel bike with 32 to 40mm tyres, mudguard and rack mounts and disc "
           "brakes: those stop in the wet and take a pannier. £500 to £800 new, £200 to £350 "
           "secondhand. A road bike with 23mm tyres and no mounts fights a commute, and a "
           "step-through frame is easier in town clothes.",
           ask=_IS_A_BIKE,
           # "should i buy a new bike or fix mine" is the keep-it-or-replace-it question, and
           # main's bike-second-hand answers it: this row took it on "buy" and "new bike"
           avoid=_NOT_A_BIKE + ("fix mine", "repair mine", "fix it", "repair it", "fix my",
                                "repair my", "or fix", "worth fixing", "worth repairing",
                                "second hand", "secondhand", "my old bike", "old one"),
           bias=2),
    _entry("commute-bike-kit",
           # the route and the safety talk are main's `bike-start`, which answers "how do i cycle
           # to work safely" better than a kit list does: the words stay out of this key
           (("lights", "light", "lock", "pannier", "waterproof",
             "kit", "gear", "clothes", "shower", "accessories", "accessory", "equipment",
             "start", "starting", "beginner", "new to", "commute", "commuting"),
            _bike(("need", "what do i", "should i", "get", "buy", "start", "cycling to work",
                   "commuting", "commute", "for a commute", "first time"))),
           "The minimum is a front light of 500 lumens or more, a rear light, a gold-rated D-lock "
           "through the frame and a rack, a waterproof jacket and gloves. Plan a route on quieter "
           "roads or a cycle path, leave shoes and a change of clothes at work, and start with two "
           "days a week: six miles takes about half an hour at an easy pace.",
           ask=_IS_A_BIKE,
           # the lock itself and a bike already gone are the row above, not the kit list
           # "im buying a bike for my commute" is what to buy, not what to carry on it
           avoid=_NOT_A_BIKE + ("what lock", "which lock", "best lock", "lock it", "locking",
                                "locked", "stolen", "stole", "theft", "thief",
                                "buying a bike", "buy a bike", "buying a new bike",
                                "which bike", "what bike", "new bike", "fix mine",
                                "repair mine", "second hand", "secondhand",
                                # "how far should i cycle as a beginner" is a distance, and the
                                # kit list answered it because "beginner" is one of its keys
                                "how far", "how long", "distance", "miles", "kilometres",
                                "kilometers", "km", "in a day", "a day"),
           bias=2),

]
