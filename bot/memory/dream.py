"""The reading of a line that is about a dream, and the scene the dream was made of.

A dream is a scene rather than an event, and the words of one are the words of the real thing:

    i dreamt my dad died              the loss composer offered sympathy for a death
    i keep dreaming my teeth fall out a child's milk teeth were explained
    i had a dream my house was on fire  "ugh, that's a lot to carry"

One reading serves all three, because the only thing that separates a dream from the event is the
frame around it - `dreamt`, `dreamed`, `i had a dream`, `i keep dreaming`. It is here rather than
in one module because three readers need it: `bot/modules/dreams.py` answers the dream,
`bot/compose/loss.py` has to stand down when the death is inside one, and the knowledge entries
have to stand down when the tooth or the fire is inside one.

The frame is read the way the sentence is built: the dream verb comes *before* the scene it is
about, and the speaker is in it. That is what keeps two other lines out:

    my dad died and i dreamt about him      the death is real, and it came first
    why do we dream / what do dreams mean   nobody in the line is dreaming
"""
import re

DREAM = re.compile(r"\b(dreamt|dreamed|dreaming|dream|dreams)\b")
FIRST_PERSON = re.compile(r"\b(?:i|im|i'm|ive|i've|id|i'd|my|me)\b")
# A nightmare is named rather than dreamt, and `bot/knowledge/sleep.py` already answers it well,
# so a line that says the word is left to that entry.
NAMED_A_NIGHTMARE = re.compile(
    r"\b(?:nightmares?|night terrors?|(?:bad|scary|terrible|awful|horrible)\s+dreams?)\b")
# A dream somebody is working towards is not a dream they had: "i dream of one day owning a
# house" and "i have a dream" are wishes, and there is nothing to read a scene out of.
A_WISH = re.compile(r"\bdream(?:s|ing)?\s+of\b|\b(?:i|we)\s+have\s+a\s+dream\b(?![^.]*\b(?:last|other)\s+night)\b")
# "i dream of ending it all", "i dream about killing myself": `dream of` and `dream about` are also
# how people say a wish, and a wish to be gone is not a night dream. Read as a scene it took the
# crisis card off the line and answered the dream instead - the worst trade this reading can make.
A_WISH_TO_BE_GONE = re.compile(
    r"\bdream(?:s|t|ed|ing)?\s+(?:of|about)\s+(?:my\s+own\s+|me\s+|being\s+)?"
    r"(?:ending\s+it(?:\s+all)?|ending\s+things|ending\s+my\s+life|ending\s+everything|"
    r"kill(?:ing)?\s+myself|suicide|suicidal|dying|death|being\s+dead|dead|not\s+waking|"
    r"not\s+being\s+here|disappearing|gone\s+for\s+good)\b", re.I)
# A dream said as a verb - dreamt, dreamed, dreaming - is always a night dream, whatever noun
# follows it: "i dreamt my dream job was awful" is a dream about the job.
DREAM_VERB = re.compile(r"\b(?:dreamt|dreamed|dreaming)\b")
# Said plainly, a wish to be gone is not a scene even with a dream verb in front of it:
# "i dreamt i wanted to die" is a wish the person told in a dream. Only the strong phrasings go
# here - "i dreamt my nan died" and "i dreamt i was dead" are still dreams about a death.
A_SAID_WISH = re.compile(
    r"\b(?:ending\s+it\s+all|ending\s+things|kill(?:ing)?\s+myself|kill\s+me|suicide|suicidal|"
    r"want(?:ed|ing)?\s+to\s+die|wanted\s+to\s+be\s+dead|wish(?:ed)?\s+i\s+(?:was|were)\s+dead|"
    r"not\s+being\s+here|not\s+here\s+any\s+more|don'?t\s+want\s+to\s+be\s+here)\b", re.I)

# A dream somebody is working towards is a plan, not a night: "my dream job is nursing but i have
# no qualifications" is a question about nursing, and "dream <noun>" is not a dream frame at all.
A_DREAM_AHEAD = re.compile(
    r"\bdream(?:s)?\s+(?:job|jobs|career|role|home|house|flat|holiday|holidays|trip|car|"
    r"wedding|team|life|garden|kitchen|body|figure|man|woman|partner|business|company|"
    r"kitchen|room|wardrobe|outfit)\b")
A_SCENE_OF_NOTHING = re.compile(r"^(?:about\s+)?(?:it|that|this|him|her|them|one)?$")


