"""The kit for a small plan: a picnic, a gym bag, a spa day, an interview, a barbecue, a day at
the beach, an exam, a cold, a race, a hospital bag, a driving test and a swim.

"What do i need for a picnic", "what should i take to a barbecue" and the like are the commonest
of the everyday kit questions, and 42 of the 103 deck turns that ask what somebody needs for a
thing were answered with a shrug (answers, #answers 16). Each row is keyed by the plan and asks
for a need word, so "how do i cook on a barbecue" keeps its own answer.
"""
import re

from .lookup import entry

# The plans are days out, a workout, a booking and a job: the topics the base already covers.
ANSWERS = ("food-and-drink", "fitness", "work")

# The kit question, not the plan: "why is a picnic nice" and "how do i join a gym" are not this.
# "wear" is not here on purpose: "what should i wear to an interview" is the dress question.
# "get", "buy" and "first" are not here: "i didn't get the job i interviewed for" holds two of
# them, and it is not asking for the kit (deck row `multi-025`).
_NEEDS = ("need", "needs", "needed", "bring", "brings", "take", "takes", "pack", "packing",
          "kit", "list", "prepare", "prep", "essentials", "supplies")


# A trip of some days is the packing question, not the kit for one occasion. "What should i pack
# for a beach holiday" and "what should i pack for a week at the beach" were answered with the
# day kit - sun cream, water, a hat - when the answer they wanted was the week's list of clothes.
# The length can be said as a word ("holiday", "fortnight") or as a number of days or nights, and
# it is read from this turn's line only: the trip planned two turns ago does not turn today's kit
# question into a packing one.
_A_TRIP_OF_SOME_LENGTH = re.compile(
    r"\b(?:holiday|holidays|vacation|vacations|fortnight|fortnights|week away|weeks away|"
    r"week at|weeks at|week in|weeks in|long weekend|next week|next month|week after next|"
    r"\d+\s*(?:days?|nights?|weeks?)|a couple of (?:days|nights|weeks)|"
    r"couple of (?:days|nights|weeks)|few (?:days|nights|weeks))\b", re.IGNORECASE)


def _a_trip_of_some_length(understood):
    """True when the line is about a stay of some days rather than one occasion."""
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    if not said:
        said = " ".join(str(word) for word in ((understood or {}).get("words") or ()))
    return bool(_A_TRIP_OF_SOME_LENGTH.search(said))


def _asks_for_the_kit(understood):
    """True when the line is asking what to have with them, for one occasion and not a trip."""
    words = set((understood or {}).get("words") or ())
    return any(word in words for word in _NEEDS) and not _a_trip_of_some_length(understood)


def _a_trip_said_before(memory):
    """True when a turn or two back named a stay of some days rather than the day itself.

    A guard cannot read the conversation, so the trip is read here: "my holiday is next week"
    then "what should i pack for a beach" is the week's packing list, which another row answers,
    and the day's sun cream is the wrong answer to it.
    """
    turns = (memory or {}).get("turns")
    if not isinstance(turns, list):
        return False
    earlier = [str(one.get("user") or "") for one in turns[-4:] if isinstance(one, dict)]
    return bool(_A_TRIP_OF_SOME_LENGTH.search(" ".join(earlier)))


def _the_day_at_the_beach(memory, understood):
    """The kit for a day at the beach, or nothing when the conversation is a trip away."""
    if _a_trip_said_before(memory):
        return None
    return ("Factor 30 or higher sun cream, a bottle of water each, a hat, and a windbreak or "
            "umbrella for shade, plus a towel each and one spare for the car. Take cash for "
            "parking and a bag for your rubbish, because bins on the sand are thin on the "
            "ground.")


