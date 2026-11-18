"""A question about somebody's care is the ward's to answer, not a search.

On main the questions families actually ask while somebody is in hospital all reach the
composer's search hedge - "I don't know enough to answer that honestly. A search should sort you
out quickly":

    how long will she be in hospital        -> the search hedge
    when can she come home from hospital    -> "That's beyond what I know well, sorry"
    what ward is she on                     -> the search hedge
    is he allowed visitors                  -> the search hedge
    what time is her operation              -> the search hedge
    has she had the scan results yet        -> "That's beyond what I know well, sorry"

No search settles any of them. How long a stay is, when somebody is discharged, which ward they
are on, when the theatre list runs and whether the results are back are all in that person's
notes, and the only people holding the notes are the ones looking after them. Telling somebody
to look it up sends them away from the one place that can answer, which is the failure STYLE.md's
"Not knowing, honestly" is written against: say what the bot cannot do, then name who knows.

So every reply does two things and nothing else: it says plainly that nothing here can see the
notes, and it names the ward and the one thing to do - ring, ask for the nurse looking after them
and put the question as it was put here. Nothing is guessed: not a number of days, not a ward
name, not a visiting hour. The reading is the same for all of them because the reply is the same:
this is somebody else's patient and the notes are not here.

What is read, in the line, is

  - somebody it is about: he/she/they, or "my/our/his/her/their <person>" (mum, dad, son,
    daughter, wife, husband, partner, gran, grandad, sister, brother, friend, baby, ...), or the
    speaker with a place of care in the line - "how long will i be in hospital" is their own
    notes as much as anybody's;
  - a place or a person of care - hospital, ward, hospice, care home, clinic, unit, theatre,
    consultant, doctor, nurse, midwife - or one of the care facts that live in the notes: the
    operation, the scan, the results, the discharge, the visitors;
  - and a practical ask about it: how long, when, what time, which, where, whether they are in
    or out, have they had, can i, is he allowed.

It stands down where another reading owns the line, because those are answers and this file is
the last resort: a symptom or an injury ("is her chest infection serious", "her wound is
bleeding") is the health cards', a how-to about doing something ("should i drive after the
operation") is knowledge the bot has, a thing of theirs to tell ("how did the scan go") is
how_it_went.py, and a pet's stay is the vet's line, which the composer already has. Like the
other readers of a hedge, `bot/modules/greeting.py` asks this only when the composer has nothing
but a shrug, so a line with an answer of its own never reaches this file.
"""
import re

# Somebody the line is about, other than the person typing.
PERSON = re.compile(
    r"(?<![a-z])(?:he|she|they|him|her|them|his|their)(?![a-z])"
    r"|(?<![a-z])(?:my|our|his|her|their)\s+(?:mum|mom|mother|dad|father|son|daughter|child|kid|"
    r"wife|husband|partner|brother|sister|gran|granny|grandma|grandad|grandpa|nana|nan|aunt|"
    r"uncle|cousin|friend|mate|neighbour|neighbor|baby|boy|girl|lad|boss|colleague)(?![a-z])",
    re.I)
# The person typing. It carries the question only with a place of care in the line: "how long will
# i be in hospital" is their own stay and their own notes, while "should i drive after the
# operation" is a how-to the knowledge base answers.
SELF = re.compile(r"(?<![a-z])(?:i|me|my|mine|myself)(?![a-z])", re.I)
# The place, or the person, whose notes hold the answer.
PLACE = re.compile(
    r"(?<![a-z])(?:hospital|ward|hospice|care home|nursing home|residential home|clinic|"
    r"infirmary|a&e|theatre|theatres)(?![a-z])", re.I)
STAFF = re.compile(
    r"(?<![a-z])(?:consultant|doctor|nurse|midwife|anaesthetist|anesthetist|surgeon|registrar|"
    r"duty nurse)(?![a-z])", re.I)
# The care facts that are in the notes and nowhere else.
DETAIL = re.compile(
    r"(?<![a-z])(?:operation|surgery|op|procedure|scan|x-ray|xray|mri|ct scan|ultrasound|"
    r"results|test results|notes|chart|discharge|discharged|visitors|visiting|"
    r"visiting hours)(?![a-z])", re.I)
# The practical ask. A line that asks none of these is a statement, and a statement about
# somebody in hospital is met by an answer of its own (the heavy-news and sympathy pools).
ASK = re.compile(
    r"(?<![a-z])(?:how long|how soon|how many days|when|what time|what ward|what room|"
    r"what unit|what bed|what hospital|which|where|has (?:she|he|they)|have they|"
    r"is (?:she|he|they)|are they|will (?:she|he|they)|can i|can we|could i|am i allowed|"
    r"are we allowed|did they)(?![a-z])", re.I)
# A symptom or an injury belongs to the health cards, which answer with the sign to watch for.
# "The ward knows" is a shrug of a different shape where the bot has something to say.
SOMETHING_WRONG = re.compile(
    r"(?<![a-z])(?:pain|painful|hurts?|hurting|aching|aches?|sore|swollen|swelling|bleeding|bled|"
    r"fever|temperature|rash|infection|infected|vomit|vomiting|dizzy|breathless|bruise|wound|"
    r"symptom|diagnos\w*)(?![a-z])", re.I)
# A pet's stay is the vet's, and the composer already says so ("Your vet is the one to ask").
A_PET = re.compile(
    r"(?<![a-z])(?:vet|vets|veterinary|puppy|kitten|rabbit|hamster|guinea|budgie|parrot|"
    r"dog|cat|horse|pony)(?![a-z])", re.I)
