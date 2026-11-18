"""A debt said flat: the rate on it, or the balance, answered with what it means.

Somebody who tells the bot about a card, a loan or a debt is handing over the number that decides
everything about their money, and the number is often the whole line:

    ive got a credit card at 24 percent
    ive got 5 grand on the card
    weve got 2000 on the visa at 20 percent

None of those is a question, so no card in the knowledge base is reached - the debt card wants the
question ("should i pay off my card or save") - and what answered them was the day pool ("Sounds
alright. Anything good in it?", "How was it, overall?") or the store's receipt ("Noted: you've got
a loan at 30 percent."). Neither is an answer: a comment on somebody's day says nothing about the
debt, and the receipt is the coldest line in the file.

What the bot does know here it can say. A rate tells you whether the balance should be cleared
before anything is saved - that is the reading the debt card makes, made on the number the person
actually gave. A balance tells you the same about the order, and asks the one thing still missing
(the rate, or whether there is more than one). Below the point where "it costs more than saving
pays" is true, the claim is not made at all: a cheap rate gets said to be cheap, and the question
that catches people out - when it runs out - is asked instead.

The module answers only the turn that says the debt. A question about it ("should i pay it off",
"what is the minimum") is a card's, and the store's follow-up turns are the store's; this returns
None for both.
"""
import re

from ..compose import pick

# Below every real answer and above the fallback band, which is where a reader that only fills a
# gap belongs: a knowledge card that answers the debt ("Pay more than the minimum: it's set at 1-3%
# of the balance") keeps its turn, and this answers the flat line that nothing else answered. A
# module below 0 is a fallback to the arbiter, which is exactly what this is.
PRIORITY = -500

# A rate: the number with the sign on it, which is the number the reply turns on.
_A_RATE = re.compile(r"\b(\d{1,2}(?:\.\d{1,2})?)\s*(?:%|per\s?cent|percent)")
# What people call a borrowing. The card brands are in it because "2000 on the visa at 20 percent"
# is a card balance and nothing else in the line says so; they are only read as a card when they
# are somebody's ("my visa", "on the mastercard") or named as one ("visa card"), since a visa is
# also a stamp in a passport and "my visa cost 200 pounds" is not a debt.
_A_BORROWING = re.compile(
    r"\b(?:credit\s+card|store\s+card|storecard|credit\s+cards|payday\s+loan|overdraft|"
    r"debt|debts|catalogue|klarna|bnpl|buy\s+now\s+pay\s+later|a\s+loan|my\s+loan|the\s+loan|"
    r"loan|loans|card|cards)\b"
    r"|\b(?:my|the|on\s+the|our|me)\s+(?:visa|mastercard|amex|american\s+express)\b"
    r"|\b(?:visa|mastercard)\s+card\b")
# A line that joins itself to the one before: a follow-up, not a statement of its own.
_A_JOINED = re.compile(r"^(?:and|but|so|also|then|plus|or|what\s+about|how\s+about|"
                       r"same|still|anyway)\b")
# A sum of money near the borrowing, read as a balance: "ive got 200 pounds on a credit card",
# "ive got a debt of 3,000", "5 grand on the card". Three digits and up, so the "2" of "2 cards"
# and an hour or a date are not balances.
_A_BALANCE = re.compile(r"£\s?\d[\d,]*|\b\d[\d,]{2,7}\s?(?:pounds|quid|grand|k\b)?"
                        r"|\b\d+\s?(?:grand|k\b)")
# A debt being dealt with is not a debt still standing there: "i paid off my credit card", "i
# cleared the overdraft", "ive got rid of the loan" are wins, and the good-news pools keep them.
_A_DEBT_DONE = re.compile(
    r"\b(?:paid\s+off|paid\s+up|paying\s+off|cleared|clearing|settled|rid\s+of|getting\s+rid|"
    r"sorted\s+out|over\s+with|done\s+with)\b"
    r"|\b(?:paid|pay|paying|settled)\b[^.?!]{0,20}\b(?:off|up)\b")
# A borrowing that must not get the "clear it first" reading: a student loan is repaid out of pay
# at a rate set by the plan, not cleared out of savings, and for most people it is the last debt to
# touch rather than the first. Saying "clear it first" over one would be a confident wrong answer,
# which is the worst thing this file could do, so it stands down and lets the card answer.
_A_NOT_THIS_DEBT = re.compile(
    r"\bstudent\s+(?:loan|loans|debt|debts|finance|loan\s+company)\b|\bplan\s+[1245]\b"
    r"|\bmaintenance\s+loan\b|\bmortgage\b|\bmortgages\b")
