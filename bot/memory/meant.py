"""They ask what the bot meant, and the answer is in the line it just gave.

"what do you mean by that" is one of the commonest follow-ups in the language, and it was
answered with a search hedge ("That's beyond what I know well, sorry - searching for it will turn
up better sources"), as if the line the bot had just written had nothing to do with the question.
It has everything to do with it: the bot meant the first thing it said, or - when its own line
ended on a question - the question it asked.

So: a bare "what do you mean", pointed at the sentence the bot meant, with a lead-in that hands
the bit over ("Just this: ...").

The rule is narrow on purpose:
* the line is only that question and nothing else, so "what do you mean about the deposit" - a
  question with a thing of its own - never comes here;
* there has to be a bot turn in the last turn or two to point at, so an opening "what do you mean
  by that" (nothing has been meant yet) keeps the honest hedge;
* a hedge is never cited back at itself: where the bot had no answer, the question still gets none;
* one sentence of the answer, cut at its first clause boundary, never the paragraph again, and
  never the line this rule already gave.
"""
import re

from ..compose import pick
from . import again, repeat
from . import topics
from . import quotes as quoted

# The line is this question and nothing else.
# People do not type the question bare. They put a word or two in front of it, and often a comma
# after that word: "sorry, what do you mean", "didnt catch that, what do you mean", "im not sure
# what you mean". Each of those is the same ask, and each of them was answered with "I'm listening"
# or with a shrug, because the rule wanted the question from the first character.
OPENERS = (r"^(?:(?:and|so|but|ok|okay|well|right|sorry|wait|basically|hmm|um|er|uh|ah|oh|yeah|"
           r"then|no|nope|again|hold\s+on|alright)\b[\s,]+)*"
           r"(?:(?:i\s*(?:'m|m)\s*)?not\s+sure(?:\s+(?:what|that|if))?[\s,]+|"
           r"i\s+don(?:'t|t)\s+(?:get|understand|follow)\b[\s,]*(?:it|that|this)?[\s,]*|"
           r"(?:i\s+)?did(?:n'?t|nt)\s+(?:catch|follow)(?:\s+(?:that|you))?[\s,]+|"
           r"not\s+following[\s,]+|you\s+lost\s+me[\s,]+)*")

MEAN = re.compile(r"^\s*" + OPENERS +
                  r"(?:"
                  # The helper is the word people leave out when they type quickly, and "what" has
                  # half a dozen spellings: "wot u mean", "wat u mean", "whatcha mean", "whaddya
                  # mean by that". All of them name nothing of their own, so all of them are the
                  # same question about the line just given - and none of them were read as it, so
                  # they fell through to the search hedge or to "I'm listening".
                  r"(?:what|wot|wat|wut|whut)\s+(?:(?:do|did|d)\s+)?(?:you|u|ya)\s+mean"
                  r"(?:\s+(?:by\s+(?:that|it|this)|exactly|though|then))?|"
                  r"(?:whatcha|watcha|whaddya|whadya|whatdya)\s+mean"
                  r"(?:\s+by\s+(?:that|it|this))?|"
                  # The same question with the bot's line as the subject: "what does that mean",
                  # and the half a dozen words people put into it - "what does that *actually*
                  # mean", "what does it mean exactly", "what's that supposed to mean". Those
                  # all name nothing of their own either, and they were read one by one and
                  # missed one by one: after an answer, "what does that actually mean" got the
                  # search hedge and "whats that mean" got the maths card for a mean average.
                  r"how\s+(?:do|did)\s+(?:you|u|ya)\s+mean"
                  r"(?:\s+(?:by\s+(?:that|it|this)|exactly))?|"
                  r"what(?:'s|s)?\s+(?:(?:does|do|is)\s+)?(?:that|it|this)\s+"
                  r"(?:(?:actually|really|exactly|precisely|even|then)\s+)?"
                  r"(?:supposed\s+to\s+)?mean"
                  r"(?:\s+(?:then|though|exactly|precisely))?"
                  r"(?:\s+by\s+(?:that|it|this))?"
                  # "what does that mean for me" is the same question with the person put into
                  # it: they want the bot's own answer applied to them, not a fact about the
                  # world. It was the search hedge, one word past a form that was read.
                  r"(?:\s+for\s+(?:me|us|him|her|them|my\s+case|my\s+situation|"
                  r"(?:my|our)\s+[\w'\u2019-]+(?:\s+[\w'\u2019-]+)?))?"
                  # "what does that mean about my phone" is the same question with the thing
                  # it is asked of in the line: it was beyond the bot's knowledge and got the
                  # search hedge, though the answer above it was about the phone.
                  r"(?:\s+about\s+(?:my|our|the|this|that)\s+[\w'\u2019-]+"
                  r"(?:\s+[\w'\u2019-]+){0,2})?"
                  r"(?:\s+in\s+(?:practice|reality|real\s+terms))?"
                  r"(?:\s+(?:then|though|exactly|precisely))?|"
                  # "meaning what" and "explain what you mean" are the same ask in fewer or
                  # more words, and they were the intake form or the search hedge.
                  r"meaning\s+what|explain\s+(?:what\s+)?(?:you|u)\s+mean|"
                  r"wdym|mean\s+what\s+exactly|"
                  # "whats the meaning of that" says "meaning" and not "mean", and the one
                  # word was enough to lose the question: the maths card took it as the mean
                  # average, and after a battery answer it was a car's red oil light, because
                  # "mean" is a word in that entry's key. "that means what" is the same ask
                  # with the words the other way round.
                  r"(?:what(?:'s|s)?|what\s+is)\s+(?:the\s+)?meaning\s+of\s+(?:that|it|this)|"
                  r"(?:the\s+)?meaning\s+of\s+(?:that|it|this)|and\s+that\s+means\?|"
                  r"what\s+is\s+meant\s+by\s+(?:that|it|this)|whats?\s+the\s+meaning|"
                  r"(?:that|it|this)\s+means\s+what"
                  r"(?:\s+(?:exactly|then|though|precisely))?|"
                  # "what you mean" without the helper: "not sure what you mean", "tell me what you
                  # mean" - the opener in front of it says who is confused, not what about.
                  r"what\s+(?:you|u|ya)\s+mean|what\s+(?:that|it|this)\s+means?"
                  r"(?:\s+(?:exactly|then|though|precisely))?"
                  r")"
                  # A meaning follow-up with a filler on the end - "what does that mean, then" -
                  # is the same ask. A yes/no question hung on the end is not: see ASKS_SOMETHING.
                  r"(?:,\s*(?:then|though|exactly|precisely|really|actually)\b)?"
                  r"\s*[?.!]*\s*$", re.I)

