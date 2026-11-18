"""Which part of the body the line says is unwell, when the illness is the speaker's own.

One reading for everybody: "i have a migraine" and "my throat is killing me" are the same kind
of line as "i have a cold", and the only thing that tells them apart is the part named. The
composer keeps a pool of lines per part (`ill` is the cold's), so this reading says which pool
the line is asking for instead of every module matching the words again.

Three things are checked, and all are needed:

* the part, from the words people use for it ("migraine", "sore throat", "fever", "throwing up",
  "chest infection");
* whose it is. "my son has a fever" is the child's illness and the child's advice, "she gets
  migraines" is hers, and only the speaker's own comes here. "My" counts only when the part
  itself follows it - "my head" is the speaker's, "my room temperature is 40" is a room's - and
  anything else needs the speaker in front of it ("i have a headache", "ive been throwing up");
* that it is the body and not the word: hay fever is not a fever, and "i feel sick about going
  to the dentist" is dread rather than a stomach.

The reading is `None` on every line that names no part - a cold, the flu and "i feel ill" stay
with the plain illness pool, which is what those lines want.
"""
import re

from . import kinds, lexicon
from .normalize import LEXICON as COMMON_WORDS

# A fever goes both ways: cold one minute and hot the next. The connector joins two words, and
# only a cold word on one side of it and a hot word on the other is that going both ways. Two
# words on the same side are one state, not a fever - "im hot and sweaty" is heat and exertion,
# and "im cold and shivery" is one shiver - and those keep the reading they had.
_COLD_SIDE = r"\b(?:freezing|cold|chilly|shivering|shivery)\b"
_HOT_SIDE = r"\b(?:sweating|sweaty|boiling|hot|burning(?: up)?)\b"
# What may stand between the two words and leave them one clause: nothing, a time word, or the
# pronoun said again ("im hot and then im cold"). A thing with a determiner in front of it is a
# second subject - "im hot and the pool is cold", "im hot and i got cold water" are a hot person
# next to something cold, not a person going both ways - so the filler is a word list rather than
# a character count, which let those two through.
_FILL = (r"(?:\s+(?:one|two|a|an|the|some|bit|minute|minutes|or|and|then|so|very|really|"
         r"sometimes|always|all|next|im|i'm|i|am|at|in|of|night|nights|morning|"
         r"mornings|day|days|evening|evenings|afternoon|week|weekend|first|second))*\s*")
_JOIN = _FILL + r"(?:and\s+then|then|and|or|but)" + _FILL + r"\s*"
# "i keep going from cold to hot" is the same going both ways, said with from and to.
_FROM_TO = ("(?:" + _COLD_SIDE + r"\s+to\s+" + _HOT_SIDE + "|" + _HOT_SIDE + r"\s+to\s+"
            + _COLD_SIDE + ")")
_ALTERNATING = ("(?:" + _COLD_SIDE + _JOIN + _HOT_SIDE + "|" + _HOT_SIDE + _JOIN + _COLD_SIDE
                + "|" + _FROM_TO + ")")
# The same shape as one compiled pattern, so the body-state reading in the composer and the
# temperature reading here agree about what "cold and hot in one breath" is.
GOING_BOTH_WAYS = re.compile(_ALTERNATING, re.I)

# name, the words a person uses for it, and the nouns that can follow "my" for it. Longest
# phrase first, so "chest infection" is never read as a cold and "hay fever" never as a fever.
# A new part is a row here and a pool of its own in the composer.
# "Chucking up" is two verbs: the sickness ("i keep chucking up", "ive been chucking up since
# last night", "chucking up my lunch") and the hanging one ("chucking up some shelves", "im
# chucking up my job", "chucking up my evening class"). The list of things people hang got every
# phrasing it was written for and none of the others, so quitting an evening class got the
# stomach card. What follows "up" is the signal: the sickness is read when nothing follows it,
# when what follows is how often or how long - and a time word counts, because "i was chucking
# up yesterday" is the sickness and it was being read as a thing being chucked - or when the
# thing coming up is food, drink or blood. A determiner in front of anything else is the
# other verb.
_CHUCK_UP = (
    r"\b(?:been |kept? |keep |still )?chuck(?:s|ed|ing)?"
    r" (?:it |them |his |her |my |their |our )?up\b"
    r"(?=\s*(?:$|[,.!?;:]|(?:all|every|again|still|constantly|most|so|since|at|during|"
    r"yesterday|today|tonight|tomorrow|now|once|twice|last|this|in|for|after|before|"
    r"the other\b)\b"
    r"|(?:my |the |his |her |their |your |our |some |that )?"
    r"(?:lunch|dinner|breakfast|tea|supper|food|water|drink|drinks|milk|coffee|beer|wine|"
    r"blood|bile|medicine|meal|it)\b))")

