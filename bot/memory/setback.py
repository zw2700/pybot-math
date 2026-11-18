"""Something went wrong for them, and they have not said how.

"my cake was a disaster", "the boiler went wrong", "the party went badly", "everything went
wrong today": the person is handing over a setback and waiting for the one thing a friend asks,
which is what happened. Every one of these lines was answered by the bot filing it away -
"Got it - your cake was a disaster", "Noted: the curry was a disaster", "You ruined everything,
good to know" - or with a stock line that would fit any message ("Got it. Is there anything
you'd like a hand with?"). Saying a person's bad news back to them as a receipt is the coldest
reply in STYLE.md, and on a line this open it also answers nothing.

So this reads the vague setback and the composer asks about it (bot/compose/trouble.py, which
owns the turn for "something of theirs has gone wrong"): a short acknowledgement and the one
question the line leaves open, in the person's own thing where the line names one ("what
happened with your cake?", not "what happened?").

The same line in the present tense is the other half of this: "the deadline is killing me",
"this spreadsheet is killing me", "the commute is a nightmare". Nothing has happened yet, so the
question is not what happened but which part of it wears most ("what's the worst bit of it?"),
which is the reply STYLE.md gives for a spreadsheet that is killing somebody. Both were filed
away before - "Got it - the deadline is killing you".

Guards, because the shape is easy to over-read:

* only the vague report. The line has to stop at the setback: "the cake went wrong and it sank"
  or "my laptop went wrong after the update" says what happened, and the entry that diagnoses
  it has the better answer, so a line that goes on is left alone.
* never a question ("why did my cake go wrong?"), never a line about somebody else ("my mum was
  a nightmare" - trouble.py refuses those too), never a line about their body ("my knee is
  killing me" is an ache, and the body modules answer it), and never a line that names its own
  fault ("my cake flopped", "my sourdough failed"): those are the knowledge base's diagnosis.
* the thing named has to be theirs: "my hair went wrong" is "your hair", not "the hair", and a
  day, a week or a life is spoken to as a day rather than as a gadget ("what did your life do?"
  is the question this file exists to avoid).
"""
import re

# The setback itself, in the shapes people type it. Only the vague ones: a named fault ("my cake
# sank", "the boiler is leaking") belongs to the knowledge base, and listing those words here
# would take their turn.
VAGUE = re.compile(r"""\b(?:
        went\s+wrong | gone\s+wrong
      | (?:was|were|has\s+been|have\s+been|turned\s+out)\s+(?:a\s+|an\s+)?
        (?:(?:bit\s+of\s+a|total|complete|real|proper|right|absolute|utter|huge|massive|
             big)\s+)?
        (?:disaster|catastrophe|flop|washout|shambles|nightmare)
      | went\s+badly | went\s+pear[\s-]?shaped | came\s+out\s+wrong
    )\b""", re.X)

# The same said as something still going on: "the deadline is killing me", "the commute is a
# nightmare". It is not an old event to ask about, it is the thing they are carrying today, so
# the question is which part of it is worst. Only for a thing that is not their body: "my feet
# are killing me" is a complaint about the feet, and the body modules answer it.
NOW = re.compile(r"""\b(?:is|are|'s|'re)\s+(?:really\s+|properly\s+|still\s+|just\s+)?
    (?:
        killing\s+me | doing\s+my\s+(?:head|nut)\s+in
      | driving\s+me\s+(?:mad|crazy|nuts|insane|up\s+the\s+wall|round\s+the\s+bend)
    )
  | \b(?:is|are|'s|'re)\s+(?:really\s+|still\s+|all\s+|just\s+)?going\s+wrong\b
  # The same thing said as a gradual decline rather than a fault: "the training is going
  # badly", "the lessons are not going well", "its going badly". Read as a fact to file, each of
  # these was answered "Got it - the training is going badly", which is the coldest reply in
  # STYLE.md on a line that has just handed over something going wrong.
  | \b(?:isn['\u2019]?t|aren['\u2019]?t|is\s+not|are\s+not|not)
    \s+going\s+(?:well|great|smoothly|to\s+plan|right)\b
  | \b(?:is|are|'s|'re|was|were)\s+(?:really\s+|still\s+|all\s+|just\s+)*
    going\s+(?:badly|awfully|terribly|wrong)\b
  | \bits\s+(?:all\s+|really\s+|still\s+|just\s+)?
    (?:not\s+going\s+(?:well|great|smoothly|to\s+plan|right)|going\s+(?:badly|awfully|terribly|wrong))\b
  | \b(?:is|are|'s|'re)\s+(?:a\s+|an\s+)?
    (?:(?:bit\s+of\s+a|total|complete|real|proper|right|absolute|utter|huge|massive|big)\s+)?
    (?:disaster|catastrophe|nightmare|shambles)\b
  # A thing of theirs wearing them down over time: "work has been getting me down lately",
  # "the commute is getting me down", "my job gets me down". The auxiliary is optional because
  # people leave it out ("work gets me down"), and "has been"/"have been" is how the same
  # thing is said when it has gone on a while. A person is not a thing here - "my boss gets me
  # down" names somebody, and `_refused` leaves those to bot/compose/harm.py.
  | \b(?:(?:is|are|was|were|'s|'re)\s+)?(?:(?:has|have|had)\s+been\s+|been\s+)?
    (?:getting|gets|got|wearing|wears|wore)\s+(?:me|us)\s+down\b
""", re.X)

