"""An invitation to the bot is a person asking for company, and nothing in the composer heard it.

"do you fancy a walk" is not a question about anything in the world: it is one person asking
another along. Every reading in `bot/compose/fallback.py` hears it as a question anyway, so it
reached the search hedge ("that's beyond what I know well, sorry") or, said the other way, the
intake form ("Got it. Is there anything you'd like a hand with?"). Neither is what a person hears
when they invite someone out, and neither is what a friend says back.

A friend who cannot come does not do either. They say no to the coming - plainly, without
apologising for existing and without pretending they could - and they say yes to the thing: where
would you go, what is on, who is going. So the refusal comes first and the next question is about
the thing invited to, which is what `TOGETHER_AT` picks the pool by.

Only a line spoken to the bot is an invitation. "i want to go for a pint" is their own plan and
"we went for a walk" is their news, so the shape has to be addressed ("do you fancy", "shall we")
or start at the verb with nothing in front of it ("fancy a brew", "want to grab a coffee").

`bot/modules/invitation.py` is the turn: it asks this reading and proposes the line, at a
PRIORITY below the knowledge base, so a thing the answers do know keeps its answer ("shall we get
a takeaway" still gets the fish and chips, "you up for a curry on friday" the quick curry).
"""
import re

from . import pick as compose_pick

# An invitation to the bot itself. "do you fancy a walk" is not a question about anything in the
# world - it is a person asking for company - and every reading below hears it as one: it reached
# the search hedge ("that's beyond what I know well") or the intake form ("Got it. Is there
# anything you'd like a hand with?"). A friend who cannot come does not do either. They say no to
# the coming, plainly and without apologising for existing, and they say yes to the thing: where
# would you go, what is on, who is going. The invitation is the whole line, so the answer is the
# next question about it.
#
# Only a line spoken to the bot counts. "i want to go for a pint" is their own plan and "we went
# for a walk" is their news, so the shape has to be addressed (do you / would you / fancy / shall
# we) or start at the verb with nothing in front of it ("fancy a brew", "want to grab a coffee").
INVITED = re.compile(
    r"\b(?:do|would|will|can)\s+you\s+(?:want|fancy|feel\s+like|be\s+up\s+for|come|join)\b"
    r"|\b(?:do|would|will)\s+you\s+(?:like\s+to\s+)?(?:come|join)\b"
    r"|\bfancy\b|\bup\s+for\b|\bwanna\b|\bshall\s+we\b|\bwe\s+could\b"
    r"|\bwant\s+to\s+(?:go|get|grab|have|see|watch|come|join)\b"
    r"|\bcare\s+to\s+(?:come|join)\b")
# The verb has to be the first thing in the line for these two: "want to go for a pint" is an
# invitation, "i want to go for a pint" is a want of theirs, and "we want to go" is a plan.
INVITED_AT_THE_START = re.compile(r"^(?:fancy|wanna|up\s+for|shall\s+we|we\s+could|want\s+to)\b")
NOT_THEIRS = re.compile(r"^(?:i|we|he|she|they|my|our|her|his|their)\b")
# A question about what the bot can tell them is not an invitation: "do you want to know how to
# fix a bike" is asking for a fact, and the invitation shape only differs from it by a verb.
NOT_WANTED = re.compile(
    r"\b(?:know|knew|learn|ask|asked|tell|say|hear|check|explain|guess|help|try)\b"
    r"|\b(?:see|check|find\s+out)\s+if\b|\bwhether\b|\bhow\s+to\b")
# Not every line with an invite word in it is asking the bot along. "Do you want me to ring
# them" is an offer to do something for the bot, "do you want a hand with that" offers help,
# "do you want anything from the shop" is a shopping list and "do you fancy her" is asking
# about somebody else. None of them invites anybody anywhere, so none of them gets a refusal.
NOT_AN_INVITE = re.compile(
    r"\b(?:anything|something|a\s+hand|a\s+lift|a\s+receipt|a\s+piece|me\s+come|"
    r"her|him|them|die|dying|kill)\b"
    r"|\b(?:want|like|need|fancy)\s+(?:me|us)\s+to\b")

