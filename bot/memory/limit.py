"""A follow-up that puts a limit on the answer just given.

"how do i unblock the sink" is answered with a plunger and then the trap underneath. The next line
- "i dont have a plunger" - is not news about the person and not a new question: it is about the
answer they have just been given, and the answer already holds the steps that still work. The same
goes for "i ran out of oven cleaner" after the oven answer, and for "ive got a cat" after the ants
answer, where nothing is missing but one step has become unsafe.

So this module answers from the words of the previous answer: it cuts the answer into steps, drops
the ones the limit rules out, and says the rest back with the limit as the reason. It never asks the
knowledge base again with the limit on the end of the question - "how do i get rid of ants with a
cat in the house" reaches the rehoming-a-pet entry, which is not what the person asked.

It answers only a short line that names a limit, and only the turn after an answer. Everything else
is passed on, unchanged, to the modules that were going to answer it.
"""
import re

from ..understanding import understand as understanding
from ..compose import pick
from . import topics, tried

# Running out of the thing an answer wants: "i ran out of oven cleaner", "we're out of white
# spirit", "no bicarbonate". A product is what a person runs out of, which is why this reading is
# the one that may say the thing is not needed at all.
OUT_OF = re.compile(
    r"\b(?:i|we)(?:\s*(?:have|'ve|ve|had|'m|'re|am|are))?\s*(?:just\s+|now\s+|actually\s+)?"
    r"(?:ran out of|run out of|ran outta|am out of|are out of|m out of|'m out of|'re out of|"
    r"re out of|out of)\s+"
    r"(?:any\s+|a\s+|an\s+)?(?P<thing>[a-z][a-z' -]{1,24})"
    r"|\b(?:no|without)\s+(?:a\s+|an\s+|any\s+)?(?P<thing3>[a-z][a-z' -]{1,24})",
    re.I)

# The thing is simply not there: "i dont have a plunger", "we havent got any white spirit". This is
# not the same as running out, because what a person does not have may be a life and not a product
# ("i dont have a job"), so this reading only drops a step that names the thing and never says
# "you don't need it".
NOT_HAVE = re.compile(
    r"\b(?:i|we)\s+(?:(?:do|did|have)\s+not|do\s*n'?t|don'?t|dont|did\s*n'?t|didnt|"
    r"haven'?t|havent|hadn'?t|hadnt)\s+(?:(?:got|have|own|any)\s+)?"
    r"(?:any\s+|a\s+|an\s+)?(?P<thing2>[a-z][a-z' -]{1,24})", re.I)

# The supply the answer is about, said back as a shortage after a fault: "no hot water" after the
# boiler answer. That is not a limit on the answer's steps - nothing is dropped, the person is saying
# the boiler is still doing it wrong - and "You don't need hot water for that: check the pressure
# gauge" tells someone with a cold tap to skip the thing they are asking about. The boiler's own card
# is what answers it, so this reader stands down. Only a supply goes on the list, never a product:
# "no oven cleaner" after the oven answer is a real limit, and the answer's bicarbonate is the way out.
# The modifier is required: bare "no water" is not the supply said back, it is the damage ("my boiler is
# leaking / no water" is a burst pipe, and standing down there answered it with a shrug).
A_DETAIL_OF_THE_FAULT = re.compile(r"^(?:(?:hot|cold|running)\s+water)$", re.I)

# ... and only when the fault reported the turn before was about that plant. "my boiler is broken"
# then "no hot water" is the same fault twice; "my kettle is broken" then "no hot water" is not, and
# standing down there handed a faulty kettle the boiler's programmer card. So the reported line has to
# name something that heats the water before this reader leaves the turn alone.
A_HEATING_FAULT = re.compile(
    r"boiler|heating|radiator|combi|immersion|cylinder|pilot light|"
    r"water pressure|thermostat", re.I)

# ...and only when that fault is not one with a stop in it. "my boiler is leaking" then "no hot
# water" is water coming out of it, and the boiler card's first move is the programmer; the answer
# that turn needs is the one that says turn it off at the wall switch, which is what a limit on the
# answer would have thrown away. A leak, a burst, a fume or a fire keeps the answer that stops
# things, so the shortage is not read as a detail of the fault there.
A_LEAKING_FAULT = re.compile(
    r"leak|drip|burst|pour|flood|water everywhere|water coming|spray|seep|smok|fume|soot|"
    r"flame|on fire", re.I)

# Words that say the line is about not having a thing at all, or about not having done something:
# "i dont have a clue", "we have no idea", "i dont have ants anymore" are not limits on an answer.
NOT_A_THING = re.compile(
    r"\b(?:idea|clue|time|money|the foggiest|chance|choice|room|option|ants anymore|anymore|"
    r"any more|no more|a life|a job|job|work|a car|"
    # An idiom of disbelief or reassurance is not a missing product: "no way" was read as a limit
    # on the answer and came back as "You don't need way for that: ...", and "no luck" /
    # "no bother" are the same shape.
    r"way|luck|bother|worries|worry|problem|doubt|wonder|rush|need|joke|point|sense|harm|"
    r"thanks|matter)\b", re.I)

# A pet or a small child in the house rules out poison and traps, which is a different kind of limit
# from a missing product: nothing is missing, one step has become unsafe.
IN_THE_HOUSE_WORDS = (r"cat|cats|kitten|kittens|dog|dogs|puppy|puppies|rabbit|rabbits|"
                       r"hamster|hamsters|guinea pig|budgie|parrot|tortoise|child|children|kid|"
                       r"kids|toddler|baby|son|daughter")
