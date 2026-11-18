"""The rule is not the bot's to state: whose it is, and where it is written.

STYLE.md draws the line this module sits on. Asked whether something is allowed, the bot must
not invent the rule, and it must not shrug either:

    is it against the law to park on the pavement
    Different councils, different rules - yours is the only one that counts here. It is on their
    site, and the council themselves will tell you where you stand if you ring.

Two things make that reply worth more than "a quick search online will get you a solid answer":
it names **who owns the rule** (the council, the court's office, the government) and it does not
guess at the wording. Nothing in this file states a rule, a penalty or a deadline, and nothing in
it is a fact about the world that could go out of date - the same reason a live price or a
surgery's opening hours are not here.

Three owners are read, and no more:

* a **court thing** - a court date, an ignored letter, a summons, a tribunal. The office named on
  the letter knows its own dates, and the reference is what gets a person through.
* a **local rule** - parking, bins, a shed, planning permission, a licence. The council writes it,
  it changes from one street to the next, and their own site has the exact wording.
* **the law in general** - cash, recording a call, points on a licence. It is published on gov.uk
  before it is guessed at, and Citizens Advice reads it against the person's own case.

What is *not* here is as deliberate. A body or a medicine stands the whole file down, so
"am i allowed to take these tablets with my antibiotics" stays a pharmacist's question. A court
you play on is not a court of law, so "how long is the tennis court open" keeps its own answer.

This is a last resort, and it is asked like one: `bot/modules/greeting.py` asks it only when the
composer's reply is already a hedge, so a card, a module or a line of the composer's own never
loses a turn to it. What it can lose is a search hedge nobody wanted, and it cannot invent a fact
to fill the gap.
"""
import re

from . import pick

# A court, a summons, a solicitor's letter: the things whose answer is an office's own dates and
# steps. Bare "hearing" is left out on purpose - "i keep hearing voices" is a health line, and a
# court hearing that matters here is named as one.
A_COURT_THING = re.compile(
    r"\bcourt\b|\bsummons\b|\btribunal\b|\bhearing\s+(?:date|on|for)\b|"
    r"\bmagistrates?\b|\bsmall\s+claims\b|\bbailiffs?\b|\bsolicitors?\s+letter\b")
# A court you play on or eat in is not a court of law: "how long is the tennis court open" is the
# leisure centre's hours, and a letter from the court office would be an invention.
A_GAME_COURT = re.compile(
    r"\b(?:tennis|squash|badminton|basketball|netball|volleyball|football|padel|pickleball|"
    r"handball|five-a-side|bowls)\s+courts?\b|\b(?:food|courtyard|shopping|outlet)\s+courts?\b")
# The things only a council rules on, or rules on differently from the next council along.
# "speeding" and "speed limit" are deliberately not in here: a fine for speeding is the general
# law, not the council's, and reading it as local would send the person to the wrong desk.
A_LOCAL_RULE = re.compile(
    r"\b(?:council|local\s+authority|parking|pavement|kerb|driveway|bins?|bin\s+day|"
    r"fly\s*tipping|noise\s+nuisance|planning\s+permission|permission\s+for|shed|fence|"
    r"conservatory|loft|extension|licen[cs]e|permit|bus\s+lane|allotment|dog\s+warden|hedge|"
    r"garden|chickens?|hens?|"
    r"bees?|hive|bonfire|barbeque|barbecue)\b")
# The ask itself. Read as wordings rather than as the word "law", because "whats the law on
# recording a call" is the same ask as "is it legal to record a call".
LAW_ASKED = re.compile(
    r"\b(?:is|isnt|is\s+not|was|wasnt)\s+(?:it|that|this)\s+(?:actually\s+|really\s+|even\s+)?"
    r"(?:legal|illegal|lawful|unlawful|against\s+the\s+law|allowed|a\s+crime)\b"
    r"|\bam\s+i\s+(?:legally\s+)?allowed\s+to\b"
    r"|\bdo\s+i\s+have\s+to\s+(?:by\s+law|legally)\b"
    r"|\bcan\s+(?:i|they|he|she|you|we)\s+be\s+fined\b"
    r"|\bwill\s+(?:i|they|he|she|we)\s+get\s+(?:done|fined|prosecuted|points|a\s+fine)\b"
    r"|\bwhats?\s+the\s+law\s+(?:on|about|say)\b"
    r"|\bdoes\s+the\s+law\s+say\b"
    r"|\bwhat\s+does\s+the\s+law\s+say\b"
    r"|\bis\s+there\s+a\s+law\s+(?:against|on|about)\b")
