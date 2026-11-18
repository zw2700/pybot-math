"""What everyday jobs and things cost: a typical range, what moves it, and what to ask.

Prices are the one thing a bot with no network must never state as fact, so this domain does the
next best thing a friend can do: it says what people usually pay in the UK, names the two or three
things that swing the figure, and ends with the question that turns the guess into a quote. Every
answer is a range, said as a range ("usually", "in most of the country"), and the number that
matters - the one on the quote - is always the firm's to give.

The knowledge is one table, JOBS: a name, the words people use for it, and three sentences. The
entries are built from it, so a new job or a new thing is one line of data and no new code, and a
thousand ways of asking ("how much does a plumber charge", "what does a plumber cost", "is 200
about right for a plumber") all reach the same row.
"""
import re

from .lookup import entry, the_appliance_swallows_the_name

# Every way of asking what something costs. The entry for a job needs one of these as well as the
# job itself, so "my plumber is coming tomorrow" and "how do i fix a leaky tap" stay elsewhere.
_COST = ("how much", "how many pounds", "cost", "costs", "costing", "charge", "charges",
         "charging", "price", "prices", "priced", "quote", "quotes", "quoted", "fee", "fees",
         "hourly rate", "day rate", "call out fee", "callout", "what should i pay", "worth paying",
         "is it worth", "expensive", "cheaper", "afford", "budget for", "typical price",
         "going rate", "fair price", "rip off", "ripped off", "overcharged", "how much is",
         # "is the dentist free on the nhs" is a price question too, and it was the one
         # price question the table did not read: the name of the job still has to be in the
         # line, so "is it free to park" is not a job price.
         "is it free", "free on the nhs", "free on the health service", "do i pay",
         # "are prescriptions free in wales" is the same price question with the country in it,
         # and the bare "free" is what those lines have: the name of the job is still needed
         # beside it, so "free food" and a free boiler grant are not price questions.
         "free in england", "free in scotland", "free in wales", "free in northern ireland",
         "are they free", "are prescriptions free", "is it free in", "free of charge",
         "free for children", "free for pensioners", "free for over 60",
         "do i have to pay", "nhs free", "does the nhs pay", "covered by the nhs",
         # A price is also asked as a verdict on one: "is 400 too much for a roof repair" and
         # "does 2,000 sound right for a new boiler" are the same question as "how much does a
         # roofer charge", and they reached nothing at all.
         "too much", "too expensive", "too dear", "about right", "sound right", "sounds right",
         "reasonable", "over the odds", "is that fair", "is this fair", "fair amount",
         "is that about right",
         # a price is also asked as a verdict and as a complaint: "is a prepayment certificate
         # worth it" and "why am i paying for my prescriptions" are the same charge question as
         # "how much is a prescription", and both reached nothing
         "worth it", "why am i paying", "am i paying", "paying for my", "do i have to pay for",
         "get free", "get them free")

# A trade who puts a figure on the visit itself is asking for that figure to be judged: "the
# electrician wants 120 just to look at it" and "the plumber wants 90 just to come out" are the
# call-out price, and both reached a placeholder, because "wants" and a number are not a price
# word. The "just to" is what keeps the arrival a complaint about money: "when is the plumber
# going to turn up" is a when, and "the plumber wants to come on friday" stays a date.
#
# Only the jobs whose unit of work is the visit get these. A boiler, a kitchen or a bathroom is
# priced as a whole job, and "the boiler man wants 90 just to look at it" answered with the price
# of a new boiler would be a wrong answer where a placeholder at least was honest.
_A_VISIT_FEE = ("just to come out", "just to come round", "just to come over",
                "just to come and look", "just to look", "just to have a look",
                "just to turn up", "just to show up", "just to pop round", "just to call out")
_VISIT_FEE_JOBS = frozenset((
    "plumber", "electrician", "boiler-service", "washing-machine-repair", "drains", "locksmith",
    "handyman", "decorator", "gardener", "oven-clean", "carpet-clean", "gutter-clean", "vet",
    "dentist", "eye-test", "smoke-alarm", "dog-groomer"))

# A repair of a machine in the home is asked as a price, so it needs a price word said outright.
# "is it worth repairing my dishwasher" and "should i repair or replace it" are the decision, and
# they have their own answer: the money rule, not the engineer's rate.
_PRICE = ("how much", "how many pounds", "cost", "costs", "costing", "charge", "charges",
          "price", "prices", "quote", "quotes", "what should i pay", "going rate", "call out",
          "callout", "hourly rate", "pay for")

# A line asking how to do the job itself is the DIY answer, not the price of hiring someone.
# "how to" is not in this list. An avoid phrase is read loosely, so "how to" reached across the
# words in "how much to repair a dishwasher" and stood the price table down - and that line is the
# price of a repair, not the steps for one. The steps are fenced where the two words sit next to
# each other, in _not_a_steps_ask below.
_DIY = ("how do i", "how can i", "myself", "my own", "diy", "step by step",
        # A tip is not a price, and "how much do you tip a cleaner" was quoted £12 to £18 an
        # hour: what the job costs and what to hand the person who does it are two questions,
        # and the tip table answers the second one.
        "tip", "tips", "tipping", "gratuity", "tipped")

# A line that says "how to", read next to each other. "how much to repair a dishwasher" is a
# price and "how to repair a dishwasher" is the steps; the loose avoid above could not tell them
# apart, and no other word does either.
_HOW_TO = re.compile(r"\bhow\s+to\b|\bhow\s+2\b")


def _not_a_steps_ask(understood):
    """False when the line asks for the steps themselves ("how to unblock a drain")."""
    text = understood.get("clean") or understood.get("text") or ""
    return not _HOW_TO.search(str(text).lower())


# "how much does it cost to renew my passport" is a fee question with a how-to verb in it, and
# "how do i renew my passport" is the how-to. A government fee is a set sum, so those rows cannot
# drop "renew" and "apply" from their avoid list without taking the price with it - the two need
# reading apart the way "how much to" and "how to" did above.
_STEPS_ASK = re.compile(
    r"\b(how do i|how can i|how to|how 2|what do i need|what do you need|what do i take|"
    r"do i need|can i renew|can i apply|can i do it|where do i|when should i|what happens if)\b")
_PRICE_ASK = re.compile(
    r"\b(how much|how many pounds|cost|costs|costing|price|prices|priced|fee|fees|charge|"
    r"charges|pays|pay|paid|pence|cheapest|expensive)\b")


def _a_steps_ask_with_no_price(understood):
    """True when the line asks how, or what is needed, and never asks what it costs."""
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    return bool(_STEPS_ASK.search(text)) and not bool(_PRICE_ASK.search(text))


# What people pay in the UK, in ranges. "typical" is the middle of what people report paying,
# "moves" is what pushes it to either end, and "ask" is the one question that gets a real number.
# Ranges, never a single figure: a shop, a region and a month all move it.
# The repair of a machine in the home, asked as "how much does it cost to fix a washing machine",
# "what does a repair on the dishwasher cost". The phrases are built from the appliance names, so a
# new machine is one word here and every way of saying "fix" and "repair" comes with it.
APPLIANCES = ("washing machine", "dishwasher", "tumble dryer", "dryer", "oven", "fridge freezer",
              "fridge", "freezer")


def _repair_phrases(name):
    article = "an" if name[0] in "aeiou" else "a"
    return tuple(f"{verb} {article} {name}" for verb in ("fix", "repair")) + (
        f"fix the {name}", f"repair the {name}", f"fix my {name}", f"repair my {name}",
        f"repair on the {name}", f"fix on the {name}", f"repair on a {name}",
        # The machine in front of the verb, the way it is usually typed: "how much does a fridge
        # repair cost". Every phrase above puts the doing first, so the plain noun-first ask reached
        # no price at all and hedged while "a repair on a fridge" was answered - the same question
        # in the other word order.
        f"{name} repair", f"{name} repairs", f"{name} fix",
        # And the passive: "how much to get my oven fixed". The person is not doing the job, so
        # this is the price of a repair, not the fix-it card's steps.
        f"get the {name} fixed", f"get my {name} fixed", f"get {article} {name} fixed",
        f"get the {name} repaired", f"get my {name} repaired",
        f"have the {name} fixed", f"have my {name} fixed", f"have {article} {name} fixed",
        f"have the {name} repaired", f"have my {name} repaired",
        f"have {article} {name} repaired",
        f"{name} fixed", f"{name} repaired",
        f"{name} looked at", f"look at the {name}", f"look at my {name}")


APPLIANCE_REPAIRS = tuple(phrase for name in APPLIANCES for phrase in _repair_phrases(name))

# A part of a room, or the cleaning of it, is a different price from fitting the whole room.
# Without this "how much is a bathroom mirror" and "how much does it cost to clean a bathroom"
# became the price of a new suite, which is a bigger number than either of them asks for.
_SMALL_THING = ("tap", "taps", "mirror", "mirrors", "tile", "tiles", "tiling", "retile",
                "retiling", "grout", "sealant", "silicone", "shower head", "toilet seat",
                "cistern", "radiator", "extractor", "fan", "lino", "vinyl", "flooring",
                "splashback", "cupboard", "cupboards", "shelves", "worktop", "worktops",
                "panel", "panels", "clean", "cleaning", "deep clean", "cleaner", "cleaners")

# The rooms a decorator is asked to price. One list, so "paint a bedroom", "decorate the hallway"
# and "get the living room painted" all answer the same way.
_PAINT_ROOMS = ("bedroom", "bedrooms", "hallway", "hall", "landing", "lounge", "living room",
                "front room", "dining room", "kitchen", "bathroom", "nursery", "box room",
                "spare room", "study", "office", "stairs", "stairwell", "ceiling", "flat",
                "whole house", "house inside", "one room", "room")

# A bigger job that mentions a room is not the price of refitting the room. A bare "kitchen" or
# "bathroom" took "how much does a kitchen extension cost" off main's per-square-metre extension
# table and gave it the fitted-kitchen figure, and "is it cheaper to refit a kitchen or move" the
# same. The comparison shapes are written as phrases on purpose: a bare "move" would also stand the
# room down for "how much does it cost to move a bathroom", which is the room-moving answer.
_BIGGER_JOB = ("extension", "extensions", "kitchen extension", "bathroom extension", "loft",
               "loft conversion", "conservatory", "or move", "cheaper to move", "rather than move",
               "instead of moving", "moving house", "or sell", "sell up", "or buying",
               "worth doing")

def _boiler_service_answer(memory, reading):
    """The verdict for "is it worth servicing the boiler", the price otherwise."""
    asks = set(reading.get("asks") or ())
    if "how_often" not in asks and asks & {"yesno", "recommend"}:
        return ("Yes, once a year: a boiler service is usually £60 to £120 depending on where you "
                "are, it keeps the warranty valid, catches a failing part before it strands you in "
                "winter, and landlords are legally required to have one. Book it in late summer, "
                "when engineers are quiet and the price is lower.")
    return ("A boiler service is usually £60 to £120 once a year, and a gas safety check on top is "
            "£50 to £90 if you rent the place out. It is a check, not a repair: the engineer "
            "cleans and tests the boiler and tells you what is wearing out, so it is the cheap way "
            "to avoid a winter breakdown. Ask whether the price includes the gas safety certificate "
            "if you need one.")


