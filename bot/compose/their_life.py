"""A particular of the person's own life is theirs to say, and no search can find it.

"I have a sister in Cork" / "what does she do", "do i like fish", "how long is she likely to be
in" - main answered all of them with the search hedge ("I don't know enough to answer that
honestly. A search should sort you out quickly"). A search cannot say what somebody's sister does
for a living, whether a person likes fish, or how long a ward will keep somebody in: the only
places those facts live are the person in front of the bot and the people around them. A pointer
at a search page tells them to go and look for something nobody has written down.

What IS honest here is short: the bot has not met them and has no page to read, so it says that
in a few words and asks for the one thing it needs - and it keeps what it is told for the rest of
the chat, which is the half it can really do.

Four kinds, all of them a question with no source but the people in it:
  - "taste"  - their own like or dislike ("do i like fish", "would i like oysters")
  - "work"   - what somebody they know does ("what does she do", "whats she like")
  - "stay"   - how long somebody will be in hospital, or away ("how long is she likely to be in")
  - "theirs" - any other particular of a person they know ("who is my friend coming with")

An ask for an idea about them is not one of the four either: "what could she build for the
project", "what can she take to school", "what does she need to get better" want a suggestion,
and this reader has one answer - that the person would know better - which is no help at all.

An age, a name or a place about one of their people is not read here: @scarlet-bat's
`bot/compose/untold.py` (#8690) answers those three shapes ("how old is she", "whats her name",
"where does he live"), and two readers on one turn would only fight over it.

It reads only the bare question, and it is called only where the composer's own reply was the
search hedge, so a card that answers, a thread that remembers, the records a person can only see
themselves (bot/compose/fallback.py, the own-record families) and every safety answer keep their
turn. A fact said earlier in the chat is the memory store's, not this: if the person has already
told the bot what they asked about, the thread answers it before the fallback is reached.
"""

import re

# The line has to be a short question with the person in it - "how old is he", "what does she do".
TOO_LONG = 12

# --- their own taste -----------------------------------------------------------------------
# "do i like fish" is a person thinking aloud about a thing they cannot look up; the bot has
# never eaten with them. "would i like oysters" and "did i like it" are the same ask.
TASTE = re.compile(
    r"^(?:so |and |but |ok |okay )?(?:do|did|would|will|should)\s+i\s+"
    r"(?:actually\s+|even\s+|really\s+|still\s+|probably\s+|think\s+i\s+)?"
    r"(?:like|love|enjoy|hate|want|fancy|prefer|get\s+on\s+with)\b", re.I)

# --- somebody they know --------------------------------------------------------------------
# A relation word makes the person theirs, so "how old is my mum" reads even with no thread.
RELATION = (r"(?:mum|mom|mam|dad|father|mother|son|daughter|child|kid|boy|girl|baby|sister|"
            r"brother|sibling|friend|mate|boss|manager|partner|husband|wife|boyfriend|"
            r"girlfriend|fianc\w*|nan|nana|gran|granny|grandma|grandad|grandpa|aunt|auntie|"
            r"uncle|cousin|niece|nephew|neighbour|neighbor|landlord|landlady|carer|colleague|"
            r"coworker|in-?laws?|stepson|stepdaughter|stepsister|stepbrother|ex|flatmate|"
            r"housemate|roommate|tutor|teacher|dog|cat|puppy|kitten|vet)")
# The person in the line: a relation of theirs, or a pronoun bound to one said a moment ago.
THEM = (r"(?:(?:my|our|his|her|their)\s+" + RELATION + r"|she|he|they|him|her|them)")

# The age, the name and the place of somebody they know are @scarlet-bat's `untold.py` (#8690),
# so a line asking any of the three is left to it even where this reading would fit.
AN_AGE_NAME_OR_PLACE = re.compile(r"\bhow\s+old\b|\bname\b|\bwhere\b", re.I)
WORK = re.compile(r"\bwhat\s+(?:does|do|did)\s+" + THEM + r"\s+(?:do|work\s+as)\b"
                  r"|\bwhats?\s+" + THEM + r"\s+like\b"
                  r"|\bwhat\s+is\s+" + THEM + r"\s+like\b", re.I)
