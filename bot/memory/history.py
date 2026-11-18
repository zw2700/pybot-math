"""Questions about the conversation as a whole: what have we been on, and what came first.

The conversation lane owns this. Two things people ask about a chat they have been having have
no other home on main:

- what have we talked about ("what have we covered?", "summarise our chat")
- what came first ("what was the first thing I said?", "where did we start?")

"What did I say about X?" is read from the fact by the store's own recall (the `what did i say
about the boiler` path), so nothing here quotes a single line back.

The data is already there: memory["turns"], memory["topics"], written by
bot/modules/memory_store.py. Nothing here replies; memory_store words the answer.
"""
import re

from . import topics

# "what have we talked about", "what did we cover", "what have we been on about".
# "else" is what people add when they want the rest of the list, and "remind me" is the same
# question with the asking in front of it.
TALKED_ABOUT = re.compile(
    r"\bwhat (?:else )?(?:have|did|were) (?:we|you and i|you and me) "
    r"(?:been )?(?:talking|talked|talk|chatting|chatted|on|covering|covered|go over|through|about|discussed|discussing)\b"
    r"|\bwhat (?:topics|things|stuff) (?:have|did) we\b"
    r"|\bwhat did we (?:cover|discuss|mention|go over)(?:\s+(?:so far|today|just now|again))?\s*[?.!]*$"
    r"|\bremind me (?:what|of what) (?:we|you and i|you and me)(?:'ve|'d)? (?:have )?(?:been )?"
    r"(?:talked|spoken|chatted|discussed|covered|been on|gone over|been over)\b"
    r"|\bwhat did we go over(?:(?:\s+so far|\s+today|\s+just now))?\s*[?.!]*$")

# "what was the first thing i said", "what did i ask first", "where did we start".
# The noun alone is not enough: "what was the first thing in the box" is a question about the
# box, so the branch has to end the line or be followed by "i"/"we". "you" is the bot's own
# first line, which is a different answer (the bot's turn is kept beside the user's).
FIRST_THING = re.compile(
    r"\bwhat (?:was|were|is) (?:the|my) first (?:thing|question|topic|bit|line|message|words?)"
    r"(?:\s+(?:i|we)\b|\s*[?.!]*$)"
    r"|\bwhat did (?:i|we) (?:say|ask|mention|talk about) first\b"
    r"|\b(?:where|how) did (?:we|i|you and i) (?:start|begin)\s*[?.!]*$"
    r"|\b(?:where|how) did (?:this|our|the) (?:chat|conversation|talk) (?:start|begin|go)\b"
    r"|\bhow did we (?:get|come) (?:on|to) (?:to )?(?:this|that|it)\b"
    r"|\bwhat did (?:i|we) (?:open|start) with\b")

# The bot's own opening line: "what was the first thing you said", "what did you say first".
FIRST_SAID_BY_BOT = re.compile(
    r"\bwhat (?:was|were|is) the first (?:thing|question|line|message|words?|answer|reply) "
    r"(?:that )?you\b"
    r"|\bwhat (?:was|were|is) your first (?:thing|question|line|message|words?|answer|reply)\b"
    r"|\bwhat did you (?:say|ask) first\b"
    r"|\bhow did you start\b"
    # The opening named as when it happened rather than as "first": "what did you say at the
    # start", "what did you tell me at the beginning". Same question, and it used to reach
    # nothing at all and be handed the shrug about not knowing enough.
    r"|\bwhat did you (?:say|tell me|answer|ask)(?: \w+){0,2} (?:at the (?:very )?(?:start|beginning)"
    r"|in the beginning|early on)\b")

# "what did i say about my daughter" is a question about the chat, not a subject the chat was
# on; it can reach memory["topics"] because the store's own ask reader is narrower.
RECALL_ABOUT = re.compile(
    r"\bwhat (?:did|have|do) (?:i|we) (?:say|said|tell you|told you|mention|mentioned)"
    r"(?: to you)? about\b"
    r"|\b(?:remind me|tell me again) (?:what|of what) (?:i|we)(?:'ve)? (?:said|told you|"
    r"mentioned|talked about|been on about)\b[^?.!]*\babout\s+\w")

