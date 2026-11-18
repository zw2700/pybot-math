"""A body ending said at a bill is a figure of speech, and the bill is the question.

Thirteen lines typed on `6f5447f3b`, and every one of them got an answer about the wrong subject:

    i nearly died when i saw the bill           -> the bereavement team card: "say the account
                                                   holder has died and they close the account"
    i nearly fell over when i saw the bill      -> the falls review
    i nearly had a heart attack at the bill      -> the dizzy-spell card
    my heart stopped when i saw the bill        -> "That's something only they can see"
    i couldnt breathe when i saw the bill      -> "Got it. Is there anything you'd like a hand with?"
    i opened the statement and nearly cried     -> "How did that go, overall?"
    i read the invoice and nearly died         -> "Annoying. Is it every time, or only now and then?"
    i saw the bill                              -> "Nice one. How did the rest of it go?"
    i opened the bill                           -> "Good to hear. What was the best bit?"

The knowledge base has no card for "a bill shocked me", so each of those lines reached whichever
card owned the *ending* - a death, a fall, a faint, a choking - or a greeting pool that cheered at
it. The person is asking about the bill.

So the module answers one subject and nothing else: a body ending and a **bill, statement or
invoice** said of each other. Three orders count, and each has its own reason:

* the ending, then the page - "i nearly died when i saw the bill". The page has to come after the
  ending, so `i nearly died` on its own stays with loss and grief, and `the bill nearly killed me`
  stays with the cards below.
* the page, then the ending - "i read the invoice and nearly died", "the bill took my breath away".
  A page verb has to sit in front of the document, so `i paid the bill and nearly died on the
  motorway` is left to the safety module: there the person was not reading.
* the page in hand and nothing else - "i saw the bill", "i opened the bill". A line that is only
  somebody holding a bill is asking about the bill.

A bill that has not come is answered for what it is (confirm the address, note the date and who
you spoke to, and what to look for when it lands); a bill that came with a figure is not asked
"how much?" back. The answer is the page-check a friend gives: what it says you are charged for,
the dates it covers, the reference, ask for the breakdown in writing, keep a copy. A card that
knows the bill itself keeps its turn, and the module stands down for it: when the line names a kind
of bill (council tax, energy, water, gas) and the knowledge base's own reply names that kind in its
opening sentence, the card read the bill - the band and the discounts, the tariff and the standing
charge - and the general page-check is the lesser answer.
"""
import re


# Above the knowledge base and below every module that reads a real event: this is a reading of
# what the line is about, not a new subject of its own.
PRIORITY = 1000

# The body ending: the figure of speech, in the words people type it in.
A_BODY_ENDING = re.compile(
    r"\b(?:nearly|almost|bloody\s+near|like\s+to\s+have)\s+"
    r"(?:died|fell\s+over|fainted|passed\s+out|choked|keeled\s+over|collapsed)\b"
    r"|\b(?:had|having)\s+a\s+heart\s+attack\b|\bmy\s+heart\s+(?:stopped|sank)\b"
    r"|\bcould(?:n'?t| not)\s+(?:breathe|get\s+my\s+breath|catch\s+my\s+breath)\b"
    r"|\bmy\s+(?:jaw|eyes|heart)\s+(?:dropped|fell|nearly\s+dropped)\b"
    r"|\b(?:was|were)\s+(?:gasping|choking)\b|\bchoked\b|\bgasped\b"
    r"|\bnearly\s+(?:cried|wept)\b"
    r"|\bwent\s+(?:white|pale)\b|\bmy\s+knees\s+(?:went|gave)\b", re.I)
# A shock at a *page* is not a body event at all, so there the document can come first: "the bill
# took my breath away", "my jaw dropped when the statement came". These are said of a bill and
# almost never of anything else in a line that also names one.
A_SHOCK_AT_A_PAGE = re.compile(
    r"\btook\s+my\s+breath\s+away\b|\bmy\s+(?:jaw|heart)\s+(?:dropped|fell|sank)\b"
    r"|\bwent\s+(?:white|pale)\b|\bmy\s+knees\s+(?:went|gave)\b", re.I)
# The document, and only the three things this module has an answer for. "The price" is left out
# on purpose: a price on a shelf is a shopping question, and a figure in the air has no page.
A_DOCUMENT = re.compile(
    r"\b(?:bill|bills|statement|statements|invoice|invoices|invoiced)\b", re.I)
