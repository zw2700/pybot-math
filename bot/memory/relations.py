"""The people and animals in the store: a relation, the group it belongs to, the name they were given,
the age they were said to be, and the answer to a question about them.

Moved out of `bot/modules/memory_store.py` whole, name by name, with nothing changed but the
import lines: the file is over the Hub's 1 MiB limit, which stops every PR in the swarm until it
is under it again. The set is closed - these names need nothing from the module they left - and
the module imports them back, so no call site and no reply changes.
"""

from bot.compose import pick
from bot.memory import history
from bot.memory import facts as extract
from bot.memory import last_bot
from bot.memory import others
from bot.memory import stem
from bot.memory import user
from bot.memory.store_lines import CHILD
from bot.memory.store_lines import CHILD_OF
from bot.memory.store_lines import CHILD_RELATIONS
from bot.memory.store_lines import FAMILY_GROUP
from bot.memory.store_lines import GROUP_OF
from bot.memory.store_lines import HAVE_ANY_WORDS
from bot.memory.store_lines import HER_WORD
from bot.memory.store_lines import PERSON_GROUP
from bot.memory.store_lines import PET_WORDS
from bot.memory.store_lines import PRONOUN_PEOPLE
from bot.memory.store_lines import RELATION_ALIKE
from bot.memory.store_lines import _ABOUT_WHO
from bot.understanding import breeds
from bot.understanding.normalize import normalise
import re


CHAT_TAIL = re.compile(
    r"(?:[\s,]*\b(?:of|in|from|for|to)\s+(?:this|our|the)\s+"
    r"(?:chat|conversation|talk|session|thread|conversation so far)\b"
    r"(?:\s+(?:so far|today|here|with you|we have had))?)+")


def _folded(text, memory=None):
    """The line with chat-speak folded to plain words ("whats my name" -> "what is my name"),
    from the understanding engine when it has read this very line, else read here."""
    low = " ".join(str(text or "").lower().split())
    if not low:
        return ""
    seen = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(seen, dict) and " ".join(str(seen.get("text") or "").lower().split()) == low:
        folded = seen.get("norm_text") or ""
        if folded:
            return CHAT_TAIL.sub("", " ".join(
                folded.replace(" | ", " ").lower().split())).strip(" ,.;:!?")
    try:
        folded = normalise(text).get("norm_text") or ""
    except Exception:
        folded = ""
    # The chat itself named after the ask is a wrapper, not content: every reader below works on
    # the ask inside it ("what did i say at the start of this chat" is "what did i say at the
    # start"), so it comes off here, once, for all of them.
    return CHAT_TAIL.sub("", " ".join(
        (folded or low).replace(" | ", " ").lower().split())).strip(" ,.;:!?")


def _person_from_pronoun(text, memory, named_here=()):
    """Who a bare "she"/"he" in this line is: the last person named whose pronoun fits.

    "my mum is coming on sunday" then "she doesnt eat meat" is a fact about the mum, not about
    nobody: without this the diet is kept against "", and the next "what did i say about my mum"
    has nothing to find.
    """
    low = text.lower()
    people = [who for who in (user(memory).get("people") or []) if isinstance(who, str)]
    # A person the store already keeps a fact about is someone "she"/"he"/"they" can point at,
    # even when their name went into the fact rather than into the list of people: "my kids are
    # allergic to nuts" files a kid, and the next "what can they eat" is about that kid.
    people += [str(entry.get("who")) for entry in others(memory) if entry.get("who")]
    people = list(named_here) + people
    for pronoun, fits in (("she|her", extract.SHE), ("he|his", extract.HE)):
        # "he's 8" and "shes 5" are the same pronoun as "he" and "she": people type the apostrophe
        # out, and a line whose pronoun was not seen fell back to the last person named, which put
        # the daughter's age on the son.
        if re.search(r"\b(?:" + pronoun + r")(?:'s|s)?\b", low):
            for who in _newest_first(people, memory):
                # A plural is not one person: "my kids are 5 and 7" then "what did i say his
                # age was" said one of the kids' ages, when "his" was the puppy three lines up.
                if who.endswith("s") and who not in fits:
                    continue
                # "mother in law" is a she though the phrase is not a word in the list: the
                # person is the relation word the phrase opens with.
                if _pronoun_fits(who, fits):
                    return who
            # A "he" when the only people in the chat are her mum and her sister is not one of
            # them, and answering about the newest one anyway puts a fact on the wrong person.
            return ""
    people = _newest_first(people, memory)
    return people[0] if people else ""


def _gender_of(who):
    """The gender a person word carries, or "" when it carries none ("partner", "kid")."""
    word = str(who or "").strip().lower()
    if not word:
        return ""
    parts = [part for part in re.split(r"[-\s]+", word) if part]
    for part in [word] + parts:
        if part in extract.SHE and part in extract.HE:
            return ""  # partner, friend, colleague: either
        if part in extract.SHE:
            return "she"
        if part in extract.HE:
            return "he"
    # "stepmum", "granddad", "godmother": the gender sits at the end of a word this file has no
    # name for. The longest ending wins, so "granddad" ends in "dad" and not in "gran".
    for roots, gender in ((extract.SHE, "she"), (extract.HE, "he")):
        for root in sorted((root for root in roots if len(root) > 2), key=len, reverse=True):
            if word.endswith(root):
                return gender
    return ""


def _pronoun_fits(who, fits):
    """Whether a pronoun of that gender can point at this person.

    A word that says no gender either way ("partner", "kid") can be either, so it is reachable by
    both pronouns; a word that names one gender is only that one, whether the whole word names it
    ("mum") or only its ending does ("stepmum", "granddad").
    """
    who = str(who or "").strip().lower()
    if who in fits:
        return True
    gender = _gender_of(who)
    if not gender:
        return True
    return (extract.SHE if gender == "she" else extract.HE) is fits


def _newest_first(people, memory):
    """The people, the one named last in the chat first, each kept once.

    "my son is allergic to nuts" / "my wife is vegetarian" / "my husband is diabetic" makes
    three people, and a bare "he" in the next line is about the husband. The list is not in
    that order on its own: the people the store keeps a fact for are added after the list of
    names, so a stale "son" sat after a fresh "husband" and "is he allergic to anything" was
    answered from the son. The order of the facts is the order they were said in, so the newest
    mention of each person comes first; a person named twice takes their newest place.
    """
    order = []
    for entry in reversed(memory.get("facts_log") or ()):
        if not isinstance(entry, dict):
            continue
        text = str(entry.get("text") or "").lower()
        for who in people:
            if who and who not in order and re.search(r"\b" + re.escape(who) + r"s?\b", text):
                order.append(who)
    for who in reversed(people):
        if who and who not in order:
            order.append(who)
    return order


PERSON_AFTER = re.compile(
    r"^(?:\s*$|\s*[?.!,;]|\s+(?:is|are|was|were|and|or|now|then|today|already|yet|turning|"
    r"turn|turns|aged|age|again|too)\b)", re.I)


def _named_person(low, memory=None):
    """The relation a line names as a person, or "" when it names their thing.

    A wrong answer is worse than the shrug it replaces, so "how old is my sons school" and "how
    old is my mums car" name nobody: the possessive takes the word away from the person.

    The family words people use are wider than the ones the store's oldest list names - a stepson
    and a grandson are their own people - so every word the store can file is a word an ask can
    name. One of those wider words only counts when the chat was told about that person: with the
    store empty, "how old are my grandparents" is not "you haven't told me how old your grandparent
    is", because the line gave the ages itself and the plural is a group the store does not keep.
    """
    # A pair of people named as one ("my partner's mum", "my sisters husband") is the person the
    # store filed the age against: read word by word the ask lands on "mum" and answers "You
    # haven't told me how old your mum is" about a line that gave her age. The pair is looked for
    # first and only counts when the chat holds that exact pair, so "my mums car" still names
    # nobody.
    chained = extract.a_chained_person(low)
    if chained:
        # The pair is what the line names, whether or not the chat holds an age for her: with
        # nothing filed, the honest line is "You haven't told me how old your partner's mum is",
        # never "your mum", which is a person the line did not ask about.
        return extract.a_person_word(chained)
    for relation in extract.KIN_WORDS + extract.ALONE_PERSON:
        # "my mother in law" is a person of her own and not a mother: the second words are kept,
        # so the age or the name filed against her is found by the ask that names her.
        for found in re.finditer(r"\b" + relation + r"(?:\s+in\s+laws?)?(?:'s|s)?\b", low, re.I):
            if not PERSON_AFTER.match(low[found.end():]):
                continue
            if (memory is not None and relation not in extract.RELATIONS
                    and not _a_person_in_the_store(memory, relation)):
                continue
            name = " ".join(found.group(0).lower().replace("'s", "").split())
            name = re.sub(r"\bin laws$", "in law", name)
            name = re.sub(r"s$", "", name) if not name.endswith("law") else name
            return relation if name == relation else name
    return ""


def _a_person_in_the_store(memory, who):
    """Whether the chat was ever told about this person, by the word the line used."""
    who = str(who or "").lower()
    if not who:
        return False
    for entry in others(memory):
        if str(entry.get("who") or "").lower() == who:
            return True
    return who in [str(person).lower() for person in (user(memory).get("people") or [])]


# "about" and "on" are the same preposition in this ask: "what have you got on my mum" is "what do
# you know about my mum" said the way people say it, and it was answered with the search hedge
# while the store held her age. "have" and "had" are the same asking verb as "got" - "what do you
# have on my kids" asks for the same facts.
ABOUT_PERSON_ASK = re.compile(
    r"\b(?:what|anything|everything|much)\b[^?]{0,30}?\b(?:know|knows|remember|learnt|learned|"
    r"told|tell|said|say|mention|mentioned|got|have|has|had)\b[^?]{0,20}?\b(?:about|on)\s+(?:"
    + _ABOUT_WHO + r")|"
    r"\btell me (?:a bit |a little |more |anything )?(?:more )?about\s+(?:" + _ABOUT_WHO + r")|"
    # The same ask with the asking word after the verb, which is how people say it: "do you know
    # anything about my mum", "did i tell you much about my son". Read as none of these, the line
    # fell to the search hedge while "what do you know about my mum" got the whole person back.
    r"\b(?:do|did|can|could)\s+(?:you|i)\s+(?:ever\s+|already\s+)?(?:know|remember|recall|tell|"
    r"told|mention|mentioned|say|said|hear|heard)\b[^?]{0,30}?\b(?:about|on)\s+(?:"
    + _ABOUT_WHO + r")",
    re.I)


ANOTHER_PERSON = re.compile(r"^(?:(?:and|or|also|then|ok|okay|what about|and what about|"
                            r"how about)\s+)*(?:my|our|the|your)?\s*"
                            r"(?:little|big|older|younger|eldest|youngest|oldest|other|second|"
                            r"third)?\s*(?:" + "|".join(extract.RELATIONS) + r")s?\s*\?*$", re.I)


