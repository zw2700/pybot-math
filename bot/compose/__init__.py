"""Phrasing helpers for the response composer. The routing lane owns the composer: what to do
this turn (bot/modules/arbiter.py chooses among the modules' replies) and how it is phrased.
"""
import random
import re

from ..memory import history

# A feeling or news word only says what it says when nothing in front of it turns it round:
# "not happy", "didn't win", "never finished". Every module that reads mood from words uses
# this, so no pool is cheerful at someone who has just said they feel awful.
NEGATORS = frozenset((
    "not", "no", "never", "hardly", "barely", "nothing", "without", "cant", "cannot", "dont",
    "doesnt", "didnt", "isnt", "wasnt", "arent", "werent", "wont", "wouldnt", "couldnt",
    "shouldnt", "havent", "hasnt", "aint",
))

# A nearly-done thing is not done: "i nearly finished it", "i almost won". It is not condoled
# either, so a cue with one of these in front of it is skipped rather than counted the other way.
NEARLY = frozenset(("nearly", "almost"))
# A line that says how long something has been going: "a cough that wont go away", "going nearly
# three weeks", "it has been dragging on". The length is what the person is telling you, so the
# answer for the first day of a cold - "rest, warm drinks and an early night" - is the wrong one.
# A bare "still" is deliberately not in here: "still at work", "still love him" and "still snow
# outside" all carry it, so a caller that wants the "still here after a week" sense pairs
# STILL_AT_IT with the illness words it already matched.
SAYS_IT_HAS_LINGERED = re.compile(
    r"\b(?:wont|won'?t|not)\s+(?:go|shift|clear|budge|settle)\w*|"
    r"\bfor\s+(?:\d+|a\s+couple\s+of|a\s+few|a|an|two|three|four|five|six|seven|eight|nine|"
    r"ten)\s+(?:days?|weeks?|months?|years?)\b|\b(?:been going|going on|dragging on)\b", re.I)
STILL_AT_IT = re.compile(r"\bstill\b", re.I)


# A day or two is not "long enough to be a different question": "i had a cough for two days" is
# a bug that has just arrived, and the answer for a thing that has hung on reads as alarm.
# "day two" is the other way people say a bug is two days old, and it is the same short run:
# "im still full of cold, day two" was answered "anything that has hung on is worth getting
# looked at" by the "still" arm below.
_SHORT_RUN = re.compile(r"\b(?:(?:one|two|a\s+couple\s+of)\s+days?|day\s+(?:one|two|three|1|2|3))\b",
                        re.I)


def says_it_has_lingered(clean, illness=False):
    """True when the line says the thing has been going long enough to be a different question.

    A bare "still" is not that: it says "not gone yet", and how long that is the line never says.
    Reading it as "long enough" answered "im still full of cold" with "that is long enough to be
    worth a proper look rather than another stretch of waiting", which is a different claim from
    the one the person made, and "im still full of cold, day two" with the same sentence about a
    bug two days old. So the duration has to be in the words: a run of days, weeks or months, a
    thing that will not shift, or a thing that has been dragging on. `illness` is kept for the
    callers that already know they read a cold or a bug, and it no longer decides on its own.
    """
    return bool(SAYS_IT_HAS_LINGERED.search(clean) and not _SHORT_RUN.search(clean))


# The answers for a thing that has hung on rather than a thing just started, in one place so the
# module that says it and the composer's symptom path give the person the same sentences. The
# "take it easy today" comfort line is not in here: a cough that will not go away is not a day
# off, it is a thing to have looked at, which is the whole reason this pool exists.
LINGERED_LINE = (
    "Anything that has hung on is worth getting looked at — a pharmacist will see you quicker "
    "than a GP, and they'll tell you if it needs one.",
    "That is long enough to be worth a proper look rather than another stretch of waiting: a "
    "pharmacist today, and a GP if it is still there after that.",
    "Sorry it is still going. Note when it is worst and what eases it, then take that to a "
    "pharmacist — a thing that has lasted this long is worth putting a name to.",
)
# The words a bare "t" follows when a line lost its apostrophe: "can t keep anything down".
AUX = frozenset(("can", "could", "do", "does", "did", "is", "was", "were", "are", "would",
                 "should", "have", "has", "had", "wo", "ai", "must", "need", "might"))


