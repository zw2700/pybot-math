"""The answer in the first sentence, for every answer module at once.

Two rules live here, both about the same thing: STYLE.md's "the answer in the first sentence",
read from `memory["understood"]["wants"]`. The first turns a method round when a card written for
"how long" is asked "how"; the second puts a row's own declared opening (`entry(..., lead=...)`)
in front of a card that is written for the harder question and has the plain one to answer too
(`entry(..., lead=("yesno", "Usually, yes"))`: the shape of line, then the sentence owed to it).
Both are read by the one place every knowledge row is rendered (`bot/modules/answers.py`), so a
row in any domain gets them without a module changing.

STYLE.md asks for the answer in the first sentence. A row that holds a dish holds one answer for
every way the dish is asked about, so it is written the way the clock asks for it: "About 40
minutes start to finish. Fry 500g mince hard ...". That is the answer to "how long does chilli
take" and it is not the answer to "how do i make chilli", which is the method the person came
for: read out, the first thing they get is a duration they did not ask for, and the paragraph
that tells them what to do starts in the second sentence.

So when the line asks for the method (`memory["understood"]["wants"]` is `steps`), a reply whose
opening sentence is only the total time of the job is turned round: the method leads and the
total time closes the answer, where it is still useful and no longer in the way of it. Nothing is
added, cut or reworded - the same sentence moves to the end - and every other ask is left exactly
as it is, because "how long" wants the clock first and a limit or a fault is not this file's.

The move is safe because the sentence it moves says only how long the whole thing takes: it
carries "start to finish", "from start to finish", "in total", "altogether" or "all in", so it is
a summary of the job and not one step's own time ("simmer 30 minutes" stays where it is, inside
the method it belongs to).
"""
import re

from . import fit

# The whole answer's duration said as a sentence of its own: "About 40 minutes start to finish.",
# "About 2 hours start to finish for a 2kg chicken.", "About 5 minutes start to finish, then 30
# minutes resting." A figure, a time unit, and the words that make it the total rather than a
# step's own time.
_TOTAL = re.compile(
    r"^(?:about|around|roughly|just|only|under|over|about an?|an?|a)\s*"
    r"[^.]{0,60}"
    r"\b(?:minutes?|mins?|hours?|hrs?|days?)\b"
    r"[^.]{0,60}?"
    r"\b(?:start to finish|from start to finish|in total|altogether|all in|end to end)\b",
    re.I)

# One sentence: everything up to a full stop that ends a sentence (not the dot of "1.5kg" or
# "190C." inside a number), and the rest of the reply.
_OPENING = re.compile(r"^\s*(\S.*?[.!?])\s+(\S.*)$", re.S)

# The shapes that ask for the method itself. A soft `advice` is a reply to the person's situation
# rather than a set of steps, so it is not turned round here.
_METHOD = frozenset(("steps",))

# A sentence that only says what follows. It carries a count and a noun, or points forward, and
# names no fact of its own: "Three tests, in this order.", "Two things to know.", "Here's the
# short version." A count with a verb ("Two things are true") is not this, because it says
# something; a count with no noun ("Two hours.") is an answer, not a signpost.
_SIGNPOST = re.compile(
    r"^(?:"
    r"(?:a few|a couple of|two|three|four|five|six|\d+)\s+"
    r"(?:things?|tests?|steps?|options?|ideas?|ways?|rules?|checks?|questions?|tips?|notes?|"
    r"points?|parts?)"
    r"(?:\s*,?\s*(?:in this order|to know|to try|to check|to keep in mind|first|for you|"
    r"to start with|before you start))?"
    r"|here(?:'?s| is| are)\s+(?:the|a|an|what|how|my|our|it|this)\b[^:]{0,60}"
    r"|the following\b[^:]{0,40}"
    r"|these are\b[^:]{0,40}"
    # A sentence that talks about the question or the answer instead of giving it. It carries no
    # fact, so it is not the answer whatever shape was asked for.
    r"|(?:great|good|fair|interesting|nice|lovely) question"
    r"|(?:that'?s|it'?s) (?:a )?(?:great|good|fair|interesting|nice) question"
    r"|you (?:asked|want(?:ed)? to know|were asking|are asking)\b[^:]{0,80}"
    r"|so (?:you'?re|you are) asking\b[^:]{0,80}"
    r"|the question (?:is|was)\b[^:]{0,80}"
    r"|let me (?:start|explain|answer|walk you through|take you through|think)"
    r"|i'?ll (?:start|explain|answer|walk you through|take you through)"
    r"|i can (?:help|answer|explain|tell you)"
    r")$", re.I)


