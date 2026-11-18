"""A taste of their own, said plainly, gets a reply that answers back.

People say what they like and what they cannot stand in the middle of a conversation, usually as
a line on its own: "i love thai food", "i really like jazz", "im not a fan of football", "i cant
stand mushrooms". No module reads them, so they reach the composer, and the composer hands the
sentence back with a receipt on it:

    i love thai food            -> "Got it — you love thai food."
    i like a girl at work       -> "Noted: you like a girl at work."
    i really like jazz          -> nothing at all from any module above the composer

A friend does not hand a person their own sentence. They say what they think of the thing
("Can't argue with thai food"), and then ask the one thing only the person can answer: what got
them into it, how often they get it, what it is about it they like. That is all this module does,
for a like and for a dislike, because the two take different lines.

Only a whole line is one of these: the taste has to be the line and not the beginning of a story
("i love thai food but it's so expensive to make" is a story with a taste in it). A thing that is
a person ("i like a girl at work", "i love you"), a thing that is the bot's own, or a word that
stands in for a thing ("i love it here", "i like that") is not a taste this can answer, and
neither is a line about their own life going wrong ("i hate my life", "i hate my job" after "my
boss has it in for me") - those keep whatever turn they have. A taste said straight after heavy
news is not a question back, either: the module stands down for the turn before.
"""
import re

from ..compose import fallback, pick
try:  # the step that does not lean on the thing they have just said they cannot stand
    from ..memory import obstacle as _obstacle
except Exception:  # noqa: BLE001 - a reading that cannot be imported just adds no guard
    _obstacle = None

# The band just above the composer (-1000) and below every module that has something of its own
# to say (`nudge` -950, `urgent` -900, `invitation` -500, `ruled_out` -450). A taste is answered
# here only where the reply would otherwise be the person's own sentence handed back, so this is
# a fallback and it is placed with the fallbacks.
PRIORITY = -960

# What they like. Three lines each, so a person who names two liked things does not hear the same
# sentence twice, and so that a thread coming back to the same taste has something new.
# Every line has to fit *any* noun, because `_THING` takes one to five words of anything: the thing
# can be a food, a band, a season, a room or a silence. "What got you into it?" and "How often do
# you get it?" read a taste as an activity, and said to "i love christmas" or "i love silence" they
# are worse than the receipt they replace - a receipt is dead, a wrong question is not. So the
# question is always about the liking, never about when or how they came to it.
#
# The thing is named again rather than picked up with a pronoun: "olives" is plural and "it" reads
# wrong after it, and a line cannot know which of the two it has.
_LIKES = (
    "Can't argue with {thing}. What do you like most?",
    "{Thing} - good taste. What is it about {thing} that you like?",
    "That is a good thing to like. What do you like most about {thing}?",
)

# What they cannot stand. The same shape, and a different thing to ask: a dislike is not a
# request to be talked round, so the line takes it as reasonable and asks what it is.
_DISLIKES = (
    "{Thing} - fair enough. What is it you don't like about {thing}?",
    "Nobody is going to talk you round on {thing}, and nobody needs to. What is it that puts "
    "you off?",
    "Plenty of people would say the same about {thing}. What is it you cannot take about {thing}?",
)

# The verbs, longest first, so "i really like" is not read as "i like" with a word in front.
_LIKE_VERBS = (
    "really like", "do like", "love", "like", "adore", "am mad about", "m mad about",
    "am into", "m into", "can't get enough of", "cant get enough of", "can not get enough of",
    "am a fan of", "m a fan of", "am obsessed with", "m obsessed with", "have always loved",
)
_DISLIKE_VERBS = (
    "really don't like", "really dont like", "don't like", "dont like", "hate", "dislike",
    "can't stand", "cant stand", "can not stand", "am not a fan of", "m not a fan of",
    "am not keen on", "m not keen on", "have never liked", "have gone off",
    # "i am sick of X" and "i am fed up of X" are not tastes: they are a person at the end of
    # something ("im sick of all this" is a hard week, not a dislike of a thing), and they keep
    # whatever turn they have.
)
# "... fan of" takes an adjective between the two words often enough that it cannot be a list:
# "i am a massive fan of soup", "i am a big fan of cricket", "im a proper fan of dolly parton".
_FAN_OF = re.compile(
    r"(?:am|m)\s+(?:a\s+)?(?:\w+\s+){0,2}fan\s+of", re.I)
