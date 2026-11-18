"""The thread of the conversation: what we are on, and how to say the user's earlier lines.

The conversation lane owns this. A module that answers a question about the conversation
itself ("where were we?", "what did I just ask you?") needs two things that no other module
provides:

* `subject(memory)`: the thing the last few turns were about, in a phrase the bot can name
  ("the birthday cake", "the chicken", "Lisbon"), read from the user's own lines.
* `restate(text)`: the user's earlier line said again inside a sentence, in their words and
  in grammar that fits ("can i make it the day before" -> "whether you can make it the day
  before"; "how long should i cook a 2kg chicken" -> "how long you should cook a 2kg
  chicken"). First person becomes second person, the question is embedded, nothing is
  invented.

Both read `memory["turns"]` and the shared reading of each line (`bot.understanding`), so they
work for any topic and any wording. Nothing here writes to memory or answers a turn.
"""
import re

from ..understanding import understand
from ..understanding.kinds import NEGATIVE, POSITIVE, VERB_FORMS, VERBISH
from ..understanding.normalize import IRREGULAR_PARTICIPLES
from ..understanding.topics import PLACES as PLACE_WORDS
from ..compose import pick
from . import detail
from . import _from_the_bot, _to_the_bot
from .facts import no_tone

# Lines that carry no subject of their own: acknowledgements and short reactions.
THIN = frozenset(("ok", "okay", "k", "cool", "nice", "great", "good", "yeah", "yep", "yes",
                  "no", "nah", "nope", "lol", "haha", "ha", "mm", "hmm", "right", "fair",
                  "sure", "same", "true", "thanks", "thx", "ta", "cheers", "please"))

# A line that only signs off carries no subject either. "night" after the bot said goodnight is
# the person closing the app, and reading it as a statement made a chat end on it: the recap
# looked at the closing, not at the line before, so a chat with a real line in it and two
# closings at the end was told "there's nothing of yours to look back on". A closing is the word
# itself with only the chat's filler in front of it, so "off to bed" and "right, night then"
# are closings and "my bed is uncomfortable" is not.
CLOSINGS = frozenset(("night", "nite", "goodnight", "goodnite", "nighty", "bed", "bedtime",
                      "bye", "byebye", "cya", "sleep"))

CLOSING_FILLER = frozenset(("right", "ok", "okay", "well", "anyway", "im", "i", "am", "we",
                            "were", "re", "going", "gonna", "gotta", "off", "to", "the", "a",
                            "now", "so", "then", "just", "time", "for", "up"))

SIGNS_OFF = re.compile(
    r"^(?:(?:" + "|".join(sorted(CLOSING_FILLER, key=len, reverse=True)) + r")\s+)*"
    r"(?:" + "|".join(sorted(CLOSINGS, key=len, reverse=True)) + r")$")

# Words that name a document or an event rather than the thing being discussed.
WEAK = frozenset(("name", "time", "day", "week", "weekend", "month", "year", "thing", "lot",
                  "bit", "way", "kind", "sort", "part", "place", "trip", "plan", "idea",
                  "question", "answer", "chat", "talk", "conversation", "help", "advice"))

# Words that never name the thing the conversation is on, when a line has no entity at all.
NON_NOUN = WEAK | THIN | frozenset((
    "before", "after", "again", "still", "just", "only", "maybe", "perhaps", "really",
    "nervous", "worried", "scared", "fine", "ok", "better", "worse", "best", "worst",
    "one", "ones", "two", "three", "first", "last", "next", "ask", "asked", "say", "said",
    "want", "need", "try", "trying", "started", "start", "stop", "make", "made", "get",
    "getting", "think", "thought", "going", "went", "come", "came", "much", "many", "more",
    "less", "all", "any", "some", "else", "something", "anything", "everything", "nothing",
    "remember", "recall", "forget", "said", "saying", "talked", "covered", "discussed", "meant",
    # "rid" is what is left of "get rid of" once the verb has gone, and it reads as the thing the
    # chat is on: a recap said "We were on the rid" about a fridge that smelled. The thing is what
    # was being got rid of, and that is the next word along.
    "rid",
))

# Discourse markers that open a follow-up rather than the topic.
LEAD = ("by the way", "btw", "anyway", "anyways", "so", "and", "but", "ok", "okay", "well",
        "oh", "ah", "right", "great", "sorry", "also", "then", "now", "ha", "hmm", "just",
        "cool", "nice", "yes", "yeah")

MODAL = frozenset(("would", "should", "will", "can", "could", "may", "might", "must", "shall",
                   "ought"))
AUX = frozenset(("am", "is", "are", "was", "were", "do", "does", "did", "have", "has", "had",
                 "can", "could", "will", "would", "shall", "should", "may", "might", "must"))
WH = frozenset(("what", "why", "how", "when", "where", "who", "whom", "whose", "which"))
PRONOUN = frozenset(("i", "we", "you", "it", "they", "he", "she", "this", "that", "there",
                     "the", "a", "an", "my", "our", "your"))
SUBJECTISH = PRONOUN | frozenset(("people", "anyone", "someone", "everyone", "kids", "children"))

# First person in a question the user asked is second person when the bot says it back.
FLIP = {"i": "you", "me": "you", "my": "your", "mine": "yours", "myself": "yourself",
        "we": "you", "us": "you", "our": "your", "ours": "yours", "ourselves": "yourselves",
        "i'm": "you're", "i've": "you've", "i'd": "you'd", "i'll": "you'll",
        "we're": "you're", "we've": "you've", "we'd": "you'd", "we'll": "you'll",
        "im": "you're", "ive": "you've", "am": "are"}

PLACE_NAMES = frozenset(("place", "name"))
# A day or a month says when, never what about: "we're off to rome in july" is on Rome.
CALENDAR = frozenset("""today tomorrow yesterday tonight morning afternoon evening night week
weekend month year hour minute second monday tuesday wednesday thursday friday saturday sunday
january february march april may june july august september october november december
spring summer autumn winter christmas easter holidays""".split())
QUALITY = POSITIVE | NEGATIVE

# "It's for a warehouse job": the reading calls the contraction a name; it names nothing.
CONTRACTIONS = frozenset(("it's", "that's", "there's", "they're", "we're", "he's", "she's",
                          "you're", "i'm", "i've", "i'd", "i'll", "there", "it", "this",
                          "that", "they", "these", "those", "here"))


def _asks_about_the_bot(reading):
    """True when the line asks about the bot itself rather than about something of their own.

    "Are you a real person" is not a subject the chat was on, so it must not be named back as
    one: on main the next "what did we talk about" answered "We were on the real person", a
    phrase nobody said, cut out of a question about the bot. The reading is the understanding
    engine's own (`about_bot`), so every shape of the question is covered rather than a list of
    phrasings here: "are you a robot", "are you human", "do you sleep", "what model are you".
    A line that asks about the bot and also says something of their own is not in this: the
    reading only sets `about_bot` when the whole line is about the bot.
    """
    return bool(reading.get("about_bot"))


def _asks_about_the_chat(text, memory, skip):
    """True when the store says this line is about the conversation, not about the world.

    The store owns that test (`memory_store._about_this_chat`), so it is passed in rather than
    copied: a second list of the same phrasings would drift. Without it the reading's own
    `topic_own`/`kind` still catches most of these lines.
    """
    return bool(skip) and bool(skip(text, memory))


def _turns(memory):
    turns = memory.get("turns") if isinstance(memory, dict) else None
    return turns if isinstance(turns, list) else []


def earlier_turn(memory):
    """True when there is an earlier turn for a reply to point back at.

    One check, in one place, for every reply that refers back to something said before: a
    point back at turns that never happened is the same fault wherever it appears - the first
    reply answering "im back" with "What were we saying?", a receipt for a question nobody
    asked, a nod at a feeling no one expressed. Modules ask this rather than each testing
    `memory` their own way, so a new pool cannot reintroduce the fault by forgetting to.
    """
    return any(isinstance(turn, dict) and (turn.get("user") or turn.get("reply"))
               for turn in _turns(memory))


_ONLY_THE_ARRIVAL = re.compile(
    r"^(?:(?:hi|hiya|hey|hello|ok|okay|right|so|well|anyway)[,\s]+)*"
    r"(?:im|i am|iam|we are|were|we're)?\s*back"
    r"(?:\s+(?:again|home|now|too|from\s+(?:work|the\s+\w+|holiday|holidays|town|"
    r"school|shopping|the\s+shop|hospital|abroad|lunch|a\s+break)))?"
    r"[\s.!?]*$")


def only_the_arrival(text):
    """True when the line says nothing but that the person is back.

    A return carries no symptom, no subject and no question: "im back", "back again", "back
    from work", "we are back home". A chat with a bad knee in it still read the word "back" as
    the part and answered a return with the back-pain card, which is the message talking about
    somebody's spine when they said they were back from the shop. The check is here, once, so
    any row that reads a body word can ask it rather than each one learning the word order.
    """
    said = str(text or "").strip().lower().replace("'", "")
    said = re.sub(r"[.,!?]+", " ", said)
    return bool(_ONLY_THE_ARRIVAL.match(" ".join(said.split())))


def user_lines(memory):
    """The user's earlier lines, oldest first, as (text, reading)."""
    out = []
    for turn in _turns(memory):
        text = turn.get("user") if isinstance(turn, dict) else None
        if isinstance(text, str) and text.strip():
            out.append((text, understand(text, {})))
    return out


# A receipt takes the reply in and says nothing about the world: "got it", "alright then",
# "will do", "nice one". It carries no subject either, so the chat was not "on" it, and a recall
# ask two lines later must read the line before it: "im learning spanish" / "got it" / "what am
# i learning" answered "You said got it. Want to carry on?".
RECEIPT_WORDS = frozenset("""
got it alright then will do ok okay right noted thanks thank you ta cheers sure cool great
nice one lovely perfect brilliant grand fine fair enough no worries problem understood
makes sense course yes yeah yep yup mhm okay-doke done
""".split())
# How many words a receipt is allowed: the longest ones above ("fair enough", "no worries",
# "makes sense") are two, and "ok thanks" is two, so four leaves room without reading a sentence.
RECEIPT_LONGEST = 4


def _is_a_receipt(reading):
    """True when the line only takes the reply in and says nothing else."""
    words = [w.strip(".,!?-\u2014\u2013()") for w in reading.get("words") or []]
    words = [w.lower() for w in words if w]
    return bool(words) and len(words) <= RECEIPT_LONGEST and \
        all(w in RECEIPT_WORDS for w in words)


def _is_thin(reading):
    words = [w.strip(".,!?") for w in reading.get("words") or []]
    if not words:
        return True
    if _is_a_receipt(reading):
        return True
    return len(words) <= 2 and all(w in THIN for w in words)