# The thing said after a setback that does not answer it: "this job is getting me down and i
# dont know what to do" says nothing about the job, it says the person is stuck, which is
# another reason to ask what wears most rather than a diagnosis with an entry of its own. Those
# clauses are taken off before the goes-on test, so the setback reading still stands.
HELPLESS = re.compile(r"""\s*(?:,|\band\b|\bbut\b|\bso\b)\s*
    (?:\w+\s+){0,3}?
    (?:i\s+)?(?:don['\u2019]?t|do\s+not|dont|can['\u2019]?t|cannot|cant)\s+
    (?:really\s+|even\s+|honestly\s+)?
    (?:know\s+what\s+to\s+do|know\s+where\s+to\s+start|cope|keep\s+going|take\s+it\s+any\s+more)
  | \s*(?:,|\band\b|\bbut\b)\s*
    (?:\w+\s+){0,3}?i\s*(?:['\u2019]m|m\b|am)\s*(?:at\s+my\s+wits['\u2019]?\s*end|at\s+the\s+end\s+of\s+my\s+tether)
""", re.X)

# The person blaming themselves for it: "i messed up the cake", "i ruined everything". Read here
# because it is the same open question - what happened - and it got the same filing-cabinet reply
# ("You ruined everything, good to know.").
BLAME = re.compile(r"""\b(?:i|we)\s+(?:really\s+|totally\s+|completely\s+|properly\s+|just\s+)*
    (?:messed|screwed|balls(?:ed)?|buggered|wrecked)\s+(?:it\s+)?up\b
    |\b(?:i|we)\s+(?:really\s+|totally\s+|completely\s+)?(?:ruined|wrecked)\b""", re.X)

# What the setback was about, when the line names it: "my cake", "the boiler", "your first
# attempt". The second noun is there for the modifiers people put in front of the thing that
# actually went wrong ("my driving test", "our first attempt"), so the question names the test
# and not the driving.
OWNER = re.compile(r"\b(my|our|the|this|that|his|her|their)\s+(?:whole\s+|entire\s+)?"
                   r"([a-z][a-z'-]{1,18})(?:\s+([a-z][a-z'-]{1,18}))?")
MODIFIER = frozenset("""
    first second third last next previous other own new old little big huge favourite favorite
    front back spare cheap expensive birthday christmas driving washing running first
""".split())
YOURS = frozenset(("my", "our"))

# A thing named here is not a thing to ask about, it is the whole of it: the day, the week, or
# the person's life. Asked "what happened with your life?" the reply reads as a form.
NOT_A_THING = frozenset("""
    day week month year weekend morning evening night time life everything anything it all
    whole world lot bit thing way start begin end minute hour afternoon
""".split())

