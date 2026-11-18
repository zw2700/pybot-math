"""A bare thing, offered as the reason for the state they just reported.

People talk in shorthands with someone who was listening a moment ago. A woman says she is
knackered, asks the bot why it thinks so, and answers the bot's own question with two words:

```
im knackered
  -> Long one? Give yourself half an hour doing nothing before the next thing.
why
  -> I'd be guessing at the reason - the cause is not something I can see from here. Which part
     of that do you want the why for?
the baby
  -> I'm listening — say more if it helps.
```

"The baby" is the answer to the question the bot just asked. It is not a fragment nobody can
use: it is a reason, and one the bot has plenty to say about. Said as the full statement it is
("im knackered, the baby"), the knowledge base answers it with the broken nights and the shift
that gets each of them a block of sleep. The whole of the failure is that the words the person
left out were the words that made it a sentence.

So this reads the line against the state they reported: the phrase is joined to it, and the
line that comes out is answered as a line of its own.

The rule is narrow on purpose:
* the line has to be a thing and nothing else - no verb, no question, at most four words - so
  "and the baby needs a feed at 3" stays a line of its own;
* it has to follow the bot's own turn, so a bare "the garden" as the opening line - or straight
  after the person's own words - is not read as a reason for anything;
* there has to be a state reported in the last three turns ("im knackered", "i feel low",
  "ive been stressed"), and the state has to be one of the words people use for how they are,
  so "im thinking of a dog" is not a state to be given a reason for;
* the answer has to be one the bot has not just given, so this cannot turn a shrug into the
  same line twice.
"""
import copy
import importlib
import random
import re

from ..compose import pick
from ..understanding import understand
from . import topics

# How they said they were, and the word for it. The lead-ins are the ones people put in front of
# a state ("im bloody knackered", "feel a bit low") and nothing else about the line is read.
STATE = re.compile(
    r"\b(?:i'?m|i am|i feel|i'?ve been|i have been|i'?ve had|i have had|i had|it'?s been|"
    r"its been|feel|feeling|been)\s+"
    r"(?:(?:so|very|really|proper|properly|totally|completely|absolutely|a bit|a little|well|"
    r"fairly|quite|pretty|dead|bloody|seriously|still|just|always|knackered|feeling)\s+)*"
    # "im having a rubbish day", "ive been having a rough week": the state is said as a day
    # rather than as an adjective on its own. "im having a baby" reads "baby", which is not a
    # state word, so nothing is joined to it.
    r"(?:(?:having|had)\s+)?(?:(?:a|an|the)\s+)?"
    r"([a-z']+(?:\s+up)?)\b", re.I)

# The states that are a way of being and not a thing they are doing. "i'm thinking", "i'm
# learning to drive" and "i'm after a new job" are all lines with a subject of their own, and
# handing them a reason they did not give would be inventing one.
STATE_WORDS = frozenset("""
tired knackered shattered exhausted drained worn weary stressed stressed-out anxious worried
nervous low down depressed miserable unhappy sad lonely bored fed up hacked off angry cross
annoyed upset rubbish awful terrible rough ill sick poorly unwell sore achy achey hurting
skint broke strapped poor lost stuck overwhelmed snowed swamped
flat empty numb crap
""".split())

# A state said as a thing rather than an adjective: "im in a state", "feeling at the end".
STATE_PHRASES = (
    "in a state", "at the end of my tether", "at the end", "under the weather", "run down",
    "worn out", "fed up", "hacked off", "on my knees", "all over the place", "not sleeping",
    "not been sleeping", "short of money", "hard up", "out of work", "off sick",
    # A day said as a day: "ive had a rubbish day", "its been a rough week". The state is in the
    # day and not in an adjective on the person, and without these the low was read as no state
    # at all, so the reason line after it fell to the floor.
    "bad day", "rough day", "hard day", "long day", "tough day", "off day",
    "down day", "flat day", "rubbish week", "bad week", "rough week", "hard week", "long week",
)

# The bot's last line asked them something. It has to be the bot's own question, not a question
# quoted from them, so it is read off the end of the line.
A_QUESTION_AT_THE_END = re.compile(r"\?\s*[\"'”’)]?\s*$")

