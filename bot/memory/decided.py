"""What they settled on, and the ask that wants it back.

A chat that weighs two things and then picks one keeps the choosing line ("actually a dog",
"lets go with spain") only as a line they said: "what did i decide to get" found no reader at all
and answered with a search hedge, "what did we settle on" and "which one did i pick" were taken
by the topic's advice (dog walking, holiday packing), and "what am i getting" got the advice
again. The choosing line is a small shape, and the answer to the ask is the thing it named, so
the shape is read here and kept as a decision of its own.
"""

import re
import string

from ..compose import pick

# "ok so", "right then": the little lead-in a spoken choice usually carries.
LEAD_IN = re.compile(r"^(?:ok(?:ay)?|so|right|well|then|hmm|oh|and|but)[, ]+", re.I)

# The shapes of a choice, each with the thing they went for in `what`. The cue comes first in the
# spoken ones ("actually a dog"), the verb in the rest ("lets go with spain", "i decided on the
# blue one", "i went for fixing mine").
#
# Two weights. "i've decided on the blue one", "we settled on italy", "i picked the cat" and the
# spoken cue ("actually a dog") settle the choice on their own - somebody saying those has
# decided, whatever came before. "lets go with spain", "ill get the dog", "i went with the bike"
# are the same words a person uses for a walk ("i went for a walk"), so those only count when the
# chat had a choice on the table.
SETTLING = (
    re.compile(r"^(?:(?:actually|instead|in the end|in that case|on second thoughts?|"
               r"on second thought)[,]?\s+)(?P<what>.+)$"),
    re.compile(r"\b(?:i|we|i've|ive|we've|weve)\s+(?:have\s+|had\s+)?(?:decided|settled)\s+"
               r"(?:on|for)?\s*(?P<what>.+)$"),
    re.compile(r"\b(?:i|we)\s+(?:picked|chose|landed on|ended up with)\s+(?P<what>.+)$"),
    # "i went with the dog", "im going with the job", "im going to go with a heat pump": the verb
    # names the choosing itself, so there is nothing to weigh up first. A phrase that starts with
    # "my" or "our" is company, not a thing chosen ("i went with my mum"), and _the_thing refuses it.
    re.compile(r"\b(?:i|we)\s+(?:go|went|goes)\s+with\s+(?P<what>.+)$"),
)

# "im going for a run", "im going to go for a shower": the same verbs say a plan as often as a
# choice, so they are read apart from SETTLING and a tail that names an activity names no thing
# (see ACTIVITY). Saying a plan is a decision the person never made is a false memory that comes
# back in every later answer.
GOING = (
    re.compile(r"\b(?:i'?m|im|i am|we'?re|were)\s+(?:going|gonna)\s+(?:with|for)\s+"
               r"(?P<what>.+)$"),
    re.compile(r"\b(?:i'?m|im|i am|we'?re|were)\s+going to\s+go\s+(?:with|for)\s+"
               r"(?P<what>.+)$"),
)

# The activities a "going for" line is about. "im going for a run" is how somebody says what they
# are doing this evening, not a choice between two things.
ACTIVITY = frozenset("""run jog walk stroll hike swim shower bath drive ride cycle coffee
    drink pint curry dinner lunch breakfast supper nap kip sleep sit look wander shop shopping
    haircut massage break rest smoke fag wee pee leak""".split())
