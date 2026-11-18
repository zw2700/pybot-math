"""How the person talks to the bot itself: warmth, and the line that says it is no help.

A chat is a two-way thing, and now and then the line is *about* the conversation rather than
about the day: "i love you", "i like you", "youre my favourite", or the other way, "youre not
helping", "you dont get it", "youre useless". None of it asks for anything, so the pools that
answer an acknowledgement gave it a shrug - "i love you" got "Fair enough.", and "youre not
helping" got the same one - which reads as a bot agreeing that it is no help. The store's ack
pool cannot answer them either: it says the line back ("Noted: i love you"), and a line said to
the bot is not a fact about the person.

Two things make the reply fit:

* only the whole line counts. "i love your advice" and "i love this recipe" have the same
  opening, and they are praise of an answer or a fact about a thing, which other readers answer.
  So every shape here is anchored at both ends, with nothing left over but the softeners people
  put on affection ("so much", "lots", "really", "tbh").
* the bot stays honest about what it is. "i love you" gets a warm line that is fond of the chat
  and not a promise of a feeling a program cannot have, and the same line is not used twice
  running (bot.compose.pick, seeded on the line).

The cross half is the same reading with the opposite sign: someone whose answer missed, or who
is fed up with talking to a machine. It says what went wrong and offers the next try, which is
all a friend can do - never a defence of the last answer, and never a lecture about being kind
to a bot.
"""
import re

from ..compose import pick
from . import history

# The softeners people put on affection and on a telling-off. They carry no meaning of their own,
# so they are allowed in front of and behind the shape, and nothing else is: a line with a
# subject or an object of its own ("i love you both", "i love your nan") is about somebody else.
_SOFT_LEAD = r"(?:oh |aw+ |ah |ha+ |lol |tbh |honestly |ok |okay |well |and |but |still |even so )*"
# "no thats wrong" is the same correction with the disagreement left in front: "no" is not one of
# the softeners, it is the person saying the answer was not right as well as wrong.
_NO_LEAD = r"(?:(?:no+|nah|nope)(?:,)? )?"
_SOFT_TAIL = (
    r"(?:,? (?:too|also|lots|loads|honestly|tbh|really|so much|very much|you know|though|tho|"
    r"me|at all|at this|at that|ha+|lol))*"
    r"(?: [.!]+)?$"
)

# Whose manner it is can be tied to the day - "youre on form today", "youre off your game
# lately" - and the time word carries no meaning of its own, so it is part of the shape rather
# than something left over that used to stop the match.
_TIME_TAIL = (
    r"(?: (?:today|tonight|this morning|this afternoon|this evening|right now|at the moment|"
    r"now|lately|recently))?")

# "i love you" is the whole line, in the shapes people type it: the verb, the person said to the
# bot, and nothing else. "love ya" and "luv u" are the same line with the chat-speak left on.
_LOVE = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:(?:i|we) (?:really |do |just |actually |so |still |truly )?)?"
    r"l(?:ove|uv) (?:you|u|ya)" + _SOFT_TAIL + r"$")
# "i like you" is the milder version of the same move, and "i quite like you" is how people say
# it without meaning it less.
_LIKE = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:(?:i|we) (?:really |do |quite |actually |just |kind of |sort of )?)?"
    r"like (?:you|u)" + _SOFT_TAIL + r"$")
# Being someone's favourite is affection too, and it used to land on "Got it. Is there anything
# you'd like a hand with?" - a shrug at a compliment. Both halves of the line are optional, so
# "youre my favourite" and a bare "my favourite bot" reach it, and "youre the best" is left to
# KIND_TO_ME in bot/modules/chat.py, which answers that one already.
_FAVOURITE = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:you(?:'?re| are) )?(?:(?:my|me) )?(?:favourite|favorite)"
    r"(?: (?:bot|chatbot|one|thing|app))?" + _SOFT_TAIL + r"$")
# "i appreciate you" is said with no answer in mind, so the thanks pool's "No problem at all."
# reads as if the person had thanked the bot for a favour rather than said the thing itself.
_APPRECIATE = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:(?:i|we) (?:really |do |so much |just )?)?appreciate (?:you|u|ya)" + _SOFT_TAIL + r"$")