IN_THE_HOUSE = re.compile(
    r"\b(?:(?:i|we)(?:\s+have|'ve|ve|got)?\s+(?:got\s+|have\s+)?(?:a|an|two|three|our|my)\s+"
    r"(?P<who>" + IN_THE_HOUSE_WORDS + r")\b"
    r"|(?:there'?s|theres)\s+(?:a|an)\s+(?P<who2>" + IN_THE_HOUSE_WORDS + r")\s+"
    r"(?:in the house|here|at home))", re.I)

# A second one said in the same breath: "i have a dog and a toddler" is both of them, and a reply
# that names the dog and drops the toddler has read half the line.
ALSO_THERE = re.compile(r"\s*(?:,|and|plus)\s+(?:a|an|the|my|our|two)\s+(?P<who3>"
                        + IN_THE_HOUSE_WORDS + r")\b", re.I)

# The steps a pet or a child rules out. A trap is not poison, but a cat that puts a paw in one is
# the same kind of accident, so it goes with the bait.
NOT_WITH_A_PET = re.compile(
    r"\b(?:bait|baits|baited|poison|poisoned|pellets?|killer|insecticide|rodenticide|"
    r"spring ?traps?|mousetraps?|rat traps?|glue ?boards?|ant powder|ant spray|blue grains)\b",
    re.I)

# "i only have vinegar" is deliberately not here. Saying which one thing they do have does not
# say which step the answer loses, and the reply it invites - "With only vinegar, make a paste of
# bicarbonate of soda and water" - contradicts itself. That line is left to the modules that read
# what a person has.

# A line with a question of its own is answered by the module that answers questions: "i dont have a
# plunger, what else works?" is a new ask, not a limit on the last answer.
ASKS = re.compile(r"\?|\b(?:how|what|why|when|which|should|can|could|would|do i|is there)\b", re.I)

# A line that names a meal to choose is an ask of its own even with no question mark in it: "dinner
# ideas with no pasta" and "meal ideas without cheese" want a dinner, not the answer just given with
# a step dropped. Read as a limit after a dish that had pasta in it, the first of those was answered
# "You can't do the first step without the pasta, and the rest of that answer is done after it".
ASKS_A_CHOICE = re.compile(
    r"\b(?:ideas?|dinners?|meals?|lunches?|suppers?|breakfasts?|recipes?|suggestions?)\b", re.I)

# A limit names a thing and not a clause: "no i meant the other one" is a correction, and read as a
# limit it told somebody they did not need "i meant the other one" for the job. Only the first word
# is looked at, because a thing can carry one of these inside it ("no gym near me").
CLAUSE_STARTS = frozenset("""i im i'm ive iv we you it its it's that this there they he she
    meant mean wants want wanted needs need think thought know knew said say says told ask asked
    just really actually yes no thanks sorry""".split())

# A clause is a step: "wipe the trail away with vinegar and water", "leave it overnight". This is
# only used to decide whether a piece of the answer can stand on its own, so it is a wide set of the
# verbs an instruction opens on.
STEP = re.compile(
    r"^(?:start|begin|use|put|place|leave|let|keep|wipe|rub|mix|make|add|take|coat|scrub|brush|"
    r"soak|pour|drain|wash|rinse|blot|hang|air|open|close|undo|unscrew|pull|lift|fill|top|cut|"
    r"trim|cover|seal|spray|check|turn|hold|run|go|get|do|give|ask|book|call|wait|set|sit|"
    r"stand|watch|pick|dig|move|remove|replace|clean|unplug|vacuum|sweep|boil|simmer|bake|"
    r"rest|chill|store|freeze|test|look|try|screw|tighten|loosen|slide)\b", re.I)

# An "and" that joins two steps, not two things: "wipe the trail and put bait down" is two, and
# "bicarbonate of soda and water" is one.
AND_STEP = re.compile(
    r"\s+(?:and|then|so|but)\s+(?=(?:start|begin|use|put|place|leave|let|keep|wipe|rub|mix|make|"
    r"add|take|coat|scrub|brush|soak|pour|drain|wash|rinse|blot|hang|air|open|close|undo|unscrew|"
    r"pull|lift|fill|top|cut|trim|cover|seal|spray|check|turn|hold|run|go|get|do|give|ask|book|"
    r"call|wait|set|sit|stand|watch|pick|dig|move|remove|replace|clean|unplug|vacuum|sweep|boil|"
    r"simmer|bake|rest|chill|store|freeze|test|look|try|screw|tighten|loosen|slide)\b)", re.I)

# How the limit is said back. A product is said in the step itself ("skip the plunger: undo the trap
# underneath"), so that reply opens on the step; with only one thing, or a cat in the house, the
# limit is the reason the step is out, so it leads.
LEADS = {"pet": "With {who} in the house, "}

# How many words a limit is. A sentence with the day in it ("i ran out of oven cleaner last week and
# i keep forgetting to buy more") is a story, and the answer is not the reply to it.
LONGEST = 9

# The words in an answer that make it an answer about something being done, so a product the person
# never mentioned can be called unnecessary rather than needed: "i ran out of oven cleaner" after a
# how-to. Nothing else gets that sentence, because a line that is not about a job ("i dont have a
# job") must not be told it is not needed.
def words_of(text):
    return re.findall(r"[a-z']+", str(text or "").lower())