# The bot's own answer about a named thing: "what did you say about chewing", "remind me what you
# told me about the boiler", "what was your advice about the deposit". The person's side of this
# ("what did i say about my daughter") is the store's own recall; the bot's side reached nothing,
# and the pair of them is what a chat that remembers is for.
SAID_ABOUT_HEAD = re.compile(
    r"^(?:and |so |ok |okay |also |but |oh )*"
    r"(?:what did you (?:say|tell me|mention|suggest|recommend)"
    r"|remind me what you (?:said|told me|mentioned)"
    r"|what was (?:it|that) you (?:said|told me|mentioned)"
    r"|what was your (?:answer|advice|reply|take)"
    r"|what did you tell me)\s*(?:about|on|regarding|for)\s+(?P<thing>.+)$")

# Any line that asks about the conversation rather than about the world. The store records the
# topic of a line it answers from memory, so a chat question that nobody answered as one can
# end up in memory["topics"]; it is never a subject we have been on.
CHAT_QUESTION = re.compile(
    r"\b(?:what|which|anything) (?:else )?(?:have|did|were|do) (?:we|i|you and i|you and me)\b"
    r"[^?.!]*\b(?:talk|talked|talking|chat|chatted|chatting|discuss|discussed|discussing|"
    r"cover|covered|covering|say|said|mention|mentioned|go over|been on|spoken)\b"
    r"|\b(?:remind me|tell me again|recap)\b[^?.!]*"
    r"\b(?:talked|talk|spoken|spoke|chatted|discussed|covered|said|been on|conversation|chat)\b"
    r"|\bsummar(?:y|ise|ize)\b.*\b(?:chat|conversation|talk|said)\b"
    r"|\bwhere (?:did|do) (?:we|i) (?:start|begin|get to|leave off|started)\b"
    r"|\bwhat (?:was|is) (?:the )?(?:first|last) (?:thing|question|topic|bit|line|message|words?)\b")

# "remind me what we've covered" is the asking in front of the same question, but the store
# answers it better: it names the thing we were on and what was asked about it ("We were on
# Lisbon - you asked how many days I would give it"). A list of earlier lines cannot do that,
# so this half of the family is left to the store.
REMIND_ME_RECAP = re.compile(
    r"\bremind me (?:what|of what) (?:we|you and i|you and me)(?:'ve|'d)? (?:have )?(?:been )?"
    r"(?:covered|been on about|been on|discussed)\b")

# The store already answers these with the single thing we were on; leave them to it.
WHERE_WE_WERE = re.compile(
    r"\bwhat (?:were|are|was) (?:we|i|you) (?:talking|chatting|on) about\b"
    r"|\bwhere were we\b|\bwhat was i saying\b")


# The store already answers these itself, and better than a list of quoted lines can: "summarise
# our chat" is the picture it keeps ("So far I know you're Tom; a bus driver; ..."), and "recap",
# "catch me up" and "where did we leave it" are the one thing we were on. A list that opens with
# the oldest line answers none of them, so these stand down.
STORE_SUMMARY = re.compile(
    r"\bsummar(?:y|ise|ize)\b"
    r"|\brecap\b"
    r"|\bcatch me up\b"
    r"|\bwhere (?:did|do) we (?:leave|left|get|got)\b")

# "what does my mum eat", "where do i live", "am i vegetarian": an ask about what they have
# told you, which the store answers from memory. Whether or not it was answered, it is not a
# subject the chat was on, so it is never quoted back as one.
RECALL_SHAPE = re.compile(
    r"\bwhat (?:does|do|did|is|are|was|were) (?:my|his|her|our|their)\b"
    r"|\b(?:what|where|who|when|how many) (?:do|did|am|is|are) (?:i|we)\b"
    r"|\bam i\b|\bdo i (?:have|live|work|need|eat)\b")


def _flat(text):
    """"What have we talked about?" as plain words, punctuation stripped from the ends."""
    return " ".join(str(text).lower().replace("’", "'").split()).strip(" ?.!,")


