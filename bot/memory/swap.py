"""A follow-up that only names a new thing: the same question, with that thing in it.

"can you give me a dinner idea" ... "what about a dessert" is one question asked about two
things. The second line names no ask at all - just a thing and the words that say it is a
follow-up - so read on its own no entry fits it, and the bot shrugs ("I don't know enough to
answer that honestly") at a question it answers perfectly well when it is asked in full ("any
dessert ideas" gets a crumble). Said again as the earlier question with the earlier thing
swapped for the new one, it reaches the same entry.

Which word is swapped is read off the conversation rather than guessed: the earlier question's
own content word that the answer just given took up is the thing being talked about ("dinner"
in "can you give me a dinner idea", taken up by "Ten-minute dinners: ..."), and that is the
word the new line replaces.

Only a line that says nothing but "and X" / "what about X" is rewritten; a line with an ask of
its own, a pronoun ("what about it", "and that one") or a figure is left alone. The rewritten
line still has to reach an entry whose answer is about the new thing, which is the caller's
check: this module offers a reading, it does not answer.
"""
import re

# The whole line has to be a follow-up and a thing, and nothing else.
LEAD = re.compile(
    r"^\W*(?:(?:ok|okay|right|so|yes|yeah|and)\b[\s,]*)*"
    r"(?:(?:and|but|or)\s+)?"
    r"(?:(?:what|how)\s+about|what\s+of|and|also|plus)\b[\s,]*", re.I)
# A repair is the same follow-up the other way round: the person takes back the thing they named
# and puts another in its place. "no i mean brown rice" after "how long does it take to cook
# rice" is that question about brown rice, so the thing it names goes where the old one was. The
# look-back is the same one a "what about X" gets: the earlier question's own content word is
# what the new thing replaces.
REPAIR = re.compile(
    r"^\W*(?:(?:no|nope|sorry|apologies|actually|wait|hold on|oops)[\s,.!-]+)*"
    r"(?:i\s+(?:mean|meant|said)(?:\s+to\s+say)?|(?:you\s+)?mean|i\s+did\s+mean)"
    r"[\s,.!-]+", re.I)
# A take-back that names the new thing without the verb of correcting it: "no wait, a laptop",
# "or rather the freezer", "scratch that, pepper plants". Only a line that is the take-back and
# then the thing is read this way; "no, the wifi is down" and "hold on, it broke" are statements
# of their own, and what they say is not a thing to put in place of the last one.
TAKE_BACK = re.compile(
    r"^\W*(?:(?:no|nope|wait|hold on|or rather|scratch that|oops)[\s,.!-]+)+", re.I)
# Words that answer a question rather than name a thing of their own. "no thanks at all" reads as
# the take-back "no" with the thing "thanks at all", "no ta" as "ta" and "no worries" as
# "worries", so the answer they did not want was handed to them again under "The same goes for
# the thanks at all: ...". Nobody declines a thing by naming one, so a courtesy never swaps.
A_COURTESY = frozenset("""
    thanks thank thankyou ta cheers mate love hun pal duck fella sir madam
    worries worry anyway anyhow though please fine alright ok okay all much
    """.split())
# The words that make what follows a clause rather than a thing.
A_CLAUSE = re.compile(
    r"\b(?:is|are|was|were|isnt|arent|wasnt|werent|does|did|do|doesnt|didnt|dont|has|have|had"
    r"|hasnt|havent|hadnt|will|would|wont|wouldnt|can|cant|could|couldnt|should|shouldnt|must"
    r"|im|ive|id|ill|weve|youre|its|thats|theres)\b", re.I)


def _after_a_take_back(said):
    """What a line says after its "no wait", or None when the line is not a take-back and a thing.

    The rest has to be short and name no happening of its own, because the reading it is offered
    is the last question with this thing swapped in: "no wait, a laptop" after "i need a new
    phone" is that sentence about a laptop, while "no, the wifi is down" is news.
    """
    lead = TAKE_BACK.match(said)
    if not lead:
        return None
    rest = TAIL_OFF.sub("", said[lead.end():].strip(" ?!.,")).strip(" ?!.,")
    if not rest or len(rest.split()) > 3 or A_CLAUSE.search(rest):
        return None
    return rest