# A thing the line names, saying what it lacks: "my shower has no water pressure", "the fridge has
# no power", "my phone has no signal". The subject of the lack is the thing, so the line is a
# report about that thing and the card for it answers; read as a limit on the answer above, all
# three came back as "You don't need water pressure for that: <the answer to an unrelated how-to>".
# "i have no eggs" keeps its reading, because there the person is the subject of the lack and the
# thing is a supply they have run out of.
A_FAULT_IN_A_NAMED_THING = re.compile(
    r"\b(?:my|our|the|his|her|their|your|its|this|that|these|those)\s+"
    r"[a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,2}\s+"
    r"(?:has|have|had|'s|is|are|was|were|gets?|got|does|do|keeps?|comes?|shows?|gives?|"
    r"leaves?|makes?|runs?)\s+$", re.I)


def _a_fault_in_the_thing(said, found):
    """True when the words before the lack name the thing that lacks it.

    "my shower has no water pressure" is a shower that is doing something wrong, and the shower's
    own card is the answer. It is not a person running out of a product, so nothing is cut out of
    the answer above.
    """
    return bool(A_FAULT_IN_A_NAMED_THING.search(str(said or "")[:found.start()]))


def _shown(match):
    """The thing a limit names, as said, without a trailing weight, and as it is named.

    The three are not the same: "i ran out of oven cleaner for that" says the thing as "oven
    cleaner", and "i dont have ants anymore" is a phrase whose last word says the line is not about
    having a thing at all, so that word has to be read before it is thrown away.
    """
    for group in ("thing", "thing2", "thing3"):
        if match.groupdict().get(group):
            raw = " ".join(match.group(group).split())
            said = re.sub(r"\s+(?:left|anyway|though|tho|either|now|anymore|for that|for it)$",
                          "", raw, flags=re.I).strip(" .,!?;:'\"")
            # A limit is often said with the next thing after it: "i have no oven cleaner but i
            # have vinegar" is a limit on the oven cleaner and then a note about the vinegar, and
            # read whole it told the person they did not need "oven cleaner but i have v".
            said = re.split(r"\s+(?:but|and|though|although|because|so|unless|whereas)\s+"
                            r"(?=(?:i|we|you|they|it|there|he|she)\b)", said, flags=re.I)[0]
            said = _without_a_reason(said)
            said = said.strip(" .,!?;:'\"")
            # A thing is followed by where it was: "no yeast in the house" is a limit on the yeast.
            said = WHERE_IT_IS.sub("", said).strip(" .,!?;:'\"")
            return said, _bare(said), raw
    return "", "", ""


# Why they have not got it is not part of its name. "no fan because the dog chews cables" names
# the fan, and the regex that found it ran on into the reason (up to its own 24 characters, so the
# thing came out as "fan because the dog chews"), which then matched nothing the answer said: the
# reply told them "You don't need fan because the dog chews for that:" and went on to put a bowl of
# ice in front of the fan they had just said they had not got. "no ant powder because of the cat"
# came out as "ant powder because of the" and kept the step that tells a cat owner to put bait down.
# A reason is cut at the word that starts it; what it says about the house is read on its own.
A_REASON = re.compile(r"\s+(?:because|cos|coz|cus|coz of|cos of|because of|seeing as)\b.*$", re.I)

# Where the thing was when the person last looked: "no yeast in the house", "we are out of it at
# home". The place is not part of the thing's name, and read as part of it the thing matched
# nothing the answer said.
WHERE_IT_IS = re.compile(r"\s+(?:in|at|on)\s+(?:the|my|our)\s+[a-z]+(?: [a-z]+)?$", re.I)


def _without_a_reason(said):
    """The thing without the reason they said after it: "fan" from "fan because the dog chews"."""
    return A_REASON.sub("", said).strip(" .,!?;:'\"")


# A pet or a child named as the reason a thing is not there is still a pet or a child in the house:
# "no ant powder because of the cat" is the line that got the bait-and-poison answer. The words are
# the ones `IN_THE_HOUSE_WORDS` already knows, said after a reason word and a "the"/"my"/"our".
A_PET_IN_THE_REASON = re.compile(
    r"\b(?:because|cos|coz|cus|since|with|of)\s+(?:it'?s\s+)?(?:the|my|our|a|an)\s+(?P<who>"
    + IN_THE_HOUSE_WORDS + r")\b", re.I)


def _a_pet_in_the_reason(said, found):
    """The animal or child the limit was explained by, or "" when the reason names none."""
    rest = str(said or "")
    hit = A_PET_IN_THE_REASON.search(rest)
    return hit.group("who") if hit else ""


def _bare(said):
    """"oven cleaner" from "the oven cleaner", "some white spirit" from "white spirit"."""
    words = [word for word in said.split() if word.lower() not in
             ("the", "a", "an", "any", "some", "my", "our", "of", "it")]
    return " ".join(words) or said


def _the_read(said, memory):
    """The reading of the line, from the turn that already made one, or a fresh one."""
    read = (memory or {}).get("understood")
    if isinstance(read, dict) and " ".join(str(read.get("text") or "").split()).strip(" .,!;:") == said:
        return read
    return understanding(said, {}) or {}


