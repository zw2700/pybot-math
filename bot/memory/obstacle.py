"""A stated dislike of the thing the last answer leaned on.

"i want to lose weight" gets the plan, and the next line is "i hate exercise". Nothing answers
it, so the composer echoes the person's own words back ("Got it - you hate exercise"), which is a
receipt for a sentence rather than a reply to it, and it ends the conversation: the person has
just said what does not fit, and the bot has said nothing about it.

What a friend does with "i hate exercise" is leave it out and say which part of the plan still
holds: "Fair enough - this part doesn't need exercise: Fill up on protein and fibre first...". The
step is the one they were already given, so it is honest without any new knowledge, and it answers
the objection instead of filing it.

The rule is narrow on purpose:
* the line has to be nothing but a stated dislike or a lack of a thing ("i hate exercise", "i
  cant stand the gym", "i dont like cooking"): `ack.only_a_dislike` is the same reading the
  composer uses to keep a dislike from being read as a bad day, so "i hate my boss shouting at me"
  and "i hate my job" stay the composer's;
* the answer being objected to has to be a knowledge answer with a step in it, and it has to be
  about the same thing the chat is still on, so a line that changes the subject ("how do i fix the
  tap" then "i hate exercise") is left alone;
* a step that itself names the thing they dislike is not handed back as the thing to do - the
  answer is searched for the first step that does not need it, and when every step needs it the
  line is left to the composer;
* the step is not said a third time: what has already come back once comes back in its first
  clause or not at all.

The same answer is on the screen for a refusal of the move rather than a dislike of a thing:
"theres a mouse in my kitchen" gets the way in, the traps and the poison, and "i dont want to
kill it" was met with the floor ("Got it. Is there anything you'd like a hand with?") - a line
that would fit any message, one turn after being told how. What a friend does with that is not
argue for the trap: it is to say that the move is not owed at all, and hand over the part of the
answer that never needed it ("You don't have to kill it: Find the way in first: ... block those
with wire wool and filler"). No new knowledge goes into it - the part handed over is a sentence of
the answer already given, so it is honest by construction.

That reading is narrower than it looks. The refused move has to be one of a short list of words a
knowledge answer actually prescribes (`kill`, `trap`, `poison`, `bait`, `take`), together with the
words the answer uses for the same move (`THE_SAME_MOVE`), and the answer has to contain one of
them: "i dont want to upset her" and "i dont want to make it a big thing" name nothing the answer
prescribes, so those lines keep the composer's reply. The step handed over has to contain none of
the family at all, or the reply would hand back the very thing they refused.

A refusal names its move either as a doing ("i dont want to kill it", "i dont want to take pills")
or as the thing itself ("i dont want pellets", "i dont want medication"), and the lead is written
for the one it is: a noun put where a doing goes reads as "You don't have to pellets".
"""
import re

from ..understanding import understand
from . import ack, detail, repeat, topics

# The verbs a person states a dislike with, and the thing after them. "hate", "cant stand" and
# "not a fan of" are the ways it is said; the taste reading (`ack.only_a_dislike`) is what
# decides whether the line is a dislike of a thing or a bad day about a person.
DISLIKE = (
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
               r"i\s+(?:(?:just|really|properly|actually|kind of|sort of)\s+)*"
               r"(?:hate|hates|dislike|dislikes)\s+(?P<thing>.+)$", re.I),
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
               r"i\s+(?:(?:just|really|properly|actually)\s+)*"
               r"(?:cant|cannot|can\s*not|can'?t)\s+stand\s+(?P<thing>.+)$", re.I),
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
               r"i\s*(?:'m|m|am)?\s*(?:not|n't)\s+(?:a\s+)?(?:fan|keen)\s+(?:of|on)\s+"
               r"(?P<thing>.+)$", re.I),
    # "i dont like cooking", "i dont love the gym": the same dislike said without "hate". The
    # taste reading is what keeps it from being a bad day, so these are read the same way.
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
               r"i\s+(?:(?:just|really|properly|actually)\s+)*"
               r"(?:dont|do\s*not|don'?t)\s+(?:like|love|fancy)\s+(?P<thing>.+)$",
               re.I),
)
# A thing, not a pronoun: "i hate it" and "i hate that" point at something already said, and the
# answer to those is the composer's, which can see the whole run.
NOT_A_THING = frozenset("""it its it's that this these those them him her you me everything
    anything something stuff things thing more any all
    myself yourself himself herself itself ourselves themselves""".split())
