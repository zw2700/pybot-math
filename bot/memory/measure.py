"""A follow-up that asks the measure again: "and how much", "and how often", "and how long".

Nobody says the subject twice. The person asked how much water to drink, the answer gave six to
eight glasses, and then they asked "and how much" - and nothing in those three words says water,
so the knowledge base read them as words in their own right and answered from a different entry:

    how much water should i drink a day
      Six to eight glasses a day, about 1.5 to 2 litres, is plenty, and more in heat or after ...
    and how much
      The UK limit is 14 units a week for men and women ... (the alcohol card, reached by "drink")

The same shape took "and how often" after a dog-walking answer to the puppy paragraph, and after
a roast-chicken answer to "Same answer, and it covers this: About 20 minutes per 500g ...". The
figure is already in the answer above, so the follow-up is answered from that answer: the
sentence of it that carries the measure the person asked for, in the answer's own words.

Narrow on purpose:

* the line has to be *only* the measure - "and how much", "how often again", "and how long is
  that" - with no subject of its own, because "how much water for a puppy" asks about a puppy;
* the answer above has to be a card the bot really said on the turn before (the same check
  `bot/memory/topics.entry_answer` makes), so a chat line is never quoted back as an answer;
* the sentence handed back has to carry the measure that was asked for, or the module passes and
  the line is answered exactly as it was.
"""
import re

# The measure words, and the sentence each one is looked for in. "much" and "many" are a quantity
# ("1.5 to 2 litres", "six to eight glasses"), "often" is a frequency ("once a week", "twice a
# day"), "long" is a duration ("20 minutes", "eight weeks") and the rest are a quantity with its
# own unit ("4 miles", "200C", "two inches").
MEASURES = {
    # A quantity needs a figure: "six to eight glasses", "1.5 to 2 litres", "6g". A card that says
    # "cut the liquid sugar first" is advice about an amount, not the amount, and handing that
    # back as the answer to "and how much" would be a sentence with no figure in it.
    "much": re.compile(r"\b\d", re.I),
    "many": re.compile(r"\b\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|dozen)\b",
                       re.I),
    "often": re.compile(r"\b(?:once|twice|thrice|every|each\s+(?:day|week|month|morning|night)|"
                        r"daily|weekly|monthly|hourly|times\s+a|a\s+day|a\s+week|a\s+month|"
                        r"\d\s*(?:-|to)?\s*\d*\s*times)\b", re.I),
    "long": re.compile(r"\b\d+\s*(?:second|minute|hour|day|week|month|year)s?\b|"
                       r"\b\d+\s*(?:-|to)\s*\d+\s*(?:second|minute|hour|day|week|month|year)s?"
                       r"\b|\bovernight\b|\ball\s+(?:day|night)\b", re.I),
    "far": re.compile(r"\b\d+\s*(?:mile|km|kilometre|kilometer|metre|meter|yard|foot|feet)s?\b",
                      re.I),
    "hot": re.compile(r"\b\d{2,3}\s*(?:\u00b0|c\b|f\b|degrees?)|\bgas\s*mark\s*\d", re.I),
    "deep": re.compile(r"\b\d+\s*(?:cm|centimetre|centimeter|inch|in|mm|metre|meter)s?\b", re.I),
    "big": re.compile(r"\b\d+\s*(?:cm|centimetre|centimeter|inch|in|mm|litre|liter|gram|kilo)s?"
                      r"\b", re.I),
}

# A leading "and"/"so"/"ok" and a trailing "again"/"then"/"exactly" belong to the follow-up, not to
# the question: they say the person is asking the same thing over, which is exactly the case here.
LEAD = re.compile(r"^(?:(?:and|so|ok|okay|but|then|right|yeah|yes|well|oh|er|um|hmm)\b[\s,]*)+",
                  re.I)
TAIL = re.compile(r"[\s,]*(?:(?:again|then|exactly|please|thanks|though|for\s+that|for\s+one|"
                  r"for\s+each|per\s+(?:day|week|person|one)|roughly|about|or\s+so|"
                  r"is\s+that|was\s+that|would\s+that\s+be|does\s+that|do\s+i|did\s+i|"
                  r"would\s+i|should\s+i|will\s+i|of\s+that|there)\b[\s,]*)*$", re.I)

