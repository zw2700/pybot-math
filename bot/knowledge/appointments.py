"""What to do before an appointment, asked either way round.

A domain of its own because the question is about the visit rather than about the body: the same
"do i need to do anything before i go" wants the dentist's answer after a dentist and the fasting
rule after a blood test, and it reaches nothing at all if the kind of visit is not part of the
key. It answers health, so a follow-up in a health conversation can find it - a domain that does
not declare health is never searched with the line before it.
"""
import re

from .lookup import entry

ANSWERS = ("health", "food-and-drink")

# What to do before an appointment is a health question, and every way of asking it was reaching
# nothing: "do i need to do anything before i go" after "i have a dentist appointment tomorrow"
# was the search hedge, "should i eat before" ahead of a scan was a refusal, and "what should i
# bring" was an offer to make a list. The appointment itself is the first group, the preparing is
# the second, and one card answers the lot because the answer differs only in the detail.
_APPOINTMENT_KINDS = (
    "appointment", "appointments", "appt", "appts", "dentist", "dental", "hygienist",
    "doctor", "gp", "surgery", "health centre", "health centre", "clinic", "hospital",
    "consultant", "specialist", "physio", "physiotherapy", "chiropodist", "optician",
    "eye test", "check up", "checkup", "scan", "scans", "x-ray", "xray", "x ray", "ultrasound",
    "mri", "ct scan", "mammogram", "colonoscopy", "endoscopy", "blood test", "blood tests",
    "referral", "outpatients",
)

_BEFORE_IT = (
    "before", "beforehand", "in advance", "the day before", "night before", "before i go",
    "before it", "before i come in", "prepare", "preparing", "prep", "get ready", "be ready",
    "anything i should do", "anything i need", "anything i should", "is there anything",
    "do i need to do", "do i need to", "need to do anything", "what do i need", "what do i do",
    "what should i do", "what should i bring", "what do i bring", "bring", "bring with me",
    "take with me", "fast", "fasting", "should i eat", "should i drink", "eat before",
    "empty stomach", "how early", "what time should i",
)

# The giving-up rows, the nerves rows and the pain rows own their own lines, and a line about a
# bill or about getting registered is not a question about how to present yourself on the day.
_NOT_ABOUT_GETTING_READY = (
    "cancel", "cancelling", "canceling", "cancelled", "canceled", "reschedule", "rescheduling",
    "rebook", "rebooking", "postpone", "postponing", "call off", "didnt turn up", "did not turn up",
    "missed", "no show", "nervous", "scared", "afraid", "frightened", "terrified", "dread",
    "anxious", "anxiety", "phobia", "hate the dentist", "hate going",
    "toothache", "tooth ache", "pain", "hurts", "hurting", "abscess", "broken tooth", "chipped",
    "knocked out", "bleeding", "emergency", "a&e", "999", "urgent", "same day",
    "how much", "cost", "costs", "price", "free", "nhs", "register", "registering", "sign up",
    "find a dentist", "find a doctor", "take new patients", "waiting list",
    "how long will it take", "how long does it take", "how long will i be", "how long will it last",
    "after my appointment", "after the appointment", "afterwards", "what happens at",
    "what happens during", "results", "my results", "test results",
    "see a doctor", "see the doctor", "see a gp", "go to the doctor", "call a doctor",
    "should i go", "worth seeing",
    # A visitor and a person being brought something are the visiting and the gift rows: bare
    # "bring" is in _BEFORE_IT, so "can i bring visitors to the hospital" and "what do i bring
    # her" were read as an appointment to get ready for.
    "visitors", "visiting", "visiting hours", "bring her", "bring him", "bring them",
    "bring a gift", "bring flowers", "bring something", "bring to my friend",
    "bring to my mum", "bring to my dad", "bring to see",
    # the dentist's own work has its own answers, and the dentist is not in the "see a" list
    # above: "how do i prepare for a dental implant" is the implant card
    "see a dentist", "see the dentist", "see an optician", "feel sick", "feeling sick",
    "nauseous", "implant", "extraction", "root canal", "crown", "dentures", "braces",
    "wisdom tooth",
)

_ITS_A_BLOOD_TEST = ("blood test", "blood tests", "blood sample", "bloods", "venepuncture",
                     "cholesterol test", "thyroid test", "hba1c", "glucose test")
_ITS_A_SCAN = ("scan", "scans", "x-ray", "xray", "x ray", "ultrasound", "mri", "ct scan",
               "mammogram", "colonoscopy", "endoscopy", "imaging", "radiographer")
