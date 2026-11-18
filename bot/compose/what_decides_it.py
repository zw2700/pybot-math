"""A qualifier after a knowledge answer: say the test the answer gave, in its own words.

    i keep getting heartburn      "An antacid settles most heartburn ... See a GP if it lasts more
                                   than three weeks or you find food sticking on the way down."
    im 34 and not overweight      the fallback: "I'm listening - say more if it helps."

    what should i get from the chippy    "Fish and chips feeds a group for the least money ..."
    not that hungry                      the fallback: "Got it. Is there anything you'd like a
                                         hand with?"

The second line is not a question and asks for nothing new. It is the person putting a fact about
themselves against what they were just told - an age, a weight, a negation ("not that hungry",
"i dont smoke"), the kind of thing they have ("its the flat pack kind with two doors"). A friend
answers that by saying which part of what they said that fact actually bears on, and the answer is
already in the reply: the test it gave ("if it lasts more than three weeks", "if you find food
sticking") is what decides, not the age or the weight.

This reader quotes that test back and nothing else. It never invents a rule, never says whether the
person's fact matters - when the qualifier and the test share a content word (`i dont smoke` against
`if you smoke, take extra care`) the two are in contact and the reply stops being the bot's to give,
so the reading stands down and the line goes where it went before. The bar for it is the same one
`bot/compose/kept_nearby.py` keeps: name the kind, stay inside what the bot itself said.
"""
import re

# The bot's last turn has to be a knowledge answer: a card, an entry, a question back or the
# fallback's own line is somebody else's turn, and a qualifier after those is not this one.
ANSWER_MODULE = "answers"

# A sentence that carries a rule rather than a fact: these are the tests an answer gives.
_CONDITION = re.compile(r"\b(if|unless|until|once|before|after|whenever|as long as)\b")

# What the person puts against it. Negations and quantities about themselves, and the shape people
# use for "the kind of thing I have".
# A condition on its own is not a test: "if tastes differ, Indian beats Chinese" is one of the
# options the answer offers, not the thing that decides. A test hands you on to somebody, or gives
# a limit in days, weeks or months - "see a GP if it lasts more than three weeks", "ring the council
# once it has been out a fortnight". Only those are quoted.
_HANDOFF = re.compile(r"\b(gp|doctor|nurse|pharmacist|chemist|dentist|vet|council|landlord|"
                      r"seller|retailer|shop|airline|insurer|bank|999|111|nhs|advice|adviser|"
                      r"advisor|helpline|ombudsman|employer|school)\b")
_LIMIT = re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fourteen|"
                    r"twenty)\s+(day|days|week|weeks|month|months|year|years)\b")
_MORE_THAN = re.compile(r"\b(more than|over|longer than|up to|at least)\b")

_NEGATION = re.compile(r"\b(not|no|none|never|dont|doesnt|didnt|isnt|arent|wasnt|cant|cannot|"
                       r"without|nobody|nothing)\b")
_AMOUNT = re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b")

# Lines that are questions ask something; those are other readers' (a card, a gap, a figure).
_QUESTION_START = frozenset((
    "what", "how", "why", "when", "where", "who", "whom", "whose", "which", "can", "could",
    "should", "would", "shall", "will", "do", "does", "did", "is", "are", "was", "were", "am",
    "have", "has", "had", "may", "might", "must", "any", "anything", "isnt", "arent", "dont",
    "doesnt", "cant", "wont", "whats", "hows", "wheres", "whys",
))

# A correction is not a qualifier: "no i meant with my flatmate not my wife" is the person moving
# the subject, and it needs the bot to take the new one, not to say the test is unchanged.
_CORRECTION = re.compile(r"\b(i meant|i mean|i said|i wasnt saying|im talking about|"
                         r"i was talking about|the other one|not my|not the)\b")