def signs_off(text):
    """True for a line that is only a closing: "night", "im off to bed", "see ya".

    A closing ends a chat and does not move it on, so it is not what the chat was on: a chat
    with a real line in it and two closings at the end was told "there's nothing of yours to
    look back on", because the closings had been read as the whole of the last thing said.
    """
    reading = understand(text, {})
    words = [w.strip(".,!?") for w in reading.get("words") or []]
    if not words:
        return False
    if reading.get("intent") == "farewell":
        return True
    return bool(SIGNS_OFF.match(" ".join(words)))


def carries_subject(text):
    """True when the line can be the thing the chat was on: "hi" and "ok" cannot."""
    said = restate(text) or ""
    return bool(said) and _is_subject_phrase(said)


def thin(text):
    """True for a line that carries no subject: "hi", "ok", "lol", "thanks".

    A greeting is as thin as an "ok": "hi" and then "what were we talking about?" is not a
    conversation about hi, and "We were on hi." answers a subject nobody raised. A line that
    asks about the conversation itself carries no subject either, for the same reason.
    """
    reading = understand(text, {})
    return _is_thin(reading) or _is_memory_line(reading)


# A line that points back at what was said before and names nothing of its own: "same as
# before", "like last time", "the usual", "and that one", "the thing you said", "i meant the
# other one", "same again". With a turn behind it these lines are read as they always were - the
# store's for a correction, the composer's for a choice - so this reading only speaks where the
# chat has nothing behind it, and then the whole answer is that there is no "before" to go on.
POINTS_BACK = re.compile(
    r"^(?:and |so |but |or |ok |okay |well |no |nah |yes |yeah |right |actually |sorry |please"
    r"|how about |what about )*"
    r"(?:"
    r"(?:the )?same(?: one| thing)?"
    r"(?: as (?:before|last time|last night|last week|last year|yesterday|the other day"
    r"|the usual|usual|that|then|them|it|earlier))?"
    r"|(?:just )?like (?:before|last time|last night|last week|yesterday|the usual|that|them|it)"
    r"|(?:anything|something|what) else like (?:that|before|it|them)"
    r"|the usual"
    r"|as (?:we|i) (?:said|discussed|agreed)"
    r"|(?:the )?(?:other|second|first|last) one"
    r"|(?:that|this) one"
    r"|(?:the )?(?:same|other) thing"
    r"|(?:do |try |use )?what (?:you|we) said"
    r"|the thing (?:you|we) said"
    r"|(?:sorry )?(?:i|we) meant (?:the )?(?:other|that)(?: one| thing)?"
    r")"
    r"(?: (?:then|please|again|really|though|now|too|instead))*$")


def points_back(text):
    """True for a line that names nothing of its own and points at what was said before.

    The words are the whole line ("and the other one then"), because a line with a subject in
    it is that subject's: "the other flat" names a flat, and "same as the boiler" names the
    boiler. Nothing here is a question about the chat, which the store reads elsewhere.
    """
    low = " ".join(str(text or "").lower().replace("'", "").split()).strip(" .!?,")
    return bool(low) and len(low.split()) <= 6 and bool(POINTS_BACK.match(low))


# A pointing word that is the whole subject of an ask: "how do i do it", "how long will it
# take", "do that again", "is it worth it". The word carries the subject, so the line names
# nothing the store or the knowledge base can be asked about. "it" and the rest are read as one
# subject by the person typing it, whatever the line around it is asking.
POINTING_WORD = re.compile(r"\b(?:it|that|this|them|those|these|one|ones|there)\b", re.I)
# What the rest of such a line may be made of: the asking words, the auxiliaries, the little
# prepositions, and the verbs that say what to do with a thing without naming one. A line with
# any word outside these names its own subject ("how do i fix a bike"), and is not this.
ASK_WORD = frozenset("""how what when where why which who whose do does did doing done can could
should would will shall am is are was were be been being have has had may may might must i you we
me my our your it that this them those these there one ones a an the and or but so then again
please about for of in on at to with from much many long soon often far time worth better best
good right now just really any ok okay well hey hmm hm oh ah sorry up down off out back
away over around through""".split())
# The verb has to be there: "what about that" and "that one" are the pointer on its own, which
# the composer answers, and this reading is for the ask that has one ("how do i do it").
ASK_VERB = frozenset("""do does did make makes get gets take takes cost costs try use uses go goes
work works need needs start starts keep keeps put puts cook cooks buy buys fix fixes help helps
worth better eat eats drink drinks say says""".split())


# A line that asks the bot to pick between things ("which one should i buy", "should i get this
# one") names no subject either, but the answer it wants is the decision one - "that is yours to
# weigh, not mine" - not "which thing are you pointing at". The decision readers own it, and this
# reading must keep its hands off, or an ask anybody can be helped with gets a shrug about a
# missing subject.
A_CHOICE = re.compile(r"\bwhich\b[^?]*\b(?:should|better|best|instead)\b"
                      r"|\bshould i\b[^?]*\b(?:buy|choose|pick|go for)\b", re.I)


def points_at_a_word_alone(text):
    """True for an ask whose only subject is a pointing word: "how do i do it".

    "how do i do it" as the first line of a chat has no thing in it to answer: the "it" points
    at something the chat has not got, and the turn was answered with a search hedge ("I'm not
    sure about that one, sorry") while the honest reply is that there is nothing for "it" to be
    yet. The words outside the asking words are what is tested, so a line that names a thing of
    its own ("how do i fix a bike", "how long does a chicken take") is not this, and neither is
    "what about that", which is the pointer with no ask around it.
    """
    low = " ".join(str(text or "").lower().replace("'", "").split()).strip(" .!?,")
    words = re.findall(r"[a-z]+", low)
    if not words or not POINTING_WORD.search(low):
        return False
    if A_CHOICE.search(low):
        return False
    other = [word for word in words if word not in ASK_WORD and word not in ASK_VERB]
    if not other:
        return any(word in ASK_VERB for word in words)
    # One word outside the asking words is the verb, and it is read as the verb only when it acts
    # on the pointing word, which is what puts it in front of it: "how do i stop it", "how do i
    # warm it up". A word after the pointing word names the thing itself ("how do i cook this
    # chicken"), and two words are a phrase the store cannot place, so neither is this.
    if len(other) > 1:
        return False
    at = words.index(other[0])
    return at + 1 < len(words) and bool(POINTING_WORD.fullmatch(words[at + 1]))


# A line that asks what they said or were worried about, in their own words: "what was it i was
# worried about", "what were we talking about", "what was it i said". The recall readers read the
# slot ("what did i say her birthday was"), and a line naming no slot at all had no reader: "what
# was it i was worried about" was read as a line about a worry and answered with advice about
# worrying, to somebody who had said nothing yet.
# Only the feelings and the thinking: "what was it i said" and "what were we talking about" name
# the chat itself and already have a reader that answers them with the store's own words, so this
# leaves those alone. What has no reader is the line that names a feeling the chat never heard.
WHAT_I_SAID = re.compile(
    r"\bwhat (?:was|were) (?:it )?(?:i|we) (?:(?:was|were|am|are|had been) )?"
    r"(?:worried|upset|angry|annoyed|sad|unhappy|thinking|saying)(?: (?:about|of))?\b", re.I)


def asks_what_i_said(text):
    """True for an ask about what was said or felt in this chat, naming no slot of its own."""
    return bool(WHAT_I_SAID.search(str(text or "")))


def nothing_said(memory):
    """True when no earlier line of theirs has carried a subject yet.

    "hi" and then "same as before" is a chat with nothing to be the same as, and the same goes
    for "ok" or "thanks" in front of it: a recap or a pointer needs a subject behind it, and a
    greeting has none.
    """
    return not any(carries_subject(str(turn.get("user") or "")) for turn in _turns(memory))


def _is_memory_line(reading):
    """A line about the conversation itself ("do you remember what we talked about") is not
    something the conversation is about."""
    return reading.get("topic_own") in ("about-the-bot", "memory") or \
        reading.get("intent") in ("about_bot", "greeting") or \
        reading.get("kind") in ("greeting", "memory")


def _named_entities(reading):
    """The entities worth naming: no documents, no pronouns, no one-word filler."""
    out = []
    if _is_memory_line(reading):
        return out
    for entity in reading.get("entities") or []:
        if not isinstance(entity, dict):
            continue
        name = (entity.get("text") or "").strip()
        core = name.lower()
        if not name or core in WEAK or core in FLIP or core in THIN or len(core) <= 2:
            continue
        if core.split()[0] in CONTRACTIONS:
            continue
        # A number and its unit are a quantity: "6,000 pounds" is not a subject.
        if core in MEASURE or name[:1].isdigit():
            continue
        out.append(entity)
    return out


def _groups(entities, reading):
    """Entities that sit next to each other in the line, joined: "birthday" + "cake"."""
    text = reading.get("norm_text") or ""
    groups = []
    for entity in entities:
        name = entity["text"].strip()
        if groups:
            last = groups[-1]
            joined = last[-1]["text"].strip() + " " + name
            if joined.lower() in text:
                last.append(entity)
                continue
        groups.append([entity])
    return groups


# A word straight after one of these is the sentence's verb, not a thing: "what should i put on
# the cake" asks about the cake, and the put is only how the line gets there. A modal or a subject
# pronoun covers almost every sentence, so the test is the grammar, not a verb list. "to" is left
# out on purpose: it marks a place as often as a verb ("a trip to rome", "off to july").
VERB_BEFORE = AUX | frozenset(("i", "we", "you", "they", "he", "she", "it", "not",
                              "please", "lets", "let's", "who", "dont", "doesnt", "didnt",
                              "cant", "wont", "wouldnt", "couldnt", "shouldnt"))


def _is_the_verb(reading, word):
    """True when `word` sits where the sentence puts its verb ("should i put", "we moved")."""
    words = [str(w).strip(".,!?").lower() for w in (reading.get("words") or [])]
    for index in range(len(words) - 1, -1, -1):
        token = words[index]
        if token != word.lower() and not token.startswith(word.lower()):
            continue
        return index > 0 and words[index - 1] in VERB_BEFORE
    return False


def _verb_after_a_subject(reading, word):
    """True when the word is the verb of "my back hurts", "the shed leaks".

    A noun the line has already determined ("my back", "the shed") cannot be followed by another
    bare noun, so a word that ends in -s there is what the clause does, not a second thing. Only
    that shape: a plural said on its own ("the chair legs") is read the same way only because the
    word before it is a noun the line determined, and "the chair" is a fair subject for it too.
    """
    if not word.endswith("s") or word.endswith("ss") or len(word) < 3:
        return False
    words = [str(w).strip(".,!?").lower() for w in (reading.get("words") or [])]
    for index in range(len(words) - 1, -1, -1):
        token = words[index]
        if token != word.lower() and not token.startswith(word.lower()):
            continue
        if index < 2:
            return False
        before, owner = words[index - 1], words[index - 2]
        return owner in DETERMINERS or owner in ("my", "our", "your", "his", "her", "their")
    return False


