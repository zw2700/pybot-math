"""Whether today needs a coat: the one clothes question with no garment to buy, wash or mend.

"Do I need a coat today" is a yes or no about the next few hours, and two rows in this package
say in their own comments that they leave it to somebody else: `clothing.py`'s `child-coat`
keeps "today" and "weather" out of its key because "do the kids need a coat today" is a forecast
question, and `shopping.py`'s `coat-worth` keeps "tonight", "tomorrow" and "umbrella" out for the
same reason. Nothing answered it, so those lines got a shrug ("That's your call, not mine"), a
weather note with no answer in it ("A weather app has the next few days in one tap"), or a card
about something else entirely ("is it cold enough for a coat" was answered with the washing
machine's 30C setting).

The bot cannot see a forecast. What a friend says is the rule: take it, because being cold or
wet for an hour costs more than carrying a coat you never put on, and read the forecast for the
hours you will actually be out rather than the day's high.

The row lives in its own domain rather than in `clothing.py` because the garment words are shared
with the buying card, the washing card and a coat of paint, and the guard below is what keeps
them apart - a rule about the next few hours, not a fact about a coat.
"""
import re

from .lookup import entry

# The topics this domain answers, as the ids in bot/understanding/topics.py.
ANSWERS = ("home-and-diy", "shopping", "nature-and-weather")

# The day the line is about. A coat question with no day in it ("do i need a jacket", "what coat
# should i get for winter") is a buying question and belongs to `shopping.py`'s `coat-worth`.
OUT_WHEN = ("today", "tonight", "tomorrow", "this morning", "this afternoon", "this evening",
            "in the morning", "in the afternoon", "in the evening", "right now", "later",
            "later on", "out", "outside", "weather", "forecast", "cold out", "chilly out",
            "warm out", "raining", "rain today", "enough", "the weekend",
            "this weekend", "saturday", "sunday", "monday", "tuesday", "wednesday", "thursday",
            "friday", "after work", "school run", "when i go out",
            # a coat to work or to school is the same question as a coat to Leeds: only the place
            # differs, and the place is where the hours out are spent. These four were in `avoid`
            # and took "should i take a coat to work today" and "does my child need a coat for
            # school today" back to the shrug (black-crab on #10612).
            "to work", "at work", "for work", "to school", "at school", "for school",
            "to the office", "at the office", "in the office",
            # a clock is a day word too: "should i bring a jacket this pm" was a shrug
            "this pm", "this am", "in the morning", "before work")

OUT_TAKE = ("Take it: being cold or wet for an hour costs you far more than carrying something "
            "you never put on, and it is the bright morning that catches people out. Read the "
            "forecast for the hours you will actually be out, because the day's high is at two "
            "in the afternoon and the cold and the showers come later; under it a thin layer you "
            "can take off is worth more than a thicker coat, and if you will be standing about "
            "after dark, that is the case for the warm one.")

# The words a line about buying, choosing or mending a garment is asked with. They are not in the
# key, because "should i take a coat to leeds tomorrow" and "what coat should i get for winter"
# share the garment and nothing else: the first is a yes or no about the next few hours and the
# second wants the price, the fabric and the fit. The reading below is what keeps them apart.
_NOT_ABOUT_TODAY = ("what coat", "what jacket", "which coat", "which jacket", "should i get",
                    "should i buy", "worth it", "is it worth", "buy", "buying", "bought", "price",
                    "cheap", "expensive", "best", "recommend", "shop", "sale", "size", "fits",
                    "fit me", "too small", "too big", "outgrew", "needs a new", "need a new",
                    "a new coat", "a new jacket", "new coat", "new jacket", "brand new",
                    "zip", "zipper", "torn", "ripped", "stain", "smell", "store", "storage",
                    "put away", "moth", "wash", "clean", "repair", "waterproof it", "reproof",
                    "leak", "paint", "second coat", "coats of", "jacket potato", "potato",
                    "antivirus", "laptop", "computer", "macbook", "city break", "weekend away",
                    "holiday", "packing", "for the trip", "winter coat", "warm coat",
                    "coat thats", "coat that is", "waterproof coat", "puffer",
                    # a coat on its way from a shop is a size question: "i ordered a coat in a
                    # medium last tuesday" was answered here on "coat" and "tuesday"
                    "ordered", "order", "medium", "small", "large", "arrived", "delivery",
                    # a coat that went on yesterday is a story, not a decision: "i wore my jumper
                    # inside out all day" was answered here on "wore" and "all day"
                    "wore", "worn", "inside out", "yesterday", "all day",
                    # "enough" is a day word here ("is it cold enough for a coat") and the same
                    # word is a question about how a coat fits: "is my coat big enough for a
                    # jumper underneath" wants a fit answer, not a forecast one. So do the words
                    # about the sleeves and the shoulders, which are the tailor's question.
                    "big enough", "long enough", "too long", "too short", "sleeves", "sleeve",
                    "shoulders", "alter", "altering", "tailor")


