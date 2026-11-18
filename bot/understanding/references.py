"""What "it", "that", "they" and "there" point at, and whether this line follows the last one.

People answer in fragments and lean on the last turn: "How long will it take?", "And if I
stuff it?", "Anything cheaper there?". This module reads the previous user line and says what
a pronoun most likely means, so a module can answer about the right thing.

`resolve()` never guesses when there is nothing to point at: on the first turn every referent
is None and `followup` is False.
"""
import re
import string

from . import topics

PRONOUNS = {
    "it": ("it", "its", "itself"),
    "that": ("that", "this", "these", "those", "one", "ones"),
    "they": ("they", "them", "their", "theirs"),
    "there": ("there",),
    "he": ("he", "him", "his", "himself"),
    "she": ("she", "her", "hers", "herself"),
}
FOLLOWUP_STARTS = (
    "and", "also", "but", "so", "what about", "how about", "what if", "and what", "then",
    "why", "how long", "how much", "how many", "how often", "when", "where", "which",
    "same", "another", "more", "else", "other", "instead", "so that", "ok and", "ok so",
    "even if", "does it", "is it", "can it", "will it", "does that", "is that", "can that",
    "will that", "would it", "should it", "what else", "anything else", "and then",
)
# A pronoun after a preposition is what the sentence acts on, not its subject: "my husband
# spilt red wine on it" is still about the sofa, and the husband is only who did it.
POINTING_BACK = frozenset("""on in at with to for from by under over near into onto around
    inside outside about off through across behind beside""".split())
# The first word of a clause that tests a proposal - "will that work", "does that help" - as
# opposed to judging what was just said, which is "is that normal". Only the first leans on the
# last turn; the second is about the thing its own clause named.
ASK_OPENERS = frozenset("""will would shall should can could do does did may might must""".split())
WHERE_WORDS = frozenset("there where place city area town country".split())
# A word that starts a clause of its own: "to be honest it hurts" says what the last turn's
# plan is not, and the purpose clause is over by then.
CLAUSE_SUBJECTS = frozenset("""i you we they he she it there its im ive dont cant thats""".split())
TIME_RE = re.compile(r"^(and|also|but|so)\b")


def _target(prev_line, prev_entities, prev_topic):
    """The thing the last user line was about: its short phrase, and what kind of thing it is.

    A pronoun stands for what the line was *about*, not for the last noun in it: after "I'm
    baking a birthday cake for my son", "it" is the cake, not the son. So things come first,
    anchored on the first thing the line names, with the thing words next to it joined,
    because "birthday cake" and "beef stew" are one thing. When the line names nothing, the
    last resort is the topic it was read as, and `kind` says so: a topic label ("school and
    study") is not a thing a sentence can be about, so a caller that needs a noun can tell the
    two apart.
    """
    things = [entity for entity in prev_entities if entity["type"] == "thing"]
    if things:
        words, at = [things[0]["text"]], things[0]["at"]
        for later in things[1:]:
            if later["at"] == at + 1:
                words.append(later["text"])
                at = later["at"]
        return " ".join(words).lower(), "thing"
    for kind in ("title", "name", "place", "person"):
        for entity in prev_entities:
            if entity["type"] == kind:
                return entity["text"].lower(), kind
    if prev_topic:
        return prev_topic.replace("-", " "), "topic"
    return None, None


def _person(prev_entities, fallback):
    """The person the last line was about, for he/she: a proper name first, then the
    relation ("my daughter"), so "her" points at Mia rather than at the phrase."""
    for kind in ("name", "title", "person"):
        for entity in prev_entities:
            if entity["type"] == kind:
                return entity["text"].lower()
    return fallback


def _place(prev_entities, prev_topic):
    for entity in prev_entities:
        if entity["type"] == "place":
            return entity["text"].lower()
    return prev_topic.replace("-", " ") if prev_topic == "geography-and-travel" else None


# Entities that can be the thing a line is about, in the order they are worth trying.
OWN_THINGS = ("title", "name", "person", "place", "thing")
# A person named in a line is a new subject even when the line stays on the same topic: "my
# son keeps picking on his brother and it's doing my head in" is about the son, not about the
# homework of a turn earlier.
OWN_PERSONS = ("title", "name", "person")


def _moved(read, prev_topic):
    """True when this line has left the topic the last turn was about."""
    topic = read.get("topic")
    if not topic or not prev_topic:
        return False
    return topic != prev_topic