# A word that ends the taste and adds nothing to it: "i love thai food tbh".
_TONE = re.compile(
    r"(?:\s+(?:tbh|tho|though|really|honestly|actually|literally|so\s+much|a\s+lot|"
    r"as\s+well|too|now|anyway|i\s+suppose|i\s+guess|lol|ha|haha|btw|atm|lately|"
    r"these\s+days|at\s+the\s+moment|right\s+now|still|again))+$", re.I)
# A word in front of the taste that is the person clearing their throat: "god i love thai food".
_LEAD = r"(?:(?:oh|god|god,|honestly|yeah|well|actually|man|christ|jesus|blimey)\s+)*"
# The taste itself: one to five words, letters only, so a clause is not swallowed into it.
_THING = re.compile(r"^(?P<thing>[a-z][a-z'\-]*(?:\s+[a-z][a-z'\-]*){0,4})$")
# A word that stands in for a thing: the bot has to know the thing to say anything about it.
_NOT_A_THING = frozenset((
    "it", "that", "this", "them", "these", "those", "him", "her", "you", "me", "us", "here",
    "there", "everything", "anything", "nothing", "everyone", "someone", "it all", "that one",
    "this one", "one", "ones", "things", "stuff", "life", "my life", "myself", "my job",
    "my work", "people", "the world", "the news", "him too", "her too", "your advice", "advice",
    "your help", "this recipe", "the recipe", "your recipes", "this place", "this app",
    "chatting to you", "talking to you", "you too", "you both", "your voice",
    # "i cant stand much more of this" is a person at the end of their tether, not a dislike of a
    # thing, and it is the last line to answer with a question about the thing.
    "much more of this", "more of this", "much more", "any more of this", "it any more",
    "it anymore", "this any more", "this anymore",
))
# A person and not a thing: a taste in somebody is its own conversation, with its own lines.
_A_PERSON = re.compile(
    r"\b(?:girl|boy|woman|man|guy|lad|lass|bloke|fella|someone|somebody|people|person|"
    r"her|him|them|she|he|they)\b", re.I)
# A thing can be theirs and still be a thing: "i love my bed", "i like my house", "i love my new
# kitchen". What cannot be is somebody else - a partner, a child, a pet - or a word for their own
# life, because those are the store's business or the day's, not a taste of a thing. The fence is
# on who could be meant, not on the "my".
_THEIRS_BUT_NOT_A_THING = re.compile(
    r"\b(?:mum|mom|mother|dad|father|son|daughter|kid|kids|child|children|wife|husband|partner|"
    r"baby|gran|grandma|grandmother|nan|nana|grandad|grandpa|grandfather|aunt|uncle|cousin|"
    r"sister|brother|parents|family|dog|cat|puppy|kitten|pets?|bird|horse|rabbit|hamster|"
    r"boss|friend|mate|neighbours?|self|life|job|work|body|looks|health|mind|sleep)\b", re.I)
# A word of their own life going wrong behind "i hate": that is not a taste, it is the day.
_NOT_A_TASTE = re.compile(
    r"\b(?:my life|myself|my job|my work|my body|my looks|the world|people|mondays?\s+morning)\b",
    re.I)

# The subjects a taste can be said with, and only these: "my wife loves jazz" is about her and
# belongs to the module that answers a fact about one of theirs. "im" and "ive" are how people
# type, so they are read as "i'm" and "i've".
_I_SAY = r"^(?:i|i'm|i've)\s+"
_TYPED = (("im ", "i am "), ("i m ", "i am "), ("ive ", "i have "))