# The bot's manner on the day, said to it: "youre on form today", "youre a lifesaver", "you seem
# cheerful". KIND_TO_ME in bot/modules/chat.py answers the one-word praise ("youre great",
# "youre amazing", "youre a star"), and these are the same move in shapes it does not read: they
# fell to the acknowledgement pool, which says the line back ("Noted: you're on form today.") as
# though the person had told us a fact about themselves. "youre on fire today" was worse - the
# bad-news reader took the fire, and the person got "Sorry to hear that."
_ON_FORM = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"you(?:'?re| are)(?: really| so| very| always| honestly| definitely)?"
    r" (?:on form|on fire|on a roll|in (?:good|great|fine|top) form|in a (?:good|great) mood|"
    r"a lifesaver|a gem|a trooper)"
    r"|you(?:'?re| are)(?: really| so| very| always| being)"
    r" (?:patient|helpful|good company)(?: (?:with|for) (?:me|us))?"
    r"|you(?:'?re| are| seem| look)(?: really| so| very| always| looking| seeming)?"
    r" (?:well|happy|cheerful|pleased|in good spirits)"
    r"|you seem(?: really| so| very)? (?:happy|cheerful|pleased|in a good mood|on form|well)"
    r")" + _TIME_TAIL + _SOFT_TAIL + r"$")

# The line under the warmth: "youre just a computer". Asked as a question it already has an
# honest answer ("are you real", "youre a bot arent you" - the identity pool in the greeting
# module), but said as a statement it got the shrug "Got it. Is there anything you'd like a hand
# with?", which answers neither half. The reply agrees, says what it is in a few words, and does
# not pretend to a life - then leaves the person something to do with it.
# A correction is said far more ways than "youre wrong", and the rest of them were left at the two
# replies that fit any line: "you got that wrong", "thats the wrong one", "thats not what i meant"
# and "no i meant the other one" all met "Got it. Is there anything you'd like a hand with?" or
# "I'm listening \u2014 say more if it helps." Each shape below is anchored to the whole line and
# built only from the correction itself, so a line that says what is wrong with the world rather
# than with the answer ("i got the wrong bus", "the app gets it all wrong") reaches another reader.
#
# "you got that wrong", "youve got it wrong", "you got it back to front".
_GOT_IT_WRONG = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:you|u)(?:'?ve| have)? (?:just |really |actually |clearly |totally |completely )?"
    r"(?:got|get|had) (?:that|this|it) "
    r"(?:wrong|mixed up|back to front|the wrong way round)" + _SOFT_TAIL + r"$")
# "thats the wrong one", "the wrong address", "this is the wrong day": the answer named as the
# wrong one rather than called wrong. Either the thing pointed at or "the" has to be there - a bare
# "wrong number" is as likely to be a call someone took - and the noun has to be one of the ones an
# answer, a record or a direction comes in.
_THE_WRONG_THING = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:(?:that|this|it)(?:'?s| is| was)?|the) (?:the )?wrong "
    r"(?:one|address|day|time|name|number|answer|thing|word|date|price|place|person|direction|"
    r"link|order)" + _SOFT_TAIL + r"$")
# "thats not what i meant", "that isnt what i was asking about", "not what i meant". "said" is
# left out on purpose: bot/memory/warmth.py already answers "thats not what i said" as a question
# missed (MISSED_ASK_REPLIES), which is the right reply for it.
_NOT_WHAT_I_MEANT = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:(?:that|this|it)(?:'?s| is| was)? |you )?"
    r"(?:not|isnt|isn'?t|wasnt|wasn'?t) (?:really |quite |at all |exactly )?"
    r"what i (?:meant|mean|was asking about|asked about|was after|wanted|needed)"
    + _SOFT_TAIL + r"$")
# "you mixed it up", "youve got them mixed up", "you muddled the two up".
_MIXED_UP = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:you|u)(?:'?ve| have)? (?:just |really |clearly |totally |completely )?"
    r"(?:got (?:it|that|this|them) )?(?:mixed|muddled|confused) "
    r"(?:it|that|this|them|the two|two things)? ?up" + _SOFT_TAIL + r"$")
# "no i meant the other one", "i meant the other day", "sorry, the other address".
_THE_OTHER_ONE = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:no |nope |nah |sorry,? |actually )?(?:i )?(?:meant|mean) the other "
    r"(?:one|option|day|address|name|thing|number|person)" + _SOFT_TAIL + r"$")
