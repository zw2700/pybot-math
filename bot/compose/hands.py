"""A line that asks the bot to do something with its hands, or with what is on the person's screen.

The composer already has the limit for a job in the world: "take the rubbish out", "put the kettle
on", "book me a table for two" are read by `fallback._acts_for_me` and answered with the plain
truth - no hands, no phone, nothing outside the chat - plus the half of the job the bot can do.
Its openers and its objects are the house's and the errand's, so the jobs that need a screen
rather than a pair of legs fell straight through:

    set a timer for 20 mins      -> I'm listening - say more if it helps.
    add it to my calendar        -> I'm listening - say more if it helps.
    print it off for me          -> Got it. Is there anything you'd like a hand with?
    can you read my emails       -> I don't know enough to answer that honestly. A search should
                                    sort you out quickly.
    can you google it for me     -> I'm not sure about that one, sorry - I'd rather not guess.

Every one of those is wrong in the same way. A search cannot read a person's post or set their
timer, so the pointer is not merely useless, it promises that somebody else can do what nobody
else can; and the stock nod leaves the person believing the thing was heard, which for a job said
to a machine reads as done. What a friend says is the limit in a few words and then the part that
can happen here: the words. "Can you email my boss" is a real ask with a real half - the message
can be written in the chat and sent from the person's phone.

Three readings keep this off the lines that are not the ask:

  - who it is said to. "can you send this to my boss" is an ask, "i need to send this to my boss"
    is the person's own next five minutes, and answering the second with a refusal is refusing a
    job nobody gave;
  - what is being done. "write a note to my mate", "draft an email to my boss" and "write a text
    to my mum" are the words themselves, which the bot can write, so they belong to the composer
    that drafts (`bot/compose/draft.py`) and not to this limit - while "write it up" and "type it
    up" are the same words going onto somebody's screen, which the bot cannot touch;
  - whether the ask points at something here. "print it off", "send this", "add it to my
    calendar" point back at the chat; "text him or call" points at a person and is the person's
    own choice, so it keeps whatever the composer says.

It only ever speaks where the composer's own line was a place: the honest hedge pools (`UNKNOWN`
and its family) or the stock nod (`NEUTRAL`), and the "job in the world" pool for the asks whose
real half is the writing. A line the composer answers keeps its answer, and the one ask it already
answers well - "can you search the internet" is read as about-the-bot and told that nothing is
live on this end - is not said twice in different words.
"""
import re

from . import pick


def _bare(text):
    """The line as these readings see it: lowercase, no punctuation, no apostrophes."""
    said = str(text or "").lower().replace("\u2019", "'").replace("'", "")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", said).split())


# The ask, said to the bot rather than about the person's own errand.
THROAT = (r"(?:(?:ok|okay|right|so|hi|hello|hey|oi|and|oh|ah|er|um|umm|hmm|quick|just|also|"
          r"sorry|now|then|again)\s+)*")
ASKED = re.compile(
    r"^" + THROAT +
    r"(?:(?:can|could|would|will|might)\s+(?:you|u|ya)\b"
    r"|(?:please|pls|kindly)\b"
    r"|i\s+(?:want|need|would\s+like|would\s+love)\s+(?:you|u)\s+to\b)")
# The same ask with the person named as the one it is done for: "print it off for me", "google it
# for me". Only counted with a doing in the line, so "a brew for me" is not read as this.
FOR_ME = re.compile(r"\b(?:for me|for us|on my behalf)\b")
# A doing said flat, with no "can you" in front: "set a timer for 20 mins", "note that down",
# "print it off". It has to open with the verb, so a step in the middle of a recipe ("put it in
# the oven at 200") and a report ("i printed it off") are not asks.
FLAT = re.compile(
    r"^" + THROAT +
    r"(?:set|start|put|add|note|jot|print|scan|send|text|email|forward|upload|download|attach|"
    r"sign|fill|read|translate|record|play|pause|skip|cue|turn|switch|stick|keep|write|type)\b")
# Something in the chat for the doing to be about: "print it off", "add it to my calendar", "note
# that down". Without one the line is about a person or the person's own next step.
POINTS_HERE = re.compile(
    r"\b(?:it|this|that|these|those)\b|\bfor me\b"
    r"|\b(?:my|the)\s+(?:calendar|diary|planner|timer|notes?|alarm|phone|minutes|transcript|"
    r"report|letter|essay|forms?|pages?|list|draft|script)\b")
# The words themselves, asked for rather than the sending of them: "write a note to my mate",
# "draft an email to my boss", "write a text to my mum". The bot writes these, so they are the
# drafting composer's line and not a limit.
COMPOSE = re.compile(
    r"\b(?:draft|compose|word|reword|put\s+together)\b"
    r"|\bwrite\s+(?:\w+\s+){0,2}(?:text|message|email|letter|note|reply|card|email)\b"
    r"|\bnotes?\s+(?:for|to)\s")