# The same page, unread: a bill that has not come is not one to check.
_NOT_YET = re.compile(
    r"\b(?:hasn'?t|hasnt|haven'?t|havent|hadn'?t|hadnt|didn'?t|didnt|never|no)\b"
    r"[^.!?]{0,30}\b(?:arrived|come|came|turned\s+up|showed\s+up)\b"
    r"|\bno\s+(?:bill|statement|invoice)\s+(?:yet|at\s+all)\b"
    r"|\b(?:not|never)\s+(?:had|received|got)\s+(?:it|a\s+(?:bill|statement|invoice))\s+yet\b"
    r"|\bstill\s+waiting\b", re.I)


# The page itself in somebody's hand: the verbs that mean they are looking at it, and the shape
# of a line that is only that ("i opened the bill", "just got the statement", "i saw the invoice
# today"). Read on its own because a person holding a bill is asking about the bill.
A_PAGE_VERB = re.compile(
    r"\b(?:saw|seen|opening|opened|read|reading|looked\s+at|looking\s+at|looked\s+through|"
    r"checked|checking|got|get|received|receiving|landed|arrived|through\s+the\s+door)\b", re.I)
_ONLY_THE_PAGE = re.compile(
    r"^(?:i|we)?\s*(?:have\s+|had\s+|just\s+|only\s+just\s+|finally\s+|today\s+|"
    r"this\s+morning\s+|yesterday\s+)*"
    r"(?:saw|seen|opened|opening|read|reading|got|get|received|checked|looked\s+at)\s+"
    r"(?:the|my|this|our|that|a)\s+"
    r"(?:bill|bills|statement|statements|invoice|invoices)\b"
    r"(?:\s+(?:today|yesterday|this\s+morning|last\s+night|again|now))?[.!]*$", re.I)


def _a_complaint_added_after_the_ending(text):
    """True when a real complaint is said after the figure of speech, which is the answer needed.

    "i nearly died when i saw the bill" is about the bill, but "i nearly fainted when i saw the bill
    and now i feel sick" and "... and my knee hurts" have two subjects, and the person's own body
    is the one to answer: those lines belong to the faint card and the sore-knee card. The words
    are the shared symptom list the composer already keeps (`bot/compose/fallback_data.py`), read
    only after the ending, so the ending's own words ("my heart sank", "couldnt breathe") are not
    the complaint.
    """
    line = " ".join((text or "").lower().split())
    said = A_BODY_ENDING.search(line)
    if not said:
        return False
    tail = line[said.end():]
    after = set(re.findall(r"[a-z']+", tail))
    if after & (_A_SYMPTOM | _ALSO_A_COMPLAINT):
        return True
    if _A_WENT_OUT_COLD.search(tail):
        return True
    # A body word the shared list does not hold, with the state it is in beside it: "my chest is
    # still tight" is a symptom still going on, not noise after an idiom, and no list of symptoms
    # was going to hold every way a body is described. The state word is what makes it a state.
    return bool(after & _A_BODY_WORD) and bool(_A_STATE_OF_A_BODY.search(tail))


# A complaint the shared list does not hold yet, all of them things said after a shock about the
# body rather than about the page: "and my arm went numb", "and i went all weak".
_ALSO_A_COMPLAINT = frozenset((
    "numb", "numbness", "weak", "weakness", "shaky", "shaking", "lightheaded", "sweating",
    "faint", "fainting", "dizzy", "dizziness", "breathless", "breathlessness",
))

# Something the body did, which is a symptom whether or not it is in a list of parts: "and i
# blacked out", "and i passed out after it".
_A_WENT_OUT_COLD = re.compile(r"\b(?:blacked out|blackout|blacked|passed out|out cold|unconscious|"
                              r"keeled over|collapsed|fainted|fainting fits?)\b")
# How a body is when it is not right, next to a part in `_A_BODY_WORD`: "still tight", "gone
# numb", "hurts", "pounding". Read only in the tail, so a bill for a knee operation is still a bill.
_A_STATE_OF_A_BODY = re.compile(
    r"\b(?:hurt|hurts|hurting|sore|soreness|tight|tightness|numb|numbness|ache|aches|aching|throb|"
    r"throbbing|swollen|swelling|bleeding|stiff|stiffness|weak|weakness|shaky|shaking|still|worse|"
    r"pounding|squeezing|burning|itchy|itching|watering|gone|goes|went)\b")

try:
    from ..compose.fallback_data import BODY_PARTS as _A_BODY_WORD  # noqa: PLC0415
    from ..compose.fallback_data import SYMPTOM_WORDS as _A_SYMPTOM  # noqa: PLC0415