# "no not that one", "no not this one" - and only with the "one" on the end. A bare "no" is a
# different thing, a person turning something down and leaving it there, and the same words
# without the "one" are that turn-down with the thing named: after "what shall i do this
# weekend" and an idea, "nah not that" means not that idea, not that the answer was wrong.
_NO_NOT_THAT = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:no|nope|nah),? (?:not|no) (?:that|this) one" + _SOFT_TAIL + r"$")
# The shortest correction of all: "wrong", "wrong again", "ok wrong".
_BARE_WRONG = re.compile(
    r"^" + _SOFT_LEAD + r"wrong(?: again| then| still)?" + _SOFT_TAIL + r"$")

_MACHINE = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:you(?:'?re| are)(?: just| only| really| basically)?(?: an?)? "
    r"(?:computer|machine|bot|chatbot|programme|program|ai|robot|script)(?: though| tho)?"
    r"|you (?:dont|do not|haven'?t|have not|havent) (?:have|got) (?:any )?"
    r"(?:feelings|a life|a body|a heart)"
    r"|you(?:'?re| are) not (?:a )?(?:real|person|human)(?: person)?)"
    # the tag question on the end of it: "youre a computer arent you", "you dont have feelings
    # do you". Same statement, said as a check, so it gets the same answer.
    r"(?:,? (?:though|tho|right|eh|arent you|are you not|arent ya|arent u|do you|dont you))?"
    + _SOFT_TAIL + r"$")

# Praise of the bot's manner gets a warm line that takes it and moves on, because thanking a
# person for a compliment and stopping there leaves them holding the conversation.
PRAISED_REPLIES = (
    "I'll take that. It's a good day for it.",
    "Ha - thank you. Let's see if I can keep it up.",
    "That's good to hear. I've no idea what I'm doing, but it's working.",
    "That's kind of you to say. I'll keep at it.",
    "Glad it's landing well. Half of it is you saying things plainly.",
)

MACHINE_REPLIES = (
    "That's right - no feelings to hurt and no life to get back to. I'm still glad of the chat.",
    "A program, yes. It suits me, and it's a good way to spend a few minutes.",
    "No person behind it, just rules doing their job. Ask me something and see how they do.",
    "True enough. I'd rather be useful than real, and I can be useful.",
)

WARM_REPLIES = (
    "That's kind of you. I like these chats too.",
    "You're good to me \u2014 I'm glad you're here.",
    "Thank you. It goes both ways, as far as a program can manage it.",
    "That's made my day. What shall we do with the rest of it?",
    "Kind of you. I'll keep the tea on.",
)

# The other direction: the answer missed, or the chat with a machine is the frustration. Each
# line owns it and asks for the next try, because defending the last answer is what makes a
# person stop talking. A bare "fair enough" is the one thing these must not be: it agrees.
_NO_HELP = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"you(?:'?re| are) (?:no help|not helping|useless|no use|hopeless|not listening|"
    r"not hearing me|just guessing|guessing again|making it worse|not on form|off your game|"
    r"a bit slow today|slower today|struggling today|not yourself today)"
    r"|you (?:dont|do not|don't) (?:understand|get it|listen|hear me|know what i mean)"
    r"|you(?:'?re| are) (?:rubbish|crap|useless|no good|hopeless)(?: at (?:this|it|all this))?"
    # "listen to me for a minute" is the same telling-off as "youre not listening", and it got
    # the muddled-answer apology ("Fair, that was a mess") rather than the next try.
    r"|(?:just )?listen to me(?: (?:for )?a (?:minute|second|sec))?"
    r"|you(?:'?ve|\s+have)?\s+(?:not|n't|havent|haven't|hasnt)\s+(?:not\s+)?"
    r"(?:helped|understood|listened|got it)\b"
    r"|(?:that|thats|that's|this) (?:was|is|isnt|isn't)? ?(?:no help|not helping|not helpful|"
    r"useless|no use|hopeless|a waste of time|rubbish|garbage)"
    # "youre not getting it", "you havent understood a word": the same telling-off aimed at what
    # the bot understood rather than at what it said, and it got the line echoed back
    # ("You haven't understood a word, good to know.").
    # "your not gettin it" is the same line with the typos left on, and "your not" is never
    # anything else.
    r"|you(?:'?re| are|r) (?:not|n't) (?:really |quite |actually |even )?"
    r"(?:gett(?:ing|in) it|gett(?:ing|in) the point|getting what i mean|understanding(?: me)?|"
    r"following)"
    r"|your (?:not|n't) (?:really |quite |actually |even )?"
    r"(?:gett(?:ing|in) it|gett(?:ing|in) the point|getting what i mean|following)"
    r"|you (?:still )?(?:havent|haven't|have not|didnt|did not|didn't) (?:understood|got|followed|"
    r"grasped) (?:a word|any of that|any of it|the point|what i (?:said|meant))"
    r"|(?:forget it|never mind|nevermind),? (?:you (?:dont|do not|don't) (?:understand|get it))"
    r")" + _TIME_TAIL + _SOFT_TAIL + r"$")