def reads_as_a_limit(text, memory=None):
    """(kind, the thing as said, the thing as named) for a line that limits the last answer."""
    said = " ".join(str(text or "").split()).strip(" .,!;:")
    if not said or len(words_of(said)) > LONGEST:
        return None
    # A line that asks for a name is an ask, not a limit on the answer above, however it is
    # worded. "ne1 no a good plumber" is "anyone know a good plumber" typed short: the bare "no X"
    # shape found the thing, so the answer to "my boiler is broken" was handed back cut down -
    # "You don't need good plumber for that: check the pressure gauge (1 to 1.5 bar)..." - which
    # is not what was asked. `ASKS` above does not know this shape, but the reading does.
    if "recommend" in (_the_read(said, memory).get("asks") or ()):
        return None
    for kind, pattern in (("ran_out", OUT_OF), ("not_have", NOT_HAVE), ("pet", IN_THE_HOUSE)):
        found = pattern.search(said)
        if not found:
            continue
        if kind == "pet":
            who = _everyone_in_the_house(said, found)
            return ("pet", who, who)
        if ASKS.search(said.replace(found.group(0), " ")):
            return None  # the line has a question of its own, so it is an ask
        if ASKS_A_CHOICE.search(said.replace(found.group(0), " ")):
            return None  # the line asks for a meal, which is a choice and not a limit
        if _a_fault_in_the_thing(said, found):
            # The thing they name is the subject of the lack, not a product they have run out of:
            # the line reports a fault and its own card answers it.
            return None
        shown, bare, raw = _shown(found)
        if raw and raw.split()[0].lower().strip(".,!") in CLAUSE_STARTS:
            return None
        if re.search(r"\b(?:is|are|was|were|isn'?t|aren'?t)\b", bare or "", re.I):
            return None  # "no my car is fine" is a sentence about a thing, not a limit on one
        if not bare or NOT_A_THING.search(bare) or NOT_A_THING.search(raw):
            return None
        if ASKS.search(bare):
            return None
        who = _a_pet_in_the_reason(said, found)
        if who:
            # A pet or a child named as the reason is one in the house, and it is the household
            # that decides which steps are safe: only a step the answer gives that a pet rules out
            # ("no ant powder because of the cat" got "put bait down close to it") makes the reply
            # the pet one. Anything else is the plain limit, with the thing cut out.
            answer = _last_answer(memory)[0] if isinstance(memory, dict) else ""
            if answer and NOT_WITH_A_PET.search(answer):
                said_as = who if who.endswith("s") or who == "children" else "a " + who
                return ("pet", said_as, said_as)
        return (kind, shown, bare)
    return None


# A line whose whole content is what to leave out: "no walking up hills" after a weight-loss plan,
# "no long walks", "nothing too strenuous". Every word of it is the limit, so there is nothing on the
# line to look up. Read as a subject, the word after "no" is a topic like any other and the knowledge
# base answers the thing the person has just taken away: "no walking up hills" got the entry about
# riding a bike up a hill ("Change down before the hill rather than on it..."), which answers a
# cyclist, over the plan on the screen with the walking taken out of it.
#
# The reply is the composer's (`bot/compose/limit.py`), which already keeps the answer above and
# takes the ruled-out thing out of it. What is read here is only whether the line is a limit and
# nothing else: one word of its own - a person ("my sister cant walk far"), a time, a place - makes
# it a subject again, and the answer for that subject keeps its turn.
_MOVE_WORDS = frozenset("""
tiring strenuous energetic demanding exhausting exhaustive walking walk walks hike hikes hiking
hill hills stair stairs steps standing stand climbing climb lifting lift far long running run
cycling cycle bike bikes swimming swim carrying carry bending bend kneeling kneel squat squats
""".split())
# The frame a limit is said in: the negation, how much, and the words that join the phrase. None of
# these is a thing to answer about on its own.
_LIMIT_FRAME = frozenset("""
no not nothing never nowt without too very much any more most lot lots really just only still
cant cannot can can't able manage do does did done get gets up down and or but the a an my our
your his her its it that this those these there here of for in on at with to i we im me us
be being is are was were have has had about even anymore either please thanks
""".split())


# A line opens by taking something away, rather than by saying what the person can still do. "no
# walking up hills" is a revision of the plan above it; "i cant do stairs" is a complaint about the
# knee, and the card for knee pain on stairs is the answer to that one.
_LEAVES_IT_OUT = re.compile(r"^(?:and |also |but |so |then )*(?:no|nothing|not|never|nowt|without)\b",
                            re.I)


def only_a_limit(text, memory=None):
    """True when every word of the line is the limit and none of it is a subject of its own."""
    try:
        from .facts import a_limit_on_the_plan
    except Exception:  # noqa: BLE001 - the store must keep working without the reading
        return False
    said = " ".join(str(text or "").split()).strip(" .,!;:")
    if not said or len(words_of(said)) > LONGEST:
        return False
    if not _LEAVES_IT_OUT.match(said):
        return False
    try:
        if a_limit_on_the_plan(said) != "move":
            # A limit on the money ("keep it cheap") is about what kind of answer to give, and the
            # entry keyed on it is still the answer. Only a limit on the feet names a thing to
            # leave out of the answer above.
            return False
    except Exception:  # noqa: BLE001 - a line the reading cannot place is left alone
        return False
    words = [word.strip("'") for word in re.findall(r"[a-z']+", said.lower())]
    return bool(words) and all(word in _MOVE_WORDS or word in _LIMIT_FRAME for word in words)


def _everyone_in_the_house(line, found):
    """"a dog and a toddler" from a line that names both of them."""
    names = [found.groupdict().get("who") or found.groupdict().get("who2") or ""]
    rest = line[found.end():]
    while True:
        more = ALSO_THERE.match(rest)
        if not more:
            break
        names.append(more.group("who3"))
        rest = rest[more.end():]
    seen, out = set(), []
    for name in names:
        name = " ".join(name.split())
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        # Said as a person says it: "with a dog and a toddler in the house", not "with dog".
        out.append(name if name.endswith("s") or name in ("children",) else "a " + name)
    return " and ".join(out)