def _sentences(reply):
    """The reply's sentences, in order, with their own punctuation kept."""
    text = " ".join(str(reply or "").split())
    if not text:
        return []
    out, start = [], 0
    for end in _SENTENCE_END.finditer(text):
        before = text[start:end.start()]
        if _ABBREVIATION_END.search(before):
            continue
        out.append(text[start:end.start()].strip())
        start = end.end()
    if text[start:].strip():
        out.append(text[start:].strip())
    return [sentence for sentence in out if sentence]


# A dot after one of these ends a word, not the sentence, as in `bot/compose/fit.py`.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_ABBREVIATION_END = re.compile(
    r"\b(?:e\.g|i\.e|approx|incl|etc|vs|cf|fig|dept|est|ref|tel|mr|mrs|ms|dr|prof)\.$", re.I)


def _wants_the_method(understood):
    if not isinstance(understood, dict):
        return False
    want = understood.get("wants")
    if isinstance(want, str):
        want = want.strip().lower()
    return want in _METHOD


# The line that asks how often, and the rate it is answered with. "Once a week", "every other day",
# "two or three times a week" - a phrase a sentence can open on, which is what makes it movable: a
# rate named inside a sentence about something else ("most freezers need this once or twice a
# year") is that sentence's fact and stays where it is.
_ASKS_HOW_OFTEN = re.compile(
    r"\bhow\s+(?:often|frequently)\b|\bhow\s+many\s+times\b|\bwhat\s+interval\b", re.I)
_A_RATE = re.compile(
    r"\b(?:once|twice|(?:three|four|five|six|\d+)\s+times"
    r"|every(?:\s+other)?(?:\s+\w+)?\s+(?:day|week|month|year|morning|evening|night)"
    r"|daily|weekly|monthly|yearly|nightly|fortnightly"
    r"|\d+\s+times\s+(?:a|an|per|each)\s+(?:day|week|month|year)"
    r"|(?:two|three|four|five)\s+times\s+(?:a|an|per|each)\s+(?:day|week|month|year))"
    r"(?:\s+(?:a|an|per|each)\s+(?:day|week|month|year))?\b", re.I)