JOBS = {
    "plumber": {
        "names": ("plumber", "plumbers", "plumbing"),
        "thing": "a plumber",
        "reply": "Most plumbers charge £50 to £100 to turn up and then £40 to £80 an hour, so a "
                 "small job like a dripping tap or a leaking joint comes to £100 to £200. An "
                 "emergency at night or at a weekend roughly doubles it, and parts are on top. "
                 "Ask whether the call-out includes the first hour before you book, and get a "
                 "second quote for anything over a few hundred pounds.",
    },
    "electrician": {
        "names": ("electrician", "electricians", "sparky"),
        "thing": "an electrician",
        "reply": "An electrician is usually £40 to £70 an hour, with a call-out of £50 to £100 "
                 "that often covers the first hour. A new socket or a light fitting is a one-hour "
                 "job; a fuse board or any work in a bathroom or kitchen needs a certificate, "
                 "which adds £50 to £150. Ask for the certificate in the quote, because a "
                 "landlord or a buyer will want it.",
    },
    "boiler": {
        "names": ("boiler", "boilers", "combi boiler"),
        "thing": "a new boiler",
        "reply": "A new combi boiler fitted in place of an old one is usually £1,800 to £3,000, and "
                 "£3,000 to £4,500 if the pipework has to change or a tank comes out. A service is "
                 "£60 to £120 once a year. Get two or three quotes on the same boiler model, "
                 "because the price is mostly the fitter's day and a cheap boiler with a poor "
                 "warranty costs more later; ask how long the warranty runs and who honours it.",
    },
    "heat-pump": {
        # the price of the job, not what a heat pump is: `home_craft`'s own row and the heating
        # fuel comparison both keyed the words "cost" and "running", so "how much does a heat
        # pump cost" was told how one works and "how much does a heat pump cost to run" was told
        # what the fuel costs per unit. The figure is the answer to both, and this row is the
        # figure.
        "names": ("heat pump", "heat pumps", "air source heat pump", "air source",
                  "ground source heat pump", "heat pump cost", "heat pump price"),
        "thing": "a heat pump",
        "bias": 2,
        # what it costs to run is the row under this one, and the figure there is per year.
        # "is it worth getting a heat pump" is the verdict row's question and not a price one:
        # "is it worth" is a price ask in _COST, so the worth-it card lost its own line to a quote.
        "avoid": ("to run", "cost to run", "costs to run", "run a heat pump", "running cost",
                  "running costs", "per year", "a year", "per month", "a month", "electricity",
                  "units of", "how much electricity",
                  # "is a heat pump cheaper than a boiler" is a comparison, and the card that sets the
                  # two fuels side by side answers it; the install price does not.
                  "cheaper than", "than a boiler", "than gas", "compare", "compared", "vs",
                  "versus", "better than", "instead of a boiler",
                  "worth", "worthwhile", "should i", "should we", "would you recommend",
                  "recommend", "any point", "a good idea", "good idea", "sensible"),
        "reply": "An air source heat pump is usually £10,000 to £14,000 fitted, and the Boiler "
                 "Upgrade Scheme takes £7,500 off, so most people pay £2,500 to £6,500. Running "
                 "it costs less than gas for the same heat if the house is insulated and the "
                 "radiators are big enough for the lower flow temperature, so a draughty house "
                 "with small radiators eats the saving. Ask for two quotes, each with a heat loss "
                 "survey of your own house, because that survey is what the price turns on.",
    },
    "heat-pump-running": {
        # "how much does it cost to run a heat pump" is the yearly figure, and the install price
        # is not it: the row above stands down on the run words so this one is the answer.
        "names": ("heat pump", "heat pumps", "air source heat pump", "ground source heat pump"),
        "thing": "a heat pump",
        "bias": 3,
        "ask": ("run", "runs", "running", "to run", "per year", "a year", "a month",
                "electricity", "kwh", "kilowatt", "units", "cost to run", "running cost"),
        "avoid": ("worth", "worthwhile", "should i", "should we", "recommend", "any point",
                  "a good idea", "good idea", "sensible"),
        "reply": "A well-fitted heat pump uses about a third of the electricity of panel heaters "
                 "for the same warmth: a typical three-bedroom house runs one for roughly £700 to "
                 "£1,100 a year at today's electricity price, against £900 to £1,200 on gas, and "
                 "the gap widens as gas gets dearer. It needs radiators big enough for a 45 to "
                 "55C flow temperature and a well-insulated house to hit that; in a draughty house "
                 "with small radiators the running cost climbs above gas. Ask the installer for "
                 "the figure off their own room-by-room design, not the brochure's.",
    },
    "wood-burner": {
        # "how much does a wood burner cost" and "how much to install a log burner" were answered
        # with the price of a hob ring, because "burner" was the only word the cooker's row needed.
        "names": ("wood burner", "woodburner", "wood burning stove", "woodburning stove",
                  "log burner", "logburner", "multi fuel stove", "multifuel stove",
                  "wood stove", "log stove", "stove", "stoves"),
        "thing": "a wood burner",
        "bias": 2,
        "avoid": ("camping", "tent", "gas", "cooker", "cookers", "oven", "hob", "ring",
                  "plate", "kitchen", "backpacking", "trangia", "calor", "bottle",
                  "worth", "worthwhile", "should i", "should we", "recommend", "any point",
                  "a good idea", "good idea", "sensible"),
        "reply": "A wood burning stove is usually £400 to £1,500 for the stove itself and £1,500 "
                 "to £3,000 to line the chimney and fit it, so budget £2,000 to £4,500 done "
                 "properly. It has to be fitted by a Hetas-registered installer, or signed off by "
                 "building control, and only an Ecodesign stove can be sold new now. Ask whether "
                 "the chimney is yours to use and whether the house is in a smoke control area "
                 "before you buy: both change what you can fit.",
    },
    "boiler-service": {
        # "service a boiler" and "serviced" are the ways people type it, and the new-boiler row
        # above takes the bare word: "how much to service a boiler" was quoted £1,800 to £3,000 for
        # a new one, because the phrase "boiler service" is the other word order.
        "names": ("boiler service", "boiler servicing", "service the boiler",
                  "service my boiler", "service a boiler", "service our boiler",
                  "annual boiler service", "gas safety check", "boiler serviced",
                  "get the boiler serviced", "get my boiler serviced",
                  "get a boiler service", "boiler safety check"),
        "thing": "a boiler service",
        # a service is the yearly check; the row above is the price of a new boiler
        "bias": 2,
        "reply": _boiler_service_answer,
    },
    "skip": {
        # "skip" alone is a verb too ("my gears skip", "skipping breakfast"), and a carried
        # "skip" from an earlier line about gears reached this price on "is it worth getting it
        # serviced". Narrowing the names to the article-only forms fixed that and cost four real
        # skip lines ("skip cost", "how much are skips", "i need a skip for the garden" then "how
        # much"), so the plural stays and the verb sense is cancelled by the words that make it
        # one: a gear that skips is not a container to hire, and neither is a meal you missed.
        "names": ("a skip", "skip hire", "hire a skip", "skip permit", "skip bag",
                  "a builder's skip", "skip", "skips", "skip cost", "skip price",
                  "skip prices", "skip size", "skip sizes", "size skip", "yard skip"),
        # avoid is read against the whole talk, so the word that carried the verb into the next
        # turn is the same word that cancels the row. "skipping"/"skipped" must NOT be here: a
        # loose form of either is the bare word "skip", which would cancel every skip line.
        "avoid": ("gears", "gear", "chain", "chains", "cassette", "derailleur", "sprocket",
                  "pedal", "pedals", "bike", "bikes", "bicycle", "cycl", "breakfast", "brunch",
                  "meal", "meals", "lunch", "dinner", "tea", "homework", "class", "school",
                  # Nothing is ever "serviced" but a machine, so the word rules the hire out: a
                  # carried "skip" from a gears line reached this price on "is it worth getting it
                  # serviced", and a builder's skip at £150 to £300 was the answer to a bicycle
                  # question. The service is the bike's card (bot/knowledge/bikes.py).
                  "serviced", "servicing", "tune up", "tuneup", "overhaul", "mechanic"),
        "thing": "a skip",
        "reply": "A builder's skip is usually £150 to £300 for a week, and a permit on a public "
                 "road adds £30 to £60. Soil, rubble and hardcore cost more than household "
                 "rubbish because of the weight, and a mattress or a fridge often cannot go in at "
                 "all without a surcharge. Ask what the price includes and what happens if it is "
                 "overfull, since a second skip is the usual surprise.",
    },
    "removals": {
        "names": ("removal firm", "removals", "removal company", "removal van", "removal men",
                  "moving firm"),
        "thing": "removals",
        "reply": "Two movers and a van are usually £400 to £700 for a local day, and a one-bedroom "
                 "flat moved locally comes in around £300 to £500. A three-bedroom house is "
                 "£800 to £1,500, more if there are stairs or a long carry, and packing as well "
                 "roughly doubles it. Ask whether the quote is fixed or hourly, whether insurance "
                 "covers breakage, and whether the price changes if the move runs into a second "
                 "day.",
    },
    "van-hire": {
        # A hired car is not a hired van: with "hire a car" and "car hire" in this list, "how much
        # does it cost to hire a car" was quoted 40 to 80 pounds a day for a transit and a deposit
        # against damage on a vehicle the person had not described. The car is travel.car-hire's
        # question, which says to compare the total and to pay the deposit on a credit card.
        "names": ("van hire", "hire a van"),
        "thing": "hiring a van",
        "reply": "A transit-sized van is usually £40 to £80 a day, plus a deposit of £150 to £300 "
                 "held against damage. Mileage and a young-driver surcharge are the two things "
                 "that turn a cheap ad into an expensive day, and the excess on the insurance is "
                 "often £1,000 unless you pay extra. Ask for the total with mileage and the excess "
                 "before you book, and photograph the van all round before you drive it away.",
    },
    "cleaner": {
        "names": ("cleaner", "cleaners", "cleaner charge", "housekeeper", "domestic cleaner"),
        # "how much is a steam cleaner" was quoted a cleaner's hourly rate: the machine's name
        # carries the word "cleaner" and nothing in the line says a person. Every machine with
        # cleaner in its name is a price of its own, and none of them is this hourly rate.
        "avoid": ("steam cleaner", "steam cleaners", "steam mop", "steam mops",
                  "vacuum cleaner", "vacuum cleaners", "hoover", "oven cleaner",
                  "drain cleaner", "pressure washer", "jet washer", "pool cleaner",
                  # A window cleaner is the one machine-shaped name that is still a person: he
                  # quotes by the hour, and holding his words out sent "how much does a window
                  # cleaner charge" to the glazing card, which is the opposite of the bug this
                  # list fixes. A dry cleaner is a shop, and a steam, vacuum, oven, drain or pool
                  # cleaner is a thing, so those stay.
                  "robot cleaner", "dry cleaner", "dry cleaners",
                  # Now that window cleaning has its own band - it is priced by the visit, not
                  # the hour - the word goes out here, so the person on a ladder gets the visit
                  # price rather than the £12 to £18 an hour of a house cleaner.
                  "window", "windows", "window cleaner", "window cleaners",
                  # A carpet cleaner is a machine you hire or buy, and the hourly rate of the
                  # person who cleans a house was the answer to both "how much is a carpet
                  # cleaner" and a hire price.
                  "carpet cleaner", "carpet cleaners"),
        "thing": "a cleaner",
        "reply": "A cleaner is usually £12 to £18 an hour, so a two-hour weekly visit is £25 to "
                 "£40, and a one-off deep clean of a three-bedroom house is £60 to £120. An "
                 "agency costs more than someone working for themselves but covers insurance, tax "
                 "and holidays. Ask what is included (inside the oven and the fridge usually are "
                 "not), and whether you supply the products.",
    },
    "decorator": {
        # "how much does it cost to paint a room" was the shopping list for the paint, and the
        # named room is the same question: "how much does it cost to paint a bedroom" and
        # "wallpapering one room" were the shopping list or a pass. The room shapes are built
        # from one list so a new room answers every wording without a new key.
        "names": ("decorator", "decorators", "painter", "painters", "painting and decorating",
                  "paint a room", "paint the room", "paint my room", "paint a wall",
                  "paint the walls", "paint my walls", "painting a room", "decorate a room",
                  "decorating a room", "get a room painted", "have a room painted",
                  "hang wallpaper", "wallpapering", "wallpaper a room", "wallpapering a room",
                  "wallpaper one room", "wallpapering one room", "decorate the flat",
                  "get the room decorated", "have a room decorated", "have the room decorated",
                  "paint the flat", "decorating a flat", "painting the house inside")
                  + tuple("paint a " + room for room in _PAINT_ROOMS)
                  + tuple("paint the " + room for room in _PAINT_ROOMS)
                  + tuple("decorate a " + room for room in _PAINT_ROOMS)
                  + tuple("decorate the " + room for room in _PAINT_ROOMS)
                  + tuple("wallpaper a " + room for room in _PAINT_ROOMS)
                  + tuple("get a " + room + " painted" for room in _PAINT_ROOMS)
                  + tuple("get the " + room + " painted" for room in _PAINT_ROOMS)
                  + tuple("get a " + room + " decorated" for room in _PAINT_ROOMS),
        # A price is not a quantity. "how much wallpaper do i need" was this card in full - a
        # decorator's day rate and a question about who moves the furniture - when the person
        # wanted the roll count, and "how many rolls" reached the wallpaper card all along. The
        # ask for the amount is the other card's, so the cut is on the verb and not on the word
        # wallpaper: "how much does it cost to decorate a room" keeps this answer.
        "avoid": ("do i need", "will i need", "how many rolls", "rolls of wallpaper",
                  "how much wallpaper", "how much paint do i need", "how much paint will i need",
                  "how much wall", "coverage", "square metres of", "per square metre"),
        "thing": "a decorator",
        "reply": "A decorator is usually £150 to £250 a room for walls and ceiling, or £20 to £40 "
                 "an hour, with paint and materials on top. Emulsion on sound walls is the cheap "
                 "end; filling, lining paper, gloss woodwork and high ceilings push it up. Ask "
                 "whether the price includes the paint, how many coats, and who moves the "
                 "furniture.",
    },
    "handyman": {
        "names": ("handyman", "handymen", "odd job man", "odd jobs"),
        "thing": "a handyman",
        "reply": "A handyman is usually £25 to £45 an hour with a minimum of one or two hours, so "
                 "a morning of small jobs is £100 to £150. Jobs that need a certificate - gas, "
                 "electrics in a bathroom, anything structural - are not handyman work whatever "
                 "the advert says. Ask for the hourly rate, the minimum charge and whether they "
                 "take the rubbish away.",
    },
    # A carpenter and a joiner are the same trade in most firms, and both were the "two quotes"
    # fallback on main ("I can't price a job from here") while a plumber, a decorator, a handyman,
    # a builder and a locksmith all had a band. Fitted work is priced by the job, which is the
    # point a day rate cannot make on its own.
    "carpenter": {
        "names": ("carpenter", "carpenters", "joiner", "joiners", "carpentry", "woodwork",
                  "cabinet maker", "cabinetmaker", "fitted wardrobes", "fitted furniture"),
        "thing": "a carpenter",
        "reply": "A carpenter is usually £150 to £250 a day, or £30 to £50 an hour for small jobs "
                 "with a one-hour minimum, and a joiner hanging an internal door is £60 to £120 "
                 "each. Fitted wardrobes and shelving are priced as a whole: £1,000 to £3,000 for "
                 "a run of built-in wardrobes with the materials in. Ask for the day rate, whether "
                 "the price is fixed or an estimate, and get the material allowance in writing.",
    },
    # Every trade a person rings for a job has a rate band, and eight of them had none: "how much
    # does a plasterer charge" and "how much does a tiler charge" were the "two quotes" fallback,
    # "how much does a gas engineer charge" was "there is no list price", a heating engineer and a
    # glazier were the car-parts "prices move too fast", a surveyor was the advice card with no
    # figure in it, and "how much does a drain company charge" reached the phone-battery card on
    # the word "drain". A trade named with a price asked is this table's question.
    "plasterer": {
        "names": ("plasterer", "plasterers", "plastering", "skim a wall", "skim a ceiling",
                  "skimming", "plasterboard"),
        "thing": "a plasterer",
        "reply": "A plasterer is usually £150 to £250 a day, or £15 to £25 a square metre for "
                 "skimming: a whole room's walls and ceiling is £300 to £600, and patching a "
                 "ceiling after a leak is £80 to £150. Boarding over old plaster adds £200 to "
                 "£400 a room. Ask whether the price includes the boards and the finishing coat, "
                 "and how long it takes to dry before paint.",
    },
    "tiler": {
        "names": ("tiler", "tilers", "tiling", "tile a bathroom", "tile a kitchen", "retile",
                  "re-tile"),
        "thing": "a tiler",
        "reply": "A tiler is usually £150 to £250 a day, or £25 to £45 a square metre for labour: "
                 "a small bathroom's walls and floor is £500 to £900, and a kitchen splashback "
                 "£150 to £300. Tiles themselves are £15 to £60 a square metre on top. Ask "
                 "whether the price includes taking the old tiles off, the adhesive and the "
                 "grouting, because that is where two quotes differ most.",
    },
    "gas-engineer": {
        "names": ("gas engineer", "gas safe", "gas safe engineer", "heating engineer",
                  "boiler engineer", "boiler service", "service the boiler", "boiler repair",
                  "gas boiler", "gas fire", "gas hob fitting"),
        "thing": "a Gas Safe engineer",
        "reply": "A boiler service is £60 to £120, and a repair is £80 to £250 including the "
                 "common parts, with the first hour often £50 to £90. Out of hours or a "
                 "breakdown in winter costs £100 to £150 before parts. Check the engineer is on "
                 "the Gas Safe register, and ask whether the repair is a fixed price before they "
                 "start.",
    },
    "glazier": {
        "names": ("glazier", "glaziers", "double glazing repair", "broken window", "new window "
                  "pane", "replace a window pane", "sealed unit", "window glass", "cracked window"),
        "thing": "a glazier",
        "reply": "A single pane of ordinary glass is £60 to £120 fitted, and a sealed double-glazed "
                 "unit is £100 to £250, with a big or toughened one £250 to £500. A broken window "
                 "boarded up the same day is £100 to £200. Ask whether the frame is sound, because "
                 "a rotten frame means a whole new window at £400 to £1,000, and check whether "
                 "your home insurance covers the glass.",
    },
    "window-cleaner": {
        # gutter clearing has a band of its own in this table, so the windows row names no
        # gutter: "how much does it cost to clean the gutters" was answered with window prices
        "names": ("window cleaner", "window cleaners", "clean the windows", "window cleaning",
                  "fascia cleaning"),
        "thing": "a window cleaner",
        "bias": 2,
        "reply": "A window cleaner is usually £10 to £25 for a small house and £25 to £40 for a "
                 "larger one, inside usually not included, and a four-weekly round is cheaper "
                 "than a one-off. Gutter clearing is £60 to £150 for a house, and fascia cleaning "
                 "£100 to £250. Ask whether they use pure water and a pole or ladders, and "
                 "whether the price covers the frames and the sills.",
    },
    "chimney-sweep": {
        "names": ("chimney sweep", "chimney sweeps", "sweep the chimney", "sweeping the chimney",
                  "flue sweep", "sweep the flue"),
        "thing": "a chimney sweep",
        "reply": "A chimney sweep is usually £50 to £90 for an ordinary chimney, and £90 to £150 "
                 "if it is lined, thatched or needs a camera. A wood burner wants sweeping once a "
                 "year before the season and twice if it is your main heat, and a gas appliance "
                 "needs a Gas Safe service rather than a sweep. Ask for a certificate, because "
                 "your insurer may ask for one after a chimney fire.",
    },
    "surveyor": {
        "names": ("surveyor", "surveyors", "survey", "surveys", "house survey", "building survey",
                  "homebuyer report", "structural survey", "condition survey", "valuation"),
        "thing": "a surveyor",
        # "how much does a surveyor charge" and "what does a structural survey cost" came back
        # as "Yes, have one done - the lender's valuation is not a survey..." from the house
        # survey card, which does carry the figures, in its second sentence: the card and this
        # band sat at the same weight, so which one a person got was chance. The band answers
        # the price with the price, so it takes the price ask; the card keeps "do i need a
        # surveyor" and "is a structural survey worth it", which name no price at all.
        "bias": 2,
        "reply": "A survey is £400 to £700 for a HomeBuyer report and £600 to £1,200 for a full "
                 "building survey, on a typical house; a flat is at the lower end and a big or old "
                 "house at the top. The lender's valuation is not a survey and only tells the "
                 "lender the house is worth the loan. Get the survey before you exchange, and "
                 "ring the surveyor afterwards to ask what actually matters.",
        # a decision is the card's: "is a structural survey worth it" wants the yes or no, and
        # the band's figures are already in the card's own answer.
        # ... and a survey already in hand is a report to read, not a price to ask.
        "avoid": ("worth it", "is it worth", "worth", "do i need", "should i", "instead of",
                  "which level", "what level", "came back", "come back", "found", "flagged",
                  "says", "damp", "the survey said", "had the survey", "got the survey"),
    },
    "pest-control": {
        "names": ("pest control", "pest controller", "pest control company", "exterminator",
                  "rat catcher", "get rid of rats", "wasp nest removal", "bed bug treatment",
                  "mouse treatment"),
        "thing": "pest control",
        "reply": "A pest controller is usually £80 to £150 for a wasp nest and £100 to £250 for "
                 "rats or mice, which usually covers two visits and the bait. Bed bugs are the "
                 "expensive one at £300 to £800 for a flat, sometimes with a second treatment. "
                 "Your council may do rats and mice cheaper, so ring them first, and ask whether "
                 "the price includes the follow-up visit.",
    },
    "architect": {
        "names": ("architect", "architects", "architectural drawings", "planning drawings",
                  "building regs drawings", "structural engineer"),
        "thing": "an architect",
        "reply": "Drawings for an extension are usually £1,000 to £2,500, and a full service is 8 "
                 "to 15% of the build cost, so a £60,000 extension is £5,000 to £9,000 in fees. A "
                 "structural engineer's calculations are £400 to £1,000 on top when a wall is "
                 "coming out. Ask what the fee covers - planning, building regs, and site visits "
                 "during the build are separate jobs.",
    },
    "gardener": {
        "names": ("gardener", "gardeners", "landscaper", "lawn care"),
        "thing": "a gardener",
        "reply": "A gardener is usually £20 to £35 an hour, and a fortnightly cut of a small lawn "
                 "is £30 to £50 a visit. One-off clearances, hedges and anything with a skip are "
                 "priced by the job instead. Ask whether green waste is taken away or left for "
                 "you, because that is often the difference between two quotes.",
    },
    "washing-machine-repair": {
        # the repair phrases only: "how much does a washing machine cost" is the price of the
        # machine and belongs with the shopping answers, not with this one
        "names": ("washing machine repair", "tumble dryer repair", "dishwasher repair",
                  "appliance repair", "get the washing machine fixed") + APPLIANCE_REPAIRS,
        "thing": "repairing an appliance",
        "ask": _PRICE,
        "reply": "A repair is usually £60 to £120 including the first hour, with parts on top, so "
                 "expect £100 to £200 for a common fault. On a machine more than eight years old, "
                 "compare the quote with a new one: a £150 repair on a ten-year-old machine is "
                 "often money down. Ask for the call-out charge and whether it comes off the "
                 "repair if you go ahead.",
    },
    "drains": {
        # "how much does a drain company charge" and "what do drainage companies charge" name the
        # firm rather than the blockage, and they were the "prices move too fast" fallback.
        "names": ("drain", "drains", "blocked drain", "drain unblocking", "sewer",
                  "drain company", "drain companies", "drainage company", "drains company",
                  "sewer company", "drain clearing", "clear a drain", "clear the drain"),
        # A battery that drains is not a pipe under the house. "how do i stop my phone battery
        # draining so fast" then "i charge it every night" reached this price, because the
        # conversation's subject was written back into the line and "charge" is what a plumber
        # does; there is no plumbing in the chat at all. The device words and the charging
        # phrases stand this entry aside, and a drain in a house still gets its price.
        # "charging" cannot be in an avoid list: an avoid is read loosely, so it also stood this
        # row down for the word "charge", and "how much does a drain company charge" - a price
        # asked with "charge" in it - was left with no answer at all.
        "avoid": ("battery", "batteries", "phone", "iphone", "ipad", "android", "laptop",
                  "computer", "tablet", "charger", "charge it", "charge my",
                  "charge the phone", "charge overnight", "battery drain",
                  "draining fast", "drains fast", "drains so fast"),
        "thing": "clearing a drain",
        "reply": "Clearing a blocked drain is usually £80 to £200 with rods or a pressure jet, and "
                 "a camera survey to find the cause is £150 to £300 on top. Roots and collapsed "
                 "pipework are the expensive cases. Ask whether the price includes the survey and "
                 "the waste removal, and if the blockage is in the pipe the water company owns, "
                 "ring them first because they clear it free.",
    },
    "locksmith": {
        "names": ("locksmith", "locksmiths", "lock change", "locked out"),
        "thing": "a locksmith",
        "reply": "A locksmith is usually £60 to £120 to let you back in during the day, and £120 to "
                 "£250 at night or at a weekend, with a new lock £80 to £150 fitted. The cheap "
                 "quote on a van is often the call-out only, with the rest added on the doorstep. "
                 "Ask for the total price on the phone, before they come out, and pay by card so "
                 "there is a record.",
    },
    "storage": {
        "names": ("storage unit", "self storage", "storage"),
        # a phone out of storage is not a room to rent: "how much storage do i have left on my
        # phone" is the screen that shows it, which is technology's answer
        "avoid": ("phone", "iphone", "ipad", "android", "laptop", "computer", "mac", "macbook",
                  "pc", "tablet", "disk", "hard drive", "hard disk", "gb", "mb", "memory",
                  "space left", "storage left", "left on my", "storage do i have",
                  # how much a device needs is technology's question, not a room to rent:
                  # "how much storage do i need for photos" was quoted a self-storage unit
                  "ssd", "hdd", "hard drive", "hard disk", "disk space", "photos on",
                  "pictures", "512gb", "256gb", "128gb", "500gb", "1tb", "2tb", "ps5",
                  "console", "steam", "laptop", "tablet", "ipad", "macbook",
                  # the cloud is the same word and a different shop: "is it worth paying for cloud
                  # storage" was priced as a room to rent. A plan is paid for monthly and holds
                  # photos, so the words that say so stand this row down.
                  "cloud", "icloud", "the cloud", "google drive", "google one", "onedrive",
                  "dropbox", "backup", "back up", "backed up", "photos", "subscription",
                  "paying for"),
        "thing": "a storage unit",
        "reply": "A storage unit is usually £60 to £150 a month for 25 to 50 square feet, which "
                 "holds a one-bedroom flat, and the first month is often half price. The price "
                 "creeps up after the intro offer, and insurance is either included or pushed at "
                 "you on the day. Ask what the rate is in month four, the notice period, and "
                 "whether you need your own padlock.",
    },
    "sofa": {
        "names": ("sofa", "sofas", "couch", "settee", "armchair"),
        # a sofa being cleaned is the cleaning price, not the price of a sofa
        "avoid": ("clean", "cleaning", "cleaned", "wash", "washing", "stain"),
        "thing": "a sofa",
        "reply": "A mid-range three-seater is usually £600 to £1,200, with £300 to £500 at the "
                 "cheap end and £1,500 upwards for a good frame and fabric. The frame, the filling "
                 "and the fabric are what the money buys, and delivery, assembly and a stain "
                 "guard are usually extra. Sit on it in the shop for ten minutes and ask what the "
                 "frame is made of and how long the cover is guaranteed.",
    },
    "mattress": {
        "names": ("mattress", "mattresses"),
        "thing": "a mattress",
        "reply": "A decent double mattress is usually £300 to £700, with £150 to £250 at the cheap "
                 "end and £900 upwards for pocket springs or a good foam. Firmness matters more "
                 "than price, and a mattress that is too soft is the common mistake. Ask about the "
                 "trial period and whether the guarantee covers sagging, and take the old one away "
                 "as part of the deal if you can.",
        # "how much water do i need to clean a mattress stain" is a cleaning question with a
        # "how much" in it, and the price answer is the wrong one: cleaning.py owns every line
        # with a stain, a smell or a wash in it, whatever the money words say.
        "avoid": ("clean", "cleaning", "cleaned", "stain", "stains", "smell", "smells",
                  "wash", "washing", "vacuum", "hoover", "water"),
    },
    "driving-lessons": {
        "names": ("driving lesson", "driving lessons", "driving instructor", "learner driver"),
        "thing": "driving lessons",
        "reply": "Lessons are usually £30 to £45 an hour, and a block of ten is often £270 to £400. "
                 "Most people need 40 to 50 hours of lessons plus practice, so the total lands "
                 "around £1,500 to £2,000 with the tests. Ask whether the car is used for the test "
                 "and what that costs, and whether the instructor is on the official register.",
    },
    "vet": {
        "names": ("vet", "vets", "vet visit", "veterinary", "vet bill"),
        "thing": "a vet visit",
        "reply": "A consultation is usually £40 to £70, and anything done in it - a jab, a blood "
                 "test, an x-ray - is on top, so a first visit often lands at £80 to £150. Out of "
                 "hours is £150 or more before treatment. Ask for the estimate in writing before "
                 "you agree to treatment, and ask what insurance would have covered, because the "
                 "cost of a dog or cat is mostly these bills.",
    },
    "dentist": {
        "names": ("dentist", "dentists", "dental", "check up", "checkup"),
        "thing": "a dentist",
        # whether it is free is the qualifying list, which nhs-dentist-free answers
        "avoid": ("free", "is it free", "do i pay", "do i have to pay", "covered", "qualify",
                  "exempt"),
        "reply": "A private check-up is usually £40 to £80, with a hygienist visit £40 to £70 and a "
                 "filling £80 to £200. On the NHS in England you pay a fixed band charge set "
                 "nationally, which covers the check-up and any work in that band, and Wales, "
                 "Scotland and Northern Ireland have their own charges. Ask which band your "
                 "treatment falls in before you agree to it.",
    },
    "glasses": {
        # "eyeglasses" is a different word to the matcher from "glasses", so the cost of a pair
        # went unanswered for anyone who writes it.
        "names": ("glasses", "spectacles", "eyeglasses", "eye glasses"),
        # "a glass of milk" is a portion, not a pair of spectacles: the food tables answer what
        # is in it, and the cost of eyewear is a different question.
        "avoid": ("eye test", "eye tests", "contact lens", "contact lenses", "optician",
                  "glass of", "glasses of",
                  # "how much water in a glass" is a drink measure, not the price of
                  # spectacles: the drink words keep the price entry off the lines the units
                  # table answers.
                  "water", "milk", "juice", "squash", "cola", "beer", "wine", "drink",
                  "drinks"),
        "thing": "glasses",
        "reply": "A pair of glasses is usually £100 to £300 with standard lenses, and varifocals or "
                 "thin lenses push it to £300 to £500. The frame is where the money goes, and the "
                 "two-for-one offers usually mean two pairs of a cheap lens. Ask what the lenses "
                 "cost on their own, and ask for your prescription and pupillary distance so you "
                 "can compare anywhere.",
    },
    "eye-test": {
        "names": ("eye test", "eye tests", "sight test", "optician"),
        "thing": "an eye test",
        "bias": 2,
        "reply": "An eye test is usually £25 to £45 on the high street, and free on the NHS if you "
                 "qualify - over 60, diabetic, glaucoma in the family, or on certain benefits. A "
                 "retina photo or a scan is often offered as an extra £10 to £25. Ask what the "
                 "test includes and whether the prescription is yours to take away.",
    },
    "contact-lenses": {
        "names": ("contact lenses", "contact lens", "daily lenses", "monthly lenses"),
        "thing": "contact lenses",
        "bias": 2,
        "reply": "Contact lenses are usually £15 to £35 a month on a supply plan, and the "
                 "fitting appointment at the start is £30 to £60. Daily disposables cost more per "
                 "day than monthlies and need no cleaning, and the aftercare visit is often "
                 "included in the plan. Ask what the plan includes, how often the checks are, and "
                 "whether you can stop whenever you like.",
    },
    "oven-clean": {
        "names": ("oven clean", "oven cleaning", "clean the oven", "clean my oven",
                  "extractor clean"),
        "thing": "an oven clean",
        "reply": "An oven clean by a professional is usually £50 to £90, and the hob and the "
                 "extractor are often £15 to £30 extra each. It takes an hour or two and the "
                 "difference is mostly how long since it was last done. Ask whether the price "
                 "includes the shelves and the door glass, and whether they use a dip tank for the "
                 "racks - the good ones do.",
    },
    "carpet-clean": {
        "names": ("carpet clean", "carpet cleaning", "clean a carpet", "clean my carpets",
                  "clean the carpets", "clean the carpet", "rug clean", "sofa clean",
                  "clean a sofa", "clean my sofa", "sofa cleaning", "clean the sofa",
                  "clean my couch"),
        "thing": "a carpet clean",
        "reply": "A carpet clean is usually £25 to £40 a room, or £100 to £200 for a whole flat, "
                 "with stairs and stubborn stains priced separately. A sofa or a rug is £40 to "
                 "£100. Ask whether the price includes the stairs and a stain treatment, and "
                 "whether they move the furniture, because two quotes that look different usually "
                 "differ on those two things.",
    },
    "kitchen": {
        "names": ("new kitchen", "kitchen fitter", "kitchen units", "fitted kitchen",
                  # the same plain-room fault as the bathroom below
                  "kitchen", "kitchen refit", "refit a kitchen", "redo the kitchen",
                  "kitchen refurb", "kitchen renovation"),
        "thing": "a new kitchen",
        # the plain room is greedy on its own: a tap, a worktop or a clean is a different price
        # from fitting the whole room, so those stand the whole-room row down.
        "avoid": _SMALL_THING + _BIGGER_JOB,
        "reply": "A mid-range kitchen is usually £5,000 to £15,000 fitted, and £20,000 or more with "
                 "appliances, worktops and building work. Roughly a third units, a third worktop "
                 "and appliances, a third fitting. Get three quotes on the same written scope and "
                 "ask what happens if the walls are not square, which is where the price moves.",
    },
    "worktop": {
        # The room rows above stand down for a worktop on purpose: a worktop is its own job and
        # its own price, and until this row existed "how much is a kitchen worktop" stood every
        # room row down and was answered by the kitchen-cleaning card.
        "names": ("worktop", "worktops", "kitchen worktop", "kitchen worktops", "countertop",
                  "counter top", "countertops", "counter", "counters", "butcher block"),
        "thing": "a worktop",
        # A how-to about the surface is the cleaning and the fitting card's question, and a
        # scratch or a burn is a repair, so the price row leaves those alone.
        "avoid": ("clean", "cleaning", "wipe", "disinfect", "oil", "oiling", "stain",
                  "stains", "scratch", "scratches", "scratched", "burn", "burnt", "chip",
                  "chips", "chipped", "repair", "replace myself", "how do i fit",
                  "how to fit", "fit it myself", "seal", "sealing", "shine", "polish"),
        "reply": "A laminate worktop is usually £60 to £120 a metre, solid wood £150 to £400, and "
                 "quartz, granite or sintered stone £250 to £600. Fitting is £200 to £500 for a "
                 "straight run, and more where it has to be cut round a sink, a hob or a corner. "
                 "Ask whether the price is per metre or for the length you need, whether cutting "
                 "and sealing the edges is included, and have it templated on site rather than "
                 "from your own measurements.",
    },
    "smoke-alarm": {
        "names": ("smoke alarm", "smoke alarms", "smoke detector", "smoke detectors"),
        "thing": "a smoke alarm",
        # Where one goes, why it chirps and how many a flat needs are the placement card's
        # questions, and a price is not what those lines are asking.
        "avoid": ("where", "place", "placing", "put", "position", "how many", "install",
                  "installing", "fitted", "beep", "beeps", "beeping", "chirp", "chirping",
                  "false alarm", "goes off", "battery", "batteries", "test", "testing",
                  "hard of hearing", "landlord", "wired", "wiring", "heat detector"),
        "reply": "A battery smoke alarm is usually £10 to £25, and £30 or so with a sealed "
                 "ten-year battery. A mains one with a backup battery is £25 to £40 plus an "
                 "electrician, and three linked so they all sound together is £60 to £120. Test "
                 "it monthly and change the battery once a year even if it has not chirped, and "
                 "ask your landlord about the mains one in a rented flat, since fitting and "
                 "checking it is their job rather than yours.",
    },
    "bathroom": {
        # "how much does a bathroom cost" and "how much is a bathroom refit" are the same
        # question as "how much does a new bathroom cost", and they were the cleaning routine:
        # the name list wanted "new" or a fitter, so the plain room fell through to the cleaner.
        # The how-to is fenced by _DIY ("how do i clean the bathroom" says "how do i") and the
        # room on its own is read only beside a price word, so the cleaning lines stay put.
        "names": ("new bathroom", "bathroom fitter", "bathroom suite", "bathroom",
                  "bathroom refit", "refit a bathroom", "redo the bathroom", "bathroom refurb",
                  "bathroom renovation", "shower room"),
        "thing": "a new bathroom",
        # the plain room is greedy on its own: a tap, a mirror or a clean is a different price
        # from fitting the whole room, so those stand the whole-room row down.
        "avoid": _SMALL_THING + _BIGGER_JOB,
        "reply": "A new bathroom is usually £3,000 to £7,000 fitted, and £8,000 to £12,000 with the "
                 "bath moved, the walls tiled and the plumbing changed. Tiling and moving the "
                 "toilet or the bath account for most of the difference. Ask for the scope written "
                 "down, including who makes good the walls, and agree what happens if the floor "
                 "under the old suite is rotten.",
    },
    "gutter-clean": {
        "names": ("gutter", "gutters", "gutter clean", "gutter cleaning"),
        "thing": "cleaning gutters",
        "reply": "Gutter clearing is usually £60 to £150 for a house, more for three storeys or a "
                 "lot of access problems. A repair or a new run of gutter is a separate job, "
                 "priced by the metre. Ask whether the price includes the downpipes and a check "
                 "for leaks, and whether they clear up what comes out.",
    },
    "haircut": {
        "names": ("haircut", "hair cut", "barber", "hairdresser", "salon"),
        # a tip is a share of the bill, not the price of the cut
        "avoid": ("tip", "tips", "tipping", "gratuity",
                  # what to charge is the other side of the counter, and "how much to charge for a
                  # haircut" was answered with what a cut costs to buy
                  "to charge", "charge for", "should i charge", "what to charge", "my prices",
                  "price list", "self employed", "self-employed", "my rate", "my rates",
                  "charge per"),
        "thing": "a haircut",
        "reply": "A cut is usually £15 to £35 in a salon and £10 to £20 at a barber, with colour "
                 "from £60 to £150 depending on how much work it is. A senior stylist costs more "
                 "than a junior, and a dry cut is often cheaper. Ask for the price of the cut and "
                 "the blow dry separately, because the blow dry is the surprise on the bill.",
    },
    "dog-groomer": {
        # "how much to groom a dog" was the grooming how-to, because the row only knew the words
        # "groomer" and "dog grooming": the verb is how most people ask for the price.
        "names": ("dog groomer", "groomer", "groomers", "dog grooming", "groom my dog",
                  "groom a dog", "groom the dog", "grooming my dog", "grooming a dog", "dog groom",
                  "get my dog groomed", "get the dog groomed", "dog bathed", "dog clipped",
                  "dog trimmed", "dog hand stripped", "grooming cost", "dog grooming cost",
                  "cost of grooming", "grooming for a dog"),
        "thing": "a dog groomer",
        "reply": "A dog groomer is usually £30 to £60 depending on the size and coat, with a "
                 "hand-strip or a matted coat costing more. Ask what happens if your dog is "
                 "matted, because some charge by the hour to sort it out, and book four to six "
                 "weeks apart for a coat that keeps its shape.",
    },
    "neutering": {
        # "how much does it cost to neuter a dog" now reaches the operation's own price instead of
        # the price of buying a puppy
        "names": ("neuter", "neutering", "neutered", "spay", "spaying", "spayed", "castrate",
                  "castrating", "castrated", "get my dog done", "get my cat done"),
        "thing": "neutering",
        # this price is the dog's and the cat's, and a rabbit is a different operation at a
        # different price, answered by the pet knowledge row
        "avoid": ("rabbit", "rabbits", "bunny", "bunnies", "hamster", "hamsters", "guinea pig",
                  "guinea pigs", "gerbil", "gerbils", "ferret", "ferrets",
                  # "is it worth neutering my dog" is whether to do it, not what it costs, and
                  # the pet row has the health case for the animal named
                  "why", "worth it", "is it worth", "worth doing", "worth getting", "benefit",
                  "benefits", "point of", "point in", "pros", "pros and cons",
                  "cons and pros", "should i", "should we",
                  "good idea", "advice"),
        "reply": "Neutering is usually £150 to £300 for a dog and £60 to £120 for a cat, with a "
                 "bitch or a female cat at the top of the range because the operation is bigger. "
                 "Many charities run low-cost schemes, and the price usually includes pain relief "
                 "and a check-up. Ask whether the quote covers a follow-up visit, and most are "
                 "home the same day and back to normal within a few days.",
    },
    "dog-walker": {
        # the walker and the groomer are two prices for two jobs, and a walker question used to
        # open with the groomer's £30 to £60
        "names": ("dog walker", "dog walkers", "dog walking", "walk my dog", "walk the dog",
                  "dog walk", "someone to walk my dog", "dog walker cost", "walking cost",
                  "dog walking cost", "cost to walk a dog", "cost of a dog walker"),
        "avoid": ("groom", "groomer", "grooming", "clip", "trim", "bath"),
        "thing": "a dog walker",
        "reply": "A dog walker is usually £10 to £18 for a half-hour walk and £15 to £25 for an "
                 "hour, less per dog if they walk a group of four or five. Solo walks cost the "
                 "most, and a walker who is insured and does a first meet-and-greet at your house "
                 "is worth a pound or two more. Ask what happens on a wet day and how many dogs "
                 "go out at once.",
    },
    "builder": {
        "names": ("builder", "builders", "building work"),
        "thing": "a builder",
        "reply": "A builder is usually £150 to £300 a day for one person, or £200 to £350 for two, "
                 "and the big jobs are priced as a whole rather than by the day. Scaffolding, skips, "
                 "and any work that needs building regulations add to it, and a quote should name "
                 "all three if they apply. Ask for the price with the materials listed separately, "
                 "and ask what happens if the job runs over, because that is where the total moves.",
    },
    "fence": {
        "names": ("fence", "fencing", "garden fence", "fence panels"),
        "thing": "a fence",
        # who owns the fence and who pays for it is not what a fence costs: the home answer
        # takes those, and "do i have to pay half the fence" was quoted a price per metre
        "avoid": ("pay half", "half the cost", "go halves", "split the cost", "who pays",
                  "who should pay", "who has to pay", "who owns", "whose fence",
                  "who is responsible", "responsible for", "my neighbour", "my neighbor",
                  "boundary", "deeds", "blew down", "blown down", "fell down", "repair",
                  "rotten", "rotted", "treat", "treating", "stain", "how tall", "how high",
                  # how deep a post goes is a how-to that says "how much", and the fence row in
                  # home.py answers it: "how much of a fence post goes in the ground" was
                  # quoted the price of a new fence
                  "how deep", "deep enough", "depth", "in the ground", "into the ground",
                  "buried", "foot down", "feet down",
                  # how much concrete a post hole takes is a quantity, and the materials row
                  # answers it: a fence post is not the price of a fence
                  "do i need", "will i need", "post hole", "posthole", "postcrete",
                  "cement", "concrete", "ballast", "mortar", "bags of"),
        "reply": "A new closeboard fence is usually £50 to £90 a metre supplied and fitted, so 20 "
                 "metres of garden is £1,000 to £1,800. Concrete posts and a trellis or a gate push "
                 "it up, and taking the old one away is often extra. Ask whether the price includes "
                 "the posts and the removal of the old panels, and check the height limit before "
                 "you order.",
    },
    "patio": {
        "names": ("patio", "patios", "block paving", "driveway"),
        "thing": "a patio or driveway",
        # "how much gravel do i need for a driveway" and "how much sand do i need for a patio" are
        # quantities, not prices: how much of it to buy is answered as a volume by the materials
        # row, and only the words of that ask stand this one down. "how much does a gravel
        # driveway cost" still gets the price, because it asks a price and not a quantity.
        "avoid": ("do i need", "will i need", "bags of", "tonnes of", "tons of", "cubic",
                  "how deep", "how thick",
                  # the materials for the base are a quantity question, and the sand-and-cement
                  # row answers it: "how much sand and cement for a patio base" was quoted the
                  # price of a patio laid
                  "how much sand", "sand and cement", "how much cement", "how much ballast",
                  "patio base", "base for a patio", "base for the patio", "sand base",
                  "sub base", "sub-base", "type 1", "type one", "bulk bag",
                  # how much of a mix it takes is a quantity too, asked without "do i need":
                  # "how much mortar for 20 square metres of block paving" was this price
                  "mortar", "mortar mix", "sharp sand", "building sand", "what mix",
                  "mix ratio", "what ratio"),
        "reply": "A patio is usually £60 to £120 a square metre laid, so a small 15 square metre "
                 "patio is £900 to £1,800, and block paving for a driveway £80 to £150 a square "
                 "metre. The base and the drainage are what separate a good job from a cheap one. "
                 "Ask what depth of sub-base they are laying, and whether the price includes the "
                 "skip and the sealing.",
    },
    "conservatory": {
        "names": ("conservatory", "conservatories", "orangery", "garden room"),
        "thing": "a conservatory",
        "reply": "A conservatory is usually £8,000 to £20,000 depending on size and whether it has "
                 "a solid roof, and an orangery with the same footprint is £20,000 to £40,000. A "
                 "solid roof and underfloor heating cost more but make the room usable all year. "
                 "Ask whether the price includes the foundations, the electrics and building "
                 "regulations sign-off, because those are the three that get left out of a quote.",
    },
    "loft-conversion": {
        "names": ("loft conversion", "loft", "attic conversion", "extension", "house extension"),
        "thing": "a loft conversion or extension",
        # A loft is also where the boiler is, so "the boiler is in the loft" puts the word in the
        # last turn and "is it worth getting someone out" then asked a builder's question. Asking
        # about a repair or a tradesman is not a build, so the job stands aside for it.
        "avoid": ("someone out", "someone in", "get someone", "call someone", "an engineer",
                  "engineer", "callout", "call out", "boiler", "hot water", "repaired",
                  "repair it", "broken", "isnt working", "is not working",
                  # insulation is a few hundred pounds, not a conversion: "loft insulation cost"
                  # was quoted £25,000 to £60,000
                  "insulate", "insulation", "lagging", "mineral wool", "loft insulation",
                  "board out", "boarding"),
        "reply": "A loft conversion is usually £25,000 to £60,000 depending on the type, and a "
                 "single-storey extension £1,800 to £2,500 a square metre. A dormer and a "
                 "bathroom in the roof are the two things that move it most, and structural "
                 "engineers, party wall agreements and building regulations are all extra. Ask "
                 "whether the quote is fixed, what it excludes, and who is managing the "
                 "inspections.",
    },
    "roof": {
        "names": ("roof", "roofs", "roofing", "roofer", "roofers", "re-roof", "reroof",
                  "roof repair", "roof leak", "roof leaks", "leaking roof", "roof tiles",
                  "ridge tiles", "flat roof", "felt roof", "gutter", "gutters"),
        "thing": "a roof repair",
        # "my car roof leaks" and a sunroof are the car's question, and a garage prices those
        "avoid": ("car", "cars", "van", "vans", "sunroof", "windscreen", "convertible",
                  "how do i", "how to", "myself", "clear the", "clearing", "unblock"),
        "reply": "A roofer is usually £200 to £300 a day, and the small jobs are priced whole: a "
                 "patch or a few slipped or broken tiles is £150 to £400, a flat roof on a garage "
                 "£1,500 to £3,000. A whole roof - a full re-roof or a new roof on a three-bed "
                 "semi - is £5,000 to £15,000, and scaffolding is £800 to £1,500 of that on its "
                 "own. Ask whether the quote includes the scaffolding, the disposal of the old "
                 "covering and a guarantee on the workmanship, and get three quotes on the same "
                 "written description of the job.",
    },
    "shed": {
        "names": ("shed", "summerhouse", "log cabin", "garden office"),
        "thing": "a shed",
        "reply": "A decent 6 by 8 foot shed is usually £400 to £900, and a garden office £3,000 to "
                 "£10,000. The base is the part people forget: a shed on grass or soil will never "
                 "sit square, so £100 to £200 on a paved or timber base is money well spent. Ask "
                 "whether the price includes the base, delivery and the treatment, and how thick "
                 "the timber is - thin boards are the cheap shed's secret.",
    },
    "passport": {
        "names": ("passport", "passports", "passport renewal", "new passport"),
        "thing": "a passport",
        # A government fee is not a range, so this row says what it is and warns about the
        # middlemen: the fee is the same wherever you apply, and the only part that moves is the
        # post-versus-online difference and the April increase.
        # "renew" and "apply" are not avoided any more: "how much does it cost to renew my
        # passport" was answered with the how-to card, because the verb that makes it a how-to
        # was standing this row down and taking the fee with it. `fence_how_to` reads the two
        # apart - a how-to with no price in the line stands this row down, a price keeps it.
        "fence_how_to": True,
        "avoid": ("expires", "expiry", "six months", "6 months", "lost", "stolen", "damaged",
                  "travel with", "valid", "photo", "track"),
        "reply": "An adult passport is about £95 and a child's about £62, done on gov.uk, and "
                 "about £12 more each if you post the paper form instead. Do it on gov.uk "
                 "itself: the websites that charge £20 to fill the same form in for you are "
                 "charging for a service the site gives away, and a Post Office check-and-send "
                 "is about £16 on top for checking the photo. The fee goes up each April, and "
                 "it usually takes about three weeks, longer in the summer.",
    },
    "driving-licence": {
        "names": ("driving licence", "driving license", "provisional licence",
                  "provisional license", "photocard licence"),
        "thing": "a driving licence",
        # same split as the passport: "how much does it cost to renew my licence" was the
        # how-to card, and the fee was lost with it
        "fence_how_to": True,
        "avoid": ("points", "banned", "revoked", "medical", "address", "change of address",
                  "lost", "stolen", "photo", "driving test", "lessons"),
        "reply": "A first provisional licence is £34 online, or £43 on the paper form, and "
                 "renewing the photocard is £14 online, or £17 on paper. The tests are separate: "
                 "about £23 for the theory and £62 for the practical, £75 at an evening or "
                 "weekend slot. Book all of it on gov.uk, and do the provisional first - you "
                 "cannot book a test without the number.",
    },
    "prescription": {
        "names": ("prescription", "prescriptions", "prescription charge",
                  "prescription charges", "nhs prescription",
                  # "how much is a prepayment certificate" is this row's question: it is the
                  # yearly way of paying for prescriptions, and the energy table was taking it
                  # on the word "prepayment".
                  "prepayment certificate", "prescription prepayment certificate",
                  "prescription prepayment", "prescription prepayment certificate", "ppc",
                  "prescriptions free", "are prescriptions free", "free prescriptions",
                  "prescription fee", "prescription fees", "prescription cost",
                  "prescription costs"),
        "thing": "a prescription",
        "diy": False,
        "shapes": ("prepayment", "prepayment certificate", "prescription prepayment",
                   "certificate", "how do i pay", "apply for", "ppc"),
        # Ordering a repeat is the repeat prescription card's question, and the pills are other
        # cards'. The bare "how do i" that used to be here took the certificate's own how-to
        # with it: "how do i get a prescription prepayment certificate" was answered with a
        # GP's two working days and a pharmacy order.
        "avoid": ("tablet", "tablets", "pill", "pills", "antibiotic", "antibiotics", "dose",
                  "side effect", "side effects", "refill", "repeat prescription", "repeat",
                  "order my", "order a", "ordering", "how do i order", "how do i get a repeat",
                  "how to order", "how do i reorder", "reorder", "ran out", "run out",
                  "has run out", "pharmacy", "chemist", "my dog", "my cat", "the vet",
                  "for the dog", "for my dog", "for the cat", "for my cat", "puppy", "kitten"),
        "reply": "A prescription in England is £9.90 an item, and it is free in Scotland, Wales "
                 "and Northern Ireland. Check the exemptions before you pay, because a lot of "
                 "people pay and should not: under 16, 16 to 18 in full-time education, over 60, "
                 "pregnant or with a baby under 12 months, or on a benefit, and some long-term "
                 "conditions are exempt. If you pay for more than about 12 items a year, a "
                 "prepayment certificate is about £33 for three months or £115 for a year and "
                 "covers everything on it. Get one on the NHS website or at a pharmacy counter, "
                 "and it starts the day you pay, so buy it before the next item rather than "
                 "after it.",
    },
    "speeding-fine": {
        "names": ("speeding fine", "speeding ticket", "speeding penalty", "speeding offence",
                  "speeding"),
        "thing": "a speeding fine",
        "avoid": ("how do i", "how to", "appeal", "points on my licence", "insurance",
                  "caught", "camera", "notice"),
        "reply": "A speeding ticket is usually £100 and three points, or a speed awareness "
                 "course instead at about £100 if you were not far over the limit and have not "
                 "done one recently. If it goes to court the fine is means-based and up to "
                 "£1,000, or £2,500 on a motorway, and the points can be more. Pay within the 28 "
                 "days and tell your insurer: the policy nearly always asks, and finding out "
                 "later costs more than the fine.",
    },
    "tool-hire": {
        # A hired tool is spoken as "hire a breaker", so every name here carries the hire: "how
        # much is a breaker" is the price of buying one, and a shop's day rate answers the wrong
        # question. The word "hire" is what makes the line this row's, and a hire shop is a price
        # by the day with a deposit behind it, which is what the reply says.
        "names": ("hire a breaker", "breaker hire", "hire a kango", "kango hire",
                  "hire a drill", "drill hire", "hire an sds drill", "sds drill hire",
                  "hire a hammer drill", "hire a ladder", "ladder hire",
                  "hire a step ladder", "hire a scaffold tower", "scaffold tower hire",
                  "tower hire", "hire a floor sander", "floor sander hire", "hire a sander",
                  "hire a carpet cleaner", "carpet cleaner hire",
                  "hire a wallpaper stripper", "hire a tile cutter", "tile cutter hire",
                  "hire a pressure washer", "pressure washer hire",
                  "hire a hedge trimmer", "tool hire", "hire shop", "hire a tool",
                  "hiring a tool", "hire tools", "hire some tools"),
        "thing": "a hired tool",
        "reply": "Most tools are £10 to £35 for the first day at a hire shop: a breaker or a big "
                 "drill £15 to £30, a step ladder £10 to £20, a carpet cleaner £20 to £35, a "
                 "floor sander £35 to £60 and a scaffold tower £40 to £80, and a weekend rate is "
                 "often the price of one day. The deposit, not the day rate, is the figure that "
                 "adds up at the counter, usually £50 to £200 and back when the tool comes back "
                 "clean, and a late return is charged as another day. Ask two shops for the day "
                 "rate with the damage waiver included before you book.",
    },
    "photographer": {
        "names": ("photographer", "wedding photographer", "photo shoot"),
        "thing": "a photographer",
        "reply": "A wedding photographer is usually £1,000 to £2,500 for the day, and a family "
                 "shoot £150 to £400 including some prints. The package matters more than the "
                 "day rate: ask how many hours, how many edited images, and whether you get the "
                 "files to print yourself.",
    },
}