def _word_behind_prep(reading, word):
    """True when the only place this word holds in the line is behind a preposition."""
    words = [str(w).lower() for w in (reading.get("words") or [])]
    for index in range(len(words) - 1, -1, -1):
        if words[index] != word.lower():
            continue
        before = index - 1
        while before >= 0 and words[before] in DETERMINERS:
            before -= 1
        if before >= 0 and words[before] in PREP:
            return True
    return False


def _behind_a_prep(reading, entity):
    """True when the words just before this entity are a preposition and its article."""
    words = reading.get("words") or []
    at = entity.get("at")
    if not isinstance(at, int) or at <= 0 or at > len(words):
        return False
    before = [w.lower() for w in words[max(0, at - 2):at]]
    while before and before[-1] in DETERMINERS:
        before.pop()
    return bool(before) and before[-1] in PREP


def _the_phrase_around(reading, word):
    """The phrase `word` sits in: ("your", "back") for "my back", ("the", "cake"), or ().

    A line whose question word is the only thing before the noun ("where should i go on
    holiday") has no phrase around it, and a bare word there is as likely to be half a verb.
    """
    words = [str(w).strip(".,!?").lower() for w in (reading.get("words") or [])]
    for index, token in enumerate(words):
        if token != word.lower() and not token.startswith(word.lower()):
            continue
        before = words[index - 1] if index else ""
        if before in ("my", "our", "your"):
            return ("your", word)  # said as the person's own, the way an entity is
        if before in DETERMINERS:
            return (before, word)
        return ()
    return ()


def _phrase_for(text, reading, named_only=False):
    """The thing this line is about, as a phrase with its article, or None."""
    keywords = [w for w in reading.get("keywords") or [] if w not in WEAK and w not in THIN]
    entities = _named_entities(reading)
    chosen = None
    for kind in ("place", "person", "name", "thing"):
        groups = _groups([e for e in entities if e.get("type") == kind], reading)
        if kind in ("person", "thing"):
            # A person or a thing behind a preposition is what the line is for, not what it is
            # about: "a birthday cake for my son" is on the cake, and "a word with my boss" is on
            # the word. A place is normally reached through one ("a trip to Portugal"), so it is
            # said as it is.
            groups = [g for g in groups if not _behind_a_prep(reading, g[0])]
        if groups:
            chosen = groups[-1]
            break
    if chosen:
        name = " ".join(e["text"].strip() for e in chosen)
        # "birthday" + "cake", "job" + "interview": a qualifying word just before it belongs.
        before = _qualifier(reading, name, keywords)
        if before:
            name = before + " " + name
        name = _same_spelling(text, name)
        kind = chosen[0].get("type")
        if name.lower().startswith("my "):
            name = "your " + name[3:]
        if kind in PLACE_NAMES or kind == "name" or name[:1].isupper():
            return _place_case(name)
        if name.lower().startswith(("your ", "a ", "an ", "the ")):
            return name
        return "the " + name
    nouns = [w for w in keywords
             if not w.endswith(("ing", "ed")) and w not in NON_NOUN
             and w not in QUALITY and w not in CALENDAR
             and not _is_the_verb(reading, w)
             and not _verb_after_a_subject(reading, w)]
    if not nouns:
        return None
    # "what should i cook" is still about the cook: a word that is also a bare verb is only
    # dropped when the line has another noun to carry the subject.
    things = [w for w in nouns if w not in VERB_FORMS]
    if things:
        nouns = things
    # "a second hand bike for the commute" is about the bike: a word reached through a
    # preposition says what the line is for. A place is reached that way as a matter of course
    # ("a trip to lisbon"), so it is left in.
    kept = [w for w in nouns if w in PLACE_WORDS or not _word_behind_prep(reading, w)]
    if kept and len(kept) < len(nouns):
        nouns = kept
    # A place is said as it was typed ("Rome", not "the Rome"), the way an entity is.
    if nouns[-1] in PLACE_WORDS:
        return _place_case(_same_spelling(text, nouns[-1]))
    around = _the_phrase_around(reading, nouns[-1])
    if named_only and not around:
        return None
    if around and around[0] == "your":
        return "your " + nouns[-1]
    return "the " + nouns[-1]


def _place_case(name):
    """A place is a name, so it keeps its capital however it was typed: "rome" -> "Rome"."""
    words = name.split()
    if not words:
        return name
    if name.lower() in PLACE_WORDS or all(w.lower() in PLACE_WORDS for w in words):
        return " ".join(_capital(w) for w in words)
    return name


def _same_spelling(text, phrase):
    """`phrase` as it was typed, so a name keeps its capitals ("Lisbon", not "lisbon")."""
    lowered = text.lower()
    index = lowered.find(phrase.lower())
    if index >= 0:
        return text[index:index + len(phrase)]
    return phrase


DETERMINERS = frozenset(("a", "an", "the", "my", "your", "our", "their", "his", "her",
                         "its", "this", "that", "these", "those", "some", "any", "many",
                         "much", "no", "every", "each"))


def _qualifier(reading, phrase, keywords):
    """The word that belongs to `phrase`: "birthday cake", "job interview", "rescue dog".

    Only a word that sits between a determiner and the thing counts, so "to save money" keeps
    "money" and "a rescue dog" becomes "rescue dog".
    """
    text = reading.get("norm_text") or ""
    index = text.find(phrase.lower())
    if index <= 0:
        return None
    words = text[:index].split()
    if len(words) < 2:
        return None
    before = words[-1].strip(".,!?")
    if before not in keywords or words[-2].strip(".,!?") not in DETERMINERS:
        return None
    return before


def about(memory, skip=None):
    """The thing the conversation is on, as a phrase ("the birthday cake", "Lisbon"), or None.

    The newest line that carries a subject wins, so a return to something said earlier is
    named before the small talk that followed it. A line that names something beats one that
    only carries a content word, so "and can I make it the day before?" never becomes the
    subject of a conversation about a cake.

    When no line carries a subject of its own it defers to `topics.subject`, so this module
    adds a reader on top of the store's answer instead of a second answer to the same
    question.
    """
    lines = [(text, reading) for text, reading in user_lines(memory)
             if not _is_thin(reading) and not _is_memory_line(reading)
             and not _asks_about_the_chat(text, memory, skip)
             and not _asks_about_the_bot(reading)
             # A closing ends the chat and does not change what it was on: "right, im off to bed"
             # is not a chat about the bed, and reading it as one turned the "night" after it
             # into a mattress question.
             and not signs_off(text)]
    for pass_kind in ("entity", "statement", "any"):
        for text, reading in reversed(lines):
            names_something = bool(_named_entities(reading))
            if pass_kind == "entity" and not names_something:
                continue
            # A question that names nothing is not what the conversation is on: "what should I
            # see there?" is about Rome, and "how much would a service cost?" is about the bike.
            # It is still the subject when nothing else in the conversation names anything, which
            # is the one-line case: "where should i put the plant?" is on the plant.
            if pass_kind == "statement" and reading.get("kind") == "question" \
                    and not names_something:
                continue
            if pass_kind != "entity" and (reading.get("intent") == "feeling"
                                          or reading.get("topic_own") == "feelings"):
                continue
            phrase = _phrase_for(text, reading, named_only=pass_kind == "any")
            if phrase and _is_subject_phrase(phrase):
                return phrase
    return _from_topics(memory)


# The verbs a request is made with: "can you take a look at this" is a request, not a subject.
BARE_VERBS = frozenset("""do give get go try keep sort call tell know feel be been have wait
    stop start find leave come put use take see say think love like want look check help send
    make book buy fix sort plan""".split())


# The numbers people say in words, up to the ones a line has a count of ("a roast for six").
NUMBER_WORD_HEADS = frozenset("""
zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen
sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety
hundred thousand million
""".split())


def _is_subject_phrase(phrase):
    """True when the phrase can stand after "we were on".

    A greeting or an "ok" the line carried is not a thing to be on ("we were on hi"), and
    neither is a verb someone used to ask for help ("can you take a look at this" is not "the
    look"). The store has a line to say back instead, or an honest "we haven't started yet".
    """
    words = [w.strip(",.;:") for w in str(phrase or "").split()]
    # The article belongs to the phrase, not to what it is about: "the look" is the verb "look".
    if len(words) > 1 and words[0].lower() in DETERMINERS:
        words = words[1:]
    head = words[0].lower() if words else ""
    if not head:
        return False
    try:
        from ..memory import topics as _topics
    except ImportError:  # pragma: no cover - the module is always there in the bot
        return True
    # A figure is not a thing to be on: "im doing a roast for 6" gave a subject of "the six",
    # and "We were on the six" is a person hearing a number read back as if it were the thing.
    if head.isdigit() or head in NUMBER_WORD_HEADS:
        return False
    return not (head in _topics.GREET or head in _topics.ACKS or head in BARE_VERBS)


def _from_topics(memory):
    """What the memory store calls the subject, with the article a sentence needs.

    `topics.subject` answers in keywords ("birthday cake", "trip portugal june"), which is
    right for a key and reads wrong after "we were on". A proper noun keeps no article.
    """
    try:
        from ..memory import topics
    except ImportError:  # pragma: no cover - the module is always there in the bot
        return None
    phrase = " ".join(str(topics.subject(memory) or "").split())
    if not phrase:
        return None
    if not _is_subject_phrase(phrase):
        return None
    words = phrase.split()
    if words[0].lower() in DETERMINERS or words[0][:1].isupper():
        return phrase
    return "the " + phrase


# The reading keeps the question word as a key in `asks`; put the words back.
ASK_WORDS = {"how_long": ("how", "long"), "how_much": ("how", "much"),
             "how_many": ("how", "many"), "how_far": ("how", "far"),
             "how_often": ("how", "often")}


def _is_wh(word):
    """True when the word is a question word, contraction and all.

    "whats the cheapest way" is the question word with its verb on the end, so a question word
    put in front of it made "what whats the cheapest way to that" - the same sentence with the
    ask said twice, once broken. The apostrophe is often not typed, so it is not required.
    """
    core = str(word or "").strip(".,!?").lower().replace("'", "").replace("\u2019", "")
    if core in WH:
        return True
    return core.endswith("s") and core[:-1] in WH