def the_thing_named(text):
    """The thing a "what did you say about X" names, or "" when there is no such thing."""
    low = _flat(text).strip(" ?.!,")
    match = SAID_ABOUT_HEAD.match(low)
    if not match:
        return ""
    thing = match.group("thing").strip(" ?.!,")
    # "what did you say about it" and "about that" name nothing: the ask is for the last answer
    # again, which the repeat reader answers.
    if not thing or thing in ("it", "that", "this", "them", "those", "these"):
        return ""
    return thing


# The person's own side of the same ask: "what did i say about lisbon", "remind me what i said
# about the trip", "what was it i said about my tablets". It names a thing of theirs, and the
# answer is the turn that names it - not the bot's answer about it, which is a different question
# and is what `SAID_ABOUT_HEAD` reads.
MY_SAID_ABOUT_HEAD = re.compile(
    r"^(?:and |so |ok |okay |also |but |oh )*"
    r"(?:what did (?:i|we) (?:say|tell you|mention)"
    r"|(?:what|anything) have (?:i|we) (?:said|told you|mentioned)"
    r"|remind me what (?:i|we) (?:said|told you|mentioned)"
    r"|what was (?:it|that) (?:i|we) (?:said|told you|mentioned)"
    r"|did (?:i|we) (?:say|mention))\s*(?:anything\s+)?(?:about|on|regarding|for)\s+(?P<thing>.+)$")


def the_thing_they_named(text):
    """The thing a "what did i say about X" names, or "" when there is no such thing.

    The mirror of `the_thing_named`, which reads the bot's side. Kept apart from it because the
    two are answered from different turns: what they said about the tablets is their own line,
    and what the bot said about the tablets is its answer, and reading one as the other handed
    back the bot's advice where the person's line was asked for.
    """
    low = _flat(text).strip(" ?.!,")
    match = MY_SAID_ABOUT_HEAD.match(low)
    if not match:
        return ""
    thing = match.group("thing").strip(" ?.!,")
    thing = re.sub(r"\s+", " ", thing)
    if not thing or thing in ("it", "that", "this", "them", "those", "these"):
        return ""
    return thing


def asked(text, memory=None):
    """Which conversation question this is: 'topics', 'first' or None.

    `memory` is not needed for the answers here; it is passed so a caller can ask about the
    line in the store's own kept state without a second signature.
    """
    low = _flat(text)
    if WHERE_WE_WERE.search(low) or STORE_SUMMARY.search(low):
        return None
    if REMIND_ME_RECAP.search(low):
        return None
    if RECALL_ABOUT.search(low):
        # "remind me what i said about the boiler" names the thing it wants back, so the store's
        # own recall reader answers it with the line itself, in full; a summary would be worse.
        return None
    if the_thing_named(low):
        return "said_about"
    if FIRST_SAID_BY_BOT.search(low):
        return "first_bot"
    if FIRST_THING.search(low):
        return "first"
    if TALKED_ABOUT.search(low):
        return "topics"
    return None


# Nothing said yet: a greeting, a thank you, or a request for the bot to perform. These are
# not a subject the conversation has been on, so "hi" then "what have we talked about" says
# the chat has not got going rather than quoting "hi" back.
NOTHING_SAID = re.compile(
    r"\s*(?:hi|hiya|hello|hey|yo|morning|evening|good (?:morning|afternoon|evening)|\s*"
    r"how (?:are you|r you|are u)(?:\s+doing)?(?:\s+today)?|how(?:'s| is|s) it going|how are things|"
    r"what(?:'s| is|s) up|thanks?|thank you|cheers|ta|nice(?: one)?|great|lovely|ok(?:ay)?|cool|wow|"
    r"tell me (?:a|another) (?:joke|story|fact)|tell me something|say something|sing me\b[^?.!]*|"
    r"give me a joke)\s*[.!?]*\s*")


# "hi there", "morning all", "hiya everyone": the same hello with someone named after it.
GREETING_WITH_AN_ADDRESS = re.compile(
    r"\s*(?:hi|hiya|hello|hey|yo|morning|evening|good (?:morning|afternoon|evening))"
    r"(?:\s+(?:there|all|everyone|everybody|guys|folks|mate|team|both|you|y'all))+\s*[.!?]*\s*")


def _nothing_said(text):
    """A greeting, a thank you or a request to be entertained: not a subject."""
    low = _flat(text)
    return bool(NOTHING_SAID.fullmatch(low) or GREETING_WITH_AN_ADDRESS.fullmatch(low))


