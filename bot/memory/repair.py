"""They swapped the thing they were asking about: "no i meant the front room".

A person asks about one thing, gets an answer, and then says the thing they meant was a different
one. It is a repair, and it keeps the ask: the question is the same question about a different
thing. Main reads only the value side of that - `no i said 700`, `sorry, i meant the 13th of june`
- and there the store has a fact to move. When the thing swapped is the *subject* of the ask and
no fact holds it, the line was left to the composer, and the person who corrected themselves got
no answer at all:

```
i need to pick a paint colour for the hall
  -> "Pick the thing you cannot change - the floor, the tiles, the worktop..."
no i meant the front room
  -> "Thanks for telling me - I'm here if you want to dig into any of that."
its quite dark in there
  -> "It's quite dark in there - noted."
```

Two turns lost after a good answer. What they asked for is the same advice about the front room,
and the bot has it: read as the ask they would have said if they had said it right the first time,
it answers.

So this module builds that ask. The thing the last line named is its last content word - the plan
is kept as the sentence it arrived in ("Pick a paint colour for the hall"), so the word that moves
is the one at the end of it - and the new thing takes its place:

    i need to pick a paint colour for the hall  ->  i need to pick a paint colour for the front room

Three rules keep it to the lines it is good at:

* the whole line has to be the repair and a thing: "no i meant the front room", "sorry, i meant
  the other one" is refused because a pronoun names no thing, and "no i meant 500" is refused
  because a value is the store's own correction to make, not a subject to re-ask.
* the thing has to replace something: a word of its own already in the line ("no i meant the
  hall" after the hall) leaves the ask exactly as it was, and answering it again is a repeat.
* the answers have to have something to say about the ask they would have made. When they do not
  ("i live in bristol" / "no i meant leeds" is a fact to change, not an ask to answer) this module
  says nothing and the turn goes back to the rest of the bot, which knows how to move a fact.

The store also keeps the swap, so the turns after it are about the thing they meant: the topic is
the corrected line and the plan says the new thing, or "its quite dark in there" is answered about
the hall they have just taken back.
"""
import re

from ..compose import pick
from . import current, last_user
from . import facts as extract
from .topics import answer_in_hand, keywords

# The repair and the thing after it. The frames are the ones people say a swap in; "i mean" alone
# is left out because "i mean, its fine" opens a remark rather than naming a thing.
REPAIR = re.compile(
    r"^\W*(?:(?:no|nah|nope|sorry|actually|oh|wait|hmm|well|ok|okay|right|yes)[,\s]+)*"
    r"(?:i\s+(?:meant|mean)|i\s+did\s+mean|we\s+meant|meant|rather)\b[,\s:]+"
    r"(?P<thing>\S.*?)\W*$", re.I)

# People also correct the subject without the word "meant": the repair is the bare frame and the
# thing, and the thing is the whole of the line. "no my car keys" after "i lost my keys", "no a
# duck egg" after "how long do i boil an egg", "actually i have chicken" after "what can i cook
# with mince" were all met with the line said back as a receipt ("Got it - no your car keys"),
# because the frame the repair reader looks for is not there.
BARE_REPAIR = re.compile(
    r"^\W*(?:(?P<frame>no|nah|nope|sorry|actually|oh|wait)[,\s]+)+"
    r"(?P<thing>[^.!?]+?)\W*$", re.I)
# The words a bare frame is said with when it takes nothing back: "no thanks", "no worries", "no
# problem", "sorry, my fault". None of them names a thing an answer could be about.
NOT_A_SWAP = frozenset("""
    thanks thank worries worry problem problems idea matter matters clue doubt chance way luck
    bother hurry rush need point sense reason question questions bother drama fault apologies
    apology offence offense harm damage wonder need boat idea lot bit little
""".split())
# The same repair said as what they have instead: "actually i have chicken", "sorry, we've got a
# dog not a cat". The possessor is how the line is built, and the thing is what it names.
# ...and the correction word is what makes it one: "i have a dog" on its own is a fact to keep,
# so the frame is only read when the line opens with the word that takes the last one back.
A_POSSESSION_REPAIR = re.compile(
    r"^\W*(?:(?P<frame>no|nah|nope|sorry|actually|oh|wait)[,\s]+)+"
    r"(?:i|we)(?:'ve|ve|\s+have|\s+have\s+got|\s+got)\s+(?:got\s+)?"
    r"(?P<thing>[^.!?]+?)\W*$", re.I)
# A bare frame is followed by a thing and nothing else: "no the boiler is fine" answers a
# question about the boiler and is not a swap, so a form of a verb in the phrase says the line is
# a clause rather than the thing they meant.
A_VERB_IN_THE_THING = frozenset("""
    is are was were am be been being do does did done doing have has had having
    can could should would will shall may might must
    want wants wanted need needs needed got get gets got make makes made take takes took
    give gives gave go goes went gone like likes liked love loves loved hate hates hated
    feel feels felt hurt hurts hurt think thinks thought know knows knew said says say
    tell tells told see sees saw seen try tries tried use uses used work works worked
    live lives lived play plays played eat eats ate drink drinks drank buy buys bought
    sell sells sold pay pays paid find finds found lose loses lost break breaks broke
    fix fixes fixed start starts started stop stops stopped keep keeps kept put puts
    run runs ran walk walks walked cook cooks cooked clean cleans cleaned
""".split())

# "i meant to call her but forgot" is a thing they did not do, not a thing they meant instead:
# only "meant to say" puts the phrase in front of a thing the way a repair does.
AN_INTENTION = re.compile(r"\b(?:i|we)\s+meant\s+to\s+(?!say\b)", re.I)

# A thing is never a figure or a date: those are values of a fact, and the store has its own
# readers for them ("no i meant 500", "sorry, i meant the 13th of june").
A_VALUE = re.compile(r"\d", re.I)
# Nor is it the word that puts one value against another: "no, thursday not tuesday" and
# "sorry, it's not that bad" correct a day or a figure, and the store moves those itself.
# "rather" is not one of these words: it is a frame of its own above ("rather the front room"),
# and reading it as a contrast here took that repair away.
A_CONTRAST = re.compile(r"\b(?:not|instead|isn'?t|wasn'?t|isnt|wasnt)\b", re.I)

