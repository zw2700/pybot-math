"""A car with something wrong with it, which is not a question about learning to drive.

The two things share a word. "drive" is the verb of a lesson and the verb of a broken car, so a
chat about a car that has gone wrong collects the learning-to-drive rows:

    my punto makes a clicking noise when i turn
    is it safe to drive
    what will it cost roughly   -> "Most people need around 45 hours of lessons..."

The price of a repair answered with the price of lessons. Nothing in the third line says which
car it is: the fault is two lines back, and a bare "what will it cost roughly" is the same
sentence for a clutch and for a test. So the reading is made from the chat, once per turn: a car
and something wrong with it in the last few lines, and nothing in this line about learning.

A line that does name the learning keeps its own row - "how much do driving lessons cost" after a
car fault is still the lessons question - so the learning words here take the reading back.
"""
import re

# The machine. A make or a model (the list the topic reader keeps), a plain car word, or the
# thing a garage does the work on.
CAR = re.compile(
    r"\b(?:car|cars|van|vans|mot|mot'd|garage|garages|mechanic|mechanics|tyre|tyres|tire|tires"
    r"|engine|gearbox|clutch|brakes|brake|exhaust|radiator|battery|alternator|starter"
    r"|windscreen|bonnet|suspension|shock|absorber|wheel|wheels|hub|bearing|bearing's"
    r"|jump\s?start|service|serviced|motoring"
    r"|audi|ford|vauxhall|toyota|honda|nissan|renault|peugeot|citroen|skoda|hyundai|kia|mazda"
    r"|volvo|suzuki|bmw|mercedes|volkswagen|vw|fiat|tesla|dacia|chevrolet|chrysler|dodge"
    r"|subaru|mitsubishi|lexus|saab|alfa|jeep|bentley|porsche|ferrari|lamborghini|aston|lada"
    r"|daewoo|infiniti|acura|punto|corsa|clio|astra|mondeo|passat|micra|yaris|fabia|octavia"
    r"|ibiza|qashqai|juke|captur|kadjar|sandero|duster|sprinter|picanto|zafira|insignia|vectra"
    r"|laguna|megane|berlingo|picasso|cupra|leon|toledo|kamiq|karoq|kodiaq|tucson|sportage"
    r"|camaro|impreza|forester|hilux|auris|avensis|prius|celica|supra|aygo|navara)\b")

# What is wrong with it. A noise, a failure to start, a light, a leak - the words a person uses
# before anybody has looked at the car, and the words a garage's verdict is reported in.
FAULT = re.compile(
    r"\b(?:noise|noises|noisy|rattle|rattles|rattling|click|clicking|clicks|knock|knocking"
    r"|grinding|squeal|squealing|squeak|squeaking|whining|humming|judder|juddering"
    r"|wont start|won't start|wouldnt start|wouldn't start|not starting|cutting out|cuts out"
    r"|stalls|stalled|warning light|engine light|light on|leak|leaks|leaking|leaked|smoke"
    r"|smoking|overheating|overheated|misfire|misfiring|broken|broke|faulty|gone wrong"
    r"|failed|failing|fail|puncture|punctured|flat|bald|locked up|seized|clunk|clunking"
    r"|vibration|vibrating|pulling|sticking|jammed|rust|rusted|corroded|seized up"
    # A garage's verdict is a fault even when the part it names has no word of its own: "the
    # garage says its the cv joint", "they quoted me for a head gasket".
    r"|garage (?:says|said|thinks|reckons|quoted|quotes|wants|has had)|they quoted"
    r"|needs? (?:a )?(?:new|replacing)|worn|knackered|shot)\b")

# A learning question is not a repair: it keeps the row about lessons, whatever the chat has
# been about. "how much do driving lessons cost" two lines after a clutch is still the lessons.
LEARNING = re.compile(
    r"\b(?:lesson|lessons|learner|learners|instructor|instructors|provisional|theory"
    r"|driving test|test booked|passed|pass|learn|learning|beginners?|tuition)\b")