# What people call the money they are asking about, on top of the job's own names.
ENTRIES = [
    # A job's price is also asked by naming the way it is paid rather than a price word:
    # "how do i get a prescription prepayment certificate" has no "how much" in it, and the
    # name of the certificate alone was one part short of the row.
    entry("cost-" + key,
          (data["names"],
           _COST + (_A_VISIT_FEE if key in _VISIT_FEE_JOBS else ()))
          + ((data["shapes"],) if data.get("shapes") else ()),
          data["reply"],
          # the how-to of the job is the DIY answer, and a comparison is the shopping one. A job
          # whose how-to IS the price - a prepayment certificate is bought at a counter for a
          # set sum - sets diy to False and fences its own order shapes instead.
          avoid=(_DIY if data.get("diy", True) else ())
          + ("cheaper at", "or a", "instead of", "which is better", "best buy")
          + data.get("avoid", ()),
          ask=data.get("ask", ()),
          # a name that is a part of an appliance is the appliance's question: "how much does a
          # heat pump dryer cost" is a dryer's price, and the appliance's own row answers it
          # names is bound per row: a lambda inside this comprehension that read `data` would see
          # the last job in the table, not its own.
          guard=lambda understood, names=data["names"], fence=data.get("fence_how_to", False): (
              _not_a_steps_ask(understood)
              and not (fence and _a_steps_ask_with_no_price(understood))
              and not the_appliance_swallows_the_name(understood, names)),
          bias=data.get("bias", 1))
    for key, data in JOBS.items()
]