except Exception:  # noqa: BLE001 - the composer moves; the fence then rests on its own words
    _A_BODY_WORD = frozenset((
        "arm", "back", "chest", "ear", "eye", "eyes", "foot", "hand", "head", "hip", "jaw",
        "knee", "leg", "neck", "shoulder", "skin", "stomach", "teeth", "throat", "toe", "wrist",
    ))
    _A_SYMPTOM = frozenset((
        "ache", "aches", "bleed", "bleeding", "bruise", "confused", "cough", "dizzy", "fever",
        "headache", "hurt", "hurting", "hurts", "nausea", "nauseous", "pain", "painful", "rash",
        "sick", "sore", "swollen", "temperature", "tired", "vomit", "vomiting", "wheezing",
    ))


def _the_page_in_hand(line):
    """True when the line is only somebody holding or looking at a bill, statement or invoice."""
    return bool(_ONLY_THE_PAGE.match(line) and not _NOT_YET.search(line))


def _the_ending_and_the_page(text):
    """True when a body ending and a document are said of each other.

    Two orders count, and each one has its own reason:
    * the ending, then the page - "i nearly died when i saw the bill". This is the shape that
      reached a bereavement card, a falls review and a dizzy spell.
    * the page, then the ending - "i read the invoice and nearly died", "the bill took my breath
      away". A page verb has to sit in front of the document, so "i paid the bill and nearly died
      on the motorway" is left to the loss and safety modules: there the person was not reading.
    """
    line = " ".join((text or "").split())
    if not line:
        return False
    if _the_page_in_hand(line):
        return True
    # A page that has not come and a body ending in the same line is the wait for it: nobody is
    # dying of a bill they have not seen, and the line is about the page either way.
    if _NOT_YET.search(line) and A_DOCUMENT.search(line) and A_BODY_ENDING.search(line):
        return True
    page = A_SHOCK_AT_A_PAGE.search(line)
    if page:
        return bool(A_DOCUMENT.search(line))
    said = A_BODY_ENDING.search(line)
    if not said:
        return False
    after = A_DOCUMENT.search(line, said.end())
    if after:
        return True
    # the page first: a page verb, then the document, then the ending
    document = A_DOCUMENT.search(line)
    if not document:
        return False
    before = line[:document.start()]
    return bool(A_PAGE_VERB.search(before[-24:]))


# The page-check a friend gives, and the one question left over: what it is charging for and how
# much, unless the line has already said the figure.
_BILL_LINES = (
    "A bill is worth checking before you pay it: the dates it covers, what it says you are being "
    "charged for, and the reference. Ask for the breakdown in writing, and if it is wrong say so "
    "in writing before the date on it, keeping a copy. What is it for, and how much?",
    "Before paying a bill you did not expect, check the dates it covers, what it is charging for "
    "and the reference. Ask for the breakdown in writing, and answer in writing before the date "
    "on it, keeping a copy. What is it charging you for?",
)
_WITHOUT_A_FIGURE = (
    "That is worth checking before you pay it: the dates it covers, what it says you are being "
    "charged for, and the reference. Ask for the breakdown in writing, and if it is wrong say so "
    "in writing before the date on it, keeping a copy. What is the reference on it?",
    "Before you pay it, check the dates it covers, what it says you are charged for and the "
    "reference. Ask for the breakdown in writing and keep a copy of everything. Does it say what "
    "period it covers?",
)
# A bill that has not come yet is not one to check, so the same page-check is said for it: what to
# find on the page when it lands, and the one thing worth doing before it does.
_BEFORE_IT_COMES = (
    "When it comes, the three things to find are the date they want an answer by, what it says you "
    "are charged for and the reference. Ask them to confirm when it was sent and to which address, "
    "and note who you spoke to and when.",
    "While you wait, it is worth confirming they have your right address, and noting "
    "the date and the name of whoever you speak to. When it lands, the reply-by date, what it "
    "charges for and the reference are the things to check first.",
)
_A_FIGURE = re.compile(
    r"(?:\u00a3\s*\d|\b\d+(?:[.,]\d+)?\s*(?:pounds?|quid|p|per\s?cent|%)\b"
    r"|\b(?:for|of|cost(?:s|ing)?|paid|owe[sd]?|totall?ing)\s+\u00a3?\d+)", re.I)


def _pick(lines, memory):
    """Two wordings, so a second bill ask does not repeat the first reply word for word."""
    try:
        last = str(((memory or {}).get("turns") or [{}])[-1].get("bot") or "")
    except (AttributeError, IndexError, TypeError):
        last = ""
    for line in lines:
        if line != last:
            return line
    return lines[0]