def _continues_an_about_ask(memory, low):
    """True when the line is another person named after an ask about a person.

    The ask of the turn before is the one being continued, so "and my dad" reads as "what do you
    know about my dad" and not as the age question the figure in the earlier line suggests.
    """
    line = str(low or "").strip()
    if not ANOTHER_PERSON.match(line) or not _named_person(line):
        return False
    users = [str(turn.get("user") or "") for turn in _every_line(memory) if turn.get("user")]
    # The line being answered may already be in the log, so the ask before it is the last one
    # that is not this line.
    here = line.lower()
    while users and users[-1].strip().lower() == here:
        users.pop()
    return bool(users and ABOUT_PERSON_ASK.search(users[-1].lower()))


AGE_ASK = re.compile(r"\bhow old (?:is|are|was|were)\b|\bwhat age(?:s)? (?:is|are|was|were)\b|"
                     r"\bwhat ages?\b|\bhow old\b")


AGE_RULE_WORD = re.compile(r"^(?:do|does|did|should|shall|can|could|will|would|must|may|might|"
                           r"need)\b", re.I)


AGE_YOU_SAY = re.compile(r"^(?:you|u|i)\s+(?:say|said|think|guess|remember|know|reckon)\b",
                         re.I)


AGE_COPULA = re.compile(r"^(?:is|are|was|were|be|am)\b", re.I)


AGE_ADVERB = re.compile(r"^(?:exactly|really|roughly|approximately|about|now|actually|again|"
                        r"already|even)\b", re.I)


AGE_DETERMINER = re.compile(r"^(?:my|our|your|their|his|her|the|a|an)\b", re.I)


AGE_PERSON_WORD = re.compile(
    r"^(?:kids?|children|child|family|i|you|u|we|they|them|he|she|everyone|both|little|one)\b",
    re.I)


def _a_word_the_store_knows(memory, word):
    """Whether the word is the name of a person or an animal this chat was told about."""
    word = str(word or "").lower()
    if not word:
        return False
    for entry in others(memory):
        if word in (str(entry.get("name") or "").lower(), str(entry.get("who") or "").lower()):
            return True
    for pet in user(memory).get("pets") or []:
        if isinstance(pet, dict) and str(pet.get("name") or "").lower() == word:
            return True
    return word in [str(person).lower() for person in (user(memory).get("people") or [])]


def _age_is_about_a_person(low, memory):
    """Whether an age ask is about somebody in the chat rather than about the world.

    A rule ask names children or a relation too - "what age do kids stop napping", "how old should
    a kitten be to leave its mum" - but the age belongs to the rule or to the animal, and the
    store has nothing to recall about it. The person has to be what the ask asks, so the answer is
    left to the modules that know the world; the store's own recall asks are untouched.
    """
    if _the_place_end(low)[1]:
        # "how old is the eldest", "how old is the little one": a child named by their place in
        # the family is a person the chat can have been told an age for, and without this the ask
        # was left to the modules that know the world - a question about contracts answered the
        # one about the eldest.
        return True
    ask = AGE_ASK.search(low)
    if not ask:
        return True
    if extract.a_chained_person(low):
        # "how old is my partner's mum" is a person, not a rule about mothers: the pair read word
        # by word is not a word the store knows, so the ask was taken for a question about the
        # world and answered with a search hedge one line after the age had been noted.
        return True
    rest = low[ask.end():].strip()
    while True:
        adverb = AGE_ADVERB.match(rest)
        if not adverb:
            break
        rest = rest[adverb.end():].strip()
    rule = AGE_RULE_WORD.match(rest)
    if rule:
        # "how old did you say he was" asks the store what it was told, so the asking verb keeps
        # the ask about the person named after it. "what age do kids stop napping" has no such
        # verb and is a rule.
        if not AGE_YOU_SAY.match(rest[rule.end():].strip()):
            return False
        rest = rest[rule.end():].strip()
    copula = AGE_COPULA.match(rest)
    if copula:
        rest = rest[copula.end():].strip()
    determiner = AGE_DETERMINER.match(rest)
    if determiner:
        # "a kitten" and "an animal" name the kind, not one of theirs: "how old is a kitten when it
        # leaves its mum" is about kittens, while "the kitten" and "my kitten" are the one at home.
        if determiner.group(0).lower() in ("a", "an"):
            return False
        rest = rest[determiner.end():].strip()
    word = re.match(r"[a-z']+", rest, re.I)
    if not word:
        return False
    subject = word.group(0)
    if AGE_PERSON_WORD.match(subject) or subject.lower() in extract.KIN_WORDS:
        return True
    if _PET_WORD.fullmatch(subject) or _PET_WORD.fullmatch(subject.rstrip("s")):
        return True
    return _a_word_the_store_knows(memory, subject)


AGE_AGAIN = re.compile(r"^(?:(?:and|or|also|ok|okay|what about|and what about)\s+)*"
                        r"(?:my|your|the|our)?\s*"
                        r"(?:little|big|older|younger|eldest|youngest|oldest|other)?\s*"
                        r"(" + "|".join(extract.KIN_WORDS + extract.ALONE_PERSON)
                       + r"|kids?|children)s?\s*$", re.I)


NAME_AGAIN = re.compile(
    r"^(?:(?:and|or|also|then|ok|okay|what about|and what about)\b[\s,]*)*"
    r"(?:my|our|your|the)?\s*(?:" + "|".join(extract.KIN_WORDS) + r")(?:'s|s)?\s+name\s*\?*$",
    re.I)


AGE_SAID = re.compile(r"\b(?:your|his|her|their)\s+\w+\s+is\s+\d+\b|^\w+\s+is\s+\d+\b", re.I)


THE_KIDS = re.compile(r"\b(?:kids?|children|child|family|everyone|both|they|them|their|"
                      r"boys?|girls?)\b", re.I)


CHILD_WORD = re.compile(r"\b(?:kids?|children|child|family|boys?|girls?)\b", re.I)


# The plurals that are not the word with an "s" on the end. A singular ask reaches the group the
# chat filed under the plural: "how old is my grandchild" after "my grandchildren are 3 and 5".
_IRREGULAR_PLURAL = {"child": "children", "grandchild": "grandchildren"}


AGE_WORD = re.compile(r"\b(?:my|our|the|their|his|her|your)\s+(?:\w+\s+)?ages?\b|"
                      r"\bages?\s+of\s+(?:my|our|the|their)\b", re.I)


AGE_AS_A_CAUSE = re.compile(
    r"\b(?:just|only|part of|down to|because of|normal for|usual for|expected at)\s+"
    r"(?:\w+\s+){0,2}(?:age|old age|getting old)\b|\bold age\b|\bat (?:her|his|their|my) age\b",
    re.I)


GROUP_ASK = re.compile(
    r"\b(?:my|the|his|her|their|our|your)\s+("
    + "|".join(sorted(FAMILY_GROUP, key=len, reverse=True)) + r")\b", re.I)


def _tidy_name(value):
    """"rufus" is the name they mean, and a name reads "Rufus" at the start of a sentence."""
    value = str(value or "").strip(" .,!?;:")
    return value[:1].upper() + value[1:] if value and value[:1].islower() else value


def _same_as_last(reply, memory):
    """True when this exact sentence was the bot's line in the turn just before."""
    turns = memory.get("turns") or []
    for turn in reversed([turn for turn in turns if isinstance(turn, dict)]):
        said = turn.get("bot")
        if isinstance(said, str) and said.strip():
            return said.strip() == str(reply).strip()
    return False


def _animal_family(animal):
    """The animal a pet word belongs to: a puppy is a dog, a kitten is a cat."""
    word = str(animal or "").lower()
    return {"puppy": "dog", "dog": "dog", "kitten": "cat", "cat": "cat",
            "bunny": "rabbit", "rabbit": "rabbit", "goldfish": "fish", "fish": "fish",
            "pony": "horse", "horse": "horse", "bird": "parrot", "parrot": "parrot"}.get(
                word, word)


def _a(word):
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


THEIR_NAME = re.compile(
    r"\b(?:what|which)\b[^.?!]*\bname\b|"
    r"\bwhat (?:is|was) (?:my|our)\s+\w+'?s?\s+(?:called|named)\b|"
    r"\bwhat do (?:i|you) call my\b", re.I)


THEIR_AGE = re.compile(
    r"\bhow old (?:is|was|are|were)\b|\bwhat age (?:is|was)\b|"
    r"\b(?:what|which)(?:'s| is| was| are)?\s+"
    r"(?:(?:my|our)\s+\w+'?s?|her|his|their)\s+age\b", re.I)


GROUP_WORDS = "|".join(sorted(GROUP_OF, key=len, reverse=True))


GROUP_NAME_ASK = re.compile(
    r"\bwhat (?:are|were)\s+(?:my|our|the)\s+(?P<a>" + GROUP_WORDS + r")\s+called\b"
    r"|\bwhat (?:are|were)\s+(?:my|our|the)\s+(?P<b>" + GROUP_WORDS + r")['\u2019s]*\s+names?\b"
    r"|\b(?:names? of|name of)\s+(?:my|our|the)\s+(?P<c>" + GROUP_WORDS + r")\b"
    r"|\b(?:my|our|the)\s+(?P<d>" + GROUP_WORDS + r")['\u2019s]*\s+names\b"
    r"|\bwhat (?:are|were)\s+(?:they|their|them)\s+called\b"
    r"|\bwhat are their names\b|\btheir names\b", re.I)


THEIR_TASTE_WHAT = re.compile(
    r"\bwhat\s+(?:does|do|did)\s+"
    r"(?:(?:my|our)\s+(?P<who>[a-z][a-z'\u2019-]*)|(?P<pronoun>she|he|they))\s+"
    r"(?P<how>like|love|enjoy|hate|dislike|not like)\b", re.I)


THEIR_TASTE_INTO = re.compile(
    r"\bwhat\s+(?:is|was)\s+"
    r"(?:(?:my|our)\s+(?P<who>[a-z][a-z'\u2019-]*)|(?P<pronoun>she|he|they))\s+"
    r"(?:into|keen on|mad about|a fan of|big on|fussed on)\b", re.I)

# The dislike asked for the other way round. Every pattern above puts the taste verb after the
# person ("what does he like"), and a person who wants to know what somebody cannot stand says it
# with the "not" in front of the person, often with a word before that:
#     what food doesnt he like
#     what doesnt she like
#     what else doesnt he like
#     what wont she eat
#     whats he not keen on
# Without a reader here all five were answered with something else entirely - the kitchen's
# fussy-eater card for a son who does not like cheese, the last answer said again, a search hedge
# about a father who is not keen on spicy food. The dislike the chat already gave is a fact the
# store holds, so it is said back exactly as it is for the other way round. Only a bare ask counts
# (the line ends at the verb), so "what doesnt he like about school" is still somebody else's.
THEIR_TASTE_NOT = re.compile(
    r"\bwhat(?:\s+[a-z']+){0,2}?\s+"
    r"(?:doesn'?t|doesn|does\s+not|don'?t|do\s+not|won'?t|will\s+not|can'?t|cannot|never)\s+"
    r"(?:(?:my|our)\s+(?P<who>[a-z][a-z'\u2019-]*)|(?P<pronoun>she|he|they))\s+"
    r"(?:really\s+|actually\s+|even\s+|ever\s+)?"
    r"(?:like|love|eat|drink|have|stand|touch|want|be\s+keen\s+on)\b"
    r"(?:\s+(?:eating|drinking|at\s+all|really|then|now|though))*\W*$", re.I)

