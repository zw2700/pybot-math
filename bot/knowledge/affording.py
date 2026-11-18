"""Saying no to something you cannot afford: the invitation, not the price.

The answers lane owns this domain. Everything here is data: the row is keyed by meaning (an
invitation that costs more than the person has) and phrased the way a sensible friend would
answer, not the way the money or the event happens to be worded.

Why the row is here rather than in `money` or `family`: those two domains already hold
`gift-budget`, which keys `friend` beside `afford` because it answers what a present should
cost. Any line that says "I cannot afford it" and names a friend therefore reads as a question
about a price, and the answer a person got was "Roughly £10 to £15 covers a secret santa or a
colleague" - a figure, to somebody who has just said they cannot go. `family`'s
`friend-cant-afford-wedding` is the right card and answered weddings only. This row is the
other half of the subject in one place, so a holiday, a stag, a hen, a birthday dinner and a
share of a trip all reach the same answer, the price rows keep their own lines, and a wedding
keeps `friend-cant-afford-wedding`, which already says it well.
"""
import re

from .lookup import entry

# The topics this domain answers, as ids from bot/understanding/topics.py.
ANSWERS = ("friends-and-relationships", "money", "family-and-parenting")

# The money not being there, said the ways people type it: the apostrophe comes and goes, and
# so does the pronoun after "afford". These are the words that make the line a refusal rather
# than a question about prices.
_NO_MONEY = (
    "cant afford", "can't afford", "cannot afford", "couldnt afford", "couldn't afford",
    "cant go", "can't go", "cant come", "can't come", "too expensive for me",
    "too expensive for us", "thats too expensive", "that's too expensive",
    "expensive things", "expensive stuff", "priced out", "money is tight", "moneys tight",
    "money's tight", "no money for", "cant stretch to", "can't stretch to",
)

# The thing the money was for: an invitation and what it costs to accept one. A rent, a car, a
# bill and a present are deliberately absent - each has its own answer.
_THE_OCCASION = (
    "holiday", "holidays", "trip", "trips", "weekend away", "long weekend", "city break",
    "stag", "stag do", "stags", "hen", "hen do", "hens",
    "birthday dinner", "birthday meal", "birthday drinks", "birthday do", "birthday party",
    "dinner", "meal", "night out", "party", "parties", "bridesmaid", "best man", "godparent",
    "to come", "to go", "come along", "be there", "my share", "my half", "the share",
    "my ticket", "the ticket", "inviting me", "invited me", "invites me", "invitation",
)

# Who the line is about. An invitation names a person or is about coming; a bill is about the
# bill, and "i cant afford a holiday this year" is a question about finding a cheaper one, so
# the person (or the being-invited) has to be in the line for this row to answer at all.
_A_PERSON_OR_AN_INVITATION = re.compile(
    r"\b(?:friend|friends|mate|mates|pal|pals|mum|mam|mom|mother|dad|father|sister|brother|"
    r"sibling|cousin|colleague|workmate|family|she|he|they|her|him|them|"
    r"invit(?:e|es|ed|ing|ation|ations)|asking me|asked me|keep asking|"
    r"to come|to go|come along|be there|my share|my half)\b", re.IGNORECASE)

# A line that is planning the thing, or asking what it should cost, is a different question and
# belongs to `gift-budget`, `wedding-budget` or the travel rows.
_PLANNING = re.compile(
    r"\b(?:planning|guest list|how much should|how much do i|budget(?:ing)? for|"
    r"cheapest|cheap|save for|saving for|my own wedding|our wedding|we are getting married|"
    r"afford a holiday|afford a trip|afford a wedding)\b", re.IGNORECASE)


def _an_invitation_is_what_they_cannot_afford(understood):
    """Whether the money that is not there was for something somebody asked them to.

    True means this row may answer. A line with no "cant afford" in it is untouched, so every
    other way of saying the money is short keeps whatever row it had. A line with one has to
    name the person or the invitation, and must not be a line about planning or pricing.
    """
    reading = understood or {}
    words = " ".join(str(one) for one in (reading.get("words") or ()))
    text = str(reading.get("clean") or reading.get("text") or "") or words
    if not _A_PERSON_OR_AN_INVITATION.search(text):
        return False
    return not _PLANNING.search(text)


ENTRIES = [
    entry("an-invitation-you-cannot-afford",
          (_NO_MONEY, _THE_OCCASION),
          "Say it early, to the person who asked you, and keep it about the money rather than "
          "about them: 'I'd love to be there, and I can't do the whole thing this year.' Offer "
          "the part you can do - the meal, the one night, a smaller gift - and name a number if "
          "you have one. Don't invent a reason and don't leave it to the week before: one "
          "honest no, said kindly, is much easier to hear than a yes you cannot afford.",
          bias=2,
          guard=_an_invitation_is_what_they_cannot_afford,
          # A present has a price and a bill has a due date: both are asked about in the same
          # words ("i cant afford it"), and neither is somebody invited to something.
          avoid=("wedding", "weddings", "bride", "groom", "bridesmaid", "best man",
                 "godparent",
                 "present", "presents", "gift", "gifts", "secret santa", "christmas", "xmas",
                 "rent", "mortgage", "bill", "bills", "energy", "electric", "gas", "council tax",
                 "insurance", "car", "van", "petrol", "fuel", "childcare", "nursery",
                 "school trip", "uniform", "food", "shopping", "dental", "dentist", "glasses")),
]