MOST_WORDS = 12
# One instruction, trimmed the way a detail's step is trimmed, so the answer is not read out again.
STEP_WORDS = 16
SHORTER = 10
# The lead says what the step does about the objection, and the step follows it (STYLE.md, "answer
# in the first sentence"): the objection is met in the first few words, not the step alone handed
# back as if nothing had been said.
LEADS = (
    "Fair enough - this part doesn't need {thing}: {step}",
    "That's fine, this works without {thing}: {step}",
    "You can leave {thing} out of this one: {step}",
    "This one works without {thing}: {step}",
    "Then skip {thing} - the rest of it stands: {step}",
)
# A thing the person cannot use is a limit, not a dislike, and the plan has nothing to hand back
# without it: "gyms" is not something they hate - it is not open to them. The reply names the limit
# and asks for the alternative, which is the one question that decides the plan. Every frame dodges
# the copula, because the thing may be plural ("gyms") or carry its determiner ("the gym") and
# "Gyms is out" is not something anybody says.
CANNOT_USE_ASKS = (
    "No {bare}, then - what could you do instead?",
    "So {thing} won't work - what else is there?",
    "Okay, so not {thing}: what could you do instead?",
)
# The refusal of a move, said as the thing they will not do: "i dont want to kill it" after the
# mouse answer, "i dont want to take anything" after the sleep one. Nothing is disliked here - no
# thing is named to leave out of the plan - so `the_thing` does not read it, and the answer's own
# sentence that does not need the move is what they get instead.
REFUSAL = (
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright|honestly)\W+)*"
               r"i\W+(?:(?:just|really|actually|honestly|properly|definitely|absolutely|kind\s+of|"
               r"sort\s+of)\W+)*"
               r"(?:dont|do\s*not|don'?t|wouldnt|would\s*not|won'?t|wont)\s+"
               r"(?:want\s+(?:to\s+)?|wanna\s+)?(?P<move>[a-z].*)$", re.I),
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright|honestly)\W+)*"
               r"i(?:['\u2019]?d|\s+would)\s+(?:really\s+|much\s+)?rather\s+(?:not\s+)?"
               r"(?P<move>[a-z].*)$", re.I),
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright|honestly)\W+)*"
               r"i\s+(?:refuse\s+to|wouldnt\s+be\s+able\s+to|wont\s+be\s+able\s+to)\s+"
               r"(?P<move>[a-z].*)$", re.I),
)
# The words an answer uses for a move a person has just refused. A person who will not kill a
# mouse is not helped by the bait and the poison, and those are the answer's words for it: the
# family is what says the sentence being handed back does not need the move. Only moves a
# knowledge answer actually prescribes are in here, so "i dont want to upset her" is not read.
# The words a treatment goes by when the answer does not use the word the person refused. A
# spot-on or a flea tablet is a pesticide on the animal, and an answer that says "a spot-on or
# tablet from the vet" gives the spray it never names: without these, "i dont want to use chemical
# sprays" was promised "Nobody is asking you to use chemical sprays" and then handed one. A name
# of two words is written with a space; `-` is read as a space before any of this is matched, so
# `spot-on` is `spot on`.
_TREATMENT = ("spot on", "flea treatment", "flea product", "flea collar", "flea tablet",
              "flea drop", "wormer", "dewormer", "shampoo", "permethrin", "fipronil",
              "imidacloprid", "frontline", "advocate", "drops")
# The names a medicine goes by, one list for every family a refusal of one can land in: "i dont
# want to take sleeping pills" is a refusal of the melatonin card as much as of the word "pills".
_MEDICINE = ("pill", "tablet", "medicine", "medication", "dose", "drug", "supplement",
             "paracetamol", "ibuprofen", "aspirin", "painkiller", "antibiotic", "antihistamine",
             "steroid", "inhaler", "melatonin")
