"""A fact about the person's own life, said on its own, gets its own turn.

People drop the shape of their life into a conversation while it is about something else:
"we live near the park", "i live in a flat", "we rent", "we have a dog", "i've got two cats".
Said mid-thread, none of them is a detail of the answer before it, and today two things can
happen instead of an answer to it:

- after a knowledge answer, the rest of that answer is handed over again: "my laptop broke"
  then "we live near the park" is answered "If there is no light on the charger at all, try
  another socket and cable" (bot/modules/greeting.py, `the_step_they_have_not_had`, whose
  `A_DETAIL_OF_IT` matches any "in/near/on the X" - the intended line there, "its fine in the
  kitchen", has no subject of its own, and "we live" does);
- the thread decides the entry: "my back hurts" then "we have a dog" is answered about a dog
  in pain, which the person never said;

and a fact with nothing else in the line is only nodded back ("Noted: you have a sister and a
brother.", "Noted: you're 34." - the `FRAMES` receipt in bot/memory/ack.py, which knows the fact
and has nothing to say about it).

What a friend does with any of these is take the fact in and ask the one thing about it. That is
all this module does, for the five shapes of ordinary life that turn up this way - where they
live, the animals in the house, the brothers and sisters they have, how old they are, and a
plain detail about somebody else in their life - so a person who mentions their dog is not
answered about their back, and a person who mentions their sister is not handed their own
sentence back. The last of those is the same fault one person out: "my mum is 71" and "my wife
works three days a week" were said back as "Noted: your mum is 71." by the composer, which knows
the fact and has nothing to say about it, and a question about the person who was mentioned is
what a friend asks.

What a friend does with "we live near the park" is take the fact in and ask the one thing about
it. That is all this module does, for the two shapes of ordinary life that turn up this way -
where they live, and the animals in the house - so a person who mentions their dog is not left
with the answer to their back.

Only a whole line is one of these facts: a line that goes on to say something else ("we have a
dog that keeps barking at the postman", "we live near the park and the gate is broken") keeps
the reading it has. A line in a heavy thread, or one carrying a symptom or a loss, is not a
fact about the shape of their life, and stands this down.
"""
import re

# Above the knowledge module (0) and below the chat module (300): the chat module has the place
# with a town name in it and the pets it knows, and it keeps those turns. This answers the lines
# it does not take, and the ones the thread would otherwise answer with the wrong entry.
PRIORITY = 100

# The two shapes, each with the lines it can be answered by: three, so a conversation that
# comes back to the same fact twice does not hear the same sentence.
_PLACES = (
    "{Where} - what's it like there?",
    "How long have you been there?",
    "{Where}, then. Is it handy for what you need?",
)

# One animal has a name and a history; more than one has the pair of them to ask about, which is
# the better question when there are two ("Two cats - do they get on?" is what a friend asks).
# The animal is named in the line, so a person who says "we have a dog" is answered about their
# dog rather than in the abstract.
_ONE_PET = (
    "{Pet} - what's their name?",
    "How long have they been with you?",
    "{Pet} - who spoils them most?",
)

_PETS = (
    "{Pets} - do they get on?",
    "{Pets} - what are their names?",
    "{Pets} - who spoils them most?",
)

# The words for a number in front of the animal, as the person said them.
_NUMBER_WORDS = {"two": "Two", "three": "Three", "four": "Four", "five": "Five", "six": "Six"}

# The words a line cannot carry and still be a fact about the shape of their life: a symptom, a
# loss, a problem. The same reader in the composer treats these as news (bot/compose/fallback.py,
# `_reads_as_heavy_news`), and a fact wrapped round one of them is a story with the fact inside.
_NOT_A_SHAPE = re.compile(
    r"\b(?:pain|pains|painful|hurt|hurts|hurting|ill|sick|poorly|dying|died|dead|death|"
    r"cancer|chemo|radiotherapy|tumour|tumor|dementia|alzheimers|alzheimer's|stroke|"
    r"hospital|hospice|funeral|buried|passed away|lost|loss|bereave\w*|griev\w*|"
    r"depress\w*|anxious|anxiety|panic|suicid\w*|self harm|crisis|emergency|"
    r"broken|leaking|damp|mould|flood\w*|evicted|eviction|arrears|debt|bailiff\w*|"
    r"divorce|separated|affair|abusive|violent|police|social services)\b", re.I)