# A fixture that nobody owns is still a trade's job. The garage row stands down on the names of
# the fixtures, and a sink was the one with no card of its own, so "how much does it cost to fix a
# sink" fell through to the buoyancy card off the word "sinks" - a lesson in density instead of a
# price. The repair shape is what is keyed here, not the fixture alone: a new sink is a shop
# question, and a blocked or dripping one has its own how-to rows.
ENTRIES.append(entry("cost-plumber-sink",
      (("sink", "sinks", "fix a sink", "repair a sink", "sink repair", "sink leak",
        "a leaking sink", "fit a sink", "fitting a sink", "install a sink", "a new sink"),
       _COST + ("fix", "fixes", "repair", "repairs", "repairing", "replace", "replacing", "fit",
                "fitting", "install", "installing")),
      JOBS["plumber"]["reply"],
      # the how-to rows keep their own lines, and a shop question about the bowl itself is not a
      # call-out: "how much is a sink unit" is a price in a catalogue. Fitting is left in, because
      # "how much to fit a new sink" is a plumber's job and the price is the answer to it either way
      avoid=_DIY + ("basin", "sink unit", "sink waste", "sink plug", "buy a sink", "cheapest",
                    "best buy", "blocked", "blockage", "unblock", "smell", "smells", "clean",
                    "cleaning", "drain", "drains", "tap", "taps"),
      bias=2))


