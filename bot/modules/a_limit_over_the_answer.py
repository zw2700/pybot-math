"""A limit of theirs, said over an answer already given, changes that answer - it is not a receipt.

People give the answer a constraint once they have heard it, in the shortest way they can:

    the kitchen tap is dripping / we rent the flat     -> "Right, so you rent. What are you
                                                          trying to sort out?"
    i want to visit my sister / we have no car          -> "You have no car - noted."
    the wedding is in italy / its in a field            -> "I'm listening - say more if it helps."

Every one of those is the bot taking the fact and handing the conversation back. Nobody is trying
to sort out what they just asked about: they are telling the bot what the answer has to work
around. A friend does the one thing the limit changes and gets on with the plan.

So this module answers **only** the turn that states the limit, and only when there is an answer
above it to change: the answer's own first move is repeated with the limit already in it.

The answer in hand is `memory["last_answer"]`, which only `bot/modules/answers.py` writes, so this
module can only ever fire after a card from that module: a limit said after a reply from anywhere
else ("whats the weather like tomorrow" / "we have no car") is left to the greeting it gets today.
That is a real narrowing and it is the honest one - the limit needs an answer to change.

It also has to be about the same kind of thing as the limit. That is read from the answer's own
`keys`, not from its prose: "water" is in a balcony's word list and in "350ml warm water" of every
bread recipe, so matching the prose told a bread answer a balcony was enough for it. One of the
kind's words among the answer's keys is enough; a word in the prose needs a second one beside it,
because one shared word in a sentence is a coincidence.

Everything else is left alone: a limit opening the conversation belongs to
`bot/compose/circumstance.py`, a limit that is a question ("can we do it by train") is the answers
lane's, and a line with anything else in it keeps its own reading.

Two limits are deliberately not here. "money is tight" and "how long have you got" are answered by
cards of their own, and repeating the answer's first move in front of them is the answer given
again with a lead-in - the arbiter is right to give the turn to the card. The five kinds below are
the ones where the limit changes *whose job it is* or *where the thing goes*, which the answer in
hand cannot say for itself.
"""

import re

PRIORITY = 500

# The words people leave off the front of a limit line: "we only rent", "honestly we have no car".
_LEAD = re.compile(r"^(?:well|ok|okay|so|oh|ah|and|but|honestly|actually|yeah|sorry|"
                   r"anyway|course|of\s+course)\b[\s,]*", re.I)

# What ends a limit line without adding anything: "we rent the flat tbh".
_TAIL = re.compile(r"(?:\s+(?:tbh|tho|though|anyway|actually|really|literally|honestly|"
                   r"i\s+suppose|i\s+guess|still|also|too|by\s+the\s+way|btw|atm|"
                   r"at\s+the\s+moment|lol|ha|haha|so\s+yeah|though|mate|dude|sadly|"
                   r"unfortunately))+$", re.I)

# A line that asks is somebody else's turn.
_ASKS = re.compile(r"\?|^\s*(?:what|how|when|where|why|who|can|could|should|would|do|does|did|"
                   r"is|are|was|were|will|shall|any)\b", re.I)


def _clean(text):
    """The line with the tone and the lead-in taken off, lower case, no end punctuation."""
    low = " ".join(str(text or "").replace("\u2019", "'").split()).strip(" .!,")
    for _ in range(3):
        before = low
        low = _LEAD.sub("", low)
        low = _TAIL.sub("", low)
        if low == before:
            break
    return low.lower().strip(" .,!")