# A verb out of these puts the line into the middle of something - a story, a plan, a complaint -
# rather than naming the shape of their life: "we have a dog that keeps barking", "we live near
# the park and the gate is broken".
_STORY = re.compile(
    r"\b(?:that|which|who|and|but|because|so|when|while|if|keeps?|kept|started|stopped|"
    r"barking|bites|bit|chewed|escaped|ran|went|got|needs?|needed|wants?|made|makes|"
    r"cost|costs|comes?|came|goes?|going|has|have|had|is|are|was|were|will|would|can|could)\b",
    re.I)

# The tone that ends a line without adding anything to it: "we have a dog tbh".
_TONE = re.compile(
    r"(?:\s+(?:tbh|tho|though|now|anyway|actually|really|literally|honestly|i\s+suppose|"
    r"i\s+guess|still|also|too|by\s+the\s+way|btw|atm|at\s+the\s+moment|lol|ha|haha|lmao|"
    r"so\s+yeah|yeah|innit|mate|dude|as\s+well))+$", re.I)

# Where they live: a place named without a town ("near the park", "in a flat", "by the river").
# A town has its own reader in the chat module ("Leeds - nice. How long have you been there?"),
# which is at a higher PRIORITY and keeps the turn; this is for the lines it does not take.
_LIVE = re.compile(
    r"^(?P<who>i|we)\s+(?:live|stay)\s+"
    r"(?P<where>(?:in|near|on|by|above|below|behind|next\s+to|opposite|at)\s+"
    r"(?:a|an|the|my|our|their|his|her)?\s*[a-z][a-z' -]{0,24})$")

# The place itself, without the direction: "we live in a flat".
_PLACE_KINDS = re.compile(
    r"^(?:in|near|on|by|above|below|behind|next\s+to|opposite|at)\s+"
    r"(?:a|an|the|my|our)?\s*(?:flat|house|home|place|bungalow|cottage|farm|boat|caravan|"
    r"car park|park|river|canal|sea|coast|beach|woods|wood|common|high\s+street|"
    r"village|town|city|estate|council\s+estate|block|tower\s+block|camper|motorhome|"
    r"shop|pub|office|station|hospital\s+car\s+park|school|church|allotment)$")

_PET = re.compile(
    r"^(?P<who>i|we)(?:'ve\s+got|\s+(?:have|got|own))\s+"
    r"(?P<num>a|an|one|two|three|four|five|six|\d+|\d+\s+)?\s*"
    r"(?P<pet>dogs?|cats?|puppies|puppy|kittens?|kitten|rabbits?|hamsters?|budgies?|parrots?|"
    r"horses?|pony|guinea\s+pigs?|tortoises?|snakes?|lizards?|geckos?|fish|gerbils?|ferrets?|"
    r"chickens?|hens?|ducks?|goats?|bees)$")


# The brothers and sisters they have: "i have a sister and a brother", "i have two brothers".
# The whole line has to be the family and nothing else, so "i have a brother who is ill" keeps the
# reading it has. Kids are left to the chat module ("Three kids. What are they into at the
# moment?"), which reads them already.
_SIBLINGS = re.compile(
    r"^(?P<who>i|we)(?:'ve\s+got|\s+(?:have|got))\s+(?P<what>"
    r"(?:(?:a|an|one|two|three|four|five|six|seven|eight|\d+|older|younger|little|big|twin|"
    r"step|half)[\s-]+)*(?:brother|sister|brothers|sisters)"
    r"(?:\s*(?:,|and)\s*)?"
    r"(?:(?:a|an|one|two|three|four|five|six|seven|eight|\d+|older|younger|little|big|twin|"
    r"step|half)[\s-]+)*(?:brothers?|sisters?)?)$")

_SIBLING_LINES = (
    "{What} - older or younger than you?",
    "{What} - do you see much of them?",
    "{What}, and do you get on?",
)

# Their age, said on its own: "im 34", "im 34 years old". A number with a measure after it is
# something else ("im 34 weeks pregnant", "im 34 kilos"), which is not a fact to ask a question
# about here.
_AGE = re.compile(
    r"^(?:im|i'm|i\s+am)\s+(?P<age>\d{1,2})(?:\s*(?:years?\s+old|yrs?\s+old|y/?o|yo|now|"
    r"today))?$")

_NOT_AN_AGE = re.compile(
    r"\b(?:weeks?|days?|months?|pregnan\w*|kilos?|kg|stone|pounds?|lbs?|miles?|minutes?|"
    r"hours?|degrees?|percent|%|cm|feet|foot|ft)\b", re.I)