# The price of the ordinary food shop. "How much is a pint of milk" and "how much is a block of
# cheese" are the same question as "how much does a plumber charge", and on their own words they
# reached a punt ("Prices move too fast for me to know") or a different question entirely: the
# bread ratio for "how much is a loaf of bread", 75 to 100g a person for "how much is a bag of
# pasta", 30g a portion for "how much is a block of cheese", the 400mg caffeine limit for "how
# much is a cup of coffee".
#
# The two questions wear the same first words - "how much is a loaf of bread" is a price and "how
# much bread for four people" is an amount - so the guard is the price shape itself: "how much
# is/are/does" or the words cost and price, and nothing about portions, grams, calories or people.
# With that in front, a bare "milk" or "bread" is safe as a name, which is how the whole shop gets
# covered in one table.
# "how much is a loaf" is a price, and "how much does a loaf need to rise" is the bread ratio, so
# the how-much-does shape only counts when it carries the word cost with it.
_PRICE_SHAPE = re.compile(
    r"\bhow\s+much\s+(?:is|are|was|were|for|would|will)\b"
    r"|\b(?:cost|costs|costing|price|prices|priced)\b", re.IGNORECASE)
_AMOUNT_SHAPE = re.compile(
    r"\bhow\s+many\b|\bper\s+(?:person|head|serving|portion|adult|child|kg|kilo)\b"
    r"|\bportions?\b|\bgrams?\b|\bcalories\b|\bprotein\b|\bper\s+day\b|\ba\s+day\b"
    r"|\bfor\s+(?:\d+|two|three|four|five|six|seven|eight)\b|\bpeople\b|\bserves?\b"
    r"|\bhow\s+long\b|\bkeep\b|\bfreez(?:e|es|ing)\b|\bleft\s?overs?\b"
    # an amount is "how much should i use/eat/make"; "how much should i pay for a chicken" is a price
    r"|\bshould\s+i\s+(?:use|eat|have|drink|cook|add|give|feed|take|put|make|buy)\b"
    r"|\b(?:should|shall)\s+(?:i|we)\s+(?:use|eat|have|drink|cook|add|give|feed|take|put|make)\b"
    # An ingredient's name is not a shop line when the line names something to grow or to cook:
    # "how much is a tomato plant" is a tomato plant and "how much are seed potatoes" is seed
    # potatoes for planting, while a soup, a pie or a sandwich is a dish, not the price of what
    # goes in it.
    r"|\bplant|\bplants|\bseed\b|\bseeds|\bseedlings?|\bgrow|\bgrows|\bgrowing|\bgrew\b"
    r"|\bgrown\b|\bvariet(?:y|ies)|\bharvest|\bsow\b|\bsow(?:ed|ing)\b|\bplanting\b"
    r"|\bsoup\b|\bsoups\b|\bpie\b|\bpies\b|\bpuddings?\b|\bsandwich|\btoast\b"
    r"|\bjacket\b|\bmash\b|\bmashed\b|\bcurry|\bcasseroles?\b|\bstew|\broast\b"
    r"|\bjar\b|\bjars\b|\bsalad\b|\bbake\b|\bbaked\b|\btopping|\bfilling|\bpizza"
    r"|\bcake\b|\bbiscuits?\b|\bbread\b|\bpot\b|\bpots\b", re.IGNORECASE)


