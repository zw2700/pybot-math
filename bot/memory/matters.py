"""A follow-up that says a fact about the person the answer was about, written out with them in it.

    my mum is 78 and keeps falling
      -> Falls are usually several small things adding up ... Ask the GP for a falls review ...
    she lives alone
      -> Got it - she lives alone.                      (base: the receipt STYLE.md rules out)

"she lives alone" is not news about the person and not a new question: it is the one fact that
changes which part of that answer matters. On her own, the strength and balance class is not the
first thing - a free care needs assessment, a pendant alarm, a key safe and a neighbour with a key
are - and the knowledge base already has that answer under "my mum lives alone".

What it does not have is "she lives alone": the store holds the person as "mum", so a line that
says "she" names nobody the entries are keyed on, the lookup finds nothing, and the turn falls to
the store, which says the line back. This module writes the line out with the person in it and
hands it on, so the answer is the answer to the fact and not a receipt.

Only the narrow shape is taken, because a pronoun is not always the person on screen:
  * the line opens with "she" or "he" and says nothing else of its own - no question mark, a
    handful of words, and the rest of the line starts with a verb a fact about a person uses
    ("lives", "is", "has", "keeps", "falls", "wont", "refuses", "uses");
  * the store holds exactly one person (`memory["others"]`), so "she" has one person to be;
  * that person's sex agrees with the pronoun, where the store knows it.
Everything else - "my sister lives alone", which the entries already reach, two people in the
store, a question about her ("should she move?"), a report ("she said thanks") - is passed on
unchanged, and the turn is answered exactly as it was before this module existed.
"""
import re

from . import people

# The relation word a person in the store is keyed by, as a possessive the entries read:
# "mum" -> "my mum". A store person whose relation is somebody else's ("his mum" kept as "mum")
# still reads as "my mum", which is what the entries are keyed on.
MINE = "my "

# The line opening with the pronoun for a person: "she", "she's", "shes", "he", "he's", "hes".
SO = re.compile(r"^\s*(?:and|but|also|oh|well|so|see)?\s*,?\s*"
                r"(?P<who>she|he)(?P<is>'s|s)?\s+(?P<rest>[^?]{2,60})\s*$", re.I)
# The verb a fact about a person opens with: "lives alone", "is on blood thinners", "keeps
# falling", "wont have a carer". "should", "did", "can" and the rest open a question about them,
# and a question about her is hers to answer, not a fact to look up.
FACT_VERB = frozenset("""
live lives lived living is are was were has have had keeps keep kept falls fall fell falling
refuses refuse refused wont won't cant can't cannot doesnt doesn't never always still only on
takes take uses use needs need gets get goes go wants want sits sit walks walk forgets forget
wears wear uses stopped stops started starts keeps manages manages
""".split())
# Words that make the line a report of what somebody said rather than a fact about them: the
# store's reply to "she says she's fine" is the ack, and the ack is right for it.
A_REPORT = re.compile(r"^\s*(?:says?|said|told|thinks?|wants?|asked|keeps saying|thinks)\b", re.I)
# What a person eats and what they refuse is the store's, not a question for the entries: "she
# doesnt eat meat" after a suggestion is the diet the next dinner has to work around, and asking
# the knowledge base with "my girlfriend doesnt eat meat" answers something else entirely.
THEIR_DIET = re.compile(
    r"^(?:"
    r"(?:does\s*nt|does\s+not|do\s*nt|don'?t|won'?t|wont|cant|can'?t|never|only)"
    r"\s+(?:eat|eats|drink|drinks|touch|touches|stand|stands|like|likes|want|wants)\b"
    r"|(?:is\s+)?(?:hates?|likes?|loves?|avoids?|allergic|refuses?)\b"
    r")", re.I)
MOST_WORDS = 8

# Two ways of saying one fact, written as the one the entries are keyed on: "lives on her own"
# and "lives alone" are the same thing about a person, and only one of them reaches the answer
# about a person on their own - the other reaches an entry about inviting somebody out, which is
# about a lonely week and not about the falling.
ON_THEIR_OWN = re.compile(
    r"^liv(?:es?|ing)\s+"
    r"(?:on\s+(?:her|his|their|its)\s+own|by\s+(?:her|him|them)sel(?:f|ves)|alone)\b\s*"
    r"|^(?:is\s+)?"
    r"(?:on\s+(?:her|his|their|its)\s+own|by\s+(?:her|him|them)sel(?:f|ves)|alone)"
    r"(?:\s+at\s+home)?\b\s*",
    re.I)
LIVES_ALONE = "lives alone" 


def _the_person(memory):
    """The one person the chat knows: (relation, sex) or None. Two people is nobody in particular."""
    others = memory.get("others") if isinstance(memory, dict) else None
    if not isinstance(others, list):
        return None
    seen = []
    for record in others:
        if not isinstance(record, dict):
            continue
        who = str(record.get("who") or "").strip().lower()
        if who and who not in [one[0] for one in seen]:
            seen.append((who, record))
    if len(seen) != 1:
        return None
    who, record = seen[0]
    sex = ""
    if who in people.HIM:
        sex = "him"
    elif who in people.HER:
        sex = "her"
    return who, record, sex