# "whats he not keen on", "what is she not a fan of": the taste is put as a negative the person
# carries, in the same words the "into" reader above knows.
THEIR_TASTE_NOT_INTO = re.compile(
    r"\bwhat(?:'s|s|\s+is|\s+was)?(?:\s+[a-z']+)?\s+"
    r"(?:(?:my|our)\s+(?P<who>[a-z][a-z'\u2019-]*)|(?P<pronoun>she|he|they))\s+"
    r"(?:not|isn'?t|is\s+not)\s+"
    r"(?:into|keen\s+on|mad\s+about|a\s+fan\s+of|big\s+on|fussed\s+on)\b\W*$", re.I)


THEIR_TASTE_A_YES_NO = re.compile(
    r"\b(?:does|do|did)\s+"
    r"(?:(?:my|our)\s+(?P<who>[a-z][a-z'\u2019-]*)|(?P<pronoun>she|he|they))\s+"
    r"(?P<how>like|love|enjoy|hate|dislike)\s+(?P<thing>[a-z][a-z'\u2019 ]*?)\W*$", re.I)


def _their_taste(memory, low):
    """What a person the chat knows likes, said back for an ask about it.

    Only a fact the store holds is answered, the same rule as a name or an age, and only for a
    person it can name: "what does she like" with nobody pointed at stays free for whoever can
    answer it. The verb comes from the ask when the ask has one ("does my mum like gardening")
    and from the fact when it does not ("what does my mum like").
    """
    said = None
    how = ""
    thing = ""
    for pattern in (THEIR_TASTE_A_YES_NO, THEIR_TASTE_WHAT, THEIR_TASTE_INTO):
        match = pattern.search(low)
        if match:
            said = match
            break
    if said is None:
        # The same fact asked for with the "not" in front of the person: the answer is what is on
        # their dislike list, and that is what the reader below does with "not like".
        for pattern in (THEIR_TASTE_NOT, THEIR_TASTE_NOT_INTO):
            match = pattern.search(low)
            if match:
                said = match
                how = "not like"
                break
    if said is None:
        return None
    how = how or (said.groupdict().get("how") or "").lower()
    thing = (said.groupdict().get("thing") or "").strip().lower()
    who = (said.groupdict().get("who") or "").lower()
    pronoun = (said.groupdict().get("pronoun") or "").lower()
    known = None
    if who:
        known = next((entry for entry in others(memory)
                      if (entry.get("who") or "").lower() == who), None)
    elif pronoun:
        fits = extract.SHE if pronoun in ("she", "her") else extract.HE
        known = next((entry for entry in reversed(others(memory))
                      if (entry.get("who") or "").lower() in fits
                      and (entry.get("likes") or entry.get("dislikes"))), None)
        if known is not None:
            who = (known.get("who") or "").lower()
    if known is None:
        return None
    likes = [str(item) for item in (known.get("likes") or []) if str(item).strip()]
    dislikes = [str(item) for item in (known.get("dislikes") or []) if str(item).strip()]
    if thing:
        # "does my mum like gardening" is about that one thing, and the answer is about it too.
        for item in likes:
            if _same_thing(item, thing):
                return _they_like_sentence(who, [item], "yes", pronoun)
        for item in dislikes:
            if _same_thing(item, thing):
                return _they_like_sentence(who, [item], "no", pronoun)
        return None
    if how in ("hate", "dislike", "not like"):
        if not dislikes:
            if likes:
                # The list she had was taken back ("my wife hates mushrooms" then "actually she
                # loves them"), so "what does my wife hate" is answered with what is on the
                # other list now - the honest answer is nothing, and a hedge says less than that.
                said = _they_like_sentence(who, likes, "yes", pronoun)
                return "Nothing now \u2014 " + said[:1].lower() + said[1:]
            return ("You haven't told me what your " + who + " doesn't like yet.")
        return _they_like_sentence(who, dislikes, "no", pronoun)
    if not likes:
        # The store holds the person but not this list, and the honest line is better than the
        # search shrug: "what does my son hate" about a son it was told the age of is a question
        # the chat can answer in a word, and the kitchen's fussy-eater card is no answer to it.
        return "You haven't told me what your " + who + " likes yet."
    return _they_like_sentence(who, likes, "yes", pronoun)


def _same_thing(one, other):
    """Whether two ways of naming a taste are the same thing ("cooking", "cook")."""
    one = str(one or "").lower().strip()
    other = str(other or "").lower().strip()
    if not one or not other:
        return False
    if one == other:
        return True
    return stem(one.split()[-1]) == stem(other.split()[-1])


_PLURAL = frozenset("""kids children sons daughters boys girls parents friends brothers sisters
grandchildren grandkids nieces nephews cousins grandparents in-laws""".split())


def _plural_person(who):
    who = str(who or "").lower()
    return who in _PLURAL or (who.endswith("s") and who not in ("boss", "christmas"))


def _they_like_sentence(who, things, how, pronoun=""):
    """What they like, said back short: "Your sister loves cooking." / "Your son doesn't like
    mushrooms." The person comes first when the store can name them, and the pronoun they used
    when it cannot.
    """
    listed = " and ".join(things[:2])
    if who:
        head = "Your " + who + " "
        some = _plural_person(who)
    else:
        head = "They " if pronoun == "they" else "She " if pronoun == "she" else "He "
        some = pronoun == "they"
    if how == "no":
        return head + ("don't like " if some else "doesn't like ") + listed + "."
    return head + ("love " if some else "loves ") + listed + "."


THEIR_JOB = re.compile(
    r"\bwhat\s+(?:does|do|did)\s+"
    r"(?:(?:my|our)\s+(?P<who>[a-z][a-z'\u2019-]*)|(?P<pronoun>she|he|they))\s+do\b"
    r"(?:\s+(?:for (?:a living|work|their job)|as a job|exactly|all day|now))?\W*$|"
    r"\bwhat(?:'s|s| is| was)?\s+"
    r"(?:(?:my|our)\s+(?P<who2>[a-z][a-z'\u2019-]*)|(?P<pronoun2>she|he|they))"
    r"'?s?\s+(?:job|work)\b|"
    # "remind me what my brother does", "what she does": the same ask with the person in front of
    # the verb, which is how people ask for something to be told back to them.
    r"\bwhat\s+(?:(?:my|our)\s+(?P<who3>[a-z][a-z'\u2019-]*)|(?P<pronoun3>she|he|they))"
    r"\s+(?:does|do)\b\W*$", re.I)


def _their_job(memory, low):
    """What a person the chat knows does, said back for an ask about it.

    Only a role the store holds is answered, the same rule as a name or an age: "what does my
    sister do" with nothing kept about a sister stays free for whoever can answer it. The
    person is the one the ask names, or the one a pronoun points at.
    """
    match = THEIR_JOB.search(low)
    if not match:
        return None
    groups = match.groupdict()
    who = (groups.get("who") or groups.get("who2") or groups.get("who3") or "").lower()
    pronoun = (groups.get("pronoun") or groups.get("pronoun2")
               or groups.get("pronoun3") or "").lower()
    known = None
    if who:
        known = _a_kept_person(memory, who)
        if known is not None:
            who = (known.get("who") or "").lower()
    elif pronoun and pronoun != "they":
        fits = extract.SHE if pronoun == "she" else extract.HE
        known = next((entry for entry in reversed(others(memory))
                      if (entry.get("who") or "").lower() in fits and entry.get("job")), None)
        if known is not None:
            who = (known.get("who") or "").lower()
    if known is None:
        who_kept = bool(who) and not pronoun and (who in extract.KIN
                                                 or _kin_forms(who) & set(extract.KIN))
        if who_kept:
            # A question about somebody the store has nothing on is answered honestly, the same
            # way it answers a name or an age it was never told: a search hedge is no help with
            # a question only the person asking it can answer.
            return "You haven't told me what your " + who + " does yet."
        return None
    job = str(known.get("job") or "").strip()
    if not job:
        return "You haven't told me what your " + who + " does yet." if who else None
    if who and _plural_person(who):
        return "Your " + who + " work as " + _a(job) + "."
    if who:
        return "Your " + who + " is " + _a(job) + "."
    return ("She's " if pronoun == "she" else "He's ") + _a(job) + "."


def _kin_forms(who):
    """The relation words a possessive ask can name: "sisters" and "sister's" are "sister".

    "whats my sisters job" puts the possessive on the relation word, so the word the store
    holds is the same word without its ending.
    """
    word = str(who or "").lower().strip()
    forms = {word}
    bare = re.sub(r"(?:'s|s'|s)$", "", word)
    if bare and bare != word:
        forms.add(bare)
    forms.add(word + "s")
    return forms


def _a_kept_person(memory, who):
    """The entry the store holds for the person an ask names, if it holds one."""
    forms = _kin_forms(who)
    for entry in others(memory):
        if (entry.get("who") or "").lower() in forms:
            return entry
    return None


def _same_name_however_they_wrote_it(entry, line):
    """Whether the line names the person, under the name they have now or the one put right.

    "my daughter is called lily" then "its lilly not lily" keeps Lilly, and the ask after it -
    "how old is lily" - is about the same daughter: a correction puts a name right, it does not
    make the person the chat already knows a stranger to the next question.
    """
    if _same_name(entry.get("name") or "", line):
        return True
    return any(_same_name(old, line) for old in (entry.get("was") or []))


def _same_name(known, line):
    """Whether the person the store knows is the one the line names: "how old is janet".

    The line arrives folded, so "ann" is "an" by the time it gets here while the store keeps the
    name as it was said. Both sides are folded and compared, which is the only way an ask by a
    short name reaches the person it belongs to.
    """
    known = str(known or "").strip().lower()
    if not known:
        return False
    tokens = re.findall(r"[a-z']+", str(line or "").lower())
    for token in tokens:
        if token == known:
            return True
        folded = _folded(token)
        if folded == _folded(known):
            return True
    return False


def _more_than_one(who):
    """Whether the word for the person takes "are": "my kids are 4 and 7", "my mum is 72".

    "boss" ends in an s and is one person, and one rule for it lives in `_plural_person`:
    "Your boss are called Dave" is not a sentence anybody says.
    """
    return _plural_person(who)


def _canon_relation(word):
    """The relation a word names, in the word the store files it under: "mother" is "mum"."""
    word = str(word or "").strip(" .,").lower()
    word = RELATION_ALIKE.get(word, word)
    if word.endswith("s") and word[:-1] in RELATION_ALIKE:
        return RELATION_ALIKE[word[:-1]]
    if word.endswith("s") and word[:-1] in CHILD_RELATIONS:
        return word[:-1]
    return word