def _with_wh(reading, words):
    """Some readings keep the question word out of the focus ("how many days would you give it"
    reads as "would you give it"), so take it from the words the user typed."""
    if reading.get("kind") != "question" or not words:
        return words
    if _is_wh(words[0]):
        return words
    # A wh the clause still holds is part of the sentence, not the question word the reading
    # dropped: "what" in "do you remember what i said" is the thing asked about, so adding it
    # again gave "what I remember what you said", and "can you tell me how long it takes" came
    # out as "how long I can tell you how long it takes". The line opened on an auxiliary, so
    # it is a "whether" clause with the clause's own words in it.
    held = {str(word).strip(".,!?;:").lower() for word in words}
    norm = [str(word).strip(".,!?").lower() for word in reading.get("norm") or []]
    for index, word in enumerate(norm):
        if word not in WH:
            continue
        phrase = []
        for word2 in norm[index:index + 3]:
            if phrase and (word2 in AUX or word2 in SUBJECTISH or word2 in ("the", "a", "an")):
                break
            phrase.append(word2)
        if phrase and str(phrase[0]).lower() not in held:
            return phrase + list(words)
        break
    for ask in reading.get("asks") or []:
        phrase = ASK_WORDS.get(ask) or ((ask,) if ask in WH else ())
        if phrase and str(phrase[0]).lower() not in held:
            return list(phrase) + list(words)
    return words


def _strip_lead(words):
    """Drop the discourse markers that open a follow-up ("and", "so", "ok")."""
    words = list(words)
    changed = True
    while changed and words:
        changed = False
        for lead in LEAD:
            parts = lead.split()
            if words[:len(parts)] == parts:
                words = words[len(parts):]
                changed = True
    return words


# In a question, the person's "you" is the bot. Said back inside a sentence, that "you" is the
# one speaking: "can you suggest some books?" is "whether i can suggest some books", and
# "did i tell you about the dog" is "whether you told me about the dog".
ADDRESSEE = {"you": "me", "your": "my", "yours": "mine", "yourself": "myself",
             "you're": "i am", "youve": "i have", "you've": "i have", "you'd": "i would",
             "you'll": "i will"}
SUBJECT_YOU = "I"


# A line people say with the subject left off, the way nobody writes it in a grammar book:
# "cant sleep", "didnt get it". The "you" goes in front and the word stays as it was typed.
LOST_SUBJECT = frozenset((
    "cant", "can't", "couldnt", "couldn't", "dont", "don't", "didnt", "didn't", "wont", "won't",
    "havent", "haven't", "hadnt", "hadn't", "wouldnt", "wouldn't", "shouldnt", "shouldn't",
))

# The words a statement can open on and still be about the person, having dropped the "I": the
# be-forms and the contractions above. Not "do", "have" or "would" on their own, which are as
# often an instruction or a whole verb ("just do what you can", "had a rough day").
DROPPED_SUBJECT = LOST_SUBJECT | frozenset(("am", "is", "are", "was", "were", "will", "might"))

# A statement with its subject left out puts "you" in front of the auxiliary it kept, and the
# auxiliary moves to the second person with it: "was making tea" -> "you were making tea".
SECOND_PERSON = {"am": ("you", "are"), "is": ("you", "are"), "are": ("you", "are"),
                 "was": ("you", "were"), "were": ("you", "were")}


def _with_you(words):
    """The subject a line that opens on an auxiliary left out, and the verb that goes with it."""
    if not words:
        return ["you"]
    first = (words[0].strip(".,!?;:") or "").lower()
    lead = SECOND_PERSON.get(first)
    if lead is not None:
        return list(lead) + list(words[1:])
    return ["you"] + list(words)


# The auxiliary in front of the "I" a person's "you" becomes: "are you" -> "am I",
# "were you" -> "was I". The rest already agree ("do I", "have I", "can I", "did I").
FIRST_PERSON_AUX = {"are": "am", "were": "was", "is": "am", "am": "am"}


def _first_person_aux(word):
    core = word.strip(".,!?;:")
    tail = word[len(core):]
    return FIRST_PERSON_AUX.get(core.lower(), core) + tail


def _flip(words, addressee=False):
    """First person the user used becomes second person when the bot says it back.

    With addressee, the person's "you" is the bot: it is "I" where the question makes it the
    subject ("can you suggest" -> "can I suggest") and "me" where it is the object ("did i tell
    you" -> "whether you told me").
    """
    out = []
    for index, word in enumerate(words):
        core = word.strip(".,!?;:")
        tail = word[len(core):]
        if addressee and core in ADDRESSEE:
            before = words[index - 1].strip(".,!?;:").lower() if index else ""
            if core == "you" and (not index or before in AUX or before in WH):
                if out:
                    # The auxiliary the "you" hangs on moves to the first person with it:
                    # "what were you saying" is "what I was saying", not "what I were saying".
                    out[-1] = _first_person_aux(out[-1])
                out.append(SUBJECT_YOU + tail)
            else:
                out.append(ADDRESSEE[core] + tail)
            continue
        out.append(FLIP.get(core, core) + tail)
    return out


# Said back inside a sentence, a person's line is easier to read with the contractions opened:
# "I'm nervous about Friday" is "you are nervous about Friday", not "you're nervous about
# Friday.". Only the words people type, not grammar.
EXPAND = {
    "i'm": "i am", "im": "i am", "i've": "i have", "i'd": "i would", "i'll": "i will",
    "it's": "it is", "that's": "that is", "there's": "there is", "what's": "what is",
    "we're": "we are", "they're": "they are", "you're": "you are", "he's": "he is",
    "she's": "she is", "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "can't": "cannot", "won't": "will not", "isn't": "is not", "aren't": "are not",
    "wasn't": "was not", "weren't": "were not", "haven't": "have not", "hasn't": "has not",
    "couldn't": "could not", "wouldn't": "would not", "shouldn't": "should not",
}


def your_words(text):
    """The person's own phrase in the second person, for a reply that says it back.

    A stock line drops the phrase straight into a sentence ("{X} keeps happening"), and the
    phrase is the person's own words: "comparing myself to others" reads as the bot's own
    trouble unless it is flipped to "comparing yourself to others", and "my keys" to "your
    keys". Only the person's first person moves; everything else is left as they said it.
    """
    words = str(text or "").split()
    return " ".join(_flip(words))


def _expand(text):
    """The line with its contractions opened and no full stop at the end."""
    words = [EXPAND.get(word.strip(".,!?;:").lower(), word) for word in str(text or "").split()]
    return " ".join(words).strip(" ,;:").rstrip(".")


def _as_text(value):
    """The reading gives `focus` as words or as a string; take either."""
    if isinstance(value, (list, tuple)):
        return " ".join(str(w) for w in value).strip()
    return str(value or "").strip()


# A question said back has to put its auxiliary behind the subject, so the subject has to be
# picked out whole: "is my boiler safe" is "whether my boiler is safe", not "whether my is
# boiler safe". A subject runs from a determiner to the word before the predicate.
PREDICATE = frozenset((
    "safe", "ok", "okay", "normal", "fine", "good", "bad", "better", "worse", "worth",
    "hard", "easy", "difficult", "available", "allowed", "legal", "dangerous", "broken",
    "working", "fixed", "cheap", "cheaper", "expensive", "possible", "true", "wrong",
    "open", "closed", "included", "covered", "needed", "sick", "ill", "dead", "alive",
    "serious", "urgent", "done", "ready", "likely", "fair", "free", "late", "busy",
    "hot", "cold", "warm", "healthy", "insured", "enough"))
PREP = frozenset(("to", "for", "in", "on", "at", "with", "from", "by", "about", "of",
                  "than", "after", "before", "during", "into", "over", "under", "out",
                  "up", "down", "when", "if", "because", "as", "so", "like", "near"))
# A unit is a quantity, not a thing to be on: "my budget is 6,000 pounds" is not about
# "the pounds". The units people weigh money, distance and shopping in.
MEASURE = frozenset((
    "pound", "pounds", "quid", "euro", "euros", "dollar", "dollars", "cent", "cents", "penny",
    "kilo", "kilos", "kilogram", "kilograms", "gram", "grams", "ounces", "ounce", "stone",
    "litre", "litres", "liter", "liters", "mile", "miles", "kilometre", "kilometres",
    "kilometer", "kilometers", "percent", "degree", "degrees", "minute", "minutes", "hour",
    "hours"))

# Words that stand between the auxiliary and the verb: "what did i just ask you".
ADVERB = frozenset(("just", "ever", "already", "actually", "really", "first", "originally",
                    "previously", "recently", "still", "also", "always", "never", "even"))


def _subjects_at(words, index, names=()):
    """True when words[index] can be the subject right after an auxiliary."""
    if index >= len(words):
        return False
    core = words[index].strip(".,!?").lower()
    return core in SUBJECTISH or core in names


def _np_end(words, start, most=3):
    """Where the subject after an auxiliary ends: "my boiler" in "is my boiler safe".

    A pronoun is the whole subject; a determiner opens a phrase that runs to the word before
    the predicate ("is the best way to cook it" keeps "the best way").
    """
    if start >= len(words):
        return start
    if words[start].strip(".,!?;:").lower() not in DETERMINERS:
        return start + 1
    end = start + 1
    while end < len(words) and end - start < most:
        core = words[end].strip(".,!?;:").lower()
        if core in AUX or core in WH or core in PREDICATE or core in PREP or core in ADVERB:
            break
        end += 1
    return max(end, start + 1)


def _embed(words, names=()):
    """The question with its auxiliary behind the subject, i.e. said back inside a sentence.

    "is my boiler safe" -> "my boiler is safe"; "does he need a booster seat" -> "he needs a
    booster seat"; "how long should i cook it" -> "how long you should cook it". A yes/no
    question keeps its auxiliary (the caller puts "whether" in front); a do/does/did question
    drops it and inflects the one verb instead, so nothing is inflected twice.
    """
    for index in range(len(words) - 1):
        aux = words[index].strip(".,!?;:").lower()
        if aux not in AUX:
            continue
        start = index + 1
        if not _subjects_at(words, start, names):
            continue
        end = _np_end(words, start)
        subject, tail = words[start:end], words[end:]
        # "how much would a service cost": with a question word and a modal in front, the last
        # word of the line is the verb, not the end of the subject. Nothing is moved when the
        # clause already has words after the subject to act as its verb.
        if aux in MODAL and index > 0 and len(subject) > 1 and not tail:
            subject, tail = subject[:-1], subject[-1:]
        if aux in ("do", "does", "did"):
            verb = 0
            while verb < len(tail) and tail[verb].strip(".,!?;:").lower() in ADVERB:
                verb += 1
            if verb < len(tail):
                tail[verb] = _agree(tail[verb], aux)
            elif len(subject) > 1 and subject[-1].strip(".,!?;:").lower() not in (
                    DETERMINERS | PREDICATE | MEASURE):
                # "how long does that take": the noun-phrase reader stops at a determiner and
                # then runs to the end, so "take" was taken for part of the subject and the
                # clause came out as "how long that take" - the shape a recap then reads out as
                # broken English ("you asked how long that take"). With nothing after the
                # subject, the last word of the phrase is the verb, and it is the one to inflect.
                subject, tail = subject[:-1], [_agree(subject[-1], aux)]
            return words[:index] + subject + tail
        return words[:index] + subject + [words[index]] + tail
    return words