# A person named in the line is not a thing of theirs that went wrong: "my mum was a
# nightmare" is somebody else's day, and bot/compose/trouble.py stands aside for those, because
# what is asked about another person is not a setback of the speaker's. Kept here as well so the
# reading is right on its own, for a lane that has no composer to check it.
PEOPLE = frozenset("""
    he she him her his hers they them their mum mam mom mummy dad daddy father mother parent
    son daughter child kid kids baby toddler teenager boy girl husband wife partner boyfriend
    girlfriend fiance fiancee nan nana gran granny grandma grandad grandpa grandparents brother
    sister sibling aunt uncle cousin nephew niece friend mate flatmate housemate neighbour
    neighbor colleague boss manager landlord landlady tenant carer nurse vet dog cat puppy
    kitten pet
""".split())

# A line that goes on after the setback has said more than the setback: "the cake went wrong and
# it sank" names its own fault, and somebody else's reply is the answer to that.
GOES_ON = frozenset(("and", "but", "because", "cos", "cause", "so", "then", "when", "after",
                     "before", "while", "which"))
MORE_THAN = 4  # words after the setback, "again"/"today"/"this morning" being up to three

# The question the line leaves open, with the person's own thing in it. A reply that could have
# been sent to any line is what this is written against, so the thing is the sentence.
ABOUT_THING = (
    "Oh no \u2014 what happened with {thing}?",
    "Ah, that's a shame. What went wrong with {thing}?",
    "That's rotten \u2014 what happened with {thing}?",
    "Ah no. What went wrong with {thing}?",
    "Oh no. How did {thing} go wrong?",
)
# The same for a thing that cannot do anything of its own (an interview, a party, a test).
ABOUT_OCCASION = tuple(line for line in ABOUT_THING if "what happened with" in line
                       or "what went wrong with" in line) + \
                 ("Oh no. What went wrong with {thing}?",)
# The same for something still going on, where the question is which part of it wears most.
ONGOING = (
    "Ugh \u2014 {thing} sounds relentless. What's the worst bit of it?",
    "That's a lot to be carrying. What's the hardest part of {thing}?",
    "Ah no. What's the worst of {thing} at the moment?",
    "I bet. What is it about {thing} that's wearing you down?",
)
# A whole day, or a person blaming themselves with nothing named.
WHOLE = (
    "Sounds like one of those days. What went wrong?",
    "Oh no \u2014 what happened?",
    "Ouch. What went wrong?",
    "Ah, everything at once? What happened?",
)
WHOLE_NOW = (
    "Ugh, that sounds relentless. What's the worst bit of it?",
    "That's a lot at the moment. What's the hardest part?",
    "Ah no. What is it that's wearing you down?",
)
# A word after the thing's first word only belongs to its name when it is part of that name:
# "the school run", "a cover letter". A joiner or a verb after it is the rest of the sentence -
# "the commute to leeds is a nightmare" is the commute - and taking it made the bot ask about
# "the commute to".
JOINERS = frozenset(("to", "for", "at", "in", "on", "onto", "into", "with", "and", "or", "but",
                     "because", "since", "after", "before", "while", "when", "that", "which",
                     "who", "is", "was", "were", "are", "am", "be", "been", "being", "went",
                     "goes", "going", "gone", "has", "have", "had", "keeps", "kept", "makes",
                     "made", "turned", "turns", "came", "comes", "last", "next", "this", "the",
                     "a", "an", "of", "about", "from", "by", "so", "as", "then", "now", "today",
                     "yesterday", "again", "too", "really", "still", "just", "all", "totally",
                     "completely", "absolutely", "properly"))
NOT_A_DOER = frozenset(("interview", "exam", "test", "party", "meeting", "date", "holiday",
                        "essay", "presentation", "wedding", "birthday", "appointment", "shift",
                        "lesson", "class", "review", "application", "audit", "trial", "day"))


def _flat(text):
    return " ".join(str(text or "").lower().replace("\u2019", "'").split())


def _thing(text):
    """The person's own words for the thing that went wrong, or "" for a day or nothing."""
    for match in reversed(list(OWNER.finditer(text))):
        qualifier, word, after = match.group(1), match.group(2), match.group(3) or ""
        if word in ("whole", "entire") and after:
            # "my whole kitchen" is the kitchen, and "my life" is not a thing either way.
            word, after = after, ""
        elif word in MODIFIER and after:
            word, after = word + " " + after, ""
        elif after in JOINERS:
            # "the commute to leeds" is the commute: the word after it starts the rest of the
            # sentence, and it is not part of the thing's name.
            after = ""
        if word in NOT_A_THING:
            return ""
        owner = "your" if qualifier in YOURS else "the"
        return (owner + " " + word + (" " + after if after else "")).strip()
    return ""