# The clause after the comma decides whether this is one question or two. "what does that mean,
# then" is the meaning follow-up with a filler on it. "what does that mean, is she ill" is not:
# the person is worried about the cat, and the sentence the bot just said is not what they want
# handed back - they want to know whether the cat is ill, and the yes/no modules answer that. The
# hand-back read the whole line, so it answered the worry with the opening clause of the allergy
# card and left the question standing, which is worse than the hedge it replaced.
ASKS_SOMETHING = re.compile(
    r",\s*(?:is|are|was|were|am|does|do|did|will|would|can|could|should|shall|has|have)\s+"
    r"[\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,6}\s*[?.!]*\s*$", re.I)

# The same turn said the other way: they did not follow it, or did not catch it, and want the last
# thing said again in plainer words. "can you explain that again" was answered with "I don't know
# enough to answer that honestly" - as if the bot's own line had not just said something to
# explain - and "i dont understand" with "Got it - you don't understand", an echo of their words.
# Every one of these names nothing of its own, so there is only the bot's last line to point at;
# a line with a subject ("i dont understand the boiler") is a question and never comes here.
REPEAT = re.compile(r"^\s*(?:and\s+|so\s+|but\s+|ok\s+|okay\s+|well\s+|right\s+|sorry\s+|er+\s+|um+\s+)*"
                    r"(?:"
                    r"(?:can|could|would)\s+you\s+(?:please\s+)?"
                    r"(?:say|repeat|explain|rephrase|clarify)(?:\s+(?:that|it))?(?:\s+again)?"
                    r"(?:\s+please)?|"
                    r"(?:say|repeat)\s+(?:that|it)\s+again|"
                    r"explain(?:\s+that)?|explain\s+again|meaning|"
                    # "i still dont get it", "i dont get what you mean", "im confused", "you lost
                    # me": the same lost person, said with an intensifier in front or with the
                    # thing unsaid at the end. All of them were answered with an echo of their own
                    # words - "You still don't get it - noted." and "I'm listening - say more if it
                    # helps." - as if the bot's last line had not just said something to explain.
                    r"(?:i\s+)?(?:(?:still|really|just|honestly|actually|literally)\s+)?"
                    r"(?:do\s*n[o']?t|dont|does\s*n[o']?t|did\s*n[o']?t|didnt)\s+"
                    # "i dont really understand that", "i dont still follow it", "i dont get it
                    # at all": the intensifier the person put after the negated verb is the same
                    # one in front of it, and only the front one was read.
                    r"(?:(?:really|still|quite|honestly|fully)\s+|at\s+all\s+)?"
                    r"(?:understand|follow|get\s+it|catch\s+that|"
                    r"(?:get|see|follow)\s+what\s+you(?:'re|\s+are)?\s+(?:saying|on\s+about|mean))"
                    r"(?:\s+(?:it|that|this|at\s+all|one\s+bit|any\s+of\s+it|"
                    r"what\s+you\s+mean|a\s+word\s+of\s+it|the\s+last\s+bit))?|"
                    r"(?:i'?m|im)\s+not\s+(?:following|with\s+you)|"
                    r"(?:i'?m|im)\s+(?:still\s+|a\s+bit\s+|totally\s+|completely\s+)?"
                    r"(?:confused|lost)|"
                    r"(?:you\s+)?(?:have\s+)?lost\s+me(?:\s+(?:there|completely|entirely))?|"
                    r"(?:that|this)\s+is\s+confusing|"
                    r"(?:that'?s|thats)\s+confusing|"
                    r"(?:what|pardon|eh|huh)\?*|"
                    # "sorry?" with the mark is the repeat; a bare "sorry" is the apology. The
                    # courtesy word often comes with the repeat word after it instead of on its
                    # own - "sorry, what", "sorry what was that" - and only the word "what" was
                    # read as the repeat, so the whole line missed and got a search hedge.
                    r"sorry\s*,?\s*(?:what|pardon|eh|huh)?\s*\?+|"
                    r"sorry\s*,?\s*(?:what|pardon|eh|huh)\s*[?.!]*|"
                    # "in english?" is the same lost person: they want the last line put in
                    # words they can use, and it was the search hedge - as if the bot had said
                    # nothing to explain. "in plain english", "put it in english" and
                    # "whats that in english" are the same ask with the courtesy or the pointer
                    # spelled out.
                    r"(?:say|explain|put)\s+it\s+in\s+(?:plain\s+)?english(?:\s+please)?|"
                    r"what(?:'s|s|\s+is)?\s+(?:that|this|it)\s+in\s+(?:plain\s+)?english|"
                    r"in\s+(?:plain\s+)?english(?:\s+please)?|english\s+please|"
                    r"come\s+again|say\s+what"
                    r")\s*[?.!]*\s*$", re.I)