POSSESSIVE = re.compile(r"([A-Za-z]+)(?:'s|\u2019s)\b")
# After these the "'s" is always "is" or "has", so it is never a possessive to put back:
# "it's a front loader" is "it is a front loader", not "it's is a front loader".
IS_NOT_POSSESSIVE = frozenset("""it that this there here what who he she one everyone nobody
somebody anyone""".split())


def _keep_possessives(clause, clean):
    """Put back the "'s" the reading drops: "my mum's birthday" is "your mum's birthday".

    The reading's focus words carry the noun without its possessive, so a line said back loses
    it ("your mum birthday"). Only the stems that really had one in the line get it back."""
    stems = {match.group(1).lower() for match in POSSESSIVE.finditer(clean or "")}
    if not stems:
        return clause
    words = str(clause or "").split()
    out = []
    for index, word in enumerate(words):
        core = word.strip(".,!?;:")
        # A stem at the end of the clause is not the possessive: "the kettle's just boiled" says
        # the kettle is boiling, and "we were on the kettle's" is not a thing.
        if index == len(words) - 1:
            out.append(word)
            continue
        if (core.lower() in stems and "'" not in core and "\u2019" not in core
                and core.lower() not in IS_NOT_POSSESSIVE):
            out.append(core + "'s" + word[len(core):])
        else:
            out.append(word)
    return " ".join(out)


def _truncated(clause, clean):
    """True when the reading's focus stops before the line does ("am i right about the boiler"
    leaves "am i"), so saying it back would lose the question."""
    if not clause or not clean:
        return False
    focus_words = clause.replace("?", "").lower().split()
    clean_words = clean.replace("?", "").lower().split()
    return len(focus_words) < len(clean_words) and clean_words[:len(focus_words)] == focus_words


# "6,000 pounds" is read back as "6000 pounds": the reading drops the comma, and a number said
# back differently from how it was typed reads like a different number. The form the person
# used is kept.
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text, clause):
    """The numbers in `clause` as the person typed them: "6000" -> "6,000"."""
    typed = {match.group(0).replace(",", ""): match.group(0) for match in NUMBER.finditer(text or "")}
    if not typed:
        return clause
    def keep(match):
        return typed.get(match.group(0)) or match.group(0)
    return re.sub(r"\d[\d,]*(?:\.\d+)?", keep, clause)


def restate(text):
    """The user's line said again inside a sentence, in their words, or None.

    A yes/no question becomes a "whether ..." clause, a wh-question is embedded
    ("how long should i cook it" -> "how long you should cook it"), and first person becomes
    second person. Statements are returned as they are, minus a leading "and"/"so".
    """
    reading = understand(text, {})
    clean = (reading.get("clean") or "").strip()
    clause = _as_text(reading.get("focus"))
    if not clause:
        clause = (reading.get("norm_text") or "").split(" | ")[-1].strip()
    if _truncated(clause, clean):
        # "am i right about the boiler" reads as the focus "am i", which leaves the question
        # without its subject; the line itself is the better thing to say back
        clause = clean
    if not clause:
        clause = clean
    # A fragment is not a thing to say back. Two shapes of it: a clause that starts with a
    # preposition ("it's a front loader, about five years old" -> "about five years old"), and
    # a piece of a word the line never had on its own ("my budget is 6,000 pounds" -> "000
    # pounds"). Both are caught by testing the first word against the words of the line, so
    # the whole line is said back instead.
    first_word = (clause.split() or [""])[0].strip(".,!?;:").lower()
    line_words = {word.strip(".,!?;:").lower() for word in clean.split()}
    if clean and (first_word in PREP or (first_word and first_word not in line_words)):
        clause = _expand(clean)
    words = _strip_lead(clause.replace("?", "").split())
    if not words:
        return None
    words = _with_wh(reading, words)
    # The reading may normalise "does he need" to "do he need"; the word the user typed decides
    # how the one verb is inflected ("whether he needs", not "whether he need").
    typed = [word.strip(".,!?;:").lower() for word in str(text or "").split()]
    typed_aux = next((word for word in typed if word in ("do", "does", "did")), None)
    if typed_aux:
        for index, word in enumerate(words):
            core = word.strip(".,!?;:").lower()
            if core in ("do", "does", "did") and core != typed_aux:
                words[index] = typed_aux + word[len(word.strip(".,!?;:")):]
                break
    first = words[0].strip(".,!?").lower()
    # A name the user typed can be the subject after the auxiliary ("is Lisbon warm in April").
    names = {(entity.get("text") or "").strip().lower() for entity in reading.get("entities") or []
             if isinstance(entity, dict)}

    if first in AUX or first in WH or first in DROPPED_SUBJECT:
        words = _flip(words, addressee=True)
        if first in DROPPED_SUBJECT and reading.get("kind") != "question":
            # A statement that opens on an auxiliary has lost its subject, not become a
            # question: "was making tea" is "you were making tea", not "whether was making tea".
            words = _with_you(words)
            said = " ".join(_embed(words, names))
            clause = said
        else:
            said = " ".join(_embed(words, names))
            clause = ("whether " + said) if first in AUX else said
    else:
        # A statement keeps its "you" unless the line's own doing landed on the bot: "i told you
        # my sister is called emma" said back was "you told you your sister is called emma", and
        # "sorry i snapped at you" was "sorry you snapped at you". `_to_the_bot` marks the one
        # "you" a verb of saying or a preposition makes the bot (told, called, at, with), so the
        # flip leaves it alone and it comes back as "me"; a "you" that is only the person being
        # spoken to - "i think you should rest", "a thank you card", "talk to me whenever you
        # like" - is not marked and stays as it was typed.
        clause = _from_the_bot(" ".join(_flip(_to_the_bot(" ".join(words)).split())))
    clause = _conditional(clause)
    # The reading drops a possessive, so a line said back reads "your mum birthday" where the
    # person wrote "my mum's birthday". `_keep_possessives` puts back only the "'s" the line had.
    clause = _keep_possessives(clause, clean)
    # "any tips?" has neither an auxiliary nor a question word once its "if" is expanded, so
    # there is nothing to say back: "you asked any tips" is not a sentence. Say nothing and let
    # the store pick an earlier ask that has a shape.
    if reading.get("kind") == "question":
        core = {word.strip(".,!?;:").lower() for word in clause.split()}
        opening = (clause.split() or [""])[0]
        if not (core & (AUX | WH)) and not _is_wh(opening) and "whether" not in core:
            return None
    clause = _numbers(text, clause)
    # A line said back that ends on "to be honest" or "haha" reads like a transcript:
    # "you said your sister is called meg to be honest". The tone goes; the line stays.
    clause = no_tone(clause)
    if not clause:
        return None
    return _restore_case(text, clause.strip(" ,;:")) or None


# The past tense of the verbs people use when they ask what they said: a table of words, not
# rules about lines. Anything else takes the regular ending.
PAST = {
    "say": "said", "tell": "told", "go": "went", "get": "got", "make": "made", "take": "took",
    "buy": "bought", "think": "thought", "see": "saw", "do": "did", "have": "had", "eat": "ate",
    "drink": "drank", "come": "came", "find": "found", "give": "gave", "know": "knew",
    "leave": "left", "pay": "paid", "put": "put", "read": "read", "run": "ran", "send": "sent",
    "sit": "sat", "speak": "spoke", "spend": "spent", "write": "wrote", "fly": "flew",
    "drive": "drove", "meet": "met", "hear": "heard", "feel": "felt", "keep": "kept",
    "sleep": "slept", "win": "won", "lose": "lost", "break": "broke", "choose": "chose",
    "begin": "began", "become": "became", "bring": "brought", "build": "built",
    "catch": "caught", "cost": "cost", "cut": "cut", "fall": "fell", "forget": "forgot",
    "hold": "held", "hit": "hit", "hurt": "hurt", "lend": "lent", "let": "let",
    "mean": "meant", "sing": "sang", "teach": "taught", "understand": "understood",
    "wear": "wore", "wake": "woke",
}


def _past(word):
    core = word.strip(".,!?;:")
    suffix = word[len(core):]
    if core in PAST:
        return PAST[core] + suffix
    if not core or not core[-1:].isalpha():
        return word
    if core.endswith("e"):
        return core + "d" + suffix
    if len(core) > 2 and core.endswith("y") and core[-2] not in "aeiou":
        return core[:-1] + "ied" + suffix
    return core + "ed" + suffix


def _agree(verb, aux):
    """The verb form that goes with the subject once "do/does/did" is dropped."""
    if aux == "did":
        return _past(verb)
    if aux == "does":
        return _third(verb)
    return verb


THIRD = {"have": "has", "be": "is", "do": "does", "go": "goes", "say": "says"}


def _third(verb):
    """A base verb in the third person: "need" -> "needs", "try" -> "tries", "have" -> "has".

    A do/does question takes the base form, so nothing here is already inflected except the
    irregulars; "need" ends in -ed and must still become "needs".
    """
    core = verb.strip(".,!?;:")
    suffix = verb[len(core):]
    low = core.lower()
    if not core or not core[-1:].isalpha():
        return verb
    if low in THIRD:
        return THIRD[low] + suffix
    if low in AUX:
        return verb
    if low.endswith(("s", "sh", "ch", "x", "z", "o")):
        return core + "es" + suffix
    if len(low) > 2 and low.endswith("y") and low[-2] not in "aeiou":
        return core[:-1] + "ies" + suffix
    return core + "s" + suffix


def _conditional(clause):
    """An "if" question is said back as what happens in that case: "if i stuff it" ->
    "what happens if you stuff it"."""
    if clause.startswith("if "):
        return "what happens " + clause
    return clause


def _restore_case(text, clause):
    """Put back the capitals the reading lowers: "priya" -> "Priya", "leeds" -> "Leeds"."""
    typed = [w.strip(".,!?;:") for w in str(text or "").split()]
    # The first word of a line is capitalised for being first, not for being a name.
    capitals = {w.lower() for w in typed[1:] if w[:1].isupper()}
    out = []
    for word in clause.split():
        core = word.strip(".,!?;:")
        out.append(_capital(core) + word[len(core):] if core in capitals else word)
    return " ".join(out)


def _capital(text):
    return text[:1].upper() + text[1:] if text else text


# A phrase that names a thing by its verb is not a thing to say back: "my bike chain keeps
# slipping" was read as "the keeps", and "the keeps" is not on anyone's table.
NOT_A_THING = frozenset(("keep", "keeps", "kept", "do", "does", "did", "get", "gets",
                         "got", "go", "goes", "going", "went", "want", "wants", "wanted",
                         "need", "needs", "needed", "try", "tries", "tried", "make",
                         "makes", "made", "start", "starts", "started", "stop", "stops",
                         "say", "says", "said", "think", "thought", "happen", "happens",
                         "happening", "thing", "things", "it", "something", "anything"))


