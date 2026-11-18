"""One question back about a trouble, named, instead of a stall that fits any message.

The census turn (`notes/tools/stockline.py`) that leaves people nowhere is a plain statement of a
trouble with no card behind it:

    my airpods are not showing up          -> Got it. Is there anything you'd like a hand with?
    my electric blanket is smoking          -> the same stall, on main and after this change

The first is answerable with one question, and it is the same question for a boiler, a car
and a laptop: is it every time or only sometimes, and did anything change. A friend who cannot
see the thing asks that rather than "tell me more", because the answer decides what to ask next.

So the reply names the thing from the person's own line - one word of it, the most specific - and
asks one of the three questions a troubleshooter asks first. It holds no fact, so it cannot be
wrong, and it leaves the thread somewhere to go.

It is not for a decision ("im chucking up my evening class"), a feeling, or anything a card
answers: `A_TROUBLE` is the words that mean a thing is not doing its job, and the module stands
down unless the composer's own reply says nothing about the line.
"""
import re

from .aboutness import is_a_hedge as _a_hedge, restates_the_line, unlike_the_line

# A thing that is not doing its job. Deliberately about the machine, not the feeling: "im fed up
# with my job" is not a trouble to narrow down, and the care and work readers own those.
_VERBING = (r"(?:work\w*|show\w*|connect\w*|pair\w*|charg\w*|turn\w*|start\w*|boot\w*|"
           r"open\w*|load\w*|sync\w*|respond\w*|detect\w*|heat\w*|drain\w*|fill\w*|"
           r"print\w*|spin\w*|run\w*|play\w*|record\w*|boil\w*|flush\w*|close\w*|lock\w*|"
           r"los\w*|drop\w*|cut\w*|jamm\w*|fall\w*|slip\w*|stall\w*|stall?|squeal\w*|whistl\w*|"
           r"smell\w*|smoke|smoking|overheat\w*|beep\w*|go\w*|going|gone|drip\w*|clog\w*)")

# A thing not doing its job, as a phrase rather than a word: "not too far" is not a trouble, and
# neither is "she doesnt like chocolate" - both are about what somebody wants, and the detail
# reader above this one owns those.
A_TROUBLE = re.compile(
    r"(?:"
    r"\b(?:is\s+not|isn'?t|are\s+not|aren'?t|was\s+not|wasn'?t|does\s+not|doesn'?t|"
    r"do\s+not|don'?t|did\s+not|didn'?t)\s+" + _VERBING +
    r"|\b(?:wont|won'?t|will\s+not|wouldn'?t|refuses?\s+to)\s+" + _VERBING +
    r"|\b(?:keeps?|kept|stopped|stops)\s+" + _VERBING +
    r"|\b(?:is|are|it'?s)\s+(?:broken|bust|busted|dead|faulty|knackered|on\s+the\s+blink)\b"
    r"|\b(?:mak\w*|made)\s+(?:a\s+|an\s+|that\s+)?(?:noise|racket|din|humming|buzzing|whirring|clicking)\b"
    r"|\b(?:broke|broken|leaks?|leaking|leaked|stuck|sticking|noisy|noise|rattl\w*|slow|sluggish|"
    r"laggy|freez\w*|crash\w*|error|glitch\w*|bug|bugs|buggy|acting\s+up|playing\s+up|"
    r"gone\s+wrong|doing\s+something\s+weird)\b"
    r")", re.I)

# A person is not a machine, and neither is a marriage or a heart. "my son is dead" and "my
# marriage is dead" reached "is it every time, or only sometimes?" through the bare `is broken`
# arm; the loss and care readers own those lines.
NOT_A_MACHINE = re.compile(
    r"\b(?:son|daughter|child|kid|baby|mum|mom|mother|dad|father|wife|husband|partner|"
    r"boyfriend|girlfriend|brother|sister|friend|mate|nan|gran|grandad|grandma|aunt|uncle|"
    r"cousin|family|relationship|marriage|heart|trust|friendship|things)\b.{0,20}?"
    r"\b(?:is|are|was|were|it'?s)\s+(?:broken|bust|busted|dead|gone|over|finished|ruined)\b",
    re.I)

# A fire word is a hazard, not a fault to narrow down: "the hairdryer is sparking" gets neither a
# question about how often nor an echo. The safety lane owns it.
FIRE_WORD = re.compile(
    r"\b(?:spark\w*|scorch\w*|burn(?:s|ing|t)?|catch(?:es|ing)?\s+fire|flames?|"
    r"melt(?:s|ing|ed)?|fizz\w*|smoulder\w*)\b", re.I)