# A thing named after the follow-up words: an article and up to three ordinary words.
THING = re.compile(r"^(?:(?:a|an|the|some|any|another)\s+)?([a-z][a-z' -]{0,24})$", re.I)
# A thing names a thing; an ask opens with a word that asks something or with an auxiliary and
# the person it is about ("should i quit", "will it work"). Only that opening is refused, so a
# thing whose own words include an auxiliary keeps its swap: "no i mean a can of tomatoes" is
# still the tomatoes put in place of the mince.
ASKS_A_THING = re.compile(
    r"^(?:what|which|how|why|when|where|who|whose|whom)\b"
    r"|^(?:can|could|should|would|will|shall|do|does|did|is|are|was|were|have|has|had|am|may"
    r"|might|must|need)\s+(?:i|we|you|they|it|he|she)\b", re.I)
# "and in the freezer too" names a place, and the words that say so are part of it: the new thing
# goes where the old one was, with its own preposition - "the smell in the fridge" is asked again
# about "the smell in the freezer". The tail is the words that only say it is a follow-up.
TAIL_OFF = re.compile(r"[\s,]*(?:\b(?:too|as well|also|instead|then|now|though|please|thanks)\b"
                      r"[\s,.!?]*)+$", re.I)
# The word that says how sure they are about the thing is theirs, not part of its name. Left in,
# the frame that hands the earlier answer to the new thing says it out loud - "a labrador
# probably" after the dog question came back "The same goes for the labrador probably: ...", and
# "what about the freezer maybe" "The same goes for the freezer maybe: ..." - which is their
# hesitation in a noun slot. Only the tail is read, because "probably a labrador" is not how an
# answer gets handed to a thing in the first place.
HEDGE_OFF = re.compile(
    r"[\s,]*(?:\b(?:probably|maybe|perhaps|possibly|definitely|likely|obviously|actually|"
    r"really|sure|suppose|supposedly|hopefully|honestly|frankly)\b"
    r"|\b(?:i|we)\s+(?:think|guess|suppose|reckon|imagine|hope)\b"
    r"|\bof course\b|\bfor now\b|\bright\b|\bok(?:ay)?\b)[\s,.!?]*$", re.I)
# Words that point at something already said rather than naming a thing.
DEICTIC = frozenset((
    "it", "its", "it's", "that", "this", "them", "they", "those", "these", "him", "her",
    "one", "ones", "the same", "same", "the other", "rest", "more", "less", "instead",
    "then", "now", "there", "here", "you", "me", "us", "my", "your", "mine", "yours",
))
STOP = frozenset((
    "a", "an", "the", "and", "or", "but", "if", "of", "for", "to", "in", "on", "at", "with",
    "about", "as", "by", "from", "into", "over", "after", "before", "than", "then", "so",
    "i", "im", "i'm", "me", "my", "we", "you", "your", "it", "its", "is", "are", "was",
    "were", "be", "am", "do", "does", "did", "done", "can", "could", "should", "would",
    "will", "shall", "may", "might", "must", "have", "has", "had", "get", "got", "give",
    "make", "much", "many", "long", "how", "what", "when", "where", "which", "who", "why",
    "any", "some", "good", "best", "better", "more", "most", "not", "no", "yes", "please",
    "there", "here", "that", "this", "these", "those", "them", "they", "he", "she", "his",
    "her", "him", "want", "need", "like", "one", "also", "just", "really", "very", "know",
    "tell", "think", "say", "said", "help", "idea", "ideas", "thing", "things", "anything",
    "something", "way", "ways", "time", "times", "kind", "kinds", "sort", "sorts",
))
OPENERS = ("how", "what", "when", "where", "which", "who", "why", "can", "could", "should",
           "would", "do", "does", "did", "is", "are", "was", "were", "will", "shall")
# The asking words with the apostrophe taken out ("whats the capital of australia"). They are the
# ask, not the thing asked about, so a swap never lands on one of them.
ASK = frozenset(("whats", "hows", "wheres", "whos", "whys", "whens", "whatre", "hows"))


def _said(text):
    return " ".join(str(text or "").lower().split())


def _stem(word):
    word = word.strip("?.!,;:")
    for end in ("ies", "es", "s"):
        if len(word) > 4 and word.endswith(end):
            return word[: -len(end)]
    return word


