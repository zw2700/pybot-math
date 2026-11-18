"""A line that says it does not want advice wants to be heard, not fixed.

Nobody types "and i dont want advice" to a machine unless they have had advice they did not ask
for, and the worst thing to do with it is hand them a card. Yet every one of these reached a card
or a search pointer:

    my son was in an accident and i dont want advice     -> "a search should sort you out"
    my dog is ill and i dont want advice                 -> "What would help most right now?"
    i dont want advice, i just want to talk              -> "That's beyond what I know well"
    not looking for a solution, just want to know what you think
                                                         -> the chemistry definition of a solution
    i dont need advice, just someone to listen           -> a card about listening to people
    im not looking for advice, only to say it out loud   -> "I'm not sure about that one"
    i know what to do, i just wanted to tell someone     -> a place to visit

The words of the line are the words of the thing they do not want, so each of them was a lookup
that found exactly the wrong entry. Nothing about it is a question to look up. What the bot knows
is the shape of the turn itself: somebody is telling it something, and the useful reply is to say
they have been heard and make it easy to go on - no advice, no card, and no "search for it".

Two shapes, because they ask for different things. Most decline the fixing altogether. A few
decline the fix and ask for a view instead ("just want to know what you think"), and a view is
something the bot can give once it knows the situation, so that shape asks for the situation.

The matcher needs a decline, in the same clause as the thing declined, so a line that asks for
advice keeps its answer ("what advice would you give my sister", "should i take advice from a
broker"), and "i dont want to give advice" - about somebody else - is not this line either.
"""
import re

# The thing declined, named as people name it. "help" alone is left out on purpose: "i dont want
# help getting up the stairs" is a fact about their knees, not a turn about being heard.
_DECLINED_LITERAL = (r"(?:advice|advise|solutions?|tips?|suggestions?|a\s+lecture|"
                     r"lectures?|to\s+be\s+told\s+what\s+to\s+do|"
                     r"telling\s+me\s+what\s+to\s+do)")

# "i dont want advice", "im not asking for advice", "no advice please", "dont give me advice",
# "without advice", "no solutions thanks", "i didnt ask for advice".
_NO_ADVICE = re.compile(
    r"\b(?:(?:i|we|he|she|they)\s+(?:dont|don't|do\s+not|doesnt|doesn't|didnt|didn't|"
    r"wouldnt|wouldn't)\s+(?:really\s+|actually\s+|even\s+)?"
    r"(?:want|need|wanted|needed|asked\s+for|ask\s+for)\s+"
    r"(?:(?:any|no|your|more|further|the|medical|financial|legal|diet|parenting|career)\s+){0,2}"
    r"(?:" + _DECLINED_LITERAL + r")|"
    r"(?:i|we|im|i'm)\s+(?:am\s+)?(?:not|n't)\s+(?:looking|asking|after|here)\s+for\s+"
    r"(?:a\s+|any\s+|the\s+)?(?:advice|solutions?|fix|fixing|tips?|suggestions?)|"
    r"(?:not|n't)\s+looking\s+for\s+(?:a\s+|any\s+)?(?:solution|advice|fix)|"
    r"no\s+(?:advice|solutions?|tips?|lectures?)(?:\s+(?:please|thanks|thank\s+you))?|"
    r"without\s+(?:the\s+)?(?:advice|lecture|tips)|"
    r"(?:dont|don't|do\s+not|no)\s+(?:give|giving)\s+me\s+(?:any\s+)?(?:advice|tips)|"
    r"not\s+(?:asking|looking)\s+for\s+(?:advice|a\s+solution)|"
    r"(?:dont|don't|do\s+not|stop)\s+tell(?:ing)?\s+me\s+what\s+to\s+do|"
    r"(?:i|i've|ive)\s+(?:already\s+)?know\s+what\s+to\s+do,\s+(?:i\s+)?(?:just|only)\s+"
    r"(?:want|wanted|need|needed))\b", re.I)

# The same turn said as what they do want instead, with nothing about advice in it: "i just want
# to talk", "just want to vent", "only wanted to say it out loud", "i just need to get this off my
# chest". These are the lines whose whole content is "listen to me". What they want to say is named
# as a thing ("say it", "say this"), never as a courtesy: "i just want to say thank you" and "i
# wanted to tell you about my day" are their own turns and keep their own answer.
_WANT_TO_BE_HEARD = re.compile(
    r"\b(?:(?:just|only|really)\s+(?:want|wanted|need|needed)\s+(?:to\s+)?"
    r"(?:talk|vent|be\s+heard|get\s+(?:it|this|that|something)\s+off\s+(?:my|our)\s+chest)|"
    r"(?:just|only)\s+(?:wanted|want|needed)\s+to\s+(?:say\s+(?:it|this|that|something)|"
    r"tell\s+(?:you|u|someone|somebody|them|him|her)\s+something)|"
    r"(?:just|only)\s+(?:wanted|want)\s+(?:to\s+)?(?:say|tell)\s+(?:it\s+)?out\s+loud|"
    r"wanted\s+to\s+say\s+it\s+out\s+loud|"
    r"i\s+(?:just\s+)?(?:want|wanted)\s+to\s+be\s+heard|"
    r"(?:just\s+|only\s+)?(?:want|wanted|need|needed)\s+(?:someone|somebody|a\s+person)\s+"
    r"(?:who\s+)?(?:to\s+)?listen|"
    r"just\s+(?:talk|listen)\s+to\s+me|"
    r"(?:let|allow)\s+me\s+(?:to\s+)?(?:talk|vent|rant)|"
    r"(?:just\s+|only\s+)?(?:want|need|wanted|needed)\s+to\s+(?:vent|rant)|"
    r"can\s+i\s+(?:just\s+)?(?:vent|rant)|"
    r"i\s+need\s+(?:a\s+)?(?:vent|rant)|"
    r"can\s+i\s+just\s+talk)\b", re.I)