def _has_moved(line, prev_topic):
    """True when the line's own topic is not the last turn's.

    `resolve()` is called with the line's first reading (`kinds.classify`), which has no
    `topic` in it, so `_moved(read, prev_topic)` is always False on that path and a thing the
    line names in front of its pronoun never takes the pronoun back: after "my cat keeps
    scratching the sofa", "im 3 weeks into a new job and hate it already" read as a follow-up
    about the sofa and answered with the return-goods card. Reading the line's own topic here
    (nothing inherited) is what says whether it has left the last turn behind, so `a new job`,
    `a bike` and `my shed door` can be the subject of their own `it`.
    """
    if not prev_topic:
        return False
    own, _ = topics.detect_topic(line, None, topics.detect_entities(line))
    return bool(own) and own != prev_topic


# The word in front of a noun that makes it a noun phrase of its own: "a bike", "my shed door".
# A bare noun is usually a material or a tool ("will vinegar fix it", "will lime turn it pink"),
# so it names no subject: only a determiner starts a thing the line is about.
DETERMINERS = frozenset("""a an the this these those that my your his her its our their
    some any each every another""".split())
# A coordinator is what joins a second clause to the thing's own: "i bought a bike and i love
# it", "my tap is dripping and its driving me mad". Without one the pronoun is part of the same
# clause the thing is an argument of: "is cleaning the filter worth it" is still the machine.
COORDINATORS = frozenset("and but so then".split())
# A possessive pronoun makes the thing its own subject even in the same clause: "my car failed
# its mot" is about the car, not about whatever was on the table a turn earlier.
POSSESSIVE_PRONOUNS = frozenset("its their".split())
# Every form of every pronoun: a noun phrase is over when one starts.
PRONOUN_WORDS = frozenset(word for forms in PRONOUNS.values() for word in forms)
# Grammar words that end a noun phrase before it reaches a determiner: "is sticking and it"
# has no noun phrase in it, while "a new job and it" does.
CLAUSE_STOPS = frozenset("""is was are were be been am do does did have has had will would can
    could should to of in on at for from with by if when because so that which who""".split())


def _a_thing_of_its_own(norm, at, word):
    """True when a noun phrase the line opens itself is what the pronoun's clause is about.

    "a bike", "my shed door" and "a new job" start a thing; a bare noun is an argument of
    the sentence ("will vinegar fix it", "will lime turn it pink"), so it starts nothing. The
    phrase also has to be joined to the pronoun's clause by a coordinator ("bought a bike and
    i love it") or be the thing whose own part a possessive names ("my car failed its mot").
    """
    opened = _last_noun_phrase(norm, at)
    if opened is None:
        return False
    if word in POSSESSIVE_PRONOUNS:
        return True  # "i started a course and its a lot of work"
    return any(other in COORDINATORS for other in norm[opened:at])


def _last_noun_phrase(norm, at):
    """Where the last determiner in the words before `at` opens a noun phrase, or None."""
    for index in range(at - 2, max(-1, at - 12), -1):
        word = norm[index]
        if word in DETERMINERS and index + 1 < at:
            return index
        if word in PRONOUN_WORDS:
            return None  # a pronoun starts its own clause: what came before is not this one
    return None


def _named_before(line, names, moved=True):
    """The pronouns of `names` that come after a thing the line names itself.

    "my mum keeps asking when we're having kids and it's doing my head in" names the mum and the
    kids before its "it", so that "it" is about the mum's nagging, not the chicken cooked a turn
    earlier. In "how do i stop it chewing the furniture?" the "it" comes first, so it still
    points back at the puppy.

    `moved` says whether the line has left the topic of the last turn. A thing named in the
    same conversation is usually an argument of the sentence rather than a new subject -
    "will vinegar fix it" and "50 pounds to spend on it" name a tool and a price, and their
    "it" is still the pan and the thing being bought. A person named in front of the pronoun
    takes it away on its own; a thing has to be a noun phrase of its own ("a new job", "my
    shed door") in a clause joined to the pronoun's ("and i hate it"), or be the thing whose
    own part the possessive pronoun names ("my car failed its mot").
    """
    norm = line["norm"]
    people = [entity.get("at", 0) for entity in topics.detect_entities(line)
              if entity.get("type") in OWN_PERSONS]
    found = []
    for name in names:
        at = next((i for i, word in enumerate(norm) if word in PRONOUNS[name]), None)
        if at is None:
            continue
        if at and norm[at - 1] in POINTING_BACK:
            continue  # "spilt red wine on it": the pronoun is what the person acted on
        if _asks_about(line, (name,)):
            continue  # "will that work": the clause asks about the last turn's thing
        named = any(spot < at for spot in people)
        if not named and moved:
            named = _a_thing_of_its_own(norm, at, norm[at])
        if not named:
            continue
        found.append(name)
    return found