# Where a taste turns into a story: any of these after it means the line goes on.
_STORY = re.compile(
    r"\b(?:but|because|so|though|although|when|whenever|if|since|which|that|keeps?|"
    r"makes?|gets?|goes?|go|went|got|costs?|cost|is|are|was|were|will|would|can|could|"
    r"have|has|had|need|needs|want|wants|helps?|works?|tastes?|smells?)\b"
    # "and" joins two things as often as it starts a clause: "black and white films" is one thing
    # and "i love jazz and i play it too" is a story, so "and" only counts before a person or a
    # pronoun that begins the rest of the sentence.
    r"|\band\s+(?:i|it|its|it's|they|we|you|he|she|there|thats|that's)\b", re.I)

# The line before, when it is heavy news: a taste answered with a question straight after "my
# mum has dementia" reads as not listening. The composer's own reading, plus the plainer words
# people use ("my friend is very ill", "my son is being bullied") that it does not read.
_HEAVY = re.compile(
    r"\b(?:ill|unwell|poorly|sick|dying|died|death|passed away|funeral|bereave\w*|griev\w*|"
    r"cancer|chemo\w*|radiotherap\w*|tumou?r|dementia|alzheim\w*|stroke|sepsis|surgery|"
    r"operation|transplant|hospice|palliative|terminal|hospital|icu|ambulance|diagnos\w*|"
    r"bully\w*|bullied|depress\w*|suicid\w*|self harm|miscarr\w*|stillborn|addict\w*|"
    r"relapse\w*|overdose\w*|sectioned|in pain|suffering)\b", re.I)


# What the composer writes when it has nothing to say: the person's own sentence handed back
# (`FRAMES` in bot/memory/ack.py), a listening line, or a hedge. On any of those the turn is this
# module's; on anything else the composer has a line of its own and keeps it ("im into climbing"
# is answered "How's climbing treating you?", which is better than any pool here).
_PLACEHOLDER_OPENINGS = (
    "noted", "got it", "i'm listening", "i am listening", "thanks for telling me",
    "that's noted", "thats noted", "ok.", "okay.", "i don't know enough",
    "i dont know enough", "that's beyond what i know", "thats beyond what i know",
    "i'm not sure about that one", "im not sure about that one",
)


def _the_composer_would_answer(text, memory):
    """True when the composer has a line of its own for this line, rather than a placeholder."""
    try:
        reply = fallback.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a composer that cannot be asked claims nothing
        return False
    said = " ".join(str(reply or "").lower().split())
    if not said:
        return False
    if any(said.startswith(opening) for opening in _PLACEHOLDER_OPENINGS):
        return False
    return True


def _the_greeting_would_answer(text, memory):
    """True when the band below this module has a line of its own, rather than a placeholder.

    `fallback.reply_for` is not the whole floor. `greeting` sits one band down and has a reader of
    its own for a taste which names the thing and asks about it in the person's own terms - "Ah,
    thai food. What got you into that?", "Your new flat - I can see why. What do you like most
    about it?", "The sea, nice one. What is the draw for you?". Asking only the composer meant a
    tailored line was replaced by one of three templates: a receipt is dead, but a flat template
    over a good line is worse, and it is the same mistake in the other direction.

    The receipts it also gives ("Noted: you love thai food") are the placeholder openings above,
    so those still stand this module up.
    """
    try:
        from . import greeting
    except Exception:  # noqa: BLE001 - a band that cannot be imported claims nothing
        return False
    try:
        reply = greeting.respond(text, memory)
    except Exception:  # noqa: BLE001 - a reading that fails leaves the line to this module
        return False
    said = " ".join(str(reply or "").lower().split())
    if not said:
        return False
    if any(said.startswith(opening) for opening in _PLACEHOLDER_OPENINGS):
        return False
    return True


def _the_line_before(memory):
    """What the person said on the turn before this one, or "" on the first turn."""
    turns = [turn for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)]
    return str(turns[-1].get("user") or "") if turns else ""


def _the_thread_is_heavy(memory):
    """True when the turn before this one was heavy news rather than ordinary talk."""
    before = _the_line_before(memory)
    if not before:
        return False
    try:
        if fallback._reads_as_heavy_news(before):
            return True
    except Exception:  # noqa: BLE001 - a composer that cannot be asked is not a reason to fail
        pass
    return bool(_HEAVY.search(before))