def about_them(text, memory):
    """The line written with the person in it: "she lives alone" -> "my mum lives alone".

    Empty when the line is not the narrow shape above, so the caller answers exactly as before.
    """
    if not isinstance(text, str):
        return ""
    found = SO.match(text)
    if not found:
        return ""
    rest = " ".join(found.group("rest").split())
    if len(rest.split()) > MOST_WORDS:
        return ""
    if A_REPORT.match(rest) or THEIR_DIET.match(rest):
        return ""
    alone = ON_THEIR_OWN.match(rest)
    if alone:
        # Two ways of saying one fact, written as the one the entries are keyed on: "on her own at
        # home" and "by herself" are "lives alone" about a person, and only "lives alone" reaches
        # the answer about a person on their own - "on her own" reaches the entry about inviting
        # somebody out, which is about a lonely week and not about the falling.
        rest = (LIVES_ALONE + " " + rest[alone.end():]).strip()
    elif rest.split()[0].strip(",.").lower() not in FACT_VERB:
        return ""
    person = _the_person(memory)
    if person is None:
        return ""
    who, _record, sex = person
    said = found.group("who").lower()
    if sex and ((said == "she" and sex != "her") or (said == "he" and sex != "him")):
        # "she" and the store's one person is a son: the pronoun is about somebody else.
        return ""
    if who in rest.lower().split():
        return ""  # the line names a relation already, and the entries read it as it stands
    if alone:
        # "she's on her own at home" is "she lives alone", verb and all, so the copula in the
        # line is not said again ("my mum is lives alone").
        return MINE + who + " " + rest
    if found.group("is"):
        # "she's on blood thinners" is "she is on blood thinners", and the verb has to be in the
        # rewrite: "my mum on blood thinners" is not what the entries are keyed on.
        return MINE + who + " is " + rest
    return MINE + who + " " + rest

# The line that reports what the person says about themselves is not a fact to look up and not a
# thing to say back: after a falls answer, "she says she's fine" is her asking for no fuss, and the
# turn wants the one thing that works around that. Said back ("Got it - she's fine." /
# "She says she's fine - noted.") it is the receipt STYLE.md rules out, and it leaves the person
# with the same worry and nothing to do next.
THEIR_WORD = re.compile(
    r"^\s*(?:and|but|so|also|oh|well|see)?\s*,?\s*"
    r"(?P<who>she|he|they|mum|mom|dad|nan|nana|gran|granny|grandma|grandad)\b"
    r"(?:'s|s|\s+is|\s+are)?\s+"
    r"(?:says?|said|tells? me|told me|insists?|insisted|reckons?|reckoned|claims?|claimed|"
    r"keeps saying|thinks?)\s+"
    r"(?:(?:that\s+)?(?:she|he|they)(?:'s|s|\s+is|\s+are)?\s+)?"
    r"(?P<what>fine|alright|all right|ok|okay|grand|managing|coping|all good|not too bad)\b"
    r"(?:\s*,?\s*(?:thank you|thanks|i think|i reckon|really|honestly|though|anyway|actually)"
    r"){0,2}\s*[.!]?\s*$", re.I)
# The worry the refusal is about: falls, a carer, a memory, a hospital stay. Without one of these
# in the chat, "she says shes fine" is small talk about somebody, and the pools read it better.
CARE_MATTER = re.compile(
    r"\b(?:fall|falls|fallen|fell|falling|carer|carers|care|dementia|alzheim\w*|memory|"
    r"forget\w*|confused|hospital|stroke|doctor|gp|surgery|social services|needs assessment|"
    r"pendant|alarm|key safe|blood thinner\w*|warfarin|tablets|medication)\b", re.I)
# The reply is the same shape whatever the refusal was, so there are a few of them and the store
# counts which was used: the same three sentences twice in one chat is the stock line.
FINE_REPLY = (
    "That usually means your {who} doesn't want a fuss, not that nothing is wrong. Don't argue "
    "the point - ask for one small thing instead, the GP appointment with you in the room, and "
    "let the doctor carry the worry.",
    "They say that to keep the peace, and it does not mean it has stopped. Keep a note of when it "
    "happens and ring your {who}'s GP yourself: they can act on what you tell them, and nobody "
    "has to ask for it.",
    "How your {who} feels is worth believing; the risk is not something to take their word for. "
    "Make the whole ask one thing you do together - the free falls review, or a walk to the end "
    "of the road - so there is nothing to admit to.",
)


def _a_worry_in_the_chat(memory):
    """True when the chat has named a care worry about the person, and not just a mood."""
    if not isinstance(memory, dict):
        return False
    turns = memory.get("turns") or ()
    said = []
    for turn in list(turns)[-5:]:
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or ""))
        elif isinstance(turn, (list, tuple)) and turn:
            said.append(str(turn[0]))
        else:
            said.append(str(turn))
    return bool(CARE_MATTER.search(" ".join(said)))


