"""A question about a person the chat already holds: answer it with what the chat holds.

    my mum is in hospital / she had a fall / she is 82 / how is she doing
        -> "Same as before: Falls are usually several small things adding up ..."

A friend asked how their mum was doing, and the bot read the word "doing" as the fall it had
already answered and said the same paragraph again, headed "Same as before". The person was not
asking for the advice twice; they were asking after their mum, and the only thing the bot knows
about her is what they told it.

So the reply is what the chat holds, said in one line: the person ("your mum"), what they said
about her ("had a fall"), her age if it was given, and the one thing a friend asks - whether
there is any word since. When the chat holds nobody, there is nothing to answer with and the
module stands down.
"""
import re

from . import facts, holds as earlier

# The ask about a person already on the table: "how is she doing", "how's he getting on", "how
# has she been", "is she any better".
THE_ASK = re.compile(
    r"^\s*(?:and\s+|so\s+|but\s+)?(?:"
    r"how(?:'s|\s+is|\s+are|\s+was|\s+were)\s+(?P<who>he|she|they|him|her|them)\s*"
    r"(?:doing|getting\s+on|going|coping|holding\s+up|been)?"
    r"|how\s+(?:has|have)\s+(?P<been>he|she|they)\s+been"
    r"|is\s+(?P<better>he|she|they)\s+(?:any\s+)?better"
    r")\s*(?:now|today|then|since|at\s+the\s+moment)?\s*\?*\s*$",
    re.I)
# The same ask with the person named instead of pointed at: "how is your mum", "how's mum doing",
# "any news about your mum".
THE_NAMED_ASK = re.compile(
    r"^\s*(?:and\s+|so\s+)?(?:"
    r"how(?:'s|\s+is|\s+was)\s+(?:your\s+|my\s+)?(?P<who>[a-z]{2,})"
    r"|any\s+news\s+(?:about|on|of)\s+(?:your\s+|my\s+)?(?P<news>[a-z]{2,})"
    r"|how\s+did\s+it\s+go\s+with\s+(?:your\s+|my\s+)?(?P<went>[a-z]{2,})"
    r")\s*(?:doing|getting\s+on|now|then|today)?\s*\?*\s*$",
    re.I)
# The words that are a person in a chat that holds one: "mum" is a relation, "better" is not.
THE_RELATIONS = frozenset(facts.RELATIONS) | frozenset(
    "mum mom mam mother dad father gran granny grandma grandad grandpa nan nana pops".split())
# A line that only gives their age: "she is 82", "mum turned 74". It is not the news, because
# the reply already says the age - the line before it is the news.
AN_AGE = re.compile(r"^(?:is|was|turned|is\s+now|just\s+turned)\s+\d{1,3}\b", re.I)
# The most words of the earlier line that can be said back as the news about them.
MOST_WORDS_OF_NEWS = 9


def _the_person_held(memory):
    """(relation, name, age) for the person the chat holds last, or None."""
    from . import others as the_others
    held = [one for one in (the_others(memory) or []) if isinstance(one, dict)]
    for one in reversed(held):
        relation = str(one.get("who") or "").strip().lower()
        if not relation:
            continue
        name = str(one.get("name") or "").strip()
        age = one.get("age")
        return relation, name, age
    # The store files a person when it has something to file - an age, a name, a job - and a
    # person the chat only mentioned in passing is still the person a "how is she doing" asks
    # after: "my mum is in hospital" leaves no `others` entry, and the ask after it was answered
    # by the hospital paragraph again. The relation the chat used is the fallback.
    named = []
    for line in earlier.lines(memory):
        for found in re.finditer(r"\b(?:my|our)\s+([a-z]{3,})\b", str(line).lower()):
            word = found.group(1)
            if word in THE_RELATIONS and word not in named:
                named.append(word)
    if len(named) == 1:
        return named[0], "", None
    if named:
        # More than one person has been mentioned, so a "she" could be either: only the last one
        # the chat named is a reading, and only when nothing else names a person after it.
        return named[-1], "", None
    return None


def _the_news_about(memory, relation, name):
    """What an earlier line said about them, with the person taken off the front.

    "she had a fall" becomes "had a fall", and "my mum is in hospital" becomes "is in hospital":
    both read on from "your mum", so the reply can say the one thing the chat holds without
    quoting the line back at them.
    """
    words = [relation] + ([name] if name else []) + list(_the_pronouns(relation))
    for line in reversed(earlier.lines(memory)):
        low = " ".join(str(line).lower().split())
        if "?" in low or not low:
            continue
        for word in words:
            found = re.search(r"\b(?:my|our|the)?\s*" + re.escape(word) + r"\b", low)
            if not found:
                continue
            rest = low[found.end():].strip(" ,.;:!-")
            if not rest or len(rest.split()) > MOST_WORDS_OF_NEWS:
                continue
            if AN_AGE.search(rest):
                # "she is 82" is the age, and the age is said by the reply already: the news is
                # the line before it, so keep reading back rather than say the number twice.
                continue
            if rest.split()[0] in ("is", "was", "had", "has", "have", "went", "got", "kept",
                                   "said", "wants", "wanted", "needs", "keeps", "lives",
                                   "does", "did", "came", "started", "turned", "seems"):
                return rest.rstrip(".")
    return ""


def _the_pronouns(relation):
    if relation in facts.HE:
        return ("he",)
    if relation in facts.SHE:
        return ("she",)
    return ("they",)