def rate_first(reply, understood, line=None):
    """The rate sentence leads when the line asked how often and the row puts it second.

    A row holds one answer for every way its subject is asked about, and a row written for the job
    answers the frequency later: "Cut them straight across rather than down the sides, leave a
    millimetre or two of white ... Once a fortnight is plenty". Read out to someone who asked
    "how often should i trim my toenails", that answers a different question for a sentence and
    reaches the rate last.

    Only a sentence that opens on the rate is moved - "Once a fortnight is plenty", "Every six
    months", "Two or three times a week" - because a rate named inside a sentence about something
    else ("most freezers need this once or twice a year") is that other sentence's fact, not the
    rate on its own. Nothing is added, cut or reworded: the same sentence moves, and the sentence
    it passes keeps its place behind it.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    if not isinstance(line, str) or not _ASKS_HOW_OFTEN.search(line):
        return reply
    parts = _sentences(reply)
    if len(parts) < 2:
        return reply
    if _A_RATE.search(parts[0]):
        return reply
    for at, sentence in enumerate(parts[1:], 1):
        if _A_RATE.match(sentence) and len(sentence.split()) <= 22:
            return " ".join([sentence] + parts[:at] + parts[at + 1:])
    return reply


def answer_first(reply, understood, line=None):
    """The answer leads: a sentence that only announces the answer is not the answer.

    A row, a card or a composer line is often written to be read on a screen, where a signpost
    helps: "Three tests, in this order.", "Two things to know.", "Here's the short version.",
    "Good question.", "You asked how long rice takes." Read out as the first thing the person
    gets, it answers nothing. STYLE.md puts the answer in the first sentence, so that sentence is
    dropped and the sentence it was announcing leads.

    The same reading is used for every shape of answer: a signpost is not a time, a figure, a
    list, a comparison, a verdict or a method, so no table of labels is kept here. The sentence is
    dropped only when there is another sentence to lead, and nothing else is reordered, added or
    reworded. A count in a signpost ("three tests") is still carried by the tests that follow.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    # A line that asks how often gets the sentence that says how often, in front: see `rate_first`.
    reply = rate_first(reply, understood, line)
    parts = _sentences(reply)
    if len(parts) > 1:
        first = parts[0].rstrip(".!? ").strip()
        if first and _SIGNPOST.match(first):
            reply = " ".join(parts[1:])
    # A yes-or-no ask read out gets a description first: the air-fryer card opens on what the
    # machine is and reaches "Worth it for one or two people" in its second sentence, and the
    # person asked whether to buy one. The verdict is in the card, so it leads.
    reply = verdict_first(reply, understood, line)
    # A method ask is already turned round by `method_first`, which moves the one sentence that
    # is only the whole job's clock and leaves every step's own time inside the method.
    if _wants_the_method(understood):
        return method_first(reply, understood)
    return cause_first(reply, understood)


# A sentence that opens with the answer to a yes-or-no question. It is the row's own words, and
# the words are what make it a verdict: "Worth it for one or two people", "Not worth it for most
# people", "Yes", "No", "It depends". A sentence that merely happens to hold "yes" or "no" later
# on ("which is not a reason to buy one") is not this, because a verdict is said at the start.
_VERDICT_OPENS = re.compile(
    # A bare yes or no, as an answer of its own: "Yes, but ...", "No. A test is ...". The word has
    # to end there - "No real bank asks for that" is a statement about banks, not a no.
    r"^(?:yes|yeah|yep|no|nope)\b(?=\s*[,.;:!?-]|\s*$)"
    r"|^(?:not really|not usually|not always)\b"
    r"|^(?:worth it|not worth it|worth the money)\b"
    r"|^(?:it is|it's) (?:worth|not worth|fine|safe|okay|ok|not safe|not fine)\b"
    r"|^(?:it depends|usually|definitely|in most cases|most of the time)\b", re.I)


# A verdict on the thing is not a verdict on thinking about it. "It is worth asking whether ...",
# "worth a conversation", "worth thinking about" all open the question rather than answer it, and
# the card that says one of them says the answer in its next sentence.
_THINKING_IT_OVER = re.compile(
    r"\bworth\b[^.]{0,40}\b(?:whether|asking|thinking|a thought|considering|wondering|"
    r"talking about it|a conversation|a talk|checking first)\b", re.I)