# "just listen" is a request only as the end of the line: "i just listen to my doctor and it works"
# and "i only listen to my gut" are statements about what the person does, and the listening line
# was answering them. A request puts it last ("...just listen", "just listen to me", "just listen
# please"), which is where the anchored pattern looks.
_JUST_LISTEN = re.compile(r"\b(?:just|only)\s+listen(?:\s+to\s+me)?(?:\s+please)?\s*[.!]*$",
                          re.I)

# A line that declines the fix but asks for a view. "not looking for a solution, just want to
# know what you think" is the example; "what would you do" and "your honest opinion" are the same
# ask. It is not advice if the person has asked for it.
_ASKS_A_VIEW = re.compile(
    r"\b(?:what\s+(?:do\s+)?(?:you|u)\s+(?:think|reckon|make\s+of\s+it)|"
    r"whats\s+your\s+(?:honest\s+)?(?:opinion|view|take)|what\s+is\s+your\s+(?:opinion|view|take)|"
    r"your\s+honest\s+opinion|your\s+view\s+on\s+it|"
    r"(?:must|would\s+you)\s+think\s+of\s+me|does\s+that\s+(?:sound|seem)\s+?"
    r"(?:mad|silly|wrong|bad)|am\s+i\s+(?:being\s+)?(?:mad|silly|wrong|unreasonable))\b", re.I)

# Somebody else's advice, or a question about whether to take advice: "i dont want to give
# advice to my friend" is about the friend, and "should i take advice from a broker" is the
# broker's line. The decline there is not about this bot's answer, so these keep their own reply.
_NOT_THIS = re.compile(
    r"\b(?:what|some|good|the\s+best|better)\s+advice\b|"
    r"should\s+i\s+take\s+(?:her|his|their|my|any|some)\s+advice|"
    r"(?:give|giving|offer|offering)\s+(?:her|him|them|my|his|your)\s+advice|"
    r"(?:dont|don't|do\s+not)\s+want\s+to\s+give|"
    r"asked\s+(?:for|about)\s+(?:her|his|their|my)\s+advice", re.I)

# The same line carrying a question of its own: "i dont want advice about my pension, what should
# i do" declines the pension card and then asks for it. Two things, and the second is the ask, so
# the tune about being heard would drop it. A question anywhere in the line is enough - the line
# that only declines advice has none.
_AN_ASK = re.compile(
    r"(?:\b(?:what|how|which|when|where|who|why|should|could|would|can|is|are|does|do)\b"
    r"[^?.!]{0,60}\?|\b(?:what|how|which|where|who)\b\s+(?:do|should|can|could|would)\b|"
    r"\bwhats\b|\bwhat's\b|\bshould\s+i\b|\bcan\s+i\b|\bcould\s+i\b)", re.I)


# Anything asked after the decline belongs to the person, not to the turn about being heard:
# "no advice, what time does the pharmacy shut" is a question with a decline in front of it, and
# handing it the listening line loses the hours. So the ask test is on what is LEFT of the line
# once the decline is taken out, not on the line as a whole.
_A_DECLINE = re.compile(
    r"(?:%s)|(?:%s)|(?:%s)" % (_NO_ADVICE.pattern, _WANT_TO_BE_HEARD.pattern, _JUST_LISTEN.pattern),
    re.I)
# What an ask looks like in the tail. Wider than _AN_ASK on purpose: an interrogative anywhere in
# what is left is an ask ("what time does the pharmacy shut" has no "what do" in it), and so is a
# wish to be told something ("i want to know if its normal to feel like this").
_AN_ASK_LATER = re.compile(
    r"\b(?:what|whats|what's|how|which|when|where|who|why|should|could|would|can|is|are|was|"
    r"were|do|does|did|will|want\s+to\s+know|wondering|wonder\s+if|"
    r"tell\s+me\s+(?:if|whether|what|how)|let\s+me\s+know\s+(?:if|whether|what|how))\b",
    re.I)