def _asks_about(line, names):
    """True when the clause that holds one of `names` is a question: "will that work".

    A clause that asks is leaning on the last turn whatever it names: "my neighbour uses
    vinegar, will that work" asks whether the vinegar works *for the ants*, so the answer is
    still the ants.
    """
    aliases = set()
    for name in names:
        aliases.update(PRONOUNS[name])
    for clause in line.get("clauses") or ():
        if clause and clause[0] in ASK_OPENERS and aliases & set(clause[:3]):
            return True
    return False


# The pronouns that stand for one person the line is about. "it", "they" and "them" are left
# out: those are just as often the thing on the table ("the muffins are in the oven" / "should
# i take them out"), and a thing in hand is exactly what a follow-up leans on.
ONE_PERSON = ("he", "him", "his", "she", "her", "hers")


def person_is_new(line, prev_entities):
    """True when the line is about a person no line in the chat has introduced yet.

    "should i text him back" is a question about a person, and after an answer about a knee
    there is no him anywhere in the chat: nobody has been named, so the person is new. Read as
    a follow-up ("should i text him back" with "my knee clicks when i climb stairs" in front of
    it) the knee entry answers it again and the person gets their own question back. The same
    line after "my landlord wont fix the boiler" is about the landlord the last line named, so
    it is a follow-up and keeps leaning.

    Kept as a plain question about the words and the last line's people, so a caller can use it
    as a fence: a line that brings somebody new is a line of its own.
    """
    people_here = bool(topics.person_names(line)) or any(
        entity.get("type") == "person" for entity in topics.detect_entities(line))
    if not people_here and not set(line.get("norm") or ()) & set(ONE_PERSON):
        return False
    return not any(entity.get("type") == "person" for entity in prev_entities or ())


def _only_the_purpose(line):
    """True for a line that is only a purpose clause: "to cycle to work".

    Nobody opens a conversation with "to cycle to work". It is the rest of the last turn's plan
    ("i want to get fit"), so the line goes on with what was being talked about - and read as a
    greeting it was answered as if the person had just said hello ("Got it - to cycle to work").
    The infinitive is the whole line: a clause with its own subject after it ("to be honest it
    hurts") is the speaker's own sentence, and only what "it" is comes from the last turn.
    """
    norm = line["norm"]
    if len(norm) < 2 or norm[0] != "to":
        return False
    return not (set(norm[1:]) & CLAUSE_SUBJECTS)


# "is it ok to run every day" is not about the thing the last turn was on. That "it" is a
# placeholder the frame brings along and the line names its own subject after it - the activity
# itself, "to run", "to feel tired all the time" - so a question about running was answered with
# the night waking it followed, word for word.
#
# What tells a placeholder from a pronoun that does point back is whether the clause after it
# names a thing of its own. "is it safe to drink the tap water" says "the tap water", so the line
# has its own thing and the place the last turn named is what makes the answer land ("Tap water
# in Rome is safe to drink"); "is it worth getting a new one" says "one", so it is still the
# boiler. Only a clause that names nothing - an activity and a frequency, "to run every day" -
# is the frame's own placeholder.
PLACEHOLDER_IT = re.compile(
    r"^(?:is|was|would|will|does|did|can|could|should)(?:n'?t)?\s+it\s+"
    r"(?:[a-z']+\s+){0,3}?to\s+[a-z]+")
# A thing of the line's own: an article or a possessive and the word it belongs to. "a pint" and
# "the sea" count, because a line that picks out a thing is about that thing and not about the
# last turn.
NAMES_A_THING = re.compile(
    r"\b(?:a|an|the|some|any|my|your|our|their|his|her|its|another)\s+[a-z]", re.I)
# A word that stands for something said earlier. A clause carrying one is leaning on the last
# turn even when it names nothing with an article: "is it ok to use it in the rain".
STANDS_FOR_SOMETHING = frozenset("""it its them they that this these those him her one ones
    there""".split())
# A clause that stops on a joining word has left something out: "is it ok to go to bed straight
# after" is straight after the eating the last turn was about, so it leans on it even though it
# names nothing with an article. "to run every day" stops on its own time, not on a link.
LEAVES_SOMETHING_OUT = frozenset("""after before then while during since until till instead
    without with on in at for to from about when if and but or that""".split())