THE_SAME_MOVE = {
    "kill": ("kill", "trap", "snap", "poison", "bait", "pest", "exterminat"),
    "trap": ("trap", "snap", "bait", "kill"),
    "poison": ("poison", "bait", "pesticide", "chemical", "spray", "fogger", "insecticide") + _TREATMENT,
    "bait": ("bait", "poison", "trap"),
    "chemical": ("chemical", "pesticide", "spray", "insecticide", "fogger", "poison") + _TREATMENT,
    "spray": ("spray", "pesticide", "chemical", "fogger", "insecticide") + _TREATMENT,
    "fogger": ("fogger", "spray", "pesticide", "chemical", "insecticide") + _TREATMENT,
    "pellet": ("pellet", "bait", "poison", "slug"),
    # The words a health answer prescribes something by. The verb itself ("take", "taking") is
    # not one of them, or "i dont want to take anything" would be answered as if "keep walking
    # rather than taking to your bed" were a medicine.
    "pill": _MEDICINE,
    "tablet": _MEDICINE,
    "medicine": _MEDICINE,
    "medication": _MEDICINE,
    "drug": _MEDICINE,
    "take": _MEDICINE,
    "swallow": _MEDICINE,
}
# The lead says the move is not owed before it says what is, which is the whole of the answer to
# "i dont want to kill it" (STYLE.md, "answer in the first sentence"). Two pools, because the two
# cases are not the same promise: where the answer does give the move somewhere, the step handed
# over is the part that does not need it and the rest of the answer still stands, so the lead says
# only that they do not have to start there. Where the answer never gives the move at all, the
# promise is the larger one and it is exactly true.
REFUSAL_LEADS = (
    "You don't have to {move} to start. {step}",
    "Start with the part that does not need you to {move}. {step}",
    "That comes later, if at all - this first: {step}",
)
# A lead can carry an ordering of its own ("this first: {step}"), and some steps open with one
# ("Find the way in first: mice follow pipes and cables ..."), so the two together are a stutter
# and a colon run into a colon: "That comes later, if at all - this first: Find the way in first:
# mice follow pipes ...". A lead that orders is only tried when the step does not.
LEAD_ORDERS = re.compile(r"\bthis first\b", re.I)
STEP_ORDERS = re.compile(r"^(?:first|firstly|find|start|begin|sort)\b", re.I)
NOTHING_TO_DO_LEADS = (
    "You don't have to {move}. {step}",
    "None of this needs you to {move}. {step}",
    "Nobody is asking you to {move}. {step}",
)
# The same two promises for a refusal that names the thing itself rather than the doing: "i dont
# want pellets", "i dont want medication", "i dont want chemicals". A noun does not fit a sentence
# written for a doing - "You don't have to pellets", "None of this needs you to medication" - so the
# thing's leads say it as a noun. Which of the two kinds a refusal is, is read off its first word.
REFUSAL_THING_LEADS = (
    "You don't have to start with the {thing}. {step}",
    "Start with the part that needs no {thing}. {step}",
)
NOTHING_THING_LEADS = (
    "None of this needs {thing}. {step}",
    "Nobody is asking for {thing}. {step}",
    "You can leave {thing} out of this: {step}",
)
# The words in front of a noun that belong to the line rather than to the thing.
THE_NOUN = re.compile(r"^(?:the|a|an|any|my|your|our|their|his|her|some|those|these)\s+", re.I)
# The frame of a refusal, so what is left of the line once the move is taken out is the subject it
# brings of its own. A line that is nothing but the move brings none.
FRAME_WORDS = frozenset("""i dont don't do not want wanna to really just actually honestly
    properly definitely absolutely kind of sort would much rather though tho too either at all as
    well anymore now any and but so oh also yeah yep ok okay right alright""".split())
# A sentence of the answer is handed over whole when it is one move, because cutting it at its
# first clause loses the thing that makes it a move: "Find the way in first" on its own is not the
# help, and neither is the list of gaps without the "block those with wire wool and filler" it ends
# on - the mouse sentence is 57 words and it is one instruction. The cap is the length after which
# a single sentence is a paragraph rather than a move.
REFUSAL_WORDS = 60
# A dislike said of a thing that is one of the plan's own words is the plan's word for it: "i
# hate cardio" after an answer about running counts as the running.
STOP = frozenset("""the a an my our your their his her its some any and but so of to for at on
    in with about really very quite just too""".split())


def _flat(text):
    return " ".join(str(text or "").split())


def _words(text):
    return re.findall(r"[a-z']+", _flat(text).lower())


def the_thing(text):
    """The thing the person has just said they cannot stand, or None.

    None means the line is not a stated dislike on its own: a question, a longer sentence about
    someone's behaviour, or a dislike of "it", which is about what was already said.
    """
    said = _flat(text)
    if not said or "?" in said or len(said.split()) > MOST_WORDS:
        return None
    if not ack.only_a_dislike(said):
        return None
    for pattern in DISLIKE:
        found = pattern.match(said)
        if not found:
            continue
        thing = found.group("thing").strip(" .!,;:")
        if not thing or thing.lower() in NOT_A_THING:
            return None
        return thing
    return None