PARTS = (
    ("head",
     r"\bmigraines?\b|\bmigranes?\b|\bheadaches?\b|\bhead aches?\b"
     r"|\bhead\b[^.!?]{0,14}?\b(?:is |feels? |keeps? |has )?"
     r"(?:pounding|throbbing|splitting|banging|hurts?|hurting|aching|killing)\b"
     r"|\b(?:pounding|throbbing|splitting)\b[^.!?]{0,10}?\bhead\b",
     frozenset("head headache headaches migraine migraines".split())),
    ("throat",
     r"\bsore throat\b|\bstrep throat\b"
     r"|\bthroat\b[^.!?]{0,14}?\b(?:hurts?|hurting|aches?|is sore|is killing|feels? raw|"
     r"is rough|is scratchy)\b",
     frozenset("throat".split())),
    # "hay fever" is an allergy and has its own answer, so it is not a temperature. The
    # alternating shape is the same fever said the long way: "im freezing then boiling",
    # "im hot one minute and cold the next" is a person going from shivering to sweating, and
    # "hot and cold" is the same line. Read as a temperature so the fever pool answers it, and
    # kept out of the body-state pool in the composer, which would tell them to open a window.
    ("temperature",
     r"(?<!hay )\bfever\w*|\btemperature\b|\bshivery\b|\bchills\b|\bhot and cold\b"
     r"|\bburning up\b|" + _ALTERNATING,
     frozenset("temperature fever".split())),
    ("stomach",
     r"\bstomach (?:bug|ache|cramps?|upset)\b|\btummy (?:ache|bug)\b"
     r"|\b(?:stomach|tummy)\b[^.!?]{0,12}?\b(?:hurts?|hurting|aches?|aching|is killing|"
     r"is (?:sore|cramping))\b"
     r"|\b(?:(?:going|gonna|about)\s+to\s+|been |kept? |keep |still )?(?:throwing up|"
     r"thrown up|threw up|throws up|throw up|vomiting|vomited|vomit|vomits|puk(?:e|es|ed|ing)|"
     r"barf(?:s|ed|ing)?|" + _CHUCK_UP +
     # The same sickness in every tense people say it. Only the forms that say it happened are
     # read: "im sick" alone is ill rather than being sick, and "get sick out of a car seat" is
     # cleaning. "sick of" and "sick to death of" are the other word for it (fed up), which is
     # what the lookahead keeps out.
     r"|(?:be|been|being|was|were) sick(?!\s+(?:of|to death|and tired)\b)|nauseous|nausea)\b"
     # A fragment is the whole line when a count or a time follows "sick": "sick twice today",
     # "sick since friday". "sick today" on its own is not read, because "im off sick today" is
     # a day off work rather than a symptom.
     r"|\bsick\b(?=\s+(?:\d|twice|once|three|four|five|since|all |last night|"
     r"yesterday|most mornings|every))"
     # Keeping nothing down is the sickness itself, said without the word for it.
     r"|\b(?:can ?not|cant|can't|could not|couldnt|couldn't|unable to|not able to) keep "
     r"(?:anything|much|water|fluids?|food|it) down\b"
     r"|\bkeep(?:ing)? nothing down\b"
     r"|\b(?:feel|feels|feeling|felt) sick\b(?!\s+(?:about|at|of|thinking)\b)"
     r"|\bdiarrhoea\b|\bdiarrhea\b|\bd\s?and\s?v\b",
     frozenset("stomach tummy belly gut".split())),
    ("chest",
     r"\bchest infection\b|\bchesty\b|\bwheez\w*",
     frozenset("chest".split())),
    # "toothache" and "earache" are the words people type, and neither was read as anything: the
    # line fell to whatever answers a line with no subject ("Got it. Is there anything you would
    # like a hand with?"). A tooth and an ear each want their own advice - a dentist, and the
    # reason not to poke about in it.
    ("teeth",
     r"\btoothaches?\b|\btooth aches?\b|\bteeth\b[^.!?]{0,14}?\b(?:hurt|hurts|aching|"
     r"ache|sensitive|killing)\b|\btooth\b[^.!?]{0,14}?\b(?:hurts?|aching|aches?|"
     r"throbbing|is killing)\b|\b(?:dental|dentist)\b[^.!?]{0,20}?\b(?:pain|"
     r"agony|hurts?)\b|\babscess\b|\bgums?\b[^.!?]{0,14}?\b(?:sore|bleeding|swollen|"
     r"hurts?|aching)\b",
     frozenset("tooth teeth gum gums mouth jaw".split())),
    ("ear",
     r"\bearaches?\b|\bear aches?\b|\b(?:ear|ears)\b[^.!?]{0,16}?\b(?:hurts?|hurting|"
     r"aching|aches?|throbbing|is killing|is sore)\b"
     r"|\bear infection\b|\bglue ear\b",
     frozenset("ear ears".split())),
)