ASKED = re.compile(r"\bhow\s+(much|many|often|long|far|hot|deep|big)\b", re.I)

# The end of a sentence, and the same rule the rest of the memory uses: a full stop, question mark
# or exclamation after which a capital letter stands.
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def the_measure_asked(line):
    """Which measure the line asks for, or "" when the line is not only a measure.

    "and how much" is the ask; "and how much is that in litres" carries words of its own and is a
    question the person asked in full, so it is left to the module that can answer it.
    """
    text = str(line or "").strip()
    if not text:
        return ""
    text = LEAD.sub("", text)
    text = TAIL.sub("", text)
    text = text.strip(" ?.!,:;-")
    text = LEAD.sub("", text).strip(" ?.!,:;-")
    match = ASKED.fullmatch(text)
    if not match:
        return ""
    return match.group(1).lower()


# The modules whose answer is about the person and not about a card, so a measure asked after one
# of them is theirs to answer.
KEEP_THEIR_TURN = frozenset(("loss", "grief", "safety", "safety_cards", "safety_phrases"))


def _the_card_said_last(memory):
    """The card the bot answered with on the turn before, or "" when the last turn was not one."""
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1]
    if not isinstance(last, dict):
        return ""
    # A measure asked again inside something hard is not a question about a card: after the loss
    # and grief modules or the safety band have answered, "and how long" is about what they said,
    # and those modules keep their turn.
    if str(last.get("module") or "") in KEEP_THEIR_TURN:
        return ""
    said = " ".join(str(last.get("bot") or "").lower().split())
    if not said:
        return ""
    records = memory.get("entry_answers")
    if not isinstance(records, list) or not records:
        records = [memory.get("entry_answer")]
    for record in reversed(records):
        if not isinstance(record, dict):
            continue
        text = str(record.get("text") or "").strip()
        if not text:
            continue
        opening = " ".join(text.lower().split()[:8])
        if said.startswith(opening) or " ".join(text.lower().split()[:5]) in said:
            return text
    return ""


# A card runs long: the answer to "how much water" is one sentence with the figure in its first
# half and the reasons after ("Six to eight glasses a day, about 1.5 to 2 litres, is plenty, and
# more in heat or after exercise; tea, coffee, milk, squash and food all count towards it"), and
# handing the whole of it back is the answer the person read a turn ago, word for word. So the
# clause that carries the measure goes back instead. A card ends a clause where a new one starts:
# "is", "are", "and", "so", "but", "which", "then", "because", "when", "it", "with", "plus". Never
# at a bare comma with anything after it, because "Cut the liquid sugar first, because it is the
# easiest to lose" ends nowhere useful either.
A_NEW_CLAUSE = frozenset("""and so but or which is are was were then because when if that
it they there this these with plus while as""".split())


def _the_clause_that_carries(sentence, pattern=None):
    """The first clause of the sentence that carries the measure, in the sentence's own words."""
    for boundary in re.finditer(r"[,;:]\s+", sentence):
        rest = sentence[boundary.end():]
        first = (re.split(r"\s+", rest.strip()) or [""])[0].strip(",.;:").lower()
        if first in A_NEW_CLAUSE:
            said = sentence[:boundary.start()].strip()
            if len(said.split()) >= 4:
                return said
    return sentence


def _the_sentence_with(text, measure):
    """The clause of an answer that carries the measure asked for, or "" when none does."""
    pattern = MEASURES.get(measure)
    if not pattern:
        return ""
    sentences = [part.strip() for part in SENTENCE.split(text) if part.strip()]
    for sentence in sentences:
        if pattern.search(sentence):
            return _the_clause_that_carries(sentence, pattern)
    return ""