# Nothing here may answer a line that names a body or a medicine: "is it legal to put my dog in
# the garden" is a question about the dog's care, and "am i allowed to take these tablets" is a
# pharmacist's, not a council's.
NOT_A_RULE_ASK = re.compile(
    r"\b(?:tablets?|pills?|painkillers?|paracetamol|ibuprofen|antibiotics?|insulin|medicines?|"
    r"dose|dosage|prescription|symptoms?|bleeding|pregnant|pregnancy|baby|babies|child|kids?|"
    r"sick|ill|hurt|pain|doctor|gp|nurse|hospital)\b")
# The turn after a rule is named is usually the same question about the same rule: "the council
# are saying i need planning permission" then "will they turn it down". The line has no rule word
# of its own, so the shape that asks what will happen is what carries the thread's rule forward.
A_FOLLOW_UP = re.compile(
    r"\b(?:will|would|can|could|do|does|did)\s+(?:they|it|he|she|the\s+council|the\s+court)\b"
    r"|\bwhat\s+(?:happens|happened|now|next)\b|\bhow\s+long\b|\bwhat\s+do\s+i\s+do\b"
    r"|\bam\s+i\s+(?:in\s+trouble|stuck|liable)\b")

# A rule, honestly: the council's wording is the council's, the court's office knows its own
# dates, and the law in general is published before it is guessed at.
UNKNOWN_THE_LAW = (
    "There is an answer in law to that, and it turns on the exact situation rather than the "
    "general idea - which is the part I would get wrong. gov.uk has the wording in plain English, "
    "and Citizens Advice will read it against your own case for free.",
    "The general rule is written down, but where it lands depends on your side of it, and that is "
    "exactly the bit I would only be guessing at. gov.uk has the wording, and Citizens Advice is "
    "free and will apply it to your situation.",
    "I can tell you where this one is kept rather than what it says: law like this is published in "
    "full, and a summary from me could be wrong on a detail that matters. It is on gov.uk in plain "
    "words, and Citizens Advice will answer the same question about your own case free of charge.",
)
UNKNOWN_A_LOCAL_RULE = (
    "Rules like this are set by your council rather than nationally, so two roads can answer "
    "differently - which is why I would only be guessing at yours. Their own site has the exact "
    "wording and any charge, and their phone line settles it in a minute.",
    "This one is your council's to set and enforce, and it changes from place to place. Their "
    "site has it in writing, and Citizens Advice is free if the page is a maze, which it often is.",
    "The council writes this one, so theirs is the only wording that counts - and it varies by "
    "street, so a general answer would be no use to you. It is on their site with the details; "
    "ringing them is quicker than reading, and the number is on the page.",
)
UNKNOWN_A_COURT_THING = (
    "The letter is the thing that matters here: it names the date and the office that can answer "
    "for it, and that office is quicker than the paperwork looks. Ring it with the reference to "
    "hand, sooner rather than later - and Citizens Advice will read the letter with you first, free.",
    "Whoever sent it knows what happens next and by when, and nothing I say changes a date that is "
    "already set. Ring the office named on the letter with the reference to hand; Citizens Advice "
    "will go through the wording with you first at no cost.",
    "A court's next step is on the paperwork rather than in a general answer, and the office that "
    "sent it can tell you where you stand. The reference on the letter is what gets you through - "
    "and Citizens Advice will read it with you for free if the wording is unclear.",
)


def _said(text):
    """The line, lowercased and with its spacing tidied."""
    return " ".join(str(text or "").lower().split())


def _a_court_of_law(said):
    """True when a court word in the line means a court of law rather than a place you play.

    "how long is the tennis court open" and "how far is the tennis court" are the leisure
    centre's hours and the walk there. A line that asks about the law as well keeps the court
    arm, so a tennis court that has brought the council round is still read as both.
    """
    if not A_COURT_THING.search(said or ""):
        return False
    return not (A_GAME_COURT.search(said or "") and not LAW_ASKED.search(said or ""))