# The words that name what is wrong rather than what it is wrong with ("showing", "slow"), so a
# reply never says "Showing - is it every time, or only sometimes?".
_NOT_THE_THING = frozenset("""
working work works worked showing show shows shown connecting connected pairing paired
charging charged turning turned booting booted starting started opening opened loading loaded
syncing synced updating updated playing played running ran doing done going stuck slow
wrong broken bust faulty weird strange dead fine better worse again still always never
keep keeps kept isnt arent wasnt doesnt dont didnt wont wont stop stops stopped making makes
noise leaking leak making enough too quite really
today tonight tomorrow yesterday morning afternoon evening night daytime weekend now later
meantime outside indoors upstairs downstairs somewhere anywhere nowhere everywhere here there
""".split())

# The weather is not a thing that is not doing its job. "Its freezing out there today" matched the
# bare `freez\w*` arm and the only word left to name was "today", so the reply was "The today -
# every time, or only sometimes?" - a placeholder that reads as if the bot had misheard the line
# (own seed-3313 census, small-talk). A line about the weather has nothing in it to narrow down,
# and the composer's "Cold one. Thick socks make more difference than people expect." is the answer.
ITS_THE_WEATHER = re.compile(
    r"^\s*(?:oh\s+)?(?:it'?s|its|it\s+is)\s+(?:so\s+|very\s+|really\s+|properly\s+|"
    r"absolutely\s+|bloody\s+|still\s+|turned\s+|got\s+)?(?:freezing|boiling|roasting|baltic|"
    r"chilly|nippy|pouring|raining|snowing|sleeting|hailing|blowing|howling|mild|warm|hot|cold|"
    r"wet|dry|damp|dark|grey|gray|grim|miserable|lovely|nice|glorious)\b"
    r"|\bchucking\s+it\s+down\b|\bblowing\s+a\s+gale\b"
    r"|\brain(?:ing|y)\s+(?:again|all\s+day|now)\b", re.I)

# What a troubleshooter asks first, and what a friend asks instead of "tell me more".
_REPLIES = (
    "%s - every time, or only sometimes?",
    "Has anything changed since %s last worked - an update, a new one, a move?",
    "%s - how long has it been doing that?",
)

# The thing, with the words in front of it that make it a sentence: "my airpods" is what the
# person said, and "the airpods" is what the bot can say back without copying the whole line.
_DETERMINERS = ("my", "our", "the", "this", "that", "your", "his", "her", "their", "its")

# The words that do not name a thing at all, however many letters they have.
_FUNCTION = frozenset("""
the a an my our your his her their its this that these those that's thats some any something
anything nothing everything all most more less very just really quite still always never again
there here out up off down over back with without from than then about into onto and but so
when since while if or of to in on at for as it is are was were be been being got have has had
""".split())

# The words that come between the thing and what is wrong with it.
_STOP = frozenset("""
is are was were has have had wont will does doesnt didnt not never keeps kept still always
in on at to of for with and but so when since about all just really very much more less
isnt arent wasnt dont wont cant couldnt shouldnt wouldnt
""".split())


def the_thing(clean):
    """The most specific thing the line is about, with its determiner, or "" when there is none."""
    clean = str(clean or "")
    words = clean.split()
    # The words of the trouble itself are what is wrong, not what it is wrong with: "the start"
    # out of "my car wont start" is not a thing.
    spans = [(one.start(), one.end()) for one in A_TROUBLE.finditer(clean)]
    trouble_words = set()
    for start, end in spans:
        trouble_words.update(clean[start:end].split())
    found = [word for word in words
             if len(word) >= 3 and word not in _FUNCTION and word not in _NOT_THE_THING
             and word not in trouble_words
             and word.isalpha()]
    if not found:
        return ""
    return _named(clean, words, found, spans)


def _named(clean, words, found, spans):
    # The first thing named is the thing: "my car wont start in the cold" is about the car, not
    # about the cold, and "my washing machine" is two words of one thing.
    best = found[0]
    at = words.index(best)
    name = best
    after = words[at + 1] if at + 1 < len(words) else ""
    if (after and after.isalpha() and len(after) >= 4 and after in found
            and after not in _STOP):
        name = "%s %s" % (best, after)
    before = words[at - 1] if at else ""
    if before in _DETERMINERS:
        return "%s %s" % (before, name)
    return "the %s" % name