_AGE_LINES = (
    "{Age} - how's this year treating you?",
    "{Age}, then. Anything you'd like to be different by {Next}?",
    "{Age} - a good age to be, or not?",
)

# Somebody else in their life, with one plain detail about them: "my wife works three days a week",
# "my brother works nights", "my cousin works in a bank", "my aunt has three kids". Said on
# its own, the composer files the fact and nods it back ("Noted: your aunt has three kids."),
# which is the reply that would fit any sentence at all. The same rule as the four shapes above
# applies one person out: take the fact in and ask the one thing about the person.
#
# Only a whole line, and only a detail this reader knows: the rest of the line is one of a few
# plain shapes, so "my mum is 71 and she keeps falling", "my sister is pregnant" and "my wife
# works three days a week and i do four" keep the reading they have. The days and the place are
# already read for the person themselves ("my brother is a chef", "my gran lives in spain"), so
# what is added here is the detail that was being filed and nodded back.
_RELATION = (
    r"mother\s+in\s+law|father\s+in\s+law|son\s+in\s+law|daughter\s+in\s+law|"
    r"sister\s+in\s+law|brother\s+in\s+law|"
    r"step\s?mum|stepmum|step\s?dad|stepdad|step\s?daughter|stepdaughter|step\s?son|"
    r"stepson|"
    r"mum|mom|mother|mam|dad|father|gran|granny|grandma|nan|nana|grandad|grandpa|grandfather|"
    r"sister|brother|son|daughter|aunt|auntie|uncle|cousin|niece|nephew|wife|husband|partner|"
    r"boyfriend|girlfriend|grandson|granddaughter|grandchild"
)

_SOMEONE = re.compile(r"^(?P<who>my|our)\s+(?P<rel>" + _RELATION + r")\s+(?P<rest>[a-z0-9 ']+)$")

# Where they work: "works in a bank", "works at tesco", "works for the council".
_SOMEONE_WORK = re.compile(
    r"^works?\s+(?:in|at|for)\s+(?:a|an|the)?\s*(?P<place>[a-z][a-z' ]{1,24})$")

# The hours they work, when the hours are the whole detail: "works nights", "works three days a
# week". The question is about the hours, because that is what the person said.
_SOMEONE_HOURS = re.compile(
    r"^works?\s+(?P<hours>nights?|days?|night\s+shifts?|shifts|weekends?|evenings?|weekdays|"
    r"part\s+time|full\s+time|(?:two|three|four|five|six)\s+days\s+a\s+week|"
    r"long\s+hours|away\s+a\s+lot)$")

# How old they are: "is 71", "is 40 years old". A number with a measure after it is something
# else, and the person's own age is read separately ("im 34").
_SOMEONE_AGE = re.compile(
    r"^is\s+(?P<age>\d{1,2})(?:\s*(?:years?\s+old|yrs?\s+old|y/?o|yo|now|today))?$")

# A child's age is not asked here: the composer already has an age-aware pool for a grown child,
# a school child and a toddler ("12 is a good age. What is he into at the moment?"), and that is a
# better answer than a flat question. The age bands live there, so this reader stands down.
_AGE_READ_ELSEWHERE = frozenset((
    "son", "daughter", "kid", "kids", "child", "children", "boy", "girl", "eldest", "youngest",
    "grandson", "granddaughter", "grandchild", "grandchildren", "grandkids",
    "stepson", "stepdaughter", "step son", "step daughter", "son in law", "daughter in law",
    "niece", "nephew",
))

# The children they have, as a count: "has three kids", "has two boys".
_SOMEONE_KIDS = re.compile(
    r"^has\s+(?P<num>\d+|one|two|three|four|five|six|seven|eight)\s+"
    r"(?P<kids>kids|children|child|boys?|girls?|sons?|daughters?|twins?)$")

# The pronoun for the person mentioned, used only as an object ("do you see much of her?"), so a
# template never has to agree with it: "them" for the ones that can be either.
_HER = frozenset((
    "mum", "mom", "mother", "mam", "gran", "granny", "grandma", "nan", "nana", "sister",
    "daughter", "aunt", "auntie", "niece", "wife", "girlfriend", "stepmum", "step mum",
    "stepdaughter", "step daughter", "mother in law", "daughter in law", "sister in law",
    "granddaughter",
))
_HIM = frozenset((
    "dad", "father", "grandad", "grandpa", "grandfather", "brother", "son", "uncle", "nephew",
    "husband", "boyfriend", "stepdad", "step dad", "stepson", "step son", "father in law",
    "son in law", "brother in law", "grandson",
))