def _pieces(answer):
    """The answer as sentences, each split at the commas that open a new step."""
    pieces = []
    for sentence in re.split(r"(?<=[.!?])\s+", str(answer or "")):
        sentence = sentence.strip()
        if not sentence:
            continue
        clauses = [clause.strip() for clause in re.split(r",\s+(?=[a-z])", sentence) if clause.strip()]
        pieces.append((sentence, clauses))
    return pieces


def _steps(answer):
    """[(clause, sentence)] - the steps of an answer, in the order they were given."""
    out = []
    for sentence, clauses in _pieces(answer):
        for clause in clauses:
            for step in re.split(AND_STEP, clause):
                step = step.strip(" .,;:")
                if step:
                    out.append((step, sentence))
    return out


# Words that join the parts of a thing's name, so the same thing is said two ways: "bicarbonate of
# soda" and "bicarbonate soda", "a damp cloth" and "damp cloth". They are dropped from both sides
# before the thing is looked for, or an answer telling somebody to make a paste of bicarbonate of
# soda read as not naming the bicarbonate they had just said they had run out of.
JOINING = frozenset("of the a an my your our their its some any".split())


def _names(clause, thing):
    """Whether a clause names the thing, by that thing's own forms: "oven cleaner" and "cleaner".

    A two-word thing is also found with the joining word left out, and with the words the other way
    round, because a person says "bicarbonate of soda" and a thing's bare form drops the "of".
    """
    forms = topics.forms(thing)
    words = set(words_of(clause))
    if forms & words:
        return True
    want = [word for word in words_of(thing) if word not in JOINING]
    if len(want) < 2:
        return False
    got = [word for word in words_of(clause) if word not in JOINING]
    for start in range(len(got) - len(want) + 1):
        window = got[start:start + len(want)]
        if all(one == other or one in topics.forms(other)
               for one, other in zip(window, want)):
            return True
    return False


def _first_with(answer, thing):
    """The first step of the answer that names the thing, or "" if the answer never does."""
    for clause, _ in _steps(answer):
        if _names(clause, thing):
            return clause
    return ""


# A word that makes a clause a statement rather than a thing on a list: "white wine or salt are
# the old tricks" says what to do with the wine, where "7g dried yeast" only names it.
SAID_OF_IT = re.compile(
    r"\b(?:is|are|was|were|be|been|has|have|had|does|do|did|will|can|makes?|keeps?|works?|"
    r"takes?|needs?|gives?|goes|go|comes?|gets?|stays?|holds?|sits?|starts?|ends?|means?|"
    r"sounds?|clears?|pulls?|dries?|helps?|turns?|leaves?|leaving|adding|mixing|cooks?|"
    r"removes?|kills?|stops?|lasts?)\b", re.I)


# A quantity in front of a thing: "500g strong white flour", "7g yeast", "325ml warm water". A run
# of those joined by commas is what a job is made of, whatever verb the sentence opens with.
MEASURED = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:g|kg|ml|l|cl|oz|lb|grams?|kilos?|litres?|millilitres?|"
    r"tbsp|tsp|tablespoons?|teaspoons?|cups?|pints?|pinch(?:es)?|handfuls?)\b", re.I)
MEASURED_PARTS = re.compile(r",|\band\b", re.I)


# A word just before the thing that makes it an amount of it rather than a step to take with it:
# "use the same weight of soft butter", "add a splash of vinegar". The clause "use the same weight of
# soft butter" opens with a step verb and is still one item of a recipe's list.
AN_AMOUNT = frozenset("""
weight amount quantity part parts half quarter third fifth pinch splash dash drizzle
spoonful spoon spoons tablespoon tablespoons tbsp teaspoon teaspoons tsp cup cups gram grams g kg
ml litre litres ounce ounces oz pound pounds lb handful knob
""".split())


def _the_amount_of_it(clause, thing):
    """True when the thing is said as an amount: "the same weight of soft butter", "325ml water"."""
    words = words_of(clause)
    wanted = set(words_of(thing)) - JOINING
    for place, word in enumerate(words):
        if word not in wanted:
            continue
        before = words[max(0, place - 4):place]
        if any(one in AN_AMOUNT for one in before) or re.search(r"\d", " ".join(before)):
            return True
    return False


def _among_measured_things(clause, thing):
    """True when the thing is one item of a measured list: "500g flour, 7g yeast, 10g salt".

    The shopping list a recipe opens with reads as a step - "Mix 500g strong white flour, 7g yeast,
    10g salt and 325ml warm water into a soft dough" starts with the verb "mix" - so a limit that
    landed on the yeast was answered "skip the yeast" and handed back the rest of a yeasted loaf,
    which is not a bread anyone can make. The verb is about the list, not about the thing: three or
    more measured items with the thing among them make it a list, and the knowledge base keeps the
    turn.
    """
    words = str(clause or "").lower()
    if not thing or not MEASURED.search(words):
        return False
    parts = [part.strip() for part in MEASURED_PARTS.split(words) if part.strip()]
    if len(parts) < 3:
        return False
    return any(_names(part, thing) for part in parts)