def about_the_chat(text):
    """True for anything that asks about the conversation itself, answered or not.

    A line like "what else have we talked about" that nothing answers is still a question about
    the chat, so it must not come back later quoted as a subject we have been on.
    """
    low = _flat(text)
    return bool(asked(low) or RECALL_ABOUT.search(low) or CHAT_QUESTION.search(low))


def not_a_subject(text):
    """Nothing we can say we have been on: a chat question, an ask about what they told you,
    a greeting, or a joke request."""
    return about_the_chat(text) or _nothing_said(text) or bool(RECALL_SHAPE.search(_flat(text)))


# A reply that speaks about something earlier in the conversation. The opening line has nothing
# behind it, so a reply like this is about a chat that never happened: "im back" as the first thing
# anyone says was answered "Welcome back. Where were we?" - a return to a conversation nobody had.
# The list is the shapes a composer reaches for when it thinks there is a history: the chat itself
# ("where we were", "what were we saying"), a thing said before ("you mentioned", "as I said",
# "last time"), and a return ("welcome back", "back again", "good to see you again").
CLAIMS_A_PAST = re.compile(
    r"\b(?:where\s+we\s+(?:were|left\s+off|got\s+to)|what\s+were\s+we\s+(?:saying|on\s+about|up\s+to)"
    r"|what\s+were\s+you\s+saying"
    r"|as\s+(?:i|we)\s+said|as\s+before|same\s+as\s+before|you\s+mentioned|earlier\s+(?:you|we)"
    r"|last\s+time\s+(?:we|you|i)\b|what\s+did\s+i\s+say|remind\s+me\s+(?:what|where|which|how)"
    r"|carry\s+on\s+where|before\s+we\s+(?:broke\s+off|stopped)|still\s+here\s*,?\s+(?:if|so)"
    r"|what\s+(?:are|were)\s+we\s+(?:working\s+on|on|talking\s+about)"
    r"|whatever\s+you(?:'ve|\s+have)\s+been\s+(?:doing|up\s+to)"
    r"|(?:a\s+)?break\s+does\s+(?:a\s+lot\s+of\s+|you\s+)?good"
    r"|keep\s+it\s+going\s+(?:for\s+)?another|since\s+we\s+last\s+spoke|last\s+we\s+spoke"
    r"|(?:we|i)\s+(?:talked|spoke)\s+about\s+(?:it|that|this)"
    r"|where\s+(?:were\s+we|did\s+we\s+get\s+to|did\s+we\s+leave"
    r"|have\s+we\s+got\s+to))\b", re.I)

# The return half of the same list, read only where a welcome can be: at the front of a reply.
# "Welcome back", "you're back", "back again", "hello again" are openers, and the same words
# inside a sentence are about something else entirely - a card about a dog left alone says "a
# proper walk before you go and another when you are back", of a person coming home in the
# evening, and the guard read that as a welcome to a conversation that had not happened. The card
# that answered the line stood down for a remark about the dog's name, on the opening line of a
# chat. Nothing before the opener but the little words a reply can start with.
GREETS_A_RETURN = re.compile(
    r"^\s*(?:(?:oh|ah|well|hello|hi|hey|right|ok|okay|and|so)\s*[,!.]?\s*)?"
    r"(?:welcome\s+back|you(?:'re|\s+are)\s+back|back\s+again|"
    r"(?:good|nice)\s+to\s+(?:see|have)\s+you\s+(?:again|back)|(?:hello|hi|hey)\s+again)\b",
    re.I)