_SOMEONE_WORK_LINES = (
    "A {Place}, then. What's that like for {them}?",
    "{Place} - is that new for {them}?",
    "A {Place}, then. Do you hear much about it from {them}?",
)

_SOMEONE_HOURS_LINES = (
    "{Hours} - does that leave much time for {them}?",
    "{Hours}, then. What's that like for {them}?",
    "{Hours} - does it suit {them}?",
)

_SOMEONE_AGE_LINES = (
    "{Age} - do you see {them} much?",
    "{Age}, then. Do you get to see {them} often?",
    "{Age} - how often do you get to see {them}?",
)

_SOMEONE_KIDS_LINES = (
    "{Num} kids - how old are they?",
    "{Num} kids, then. Do they live near you?",
    "{Num} kids - what are they into?",
)

_NUMBER_WORD = {"1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six",
                "7": "Seven", "8": "Eight"}

_MORE_THAN_ONE = frozenset(("two", "three", "four", "five", "six"))


def _more_than_one(num):
    """True for "two", "4", "10" - the count in front of the animal, when there is one."""
    said = str(num or "").strip()
    if said in _MORE_THAN_ONE:
        return True
    return said[:1].isdigit() and said not in ("0", "1")


def _line(text):
    """The line as this reader wants it: lower case, no edge punctuation, no tone on the end."""
    said = str(text or "").replace("\u2019", "'").strip().lower()
    said = said.strip(" .,!;:-\"'")
    said = re.sub(r"\s+", " ", said)
    while True:
        trimmed = _TONE.sub("", said)
        if trimmed == said:
            return said
        said = trimmed


def _a_fact_about_their_life(said):
    """The kind of fact this is, or None: "place", "pet", "siblings" or "age"."""
    if not said or "?" in said or _NOT_A_SHAPE.search(said):
        return None
    lived = _LIVE.match(said)
    if (lived and _PLACE_KINDS.match(lived.group("where"))
            and not _STORY.search(lived.group("where"))):
        return "place"
    siblings = _SIBLINGS.match(said)
    if siblings and not _STORY.search(said[siblings.end():]):
        what = _TONE.sub("", siblings.group("what")).strip(" ,")
        if what:
            return "siblings:" + what
    age = _AGE.match(said)
    if age and not _NOT_AN_AGE.search(said) and 13 <= int(age.group("age")) <= 99:
        return "age:" + age.group("age")
    pet = _PET.match(said)
    if pet and not _STORY.search(said[pet.end():]):
        num = (pet.group("num") or "").strip()
        kind = "two_pets" if _more_than_one(num) else "pet"
        return kind + ":" + num + ":" + pet.group("pet")
    someone = _SOMEONE.match(said)
    if someone:
        detail = _a_detail_about_someone(someone.group("rel"), someone.group("rest"))
        if detail:
            return "someone:" + someone.group("rel") + ":" + detail
    return None


def _a_detail_about_someone(rel, rest):
    """The plain detail said about somebody in their life, or None.

    Three shapes, each written out as the detail the person named: "work:a bank", "hours:nights",
    "age:71", "kids:three". Anything else about them is not this reader's - a symptom, a plan, a
    judgement, a line with something else after the detail, and the animals or the place they live
    in (tests/test_the_shape_of_their_life.py keeps those out of this reader). A child's age is not
    asked here either: the composer's age bands answer it better (_AGE_READ_ELSEWHERE).
    """
    said = (rest or "").strip()
    if not said:
        return None
    worked = _SOMEONE_WORK.match(said)
    if worked and not _STORY.search(worked.group("place")):
        return "work:" + worked.group("place").strip()
    hours = _SOMEONE_HOURS.match(said)
    if hours:
        return "hours:" + hours.group("hours").strip()
    age = _SOMEONE_AGE.match(said)
    if age and 1 <= int(age.group("age")) <= 99:
        if (rel or "").strip() not in _AGE_READ_ELSEWHERE:
            return "age:" + str(int(age.group("age")))
    kids = _SOMEONE_KIDS.match(said)
    if kids:
        return "kids:" + kids.group("num").strip()
    return None


def _their_pronoun(rel):
    """Somebody in their life as an object: "my mum" -> "her", "my cousin" -> "them"."""
    said = re.sub(r"\s+", " ", (rel or "").strip())
    if said in _HER:
        return "her"
    if said in _HIM:
        return "him"
    return "them"


def _where_words(said):
    """The place said back in their own words: "near the park" -> "Near the park"."""
    lived = _LIVE.match(said)
    where = lived.group("where") if lived else said
    return where[:1].upper() + where[1:]