def _relations_of(who):
    """The relations a stored word for people stands for: "kids" is every child relation."""
    found = []
    for word in re.split(r"\s+and\s+|\s+|,", str(who or "").strip().lower()):
        canon = _canon_relation(word)
        if not canon:
            continue
        if canon in ("child", "children", "kid", "kids"):
            found.extend(CHILD_RELATIONS)
        elif canon == "parent" or canon == "parents":
            found.extend(GROUP_OF["parents"])
        else:
            found.append(canon)
    return tuple(found)


def _in_the_group(who, group):
    """Whether a relation the store holds is one of the people the ask named."""
    return any(word in group for word in _relations_of(who))


def _a_list_of_names(names):
    """Three names read "Jack, Emma and Ada", not "Jack and Emma and Ada"."""
    said = [str(name) for name in names if str(name)]
    if len(said) < 3:
        return " and ".join(said)
    return ", ".join(said[:-1]) + " and " + said[-1]


def _mentioned_the_group(memory, group, word):
    """Whether the chat was told the group exists, even with no name filed for any of them.

    "i have two children" then "what are my children called" is a chat that knows there are two
    of them: the honest answer is about the name, not "you haven't told me about your children".
    """
    held = user(memory)
    if word in ("children", "kids", "childs") and held.get("kids"):
        return True
    if any(_in_the_group(person, group) for person in (held.get("people") or [])):
        return True
    # What the store holds is not the whole of what was said: "my kids are tom and sam" is a line
    # the readers do not file, and the group was still named. Only a group nobody ever mentioned
    # may be answered "you haven't told me about your children".
    return _the_group_was_said(word, memory)


HAVE_ANY = re.compile(
    r"^(?:and\s+|so\s+|ok\s+|okay\s+|but\s+)?(?:do|have|did)\s+(?:i|we)\s+"
    r"(?:got|have|has)?\s*(?:(?:any|a|an)\s+)?"
    r"(?P<what>(?:" + "|".join(sorted(HAVE_ANY_WORDS, key=len, reverse=True)) + r")"
    r"(?:\s*(?:,|or|and)\s*(?:brothers|sisters|siblings|children|kids|parents|family)"
    r"|\s*(?:,|or|and)\s*(?:brother|sister|parent|child|kid))*)\b", re.I)


def _whether_they_have(memory, low):
    """Whether they have any of a kind of person, answered from the people on file.

    "do i have any brothers or sisters" is a question about the chat's own family, so a search
    for it is never the answer: the store says who it has been told about, and when the ask names
    two kinds of person and only one is on file it says which one it has nothing on. The answer
    is what was said and no more - it does not guess that a missing brother does not exist.
    """
    if not isinstance(low, str):
        return None
    match = HAVE_ANY.match(low.strip(" ,.!?;:"))
    if not match:
        return None
    words = [word for word in re.split(r"\s*(?:,|\bor\b|\band\b)\s*",
                                      match.group("what").lower()) if word]
    if not words:
        return None
    held = [entry for entry in others(memory) if isinstance(entry, dict)]
    # A relation they named without a name ("i have a sister") is kept as a word and not as a
    # person, so it still counts as a sister the chat has been told about.
    plain = [str(word).lower() for word in (user(memory).get("people") or [])]
    counts = {}
    found = []
    said_without_a_name = []
    empty = []
    for word in words:
        group = (CHILD_RELATIONS + GROUP_OF["parents"] + GROUP_OF["siblings"]
                 + GROUP_OF["grandparents"]) if word == "family" else (
                     GROUP_OF.get(word) or (_canon_relation(word),))
        mine = [entry for entry in held if _in_the_group(entry.get("who"), group)]
        if mine:
            found.append((word, mine[0]))
            continue
        hinted = [_canon_relation(one) for one in plain if _in_the_group(one, group)]
        count = user(memory).get("kids")
        if hinted:
            said_without_a_name.extend(hinted)
            continue
        if (isinstance(count, int) and not isinstance(count, bool) and count == 0
                and _in_the_group("child", group)):
            # A count of zero is an answer, not a gap: "do i have any children" after "i dont
            # have any kids" was "You haven't told me about any children yet", which is what the
            # store says to somebody who has told it exactly that.
            said_without_a_name.append(word)
            counts[word] = count
            continue
        if isinstance(count, int) and count > 0 and _in_the_group("child", group):
            # "i have two kids" told the chat how many there are, so "do i have any children"
            # is answered with the number and the name that is still missing.
            word = word if word in ("kids", "children", "childs") else "child"
            said_without_a_name.append(word)
            counts[word] = count
            continue
        empty.append(word)
    if not found and not said_without_a_name:
        asked = _a_plural_list(words)
        return pick(["You haven't told me about " + _a_or_any(words) + " yet.",
                     "Nothing on your " + asked + " yet - tell me and I'll keep it."], memory)
    said = []
    bare = list(dict.fromkeys(said_without_a_name))
    for word, entry in found:
        who = str(entry.get("who") or word).strip()
        name = str(entry.get("name") or "").strip()
        names = [str(one) for one in (entry.get("names") or []) if str(one).strip()]
        if not name and len(names) > 1:
            said.append("your " + who + " are called " + _a_list_of_names(names))
        elif name:
            said.append("your " + who + " " + _called(name))
        elif who not in bare:
            bare.append(who)
    line = ""
    if said:
        line = "You've mentioned " + _a_list_of_names(said)
    if bare:
        none_of_them = bool(counts) and not any(counts.values())
        how_many = next((value for value in counts.values() if value), 0)
        if none_of_them:
            # Said as none, not as a number that never arrived.
            line += (" " if line else "") + "You told me you don't have any " + \
                _a_list_of_words(bare) + "."
        else:
            if how_many:
                said_them = str(how_many) + " " + bare[0]
            else:
                said_them = _a_list_of_words([_with_article(word) for word in bare])
            names = ("their names" if len(bare) > 1 or how_many > 1
                     else HER_WORD.get(bare[0], "their") + " name")
            line += (" " if line else "") + "You've told me you have " + said_them + \
                ", but not " + names + " yet."
    if empty:
        tail = "no " + _a_list_of_words(empty) + " that you've told me about"
        if line:
            line = line.rstrip(".") + " - and " + tail + "."
        else:
            line = "You haven't mentioned any " + _a_list_of_words(empty) + " yet."
    return line if line.endswith(".") else line + "."


def _a_list_of_words(words):
    """A list of words for people, read "a sister and a brother"."""
    said = [str(word) for word in words if str(word)]
    if len(said) < 2:
        return "".join(said)
    if len(said) == 2:
        return said[0] + " and " + said[1]
    return ", ".join(said[:-1]) + " and " + said[-1]


def _more_than_one_word(word):
    """Whether a word for people is a plural one: "brothers", "children"."""
    word = str(word or "").strip().lower()
    return word.endswith("s") or word in ("children", "kids", "family")


def _with_article(word):
    """One kind of person, with the article the word takes: "a brother", "any sisters"."""
    word = str(word or "")
    return ("any " if _more_than_one_word(word) else "a ") + word


def _a_or_any(words):
    """An ask about a kind of person reads "a brother" or "any brothers or sisters"."""
    said = [str(word) for word in words if str(word)]
    if len(said) == 1:
        return _with_article(said[0])
    first = said[0]
    rest = " or ".join(said[1:])
    return ("any " if _more_than_one_word(first) else "a ") + first + " or " + rest


def _a_plural_list(words):
    """Two or three kinds of person read "brothers or sisters", not "and".
    """
    said = [str(word) for word in words if str(word)]
    if not said:
        return ""
    if len(said) == 1:
        return said[0]
    if len(said) == 2:
        return said[0] + " or " + said[1]
    return ", ".join(said[:-1]) + " or " + said[-1]


GROUP_NAMES_TYPED = re.compile(
    r"\bmy (?P<who>" + "|".join(["kids", "children", "childs", "sons", "daughters", "boys",
                                 "girls", "parents", "brothers", "sisters", "grandchildren"])
    + r")\s+(?:are|is)\s+(?P<names>[^.!?]{3,60})", re.I)


def _the_group_names_typed(word, memory):
    """The names a line of theirs gave for a group, as a list: "my kids are tom and ada".

    Only the names they typed are used, taken from the group word, and only when two or three of
    them are there: one word after "my kids are" is as likely to be a state ("happy", "young") as
    a name. The last line that gives them wins, because that is the one the chat is on.
    """
    said = []
    for turn in (memory or {}).get("turns") or []:
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("user") or "")
        match = GROUP_NAMES_TYPED.search(line)
        if not match:
            # "i have two kids" then "they are called tom and ada": the pronoun gives the names
            # for the group the line before named, so the group reply has them to say and does
            # not have to claim the chat holds nothing.
            names = _the_names_a_pronoun_gave(line)
            if names and ((memory or {}).get("user") or {}).get("kids"):
                said = names
            continue
        if not _in_the_group(match.group("who").lower(), GROUP_OF.get(word, ())):
            continue
        names = [one.strip(" .,") for one in re.split(r",|\band\b|&", match.group("names"))
                 if one.strip(" .,")]
        names = [one for one in names if 2 <= len(one) <= 14 and one.isalpha()
                 and one.lower() not in extract.KIN_WORDS]
        if 2 <= len(names) <= 3:
            said = names
    return said


THEY_ARE_NAMED = re.compile(
    r"^\W*(?:they|they're|theyre|those|these)\s+(?:are|were)\s+(?:called|named)\s+"
    r"(?P<names>[^.!?]{3,60})$", re.I)


def _the_names_a_pronoun_gave(line):
    """The names a "they are called ..." line gives, as a list, or []."""
    match = THEY_ARE_NAMED.search(str(line or "").strip())
    if not match:
        return []
    return _the_names_from(match.group("names"))


def _the_names_from(said):
    """Two or three names out of the words that follow "called", "named" or a comma.

    One word after "my kids are" is as likely to be a state ("happy", "young") as a name, and a
    word a relative is called ("my boys and my daughter") names no one, so only two or three plain
    words that are nobody's kin word count. One reader, because every reply that says a name back
    had its own copy of this test and they did not agree.
    """
    names = [one.strip(" .,") for one in re.split(r",|\band\b|&", str(said or ""))
             if one.strip(" .,")]
    names = [one for one in names if 2 <= len(one) <= 14 and one.isalpha()
             and one.lower() not in extract.KIN_WORDS]
    return names if 2 <= len(names) <= 3 else []


# A line that named more than one person, whatever shape it put them in: "my sister sarah has two
# boys", "the kids", "my parents", "two daughters". The words are the plural of the words the store
# files a person under (`CHILD_RELATIONS` and the group words), so a shape nobody wrote a rule for
# still has a word that says how many the line named.
PEOPLE_MANY = ("kids|children|childs|sons|daughters|boys|girls|brothers|sisters|twins|parents"
               "|grandchildren|grandparents|aunts|uncles|cousins|siblings|stepchildren|nieces"
               "|nephews|babies|teens|teenagers")