LEAD = ("Right.", "Got it.", "Fair enough.", "Okay.", "Right then.")
POOL = (
    "{lead} The test does not turn on that: {clause}.",
    "{lead} Same test either way: {clause}.",
    "{lead} That leaves the test where it was: {clause}.",
    "{lead} The bit that decides it is unchanged: {clause}.",
)

STOP = frozenset("""
a an the and or but if then than that this these those it its it's is are was were be been being
i im i'm me my you your we our they their he she his her them us of in on at to for from with
about into over under as so not no do does did done have has had can could should would will
just very really quite too also more most much many some any thing things kind sort lot bit
""".split())


def _turns(memory):
    return [t for t in (memory or {}).get("turns") or [] if isinstance(t, dict)]


def _clean(text):
    return " ".join(str(text or "").lower().replace("\u2019", "'").split())


def _answer_above(memory):
    """The bot's own last reply, when it was a knowledge answer."""
    turns = _turns(memory)
    if not turns:
        return ""
    last = turns[-1]
    if str(last.get("module") or "") != ANSWER_MODULE:
        return ""
    return str(last.get("bot") or "").strip()


def _is_a_qualifier(clean):
    """A short statement about themselves, not a question and not a new subject."""
    if not clean or "?" in clean:
        return False
    words = clean.split()
    if len(words) > 10:
        return False
    if words[0].strip(",.") in _QUESTION_START:
        return False
    if _CORRECTION.search(clean):
        return False
    if not (_NEGATION.search(clean) or _AMOUNT.search(clean) or "kind" in clean
            or "sort of" in clean):
        return False
    return True


def _content(text):
    out = set()
    for word in re.findall(r"[a-z']+", _clean(text)):
        word = word.strip("'")
        if len(word) < 4 or word in STOP:
            continue
        out.add(word[:-1] if word.endswith("s") and len(word) > 4 else word)
    return out


def _sentences(answer):
    parts = re.split(r"(?<=[.!?])\s+", str(answer or "").strip())
    return [p.strip() for p in parts if p.strip()]


def _is_a_test(sentence):
    lowered = " " + sentence.lower() + " "
    if not _CONDITION.search(lowered) or len(sentence.split()) < 5:
        return False
    return bool(_HANDOFF.search(lowered) or _LIMIT.search(lowered)
                or (_MORE_THAN.search(lowered) and _LIMIT.search(lowered)))


def _the_test(answer):
    """The answer's own deciding sentence: the last one that carries a condition."""
    # The last sentence with a rule in it: advice builds to the point where it hands you on to
    # somebody ("see a GP if ..."), and an earlier "if" is usually a description of the thing.
    found = ""
    for sentence in _sentences(answer):
        if _is_a_test(sentence):
            found = sentence
    if not found:
        return ""
    words = found.rstrip(" .;:,").split()
    if len(words) > 34:
        # cut at the last comma that still leaves a clause worth quoting, never mid-phrase: a red
        # flag quoted without what to do about it ("...ring 999") would be worse than no quote
        cut = " ".join(words[:34])
        comma = cut.rfind(",")
        words = (cut[:comma] if comma > 60 else cut).split()
    found = " ".join(words).rstrip(" ,;:")
    # "See a GP" reads as "see a GP" in the middle of a line; an acronym or a name keeps its case.
    first = found.split(" ", 1)[0]
    if first[:1].isupper() and first[1:].islower():
        found = found[0].lower() + found[1:]
    return found


def _in_contact(clean, test):
    """True when the person's own words bear on the test: then the reply is not ours to give."""
    return bool(_content(clean) & _content(test))


def answer_for(text, memory=None):
    """One line naming the test the answer above gave, or None when the line is not a qualifier."""
    clean = _clean(text)
    answer = _answer_above(memory)
    if not answer or not _is_a_qualifier(clean):
        return None
    test = _the_test(answer)
    if not test or _in_contact(clean, test):
        return None
    lead = LEAD[sum(ord(c) for c in clean) % len(LEAD)]
    line = POOL[sum(ord(c) for c in clean + test) % len(POOL)]
    return line.format(lead=lead, clause=test)