# Handing the same bit back a second time as a repeat, not as a meaning: "I said: ..." not
# "I mean this: ...", because nothing was unclear about what the bot meant - it went past them.
REPEAT_LEADS = (
    "I said: {said}",
    "Same again: {said}",
    "Let me put it plainer: {said}",
)

# How the bit comes back: a way of handing it over, not a way of talking about the bot's words.
LEADS = (
    "I mean this: {said}",
    "Just this: {said}",
    "What I meant: {said}",
)

# An ask that puts the person into it - "what does that mean for me", "what does that mean in
# practice" - is not answered by the same sentence read out a third time, but it is not the same
# ask twice either: what they want is that sentence applied to them. After "I mean this: Below 80%
# of its original capacity is when a new battery is worth it", "ok and what does that mean for me"
# got "I've put that twice now, so the words in it are probably the problem" - which tells someone
# who understood every word that the trouble is theirs.
PERSONAL = re.compile(r"\bfor\s+(?:me|us|him|her|them|my\s+case|my\s+situation|"
                      r"(?:my|our)\s+[\w'\u2019-]+)\b|"
                      r"\bin\s+(?:practice|reality|real\s+terms)\b", re.I)

# The subject a line names for itself in "what does that mean for my pay" / "for our boiler".
# The person is asking about their own thing, which is the same ask as "for me" only when the
# thing is already on the table - the answer the bot just gave, or the line the person raised it
# with. A line that brings a new subject in ("what does that mean for my mortgage" after a card
# about savings rates) is a question about that subject, not a follow-up on the bot's own line.
FOR_MINE = re.compile(r"\bfor\s+(?:my|our)\s+"
                      r"(?!case\b|situation\b|own\b|end\b|side\b|part\b)"
                      r"([\w'\u2019-]+(?:\s+[\w'\u2019-]+)?)\s*[?.!]*\s*$",
                      re.I)
PERSONAL_LEADS = (
    "For you, that means: {said}",
    "In your case: {said}",
)

# The same ask said with none of the words the patterns above are built from: "can you put that
# another way", "in simple terms", "which means what exactly", "break that down", "in what
# sense", "what does that tell me", "explain like im five". Nobody writes those as a phrase list
# and nobody should have to: every word in them is either a pointer back at the last line or a
# word for putting it in other words, and a line made of nothing else cannot be about anything
# but the last line. So the whole line is read by its words instead of by its shape -
# everything in it has to be one of these, and it has to hold at least one of the
# putting-it-plainer words. A line with any other word in it names something (a boiler, a
# number, a person) and is left to the readings above: "is that real", "are you real" and
# "what do you say" all miss on purpose.
FOLLOW_UP_WORDS = frozenset("""what whats which that this it thats those them they
    mean means meaning meant you u ya your i im sorry ok okay so then and but well just really
    actually exactly precisely simply plain plainer please can could would will do does did is
    are was were there here have has had
    put putting say saying said tell telling explained explaining explain
    break down again another other way words wording sense terms term practice reality real life
    english jargon
    technical simpler simple clearly five like of in on about to for me us him her huh pardon
    people normal someone folk most""".split())
PUT_IT_PLAINER = frozenset("""mean means meaning meant explain explained explaining
    tell telling another sense terms term practice reality english jargon technical plain words
    plainer simpler simple simply clearly break""".split())
# A figure in the line is something the person is adding or correcting, not a word for the bot's
# own words. The reading below keeps only the letters out of the line, so without this
# "sorry i meant 1.5" was the ask for the last line again - the correction was thrown away and
# the turn before it handed back: eight lines in the deck correct a figure and not one of them
# meant "say that again". "explain like im five" does not need the figure: "explain" is the word.
NOT_LETTERS = re.compile(r"[^a-z'\s]")
# "tell" only puts the last line another way when the line points at that line first: "what does
# that tell me" is the ask, and "what do i tell him" and "tell me about it" are about something
# else - a person to talk to, and an agreement - so the same word is not the same turn.
TELLS = re.compile(r"\b(?:that|this|it|those|these)\b[^.?!]{0,20}\btell", re.I)
# A question about the bot itself is not a question about the words it used, however it opens:
# "i mean what are you exactly" was answered "I said: Nothing to be bored with".
WHAT_YOU_ARE = re.compile(r"\b(?:what|who)\s+(?:are|r)\s+(?:you|u|ya)\b|\bwhat do you do\b", re.I)
# A line that ends in one of these is asking what the thing does, how long it takes or what it
# costs - "is it simple to do" - and that is a question about the thing, not about the words the
# bot used. The words above cannot tell them apart, so the ending does.
ASKING_ABOUT_DOING = frozenset("""do does did done work works took take takes costing cost
    last lasts hurt hurts help helps happen happens matter matters""".split())


def _asked_plainly(clean):
    """True when the whole line is a pointer back at the last line or a word for plainer words.

    Read by the words rather than by the shape: no word in the line can name anything, and at
    least one of them has to ask for the thing in other words. See `FOLLOW_UP_WORDS`.
    """
    said = str(clean or "").lower().replace("\u2019", "'").strip(" ?.!,")
    if NOT_LETTERS.search(said):
        return False
    words = re.findall(r"[a-z']+", said)
    if not words or len(words) > 9:
        return False
    if not set(words) <= FOLLOW_UP_WORDS:
        return False
    if not set(words) & PUT_IT_PLAINER:
        return False
    if ("tell" in words or "telling" in words) and not TELLS.search(said):
        return False
    if WHAT_YOU_ARE.search(said):
        return False
    if words[-1] in ASKING_ABOUT_DOING:
        return False
    # An ask about how to say something in another language is a different question, and it
    # always names that language: "how do i say this in french" is not this turn.
    return True