# A monthly payment is not a balance: "my loan payment is 240 a month" names the instalment, and
# the reading about what is on the balance would be about a figure the line never gave.
_A_PAYMENT = re.compile(r"\b\d[\d,]{1,7}\s?(?:pounds|quid|grand|k)?\s*(?:a|per|each)\s*"
                        r"(?:month|week|year|fortnight)\b")
# A borrowing named on its own, with no figure: "ive got a store card", "we have 3 credit cards".
# Only these, so the greeting card ("i got a card from my nan") and the playing card are not debts.
_A_DEBT_NAMED = re.compile(
    r"\b(?:credit\s+cards?|store\s*cards?|storecards?|overdraft|catalogue|klarna|bnpl|"
    r"pay\s?day\s+loans?|buy\s+now\s+pay\s+later|a\s+loan|my\s+loan|the\s+loan|loans|"
    r"debts?)\b|\b(?:my|the|our|on\s+the|me)\s+(?:visa|mastercard|amex|american\s+express)\b"
    r"|\b(?:visa|mastercard)\s+card\b")
# A card for somebody is a present, not a borrowing: "i spent 250 pounds on a card for my mum" and
# "i bought my mum a card and spent 200 pounds" were read as a balance, and got "It is usually the
# first thing to clear, ahead of saving". The greeting card is the figure arm of the same slip the
# no-figure arm already guarded (`_A_DEBT_NAMED`), so it is fenced by the shapes a card is bought
# in - the occasion in front of it, a person after it, or a verb of giving before it - and never by
# the word alone. "i got 2000 on a card" is a balance, so "on" in front of the article stands the
# reading down: the money went on the card, and the card was not given to anybody.
_A_GREETING_CARD = re.compile(
    r"\b(?:birthday|christmas|xmas|thank[- ]?you|sympathy|get[- ]well|anniversary|leaving"
    r"|wedding|new\s+baby|congratulations|farewell)\s+cards?\b"
    r"|\bcards?\s+(?:for|from|to)\s+(?!my\s+card|the\s+card|pay)\w+"
    r"|\b(?:bought|buy|buying|sent|send|sending|gave|give|giving|made|making|got|getting|"
    r"picked\s+up|picking\s+up)\b(?:\s+(?!on\b|off\b)\w+){0,3}\s+"
    r"(?:a|an|the|some)\s+cards?\b")

# Having one, rather than spending on it or fretting about it: "i keep spending on the card" is
# the conversation's, and its reply is the one that asks what the spending is for.
_A_HAVE = re.compile(r"\b(?:got|have|has|owe|owes|ive|weve|theyve|there'?s)\b")
_A_THINKING = re.compile(r"\b(?:spend|spending|spent|overspend|stop|again|keep|"
                         r"shouldn'?t|worried|scared|hate|stuck|struggling)\b")
# A question about the debt is the knowledge base's: the debt card answers "should i pay off my
# card or save", and a second copy of that answer here would be the bot answering a card's turn.
# Only the question that opens the line counts, since "the card is at 24 percent" says "is" in the
# middle and is the flat statement this module is for.
_A_ASK = re.compile(
    r"^(?:should|shall|can|could|would|do|does|did|is|are|was|were|what|how|which|when|where|"
    r"who|why|worth|better|best)\b")

A_DEBT_RATE = (
    "That is an expensive rate: {rate}% a year is more than most savings accounts pay, so spare "
    "money does more going off the balance than into a saver. Roughly what is on it?",
    "{rate}% is dear money, more than most savers pay you, so clearing it first beats saving "
    "alongside it. How much is left on it?",
    "At {rate}% that is costing you every month it sits there, and it is more than most savings "
    "pay, so the balance comes first. How much is on it?",
)

A_DEBT_BALANCE = (
    "A balance like that is usually the first thing to clear: it costs more than most saving "
    "pays, so spare money is better off going to it than to a saver. Can you pay more than the "
    "minimum?",
    "That is the one to aim spare money at, since borrowing costs more than a saver pays you. "
    "What is the rate on it, and is it the only one?",
    "It is usually the first thing to clear, ahead of saving: what goes on the balance saves you "
    "more than the same money earns in a saver. Is it just the one balance?",
)