def _a_price_for_the_shop(understood):
    """True when the line asks what a grocery costs, and not how much of it to use."""
    if not isinstance(understood, dict):
        return False
    line = (understood.get("clean") or understood.get("text") or "").lower()
    if not line or _AMOUNT_SHAPE.search(line):
        return False
    return bool(_PRICE_SHAPE.search(line))


# One line of data an item: what people call it and the price. Ranges, never a single figure.
# The loaf, the eggs and the pint of milk are not here: main's own everyday-price table answers
# those three already (a supermarket loaf £1.20 to £1.60, six free-range eggs £1.50 to £2.20,
# milk about 70p a pint), and a second table for the same shopping is the copy the lane forbids.
# What is here is the rest of an ordinary basket, which was a punt or a portion card.
GROCERIES = {
    "water": {
        "names": ("bottle of water", "bottled water", "pack of water", "case of water",
                  "water in a shop", "still water", "sparkling water"),
        "reply": "A 500ml bottle of water is about £1 in a shop and £2 or more at a station, "
                 "while a 6-pack of 1.5 litre bottles is about £3 to £4 in a supermarket. Tap "
                 "water is the same stuff and costs nothing, so the bottle is for the day out.",
    },
    "cheese": {
        "names": ("cheese", "block of cheese", "block of cheddar", "cheddar", "400g of cheese",
                  "packet of cheese"),
        "reply": "A 400g block of cheddar is about £3.50 to £5, and the same weight of a named "
                 "farmhouse one £4 to £6. Mature costs a little more than mild, and the deli "
                 "counter is dearer than the block.",
    },
    "butter": {
        "names": ("butter", "block of butter", "packet of butter", "tub of butter"),
        "reply": "A 250g block of butter is about £2.20 to £3, and a tub of spread about £1.50. "
                 "Own-brand butter is the cheapest, and it freezes well, so buy it when it is on "
                 "offer.",
    },
    "pasta": {
        "names": ("pasta", "bag of pasta", "packet of pasta", "spaghetti", "penne"),
        "reply": "A 500g bag of dried pasta is about 75p to £1.50, and a fresh one £2 to £3. "
                 "Dried is a fifth of the price a portion, and the shape does not change the "
                 "price much.",
    },
    "rice": {
        "names": ("rice", "bag of rice", "kilo of rice", "basmati", "long grain rice"),
        "reply": "A kilo of long-grain rice is about £1 to £2.50 and a kilo of basmati £2 to "
                 "£3.50. It keeps for months in a cupboard, so the bigger bag is usually the "
                 "better buy.",
    },
    "bacon": {
        "names": ("bacon", "pack of bacon", "packet of bacon", "rashers", "smoked bacon"),
        "reply": "A 300g pack of bacon is about £2.50 to £4. Dry-cured costs more than the kind "
                 "that is pumped with water, which shrinks in the pan, and the 2-for deals are "
                 "usually the cheapest way to buy it.",
    },
    "salmon": {
        "names": ("salmon", "salmon fillets", "side of salmon", "piece of salmon"),
        "reply": "Two salmon fillets are about £5 to £7, and a whole side £15 to £25. The frozen "
                 "fillets are often half the price of the fresh counter for the same fish.",
    },
    "bananas": {
        "names": ("bananas", "banana", "bunch of bananas"),
        "reply": "Bananas are about 15p to 25p each, so a bunch of five is roughly £1. Loose ones "
                 "are cheaper than a pre-packed bag, and the ripe ones on the reduce shelf are "
                 "the bargain.",
    },
    "apples": {
        "names": ("apples", "apple", "bag of apples"),
        "reply": "Six apples are about £1.50 to £2.50 and a kilo about £2. Loose ones let you "
                 "pick the size, and a bag of the smaller ones is usually the cheapest way.",
    },
    "tomatoes": {
        "names": ("tomatoes", "tomato", "pack of tomatoes", "punnet of tomatoes", "cherry tomatoes"),
        "reply": "A 400g pack of salad tomatoes is about £1 to £2, and a punnet of cherry ones "
                 "£1.50 to £2.50. Loose ones are usually cheaper than a punnet, and in August "
                 "they are half the winter price.",
    },
    "mince": {
        "names": ("mince", "beef mince", "pack of mince", "minced beef"),
        "reply": "500g of beef mince is about £4 to £6, with the 5% fat one a pound or two more "
                 "than the 20%. Turkey and pork mince are cheaper, and a bigger pack is usually "
                 "the better price a kilo.",
    },
    "sausages": {
        "names": ("sausages", "sausage", "pack of sausages", "pork sausages"),
        "reply": "Six to eight sausages are about £2.50 to £4, and a butcher's £4 to £6. The "
                 "cheapest are mostly rusk and water, so read the meat percentage on the pack.",
    },
    "cereal": {
        "names": ("cereal", "box of cereal", "cornflakes", "box of cornflakes", "muesli"),
        "reply": "A box of cereal is about £2 to £3.50, and the shop's own version of a branded "
                 "one about half the price. A big bag of own-brand flakes is the cheapest "
                 "breakfast there is a bowl.",
    },
    "yoghurt": {
        "names": ("yoghurt", "yogurt", "pot of yoghurt", "tub of yoghurt", "greek yoghurt"),
        "reply": "A four-pack of yoghurt is about £1.50 to £2.50, and a 1kg tub £2 to £3, which "
                 "is much cheaper a portion. Greek-style costs more than natural, and the big "
                 "tub is the one to buy if you eat it every day.",
    },
    "peas": {
        "names": ("peas", "frozen peas", "bag of peas", "kilo of peas"),
        "reply": "A kilo of frozen peas is about £1.50 to £2 and lasts months. Fresh peas in "
                 "season are sweeter but cost three or four times as much for a much smaller "
                 "bag.",
    },
}

ENTRIES += [
    entry("shop-" + key,
          (data["names"], _PRICE),
          data["reply"],
          # a portion, a recipe and a diet question are the other half of these lines
          avoid=("per person", "per head", "portion", "portions", "recipe", "recipes",
                 "to make", "to bake", "how to make", "how do i make", "from scratch",
                 # "how much is too much" carried the milk from the turn before and was answered
                 # with the price of a pint; "how much is a splash of milk" is a measure
                 "too much", "splash", "splash of", "a dash", "dash of", "a drop", "drop of",
                 "glug", "a bit", "how much is left", "left over",
                 # "and how much for a bigger loaf" came after the bread ratio: same words, and
                 # the amount is what a bigger loaf needs, not what it costs in a shop
                 "bigger", "larger", "smaller",
                 "calories", "protein", "how many", "a day", "substitute", "instead of",
                 "allergy", "allergic", "baby", "toddler", "freeze", "freezer", "defrost"),
          ask=("how much", "cost", "costs", "price", "prices", "much does", "much is",
               "much are", "much for"),
          bias=2,
          guard=_a_price_for_the_shop)
    for key, data in GROCERIES.items()
]

# --------------------------------------------------------------- the other question about a job
# A job is asked two ways, and they want different halves of the same knowledge: "how much does an
# MOT cost" wants the price, "how long does an MOT take" wants the clock. Only the price had a
# table, so a how-long line either matched nothing and fell to whatever card happened to carry the
# job's name (the boiler service card answered "how long does a house survey take") or was told
# what the job covers instead of how long it takes ("how long does an MOT take" listed the test).
#
# This is the same table idea as JOBS: a job, the words people use for it, and the duration, so a
# new job is one line of data. A row needs the job *and* the time it is asked by, which is what
# keeps "how much does an MOT cost" on the price row and "when is my MOT due" on the row that
# reads the date. The reply leads with the time, because that is the question.
#
# The figures are the usual ones in the UK, said as a range, with the thing that makes them longer.
# They are not promises: a garage, a surgery and a house are all different, so each says what
# moves it rather than a single exact number.
# A length of time, not a wait: "how soon can i see a dentist" asks when the next slot is and
# "how quickly can i get an mot" asks how booked up they are, and neither is answered by saying
# the job takes twenty minutes. Those two lines keep the answer they had.
_TIME = ("how long", "how many hours", "how much time", "long does", "long will",
         "hours does", "minutes does", "how many days", "how many minutes")

# "How long before I ring the dentist" and "how long should I leave it" ask when to act, not how
# long the visit runs: "A check-up is about 20 minutes" answered half of a line about a tooth
# that needed ringing about. The length rows all stand down for a wait, because the wait belongs
# to the symptom or the slot and none of these jobs can answer it.
_A_WAIT = ("how long before", "how long after", "how long till", "how long until",
           "how long should i leave", "how long do i leave", "how long to wait",
           "how long do i wait", "should i wait", "leave it before", "before should i",
           # The wait is the queue for the slot, and people put words in between: "how long do i
           # have to wait", "how long will i have to wait", "how long is the wait", and the list
           # itself, "how long is the waiting list for a physio". Every one of these was answered
           # with the length of the visit.
           "how long do i have to wait", "how long will i have to wait",
           "how long will we have to wait", "how long do you have to wait",
           "have to wait", "how long is the wait", "how long the wait", "how long a wait",
           "the wait for", "wait to see", "waiting list", "how long would i wait",
           "how long is the waiting")

# "How long have i had the boiler now" is the age of the thing the person already owns, not the
# length of the job: the boiler-service row answered it with "about an hour", which is the visit,
# and that line is on the deck. The perfect tense with the person in it turns a how-long into a
# possession, and a job cannot be owned, so every job row stands down for it.
# The phrases below are plain substrings, not regexes: the share of a line that makes it a
# possession is "how long have/has <who>", and the thing owned comes after. So the person is
# spelled out ("how long have i had", "how long has my", "how long have these") rather than the
# shape, which is the same trade every other avoid list in this file makes.
A_AGE_OWNED = ("how long have i had", "how long have i been", "how long have i owned",
               "how long have i kept", "how long have you had", "how long have you been",
               "how long have you owned", "how long have you kept", "how long have we had",
               "how long have we been", "how long have we kept", "how long have they had",
               "how long have they been", "how long has it been", "how long has he had",
               "how long has she had", "how long did i have", "how long did you have",
               "how long has my", "how long has our", "how long has this", "how long has the",
               "how long has that", "how long has she been", "how long has he been",
               "how long have my", "how long have our", "how long have these",
               "how long have those", "how long have the")