def thing(text):
    """The new thing a follow-up names, or None: "what about a dessert" -> "dessert"."""
    said = _said(text).strip(" ?!.")
    if not said:
        return None
    lead = LEAD.match(said)
    repaired = False
    if lead:
        rest = said[lead.end():]
    else:
        lead = REPAIR.match(said)
        if lead:
            rest = said[lead.end():]
            repaired = True
        else:
            rest = _after_a_take_back(said)
            if rest is None:
                return None
    # A repair puts another *thing* where the last one was, and a thing is not a clause. "i hate my
    # job" then "no i mean should i quit" is the question they meant, said plainer, not a new
    # subject: read as a thing it swapped "job" for "should i quit" - "i hate my should i quit" -
    # which the strict-teacher row reached on the word "hate" and answered a question about
    # quitting with a lesson plan. So the take-back path keeps a sentence out, by the same test
    # `_after_a_take_back` already makes.
    if repaired and A_CLAUSE.search(rest):
        return None
    # "and in the freezer too" / "what about the freezer as well": the words after the thing only
    # say it is a follow-up, and the words in front only say it is one too.
    rest = TAIL_OFF.sub("", rest.strip(" ?!.,")).strip(" ?!.,")
    # And the hesitation comes off before the name is read: "a labrador probably" names the
    # labrador, and the "probably" is the person being unsure, which the reply has no slot for.
    for _ in range(3):
        hedged = HEDGE_OFF.sub("", rest).strip(" ?!.,")
        if hedged == rest:
            break
        rest = hedged
    if not rest or len(rest.split()) > 4:
        return None
    found = THING.match(rest)
    if not found:
        return None
    name = found.group(1).strip()
    words = [word for word in re.split(r"[ ']", name) if word]
    if len(words) > 1 and words[0] in OWNER_WORDS:
        # "what about my hip" names the hip: the possessive says whose it is, not which one is
        # meant, and the earlier line already says whose. Left in, "my" makes the thing a
        # pointing word and the follow-up names nothing at all.
        words = words[1:]
        name = " ".join(words)
    if not words or len(words) > 3:
        return None
    if name in DEICTIC or " ".join(words) in DEICTIC:
        return None
    # "what about it" and "and the same again" point back; "what about a dessert" names a thing.
    if any(word in DEICTIC for word in words):
        return None
    # An ask is not a thing. "no i mean should i quit" is the question they meant to ask, and put
    # in place of the last thing named it builds a line nobody wrote - after "i hate my job" it
    # was "i hate my should i quit", which is not English and reached the row about a strict
    # teacher, so a person who hates their job got advice about a lesson. The same shape as a
    # take-back, which already refuses a clause; the correction readers answer the ask itself.
    if ASKS_A_THING.search(name):
        return None
    if all(word in STOP for word in words):
        return None
    # "no thanks at all", "no ta", "no worries": what is left after the no answers the question
    # instead of naming a new thing to ask it about.
    if all(word in A_COURTESY or word in STOP for word in words):
        return None
    return name


# A follow-up that only names a person: "what about my dad", "and something for my brother".
# "What should I get my mum for her birthday" ... "what about my dad" is one question asked about
# two people, and read on its own it is a bare ask that no entry fits, so the person got the
# search hedge or the line said back. The possessive is what makes it a person rather than a
# thing: "my mum" is somebody, "the shed" is not.
PERSON_LEAD = re.compile(
    r"^\W*(?:(?:ok|okay|right|so|yes|yeah|and)\b[\s,]*)*"
    r"(?:(?:and|but|or)\s+)?"
    r"(?:(?:what|how)\s+about|what\s+of|and|also|plus)\b[\s,]*"
    r"(?:something\s+for|one\s+for|a\s+gift\s+for|the\s+same\s+for|presents?\s+for)?[\s,]*", re.I)
# What is left of the line once the person is taken out has to say nothing about them: "what
# about my dad" is the person, "what about my dad's birthday" is their birthday, another thing.
PERSON_FILLER = frozenset((
    "for", "to", "about", "with", "then", "too", "also", "instead", "please", "thanks",
    "the", "a", "an", "get", "buy", "got", "them", "him", "her", "and", "as", "well",
    "his", "hers", "their", "birthday", "christmas", "present", "gift", "presents",
    "gifts",
))