CORRECTING_LINE = (
    # "no, the blue one". The comma is the difference between a correction and a statement: "no
    # change" and "no thanks i'm fine" say what they say and choose nothing.
    re.compile(r"^(?:no|nah|nope)[,:]\s*(?:i mean(?:t)?[, ]+)?(?P<what>.+)$"),
    # "no i mean the cat": the frame carries the correction without a comma.
    re.compile(r"^(?:no|nah|nope)\s+i mean(?:t)?[, ]+(?P<what>.+)$"),
)
CHOOSING = (
    re.compile(r"\b(?:lets|let's|i'?ll|ill|we'?ll|well|i'?m going to|im going to|i'?m gonna|"
               r"im gonna|we'?re going to|were going to)\s+"
               r"(?:go|going|get|getting|have|having|take|taking|do|doing|pick|picking|choose|"
               r"choosing|book|booking|buy|buying)\s+(?:with|for)?\s*(?P<what>.+)$"),
    re.compile(r"\b(?:i|we)\s+went for\s+(?P<what>.+)$"),
    # The thing on its own, with the thinking after it: "spain i think". Only after the chat has
    # put two things in front of them, since a short line is also "nice i think".
    re.compile(r"^(?P<what>.{2,40}?),?\s+i (?:think|reckon|suppose)$"),
    # A bare thing where a question offered two: "should i get the blue coat or the green one" then
    # "the blue one". It has to start with an article to be a thing at all.
    re.compile(r"^(?P<what>(?:a|an|the|some)\s+[\w'’-]+(?:\s+[\w'’-]+)?)$"),
    # "were looking at a fiesta or a focus" then "make it the focus": the verb is the choosing, and
    # the thing is the focus. Only after two things were on the table, since "make it quick" and
    # "make it work" name nothing (IDIOM keeps them out).
    re.compile(r"\bmake it\s+(?P<what>.+)$"),
    # "lets do the focus", "ill take the focus": the same shape with the verb the shop uses.
    re.compile(r"\b(?:lets|let's|i'?ll|ill|we'?ll|well|i will|we will)\s+"
               r"(?:take|do|have)\s+(?P<what>.+)$"),
    # "we said spain" says the choice back without a choosing verb of its own.
    re.compile(r"\b(?:i|we)\s+said\s+(?P<what>.+)$"),
)

# The words that put a choice on the table: "im thinking of getting a cat or a dog", "weighing up
# a new bike or fixing mine", "should i get a cat". A weak choosing line counts when one of these
# is in the chat already, which is what makes "i went with the dog" a choice and a walk a walk.
#
# "between" carries a choice nearly every time it is said in a chat that then picks one ("i cant
# decide between spain and italy", "im torn between the bike and the train", "help me pick
# between..."), and it is the word the other shapes are spelt with, so it is what the gate reads.
OPTIONS = re.compile(r"\bor\b|\bbetween\b|\btorn\b|\bthinking of\b|\bthinking about\b|"
                     r"\bweighing up\b|\bshould i\b|\beither\b|\bwhich one\b|"
                     r"\bdecid(?:e|ed|ing)\b|cannot decide|can'?t decide|\bchoose\b|"
                     r"\bchoices?\b|\boptions\b|\bhelp me pick\b|\bvs\b", re.I)

# A phrase that begins with one of these is not a thing they chose: it is the person, a
# correction, or the rest of a question ("actually its tuesday", "actually i live in leeds").
NOT_A_THING = frozenset("""
i im i'm we we're you you're it its it's that this which what who they he she there here
me my our your his her their is are am was were do does did dont don't doesnt didn't
""".split())

# A correction said as a whole clause: "actually we booked portugal" settles the trip in the
# clause, and the noun is the thing. Only a clause about the two of us is read - "actually my
# landlord said no" is news, not a choice - and the verb has to be one of taking a thing.
CLAUSE_CHOICE = re.compile(
    r"^(?:actually|instead|in the end|turns out|it turns out)[,]?\s+"
    r"(?:i|we)(?:'ve|ve|'d|d)?\s+(?:have\s+|had\s+|just\s+)?"
    r"(?:booked|bought|got|ordered|chosen|chose|picked|reserved|taken|took|signed up for|"
    r"settled on|decided on|gone with|went with|landed on)\s+(?P<what>.+)$", re.I)

# A correction said inside the line: "actually no, a cat" chooses the cat, and "no i mean the cat"
# is the choice said again. The word is the correction and not part of the thing. "not" is left out
# on purpose: "not the green one" names the one they do not want.
CORRECTING = re.compile(r"^(?:no|nah|nope|i mean|i meant|wait|sorry)[, ]+", re.I)

# The tail a choosing line often carries, which belongs to the sentence and not to the thing.
TAIL = re.compile(r"\s+(?:instead|after all|i think|i reckon|i suppose|then|actually|"
                  r"last night|last week|yesterday|today|this morning)$", re.I)

# "lets go with the flow" agrees with the mood, it does not pick one of two things.
# The words that end a choosing verb without naming a thing: "go with the flow", "make it quick".
IDIOM = frozenset(
    ["the flow", "the grain", "the crowd", "thank you", "thanks", "the rest"]
    + """it that this them worries way idea chance problem doubt quick fast work happen up right
    better worse soon now snappy official count brief short clear easy fun nice worth cheaper
    bigger smaller louder quieter sense money""".split())

# A thing has a few words at most: "a dog", "the blue one", "fixing mine", "a fortnight in spain".
MOST_WORDS = 4