# The verbs a limit is said with: "i cant do gyms", "i cant afford a bike", "i cant eat dairy".
# The verb is what keeps an idiom out - "i cant believe it", "i cant wait", "i cant sleep", "i
# cant cope" are not a part of the plan being ruled out, and none of those words is here. The
# thing after the verb is still checked against NOT_A_THING, so "i cant do it" stays the
# composer's. A dislike has its own verbs and its own reader (`the_thing`), so "i cant stand the
# gym" is a grumble about the gym rather than a limit on it.
UNABLE_VERB = (r"do|use|afford|eat|have|get\s+to|go\s+to|join|manage|handle|attend|access|"
               r"buy|pay\s+for|reach|keep\s+up")
CANNOT_USE = (
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
               r"(?:the\s+problem\s+is\s+|its\s+just\s+that\s+)?"
               r"i\s+(?:(?:just|really|actually|properly|kind\s+of|sort\s+of)\s+)*"
               r"(?:cant|cannot|can\s*not|can'?t)\s+(?:" + UNABLE_VERB + r")\s+"
               r"(?P<thing>.+)$", re.I),
    # "i dont have a car", "we havent got an oven", "i dont own a car": a lack said with a thing of
    # its own. The determiner is what keeps it from reading "i dont have time" as the plan's own
    # word: "time" and the rest of the abstract ones are not things a step can be built without,
    # so they are left to the composer.
    re.compile(r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright)\W+)*"
               r"(?:the\s+problem\s+is\s+|its\s+just\s+that\s+)?"
               r"(?:i|we)\s+(?:(?:just|really|actually)\s+)*"
               r"(?:dont|do\s*not|don'?t|havent|have\s*not|haven'?t)\s+(?:got\s+)?"
               r"(?:have\s+|own\s+)?(?P<thing>(?:a|an|any|the|my|our)\s+[a-z][a-z' ]{0,24})$",
               re.I),
)
# A limit of these is not a part of a plan: "i dont have time" and "i cant afford it" are about the
# chat as a whole, not about one step that can be done another way.
NOT_A_LIMIT = frozenset("""time clue idea choice chance point reason way word answer option
    money cash budget it that this them those these""".split())


def the_thing_they_cannot_use(text):
    """The thing the person has just said they cannot do or have not got, or None.

    "i cant do gyms" after the plan for losing a stone is the same shape as "i hate exercise": one
    part of the plan is out - except that nothing in it can be handed back without the thing, so
    the answer has to ask what is left. The line has to be short and to name the thing itself, so
    "i cant do it" and "i cant believe it" are not this.
    """
    said = _flat(text)
    if not said or "?" in said or len(said.split()) > MOST_WORDS:
        return None
    for pattern in CANNOT_USE:
        found = pattern.match(said)
        if not found:
            continue
        thing = found.group("thing").strip(" .!,;:")
        core = " ".join(word for word in _words(thing) if word not in STOP)
        if not thing or not core or core in NOT_A_THING or core in NOT_A_LIMIT:
            return None
        # A limit with a reason or a second half ("i cant do gyms because of my knee") is not a
        # thing the plan can be built around: the reason is what the person is telling them, and
        # the composer's reply to that is the one to keep.
        if re.search(r"\b(?:because|since|as|though|although|but|unless|if|when)\b", thing.lower()):
            return None
        return thing
    return None


def the_move(text):
    """The move the person has just refused, in their own words, or None.

    None means the line is not a refusal of a move on its own: a question, a longer sentence, or a
    "i dont want to" about something other than a thing to do ("i dont want a row").
    """
    said = _flat(text)
    if not said or "?" in said or len(said.split()) > MOST_WORDS:
        return None
    for pattern in REFUSAL:
        found = pattern.match(said)
        if not found:
            continue
        move = found.group("move").strip(" .!,;:")
        move = re.sub(r"^(?:be\s+|have\s+to\s+|keep\s+)", "", move)
        # The words after the move that only soften it: "i dont want to take anything though" is a
        # refusal to take anything, and the "though" belongs to the line, not to the move.
        move = re.sub(r"[\s,]+(?:though|tho|too|either|really|honestly|at\s+all|as\s+well|"
                      r"any\s+more|now)$", "", move, flags=re.I)
        if not move:
            return None
        # The move has to be one a knowledge answer actually prescribes, or a light verb in front
        # of it ("i dont want to use chemicals", "i dont want to take pills") is what the answer's
        # words have to be read against.
        family = _the_family(move)
        if not family:
            return None
        return move
    return None


def _the_family(move):
    """The words the answer uses for the move the person has refused, or ().

    The key is the first word of the move that a knowledge answer prescribes, read by its stem so
    "chemicals" and "pellets" are the words they are: "i dont want to use chemicals" is a refusal
    of the chemicals, not of using.
    """
    for word in _words(move):
        if word in STOP:
            continue
        for key, family in THE_SAME_MOVE.items():
            if word.startswith(key):
                return tuple(family)
    return ()