def someone(text):
    """The person a follow-up only names, or None: "what about my dad" -> "dad".

    "and something for my brother", "what about my mum then" and "no i mean my sister" are the same
    reading. A line that says anything else about them ("what about my dad's birthday", "how old
    is my dad") is not this: it asks its own thing, and reading it as the earlier question would
    throw that away.
    """
    from .topics import person

    said = _said(text).strip(" ?!.")
    if not said or len(said.split()) > 6:
        return None
    lead = PERSON_LEAD.match(said) or REPAIR.match(said)
    if not lead:
        return None
    rest = said[lead.end():].strip(" ?!.,")
    who = person(rest)
    if not who:
        return None
    left = re.sub(r"'s\b", "", re.sub(r"\b(?:my|our)\s+" + re.escape(who) + r"\b", " ", rest))
    spare = [word for word in re.split(r"[ ']", left)
             if word and word not in PERSON_FILLER and word not in STOP]
    if spare:
        return None  # their birthday, their new job: a thing of theirs, not the person
    return who


def _earlier(memory, text, n=4, wide=False):
    """The person's own questions before this line, newest first, with the answer each got.

    *wide* takes statements as well as questions. A repair is the person saying the earlier line
    got its subject wrong, so it can take back a statement too: "my tomato plants have yellow
    leaves" ... "i meant my pepper plants". Nothing else asks for that, because a "what about X"
    hanging off a statement is not a rewrite of it.
    """
    from . import recent

    here = _said(text)
    found = []
    for turn in reversed([t for t in recent(memory, n + 2) if isinstance(t, dict)]):
        question = _said(turn.get("user"))
        if question and (question == here or question == here.rstrip(" ?!.")):
            continue  # this line, already written down
        answer = _said(turn.get("bot"))
        if len(question.split()) < 3:
            continue
        first = question.split()[0].strip("?,!")
        if not wide and "?" not in question and first not in OPENERS and first not in ASK:
            continue  # "whats the capital of australia" with no question mark is still a question
        found.append((question, answer))
        if len(found) >= n:
            break
    return found


# The words that make a subject a phrase rather than the subject itself: "my dog" is the dog,
# "a boiler" is the boiler. What is left is what a correction puts the new thing into.
OWNER = frozenset(("my", "our", "your", "their", "his", "her", "the", "a", "an", "some",
                   "this", "that"))


def _about(question):
    """The thing an earlier line is asked about, or None: the chicken in "how long does a
    chicken take to roast".

    Read off the understanding of the earlier line rather than guessed from its words, because
    the word an answer takes up is often the verb ("about 20 minutes per 500g" takes up "take"
    and never says chicken), and a correction puts the new thing in place of the thing asked
    about, not in place of the asking. A line with no subject of its own ("how do i get rid of
    ants") has nothing to offer.
    """
    from ..understanding import understand

    try:
        read = understand(question, {})
    except Exception:  # noqa: BLE001 - a line that cannot be read offers no subject
        return None
    subject = _said((read or {}).get("subject") if isinstance(read, dict) else "")
    subject = subject.strip(" ?!.,")
    if not subject or len(subject.split()) > 3:
        return None
    words = subject.split()
    while words and words[0] in OWNER:
        words = words[1:]
    if not words or all(word in STOP for word in words):
        return None
    return " ".join(words)


# The possessives a follow-up can put in front of the thing it names ("what about my hip").
# They are not part of the thing: the earlier line already says whose it is.
OWNER_WORDS = frozenset(("my", "our", "your", "their"))


def _reads_as_a_question(line):
    """True when the earlier line asks something of its own.

    A line with a question mark, or one that opens with a question word ("whats the capital of
    australia" has no question mark and is still a question), is a question. Anything else is a
    statement, and a statement is read differently: see `rewritten`.
    """
    words = line.split()
    if not words:
        return False
    if "?" in line:
        return True
    first = words[0].strip("?,!")
    return first in OPENERS or first in ASK


def _word(question, answer, new_words, taken_up):
    """The earlier question's content word to swap: the one the answer took up (or, on the
    second pass, its last content word), or None."""
    words = [w.strip("?.!,;:") for w in question.split()]
    for word in reversed(words):
        if word in STOP or len(word) < 3 or not word.isalpha():
            continue
        if word in new_words or word in DEICTIC or word in ASK:
            continue
        if taken_up and not (_stem(word) and _stem(word) in answer):
            continue
        return word
    return None


