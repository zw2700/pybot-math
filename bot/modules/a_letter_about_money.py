"""A letter about money is answered by what is on the page, not by guessing at it.

"i got a letter about a benefit overpayment" and "i got a bill i wasnt expecting" name a piece
of post the person has and the bot cannot see. The knowledge base has cards for some of these
subjects, but the ones it does not know fell to the greeting - "Go on then - what was the answer?"
to a letter nobody had asked about, or "Noted: you got a bill you weren't expecting." That is the
wrong subject: the person needs to know what to do with the letter.

So this module answers only a line that says a letter, notice or bill has arrived and names
money on it, and it says the three things a friend can: what to find on the page, to ask for the
breakdown and answer in writing, and to keep a copy. A card that knows the subject sits above
this one and keeps the turn; a letter about anything else is not this answer.

The mirror line - "the bill hasnt arrived", "my benefit letter never arrived" - is the same
subject and the opposite state, and the arrival reader matches its verb. It gets its own short
answer (check the sender's account or phone line, confirm the address, note the date), because
telling somebody what is on a page they do not have is the confident wrong answer this module
exists to avoid.
"""
import re

PRIORITY = -600  # above the greeting, below every module that knows the subject itself

# The post arriving, then the thing: "i got a letter", "i received a notice", "the dwp sent me a
# bill". A letter that is only being written or read is not this shape.
_ARRIVED = re.compile(
    # The giving direction: "i got a letter", "i received a notice", "i had a bill". "have" is
    # allowed only when it is not "have to" (an obligation to write one, not a letter in hand).
    r"\b(?:got|received|receive|had|have(?!\s+to))\b"
    r"[^.!?]{0,30}\b(?:a|an|this|the|my|our)\s+(?:[a-z'-]+\s+){0,2}(?P<thing>letter|notice|bill)\b"
    # "i was sent a letter", "i got sent a notice", "they sent me a bill"
    r"|\b(?:was|were|been|be|got)\s+sent\b[^.!?]{0,20}\b(?:a|an|this|the|my|our)\s+"
    r"(?:[a-z'-]+\s+){0,2}(?P<thing4>letter|notice|bill)\b"
    r"|\bsent\s+(?:me|us)\b[^.!?]{0,20}\b(?:a|an|this|the|my|our)\s+"
    r"(?:[a-z'-]+\s+){0,2}(?P<thing5>letter|notice|bill)\b"
    # "my benefit letter says i owe", "the notice about my tax credits", "a letter from the dwp"
    r"|\b(?:a|an|my|our|the|this)\s+(?:[a-z'-]+\s+){0,2}(?P<thing2>letter|notice|bill)\b"
    r"[^.!?]{0,25}\b(?:says?|said|about|from|saying|came|arrived|turned\s+up)\b"
    # "the bill came today", "a notice turned up" - the thing first, the arrival after it
    r"|\b(?:a|an|my|our|the|this)\s+(?:[a-z'-]+\s+){0,2}(?P<thing3>letter|notice|bill)\b"
    r"[^.!?]{0,20}\b(?:came|arrived|turned\s+up)\b", re.I)
# The other direction shares the verbs: a letter they are writing, sending away, or asking for is
# not one that has arrived. Only the words before the matched thing matter, so a later "and sent
# a reply" does not hide a letter that was received first.
# The same nouns and verbs with the arrival denied. A letter that has not come is not a letter in
# hand; the arrival reader would otherwise match its verb and describe a page nobody has.
_NOT_YET = re.compile(
    r"\b(?:hasn'?t|hasnt|haven'?t|havent|hadn'?t|hadnt|didn'?t|didnt|never|not|still\s+no|no)\b"
    r"[^.!?]{0,30}\b(?:arrived|arrive|come|came|turned\s+up|turned\s+up|show(?:ed|n)?\s+up|been\s+sent|receive|received|got|get|had)\b"
    r"|\b(?:still\s+)?waiting\s+(?:for|on)\b"
    r"|\bno\s+(?:[a-z'-]+\s+){0,3}(?:letter|notice|bill)\b[^.!?]{0,20}\byet\b", re.I)
_OUTGOING = re.compile(
    r"\b(?:i|we)\s+(?:sent|send|sending|posted|post|posting|wrote|write|writing|need|needs|want|wants|asked|asking)\b"
    r"|\b(?:have|had|got|need|needs|want|wants)\s+to\s+(?:write|send|post|get|receive)\b"
    r"|\b(?:can|could|may|might|should|would|will)\s+(?:i|we)\s+(?:get|have|receive|request|ask)\b"
    r"|\b(?:could|can|would|will)\s+you\s+(?:send|post|write|get)\b"
    r"|\b(?:writing|sending|posting)\s+(?:a|an|the|my|our)\s+(?:letter|notice|bill)\b", re.I)
# Money has to be named on it. The thing itself counts for a bill: "i got a bill for 600" has no
# other money word, and a bill is money by definition.
# The words this answer turns on, with the misspellings people type. A letter about a "benifit"
# is the same letter; the module should not lose the turn to one wrong vowel.
_SPELLINGS = (
    (re.compile(r"\brecieved\b|\brecived\b|\breceved\b"), "received"),
    (re.compile(r"\bbenifits?\b|\bbenfits?\b"), "benefits"),
    (re.compile(r"\blett(?:re|r|ar|e)\b"), "letter"),
    (re.compile(r"\buniveral\b"), "universal"),
    (re.compile(r"\boverpaymant\b"), "overpayment"),
    (re.compile(r"\bhousng\b"), "housing"),
)
_MONEY = re.compile(
    r"\b(?:overpay(?:ment|ments)?|overpaid|benefits?|universal\s+credit|tax\s+credits?|"
    r"housing\s+benefit|child\s+benefit|dwp|hmrc|tax|taxes|council\s+tax|arrears?|debt|debts|"
    r"owe|owed|owes|repay|repayment|money|amount|charge|charges|bill|bills|rent|rents|"
    r"mortgage|insurance|loan|loans|credit\s+card|pension|pip|dla|esa|jsa|income\s+support|"
    r"student\s+loan|fine|fines)\b", re.I)