# A thing and nothing else: at most four words, no verb in it. The words in front are the ones
# people put before a thing when they are picking it out of the air ("just the baby", "the baby
# probably", "mostly work").
A_THING = re.compile(
    r"^(?:(?:just|only|mostly|mainly|probably|definitely|honestly|mostly just|just the|"
    r"probably the|i think|i suppose|suppose|maybe)\s+)*"
    r"(?:the|my|our|his|her|their|this|that|a|an|no|not having|having|being|work|money|"
    r"sleep|kids|family|everything|it|me|us)?\s*"
    r"([a-z' ]{1,40})$", re.I)

# The words people put in front when they are guessing rather than telling. "maybe its work",
# "i think the kids", "it's money probably" - the guess is not part of the reason, and with it
# left on, the reason reads as a sentence of its own and is never joined to the state.
# "just", "really" and "only" are the same thing said smaller: "maybe its just tiredness" is
# tiredness, and with the word left on the reason it lands in the sentence as "just tiredness".
A_GUESS_IN_FRONT = re.compile(
    r"^(?:(?:maybe|probably|likely|definitely|honestly|really|just|only|actually|possibly|"
    r"must be|its|it's|i think|i suppose|suppose|i reckon|reckon|though|but|and|also)\s+)+",
    re.I)

# The words that stand in for every reason at once: "everything", "life", "it all". They name
# nothing, so a line about them would be a shrug in a longer shape - "Everything can do that to
# you. What is the worst of it at the moment?" - and the mood pools answer the line instead.
NOT_A_REASON = frozenset("""
everything everyone everybody anything nothing something life stuff things
""".split())
NOT_A_REASON_PHRASES = ("it all", "all of it", "the world", "the lot", "everything else",
                        "everything at once")


# What the bot says for the person's reason: the reason is theirs, so the bot speaks of it as
# "your". Lifted out of their line it is still in the first person ("my sleep", "my job"), and
# "My job - that is the usual one" is the bot talking as if it were the one with the job.
A_SWAP_TO_YOURS = ((re.compile(r"\bmy\b", re.I), "your"), (re.compile(r"\bour\b", re.I), "your"),
                   (re.compile(r"\bhis\b|\bher\b|\btheir\b", re.I), "your"),
                   (re.compile(r"\bme\b", re.I), "you"), (re.compile(r"\bi\b", re.I), "you"))

# "i've no idea", "dont know why", "who knows": the answer to a question about the reason saying
# there is no answer. It is not a reason, and reading it as one gave "Dont know why can do that to
# you. What is the worst of it at the moment?" - the bot repeating their shrug back as if it were
# the thing behind how they feel.
NO_IDEA = re.compile(
    r"\b(?:do(?:n'?t| not)|doesnt|doesn'?t|didnt|didn'?t|dunno|dun+o)\s+(?:really\s+)?know\b"
    r"|\bno idea\b|\bnot (?:sure|a clue)\b|\bwho knows\b|\bgod knows\b|\bbeats me\b"
    r"|\bno clue\b|\bsearch me\b|\bhaven'?t a clue\b|\bnot got a clue\b", re.I)

# A reason that has its own reader and its own answer: a part of their body is the health pool's
# to answer ("Sorry - that's a rotten way to feel. Has it been like that long?"), and a person in
# their life is the worry-about-someone pool's. Neither is the general mood-with-a-reason case.
A_BODY_OR_A_PERSON = re.compile(
    r"\b(?:(?:my|his|her|their|the)\s+)?(?:head|heads|back|knee|knees|shoulder|shoulders|hip|"
    r"hips|neck|stomach|belly|gut|tooth|teeth|gum|gums|foot|feet|ankle|ankles|arm|arms|leg|legs|"
    r"hand|hands|wrist|elbow|ear|ears|throat|chest|skin|eye|eyes|migraine|migraines|cough|cold|"
    r"flu|toothache|backache|sciatica|arthritis)\b"
    r"|\b(?:my|our|his|her|their)\s+(?:husband|wife|partner|boyfriend|girlfriend|mum|mom|mam|"
    r"mother|dad|father|son|daughter|child|kid|kids|baby|brother|sister|friend|mate|boss|"
    r"colleague|nan|gran|grandma|grandad|aunt|uncle|cousin)\b", re.I)

# Words that are never the thing itself: a yes, a thanks, an agreement.
NOT_A_THING = frozenset("""
yes yeh yeah yep ok okay k cool nice right sure no nope nah nothing none nothing much
thanks thank you ta cheers hi hello hey hmm mm mmm oh ah sorry alright fine definitely
maybe probably dont know dunno what why how who when where l don't know not sure
""".split())