# "what did i decide to get", "what have we settled on", "have we decided", "which one did i
# pick", "so what am i
# getting", "where did i decide to go": every shape that wants back what the chat settled on. The
# reminder forms ("remind me what i decided", "what i decided", "remind me which one i went with")
# are the same ask with the frame off.
ASK = re.compile(
    r"\bwhat (?:did|do|have|had) (?:i|we) (?:decide|decided|settle(?:d)? on|choose|chose|"
    r"pick|picked|go for|went for|end up with)\b"
    r"|\bwhat (?:am|are) (?:i|we) (?:getting|going with|going for|ending up with|having)\b"
    r"|\bwhich (?:one|of (?:them|those))? (?:did (?:i|we) (?:pick|choose|go for|decide|"
    r"settle on|go with|end up with)|(?:am|are) (?:i|we) (?:getting|going with))\b"
    r"|\bwhich (?:one|of (?:them|those)) (?:i|we) (?:picked|chose|went with|went for|settled on|"
    r"decided on)\b"
    r"|\bwhere did (?:i|we) (?:decide|settle) (?:to go|on)\b"
    r"|\bso what (?:am|are) (?:i|we) (?:getting|going with|doing)\b"
    r"|\bwhat (?:i|we) (?:decided|chose|picked|settled on|went with|went for)\b"
    r"|\b(?:have|has|had|did) (?:i|we) (?:decide|decided|picked|chosen|chose|settled)\b"
    r"|\bare (?:we|you) decided\b"
    r"|\bwhat was (?:decided|chosen|picked|settled on)\b"
    r"|\bwhat (?:did|do) (?:i|we) (?:land|opt) (?:on|for)\b"
    r"|\bwhich did (?:i|we) (?:go for|pick|choose|decide on|settle on)\b"
    r"|\bwhat did (?:i|we) say (?:i|we)(?:'d| would) (?:get|choose|pick|go for|have)\b"
    r"|\bremind me (?:of|about) (?:the|our) choice\b"
    r"|\bdid (?:i|we) (?:go with|go for|settle on|pick|choose|decide on|end up with)\b")

# An ask that names the answer it expects: "did we settle on spain". A yes or a no is the
# answer a person wants there, and the choice on record says which one it is.
GUESSING_ASK = re.compile(
    r"\bdid (?:i|we) (?:go with|go for|settle on|pick|choose|decide on|end up with)\s+"
    r"(?P<what>[^?.!,]+)", re.I)

# Said back to them, first person is second person: "fixing mine" is "fixing yours".
TO_YOU = {"i": "you", "im": "you're", "i'm": "you're", "me": "you", "my": "your",
          "mine": "yours", "myself": "yourself", "we": "you", "our": "your", "ours": "yours",
          "ive": "you've", "i've": "you've"}


# The deciding verb said again inside the line: "actually ive decided on greece" puts the frame
# after the lead-in word, and the frame is not part of the thing.
INNER_DECIDE = re.compile(
    r"^(?:i|we)(?:'ve|'d|ve|d| have| had)?\s+(?:decided|settled|chosen|chose|picked|gone|"
    r"went|going|go)\b\s*(?:on|with|for)?\s*", re.I)


def _the_thing(phrase):
    """The chosen thing as the store should keep it, or None when the phrase is not one."""
    phrase = " ".join(str(phrase or "").split()).strip(" ,.;:!?")
    while True:
        trimmed = CORRECTING.sub("", phrase).strip(" ,.;:!?")
        if trimmed == phrase:
            break
        phrase = trimmed
    while True:
        trimmed = INNER_DECIDE.sub("", phrase).strip(" ,.;:!?")
        if trimmed == phrase:
            break
        phrase = trimmed
    while True:
        trimmed = TAIL.sub("", phrase).strip(" ,.;:!?")
        if trimmed == phrase:
            break
        phrase = trimmed
    if phrase.lower() in IDIOM:
        return None
    if re.fullmatch(r"[\d.,]+", phrase):
        # "no i mean 43" puts a number right; a number is not a thing chosen.
        return None
    words = phrase.split()
    # "i decided to wait for the new phone" is a decision stated as a verb phrase, and those run
    # longer than the noun phrases ("the blue one") the four-word limit is there for.
    verb_phrase = len(words) > 1 and words[0].lower() == "to"
    if not words or len(words) > (MOST_WORDS + 4 if verb_phrase else MOST_WORDS):
        return None
    if words[0].lower() in NOT_A_THING:
        return None
    if any(word.lower() in NOT_A_THING for word in words[1:]):
        # "a dog and i" is not a thing, and neither is "its tuesday" in the middle of a phrase.
        return None
    return phrase