def _has_family(words, family):
    """Whether any of these words is one the answer uses for the move (or a form of one)."""
    for word in words:
        for stem in family:
            if word.startswith(stem):
                return True
    return False


def _carries_a_move(sentence, family):
    """Whether this sentence names the move, by a word of the family or by a name of two words."""
    if _has_family(_words(sentence), family):
        return True
    said = " " + re.sub(r"[^a-z0-9]+", " ", _flat(sentence).lower()) + " "
    return any(" " + stem + " " in said for stem in family if " " in stem)


# Every word any family knows, because a promise about the whole of the answer is only true when
# the step it introduces names none of them: "my cat has fleas" / "i dont want to use chemical
# sprays" handed over "a spot-on or tablet from the vet for every pet" under "Nobody is asking you
# to use chemical sprays". The family of the refused move says what the answer calls it elsewhere;
# this says whether the step is a treatment of any kind.
_ANY_MOVE = tuple(sorted({stem for family in THE_SAME_MOVE.values() for stem in family}))


# The words a sentence opens with when it tells the person to do something. Most of them are the
# doing words the memory already keeps; these are the ones a knowledge answer uses for a job about
# the house that the shared list has no need of elsewhere.
A_DOING = topics.IMPERATIVE | frozenset("""
empty vacuum hoover dust brush scrub bleach seal strip snip trap bait sprinkle hang launder soak
""".split())
# The verbs a refusal opens on beyond the household ones, because the move people refuse is drawn
# from a smaller set than the jobs an answer gives: "i dont want to spray anything" and "i dont want
# to poison it" are the same shape as "i dont want to kill it".
REFUSED_VERBS = A_DOING | frozenset("""
kill trap bait poison spray use take put set call pay buy hire throw burn bury dig cut wash fill
""".split())
# A word that says the rest of the move is where the thing is rather than what is done with it:
# "poison in the house" names the poison, while "poison it" names the doing.
PREPOSITIONS = frozenset("""in on at round around under over by near behind inside outside from
    with about across through along""".split())


# A list a knowledge answer introduces with a frame: "The things that work: same wake-up time
# every day, no caffeine after early afternoon, ...". The items are noun phrases rather than
# instructions, so no reader of a move finds one, and the sentence is still the whole of the help
# the person was given. Only the frames the knowledge base writes with are read here, because a
# colon after a statement ("Brown tips are usually dry air: ...") introduces a reason, not a list.
FRAME = re.compile(
    r"^(?:the things? that (?:work|help|matter)|what (?:works|helps)|the fix|the trick|the plan|"
    r"the short version|what i would do|the basics)\b[^:.!?]{0,40}:\s+\S", re.I)


def _opens_on_a_verb(move):
    """True when the refusal names the doing ("kill it", "spray anything"), not the thing.

    One word is a thing: "i dont want pellets" and "i dont want poison" both name the substance. A
    second word that is a preposition leaves the first one a thing too ("poison in the house"),
    while an object after it makes it the doing ("poison it", "spray chemicals about"). Without the
    second half of this, "i dont want to spray anything" - a deck row - was read as a noun and the
    lead became "You don't have to start with the spray anything".
    """
    words = _words(move)
    if len(words) < 2 or words[0] not in REFUSED_VERBS:
        return False
    return words[1] not in PREPOSITIONS


def _the_noun(move):
    """The move as a bare noun: "the pellets" and "pellets at all" are both "pellets"."""
    return THE_NOUN.sub("", _flat(move)).strip(" .!,;:")


def _a_list_under_a_frame(one):
    """True when the sentence is a framed list of dos: "The things that work: ..., ..., and ..."."""
    said = " ".join(str(one or "").split())
    if "?" in said or not FRAME.match(said):
        return False
    tail = said.split(":", 1)[1]
    return tail.count(",") >= 2


def _a_doing(one):
    """True when the sentence tells the person to do something, rather than saying what a thing is.

    `detail._a_step` answers the same question for a sentence it can read as one move, but it
    stands aside on a long one and on a list: "Empty the wardrobe, wash or dry-clean everything
    woollen, then vacuum the drawer ..." is 46 words and is one instruction, and it is exactly the
    sentence a person who will not use chemicals needs. The first word is the reliable part - a
    reason opens on its subject ("Waking in the night is normal", "Brown tips are usually dry
    air"), and a move opens on its verb.
    """
    if detail._a_step(one):  # noqa: SLF001 - same package
        return True
    words = str(one or "").split()
    if not words:
        return False
    first = words[0].strip(",;:.-\u2014\u2013'\"").lower()
    if first in A_DOING:
        return True
    return _a_list_under_a_frame(one)