# An abscess is not the tooth pool's line. The pool says "book the dentist today", which is
# right for an aching tooth and wrong for an abscess: an abscess is a spreading infection, and
# the answer for it already exists and is a stronger one ("A fever, pus or a puffy face with a
# bad tooth or swollen gums is a spreading dental infection, so ring a dentist today ... go to
# A&E if the swelling closes your eye"). Read as a tooth, the line lost those red flags. So the
# abscess is read for the mouth only when the line gives it nothing else to be: no mouth word
# next to it, no sign that it is spreading, and no other part of the body named. `i think i have
# an abscess` has none of those and keeps the new card.
AN_ABSCESS = re.compile(r"\babscess\w*\b", re.I)
A_MOUTH_WORD = re.compile(
    r"\b(?:tooth|toothache|toothaches|teeth|gums?|mouth|jaw|dental|dentist|molar)\b"
    r"[^.!?]{0,20}?\babscess\w*"
    r"|\babscess\w*\b[^.!?]{0,20}?\b(?:tooth|toothache|teeth|gums?|mouth|jaw|dental|molar)\b",
    re.I)
A_SPREADING_SIGN = re.compile(r"\b(?:fever|temperature|pus|pussy|puffy|swelling|swollen|"
                              r"spreading|swallow|swallowing|cheek|face)\b", re.I)
ANOTHER_PART = re.compile(r"\b(?:leg|legs|arm|arms|foot|feet|toe|toes|hand|hands|finger|"
                          r"fingers|knee|knees|hip|hips|back|shoulder|shoulders|skin|wound|"
                          r"wounds|armpit|groin|bum|bottom|thumb|elbow|ankle|shin|thigh|chest|"
                          r"stomach|tummy|neck|scalp|eye|eyes|breast|breasts|ear|ears)\b", re.I)
ALREADY_DEALT_WITH = re.compile(r"\b(?:drained|lanced|removed|burst|popped|gone)\b", re.I)
# A sample, a test or a pot is a thing being handed in, not a part playing up: "my stool sample"
# is a line about the appointment, and the gut advice is the wrong answer to it.
A_SAMPLE = re.compile(r"\b(?:sample|samples|test|tests|tested|testing|kit|pot|"
                      r"container|form|forms)\b", re.I)


def _an_abscess_elsewhere(text):
    """True when the line's abscess is not one the tooth pool should answer.

    Three ways to say so. It is at another part of the body ("an abscess on my leg", "an abscess
    on my back"); it is already dealt with ("i had an abscess drained at the hospital", "my
    abscess burst"); or it is a mouth abscess, which is a spreading infection with its own
    urgent answer ("a gum abscess", "a tooth abscess"), not pain to book an appointment for.
    A line that says none of those - `i think i have an abscess` - is the tooth pool's.
    """
    if not AN_ABSCESS.search(text):
        return False
    return bool(A_MOUTH_WORD.search(text) or A_SPREADING_SIGN.search(text)
                or ANOTHER_PART.search(text) or ALREADY_DEALT_WITH.search(text))


# A line that asks what to do about a part ("what helps a migraine", "what should i take for a
# headache") wants the same advice as the line that says they have one, so the part is read for
# it too. It has to be an ask about a cure: "how long does a migraine last" is a different
# question, and a person named in the line ("what helps a fever in a toddler") makes it theirs.
ASKING = re.compile(
    r"\b(?:what|anything|something)\b[^.!?]{0,26}?\b(?:helps?|works?|should i (?:take|do)|"
    r"can i take|do i take|do for|to take|to do)\b"
    r"|\bhow (?:do|can) i (?:get rid of|stop|shift|ease)\b|\bany (?:advice|tips|ideas)\b")


# A stool is a chair as well as what comes out of a person, and only the word beside it says
# which: nothing wooden is loose or runny. "loose stools for 3 days" and "soft stools and stomach
# ache" were answered with the wood-glue answer ("turn it over and find the loose joint"), which
# is the worst kind of reply - confident, detailed and about the wrong thing entirely - because
# no "my" in the line made it the speaker's, which is the only way the part below is read. A
# word that no chair can have settles it on its own. How the poo looks is left out of this rule:
# "my poo is pale and floats" and "my poo is black and tarry" are the red flags, and the safety
# card answers those.
A_LOOSE_STOOL = re.compile(
    r"\b(?:loose|runny|watery|liquid|soft)\s+(?:stools?|poos?|poops?|bowels?)\b"
    r"|\b(?:stools?|poos?|poops?|bowels?)\b[^.!?]{0,24}?"
    r"\b(?:loose|runny|watery|liquid|like water)\b"
    # "The runs" is what most of these words are: the quiet names people type when they would
    # rather not spell it out. Each one is "the <word>", because the bare word is something else
    # ("he runs the shop"), and the article is what makes it the gut. "The runs" itself is not in
    # the list: a person's runs are also the ones they go on, and "the runs were great today" is
    # a good morning out.
    r"|\bthe (?:trots|shits|squits|skitters|squirts)\b",
    re.I)