# Any other particular of theirs - "who is my friend coming with", "what is she like", "where is
# my son staying" - is the same wall: the bot has never met them. It is read only where the
# composer's reply is the search hedge, so a card that answers (a sick relative, a wedding invite,
# a school term) keeps its turn.
# The auxiliaries are the ones that ask after a fact. "can", "could", "will", "would" and "might"
# in this position ask for an idea instead: "what could she build for the project" and "what can
# she take to school for lunch" want a suggestion, and "that is yours to know" is no answer to a
# parent asking what to pack.
ABOUT_THEM = re.compile(
    r"\b(?:who|what|where|when|which|how(?:\s+\w+)?)\s+(?P<about>(?:\w+\s+){0,2})"
    r"(?:is|was|are|were|does|did|do|has|have)\s+" + THEM + r"\b", re.I)
# A question about a thing the person has already put in the chat is the thread's to repeat, not a
# particular nobody can know: "my daughter starts year 3 in september" and then "and what year is
# she going into" was answered "I've never met them, tell me and I'll keep it" - to somebody who
# had told the bot the year one turn earlier. So the noun the question turns on is looked for in
# the earlier turns first, and if it is there this reader leaves the line to the memory store.
ALREADY_SAID = re.compile(r"\b[A-Za-z]{4,}\b")
STOP_ABOUT = frozenset("what whats which when where who whom whose does did have has about going "
                       "doing being their there these those".split())
# A person and a verb of doing is advice about them rather than a fact of theirs: "what does she
# need to get better" is a request for a suggestion about a sick parent, and the coldest reply in
# the file ("tell me, then") is the wrong one. "do" is not in this list because "what does she do"
# is the work reader's, and that one is a fact.
A_NEED_OF_THEIRS = re.compile(
    r"\b" + THEM + r"\s+(?:need|needs|want|wants|take|takes|build|builds|make|makes|cook|"
    r"cooks|wear|wears|bring|brings|give|gives|try|tries|use|uses|buy|buys|eat|eats|say|says|"
    r"tell|tells|get|gets|say\s+to|do\s+about)\b", re.I)

STAY = re.compile(
    r"\bhow\s+long\s+(?:is|are|will|would|might|could|does|do)\s+" + THEM + r"\s+"
    r"(?:(?:likely|going|expected|probably|meant)\s+to\s+)?(?:be\s+)?(?:in|staying|stay|away|"
    r"off|be\s+off|be\s+in|have\s+to\s+stay|need\s+to\s+stay)\b"
    r"|\bhow\s+long\s+(?:is|are)\s+(?:the\s+)?(?:course|treatment|recovery|stay|operation)"
    r"\s+(?:going\s+to\s+)?(?:take|last)\b", re.I)
# A person who is missing is not a particular to be asked about: that is the safety modules' line
# and a question back ("I've not met them") would be the worst answer in the file.
MISSING = re.compile(r"\b(?:missing|lost|gone|disappeared|found|ran\s+off|run\s+off|"
                     r"not\s+come\s+home|havent\s+come\s+home|hasnt\s+come\s+home)\b", re.I)
# Where somebody is at this minute is not a particular to be asked about either: the bot cannot
# know it, and "I've not met them, tell me" is no answer to a person wondering where their son is.
WHERE_THEY_ARE = re.compile(r"\bwhere(?:'s|\s+is|\s+are|\s+was|\s+were)\s+" + THEM + r"\b", re.I)
# A pronoun needs somebody of theirs said in the last few turns, or it is about a stranger and
# "how old is she" could be a fact the bot does know (a singer, an actor, the person in the news).
A_PRONOUN = re.compile(r"\b(?:she|he|they|him|her|them)\b", re.I)
SAID_WHO = re.compile(r"\b(?:my|our|his|her|their)\s+" + RELATION + r"\b|\b(?:mum|dad|son|"
                      r"daughter|sister|brother|friend|mate|partner|husband|wife|nan|gran|"
                      r"boss|colleague|neighbour)\b", re.I)

# --- what is not this ---------------------------------------------------------------------
# The records only they can see, and the things with a page of their own: a policy, a booking, a
# balance, the date on a letter, opening hours. Those are read elsewhere (the own-record
# families in the fallback, the venue clock); a search pointer is wrong for them too, but the
# answer is the record's name, not a question back.
NOT_THIS = re.compile(
    r"\b(?:excess|booking|reference|policy|premium|prescription|appointment|balance|account|"
    r"order|invoice|bill|refund|renewal|renew|due\s+date|expiry|expires|warranty|guarantee|"
    r"membership|subscription|statement|receipt|tracking|delivery|parcel|form|deadline|"
    r"opening|closing|open|close|closed|hours|times|timetable|train|bus|flight|"
    r"what\s+time|"
    r"cost|price|how\s+much)\b", re.I)