LETTER_LINES = (
    "I can't read the letter from here, but the answer is on the page: the date they want a reply "
    "by, the amount and the period it covers, and the reference. Ask for the breakdown in "
    "writing, answer in writing before that date, and keep a copy; if it is a decision, the "
    "letter says how to challenge it and by when. Tell me the amount and the dates on it and "
    "I'll help you check it.",
    "That letter has three things worth finding before anything else: the date they want an "
    "answer by, the amount and the period it covers, and the reference. Ask for the breakdown "
    "in writing and put your answer in writing too, keeping a copy. If it is a decision you can "
    "challenge, the deadline is on the letter. What does it say the amount is?",
)
BILL_LINES = (
    "A bill is worth checking before you pay it: the dates it covers, "
    "what it says you are being charged for, and the reference. Ask for the breakdown in "
    "writing, and if it is wrong say so in writing before the date on it; keep a copy. Tell me "
    "the amount and the dates on it and I'll help you check it.",
    "Before paying a bill you did not expect, check the dates it covers, what it is charging "
    "for, and the reference. Ask for the breakdown in writing, and answer in writing before "
    "the date on it, keeping a copy. What is it for, and how much?",
)
NOT_YET_LINES = (
    "If it should have arrived, the sender's own account page or phone line is where to check it "
    "was sent and to which address - ask them to confirm the date it went out, and note who you "
    "spoke to and when. When it comes, the reply-by date and the reference are the two things to "
    "look for first.",
    "Before it arrives, check the sender has your current address: their account page or a phone "
    "call can confirm when it was sent and to where. Keep a note of the call. When it comes, the "
    "reply-by date and the reference are the two things to note first.",
)
# The reply should ask for what the person has not already said. A line that carries the figure
# does not need "how much?" back; a line that carries the date does not need "the dates". The
# reference and the period are the two things that are on the page and not in the sentence.
_AMOUNT = re.compile(
    r"(?:£\s*\d|\b\d+(?:[.,]\d+)?\s*(?:pounds?|quid|p|pc|per\s?cent|%)\b|"
    r"\b(?:for|of|cost(?:s|ing)?|paid|owe[sd]?)\s+£?\d+\b)"
)
_DATE = re.compile(
    r"\b(?:today|yesterday|tomorrow|this\s+(?:week|month|year)|last\s+(?:week|month|year)|"
    r"next\s+(?:week|month|year)|"
    r"(?:january|february|march|april|may|june|july|august|september|october|november|december)|"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b", re.I)


def _ask_for_what_is_missing(line, clean, thing):
    """Point the question at the detail the line does not already carry.

    The first reply asks for both the amount and the dates; a person who has just written
    "my bill came to 80 pounds" has answered half of that. Asking it back reads as if the bot
    did not listen, and the useful thing left is the period, the reference or what it is for.
    """
    has_amount = bool(_AMOUNT.search(clean))
    has_date = bool(_DATE.search(clean))
    if not has_amount:
        if not has_date:
            return line
        return line.replace(
            "Tell me the amount and the dates on it and I'll help you check it.",
            "Tell me the amount on it and I'll help you check it.",
        )
    if not has_date:
        return line.replace(
            "Tell me the amount and the dates on it and I'll help you check it.",
            "Tell me the dates it covers and I'll help you check it.",
        ).replace(
            "What is it for, and how much?",
            "What is it for, and what dates does it cover?",
        )
    return line.replace(
        "Tell me the amount and the dates on it and I'll help you check it.",
        "Tell me the reference and I'll help you check it.",
    ).replace(
        "What does it say the amount is?",
        "What is the reference on it?",
    ).replace(
        "What is it for, and how much?",
        "What is it for, and what is the reference?",
    )


def respond(text, memory):
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return None
    for pattern, right in _SPELLINGS:
        clean = pattern.sub(right, clean)
    match = _ARRIVED.search(clean)
    if match is None:
        # "the bill hasnt come yet" has the noun and the denied arrival but no positive arrival
        # verb for `_ARRIVED`; the state is still the same one this pool answers.
        if (_NOT_YET.search(clean) and _MONEY.search(clean)
                and re.search(r"\b(?:letter|notice|bill)\b", clean, re.I)
                and not _OUTGOING.search(clean)):
            return _pick(NOT_YET_LINES, memory)
        return None
    if _OUTGOING.search(clean[:match.start()]):
        return None
    thing = (match.group("thing") or match.group("thing2") or match.group("thing3")
             or match.group("thing4") or match.group("thing5") or "").lower()
    if not thing:
        return None
    if not _MONEY.search(clean):
        return None
    if _NOT_YET.search(clean):
        return _pick(NOT_YET_LINES, memory)
    if thing == "bill":
        return _ask_for_what_is_missing(_pick(BILL_LINES, memory), clean, thing)
    return _ask_for_what_is_missing(_pick(LETTER_LINES, memory), clean, thing)


def _pick(lines, memory):
    """Two wordings, so a second letter ask does not repeat the first reply word for word."""
    try:
        last = str((memory.get("turns") or [{}])[-1].get("bot") or "")
    except (AttributeError, IndexError, TypeError):
        last = ""
    for line in lines:
        if line != last:
            return line
    return lines[0]