# The words a line puts in front of the two things it names ("we were thinking italy or spain",
# "im going to spain in may or june"): the ask names the two things and not the frame.
OPTION_FILLER = frozenset("""im i we you they should shall do does did get gets getting got
    go goes going gonna want wants wanted need needs like rather prefer thinking thought
    about of between torn pick picking choose choosing decide decided deciding help me if
    maybe well so and then also still just were was are is am been being cant can't cannot
    unsure whether if better best worse worth it to up weighing""".split())


def _two_things(said):
    """The two things a line put side by side, as "X or Y", or None.

    Used by the ask that finds nothing settled: naming the two things the chat left open is an
    answer, and "Nothing settled yet." on its own tells the person less than they told us.
    """
    low = " ".join(str(said or "").lower().split()).strip(" ?.!,")
    left = right = ""
    if " between " in low and " and " in low.split(" between ", 1)[1]:
        head = low.split(" between ", 1)[1]
        left, right = head.split(" and ", 1)
    elif " or " in low:
        cut = low.rfind(" or ")
        left, right = low[:cut], low[cut + 4:]
    else:
        return None
    left_words = left.split()
    while left_words and left_words[0].strip(",;:") in OPTION_FILLER:
        left_words.pop(0)
    right_words = right.split()[:3]
    while right_words and right_words[-1].strip(",;:") in OPTION_FILLER:
        right_words.pop()
    left = " ".join(left_words[-3:]).strip(" ,;:")
    right = " ".join(right_words).strip(" ,;:")
    if not left or not right:
        return None
    if left in IDIOM or right in IDIOM or left in NOT_A_THING or right in NOT_A_THING:
        return None
    return left + " or " + right


def _options_since(memory, line):
    """The pair put on the table after the choice on the book was made, or None.

    "im thinking of getting a cat" / "actually a dog" is a choice; a later "we were thinking italy
    or spain" is a new question, and answering it with the dog answers a chat that is over.
    """
    turns = list((memory or {}).get("turns") or [])
    key = " ".join(str(line or "").lower().split())
    if not key:
        return None
    seen = False
    for turn in reversed(turns[-6:]):
        said = " ".join(str((turn or {}).get("user") or "").split())
        if not said:
            continue
        if said.lower() == key:
            seen = True
            break
        if asks(said) or not OPTIONS.search(said):
            continue
        pair = _two_things(said)
        if pair:
            return pair
    return None


def _the_pair_left_open(memory):
    """"italy or spain" for the last line that put two things in front of them, or None."""
    for turn in reversed(list((memory or {}).get("turns") or [])[-3:]):
        said = str((turn or {}).get("user") or "")
        if not said or asks(said) or not OPTIONS.search(said):
            continue
        pair = _two_things(said)
        if pair:
            return pair
    return None


def _as_typed(text, thing):
    """The thing with the case the person typed it in: "Spain" stays, "spain" stays lower."""
    words = thing.split()
    if not words:
        return thing
    pattern = r"\b" + r"\s+".join(re.escape(word) for word in words) + r"\b"
    match = re.search(pattern, str(text or ""), re.I)
    return match.group(0) if match else thing


def read(text):
    """The choice a line makes: {"what": thing, "settled": bool}, or None.

    "settled" says whether the line settles the choice by itself ("i've decided on the blue one",
    "actually a dog") or only when the chat had options on the table ("lets go with spain").
    """
    line = " ".join(str(text or "").lower().split())
    if not line or "?" in line or len(line.split()) > 14:
        return None
    if asks(line):
        # "did i go with a cat" quotes the choosing verb and chooses nothing: a question about
        # the choice must never become the choice.
        return None
    while True:
        trimmed = LEAD_IN.sub("", line)
        if trimmed == line:
            break
        line = trimmed
    clause = CLAUSE_CHOICE.search(line)
    if clause:
        thing = _the_thing(clause.group("what"))
        if thing and not _an_activity(thing):
            return {"what": _as_typed(text, thing), "settled": True}
    for pattern in CORRECTING_LINE:
        match = pattern.search(line)
        if match:
            thing = _the_thing(match.group("what"))
            if thing:
                return {"what": _as_typed(text, thing), "settled": False, "corrects": True}
    for pattern in GOING:
        match = pattern.search(line)
        if not match:
            continue
        thing = _the_thing(match.group("what"))
        if thing and not _an_activity(thing):
            return {"what": _as_typed(text, thing), "settled": True}
    for patterns, settled in ((SETTLING, True), (CHOOSING, False)):
        for pattern in patterns:
            match = pattern.search(line)
            if not match:
                continue
            thing = _the_thing(match.group("what"))
            if thing:
                return {"what": _as_typed(text, thing), "settled": settled}
    return None