# The same ask with the thing it is asked of in the line: "what does that mean about my phone",
# "what does that mean about the boiler". It is the ask when the thing is what the last turn or
# two is about, the way "for my pay" is, and a new question when the thing is new - a boiler that
# nothing has mentioned is a question about boilers, not about the bot's own line.
ABOUT_MINE = re.compile(r"\babout\s+(?:my|our|the|this|that)\s+"
                        r"([\w'\u2019-]+(?:\s+[\w'\u2019-]+){0,2})\s*[?.!]*\s*$", re.I)
# "what does that mean for him" is the same ask about somebody the line already named - a parent
# asking about their son, or a son about a parent - so the answer is the bot's own sentence as it
# applies to that person, not "For you", which reads as if the bot had mixed the two of them up.
SOMEONE_ELSE = re.compile(r"\bfor\s+(him|her|them)\b", re.I)
SOMEONE_LEADS = "For {who}, that means: {said}"
_PERSONAL_HEADS = tuple(lead.split("{")[0] for lead in PERSONAL_LEADS) + ("For him, that means: ",
                                                                         "For her, that means: ",
                                                                         "For them, that means: ")


def _personal(said):
    """True when this line already hands the answer over as it applies to the person."""
    return (said or "").strip().startswith(_PERSONAL_HEADS)


def _their_subject(said):
    """The thing a line names for itself in "what does that mean for my pay", or ""."""
    found = FOR_MINE.search(said or "")
    return " ".join(found.group(1).lower().split()) if found else ""


def _on_the_table(noun, memory):
    """True when `noun` is already what the last turn or two is about.

    "so what does that mean for my pay" after a card about an emergency tax code is the same ask
    as "what does that mean for me": the card is about their pay and the word is in their own
    line. "what does that mean for my mortgage" after a card about savings rates names a subject
    nothing has said, so it is a question about that subject and not a follow-up on the bot's own
    line - and the bot's sentence, handed back as it applies to a mortgage, would be a guess.
    Read on the words of the last two turns both ways about, so the compound the person used
    ("payslip" for "pay", "boiler pressure" for "boiler") counts.
    """
    head = (noun or "").split()
    head = head[0] if head else ""
    if not head or not isinstance(memory, dict):
        return False
    said = ""
    for turn in (memory.get("turns") or [])[-2:]:
        if isinstance(turn, dict):
            said += " %s %s" % (turn.get("user") or "", turn.get("bot") or "")
    return bool(re.search(r"\b%s" % re.escape(head), said.lower()))


def _under_the_lead(said):
    """The answer a hand-back is carrying, whichever module wrote the lead-in.

    `_carried` reads the frames of the module that hands short forms back (`again.unframed`); this
    module's own leads ("I mean this: ...", "For you, that means: ...") are not among them, so a
    personal ask after one of those found nothing to apply to the person.
    """
    text = (said or "").strip()
    for head in sorted(_HERE, key=len, reverse=True):
        if text.lower().startswith(head.lower()):
            return text[len(head):].strip()
    return _carried(text)

SENTENCE = re.compile(r"(?<=[.!?])\s+")
# The bot's own frames for taking a line down or asking for more of it, rather than answering it.
# Handing one of those back as "I said: ..." tells the person their subject was explained when the
# bot had said nothing about it at all: "i dont follow" after "my knee clicks when i run" was
# answered "I said: Sure - I'm listening - say more if it helps.", and after "my boiler is losing
# pressure" - "I said: Thanks for telling me - I'm here if you want to dig into any of that." The
# search hedge is the same kind of line and is caught by repeat.HEDGE beside this.
RECEIPT = re.compile(
    r"^\s*(?:sure\s*[-\u2014]\s*)?(?:noted\b|got it\b|so far i know\b|"
    r"thanks for telling me\b|i hear you\b|i'?m listening\b|say more\b|tell me more\b|"
    r"that sounds\b|i'?ll keep that\b|good to know\b|nothing (?:to do|i can add)\b|"
    r"i'?m here if\b|(?:i\s+)?haven'?t put anything about it into words|"
    r"nothing of mine to go back over|is there anything you'?d like\b|"
    r"you'?re (?:noted|on the list)\b)"
    # ...and the same receipt with the thing in front of it: "A puppy \u2014 good to know.",
    # "Your sister is called Meg \u2014 noted.", "Just you, four nights, right \u2014 I've got
    # that." Citing one of those back says the bot explained the subject when it only filed it.
    r"|[\u2014-]\s*(?:noted|good to know|got it|i'?ll remember that|i'?ve got that)\b[.!]*\s*$",
    re.I)

# The bot said nothing about the thing yet, so there is nothing of its own to go back over. The
# search hedge is the wrong answer to that: nothing needs looking up, and the person is not asking
# about the world, they are asking about the last thing on the screen.
NOTHING_WRITTEN = (
    "I haven't put anything about it into words yet - give me a bit more and I'll start from "
    "there.",
    "Nothing of mine to go back over yet. Tell me a little more and I'll take it from the top.",
    # The line above opened by saying how the news lands and stopped there ("Sorry to hear it."),
    # so there is no answer of the bot's to put straighter either. Those three say the same thing
    # in the words a condolence needs, without naming it, so they fit both cases.
    "I hadn't answered anything yet, so there's nothing of mine to put straighter - tell me what "
    "you were after and I'll take it on.",
    "Nothing of mine to explain yet: I said how that landed and stopped there. Say what you were "
    "asking and I'll have a proper go at it.",
    "That was me saying how it lands, not an answer. Ask me again and I'll take it on.",
)