# "what was it i said", "which shift pattern was it i said" is the chat's own memory, not a fact
# about their life: the thread reader answers it, and a question back would read as a bot with no
# memory at all.
RECALL = re.compile(r"\b(?:was\s+it|which\s+(?:\w+\s+)?was\s+it|what\s+did\s+i\s+say|"
                    r"again\b.*\bwhat|remind\s+me\s+what)\b", re.I)
A_HOW_TO = re.compile(r"\bhow\s+(?:do|does|did|can|could|should)\s+(?:i|you|we)\b", re.I)

PROSE = {
    "taste": (
        "That one's yours, not mine: I can't know what you like from here. What does your gut say?",
        "No way for me to know that, sorry - only you can say. What is your instinct telling you?",
        "I'd only be guessing, and you'd know in a second. What do you reckon?",
    ),
    "work": (
        "I've not met them, so I can't say what they do. What do they do?",
        "No idea, sorry - nobody has told me. What do they do for a living?",
        "Not a thing I could know. Tell me about them and I'll keep it straight from here: what "
        "do they do for a living?",
    ),
    "theirs": (
        "I've never met them, so I've nothing on that one - you'd know better than any page. "
        "Tell me and I'll keep it for the rest of our chat.",
        "That's yours to know and mine to be told. What's the answer?",
        "No idea, sorry - nobody has introduced us. Tell me and it stays here with me.",
    ),
    "stay": (
        "Only the people looking after them can say that - ask the nurse on the ward and they "
        "will give you a rough day. How are they in themselves?",
        "Nobody here can say how long they'll keep them in. The staff on the ward can, and the "
        "desk will ring through for you. How are they doing?",
        "That's the ward's call, not mine - the nurse looking after them knows, and it is one "
        "question at the desk. How is she in herself?",
    ),
}


def _bare(text):
    return re.sub(r"\s+", " ", (text or "").strip()).strip(" .!,").lower()


def _a_thing_already_said(match, memory):
    """True when the noun the question turns on was said by the person earlier in the chat."""
    about = (match.group("about") or "").strip()
    words = [w for w in ALREADY_SAID.findall(about.lower()) if w not in STOP_ABOUT]
    if not words:
        return False
    # the question itself is the last turn, so it is not evidence of anything
    turns = [str(t.get("user") or "").lower() for t in (memory.get("turns") or [])
             if isinstance(t, dict)]
    earlier = " ".join(turns[:-1])
    return any(w in earlier for w in words)


def _somebody_of_theirs(memory):
    """"she", "he" and "they" are theirs when the last few turns named somebody they know."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)][-6:]
    return any(SAID_WHO.search(str(t.get("user") or "")) for t in turns)


def reads(text, memory=None):
    """The kind of particular this is - "taste", "work", "stay", "theirs" - or None."""
    line = _bare(text)
    if not line:
        return None
    if len(line.split()) > TOO_LONG:
        return None
    if NOT_THIS.search(line) or RECALL.search(line) or A_HOW_TO.search(line):
        return None
    if AN_AGE_NAME_OR_PLACE.search(line):
        return None
    if MISSING.search(line) or WHERE_THEY_ARE.search(line):
        return None
    if A_NEED_OF_THEIRS.search(line):
        return None
    if TASTE.search(line):
        return "taste"
    for kind, pattern in (("work", WORK), ("stay", STAY), ("theirs", ABOUT_THEM)):
        found = pattern.search(line)
        if not found:
            continue
        if found.re is ABOUT_THEM and _a_thing_already_said(found, memory or {}):
            return None
        if A_PRONOUN.search(line) and not re.search(
                r"\b(?:my|our|his|her|their)\s+" + RELATION, line, re.I):
            if not _somebody_of_theirs(memory or {}):
                return None
        return kind
    return None


def reply_for(text, memory):
    """The honest line and the one question, or None when this is not the ask."""
    kind = reads(text, memory)
    if not kind:
        return None
    lines = PROSE[kind]
    turns = len([t for t in (memory.get("turns") or []) if isinstance(t, dict)])
    return lines[turns % len(lines)]