SEVERAL_PEOPLE_NAMED = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+"
    r"|a couple of|a few|both|the pair)\s+(?P<counted>" + PEOPLE_MANY + r")\b"
    r"|\b(?:my|our|the|his|her|their)\s+(?P<group>" + PEOPLE_MANY + r")\b"
    r"|\b(?P<bare>" + PEOPLE_MANY + r")\b", re.I)


# "a sister and a brother" is several people in two singular words, and neither word is in
# PEOPLE_MANY: the store files one person per word, so the plural an ask leans on is the pair
# itself. The words are the ones the store files a person under.
TWO_OF_KIN = re.compile(
    r"\b(?:my|our|the|a|an)\s+(?P<a>" + "|".join(sorted(extract.KIN_WORDS)) + r")\s+and\s+"
    r"(?:my|our|the|a|an)?\s*(?P<b>" + "|".join(sorted(extract.KIN_WORDS)) + r")\b", re.I)


def _the_several_named_before(memory):
    """The newest earlier line that named more than one person: (word, names, line).

    "their" and "they" mean more than one person, so the line they point at has to be one that
    named more than one. The line is read for the names it gave ("..., tom and ben", "called tom
    and ada") whether or not the store filed them, because the store files a person's own name and
    drops the people named beside them.
    """
    for line in reversed(history.the_lines_before(memory)):
        # The line has to be one that named them, not one that asked about them: "what are my
        # parents called" has the group word in it and no name at all, and reading a question as
        # the line that named the people answered "You told me about your parents, but not their
        # names" one turn after both names had been given.
        if not history.is_their_news(line):
            continue
        found = SEVERAL_PEOPLE_NAMED.search(line)
        names = _the_names_from(_the_names_tail(line))
        pair = TWO_OF_KIN.search(line) if not found else None
        if not found and not pair and not names:
            continue
        word = ((found.group("counted") or found.group("group") or found.group("bare"))
                if found else "").lower()
        # The words the line used, as it used them: "two boys" is the sister's boys and "your
        # kids" is nobody else's, so the answer says the line's own phrase instead of guessing
        # whose they are.
        phrase = " ".join(found.group(0).split()) if found else ""
        if pair:
            one, other = pair.group("a").lower(), pair.group("b").lower()
            word = one + " and " + other
            phrase = "your " + one + " and your " + other
        return word, names, phrase
    return "", [], ""


def _the_names_tail(line):
    """The words after "called", "named", a comma or the "are" of a group, where names go.

    "my boys are tom and ben" gave its names with no word to announce them, and the reader that
    only looked after "called" and a comma said the chat had no names for the boys one line after
    it had given them.
    """
    said = str(line or "")
    match = re.search(r"(?:\bcalled\b|\bnamed\b|,)\s*(?P<names>[^.!?]{3,60})$", said, re.I)
    if match:
        return match.group("names")
    match = re.search(r"\b(?:" + PEOPLE_MANY + r")\s+(?:are|were)\s+(?P<names>[^.!?]{3,60})$",
                      said, re.I)
    return match.group("names") if match else ""


def _the_names_of_them_all(memory):
    """The names of the several people an earlier line named, for a plural pronoun ask.

    "what are their names" leans on the line before it, and the store holds one person from that
    line and not the people it named: "my sister sarah has two boys, tom and ben" files the sister
    and drops the boys, so answering from the store said "Your sister is called Sarah." - one
    person, and the wrong one. The line is the antecedent of "their", so the answer comes from
    the line, and with the people named and no names given it says exactly that instead of
    denying the line that is right there.
    """
    word, names, phrase = _the_several_named_before(memory)
    if names:
        return _a_list_of_names([_called(one) for one in names]) + "."
    if word:
        told = re.sub(r"^(?:my|our|the)\s+", lambda m: "your ", phrase, flags=re.I) or word
        return pick(["You told me about " + told + ", but not their names - what are they called?",
                     "I've got " + told + " from you, but not their names. Tell me and I'll keep "
                     "them."], memory)
    return None


def _the_names_they_typed(word, memory):
    """The names a line of theirs gave for a group, said back: "Tom and Sam, then - your kids"."""
    said = _the_group_names_typed(word, memory)
    if not said:
        return None
    return _a_list_of_names([_called(one) for one in said]) + ", then - I'll keep those as your " \
        + word + "' names."


def _the_names_of_the_group(memory, low):
    """The names of more than one person they told us about: "Your son is called Jack, and ..."

    A plural ask ("what are my children called", "what are their names", "the names of my kids")
    is about the people the chat already holds, so it is answered from them and from nowhere
    else. With the group named and no name on file the honest line is that, never a search for
    what to call a child; with only a plural pronoun it stays free for whoever can answer it,
    because "what are their names" can be about people the store was never told about.
    """
    if not isinstance(low, str):
        return None
    ask = GROUP_NAME_ASK.search(low)
    if not ask:
        return None
    word = next((ask.group(g) for g in ("a", "b", "c", "d") if ask.group(g)), "").lower()
    known = [entry for entry in others(memory) if isinstance(entry, dict)]
    if word:
        group = (CHILD_RELATIONS + GROUP_OF["parents"] + GROUP_OF["siblings"]
                 + GROUP_OF["grandparents"] + GROUP_OF["grandchildren"]
                 + GROUP_OF["aunts"] + GROUP_OF["uncles"] + GROUP_OF["cousins"])
        if word != "family":
            group = GROUP_OF.get(word, ())
        known = [entry for entry in known if _in_the_group(entry.get("who"), group)]
        if not known and not _mentioned_the_group(memory, group, word):
            return pick(["You haven't told me about your " + word + " yet.",
                         "I've got nothing about your " + word + " yet - tell me and I'll keep it."],
                        memory)
    else:
        # A plural pronoun is more than one person: "their" can never be answered with the one
        # person a line happened to file beside the people it named. "my sister sarah has two
        # boys" files the sister, and "whats their names again" said "Your sister is called
        # Sarah." - one person, and not the one asked about.
        # Two entries are two people, whatever each one is called: "my mum is called janet and my
        # dad is called brian" files both, and reading each entry on its own dropped the pair and
        # answered "Your dad is called Brian." The filter is for the one entry a line about
        # several people leaves behind - "my sister sarah has two boys" files the sister alone.
        if len(known) < 2:
            known = [entry for entry in known
                     if _more_than_one(entry.get("who"))
                     or len([one for one in (entry.get("names") or []) if str(one).strip()]) > 1
                     or int(entry.get("count") or 1) > 1]
    said = []
    for entry in known[:4]:
        who = str(entry.get("who") or "").strip()
        name = entry.get("name")
        names = [str(n) for n in (entry.get("names") or []) if str(n).strip()]
        # "my parents are called janet and brian" files both the pair and the first name, and
        # the pair is the whole fact: said from the single name the answer dropped Brian.
        if len(names) > 1:
            # "my mum and dad are dave and sue" is one fact about two people: the line never said
            # which name is whose, so the answer says what it was told.
            said.append((who, _a_list_of_names(names), True))
        elif isinstance(name, str) and name:
            said.append((who, _called(name), False))
    if not said:
        if not word:
            # The people a plural pronoun points at are in an earlier turn or nowhere: the chat
            # itself is the only place to look, and it answers this or nothing.
            forgotten = _the_names_of_them_all(memory)
            if forgotten:
                return forgotten
            # The chat holds more than one person and a name on none of them: the group is the
            # people it holds, and the honest line is about all of them. Falling through to the
            # reader that answers about one person said "You haven't told me your brother's name"
            # to a question about a sister and a brother, and with nothing to name at all it said
            # "You haven't told me a name for your  yet".
            group = next((str(entry.get("who") or "").strip() for entry in known
                          if _more_than_one(entry.get("who"))), "")
            if group:
                return pick(["You haven't told me a name for your " + group + " yet - what are "
                             "they called?", "I've got your " + group + " but no names for them - "
                             "what are they called?"], memory)
        if _the_group_was_said(word, memory):
            # The line that named them is in the chat and the readers did not file it: saying
            # "you haven't told me a name for your kids" denies what was just typed, and the
            # search hedge is no better. What the store has is the line itself, so it says the
            # names back and takes them.
            typed = _the_names_they_typed(word, memory)
            if typed:
                return typed
            # Named, and the names could not be read out of the line ("my children are with my
            # mum this weekend" names them and gives no names): asking for them keeps the chat
            # moving, where the denial denies and the search hedge says nothing about them.
            return pick(["What are your " + word + " called? I'll keep their names.",
                         "Tell me what your " + word + " are called and I'll keep it."], memory)
        if not word:
            # Nothing to name: the line came this far with no group word, and "a name for your
            # yet" is not a sentence. The readers below can still answer it, so this one declines.
            return None
        return pick(["You haven't told me a name for your " + word + " yet.",
                     "I don't have a name for your " + word + " yet."], memory)
    # Two people filed under the same word are one sentence: "my kids are tom 8 and ada 5" files
    # Tom and Ada separately, and "your kids are called Tom, and your kids are called Ada" reads
    # as a list of two groups rather than of two children.
    grouped = []
    for who, value, paired in said:
        for at, (held_who, held_value, held_paired) in enumerate(grouped):
            if not paired and not held_paired and held_who == who:
                grouped[at] = (who, held_value + "\0" + value, paired)
                break
        else:
            grouped.append((who, value, paired))
    parts = []
    for who, value, paired in grouped:
        if paired:
            parts.append("you told me your " + who + " are called " + value)
        else:
            parts.append("your " + who + (" are" if _more_than_one(who) else " is")
                         + " called " + _a_list_of_names(value.split("\0")))
    if len(parts) == 1:
        one = parts[0]
        return (one[0].upper() + one[1:]) + "."
    if len(parts) == 2 and not any(paired for _, _, paired in said):
        return (parts[0][0].upper() + parts[0][1:]) + ", and " + parts[1] + "."
    return ". ".join(part[0].upper() + part[1:] for part in parts) + "."


def _did_you_mean(entry, property_, ask_gender=""):
    """The one person the store holds, offered back as a question rather than stated as a fact.

    The sentence agrees with the person: "She is 50", "They are 50", "They turn 61 next april".
    When the ask's own pronoun is the other one - "how old is she" about the son the store holds -
    the mismatch is said out loud rather than papered over, because a "she" is not the son and
    answering as though it were is a fact on a person they did not mean.
    """
    who = str(entry.get("who") or "")
    gender = _gender_of(who)
    pronoun = "She" if gender == "she" else "He" if gender == "he" else "They"
    plural = pronoun == "They"
    if property_ == "name":
        verb = "are called " if plural else "is called "
        fact = _called(str(entry.get("name") or ""))
    elif entry.get("turns"):
        verb = "turn " if plural else "turns "
        fact = str(entry.get("age") or "") + " " + str(entry["turns"])
    else:
        verb = "are " if plural else "is "
        fact = str(entry.get("age") or "")
    if ask_gender and gender and gender != ask_gender:
        him = "her" if gender == "she" else "him"
        return ("I've only got your " + who + " down, and " + pronoun.lower() + " " + verb
                + fact + ". Did you mean " + him + "?")
    return "Did you mean your " + who + "? " + pronoun + " " + verb + fact + "."