# The bot had no answer at all, so there is nothing of its own to go back over either. The search
# hedge repeated at a person who asked what the bot meant is the same shrug twice, and citing it
# back ("I said: I don't know enough to answer that honestly") claims there was something to
# follow. What is left to say is that there was no answer, and how to get one.
NO_ANSWER_OF_MINE = (
    "I didn't have an answer there, so there's nothing of mine to explain - it just didn't know. "
    "Say a bit more about it and I'll have a proper go.",
    "Nothing of mine to go over: I didn't know that one. Tell me more and I'll try again.",
)

# Everything the bot said about it has now been read out a second time, once under a lead. Asking
# again is not answered by the same sentence a third time; what is left to say is that it has been
# said, and to ask which word of it is the trouble.
SAID_TWICE = (
    "I've put that twice now, so the words in it are probably the problem - tell me which bit and "
    "I'll unpack that one.",
    "That is the second time I've said it that way. Which word in it is the trouble?",
)

# A clause boundary inside a long sentence: the gist is what comes before it.
CLAUSE = re.compile(r":\s+|\s+-\s+|;\s+|,\s+so\s+|,\s+and\s+|,\s+but\s+|,\s+which\s+", re.I)
# The bit handed over is short: the first clause of the sentence, one line, not a paragraph.
MOST = 150
LEAST = 30
# A sentence shorter than this says nothing worth handing over.
ANSWERED = 20
# The answer pointed at was the turn before this one, or the one before that.
LOOK_BACK = 3
# How far back to look when none of those can be handed over - every line of them a receipt, or a
# line that has already been framed. A chat that has asked twice for the same thing has two such
# lines between it and the answer.
LOOK_BACK_FAR = 7


def _sentences(said):
    """The sentences of an answer, with a quotation kept in one piece.

    The split cuts at a full stop and a space, and the words an answer hands over to say have
    full stops of their own: "say this: \"I'm not going to do this justice by Friday. Could I have
    until Tuesday?\"" is one sentence to a person and three to the splitter. Read as three, the
    first of them - half a letter, quote left open - was handed back as the sentence the bot
    meant, which is what "say that again" after the essay answer printed.
    """
    return quoted.sentences(said, SENTENCE)


# The shape of a sentence that says what a thing is or means, rather than what to do about it or
# where to look for it. "Below 80% of its original capacity is when a new battery is worth it"
# explains the figure the person asked about; "On an iPhone it is Settings > Battery > Battery
# Health" only says where to look. A line that says how the news lands and then explains after the
# colon ("That is good news, and there is nothing to do about it: a clear result means nothing was
# found") is the same case in one sentence.
DEFINES = re.compile(
    r"\bmeans?\b|\bis when\b|\bis what\b|\bis where\b|\bin other words\b|\brefers to\b|"
    r"\bstands for\b|\bwhich means\b|\bthat is what\b", re.I)


def _gist(sentence):
    """The first clause of a sentence: the bit that carries what the bot meant.

    "Most back pain is muscular and settles in two to six weeks, and staying active is what helps
    most: keep walking..." is about the two to six weeks; handing the whole thing back (and
    cutting it off with an ellipsis) says less than the gist does.

    The exception is a sentence that says how the news lands and puts the explanation after a
    colon: what was meant is on the right of it, so "That is good news, and there is nothing to do
    about it: a clear result means nothing was found" hands over the second half. The test is the
    same one `_meant` uses - the half on the right has to say what the thing means - so "Grinding
    means the pads are down to metal: stop driving and get them changed" still keeps the left.
    """
    sentence = (sentence or "").strip()
    cut = None
    after_a_colon = False
    for match in CLAUSE.finditer(sentence):
        if match.start() >= LEAST:
            cut = match.start()
            after_a_colon = match.group(0).startswith(":")
            break
    if cut is not None:
        explained = sentence[cut:].lstrip(":;- ").strip()
        if after_a_colon and len(explained) >= LEAST and DEFINES.search(explained):
            sentence = explained[:1].upper() + explained[1:]
        else:
            sentence = sentence[:cut]
    sentence = sentence.strip().rstrip(",;:- ")
    if len(sentence) > MOST:
        sentence = sentence[:MOST].rsplit(" ", 1)[0].rstrip(",;:- ")
    if sentence and sentence[-1] not in ".!?":
        sentence += "."
    return sentence


# The replies the repeat ask must never point back at: an emergency, and the two modules that
# answer a death. Read from the turn the memory store keeps, so any module added later can be
# named here without a second mechanism.
NOT_TO_REPEAT = frozenset(("safety", "loss", "grief"))

# A condolence is not an explanation, whatever follows it. "i failed my driving test" was answered
# "Sorry to hear it. Give it a day before deciding anything, then look at what you can control next
# time.", and the person who then said "im confused" was handed "Let me put it plainer: Give it a
# day ..." - as if the bot had explained the subject and they had missed it, when the line opened
# by saying how the news lands. Where the answer above opens like that, the turn falls through to
# what it did before this module read it, and a bereaved or disappointed person keeps their own
# reply. The check is on the opener only: an answer that happens to end with sympathy still counts.
CONDOLENCE = re.compile(
    r"^\s*(?:(?:oh|ah)\s*,?\s+|(?:i'?m|i\s+am)\s+(?:so\s+|really\s+|very\s+)?)*sorry\b|^\s*"
    r"(?:oh\s+no|ugh|that'?s\s+(?:rough|hard|awful|a\s+lot\s+to\s+carry)|that\s+is\s+rough|"
    r"what\s+a\s+shame|how\s+awful|that\s+sounds\s+(?:rough|tough|hard|awful|horrible))\s*[,:.\u2014-]",
    re.I)


