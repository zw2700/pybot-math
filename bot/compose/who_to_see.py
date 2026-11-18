"""A bare "do i need to see anyone" is answered by the someone the answer already named.

    my dog ate chocolate
      "Yes, chocolate is poisonous to dogs: the darker the chocolate, the worse it is. Ring your
       vet with the dog's weight and roughly how much and what kind of chocolate it ate; don't
       wait for symptoms."
    do i need to see anyone
      before: "That's beyond what I know well, sorry. Searching for it will turn up better sources
               than I can offer; tell me what you find and I'll help you weigh it up."
      after:  "Yes - your vet. Ring them with the dog's weight and roughly how much and what kind
               of chocolate it ate."

The answer had already said who to ring, in an instruction with no fence around it, and the line
asks only whether somebody should be seen. Nothing in the knowledge base matches those words -
"anyone" is not a topic - so the turn fell to the don't-know line, which is the one reply that
throws away an answer the bot had just given.

What this file is careful about:

* The ask must be **bare**. A line that names what it is about ("do i need to see anyone about my
  tax return", "i need to see a doctor tomorrow") is somebody else's, and is left alone.
* The answer in hand must name a **person to contact**, in an instruction with no "if", "when" or
  "most days" in front of it - the reading `verdict._referral` already makes, so the fence rules
  written there are the ones used here. An answer that says "see a doctor if it is still there in
  three weeks" is advice for later, and the doubt about it is answered by the condition, not by
  this.
* The reply is the answer's own words, cut to the instruction. Nothing is added about the thing
  the answer was about, so the bot cannot say more than it already did.
"""
import re

from . import pick, verdict

# A line that asks only whether somebody should be seen, and names nothing else. The subject of
# the question is in the answer above, so every form here is short and whole-line.
ASK = re.compile(
    r"(?:do|should|shall|must|need|will|would|can|could|have)\s+"
    r"(?:i|we|you)\s+"
    r"(?:(?:need|have|got|want)\s+to\s+|really\s+|actually\s+|even\s+|just\s+)?"
    r"(?:see|ring|call|visit|contact|speak\s+to|talk\s+to|go\s+(?:to|and\s+see)|get\s+seen\s+by|"
    r"book\s+(?:in\s+with|an?\s+appointment\s+with)|get\s+(?:an?\s+)?appointment\s+with)\s+"
    r"(?:somebody|someone|anybody|anyone|a\s+professional|"
    r"a\s+(?:doctor|vet|dentist|nurse|gp|pharmacist|optician|midwife|lawyer|plumber|"
    r"electrician|specialist)|the\s+(?:doctor|vet|dentist|nurse|gp|pharmacist|optician))\b"
    r"\s*[?.!]*$")

# The person the answer named, in the order a person would say it. Read out of the instruction so
# the reply can name them first: the line asked "anyone", and "your vet" is the answer to that.
A_PERSON = re.compile(
    r"\b(?:your|the|a|an|their|his|her)?\s*"
    r"(vet|doctor|gp|dentist|nurse|pharmacist|optician|midwife|health visitor|paramedic|"
    r"physio(?:therapist)?|practice nurse|a&e|111|999)\b", re.IGNORECASE)

# A place is not a person. "a knock-out, being sick, or feeling confused or sleepier than usual
# means an ambulance or A&E" names somewhere to go, and "The answer named one: A&E" reads as though
# a person were being named; and there is nobody for a pronoun to stand in for (hearty-emu's
# #11181 review). A place takes the answer's own words and a plain yes.
A_PLACE = re.compile(
    r"(?:a&e|the\s+emergency\s+department|walk-?in\s+centre|minor\s+injuries(?:\s+unit)?|"
    r"urgent\s+care|out\s+of\s+hours|999|911|111|112)\b", re.IGNORECASE)

# The somebody named, said back as the answer of the question they asked.
SOMEONE_LINES = (
    "Yes - {person}. {call}",
    "Yes, {person} - {call_lower}",
    "The answer named one: {person}. {call}",
    "Yes: {person}. {call}",
)

# ...and where the name is a place, which is nobody to name first: the answer's own instruction is
# the whole reply ("Yes - take them to A&E now instead of waiting").
PLACE_LINES = (
    "Yes - {call_lower}",
    "{call}",
    "Yes, that one: {call_lower}",
)

# ...and for an emergency number, where the number in the answer's own sentence is the reply.
ON_THE_PHONE_LINES = (
    "{call}",
    "Yes - {call_lower}",
    "The answer said it plainly: {call_lower}",
)

# The instruction cut short enough to read after the name. The answer's own words up to the first
# semicolon, and then up to the first comma when that is still long: a bare doubt gets a sentence,
# not the paragraph it came from.
A_LONG_CALL = 16


def _clean(text):
    return " ".join(str(text or "").lower().split())