# Somebody who is already home has no ward to ring: "my nan is home from hospital at last" then
# "how long until she is back on her feet" is a question about getting better at home, and sending
# somebody to a ward they have left is worse than the hedge it replaced. A discharge still to come
# ("when can he come home from hospital", "when will i get out of hospital", "when is he being
# discharged") is the ward's question, so the words are read as the having-left ones only.
HOME_AGAIN = re.compile(
    r"(?<![a-z])(?:"
    r"is (?:now )?home|are (?:now )?home|was home|were home|got home|back home|"
    r"came home|has come home|had come home|"
    r"left (?:the )?hospital|came out of (?:the )?hospital|got out of (?:the )?hospital|"
    r"out of (?:the )?hospital now|"
    r"(?<!come )(?<!coming )(?<!comes )(?<!get )(?<!getting )(?<!go )(?<!going )(?<!going to )"
    r"home from (?:the )?hospital|"
    r"(?:has|have|had) been discharged|was discharged|is discharged"
    r")(?![a-z])", re.I)
# A place read from an earlier turn belongs to that turn. "she is on the ward" then "where does he
# work" is a job question, and the ward is not in it: only a word about a stay carries the place
# across the turn - "how long will she be in for", "what room is she in", "can i stay overnight",
# "when is he being discharged". Without one the earlier line is the subject that has changed, and
# the composer's own answer for the new line stands.
A_STAY_IN_THE_LINE = re.compile(
    r"(?<![a-z])(?:in for|in there|in here|still in|be in|is (?:she|he|they) in|are they in|"
    r"staying|stay overnight|staying overnight|can i stay|"
    r"out of (?:there|hospital)|discharg\w*|visitors?|visiting|room|bed|bay|ward|"
    r"(?:coming|came|come) home|(?:going|went) home|get home|getting home|back on (?:her|his|their) feet)"
    r"(?![a-z])", re.I)
# The bot's own question is the manners pool's ("when can you come home" is not about a patient).
THE_BOT = re.compile(r"(?<![a-z])(?:you|your|yours|yourself)(?![a-z])", re.I)

# Every reply says the same two things - nothing here can see the notes, and the ward is where
# the answer is - and none of them guesses a number, a ward name or a time.
THE_WARD_KNOWS = (
    "Nobody here can see {whose} notes, so the ward is the way to find out: ring and ask for the "
    "nurse looking after {whom}, and put the question as you put it to me.",
    "That sits in {whose} notes, and nothing here can read them. Ring the ward and ask for the "
    "nurse on duty - they will tell you what is happening and what happens next.",
    "Only the people looking after {whom} can say. Ring the ward, say who you are and who you are "
    "asking about, and ask them straight.",
    "I can't see {whose} chart from here. Ring the ward and ask for the nurse looking after "
    "{whom}: they have the notes in front of them and they answer this all day.",
    "The answer is in {whose} notes, so it has to come from the ward. Ring them, ask for the "
    "nurse on duty, and say what you need to know - they can look it up while you are on the "
    "phone.",
)
# The possessive that goes with the pronoun the person is spoken of by. "you" is the person
# typing, asking about their own stay ("how long will i be in hospital").
WHOSE = {"her": "her", "him": "his", "them": "their", "you": "your"}


def _whom(said):
    """The pronoun for the person, from the words of the line: her, him, them or you."""
    if re.search(r"(?<![a-z])she(?![a-z])", said, re.I):
        return "her"
    if re.search(r"(?<![a-z])he(?![a-z])", said, re.I):
        return "him"
    # Their own stay, named with a place of care and no third person in the line.
    if not PERSON.search(said):
        return "you"
    return "them"


def _the_place_before(memory):
    """The care words of the last few turns, or "" on the first turn.

    A family talks in two parts: "my mum went into hospital last night" and then "how long will
    she be in for", "what room is she in", "can i stay overnight with her". The second turn names
    the person and the question, and the place is one turn back. Only the place is read from the
    earlier lines, never the answer, and three turns is enough for a person to have changed the
    subject.
    """
    if not isinstance(memory, dict):
        return ""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return " ".join(str(turn.get("user") or "").lower() for turn in turns[-3:])


def answer_for(text, memory=None):
    """The ward line for a question about somebody's care, or None to leave the reply alone."""
    said = " ".join(str(text or "").lower().split())
    if len(said.split()) < 3 or THE_BOT.search(said):
        return None
    # The person and the question are in this line; the place may be one turn back ("how long
    # will she be in for" after "my mum went into hospital").
    room = " ".join((said, _the_place_before(memory)))
    if A_PET.search(room) or SOMETHING_WRONG.search(room) or HOME_AGAIN.search(room):
        return None
    if not (PLACE.search(room) or STAFF.search(room) or DETAIL.search(room)):
        return None
    # Nothing of the care is in this line: it is carried from a turn before, and then the line has
    # to be about the stay rather than about something else entirely.
    if not (PLACE.search(said) or STAFF.search(said) or DETAIL.search(said)) \
            and not A_STAY_IN_THE_LINE.search(said):
        return None
    # Who it is about: somebody else, or the speaker with a place of care in the line.
    if not (PERSON.search(said) or (SELF.search(said) and PLACE.search(room))):
        return None
    if not ASK.search(said):
        return None
    whom = _whom(said)
    seed = len((memory or {}).get("turns") or []) * 31 + len(said)
    return THE_WARD_KNOWS[seed % len(THE_WARD_KNOWS)].format(whose=WHOSE[whom], whom=whom)