def _answers(memory, back=LOOK_BACK):
    """The bot's own lines in the last turn or two, newest first, each with the line it answered."""
    out = []
    for turn in reversed((memory.get("turns") or [])[-back:]):
        if not isinstance(turn, dict):
            break
        said = str(turn.get("bot") or "").strip()
        if not said:
            continue
        # An emergency reply is not an explanation to point back at, and neither is a condolence: a
        # bereaved person saying "i dont understand" is not asking for "I'm sorry, that's a real
        # loss." to be read back, and "I said: ..." over it reads as if they failed to follow it.
        # The module that answered says which kind of turn this was.
        if str(turn.get("module") or "") in NOT_TO_REPEAT:
            break
        out.append((said, str(turn.get("user") or "").strip()))
    return out


def _thick_enough(said, asked):
    """True when the bot's line could be explaining something, rather than saying how the news lands.

    "Ugh, that's annoying." is the right reply to "my rent went up by 200", and it is not an
    explanation of anything: handing it back as "I said: Ugh, that's annoying." tells a person who
    asked what the bot meant that they missed something they had in front of them. A line says
    something in the person's own subject when it is long enough to, or when it takes a word of
    what they said into it; a short line that shares nothing with their line is a comment on it.
    """
    words = [w for w in topics.words(said) if w not in topics.STOPWORDS and len(w) > 2]
    if len(words) >= 5:
        return True
    theirs = {w for w in topics.words(asked) if w not in topics.STOPWORDS and len(w) > 2}
    return bool(theirs.intersection(words))


# The lead-ins this module puts on a line it hands over. `repeat.framed` knows the ones that
# module writes; a line framed by either is a hand-back already.
_HERE = tuple(lead.split("{")[0] for lead in LEADS + REPEAT_LEADS + PERSONAL_LEADS)


def _framed(said):
    """True when this line already has a hand-back lead on it, from this module or from repeat."""
    return repeat.framed(said) or (said or "").strip().startswith(_HERE)


def _a_figure(said):
    """True when the line states a figure, which is an answer however short it is.

    "180\u00b0C is 356\u00b0F." is sixteen characters and it is the whole of the answer to "what is
    180c in fahrenheit", but it is under the length a line needs before it counts as an
    explanation, so a person who said "im confused" or "what?" after it was told "Nothing of mine
    to go back over yet" - as if the bot had said nothing at all. A comment on how the news lands
    ("Ugh, that's annoying.") is short in the same way and answers nothing, and the figure is what
    tells the two apart: a line that gives one has answered something, whatever its length.
    """
    return bool(re.search(r"\d", str(said or "")))


def _a_question(sentence):
    """True when the sentence the bot would hand over is its own question."""
    return str(sentence or "").strip().endswith("?")


def _worth_handing_over(said, sentence, asked):
    """Whether what would come back is an answer rather than a way of saying how the news lands.

    A long line can be a comment with a question after it ("Ugh, that's a lot to carry. What would
    make today a bit lighter?"). Handing the comment over says the bot explained the subject when
    all it did was say how the news lands, so the sentence itself has to be an answer: it states a
    figure, it is the bot's own question (which is what "what do you mean" is asking about), or it
    says enough in the person's own subject. The whole line still has to hold something - a
    greeting that only asks "what are we working on?" has nothing to go over.
    """
    if not (_thick_enough(said, asked) or _a_figure(said)):
        return False
    return _a_figure(said) or _a_question(sentence) or _thick_enough(sentence, asked)


def _cite(said, sentence, asked="", memory=None):
    """The sentence to hand over, or None when there is nothing to cite: the bot's own line was a
    hedge (so it had no answer), a receipt for the person's line, a comment on how the news lands,
    or a hand-back that already has a lead on it."""
    if repeat.HEDGE.search(said):
        return None
    if CONDOLENCE.match(said):
        # It opened by saying how the news lands. That sentence is not an explanation of anything,
        # but the answer can be in the part after it ("Sorry to hear it. Give it a day before
        # deciding anything, then look at what you can control next time."), so the condolence is
        # taken off and the rest is read as the line: handing the whole thing back says the bot
        # explained the subject when all it did first was say how the news lands.
        said = _after_the_condolence(said)
        if not said:
            return None
        if sentence and sentence not in said:
            # The sentence picked for handing over was the condolence itself, which is not part
            # of the line any more: the answer is read off what the bot went on to say.
            sentence = _meant(said, said.rstrip().endswith("?"))
    if len(sentence) < ANSWERED and not _a_figure(said) and not _thick_enough(said, asked):
        return None
    if RECEIPT.search(said) or RECEIPT.search(sentence):
        # A line can be a receipt in one of its sentences and a question in the next ("A puppy -
        # good to know. How's it going so far?"), and the sentence is what gets handed over.
        return None
    if _framed(said):
        return None
    if said in ((memory or {}).get("repeated") or []):
        return None
    if not _worth_handing_over(said, sentence, asked):
        return None
    return _gist(sentence)


# The shape of a sentence that says what a thing is or means, rather than what to do about it.
# "Below 80% of its original capacity is when a new battery is worth it" explains the figure the
def _meant(said, asked_what_it_meant=False):
    """The sentence the bot meant: its question when its own line ended on one, otherwise the
    first thing it said that is not a hedge - or, when that first thing only tells the person
    where to look or what to do, the sentence further on that says what the thing means.

    Which one depends on the ask. "What do you mean" asks what the bot was getting at, and a line
    that ended on the bot's own question was getting at the answer to that question. "I don't
    follow" asks for the same content in plainer words, so where the line said something and then
    asked, the something is what went past them: "Then start with the smallest version of it.
    What would the first step be?" handed back as the question tells them nothing they did not
    just read.
    """
    parts = _sentences(said)
    if not parts:
        return ""
    if said.rstrip().endswith("?") and (asked_what_it_meant or len(parts) == 1):
        return parts[-1]
    first = ""
    for sentence in parts:
        if not repeat.HEDGE.search(sentence) and len(sentence) >= ANSWERED:
            first = sentence
            break
    if not first:
        return parts[0]
    if not DEFINES.search(first):
        for sentence in parts:
            if sentence == first or repeat.HEDGE.search(sentence):
                continue
            if len(sentence) >= ANSWERED and DEFINES.search(sentence):
                return sentence
    return first