# The auxiliaries a lost apostrophe leaves in front of "nt": "didnt", "wasnt", "couldnt",
# "havent". Only these make an "nt" a negation. Any word ending in "nt" used to count, so an
# ordinary word did the negation's work and the line was read as a denial: "im 34 weeks pregnant
# and knackered" was answered "Right, not that one. What's behind it?", because "pregnant" ends in
# "nt". "content", "spent", "went", "silent" and "important" are the same trap.
CONTRACTED_AUX = frozenset(("do", "did", "ca", "wo", "ai", "is", "are", "was", "were", "has",
                            "have", "had", "could", "would", "should", "must", "need", "dare",
                            "does", "am", "might"))


def negator(word):
    """True when the word turns the next one round: "not", "didn't", "can't"."""
    plain = word.replace("'", "").replace("\u2019", "")
    if plain in NEGATORS:
        return True
    # "didnt" is "didn't", and only an auxiliary in front of the "nt" says so: see
    # CONTRACTED_AUX for why the "nt" alone is not enough.
    return len(plain) > 3 and plain.endswith("nt") and plain[:-2] in CONTRACTED_AUX


def turned(words):
    """True when these words turn the next one round: "not", "didn't", and also "can t",
    which is how a line that lost its apostrophe splits into two tokens."""
    for i, word in enumerate(words):
        if negator(word):
            return True
        if word == "t" and i and words[i - 1] in AUX:
            return True
    return False


# "I can't believe I finished it" is delight, not a denial of finishing it, so a can't/couldn't
# in front of a doubt word is an intensifier and the cue counts. A plain "not" or "don't" with
# "think" in front stays a real negation: "I don't think I'm happy" is not a happy line.
DOUBT = frozenset(("believe", "believed", "imagine", "imagined", "thought", "think"))
CANNOT = frozenset(("cant", "cannot", "couldnt", "never", "always"))


def turns_round(words):
    """True when these words (the ones just before a cue) turn it round.

    A doubt word after can't/couldn't/never/always is an intensifier, not a negation: "I can't
    believe I finished it" and "I never thought I'd be so happy" are delight. A plain "not"/"don't"
    before "think" stays a real negation ("I don't think I'm happy" is not a happy line), so
    "think" only counts after those four.
    """
    if not turned(words):
        return False
    plain = [word.replace("'", "").replace("\u2019", "") for word in words]
    if any(word in DOUBT for word in plain) and any(word in CANNOT for word in plain):
        return False
    return True


def negated(clean, phrase, window=3):
    """True when a negator stands just before the phrase: "im not feeling great".

    A phrase that opens with a negator is a shape of its own ("not ok" is a feeling), so it is
    left alone."""
    parts = phrase.split()
    if parts and negator(parts[0]):
        return False
    for match in re.finditer(r"\b" + re.escape(phrase) + r"\b", clean):
        if turns_round(clean[:match.start()].split()[-window:]):
            return True
    return False


def nearly(clean, phrase, window=2):
    """True when "nearly" or "almost" stands just before the phrase: "im almost happy".

    A thing nearly done is not done: "i nearly finished it" is not a result to congratulate, and
    "im almost happy" is not a claim to a happy line. It is left out rather than counted the
    other way, because "i almost won" is not bad news either."""
    parts = phrase.split()
    if parts and parts[0] in NEARLY:
        return False
    for match in re.finditer(r"\b" + re.escape(phrase) + r"\b", clean):
        if set(clean[:match.start()].split()[-window:]) & NEARLY:
            return True
    return False


