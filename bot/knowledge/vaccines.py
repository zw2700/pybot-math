"""Vaccinations: which jab a disease names, when a booster is due, and whether it is safe.

The answers lane owns this domain. It is a domain of its own rather than another run of rows at
the end of bot/knowledge/health.py for two reasons. The word "booster" is three things - a jab, a
wifi repeater and the child car seat - and the rows that own the other two live in
bot/knowledge/technology.py and bot/knowledge/cars.py, so the jab's rows are the third side of
that cross-product and read best together with the comment that says so. And health.py is the
largest file in the knowledge base, close enough to the uploader's size ceiling that every
append there is a conflict with whoever appended last; a new domain file is one file the other
lanes never touch.

Imported back from health.py, not copied: `PETS` (a dog's booster is the vet's) and `_the_line`,
the wording reader every guard in that file uses.
"""
import re

from .health import PETS, _the_line
from .lookup import entry

# The topics this domain answers, as ids from bot/understanding/topics.py.
ANSWERS = ("health",)

# A "booster" was answered as two other things before it was answered as a jab: "should i get a
# covid booster" got the wifi repeater, and "when should i get my covid booster" got the child
# car seat, because both rows list the bare word and their ask groups hold "get" and "when".
# The rows stay for their own lines and stand down on a vaccine word, and this row answers the
# jab. It is one row because the shape of the question is the same ("do i need", "am i due",
# "when should i get"), and the two answers are not: the autumn boosters are offered to everybody
# over 65 whatever their health, and a tetanus booster belongs to the wound and the years since
# the last one. Neither timing can be looked up here, so the reply gives the rule and where to ask.
VACCINE_BOOSTER_ANSWER = (
    "The covid and flu boosters are offered each autumn to anyone 65 or over, pregnant, in a care "
    "home, or living with a condition like asthma, diabetes or a weak immune system, plus carers "
    "and health staff; the invitation comes to you, and failing that a pharmacy or the NHS app "
    "will book it. They are yearly because protection fades, and outside those groups a pharmacy "
    "gives the flu jab for about £15 to £20.")

TETANUS_JAB_ANSWER = (
    "You need a tetanus booster if it is more than 5 years since your last one and the wound was "
    "dirty - soil, a bite, a deep puncture or a burn - while a clean small cut within 10 years is "
    "usually fine. A pharmacist, a minor injuries unit or A&E can give it the same day, so ask "
    "today rather than waiting. Get a deep or heavily bleeding wound looked at straight away, not "
    "just for the jab.")


# The disease named in the line decides the jab: a booster "for measles" is the MMR, and the
# autumn covid card answered it because the row had no measles answer and fell through to the
# covid/flu timing. One table, so the next disease is one line of data rather than another phrase.
MEASLES_JAB_ANSWER = (
    "Measles is covered by the MMR, which is two doses: the first at about 1 year old and the "
    "second at 3 years and 4 months, and two doses is what counts as protected. An adult born "
    "after 1970 who never had two doses, or cannot remember, can have the MMR free at a GP "
    "surgery - and anyone born before 1970 is usually immune from having had measles itself. "
    "One dose gives about 90 per cent protection and two gives about 99.")

SHINGLES_JAB_ANSWER = (
    "The shingles vaccine is offered on the NHS when you turn 65 and again at 70, and it is two "
    "doses given two months apart. If you have already had shingles you can still have it, "
    "because it lowers the chance of it coming back, and younger adults with a weakened immune "
    "system are offered it too - ask the GP if you are not sure whether you have had it.")

PNEUMONIA_JAB_ANSWER = (
    "The pneumonia jab (pneumococcal) is a one-off rather than a yearly one, offered at 65 and to "
    "anyone with asthma, diabetes, heart, kidney or liver disease, or no spleen. If you have had "
    "it you do not need it again, and the GP record will say - the yearly autumn jab you are "
    "thinking of is the flu one, which is a different vaccine.")