# The sentence a condolence opens with, up to and including its full stop: the rest of the line
# is what the bot went on to say, which may be the answer.
CONDOLENCE_SENTENCE = re.compile(
    r"^\s*(?:(?:oh|ah)\s*,?\s+|(?:i'?m|i\s+am)\s+(?:so\s+|really\s+|very\s+)?)*sorry[^.!?]*[.!?]"
    r"|^\s*(?:oh\s+no|ugh|that'?s\s+(?:rough|hard|awful|a\s+lot\s+to\s+carry)|that\s+is\s+"
    r"rough|what\s+a\s+shame|how\s+awful|that\s+sounds\s+(?:rough|tough|hard|awful|horrible))"
    r"[^.!?]*[.!?]",
    re.I)


def _after_the_condolence(said):
    """What the bot said after it said how the news lands, or "" when it only said that.

    The condolence is the opener, not the whole line: "Sorry to hear it. Give it a day before
    deciding anything, then look at what you can control next time." has an answer in it, and a
    person asking for plainer words wants that bit, without being told the bot explained the
    subject.
    """
    cut = CONDOLENCE_SENTENCE.match(said or "")
    if not cut:
        return ""
    rest = " ".join((said or "")[cut.end():].split())
    return rest


def _same_bit(one, other):
    """Whether two lines hand over the same bit, even when one is cut shorter than the other:
    "Most back pain is muscular" and "Most back pain is muscular and settles in two weeks" are
    the same answer to the same question."""
    one = (one or "").strip().rstrip(".?! ").lower()
    other = (other or "").strip().rstrip(".?! ").lower()
    for lead in LEADS + REPEAT_LEADS:
        head = lead.split("{")[0].lower()
        if other.startswith(head):
            other = other[len(head):].strip()
    if not one or not other:
        return False
    short, long = (one, other) if len(one) <= len(other) else (other, one)
    return long.startswith(short) or short in long


def _already(cited, said_since):
    """The same bit twice reads worse than moving on: once it has been handed over, the question
    has had its answer."""
    return any(_same_bit(cited, line) for line in said_since)


def _carried(said):
    """The answer a hand-back is carrying, or "" when the line above is not one.

    Shared with the module that writes the frames (`again.unframed`), so every lead-in the codebase
    puts in front of an answer is read through: "my knee hurts when i run" twice, then "say that
    again", was answered out of the line "Same as before: Cut the distance and the speed for a week
    or two" - that is the frame's answer, and handing it back under a second frame put two lead-ins
    on one sentence.
    """
    return again.unframed(said) or ""


def _applied_to_the_person(clean, said, asked, memory, what_it_meant):
    """The last answer handed back as it applies to the person asked about, or None.

    "what does that mean for me" after a hand-back is the same sentence applied to them, not a
    repeat of the sentence, and "for him" names the person it is applied to. This is read as soon
    as the nearest answer is a hand-back, before the window widens: the sentence under the last
    hand-back is the one the person is asking about, and reaching further back for a sentence that
    `_cite` will take got "For him, that means: 4, 6 and 11 add to 21, and 21 ÷ 3 = 7, so the mean
    is 7" after a chat that had also asked what an average is - the maths card, three turns back.
    """
    if not (what_it_meant and PERSONAL.search(clean)):
        return None
    carried = _under_the_lead(said)
    if not carried or _personal(said):
        return None
    noun = _their_subject(clean)
    if noun and not _on_the_table(noun, memory):
        return None
    # The sentence under the last hand-back is the answer, whatever `_cite` makes of it: that check
    # drops a line the bot has already said, and here saying it again is the point - the same
    # sentence is being applied to the person rather than to themselves.
    cited = _cite(carried, _meant(carried, what_it_meant), asked, memory) or carried
    if not cited:
        return None
    someone = SOMEONE_ELSE.search(clean)
    if someone:
        lead = SOMEONE_LEADS.format(who=someone.group(1).lower(), said=cited)
    else:
        lead = pick(PERSONAL_LEADS, memory, clean).format(said=cited)
    return repeat.handed_back(memory, lead)