# The other half of the same fault: a reply that *answers* a turn rather than pointing back at
# one. "sorry, i got cut off" as the first thing in a chat was answered "Good to hear. What was the
# best bit?", "as i was saying" by "Sounds alright. Anything good in it?", "carry on" by "Thanks
# for telling me", "back to what we were saying" by "Nice one. How did the rest of it go?", "same
# as before" by "I'm listening - say more if it helps." Every one of those is the right reply a
# turn later and none of them is written for a first line.
#
# These frames cannot be read the way `CLAIMS_A_PAST` is, because the same words are also a friendly
# reply to something the person has just said: "nice one", "sounds alright", "good to hear" are
# right on a first line ("weve booked a week in cornwall" is well met by "Nice one. Is it soon, or
# have you got a while yet?"), and standing those down alone changed 22 of the deck's 395 opening
# lines, five of them for the worse. What separates the two is the line they are answering: a frame
# here is only a fault when the line it answers brings nothing of its own. So a reply is read with
# the person's line, and the frame counts when the line is pointing back too.
ANSWERS_AN_EARLIER_TURN = (
    "good to hear", "glad to hear", "sounds alright", "sounds good", "nice one",
    "thanks for telling me", "thanks for that", "say more", "tell me more about that",
    "how did the rest of it go", "anything good in it", "same as before", "same answer",
    "same again", "nothing new to add", "that is still the thing to do", "as i said",
    "as you said", "like i said", "you said", "you told me", "you mentioned", "back to what we",
    "where we were", "where were we", "the same goes for", "how did that go", "what was the best",
)
# The words a line is made of when it points back and says nothing else: "go on", "carry on", "same
# as before", "as i was saying", "you told me earlier", "nothing new to add then", "sorry, i got cut
# off", "where were we". A line with any word outside this set brings something of its own - "the
# same goes for the bathroom" names the bathroom - and is answered like any other line.
NO_CONTENT_WORDS = frozenset("""
a an the as i we you he she it they me my our your us them and or but so if then than that this
these those is was were be been being am are do does did done have has had got get gets go goes
going went gone on off up down out back again please sorry said say saying says tell told earlier
before after now still just really very fine ok okay right well yes no yeah nope hi hey hello
thanks thank nothing new same add to for of in at with about what where when who how why which
carry carrying never again anyway anyways so oh ah hmm um eh sort kind lot bit one cut
missed missed replies reply replied message messages quiet silence paused pause interrupted
distracted resume continue thread thought half unfinished midway apologise apologize apologies
gone away mid
""".split())


def brings_nothing_of_its_own(text):
    """True when the line has no subject of its own, only a point back at the conversation."""
    words = re.findall(r"[a-z0-9']+", str(text or "").lower())
    if not words:
        return True
    return all(word in NO_CONTENT_WORDS for word in words)


def an_earlier_turn(memory, text=""):
    """Whether the conversation has a turn before this one.

    The runtime appends a turn after the modules answer it, so an empty history is the opening
    line. One reading of that, so every reply that leans on the chat asks the same question of the
    same place. `text` is the line being answered: a turn carrying those words is this line and
    not an earlier one, which matters to a reader that cannot rely on the store having recorded
    the line yet.
    """
    return bool(_earlier_turns(memory, text))


def a_past_that_is_not_there(reply, memory, said=None):
    """True when a reply leans on a conversation that has not happened yet.

    One question, asked by every reply that speaks about the chat: is there an earlier turn? The
    replies that say there is come in two kinds - the ones that point back at it ("welcome back",
    "where were we", "you mentioned", "as I said") and the ones that answer it ("good to hear",
    "nice one, how did the rest of it go", "thanks for telling me"), and the second kind is only
    wrong when `said` - the person's line - brings nothing of its own. A caller that does not have
    the line to hand (`said` left out) gets the pointing-back list only, which needs no gate.
    """
    if an_earlier_turn(memory):
        return False
    low = " ".join(str(reply or "").lower().split())
    if not low:
        return False
    if CLAIMS_A_PAST.search(low) or GREETS_A_RETURN.match(low):
        return True
    if said is None:
        return False
    if not brings_nothing_of_its_own(said):
        return False
    return any(frame in low for frame in ANSWERS_AN_EARLIER_TURN)


def first_bot_line(memory):
    """The first thing the bot said in this conversation, or ''."""
    turns = memory.get("turns")
    if isinstance(turns, list):
        for turn in turns:
            if isinstance(turn, dict) and str(turn.get("bot", "")).strip():
                return " ".join(str(turn["bot"]).split())
    return ""