def _the_answer_in_hand(memory):
    """The reply the bot gave last, or ""."""
    turns = (memory or {}).get("turns")
    if not turns:
        return ""
    for turn in reversed(turns):
        said = turn.get("bot") if isinstance(turn, dict) else None
        if isinstance(said, str) and said.strip():
            return said
    return ""


# A sign is not a step. "a knock-out, being sick, or feeling confused or sleepier than usual means
# an ambulance or A&E rather than wait" says what a sign means, and the person has not said they
# have the sign: told "go to A&E" over it, somebody with a bump that needs an ice pack is sent to
# hospital. A sentence whose naming is the consequence of a sign - "means", or a condition in
# front of it - is a rule about when to go, not the thing to do now (hearty-emu's #11181 review).
A_SIGN_MEANS = re.compile(
    r"\b(?:if|unless|when|whenever|means|would\s+mean|otherwise|in\s+case)\b",
    re.IGNORECASE)
# ...and the somebody a condition names can be nobody in particular: "See someone the same day if
# the eye is painful" is the answer to a bare ask all the same.
ANYBODY = re.compile(r"\b(?:someone|somebody|anyone|anybody|a\s+professional)\b", re.IGNORECASE)

# The instruction verb directly in front of the mention is what makes a pronoun fit: "Ring your
# vet" and "it is worth saying to a GP" take "them", and "an ambulance or a doctor rather than
# wait" does not - "an ambulance or them" reads as though somebody had already been named.
AN_OBJECT_OF = re.compile(
    r"\b(?:see|ring|call|contact|visit|ask|speak\s+to|talk\s+to|say\s+to|saying\s+to|go\s+to|"
    r"book\s+in\s+with|appointments?\s+with|with|to)\s*$", re.IGNORECASE)

# The reply when the answer made the referral depend on a sign: the answer's own conditional
# clause is the honest answer to "do i need to see anyone" over it, and the answer's own question
# is asked back, because the answer asked it for the same reason.
CONDITION_LINES = (
    "Not always. {clause}",
    "It depends. {clause}",
    "Go by this. {clause}",
    "Only if it comes to that. {clause}",
)


def _the_condition(said):
    """The answer's own sentence making a referral depend on a sign, cut to the sign."""
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        person = A_PERSON.search(sentence) or ANYBODY.search(sentence)
        if not person or not (verdict.NAMES_A_CLINICIAN.search(sentence)
                              or ANYBODY.search(sentence)):
            continue
        if not (A_SIGN_MEANS.search(sentence) or _a_sign_not_a_step(sentence, person)):
            continue
        clause = sentence.strip()
        # "A bumped head hurts for a day or two and an ice pack on it for ten minutes is plenty,
        # but a knock-out ... means an ambulance or A&E" - the person knows the bump, and the sign
        # is what the doubt is about. A fence written after the name ("See a GP if it lasts more
        # than three weeks") is the answer's own sentence whole, which is what to say.
        cut = clause.rfind(", but ")
        if cut > 0 and _a_sign_not_a_step(clause, person):
            # The half after "but" starts mid-sentence and opens the reply, so it is capitalised.
            clause = clause[cut + len(", but "):]
            clause = clause[:1].upper() + clause[1:]
        return clause
    return ""


def _the_question(said, clause=""):
    """The answer's own question, if it asked one the person can answer."""
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        said_now = sentence.strip()
        if said_now and said_now not in clause and (
                said_now.endswith("?") or "? " in said_now):
            if "?" in said_now:
                return said_now[:said_now.index("?") + 1]
    return ""


def _the_condition_reply(said, memory):
    clause = _the_condition(said)
    if not clause:
        return ""
    written = clause.rstrip(" .") + "."
    reply = pick(CONDITION_LINES, memory, clause).replace("{clause}", written)
    question = _the_question(said, clause)
    if question and question not in reply:
        reply = reply.rstrip() + " " + question
    return reply


# A sentence can also make its referral depend on a subset of the thing rather than on the thing:
# "A cut that gapes open, is deep, or keeps bleeding through the cloth needs a nurse or A&E" is a
# rule about some cuts, and "Yes - a nurse" over a nick from an onion is more than the answer said.
A_SUBSET_OF_TIME = re.compile(r"\b(?:that|which|who)\b", re.IGNORECASE)

# The words that make a sentence naming a clinician a thing to do rather than a mention of one.
# "Weeks of it is not a bad day any more, and it is worth saying to a GP rather than waiting it
# out" is the answer's own advice about the person's low mood, and "the vet records are in the
# folder" is not advice about anything.
SAYS_TO_DO = re.compile(r"\b(?:worth|should|needs?|must|ring|call|see|speak|talk|book|get|go|"
                        r"make an appointment|appointment|check(?:ed)?|look(?:ed)? at)\b", re.I)


def _a_sign_not_a_step(said, person):
    """True when what comes before the named person makes the referral depend on a sign."""
    if person is None:
        return False
    before = str(said or "")[:person.start()]
    return bool(A_SIGN_MEANS.search(before) or A_SUBSET_OF_TIME.search(before))