# The words a question is built out of. A thing swapped in is a noun phrase, so it never opens
# with one of these: "no i mean should i quit" after "i hate my job" is the same question asked
# plainer, not a different subject, and reading it as a thing swapped "job" for "should i quit" -
# "i hate my should i quit" - which reached the strict-teacher row on the word "hate" and answered
# a question about quitting a job with a lesson plan. The determiners that begin most things
# ("the front room", "a dog") are not here, so the ordinary swap is untouched.
AN_ASK = frozenset("""
    should shall can could would will may might must do does did is are was were am
    have has had what whats how when where which who why whose
""".split())

# Words that name nothing to answer about on their own: a pronoun or a pointer says "the other
# one of the things we were talking about", which is a choice for another module.
NOT_A_THING = frozenset("""
    it that this these those them one other the a an something anything nothing whatever thing
    things what which same more less first second last next another both all here there
""".split())

# The words a remark opens with. "i mean its fine" and "i mean, whatever" are someone waving a
# subject away, not naming the thing they meant, and a thing never starts with one of them.
A_REMARK = frozenset("""
    i im id ill ive we you he she they it its that there this just only also really very so
    whatever anyway honestly
""".split())

# Words that cannot be the thing the last line named: the grammar words of a line, and the ones a
# question is built out of, so "whats a good way to cook a whole chicken" names the chicken and
# not the "whole" or the "cook".
NOT_THE_THING = frozenset("""
    a an the my our your his her their its some any this that these those it them
    is are was were am be been being do does did done doing have has had having
    can could should would will shall may might must
    and or but so then than too also just very really quite more most less least
    for with without about at in on of to from by into onto over under again
    what whats how when where which who why whose way much many long
    good best great nice better bad worse ok okay please thanks thank
    today tomorrow tonight yesterday now soon later weekend weekends weekday weekdays
    this weekend next weekend last weekend
    one ones thing things stuff lot lots bit little
""".split())


A_DETERMINER = re.compile(
    r"^(?:a|an|the|my|our|your|his|her|their|this|that|these|those)\b", re.I)


def _the_thing(text):
    """The thing the repair names, in the words it was said in, or None."""
    said = " ".join(str(text or "").split())
    if AN_INTENTION.search(said):
        return None
    if A_CONTRAST.search(said):
        # "no, thursday not tuesday" puts one value against another: the store's own correction
        # to make, and a thing to swap is not in the line.
        return None
    match = REPAIR.match(said)
    bare = False
    if not match:
        # The subject corrected without the word "meant": "no my car keys", "actually i have
        # chicken". Both frames are read here so the swap is the same swap, and the refusal
        # rules below hold them to a thing rather than a clause of their own.
        match = A_POSSESSION_REPAIR.match(said)
        if not match:
            match = BARE_REPAIR.match(said)
            if match:
                # Any of these frames is the whole of the line, so what follows has to be a thing
                # and nothing else: the verb guard below is what tells "no my car keys" from "no
                # the boiler is fine".
                bare = True
        if not match:
            return None
    # "sorry i meant to say bristol" is the same repair with a phrase in front of the thing, and
    # the phrase is not what they meant: it is how they said it.
    thing = re.sub(r"^to\s+(?:say\s+|mean\s+)?", "", match.group("thing").strip())
    thing = thing.strip(" ,.!?;:\"'")
    # "no i meant it", "sorry i meant the other one": a pointer is not a thing.
    if not thing or A_VALUE.search(thing):
        return None
    words = [word.strip("'") for word in re.findall(r"[a-z0-9']+", thing.lower())]
    if not words or all(word in NOT_A_THING for word in words):
        return None
    if words[0] in A_REMARK:
        # The frame is followed by a remark, not a thing: "i mean its fine", "i mean whatever".
        return None
    if bare and not A_DETERMINER.match(thing):
        # A thing named without an article or a possessive, right after "no", is what is missing
        # rather than a thing to swap: "my boiler pressure is low" / "no heating" is a person with
        # a cold house, and reading it as a repair answered "Heating, then. Same advice as the low"
        # - advice about the thing they never named. A correction names a thing they have: "no my
        # car keys", "no a duck egg", "no the lower one".
        return None
    if bare and all(word in NOT_A_SWAP for word in words if word not in NOT_THE_THING):
        return None
    if bare and any(word in A_VERB_IN_THE_THING for word in words):
        # "no the boiler is fine" is an answer about the boiler, not the thing they meant.
        return None
    if words[0] in AN_ASK:
        # The frame is followed by an ask, not a thing: the person is putting the question they
        # meant in front of the bot, and the composer answers it as the ask it is.
        return None
    if words[-1] in NOT_A_THING and words[-1] != words[0]:
        # "the one thing" and "that sort of thing" trail off into a word that names nothing; the
        # words in front of it are what the person pointed at, and they are not a thing either.
        return thing if not all(word in NOT_A_THING | NOT_THE_THING for word in words) else None
    return thing


def _a_different_thing(old, thing):
    """Whether the thing they meant is a thing of its own, and not the one already in the ask.

    A word of the old thing inside the new one is a refinement, not a repeat: "i lost my keys"
    then "no my car keys" is the answer about car keys, and "how long do i boil an egg" then "no a
    duck egg" is the egg answer for a duck egg. The line is unchanged only when the new thing says
    nothing the old one did not - "no i meant the hall" after the hall is the same ask, and
    answering it again is a repeat.
    """
    held = _content_words(old)
    said = _content_words(thing)
    if not said:
        return False
    return bool(said - held)


def _content_words(text):
    """The words a thing is named with, determiner and all left out."""
    words = [word.strip("'") for word in re.findall(r"[a-z0-9']+", str(text or "").lower())]
    return {word for word in words
            if word and word not in ("a", "an", "the", "my", "our", "your", "his", "her",
                                     "their", "its", "some", "any", "this", "that")}


# The reading of one line, so the correction reads it once however many candidates it tries: the
# understanding is the expensive half of this path, and a two-hop correction asks it per candidate.
_READINGS = {}


def _the_reading(line):
    """The understanding of the line the correction is about, read once and kept."""
    said = str(line or "")
    if said in _READINGS:
        return _READINGS[said]
    from ..understanding import understand  # noqa: PLC0415 - answers imports this package
    try:
        read = understand(said, {"turns": []})
    except Exception:
        read = {}
    if not isinstance(read, dict):
        read = {}
    if len(_READINGS) > 12:
        _READINGS.clear()
    _READINGS[said] = read
    return read