# "is my booster jab safe" was answered with who is offered one, which is a different question.
# The safety answer is the same for every routine jab, so it is one card rather than one per
# disease.
JAB_SAFETY_ANSWER = (
    "A sore arm, tiredness and a mild fever for a day or two are the ordinary after-effects, and "
    "serious reactions are rare - a severe allergic reaction is about one in a million doses, "
    "which is why you wait 15 minutes afterwards. The flu jab cannot give you flu because it is "
    "not a live virus, while the MMR and the children's nasal flu spray are live but weakened and "
    "are not given in pregnancy or to someone whose immune system is badly weakened. Mention any "
    "reaction you have had before when you book, and the pharmacist or GP will say whether it is "
    "a reason to skip one.")

PREGNANCY_JAB_ANSWER = (
    "The flu and covid jabs are offered in pregnancy at any stage, because both illnesses are "
    "harder on you and the baby then, and the whooping cough jab is offered from about 16 weeks "
    "and again in each pregnancy. Say you are pregnant when you book, at the GP, the pharmacy or "
    "the maternity team, and they will give you the one for your stage.")


# A day or a booking in the line means the jab is already arranged, and the person is telling you
# about it rather than asking who gets one:
# "im due for my jab on monday" got this row's who-gets-one card out of "due", where "How are you
# feeling about it?" was the warmer and the more useful reply.
_AN_APPOINTMENT_DAY = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|tonight|next week|"
    r"next month|this week|this afternoon|this morning|booked|booking|appointment|appointments|"
    r"rescheduled|rebooked|cancelled|canceled|yesterday|already had|already been|just had)\b")


def _it_is_not_an_appointment_already(understood):
    """A jab booked for a day is news to react to, not the schedule question."""
    if str((understood or {}).get("kind") or "") == "question":
        return True
    return not _AN_APPOINTMENT_DAY.search(_the_line(understood))


def _the_vaccine_row_is_the_answer(understood):
    """Every gate: not a booked jab, not the flu on its own, and not a booster of another kind."""
    return (_it_is_not_an_appointment_already(understood)
            and _not_the_flu_on_its_own(understood)
            and _the_booster_is_the_jab(understood))


# A bare "booster" is three things and the word alone does not say which: a jab, the wifi repeater
# and the child car seat. The line's own jab words settle it, and so does a line with nothing
# behind it ("when do i get my booster" on its own is the jab). What must not settle it is the
# chat: "should i get a booster" three turns into a chat about wifi drops is the repeater, and one
# after "when does my child need a booster seat" is the seat. So a line with no jab word of its
# own is only this row's when the line it follows is about a jab too.
_A_JAB_WORD = re.compile(
    r"\b(covid|flu|jab|jabs|jabbed|jabbing|vaccine|vaccines|vaccinate|vaccinated|vaccination|"
    r"vaccinations|immunisation|immunization|immunised|immunized|inoculation|tetanus|lockjaw|"
    r"booster shot|booster jab|pregnan\w*|expecting|whooping cough|shingles|pneumonia)\b")


def _the_booster_is_the_jab(understood):
    """A booster alone is the jab only when the chat it follows is about a jab as well."""
    if _A_JAB_WORD.search(_the_line(understood)):
        return True
    lean = (understood or {}).get("leans_on") or {}
    if not str(lean.get("text") or "").strip():
        return True
    said = " ".join([str(lean.get("text") or ""), str(lean.get("subject") or ""),
                     " ".join(str(word) for word in lean.get("words") or ())]).lower()
    return bool(_A_JAB_WORD.search(said))


def _not_the_flu_on_its_own(understood):
    """A plain flu question is the flu-jab row's, which is the more specific answer.

    The flu on its own ("when do I get my flu vaccine") names the same jab this row does, so it
    scored here too and took the flu card's line. It stays with the flu card unless the line adds
    what makes it this row's question - a pregnancy, or the word booster.
    """
    line = _the_line(understood)
    if "flu" in line and not any(word in line for word in ("pregnan", "expecting", "booster",
                                                          "jabbed", "booster jab")):
        return False
    return True


# The jab a disease names, checked before the general timings. The disease word is the reading,
# not the question shape: "do i need a booster for measles" and "should i have the mmr" are the
# same answer.
_JAB_BY_DISEASE = (
    (("measles", "mumps", "rubella", "mmr"), MEASLES_JAB_ANSWER),
    (("shingles",), SHINGLES_JAB_ANSWER),
    (("pneumonia", "pneumococcal"), PNEUMONIA_JAB_ANSWER),
)