# The same ask said as a plain request for the bot's company rather than as an invitation:
# "can you come to the bbq", "will you be at the party", "can you come round", "could you meet me
# there", "are you coming on saturday", "can you be there on the day". These are the most ordinary
# way people ask a bot along, and the shape was read by nothing at all: the verbs are not the
# invite words above, so the line fell through to the search hedge ("that's beyond what I know
# well, sorry - searching for it will turn up better sources"), which answers a request for
# company with a suggestion to go and look it up.
#
# Only a line addressed to the bot is one of these, so every pattern carries the "you". "can i
# come to yours" is the person asking about their own journey, and "how do i come off my
# tablets" is not about anybody's company.
PRESENCE = re.compile(
    r"\b(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|possibly\s+)?"
    r"(?:come|pop|stop|drop|visit|join|meet|attend|be)\b"
    r"|\bare\s+(?:you|u)\s+(?:coming|free|around|about)\b"
    r"|\b(?:do|would|will)\s+(?:you|u)\s+(?:be\s+)?(?:coming|there|around)\b"
    r"|\b(?:you|u)\s+(?:coming|joining\s+(?:me|us))\b"
    r"|\bwhy\s+don'?t\s+(?:you|u)\s+(?:come|join)\b"
    r"|\b(?:come|join)\s+(?:me|us)\s+(?:for|to)\b")
# "come up with" is inventing something and "come back to me" is a reply later, not company; "be
# there for me" is comfort, which is answered as comfort; "meet the deadline" and "meet my
# targets" name a thing to hit rather than a person, so meet needs a person or "there" behind it.
NOT_PRESENCE = re.compile(
    r"\bcome\s+(?:up|back|across|down\s+to|off)\b"
    r"|\b(?:be|being)\s+there\s+for\s+(?:me|us|him|her|them)\b"
    r"|\bmeet\s+(?:the|a|an|my|your|our)\b"
    r"|\b(?:be|is|are|was)\s+(?:there|around)\s+(?:when|if|to\s+(?:help|talk|listen))\b")
# The one it can take up: the person is asking whether the bot is around, not asking it along.
# "are you there", "you there", "are you about" want a yes and the floor, not a refusal.
ASKING_IF_IM_HERE = re.compile(
    r"^(?:hi|hey|hello|ok|okay|so|right|and|thanks|ta|sorry|please)?\s*"
    r"(?:are\s+(?:you|u)|you|r\s+u)\s+(?:there|here|about|around)\s*[?.!]*$")