def _the_thing_the_reading_named(line):
    """The thing the reading finds in the line, or "" when it finds no single one.

    "the washing machine is broken" then "no the dishwasher" is a swap of the machine. The last
    content word of that line is "broken" - the state the thing is in, not the thing - so the
    corrected ask came out as "the washing machine is dishwasher" and the row on how to run a
    wash answered it. The reading names one thing there ("washing machine"), and the swap made on
    that gives "the dishwasher is broken", which is the dishwasher's own row. Only a thing, never
    a person: a correction of a person is `_the_person_the_line_named`'s to move.
    """
    read = _the_reading(line)
    found = []
    for one in read.get("entities") or ():
        if not isinstance(one, dict):
            continue
        if str(one.get("type") or "") not in ("thing", "animal", "food", "place"):
            continue
        text = " ".join(str(one.get("text") or "").lower().split())
        if not text:
            continue
        at = one.get("at")
        at = at if isinstance(at, int) else None
        found.append((at, text))
    if not found:
        return ""
    # The reader splits a two-word thing ("washing", "machine"), so words that sit next to each
    # other are one thing. Two things with a gap between them are two things, and a correction of
    # one of them is not this: "the washing machine is better than the dishwasher" names both.
    found.sort(key=lambda pair: (pair[0] is None, pair[0]))
    one = found[0][1]
    for index, (at, text) in enumerate(found[1:], start=1):
        before = found[index - 1]
        if at is not None and before[0] is not None \
                and at == before[0] + len(before[1].split()):
            one = one + " " + text
        else:
            return ""
    said = " ".join(str(line or "").lower().split())
    return one if one in said else ""


def _the_thing_the_last_line_named(line):
    """The thing the ask before the repair was about: its last content word, or None.

    A plan is kept as the sentence it arrived in, so the thing a line is about is at the end of
    it: "pick a paint colour for the hall" is about the hall, "cook a whole chicken" is about the
    chicken. A line that ends on a grammar word, a figure or a date named no thing this way, and
    the swap is not made.
    """
    words = [word.strip("'") for word in
             re.findall(r"[a-z0-9']+", str(line or "").lower())]
    for word in reversed(words):
        if len(word) < 3 or word in NOT_THE_THING or word in NOT_A_THING:
            continue
        if word in extract.MONTHS or word in extract.DAYS or word.isdigit():
            return None
        if keywords(word):
            # The reader answers with a stem ("keys" is kept as "key"), so asking whether the
            # word is one of its own keywords refused every plural thing: "i lost my keys" named
            # no thing, and "no my car keys" had nothing to swap.
            return word
        return None
    return None


# A refinement points at a part of the thing already named: "my back hurts" / "no the lower one",
# "i want a new bag" / "i meant the big one". The thing in the line is the pointer, so the word that
# moves is the noun it counts, and the swap puts the two together: "my lower back".
A_POINTER = frozenset(("one", "ones"))


def _the_noun_the_line_named(line):
    """The thing a pointer counts: the last noun the ask named, with the verbs passed over.

    "my back hurts" names the back, not the hurting, and the hurting is the word at the end of the
    line. A word that says what the thing is doing is not the thing.
    """
    words = [word.strip("'") for word in
             re.findall(r"[a-z0-9']+", str(line or "").lower())]
    for word in reversed(words):
        if len(word) < 3 or word in NOT_THE_THING or word in NOT_A_THING:
            continue
        if word in A_VERB_IN_THE_THING or word in extract.MONTHS or word in extract.DAYS:
            continue
        if keywords(word):
            return word
        return None
    return None


def _the_pointer_refines(thing, line):
    """What the pointer refines, as the thing to swap in, or None.

    Returns the pair (the word it counts, the thing to put in its place): "the lower one" about
    "my back hurts" is ("back", "lower back").
    """
    words = [word.strip("'") for word in re.findall(r"[a-z0-9']+", str(thing or "").lower())]
    if not words or words[-1] not in A_POINTER:
        return None
    mods = [word for word in words[:-1]
            if len(word) >= 2 and word not in NOT_THE_THING and word not in NOT_A_THING]
    if not mods:
        return None
    noun = _the_noun_the_line_named(line)
    if not noun:
        return None
    return noun, " ".join(mods) + " " + noun


def _the_relation(word):
    """The relation a word names, allowing for the way it is typed: "grans" is "gran".

    "my grans 84" is "my gran's 84" with the apostrophe dropped, which is how most people type
    it, and the word that moves on "sorry i meant my nan" is that gran. Without this the line was
    read as being about a "grans", which is nobody, so the correction had no person to move and
    the age stayed on the gran.
    """
    plain = str(word or "").strip().lower().strip("'")
    if plain in extract.RELATIONS:
        return plain
    if plain.endswith("'s"):
        plain = plain[:-2]
    elif plain.endswith("s"):
        plain = plain[:-1]
    if plain in extract.RELATIONS:
        return plain
    if plain.endswith("'"):
        plain = plain[:-1]
    return plain if plain in extract.RELATIONS else None


def _the_person_the_line_named(line, thing):
    """The person a correction of who is about: "my son has a cough" / "sorry, i meant my daughter".

    A correction of a person often names somebody who would not fit where the last content word
    of the line goes - "my son has a cough" with "my daughter" is not "my son has a my daughter" -
    and the word that moves is the person the line was about. Only a correction that names a
    person of its own is read this way; anything else keeps to the last content word.
    """
    named = {person for person in (_the_relation(word)
                                   for word in re.findall(r"[a-z']+", str(thing or "").lower()))
             if person}
    if not named:
        return None
    for word in re.findall(r"[a-z']+", str(line or "").lower()):
        person = _the_relation(word)
        if person and person not in named:
            return person
    return None


def _swapped(line, old, thing):
    """The ask they would have said if they had said it right the first time."""
    said = " ".join(str(line or "").split())
    new = str(thing or "").strip()
    # A relation is often typed with the possessive on it: "my grans 84" is "my gran's 84", and
    # the word that moves on "sorry i meant my nan" is that one, so the suffix is part of the
    # match. Only for a relation: "chicken" and "chickens" are two things to the store.
    tail = r"(?:'s|s)?" if old in extract.RELATIONS else ""
    match = re.search(r"\b" + re.escape(str(old)) + tail + r"\b", said, re.I)
    if not match:
        return ""
    # The determiner belongs to the sentence, not to the thing: "for the hall" with "the front
    # room" is "for the front room" and not "for the the front room", and "a whole chicken" with
    # "a turkey" is "a whole turkey". Only a thing at the very start of the line brings its own.
    before = said[:match.start()].split()
    if before and re.match(r"^(?:a|an|the|my|our|your|his|her|their|this|that|these|those)\b",
                           new, re.I):
        new = re.sub(r"^(?:a|an|the|my|our|your|his|her|their|this|that|these|those)\s+", "",
                     new, count=1, flags=re.I)
    out = said[:match.start()] + new + said[match.end():]
    out = _no_repeat(" ".join(out.split()))
    return "" if out.lower() == said.lower() else out