# "This weather is the shits" and "the trains are the shits" are a judgement of a thing, the
# way "it is rubbish" is, and there the same words are not the gut. A copula in front of them
# is what makes the sentence about something else, so a line shaped that way is not read; a
# person who has it says "ive got the shits", "had the shits" or just "the shits again".
A_THING_IS_TERRIBLE = re.compile(
    r"\b(?:is|are|was|were|be|being|been|seems?|looks?|feels?|gone|go(?:es|ing)?|went)\s+"
    r"(?:to\s+|a (?:bit |total |right |proper |complete |real |crock )?of\s+|such\s+|"
    r"right\s+|proper\s+|complete\s+)?"
    r"the (?:shits|trots|squits|skitters|squirts)\b", re.I)
# Nothing wooden is loose or runny: "one leg of the stool is loose" and "how do i tighten a loose
# stool leg" are a wobbly chair, and the loose-stool rule above took them to the stomach and
# answered a furniture line with fluids. One chair word in the line settles it, because no body
# line has a joint, a seat or a screwdriver in it.
A_CHAIR_WORD = re.compile(
    r"\b(?:leg|legs|joint|joints|seat|seats|wood|wooden|screw|screws|screwdriver|tighten|tight"
    r"|wobbly|wobble|wobbles|rickety|bracket|glue|chair|chairs|table|tables|bench|furniture"
    r"|dresser|sideboard|kitchen|carpenter|flat ?pack)\b"
    # "my bar stool is loose" and "my counter stool" are furniture said with a word the list
    # above does not hold: the compound is what makes it the chair, not the room.
    r"|\b(?:bar|counter|pub|breakfast|dining) ?stools?\b", re.I)
# A stool is a chair with a loose leg, so "my stool is loose" is the one line where the word for
# the gut is also the word for the furniture and the word for what is wrong with it is both as
# well. A line that means the gut says one word no chair can use - what it is like rather than
# just loose, where it goes, or how long it has been going on - and a line with none of them is
# the chair its owner has in mind.
A_GUT_ONLY = re.compile(
    r"\b(?:runny|watery|liquid|soft|hard|firm|pale|smelly|stinking|streaked|streaks|slimy|mucus"
    r"|diarr?hoea|constipat\w*|tummy|stomach|gut|guts|ache|aches|aching|pain|pains|painful"
    r"|cramps?|cramping|sore|wind|bloat\w*|toilet|loo|bum|poo|poos|pooed|pooping|bowels?"
    r"|sick|nausea|nauseous|vomit\w*|days?|weeks?|months?|since|morning|mornings|night|nights"
    r"|yesterday|today|times|a day)\b", re.I)
# What a poo can be that is a red flag or the safety card's: those lines are answered already,
# so the loose-stool rule stands aside for them.
A_POO_COLOUR = re.compile(r"\b(?:pale|black|tarry|bloody|blood|red|floats?|green|colour|"
                          r"color|mucus|slimy)\b", re.I)


# A part name typed with the wrong letter is still the part. "my stomacs been rough all week"
# was answered "Got it. Is there anything you'd like a hand with?", "my teath is killing me" with
# "Ugh - your teath sounds relentless" and "my stamach is killing me" with a question about the
# stamach, while the same lines spelled right get the stomach, the dentist and the stomach. The
# tables below are written the way each word is spelled, so a line that misses the spelling by
# one letter misses the part, and with it the pool and the card the part decides.
# The repair is the smallest one there is - a letter added, left out, or put in another's place -
# and it is made only when the typed word is not a word at all (the lexicon already settles the
# typos that matter, and one that lands on a real word is the other word: "cheat" is a letter
# from "chest") and when the part it reaches is the only part it could be, because two
# candidates are two parts and the line would be guessing between them.
PART_NOUNS_BY_LENGTH = {}
for _part_name, _part_pattern, _part_nouns in PARTS:
    for _noun in _part_nouns:
        PART_NOUNS_BY_LENGTH.setdefault(len(_noun), set()).add(_noun)


def _one_letter_apart(typed, spelled):
    """True when the word is the part with one letter added, left out, or put in another's place."""
    if abs(len(typed) - len(spelled)) > 1:
        return False
    if len(typed) == len(spelled):
        return sum(1 for typed_at, spelled_at in zip(typed, spelled)
                   if typed_at != spelled_at) == 1
    short, long_ = sorted((typed, spelled), key=len)
    return any(long_[:at] + long_[at + 1:] == short for at in range(len(long_)))