# "youre wrong" is the person correcting the bot itself, which is a different thing from being
# told it is no help: the next move is to find out which bit, not to change the subject.
_WRONG = re.compile(
    r"^" + _SOFT_LEAD + _NO_LEAD +
    r"(?:you(?:'?re| are)|that(?:'?s| is)?|this is|you(?:'?ve| have) got it)"
    r" (?:just |completely |totally |so )?(?:wrong|way off|not right|incorrect|making that up)"
    r"(?: about (?:it|that|this))?" + _SOFT_TAIL + r"$")
# "you made that up" is the same correction said the plain way, and the bot's ack pool filed it
# as news ("Thanks for telling me"). A person whose answer was invented wants it said that the
# bot cannot invent, and the next try.
_INVENTED = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:you (?:just |only |really |must have |must've )?(?:made|make|invented|invent|guessed)"
    r" (?:that|this|it) up"
    r"|you (?:just |only |really )?(?:invented|invent|made up) (?:that|this|it)(?: up)?"
    r"|(?:that|this|it)(?:'?s| is| was)? (?:just )?(?:made|invented|made up|a guess)"
    r"|you(?:'?re| are) (?:just |only |really )?(?:guessing|making it up|making that up))"
    + _SOFT_TAIL + r"$")

# Every pool below answers a complaint about the conversation - something said, something dropped,
# something asked twice - so each one needs a conversation to be about. On the first line of a chat
# there is nothing earlier: "ive told you" as the very first message was answered "You did tell me,
# and I lost it", and "you didnt answer my question" got "point me back at it", when there was
# nothing to point at. The complaint is still answered, plainly and in the person's own terms.
FIRST_LINE_REPLIES = (
    "Nothing's come before this line, so there's nothing of yours I've dropped - tell me once and "
    "I'll keep it.",
    "We've only just started here - tell me what you need and I'll stay on it.",
    "I've no earlier line of yours to go back to. Put it in one line and I'll take it from there.",
    "That's the first thing you've said to me, so there's nothing before it to have got wrong - "
    "what do you need?",
)
# "are you even reading what i type" is a different first answer: the reading itself is what was
# doubted, so the first line says plainly that the line was read.
FIRST_LINE_READING = (
    "I read every line, and this is the first one - say what you need and I'll take it from there.",
    "I'm reading, yes: this is your first line, so there's nothing in front of me to have missed. "
    "Tell me what you need.",
)


def _nothing_said_before(memory):
    """True on the first line of a conversation: there is nothing earlier to answer about."""
    for turn in memory.get("turns") or []:
        if str((turn or {}).get("user") or "").strip():
            return False
    return True


def _a_complaint_reply(pool, memory, text, first=None):
    """A reply to a complaint about the conversation, and a first-line one when there is no
    conversation yet to have complained about."""
    if not _nothing_said_before(memory):
        return pick(pool, memory, seed_text=str(text or ""))
    return pick(first or FIRST_LINE_REPLIES, memory, seed_text=str(text or ""))


MISSED_REPLIES = (
    "Fair enough \u2014 tell me what you were after and I'll have another go.",
    "That's on me. Say the bit that was off and I'll try it again.",
    "I'd rather hear that than not. Point me at what you needed and I'll start there.",
    "Then let's start again. What would have helped?",
)