def is_a_thing_on_a_list(clause, thing=""):
    """True for a step of an answer that only names a thing: "7g dried yeast", "350ml warm water".

    A list of what a job is made of is not a set of steps: bread without the yeast is not bread
    with one step fewer, and the answer to "i havent got any yeast" is the one that says what to
    make instead. So a limit that lands on a thing on a list is not answered from the steps; the
    knowledge base keeps the turn and answers the line itself.
    """
    # The clause is a step even when it opens with the joining word: "and put a bowl of ice in
    # front of a fan" is not a thing on a shopping list, and read with its "and" it matched no
    # step at all, so a limit on the fan was read as an ingredient the answer could not do
    # without and the turn was handed back unanswered. A clause that measures the thing is still
    # a list and not a step: "then fill with 3 eggs beaten with 200ml cream" is what a quiche is
    # made of, and read as a step it told somebody with no eggs to skip the eggs.
    said = str(clause or "").strip()
    tidied = _tidy(said)
    if tidied and not MEASURED.search(tidied):
        said = tidied
    if not said:
        return False
    if _among_measured_things(said, thing) or _the_amount_of_it(said, thing):
        return True
    return not STEP.match(said) and not SAID_OF_IT.search(said)


def after_an_answer(memory):
    """True when the turn before this one was an answer to a how-to, not the bot's own chatter."""
    return tried.after_an_answer(memory)


def _last_answer(memory):
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return "", ""
    last = turns[-1]
    asked = str(turns[-2].get("user") or "") if len(turns) > 1 else str(
        (memory.get("last_answer") or {}).get("question") or "")
    return str(last.get("bot") or ""), asked


def reads_the_answer(text, memory):
    """True when this limit is answered from the last answer's own steps.

    `answers` stands down on this and not on `reads_as_a_limit`, because not every limit is about
    the answer just given: "how do i clean my oven" then "i dont have any eggs" is a cooking
    question, and the answer that helps it is about what replaces an egg in a cake. Only a thing
    the answer itself asks for, or a product missing after a how-to, belongs here.
    """
    if not after_an_answer(memory):
        return False
    limit = reads_as_a_limit(text, memory)
    if not limit:
        return False
    kind, _thing, bare = limit
    answer, _asked = _last_answer(memory)
    if not answer:
        return False
    if kind == "pet":
        return _with_a_pet(answer, bare) is not None
    named = _first_with(answer, bare)
    if named:
        return not is_a_thing_on_a_list(named, bare)
    if _without_the_appliance(bare, answer, memory):
        # The answer never says the appliance, it says "bake at 200C": there is no step to cut,
        # and the card the knowledge base reaches with the limit on the end of the carried
        # question tells the person to bake anyway. This module has the answer for it.
        return True
    return bool(tried.asks_for_a_fix(memory)
                and (_about_the_job(bare, memory) or _a_fault_in_the_line_answered(memory))
                and not a_detail_of_a_fault(memory, bare))


def _the_line_answered(memory):
    """The person's line that the answer above was written for."""
    for turn in reversed([turn for turn in (memory or {}).get("turns") or []
                          if isinstance(turn, dict)]):
        if turn.get("bot"):
            return str(turn.get("user") or "")
    return str(((memory or {}).get("last_answer") or {}).get("question") or "")


def _a_fault_in_the_line_answered(memory):
    """True when the answer above was written for a thing that has gone wrong."""
    reported = _the_line_answered(memory)
    return bool(reported) and bool(tried.FAULT.search(reported.lower()))


def _about_the_job(bare, memory):
    """True when the thing they lack is part of the job the answer above was for.

    "my shower has no water pressure" and "i have no eggs" are not about the fruit fly answer
    above them, and saying "You don't need water pressure for that" hung an answer about flies on
    a fault in a shower. What a how-to may call unnecessary is a product of its own job, so the
    thing has to be named by the line that was answered or by the answer itself.
    """
    named_words = set()
    for word in words_of(_the_line_answered(memory)):
        if len(word) > 3 and word not in topics.STOPWORDS:
            named_words |= topics.forms(word)
    if not named_words:
        return False
    return any(named_words & topics.forms(word) for word in words_of(bare)
               if len(word) > 3 and word not in topics.STOPWORDS)


def reply_for(text, memory):
    """The reply a limit on the last answer deserves, or None to leave the turn alone."""
    reply = _limit_reply(text, memory)
    if reply:
        # The steps the limit left are what the next short ask is about: "whats the first thing to
        # change" a turn later is the first of them, not a new search.
        memory["limit"] = {"said": reply, "steps": _steps_the_limit_left(text, memory)}
    return reply


# A line that asks for the move out of the answer: "whats the first thing to change", "where do i
# start". It is short, it names no thing of its own, and it comes right after the limit was said.
MOVE = re.compile(r"\b(?:first|start|begin|next|step|steps|change|try)\b", re.I)


def move_after_a_limit(text, memory):
    """The first step the limit left, when the line right after it asks for the move.

    A limit reply is read from the answer behind it, so the answer is no longer the turn on the
    screen: the move ask would find nothing to pick from and stop at a search hedge, when the step
    it wants is the first one the limit kept.
    """
    record = memory.get("limit")
    if not isinstance(record, dict):
        return None
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns or str(turns[-1].get("bot") or "").strip() != str(record.get("said") or "").strip():
        memory.pop("limit", None)  # a limit reply two turns back is not what this line is about
        return None
    line = str(text or "").strip()
    if not MOVE.search(line) or len(words_of(line)) > 8:
        return None
    if topics.pairing(line) or not _names_no_thing(line):
        return None
    steps = [step for step in (record.get("steps") or []) if step]
    if not steps:
        return None
    step = steps[0].strip().rstrip(". ")
    if not step:
        return None
    return "I would start here: " + step[0].lower() + step[1:] + "."