def _replace(question, word, new):
    """The earlier question with *word* taken out and the new thing in its place."""
    found = re.search(r"\b(?:(a|an)\s+)?" + re.escape(word) + r"\b", question, re.I)
    if not found:
        return None
    if found.group(1):
        # "boil an egg" with "duck egg" put in is "boil a duck egg": the article belongs to the
        # new thing, not to the one it replaced.
        lead = "an " if new[:1] in "aeiou" else "a "
    else:
        lead = ""
    rewritten = question[:found.start()] + lead + new + question[found.end():]
    # A new thing that ends in a word the question already has next to it would say it twice:
    # "my tomato plants have yellow leaves" with "pepper plants" for "tomato" is "my pepper
    # plants plants have yellow leaves".
    rewritten = re.sub(r"\b(\w+)\s+\1\b", r"\1", rewritten)
    if rewritten == question:
        return None
    # A correction renames the thing, so the old thing goes. When the new thing's own head noun is
    # still in the line, the swap took out something else: "i want to lose a stone" corrected to
    # "half a stone" put the new thing where "lose" was and left "a stone" behind, and the doubled
    # noun reached the running entry ("a half marathon takes twelve to sixteen weeks"). A reading
    # that renames nothing is not a reading.
    head = new.split()[-1].lower()
    if len(new.split()) > 1 and rewritten.lower().count(head) > 1:
        return None
    return rewritten


def _spans(question, subject):
    """The stretches of the earlier question a new thing could take the place of.

    The thing asked about is often more than its head word: "how do i clean a stainless steel
    pan" asked about cast iron is that question with "stainless steel" put right, and "how
    much does a boiler service cost" asked about a gas safety check is "how much does a gas
    safety check cost", with the "service" gone. So the words around the subject are offered
    too, longest first, because a longer stretch leaves less of the old thing behind.
    """
    words = [w.strip("?.!,;:") for w in question.split()]
    if " " in subject or subject not in words:
        return [subject]
    at = words.index(subject)

    def may_be_it(word):
        return bool(word) and word.isalpha() and word not in STOP and word not in DEICTIC \
            and word not in ASK

    spans = []
    for back in (2, 1):
        if at - back >= 0 and all(may_be_it(w) for w in words[at - back:at]):
            spans.append(" ".join(words[at - back:at + 1]))
    if at + 1 < len(words) and may_be_it(words[at + 1]):
        spans.append(" ".join(words[at:at + 2]))
    spans.append(subject)
    for back in (2, 1):
        if at - back >= 0 and all(may_be_it(w) for w in words[at - back:at]):
            spans.append(" ".join(words[at - back:at]))
    found, out = set(), []
    for span in spans:
        if span and span not in found:
            found.add(span)
            out.append(span)
    return out


def is_repair(text):
    """True when the line takes back the thing it named: "i meant a turkey", "no wait, duck"."""
    said = _said(text).strip(" ?!.")
    return bool(REPAIR.match(said)) or _after_a_take_back(said) is not None


def candidates(text, memory, most=3):
    """The lines this one could be read as, best first, each with the word it replaced.

    A follow-up that only names a new thing is the earlier question with that thing in it, and
    the earlier question is not always about the word its answer took up: "how long does a
    chicken take to roast" is answered with "20 minutes per 500g plus 20", which takes up
    "take" and never says chicken, so "i meant a turkey" was swapped into "how long does a
    chicken turkey to roast" and reached nothing. The thing the earlier line is asked about is
    tried first, then the word the older reading picked, then its last content word - and the
    caller holds every reading to an entry whose answer is about the new thing, so a swap the
    conversation does not support costs a shrug, not a wrong answer.
    """
    new = thing(text)
    if not new:
        return []
    repaired = is_repair(text)
    new_words = set(re.split(r"[ ']", new))
    place = bool(_the_preposition_of(new))
    found = []
    for question, answer in _earlier(memory, text, wide=repaired):
        subject = _about(question)
        words = []
        if place:
            # A thing that arrives with its own preposition ("from birmingham", "in the
            # freezer") goes where the earlier question's own place was, whole: the word to swap
            # is the place the same preposition was said with, and it is tried first. Put into a
            # bare noun instead, the question kept both places - "whats a good from birmingham
            # trip from manchester" - and that line, which nobody wrote, reached the entry on how
            # long a trip should be rather than the one that knows the day trips from Birmingham.
            had = _the_place_after_the_same_preposition(question, new)
            if had:
                words.append(had)
        words += _spans(question, subject) if subject else []
        words += [_word(question, answer, new_words, True),
                  _word(question, answer, new_words, False)]
        for word in words:
            if not word:
                continue
            line = placed(question, word, new) if place else _replace(question, word, new)
            if not line or _a_second_place(question, line, new):
                continue
            if any(line == had for had, _old in found):
                continue
            found.append((line, word))
            if len(found) >= most:
                return found
    return found