def respond(text, memory):
    said = _line(text)
    found = _a_fact_about_their_life(said)
    if not found:
        return None
    kind, _, rest = found.partition(":")
    if kind in ("siblings", "age", "someone"):
        num, animal = rest, ""
    elif kind in ("pet", "two_pets"):
        num, animal = rest.split(":", 1)
    else:
        num, animal = "", ""
    # A heavy thread is not the place for a cheery question about the dog: after a death or a
    # diagnosis the fact is something the person said while telling the thing that matters, and
    # that thing keeps the turn.
    from ..compose import fallback
    if (fallback._the_thread_is_heavy(memory) or fallback._reads_as_heavy_news(said)
            or _THE_LINE_BEFORE_IS_HEAVY.search(_the_line_before(memory))):
        return None
    return _the_fact(kind, num, animal, said, memory)


# fallback's own read of heavy news is about the words a person says when they are telling you
# the news; the line before can carry it in a plainer word ("my friend is very ill", "my son is
# being bullied") that it does not read, and a cheery question about the dog after that is worse
# than the composer's own answer.
_THE_LINE_BEFORE_IS_HEAVY = re.compile(
    r"\b(?:ill|unwell|poorly|sick|dying|died|death|passed away|funeral|bereave\w*|griev\w*|"
    r"cancer|chemo\w*|radiotherap\w*|tumou?r|dementia|alzheim\w*|stroke|sepsis|surgery|"
    r"operation|transplant|hospice|palliative|terminal|hospital|icu|ambulance|diagnos\w*|"
    r"bully\w*|bullied|depress\w*|suicid\w*|self harm|miscarr\w*|stillborn|addict\w*|"
    r"relapse\w*|overdose\w*|sectioned|in pain|suffering)\b", re.I)


def _the_line_before(memory):
    """What the person said on the turn before this one, or "" on the first turn."""
    turns = [turn for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)]
    return str(turns[-1].get("user") or "") if turns else ""


def _the_fact(kind, num, animal, said, memory):
    if kind == "siblings":
        what = num[:1].upper() + num[1:]
        return _pick(_SIBLING_LINES, memory).replace("{What}", what)
    if kind == "age":
        line = _pick(_AGE_LINES, memory)
        return line.replace("{Age}", num).replace("{Next}", str(int(num) + 1))
    if kind == "place":
        return _pick(_PLACES, memory).replace("{Where}", _where_words(said))
    if kind == "someone":
        rel, _, detail = num.partition(":")
        return _the_someone_line(rel, detail, memory)
    if kind == "two_pets":
        line = _pick(_PETS, memory)
        count = _NUMBER_WORDS.get(num, "The")
        return line.replace("{Pets}", count + " " + _plural(animal))
    line = _pick(_ONE_PET, memory)
    return line.replace("{Pet}", ("An " if animal[:1] in "aeiou" else "A ") + animal)


def _the_someone_line(rel, detail, memory):
    """The question about the person who was mentioned: "my mum is 71" -> "71 - do you see much
    of her?"."""
    kind, _, said = detail.partition(":")
    them = _their_pronoun(rel)
    if kind == "work":
        line = _pick(_SOMEONE_WORK_LINES, memory)
        place = said.capitalize() if line.startswith("{Place}") else said
        return line.replace("{Place}", place).replace("{them}", them)
    if kind == "hours":
        line = _pick(_SOMEONE_HOURS_LINES, memory)
        return line.replace("{Hours}", said.capitalize()).replace("{them}", them)
    if kind == "age":
        line = _pick(_SOMEONE_AGE_LINES, memory)
        return line.replace("{Age}", said).replace("{them}", them)
    line = _pick(_SOMEONE_KIDS_LINES, memory)
    num = _NUMBER_WORD.get(said, said.capitalize())
    return line.replace("{Num}", num)


def _plural(word):
    """The animal as more than one, whatever the person typed: "cat" -> "cats"."""
    said = str(word or "")
    if said.endswith("s") or said in ("fish", "sheep", "deer"):
        return said
    if said.endswith("y"):
        return said[:-1] + "ies"
    return said + "s"


def _pick(pool, memory):
    """The first line of the pool this conversation has not said yet."""
    said = set()
    for turn in (memory.get("turns") or []):
        if isinstance(turn, dict) and isinstance(turn.get("bot"), str):
            said.add(turn["bot"].strip())
    for line in pool:
        if line not in said:
            return line
    return pool[0]