def the_scene(line):
    """What the dream was about, or None when the line is not a dream somebody had."""
    text = " ".join(str(line or "").lower().split())
    if not text or len(text) > 400:
        return None
    if NAMED_A_NIGHTMARE.search(text):
        return None
    found = DREAM.search(text)
    if not found:
        return None
    before = text[:found.start()]
    if not FIRST_PERSON.search(before):
        return None
    scene = text[found.end():].strip(" ,.:;!-")
    if A_WISH.search(text) or "one day" in scene or A_SCENE_OF_NOTHING.match(scene):
        return None
    if A_WISH_TO_BE_GONE.search(text) or A_SAID_WISH.search(text):
        return None
    if A_DREAM_AHEAD.search(text) and not DREAM_VERB.search(text):
        return None
    return scene or None


def named(line):
    """True when the line is a dream the speaker had, so a reader of the scene stands down."""
    return the_scene(line) is not None


def dreamed_before(line, pattern):
    """True when `pattern` is found inside the dream and not before it.

    `i dreamt my dad died` is a dream; `my dad died and i dreamt about him` is a death with a
    dream after it, and the death is what the line is for.
    """
    text = " ".join(str(line or "").lower().split())
    scene = the_scene(text)
    if scene is None or not pattern.search(scene):
        return False
    return not pattern.search(text[:text.find(scene)])


# The follow-up that settles it: the person says the dream was only a dream and the one in it is
# all right. It names no dream frame of its own - the frame is in the turn before it - so nothing
# here reads it as a dream, and `hes fine its just a dream` after "i dreamt my dad died" was met
# by the loss composer with "I'm here. Take your time with it", sympathy for a bereavement that
# the same person had just said did not happen. The words "just a dream" are the denial itself,
# and they are what this reads; the one-in-it-is-fine arm only counts when a dream was told in
# the turn before (see `bot/modules/dreams.py`), so "hes fine" about a real accident is untouched.
SETTLED_IT = re.compile(
    r"\b(?:just|only)\s+(?:a\s+|an\s+)?(?:bad\s+|weird\s+|strange\s+|silly\s+|daft\s+)?"
    r"(?:dream|nightmare)\b|"
    r"\b(?:it|that|this)\s+(?:was|were|is)\s+(?:only\s+|just\s+)?(?:a\s+)?"
    r"(?:dream|nightmare)\b|"
    r"\bnot\s+real\b|\bwasn'?t\s+real\b|\bnever\s+happened\b|"
    r"\b(?:he|she|they|it)(?:'s|\s+is|\s+was|\s+were)?\s+"
    r"(?:fine|ok|okay|alright|all\s+right|safe|still\s+here|still\s+alive|alive)\b",
    re.I)


# What people say when the scene was a dream.
DREAM_NAMED = re.compile(
    r"\b(?:i|we)\s+(?:just\s+)?(?:had\s+(?:a\s+|the\s+|this\s+)?(?:dream|nightmare|bad\s+dream)"
    r"|(?:had|have)\s+(?:a\s+|this\s+)?(?:dream|nightmare|nightmares|bad\s+dreams?|weird\s+dreams?)"
    r"|dream(?:t|ed|ing)?(?:\s+about|\s+that|\s+of|,|\s+i\b)"
    r"|keep\s+dreaming|kept\s+dreaming|nightmares?\s+(?:about|where|that)"
    r"|(?:was|were)\s+dreaming)\b",
    re.I)
# A dream said in the third person, or said after the fact: "last night i saw myself drowning".
DREAM_NAMED_LOOSE = re.compile(
    r"\b(?:in\s+(?:my|a|the)\s+dream|in\s+my\s+nightmare|in\s+dreams?|"
    r"dreamt|dreamed|dreaming|nightmares?|nightmare)\b",
    re.I)