# Each limit: the shapes it is said in, the words its answer would be about, and the sentence that
# says what the limit changes - three of them, so a conversation that meets the same limit twice
# does not hear the same lead-in.
_KINDS = (
    ("rent", (
        re.compile(r"^(?:we|i)\s*(?:just\s+)?rent(?:ing)?(?:\s+(?:a|an|the|our|this)\s+"
                   r"(?:flat|house|place|home|bungalow|room|council\s+flat))?$"),
        re.compile(r"^(?:we|i)\s*(?:are|re)\s+(?:renting|in\s+a\s+rented|renters?)$"),
        re.compile(r"^(?:its|it\s+is)\s+(?:a\s+)?(?:rented|rental|council|housing\s+association)"
                   r"(?:\s+(?:flat|house|place|home))?$"),
        re.compile(r"^(?:we|i)\s+(?:are|re)?\s*(?:just\s+)?tenants?$"),
        re.compile(r"^(?:we|i)\s+(?:dont|do\s+not)\s+own\s+(?:it|the\s+flat|the\s+house|our\s+home)$"),
    ), (
        "repair", "fix", "damp", "boiler", "radiator", "tap", "leak", "leaking", "dripping",
        "drip", "wall", "ceiling", "paint", "heating", "plumb", "roof", "floor", "fuse",
        "washer", "mould", "mold", "window", "door", "drains", "toilet", "shower", "bath",
        "landlord", "carpet", "electric", "socket", "gutter", "chimney",
    ), (
        "Then it's your landlord's to fix, not yours - but do the free bit first: {move}",
        "Renting puts that on them: report it in writing, and meanwhile {move_lower}",
        "Right, so it's their job. What you can do now: {move_lower}",
    )),
    ("no_car", (
        re.compile(r"^(?:we|i)\s*(?:have|ve)\s+(?:got\s+)?no\s+car$"),
        re.compile(r"^(?:there\s+is\s+)?no\s+car(?:\s+here)?$"),
        re.compile(r"^(?:we|i)\s*(?:dont|do\s+not|can\s*not|can't|cant)\s*drive$"),
        re.compile(r"^(?:we|i)\s*(?:dont|do\s+not)\s+have\s+(?:a\s+)?car$"),
        re.compile(r"^(?:its|it\s+is)\s+(?:a\s+)?no\s+car\s+(?:household|family)$"),
    ), (
        "drive", "driving", "car", "travel", "journey", "get there", "getting there", "route",
        "station", "bus", "train", "coach", "parking", "park", "trip", "visit", "ferry",
        "flight", "fly", "airport", "motorway",
    ), (
        "Then go by train or bus instead of driving - and the rest of it still holds: {move_lower}",
        "No car changes the how, not the plan: {move_lower}",
        "Then book the train rather than drive. Everything else stands: {move_lower}",
    )),
    ("only_a_balcony", (
        re.compile(r"^(?:we|i)\s*(?:only|just)\s+(?:have|ve\s+got|got)\s+(?:a\s+|one\s+)?"
                   r"(?:small\s+)?(?:balcony|windowsill|window\s+box|yard|patio|terrace|yard)$"),
        re.compile(r"^(?:its|it\s+is)\s+(?:just\s+)?(?:a\s+)?(?:balcony|windowsill|window\s+box)$"),
    ), (
        "plant", "sow", "sowing", "grow", "growing", "pot", "pots", "garden", "soil", "seed",
        "seeds", "compost", "bed", "patch", "allotment", "water", "sun", "shade", "herbs",
        "tomato", "tomatoes", "flower", "flowers", "bulb",
    ), (
        "Then keep it all in pots - that's the part that matters: {move_lower}",
        "A balcony is enough for that: {move_lower}",
        "Then it's pots on the balcony rather than a bed: {move_lower}",
    )),
    ("no_garden", (
        re.compile(r"^(?:we|i)\s*(?:dont|do\s+not)\s+have\s+(?:a\s+|any\s+)?"
                   r"(?:garden|outside\s+space|yard|plot|allotment)$"),
        re.compile(r"^(?:no|without\s+a)\s+(?:garden|outside\s+space|allotment)$"),
    ), (
        "plant", "sow", "sowing", "grow", "growing", "pot", "pots", "garden", "soil", "seed",
        "seeds", "compost", "bed", "patch", "allotment", "water", "sun", "shade", "herbs",
        "tomato", "tomatoes", "flower", "flowers", "bulb",
    ), (
        "Then keep it all in pots or a window box - that's the part that matters: {move_lower}",
        "No garden is fine for that: {move_lower}",
        "Then it's containers rather than a bed: {move_lower}",
    )),
    ("a_nervous_animal", (
        re.compile(r"^(?:hes|he\s+is|shes|she\s+is|its|it\s+is)\s+(?:a\s+)?(?:rescue|rescued)"
                   r"(?:\s+(?:and\s+)?(?:quite\s+|very\s+|really\s+)?(?:nervous|anxious|shy|"
                   r"scared|terrified|timid))?$"),
        re.compile(r"^(?:hes|he\s+is|shes|she\s+is|its|it\s+is)\s+(?:quite\s+|very\s+|really\s+)?"
                   r"(?:nervous|anxious|scared|terrified|timid|shy)$"),
        re.compile(r"^(?:hes|shes|its)\s+(?:a\s+)?rescue$"),
    ), (
        "dog", "dogs", "puppy", "cat", "cats", "kitten", "lead", "leash", "walk", "walks",
        "train", "training", "scratch", "scratching", "bark", "barking", "sofa", "litter",
        "collar", "harness", "garden", "vet", "animal", "rescue", "puppy",
    ), (
        "Then go slower than that and keep every go short: {move_lower}",
        "A nervous rescue needs that done in small doses: {move_lower}",
        "Then take it at their pace - the first step is the same: {move_lower}",
    )),
)