def _a_part_typed_with_one_letter_wrong(word):
    """The one part noun this word is a letter away from, or None when it is none or more than one."""
    fits = set()
    for length in (len(word) - 1, len(word), len(word) + 1):
        for noun in PART_NOUNS_BY_LENGTH.get(length, ()):
            if noun[0] == word[0] and _one_letter_apart(word, noun):
                fits.add(noun)
                if len(fits) > 1:
                    return None
    return fits.pop() if fits else None


# A real word that happens to sit one letter from a part is the word, not a typo of the part:
# "my gout is bad again" is gout, and read as a gut it got "fluids first, plain food". The
# lexicon settles most of these, but it is a list of the words the reader needs for spelling and
# it does not hold every ordinary word, so the ones within a letter of a part are named here.
# A word only belongs here when it is a word of its own AND a letter from a part: a misspelling
# nobody writes on purpose is not a word and stays repaired. A named illness is here by another
# route - `topics.CONDITIONS` is the engine's own list of them, so gout, piles and sciatica are
# fenced without being written twice.
A_WORD_OF_ITS_OWN = frozenset("""
    bella bell bully chesty chess earns glut glum heady heal heap heat heed tommy threat
    """.split())


def _a_word_rather_than_a_typo(word):
    """True when the word is a word already, so it is never read as a part typed wrong.

    The conditions list is imported here rather than at the top because `topics` imports this
    module for its gut words, and the reading is only ever asked for a word the lexicon has
    never seen, which is rare enough for the import to be free.
    """
    if word in COMMON_WORDS or word in A_WORD_OF_ITS_OWN:
        return True
    from .topics import CONDITIONS
    return word in CONDITIONS


def _spell_the_parts(text):
    """The line with a part name typed one letter wrong spelled the way the tables have it."""
    repaired = text
    for word in set(re.findall(r"[a-z]+", text.lower())):
        if len(word) < 4 or _a_word_rather_than_a_typo(word):
            continue
        part = _a_part_typed_with_one_letter_wrong(word)
        if part:
            repaired = re.sub(r"\b%s\b" % word, part, repaired)
    return repaired


def _the_gut_is_settled(text):
    """True unless the only word for the gut here is "stool" and nothing else settles it.

    "my stool is loose" is a chair with a loose leg as easily as a body line, and both words in
    it are the chair's too, so the loose rule reads the line only when something in it can be
    nothing but the gut ("loose stools for 3 days", "soft stools and stomach ache", "runny
    stools"). A line with only the shareable words is the furniture, which is what the person
    owning a stool in their kitchen means by it.
    """
    words = set(re.findall(r"[a-z']+", text.lower()))
    if not words & {"stool", "stools"}:
        return True
    return bool(words & set(A_GUT_ONLY.findall(text.lower())))


