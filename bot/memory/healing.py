"""A healing ask answered from the card the person was just given.

"my back hurts" gets a paragraph about what helps, and the next line is
"how long will it take to heal". The paragraph is what the bot knows about that back, and the
span in its first sentence - "settles in two to six weeks" - is the answer to the ask. On its own
the ask names nothing, so the readers that follow it look for an entry keyed on the words of the
line, and the entries that answer "how long to heal" are keyed on bones and on sprains:

    my knee hurts / how long does it take to get better -> "Two days."
    my shoulder hurts / how long does it take to heal   -> "About six weeks for most bones ..."
    i cut my finger / how long will it take to heal     -> "About six weeks for most bones ..."

"Two days" is the icing in the knee card ("for the first two days") read back as the healing time,
and the bones card answers a cut finger because "heal" is its word. So a recovery ask is answered
from the answer already on the screen: the span that answer states, or, where it states none, the
plain fact that what the bot has is the care rather than the timeline. A figure picked up from
another card is wrong, and being wrong about how long a body takes is worse than saying so.

Only two things make a line this kind of ask: it asks how long, and it names recovering, healing,
getting better, clearing up or going away. Only a care card in front of it makes the turn this
module's: "im learning to drive" / "how long will it take to get better" is answered by the
driving entry, and a card that states no care is not a body being looked after.
"""
import re

# How long, and then recovering. The verb can follow "take" ("how long will it take to heal") or
# be the whole ask ("how long till it heals", "how long before it clears up"), and people type
# the pronoun or leave it out ("how long to heal", "how long will this take to go").
ASKS = re.compile(
    r"\bhow long\b[^.?!]{0,40}?"
    r"\b(?:heal|heals|healing|mend|mends|mending|recover|recovers|recovering|"
    r"get better|gets better|getting better|get over|gets over|getting over|"
    r"clear up|clears up|clearing up|go away|goes away|going away|die down|dies down|"
    r"settle down|settles down|stop hurting|ease off|eases off|get well|be better|"
    r"feel better|feels better|feel normal|back to normal|"
    r"be like this|stay like this|stays like this|be gone|keep me off my feet|"
    r"last|lasts|lasted)\b", re.I)

# "last" is here and a bare "take" is not: "how long will it take" after "i want to lose a stone"
# is answered by the weight card, whose only care word is "see a GP", and a healing line there is
# a shrug in place of a good answer. An ask that says what it wants healed ("take to heal") is
# matched by the verb.

# ... and the words of the ask itself: a line that names a body of its own ("how long does a
# broken wrist take to heal") is answered by the entry for that body, and the card in front is
# not needed for it.
NAMES_ITS_OWN = re.compile(
    r"\bhow long (?:does|do|will|would|should|is|are|can|could)\b", re.I)

# The care in an answer, in the words the cards use for it. A card is a body being looked after
# when it says what to do now; a paragraph about learning to drive says none of this.
CARE = re.compile(
    r"\b(?:ice it|ice for|rest it|rest the|raise it|keep it up|wrap it|press a clean|"
    r"cool running water|paracetamol|ibuprofen|antihistamine|hydrocortisone|"
    r"see a gp|ring the surgery|get it looked at|get it checked|have it looked at|"
    r"ease off|keep it moving|keep moving|plenty of (?:fluids|water)|drink plenty|"
    r"prop yourself up|a spoonful of honey|warm drinks|early night|stay off it)\b", re.I)

# A length of time, in the shapes the cards write it: "two to six weeks", "a week to ten days",
# "one to three weeks", "a couple of days", "10 days".
_SPAN = (r"(?:\d+|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a couple of"
         r"|a few|several)(?:\s*(?:to|or|-)\s*(?:\d+|one|two|three|four|five|six|seven|eight"
         r"|nine|ten|eleven|twelve|a few))?\s*"
         r"(?:hours?|days?|weeks?|fortnights?|months?|years?)")