def _names_no_thing(line):
    """True when the line names nothing of its own: "whats the first thing to change"."""
    words = [word for word in words_of(line)
             if word not in topics.STOPWORDS and word not in MOVE_ASKS and len(word) > 1]
    return not words


MOVE_ASKS = frozenset("""what whats where when which who why how first start begin next step steps
    change try do i we you should shall can could would the a an it that this there and then so
    now best thing things makes make much about on in to""".split())


def _steps_the_limit_left(text, memory):
    """The steps of the last answer that the limit does not rule out."""
    limit = reads_as_a_limit(text, memory)
    answer, _asked = _last_answer(memory)
    if not limit or not answer:
        return []
    kind, _thing, bare = limit
    if kind == "pet":
        return [step for step, _ in _steps(answer) if not NOT_WITH_A_PET.search(step)]
    return [step for step, _ in _steps(answer) if not _names(step, bare)]


def a_detail_of_a_fault(memory, bare):
    """True when the line says the fault again, in the words of the answer that was just given.

    "my boiler is broken" then "no hot water" is the same fault twice: the person is not telling the
    answer that it may leave the water out, they are telling it what the boiler is doing wrong. The
    knowledge base holds the boiler card, so this reader stands down where a product would have been
    cut out of the answer.
    """
    if not A_DETAIL_OF_THE_FAULT.match(" ".join(str(bare or "").split())):
        return False
    # The current line is not in the store yet when the modules read it, so the fault being answered
    # is the person's line of the last turn that has a reply of its own.
    reported = ""
    for turn in reversed([t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)]):
        if turn.get("bot"):
            reported = str(turn.get("user") or "")
            break
    if not reported:
        return False
    line = reported.lower()
    return (bool(A_HEATING_FAULT.search(line)) and bool(tried.FAULT.search(line))
            and not A_LEAKING_FAULT.search(line) and not tried.buying(memory))


# An appliance is not a thing *inside* the answer, it is the tool those instructions use. "a
# salmon traybake" was answered "Wrap the fish in foil... bake at 200C", and "no oven" could take
# nothing out of that answer because it never says the word oven. The answer still has to change,
# and what the person is asking is the question of its own - "what can I cook with no oven?" -
# which the knowledge base has a card for. Only where the answer in front needs the appliance:
# a hob-only answer after "no oven" is left alone by `cooking.unusable`.
APPLIANCES = ("oven", "hob", "microwave", "cooker", "stove")
NO_APPLIANCE = (
    "No {thing}, then. {answer}",
    "Right, no {thing}. {answer}",
    "Without a {thing}, then. {answer}",
)


def _without_the_appliance(thing, answer, memory):
    """What to cook without it, when the answer in front needs the thing that has gone."""
    name = str(thing or "").strip().lower()
    if name not in APPLIANCES:
        return None
    from ..knowledge import cooking  # noqa: PLC0415 - only this line asks the kitchen
    asked = "what can i cook with no " + name
    understood = {"clean": asked, "words": asked.split(), "excludes": [name],
                  "constraint": True}
    if not cooking.missing(understood):
        return None
    if not cooking.unusable(answer, understood):
        return None
    alternative = cooking.without(understood)
    if not alternative:
        return None
    alternative = alternative[:1].upper() + alternative[1:]
    return pick(NO_APPLIANCE, memory, name).format(thing=name, answer=alternative)


def _limit_reply(text, memory):
    """The reply a limit on the last answer deserves, or None to leave the turn alone."""
    if not after_an_answer(memory):
        return None
    limit = reads_as_a_limit(text, memory)
    if not limit:
        return None
    kind, thing, bare = limit
    answer, _asked = _last_answer(memory)
    if not answer:
        return None
    if kind == "pet":
        return _with_a_pet(answer, bare)
    if a_detail_of_a_fault(memory, bare):
        return None

    steps = _steps(answer)
    if not steps:
        return None
    named = _first_with(answer, bare)
    if not named:
        # An appliance the answer's instructions need is not a thing inside it: what is left is
        # the card for cooking without it, which is the question the person just asked.
        alternative = _without_the_appliance(bare, answer, memory)
        if alternative:
            return alternative
        # The answer never asks for the thing. Only a shortage said after a thing that has gone
        # wrong gets the outright line - "You don't need hot water for that:" and then what is
        # left of the fault answer, which is the stopping advice. A how-to is not that: what it
        # answers for is the products of its own job, and nothing in the line says the product is
        # one of them, so "i have no eggs" after an answer about fruit flies was answered "You
        # don't need eggs for that:" with the fruit fly answer on the end. The card for the line
        # itself is the reply, and it is in the modules below.
        if not _a_fault_in_the_line_answered(memory) or not tried.asks_for_a_fix(memory):
            return None
        return _say("You don't need " + thing + " for that: ", _up_to_words(_kept(answer, bare)))
    if is_a_thing_on_a_list(named, bare):
        # Bread without the yeast is not bread with one step fewer, so the answer behind the limit
        # is not the reply. The line is left to the knowledge base, which has a soda bread for it.
        return None
    if _names(steps[0][0], bare) and _holds_on(answer, bare):
        # The step that is out is the one the answer opens with, and what is left of it is done to
        # what that step made: topping the pressure up and then bleeding the radiators is not one
        # step fewer, it is a job that loses the pressure again. Handing the rest over would be
        # instructions for something that cannot be done, so the reply says what the job needs.
        return _needs_it(thing, answer)
    kept = _without_a_repeated_time(_kept(answer, bare))
    if not kept:
        return None
    # A step the answer asks for is out, and the step is where the thing is said, so the reply names
    # it once and gives the rest.
    # Said the way they said it: "bicarbonate of soda", not the bare "bicarbonate soda" the
    # reading is filed under.
    verbatim = thing if _names(named, thing) else _bare_phrase(named, bare)
    return _say("Skip the " + verbatim + ": ", _up_to_words(kept))