def _no_repeat(line):
    """The line without a run of words the swap made twice: "a new new shower" -> "a new shower".

    The new thing brings its own words and the old one had them in front of it, so "i need a new
    boiler" with "a new shower" is "i need a new new shower" unless one run goes. The words before
    the thing are read from the left, so a thing that repeats a word already in the sentence keeps
    the sentence's own word and drops its copy.
    """
    words = line.split()
    out = []
    for word in words:
        if out and word.lower() == out[-1].lower():
            continue
        out.append(word)
    return " ".join(out)


def _the_answer(line, memory):
    """What the answers say about the ask they would have made, or None.

    The readers are given this turn's memory, so the line is read on its own the way the
    corrected ask would have been read on the turn it was first made: a swap is not a follow-up
    to the thing it takes back.
    """
    from ..modules import answers  # noqa: PLC0415 - answers imports this package
    from ..understanding import understand  # noqa: PLC0415

    # The corrected ask is read as the line it is, not as the next turn of the chat: told the
    # whole chicken turns as well, "whats a good way to cook a whole turkey" was widened back to
    # the chicken and the swap was answered with a chicken curry. The facts the person stated are
    # kept, because an answer may depend on them ("no i meant a dog" and their allergy), and the
    # chat's own keys are left behind, because it is not about the thing they took back.
    fresh = {"turns": [], "aside": True, "understood": understand(line, {"turns": []})}
    for key in ("user", "others", "facts_log"):
        if key in memory:
            fresh[key] = memory[key]
    try:
        reply = answers.respond(line, fresh)
    except Exception:
        return None
    if isinstance(reply, str) and reply.strip():
        # What the answers noted down about this ask has to land in the chat's own memory, or the
        # turns after the swap are about the thing they took back: "and how long to rest it"
        # after "sorry i meant a turkey" was answered from the chicken's row, 15 minutes, because
        # the note beside the answer still said chicken.
        for key in ("entry_answer", "entry_answers"):
            if key in fresh:
                memory[key] = fresh[key]
        # The note the answers keep about the last answer is left where it is: it belongs to the
        # turn the chat actually gave, and a copy of it written here sends the never-repeat rule
        # looking for an answer that was never said.
        return reply.strip()
    return None


def _the_plain_answer(text, memory):
    """What the answers say about the line as it stands, read with the chat it is in."""
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    try:
        reply = answers.respond(text, memory)
    except Exception:
        return None
    said = " ".join(str(reply or "").split())
    return said or None


def _about_the_same_thing(first, second):
    """Whether two answers are about the same thing, by the content words they share.

    A correction line is read for an answer of its own, and that answer only counts when it is
    about the thing the person just named: "sorry, i meant my dad" read whole reached the row on
    how to word an apology and never says "dad", so it is an answer to the word "sorry" and not to
    what they meant, while "sorry i meant a turkey" read whole is the turkey. The words are the
    content words of both, stemmed, so "turkeys" and "turkey" are one thing.
    """
    left = {word for word in keywords(str(first or "")) if len(word) > 3}
    right = {word for word in keywords(str(second or "")) if len(word) > 3}
    return bool(left & right)


def _the_shape_the_swap_had(memory, line, old, thing):
    """The corrected line written the way the store has always written it: the word at the end of
    the line swapped for the new thing.

    The reply to a correction is about the thing the line named ("the washing machine is broken" /
    "no the dishwasher" is answered about dishwashers). The record the follow-ups are read against
    is a different matter: everything downstream - the rewritten line a bare "what about a duck"
    is read as, the words a part or a measure ask is filled from - was written against the store's
    own shape, which swaps the last word of the line. Handing that a reshaped sentence changed
    turns that answered before: "how long does a chicken take to roast" / "i meant a turkey" /
    "what about a duck" reached the duck on the old shape and got a search hedge on the new one.
    So the reply keeps the better reading and the bookkeeping keeps the old shape, and no chat
    downstream of a correction moves.
    """
    last = str(last_user(memory) or "")
    tail = _the_thing_the_last_line_named(last) if last else ""
    if tail and _a_state_not_a_thing(last, tail):
        # "the washing machine is broken": the word at the end of the line is the state the thing
        # is in, and the correction swaps the thing, not the state. Swapping it as the store's
        # shape does makes a topic of "the washing machine is dishwasher", and every follow-up
        # after the correction is then read against a sentence that is not a sentence.
        return line
    if tail and tail != old and _a_different_thing(tail, thing):
        older = _swapped(last, tail, thing)
        if older:
            return older
    return line


def _a_state_not_a_thing(line, tail):
    """True when the word the line ends on is what the thing is doing or is, not a thing itself.

    "the boiler is noisy" ends on what it is like, and "i need a new boiler" ends on the thing. The
    copula in front of it is what tells the two apart, and it is the whole of the test on purpose:
    a state word chosen from a list would miss the next one somebody says.
    """
    pattern = (r"\b(?:is|are|was|were|isn'?t|aren'?t|wasn'?t|weren'?t|feels?|seems?|looks?|gets?"
               r"|got|goes|went|has|have|had|keeps?|stays?|stops?)\s+" + re.escape(str(tail)) + r"\b")
    return bool(re.search(pattern, str(line or ""), re.I))


def _keep_the_swap(memory, line, old, thing):
    """The topic and the plan are the corrected line, so the turns after it are about the thing
    they meant rather than the one they took back."""
    line = _the_shape_the_swap_had(memory, line, old, thing)
    record = current(memory)
    if isinstance(record, dict):
        record["text"] = line
        record["words"] = keywords(line)
        record["corrected"] = thing
        topics = memory.get("topics")
        if isinstance(topics, list) and topics and topics[-1] is not record:
            topics[-1] = record
    known = memory.get("user")
    if not isinstance(known, dict):
        return
    for key in ("plan", "plans"):
        held = known.get(key)
        if isinstance(held, str):
            moved = _swapped(held, old, thing)
            if moved:
                known[key] = moved
        elif isinstance(held, list):
            known[key] = [_swapped(str(one), old, thing) or str(one) for one in held]
    for entry in reversed(list(memory.get("facts_log") or [])[:6]):
        if not isinstance(entry, dict) or entry.get("key") not in ("plan", "plans"):
            continue
        value = entry.get("value")
        if isinstance(value, str):
            moved = _swapped(value, old, thing)
            if moved:
                entry["value"] = moved