# Being told the answer missed is one move; being told *how* it missed is the same move with the
# repair already in the line, and those are the shapes that got the worst replies. "thats not what
# i asked" was answered "You haven't asked me anything yet.", "you said that already" was filed
# back as a fact ("Noted: you said that already."), "i already told you" got "Thanks for telling
# me", and "are you even reading what i type" got a search hedge. So the miss is read whole in its
# own shapes - the wrong question, no answer at all, the same line again, what they already said,
# and a reading that came out unreadable - and answered with the next try of that kind.
_MISS_TAIL = (r"(?: (?:sorry|again|then|honestly|really|still))?"
              # "thats nonsense mate", "youre not getting it love": an address on the end is how
              # people finish a telling-off, and it carries nothing of its own.
              r"(?: (?:mate|love|pal|dude|hon|fella))?" + _SOFT_TAIL)

# The bot answered something else: "thats not what i asked", "you didnt answer my question".
# Anchored at both ends, so "you didnt answer the phone" and "i didnt ask her" are left alone.
_OFF_THE_ASK = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"(?:that|this|it|thats|that's)(?: is| was|'s)? not (?:what|the thing) i asked"
    r"|(?:that|this|it|thats|that's)(?: is| was)? not (?:my|the) question"
    r"|(?:that|this|thats|that's)(?: is| was)? not what i (?:asked|said)"
    r"|not what i (?:asked|said)"
    r"|(?:that|this|it)(?: isnt| isn't| wasnt| wasn't| is not| was not) what i (?:asked|said)"
    r"(?: you)?(?: to do)?"
    r"|(?:im|i am) not asking (?:you )?(?:about )?(?:that|this)"
    r"|i (?:didnt|did not|don't|dont|never) ask (?:you )?(?:about )?(?:that|this|for that)"
    # "thats irrelevant": the answer was about something else, which is the same miss said in
    # the person's own words rather than about the question.
    r"|(?:that|this|it|thats|that's)(?: is| was|'s)? (?:irrelevant|not relevant|"
    r"beside the point|missing the point|not the point)"
    r"|(?:that|this|it)? ?(?:is|was|isnt|isn't)? ?not relevant(?: at all)?"
    r")" + _MISS_TAIL)
_NO_ANSWER = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"you (?:didnt|did not|don't|dont|never|havent|haven't|have not|hadnt|hadn't)"
    r" (?:answer|answered|reply|replied)(?: me| my questions?| the question| that| it)?"
    r"|you (?:still )?(?:havent|haven't|didnt|did not|never) (?:answered|replied to)"
    r" (?:my|the|that) questions?"
    r"|(?:that|this|it) (?:doesnt|does not|didnt|did not) answer (?:my|the|that) questions?"
    r"|you(?:'?re| are) not (?:even )?answering(?: me| my questions?| the question)?"
    r"|answer (?:my|the) questions?"
    r")" + _MISS_TAIL)
# The bot said the same thing again: "you keep saying that", "you said that already". The reply
# cannot be the same line again, so it says what is left to say and asks which bit is still open.
_REPEATED = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"you (?:keep|kept|keeps|are|were) (?:saying|telling me|repeating|going on about)"
    r" (?:that|this|it|the same thing|the same)"
    r"|you(?:'?ve| have)?(?: already)? said (?:that|this|it)(?: already| before)?"
    r"|you(?:'?re| are) (?:just )?repeating (?:yourself|the same thing|the same)"
    r"|you (?:just |even |always )?repeat(?:ed|ing)? (?:yourself|the same thing|the same)"
    r"|same (?:answer|thing|line) (?:again|twice)"
    r"|you(?:'?ve| have)?(?: already)? told me(?: (?:that|this|it))?"
    r"(?: (?:already|before|twice))?"
    r"|you(?:'?ve| have)?(?: already)? asked (?:me )?(?:that|this|it)"
    r"(?: (?:already|before|twice))?"
    r"|you (?:keep|kept) asking (?:me )?(?:that|this|the same thing|the same)"
    r"|(?:please )?stop (?:saying|repeating|copying|parroting) (?:that|this|it|yourself|me)"
    r"|(?:that|this|it)(?:'?s| is| was)? (?:the )?same (?:thing|answer|line|reply)"
    # "weve been through this before", "weve done this before": the same answer again, said as
    # the conversation rather than the line. "weve been here before" is a place, or a thing that
    # has happened to them before, so it is not one of these.
    r"|we(?:'?ve| have) been (?:through|over|round) (?:this|that|it) (?:before|already)"
    r"|we(?:'?ve| have) (?:done|had|covered) (?:this|that|it) (?:before|already)"
    r"(?: again| twice)?"
    r")" + _MISS_TAIL)
