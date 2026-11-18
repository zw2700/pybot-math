"""A thing of theirs with a date on it is the holder's to answer, not a search.

"Will my parcel come before friday" and "is my library book due back" name a record the person
owns and a date only the holder can see. The fallback used to send them to a search, and the
place pools could read the parcel as "my account" and answer about a bank balance, or read the
library card as a venue and answer about opening hours. Both are the wrong subject.

So this module answers only a line that names one of those records and asks about its state or
date, and it says the two things a friend can: I cannot see it from here, and this is where it
lives. Everything else, including "how do i return my order" (a procedure) and "my order of the
words" (not a record at all), passes.
"""
import re

PRIORITY = -500  # above the fallback, below every module that knows the subject itself

# The possessive phrase. Two words may sit between "my" and the noun ("my asos parcel"), and the
# noun has to end there so "my ordering" and "my orders of the day" are not records.
_RECORD = re.compile(
    r"\b(?:my|our)\s+(?:[a-z']+\s+){0,2}"
    r"(?P<thing>parcels?|orders?|deliver(?:y|ies)|tracking|couriers?|dispatch|"
    r"library\s+cards?|library\s+books?|library\s+loans?)\b", re.I)
# "my order of the words", "my delivery of the speech": the words after the noun say which thing
# it is, not the record the person is asking about.
_QUALIFIED = re.compile(r"\s+(?:of|that|which)\b", re.I)
_ASK = re.compile(
    r"^\s*(?:so|and|but|ok|okay|also|hi|hello|morning|quick one)?\s*,?\s*"
    r"(?:will|is|are|was|were|has|have|did|does|do|can|could|when|where|what|how|any)\b", re.I)
# The same record with the state after it is the same ask: "my library book is late", "my order
# was meant to arrive yesterday", "my parcel hasnt moved in three days". The question mark is not
# what makes it theirs; the record and its state are.
_STATE_AFTER = re.compile(
    r"\b(?:(?:still|never|now|already)\s+)?"
    r"(?:is|are|was|were|has|have|had|did|does|do)(?:n't|nt)?\s+"
    r"(?:not\s+|yet\s+)?(?:[a-z]+\s+){0,2}"
    r"(?:late|overdue|due|back|out|renewed|expired|dispatched|delivered|arrived|arriving|"
    r"coming|come|came|delayed|lost|missing|stuck|held|waiting|ready|moved|on\s+its\s+way|"
    r"turned\s+up|shown\s+up|meant\s+to\s+(?:arrive|come)|"
    r"supposed\s+to\s+(?:arrive|come)|expected)\b", re.I)
# A procedure or a judgement is not the record's state, and the answer above it is not this one.
_NOT_THE_STATE = re.compile(
    r"\b(?:how\s+(?:do|can|could|should)\s+i|how\s+to|should\s+i|do\s+i\s+need|"
    r"return|refund|cancel|change|complain|worth|warranty|guarantee|recycle)\b", re.I)

# A delivery ask has to be about where it has got to, not a request to go and fetch it:
# "can you pick up my parcel from the shop" is a thing to do, and the tracker line is an answer
# to a different question.
_DELIVERY_STATE = re.compile(
    r"\b(?:arrive|arrives|arrived|arriving|come|comes|coming|came|get\s+here|be\s+here|"
    r"turn\s+up|turned\s+up|show\s+up|shown\s+up|delivered|delivery|dispatch|dispatched|"
    r"tracking|track|check|overdue|"
    r"late|delayed|lost|missing|stuck|held|waiting|ready|moved|on\s+its\s+way|expired|"
    r"where|when|before|by|due|today|tomorrow|tonight|this\s+week|next\s+week|"
    r"mon(?:day)?|tues(?:day)?|wed(?:nesday)?|thurs(?:day)?|fri(?:day)?|sat(?:urday)?|"
    r"sun(?:day)?)\b", re.I)

_LIBRARY_CARD = ("library card", "library cards")
_LIBRARY_LOAN = ("library book", "library books", "library loan", "library loans")
_DELIVERY = ("parcel", "parcels", "order", "orders", "delivery", "deliveries", "tracking",
             "courier", "couriers", "dispatch")


def _the_record(clean):
    """The person's own record the line names, or None."""
    for match in _RECORD.finditer(clean):
        if not _QUALIFIED.match(clean, match.end()):
            return " ".join(match.group("thing").lower().split())
    return None