def extract(text):
    """The thing a choosing line settled on, or None.

    "actually a dog" is one; so is "lets go with spain", "ive decided on the blue one" and "i
    think ill go with fixing mine". "actually i live in leeds" is a correction, "actually its
    tuesday" puts a day in place, and neither settles anything, so both are left alone.
    """
    reading = read(text)
    return reading["what"] if reading else None


def _an_activity(thing):
    """True when the thing after a going verb is something a person does, not something chosen."""
    words = [w.strip(" ,.;:!?").lower() for w in str(thing or "").split()]
    while words and words[0] in ("a", "an", "the", "some", "my", "our"):
        words = words[1:]
    return bool(words) and words[0] in ACTIVITY


def _a_bare_thing(said):
    """True when a line is one short thing and nothing else: "cat", "the blue one"."""
    line = " ".join(str(said or "").lower().split()).strip(" ,.;:!?")
    if not line or "?" in line:
        return False
    words = line.split()
    if len(words) > 2 or any(w in NOT_A_THING for w in words):
        return False
    return all(w.isalpha() for w in words) and len(words[-1]) > 2


def _options_on_the_table(memory):
    """Whether the last thing said put a choice in front of them.

    Only the two turns before the choosing line count. A choice is made right after the options
    are named ("i cant decide between spain and italy" then "lets go with spain"), and a word like
    "between" from three turns back is about something else by then: it is what made "im torn
    between the bike and the train", "ill go with the train" and then "i went for a walk" file the
    walk as a choice.
    """
    for turn in reversed(list((memory or {}).get("turns") or [])[-2:]):
        said = str((turn or {}).get("user") or "")
        if str((turn or {}).get("bot") or "") and not said:
            continue
        if _a_bare_thing(said):
            # "cat" on its own is a thing said out loud with the other one left unsaid, which is
            # what makes "no, a dog" a correction of it.
            return True
        if asks(said):
            # "remind me which one i went with" is a question about the choice, not two things on
            # the table, even though it says "which one".
            continue
        if OPTIONS.search(said):
            return True
    return False


# The words a line reaches for a choice with, including the ones this reader cannot name the thing
# out of ("im going to take the train", "i went for a curry last night"). A denial after one of
# those contradicts the person, which is worse than the hedge this module replaces.
REACHES_FOR_A_CHOICE = re.compile(
    r"\b(?:go|goes|going|went)\s+(?:with|for)\b"
    r"|\b(?:settled|decided|landed|ended up)\s+(?:on|for|with)\b"
    r"|\b(?:(?:going|gonna)\s+to\s+)?(?:take|taking|took|book|booking|pick|picked|choose|"
    r"chose|choosing)\s+(?:the|a|an|my|that|this)\b"
    r"|\b(?:picked|chose|choosing)\b", re.I)


# A question is not a choice: "is it better to walk or take the bus" puts two things on the
# table, so the ask after it is answerable, and the words "take the bus" are not a choice made.
OPENING_QUESTION = re.compile(r"^(?:is|are|was|were|should|shall|do|does|did|can|could|would|"
                              r"will|what|which|how|where|when|why|any|if)\b", re.I)


def _a_choice_reached_for(memory, kept_line=None):
    """Whether the last thing they said is a choice this reader could not name.

    A line the store already holds is the one exception: it was named when it was said.
    """
    for turn in reversed(list((memory or {}).get("turns") or [])[-3:]):
        said = " ".join(str((turn or {}).get("user") or "").split())
        if not said or asks(said):
            continue
        if "?" in said or OPENING_QUESTION.match(said):
            continue
        if kept_line and said.lower() == str(kept_line).lower():
            return False
        return bool(REACHES_FOR_A_CHOICE.search(said))
    return False


# The ask names the deciding itself: "what did i decide to do" is a question about a decision, and
# "did i go for a run" is a question about the run.
DECIDING_WORD = re.compile(r"\b(?:decid|settl|pick|cho(?:o|s)|decided|deciding)\w*", re.I)