# "is it safe" is its own question: the lines were answered with who is offered a jab.
_ASKING_IF_IT_IS_SAFE = re.compile(
    r"\b(?:\w+\s+){0,4}safe\b|\bany (?:risk|risks|danger)\b|\bside effects?\b|"
    r"\bdangerous\b|\bharmful\b|\bbad for (?:me|you)\b")


def _vaccine_booster_answer(memory, understood):
    """The disease names the jab; the timings are the pregnancy, the wound and the autumn."""
    line = _the_line(understood)
    # the pregnancy is the most specific thing a line can say, then the safety question, which is
    # the same answer whichever jab is named: "is the mmr safe" is asking about safety, not when
    # the two doses are given
    if any(word in line for word in ("pregnan", "expecting", "due in", "weeks gone")):
        return PREGNANCY_JAB_ANSWER
    if _ASKING_IF_IT_IS_SAFE.search(line):
        return JAB_SAFETY_ANSWER
    for words, answer in _JAB_BY_DISEASE:
        if any(word in line for word in words):
            return answer
    if "tetanus" in line or "lockjaw" in line:
        return TETANUS_JAB_ANSWER
    return VACCINE_BOOSTER_ANSWER


ENTRIES = []

ENTRIES.append(entry(
    "vaccine-booster",
    (("booster", "booster jab", "booster shot", "booster dose", "booster vaccine", "top up jab",
      "covid booster", "covid jab", "covid vaccine", "covid vaccination", "covid shot",
      "jab", "jabs", "jabbed", "vaccine", "vaccines", "vaccination", "vaccinations",
      "immunisation", "immunization", "tetanus", "tetanus jab", "tetanus shot",
      "flu booster",
      # the disease names the jab, and a disease on its own is not this row's question unless
      # it is one of the routine jabs: "should i have the mmr" reached a shrug
      "measles", "mumps", "rubella", "mmr", "shingles", "shingles jab", "pneumonia",
      "pneumococcal"),
     ("need", "needed", "should", "when", "due", "overdue", "get", "got", "have", "had",
      "worth", "how often", "again", "another", "next", "am i", "do i", "can i", "is it",
      "time", "book", "where", "free", "pay", "top up", "safe", "ok", "fine")),
    _vaccine_booster_answer,
    # A booster seat, a wifi booster, a pet's booster and a baby's jabs are four other answers,
    # and a sore arm afterwards is the after-the-jab question rather than this one.
    avoid=("seat", "car seat", "booster seat", "child seat", "isofix", "cushion", "trolley",
           # a seat is also called by its shape and the law rather than the word "seat":
           # "is a backless booster ok" and "is a backless booster safe" were taken by this row
           # once the bare "booster" was keyed with "ok" and "safe", because neither row named
           # "backless". The words stay here and the seat row answers them.
           "backless", "high backed", "high-backed", "rear facing", "rear-facing", "135",
           "height", "booster cushion",
           "pushchair", "high chair", "car", "cars", "van", "driving", "travel", "flight",
           "plane", "holiday",
           "wifi", "wi fi", "wireless", "router", "internet", "broadband", "signal", "reception",
           "mobile signal", "tv", "telly", "aerial", "speaker", "amp", "hifi", "punch", "punching",
           "boxing", "sparring",
           # the day after the jab is the after-effects row's question, and a jab a country
           # wants is the travel one: "can i take paracetamol after the vaccine" and "do i need
           # a yellow fever jab for kenya" are not the autumn-booster timing
           "after the", "after my", "paracetamol", "ibuprofen", "alcohol", "drink",
           "yellow fever", "typhoid", "hepatitis", "rabies", "dengue", "malaria",
           "travel vaccine", "travel jab", "travel clinic",
           "sore", "ache", "hurts", "hurting", "swollen", "side effect", "side effects",
           "arm", "shoulder",
           "baby", "babies", "toddler", "newborn", "child", "children", "kid", "kids",
           "my son", "my daughter", "my boy", "my girl", "school", "nursery", "puppy", "kitten",
           "hamster", "rabbit", "parrot") + PETS,
    # ...and the flu on its own is the flu-jab row's line, and a jab already booked for a day is
    # somebody telling you their news rather than asking who gets one
    guard=_the_vaccine_row_is_the_answer))