def what_they_say(text, memory):
    """The reply for "she says she's fine" about the person on screen, or "" to pass.

    Asked only when the store holds one person, the pronoun is that person's, and the chat has a
    care worry in it: anything else is somebody's ordinary remark and keeps its own turn.
    """
    if not isinstance(text, str):
        return ""
    found = THEIR_WORD.match(text)
    if not found:
        return ""
    person = _the_person(memory)
    if person is None:
        return ""
    who, _record, sex = person
    said = found.group("who").lower()
    if sex and ((said in ("she", "her") and sex != "her") or (said == "he" and sex != "him")):
        return ""  # "she says she's fine" and the one person in the store is a son
    if not _a_worry_in_the_chat(memory):
        return ""
    pool = list(FINE_REPLY)
    at = memory.get("fine_said") if isinstance(memory, dict) else 0
    if not isinstance(at, int) or at < 0:
        at = 0
    if isinstance(memory, dict):
        memory["fine_said"] = at + 1
    return pool[at % len(pool)].format(who=who)

# A correction of one of the ages a group of children was given. The group is filed as one fact
# ("my kids are 4 and 6"), so the correction machinery for a single person's age cannot place it:
# "sorry ones 7" left the store saying four and six while the bot said the line back ("Got it -
# ones 7."), and "what ages are they" then answered "Your kids are 4 and 6" - the bot told them
# the correction landed and then contradicted itself.
_ONE_AGE = re.compile(r"\b(?P<age>\d{1,3})\b")
_NOT_THE_OLD_ONE = re.compile(r"\b(?:not|instead of|rather than|no wait,? not)\s+(?P<old>\d{1,3})\b",
                              re.I)
# Which of the group the line is about. The words people use for the older or the younger of two,
# and nothing else: "my older sister" is a different person, and the relation has to be absent for
# this to be about the group.
_OLDEST = re.compile(r"\b(?:oldest|eldest|older|bigger|elder|big one)\b", re.I)
_YOUNGEST = re.compile(r"\b(?:youngest|younger|littlest|little|smallest|baby|wee one)\b", re.I)
_A_CORRECTION = re.compile(r"\b(?:actually|no|nope|sorry|wait|i mean|i meant|make it|makes it|"
                           r"not|instead)\b", re.I)


def _the_group_ages(memory):
    """The single group of ages the store holds, or (None, [])."""
    if not isinstance(memory, dict):
        return None, []
    found = []
    for entry in memory.get("others") or ():
        if not isinstance(entry, dict):
            continue
        ages = [age for age in entry.get("ages") or () if isinstance(age, int)]
        if len(ages) > 1:
            found.append((entry, ages))
    if len(found) != 1:
        return None, []
    return found[0]


def _say_the_ages(ages):
    ages = sorted(ages)
    if len(ages) == 2:
        return "%d and %d" % (ages[0], ages[1])
    return ", ".join(str(age) for age in ages[:-1]) + " and " + str(ages[-1])


def a_corrected_age(text, memory):
    """The reply for a corrected age in a group of children, or "" to pass.

    Only the corrections that say which child they are about are applied; one that could be either
    asks which, because guessing puts the wrong age on a child and the chat then answers every
    later question with it.
    """
    if not isinstance(text, str):
        return ""
    low = " ".join(text.lower().split())
    if not low or len(low.split()) > 10:
        return ""
    entry, ages = _the_group_ages(memory)
    if entry is None:
        return ""
    numbers = [int(m.group("age")) for m in _ONE_AGE.finditer(low)]
    numbers = [age for age in numbers if 0 < age <= 120]
    if not numbers:
        return ""
    correcting = bool(_A_CORRECTION.search(low))
    # "ones 7 not 6" names the age being replaced, so there is nothing to guess.
    replaced = _NOT_THE_OLD_ONE.search(low)
    if replaced:
        was = int(replaced.group("old"))
        new = [age for age in numbers if age != was]
        if was in ages and new:
            ages[ages.index(was)] = new[0]
            entry["ages"] = sorted(ages)
            return "Right — %s, then." % _say_the_ages(entry["ages"])
        return ""
    # "the oldest is 7 now" and "the little one is 2": the word says which end of the group moves.
    if _OLDEST.search(low) and not _YOUNGEST.search(low):
        ages[ages.index(max(ages))] = numbers[0]
        entry["ages"] = sorted(ages)
        return "Right — %s, then." % _say_the_ages(entry["ages"])
    if _YOUNGEST.search(low) and not _OLDEST.search(low):
        ages[ages.index(min(ages))] = numbers[0]
        entry["ages"] = sorted(ages)
        return "Right — %s, then." % _say_the_ages(entry["ages"])
    # "sorry ones 7": a number where there were two, and nothing saying which child. Asking is the
    # honest reply - it is one word back and the answer lands on the right child.
    if correcting and numbers[0] not in ages:
        which = " or the ".join(str(age) for age in sorted(ages))
        return "Which one is %d — the %s?" % (numbers[0], which)
    return ""