def _a_plan_since(memory):
    """Whether the last thing they said was a plan still going: "im going for a run".

    A plan is read and refused rather than unreadable, so the ask after it can be answered with
    the truth ("Nothing settled yet.") instead of the module standing down.
    """
    for turn in reversed(list((memory or {}).get("turns") or [])[-3:]):
        said = " ".join(str((turn or {}).get("user") or "").split())
        if not said or asks(said) or "?" in said:
            continue
        for pattern in GOING:
            match = pattern.search(said.lower())
            if match:
                return bool(_an_activity(_the_thing(match.group("what")) or ""))
        # "i went for a curry last night" is read and refused as a choice, and the ask after it is
        # left alone: a report of what they did is not a plan that is still open.
        return False
    return False


def observe(text, memory):
    """Keep the thing they settled on. A later choice is the one they settled on."""
    reading = read(text)
    if not reading or not isinstance(memory, dict):
        return None
    if reading.get("corrects") and not (the_decision(memory) or _options_on_the_table(memory)):
        # "no i mean the cat" is the choice said again: it needs one on record, or two things on
        # the table, to be a choice at all. With neither, "no thanks" stays a no.
        return None
    if not reading["settled"] and not reading.get("corrects") and not _options_on_the_table(memory):
        # "i went for a walk" is not a choice, and neither is "lets go with the flow": the same
        # words carry a choice only when the chat had one to make.
        return None
    memory["decided"] = {"what": reading["what"],
                          "line": " ".join(str(text or "").lower().split())}
    return memory["decided"]


# A chat that settled the month of a trip has settled something. Answered "where did we settle on"
# two lines after the bot itself said "you are going to Cornwall in September", this reader said
# "You haven't settled on one yet." - the chat contradicted itself, and the one thing it did settle
# was on the record the whole time. The plan is what a chat settles when it settles no choice.
PLAN_KEYS = ("plans", "plan")


def _the_plan_on_record(memory):
    """The plan the chat has already said back to them, latest first, or None.

    A plan the bot never said back is not one the chat settled: "im learning to swim" files the
    plan "Swim", and "you settled on Swim" is a decision they never made. A plan the bot has
    already confirmed - "Got it - you are going to Cornwall in September." - is the chat settled,
    and the ask about it must not be told the chat settled nothing.
    """
    user = (memory or {}).get("user") if isinstance(memory, dict) else None
    if not isinstance(user, dict):
        return None
    plans = [user.get("plan")] if user.get("plan") else []
    if isinstance(user.get("plans"), list):
        plans = list(user["plans"]) + plans
    for plan in reversed([p for p in plans if p]):
        plan = " ".join(str(plan or "").split())
        words = [w for w in plan.lower().replace(",", " ").split() if len(w) > 2]
        if words and said_back(memory, words):
            return plan
    return None


def said_back(memory, words):
    """Whether an earlier reply of the bot already said these words."""
    for turn in list((memory or {}).get("turns") or []):
        said = str((turn or {}).get("bot") or "").lower()
        if said and all(w in said for w in words):
            return True
    return False


def the_decision(memory):
    """The choice on record, or None."""
    held = (memory or {}).get("decided") if isinstance(memory, dict) else None
    if isinstance(held, dict) and str(held.get("what") or "").strip():
        return held
    return None


def asks(text):
    """Whether the line is asking back what the chat settled on."""
    low = " ".join(str(text or "").lower().split())
    return bool(ASK.search(low))


def the_guess(text):
    """The thing an ask expects to hear back ("did we settle on spain"), or None."""
    low = " ".join(str(text or "").lower().split()).strip(" ?.!,")
    match = GUESSING_ASK.search(low)
    if not match:
        return None
    return _the_thing(match.group("what"))


def _the_same_thing(said, held):
    """Whether the thing guessed is the thing on record: "spain" is "spain in may"."""
    one = " ".join(str(said or "").lower().split()).strip(" ?.!,")
    other = " ".join(str(held or "").lower().split()).strip(" ?.!,")
    if not one or not other:
        return False
    if one.startswith("to "):
        one = one[3:]
    if other.startswith("to "):
        other = other[3:]
    if one == other or one in other or other in one:
        return True
    # The same decision said twice, once as a gerund: "giving up sugar" for "give up sugar".
    first, second = one.split(), other.split()
    if len(first) > 2 and len(second) > 2 and first[1:] == second[1:]:
        verb_one, verb_two = first[0], second[0]
        return len(verb_one) > 2 and len(verb_two) > 2 and verb_one[:3] == verb_two[:3]
    return False