def _a_placeholder_it(line):
    """True for "is it <test> to <verb> ..." where the clause names nothing of its own.

    The whole line is the test, so a caller can use it as a fence: a line that brings a
    placeholder is a line of its own and the last turn's thing is not what it is about.
    """
    said = " ".join(line["norm"])
    frame = PLACEHOLDER_IT.match(said)
    if not frame:
        return False
    rest = said[frame.end():]
    if NAMES_A_THING.search(rest):
        return False
    if set(rest.split()) & STANDS_FOR_SOMETHING:
        return False
    tail = rest.split()[-1:]
    return not (tail and tail[0] in LEAVES_SOMETHING_OUT)


# The animal a line only points at. A person who has just said "my cat milly is 12" does not say
# the word again: "she's been drinking a lot more water", "how much should i feed her", "hes
# getting slow on walks". The entries that answer a line like that are keyed on the animal, so
# nothing keyed on a cat or a dog matched, and the answer for a person's own body took the turn -
# the daily figure for drinking water went to a cat. `resolve()` has already said what the pronoun
# means, so the animal it names can be read into the line: the knowledge lookup puts the word
# where the pronoun stands, the way breeds.py puts the animal's own word beside a breed's, and a
# pet answer says the animal back.
ANIMALS_IN_HAND = re.compile(
    r"\b(dogs?|pupp(?:y|ies)|cats?|kittens?|rabbits?|bunn(?:y|ies)|hamsters?|guinea\s+pigs?"
    r"|parrots?|budgies?|goldfish|fish|tortoises?|turtles?|snakes?|lizards?|geckos?|horses?"
    r"|pon(?:y|ies))\b", re.I)
# A line that makes the speaker its subject is about the speaker: "my cat's fine but i've got a
# headache" keeps every word it typed. "my hands" is not a subject - it is what the animal is
# biting - so only the pronouns that carry a subject are here.
OWN_SUBJECT = frozenset("""i im ive id ill we weve wed""".split())
# The same pronouns with the apostrophe gone, which is how they are typed: "hes getting slow on
# walks" is one word to the reader.
WITHOUT_THE_APOSTROPHE = {"he": ("hes", "hed", "hisself"), "she": ("shes", "shed"),
                          "they": ("theyre", "theyd", "theyll")}
# An animal word is enough to tell the animal apart: "cat", "dog", "kitten". A line that names one
# already has the word this would add.
ANIMAL_NAMES = frozenset("""dog dogs puppy puppies cat cats kitten kittens""".split())


def _the_breed_in(text):
    """The animal a breed word in the line names, or "" when the line names none.

    "we got a rescue greyhound on saturday" and then "she wont eat in the day" is a question
    about the dog: the breed is the only animal word in the thread, and the pronouns a person
    uses for a dog are the same ones they use for a cat. The table of breeds and the frames that
    make one an animal (not a bus, not a race) is `breeds.py`'s, so this asks it rather than
    keeping a second list of dog names here.
    """
    from .breeds import BREED_KIND, the_animal_a_breed_is
    # What the pronoun was resolved to is often the animal's name and nothing else
    # ("greyhound", "maine coon"), which is no longer a line to read a frame in: the frame was
    # read the turn before.
    whole = str(text or "").strip().lower()
    if BREED_KIND.get(whole):
        return BREED_KIND[whole]
    said = re.findall(r"[a-z']+", str(text or "").lower())
    if not said:
        return ""
    filled = the_animal_a_breed_is(list(said))
    if not isinstance(filled, list) or len(filled) <= len(said):
        return ""
    index = 0
    for piece in filled:
        if index < len(said) and piece == said[index]:
            index += 1
            continue
        return str(piece).lower()
    return ""


def _the_pronouns(name):
    return frozenset(PRONOUNS[name]) | frozenset(WITHOUT_THE_APOSTROPHE.get(name, ()))


# An animal word said two lines back is still what a pronoun in this line points at, as long as
# the line names no animal of its own: "we are getting a rescue greyhound" / "she wont eat in the
# day" / "and whats the best way to walk her". The third line's own words say nothing about a dog,
# so the only place the animal can come from is the chat.
THIRD_PERSON = frozenset(word for name in PRONOUNS for word in PRONOUNS[name])
# "and my back hurts" points at the speaker's own body, not at the animal: a line that says whose
# thing it is with "my" or "our" is about that thing, whatever else the line carries.
MINE = frozenset("""my mine our ours""".split())