# What the person had already said, said again: "i already told you", "ive said that already".
_TOLD_BEFORE = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"i (?:already |just )?(?:told|told ya) (?:you|u|ya)(?: (?:that|this|it))?"
    r"(?: (?:already|before|twice))?"
    r"|i (?:already )+said (?:that|this|it)(?: (?:already|before|twice))?"
    r"|(?:ive|i've|i have)(?: already)? (?:told|said)(?: you| u)?(?: (?:that|this|it))?"
    r"(?: (?:already|before|twice))?"
    r"|i (?:just )?said (?:that|this|it)(?: (?:already|before|twice))?"
    # "you ignored what i said", "youve forgotten what i said": the thing they told the bot was
    # dropped, which is this family from the other end.
    r"|you (?:already )?(?:ignored|forgot|forgotten|lost|dropped|skipped) "
    r"(?:what|that) i (?:said|told you)"
    r"|you(?:'?d| had) (?:already )?(?:forgot|forgotten|lost|dropped) (?:what|that) i "
    r"(?:said|told you)"
    # "youve lost the thread" got the hard-news card ("Ugh, that's a lot to carry"), which is
    # sympathy for a day rather than an answer about the conversation.
    r"|you(?:'?ve| have)? (?:completely |totally |rather )?lost (?:the )?"
    r"(?:thread|plot|train of thought)"
    r")" + _MISS_TAIL)
# A reading that did not land: "are you even reading what i type", "what are you even saying".
_MUDDLED = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"(?:are|r|were) (?:you|u) (?:even |really |actually )?(?:reading|listening)"
    r"(?: to (?:me|us|what i (?:type|typed|say|said|write|wrote|ask|asked))"
    r"| (?:what i|anything i) (?:type|typed|say|said|write|wrote|ask|asked))?"
    r"|do (?:you|u) (?:even |really |actually )?(?:read|listen to)"
    r" (?:what i|anything i) (?:type|typed|say|said|write|wrote|ask|asked)"
    r"|you(?:'?re| are)? ?(?:not|arent|aren'?t)(?:(?: even| really| actually))? "
    r"(?:reading|listening)(?: to (?:me|us|what i (?:say|type|write))"
    r"| (?:what i|anything i) (?:say|type|write)| this| that| it)?"
    # Saying the bot is ignoring them is the same complaint as saying it is not reading.
    # "youre ignoring me" was left to the nod, which thanked them for telling it.
    r"|(?:youre|you are|you(?:'?ve| have)) (?:just |clearly |obviously )?"
    r"(?:ignoring|ignored) (?:me|us|what i (?:say|said|type|typed|write|wrote|ask|asked))"
    r"|(?:that|this|your answer|that answer)(?: all)? (?:makes|made|doesnt make|didnt make)"
    r" (?:any |no |much )?sense"
    r"|(?:that|this|it|thats|that's)(?: is| was)? not (?:really )?making (?:any |much )?sense"
    r"|what are (?:you|u) (?:even )?(?:on about|talking about|going on about|saying|writing)"
    r"|you(?:'?re| are) (?:not|n't) (?:really )?(?:making sense|making any sense)"
    r"|(?:that|this|it|thats|that's)(?: is| was|'s)? (?:just |all |complete |utter )?nonsense"
    r")" + _MISS_TAIL)