def _earlier_turns(memory, text=""):
    """Every turn of theirs before this line, oldest first.

    The store writes the line being answered into memory["turns"] as it observes it, so the
    newest turn is this line itself and is not an earlier one. Comparing the words rather than
    dropping the last turn keeps this right for a reader called with a line the store has not
    seen yet.
    """
    mine = " ".join(str(text or "").split()).lower()
    out = []
    for row in (memory.get("turns") if isinstance(memory, dict) else None) or []:
        if not isinstance(row, dict):
            continue
        line = " ".join(str(row.get("user") or "").split())
        if line and line.lower() != mine:
            out.append(row)
    return out


# A line they asked is not a thing they said. "what was it i said about the tap", asked twice in a
# row, quoted the first ask back: "That was: "remind me what i said about the tap"". A recall is
# about a line that gave something, so the asks in the chat are not candidates for it.
A_THEY_ASKED = re.compile(
    r"\?\s*$|^(?:what|when|where|who|why|how|which|do|does|did|can|could|should|would|is|are|"
    r"was|were|have|has|will|remind|tell me|any idea|any chance)\b", re.I)


def _a_line_they_asked(row):
    """True when the turn is a question of theirs, not something they told the chat."""
    return bool(A_THEY_ASKED.search(" ".join(str((row or {}).get("user") or "").split())))


def _the_forms(words):
    """The words and the verb forms of each - "walking" asks about a line that says "walk".

    `topics.content` takes the ending off what it keeps, so the ask and the line can miss each
    other ("walking" against "walk"), and the ask then fell back to the newest line and handed
    back something said about another thing.
    """
    out = set()
    for word in words or ():
        out |= topics.forms(word)
    return out


def the_earlier_turn(memory, text="", about=""):
    """The turn of theirs this line is about, or None when the chat holds no earlier one.

    The one check for "is there an earlier turn?", and for which one. An ask that names a thing
    ("what did i say about lisbon") is about the turn that names it, not about the newest line:
    a chat that says "im saving 3000 for a trip to lisbon" and then "the flights are about 120
    each" answers the lisbon ask from the first line, where reading the newest line handed back
    a figure given for something else. When the line names nothing, or names something no turn
    has, the newest turn is the honest one.
    """
    earlier = _earlier_turns(memory, text)
    if not earlier:
        return None
    told = [row for row in earlier if not _a_line_they_asked(row)]
    if told:
        earlier = told
    thing = about or the_thing_they_named(text) or the_thing_named(text)
    wanted = _the_forms(topics.content(thing)) if thing else set()
    if not wanted:
        return earlier[-1]
    scored = [(len(wanted & _the_forms(topics.content(row.get("user") or ""))), row)
              for row in earlier]
    best = max(hit for hit, _row in scored)
    if not best:
        return earlier[-1]
    return [row for hit, row in scored if hit == best][-1]


def first_line(memory):
    """The first thing the user said in this conversation, or ''."""
    turns = memory.get("turns")
    if isinstance(turns, list):
        for turn in turns:
            if isinstance(turn, dict) and str(turn.get("user", "")).strip():
                return " ".join(str(turn["user"]).split())
    return ""


def topic_lines(memory, limit=3):
    """The subjects the conversation has been on, oldest first, as the user put them."""
    seen, out = set(), []
    records = memory.get("topics")
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        text = " ".join(str(record.get("text", "")).split())
        if not text or text.lower() in seen or not_a_subject(text):
            continue
        seen.add(text.lower())
        out.append(text)
    # The store only records a line that moves the topic on, so "he keeps scratching" after
    # "my dog Biscuit" is not a record of its own. It was still said, and "what have we
    # covered" is about what was said, so the last line joins the list - unless it was a
    # question about the chat itself, which the store answered from memory rather than from
    # the world ("what am i allergic to" is a recall, not a subject we have been on).
    turns = memory.get("turns")
    last = ""
    for turn in reversed(turns if isinstance(turns, list) else []):
        if not isinstance(turn, dict) or not str(turn.get("user", "")).strip():
            continue
        if turn.get("module") == "memory_store":
            continue
        last = " ".join(str(turn["user"]).split())
        break
    if last and last.lower() not in seen and not not_a_subject(last):
        out.append(last)
    return out[-limit:]