# Training for the job is the other length: "how long does vet school take" was five years and is
# now a fifteen-minute consultation, and "how long does it take to train as a physio" the same.
# The bare word for a job is what makes it reachable, so the row says which way it is not asked.
_A_CAREER = ("school", "vet school", "med school", "training", "train", "trained", "degree",
             "study", "studying", "university", "college", "qualify", "qualified", "qualifying",
             "become", "becoming", "career", "get into", "to be a", "how do i", "myself")

# The cars domain holds these rows, and its entries all turn a bicycle away: a bike shop services
# a bike, and the bike domain answers that. A motorbike does need an MOT, and it is the bike
# domain's MOT question, so the same words stand this table's car rows down.
_NOT_A_CAR = ("bike", "bikes", "bicycle", "bicycles", "cycling", "cyclist", "motorbike",
              "motorbikes", "motorcycle", "motorcycles", "scooter", "scooters")

JOB_TIMES = {
    "dentist": {
        "names": ("dentist appointment", "dentist appointments", "dental appointment",
                  "check up at the dentist", "dentist check up", "dentist checkup",
                  "appointment at the dentist", "dentist", "dentists",
                  # "how long does a dentist take" went to the register-with-a-practice card,
                  # which keys the verb "taking": the job and the verb together are this row
                  "dentist take", "dentist takes", "dentist taking"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("dentist", "dental"),
        # "how long does a dentist appointment take" was told how to register with a practice.
        "reply": "A check-up is about 20 minutes. A filling is 30 to 45 minutes, and a crown or a "
                 "root canal is usually one longer visit or two, so book the morning for one of "
                 "those and do not plan anything straight after.",
        "bias": 1,
        "avoid": ("register", "registering", "find a dentist", "nhs dentist", "emergency",
                  "pain", "toothache", "tooth hurts", "cost", "costs", "much", "price", "free",
                  "brace", "braces", "implant", "child", "children", "baby", "become",
                  "training", "degree", "study", "how do i", "myself"),
    },
    "eye-test": {
        "names": ("eye test", "eye tests", "eye exam", "appointment at the optician",
                  "optician appointment"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("eye test"),
        "reply": "An eye test is about 20 to 30 minutes, and longer if you are choosing glasses "
                 "afterwards. Say at the start if you drive or use a screen all day, because the "
                 "test and the prescription are read with that in mind.",
        # a prescription is good for a year or two, and that length is a different answer
        "avoid": ("cost", "costs", "much", "price", "free", "glasses", "contact lens",
                  "contacts", "child", "children", "baby", "how do i", "myself", "valid",
                  "good for", "prescription", "last", "lasts"),
    },
    "gp-appointment": {
        "names": ("gp appointment", "doctor appointment", "doctor's appointment",
                  "appointment with the doctor", "appointment with a doctor", "see the doctor",
                  "see a doctor"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("gp", "doctor"),
        "reply": "A standard GP appointment is 10 minutes, so it is worth naming the one problem "
                 "that matters most and what you need from it. If there are several things, say "
                 "so when you book and ask for a double slot rather than trying to fit them in.",
        "avoid": ("register", "registering", "find a doctor", "out of hours", "emergency",
                  "urgent", "999", "111", "cost", "costs", "much", "price", "how do i",
                  "myself", "letter", "fit note", "sick note",
                  # a referral and a wait for a slot are the other length, and neither is this
                  "referral", "referred", "refer", "waiting", "wait", "available", "booking",
                  "book", "to see", "get seen", "appointment come through", "hear back"),
    },
    "physio": {
        "names": ("physio appointment", "physiotherapy appointment", "physio session",
                  "physiotherapy session", "appointment with the physio",
                  "appointment with a physio", "see the physio", "see a physio"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("physio", "physiotherapy"),
        "reply": "A first physiotherapy appointment is usually 30 to 45 minutes, because it "
                 "starts with the history and an examination, and the follow-ups are 20 to 30. "
                 "Ask what the plan is and how many sessions they expect before you pay for a "
                 "block, and whether you need to bring shorts or a vest to move in.",
        "avoid": ("cost", "costs", "much", "price", "nhs", "refer", "referred", "referral",
                  "how do i", "myself", "exercises", "worth",
                  # how long it takes to work is not how long a session runs
                  "to work", "before it works", "start working", "helps", "help", "recover",
                  "recovery", "sessions will i need", "how many sessions", "how many"),
    },
    "haircut": {
        "names": ("haircut", "hair cut", "cut my hair", "hairdresser", "hairdressers", "barber",
                  "hair appointment", "hair appointments", "salon appointment", "highlights",
                  "colour my hair", "dye my hair"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("haircut"),
        "reply": "A cut is 30 to 45 minutes; colour, highlights or a restyle is one and a half to "
                 "two and a half hours. If it is your first colour at a salon they will want a "
                 "patch test 48 hours before, so ring ahead and get that done.",
        # "how long does a haircut last" is how long it stays looking right, not how long the
        # appointment is, and it is asked in weeks rather than minutes.
        "avoid": ("cost", "costs", "much", "price", "style", "which", "child", "children",
                  "baby", "myself", "how do i", "last", "lasts", "lasted", "grow out",
                  "how often"),
    },
    "house-survey": {
        "names": ("house survey", "home survey", "building survey", "homebuyer report",
                  "homebuyers report", "structural survey", "surveyor", "survey"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("survey"),
        "reply": "A valuation is 20 to 30 minutes on site, a homebuyer's report two to three "
                 "hours, and a full building survey four to six. The written report usually "
                 "follows within a few days, so ask when you will have it before you book, "
                 "because your lender and your solicitor may both be waiting on it.",
        "avoid": ("garden", "soil", "land", "cost", "costs", "much", "price", "quote",
                  "choose", "find a surveyor", "how do i", "myself", "satisfaction"),
    },
    "vet": {
        "names": ("vet appointment", "appointment at the vet", "appointment with the vet",
                  "vet visit", "see the vet",
                  # "how long does the vet take" was read as the career: the job and the verb
                  # together are this row
                  "vet take", "vet takes", "vet taking"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("vet"),
        "reply": "A routine consultation is 15 to 20 minutes; a procedure, a scan or a dental is "
                 "longer and the practice will tell you how long when you book. Ask for an "
                 "estimate before they start, and for the out-of-hours number on the way out.",
        "avoid": ("cost", "costs", "much", "price", "quote", "insurance", "put down", "euthan",
                  "how do i", "myself"),
    },
    "tyres": {
        "names": ("tyre fitting", "fit tyres", "fit a tyre", "fit two tyres", "fitting tyres",
                  "new tyres", "puncture repair", "puncture", "change a tyre", "change my tyres",
                  "tyre", "tyres"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("tyre", "tyres"),
        "reply": "Two tyres take about 30 to 45 minutes, and a puncture repair 20 to 30. Most "
                 "places take walk-ins, but ring first if you need a particular tyre, and check "
                 "the pressures again a day or two later.",
        # "how long do tyres last" is the lifespan card and is right, so the words that make it
        # that question stand this row down; the fitting time is what is left.
        "avoid": ("last", "lasts", "lasted", "life", "wear", "worn", "miles", "tread",
                  "pressure", "which", "winter", "snow", "best", "cheap", "cost", "costs",
                  "much", "price", "how do i", "myself", "spare") + _NOT_A_CAR,
    },
    "car-service": {
        "names": ("car service", "service my car", "service the car", "car servicing",
                  "full service", "major service"),
        # The word people type for this job, with no "appointment" or "session" after it.
        "bare": ("car service"),
        "reply": "A car service is usually two to three hours for an interim or a full service, "
                 "and a major service with plugs and filters can take most of the day. Ask when "
                 "you book whether they keep the car or you wait, and whether the price includes "
                 "the MOT if it is due.",
        "avoid": ("cost", "costs", "much", "price", "quote", "which", "worth", "due",
                  "how do i", "myself") + _NOT_A_CAR,
    },
}

# The row is built where the job is at home, because a domain's entries have to answer the topic
# the line is read as: the MOT row sits in cars, the boiler rows in home, the dentist's in health.
# `time_entries` is how each of those domains asks for its slice, with the same `entry` the price
# rows use, so the matching and the stand-downs are one set of code and a new job is one line of
# data. The time row and the price row share the job's names and are told apart by the ask: one
# needs a price word, this one needs a how-long.
def time_entries(*keys):
    """The how-long rows for the jobs named, to be appended to a domain's ENTRIES."""
    rows = []
    for key in keys:
        data = JOB_TIMES[key]
        # The bare word for the job is in the same list as the phrases: "how long does physio
        # take" and "how long does a gp take" name the job and ask for its length, and the row
        # was reading past them to a general how-long card because only "physio session" and
        # "gp appointment" were listed. One word per job, so a new job gets this for free.
        bare = data.get("bare", ())
        names = data["names"] + ((bare,) if isinstance(bare, str) else tuple(bare))
        rows.append(entry("time-" + key,
                          (names, _TIME),
                          data["reply"],
                          avoid=_A_WAIT + _A_CAREER + A_AGE_OWNED + _DIY + data.get("avoid", ()),
                          # above the job's price row, which is where the other half of the
                          # question lives: "how long does it take to fit tyres" reached the
                          # tyre price row because both hold the job's name and the price row
                          # was read first. The length ask is this row's gate, so the row that
                          # needs the how-long is the one that answers it.
                          bias=max(data.get("bias", 0), 3)))
    return rows

# The cost of a job is asked in the home, in the shops and about money, and the arbiter uses this
# to know answers is the specialist for those lines.
ANSWERS = ("home-and-diy", "shopping", "money", "pets", "garden-and-plants")


# ---------------------------------------------------------------- a sum a month, and an opinion
# "Is 40 a month for a gym too much" is not a question about the gym: it is a question about the
# money, and the gym's own card (injuries, what to do there) answers the thing instead. The same
# line comes for a phone, a broadband deal, a subscription, a nursery: a sum of money, the period
# it is for, and an opinion word ("too much", "a rip off", "worth it", "about right").
#
# What a friend says first is the verdict, and then the two things that turn it into one: what the
# sum comes to over a year, and what people usually pay for that thing. The table is the usual
# monthly range in the UK, always a range, because a city, a chain and a contract all move it.
# Each row also carries the test that settles it, because "is it worth it" is nearly always a
# question about the cost per use - so the row that says "per visit" is the one that knows it.
SUBSCRIPTIONS = {
    "gym": {
        "names": ("gym", "gyms", "gym membership", "leisure centre", "leisure center"),
        "thing": "a gym",
        "span": (20, 45),
        # What a single visit costs paid as you go, which is the figure a fee is judged against
        # when the person says how often they go.
        "visit": (6, 12),
        "uses": "A gym is only worth it per visit: at eight visits a month that is {eighth} a "
                "visit, at four it is {quarter}.",
        "advice": "Watch the joining fee and the 12-month contract, and ask them to drop the "
                  "joining fee - a council gym or a pay-as-you-go swim usually beats the chain.",
    },
    "phone": {
        "names": ("phone", "mobile", "sim", "sim only", "sim-only", "handset", "contract",
                  "iphone", "smartphone"),
        "thing": "a phone deal",
        "span": (5, 30),
        "uses": "A SIM-only deal is £5 to £25 a month and a contract that includes the handset is "
                "£20 to £45, so it is only the handset part that is dear.",
        "advice": "Buying the phone outright and taking a cheap SIM usually costs less over two "
                  "years, and you are not tied in when the next one comes out.",
    },
    "broadband": {
        "names": ("broadband", "fibre", "internet", "wifi", "wi-fi"),
        "thing": "a broadband deal",
        "span": (25, 40),
        "uses": "There is no per-use test here, so the thing to compare is the speed you actually "
                "use: a 100Mb line is enough for two people streaming.",
        "advice": "The price almost always goes up out of contract, so diarise the end date - the "
                  "retention price on a call is usually £5 to £10 a month less than the renewal.",
    },
    "tv": {
        "names": ("netflix", "streaming", "sky", "now tv", "disney", "prime", "tv package",
                  "tv licence", "subscription"),
        "thing": "a TV service",
        "span": (6, 20),
        "uses": "Two services at once is where this gets expensive, so count how many you pay for "
                "and when you last watched each.",
        "advice": "Pick one at a time and cancel the one you are not watching: they all let you "
                  "restart it in a month, and the yearly price of two is the price of a holiday.",
    },
    "magazine": {
        "names": ("magazine", "magazines", "newspaper", "paper", "journal"),
        "thing": "a magazine",
        "span": (4, 12),
        "uses": "The issue price is £4 to £7 in a shop, so a monthly one is a small saving.",
        "advice": "The library app gives most UK magazines away free with a library card, which is "
                  "the cheapest way to read them.",
    },
    # A bill per month is the same question as a subscription per month, and it was the one sum
    # people ask about most: "i pay 250 a month in electricity is that a lot" was answered
    # "Thanks for telling me - I'm here if you want to dig into any of that". The ranges are the
    # yearly average for a typical home in the UK, which is what a direct debit is set from.
    "electricity": {
        "names": ("electricity", "electric bill", "electricity bill", "electric", "power bill",
                  "electricity prices"),
        "thing": "electricity for a typical home",
        "span": (60, 120),
        "uses": "That range is a two- or three-bedroom home on a standard tariff: a one-bed flat "
                "can be half of it, and electric heating or charging a car at home doubles it.",
        "advice": "The standing charge is fixed whatever you use, so the levers are the unit rate "
                  "and what runs the heat: a smart meter display shows what each appliance costs, "
                  "and a timer on the immersion is usually the first saving.",
    },
    "gas": {
        "names": ("gas bill", "gas", "gas prices", "heating bill", "gas heating"),
        "thing": "gas for a typical home",
        "span": (45, 100),
        "uses": "Gas is heating and hot water, so it swings with the weather: much more in "
                "January and almost nothing in July, which is what the yearly average smooths out.",
        "advice": "Turning the boiler's flow temperature down to 55 to 60C, and the room "
                  "thermostat down by one degree, are the two cheapest savings.",
    },
    "energy": {
        "names": ("dual fuel", "energy bill", "energy bills", "energy", "gas and electric",
                  "gas and electricity"),
        "thing": "gas and electricity together",
        "span": (110, 210),
        "uses": "That is both fuels averaged over the year, which is what a direct debit is "
                "spread across.",
        "advice": "Check the unit rate against the price cap and the standing charge against the "
                  "rest, take a fixed deal when the cap is about to rise, and read the meter on "
                  "the day you switch.",
    },
    # Childcare is not a row here: a nursery place is priced per day and part-time places are a
    # fraction of a full-time one, so the range the bot already has for it is the better card.
    "class": {
        "names": ("class", "classes", "lesson", "lessons", "swimming lessons", "yoga", "pilates",
                  "dance", "tutor", "tutoring", "club"),
        "thing": "a class",
        "span": (8, 30),
        "visit": (8, 15),
        "uses": "At four classes a month that is {quarter} a class, at eight it is {eighth}, and "
                "a block of ten is usually cheaper than ten singles.",
        "advice": "A leisure centre class is a good deal cheaper than a studio one, and the first "
                  "session is usually free, so try it before you pay for a term.",
    },
}

# A slash is how a price is written, not how it is said: "£40/month for yoga classes" was a punt
# because the period pattern only knew the words. Same for "p/m" and "40 / mo".
_PERIODS = (
    (re.compile(r"\b(?:a|per|each|every|one)\s*month\b|\bmonthly\b|\bpcm\b|\bp/m\b|"
                r"/\s*(?:mo|mth|month)\b", re.I), 12.0),
    (re.compile(r"\b(?:a|per|each|every)\s*(?:week|wk)\b|\bweekly\b", re.I), 52.0),
    (re.compile(r"\b(?:a|per|each|every)\s*year\b|\bannual(?:ly)?\b|\bpa\b|\bp\.a\.", re.I), 1.0),
    (re.compile(r"\b(?:a|per|each|every)\s*(?:day|night)\b|\bdaily\b", re.I), 365.0),
)
_SUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(k\b)?", re.I)
# "Too much" is a question about the price and "worth it" is a question about the value, and the
# verdict words differ: the same £8 answered "No, that is normal" reads as a shrug when the person
# asked whether it was worth paying. "About right" asks for a yes, and gets one.
_TOO_MUCH = re.compile(
    r"\b(?:too much|too expensive|too dear|rip[\s-]?off|ripped off|over the odds|steep|"
    r"overpriced|bad value|a lot of money|a lot|that much|expensive)\b", re.I)
_WORTH_IT = re.compile(r"\b(?:worth it|worth paying|good value|value for money)\b", re.I)
_ABOUT_RIGHT = re.compile(
    # "is 40 a month for a gym normal" and "is that about the going rate" are the same yes/no as
    # "about right", and both were a punt ("I don't know enough to answer that honestly").
    r"\b(?:about right|sound right|sounds right|reasonable|fair price|normal|"
    r"the going rate|about the rate|ok|okay|fair)\b", re.I)
# A fee the state sets is the same for everybody, so a monthly range would be a false verdict on
# it: "is 15 a month for a tv licence too much" was answered from the TV-service row ("two
# services at once is where this gets expensive"), which is not what a licence is. The row stands
# aside and the licence's own card answers.
_FIXED_FEE = re.compile(
    r"\b(?:licence|license|council tax|road tax|car tax|vat|duty|fine|penalty|mot|prescription|"
    r"passport|stamp duty|tuition|fee for|application fee|standing charge|court fee)\b", re.I)
# Words for the paying, not for the thing paid for: a line that names one of these and a thing
# is about the thing ("a magazine subscription" is a magazine), and these never outrank it.
_JUST_A_PAYMENT = frozenset(("subscription", "subscriptions", "contract", "package", "deal",
                             "bill", "bills"))
# "is 300 a month for an electric car too much" is a car on finance, not a bill: the thing that
# runs on electricity is priced like the thing it is, so those lines are not the energy rows'.
# The ranges below are UK ones, so a sum in another currency gets no verdict from them: "is $50 a
# month for a gym too much" was answered "£50 a month is £600 a year", which is a different number
# in a different country.
_NOT_POUNDS = re.compile(r"[$]|\bdollars?\b|\bbucks\b|\beuros?\b|\u20ac", re.I)
# A day or a week of a single occasion is that occasion's own price, not a sum for the month:
# "is 8 a week for a swimming lesson too much" is £8 a lesson against £8 to £15 a visit, and
# comparing it as £35 a month called a cheap lesson too much. A week of the thing itself is still
# a month's question - "is 25 a week for a gym too much" is £108 a month and far too much - so the
# stand-down needs both the short period and a word for one occasion.
_SHORT_PERIOD = re.compile(
    r"\b(?:a|per|each|every)\s*(?:day|night|week|wk)\b|\bdaily\b|\bweekly\b|"
    r"/\s*(?:day|wk|week)\b|\bp/w\b", re.I)
_ONE_OCCASION = re.compile(
    r"\b(?:lesson|lessons|class|classes|session|sessions|swim|swims|visit|visits|"
    r"appointment|appointments|treatment|treatments|haircut|haircuts|massage|massages|"
    r"clean|cleans|round of golf|court booking)\b", re.I)
_NOT_A_BILL = re.compile(
    r"\b(?:electric|electrical) (?:car|vehicle|bike|scooter|van|blanket|shower|toothbrush|"
    r"razor|guitar|heater|fire)\b|\bev\b|\be-?bike\b", re.I)
# A line that says how often the person uses the thing has already asked the better question, and
# the cost-per-use card answers it with their own figure: "im paying 40 a month for the gym and i
# go twice" wants "that is £20 a session", not a verdict on the membership fee.
_COUNT = {"once": 1, "twice": 2, "three times": 3, "four times": 4, "five times": 5,
          "six times": 6, "seven times": 7}
_USES_IT = re.compile(
    r"\b(once|twice|three times|four times|five times|six times|seven times|\d+ times)\b"
    r"(?:\s*(?:a|per|each|every|a week|a month)\s*(week|month|day|fortnight)\b)?", re.I)


# "i never use it" is the same sum with the honest answer on the other side: the fee is not
# whether it is normal, it is £480 a year for nothing. Only the rows that price a visit say this,
# because it is the visit that is not happening.
_NOT_GOING = re.compile(
    r"\bnever (?:go|goes|use|used|been|attend|make it)\b|\bdon'?t (?:go|use|used)\b|"
    r"\bdo not (?:go|use)\b|\bnot (?:using|going|been)\b|\bhaven'?t (?:been|used|gone)\b|"
    r"\bstopped going\b", re.I)


def _visits_a_month(text):
    """How often they say they go, as visits a month.

    0 is a line that says nothing about how often. -1 is a line that says it without a period
    ("i go twice"), which is not a rate: twice a week and twice a year are the same words, so the
    row that shows both figures at once keeps that line.
    """
    match = _USES_IT.search(text)
    if not match:
        return 0
    said = match.group(1).lower()
    count = _COUNT.get(said)
    if count is None:
        digits = re.match(r"(\d+)", said)
        count = int(digits.group(1)) if digits else 0
    if not count:
        return 0
    period = (match.group(2) or "").lower()
    if not period:
        return -1
    if period in ("month",):
        return count
    if period in ("day",):
        return count * 30
    if period in ("fortnight",):
        return count * 2
    return count * 52.0 / 12.0


def _sum_and_per_month(text):
    """The first sum in the line and what it comes to per month, or (0, 0)."""
    for match in _SUM.finditer(text):
        amount = float(match.group(1).replace(",", ""))
        if match.group(2):
            amount *= 1000
        if amount < 1:
            continue
        for pattern, a_year in _PERIODS:
            if pattern.search(text[match.end():match.end() + 22]):
                return amount, amount * a_year / 12.0
    return 0.0, 0.0


def _pounds(figure):
    return "£%s" % format(int(round(figure)), ",")


def _verdict(monthly, low, high, text, thing):
    """Yes or no in the words the line asked with: too much, worth it, or about right."""
    if _WORTH_IT.search(text):
        if monthly < (low + high) / 2.0:
            return "Yes, that is good value for %s" % thing
        if monthly <= high:
            return "Yes, that is about the going rate for %s" % thing
        return "No, that is dear for %s" % thing
    if _ABOUT_RIGHT.search(text):
        if monthly <= high:
            return "Yes, that is about right for %s" % thing
        return "No, it is above the usual range for %s" % thing
    if monthly < low:
        return "No, that is below the usual range for %s" % thing
    if monthly <= high:
        return "No, that is normal for %s" % thing
    if monthly <= high * 1.6:
        return "No, though it is at the top of the range for %s" % thing
    return "Yes, that is well above the range for %s" % thing


def _sum_a_month_reply(understood):
    read = understood or {}
    text = str(read.get("clean") or read.get("text") or "")
    if not (_TOO_MUCH.search(text) or _WORTH_IT.search(text) or _ABOUT_RIGHT.search(text)):
        return None
    if _FIXED_FEE.search(text) or _NOT_A_BILL.search(text) or _NOT_POUNDS.search(text):
        return None
    uses = _visits_a_month(text)
    amount, monthly = _sum_and_per_month(text)
    if not monthly:
        return None
    where = " ".join(str(word) for word in (read.get("words") or ())).lower() or text.lower()
    # The row a line belongs to is the one that names the thing, not the first row that matches
    # anything: "is 20 a month for a magazine subscription too much" named a subscription, which
    # the TV row keys, so it was answered "that is normal for a TV service". A name for the thing
    # beats a name for the kind of payment, and among the things the longer name is the more
    # specific one ("gas and electric" is the two together, not the gas alone).
    named = []
    for data in SUBSCRIPTIONS.values():
        matched = [name for name in data["names"]
                   if re.search(r"\b%s\b" % re.escape(name), where)]
        thing_named = [name for name in matched if name not in _JUST_A_PAYMENT]
        if thing_named:
            named.append((1, max(len(name) for name in thing_named), data))
        elif matched:
            named.append((0, max(len(name) for name in matched), data))
    for _, __, data in sorted(named, key=lambda row: (-row[0], -row[1])):
        low, high = data["span"]
        if _NOT_GOING.search(text) and data.get("visit"):
            visit_low, visit_high = data["visit"]
            return ("Yes, that is too much for something you do not use: %s a month is %s a year "
                    "for nothing. Cancel it in writing and keep the date you sent it, because most "
                    "gyms want a month's notice, and pay as you go when you do go - about %s to "
                    "%s a visit." % (_pounds(monthly), _pounds(monthly * 12), _pounds(visit_low),
                                     _pounds(visit_high)))
        if _NOT_GOING.search(text):
            return None
        if uses >= 1 and data.get("visit"):
            # They said how often they go, so the honest answer is what a visit costs them.
            per_visit = monthly / uses
            visit_low, visit_high = data["visit"]
            if per_visit <= visit_high:
                verdict = "No, that works out at a fair price a visit"
            elif per_visit <= visit_high * 1.6:
                verdict = "No, though it is dear per visit at the rate you go"
            else:
                verdict = "Yes, that is too much for how often you go"
            count = int(round(uses))
            return ("%s. %d visit%s a month at %s a month is %s a visit, and paying as you go is "
                    "usually %s to %s a visit. %s"
                    % (verdict, count, "" if count == 1 else "s", _pounds(monthly),
                       _pounds(per_visit),
                       _pounds(visit_low), _pounds(visit_high), data["advice"]))
        if uses != 0:
            # A usage count is another card's question for every row but the ones with a visit
            # price, so the sum row stands aside rather than answer half of it.
            return None
        if (data.get("visit") and _SHORT_PERIOD.search(text)
                and _ONE_OCCASION.search(text)):
            # A week or a day of one lesson, swim or session is the visit's own card.
            return None
        return ("%s. %s a month is %s a year, and %s is usually %s to %s a month. %s %s"
                % (_verdict(monthly, low, high, text, data["thing"]), _pounds(monthly),
                   _pounds(monthly * 12), data["thing"], _pounds(low), _pounds(high),
                   data["uses"].format(quarter=_pounds(monthly / 4),
                                       eighth=_pounds(monthly / 8),
                                       day=_pounds(monthly / 22),
                                       week=_pounds(monthly * 12 / 52)),
                   data["advice"]))
    return None


def _a_sum_a_month(memory, understood):
    """A sum per period with an opinion of it: the verdict first, then what makes it one.

    The reply is built from the line, so read with no line at all - which is how the check that
    holds every row here to a range and a question to ask reads it - the row says what it says
    about its own sample line, and the check has an answer to read instead of a function.
    """
    return (_sum_a_month_reply(understood)
            or _sum_a_month_reply({"clean": SUM_A_MONTH_SAMPLE}))


# One signal is the thing, the other is the opinion of the money, and the guard is the sum: a line
# that names a gym and says "too much" without a figure per month is the gym's own card, not this.
_SUM_A_MONTH_KEY = (
    ("too much", "too expensive", "too dear", "rip off", "rip-off", "ripped off",
     "over the odds", "worth it", "worth paying", "about right", "sound right", "sounds right",
     "reasonable", "good value", "bad value", "steep", "a lot of money", "overpriced",
     "normal", "the going rate", "ok", "okay", "fair",
     # the ask as people type it: "i pay 250 a month in electricity is that a lot", and the two
     # words either side of the money - expensive, cheap - with the sum and the thing named
     "a lot", "that much", "too much money", "expensive"),
    tuple(name for data in SUBSCRIPTIONS.values() for name in data["names"]),
)

SUM_A_MONTH_ID = "cost-a-sum-a-month"
# One line of the family, for the checks that hold every row in this table to a range and a
# question to ask: the row's own reply is built from the sum, so a line is the only way to see it.
SUM_A_MONTH_SAMPLE = "is 40 a month for a gym too much"

ENTRIES.append(entry(
    SUM_A_MONTH_ID,
    _SUM_A_MONTH_KEY,
    _a_sum_a_month,
    # The line is a question about the money, so the thing's own card has to stand aside for it.
    guard=lambda understood: bool(_sum_a_month_reply(understood)),
    bias=2))