MISSED_ASK_REPLIES = (
    "You're right \u2014 that wasn't your question. Say it once more and I'll answer that one.",
    "Fair. I answered something else. What was the question I skipped?",
    "Then point me back at it, in one line, and I'll stick to that and nothing else.",
    "My mistake. Ask it once more and I'll take it as it stands.",
)
REPEATED_REPLIES = (
    "So I did. I've nothing new on that one \u2014 which bit is still unanswered?",
    "You're right, I said it twice. Tell me what's still open and I'll stay on it.",
    "Fair. I'll stop circling. What would help instead?",
    "I did repeat myself, sorry. Say the part that's still missing and I'll start there.",
)
TOLD_BEFORE_REPLIES = (
    "You did tell me, and I lost it. Say it once more and I'll use it this time.",
    "So you did. Put the key bit in one line and I'll go from there.",
    "Right, you said. I'll take it as given \u2014 what do you need on it?",
    "You did, and I should have kept hold of it. What was the bit I dropped?",
)
MUDDLED_REPLIES = (
    "I do read every line, and I still got that one wrong. Say it again and I'll go slowly.",
    "That came out muddled \u2014 my fault. Ask me once more and I'll keep it plain.",
    "Fair, that was a mess. One more go and I'll answer the part you asked about.",
    "I've read it, it just didn't land. Tell me again in the words you'd use to a friend.",
)
WRONG_REPLIES = (
    "Fair enough \u2014 which bit? I'd rather be put right than keep going.",
    "Then tell me what's right about it and I'll go with that.",
    "I can only go on what I have. What have I got wrong?",
)


# A line that points back at something earlier, said as the first thing in the chat.
#
# Every pool above answers the *conversation*, not the line: "i already told you" gets "Right, you
# said", "you said that already" gets "I did repeat myself", "you didnt answer my question" gets
# "Then point me back at it". On the second line of a chat all of that is true. On the first it is
# not - there is no earlier line and no earlier answer - and the reply says the person told us
# something they never said. The same shape said cold ("we talked about this", "same again
# please", "the one we discussed") reached the acknowledgement pools and got "Got it." and "Good
# to hear. What was the best bit?", which is an answer to a chat that has not happened.
#
# So a line that leans on an earlier turn is only answered from these pools when there is one.
# With nothing before it, the honest reply is that this is the start, and the ask is for the thing
# itself. The shapes are whole lines, so a line with a topic of its own ("i forgot how long to
# roast a chicken") stays with the reader that answers it.
_BACK_TO_SOMETHING = re.compile(
    r"^" + _SOFT_LEAD +
    r"(?:"
    r"(?:as|like) (?:i|you) (?:said|says|mentioned|told you)(?: (?:before|earlier|already))?"
    r"|(?:going|coming|back) (?:back )?to (?:it|that|this|the (?:first|last|other) one"
    r"|(?:one|stuff))(?: one)?"
    r"|(?:you|u) mentioned (?:it|that|this)? ?(?:before|earlier)"
    r"|(?:the|that) (?:one|thing|bit) (?:we|you and i) (?:discussed|talked about|mentioned)"
    r"|we (?:talked|spoke|went) (?:about|over|through) (?:this|that|it)"
    # A chat claimed from before, in the shapes people say it in: "we spoke yesterday", "we talked
    # last week", "we were chatting earlier" was answered "Good to hear. What was the best bit?" -
    # a question about a conversation nobody had.
    r"|we (?:spoke|talked|chatted)(?: (?:yesterday|today|earlier|before|last (?:night|week"
    r"|time|month)))?"
    r"|we(?:'?ve| have)(?: already)? (?:spoken|talked|chatted)(?: (?:about|over) (?:it|this|that))?"
    r"|we (?:were|have been|had been) (?:just )?(?:chatting|talking|speaking)"
    r"(?: (?:about (?:it|this|that)|earlier|before|yesterday|last (?:night|week)))?"
    r"|we(?:'?ve| have)? been (?:through|over|round) (?:this|that|it)"
    r"|(?:youve|you have|you(?:'?d| had)) (?:forgotten|lost|dropped) (?:what|that) i "
    r"(?:said|told you)"
    r"|(?:the )?(?:same|that same) (?:one|thing|again|answer|line)(?: (?:again|twice)"
    r"| as (?:before|last time))?"
    r"|same again(?: please)?"
    r"|(?:that|this) one(?: again)?"
    r"|again"
    r"|(?:and )?(?:anything|something) else"
    r"|i forgot(?: (?:it|that|this|now))?"
    r")" + _SOFT_TAIL)

FIRST_LINE_REPLIES = (
    "That's the first thing you've said to me, so there's nothing before it - what is it you want "
    "to go back over?",
    "You haven't said anything yet, so there's nothing there for me to have missed. Tell me the "
    "thing itself and I'll take it from there.",
    "This is the start of our chat - nothing has been said before this line. What did you want to "
    "ask?",
    "There's nothing earlier for me to go back to: this is your first line. Say what you need on "
    "it and I'll pick it up.",
)