# ---------------------------------------------------------------------------------------------
# The rest of "is there an earlier turn?": what they said in it, and which earlier line names the
# thing this line means by "it", "that" or "their". Readers that answer a follow-up used to ask
# these questions in their own words, so two readers disagreed about the same chat: "my sister has
# two boys" / "what are their names" was answered "You haven't told me your sister's name" by one
# and echoed back at the person by another. One rule, one place: they ask here.
#
# Nothing below reads the world or the line being asked. It reads `memory["turns"]`, which holds
# the turns *before* this one, and it answers "no earlier turn" honestly for a memory with none,
# for a memory shaped wrongly, and for `None` - a module that raises is skipped without a word.
# ---------------------------------------------------------------------------------------------

# How far back a follow-up may lean. Eight turns is a chat's own subject; older than that and
# "their" is as likely to mean somebody from another part of the conversation, so a reader that
# wants further back asks for it by name.
LOOK_BACK = 8

# A turn that is their news: they have a first person in it, and it neither asks the bot anything
# nor wants something, because a want has no details to have left out and a question is the ask.
THEIR_NEWS = re.compile(r"\b(?:i|we|my|our|me|mine|us)\b|\bive\b|\bim\b", re.I)
A_QUESTION = re.compile(r"^\W*(?:what|where|when|who|why|how|which|do|does|did|is|are|was|were"
                        r"|can|could|should|would|will|shall|have|has|any)\b", re.I)
A_WANT = re.compile(r"\b(?:want|wants|wanting|need|needs|needed|hoping|hope to|planning|plan to"
                    r"|going to|thinking of|thinking about)\b", re.I)
A_BARE_YES = re.compile(r"^\W*(?:yes|yeah|yep|no|nope|ok|okay|sure|thanks|thank you|ta|right"
                        r"|cool|nice|hmm+|ah+|oh+)\W*$", re.I)


def turns_before(memory):
    """Every turn the chat has had before this one, oldest first. Never raises."""
    if not isinstance(memory, dict):
        return []
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return []
    return [turn for turn in turns if isinstance(turn, dict)]


def the_turn_before(memory):
    """The newest turn before this one, as a dict, or None when the chat has none.

    `an_earlier_turn` above is the yes-or-no that most readers want; this is the same question
    answered with the turn itself, for a reader that wants to read it.
    """
    turns = turns_before(memory)
    return turns[-1] if turns else None


def nothing_said_before(memory):
    """Whether this line is the first thing they have said.

    Read from `turns_before` rather than from `an_earlier_turn`: a `turns` list of things that are
    not turns holds nothing a reader can lean on, so it is as good as no earlier turn at all.
    """
    return not turns_before(memory)


def the_lines_before(memory, look_back=LOOK_BACK):
    """What they said in the last `look_back` turns, oldest first, empties dropped."""
    said = [str(turn.get("user") or "").strip() for turn in turns_before(memory)[-look_back:]]
    return [line for line in said if line]


def the_line_before(memory, look_back=LOOK_BACK):
    """What they said in the newest earlier turn, or ''."""
    lines = the_lines_before(memory, look_back)
    return lines[-1] if lines else ""


def is_their_news(line, words=3):
    """Whether a line is news of theirs, rather than a question, a want or a bare "yes".

    A reader that asks back a detail the person left out needs a line that could have left one
    out: "i got the job" has, "how much" has not, and "i want to go to rome" has a price tag
    rather than a detail.
    """
    said = " ".join(str(line or "").split())
    if len(said.split()) < words:
        return False
    low = said.lower()
    if said.endswith("?") or A_QUESTION.match(low) or A_BARE_YES.match(low):
        return False
    if A_WANT.search(low):
        return False
    return bool(THEIR_NEWS.search(low))


def the_news_turn_before(memory, words=3):
    """What they said in the newest earlier turn that was their news, or ''.

    "is it worth getting a flu jab" / "how much does it cost" has no news in it to leave a detail
    out of, and neither has the bare "yes" after a plan, so both answer '' and the reader that
    asked declines instead of asking the person their own question back.
    """
    for line in reversed(the_lines_before(memory)):
        if is_their_news(line, words):
            return line
    return ""