# Which bills this module answers, and which belong to another card.
#
# Measured on main, one line per conversation, with an ending in front of sixteen kinds: an
# account or utility bill that gets a shock ("my energy bill is huge" is the energy card, but
# "i nearly died when i saw the energy bill" was the condolence card) has no card of its own, and
# this module's page-check is the answer. A bill for a meal, a visit or a repair does have one -
# `i nearly cried at the vet bill` is the pet insurance card, `i nearly died at the dentist bill`
# is "complain to the practice manager", `i nearly died when i saw the restaurant bill` is
# "split by what people actually had" - and the general page-check is the lesser answer there.
#
# So the word the person put in front of the document decides. A kind word that is not an account
# stands this module down, whatever the kind is, which is the rule a reviewer asked for: it holds
# for the restaurant, the dentist and the vet above and for every kind added later.
_A_ACCOUNT_WORD = frozenset("""
account annual quarterly monthly bank bill card charge council credit debit electricity electric
energy gas insurance internet loan metered metering meter mobile mortgage phone rent service
sewerage student supply tax tv utility water
""".split())

# Words in front of the document that say nothing about *which* bill it is: determiners,
# possessives, and the adjectives people put on any bill ("the huge bill", "my latest statement").
_A_WORD_ABOUT_ANY_BILL = frozenset("""
a an the my our your their his her its this that these those some any no
big small huge massive enormous enormous giant tiny little
new old latest last first second third final whole same other another next
unexpected surprise shocking ridiculous stupid bloody damn awful terrible
monthly quarterly annual weekly daily
""".split())


# A kind that *is* an account word but still has a card of its own on main: the band and the
# discounts, the reference never applied. Add a kind here when a card for it exists.
A_BILL_WITH_ITS_OWN_CARD = ("council tax",)


# The words that end the noun phrase in front of the page: everything the person says about the
# shock itself ("when i saw", "i opened", "and") and every function word. A kind word has to be
# the last word of the noun phrase before the bill - "the restaurant bill", "my vet bill".
_A_WORD_BEFORE_A_KIND = frozenset("""
i me my we us our you your he him his she her it its they them their
saw see seen seeing read reading reads open opened opening opens got get gets getting
receive received receiving arriving arrived arrive came come comes coming
paid pay paying sent send sends sending took take taken
in on at for from with about of to and but or when after before then now today
the first second last final
""".split())


# Somebody else's ending is news, not a page to check. "my mum nearly died and the funeral bill is
# 4000" is a person in a bad week, and the answer is about her: the loss card keeps the turn. The
# same for "he nearly died and now the hospital statement says 800". Read only in front of the
# ending, because the third person can come afterwards in a clause that does not change the subject
# ("i nearly died when i saw the bill and then she rang").
_A_SOMEBODY_ELSE = re.compile(
    r"\b(?:my|his|her|their|our)\s+(?:mum|mom|mammy|dad|father|mother|son|daughter|"
    r"wife|husband|partner|boyfriend|girlfriend|nan|nana|gran|granny|grandma|granddad|"
    r"grandad|grandpa|grandmother|grandfather|brother|sister|uncle|aunt|cousin|friend|"
    r"kid|kids|child|baby|boy|girl|dog|cat|neighbour|neighbor)\b"
    r"|\b(?:he|she|they|him|her|them)\b")


def _the_ending_is_somebody_elses(text):
    """True when the body ending is said of another person, whose news is the thing to answer."""
    line = " ".join((text or "").lower().split())
    said = A_BODY_ENDING.search(line)
    if not said:
        return False
    return bool(_A_SOMEBODY_ELSE.search(line[:said.start()]))


def _a_kind_word_in_front_of_the_page(text):
    """The kind word the person put in front of a bill/statement/invoice, or ""."""
    line = " ".join((text or "").lower().split())
    for document in A_DOCUMENT.finditer(line):
        before = re.findall(r"[a-z']+", line[max(0, document.start() - 40):document.start()])
        for word in reversed(before):
            if word in _A_WORD_ABOUT_ANY_BILL:
                continue
            if word in _A_WORD_BEFORE_A_KIND or word in _A_ACCOUNT_WORD:
                return ""
            return word
    return ""