def _a_sentence_that_names_someone(said):
    """The answer's own sentence naming somebody to contact, if it is advice and not a condition."""
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        if not verdict.NAMES_A_CLINICIAN.search(sentence):
            continue
        if verdict.FENCED_IN_SENTENCE.search(sentence):
            continue
        if _a_sign_not_a_step(sentence, A_PERSON.search(sentence)):
            continue
        if SAYS_TO_DO.search(sentence):
            return sentence
    return ""


def _the_call(said):
    """The instruction in the answer that names somebody to contact, and who it names."""
    sentence = verdict._the_referral_sentence(said)
    person_in_it = A_PERSON.search(sentence) if sentence else None
    if sentence and (person_in_it is None or _a_sign_not_a_step(sentence, person_in_it)):
        # The sentence the referral reading picked names nobody ("Falls are usually several small
        # things adding up ...") or puts the referral behind a sign the person has not said they
        # have; either way the instruction is somewhere else in the answer.
        sentence = ""
    if not sentence or verdict._referral(said) is None:
        # No unconditional referral: the answer fenced it ("see a doctor if it lasts three weeks"),
        # and the condition is the reply to this line, not an instruction to see anybody. A
        # sentence that plainly names somebody and plainly says to go is still advice, and that is
        # the second reading: the low-mood answer's "it is worth saying to a GP rather than waiting
        # it out" is not written as an instruction and is the answer to this line all the same.
        sentence = _a_sentence_that_names_someone(said)
        if not sentence:
            return "", None
    text = str(sentence).strip()
    call = text
    head = text.split(";")[0].strip()
    if A_PERSON.search(head):
        call = head
    # A sentence that still runs long is cut after the person is named, never before: the answer
    # "For an ordinary headache, water, a dark quiet room ... then take it to a pharmacist" cut at
    # its first comma names nobody, and the reply was "Yes, pharmacist. For an ordinary headache."
    if len(call.split()) > A_LONG_CALL:
        person = A_PERSON.search(call)
        tail = call[person.end():] if person else ""
        breaks = [tail.index(mark) for mark in (",", ":", ";") if mark in tail]
        if breaks:
            call = call[:person.end() + min(breaks)].strip()
    call = call.rstrip(" .;:,")
    if not call or not A_PERSON.search(call):
        return "", None
    return call[0].lower() + call[1:], A_PERSON.search(call)


def reply_for(text, memory):
    """The reply to a bare "do i need to see someone", or None."""
    if not ASK.match(_clean(text)):
        return None
    said = _the_answer_in_hand(memory)
    if not said:
        return None
    call, person = _the_call(said)
    if not call or person is None:
        # The answer fenced its referral, so the condition is what answers a bare doubt about it.
        return _the_condition_reply(said, memory) or None
    named = " ".join(person.group(0).split())
    on_the_phone = named.strip("the ").lower() in ("999", "911", "111", "112")
    a_place = on_the_phone or bool(A_PLACE.match(named))
    if a_place:
        # A place or a number is nobody to name first, and nobody for "them" to stand in for.
        said_again = call
    elif not AN_OBJECT_OF.search(call[:person.start()]):
        # The mention is not the object of an instruction ("an ambulance or a doctor rather than
        # wait"), so the answer's own sentence is kept as it was written.
        said_again = call
    else:
        # The mention inside the instruction becomes a pronoun, because the reply has just named
        # the person: "Ring your vet with the dog's weight" -> "Ring them with the dog's weight".
        # A mention that is the thing to book is not a pronoun's job ("the next step is a GP
        # appointment" would become "them appointment"), so it takes "an appointment" instead.
        after = call[person.end():]
        place = re.match(r"\s*(appointments?|visits?|checks?)\b", after)
        if place:
            noun = place.group(1)
            pronoun = ("an appointment" if noun.startswith("appointment")
                       else "a " + noun.rstrip("s"))
            said_again = (call[:person.start()].rstrip() + " " + pronoun
                          + after[place.end():].rstrip()).strip()
        else:
            said_again = (call[:person.start()].rstrip() + " them "
                          + after.lstrip()).strip()
    # A number is not somebody to name in front of the instruction: "The answer named one: 999"
    # is a strange thing to read over an emergency. The answer's own sentence says it.
    pool = ON_THE_PHONE_LINES if on_the_phone else PLACE_LINES if a_place else SOMEONE_LINES
    line = pick(pool, memory, call).replace("{person}", named)
    said_again = said_again[:1].upper() + said_again[1:] + "."
    return line.replace("{call}", said_again).replace("{call_lower}", said_again[:1].lower()
                                                       + said_again[1:])


def replies_to_a_who_to_see(text, memory):
    """True when this file has the line, for the module that declares the claim."""
    try:
        return bool(reply_for(text, memory))
    except Exception:  # noqa: BLE001 - a reading that cannot run claims nothing
        return False