def read(text):
    """The part of the body the speaker says is unwell, or None.

    `text` is the line, lowercased and with the typed short forms spelled out.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    # The line comes with the normaliser's clause break in it ("i am hot and | i am cold"), which
    # is a mark of where the sentence was split rather than a word the person said, so it is
    # taken out. A shape that runs across the break - "im hot and then im cold" - is one thing
    # said in two halves, and the two words either side of the "and" are still one breath.
    text = _spell_the_parts(text.replace("|", " "))
    if (A_LOOSE_STOOL.search(text) and not A_SAMPLE.search(text)
            and not A_POO_COLOUR.search(text) and not A_CHAIR_WORD.search(text)
            and not A_THING_IS_TERRIBLE.search(text)
            and not _someone_else(text) and _the_gut_is_settled(text)):
        return "stomach"
    sample = bool(A_SAMPLE.search(text))
    for name, pattern, nouns in PARTS:
        if name == "teeth" and _an_abscess_elsewhere(text):
            continue
        if name == "stomach" and sample:
            continue                     # "my stool sample", not a stomach
        for match in re.finditer(pattern, text, re.I):
            # The words in front of the part are read up to the end of it, so the verb that
            # carries it ("i feel sick") is part of what says whose it is.
            if _the_speakers(text, match.end(), nouns, match.start()):
                return name
            if ASKING.search(text) and not _someone_else(text):
                return name
            if _just_the_part(text, match) and not _someone_else(text):
                return name
    return _said_about_itself(text)


def _the_speakers(text, at, nouns, began=None):
    """True when the words in front of the part make the illness the speaker's own.

    "my head is pounding" and "i have a fever" are the speaker's. "my son has a fever" is the
    child's, "she gets migraines" is hers, and "my room temperature is 40" is a room's: a "my"
    only makes the part the speaker's when the part itself comes next.

    `began` is where the match starts, when the caller knows it: the words between the speaker
    and the complaint are then read too, for the complaints the person says with the verb as
    the whole predicate ("i threw up twice", "i vomited", "i cant stop being sick").
    """
    words = re.findall(r"[a-z']+", text[:at])
    owner = None
    for index, word in enumerate(words):
        if word in kinds.OTHER_PEOPLE or word == "my":
            owner = (word, index)
    if owner is not None:
        word, index = owner
        if word != "my":
            return False          # a person was named after the last "my": theirs, not ours
        return bool(words[index + 1:index + 2]) and words[index + 1] in nouns
    # Six words of the clause in front of the part say whose it is. Spelled out, "im" is "i am"
    # and "ive" is "i have", which is two words where the person typed one, so a six-word window
    # can cut the subject off its verb: "im hot one minute and cold" was the speaker's and
    # "i am hot one minute and cold" was nobody's. The window takes a word in while it opens on a
    # verb that needs the one before it.
    start = max(0, len(words) - 6)
    while start > 0 and words[start] in _A_VERB_NEEDING_ITS_SUBJECT:
        start -= 1
    tail = " ".join(words[start:])
    tail = re.sub(r"\bi'?m\b", "i am", tail)
    tail = re.sub(r"\bi'?ve\b", "i have", tail)
    tail = re.sub(r"\bwe'?re\b", "we are", tail)
    tail = re.sub(r"\bwe'?ve\b", "we have", tail)
    if SPEAKER_ILL.search(tail) or kinds._speaker_before(text, at):
        return True
    if began is None:
        return False
    return _the_speaker_is_the_subject(words, len(re.findall(r"[a-z']+", text[:began])))


# What may stand between the speaker and the complaint and leave it theirs: a negation, a
# helper, an adverb, or the words that turn a complaint into one they cannot stop ("i cant stop
# being sick", "i keep throwing up"). A noun or a second subject in between takes it away
# ("i made the kids throw up", "i hope the dog is sick"), because then the complaint is not
# about the speaker.
_BEFORE_THE_COMPLAINT = frozenset("""i we am is are was were be been being have has had got
    get gets getting keep keeps kept stop stops stopped can cannot cant can't could couldnt
    couldn't not dont don't never still just only also really so very badly feel feels felt
    again night days woke up started begin began""".split())

# A complaint after one of these is a maybe, not what happened: "im so nervous i could be sick"
# is dread, and the stomach's answer is the wrong one for it. It is what happened when the word
# after it turns it back into an account of something ("i could not stop being sick").
_A_MAYBE = frozenset("could might may would should must can".split())
_A_NO = frozenset("not never cant cannot couldnt couldn't didnt didn't".split())


def _only_the_fillers_between(between):
    """True when nothing but a helper, a negation or an adverb stands between speaker and part."""
    if between and between[0] in _A_MAYBE:
        if not (len(between) > 1 and between[1] in _A_NO):
            return False
        between = between[1:]
    return all(word in _BEFORE_THE_COMPLAINT for word in between)


def _the_speaker_is_the_subject(words, began):
    """True when a first-person subject is the one the complaint is about.

    "i threw up twice last night" and "i vomited" carry no helper the illness window knows, so
    the subject was not found and the line was read as naming nobody: a person who had been
    sick all night got the sleep pool. The first person in front of the complaint, with nothing
    but a negation, a helper or an adverb between, is the person it happened to.
    """
    for index in range(len(words) - 1, -1, -1):
        if words[index] not in ("i", "we"):
            continue
        if _only_the_fillers_between(words[index + 1:began]):
            return True
    return False


# The verbs that carry an illness are the ones the window must not open on, because the subject
# is the word in front of them: "i am", "i have", "we were", "i keep".
_A_VERB_NEEDING_ITS_SUBJECT = ("am", "is", "are", "was", "were", "be", "been", "being", "have",
                               "has", "had", "ve", "feel", "feels", "felt", "keep", "keeps")


# The speaker is the one who has it, without "my": "i have a fever", "ive had a headache all
# day", "i keep getting migraines", "i feel sick". Spelled out first, because "ive" and "im" are
# what people type.
SPEAKER_ILL = re.compile(
    r"\b(?:i|we) (?:both |also |all )?(?:have|had|has|got|get|getting|having|been|being|keep|"
    r"keeps|keeping|am|was|are|were|feel|feeling|felt|suffer\w*|with)\b")


# A line that is only the complaint is the person saying they have it: "headache", "sore
# throat", "bad stomach ache" are "i have a headache" with the front cut off. They were read as
# naming no part at all, so a person who typed "headache" got "Got it. Is there anything you'd
# like a hand with?" while "i have a headache" got the water-and-a-dark-room answer. The words
# left over have to be a quantity or a qualifier ("really bad", "a bit of"), so "migraine
# tablets" and "headache clinic" keep their own reading.
FILLER = frozenset("""a an the my some this that bit of a really very so proper proper
    bad worse worst sore slight terrible awful horrible nasty mild chronic another again
    another little quite too pretty still""".split())


# The patterns above spell out the shapes people use, and each row also carries the nouns the
# part is called. A row's own noun with a word of pain beside it is that part however the
# sentence is built round it, and a few of those sayings reached no pool at all: "my belly
# hurts", "my gut hurts" and "belly ache" got "Is it getting better, worse, or about the same?",
# "sore tooth" got a question about how long, and "my gum is killing me" got nothing - while
# "my tummy hurts", the same complaint with the other word for it, got the stomach answer. So
# after the patterns, every noun each row owns is read with a word of pain beside it.
#
# Two rows are left out. A chest is the safety module's: "my chest hurts" is the emergency and
# the pattern row is only the chest infection on purpose. And a temperature is a number rather
# than a part - "my temperature" with a word of pain beside it is not a saying anybody has.
PLAIN_SKIP = frozenset(("chest", "temperature"))
# A jaw is the teeth row's word, but a jaw is not a tooth: the heart attack that starts in the jaw
# ("my jaw hurts and my left arm is numb", "i have jaw pain and im sweating") must not be handed
# the dentist's pool, and a jaw that hurts on its own already has its own answer, which is about
# the joint rather than the teeth. So the plain rule leaves the word to the tables that know it.
PLAIN_SKIP_WORDS = frozenset(("jaw",))
# A word of pain close enough to the part to be about it. The lexicon's own list, plus the
# ways people say a part is unwell without a word for pain in them ("bad belly", "upset
# stomach"); "my bad" is not a part, so the apology is never read as one.
PLAIN_PAIN = frozenset(lexicon.PAIN_WORDS) | frozenset(("bad", "cramping", "cramps", "upset"))
# The words that say when a complaint happened and nothing else. They do not say whose it is,
# so they leave a line of only the complaint the speaker's own: "throwing up all night".
WHEN_IT_HAPPENED = frozenset("""today tonight yesterday morning mornings afternoon afternoons
    evening evenings night nights week weeks weekend weekends month months day days all since
    last this now again every hour hours minute minutes am pm o clock time times midnight noon
    monday tuesday wednesday thursday friday saturday sunday once twice three four five six ten
    couple few several""".split())

# A helper left over in front of a complaint whose person was cut off: "was sick twice today",
# "been throwing up since midnight", "kept being sick". The helper says it happened; the time
# says when; the person is the one typing.
_A_HELPER_BEFORE = frozenset("be been being am is are was were keep keeps kept still just".split())

# A word of pain written in front of the part, as people write it: "sore throat", "bad tooth",
# "aching knee", "upset stomach". Only the shapes an adjective takes, because a verb in front
# of the part has a subject of its own: "how do i stop my headphones hurting my ears" is the
# headphones, and the ears are what they hurt.
PAIN_ADJECTIVE = frozenset("""sore painful aching achy bad swollen cramping crampy upset stiff
    throbbing stinging burning numb rough dodgy awful terrible horrible rubbish queasy
    trouble troubles""".split())
# What may stand between the part and its word of pain and leave them one thing: a be-word or
# an auxiliary and the small words people put round them. "my throat is really sore" is the
# part and the pain two words apart, while "my tooth is coming through and hurts" is a tooth
# doing something else, and the pain is about the coming through.
PAIN_BETWEEN = frozenset("""is am are was were be been being feels feel felt gets getting got
    gone keep keeps kept very really so too quite a bit little just now still often always""".split())
PAIN_REACH = 3
# Whose part is being talked about, for the one word that is not only a state. "off" is a
# particle as well as a way of saying a part is wrong, so a part with "off" straight after it and
# nothing at all between them is the phrasal verb far more often than a complaint: "im gonna head
# off", "head off" and "im gonna head off to the shop" were all read as a sore head and answered
# with "water, food, a painkiller and twenty minutes away from a screen". Whose it is decides it -
# "my stomach's off" and "my stomach is off" say whose stomach, and "head off" says nothing about
# anybody's part at all.
POSSESSIVE = frozenset("my his her their our your".split())
# The words that say a part is unwell without naming any pain in it: "my stomach is off", "my
# guts are rough". They only count beside a part, which is why they can be as ordinary as "off".
PLAIN_UNWELL = frozenset("""off rough bad awful terrible horrible rubbish dodgy queasy
    trouble troubles unhappy wrong grim""".split())
# "off" is both a way of saying a part is unwell ("my stomach is off") and the commonest
# preposition in the language, so a part with a word of "off" after it is not a complaint:
# "how do i get chewing gum off a rug" was read as a gum in a mouth and answered with a dentist
# and a spreading infection. It counts as the unwell word only when the line stops there or goes
# on about time and degree ("off for days", "off all week", "off again").
OFF_MAY_GO_ON = frozenset("""and but for since today tonight now still again all most
    lately recently days weeks months hours mornings afternoons evenings nights every
    couple few several very really quite bit little""".split())
# Two words that say the same thing together and nothing at all apart: "my guts are in knots",
# "my belly is playing up". Each half is an ordinary word, so only the pair counts.
PAIN_PHRASE = (("playing", "up"), ("acting", "up"), ("in", "knots"), ("in", "bits"),
               ("in", "a", "knot"), ("all", "over", "the", "place"), ("giving", "me", "grief"),
               ("giving", "me", "jip"))


def _an_unwell_word(words, at):
    """True when this word says the part before it is unwell, not that it is a preposition."""
    word = words[at]
    if word in PLAIN_PAIN:
        return True
    if word not in PLAIN_UNWELL:
        return False
    if word != "off":
        return True
    return at + 1 >= len(words) or words[at + 1] in OFF_MAY_GO_ON


def _pain_after(words, index):
    """True when the part is what the word of pain is about: "belly hurts", "throat is sore"."""
    for step in range(1, PAIN_REACH + 1):
        at = index + step
        if at >= len(words):
            return False
        if _an_unwell_word(words, at):
            # See POSSESSIVE: "head off" is a leaving and "my stomach's off" is a stomach.
            if words[at] == "off" and not (index > 0 and words[index - 1] in POSSESSIVE):
                break
            return True
        if words[at] not in PAIN_BETWEEN:
            break
    return _phrase_after(words, index)


def _phrase_after(words, index):
    """True when one of the phrases that says a part is unwell comes right after it."""
    for phrase in PAIN_PHRASE:
        at = index + 1
        for word in phrase:
            if at < len(words) and words[at] in PAIN_BETWEEN:
                at += 1
            if at >= len(words) or words[at] != word:
                break
            at += 1
        else:
            return True
    return False


def _said_about_itself(text):
    """The part from a row's own noun and a word of pain beside it, or None.

    Whose it is, is the same question the patterns ask: the speaker's own part is read, and a
    part that belongs to somebody else ("my son has a bad tummy", "my husband has a sore
    throat") is theirs. A pain word in front of the part says the part itself is unwell, so
    the rest of that line can say anything; a part that the pain follows has to be the
    speaker's own ("my belly hurts"), or the whole line the complaint ("belly ache").
    """
    found = list(re.finditer(r"[a-z']+", text))
    words = [match.group() for match in found]
    for index, word in enumerate(words):
        for name, _pattern, nouns in PARTS:
            if name in PLAIN_SKIP or word in PLAIN_SKIP_WORDS or not _the_part_word(word, nouns):
                continue
            in_front = index > 0 and words[index - 1] in PAIN_ADJECTIVE
            if not (in_front or _pain_after(words, index)):
                continue
            if _the_speakers(text, found[index].end(), nouns, found[index].start()):
                return name
            if index > 0 and words[index - 1] in ("my", "our", "me"):
                return name
            if index == 0 and _pain_after(words, index):
                return name          # the part leads the line: "stomachs been off for days"
            if _someone_else(text):
                continue
            if in_front or _just_the_part_words(words, index):
                return name
    return None


def _the_part_word(word, nouns):
    """The row's noun this word is, or None. A missing apostrophe and a plural both count:
    "bellys bad", "tummys rough", "my guts are in knots"."""
    if word in nouns:
        return word
    bare = word
    if bare.endswith("'s"):
        bare = bare[:-2]
    elif bare.endswith("s"):
        bare = bare[:-1]
    return bare if bare in nouns else None


def _just_the_part_words(words, index):
    """True when the part and words of pain are all the line says ("sore tooth", "bad belly")."""
    rest = words[:index] + words[index + 1:]
    allowed = FILLER | PLAIN_PAIN | PLAIN_UNWELL | PAIN_BETWEEN
    return all(word in allowed for word in rest)


def _just_the_part(text, match):
    """True when the part and when it happened are all the line says: "headache all week".

    A complaint with the front cut off is still the speaker's own when the rest of the line
    only says when it happened ("throwing up all night", "sore throat since tuesday", "sick
    twice today"): the time says when, not whose, and nobody describes somebody else's night
    that way without naming them.
    """
    rest = (text[:match.start()] + " " + text[match.end():]).strip()
    words = re.findall(r"[a-z']+", rest)
    return all(word in FILLER or word in WHEN_IT_HAPPENED or word in _A_HELPER_BEFORE
               or word.isdigit() for word in words)


def _someone_else(text):
    """True when a person other than the speaker is named anywhere in the line."""
    for word in re.findall(r"[a-z']+", text):
        if word in kinds.OTHER_PEOPLE or word.rstrip("s") in kinds.OTHER_PEOPLE:
            return True
    return False