# The ways a card says how long a thing takes to mend. Each is a word that makes the length after
# it a timeline rather than a period of doing something: the icing that goes on "for the first two
# days" is not one of these, which is the whole point - "two days" is what a knee was answered
# with. "Take it easy for a day or two" is a period of rest and is not one either: "take" is here
# only as "takes two weeks", with the length straight after it.
_TIMELINE = re.compile(
    r"\b(?P<verb>settles?|settled|eases?|eased|heals?|healed|mends?|mended|recovers?|recovered|"
    r"lasts?|lasted|clears? up|cleared up|fades?|faded|dies down|die down|goes away|go away|"
    r"gets? better|get better|getting better|is properly better|are properly better|"
    r"properly better|is better|are better|feels? normal|back to normal|takes|took|"
    r"hangs? on|hang on|lingers?|settling|easing|healing|mending)\b"
    r"(?:[^.?!;:]{0,30}?)\b(?:in|within|after|for|about|around)?\s*"
    r"(?P<span>" + _SPAN + r")", re.I)

# Where a card gives the length without a verb: "Two to three weeks." as a sentence of its own.
_BARE_SPAN = re.compile(r"^\s*(?:about|around|roughly|usually)?\s*(?P<span>" + _SPAN + r")\s*[.!]?\s*$",
                        re.I)

# A short reply that is only a length: "Two days.", "Two to three weeks." It is the number alone,
# so the person cannot see what it is a number for, and it is the shape the wrong answers take.
_ONLY_A_SPAN = re.compile(r"^\s*(?:about|around|roughly|usually)?\s*" + _SPAN + r"\s*[.!]?\s*$", re.I)

# What the bot says when the card it gave states the care and not the timeline. It has to be
# honest without being a shrug, and it must not carry a figure of its own: the whole fault here
# is a figure that came from somewhere else. Three wordings, because the same ask twice in a row
# is answered twice, and a friend does not say the same sentence twice.
NO_TIMELINE = (
    "I know what helps with it, but not how long it takes to mend - I'd rather not guess at a "
    "number. If it's no easier after a few days, that's the point to get it looked at.",
    "How long it takes is the part I would be guessing at. What I have is what helps in the "
    "meantime, and if there's no change in a few days, that's when to get it looked at.",
    "I'd rather say I don't have a time than make one up. Keep doing what's in the card above and "
    "give it a few days - if it's no better by then, get it looked at.",
)

# The same line where the card has a step to hand over: the step goes first, because it is the
# helpful half and because a later "and what should i do" reads the opening of the answer on the
# screen for the step to give back - a disclaimer in front of it was read as the step, and
# "what should i do" came back as "The thing to do first: I can't put a time on that one, sorry".
NO_TIME_THEN_STEP = (
    "{step} How long it takes is the part I would be guessing at.",
    "{step} I can't say how long it will take - the care is the part I know.",
    "{step} Past that I can't put a time on it, sorry.",
)

# A reply that already says the bot has no figure. It is a shrug on its own, and the search hedge
# in particular reads as the bot disowning its own card, but it is honest and it is not wrong, so
# it is left where a card states no timeline: replacing it costs more than it gains.
HEDGE = re.compile(
    r"\b(?:i'm not sure about that one|i don't know|beyond what i know|i'd rather not guess|"
    r"a quick search|search online|can't put a time on|would be guessing at|up to date on that"
    r"|beyond me)\b", re.I)

SENTENCE = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"[a-z']+")


def asks(text):
    """Whether the line asks how long something takes to mend."""
    line = str(text or "")
    if not line.strip() or not ASKS.search(line):
        return False
    return True


def the_timeline(answer):
    """The sentence of an answer that states how long a thing takes to mend, or "".

    The sentence is cut at the end of the length itself, because what follows it in a card is the
    next thing to do rather than the answer: "Most back pain is muscular and settles in two to six
    weeks, and staying active is what helps most: keep walking ..." answers the ask up to "weeks".
    """
    text = str(answer or "")
    if not text.strip():
        return ""
    for sentence in SENTENCE.split(text):
        match = _TIMELINE.search(sentence)
        if not match:
            continue
        end = match.end("span")
        clause = sentence[:end].rstrip(" ,;:-")
        if not clause:
            continue
        return clause[:1].upper() + clause[1:] + "."
    return ""