def _a_whole_step(sentence):
    """The sentence as one move, capped at `REFUSAL_WORDS` words at a clause boundary.

    The punctuation is kept as the answer wrote it: "Find the way in first: mice follow pipes and
    cables" is a frame and its content, and joined with a comma it reads as two instructions in a
    row.
    """
    said = " ".join(str(sentence or "").split())
    if not said:
        return ""
    if len(said.split()) <= REFUSAL_WORDS:
        return said if said.endswith(".") else said + "."
    cut = ""
    for piece in re.split(r"(?<=[,;:])\s+", said):
        trial = (cut + " " + piece).strip()
        if cut and len(trial.split()) > REFUSAL_WORDS:
            break
        cut = trial
    if len(cut.split()) > REFUSAL_WORDS:
        cut = " ".join(cut.split()[:REFUSAL_WORDS])
    cut = cut.strip(" ,;:-")
    return cut + "." if cut else ""


def a_move_refused(text, memory):
    """The reply for a refusal of the move the last answer gave, or None.

    Only called once the composer's reply for the turn is a receipt or the floor, so a line the
    composer has an answer for keeps it (bot/modules/greeting.py).
    """
    if not isinstance(memory, dict):
        return None
    move = the_move(text)
    if not move:
        return None
    family = _the_family(move)
    if not family:
        return None
    about = (understand(_flat(text), {}) or {}).get("topic_own")
    # A refusal that is nothing but the move ("i dont want to take pills") brings no subject of its
    # own, so the topic the move happens to have - a pill is health, the answer in front of it was
    # sleep - is not evidence that the chat has moved on. Reading it as one lost the sleep answer's
    # step: the line went to the floor ("Got it - you don't want to take pills.") a turn after
    # being told how.
    mine = set(_words(move))
    only_the_move = not [w for w in _words(text) if w not in mine and w not in FRAME_WORDS]
    for back, asked, said in repeat._recent_answers(_before_this_turn(memory, text)):  # noqa: SLF001
        if back > 2:
            continue
        if back > 1 and not repeat._about_the_same_thing(asked, said, memory):  # noqa: SLF001
            continue
        there = (understand(_flat(asked), {}) or {}).get("topic_own")
        if about and there and about != there and not only_the_move:
            continue
        # Whether the answer gives the move at all decides the promise the lead can make. An
        # answer that never gives it is the common case for a refusal - "slugs are eating my
        # hostas" never says a pellet - and there the whole of what was refused is not needed.
        gives_it = _carries_a_move(said, family)
        step = ""
        sentence = ""
        for one in re.split(r"(?<=[.!?])\s+", _flat(said)):
            if _carries_a_move(one, family):
                continue
            # Where the answer never gives the move, the lead promises the larger thing - the step
            # handed over needs none of it - so a step that is a treatment under another name
            # cannot carry that promise. Nothing is promised that the sentence does not keep.
            if not gives_it and _carries_a_move(one, _ANY_MOVE):
                continue
            piece = _a_whole_step(one)
            if not piece:
                continue
            # A sentence that is not a move is the reason, not the help ("Waking in the night is
            # normal - sleep runs in cycles of about ninety minutes").
            if not _a_doing(one):
                continue
            step, sentence = piece, one
            break
        if not step:
            continue
        if repeat._already_repeated(step, memory):  # noqa: SLF001 - said once already
            step = detail._first_clause(step)  # noqa: SLF001
            if not step or repeat._already_repeated(step, memory):  # noqa: SLF001
                return None
        pool = REFUSAL_LEADS if gives_it else NOTHING_TO_DO_LEADS
        said_move = move
        if not _opens_on_a_verb(move):
            pool = REFUSAL_THING_LEADS if gives_it else NOTHING_THING_LEADS
            said_move = _the_noun(move) or move
        if STEP_ORDERS.match(step):
            pool = tuple(lead for lead in pool if not LEAD_ORDERS.search(lead)) or pool
        reply = repeat.pick(pool, memory, text).format(move=said_move, thing=said_move, step=step)
        if sentence:
            repeat._handed_back(memory, sentence)  # noqa: SLF001 - said, if not in so many words
        return repeat._handed_back(memory, reply)  # noqa: SLF001
    return None