# The thing the earlier line put straight after the measure word: "how much water", "how many
# eggs", "how long rice". A clause of the answer does not always name it ("Six to eight glasses a
# day, about 1.5 to 2 litres" does not say water), and a bare figure is an answer to a question
# nobody can see, so the word the person used goes in front as a one-word headline.
THING_AFTER = re.compile(r"\bhow\s+(?:much|many|often|long|far|hot|deep|big)\s+"
                         r"(?:of\s+)?(?P<thing>[a-z][a-z\\s'&/-]{0,28})\b", re.I)
STOPS_THE_THING = frozenset("""should do can could would shall will did does is are was were
to for before when if after and or but in on at with by the a an my your his her their our
it them that this i we you they""".split())


def _the_thing_the_line_named(memory):
    """The short phrase the earlier line put straight after its measure word, or "".

    Only when it is one to three words with no verb in it, so "how much water" gives "water" and
    "how long do i roast a chicken for" gives nothing.
    """
    said = ""
    for turn in reversed(memory.get("turns") or []):
        if isinstance(turn, dict) and str(turn.get("user") or "").strip():
            said = str(turn.get("user") or "")
            break
    match = THING_AFTER.search(said)
    if not match:
        return ""
    words = [word for word in re.split(r"\s+", match.group("thing").strip()) if word]
    kept = []
    for word in words:
        if word.lower().strip(",.;:") in STOPS_THE_THING:
            break
        kept.append(word.strip(",.;:"))
        if len(kept) == 3:
            break
    thing = " ".join(kept).strip(" ,.;:-")
    return thing if thing and thing.lower() not in THING_NOT_WORTH_SAYING else ""


# Words that name nothing a person would say back as a headline.
THING_NOT_WORTH_SAYING = frozenset(("it", "that", "this", "them", "there", "one"))


# The unit a figure is counted in, where it is a thing that holds what was asked about. The water
# card says "Six to eight glasses a day" and never says water, so the answer to "and how much"
# would be six to eight glasses of what. A container is the one place the thing can go: "about
# four cups of instant coffee" already says its own thing, and "400mg of caffeine" is a weight of
# the caffeine, so nothing is put in front of a weight or a volume.
A_CONTAINER = re.compile(r"\b(?:glasses|glass|cups|cup|pints|pint|slices|slice|portions|portion|"
                         r"pieces|piece|sachets|sachet|scoops|scoop|cloves|clove|tins|tin|"
                         r"cans|can|teaspoons|teaspoon|tablespoons|tablespoon|sprays|spray|"
                         r"doses|dose|wipes|wipe|sheets|sheet)\b", re.I)


def _with_the_thing(sentence, thing):
    """The sentence with the thing the line named set in front of its first container, or ""."""
    found = A_CONTAINER.search(sentence)
    if not found:
        return ""
    head = sentence[:found.end()]
    tail = sentence[found.end():]
    return "%s of %s%s" % (head, thing, tail)


def _as_a_headline(thing, sentence):
    """The thing as a one-word headline, then the answer in lower case where it reads as prose."""
    first = sentence[0]
    rest = sentence[1:]
    if first.isupper() and rest[:1].islower():
        sentence = first.lower() + rest
    return "%s: %s" % (thing[0].upper() + thing[1:], sentence)


def _as_a_sentence(text):
    """The clause as the one sentence the reply is: a card's clause loses its full stop when it is
    cut out of a longer sentence, and a reply line that ends on "about once a week" reads as if the
    bot were cut off."""
    if text and text[-1] not in ".!?":
        return text + "."
    return text


def reply_for(text, memory):
    """The clause of the answer above that answers the measure asked again, or None."""
    measure = the_measure_asked(text)
    if not measure:
        return None
    card = _the_card_said_last(memory)
    if not card:
        return None
    sentence = _the_sentence_with(card, measure)
    if not sentence:
        return None
    thing = _the_thing_the_line_named(memory)
    if thing and thing.lower() not in sentence.lower():
        # A card about water that never says water: "Six to eight glasses of water a day, about 1.5
        # to 2 litres" is the same answer with the thing said, and the head is what a one-word
        # headline would have said anyway.
        said = _with_the_thing(sentence, thing)
        if said:
            return _as_a_sentence(said)
        return _as_a_sentence(_as_a_headline(thing, sentence))
    return _as_a_sentence(sentence)