def _heavy(memory):
    """True when the thread is heavy news, read through the composer's own test for it."""
    from . import fallback as _fallback
    turns = list((memory or {}).get("turns") or [])
    if not turns:
        return False
    return bool(_fallback.reads_as_heavy_news(" ".join(str(turns[-1].get("user") or "").split()))
                or _fallback._the_thread_is_heavy({"turns": turns}))


def trouble_pool(clean, memory):
    """The one question this trouble raises, or None when this is not a trouble."""
    clean = " ".join(str(clean or "").lower().split())
    if _heavy(memory):
        return None  # the care readers own a heavy thread, whatever the line says
    from . import fallback as _fallback
    if _fallback.reads_as_heavy_news(clean):
        return None  # and they own a heavy line on its own, before there is any thread
    if NOT_A_MACHINE.search(clean) or FIRE_WORD.search(clean):
        return None  # a person or a hazard, not a thing that is not doing its job
    if ITS_THE_WEATHER.search(clean):
        return None  # the weather is no fault of anything, and "today" is not the thing it is wrong with
    if not clean or "?" in clean or len(clean.split()) < 3:
        return None  # a question has its own answers; a bare word names nothing to ask about
    if not A_TROUBLE.search(clean):
        return None
    thing = the_thing(clean)
    if not thing:
        return None
    pool = tuple((line % thing)[0].upper() + (line % thing)[1:] for line in _REPLIES)
    return pool if all(2 < len(line.split()) < 22 for line in pool) else None


# A placeholder is short. Anything longer than this is an answer of its own, and the reader has no
# business taking its turn however few of the line's words it happens to share.
_STOCK_LENGTH = 14

# A reply that is already narrowing the trouble down is one to leave alone: "Annoying. Is it every
# time, or only now and then?" is the same question this module would ask, asked better, because
# the composer said it in its own voice. Only a stall, a hedge or the line given back is replaced.
_ALREADY_NARROWING = re.compile(
    r"\b(?:every\s+time|now\s+and\s+then|now\s+and\s+again|when\s+did\s+it\s+start|"
    r"how\s+long\s+has|what\s+does\s+it\s+do|what'?s\s+it\s+doing|what\s+happens\s+when|"
    r"what\s+were\s+you\s+doing|since\s+when|what\s+it\s+does|what\s+have\s+you\s+tried|"
    r"tell\s+me\s+what|say\s+more)\b", re.I)


# "Is there anything you'd like a hand with?" is a question with nothing in it; any other question
# is the composer asking something of its own, and replacing it loses the answer.
_A_BARE_OFFER = re.compile(
    r"^\s*(?:got it[.,]?\s*|okay[.,]?\s*|right[.,]?\s*)?"
    r"(?:is\s+there\s+anything|anything\s+else|what\s+else|can\s+i\s+help)", re.I)


def _a_bare_offer(reply):
    return bool(_A_BARE_OFFER.search(str(reply or "")))


# The bot's own things to say when it has nothing to say: "I'm listening - say more if it helps",
# "Got it. Is there anything you'd like a hand with?". They fit any message, so a line that is one
# of these is the placeholder this reader exists for, whatever else the reply contains.
STALL = re.compile(
    r"(?:\bi'?m listening\b|\bsay more if it helps\b|\btell me more\b|"
    r"\banything you'?d like a hand with\b|\bwhat'?s on your mind\b|"
    r"\bi'?m here if you want to\b)", re.I)


def says_nothing_about_the_line(reply, text):
    """True when the composer's own reply is a hedge, the line given back, or a stock line."""
    reply = str(reply or "").replace("\u2019", "'")
    if not reply.strip():
        return True
    if STALL.search(reply):
        return True  # a stall is a stall however long it is: "Thanks for telling me - I'm here if
        # you want to dig into any of that" is sixteen words of nothing
    if len(reply.split()) > _STOCK_LENGTH:
        return False  # a real answer, however it is worded; only a short line is a placeholder
    if reply.rstrip().endswith("?") and not _a_bare_offer(reply):
        return False  # a question of its own already moves the thread along
    if _ALREADY_NARROWING.search(reply):
        return False  # a question about the trouble is already an answer to it
    if _a_hedge(reply) or restates_the_line(reply, text):
        return True
    about, said = unlike_the_line(reply, text)
    return bool(about) and not said
