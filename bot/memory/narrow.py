"""The part of an answer that a follow-up asks for.

A follow-up often asks about the answer the bot has just given: after "How do I roast a
chicken?", "what temperature should the oven be?" wants the oven temperature, not the whole
method again. STYLE.md says never answer the same way twice in a row, and the full answer is
already on screen, so this returns the sentence, clause or number that answers the property
asked for ("190C (170C fan).", "40 to 45 minutes.", "20 minutes per 500g.").

It is deliberately conservative. It only acts when the line asks for a property it knows how
to find (time, heat, amount, money, distance, order), and it returns None rather than guess:
a sentence with several different times is handed back whole unless the question or the
sentence says which one is meant. The caller decides whether the entry is the right one; this
module only reads the answer.
"""
import re

# A time question that names a place ("in the oven", "in the pan") must be answered by a
# sentence that mentions that place or the cooking done there. Otherwise a softening time
# ("leave it out for 15 minutes") becomes the oven time.
PLACE = re.compile(r"\b(?:oven|hob|pan|grill|fridge|freezer|microwave|slow cooker"
                   r"|barbecue|barbie|air fryer|steamer|skillet|airing cupboard|kettle"
                   r"|pot|saucepan|dish|tray|tin)\b", re.I)
COOKS = re.compile(r"\b(?:bake|baking|roast|roasting|boil|boiling|fry|frying|grill|grilling"
                   r"|simmer|simmering|steam|steaming|cook|cooking|reheat|reheating"
                   r"|warm|warming)\b", re.I)

# An answer with an urgent warning stays whole. Trimming it can drop the red flag the
# person needs ("cannot swallow fluids", "stiff neck") and leave only a mild criterion.
URGENT = re.compile(r"\b(?:999|111|a&e|a and e|emergency|urgent|chest pain"
                    r"|can(?:no|'|’)t breathe|cannot breathe|difficulty breathing"
                    r"|stiff neck|can(?:no|'|’)t swallow|cannot swallow"
                    r"|unconscious|not breathing|suicid\w*|overdos\w*|self[- ]harm"
                    r"|see (?:a|your|the) (?:gp|doctor|physio|nurse|dentist|midwife|pharmacist))\b",
                    re.I)

# What the line asks for. Money is checked before amount, because "how much does it cost"
# contains "how much" but wants the price.
ASKS = (
    ("money", re.compile(r"\bhow much (?:does|do|is|are|will|would|should|can|could)\b"
                         r".*\b(?:cost|costs|pay|price|spend|budget|charge|charges"
                         r"|fee|fees|quote|rate|rates)\b"
                         r"|\bwhat(?:'s| is) the price\b|\bhow much for\b")),
    # A yes/no question about the price is a question about the money. "is that expensive" after
    # "my car failed its mot on a tyre" names no unit and asks for no figure, so it was read as a
    # plain question about the thing and the fail sheet came back again - while "how much will
    # that cost" straight after the same line reached the fee. The price is the part being asked
    # for, and it is asked for in the same words people use for anything else ("is it pricey",
    # "will that be expensive").
    ("money", re.compile(
        r"\b(?:is|are|was|were|will|would|does|do|did|should)\s+"
        r"(?:that|this|it|they|those|these|the\s+[a-z]+|a\s+[a-z]+|an\s+[a-z]+)"
        r"(?:\s+(?:be|going to be))?(?:\s+[a-z]+){0,3}\s+"
        r"(?:expensive|pricey|costly|cheap)\b"
        r"|\bhow much (?:is|was|are|were)\s+(?:that|this|it|those|these)\b")),
    ("pressure", re.compile(r"\bwhat pressure\b|\bhow much pressure\b"
                           r"|\bwhat should the pressure\b")),
    ("distance", re.compile(r"\bhow far\b|\bhow many (?:miles|km|kilometres|kilometers)\b")),
    # A time of day is not a length of time: "what time should she go to bed" was read as
    # asking for a duration and answered with "two or three weeks" from the sentence it landed
    # in. The clock comes first so it is asked for by its own shape.
    ("clock", re.compile(r"\bwhat time\b|\bat what time\b|\bwhat(?:'s| is) the time\b")),
    ("time", re.compile(r"\bhow long\b|\bhow many (?:minutes|mins|hours|hrs|days|weeks)\b"
                        r"|\bhow much time\b")),
    # "temp" and "degrees" are the words people type for it: "what temp" after a sponge was read
    # as asking for no part of the answer at all, so the next entry that knew the word answered and
    # a cake question got a person's body temperature.
    ("heat", re.compile(r"\b(?:what|which) (?:temperature|temp|temps|degrees)\b|"
                        r"\bhow (?:hot|warm)\b|\bwhat heat\b"
                        r"|\bwhat gas mark\b|\bhow (?:high|low) (?:a )?(?:heat|temperature)\b")),
    ("amount", re.compile(r"\bhow much\b|\bhow many\b|\bhow (?:big|large)\b|\bwhat size\b")),
    ("order", re.compile(r"\bbefore (?:or|and) after\b|\bwhich (?:first|way round)\b"
                         r"|\bin what order\b|\b(?:the day before|ahead of time|in advance)\b")),
    # "what could be causing it?" after a symptom or a fault asks for the reason, not a figure.
    # It is read as a sentence of the answer, and the sentence has to say a cause.
    ("cause", re.compile(r"\bwhy\b"
                         r"|\bwhat(?:'s| is| was| could be| might be| else could be)?\s+"
                         r"(?:causing|caused|causes?|cause|behind)\b"
                         r"|\bwhat(?:'s| is) the reason\b|\breason (?:for|behind)\b")),
    # "What can i take for it" after a symptom asks for the part of the answer that says what to
    # take or do, the way "why" asks for the part that says the cause. It has to point back at
    # something already said ("for it", "for that"), so that "anything i can take" on its own,
    # "what can i take for a picnic" and "what can i take instead of the train" stay somebody
    # else's line.
    ("remedy", re.compile(
        r"\bwhat (?:can|could|should|do) i (?:take|use)\b[^?]{0,30}\b(?:it|that|this)\b"
        r"|\banything (?:i can|to) take for (?:it|that|this)\b"
        r"|\bhow (?:do|can) i (?:treat|soothe|ease) (?:it|this|that)\b"
        r"|\bwhat (?:eases|soothes|helps with) (?:it|this|that)\b"
        # The same ask with nothing pointing back at the answer: "what can i take" after a
        # symptom is about the thing on the table, and the line names nothing of its own. It is
        # read only when the answer in hand is a symptom answer (see `_the_remedy_in`), so a line
        # that names a subject of its own ("what can i take for a picnic", "what can i take to
        # spain") is left to whoever reads the subject, and only the bare ask is this kind.
        r"|^\s*(?:and\s+|so\s+|ok\s+|okay\s+|but\s+|well\s+|right\s+)*"
        r"(?:is\s+there\s+(?:anything|something)"
        r"|anything"
        r"|(?:what|which)\s+(?:can|could|should|shall|do|would)\s+i)"
        r"(?:\s+i)?\s*(?:can\s+|could\s+|should\s+|shall\s+)?(?:take|use)\b"
        r"(?:\s+(?:for|of)\s+(?:it|that|this|them|those|the pain|the ache))?"
        r"(?:\s+(?:instead|now|then|please|again))?\W*$")),
    # A history or science answer carries its dates in the sentences, so "when did they leave"
    # is answered by the sentence with the year in it, not by the whole paragraph again.
    # "when could they actually vote" is a date ask like "when did they vote": the modal is how a
    # follow-up asks it ("and when could they actually vote"), and without it the answers module
    # found nothing to narrow to and the bot said "that is everything I have on that one" over a
    # card that holds 1918 and 1928.
    ("date", re.compile(r"\bwhen (?:was|were|did|does|do|is|are|had|could|can|might)\b"
                        r"|\bwhen exactly\b"
                        r"|\bwhat (?:year|date)\b|\bwhich year\b|\bhow long ago\b")),
)

# A question about whether the food is ready is answered by the test, not by a time.
DONENESS = re.compile(r"\b(?:done|ready|cooked|baked|finished|ready to eat|is it ready)\b")

# A line that asks for the date itself, rather than for the time something takes: "what year"
# and "what date" and "how long ago" want the year, and the duration in the answer is not it.
ASKS_THE_DATE_ITSELF = re.compile(r"\b(?:what|which)\s+(?:year|date)\b|\bhow long ago\b")
# A length a line can name on its own: "for a week", "since monday", "about three days".
A_LENGTH = re.compile(
    r"\b(?P<lead>for|since|about|nearly|almost|over|going on|the last|the past|these last|the "
    r"best part of)\s+(?:(?P<amount>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|a couple of|couple of|a few|few|several|a good)\s+)?"
    r"(?P<unit>hours?|days?|weeks?|months?|years?|nights?|fortnight|weekends?|monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday|christmas|yesterday)\b",
    re.I)

# What the rest of the line can be made of and still be only a length. Anything else is a line
# saying something new about the thing ("its been like that for a week and now the freezer is
# warm"), and that line has its own answer.
LENGTH_FILLER = frozenset("""
    its it's it has is been being bin like that this the same way here still yeah yep yes well
    honestly god ugh urgh so and but no not much pretty just only nothing change changed
    different doing happening going on now we we've were i im ive i've of a an half
    for since about nearly almost over going the last past these best part a an couple few
    several good
    """.split())

# Weekdays and the one other day that is a name keep their capital: "since monday".
LENGTH_NAMED_DAYS = frozenset((
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "christmas"))


def only_a_length(text):
    """Whether the line says nothing but how long the thing has been going.

    "its been like that for a week" after an answer is the person telling that answer how long
    it has had, and it is not a new ask: the episode it belongs to is the answer, and the reply
    that fits is the question a length asks. Read here rather than in one module, because both
    the store's own reply and the knowledge base's repeat handling need the same reading, and
    neither may answer such a line twice.
    """
    if not isinstance(text, str) or "?" in text:
        return False
    found = A_LENGTH.search(text)
    if not found:
        return False
    rest = (text[:found.start()] + " " + text[found.end():]).replace(",", " ").split()
    if len(rest) > 6:
        return False
    return all(word.lower() in LENGTH_FILLER for word in rest)

# "one minute less than the packet says" is a relative instruction, not the cooking time:
# the figure it modifies is the packet's, which the answer does not state.
NOT_RELATIVE = r"(?!\s+(?:less|more|earlier|later|longer|shorter)\b)"
# A length is often said with a word between the figure and the unit: "about three full days",
# "3 whole weeks", "two solid hours". A relative word ("one minute more") is still not a span,
# which is what NOT_RELATIVE below says. Read only with the unit right after the figure, a
# reader missed the answer's own span and took the next one it found ("three full days in
# Lisbon ... keep one day free" answered "how many days" with "One day.").
SPAN_FILLER = r"\s+(?:(?:full|whole|solid|clear)\s+)?"

# A time of day: "7pm", "7.30", "19:30", "half past seven" is not one of them yet, and a
# duration ("two or three weeks") never is.
CLOCK = re.compile(r"\b\d{1,2}\s*(?::\s*\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)?|\s*(?:am|pm|a\.m\.|p\.m\.))"
                   r"|\b\d{1,2}\.\d{2}\b|\b(?:midday|midnight|noon)\b", re.I)

# A sentence that gives a reason: "usually a strain", "because it is hot", or the colon that
# opens a list of causes ("Most constant tiredness is dull rather than medical: too little sleep").
# It is deliberately not every colon: a recipe's "For the sauce:" is a step, not a cause.
CAUSE = re.compile(r"\b(?:because|since|due to|caused by|causes?|causing|usually"
                   r"|commonly|linked to|comes from)\b"
                   r"|\b(?:is|are|was|were)\b[^.!?]*:|,\s*so\b", re.I)

# A sentence that says what to take or do about a symptom: "Paracetamol or ibuprofen, plenty to
# drink, honey in warm water and a salt-water gargle all ease it". A body answer usually has one
# sentence for why it happens ("usually dry air ... leave a window open") and another for the
# remedy, so an answer worth handing back to "what can i take for it" is the one that names a
# remedy. The words are the ones people use for self-care at home; a word like "rest" or "ice" is
# left out because it is in half the answers that have nothing to do with a remedy.
REMEDY = re.compile(
    r"\b(?:paracetamol|ibuprofen|aspirin|painkillers?|pain-relief|antihistamines?|antacids?"
    r"|lozenges?|gargle|gargles|honey|lemon|salt[- ]water|steam|plasters?|antiseptic"
    r"|rehydration|over[- ]the[- ]counter|pharmac(?:y|ist)|plenty to drink|drink plenty"
    r"|\bdrops?\b"
    r"|drink water|anti-inflammator[^ ]*)\b",
    re.I)


# A word in the answer that says it is about a body: without one, a remedy word in a recipe or
# a travel answer ("a squeeze of lemon", "the pharmacy over there") would answer a bare "what can
# i take" with a cooking line. The two together are what make the answer a symptom answer.
SYMPTOM = re.compile(
    r"\b(?:pain|ache|aches|aching|achy|sore|hurt|hurts|hurting|ill|sick|unwell|symptom|symptoms"
    r"|cold|flu|cough|coughs|coughing|throat|headache|migraine|temperature|fever|nausea"
    r"|rash|rashy|itch|itches|itching|swelling|swollen|nose|ear|earache|earwax|eye|eyes|stomach"
    r"|tummy|constipat\w*|diarrhoea|hayfever|hay fever|allerg\w*|sprain\w*|strain\w*|cramp|cramps"
    r"|burn|burns|burnt|blister\w*|tooth|toothache|gum|gums|verruca|hearing)\b",
    re.I)

# Where the clause that says what to take begins: at a comma, a semicolon or a colon, because
# that is where an answer says one more thing about the sentence it is in.
REMEDY_CUT = re.compile(r"\s*[,;:]\s*")
# The words that tie a clause to the one before it, taken off the front so the clause can open a
# sentence of its own: "and take paracetamol or ibuprofen if you can" -> "Take paracetamol ...".
REMEDY_JOINER = re.compile(r"^(?:and|but|so|then|plus|also|or|instead)\s+", re.I)


def _the_remedy_in(said):
    """The clause of a symptom answer that says what to take, or None when there is none.

    The remedy is rarely the answer's opening. "Most back pain is muscular and settles in two to
    six weeks ... and take paracetamol or ibuprofen if you can" gives what to take at the end of
    its longest sentence, and that clause - not the paragraph it sits in - is the answer to
    "what can i take". A sentence that names a remedy in three words takes the clause after it,
    because "Paracetamol or ibuprofen" on its own says the medicine and nothing about it.
    """
    said = str(said or "")
    if not REMEDY.search(said) or not SYMPTOM.search(said):
        return None
    for sentence in [s.strip() for s in SENTENCE.split(said) if s.strip()]:
        pieces = [piece.strip() for piece in REMEDY_CUT.split(sentence) if piece.strip()]
        for at, piece in enumerate(pieces):
            if not REMEDY.search(piece):
                continue
            kept = [piece]
            while at + len(kept) < len(pieces) and len(" ".join(kept).split()) < 6:
                kept.append(pieces[at + len(kept)])
            part = tidy(REMEDY_JOINER.sub("", ", ".join(kept).strip(" ,;:")))
            if part and part.count("(") == part.count(")"):
                return part
    return None


def carries(reply, kind):
    """Whether an answer holds the part a line of this kind asks for.

    A figure is the part for money, a time or a date; a remedy is a sentence that names one, so
    it is read by its own words rather than by a number. A caller that only needs to know
    whether handing this answer back would answer the line uses this, and the answer itself is
    still given in full or under a lead-in.
    """
    if kind == "remedy":
        return bool(REMEDY.search(" ".join(str(reply or "").lower().split())))
    span = SPANS.get(str(kind or ""))
    return bool(span and span.search(str(reply or "")))


# Something in a sentence that can answer the property.
# A date, however an answer writes one: a year with its era ("410 AD"), four digits on its own
# ("1066"), a bare three-digit year ("410"), or a day of a month ("5 October", "October 5th").
# The last one is not decoration: "and when is the deadline" after the self-assessment answer was
# answered with the definition of self assessment again, because the answer's dates are days of
# months and nothing here knew that.
MONTHS_LONG = (r"(?:january|february|march|april|may|june|july|august|september|october"
               r"|november|december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec)")
# A weekday and a clock time say when as plainly as a year does, and the answer to a question
# about a date is often written with nothing else in it: "the clocks go back an hour at 2am on the
# last Sunday in October" holds no year and no day of a month, and the follow-up "and when do they
# go forward" was then left with the words "An hour." - the figure from the answer with the date
# dropped off it.
WEEKDAY_OR_CLOCK = (r"|\b(?:(?:this|next|last|coming|bank)\s+)?(?:monday|tuesday|wednesday"
                    r"|thursday|friday|saturday|sunday)\b"
                    r"|\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b")
DAY_OR_YEAR = re.compile(
    r"\b\d{1,4}\s*(?:bc|bce|ad|ce)\b"
    r"|\b(?:1[0-9]|20[0-9])\d{2}\b"
    r"|\b[1-9]\d{2}\b"
    r"|\b(?:[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?\s+(?:of\s+)?" + MONTHS_LONG + r"\b"
    r"|\b" + MONTHS_LONG + r"\s+\d{1,2}(?:st|nd|rd|th)?\b" + WEEKDAY_OR_CLOCK, re.I)

# A date that cannot be anything else: a month with a day, or a year with its era. A bare three
# or four digit number can be money ("over £150,000"), which is how the definition sentence of a
# tax answer outbid the sentence holding the deadline: both looked like dates, and the opening
# sentence came first.
DATED_STRONG = re.compile(
    r"\b\d{1,4}\s*(?:bc|bce|ad|ce)\b"
    r"|\b(?:[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?\s+(?:of\s+)?" + MONTHS_LONG + r"\b"
    r"|\b" + MONTHS_LONG + r"\s+\d{1,2}(?:st|nd|rd|th)?\b" + WEEKDAY_OR_CLOCK, re.I)


def has_a_date(sentence):
    """Whether a sentence gives a date, counting a bare number only when it is not money."""
    if DATED_STRONG.search(sentence):
        return True
    return bool(SPANS["date"].search(SPANS["money"].sub(" ", sentence)))

# A length written with a word between the figure and the unit: "two full days", "three whole
# weeks". Nothing in the time patterns allowed one, so an answer whose only length was written
# that way had no figure in it at all: after "Edinburgh wants about two full days", "how many
# days" read on past that sentence to "keep one day free in the middle" and came back "One day."
FULL_LENGTH = (r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven"
               r"|twelve|a few|a couple of|a|an)\s+(?:full|whole|entire)\s+(?:days?"
               r"|nights?|weeks?|months?|years?|hours?|minutes?)\b")