def _relation_reply(memory, low):
    """A fact about someone they mentioned, said back: "Your mum is called Janet."

    The person is the one the ask names ("my mum", "janet"), the one it points at with a pronoun
    ("how old is she"), or, when it names nobody, the last person the store heard about. Only a
    fact the store holds is answered: "what's my mum's name" with no name keeps the turn free for
    whoever can answer it.
    """
    tasted = _their_taste(memory, low)
    if tasted:
        return tasted
    worked = _their_job(memory, low)
    if worked:
        return worked
    have_any = _whether_they_have(memory, low)
    if have_any:
        return have_any
    grouped = _the_names_of_the_group(memory, low)
    if grouped:
        return grouped
    wants_name = bool(THEIR_NAME.search(low) or NAME_AGAIN.match(low))
    wants_age = bool(THEIR_AGE.search(low))
    by_name = ""
    if not (wants_name or wants_age):
        return None
    property_ = "name" if wants_name else "age"
    who = _named_person(low, memory)
    if (property_ == "age" and who and not who.endswith("s")
            and re.search(r"\b" + re.escape(who) + r"s\b", low)):
        # "how old are my daughters" asks about the group, and `_named_person` answers with the
        # word the store files one of them under. The store keeps both ("daughters" with the ages
        # 4 and 7, and "daughter" at 4), so this reader answered with one of the two in the wrong
        # number. `_ages_reply` says every age the chat was given for the word they used.
        return None
    known = None
    for entry in others(memory):
        if who and entry.get("who") == who:
            known = entry
            break
        if not who and _same_name_however_they_wrote_it(entry, low):
            # "how old is janet" names the person the store knows by name, whether or not it
            # holds the thing asked for: what it does hold is said back below. The answer uses
            # their name, because "how old is sam" asking after "my kids are ada 7 and sam 4" is
            # a line about sam, and "Your kids is 4" is about nobody.
            known = entry
            by_name = entry.get("name") or ""
            who = entry.get("who") or ""
            break
    if (known is None and not who and property_ == "age" and
            re.search(r"\b(?:they|them)\b", low)):
        # "how old are they" is every person the chat has an age for, not one of them: the
        # pronoun is plural, and the single-person reader below would take the first person
        # whose gender pattern happens to fit "they" (the son, not the daughter). `_ages_reply`
        # answers the plural with all the ages, so this turn is left to it.
        return None
    if known is None and not who and re.search(r"\b(?:she|he|her|his|they|them)\b", low):
        # "how old is she" after "my mum is 72" is the mum: the last person the store heard
        # about is the one a pronoun points at. A pronoun only points at a person it fits, so
        # "my son is called Ada" then "what's her name" is not the son.
        she = re.search(r"\b(?:she|her)\b", low) is not None
        fits = extract.SHE if she else extract.HE
        for entry in reversed(others(memory)):
            has_fact = entry.get(property_) or (property_ == "age" and entry.get("months"))
            if has_fact and _pronoun_fits(entry.get("who") or "", fits):
                known = entry
                who = entry.get("who") or ""
                break
    if known is None and not who and re.search(r"\b(?:she|he|her|his)\b", low):
        # The pronoun fits nobody the store holds: "my daughter is 3" then "how old is he".
        # Answering about the daughter anyway puts the fact on the wrong person, and a search
        # hedge says nothing at all. When exactly one person holds this fact, the honest reply
        # offers that person as a question: "Did you mean your daughter? She is 3."
        held = [entry for entry in others(memory) if isinstance(entry, dict)
                and (entry.get(property_) or (property_ == "age" and entry.get("months")))]
        if len(held) == 1:
            offered = _did_you_mean(held[0], property_, _ask_gender(low))
            if offered:
                return offered
    if known is None and who:
        # A pair given in one breath ("my mum and dad are dave and sue") is kept whole, because
        # the line does not say which name is whose. So the answer says what was said and asks
        # for the one thing that settles it: guessing would file a fact about their mother they
        # never gave, and denying it would throw away something they did say.
        for entry in others(memory):
            words = [w.strip() for w in str(entry.get("who") or "").split(" and ")]
            names = entry.get("names") or []
            grouped = _relations_of(entry.get("who"))
            if (len(names) > 1 and (who in words or _canon_relation(who) in grouped)):
                return ("You told me your " + str(entry["who"]) + " are "
                        + _a_list_of_names(names) + " - which one is your "
                        + who + "?")
    if known is None and wants_name and who:
        # An everyday memory question deserves the honest answer, not a shrug: "whats my mums
        # name" with no name ever told is the store saying it does not hold one yet, the way it
        # already does for an age and for a pet. A pronoun ask with nobody named stays free,
        # because "what's her name" can be about someone in the room.
        return "You haven't told me a name for your " + who + " yet."
    if known is not None and not known.get(property_) and property_ == "age" and known.get("name"):
        # They told us who she is but not how old she is: "how old is janet" after "my mum is
        # called janet" is answered with what the store has, not with a search.
        pronoun = _pronoun_for(who, known)
        # A person whose word does not say whether they are a she or a he is a "they", and a
        # "they" takes "are": "but you haven't told me how old they is" is not a sentence.
        return ("Your " + who + " is called " + _called(str(known["name"]))
                + ", but you haven't told me how old " + pronoun
                + (" are." if pronoun == "they" else " is."))
    if property_ == "age" and known and known.get("months") and not known.get("age"):
        # A baby's age was said in months ("my son is 18 months old"), so it is said back in
        # months. Treating it as eighteen years is wrong, and denying it after the bot already
        # said it is a contradiction in the same chat.
        pronoun = str(known.get("pronoun") or "")
        if who:
            name = "Your " + who
            plural = who.endswith("s")
        else:
            # An age the chat only ever said with a pronoun ("shes 4 months"): the pronoun is the
            # name, and "They is 4 months old" is not a sentence.
            name = {"she": "She", "he": "He"}.get(pronoun, "They")
            plural = pronoun in ("", "they")
        return name + (" are " if plural else " is ") + str(known["months"]) + " months old."
    if known is None or not known.get(property_):
        return None
    said = _called(str(known[property_])) if property_ == "name" else str(known[property_])
    if not who:
        return ("Their " if re.search(r"\bthey\b", low) else "That's ") + said + "."
    if known.get("name") and (by_name or _same_name(str(known["name"]), low)):
        # The ask named the person by their own name, so the answer is about that person and not
        # about the word they were filed under: "how old is ada" after "my kid is ada 7" is
        # "Ada is 7.", never "Your kid is 7." - the person asked about Ada, and a friend who
        # knows her name uses it. This covers a group word too ("how old is sam" after "my kids
        # are ada 7 and sam 4"), where the word could not be one person's at all.
        named_one = _called(str(known["name"]))
        return (named_one + (" is called " if property_ == "name" else " is ") + said + ".")
    # A word for more than one person takes "are": "how old are my kids" is about the children,
    # and "Your kids is 4" is not said by anybody.
    mine = "Your " + who + " " + ("are " if _more_than_one(who) else "is ")
    if property_ == "name":
        return mine + "called " + said + "."
    if known.get("turns"):
        # An age still to come ("she's 4 next month") is said as a birthday, the way `_ages_reply`
        # already says it for everyone the chat holds. Saying "Your daughter is 4" a year early
        # contradicts the line the person just gave.
        return _one_age(who, known["age"], str(known["turns"]), known.get("to_come"))
    return mine + said + "."


def _pronoun_for(who, known=None):
    """The pronoun a person takes: "she", "he" or "they".

    Most words say it ("mum" is a she, "son" is a he). A role can be held by anybody - a landlord,
    a tutor, a boss - and the store had them as both, so the first test won and a landlord called
    Mr Smith was answered as a "she". A title is evidence and wins over the word: Mr is a he.
    """
    name = str((known or {}).get("name") or "")
    title = name.split(" ")[0].strip(".").lower() if " " in name or name else ""
    if title in extract.TITLE_GENDER:
        return extract.TITLE_GENDER[title]
    if who in extract.SHE and who not in extract.HE:
        return "she"
    if who in extract.HE and who not in extract.SHE:
        return "he"
    return "they"


def _the_group_word(who):
    """The group word the person used, in the spelling the answer can say out loud.

    "childrens" is a slip for "children" and the possessive is the same ask ("what are my
    childrens names"), so the word that matched is the one the answer uses, never their typo.
    """
    who = str(who or "").lower()
    for word in (who, who[:-2] if who.endswith("es") else "", who[:-1] if who.endswith("s") else "",
                 CHILD_OF.get(who, ""), who + "s"):
        if word and word in PERSON_GROUP:
            return word
    return ""


def _the_group_was_said(who, memory):
    """Whether any of the person's own lines named this group, in any spelling of it.

    A group the store holds nothing for is either one nobody mentioned ("what are my parents
    called" in a chat that never spoke of them) or one named in a line the readers could not
    file ("my kids are called tom and sam"). Only the first may be answered "you haven't told
    me": the second would deny the line before it.
    """
    word = _the_group_word(who)
    if not word:
        return False
    forms = {word, word + "s", word + "es", CHILD_OF.get(word, "")}
    forms = {one for one in forms if one and len(one) > 2}
    for turn in (memory or {}).get("turns") or []:
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "").lower()
        if any(re.search(r"(?<![a-z])" + re.escape(one) + r"(?![a-z])", said) for one in forms):
            return True
    return False