def _said_to_you(thing):
    """The thing in second person, in the case they typed it: "fixing mine" -> "fixing yours"."""
    words = []
    for word in str(thing or "").split():
        bare = word.strip(".,!?;:")
        swapped = TO_YOU.get(bare.lower())
        words.append(swapped if swapped else word)
    return " ".join(words)


def _a_verb_phrase(thing):
    """True for a decision stated as what they will do: "to give up sugar", "to take the job"."""
    words = str(thing or "").split()
    return len(words) > 1 and words[0].lower() == "to"


def _the_choice_said(thing):
    """The choice in a sentence: "the blue one" -> "You went with the blue one."."""
    if _a_verb_phrase(thing):
        # "You went with to give up sugar" is broken English, and the person's own words have the
        # shape the sentence wants.
        return "You decided " + thing + "."
    return "You went with " + thing + "."


def _at_the_start(thing):
    """The thing where it opens the sentence: "fixing yours" -> "Fixing yours"."""
    return thing[:1].upper() + thing[1:] if thing else thing


# The words the ask itself is made of. What is left of a line once they are taken off names
# something of its own: "what did i decide about the boiler" is about the boiler, and the choice
# on record is about something else.
ASK_FRAME = frozenset("""what which one ones did do does have has had i we you me us my our
    decide decided deciding settle settled settling on choose chose chosen pick picked picking
    go went going for get gets getting got have having take took end ended up with am are was
    were so about of to the a an it that this them those remind remember again the choice
    our land landed opt opted for say said would will should and then there where when why
    how who whose much many long kind sort time place""".split())

# A word that names an answer rather than a thing, so it says nothing about what the ask is on.
NOT_A_SUBJECT = frozenset("""one ones one's best better worse right thing things way again now
    then really please just also still ever again""".split())

# The doing the ask is phrased with, which is not a thing the ask is about: "what did i decide to
# make" names the making, not a subject, so it is no reason to stand down from a choice the chat
# made. "im making a curry tonight" / "actually a stir fry" / "what did i decide to make" got the
# stir fry entry's cooking steps, because "make" read as a thing the choice on record was not
# about. Only verbs a choice ask is phrased with, and never a word that is as often the thing
# chosen: "what did i decide to read" could be either, so "read" is not here and that ask stands
# down as it did before, and "what did i decide about the boiler" still names the boiler.
DOING = frozenset("""make makes made making cook cooks cooked cooking eat eats eating drink
    drinks drinking buy buys buying wear wears wearing watch watches watching learn learns
    learning study studies studying grow grows growing plant plants planting build builds
    building serve serves serving""".split())

# A verb followed by "with" can ask about the company the thing is in, and only some verbs can:
# "what did i decide to drink with it" after a curry became a stir fry is a question about the
# drink, and the drink entry has that answer - read as the asking it became a false memory ("You
# went with a stir fry." when nothing was said about the drink). The verb there names something
# alongside the dish, so what follows "with" is the subject and the subject stands us down.
#
# `cook`, `make` and `eat` are not in this set, and they must not be: they are the act the choice
# was made in, so "what did i decide to cook with it" and "what did i decide to eat with" point
# back at the dish, and the memory is the right answer. @olive-trumpet measured all three on
# #7471: standing them down left a punt or a shrug where base said "You settled on a stir fry."
COMPANION_VERBS = frozenset("""drink drinks drinking serve serves serving have has having
    order orders ordering pair pairs pairing pour pours pouring""".split())
COMPANION = re.compile(r"\b(?:%s)\s+(?:with|alongside)\b" % "|".join(sorted(COMPANION_VERBS)))


def _asks_about_another_thing(text, held):
    """True when the ask names a thing the choice on record is not about.

    "my boiler is playing up" / "what did i decide about the boiler": the person is asking about
    the boiler, and the chat never settled on one, so naming the dog would be a false memory and
    "nothing settled yet" would throw away the boiler answer. The module stands down instead.
    """
    said = " ".join(str(text or "").lower().split())
    held_text = " ".join(str((held or {}).get("what") or "").lower().split())
    if COMPANION.search(said):
        # "what did i decide to drink with it" asks about the drink, not the dish.
        return True
    words = [w.strip(string.punctuation) for w in said.split()]
    named = [w for w in words
             if w and w not in ASK_FRAME and w not in NOT_A_SUBJECT and w not in DOING
             and len(w) > 2 and not w.isdigit()]
    if not named:
        return False
    return not any(w in held_text or (len(w) > 3 and held_text.startswith(w[:4]))
                   for w in named)