# How the answer's own move is cut down to something that can sit in a sentence.
# The verbs a line of advice starts its move with, so the why in front of it can be dropped.
_INSTRUCTION = re.compile(r"^(?:sow|plant|prune|feed|mulch|pot|repot|thin|stake|tie|harvest|"
                          r"practise|practice|learn|watch|read|listen|repeat|spend|save|budget|"
                          r"compare|download|install|print|wear|cut|freeze|store|label|"
                          r"turn|put|take|use|keep|start|add|set|get|open|close|ask|book|"
                          r"check|try|make|give|water|clean|wash|report|write|stand|hold|"
                          r"cut|mix|place|leave|move|cover|wrap|soak|strip|sand|fill|fit|"
                          r"call|text|email|ring|go|walk|run|sit|lie|rest|eat|drink|buy|"
                          r"pick|choose|measure|weigh|boil|fry|bake|simmer|stir|season|"
                          r"remove|replace|tighten|loosen|unplug|switch|plug|drain|bleed)\b",
                          re.I)

# Words a cut can leave on the end of a half-said list or phrase.
_DANGLING = frozenset(("and", "or", "with", "a", "an", "the", "of", "to", "for", "in", "on",
                       "at", "plus", "then", "but", "so", "your", "my", "its"))

# The word a clause carries in front of its verb: "so put a post there", "then turn it off".
_JOINER = re.compile(r"^(?:so|and|then|but|just|really|also|first|afterwards?)\s+", re.I)

_LEAD_INS = re.compile(r"^(?:same\s+as\s+before|the\s+first\s+thing\s+to\s+do|"
                       r"first\s+thing|so|right|okay|ok|then)\s*:\s*", re.I)


def _a_limit(text):
    """`(kind, words, leads)` for a line that is only a limit, or None."""
    low = _clean(text)
    if not low or _ASKS.search(low):
        return None
    for kind, shapes, about, leads in _KINDS:
        for shape in shapes:
            if shape.match(low):
                return kind, about, leads
    return None


def _the_answer(memory):
    """The answer in hand, while the chat is still about it.

    It is `memory["last_answer"]`, which only `bot/modules/answers.py` writes, so this module can
    only ever fire after a card from that module: a limit said after a reply from anywhere else
    ("whats the weather like tomorrow" / "we have no car") is left to the greeting it gets today.
    That is a real narrowing, and the record's own `keys` are what say whether the answer is about
    the same kind of thing as the limit.
    """
    if not isinstance(memory, dict):
        return None
    record = memory.get("last_answer")
    if not isinstance(record, dict) or not isinstance(record.get("reply"), str):
        return None
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return None
    turn = record.get("turn")
    if not isinstance(turn, int) or turn < 0 or len(turns) - 1 - turn > 2:
        return None
    return record


def _what_the_answer_is_about(record):
    """The words the answer is about, from the record's own keys.

    Not the prose: "water" is in a balcony's word list and in "350ml warm water" of every bread
    recipe, so a bread answer was being told a balcony is enough for it. The keys are the subject
    the card answered.
    """
    keys = record.get("keys") if isinstance(record, dict) else None
    if isinstance(keys, str):
        keys = keys.split()
    if not isinstance(keys, (list, tuple, set, frozenset)):
        return set()
    return {str(key).lower() for key in keys}


def _the_answer_is_about(record, about):
    """True when the answer is about the same kind of thing as the limit.

    One of the kind's words in the answer's own keys is enough, because the keys are the subject
    the card answered. The prose needs two: "water" is in every bread recipe and in a balcony's
    word list, so one shared word in a sentence is a coincidence, while two of them ("sow",
    "pot", "sun") make the answer the one the limit is about.
    """
    if not about:
        return True
    if any(word in _what_the_answer_is_about(record) for word in about):
        return True
    low = record["reply"].lower()
    return len({word for word in about if word in low}) >= 2


# A move said back to somebody is a whole sentence: the card's own first instruction, to the end
# of the sentence it is in, and only cut short if that sentence is a paragraph.
_MOVE_WORDS = 45
_MOVE_CUT = 34