# "I don't think I passed" and "I doubt I passed" are doubts, not results, and the negator sits
# further back than a cue's own window because a doubt word carries it. "I can't believe I
# passed" is the opposite - delight - so `turns_round` decides which of the two it is.
SURE = frozenset(("think", "thought", "know", "knew", "reckon", "guess", "suppose", "sure",
                  "expect", "imagine", "say", "believe", "believed", "certain"))
DOUBTED = frozenset(("doubt", "doubts", "doubted", "doubting", "unsure", "uncertain"))
# The verbs that take the news itself as their object ("believe it", "believe that"), so an "it"
# straight after them is the thing doubted rather than the claim.
BELIEVE_IT = frozenset(("believe", "believed"))


def doubted(clean, window=4):
    """True when the line only thinks, hopes or doubts what it says afterwards.

    Read before a result is congratulated, never after: "i dont think i passed", "i doubt i
    passed", "i dont think it went well". A doubt word alone is enough; a plain negator needs
    one of the asking words after it, so "i dont think i passed" is a doubt and "i cant believe
    i passed" stays a win.
    """
    plain = [word.strip(".,!?;:\"'").replace("\u2019", "") for word in str(clean).split()]
    if any(word in DOUBTED for word in plain):
        return True
    for i, word in enumerate(plain):
        if word not in SURE or not turns_round(plain[max(0, i - window):i]):
            continue
        if plain[i] in DOUBT and any(word in CANNOT for word in plain[max(0, i - window):i]):
            # "i cant believe i passed" - a cant in front of the verb is an intensifier, the
            # same reading `turns_round` makes for a cue it can see.
            continue
        if plain[i] in BELIEVE_IT and i + 1 < len(plain) and plain[i + 1] == "it":
            # "i dont believe it, i passed" is delight at the news, not a doubt about it: the
            # thing doubted is "it", not the result that follows. "i dont believe i passed"
            # has nothing after the verb, so the doubt is about the result and counts.
            continue
        return True
    return False


# A reply the bot has just given is the same sentence even when the person in it is named
# differently. Safety renders its pools after the draw ("stay with them" -> "stay with him"),
# so a plain string compare never sees the repeat and the window lets it through.
_PERSON_WORD = re.compile(
    r"\b(?:he|she|they|him|her|them|his|hers|their|himself|herself|themselves)\b", re.I)


def said_again(text):
    """The sentence with whoever it is about blanked, so two sayings of it compare equal."""
    return _PERSON_WORD.sub("@", " ".join(str(text or "").lower().split()))


_CAPITAL_I = re.compile(r"I(?:'|’|\b)")


# The hello already given, in the shapes a welcome uses: a reply that opens with one is not
# given a second.
_HELLO_OPENS = ("hi ", "hi,", "hello", "hey", "morning", "afternoon", "evening",
                "nice to meet", "good to meet")

# A reply that opens with a name or a place keeps its capital when a name goes in front of it:
# "Bristol — nice. How long have you been there?" lowered into "Hi Sam — bristol — nice" puts a
# small letter in a place name and one dash after another where a full stop belongs. Only a word
# that opens an ordinary sentence is lowered into the hello - and a word that is often a name too
# ("Rose", "Hope", "Mark") is deliberately left out, so a reply opening with one keeps its
# capital and takes the full stop.
_ONE_WORD_THEN_A_BREAK = re.compile(r"^([A-Za-z'\u2019-]{1,20})\s*(?:\u2014|--|-|\?|!|:|,)")
_OPENS_A_SENTENCE = frozenset("""
    a an the and but or nor so yet if then when while with without for from to of in on at by
    it its it's i i'm im you you're ur your yours he she they we us them there here this that
    these those what whats why how who whom where which yes no not never always often usually
    sometimes maybe perhaps probably honestly actually really just only also still even too
    one two three four five few some any all each both most many more less least enough
    good bad best worst great fine okay ok right well now today tonight tomorrow first next last
    check try keep stop start put take give get go going let leave look make use ask call add
    avoid buy clean cook cover cut drink eat drive hold pick raise read ring run say see set sit
    sort speak stick tell turn walk wash wear write fill fix top find change wait watch worth
    sounds looks seems sorry thanks thank please sorry glad sadly luckily hopefully
""".split())