def answer_for(text, memory):
    """The bit the bot meant, or None when this is not that turn."""
    if not isinstance(memory, dict):
        return None
    # The line as the reading has it, so an abbreviation is met as the phrase it stands for: the
    # reading spells out a chat word ("wym" is "what do you mean"), and matching on the letters as
    # typed, this reader never saw the question, so a shorthand after a feeling was answered as
    # the reason for it ("Wym - that is the usual one. Is it worse now than it was a month ago?").
    clean = ((memory.get("understood") or {}).get("clean") or text or "").strip()
    # A slip in the asking is still the asking: "what dos that mean", "what dos that meen" and
    # "wot do u mean" are the same question as the spelled-out one, and the two patterns below
    # read the letters as typed. `clean` keeps the slip and the reading's own repair does not
    # (`understood["plain"]` has "what does that mean"), so a line that misses on `clean` is read
    # again as the reading repaired it. Without this the slip fell past both readers and reached
    # the pools under them: after "i have a rash on my arm", `what dos that mean` was answered
    # "I cannot weigh that one safely, sorry. Ring 111 or your surgery" - a medical hand-off for a
    # question about the sentence the bot had just said.
    repaired = ((memory.get("understood") or {}).get("plain") or "").strip()
    if repaired and repaired != clean and not (MEAN.match(clean) or REPEAT.match(clean)):
        if MEAN.match(repaired) or REPEAT.match(repaired):
            clean = repaired
    # Two ways of asking the same thing: what the bot meant, and what it said - "i dont follow"
    # and "can you explain that again" want the line again, in plainer words.
    # A question hung on the end of a meaning ask is the question: "what does that mean, is she
    # ill" wants an answer about the cat, not the last sentence again. That turn belongs to the
    # yes/no reader, so this one passes on it.
    if MEAN.match(clean) and ASKS_SOMETHING.search(clean):
        return None
    if MEAN.match(clean):
        leads = LEADS
        what_it_meant = True
        # "what does that mean for my boiler" is the same ask as "for me" when the boiler is what
        # the bot just talked about, and a new question when it is not.
        if _their_subject(clean) and not _on_the_table(_their_subject(clean), memory):
            return None
        about = ABOUT_MINE.search(clean)
        if about and not _on_the_table(about.group(1), memory):
            return None
    elif REPEAT.match(clean):
        leads = REPEAT_LEADS
        what_it_meant = False
    elif _asked_plainly(clean):
        leads = REPEAT_LEADS
        what_it_meant = False
    else:
        return None
    said_since = []
    # The window widens when nothing in the last few turns can be handed over. Asking to
    # understand the last thing better is not only about the turn just gone: the bot can have
    # said a receipt, then the person asked again, and the answer is the one behind both - the
    # answer the receipt was acknowledging. Handing back the receipt, or a search hedge a turn
    # later, gives them less than they asked about.
    lines = []
    # Once the last hand-back was already put as it applies to the person, a second personal ask
    # has had its answer: the same sentence is applied a third time if the older hand-back under it
    # is read as if it were fresh.
    applied_once = False
    for back in (LOOK_BACK, LOOK_BACK_FAR):
        for said, asked in _answers(memory, back):
            if said in said_since:
                continue
            if not applied_once and (what_it_meant and PERSONAL.search(clean)
                                     and _personal(said)):
                applied_once = True
            if not applied_once:
                applied = _applied_to_the_person(clean, said, asked, memory, what_it_meant)
                if applied:
                    return applied
            carried = _carried(said)
            if carried:
                # The line just above is already a hand-back, so citing it would put a second
                # lead-in in front of the first. The answer under the frame is what is read out.
                cited = _cite(carried, _meant(carried, what_it_meant), asked, memory)
                if cited and not _already(cited, said_since):
                    return pick(leads, memory, clean).format(said=cited)
                said_since.append(said)
                lines.append((said, asked))
                continue
            cited = _cite(said, _meant(said, what_it_meant), asked, memory)
            if cited and not _already(cited, said_since):
                return pick(leads, memory, clean).format(said=cited)
            said_since.append(said)
            lines.append((said, asked))
    # The bot has said nothing about the thing yet - what it wrote was a receipt for the person's
    # line, or a comment on how the news lands. Handing that back says the subject was explained
    # when it was not, so say which it is. Kept as a hand-back, so a second ask for it gets another
    # line from the pool rather than this one back again under a lead.
    if lines and _framed(lines[0][0]):
        # The line just handed over was itself a hand-back, so the answer behind it has been read
        # out twice: a third reading is not an answer to "i dont follow", and neither is the
        # search hedge - unless this ask is a different one. "what does that mean for me" hands
        # the same sentence over as it applies to them, once; a second personal ask gets the
        # "said twice" line, because by then it is the same sentence a third time.
        carried = _under_the_lead(lines[0][0])
        noun = _their_subject(clean)
        if (what_it_meant and carried and PERSONAL.search(clean)
                and (not noun or _on_the_table(noun, memory))
                and not _personal(lines[0][0])):
            applied = _applied_to_the_person(clean, lines[0][0], lines[0][1], memory,
                                            what_it_meant)
            if applied:
                return applied
        return repeat.handed_back(memory, pick(SAID_TWICE, memory, clean))
    if lines and CONDOLENCE.match(lines[0][0]):
        # The line above was the bot saying how the news lands, and there is no answer behind it to
        # put plainer, so it is the same case as an answer too thin to go back over. Falling
        # through here is worse than either: a card written for a feeling reads "i dont understand"
        # as the reason for one ("You don't understand. That explains it - no wonder it sits on
        # you"), so the turn is answered where it was raised.
        return repeat.handed_back(memory, pick(NOTHING_WRITTEN, memory, clean))
    if lines and repeat.HEDGE.search(lines[0][0]):
        # It had no answer, so the leftover echo of the person's own words ("Got it - you don't
        # follow") is not the reply either: saying there is nothing of the bot's to explain is.
        return repeat.handed_back(memory, pick(NO_ANSWER_OF_MINE, memory, clean))
    if lines and (RECEIPT.search(lines[0][0])
                  or (not _a_figure(lines[0][0])
                      and (not _thick_enough(lines[0][0], lines[0][1])
                           or len(_meant(lines[0][0])) < ANSWERED))):
        return repeat.handed_back(memory, pick(NOTHING_WRITTEN, memory, clean))
    return None


def reads_it(text):
    """Whether the line asks for the last answer again - the one ask that repeats on purpose.

    The hand-back this module writes is the answer just given with a lead in front of it, so the
    module that owns the turn has to know the repeat was asked for and not a card read out twice.
    """
    clean = " ".join(str(text or "").lower().split())
    return bool(MEAN.match(clean) or REPEAT.match(clean) or _asked_plainly(clean))