# The units a figure is written with, symbol and word both. A dose comes written either way -
# "10mg" and "10 micrograms a day" are the same figure - so both patterns below read from this
# one list, and a unit added for a new row is added once.
AMOUNT_UNIT = (r"microgrammes?|micrograms?|milligrammes?|milligrams?|millilitres?|milliliters?"
               r"|centilitres?|decilitres?|grammes?|grams?|mg|mcg|\u00b5g|g|kg|ml|l|litres?|liters?"
               r"|tbsp|tsp|tablespoons?|teaspoons?|cups?|parts?|people|slices?|tins?"
               r"|oz|lbs?|pounds?|tablets?|capsules?|drops?|puffs?|sprays?|units?|iu"
               r"|kcal|calories|pouches?|sachets?|scoops?")

SIGNALS = {
    "money": re.compile(r"£\s?\d|\b\d[\d,.]*\s*(?:pounds?|quid|euros?|dollars?)\b", re.I),
    "distance": re.compile(r"\b\d+(?:\.\d+)?\s*(?:m|km|metres?|meters?|miles?|mi)\b", re.I),
    "pressure": re.compile(r"\b\d+(?:\.\d+)?\s*(?:bar|psi)\b", re.I),
    "clock": CLOCK,
    "time": re.compile(r"\b\d+(?:\.\d+)?(?:\s*(?:-|to|–|and)\s*\d+(?:\.\d+)?)?"
                       + SPAN_FILLER +
                       r"(?:minutes?|mins?|hours?|hrs?|seconds?|secs?|days?|weeks?|months?"
                       r"|years?)\b"
                       + NOT_RELATIVE +
                       r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
                       r"|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
                       r"|thirty|forty|forty-five|fifty|sixty|seventy|eighty|ninety"
                       r"|twenty-four|thirty-six)"
                       + SPAN_FILLER +
                       r"(?:minutes?|mins?|hours?|hrs?|seconds?|secs?|days?|weeks?|months?"
                       r"|years?)\b"
                       + NOT_RELATIVE +
                       # "a minute a side", "a couple of minutes": a time written in words
                       # with no figure in it. The pancake answer gives its cooking time that
                       # way, so "how long do i cook them" found no sentence to read.
                       # "half an hour" and "two and a half hours" are the same kind of length,
                       # and so is "an hour and a half": a reader that stopped at "an hour" cut
                       # "about an hour and a half start to finish" down to "An hour." when the
                       # line asked how long the whole thing took. These three sit in front of
                       # the plain alternatives, which would otherwise match the shorter span.
                       r"|\b(?:an?|one|two|three|four|five|six|seven|eight|nine|ten|a couple of|a few)\s+"
                       r"(?:hours?|minutes?|days?|weeks?|months?|years?)\s+and\s+a\s+half\b" + NOT_RELATIVE +
                       r"|\b(?:an?|one|two|three|four|five|six|seven|eight|nine|ten|a couple of|a few)\s+"
                       r"and\s+a\s+half\s+"
                       r"(?:hours?|minutes?|days?|weeks?|months?|years?)\b" + NOT_RELATIVE +
                       # Only the short units: "half an hour" and "half a minute" are lengths
                       # in themselves, while "the beach for half a day" is one step inside a
                       # day out and answering "how long should we go for" with it is wrong.
                       r"|\bhalf\s+an?\s+(?:hour|minute|second)\b" + NOT_RELATIVE +
                       r"|\b(?:a|an|one|half an|a couple of|a few|a handful of)\s+"
                       r"(?:(?:full|whole|solid|clear)\s+)?"
                       r"(?:minute|second|hour|day|week|month|year)s?\b" + NOT_RELATIVE +
                       # A duration written as an adjective: "a 20-minute job", "a 3-day
                       # course". The hyphen is not a range here, it is how the length is
                       # spelled, and the answer to "how long" is "20 minutes".
                       r"|\b\d+(?:\.\d+)?\s*[-\u2013]\s*(?:minutes?|mins?|hours?|hrs?"
                       r"|days?|weeks?|months?|years?)\b" + NOT_RELATIVE +
                       r"|\b\d+\s*hours?\s*\d+\b" + NOT_RELATIVE +
                       r"|\b" + FULL_LENGTH + NOT_RELATIVE, re.I),
    "heat": re.compile(r"\b\d{2,3}\s*(?:°\s*)?c\b|\b\d{2,3}\s*degrees?\b|\bgas mark \d\b", re.I),
    # A dose is written with a symbol as often as with the word: "10mg" and "10 micrograms a
    # day" are the same figure, and only the symbols were listed here. An answer whose whole
    # amount was written out ("10 micrograms a day") read as an answer with no figure in it at
    # all, so the follow-up asking for that figure was told "I can't put a figure on that one,
    # sorry" over a sentence that had it. The units live in one place so the two patterns
    # cannot drift (AMOUNT_UNIT, above).
    "amount": re.compile(r"\b\d+(?:\.\d+)?\s*(?:" + AMOUNT_UNIT + r")\b", re.I),
    "order": re.compile(r"\b(?:before|after|first|last|ahead|in advance)\b", re.I),
    # A year: written with its era ("410 AD") or as four digits on its own ("1066").
    # A history answer often writes the year on its own ("the legions left in 410"), and the
    # question that follows it is still a when: a bare three or four digit number counts, while
    # the alternatives above still catch "1066" and "43 AD". A day of a month counts too: a tax
    # or a school answer gives its dates as "register by 5 October, file by 31 January", and a
    # when-follow-up with no year-shaped figure in the answer was answering the opening sentence
    # of the answer instead ("and when is the deadline" got the definition back).
    "date": DAY_OR_YEAR,
}

# The number that is the answer, when one span is enough.
SPANS = {
    "money": re.compile(r"£\s?\d[\d,]*(?:\.\d+)?(?:\s*(?:-|to|–)\s*£?\s?\d[\d,]*(?:\.\d+)?)?",
                        re.I),
    "distance": re.compile(r"\b\d+(?:\.\d+)?\s*(?:m|km|metres?|meters?|miles?|mi)\b", re.I),
    "pressure": re.compile(r"\b(?:between\s+)?\d+(?:\.\d+)?"
                           r"(?:\s*(?:-|to|and|–)\s*\d+(?:\.\d+)?)?\s*(?:bar|psi)\b", re.I),
    # "1 hour 40 minutes" is one span, unit and all: the hour-and-a-half figure was cut at
    # "1 hour 40", so a follow-up asked for the time got "1 hour 40." with its unit dropped.
    "clock": CLOCK,
    "time": re.compile(r"\b\d+\s*(?:months?|years?)\s*(?:-|to|or|and|–)\s*"
                       r"(?:\d+(?:\.\d+)?|two|three|four|five|six|seven|eight|nine|ten"
                       r"|twelve|eighteen|twenty-four)\s*(?:months?|years?)\b"
                       r"|\b\d+\s*hours?\s*(?:and\s*)?\d+\s*(?:minutes?|mins?)?\b"
                       r"|\b\d+(?:\.\d+)?(?:\s*(?:-|to|–|and)\s*\d+(?:\.\d+)?)?\s*"
                       r"(?:minutes?|mins?|hours?|hrs?|seconds?|secs?|days?|weeks?"
                       # a history answer gives its time in years, not in minutes: "how long
                       # were they here" after "the Romans held Britain for nearly 400 years"
                       r"|years?|months?|decades?|centur(?:y|ies))"
                       r"(?:\s*(?:per|a)\s*\d*\s*(?:g|kg|kilo|pound|lb))?\b"
                       + NOT_RELATIVE +
                       # A time written in words, with a range and with months and years in it:
                       # "Twenty minutes a day gets you a simple song in two or three months"
                       # names the length of the job in the only figure the sentence has, and a
                       # spelled-number branch that stopped at weeks could not see it at all.
                       # "two or three months", "a couple of weeks", "three to four weeks".
                       r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
                       r"|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
                       r"|thirty|forty|forty-five|fifty|sixty|seventy|eighty|ninety)"
                       # A range of them ("two or three months", "three to four weeks") is the
                       # length of the job said in the only figure the sentence has.
                       r"(?:\s*(?:or|to|and|-|\u2013)\s*(?:one|two|three|four|five|six|seven"
                       r"|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen"
                       r"|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty"
                       r"|seventy|eighty|ninety))?"
                       r"\s+(?:minutes?|mins?|hours?|hrs?|seconds?|secs?|days?|weeks?|months?"
                       r"|years?)\b"
                       + NOT_RELATIVE +
                       # Half of a unit is a length of its own: "an hour and a half", "two and
                       # a half hours", "half a day". Read only as far as the unit, the span was
                       # "an hour" and the answer to "how long does it take" came back as
                       # "An hour." from "about an hour and a half start to finish".
                       r"|\b(?:an?|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
                       r"(?:hours?|minutes?|days?|weeks?|months?|years?)\s+and\s+a\s+half\b"
                       + NOT_RELATIVE +
                       r"|\b(?:an?|one|two|three|four|five|six|seven|eight|nine|ten)\s+and\s+"
                       r"a\s+half\s+(?:hours?|minutes?|days?|weeks?|months?|years?)\b"
                       + NOT_RELATIVE +
                       # Only the short units: "half an hour" and "half a minute" are lengths
                       # in themselves, while "the beach for half a day" is one step inside a
                       # day out and answering "how long should we go for" with it is wrong.
                       r"|\bhalf\s+an?\s+(?:hour|minute|second)\b" + NOT_RELATIVE +
                       r"|\b(?:an|one|half an) hour\b" + NOT_RELATIVE +
                       # The number after the unit: "give it a week or two", "a month or
                       # three". No space-free reading takes it as a range otherwise.
                       r"|\b(?:a|an|one)\s+(?:second|minute|hour|day|week|month|year)\s+or\s+"
                       r"(?:two|three|four|five|six)\b" + NOT_RELATIVE +
                       # "a couple of weeks", "a few months": a length to plan around, and only
                       # in weeks or longer - "a few minutes" is a step inside a method, and
                       # reading it as the length of the job handed back the method sentence.
                       r"|\b(?:a couple of|a few)\s+(?:weeks?|months?|years?)\b" + NOT_RELATIVE +
                       # "a full week", "a whole day": the same length with the word that says
                       # all of it in the middle, which the signal above reads as a span and
                       # this table has to hand back as the answer.
                       r"|\b(?:a|an|one)\s+(?:full|whole|solid)\s+"
                       r"(?:minutes?|hours?|days?|weeks?|months?|years?)\b" + NOT_RELATIVE +
                       r"|\b\d+(?:\.\d+)?\s*[-\u2013]\s*(?:minutes?|mins?|hours?|hrs?"
                       r"|days?|weeks?|months?|years?)\b" + NOT_RELATIVE +
                       r"|\b" + FULL_LENGTH + NOT_RELATIVE, re.I),
    "heat": re.compile(r"\b\d{2,3}\s*(?:°\s*)?c\b(?:\s*\(\s*\d{2,3}\s*°?\s*c\s*fan\s*\))?"
                       r"|\bgas mark \d\b", re.I),
    "amount": re.compile(r"\b\d+(?:\.\d+)?\s*(?:" + AMOUNT_UNIT + r")\b", re.I),
    "cause": CAUSE,
    # A history answer often writes the year on its own ("the legions left in 410") and the
    # question after it is still a when, so a bare three or four digit number counts. So does a
    # day of a month, which is how a tax or school answer writes its dates.
    "date": DAY_OR_YEAR,
}

# A rate is not a total: "and how long per kilo?" must get "20 minutes per 500g", never the
# 2kg total the answer also names.
RATE = re.compile(r"\bper\b\s*(?:kilo|kg|500g|pound|lb|person|head|each|serving|litre|liter)\b"
                  r"|\ba (?:kilo|pound|person)\b|\beach\b", re.I)

# How often to do something is not how long it takes: "Twenty minutes a day gets you a simple
# song in two or three months" answers "how long does that take to learn" with the months, and
# "Twenty minutes." is a wrong answer a person would act on. A time that hangs a period on it
# ("a day", "per week", "each session") is a rate, and so is a figure that is itself the
# frequency ("5 days a week", "three times a week"): neither is a length to plan around.
FREQUENCY_AFTER = re.compile(
    r"^\s*(?:a|an|per|each|every|once\s+a|twice\s+a|\d+\s*times\s+a)\s*"
    r"(?:day|week|month|year|session|evening|morning|night|go|class|lesson|walk|run|"
    r"fortnight|hour)\b", re.I)
FREQUENCY_AFTER_TIMES = re.compile(r"^\s*times\b", re.I)
# The same rate said the other way round: the interval comes first and the figure after it. "Treat
# bare fence timber every two or three years" is how often to treat the fence, not how long
# treating it takes, and asked "how long will it take" to paint a shed the bot answered "Two or
# three years." A count in front of the unit is part of the figure itself ("every two or three
# years" reads as the figure "two or three years"), so the "every" is all there is to see before.
FREQUENCY_BEFORE = re.compile(r"\b(?:every|each|once\s+every|once\s+in)\s*$", re.I)
# "Twenty minutes at a time beats an afternoon" is how much to do in one go, not how long the
# whole job takes: handed back for "how long does it take" it was "Twenty minutes." - a rate
# for a length, the same shape as a per-day figure.
FREQUENCY_AFTER_AT_A_TIME = re.compile(r"^\s*at\s+a\s+time\b", re.I)

# The asks that want how long the whole job takes. "how long should i practise" is not one of
# them: the rate is the answer to it ("20 minutes"), so passing over the rate there would
# answer a question nobody asked.
LENGTH_OF_THE_JOB = re.compile(
    r"\bhow long (?:does|do|will|would|is|did|should) (?:it|that|this|they|these|the)\b"
    r"|\bhow long (?:until|before|till|til)\b"
    r"|\bhow much time\b", re.I)

# A sentence whose every figure is a rate has no length in it, and saying so is not the same as
# saying the answer has none: the length is usually written in the sentence after it.
class _NoLength:
    """The answer that says a rate and no length.

    It is falsey, so the ordinary `if part:` guard on a part cut out of an answer passes over it
    the way it passes over None. It used to be a bare `object()`, which is truthy, and the guards
    that only looked at the truth of the part handed it on: "how long is the flight", asked after
    a line about the trip, was answered with "<object object at 0x...>." - the sentinel read out
    to the person as the length.
    """

    def __bool__(self):
        return False

    def __repr__(self):
        return "NO_LENGTH"


NO_LENGTH = _NoLength()

# A job a person asks the length of is not measured in seconds. "a child who can balance for five
# seconds" says how long a test of balance lasts, and handed back for "how long does it take" it
# was "Five seconds." - a figure to plan around that is not the length of anything. Seconds are
# the unit of one step, one hold or one check, so a length-of-the-job ask looks past them to the
# sentence that says how long the whole thing takes.
# A countdown is the one length ask where seconds are the answer: "how long until the glue sets" is
# thirty seconds, while "how long does it take" is never a moment.
A_COUNTDOWN = re.compile(r"\bhow long (?:until|before|till|til)\b", re.I)

A_MOMENT = re.compile(r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten"
                      r"|fifteen|twenty|thirty|forty-five|sixty|a few|a couple of)"
                      r"\s*(?:seconds?|secs?)\b", re.I)

# The clause a sentence opens with when it names the rate before the length: "With 15-20 minutes
# a day, a simple tune is usually a few months", "At 20 minutes a day, you will ...".
RATE_LEAD = re.compile(r"^\s*(?:with|at|on|after|using|in)\b[^,;:]{0,60},\s*", re.I)

# A step that follows another ("then roast for 40 to 45 minutes") makes the last time the
# cooking time, not the parboil before it.
# An answer that tells the person to do something: a marker that says what comes next, or the
# verb of a job about the house somewhere in it ("leave it overnight and wipe it out", "run a hot
# service wash"). "A panic attack peaks in about ten minutes... breathe out for longer than you
# breathe in" has neither, and the honest no-interval line is only for answers that are a
# procedure - a person asking how often a panic attack comes is not asking about steps.
A_SET_OF_STEPS = re.compile(r"\b(?:then|next|after that|finally|lastly|step \d)\b"
                            r"|\b(?:wipe|rinse|boil|scrub|soak|coat|vacuum|hoover|descale"
                            r"|bleed|unblock|flush|brush|blot|vacuum|lather|scrub|polish"
                            r"|add|stir|mix|fill|leave it|leave them|run a|wash|clean)\b", re.I)


SEQUENCE = re.compile(r"\b(?:then|next|after that|finally|lastly|plus|followed by)\b", re.I)

# "how long should I rest it" is about the step after cooking, which may be a later sentence.
WAIT = re.compile(r"\b(?:rest|resting|cool|cooling|leave|leaving|sit|sitting|stand|standing"
                  r"|wait|waiting|chill|chilling|set|setting)\b", re.I)

# One sentence can give a time for each step of a job ("12 minutes on a low simmer, then 10
# minutes off the heat"). The steps are told apart by the clause each time sits in.
STEP = re.compile(r";\s*|:\s*|,\s*(?:then|and then|and)\s+|\s+(?:then|and then|and)\s+"
                  r"|\s+but\s+", re.I)

# A clause about what happens once the job is done ("then leave it for 10 minutes off the
# heat") gives a time that is not the time the job takes.
AFTER = re.compile(r"\b(?:off the heat|out of the oven|rest|resting|cool|cooling|leave|leaving"
                   r"|sit|sitting|stand|standing|wait|waiting|chill|chilling|set|setting)\b", re.I)


# The oven is the step however the person says it: "how long do i bake it" picks the oven time
# in "35 to 40 minutes in the oven, and the ragu wants 30 to 40 minutes on the hob".
OVEN = frozenset(("oven", "bake", "baked", "bakes", "baking", "roast", "roasted", "roasts",
                  "roasting"))