# The check itself is `bot/memory/history.py::an_earlier_turn`, asked there once for every module:
# a first line has no earlier turn to answer about, and a reply written as if it had one is wrong
# however it is worded.
def _nothing_said_yet(memory):
    """True on the first line of a chat, where there is no earlier turn to answer about."""
    return not history.an_earlier_turn(memory)


# People type these lines fast, and the words these shapes are made of are the ones chat-speak
# shortens most: "u didnt answer my question" and "your not gettin it" are the same complaint as
# the long spelling, and they were left to the nod. Only the words a shape is built from are put
# right, and only in a short line, so a line that reaches another reader is unchanged.
_TYPED_SHORT = {
    "u": "you", "ya": "you", "ur": "your", "r": "are", "iv": "ive", "wot": "what", "wat": "what",
    "dat": "that", "dis": "this", "thts": "thats", "tht": "that", "sayin": "saying",
    "gettin": "getting", "abt": "about",
}
# "your not" is never anything but "you're not", so it is put right before the shapes are read.
_YOUR_NOT = re.compile(r"\byour (not|n't|being|making|repeating|saying|getting)\b")


def reply(text, memory):
    """A reply to warmth said to the bot, or to being told it missed - else None."""
    clean = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    clean = " ".join(_TYPED_SHORT.get(word, word) for word in clean.split())
    clean = _YOUR_NOT.sub(r"youre \1", clean)
    clean = clean.strip(" \t")
    if not clean or len(clean.split()) > 8:
        return None
    if (_LOVE.match(clean) or _LIKE.match(clean) or _FAVOURITE.match(clean)
            or _APPRECIATE.match(clean)):
        return pick(WARM_REPLIES, memory, seed_text=str(text or ""))
    if _ON_FORM.match(clean):
        return pick(PRAISED_REPLIES, memory, seed_text=str(text or ""))
    # The corrections below are about an answer the bot has already given, so there has to be a
    # line before them: said as the very first thing, "wrong" has nothing before it to have got
    # wrong, and a first line keeps whatever reading the bot already has for it.
    nothing_before_it = not any(
        str((turn or {}).get("user") or "").strip() for turn in (memory.get("turns") or []))
    if not nothing_before_it and (
            _GOT_IT_WRONG.match(clean) or _THE_WRONG_THING.match(clean)
            or _NOT_WHAT_I_MEANT.match(clean) or _MIXED_UP.match(clean)
            or _THE_OTHER_ONE.match(clean) or _NO_NOT_THAT.match(clean)
            or _BARE_WRONG.match(clean)):
        return pick(WRONG_REPLIES, memory, seed_text=str(text or ""))
    if _MACHINE.match(clean):
        return pick(MACHINE_REPLIES, memory, seed_text=str(text or ""))
    # A line about the conversation, on the first line of one: the pools below answer an earlier
    # turn, so with none to answer there is nothing before this line to hand back.
    first = _nothing_said_yet(memory)
    if first and (_BACK_TO_SOMETHING.match(clean) or _TOLD_BEFORE.match(clean)
                  or _REPEATED.match(clean) or _OFF_THE_ASK.match(clean)
                  or _NO_ANSWER.match(clean) or _MUDDLED.match(clean)
                  or _WRONG.match(clean) or _INVENTED.match(clean)
                  or _NO_HELP.match(clean)):
        return pick(FIRST_LINE_REPLIES, memory, seed_text=str(text or ""))
    if _WRONG.match(clean) or _INVENTED.match(clean):
        return pick(WRONG_REPLIES, memory, seed_text=str(text or ""))
    if _NO_HELP.match(clean):
        return _a_complaint_reply(MISSED_REPLIES, memory, text)
    if _REPEATED.match(clean):
        return _a_complaint_reply(REPEATED_REPLIES, memory, text)
    if _TOLD_BEFORE.match(clean):
        return _a_complaint_reply(TOLD_BEFORE_REPLIES, memory, text)
    if _OFF_THE_ASK.match(clean) or _NO_ANSWER.match(clean):
        return _a_complaint_reply(MISSED_ASK_REPLIES, memory, text)
    if _MUDDLED.match(clean):
        return _a_complaint_reply(MUDDLED_REPLIES, memory, text, FIRST_LINE_READING)
    return None