# How far back an apology looks for the things on the table: the last dozen turns, which is a few
# subjects and the turns around them. Every prefix of a long chat read again is linear in the
# length of the chat, so an unbounded walk made the apology the most expensive line in the bot.
ON_THE_TABLE_TURNS = 12
# A run of prefixes that add nothing new means the older ones would say the same phrase again.
ON_THE_TABLE_MISSES = 3


def on_the_table(memory, limit=3):
    """The things the chat is holding, newest first, as phrases the bot can name.

    `about` answers with the one thing the conversation is on. A person apologising for the shape
    of the chat ("sorry i keep jumping about", "sorry for jumping between things") is asking,
    underneath it, whether the bot still has hold of what they brought - so this walks the same
    readings over the chat and collects the two or three things said, newest first: "your sister,
    the mince and your manager".

    Each phrase comes from `about` on the chat up to that turn, so this adds no second reading of
    a line; a phrase whose head is a verb ("the keeps") is dropped, and a repeated one is said
    once. Nothing here writes to memory or answers a turn.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return []
    # An apology is about the chat as it stands, so the things it is holding are the recent ones:
    # walking every prefix of a long chat cost 1.4 s at forty turns and 2.3 s at sixty to find the
    # same three phrases the last handful of turns give (deft-apricot, #4275). The window is wide
    # enough to hold a few subjects and the turns around them.
    recent = turns[-ON_THE_TABLE_TURNS:]
    out = []
    misses = 0
    for size in range(len(recent), 0, -1):
        shorter = dict(memory)
        shorter["turns"] = recent[:size]
        phrase = about(shorter)
        if not phrase:
            continue
        head = (phrase.split() or [""])[-1].strip(".,!?")
        if head in NOT_A_THING:
            continue
        if not _said_in_the_chat(phrase, recent[:size]):
            # "the shed roof leaks" was read as "the leaks" and "wanted to play the guitar" as
            # "the play": a phrase the chat never said is not a thing to offer back, and the
            # older turns still have a real one.
            continue
        if any(phrase.lower() == one.lower() for one in out):
            misses += 1
            if misses >= ON_THE_TABLE_MISSES:
                # Three prefixes in a row with nothing new: the chat has been on the same thing
                # for a while, and every older prefix would say it again.
                break
            continue
        out.append(phrase)
        misses = 0
        if len(out) >= limit:
            break
    return out


def _said_in_the_chat(phrase, turns):
    """True when the phrase's words sit side by side in something the person said.

    The phrase is built from the reading, so it can join words the chat only had apart ("the"
    from one place, "leaks" from another). A thing on the table has to be a thing they said:
    the check is a run of words, with the store's "your" put back to their "my".
    """
    words = str(phrase or "").lower().split()
    if not words:
        return False
    if words[0] == "your":
        words = ["my"] + words[1:]
    head = words[-1]
    for turn in turns:
        text = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(text, str):
            continue
        said = text.lower().split()
        run = len(words)
        for start in range(len(said) - run + 1):
            if said[start:start + run] == words:
                return True
        if head in VERB_WORDS:
            continue
        for entity in understand(text, {}).get("entities") or ():
            if entity.get("type") not in ("thing", "person"):
                continue
            if (entity.get("text") or "").lower() != head:
                continue
            if _said_as_a_state(head, text):
                # "im skint this month" is how they are, not a thing they brought to the chat:
                # the reading types the bare word as a thing, and the store offered "the skint"
                # back. A word that only ever arrives after "im" / "i feel" is a state.
                continue
            return True
    return False


# The words that stand in front of a state rather than a thing: "im very skint", "i feel a bit
# low". A word the chat only ever used after one of these is how they are.
COPULA = frozenset("""im i'm am is are was were been being feel feels felt feeling look looks
    seem seems get gets got getting become""".split())
STATE_FILLER = frozenset("""a an the bit little very really so quite pretty too that this
    honestly actually just totally proper still always kinda sorta dead well rather""".split())


def _said_as_a_state(head, text):
    """True when every time the chat said this word, it was after a copula: "im skint"."""
    said = text.lower().replace("\u2019", "'").split()
    seen = False
    for i, word in enumerate(said):
        if word.strip(".,!?;:\"'") != head:
            continue
        seen = True
        j = i - 1
        while j >= 0 and said[j].strip(".,!?;:\"'") in STATE_FILLER:
            j -= 1
        if j < 0 or said[j].strip(".,!?;:\"'") not in COPULA:
            return False
    return seen


# A word the reading knows as a verb is not a thing to offer back: "wanted to play the guitar"
# reads as "the play".
VERB_WORDS = VERB_FORMS | VERBISH


def in_a_list(phrases):
    """The things as one clause: "your sister, the mince and your manager".

    Empty when there is nothing to name, so a caller can tell a chat with something on the table
    from one without: the reply that lists the things is only honest when the store has them.
    """
    items = [str(one).strip() for one in (phrases or []) if str(one).strip()]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def topic_index(memory, skip=None):
    """Where in `user_lines` the newest line that names the thing we are on sits, or None.

    `about` reads the phrase out of that line; this is the same search, keeping the position so a
    caller can tell an ask about the thing we are on from one asked two subjects ago.
    """
    keep = []
    for index, (text, reading) in enumerate(user_lines(memory)):
        if _is_thin(reading) or _is_memory_line(reading):
            continue
        if _asks_about_the_chat(text, memory, skip):
            continue
        keep.append((index, text, reading))
    for require_entity in (True, False):
        for index, text, reading in reversed(keep):
            if require_entity and not _named_entities(reading):
                continue
            if not require_entity and (reading.get("intent") == "feeling"
                                       or reading.get("topic_own") == "feelings"):
                continue
            if _phrase_for(text, reading):
                return index
    return None


def last_ask(memory, skip=None, not_before=None):
    """The last thing the user asked, restated, or None.

    `not_before` is a `user_lines` position: an ask older than that was asked about something
    else, and saying it back beside the thing we are on now is a claim about them they never made
    ("we were on the bathroom — you asked how long it will take", from a cake two subjects ago).
    """
    lines = user_lines(memory)
    for index in range(len(lines) - 1, -1, -1):
        if not_before is not None and index < not_before:
            break
        text, reading = lines[index]
        if _is_memory_line(reading) or _asks_about_the_chat(text, memory, skip):
            continue
        if reading.get("kind") == "question" or "?" in text:
            said = restate(text)
            if said:
                return said
    return None


# A line that only says what the thing on the table is hands back a detail, not a subject:
# "the bathroom tap has been dripping for a week" then "its a mixer tap" then "what were we
# talking about?" came back as "You said its a mixer tap", which leaves the person no closer to
# what the chat was on. The detail belongs to the line before it, so that line is the answer.
# The reader is `detail.the_detail`, so the shapes are the ones the rest of the memory reads as
# details rather than a list of nouns kept here.
DETAIL_OPENER = re.compile(r"^\s*(?:its|it's|it is|thats|that's|that is|theyre|they're|"
                           r"they are|hes|he's|she's|shes)\s+", re.I)


def _only_a_detail(text):
    """True when the whole line is a detail about something already on the table."""
    line = " ".join(str(text or "").split()).strip(" .!?")
    rest = DETAIL_OPENER.sub("", line)
    if rest == line:
        return False
    got = detail.the_detail(line)
    if not got:
        return False
    words = lambda t: [w.lower() for w in str(t or "").split()]
    return words(got) == words(rest)


def last_said(memory, skip=None):
    """The last substantial thing the user told the bot, restated, or None.

    A closing is walked past: "night" after a chat about a knee is not what the chat was on,
    and handing it back as the last thing said ("you are off to bed") answers a question nobody
    asked while the real line sat one turn back.

    Where that walk stepped over a closing, the chat had already ended, and the thing the chat
    was on is the better answer ("we were on the deposit" rather than "you said work is mad at
    the moment", which is only what was said just before they went to bed). So nothing is handed
    back then, and the caller falls through to the subject it already knows.
    """
    said, past_a_closing = last_said_past_closings(memory, skip)
    if past_a_closing and said and about(memory, skip):
        return None
    return said


def last_said_past_closings(memory, skip=None):
    """The last thing said, plus whether a closing had to be walked past to reach it.

    A recap that had to step over "ok goodnight" is answering about a chat that ended, so the
    subject the chat was on ("we were on the deposit") is the better thing to hand back than the
    last line before the closing. A recap with nothing to step over answers with the last line.
    """
    past_a_closing = False
    for text, reading in reversed(user_lines(memory)):
        if _is_thin(reading) or reading.get("kind") == "question" or _is_memory_line(reading):
            continue
        if signs_off(text):
            past_a_closing = True
            continue
        if _asks_about_the_chat(text, memory, skip):
            continue
        if _only_a_detail(text):
            continue
        said = restate(text)
        if said:
            return said, past_a_closing
    return None, past_a_closing


def named(memory, limit=2):
    """The things and places the user has named, newest first, each used once."""
    out = []
    for _text, reading in reversed(user_lines(memory)):
        for entity in reading.get("entities") or []:
            if not isinstance(entity, dict):
                continue
            name = (entity.get("text") or "").strip()
            if entity.get("type") == "thing" or not name or name.lower() in WEAK:
                continue
            if name.lower() in FLIP or len(name.strip(".,")) <= 2:
                continue
            if name.lower().startswith("my "):
                name = "your " + name[3:]
            if name.lower() in (n.lower() for n in out):
                continue
            out.append(name)
            if len(out) >= limit:
                return out
    return out


# A line that only asks for the verdict back. "is that alright" / "will that work" / "that ok?"
# names nothing of its own: it is the bot's own last answer it is asking about, and answering it
# with the ack pool ("Sounds good.") is the bot agreeing with itself when it had just said no.
CHECK_VERDICT = re.compile(
    r"^(?:(?:and|but|so|ok(?:ay)?|right|oh|hmm|well|then)[, ]+)*"
    r"(?:(?:is|will|would|does|do|was)\s+(?:that|it|this)"
    r"(?:\s+be)?"
    r"|(?:that|it|this)(?:'s|s|\s+is)?)"
    r"\s+(?:alright|all right|ok|okay|fine|safe|allowed|work|works)"
    r"(?:\s+for (?:me|us|him|her|them))?"
    r"(?:\s+(?:though|then|now))?"
    # The same check said as a doubt about the bot rather than about the thing: "are you sure",
    # "you sure about that", "really?", which after a verdict ask for it to be said again.
    r"|^(?:(?:and|but|so|ok(?:ay)?|right|oh|hmm|well|then)[, ]+)*"
    r"(?:are|r)\s+(?:you\s+)?(?:really\s+)?sure"
    r"(?:\s+(?:about|of)\s+(?:that|it|this))?$"
    r"|^(?:you\s+)?(?:really\s+)?sure(?:\s+(?:about|of)\s+(?:that|it|this))?$", re.I)

# The bot's last answer when it gave a verdict: "No: a satay is made with nuts, and that is off the
# table for you. ...", "Yes: ... have no nuts in them, so they are fine for you.", "No - the part
# you asked about is the harmless kind. ...".
VERDICT_SAID = re.compile(
    r"^(?:still\s+(?:a\s+)?)?(yes|no|afraid not|no, sorry|no, afraid not)\s*[:\u2014\u2013-]\s*(.+)$",
    re.I | re.S)

# The frames a held verdict is said in. A second check in a row rotates to the next one: a person
# who asks twice because they did not believe it is entitled to an answer, not to the same
# sentence again.
NO_FRAMES = ("Afraid not \u2014 {reason}.", "Still a no \u2014 {reason}.",
             "No, sorry \u2014 {reason}.")
YES_FRAMES = ("Yes \u2014 {reason}.", "Still yes \u2014 {reason}.")
# What the bot's last line opened with (its own held frame, not the module's "No:" verdict) and the
# frame taken next: a check asked twice is answered, not parroted.
NO_USED = (("afraid not", 1), ("still a no", 2), ("no, sorry", 0))
YES_USED = (("yes \u2014", 1), ("still yes", 0))


def checking_the_verdict(text, memory):
    """The verdict said again, or None.

    "is that alright" after "No: a satay is made with nuts, and that is off the table for you"
    got the ack pool: *Sounds good.* The bot agreed with a plan it had just ruled out, and the
    person is left thinking the satay is fine. A check with no subject of its own is about the
    answer the bot just gave, so the answer holds: the same direction, and the reason it gave,
    in a sentence short enough to be an answer to a yes-or-no question rather than a repeat.

    Only a line that names nothing and asks nothing else gets here, and only when the bot's last
    line was a verdict with a reason in it. Everything else is left to the modules that answered
    it before, so this can add a reply and never take one away.
    """
    if not isinstance(memory, dict):
        return None
    said = " ".join(str(text or "").lower().split()).strip(" .!?,")
    if not said or len(said.split()) > 9 or not CHECK_VERDICT.match(said):
        return None
    turns = memory.get("turns")
    last = ""
    if isinstance(turns, list) and turns:
        last = str(turns[-1].get("bot") or "").strip()
    verdict = VERDICT_SAID.match(last)
    if not verdict:
        return None
    reason = _first_clause(verdict.group(2))
    if not reason:
        return None
    # "Afraid not" is this function's own refusal said back, so a third check in a row holds too.
    if verdict.group(1).lower() == "yes":
        return _next_frame(YES_FRAMES, YES_USED, last).format(reason=reason)
    return _next_frame(NO_FRAMES, NO_USED, last).format(reason=reason)


# A line that only asks whether the answer on screen is right. "is that right", "is that true",
# "is that correct" name nothing of their own: they are the bot's own last answer being checked,
# and the ack pool answered them with "Alright then - good luck with it." after a raw chicken keeps
# "1 to 2 days in the fridge" - which neither confirms nor corrects, so the person is left holding
# a fact they were unsure about.
CHECK_A_FACT = re.compile(
    r"^(?:(?:and|but|so|ok(?:ay)?|right|oh|hmm|well|then|thanks|ta|great|good|nice)[, ]+)*"
    r"(?:"
    r"(?:is|was|are)\s+(?:that|it|this|they|those)"
    r"(?:\s+(?:really|actually|definitely|all|exactly|still))?"
    r"\s+(?:right|true|correct|accurate|the right (?:answer|thing)|how it works|what you meant)"
    r"(?:\s+(?:then|though|now|yeah|yes|or not|or what))?"
    r"|(?:that|it|this)(?:'s|s|\s+is)?\s+(?:right|true|correct|accurate)"
    r"|(?:right|correct|true)"
    r")\s*[?.!]*$", re.I)
# The answer on screen is not a fact to confirm when it is a doubt or a hedge: "i'm not sure about
# that one" is the bot saying it does not know, and "that's right - i'd rather not guess" is not a
# confirmation of anything.
NO_FACT_SAID = re.compile(
    r"^(?:i'm not sure|i am not sure|i don't know|i do not know|i'd rather not guess|"
    r"that's beyond what i know|not something i know)", re.I)
# The frames a checked fact is said in, moving on from the one used last time so a second check is
# answered rather than parroted.
FACT_FRAMES = ("That's right.", "Yes — that's the usual guidance.",
               "That is the answer I have, yes.", "That's how I understand it too.",
               "Yes — that's the standard advice.", "That's right, as far as I know.")
# What the bot says when it is holding a thing, noting it, or nodding: none of it is a fact the
# person could be checking, so "is that right" after one of them keeps the reply it had.
NOT_A_FACT = re.compile(
    r"(?:^|\b)(?:i'll remember|i will remember|noted\b|got it\b|alright then|sounds good|"
    r"fair enough|i'm listening|say more|tell me more|back on the table)", re.I)


def checking_a_fact(text, memory):
    """The answer on screen confirmed, or None.

    Only for a line that asks nothing else, and only when the answer on screen is a fact: the
    turn before it was answered from a knowledge entry, or it is a confirmation this function
    itself gave (a check asked twice is answered, not parroted). A store line, an echo or a
    question back is not a fact to confirm, so those lines keep the reply they had.

    The answer is not read out again. The arbiter passes over a reply that says the last answer
    again behind a nod, and rightly: the person has those words in front of them. What they are
    asking for is the bot standing behind them.
    """
    if not isinstance(memory, dict):
        return None
    said = " ".join(str(text or "").lower().split()).strip(" .!?,")
    if not said or len(said.split()) > 7 or not CHECK_A_FACT.match(said):
        return None
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return None
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    answer = " ".join(str(last.get("bot") or "").split())
    if not answer or answer.endswith("?"):
        return None
    if not _fact_from(answer):
        if len(answer.split()) < 8 or NO_FACT_SAID.match(answer) or NOT_A_FACT.search(answer):
            return None
        from . import topics  # lazy: the store reads both, and topics reads the knowledge base
        if topics.an_entry_for(str(last.get("user") or "")) is None:
            return None
    return _a_frame_not_said(FACT_FRAMES, memory)


def _fact_from(answer):
    """True when the answer on screen is a confirmation this function gave a turn ago."""
    low = answer.lower()
    return any(low.startswith(frame.lower().rstrip(".")) for frame in FACT_FRAMES)


def _a_frame_not_said(frames, memory):
    """The first of `frames` the bot has not said in this conversation yet.

    A check asked a fourth time in a row would otherwise come back to the frame used first, and
    the arbiter passes over a reply already on screen: the person would get the whole answer read
    out again instead of a confirmation.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    said = [" ".join(str(turn.get("bot") or "").lower().split())
            for turn in (turns or []) if isinstance(turn, dict)][-6:]
    for frame in frames:
        stem = frame.lower().rstrip(".")
        if not any(line.startswith(stem) for line in said):
            return frame
    return frames[0]


def _next_frame(frames, used, said):
    """The frame this verdict is said in, moving on from the one the bot used last time."""
    stem = " ".join(str(said or "").split()).lower()
    for lead, going_to in used:
        if stem.startswith(lead):
            return frames[going_to]
    return frames[0]


def _first_clause(said, limit=13):
    """The first reason in a verdict: "a satay is made with nuts" out of a two-sentence answer."""
    said = " ".join(str(said or "").split())
    if not said:
        return ""
    cut = re.split(r"(?<=[.!?])\s|;\s|,\s+(?:and|so|but)\s", said, maxsplit=1)[0]
    cut = cut.strip(" .,;:")
    words = cut.split()
    if len(words) > limit:
        cut = " ".join(words[:limit]).rstrip(",;:")
    return cut


# --- the thing they had today, and the ask about how it went -----------------------------------
# "i had an interview today" / "how did it go" was answered with advice on how to prepare for an
# interview, one line after the person said it was already over: the ask has no subject of its
# own, and the topic ("interview") was answered by the knowledge base as though it were a new
# question. "did it go well" was a search hedge, and "how did it go?" with a question mark was a
# hedge too. A friend says the one thing only the person can answer, and asks them.
#
# Every shape the ask is typed in, with the person left off the front ("so", "and", "ok") and a
# tag on the end ("then", "in the end"), fits WENT_ASK; nothing else does, so a line that asks
# how something is done or how long it takes is left to the modules that answer it.
WENT_ASK = re.compile(
    r"^(?:(?:so|and|then|but|well|ok|okay|right|oh|ah|hey|great|good|nice|hmm+|anyway|go on|"
    r"aw+|yes|yeah)\b[\s,]*)*"
    r"(?:"
    r"how\s+(?:did|does|has|have|was|were)?\s*(?:it|that|things|everything)\s*"
    r"(?:go|gone|been|turn\s+out|work\s+out)?(?:\s+(?:ok|okay|well|fine|alright|good|bad))?"
    r"|how(?:'s|d|s)?\s+(?:it|that)\s+(?:go|gone|been|turn\s+out)"
    r"|how'd\s+(?:it|that)\s+go"
    r"|did\s+(?:it|that|things|everything)\s+(?:go|turn\s+out)"
    r"(?:\s+(?:ok|okay|well|fine|alright|good|bad))?"
    r"|how\s+(?:did|was|were)\s+(?:the|your|my|that)\s+(?P<thing>[a-z][a-z' -]{1,40}?)"
    r"(?:\s+(?:go|gone|turn\s+out))?"
    r")"
    r"(?:[\s,]*(?:then|though|today|tonight|in the end|honestly|please|anyway|huh|so far))*"
    r"[\s?.!]*$", re.I)
# A piece of time is not the thing that happened: "how was your day" and "how was your weekend"
# are the bot's own day, asked of the bot, and the composer has them.
NOT_THE_THING = frozenset((
    "day", "days", "week", "weeks", "weekend", "weekends", "evening", "evenings", "morning",
    "mornings", "afternoon", "night", "nights", "holiday", "holidays", "break", "time",
    "weather", "sleep"))
# Not everything a person "had" is a thing with a verdict pending. A birth, a loss, bad news and a
# bad day are whole events, and a fall, a panic attack or a seizure is a moment their body had: no
# one answers "how did the panic attack go", and asking takes away an answer they were given ("i had
# a panic attack today" got the panic-attack card, and this ask in its place is worse).
#
# Two fences, because the same word is a name for one person and a state for another: "my first day
# at the new job was today" is a day worth asking about, and "a really bad day" is not. The words
# here are never a thing with a name, wherever they sit; the words in the second set are only that
# when they are all there is - the word the thing ends on - so a "day" with a name in front of it
# ("first day") keeps its question, and a day on its own does not.
NEVER_A_THING_THAT_WENT = frozenset((
    "baby", "birth", "stillbirth", "miscarriage", "loss", "death", "passing", "funeral",
    "news", "fall", "tumble", "panic", "attack", "seizure", "fit", "convulsion", "bleed",
    "bleeding", "symptom", "diagnosis", "result", "fever", "pain", "ache", "flu", "bug",
    "infection", "migraine", "headache", "period", "cramp", "rash", "shock", "scare", "fright"))
_A_STATE_ITSELF = frozenset((
    "day", "week", "night", "morning", "afternoon", "evening", "weekend", "holiday", "break",
    "time", "cold", "temperature", "argument", "row", "cry", "crying", "upset", "tiredness"))
# The words in front that turn a thing into a description of one: "some bad news", "a really bad
# day". What follows is how it was, not what it was, and "how did the some bad news go" is not a
# sentence. "lovely" and "nice" are not here: "i had a lovely walk today" is a walk.
# A word that names an occasion rather than describing one: "my first day at the new job" is a day
# with a name, and the ask about it is a good one.
_A_NAME_FOR_IT = frozenset(("first", "second", "third", "last", "next", "final", "new", "other"))
_A_DESCRIPTION = frozenset(("some", "any", "such", "really", "very", "quite", "rather", "proper",
                            "bit", "lot", "few", "another", "little", "bad", "awful", "terrible",
                            "rough", "dreadful", "horrible", "hard", "tough", "rotten"))
# The words that say when it happened. A thing they are about to do is not one they can report on,
# so the report carries a past time and not a plan ("i have an interview tomorrow").
HAPPENED = re.compile(r"\b(?:today|tonight|this\s+(?:morning|afternoon|evening)|last\s+night|"
                      r"yesterday|earlier)\b", re.I)
# "i had an interview", "we went for a meal", "i did my exam": the verb that says it is over.
HAD_IT = re.compile(r"\b(?:i|we)\s+(?:had|went\s+(?:for|to|on)|did|took|sat|attended|started|"
                    r"finished|gave)\s+(?:an|a|my|our|the)?\s*(?P<thing>[a-z][a-z' -]{1,40})", re.I)
# "my first day at the new job was today": the thing leads and the time closes the line.
IT_WAS = re.compile(r"\bmy\s+(?P<thing>[a-z][a-z' -]{2,40}?)\s+(?:was|were|is|are)"
                    r"(?:\s+(?:today|tonight|yesterday|this\s+[a-z]+|last\s+night|earlier))?"
                    # "... was today and it was awful": the line goes on to say how it went, and
                    # that is the same thing they had, not a different one.
                    r"(?:\s*[,;]?\s*(?:and|but|so)\b.*)?\s*$",
                    re.I)
# The words a thing ends at: the time it happened, and the clause said after it.
THING_END = frozenset(("today", "tonight", "yesterday", "this", "last", "and", "but", "so",
                       "then", "which", "because", "when", "where", "it", "that", "was", "were",
                       "is", "at", "in", "on", "with", "for", "to", "after", "before", "earlier"))
# "i had a go at my boss today": the thing said back has to be a thing, and "have a go", "have a
# look", "have a word" are the doing of something, not an event with a name. "how did the go go"
# is not a sentence anyone says, so the report is left to the modules that read how it landed.
_A_THING_DONE = frozenset((
    "go", "try", "look", "glance", "peek", "chat", "talk", "word", "think", "laugh", "cry",
    "moan", "nag", "row", "argument", "argue", "fight", "lie", "bath", "shower", "wash",
    "rest", "nap", "snooze", "kip", "sleep", "sit", "drink", "bite", "cuddle", "listen",
    # "i had a wobble", "i had a turn": how it went for them, not a thing with a name.
    "wobble", "turn", "moment", "blip", "dip"))
# A phrasal verb keeps its particle ("my wart frozen off"), and a thing that ends in one is the
# doing of something again: "how did the wart frozen off go" is not a sentence.
THING_PARTICLE = frozenset(("off", "out", "up", "down", "away", "back", "over", "round",
                            "around", "through", "along", "about", "in", "on"))
# "i had my hair cut today" is not the thing "hair cut": the participle says the thing was done,
# so what they had is whatever is in front of it. "blood test done" is the blood test.
DONE_WORDS = frozenset(("cut", "put", "set", "shut", "hit", "let", "cost", "hurt", "burst",
                        "spread", "rid", "shed", "split", "stuck", "sent", "built", "frozen"))


def _a_done_word(word):
    """Whether this word is a participle, so what follows "i had" is the doing, not the thing."""
    return word.endswith("ed") or word in DONE_WORDS or word in IRREGULAR_PARTICIPLES
# The frames the ask is answered in: the person's own news handed back to them, in the words the
# thing was named with. They vary, and none of them is advice about the thing.
WENT_FRAMES = ("So how did the {thing} go? You'd know before I would.",
               "You tell me \u2014 how did the {thing} go?",
               "Go on then: how did the {thing} go?",
               "How did the {thing} go? I only know what you tell me.")
WENT_FRAMES_NO_THING = ("Then you'll have to tell me \u2014 how did it go?",
                        "Go on then, how did it go?",
                        "I can't see your day from here. How did it go?")
# The same ask a second time: the bot has already said it cannot see the person's day, so the reply
# says it plainly rather than asking again - and rather than falling through to advice about the
# thing they have already done ("how did it go" twice was answered with how to prepare for an
# interview).
WENT_AGAIN = ("I've no way of seeing it from here \u2014 you'll have to tell me.",
              "Still yours to tell me: how did it go?",
              "I can't see it from where I am, so tell me how it went.")
# The report already said how it went ("i had a scan yesterday and it was fine"). Asking again is
# the bot not listening, so the verdict is answered instead of the question being put back.
A_VERDICT = re.compile(
    r"\b(?:it|that|they)\s+(?:was|were|is|are)\s+(?P<v>fine|good|great|ok|okay|all right|alright|"
    r"lovely|brilliant|awful|terrible|horrible|dreadful|rubbish|a disaster|a nightmare)"
    r"|\bwent\s+(?P<w>well|fine|badly|great|ok|okay|awful|terrible)", re.I)
_WENT_WELL = frozenset(("fine", "good", "great", "ok", "okay", "all right", "alright", "lovely",
                        "brilliant", "well"))
WENT_TOLD_WELL = ("Good \u2014 you told me it was {v}. That's the main thing.",
                  "{V} is a relief, then. Tell me more if there's more in it.",
                  "So it went {v}. Nothing for me to ask there.")
WENT_TOLD_BAD = ("Sorry it went {v}. What happened?",
                 "{V} \u2014 that's rough. Tell me the worst bit, if you want to.",
                 "That's a rotten one to have had. What went wrong?")


def _the_verdict_they_gave(line):
    """The word the report used for how it went, or "".

    "i had a scan yesterday and it was fine" has already answered the ask, so the reply would be
    asking the person to say again what they just said.
    """
    low = " ".join(str(line or "").lower().split())
    match = A_VERDICT.search(low)
    if not match:
        return ""
    return (match.group("v") or match.group("w") or "").lower()


def _the_thing_they_had(line):
    """The thing the line says they had, did or went to, in a few words, or "".

    "i had an interview today" is "interview", "i had a dentist appointment today" is "dentist
    appointment", and "my first day at the new job was today" is "first day at the new job".
    """
    low = " ".join(str(line or "").lower().split())
    if not low or not HAPPENED.search(low):
        return ""
    for pattern in (IT_WAS, HAD_IT):
        match = pattern.search(low)
        if not match:
            continue
        words = []
        for word in match.group("thing").split():
            if word in THING_END:
                break
            words.append(word)
        thing = " ".join(words).strip(" ,;:-")
        if not thing or thing in NOT_THE_THING:
            continue
        if words and words[0] in _A_THING_DONE:
            continue
        # A state they were in is not an event with a verdict: "i had a really bad day today",
        # "i had a fall this morning", "i had some bad news today".
        if any(word in NEVER_A_THING_THAT_WENT for word in words):
            continue
        if words[-1] in _A_STATE_ITSELF and not any(word in _A_NAME_FOR_IT for word in words):
            continue
        if any(word in _A_DESCRIPTION for word in words):
            continue
        if any(word in THING_PARTICLE for word in words):
            continue
        # "i had my blood test done today" is the blood test they had, so a participle on the end
        # is dropped; one in the middle ("hair cut short") leaves nothing that is a thing.
        if words and _a_done_word(words[-1]):
            words = words[:-1]
            thing = " ".join(words).strip(" ,;:-")
            if len(words) < 2 or thing in NOT_THE_THING:
                continue
        elif any(_a_done_word(word) for word in words[:-1]):
            continue
        return thing
    return ""


def went(text, memory):
    """The reply to "how did it go" after they told the chat about a thing they had today.

    The ask is about the person's own day, and the bot was not there: the honest reply is to ask
    them. Only their own report of a thing that is over can be the subject, and only the ask
    shapes above are read, so a how-to ("how did you fix the boiler", "how do i get there") is
    left to the modules that answer it. When the bot's own last line was already this question,
    it is not asked a second time.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    said = " ".join(text.lower().split()).strip(" ?.!,")
    match = WENT_ASK.match(said)
    if not match:
        return None
    turns = [turn for turn in _turns(memory) if isinstance(turn, dict)]
    if not turns:
        return None
    asked_before = _asked_already(turns[-1].get("bot") or turns[-1].get("reply"))
    thing = ""
    verdict = ""
    for turn in reversed(turns):
        thing = _the_thing_they_had(turn.get("user"))
        if thing:
            verdict = _the_verdict_they_gave(turn.get("user"))
            break
    asked_about = (match.groupdict().get("thing") or "").strip()
    if asked_about:
        # The line names the thing itself ("how did the interview go"), so the person's own word
        # is said back - but only when the chat has heard of that thing happening, and only when
        # that word is a thing: "how did the go go" is not a question about anything.
        if not thing or asked_about in NOT_THE_THING or asked_about in _A_THING_DONE:
            return None
        thing = asked_about
    if not thing:
        return None
    if verdict:
        # They have already said how it went; asking again would be worse than useless.
        frames = WENT_TOLD_WELL if verdict in _WENT_WELL else WENT_TOLD_BAD
        return pick([frame.format(v=verdict, V=verdict.capitalize()) for frame in frames], memory)
    if asked_before:
        return pick(list(WENT_AGAIN), memory)
    return pick([frame.format(thing=thing) for frame in WENT_FRAMES], memory)


def _asked_already(reply):
    """Whether the bot's own line was this question, so the chat does not ask it twice."""
    said = " ".join(str(reply or "").lower().split())
    if not said.endswith("?"):
        return False
    return bool(WENT_ASK.match(said.rstrip("?").strip())) or bool(
        re.search(r"how (?:did|was) (?:it|that|the|your)\b.*\bgo\b", said))