def _the_paragraph_already_given(answer, memory, old, thing):
    """True when this answer is the one the chat has just read, with the thing's word changed.

    `the washing machine is broken` / `no the dishwasher` gets the dishwasher card, and the store's
    two cards for a machine that stops dead are the same paragraph with the machine's own word in
    it. Read out, it is the same answer twice in two turns, which is what the rest of this module
    spends its time preventing; what the person asked for was the swap, not the paragraph again.
    """
    said = set(re.findall(r"[a-z0-9']+", " ".join(str(answer or "").lower().split())))
    if len(said) < 25:
        return False
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return False
    for turn in reversed(turns[-4:]):
        earlier = str((turn or {}).get("bot") or "")
        if len(earlier.split()) < 20:
            continue
        other = set(re.findall(r"[a-z0-9']+", " ".join(earlier.lower().split())))
        if not other:
            continue
        shared = len(said & other) / float(len(said | other))
        if shared < 0.8:
            continue
        # Only when the paragraph names its own thing on both sides: the machine cards say "most
        # washing machines that will not start" and "most dishwashers...", so the two are one
        # paragraph about two things, and the swap is the whole of what is new. Two cards that
        # name no thing (a dripping tap, a child who will not sleep) are the same advice however
        # they are read, and there the correction is worth saying with the advice behind it.
        if not (keywords(thing) and keywords(old)):
            continue
        if not _names(said, keywords(thing)) or not _names(other, keywords(old)):
            continue
        if _names(said, keywords(old)):
            # The paragraph still names the thing they took back ("a dripping tap" after "no the
            # bathroom one"), so the swap did not change what the answer is about: the advice
            # belongs on the turn.
            continue
        return True
    return False


def _names(words, wanted):
    """True when a set of words of an answer holds one of the words, plural or possessive.

    "the dishwasher" is in a card that says "most dishwashers that will not start", and the swap
    is only worth standing down when the answer itself is about the thing they meant.
    """
    for one in wanted:
        one = str(one or "").lower()
        if not one:
            continue
        for word in words:
            if word == one or word == one + "s" or word.rstrip("s") == one:
                return True
    return False


def _without_the_repeat_lead(answer):
    """The answer itself, without a lead-in that already names the thing they meant."""
    said = REPEAT_LEAD.sub("", " ".join(str(answer or "").split()))
    return said if len(said) >= 40 else answer


def _still_the_old_thing(answer, old, thing):
    """True when the store's own answer is still about the thing they took back.

    Read with the chat, "sorry i meant a turkey" is widened back to the chicken, and the answer
    that comes back is a chicken curry - the thing they just replaced. An answer that opens on the
    thing they meant is not this: "The same goes for the front room: before paint you need ..."
    names the room, and only then talks about the paint both rooms share.
    """
    said = " ".join(str(answer or "").lower().split())
    if not old:
        return False
    words = set(re.findall(r"[a-z']+", said))
    if not any(str(word).lower() in words for word in keywords(old) or ()):
        return False
    opening = set(re.findall(r"[a-z']+", " ".join(said.split()[:12])))
    for word in keywords(thing) or ():
        if str(word).lower() in opening:
            return False
    return True


def _bare(thing):
    """The thing without the word in front of it, for a sentence that has one of its own."""
    words = " ".join(str(thing or "").split()).strip(" .,").split()
    if len(words) > 1 and words[0].lower() in ("a", "an", "the", "my", "our", "your", "his",
                                               "her", "their"):
        return " ".join(words[1:])
    return " ".join(words)


def _said_before(answer, memory):
    """True when this answer is one the chat has already read, word for word.

    The same ask about a thing of the same kind often reaches the same entry: "i need to pick a
    paint colour for the hall" / "no i meant the front room" is the paint advice again, because
    the advice is about paint and not about which room. Read out a second time with a nod in
    front it is not a new answer, and the arbiter passes it over as an echo, which leaves the
    turn to whatever else scored on the line. Said as the same advice for the thing they meant,
    it is the answer, and it keeps the full paragraph for the follow-up that asks for it.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return False
    opening = " ".join(" ".join(answer.lower().split()).split()[:10])
    if not opening:
        return False
    return any(opening in " ".join(str((turn or {}).get("bot") or "").lower().split())
               for turn in turns)


# A figure said back as the one they meant: "sorry i meant 8" after a line worked out for six.
# Digits only, because a number word reaches the store's own readers as a thing ("i meant two" of
# anything), and a figure put right is written as one.
A_FIGURE_REPAIR = re.compile(
    r"^\W*(?:(?:no|nah|nope|sorry|actually|oh|wait|hmm|well|ok|okay|right|yes)[,\s]+)*"
    r"(?:i\s+(?:meant|mean)|i\s+did\s+mean|we\s+meant|meant)\b[\s,:-]+"
    r"(?P<figure>\d+(?:\.\d+)?)\s*(?P<unit>[a-z]{0,10})\W*$", re.I)

# The units a figure is said with. A correction that brings a unit of its own has to bring the one
# the line it corrects used - "sorry i meant 3 days" after "a roast for 6" corrects nothing, and
# the line rebuilt as "a roast for 3 days" would be answered as a question nobody asked.
FIGURE_UNITS = frozenset("""
    kg kilo kilos g gram grams lb lbs oz litre litres liter liters ml pint pints
    pound pounds quid hours hour mins minutes min days day weeks week months month years year
    people person guests adults kids children degrees degree percent