# Where the cooking happens. A sentence with no "then" in it can still give a time for each
# step, because each half names a different place: "35 to 40 minutes in the oven, and the ragu
# wants 30 to 40 minutes on the hob". Two different places is two steps; the same place twice, or
# none, is one figure per thing (the fridge advice for raw and cooked chicken) and must not be
# cut. `_step_time` reads this only when no joining word is there to say it.
WHERE = frozenset("""oven hob grill pan pot microwave barbecue bbq steamer fryer airfryer""".split())
# "How long before I can play a song?" asks when the result comes, and the answer is "two or
# three months", not "twenty minutes a day": a figure with a day or a week after it is how much
# to do, not how long the thing takes. Only a span in weeks, months or years can be that time,
# so the question reads past the per-day figure when the sentence has one.
BEFORE = re.compile(r"\b(?:before|until|till|til|by the time)\b", re.I)
RESULT = re.compile(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|eighteen"
                    r"|twenty-four)(?:\s*(?:-|to|or)\s*(?:\d+|one|two|three|four|five|six"
                    r"|seven|eight|nine|ten|twelve))?\s*(?:days?|weeks?|months?|years?)\b",
                    re.I)

# A shelf life is not a time the job takes. "Strain it, cool it fast and it keeps 4 days in the
# fridge or 3 months frozen" gives the keeping time, so a question about the cooling gets the
# cooling rule and never the 3 months. Read out of the keeping entry it is still the right figure
# for "how long does it keep", which is a keeping question and not a step.
# A figure written in two units is one figure: "4 years and 2 months", "1 hour and 20 minutes".
# The "and" in it is not a step, so the pieces on either side of it stay together.
BARE_UNIT = re.compile(r"^\d+(?:[.,]\d+)?\s*(?:seconds?|secs?|minutes?|mins?|hours?|hrs?"
                       r"|days?|weeks?|months?|years?)[.!]?$", re.I)

KEEPS = re.compile(r"\b(?:keeps?|keeping|kept|fridge|freezer|frozen|freeze|leftovers?|shelf life"
                   r"|stored?|storing|use by)\b", re.I)

# "how long for a hard one?" is about the hard-boiled line, not the first number in the answer.
QUALIFIER_WORDS = frozenset("hard soft runny jammy medium rare well done fan gas top bottom"
                            " thick thin large small whole skimmed semi".split())
QUALIFIER = re.compile(r"\b(?:" + "|".join(sorted(QUALIFIER_WORDS, key=len, reverse=True))
                       + r")\b", re.I)
# A clause of nothing but qualifiers and the words that join them is a condition, not an option
# named: "Too thin or runny, simmer it uncovered to reduce it" cut at the comma is "Too thin or
# runny", which reads as a verdict on its own but tells the person nothing to do.
QUALIFIER_FILLER = frozenset("a an the and or but so too very quite not no more less most"
                             " it its it's this that these those".split())

SENTENCE = re.compile(r"(?<=[.!?])\s+")
# A range is one piece. "Top the pressure up to between 1 and 1.5 bar" was cut at its " and " and
# handed back as "Top the pressure up to between 1.", which is half an instruction and reads as a
# typo: the number the answer is about was in the half that was dropped. A number joined to
# another by " and " (with the "between" that opens the range) is put back together before the
# pieces are cut, and a range with a dash in it never splits because there is no " and " in it.
NUM_RANGE = re.compile(r"\b(?:between\s+)?-?\d+(?:\.\d+)?\s+and\s+-?\d+(?:\.\d+)?", re.I)
RANGE_JOIN = "\x00"
# A thousands separator is not a place a clause can end. "You can pay in up to 20,000 pounds a
# year" cut at its comma hand back "000 pounds a year" - a broken number and half a sentence,
# handed to the person as the whole reply. Every money answer with a figure written the way a
# bank writes it can be cut there, so the comma inside a number is held like a range is.
THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?:\D|$))")
# The sentinel is not `\x01`: `narrow.HELD` holds an aside behind `\x01<number>\x01`, and
# the two markers were the same character - so every answer with a bracket or a dash aside
# had its aside turned into a comma by the replace below, and a step cut out of one was
# handed to the person as "... out of the back ,0, level the feet".
THOUSANDS_JOIN = "\x02"


def pieces_of(text, pattern):
    """`text` cut into pieces on `pattern`, with a numeric range and a thousands comma kept whole."""
    guarded = NUM_RANGE.sub(lambda found: found.group(0).replace(" and ", RANGE_JOIN),
                            str(text or ""))
    guarded = THOUSANDS.sub(THOUSANDS_JOIN, guarded)
    return [piece.replace(RANGE_JOIN, " and ").replace(THOUSANDS_JOIN, ",")
            for piece in re.split(pattern, guarded)]

WORD = re.compile(r"[a-z0-9']+")

# Words too common to say what a clause is about. Nothing that is meant as a note goes inside
# this string: every word of it becomes a word narrow() will not look for.
# "How long will that take?" asks about the answer, it does not name a thing in it - left in,
# "take" matched the sentence that says "take the handle off" and the length of time in the next
# one was never reached, so the follow-up got the whole paragraph again.
EMPTY = frozenset("""
a an the and or but if then than that this these those it its is are was were be been being
am do does did doing done have has had having i me my mine you your yours we us our they them
their he she his her one ones so too very just also as at by for from in into of off on onto
to up with about after before again any can could should would will shall may might must not
no yes ok okay please thanks thank there here what which who whom whose when where why how
much many long need needs needed want wants like get gets got make makes made use uses used
good best better still only even more most less few all some same other own now
# "around" and its family say a figure is approximate, not what a clause is about. Left in,
# "and how do i get around" was one content word, and the sentence it named in the answer before
# it was the one that happens to write "around twelve to fifteen euros" - so a question about
# the trams was answered with the cheap-meal card.
around roughly approximately
take takes took taken
""".split())

# Words that mean the same thing when a question asks about a property of the answer: someone
# asking how to get potatoes crisp is asking about the sentence that says they go crunchy.
SAME = {}


def _same(words):
    group = frozenset(str(words).split())
    for word in group:
        SAME[word] = group


_same("crisp crispy crunchy crackling")
_same("soft tender mushy soggy")
_same("juicy moist")
_same("hot warm")
_same("cold chilled cool")
_same("quick fast quickest speedy faster")
_same("cheap cheaper cheapest budget affordable saving")
_same("expensive pricey costly")
_same("big large huge bigger")
_same("small little tiny smaller")
_same("leave left leaving leaves")

# An elliptical ask about one option: "and for a hard boiled one?" names the option but not
# the property, so the option's clause in the answer says what is wanted.
OPTION = re.compile(r"^\s*(?:and|what about|for)\b", re.I)
NOT_OPTION = re.compile(r"\b(?:is|are|was|were|do|does|did|will|would|can|could|should|shall"
                        r"|have|has|had|change|changes|take|takes|need|needs|use|uses)\b", re.I)

# A follow-up that names something the answer mentions ("and if I use a loaf tin?") is asking
# about that thing, not about the answer as a whole: the answer says the loaf tin needs longer,
# so the sponge's time is the wrong figure and the loaf tin's is the right one.
FOLLOW_UP = re.compile(r"^\s*(?:and|also|plus|what about|how about|what if|if|then|does that"
                       r"|would that|will that|does it|is that)\b")

# The unit a bare range needs when it stands on its own: "45 to 55" is "45 to 55 minutes"
# because the sentence before it said minutes.
UNIT = re.compile(r"\b(?:minutes?|mins?|hours?|hrs?|seconds?|days?|weeks?|degrees?|g|kg|ml"
                  r"|litres?|liters?|tbsp|tsp|cups?|bar|psi|miles?|metres?|meters?)\b", re.I)
# Words a follow-up uses about the answer rather than about a thing in it.
NAMING_IGNORE = frozenset("""
use using used instead recipe version way time times take takes taking need needs
put putting cook cooking make making do doing think reckon okay ok actually really
also still there then already right again another one ones bit lot kind sort thing things
worth good best better worse fine matter matters any much should shall must
safe saf unsafe unsaf dangerous dangerou alright normal risky sensible sensibl
""".split())
BARE_RANGE = re.compile(r"\d(?:[\d.,]*\d)?\s*(?:-|to|and|–)\s*\d(?:[\d.,]*\d)?\s*$")
# A question about a thing the answer names, however it is turned round: "is it worth cleaning
# the filter" and "is cleaning the filter worth it" are the same question.
ASKS_ABOUT_IT = re.compile(r"^\s*(?:is|are|do|does|should|shall|can|could|will|would|must"
                           r"|need|have|was|were)\b|\?\s*$")

# A follow-up that names nothing of its own ("and how long?", "how long does it keep?") is about
# the thing the answer is already about, so the first figure in it is that thing's: the keeping
# answer's opening "1 to 2 days" is the answer, and the cooked-chicken and freezer figures after
# it are about something else. Without this the whole sentence came back, which is the answer
# repeated rather than the part asked for.
ASKING_ONLY = frozenset("""how what when where which who why much many long time times take takes
taking keep keeps keeping last lasts stay stays good safe should does do is are was were it its
and or the a an of in on at for to from with you we i that this these those still about""".split())

# A yes/no question about one step of the answer: "do I need to parboil them first?"
YES_NO = re.compile(r"^\s*(?:do|does|should|shall|can|could|is|are|will|would|must|need"
                     r"|have)\s+(?:i|we|you|it|they|he|she|this|that|there)\b"
                     r"|\bdo (?:i|we|you) need to\b")

# The step that question actually names: the verb after the pronoun. "Should I have a go" names
# "have", not "worth". Without this the first word of any sentence that shared one word with the
# line counted as its step, and "is it worth paying a plumber or shall I have a go" was answered
# by the last reply's "Worth it for one or two people ..." as if "worth" were the step.
STEP_VERB = re.compile(r"\b(?:do|does|should|shall|can|could|will|would|must|need|have)"
                       r"\s+(?:i|we|you)\s+"
                       r"(?:(?:need|have|want|got)\s+to\s+|be\s+)?"
                       r"([a-z']+)", re.I)


def step_word(question):
    """The verb a yes/no question names as its step, or None when it names none."""
    found = STEP_VERB.search(flat(question))
    return found.group(1).lower() if found else None


def kind_of(question):
    """The property the line asks for: money, distance, time, heat, amount, order or None."""
    clean = " ".join(str(question or "").lower().split())
    for kind, pattern in ASKS:
        if pattern.search(clean):
            # "when is it done" is `when ... is`, so it reads as a date, but a cooking answer
            # has no year to cut out: the line wants the doneness test, which is a sentence
            # ("it sounds hollow when you tap the base"), not a figure. Read as a date it fell
            # back to the timing and said "10 minutes" for bread, and 10 minutes is the knead.
            if kind == "date" and DONENESS.search(clean):
                return None
            return kind
    return None


def asks_a_part(question):
    """Whether a follow-up asks for a part of the answer: a figure, a step or a property."""
    return (kind_of(question) is not None or _property_ask(question) or _option_ask(question)
            or _named_follow_up(question) or bool(YES_NO.search(flat(question)))
            or bool(ASKS_FREQUENCY.search(flat(question)))
            or bool(ASKS_FOR_A_HAND.search(flat(question))))


def _named_follow_up(question):
    """Whether the line follows up on a thing it names ("and if I use a loaf tin?")."""
    clean = flat(question)
    if not FOLLOW_UP.search(clean):
        return False
    named = [word for word in words_of(clean) if word not in NAMING_IGNORE and len(word) > 2]
    return 1 <= len(named) <= 4


_COUNTED_UNIT = re.compile(
    r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
    r"|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty"
    r"|fifty|sixty|seventy|eighty|ninety|a couple of|a few)"
    r"\s+(?:full\s+|whole\s+|solid\s+|straight\s+)?"
    r"(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)\b", re.I)


def _gives_a_figure_in(part, unit):
    """Whether this part of an answer gives a figure in that unit ("about eight weeks").

    The unit word has to be counting a figure, and the figure has to be the word right before it:
    "three times a week" says how often and "each week add a minute" says what to add, and
    neither is the answer to "how many weeks".
    """
    return any(_unit_stem(hit.group(1)) == unit
               for hit in _COUNTED_UNIT.finditer(str(part or "")))


CLAUSE_BREAK = re.compile(r";\s+|,\s+(?:and|but|so)\s+|,\s+", re.I)


def _the_clause_in_the_unit(sentence, unit):
    """The clause of that sentence that gives the figure, said on its own, or None.

    "Each week add a minute to the jog and take one off the walk, and in about eight weeks you
    will run 20 minutes without stopping" holds the figure in its second half, and that half is
    what answers "how many weeks".
    """
    for clause in CLAUSE_BREAK.split(str(sentence or "")):
        part = clause.strip()
        if not part or not _gives_a_figure_in(part, unit):
            continue
        part = re.sub(r"^(?:and|but|so|then|also)\s+", "", part, flags=re.I)
        if len(part.split()) >= 3:
            return part[:1].upper() + part[1:]
    return None