def verdict_first(reply, understood, line=None):
    """The verdict leads when the line asked yes or no and the card gave it later.

    A row holds one answer for every way its subject is asked about, and the worth-it cards are
    written to be read whole: what the thing is, who it suits, what to pay. Asked "is it worth
    it", the first thing the person gets is a description, and the sentence that answers them is
    the second one. STYLE.md puts the answer in the first sentence, so the sentence that opens
    with a verdict is moved to the front and the rest follows in the order it was written.

    Nothing is added or reworded, and the move is only made when the shape check can see that the
    opening sentence is *not* a yes or no: `fit.gives(opening, "yesno", line) is False`. So a card
    that already answers first is left alone, a card whose opening the check cannot read is left
    alone, and a line that did not ask yes or no never comes here.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    if _the_want(understood) != fit.YESNO:
        return reply
    parts = _sentences(reply)
    if len(parts) < 2:
        return reply
    bare_opening = parts[0].rstrip(".!? ").strip()
    if _VERDICT_OPENS.match(bare_opening):
        return reply
    for place, sentence in enumerate(parts[1:], 1):
        bare = sentence.rstrip(".!? ").strip()
        if not bare or not _VERDICT_OPENS.match(bare):
            continue
        if _THINKING_IT_OVER.search(bare):
            # "It is worth asking whether you want them or the life you had with them" is the
            # reply turning the question back, not the verdict on it: the sentence that settles
            # it ("Go back only if ...") is the one that answers.
            continue
        try:
            if fit.gives(bare, fit.YESNO, line) is False:
                continue
        except Exception:  # noqa: BLE001
            continue
        rest = " ".join(parts[:place] + parts[place + 1:])
        return "%s %s" % (sentence, rest)
    return reply


def method_first(reply, understood):
    """The reply with its total time moved to the end when the line asked for the method.

    Returns the reply unchanged for every other line, for a reply that is one sentence (there is
    nothing to lead with), and for a reply whose opening sentence is about more than its total
    time.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    if not _wants_the_method(understood):
        return reply
    found = _OPENING.match(reply)
    if not found:
        return reply
    opening, rest = found.group(1).strip(), found.group(2).strip()
    if not _TOTAL.match(opening):
        return reply
    if not rest:
        return reply
    return "%s %s" % (rest, opening)


# A sentence whose own subject is the cause: "The reason is hair, soap and grease caught in the
# trap", "The usual cause is too much water", "The commonest cause is worms". Only such a sentence
# moves, because it says what it is about and stands on its own at the head of a reply. "That is
# because ..." and "It is because ..." point back at the sentence before them, so moved to the
# front they would lead with a word that names nothing.
_CAUSE_SENTENCE = re.compile(
    r"^\s*(?:the|a|an)\s+"
    r"(?:usual|main|most likely|likely|commonest|common|real|other|whole)?\s*"
    r"(?:reason|cause)s?\b(?![?!])",
    re.I)


def _wants_the_cause(understood):
    if not isinstance(understood, dict):
        return False
    want = understood.get("wants")
    if isinstance(want, str):
        want = want.strip().lower()
    return want == fit.REASON