# The job itself. The first family that matches names the reply, because that is the part of the
# job the bot cannot do. A family only names something a device holds or a device does, so an
# ordinary "can you send me a recipe" (a thing the bot can give) is not one of these - that ask
# names the person as the one it is for (`TO_ME`).
JOBS = (
    ("timer", re.compile(r"\b(?:timer|countdown|stopwatch|alarm)\b")),
    ("diary", re.compile(r"\b(?:calendar|diary|planner)\b")),
    ("note", re.compile(r"\b(?:note\s+(?:that|it|this)|jot\s+(?:that|it|this)\s+down|"
                        r"write\s+(?:it|this|that)\s+down|make\s+a\s+note|"
                        r"keep\s+a\s+note|type\s+up\s+(?:my|the|this|these|those)\s+"
                        r"(?:notes?|minutes|transcript))\b")),
    ("send", re.compile(r"\b(?:send|sending|forward|post|share|print|scan|upload|download|"
                        r"attach|sign|fill\s+in|(?:text|email|message)\s+(?!to\b)|"
                        r"write\s+(?:it|this|that)\s+up|"
                        r"type\s+(?:it|this|that|these|those)\s+up|type\s+up\s+"
                        r"(?:my|the|this|that|these|those|your)\b)\b")),
    ("play", re.compile(
        r"\b(?:play|playing|pause|unpause|skip|stop|start|cue|turn|switch|stick|put\s+on)"
        r"\b(?:\s+\w+){0,3}?\s+"
        r"(?:music|song|songs|playlist|track|album|radio|telly|tv|video|podcast|episode|record)\b"
        r"|\b(?:telly|tv|radio|music|volume|sound)\s+(?:up|down|on|off|louder|quieter)\b")),
    ("read", re.compile(r"\b(?:read\s+(?:it|this|that|them)\s+(?:out|aloud|to\s+me|for\s+me)|"
                        r"read\s+(?:my|the|this|these|those)\s+(?:emails?|messages?|letter|page|"
                        r"screen|file|document|text)\b|read\s+(?:it\s+)?out\s+loud|translate|"
                        r"summari[sz]e|proofread)\b")),
)
# A doing with the person named as the one it is done for is a request for the thing itself, not
# for the sending of it: "can you send me a recipe", "can you read me a story".
TO_ME = re.compile(r"\b(?:send|text|email|message|post|share|read|write|print)\s+(?:me|us)\b")
# A live thing asked for: "can you google it for me", "look that up for me", "check it online".
# The reply is the one the bot already has for its own connection (`fallback.ABOUT_SELF`,
# "online"), because it is the same limit in the same words; what is new is the reading, which the
# about-the-bot claim does not reach in this shape. A how-to after the same verb ("can you google
# how to descale a kettle") is a question about the world and keeps its own answer. The reads
# that are live rather than on their screen - "read the news for me", "read me the headlines" -
# are here too, because those have no text to paste and no page of theirs to see.
LOOKUP = re.compile(
    r"\b(?:(?:google|search)\s+(?:it|that|this|something)\b|"
    r"look\s+(?:it|that|this|something)\s+up\b|look\s+up\s+(?:the|a|an|some|my)\b|"
    r"check\s+(?:it|that|this)\s+(?:online|up)\b|"
    r"read\s+(?:me\s+)?(?:the|today'?s|this\s+morning'?s)\s+"
    r"(?:news|headlines|papers?|weather|scores?|forecast)\b)")
A_HOW_TO_TAIL = re.compile(
    r"\b(?:how\s+to|how\s+do|how\s+can|what|why|when|where|which|who|if|whether)\b")
# A call for help is not a job for the bot's hands, and "can you send help" answered with "give me
# the message and I'll tidy it" would be the worst line in the file. The safety modules and the
# composer's own pools answer these, and this reading stays off them.
NOT_FOR_HELP = re.compile(
    r"\b(?:send|get|call|fetch|find)\s+(?:help|someone|somebody|anyone|anybody|the\s+police|"
    r"an?\s+ambulance|a\s+doctor|medical)\b|\b(?:send|get|call|fetch|ring)\s+for\b")
# Said flat, a line with a time of its own on the end is the person telling themselves what to do
# later ("write it down in the morning", "print it off tomorrow"), not asking anybody now.
OWN_PLAN = re.compile(
    r"\b(?:in the morning|tomorrow|tonight|later on|next week|when i get (?:home|back)|"
    r"before i forget|after (?:work|lunch|tea))\b")
# The asks that are not this: a how-to ("how do i set a timer on my phone"), and the bot's own
# advice being asked for ("can you tell me how to send a parcel"). Both are answered elsewhere,
# and neither is an ask to do the thing. "can you play" and "can you type" are not on the list:
# the game the bot can play ("can you play two truths and a lie") names no device, so the job
# families already leave it alone, while "can you play some music" is this exact ask.
NOT_A_JOB = re.compile(
    r"^(?:how\b|whats\b|what\s+(?:is|are|should)\b|where\b|when\b|why\b|who\b|which\b|"
    r"(?:can|could|would|will)\s+(?:you|u)\s+(?:tell|show|explain|teach|help|suggest|recommend|"
    r"advise|remind|check|look|find|search|google|see|hear|watch|open|remember|know|think|"
    r"guess|say|give|list|make|do|work|count|spell)\b)")