def _the_sentence_in_the_unit(reply, unit):
    """The answer's own sentence that gives a figure in that unit, or None.

    The plain narrowing hands back the first length in the answer, and an answer to a plan names
    several: "one minute of easy jogging, two minutes of walking, repeated for 20 minutes, three
    times a week ... and in about eight weeks you will run 20 minutes without stopping". Asked
    "how many weeks", the 20 minutes answers a question nobody asked, so the sentence whose
    figure is written in the unit asked is the one to hand back.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", str(reply or "")):
        part = sentence.strip()
        if part and _gives_a_figure_in(part, unit):
            return _the_clause_in_the_unit(part, unit) or part
    return None


def part_in_the_unit(reply, question):
    """The part of an answer that gives a figure in the unit the line asks for, or None.

    "How many weeks should I train" after a plan that says sixteen weeks and three runs a week
    wants the sixteen weeks, and this is the one caller that insists on it: a line about another
    unit ("how many days a week" after an answer of 20 minutes) gets nothing here and is left to
    whoever reads the sentence.
    """
    asked = ASKED_UNIT.search(str(question or ""))
    if asked is None:
        return None
    part = narrow(reply, question)
    if not isinstance(part, str) or not part.strip():
        return None
    unit = _unit_stem(asked.group(1))
    said = [word for word in re.findall(r"[A-Za-z]+", part) if _unit_stem(word) == unit
            and word.lower().rstrip("s") in _UNITS]
    return part if said else None


# A validity question asks how long the thing itself lasts, and the answer just given is about a
# different length: "when does it expire", a turn after "how do i renew my passport", was cut out
# of that answer as "Ten weeks." - the processing time, handed back as the life of the document.
# The figure a validity question wants is not in a paragraph about the job, so nothing is cut.
#
# Only for a document. "When does it expire" is also how a kitchen follow-up is asked - "how long
# does cooked chicken keep", then "when does it expire" - and standing down for it there handed
# back "That's beyond what I know well" instead of the chicken's three days. So the stand-down
# needs the thing whose life expires to be in the question or in what the last answer was about.
PAPERWORK = re.compile(
    r"\b(?:passport|licen[cs]e|visa|insurance|policy|certificate|document|membership|permit"
    r"|registration|warranty|guarantee|contract|tenancy|agreement|ticket|card|badge|ehic|ghic"
    r"|prescription|mortgage|bond|deed|statement|mot)\b")
A_VALIDITY_ASK = re.compile(
    r"\bwhen\s+(?:does|do|will|did)\b[^?]{0,40}\bexpir"
    r"|\bexpiry\b|\bexpiration\b"
    r"|\bhow\s+long\s+(?:is|are|does|do|will)\b[^?]{0,40}\b(?:valid|last)\b"
    r"|\b(?:is|are)\b[^?]{0,40}\b(?:still\s+)?(?:valid|in\s+date|out\s+of\s+date|expired)\b")



def asked_unit(question):
    """The unit a "how many weeks" line asks for, as a stem, or None when it names none."""
    asked = ASKED_UNIT.search(str(question or ""))
    return _unit_stem(asked.group(1)) if asked else None


def _states_a_length(part):
    """Whether this part of an answer gives a figure in any unit at all ("20 minutes")."""
    return any(True for _ in _COUNTED_UNIT.finditer(str(part or "")))


# A follow-up that asks how a thing turns out is about the subject the last answer was about:
# "will it be alright" after "i dropped my phone in the sink" wants whether the phone survives,
# "is that bad" after a sore back wants how serious it is, and "what happens now" after the
# boiler keeps losing pressure wants the next move. The line names no subject of its own, so the
# row that answered the line before is the row that owes the answer - and every sentence of its
# card is already on the screen, which is why reading the card out again is not an answer and the
# turn used to give up and point at a search instead. A row that has an answer of its own for the
# ask declares it (`entry(..., outcomes=(("survives", "..."),))`) and this table says which shape
# a line is making, so the same reading decides it for every domain.
OUTCOME_ASKS = (
    # Whether the thing will be all right. Not "is that bad" - that one asks how serious it is.
    ("survives", re.compile(
        r"\bwill (?:it|that|this|they) (?:be )?(?:alright|all right|ok|okay|fine|safe)\b"
        r"|\bis (?:it|that|this) (?:going to be )?(?:alright|all right|ok|okay|fine|safe)\b"
        r"|\bwill (?:it|that|this) (?:survive|recover|work again|be ruined|be knackered)\b"
        r"|\bis (?:it|that|this) (?:ruined|knackered|a write[- ]off|done for)\b"
        r"|\bcan (?:it|that|this) be (?:saved|fixed|repaired|salvaged)\b"
        r"|\bis (?:it|that|this) worth (?:fixing|repairing)\b", re.I)),
    # How serious it is, and whether it needs anything doing. "is that normal" is the same ask
    # about a symptom or a child.
    ("serious", re.compile(
        r"\bis (?:that|this|it) (?:bad|serious|dangerous|normal|common)\b"
        r"|\bhow (?:bad|serious) is (?:it|that|this)\b"
        r"|\bshould i (?:be )?worr(?:y|ied)\b"
        r"|\bis (?:that|this) (?:something|anything) to worry about\b"
        r"|\bis that (?:a|normal)\b", re.I)),
    # What happens next, as in what follows from it. Not "what do i do now": that is the same
    # question the card has just answered, and the first sentence of the card is its answer -
    # reading it as an outcome sent "my boiler pressure is low" then "what do i do now" to the
    # engineer, where topping the pressure up is the move.
    ("next", re.compile(
        r"\bwhat happens (?:now|next)\b"
        r"|\bwhat next\b|\bwhat(?:'s| is| was) (?:the )?next\b|\bso what now\b"
        r"|\bwhat now\b", re.I)),
    # What the thing said actually means.
    ("explain", re.compile(
        r"\bwhat does (?:that|this|it) mean\b|\bwhat do you mean\b"
        r"|\bwhat(?:'s| is) that (?:mean|mean then)\b|\bmeaning what\b", re.I)),
)


def the_outcome_asked(question):
    """Which of the outcome asks the line makes, or "" when it makes none."""
    said = flat(question)
    for which, pattern in OUTCOME_ASKS:
        if pattern.search(said):
            return which
    return ""


def the_part_asked(reply, question, about=""):
    """The part of the answer the line asks for, with the unit it names respected.

    "how many weeks" after a training plan was answered "20 minutes." - the narrowing takes the
    first length in the answer, and that length is written in another unit than the one asked
    for. A line that names its unit is answered by the figure the answer writes in that unit,
    when the answer has one. A part that states no length at all ("9 to 10 for hard boiled") is
    the answer's own shape for the figure asked, so it stands, and so does a line that names no
    unit ("how long"), which is the narrowing's business.
    """
    part = narrow(reply, question, about)
    unit = asked_unit(question)
    if unit is None or _gives_a_figure_in(part, unit) or not _states_a_length(part):
        return part
    return _the_sentence_in_the_unit(reply, unit) or part


# A period written on a figure makes it a rate rather than a price: "£1,500 a year", "25 an
# hour". "once a year" is how often the thing happens, not what the figure is for, so the period
# has to follow the number directly.
A_RATE_ON_A_FIGURE = re.compile(
    r"\s+(?:a|an|per|each)\s+(year|month|week|day|hour)\b", re.I)
A_PERIOD_IN_A_LINE = re.compile(
    r"\b(?:a|an|per|each)\s+(year|month|week|day|hour)\b", re.I)


def _a_rate_cut_from_its_figure(reply, part, question):
    """Whether `part` is a figure that left the period making it a rate behind.

    "and how much does one cost" after a dog's "budget about £1,500 to £2,000 a year" was
    handed "£1,500 to £2,000.", the yearly cost of keeping a dog said as if it were the price
    of one. A rate the line did not ask about is not the price it asked for; a line that asks
    "a year" keeps it. Only a period written directly on the figure counts: "a service is £60
    to £120 once a year" prices the service, not the year.
    """
    whole = flat(reply)
    piece = flat(part)
    figure = next(SPANS["money"].finditer(piece), None)
    if figure is None:
        return False
    asked = A_PERIOD_IN_A_LINE.search(flat(question))
    periods = []
    for hit in SPANS["money"].finditer(whole):
        if hit.group(0).lower() != figure.group(0).lower():
            continue
        found = A_RATE_ON_A_FIGURE.match(whole[hit.end():hit.end() + 14])
        if not found:
            # The same figure is also written as a plain price somewhere in the answer, so the
            # part may be that price: leave it alone rather than guess.
            return False
        periods.append(found.group(1).lower())
    if not periods:
        return False
    return not asked or asked.group(1).lower() not in periods


def narrow(reply, question, about=""):
    """The part of `reply` that answers `question`, or None when it cannot say safely.

    None also means the part would be the whole reply: the caller must not repeat it.
    about is what the last answer was about, for a question too short to say its own subject
    ("when does it expire" after the passport): it decides whether the line is asking about a
    document, and only a document's life is a validity question.
    """
    said = flat(question)
    if A_VALIDITY_ASK.search(said) and (PAPERWORK.search(said) or PAPERWORK.search(flat(about))):
        return None
    part = _narrow(reply, question)
    if part is None:
        return None
    # A part that starts on the word joining it to the rest of its sentence is not an answer
    # anyone can read: "Around 400mg of caffeine a day is the usual safe limit for an adult,
    # which is about four cups of coffee" was handed back as "Which is about four cups of
    # coffee." - a relative clause said on its own. The readers below cut at commas and at
    # "and"/"but", so this is the last check before the turn is spoken.
    if JOINS.match(flat(part)):
        return None
    if kind_of(question) == "money" and _a_rate_cut_from_its_figure(reply, part, question):
        return None
    return part


# The words that cannot open a sentence: they tie a clause to the one before it. A clause that
# begins with one of these was cut out of the middle of a sentence and needs the clause in front.
# Only the words that cannot open a sentence at all. "and", "but", "so" and "then" can, and a
# part starting with one of those ("Then leave it five minutes.") is a sentence in its own right.
JOINS = re.compile(r"^(?:which|that|who|whom|whose|where|because|though|although|whereas"
                   r"|while|yet|however|instead|plus|as well)\b", re.I)


# A line that asks how long the thing itself lasts, rather than how long a job takes.
_STATE_LENGTH_ASKS = re.compile(
    r"\b(?:last|lasts|lasted|keep|keeps|kept|stays?|stay like this|be like this|go away|"
    r"goes away|clear up|clears up|get better|gets better|recover|recovers|heal|heals)\b", re.I)
# The doings an advice card gives a time for: "ice it for 20 minutes", "rest it for two days".
_A_DOING = re.compile(
    r"\b(?:ice|icing|rest|resting|take|taking|apply|applying|use|using|hold|holding|keep|keeping|"
    r"wear|wearing|put|putting|wrap|wrapping|elevate|elevating|soak|soaking|leave|leaving|rinse|"
    r"rinsing|clean|cleaning|stretch|stretching|massage|massaging|drink|drinking|eat|eating|"
    r"swallow|swallowing|avoid|avoiding|stop|stopping|exercise|exercising|compress|bandage|"
    r"dress|dressing|change|changing|walk|walking|run|running|sit|sitting|lie|lying)\b")


def _a_length_of_a_doing(sentence, part, question):
    """True when `part` is how long something the advice tells them to do goes on for.

    "my knee hurts" then "how long will it last" was answered "Two days.", cut out of "ice it for
    20 minutes at a time with a cloth round it for the first two days": the two days are how long
    to keep icing it, not how long the sore knee lasts, and "Two days." to somebody worried about
    their knee is a promise nobody made. A line that names the doing keeps its figure ("how long
    should i ice it"), and a length with no doing in front of it is the thing's own ("most coughs
    after a cold last two to three weeks").
    """
    if not _STATE_LENGTH_ASKS.search(flat(question)):
        return False
    said = flat(sentence)
    cut = flat(part)
    at = said.find(cut) if cut else -1
    if at < 0:
        return False
    doing = set(_A_DOING.findall(said))
    if not doing or doing & set(_A_DOING.findall(flat(question))):
        return False
    # The clause the figure sits in, not a window of characters: the doing that owns a length is
    # the one the clause opens with ("ice it for 20 minutes at a time with a cloth round it for
    # the first two days"), and a figure of the thing itself opens its own clause with the thing
    # ("most coughs after a cold last two to three weeks").
    return bool(_A_DOING.search(_a_clause_before(said, at)))


# The figure of an advice card is often a cut-off, not a length: "For a baby over six months, a
# consistent wind-down..." was answered to "how long will this last" with "Six months." - the age
# the advice starts at, said as the length of the trouble. "At around six months", "never under 3
# months", "adults over 65" and "aged 6 to 12" are the same figure, and none of them says how long
# anything lasts. What tells a cut-off from a real length in the same words is the verb: "most back
# pain lasts over two weeks" writes the figure as the length of the thing, while a cut-off has a
# noun in front of it and no verb of duration between.
_A_CUT_OFF_BEFORE = re.compile(
    r"\b(?:over|under|above|below|past|aged|beyond|around|about|from|at|by|until|till|"
    r"after|before|of)\s*$", re.I)
_A_CUT_OFF_AFTER = re.compile(
    r"^\s*(?:or\s+(?:over|older|under|younger|more|less)|and\s+(?:over|under)|of\s+age)\b", re.I)
_A_DURATION_VERB = re.compile(
    r"\b(?:last|lasts|lasted|lasting|take|takes|took|taking|settle|settles|go|goes|went|gone|"
    r"going|run|runs|ran|keeping|kept|stay|stays|stayed|heal|heals|healed|clear|clears|"
    r"cleared|recover|recovers|recovered|recede|recedes|ease|eases|expires?|expiring|"
    r"is|are|was|were|be|been|being)\b", re.I)
# A cut-off on a thing's own trouble is written in weeks and days ("a cough over three weeks needs
# a look"), and that figure is how long the trouble has gone on, not an age. The figures that
# stand for an age are the ones in months and years, or said with no unit at all ("children under
# five").
_IN_MONTHS_OR_YEARS = re.compile(r"\b(?:month|months|year|years)\b", re.I)
_A_RANGE = re.compile(r"\b(?:to|or|-|and)\b", re.I)
_A_BARE_FIGURE = re.compile(
    r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
    r"fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|\d{1,3}|a|an|"
    r"half)", re.I)


def _a_cut_off_not_a_length(sentence, part):
    """True when the figure `part` is the cut-off a rule starts at, not a length of anything.

    Only the words around the figure decide it. A figure with over/under/aged/around in front of
    it, whose own clause has no verb of duration, is a condition on the person or thing it
    describes ("a baby over six months", "children under five"), so cutting it out answers "how
    long will this last" with an age nobody said was a length. The same words with a duration verb
    in front of them ("most back pain lasts over two weeks") are the thing's own length and stand.
    """
    said = flat(sentence)
    cut = flat(part).rstrip(". ")
    if not cut:
        return False
    at = said.find(cut)
    if at < 0:
        return False
    before = said[:at]
    after = said[at + len(cut):]
    if not (_A_CUT_OFF_BEFORE.search(before) or _A_CUT_OFF_AFTER.match(after)):
        return False
    if not (_IN_MONTHS_OR_YEARS.search(cut) or _A_BARE_FIGURE.fullmatch(cut)):
        return False
    if _A_RANGE.search(cut):
        return False  # "four to six months" is a span someone can ask the length of
    clause = _a_clause_before(said, at)
    return not _A_DURATION_VERB.search(clause)


def _a_clause_before(said, at):
    """The clause `at` sits in: back to the nearest comma, colon or semicolon.

    The nearest mark, whatever it is: taking the first kind of mark that turns up reads across a
    semicolon into the clause before it, and "most coughs after a cold settle in two to three
    weeks" then looked like an instruction to keep doing something, because the half-sentence
    before it in the same sentence says "keep the room from getting dry".
    """
    start = 0
    for mark in (",", ";", ":"):
        cut = said.rfind(mark, 0, at)
        if cut >= 0:
            start = max(start, cut + 1)
    return said[start:at]


def the_doings_length(reply, question):
    """The clause of `reply` that gives a time for something to keep doing, or "".

    `_narrow` skips such a part, which leaves a length ask with nothing - and nothing is not an
    improvement on the wrong figure. "my knee hurts" then "how long will it last" was answered
    "Two days.", then left the card below it to guess at bones; what the card does hold is a real
    instruction with a clock on it ("ice it for 20 minutes at a time with a cloth round it for the
    first two days"), and a caller can say honestly that it holds no length of its own and give
    that instruction instead.

    Nothing is handed back when the answer states a length of the thing itself ("most coughs
    after a cold last two to three weeks"), because then there is a length to answer with, and
    nothing when the line names the doing ("how long should i ice it"), because that figure is
    the answer.
    """
    whole = flat(reply)
    if not whole or not _STATE_LENGTH_ASKS.search(flat(question)):
        return ""
    kind = kind_of(question)
    if kind not in ("time", "clock"):
        return ""
    clauses = []
    for sentence in SENTENCE.split(str(reply or "")):
        if not sentence.strip() or not SIGNALS[kind].search(sentence):
            continue
        part = _part(sentence, kind, question)
        if not part or part is NO_LENGTH:
            continue
        if not _a_length_of_a_doing(sentence, part, question):
            return ""  # the answer states the thing's own length, so there is nothing to add
        said = flat(sentence)
        clause = _the_clause_around(said, said.find(flat(part)))
        if clause and flat(clause) != whole:
            clauses.append(clause)
    return clauses[0] if clauses else ""


def _the_clause_around(said, at):
    """The clause `at` sits in, back to the mark before it and up to the mark after it."""
    if at < 0:
        return ""
    start = 0
    for mark in (",", ";", ":"):
        cut = said.rfind(mark, 0, at)
        if cut >= 0:
            start = max(start, cut + 1)
    end = len(said)
    for mark in (",", ";", ":"):
        cut = said.find(mark, at)
        if cut >= 0:
            end = min(end, cut)
    return said[start:end].strip(" .")


def _at_another_place(sentence, part, question):
    """Whether this part gives the figure of a place other than the one the line asks about.

    "8 minutes in the microwave first cuts the oven time to 25" holds the microwave's figure, and
    asked "how long in the oven" the part cut out of that sentence was "8 minutes": the words just
    after a figure say whose figure it is, and the oven's own time is in the sentence around it
    ("bake at 200C for about an hour"). A figure followed by the place asked for ("45 minutes in
    the oven") is that place's own, and so is a figure no place follows.
    """
    asked = {word.lower() for word in PLACE.findall(flat(question))}
    if not asked:
        return False
    said = flat(sentence)
    cut = flat(part)
    at = said.find(cut) if cut else -1
    if at < 0:
        return False
    found = PLACE.search(said[at + len(cut):])
    if not found:
        return False
    return found.group(0).lower() not in asked


def _gives_another_places_figure(sentence, kind, question):
    """Whether the sentence's own figure for this ask is written at another place."""
    if kind not in SPANS:
        return False
    part = _part(sentence, kind, question)
    if not part or part is NO_LENGTH:
        return False
    return _at_another_place(sentence, part, question)


def _narrow(reply, question):
    if not isinstance(reply, str) or not reply.strip():
        return None
    kind = kind_of(question)
    if kind == "remedy":
        # What to take is a clause of a sentence, not a figure: the answer names the medicine
        # somewhere inside itself, and the part asked for is that clause.
        part = _the_remedy_in(reply)
        return part if part and flat(part) != flat(reply) else None
    if kind is not None and kind not in SPANS:
        # "can I make it the day before?" asks for a step, and there is no figure in the answer
        # to cut out for it: this module hands back figures and the clause around them, so the
        # sentence such a question lands in (the doneness test) is not the answer to it.
        # Whoever reads whole sentences answers that line, not this module.
        return None
    whole = flat(reply)
    if URGENT.search(whole):
        return None
    sentences = [s.strip() for s in SENTENCE.split(reply.strip()) if s.strip()]
    when_ask = False
    if kind == "date":
        dated = _dated(sentences, question, whole)
        if dated:
            return dated
        # A date ask with no dated sentence in the answer is the timing in it when the line
        # asks when something happens ("when should the bread go in"). It is not the timing
        # when the line asks for the date itself: "what year" after a proving answer was
        # answered "1 to 2 hours", a duration handed to a question about a year.
        if ASKS_THE_DATE_ITSELF.search(flat(question)):
            return None
        when_ask = True
        kind = "time" if SIGNALS["time"].search(reply) else None
        if kind is None:
            return _the_answer_said_again(sentences, whole)
    # A question that names the thing it is about ("how long should the opening be?") is
    # answered by the sentence that names it too, not by the first figure in the answer. The
    # words that only point at the thing in hand are not names: see `POINTS_BACK`.
    wanted = {word for word in words_of(question) if word not in POINTS_BACK}
    if wanted:
        naming = [one for one in sentences if wanted & set(words_of(one))]
        if naming:
            # A sentence can name the place asked about and give the figure of another place
            # ("8 minutes in the microwave first cuts the oven time to 25"), and then reading
            # only the sentences that name the place leaves nothing but the wrong figure. Where
            # that is every sentence which names it, the answer is read as it was before.
            sentences = [one for one in naming
                         if not _gives_another_places_figure(one, kind, question)] or sentences
    if kind == "cause":
        # The reason is a whole sentence, not a figure: give the one that says why and leave
        # everything else out. No sentence that says why -> no answer, rather than a guess.
        # A bare "why?" could be about any part of a long answer, so only its opening sentence
        # gets a say; a line that says what it is asking about ("what could be causing it")
        # can reach the sentence that names the reason later on.
        # A word only one sentence has ("sunset", "whistling") says which cause is being
        # asked about, even when an earlier sentence also gives a reason.
        only = {word for word in wanted
                if sum(word in set(words_of(one)) for one in sentences) == 1}
        if only:
            named = [one for one in sentences if only & set(words_of(one))]
            if named:
                sentences = named
        openings = sentences[:1] if flat(question).strip(" ?!.") == "why" else sentences
        for sentence in openings:
            if CAUSE.search(sentence):
                return tidy(sentence) if flat(sentence) != whole else None
        return None
    if kind == "time" and PLACE.search(question):
        sentences = [one for one in sentences if PLACE.search(one) or COOKS.search(one)]
    if kind == "time" and BEFORE.search(question):
        # "how long before i can play a song" asks when the result comes, so the sentence that
        # names the result is the one to read and it is read ahead of everything else: in "ten to
        # fifteen minutes a day beats one long session ... then play songs that use them" the
        # word "song" is in the practise sentence, so the clause reader took that one and the
        # per-day figure came back for a question about months. When no sentence names a result
        # the rest of the answer is read as before.
        for sentence in [one for one in sentences if RESULT.search(one)]:
            # The span in days, weeks, months or years is the answer, and the sentence around it
            # is often longer than the line asked for: "Most people can strum through a simple
            # song in two or three months that way; sore fingertips for the first fortnight are
            # normal" gives the months on their own.
            found = [_figure(match, sentence) for match in RESULT.finditer(sentence)]
            part = tidy(found[-1]) if found else None
            if part and flat(part) != whole:
                return part
    # The clause of the answer that is about the thing the line names ("the loaf tin", "the
    # shoes"): a follow-up about a thing in the answer gets that thing, not the whole answer.
    piece = _named_clause(reply, question)
    if piece:
        piece = _with_unit(piece, reply)
        if kind is not None and kind in SPANS and SIGNALS[kind].search(piece):
            part = _part(piece, kind, question)
            if part is NO_LENGTH:
                # A clause of rates ("20 minutes a day ... a week") holds no length for a
                # "how long does the whole job take" ask: `_part` says so with the sentinel, and
                # it is not a figure. Read as one it went through `tidy` and came back to the
                # person as "<object object at 0x...>." - see `tidy`'s own guard below.
                part = None
            if part and _at_another_place(piece, part, question):
                # The clause names the place asked about and gives another place's figure, so the
                # figure the person wants is in the sentences below.
                part = None
            if part:
                part = tidy(part)
                if part and flat(part) != whole:
                    return part
    if kind is None:
        often = _how_often(sentences, question, whole)
        if often:
            return often
        found = _not_a_figure(sentences, question, whole, reply)
        if found:
            return found
        named = _the_part_they_named(sentences, question, whole)
        if named:
            return named
        # A follow-up that names a thing without asking its figure ("and for chops", "what
        # about a turkey") is still about the figure that thing has, and the answers read that
        # way are lists of one figure per thing. The words of the line pick the item; the whole
        # clause around the list names every one of them.
        for guess in ("time", "money", "distance", "amount", "heat"):
            one = _the_item_they_named(piece or reply, guess, question)
            if one:
                part = tidy(one)
                if part and flat(part) != whole:
                    return part
        if piece and (FOLLOW_UP.search(flat(question)) or YES_NO.search(flat(question))
                      or ASKS_ABOUT_IT.search(flat(question))):
            # A yes/no question about a thing the answer names is answered by the clause that
            # speaks of that thing: "is it worth cleaning the filter" wants "clean the filter
            # and the detergent drawer while it runs", not the whole service wash again. It is
            # named outright rather than pointed at, which is why the pointer words are not
            # needed here.
            said = tidy(piece)
            if not _informative(piece) or _cuts_a_list(piece, reply):
                # "closed clean shoes" is the part that answers, but said alone it is a piece of
                # the sentence that gives it: that sentence carries what to do with it.
                holder = [one for one in sentences if flat(piece) in flat(one)]
                longer = tidy(holder[0]) if holder else None
                if longer and len(longer.split()) > len(said.split()) \
                        and flat(longer) != whole:
                    return longer
            if said and flat(said) != whole:
                return said
        return None
        return None
    wait = bool(WAIT.search(question))
    skipped_a_cut_off = False
    for sentence in sentences:
        if not SIGNALS[kind].search(sentence):
            continue
        both = _a_figure_each(sentence, kind)
        if both:
            # Two figures for two things in one sentence: a line that names one of them is asking
            # about that one, and the other half's figure is the wrong answer to it ("how long for
            # black tea" came back as the green tea's 2 to 3 minutes). A line that names neither is
            # left to the clause reader below, so the bare "and how long" says exactly what it
            # said before.
            one = _the_half_they_named(both, question)
            if one:
                part = tidy(one)
                if part and flat(part) != whole:
                    return part
        if wait and kind == "time" and not WAIT.search(sentence):
            continue
        part = _part(sentence, kind, question)
        if part is NO_LENGTH:
            continue  # a sentence of rates: the length, if there is one, is in the next
        if part and _at_another_place(sentence, part, question):
            continue  # another place's figure: this place's is in the sentence after it
        if part and part is not NO_LENGTH and _a_length_of_a_doing(sentence, part, question):
            continue  # how long to keep doing it, not how long the thing lasts
        if part and part is not NO_LENGTH and _a_cut_off_not_a_length(sentence, part):
            skipped_a_cut_off = True
            continue  # the age a rule starts at, not how long anything goes on for
        if part:
            part = tidy(_as_a_length(part))
            if part and flat(part) != whole:
                holder = _the_sentence_a_figure_hangs_on(part, sentence, whole, when_ask)
                if holder:
                    return holder
                return part
        if when_ask:
            # The answer holds no sentence that says when, so there is no part of it to cut out
            # and the person's "and when do i pay it" would go to the general hedge - "That's
            # beyond what I know well, sorry" - right after the answer about the same thing.
            # What this chat knows about it is the answer they were just given, so its opening
            # is said again rather than nothing.
            return _the_answer_said_again(sentences, whole)
        if skipped_a_cut_off:
            # The only figure this answer gave was the age the advice starts at, so this sentence
            # has no length to cut out. The next one may say how long the thing goes on for.
            continue
        return None
    if kind == "time" and (LENGTH_OF_THE_JOB.search(flat(question))
                           or _STATE_LENGTH_ASKS.search(flat(question))):
        # A "how long" whose answer states no length at all - a skill, a habit, a job - has no
        # figure to cut out. What it does say is how the time is spent, and that is the answer
        # to give instead of a figure about something else in the sentence.
        said = _the_time_it_does_keep(sentences, whole)
        if said:
            return said
    return None


# What a length ask gets from an answer that states no length: the sentence that says how the
# time is spent, said plainly and marked as the one thing the answer does say. Cutting the figure
# out of the answer instead gave "Five seconds." (how long a child must balance) and "Ten
# minutes." (the warm-up), and handing back nothing repeated the whole paragraph behind "Same as
# before:". Neither is an answer to "how long does it take".
NO_SET_TIME = "No set time on that one - "
# The answer's only figure is the age the advice starts at, so there is no length in it anywhere:
# the solids card gives "three signs, all at once, and around six months" and nothing about how
# long the stage lasts. Cutting that figure out said "Six months." as though it were a length, and
# handing the whole card back answered a different question - `should i start him on solids` /
# `how long will that go on for` got the card again, with no length in it at all. What is left is
# the honest one: there is no set stretch, and the figure is where the thing starts.
A_STAGE = ("It's a stage rather than a set stretch: {when} is where it starts.",)
# The leads that read as a start age: "around six months", "from six months". "Under" and "below"
# are the other way round - "under 3 months is too early" is a warning and not a start.
A_START_LEAD = re.compile(r"\b(?:around|about|at|by|from|after|past)\s+$", re.I)


def _the_start_age(sentence, figure, at):
    """The figure as a start age ("around six months"), or None if it is not read as one."""
    flat_sentence = flat(sentence) if hasattr(sentence, "split") else str(sentence)
    try:
        before = flat_sentence[max(0, at - 24):at]
    except Exception:  # noqa: BLE001 - a sentence that cannot be cut gives no start age
        return None
    lead = A_START_LEAD.search(before)
    if lead:
        return " ".join((lead.group(0).strip() + " " + figure).split())
    return " ".join(figure.split())



def _the_time_it_does_keep(sentences, whole):
    """The sentence of the answer that talks about time, said as the help it is."""
    start_age = None
    for sentence in sentences:
        if not SIGNALS["time"].search(sentence):
            continue
        timed, last_end = [], -1
        for match in SIGNALS["time"].finditer(sentence):
            if match.start() < last_end:
                continue  # the "a day" of "30 minutes a day": part of a rate, not its own figure
            last_end = match.end()
            if IN_A_RELATIVE.search(sentence[:match.start()]):
                continue  # a figure about something else: "who can balance for five seconds"
            if FREQUENCY_AFTER.match(match.group(0)) \
                    and not _a_period_of_extent(sentence, match.start()):
                continue  # a period word on its own is the "a day" of a rate, not a figure
            if FREQUENCY_AFTER.match(sentence[match.end():]):
                continue  # the period word of a rate ("a day" of "30 minutes a day")
            timed.append(match)
        if not timed:
            continue
        if LENGTH_OF_THE_JOB.search(sentence) or re.search(r"\bdepends\b", sentence, re.I):
            continue
        if start_age is None and all(_a_cut_off_not_a_length(sentence, match.group(0))
                                     for match in timed):
            # Every figure in this sentence is the age the advice starts at. It is not the length,
            # but it is the only thing the answer says about when, so it is kept in case the
            # answer turns out to have no length at all.
            one = timed[0]
            start_age = _the_start_age(flat(sentence), one.group(0), one.start())
        clause = None
        for one in re.split(r"\s*(?:;|,\s*(?:and|but|so)\b)", sentence.strip()):
            # The clause that says how the time is spent is not always the first one: "For a baby
            # over six months, a consistent wind-down helps; feedings at night are normal for much
            # longer" opens on the age the advice starts at, and the half after the semicolon is
            # the one about the time. A clause whose only figure is that age is passed over.
            one = one.strip(" .,")
            if _only_a_cut_off(one) or not _says_a_time(one):
                continue
            clause = one
            break
        if clause is None:
            continue
        if len(clause.split()) < 3 or len(clause.split()) > 24:
            continue
        if flat(clause) == whole:
            continue
        return NO_SET_TIME + clause[0].lower() + clause[1:] + "."
    if start_age:
        # The answer has no length in it at all, and the ask was how long it goes on for. The
        # stage line says what the answer does say: this much is where it starts.
        return A_STAGE[0].format(when=start_age)
    return None


# A bare period word is usually the "a day" of a rate ("20 minutes a day", "twice a year"), which
# is why the fallback above passes it over. Introduced by a word of extent it is a length: "milk is
# still the main meal until about a year" says how long the phase goes on, and a length ask about
# it has an answer in the answer already given.
_A_PERIOD_OF_EXTENT = re.compile(
    r"\b(?:until|till|til|from|after|by|for|about|around|up to|past|through|over|under|beyond)\s+"
    r"(?:about\s+|around\s+|roughly\s+|nearly\s+|almost\s+|just\s+)?$", re.I)


def _a_period_of_extent(sentence, at):
    """Whether the time ending at `at` is introduced by a word of extent ("for a month")."""
    return bool(_A_PERIOD_OF_EXTENT.search(flat(sentence)[:at]))


def _says_a_time(clause):
    """Whether this clause says anything about time at all.

    The fallback hands the person the half of the sentence about the time, so a half that only
    lists signs ("three signs, all at once") is not it - that answered "how long will that go on
    for" with a list of what to look for.
    """
    return bool(SIGNALS["time"].search(clause)
                or re.search(r"\b(?:long|longer|slow|quick|soon|never|until|till|months?|weeks?|"
                             r"years?|days?|hours?|minutes?)\b", clause, re.I))


def _only_a_cut_off(clause):
    """Whether every figure in this clause is the age a rule starts at, and none is a length.

    "For a baby over six months" is a clause about when the advice begins; "feedings at night are
    normal for much longer" is a clause about the time. Only the second answers "how long will
    this last", so the first is passed over rather than said as if it gave the length.
    """
    figures = [match.group(0) for match in SIGNALS["time"].finditer(clause)]
    if not figures:
        return False
    return all(_a_cut_off_not_a_length(clause, figure) for figure in figures)


def _the_answer_said_again(sentences, whole):
    """The sentence an answer opens with, when the answer has more to it than that.

    Only for a when ask the answer says no when about: the hedge that would take the turn instead
    reads as the bot forgetting what it just said.
    """
    if len(sentences) < 2:
        return None
    opening = tidy(sentences[0])
    if not opening or flat(opening) == whole or len(opening.split()) > 30:
        return None
    return opening


# A figure on its own is a fragment, not an answer: "when do i have to pay" got "14 days." out
# of "Paying within 14 days usually gets a 50% discount", and only the sentence says when the
# figure is on. A piece that carries its own when already ("within 14 days", "by Friday") stands
# alone, and a long sentence is not an improvement on a short figure.
A_WHEN_WORD = re.compile(r"\b(?:within|by|in|on|at|from|after|before|until|till|til|since|every"
                         r"|each|during|over|under|about|around|past|for|of)\b", re.I)


def _the_sentence_a_figure_hangs_on(part, sentence, whole, when_ask=False):
    # Only a when ask: a length is a figure by design, and "how long were they here" wants the
    # "400 years" it was answered with, not the sentence that length sits in.
    if not when_ask:
        return None
    if A_WHEN_WORD.search(part) or len(part.split()) > 4:
        return None
    holder = tidy(sentence)
    if not holder or flat(holder) == whole or len(holder.split()) > 25:
        return None
    if flat(part).strip(" .,;:!?") not in flat(holder):
        return None
    return holder


# A follow-up that asks how often ("how often should i go", "and how often in winter") wants
# the answer's own frequency, which is a phrase rather than a figure: "two or three sessions a
# week", "once a day", "every other morning".
ASKS_FREQUENCY = re.compile(r"\bhow (?:often|regularly|frequently)\b|\bhow many times\b", re.I)

# "a day" and "a week" on their own are rates, not how often something is done: "under 6g a day"
# is an amount. A frequency names how many times (once, twice, three times), a period
# (daily and its family), or repeats it ("every other morning").
FREQUENCY = re.compile(
    # "once" is a rate only when a period follows it: "once a week" is how often, "once the
    # walking feels easy" is a condition, and reading the second as a rate answered "how often
    # should i go" with the strength work rather than with the two walks a week.
    r"\bonce (?:a|an|every|per|or twice|in a)\b"
    r"|\b(?:twice|thrice|nightly|daily|weekly|fortnightly|monthly|yearly|annually)\b"
    r"|\b(?:two|three|four|five|six|seven|eight|ten|twelve) (?:times|sessions|days|nights"
    r"|weeks|months|years) (?:a|per|each)\b"
    r"|\b(?:two|three|four) (?:or|to) (?:three|four|five) (?:times|sessions|days|nights)\b"
    r"|\bevery (?:(?:couple|few|other|one|two|three|four|six|twelve|\d+)\s+(?:of\s+)?)?"
    r"(?:day|week|month|year|morning|evening|night|fortnight)s?"
    r"|\bnot on a fixed\b", re.I)

# The words of the ask that say nothing about the thing done: what is left is the verb the
# person asked about ("mow", "check", "go"), and a clause about something else is not the answer.
FREQUENCY_IGNORE = frozenset("""
often regular regularly frequent frequently times time many much usually normally should
shall need needs want wants how do does did i we you they it them the a an of for in on at
winter summer spring autumn fall morning evening night day week month year now
and but so then or also plus because while which
""".split())

# "how many weeks", "how many minutes": the ask says which unit the figure it wants is in.
ASKED_UNIT = re.compile(r"\bhow many\s+(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?"
                        r"|weeks?|months?|years?)\b", re.I)
_UNITS = {"second": "second", "sec": "second", "minute": "minute", "min": "minute",
          "hour": "hour", "hr": "hour", "day": "day", "week": "week", "month": "month",
          "year": "year"}


def _unit_stem(word):
    """The thing a unit word counts: "mins", "minute" and "minutes" are all a minute."""
    bare = str(word or "").strip(".,;:!?").lower().rstrip("s")
    return _UNITS.get(bare, bare)

# "fifteen minutes of puzzles a day" is how often too, but "under 6g of salt a day" is an
# amount, so this weaker reading is only used when the clause is about the very thing the line
# names ("how often should i play" -> the puzzles sentence, never the salt one).
RATE_FREQ = re.compile(r"\b(?:a|an|per|each) (?:day|week|month|year)\b", re.I)

# A bare "and" joins nouns as often as it joins clauses: "flour and water, ... once a day" is
# one instruction, and cutting at the "and" said back "Water, about its own weight, once a day",
# which is not a sentence anyone can act on. Only a comma before the conjunction, a semicolon or
# a full stop is a boundary.
FREQ_CLAUSE = re.compile(r";\s*|(?<=[.!?])\s+|,\s+(?:and|but|so|then)\s+")


def _same_word(one, other):
    """Whether two words are the same word or one is the other with an ending on it."""
    if one == other:
        return True
    short = 4 if min(len(one), len(other)) >= 4 else 3
    return one[:short] == other[:short]


def _names_one_of(wanted, words):
    return any(_same_word(word, said) for word in wanted for said in words)


# A condition is an interval too, and often the only honest one: the shower head has no rate in
# it at all, just "do it again whenever it furs up", and that is what "how often" is asking for.
# The verb after it has to be one of a thing needing or showing, so a "when" that is doing some
# other work in the sentence is not read as the interval.
TRIGGER_PATTERN = (r"\b(?:whenever|when|as soon as|if)\s+(?:it\s+|they\s+|you\s+)?"
                   r"(?:needs?|starts?|looks?|furs?|smells?|sounds?|shows?|gets?|builds?|feels?"
                   r"|goes?|is\b)")
TRIGGER = re.compile(TRIGGER_PATTERN, re.I)

# An interval is a rate, and a rate is a count with a period round it: "boil fresh water twice"
# is how many times to boil, not how often to descale. FREQUENCY is right for finding the rate
# clause inside a sentence, but a bare "twice" is enough for it, so the test for whether an
# answer has an interval at all needs the period.
RATE_INTERVAL = re.compile(
    r"\bonce (?:a|an|every|per|or twice|in a)\b"
    r"|\b(?:twice|thrice)\s+(?:a|an|per|each|every|daily|weekly|monthly|yearly|nightly)\b"
    r"|\b(?:daily|weekly|fortnightly|monthly|yearly|annually|nightly)\b"
    r"|\b(?:two|three|four|five|six|seven|eight|ten|twelve) (?:times|sessions|days|nights"
    r"|weeks|months|years) (?:a|per|each)\b"
    r"|\bevery (?:other )?(?:day|week|fortnight|month|year|morning|evening|few|couple|\d+)\b"
    r"|\bevery (?:month|week|day|year) or (?:two|so)\b"
    + "|" + TRIGGER_PATTERN)

# "twice" on its own counts how many times, and a rate needs the period beside it.
A_BARE_COUNT = re.compile(r"\b(?:once|twice|thrice|(?:" 
                          r"two|three|four|five|ten) times)\b(?!\s*(?:a|an|per|each|every|"
                          r"daily|weekly|monthly|yearly|nightly|or\b|in a\b))", re.I)


def _only_a_count(piece):
    """True when the only rate words in the piece are counts with no period beside them."""
    found = list(FREQUENCY.finditer(piece))
    if not found:
        return False
    return all(A_BARE_COUNT.match(match.group(0)) or match.group(0).lower().strip() in
               ("once", "twice", "thrice") for match in found) and \
        not RATE_INTERVAL.search(piece)


# A line that is only the interval ask: "how often", "and how often", "how often should i do
# that". It names no thing of its own, so the thing in hand is the answer it follows - and where
# that answer carries no interval there is none to hand back ("how do i descale my kettle" then
# "how often" gave the last step again, and the oven gave the whole how-to behind "Same as
# before:"). The steps answer what to do, not when.
ONLY_THE_INTERVAL_ASK = re.compile(
    r"^\s*(?:and |also |so |ok |okay |oh |right )*"
    r"(?:how (?:often|regularly|frequently)|how many times)"
    r"(?:\s+(?:should|do|would|must|need|needs|shall)\s+(?:i|we|you))?"
    r"(?:\s+(?:i|we)\s+(?:need|have|ought)\s+to)?"
    # Only "do that" / "do it": a line that names its own verb ("how often do i feed it") says
    # what it is about, and the answer it is in has already been read for that - the caller's
    # own reading of it is better than a sentence that says the steps have no interval.
    r"(?:\s+do(?:es)?\s+(?:that|it|this|so))?"
    r"(?:\s+(?:do|does)\s+(?:i|we)\s+need\s+to)?"
    r"(?:\s+(?:it|that|this|them|those))?"
    r"(?:\s+(?:again|then|now|really))?"
    r"\s*[?.!]*\s*$", re.IGNORECASE)

# What is said when the answer in hand has no interval in it. It does not invent a rate: the
# person asking "how often" wants a number, and a made-up number is worse than the truth, which
# is that the steps say what to do and not when to do it.
NO_INTERVAL_SAID = ("The steps don't say how often, and I'd rather not make a number up - go by "
                    "when it needs doing again rather than by a calendar.")


# "how often should i run it": the ask is about a doing, and the object is a pronoun, so nothing
# of its own is named. Only the end of the line is read, so "how often should i clean the filter"
# is not this shape.
# The particle after the pronoun is part of the doing, not a thing of its own: "how often should i
# top it up" and "how often should i clean it out" name nothing the answer has to be read for, and
# the pronoun is not the last word. Without this the line was left to the caller, which handed back
# the first step of the answer in hand - "how often should i top it up" after the boiler was
# answered "Top the pressure up to between 1 and 1.5 bar using the filling loop", a how-much for a
# how-often. Only a short particle is allowed, so a line that names a thing after the pronoun
# ("how often should i clean it with vinegar") is still left to the caller.
A_HOW_OFTEN_THE_DOING = re.compile(
    r"\b(?:how often|how many times|how regularly|how frequently)\b"
    r".*\b(?:it|that|this|them|those)"
    r"(?:\s+(?:up|out|down|off|in|on|round|around|over|through|away|back|again|properly|too))?"
    r"\s*[?.!]*\s*$", re.IGNORECASE)


def _how_often(sentences, question, whole):
    """The clause of the answer that says how often, when the line asks that.

    "i started going to the gym" is answered with the movements and then "two or three sessions
    a week", and "how often should i go" wants that clause. The clause has to be about the same
    thing the line asks about: "how often should i mow it" after a lawn answer that only says
    how often to water is left to the caller rather than answered with the watering.
    """
    if not ASKS_FREQUENCY.search(flat(question)):
        return None
    wanted = {word for word in words_of(question)
              if word not in NAMING_IGNORE and word not in FREQUENCY_IGNORE and len(word) > 2}
    # A line that names nothing of its own ("and how often" after the feeding answer) is asking
    # how often the thing on the table is done, so a rate in the answer ("two measured meals a
    # day") is the answer even though it is not written "once a week". A rate is only the answer
    # when it is a schedule, though: a limit ("should never go more than a day without eating")
    # or a portion ("about 3 or 4 x 85g pouches") says how much, not how often, so a real
    # frequency is preferred and a limit or a measured amount is passed over while another
    # candidate is left.
    # A count of how many times is not a rate on its own: "tip it out and boil fresh water twice"
    # is part of how to descale, not how often to do it, and it was read as the rate because
    # "twice" is a rate word elsewhere ("twice a week"). Such a clause is kept only as the last
    # resort, so a sentence that does say how often is preferred to it.
    rates = []
    counted = None
    for sentence in sentences:
        about = bool(wanted) and _names_one_of(wanted, words_of(sentence))
        clause = _freq_clause(sentence, weak=about or not wanted,
                              wanted=wanted if about else frozenset())
        if not clause:
            continue
        if wanted and not about:
            continue
        said = tidy(clause)
        if not said or flat(said) == whole:
            continue
        if FREQUENCY.search(flat(said)) and not _only_a_count(said):
            return said  # "twice a year", "every other morning": the answer itself
        if _only_a_count(said):
            counted = counted or said
            continue
        rates.append(said)
    for said in rates:
        if _only_a_count(said):
            counted = counted or said
            continue
        if not (FREQ_LIMIT.search(said) or FREQ_PORTION.search(said)):
            return said
    if counted:
        return counted
    if rates:
        # A limit or a portion, when the answer has nothing better: it still says something
        # about the thing asked about, and the honest line below is only for an answer with no
        # figure at all.
        return rates[0]
    # No rate anywhere in the answer, but a sentence that says when to do it again: "rinse twice
    # afterwards, and do it again whenever it furs up" answers how often as well as a number does.
    for sentence in sentences:
        if TRIGGER.search(sentence) and re.search(r"\bagain\b", sentence, re.I):
            said = tidy(sentence)
            if said and flat(said) != whole:
                return said
    # Nothing in the answer says how often, and the line asked nothing else: say so rather than
    # hand back a step that reads like an answer to the wrong question. Only for an answer that
    # really is a set of steps, though: "i think im having a panic attack / and how often" is a
    # person asking about something that happens to them, and "The steps don't say how often" is
    # a machine talking to itself. Anything else is left to the caller, as it was before.
    # A follow-up that asks how often the doing in hand is done - "how often should i run it"
    # after the service wash - is the same ask as "and how often": the object is a pronoun, so
    # the line names no thing of its own, and the verb it does name is the answer's own doing. It
    # used to be left to the caller, which answered a question about a service wash with how to
    # sort a wash by colour. Where the answer says no rate in it, the honest line is the same one
    # the bare ask gets; a line that names a thing of its own ("how often should i clean the
    # filter") is still left to the caller.
    # The doing has to be what the answer opens on doing: a cast iron pan is seasoned in its second
    # instruction, so "how often should i season it" is not the pan's own opening ask and its
    # reader keeps the turn it always had.
    opening = sentences[0].strip() if sentences else ""
    first_word = opening.split()[0].strip(",.;:").lower() if opening.split() else ""
    the_doing = bool(A_HOW_OFTEN_THE_DOING.search(flat(question)) and wanted and first_word
                     and _names_one_of(wanted, [first_word]))
    if ((ONLY_THE_INTERVAL_ASK.match(question) or the_doing)
            and not RATE_INTERVAL.search(whole) and A_SET_OF_STEPS.search(whole)):
        return NO_INTERVAL_SAID
    return rates[0] if rates else None


# A rate that is really a limit or an amount: "never more than a day without eating", "no more
# than twice a week", "about 3 or 4 x 85g pouches a day". Asked how often, these say how much or
# how long between, not how often to do it.
FREQ_LIMIT = re.compile(r"\b(?:never|no more than|not more than|at most|at least|less than|"
                        r"more than|up to|until|before)\b", re.I)
FREQ_PORTION = re.compile(r"\d+\s*(?:g|kg|ml|cl|l|oz)\b|\b(?:pouches?|grams?|tins?|cans?|"
                          r"packets?|litres?|liters?|sachets?)\b", re.I)


def _counts_on_the_answer(piece):
    """Whether the clause counts something the answer already said rather than naming its rate."""
    return bool(re.search(r"\b(?:the same|same count|that count|as above|as before)\b", piece, re.I))


def _freq_clause(sentence, weak=False, wanted=frozenset()):
    """The clause of one sentence that carries the frequency, or None."""
    pieces = [piece.strip(" ,;:") for piece in FREQ_CLAUSE.split(sentence) if piece.strip(" ,;:")]
    found = [piece for piece in pieces
             if FREQUENCY.search(piece) or (weak and RATE_FREQ.search(piece))]
    if not found:
        return None
    if len(sentence.split()) <= 30:
        # A sentence short enough to say back whole is said whole. Cutting is how one instruction
        # is found in a long entry, not a way of shortening a sentence that is already one: on a
        # snake plant the clause after the comma ("and only when the compost is dry all the way
        # down") is the rest of how often in winter, and cutting there left the person with the
        # summer and winter rates but not the rule that says when to follow them.
        return sentence
    if wanted:
        # The sentence naming the thing is not enough: "how often do i feed it" about a lawn is
        # answered by a sentence that does say "feeding", and the only frequency in it is the
        # watering's ("a deep soak once a week in dry weather"), so the reply told them how often
        # to water when they asked how often to feed. The clause that is said back has to name the
        # thing asked about too; when no clause does, the caller says the whole answer instead.
        found = [piece for piece in found if _names_one_of(wanted, words_of(piece))]
        if not found:
            return None
    # A clause that counts something said earlier in the answer paints no picture on its own:
    # "pillowcases twice a week on the same count" counts nothing when the count is not in the
    # line, and the earlier rate - the one the count refers to - is the answer.
    plain = [piece for piece in found if not _counts_on_the_answer(piece)] or found
    # "for the first fortnight, then once a day" names two, and the first is the one said first:
    # a rate that opens on a joiner is the continuation of the clause before it, not a new one.
    piece = plain[0]
    if len(plain) > 1 and re.match(r"(?:then|and|also|plus|after that|afterwards)\b", piece, re.I):
        piece = plain[1]
    if len(piece.split()) <= 3 and len(found) > 1:
        piece = " ".join(found[-2:])
    if len(piece.split()) > 14:
        # Too long to say back whole: keep the part of it that names the frequency, and the part
        # before it when that is what the frequency is attached to ("water when the compost is
        # dry, not on a fixed day").
        parts = [part.strip(" ,;:") for part in re.split(r",\s*", piece) if part.strip(" ,;:")]
        at = [index for index, part in enumerate(parts) if FREQUENCY.search(part)]
        if at:
            last = at[-1]
            piece = parts[last]
            if len(piece.split()) <= 5 and last:
                piece = parts[last - 1] + ", " + piece
    return piece if len(piece.split()) >= 2 else None

def _dated(sentences, question, whole):
    """The sentence of the answer that says when, picking between dates by the words used.

    After an answer that holds both 43 AD and 410 AD, "when did they leave" is about the
    second one, and the word the question uses ("leave") is the word that sentence uses.
    """
    wanted = set(words_of(question))
    for word in list(wanted):
        wanted.update(SAME.get(word, ()))
    best, best_score = None, (-1, -1)
    for sentence in sentences:
        if not has_a_date(sentence):
            continue
        score = (1 if DATED_STRONG.search(sentence) else 0,
                 len(wanted.intersection(words_of(sentence))))
        if score > best_score:
            best, best_score = sentence, score
    if best is None or flat(best) == whole:
        return None
    return tidy(best)


# A line that asks for a hand with a thing it names ("any tips for the first thirty seconds?",
# "any advice for the shaky voice") is a question about that part of the answer, and the part is
# the sentence that names the same thing. Without the ask, two words in common is a coincidence;
# with it, the person has named the part of the answer they want more of.
ASKS_FOR_A_HAND = re.compile(r"\b(?:tips?|tricks?|hacks?|advice|pointers?|suggestions?|ideas?)\b", re.I)
# Two words in common is naming a part; one is a coincidence ("the", "and", a shared verb).
NAMES_A_PART = 2


def _the_part_they_named(sentences, question, whole):
    """The sentence of the answer about the thing this advice ask names, or None."""
    if not ASKS_FOR_A_HAND.search(flat(question)):
        return None
    sentence = _by_words(sentences, question)
    if not sentence:
        return None
    shared = set(words_of(question)) & set(words_of(sentence))
    if len(shared) < NAMES_A_PART:
        return None
    said = tidy(sentence)
    if said and flat(said) != whole:
        return said
    return None


def _not_a_figure(sentences, question, whole, reply=None):
    """The sentence that answers a step or a property question, when it is not a figure.

    A yes/no about one step ("do I need to parboil them first?") is answered by the sentence
    that starts with that step. A question about a property ("how do I get them crisp?") is
    answered by the sentence that says the same thing in other words ("...they go crunchy").
    Both return None when no sentence speaks to the line, so the caller passes instead of
    repeating the whole answer.

    `reply` is the answer before the caller kept only the sentences that name the thing asked
    about, because a script quoted in the answer can be split across two of the original
    sentences (see `_with_the_script`).
    """
    option = _by_option(sentences, question)
    if option and flat(option) != whole:
        return _with_the_script(option, sentences, reply) or tidy(option)
    step = _by_step(sentences, question)
    if step and flat(step) != whole:
        return _with_the_script(step, sentences, reply) or tidy(step)
    if _property_ask(question):
        sentence = _by_words(sentences, question)
        if sentence and flat(sentence) != whole:
            return tidy(sentence)
    return None


def _named_clause(answer, question):
    """The clause of the answer about a thing the line names, or None.

    Only a thing that the answer says in exactly one clause counts: the loaf tin is named in
    one, so the question about it has one place to look. A word that runs through every clause
    ("the oven" in an oven method) names no one part, and is left to the readers below.

    Two words that belong together name that thing and nothing else: a bundt tin is not the
    loaf tin the answer talks about, however many tins both of them mention.
    """
    # The words are read the way the answer's words are (words_of): "the meters" and "the shoes"
    # name meter and shoe, and a plural as typed never matched the singular the answer files.
    named = [word for word in words_of(question)
             if word not in NAMING_IGNORE and len(word) > 2]
    if not named:
        return None
    pairs = [(named[i], named[i + 1]) for i in range(len(named) - 1)]
    pieces = [piece.strip() for piece in
              pieces_of(" ".join(str(answer or "").split()),
                        r";\s*|(?<=[.!?])\s+|,\s+(?:and|but|so)\s+|\s+(?:and|but|so)\s+")
              if piece.strip()]
    roots = {_root(word) for word in named}
    pieces = clauses(" ".join(str(answer or "").split()), NAMED_BREAK)
    best, best_score, best_count = None, 0, 0
    for piece in pieces:
        said = flat(piece)
        score = len([pair for pair in pairs if _says(said, " ".join(pair))]) if pairs else 0
        if not score:
            # The same word said another way: "is it worth cleaning the filter" names the
            # clause that says "clean the filter", and a question about the drum is about what
            # the answer calls "the seal". Plural and verb endings are the two ways the same
            # thing turns up spelled differently, so the roots are what is compared.
            score = len({_root(word) for word in words_of(piece)}.intersection(roots))
        if score > best_score:
            best, best_score, best_count = piece, score, 1
        elif score == best_score and score:
            best_count += 1
    if not best or best_count != 1:
        return None
    # Every thing the line names has to be spoken of by the answer. One shared verb is not
    # enough: "is it worth cleaning the oven" shares "clean" with the advice to clean the
    # filter, and the oven is not in that answer at all.
    if not roots <= {_root(word) for word in words_of(answer)}:
        return None
    return best.rstrip(".!?,;: ")


def _root(word):
    """The stem a word shares with its other endings ("cleaning", "cleaned" -> "clean")."""
    for ending in ("ing", "ed", "es", "s"):
        if len(word) > len(ending) + 2 and word.endswith(ending):
            word = word[:-len(ending)]
            break
    return word[:-1] if len(word) > 3 and word.endswith("e") else word


def _says(text, phrase):
    """Whether `text` says `phrase`, plurals included ("loaf tin" in "loaf tins")."""
    pattern = r"\b" + r"[a-z]*\s+".join(re.escape(word) for word in phrase.split()) + r"[a-z]*\b"
    return re.search(pattern, flat(text)) is not None


def _informative(piece):
    """Whether this clause answers on its own: a figure in it, or a step to take."""
    return bool(re.search(r"\d", piece) or COOKS.search(piece) or WAIT.search(piece))


def _cuts_a_list(piece, answer):
    """Whether this clause is one item of a list the answer carries on with.

    "For a warm week: light cotton tops" is the first item of "light cotton tops and shorts, one
    long-sleeved layer and a light waterproof ... shoes you can walk in", and said alone it reads
    like an answer that stopped halfway. A clause the comma or the "and" in front of it belongs
    to is not a piece of its own, so the sentence that holds it is the answer.
    """
    said = " ".join(str(piece or "").split())
    whole = " ".join(str(answer or "").split())
    if not said or said not in whole:
        return False
    rest = whole[whole.index(said) + len(said):]
    return bool(re.match(r"\s*(?:[,;]|\band\b)", rest))


def _with_unit(piece, reply):
    """A clause that ends on a bare range gets the unit the answer used before it.

    "A loaf tin needs 45 to 55" is right in the middle of the answer and thin on its own; the
    minutes are a word earlier, so they come along.
    """
    text = piece.strip()
    if not BARE_RANGE.search(text) or UNIT.search(text[-12:]):
        return text
    before = flat(reply)
    at = before.find(flat(text))
    units = list(UNIT.finditer(before if at < 0 else before[:at]))
    if not units:
        return text
    return text + " " + units[-1].group(0)


def _property_ask(question):
    """Whether the line asks how the thing turns out, in words the answer may say differently.

    Only a "how do I get it crisp?" shape counts. A statement that happens to hold one of
    those words ("a big project slipped") is not a question about the answer. "Saving" is a
    cheapness word only as a property of the thing ("how do I get it for less"); the person's
    own saving ("how do I start saving money", "how do I save up for a car") is a plan they
    are asking about, not a part of the answer we just gave.
    """
    if not re.search(r"\bhow (?:do|can|should|would|could) (?:i|we|you)\b", flat(question)):
        return False
    if OWN_SAVING.search(flat(question)):
        return False
    return any(word in SAME for word in words_of(question))


# The person's own saving, which is a subject of theirs and not a word for cheap: a line that
# says "start saving" or "save up for" is not a follow-up about how something turned out.
OWN_SAVING = re.compile(r"\b(?:start|begin|keep|stop|try|need|want)\s+(?:to\s+)?sav(?:e|ing)\b"
                        r"|\bsav(?:e|ing)\s+(?:up\b|money\b|for\b)", re.I)


def _option_ask(question):
    """Whether the line is an elliptical ask about one named option ("and for a hard one?")."""
    clean = flat(question)
    return bool(OPTION.search(clean) and QUALIFIER.search(clean) and not NOT_OPTION.search(clean)
                and len(words_of(clean)) <= 8)


def _stands_alone(piece):
    """Whether a clause cut out of an answer is an answer on its own, not half a sentence.

    A qualifier word can sit in a fragment: "A hard" out of "A hard, fixed lump under the skin
    is worth showing to a GP", "Gas." out of a sentence about magma. Said alone the fragment is
    not a reply, but the sentence it was cut from says the same thing with what to do about it,
    so that sentence is the answer. A figure stands on its own ("200C."), and so does any
    clause of two content words ("Under the skin", "Not the top").
    """
    text = str(piece or "").strip()
    if not text:
        return False
    if re.search(r"\d", text):
        return True
    return len(words_of(text)) >= 2


def _by_option(sentences, question):
    """The clause of the sentence that names the option the line asks about."""
    qualifier = QUALIFIER.search(question)
    if not qualifier:
        return None
    for sentence in sentences:
        clause = _clause_with(sentence, qualifier.group(0))
        if clause and flat(clause) != flat(sentence):
            # "A thick" naming the option is half of "A thick, yellow or crumbly nail is a fungal
            # infection: ...": said alone it is not an answer, so the sentence it came from is.
            if _only_a_qualifier(clause):
                # ...and a clause of nothing but the qualifier is the condition the sentence is
                # about, not an option named: "Too thin or runny, simmer it uncovered to reduce
                # it" cut at the comma says too thin or what, and the instruction is the answer.
                return sentence
            return clause if _stands_alone(clause) else sentence
    return None


def _only_a_qualifier(clause):
    """Whether a clause cut out of an answer names nothing but the qualifier the line asked for."""
    words = [word for word in words_of(clause) if word not in QUALIFIER_FILLER]
    return bool(words) and all(word in QUALIFIER_WORDS for word in words)


# A step that tells them to say something is not whole without the words: "Say it once, about
# the pattern rather than the last time: \"We've cancelled three times now... Can we pick a night
# we'll both keep?\"" cut at the comma is "Say it once.", the verdict with the script dropped, and
# the script is the one part of that answer a person cannot write for themselves. Asked "should i
# say something" after the cancelling answer, that was the whole reply. Only a *bare* verdict is
# this short: "Say the good news once and let theirs be theirs" is an instruction a person can act
# on already, so it keeps its cut and the reason after the colon stays off. A step about a doing
# ("Turn the boiler off: the pump...") keeps its cut too, because what follows is why.
SAYS_SOMETHING = re.compile(r"^(?:and |then |so )?(?:say|tell|ask|text|message|write|word|phrase"
                            r"|reply|mention|bring|raise|broach)\b", re.I)
# A verdict on its own: "Say it once", "Tell her" - past this length the head is the instruction.
BAREST_VERDICT = 24


def _by_step(sentences, question):
    """The clause that starts with the step a yes/no question names, or None."""
    if not YES_NO.search(flat(question)):
        return None
    wanted = set(words_of(question))
    # The step is the verb the question names, when it names one: a sentence is the answer to
    # "should I have a go" only if it starts with "have", not if it starts with any word the
    # line happens to share ("worth" in "is it worth paying a plumber").
    step = step_word(question)
    if step:
        wanted = {step} | set(SAME.get(step, ()))
    for sentence in sentences:
        # The sentence must *start* with the step, not merely have it as its first content
        # word: "It takes ten minutes" does not start with "take".
        raw = WORD.findall(flat(sentence))
        if not raw:
            continue
        first = raw[0]
        if len(first) > 3 and first.endswith("s") and not first.endswith("ss"):
            first = first[:-1]
        if first in wanted:
            cut = re.split(r"[:,]\s+", sentence.strip())[0].strip() or sentence
            return cut if _stands_alone(cut) else sentence.strip()
    return None


def _with_the_script(part, sentences, reply=None):
    """A bare verdict on the saying, with the words the person would use, and nothing else.

    The readers above cut a sentence at its comma or its colon, which is right for a step whose
    tail is the reason it works ("Turn the boiler off: the pump..."). It is wrong for a verdict
    on the saying, because the tail there is a script quoted in the answer, and a person cannot
    write that themselves: asked "should i say something" after the cancelling answer, the turn
    was "Say it once." on its own.

    What is handed back is the verdict *and the quotation*, not the whole sentence: the rest of
    that sentence is why the script works, which the previous turn already said, and a reply that
    reads the last answer out again is passed over as a repeat. So a sentence with no quotation
    in it returns nothing here and keeps its plain cut. Only a *bare* verdict is treated this
    way: "Say the good news once and let theirs be theirs" is an instruction a person can act on
    already, and keeps its cut too.
    """
    head = str(part or "").strip().strip(".?! ")
    said = flat(head)
    if not said or len(said) > BAREST_VERDICT or " " not in said:
        return None
    if not SAYS_SOMETHING.match(said):
        return None
    # The answer's own sentences, not the ones the caller kept: the head of a script and its
    # ending can share a word with the line and its close with nothing at all, so the list the
    # caller filtered on often holds the first half only.
    whole_answer = [one.strip() for one in SENTENCE.split(str(reply or "").strip()) if one.strip()]
    if not whole_answer:
        whole_answer = sentences
    for at, sentence in enumerate(whole_answer):
        if flat(sentence).startswith(said):
            words = _the_quotation(_to_the_end_of_the_script(whole_answer, at))
            if not words:
                return None
            return '%s, like this: %s' % (head, words)
    return None


# The script in an answer, quotation marks and all: the words the person would say, which is the
# one part of that answer they cannot write for themselves. Both marks are read, because an answer
# that has a contraction in the script quotes it with one kind and an answer without with the other.
QUOTED_WORDS = re.compile(r'"[^"]{10,}"')
QUOTED_WORDS_SINGLE = re.compile(r"(?::\s|,\s)'(.{10,}?[.?!])'(?=\s|$)")


def _the_quotation(sentence):
    """The words quoted in the sentence, marks and all, when it quotes any."""
    text = str(sentence or "")
    found = QUOTED_WORDS.search(text)
    if found:
        return found.group(0).strip()
    found = QUOTED_WORDS_SINGLE.search(text)
    if found:
        return "'%s'" % found.group(1).strip()
    return None


def _to_the_end_of_the_script(sentences, at):
    """The sentence, plus what the splitter took for the next one when it broke inside a quote.

    The answer's script is a quotation, and a full stop inside it ends a sentence for the
    splitter: handed back on its own, "Say it once, about the pattern rather than the last time:
    \"We've cancelled three times now and honestly it's starting to feel like I'm an afterthought"
    is the words cut off in the middle, which is worse than the verdict alone. So the quote is
    counted and the following sentences are added until it closes.
    """
    text = sentences[at].strip()
    index = at
    while index + 1 < len(sentences) and text.count('"') % 2:
        index += 1
        text = text + " " + sentences[index].strip()
    return text


def _by_words(sentences, question):
    """The sentence that shares the most words with the question, when it shares any."""
    wanted = set(words_of(question))
    for word in list(wanted):
        wanted.update(SAME.get(word, ()))
    if not wanted:
        return None
    best, best_score, best_length = None, 0, 0
    for sentence in sentences:
        score = len(wanted.intersection(words_of(sentence)))
        length = len(words_of(sentence))
        if score and (score > best_score or (score == best_score and length < best_length)):
            best, best_score, best_length = sentence, score, length
    return best


# A duration written as an adjective ("a 20-minute job", "a 5-day trip") answers a how-long
# question as the plain length of time: "20 minutes", not "20-minute".
DURATION_ADJECTIVE = re.compile(r"\b(\d+(?:\.\d+)?)\s*[-–]\s*"
                                r"(minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)\b",
                                re.I)


def _as_a_length(text):
    """`a 20-minute job` read as `20 minutes`: the answer to how long is the time itself."""
    def say(match):
        number, unit = match.group(1), match.group(2).lower()
        if number not in ("1", "1.0") and not unit.endswith("s"):
            unit += "s"
        return number + " " + unit
    return DURATION_ADJECTIVE.sub(say, str(text))


# Words that point at what is already on the table rather than naming anything: "how long
# until i can do the whole thing", "how long until it is done". They are the question's own
# grammar, the way "how" and "long" are, so a sentence is not about the line just because it
# happens to say one of them - the training answer said "until you can run 20 minutes", and
# "how long until i can do the whole thing" was handed that sentence's "20 minutes" instead of
# the "eight weeks" the plan is measured in.
POINTS_BACK = frozenset("until till til whole thing things".split())


def _names_a_thing(question):
    """Whether the line names something of its own beyond the property it asks for."""
    return any(word not in ASKING_ONLY and word not in POINTS_BACK
               for word in words_of(flat(question)))


# A follow-up that carries on from the answer rather than being a bare ask of its own: "and how
# long?", "so how long?", "what about the time?". A line with no join in it ("how long") is not
# enough on its own to cut an answer up: nobody shouts "how long" at a friend and means "cut the
# last paragraph down to one figure".
CARRIES_ON = re.compile(
    r"^\s*(?:and|so|also|then|but|ok|okay|right|plus|same|also|what about|how about|what of)\b",
    re.I)

# Two figures the answer gives the same thing in different states or places - "it keeps 4 days in
# the fridge or 3 months frozen". Cutting to the first drops the half that keeps the food safe.
EITHER_OR = re.compile(r"\d[^.;]{0,40}\bor\b[^.;]{0,40}\d", re.I)
# The measure a figure is in ("180C" is degrees, "450 words" is a count), so two figures of the
# same kind can be told apart from one figure said in two scales.
FIGURE_MEASURE = re.compile(r"\d+(?:\.\d+)?\s*(?:to\s*\d+(?:\.\d+)?\s*)?[-\u2013]?\s*([a-z%]+)",
                            re.I)


def _measure(span):
    """The unit a figure is given in, or "" when it names none."""
    found = FIGURE_MEASURE.search(str(span or ""))
    return found.group(1).lower() if found else ""


def _figure(match, text):
    """The whole figure a span found, thousands separator and all.

    The span patterns read a figure by its unit ("475 km", "500C"), and a number written with
    thousands separators starts a new word at every comma, so 3,475 km was read as 475 km and
    5,500C as 500C. Asked again, the answer came back as the wrong figure by a factor of seven:
    `how far is the moon from earth`, after the moon's size was answered, gave "400 km." from
    "384,400 km", and "how many miles is that" after a tyre's life gave "000 miles." from
    "20,000 to 40,000 miles". The span is widened back over the digits and commas in front of it
    here, rather than in every pattern, so a figure comes out whole whatever its unit.
    """
    text = str(text or "")
    start = match.start()
    left = start
    while left > 0 and (text[left - 1].isdigit() or text[left - 1] in ",."):
        left -= 1
    if left == start:
        return match.group(0)
    return text[left:match.end()].lstrip(".,")


def _a_figure_each(sentence, kind):
    """The halves of a sentence that each state a figure for a thing, or None.

    One sentence can hold two answers: "Green tea wants water at about 80C for 2 to 3 minutes;
    black tea wants it just off the boil for 3 to 5." Each half names a thing and gives the
    figure that belongs to it, so the first figure on its own is not the answer - it is the time
    for the first of the two with nothing saying which. Only a semicolon joins two answers like
    that, and only when both halves carry a figure; a sentence of one answer that happens to use
    a semicolon is left to the clause reader as before.
    """
    figure = SPANS.get(kind)
    if not figure or ";" not in str(sentence or ""):
        return None
    halves = [one.strip() for one in sentence.split(";") if one.strip()]
    if len(halves) < 2:
        return None
    # The second half of a pair like "2 to 3 minutes; black tea ... 3 to 5" gives its figure
    # without the unit, which the first half already said, so a bare range counts as the figure
    # when one of the halves states the unit.
    stated = any(figure.search(one) for one in halves)
    if not stated:
        return None
    if any(not (figure.search(one) or BARE_RANGE.search(one.rstrip(".!?"))) for one in halves):
        return None
    return halves


# One sentence often gives a figure for each thing in a list: "15 to 20 minutes for a chicken or
# a turkey, 10 to 20 for a joint of beef, 5 to 10 for a steak or chops, and 20 to 30 for a
# brisket". A line that names one of the things is asking about that one, and the sentence read
# whole is the answer to a question nobody asked: "how long should i rest a steak" got the whole
# paragraph, and the figure it wanted was "5 to 10". The unit is stated once, at the top of the
# list, so an item that has only a figure takes the unit from the item that has it.
A_UNIT_WORD = re.compile(r"\b(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|months?"
                         r"|years?)\b")
# The second item of a list states its figure without the unit the first one gave: "15 to 20
# minutes for a chicken, 10 to 20 for a joint of beef". A bare range is the start of an item.
A_BARE_RANGE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:-|to|or|and|\u2013)\s*\d+(?:\.\d+)?\b")
# What the figure of a list item is for: "5 to 10 for a steak or chops". The unit may come
# between the figure and the "for", because the list states it once, at the top.
A_FOR_A_THING = re.compile(r"\s*(?:seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?"
                           r"|months?|years?)?\s*for\b", re.I)


def _the_item_they_named(sentence, kind, question):
    """The item of a one-figure-per-thing list that the line names, or None.

    Each item runs from one figure to the next, so the list is cut at its figures rather than at
    its commas: in "10 to 20 for a joint of beef, lamb or pork, 5 to 10 for a steak" the "lamb or
    pork" belongs to the beef, and cutting at a comma would leave it with no figure and drop it.
    Only a list of two or more items is read this way, and only when the line names one of them
    and no other: a bare "and how long" matches none of them and is left to the readers below,
    which is what it said before.
    """
    figure = SPANS.get(kind)
    if not figure:
        return None
    said = set(words_of(flat(question)))
    if not said:
        return None
    # A sentence that opens with what the list is for ("Loosely under foil and off the heat, not
    # back in the oven: 15 to 20 minutes for a chicken ...") says it before the colon.
    body = sentence.split(":", 1)[1] if ":" in sentence else sentence
    starts = re.compile(figure.pattern + "|" + A_BARE_RANGE.pattern, re.I)
    found = [match for match in starts.finditer(body)
             if not _a_frequency(body, match.end())]
    if len(found) < 2:
        return None
    items = []
    for index, match in enumerate(found):
        stop = found[index + 1].start() if index + 1 < len(found) else len(body)
        items.append((match.group(0), body[match.start():stop]))
    if any(not A_FOR_A_THING.match(piece, len(span)) for span, piece in items):
        # Every item of such a list says what its figure is for: "15 to 20 minutes for a chicken",
        # "10 to 20 for a joint of beef". A sentence with several figures that do not read that
        # way is arithmetic or a method ("20 minutes per 500g plus 20 minutes at 190C, so a 3kg
        # bird takes 1 hour 40"), and one of its figures said alone is not the answer to anything.
        return None
    scored = [(len(said & set(words_of(piece))), piece) for _, piece in items]
    best = max(score for score, _ in scored)
    winners = [piece for score, piece in scored if score == best]
    if best == 0 or len(winners) != 1:
        return None
    item = re.sub(r"[\s,]*(?:and|or)?[\s,]*$", "", winners[0].strip())
    if not A_UNIT_WORD.search(item):
        # The unit is stated once, at the top of the list: the item that has only a figure takes
        # it from the item that has the unit, or the answer is a bare number.
        unit = next((A_UNIT_WORD.search(one) for _, one in items if A_UNIT_WORD.search(one)), None)
        if not unit:
            return None
        # The unit goes after the figure, not at the end of the item: "10 to 20 minutes for a
        # joint of beef, lamb or pork", never "... lamb or pork minutes".
        head = A_BARE_RANGE.search(item)
        split = head.end() if head else len(item)
        item = item[:split] + " " + unit.group(0).lower() + item[split:]
    return item


def _the_half_they_named(halves, question):
    """The half of a two-answer sentence the line names, or None when it names neither.

    "how long for black tea" names the black tea half and not the green one, so the words the
    line shares with each half decide it. A line that names both halves equally ("and how
    long") gets None, because then both figures are the answer and neither works alone.
    """
    said = set(words_of(flat(question)))
    if not said:
        return None
    scored = [(len(said & set(words_of(one))), one) for one in halves]
    best = max(score for score, _ in scored)
    winners = [one for score, one in scored if score == best]
    if best == 0 or len(winners) != 1:
        return None
    return winners[0]


# A figure that says how long a *state* lasts is not how long the job takes: "a child who can
# balance for five seconds can ride" answers when they can ride, and "twenty minutes at a time
# beats an afternoon" is how long one go lasts. Asked "how long does it take" after the cycling
# answer, this module cut the five seconds out of the relative clause and the person got "Five
# seconds." - a confident figure about something else. The same shape gave "Ten minutes." for
# getting fit (the warm-up) and the session length for a guitar practice ask.
IN_A_RELATIVE = re.compile(r"\b(?:who|which|whose)\b", re.I)
# "on a dry day with no rain forecast for 24 hours" is how long the weather has to hold, not how
# long the job takes: that figure is a window the forecast has to stay inside. With the treatment
# interval passed over, the 24 hours became the answer to "how long will it take" to paint a shed.
A_WEATHER_WINDOW = re.compile(
    r"\b(?:forecast|rain|showers?|dry|damp|frost|wind|sunshine?|weather|mild|warm|cold)\b"
    r"[^.;:,]{0,25}\bfor\s+$", re.I)
AT_A_TIME = re.compile(r"^\s*(?:at a time|to warm up|to cool|of it)\b", re.I)
# A bounded figure inside an "if" or "when" clause is a threshold, not how long the job takes:
# "getting out of bed if you're awake for more than 20 minutes" is a rule, and handed back for
# "how long will it take" it was "20 minutes." - a figure about a rule, not a length. A plain
# figure in the same clause stays ("if the room is cold, give it 40 minutes"), because that
# is still how long the job takes in that case.
IN_A_CONDITION = re.compile(r"\b(?:if|unless|when|whenever|once)\b", re.I)
A_BOUNDED = re.compile(r"\b(?:more than|less than|at least|at most|up to|within|over|under"
                       r"|no more than|not more than)\s+$", re.I)
# "It has gone on for weeks" is how long a state has lasted, not how long the job takes.
A_STATE_FOR = re.compile(r"\b(?:gone on|been|lasted|going on|had (?:it|this|that))\b"
                         r"[^.;:]{0,30}\bfor\s+$", re.I)
# "Screens off half an hour before bed" is a clock offset, not the length of anything: the
# "before" names the event the half hour is measured from. A clause after it is not an offset:
# "give it six weeks before you judge it" is still how long the job takes, and so is "20 minutes
# before serving" (a gerund names an action, not a point in the day).
A_RELATIVE_AFTER = re.compile(
    r"^\s*(?:before|after)\s+(?!you\b|i\b|we\b|they\b|it\b|he\b|she\b|\w+ing\b)\w", re.I)


def _a_condition(sentence, match):
    """True when the figure counts something other than the length of the whole job."""
    if AT_A_TIME.match(sentence[match.end():]):
        return True
    if A_RELATIVE_AFTER.match(sentence[match.end():]):
        return True
    before = sentence[:match.start()]
    if IN_A_CONDITION.search(before) and A_BOUNDED.search(before):
        return True
    if A_STATE_FOR.search(before):
        return True
    if A_WEATHER_WINDOW.search(before):
        return True
    return bool(IN_A_RELATIVE.search(before))


def _part(sentence, kind, question):
    """The tightest safe answer inside one sentence."""
    # A kind with no span pattern of its own ("order": before, after, first) is read from the
    # clause that names it, not from a figure: SPANS holds the figures only, and asking it for
    # one it does not have used to take the turn down with it.
    figure = SPANS.get(kind)
    qualifier = QUALIFIER.search(question)
    if qualifier:
        clause = _clause_with(sentence, qualifier.group(0))
        if clause:
            found = [_figure(match, clause) for match in figure.finditer(clause)] if figure else []
            if found:
                return found[-1]
            if re.search(r"\d", clause):
                return clause
    spans = [_figure(match, sentence) for match in figure.finditer(sentence)] if figure else []
    if kind == "time" and spans and LENGTH_OF_THE_JOB.search(flat(question)):
        lengths = [_figure(match, sentence) for match in figure.finditer(sentence)
                   if not _a_frequency(sentence, match.end(), match.start())
                   and not (A_MOMENT.fullmatch(match.group(0).strip())
                            and not A_COUNTDOWN.search(flat(question)))
                   and not _a_condition(sentence, match)]
        if not lengths:
            # Every figure in the sentence is a rate ("Twenty minutes a day beats one long
            # session a week"), so this sentence has nothing to say about how long the job
            # takes. The next sentence of the answer may: "Most people can strum through a
            # simple song in two or three months" is the length, and giving up here handed the
            # whole first sentence back as the answer instead.
            return NO_LENGTH
        # A rate that opens the sentence is not part of a whole-job answer: "With 15-20 minutes
        # a day, a simple tune is usually a few months" answers "how long does that take" with
        # everything after the comma, and the opening clause went to answers' fallback as "With
        # 15-20 minutes a day." - a rate handed back for a length ask.
        lead = RATE_LEAD.match(sentence)
        if lead and figure.search(lead.group(0)):
            cut = sentence[lead.end():].strip()
            if cut and figure.search(cut):
                sentence = cut
                lengths = [_figure(match, sentence) for match in figure.finditer(sentence)
                           if not _a_frequency(sentence, match.end(), match.start())]
        spans = lengths
    if kind == "time" and spans and not LENGTH_OF_THE_JOB.search(flat(question)):
        # A rate ask ("how long should i practise") wants the rate, and now that a spelled-out
        # months figure is a span too, one sentence can hold both. Where it does, the rate is
        # the answer to this question: "Twenty minutes a day gets you a simple song in two or
        # three months" must not hand back the months to it. A sentence with no length in it
        # ("Walk 30 minutes a day, 5 days a week") is left as it was, because the clause reads
        # better than the bare figure.
        rates = [_figure(match, sentence) for match in figure.finditer(sentence)
                 if _a_frequency(sentence, match.end(), match.start())]
        lengths = [_figure(match, sentence) for match in figure.finditer(sentence)
                   if not _a_frequency(sentence, match.end(), match.start())]
        if rates and lengths:
            return rates[0]
    if not spans:
        # "Two or three weeks of doing it the same way ... turns it round" is not an answer to
        # "what time should she go to bed", however well the rest of the sentence fits: a clock
        # ask needs a clock in it.
        if kind == "clock":
            return None
        return sentence if len(sentence.split()) <= 28 else None
    # "how many weeks should i train" names the unit it wants, so the answer's own figure in
    # that unit is the answer even when the sentence has another length beside it ("build up
    # over about sixteen weeks: three runs a week"). Only a single such figure is handed back:
    # two of them are the answer saying which is which, and that sentence is read whole.
    wanted_unit = ASKED_UNIT.search(question or "")
    if kind == "time" and wanted_unit and len(spans) > 1:
        unit = _unit_stem(wanted_unit.group(1))
        same = [span for span in spans if _unit_stem(span.split()[-1]) == unit]
        if len(same) == 1:
            return same[0]
    if kind == "amount":
        return _clause(sentence, question) or sentence
    if kind in ("money", "distance"):
        return spans[0]
    if RATE.search(question):
        wanted = [span for span in spans if re.search(r"\bper\b|\ba\b", span, re.I)]
        if not wanted:
            return None
        # "20 minutes per 500g plus 20 minutes on top: 40 minutes per kilo, so a 2kg bird
        # takes 1 hour 40" is the rate worked into a total. Keep the sentence rather than
        # make the person do the sum from "per 500g".
        if len(spans) > 1 and re.search(r"\b(?:takes|so)\b", sentence, re.I):
            return sentence
        return wanted[0]
    # Several values given "for" different options: "6 minutes for a runny yolk, 7 for jammy,
    # 9 to 10 for hard boiled". Without a qualifier in the question, one of them would be a
    # guess, so hand back nothing and let an honest "which one?" take the turn.
    options = re.findall(r"\b\d+(?:[^,.;:]{0,18}?)\bfor\b", sentence, re.I)
    if len(options) >= 2:
        return None
    if kind == "time" and BEFORE.search(question):
        # "how long before i can play a song" wants the months, not the "twenty minutes a day"
        # that goes with them: the per-day figure answers how much, not how long.
        result = [_figure(match, sentence) for match in RESULT.finditer(sentence)]
        if result:
            return result[-1]
    # An answer that leads with the figure and then details it ("Three minutes, about 450
    # words, is the length to aim for: ... keep that opening 30 seconds short") answers "how
    # long" in that opening clause. A figure further in belongs to one detail of it, and giving
    # that one contradicts the answer the person can still see. A step-by-step timing ("then
    # roast for 40 to 45 minutes") is a different shape and keeps its last figure.
    if len(spans) > 1 and not SEQUENCE.search(sentence):
        lead = re.split(r"[:,;]\s+|\s+-\s+", sentence.strip())[0]
        lead_spans = [match.group(0) for match in SPANS.get(kind, ()).finditer(lead)]
        # A later figure in the same measure is the same answer said twice, not a detail under
        # it: "180C, or 160C in a fan oven" is one temperature in two scales, and handing back
        # the bare "180C" loses the half of it many ovens need.
        rest = [span for span in spans if span not in lead_spans]
        if len(lead_spans) == 1 and any(_measure(span) != _measure(lead_spans[0])
                                        for span in rest):
            return lead_spans[0]
    if len(spans) == 1:
        return spans[0]
    stepped = _step_time(sentence, question, figure)
    if stepped:
        return stepped
    if SEQUENCE.search(sentence) and not WAIT.search(question):
        # A sentence that says "first this, then that" is read as steps before anything else:
        # "parboil 8 minutes, then roast for 40 to 45" asked "and how long?" is the roast, and
        # the first figure in it would be the parboil.
        return spans[-1]
    if (not _names_a_thing(question) and CARRIES_ON.search(question)
            and not re.search(r"\bper\b", spans[0], re.I)
            and not EITHER_OR.search(sentence)):
        # the follow-up asks for the figure again and nothing else: the clause carrying the
        # figure is the answer, so the subject comes with the number - "Raw chicken keeps 1 to 2
        # days.", not "1 to 2 days." for whichever food they happen to have. Not a rate
        # ("20 minutes per 500g" is a figure to work from, and the total later in the sentence is
        # the time asked for), and not a figure given for two states (fridge and freezer), where
        # one alone is half an answer.
        return _clause_holding(sentence, spans[0]) or spans[0]
    # Several times for different sizes or tins: the sentence says which is which, the span
    # alone would pick one and be wrong. Hand back the sentence.
    return _clause(sentence, question) or sentence


def _canonical(word):
    """The step a kitchen word names, so the oven is the oven however the person says it."""
    return "oven" if word in OVEN else word


def _a_frequency(sentence, end, start=None):
    """Whether the time that ends at `end` is how often to do something, not how long it takes.
    "Twenty minutes a day", "5 days a week" and "three times a week" are all rates: asked how
    long the job takes, the figure to hand back is the length in the sentence ("two or three
    months"), and a rate handed back is a wrong answer a person plans around.
    """
    after = sentence[end:]
    if start is not None and FREQUENCY_BEFORE.search(sentence[:start]):
        # "every two or three years" is the interval the thing is done at, said with the interval
        # in front: only the words after the figure were read before, so a treatment's recurrence
        # was handed back as the length of the job.
        return True
    return bool(FREQUENCY_AFTER.match(after) or FREQUENCY_AFTER_TIMES.match(after)
                or FREQUENCY_AFTER_AT_A_TIME.match(after))


def _same_step(asked, words):
    """True when the question and the clause name the same step.

    "parboil" is the "boil" the clause is about: the person's word has the answer's word in it,
    so a prefix or a suffix of at least two letters is the same step ("parboil" is "boil",
    "roasting" is "roast"), and one extra letter is a different word ("rice" is not "price",
    "ice" is not "slice"). Two words for one step count as one word: "bake" and "in the oven"
    are the same step, and so are "roast" and "in the oven", which is how a question about
    baking picks the oven time out of a sentence that also gives the hob time.
    """
    if {_canonical(word) for word in asked} & {_canonical(word) for word in words}:
        return True
    for mine in asked:
        for theirs in words:
            short, long_ = (mine, theirs) if len(mine) <= len(theirs) else (theirs, mine)
            if len(short) >= 4 and len(long_) - len(short) >= 2 and short in long_:
                return True
    return False


def _step_time(sentence, question, figure):
    """The time in the clause about the step the question names, or None.

    "12 minutes on a low simmer, then 10 minutes off the heat" gives the time for cooking and
    the time for standing, and asking how long to cook it must not come back with the standing
    time. The verb the question uses picks the clause. A question that names no step still never
    wants the standing time: what it asked is how long the job takes, and waiting afterwards is
    not the job.
    """
    asked = {word.rstrip("s") for word in words_of(question) if len(word) > 3}
    pieces = []
    for piece in (one.strip() for one in STEP.split(sentence) if one.strip()):
        # "50 months, about 4 years and 2 months" splits at the "and" into a figure and a bare
        # unit: the second half belongs to the same figure, and read as a step of its own it is
        # what answered "how long will that take" with "2 months". A figure in two units is one
        # figure, so the bare unit goes back on the piece before it.
        if pieces and BARE_UNIT.match(piece):
            pieces[-1] = pieces[-1] + " and " + piece
        else:
            pieces.append(piece)
    if not (SEQUENCE.search(sentence) or AFTER.search(sentence)):
        # A sentence that says nothing about a sequence is not a list of steps. "Raw chicken
        # keeps 1 to 2 days in the fridge ... and cooked chicken 3 days" gives one figure per
        # *food*, and cutting it to one of them drops which food it was for: asked "how long"
        # after it, the answer came back "3 days" - the cooked figure - for raw chicken. Two
        # different places in the pieces is the exception: each half is a step of its own.
        places = {word for piece in pieces for word in words_of(piece) if word in WHERE}
        if len(places) < 2:
            return None
    if len(pieces) < 2:
        return None
    named, cooking, waiting = [], [], []
    for piece in pieces:
        found = [_figure(match, piece) for match in figure.finditer(piece)] if figure else []
        if not found:
            continue
        if KEEPS.search(piece):
            # a shelf life in the clause is not a time the step takes, whichever step it is
            continue
        words = {word.rstrip("s") for word in words_of(piece) if len(word) > 3}
        waiting_here = bool(AFTER.search(piece))
        (waiting if waiting_here else cooking).append(found[-1])
        # A clause about waiting is not the step the question names, even when it names the
        # same thing: "rest it 10 minutes out of the oven" mentions the oven and is not the
        # baking. Only a question about the waiting itself reaches it.
        if _same_step(asked, words) and not (waiting_here and not WAIT.search(question)):
            named.append(found[-1])
    if not (SEQUENCE.search(sentence) or AFTER.search(sentence) or named):
        # A sentence that says nothing about a sequence is not a list of steps. "Raw chicken
        # keeps 1 to 2 days in the fridge ... and cooked chicken 3 days" gives one figure per
        # *food*, and cutting it to one of them drops which food it was for: asked "how long"
        # after it, the answer came back "3 days" - the cooked figure - for raw chicken. A
        # question that names one of the steps is not guessing, so it reads the clause anyway:
        # "35 to 40 minutes in the oven, and the ragu wants 30 to 40 minutes" is two steps with
        # no sequence word in it, and "how long do i bake it" has its answer there.
        return None
    if asked:
        if len(named) == 1:
            return named[0]
        if named:
            return None  # the question fits two steps, so no single figure is its answer
    if WAIT.search(question) and waiting:
        return waiting[-1]
    # Two steps that both take a different time ("35 to 40 minutes in the oven, and the ragu
    # wants 30 to 40 minutes on the hob") and a question that names neither: the last one is a
    # guess, so hand back nothing and let the sentence answer.
    if len(set(cooking)) > 1:
        return None
    if cooking:
        return cooking[-1]
    return waiting[-1] if waiting else None


# A dash aside or a bracket sits in the middle of a sentence like a parenthesis: "Feed a
# complete cat food - wet, or wet with a little dry - and weigh the day's portion". Cutting a
# clause at a separator inside it leaves a fragment, and a fragment that changes the meaning:
# the cut at the comma gave "Feed a complete cat food - wet." for an entry that says wet *or*
# wet with a little dry, and the aside is one thing said between two dashes, not two clauses.
# So a separator inside an aside is not a place to cut.
ASIDE = re.compile(r"\s+-(?!\s*-)[^-;.!?]{1,200}?-\s+"
                   r"|[\u2014\u2013][^\u2014\u2013]{1,200}?[\u2014\u2013]"
                   r"|\([^()]{1,200}\)")
# The aside and the conjunction right after it: the words on both sides of a dash aside are one
# clause with the aside pushed into the middle of it, so "a complete cat food - wet, or wet with a
# little dry - and weigh the day's portion" is one clause, not two. The conjunction is taken into
# the aside so the cut cannot land between them either.
ASIDE_ON = re.compile("(?:" + ASIDE.pattern + r")(?:(?:and|but|so)\s+|,\s*|;\s*)?")
# The placeholder an aside is held behind while the text is cut. It has no comma, semicolon or
# conjunction in it, so a cut cannot land inside an aside.
HELD = re.compile(r"\x01(\d+)\x01")


def _aside_held(text):
    """The text with each aside replaced by a placeholder, and the asides, to put back."""
    kept = []

    def hide(match):
        kept.append(match.group(0).strip())
        return " \x01%d\x01 " % (len(kept) - 1)

    return ASIDE_ON.sub(hide, str(text or "")), kept


def _aside_back(piece, kept):
    return " ".join(HELD.sub(lambda match: kept[int(match.group(1))], piece).split())


def clauses(text, pattern):
    """The pieces of `text` cut at the separators in `pattern` that are not inside an aside.

    Every reader that narrows an answer to one of its clauses cuts the sentence at a comma, a
    semicolon or a conjunction, and they all took a dash aside apart the same way. The cut is
    shared so the aside is kept whole by all of them, in the words it was written in.
    """
    return clauses_bare(text, pattern)[0]


def clauses_bare(text, pattern):
    """The pieces of `clauses()`, and the same pieces with their asides left out.

    The bare form is what a piece is *about*: a remark between two dashes says something about
    the clause, it is not what the clause is about ("a complete cat food - wet, or wet with a
    little dry - and weigh the day's portion" is about feeding wet, and the aside mentions dry
    without giving an amount for it). Reading the words of a piece without its asides keeps a
    question about the aside's own word ("how much dry food?") from settling on the piece that
    only mentions it, and the answer falls back to the whole sentence instead.
    """
    held, kept = _aside_held(text)
    pieces, bare = [], []
    # `pieces_of` keeps a numeric range whole ("1 and a half mugs"): the aside is held first, so
    # the range guard and the aside guard work on the same cut rather than one undoing the other.
    for piece in pieces_of(held, pattern):
        dressed = _aside_back(piece, kept).strip(" ,;:")
        if not dressed:
            continue
        pieces.append(dressed)
        bare.append(" ".join(HELD.sub(" ", piece).split()).strip(" ,;:"))
    return pieces, bare


# Where one piece of an answer ends and the next begins, for a reader looking for the clause
# that names a thing: a full stop, a semicolon, or a conjunction joining two clauses.
NAMED_BREAK = re.compile(r";\s*|(?<=[.!?])\s+|,\s+(?:and|but|so)\s+|\s+(?:and|but|so)\s+")
# A clause that opens on a joining word is the continuation of the one before it, not a clause of
# its own: "or 40-50g of dry" is a figure with no sentence around it, so it is not something to
# hand a person as the reply. red-door found it on the same entry (PR #3758); the aside holds
# whole either way, this is what the piece reads like once the cut is right.
LEANING = re.compile(r"^(?:or|and|but|so|plus|also)\b", re.I)
# Where a clause can end: a semicolon, a comma, or a conjunction joining two of them.
# A comma between digits is a thousands separator, not the end of a clause: "1,000" is one
# figure, and a cut inside it gave the follow-up "000" instead of the sum.
CLAUSE_BREAK = re.compile(r"(?:;\s*|,(?!\d)\s*|\s+(?:and|but|so)\s+)")
# The same, with a colon: "a complete cat food: wet or dry" says one thing in two parts, and a
# reader looking for the word that says which one wants the part after the colon.
CLAUSE_BREAK_COLON = re.compile(r"(?:;\s*|,(?!\d)\s*|\s+(?:and|but|so)\s+|:\s*)")


def _clause(text, question):
    """The clause that shares the most words with the question, when that is a real narrowing."""
    wanted = set(words_of(question))
    if not wanted:
        return None
    pieces, bare = clauses_bare(text, CLAUSE_BREAK)
    if len(pieces) < 2:
        return None
    scores = [len(wanted.intersection(words_of(piece))) for piece in bare]
    best = max(scores)
    if best and scores.count(best) == 1:
        piece = pieces[scores.index(best)]
        return None if LEANING.match(piece) else piece
    return None


def _clause_with(text, word):
    """The clause of `text` that says `word`, when it says it in exactly one."""
    pieces = clauses(text, CLAUSE_BREAK_COLON)
    hits = [piece for piece in pieces if re.search(r"\b" + re.escape(word) + r"\b", piece, re.I)]
    return hits[0] if len(hits) == 1 else None


def _clause_holding(text, span):
    """The one clause of the sentence that carries this figure, when one clause carries it alone.

    "Raw chicken keeps 1 to 2 days in the fridge, on the bottom shelf, and cooked chicken 3 days"
    gives a figure per food, so the figure on its own - "1 to 2 days." - is read as the answer for
    whichever food the person has. The clause keeps the subject with the number: "Raw chicken
    keeps 1 to 2 days in the fridge."
    """
    pieces = [piece.strip() for piece in pieces_of(text, CLAUSE_BREAK_COLON)
              if piece and piece.strip()]
    hits = [piece for piece in pieces if span in piece]
    return hits[0] if len(hits) == 1 else None


def words_of(text):
    """The content words of `text`, without fillers or plurals."""
    found = []
    for word in WORD.findall(flat(text)):
        word = word.strip("'")
        if not word or word in EMPTY:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        if word not in found:
            found.append(word)
    return found


def flat(text):
    return " ".join(str(text or "").lower().split())


def tidy(text):
    """One clean line: no trailing comma, no lowercase start, no double spaces."""
    if not isinstance(text, str):
        # Only a string can be a reply. A sentinel or a number that reaches here is a caller's
        # mistake, and `str()` turned the `NO_LENGTH` sentinel into "<object object at 0x...>."
        # and handed that to the person: the address changes every run, so it also read as a
        # changed reply in every comparison of a run against itself.
        return None
    text = " ".join(text.split()).strip().rstrip(",;:")
    if not text:
        return None
    if text[0].islower():
        text = text[0].upper() + text[1:]
    if not text.endswith((".", "!", "?")):
        text += "."
    return text