def _opens_with_a_name(body):
    """True when the reply opens with a name or a place rather than a word that starts a sentence.

    Only the shape of a one-word opening followed by a break ("Bristol — nice", "Leeds? Good to
    know", "Biscuit — good name for a dog") is read this way. A reply that opens with an ordinary
    word keeps the hello's own dash and is lowered as before ("Hi Jess — most people who cannot
    sleep", "Hi Jim — the things that work").
    """
    match = _ONE_WORD_THEN_A_BREAK.match(str(body or "").strip())
    if not match:
        return False
    return match.group(1).lower().strip("'\u2019") not in _OPENS_A_SENTENCE


def greet_with(name, reply):
    """The answer to a line that introduced someone, with the hello in front of it.

    "hi im jess, i cant sleep" says two things: who they are and what they need. The welcome on
    its own answers neither ("Nice to meet you, Jess. What can I help with?"), and the answer on
    its own loses the name, so the answer is what is said, with the hello in front of it: "Hi
    Jess — most people who cannot sleep at this hour are still wound up from the evening." A
    reply that already opens with a hello is left alone, and so is an empty one.
    """
    if not name or not isinstance(reply, str) or not reply.strip():
        return reply
    body = reply.strip()
    plain = body.lower()
    if plain.startswith(_HELLO_OPENS) or plain.startswith("i'm " + str(name).lower()):
        return body
    name = str(name).strip()
    # The person's own voice keeps its capital ("I'm not sure about that one, sorry"); every
    # other sentence is part of the greeting and starts lower down.
    if _CAPITAL_I.match(body):
        return "Hi " + name + " — " + body
    if _opens_with_a_name(body):
        # "Bristol — nice" is a place, and a place does not lose its capital.
        return "Hi " + name + ". " + body
    return "Hi " + name + " — " + body[0].lower() + body[1:]


# A pool line that opens by asking about something only a question from the bot could have named:
# "Long one? Give yourself half an hour doing nothing", "Again? That's rough", "Been one of
# those? Park it for tonight". The fragment in front is the person's own words handed back or a
# reference to the thing the bot was asking about, and as the first thing said it is nonsense - "i
# feel tired" was answered "Long one? Give yourself half an hour doing nothing before the next
# thing", which is the reply to a question nobody asked. The words are looked for in the person's
# line and in the bot's last one, so the same shape is left alone where it does stand up: "Joined
# online? You have 14 days to cancel" is the answer to somebody who said they joined online.
OPENS_ON_A_FRAGMENT_QUESTION = re.compile(r"^\s*([A-Z][\w'\u2019]*(?:\s+[\w'\u2019]+){0,3})\?\s")
_NOT_A_FRAGMENT = frozenset("""what who why when where which how whatever honestly really
    sorry right ok okay so then and but well anyway""".split())


def _asks_about_a_thing_nobody_said(option, last, said):
    """True when a pool line opens on a fragment question about a thing neither side has named.

    A fragment is a question with no verb and no asking word in it ("Long one?", "Again?", "Been
    one of those?"), so it points at something already on the table. If the bot asked nothing and
    the person's line does not hold the words, there is nothing on the table and the line cannot
    be the reply - the pool has others that can open a conversation.
    """
    if last and str(last).strip().endswith("?"):
        return False  # the bot has just asked something, so a question back is fair
    match = OPENS_ON_A_FRAGMENT_QUESTION.match(str(option or ""))
    if not match:
        return False
    fragment = match.group(1)
    words = {w for w in re.findall(r"[a-z']+", fragment.lower()) if len(w) > 2}
    if not words or words & _NOT_A_FRAGMENT:
        return False
    heard = set(re.findall(r"[a-z']+", f"{last or ''} {said or ''}".lower()))
    return not (words & heard)