def _ages_reply(memory, low, text=""):
    """How old a person they told us about is, said back: "Your son is 7."

    Their ages are filed with the person ("my son is 7", "my mum is 68"), so the ask is about
    what the chat has been told, not about the world. A form of words the store has no pattern
    for still reaches this: "how old is the little one" is answered when a child was the last
    person named, and an honest "you haven't told me" comes back when no age was ever given.
    """
    if not isinstance(low, str):
        return None
    # "and my dad" after "what do you know about my mum" is that ask about another person, not
    # the age question: the store knows a number about the mum, not the age of the dad.
    if _continues_an_about_ask(memory, low):
        return None
    if not (AGE_ASK.search(low) or AGE_WORD.search(low)):
        # "and my daughter?" is only an ask about an age when it follows one: on its own it is a
        # name, not a question, and the store must not answer a question nobody asked.
        said = str(text or low).strip().rstrip("?.!").lower()
        if not (_just_gave_an_age(memory) and AGE_AGAIN.match(said)):
            return None
    # An age named as the reason for something is not a request for the number.
    if AGE_AS_A_CAUSE.search(low) and not AGE_ASK.search(low):
        return None
    # An age a rule turns on is not an age of theirs: the person has to be what the ask asks.
    if AGE_ASK.search(low) and not _age_is_about_a_person(low, memory):
        return None
    # "is that normal for his age" is not the ask "how old is he": the age is the measure the
    # question turns on, and saying the number back answers a different question. The modules
    # that know what is usual for an age answer it; the store keeps to the age it was asked for.
    if (not AGE_ASK.search(low)
            and re.search(r"\b(?:normal|typical|usual|common|expected)\b", low)
            and any(isinstance(entry.get("age"), int) or isinstance(entry.get("months"), int)
                    or entry.get("ages") for entry in others(memory))):
        # Only when the store does hold an age: with none of file, "you haven't told me how old
        # your nan is" is the honest answer and the right prompt, not a question dodged.
        return None
    told = []
    for entry in others(memory):
        who_said = str(entry.get("who") or "")
        turns = str(entry.get("turns") or "")
        # A child named as well as aged is said back by their name: "Ada is 7", not "your kids is
        # 7". The name rides along with the age so the answer can use it wherever it got there,
        # beside the birthday still to come, which is the other thing an age can arrive with.
        held = str(entry.get("name") or "")
        to_come = entry.get("to_come")
        if isinstance(entry.get("age"), int):
            told.append((who_said, entry["age"], turns,
                         to_come if isinstance(to_come, int) else None, held))
        # The children said as a group keep a list of ages ("my kids are 4 and 7"), so each of
        # them is an age the chat was given, said back in the order they were told.
        for age in entry.get("ages") or []:
            if isinstance(age, int):
                told.append((who_said, age, turns, None, ""))
        # A baby's age is kept in months, and it is an age of theirs like any other: "my daughter
        # is 4 months old" then "what did i say her age was" said she had never told. The figure
        # carries its unit into the answer, because "4" alone would read as four years.
        months = entry.get("months")
        if isinstance(months, int):
            told.append((who_said, str(months) + " months", turns, None, held))
    # The plural names the same person ("how old are my sons" is the son filed above); a possessive
    # in front of another noun is not the person at all.
    if not _named_person(low, memory):
        # A child named by their place in the family, which the store files under other words.
        placed = _the_place_word_filed(memory, low)
        if placed:
            return placed
    who = _named_person(low, memory)
    # The ask's own word decides the number. `_named_person` answers with the word the store files
    # the person under ("daughter"), so "how old are my daughters" came back as "Your daughter is
    # 4." - one of the two, in the wrong number.
    asked_plural = bool(who) and (who.endswith("s")
                                  or bool(re.search(r"\b" + re.escape(who) + r"s\b", low)))
    group = GROUP_ASK.search(low)
    if group:
        # "how old are my parents" is about the family the line names, not about one member of it:
        # the answer says every age the store holds for that family, in the words the chat used.
        word = group.group(1).lower()
        # The word they used and the word the chat used are the same family: "my children are 4,
        # 7 and 9" is filed under "children", and "how old are the kids" asks about that entry.
        # The group word the line itself said is in the store exactly as it was said ("my parents
        # are 66 and 70" is one reading of two people), so the word they used matches it directly
        # - without that, "how old are my parents" was answered "You haven't told me how old your
        # parents are" one line after the store had said both ages back.
        members = [entry for entry in told
                   if entry[0].split()[0] in FAMILY_GROUP[word]
                   or entry[0].split()[0] == word
                   or CHILD_OF.get(entry[0].split()[0]) in FAMILY_GROUP[word]]
        if members:
            return _ages_sentence(members)
        if word in ("kids", "children") and not told:
            return "You haven't told me how old they are."
        return "You haven't told me how old your " + word + " are."
    if not who and THE_KIDS.search(low):
        children = [entry for entry in told
                    if CHILD_OF.get(entry[0], entry[0].rstrip("s")) in CHILD]
        if CHILD_WORD.search(low):
            # "my kids", "the children": the people who are children, not everyone the chat knows.
            # The word wins over the person named last: after "my sister is 29", "the ages of my
            # kids" asks about the children, and an answer about the sister is an answer about
            # somebody the line did not name. With no child's age on file the honest line is that,
            # never somebody else's age.
            if not children:
                return "You haven't told me how old they are."
            return _ages_sentence(children)
        # "they", "them", "their", "both", "everyone": the ages in front of the chat, children
        # first, and whatever person it does know when there are no children in it.
        told = children or told
        if not told and not re.search(r"\b(?:kids?|children|child|family)\b", low):
            # "how old are they" straight after "my dog is 5 and my cat is 12" is about the
            # animals: answering that we were never told denies two facts just given.
            ages = _pet_ages(memory)
            if ages:
                return _pet_ages_sentence(ages)
        if not told:
            theirs = memory.get("their_age")
            if isinstance(theirs, dict) and theirs.get("age"):
                # An age the line gave for "they" and never for anybody named: "theyre 12" then
                # "how old are they" is the one age the chat has for them.
                return _one_age("", theirs["age"], theirs.get("turns") or "")
            return "You haven't told me how old they are."
        return _ages_sentence(told)
    if not who and re.search(r"\b(?:she|her|hers|he|him|his)\b", low):
        who = _person_from_pronoun(low, memory)
        if not who:
            # An age the chat keeps against the pronoun itself ("hes 8 next month", said after a
            # line about somebody else): there is no name to look up and the pronoun is who the
            # store was given, so the honest answer is that person's, not "I don't know".
            pronoun = "she" if re.search(r"\b(?:she|her)\b", low) else "he"
            for entry in others(memory):
                if str(entry.get("pronoun") or "") != pronoun:
                    continue
                age = entry.get("age")
                months = entry.get("months")
                if not isinstance(age, int) and not isinstance(months, int):
                    continue
                if isinstance(months, int):
                    # "shes 4 months" is said back in months: "4" alone would read as four years.
                    return ("He is " if pronoun == "he" else "She is ") + str(months) + " months."
                when = str(entry.get("turns") or "")
                he = pronoun == "he"
                if when:
                    return ("He turns " if he else "She turns ") + str(age) + " " + when + "."
                return ("He is " if he else "She is ") + str(age) + "."
    if not who:
        # An animal they told us about has an age the chat holds the same way: "how old is my
        # dog", "how old is max". Without this "how old is my cat" was answered with advice
        # about older cats, which is a confident answer to a question nobody asked.
        pet = _pet_age_reply(memory, low)
        if pet:
            return pet
        # Nothing in the line says whose age: "how old is the earth" is a question about the
        # world, and the modules that know about the world answer it, not this one.
        return None
    # A child named in the line is the person the ask is about, and their age is the one filed
    # with their name: "how old is sam" is Sam's age, not the age of the children as a group.
    for who_said, age, turns, to_come, held in told:
        if held and re.search(r"\b" + re.escape(held.lower()) + r"\b", low):
            return _one_age(who, age, turns, to_come, held)
    # A plural ask is about the group, not the one person the store filed under the same word:
    # "my daughters are 4 and 7" is kept as the group ("daughters", ages 4 and 7), and "how old
    # are my daughters" answered "Your daughter is 4." - half the fact, in the wrong number. Every
    # age the store holds for that word is said, in the order they were given.
    if asked_plural:
        word = who if who.endswith("s") else who + "s"
        family = [age for age in told if age[0].split()[0] == word]
        if len(family) > 1:
            return _ages_sentence(family)
    for who_said, age, turns, to_come, held in told:
        if who_said == who or (who.endswith("s") and who_said == who[:-1]):
            return _one_age(who, age, turns, to_come, held)
    # The store keeps a plural word for the people a plural line named as one group ("my brothers
    # are 20 and 24" is one reading of two people), so a singular ask with that word in it is
    # about the same people: "how old is my brother" said "You haven't told me how old your
    # brother is" about an age the chat had just been given. Every age held for the group is
    # said, in the words the person used, because which of the two they meant is not in the line.
    family = [one for one in told
              if one[0].split()[0] in (who + "s", _IRREGULAR_PLURAL.get(who, who + "s"))]
    if family:
        return _ages_sentence(family)
    # A person was named, so the answer is about them and nobody else: someone else's age is not
    # an answer to "how old is my mum", and it would be worse than saying we do not know.
    return "You haven't told me how old your " + who + (" are." if who.endswith("s") else " is.")


# The words for a child's place in the family are not one word each: "the little one", "the baby"
# and "the youngest" name the same child, and so do "the eldest" and "the oldest". Asked in a word
# the store holds nothing under, the answer was a shrug - or, worse, advice about the world - about
# a child the chat had been told an age for one line before. So a place word in the ask is read as
# the person on file at the same end of the family, and only when exactly one of them is there.
_THE_YOUNGER_END = frozenset(("youngest", "littlest", "baby", "toddler", "newborn", "little one",
                              "wee one", "little lad", "little girl", "little boy", "small one",
                              "younger one"))
_THE_OLDER_END = frozenset(("eldest", "oldest", "elder", "big one", "older one", "biggest"))
_A_PLACE_ASK = re.compile(
    r"\b(?:the|my|our|your)\s+(?P<who>"
    + "|".join(sorted(_THE_YOUNGER_END | _THE_OLDER_END, key=len, reverse=True)) + r")\b", re.I)


# The words that can follow a place word and leave it naming a person: the end of the line, the
# punctuation, or one of the little words a spoken line puts after it ("the little one now", "the
# eldest though"). Anything else is a noun - "the oldest person in the world", "the baby food" -
# and the place word there is an adjective, not somebody's place in the family.
_THE_PLACE_STANDS_ALONE = frozenset((
    "now", "then", "there", "too", "though", "anyway", "please", "is", "was", "were", "are",
    "again", "still", "yet", "today", "nowadays", "here", "of", "in", "at", "on", "and", "or",
    "got", "has", "have", "had", "will", "would", "should", "can", "could", "might", "must",
    "turns", "turned", "just", "only", "already", "actually", "really"))


def _the_place_end(low):
    """"young", "old" or "" - the end of the family the ask's place word names, and the word.

    The place word has to be the whole of the noun phrase, so an adjective use ("the oldest
    person in the world", "the little dog") is not somebody's place in their family.
    """
    asked = _A_PLACE_ASK.search(str(low or ""))
    if not asked:
        return "", ""
    after = str(low)[asked.end():]
    after = re.split(r"[.,;:!?]", after, maxsplit=1)[0].strip()
    next_word = after.split()[0].lower() if after else ""
    if next_word and next_word not in _THE_PLACE_STANDS_ALONE:
        return "", ""
    word = " ".join(asked.group("who").lower().split())
    return ("young" if word in _THE_YOUNGER_END else "old"), word


def _the_child_ages_on_file(memory):
    """The ages the chat holds for children of theirs, oldest first as (word, age, turns)."""
    found = []
    for entry in others(memory):
        if not isinstance(entry, dict):
            continue
        who = str(entry.get("who") or "").lower()
        if CHILD_OF.get(who, who.rstrip("s")) not in CHILD and who not in CHILD:
            continue
        turns = str(entry.get("turns") or "")
        if isinstance(entry.get("age"), int):
            found.append((who, entry["age"], turns))
        for age in entry.get("ages") or []:
            if isinstance(age, int):
                found.append((who, age, turns))
    return found