def _the_ask(text, memory):
    """(relation, name, age) for the person the line asks about, or None."""
    if not isinstance(memory, dict):
        return None
    said = " ".join(str(text or "").lower().split())
    match = THE_ASK.match(said)
    if match:
        held = _the_person_held(memory)
        if not held:
            return ""
        # "how are they doing" is only one person when the chat holds one person, and the reply
        # says "your mum" for a "they" that was a "her": the pronoun is the chat's, not theirs.
        pointed = match.group("who") or match.group("been") or match.group("better") or ""
        if pointed in ("he", "she"):
            wanted = "he" if pointed == "he" else "she"
            if _the_pronouns(held[0])[0] != wanted:
                return ""
        return held
    match = THE_NAMED_ASK.match(said)
    if match:
        word = (match.group("who") or match.group("news") or match.group("went") or "").strip()
        if word not in THE_RELATIONS:
            return ""
        held = _the_person_held(memory)
        if not held:
            return ""
        # "how is your mum" is about the mum the chat holds, and if it holds a dad instead the
        # ask is about somebody it has nothing on: stand down rather than answer about the dad.
        if held[0] not in (word, word.rstrip("s")):
            return ""
        return held
    return ""


# Where the news about them is a medical episode, "any news?" is not what the person needs: a
# stay in hospital is a day with things to ask the ward and things to take in, and the bot has
# those. This reading stands down so the answer about the stay keeps the turn - `my mum is in
# hospital` / `she had a fall` / `how is she doing` was handed "Your mum had a fall, you said.
# Any news since?" over the ward's three questions, and the ward's three questions are the help.
# Only a stay, an operation or a move into care: a fall at home, a first day at school and a new
# baby are news the chat alone holds, and there the callback is the answer.
IN_A_MEDICAL_EPISODE = re.compile(
    r"\b(?:hospital|hospitalis\w*|hospitaliz\w*|surgery|surgical|operation"
    r"|a&?e|casualty|intensive care|icu|coronary care|hospice|care home|nursing home"
    r"|the ward|on a ward|in a ward)\b", re.I)
# How far back a stay still colours the ask: the person says it once and asks after them for a
# few turns after.
EPISODE_TURNS = 6


def _a_medical_episode(memory):
    """Whether a turn the chat holds is a stay, an operation or a move into care."""
    for line in earlier.lines(memory)[-EPISODE_TURNS:]:
        if IN_A_MEDICAL_EPISODE.search(str(line)):
            return True
    return False


def reply_for(text, memory):
    """What the chat holds about the person the line asks after, or ""."""
    if not isinstance(memory, dict) or not earlier.there_is_one(memory):
        return ""
    if _a_medical_episode(memory) or IN_A_MEDICAL_EPISODE.search(str(text or "")):
        return ""
    held = _the_ask(text, memory)
    if not held:
        return ""
    relation, name, age = held
    who = name.capitalize() if name else "your " + relation
    news = _the_news_about(memory, relation, name)
    # "she is 82" is the age, which has a line of its own below: said as the news it reads
    # "your mum \u2014 you said is 82", which is the line said back at them with a word missing.
    if age and news and re.fullmatch(r"(?:is|was)\s+" + re.escape(str(age)) + r"(?:\s+years?\s+old)?", news):
        news = ""
    since = ("Any word since then?", "Any news since?", "Has there been any change?",
             "Anything new since?")
    if news:
        pool = ("You said {who} " + news + ". {since}",
                "Last you said, {who} " + news + ". {since}",
                "{who_cap} " + news + ", you said. {since}")
        return _choose([line.format(who=who, who_cap=who.capitalize(), since=ask)
                        for line in pool for ask in since], memory)
    if age:
        # The age is the one thing the chat holds, and the ask already asked how they are: the
        # reply says the age and asks something else, or it is the person's own question handed
        # back to them - "how is she doing" answered with "how is she getting on".
        # Every one of these names them: a reply that shares no word with the line is handed
        # over to a card beside it by the arbiter (`_a_card_that_names_the_line`), and the asks
        # here are all made of the relation or the pronoun - "how has she been" - so naming them
        # is also what keeps the turn on the person the chat holds. It is what a friend does with
        # somebody they have only heard the age of, too.
        pool = ("{who_cap} is " + str(age) + " - what has {pronoun} been saying?",
                "{who_cap} is " + str(age) + ", and that is all I have. What is {pronoun} up to "
                "at the moment?",
                "{who_cap} is " + str(age) + " - has {pronoun} been in touch?")
        return _choose([line.format(who_cap=who.capitalize(), pronoun=_the_pronouns(relation)[0])
                        for line in pool], memory)
    return ""


def claims(text, memory):
    """The lines this reading answers even when another module claims the turn as it comes.

    "how is she doing" is a claim of `answers` - it takes the follow-up as it comes and reads
    "doing" as the thing it last answered - so the module's own PRIORITY cannot take the turn.
    The claim is given up only to a module that says so itself (README.md, "Interface"), and this
    is the line where the chat holds the person being asked after.
    """
    return bool(reply_for(text, memory))


def _choose(pool, memory):
    """One line from the pool, not one this chat has already had.

    The lines are compared *as they would read*, not as they were built: the pool holds the
    skeleton with `{who}` and `{since}` in it, so a skeleton never matched a sentence the bot had
    already said and the whole pool counted as fresh. Two asks in a row about the same news then
    got the same sentence word for word - "Last you said, your mum had a fall on sunday. Any news
    since?" twice, which is the one thing a reply must never do.
    """
    import random
    said = earlier.the_bot_lines(memory)
    fresh = [line for line in pool if line not in said]
    return random.choice(fresh or list(pool))
