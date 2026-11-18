"""The words to say, when the answer just gave them.

A person who has been told what to do often asks for the words next: "what should i say to
her", "how do i word it", "what do i text him", "what should i put in the email". By then the
answer has usually already put the sentence in their mouth - "Mention it lightly instead of
letting it fester: 'I missed hearing from you on my birthday, did it slip your mind?'", "ask
for a specific figure with the reason attached: "I'd like to move to 34,000, given..."" - and
the bot was answering all of those with "Keep it to two sentences... send me the gist and I'll
draft it", asking again for what it had already written. A wording ask is answered with the
words the last answer quoted, so the person can copy them.

So this module answers only when all three hold: the line asks for the words themselves, the
bot has just said something, and that something quoted a sentence of three words or more. It
never invents a sentence and never guesses at one: no quote in the last answer, no reply.
"""
import re

from ..compose import pick
from ..memory import last_bot

PRIORITY = 1200  # a follow-up about the wording of the answer the bot has just given

# The ask for the words, not for the decision: "what should i say to her", "how do i word it",
# "what do i text him", "how should i put this", "what should i write". A line that asks
# whether to say it at all ("should i say something") is a different question and is left alone,
# and so is a first line with nothing behind it, because there are no words to hand back.
ASKS_WORDS = re.compile(
    r"\b(?:what|how)\s+(?:should|do|would|shall|can|could|might)\s+i\s+"
    r"(?:say|text|email|message|write|reply|answer|word|phrase|tell|open|start)\b"
    # "put" is an ordinary verb about placing a thing somewhere, and the ask for the words is
    # only one of its shapes: after "what can i put in his lunchbox" the last answer had
    # quoted 'may contain nuts', and the person asking about food was handed it back with
    # "That is the whole of it, so don't add a second explanation after it". So "put" counts
    # only with the words as its object ("put it", "put this") or with a thing you write in
    # after it ("in the email", "in the card"). "What do i put on a burn" is a first-aid
    # question and keeps its own answer.
    r"|\b(?:what|how)\s+(?:should|do|would|shall|can|could|might)\s+i\s+put\s+"
    r"(?:it|this|that|these|those|them)\b"
    r"|\b(?:what|how)\s+(?:should|do|would|shall|can|could|might)\s+i\s+put\s+"
    r"(?:[^?.]{0,30}?\b(?:in|into|on)\s+)?(?:the|my|his|her|their|your|our|a|an)\s+"
    r"(?:e-?mail|letter|card|note|text|message|msg|reply|answer|application|invitation|"
    r"invite|whatsapp|bio|post|comment|review|essay|report)\b"
    r"|\bhow\s+(?:do|should|would|can|could)\s+i\s+(?:word|phrase|put)\s+(?:it|this|that)\b"
    # "how do i ask for it back" after an answer that quoted the sentence to send is the same
    # ask as "what do i say": the answer just gave the words, and the person wants them again
    # as a sentence. Only the back-reference counts - "how do i ask for a refund" is a question
    # of its own with its own answer - and the reply only exists when the answer had a quote.
    r"|\bhow\s+(?:do|should|would|can|could)\s+i\s+ask\s+(?:for\s+)?"
    r"(?:it|that|this|them|him|her|someone|somebody)\b"
    # "can i ask for it back" is the same ask said as a question about asking it: the person
    # wants the words they were just given, not permission. It has to end there, though - "can
    # i ask for it at the till" is a question about asking for a thing and keeps its own
    # answer - and the module is only this eager when the answer before quoted a sentence.
    r"|\b(?:can|could|should)\s+i\s+ask\s+(?:for\s+)?"
    r"(?:it|that|this|them|him|her)\b(?:\s+(?:back|again))?[\s.?!]*$"
    r"|\b(?:can|could|would)\s+you\s+(?:word|phrase)\s+(?:it|this|that)\b"
    r"|\b(?:give|gimme)\s+me\s+the\s+words\b|\bwhat\s+are\s+the\s+words\b"
    r"|\bwhat(?:'s| is)\s+the\s+wording\b"
    # Said helplessly rather than as a question, which is how most people ask for the words:
    # "i dont know how to tell her", "no idea how to say it", "not sure how to word this". The
    # ask is the same one, and without this the sharpest line of the chat - the one right after
    # the answer handed them a sentence - was the one that fell to the search hedge.
    r"|\b(?:don'?t|do\s+not|dont|no\s+idea|not\s+sure|never\s+know\s+how|can'?t\s+work\s+out)"
    r"\s+(?:know\s+)?how\s+to\s+"
    r"(?:tell|say|word|phrase|put|ask|bring|raise|mention|open|start|write|text|email|message)\b"
    r"|\b(?:don'?t|do\s+not|dont|no\s+idea|not\s+sure)\s+what\s+to\s+"
    r"(?:say|text|write|reply|message|email|call|tell)\b", re.I)

# A quoted sentence in the bot's own answer: 'I missed hearing from you on my birthday', "Hi -
# the boiler has stopped working", “...”. ASCII and typographic, and short quotes are skipped
# because "'no'" is not a sentence to hand back.
# A quote opens and closes where a quote mark stands alone, and the apostrophe inside a word is
# not one of those. "Ask once: 'I'm sorting my budget, when can you pay me back?'" ends on the
# mark after the question: without the lookarounds the span stopped at "I" - the apostrophe in
# "I'm" closed it - and the person was handed "m sorting my budget" instead of the sentence.
QUOTED = re.compile(
    r"(?<![A-Za-z0-9])'((?:[^']|'(?=[A-Za-z])){12,300})'(?![A-Za-z0-9])"
    r"|(?<![A-Za-z0-9])\"((?:[^\"]|\"(?=[A-Za-z])){12,300})\"(?![A-Za-z0-9])"
    r"|\u201c([^\u201d]{12,300})\u201d"
    r"|\u2018([^\u2019]{12,300})\u2019")