def answer(text, memory):
    """The reply to an ask that wants the choice back, or None when the line is not one.

    With nothing settled the answer says so: a choice the chat never made is not a fact, and
    "you haven't picked one yet" is the one true thing to say.
    """
    if not asks(text):
        return None
    held = the_decision(memory)
    if held:
        moved_on = _options_since(memory, held.get("line"))
        if moved_on and not _a_choice_reached_for(memory, held.get("line")):
            # They went on to another pair of things ("we were thinking italy or spain" after the
            # dog), so the choice on the book is about an earlier chat, and the ask is about this.
            return pick(["Nothing settled yet: " + moved_on + ".",
                         "Not yet: " + moved_on + ".",
                         "Neither one yet: " + moved_on + "."], memory,
                        seed_text=str(text or ""))
    if held and not the_guess(text) and _asks_about_another_thing(text, held):
        # The ask names a thing of its own and the choice is not about it: the answer module
        # knows the boiler, and this reader has nothing to say about it.
        return None
    if held and _a_choice_reached_for(memory, held.get("line")):
        # They said another choice in words this reader does not have. The one on record may be
        # the older one, and naming it would answer a question they did not ask.
        return None
    if not held:
        if _asks_about_another_thing(text, held) and not the_guess(text):
            # "what did i decide about the boiler" with nothing settled: the ask is about the
            # boiler, and the module that knows boilers should answer it.
            return None
        plan = _the_plan_on_record(memory)
        if (plan and DECIDING_WORD.search(str(text or ""))
                and not _asks_about_another_thing(text, {"what": plan})):
            # "what did we settle on" with a plan on record answers with the plan: the chat did
            # settle it, and saying it settled nothing is the one answer that is not true.
            return pick(["You settled on " + plan + ".",
                         "That's settled: " + plan + ".",
                         "The chat settled it: " + plan + "."], memory,
                        seed_text=str(text or ""))
        if _a_choice_reached_for(memory):
            if not (DECIDING_WORD.search(str(text or "")) and _a_plan_since(memory)):
                # They said a choice in words this reader does not have. Saying "nothing settled"
                # after it tells the person the chat did not happen, so the module stays quiet.
                # A plan is the exception: "i went for a walk" then "what did i decide to do" has
                # a true answer, and the person asked about the deciding.
                return None
        pair = _the_pair_left_open(memory)
        if pair:
            # "which one did we pick" after "we were thinking italy or spain" is answered with the
            # two things the chat left open, not a bare "nothing settled".
            return pick(["Nothing settled yet: " + pair + ".", "Not yet: " + pair + ".",
                         "Neither one yet: " + pair + "."], memory,
                        seed_text=str(text or ""))
        return pick(["Nothing settled yet.", "You haven't picked one yet.",
                     "You haven't settled on one yet."], memory,
                    seed_text=str(text or ""))
    thing = _said_to_you(held.get("what"))
    guess = the_guess(text)
    if _a_verb_phrase(held.get("what")):
        # A decision stated as what they will do keeps that shape in every tail: the noun-phrase
        # tails turn "to give up sugar" into "You went with to give up sugar".
        if guess:
            if _the_same_thing(guess, held.get("what")):
                return pick(["That's right: you decided " + thing + ".",
                             "Yes - you decided " + thing + "."],
                            memory, seed_text=str(text or ""))
            return pick(["Not quite: you decided " + thing + ".",
                         "The other one: you decided " + thing + "."],
                        memory, seed_text=str(text or ""))
        return pick(["You decided " + thing + ".",
                     "You decided " + thing + ", in the end."],
                    memory, seed_text=str(text or ""))
    if guess:
        # "did we settle on spain" wants a yes or a no, and the record says which.
        if _the_same_thing(guess, held.get("what")):
            return pick(["Yes - " + thing + ", in the end.",
                         "That's right: " + thing + ".",
                         "Yes, " + thing + "."],
                        memory, seed_text=str(text or ""))
        return pick(["No - " + thing + ", in the end.",
                     "Not quite: " + thing + ", in the end.",
                     "The other one: " + thing + "."],
                    memory, seed_text=str(text or ""))
    return pick([_at_the_start(thing) + ", in the end.",
                 "You settled on " + thing + ".",
                 _the_choice_said(thing)],
                memory, seed_text=str(text or ""))