def _a_bill_of_another_kind(text):
    """True when the line names a kind of bill whose own card keeps the turn."""
    low = " ".join((text or "").lower().split())
    return bool(_a_kind_word_in_front_of_the_page(text)) or any(
        kind in low for kind in A_BILL_WITH_ITS_OWN_CARD)


# The second half of a line can be a money problem of its own, and that is a money question with a
# card behind it in the knowledge base (send the two payment references and ask for the duplicate
# to be reversed; tell them what you can pay and when; say it before they have to ask). Those lines
# are the ones this module must not take: the shock is the frame and the money is the ask.
# "i nearly died at the bill and theyve charged me twice" was answered with the duplicate-charge
# line before this module existed, and the page-check is the lesser answer there.
A_MONEY_PROBLEM = re.compile(
    r"\b(?:charged\s+(?:me\s+)?twice|double\s+charged|charged\s+me\s+double|duplicate|"
    r"overcharged|over\s*charged|cant\s+pay|can'?t\s+pay|cant\s+afford|can'?t\s+afford|"
    r"cannot\s+pay|cannot\s+afford|owe|owes|owed|arrears|in\s+arrears|payment\s+plan|"
    r"instal+ments?|wrong|too\s+much|discount|rebate|refund|benefit|hardship|"
    r"meter\s+read|reading|estimated)\b", re.I)


def TAKES_AS_IT_COMES(text, memory=None):
    """This line, because the module read it whole: a body ending and a document after it.

    Without this the knowledge base answers first on most of these lines, and its card is about
    the *ending* - a bereavement team, a falls review, a dizzy spell. The claim is not a band: the
    module proposes on many lines it has no business taking (any bill at all), so it says which of
    its own proposals is this one, on the line in front of it.
    """
    if not _the_ending_and_the_page(text):
        return False
    if _a_complaint_added_after_the_ending(text):
        return False
    if _the_ending_is_somebody_elses(text):
        return False
    if _a_money_problem_in_the_line(text, memory):
        return False
    return not _a_bill_of_another_kind(text)


def _ask_for_what_is_missing(memory, text):
    """The page-check, asking for the thing the line has not already said."""
    line = " ".join((text or "").split())
    if _NOT_YET.search(line):
        return _pick(_BEFORE_IT_COMES, memory)
    said_the_figure = bool(_A_FIGURE.search(line))
    lines = _WITHOUT_A_FIGURE if said_the_figure else _BILL_LINES
    return _pick(lines, memory)


# A card about money says so in its first line: a payment plan, a duplicate charge, arrears, a
# refund, the band and the discounts. A card about the *ending* does not, which is what makes this
# the test for whether the knowledge base read the money half of the line or only the shock.
A_MONEY_IN_THE_ANSWER = re.compile(
    r"\b(?:pay|pays|paid|payment|payments|overdraft|refund|refunds|duplicate|charge|charges|"
    r"charged|owe|owes|arrears|debit|instal+ments?|bill|bills|council|band|discount|discounts|"
    r"rebate|tariff|standing\s+charge|meter|account|bank|money|rent)\b", re.I)


def _a_money_problem_in_the_line(text, memory=None):
    """True when the line names a money trouble *and* the knowledge base answers about the money.

    Both halves are needed. The line alone is not enough: "i nearly fell over when i saw the bill,
    its been overcharged" names a money trouble, and the only card behind it is the falls review
    (the knowledge base read the ending), where the page-check is the better answer. The knowledge
    base's own answer alone is not enough either: for "i nearly died when i saw the bill" it is the
    bereavement team, which is the misreading this module exists to fix.
    """
    if not A_MONEY_PROBLEM.search(" ".join(str(text or "").lower().split())):
        return False
    try:
        from . import answers as _answers  # noqa: PLC0415 - the knowledge base, read only here
        reply = _answers.respond(text, memory if isinstance(memory, dict) else {})
    except Exception:  # noqa: BLE001 - a knowledge base that cannot be read adds no stand-down
        return False
    return bool(reply) and bool(A_MONEY_IN_THE_ANSWER.search(reply))


def respond(text, memory=None):
    """The bill's answer to a line that says a shock at a bill, or None."""
    if not _the_ending_and_the_page(text):
        return None
    if _a_complaint_added_after_the_ending(text):
        return None
    if _the_ending_is_somebody_elses(text):
        return None
    if _a_money_problem_in_the_line(text, memory):
        return None
    if _a_bill_of_another_kind(text):
        return None
    try:
        return _ask_for_what_is_missing(memory or {}, text)
    except Exception:  # noqa: BLE001 - a module that cannot answer adds nothing
        return None