def _the_move(answer):
    """The answer's first instruction, said back as a whole sentence, or "".

    A clause is not a sentence: "turn the water off at the isolating valve under the sink, take the
    handle off" stops before the part that finishes the job ("... and take it to a plumbing
    merchant to match it"), and a person reads an instruction that breaks off. So the move runs on
    to the end of the sentence it starts in. Only a sentence too long to say back is cut, and then
    at a whole clause with the full stop put back on.
    """
    text = " ".join(answer.replace("\u2014", "- ").split())
    text = _LEAD_INS.sub("", text)
    first = re.split(r"(?<=[.!?])\s", text)[0].strip(" .;:,-")
    if not first:
        return ""
    # The instruction usually comes after the explanation ("A dripping tap is nearly always a worn
    # washer or cartridge: turn the water off ..."), so it is the colon's tail that is said back -
    # unless the head itself opens with the verb ("Turn the water off at the valve: then ...").
    if ":" in first:
        head, tail = first.split(":", 1)
        if len(tail.split()) >= 4:
            first = tail.strip()
    parts = [part.strip() for part in re.split(r"[,;]\s", first) if part.strip()]
    # A clause that opens with a verb is the instruction; the clauses before it are the why.
    if parts and not _INSTRUCTION.match(_JOINER.sub("", parts[0])):
        found = False
        for index, part in enumerate(parts[1:], 1):
            if _INSTRUCTION.match(_JOINER.sub("", part)):
                parts = parts[index:]
                found = True
                break
        if not found:
            # No clause in the answer tells anyone to do anything - it is all why ("they carry the
            # bait back to the nest and that is what kills them"). Said again with a lead-in it
            # promises a change and repeats the explanation, so the turn is left to what answers
            # it today.
            return ""
    parts = [_JOINER.sub("", part) for part in parts]
    whole = [part for part in parts]
    # As much of the sentence as can be said back, but never half of a clause.
    out = []
    for part in whole:
        if out and len(" ".join(out + [part]).split()) > _MOVE_WORDS:
            break
        out.append(part)
    if len(out) > 1 and len(" ".join(out).split()) > _MOVE_CUT:
        # A sentence too long to repeat in full: take whole clauses up to the cut, and no more.
        kept = []
        for part in out:
            if kept and len(" ".join(kept + [part]).split()) > _MOVE_CUT:
                break
            kept.append(part)
        out = kept or out[:1]
    cut = ", ".join(out) if out else first
    cut = cut.strip(" ,;:-.")
    # Nothing left dangling: "check the site for the trains, buses and" is not a sentence.
    while cut and cut.split()[-1].lower().strip(" ,.;:-") in _DANGLING:
        cut = " ".join(cut.split()[:-1])
    cut = cut.strip(" ,;:-.")
    # Never hand back half a bracket.
    if cut.count("(") > cut.count(")"):
        cut = cut[:cut.index("(")].strip(" .;:-, ")
    if not cut:
        return ""
    # Said back as a sentence of its own: the card's first word capitalised and a full stop on it.
    return cut[0].upper() + cut[1:] + "."


def TAKES_AS_IT_COMES(text, memory):
    """This line is the limit itself, and there is an answer above it for the limit to change.

    Declared rather than won on PRIORITY: the answers lane holds a card for a limit said on its
    own (a limit said with no answer above it is a card in `bot/compose/circumstance.py`), and that
    card answers a line nobody asked as a question. The limit is not a new topic - it is a change
    to the answer already given.
    """
    if not isinstance(text, str):
        return False
    return _a_limit(text) is not None and bool(_the_answer(memory))


def observe(text, memory):
    """Nothing to keep: the limit is answered against the answer above it, every time."""
    return None


def respond(text, memory):
    """The answer in hand with the limit worked into it, or None."""
    if not isinstance(text, str):
        return None
    read = _a_limit(text)
    if read is None:
        return None
    kind, about, leads = read
    record = _the_answer(memory)
    if record is None:
        return None
    answer = record["reply"]
    low = answer.lower()
    # The answer has to be about the same kind of thing as the limit: its own subject words have
    # to hold one of the kind's words, which its prose is no use for.
    if not _the_answer_is_about(record, about):
        return None
    move = _the_move(answer)
    if not move:
        return None
    # The answer already said the limit itself ("if you rent, tell the landlord"): nothing to add.
    if kind == "rent" and "landlord" in low:
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    pick_from = len(turns) if isinstance(turns, list) else 0
    lead = leads[pick_from % len(leads)]
    reply = lead.format(move=move, move_lower=move[:1].lower() + move[1:])
    return " ".join(reply.split())