def pick(options, memory, seed_text=""):
    """One of options, never the reply just given, preferring one the bot has not said lately.

    `seed_text` is the user's line when the caller has it: two different lines answered from
    the same pool should not get the same sentence just because they are turn one of their
    conversation. Same line, same turn, same reply, so a run can be compared.
    """
    turns = memory.get("turns") or []
    last = turns[-1].get("bot") if turns and isinstance(turns[-1], dict) else None
    # A line that opens by asking about something nobody has said yet is not a line that can open
    # a conversation, so it is passed over while there is another one in the pool.
    standing = [o for o in options if not _asks_about_a_thing_nobody_said(o, last, seed_text)]
    if standing and len(standing) < len(options):
        options = standing
    # A pool's returning lines ("Hello again. What's next?", "Anything changed since we last
    # spoke?") speak about a chat that has happened. On the opening turn there is none, so they
    # are passed over for one that can open a conversation - the same reading the arbiter holds a
    # module's own reply to, so a pool line and a written-out line are judged alike.
    if not history.an_earlier_turn(memory):
        backed = [o for o in options if not history.a_past_that_is_not_there(o, memory)]
        if backed:
            options = backed
    # A pool no bigger than the window would empty, and emptying it put the whole pool back with
    # the reply just given in it: ten "ok"s in a row said one line twice running. Drop the reply
    # just given first, so an adjacent repeat cannot happen, then prefer an unseen one.
    fresh = [o for o in options if o != last] or list(options)
    # A reply this conversation has already had is not said again while there is another one to
    # say, however long ago it was: the window looked five turns back, so a bereavement chat said
    # "I'm so sorry to hear that. It's a hard thing to carry..." at turn one and again at turn
    # eight, seven turns after the first. Where every option has been said, the one said longest
    # ago is the least like a repeat of what is on the screen.
    said = {}
    for position, turn in enumerate(turns):
        if isinstance(turn, dict):
            said.setdefault(said_again(turn.get("bot")), position)
    unsaid = [o for o in fresh if said_again(o) not in said]
    if unsaid:
        fresh = unsaid
    else:
        oldest = min(said.get(said_again(o), -1) for o in fresh)
        fresh = [o for o in fresh if said.get(said_again(o), -1) == oldest]
    if seed_text:
        seed = len(turns) * 7919 + sum(ord(c) for c in str(seed_text))
    else:
        seed = len(turns)  # a caller without the line gets the same choice as before
    return random.Random(seed).choice(fresh)