# A line that is only a nod names no thing to be the reason for anything, whatever words the
# nod is made of. A single ack word was already refused above, but people put a second word
# with it - "ok then", "lol ok", "alright then", "yeah well", "good stuff", "thats grand" - and
# the pair got through as a thing. So after "im knackered", "and if i havent got any onions",
# the nod was read as the reason and asked again as a line: the knowledge base, still on the
# cooking, came back with a whole new dish, and "lol ok" after the same chat came back with a
# definition of LOL. A nod is answered by the pools that answer nods; it is never a subject to
# look up.
#
# The nod is read two ways, because people approve in words an ack list never holds: the store's
# own `topics.is_ack` (a short line that answers the bot's last turn) or a line whose every word
# is a nod word. The approval words below are the ones people type instead of a yes - "brill
# thanks", "great stuff", "thats grand", "loverly" - and the shrug nouns "stuff" and "things",
# which name nothing to be a reason for.
A_NOD = topics.ACKS | topics.STOPWORDS | frozenset("""
good great brilliant brill ace excellent amazing wonderful lovely loverly luvly fab fabulous
super top sorted sound grand mint quality class legend star stuff things one
mate matey fella boss hun love dude bud pal thats that thank ta cheers much many lot lots
ha haha lol lols hehe x xx xxx aye yeh yep yes yeah ok okay kk alright then so well too anyway
anyhow though also still just only really honestly actually truly right fine
""".split())

# A line that says there is no reason: "i dont know why", "no idea why", "i cant explain why".
# It is not a thing to be joined to the state, and it is not a shrug to be left at the floor -
# after "im feeling really down today" it is the person answering the question a friend asks
# next. The words around it are allowed ("i really dont know why", "i honestly have no idea why").
NO_REASON = re.compile(
    r"^\W*(?:"
    # "i dont know why", "no idea why", "i cant explain why" - the plain shapes.
    r"(?:(?:i\s+)?(?:really|honestly|actually|genuinely)\s+)?(?:i\s+)?"
    r"(?:(?:dont|don'?t|do not)\s+(?:really\s+)?know"
    r"|(?:have\s+)?no\s+idea"
    r"|(?:i\s*(?:'m|m| am)\s+)?(?:not|cant|can'?t|cannot)\s+(?:really\s+)?"
    r"(?:sure|explain|say|tell)"
    r"|dunno)\s+why\b"
    # "nothing happened", "nothing much has happened": the same answer to the same question,
    # said as the absence of a cause rather than as not knowing one. Both readings are a line
    # with no reason in it, and neither is a thing to join to the state as a cause.
    r"|(?:but\s+|and\s+|so\s+)?(?:nothing|nowt)(?:\s+(?:much|really|at all))?\s+"
    r"(?:has\s+|had\s+)?happened\b"
    # "no reason", "no particular reason", "for no reason at all".
    r"|(?:for\s+)?(?:no|not\s+any|without\s+a)\s+(?:particular\s+|real\s+|obvious\s+)?reason\b"
    # "no idea", "dunno", "i dont know": the same answer with the "why" left off. The caller
    # only answers it when a state is in the last few turns, so a bare "no idea" on its own is
    # still the chat's line about a choice, not a reason.
    r"|(?:i\s+)?(?:dont|don'?t|do not)\s+(?:really\s+)?know"
    r"|(?:have\s+)?no\s+idea"
    r"|dunno"
    r")"
    r"(?:\s+(?:really|at all|though|today|honestly|maybe|i suppose))*\s*[.!?]*\s*$", re.I)

# The verbs that make the line a statement instead of a thing. "the baby needs a feed" is a
# line of its own, and a line of its own is answered as one.
A_VERB = re.compile(
    r"\b(?:is|are|was|were|be|been|am|do|does|did|have|has|had|will|would|can|could|should|"
    r"shall|may|might|must|need|needs|needed|want|wants|wanted|got|get|gets|getting|go|goes|"
    r"went|make|makes|made|take|takes|took|keep|keeps|kept|wake|wakes|woke|feed|feeds|"
    r"cries|cried|come|comes|came|start|starts|started|stop|stops|stopped|work|works|"
    r"working|left|leave|leaves|lost|lose|loses|hate|hates|love|loves|said|says|tell|told)\b",
    re.I)