_ITS_THE_DENTIST = ("dentist", "dental", "hygienist", "check up", "checkup", "filling")
_ITS_THE_OPTICIAN = ("optician", "opticians", "eye test", "sight test", "optometrist")
# "surgery" is the GP's building and also the operation, and "do i need to fast before surgery"
# is the second one: its answer is the hospital's fasting rule, not "most appointments need
# nothing".
_ITS_AN_OPERATION = ("surgery", "an operation", "operating", "anaesthetic", "anesthetic",
                     "anaesthesia", "pre-op", "pre op", "preoperative", "theatre")
# "do i need to shave before surgery" is a question about the operation, and the fasting card
# answered it with six hours of no food: the reason is a wound-infection rule about nicks in the
# skin, which is the ward's instruction, not eating. The honest punt is better than a confident
# answer to a different question, so these stand the fasting card down and the line keeps
# whatever else it had. The rest of the operation lines, the prep, the tablets and the lift home
# included, are what this card is for.
_NOT_THE_FASTING = ("shave", "shaving", "shaved", "hair removal", "wax", "waxing", "nail varnish",
                    "nail polish", "make up", "makeup", "deodorant", "jewellery", "jewelry")
# "should i take my medication before surgery" and "can i take my blood pressure tablets before
# surgery" are questions about a dose, and the fasting card answered them with six hours of no
# food. A tablet question is the one to hand to a pharmacist, so the row stands down and the line
# keeps the answer it had - except when the thing named is a list to carry in, which is what the
# preparation card is for and what "should i bring my medication list to the hospital" asks.
_MEDICINE_NAMED = ("medication", "medications", "medicine", "medicines", "meds", "tablet",
                   "tablets", "pills", "inhaler", "insulin", "blood thinner", "blood thinners",
                   "warfarin", "statins", "antibiotic", "antibiotics", "painkiller",
                   "painkillers")
_A_LIST_TO_CARRY = ("list", "lists", "boxes", "packet", "pack", "bring", "brings", "carry",
                    "with me", "along", "prescription")


def _a_dose_is_the_question(line):
    """A tablet question rather than a fasting one, and not a list to carry in.

    The verb is what divides them: "should i take my medication before surgery" is a dose, and
    "should i bring my medication list to the hospital" is a thing to put in a bag, which is what
    the preparation card answers.
    """
    if not any(word in line for word in _MEDICINE_NAMED):
        return False
    return not any(word in line for word in _A_LIST_TO_CARRY)


def _the_line_before(memory, reading):
    """The user's last line, or "" - read from whatever the runtime hands a card.

    The understanding only hands the earlier line back as `leans_on` when the new line points at
    nothing of its own, and "should i eat before" names food, so the lean is None exactly on the
    follow-ups that need it most. The card reads the chat itself instead, and it reads it several
    ways, because a card is passed a memory whose shape is the runtime's business: a helper that
    moved, a turn that spells the user's line differently, or a copy of the memory with no turns
    are all things a later change can do, and each one used to turn this card silently back into
    the general one.
    """
    if isinstance(reading, dict):
        for key in ("context", "last_user", "earlier_line"):
            said = reading.get(key)
            if isinstance(said, str) and said.strip():
                return " ".join(said.split()).lower()
    try:
        from ..memory import last_user
        said = last_user(memory)
    except Exception:
        said = ""
    if isinstance(said, str) and said.strip():
        return " ".join(said.split()).lower()
    turns = []
    if isinstance(memory, dict):
        turns = memory.get("turns") or memory.get("history") or []
    for turn in reversed(list(turns or ())):
        if isinstance(turn, dict):
            for key in ("user", "said", "text", "clean"):
                said = turn.get(key)
                if isinstance(said, str) and said.strip():
                    return " ".join(said.split()).lower()
    return ""


# The hours a person goes without food is the fasting row's question, and the line says so: it
# names the fast (or the food it cannot have) and asks how long. Kept as the reading health.py
# uses, so the two agree on which lines are the fasting ones.
_A_FAST_LENGTH_ASK = re.compile(
    r"\bhow long\b[^.?]*(?:fast|fasting|fasted|without food|no food|nothing to eat|empty stomach)"
    r"|(?:fast|fasting|fasted)\b[^.?]*\bhow long\b"
    r"|\bhow many hours\b[^.?]*(?:fast|fasting|fasted|without food|no food|nothing to eat)",
    re.IGNORECASE)