# The tail that is not an ask even though it has an asking word in it: "i just want to talk about
# my mum, is that ok" is the turn about being heard with a check on the end of it.
_NOT_AN_ASK = re.compile(
    r"\b(?:is\s+that\s+(?:ok|okay|alright|fine)|if\s+thats?\s+(?:ok|okay|alright|fine)|"
    r"does\s+that\s+make\s+sense|is\s+that\s+alright\s+with\s+you)\b", re.I)


def _what_is_left_after_the_decline(line):
    """The rest of the line once the decline is taken out of it."""
    said = _A_DECLINE.search(line)
    if not said:
        return line
    return line[said.end():]


def asks_something_of_its_own(line):
    """True when the line asks something besides the decline, so the ask is the turn."""
    left = _NOT_AN_ASK.sub(" ", _what_is_left_after_the_decline(line))
    return bool(_AN_ASK_LATER.search(left))


# A death in the line is a death however the rest of it is put, and the module that reads a loss
# has the better answer: "my mum died and i dont want advice" is not a line to meet with "go on,
# I'm listening". Read narrowly on purpose - "i lost my job" and "missing my sister" are the same
# words without a death in them, and those lines belong here.
A_DEATH = re.compile(
    r"\b(?:died|dying|dead|death|killed|suicide|passed\s+away|passed\s+on|funeral|burial|"
    r"cremation|took\s+(?:his|her|their)\s+own\s+life|"
    r"buried|burying|bereav\w*|grief|grieving|widow|widowed|mourning)\b|"
    r"\b(?:lost|bury|lose|losing)\s+(?:my|our|her|his|their|the)?\s*(?:mum|mom|mother|dad|father|"
    r"wife|husband|baby|child|son|daughter|brother|sister|partner|gran|granny|nan|grandad|"
    r"grandpa|friend|mate)\b", re.I)


def _plain(text):
    return " ".join((text or "").split())


def says_a_death(text):
    """True when the line carries a death, so a loss reader has the better answer."""
    return bool(A_DEATH.search(_plain(text)))


def asks_for_a_view(text):
    """True when the same line asks for the bot's view instead of a fix."""
    return bool(_ASKS_A_VIEW.search(_plain(text)))


def says_no_advice(text):
    """True when the line declines advice, or asks only to be heard."""
    line = _plain(text)
    if not line:
        return False
    said = bool(_NO_ADVICE.search(line) or _WANT_TO_BE_HEARD.search(line)
                or _JUST_LISTEN.search(line))
    if not said:
        return False
    if asks_for_a_view(line):
        # "not looking for a solution, just want to know what you think": the view was asked for,
        # so the bot gives one - after it knows the situation.
        return True
    if _NOT_THIS.search(line):
        # The word belongs to somebody else, or the line asks about advice rather than declining
        # it: the decline is not on this turn.
        return False
    # "can i just vent" is a request to be heard and it has an asking word in it, so the wants are
    # taken out before the line is read for a question of its own.
    rest = _JUST_LISTEN.sub(" ", _WANT_TO_BE_HEARD.sub(" ", line))
    if _AN_ASK.search(rest):
        # Declined and then asked in the same breath: the ask is what to answer.
        return False
    if asks_something_of_its_own(line):
        # The decline is not the whole of what the line asks for - "no advice, what time does the
        # pharmacy shut", "i dont want advice, i want to know if its normal". The question is the
        # turn, and the listening line would take it away.
        return False
    return True


def pool_name(text):
    """Which reply pool the line wants: the view one, or the plain "I'm listening" one, or None."""
    if not says_no_advice(text):
        return None
    return "a_view" if asks_for_a_view(text) else "no_advice"


# What the bot says. Not a card and not a pointer: the turn is about being heard, so the reply says
# it is listening and asks for the rest. These would fit any message, which is right here - the
# message is about the turn and not about a subject - but they are never offered on another line.
HEARD = (
    "Fair enough - I'll keep the advice to myself. Tell me the rest of it.",
    "Understood. I'm listening - how are you doing with it?",
    "Right, no fixing from me then. What's on your mind?",
    "That's fair. Say it all and I'll just listen.",
    "No advice, then. Go on - I'm here.",
    "Okay - no advice from me. Where are you with it all?",
)

# The same turn when what they asked for instead is a view: "not looking for a solution, just want
# to know what you think". A view with nothing behind it would be invented, so the one honest move
# is to ask for the situation and promise the view. The person asked for an opinion, and saying
# "no advice" back to them would be the same refusal they came in with.
A_VIEW = (
    "Then tell me the whole of it and I'll say what I think - no fixing, just my honest view.",
    "Okay - the situation as it is, and I'll give you my straight view of it.",
    "I'll tell you what I think, then. What's the situation?",
    "Fair enough. Lay it out and I'll tell you honestly what I make of it.",
)


def lines_for(pool):
    """The pool of lines for the turn: the listening ones or the view ones."""
    return A_VIEW if pool == "a_view" else HEARD


def reply_for(pool, text, memory=None):
    """The line for this turn, varied on the person's own words so two lines do not read alike."""
    from . import pick

    return pick(list(lines_for(pool)), memory, text)