# The break between a frame and the move it introduces: "Change a few things you can keep doing
# rather than going on a diet: fill half the plate with vegetables ...". A colon, a dash or a
# semicolon is the same break, and the answer writes all three.
FRAME_BREAK = re.compile(r"\s*(?::|\u2014|\u2013|--|;)\s*")


def _under_its_frame(one):
    """The move inside a framed sentence, taken from the clause after its colon or dash.

    `detail._a_step` stands aside on a sentence that opens on a frame ("Change a few things you
    can keep doing rather than going on a diet: fill half the plate with vegetables, put protein in
    every meal ..."): it is long, and the part before the colon is not the move. The move is the
    clause after it, and without this the weight answer had no steps at all, so
    `i want to lose weight` / `i hate exercise` was answered "Got it - you hate exercise." - the
    receipt this whole module exists to replace. The tail has to be a move in its own right
    (`_a_doing`), so a frame followed by a fact is left alone: "Find the way in first: mice follow
    pipes and cables" is not a doing under a frame, it is the why of one.
    """
    said = " ".join(str(one or "").split())
    parts = FRAME_BREAK.split(said, 1)
    if len(parts) != 2:
        return ""
    head, tail = parts[0].strip(), parts[1].strip()
    if not head or not tail or len(head.split()) > REFUSAL_WORDS:
        return ""
    if not _a_doing(tail):
        return ""
    return _a_whole_step(tail)


def _the_frame(one):
    """The lead-in of a framed sentence ("Change a few things you can keep doing..."), or ""."""
    parts = FRAME_BREAK.split(" ".join(str(one or "").split()), 1)
    return parts[0].strip() if len(parts) == 2 else ""


def _steps(said):
    """Every instruction in the answer, in order, as (the sentence, the step, under a frame).

    The third item is True when the step was cut from under the sentence's colon rather than read
    off the sentence itself. The sentence is then still mostly unsaid - the frame is the lead-in
    and the rest of its list has not been handed over - so `answer_for` does not count the whole
    of it said, which is what kept `what else` from reaching the next clause of the list.
    """
    out = []
    for sentence in re.split(r"(?<=[.!?])\s+", _flat(said)):
        # The bot's own question still stands as the rest of the answer, so it is a step here:
        # "Then skip black pepper - the rest of it stands: tell me what is in the fridge and I
        # will pick properly" answers the objection, where the bare "Got it - you hate black
        # pepper" is a receipt. As the first thing to do it is not a step, which is why the
        # other readers keep the question out.
        step = detail._a_step(sentence, questions_are_steps=True)  # noqa: SLF001 - same package
        if step:
            out.append((sentence, step, False))
            continue
        under = _under_its_frame(sentence)
        if under:
            out.append((sentence, under, True))
    return out


def _needs_it(step, thing):
    """Whether this step leans on the thing the person has just ruled out."""
    wanted = set(_words(thing)) - STOP
    return bool(wanted & set(_words(step)))


def _leans_on_it(said, thing, asked=None):
    """Whether the answer being objected to names the thing at all.

    The dislike has to be of something the last answer actually leaned on, or every grumble in a
    chat is answered as a part of the plan: `i want to lose weight` / `i hate waiting`, `i hate
    mondays` and `i hate people` all came back as "this works without waiting/mondays/people",
    which is a nonsense reply to a person who was only letting off steam. A thing the answer never
    mentions is not what they are objecting to, so that line is left to the composer.
    """
    wanted = set(_words(thing)) - STOP
    if not wanted:
        return False
    if wanted & set(_words(said)):
        return True
    # A thing the answer never names can still be the thing it leans on when both are in the same
    # area: `i want to lose weight` / `i cant stand the gym` is about the gym, though the diet
    # answer's own words are about food. A grumble outside that area (`i hate mondays`, `i hate
    # waiting`, `i hate people`, `i hate the cold`) is not part of the plan.
    there = (understand(_flat(thing), {}) or {}).get("topic_own")
    mine = (understand(_flat(asked or ""), {}) or {}).get("topic_own")
    return bool(there and mine and there == mine)


def _before_this_turn(memory, text):
    """The memory as it stood before the line being answered, when this turn is already recorded.

    A module that runs after another has answered can see its own turn in the history, which
    counts the answer it is objecting to as two turns back rather than one - and two turns back
    has to be about the same thing the chat is still on, which by then it is not ("i want to lose
    weight" / "i cant stand the gym" was refused for that reason). The turn being answered is the
    one to drop, so the distance is counted in answers.
    """
    if not isinstance(memory, dict):
        return memory or {}
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    mine = _flat(text)
    while turns and _flat(str(turns[-1].get("user") or "")) == mine:
        turns.pop()
    if len(turns) == len(memory.get("turns") or []):
        return memory
    return dict(memory, turns=turns)