def _said_plainly(clean):
    """The line without the throat-clearing and the trailing tone words."""
    said = clean
    for typed, proper in _TYPED:
        if said.startswith(typed):
            said = proper + said[len(typed):]
    said = re.sub(r"^" + _LEAD, "", said)
    changed = True
    while changed:
        stripped = _TONE.sub("", said)
        changed = stripped != said
        said = stripped
    return said.strip()


def _a_taste(clean):
    """(kind, the thing as they said it) for a line that is a taste on its own, or None."""
    if not clean or "?" in clean:
        return None
    for kind, verbs, pool in (("like", _LIKE_VERBS, _LIKES), ("dislike", _DISLIKE_VERBS, _DISLIKES)):
        for verb in verbs + (_FAN_OF.pattern,):
            head = _I_SAY + (verb if verb is _FAN_OF.pattern else re.escape(verb)) + r"\s+"
            match = re.match(head, clean, re.I)
            if not match:
                continue
            rest = clean[match.end():].strip()
            if not rest or _STORY.search(rest):
                continue
            thing = _THING.match(rest)
            if not thing:
                continue
            rest = thing.group("thing")
            if rest in _NOT_A_THING or _A_PERSON.search(rest):
                continue
            if kind == "dislike" and _NOT_A_TASTE.search(rest):
                continue
            # A thing they own, an infinitive, or a place held by a word that stands for one: none
            # of them is a thing the bot can say anything about ("i love my new kitchen", "i like
            # to swim", "i love it here").
            first = rest.split()[0]
            if first in ("to", "your", "our", "it", "that", "this", "them", "here", "there"):
                continue
            if first == "my":
                held = rest[3:].strip()
                if not held or _THEIRS_BUT_NOT_A_THING.search(held):
                    continue
            # "i love it" and "i love your advice" are in _NOT_A_THING, but a thing of the bot's
            # own can carry a word in front of it: "i love this recipe" is not a taste either.
            if re.match(r"^(?:your|this|that|these|those)\s+", rest):
                continue
            return kind, rest
    return None


def _the_thing_said(thing):
    """The thing in the person's own words, with their "my" turned round."""
    words = thing.split()
    if words and words[0] == "my":
        words[0] = "your"
    return " ".join(words)


def _pick(pool, memory, said):
    """One line of the pool, seeded by the person's line and never the one just given.

    The composer's own pick is used rather than the first unseen line, because a pool of three
    read out in order means every person who says a taste on their first turn gets the same
    sentence: eleven deck chats changed to "Can't argue with ...", word for word.
    """
    return pick(pool, memory, said or "")


def _the_reply(kind, thing, memory):
    thing = _the_thing_said(thing)
    pool = _LIKES if kind == "like" else _DISLIKES
    line = _pick(pool, memory, " ".join(str(thing).split()))
    return line.replace("{Thing}", thing[:1].upper() + thing[1:]).replace("{thing}", thing)


def respond(text, memory):
    """The line, when it is a taste on its own and the thread is not a heavy one."""
    if not isinstance(text, str):
        return None
    clean = _said_plainly(" ".join(text.lower().split()))
    if not clean or "?" in clean:
        return None
    taste = _a_taste(clean)
    if not taste:
        return None
    if not isinstance(memory, dict):
        memory = {}
    if _the_thread_is_heavy(memory):
        return None
    # The composer's own line for the thing the last answer leaned on ("i hate exercise" after a
    # plan for losing weight) is written by the module below this one, and it is the better
    # answer: a taste is not a request to be talked round, but this one is about the advice.
    if _obstacle is not None:
        try:
            if _obstacle.answer_for(text, memory):
                return None
        except Exception:  # noqa: BLE001 - a reading that cannot be asked adds no guard
            pass
    if _the_composer_would_answer(text, memory):
        return None
    if _the_greeting_would_answer(text, memory):
        return None
    kind, thing = taste
    return _the_reply(kind, thing, memory)