""".split())

A_FIGURE = re.compile(r"\b(?P<figure>\d+(?:\.\d+)?)\s*(?P<unit>[a-z]{0,12})", re.I)

# A count can be written out as a word, and the entry's answer may say it either way: the two
# answers are the same advice when their figures come out, whatever form they are in.
FIGURE_OR_WORD = re.compile(
    r"(?<![\d.])\d+(?:\.\d+)?(?![\d])"
    r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty)\b",
    re.I)

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _the_same_words(one, other):
    """Whether two sentences are the same advice once their figures are taken out of them.

    A figure takes its unit with it when it moves: "a 2kg bird takes roughly 1 hour 40 minutes"
    and "a 3kg bird takes roughly 2 hours 20 minutes" are the same sentence with the arithmetic
    done again, and the singular turning plural is part of the arithmetic, not a new sentence.
    """
    def stemmed(sentence):
        words = FIGURE_OR_WORD.sub("#", str(sentence or "").lower()).split()
        return [word[:-1] if len(word) > 3 and word.endswith("s") else word for word in words]

    return stemmed(one) == stemmed(other)


def _the_figure_in(line):
    """The figure at the end of the line a correction is about, and the unit said with it.

    "im doing a roast for 6" -> the 6, with no unit of its own; "i need 2 kilos of potatoes" ->
    the 2, in kilos. The last figure of the line is the one a person corrects, because it is the
    one they have just said.
    """
    found = None
    for match in A_FIGURE.finditer(str(line or "")):
        unit = (match.group("unit") or "").lower()
        found = (match, unit if unit in FIGURE_UNITS else "")
    return found


def _the_figure_they_meant(text, memory):
    """The answer worked out again for the figure they put right, or "".

    "im doing a roast for 6" is answered with the joint to buy and the time in the oven for six,
    and "sorry i meant 8" was met with "Thanks for telling me - I'm here if you want to dig into
    any of that.": the number the whole answer was worked out from had changed, and nothing was
    worked out again.

    So the line is said again with the new figure in it and read as the ask it is, and what comes
    back is the part of the answer that moved - the joint, the time - rather than the paragraph
    the person has just read. That is only the right turn when the change really is only a
    figure: both answers have to be word for word the same once the figures are taken out of
    them. A correction that reaches a different answer altogether is a different question, and
    the rest of the bot answers it.
    """
    match = A_FIGURE_REPAIR.match(" ".join(str(text or "").split()))
    if not match:
        return ""
    figure = match.group("figure")
    unit = (match.group("unit") or "").lower()
    if unit and unit not in FIGURE_UNITS:
        return ""
    before = " ".join(str(last_user(memory) or "").split())
    if not before:
        return ""
    found = _the_figure_in(before)
    if not found:
        return ""
    held, held_unit = found
    if held.group("figure") == figure:
        return ""  # the same figure said again corrects nothing
    if unit and unit != held_unit:
        return ""
    line = before[:held.start("figure")] + figure + before[held.end("figure"):]
    said = answer_in_hand(memory) or {}
    said = str((said or {}).get("bot") or "") if isinstance(said, dict) else ""
    if not said or not _the_answer_says(said, held.group("figure")):
        return ""  # the answer on the screen was not worked out from that figure
    # The answers' note is written into a scratch copy and only kept when this really is the
    # turn: a rebuilt ask that comes back as a different answer altogether leaves the chat on the
    # answer the person actually read.
    scratch = dict(memory)
    redone = _the_answer(line, scratch)
    if not redone:
        return ""
    changed = _the_figures_that_moved(said, redone)
    if not changed:
        return ""
    _keep_the_corrected_answer(memory, scratch, line)
    return changed


# A figure is spelled either way, and the answer often spells it out: "About 250 g of potatoes
# each, so 1 kg for four" was worked out from the 4 in the line without ever writing a 4.
THE_WORD_FOR = {number: word for word, number in extract.FIGURE_WORDS.items()}


def _the_answer_says(said, figure):
    """Whether the answer on the screen was worked out from this figure, in figures or words."""
    for spelling in (str(figure), THE_WORD_FOR.get(str(figure), "")):
        if not spelling:
            continue
        # A figure written with its unit on it ("2kg") has no word boundary after it, so the
        # lookarounds are for digits rather than for words.
        if re.search(r"(?<![\d.])" + re.escape(spelling) + r"(?![\d])", said, re.I):
            return True
    return False


def _the_figures_that_moved(said, redone):
    """The sentences of the answer worked out again that carry a figure the first one did not.

    Nothing comes back unless every sentence of the two is word for word the same once the
    figures are out of them: then the advice has not changed and only the arithmetic has, so the
    sentences whose arithmetic moved are the whole of what the person needs.
    """
    before = [one for one in SENTENCE_END.split(" ".join(str(said or "").split())) if one]
    after = [one for one in SENTENCE_END.split(" ".join(str(redone or "").split())) if one]
    if not before or len(before) != len(after):
        return ""
    changed = []
    for old, new in zip(before, after):
        if not _the_same_words(old, new):
            return ""
        if old != new:
            changed.append(new)
    if not changed:
        return ""
    said = " ".join(changed).strip()
    return said[:1].upper() + said[1:]


def _keep_the_corrected_answer(memory, scratch, line):
    """The answers' note and the topic are the line with the right figure in it.

    The reply below is part of a long answer, and the turn after it asks for another part of the
    same one: "and how long does that take" after the joint and the time for eight has to reach
    the eight, not the six the entry was first asked about.
    """
    for key in ("entry_answer", "entry_answers"):
        if key in scratch:
            memory[key] = scratch[key]
    record = current(memory)
    if isinstance(record, dict):
        record["text"] = line
        record["words"] = keywords(line)


# Said first, then the answer: the person needs to know the swap landed before the advice that
# follows it answers about a thing they had not named until a second ago.
SWAPPED = (
    "{thing}, then.",
    "Got it \u2014 {thing}.",
    "{thing} it is.",
)

# An ask is not a thing to swap. "no i meant should i see someone" is the question they meant to
# ask, not a subject to put in place of the one the line before named: folded into that line it
# builds "my back hurts should i see someone", and on a complaint about a job, "i hate my should i
# quit", which is neither English nor the ask - it reached the strict-teacher row and answered a
# person who hates their job with advice about a lesson, and the nod in front of it read "Should i
# see someone it is." The thread already holds the subject, so the ask is answered as the question
# it is.
AN_ASK_OPENS = re.compile(
    r"^(?:how|what|why|when|where|which|who|whose|whom)\b"
    r"|^(?:can|could|should|would|will|shall|do|does|did|is|are|was|were|have|has|had|am|may"
    r"|might|must|need)\s+(?:i|we|you|they|it|he|she|that|this|there)\b", re.I)

# A reply that says it cannot answer is not an answer to keep.
HEDGE = re.compile(r"\b(?:beyond what i know|don'?t know enough|a quick search|i'?d rather not "
                   r"guess|not sure about that|i don'?t know that one)\b", re.I)

# An answer long enough to be one, rather than a greeting or a nod.
A_REAL_ANSWER = 80

# An answer that opens by saying it is the same answer for the thing they meant does not need the
# nod in front of it said twice: "Got it - the front room. The same goes for the front room: ..."
# names the room twice in one sentence, and read out at the follow-up it reads as a mistake. What
# is left after the lead-in is the answer itself, which is the shape the rest of this module
# works out.
REPEAT_LEAD = re.compile(
    r"^[^:]{0,90}\b(?:same goes for|same advice (?:as|for|as for)|same as (?:for |the |as )?)\b"
    r"[^:]{0,90}:\s*", re.I)

# ...and when the answer is one the chat has already read, the swap is said with the advice held
# as the same advice, rather than the paragraph twice in one conversation with nothing to say the
# paragraph is the same one. The lead-in is longer than a nod on purpose: it says which thing the
# advice is still for, which is the whole of what the person needs from this turn.
SAME_AGAIN = (
    "{said}, then \u2014 the same advice as for the {old}: {answer}",
    "Got it \u2014 {thing}. The same advice as for the {old} holds: {answer}",
    "{said}, then. Same advice as the {old}: {answer}",
)

# ...and when the answer the correction gives is the paragraph the chat has just read with only the
# thing's word changed, the card is not read out a second time. What the correction changes is which
# thing the advice is about, and the person already has the advice: saying it again puts two copies
# of one paragraph in the chat, and every follow-up after it is read against a doubled answer ("and
# what about the filter" then answers with the first step of the card the person has just been given
# rather than with the filter). So the turn says the swap and that the advice is the same one.
SAME_ADVICE = (
    "{said}, then \u2014 the same advice as for the {old}.",
    "Got it \u2014 {thing}. The same advice as for the {old} applies.",
    "{said}, then. Same advice as the {old}.",
)

# A person named as a slip is the person they meant: "my grans 84" then "sorry i meant my nan" is
# one age said of two words, and the age belongs to the nan. Left under the slip, the chat keeps a
# fact it cannot use and answers "you haven't told me how old your nan is" - the age was there,
# filed under somebody who does not exist. What the person needs to hear is that the fact moved
# with the name, because that is the whole of what the correction was for.
THE_FACT_MOVED = (
    "Got it \u2014 your {new}'s {fact}, not your {old}.",
    "Noted \u2014 your {new} is the one who's {fact}.",
    "Your {new}, then, not your {old} \u2014 your {new}'s {fact}.",
)


_KEEP = True


def _a_fact_of_the_person(entry):
    """The first fact the store holds about somebody, as a person would say it: "84"."""
    age = entry.get("age")
    if age:
        return str(age)
    allergies = entry.get("allergies")
    if allergies:
        return "allergic to " + _a_list_of(allergies)
    return ""


def _a_list_of(things):
    """`nuts` -> "nuts", `nuts` and `dairy` -> "nuts and dairy"."""
    said = [str(one).strip() for one in things if str(one).strip()]
    if not said:
        return ""
    if len(said) == 1:
        return said[0]
    return ", ".join(said[:-1]) + " and " + said[-1]


def _the_fact_moved_to_the_person_they_meant(memory, old, thing, text):
    """The facts filed under the person they took back, moved onto the person they meant.

    A correction of who says the words were wrong and the person is one: there is no gran to keep
    an 84 for. The entry is put back through the store's own merge, so a name on it and a person
    already held under the new word are read the same way as any other fact.
    """
    from . import others, remember_other  # noqa: PLC0415 - the store calls in here

    wanted = extract.a_person_word(_bare(thing))
    if not wanted or wanted == extract.a_person_word(old):
        return ""
    for entry in list(others(memory)):
        if extract.a_person_word(entry.get("who")) != extract.a_person_word(old):
            continue
        fact = _a_fact_of_the_person(entry)
        if not fact:
            return ""
        others(memory).remove(entry)
        moved = {key: value for key, value in entry.items() if key != "who"}
        moved["who"] = wanted
        remember_other(memory, moved, str(text))
        return fact
    return ""


def _the_fact_moved_line(fact, old, thing, text, memory):
    """The reply to a correction of who, when the fact is the only thing worth saying."""
    if not fact:
        return None
    said = pick(THE_FACT_MOVED, memory, str(text)).format(
        new=_bare(thing), old=_bare(old), fact=fact)
    return said if said.endswith((".", "!", "?")) else said + "."


def _the_swap_in_the_line(text, memory):
    """What the line swaps: (the last line, the words that could be the old thing, the new thing).

    None when the line is no correction of a thing, or when there is no earlier line to correct.
    The old thing is tried in order: the person the last line named, then the thing its reading
    names - the thing and not the state it is in ("the washing machine is broken" names the
    machine, not the broken) - then the word at the end of the line, which is what a row keyed on
    the whole sentence was reached by.
    """
    if not isinstance(memory, dict):
        return None
    thing = _the_thing(text)
    if not thing or AN_ASK_OPENS.match(thing) or thing.rstrip().endswith("?"):
        return None
    last = str(last_user(memory) or "")
    if not last:
        return None
    refined = _the_pointer_refines(thing, last)
    if refined:
        # "no the lower one" after "my back hurts" is not a thing of its own: it points at a part
        # of the thing already named, so the ask they would have made is "my lower back hurts".
        old, thing = refined
        return last, [old], thing, refined
    # A correction of a person moves the person, not the last noun of the line: "my son has a
    # cough" with "my daughter" is about a daughter's cough.
    old = _the_person_the_line_named(last, thing)
    olds = [old] if old else []
    for one in (_the_thing_the_reading_named(last), _the_thing_the_last_line_named(last)):
        if one and one not in olds:
            olds.append(one)
    if not olds:
        return None
    return last, olds, thing, None


def keep_the_correction(text, memory):
    """Keep the swap the line made, for a correction another reader answered.

    "how long does a chicken take to roast" then "i meant a turkey" reads right either way - the
    turkey row answers the correction itself - but the chat has still been corrected, and the line
    after it has to be read against the turkey: asked "what about a duck" the chat was still on
    the chicken, so the duck row was never reached and the person got a search hedge. Called by
    the store whatever gave the reply, so the bookkeeping does not depend on which reader won the
    turn.
    """
    found = _the_swap_in_the_line(text, memory)
    if not found:
        return
    last, olds, thing, _refined = found
    for one in olds:
        if not _a_different_thing(one, thing):
            continue
        swapped = _swapped(last, one, thing)
        if swapped:
            _keep_the_swap(memory, swapped, one, thing)
            return


def the_thing_they_meant(text, memory):
    """The answer about the thing they said they meant, or None.

    Called when the rest of the store has nothing to say about the line, so a value correction
    and a fact to move have already had their turn.
    """
    if not isinstance(memory, dict):
        return None
    figure = _the_figure_they_meant(text, memory)
    if figure:
        # "sorry i meant 8" is the store's own correction to make, and when it holds no fact with
        # the old figure in it, the answer on the screen was worked out from it: that answer is
        # worked out again, and only the part that moved is said.
        return figure
    thing = _the_thing(text)
    if not thing:
        return None
    if AN_ASK_OPENS.match(thing) or thing.rstrip().endswith("?"):
        # The correction is the ask itself, not a thing to swap: answer it against the thread.
        answer = _the_answer(thing, memory)
        if not answer:
            return None
        answer = _without_the_repeat_lead(answer)
        if _said_before(answer, memory):
            # The chat has already read this answer, so saying it again wants the frame below that
            # says it is the same advice - and there is no thing here to put that frame round.
            return None
        return answer if answer.endswith((".", "!", "?")) else answer + "."
    last, olds, thing, refined = _the_swap_in_the_line(text, memory)
    held = olds[0]
    # The fact the last line stated belongs to the person they meant. This is a correction of who
    # and not of what, so it is right whether or not there is an answer for the corrected ask:
    # the reply says the fact moved only when there is no answer of its own to give.
    fact = _the_fact_moved_to_the_person_they_meant(memory, held, thing, text)
    answer, line, old = "", "", ""
    for one in olds:
        if not _a_different_thing(one, thing):
            continue
        swapped = _swapped(last, one, thing)
        if not swapped:
            continue
        found = _the_answer(swapped, memory)
        if found:
            answer, line, old = found, swapped, one
            break
    if not answer:
            return _the_fact_moved_line(fact, held, thing, text, memory)
    answer = _without_the_repeat_lead(answer)
    plain = _the_plain_answer(text, memory)
    if plain and not (_about_the_same_thing(plain, thing)
                      or _about_the_same_thing(plain, answer)):
        # An answer to a correction is about the thing they just named. When the reading of the
        # line whole never mentions it, the entry matched a word of the frame instead: "sorry, i
        # meant my dad" after a visit to their mum reached the row on how to word an apology,
        # because "sorry" is in its ask words and "dad" in its second part, and the correction was
        # answered with advice about saying sorry to him. The corrected ask is the answer then,
        # given the way any swap is.
        plain = None
    if plain and _without_the_repeat_lead(plain) == answer:
        # The store's own reading of the line already gives the answer to the corrected ask, so
        # there is nothing to repair: "sorry i meant a turkey" names the turkey and the turkey row
        # answers it. Framing that answer with a nod only puts a second acknowledgement in front
        # of it, and the arbiter drops the pair as an echo anyway.
        #
        # The swap is kept even so. The turn reads right, and the line after it does not: asked
        # "what about a duck" the chat was still on the chicken, so the duck row was never reached
        # and the person got a search hedge. The correction happened whatever the reply to it is.
        _keep_the_swap(memory, line, old, thing)
        return None
    if plain and len(plain) > A_REAL_ANSWER and not HEDGE.search(plain) \
            and not _still_the_old_thing(plain, old, thing):
        # The line read as it stands has an answer of its own, in its own words - the paint chat's
        # "no i meant the front room" carries the paint question, so the supplies list is the
        # answer for the room they meant. It is given as it stands rather than behind a nod, which
        # would name the room a second time in one sentence.
        if _said_before(plain, memory):
            # ...unless the chat has already read it: then the correction changes nothing the
            # person can see, and the store's plain acknowledgement is the better turn.
            return None
        _keep_the_swap(memory, line, old, thing)
        return plain if plain.endswith((".", "!", "?")) else plain + "."
    if plain == answer:
        # The store's own reading of the line already answers the thing they meant: "sorry i meant
        # a turkey" names the turkey, so the turkey row reaches it without any help. Nothing is
        # wrong with that answer, and a nod in front of it is not worth the turn the bookkeeping
        # behind it costs. The bookkeeping itself is still owed: the chat has been corrected, and
        # the next line ("what about a duck") has to be read against the thing they meant rather
        # than the one they took back.
        _keep_the_swap(memory, line, old, thing)
        return None
    _keep_the_swap(memory, line, old, thing)
    if refined and not _said_before(answer, memory):
        # They narrowed the thing already on the table rather than swapping it for another one
        # ("i want a coat" / "no i meant a waterproof one"), so the advice is for the very thing
        # they have just named and answers as it stands. A nod in front of it only names it twice
        # in two sentences: "Got it - Waterproof coat. For rain, a waterproof shell...".
        return answer if answer.endswith((".", "!", "?")) else answer + "."
    shown = thing[:1].upper() + thing[1:]
    if _the_paragraph_already_given(answer, memory, old, thing):
        # The pools put the thing after a determiner of their own, so a determiner the person said
        # comes off the copy that follows one, and stays on the copy that opens the sentence.
        held = _bare(thing)
        if shown.split()[0].lower() in ("the", "a", "an", "my", "our", "your", "his", "her"):
            held = shown[:1].lower() + shown[1:]
        said = pick(SAME_ADVICE, memory, str(text)).format(
            said=shown, thing=held, old=_bare(old))
        return said if said.endswith((".", "!", "?")) else said + "."
    if _said_before(answer, memory):
        # The pools put the thing after a determiner of their own, so a determiner the person
        # said is taken off first: "the front room", not "the the front room".
        held = _bare(thing)
        if shown.split()[0].lower() in ("the", "a", "an", "my", "our", "your", "his", "her"):
            held = shown[:1].lower() + shown[1:]
        said = pick(SAME_AGAIN, memory, str(text)).format(
            said=shown, thing=held, old=_bare(old), answer=answer[:1].lower() + answer[1:])
        return said if said.endswith((".", "!", "?")) else said + "."
    shape = pick(SWAPPED, memory, str(text))
    if not shape.startswith("{thing}"):
        # The thing is said inside a sentence, so the determiner in front of it is not the
        # capital a name takes there: "Got it - the front room." and not "Got it - The front room."
        if shown.split()[0].lower() in ("the", "a", "an", "my", "our", "your", "his", "her"):
            shown = shown[:1].lower() + shown[1:]
    said = shape.format(thing=shown)
    return (said + " " + answer).strip()