# It is not a dream, it is happening: a body, a room, a moment.
DREAM_IS_HAPPENING_NOW = re.compile(
    r"\b(?:woke\s+up|woken\s+up|wake\s+up|awake|awoken|"
    r"still\s+(?:there|here|going|on|going\s+on|burning|bleeding|hurting|happening|smoking|"
    r"happens|feel|feels|have|got)|"
    r"right\s+now|just\s+now|this\s+minute|at\s+the\s+moment|"
    r"and\s+i\s+(?:can'?t|cannot|cant)\s+(?:breathe|move|feel|stop)|"
    r"it\s+(?:is|was)\s+real|"
    r"i\s+(?:can|could)\s+smell\s+(?:smoke|gas|burning)|"
    r"i\s+(?:have|took|taken|swallowed|drank|drunk)\s+(?:them|it|the|some|a\s+few|"
    r"\d+|all\s+of)|\b\d+\s+(?:of\s+them|tablets|pills)|"
    r"i\s+am\s+(?:bleeding|burning|stuck|trapped|drowning|having|on\s+fire)|"
    r"i'?m\s+(?:bleeding|burning|stuck|trapped|drowning|having|on\s+fire|not\s+breathing)|"
    r"my\s+(?:arm|leg|chest|head|back|side|stomach|belly|hand|foot|face)\s+(?:is\s+|feels\s+)?"
    r"(?:numb|bleeding|swollen|hot|painful|hurts|broken|blue)|"
    r"there\s+(?:is|are)\s+(?:smoke|flames?|blood|pain)|"
    r"the\s+(?:smoke|flames?|alarm|bleeding)\s+(?:is|are)\s+(?:still|now|real)|"
    r"(?:i\s+|we\s+)?(?:can\s+)?(?:smell|smells|smelling)\s+(?:smoke|gas|burning)|"
    r"\b(?:smoke|flames?)\s+(?:is\s+|are\s+)?(?:coming|pouring|everywhere)|"
    r"\balarm\s+(?:is\s+|keeps\s+)?(?:going|beeping|sounding)|"
    r"\b(?:is|are)\s+(?:going|happening)\s+(?:on\s+)?now|"
    # ...and the body in the room now, said about somebody else: "i dreamt my baby stopped
    # breathing and shes not breathing now" is the CPR card, not a dream about a baby.
    r"\b(?:he|she|they|it|the\s+baby|my\s+baby)(?:'s|s|\s+is|\s+was|\s+are|\s+were)?\s+"
    r"(?:not|isn'?t|wasn'?t|aren'?t|aint|ain'?t|no\s+longer)\s+"
    r"(?:breathing|moving|responding|waking|conscious|with\s+us|alive)|"
    r"\b(?:shes|hes|theyre|its)\s+(?:not|isn'?t)\s+(?:breathing|moving|responding|waking|conscious)|"
    r"\b(?:lying|lay)\s+(?:there|on\s+the\s+(?:floor|ground|bed|road))\s+(?:now|still)|"
    r"\b(?:there'?s|theres)\s+smoke\s+(?:in|coming|everywhere)|"
    r"\b(?:i\s+can\s+hear|i\s+hear)\s+(?:the\s+alarm|smoke\s+alarm|sirens))\b",
    re.I)


def told_in_the_turn_before(memory):
    """True when the turn just before this one was a dream, so a line can be about that dream.

    A follow-up that settles it names no frame of its own - "hes fine its just a dream" - and
    every reader of `SETTLED_IT` has to know that the dream is in the turn before, not in the
    line. One reading in one place: `bot/modules/dreams.py` takes the turn and
    `bot/compose/loss.py` stands down, both by asking this.
    """
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not (isinstance(turns, list) and turns and isinstance(turns[-1], dict)):
        return False
    last = turns[-1]
    if str(last.get("module") or "") == "dreams":
        return True
    return the_scene(str(last.get("user") or "")) is not None


def told_as_a_dream(line):
    """True when the line tells a dream of its own and nothing in it says the room has it.

    What a knowledge entry stands down for: "i had a bad dream last night" names no scene and the
    sleep entry is the answer to it, and "i dreamt my baby stopped breathing and shes not
    breathing now" is the room, so neither stands anything down.
    """
    return named(line) and a_dream_is_not_happening(line)


def a_dream_is_not_happening(line):
    """True when the line is about a dream and nothing in it says it is happening now."""
    if not line:
        return False
    text = str(line)
    if not (DREAM_NAMED.search(text) or DREAM_NAMED_LOOSE.search(text)):
        return False
    if A_WISH_TO_BE_GONE.search(text) or A_SAID_WISH.search(text):
        return False  # a wish to be gone, whatever verb is in front of it
    if A_DREAM_AHEAD.search(text) and not DREAM_VERB.search(text):
        return False  # "my dream job", not a night dream
    return not DREAM_IS_HAPPENING_NOW.search(text)

# The death said before the dream is in the waking life: "my dad died and i dreamt about him" is a
# bereavement that came into a dream, not a dream of a death, and the loss composer owns it.
A_DEATH_BEFORE_THE_DREAM = re.compile(
    r"\b(?:died|dying|death|dead|deaths|passed\s+away|passed\s+on|killed|funeral|buried|"
    r"cremation|widow|widowed)\b[^.]*?\b(?:dream|dreams|dreamt|dreamed|dreaming|dreamed|"
    r"nightmare|nightmares)\b",
    re.IGNORECASE)


def a_death_came_first(line):
    """True when the line names a death before it names a dream."""
    return bool(A_DEATH_BEFORE_THE_DREAM.search(" ".join(str(line or "").lower().split())))