# "how long does a fasting blood test take" is about the visit, and this card says five minutes
# in the chair, so that line stays here even though it names the fast.
_A_TEST_THAT_TAKES = re.compile(
    r"\b(?:test|tests|appointment|appointments)\s+(?:take|takes|took|last|lasts)\b", re.IGNORECASE)


def _the_line_wants_a_length(line, reading):
    """Whether the line asks how long to go without food, which is the hours and not this advice.

    `memory["understood"]["wants"]` is the shared reading of the shape of answer a line asks for,
    written once by bot/modules/intent.py, and "time" is a length. This card has no length in it,
    so on a fasting question it stands aside and the row in health.py that opens with "eight to
    twelve hours without food" answers. The card keeps every line it can answer itself: "do i
    need to fast", "what should i do before a blood test", "what should i bring", and "how long
    does a fasting blood test take", whose five minutes in the chair are here.
    """
    if str((reading or {}).get("wants") or "").strip().lower() != "time":
        return False
    if _A_TEST_THAT_TAKES.search(line):
        return False
    return bool(_A_FAST_LENGTH_ASK.search(line))


def _before_an_appointment(memory, reading):
    """The card for the kind of appointment the line is about, or the general one."""
    line = " ".join(str((reading or {}).get("text") or "").split()).lower()
    leans = (reading or {}).get("leans_on")
    before = ""
    if isinstance(leans, dict) and leans.get("text"):
        # The kind is often in the line before: "i have a dentist appointment tomorrow" then
        # "do i need to do anything before I go".
        before = " ".join(str(leans.get("text") or "").split()).lower()
    if not before or not any(word in line for word in _APPOINTMENT_KINDS):
        # The card reads the chat when the line names no visit of its own. When it does name one,
        # the line wins: "should i eat before a scan" after a dentist appointment is still the
        # scan's question.
        earlier = _the_line_before(memory, reading)
        if earlier and earlier not in line:
            before = (before + " " + earlier).strip()
    if before:
        line += " " + before
    # A meeting at the bank or the job centre is an appointment and none of this applies to it:
    # the row turns it down so the line keeps the answer it had (the packing and paperwork list).
    if any(word in line for word in _NOT_A_MEDICAL_VISIT) \
            and not any(word in line for word in _STILL_MEDICAL):
        return None
    if any(word in line for word in _ITS_AN_OPERATION) and _a_dose_is_the_question(line):
        # Ask a pharmacist: the honest punt the line had beats six hours of no food told to
        # someone who asked whether to swallow their tablets.
        return None
    if any(word in line for word in _ITS_AN_OPERATION) \
            and not any(word in line for word in _NOT_THE_FASTING) \
            and not any(word in line for word in ("gp surgery", "the surgery", "at the surgery",
                                                  "surgery hours", "surgery number")):
        return ("The hospital sets this one and you should not guess: usually nothing to eat for "
                "six hours before an anaesthetic and nothing clear to drink for two, and the "
                "letter or the pre-op call gives you the exact times. Ask about your regular "
                "tablets at the pre-op rather than deciding yourself, because most are continued "
                "but blood thinners are often stopped for a few days. Arrange for someone to "
                "bring you home, as you cannot drive or go home alone after a general "
                "anaesthetic.")
    if any(word in line for word in _ITS_A_BLOOD_TEST):
        # "how long do i need to fast before a blood test" asks for the hours, and there are none
        # in this card: it stands aside and the fasting row answers, where the visit and the counts
        # were given to a line that asked how long.
        if _the_line_wants_a_length(line, reading):
            return None
        return ("Only fast if the letter or the person who booked it told you to: most blood tests "
                "need no fasting at all, and water is fine even when they do. Wear something with "
                "a short or loose sleeve so the arm is easy to get at, and keep your hands warm on "
                "the way in, which makes the vein easier to find. Keep taking your medicines as "
                "usual unless the letter says otherwise - thyroid and blood pressure tablets are "
                "meant to be taken, so ring the surgery rather than skipping one.")
    if any(word in line for word in _ITS_A_SCAN):
        return ("Follow the letter rather than a general rule, because what to do differs: a "
                "plain x-ray needs nothing, an ultrasound often wants a full bladder, some scans "
                "want an empty stomach for a few hours, and a colonoscopy is the bowel prep it "
                "gives you plus nothing to eat after the time it names. Leave metal at home for "
                "an MRI - jewellery, keys, an underwired bra - and tell them if you have a "
                "pacemaker, a metal implant or could be pregnant. Take the letter with you and "
                "ring the department if any of it is unclear or you cannot make the time.")
    if any(word in line for word in _ITS_THE_DENTIST):
        return ("For a check-up there is nothing to prepare: brush as usual and eat normally. "
                "Bring the names of the medicines you take, and say if you are on a blood thinner "
                "or have had a heart valve replaced, because they may want to check before "
                "treatment; tell them early if you are nervous, since they can plan the visit "
                "around it. Arrive a few minutes early, as the paperwork at a practice you have "
                "not been to before takes longer than the appointment.")
    if any(word in line for word in _ITS_THE_OPTICIAN):
        return ("Take your current glasses, or the prescription if you have it, and any eye drops "
                "you use, and write down what you have noticed - blurring at a distance, trouble "
                "reading, glare at night - because the test is quicker when they know what to "
                "look for. Say if you drive: dilating drops blur your vision for a few hours, so "
                "you may want someone with you or the bus.")
    return ("Read the letter or the text reminder first, because it says what to do before this "
            "one and most appointments need nothing. Worth doing every time: write down the two "
            "or three things you want to raise, most worrying first, and take the list of "
            "medicines you are on, or the boxes themselves. Arrive ten minutes early for a place "
            "you have not been to, and ring if you cannot make it - a missed slot usually means a "
            "long wait for the next one.")