def rewritten(text, memory):
    """The line read as the earlier question with the earlier thing swapped, or None.

    Returns the rewritten question and the word it replaced: the caller needs the replaced word
    to tell an answer about the new thing from the old answer said again.
    """
    new = thing(text)
    if not new:
        return None
    new_words = set(re.split(r"[ ']", new))
    # A statement counts here as well as a question: "my knee hurts" ... "what about my hip" is
    # that statement about the hip, and read on its own the follow-up names nothing but its
    # thing. The rewritten line still has to reach an entry whose answer is about the new thing,
    # which is the caller's check, so a statement the conversation does not support costs a shrug.
    earlier = _earlier(memory, text, wide=True)
    asked = [(line, answer) for line, answer in earlier if _reads_as_a_question(line)]
    told = [(line, answer) for line, answer in earlier if not _reads_as_a_question(line)]
    # The thing being talked about is the one the answer took up: that is the word to replace,
    # and it is tried first because it is the reading the conversation supports. An answer can
    # take up none of the question's words and still be the answer to it, though - "Canberra, not
    # Sydney: it was purpose-built ..." says nothing about Australia - and then "and what about
    # New Zealand" is left with no swap word at all. So a second pass takes the question's own
    # last content word, which is where a subject usually sits ("the capital of Australia", "how
    # tall is Everest"). The caller still holds the rewritten line to an entry whose answer is
    # about the new thing, so a swap the conversation does not support costs a shrug, not a
    # wrong answer.
    for taken_up in (True, False):
        for question, answer in asked:
            if not answer:
                continue
            swap = _word(question, answer, new_words, taken_up)
            if not swap:
                continue
            candidate = placed(question, swap, new)
            if candidate and candidate != question:
                return candidate, swap
    # A question always gets first refusal: a statement is the weaker reading of the two, and
    # "what should i do this weekend" ... "its meant to rain" ... "what about anything cheap"
    # read off the weather line ("its meant to anything cheap") reaches the budget entry and
    # answers a plan for a rainy weekend with "fixed bills and food first, then savings".
    # A statement has no ask of its own, so the word a new thing goes in place of can be the
    # thing the statement is about rather than any word of it: "im thinking of baking a cake"
    # ... "what about a coffee cake" is that statement about a coffee cake, and "cake" is what
    # the new thing replaces.
    # It is only a list being worked down when the new thing is another kind of the thing a
    # follow-up in between named: "what about a carrot cake" ... "what about a coffee cake" is
    # the same question about two kinds of cake. A follow-up that names something else entirely
    # ("what about a rescue dog" ... "what about a puppy") is not that list, and the statement
    # behind it is not the question to ask again - read that way, the puppy got a vet referral
    # where the dog answer had just been given.
    in_between = thing(earlier[0][0]) if earlier else None
    head = new.split()[-1].strip("?.!,;:").lower() if len(new.split()) > 1 else ""
    if in_between and head not in in_between.split():
        return None
    for question, answer in told:
        if not answer:
            continue
        subject = _about(question)
        for swap in (_spans(question, subject) if subject else []):
            candidate = placed(question, swap, new)
            if candidate and candidate != question:
                return candidate, swap
    return None


def _named_somebody(memory, text, n=4):
    """The person's own lines before this one that name somebody, newest first, with the answer.

    A statement counts here where the thing swap asks for a question: "I'm buying a gift for my
    sister" ... "what about my brother" is one question about two people even though the first
    line was not phrased as one. Nothing is guessed from it - the rewritten line still has to
    reach an entry, and the answer still has to be about the new person.
    """
    from . import recent

    here = _said(text)
    found = []
    for turn in reversed([t for t in recent(memory, n + 2) if isinstance(t, dict)]):
        line = _said(turn.get("user"))
        if not line or line == here or line == here.rstrip(" ?!."):
            continue
        if len(line.split()) < 3:
            continue
        found.append((line, _said(turn.get("bot"))))
        if len(found) >= n:
            break
    return found