def _name_just_given(memory):
    """The name the person gave in this very turn, plain, or "".

    The memory lane records every fact with the turn it was learned on, so an entry whose turn
    is this one is something the person has just said. This reads the store, not the words, so a
    name mentioned in passing ("my brother jess") is not a person introducing themselves.
    """
    if memory.get("aside"):
        # The line was put to the entries on its own account, with the chat left behind: a verdict
        # on the thing in hand read as a line of its own (`bot/memory/carry._a_fresh_memory`) or
        # the ask a correction meant (`bot/memory/repair`). Nobody is introducing themselves in
        # those, and the name in the store was given turns ago. Greeting there is worse than odd:
        # "is that dangerous" about a boiler the chat had answered at turn two came back as
        # "Hi Sam - top the pressure up to between 1 and 1.5 bar ...", the same paragraph with a
        # name in front, which also hid it from `carry._already_on_the_screen` (the opening no
        # longer matched) and put a paragraph already read out back on the screen.
        return ""
    log = memory.get("facts_log")
    if not isinstance(log, list):
        return ""
    turns = memory.get("turns")
    now = len(turns) if isinstance(turns, list) else 0
    for entry in reversed(log):
        if not isinstance(entry, dict) or entry.get("turn") != now:
            continue
        if entry.get("key") != "name":
            continue
        value = entry.get("value")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def with_name(reply, memory):
    """The answer the person is owed, with the name they just gave in front of it.

    "hi im sam, how do i bleed a radiator" has two halves and the two are answered by different
    things: the entry has the substance and the welcome has the person. Handing the turn to the
    welcome trades a real answer for "nice to meet you, Sam. What can I help with?", which fits
    any message and tells nobody anything (STYLE.md). So the name goes in front of the answer
    that won instead - "Hi Sam — radiators that are hot at the bottom ...".

    The hello and the name are `greet_with`'s, not this function's own wording: the same
    introduction reaches an answer by two roads (this one from an entry, and `chat.respond` from
    a line that greets and says something the chat module can answer), and two roads must not give
    a person two different greetings. "Jess — the things that work" and "Hi Jess — sorry to hear
    that" were both live, so the same introduction was answered in two shapes.

    This is called only where an entry has answered the line, so a reply coming back already
    means there was something to answer: a name said on its own ("hi im sam") never gets here,
    because the welcome takes that turn. Nothing is added either for a reply that already says
    the name, or on a turn where no name was given.
    """
    if not isinstance(reply, str) or not reply.strip():
        return reply
    name = _name_just_given(memory)
    if not name:
        return reply
    plain = " ".join(name.split())
    if not plain.isalpha() or len(plain) > 20:
        return reply
    # "nice to meet you, jess." already greets them, so the word is matched on its boundaries
    # rather than with spaces around it: a comma or a full stop after the name still counts.
    if re.search(r"\b" + re.escape(plain.lower()) + r"'?s?\b", reply.lower()):
        return reply
    return greet_with(plain.capitalize(), reply)


# A step asked for in as many words after the bot's own comfort line - "what should i do" after
# "want a hand working out the next step?" - is the person taking up the offer. The subject of
# that thread is how they feel, so there is nothing more concrete to be about than the first
# step of a bad day, and the hedge ("a quick search online will get you a solid answer") is the
# one reply that must never come back to it.
STEP_WHEN_LOW = (
    "Start with the smallest thing that would help: something to eat, a shower, ten minutes "
    "outside. One of those, and that is today's job.",
    "Write down the three things on your mind, then do the smallest one. The other two can wait "
    "an hour.",
    "Tell one person today \u2014 a friend, family, whoever is easiest \u2014 that it is a rough one. "
    "It weighs less once somebody else knows.",
    "If it has been like this for weeks rather than days, the GP is the practical step: that is "
    "what they are there for, and you do not have to explain it well.",
    "Do the small thing in front of you \u2014 the dishes, a walk, a shower. The push to do the next "
    "one comes after the first, not before.",
)
# A step ask with nothing after it: "what should i do", "what now", "where do i start", "so
# what should i do". One that names a thing of its own ("what should i do with the mince") is a
# subject question and belongs to whoever owns that subject.
A_STEP_ASK = re.compile(
    r"^\s*(?:so\s+|and\s+|ok(?:ay)?\s+|right\s+|well\s+)?"
    r"(?:what|where|how)\s+(?:should|do|can|could|shall|would)\s+(?:i|we)\s+"
    r"(?:do|start|begin|try|go|handle|sort|fix|deal)"
    r"(?:\s+(?:now|then|next|first|it|this|that|about it|about that|from here|today|tonight|at all))?"
    r"\s*[?.!]*\s*$"
    r"|^\s*(?:so\s+|and\s+|ok(?:ay)?\s+|right\s+)?what\s+(?:now|next)\s*[?.!]*\s*$"
    # "now what" is "what now" in the word order people actually type, and after the
    # bot's own comfort line the two got different replies: the step, or the search hedge.
    r"|^\s*(?:so\s+|and\s+|ok(?:ay)?\s+|right\s+)?now\s+what\s*[?.!]*\s*$"
    # "what helps" and "how do i feel better" are the same request as "what should i do" when
    # the bot has just answered a heavy feeling. Neither names a thing, so the step is the
    # answer; left out they reached the search hedge, which is the one reply that never helps.
    r"|^\s*(?:so\s+|and\s+|ok(?:ay)?\s+|right\s+)?(?:what|anything)\s+"
    r"(?:helps|would\s+help|can\s+help|might\s+help)\s*[?.!]*\s*$"
    r"|^\s*(?:so\s+|and\s+)?how\s+(?:do|can|could|should)\s+i\s+"
    r"(?:feel|get|make\s+myself\s+feel)\s+better\b[^?.!]*[?.!]*\s*$",
    re.IGNORECASE)