# A line that asks something is a line of its own, even when it is short: "whats behind it" is
# a question about the state, not the thing behind it.
A_QUESTION_WORD = re.compile(
    r"^\W*(?:what|whats|what's|why|how|hows|how's|when|whens|where|who|whos|which|whose|"
    r"do|does|did|is|are|was|were|can|could|would|should|will|shall|have|has|had|am)\b", re.I)

# The bot telling them it is saying the same thing again: a frame for a repeat, not an answer.
REPEATED_ON_PURPOSE = re.compile(
    r"^\W*(?:same (?:answer|as|one)|it'?s what i said|as i said|said already|"
    r"that is the same|the same as|again:)", re.I)

# The bot saying it has nothing: a reason read into a shrug is not an answer. The lines a flat
# two-word line comes back with when nothing in the bot has picked it up - "I'm listening - say
# more if it helps", "Thanks for telling me - I'm here if you want to dig into any of that",
# "Got it. Is there anything you'd like a hand with?", "Your mum - noted."
NOTHING_SAID = re.compile(
    r"\b(?:i'?m listening|say more|not sure about that one|don'?t know enough|"
    r"beyond what i know|rather not guess|everything i have on that one|"
    r"not much (?:i can add|to go on)|which bit do you|tell me more|"
    r"i'?m here if you want|anything you'?d like a hand with|thanks for telling me)\b"
    r"|\u2014\s*noted\.|\s-\s*noted\.", re.I)


def _flat(text):
    return " ".join(str(text or "").lower().replace("’", "'").split())


def _turns(memory):
    return [t for t in (memory.get("turns") or []) if isinstance(t, dict)]


def _the_state_they_reported(memory, back=4):
    """The state line, said as it was said, from the last few turns (newest first)."""
    for turn in reversed(_turns(memory)[-back:]):
        line = _flat(turn.get("user"))
        if not line:
            continue
        for phrase in STATE_PHRASES:
            if re.search(r"\b" + re.escape(phrase) + r"\b", line):
                return line, phrase
        found = STATE.search(line)
        if found and found.group(1).strip() in STATE_WORDS:
            return line, found.group(1).strip()
    return None, None


def _the_bot_just_spoke(memory):
    """The bot's line on the turn before, or "" when it said nothing."""
    for turn in reversed(_turns(memory)[-2:]):
        said = str(turn.get("bot") or "").strip()
        if said:
            return said
    return ""


def _already_has_it(said, thing):
    """The bot's own line already names the thing: "The baby - so that is the part behind it."

    It has been understood, and a question of its own was asked about it, so the reason is not
    something the bot is missing. Answering the state line again over the top of that question
    talks past the person instead of with them.
    """
    if not said:
        return False
    line = " " + _flat(said) + " "
    words = [w for w in _flat(thing).split()
             if w not in ("the", "my", "our", "his", "her", "their", "a", "an", "this", "that",
                          "just", "only", "mostly", "mainly", "probably", "definitely")]
    return bool(words) and all(re.search(r"\b" + re.escape(w) + r"\b", line) for w in words)


# A line that says the person does not know or is not sure is an answer to a question, not a
# reason for how they feel. "im feeling down today" / "i dont know why" / "im not sure" is the
# person thinking aloud; joined to the state it was read as the reason "not sure" and the mood
# line came back a third time. The line is left to the readers that answer uncertainty.
A_HESITATION = re.compile(
    r"^\W*(?:i\s*(?:'m|m| am)\s+)?(?:not\s+(?:really\s+|too\s+|so\s+)?sure|unsure|"
    r"not\s+(?:really\s+)?certain|(?:i\s+)?(?:dont|don'?t|do not)\s+(?:really\s+)?know|"
    r"dunno|no\s+idea)\b", re.I)


def _only_a_nod(text):
    """True when the line is nothing but a nod: the store's own ack reading, or every word of it
    a nod word ("good stuff", "thats grand", "brill thanks", "loverly"). It names no thing."""
    if topics.is_ack(text):
        return True
    words = [word.strip(".,!?'") for word in _flat(text).lower().split()]
    return bool(words) and all(word in A_NOD for word in words if word)