def cause_first(reply, understood):
    """The cause sentence leads when the line asked why and the card puts it last.

    A card is written for the screen and for every way its subject is asked about, so the fix
    comes first and the cause closes the paragraph: "Pull the hair and soap out of the trap first
    ... The reason is hair, soap and grease caught in the trap and the bend." Read out to someone
    who asked "why is my drain slow", that answers a different question for two sentences and
    reaches their answer last.

    So when `memory["understood"]["wants"]` is `reason`, a sentence that names itself as the cause
    is moved to the front. Nothing is added, cut or reworded - the same sentence moves - and a
    reply whose first sentence is already a cause is left exactly as it is. Every other shape of
    line is left alone: "how do i unblock my drain" wants the fix first whatever the card says
    later, and `method_first` above owns the `steps` case.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    if not _wants_the_cause(understood):
        return reply
    parts = _sentences(reply)
    if len(parts) < 2:
        return reply
    for index in range(1, len(parts)):
        if _CAUSE_SENTENCE.match(parts[index]):
            moved = parts[index]
            rest = parts[:index] + parts[index + 1:]
            return " ".join([moved] + rest)
    return reply


# The shapes a single sentence can carry, and so the shapes a row can owe a sentence for. The
# soft ones (`opinion`, `advice`, `comfort`, `answer`) are the whole reply rather than a figure, a
# place or a verdict, so no one sentence gives one and no row can declare one for them.
_HARD = frozenset((fit.TIME, fit.AMOUNT, fit.PLACE, fit.PERSON, fit.MEANING,
                   fit.YESNO, fit.PICK, fit.STEPS, fit.OPTIONS, fit.REASON))

# The words a sentence is about: the short ones ("a", "in", "of") say nothing on their own.
_SAID_WORD = re.compile(r"[a-z0-9]+")


def _the_want(understood):
    if not isinstance(understood, dict):
        return ""
    want = understood.get("wants")
    if not isinstance(want, str):
        return ""
    return want.strip().lower()


def _the_opening(reply):
    return fit.first_sentence(reply)


def _already_said(lead_said, opening):
    """True when the opening sentence already says the declared one, in its own words."""
    mine = [w for w in _SAID_WORD.findall(lead_said.lower()) if len(w) > 2]
    if not mine:
        return lead_said.lower().strip(" .,!?") == " ".join(_SAID_WORD.findall(opening.lower()))
    there = set(_SAID_WORD.findall(opening.lower()))
    return all(word in there for word in mine)


def _the_own_sentence_holding(parts, bare):
    """The place of the reply's own sentence that says the declared words, or None.

    A row written for the harder question puts the plain answer in its second or third sentence
    ("... and it booms loudest when you accelerate. It is not an emergency, but fumes can get
    into the cabin ..."). `bare` is usually the opening of that sentence rather than all of it,
    so the test is whether every word they share is in it - the sentence's own trailing detail
    ("but fumes can get into the cabin") is carried along with it.
    """
    mine = [w for w in _SAID_WORD.findall(bare.lower()) if len(w) > 2]
    if not mine:
        return None
    for at, part in enumerate(parts):
        there = set(_SAID_WORD.findall(part.lower()))
        if all(word in there for word in mine):
            return at
    return None

def the_sentence_owed(reply, understood, declared=None):
    """The sentence the line asked for, put in front, when the row declares one for its shape.

    A row holds one answer for every way its subject is asked about, and it is written for the
    harder question: the side-effects card was written for "my medication is making me feel odd"
    and answers "are these side effects normal" with a paragraph about the leaflet that reaches
    the verdict only in its third clause. STYLE.md asks for the answer in the first sentence, so
    a row declares the sentence it owes and the shape of line it owes it to -
    `entry(..., lead=("yesno", "Usually, yes"))`, or a callable in place of the sentence for a row
    whose key is asked from both sides ("No" for "is a cold the same as the flu", "" for "can i
    get flu twice") - and this puts it in front.

    What decides is the line, not a reading of the card: the line's `wants` has to be the shape
    the row declared, and only then does the sentence go in front. So a line that wants a time is
    left alone by a row whose sentence is a verdict, a card that already opens on the same words
    is left exactly as it was, and a sentence the shape check can read as another shape is never
    used. Nothing is reworded: the sentence is the row's own words.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    if not isinstance(declared, (tuple, list)) or len(declared) != 2:
        return reply
    shape, said = declared
    shape = shape.strip().lower() if isinstance(shape, str) else ""
    if shape not in _HARD or _the_want(understood) != shape:
        return reply
    if callable(said):
        # a row whose key is asked from both sides of one question reads the line and says which
        # sentence it owes, exactly as a row's `guard=` reads the line. Anything it cannot answer
        # with is no sentence at all.
        try:
            said = said(understood)
        except Exception:  # noqa: BLE001 - a sentence is never worth a turn
            return reply
    if not isinstance(said, str) or not said.strip():
        return reply
    bare = " ".join(said.split()).rstrip(" .!?")
    if not bare:
        return reply
    opening = _the_opening(reply)
    if reply.lstrip().lower().startswith(bare.lower()):
        return reply
    if _already_said(bare, opening):
        # the card opens on the same answer in its own words: "Yes. Yes, but only ..." is not a
        # reply, and "In the cupboard. It keeps a fortnight in the cupboard." is not one either.
        return reply
    line = understood.get("text") if isinstance(understood, dict) else None
    if not isinstance(line, str):
        line = (understood.get("clean") if isinstance(understood, dict) else "") or ""
    try:
        if fit.gives(bare, shape, line) is False:
            # the sentence is unmistakably another shape for this line, so the row is mis-declared
            return reply
    except Exception:  # noqa: BLE001 - a shape check must never cost a turn its reply
        return reply
    # The row already says this sentence, later on. A row written for the harder question has the
    # plain answer in its second or third sentence, so prepending the words would say the answer
    # twice ("It is not an emergency. ... It is not an emergency, but fumes can get into the
    # cabin."). The sentence that holds them moves to the front instead, whole, and everything
    # else keeps its order: nothing is added, cut or reworded.
    parts = _sentences(reply)
    at = _the_own_sentence_holding(parts, bare)
    if at is not None and at > 0:
        return " ".join(parts[at:] + parts[:at])
    return "%s. %s" % (bare, reply.lstrip())


# The shapes a sentence can be lifted for: each one is a check `fit.gives` can make on a single
# sentence, so the lift only moves a sentence the checker has already read as the answer.
_LIFTABLE = frozenset((fit.TIME, fit.AMOUNT, fit.PLACE))

# A sentence that only makes sense after the one before it cannot be lifted to the front: "It is
# 150cm", "That takes about an hour", "They go every two weeks" all point at something said
# already, and read first they point at nothing.
_POINTS_BACKWARDS = re.compile(
    r"^\s*(?:it|its|it's|that|that's|this|these|those|they|them|their|there\s+(?:it|they|you|we|that|those|these)\b|then|so|and|but|also|"
    r"otherwise|still|though|however|either|neither|both|such|the same|which|who|if|unless|"
    r"in that case|at that point|after that|for now)\b", re.I)


# Sympathy is the answer's opening whatever was asked: "my dog died, how much is a cremation" was
# answered "I'm sorry, that's one of the hardest days. Nothing has to be decided today..." and
# moving the practical sentence in front of the condolence puts the price before the person. No
# figure is worth leading with over that, so a reply that opens with it is left as it was written.
_OPENS_WITH_SYMPATHY = re.compile(
    r"^\s*(?:(?:i'm|i am|so|very|truly)\s+)*(?:sorry|apologies)\b|"
    r"^\s*that'?s\s+(?:hard|awful|terrible|rough|grim|rotten|a lot)\b|"
    r"^\s*i'?m\s+so\s+sorry\b|^\s*my\s+(?:heart|sympathies)\b", re.I)


# An opening that warns says what to do about the answer, so it is never traded for a figure:
# "There is no safe number of drinks before driving" read as the legal figure instead buried the
# warning, and "Do not drink the water" read as the bacteria count below it does the same. The
# reading is the head of the sentence only - a "never" or a "do not" anywhere in the reply is an
# ordinary sentence and not this opening.
_OPENS_WITH_A_WARNING = re.compile(
    r"^\s*(?:there'?s?\s+(?:is\s+)?no\s+safe\b|no\s+safe\b|never\b|do\s+not\b|don'?t\b|"
    r"(?:call|ring|phone)\s+999\b|999\b|go\s+to\s+(?:a&e|the\s+hospital)\b)", re.I)


# A sentence that names nothing the line names is not the answer to it, whatever figure it
# carries: "A second quote is normal and free, and the partial retest is free if the work is back
# within 10 working days" answers a question about quotes, and read first after "is that
# expensive" it answers nothing the person asked. A sentence that does share a word with the line
# is the one the answer is about - "Six to eight weeks off running ... for a stress fracture".
_SHARED_WORDS = frozenset((
    "the", "and", "for", "that", "this", "with", "you", "your", "have", "has", "are", "was",
    "were", "what", "when", "where", "which", "who", "why", "how", "should", "could", "would",
    "will", "been", "being", "about", "there", "their", "them", "they", "from", "into", "than",
    "then", "some", "any", "can", "does", "did", "doing", "not", "but", "one", "out", "over",
    "very", "just", "like", "get", "gets", "got", "much", "many", "more", "most", "long",
    "take", "takes", "need", "needs", "want", "wants", "make", "made", "is", "it"))


def _words(text):
    return {word for word in re.findall(r"[a-z]{4,}", str(text or "").lower())
            if word not in _SHARED_WORDS}


def _names_the_line(sentence, line):
    """True when the sentence shares a word with the line that asked."""
    if not line:
        return True
    asked = _words(line)
    return bool(asked & _words(sentence))


def _sentence_stands_alone(sentence):
    """True when a sentence reads as an answer with nothing before it."""
    text = " ".join(str(sentence or "").split())
    if len(text.split()) < 4:
        return False
    if _POINTS_BACKWARDS.match(text):
        return False
    return not text.endswith("?")


def shape(reply, understood, line=None):
    """The reply with the sentence that answers the wanted kind of question moved to the front.

    `understood` is the turn's reading, whose `wants` names the kind of answer the line asked for
    (`bot/compose/fit.py`). A method asks for its own move (`method_first`); a time, an amount or a
    place lifts the first sentence that gives that kind of answer, and only when the reply's
    opening does not already give it. A yes or no and a pick are left alone: their checks cannot
    be sure enough that a sentence is the answer rather than a remark that mentions one.
    Everything else is returned unchanged, and a sentence is never reworded, only moved.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    if not isinstance(understood, dict):
        return reply
    want = understood.get("wants")
    if not isinstance(want, str):
        return reply
    want = want.strip().lower()
    if want in _METHOD:
        return method_first(reply, understood)
    if want not in _LIFTABLE:
        return reply
    parts = _sentences(reply)
    if len(parts) < 2:
        return reply
    # The opening already answers the question, so there is nothing to lift; and a reply that
    # opens on a shrug is not reshaped here, because the sentence after it is not an answer the
    # row wrote to be read first.
    if fit.gives(parts[0], want, line) is True or fit.is_a_punt(parts[0]):
        return reply
    # An opening that names the thing asked about and carries a figure is an answer the check may
    # have no unit for - "A marathon is 26.2 miles, or 42.2 kilometres" for "how long is a
    # marathon", where `fit` has no reading for a length in miles. Lifting past it trades a right
    # answer for a wrong one on the strength of a miss the checker invented. Found by
    # salmon-llama on #12640.
    if re.search(r"\d", parts[0]) and _names_the_line(parts[0], line):
        return reply
    if _OPENS_WITH_SYMPATHY.search(parts[0]):
        return reply
    # An opening that warns is the answer, whatever figure comes after it: "how many units is over
    # the limit" opens "There is no safe number of drinks before driving", and lifting the legal
    # figure past it put the warning in the middle of the reply. A person who asked about the
    # limit is told the warning first. Found by plucky-frame on #13381.
    if _OPENS_WITH_A_WARNING.search(parts[0]):
        return reply
    # A "when" is answered by a moment - a clock time or a season - and not by a length of time:
    # "when is a player booked" is answered "A yellow card is a formal warning", and lifting "in
    # football two of them in a match mean a red ... ten minutes in the bin" put a duration where
    # the moment belongs. The clock and the season are `fit`'s own reading (`CLOCK`).
    when_asked = bool(line) and re.search(r"\bwhen\b", line, re.I) is not None
    for index in range(1, len(parts)):
        sentence = parts[index]
        if when_asked and not fit.CLOCK.search(sentence):
            continue
        # A sentence that warns is never lifted to the head either: "Never give a child aspirin
        # under 16" read before "Check the label for the dose" answers a dose question with a
        # warning out of its order. A warning is not a figure, so it is not the sentence lifted.
        if _OPENS_WITH_A_WARNING.search(sentence):
            continue
        if not _sentence_stands_alone(sentence):
            continue
        # A sentence whose answer is a duration or an amount answers the clock or the amount it
        # was asked about and no other shape: "Roughly 30 minutes, start to finish" read as the
        # pick for "what should i cook" would put the time of the job where the dish belongs. The
        # same sentence is exactly what a "how long" or a "how much" came for, so it is lifted
        # for those two and left where it is for every other ask.
        if want not in (fit.TIME, fit.AMOUNT) and (fit._a_time(sentence) or fit._an_amount(sentence)):
            continue
        if fit.gives(sentence, want, line) is not True:
            continue
        if not _names_the_line(sentence, line):
            continue
        moved = [sentence] + parts[:index] + parts[index + 1:]
        return " ".join(moved)
    return reply