def rewritten_person(text, memory):
    """The line read as the earlier question with the earlier person swapped, or None.

    "What should I get my mum for her birthday" ... "what about my dad" is that question about
    the dad, and asked in full it reaches the entry that answers it. The earlier question has to
    name somebody of its own: with no person in it ("how do i stop my cat scratching the sofa")
    there is nothing to put the new one in place of, and the line keeps whatever reading it has.

    Returns the rewritten question and the person it replaced.
    """
    from .topics import person

    who = someone(text)
    if not who:
        return None
    for question, _answer in _named_somebody(memory, text):
        old = person(question)
        if not old or old == who:
            continue
        named = re.compile(r"\b(my|our)\s+" + re.escape(old) + r"\b", re.I)
        found = named.search(question)
        if not found:
            continue
        candidate = named.sub(lambda m: m.group(1) + " " + who, question, count=1)
        if candidate != question:
            return candidate, old
    return None


def names_person(old, answer, text, last=""):
    """True when an answer to the rewritten question is about the new person, not the old one.

    A gift answer names neither "mum" nor "dad" ("Go consumable and a notch better than he'd
    buy himself"), so there is no word to look for. What can be said is what must not happen: the
    old person's name in the new answer, or the answer just given handed over again as if it were
    about somebody else.
    """
    who = someone(text)
    said = _said(answer)
    if not who or not said:
        return False
    if old and re.search(r"\b" + re.escape(old) + r"\b", said):
        return False
    return not last or said != _said(last)


DETERMINER = frozenset("""the a an my your his her its their our this that these those some any
another""".split())
# The words a place is said with when it is given as a place. The earlier question's own
# preposition is taken out with the thing, so the new place brings its own instead of following
# the old one ("the smell in my fridge" is asked again as "the smell under the sink").
PREPOSITION = frozenset("""in on at for with from by to near inside outside under over behind
above below beneath underneath between beside besides alongside around across along through
against towards toward onto upon within without off out up down past opposite round via
about""".split())
# A preposition said in more than one word: only the first is part of the span taken out.
PREPOSITION_TAIL = frozenset("""next close right just all the top bottom front back inside
outside end side""".split())


def _the_preposition_of(new):
    """The preposition a new thing arrives with ("from birmingham" -> "from"), or ""."""
    words = str(new or "").split()
    if not words:
        return ""
    head = words[0].strip("?.!,;:").lower()
    return head if head in PREPOSITION else ""


def _the_place_after_the_same_preposition(question, new):
    """The earlier question's place, said with the preposition the new thing brings, or None.

    "whats a good day trip from manchester" corrected to "sorry, i meant from birmingham" is the
    same question about the other place, so the word to swap is Manchester and the preposition
    goes with it. Only the phrase right after that same preposition is offered: the place is what
    the new one takes the place of, and a question with no such phrase has nothing to put it in.
    """
    head = _the_preposition_of(new)
    if not head:
        return None
    said = question.split()
    for at, word in enumerate(said):
        if word.strip("?.!,;:").lower() != head:
            continue
        after = at + 1
        while after < len(said) and said[after].strip("?.!,;:").lower() in DETERMINER:
            after += 1
        span = []
        for follow in said[after:]:
            bare = follow.strip("?.!,;:")
            if not bare.isalpha() or bare.lower() in STOP or bare.lower() in PREPOSITION:
                break
            span.append(bare)
            if len(span) == 2:
                break
        if span:
            return " ".join(span)
    return None


def _a_second_place(question, line, new):
    """True when a reading hangs a second place on the earlier question with the same preposition.

    "from ... from ..." and "in the in the freezer" are sentences nobody writes: a place that
    brings its own preposition takes the old place's place. The reading is not the question the
    person meant, so it is dropped rather than offered to the entries.
    """
    head = _the_preposition_of(new)
    if not head:
        return False

    def count(text):
        return sum(1 for word in str(text or "").split()
                   if word.strip("?.!,;:").lower() == head)

    return count(line) > count(question)