# The day words as whole words, because "out" is in "without" and "today" is in nothing: a
# substring test answered "can i wear a coat without a shirt" as though the person had said they
# were going out today, and handed them the take-it-today card.
_OUT_WHEN = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in
                                           sorted(OUT_WHEN, key=len, reverse=True)) + r")\b")


# What happened to a garment is not a question about taking one out. A loss or a theft has no
# decision left in it for this card to make, so a line that reports one is left to the row that
# answers it. Theft is the word on its own; a loss needs the thing it was ("losing his jumper",
# "lost my gloves"), because "should i take a coat in case i lose it" is a decision about today
# and the loss there has not happened yet.
_LOST_OR_TAKEN = re.compile(
    r"\b(?:swiped|stolen|stole|nicked|robbed|burgled|pickpocket\w*|went missing|gone missing|"
    r"is missing|are missing|left (?:it|them|mine|his|hers|my|the) (?:on|in|at)|"
    r"someone took|took my|taken my|"
    r"los(?:t|ing|es) (?:his|her|their|my|our|the|it|them))\b",
    re.IGNORECASE)


# A clock is when the hours out are, and people write it as "8pm" where a word list cannot reach
# it: "will i need a coat at 8pm" is the same question as "will i need a coat tonight", and it
# had no day word in it, so the row never stood a chance.
_A_CLOCK = re.compile(r"\b\d{1,2}\s?(?:am|pm)\b", re.IGNORECASE)


def _a_garment_to_take(understood):
    """True when the line is a yes or no about taking a garment out today.

    The garment words are shared by a buying question, a washing question and a coat of paint, so
    the reading is done here rather than in the key: what this card answers is whether the thing
    goes on today, and every other question about a coat wants a price, a fabric, a wash or a
    fault instead.
    """
    said = " ".join(str(understood.get(key) or "") for key in ("words", "clean", "text")).lower()
    for filler in "[],'":
        said = said.replace(filler, " ")
    for word in ("how do i", "how do you", "how can i", "how to") + _NOT_ABOUT_TODAY:
        if word in said:
            return False
    if _LOST_OR_TAKEN.search(said):
        return False
    # This card is about the next few hours, so the line has to say which hours: a coat question
    # with no day in it is the buying card's, and the keys of the two share the garment, which is
    # enough to reach two of this key's three parts on its own.
    return bool(_OUT_WHEN.search(said) or _A_CLOCK.search(said))


ENTRIES = [
    entry(
        "coat-out-today",
    (("coat", "coats", "jacket", "jackets", "raincoat", "brolly", "umbrella", "umbrellas",
      "warm layer", "jumper", "fleece", "cardigan", "hat", "gloves", "scarf"),
     # the ask, and then the day it is about: three parts, because a coat question with no time in
     # it is the buying card's ("what coat should i get for winter") and this card cannot tell a
     # coat from a coat of paint on the garment word alone.
     ("need", "take", "bring", "pack", "wear", "wearing", "put on", "should i", "do i", "will i",
      "shall i", "bother"),
     OUT_WHEN),
    OUT_TAKE,
    guard=_a_garment_to_take,
    # the coat to wash and a walk in the rain are other cards, and each names the thing it is
    # really about. A child is not one of them: `child-coat` keeps "today" and "weather" out of
    # its own key on purpose, because "do the kids need a coat today" is this row's question, so
    # a child's line with a today in it lands here.
    avoid=("pram", "pushchair", "car seat", "travel system",
           "hiking", "hike", "hill", "hills", "walking", "walk", "cycling", "running",
           "football", "rugby", "match", "camping", "festival", "wedding", "funeral",
           "interview", "uniform", "suit",
           # a garment somebody else took is a report, not a decision about the next few hours:
           # "someone swiped my keys out my coat pocket" met the garment and "out" and was told
           # to take a coat (snappy-shark on #10612). The loss and theft words are read by
           # `_LOST_OR_TAKEN` in the guard, which is a rule rather than a word list in here.
           ),
    # "is it cold enough for a coat" meets the key on the garment and the day, and the washing
    # card reached it on "cold" and "enough" too, so the row carries bias to be reached at all.
    bias=2),
]