def _a_thing(text):
    """The thing itself, said the way they said it, or None when the line is more than a thing."""
    low = _flat(text).strip(" .!,")
    if not low or low.endswith("?"):
        return None
    # A hedge before the thing is not the thing: "dunno, the baby" and "not sure, money" are
    # the reason said with a shrug in front of it. Strip the hedge and read what is left; a bare
    # "not sure" leaves nothing and still stands down, so the uncertainty readers keep it.
    if A_HESITATION.match(low):
        low = A_HESITATION.sub("", low).strip(" .,:;-")
        if not low:
            return None
    if A_QUESTION_WORD.match(low):
        return None
    # A guess at the reason is still the reason: "maybe its work" is the same answer as
    # "work" to the question the bot asked.
    body = A_GUESS_IN_FRONT.sub("", low).strip() or low
    body = A_GUESS_IN_FRONT.sub("", body).strip() or body
    words = body.split()
    if len(words) > 4 or len(words) < 1:
        return None
    if body in NOT_A_THING or " ".join(words) in NOT_A_THING:
        return None
    # A verb only makes the line a statement when there is something else in it: one word on its
    # own cannot be a statement, so "work" is the reason and not "they work".
    if len(words) > 1 and A_VERB.search(body):
        return None
    if not A_THING.match(body):
        return None
    if _only_a_nod(body):
        return None
    low = body
    words = low.split()
    # A thing that is only a determiner ("the") is not a thing.
    if not [w for w in words if w not in (
            "the", "my", "our", "his", "her", "their", "this", "that", "a", "an", "it", "just",
            "only", "mostly", "mainly", "probably", "definitely", "honestly", "maybe", "i",
            "think", "suppose")]:
        return None
    return low


def expand(text, memory):
    """The full statement this bare thing is the reason for, or None.

    None whenever the line is not a thing said as a reason: a line of its own, a line with no
    state behind it to be a reason for, or a line after a bot turn that asked nothing.
    """
    thing = _a_thing(text)
    if not thing:
        return None
    spoke = _the_bot_just_spoke(memory)
    if not spoke:
        return None
    if _already_has_it(spoke, thing):
        return None
    said, word = _the_state_they_reported(memory)
    if not said or not word:
        return None
    # The line the person typed, with the state in front of it: "im knackered" + "the baby" is
    # "im knackered, the baby", which is the sentence they would have said with more breath.
    # A long line already carries the reason ("i have been up since half four with the baby"),
    # so only the state word is kept from it.
    state = said if len(said.split()) <= 8 else "im " + word
    return state + ", " + thing


def _the_bot_would_only_shrug(line, memory):
    """True when the bot's own reply to these words on their own is a line that says nothing.

    The composer already answers some of these: straight after "im knackered", "the baby" comes
    back as "The baby - so that is the part behind it. What has been hardest about it?", which is
    a real reply and not something to be talked over. But two turns later, after the bot's own
    "which part do you want the why for?", nothing picks it up and the person gets "I'm
    listening - say more if it helps". Only the second is a reply to fix, so the composer is
    asked what it would say and only its shrugs count as a gap.
    """
    try:
        from ..compose import fallback
    except Exception:  # noqa: BLE001 - no composer to ask is not a reason to answer
        return False
    probe = copy.deepcopy(memory)
    state = random.getstate()
    try:
        # Asked as the words on their own, not as this turn: the composer's verdict pool is the
        # answer to a turn and it is the floor besides, so it made this probe report an answer
        # where the composer would only have filled in (bot/compose/fallback.py, `reply_for`).
        said = fallback.reply_for(line, probe, verdict=False) or ""
    except Exception:  # noqa: BLE001
        return False
    finally:
        random.setstate(state)
    return bool(NOTHING_SAID.search(said))


def _asked(line, memory, names=("answers", "chat")):
    """What the bot would say to this line, from the knowledge base first, then the chat.

    A reason is often a feeling rather than a fact ("im stressed, money"), and the feelings are
    answered by the chat's own readers; a reason with something to know in it ("im tired, my
    back", "im knackered, the baby") is answered from the knowledge base. The first one with
    something to say wins. `names` narrows it to one reader: a feeling with no reason in it is
    a mood, and the knowledge base's answer to the words "nothing happened" is the insomnia
    entry, which is not about a mood at all.
    """
    reading_memory = copy.deepcopy(memory)
    reading_memory["understood"] = understand(line, reading_memory)
    for name in names:
        try:
            module = importlib.import_module("..modules." + name, __package__)
            said = module.respond(line, reading_memory)
        except Exception:  # noqa: BLE001 - a reader that cannot be imported adds nothing
            continue
        if isinstance(said, str) and said.strip() and not NOTHING_SAID.search(said):
            return said.strip()
    return None