# Below 8% the claim the pools above make is false, and standing down left the store's receipt
# ("Noted: you have a card at 4 percent"). A cheap rate is still a borrowing with a term on it, and
# the term is the thing that catches people out, so the honest reply is that, and the one question
# that matters.
A_DEBT_CHEAP = (
    "At {rate}% that is cheap borrowing, so it is not the one to panic about; what matters is "
    "whether the rate is fixed or runs out, because a cheap rate that jumps is where these get "
    "away from people. Do you know when it ends?",
    "{rate}% is a low rate, so it is not costing you much; the thing to check is how long it "
    "lasts and what it becomes afterwards, which the terms you were given will say. Is it fixed "
    "for a set time?",
)


# The two things that decide a card, said as knowledge rather than a nudge, then the one figure
# that would let the bot say something useful about this one.
A_DEBT_STORE = (
    "Store cards and catalogues are usually the dearest borrowing in the shop: the rate is on the "
    "statement, and it is often twice what a credit card charges. How much is on it?",
    "Catalogue and store card rates are the ones worth checking first, because they are sold at "
    "the till rather than compared. What is the rate, and how much is left on it?",
)

A_DEBT_BNPL = (
    "Buy now pay later is free until the date it is not: what catches people is the deadline "
    "passing and the fee that lands with it. When is the payment due?",
    "The thing that matters with buy now pay later is the date the interest-free bit ends, and "
    "whether the repayments come out on time. Which one is it, and when?",
)

A_DEBT_NO_FIGURE = (
    "The rate is the figure that decides what to do about a borrowing - it is on the statement or "
    "the agreement - and after that what is left on it. Do you know either?",
    "What to do about borrowing turns on two things: what it costs a year, and how much is left on "
    "it. The rate is usually the one printed on the statement. Which have you got?",
)

A_BORROWING_WORDS = re.compile(
    r"\b(?:store\s*cards?|storecards?|catalogue)\b|\b(?:bnpl|klarna|buy\s+now\s+pay\s+later)\b")


def observe(text, memory):
    """Nothing to keep: the turn is read off the line itself, every time."""
    return None


def respond(text, memory):
    """The rate or the balance said back with what it means, or None."""
    if not isinstance(text, str):
        return None
    clean = " ".join(text.lower().split())
    if not clean or "?" in clean:
        return None
    if not _A_BORROWING.search(clean):
        return None
    if _A_DEBT_DONE.search(clean):
        return None
    if _A_ASK.match(clean) and not _A_RATE.search(clean):
        return None
    # A follow-up ("and what would i save if i moved it", "what about the other card") is the
    # conversation's, and the answer to it is usually a card's: the balance-transfer rules, the
    # minimum payment. A line that opens by joining itself to the turn before is not the flat
    # statement this reads.
    if _A_JOINED.match(clean):
        return None
    if _A_NOT_THIS_DEBT.search(clean):
        return None
    # A card bought for somebody is a present: the balance reading would be about money that is
    # not there, and it is a confident wrong answer rather than a thin one.
    if _A_GREETING_CARD.search(clean):
        return None
    rate = _A_RATE.search(clean)
    if rate:
        percent = rate.group(1)
        try:
            value = float(percent)
        except ValueError:
            return None
        if value >= 8.0:
            return pick(A_DEBT_RATE, memory, clean).format(rate=percent)
        return pick(A_DEBT_CHEAP, memory, clean).format(rate=percent)
    if _A_BALANCE.search(clean):
        if _A_PAYMENT.search(clean):
            return None
        return pick(A_DEBT_BALANCE, memory, clean)
    # A borrowing named with no figure at all. The store's receipt ("Noted: you've got a store
    # card.") is the reply this replaces; what is worth saying is what decides it and the one
    # figure that is missing.
    if _A_DEBT_NAMED.search(clean) and _A_HAVE.search(clean) and not _A_THINKING.search(clean):
        kind = A_BORROWING_WORDS.search(clean)
        if kind and kind.group(0).startswith(("bnpl", "klarna", "buy")):
            return pick(A_DEBT_BNPL, memory, clean)
        if kind:
            return pick(A_DEBT_STORE, memory, clean)
        return pick(A_DEBT_NO_FIGURE, memory, clean)
    return None