# What a step that is left says about a step that is gone: "check it again the next day", "leave it
# overnight" - a pronoun with nothing in what is left to hold on to.
HOLDS_ON = re.compile(r"\b(?:it|them|this|that|these|those|the rest)\b", re.I)

# How much of an answer a reply hands on. One sentence of an answer is one thing to do, and a person
# reading two of them has the answer; three is the answer read back to them.
WORDS_IN_A_REPLY = 30

# What an answer says about when to stop and get somebody in: "get a heating engineer out".
WHO_TO_CALL = re.compile(
    r"\b(?:engineer|plumber|electrician|gas safe|corgi|professional|qualified|specialist|expert|"
    r"call (?:someone|somebody|out)|get (?:someone|somebody|an? [a-z]+ )?(?:in|out))\b", re.I)


def _kept(answer, bare):
    """The answer with the steps that name the thing cut out, one entry for each sentence left.

    Whole sentences and not single clauses, because a clause of a repair is not a repair: cutting
    the white wine out of "blot it, don't rub, with kitchen paper, then pour on cold water" and
    stopping at two clauses left "blot it, don't rub", which is half of the first thing to do.
    """
    out = []
    for sentence, clauses in _pieces(answer):
        kept = []
        for clause in clauses:
            for step in re.split(AND_STEP, clause):
                step = step.strip(" .,;:")
                if step and not _names(step, bare):
                    kept.append(step)
        if kept:
            out.append(", ".join(kept))
    return out


# A closing estimate is not a step: "10 minutes, give or take" says how long the whole job takes.
# When the steps that are left already carry a time, handing the estimate on says it twice and
# contradicts it - the egg answer kept "cook them gently for 2 minutes" and then "10 minutes, give
# or take" after it. With no time left in the steps, the estimate is the only one, so it stays.
TIME_TAIL = re.compile(
    r"^\d+(?:\s*(?:-|to)\s*\d+)?\s*(?:minutes?|mins?|hours?|hrs?|seconds?|secs?)"
    r"(?:\s*,?\s*(?:give or take|or so|roughly|about|max|at most))?[.!]?$", re.I)
A_TIME = re.compile(r"\b\d+(?:\s*(?:-|to)\s*\d+)?\s*(?:minutes?|mins?|hours?|hrs?|seconds?|secs?)\b",
                    re.I)


def _without_a_repeated_time(sentences):
    """Drop a closing time estimate when the steps left already say how long something takes."""
    out = []
    for sentence in sentences:
        if out and TIME_TAIL.match(sentence.strip()) and A_TIME.search(" ".join(out)):
            continue
        out.append(sentence)
    return out


def _up_to_words(sentences):
    """The first of them, and as many more as a reply can carry."""
    out, count = [], 0
    for sentence in sentences:
        words = len(words_of(sentence))
        if out and count + words > WORDS_IN_A_REPLY:
            break
        out.append(sentence)
        count += words
    return out


def _holds_on(answer, bare):
    """True when what the answer has left is done to what the missing step makes."""
    kept = _kept(answer, bare)
    return bool(kept) and bool(HOLDS_ON.search(kept[0]))


def _needs_it(thing, answer):
    """The reply when the step that is out is the one the rest of the answer is done to."""
    lead = ("You can't do the first step without the " + thing +
            ", and the rest of that answer is done after it. ")
    for sentence, _clauses in reversed(_pieces(answer)):
        if WHO_TO_CALL.search(sentence) and not _names(sentence, thing):
            return lead + sentence.strip()
    return lead.rstrip()


def _bare_phrase(named, bare):
    """"plunger" from "Start with a plunger", so the step can be named in six words."""
    words = words_of(named)
    for word in words:
        if word in topics.forms(bare):
            return word
    return bare


def _with_a_pet(answer, who):
    """The steps a cat or a child does not rule out, said with the reason they are missing."""
    steps = _steps(answer)
    hazard = [step for step, _ in steps if NOT_WITH_A_PET.search(step)]
    safe = [step for step, _ in steps if not NOT_WITH_A_PET.search(step)]
    if not hazard or not safe:
        return None
    named = NOT_WITH_A_PET.search(hazard[0]).group(0).lower()
    lead = LEADS["pet"].format(who=who) + "skip the " + named + ": "
    return _say(lead, safe)


def _say(lead, steps):
    """The lead and up to two steps, said as one sentence somebody would want to read."""
    said = _tidy(steps[0])
    if len(steps) > 1 and not said.endswith((".", "!", "?")):
        second = _tidy(steps[1])
        # A capital is the answer starting a new sentence, so it goes on as one: read on with a
        # comma it said "rather than flushing again, If the water is rising".
        said += (". " + second) if second[:1].isupper() else (", " + second)
    said = said.rstrip(" ,;:")
    if not said.endswith((".", "!", "?")):
        said += "."
    return lead + said[0].lower() + said[1:] if lead else said[0].upper() + said[1:]


def _tidy(step):
    """"undo the trap underneath (bucket first)" reads as it was said, without the joining word."""
    said = re.sub(r"^(?:and|then|so|but|also)\s+", "", step.strip(), flags=re.I)
    return said.strip()