def _the_place_word_filed(memory, low):
    """How old the child at the end of the family the ask names is, or "" when that end is empty.

    A child named by their place is the same child however the place is said: "the little one",
    "the baby" and "the youngest" are one end of the family, "the eldest" and "the oldest" the
    other. Asked in a word the store has nothing filed under, the answer used to be a shrug - and
    usually advice about the world, which is a confident answer to a question nobody asked - about
    a child the chat had been told an age for one line before. So the end the ask names is read
    against every age on file for a child of theirs, and the youngest or the eldest of them is the
    answer. With no age at that end, the honest line is that the chat was never told.
    """
    end, word = _the_place_end(low)
    if not end:
        return ""
    if not word:
        return ""
    ages = _the_child_ages_on_file(memory)
    if not ages:
        return ""
    ages.sort(key=lambda one: one[1])
    who, age, turns = ages[0] if end == "young" else ages[-1]
    if age in [one[1] for one in ages[:-1] if end == "old"]:
        return ""
    return _one_age(word, age, turns)


PET_ASK = re.compile(r"\b(?:my|our|the)\s+(" + PET_WORDS + r")s?\b", re.I)


BREED_ASK = re.compile(r"\b(?:my|our|the)\s+(?:" + breeds.BREED_RE.pattern + r")\b", re.I)


_PET_WORD = re.compile(r"\b(?:" + PET_WORDS + r")s?\b|" + breeds.BREED_RE.pattern, re.I)


def _pet_ages(memory):
    """The animals the store holds an age for."""
    return [pet for pet in (user(memory).get("pets") or [])
            if isinstance(pet, dict) and isinstance(pet.get("age"), int)]


def the_pronoun_said_with_a_name(memory, age):
    """The age a pronoun answer is about, said with the animal's name, or None.

    A pronoun is never a name. "we rehomed a greyhound in march" / "shes two" / "what age is she
    again" was answered "She is 2.", which would fit any animal in any chat and gave back only the
    words the person had just typed. The one rule, for every animal and every way of asking, is:
    the age the store holds for the animal it has been told about is said with that animal in it
    ("Your greyhound is 2.").

    The name has to be earned, not guessed. A pronoun in a chat with two animals is the reason the
    guess goes wrong - a rabbit's "hes one" answered "Max is 4." - so the animal is only named when
    the age about to be said is the age the store filed for it, and for exactly one animal. When
    nothing matches, there is no name to give and the pronoun path keeps the line it had, because
    a pronoun is the right answer when the chat holds nothing to name.
    """
    if not isinstance(age, int):
        return None
    aged = [pet for pet in _pet_ages(memory) if pet.get("age") == age]
    if len(aged) != 1:
        return None
    return _pet_ages_sentence([aged[0]])


def _pet_age_reply(memory, low):
    """How old an animal they told us about is: "Max is 4.", "Your dog is 5."

    The age is filed with the animal ("my dog is 5", "my dog max is 4"), so the ask is about the
    chat, not the world. When no age was ever given the store says so about that animal rather
    than guessing or searching: the person can see from their own dog that the guess is wrong.
    """
    pets = [pet for pet in (user(memory).get("pets") or []) if isinstance(pet, dict)]
    asked = []
    animal = PET_ASK.search(low)
    family = _animal_family(animal.group(1)) if animal else ""
    if not family:
        breed = BREED_ASK.search(low)
        if breed:
            family = _animal_family(breeds.the_kind_of(breed.group(0).split()[-1]))
    if family:
        asked = [pet for pet in pets if _animal_family(pet.get("animal")) == family]
        if not asked:
            # The line says the animal is theirs, so the world is not the place to look: the
            # honest answer is that the chat has not been told about one, not advice on cats in
            # general, which answers a question they did not ask.
            return ("You haven't told me about "
                    + ("an" if family[:1] in "aeiou" else "a") + " " + family + ".")
    else:
        for pet in reversed(pets):
            name = str(pet.get("name") or "").strip()
            if len(name) > 2 and re.search(r"\b" + re.escape(name.lower()) + r"\b", low):
                asked.append(pet)
    if not asked and re.search(r"\b(?:she|he|it|they|his|her|its|their)\b", low):
        # "how old is she" is about the one animal the chat holds an age for, and the pronoun is
        # the only thing that says which animal is meant. With more than one, the age has to have
        # been said in the reply right before ("Noted: your dog max is 4" then "how old is he").
        aged = _pet_ages(memory)
        if aged:
            asked = aged
    if not asked:
        return None
    aged = [pet for pet in asked if isinstance(pet.get("age"), int)]
    if not aged:
        family = _animal_family(asked[0].get("animal"))
        if len(asked) > 1 or int(asked[0].get("count") or 1) > 1:
            return "You haven't told me how old your " + family + "s are."
        return "You haven't told me how old " + _pet_named(asked[0]) + " is."
    said = _pet_ages_sentence(aged)
    if _same_as_last(said, memory):
        # "how old is my cat" right after "how old is she" is the same age: say it short, so the
        # turn is not the sentence they just got back.
        return "Still " + " and ".join(_a_pet_age(pet) for pet in aged[:4]) + "."
    return said


PLURAL_ANIMAL = re.compile(r"s$", re.I)


def _pet_named(pet):
    """How to name one animal: by the name they gave it ("Max"), or by what they call it."""
    name = str(pet.get("name") or "").strip()
    if name:
        return _tidy_name(name)
    animal = str(pet.get("breed") or pet.get("animal") or "").strip()
    if animal and not PLURAL_ANIMAL.search(animal):
        return "your " + animal
    return "your " + _animal_family(animal)


def _a_pet_age(pet):
    """The age as it was given: "5", "4 months old"."""
    unit = str(pet.get("unit") or "")
    return str(pet["age"]) + ((" " + unit + " old") if unit else "")


def _pet_ages_sentence(pets):
    """Every age the chat was given for these animals, said back as one sentence."""
    parts = []
    for pet in pets[:4]:
        who = _pet_named(pet)
        verb = " are " if who.startswith("your ") and who.endswith("s") else " is "
        parts.append(who + verb + _a_pet_age(pet))
    said = parts[0]
    for part in parts[1:]:
        said += " and " + part
    return said[0].upper() + said[1:] + "."


def _one_age(who, age, turns="", to_come=None, held=""):
    """One person's age, said back: a birthday still to come is said as one.

    With both numbers on file the answer is both, because either alone is half of it: "Your son is
    7, and turns 8 in june." Saying only the birthday leaves them guessing how old he is now, and
    saying only the age contradicts the birthday they just gave.

    A person with a name of their own is said by the name the person gave ("Ada is 7"): the word
    in front of them ("your kids") is the group they came in, not who they are.
    """
    if held:
        name = str(held)[:1].upper() + str(held)[1:]
    elif who in PRONOUN_PEOPLE:
        # A person the chat only pointed at: the pronoun is the name ("She turns 5 next month.")
        name = who
    else:
        # One person keeps the word they came in: this reader says one age of one person, and a
        # word made plural here gets a singular verb beside it ("Your daughters is 5."), which is
        # worse than main. The plural belongs to `_ages_sentence`, where two ages of one word are
        # one group.
        name = ("your " + who) if who else "they"
    # A child said by their own name is one person, whatever group word they arrived in: "Ada is
    # 7", never "Ada are 7".
    plural = not held and (who.endswith("s") or not who or who in ("they", "them"))
    if turns and isinstance(to_come, int) and to_come != age:
        said = name + (" are " if plural else " is ") + str(age) + ", and turns " + str(to_come) \
            + " " + turns
    elif turns:
        said = name + (" turn " if plural else " turns ") + str(age) + " " + turns
    else:
        said = name + (" are " if plural else " is ") + str(age)
    return said[0].upper() + said[1:] + "."


def _just_gave_an_age(memory):
    """True when the bot's last reply was an age it said back ("Your son is 7.")."""
    return bool(AGE_SAID.search(str(last_bot(memory) or "").strip()))


# The word for them said as more than one: "your daughters are 4 and 2", never "your daughter are
# 4 and 2". Two children said under one word are two children, and the sentence has to say so.
MANY_OF_THEM = {"child": "children", "grandchild": "grandchildren", "baby": "babies",
                "person": "people", "woman": "women", "man": "men"}
# A word that is already the group: "my children are 6 and 3" is not "your childrens are".
ALREADY_MANY = frozenset(MANY_OF_THEM.values())


def _the_many(who):
    """The word for the group of them, in the shape the sentence needs ("daughter" ->
    "daughters")."""
    word = str(who or "").strip().lower()
    if not word:
        return ""
    if word in MANY_OF_THEM:
        return MANY_OF_THEM[word]
    if word in ALREADY_MANY or word.endswith("s"):
        return word
    if word.endswith("y") and word[-2:-1] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


def _ages_sentence(told):
    """Every age the chat has been given, as one sentence, oldest fact first.

    Ages given for the same word are said once, in the order they were told ("your kids are 4 and
    7"): the person said them as one group and the answer is one group too.
    """
    groups = []
    for who, age, turns, to_come, held in told[:4]:
        for group in groups:
            if group[0] == who and group[4] == held and not group[2] and not turns:
                group[1].append(age)
                break
        else:
            groups.append([who, [age], turns, to_come, held])
    parts = []
    for who, ages, turns, to_come, held in groups:
        if len(ages) == 1:
            parts.append(_one_age(who, ages[0], turns, to_come, held).rstrip("."))
            continue
        name = ("your " + _the_many(who)) if who else "they"
        said = ", ".join(str(age) for age in ages[:-1])
        parts.append(name + " are " + said + " and " + str(ages[-1]))
    # A part that starts with a name keeps its capital: "Ada is 7 and Sam is 4", never "and sam".
    parts = parts[:1] + [(part[:1].lower() + part[1:]) if not any(
        group[4] and part.startswith(str(group[4])[:1].upper()) for group in groups)
        else part for part in parts[1:]]
    if len(parts) == 1:
        return (parts[0][0].upper() + parts[0][1:]) + "."
    said = ", ".join(parts[:-1]) + " and " + parts[-1]
    return said[0].upper() + said[1:] + "."


def _ask_gender(low):
    """The gender the line's own pronoun names, or "" when it names none."""
    if re.search(r"\b(?:she|her|hers)\b", str(low or "")):
        return "she"
    if re.search(r"\b(?:he|him|his)\b", str(low or "")):
        return "he"
    return ""


def _called(name):
    """A name as it is written back: "biscuit" reads "Biscuit", "mr patel" reads "Mr Patel"."""
    if not isinstance(name, str) or not name:
        return ""
    words = name.replace(".", " ").split()
    if not words:
        return ""
    if len(words) > 1:
        # A title and a name are two words, and both are written the way a name is written.
        return " ".join(word[0].upper() + word[1:] for word in words)
    return words[0][0].upper() + words[0][1:]


def _every_line(memory):
    """Every line the person has said, oldest first.

    A named thing is looked for in all of them: "do you remember what i said about the cat" is
    asked after ten turns of other subjects as often as after two, and "you haven't mentioned
    the cat" about a thing they did say is worse than no answer at all. The short window in
    `recent` stays for the pronoun asks ("what did i say about it"), where the nearest line
    really is the subject of the chat.
    """
    if not isinstance(memory, dict):
        return []
    return [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
