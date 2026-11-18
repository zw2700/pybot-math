"""The person a line is about, when the chat already knows one: who, and how old they are.

The store keeps facts about other people in `memory["others"]` (`bot/memory/__init__.py`), one
record per person: `{"who": "son", "age": 4}` from `my son is 4`. An answer that needs something
about that person - a present for their birthday, how long they should sleep - can only use it
if it can say *which* of the people in the store the line means. That is all this module does:

    my son is 4 / what should i get him for his birthday
    -> {"who": "son", "age": 4}, so the present is a four-year-old's and not a grown-up's

A line that names the relation ("my daughter", "my mum") is the sure case. A line that says only
`him` or `her` is read by the gender of the relation the store holds, and only when the store
holds exactly one person of it: two sons and a `him` is nobody in particular, and a guess about
whose age it is is worse than saying nothing. Everyone else returns None, so a module that asks
falls back to the answer it had before.
"""
import re

# Chapter and verse of nothing: these are the relations a `him` or a `her` can point at, by the
# word for them the store keys a person by. Only words that say the sex of the person are here -
# "child", "kid", "cousin", "partner", "friend" and "baby" are all either one, so a pronoun says
# nothing about which of them it is.
# A grandchild and a godchild are the relations a present is most often bought for, and a "him"
# after "my grandson is 3" pointed at nobody at all while the store held his age, so the line was
# answered with the list written for a grown-up: `what should i get him` -> the card about buying
# for someone you do not know well.
HIM = frozenset("""son dad father daddy papa husband brother nephew grandad grandpa granddad
grandfather stepdad stepson uncle boyfriend fiance grandson godson""".split())
HER = frozenset("""daughter mum mom mam mummy mumma mother wife sister niece nan nana gran
granny grandma grandmother stepmum stepdaughter aunt auntie girlfriend fiancee granddaughter
goddaughter""".split())

# The words a line uses for the person it is about without naming the relation, most direct
# first: "what should i get him", "buy her something", "he needs a new one".
HIM_SAID = re.compile(r"\b(?:him|his|he)\b", re.I)
HER_SAID = re.compile(r"\b(?:her|hers|she)\b", re.I)
# A line about more than one person at once, said back as "them": "theyre 4 in august" puts
# an age in the store under `their_age`, and "what should i get them" points at it. A "them"
# also says a person without saying which, which is how a line about somebody just mentioned
# is written: "my nephew is 5 in june" then "what can i get them". It points at the one person
# the store holds an age for, and at nobody at all when there are two of different ages,
# because a present for the wrong age is worse than the answer written for nobody.
THEM_SAID = re.compile(r"\b(?:them|they|theirs|their)\b", re.I)


def _the_age_of_the_group(memory):
    """The age the chat holds for the people a "them" points back at, or None.

    "theyre 4 in august" is filed as `memory["their_age"] = {"age": 4, "turns": "in august"}` -
    the same shape a person's age is kept in, with no relation to key it by, because the line
    named no relation. A question about "them" later in the chat is about those people, so
    their age is read here the way a relation's is read from `memory["others"]`.
    """
    theirs = memory.get("their_age") if isinstance(memory, dict) else None
    if isinstance(theirs, dict):
        age = theirs.get("age")
        if isinstance(age, int) and 0 < age < 120:
            return age
    return None


def _with_an_age(record):
    """True for a person the store knows the age of, whether it was said as one number or a list."""
    if not isinstance(record, dict):
        return False
    if isinstance(record.get("age"), int) and record.get("age") > 0:
        return True
    return any(isinstance(age, int) and age > 0 for age in record.get("ages") or ())


def _age(record):
    """The age the store holds for a person: the one number, or the first of a list."""
    if isinstance(record.get("age"), int):
        return record["age"]
    for age in record.get("ages") or ():
        if isinstance(age, int):
            return age
    return None


def a_person_with_an_age(memory, understood=None):
    """The person the line is about, taken from the store, as `{"who", "age", ...}` or None.

    `understood` is this turn's reading; its `clean`/`text` is what the line is read from, so a
    module that already has the reading does not have to pass the words twice.
    """
    from . import others
    from .topics import person

    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "")
    people = [one for one in others(memory) if isinstance(one, dict) and one.get("who")]
    if not people:
        # Nobody is kept one by one, but the chat may have been told the age of a group
        # ("theyre 4 in august") - that is a person in all but the relation, and a line that
        # points back at them is about them.
        return _the_group_record(memory, line)
    # The relation named in this line: "what should i get my son" is about him even when the
    # store holds three people with ages.
    named = person(line)
    if named:
        for one in people:
            if str(one.get("who") or "").lower() == named and _with_an_age(one):
                return one
    # A line that names a relation and an age of nobody in the store is about somebody new, and
    # the pronoun in it (`his birthday`) is that person, not one of the ones already kept.
    if named:
        return None
    said_him = bool(HIM_SAID.search(line))
    said_her = bool(HER_SAID.search(line))
    if said_him == said_her and THEM_SAID.search(line):
        return _the_ones_a_them_points_at(people)
    if said_him == said_her:
        # No pronoun, or both: the line does not pick one of the kept people out. It may still
        # point at the group the chat was told an age for ("theyre 4 in august").
        return _the_group_record(memory, line)
    wanted = HIM if said_him else HER
    found = [one for one in people
             if str(one.get("who") or "").lower() in wanted and _with_an_age(one)]
    if len(found) != 1:
        # Two sons and a "him": nobody in particular, so the generic answer stays.
        return None
    return found[0]