# A reason they named for how they feel, when the bot has nothing to know about it. It takes the
# reason as its subject, so the line cannot be one that would fit any message; the shapes are
# open and the question is asked about the reason, not about the person's mood.
A_REASON_TOOK = (
    "{reason} can do that to you. What is the worst of it at the moment?",
    "That is a lot to carry, and {reason} would wear anyone down.",
    "{reason} - that is the usual one. Is it worse now than it was a month ago?",
    "Anyone would be worn down by {reason}. What is the worst part of it just now?",
)


# The other half of the question a friend asks after "i feel low": "i dont know why". The joined
# line is the state said out loud with the missing reason on the end, and the readers answer it
# from the state - but a person whose low has been there a while has often just been given the
# advice for it, so the answer to the joined line is the answer they have read, word for word.
# `_without_what_was_just_said` then leaves nothing, and the turn went to the floor's receipt
# ("Thanks for telling me - I'm here if you want to dig into any of that"), which is the worst
# line in the conversation: it answers nothing and is said to someone who has just answered the
# bot's own question. What is left to say is about the missing reason, and these say it.
A_REASON_NOBODY_HAS = (
    "There's often no reason you could point at. It's still worth telling me.",
    "That's alright \u2014 a lot of it arrives without a why.",
    "You don't have to have the reason for it. Say what it's like and we'll go from there.",
    "Plenty of it has no cause you could name. It still counts.",
)


# The pools that answer a low that has been sitting there, rather than the thing that caused it.
# Their lines are written for the mood on its own ("be kind to yourself today"), so one of them
# answering a line that names a reason is the one shape this module replaces.
A_STOCK_LOW_POOLS = ("sad",)


def _a_stock_low_line(said):
    """True when the reply is one of the general lines a low mood is answered with."""
    try:
        from ..modules import chat
    except Exception:  # noqa: BLE001 - no pools to compare is not a reason to replace
        return False
    line = _flat(said)
    for name in A_STOCK_LOW_POOLS:
        for pool_line in chat.REPLIES.get(name) or ():
            if isinstance(pool_line, str) and _flat(pool_line) == line:
                return True
    return False


def _says_the_reason(said, thing):
    """True when the reply names the reason at all, so it is a reply to it and not to the mood."""
    words = [w for w in _flat(thing).split()
             if w not in ("the", "my", "our", "his", "her", "their", "a", "an", "this", "that",
                          "just", "only", "mostly", "mainly")]
    if not words:
        return True
    line = " " + _flat(said) + " "
    for word in words:
        stem = word[:5] if len(word) > 5 else word
        if re.search(r"\b" + re.escape(stem), line):
            return True
    return False


def _names_nothing(reason):
    """True when the reason is a word for every reason at once ("everything", "life", "it all")."""
    line = " " + _flat(reason) + " "
    if any(" " + phrase + " " in line for phrase in NOT_A_REASON_PHRASES):
        return True
    said = [word for word in _flat(reason).split()
            if word not in ("the", "my", "our", "his", "her", "their", "a", "an", "this", "that")]
    return bool(said) and all(word in NOT_A_REASON for word in said)


def _the_persons_own_reason(reason):
    """The reason said in the bot's mouth: theirs, so "my sleep" and "her job" are "your"."""
    said = _flat(reason)
    for pattern, replacement in A_SWAP_TO_YOURS:
        said = pattern.sub(replacement, said)
    return said


def _asks_for_the_rest(text):
    """True when the line asks for another option or the rest of the answer, naming nothing."""
    try:
        from . import another as another_module
        return another_module.names_nothing(text)
    except Exception:  # noqa: BLE001 - a module that will not import says nothing about the line
        return False