# How far back the fault is looked for, in the person's own lines. A fault named five turns ago
# is not what a bare "how much" is about by then.
LOOKBACK = 3


# The words that break a line into clauses. A fault on one side of them is not a fault on the
# other: "my car is fine but the boiler is broken" is the boiler's line, and reading the whole
# sentence as one thing said the car was broken. "and" is a break too - "the dishwasher is
# leaking and the car wont start" is a fault of the car only where the clause that says so names
# it.
CLAUSE_BREAK = re.compile(r"\b(?:but|and|though|although|while|whereas|so|because|then|except)\b"
                          r"|[;,.!?]")

# Between the fault and the words round it, these take the fault back: "the car isnt leaking",
# "the noise has gone", "my car is fine now". A line that says the car is well is not a fault,
# and a reader that guesses from the one word is worse than one that says nothing.
NOT_A_FAULT = re.compile(r"\b(?:not|no|never|isnt|isn't|arent|wasnt|wasn't|hasnt|hasn't"
                         r"|havent|haven't|dont|don't|cant|can't|fine|ok|okay|sorted|fixed"
                         r"|repaired|stopped|gone|better)\b")

# A car word a bike word owns is the bike's: "my bike tyre is flat and the car is fine" is a
# puncture on the bike, and "tyre" alone said it was the car.
NOT_THE_MACHINE = re.compile(r"\b(?:bike|cycle|bicycle|motorbike|motorcycle|scooter|mower"
                             r"|lawnmower|tractor|lorry|bus|train|plane|caravan|trailer)s?\b")


def _a_fault_that_is_not_undone(clause):
    """True when the clause says something is wrong, with no word taking it back."""
    for match in FAULT.finditer(clause):
        # "not starting" and "wont start" are faults written with a negation in them
        if match.group(0).lower().startswith(("not ", "wont", "won't", "wouldnt", "wouldn't")):
            return True
        before = clause[max(0, match.start() - 24):match.start()]
        after = clause[match.end():match.end() + 24]
        if NOT_A_FAULT.search(before) or NOT_A_FAULT.search(after):
            continue
        return True
    return False


def _the_car_in(clause):
    """True when the clause names the machine itself, and not a bike's part or a bus."""
    for match in CAR.finditer(clause):
        before = clause[max(0, match.start() - 20):match.start()]
        if NOT_THE_MACHINE.search(before):
            continue
        return True
    return False


def _says_a_broken_car(text):
    """True when one clause of the line names the car and says something is wrong with it."""
    low = (text or "").lower()
    for clause in CLAUSE_BREAK.split(low):
        if _the_car_in(clause) and _a_fault_that_is_not_undone(clause):
            return True
    return False


def a_broken_car_is_the_subject(text, earlier=()):
    """True when a car with something wrong with it is what this turn is about.

    `earlier` is the person's own earlier lines, oldest first. The fault may be in this line or
    in the last few, because a bare price question names none of it, and the learning words in
    this line take the reading back: a lesson question is not a repair, however broken the car in
    the chat is.
    """
    low = (text or "").lower()
    if LEARNING.search(low):
        return False
    if _says_a_broken_car(low):
        return True
    return any(_says_a_broken_car(line) for line in list(earlier)[-LOOKBACK:])


def no_broken_car(understood):
    """A guard for a row about learning or hiring a car: False when a broken one is the subject.

    The row that answers "how much do driving lessons cost" answered a bare "what will it cost
    roughly" two lines after a clicking noise, because the subject of the chat was the word
    "drive". A row about lessons stands aside for the repair, and the line itself decides (see
    `a_broken_car_is_the_subject`): "how much do driving lessons cost" is still the lessons.
    """
    return not (isinstance(understood, dict) and understood.get("car_fault"))


def no_broken_car_or_none(understood):
    """A guard for a row that answers because the chat says a car is broken: `car_fault` or no."""
    return bool(isinstance(understood, dict) and understood.get("car_fault"))
