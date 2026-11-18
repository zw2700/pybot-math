"""What the conversation is about: the current topic and the topics before it.

The conversation lane owns this. bot/modules/memory_store.py writes it in observe(), so every
lane can read it:

- memory["topic"]: {"turn", "text", "words"} for what the user is talking about now. "text" is
  the user's own line, so a follow-up can be understood in context; "words" are its content
  words, for matching.
- memory["topics"]: every topic so far, oldest first, so "back to the laptop" and "which city
  did I say first" can be answered.
- memory["return_to"]: set when the user clearly goes back to an earlier topic.

Helpers for answer modules (import bot.memory as memory):
- memory.current(memory) -> the topic record or None
- memory.expand(text, memory) -> the line, plus the topic in brackets when it is a follow-up
- memory.is_follow_up(text, memory) -> True for "how long will it take?", "and if I stuff it?"
"""
import re

from ..understanding import lexicon
from ..understanding.kinds import NEGATIVE, POSITIVE
from .filler import without_the_shrug
from . import quotes as quoted

WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

STOPWORDS = frozenset("""
a an the and or but if so of to in on at for with without about as by from into over after
before between during out up down off again further then once here there when where why how all
any both each few more most other some such no nor not only own same than too very can could
should would will shall may might must do does did doing have has had having am is are was were
be been being i me my we us our you your he him his she her it its they them their this that
these those what which who whom whose
i'm i've i'll i'd don't doesn't didn't can't won't isn't aren't wasn't weren't it's that's
# A pronoun typed without its apostrophe is still a pronoun, and it is not a thing a line is
# about: "shes 84, what can we do" is "she is 84" with the apostrophe left off, and read as a
# word of its own "shes" stems to "sh", which no entry in the world is about. So the line was
# read as naming a subject of its own, the entry the chat was already on was dropped as not
# being about it, and a follow-up about the falls answer went to a search hedge - while the same
# line written "she is 84" was answered. The set is pronouns only: a word like "shed" or "his"
# that is spelt the same with or without an apostrophe is left alone.
shes hes theyre theyve theyll theyd himself herself themselves itself
like just really quite maybe perhaps also still even much many lot lots want needs need get got
make makes okay ok right well yeah one ones youd youre im ive id ill
actually honestly literally basically simply truly
""".split())

ACKS = frozenset("""
ok okay k kk cool nice great good yeah yep yes no nah nope lol haha ha hmm sure right wow oh ah yum
aha eh meh same thanks thx ty cheers ta fine alright aw brilliant perfect awesome interesting
true agreed indeed not much nothing much idk dunno maybe probably sounds sound idea love lovely
definitely exactly fair enough makes sense got it see later
""".split())

GREET = frozenset("hi hello hey hiya morning evening afternoon night bye goodbye".split())

REFERRING = frozenset("""
it its that this these those they them there their one ones he she him her his other same
""".split())

# The words a line uses to ask where to begin in an answer rather than to name a subject: "where
# do i start", "what should i do first", "what next". They are common enough in a record's own
# words that a bare one of them is no evidence the chat went back to that record.
ORDERING = frozenset("""
start starts started starting first next then else begin beginning later more again
""".split())

# A part of the thing in hand points back at it as hard as "it" does: "can i freeze the leftovers"
# after a chicken is about that chicken's leftovers, not about freezing as a subject. Without this
# the question opened a new subject and the chicken's own answer for "is that bad" was lost, while
# "can i keep the leftovers" stayed on the chicken because "keep" is no word the entries fight
# over - the same shape answering two ways. It has to be *the* leftovers and not a leftover word:
# a bare "bones" or "cores" is the subject of somebody's own question ("can i give the bones to
# the dog"), and only a part named as this one's - with a determiner - is a part of the thing in
# hand.
# "what about tea" after a question about water is the same question asked of another thing, not
# a new subject: the answer it wants is the one just given with tea in it ("tea counts towards
# it"). Leaving it as a new topic handed the thread to whatever else the tea line reaches, which
# was a dinner suggestion.
ABOUT_ANOTHER = re.compile(r"\b(?:what|how) about\b")


PART_OF_THE_ONE = re.compile(
    r"\b(?:the|these|those|my|your|its)\s+(?:leftovers?|rest|remainder|extras?|offcuts?|"
    r"trimmings|scraps?|peels?)\b|\bwhat(?:'s| is) left\b")

CONTINUATION_START = frozenset("""
and so but then also what how why when where which who whom whose can could should would will
is are do does did have has was were if
""".split())

# A property question ("how long per kilo?", "what temperature?") can carry one or two content
# words of its own ("per kilo") and still be about the thing the conversation is on.
# The words a property ask uses to name the detail it wants. With these taken out, a line that
# has nothing left is asking that detail of the thing the chat is on ("what temperature" after a
# cake); one with words left is asking about the thing those words name.
MEASURE_WORDS = frozenset("""
long much many far often hot warm temperature temp temps degrees centigrade fahrenheit
time heat size price setting what which
""".split())

# The words a line names a property with, and nothing else: "temp" and "degrees" are as much a
# measure as "temperature" is, and a line that says "what temp" after a sponge is asking about the
# sponge. It was read as a new subject and answered with body temperature, because the list had
# the long word and not the short one people actually type.
PROPERTY = re.compile(r"\bhow (?:long|much|many|far|often|hot|warm)\b|"
                      r"\bwhat (?:temperature|temp|temps|degrees|centigrade|fahrenheit|"
                      r"time|heat|size|price|setting)\b|"
                      r"\bper (?:kilo|kg|500g|person|head|each)\b")

# A line that asks which one of the thing to get leans on the thing just named, whatever else it
# says: "what kind should I get?" after a bike, "what breed?" after a dog, "which one would you
# get?" after a coffee machine. It names no thing of its own, so it is never a new topic.
KIND_ASK = re.compile(r"\b(?:what|which)\s+(?:kind|sort|type|breed|brand|model|make|size|one)\s*\?"
                      r"|\bwhich\s+(?:one|brand|model|make)\b"
                      r"|\bwhat\s+(?:kind|sort|type|breed)\b")
SWITCHERS = ("actually", "never mind", "nevermind", "by the way", "btw", "back to", "anyway",
             "new question", "different question", "forget that", "instead", "changing the subject",
             # The same job said as an apology: "sorry, it's a funeral", "my mistake, it's in
             # august". Whether the subject really changed is still decided by _only_details,
             # so a corrected date keeps the wedding and a corrected occasion does not.
             "sorry", "apologies", "my mistake", "correction", "no wait")

# "ok back to the boiler", "anyway, the laptop", "as i was saying, Rome", "sorry, back to the
# radiator": the line starts with a few chatty words and then names a topic already discussed.
# The line has to start that way, so "we're going back to London tomorrow" stays a statement.
RETURN_LEAD = re.compile(
    r"^(?:(?:ok|okay|so|right|anyway|sorry|and|but|well|oh|then|great|nice|yes|yeah|hmm|aha|ah)"
    r"[\s,]*)*(?:back\s+to|as\s+i\s+was\s+saying|as\s+i\s+said|coming\s+back\s+to|"
    r"where\s+were\s+we(?:\s+on)?|return(?:ing)?\s+to)\b\s*")

# "anyway, the laptop" names the topic again without saying so: a chatty lead-in and then a bare
# noun phrase, no verb. Only with a determiner, so "anyway my mum called" stays a new topic.
CASUAL_LEAD = re.compile(
    r"^(?:(?:ok|okay|so|right|anyway|and|well|oh)\s*[,\s]\s*)*(?:anyway\s*[,\s]\s*)")
CASUAL_OPEN = frozenset("a an the my our your that this those these".split())
CASUAL_VERB = frozenset("""
is are was were am be been being has have had got get gets went go goes called calls said say
says told tell tells keeps keep kept needs need wants want likes like loves love works work
doing does did do can could should would will
""".split())

# "back to work tomorrow" names a time, not a topic: the return has to name a thing, so a verb
# or a day of the week in it means the line is a statement about coming up, not a return.
RETURN_TIME = frozenset("""
tomorrow today tonight now later soon monday tuesday wednesday thursday friday saturday sunday
week weekend month year morning afternoon evening night
""".split())

# A line that asks something after the return marker is a request for an answer, not a bare
# "we were on this": the answer modules handle it with the topic put back in front.
RETURN_ASKS = frozenset("""
what how why when where which who whom whose can could should would will shall is are was were
am do does did have has had if whether
whats hows whys whens wheres whichs whos
""".split())


# Typing drops the apostrophe from "what's" and "how's", so "whats" is how the question word is
# usually written: "back to lisbon, whats good to see" names Lisbon and asks about it, but read as
# a word of its own "whats" was not the question word the split looks for, so the whole clause
# came back as the thing went back to ("lisbon whats good to see", four words, so nothing at all)
# and the line was not read as a return. The answer Lisbon got on turn one then came back word for
# word six turns later instead of being framed as the return it was. The forms are the question
# words a person writes with the apostrophe missing, so a shape learnt here is read everywhere the
# ask words are.
RETURN_ASKS = RETURN_ASKS | frozenset(
    word + "s" for word in ("what", "how", "where", "who", "when", "why", "which"))


def words(text):
    """The words of a line, with the apostrophe forms folded: "what's" -> "what", "you'd" ->
    "youd", so the grammar patterns see the plain word."""
    out = []
    for word in WORD.findall(str(text).lower().replace("’", "'")):
        if word.endswith("'s"):
            word = word[:-2]
        out.append(word.replace("'", ""))
    return [word for word in out if word]


def stem(word):
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("es") and word[-3] in "sxzh":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def keywords(text):
    """The content words of a line: what it is about, without the grammar."""
    out = []
    for word in words(text):
        if word in STOPWORDS or len(word) < 3 or word.isdigit():
            continue
        key = stem(word)
        if key not in out:
            out.append(key)
    return out


# What a person is not doing, in the words that say so. The word after one of these is the thing
# that is going wrong, not the subject of the line: "my kids wont listen to me" is about the kids
# and the listening is what they will not do, so a bare ask after it ("what can i do") must not be
# widened with "listen" - read with it, the line reaches the music entry and a parent gets albums.
NOT_DOING = re.compile(r"\b(?:wont|won'?t|doesnt|doesn'?t|didnt|didn'?t|cant|can'?t|couldnt|"
                       r"couldn'?t|never|refuses? to|stopped|not)\s+([a-z']+)", re.IGNORECASE)


def _what_they_are_not_doing(text):
    """The words a line puts after a negation: "wont listen" gives {"listen"}."""
    out = set()
    for found in NOT_DOING.finditer(" ".join(str(text or "").lower().split())):
        word = found.group(1)
        if word and word not in STOPWORDS and len(word) >= 3:
            out.add(stem(word))
    return out


# A verb ending people put on a word they are talking about. "save" and "saving" are the same
# thing said twice, and so are "train" and "training"; a word family that cannot see that
# misses the recall it should have answered ("what did i say i was saving for?" after
# "im trying to save 3000 for a trip").
ENDINGS = ("ing", "ed")


def forms(word):
    """The word and the forms it takes with a verb ending on or off: {saving, save}.

    "running" drops the doubled letter to find "run", and "saving" puts back the "e" that
    "save" keeps, so both directions find each other. A root shorter than four letters is not
    a form of the word: "caring" is not about a car, "seeing" not about the sea."""
    word = str(word or "")
    out = {word}
    for ending in ENDINGS:
        if len(word) > len(ending) + 2 and word.endswith(ending):
            root = word[:-len(ending)]
            if len(root) >= 4:
                out.add(root)
            out.add(root + "e")
            if len(root) > 3 and root[-1] == root[-2] and root[-1] not in "aeiou":
                out.add(root[:-1])
    return out


def content(text):
    """The words a line is about, with the verb endings taken off and the grammar dropped.

    A recall ask keeps words the statement did not: "what did I say I was *wanted* to..." asks
    with "wanted", which is the grammar word "want" with an ending on it, and "saving" asks
    about the "save" the person actually said. Both are found by looking at the forms of each
    word rather than at the word as typed."""
    out = []
    for word in words(text):
        if len(word) < 3 or word.isdigit():
            continue
        # The word itself is checked before the stem: a grammar word can be shortened into a
        # word that is nobody's grammar word, and then it counts as a thing the line is about.
        # "this" stems to "thi" and "does" to "doe", so "what do you do about this" named a
        # thing of its own ("thi") that no entry is about and the entry reached with the topic
        # was thrown away as not being about the line, which hedged where main answered.
        if word in STOPWORDS:
            continue
        key = stem(word)
        if key in STOPWORDS or forms(key) & STOPWORDS:
            continue
        if key not in out:
            out.append(key)
    return out


def is_ack(text):
    """A short reply that answers the bot's last turn rather than starting a topic."""
    clean = " ".join(words(text))
    if not clean:
        return True
    if clean in ACKS or clean in GREET:
        return True
    parts = clean.split()
    if len(parts) <= 4 and any(w in ACKS or w in GREET for w in parts):
        return all(w in ACKS or w in GREET or w in STOPWORDS or len(w) <= 3 for w in parts)
    return False


def is_small_talk(text, kind=None):
    if kind in ("empty", "greeting", "thanks"):
        return True
    return is_ack(text)


def _a_place_the_line_moves(text):
    """The place a line moves a plan to, asked of the reader that reads the move.

    Imported inside the call rather than at the top: `facts` reads places through this module, so
    asking it at the top would close a circle.
    """
    from . import facts as _facts
    return _facts.a_moved_place(text)


def _asks_about_the_bot(read):
    """True when the understanding engine read the line as a question about the bot itself."""
    return isinstance(read, dict) and bool(read.get("about_bot"))


def _note(memory, text, kind=None):
    """Record the line as the current topic when it is about something."""
    # A line can open by saying it is changing the subject ("ok changing the subject, im planning
    # a curry tonight"). The reading has already taken that clause off, and the words left are
    # what the conversation is on from here: kept as typed, "subject" is a school word, so the
    # next line ("what should i buy") was read against a school subject the person never raised
    # and got the university entry requirements while the curry sat one turn back.
    read = memory.get("understood")
    if isinstance(read, dict):
        aim_length = _the_length_of_the_aim(read, memory)
        if aim_length is not None:
            # "how long will it take" after an aim is about the aim, and the line itself names
            # nothing: left as it came in, the reading hands every reader the deadline the aim was
            # said against ("before the holiday") as the thing the "it" points at, and the length
            # of getting fit was answered with the package-travel rules.
            memory["understood"] = aim_length
            read = aim_length
    if isinstance(read, dict) and read.get("change_of_subject"):
        kept = " ".join(str(read.get("clean") or "").split())
        if kept:
            text = kept
    _keep_person(memory, text)
    if is_small_talk(text, kind):
        return None
    if _asks_about_the_bot(read):
        # "are you a real person", "are you a robot", "do you sleep" are questions about the bot,
        # not about something of theirs, so they open no topic: on main the bot question became
        # the conversation's subject and the next "what did we talk about" answered "We were on
        # the real person", a phrase nobody said. The reading is the understanding engine's own
        # (`about_bot`), so every shape of the question is covered and a line that also says
        # something of their own is untouched.
        return None
    moved_to = _a_place_the_line_moves(text)
    if moved_to:
        # "no we changed it to devon" is the subject put right, so the chat is about Devon from
        # here: the next line that names nothing ("what should we do there", "where should we
        # stay") is read against the place they are going to now. Kept as a detail of the old
        # subject, the guide kept answering about the place they had already left.
        record = {"turn": len(memory.get("turns") or []), "text": text.strip(),
                  "words": keywords(text)}
        previous = memory.get("topic")
        if isinstance(previous, dict) and previous.get("text") == record["text"]:
            return previous
        memory["topic"] = record
        topics = memory.get("topics")
        if not isinstance(topics, list):
            topics = memory["topics"] = []
        if not topics or topics[-1].get("text") != record["text"]:
            topics.append(record)
        return record
    target = return_target(text)
    if target:
        record = find(memory, target)
        if record:
            _resume(memory, record, target, text)
            return memory["topic"]
        if not _asks(target):
            # "back to the laptop" when no laptop was ever discussed: the line is about the
            # conversation, not about a new thing, so it must not become the topic.
            return current(memory)
    # The reading in memory["understood"] knows when a line leans back on the last one
    # ("should i do the potatoes in with it?"), which is a thing a word count cannot see.
    # understand.py observes at PRIORITY 10000, so this is the reading for the current line.
    leans = isinstance(read, dict) and bool(read.get("followup"))
    if is_follow_up(text, memory) or leans:
        record = current(memory)
        if record and not _after_an_emergency(memory):
            # "my knee hurts when i run" / "how long does chicken keep in the fridge" / "it hurts
            # more in the morning": the chat moved to the chicken, and this line names a word of
            # the record it left, so it is about that record again.
            back = _the_record_they_came_back_to(text, memory, record)
            if back is not None:
                return _back_to(memory, back, text)
        if record and not _after_an_emergency(memory) \
                and (not _names_another_subject(text, record, memory)
                     or _a_part_of_the_record(read, record)):
            if not _switches(text) or _only_details(text, record):
                extra = [w for w in keywords(_without_switchers(text))
                         if w not in record.get("words", [])]
                record["words"] = (list(record.get("words") or []) + extra[:4])[:12]
                return record
    # A line that only puts a number on the subject ("we've got about 6000 pounds" after the
    # wedding, "she's 78", "its about 6 hours") is a detail about it, not a new subject: the
    # conversation stays on the wedding, and a later "what can we cut" is read against it
    # rather than against the budget line, which says nothing a kitchen or a plan can answer.
    constraint = _only_names_the_constraint(text, memory)
    if (_adds_a_detail(text, memory) or _only_adds_a_person_to_the_thing(text, current(memory))
            or constraint):
        record = current(memory)
        if record is not None and not _after_an_emergency(memory):
            if constraint:
                # The budget is kept off the subject's words as well as out of its place: the
                # words are what the next ask is looked up with, and "my budget is 5k" put
                # "budget" into the used car's words, so "what should i check" found the
                # household budget card. A constraint is not part of what the thing is.
                return record
            extra = [w for w in keywords(text) if w not in record.get("words", [])]
            record["words"] = (list(record.get("words") or []) + extra[:4])[:12]
            return record
    if _is_a_when_or_how_often(text, memory):
        record = current(memory)
        if record is not None and not _after_an_emergency(memory):
            extra = [w for w in keywords(text) if w not in record.get("words", [])]
            record["words"] = (list(record.get("words") or []) + extra[:4])[:12]
            return record
    if _asks_which_kind(text, memory):
        record = _about_record(memory)
        if record and not _after_an_emergency(memory) and not _reaches_another_thing(text, memory):
            extra = [w for w in keywords(text) if w not in record.get("words", [])]
            record["words"] = (list(record.get("words") or []) + extra[:4])[:12]
            return record
    if _asks_an_aspect_of_the_thing(text, memory):
        record = current(memory)
        # The article in "what is the food like" names a side of the thing, not a thing of its
        # own, so `_names_a_thing_of_its_own` is not asked here - it reads "the food" as a new
        # subject and that is the reading this branch exists to undo. A place of its own still
        # moves the chat ("what is the food like in naples").
        if (record is not None and not _after_an_emergency(memory)
                and not _names_a_place_of_its_own(text, record, memory)):
            extra = [w for w in keywords(text) if w not in record.get("words", [])]
            record["words"] = (list(record.get("words") or []) + extra[:4])[:12]
            return record
    kept = _the_plan_a_correction_renames(memory, text)
    if kept is not None:
        return kept
    keys = keywords(text)
    if len(keys) < 2 and len(words(text)) < 4:
        # A short line can still be the thing the conversation is on. "im so tired" has one
        # content word and three words in it, and the understanding engine reads it as being
        # about sleep; the next line ("its been going on for weeks", "what should i do about
        # it?") is read against a subject that was never written down, so the follow-up had
        # nothing to lean on and was acknowledged instead of answered. The topic id the
        # reading already found is enough to keep the conversation there.
        read = memory.get("understood")
        labels = read.get("topics") if isinstance(read, dict) else None
        labels = [str(label) for label in (labels or ()) if label]
        if not labels:
            return None
        record = {"turn": len(memory.get("turns") or []), "text": text.strip(), "words": keys,
                  "id": labels[0], "label": labels[0]}
        previous = memory.get("topic")
        if isinstance(previous, dict) and previous.get("text") == record["text"]:
            return previous
        memory["topic"] = record
        topics = memory.get("topics")
        if not isinstance(topics, list):
            topics = memory["topics"] = []
        if not topics or topics[-1].get("text") != record["text"]:
            topics.append(record)
        return record
    detail = _a_detail_of_what_we_are_on(text, memory)
    record = {"turn": len(memory.get("turns") or []), "text": text.strip(), "words": keys}
    aim = _the_aim_without_its_deadline(text)
    if aim:
        # "im trying to get fit before the holiday" is a chat about getting fit, and the deadline
        # is when they want it by. Kept whole, the only noun the chat has is the holiday, so the
        # next line - "how long will it take" - leans on the holiday and comes back with the
        # package-travel rules. The aim is the subject; the deadline is in the turns and the store
        # still has it when a line names it.
        record["text"] = aim
        record["words"] = keywords(aim)
    if detail is not None:
        # The line says something about the thing the chat is on, not about a new thing: who it
        # is for, what it is made of, what it cannot have. It stays a topic of its own - the
        # answer it reached is real, and the line is still in the turns - but it points back at
        # the thing, so the next line ("how long will it take?", "can I make it the day
        # before?") is read against the cake and not against the nuts. Read against the nuts it
        # reaches nothing and the answer already given comes back: "Same as before: <the
        # allergy answer>".
        record["of"] = str(detail.get("text") or "")
    previous = memory.get("topic")
    if isinstance(previous, dict) and previous.get("text") == record["text"]:
        return previous
    memory["topic"] = record
    topics = memory.get("topics")
    if not isinstance(topics, list):
        topics = memory["topics"] = []
    if not topics or topics[-1].get("text") != record["text"]:
        topics.append(record)
    return record


def _the_record_they_came_back_to(text, memory, record):
    """An earlier record of this chat that the line names, when the one in hand says nothing.

    "my knee hurts when i run" / "how long does chicken keep in the fridge" / "it hurts more in
    the morning": the chat moved to the chicken, and the line that comes back says "it" and
    "hurts". Read against the chicken it is a detail of the chicken, so the bot answered the
    symptom with sympathy and the knee it was about was gone. A record the chat already had, whose
    own words the line carries, is what the line is about.

    Only a word the record already has counts, and only when the record in hand shares none of the
    line's words - a follow-up that fits the thing in hand stays with it.
    """
    found = set(keywords(text))
    if not found or found & set(record.get("words") or ()):
        return None
    if found <= ORDERING:
        # A line that only asks where to begin names the answer in hand, not a subject: "where do
        # i start" and "what should i do first" carry one word each, and that word sits in an
        # earlier record's words for its own reason ("starts school"). Read as a return, the
        # chat went back to the school while the person was asking about the curry, and the
        # school card answered the ask. Only a line whose every word is one of these is left
        # alone, so "when does school start" and "what should i do first about the boiler" are
        # read as before.
        return None
    topics = memory.get("topics")
    if not isinstance(topics, list):
        return None
    for older in reversed(topics[-4:]):
        if older is record or (older.get("text") or "") == (record.get("text") or ""):
            continue
        if found & set(older.get("words") or ()) - set(REFERRING):
            return older
    return None


def _back_to(memory, record, text):
    """Make an earlier record the current one again, with the line's words added to it.

    Not `_resume`: nobody said "back to the knee", so there is no return to greet - the record is
    only what the rest of the bot reads this line against.
    """
    said = dict(record)
    kept = list(record.get("words") or ())
    said["words"] = (kept + [w for w in keywords(text) if w not in kept])[:12]
    memory["topic"] = said
    topics = memory.get("topics")
    if isinstance(topics, list):
        topics[:] = [other for other in topics if other is not record
                     and (other.get("text") or "") != (said.get("text") or "")]
        topics.append(said)
    return said

# An aim said as their own, with the deadline it is said against: "im trying to get fit before the
# holiday", "we're hoping to save 2000 by june". Only the frame people aim in, so a line that
# names a date of its own ("im going to portugal in may") keeps every word it has.
AIM_FRAME = re.compile(r"^\s*(?:(?:so|ok|okay|and|also|well|right|yeah|hi|hello)\b[, ]+)*"
                       r"(?:i'?m|im|i am|we'?re|we are)\s+"
                       r"(?:trying|aiming|hoping|planning|meaning|learning)\b", re.I)
# The deadline is what the aim is measured against, not what it is about.
A_DEADLINE = re.compile(r"\b(?:before|by|until|till|in time for|ready for|ahead of)\b", re.I)


def _the_aim_without_its_deadline(text):
    """The aim a line states, without the deadline clause it is said against, or "".

    Empty for every line that is not an aim, and for an aim that names no deadline: the words of a
    line that has no later thing in it are already the thing it is about.
    """
    line = " ".join(str(text or "").strip().split())
    match = AIM_FRAME.match(line)
    if not match:
        return ""
    rest = line[match.end():]
    cut = A_DEADLINE.search(rest)
    if not cut:
        return ""
    aim = re.sub(r"^\s*to\s+", "", rest[:cut.start()], flags=re.I).strip(" .,;:-")
    words = aim.split()
    if not 1 <= len(words) <= 8 or not re.search(r"[a-z]{3}", aim, re.I):
        return ""
    return aim[0].upper() + aim[1:] if aim[:1].islower() else aim


def _asks_which_kind(text, memory):
    """True when the line asks which kind of the thing in hand, naming no thing of its own.

    "what breed is good with young children" after "im thinking of getting a dog for the kids"
    is a dog question: "what breed" is the word for the choice between dogs, not a thing of its
    own. Read as a subject of its own, the topic became "breed good young children", and the
    next line - "how much exercise does it need" - was answered from that instead of from the
    dog. Only a conversation that already has a subject folds the line into it: with nothing on
    the table the line is all there is, so it keeps its own record.
    """
    if not KIND_ASK.search(" ".join(str(text or "").lower().split())):
        return False
    return bool(subject(memory))


# A question about a *part* of the thing in hand rather than about a thing of its own: "what is
# the food like" after "im going to rome in may", "how is the weather there", "is the beer any
# good". The aspect word is a side of the thing, not a new subject, so the line is about that
# thing still. Kept as a record of its own - text "what is the food like", words ["food"] - the
# place was gone, and the next ask ("what should i book") was read against nothing and shrugged
# at, while the answer two turns back was about Rome all along. Thirteen of mustard-boar's
# sixteen chats kept the subject because the aspect was asked with a pronoun ("what spices go in
# it"); every one that named the aspect instead lost it.
ASPECT_OF_IT = re.compile(
    r"\bwhat(?:'s| is| are| was| were)\s+(?:the\s+|their\s+|its\s+|his\s+|her\s+)?"
    r"[a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,2}\s+like\b"
    r"|\bhow(?:'s| is| are| was| were)\s+(?:the\s+|their\s+|its\s+)?"
    r"[a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,2}\s*$"
    r"|\bis\s+the\s+[a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,2}\s+"
    r"(?:any\s+good|good|worth\s+it|worth\s+doing|ok|okay|decent|safe|expensive|cheap|nice)\b",
    re.I)


# A pronoun is not a side of the thing: "how are you" matched the shape of "how is the weather"
# and would have folded the whole conversation into the line, and "how is your back" is a body of
# its own rather than a side of the last thing said.
ASPECT_IS_A_PRONOUN = frozenset("""
    you me him her them us i we they he she your my our mine yours
""".split())


def _asks_an_aspect_of_the_thing(text, memory):
    """True when the line asks about a side of the thing the chat is on, naming nothing of its own.

    Only read inside a conversation that already has a subject, and never when the line brings a
    thing or a person of its own: "what is the food like in naples" moves the chat to Naples, and
    "how are the kids" is not an aspect of anything. The words of the aspect join the record's
    words, which is what the pronoun asks ("what spices go in it") already do, so the next ask is
    looked up with the thing still in it.
    """
    if not ASPECT_OF_IT.search(" ".join(str(text or "").lower().split())):
        return False
    if person(text):
        return False
    if any(word in ASPECT_IS_A_PRONOUN for word in words(text)):
        return False
    # "how are the kids" is not a side of anything: a person is a subject of their own, in the
    # plural too, and the store reads people by the same list everywhere else.
    if any(stem(word) in WHO for word in words(text)):
        return False
    return bool(subject(memory))


def _reaches_another_thing(text, memory):
    """True when the line reaches a knowledge entry that is not about the conversation's thing.

    The record's own line is a poor stand-in for the thing: "im thinking of getting a dog for
    the kids" reaches the entry about deciding a choice, not the one about dogs, so a question
    about dogs looked like a new subject next to it. The subject the store already worked out
    ("dog") is what decides: an entry that names a word of it is still that thing, and one that
    does not - the cats - is a thing of its own.
    """
    mine = _entry(text)
    if mine is None:
        return False
    thing = subject(memory)
    if not thing:
        return False
    return not _names_it(words(thing), mine)


# A thing of the line's own, said with the possessives and the definite article: "my budget is 600
# pounds", "the oven is a fan one". "a" and "an" are left out - a detail often names one of the
# thing's parts - and so is a person ("my daughter is a vegetarian" is still about the meal).
OWN_THING = re.compile(r"\b(?:my|our|your|his|her|their|the)\s+([a-z]+)")


def _names_a_thing_of_its_own(text, record, memory=None):
    """True when the line turns the chat to a thing of its own ("my budget", "the kitchen")."""
    known = set(record.get("words") or [])
    for found in OWN_THING.finditer(" " + " ".join(words(text)) + " "):
        word = stem(found.group(1))
        if word in WHO or word in known:
            continue
        return True
    return _names_a_place_of_its_own(text, record, memory)


def _names_a_place_of_its_own(text, record, memory=None):
    """True when the line says where they are, about a place the chat is not already on.

    "how do i get rid of ants" / "i live in bristol" was kept as a detail of the ants question,
    so the knowledge base put the ants back into the line ("i live in bristol ant"), reached the
    ant entry and answered an ant's lifespan instead of the news about Bristol - and the eight
    lines people write after an answer (a place, a job, a swim on Tuesdays) were answered about
    the subject before them. The reading knows the line named a place of its own, and a place the
    chat is not on is a thing the next line can lean on ("what's it like there?", "is it
    expensive?"), which is what a topic is for. Only a place the reading itself found counts,
    never a word of the line at large, and never the question the chat is on: "which airport do
    i fly to in rome" is about the trip, not about a new place.
    """
    read = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(read, dict) or read.get("kind") == "question":
        return False
    known = set(record.get("words") or [])
    said = set(words(record.get("text") or ""))
    for found in read.get("entities") or ():
        if not isinstance(found, dict) or found.get("type") != "place":
            continue
        name = str(found.get("text") or "").strip().lower()
        if not name:
            continue
        if any(stem(part) in known for part in name.split()):
            continue
        if any(part in said for part in name.split()):
            continue
        return True
    return False


def _only_adds_a_person_to_the_thing(text, record):
    """True when the line adds a person to the thing the chat is on, rather than a subject.

    "my sister is coming too" after "im going to rome in june", and "he loves dinosaurs" after
    "my son is 7": the line names no thing a knowledge entry can answer, so it cannot be what the
    next one leans on. Kept as a topic of its own it became exactly that, and the ask after it -
    "what should i see?", "how long will it take?" - was read against a sister or a dinosaur,
    reached nothing, and the answer that was on the screen one turn earlier (the trip's
    sightseeing, the sponge's timings) turned into a search hedge. The person is part of the
    thing: their words join the thing's, and the chat stays on it.

    Two shapes count, both narrow: a person who joins the thing ("too", "as well", "coming",
    "with me"), and something said of the person the thing already names ("he loves ...", "she
    is into ...", a pronoun, with the record naming the person). A line that names a thing of
    its own is left to be a subject of its own, so "my budget is 600 pounds" after a laptop and
    "my car won't start" after a cake still move the chat.
    """
    if not isinstance(record, dict) or not record.get("text"):
        return False
    line = " ".join(words(text))
    if not line or len(line.split()) > 14:
        return False
    if _entry(text) is not None:
        # The line reaches an answer of its own (the cake's allergy variant, say): that answer is
        # about the thing, so the record stays a topic of its own that points back at it.
        return False
    named = person(text)
    theirs = person(record.get("text") or "")
    if named is None and theirs is None:
        return False
    if JOINS_THE_THING.search(line) and named is not None:
        return True
    return (ABOUT_THE_PERSON.search(line) is not None and theirs is not None
            and PRONOUN_PERSON.search(line) is not None)


# A person who is part of the thing the chat is on, rather than a subject of their own: the
# companion joins the thing ("coming", "too", "with me") or is the person the thing is for, and
# the interest is said of them ("loves", "is into", "plays", "collects").
JOINS_THE_THING = re.compile(
    r"\b(?:too|as well|along|coming|comes|with (?:me|us))\b")
ABOUT_THE_PERSON = re.compile(
    r"\b(?:loves?|loved|likes?|liked|adores?|prefers?|collects?|plays?|wants?|enjoys?|hates?|"
    r"into|is (?:mad|crazy|obsessed) about|is a fan of|fans? of|is afraid of)\b")
PRONOUN_PERSON = re.compile(r"\b(?:he|she|they|him|her|them)\b")


# A question of how many, how much or how long is read as a sum whatever it is about, so its area
# says nothing about which subject it belongs to.
MEASURE = frozenset({"maths-and-numbers"})


def _another_area(text, said):
    """True when the two lines are read as different kinds of thing (bedwetting, Lisbon).

    A detail can well be in another area from the thing it is a detail of - "he is allergic to
    nuts" after a birthday cake is food about a cake - so this never refuses a detail on its
    own; it is the third check beside the line's own answer and the words that answer speaks.
    """
    if not said:
        return False
    from ..understanding import understand  # noqa: PLC0415 - understanding imports this package
    there = (understand(said, {}) or {}).get("topic_own")
    mine = (understand(text, {}) or {}).get("topic_own")
    if mine in MEASURE:
        return False  # "and how many days in kyoto" is a count of the trip, not another subject
    return bool(there and mine and there != mine)


def _a_detail_of_what_we_are_on(text, memory):
    """The record this line only says a detail about, or None when it names a thing of its own.

    "he loves chocolate but he is allergic to nuts" after a birthday cake reaches an answer of
    its own (the cake's allergy variant), so on its words alone it looks like a new subject. It
    is not: the answer it reaches is the cake's, which is why the reply was about the cake. If
    the chat moves its subject to the nuts, the next line - one that names nothing of its own,
    like "how long will it take, start to finish?" - is read against the nuts, reaches nothing,
    and gets the answer already given again: "Same as before: <the allergy answer>". The thing
    the chat is on is the cake, so a line that answers about it is a detail of it.

    "my budget is 600 pounds" after a laptop is not one: it is about the budget, and the next
    ask ("which one would you pick?") has to be read against the budget, not the laptop.
    """
    record = current(memory)
    if not isinstance(record, dict) or not record.get("text"):
        return None
    if _this_line(record, memory) or _after_an_emergency(memory):
        return None
    if _names_a_thing_of_its_own(text, record, memory):
        return None
    turn = record.get("turn")
    if isinstance(turn, int) and len(memory.get("turns") or []) - turn > RECENT_TURNS:
        return None
    thing = gist(record.get("text") or "")
    if not thing:
        return None
    widened = _entry(str(text) + " " + thing)
    if widened is None:
        return None
    # The answer the widened line reaches has to be about the thing the chat is on: "my car
    # won't start" after a birthday cake reaches the car's answer, which says nothing about a
    # cake, so the car is a subject of its own.
    keyed = _key_words_of(widened)
    thing_words = [word for word in keywords(thing) if len(word) > 2]
    if not thing_words or not any(alike(word, key) for word in thing_words for key in keyed):
        return None
    own = _entry(text)
    if (own is not None
            and not any(alike(word, key) for word in keywords(text) for key in keyed)
            and _another_area(text, record.get("text") or "")):
        # The line has an answer of its own, the answer it reaches with the thing added speaks
        # of none of the line's own words, and the two lines are read as different kinds of
        # thing: it is a subject of its own, not a detail. "im going to lisbon in may" after a
        # bedwetting line reaches the city guide, and the bedwetting answer shares no word with
        # it; kept as a detail of the bedwetting line, the next ask ("what should i see") was
        # read against that line and answered from it.
        return None
    if own is widened:
        return None  # the line reaches this answer without the thing, so it is that answer
    if own is not None and not any(alike(word, key) for word in _key_words_of(own)
                                   for key in keyed):
        return None  # a different question about the thing, not a way of answering this one
    if keeps_away(str(text) + " " + thing, record.get("text") or "", widened):
        return None
    return record


def _a_part_of_the_record(read, record):
    """True when the reading says this line hangs off the record the chat is already on.

    "and the food" after a trip names a subject of its own - it reaches the food entry, so
    `_names_another_subject` reads it as a new thing and the trip stops being the chat's subject.
    But it is a part of the trip: the understanding engine walks back over a part line and reads
    the line after it against the trip, so the trip is what the next ask is answered from. Kept
    as the food's record instead, "and how do i get around" was widened with the food's words,
    the city was gone, and the entry that fit was the food card the person had just read.
    """
    if not isinstance(read, dict) or not isinstance(record, dict):
        return False
    leaned = " ".join(words((read.get("leans_on") or {}).get("text") or ""))
    return bool(leaned) and leaned == " ".join(words(record.get("text") or ""))


def _names_another_subject(text, record, memory=None):
    """True when a line that leans back is really about a different thing of its own.

    "how long do i boil an egg" then "my kitchen tap is dripping and its driving me mad" reads as
    a follow-up - the "its" is enough to make it lean - and carries no switching word, so the tap
    line was merged into the egg's record: the record kept the egg's text, gained the tap's
    words, and the next question ("how do i fix it?") was answered from the egg. A line that
    reaches a knowledge entry of its own, while the record reaches a different one, is about that
    other thing, however it leans. The check is on the entries, not on the words, because
    "my oven is fan assisted" reaches nothing and is the detail about the oven it is.
    """
    if (_leads_a_question(text) and _leans_back(text, record)
            and _points_at_the_record(text, record, memory)):
        # A question that leans back is a question about the thing the chat is on, even when it
        # names another entry: "should i do the potatoes in with it" after the chicken is about
        # the chicken, and it must not become a potato topic of its own. A question that names
        # another entry and points at nothing here is its own subject, however it opens: "can i
        # freeze rice" after "how do i descale the kettle" is the rice, not the kettle, and
        # reading it as a detail of the kettle left the chat on the kettle for good, so the next
        # "is that bad" was answered from the kettle's card.
        return False
    mine = _entry(text)
    if mine is None:
        return False
    theirs = _entry(str(record.get("text") or ""))
    return theirs is not None and theirs.id != mine.id


def _leans_back(text, record):
    """True when the line points at the thing the chat is on: "with it", a measure of it, or a
    word the subject already has.

    A how-long or what-temperature question names no subject of its own ("how long for a 2kg
    chicken" after a roast), so the measure is what says it is still the same thing.
    """
    found = words(text)
    if any(word in REFERRING for word in found):
        return True
    if PROPERTY.search(" ".join(found)):
        return True
    if PART_OF_THE_ONE.search(" ".join(found)):
        return True
    if ABOUT_ANOTHER.search(" ".join(found)):
        return True
    return bool(set(keywords(text)) & set(record.get("words") or ()))



def _points_at_the_record(text, record, memory=None):
    """True when the line points at the thing the chat is on, not merely reads as a property ask.

    A "how long" question is shaped like a property ask, and that shape alone was enough to say
    the line was about the thing in hand: "my washing machine smells" then "is it worth getting a
    smart meter" then "how long do i boil an egg" kept the washing machine as the subject, so the
    egg line was answered with the washing-machine card, two turns after the machine. A measure of
    the thing ("how long for a 2kg chicken"), a pronoun ("how long should i leave it in"), a part
    of it ("the rest", "the leftovers"), a word the record already holds, or a word from the answer
    on the screen ("how much water" after the rice, whose answer gives the ratio) is the line
    pointing at it. A property ask with none of those is a question about something else.
    """
    found = words(text)
    if a_placeholder_pronoun(text):
        # "is it worth getting an air fryer": the "it" is a hole for the thing the line names
        # after "getting", not a pointer back at the chat's subject. Read as a pointer it kept
        # the line tied to whatever came before, so after a child-and-veg line the air fryer
        # question was answered from the veg card ("Five a day is 400g"), and a smart meter
        # question was answered about the washing machine. The same words in the shape "should
        # i get an air fryer" already moved the subject; only the shape differed.
        found = [word for word in found if word != "it"]
    if any(word in REFERRING for word in found):
        return True
    if PART_OF_THE_ONE.search(" ".join(found)):
        return True
    if ABOUT_ANOTHER.search(" ".join(found)):
        return True
    mine = set(keywords(text))
    if not mine - MEASURE_WORDS:
        # "what temperature", "how long", "how much" on its own: the line asks for a detail and
        # names no thing of its own, so the detail is of the thing in hand.
        return True
    if mine & set(record.get("words") or ()):
        return True
    said = ""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if isinstance(turns, list) and turns and isinstance(turns[-1], dict):
        said = str(turns[-1].get("bot") or "")
    return bool(mine and said and mine & set(words(said)))


def _leads_a_question(text):
    """True when the line opens a question: "how long for a 2kg chicken", "should i ...?"."""
    found = words(text)
    return "?" in text or (bool(found) and found[0] in RETURN_ASKS)


def _switches(text):
    """True when the line turns to a different subject ("actually it's a funeral").

    "I'm going to a wedding and need a suit" then "actually it's a funeral" then "what should I
    wear to that?" is not a follow-up on the wedding: the correction replaced the subject, so the
    record has to be started again from the corrected line. A word like "actually" or "instead"
    is the person saying the subject changed, and is_follow_up() already refuses these lines; the
    reading in memory["understood"] does not see it, which is what this guards.
    """
    low = " ".join(words(text))
    return any(low.startswith(s) or (" " + s + " ") in (" " + low + " ") for s in SWITCHERS)


# The chatty words a line opens with before it gets to the point: "ok so actually it's a funeral".
# They say nothing, so the switch is read after them.
_LEADS_IN = re.compile(r"^(?:(?:ok|okay|k|kk|so|well|oh|ah|and|but|um+|uh+|er+|hmm+|right|yeah|yep|"
                       r"also|plus|now)[\s,.!-]+)*", re.I)


def opens_by_switching(text):
    """True when the line opens by turning to another subject ("actually it's a funeral").

    A switch word in the middle of a line is not a switch: "what can i actually do to help her" is
    a follow-up about the thing on the table, "can i use oil instead of butter" asks about the
    butter, and "i might be sad, actually" is a feeling said again. Read as a turn away, that
    follow-up was left with no reading at all - "actually" is a word the person talks with, not a
    subject - and the answer about the arthritis sat one word away while the turn went to a search
    hedge. Only a line that says the turning first is turning.
    """
    low = _LEADS_IN.sub("", " ".join(words(text)))
    return any(low.startswith(switcher) for switcher in SWITCHERS)


# The courtesy and the pointing that come with a correction: "actually it's in august, sorry".
CORRECTION_NOISE = frozenset("""sorry apologies apology correction correcting wrong mistake
mean meant rather wait oh""".split())


# What a line can change without changing what the conversation is about: a when, a where, how
# many or how much. "actually it's in august" is the same wedding with a new date; "actually
# it's a funeral" is a different occasion. Numbers are already dropped by keywords().
DETAIL_WORDS = frozenset("""
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec
monday tuesday wednesday thursday friday saturday sunday weekend weekday
morning afternoon evening night tonight today tomorrow yesterday day days week weeks
month months year years hour hours minute minutes oclock am pm
people person persons guest guests adult adults child children kid kids
pound pounds quid euro euros dollar dollars pence penny
kilo kilos kg gram grams litre litres liter liters pint pints cup cups tablespoon tablespoons
half quarter dozen
""".split())


def _without_switchers(text):
    """The line with the words that announce or excuse a correction taken out, so they are not
    content: "actually" and "sorry" say a correction is coming, not what it is."""
    parts = [part for switcher in SWITCHERS for part in switcher.split()]
    return " ".join(word for word in words(text)
                    if word not in parts and word not in CORRECTION_NOISE and word not in ACKS)


def _only_details(text, record):
    """True when everything a correction brings is a detail of the subject, not a new subject.

    "I'm going to a wedding in july" then "actually it's in august" is still the wedding, and
    the next line that names nothing ("what should I wear to that?") has to keep leaning on it.
    "Actually it's a funeral" replaces the occasion, so that line starts a new record instead.
    """
    have = set(record.get("words") or [])
    fresh = [key for key in keywords(_without_switchers(text)) if key not in have]
    return all(key in DETAIL_WORDS for key in fresh)


# A plan to get one thing, said before the thing turns out to be another: "im thinking of getting a
# rescue greyhound" then "actually its a whippet" is the same plan with a different animal in it,
# not a new subject. A correction that only names the thing is read as a new subject on its own
# (`_switches`), which threw the plan away: the chat had nothing on record but the word "whippet",
# so the next line, "how much exercise does it need", named nothing of its own, found nothing to
# lean on, and was answered "I don't know enough to answer that honestly" - the reading was right
# and the record had forgotten the dog.
A_THING_ON_ITS_WAY = re.compile(
    r"\b(?:thinking\s+(?:of|about)|planning\s+(?:on|to)|hoping\s+to|considering|going\s+to|"
    r"about\s+to|thinking\s+we\s+might|might|may|could)\s+"
    r"(?:get|getting|have|having|adopt|adopting|buy|buying|rescue|rescuing|rehome|rehoming|"
    r"look\s+at|look\s+for|find|finding|pick|picking\s+up|collect|collecting|bring\s+home)\b"
    r"|\b(?:looking\s+(?:at|for)|shopping\s+for|on\s+the\s+lookout\s+for)\s+(?:a|an|another)\b"
    r"|\b(?:getting|adopting|rescuing|rehoming|wanting|want|wanted)\s+(?:a|an|another|one)\b", re.I)
# The correction itself: the line says what the thing is and nothing else. "actually its a
# funeral" after "im getting a rescue greyhound" is nonsense, so the plan has to be the thing the
# correction is about, and the words carry nothing else with them.
NAMES_THE_THING = re.compile(
    r"^\W*(?:(?:ok|okay|so|well|oh|ah|no|nope|sorry|actually|wait|hmm|erm?|um)\b[\s,.!-]*)*"
    r"(?:its|it'?s|it\s+is|that'?s|that\s+is|i\s+mean|i\s+meant|make\s+that)\s+"
    r"(?:an?\s+|the\s+|just\s+|only\s+|really\s+)?[a-z][a-z' -]{2,30}"
    # The courtesy that comes after the correction: "actually its a whippet, sorry" is the same
    # line, and read as one word more than a bare name it was a dog of theirs again.
    r"(?:\s*[,.!-]*\s*(?:sorry|apologies|thanks|thank\s+you|actually|though|then|i\s+think|hmm))*$",
    re.I)
FRESH_NAMES = 3      # a name brings at most this many words the plan has not got


def _the_plan_a_correction_renames(memory, text):
    """The record the line corrects, when it names a different thing inside a plan of theirs.

    Returns None when the line is not a bare naming after a plan to get something, so every other
    correction is left to the rules that read it as a subject of its own.
    """
    record = current(memory)
    if not isinstance(record, dict) or _after_an_emergency(memory):
        return None
    if not NAMES_THE_THING.match(" ".join(str(text or "").lower().split())):
        return None
    if not A_THING_ON_ITS_WAY.search(str(record.get("text") or "")):
        return None
    extra = [key for key in keywords(text) if key not in (record.get("words") or ())]
    if not extra:
        return None
    # The plan keeps its words and gains the new name: the next line leans on the plan ("how much
    # exercise does it need" is the dog's question), and the name they have just said is in the
    # record it leans on.
    record["words"] = (list(record.get("words") or []) + extra[:FRESH_NAMES])[:12]
    return record

# "my car is a 2015 fiesta" names a new thing however many numbers it has; "its about 6 hours" does not.
MY_THING_IS = re.compile(r"^\W*(?:my|our|the)\s+([a-z]+)\s+(?:is|are|was|were)\b")
SHORTHAND = re.compile(r"^\d+(?:\.\d+)?\s*[km]$|^\d+(?:\.\d+)?\s*(?:k|m)\b")
RECENT_TURNS = 3     # a detail belongs to the subject of the last few turns, not an old one
FRESH_WORDS = 2      # a detail brings at most this many words the subject has not got


def _is_a_quantity(reading):
    """True when the numbers in the line carry a measure: "6000 pounds", "6 hours", "3k".

    A count of things is not one - "i have two cats" names the cats, it does not put a number
    on the last subject - so a bare count is left to name its own topic.
    """
    for number in reading.get("numbers") or []:
        if not isinstance(number, dict):
            continue
        if number.get("unit"):
            return True
        if SHORTHAND.match(str(number.get("text") or "").strip()):
            return True
    return False


# A line that only says when it started or how often, with no thing of its own: "since i moved
# here" after feeling lonely at weekends, "i drink about 3 coffees" after the headaches. It names
# nothing ("my", "a", "the" before a noun would be a thing), it reaches no entry, and it carries
# a when or an amount, so it is a fact about what the chat is on rather than a new subject.
#
# It has to stay a fact and not become the topic: the next short ask ("how do i meet people",
# "could it be that") is read against the topic, and a topic that is only a timeframe has nothing
# to read it against, so the turn ended in the search hedge two turns after the answer existed.
WHEN_OR_AMOUNT = re.compile(
    r"\b(?:since|for|about|around|started|began|start|most|every|each|last|this|next|"
    r"a day|a week|a month|a year|once|twice|times)\b|\b\d+\b")
# A thing of their own in the line: a determiner in front of a word. The line is then about that
# thing ("my car is a 2015 fiesta", "i started a new job last week") and starts its own topic.
NAMED_THING = re.compile(r"\b(?:my|our|your|his|her|their|the|a|an|some|any)\s+[a-z]")


def _is_a_when_or_how_often(text, memory):
    """True when the line only adds a when or a how-often to what the chat is already on."""
    read = memory.get("understood")
    if not isinstance(read, dict) or read.get("kind") != "statement":
        return False
    found = words(text)
    if not found or len(found) > 8:
        return False
    if WHEN_OR_AMOUNT.search(" ".join(found)) is None:
        return False
    if NAMED_THING.search(" " + " ".join(found) + " "):
        return False
    if len(keywords(text)) > 4:
        return False
    if _entry(text) is not None:
        return False  # it reaches an answer of its own, so it is a subject
    record = current(memory)
    if record is None:
        return False
    turn = record.get("turn")
    if isinstance(turn, int) and len(memory.get("turns") or []) - turn > RECENT_TURNS:
        return False
    return True


# The words a line can name that are a fact about the thing in hand rather than a thing to move
# to: what it may cost, how old it is, how much time there is for it. A constraint said as a
# number ("my budget is 5k" after "im buying a used car") names a word the subject does not have,
# so the budget became the topic and the next short ask - "what should i check" - was read against
# a household budget and answered "write down what comes in each month". The person is still
# buying a car, and the budget is a fact about the car.
CONSTRAINT_IS = re.compile(
    r"^(?:my|our|the)\s+(?:budget|price|cost|age|salary|wage|wages|income|savings|time|"
    r"spending|tariff|allowance)\s+(?:is|was|'s)\b")
# The same fact said as a way of travelling rather than as a thing that is a figure: "we're on a
# budget, about 300 each" after "im going to edinburgh in march" is about the trip, and a follow-up
# with no noun of its own ("what should we see", "any good pubs") was read against the budget line
# and answered "write down what comes in each month" twice, the second time word for word.
ON_A_BUDGET = re.compile(
    r"^(?:we|i|were|im)(?:\s+(?:are|am|was))?\s+(?:on|under|within|keeping to|sticking to|"
    r"trying to keep to)\s+(?:a|the|our|my|tight|small|strict)?\s*budget\b")


def _only_names_the_constraint(text, memory):
    """True when the line puts a number on a constraint of the thing in hand, and nothing else.

    It has to carry a measure ("my budget is 5k", "my budget is 5000 pounds"), because a budget
    with no figure in it ("my budget is tight") is a feeling about the money and not a quantity
    for the thing - and the line has to have something in hand to be about.
    """
    read = memory.get("understood")
    if not isinstance(read, dict) or read.get("kind") != "statement":
        return False
    said = " ".join(words(text))
    on_a_budget = ON_A_BUDGET.match(said) is not None
    if CONSTRAINT_IS.match(said) is None and not on_a_budget:
        return False
    if on_a_budget:
        # "about 300 each" is read as a maths ask rather than a quantity, so the figure is counted
        # in the line: a budget with no figure in it ("we're on a budget") is a feeling about the
        # money and says nothing about the trip.
        if not re.search(r"\d", said):
            return False
    elif not _is_a_quantity(read):
        return False
    record = current(memory)
    if record is None:
        return False
    turn = record.get("turn")
    if isinstance(turn, int) and len(memory.get("turns") or []) - turn > RECENT_TURNS:
        return False
    return True


def _adds_a_detail(text, memory):
    """True when the line only says a how-much about what the conversation is already on.

    It has to be a plain statement (a question is its own ask), it has to carry a measure (a
    price, a time, a distance), and it may bring at most a couple of words the subject does
    not already have: "we've got about 6000 pounds" after the wedding, "i can do about 3k at
    the moment" after the 10k. A line that names its own thing is not a detail of the last
    subject, so "my car is a 2015 fiesta" and "i have two cats" still start their own.
    """
    read = memory.get("understood")
    if not isinstance(read, dict) or read.get("kind") != "statement":
        return False
    if not _is_a_quantity(read):
        return False
    record = current(memory)
    if record is None:
        return False
    turn = record.get("turn")
    if isinstance(turn, int) and len(memory.get("turns") or []) - turn > RECENT_TURNS:
        return False
    named = MY_THING_IS.match(" ".join(words(text)) + " ")
    if named and stem(named.group(1)) not in (record.get("words") or []):
        return False
    numeric = set()
    for number in read.get("numbers") or []:
        if isinstance(number, dict):
            numeric.update(stem(word) for word in words(number.get("text") or ""))
    known = set(record.get("words") or [])
    fresh = [w for w in keywords(text) if w not in known and w not in numeric]
    return len(fresh) <= FRESH_WORDS


# --- who the turn is about ---------------------------------------------------
# A conversation is full of lines about somebody else: "my mum moved in with us last month",
# then "she keeps forgetting where things are in the kitchen". The second line names nobody, and
# reading it as a follow-up on the *thing* of the first line is how a person worried about their
# mother's memory was handed a packing plan. So the store keeps the person the chat is about, and
# the modules that answer read it: `memory["person"] = {"who": "mum", "said": <their line>,
# "turn": 3}`.
WHO = frozenset("""
mum mom mam mummy mumma mother dad daddy father papa son daughter child kid baby toddler
partner husband wife spouse boyfriend girlfriend fiance fiancee sister brother sibling stepsister
stepbrother stepson stepdaughter nan nana gran granny grandma grandmother grandad grandpa
granddad grandfather grandparents grandparent aunt auntie uncle cousin nephew niece friend
flatmate housemate neighbour neighbor landlord landlady lodger manager
tutor childminder carer hairdresser barber instructor
""".split())

# "my mum", "our dad": the person the speaker names as their own. His, her and their are kept
# apart because "she keeps asking for her mum" names a *third* person - the one the person the
# chat is about is asking for - and the chat is still about her, not about her mother. Reading
# them as the person this speaker owns put the wrong name in the reply ("How long has that been
# going on with your mum?" to a line about a wife).
# The possessive is written without its apostrophe more often than with it - "my mums been in
# hospital a week", "my dads getting forgetful", "my sons at uni" - and a name with an `s` on the
# end is the same person as the name. Reading only the bare name left those lines naming nobody:
# "my mums been in hospital a week" fell back to whoever the chat was last about, and in a
# conversation that had opened on `my son is 16 and wants a motorbike` the ward answer said "That
# is a worrying place for your son to be" about the mother (quality watch, main d070657077b8).
# The `s` is read as part of the possessive rather than as a missing word, so "my mums" and
# "my mum's" are one reading, and "my mums been" answers about the mum.
WHO_SAID = re.compile(r"\b(?:my|our)\s+(" + "|".join(sorted(WHO, key=len,
                                                             reverse=True)) + r")(?:'s|s)?\b")
# The same names after his, her or their, which only count when the chat is not already about
# someone: "she keeps asking for her mum" on its own still says who is being asked for.
WHO_SAID_THIRD = re.compile(r"\b(?:his|her|their)\s+(" + "|".join(sorted(WHO, key=len,
                                                                         reverse=True))
                            + r")(?:'s|s)?\b")


def person(text):
    """The person this speaker names ("my mum" -> "mum"), or None when it names nobody."""
    found = WHO_SAID.search(" ".join(words(text)))
    return found.group(1) if found else None


# A line that opens with a bare pronoun is about the person the chat is already on, and a name
# that comes later in such a line can be what that person is asking about rather than a new
# subject. "my grandad has dementia" / "he keeps asking where my nan is" is the grandad asking
# after his wife: read as a new subject, the store moved the chat onto the nan, and the next
# short ask ("what do i say") was answered "a word with your nan's GP" about a woman nobody had
# said was ill. Only an indirect question moves the name off the subject this way - "he said my
# mum is ill" does report something about the mum, so it still names her.
A_BARE_PRONOUN_SUBJECT = re.compile(
    r"\A(?:and|but|so|then|now|also|still)?\s*(?:he|she|they|hes|shes|theyre)(?:'s|'re)?\b")
A_QUESTION_THEY_ASK = re.compile(
    r"\b(?:asks?|asked|asking|keeps? asking|kept asking|wonders?|wondered|wondering|"
    r"wants? to know|wanted to know|says?|said|tells?|told|thinks?|thought|forgets?|forgot|"
    r"remembers?|remembered)\b[^.?!]*?\b(?:where|what|when|why|how|who|if|whether)\b")


def _named_inside_a_question(text):
    """Whether this line's pronoun subject is asking a question that names somebody else."""
    line = " ".join(words(str(text or "").lower().replace("\u2019", "'")))
    if not A_BARE_PRONOUN_SUBJECT.search(line):
        return False
    return bool(A_QUESTION_THEY_ASK.search(line))


def person_named(text, memory=None):
    """The person the line is about: the speaker's own, or a third one when nobody is tracked.

    "my wife has dementia" then "she keeps asking for her mum" is still about the wife, so
    `her mum` names nobody new while someone is tracked. With nothing tracked, the same line
    still names the person being asked for.
    """
    who = person(text)
    if who:
        if about(memory) is not None and _named_inside_a_question(text):
            # "he keeps asking where my nan is" is still about the person the chat is on (and the
            # nan is the one being asked after), so the subject does not change on that line.
            return None
        return who
    if about(memory) is not None:
        return None
    found = WHO_SAID_THIRD.search(" ".join(words(text)))
    return found.group(1) if found else None


def about(memory):
    """The person the chat is about, as a record, or None."""
    record = memory.get("person") if isinstance(memory, dict) else None
    return record if isinstance(record, dict) and record.get("who") else None


# The kinds of trouble a line reports about a person the user looks after, most specific first.
# This is a reading of the line, so it lives in the store rather than in the module that words the
# reply: which trouble the chat is on outlives one turn, and the reply that turn gets may come from
# another lane entirely ("she keeps forgetting where things are in the kitchen" is answered by a
# knowledge entry about forgetting). chat._about_someone words each kind; nothing here decides one.
PERSON_TROUBLE = (
    # A ward they have left is good news, and the reply a friend gives is not the ward's: "my mum
    # is out of hospital" was answered "That is a worrying place for your mum to be" about a woman
    # who had just come home, and "mum was discharged from hospital today" with "Noted: ...".
    # Read first, so the hospital pattern below only keeps the wards people are still on.
    ("homeward", re.compile(
        r"\b(?:out of|home from|back from|discharged from|released from|let out of|"
        r"came out of|come out of|got out of|getting out of)\s+(?:the\s+)?hospital\b")),
    # A person who is in hospital now is not waiting for a first appointment. The words people
    # use for an admission - "went into hospital this morning", "was taken in last night",
    # "admitted on Tuesday", "kept in overnight", "she is on the ward" - are not the "in hospital"
    # of the kind below, so the line fell through to "ill", which matches the word "hospital" in
    # it, and chat answered "Worth a GP appointment for your son this week rather than next month"
    # about a boy who was already on a ward (hearty-emu, #routing 81405). A serious diagnosis is
    # the same news: "my husband has been diagnosed with a brain tumour" is not a change to raise
    # at the next appointment, because there has been no next appointment yet.
    ("hospital", re.compile(
        r"\b(?:admitted|taken|took|rushed|whisked|brought|moved|transferred)\s+"
        r"(?:in|into|to|back to)\s+(?:the\s+)?(?:hospital|ward|icu|itu|a&e|a and e|resus)\b|"
        r"\b(?:went|gone|been|is|are|was|were|kept|staying|stuck)\s+(?:in|into|back in|"
        r"back into)\s+(?:the\s+)?hospital\b|"
        # "went to the hospital" is the same news when it is the person who is ill, and a visit
        # when it is not: "my mum went to the hospital to visit her sister" keeps its own answer.
        r"\bwent (?:in)?to (?:the )?hospital\b"
        r"(?![^.?!]{0,18}\b(?:visit|see|collect|pick|drop|meet)\b)|"
        r"(?<!work )(?<!works )(?:on|in)\s+the\s+(?:ward|stroke unit|coronary care)\b|"
        r"\bkept in (?:overnight|in|for observation|for tests)\b|"
        r"\b(?:in|into) (?:intensive care|icu|itu|resus)\b|"
        r"\bdiagnosed (?:with|as having)\s+(?:cancer|a (?:brain |lung |bowel |breast |bone )?"
        r"tumou?r|leukaemia|leukemia|lymphoma|motor neurone|parkinsons?|a terminal|"
        r"something serious)\b")),
    # Being in hospital already means the care is happening: the question is how they are, not
    # another appointment.
    ("hospital", re.compile(
        r"\b(?:in|at|on|still in) (?:the )?hospital\b|\bhad an operation\b|\boperation\b|"
        r"\bsurgery\b|\bbeing (?:seen|treated|looked after)\b")),
    # Something already known and being looked after: the reply is about this change, not about
    # getting the first appointment.
    ("known", re.compile(
        r"\b(?:diagnosed|diagnosis|has dementia|has alzheimers|already (?:has|had|sees)|"
        r"since the diagnosis|under the (?:doctor|hospital|memory clinic))\b")),
    # A home with staff in it is neither hospital nor a first appointment: what they notice day to
    # day is the record a GP works from.
    ("care", re.compile(
        r"\b(?:care home|nursing home|residential home|in a home now|a home now)\b")),
    ("memory", re.compile(
        r"\b(?:forget(?:s|ting|ful)?|forgot|memory|remember(?:ing)? (?:things|where|names)|"
        r"confus(?:ed|ing)|muddled|dementia|alzheimers?|wandering|getting lost|"
        # "he got lost coming back from his walk last week" was left to the knowledge base and
        # answered "I'm sorry - that's frustrating": the past tense and the other ways people
        # say it are the same kind as "getting lost", and the kind decides the reply.
        r"gets? lost|got lost|went missing|lost (?:her|his|their) way|"
        r"wander(?:s|ed|ing)? off|took a wrong turn|losing track|"
        r"repeat(?:s|ing)? (?:himself|herself|themselves|the same "
        r"(?:thing|story|tale|question))|"
        # "my dad keeps saying the same story" is how families describe the repetition before
        # anyone says the word "memory": with only "the same thing" here, the line was read as
        # no trouble at all, so the short ask after it ("is that a sign of anything") borrowed
        # the word "story" from the chat and got a story about the word "anything".
        r"say(?:s|ing)? (?:me |us )?the same (?:thing|story|tale|question)|"
        r"tel(?:l|ls|ling) (?:me |us )?the same (?:thing|story|tale)|"
        r"ask(?:s|ing)? the same question|"
        # The examples people give instead of the word "memory": a wrong name for a thing, a
        # brother's name for their own son, the same story twice.
        r"wrong (?:name|word|words|thing)|call(?:s|ed)? (?:me|him|her|us|them) "
        # a relative who rings too much is not a wrong name: "my daughter calls me every
        # night" was getting "take a note of what you have noticed to the GP"
        r"(?!(?:all|every|each|when|if|about|back|later|again|whenever|once|twice|from|at|"
        r"in|on|to|for|with|so|yesterday|today|tomorrow|constantly|loads|lots|more|less|too|"
        r"up|out|off|over|and|or|but|urgent)\b)\w+|mixed up|"
        r"says? the same thing|told me the same|the wrong day)\b")),
    ("falls", re.compile(
        r"\b(?:fell|fallen|fall|falls|falling|tripped|tripping|trip|unsteady|wobbly on "
        r"(?:his|her|their) feet|balance)\b")),
    # "low" is not the word on its own: low on money, low pay, low iron and low blood pressure are
    # about something else, so the mood word needs to be about them or about their spirits.
    ("low", re.compile(
        r"\b(?:low mood|low spirits|feeling low|seems? low|so low|very low|a bit low|"
        r"won'?t go out|wont go out|not eating|off (?:his|her|their) food|not themselves|"
        r"no appetite)\b")),
    # Sleep is how a body reports itself, and the low-mood answers are about a person going quiet
    # and off their life: "my baby is not sleeping" then "is that normal" was answered "Months of
    # it, or losing interest in everything, deserves an appointment", which is a withdrawal from
    # life and not a baby's night. It is read after "low", because a line that has both in it
    # ("not eating and not sleeping") is the withdrawal sentence, and going off food is often the
    # first thing a family notices about someone's spirits.
    ("sleep", re.compile(
        r"\b(?:not sleeping|not sleeping through|sleeping badly|not sleeping well|"
        r"up all night|awake all night|waking (?:up )?(?:all|every) night|not sleeping at night)"
        r"\b")),
    ("ill", re.compile(
        r"\b(?:poorly|unwell|chest infection|"
        # "keeps getting" is the everyday way to say a thing goes on, and most of what follows it
        # is ordinary: a child keeps getting out of bed, a dog keeps getting on the sofa, someone
        # keeps getting distracted. What makes it an illness is the thing they keep getting, so
        # the verb asks for one of those and nothing else: "keeps getting chest infections" is a
        # report for the GP, "he keeps getting out of bed" is the night-time routine.
        r"keeps (?:getting|having) (?:a |an |the )?(?:\w+ ){0,2}"
        r"(?:infections?|colds?|coughs?|cough|temperatures?|chest|bugs?|viruses?|virus|"
        r"migraines?|headaches?|nosebleeds?|faints?|blackouts?|tremors?|shakes?|"
        r"dizzy|dizziness|breathless|sick|unwell|worse|pain|pains|swollen)|getting worse|"
        r"got worse|in pain|aches?|aching|breathless|swollen|dizzy|dizziness|"
        r"doctor said|hospital|diagnosed)\b")),
)


# A child who bounces back up has not had the kind of fall the falls answer is about, and a
# diagnosis is not a change: "my grandma has dementia" is not news for the GP today, and the
# "make this change the GP's problem" answer would invent the change.
YOUNG_PERSON = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|[1-9]|1[0-2])\s*"
    r"(?:months?|years?)?\s*old\b|\bis (?:one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve)\b|\b(?:baby|toddler|newborn|little one|little boy|little girl|"
    r"schoolboy|schoolgirl|reception class)\b")
# A row with someone is not a fall, and this is where the reading decides it for every lane:
# "me and my mum fell out" and "my dad and i fell out last week" were read as the falls trouble -
# chat answered "Falls are rarely just age ... a GP can start on all three" and the knowledge base
# gave the falls review, with a falls clinic for someone who had said no more than that they had
# argued. Falling out *of* something is a fall ("my mum fell out of bed"), so the phrase is the
# fence, not the word "out".
FELL_OUT = re.compile(r"\bf(?:ell|all|alls|alling|allen)\s+out\b(?!\s+of\b)|\bfell\s+about\b")
FALLS_FINE = re.compile(
    r"\b(?:laughed|laughed it off|no harm|wasn'?t hurt|was not hurt|unhurt|not a scratch|"
    r"slept it off|got straight (?:back )?up|jumped (?:straight )?up|ran off|carried on|"
    r"waved it off|no damage)\b|"
    r"\b(?:he|she|they|it|hes|shes|theyre)(?:'s|'re)?\s+(?:is |was |seems |looks )?"
    r"(?:fine|ok|okay|alright)\b")
# A job is not an illness. The words for a ward are the same words for a workplace - "my mum
# works at the hospital", "he works on the ward", "she is a nurse at the clinic" - and the ward
# pool answered a job with "Sorry to hear that. How is your dad doing?", which is a reply to bad
# news about somebody's health. What tells them apart is not the place but the verb of work in
# front of it, so the place is read with that verb and the kinds that own a ward stand down. The
# ward pattern above already guards the two forms it can ("work on the ward"), with a lookbehind;
# this is the same reading for the rest, in the one place every kind passes through.
A_JOB_AT = re.compile(
    r"\b(?:works?|working|worked|starts?|started|starting|got a job|gets a job|getting a job|"
    r"hired|employed|shifts?|night shift|day shift|late shift|early shift|job|jobs|career|"
    r"boss|colleague|colleagues|manager|salary|wages|pay|overtime|contract)\b"
    r"[^.!?]{0,40}?\b(?:at|in|on|for|as)\b[^.!?]{0,14}?\b(?:the\s+)?(?:hospital|ward|unit|"
    r"icu|itu|a&e|a and e|care home|nursing home|hospice|clinic|surgery|pharmacy|practice)\b|"
    r"\b(?:my|his|her|their|our)\s+(?:new\s+)?(?:job|work|shift)\b|"
    r"\b(?:works?|working|worked)\s+(?:there|here|nights|days|shifts|full time|part time)\b")
# What a line has to hold besides the job for it to be about somebody's health: a symptom, a
# change, or a worry in their own words. Closed on purpose - a job line that carries none of these
# is only news about work.
SOMETHING_WRONG = re.compile(
    r"\b(?:ill|unwell|poorly|sick|sickness|pain|painful|hurts?|hurting|aching|aches|worse|worst|"
    r"fell|fallen|falling|fainted|collapsed|diagnosed|diagnosis|dementia|alzheimers|cancer|"
    r"operation|surgery|admitted|in hospital|on the ward|intensive care|icu|a&e|"
    r"cant|cannot|can'?t|unable|stopped|keeps|kept|forgetting|forgetful|confused|"
    r"confusion|weak|weaker|breathless|bleeding|infection|temperature|"
    r"tests?|results?|scan|appointment|worried|worrying|worry|decline|declining|"
    r"not (?:been )?(?:himself|herself|themselves)|unsteady|dizzy)\b")
CHANGE = re.compile(
    r"\b(?:new|newly|worse|worsening|suddenly|all of a sudden|since|these days|lately|recently|"
    r"stopped|no longer|used to|gone downhill|going downhill|declin(?:e|ed|ing)|"
    r"getting (?:worse|more|confused|forgetful)|"
    r"(?:this|last) (?:week|month|couple of|few)|over the (?:last|past))\b")


# The turn of phrase that puts the worry after the news: "out of hospital but still very weak".
# The recovery is real, and it is not what the person is asking about.
A_WORRY_AFTER = re.compile(
    r"\b(?:but|however|though|except)\b|\bstill\s+(?:very\s+|quite\s+|really\s+)?"
    r"(?:weak|poorly|unwell|bad|badly|tired|no better|not himself|not herself|not themselves)\b")


# A child asking for the same story again is not a memory sign. The repetition reading is
# fenced for the person words that are usually a child, unless an age in the line says otherwise:
# "my son is 40 and says the same story" is still read, "my four year old says the same story"
# is not.
A_CHILDS_PERSON = re.compile(
    r"\b(?:son|daughter|kid|kids|child|children|little one|little boy|little girl|baby|"
    r"toddler|newborn|schoolboy|schoolgirl)\b|"
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|\d{1,2})[\s-]*(?:year|yr)s?[\s-]*old\b")
A_GROWN_AGE = re.compile(r"\b(?:1[89]|[2-9]\d)\b|\b(?:eighteen|nineteen|twenty|thirty|"
                         r"forty|fifty|sixty|seventy|eighty|ninety)\b")
REPEATED_SAID = re.compile(
    r"\brepeat(?:s|ing)? the same (?:story|tale|question)|"
    r"\bsay(?:s|ing)? (?:me |us )?the same (?:thing|story|tale|question)|"
    r"\btel(?:l|ls|ling) (?:me |us )?the same (?:thing|story|tale)|"
    r"\bask(?:s|ing)? the same question\b")


def trouble(text):
    """Which kind of trouble this line reports about the person it is about, or None."""
    low = " ".join(str(text).lower().replace("\u2019", "'").split())
    if A_JOB_AT.search(low) and not SOMETHING_WRONG.search(low):
        # Where somebody earns a living is not a trouble: "he works at the hospital" got "Sorry to
        # hear that. How is your dad doing?" because "at the hospital" is the words for a ward,
        # and the kinds below only made it worse once that one stood down ("Get your dad looked
        # at"). A line that says where the work is needs something actually wrong with it to be a
        # trouble at all.
        return None
    for kind, pattern in PERSON_TROUBLE:
        if not pattern.search(low):
            continue
        if kind == "known" and not CHANGE.search(low):
            continue  # a diagnosis on its own is not a change to tell the GP about
        if kind == "memory" and REPEATED_SAID.search(low) \
                and A_CHILDS_PERSON.search(low) and not A_GROWN_AGE.search(low):
            continue  # a child's favourite story, not a memory change
        if kind == "homeward" and A_WORRY_AFTER.search(low):
            # "my dad is out of hospital but he is still very weak" is a worry with good news in
            # front of it: the line's point is the weakness, and the ward question is the closer
            # reply. The kinds below keep that line.
            continue
        if kind == "falls" and (YOUNG_PERSON.search(low) or FALLS_FINE.search(low)
                                or FELL_OUT.search(low)):
            # a child who got straight back up has not had the fall this is about, and neither
            # has anybody who was only telling you they had fallen out with someone
            continue
        return kind
    return None


def _keep_person(memory, text):
    """Record the person this line is about, and keep the last one when the line says "she".

    The kind of trouble the line reports is kept with them, so the short ask two turns later ("is
    that normal", "what should i look out for") has something to lean on whatever answered the
    turn it arrived in.
    """
    turn = len(memory.get("turns") or [])
    who = person_named(text, memory)
    kind = trouble(text)
    if who:
        kept = about(memory) or {}
        if kept.get("who") != who or kept.get("said") != text.strip():
            memory["person"] = {"who": who, "said": text.strip(), "turn": turn}
        record = memory["person"]
    else:
        record = about(memory)
        if record is not None:
            record["turn"] = turn  # they are still the person being talked about
    if record is not None and kind:
        if record.get("trouble") != kind:
            record["trouble_turn"] = turn  # this line is the first to say it
        record["trouble"] = kind
    return record


def _after_an_emergency(memory):
    """True when the bot's last answer was an emergency, so nothing here is a topic to lean on.

    "my neighbour's flat is on fire" then "is it safe to go down the stairs?" is a follow-up,
    but the fire is not a subject to keep answering from: the kept words ("fire", "smoke")
    reach a knowledge entry about clearing cooking smells, and that entry then takes the turn
    from the careful continuation. Mid-emergency the topic starts again from the line itself,
    and bot/compose/fallback.EMERGENCY_AFTER holds the thread.
    """
    turns = memory.get("turns")
    if isinstance(turns, list) and turns and isinstance(turns[-1], dict):
        return turns[-1].get("module") == "safety"
    return False


# The shapes a line takes when it replaces something said before it: "sorry, it's a 10k, not a
# half", "no, Bristol not Leeds", "i meant jen", "make that july". Only the previous line is read
# this way, and only to stop a carry, so the pattern is allowed to be generous.
CORRECTION_LINE = re.compile(
    r"^[\W]*(?:oh|sorry|no|nope|actually|oops|wait|hang on)\b[^!?]{0,60}\bnot\b|"
    r"\b(?:i\s+meant|i\s+mean|make\s+that)\b|\bnot\s+(?:a|an|the)\s+[a-z]", re.I)


def _after_a_correction(memory):
    """True when the line before this one corrected something, so nothing here is carried.

    "I need tips for my first half marathon" / "sorry, it's a 10k, not a half" / "how many weeks
    do I need to train?" is a question about the 10k. The topic record still reads "half
    marathon" - a correction replaces the subject rather than starting a new one - so carrying
    its words answers the half-marathon question to someone who has just said 10k. A correction
    ends the carry for one turn: the next line that names nothing is read on its own, which is
    where it would have been without the topic to lean on.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return False
    said = turns[-1].get("user")
    if not isinstance(said, str) or not said.strip():
        return False
    return bool(CORRECTION_LINE.search(" ".join(said.lower().split())))


# The modules whose answers are the safety thread going on rather than a move away from it.
INSIDE_A_SAFETY_THREAD = ("carers_turn", "safety_cards")


def in_a_safety_thread(memory):
    """True while the bot's last real answer was an emergency and nothing has answered since.

    A number said out loud mid-emergency is not a savings plan: someone who has just been told
    to ring 999 and then says "i can put away 250 a month" has not changed the subject, and an
    arithmetic answer would take the turn from the careful continuation that thread needs. Any
    module that answers from memory rather than the line itself asks this first.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for turn in reversed([t for t in turns if isinstance(t, dict)][-3:]):
        module = turn.get("module")
        if module == "safety":
            return True
        if module in INSIDE_A_SAFETY_THREAD or module in ("greeting", None):
            # An answer inside the thread is the thread going on, not the subject changing:
            # `carers_turn` answers the turns after the card in the words for the person it is
            # about ("The drink is the part that makes the rest of it more likely"), names no
            # number, and keeps no three words of the card - so the thread was read as over two
            # turns in, and the amends question after it was handed to the chat's own pool while
            # `carers_turn` had the answer beside it (mint-brick, #13830).
            continue
        return False
    return False


# The question words people type without the apostrophe: "whats good to see", "hows the boiler
# been". `words` folds "what's" to "what" but leaves "whats" as one word, so a return line split at
# its ask word did not split, and "back to lisbon, whats good to see" named the whole clause
# ("lisbon whats good to see", five words) and so named nothing: the return was never marked, the
# guide came back word for word five turns later, and `tests.test_long`'s repeat rule failed on
# main. Only the wh-words: "its" is a possessive as often as it is "it is".
WH_WORD_WITHOUT_ITS_APOSTROPHE = re.compile(r"\b(what|how|when|where|why|who|which)s\b")


def _the_apostrophe_back(low):
    """`whats good to see` read as `what is good to see`, so the ask word is a word again."""
    return WH_WORD_WITHOUT_ITS_APOSTROPHE.sub(r"\1 is", low)


def return_target(text):
    """What a line like "ok back to the boiler" or "anyway, the laptop" names, or ""."""
    low = _the_apostrophe_back(" ".join(words(text)))
    found = RETURN_LEAD.match(low)
    if found:
        rest = low[found.end():].strip(" ,.?!")
        return _the_thing(rest)
    casual = CASUAL_LEAD.match(low)
    if not casual:
        return ""
    target = low[casual.end():].strip(" ,.?!")
    parts = target.split()
    if not parts or parts[0] not in CASUAL_OPEN:
        return ""
    return _the_thing(target)


# A helper right after the thing opens a question about it ("back to the laptop, is it worth
# servicing?", "the boiler, does that include the service?"). A helper followed by a participle or
# an adverb is the line's own verb instead: "anyway my knee has been clicking up the stairs" was
# cut at "has" and read as going back to "my knee", so the line opened no new topic and the next
# "is that bad" was answered about the flat from two turns before.
HELPER_ASKS = frozenset("""
is are was were am do does did have has had can could should would will shall if whether
""".split())
# A participle says the thing is doing something, and the ending alone cannot tell "clicking"
# from "everything": "back to the laptop, is everything ok?" names the laptop, and reading
# "everything" as the line's verb threw that question away. The words that say something is
# happening are listed instead, so a word that only ends the same way stays part of the question.
ING_VERBS = frozenset("""
aching acting adding asking baking beating becoming beginning biting bleeding boiling breaking
breathing bringing building burning buying calling carrying catching changing clicking climbing
closing coming cooking costing coughing counting crying cutting dancing dealing deciding digging
doing drawing dreaming dressing driving dropping drying eating expecting failing falling feeding
feeling filling finding finishing fitting flying following forgetting getting giving going growing
happening hating having hearing helping hiding hitting holding hoping hurting itching jumping
keeping kicking knocking landing laughing leaking leaning learning leaving lifting listening
living looking losing making meaning meeting missing moving needing opening paying picking playing
pointing pressing pulling pushing putting raining reaching reading relaxing remembering riding
ringing rising running saying seeing selling sending shaking showing singing sitting sleeping
sliding smelling smiling sneezing speaking spending spilling standing starting staying stealing
sticking stopping struggling studying swimming taking talking tasting teaching telling thinking
throwing ticking tightening trying turning waking walking wanting washing watching wearing
weighing winning wondering working worrying writing
""".split())
VERB_PHRASE_AFTER = frozenset("""
been being had got gotten not no never still always just already also now going getting doing
making taking coming putting seeing saying starting trying
""".split())


# A modal is followed by a bare infinitive and never by a participle: "would asking why hurt my
# chances" is a question of its own, and cannot be the thing doing something. "back to the
# promotion, would asking why hurt my chances" was read as "the promotion would asking" - the
# line went back to nothing, so the answer from three turns before came back word for word with
# no lead-in. The other helpers ("is", "has", "was") carry the name's own doing, as in "anyway my
# knee is clicking" / "my knee has been clicking", and those still do.
MODALS = frozenset("would could should can will shall may might must ought".split())


def _a_question_after_the_thing(rest, split):
    """Whether the words from `split` on are a question about the thing rather than its verb."""
    parts = rest.split()
    if split >= len(parts) or parts[split] not in HELPER_ASKS:
        return True
    after = parts[split + 1].strip(".,!?;:") if split + 1 < len(parts) else ""
    if not after:
        return True
    if parts[split] in MODALS and (after in ING_VERBS or after.endswith("ed")):
        return True
    return not (after in VERB_PHRASE_AFTER or after in ING_VERBS or after.endswith("ed"))


def _the_thing(rest):
    """"the laptop, which would you get?" names the laptop; "work tomorrow" names nothing."""
    asked = re.search(r"[,?!;]|\b(?:" + "|".join(sorted(RETURN_ASKS)) + r")\b", rest)
    head = rest[:asked.start()] if asked else rest
    if asked and not _a_question_after_the_thing(rest, len(head.split())):
        return ""
    parts = head.split()
    while parts and (parts[-1] in CASUAL_OPEN or parts[-1] in STOPWORDS):
        parts.pop()
    if not parts or len(parts) > 3:
        return ""
    if any(part in CASUAL_VERB or part in RETURN_TIME for part in parts):
        return ""
    return " ".join(parts)


def _asks(text):
    if "?" in text:
        return True
    return any(word in RETURN_ASKS for word in text.split())


def asks_after(line, thing):
    """Does the line ask something *after* the thing it went back to?

    The sentence people use to go back can carry a question word before the thing: "as I was
    saying, Rome" has "was" in it, and read as a whole line that looked like a question, so the
    return reply stepped aside and the greeting said "As you was saying, Rome - noted." What
    matters is what comes after the thing: "as I was saying, Rome" asks nothing, while "back to
    the laptop, which would you get?" and "coming back to the boiler, is it worth servicing?"
    do, and the answer modules take those lines.
    """
    low = _the_apostrophe_back(" ".join(words(line)))
    named = " ".join(words(thing))
    at = low.find(named) if named else -1
    if at >= 0:
        low = low[at + len(named):]
    return _asks(low)


def the_thing_asked_again(memory, text=""):
    """The line a person went back to, with the ask they made on it, or "".

    "back to lisbon, what should i see" is one breath: the return and the question about the
    thing returned to. The line as typed is read for its own words, and "back" is a body part,
    so the back-pain card answered a question about Lisbon. The store has already put the thing
    back on the table (`_resume`), so the ask is read with that thing in front of it - "lisbon
    what should i see" - which is the line the card for it is keyed on. Only a return the store
    marked as carrying an ask, and only when the thing is named in the line, so a return that
    asks nothing ("back to the boiler") is still the store's greeting.
    """
    record = resumed(memory)
    if not isinstance(record, dict) or not record.get("asks"):
        return ""
    thing = " ".join(str(record.get("asked") or "").lower().split())
    line = " ".join(str(text or "").lower().split())
    if not thing or not line:
        return ""
    at = line.find(thing)
    if at < 0:
        return ""
    tail = line[at + len(thing):].strip(" ,;:.-")
    if not tail:
        return ""
    return thing + " " + tail


def the_thing_went_back_to(memory):
    """The thing named after a return opener ("the boiler" out of "coming back to the boiler")."""
    record = resumed(memory)
    if not isinstance(record, dict) or not record.get("asks"):
        return ""
    return " ".join(str(record.get("asked") or "").lower().split())


def _resume(memory, record, target, line=""):
    """Make the earlier topic current again, and note the turn so a reply can greet the return."""
    said = dict(record)
    # The thing the person just named is the best word for what the conversation is about now:
    # "back to saving" makes the subject "saving", not a gist of the longer line they first
    # said it in, so a follow-up ("how much do I need to put by each month?") still reaches the
    # entry that word matches.
    said["subject"] = " ".join(words(target)) if target else said.get("subject") or ""
    memory["topic"] = said
    # The list of topics is what a follow-up is read against ("how much do I need to put by each
    # month?" after going back to the saving plan), so the topic gone back to is the newest entry
    # in it too: left where it was, the line read against the subject in between and got a hedge.
    topics = memory.get("topics")
    if not isinstance(topics, list):
        topics = memory["topics"] = []
    topics[:] = [other for other in topics if other is not record
                 and (other.get("text") or "") != (said.get("text") or "")]
    topics.append(said)
    memory["return_to"] = said.get("text") or target
    memory["returned"] = {"text": said.get("text") or target, "asked": target,
                          "asks": asks_after(line, target),
                          "turn": len(memory.get("turns") or [])}
    _the_answer_on_the_return(memory, said)
    return said


def _the_answer_on_the_return(memory, said):
    """Put the answer that belongs to the topic gone back to on top of the kept answers.

    The kept answers are what a follow-up that names nothing of its own is answered from ("what
    should i do first", "how long does that take"), and the newest of them is normally the right
    one because the newest answer is about what the chat is on. Going back to an earlier topic is
    the one case where that is false, and the store already knows it: it makes the returned topic
    current. Without this, the answer to the topic they went back to sat behind the answer to the
    subject in between:

        my boiler keeps losing pressure
        my daughter is 6 and starts school in september
        anyway back to the boiler   -> "Back to the boiler, then. What did you want to know about
                                        it?"
        what should i do first      -> "Apply through your council by 15 January ..."  (school)

    So the answer whose key words are the returned topic's is moved to the end of the list, which
    is all the follow-up readers need to draw on it. It stays in the same list, so a reader that
    checks the answer was really given (`newest_answer`) still checks it, and an answer about
    nothing the topic names leaves the list alone.
    """
    kept = memory.get("entry_answers")
    if not isinstance(kept, list) or len(kept) < 2:
        return
    wanted = {form for word in keywords(said.get("text") or "") for form in (word, stem(word))}
    wanted -= STOPWORDS
    if not wanted:
        return
    best, best_score = None, 0
    for record in kept:
        if not isinstance(record, dict):
            continue
        forms = {form for key in set(record.get("keys") or ()) for form in (key, stem(key))}
        score = len(wanted & (forms - STOPWORDS))
        if score > best_score:
            best, best_score = record, score
    if not best or best is kept[-1]:
        return
    kept.remove(best)
    kept.append(best)
    memory["entry_answer"] = best


def resumed(memory):
    """The earlier topic the user went back to on this turn, or None.

    Set by note(); the turn is the number of turns when the line was read, so an answer module
    knows the return happened just now and not three turns ago.
    """
    record = memory.get("returned")
    if not isinstance(record, dict) or not record.get("text"):
        return None
    if record.get("turn") != len(memory.get("turns") or []):
        return None
    return record


def current(memory):
    """The current topic record, or None."""
    record = memory.get("topic")
    if isinstance(record, dict) and record.get("text"):
        return record
    return None


def _forms(word):
    """The word and the verb it may be built from: "saving" -> "saving", "sav", "save"."""
    forms = [word]
    if len(word) > 5 and word.endswith("ing"):
        base = word[:-3]
        forms += [base, base + "e"]
    elif len(word) > 4 and word.endswith("ed"):
        base = word[:-2]
        forms += [base, base + "e"]
    return forms


def alike(one, other):
    """Two content words name the same thing: "saving" finds "save 5000", "cakes" finds "cake"."""
    for left in _forms(one):
        for right in _forms(other):
            if left == right:
                return True
            if len(left) >= 4 and len(right) >= 4 and (left.startswith(right)
                                                       or right.startswith(left)):
                return True
            if len(left) >= 5 and len(right) >= 5 and left[:5] == right[:5]:
                return True
    return False


def find(memory, text):
    """An earlier topic matching what the user named ('back to the laptop', 'back to saving')."""
    wanted = keywords(text)
    if not wanted:
        return None
    for record in reversed(memory.get("topics") or []):
        have = record.get("words") or []
        if any(alike(word, other) for word in wanted for other in have):
            return record
    return None


# "Thanks. How long does it take?" is a follow-up: the thanks is a courtesy, not the question.
LEAD_ACKS = ACKS | GREET


def _this_line(record, memory):
    """True when the topic record was written for the line being answered right now."""
    turn = len(memory.get("turns") or []) if isinstance(memory, dict) else 0
    return record.get("turn") == turn


def is_follow_up(text, memory):
    """True when a line leans on the current topic: 'how long will it take?', 'and if I...'."""
    record = current(memory)
    if not record:
        return False
    # A record made from this very line is not the thing before it. The topic is written before
    # the modules run, so on a first line `current(memory)` is the line itself: "what can i make
    # with mince" then looks like a follow-up on "mince", nothing about the entry shares those
    # words, and the answer the line has is thrown away as a different subject.
    if _this_line(record, memory):
        return False
    clean = " ".join(words(text))
    if not clean or is_ack(text) or clean in GREET:
        return False
    rest = [word for word in words(text)]
    while rest and rest[0] in LEAD_ACKS:
        rest = rest[1:]
    if rest:
        clean = " ".join(rest)
    low = clean
    if _switches(clean):
        return False
    found = words(text)
    if len(found) > 16:
        return False
    topic_words = set(record.get("words") or [])
    fresh = [k for k in keywords(text) if k not in topic_words]
    if KIND_ASK.search(low) and len(found) <= 10:
        return True
    if found[0] in CONTINUATION_START:
        if len(fresh) <= 2 and len(found) <= 8:
            return True
        if PROPERTY.search(low) and len(fresh) <= 3 and len(found) <= 10:
            return True
    if any(word in REFERRING for word in found) and len(fresh) <= 3:
        return True
    return len(fresh) <= 1 and len(found) <= 8


def context(memory, n=2):
    """The last n topic texts, oldest first, for understanding a follow-up in context."""
    records = memory.get("topics")
    if not isinstance(records, list):
        return []
    return [r.get("text", "") for r in records[-n:] if r.get("text")]


def expand(text, memory):
    """The line plus the topic it follows, e.g. 'how long will it take? (earlier: ...)'."""
    record = current(memory)
    if record and is_follow_up(text, memory):
        earlier = context(memory) or [record["text"]]
        return text + " (earlier: " + " / ".join(earlier) + ")"
    return text


# Words that say how much or how long rather than what about: a line made only of these is
# asking about the thing the line before was about ("how long will it take, start to finish?").
# The asks that want a figure out of the answer: these are what a borrowed fact can get wrong.
MEASURED = frozenset(("how_long", "how_much", "how_many", "how_often", "time", "heat",
                      "money", "amount", "temperature"))
# A request to carry on rather than a question about what was just said: "what should I do
# about it?" asks for the next step, not for a sentence of the last answer.
PROCEED = ("what should i do", "what do i do", "what now", "what next", "then what",
           "what about now", "where do i go from here")
ASK_ONLY = frozenset("""
long much many time times often usually cost costs price prices worth expensive cheap cheaper
temperature hot warm cold heat minute minutes hour hours day days week weeks month months year years
step steps best first next last thing things way ways take takes long quick quickly soon
start finish it that them they there this these those one ones again
""".split())

# A question word in front of a subject names nothing: it is the asking, not the thing.
_LEAD_QUESTION = re.compile(r"^(?:whats?|which|how|when|where|who|why|do|does|did|is|are|"
                            r"can|could|should|would|will)\s+", re.I)

# The phrase after these belongs to someone else: "a birthday cake for my son" is about the cake.
_RELATION = re.compile(r"\b(?:for|with|to|about|because|from)\s+(?:my|our|his|her|their)\b")

# A "without" clause on a method question says what to leave out, and the thing left out is not
# what the conversation is about: after "how do i stop snoring without a machine" the follow-up
# "is there anything else" put the machine back in ("is the stop snoring machine anything
# else") and got the plug's fuse answer, because the subject kept the word the answer had just
# dropped. Only a question that asks how, though - "my first christmas without her" is about the
# absence, and that line's subject is the christmas and the person.
_FRAME_ASK = re.compile(r"\b(?:how|what|which|where|when|any way|ways|can|could|should|help)\b")
_WITHOUT_CLAUSE = re.compile(r"\s*\bwithout\b.*$")
# The verb a plan opens with is part of the action, not part of the thing: "cook a turkey" is
# about the turkey. Kept as a list of the verbs people start a plan with.
_VERBS = ("bake", "cook", "make", "build", "write", "paint", "plant", "grow", "fix", "clean",
          "decorate", "buy", "book", "prepare", "host", "throw", "plan", "learn", "start",
          "assemble", "sew", "knit", "roast", "boil", "fry", "grill", "set", "sort", "get",
          "replace", "repair", "install", "paint", "renovate", "organise", "organize")
# The words a wish or a plan opens with, and the verbs it can hand over to. A phrase that starts
# with one of these is naming the thing it wants, not the wanting: "we are thinking of getting a
# dog" is about the dog, and read as "thinking getting dog" the follow-up "how long will it take"
# asked the whole phrase a question and got an answer about toenails back.
_WISH = ("thinking", "thought", "thinking about", "considering", "planning", "hoping", "wanting",
         "looking", "interested", "keen", "trying", "dreaming", "weighing up")
_ACTION = ("get", "getting", "have", "having", "lose", "losing", "go", "going", "save", "saving",
           "learn", "learning", "try", "trying", "start", "starting", "stop", "stopping",
           "quit", "quitting", "book", "booking", "take", "taking", "do", "doing", "see",
           "seeing", "buy", "buying", "move", "moving", "change", "changing", "adopt",
           "adopting", "rescue", "rescuing")


# A verb with its particle is how a thing is reached, not the thing: "how do i get rid of slugs"
# is about the slugs, and with the particle left in the store called the chat "rid slug" - a
# recap said "We were on the rid slug", and the follow-up "will they come back" had a subject no
# module could use. The verb on its own is stripped further down (`_LEAD`); this takes the
# particle with it. Only pairs people say as one word are listed, so "i went back to work" and
# "it came back after a week" are untouched: back is not a particle of those verbs.
_PHRASAL = (
    "get rid of", "getting rid of", "got rid of", "get out of", "getting out of",
    "get on top of", "getting on top of", "get on with", "look after", "looking after",
    "look into", "looking into", "cope with", "coping with", "deal with", "dealing with",
    "put up with", "putting up with", "run out of", "running out of", "ran out of",
    "take care of", "taking care of", "keep up with", "keeping up with", "kept up with",
    "keep on top of", "keeping on top of", "keep track of", "keeping track of",
)
_PHRASAL_RE = re.compile(r"\b(?:" + "|".join(sorted((re.escape(p) for p in _PHRASAL),
                                                    key=len, reverse=True)) + r")\b")


def _gerund(verb):
    """The -ing form of a verb, spelled the way people spell it: get -> getting, make -> making."""
    if verb.endswith("ie"):
        return verb[:-2] + "ying"
    if verb.endswith("e") and not verb.endswith(("ee", "ye", "oe")):
        return verb[:-1] + "ing"
    if (len(verb) > 2 and verb[-1] not in "aeiouwxy" and verb[-2] in "aeiou"
            and verb[-3] not in "aeiou"):
        return verb + verb[-1] + "ing"
    return verb + "ing"


_VERB_WORDS = tuple(sorted({v for v in _VERBS} | {_gerund(v) for v in _VERBS if len(v) > 2}))
_WISH_RE = re.compile(
    r"^(?:(?:please|so|and|but|well|ok|okay)\s+)?"
    r"(?:i'?m|im|i\s+am|we'?re|we\s+are|i\s+have|i'?ve|"
    r"(?:i|we|you|they|he|she)\s+(?:am|are|is|was|were))?"
    r"(?:\s+(?:also|still|just|really|probably|maybe|now|only))?\s*"
    r"(?:" + "|".join(sorted(set(_WISH) | set(_ACTION), key=len, reverse=True))
    + r")\b(?:\s+(?:to|of|about|on|at|into|up|for))?\s+(?:(?:a|an|the|another|some|any|my|our)\s+)?")
_LEAD = re.compile(r"^(?:please\s+)?(?:i'?m|im|i\s+am|i\s+(?:want|need|would like|'?d like)|"
                   r"we'?re|we\s+are|i'?ve|i\s+have)?\s*"
                   r"(?:to\s+)?(?:(?:" + "|".join(_VERB_WORDS) + r")\s+)"
                   r"(?:a|an|the|my|our|some|any|two|three|this|that)?\s*")

# A correction opens with words that say "not the last thing, this one": "actually it's a
# funeral", "sorry, a funeral", "no i meant a funeral". They are not part of the thing the chat
# is on, so "what should i wear" after one asks about the funeral and not about "actually".
_CORRECTION_LEAD = re.compile(
    r"^(?:(?:no|nope|sorry|apologies|actually|oops|correction|wait)[\s,.!-]+|"
    r"my\s+mistake[\s,.!-]+|"
    r"i\s+(?:mean|meant|said|did\s+meant|didn'?t\s+mean)\s+(?:to\s+say\s+)?|"
    r"(?:its|it'?s|that'?s)\s+(?:actually\s+)?)+", re.I)
# A time is not the thing a chat is about. "im going to a funeral on friday" is about the
# funeral, and the follow-up "what should i wear" is about the funeral too; keeping "friday" on
# the end made the subject's head a day of the week and the follow-up read as being about that.
_TIME_WORDS = frozenset("""monday tuesday wednesday thursday friday saturday sunday
january february march april may june july august september october november december
week weekend month year morning afternoon evening night tonight today tomorrow yesterday
soon later midday noon am pm clock oclock""".split())
# "I'm thinking about getting a bike", "I'm looking at a new laptop": the opening says they are
# considering something, and the thing is what comes after it. Without this the subject carries
# the considering with it ("thinking getting bike") and no module that reads it can use it.
# The word that opens the phrase a person uses when they are deciding: "i'm thinking about
# getting a bike", "i'm looking at a new laptop", "i'm after a sofa". They name the thing they
# are considering, not a thing they have, and it is the thing a "which one?" is about.
#
# "getting" and "buying" only open one when a determiner or an adjective comes next, because the
# same words are states and not purchases: "we're getting married next year" is about a wedding,
# and stripping "getting" leaves "married", a word that fits half the knowledge base.
_CONSIDERING = re.compile(
    r"^(?:(?:i'?m|im|i am|we'?re|we are)\s+)?(?:"
    r"(?:thinking (?:of|about)|looking (?:at|for|into|round at)|considering|in the market for|"
    r"keen (?:on|to)|after)"
    r"|(?:getting|buying)(?=\s+(?:a|an|the|some|any|another|my|our|your|their|his|her|its|this|"
    r"that|these|those|new|used|second|old|decent|proper|cheap|good|nice|little|big|small|first|"
    r"one|two|three)\b))\s+")
# "getting married", "buying a house": the "getting" of a purchase opens a phrase about the thing
# only when the thing follows it. What follows these words here is a state or a verb, so the line
# is not about a purchase and its own verb is part of what it is about.
_BUYING_A_STATE = re.compile(
    r"^(?:(?:i'?m|im|i\s+am|we'?re|we\s+are)\s+)?(?:get|getting|buy|buying)\b(?!\s+(?:a|an|the|"
    r"some|any|another|my|our|your|their|his|her|its|this|that|these|those|new|used|second|old|"
    r"decent|proper|cheap|good|nice|little|big|small|first|one|two|three)\b)")
_MAX_SUBJECT = 4


def _strip_considering(source):
    """The line without the words that only say they are thinking of getting the thing."""
    while True:
        stripped = _CONSIDERING.sub("", source)
        if stripped == source:
            return source
        source = stripped


# A word that only counts or measures: a sum of money, a weight, a length of time. It is the unit
# of a figure, never the thing a chat is about on its own.
_A_FIGURE = frozenset("""pound pounds quid euro euros dollar dollars grand kilos kilo kg stone
    stones lb lbs ounce ounces gram grams litre litres pint pints mile miles minute minutes hour
    hours week weeks month months year years""".split())


# The chatty words in front of an announcement: "and one more thing", "ok so quick question".
_HANDOFF_THROAT = re.compile(
    r"^(?:(?:and|oh|ooh|ok|okay|so|but|right|ah|er|um|hmm|also|plus|hey|ta|anyway|then|just|"
    r"well|sorry)[\s,:-]*)+")


def _only_a_handoff(head):
    """Whether a clause only announces that something is coming: "one more thing", "quick one".

    The hand-off phrases are the reading engine's own list, so a phrase added there is read here
    too (bot/understanding/lexicon.py, `HANDOFF_LEADS`). A clause that goes on to name something
    of its own is not an announcement: "the last thing i need is another bill" is about the bill.
    """
    text = " ".join(str(head or "").lower().split()).strip(" ,.;:!?-")
    text = _HANDOFF_THROAT.sub("", text).strip(" ,.;:!?-")
    for lead in sorted(lexicon.HANDOFF_LEADS, key=len, reverse=True):
        if text == lead or (text.startswith(lead) and not keywords(text[len(lead):])):
            return True
    return False


# The days that are a date and not an event with things to arrange. "my son's birthday is next
# saturday" says when, and what the line is about comes after the "and": the cake they are going
# to bake. A wedding or a party is left out on purpose, because "i have a wedding in june and i
# have to do a speech" is about the wedding and the speech is part of it.
_DATE_OCCASIONS = frozenset(stem(word) for word in
                             """birthday birthdays anniversary christmas xmas easter""".split())
# The words a date is made of besides the day itself: "next", "this", "on".
_DATE_FILLER = frozenset("""next last this coming on in at the of""".split())
# What somebody is making: the verb and the thing it makes ("bake him a cake", "doing a cake").
# A determiner has to follow, so "i dont know what to do" and "i have no idea what to get her"
# are not read as a thing being made.
_MAKING_A_THING = re.compile(
    r"\b(?:make|making|bake|baking|cook|cooking|prepare|preparing|build|building|do|doing)\s+"
    r"(?:\w+\s+){0,2}?(?:a|an|the|some)\s+[a-z']+")


_PEOPLE = frozenset()


def _the_people():
    """The words that name a person in the user's life ("my son"), in the forms keywords keeps.

    facts.py's own list, imported late: facts.py reads this module through named.py, so an import
    at the top of the file would come back with a half-built module. Read once and kept, because
    gist runs on every line.
    """
    global _PEOPLE
    if not _PEOPLE:
        from .facts import RELATIONS
        _PEOPLE = frozenset(form for word in RELATIONS for form in (word, stem(word)))
    return _PEOPLE


def _a_word_of_a_date(word):
    """Whether a content word can be part of a date and nothing else: "saturday", "next",
    "christmas", "son".

    The forms are compared as well as the words, because `keywords` stems what it keeps:
    "christmas" comes back as "christma".
    """
    forms_ = (word, stem(word))
    return (any(form in _DATE_OCCASIONS for form in forms_)
            or any(form in _TIME_WORDS for form in forms_)
            or word in _DATE_FILLER
            or any(form in _A_FIGURE for form in forms_)
            or any(form in _the_people() for form in forms_))


def _only_a_date(clause):
    """Whether a clause only says when a day is: "my son's birthday is next saturday".

    Every content word has to be one of the day, a word of the date, a figure or a person: a
    clause that says anything else ("my knee hurts", "my mum is 78 and keeps falling") is about
    that thing, and the person in it is what the line is about.
    """
    kept = keywords(clause)
    if not kept or not any(stem(word) in _DATE_OCCASIONS for word in kept):
        return False
    return all(_a_word_of_a_date(word) for word in kept)


def _the_thing_after_a_date(text):
    """The clause that names the thing a dated line is about, or "".

    "my son's birthday is next saturday and i want to bake him a cake" led with the date, so the
    subject came back as "son birthday": the chat was on nothing to bake, the allergy line after
    it attached to no thing, and "how long will that take?" was carried as "how long will son
    birthday take", which no entry answers. The thing they are making is the subject.

    A comma is the same break as an "and" here: "my sons birthday is next saturday, im doing a
    cake" is one dated line with one thing being made.
    """
    parts = re.split(r"\b(?:and|but)\b|[,;]", text, maxsplit=1)
    if len(parts) < 2:
        return ""
    head, tail = parts
    if not _only_a_date(head) or not keywords(tail):
        return ""
    return tail if _MAKING_A_THING.search(tail) else ""


def gist(text):
    """The short noun phrase a line is really about: "birthday cake", "kitchen tap", "turkey".

    "A birthday cake for my son, 8, this weekend." is about the birthday cake; "Cook a turkey
    for Christmas." is about the turkey; "the tap in the kitchen keeps dripping" is about the
    tap in the kitchen. It keeps the words that carry the meaning and drops the rest.
    """
    source = " ".join(str(text or "").lower().split())
    source = _CORRECTION_LEAD.sub("", source)
    # "never mind, how do i boil an egg" is about the egg: the words that announce a new subject
    # are the switch, not the subject.
    for switcher in sorted(SWITCHERS, key=len, reverse=True):
        if source.startswith(switcher):
            source = source[len(switcher):].lstrip(" ,.!-")
            break
    # A clause that only dates the day is the date of the thing, not the thing: what they are
    # making after the "and" is what the chat is on.
    dated = _the_thing_after_a_date(source)
    if dated:
        source = dated
    # A verb with its particle comes off before the "for" split as well: "i cant cope with the
    # noise" was split at its own "with" and the subject came back as "cant cope".
    source = " ".join(_PHRASAL_RE.sub(" ", source).split())
    source = _RELATION.split(source)[0]
    whole = source
    if _FRAME_ASK.search(source):
        # the clause emptied, and the line kept as it was when the clause is all there is
        trimmed = _WITHOUT_CLAUSE.sub("", source).strip(" ,.;:!?")
        if trimmed and keywords(trimmed):
            source = trimmed
    # The words that say they are deciding come off first, before the "for" split: "i'm in the
    # market for a sofa" would otherwise be split at its own "for" and be about "the market".
    source = _strip_considering(source)
    # "thinking of getting a dog", "trying to lose a stone": the wishing and the doing are how
    # the thing is reached, not the thing. Only the front is dropped, so "my driving" stays.
    # "getting" and "buying" only open such a phrase when a determiner follows: the same words
    # are a state ("we're getting married next year"), and stripping "getting" from it leaves
    # "married", a word that fits half the knowledge base.
    buying = bool(_BUYING_A_STATE.match(source))
    wished = False
    for _ in range(3 if not buying else 0):
        stripped = _WISH_RE.sub("", source)
        if stripped == source or not stripped.strip(" ,.;:!?"):
            break
        source = stripped
        wished = True
    before_split = source
    # The purpose after a sum is a better subject than the sum: see _A_FIGURE below.
    segments = re.split(r"\b(?:for|tonight|today|tomorrow|yesterday|this|next)\b", source)
    source = segments[0]
    if not wished and not buying:
        source = _LEAD.sub("", source.strip(" ,.;:!?"))
        # A question left over as a subject keeps its question word: "whats the weather like" is
        # about the weather, not about "what weather", and a follow-up that puts the subject back
        # on the end of itself ("what should i wear" + "what weather") is not a line anything
        # answers.
        while True:
            trimmed = _LEAD_QUESTION.sub("", source)
            if trimmed == source or not trimmed.strip():
                break
            source = trimmed
    source = _strip_considering(source)
    # A comma opens a clause about the thing, not another thing: "i'm after a new phone, mine is
    # four years old" is about the phone, and "mine four years old" is not part of its name.
    # Unless the clause before it is only an announcement: "one more thing, my car failed its mot
    # on a tyre" is about the car, and read as the announcement it was about nothing at all -
    # empty, so `_about_record` skipped the record and the conversation kept the subject it had
    # two turns before, which is how a question about the MOT was answered about back pain.
    head, _, after_handoff = source.partition(",")
    source = after_handoff if after_handoff.strip() and _only_a_handoff(head) else \
        re.split(r"[,;]", source)[0]
    kept = [word for word in keywords(source) if word not in ASK_ONLY]
    while kept and kept[-1] in _TIME_WORDS:
        kept.pop()
    if kept and all(word in _A_FIGURE for word in kept):
        # A sum and its unit are the figure, not the thing: "im trying to save 500 pounds for a
        # trip to spain" is about the trip, and read as "pound" the follow-up "how long will it
        # take?" became a question about losing weight, the one entry keyed on pounds. What the
        # money is for is the subject, so the purpose after the "for" is read instead.
        for part in segments[1:]:
            later = [word for word in keywords(part)
                     if word not in ASK_ONLY and word not in _TIME_WORDS]
            if later and not all(word in _A_FIGURE for word in later):
                kept = later
                break
    if not kept and wished:
        # "im trying to save 3000 for a trip to iceland next summer" loses everything it has to
        # the time split, because what is left before it is a figure. A figure is a poor subject
        # but an empty one is worse: the follow-up has nothing to be about at all. So the whole
        # line, minus the times and the ask, is the last word.
        for source in (before_split, whole):
            kept = [word for word in keywords(source)
                    if word not in ASK_ONLY and word not in _TIME_WORDS]
            if kept:
                break
    if not kept:
        return ""
    return " ".join(kept[:_MAX_SUBJECT])


# "my flat is small", "the kitchen is tiny", "our bedroom is cramped": a line that only says
# how much room there is is about the thing we were already on, not a subject of its own. In
# "im thinking of getting a cat" / "my flat is small" / "what should i get for it", the flat
# says how much room the cat's things may take, and the "it" in the last line is still the cat.
_ROOM_LIMIT = re.compile(
    r"^(?P<head>(?:my|our|the|his|her|their|this|that|your)?\s*[a-z' ]{0,18}?)\s*"
    r"(?:is|are|was|were|seems|feels|gets)?\s*"
    r"(?:a bit |really |quite |very |so |too |dead |proper )*(?:small|tiny|cramped|poky|narrow)$")

# Only a space inside the home folds back into the subject the conversation was already on: a
# flat, a kitchen or a bedroom is what limits the cat's things. A garden, an allotment or a van
# named with its size is a new thing, and "the garden is small" / "what should i plant in it"
# is about the garden - folding that back answered it about the cat.
_HOME_SPACES = frozenset((
    "flat", "house", "home", "room", "rooms", "kitchen", "bedroom", "bedrooms", "bathroom",
    "lounge", "hall", "hallway", "landing", "garage", "loft", "attic", "basement", "cellar",
    "study", "porch", "conservatory", "utility",
))


def _room_limit(text):
    """The home space a line only says the size of, or "" when it says more than that.

    "my flat is small" -> "my flat", "the kitchen is really tiny" -> "the kitchen",
    "my kitchen is tiny and the oven is broken" -> "" (the line names something else too),
    "the garden is small" -> "" (a place with room in it, but not a space inside the home).
    """
    words_ = " ".join(str(text or "").lower().split())
    found = _ROOM_LIMIT.match(words_)
    if not found:
        return ""
    head = found.group("head").strip(" ,.;:!?-")
    if not head:
        return ""
    return head if head.split()[-1] in _HOME_SPACES else ""


def _thing_of(memory, record):
    """The record a detail line points back at, or None.

    A line that only says a detail of the thing the chat is on ("he is allergic to nuts" after
    a birthday cake) is still a topic: the answer it reached is about the cake, and the line
    itself is in the turns. But ask a follow-up of it - "how long will it take, start to
    finish?" - and the words it lends are the nuts, which reach nothing, so the answer already
    given comes back with "Same as before" in front of it. The record carries the thing it was
    a detail of, and that is the subject a follow-up leans on.
    """
    if not isinstance(record, dict):
        return None
    back = str(record.get("of") or "")
    if not back:
        return None
    for other in reversed(memory.get("topics") or []):
        if isinstance(other, dict) and str(other.get("text") or "") == back:
            return other
    return None


def _about_record(memory):
    """The last topic that names something, rather than only saying how much room there is.

    When every topic so far is a size line there is nothing to fold back into, so the record is
    read as it always was: "my kitchen is tiny" is about the kitchen tiny, and a follow-up after
    it is answered the way it was before this rule.
    """
    records = memory.get("topics")
    if not isinstance(records, list):
        return current(memory) or {}
    for record in reversed(records):
        if not isinstance(record, dict) or _room_limit(record.get("text")):
            continue
        if _names_nothing(record):
            # A line that only leans on what is on the table ("and how long will it take", "lol")
            # is not what the conversation is about: the record before it is. Read as the subject,
            # the follow-up's own two words ("long take") gave every reader that asks the subject
            # nothing at all, and the ask about the boiler reached no boiler.
            continue
        return record
    return current(memory) or {}


def _names_nothing(record):
    """Whether a topic record says nothing of its own about what is being talked about."""
    if " ".join(str(record.get("subject") or "").split()):
        return False
    return not gist(record.get("text") or "")


def subject(memory):
    """What the conversation is about now, as a noun phrase other modules can use.

    The plan the person gave if there is one ("birthday cake"), otherwise the gist of the
    current topic ("xmas dinner"). Empty when the conversation has no subject yet.
    """
    known = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    record = _about_record(memory)
    # A detail of the thing we are on is about the thing: "he is allergic to nuts" after a
    # birthday cake leaves the cake as the subject, so the next line ("how long will it take?")
    # is the cake's question and not the nuts'.
    thing = _thing_of(memory, record)
    if thing is not None:
        record = thing
    # A return names its topic ("back to saving"), and that word is what the line after it is
    # about, so it outranks the gist of the longer line the topic first came from.
    now = " ".join(str(record.get("subject") or "").split()) or gist(record.get("text") or
                                                                    topic_text(memory))
    planned = gist(known.get("plan") or "")
    if planned and now and planned in now:
        return planned  # the plan names the thing better than the line it came from
    return now or planned


def topic_text(memory):
    record = current(memory)
    return record["text"] if record else ""


# A follow-up that asks how long the thing takes, with the thing left out: "how long will it
# take?". The action in it ("lose a stone", "learn spanish") is what the question is about, and
# it is what the knowledge base is indexed by, so the ask is written out with it on the end.
DURATION_ASK = re.compile(r"\bhow (?:long|many (?:hours|days|weeks|months|minutes|years))\b")

# The words a bare duration ask is made of. Anything else in the line ("how long does it keep in
# the fridge") is a question of its own: it names the thing it is about and is left alone.
DURATION_WORDS = frozenset("""
how long many much hours hour days day weeks week months month minutes minute years year will
would does do did is was it that this one they them take takes taken cost costs last lasts
to for the a an in at on about
""".split())

# The verbs an ask about time can be about: "how long does it take to <verb> ...". A topic that
# is a thing rather than an action ("my boiler is making a noise") is not here.
ACTION = frozenset("""
learn lose get fix build paint clean save train study grow cook bake make do sort finish write
read find repair install set move pack apply book plant hire buy sell replace service bleed
insulate lay tile sand plaster dig compost prune knit sew drive fly travel play practise
practice teach organise organize plan prepare recover heal quit stop start cut reduce pay earn
pass sit cycle swim run walk redecorate declutter tidy clear chop boil roast freeze iron mend
patch sharpen assemble
""".split())

MAX_ACTION = 6       # "lose a stone", not the whole sentence the person said it in

# The words that come before an action the person does themselves: "i want to lose a stone",
# "im trying to quit sugar", "we're planning to move". Everything before the action has to be
# one of these, or the action is somebody else's: "my boiler is making a noise" is about the
# boiler, and the answer to "how long will it take" is not "to make a noise".
PERSON_LEAD = frozenset("""
i we me us my our she he they her his their them 'm im am was were is are have had been
really just also still only
want wanna wanted need needed try trying plan planning plans hope hoping think thinking
like 'd would will going keep keeping kept start started starting get getting got
""".split())

# An action named as the thing to do is about the person doing it ("the best way to learn
# spanish", "any tips for how to save"): after these words the action is theirs.
ACTION_AFTER = frozenset("to of about".split())


def _the_action_word(line):
    """The first word of the line that is the person's own action, and its base form.

    "im thinking of getting a rescue dog" opens on "getting": the ask about time is about the
    dog, and "get a rescue dog" is the phrase the answer is indexed by. Looking at every word,
    not only the ones after "to", is what finds it - "i want to lose a stone" puts the action
    after "to", "im learning to drive" puts it first.
    """
    for index, word in enumerate(line):
        found = forms(word) & ACTION
        if not found:
            continue
        before = line[:index]
        if before and before[-1] in ACTION_AFTER:
            pass  # "the best way to learn spanish" is the person's own doing
        elif any(word not in PERSON_LEAD for word in before):
            continue  # "my boiler is making a noise" is about the boiler
        # The base form is the one the list has; "getting" is "get", "learning" "learn".
        return index, sorted(found, key=len)[0]
    return None, None


def action(memory):
    """The action the conversation is on ("lose a stone", "learn spanish"), or "".

    A topic that is a thing rather than an action ("my boiler is making a noise") has none, so
    the caller names the thing its own way.
    """
    said = " ".join(words(topic_text(memory)))
    if not said:
        return ""
    line = said.split()
    index, base = _the_action_word(line)
    if index is None:
        return ""
    # "lose a stone and eat better" is one action, not two: what follows is another ask.
    tail = " ".join(line[index:])
    tail = re.split(r"\b(?:and|but|because|so|then|when|if|before|after)\b", tail)[0]
    words_of_the_action = tail.split()[:MAX_ACTION]
    words_of_the_action[0] = base
    return " ".join(words_of_the_action).strip()


def written_out(text, memory):
    """A bare duration ask written out with the action in it.

    "how long will it take?" after "i want to lose a stone" -> "how long will it take to lose a
    stone?", the question the knowledge base has an entry for. None when the line is not a bare
    duration ask, or the conversation is on a thing rather than an action, so the caller keeps
    its own way of naming what the answer is about.
    """
    low = " ".join(words(text))
    if not low or not DURATION_ASK.search(low):
        return None
    if any(word not in DURATION_WORDS for word in low.split()):
        return None
    done = action(memory)
    if not done:
        return None
    said = " ".join(str(text).split()).rstrip("?.! ")
    return said + " to " + done + "?"


# One attribute of the thing on the table, asked on a line of its own. After "im making bread" the
# person's next line is "and the oven temperature", which names no thing at all: the entries read
# the word "oven" and answered the repair card ("the heating element is almost always the fault"),
# and after "she wants a bike" the line "which size" reached the women's clothes chart. The thing
# is on the table and the attribute is the whole of the line, so it is written out with the thing:
# "oven temperature for bread", "how long does a chicken take", "what size bike do i need".
ONE_ATTRIBUTE = (
    (re.compile(r"\b(?:temperature|heat)\b"), "oven temperature for {thing}"),
    (re.compile(r"\b(?:time|timing|duration)\b"), "how long does {thing} take"),
    (re.compile(r"\b(?:size)\b"), "what size {thing} do i need"),
    (re.compile(r"\b(?:price|cost)\b"), "how much does {thing} cost"),
)
# Every word such a line can have: the attribute itself and the frame around it, and nothing else.
# A line with one word more is about something of its own ("and the oven fan is noisy") and keeps
# the answer it had.
ATTRIBUTE_WORDS = frozenset("""the a an and so ok okay or what which how about oven temp
temperature heat time timing duration size price cost much long does do i need it take
for of""".split())
# A thing named on the line before, unless that line named a count or a person rather than a
# thing: "im making bread" / "for 6 people" / "and the oven temperature" is still about the bread.
NOT_A_THING = frozenset("""it its that this these those they them there here thing things one
ones more less some any people person someone anyone everybody everyone you u me us we i""".split())
# A line that ends in a state is complaining about a thing, not naming one: "my bus is always
# late" is a bus that keeps coming late, and "the time" after it is how late, not "how long does
# bus alway late take" (which reached the coach fares). The word the line ends on is the state.
A_STATE = frozenset("""late early broken broke leaking noisy loud quiet slow fast cold hot warm
freezing boiling dirty clean empty full stuck blocked jammed wrong old new cheap expensive
rubbish useless dead faulty missing gone off mouldy soggy dry wet burnt raw undercooked""".split())


def _named_a_thing(line):
    """Whether a line named a thing at all, rather than an attribute of one or a state of one."""
    thing = gist(line)
    if not thing or thing in NOT_A_THING:
        return ""
    if all(word in ATTRIBUTE_WORDS for word in thing.split()):
        # "and the oven temperature" / "which size": an attribute line names no thing of its own,
        # so the thing is whatever the chat was on before it ("sofa", not "size").
        return ""
    if thing.split()[-1] in A_STATE:
        return ""
    return thing


def _the_thing_on_the_table(memory):
    """The thing the last few lines named, as few words ("bread", "bike"), or ""."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    for turn in list(reversed(turns))[:4]:
        line = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        thing = _named_a_thing(line)
        if thing:
            return thing
    return ""


def attribute_of_the_thing(text, memory):
    """A line that asks one attribute of the thing on the table, written out with the thing.

    None when the line is not only an attribute, or the chat has no thing to put in it, so the
    caller keeps the answer it would have given.
    """
    low = " ".join(words(text))
    if not low or len(low.split()) > 5:
        return None
    if any(word not in ATTRIBUTE_WORDS for word in low.split()):
        return None
    frame = None
    for pattern, said in ONE_ATTRIBUTE:
        if pattern.search(low):
            frame = said
            break
    if frame is None:
        return None
    thing = _the_thing_on_the_table(memory)
    if not thing:
        return None
    return frame.format(thing=thing)


# A line that adds a fact or a limit to what we are already on, without naming it again:
# "he's allergic to nuts" after a cake, "we've only got 50 pounds" after a present.
DETAIL = re.compile(
    r"\b(?:allerg\w*|intoleran\w*|vegetarian|vegan|coeliac|gluten|free\b|diet\w*|budget|cheaper|"
    r"expensive|afford|only (?:got|have)|no (?:time|room|oven|car)|can't|cannot|couldn't|"
    r"doesn't|don't|won't|hate[sd]?|love[sd]?|prefer[s]?|instead|substitut\w+|swap|without|"
    r"left ?over|freez\w*|reheat\w*|shelf life|keeps? for)\b", re.I)


def key_subject(text, memory=None):
    """The key words of the entry a line is about, in the fewest words.

    It is the part of a knowledge entry's key that the line actually used, so a long question
    comes back as its subject: 'how long do I cook a 2kg chicken?' -> ['chicken'], 'any tips for
    Rome in July?' -> ['rome']. Knowing just the subject is what lets a follow-up ('and if I
    stuff it?') be read as being about the chicken and not about its cooking time. When the
    line on its own reaches no entry, the earlier topics in memory are tried, so a follow-up of
    a follow-up still finds the thing they were talking about.
    """
    if memory is not None:
        # The thing a detail points back at is what the line after it is about: the words of
        # "he is allergic to nuts" reach the cake's allergy entry, and a follow-up ("and if I
        # leave the nuts out?") keyed on "nuts" reaches nothing.
        for record in reversed(memory.get("topics") or []):
            if not isinstance(record, dict) or str(record.get("text") or "") != str(text):
                continue
            if _this_line(record, memory):
                break  # the line on the table now is read on its own words
            thing = _thing_of(memory, record)
            if thing is not None:
                found = _key_subject(str(thing.get("text") or ""))
                if found:
                    return found
            break
    found = _key_subject(text)
    if found:
        return found
    if memory is not None:
        for record in reversed(memory.get("topics") or []):
            text_ = record.get("text") if isinstance(record, dict) else None
            found = _key_subject(str(text_ or ""))
            if found:
                return found
    return keywords(text)[:3]


# The words a key uses to say what is being asked rather than what it is about: a key of
# ('chicken', ('how long', 'time', 'cook', 'oven')) is about a chicken, and the ask half of it
# says nothing about the subject of a follow-up.
ASK_PART = frozenset("""how what when where why which who whose long much many time often far
soon""".split())

# What a thing costs is asked for, not named. These are the words the price table keys its
# second group with: "how much does a plumber charge" is about the plumber, and "i charge it
# every night" is about nothing the price table knows. They are read as asking words only where
# the question is whether the line named the subject of an entry (see `_asked_only`), not
# everywhere: a price line is still a subject of its own for the rest of the store.
PRICE_ASK = frozenset("""charge charges charging costing cost costs price prices priced quote
quotes quoted fee fees rate rates expensive cheaper afford free worth payable""".split())

# The words that ask for advice, which name no thing of their own: "any tips for a long shift"
# asks how to get through a shift, and the "tips" in it says how the ask is put, not what it is
# about. Every card in the body table is keyed to the phrase "any tips for", so reading it as a
# word the line named made the knee card the subject of a line about a shift: the chat lent the
# line its old subject ("... knee hurting") and the card answered a question nobody asked.
# These are read as asking words only where the question is whether the line named the thing, the
# same places PRICE_ASK is read that way - a line about a rubbish tip still leans on "tip".
ASKS_FOR_ADVICE = frozenset("""tip tips advice advise advising hint hints help helps helping
ideas idea suggestion suggestions thoughts thought recommend recommended""".split())


def _the_part_a_complaint_is_about(text):
    """The body part a line complains about, or None.

    Lazy, because the store keeps no facts of its own: the part table is the knowledge base's.
    """
    from ..knowledge.body import the_part_that_hurts
    return the_part_that_hurts(text)


# The words that start the part of a complaint saying what brought it on: "my back has been
# killing me **since i moved the sofa**". The thing named after them is the cause, not the
# subject of the complaint; "when" is left out because "my knee hurts when i run" is a line about
# the running as much as the knee, and its follow-up belongs to the running answer.
CAUSE_OF_THE_COMPLAINT = re.compile(r"\b(?:since|after|because|from)\b")


def _the_cause_words(text):
    """The words after the cause in a complaint, or an empty set when it names none."""
    found = CAUSE_OF_THE_COMPLAINT.search(str(text or "").lower())
    if not found:
        return set()
    return set(words(str(text or "").lower()[found.end():]))


def _subject_words_to_carry(record, text, memory):
    """The topic's words a follow-up carries, with a complaint's cause left behind.

    "my back has been killing me since i moved the sofa" is a line about the back, and the
    follow-up "its sort of a dull ache on the left side" is about the back too. Its key words in
    key order are ['sofa', 'back'], so the follow-up was read as an ache of the sofa and got the
    furniture-repair card. A complaint carries the part it complains about, not the thing it
    blames for it. A line with no cause ("i pulled a muscle in my groin") carries what it always
    did, because the groin answer needs the muscle with it.
    """
    topic_text = str((record or {}).get("text") or "") if isinstance(record, dict) else ""
    subject = key_subject(topic_text, memory)
    part = _the_part_a_complaint_is_about(topic_text)
    cause = _the_cause_words(topic_text)
    if part and cause and part not in words(text) and not _the_part_a_complaint_is_about(text):
        kept = [word for word in subject if word not in cause or word == part]
        if part not in kept:
            kept.insert(0, part)
        return kept
    return subject


def _key_subject(text):
    """The key words of the entry a line reaches, in key order, or None when it reaches none.

    Every part of the key the line used comes back, not just the first, so a dripping tap gives
    'tap' and 'dripping': a follow-up needs both to reach the same entry again. A part made of
    asking words ("how long", "time") is left out: it is the ask, not the subject.
    """
    found = words(text)
    item = _entry(text)
    if item is None:
        return None
    out = []
    for part in item.key:
        for alternative in (part if isinstance(part, tuple) else (part,)):
            if not isinstance(alternative, str) or not _said(alternative, found):
                continue
            part_words = words(alternative)
            if not ASK_PART.intersection(part_words):
                out.extend(part_words)
            break
    return out or None


def _said(phrase, found):
    """True when the words of a phrase are in the line, folded so eggs/egg still match.

    The words are taken in the order the line said them, because a key phrase is two words said
    in that order ("urine infection", "blood in the urine", "litter tray"). A caller that hands
    over a set has already thrown the order away, and a set is read in whatever order the hash
    seed happened to give it: the same line was answered from the cat's urine-infection entry
    under one seed and from the human one under another, because the two words of the phrase
    landed beside each other in one run and not the other. So an unordered bag is read as what it
    is - every word of the phrase said somewhere in the line - and the answer is the same under
    every seed. Callers that have the line in hand pass its words in order and get the tighter
    reading.
    """
    wanted = [stem(word) for word in words(phrase) if word not in STOPWORDS]
    if not wanted:
        return False
    if isinstance(found, (set, frozenset)):
        return all(word in {stem(one) for one in found} for word in wanted)
    have = [stem(word) for word in found]
    n = len(wanted)
    return any(have[i:i + n] == wanted for i in range(len(have) - n + 1))


def _where_the_topic_lands(topic):
    """The entry the topic is about, read past the verb it happens to share with an entry's ask.

    "My sourdough keeps coming out flat" reaches the shelf-life entry, because that entry asks for
    "keep" and names a sourdough: the line has said the thing and the ask's own verb, and nothing
    more is needed for it to score. Read without that verb the line is about the loaf that comes
    out flat, and that is the entry the trouble belongs to - "keeps coming out" is how the
    trouble goes on, not a question about how long the loaf lasts. Only a word the entry itself
    asks with is dropped, and only when dropping it lands somewhere else: every other topic is
    read exactly as it was.
    """
    found = _entry(topic)
    if found is None:
        return None
    asked = set()
    for part in getattr(found, "ask", ()):
        for phrase in (part if isinstance(part, tuple) else (part,)):
            if isinstance(phrase, str):
                asked.update(words(phrase))
    if not asked:
        return found
    kept = [word for word in words(topic) if stem(word) not in asked and word not in asked]
    if len(kept) == len(words(topic)):
        return found
    other = _entry(" ".join(kept))
    if other is None or other is found:
        return found
    # The words left have to name the thing the topic is about: two of them, as everywhere else.
    if len(_key_words_of(other) & set(keywords(topic))) < 2:
        return found
    return other


def an_entry_for(text):
    """The knowledge entry a line reaches on its own, or None.

    Read by the store for the reply on screen: a line the knowledge base answered is a fact, and a
    line it did not is a nod or a reading, which is not something to confirm.
    """
    return _entry(text)


def _entry(text):
    """The knowledge entry a line reaches, or None (the knowledge base is read, not changed)."""
    from ..knowledge.lookup import find  # lazy: the store does not need the facts
    return find({"clean": str(text), "words": words(text)})


# Words that point back at a *thing* we were on. "he", "she", "him" and "her" are left out on
# purpose: a pronoun about a person points back at that person, not at the thing the chat was
# about, so "she keeps forgetting where things are in the kitchen" after "my mum moved in with
# us last month" must not be read with the move glued onto it - the entry that reached was the
# packing plan, which is advice for a different problem.
# "he" and "she" are here on purpose: "she likes gardening and wine" after "my mums birthday is
# on saturday" is a detail of that birthday, and widening it is what makes the gift answer work.
# What a pronoun about a person does *not* mean is that the line is a follow-up question on the
# thing we were on, so `person()`/`about()` below keep who it is, and a line that reports
# something not right about them is answered about them (bot/modules/chat.py, _about_someone).
REFERRING_WORDS = frozenset("""it its that this these those they them there their one ones
he she him her his""".split())

# "Is it worth paying a plumber or shall I have a go" is not about the thing we were just on:
# that "it" is the sentence's own subject and the real subject comes after it, so the line
# pointed back at nothing and yet drew on the last answer's sentence. "Is it worth it" does
# point back, so only the frame with a word after it is dropped.
DUMMY_IT = re.compile(
    r"\b(?:is|was|would|will)(?:n't)?\s+it\s+(?=(?:worth|ok|okay|better|best|rude|normal|"
    r"fine|safe|possible|legal|allowed|weird|strange|acceptable|polite|sensible|wise|cheaper|"
    r"easier|harder|a good idea|a good thing|too late|too soon)\b"
    # The frame brings its own subject along: a word like "a", "the" or "my" before the noun
    # says the line is about a thing of its own ("is it worth paying a plumber"). Without one
    # the line is about what we were already on ("is it worth scarifying in autumn" after the
    # lawn), so its "it" does point back and the frame stays.
    r"[^?]*\b(?:a|an|the|some|any|my|your|our|their|his|her|another|one|two|three)\s+\w)")

# Words that aim a question at something without naming it: "how often should I go?" is a whole
# question about the thing the last line was about, and nothing in it reaches an entry.
ASK_MORE = frozenset("""often frequent frequently regularly sooner soonest longer quick quicker
soon best good""".split())
# A verb that only stands in for the action of the topic: "how often should I go?", "when do I
# use it?", "what should I do?". It names no subject, so it is not what makes the line its own.
STAND_IN = frozenset("""go going gone get getting do doing done use using happen happening
happens be is are was were should shall can could would will want wants need needs have has
take taking start starting help helps helping check checks checking put putting place try tries
trying fix fixing sort sorting ease easing improve improving avoid avoiding prevent preventing
change changes changing add adding expect expecting""".split())


# A line about the chat itself - what the bot knows, what was said - is not a line about the
# topic: "what do you know about me" after "i'm trying to save money" is the store's own
# question, and reading it as the saving ask gives the money advice to somebody who asked what
# the bot had kept. The words name nothing, so only this list can tell the two apart.
ABOUT_THE_CHAT = re.compile(
    r"\b(?:what\s+(?:do|did)\s+you\s+(?:know|remember|have|hear|got)"
    r"|what\s+have\s+(?:i|you)\s+(?:told|said|mentioned|got)"
    r"|what\s+did\s+i\s+(?:say|tell|mention)"
    r"|what\s+(?:am\s+i|are\s+we)\s+(?:up\s+to|on\s+about|planning|doing)"
    r"|remind\s+me\s+(?:what|who|when|where)"
    r"|what\s+were\s+we\s+(?:talking|speaking|on)\s+about"
    r"|do\s+you\s+(?:remember|know)\s+(?:me|my|what|who|that))\b")


# A line that asks something: a question mark, or a question word at the start of one of its
# clauses. Only asking lines are read with the topic's words carried over them.
# The ask words, with the contraction people type instead of the apostrophe: "whats a good
# breakfast" is the same ask as "what is a good breakfast", and read as a statement it was not an
# ask at all - so the follow-up "and for lunch" found no question to put lunch into and the
# breakfast answer came back, then the "covered above" card claimed lunch was in it.
ASK_CUE = re.compile(
    r"\?|(?:^|\b)(?:what|which|how|why|when|where|who|whose)(?:'?s|'?re)?\b"
    r"|(?:^|\b)(?:should|shall|can|could|would|will|does|did|is|are|am|any|anything"
    r"|something\s+else)\b")


# A line that is only the thing it asks about, with the asking left off: "any games?", "and
# drinks", "what about pudding", "anything else". People ask this way in the middle of a plan -
# the plan is on the table, so the question is about a part of it that the line just names. On its
# own the line is a statement ("any games" has no verb and no question word in front), so it is
# read as the ask it is: the thing named, asked about in the situation the chat is on.
ELIDED_ASK = re.compile(
    r"^(?:(?:ok|okay|so|and|also|plus|or|then|right|yeah|yes|oh|em|um)\s+)*"
    r"(?:any|anything|something|more|else|another|other|rest|what\s+about|how\s+about|"
    r"idea|ideas|tip|tips|thoughts|suggestions)\b")


# A line that puts a new thing in the place of the one the question asked about: "how much
# protein in porridge oats" / "and in a slice of bread" / "what about two slices". People talk
# this way over several turns - the ask is settled and only the thing changes - and the line on
# its own carries no asking at all ("and in a slice of bread" has no question word and no verb),
# so it is read as the last question asked with its thing said again.
SAME_ASK = re.compile(r"^(?:(?:ok|okay|so|and|also|plus|or|then|right|yeah|yes|oh)\s+|"
                      r"(?:what|how)\s+about\s+)", re.I)
# A line that only counts ("what about two slices") names the thing it counts in the turn before.
COUNTING = frozenset("""one two three four five six seven eight nine ten eleven twelve a an some
few couple half slice slices piece pieces cup cups bowl bowls portion portions glass glasses
handful handfuls tin tins can cans spoon spoons tablespoon tablespoons teaspoon teaspoons each
more""".split())

# The words the question puts before the thing it asks about: everything up to the preposition
# that introduces it ("how much protein in", "how many calories in", "what is the best time for").
THE_TAIL = re.compile(r"\b(?:in|for|of|at|on|with|from|into|about)\b", re.I)


def _the_last_question(memory):
    from ..understanding import understand  # lazy: the store does not need the reading engine
    for turn in reversed([one for one in (memory.get("turns") or []) if isinstance(one, dict)]):
        said = str(turn.get("user") or "").strip()
        if "?" in said or understand(said, memory).get("asks"):
            return said
    return ""


def how_much_of_the_thing_in_hand(line, memory):
    """The last question in the chat, with this line's count of the thing in hand in it.

    "how much protein in porridge oats" / "and in a slice of bread" / "what about two slices": the
    last line only counts, so on its own it is a statement with no thing in it ("two slices" of
    what?), and the bot punted or answered a bread entry. Read as the question the chat asked,
    with the count and the thing the turn before named, it is "how much protein in two slices
    bread" - the figure the person asked for. Only a line that *only* counts takes this reading:
    a line that names its own thing is a new thing to look up, and the answers' own paths read
    those. Returns "" when the line is not that shape, or when the question thus read reaches
    nothing.
    """
    said = str(line or "").strip()
    if not SAME_ASK.match(said):
        # "i only have half a kg" counts too, but it is a statement about what they have, not a
        # follow-up asking the same question about it.
        return ""
    body = SAME_ASK.sub("", said)
    counted = words(gist(body))
    if not counted or not all(word in COUNTING or word.isdigit() for word in counted):
        return ""
    asked = _the_last_question(memory)
    if not asked:
        return ""
    head = ""
    for match in THE_TAIL.finditer(asked):
        head = asked[:match.end()]
    from ..understanding import understand  # lazy, as above
    if not head or not understand(head + " " + body, memory).get("asks"):
        return ""
    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    before = str((turns[-1] if turns else {}).get("user") or "")
    # The thing being counted is the one the turn before named ("and in a slice of bread" ->
    # bread), never a word the question already has.
    thing = [word for word in words(gist(before))
             if word not in words(head) and word not in words(said)]
    if not thing:
        return ""
    read = " ".join(words(head) + counted + thing)
    if not read or _entry(read) is None:
        return ""
    return read


def elided_ask(text):
    """True when the line asks about a thing it names with the asking left off.

    "any games" and "what about drinks" are questions, but they carry no question word of their
    own and no verb, so the understanding engine reads them as statements. Only short lines
    count: "any games for a party of ten" already asks its own question and is left alone, and
    so is a line that names a measure ("any idea how long"), which is a different ask.
    """
    said = str(text or "").lower().strip()
    if not said or len(words(said)) > 5:
        return False
    if not ELIDED_ASK.match(said):
        return False
    # "any idea how long" asks for a figure, and it is read as the ask it is already. The "how"
    # of "how about pudding" is not one of those: it is the elision itself.
    asked = re.sub(r"^(?:(?:ok|okay|so|and|also|plus|or|then|right|yeah|yes|oh|em|um)\s+)*"
                   r"(?:how|what)\s+about\s+", "", said)
    return not re.search(r"\b(?:how|when|where|why|which|who)\b", asked)


def names_nothing(text):
    """True when a line asks something and names nothing it could be about.

    'how often should I go?' and 'why is that happening?' are answered from what the last line
    was about; 'how do I cook a chicken?' names a chicken and is left alone, and a question
    about what the bot knows is not about the topic at all.
    """
    return not _content_words(text)


def _content_words(text):
    """The words of a line that could name a thing of its own, the ask words taken out.

    "how many weeks should I train" keeps only "train": a figure the line asks for is not a thing,
    and the thing here is the training.
    """
    if ABOUT_THE_CHAT.search(str(text or "").lower()):
        return []
    return [word for word in words(text)
            if word not in STOPWORDS and word not in ASK_ONLY and word not in ASK_MORE
            and word not in STAND_IN]


# A follow-up that puts the pronoun where the subject belongs: "how long does it take?" after
# "im buying a house" asks how long the thing the chat is on takes, and the knowledge base
# answers exactly that with the subject in the pronoun's place ("how long does buying a house
# take"). The whole line has to be the shape - a line that names its own subject after the verb
# ("how long does it take to get a passport") carries nothing.
LONG_IT_TAKES = re.compile(
    r"^\s*(?P<head>how long (?:does|do|will|would|is|are|should|can|could))\s+"
    r"(?:it|that|this|they|he|she)\s+take\s*[?.!]*$", re.I)
# The person the topic opens with, so the phrase can stand on its own: "im buying a house" is
# "buying a house", and "i want to learn the guitar" is "want to learn the guitar".
TOPIC_OPENS_WITH = re.compile(r"^\s*(?:i(?:'m|m| am| have| 've| want| need)?|we(?:'re|re| are)?|"
                              r"i've|ive|i'd|id)\s+", re.I)


def _the_topic_phrase(topic):
    """The topic as the phrase a frame can take: "im buying a house" -> "buying a house"."""
    said = " ".join(str(topic or "").lower().split()).strip(" .,;:!?")
    said = TOPIC_OPENS_WITH.sub("", said).strip()
    return said if len(said.split()) >= 2 else ""


def _a_length_of_the_job(item):
    """Whether the entry is keyed to "how long ... take": the length of doing the thing.

    "how long does it take" after "im painting the kitchen" reaches the entry keyed to how long
    the paint itself lasts, and the answer it gives ("five to ten years") is a wrong fact about
    a job. A carry is only right when the entry answers the length of doing it, which its own key
    says with the asking words and "take" in the same group.
    """
    for part in getattr(item, "key", ()) or ():
        said = set()
        for phrase in (part if isinstance(part, tuple) else (part,)):
            if isinstance(phrase, str):
                said.update(words(phrase))
        if said & {"take", "takes", "taking"} and said & {"how", "long", "time"}:
            return True
    return False
# How long to stay is asked with the place in the line ("how many days in edinburgh"), and the
# knowledge base keeps a table of days per city. A follow-up that asks it without the place -
# "how many days", "how many nights", "how long should i go for" - is about the trip the chat is
# on, so the place the topic names goes into the line where that table wants it.
STAY_ASK = re.compile(r"\b(?:how (?:many|much) (?:days|nights|time)|how long)\b")
# The words the line may be made of and still be nothing but that ask: "how long should i go for"
# is the whole question, "how many days should i rest my ankle" is a question about an ankle.
STAY_ONLY = frozenset("""how many much long days day nights night should shall i we you go going
there it for a an the in of time stay staying spend would will do can could need needs then""".split())
# A city in the topic is the place of a stay only when the topic says the person is going there.
# "why is edinburgh so windy" and "i live in edinburgh" name the same city, and a holiday length
# is no answer to either: the frame is what makes the city the place of a trip.
TRIP_FRAME = re.compile(
    r"\b(?:going|go|goes|off|trip|holiday|vacation|visit|visiting|fly|flying|travelling|traveling|"
    r"travel|heading|head|booked|booking|break|away|weekend|nights?|days)\b", re.I)
# The words that say the city is where somebody lives, or where they have been: the same city in
# the same kind of line, and only a trip frame in front of it makes it somewhere they are going.
LIVES_THERE = re.compile(
    r"\b(?:live|lives|living|lived|move|moves|moved|moving|relocate|relocating|relocated|"
    r"emigrate|emigrating|grew up|grow up|born|work|works|working|commute|commuting)\b", re.I)


def the_city_of(topic):
    """The city of the days-per-city table the topic names, or None."""
    from ..knowledge.travel import CITY_DAYS, _find_in  # lazy: the store needs no facts
    return _find_in(str(topic or "").lower(), CITY_DAYS)


def the_country_of(topic):
    """The country of the where-to-go table the topic names, or None.

    A country is a trip the same way a city is, and the length of it is answered from the cities
    its card names: "we are going to portugal in june" and then "how long should we go for" was a
    search hedge, because only the cities-per-day table was carried.
    """
    from ..knowledge.travel import WHERE_TO_GO, _find_in  # lazy: the store needs no facts
    return _find_in(str(topic or "").lower(), WHERE_TO_GO)


def asks_how_long_to_stay(line):
    """Whether the line is shaped like an ask for how long, as a stay ask is."""
    return bool(STAY_ASK.search(str(line or "").lower()))


def going_there(place, topic):
    """Whether the topic says the person is going to the place, not living in it.

    "im planning a trip to edinburgh" is a trip; "i live in edinburgh", "my sister lives in
    lisbon" and "i went to edinburgh last year" are not, and the stay length answers none of
    them - a confident "Two full days in Edinburgh" to a person who lives there is worse than
    the punt main gives.
    """
    said = str(topic or "").lower()
    for match in LIVES_THERE.finditer(said):
        # The place has to be the thing they live in, not one mentioned later in the line.
        if str(place) in said[match.end():match.end() + 40]:
            return False
    return bool(TRIP_FRAME.search(said))


def a_stay_with_the_place(line, topic):
    """The stay-length ask with the place the topic names in it, or None.

    The table is reached with the city in the line and not by the topic's words put on the end:
    "how many days planning trip" is the trip plan's own key, and its "keep one day free in the
    middle" is then read back as the answer to how long to stay ("One day.").
    """
    lowered = str(line or "").lower()
    if not STAY_ASK.search(lowered):
        return None
    if [word for word in words(lowered) if word not in STAY_ONLY]:
        return None
    from ..knowledge.travel import CITY_DAYS, _find_in  # lazy: the store needs no facts
    if _find_in(lowered, CITY_DAYS):
        return None  # the line names its own city: that is the city the ask is about
    place = the_city_of(topic) or the_country_of(topic)
    if not place or not going_there(place, topic):
        return None
    return lowered.strip().rstrip("?.!").strip() + " in " + place

# The words that stand in for the subject: "when do those go in" after tomatoes is "when do
# tomatoes go in", and the subject added to the end of the line reaches nothing.
POINTING_WORD = re.compile(r"\b(?:it|that|this|those|these|them|they|one|ones)\b", re.I)


def _the_ways_of_saying_it(stem_of, line, cands):
    """The follow-up with the subject carried, said the two ways it can be said.

    A follow-up that names nothing takes the topic's words with it: "how often should I go?"
    after "I want to start running" is "how often should I go running". When the line points
    back with a word of its own ("when do those go in"), the subject is what that word stands
    for, so it is put in its place rather than added after it - "when do those go in tomatoes"
    reaches no entry, and "when do tomatoes go in" is the planting one.
    """
    for cand in cands:
        carried = " ".join(cand)
        yield stem_of + " " + carried, carried
    if POINTING_WORD.search(str(line or "")):
        for cand in cands:
            carried = " ".join(cand)
            yield " ".join(POINTING_WORD.sub(carried, str(line), count=1).lower().split()), carried


# A price, a count or a length asked of a bare thing is answered by the thing the chat is on: "im
# learning to drive" and then "how much do lessons cost" is the lessons card, and the line cannot
# reach it because the word that says which lessons they are ("driving") is not on it. The topic's
# own word goes in front of the thing, and only a thing the last answer named is widened - the
# answer already said "Lessons run 25 to 40 pounds an hour", so the line is about what was on the
# table, not a guess at what they meant.
# The words that say how the person feels about a thing rather than what it is: the reading
# engine's own two sets, so a verdict it learns to hear is a verdict here too.
A_VERDICT = NEGATIVE | POSITIVE

A_BARE_MEASURE = re.compile(r"\b(?:how much|how many|how often|how long|how far|how soon)\b")
# The words a measure ask is made of. What is left of the line is the thing it asks about.
MEASURE_WORDS = frozenset("""cost costs costed price priced charge much many more less long often
far soon take takes taking time times need needs needed spend spent pay paid get got worth
there it that this""".split())


def _the_last_answer(memory):
    """The bot's last reply, or ''."""
    turns = (memory or {}).get("turns") or ()
    for one in reversed(turns):
        said = str((one or {}).get("bot") or "")
        if said:
            return said
    return ""


def _the_topics_on_the_chat(topic=None, memory=None):
    """The topic in hand first, then the ones the chat has been on, newest first."""
    out = []
    for one in reversed((memory or {}).get("topics") or ()):
        said = str((one or {}).get("text") or "")
        if said and said not in out:
            out.append(said)
    said = str(topic or "")
    if said in out:
        out.remove(said)
    if said:
        out.insert(0, said)
    return out


def _the_thing_a_measure_is_of(line, topic=None, memory=None):
    """The bare thing a measure ask names, when the chat has an answer to be a follow-up on."""
    if not _the_last_answer(memory):
        return None
    said = str(line or "")
    if not A_BARE_MEASURE.search(said.lower()):
        return None
    on_the_chat = set()
    for one in _the_topics_on_the_chat(topic, memory):
        on_the_chat.update(keywords(_the_topic_phrase(one) or one))
    for word in keywords(said):
        if word in MEASURE_WORDS or word in on_the_chat:
            continue
        return word
    return None


def _with_the_word_before(line, word, thing):
    """The line with `word` put in front of the thing it asks about, or None."""
    said = str(line or "")
    for found in re.finditer(r"[A-Za-z']+", said):
        if stem(found.group(0).lower()) == thing:
            return (said[:found.start()] + word + " " + said[found.start():]).strip()
    return None


def _how_they_feel(word):
    """True when the word says how the person feels about the thing rather than what it is.

    A topic's entry is keyed on the whole of what they said - "hate my job" - so the words it
    lends a follow-up include the verdict. "what should i do" widened with "hate" and "job"
    reached the entry for a strict teacher, because "hate" is a word on that key too, and the
    person who said they hated their job was told what to do about a teacher. The verdict words
    are the reading engine's own two sets, so a word it learns to hear as a verdict is not a
    subject here either.
    """
    word = str(word or "")
    if not word:
        return False
    if word in A_VERDICT:
        return True
    return any(form in A_VERDICT for form in forms(word))


def _keyed_to(keyed, word):
    """Whether a key holds the word, in any of the forms it takes ("driving" for "drive")."""
    word = str(word or "")
    if word in keyed or stem(word) in keyed:
        return True
    return any(word in forms(key) for key in keyed)


def _a_measure_of_the_topic(line, topic=None, memory=None):
    """The measure ask widened with a topic word, or None.

    The chat may have moved on since the thing was on the table - "im learning to drive", then
    "my test is in march", then "how much do lessons cost" - so the topics the chat has been on
    are tried newest first. Only an entry keyed to both the topic's word and the thing counts, so
    a topic the knowledge base knows nothing about widens nothing.
    """
    thing = _the_thing_a_measure_is_of(line, topic, memory)
    if thing is None:
        return None
    said = set(words(line))
    for one in _the_topics_on_the_chat(topic, memory):
        for word in keywords(_the_topic_phrase(one) or one):
            if word in said or word in MEASURE_WORDS:
                continue
            widened = _with_the_word_before(line, word, thing)
            if not widened:
                continue
            found = _entry(widened)
            if found is None:
                continue
            keyed = _key_words_of(found)
            if thing in keyed and _keyed_to(keyed, word):
                return widened
    return None


def carry_the_ask(line, topic, understood=None, memory=None):
    """A follow-up that names nothing takes the topic's own words with it, or None.

    'how often should I go?' after 'I want to start running' is read as 'how often should I go
    running', which the knowledge base answers. Only the words of the topic the knowledge base
    knows on their own are added, so a topic that mixes a subject with its trouble keeps both
    ('why is that happening?' after a flat sourdough is read as 'why is that happening sourdough
    flat'), and a line that names its own subject is only carried when the whole of it reaches
    an entry that the line itself named.
    """
    lowered = str(line or "").lower()
    if ABOUT_THE_CHAT.search(lowered):
        return None
    # "What should I do about it?" is a request to carry on with what the bot has already said,
    # not a fresh question about the topic's words: carrying them asks the back-pain entry again
    # and the paragraph comes back word for word. It is left to the next-step reply.
    if any(phrase in lowered for phrase in PROCEED):
        return None
    # Only an ask is carried. A line that only states something ("we have a 3 year old" after a
    # cat) names nothing either, and reading it as the topic's ask gave the cat's vet advice to
    # somebody telling the bot about their child.
    elided = elided_ask(line)
    if not ASK_CUE.search(str(line or "").lower()) and not elided:
        return None
    # The line read with the topic's own words first, and the situation only when that finds
    # nothing: the topic's words already reach the answer often enough ("im planning a kids
    # party" / "any games" is the party games), and a situated read in front of it took the
    # party games off them and handed over the board games for a group of adults. What the
    # situation may do is find an answer the topic's words cannot reach at all.
    carried = _carry_the_words(line, topic)
    if carried is not None:
        return carried
    # "should i stop", "should i give up", "should i carry on" name the advice and not the thing
    # it is about. After the card about a sore knee the line is about the running, and the bot
    # answered it "You're not boring me. Take as long as it needs" - the stop read as the talk,
    # because a follow-up is the whole line and the reader that keeps the whole line is the one
    # that decides a "should i stop" is about the conversation.
    doing = _the_ask_with_its_doing(line, topic)
    if doing is not None:
        return doing
    # A price or a count of a bare thing the answer already named is the thing with the topic's
    # word in front of it ("how much do lessons cost" after "im learning to drive").
    measured = _a_measure_of_the_topic(line, topic, memory)
    if measured is not None:
        return measured
    if elided and not _the_answer_covers_it(line, memory, understood):
        return _an_elided_ask_situated(line, topic, understood)
    return None



# A bare advice ask: the person asks whether to stop, give up, carry on, cut back, rest, and the
# thing it is about is the chat's, not the line's.
ADVICE_ONLY = re.compile(
    r"^(?:so|and|but|ok|okay|well|then|hmm|erm|um|oh|ah|right|alright|just|also)?[\s,]*"
    r"(?:should|shall|can|could|do|must)\s+i\s+"
    r"(?:stop|quit|give\s+up|carry\s+on|keep\s+going|keep\s+at\s+it|cut\s+back|hold\s+off"
    r"|rest|wait|go\s+on|start|start\s+again|bother)"
    r"(?:\s+(?:now|then|for\s+now|for\s+today|today|tonight|talking|chatting|going\s+on))?"
    r"[\s.!?]*$", re.I)


def _the_ask_with_its_doing(line, topic, last_id=None):
    """The bare advice ask read with the chat's own word, or None.

    The word that carries it is the one that takes the ask somewhere new: the topic's own card
    is what the chat has just been given, so a word that only reaches that card again ("should i
    stop knee" after the sore-knee card) says nothing the person does not have. "should i stop
    running" reaches the entry about stopping, which is what they asked.
    """
    if not ADVICE_ONLY.match(str(line or "")):
        return None
    whole = _entry(str(topic or ""))
    said = words(line)
    for word in keywords(str(topic or "")):
        if word in said:
            continue
        tried = str(line or "").strip() + " " + word
        found = _entry(tried)
        if found is None or found is whole:
            continue
        if last_id and getattr(found, "id", None) == last_id:
            # The answer they already have, said again: the word that changes nothing.
            continue
        return tried
    return None


def the_advice_ask_with_its_doing(understood, memory):
    """A bare "should i stop" read as the ask about the chat's own doing, or None.

    "my knees hurt when i run" then "should i stop" is whether to stop the running, and read on
    its own the line is a question about the conversation, which is why the bot answered it
    "You're not boring me. Take as long as it needs." The chat is what says which stop it is, so
    the reading takes the chat's own word - the one that reaches an answer the person does not
    already have - and the line as typed stays what every quote is kept from.

    Only where the carried ask reaches an entry. A stop that the chat's words cannot turn into a
    question ("should i stop" after "i hate my job") is left for the reply that can answer it
    honestly, which is the one about the person.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line:
        return None
    record = memory.get("topic")
    if not isinstance(record, dict) or not record.get("text"):
        return None
    last = memory.get("last_answer")
    last_id = last.get("id") if isinstance(last, dict) else None
    doing = _the_ask_with_its_doing(line, str(record.get("text") or ""), last_id)
    if doing is None:
        return None
    reading = dict(understood)
    reading["clean"] = " ".join(doing.lower().split())
    reading["words"] = words(reading["clean"])
    return reading

def _the_answer_covers_it(line, memory, understood=None):
    """True when the answer just given already has the step this line narrows.

    "we are painting the kitchen this weekend" / "what about the ceiling": the ceiling is part of
    the room that answer was about, and its reply is the same sentence said for the ceiling
    ("Same for the ceiling: use a mid-sheen, eggshell or bathroom paint"). A fresh search for the
    words reaches the general how-to-paint card instead, which says less than the answer they are
    quoting back. A part of the plan the answer never touched - "any games" after the food for a
    picnic - is what the situation is for, and is left to it.

    The reading is `detail`'s own, so the two cannot disagree about which lines belong to the
    answer: this is the line `detail.answer_for` will answer, and it answers it better.
    """
    if not isinstance(memory, dict) or not memory:
        return False
    from . import detail  # local: the package imports this module
    # The reading the follow-up arrives in has its articles taken out ("what about ceiling"),
    # and a detail opens on one ("what about the ceiling"), so the line as it was typed is asked
    # too: the person's own words are the ones that say which part of the answer they mean.
    asked = [str(line or "")]
    typed = str(understood.get("text") or "") if isinstance(understood, dict) else ""
    if typed and typed not in asked:
        asked.append(typed)
    asked += [put_back for put_back in (_with_the_article(one) for one in asked) if put_back]
    return any(detail.answers_the_line(one, memory) for one in asked)


# "what about ceiling" is how a line arrives once the answers' module has rewritten the bare ask:
# the article goes with the ask words. A detail opens on one ("what about the ceiling"), so the
# guard asks the words back with it in rather than missing the line it is there to protect.
ABOUT_A_BARE_THING = re.compile(
    r"^(?P<open>(?:(?:ok|okay|so|and|but|also|well|yeah|right)\s+)*(?:what|how)\s+about)\s+"
    r"(?P<thing>(?!the\b|a\b|an\b|this\b|that\b|these\b|those\b|both\b|just\b)\w+)",
    re.I)


def _with_the_article(line):
    """The line with "the" put back before a bare thing ("what about ceiling"), or None."""
    found = ABOUT_A_BARE_THING.match(str(line or ""))
    if found is None:
        return None
    said = str(line)
    return found.group("open") + " the " + said[found.start("thing"):]


# "all the time", "most of the time", "these days": a frequency the thing happens with, not a
# thing the chat is on. The words are read off the phrase, so the same words said plainly ("what
# time is it", "on the day") still count as the topic's own.
A_FREQUENCY = re.compile(
    r"\b(?:all|most|half|the\s+whole|every|each|any|much\s+of)\s+(?:of\s+)?(?:the\s+)?"
    r"(?:time|times|day|days|week|weeks|month|months|while)\b"
    r"|\bat\s+the\s+moment\b|\bthese\s+days\b", re.I)


def _only_said_as_a_frequency(topic):
    """The words of the topic it says only inside a frequency phrase, which name no thing."""
    text = str(topic or "")
    left = set(words(A_FREQUENCY.sub(" ", text)))
    return {word for word in words(text) if word not in left}


PROPERTY_ASK = re.compile(r"^\s*(?:and|so|ok|okay|also|but)?\s*[,:]?\s*(?:what|which|how)\b")


def _asks_a_property_and_nothing_else(text):
    """"what temperature", "and how hot": a line that asks a property of the thing in hand.

    A line that states one ("he has a temperature") is not this: it is a thing about him, and the
    line after it is still about that. The understanding engine asks the same question of the line
    an answer leans on, with its own word list, so that neither package imports the other.
    """
    low = str(text or "").strip().lower()
    if not PROPERTY_ASK.match(low):
        return False
    found = keywords(low)
    return bool(found) and all(word in MEASURE_WORDS for word in found)


def _carry_the_words(line, topic):
    """The line widened with the topic's own words, or None when they reach no entry.

    The whole of the ordinary carry, and the place the topic's own words get their first say:
    only a line that reaches nothing here is read with the situation the chat is on.
    """
    # The stay-length ask below is read off the line as typed, and the name it reads it into was
    # never bound here: any chat whose topic named a city raised a NameError on the way through
    # this reader, so the carry was lost for that line and everything after it.
    lowered = str(line or "").lower()
    # "how long does it take?" is the one shape where the subject goes in the pronoun's place
    # rather than on the end of the line: "how long does it take house" reaches a different
    # entry (how long a container keeps something), and "how long does it take buying a house"
    # reaches it too. The entry still has to be keyed to the topic's own words, the same guard
    # the rest of this reader uses, so a topic the knowledge base knows nothing about carries
    # nothing.
    long_take = LONG_IT_TAKES.match(str(line or ""))
    if long_take:
        phrase = _the_topic_phrase(topic)
        tried = long_take.group("head") + " " + phrase + " take" if phrase else ""
        found = _entry(tried) if tried else None
        if found is not None and _a_length_of_the_job(found) and not keeps_away(tried, phrase, found):
            keyed = _key_words_of(found)
            carried = set(keywords(phrase))
            # Every word of the phrase has to be one the entry is keyed to, in the form it says
            # it ("learning" for the entry's "learn"), so the entry is about the whole thing the
            # chat is on and not about one word of it.
            if len(carried) >= 2 and all(word in keyed or stem(word) in keyed or forms(word) & keyed
                                         for word in carried):
                return tried
    # A stay-length ask asks how long to give the place the chat is on, and the place's own
    # answer is reached with the place in the line. The topic's words put on the end reach the
    # trip plan instead, and its advice is then read back as the answer to the length.
    lowered = str(line or "").lower()
    if (the_city_of(topic) is not None or the_country_of(topic) is not None) \
            and STAY_ASK.search(lowered):
        stay = a_stay_with_the_place(line, topic)
        if stay is not None:
            return stay
        # The chat is on a city and the line asks how long: either the line carries a subject of
        # its own ("how many days should i rest my ankle"), or the city is not a place they are
        # going ("i live in edinburgh"). Neither is answered by the trip table, and the ordinary
        # carry would put the city on the front of the line ("rome how many days should i rest
        # my ankle") and answer the ankle with a holiday. Both are left to the readers below.
        return None
    said = words(line)
    have = set(said)
    # A month or a season is a condition on their plan, not its subject - unless the plan has no
    # place in it yet: "im thinking of a holiday in october" and then "where should I go" is a
    # question about October, and dropping the month there answered with holidays in general
    # ("two things decide it: how long you have, and whether you want sun or a city").
    elsewhere = _the_trip_of_theirs(str(topic or "")) and not _a_sky_ask(line)
    # A topic that only asked a property ("what temperature") lends no word to the line after
    # it: "how long" then meant a roast chicken's timing and reached the entry keyed on a
    # temperature, which answered it with the fever card. A temperature somebody has is a thing
    # about them, so a topic that states one keeps it.
    lends_no_property = _asks_a_property_and_nothing_else(str(topic or ""))
    known = [word for word in keywords(str(topic or "")) if word not in have
             and not (lends_no_property and word in MEASURE_WORDS)
             and not (elsewhere and (word in MONTH_NAMES or word in SEASONS))]
    if not known:
        return None
    # When the topic itself reaches an entry, only the words that entry is keyed to are carried:
    # "bathroom" in "the bathroom tap has been dripping" is where the tap is, not the subject,
    # and carrying it would read "do i need to turn the water off first?" as the cleaning entry.
    # The topic is re-read only for a follow-up that names nothing of its own ("why is that
    # happening", "why", "and what can i do"): a line that brings a subject of its own is
    # answered from the anchor the topic itself reaches, so "what should i change?" after a
    # flat loaf still gets the starter's answer and only the bare why moves.
    anchor = (_where_the_topic_lands(str(topic or "")) if names_nothing(line)
              else _entry(str(topic or "")))
    if anchor is not None:
        keyed = _key_words_of(anchor)
        extra = [word for word in known
                 if word in keyed or stem(word) in keyed or _said(word, keyed)]
        frequency = _only_said_as_a_frequency(topic)
        if extra and frequency and all(word in frequency for word in extra):
            # "my laptop fan is loud all the time" reaches the "what time is it" entry through
            # "all the time", which is how often the fan is loud and not a thing the chat is on:
            # the clock lent the line nothing but a frequency, and the follow-up after any line
            # ending that way carried no subject at all ("what helps" then got the search shrug
            # where the answer was one turn back). A word said only inside a frequency phrase is
            # not the subject, so the topic is read as one that lands nowhere.
            extra = []
        if not extra:
            # The topic lands on an entry that shares none of its own words: "my laptop fan is
            # loud all the time" reaches the clock entry through "all the time", which is a
            # frequency and not what the chat is on, and the clock is keyed to nothing else in
            # it. With nothing to lend, the entry is not the topic's subject, so the topic's own
            # words are carried, exactly as for a topic that lands nowhere. Without this the
            # follow-up after any line ending "all the time" carried nothing at all and the
            # person got the search shrug where the answer was a turn back.
            anchor = None
            extra = known
    else:
        extra = known
    if not extra:
        return None
    stem_of = line.strip().rstrip("?.!").strip()
    # The whole of the topic first, then the words of it taken together: a subject said with
    # the trouble it is in ("sourdough ... flat") reaches its entry, and the words that only
    # say how long it has been going on ("keeps coming") are left out when the whole is too much.
    cands = [extra] + [[one, two] for one in extra for two in extra if one != two] \
        + [[one] for one in extra]
    text = item = borrowed = None
    for tried, carried in _the_ways_of_saying_it(stem_of, str(line or ""), cands):
        borrowed = carried
        found = _entry(tried)
        if found is None:
            continue
        # Every word carried over has to be a word the entry is keyed to: "flat" from "flat
        # tyre" is the entry's flat, but "bike" is not, so the soup-that-tastes-flat entry is
        # not the answer to "can you fix it?" after a tyre.
        keyed = _key_words_of(found)
        if not all(word in keyed or stem(word) in keyed or _said(word, keyed)
                   for word in carried.split()):
            continue
        text, item = tried, found
        break
    if item is None:
        return None
    # Only the carried words the entry is keyed to: "start running" reaches the exercise entry
    # through "running", and "start" says nothing about it.
    keyed = _key_words_of(item)
    lean = [word for word in borrowed.split()
            if word in keyed or stem(word) in keyed or _said(word, keyed)]
    if 0 < len(lean) < len(borrowed.split()):
        tried = stem_of + " " + " ".join(lean)
        found = _entry(tried)
        if found is not None:
            text, item, borrowed = tried, found, " ".join(lean)
    # A line that asks something of its own is carried only when its own words say a word the
    # entry is keyed to: the words the carry added cannot be the only thing that reached it.
    # "how often should i practise" after "i want to learn piano" names "practise", which the
    # entry is keyed to, so it is carried and answered. "right, any tips for a long shift" after
    # a knee answer is another ask, about a shift, and nothing in it names the knee, so the
    # carry put the knee into a question nobody asked. The entry the topic itself reached is not
    # exempt: it is the old subject, and this line has its own.
    #
    # A line that asks nothing is not doing that. "nah just tired" after the dinner ideas is a
    # reaction to the answer in hand, not a question about tiredness, and it stays on the topic
    # it was said in: carried, the turn belongs to the conversation; carried no longer, the
    # fatigue card answers a complaint nobody made.
    if not _names_it(said, item) and not names_nothing(line) and item is not anchor:
        return None
    # The entry has to be about the same thing as the entry the topic itself reached: two
    # words keyed alike ("running" and "jog" for a run and for how often to run). One shared
    # word is not enough - "beef" in a beef stew is not the beef in a steak, "tap" in a dripping
    # tap is not the tap in cleaning the sink - and a wrong fact is worse than none.
    if anchor is not None and item is not anchor:
        if len(_key_words_of(item) & _key_words_of(anchor)) < 2:
            return None
    elif anchor is None and len(_key_words_of(item) & set(keywords(str(topic or "")))) < 2:
        # A topic with no entry of its own is carried only to an entry keyed to two of its
        # words: a flat sourdough reaches the flat loaf, a beef stew does not become a steak.
        # A topic that names one thing has no second word to share: "also i want tomatoes" is
        # the tomato entry, and it is the whole of what that turn was about.
        if len(set(keywords(str(topic or "")))) > 1:
            return None
    # The entry is judged against the words carried over, not against every word of the topic:
    # "my sourdough keeps coming out flat" says "keeps" about the trouble, and the entry that
    # avoids "keep" (how long a loaf lasts) is still the right one to answer from.
    if keeps_away(text, borrowed, item):
        return None
    return text


# The last situated readings, so one turn's two asks of the same line are answered once.
_elided_situated_cache = {}


def _an_elided_ask_situated(line, topic, understood=None):
    """The line read with the situation the chat is on ("any games kid"), or None.

    The line names the part it asks about and nothing else, so the entry is chosen by the part's
    own word and the situation only says which entry of that kind is meant: a birthday picnic
    with ten children is the games answer for children, not the one for a group of adults. The
    situation is put on one word at a time, because the whole of a topic's words reach a
    neighbour as often as not ("any games ten kid coming food bring" is a hotel's details), and
    the entry found has to be named by the line itself, so the added word picks the answer and
    never becomes the subject.

    The entry also has to answer a topic the chat is about. Without that, one word of the topic
    is enough to hand over a neighbour: "any tips" about a children's picnic reached the answer
    about tipping in a restaurant.
    """
    said = words(line)
    have = set(said)
    known = [word for word in keywords(str(topic or "")) if word not in have]
    if not known:
        return None
    if not isinstance(understood, dict) or not understood:
        # Without the reading there is nothing to say which situation the line is in, and a
        # guessed situation is how "any tips" becomes the answer about tipping.
        return None
    from ..knowledge.lookup import about_the_topic  # local: the knowledge base is not a memory
    stem_of = line.strip().rstrip("?.!").strip()
    # One situation word at a time, and only the first few of them: the matcher walks the whole
    # knowledge base per try, so a topic of twelve words is not worth ten seconds of the
    # conversation's time for a line this short.
    situation = (stem_of, " ".join(known[:8]), understood.get("topic"))
    memo = _elided_situated_cache.get(situation)
    if memo is not None:
        return memo or None
    found = None
    for word in known[:8]:
        text = stem_of + " " + word
        item = _entry(text)
        if item is None or not _names_it(said, item):
            continue
        if not about_the_topic(item, understood):
            continue
        if keeps_away(text, word, item):
            continue
        found = text
        break
    if len(_elided_situated_cache) > 32:
        _elided_situated_cache.clear()
    _elided_situated_cache[situation] = found or ""
    return found
# "and what about shoes", "what about a case", "how about the passport": the thing after it is a
# thing of its own, and what is asked is that thing for the subject already on the table - "shoes
# for running" - not the subject's own answer handed back. Read with the subject's words but not
# the thing's, the line reached nothing at all ("i want to start running" / "and what about
# shoes" was a search hedge, while "shoes for running" reaches the answer about kit).
ABOUT_NAMED = re.compile(
    r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
    r"(?:what|how)\s+about\s+(?P<thing>[^.?!]+?)\s*$", re.I)
# The thing said with a pronoun on the end is the same thing: "what about a bed for it" after a
# dog is a bed, and the "for it" is the subject the sentence already carries.
_ABOUT_TAIL_PRONOUN = re.compile(r"\s+(?:for|about|with)\s+(?:it|them|him|her|that|this)\s*$", re.I)
ABOUT_MOST_WORDS = 5
# "what about the bathroom", "what about my passport": a definite thing is one the chat already
# has, so it is read against the answer just given rather than as a new thing of the subject's.
DEFINITE_OPEN = re.compile(r"^(?:the|my|our|your|his|her|its|their|this|that|these|those)\b", re.I)


# How much of an answer is compared when looking for the same one again: the opening clause is
# what the person reads first, and an answer that opens on the words already on the screen is the
# same answer however it ends.
ANSWER_OPENING = 90


def _the_same_answer_again(item, memory):
    """True when the entry's answer is the answer the person already has, or opens as it does."""
    reply = " ".join(str(getattr(item, "reply", "") or "").lower().split())
    if not reply:
        return False
    opening = reply[:ANSWER_OPENING]
    for turn in [one for one in (memory.get("turns") or []) if isinstance(one, dict)][-2:]:
        said = " ".join(str(turn.get("bot") or "").lower().split())
        if said and (opening in said or said[:ANSWER_OPENING] in reply):
            return True
    return False


def the_thing_the_subject_brings(understood, memory):
    """The widened reading for a line that asks about a thing of the subject, or None.

    "and what about shoes" after "i want to start running" is a question about shoes for running,
    and the knowledge base answers "shoes for running" while the line on its own reaches nothing.
    The entry has to be keyed to the thing the line named *and* to the subject, so the subject's
    own answer is never handed back as though it answered a thing it never mentioned, and a thing
    with no answer of its own ("what about socks", "what about a case") is left as it is rather
    than answered with something that is not about it.
    """
    if not isinstance(understood, dict):
        return None
    text = " ".join(str(understood.get("clean") or understood.get("text") or "").lower().split())
    # The kind of thing it names is read from the words the person typed. The reading drops the
    # article ("what about the bathroom" comes back as "bathroom"), and "a" or "the" is exactly
    # what says whether the thing is a new one of the subject's or one the chat already has. The
    # turn's own line is tried first: this is called again on a rewritten line, and the rewrite
    # has neither the opener nor the article.
    raw = " ".join(str(understood.get("text") or understood.get("clean") or "").lower().split())
    lines = [text, raw]
    for turn in [one for one in (memory.get("turns") or []) if isinstance(one, dict)][-1:]:
        typed = " ".join(str(turn.get("user") or "").lower().split())
        if typed:
            lines.insert(0, typed)
    for said_as in lines:
        found = ABOUT_NAMED.match(said_as)
        if found:
            break
    else:
        return None
    thing = _ABOUT_TAIL_PRONOUN.sub("", found.group("thing").strip()).strip()
    if not thing or len(thing.split()) > ABOUT_MOST_WORDS:
        return None
    # A thing said with "the" or "my" is one already in play - "what about the bathroom", "what
    # about my passport" - and narrowing an answer that has just been given is the detail
    # reader's turn, not this one's. Only a thing named anew is the thing the subject brings with
    # it: "a case", "shoes", "a sleeping bag".
    typed = _ABOUT_TAIL_PRONOUN.sub("", said_as[found.end():].strip())
    if DEFINITE_OPEN.match(thing) or DEFINITE_OPEN.match(typed):
        return None
    # A bare singular is one already named with its article left off ("what about bathroom" is
    # read from "what about the bathroom"), and a bare plural is a class of things ("shoes").
    kind = typed or thing
    if not re.search(r"^(?:a|an|some)\b", kind, re.I):
        last = (kind.split() or [""])[-1]
        if not (last.endswith("s") and not last.endswith("ss") and len(last) > 3):
            return None
    thing_words = [word for word in words(thing)
                   if word not in STOPWORDS and word not in ASK_ONLY and len(word) > 2]
    if not thing_words:
        return None
    record = carried_topic(memory, text)
    if record is None:
        return None
    # A thing the answer already spoke of is a narrowing of that answer, not a thing of its own:
    # "what about the bathroom" after the windows' answer is the bathroom's window, and widening
    # it read the whole paragraph out again. The two answers back are enough - an answer that
    # named the thing is the one the person is pointing at.
    spoke_of = set()
    for turn in [one for one in (memory.get("turns") or []) if isinstance(one, dict)][-2:]:
        spoke_of.update(stem(word) for word in words(str(turn.get("bot") or "")))
    if any(stem(word) in spoke_of for word in thing_words):
        return None
    subject_words = [word for word in key_subject(str(record.get("text") or ""), memory)
                     if word not in thing_words]
    if not subject_words:
        return None
    # One subject word at a time: the entry is keyed to the thing and the subject, and "shoes for
    # running start" reaches nothing at all while "shoes for running" is the answer. The first
    # word is the one the subject is about, so the order the reading gives them is the order to
    # try them in.
    for subject in subject_words:
        for candidate in (thing + " for " + subject, thing + " " + subject):
            item = _entry(candidate)
            if item is None:
                continue
            keyed = _key_words_of(item)
            named = any(word in keyed or stem(word) in keyed or _said(word, keyed)
                        for word in thing_words)
            about_the_subject = any(word in keyed or stem(word) in keyed or _said(word, keyed)
                                    for word in subject_words)
            if not (named and about_the_subject):
                continue
            # The answer has to be another answer than the one on the screen. Counting shared
            # key words was how this was first written, and the knowledge base grew: the running
            # entry and the shoes-for-running one now share five words, so the count read a real
            # answer about shoes as the running answer said again. What separates them is the
            # answer itself, so the answer already given is what is compared.
            anchor = _entry(str(record.get("text") or ""))
            if anchor is not None and item is not anchor:
                if _the_same_answer_again(item, memory):
                    continue
            return candidate
    return None


def follows_on(understood, text):
    """True when the understanding engine read the line as carrying on, and the line itself
    points back at something ("it", "that", "there", "he")."""
    if not isinstance(understood, dict):
        return False
    text = DUMMY_IT.sub(" ", str(text))
    points_back = any(word in REFERRING_WORDS for word in words(text))
    if not points_back:
        return False
    if understood.get("followup"):
        return True
    ref = understood.get("ref")
    return isinstance(ref, dict) and bool(ref.get("followup"))


def keeps_away(line, topic, item=None):
    """True when the entry the widened line reaches keeps itself away from a word of the topic.

    The knowledge base says which lines an entry is not about ("roast a chicken" is keyed away
    from thighs), so an entry that excludes the topic's own words is a different thing of the
    same kind: 'how long do they go in for?' after chicken thighs must not get the timings for a
    whole bird. A wrong fact is worse than none.
    """
    if item is None:
        item = _entry(line)
    avoid = getattr(item, "avoid", ()) if item is not None else ()
    said = words(topic)
    return any(_kept_away_from(phrase, said) for phrase in avoid if isinstance(phrase, str))


def _kept_away_from(phrase, said):
    """True when the entry's avoidance phrase is one the topic says.

    An avoidance phrase written as a whole question is only that question when all of it is
    there: "how much should i save" says nothing about a topic whose only word is "save", and
    read on its content word alone it refused the savings goal's own timing, so "how long will
    it take?" after "im trying to save 500 pounds for a trip to spain" got a diet answer. A
    phrase of plain words ("thighs", "cast iron") still matches on the words it names.
    """
    if not any(word in STOPWORDS for word in words(phrase)):
        return _said(phrase, said)
    wanted = [stem(word) for word in words(phrase)]
    if not wanted or not all(word in (stem(one) for one in said) for word in wanted):
        return False
    return _said(phrase, said)


def _names_it(found, item):
    """True when the line itself says a word of the entry key (not only the subject put back in).

    Widening adds the topic's subject, so a line about a two-year-old pay review can land on an
    entry keyed to offers and negotiation: it shares only the words that were added. Such an
    entry has not been named by the person, so it is not the one to answer from.

    A line that is *only* the ask - "any tips", "any advice?" - names nothing else, so the
    card keyed to that phrase is the answer it points at and still counts. The skip is for a
    line that puts the ask around a subject of its own: "any tips for a long shift" is about
    the shift, and "tips" there says how the question is put.
    """
    content = set(found) - STOPWORDS
    asked_only = not (content - (ASK_PART | ASKS_FOR_ADVICE))
    for part in getattr(item, "key", ()):
        for phrase in (part if isinstance(part, tuple) else (part,)):
            if not isinstance(phrase, str):
                continue
            named = set(words(phrase)) - STOPWORDS
            if named and not named - (ASK_PART | ASKS_FOR_ADVICE) and not asked_only:
                continue  # "how long", "any tips for": the ask, not the thing
            if _said(phrase, found):
                return True
    return False


def _key_words_of(item):
    """Every word an entry's key says it is about."""
    found = set()
    for part in getattr(item, "key", ()) if item is not None else ():
        for phrase in (part if isinstance(part, tuple) else (part,)):
            if isinstance(phrase, str):
                found.update(words(phrase))
    return found


def _names_it_as_written(found, item):
    """True when the line says a word of the entry's key as it is written, not a form of it.

    "i charge it every night" after a phone battery reaches the price of clearing a drain: the
    subject put back in the line ("... battery draining") meets `drain` through the form
    "draining", and the line's own "charge" names the price group of the same entry. A drain is
    not a thing that drains, and a price asked with no job in it is not a question about a job,
    so a price word on its own only counts when the subject is the key word itself.
    """
    for part in getattr(item, "key", ()):
        for phrase in (part if isinstance(part, tuple) else (part,)):
            if not isinstance(phrase, str) or not _said(phrase, found):
                continue
            have = {str(word).lower() for word in found}
            if any(word.lower() in have for word in words(phrase)):
                return True
    return False


def _asked_only(found, item):
    """True when the only parts of the entry key the line matches are asking words.

    "how much does a plumber charge" matches the plumber's key twice over, the job and the
    price, so it is a price question that names a job. "i charge it every night" matches the
    price group alone: the line asks for nothing and names no job, and what it is about has to
    come from the job word of the conversation, said as the entry writes it.
    """
    named = False
    for part in getattr(item, "key", ()):
        for phrase in (part if isinstance(part, tuple) else (part,)):
            if not isinstance(phrase, str) or not _said(phrase, found):
                continue
            if set(words(phrase)) <= (ASK_PART | PRICE_ASK):
                continue  # "how long", "how much", "cost": the ask, not the thing
            named = True
    return not named


def _a_sky_ask(line):
    """True for a line asking about the weather, which needs the topic's month as much as its
    place: "whats the weather like there" after a trip in May is the May figures for Rome, and
    read without the month it is "no live weather here" instead of them. A month is dropped from
    what the topic lends only for the asks that are about somewhere, not for this one."""
    return any(word in WEATHER_WORDS for word in words(line))


def _the_step_they_report(line):
    """True when the line reports a step it has taken rather than asking about the topic.

    A report is a turn of its own, not a follow-up question: "i did ring them though, twice"
    after a benefits decision came back as "i did ring them though, twice theyve stopped
    because", and that line reached the ceramic-hob card on its "ring" and the topic's
    "stopped". What the report wants is the next turn of the thread, which is `already`'s to
    answer, so widening stands aside for it.
    """
    try:
        from . import already, repeat  # lazy: both read the store, which reads this module
        return bool(already.the_step_they_took(line) or repeat._tried(line))
    except Exception:  # noqa: BLE001 - a reading that fails just widens as it always did
        return False


def widen(line, subject_words, topic_text):
    """The line with the whole of the topic's subject on the end, when that reaches an entry.

    A follow-up names no subject of its own, so it is read together with everything the topic
    was about: 'and if I stuff it?' after a chicken is the stuffing entry, 'he's allergic to
    nuts' after a birthday cake is the nut-free cake. The subject is put back whole, never cut
    down to the word that happens to find something: a beef stew shares 'beef' with the steak
    entry, and a stew is not a steak. An entry keyed away from the topic's own words, or one
    the line itself does not name, is refused too.
    """
    if a_placeholder_pronoun(line):
        # "its freezing out isnt it" then "is it worth getting a dog": the topic's word went on
        # the end and made the card for walking a dog in the cold, about a question nobody put.
        return None
    if _the_step_they_report(line):
        return None
    topic_entry = _entry(topic_text)
    have = words(line)
    # A month or a season in the topic is a condition on their plan, not its subject: "we are
    # going to spain in june" and then "what should we do there" is a question about Spain, and
    # carrying "june" into it turned the line into "where should I go in june", which was
    # answered with "the Greek islands, the Algarve or the Baltic cities" - places they had
    # already chosen against.
    # Only when the topic already says where: with no place in it yet, the month is the whole of
    # what the follow-up is asking about ("a holiday in october" -> "where should I go").
    elsewhere = _the_trip_of_theirs(topic_text) and not _a_sky_ask(line)
    extra = [word for word in subject_words
             if word not in have and not (elsewhere and (word in MONTH_NAMES or word in SEASONS))]
    if not extra:
        return None
    text = line + " " + " ".join(extra)
    item = _entry(text)
    if item is None or item is topic_entry:
        return None
    if not _names_it(have, item):
        return None
    if _asked_only(have, item) and not _names_it_as_written(extra, item):
        return None
    if keeps_away(text, topic_text, item):
        return None
    return text


# A follow-up that adds nothing but a limit on the question just answered: the time they have
# ("i only have ten minutes"), the size they have ("its a 2kg one") or being in a hurry. The
# topic's own question is asked again with the limit on it, and the knowledge base answers the
# pair: "whats a quick breakfast" with "i only have ten minutes in the morning" is the breakfast
# answer, not the ten-minute dinner entry that "ten minutes" on its own reaches.
CONSTRAINT = re.compile(
    r"\b(?:\d+|one|two|three|four|five|ten|fifteen|twenty|thirty|forty|fifty|sixty|ninety"
    r"|an hour|half an hour)\b[^.!?]{0,14}?\b(?:minutes?|mins?|hours?|hrs?)\b"
    r"|\b\d+(?:\.\d+)?\s?(?:kg|g|lb|lbs|oz|pints?|litres?|l|ml)\b"
    r"|\bin a (?:hurry|rush)\b|\bshort (?:of|on) time\b|\bno time\b"
    r"|\bnot (?:much|long) time\b", re.I)
# What a line can be made of and still be nothing but the limit: "i only have", "its a", "im in a".
CONSTRAINT_FILLER = frozenset("""a an the and but so though then just only really very about
at for in on of to be been is are was were have has had got get ive i im it its me my
that this there here now today tonight morning afternoon evening lunchtime midday night
week weeknight weekday left spare weve we you he she they one some more like most
think guess say said times""".split())


def adds_only_a_constraint(line):
    """The limit the line names, when the line is made of nothing but that limit."""
    text = str(line or "")
    match = CONSTRAINT.search(text)
    if match is None:
        return None
    rest = words(text[:match.start()] + " " + text[match.end():])
    if [word for word in rest if word not in CONSTRAINT_FILLER and not word.isdigit()]:
        return None
    return match.group(0)


def _constrains_the_ask(line, topic_text):
    """The question just answered, asked again with this line's limit on the end.

    A follow-up that only says how much time or how big the thing is is a second question about
    the same entry, so the entry is asked with the limit in it and the answer is the one for that
    limit: after the roast chicken answer, "its a 2kg one" is the 1 hour 40 the answer already
    works out, and after "whats a quick breakfast", "i only have ten minutes" keeps breakfast
    instead of reaching the ten-minute dinner entry that "ten minutes" alone finds. An entry the
    question just answered was not on is refused: a limit is not a new subject.
    """
    if adds_only_a_constraint(line) is None:
        return None
    asked = str(topic_text or "").strip()
    if not asked:
        return None
    mine = _entry(asked)
    text = asked + " " + str(line).strip()
    item = _entry(text)
    if item is None or (mine is not None and item is not mine):
        return None
    return text


SENTENCE = re.compile(r"(?<=[.!?])\s+")
# A sentence said on its own does not open with the word that joined it to the one before. The
# sentence picked out of an answer is said bare ("Then set up one meet-up with a classmate" is a
# new thing about the same subject, and framing it as a repeat would hide that), and the joining
# word only made sense in front of the sentence it followed: the child-worry answer reads "...being
# told it is nothing teaches them to hide it. Then take one small step towards whatever they are
# avoiding...", and "what can i do to help him settle" was answered with that second sentence
# whole, opening on a "Then" with no then before it. The first step of an answer is already said
# without its joining word (see `_first_step`), and so is any one sentence of it.
JOINED_ON = re.compile(r"^(?:and|then|so|but|also|now|next|plus|instead|otherwise)"
                       r"(?:\s*,\s*|\s+)", re.I)
NUMBER = re.compile(r"\d")
# A time, not just a number: "40 to 45 minutes", "1 hour 40", "20 mins". A count of people or a
# tin size is a number too, and a "how long" answered with "serves 8 to 10" is not an answer.
TIME = re.compile(r"\d[^.]{0,15}?\b(?:min\w*|hour\w*|hrs?)\b", re.I)
# The same time with the whole of it: "40 to 45 minutes", "1 hour 40", "1 hour 40 minutes".
# An amount the line names for itself: "a 1.5kg one", "4 pints", "600". A question that names one
# is owed the figure for that amount, not a time that happens to be in the next sentence.
AMOUNT = re.compile(r"\b\d+(?:\.\d+)?\s?(?:kg|g|lb|oz|pints?|litres?|l|ml|inches|inch|cm|mm)\b",
                    re.I)
# A figure in a unit an answer gives an amount in: "1 to 2 mg", "500mg", "3 pouches",
# "300 calories". The shared-word pass picks by verbs, so "how much should i take" after a
# melatonin answer chose the "take blood thinners" warning; the dose is the sentence with a
# unit in it, and this is what finds it.
AMOUNT_ANSWER = re.compile(
    # A price is a figure too: "how much is it" after the TV licence card wants "About £175 a
    # year", and the sentence holds a currency sign rather than a unit of weight or volume.
    r"(?:[\u00a3$\u20ac]\s?\d+(?:[\d,.]*)?(?:\s*(?:-|to|and|\u2013)\s*[\u00a3$\u20ac]?\s?"
    r"\d+(?:[\d,.]*)?)?"
    r"|\b\d+(?:\.\d+)?(?:\s*(?:-|to|and|\u2013)\s*\d+(?:\.\d+)?)?\s*"
    r"(?:mg|mcg|\u00b5g|g|kg|ml|l|litres?|liters?|tbsp|tsp|tablespoons?|teaspoons?|cups?|"
    r"parts?|people|slices?|tins?|oz|lbs?|pounds?|tablets?|capsules?|drops?|puffs?|sprays?|"
    r"units?|iu|kcal|calories|pouches?|sachets?|scoops?)\b)", re.I)
# A rate answers any amount of the same thing: "20 minutes per 500g" is the answer to "how long
# for a 1.5kg one" when the sentence about this size is not in the answer.
RATE = re.compile(r"\bper (?:kilo|kg|500g|pound|lb|person|head|each)\b", re.I)
# A cooking rate with the weight it is per, so a size named in a follow-up can be worked out:
# "20 minutes per 500g" is 3 times that for 1.5kg. An answer written per pound or per ounce is
# worked out in the same units it was given in.
RATE_BY_WEIGHT = re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:minutes?|mins?)\s+per\s+"
                            r"(\d+(?:\.\d+)?)\s*(kg|g|lb|lbs|pound|pounds|oz|ounce|ounces)\b", re.I)
# The size an answer has already worked its rate out for ("...so a 2kg bird takes roughly 1 hour
# 40", "About 1 hour 25 for 3.5lb: ..."). Asking for that size again wants the figure, not the
# rule; asking for another size wants it worked out.
OWN_SIZE = re.compile(r"\b(?:so an?\s+|for\s+)(\d+(?:\.\d+)?)\s*"
                      r"(kg|g|lb|lbs|pound|pounds|oz|ounce|ounces)\b", re.I)
# "plus 20 minutes on top": a fixed time every size needs, before the per-weight part.
PLUS_MINUTES = re.compile(r"\bplus\s+(\d+)\s*(?:minutes?|mins?)\b", re.I)
WEIGHT_IN_GRAMS = {"g": 1.0, "kg": 1000.0, "lb": 453.59237, "lbs": 453.59237,
                   "pound": 453.59237, "pounds": 453.59237, "oz": 28.3495,
                   "ounce": 28.3495, "ounces": 28.3495}
TIME_SPAN = re.compile(r"\b\d+(?:\.\d+)?(?:\s*(?:-|to|and)\s*\d+(?:\.\d+)?)?\s*"
                       r"(?:minutes?|mins?|hours?|hrs?)(?:\s+(?:and\s+)?\d+(?:\s*(?:-|to)\s*\d+)?"
                       r"\s*(?:minutes?|mins?)?)?", re.I)
# The duration in an answer: "20 minutes", "1-2 hours", "half an hour". A "how long" follow-up
# after an answer that has already been given once needs the part of it with the time in it.
DURATION = re.compile(
    r"\b(?:\d+(?:\s*(?:-|–|to)\s*\d+)?|half an|an?)\s*"
    r"(?:minutes?|mins?|hours?|hrs?|seconds?|days?|weeks?)\b"
    # A span is also written in words - "it usually settles in two to three days" carries no time
    # at all to the pattern above, so a "how long" follow-up was never offered it and handed back
    # the sentence about when to see a GP instead. Days and weeks only: "a few seconds" is a
    # snippet of advice ("do short practice exits, back in a minute") and not a length either.
    r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|a couple of|"
    r"several|couple of)"
    r"(?:\s*(?:-|–|to)\s*(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten))?\s*"
    r"(?:days?|weeks?)\b", re.I)
# A length written as an adjective before its noun: "a 20-minute job", "a 10-minute walk".
# It is a duration the answer states, but DURATION above does not read it, so a "how long"
# follow-up found no clause to give and fell back to a sentence chosen by a shared word.
SPAN_ADJECTIVE = re.compile(
    r"\b\d+\s*[-\u2013]\s*(?:minute|min|hour|hr|day|week|month|year)s?\b", re.I)
# A line that really asks for a length. The understanding engine labels "where do i start" as
# how_long too, and the strict duration picker must not turn a savings answer's "two weeks"
# into the answer to a question about where to begin.
LENGTH_ASK = re.compile(
    r"\bhow long\b|\bhow much time\b|\bhow many (?:minutes?|mins?|hours?|hrs?|days?|weeks?)\b"
    r"|\btime\b|\bduration\b", re.I)
# A length said as a threshold - "more than a week", "longer than three days", "at least a
# fortnight" - tells the person when to worry, not how long the thing lasts. It carries the verb
# the question used ("how long does it last" meets "it lasts more than a week"), so it used to
# win the ask on that shared word and the warning was handed over instead of the span.
THRESHOLD_SPAN = re.compile(
    r"\b(?:more than|longer than|fewer than|less than|at least|at most|over|under|beyond|up to)\s+"
    r"(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|a few|several|couple of)?\s*"
    r"(?:minutes?|mins?|hours?|hrs?|days?|weeks?|months?|fortnights?|years?)\b", re.I)
# Where a sentence can be cut into the clauses that answer different asks: "Brown the mince,
# then add the tomatoes: 20 minutes gives bolognese" carries a step and a time.
CLAUSE = re.compile(r"\s*(?:,|;|:|\u2014| - )\s*"
                    # "a week or two" is one length, so an "or" between two numbers is a span
                    # and not a clause break: splitting there left "for a week" as the answer.
                    r"|\s+or\s+(?!\d|\b(?:a|an|one|two|three|four|five|six|seven|eight|nine|"
                    r"ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|hundred|half|couple|"
                    r"several|few)\b)")
# A bracketed aside is not a clause. Its commas belong to the aside, so a cut at one leaves half
# a bracket: the shoulder answer's "the pendulum swing (lean forward, let the arm hang, circle it
# slowly) a few times a day" came back to "how long will it last" as "Circle it slowly) a few
# times a day." - a fragment with a stray bracket in it. The aside's own commas are shielded from
# the split and put back after it, so a time that lives inside the brackets still counts.
ASIDE = re.compile(r"\([^()]*\)")
SHIELD = "\x00"


def _clauses_of(sentence):
    """The clauses of a sentence, with a bracketed aside kept whole."""
    shielded = ASIDE.sub(lambda found: found.group(0).replace(",", SHIELD), str(sentence or ""))
    return [piece.replace(SHIELD, ",") for piece in CLAUSE.split(shielded)]


# A time in the tail of a warning list - "see a physio if the pain is sharp, that leg swells up
# after every run, or it is still there in two weeks" - is the point at which to worry, not the
# length they asked for. The split on " or " hands it back as a clause of its own, and said on
# its own it is a fragment: "how long will that take" was answered "Or it is still there in two
# weeks."
WARNING_SPAN = re.compile(
    r"\b(?:still there|still not|still the same|not better|no better|not gone|not settled|"
    r"not cleared|gets? worse|getting worse|keeps? (?:on|coming)|comes? back|bleeds?"
    r"|is a reason to|ring (?:the )?(?:surgery|gp|doctor|nhs|111|999)"
    r"|(?:ring|call|see|contact|speak to) (?:a |the |your )?(?:gp|doctor|nurse|pharmacist|"
    r"surgery|111|999|a&e|hospital))\b",
    re.I)
# How often, which is a different question from how long: "three times a week" is not a
# duration, and a "how often should i go" answered with "3 months" answers nothing. Only a
# phrase that carries the repetition itself, so "a couple of times" and "every other day"
# come whole and "20 minutes" never looks like one.
FREQUENCY = re.compile(
    r"\b(?:once|twice)\s*(?:a|per|every)\s*(?:day|week|month|year|fortnight|weekend|morning|"
    r"evening|night)\b|"
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a couple of|a few)\s*times?"
    r"\s*(?:a|per|every)\s*(?:day|week|month|year|fortnight|weekend|morning|evening|night)\b|"
    r"\bevery\s+(?:other\s+)?(?:day|week|month|morning|evening|night|year)\b|"
    # A counted interval is how often too: "treat bare fence timber every two or three years" is
    # a cadence, and the sentence was the only one with a time in it, so "how long will it take"
    # to paint a shed was answered "Two or three years." The same shape covers "every couple of
    # days" and "every 2 weeks".
    r"\bevery\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|couple of|"
    r"few|several|a couple of|a few)(?:\s*(?:-|to|or)\s*(?:\d+|one|two|three|four|five|six|"
    r"seven|eight|nine|ten|twelve))?\s+(?:days?|weeks?|months?|years?|nights?|mornings?|"
    r"evenings?)\b|"
    r"\b(?:daily|weekly|nightly|monthly)\b",
    re.I)

# A line about something that has not happened, or might not: repeating the last answer does not
# answer it ("what if the cake sinks?" is not the cake recipe again). A question about a quantity
# or a duration is not one of those: "how long will it take?" asks for the time, so "will it
# take" must not be read the same way as "will it work?".
NOT_A_QUANTITY = r"(?!\s+(?:take|last|need|cook|roast|bake|boil|keep|stay|be done|finish|work out))"
HYPOTHETICAL = re.compile(
    r"\b(?:what if|what happens if|in case|if it (?:goes|doesn't|does not|fails?|sinks?|burns?)|"
    r"supposing|suppose|what would|should i risk|(?:would|will) it" + NOT_A_QUANTITY + r")\b", re.I)

# How many turns an answer stays the thing we are on. A follow-up three lines later is still about
# the subject the answer was about; one after a whole new subject is not.
ANSWER_KEPT = 4


def remember_answer(memory, reply, keys):
    """Keep the whole answer an entry gave, with the words it is keyed on.

    A later follow-up can need a sentence the answer given at the time no longer carried, because
    a follow-up is answered with one sentence of it ("how long will it take?" needs "It's a
    20-minute job", which the steps sentence does not have). Keeping the entry's own answer means
    the words are still there for the next turn.
    """
    if not isinstance(reply, str) or not reply.strip():
        return
    record = {
        "text": reply,
        "keys": sorted(str(key) for key in (keys or ())),
    }
    memory["entry_answer"] = record
    # The last few, not just the last one: a turn in between can be about the same kind of thing
    # ("what do I wear" after an interview) and its entry is keyed on the same word, so the newest
    # answer is not always the one a follow-up is asking about.
    kept = memory.get("entry_answers")
    if not isinstance(kept, list):
        kept = []
    kept.append(record)
    memory["entry_answers"] = kept[-ANSWER_KEPT:]


def entry_answer(memory, topic_text):
    """The whole answer the entry for this topic gave, while it is still what we are on.

    The answer has to have been really given - one of the last few replies opens the way it does -
    because the arbiter may have chosen another module's reply for that turn, and quoting an
    answer the person never saw would be inventing one. It also has to be about this topic: the
    line's words share a word with the entry's key words, so a tap answer is not quoted for a
    question about a phone.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return None
    kept = memory.get("entry_answers")
    if not isinstance(kept, list) or not kept:
        kept = [memory.get("entry_answer")]
    mine = {form for word in keywords(topic_text) for form in (word, stem(word))}
    best, best_score = None, 0
    for record in kept:
        if not isinstance(record, dict):
            continue
        text = str(record.get("text") or "").strip()
        if not text:
            continue
        opening = " ".join(text.lower().split()[:8])
        if not any(isinstance(turn, dict)
                   and " ".join(str(turn.get("bot") or "").lower().split()).startswith(opening)
                   for turn in turns[-ANSWER_KEPT:]):
            continue  # never really said, so it is not ours to quote
        keys = set(record.get("keys") or ())
        if not keys:
            continue
        forms = {form for key in keys for form in (key, stem(key))}
        score = len(mine & forms - STOPWORDS)
        if score and score >= best_score:
            best, best_score = text, score  # on a tie the newer answer wins
    return best


# How many turns of acknowledgement are read back over to find the answer on the table. One
# turn is the "ok thanks" and the line the bot gave back to it; two allows a "thanks" then an
# "ok", which people do send in a row.
ACKED_IN_BETWEEN = 2


def answer_in_hand(memory):
    """The bot turn that answered the subject the chat is on, reading back over acknowledgements.

    "thanks", "ok" and "cheers" say nothing about what is being talked about, so they do not end
    it: after "what can i do with mince and a tin of tomatoes" and "ok thanks", "how long does
    that take" is still the ragù's question, and the answer to draw on is the paragraph before
    the thanks rather than the bot's "Glad that helped.". Only a short run of acknowledgements is
    stepped over, so a chat that really moved on keeps its last turn as the answer it is on.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return None
    index = len(turns) - 1
    stepped = 0
    while index > 0 and stepped < ACKED_IN_BETWEEN and is_ack(turns[index].get("user")):
        index -= 1
        stepped += 1
    return turns[index]


def newest_answer(memory):
    """The answer we gave most recently, while it is still one we really gave.

    A follow-up that names nothing of its own ("how long should i leave it") is about the thing
    the last answer was about, so the newest answer is the one to draw on, even when an older
    entry's key words fit the topic better.
    """
    kept = memory.get("entry_answers")
    if not isinstance(kept, list) or not kept:
        kept = [memory.get("entry_answer")]
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return None
    for record in reversed(kept):
        if not isinstance(record, dict):
            continue
        text = str(record.get("text") or "").strip()
        if not text:
            continue
        opening = " ".join(text.lower().split()[:8])
        if any(isinstance(turn, dict)
               and " ".join(str(turn.get("bot") or "").lower().split()).startswith(opening)
               for turn in turns[-ANSWER_KEPT:]):
            return text
    return None


# A sentence of the last answer that is already on the screen word for word is still the right
# answer, and giving it in the same words twice in a row is what STYLE.md rules out. So it is
# said as the repeat it is, and the wording moves on with each repeat: a person asked twice does
# not say "as I said" a second time.
REPEAT = (
    "Same as before: {reply}",
    "As I said: {reply}",
    "Same again: {reply}",
)

# The words each lead-in puts in front of the answer, so a turn that already carries one is
# still the same answer when it comes round again.
REPEAT_LEADS = (("same", "as", "before"), ("as", "i", "said"), ("same", "again"))


def _carries(said, mine):
    """Whether a bot turn is this answer word for word, with or without a repeat's lead-in."""
    if not said:
        return False
    if said == mine:
        return True
    for lead in REPEAT_LEADS:
        if said == " ".join(lead) + " " + mine:
            return True
    return False


# An acknowledgement says nothing of its own: it takes the person's detail and hands the subject
# back ("Got it - you stand all day.", "Noted: your son is coming on friday."), so an answer
# either side of it is still the answer on the screen. A short *question* ("Is it worse in the
# morning?") moves the subject on, so it is not one.
ACK = re.compile(r"^(?:got it|noted|right|ok|okay|fair enough|thanks|cheers|sure|cool"
                  r"|sounds good|no problem|not a problem|any time|you're welcome"
                  r"|understood|makes sense|good to hear|lovely to hear)\b", re.I)
# An acknowledgement is also the warm one a chat replies with when it has nothing to add ("Glad
# it helped. Say the word if there's more."). It says nothing about the subject, so it does not
# take the answer off the screen. The shape has to be closed, though: "Glad that helped, and the
# parcel came." is a warm word and then something else said, which is the chat moving on, so a
# warm line that carries a clause of its own after a comma is not an acknowledgement.
WARM_ACK = re.compile(r"\b(?:glad|pleased|happy|delighted)\b", re.I)
ACK_COURTESY = re.compile(
    r"\b(?:say the word|let me know|shout if|just ask|any ?time|good luck"
    r"|hope (?:that|it|this) (?:helps|is useful|lands))\b", re.I)


# A chat also sends a person off when a subject is finished ("Alright then — good luck with it.",
# "Enjoy it!"). That says nothing about the subject either, so an answer above it is still the
# answer on the screen: "im training for a marathon in may" / "got it, thanks" / "what am i doing
# this week" read the plan back instead of handing the programme over again.
A_CLOSE = re.compile(r"\b(?:good luck|best of luck|all the best|enjoy (?:it|the rest)|have fun"
                     r"|hope (?:it|that) goes well)\b", re.I)
# The words a close is allowed to carry besides the courtesy itself. Anything else in the line is
# a fact of its own, and then the chat has moved on.
CLOSE_FILLER = frozenset("alright ok okay right well then great lovely nice and so with it that "
                         "your the rest of day time too now very much you i me a an".split())


def _only_a_close(text):
    """True when a line does nothing but send the person off ("Alright then — good luck with it")."""
    found = A_CLOSE.search(text)
    if not found:
        return False
    rest = (text[:found.start()] + " " + text[found.end():]).split()
    for word in rest:
        word = word.strip(".,!?-\u2014\u2013\"'()").lower()
        if word and word not in CLOSE_FILLER:
            return False
    return True


SHORT_TURN = 12


def only_acknowledges(said):
    """True when a bot line only acknowledges the person's own line and adds nothing.

    A reply that adds a fact of its own after a comma ("Glad that helped, and the parcel came.")
    is the chat moving on, and the answer above it is then an old answer rather than the one on
    the screen.
    """
    text = str(said or "").strip()
    if not text or len(text.split()) > SHORT_TURN:
        return False
    if ACK.match(text):
        return True
    if _only_a_close(text):
        return True
    return bool(WARM_ACK.search(text)
                and (ACK_COURTESY.search(text) or "," not in text))

# How many turns back the answer on the screen is looked for. Two answers with only an
# acknowledgement between them are still back to back; a real turn in between is not.
LOOK_BACK = 3


def _hands_the_subject_back(said, memory):
    """Whether a turn answered a remark on the turn before rather than moving the subject on.

    "it cost a fortune" after the plan was given is a remark, not a new subject, and the answer
    above it is still the answer on the screen. The greeting writes down the replies it gave to
    remarks (`bot/memory/ack.py::_a_hand_back`), so a turn that said something else is never
    read as one: the check is the reply's own words, not its shape.
    """
    kept = memory.get("hand_backs") if isinstance(memory, dict) else None
    return isinstance(kept, list) and said in kept


# A figure in a line is a fact of its own: an age, a count, a weight.
FIGURE = re.compile(r"\b\d+(?:[.,]\d+)?\b")

# A content word that points back at what the answer has already said instead of naming a thing of
# its own. "can i get it back" after the bank answer has one content word, "back", and it named the
# money's return - so the line was read as a question of its own, the frame was withheld, and the
# person got the search hedge for a follow-up whose answer they had just read. A line that says "my
# back hurts" is still its own line, because "hurt" is a thing said about it.
#
# The words that ask for a *different* part ("and more", "what else", "same again", "another one")
# are deliberately not here: standing the frame down is what lets the reader under it pick the
# sentence the person has not had yet ("The bit of that answer worth doing first: ..."), and that
# is better than the opening said again.
POINTS_AT_THE_ANSWER = frozenset("""
back instead anyway though
""".split())


def _the_opening_of(reply):
    """The first sentence of an answer, which is the part a friend says when asked it again.

    The paragraph said again behind a lead-in is the answer printed twice: "can i get it back"
    after the bank answer came back as all 512 characters with "Same as before:" in front of
    them, and the person has the whole thing on the screen already. A sentence or two off the
    top is the same answer, said the way somebody says it a second time - and the long answer is
    still there to be read, and still comes back whole when the ask is a part of it (the readers
    below this floor answer that, before the frame is reached).

    A cut never stops inside a quotation: the words an answer hands over to say have full stops
    of their own, and half of them is a broken quote rather than a shorter answer
    (`quotes.closed`).
    """
    body = str(reply or "").strip()
    parts = quoted.sentences(body, SENTENCE)
    if len(parts) < 2:
        return body
    if len(parts[0]) >= 60:
        kept = parts[:1]
    else:
        kept = parts[:2]
    return quoted.closed(" ".join(part.strip() for part in kept), parts[len(kept):], body)


def said_again(reply, memory, line=None):
    """The reply, framed as the repeat it is when it is already on the screen, or None.

    A reply that is on the screen word for word is the right answer still, and saying it in the
    same words twice reads as a machine (STYLE.md, "Never answer the same way twice in a row").
    Framing it says what it is, and the lead-in moves on with each repeat so a person asking
    twice does not get "as I said" twice. An acknowledgement between ("Got it - you stand all
    day.") does not take the answer off the screen.

    With a line, only that line says whether this is the same ask again: a line that names
    something of its own ("am i allergic to nuts" after "my mums allergic to nuts") is a
    question of its own, even when the answer to it is the paragraph just given, and framing it
    would take the turn from a module that has something new to say about it (the store's "the
    allergy is your mum's, not yours"). A line that names nothing ("what should I do about it")
    is asking for the advice again, so the answer coming round again is framed.
    """
    from . import again as _frames  # lazy: `bot/memory/again` imports this module
    if _frames.carries_a_lead_in(reply):
        return None  # already framed: a lead-in is never stacked on another
    mine = " ".join(words(reply))
    if line is not None and pairing(line):
        return None  # a pairing question is not the same ask said twice
    if line is not None:
        from . import returned  # noqa: PLC0415 - same package, imported late to keep imports flat

        if returned.says_it_happened_again(line):
            # "my back is sore again" is news, not the same ask a second time: the trouble has come
            # back, and the modules that answer a return have the next step this paragraph cannot
            # know about ("Does it come and go, or is it there all the time?"). A request to be
            # reminded still looks like a repeat ("what was the headache thing again").
            return None
    if line is not None and (
            [word for word in keywords(line)
             if word not in ASK_ONLY and word not in POINTS_AT_THE_ANSWER]
            or FIGURE.search(str(line))):
        # A figure is something of its own too: "my son is losing weight" / "he is 9" told us the
        # age, and the whole card came back behind "Same as before:" - a person who has just said
        # something new is not asking again. `keywords` drops numbers, so the count is read here.
        return None
    turns = memory.get("turns")
    if not mine or not isinstance(turns, list):
        return None
    times = 0
    seen = 0
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            break
        if seen >= LOOK_BACK:
            break
        seen += 1
        said = words(turn.get("bot") or "")
        if _carries(" ".join(said), mine) or mine in " ".join(said):
            times += 1
            continue
        if _hands_the_subject_back(" ".join(said), memory) or only_acknowledges(turn.get("bot")):
            continue  # only an acknowledgement between ("Got it - you stand all day.")
        break
    if not times:
        return None  # not on the screen: it is a new sentence to this conversation
    short = _the_opening_of(reply)
    if short and " ".join(words(short)) != mine:
        # The whole answer is on the screen word for word. Saying it again in full is what a
        # machine does; the opening of it is what a person says when asked twice.
        reply = short
    return REPEAT[min(times, len(REPEAT)) - 1].format(reply=reply)
def _said_later_than(turn, record):
    """True when `turn` was said after `record` (both are topic records)."""
    mine = turn.get("turn") if isinstance(turn, dict) else None
    theirs = record.get("turn") if isinstance(record, dict) else None
    if not isinstance(mine, int):
        return False
    if not isinstance(theirs, int):
        return True  # a record that cannot be placed is the older one
    return mine > theirs


def _the_turn_we_lean_on(understood, memory):
    """The turn the reading says this line leans on, or None.

    The topic kept on memory is the first thing said about a subject and it keeps the words the
    subject was first said in ("im planning a veg patch"), while the last thing said about it can
    name the thing itself ("also i want tomatoes"). A follow-up leans on that last turn, and the
    reading has already worked out which turn it is.
    """
    lean = understood.get("leans_on") if isinstance(understood, dict) else None
    text = str(lean.get("text") or "") if isinstance(lean, dict) else ""
    wanted = " ".join(words(text))
    if not wanted:
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return None
    for back, turn in enumerate(reversed(turns[-8:])):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if " ".join(words(said)) == wanted:
            return {"turn": len(turns) - 1 - back, "text": said, "words": words(said)}
    return None


def _the_turn_that_answered(answer, memory, keep=6):
    """The turn whose reply is `answer`, or None (the knowledge base's answers are its own words)."""
    wanted = words(answer)[:12]
    for turn in reversed((memory.get("turns") or [])[-keep:]):
        if not isinstance(turn, dict):
            continue
        if words(str(turn.get("bot") or ""))[:12] == wanted:
            return turn
    return None


# The doing word of a question is the asking, not the thing. "how do i stop it squeaking" after
# a boiler answer shares only the word "stop" with that answer's "stop topping it up", and the
# shared verb made the boiler's sentence the answer this line "belonged to", so the door just
# asked about was answered with "If it keeps dropping, there's a leak somewhere". The subject of
# a line is in its nouns; the verb is how it is asked about.
_ASKING_VERBS = frozenset(_VERB_WORDS) | frozenset(_ACTION)


def _answer_about(line, memory, keep=6):
    """The most recent earlier answer this line's own words belong to, or None.

    A follow-up that names a thing ("how long for a hard boiled one") can come after a turn on
    something else ("my tap is dripping"), and the last answer is then the wrong answer to draw
    on. Measured on the words the line brings, not on what the topic says, so a line that names
    nothing of its own is still read from the answer just given.
    """
    # The words of the ask itself ("how long should that take") belong to every answer that
    # gives a figure, so they cannot be what ties this line to an older one: "and how long
    # should that take?" after the leg of lamb matched the chicken answer on the word "takes"
    # and handed back the chicken times for the lamb.
    asking = bool(_FRAME_ASK.search(line.lower()))
    wanted = frozenset(stem(word) for word in keywords(line)
                       if word not in ASK_ONLY
                       and not (asking and stem(word) in _ASKING_VERBS))
    if not wanted:
        return None
    turns = [turn for turn in (memory.get("turns") or [])[-keep:] if isinstance(turn, dict)]
    if len(turns) < 2:
        return None
    last = str(turns[-1].get("bot") or "")
    last_score = len(wanted & frozenset(stem(w) for w in keywords(last)))
    best, best_score = None, last_score
    for turn in turns[:-1]:
        if turn.get("module") != "answers":
            continue
        said = str(turn.get("bot") or "")
        score = len(wanted & frozenset(stem(w) for w in keywords(said)))
        if score > best_score:
            best, best_score = said, score
    return best


def answer_about(line, memory):
    """The earlier answer this line's own words belong to, when it is not the one just given.

    A public read of `_answer_about` for the knowledge base: the part-reader cuts a part out of
    the answer just given, and a line naming words of an answer from two turns back ("and how long
    in the oven" after the cake, with a turn about the frosting in between) is asking about that
    one, not about this one.
    """
    return _answer_about(line, memory)


def _the_trip_of_theirs(text):
    """The places a line of theirs says they are going to, or an empty set.

    The store already reads a plan and the place in it ("im off to cornwall next week" is a
    plan, Cornwall is its place), so this asks it rather than guessing at the words again. A
    line with no plan of its own is not a trip: "my sister is going to rome" says where she is
    going, and the answer about her trip is still the answer to the chat's own.
    """
    from . import facts  # lazy: the store's own reader, not a second guess at the words
    found = facts.extract(text) or {}
    if not found.get("plan"):
        return set()
    return {str(place).strip().lower() for place in found.get("places") or [] if str(place).strip()}


def the_place_they_are_on(memory):
    """The place of the newest trip they have started on, or an empty set.

    The current line comes first when the store has already noted it, and the turn before it is
    read when the current line names no trip: "what should i do there" carries the trip it points
    at, and that is the trip the chat is on.
    """
    turns = [turn for turn in (memory.get("turns") or [])
             if isinstance(turn, dict) and turn.get("user")]
    # A line that put something right does not name the trip it leaves behind: "actually its
    # cornwall we go to" carries the place and no trip of its own, and the rome line before it is
    # the one the words fit best. The plan the store now holds is the trip, so it is read first.
    corrected = isinstance(memory, dict) and bool(memory.get("correction"))
    if not corrected:
        for turn in reversed(turns[-2:]):
            here = _the_trip_of_theirs(str(turn.get("user") or ""))
            if here:
                return here
    # The trip the store is holding, when the turns name none or have just been corrected: it is
    # the store's plan that says which trip the chat is on, and the answer about the place they
    # left has to be told from it.
    plan = (memory.get("user") or {}).get("plan") if isinstance(memory, dict) else None
    if isinstance(plan, str) and plan.strip():
        here = _the_trip_of_theirs("we are going to " + plan.strip())
        if here:
            return here
    return set()


def about_a_place_they_left_behind(answer, memory):
    """True when the answer on the table is about a place they are no longer going to.

    "im going to rome in may", the weather in Rome, then "im off to cornwall next week": the
    next line, "what should i do there", was handed the Rome weather sentence - "Take a layer
    either way: evenings are cooler than the afternoon" - which is a fact about a city they are
    not going to, said with no sign that the trip had changed. A wrong fact is worse than none,
    so an answer that names a place they have moved off is not lent to the new trip.
    """
    here = the_place_they_are_on(memory)
    if not here:
        return False
    told = {str(place).strip().lower()
            for place in ((memory.get("user") or {}).get("places") or []) if str(place).strip()}
    left = told - here
    if not left:
        return False
    return bool(left & set(words(str(answer or ""))))


# A line that asks for the rate something is done at, and nothing else: "and how often", "how
# many times a week". Its answer is a phrase of the answer on the table, not a sentence of it.
ASKS_A_FREQUENCY = re.compile(r"\bhow (?:often|regularly|frequently)\b|\bhow many times\b", re.I)


def same_as_before(understood, memory):
    """The part of the last answer that this follow-up asks about, or None.

    The knowledge base has one entry per thing, so a line that carries on about the thing we are
    already on ("how do I fix it?" after a dripping tap, "what about the rice?" after a curry
    answer) is answered from that same entry. What the person needs is the sentence of it that
    answers this line, and the shortest honest way to give it is that sentence rather than a
    search hedge. Only a follow-up gets this, only while the knowledge base is what we are on, and
    never the whole of the last answer again (the arbiter drops an exact repeat, and so does the
    bot: a reply twice in a row reads as broken). The answer to draw on is the entry's own answer
    (see entry_answer), so a follow-up still reaches a sentence that an earlier trim left out, and
    a turn in between that got no answer does not end the subject.
    """
    if not isinstance(understood, dict):
        return None
    line = understood.get("clean") or understood.get("text") or ""
    if pairing(line):
        return None  # a pairing question names a relation, not a part of the last answer
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    last = turns[-1]
    # A "thanks" between the answer and the follow-up does not change the subject, so the answer
    # this line carries on is the one before it. The reply on the screen is still `last`'s: what
    # has already been read twice in a row is judged on that, not on the older answer.
    drawn = answer_in_hand(memory) or last
    if understood.get("kind") != "question":
        return None  # a line that adds a detail wants an answer about that, not the last one again
    # "What should I do about it?" asks for the next step, not for a sentence of the last answer
    # picked by its words: that picking gives the cause sentence they have just read. The step is
    # in the answer all the same, so this line is offered the doing part of it (see `_doing_part`)
    # and nothing at all when the answer was only a cause.
    proceed = any(phrase in line.lower() for phrase in PROCEED)
    if not (leans_on_topic(understood, memory) or asks_only(understood)):
        return None  # likewise for a line that points at nothing and asks for nothing
    record = carried_topic(memory, line)
    if left_for_a_blank(memory, line):
        # A turn in between named a thing of its own and got no answer for it ("what about a leg
        # of lamb?" after the roast chicken): the chat is on that thing now, so the next "and how
        # long should that take?" is a question about the lamb, and the chicken times are a wrong
        # answer rather than a helpful one. A line that only says what to do about the thing we
        # are on ("can I fix it myself?") leaves the topic where it was.
        return None
    asked = str((record or {}).get("text") or "")
    # The answer this line's own words belong to, when an earlier turn was about the thing it
    # names: the tap answered between the eggs and "how long for a hard boiled one" are not the
    # same subject, and the egg answer is the one the line asks about.
    earlier = _answer_about(line, memory)
    # Only a line that brings nothing of its own ("how often should i go", "what can i take for
    # it") leans on a thin word match, and then the older answer has to belong to the thing on
    # the table. "how often should i go" after "i want to start running" shares "often" with the
    # shift answer two turns back ("often two to four weeks"), and the thing on the table is the
    # running - an answer about the rota is another subject's. "what can i take for it" after
    # "my back hurts" / "only when i sit down" is the back's, and the back's answer is the one
    # to draw on. A line that names a thing of its own is free to jump to another thing's answer
    # ("how long for a hard boiled one" after the tap).
    if earlier is not None and not [word for word in keywords(line) if word not in ASK_ONLY]:
        on_the_table = _entry(asked)
        answered_by = _the_turn_that_answered(earlier, memory)
        its_subject = _entry(str((answered_by or {}).get("user") or ""))
        if on_the_table is not None and its_subject is not on_the_table:
            earlier = None
    # A line that names a thing of its own is about that thing, even when it points back with
    # "it": "how long does it take to cook rice" after a boiled egg carries rice, which has its
    # own timings, and the egg's six minutes would be a wrong fact. A wrong fact is worse than
    # none, so the answer on the table is left alone and the line is read on its own.
    # The wrong fact this guards against is a figure, a heat or an amount borrowed from another
    # thing's answer; a question that asks for no measure ("should I see a doctor if it's not
    # better by Monday?") is still about the cold it does not name, and reading it alone loses
    # the warning the answer carries.
    measured = set(understood.get("asks") or ()) & MEASURED
    fresh = [word for word in keywords(line) if word not in ASK_ONLY]
    if earlier is None and measured and fresh \
            and not set(key_subject(line)) & set(key_subject(asked)):
        mine, theirs = _entry(line), _entry(asked)
        if mine is not None and theirs is not None and mine is not theirs:
            return None
    # A line that carries nothing but the ask ("and how long?", "what temperature?") cannot be
    # the same question over again: "how long do i boil an egg" then "and how long?" shares its
    # two asking words with the question before it, and the guard threw the follow-up away - the
    # one line that most needs the answer just given. An exact repeat ("how long do i boil an
    # egg" twice) carries its own words, so it keeps the guard.
    if (not asks_only(understood) and _repeats_the_question(line, asked)) \
            or HYPOTHETICAL.search(str(line)):
        return None
    # The answer we are still on: the entry's own answer while the conversation is on that
    # subject, even when a turn in between got no answer. A hedge ("that's beyond what I know")
    # does not end what we were talking about, so the next line can still be answered from it.
    whole = entry_answer(memory, asked)
    if not any(word in keywords(asked) for word in keywords(line)):
        # The line names nothing of the subject it carries on ("how long should i leave it"),
        # so "it" is whatever the last answer was about, not the older entry whose key words
        # the topic happens to fit.
        whole = newest_answer(memory) or whole
    # A card is the answer only while the chat is still on the thing it answers: a statement in
    # between that names a thing of its own and was answered as its own subject moves the chat to
    # that thing, even though it was a statement and not a question. "we want to try for a baby"
    # ... "my baby has a fever" ... "how long does it last" was handed "Have sex every two or
    # three days rather than saving up.", a clause of the trying-for-a-baby card, as the answer
    # to a question about a child's fever. A wrong fact is the worst reply there is, so a line
    # that asks for a part of what the chat holds stops drawing on a card it has moved off.
    if whole and asks_only(understood):
        moved = _the_thing_the_chat_moved_to(whole, line, memory)
        if moved is not None:
            # The thing the chat moved to answers this line itself, so its own sentence is the
            # answer: the card the chat has left is another subject's figures.
            from .narrow import narrow as _the_part
            answer = str(getattr(moved, "reply", "") or "")
            part = _the_part(answer, line)
            if part:
                # The whole sentence it stands in says more than the figure alone ("Most fevers
                # are a virus and settle in three or four days" rather than "Three or four
                # days."), and the person has not read this answer, so there is nothing to trim.
                bare = part.strip(" .").lower()
                for sentence in (one.strip() for one in SENTENCE.split(answer)):
                    if sentence and bare and bare in sentence.lower():
                        return sentence
                return part
            return None
    if drawn.get("module") != "answers" and whole is None:
        return None  # nothing was answered from the knowledge base just now: nothing to draw on
    answer = whole or str(drawn.get("bot") or "")
    # A trip they have changed moves the answer with it: the weather, the cost and what to see
    # are facts about a place, so the answer about the old place is not the answer about the new
    # one ("im going to rome in may" ... "im off to cornwall next week" ... "what should i do
    # there" was handed the Rome weather sentence).
    if about_a_place_they_left_behind(answer, memory):
        return None
    # "how long for 700g" names no thing of its own and has no "it" or "one" to point back with,
    # so it does not look like a follow-up, but it is the same question about another size of
    # what we are on. It counts only while the answer on the table works that size out from its
    # own rate: a subject with no rate in weight gives no time here, and a line that does not
    # follow on is left alone rather than answered with somebody else's figure.
    sized = _worked_out_for_this_line(understood, line, answer)
    if not (leans_on_topic(understood, memory) or asks_only(understood) or sized):
        return None  # likewise for a line that points at nothing and asks for nothing
    # A size the answer's own rate can work out is answered before the sentence scoring, because
    # the ask's weight ("500g") is also in the rate sentence ("20 minutes per 500g"), and that
    # shared word used to hand back the answer for the size the entry had already worked out:
    # "how long for 500g" after the 3kg answer said 2 hours 20 again instead of 40 minutes.
    worked = sized_reply(answer, line, memory)
    if worked:
        return worked
    # The last answer is not always the answer this line is about: a turn about the tap in
    # between must not lend the tap's sentence to a question about boiled eggs. When the line's
    # own words fit an earlier answer better than they fit the last one, that is the answer it
    # is asking again.
    if earlier and earlier != answer:
        answer = whole = earlier
        # The line asks for a part of that answer ("how long for a hard boiled one"), and the
        # answer is often one sentence with the parts inside it: hand back the clause the line
        # asks for, not the whole of a paragraph that is no longer on the last turn.
        from .narrow import narrow
        part = narrow(answer, line)
        if part:
            return part
    # A full stop inside a name is not the end of a sentence: "and *Inside No. 9* for half-hour
    # creepers" was cut at "No." and the person was handed the leftover "9* for half-hour
    # creepers." as the answer to "how long did i want it".
    sentences = quoted.sentences(answer, SENTENCE)
    if proceed:
        if _opening_instruction(sentences[0], True):
            # The answer opens with the step itself, so the next-step reply can name it ("top the
            # pressure up first, then work down the list"): nothing to add here.
            return None
        doing = _doing_part(sentences, memory)
        # The answer that already opens with the steps ("Turn the water off at the isolating valve
        # ... take the old part to a hardware shop") has its doing in that first sentence, and
        # giving it again reads as broken. Nothing is owed there: the next-step reply says to work
        # down the list, which is the honest answer to a line that adds nothing.
        if doing and not _says_it_again(doing, sentences[0]):
            return doing
        return None
    if len(sentences) < 2 and whole is None:
        return None  # one sentence, and only a sentence of it was ever said: nothing to pick
    # A follow-up that asks for a figure ("how many weeks should i train", after a plan that
    # says sixteen) is answered by that figure, not by the answer's opening sentence again.
    from .narrow import part_in_the_unit
    part = part_in_the_unit(answer, line)
    if part and " ".join(words(part)) != " ".join(words(str(last.get("bot") or ""))):
        return said_again(part, memory, line=line) or part
    # "and how often" asks for the frequency in the answer, which is a phrase of it - "three
    # times a week with a rest day between" - and a phrase is not a sentence the word scoring can
    # find, so the line went to the search hedge with the answer it wanted on the screen. The
    # answer's own reader knows how to lift that clause (see narrow._how_often).
    if ASKS_A_FREQUENCY.search(line.lower()):
        from .narrow import narrow
        part = narrow(answer, line)
        if part and words(part) != words(answer):
            return part
    chosen = _pick_sentence(line, understood, answer, memory)
    if chosen:
        # Only the answer's opening sentence is the advice coming round again: a later sentence
        # ("Then set up one meet-up with a classmate") is a new thing to say about the same
        # subject, and framing it as a repeat hides that.
        opening = quoted.sentences(str(answer or ""), SENTENCE)
        if opening and words(opening[0]) == words(chosen):
            return said_again(chosen, memory, line=line) or chosen
        return chosen
    # A turn in between can change the subject and leave this line carrying on the one before it
    # ("what do I wear" between an interview and "what do I say about why I left my last job").
    # Draw on the answer of the nearest earlier subject this line still shares a word with.
    return _earlier_subject_sentence(line, understood, memory, record)


# "what should I do about it?", "what can I do?": the person is not asking about a part of the
# answer, they are asking for the doing in it. An answer that already tells them what to do has
# that doing in one place - the instruction the sentence opens with, or the instruction after the
# colon of the sentence that explains the cause ("it is usually the washer: turn the water off").
ADVICE_ASK = re.compile(
    r"\b(?:what|anything|something|is there anything) (?:can|could|should|would|do|shall) "
    r"(?:i|we|you) (?:do|try|use)\b|\bwhat(?:'s| is) the (?:best )?(?:thing|way) to do\b|"
    r"\bwhat do i do\b|"
    # "how do I fix it", "how do I stop it hurting": the same ask written with the verb in it.
    # The answer's first sentence is usually the cause ("Most back pain is muscular and settles
    # in two to six weeks ..."), so handing that back says what they have just read and leaves
    # out the step they asked for.
    r"\bhow (?:do|can|should|could|would|might) (?:i|we) "
    r"(?:fix|sort|stop|help|ease|improve|avoid|prevent|deal with|get rid of)\b|"
    # "what helps", "what would help with that": the same ask with no "do" in it at all. The
    # answer's sentence carries both the cause and the doing ("staying active is what helps
    # most: keep walking"), so handing the sentence back whole repeats what they have just
    # read; the doing after the colon is the answer.
    r"\bwhat (?:would |could |might |will |does |do )?(?:help|helps|helped|works|worked)\b|"
    r"\bwhat (?:should|can|could|would) (?:i|we) (?:put|set|have) in place\b", re.I)
# "what can I do with leftover rice" names a thing of its own and is a question about that thing,
# not about the answer just given. "about" and "to" point back at the answer ("what can I do
# about it", "what can I do to stop it").
ADVICE_NAMES_A_THING = re.compile(
    r"\b(?:do|try|use)\s+(?:with|for|in|on)\s+"
    r"(?!(?:it|that|this|them|these|those)\b)", re.I)
# "what can i have with it" asks what to pair with the thing, not for the last answer again.
# The pairing verb and the pronoun name a relation, so the line is not a bare ask even though
# every word in it is otherwise an ask word. "what can i do about it" is not one of these: after
# the posture answer, repeating the steps is the right reply.
PAIRING = re.compile(r"\b(?:have|eat|drink|serve|pair|put|go(?:es)?)\s+(?:with|alongside)\s+"
                     r"(?:it|that|this|these|those|them)\b", re.I)
# A noun of its own before the verb is what the line is about: "what sauce goes with it" after a
# pasta answer is a sauce question, and the pasta water answer was right. "jam" and "dressing"
# are the same shape, and "what can i have with it" has no such noun.
PAIRING_OWN = re.compile(r"\b(?:sauce|gravy|dressing|dip|jam|relish|chutney|salsa|mayo|"
                         r"mayonnaise|mustard|ketchup|wine|beer)\b", re.I)
def pairing(text):
    """True when the line leans on the pairing verb alone, with no noun of its own."""
    return bool(PAIRING.search(text or "")) and not PAIRING_OWN.search(text or "")
IMPERATIVE = frozenset("""
add apply avoid ask bake bleed book buy call change check chill choose clean clear close cover cut
deal don't do drink dry ease eat fill fit freeze get give go have heat hold ice keep kill leave let
lie look lower make mix offer open peel phone pick plan prune put raise remove replace rest rid ring
rinse run say see set sit soak sort speak start stay stop swap take talk tell text think throw
tighten top try turn use wait walk wash watch wear weed wipe write
""".split())
# A sentence that only sends them to someone else is the doing part of last resort: a person who
# asks what to do wants the step they can take now, not the pointer at the end of the answer.
SENDS_YOU_ON = frozenset("""see call phone ring book ask get""".split())


# A doing part can open with when or how often it is done ("Three times a week do sit-squats",
# "each night, write it down"). The words that say when are not the doing, so the instruction is
# the first word after them.
WHEN = frozenset("""once twice three four five six seven two a an every each daily nightly morning
afternoon evening night day week month year hour minute second time times""".split())


def _doing_word(text):
    words = str(text or "").split()
    for index, word in enumerate(words):
        core = word.strip(",;:-\u2014\u2013").lower()
        if core in WHEN and index < 5:
            continue
        return core
    return ""


def _opening_instruction(sentence, allow_pointer):
    """True when the sentence opens with an instruction ("Rinse it", "Three times a week, do")."""
    first = _doing_word(sentence)
    if first not in IMPERATIVE:
        return False
    return allow_pointer or first not in SENDS_YOU_ON


# A red flag is never the doing part on its own. "Get it looked at if it gives way" said to somebody
# who has just been told to ice it reads as alarm, not as the next step they asked for; the answer
# for a line that already has ordinary steps in it is to carry on with those.
RED_FLAG = re.compile(
    r"^(?:get (?:it|that|one|them|him|her) (?:looked at|checked|seen)"
    r"|have (?:it|that|one) (?:looked at|checked)"
    r"|ring (?:111|999|911|nhs 24)|call (?:111|999|911)"
    r"|go (?:to|into) (?:a&e|a and e|the hospital|hospital|the emergency department)"
    r"|see (?:a|your|the) (?:gp|doctor|nurse|pharmacist|midwife)"
    r"|speak to (?:a|your|the) (?:gp|doctor)"
    r"|if (?:it|that|they) (?:is |are )?(?:still|gets? worse|does not settle|doesnt settle"
    r"|has not settled|had not settled|keeps? (?:on|coming)))", re.I)


# The bot's own sign-off is not a step. A card that ends by asking the person for the one word
# it needs ("Say which bit is tightest and I'll go at that one", "Tell me who it is for and I
# will write yours") opens on an instruction the way a step does, so a line that asks what to do
# next was handed the bot's offer of help back: "im a bit skint this month" / "like what do i
# do about it" got "Say which bit is tightest and I'll go at that one." and nothing else. What
# the sentence says is what the bot will do once it has their answer, which is nothing they can
# act on, so it is passed over and the step behind it is looked for.
ASKS_THEM_BACK = re.compile(
    r"\b(?:tell me|let me know|say (?:which|what|how|if|when|where|who)|send me|give me|pick one)\b"
    r"|\b(?:and|then)\s+i(?:'ll| will)\b"
    r"|\?\s*$", re.I)


def _doing_part(sentences, memory):
    """The sentence of the last answer that says what to do, as it was written, or None.

    A doing part opens with an instruction, either as the sentence is ("Rinse it until the water
    runs clear") or after the colon of the sentence that explains the cause ("A sore knee is
    usually a strain: ease off running"). A sentence that only sends them to someone else ("See a
    physio if it swells") is the doing part of last resort, so it is tried after the others. The
    bot asking them something is not a doing part at all (see `ASKS_THEM_BACK`), however
    instructively it is worded.
    """
    for allow_pointer in (False, True):
        for sentence in sentences:
            if RED_FLAG.match(sentence):
                continue
            head, sep, tail = sentence.partition(":")
            if sep and tail.strip() and _opening_instruction(tail, allow_pointer):
                said = tail.strip()
                said = said[0].upper() + said[1:]
                if not said.endswith((".", "!", "?")):
                    said += "."
                if RED_FLAG.match(said) or ASKS_THEM_BACK.search(said):
                    continue
                if not already_said(memory, said):
                    return said
            if _opening_instruction(sentence, allow_pointer) \
                    and not ASKS_THEM_BACK.search(sentence):
                if not already_said(memory, sentence):
                    return sentence
    return None


def _says_it_again(part, sentence):
    """True when this part of the answer is already in that sentence, nearly word for word."""
    words = re.findall(r"[a-z']+", str(part or "").lower())
    said = re.findall(r"[a-z']+", str(sentence or "").lower())
    if not words or not said:
        return False
    head = words[:6]
    for index in range(len(said) - len(head) + 1):
        if said[index:index + len(head)] == head:
            return True
    return sum(1 for word in words if word in said) >= 0.8 * len(words)


# A line that asks for a ceiling ("how much is too much", "how much can i take") wants the
# sentence that carries the ceiling, not the single dose at the front of it. A sentence with one of
# these words is the limit answer; if the whole card has one, repeating it is better than cutting
# the figure to its first clause and leaving the "4g a day" behind.
A_CEILING_ASK = re.compile(
    r"\b(?:too much|too many|max(?:imum)?|limit|how much can i (?:take|have|drink|eat)"
    r"|how many can i (?:take|have|drink|eat)|how much is safe|how many is safe)\b", re.I)
A_CEILING_WORD = re.compile(
    r"\b(?:at most|no more than|max(?:imum)?|limit|up to|not (?:more|over)|safe|ceiling)\b",
    re.I)


_A_RATE = re.compile(
    r"\b(?:a|an|per|each|every)\s+(day|week|month|year)\b"
    r"|\b(daily|weekly|monthly|yearly|annually)\b", re.I)


def _the_rates_in(text):
    """The periods a line or sentence puts a figure over: {"day"}, {"week", "year"}."""
    out = set()
    for found in _A_RATE.finditer(str(text or "")):
        for word in found.groups():
            if word:
                out.add(word.lower().rstrip("s"))
    for word, one in (("daily", "day"), ("weekly", "week"), ("monthly", "month"),
                      ("yearly", "year"), ("annually", "year")):
        if re.search(r"\b" + word + r"\b", str(text or ""), re.I):
            out.add(one)
    return out


def _a_rate_that_fits(line, sentence):
    """False when the line asks for a daily amount and the sentence gives a single item's.

    "how much sugar is in a can of cola" then "how much sugar should i have a day" was answered
    with the can's 35g: the figure is real, but it is not the daily amount asked for. A sentence
    with no period at all can still answer a period ask when the line is only "how much"; this
    check is for a line that names its own period.
    """
    asked = _the_rates_in(line)
    if not asked:
        return True
    given = _the_rates_in(sentence)
    return bool(asked & given) or not given


def _a_comma_that_ends_a_clause(sentence, start):
    """The first comma after `start` that is not inside a figure, or -1.

    The clause cut out of a sentence ends at a comma, but "£20,000 on a £200,000 home" has a
    thousands comma in the middle of each figure. A comma with a digit on both sides is part of
    the number, not the end of the clause.
    """
    at = sentence.find(",", start)
    while at >= 0:
        before = sentence[at - 1] if at else ""
        after = sentence[at + 1] if at + 1 < len(sentence) else ""
        if not (before.isdigit() and after.isdigit()):
            return at
        at = sentence.find(",", at + 1)
    return -1


def _pick_amount(sentences, memory, line=""):
    """The sentence of an answer that gives a figure in a unit, or the clause with it.

    "how much should i take" after a melatonin answer wants "1 to 2 mg", and the answer's
    pharmacist warning shares the verb "take" with the line while carrying no amount. The first
    sentence with a unit is the amount; when it is already on the screen word for word, the
    clause around the figure is still news. A line that asks for the ceiling ("how much is too
    much") keeps the whole sentence, because cutting at the first comma would drop the "4g a day".
    """
    screen = " ".join(words(str((memory.get("turns") or [{}])[-1].get("bot") or ""))) \
        if isinstance(memory, dict) else ""
    wants_limit = bool(A_CEILING_ASK.search(str(line or "")))
    if wants_limit:
        for sentence in sentences:
            if AMOUNT_ANSWER.search(sentence) and A_CEILING_WORD.search(sentence):
                return sentence
        for sentence in sentences:
            if AMOUNT_ANSWER.search(sentence):
                return sentence
    named = [word for word in keywords(line) if len(word) > 2 and word not in ASK_ONLY]
    for sentence in sentences:
        # A sentence of the paragraph just given is already on the screen even though the whole
        # reply is longer, so it counts as said and the clause with the figure is used instead.
        if (AMOUNT_ANSWER.search(sentence) and " ".join(words(sentence)) not in screen
                and _a_rate_that_fits(line, sentence)):
            if named and not any(word in keywords(sentence) for word in named):
                # The line names something of its own that the sentence never mentions: it is
                # asking about a different thing, not for this figure. "how much should i keep
                # for emergencies" is not the £1,000 first rung of a plan already on the screen.
                continue
            if not _the_rates_in(line) and _the_rates_in(sentence) and re.search(
                    r"\bone\b", str(line or ""), re.I):
                # "how much does one cost" asks the price of the one thing; a yearly running
                # cost is a different figure.
                continue
            return sentence
    for sentence in sentences:
        found = AMOUNT_ANSWER.search(sentence)
        if not found or not _a_rate_that_fits(line, sentence):
            continue
        if named and not any(word in keywords(sentence) for word in named):
            continue
        if not _the_rates_in(line) and _the_rates_in(sentence) and re.search(
                r"\bone\b", str(line or ""), re.I):
            continue
        before = max(sentence.rfind(":", 0, found.start()),
                     sentence.rfind(";", 0, found.start()))
        after = _a_comma_that_ends_a_clause(sentence, found.end())
        start = before + 1 if before >= 0 else 0
        end = after if after >= 0 else len(sentence)
        part = sentence[start:end].strip(" .,;:")
        if part and len(part.split()) >= 2:
            return part[:1].upper() + part[1:] + "."
        return sentence
    return None


def _pick_sentence(line, understood, answer, memory, strict=False):
    """The sentence of this answer that answers this line, said on its own, or None."""
    return said_on_its_own(_the_sentence_it_answers(line, understood, answer, memory, strict))


def said_on_its_own(sentence):
    """`sentence` without the word that joined it to the sentence before, or None.

    A sentence handed to the person alone is read alone, so "Then take one small step" and "So
    keep the tin in the cupboard" open on a "then" and a "so" that have nothing in front of them.
    """
    if not isinstance(sentence, str):
        return sentence
    said = sentence.strip()
    if not said:
        return None
    joined = JOINED_ON.match(said)
    if joined:
        said = said[joined.end():]
        if said:
            said = said[:1].upper() + said[1:]
    return said or None


def _the_sentence_it_answers(line, understood, answer, memory, strict=False):
    """The sentence of this answer that answers this line, or None."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    last = turns[-1] if isinstance(turns, list) and turns and isinstance(turns[-1], dict) else {}
    sentences = quoted.sentences(answer, SENTENCE)
    if not sentences:
        return None
    wanted = [stem(word) for word in keywords(line)]
    asks = set(understood.get("asks") or {})
    if "how_long" in asks:
        # "how long does it need?" wants the time, not the whole answer again: give the clause
        # with the time in it, which is the one part of it this line is asking about.
        part = _pick_duration(sentences, wanted, memory, line)
        if part:
            return part
    if re.search(r"\bhow much\b", line, re.I):
        # "how much should i take" wants the dose, and the sentence that shares its verb
        # ("Ask a pharmacist first if you take ...") is not it. Read the sentence with a figure
        # in a unit, which is the answer; if that sentence is already on the screen, give the
        # clause with the figure in it rather than the whole sentence again. "How many times a
        # week" is also an amount in the reading, but its unit is a count of times, not a figure
        # in grams or milligrams, so it is left to the readers below.
        part = _pick_amount(sentences, memory, line)
        if part:
            return part
    # An ask for the doing wants the doing, whether or not its own reading carries "steps":
    # "what helps" after a back-pain answer shares the word "helps" with the sentence, so the
    # shared-word pass below hands back the whole of what they have just read, cause and all.
    if ADVICE_ASK.search(line) and ADVICE_NAMES_A_THING.search(line) is None \
            and not _names_something_new(line, answer):
        doing = _doing_part(sentences, memory)
        if doing:
            return doing
    best, best_score = 0, 0
    for index, sentence in enumerate(sentences):
        said = [stem(word) for word in keywords(sentence)]
        score = sum(1 for word in wanted if word in said)
        if score > best_score:
            best, best_score = index, score
    if best_score:
        sentence = sentences[best]
        if not already_said(memory, sentence):
            return sentence
        # That sentence has been given already: fall through to what the ask itself wants rather
        # than let a shared word ("take the handle off" for "how long will it take?") end it.
    if strict:
        return None  # an older answer gets no say unless its words answer this line
    # No shared word: the ask itself has to say what it wants. A "how do I ..." or "what should I
    # ..." is answered by the steps, and a "how long" by the sentence with the time in it.
    if asks & {"steps", "how"}:
        first = sentences[0]
        if _names_something_new(line, answer):
            # The ask names a thing none of the last answer mentions ("how do i cancel her
            # insurance" after the pets entry condoled), so the sentence the bot opened with
            # is not an answer to it: pass instead of saying it again.
            return None
        if ADVICE_ASK.search(line) and not ADVICE_NAMES_A_THING.search(line):
            # "what should I do?" wants the doing, and the answer's first sentence is often the
            # cause ("Most back pain is muscular and settles in two to six weeks, ..."), so
            # giving it back whole says the thing they have just read and leaves out the step.
            doing = _doing_part(sentences, memory)
            if doing:
                return doing
        return None if already_said(memory, first) else first
    if "how_long" in asks:
        # A later sentence that carries a time is news, so it comes whole. The first sentence is
        # the one they have just read, so only the time in it is worth saying again, and it has
        # to be a time, not a count of people or a tin size.
        amount = AMOUNT.search(line)
        worked = _sized_reply(answer, line, memory)
        if amount and worked:
            return worked
        for sentence in sentences[1:]:
            if not (TIME.search(sentence) and not already_said(memory, sentence)):
                continue
            # "how long for a 1.5kg one" is owed the figure for 1.5kg, and the sentence about
            # resting the bird for 15 minutes is about another thing however much of a time it
            # carries. A line that names an amount takes the sentence that names it, or the
            # rate that answers any amount ("20 minutes per 500g").
            if amount and amount.group(0).replace(" ", "") not in re.sub(r"\s+", "", sentence):
                # A rate answers any amount of the same thing, so the sentence that states it is
                # the answer - as long as it is not what they have just read.
                if RATE.search(answer) and not already_said(memory, answer, turns_back=1):
                    return answer
                continue
            return sentence
        if sentences and TIME.search(sentences[0]) and not already_said(memory, sentences[0]):
            span = _time_of(sentences[0])
            if span:
                return span[0].upper() + span[1:] + "."
        # The only sentence with the time in it has been said already. The time in it is still
        # the answer to this line, so give that clause rather than the whole sentence again.
        part = _pick_duration(sentences, wanted, memory, line)
        if part:
            return part
    if "how_often" in asks:
        # "how often should i do that?" after the gutters answer is answered by it: twice a year
        # is how the answer opens, and a search hedge would be the bot not reading its own last
        # line. The repetition has to open its sentence to be that answer: an aside in the
        # middle ("repeated for 20 minutes, three times a week...") is part of a longer piece
        # of advice, and cutting it out leaves "Three times a week." where the fuller line the
        # reader already gives (the sessions, the day off) is the better answer.
        for sentence in sentences:
            found = FREQUENCY.match(sentence)
            if not found or already_said(memory, sentence):
                continue
            return _phrase(found.group(0))
    return None


# The clause of a cooked answer that is about afterwards - standing, resting, cooling - carries a
# time too, and it is not the time the person asked for: "then a minute in cold water" is not how
# long an egg boils. A clause that starts "so" is the total the sentence has been working towards.
AFTERWARDS = re.compile(r"\b(?:then|rest|cool|stand|leave|sit|wait|soak|drain|cold water|"
                        r"ice|fridge|freezer|oven off|heat off)\b", re.I)
TOTAL = re.compile(r"\b(?:so|takes|total|in all|altogether)\b", re.I)


def _time_of(sentence):
    """The time in this sentence that answers "how long?": the total if it works one out, and
    otherwise the first one that is not about afterwards."""
    clauses = [clause for clause in (CLAUSE.split(str(sentence or "")) or [str(sentence or "")])
               if not _not_a_length(clause)]
    first = ""
    for clause in clauses:
        spans = list(TIME_SPAN.finditer(clause))
        if not spans:
            continue
        span = spans[-1].group(0).strip(" ,;")
        if TOTAL.search(clause):
            return span
        if not first and not AFTERWARDS.search(clause):
            first = span
    if first:
        return first
    spans = [match for clause in clauses for match in TIME_SPAN.finditer(clause)]
    return spans[-1].group(0).strip(" ,;") if spans else ""


# A clause that offers one of several times for one of several results: "6 minutes for a runny
# yolk", "9 to 10 for hard". Two of them in one sentence and the answer asked for is the range.
OPTION = re.compile(r"^\s*(\d+(?:\.\d+)?(?:\s*(?:-|to|and)\s*\d+(?:\.\d+)?)?)"
                    r"\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)?\s+for\b", re.I)


def _option_range(sentence):
    """"6 to 10 minutes" when the sentence offers times for several results, else ""."""
    found = []
    for part in CLAUSE.split(str(sentence or "")):
        match = OPTION.match(part)
        if match:
            found.append(match)
    if len(found) < 2:
        return ""
    unit = next((match.group(2) for match in found if match.group(2)), "")
    if not unit:
        return ""
    first = found[0].group(1).split()[0]
    last = found[-1].group(1).split()[-1]
    if first == last:
        return ""
    # The options have to run the same way: the times in one answer are often for different
    # things, and the first and last of them are not the ends of one range. "15 to 20 minutes
    # for a chicken or a turkey, 10 to 20 for a joint of beef ... 5 to 10 for a steak" was read
    # as "15 to 10 minutes", which is no range at all. A span that runs backwards is not an
    # answer, and the clause for the thing they asked about is.
    try:
        if float(re.sub(r"[^0-9.]", "", last)) <= float(re.sub(r"[^0-9.]", "", first)):
            return ""
    except ValueError:
        return ""
    return f"{first} to {last} {unit.lower()}"


# An apostrophe inside a word is a contraction or a possessive ("It's", "don't", "the dog's"),
# never a quotation mark: counting every one of them made half the answers with an "It's" in
# them read as half a quotation and threw their time away.
QUOTE_MARK = re.compile(r"(?<![A-Za-z])'|'(?![A-Za-z])|\"")


def _quoted(part):
    """True when this clause is inside a quotation, so it is half of what someone says."""
    text = str(part or "")
    return len(QUOTE_MARK.findall(text)) % 2


# One option of several in an answer: "6 minutes for a runny yolk", "10 to 20 for a joint of
# beef". The unit is said once and the options after it leave it out. An option runs to the next
# figure, not to the next comma: "10 to 20 for a joint of beef, lamb or pork" is one option.
OPTION_ANY = re.compile(
    r"(\d+(?:\.\d+)?(?:\s*(?:-|to|and)\s*\d+(?:\.\d+)?)?)"
    r"\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)?\s+for\b", re.I)


def _the_option_for_the_topic(sentence, line, memory):
    """The option in this answer that names what the conversation is on, or None.

    Only for an answer that offers a time for each of several things: the figure the follow-up
    wants is the one for their thing, not the first option and not a range stitched out of two
    of them. The unit is carried from the option that says it.
    """
    text = str(sentence or "")
    found = list(OPTION_ANY.finditer(text))
    if len(found) < 2:
        return None
    topic = str((carried_topic(memory, line) or {}).get("text") or "")
    subject = set(keywords(topic))
    if not subject:
        return None
    hits, unit = [], ""
    for index, found_one in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(text)
        piece = text[found_one.start():end]
        # The next option starts at its figure, so the comma (and the "and" or "or") in front of
        # it is still on the end of this one: "5 to 10 for a steak or chops, and" is one option.
        for _ in range(2):
            piece = re.sub(r"[\s,;:]+$", "", piece)
            piece = re.sub(r"\s+(?:and|or|to)$", "", piece)
        unit = found_one.group(2) or unit
        if set(keywords(piece)) & subject:
            hits.append((found_one, piece, unit))
    if len(hits) != 1:
        return None
    found_one, piece, unit = hits[0]
    if unit and not found_one.group(2):
        # "10 to 20 minutes" and not a bare "10 to 20", which reads as a count of nothing.
        cut = found_one.end(1) - found_one.start()
        piece = piece[:cut] + " " + unit.lower() + piece[cut:]
    return piece[:1].upper() + piece[1:] + "."


# Words that place a step in time and say nothing about how long it takes: "A week out" is when
# a thing happens, not a length, and said on its own it is a fragment with no verb in it.
TIME_ONLY = frozenset("""a an one two three four five six seven eight nine ten eleven twelve
    day days week weeks month months year years out before ahead after now from to in on at the
    of""".split())


def _only_a_marker(part):
    """True for a clause that is nothing but where a step sits in time ("A week out")."""
    words = re.findall(r"[a-z0-9']+", str(part or "").lower())
    if not words:
        return True
    return all(word in TIME_ONLY or DURATION.match(word) for word in words)


def _duration_clauses(sentence):
    """Every clause of this sentence that carries a time, as sentences of their own."""
    parts = []
    for part in _clauses_of(sentence):
        part = part.strip(" .")
        if _quoted(part):
            # "Play peekaboo and do short practice exits - 'I'm going to the kitchen, back in a
            # minute' - and always come back" has a time in it, but cutting the clause out of
            # the quotation gives "Back in a minute'", which is half a script and not a length.
            continue
        if part.lower().startswith("then "):
            part = part[5:]  # "then roast for 40 minutes" reads as "Roast for 40 minutes."
        if part.lower().startswith("and "):
            part = part[4:]  # "... and it settles in two to three days" is "It settles in ..."
        if WARNING_SPAN.search(part):
            continue
        if not part or _only_a_marker(part):
            continue
        if _not_a_length(part):
            continue
        if DURATION.search(part) or SPAN_ADJECTIVE.search(part):
            parts.append(part[0].upper() + part[1:] + ".")
    return parts


def _only_a_cadence(part):
    """True when the only time in this clause is how often to do it.

    "a few times a day" is a cadence and not a length: the shoulder answer's "circle it slowly)
    a few times a day" was handed back to "how long will it last" as if it were how long the
    pain lasts, and a person plans around a length. A clause that also carries a length of its
    own ("ice it for 20 minutes, three times a day") keeps it.
    """
    return bool(FREQUENCY.search(part)) and not DURATION.search(FREQUENCY.sub(" ", part))


# "on a dry day with no rain forecast for 24 hours" says how long the weather has to hold, not
# how long the job takes: the forecast is a window the work has to fit in. With the treatment
# interval passed over as a rate, that 24 hours was the only time left and answered "how long
# will it take" to paint a shed.
A_WEATHER_WINDOW = re.compile(
    r"\b(?:forecast|rain|showers?|dry|damp|frost|wind|sunshine?|weather|mild|warm|cold)\b"
    r"[^.;:,]{0,25}\bfor\s+$", re.I)


def _a_window_in_the_weather(part):
    """True when every time in this clause is how long the weather has to hold."""
    found = sorted(list(DURATION.finditer(part)) + list(SPAN_ADJECTIVE.finditer(part)),
                   key=lambda match: match.start())
    if not found:
        return False
    for match in found:
        if not A_WEATHER_WINDOW.search(part[:match.start()]):
            return False
    return True


def _not_a_length(part):
    """True when the time in this clause is not how long the job takes.

    Two shapes say a different thing with a time: how often to do it ("treat it every two or
    three years") and how long the weather has to hold ("on a dry day with no rain forecast for
    24 hours"). Both were handed back as the length of the job, so "how long will it take" to
    paint a shed was answered "Two or three years." and then "24 hours." A person plans around a
    length, so a clause that says neither is passed over.
    """
    return _only_a_cadence(part) or _a_window_in_the_weather(part)


def _duration_clause(sentence):
    """The first clause of this sentence that carries the time in it."""
    parts = _duration_clauses(sentence)
    return parts[0] if parts else None


def _shorten(part):
    """A long clause with a time in it comes back as the time itself.

    The time is the answer only when it ends the clause, which is the shape of an answer about a
    length of time: "roast it for 40 minutes" is 40 minutes. A time in the middle of a sentence
    is saying something else - "one lesson a week is what makes the rest stick" is a cadence, and
    cutting it to "a week." leaves a fragment that answers nothing.
    """
    text = str(part or "")
    if len(text.split()) > 9:
        found = DURATION.search(text)
        if found and not text[found.end():].strip(" .,;:!?"):
            # The time ends the clause but not the reply: it is cut out of the middle of the
            # answer's sentence, so it starts a sentence of its own and says so.
            span = found.group(0).strip(" .")
            return span[:1].upper() + span[1:] + "."
    return part


# The period a line counts in: "how long each day", "how many hours a week". A figure counted in
# a bigger unit than the one asked for is a different figure ("a week" is not how long each day),
# and said on its own it is not an answer at all.
PERIODS = {"minute": 0, "second": 0, "hour": 1, "day": 2, "week": 3, "month": 4, "year": 5}
PERIOD_ASK = re.compile(r"\b(?:a|an|each|every|per|one)\s+"
                        r"(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b", re.I)

# A clause that carries its time behind a verb says the doing, not the length: "repeated for 20
# minutes" to "how long each day" is 20 minutes. Only used for a period ask, where the figure
# itself is what was asked for; "boil for 10 minutes" is left as it is, because the doing is the
# only thing that says what the 10 minutes are for.
PERIOD_LEAD = re.compile(r"^(?:[a-z]+ed|takes?|lasts?|runs?)\s+(?:for|about|around|roughly)?\s*",
                         re.I)


def _asked_period(line):
    """The unit a line counts in ("how long each day" -> 2), or None when it names no period."""
    found = PERIOD_ASK.search(str(line or ""))
    if found is None:
        return None
    unit = found.group(1).lower().rstrip("s")
    return PERIODS.get(unit)


# A length of time counted on its own: a digit, or a number spelled out. The bare article is not
# one - "give each topic a day" carries a unit and no figure, and handed back as an answer it says
# "a day", which is nothing.
FIGURED = re.compile(
    r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|couple|few|several|dozen|half|quarter)\b",
    re.I)


def _in_period(part, period):
    """True when the time in this part is counted in the period the line asked for.

    A smaller unit answers a bigger period ("half an hour a week" answers "how long each week"),
    a bigger one does not: "a week" is not how long each day. A part with a unit and no figure is
    not a length of time at all, so it is never the answer to a "how long"."""
    if period is None:
        return True
    if not FIGURED.search(str(part or "")):
        return False
    found = DURATION.search(str(part or ""))
    if found is None:
        return False
    counted = found.group(0).lower()
    for name, rank in PERIODS.items():
        if name in counted:
            return rank <= period
    return False


def _pick_duration(sentences, wanted, memory, line=""):
    """The time in the answer this line is asking about.

    "And how long for a hard boiled one?" names the part it wants, and the sentence that has
    that part in it carries the unit with it ("6 minutes for a runny yolk, 7 for jammy, 9 to 10
    for hard boiled"), so that sentence comes whole: cut it to a clause and "9 to 10" has lost
    what it counts. When the line names nothing of its own ("how long do I need?"), the last
    time in the answer is the one for the dish being made, which is the oven step.
    """
    if LENGTH_ASK.search(line or ""):
        # Only a sentence that states a time can answer a how-long ask. Scoring every sentence
        # by shared words let the method sentence win on "take" ("how long will it take?"), and
        # the time sentence was never looked at.
        sentences = [sentence for sentence in sentences
                     if DURATION.search(sentence) or SPAN_ADJECTIVE.search(sentence)]
        if not sentences:
            return None
        # Of those, a stretch ("two to three days") answers "how long does it last", while a
        # threshold ("it lasts more than a week") answers "when should I worry". The threshold
        # used to take the question because it shares the verb, so it is looked at last.
        spans = [sentence for sentence in sentences if not THRESHOLD_SPAN.search(sentence)]
        if spans:
            sentences = spans
    wanted = set(wanted)
    best_overlap, best_index = 0, 0
    for index, sentence in enumerate(sentences):
        words = {stem(word) for word in keywords(sentence)}
        overlap = len(wanted & words)
        if overlap > best_overlap:
            best_overlap, best_index = overlap, index
    if best_overlap:
        sentence = sentences[best_index]
        period = _asked_period(line)
        if period is not None:
            # The line counts its answer in a period, and the sentence that shares a word with
            # it usually shares one that is not a time at all: "how long each day" meets "a
            # rest day between" in a running answer, and said whole that sentence has not
            # answered when the day's bit is. The time counted in that period is the answer.
            parts = [part for part in _duration_clauses(sentence)
                     if _in_period(part, period)]
            part = _step_they_asked_for(parts, wanted)
            if part:
                part = PERIOD_LEAD.sub("", part)
                if not part[:1].isupper():
                    part = part[:1].upper() + part[1:]
            return _shorten(part) if part else None
        # Already said: the part of it with the time in it is still news, the rest is not.
        if not already_said(memory, sentence):
            return sentence
        parts = [part for part in _duration_clauses(sentence)
                 if not already_said(memory, part)]
        part = _step_they_asked_for(parts, wanted)
        return _shorten(part) if part else None
    if not best_overlap:
        # "And how long?" over an answer that lists the options - "6 minutes for a runny yolk, 7
        # for jammy, 9 to 10 for hard" - has no one answer, and picking the first is a guess at
        # what they want. The range of the options is the honest answer and it is still a figure.
        choices = _option_range(sentences[0]) if sentences else ""
        if choices:
            return choices
        # Options for several different things do not make one range, and the answer is the
        # option for the thing the conversation is on: "how long should i rest a joint of beef"
        # then "and how long?" was answered "15 to 10 minutes" - the first and last figures of
        # four different joints - and then "15 to 20 minutes for a chicken", which is another
        # dish's time. The clause that names the subject is the one figure that answers it.
        part = _the_option_for_the_topic(sentences[0], line, memory) if sentences else None
        if part:
            return part
    period = _asked_period(line)
    parts = [part for sentence in sentences for part in _duration_clauses(sentence)
             if not already_said(memory, part) and _in_period(part, period)]
    part = _step_they_asked_for(parts, wanted)
    return _shorten(part) if part else None


def _step_they_asked_for(parts, wanted):
    """The last time in the answer that is not a step afterwards, unless they asked for that.

    "6 minutes for a runny yolk ... then a minute in cold water" ends on the cold water, and the
    cold water is not how long an egg boils; the same answer said to "how long should I rest it"
    is exactly the resting clause, so a clause they named is never dropped.
    """
    kept = [part for part in parts
            if not AFTERWARDS.search(part) or set(keywords(part)) & set(wanted)]
    if kept:
        return kept[-1]
    return parts[-1] if parts else None

def _time_in_words(minutes):
    """80 -> "1 hour 20", 50 -> "50 minutes". Rounded to five, the way a recipe talks."""
    minutes = int(round(minutes / 5.0)) * 5
    hours, rest = divmod(minutes, 60)
    if not hours:
        return f"{rest} minutes"
    hours_text = f"{hours} hour" + ("" if hours == 1 else "s")
    return f"{hours_text} {rest}" if rest else hours_text


def time_for_amount(answer, line):
    """The time an answer's own rate gives for the amount a follow-up names, or None.

    "20 minutes per 500g plus 20 minutes" is a rule that answers any weight, and someone who
    asks "how long for a 1.5kg one" wants the time for their bird, not the rule to work out
    themselves. Only a rate with a weight in it is worked out, only for an amount in the same
    kind of unit, and only for a total that a roast could plausibly take, so a rate that is
    not a cooking time is left alone.
    """
    amount = AMOUNT.search(str(line or ""))
    rate = RATE_BY_WEIGHT.search(str(answer or ""))
    if not amount or not rate:
        return None
    each, per, unit = rate.groups()
    said_unit = re.sub(r"[\d.\s]", "", amount.group(0)).lower()
    if said_unit not in WEIGHT_IN_GRAMS or unit.lower() not in WEIGHT_IN_GRAMS:
        return None
    want = float(re.sub(r"[^\d.]", "", amount.group(0))) * WEIGHT_IN_GRAMS[said_unit]
    base = float(per) * WEIGHT_IN_GRAMS[unit.lower()]
    if base <= 0 or want <= 0:
        return None
    total = float(each) * want / base
    extra = PLUS_MINUTES.search(str(answer))
    if extra:
        total += float(extra.group(1))
    if not 5 <= total <= 12 * 60:
        return None
    return _time_in_words(total)


def _already_for_this_size(line, answer):
    """True when the answer has already worked its rate out for the size this line names.

    Then the figure is in the answer for that size ("1 hour 40"), and saying the rule again
    would be longer than the answer they are owed.
    """
    asked, told = AMOUNT.search(str(line or "")), OWN_SIZE.search(str(answer or ""))
    if not asked or not told:
        return False
    grams = _in_grams(asked.group(0))
    said = _in_grams(told.group(1) + told.group(2))
    return grams is not None and grams == said


def _in_grams(text):
    """An amount in grams, or None when it is not a weight."""
    found = re.match(r"\s*(\d+(?:\.\d+)?)\s*(kg|g|lb|lbs|pound|pounds|oz|ounce|ounces)\b",
                     str(text or ""), re.I)
    if not found:
        return None
    return round(float(found.group(1)) * WEIGHT_IN_GRAMS[found.group(2).lower()], 1)


def _names_another_thing(line, answer, about=()):
    """True when the line names a word the answer is not about.

    "how long do i roast a 2kg leg of lamb" after the bird's answer carries a weight the rate
    could work out, but the lamb is not the thing the rate is for, so the figure would be
    somebody else's. A word that is only the ask ("long", "one") does not count.
    """
    said = set(stem(word) for word in keywords(answer))
    said |= set(stem(word) for word in about or ())
    for word in keywords(line):
        if AMOUNT.search(word) or word in ASK_ONLY:
            continue
        if stem(word) not in said:
            return True
    return False


def sized_reply(answer, line, memory, about=()):
    """The time this answer's own rate gives for the size this line names, or None.

    Public because the module that answers with the entry's own paragraph needs it too: the
    question "how long for 250g" reaches the roast entry by name, so the whole paragraph comes
    back before any follow-up is looked at, and the figure they asked for is inside it. `about`
    is what the entry is about, so a line naming the dish ("a 250g chicken") is not read as a
    line naming something else than the answer, which says "bird" and never "chicken".
    """
    if _names_another_thing(line, answer, about) or _already_for_this_size(line, answer):
        return None  # the rate is not for this thing, or the figure for this size is in the answer
    return _sized_reply(answer, line, memory)


def _sized_reply(answer, line, memory):
    """The time the answer's own rate gives for the amount in the line, said with the rule, or None.

    "how long for a 1.5kg one" after "20 minutes per 500g plus 20 minutes": the rule worked out
    for their size, with the rule kept behind it so nothing is hidden. Asked again in the same
    words, the same time is said another way rather than word for word.
    """
    amount = AMOUNT.search(str(line or ""))
    if not amount:
        return None
    sized = time_for_amount(answer, line)
    if not sized:
        return None
    rule = _rate_said(answer)
    if not rule:
        return None
    said = amount.group(0)
    times = _times_asked(line, memory)
    if times >= 2:
        return f"{sized.capitalize()} for {said}, the same rule: {rule}."
    if times == 1:
        return f"Still {sized} for {said}: {rule}."
    return f"About {sized} for {said}: {rule}."


def _times_asked(line, memory):
    """How many turns in a row just before this one asked this same line, word for word."""
    wanted = " ".join(str(line or "").lower().split())
    count = 0
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            break
        if " ".join(str(turn.get("user") or "").lower().split()) != wanted:
            break
        count += 1
    return count


def _rate_said(answer):
    """The sentence of an answer that states a cooking rate, without the size it worked out."""
    for sentence in SENTENCE.split(str(answer or "")):
        if not RATE_BY_WEIGHT.search(sentence):
            continue
        head = re.split(r"[,;]?\s+so\b", sentence, maxsplit=1)[0].strip(" .,;")
        head = re.sub(r"^about\s+", "", head, flags=re.I).strip(" .,;")
        return head[:1].lower() + head[1:] if head[:1].isupper() else head
    return ""


def _phrase(text):
    """A phrase of an answer said as a sentence of its own: "three times a week" -> "Three..."."""
    text = str(text or "").strip(" ,;:")
    return text[:1].upper() + text[1:] + "." if text else ""


def has_time(text):
    """True when a line or an answer carries a length of time in it ("40 to 45 minutes")."""
    return bool(TIME.search(str(text or "")))


def _worked_out_for_this_line(understood, line, answer):
    """The time an answer's own rate gives for the amount this line names, or None.

    "how long for 700g" after "20 minutes per 500g plus 20 minutes" is the same question about
    another size of the same roast: the answer works it out (time_for_amount), so it is a
    follow-up on what we are on even without an "it" or a "one" to point back with. When the
    answer carries no rate in weight (boiling an egg, roasting potatoes) nothing is worked out
    and the line is left to the subject it names.
    """
    if not isinstance(understood, dict) or "how_long" not in (understood.get("asks") or ()):
        return None
    return time_for_amount(answer, line)


# "where are you", "who are you", "what are you": the thing these name is the bot. Every word
# of them is a stopword, so they looked like a bare ask for a property of the last answer, and the
# answer just given came back with a "Same as before:" in front of it - "where are you" after a
# pot of rice re-served the rice. A question about the bot is not a question about the rice, and
# the bot's own reply (the chat module) is the one that answers it.
_ASKS_WHAT_I_AM = re.compile(
    r"^\s*(?:(?:so|ok|okay|and|but|hey|well)\s+)*"
    r"(?:where|what|who|which)\s+(?:are|r)\s+(?:you|u|ya)\b"
    r"(?:\s+(?:from|based|exactly|then|though|really|actually|now))?\s*\??\s*$")


def asks_only(understood):
    """True when the line asks for a property and names no thing of its own.

    "how long do I need?", "what temperature?", "and how much?" carry nothing but the ask. The
    thing they are about is the answer just given, so they are a question about that answer and
    not about a neighbour entry the ask happens to fit: "how long do I need?" after a tray of
    roast potatoes also reaches the boiled-potatoes entry, and boiling is not the answer to
    roast ones.

    A line made only of stopwords is this too ("what should I get for it?"), and what it wants
    is the answer just given, not a neighbour. The one exception is a request to carry on
    ("what should I do about it?"), which asks for the next step rather than a sentence of the
    last answer; `same_as_before` and `leans_on_topic` stand down for those.
    """
    if not isinstance(understood, dict) or not (understood.get("asks") or ()):
        return False
    line = understood.get("clean") or understood.get("text") or ""
    if _ASKS_WHAT_I_AM.match(str(line).lower()):
        return False
    return not [word for word in keywords(line) if word not in ASK_ONLY]


def _earlier_subject_sentence(line, understood, memory, skip, turns_back=2):
    """A sentence from the answer to an earlier subject this line still has a word in common with."""
    records = memory.get("topics")
    if not isinstance(records, list):
        return None
    mine = {stem(word) for word in keywords(line)}
    seen = 0
    for record in reversed(records):
        if not isinstance(record, dict) or record is skip:
            continue
        asked = str(record.get("text") or "")
        if not asked or already_said(memory, record.get("bot")):
            continue
        if not mine & {stem(word) for word in keywords(asked)}:
            continue
        seen += 1
        if seen > turns_back:
            return None
        answer = entry_answer(memory, asked) or str(record.get("bot") or "")
        chosen = _pick_sentence(line, understood, answer, memory, strict=True)
        if chosen:
            return chosen
    return None


def _repeats_the_question(line, asked):
    """True when this line asks what the conversation is already about, word for word."""
    wanted = [stem(word) for word in keywords(line)]
    if not wanted:
        return True
    said = [stem(word) for word in keywords(asked)]
    return sum(1 for word in wanted if word in said) >= 0.6 * len(wanted)


def already_said(memory, text, turns_back=3):
    """True when this exact wording was one of the bot's last few replies."""
    said = " ".join(str(text or "").lower().split())
    if not said:
        return True
    for turn in (memory.get("turns") or [])[-turns_back:]:
        if isinstance(turn, dict) and " ".join(str(turn.get("bot") or "").lower().split()) == said:
            return True
    return False


# The verbs and ask words that make a "how do I ..." line a request for the steps of the thing we
# are already on, rather than a question about a new thing ("how do i cancel her insurance").
STEP_ASK_WORDS = frozenset("""
how what when where which who why do does did i we you me my it this that they he she
fix sort make get work use put keep go come start stop change deal help try take set tell say
give find need want know best should can could would will shall may might
""".split())


def _names_something_new(line, answer):
    """True when the line names a thing the answer never mentions."""
    said = {stem(word) for word in keywords(answer)}
    for word in keywords(line):
        if word in STEP_ASK_WORDS or stem(word) in said:
            continue
        return True
    return False




# The words that make the next word a thing the line names for itself: "what about a leg of
# lamb", "and the radiator?".
# A line that asks the bot to fetch something is a request, not a thing of its own.
REQUEST_A_THING = re.compile(r"\b(?:find|give|send|show|get|recommend|suggest|list|write|make)"
                             r" me\b|\bdo you have\b|\bany chance\b"
                             r"|\bcan you (?:find|give|send|show|recommend|suggest|list\b)", re.I)
A_THING = frozenset("a an the my our another some this that".split())


def _named_a_fresh_thing(text, record, answer=""):
    """True when the line names a thing the topic does not have: "a leg of lamb" after a chicken.

    A word that was already in the answer just given is a detail of the subject, not a new one:
    "does the vinegar matter" and "what about the yolk" after the poached egg are about the egg.
    """
    if REQUEST_A_THING.search(str(text or "")):
        # "can you find me a recipe" asks the bot for the answer, it does not name a new subject:
        # the recipe wanted is the one for the thing the chat is already on.
        return False
    known = {stem(word) for word in (record or {}).get("words") or []}
    known |= {stem(word) for word in words(str(answer or ""))}
    said = words(str(text or ""))
    for at, word in enumerate(said[:-1]):
        if word.lower() in A_THING and stem(said[at + 1]) not in known:
            return True
    return False


# How many turns back the card a follow-up draws on can have been given.
MOVED_KEEP = 8


def _the_thing_the_chat_moved_to(whole, line, memory, keep=MOVED_KEEP):
    """The entry of the thing named after the card was given, when the chat moved to it.

    A follow-up that names nothing of its own ("how long does it last") leans on whatever the chat
    is on, and the card a follow-up draws on is the entry's answer - which can be several turns
    old. That card is the answer only while the chat is still on its subject. A statement in
    between that names a thing of its own, reaches its own entry and was answered as its own
    subject moves the chat to that thing, even though it was a statement: "we want to try for a
    baby" ... "my baby has a fever" ... "how long does it last" was handed "Have sex every two or
    three days rather than saving up.", a clause of the trying-for-a-baby card, as the answer to a
    question about a child's fever. A wrong fact is the worst reply there is.

    Only while the thing it moved to can answer the line itself: "how much should i pay a plumber"
    with a fever remark in between is still a question about the plumber, and a subject with no
    figure of the kind asked for is no better than the card the person was on.
    """
    from .narrow import SPANS, kind_of  # lazy: the store needs no reader of its own
    turns = [turn for turn in (memory.get("turns") or [])[-keep:] if isinstance(turn, dict)]
    wanted = words(str(whole or ""))[:8]
    at = None
    for index, turn in enumerate(turns):
        if words(str(turn.get("bot") or ""))[:8] == wanted:
            at = index
    if at is None:
        return None
    was = _entry(str(turns[at].get("user") or ""))
    if was is None:
        return None
    figure = SPANS.get(kind_of(line))
    if figure is None:
        return None
    for turn in reversed(turns[at + 1:]):
        said = str(turn.get("user") or "")
        if not said or words(said) == words(str(line or "")):
            continue  # the turn in hand is the one being read
        if turn.get("module") in (None, "answers"):
            continue  # the knowledge base answered it, so it was read as part of this thing
        named = _entry(said)
        if named is None or named == was:
            continue
        if figure.search(str(getattr(named, "reply", "") or "")):
            return named
    return None


def left_for_a_blank(memory, line):
    """True when the chat moved to a thing named in between and got no answer for it.

    "how do I roast a chicken" / "what about a leg of lamb?" (no entry, so a hedge) / "and how
    long should that take?" is a question about the lamb: the chicken times are a wrong answer
    rather than a helpful one, so nothing is drawn from the older subject. A line that only says
    what to do about the thing we are on ("can I fix it myself?") leaves the topic where it was.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return False
    last = turns[-1]
    if " ".join(words(str(last.get("user") or ""))) == " ".join(words(str(line or ""))):
        return False  # the turn in hand is the one being read: nothing to look past
    if last.get("module") == "answers":
        return False
    asked = str(last.get("user") or "")
    if not _a_question(asked):
        # A statement that names something is usually a detail of the thing the chat is on
        # ("one loves dinosaurs and the other loves space" is the twins' party), so it does not
        # move the chat off that thing. A question does name what it asks about.
        return False
    if not POINTS_BACK.search(str(line or "")):
        # The line has to point at the thing left blank ("and how long should that take?"). A
        # line that names nothing and points at nothing is a question about what the chat was on
        # before the remark: "how do i make bread" / "and the radiator" / "what temperature" is
        # the oven, and "how do i sharpen a knife" / "and the cat" / "what about the whetstone"
        # is the whetstone in the knife answer. Read while looking past a remark, both were
        # hedged, which is a worse answer than main's.
        return False
    # The answer on the subject is part of what the chat knows: a word in it is a detail of that
    # subject ("does the vinegar matter" and "what about the yolk" are about the poached egg),
    # so a line asking about that word does not move the chat to a thing of its own.
    record = carried_topic(memory, line)
    answer = entry_answer(memory, str((record or {}).get("text") or "")) or str(last.get("bot") or "")
    return _named_a_fresh_thing(asked, record, answer)


# A line that points back at the thing it asks about: "and how long should that take?", "how
# long does it take", "what about those". A question with none of these words and no thing of its
# own ("what temperature") is about what the chat was on before the remark in between.
POINTS_BACK = re.compile(r"\b(?:it|that|this|those|these|they|them|its)\b|\bthe one\b", re.I)

# A line that asks something: it ends on a question mark or opens with a question word. Only
# such a line says what the chat has moved to; a statement adds to what we are already on. The
# name is its own ("a question for the topic reader", not "asks") because the file already has an
# _asks, the repo's own reader that asks_after uses: a second definition of the same name silently
# takes over every earlier caller, and the two readers disagree about "and the pressure".
A_QUESTION = re.compile(r"\?\s*$|^\s*(?:and|also|or|so|but|then)\s+\S+"
                        r"|^\s*(?:what|how|which|where|when|who|why|whose|is|are|was|were|do"
                        r"|does|did|can|could|should|would|will|shall|must|have|has|had|am)\b",
                        re.I)


def _a_question(text):
    return bool(A_QUESTION.search(str(text or "")))


# A question that names no subject of its own, only what it wants to know: "what should I wear",
# "what should I do first", "where should I start". Alone it is about nothing. The advice word is
# what tells it from a question about the person's own facts ("which city did I say first",
# "what is my cat called", "what am I planning"), which is the memory's to answer, not the
# topic's: those name something of theirs and are not advice asks.
BARE_ASK = re.compile(r"\b(?:what|which|how|where|when)\b(?![^?.!]{0,40}\b(?:did|have|has)\s+i\b)"
                      r"[^?.!]{0,40}\b(?:should|shall|can|could|ought)\b"
                      r"|^\s*(?:so\s+)?(?:should|shall|can|could|must|do)\s+(?:i|we)\b", re.IGNORECASE)
BARE_WORDS = 8


def bare_question(understood, memory):
    """True for a short question with no subject of its own, after a topic it can lean on.

    "What should I wear" after "I'm going to a wedding next week" is a question about the
    wedding - the knowledge base has the wedding outfit entry and the line on its own reaches
    nothing, so it was read as a request for a search. Only a line that reaches no entry by its
    own words and only while there is a topic to lean on, so "what should I cook" said on its
    own is still the general question it is.
    """
    if not isinstance(understood, dict) or understood.get("kind") != "question":
        return False
    line = " ".join(str(understood.get("clean") or understood.get("text") or "").lower().split())
    if not line or len(line.split()) > BARE_WORDS or is_ack(line):
        return False
    if not BARE_ASK.search(line):
        return False
    if carried_topic(memory, line) is None:
        return False
    if follows_on(understood, line):
        return False  # it already points back at the topic ("how do I fix it?"): not bare
    if ASKS_ABOUT_THEMSELVES.search(line):
        return False  # the topic is not the answer: "when am i going" is in the plans memory keeps
    return _entry(line) is None


# "when am i going", "where are we staying", "what did i say": the line puts the person in the
# question as the subject of their own doings, and the answer is what they told us, not the
# knowledge base entry for the topic. Only the forms that make the person the subject (am/are/
# was/were/did) - "how do i start" and "what should i wear" carry a modal and a verb of their
# own, and those are questions about the topic.
ASKS_ABOUT_THEMSELVES = re.compile(
    r"\b(?:what|where|when|who|which|how|why)\s+(?:am|are|was|were|did)\s+(?:i|we)\b")


# A topic is the thing a follow-up is about only while the chat is still on it. One reply of
# small talk ends it, and the ask after it leans on that instead of on the topic:
# "what should i have for dinner" / "i only got mince and some spuds" / "hows it going with u" /
# "why is that" was widened with the dinner line, two turns stale, and answered with the next dish
# in the plan - a baked potato nobody had asked for, an hour after dinner.
#
# What keeps it alive: an acknowledgement or a greeting, which name nothing of their own, and any
# line that is about something ("and when did i tell you i start" is still the job). What ends it:
# a line that is small talk, because a question about the bot's day puts the chat on the bot, and
# the thing on the screen is no longer what the next ask is about.
def _still_the_topic(record, memory):
    """True when no turn since this topic's has put the chat on the bot instead."""
    if not isinstance(record, dict):
        return False
    index = record.get("turn")
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(index, int) or not isinstance(turns, list):
        return True
    from ..understanding import understand
    for turn in turns[index + 1:]:
        if not isinstance(turn, dict):
            continue
        said = " ".join(str(turn.get("user") or "").lower().split())
        if not said or is_ack(said) or said in GREET:
            continue
        if str(understand(said).get("intent") or "") == "smalltalk":
            return False
    return True


def carried_topic(memory, text):
    """The topic this line carries on from: what we were on before it, not the line itself.

    memory_store notes every line, so on a follow-up the current topic can already be this very
    line (with its words merged in). Reading it back out of memory["topics"] keeps the subject
    the follow-up left out.
    """
    line = " ".join(words(text))
    records = memory.get("topics")
    if isinstance(records, list):
        for record in reversed(records):
            if not isinstance(record, dict):
                continue
            if " ".join(words(record.get("text") or "")) != line:
                # A detail points back at the thing it is a detail of: "he is allergic to nuts"
                # is what we were on before this line, but the thing the next ask is about is
                # the cake, and the nuts' words reach nothing.
                return _thing_of(memory, record) or record
    return current(memory)


def leans_on_topic(understood, memory):
    """True when this line carries on the current topic instead of naming its own subject."""
    if not isinstance(understood, dict):
        return False
    if _after_an_emergency(memory):
        return False  # the fire is not a subject to carry a question about
    if _after_a_correction(memory):
        return False  # the subject they have just replaced is not the one being asked about
    said = understood.get("clean") or understood.get("text") or ""
    # The shrugs in the middle of the line are not part of what it is about, but the one that
    # opens it can be the turn itself ("actually it's a funeral"), so the switch is read from the
    # line as it came in and the shrugs come out only of the rest.
    text = without_the_shrug(said)
    # "What should I do about it?" carries on from the answer, not from the topic's words: read
    # in context it reaches the same entry and the paragraph comes back word for word.
    if any(phrase in text.lower() for phrase in PROCEED):
        return False
    record = carried_topic(memory, text)
    if record is None or not text.strip() or is_ack(text):
        return False
    if opens_by_switching(said):
        return False
    # A fact or a limit about what we are already on: it leaves the subject out on purpose.
    if DETAIL.search(text):
        known = set(record.get("words") or [])
        fresh = [word for word in keywords(text) if stem(word) not in known]
        return len(fresh) <= 4 and len(words(text)) <= 14
    # Otherwise the line has to point back at the topic ("and if I stuff it?", "how long will
    # that take?"), or name nothing at all and reach an entry with the topic's words carried
    # ("how often should I go?" after running). A follow-up that names something of its own
    # ("how long in the oven?") is left as it is: it may be about a different thing of the same
    # kind, and a wrong fact is worse than none.
    if follows_on(understood, text):
        return True
    carried = carry_the_ask(text, record.get("text") or "", understood, memory)
    if carried is None:
        # Nothing the topic's words reach: the one kind of line that still leans on the topic is
        # a short question that names no subject at all ("what should I wear" after a wedding,
        # "what should I do first" after a move). Read through bare_question it reaches the
        # topic's entry; read on its own it reaches nothing.
        return bare_question(understood, memory)
    # A line that names the topic's own words is still on the topic: "how many weeks should i
    # train" after "I'm training for a half marathon" names nothing but the marathon's training,
    # and the ask is about that. "how long in the oven?" names something the topic does not
    # carry, which may be a different thing of the same kind, and is left as it is.
    return names_nothing(text) or _only_the_topics_own_words(text, record)


def _only_the_topics_own_words(text, record):
    """True when every content word of the line is a word the topic already carries."""
    known = [word for word in (record or {}).get("words") or [] if isinstance(word, str)]
    if not known:
        return False
    return not [word for word in _content_words(text)
                if not any(alike(word, said) for said in known)]


# A line that only names the next thing of the same ask: "and for lunch" straight after "what
# should I have for breakfast". The knowledge base has a lunch answer; it has no answer to an
# "and for" line, so the ask is carried on with the new thing in it.
NEXT_SLOT = re.compile(r"^(?:and|also|plus|then|ok|okay|so)\s+(?:what\s+)?for\s+([a-z0-9' ]{2,24})$")
ASK_SLOT = re.compile(r"\bfor\s+([a-z0-9' ]{2,24})$")
ASK_WORDS = re.compile(r"\b(?:what|which|how|where|when|who|why|should|shall|can|could|would|any)\b")


def next_slot_reading(understood, memory):
    """'and for lunch' read as the last question with lunch in it, or None.

    Only a line that says nothing but the next thing, and only when the line before it asked
    something with a "for" in it ("what should I have for breakfast"), so an "and for" line
    after news stays the plain acknowledgement it is.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = " ".join(str(understood.get("clean") or understood.get("text") or "").lower().split())
    slot = NEXT_SLOT.match(line)
    if slot is None or understood.get("kind") == "question":
        return None
    turns = memory.get("turns")
    previous = ""
    if isinstance(turns, list) and turns:
        previous = str((turns[-1] or {}).get("user") or "")
    asked = " ".join(previous.lower().split())
    if not asked or ASK_WORDS.search(asked) is None:
        return None
    tail = ASK_SLOT.search(asked)
    if tail is None:
        return None
    thing = slot.group(1).strip()
    if not thing or thing == tail.group(1).strip():
        return None
    reading = dict(understood)
    reading["clean"] = (asked[:tail.start()] + "for " + thing).strip()
    reading["text"] = reading["clean"]
    reading["words"] = words(reading["clean"])
    reading["kind"] = "question"
    reading["intent"] = "question"
    return reading


# A line that asks how two animals will get on names neither of them ("will they get
# on?").  With a new pet in the plan and one already in the house, the introduction
# question can be put back together from the two facts the store keeps.
TWO_PETS_ASK = re.compile(
    r"^(?:and |so |but )?(?:will (?:they|the two(?: of them)?|both(?: of them)?) (?:get on|get along|"
    r"fight|like each other|settle)"
    r"(?: (?:ok|okay|alright|fine|together))?"
    r"(?: with (?:each other|one another))?"
    r"|are they going to (?:get on|get along|fight)"
    r"|(?:can|could|will) (?:they|the two) (?:live|get) (?:together|along))"
    r"[\s?.!]*$",
    re.I)
PET_WORD = re.compile(
    r"\b(kittens?|cats?|pupp(?:y|ies)|dogs?|rabbits?|bunn(?:y|ies)|hamsters?|guinea pigs?|"
    r"ferrets?|parrots?|budgies?)\b", re.I)
PET_ONE = {
    "kittens": "kitten", "cats": "cat", "puppies": "puppy", "dogs": "dog",
    "rabbits": "rabbit", "bunnies": "bunny", "hamsters": "hamster",
    "guinea pigs": "guinea pig", "ferrets": "ferret", "parrots": "parrot",
    "budgies": "budgie",
}
PET_ARRIVING = re.compile(
    r"\b(?:getting|bringing|bringing home|joining|coming|arriving|arrives|arrive|"
    r"next (?:week|month|year)|in (?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)|soon)\b", re.I)
PET_EXISTING = re.compile(r"\b(?:already|existing|older|old|has been|have had)\b", re.I)


def _introduction_covered(new, old):
    """True when an animal introduction card answers this pair.

    `cat-second-cat` covers a new cat or kitten with an older cat; `cat-dog-intro`
    covers a cat or kitten with a dog or puppy in either direction.  A rabbit,
    hamster or bird has no introduction answer yet, and the people-introduction
    card is not a substitute.
    """
    cats = {"cat", "kitten"}
    dogs = {"dog", "puppy"}
    return ((new in cats and old == "cat")
            or (new in cats and old in dogs)
            or (new in dogs and old in cats))


def introduction_question(text, memory):
    """The full introduction question for "will they get on?" after a second pet.

    A line that asks about the two animals names neither of them, so on its own it reaches
    no knowledge entry. When the plan names a new pet - or the line that brought it in says
    it is on its way - and the store has one other pet, the line is about introducing those
    two: "how do i introduce a new kitten to my older cat". Empty when the line is not that
    ask, when the store cannot tell which two animals it means, or when no animal card
    answers that pair, so a line about a child, an unrelated "problem" or a kitten and a
    rabbit is left alone.
    """
    if not isinstance(text, str) or not isinstance(memory, dict) or not TWO_PETS_ASK.search(text):
        return ""
    known = memory.get("user")
    if not isinstance(known, dict):
        return ""
    animals = []
    for pet in known.get("pets") or ():
        animal = pet.get("animal") if isinstance(pet, dict) else None
        animal = str(animal or "").strip().lower()
        animal = PET_ONE.get(animal, animal)
        if animal and animal not in animals:
            animals.append(animal)
    if len(animals) != 2:
        return ""
    plan = known.get("plan")
    named = PET_WORD.search(plan) if isinstance(plan, str) else None
    new = ""
    if named is not None:
        new = PET_ONE.get(named.group(1).lower(), named.group(1).lower())
    else:
        # A line that says the pet is on its way is the new one even when the store did not
        # keep it as a plan: "a kitten is joining us in june".  The line that says it is
        # already here ("my old cat has been here ten years") is the one it is joining.
        arriving = []
        for fact in memory.get("facts_log") or ():
            if not isinstance(fact, dict) or fact.get("key") != "pet":
                continue
            said = str(fact.get("text") or "")
            found = PET_WORD.search(said)
            if found is None or not PET_ARRIVING.search(said) or PET_EXISTING.search(said):
                continue
            animal = PET_ONE.get(found.group(1).lower(), found.group(1).lower())
            if animal not in arriving:
                arriving.append(animal)
        if len(arriving) == 1:
            new = arriving[0]
    if not new:
        return ""
    others = [animal for animal in animals if animal != new]
    if len(others) != 1:
        return ""
    old = others[0]
    if not _introduction_covered(new, old):
        # The knowledge base has animal introductions only for a cat meeting a cat and a
        # cat meeting a dog.  A kitten and a rabbit would otherwise be sent to the card
        # that introduces two people, which is a confident answer about the wrong thing;
        # leaving the line alone lets the honest hedge answer it.
        return ""
    return "how do i introduce a new %s to my older %s" % (new, old)
# --- what the weather will be like on the trip -------------------------------------------
# A day and a month are not what a chat is about, but the place and the month of a trip are what
# a weather question is answered with, so the follow-up below reads them back out of the topic.
WEATHER_WORDS = frozenset("""
weather hot hotter cold colder warm warmer cool freezing boiling rain rains raining rainy
showers shower sunny sun sunshine cloudy cloud clouds wind windy humid humidity temperature
degrees forecast snow snowing coat coats jacket layers jumper
""".split())

MONTH_NAMES = frozenset("""january february march april may june july august september october
november december""".split())

# The grammar a line can spend on asking the weather and nothing else: "will it rain this week?"
# is about the weather, while "my weather station is broken" is about the station.
WEATHER_NOISE = frozenset("""
ok okay k so and but the a an in on at for to of it its this that these there here what whats
how will would be is was were am get getting go going we you they i me my our us week weeks
day days month months time much many like look looks outside today tomorrow tonight now then do
does did shown show get better need bring bring take maybe probably out up over all there
""".split())

# A line that says when or where it is about, and it is here and now rather than the trip: "what's
# the weather like today", "what's the weather like here", "is it raining now" are questions
# about the window the person is standing at, and the trip's month is a climate average for a
# place they are not in yet. A wrong fact is worse than the honest "I can't see a forecast".
NOW_AND_HERE = re.compile(
    r"\b(?:today|tonight|tomorrow|now|right now|outside|here|this afternoon|this evening"
    r"|this morning|at the moment|currently)\b")

# What asks a question, for a line short enough that the weather word is all it is about.
WEATHER_ASKS = re.compile(
    r"\?|^(?:is|are|do|does|will|would|can|could|should|shall)\b"
    r"|\b(?:what|whats|how|when|where|which|will|would|can|could|should|any|much|many|need)\b")


def the_weather_ask(understood):
    """True for a line that only asks about the weather, naming nothing else of its own.

    "what's the weather like", "how hot will it be", "will it rain this week" are all of them
    asks with no subject: on their own they are a question about the meaning of the words, and
    the knowledge base has no numbers to give. A line that names something else is not this.
    """
    line = str(understood.get("clean") or understood.get("text") or "")
    said = words(line)
    if not any(word in WEATHER_WORDS for word in said):
        return False
    if ASK_CUE.search(line.lower()) is None and WEATHER_ASKS.search(line.lower()) is None:
        return False
    return all(word in WEATHER_WORDS or word in WEATHER_NOISE for word in said)


def the_place_and_month(text):
    """The place and the month a line names, as the knowledge base spells them, or (None, None).

    Only the places it has climate figures for are read, so the answer that follows can always
    be given: a place it knows nothing about is left to the hedge it gets today.
    """
    low = " ".join(str(text or "").lower().split())
    if not low:
        return None, None
    from ..knowledge.travel import CITY_CLIMATE  # lazy: the store does not need the facts
    for name in sorted(CITY_CLIMATE, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", low) is None:
            continue
        month = next((word for word in sorted(MONTH_NAMES, key=len, reverse=True)
                      if re.search(r"(?<![a-z])" + word, low)), None)
        return name, month
    return None, None


# The words a line can spend on naming a new period and nothing else: "and in october", "what
# about june", "how about the summer". Anything else it says is a subject of its own.
PERIOD_ONLY = frozenset("""
and or but also so in on at for about during of the a an what whats how when to it that there
weather like is will be gonna going get have we i you they month months next this coming
""".split())

SEASONS = frozenset("spring summer autumn fall winter".split())


def _the_period_in(text):
    """The period a line names, as it is spelled there, or "".

    "may" is a month and also the verb, so the word has to be standing where a period stands:
    after a preposition ("in may"), after "next"/"this", or at the end of the line. A month
    named anywhere else ("i may go to spain") is not a period.
    """
    low = " ".join(str(text or "").lower().split())
    for name in sorted(MONTH_NAMES | SEASONS, key=len, reverse=True):
        for found in re.finditer(r"(?<![a-z])" + name + r"(?![a-z])", low):
            before = low[:found.start()].split()
            after = low[found.end():].strip(" ?!.,")
            if not before or before[-1] in ("in", "next", "this", "the", "early", "late", "mid",
                                            "until", "til", "by", "for", "about", "of", "and"):
                return found.group(0)
            if name not in ("may", "march", "fall") or not after:
                return found.group(0)
    return ""


def _a_period_and_nothing_else(line):
    """True for a line that names a period and nothing else of its own."""
    said = words(line)
    if not _the_period_in(line):
        return False
    return all(word in PERIOD_ONLY or word in MONTH_NAMES or word in SEASONS for word in said)


def the_period_they_ask_about(understood, memory):
    """The question on the table asked again about a new month or season, or None.

    "whats the weather like in rome in may" then "and in october" is the same question about
    October, which the knowledge base has: asked as it came in, the month is the only subject
    and the line gets the storing turn's nod. The old period is swapped for the new one in the
    question the chat is on, so every phrasing of "and in <month>" reaches the same answer, and a
    line that brings anything else ("whats the weather like in october in cornwall") is not this.
    """
    line = str(understood.get("clean") or understood.get("text") or "")
    if not _a_period_and_nothing_else(line):
        return None
    period = _the_period_in(line)
    record = carried_topic(memory, line)
    asked = str((record or {}).get("text") or "")
    was = _the_period_in(asked)
    if was == period:
        return None      # the same period again
    if not was:
        # The question on the table names no period of its own - "whats the weather like" after
        # a trip - so the new period is the one thing missing, and the place comes from the trip
        # the chat is on: "im off to rome next week" / "whats the weather like there" / "and in
        # august" is the Rome figures for August. Only when the answer they have just read was
        # about the weather: "how much does a trip to rome cost" then "and in october" is a
        # question about money, and the climate is not the answer to it.
        if not _the_answer_was_about_the_weather(memory):
            return None
        place = _the_place_the_chat_is_on(line, memory)
        if place is None:
            return None
        return f"what is the weather like in {place} in {period}"
    if ASK_CUE.search(asked.lower()) is None and WEATHER_ASKS.search(asked.lower()) is None:
        return None      # the earlier line did not ask anything to ask again
    return _with_the_period(asked, was, period)


def _the_answer_was_about_the_weather(memory):
    """True when the last thing the bot said was about the weather."""
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "")
        if not said.strip():
            continue
        return bool(WEATHER_WORDS & set(words(said)))
    return False


def _the_place_the_chat_is_on(line, memory):
    """The place the chat is still on, from the trip the person stated, or None.

    The newest line that names a place is the one read, so a trip said later is the trip, and a
    line with no place ends the search: the chat has moved to something the climate cannot
    answer. A trip already taken is not one to give a forecast for.
    """
    mine = " ".join(words(line))
    for said in _the_lines_said(memory):
        if " ".join(words(said)) == mine:
            continue                       # this turn is not the chat it follows on from
        if the_weather_ask({"clean": said, "text": said}):
            continue                       # the same question again: the trip behind it is the trip
        if _a_period_and_nothing_else(said):
            continue                       # yesterday's "and in october": still the same chat
        if A_TRIP_TAKEN.search(" ".join(str(said).lower().split())):
            return None                    # the figures are the right climate and the wrong tense
        place, _month = the_place_and_month(said)
        if place is not None:
            return place
        return None                        # no place in the newest thing said: nothing to fill in
    return None


def _with_the_period(asked, was, now):
    """The earlier question with its period swapped for the one this line names."""
    out = re.sub(r"(?<![a-z])" + re.escape(was) + r"(?![a-z])", now, asked, count=1)
    return " ".join(out.lower().split())


# A follow-up that names another meal is the same question about the meal it names: a dairy-free
# breakfast and then "and for lunch" was answered with the breakfast list again. Anything else the
# line says is a subject of its own, so "and for lunch i want soup" is not this.
MEAL_NAMES = frozenset("""breakfast lunch dinner supper brunch""".split())
MEAL_ONLY = frozenset("""
a an about also and anything at but can could do does eat for have how i instead is it make me
or should so something that the then there to we what whats will would you
""".split())


# A bare line that opens with one of these is a follow-up on the turn before it: "and for lunch",
# "what about dinner". A line that asks its own question ("do i have to eat breakfast") is not.
OPENS_A_FOLLOW_UP = re.compile(r"^(?:and|also|then|or|so|what about|how about|whats|same)\b", re.I)


def _the_meal_in(text):
    """The meal a line names, or ""."""
    low = " ".join(str(text or "").lower().split())
    for name in sorted(MEAL_NAMES, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + name + r"(?![a-z])", low):
            return name
    return ""


def _a_meal_and_nothing_else(line):
    """True for a line that names a meal and nothing else of its own."""
    said = words(line)
    if not _the_meal_in(line):
        return False
    return all(word in MEAL_ONLY or word in MEAL_NAMES for word in said)


def the_meal_they_ask_about(understood, memory):
    """The question on the table asked again about another meal, or None.

    "what can i have for breakfast" then "and for lunch" is the same question about lunch, which
    the knowledge base answers; asked as it came in, the line names no subject of its own and
    comes back as the breakfast answer again. The meal is swapped in the question the chat is on,
    so "and for lunch", "what about dinner" and "and tea instead" all reach their own answer.
    """
    line = str(understood.get("clean") or understood.get("text") or "")
    if not _a_meal_and_nothing_else(line):
        return None
    meal = _the_meal_in(line)
    record = carried_topic(memory, line)
    asked = str((record or {}).get("text") or "")
    was = _the_meal_in(asked)
    if not was:
        # The chat is not on a meal, so there is no question to swap the meal into. A line that
        # opens a follow-up ("how do i boil an egg" then "and for lunch") is still asking about
        # the meal it names; a line that asks its own question ("do i have to eat breakfast") is
        # not this at all.
        if not OPENS_A_FOLLOW_UP.match(line):
            return None
        return "what can i have for " + meal
    if was == meal:
        return None      # the same meal again is the answer just given
    if ASK_CUE.search(asked.lower()) is None:
        return None      # the earlier line did not ask anything to ask again
    return _with_the_meal(asked, was, meal)


def meal_follow_up(understood, memory):
    """The line read again with the meal it names in it, as a reading, or None.

    The reading is built here rather than in the caller so the answer modules can use it before
    they search the earlier line: searched as it stands, "and for lunch" reaches the answer about
    the meal before it.
    """
    meal = the_meal_they_ask_about(understood, memory)
    if not meal:
        return None
    reading = dict(understood)
    reading["clean"] = meal
    reading["words"] = words(meal)
    if "norm_text" in reading:
        reading["norm_text"] = meal
    return reading


def _with_the_meal(asked, was, now):
    """The earlier question with its meal swapped for the one this line names."""
    out = re.sub(r"(?<![a-z])" + re.escape(was) + r"(?![a-z])", now, asked, count=1)
    return " ".join(out.lower().split())


def the_weather_of_the_trip(understood, memory):
    """The trip's climate question, when a weather follow-up can be answered with it, or None.

    "what's the weather like" and "how hot will it be" after "we are going to lisbon in june"
    are the Lisbon-in-June averages, which the knowledge base has; asked on their own they get
    the meaning of the word weather. The line is asked again with the trip's place and month in
    it, so every phrasing of the same question gets the same answer, and a line that names its
    own place is left alone (it already reaches the entry).
    """
    if not the_weather_ask(understood):
        return None
    line = str(understood.get("clean") or understood.get("text") or "")
    place, month = the_place_and_month(line)
    if place is not None:
        return None      # the line says where: whatever it gets today stands
    if NOW_AND_HERE.search(line.lower()):
        return None      # here and now, not the trip: the hedge is the honest answer
    place, month = the_place_and_month(_the_trip_said(line, memory))
    if place is None or month is None:
        return None      # no month, no figures: the hedge is the honest answer
    return f"what is the weather like in {place} in {month}"


# A trip that has already happened: "we went to lisbon in june", "we were in rome in may".
A_TRIP_TAKEN = re.compile(
    r"\b(?:(?:i|we|he|she|they)\s+(?:went|were|was|been|had|did|stayed|visited|flew|drove)"
    r"|got\s+back|came\s+back|back\s+from|just\s+back|returned)\b", re.I)


def _the_trip_said(line, memory):
    """The trip the chat is on, when it names a place and a month, or "".

    Only the turn the chat is actually on is read back. A weather ask is the same question asked
    again ("whats the weather like", then "will we need a coat"), so those are skipped; the first
    turn that is about something else is what the chat is on, and the figures come from it or not
    at all. A trip the chat has left - "we are going to lisbon in june", then "my boiler is
    broken" - is not the trip, and its climate is not an answer to a question about the boiler.
    """
    mine = " ".join(words(line))
    for said in _the_lines_said(memory):
        if " ".join(words(said)) == mine:
            continue                      # this turn is not the chat it is following on from
        if the_weather_ask({"clean": said, "text": said}):
            continue                      # the same question again: the ask behind it is the trip
        place, month = the_place_and_month(said)
        if place is None or month is None:
            return ""                     # the chat is on something with no figures: leave it be
        if A_TRIP_TAKEN.search(" ".join(said.lower().split())):
            # "we went to lisbon in june", "we got back from rome in may" are trips behind them:
            # the figures are the right climate and the wrong tense, and the question they are
            # followed by is what it was like, not what to pack.
            return ""
        return said
    return ""


def _the_lines_said(memory):
    """The lines the person has said, newest first."""
    if not isinstance(memory, dict):
        return []
    out = []
    for turn in reversed(memory.get("turns") or []):
        said = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        if said.strip():
            out.append(said)
    return out


# The pronouns that stand for the thing itself, not for a person: "what should I feed it".
THING_ITSELF = re.compile(r"\b(it|its|them|they)\b", re.I)
# Some "it"s are not pointing at anything: they are part of the phrase itself, and filling one
# writes a line nobody said. "how do i make it up to my mum" became "how do i make my mums
# birthday up to my mum" once the store had the birthday, and the party plan and the tray bake
# both took a turn about putting something right. Read before the fill, so the phrases stay whole.
IT_IS_PART_OF_THE_PHRASE = (
    "make it up", "making it up", "put it right", "make it right", "put it behind",
    "take it out on", "took it out on", "let it go", "let it lie", "get it wrong",
    "got it wrong", "getting it wrong", "said it wrong", "put it down to", "have it out with")
BABY_OF = {"puppy": "dog", "kitten": "cat"}
# An ask about what the thing costs is about getting one, not about the one they have: filling
# the pronoun turned the boiler's "how much will it cost" into the cat's feeding amount, because
# the entry for how much to feed a cat is also keyed on "much".
WHAT_IT_COSTS = re.compile(r"\b(?:cost|costs|costing|price|prices|worth|expensive|cheap|cheaper|"
                           r"pay|paid|fee|fees|insurance|bill|bills|money|afford)\b", re.I)
# "is it worth fixing" asks for a decision about the thing, not a price for it, and the readers
# that decide already answer it well: filling the pronoun there answered a washing machine with
# the cost of a wash, a laptop for uni with the repair rule, and an energy tariff with garage
# labour.
WORTH_DECIDING = re.compile(
    r"\b(?:is|would|will)\s+(?:it|that|this|they)\s+"
    r"(?:worth|better|best|cheaper|cheapest|smarter)\b[^?]*"
    r"\b(?:fix|repair|replac|restor|servic|renew|upgrad|pay|spend|buy"
    r"|keep|sell|insur|invest|switch)\w*", re.I)


# "is it worth getting a dog", "is it worth having a smart meter": the pronoun is where the line's
# own subject goes - worth, then a verb of having - so it stands for nothing the chat has said. A
# pronoun that points looks different: "is it worth paying more" after a laptop is that laptop,
# and "is it safe to drive" after a brake fault is that car.
PLACEHOLDER_PRONOUN = re.compile(
    r"\bworth\s+(?:getting|having|buying)|\bworth\s+(?:get|have|buy)\b", re.IGNORECASE)
# ... unless the line is about a new one *of the thing in hand*: "my boiler needs its yearly
# service" and then "is it worth getting a new one instead" is the boiler, and reading the worth
# as a fresh subject left the person with a shrug where the boiler rows had an answer.
A_NEW_ONE = re.compile(
    r"\b(?:new|another|bigger|smaller|different|better|second|cheaper|proper)\s+one\b"
    r"|\bone\s+instead\b|\bone\s+of\s+(?:those|them)\b", re.IGNORECASE)


def a_placeholder_pronoun(line):
    """True when the pronoun in the line is a hole for a subject of its own, not a pointer."""
    text = str(line or "")
    return bool(PLACEHOLDER_PRONOUN.search(text) and not A_NEW_ONE.search(text))


def the_ask_about_the_thing_it_points_at(understood, memory):
    """The reading with the thing a pronoun points at written in front of it, or None.

    "where should i keep it" after "im trying to save money" names nothing the knowledge base
    can answer, and the answer above it is about tracking spending rather than about where the
    money goes, so the turn fell to "that was the whole of my answer on it" with the savings
    entry one word away. The reading has already resolved the pronoun ("money"), so the ask is
    written the way the knowledge base keys it: "where should i keep my money".

    A last resort, asked only where every other reader has passed: a follow-up that a sentence
    of the answer above can answer ("what should i get for it", "how long does it need") is
    answered there and never reaches this, so the thing the store holds cannot take that
    turn. Only a thing, never a person, and never a word of the asking itself.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = " ".join(str(understood.get("clean") or understood.get("text") or "").split())
    if not line or not THING_ITSELF.search(line):
        return None
    if any(phrase in line.lower() for phrase in PROCEED):
        return None  # "what should i do about it" carries on from the answer
    if any(phrase in line.lower() for phrase in IT_IS_PART_OF_THE_PHRASE):
        return None  # the "it" is the phrase's own, not a pointer at a thing
    if WHAT_IT_COSTS.search(line):
        return None  # what it costs is about getting one, not about the one they have
    ref = understood.get("ref") if isinstance(understood.get("ref"), dict) else None
    # Only a thing. A conversation that named no thing at all resolves its pronoun to the label
    # of the topic it was read as ("language-and-writing"), and a label is not a noun phrase
    # anybody said: written into the ask it gave "how long will my language and writing take"
    # after "im trying to write a book", which the language-hours row answered with the Spanish
    # figure. `references._target` says the same in its own words - a caller that needs a noun
    # can tell the two apart - and this is that caller.
    if not isinstance(ref, dict) or ref.get("kind") != "thing":
        return None
    thing = ref.get("it") or ref.get("that")
    if not isinstance(thing, str):
        return None
    thing = " ".join(thing.split())
    if not thing or len(thing.split()) > 3 or thing in ("it", "that", "them", "they", "you", "me"):
        return None
    if thing in line.lower():
        return None  # the thing is already in the line, so nothing is pointed at
    filled = " ".join(THING_ITSELF.sub("my " + thing, line, count=1).split())
    reading = dict(understood)
    reading["clean"] = filled
    reading["words"] = words(filled)
    return reading


# The pronouns a line uses in place of a thing, and the slot the reading keeps it in.
POINTING_WORDS = ("it", "they", "them", "that", "this", "he", "she")


def the_pronoun_written_as_what_it_stands_for(understood, memory):
    """This line with its pronoun replaced by the thing it stands for, or None.

    "im thinking of getting a dog" / "what about a cat instead" / "how long can they be left
    alone" is a question about the cat, and the understanding engine says so - the pronoun's
    slot holds "cat" - but the line itself names no thing, so no entry answered it and the
    person got a search hedge while the cat-alone row was one entry away. Carrying the topic's
    words *after* the line ("how long can they be left alone cat instead") reaches nothing: a
    subject belongs where the pronoun was, not a word on the end.

    Every pointer the reading has filled is tried in the slot it stands in, and the entry that
    comes back has to be keyed on the thing itself, so a fill that lands on an answer about
    something else is left alone. A line that already reaches an entry keeps it: the fill is
    only for a follow-up that names nothing the knowledge base knows.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = " ".join(str(understood.get("clean") or understood.get("text") or "").split())
    if not line:
        return None
    ref = understood.get("ref") if isinstance(understood.get("ref"), dict) else None
    if not isinstance(ref, dict):
        return None
    if understood.get("kind") != "question":
        # A line that reports what somebody does ("she asks where it is") is not a question with
        # a hole in it: filling it wrote "she asks where a nan is" and the line reached the
        # borrowing-from-family entry, so a chat about presents was answered with a loan.
        return None
    if any(phrase in line.lower() for phrase in PROCEED):
        return None  # "what should i do about it" carries on from the answer
    if any(phrase in line.lower() for phrase in IT_IS_PART_OF_THE_PHRASE):
        return None  # the pronoun is the phrase's own, not a pointer at a thing
    if _entry(line) is not None:
        return None  # the line reaches an entry as it stands, so nothing is missing
    last = memory.get("last_answer") if isinstance(memory.get("last_answer"), dict) else {}
    record = carried_topic(memory, line)
    topic_entry = _entry(str((record or {}).get("text") or "")) if record else None
    topic_domain = getattr(topic_entry, "domain", None) if topic_entry is not None else None
    for word in POINTING_WORDS:
        thing = ref.get(word)
        if not isinstance(thing, str):
            continue
        thing = " ".join(thing.split())
        if not thing or thing.lower() in ("it", "that", "them", "they", "you", "me", "there"):
            continue
        if re.search(r"\b%s\b" % re.escape(thing.lower()), line.lower()):
            continue  # the thing is already in the line, so the pronoun is not standing for it
        if not re.search(r"\b%s\b" % word, line, re.IGNORECASE):
            continue
        for phrase in _the_thing_with_a_determiner(thing):
            filled = re.sub(r"\b%s\b" % word, phrase, line, count=1, flags=re.IGNORECASE)
            filled = " ".join(filled.lower().split())
            entry = _entry(filled)
            if entry is None:
                continue
            if not _the_entry_is_about_the_thing(entry, thing.split()[-1].lower()):
                continue
            if not _the_entry_answers_the_ask(entry, filled):
                continue
            if topic_domain and getattr(entry, "domain", None) != topic_domain:
                continue  # a fill that leaves the thing the chat is about is a fill into another
            if last.get("id") and entry.id == last.get("id"):
                continue  # the fill lands back on the answer they already have
            reading = dict(understood)
            reading["clean"] = filled
            reading["words"] = words(filled)
            if "norm_text" in reading:
                reading["norm_text"] = filled
            return reading
    return None


# A noun written into a sentence needs whatever it takes to sit there: "how long can a cat be
# left alone" is the line a person would say, and the bare "cat" reaches the same entry only by
# luck. A name takes none ("how long can Fish be left alone").
WITHOUT_A_DETERMINER = frozenset("""
    it they them that this he she i you we me my your our their his her its
    a an the some any no every each
""".split())


def _the_thing_with_a_determiner(thing):
    """The ways this thing can be written into a line, the plain one included."""
    ways = []
    first = thing.split()[0].lower()
    if first not in WITHOUT_A_DETERMINER:
        article = "an" if first[:1] in "aeiou" else "a"
        ways.extend([article + " " + thing, "the " + thing, "my " + thing])
    ways.append(thing)
    return ways


def the_thing_it_is(understood, memory):
    """A follow-up ask with a pronoun in it, read with the thing the store holds, or None.

    "what should I feed it" after "my cat is called Fish" names nothing the knowledge base can
    answer: carrying the topic's words gives "what should i feed it cat", which reaches no
    entry, so the turn fell to a search hedge with the answer one entry away. The store knows
    what the thing is, so the pronoun takes its place: "what should I feed my cat".

    Only where the filled ask reaches an entry. A pointer is worth filling when there is
    something at the other end, and a wrong subject is worse than none, so every pointer that
    does not land exactly on an entry is left for the reply that can answer it honestly.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line or not ASK_CUE.search(line.lower()) or not THING_ITSELF.search(line):
        return None
    if any(phrase in line.lower() for phrase in PROCEED):
        # "what should I do about it" carries on from the answer, not from the thing.
        return None
    if WORTH_DECIDING.search(line) or a_placeholder_pronoun(line):
        return None
    if not WHAT_IT_COSTS.search(line):
        # Every other ask keeps the reader it had: the animal named on the line before, and
        # nothing guessed out of the chat's subject.
        thing = the_pet_the_line_before_named(memory)
        if not thing:
            return None
        filled = THING_ITSELF.sub(thing, line, count=1)
        if _entry(filled) is None:
            return None
        reading = dict(understood)
        reading["clean"] = " ".join(filled.lower().split())
        reading["words"] = words(reading["clean"])
        return reading
    if _entry(line) is not None:
        # The ask reaches an entry as it stands, so the pronoun is not the thing that is missing:
        # "how much will it cost to fix" is the price of the repair, not the price of whatever
        # the chat is on, and filling the pronoun in it answered a MOT with the MOT fee.
        return None
    last = memory.get("last_answer") if isinstance(memory, dict) else None
    last_id = last.get("id") if isinstance(last, dict) else None
    for thing, word in _the_things_the_pronoun_stands_for(memory, line):
        filled = THING_ITSELF.sub(thing, line, count=1)
        entry = _entry(filled)
        if entry is None:
            continue
        if not _the_entry_is_about_the_thing(entry, word):
            continue
        if not _the_entry_answers_the_ask(entry, filled):
            continue
        if last_id and entry.id == last_id:
            # The fill lands back on the answer they already have, so the pronoun is not the
            # thing that is missing: "my garden is overgrown" then "is it expensive to sort
            # out" is a new ask, and the answer they have, said again with "Same answer, and it
            # covers this" in front of it, is not the reply to it.
            continue
        reading = dict(understood)
        reading["clean"] = " ".join(filled.lower().split())
        reading["words"] = words(reading["clean"])
        return reading
    return None


SOMETHING_IS_BROKEN = re.compile(
    r"\b(?:broke|broken|not working|stopped working|wont work|won't work|faulty|leaking|"
    r"isnt working|isn't working|packed in|given up)\b", re.I)


def _the_things_the_pronoun_stands_for(memory, line):
    """What the pronoun in this line can stand for, the likeliest first, as (phrase, word).

    The animal named on the line before comes first, because that is what "it" means in a pet
    chat ("how often should I walk it") and it is the word they used. The chat's own subject
    comes next, because a pronoun in a chat that is not about an animal points at the subject:
    "im going to lisbon in may" then "is it expensive" is a question about Lisbon, and with only
    the animal read here the store had nothing to fill and the turn fell to a search hedge
    while "is lisbon expensive" was answered one entry away.
    """
    out = []
    pet = the_pet_the_line_before_named(memory)
    if pet:
        out.append((pet, pet.split()[-1]))
    record = carried_topic(memory, line)
    text = " ".join(str((record or {}).get("text") or "").lower().split())
    if not text or SOMETHING_IS_BROKEN.search(text):
        # A broken thing's "is it expensive" is a question about the repair, not about the thing:
        # "my washing machine is broken" then "is it expensive" is answered by the checks worth
        # doing before anyone is paid, and filling the pronoun took that turn to the cost of a
        # wash at 30C. The thing a chat is on is put in a pronoun's place when the chat is about
        # getting one or going somewhere, and a fault is left to the answer that knows it.
        return out
    said = " " + text
    mine = _what_they_called_theirs(said)
    if mine:
        # What the chat calls theirs is what the pronoun stands for, and nothing else is tried:
        # "my laptop has started making a loud fan noise" then "is it worth repairing or should i
        # replace it" is about the laptop, and filling the noise's "fan" answered a laptop
        # question with the cost of running a room fan.
        return out + [pair for pair in mine if pair not in out]
    for word in key_subject(text, memory):
        if word in words(line):
            continue                      # the line names it already, so nothing to fill
        phrase = word
        if " my " + word in said or text.startswith("my " + word):
            phrase = "my " + word
        elif " the " + word in said or text.startswith("the " + word):
            phrase = "the " + word
        if (phrase, word) not in out:
            out.append((phrase, word))
    return out


THEIR_OWN = re.compile(r"\b(my|the)\s+([a-z']+)", re.I)
# A word after "my" that is not a thing of theirs: a person, a part of the day, a feeling.
NOT_THEIR_OWN = frozenset("""
own self way turn go mind head opinion fault point lot bit time while moment
life day week month year today house home place
""".split())
_SMALL = frozenset("""
a an the and or but of to in on at for with is was are were be been has have had got
""".split())


def _what_they_called_theirs(text):
    """The phrases the chat calls theirs: [("my laptop", "laptop"), ("the boiler", "boiler")].

    Only a thing named as belonging to the person is read here, so a pronoun in a cost ask fills
    with what they have and not with any noun the line happened to hold. One word only, because
    "my car failed" is a thing and a verb, and "my car" is the thing.
    """
    out = []
    for lead, word in THEIR_OWN.findall(text):
        if len(word) < 3 or word in _SMALL or word in NOT_THEIR_OWN:
            continue
        pair = (lead.lower() + " " + word, word)
        if pair not in out:
            out.append(pair)
    return out[:3]


# An entry whose id says what it answers ("running-cost", "car-running-costs") is the answer to
# a question about *using* the thing, so it is only the answer when the ask names that. Filling
# the pronoun in "my dishwasher is not draining" / "is it expensive" reached the running-cost key,
# which holds sixty appliances, and answered the cost of a cycle where the person asked what a
# repair costs; a car making a noise got a yearly budget.
NAMES_THE_RUNNING = re.compile(
    r"\b(?:run|runs|running|use|uses|using|used|electricity|electric|energy|power|cycle|cycles"
    r"|hour|hours|kwh|gas|water|heating)\b", re.I)


def _the_entry_answers_the_ask(entry, line):
    """Whether what the entry is about is what the ask asked ("is it expensive to run")."""
    if str(getattr(entry, "id", "")).endswith("running-cost") or str(
            getattr(entry, "id", "")).endswith("running-costs"):
        return bool(NAMES_THE_RUNNING.search(line))
    return True


def _the_entry_is_about_the_thing(entry, word):
    """Whether the entry the filled ask landed on is keyed on the thing itself.

    An ask about what something costs used to be left alone here, because filling the pronoun
    in the boiler's "how much will it cost" reached the cat's feeding entry - both keys hold
    "much". The entry itself is the test: the trip budget entry's key names Lisbon, so
    "is lisbon expensive" is an answer about Lisbon, and a key that does not name the thing is
    an answer about something else.
    """
    return any(word in group for group in entry.key)


# A yes/no about what the thing in hand is like, asked with only a pronoun standing in for it:
# "is it expensive" after "i'm going to rome in may", "is that expensive" after a bike they are
# thinking of buying. The knowledge base has no entry for the pronoun and does have one for the
# filled ask ("is rome expensive" is the cost table's Rome row), so the line was answered with
# whatever answer the chat already had - "Same as before: In Rome: the Colosseum..." - or with a
# shrug ("Alright then - good luck with it.").
WHAT_IT_IS_LIKE = frozenset("""
    expensive cheap pricey costly affordable far near close long short quick slow fast easy hard
    difficult simple complicated warm hot cold wet dry busy crowded quiet noisy loud heavy light
    big small tall serious dangerous risky safe legal allowed normal common free fresh healthy
    filling fattening spicy sweet salty sour stale raw ready open tidy good bad better worse fine
""".split())
# The pronoun that stands for the thing itself: "is it expensive", "are they any good", "is that
# one safe". A pronoun about a person ("is she expensive") is not this turn, and `WHO` below is
# where a chat about somebody else is kept out.
WHAT_STANDS_IN = re.compile(r"\b(?:it|its|they|them|that|this|those|these)\b", re.I)
STANDS_IN = frozenset("it its they them that this those these".split())
# The words that ask what something costs, whatever else the line says: they are asked as a money
# question, which is how the knowledge base's price rows are keyed.
MONEY = frozenset("""
    expensive cheap cheaper pricey costly affordable dear reasonable spend afford price cost costs
""".split())
# The line has to be the yes/no itself, not a longer question that happens to hold a pronoun:
# "is it expensive in june" names a month of its own and is left alone.
YES_NO = re.compile(
    r"^\s*(?:(?:and|but|so|ok|okay|then|also|now|hmm|oh)\s+|what\s+about\s+|how\s+about\s+)?"
    r"(?:is|are|was|were|will|would|do|does|did|should|can|could|any)\b", re.I)


# How a prognosis is asked of the thing in hand, word for word. The pronoun asks it and the
# words after it say what is to become of the thing rather than what it is like: "will it go away
# on its own" after a cough, "will it clear up", "will that heal", "will it last". The knowledge
# base has no row for "will cough get better" and does have one for "how long does a cough last",
# so the ask is written out in the wording that reaches the row about how long the thing goes on,
# which is the answer the person is after. The value is the phrase that row is keyed on, so
# "get" and "improve" are asked as "get better" whether the line says better or not.
PROGNOSIS = {
    "go": "go away", "goes": "go away", "going": "go away", "gone": "go away",
    "away": "go away", "clear": "clear up", "clears": "clear up", "clearing": "clear up",
    "heal": "heal", "heals": "heal", "healing": "heal", "settle": "settle",
    "settles": "settle", "last": "last", "lasts": "last", "lasting": "last",
    "get": "get better", "gets": "get better", "getting": "get better",
    "improve": "get better", "improves": "get better", "pass": "pass",
    "passes": "pass", "fade": "fade", "fades": "fade", "down": "go down",
}


def the_prognosis_the_line_asks(understood, memory):
    """A bare "will it get better / go away / clear up / heal / last", read as the prognosis of
    the thing the chat is on, or None.

    A person who has just said they have a cough asks the question a friend answers without being
    asked twice: will it go away on its own. Nothing in the line names the cough but the pronoun,
    so the reading reached no entry, and the turn was a search hedge - "That's beyond what I know
    well, sorry" - with the row that says most coughs settle in two to three weeks one lookup
    away. The same held for a cold, a verruca, a burn and a sprain, which is the shape of the ask
    rather than any one topic: the pronoun plus a word of becoming.

    Three things decide whether the row may be handed over, because the prognosis of whatever the
    pronoun last pointed at is a wrong answer, and worse than the honest hedge:

    * the thing is one word. The ask is built out of what the store keeps as the thing, and the
      store keeps a phrase when the person described something: "i planted tomatoes in pots" is
      kept as "planted tomatoe pot", and "the warranty runs out in march" as "warranty run march".
      Asked as a question, those reached the billiards card ("Cue games are won with the cue
      ball, not the pot") and the running plan ("Three runs a week is plenty to start"). A
      condition a prognosis is asked about is named in a word - a cough, a cold, a bruise.
    * the row is keyed on how long the thing goes on. The ask is written so it reaches that row,
      and the row it reaches is only the answer when its own key says so: the general card about
      the thing says what the card the person has just read says, which is how "will it go away"
      about a verruca came out as a third telling of one fact.
    * it is not the answer already on the screen.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line or not YES_NO.search(line) or not WHAT_STANDS_IN.search(line):
        return None
    said = words(line)
    outcomes = [PROGNOSIS[word] for word in said if word in PROGNOSIS]
    if not outcomes:
        return None
    # A line that names something of its own has its own subject, so it is not the pronoun's
    # to take: "will the dog get better" is the dog's question, asked in full.
    left = [word for word in said
            if word not in STOPWORDS and word not in STANDS_IN and word not in PROGNOSIS
            and word not in WHAT_IT_IS_LIKE]
    if left:
        return None
    if isinstance(memory.get("person"), dict) and memory.get("person"):
        return None  # the chat is about somebody, and their pronouns are not the thing's
    thing = subject(memory)
    named = words(thing) if thing else []
    if len(named) != 1 or set(named) & WHO:
        return None
    word = named[0]
    already = _entry(topic_text(memory))
    # The words the person used, then the plainest two ways the row is kept ("how long does it
    # last"): "will it go away" about a verruca lands on the pharmacy treatment, which is the
    # answer on the screen, and the row about how long they go on is the one that answers.
    for outcome in dict.fromkeys(outcomes + ["last", "get better"]):
        for written in _the_thing_as_a_question_names_it(named):
            if outcome == "last":
                ask = "how long does " + written + " last"
            else:
                ask = "how long does " + written + " take to " + outcome
            entry = _entry(ask)
            if entry is None:
                continue
            if not _the_entry_is_about_the_thing(entry, word):
                continue
            if not _keyed_on_how_long(entry):
                continue
            if already is not None and entry.key == already.key:
                continue  # the answer on the screen already is this answer
            reading = dict(understood)
            reading["clean"] = " ".join(ask.split())
            reading["words"] = words(reading["clean"])
            if "norm_text" in reading:
                reading["norm_text"] = reading["clean"]
            return reading
    return None


# The words an entry's key is written in when the entry answers how long the thing goes on. The
# ask is written in the same words, so this is the row answering the question that was asked
# rather than a card about the thing: "how long does a cough last" is keyed on weeks and months,
# and the general warts card is keyed on "what", "how" and "treat".
HOW_LONG_KEY = frozenset([
    "how long", "last", "lasts", "lasting", "duration",
    "week", "weeks", "month", "months", "day", "days", "long",
])


def _keyed_on_how_long(entry):
    """Whether the entry the prognosis ask reached is the row about how long the thing goes on."""
    return any(phrase in group for group in getattr(entry, "key", ())
               for phrase in HOW_LONG_KEY)


def _the_thing_as_a_question_names_it(named):
    """The thing as a question of its own would name it: as it was said, then with an article.

    "i have a cough" puts "cough" in the store with no article, and the row is keyed on "how long
    does a cough last": both are tried, the words they used first.
    """
    whole = " ".join(named)
    if named[0] in ("my", "a", "an", "the", "his", "her", "our", "their", "your"):
        return [whole]
    return [whole, "a " + whole, "the " + whole]


def the_property_of_the_thing(understood, memory):
    """A bare yes/no about what the thing in hand is like, read with that thing in it, or None.

    "is it expensive" after a trip to Rome is the cost question about Rome: the store knows the
    chat is about Rome, and the knowledge base answers "is rome expensive" with the price row.
    Filling the pronoun is what turns a follow-up the bot could only repeat itself over into the
    question the person asked.

    Only where the filled ask reaches a different entry than the answer already given: when the
    pronoun's place is filled and the same entry comes back, the answer would be the one they
    have just read, which is what this is here to stop. A wrong subject is worse than none, so
    every fill that does not land on another entry is left to the reply that can answer honestly.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line or not YES_NO.search(line) or not WHAT_STANDS_IN.search(line):
        return None
    said = set(words(line))
    if not said & WHAT_IT_IS_LIKE:
        return None
    # Everything the line says besides a property word and the pronoun it points with: a line that
    # names something of its own has its own subject, so it is not the pronoun's to take.
    left = [w for w in words(line)
            if w not in WHAT_IT_IS_LIKE and w not in STOPWORDS and w not in STANDS_IN]
    if left:
        return None
    if isinstance(memory.get("person"), dict) and memory.get("person"):
        return None  # the chat is about somebody, and their pronouns are not the thing's
    thing = subject(memory)
    if not thing or set(words(thing)) & WHO:
        return None
    item = None
    already = None
    looked = 0
    fallback = None
    money = bool(set(words(line)) & MONEY)
    for candidate in _fills_from_the_things(line, understood, thing, memory):
        looked += 1
        if looked > LIKE_LOOKUPS:
            # A knowledge lookup is the expensive part of a turn, and four is already more than
            # a line this short is worth: the thing the chat is about, then the words of its key.
            break
        found = _entry(candidate)
        if found is None:
            continue
        if already is None:
            already = _entry(topic_text(memory))
        if already is not None and found.key == already.key:
            continue  # the answer in hand already is this answer
        if money and not (_key_words_of(found) & MONEY):
            # "my car failed its mot on a broken spring" / "is that expensive" reaches the row
            # about what a failed MOT means, which is not what they asked: the money question is
            # answered by the row that is keyed on money (the MOT fee, the fitted price), so the
            # first row that only mentions the thing is kept as a last resort and the search goes
            # on past it.
            if fallback is None:
                fallback = (candidate, found)
            continue
        filled, item = candidate, found
        break
    if item is None and fallback is not None:
        filled, item = fallback
    if item is None:
        return None
    reading = dict(understood)
    reading["clean"] = " ".join(filled.lower().split())
    reading["words"] = words(reading["clean"])
    if "norm_text" in reading:
        reading["norm_text"] = reading["clean"]
    return reading


LIKE_LOOKUPS = 4


# A line that asks where the limit is and names nothing itself: "how much is too much", "how much
# is too much a day", "is that too much". The thing is the one the chat is on, and the knowledge
# base keeps the limit row keyed to that thing ("how much coffee is too much" is the caffeine row),
# so the ask is written out with the thing in it.
LIMIT_ASK = re.compile(
    r"\bhow (?:much|many)\b[^?.!]{0,24}?\btoo (?:much|many)\b|"
    r"\b(?:is|are|was) (?:it|that|this|they|these) too (?:much|many)\b", re.I)
# The words a limit ask may be made of and still name nothing of its own. "how much is too much a
# day" is the same ask about the same thing; "how much coffee is too much" names the coffee itself
# and is answered by the line alone, so it is not this reader's to widen.
THE_LIMIT_ITSELF = frozenset("""how much many is are was it that this they these too day days week
    weeks time of should shall i we you a an the have be can per""".split())
# The ask as the limit row is keyed: the thing first, and the words of its key beside it, so a
# thing said with its doing ("drink coffee") still reaches "how much coffee is too much".
# The last of them is the row's own name for the ask ("coffee limit"): a row about caffeine for
# babies now answers "how much coffee is too much" and "how much caffeine is too much" for anyone
# who asks, so the written-out ask alone no longer lands on the adult's limit. It is only taken
# when the row it reaches is keyed to the limit itself, so a card that says nothing about a limit
# cannot be reached this way.
THE_LIMIT = ("how much {thing} is too much", "how much {thing} a day is too much",
             "{thing} limit")


def the_limit_of_the_thing(understood, memory):
    """A bare "how much is too much" read with the thing the chat is on in it, or None.

    "i drink a lot of coffee" then "how much is too much" was answered "That's beyond what I know
    well, sorry. Searching for it will turn up better sources" - while the knowledge base has the
    caffeine row, keyed to exactly this ask once the coffee is in it. The person said no more and
    no less than "the coffee we are talking about", so the reading is the same question written
    out, and it is only taken when it lands on a row keyed to the limit words.

    Only a line that names nothing of its own is widened: "how much coffee is too much" is
    answered by the line itself, and a limit about somebody else ("how much should he have") is a
    different question and is left alone. The row it lands on has to be keyed to the limit its own
    self ("limit", "safe"), not merely to the words "too much": "i pay 45 a month for my phone and
    i barely use it" / "is that too much" is a judgement on a bill, and the row it reached there
    was the one about cutting the bill, whose paragraph answers a question nobody asked.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict) or not memory:
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line or not LIMIT_ASK.search(line):
        return None
    if [word for word in words(line) if word not in THE_LIMIT_ITSELF and word not in STOPWORDS]:
        return None  # the line names its own thing, so the thing in hand is not what it asks about
    if isinstance(memory.get("person"), dict) and memory.get("person"):
        return None  # the chat is about somebody, and their limit is not theirs alone to guess at
    thing = subject(memory)
    if not thing or set(words(thing)) & WHO:
        return None
    already = _entry(topic_text(memory))
    seen = set()
    for candidate in _the_limit_written_out(line, thing, memory):
        if candidate in seen:
            continue
        seen.add(candidate)
        if len(seen) > LIKE_LOOKUPS:
            break
        found = _entry(candidate)
        if found is None:
            continue
        keyed = _key_words_of(found)
        if not (keyed & {"limit", "limits", "safe"}):
            continue  # not a row about where the limit is
        if already is not None and found.key == already.key:
            continue  # the answer in hand already is this answer
        reading = dict(understood)
        reading["clean"] = candidate
        reading["words"] = words(candidate)
        if "norm_text" in reading:
            reading["norm_text"] = candidate
        return reading
    return None


def _the_limit_written_out(line, thing, memory):
    """The ask with the thing in it, the thing's own name before the doing word beside it.

    The store keeps the gist of the line that put the thing in hand there, so "i drink a lot of
    coffee" leaves "drink coffee": the limit row is keyed to the coffee, not to the drinking, and
    a single word of the gist that is not a verb is the thing's own name.
    """
    whole = " ".join(str(thing or "").split())
    named = [word for word in whole.split() if not _a_doing_word(word)]
    parts = named + [whole] + [word for word in whole.split() if word not in named]
    try:
        key = key_subject(line, memory)
    except Exception:
        key = []
    for word in key or ():
        if isinstance(word, str) and word.strip() and word.strip() not in parts:
            parts.append(word.strip())
    for one in parts:
        for said in THE_LIMIT:
            yield said.format(thing=one)


def _a_doing_word(word):
    """True for a word that says what is done rather than what it is done to ("drink", "put")."""
    from ..understanding import kinds  # local: the reading's own lists, not a second guess
    return word in kinds.VERB_FORMS or word in kinds.VERBISH


def _fills_from_the_things(line, understood, thing, memory):
    """Every ask the line means, the gist of the thing first and then the words of its key.

    The store's word for the thing in hand is the gist of the line that put it there - "car failed
    mot broken", "washing machine making bang" - and the price entries are keyed on the short
    noun: "how much does a car failed mot broken cost" is nothing, and "how much does mot cost"
    is the MOT fee. `key_subject` is the entry's own subject, so it is the second thing to write
    the ask with.
    """
    seen = set()
    things = [thing]
    try:
        key = key_subject(str(understood.get("clean") or understood.get("text") or ""), memory)
    except Exception:
        key = []
    for word in key or ():
        if isinstance(word, str) and word.strip():
            things.append(word)
    for one in things:
        for ask in _fills(line, one):
            if ask not in seen:
                seen.add(ask)
                yield ask


def _fills(line, thing):
    """The asks the line means, written out with the thing in it, best first.

    "is it expensive" about a banging boiler is the question a person asks before ringing an
    engineer: what will this cost. Written as "is boiler expensive" the price rows come second
    to the running-cost ones, because both rows are keyed on the machine and the dear word; the
    money phrasing reaches the fitted-price row the question is about. So a money word is asked
    as a money question, and everything else keeps the yes/no the person typed.

    Two asks at most: a knowledge lookup is the expensive part of this, and the second wording
    is only there for the rows the first one misses.
    """
    whole = " ".join(str(thing).split())
    said = WHAT_STANDS_IN.sub(whole, line, count=1)
    if set(words(line)) & MONEY:
        return ["how much does " + whole + " cost", "is " + whole + " expensive"]
    return [said]


# A line whose subject is a bare "he" or "she": the pronoun, with the filler that can come
# before it, is the thing to put the animal in place of. A written-out contraction ("he's
# scared of the car", "shes 12") is left alone: the pronoun is not a word of its own there, and
# putting the animal in front of the tense would write "my dog 's scared of the car".
HE_OR_SHE_OPENS = re.compile(
    r"^(?P<lead>(?:and |so |but |well |ok |okay |also )?)(?P<pron>he|she)\b(?!')", re.I)


# A follow-up about the airport that never says the word. "im flying to dublin next week" then
# "how early do i need to be there" reached no entry at all - "there" is not a place - and every
# widening with the topic's own words reached the *destination* entry instead (Dublin's sights),
# so the arrival answer was never given and the turn went to the composer's honest hedge. The
# flight in the topic is the only place "there" can be, so the line is read with the airport in it.
ASKS_HOW_EARLY_THERE = re.compile(
    r"\b(?:how early|how long before|what time (?:should|do|shall|must) i|"
    r"when (?:should|do|shall|must) i)\b", re.I)
A_FLIGHT_IN_THE_TOPIC = re.compile(
    r"\b(?:flight|flights|flying|fly|airport|terminals?|departure|departing|plane|boarding)\b",
    re.I)
THE_AIRPORT = "at the airport"


def the_airport_there_is(understood, memory):
    """A question about how early to be there, in a chat about a flight, read as the airport.

    Only when the line asks about the time and the pronoun is all the place it names: a line that
    names where ("how early should i be at the airport") is already answered from its own words,
    and one that asks about anything else ("how long does it take to get there") is a different
    question. The filled line also has to reach an entry of its own, and not the one in hand, so
    this can only add an answer where the line had none.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line or "there" not in words(line) or not ASKS_HOW_EARLY_THERE.search(line):
        return None
    trip = topic_text(memory)
    if not trip or not A_FLIGHT_IN_THE_TOPIC.search(trip):
        return None
    filled = re.sub(r"\bthere\b", THE_AIRPORT, line, count=1, flags=re.I)
    if filled == line:
        return None
    found = _entry(filled)
    if found is None:
        return None
    already = _entry(trip)
    if already is not None and found.key == already.key:
        return None  # the answer in hand is this answer
    reading = dict(understood)
    reading["clean"] = " ".join(filled.lower().split())
    reading["words"] = words(reading["clean"])
    if "norm_text" in reading:
        reading["norm_text"] = reading["clean"]
    return reading


def the_animal_the_subject_is(understood, memory):
    """A line whose subject is a bare "he"/"she", read with the animal the chat is on, or None.

    "we got a puppy last week" then "he keeps biting the kids" is the puppy biting: the pronoun
    was read as the animal (the understanding engine points it there, because the store holds a
    puppy and no person), but nothing put it back into the question, so the line reached the
    entry for a child who bites at nursery and the person got advice about a toddler. Read with
    the animal it is "my puppy keeps biting the kids", which is the answer they asked for.

    Only when the reading itself points the pronoun at an animal the store holds, and only when
    the filled line lands on an entry that names that animal: a person the chat is on ("my son
    is 8" then "he keeps biting the kids") points the pronoun at the son, so the line is left
    alone, and an animal with nothing to say about the trouble buys nothing either.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line or PET_WORD.search(line):
        return None  # the line names the animal already, so its own reading is the answer
    opens = HE_OR_SHE_OPENS.match(line)
    if opens is None:
        return None
    ref = understood.get("ref") if isinstance(understood.get("ref"), dict) else {}
    who = str(ref.get("he") or ref.get("she") or "")
    if not who or not PET_WORD.search(who):
        # Who "he" is has to be an animal for the store to put one in the line. A person
        # ("my husband is 40") is not this reader's business.
        return None
    thing = the_pet_the_line_before_named(memory) or _called(who)
    filled = opens.group("lead") + thing + " " + line[opens.end():].lstrip()
    item = _entry(filled)
    if item is None:
        return None
    if item is _entry(line):
        return None  # the same answer, so the reading that reached it is already right
    kind = thing.split()[-1].lower().rstrip("s")
    keyed = _key_words_of(item)
    if kind not in keyed and kind not in {stem(word) for word in keyed}:
        return None  # an entry about something other than the animal they keep
    reading = dict(understood)
    reading["clean"] = " ".join(filled.lower().split())
    reading["words"] = words(reading["clean"])
    return reading


# An answer about a child, which is not an answer about the animal in the chat. The words are
# the ones that only make sense for a person: "put the child down", "a teething baby", "back to
# nursery". A pet answer can mention children ("keep him away from the kids") and still be the
# pet's answer, so this is only ever asked together with the wider question below, which wants
# the filled line to reach an entry keyed on the animal.
CHILD_CARE = re.compile(
    r"\b(?:child|children|baby|babies|toddler|toddlers|kid|kids|nursery|nappy|nappies|cot|"
    r"pushchair|highchair|breastfeed\w*|childminder|schoolchild)\b", re.I)


def _the_kind_of_animal(text):
    """The animal a line or an answer names, as the family word: a puppy is a dog."""
    found = set()
    for word in PET_WORD.findall(str(text or "")):
        word = PET_ONE.get(word.lower(), word.lower()).rstrip("s")
        found.add(BABY_OF.get(word, word))
    return found


def answers_about_another_creature(answer, what_the_line_is):
    """True when the answer in hand is about a person or another animal than the one the chat is on.

    "we got a puppy last week" then "he keeps biting the kids" gets the entry for a child who
    bites at nursery: the advice is real and tells the person to put their child down, which is
    nothing to do with a puppy. The same line read with the puppy reaches the puppy's own entry,
    and that one is the answer. The question is only ever asked when the filled line already
    reaches an entry keyed on the animal (`the_animal_the_subject_is`), so what is left to
    decide is whether the answer in hand fits the animal at all.

    A line whose own answer is about the animal in the chat keeps it: after "i cant sleep since
    we got the puppy", "he cries when i leave the room" is answered from the entry for a baby's
    separation anxiety, and that advice - short practice exits, always coming back - is the
    right answer for a puppy too, so it is not thrown away for the one on leaving a dog alone.
    """
    said = " ".join(str(answer or "").split()[:60])
    if not said:
        return False
    if CHILD_CARE.search(said):
        return True
    kind = _the_kind_of_animal(what_the_line_is)
    named = _the_kind_of_animal(said)
    return bool(named) and not (kind & named)


def _called(who):
    """"my dog" from the animal the reading points at, which the reading may already say "my" in."""
    who = " ".join(str(who or "").strip().lower().split())
    if not who:
        return ""
    return who if who.split()[0] in {"my", "our", "the", "a"} else "my " + who




def _the_pet_the_turns_before_named(memory, back=3):
    """"my puppy" when the puppy was named a turn or two before, else "".

    "and the biting" three lines into a puppy chat names no animal at all, so the pronoun rule's
    one turn is too short and the newest animal the person named is what the line is about. Only
    a few turns back: a pet named before a change of subject is not what a bare detail ask means
    now, and a line with an animal of its own never comes here.
    """
    thing = the_pet_the_line_before_named(memory)
    if thing:
        return thing
    turns = memory.get("turns") if isinstance(memory.get("turns"), list) else []
    user = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    lines = []
    for turn in reversed(turns):
        said = turn.get("user") if isinstance(turn, dict) else None
        if isinstance(said, str) and said.strip():
            lines.append(said)
        if len(lines) > back:
            break
    for line in lines[1:back + 1]:
        # The same reading the one-turn rule does, on an earlier line of the chat.
        found = the_pet_the_line_before_named({"turns": [{"user": line}], "user": user})
        if found:
            return found
    return ""


def a_detail_of_the_thing_we_hold(understood, memory):
    """"the chewing" when that is a detail of the animal the store holds, and nothing else.

    The same reading `the_thing_a_detail_belongs_to` makes, without asking which entry the filled
    ask lands on: it says the line is about a detail of the animal they told us about, which is
    what tells an answer already given that the detail is what the line is asking about."""
    return bool(_the_kind_the_line_leaves_out(understood, memory))


def _the_kind_the_line_leaves_out(understood, memory):
    """(line, kind) when the line names a detail and leaves out the animal the store holds."""
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "").strip()
    if not line or not ASK_CUE.search(line.lower()):
        return None
    # The line names the animal itself, so its own reading is the one to answer from.
    if PET_WORD.search(line) or any(phrase in line.lower() for phrase in PROCEED):
        return None
    thing = _the_pet_the_turns_before_named(memory)
    if not thing:
        return None
    kind = thing.split()[-1]
    if kind in words(line):
        return None
    return line, kind


def the_thing_a_detail_belongs_to(understood, memory):
    """The ask read with the kind of thing the store holds, when the ask names only a detail.

    "we got a puppy called Biscuit" then "how do I stop the chewing" names the trouble and not
    the animal, and on its own "the chewing" reaches the answer about chewing a pen at a desk -
    a confident answer about the wrong thing. The store knows what the thing is, so its kind is
    put beside the detail: "how do I stop the chewing puppy" reaches the puppy's own entry. The
    same holds for a cat, a dog or a rabbit called anything at all, because the kind is read from
    the store and never from the line.

    Only where the filled ask lands exactly on an entry keyed to the kind the line has not
    named, so a line that names its own subject ("how do I stop the slugs" after a puppy) and a
    detail that belongs to nothing the store holds are both left to the reading they already
    have.
    """
    found = _the_kind_the_line_leaves_out(understood, memory)
    if not found:
        return None
    line, kind = found
    filled = line + " " + kind
    item = _entry(filled)
    if item is None:
        return None
    # The entry has to be the one the kind and the detail are both part of: "chew" is what the
    # line asks about and "puppy" is what the store holds. An entry that only the detail reaches
    # is the one the line already had, and one that only the kind reaches has not been asked.
    keyed = _key_words_of(item)
    if kind not in keyed and stem(kind) not in keyed:
        return None
    # What the line says about the trouble, in the words that name it: the ask ("how do I") and
    # the verb that carries it ("stop", "get rid of") are how the question is put and not what it
    # is about, and an entry can be reached on one of those alone. A cat with a chewing ask
    # reaches the cat-keeping-out-of-the-garden entry through its own "stop", and its advice is
    # about soil rather than about a cat that chews. So the trouble has to be named by the line.
    said = [word for word in words(line)
            if word not in ASK_PART and word not in ASK_ONLY and word not in STAND_IN
            and word not in STOPWORDS]
    trouble = [word for word in said if word not in IMPERATIVE]
    if not _names_it(trouble or said, item):
        return None
    reading = dict(understood)
    reading["clean"] = " ".join(filled.lower().split())
    reading["words"] = words(reading["clean"])
    return reading


def the_pet_the_line_before_named(memory):
    """"my cat" when the line before named a pet the store holds, else "".

    The thing a pronoun points at is what the line before it named: "how often should I walk it"
    straight after "I have a dog". A pet mentioned ten turns ago is not what "it" means now -
    "my boiler is broken" then "how much will it cost" is about the boiler, and filing the cat
    into that line would answer a different question.
    """
    turns = memory.get("turns") if isinstance(memory.get("turns"), list) else []
    before = ""
    for turn in reversed(turns):
        said = turn.get("user") if isinstance(turn, dict) else None
        if isinstance(said, str) and said.strip():
            before = said
            break
    if not before:
        return ""
    # The word they used, not the family it belongs to: "what should I feed my kitten" is the
    # kitten's answer, and filling "my cat" in its place would give the adult cat's.
    named = {}
    for word in PET_WORD.findall(before):
        word = PET_ONE.get(word.lower(), word.lower())
        named.setdefault(BABY_OF.get(word, word), word)
    user = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    # A breed is the animal it is. "we are getting a rescue greyhound next week" names no word
    # PET_WORD knows, so "how much exercise does it need" had nothing to point at and the ask fell
    # to the search hedge while the store held the dog. The animal's own word is the one an entry
    # is keyed on, so that is what goes in the line; a breed said as something else ("the
    # greyhound bus") is not an animal and `a_frame_before` is what knows the difference.
    # A puppy in the store is a dog too, and the puppy's own entry is the one that answers a puppy
    # question: "we just got a puppy" / "hes a labrador, 9 weeks old" / "how much should i be
    # feeding him" got the adult dog's 2% guide once the breed filled the line, where the word
    # they used - the puppy - reached the four-small-meals answer. So a kind the store holds as a
    # baby is left to the baby word.
    babies = set()
    for pet in user.get("pets") or []:
        if not isinstance(pet, dict):
            continue
        kind = str(pet.get("animal") or "").strip().lower().rstrip("s")
        if kind in BABY_OF:
            babies.add(BABY_OF[kind])
    from ..understanding import breeds as _breeds
    for match in _breeds.BREED_RE.finditer(before):
        if not _breeds.a_frame_before(before, match.start()):
            continue
        kind = _breeds.the_kind_of(match.group(0))
        if kind and kind not in babies:
            named.setdefault(kind, kind)
    if not named:
        return ""
    for pet in reversed(user.get("pets") or []):
        if not isinstance(pet, dict):
            continue
        kind = pet.get("animal")
        if not isinstance(kind, str) or not kind.strip():
            continue
        kind = BABY_OF.get(kind.strip().lower().rstrip("s"), kind.strip().lower().rstrip("s"))
        if kind in named:
            return "my " + named[kind]
    return ""


# "How do I keep it up?" is the question of carrying on with the thing in hand, and those words
# are the whole of the ask: after "im learning spanish" the line names no subject for the
# knowledge base to reach, so the search hedge is the reply, and after an answer it is handed the
# answer it has already had ("Same as before: ..."). Said as the question it is, the entry that
# holds the answer - keep it small and scheduled, track the days you show up - is reached.
KEEP_IT_UP = re.compile(
    r"\bhow\s+(?:do|can|should|would|could)\s+i\s+"
    r"(?:keep\s+(?:it|this|that)\s*(?:up|going|on)?|"
    r"keep\s+(?:going|on|at\s+it)|"
    r"keep\s+on\s+(?:with\s+)?(?:it|this|that)|"
    r"stick\s+(?:with|at|to)\s+(?:it|this|that)|"
    r"stay\s+(?:with|at)\s+(?:it|this|that))\b", re.I)
# The words the ask becomes. "stay motivated" is what the answer to carrying on is keyed to, and
# nothing else about the ask is changed.
STAYING_WITH_IT = "how do i stay motivated"
# The topic in hand has to be something they are learning or practising - "im learning spanish",
# "i started learning spanish last week", "im playing the piano", "im writing a novel". Only then
# is "how do i keep it up" a question about carrying that on: after "my kitchen tap is dripping"
# the same words name nothing the bot can answer, and the honest hedge is the reply rather than
# advice about keeping a habit. A plan with its own steps ("im doing couch to 5k", "im trying to
# save money") is left out on purpose: its entry already answers a question about keeping going
# with the part of the plan that says so, and the general advice would be a worse reply there.
# The ask is the same whether the thing was started years ago, last week or not yet: "i started
# learning spanish last week" and "i want to learn spanish" are the topic being kept up, and
# reading only "im learning" left both of them with the previous answer handed back clipped.
AN_ACTIVITY = re.compile(
    r"\b(?:i'?m|i am|i'?ve been|i have been|i'?m still|i am still|"
    r"i'?ve started|i have started|i started|i began|i'?ve begun|i have begun|"
    r"i want to|i'?d like to|i'?m trying to|i am trying to|i'?ve been trying to)\s+"
    r"(?:learning|studying|practising|practicing|reading|writing|playing)\b|"
    r"\b(?:i'?m|i am|i'?ve been|i have been|i'?m still|i am still|i started|i'?ve started|"
    r"i began|i want to|i'?d like to|i'?m trying to|i am trying to)\s+"
    r"(?:learn|study|practise|practice|read|write|play)\b", re.I)


def _carrying_on(understood, memory):
    """The bare "how do i keep it up" as the carrying-on question, or None.

    Only when the topic in hand is an activity, and only for the ask that says nothing else: the
    reading is handed back with the question in place of those words and nothing else changed, so
    the sentence has one subject - carrying on - and the knowledge base answers it.
    """
    line = str(understood.get("clean") or understood.get("text") or "")
    found = KEEP_IT_UP.search(line)
    if not found:
        return None
    record = carried_topic(memory, line) or {}
    text = str(record.get("text") or "")
    if not text.strip() or not AN_ACTIVITY.search(text):
        return None
    text = (line[:found.start()] + STAYING_WITH_IT + line[found.end():]).strip()
    reading = dict(understood)
    reading["clean"] = " ".join(text.lower().split())
    reading["words"] = words(reading["clean"])
    if "norm_text" in reading:
        reading["norm_text"] = reading["clean"]
    return reading

# A whole line that takes something off the thing in hand and says nothing else: "no cheese
# though", "without the sauce", "skip the onions please". The thing it names is what is gone.
LIMIT_LINE = re.compile(
    r"^\s*(?:oh\s+|and\s+|also\s+)?(?:no|nope|not|without|skip|minus|except|but\s+no)\b"
    r"\s+(?P<thing>[a-z']{3,20}(?:\s+[a-z']{3,20}){0,2}?)"
    r"\s*(?:though|tho|then|please|for\s+me|thanks|sorry)?\s*[.!]*\s*$", re.I)


def _what_the_turn_took_away(record, memory):
    """The things a turn took off the thing in hand: "no cheese though" gives {"cheese"}.

    A limit is not a subject. The turn after one was widened with the thing that had just been
    taken away - "and how long does that take" after a frittata and "no cheese though" was read
    as how long the cheese takes - which reaches nothing, so the dish's own time, one entry away
    and already on the screen, was lost.
    """
    if not isinstance(record, dict):
        return set()
    said = " ".join(str(record.get("text") or record.get("user") or "").lower().split())
    found = LIMIT_LINE.match(said)
    if not found:
        return set()
    taken = set()
    for word in found.group("thing").split():
        if word in STOPWORDS or len(word) < 3:
            continue
        taken.add(stem(word))
    return taken


def _widened(line, understood, record, memory):
    """This line read with the record's subject put back in, or None when that reaches nothing."""
    from .when import asks_what_today_is

    if asks_what_today_is(line):
        # "what day is it" asks the calendar, and no subject of the chat goes into it: widened with
        # the trip in hand it read "what day is the portugal trip", and the Portugal card answered
        # a question about today. The calendar answers it where the calendar is read.
        return None
    if not isinstance(record, dict):
        return None
    topic_text = str(record.get("text") or "")
    if not topic_text.strip():
        return None
    taken = _what_the_turn_took_away(record, memory)
    if leans_on_topic(understood, memory):
        subject_words = _subject_words_to_carry(record, line, memory)
        if taken:
            subject_words = [word for word in subject_words
                             if stem(str(word).lower()) not in taken]
        if not subject_words or all(word in words(line) for word in subject_words):
            return None
        text = widen(line, subject_words, topic_text)
        if text is not None:
            return text
        # The topic's key words did not reach an entry, but the words of the topic the
        # knowledge base knows may: "why is that happening?" after a flat sourdough.
        return carry_the_ask(line, topic_text)
    # A line that names nothing of its own ("how often should I go?") is the same kind of
    # follow-up: it is read with the topic's words, or not at all.
    return carry_the_ask(line, topic_text)


def _the_length_of_the_aim(understood, memory):
    """This turn read as the length of the aim the chat is on, when it asks only a length.

    "im trying to get fit before the holiday" / "how long will it take": the line names nothing of
    its own, so the "it" is filled in from the topic - and the only noun the chat has is the
    deadline, so the length of getting fit is answered with the package-travel rules. The aim on
    the line before is what the length is about; `bot/memory/named.py` writes that question out
    ("how long does it take to get fit") and keeps it only where an entry answers a length, so a
    line that reaches nothing is still answered by whatever reaches it.
    """
    line = str(understood.get("clean") or understood.get("text") or "")
    if not line:
        return None
    try:
        from . import named

        asked = named.a_goal_measured(line, memory)
    except Exception:  # noqa: BLE001 - a reading that fails leaves the line as it was
        return None
    if not asked:
        return None
    reading = dict(understood)
    reading["clean"] = asked
    reading["words"] = words(asked)
    if "norm_text" in reading:
        reading["norm_text"] = asked
    return reading

# The gatherings people announce they are putting on. The food for one is the first thing a
# friend asks about, and the entries hold the food, not the occasion.
GATHERING_WORDS = frozenset("""barbecue bbq party picnic birthday brunch supper do
gathering get-together potluck housewarming""".split())
# A gathering that starts tonight has no day before in it, so the food-ahead entry cannot help.
TOO_SOON_TO_COOK = re.compile(r"\b(?:tonight|today|this (?:evening|afternoon)|in an hour|in a few hours|"
                              r"right now|already)\b", re.I)
# A do put on for a child or for one person is about that person: the food for a crowd is not
# what they asked, and the bot's own question ("What are they into at the moment?") is better.
FOR_SOMEBODY = re.compile(
    r"\b(?:kid|kids|child|children|toddler|teen|teens|teenager|teenagers)\b|"
    r"\b\w+[- ]year[- ]old\b|\b\d+\s*(?:st|nd|rd|th)?\s*birthday\b|"
    r"\b(?!\d+\s)(?:for|of) (?:my|his|her|our|a|an)\s+(?:mum|mom|dad|father|mother|son|daughter|"
    r"wife|husband|partner|friend|sister|brother|nan|nana|gran|granny|grandma|grandad|grandpa|"
    r"colleague|boss|niece|nephew|cousin|aunt|uncle|godson|goddaughter)\b", re.I)
PUTTING_ON = re.compile(r"\b(?:we|i)(?:'?re| are| am|'?m)?\s+"
                        r"(?:having|doing|throwing|hosting|planning|organising|organizing|"
                        r"holding|arranging)\b")


def _a_gathering_read_as_the_food(understood, line, memory):
    """"we are having a barbecue" read as the food for it, when its own words reach nothing.

    A plan announced is the thing the chat is on, and the next turns add to it ("one of my
    friends is a vegetarian", "there will be nine of us"). The first turn itself reached no
    entry, so it was answered with a listening line and the plan never started. The food for a
    gathering is what a friend offers first, and the entry that holds it is keyed on the
    gathering's own word only for a party or a picnic, so both forms are tried and only one that
    reaches an entry is used.
    """
    if not isinstance(understood, dict):
        return None
    if understood.get("kind") != "statement" or understood.get("asks"):
        return None
    said = set(words(line))
    gathering = said & GATHERING_WORDS
    if not gathering or not PUTTING_ON.search(line):
        return None
    if _entry(line) is not None:
        return None  # the words already reach an answer: leave it alone
    if TOO_SOON_TO_COOK.search(line):
        return None  # a party tonight wants ice and glasses, and the entry is about the day before
    if FOR_SOMEBODY.search(line):
        return None  # a do put on for a child or for one person is about them, and the entry is not
    for candidate in [" ".join(sorted(gathering)) + " food", "party food"]:
        if _entry(candidate) is not None:
            return candidate
    return None


def _the_whole_topic(line, record_text, memory=None):
    """The line read with the topic's own words, phrase and all, or None when that reaches nothing.

    The topic lends its words one at a time and its gist is a single word, so a phrase the
    knowledge base keys on is split and nothing matches: after "im learning to drive", "how many
    lessons will i need" was widened to "learning drive", which reaches no entry, and the person
    got the search hedge with the answer one phrase away. Reading the topic back in whole keeps
    the particle that makes the phrase ("learn to drive", "get married", "pass my test"), and it
    is only asked for when every narrower widening has reached nothing.
    """
    if not _leads_a_question(line):
        # A statement that reaches nothing is left as it came in. Reading it against the thing
        # the chat is on is what turns "it was about a dog" - said of a film - into the entry
        # about a dog that wakes in the night, on the film's "night" and the line's "dog": a
        # question that reaches nothing wants the thing put back in, a remark does not.
        return None
    best, best_score = None, -1
    for said in _the_things_the_chat_named(record_text, memory, line):
        widened = str(line) + " " + said
        reached = _entry(widened)
        if reached is None:
            continue
        last = (memory or {}).get("last_answer")
        if isinstance(last, dict) and last.get("id") == getattr(reached, "id", None):
            # What the line reaches with the topic in it is the answer already on the screen:
            # saying it again is what this widening is for, not what it should do.
            continue
        # Which thing the chat named the line should be read against is decided by the answer
        # it reaches, not by how recent the thing is: "my test is in march" on the end of "how
        # many lessons will i need" reaches the revision planner on "test", and the plan two
        # lines back reaches the driving lessons on "drive". The thing whose words the entry is
        # actually keyed on is the one the ask is about.
        if _already_answered_here(reached, memory):
            # The chat has had this answer: a widening that reads a short line back to a thing
            # the bot has already dealt with is the repeat the store spends its time avoiding,
            # not a follow-up. "fine, ill have a look at it" after the tap got the cake
            # paragraph back, because the cake was still one of the things the chat had named.
            continue
        if not _the_answer_is_about_what_the_line_names(reached, line):
            continue
        score = _how_much_of_the_thing_the_entry_uses(reached, said)
        if score > best_score:
            best, best_score = widened, score
    return best


# A content word that names the shape of the ask rather than a thing in the world. "where do i
# start" is the whole of some lines, and every second answer the bot has says "start with"; the
# same goes for "first" ("what do i do first") and "next" ("what next"). These words are not
# evidence that an answer is about what the person asked about, so they do not confirm a
# widening on their own.
ASK_SHAPE_WORDS = frozenset("""
start starts started starting begin begins beginning beginning first next thing things step
steps part parts bit bits way ways point best better good useful help advice tip tips
""".split())


def _the_answer_is_about_what_the_line_names(entry, line):
    """True when the entry's own answer talks about the thing the line asks about.

    An entry is keyed on the words people use for its subject, so an entry about moving house
    with children is keyed on "school" while its answer is about council tax, the GP and the
    meters. After "we are thinking of moving to leeds", "what are the schools like" was widened
    to reach it and got a list of admin for a different question; the search hedge it had before
    was the better reply. So the answer the widening reaches has to use one of the line's own
    words - the driving lessons answer says "lessons", the wedding budget answer says "costs" -
    and a line with no content word of its own is let through, because there is nothing to check.
    """
    asked = [word for word in keywords(line) if len(word) > 3]
    if not asked:
        return True
    named = [word for word in asked if word not in ASK_SHAPE_WORDS]
    if not named:
        # The line is the shape of a question and nothing else - "where do i start", "what do i
        # do first", "where do i begin". Its one content word is one that any answer about any
        # subject can use (the tidying card opens "Start with what is on the floor"), so being
        # named in the entry's answer is no evidence at all that the entry answers this line.
        # After "i want to go back to work after 6 years at home", "where do i start" was widened
        # onto the room-tidying entry on the word "start" and got a paragraph about cups and
        # plates where the honest hedge was the better reply. A line that names no thing cannot
        # confirm the thing the widening reached, so the widening stands down.
        return False
    said = words(str(getattr(entry, "reply", "") or ""))
    return any(alike(word, token) for word in named for token in said)


def _already_answered_here(entry, memory):
    """True when the reply the entry gives has already been said in this conversation."""
    reply = str(getattr(entry, "reply", "") or "").strip()
    if not reply:
        return False
    opening = " ".join(reply.lower().split()[:8])
    for turn in (memory or {}).get("turns") or []:
        if not isinstance(turn, dict):
            continue
        said = " ".join(str(turn.get("bot") or "").lower().split())
        if said and said.startswith(opening):
            return True
    return False


def _how_much_of_the_thing_the_entry_uses(entry, said):
    """How many of the thing's own content words the entry the widening reached is keyed on."""
    keyed = _key_words_of(entry)
    return len([word for word in keywords(said)
                if len(word) > 2 and any(alike(word, key) for key in keyed)])


def _the_things_the_chat_named(record_text, memory, line=""):
    """The things the chat has named, newest first, to read a follow-up against.

    The topic the line leans on is not always the one that can answer it. "im learning to drive"
    then "my test is in march" then "how many lessons will i need": the newest thing the chat
    named is the date, and read against the date the ask reaches nothing, but the plan two lines
    back reaches the lessons answer in full. A follow-up is read against the newest thing that
    can answer it, which is the rule the picture is worth: the chat is still on the plan.
    """
    seen = []
    texts = [str(record_text or "")]
    if _leads_a_question(line):
        # Only a question is read against an older thing. A statement that reaches nothing is
        # left as it came in: "it was about a dog" after "i cried at a film last night" read
        # against the film reaches the dog-waking-at-night entry on "dog" and "night", and the
        # person talking about a film got advice on a dog that wakes in the night.
        for record in reversed(list((memory or {}).get("topics") or [])[-4:]):
            if isinstance(record, dict):
                texts.append(str(record.get("text") or ""))
    for text in texts:
        said = " ".join(text.lower().split())
        if not said or len(said.split()) > 12:
            continue
        if " ".join(words(said)) in seen:
            continue
        seen.append(" ".join(words(said)))
        yield said


def followup_reading(understood, memory):
    """This turn's reading with the current topic's subject put back in, when the line leans
    on it: 'and if I stuff it?' after a chicken is read as being about the chicken.

    A correction is read as the topic it corrected, because memory_store has already rewritten
    the topic with what they meant: 'sorry, I meant Florence' re-asks the Florence question.
    Only lines the reading alone cannot answer are widened, so an answer that already fits is
    never replaced by a guess.
    """
    if not isinstance(understood, dict):
        return understood
    carrying_on = _carrying_on(understood, memory)
    if carrying_on is not None:
        return carrying_on
    slot = next_slot_reading(understood, memory)
    if slot is not None:
        return slot
    if _after_an_emergency(memory):
        return understood  # mid-emergency the topic starts again from the line itself
    if _after_a_correction(memory):
        return understood  # the topic they have just corrected is not the one to widen with
    aim_length = _the_length_of_the_aim(understood, memory)
    if aim_length is not None:
        return aim_length
    # The pronoun put back where it was, before anything is carried onto the end of the line:
    # "how long can they be left alone" is the cat's question, and the subject carried onto the
    # end of it reached nothing while the cat's own row was one entry away.
    filled_in = the_pronoun_written_as_what_it_stands_for(understood, memory)
    if filled_in is not None:
        return filled_in
    pointed = the_thing_it_is(understood, memory)
    if pointed is not None:
        return pointed
    # "will it go away on its own" asks how long the thing goes on, which is a row of its own: the
    # pronoun is filled with the thing and asked in the wording that row is kept in.
    prognosis = the_prognosis_the_line_asks(understood, memory)
    if prognosis is not None:
        return prognosis
    # "is it expensive" asks what the thing in hand is like, and only the pronoun says which thing
    # it is: filling it in is what reaches the entry for the cost of the trip to Rome, instead of
    # the sights answer being handed back with "Same as before" in front of it.
    property_ask = the_property_of_the_thing(understood, memory)
    if property_ask is not None:
        return property_ask
    animal = the_animal_the_subject_is(understood, memory)
    if animal is not None:
        return animal
    airport = the_airport_there_is(understood, memory)
    if airport is not None:
        return airport
    # "how much is too much" after "i drink a lot of coffee" is the same family: the thing in hand
    # is what the limit is about, and the row that answers it is keyed to the thing.
    limit_ask = the_limit_of_the_thing(understood, memory)
    if limit_ask is not None:
        return limit_ask
    # The shrugs in the middle of the line are not part of the question the topic is put back
    # into: "what can i do to help her really" widened to "... really mum arthriti", which names
    # nothing, and the answer one word away was lost.
    line = without_the_shrug(str(understood.get("clean") or understood.get("text") or ""))
    gathering = _a_gathering_read_as_the_food(understood, line, memory)
    if gathering is not None:
        # "we are having a barbecue": they are hosting and nothing in the words reaches an
        # entry, so the turn was answered "I'm listening - say more if it helps." while the
        # store holds what to feed a crowd. A gathering announced asks for the food for it.
        reading = dict(understood)
        reading["clean"] = gathering
        reading["words"] = words(gathering)
        if "norm_text" in reading:
            reading["norm_text"] = gathering
        return reading
    period = the_period_they_ask_about(understood, memory)
    if period is not None:
        reading = dict(understood)
        reading["clean"] = period
        reading["words"] = words(period)
        if "norm_text" in reading:
            reading["norm_text"] = period
        return reading
    meal = meal_follow_up(understood, memory)
    if meal is not None:
        return meal
    trip = the_weather_of_the_trip(understood, memory)
    if trip is not None:
        reading = dict(understood)
        reading["clean"] = trip
        reading["words"] = words(trip)
        if "norm_text" in reading:
            reading["norm_text"] = trip
        return reading
    record = carried_topic(memory, line)
    if record is None or left_for_a_blank(memory, line):
        # The chat has moved on to a thing named in a turn we could not answer: widening this
        # line with the older subject would answer about the wrong thing.
        return understood
    same_ask = how_much_of_the_thing_in_hand(line, memory)
    if same_ask:
        reading = dict(understood)
        reading["clean"] = same_ask
        reading["words"] = words(same_ask)
        if "norm_text" in reading:
            reading["norm_text"] = same_ask
        return reading
    brought = the_thing_the_subject_brings(understood, memory)
    if brought is not None:
        reading = dict(understood)
        reading["clean"] = brought
        reading["words"] = words(brought)
        if "norm_text" in reading:
            reading["norm_text"] = brought
        return reading
    if elided_ask(line):
        # "any games", "what about drinks": the line names the part it asks about and leaves the
        # asking off, so the understanding engine reads it as a statement and no entry is
        # reached. The chat it is in says which entry of that kind is meant - a birthday picnic
        # with ten children is the games answer for children - and the line itself still has to
        # name the thing the entry is about, so this borrows a situation rather than a subject.
        # When the situation reaches nothing the line takes the way every other follow-up takes.
        situated = carry_the_ask(line, str(record.get("text") or ""), understood, memory)
        if situated is not None:
            reading = dict(understood)
            reading["clean"] = " ".join(str(situated).lower().split())
    leaning = _the_turn_we_lean_on(understood, memory)
    if leaning is not None and _said_later_than(leaning, record):
        # The turn the line leans on is the newer thing on the table: the subject moves on
        # inside a topic ("im planning a veg patch" / "also i want tomatoes"), and the earlier
        # words widen the line to nothing. Where the newer turn widens to nothing either, the
        # topic on memory is the one the line has been answered from all along, so nothing
        # changes for it.
        newer = _widened(line, understood, leaning, memory)
        if newer is not None:
            reading = dict(understood)
            reading["clean"] = " ".join(str(newer).lower().split())
            reading["words"] = words(reading["clean"])
            if "norm_text" in reading:
                reading["norm_text"] = reading["clean"]
            return reading
    if understood.get("intent") == "correction":
        text = str((record or {}).get("text") or "")
        if not text.strip() or " ".join(words(text)) == " ".join(words(line)):
            return understood
    elif bare_question(understood, memory) and carry_the_ask(
            line, str(record.get("text") or ""), understood, memory) is None:
        # Only when the topic's own words reach no entry: "should i cut the brown bits off?"
        # names something of its own (cutting), and the plant entry answers it through the
        # topic's subject words below, so the bare path must not take the line first - read
        # with the topic's key subjects in it, it reached the tipping entry on "tips" twice
        # and the plant chat lost its answer.
        # A question that names no subject of its own is read with the topic's own words in it:
        # "what should I wear" after an interview is the interview's words with the outfit ask,
        # and which entry answers that is the answers' to decide. The record's own words only:
        # an older record's subject is a different conversation ("im getting married in june"
        # after a boiler is not a question about the boiler), so a topic with no subject words
        # of its own lends nothing and the line is left alone.
        extra = []
        not_doing = _what_they_are_not_doing(record.get("text") or "")
        for word in _subject_words_to_carry(record, line, memory):
            if word in not_doing:
                continue  # "wont listen" is not a subject to widen the line with
            if _how_they_feel(word):
                continue  # "hate" is how they feel about the job, not what the job is
            if word not in words(line) and word not in extra:
                extra.append(word)
        if not extra:
            return understood
        widened = line + " " + " ".join(extra)
        found = _entry(widened)
        if found is None:
            # The topic as they said it, question and all: "i hate my job" / "what should i do"
            # lends only "job", and "what should i do job" reaches nothing, while the whole of
            # the topic reaches the entry about hating the job. Only an entry keyed to a word the
            # topic lent counts, so a topic that widens to an entry about something else is left
            # as it came in.
            said_whole = " ".join(str(record.get("text") or "").split() + [line])
            item = _entry(said_whole)
            if item is None or not any(_keyed_to(_key_words_of(item), word) for word in extra):
                return understood
            text = said_whole
        else:
            text = widened
    elif not _still_the_topic(record, memory):
        # The chat moved off the topic on a line answered as small talk, and nothing since has
        # leaned on it: see `_still_the_topic`. The leaning path above has already been tried,
        # because a turn of small talk does not stop the chat going back to the thing it was on.
        return understood
    elif leans_on_topic(understood, memory):
        subject_words = _subject_words_to_carry(record, line, memory)
        if not subject_words or all(word in words(line) for word in subject_words):
            return understood
        text = widen(line, subject_words, str(record.get("text") or ""))
        if text is None:
            # The topic's key words did not reach an entry, but the words of the topic the
            # knowledge base knows may: "why is that happening?" after a flat sourdough.
            text = carry_the_ask(line, str(record.get("text") or ""), understood, memory)
        if text is None:
            # A line that only adds a limit to the question ("i only have ten minutes") is that
            # question asked again with the limit in it.
            text = _constrains_the_ask(line, str(record.get("text") or ""))
        if text is None:
            text = _the_whole_topic(line, str(record.get("text") or ""), memory)
        if text is None:
            return understood
    else:
        # A line that names nothing of its own ("how often should I go?") is the same kind of
        # follow-up: it is read with the topic's words, or not at all.
        text = carry_the_ask(line, str(record.get("text") or ""), understood, memory)
        if text is None:
            text = _constrains_the_ask(line, str(record.get("text") or ""))
        if text is None:
            text = _the_whole_topic(line, str(record.get("text") or ""), memory)
        if text is None:
            return understood
    reading = dict(understood)
    reading["clean"] = " ".join(str(text).lower().split())
    reading["words"] = words(reading["clean"])
    # An entry that phrases itself from the line reads `norm_text`, the line as it was typed, so
    # the subject put back in has to be there too: "it is still tough in the stalk" after
    # sprouts reached the brassica fix on its words, and the fix then read the line as it came
    # in, found no vegetable in it, and declined - so the widening bought nothing and the turn
    # went to the small talk with a reply about tiredness.
    if "norm_text" in reading:
        reading["norm_text"] = reading["clean"]
    return reading


# The words a follow-up brings to the record it stays on, as this turn put them there. The turn is
# not over when they are added - the reply is composed afterwards - so they are noted and taken
# back if that reply turns out to be a step back.
WORDS_THIS_TURN = "words_this_turn"
# The record this turn put in place, and what it is a detail of.
TURN_TOPIC = "topic_this_turn"


def note(memory, text, kind=None):
    """File the line, and note what filing it put on the record the chat is on.

    The words a line adds are what the next line is looked up with, so they are worth keeping
    ("does beer work" after the slugs is still about the slugs). But the reply to that line can be
    a step back - "I don't know enough to answer that honestly" - and then nothing about the thing
    was answered: what the turn added is taken back once the reply is known, in
    `the_step_back_takes_its_words_back`.
    """
    _the_step_back_is_undone(memory)
    before = _the_words_before_the_turn(memory)
    previous = current(memory)
    record = _note(memory, text, kind)
    _the_words_this_turn(memory, before, record, previous)
    return record


def _the_reply_to_the_turn_before(memory):
    """What the bot said last, from the history the store keeps."""
    for turn in reversed(list(memory.get("turns") or ())):
        if isinstance(turn, dict) and turn.get("bot"):
            return str(turn.get("bot") or "")
    return ""


def _the_step_back_is_undone(memory):
    """Take back the words the turn before added when its reply was a step back.

    The reply is composed after the store has filed the line, so what the turn added is noted
    then and taken back here, at the start of the next turn. The store observes before any module
    answers, so the next line is still looked up with the record as it stood when the step back
    was the answer to the line before it.
    """
    if not (WORDS_THIS_TURN in memory or TURN_TOPIC in memory):
        return None
    said = _the_reply_to_the_turn_before(memory)
    if not said:
        memory.pop(WORDS_THIS_TURN, None)
        memory.pop(TURN_TOPIC, None)
        return None
    return the_step_back_takes_its_words_back(memory, said)


def _the_words_before_the_turn(memory):
    """The words each record holds, by the words of the line it came from."""
    held = {}
    for record in _the_records(memory):
        held[str(record.get("text") or "")] = list(record.get("words") or ())
    return held


def _the_records(memory):
    for record in [memory.get("topic")] + list(memory.get("topics") or ()):
        if isinstance(record, dict):
            yield record


def _the_words_this_turn(memory, before, record, previous):
    """Note what this turn added to the record, and which record it left in place."""
    memory.pop(WORDS_THIS_TURN, None)
    memory.pop(TURN_TOPIC, None)
    if not isinstance(record, dict):
        return
    said = str(record.get("text") or "")
    added = [word for word in (record.get("words") or ()) if word not in before.get(said, ())]
    if added:
        memory[WORDS_THIS_TURN] = {"text": said, "words": added}
    # What this turn put in place, and what it is a detail of: a detail's line becomes a topic of
    # its own pointing back with "of", and a reply that steps back must leave the chat where it
    # was rather than on a question nobody answered.
    memory[TURN_TOPIC] = {"text": said, "of": str(record.get("of") or ""),
                          "was": str(previous.get("text") or "") if isinstance(previous, dict) else ""}


def _a_step_back(reply):
    """True when the reply is one of the pools that say the bot cannot answer this."""
    from ..compose import fallback  # noqa: PLC0415 - compose imports the memory package
    try:
        return bool(fallback.is_a_hedge(str(reply or "").strip()))
    except Exception:  # noqa: BLE001 - a reply is never worth a failed turn
        return False


def _the_detail_steps_back(memory, reply):
    """Put back the thing the chat was on when this turn's detail about it was only stepped back from."""
    noted = memory.pop(TURN_TOPIC, None)
    if not isinstance(noted, dict) or not _a_step_back(reply):
        return None
    back = str(noted.get("of") or "") or str(noted.get("was") or "")
    if not back or back == str(noted.get("text") or ""):
        return None
    record = current(memory)
    if not isinstance(record, dict) or str(record.get("text") or "") != str(noted.get("text") or ""):
        return None  # the turn did not leave that record in place
    older = None
    for kept in (memory.get("topics") or ()):
        if isinstance(kept, dict) and str(kept.get("text") or "") == back:
            older = kept
    if not isinstance(older, dict):
        return None
    said = dict(older)
    memory["topic"] = said
    topics = memory.get("topics")
    if isinstance(topics, list):
        topics[:] = [other for other in topics if other is not older
                     and str((other or {}).get("text") or "") != back]
        topics.append(said)
    return said


def the_step_back_takes_its_words_back(memory, reply):
    """Undo this turn's word merge when the turn stepped back, so the next line is not looked up
    with words nobody answered."""
    _the_detail_steps_back(memory, reply)
    noted = memory.pop(WORDS_THIS_TURN, None)
    if not isinstance(noted, dict) or not _a_step_back(reply):
        return None
    words = list(noted.get("words") or ())
    if not words:
        return None
    # Every record holding that line, because the store keeps copies of a record: the current one
    # and an entry in "topics" can be two dicts with the same words, and the words a turn added
    # are on both of them.
    took_back = None
    for kept in _the_records(memory):
        if str(kept.get("text") or "") != str(noted.get("text") or ""):
            continue
        kept["words"] = [word for word in (kept.get("words") or ()) if word not in words]
        took_back = kept["words"]
    return took_back