def _the_reply_for(text, memory, thing, limited):
    """The reply for a thing the line rules out of the answer above it, or None."""
    # The line's own subject, not the chat's: the reading in memory carries the chat's topic, and
    # a line that moves the chat on would then look like it is still on the old one.
    about = (understand(_flat(text), {}) or {}).get("topic_own")
    for back, asked, said in repeat._recent_answers(_before_this_turn(memory, text)):
        if back > 2:
            continue
        if back > 1 and not repeat._about_the_same_thing(asked, said, memory):
            continue
        # A stated dislike has to be of a thing the answer leaned on, or every grumble in a chat
        # is answered as part of the plan. A limit is a different claim: it is a fact about the
        # person, and it stands whatever the answer above said. "i want to lose a bit of weight
        # before summer" then "i cant do gyms" got nothing back at all, because the plan's own
        # words are about food and the line's are about the season it is for.
        if not limited:
            # The answer being objected to has to be about the same thing the line is about. A
            # line that moves the chat on ("how do i fix the tap" then "i hate exercise") is not
            # an objection to the tap answer, and handing over the tap's step would be nonsense.
            there = (understand(_flat(asked), {}) or {}).get("topic_own")
            if about and there and about != there:
                continue
            if not _leans_on_it(said, thing, asked):
                continue
        step = None
        sentence = ""
        framed = False
        for sentence, piece, under in _steps(said):
            if not _needs_it(piece, thing):
                step = piece
                framed = under
                break
        if not step:
            # Nothing in the answer can be handed back as a step that does not need the thing. For
            # a stated dislike that is the composer's turn; for a limit it is the one turn this
            # module can still take, because the person has told it what will not work and the
            # alternative is what decides the plan.
            if limited:
                ask = repeat.pick(CANNOT_USE_ASKS, memory, text).format(
                    thing=thing, bare=THE_NOUN.sub("", thing))
                return repeat._handed_back(memory, ask)  # noqa: SLF001 - said, if not in so many words
            continue
        if repeat._already_repeated(step, memory):  # noqa: SLF001 - said once already
            step = detail._first_clause(step)  # noqa: SLF001 - the shorter form is the repeat
            if not step or repeat._already_repeated(step, memory):  # noqa: SLF001
                return None
        if len(step.split()) > STEP_WORDS:
            step = detail._first_clause(step)  # noqa: SLF001 - one instruction, not a paragraph
        reply = repeat.pick(LEADS, memory, text).format(thing=thing, step=step)
        # The sentence the step was cut from counts as said as well as the line itself, because a
        # step is one clause of it: the next "what else" would otherwise cut the same sentence at
        # its frame and hand back "Change a few things you can keep doing rather than going on a
        # diet" - the lead-in to the step they have just been given, said as another part. A step
        # taken from under a frame counts its frame as said instead, not the whole sentence: the
        # rest of the frame's list ("swap sugary drinks for water or squash") has not been handed
        # over, and marking the sentence said skipped the list and handed the rate-of-loss
        # sentence after it as if it were something to do.
        if framed:
            # The step under a frame is one clause of the frame's list, and the list is what the
            # answer is made of: the step counts as said, the sentence does not. Marking the frame
            # or the sentence said made the next "what else" skip the whole of it and hand over the
            # rate-of-loss sentence after it as if it were something to do.
            repeat._handed_back(memory, step)  # noqa: SLF001 - the clause, not the sentence
        elif sentence:
            repeat._handed_back(memory, sentence)  # noqa: SLF001 - said, if not in so many words
        return repeat._handed_back(memory, reply)  # noqa: SLF001 - the next ask counts it said
    return None


def answer_for(text, memory):
    """The reply for a stated dislike of something the last answer leaned on, or None."""
    if not isinstance(memory, dict):
        return None
    thing = the_thing(text)
    if not thing:
        return None
    return _the_reply_for(text, memory, thing, False)


def answer_for_a_thing_they_cannot_use(text, memory):
    """The reply for a thing the person cannot use, or None.

    Asked only where the composer has answered with nothing - the nod that fits any message
    ("Thanks for telling me - I'm here if you want to dig into any of that") - because an answer
    that adapts to a thing they have not got ("Skip the cheese: a frittata: whisk 6 eggs...")
    already does better than any question this module could ask about it.
    """
    if not isinstance(memory, dict):
        return None
    thing = the_thing_they_cannot_use(text)
    if not thing:
        return None
    return _the_reply_for(text, memory, thing, True)