def _says_one_of(text, said):
    """True when the bot's last line says one of `said`, dressed up or not.

    A pool line rarely comes back bare: the greeting module puts the person's name in front
    ("Hi Eve \u2014 sorry to hear that. A walk and someone to talk to usually help more than
    sitting with it.") and `with_name` puts it there for an entry. Exact equality missed every
    one of those, so `hi im eve, im feeling really low` followed by `what should i do` still got
    the search hedge while the same pair without the name got a step. The line said is the
    thing that matters, not whether a name was said with it, so the pool line is looked for
    inside the reply - and case-folded, because the greeting in front of it drops the capital
    ("Hi Eve \u2014 sorry to hear that. A walk...").
    """
    flat = text.lower()
    return any(line and line.lower() in flat for line in said)


def step_when_low(clean, memory, comfort_said):
    """A next step for a bare "what should i do" after one of the bot's own comfort lines.

    `comfort_said` is the set of lines the calling composer can say as comfort, so each
    composer decides which of its own threads count. A step asked for anywhere else - after a
    recipe, a verdict, a safety line - is that thread's and this returns None.
    """
    if not A_STEP_ASK.match(str(clean or "").strip()):
        return None
    turns = memory.get("turns") or []
    turn = turns[-1] if turns and isinstance(turns[-1], dict) else {}
    last = (turn.get("bot") or "").strip()
    if not last or not _says_one_of(last, comfort_said):
        return None
    # The comfort line over news is not an offer about how they are feeling, so the first step of a
    # bad day is not the answer to the ask that follows it. "bailiffs turned up" then "what do i do"
    # was answered with "something to eat, a shower, ten minutes outside" while the door entry
    # beside it says what to do about the bailiffs. Stand down here, and the ask reaches whoever
    # read the news: the entry that answered it, or the ask pool when nothing did.
    # The one news that keeps the step is somebody leaving: that pool asks its own question ("what's
    # it like in the house?"), and the answer to it is "what do i do", which is the same hard day
    # going on - there the step is the reply, and "nothing in this to look up" is a shrug at a
    # marriage ending.
    try:
        from .badnews import (reads_as_a_leaving_already_gone, reads_as_a_reported_leaving,
                              reads_as_a_sacking, reads_as_bad_news, reads_as_the_leaving)
        said = " ".join(str(turn.get("user") or "").lower().split())
        # The carve-out below is for a partner leaving that has counsel of its own. A leaving
        # reported in the third person has none, and the ask after it got "something to eat, a
        # shower, ten minutes outside" where the ask reader had offered to work out the first
        # step: stand down here and the ask reaches that reader.
        if reads_as_a_reported_leaving(said):
            return None
        if (reads_as_bad_news(said)
                and not reads_as_the_leaving(said)
                and not reads_as_a_leaving_already_gone(said)
                and not reads_as_a_sacking(said)):
            return None
    except Exception:  # noqa: BLE001 - a reading that fails is a reading not made
        pass
    return pick(list(STEP_WHEN_LOW), memory, clean)