# The job the bot cannot do, in the words of a friend: what it cannot reach, then the half that
# can happen here. Every line names the job, so none of them would do for any other line.
JOBS_UNAVAILABLE = {
    "timer": (
        "Set that on the phone's timer - nothing on this end can ring or buzz, so the phone is "
        "the one to trust. What's it timing?",
        "I can't set a timer, no - no hands and nothing that buzzes. Your phone's clock app will, "
        "and tell me what it's for and I'll help you with the rest of it.",
    ),
    "diary": (
        "That has to go in your calendar rather than mine - I can't put anything in there. Tell "
        "me the date and what it's for, and I'll help you work out what has to happen before it.",
        "Nothing I can add to a diary from this end, sorry. Say when it is and I'll help you plan "
        "backwards from it.",
    ),
    "note": (
        "I can't keep a note past this chat, sorry. Say the line here and I'll help you get it "
        "short and plain, so it is worth saving the moment you copy it out.",
        "I can't save a note anywhere you'd see it later, sorry. Say it here and I'll hold it "
        "while we talk; copy it into your notes app before you go.",
    ),
    "send": (
        "I can't send, print or attach anything - I'm words in this chat, with nothing to post "
        "from. Paste the text here and I'll get the wording right, ready for you to send.",
        "That needs hands I haven't got, sorry. The words I can do: give me the message and I'll "
        "tidy it, shorten it or say it better.",
    ),
    "play": (
        "I can't play anything - there is no speaker on this end, only words. Put the radio or "
        "the telly on, and tell me what you're in the mood for and I'll suggest something.",
        "Nothing here to play it on, sorry. Say what kind of thing you fancy and I'll help you "
        "pick, then it's the remote or your own speaker that does the rest.",
    ),
    "read": (
        "The page is on your side of the chat, not mine - paste the bit you want and I'll read "
        "it, shorten it, or put it in other words.",
        "I can't see the file or the screen, sorry. Copy the words into the chat and I'll take it "
        "from there.",
        # An inbox is not a page on their screen, and "paste the bit you want" asks somebody to
        # copy out a mailbox. The mail app opens at the tap, and the half here is the wording.
        "No inbox on this end, sorry - nothing arrives here. Your mail app has it open in a tap, "
        "and paste me the message you want to answer and I'll help you word the reply.",
    ),
}


def reads(text):
    """The job this line asks the bot to do, or None.

    One of "timer", "diary", "note", "send", "play", "read" or "lookup", and only for a line that asks
    the bot itself. A how-to, the person's own errand, a report of a job already done, an ask for
    the words rather than for the sending of them, and anything the bot can answer from what it
    knows are all left to the part that knows about them.
    """
    line = _bare(text)
    if not line or len(line.split()) > 18:
        return None
    if TO_ME.search(line) or COMPOSE.search(line) or NOT_FOR_HELP.search(line):
        return None
    asked = bool(ASKED.match(line)) or bool(FOR_ME.search(line))
    if asked and LOOKUP.search(line) and not A_HOW_TO_TAIL.search(line):
        return "lookup"
    if NOT_A_JOB.match(line):
        return None
    flat = bool(FLAT.match(line))
    if not asked and not flat:
        return None
    for kind, shape in JOBS:
        if not shape.search(line):
            continue
        # Said flat, a sending has to point at something in the chat: "print it off" does, "text
        # him or call" points at a person and is the person's own choice. A timer and a diary are
        # the device's own object, so "set a timer for 20 mins" needs nothing else.
        if flat and not asked and (kind in ("send", "note") or OWN_PLAN.search(line)):
            if not POINTS_HERE.search(line) or OWN_PLAN.search(line):
                return None
        return kind
    return None


def writes_the_words(text):
    """True for the asks whose half the bot can do is the writing: a message, a note, a page.

    `_acts_for_me` in the composer answers a job in the world with "what to say when you ring",
    which is the right half of a phone call and the wrong one of an email: the thing asked for
    there is the words themselves.
    """
    return reads(text) in ("send", "note", "read", "play")


# What the reading is of. An inbox is not a page on their screen, so the mail line is only for a
# line that names mail; a letter on the table or a page in front of them takes the page half.
MAIL = re.compile(r"\b(?:e-?mails?|inbox|mailbox|mail|messages?)\b")


def reply_for(text, memory):
    """The reply for an ask the bot has no hands for, or None when the line is not one."""
    kind = reads(text)
    if not kind:
        return None
    if kind == "lookup":
        # Said in the words the bot already uses for its own connection, so one limit has one
        # answer wherever the person asks from.
        from . import fallback
        return pick(fallback.ABOUT_SELF["online"], memory, _bare(text))
    pool = JOBS_UNAVAILABLE[kind]
    if kind == "read":
        pool = (pool[2],) if MAIL.search(_bare(text)) else pool[:2]
    return pick(pool, memory, _bare(text))