def _a_reason_for_how_they_are(thing, memory):
    """A warm line about the reason they named, from the reason itself, or None."""
    words = [w for w in _flat(thing).split()
             if w not in ("the", "my", "our", "his", "her", "their", "a", "an", "this",
                          "that", "just", "only", "mostly", "mainly")]
    if not words or len(words) > 3:
        return None
    # "everything" and "it all" would give a sentence that says nothing about anything: the line
    # is answered by the mood pools, the way it was before this module knew about reasons.
    if _names_nothing(thing):
        return None
    # A request for the rest of an answer is not a reason for how they feel: "any swaps" after
    # the advice on cutting down sugar was read as the thing wearing them down ("and any swaps
    # would wear anyone down").
    if _asks_for_the_rest(thing):
        return None
    body = pick(A_REASON_TOOK, memory, thing)
    reason = _the_persons_own_reason(thing)
    # The reason is the subject of half of these and the object of the other half, so it is
    # capitalised only where it opens the line.
    said = body.replace("{reason}", reason[0].upper() + reason[1:] if body.startswith("{reason}")
                        else reason)
    said = said[0].upper() + said[1:]
    kept = memory.get("repeated")
    if isinstance(kept, list) and said in kept:
        return None
    for turn in reversed(_turns(memory)[-2:]):
        line = str(turn.get("bot") or "").strip()
        if line:
            if _flat(line) == _flat(said):
                return None
            break
    return said


def _without_what_was_just_said(said, last):
    """The sentences of an answer the person has not just read, in order."""
    seen = _flat(last)
    kept = []
    for sentence in re.split(r"(?<=[.!?])\s+", said.strip()):
        if sentence and _flat(sentence) not in seen:
            kept.append(sentence.strip())
    return " ".join(kept)


def _a_new_answer(said, memory):
    """The same line, unless the bot has just said it or is framing it as a repeat."""
    if not said:
        return None
    last = ""
    for turn in reversed(_turns(memory)[-3:]):
        last = str(turn.get("bot") or "").strip()
        if last:
            break
    if last and _flat(said) == _flat(last):
        return None
    # The answer to the joined line can be the answer just given with one sentence added or
    # dropped. Handing back a sentence of it word for word is the repeat, so keep only the
    # sentences the person has not just read.
    if last:
        said = _without_what_was_just_said(said, last)
        if not said:
            return None
    if said in (memory.get("repeated") or []):
        return None
    if REPEATED_ON_PURPOSE.match(said):
        # "Same answer, and it covers this: ..." is the bot admitting it has said this already.
        # That is honest about a repeat, but it is not an answer to the reason they named; the
        # line is better left to the module that answers it without the frame.
        return None
    return said


def _the_feeling_without_a_reason(memory):
    """The state they reported, answered again with the missing reason said out loud.

    "im feeling really down today" / "i dont know why" is not a fragment nobody can use: the
    second line is the answer to the question a friend would ask, and the bot already knows the
    state it belongs to. Joined to that state it is a line the ordinary readers can answer -
    the feeling pool for a mood, and the knowledge base for tiredness - instead of the stock
    line the floor gives a line that names nothing.
    """
    said, word = _the_state_they_reported(memory)
    if not said or not word:
        return None
    state = said if len(said.split()) <= 8 else "im " + word
    # The state is the subject, so the knowledge base is asked about it as well: "im tired" and
    # "im exhausted" have a tiredness entry of their own, and joining "i don't know why" to that
    # state must not throw the entry away. The reason is never the subject here ("nothing
    # happened" is not asked), so the entry for lying awake cannot be reached from a mood.
    answer = _a_new_answer(_asked(state + ", and i don't know why", memory,
                                  names=("answers", "chat")), memory)
    if answer:
        return answer
    # The joined line was answered with something already said in this chat, so there is no new
    # answer in it about the state. The line the person is owed is about the reason they cannot
    # give, and this module is the only one that read that half of it.
    return _the_reason_nobody_has(memory)


def _the_reason_nobody_has(memory):
    """A line about there being no reason, not the one just said."""
    said = pick(A_REASON_NOBODY_HAS, memory, "no reason")
    kept = memory.get("repeated")
    if isinstance(kept, list) and said in kept:
        return None
    last = ""
    for turn in reversed(_turns(memory)[-3:]):
        last = str(turn.get("bot") or "").strip()
        if last:
            break
    if last and _flat(said) == _flat(last):
        # Never the same sentence twice in a row (STYLE.md): the pool is short, so the next line
        # is the one after this one rather than a repeat.
        pool = list(A_REASON_NOBODY_HAS)
        here = pool.index(said) if said in pool else 0
        said = pool[(here + 1) % len(pool)]
    return said