# Said back with the words, so the reply is the sentence to use and not a line about it. Each
# one is a thing a friend says after handing over the words: use them, then stop.
LINES = (
    "{words} Say that, and leave it there - it gives them an easy way to answer.",
    "{words} That is the whole of it, so don't add a second explanation after it.",
    "{words} Say it once, early, and let the silence do the rest.",
    "{words} Keep to those words and let them reply in their own time.",
    "{words} The short version lands better than a speech, so stop there.",
)


# A quote can be a sentence to send or an example of a kind of thing. "Send one small, specific
# message - a photo, a 'saw this and thought of you', or a question only they would know the answer
# to" was listing sorts of message, and the follow-up "what do i say" handed the noun phrase back
# with "Say that, and leave it there": the person was given a fragment to send when the answer had
# never written one. A phrase introduced by an article, by "like" or by "such as", and punctuated
# as neither a sentence nor a clause, is the answer naming a sort, so it is skipped. The next quote
# is tried, and an answer with no real sentence in it leaves nothing to hand back.
EXAMPLED = re.compile(r"(?:\b(?:a|an|the|one|like|such\s+as|e\.g\.))\s*$", re.I)


def _quoted(said):
    """The first quoted sentence of three words or more in the bot's last reply, with its marks.

    The marks come back with it because the answer chose them: a sentence the answer set in
    double quotes is handed back in double quotes, so it looks on screen as it did a turn ago.
    """
    text = str(said or "")
    for match in QUOTED.finditer(text):
        words = next((group for group in match.groups() if group), "").strip()
        if len(words.split()) < 3:
            continue
        if EXAMPLED.search(text[max(0, match.start() - 18):match.start()]):
            if not re.search(r"[?!.]$", words) and "," not in words:
                continue  # a sort of message, not one to copy
        return match.group(0).strip()
    return ""


# The ask for the words is the whole line. After the wording verb comes, at most, a back-reference
# to the answer just given ("say it", "word this"), the person the words go to ("say to him", "put
# in the email", "text my boss"), and the odd filler word. Anything else is the person's own
# question and has its own answer - "say no", "say sorry", "say thanks", "tell him i'm leaving",
# "tell my mum i failed", "say it without a row" - so this module passes on it. Without this gate,
# one work answer that quoted a sentence made every one of those an ask for its words and handed
# the same quote back: seven of twelve typed lines got a sentence about the wrong thing, and the
# deck's own "how do i say it without a row" lost the answer about not having a row. A missed
# hand-back costs one line that answers as it did before; a wrong one is a confident sentence
# about something else.
ASK_OBJECT = re.compile(
    r"^(?:"
    r"(?:it|this|that|them|those)\b"
    r"|(?:to|for|at|with|in|on)\s+(?:him|her|them|it|this|that|me|us|everyone|somebody|anybody)\b"
    r"|(?:to|for|at|with|in|on)\s+(?:my|his|her|their|our|your|the|a|an)\s+[a-z']+"
    r"|(?:him|her|them|everyone|somebody)\b"
    r"|(?:my|his|her|their|our|your|the)\s+[a-z']+"
    r")", re.I)
# "bring it up" and "say it out loud" carry the particle of their own verb after the object,
# which is part of the ask and not a subject of its own.
ASK_FILLER = re.compile(r"^(?:please|then|instead|just|really|up|out|loud|back)\b[,.]?", re.I)


def _names_its_own(line):
    """True when the line asks for the words *and* says what they are for.

    "what should i say to him" is the ask and nothing else, so the words of the last answer are
    the answer. "how do i say sorry" and "how do i say it without a row" carry their own subject,
    and the answer two turns back is not it.
    """
    match = ASKS_WORDS.search(line)
    if not match:
        return True
    rest = line[match.end():].strip()
    for step in range(2):
        rest = rest.strip(" ,.-")
        moved = ASK_OBJECT.match(rest)
        if moved:
            rest = rest[moved.end():].strip()
        for _ in range(3):
            filler = ASK_FILLER.match(rest)
            if not filler:
                break
            rest = rest[filler.end():].strip()
    return bool(re.sub(r"[^a-z0-9]", "", rest.lower()))


def _the_words(text, memory):
    """The quoted words this line is asking for, or "" when this line is not that ask."""
    line = str(text or "").strip()
    if not line or len(line.split()) > 14 or not ASKS_WORDS.search(line):
        return ""
    if _names_its_own(line):
        return ""  # "how do i say sorry" names its own question and has its own answer
    return _quoted(last_bot(memory))


def TAKES_AS_IT_COMES(text, memory):
    """This line is asking for the words the last answer already gave, so it is this module's.

    The reply is a quote of the answer, so on the surface it looks like the bot saying the same
    thing twice, and a general module that answers the same line about something else - a
    birthday-card line for "what should i say to her" - is preferred to it by the specialist
    fit. Declaring the line instead of raising PRIORITY says that for this reading only.
    """
    return bool(_the_words(text, memory))


def respond(text, memory):
    line = str(text or "").strip()
    words = _the_words(text, memory)
    if not words:
        return None
    # The quote keeps the punctuation the answer gave it; a sentence that opens inside a longer
    # one ("Hi - the boiler has stopped working, please let me know when an engineer can come")
    # is handed back as the answer wrote it, in the same marks.
    return pick(LINES, memory, line).format(words=words)