def _the_same_length(reply, timeline):
    """Whether a reply that is only a length says the length the timeline says."""
    said = _ONLY_A_SPAN.match(str(reply or ""))
    if not said:
        return False
    if not timeline:
        return False
    return said.group(0).strip(" .!").lower() in timeline.lower()


# The words of the ask itself, and the words any answer about the body shares. A reply that
# carries only these is not about the same thing: "how long does it take to get better" shares
# "take" with a paragraph about bones in the leg, and that is not a subject.
_ASK_WORDS = frozenset((
    "how", "long", "will", "would", "should", "could", "does", "take", "takes", "took", "get",
    "gets", "getting", "got", "heal", "heals", "healing", "mend", "mends", "mending", "recover",
    "recovers", "recovering", "better", "clear", "clears", "clearing", "away", "away", "goes",
    "going", "gone", "settle", "settles", "settling", "down", "ease", "eases", "easing", "time",
    "till", "until", "before", "after", "much", "many", "usually", "normal", "back", "stop",
    "feel", "feels", "well", "this", "that", "there", "then", "than", "them", "they", "their",
))


def _stem(word):
    """A word with its ending taken off, so "sprained" and "sprain" count as the same thing.

    Only the endings that change nothing about the subject: a bone is not "boned", and "knees"
    and "knee" are the same knee.
    """
    for ending in ("ing", "ed", "es", "s"):
        if word.endswith(ending) and len(word) - len(ending) >= 4:
            return word[:-len(ending)]
    return word


def _carries(text):
    """The words of a line that say what it is about, without the words of the ask."""
    return {_stem(word) for word in WORD.findall(str(text or "").lower())
            if len(word) > 2 and word not in _ASK_WORDS}


def _said_before(memory, keep=2):
    """The user's own lines before this turn, newest first."""
    lines = []
    for turn in reversed(list((memory or {}).get("turns") or ())):
        if isinstance(turn, dict) and turn.get("user"):
            lines.append(str(turn.get("user")))
            if len(lines) >= keep:
                break
    return lines


def derived(memory):
    """Whether the reply on the screen was read off the answer above it rather than out of an entry.

    The card behind a healing line is the answer a later doubt is about - "my knee hurts" / "how
    long does it take to get better" / "and what should i do" asks its "what should i do" of the
    knee card, and the healing line has no steps in it to give. The mark is the turn the line was
    spoken on, so it cannot outlive that turn: `len(turns)` grows and the equality fails.
    """
    if not isinstance(memory, dict):
        return False
    at = memory.get("healing_at")
    turns = memory.get("turns")
    if not isinstance(at, int) or not isinstance(turns, list):
        return False
    return at == len(turns) - 1


def _no_timeline(memory, step=""):
    """The honest line, a different one each time the same ask comes back."""
    turns = len(list((memory or {}).get("turns") or ()))
    step = str(step or "").strip()
    if step:
        step = step[:1].upper() + step[1:]
        return NO_TIME_THEN_STEP[turns % len(NO_TIME_THEN_STEP)].format(step=step)
    return NO_TIMELINE[turns % len(NO_TIMELINE)]


def _a_hedge(reply):
    """Whether the reply already says the bot has no figure for the ask."""
    return bool(HEDGE.search(str(reply or "")))


def _the_card(memory):
    """The answer on the screen: the bot's last line, or the card behind a healing line.

    A healing line is read off the card above it, so a second ask in a row is about that card and
    not about the line: reading the line gave a step that was the line's own disclaimer, and the
    ask was answered with "How long it takes is the part I would be guessing at. Past that I can't
    put a time on it, sorry."
    """
    said = [str(turn.get("bot")) for turn in (memory or {}).get("turns") or ()
            if isinstance(turn, dict) and turn.get("bot")]
    if derived(memory) and len(said) > 1:
        return said[-2]
    return said[-1] if said else ""