LIBRARY_CARD_LINES = (
    "Your library account has the expiry date: sign in with the card number and PIN, or ring the "
    "branch and they can renew the card in a minute - usually free if nothing is owed on it.",
    "That lives with the library rather than anywhere I can see. The card number gets you into "
    "your account, which shows when it runs out, and the desk can renew it on the spot.",
)
LIBRARY_LOAN_LINES = (
    "Your library account has the due date: sign in with the card number and PIN to see the loans "
    "and renew them, and the desk or the number on the card can do it in a minute.",
    "That one lives in your library account rather than here. The card number shows what is out, "
    "when it is due and how many renewals are left; the branch can renew it by phone.",
)
LIBRARY_LATE_LINES = (
    "Ugh, the late ones are a pain. Renew it in your library account first: the card number and PIN "
    "do it if nothing is reserved, and that stops the clock. If it is already overdue, take it back "
    "and the desk will tell you what is owed - I can't see the fine from here.",
    "Late books happen. The account with the card number and PIN is where the renewal is, if the "
    "book is not reserved. Once it is overdue the desk has the amount and can take it back; I "
    "can't see either from here.",
)
_LATE = re.compile(r"\b(?:late|overdue)\b", re.I)
# A past state with no auxiliary: "my order never turned up", "my parcel never came".
_BARE_STATE = re.compile(
    r"\b(?:never|not)\s+(?:arrived|came|come|turned\s+up|shown\s+up|moved)\b", re.I)
_LOST = re.compile(r"\b(?:lost|stolen)\b", re.I)
LIBRARY_LOST_LINES = (
    "Tell the library as soon as you can: the desk or the number on their site can cancel the card "
    "or mark the book lost, and tell you what a replacement costs. I can't see the charge from here.",
    "That is the library's to sort, not something I can see: ring them or call at the desk with your "
    "card number, and they will cancel it or mark the book lost and say what is owed.",
)
DELIVERY_LINES = (
    "The tracking link in the confirmation email or the shop's app has the last scan, and if it "
    "has not moved for a day or two it is the shop to chase - they open the case with the courier, "
    "not you. I can't see the tracking from here.",
    "The tracking link in the order email shows where a parcel is and the day it is due, and if "
    "that day has gone the shop chases the courier for you; no window on it from this end.",
)
# A parcel that is late or stuck is a trouble as well as a record: lead with the sympathy a
# friend gives, then the tracking and the shop, rather than a cold "I can't see it" first.
DELIVERY_TROUBLE_LINES = (
    "That's a pain. The tracking link in the order email has the last scan and the day it was due; "
    "if that day has gone or it has not moved for a day or two, the shop chases the courier - they "
    "open the case, not you.",
    "Sorry - that is annoying. The order email's tracking shows where it got to; once the promised "
    "day has gone, the shop can chase the courier or refund and replace it, so ask them rather than "
    "the courier.",
)
DELIVERY_AGAIN_LINES = (
    "Again? That's a pain. The tracking in the order email has the last scan; if it has not moved "
    "for a day or two, the shop is the one to chase the courier, and they can refund or replace it.",
    "Not again - sorry. Check the tracking in the order email first, then ask the shop to chase the "
    "courier: they open the case and can refund or replace it, and the courier cannot do that for you.",
)
_TROUBLE = re.compile(r"\b(?:late|delayed|lost|missing|stuck|held|still|never|overdue)\b|"
                      r"\bhas(?:n't|nt)\b|\bnot\s+moved\b|\b(?:meant|supposed)\s+to\b", re.I)
_AGAIN = re.compile(r"\bagain\b", re.I)


def respond(text, memory):
    clean = " ".join(str(text or "").lower().split())
    if not clean or not (_ASK.search(clean) or _STATE_AFTER.search(clean)
                         or _BARE_STATE.search(clean)):
        return None
    record = _the_record(clean)
    if record is None:
        return None
    if _NOT_THE_STATE.search(clean):
        return None
    if record in _LIBRARY_CARD or record in _LIBRARY_LOAN:
        if _LOST.search(clean):
            return _pick(LIBRARY_LOST_LINES, memory)
    if record in _LIBRARY_CARD:
        return _pick(LIBRARY_CARD_LINES, memory)
    if record in _LIBRARY_LOAN:
        if _LATE.search(clean):
            return _pick(LIBRARY_LATE_LINES, memory)
        return _pick(LIBRARY_LOAN_LINES, memory)
    if record in _DELIVERY:
        # A state ask about a delivery is the tracker's: "will it come before friday", "where is
        # my parcel", "has my order arrived". A request to fetch or post it is not this answer.
        if not _DELIVERY_STATE.search(clean):
            return None
        if _TROUBLE.search(clean):
            if _AGAIN.search(clean):
                return _pick(DELIVERY_AGAIN_LINES, memory)
            return _pick(DELIVERY_TROUBLE_LINES, memory)
        return _pick(DELIVERY_LINES, memory)
    return None


def _pick(lines, memory):
    """Two wordings, so a second record ask does not repeat the first reply word for word."""
    try:
        last = str((memory.get("turns") or [{}])[-1].get("bot") or "")
    except (AttributeError, IndexError, TypeError):
        last = ""
    for line in lines:
        if line != last:
            return line
    return lines[0]