def _the_thread_said(memory, pattern, look_back=2):
    """True when one of the last few things the person said matched `pattern`."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    return any(pattern.search(_said(turn.get("user"))) for turn in turns[-look_back:])


def _a_court_of_law_in_the_thread(memory, look_back=2):
    """True when one of the last few lines named a court of law.

    "my ex is taking me to court" then "what happens if i ignore the letter": the line says only
    "the letter", and the letter is the court's.
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    return any(_a_court_of_law(_said(turn.get("user"))) for turn in turns[-look_back:])


# A noun from the council's world is not a rule ask on its own. Somebody growing veg in a back
# garden says "garden", and "small back garden with clay soil" then "can i do it from seed" was
# read as a follow-up about a garden rule - a confident wrong answer invented out of a shared word.
# So the thread carries its rule forward on one of two things: an earlier line that really was a
# rule ask (a permission wording, the council or the court by name, a penalty named), or a
# follow-up that names a penalty itself ("i put my bin out early" then "will they fine me").
PERMISSION_ASKED = re.compile(
    r"\b(?:can|could|may)\s+(?:i|we|you|they|he|she)\b"
    r"|\b(?:do|does|did)\s+(?:i|we|you|they|he|she)\s+(?:need|have\s+to|require|apply)\b"
    r"|\b(?:i|we|they|he|she)\s+(?:need|needs|have\s+to|has\s+to|required|requires)\b"
    r"|\bam\s+i\s+(?:allowed|supposed)\b"
    r"|\bis\s+it\s+(?:allowed|legal|illegal|against\s+the\s+law)\b"
    r"|\bwhat\s+(?:are|is)\s+the\s+rules?\b"
    r"|\b(?:rules?|regulations?|bylaws?|by-laws?|permission|permit|licen[cs]e)\b")
WHO_OWNS_IT = re.compile(
    r"\b(?:council|local\s+authority|town\s+hall|court|tribunal|planning|enforcement|"
    r"warden|inspector|officer)\b")
A_PENALTY = re.compile(
    r"\b(?:fines?|fined|penalt(?:y|ies)|prosecut\w*|summons|points|asbos?|"
    r"notice|tribunal|evict\w*|bailiffs?)\b")


def _said_a_local_rule_recently(memory, look_back=2):
    """True when the last few lines named something a council sets a rule about."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    return any(A_LOCAL_RULE.search(_said(turn.get("user"))) for turn in turns[-look_back:])


def _a_rule_ask_in_the_thread(memory, look_back=2):
    """True when one of the last few lines was itself a rule ask.

    "i put my bin out early" then "will they fine me" is the same rule. "small back garden with
    clay soil" then "can i do it from seed" is gardening, and the word that matched is "garden".
    """
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        earlier = _said(turn.get("user"))
        if not earlier or NOT_A_RULE_ASK.search(earlier):
            continue
        if LAW_ASKED.search(earlier) or WHO_OWNS_IT.search(earlier):
            return True
        if A_LOCAL_RULE.search(earlier) and PERMISSION_ASKED.search(earlier):
            return True
    return False


def pool_for(text, memory=None):
    """The pool that names who owns this rule, or None when the line is not about one."""
    said = _said(text)
    if not said or NOT_A_RULE_ASK.search(said):
        return None
    if _a_court_of_law(said) or _a_court_of_law_in_the_thread(memory):
        return UNKNOWN_A_COURT_THING
    if LAW_ASKED.search(said):
        if A_LOCAL_RULE.search(said):
            return UNKNOWN_A_LOCAL_RULE
        return UNKNOWN_THE_LAW
    if A_FOLLOW_UP.search(said) and _said_a_local_rule_recently(memory):
        if A_PENALTY.search(said) or _a_rule_ask_in_the_thread(memory):
            return UNKNOWN_A_LOCAL_RULE
    return None


def answer_for(text, memory=None):
    """One line naming the rule's owner, or None when the line is not a rule ask."""
    said = _said(text)
    pool = pool_for(said, memory)
    if not pool:
        return None
    return pick(pool, memory if isinstance(memory, dict) else {}, said)