# The thing invited to, so the question that comes back is about that thing: a drink is a place
# and a time, a film is what is on, a walk is where it goes.
TOGETHER_AT = (
    ("drink", re.compile(
        r"\b(?:coffee|cuppa|brew|pint|beer|wine|drink|juice|tea\s+out|pub|bar|cafe|"
        r"coffee\s+shop)\b")),
    ("meal", re.compile(
        r"\b(?:lunch|dinner|brunch|breakfast|takeaway|take\s+away|curry|pizza|chinese|indian|"
        r"bite|meal|restaurant|nando'?s|kebab)\b")),
    ("walk", re.compile(
        r"\b(?:walk|stroll|hike|wander|run|jog|cycle|bike\s+ride|swim|gym|park\s+run)\b")),
    ("screen", re.compile(
        r"\b(?:film|movie|show|play|gig|concert|match|telly|cinema|theatre|festival)\b")),
    ("shopping", re.compile(
        r"\b(?:shopping|shops|market|city\s+centre|high\s+street|boot\s+sale)\b")),
    ("out", re.compile(
        r"\b(?:day\s+out|weekend\s+away|trip|beach|countryside|seaside|coast|museum|"
        r"stately\s+home|picnic)\b")),
    ("do", re.compile(
        r"\b(?:party|bbq|barbecue|barbeque|wedding|birthday|christening|housewarming|"
        r"house-warming|quiz|karaoke|reunion|funeral|wake|service|graduation|"
        r"engagement|anniversary|get-together|get\s+together|celebration|naming\s+ceremony)\b"
        # "a do" is a party, but the word on its own is the verb in "do you fancy" and in "what
        # do you do", so it only counts behind a word that makes it a noun.
        r"|\b(?:a|the|this|that|my|his|her|their|big|fancy|work|office|leaving|christmas|"
        r"charity|fundraising|retirement|birthday)\s+do\b")),
)
TOGETHER_REPLIES = {
    "drink": (
        "I can't come along, but that sounds like a good idea. Where do you go for it?",
        "Wish I could join you. Somewhere near you, or the place you always go?",
    ),
    "meal": (
        "I can't make it, but that sounds good. Is it a treat, or an ordinary weeknight?",
        "Wish I could be there. Somewhere new, or the place you always end up in?",
    ),
    "walk": (
        "I can't come with you, but that sounds like a good idea. Is there a route you like, or "
        "somewhere new to try?",
        "Wish I could join you. It clears the head more than people expect - where do you go?",
    ),
    "screen": (
        "I can't come along, but that is a good shout. What is on?",
        "Wish I could be there. Something you have been meaning to see, or picking on the night?",
    ),
    "shopping": (
        "I can't come along, but that sounds like a good afternoon. Is it a browse, or are you "
        "after something in particular?",
        "Wish I could be there. Do you know what you want, or will it find you?",
    ),
    "out": (
        "I can't come along, but that sounds like a good day out. Where are you thinking?",
        "Wish I could be there. Have you been before, or would it be the first time?",
    ),
    "do": (
        "I can't be there - I'm words on a screen - but it sounds a good do. What do you need "
        "help with for it: what to take, what to wear, or what to say to the host?",
        "No legs on this end, so I can't make it, sorry. Tell me how many are going and what you've "
        "got to sort out, and I'll do the planning side of it.",
    ),
}

# A request for company that names no occasion the pools know: "can you come round", "can you meet
# me there", "will you be at the hospital with me". The refusal is one clause, and the rest is the
# work the bot can actually do for the day, so the line is never a bare no and never a pointer.
PRESENCE_REPLIES = (
    "I can't be there in person - nothing here leaves the chat - but tell me the plan and I'll do "
    "the useful half: what to take, what to cook, how to get there.",
    "No body on this end, so coming along isn't mine, sorry. Say what the day looks like and I'll "
    "help with the bits that are words - the list, the timing, what to say.",
    "I'd be there if I could. I'm not, so let me help from here: how many are coming, and what have "
    "you got left to sort?",
)


def _the_invitation(clean):
    """Which pool answers an invitation to the bot, or None when the line is not one."""
    text = " ".join(str(clean or "").lower().split())
    if not text or ASKING_IF_IM_HERE.match(text):
        return None
    present = bool(PRESENCE.search(text)) and not NOT_PRESENCE.search(text)
    if not present and not INVITED.search(text):
        return None
    if not INVITED_AT_THE_START.match(text) and NOT_THEIRS.match(text):
        return None
    if not present and (NOT_WANTED.search(text) or NOT_AN_INVITE.search(text)):
        return None
    # A request for company that also names a job ("can you pop round and help", "can you come and
    # help me shift a sofa") is still about the company: the refusal to be there is the answer, and
    # `NOT_WANTED` above would read the word "help" as a question about how to do something.
    if present and NOT_AN_INVITE.search(text):
        return None
    for kind, pattern in TOGETHER_AT:
        if pattern.search(text):
            return TOGETHER_REPLIES[kind]
    # A request for the bot's company with no occasion the pools know keeps the refusal, because
    # the ask is the whole line: "can you come round" is not a question about anything in the
    # world, and the search hedge answered it as one.
    if present:
        return PRESENCE_REPLIES
    # Nothing the pools know: "do you fancy" on its own, "want to go somewhere". The refusal
    # with no thing in it is the shape that gets everything else wrong ("do you want a lift
    # home", "do you want a receipt"), so a line with no thing is left to the rest of the bot.
    return None


def reply_for(text, memory):
    """The line an invitation to the bot gets, or None when the line is not one."""
    clean = " ".join(str(text or "").lower().split())
    pool = _the_invitation(clean)
    if not pool:
        return None
    return compose_pick(pool, memory, clean)