def vetted(text, memory, reply, step_of=None):
    """The reply to a healing ask, or the reply it had.

    A healing ask is answered from the card the person was just given: the timeline it states,
    or the plain statement that it states none. Two replies are left alone. One is a paragraph of
    the same body - the card that answers "how long" for a twisted ankle is the sprain one, and it
    names the ankle - and the other is the length the card states, said short ("Two to three
    weeks." after a cough, whose card says "settle in two to three weeks").
    """
    if not asks(text):
        return reply
    card = _the_card(memory)
    if not card.strip() or not CARE.search(card):
        return reply  # the last thing said was not care, so this is not a body being looked after
    timeline = the_timeline(card)
    said = str(reply or "")
    if not said.strip() and not timeline:
        # This module found no answer of its own and the card states no span either: the turn is
        # the composer's hedge, which is honest already, and taking it would only put a different
        # shrug in its place and lose the card behind it (a burn's "should i cover it" read the
        # hedge as the answer and the honest line as a subject it knew nothing about).
        return reply
    step = ""
    if callable(step_of):
        try:
            step = str(step_of(card) or "").strip()
        except Exception:  # noqa: BLE001 - a step is a nicety, the line stands without it
            step = ""
    vetted_reply = _the_healing_line(said, timeline, card, memory, step)
    if vetted_reply != said and isinstance(memory, dict):
        turns = memory.get("turns")
        # The turn this line is spoken on, so a later "and what should i do" reads the card and
        # not this: there are no steps in a timeline.
        memory["healing_at"] = len(turns) if isinstance(turns, list) else 0
    return vetted_reply


# The lead-ins `topics.said_again` puts in front of an answer already on the screen. The card is
# still the same card behind one of them.
_REPEAT_LEAD = re.compile(r"^(?:same as before|as i said|same again)\s*[:,]?\s*", re.I)


def _the_same_as_the_card(said, card):
    """Whether the reply is the card the person already has, said again.

    A length ask about a card that states no timeline has nothing to hand back: the shoulder
    paragraph's times are how often to do the exercise ("a few times a day"), so the paragraph
    read back for "how long will it last" is the card again, and the frame in front of it
    ("Same as before:") says as much. What is owed is the honest line.
    """
    said = str(said or "").strip().lower()
    card = str(card or "").strip().lower()
    if len(said) < 20 or len(card) < 40:
        return False
    # The whole of one is the whole of the other, possibly behind a repeat frame ("Same as
    # before: Most shoulder pain...") or cut to the part the line asks for ("...a few times a
    # day", the rest of the card still above it). A new card that quotes a sentence of the old one
    # it replaces is neither, and keeps the timeline it was just given.
    body = _REPEAT_LEAD.sub("", said)
    return body in card or card in body


def _the_healing_line(said, timeline, card, memory, step=""):
    if not said.strip():
        return timeline or _no_timeline(memory, step)
    if _the_same_as_the_card(said, card):
        # The card again, with no timeline in it: the honest line is the answer.
        return timeline or _no_timeline(memory, step)
    if _a_hedge(said):
        # Already honest, so only a card that states the span improves on it.
        return timeline or said
    if _ONLY_A_SPAN.match(said):
        return said if _the_same_length(said, timeline) else (timeline or _no_timeline(memory, step))
    if len(said.split()) > 10:
        # A paragraph, and a short answer that is a whole sentence: what matters is whether it is
        # about the thing the ask leans on. "About six weeks for most bones" is a paragraph about
        # bones in the leg when the line was about a cut finger, and "Bones in the leg take the
        # longest: about 12 weeks for a shin or ankle" is the same wrong answer in one line.
        # The subject is what the last lines of theirs named, both of them: "i have a headache" /
        # "what should i do" / "how long will it take to go away" is still the headache, and the
        # middle turn names nothing of the body, so reading only the newest one made the migraine
        # sentence look like a paragraph about something else and disowned it.
        before = _said_before(memory)
        subject = _carries(" ".join(before)) if before else set()
        if subject & _carries(said):
            return said  # a paragraph about the same body: the sprain card for a twisted ankle
        if timeline and _carries(timeline) & _carries(said):
            return said
        return timeline or _no_timeline(memory, step)
    return said
