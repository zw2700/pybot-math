"""The chat-speak people hang off the end of a line, and the line without it.

It is not part of what they told you: the fact is "my sister is called meg", and "you said your
sister is called meg to be honest" says the fact back with a shrug on it. The reply that notes a
line, the summary that quotes it, and the plan the store keeps all read this, so the words that
are only a shrug are dropped in one place rather than three.
"""

# Only pure filler is here, so "as well" ("my knee is bad as well") and "right" stay where the
# person put them.
TAIL_OFF = frozenset("""tho though lol lmao haha ha hehe tbh ngl imo idk innit x xx xxx
    actually btw""".split())

# The shrug is a phrase as often as it is a word, and the phrases are the ones people hang on the
# end of a question: "how old is my son by the way", "whats the postcode out of interest". Read as
# words of the line they were the subject of the ask - the age ask reached nothing and the answer
# on the screen was "I'm not sure about that one", and the trip the chat holds came back as "You
# go to cornwall bies the way in August". Longest first, so "by the way" is taken whole.
TAIL_PHRASES = ("by the way", "out of interest", "while im at it", "whilst im at it",
                "as it happens", "if thats ok", "if that's ok", "if you dont mind",
                "if you don't mind", "come to think of it", "now i think of it",
                "now that i think of it")

# The same shrugs, put in the middle of the line rather than on the end: "what can I actually do
# to help her", "is it really that expensive". They are not part of what is asked either, and a
# reader that has to see the question under them - the follow-up read with the topic put back in
# - was reading the shrug as one more word of the subject and reaching nothing.
IN_THE_WAY = frozenset("actually really honestly literally genuinely basically".split())


def without_filler(said):
    """`said` without the chat-speak hanging off the end: "im veggie tho" -> "im veggie"."""
    words = str(said or "").split()
    while len(words) > 1 and words[-1].lower().strip(".,;:!?") in TAIL_OFF:
        words.pop()
    # The phrases go last and all at once, so the words of a shrug that is a phrase are never read
    # as words of the line: "by the way" is not about a way, and "out of interest" is not about
    # interest.
    text = " ".join(words)
    changed = True
    while changed and text:
        changed = False
        stripped = text.rstrip(" .,;:!?")
        low = stripped.lower()
        for phrase in TAIL_PHRASES:
            if low.endswith(" " + phrase) or low == phrase:
                cut = stripped[:len(stripped) - len(phrase)].rstrip(" ,;:-")
                if cut:
                    text = " ".join(cut.split())
                    changed = True
                break
    return text


# What is dropped from an ask and from an ask only: the phrases people hang on a question, and the
# two words that are a shrug when they end one ("how old is my son by the way", "whats it actually
# like"). The words in TAIL_OFF that carry a meaning of their own - "though" turns a line into the
# other side of an argument, "tho" is the same shrug - are left to the readers that already read
# them: dropping "though" from "is that legal though" turned the answer into the one before it.
ASK_TAIL = ("by the way", "btw", "out of interest", "while im at it", "whilst im at it",
            "as it happens", "if thats ok", "if that's ok", "if you dont mind", "if you don't mind",
            "come to think of it", "now i think of it", "now that i think of it", "actually")


def without_the_end_shrug(said):
    """`said` without the shrug hung on the end of an ask: "how old is my son by the way"."""
    text = " ".join(str(said or "").split())
    changed = True
    while changed and text:
        changed = False
        stripped = text.rstrip(" .,;:!?")
        low = stripped.lower()
        for phrase in sorted(ASK_TAIL, key=len, reverse=True):
            if low.endswith(" " + phrase) or low == phrase:
                cut = stripped[:len(stripped) - len(phrase)].rstrip(" ,;:-")
                if cut:
                    text = " ".join(cut.split())
                    changed = True
                break
    return text


def without_the_shrug(said):
    """`said` without the fillers in the middle of it: "what can i actually do" -> "what can i do".

    One word is always left, so a line that was nothing but a shrug comes back as it was.
    """
    words = str(said or "").split()
    kept = [word for word in words if word.lower().strip(".,;:!?") not in IN_THE_WAY]
    return " ".join(kept) if kept else " ".join(words)