ENTRIES = [
    entry("a-picnic-kit",
          (("picnic", "picnics"), _NEEDS),
          ("A rug, a cool bag with a freezer block, plates and cups you do not mind losing, a "
           "bottle opener, napkins, a bin bag and water. Skip anything heavy with mayonnaise "
           "unless it is eaten within the hour: sausage rolls, cheese, fruit and a flask keep for "
           "hours."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          # a picnic somebody eats is the food row's question ("whats a good picnic to take for a
          # day out", deck row `multi-9021`), and so is a blanket or a table
          avoid=("table", "bench", "site", "recipe", "cake", "bread", "sandwich", "blanket",
                 "basket", "hamper", "good", "best", "nice", "ideas", "food", "eat", "something",
                 "lunch", "snack")),
    entry("a-gym-bag-kit",
          (("gym", "gyms", "workout", "workouts"), _NEEDS),
          ("For the gym: trainers you only wear indoors, two towels (one for the floor and "
           "machines), a water bottle, a padlock for the locker, deodorant and a bag for wet kit. "
           "A resistance band and a notebook beat anything else a shop will sell you."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          # "what do i need for the gym" is this list - the towels, the padlock, trainers kept for
          # indoors - and the first-session row in clothing.py keys the gym and the asking words
          # too, so the specific list takes the tie
          bias=3,
          avoid=("join", "membership", "contract", "cancel", "price", "cost", "cheap", "app")),
    entry("a-spa-day-kit",
          (("spa", "spas"), _NEEDS),
          ("Swimwear, flip-flops, a towel and robe if the place does not lend them, a hair tie, "
           "a bottle of water, and your own shampoo if you are fussy. Leave the phone in the "
           "locker: the pools and steam rooms dehydrate you faster than people expect."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          avoid=("price", "cost", "cheap", "voucher", "book", "booking", "cancel")),
    entry("an-interview-kit",
          (("interview", "interviews"), _NEEDS),
          ("Take the letter or email with the address and time, a printed copy of your CV, a pen "
           "and a notepad, and the name of the person you are meeting. Photo ID for the building, "
           "and ask at the desk for them by name."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          avoid=("questions", "answers", "nervous", "nerves", "salary", "job offer",
                 "thank you letter")),
    entry("a-barbecue-kit",
          (("barbecue", "bbq", "barbeque", "cookout"), _NEEDS),
          ("Charcoal (about 1kg for ten people), a chimney starter and firelighters, long tongs, "
           "a wire brush, a tray for the cooked meat, and a meat thermometer. Put a bucket of "
           "water or sand beside it; a gas one needs a spare bottle instead."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          avoid=("sauce", "marinade", "rub", "recipe", "how long", "temperature", "weather")),
    # --- the days out and the appointments a person packs for ---------------------
    # The same question about a day at the beach, an exam, a cold, a race, a hospital bag, a
    # driving test and a swim was a shrug or a card about something else: "what do i need for an
    # exam" was answered with how to revise, "what do i need for my driving test" with the age
    # you stop needing to take one, and "what do i need for a hospital bag" with the appointment
    # card telling them to read the letter.
    entry("a-beach-day-kit",
          (("beach day", "beach", "beach trip", "day at the beach"), _NEEDS),
          _the_day_at_the_beach,
          ask=_NEEDS, guard=_asks_for_the_kit,
          # a swim, the tide and the parking are the beach's own answers, and "what should i wear
          # to the beach" is the clothes question
          # a line that names something else it wants - a bed, a meal, a way there - is answered
          # by the row for that want, and the day kit is what is left. "we need a hotel near the
          # beach" was answered with sun cream and "what food should we take to the beach" with
          # the same, when the picnic food was the answer both times.
          avoid=("how long", "how much", "parking", "car park", "tide", "tides", "swim",
                 "swimming", "dog", "dogs", "wear", "nearest", "seaside", "coast",
                 "hotel", "hotels", "stay", "staying", "place to stay", "accommodation",
                 "somewhere to stay", "guest house", "b&b", "airbnb", "food", "eat", "eats",
                 "eating", "lunch", "dinner", "breakfast", "snack", "snacks", "picnic",
                 "restaurant", "cafe", "get there", "travel", "train", "coach", "flight",
                 "flights")),
    entry("an-exam-kit",
          (("exam", "exams", "mock exam", "gcse exam", "a level exam"), _NEEDS),
          ("Two pens, a pencil, a spare, an eraser, and your photo ID plus the letter with the "
           "room and the time on it. A clear bottle of water if the rules allow one, and nothing "
           "else in your pockets - a phone switched off still counts as being in the room, so "
           "leave it at home."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          # how to revise, how long the paper is and what the result means are all other rows
          avoid=("revise", "revision", "revising", "how to", "how long", "result", "results",
                 "grade", "grades", "resit", "coursework", "panic", "nervous", "anxiety",
                 "remark", "re-mark")),
    entry("a-cold-kit",
          (("a cold", "my cold", "this cold", "a bad cold", "a chesty cold"), _NEEDS),
          ("Paracetamol or ibuprofen, a decongestant spray, tissues, honey and lemon, and a "
           "thermometer. Rest and plenty to drink do most of the work, and a cold clears in about "
           "a week without antibiotics - see a GP if you are short of breath, if a fever lasts "
           "more than five days, or if you are getting worse after day five rather than better."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          avoid=("sore", "sore throat", "chest", "cough", "coughs", "flu", "how long", "how to",
                 "get rid", "shift", "cure", "medicine", "tablets", "antibiotics", "doctor",
                 "gp", "child", "kid", "kids", "baby", "toddler", "pregnant", "asthma")),
    entry("a-race-day-kit",
          (("marathon", "half marathon", "a 10k", "race day"), _NEEDS),
          ("Nothing new on the day: the shoes, socks and kit you did your long runs in, plus your "
           "race number, safety pins, a bottle, and the gels or sweets you have practised with. "
           "Eat the breakfast you have tested, get there an hour early, and set off slower than "
           "feels right."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          avoid=("training", "train for", "plan", "how long", "how to", "pace", "pacing",
                 "beginner", "schedule", "lose weight", "diet", "injury", "injured", "knee",
                 "shin", "blister", "blisters")),
    entry("a-hospital-bag",
          (("hospital bag", "baby bag", "birth bag", "bag for hospital",
            "bag for the hospital"), _NEEDS),
          ("Nappies and wipes, three or four babygrows and vests, maternity pads, your own "
           "toiletries and a phone charger with a long cable, plus snacks and a water bottle. "
           "Pack two bags - a small one for the labour room and a bigger one for the ward - and "
           "keep your notes and ID on the top of one, because someone asks for them at the door."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          avoid=("appointment", "appointments", "scan", "scans", "surgery", "operation",
                 "admission", "discharge", "visit", "visiting", "letter", "parking", "nursery",
                 "car seat", "cot")),
    entry("a-driving-test-kit",
          (("driving test", "practical test", "practical driving test", "driving test day"),
           _NEEDS),
          ("Your provisional licence and the theory pass certificate if you have the paper one, "
           "and the car you are using, with L plates front and back, insurance that covers a "
           "learner, a valid MOT and enough fuel. Take glasses or contact lenses if you need them "
           "to drive, and be there ten minutes early - the examiner reads the documents before "
           "you move off."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          avoid=("theory", "provisional", "licence", "license", "book", "booking", "cancel",
                 "cost", "price", "fail", "failed", "passed", "nervous", "lessons",
                 "instructor", "insurance", "mot", "age", "how long", "waiting",
                 "what happens", "tips", "advice")),
    entry("a-swim-kit",
          (("swimming", "a swim", "swim session", "swimming session"), _NEEDS),
          ("Goggles, a swimming costume or trunks, a towel and a padlock for the locker, plus "
           "flip-flops for the poolside and a bottle of water. A swim hat if the pool asks for "
           "one, and a pound coin for an old locker."),
          ask=_NEEDS, guard=_asks_for_the_kit,
          # learning to swim, the stroke and the price of a membership are other rows, and a
          # swimming lesson is a booking rather than a kit
          avoid=("how do i", "how to", "learn", "cant", "can't", "scared", "fear", "afraid",
                 "breaststroke", "front crawl", "technique", "how long", "how often",
                 "how much", "price", "cost", "membership", "sea", "open water",
                 "lose weight", "child", "kid", "kids", "toddler", "baby", "lane", "club",
                 "classes", "timetable", "lesson", "lessons", "class", "course")),
]