def the_earlier_line(memory, pattern, look_back=LOOK_BACK):
    """The newest earlier line of theirs that matches `pattern`, or ''.

    The pattern may be compiled or a string. This is how a follow-up finds its antecedent: "what
    are their names" looks back for the line that named more than one person, and finds it however
    the person happened to word it.
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern, re.I)
    for line in reversed(the_lines_before(memory, look_back)):
        if pattern.search(line):
            return line
    return ""


def the_earlier_lines_that(memory, pattern, look_back=LOOK_BACK):
    """Every earlier line of theirs that matches, newest last."""
    if isinstance(pattern, str):
        pattern = re.compile(pattern, re.I)
    return [line for line in the_lines_before(memory, look_back) if pattern.search(line)]


def only_with_an_earlier_turn(reader):
    """Wrap a store reader so it answers only when the chat has a turn before this one.

    A reader that hands back what was said cannot be right on the first line of a chat, whatever
    its patterns say; used as a decorator it saves each one from its own copy of the check.
    """

    def guarded(memory, *args, **kwargs):
        if nothing_said_before(memory):
            return None
        return reader(memory, *args, **kwargs)

    guarded.__name__ = getattr(reader, "__name__", "guarded")
    return guarded


# --------------------------------------------------------------------------------------------
# One check for "is there an earlier turn?", which every memory-based reply goes through.
#
# `turns_before` and `the_turn_before` above answer "did anything happen yet". These two answer
# what the answer *was*: almost every reader in this package reaches back for the bot's last line
# and each used to spell the reach out for itself - a list comprehension over the turns, a step
# back past the composer's own notes, a step back past a hedge. Three copies is three places to get
# the window wrong, and a fix in one leaves the other two answering about a turn that ended the
# thread. So `the_last_answer` is the line as written, notes and hedges included (what the person
# can see), and `the_answer_on_screen` is the answer rather than the last line. A reply with no
# earlier turn to go on gets "" and passes.
#
# Callers use the module, not the function: `from ..memory import history` then
# `history.the_last_answer(memory)`. One implementation is then the one a test can point at.
def the_last_answer(memory):
    """The bot's last line as it was written, or "" when there is no earlier turn.

    This is the raw line, notes and hedges included: what the person can see. A caller that wants
    the answer rather than the last line asks `the_answer_on_screen`, which steps back over the
    turns that are not answers.
    """
    said = [one.get("bot") for one in turns_before(memory) if str(one.get("bot") or "").strip()]
    return " ".join(str(said[-1]).split()) if said else ""


# The composer's own turn is not an answer to come back to: a note about the answer, or the
# repeat of it, adds no fact, so a follow-up two lines later still has the answer to work from.
def _a_note_not_an_answer(said):
    from ..compose import fallback, verdict

    return verdict.takes_a_fact_back(said) or fallback.is_said_it_already(said)


def _a_hedge(said):
    from ..compose import fallback

    flat = said.lower()
    return fallback._is_a_hedge(said) or any(punt in flat for punt in fallback.PUNT)


def the_answer_on_screen(memory, within=3, modules=("answers", "safety")):
    """The knowledge answer the person is looking at, or "" when the last turns hold none.

    This is the answer a follow-up is read from, so it steps back past the composer's notes and
    past a hedge - neither is an answer - and it stops at the first real answer only when that
    answer came from the knowledge base or a safety card. A turn of the store's own, or of small
    talk, is not an answer to come back with, and "" is what the caller needs to pass.
    """
    seen = 0
    for turn in reversed(turns_before(memory)):
        said = str(turn.get("bot") or "").strip()
        if not said:
            continue
        seen += 1
        if seen > within:
            break
        if _a_note_not_an_answer(said):
            continue
        if str(turn.get("module") or "") not in modules:
            return ""
        if _a_hedge(said):
            return ""
        return " ".join(said.split())
    return ""


def the_turn_the_answer_came_from(memory, within=3):
    """The turn dict `the_answer_on_screen` read, or None - for callers that need the module."""
    answer = the_answer_on_screen(memory, within)
    if not answer:
        return None
    for turn in reversed(turns_before(memory)):
        if " ".join(str(turn.get("bot") or "").split()) == answer:
            return turn
    return None


def the_answer_is_a_card(memory, within=3):
    """Whether the answer on the screen is a safety card rather than a knowledge entry."""
    turn = the_turn_the_answer_came_from(memory, within)
    return bool(turn) and str(turn.get("module") or "") == "safety"
