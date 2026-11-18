"""A check-with-you question - "u ok with that", "is that ok with you" - gets an answer.

One shape, and today it lands in seven different places, none of them an answer:

    u ok with that           -> "Thanks for telling me - I'm here if you want to dig into any of that."
    are you ok with that     -> "I'm a chatbot, not a person: a program built to help ..."
    are you fine with that   -> "That's beyond what I know well, sorry. Searching for it ..."
    u happy with that        -> "Lovely to hear. Enjoy it!"
    you good with that plan  -> "Got it. Is there anything you'd like a hand with?"
    is that ok with you      -> "I don't know enough to answer that honestly. A search should ..."
    does that work for you   -> "That's beyond what I know well, sorry. Searching for it ..."

Three of those are the search hedge, two are receipts (the person's own words handed back), one
reads "are you ok" as a question about what the bot is, and "u happy with that" was taken as a
report of good news. The line is not any of those things: the person is checking a plan against
the bot, and the only honest answer is agreement plus whose call it is. The bot has no stake; the
person does, so the line says it is fine by the bot and leaves it with them.

The shapes are tight on purpose - the bot as the subject with a stance word and a connector, or
an object stance with the bot as the one it has to suit - because the same words in other orders
belong to other readers: "is that ok to drive on" is a question about a thing (the cards have the
driving rules), "are you safe to talk to" is the privacy card, and "u alright to drive" is the
person checking themselves, which has no business being answered by a bot.
"""
import re

# The stance word, and the connectors that make a check out of it.
_STANCE = r"(?:ok|okay|alright|all\s+right|fine|happy|cool|good|easy|content)"
_OBJECT = (r"(?:that|this|it|them|those|these|the\s+\w+|my\s+\w+|"
           r"me(?:\s+\w+ing)?|me\s+\w+|if\s+i\b|it\s+if)")

# 1. The bot as the subject: "are you ok with that", "u happy about it", "you fine with that".
_A_CHECK_ASKED = re.compile(
    r"\b(?:are|r|is|was|do|does|would|will|could)?\s*(?:you|u|ya)\s+"
    r"(?:really\s+|still\s+|definitely\s+)?(?:be\s+)?" + _STANCE + r"\s+"
    r"(?:with|wiv|wid|about|by)\s+" + _OBJECT + r"\b"
)
# 2. The object as the subject and the bot as the one it has to suit: "is that ok with you",
#    "was that alright for you". "is that ok for the plant" is a different reader's line, because
#    the person it has to suit is not the bot.
# Only the stance words that mean "alright with you" here. `good for you` is not a check - "i had a
# big bowl of rice" / "is that good for you" is the health question, and answering "fine by me" to
# it is a confident wrong answer about food.
# The copula is optional because chat drops it: "is that ok with you" arrives as "that ok with
# you" and "that alright with you" about as often as with the verb.
_A_THING_FOR_YOU = re.compile(
    r"\b(?:(?:is|was|are|were)\s+)?(?:that|this|it|those|these)\s+(?:really\s+)?"
    r"(?:ok|okay|alright|all\s+right|fine)\s+(?:with|wiv|wid|by|for)\s+(?:you|u|ya)\b"
)
# 3. The same check said as a verb: "does that work for you", "would that suit you", "works for
#    you?". Only the two verbs that carry a check; "does that sound like you" is a different line.
_A_VERB_FOR_YOU = re.compile(
    r"\b(?:does|do|would|will|did)?\s*(?:that|this|it)\s+(?:work|suit|square|be\s+alright|"
    r"be\s+ok|be\s+fine)\s+(?:for|with|wiv|wid)\s+(?:you|u|ya)\b"
)
# "works for you?" and "ok with you?" with the subject left off - a follow-up, which is how it is
# usually typed after a plan has just been said.
_A_VERB_YOU = re.compile(
    r"\b(?:does|do|would|will|did|is)\s+(?:that|this|it)\s+(?:work|suit|do)\s+(?:you|u|ya)\b"
)
# The stance words a bare line can carry. `good` is not one of them: "good for you" on its own is
# the congratulation, not a check of anything, and the bot's own "good for you" answer is right.
_BARE_STANCE = r"(?:ok|okay|alright|all\s+right|fine|happy|cool|easy|content)"
_BARE_FOR_YOU = re.compile(
    r"^\s*(?:so\s+)?(?:" + _BARE_STANCE + r"|work|works|suit|suits|square)\s+"
    r"(?:for|with|wiv|wid|by)\s+(?:you|u|ya)\s*\??\s*$"
)

A_CHECK = (_A_CHECK_ASKED, _A_THING_FOR_YOU, _A_VERB_FOR_YOU, _A_VERB_YOU, _BARE_FOR_YOU)

# Agreement, and whose call it is. Never a question back: the person asked a yes/no about a plan
# and the answer is the yes, with the one thing the bot can add - that it is not the bot's call.
AGREED = (
    "Fine by me - and it's your call, not mine.",
    "That suits me. Whether it suits you is the part I can't answer.",
    "No objection here. You're the one it has to work for, though.",
    "Sounds alright to me. I've got nothing at stake in it either way.",
    "Happy with that. It's your call at the end of it.",
    "Works for me - just don't count me as the one who decided it.",
    "That's fine as far as I'm concerned. What matters is whether it's fine by you.",
)

# Words that put the line in another reader's hands even when the shape matches. "drive", "tow",
# "insure" and "sign" are the person checking themselves or a thing, and the cards answer those.
_NOT_A_CHECK = re.compile(
    r"\b(?:drive|driving|tow|towing|insure|sign|signing|sue|arrest|publish|fly|flying|"
    r"sail|carry|carrying|keep\s+it|eat|drink)\b"
)


def reads_as_a_check(text):
    # `sure` is not in the stance list on purpose: "are you sure about that" is a question about
    # the bot's own certainty, not a check of a plan, and answering it "fine by me" would be a
    # confident wrong answer to a fair question.
    """True when the line is a check of a plan against the bot."""
    said = " " + re.sub(r"[^a-z0-9'? ]", " ", (text or "").lower()) + " "
    if _NOT_A_CHECK.search(said):
        return False
    for shape in A_CHECK:
        if shape.search(said) or (shape is _BARE_FOR_YOU and shape.search(said.strip())):
            return True
    return False


def answer_for(text, memory=None, choose=None):
    """The agreement line, or None when this is not a check-with-you question."""
    if not reads_as_a_check(text):
        return None
    if choose is None:
        import random
        choose = random.choice
    return choose(AGREED)