def _the_group_record(memory, line):
    """The people a "them" points back at, as a person record with their age, or None."""
    if not THEM_SAID.search(line or ""):
        return None
    age = _the_age_of_the_group(memory)
    if not age:
        return None
    return {"who": "them", "age": age}


def _the_ones_a_them_points_at(people):
    """The person a plural pronoun points at: the one with an age, when there is only one age.

    "them" is a group word, so it is read through what the store holds rather than guessed: one
    person with an age is who they mean, and so is a houseful of children the same age ("the
    twins are 5"). Two people of different ages and a "them" is nobody in particular - a present
    for the wrong age is worse than the answer written for nobody.
    """
    with_an_age = [one for one in people if _with_an_age(one)]
    if not with_an_age:
        return None
    ages = {_age(one) for one in with_an_age}
    if len(ages) != 1:
        return None
    return with_an_age[0]


# The relations that are a child of the family: a present for one of these is a child's present
# unless the chat has said how old they are.
CHILD_OF_THE_FAMILY = frozenset("""son daughter grandson granddaughter nephew niece stepson
    stepdaughter grandchild""".split())


def the_people(memory):
    """Every person the store keeps for this chat: `memory["others"]` plus the one in hand."""
    from . import others

    found = [one for one in others(memory) if isinstance(one, dict) and one.get("who")]
    one = memory.get("person") if isinstance(memory, dict) else None
    if isinstance(one, dict) and one.get("who") and one not in found:
        found.append(one)
    return found


def a_child_the_chat_is_about(memory, understood=None):
    """True when the person this chat is about is a child of the family, with or without an age.

    "my son starts school in september" then "what should i get him" was answered with the
    grown-up list - a kitchen knife, warm socks, decent coffee - because the present reader asks
    the store for an *age* and a line about a child starting school names no number. A relation
    that is a child's relation is what the answer needs to know: a son, a daughter, a nephew is a
    child's present unless the chat has said they are grown.
    """
    from .topics import person

    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "")
    people = the_people(memory)
    named = person(line)
    if named:
        # The line names the person it is about, so the store's son does not decide a present for
        # somebody else: "my son starts school" then "what should i get my mum" is a present for
        # the mother. An adult relation is never a child's present.
        if named not in CHILD_OF_THE_FAMILY:
            return False
        for one in people:
            if str(one.get("who") or "").lower() != named:
                continue
            age = _age(one)
            if age is not None and age >= 18:
                return False  # a grown son is a grown-up's present
        # A line that names a child relation of its own, with nobody in the store to go on: "what
        # should i get my nephew" is a child's present, and the row knows nothing else about him.
        return True
    said_him = bool(HIM_SAID.search(line))
    said_her = bool(HER_SAID.search(line))
    wanted = HIM if said_him and not said_her else HER if said_her and not said_him else None
    # One person can be held twice - the store's record with the age and the reading's own record
    # of the line that named them - so the age is read per person, not per record.
    ages = {}
    for one in people:
        who = str(one.get("who") or "").lower()
        age = _age(one)
        if age is not None:
            ages[who] = age
    if wanted is not None:
        # `him` with a son and a father in the store is nobody in particular, and a guess about
        # whose present it is is worse than the list for a person nobody knows: "my son is 4 |
        # my dad is 72 | what should i get him" is not the scooter and the duplo.
        of_that_kind = {str(one.get("who") or "").lower() for one in people
                        if str(one.get("who") or "").lower() in wanted}
        if len(of_that_kind) > 1:
            return False
    for one in people:
        who = str(one.get("who") or "").lower()
        if who not in CHILD_OF_THE_FAMILY:
            continue
        if wanted is not None and who not in wanted:
            continue  # "what should i get her" is not about the son
        age = ages.get(who)
        if age is not None and age >= 18:
            continue
        return True
    return False


def the_age_of_the_person_they_mean(memory, understood=None):
    """How old the person this line is about is, from the store, or None.

    A group the chat said the age of ("theyre 5 in june", kept as `memory["their_age"]`) is read
    the same way when the line points at them, so "what can i get them" is a five-year-old's
    present and not the list written for a grown-up nobody.
    """
    found = a_person_with_an_age(memory, understood)
    if found:
        return _age(found)
    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "")
    if not THEM_SAID.search(line) or HIM_SAID.search(line) or HER_SAID.search(line):
        return None
    held = memory.get("their_age") if isinstance(memory, dict) else None
    if isinstance(held, dict) and _with_an_age(held):
        return _age(held)
    return None