def placed(question, old, new):
    """The earlier question with the old thing taken out and the new one in its place, or None.

    A new thing that carries its own preposition ("and in the freezer too", "what about under the
    sink") goes where the old place was whole: the preposition in front of the old thing, any
    "my"/"the" in between, and the thing itself come out together, so the question is asked again
    as "the smell in my freezer" or "the smell under the sink". Where the earlier question has no
    preposition in front of the thing ("how do i clean the oven") there is no place to put the
    new one, and None is returned: a hedge, not "the smell in my under the sink".
    """
    words = question.split()
    new_words = new.split()
    at = next((i for i, word in enumerate(words) if word.strip("?.!,;:") == old), None)
    if at is None or not new_words:
        return None
    # What decides is whether the new thing arrives with a place's preposition of its own, not how
    # many words it has: "new zealand" is two words and carries none, so it goes where the old
    # thing was like any bare thing ("the capital of new zealand"), while "under the sink" brings
    # its own preposition and takes the old one's place with it.
    head = new_words[0].strip("?.!,;:").lower()
    if head in PREPOSITION or head in PREPOSITION_TAIL:
        start = at
        while start > 0 and words[start - 1].strip("?.!,;:").lower() in DETERMINER:
            start -= 1
        if start == 0 or words[start - 1].strip("?.!,;:").lower() not in PREPOSITION:
            # The earlier question has no place around the thing ("how do i clean the shower"),
            # so there is no place to put the new one beside. The new place goes where the thing
            # was: "how do i clean under the sink". Reading it out with "the" left in front
            # ("how do i clean the under the sink") is what the crude string replace did, and
            # turning the line down leaves the person with their own words repeated back
            # ("Got it - under the sink"), which is worse than either.
            return " ".join(words[:start] + new_words + words[at + 1:])
        start -= 1
        if start > 0 and words[start - 1].strip("?.!,;:").lower() in PREPOSITION_TAIL:
            start -= 1  # "next to my shed", "on top of the fridge"
        return " ".join(words[:start] + new_words + words[at + 1:])
    rewritten = question.replace(old, new, 1)
    # A new thing whose own head noun is already beside the old one would say it twice: "what
    # about a carrot cake" asked again about a coffee cake is "what about a coffee cake cake",
    # and a line that renames nothing is not a reading of the follow-up. The earlier line is
    # passed over and the question behind it is read instead.
    head = new_words[-1].strip("?.!,;:").lower()
    if len(new_words) > 1 and rewritten.lower().count(head) > 1:
        return None
    return rewritten


def _said_again(answer, memory):
    """True when this answer is the one just given, word for word.

    A follow-up that hands back the paragraph it just gave is the one reply worse than a hedge.
    The fridge entry is keyed on "smell" and says nothing about either place, so the rewritten
    freezer question reaches it and the fridge paragraph comes back whole.
    """
    if not isinstance(memory, dict):
        return False
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return False
    last = str(turns[-1].get("bot") or "")
    if not last.strip():
        return False
    return (" ".join(str(answer or "").lower().split())
            == " ".join(last.lower().split()))


def _brings_its_own_place(new):
    """Whether the new thing is a place said with its own preposition ("under the sink")."""
    words = str(new or "").split()
    return bool(words) and words[0].strip("?.!,;:").lower() in PREPOSITION


def names(old, answer, text, memory=None, question=None):
    """True when an answer to the rewritten question is about the new thing, not the old one.

    "can you give me a dessert idea" reaches the crumble, and the crumble is not about dinners:
    an answer that still talks about the thing the line replaced is the earlier answer said
    again ("how long do i roast a dessert for" reaches the chicken entry and talks chicken), and
    handing that over is worse than not answering. An answer that names neither is taken, since
    the entry was reached by a question about the new thing.

    A place that brings its own preposition is the one case where naming neither is not enough.
    The rewritten question ("how do i get rid of the smell in the shed") reaches entries on a
    reading of a line nobody wrote, and "the smell in the shed" reaches the weight-loss entry and
    gets "fill up on protein and fibre first" - an answer about nothing the person asked. So for
    a place the answer also has to be about the question: one of its own subject words
    ("smell" for the smell in the shed's sink) has to be in what comes back, or the line keeps
    its hedge.
    """
    new = thing(text)
    said = _said(answer)
    if not new or not said:
        return False
    if _said_again(answer, memory):
        return False  # the same paragraph again is not an answer about the new thing
    fresh = [word for word in re.split(r"[ ']", new) if word and word not in STOP]
    if any(_stem(word) in said for word in fresh):
        return True
    if _brings_its_own_place(new):
        asked = [word for word in re.split(r"[ ']", _said(question))
                 if word and word not in STOP]
        return any(_stem(word) in said for word in asked)
    return _stem(old or "") not in said