def _named_after(text):
    """The thing after a blaming verb: "i messed up the cake" -> "your cake"."""
    match = re.search(r"\b(?:the|my|our|this|that)\s+(?:whole\s+)?"
                      r"([a-z][a-z'-]{1,18})(?:\s+([a-z][a-z'-]{1,18}))?", text)
    if not match:
        return ""
    word, after = match.group(1), match.group(2) or ""
    if word in MODIFIER and after:
        word, after = word + " " + after, ""
    elif after in JOINERS:
        after = ""
    if word in NOT_A_THING:
        return ""
    return "your " + word + (" " + after if after else "")


def _bare_subject(head):
    """The thing a line names with no "my"/"the" in front of it: "work is killing me"."""
    words = [word for word in head.split() if word]
    # The auxiliaries too, or "work has been getting me down" named "has" and asked what's the
    # worst of has.
    while words and words[-1] in ("is", "are", "was", "were", "been", "has", "have",
                                  "had", "really", "just"):
        words.pop()
    if not words:
        return ""
    word = words[-1]
    if word in NOT_A_THING or word in ("i", "im", "it", "that", "this", "there", "he",
                                      "she", "they", "we", "you"):
        return ""
    return word


def _refused(name):
    """Whether the thing the line names is not a thing to ask about."""
    return bool(name) and name.split()[-1] in PEOPLE


def reading(text):
    """(name, "past") | (name, "now") for a setback or a thing wearing on them, or None.

    `name` is the person's own phrase for the thing ("your cake"), or "" for a whole day and
    for a person blaming themselves without naming it, which are answered with the same short
    question in its own tense.
    """
    clean = _flat(text)
    if not clean or "?" in clean:
        return None
    for pattern, tense in ((VAGUE, "past"), (NOW, "now"), (BLAME, "past")):
        match = pattern.search(clean)
        if not match:
            continue
        after = clean[match.end():].split()
        rest = HELPLESS.sub("", clean[match.end():]).split() if after else []
        if len(rest) > MORE_THAN or any(word.strip(".,!") in GOES_ON for word in rest):
            # The line has gone on to say what happened, or to name the fault. That has a
            # diagnosis of its own, and the entry that knows it answers better than a question.
            return None
        name = _thing(clean[:match.start()])
        if not name and pattern is BLAME:
            name = _named_after(clean[match.end():])
        if not name and pattern is NOW:
            name = _bare_subject(clean[:match.start()])
        if _refused(name):
            return None
        return (name, tense)
    return None


# The thing said here is often a plural ("the lessons", "the mornings"), and a pool written for
# one thing reads wrong the moment it is one of those: "the lessons sounds relentless" is the kind
# of sentence that makes a person stop believing the bot is listening. Only the verb is about the
# thing, so only the verb is made to agree.
_NOT_A_PLURAL_ENDING = ("ss", "us", "is", "ws")


def _a_plural_thing(name):
    """Whether the phrase for the thing reads as a plural ("the lessons", "my feet")."""
    words = str(name or "").split()
    if not words:
        return False
    last = words[-1].lower().strip(".,!?;:")
    if not last.endswith("s"):
        return False
    return not last.endswith(_NOT_A_PLURAL_ENDING)


def _agrees_with_the_thing(line, name):
    """The pool line with its verb made to agree with the thing that fills it."""
    if _a_plural_thing(name):
        return line.replace(" sounds ", " sound ").replace(" it sounds ", " they sound ")
    return line


def pool(text):
    """The replies for a setback, in the person's own thing where the line named one."""
    said = reading(text)
    if not said:
        return ()
    name, tense = said
    if not name:
        return WHOLE_NOW if tense == "now" else WHOLE
    if tense == "now":
        return tuple(_agrees_with_the_thing(line.format(thing=name), name) for line in ONGOING)
    last = name.split()[-1]
    lines = ABOUT_OCCASION if last in NOT_A_DOER else ABOUT_THING
    return tuple(line.format(thing=name) for line in lines)