def the_animal_the_chat_is_on(words, last_read):
    """The animal the line before had in hand, when this line only points at it.

    A pronoun in this line has to point at something, and a line that names no animal of its own
    is pointing at the one the chat has been about. A line that makes the speaker its subject
    ("i've got a headache too") or that names another animal keeps what it says.
    """
    if not isinstance(last_read, dict):
        return ""
    animal = str(last_read.get("animal_in_hand") or "").lower()
    if not animal:
        return ""
    bare = set()
    for word in words or ():
        bare.add(str(word).lower().strip(string.punctuation + "\u2019").split("'")[0])
    if bare & ANIMAL_NAMES or bare & MINE:
        return ""
    if not bare & THIRD_PERSON:
        return ""
    return animal


def the_animal_in_hand(ref, words):
    """The animal a follow-up only points at, or "" when the line is about something else.

    Only for a line whose subject is the pronoun: a line that says nothing of its own about which
    animal ("she's been drinking a lot more water") cannot be answered by any entry keyed on a cat
    or a dog. A line with a subject of its own keeps it, and so does one that already names an
    animal.
    """
    if not isinstance(ref, dict) or not ref.get("followup"):
        return ""
    bare = set()
    for word in words or ():
        bare.add(str(word).lower().strip(string.punctuation + "\u2019").split("'")[0])
    if bare & OWN_SUBJECT or bare & ANIMAL_NAMES:
        return ""
    for name in PRONOUNS:
        if not bare & _the_pronouns(name):
            continue
        said = str(ref.get(name) or "")
        animal = ANIMALS_IN_HAND.search(said)
        if animal:
            return animal.group(0).lower()
        breed = _the_breed_in(said)
        if breed:
            return breed
    return ""


def resolve(line, read, prev_line=None, prev_entities=None, prev_topic=None):
    """{"it", "that", "they", "there", "followup"} for the current line."""
    prev_entities = prev_entities or []
    words = set(line["norm"])
    used = {name: next((p for p in aliases if p in words), None)
            for name, aliases in PRONOUNS.items()}
    ref = {"it": None, "that": None, "they": None, "there": None, "he": None, "she": None,
           "kind": None, "followup": False}
    if prev_line is None:
        return ref

    target, kind = _target(prev_line, prev_entities, prev_topic)
    person = _person(prev_entities, target)
    reference = bool(used["it"] or used["that"] or used["they"] or used["there"]
                     or used["he"] or used["she"])
    placeholder = _a_placeholder_it(line)
    starts = " ".join(line["norm"][:4])
    opens_like_followup = any(starts == phrase or starts.startswith(phrase + " ")
                              for phrase in FOLLOWUP_STARTS) or _only_the_purpose(line)
    if placeholder and not (used["that"] or used["they"] or used["there"]
                            or used["he"] or used["she"]):
        # the "is it" opener is this frame's, not a lean on the last turn
        opens_like_followup = False
        asks_without_topic = False
    short = len(line["norm"]) <= 3 and read["kind"] not in ("greeting", "thanks")
    adds_topic = topics.subject_topic(line, topics.detect_entities(line)) is not None
    asks_without_topic = read["kind"] == "question" and not adds_topic

    ref["kind"] = kind
    if reference and placeholder and not (used["that"] or used["they"] or used["there"]
                                          or used["he"] or used["she"]):
        # the only pronoun in the line is the one the frame brought, so nothing points back
        reference = False
    if reference:
        ref["it"] = target
        ref["that"] = target
        ref["they"] = target
        ref["he"] = person
        ref["she"] = person
    ref["there"] = _place(prev_entities, prev_topic)
    ref["followup"] = bool(reference or opens_like_followup or short or asks_without_topic)
    named_first = _named_before(line, ("it", "that", "they", "there"),
                                moved=_moved(read, prev_topic) or _has_moved(line, prev_topic))
    for name in named_first:
        # the line named a thing of its own first, so this pronoun is about that thing
        ref[name] = None
        if name in ("they", "that"):
            ref["he"] = ref["she"] = None
    pointed_back = [name for name in ("it", "that", "they", "there") if used[name]]
    if pointed_back and set(pointed_back) == set(named_first) and not (used["he"] or used["she"]):
        # every pronoun in the line is about its own new subject, so nothing here leans on the
        # last turn: "my mum keeps asking about kids and it's doing my head in" is not a follow-up
        ref["followup"] = bool(opens_like_followup or short or asks_without_topic)
    return ref