# The ask on its own, after the line that named the appointment: "i have a scan on thursday" and
# then "should i eat before" has no appointment word in it at all, so a row keyed only on the
# appointment is found only when the earlier line is searched with it. These are the two halves
# of that ask - what the line wants to know, and the preparing shape it asks in - and the guard
# below means the row answers only when the line before it named a kind of appointment, so
# "should i eat" after a barbecue and "what should i bring" after a visit from a brother are
# left to their own answers.
_PREPARING_SUBJECT = (
    "eat", "eating", "drink", "drinking", "food", "water", "fast", "fasting", "empty stomach",
    "bring", "bring with me", "take with me", "get ready", "prepare", "preparing",
    "anything i should", "anything i need",
)
_PREPARING_ASK = (
    "before", "beforehand", "in advance", "day before", "night before", "before i go",
    "before i come in", "do i need to", "should i", "can i", "am i allowed", "what should i",
    "what do i", "what to", "what time", "how early", "is there anything",
)


# An appointment is not always a medical one, and the preparing card is about the body: a meeting
# at the bank or the job centre wants the paperwork, not the list of medicines and the fasting
# rule, so those lines keep the answer they had.
_NOT_A_MEDICAL_VISIT = (
    "bank", "building society", "job centre", "jobcentre", "benefits office", "council",
    "solicitor", "lawyer", "interview", "vet", "garage", "mot", "hairdresser", "barber",
    "estate agent", "letting agent", "landlord", "passport", "immigration", "school",
    "university", "mortgage", "tax office", "hmrc", "dwp",
)
_STILL_MEDICAL = ("dentist", "dental", "gp", "doctor", "hospital", "clinic", "nurse", "surgery",
                  "health", "physio", "optician", "scan", "blood", "medical", "consultant",
                  "midwife", "pharmacy", "a&e", "nhs")


def _follows_an_appointment(understood):
    """Whether this line is a question about an appointment the line before it named."""
    if not isinstance(understood, dict):
        return False
    leans = understood.get("leans_on")
    if not isinstance(leans, dict):
        return False
    before = " ".join(str(leans.get(part) or "") for part in ("text", "subject", "topic"))
    before = " ".join(before.split()).lower()
    if not before:
        return False
    if any(word in before for word in _NOT_A_MEDICAL_VISIT) \
            and not any(word in before for word in _STILL_MEDICAL):
        return False
    return any(word in before for word in _APPOINTMENT_KINDS)


ENTRIES = [entry(
    "before-an-appointment",
    (_APPOINTMENT_KINDS, _BEFORE_IT),
    _before_an_appointment,
    ask=_APPOINTMENT_KINDS,
    avoid=_NOT_ABOUT_GETTING_READY)]
# The same question with the appointment only in the line before it. The row above needs the
# appointment in the line, which is right for "should i eat before a scan" and misses the
# follow-up shape, so the pairing is done here: the preparing words are the key, the earlier line
# has to name the visit, and the reply is the same card the line would get if it named the visit
# itself.
ENTRIES.append(entry(
    "before-an-appointment-follow-up",
    (_PREPARING_SUBJECT, _PREPARING_ASK),
    _before_an_appointment,
    guard=_follows_an_appointment,
    avoid=_NOT_ABOUT_GETTING_READY))