def _the_knowledge_base_answers_it(thing, memory):
    """True when the knowledge base has an answer to the bare thing on its own.

    The join is for words nothing answers ("the baby", "work", "money"). A thing with an entry
    of its own is a line of its own, and the entry is the answer the person should get.
    """
    try:
        module = importlib.import_module("..modules.answers", __package__)
        reading_memory = copy.deepcopy(memory)
        reading_memory["understood"] = understand(thing, reading_memory)
        said = module.respond(thing, reading_memory)
    except Exception:  # noqa: BLE001 - no knowledge reader is not a reason to refuse
        return False
    return bool(isinstance(said, str) and said.strip())


# A line that asks what the bot meant is about the bot's own last line, not a reason for how they
# feel. Typed in full ("what do you mean") the reading is `about-the-bot` and the reason-reader
# never saw it; typed as "wdym" the words of the line were the abbreviation itself, so the line
# was a "thing" and the bot answered it as the cause of the feeling it had just named:
# "im low on confidence" / "wdym" came back as "Anyone would be worn down by wdym."
def _asks_about_the_bot(text, memory):
    """True when the line is the question about the bot's last line, and the store can answer it.

    Both halves matter. The reading says the line is about the bot's last line rather than a
    reason for how they feel; the question only stands this reader down when the meant reader
    has something to say back, because a question it cannot answer is still a line somebody
    typed, and standing down for it left "im knackered" / "wdym" with the search hedge where
    main answered the tiredness card.
    """
    try:
        reading = understand(text, memory)
    except Exception:  # noqa: BLE001 - no reading is no reason to refuse the reason
        return False
    if not isinstance(reading, dict):
        return False
    if not (reading.get("topic") == "about-the-bot"
            and reading.get("kind") == "question"
            and not reading.get("entities")):
        return False
    try:
        from . import meant
        return bool(meant.answer_for(text, memory))
    except Exception:  # noqa: BLE001 - no meant reader is no reason to refuse the reason
        return False


def answer_for(text, memory):
    """The reply to the reason they named, or None when there is nothing to answer it with."""
    if _asks_about_the_bot(text, memory):
        return None
    if NO_REASON.match(_flat(text)):
        return _the_feeling_without_a_reason(memory)
    reading = expand(text, memory)
    if not reading:
        return None
    thing = _a_thing(text)
    if thing and _the_knowledge_base_answers_it(thing, memory):
        # "im feeling really down today" then "nothing happened": the two words have an entry
        # of their own in the knowledge base, and joining them to the state would send the line
        # to a different entry - the insomnia one - over the top of the answer they already
        # had. A reason the bot can answer on its own is a line of its own.
        return None
    if thing and not _the_bot_would_only_shrug(thing, memory):
        # The two words on their own already have an answer. "im knackered" then "the baby" is
        # met with "The baby - so that is the part behind it. What has been hardest about it?",
        # which is the bot asking about the reason rather than talking past the person. The gap is
        # only where the bot would otherwise shrug.
        return None
    said = _asked(reading, memory)
    # A shrug is still read as the reason it is, so a line that says "no idea" keeps whatever the
    # mood pools answer ("That's a heavy feeling, and it's fair to have it") - but there is no
    # reason in it to write a reply about, and "Dont know why can do that to you" is the bot
    # handing their shrug back to them.
    plain = bool(thing) and not NO_IDEA.search(thing or "")
    if not said:
        # The reason is a plain one and nothing in the bot knows anything about it: the state is
        # not a symptom to look up, it is a person saying what is behind how they feel. Answered
        # as the reason itself rather than with a receipt ("Maybe it's work \u2014 noted.") or a
        # shrug ("I'm listening \u2014 say more if it helps"), neither of which is a reply to a
        # guess at why they feel like that.
        return _a_reason_for_how_they_are(thing, memory) if plain else None
    if (plain and not A_BODY_OR_A_PERSON.search(thing)
            and _a_stock_low_line(said) and not _says_the_reason(said, thing)):
        # The answer is a line from a pool about a mood that has been there a while, and it would
        # fit any low day: "i feel low today, work" came back with "That sounds rough. If it's
        # been hanging around for a while, talking to someone you trust is worth it." The person
        # has just named the thing behind it and the line says nothing about it, which is the
        # machine talking past them. A pool that answers a feeling answers a feeling; a reason
        # named needs a reply about the reason.
        warmer = _a_reason_for_how_they_are(thing, memory)
        if warmer:
            return warmer
    return _a_new_answer(said, memory)
