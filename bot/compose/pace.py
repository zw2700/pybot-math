"""The pace of the plan the bot just gave: "how slowly should i build up", "how fast should i go".

The person has a plan in hand - "run-walk to start, one minute of easy jogging to two of walking,
twenty minutes, three times a week, and add a minute of running a week" - and asks how fast or how
slowly to go at it. The rate is already in the answer they were given, so the reply hands it back
rather than looking the question up or saying it cannot be answered:

    how slowly should i build up   "Slowly, a step at a time: add a minute of running a week for
                                    six weeks. The rest of the plan is the check on it: one minute
                                    of easy jogging to two of walking, three times a week."

The same reading answers the length of it - "how long should i keep that up", "how long do i keep
going" - from the answer's own mark ("two or three weeks of doing it the same way"), because the
person is asking about the advice in front of them and not about the world.

Only a line that names nothing of its own qualifies. "how fast should i run a 5k" names the 5k and
has an answer in the knowledge base, so it is left to that module; a bare "how fast should i be
going" has no subject and is asking about the answer in front of it, which is exactly what this
reads. And a line only gets this when the last answer really does say a pace: with no rate in it
there is nothing to hand back, and the composer answers as it did before.
"""
import re

from . import pick

# The words that make a line a rate asked for: how slowly, how fast, how quickly, how soon.
PACE_ASK = re.compile(r"\bhow (?:slowly|fast|quickly|soon)\b", re.I)

# The words that make a line a length asked of the answer in hand: "how long should i keep that
# up", "how long do i keep going in", "how long should i carry on with it". The verb of carrying
# on is what makes it this question - "how long should i keep my old phone" names the phone and
# has an answer of its own, so it is not this line.
KEEP_UP_ASK = re.compile(
    r"\bhow long (?:should|shall|do|can|could|would) (?:i|we) (?:keep|carry on|go on|stick|stay|"
    r"continue|persist)\b"
    r"|\bhow long (?:should|shall|do|can|could|would) (?:i|we) keep \w+ing\b", re.I)

# A line asking how long a thing takes or lasts is not this question. The length in the answer
# above is then a window on the thing ("a full refund within 30 days of buying it") and not a
# length to keep at anything, so "how long should it take" after a refund answer, and "and how
# long should it last" after a packed lunch, are left to the modules that read them.

# A length of time the answer itself gives: "two or three weeks", "for six weeks", "twenty
# minutes". This is the answer's own mark, and it is what a person asking how long wants back.
_A_LENGTH = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
    r"fifteen|sixteen|eighteen|twenty|thirty|forty|fifty|sixty|a few|a couple of|several|a)\s+"
    r"(?:(?:or|to)\s+(?:\d+|two|three|four|five|six|seven|eight|ten|twelve|fifteen|twenty)\s+)?"
    r"(?:weeks?|months?|days?|hours?|minutes?|fortnights?)\b", re.I)

# A figure followed by "a week" is a rate, not a length: "three runs a week", "add a minute a week",
# "once a day". The length of the undertaking is the whole quantity, so a time unit that a count or
# a quantity of the same thing stands in front of is the denominator of a rate and is passed over.
_A_RATE_LEAD = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|a|an|once|twice|half)\s+"
    r"(?:runs?|times|sessions?|days?|weeks?|months?|hours?|minutes?|miles?|km|kms|kilometres?|"
    r"reps?|sets?|walks?|workouts?|feeds?|charges?|meals?|nights?)\s+$", re.I)

# Everything such a line is allowed to say beside the rate. A line that names a thing - a 5k, a
# rowing machine, a mortgage - has a subject of its own and is not asking about the answer above.
# The verbs of a plan are here because "how slowly should i build up" is the same question.
_ALLOWED = frozenset("""
a an the this that these it i you we me my our
should shall can could would will do does did be is was are am
go going do doing now then again first next too so much more
add build start push increase work step up at on in to of for
run runs running walk walks walking jog jogging going train training slower faster easy harder
slow fast
""".split())

# The words a how-long-to-keep-going line may say beside the ask. "how long should i keep looking
# tonight" is about the answer above; "how long should i keep my old phone" is not, and the phone
# is not in here.
_KEEP_ALLOWED = frozenset("""
looking searching waiting trying watching going at it tonight today now longer long for doing
this that the same way
""".split())

# The step the plan moves up by: "add a minute of running a week for six weeks", "build up by a
# minute each week". This is the pace itself, and it is said first.
_STEP = re.compile(
    r"\b(?:add|increase|build(?:ing)? up|work(?:ing)? up|step(?:ping)? up|extend|progress)\b"
    r"[^.;]{0,70}\b(?:a|an|each|every|per)\s+(?:week|day|session|run|month|fortnight)\b",
    re.I)

# The rate the answer already gives: a step a week, three times a week, every other day, week by
# week. A figure with a period attached is what a build-up is made of.
_PACE = re.compile(
    r"\b(?:add|increase|build(?:ing)? up|work(?:ing)? up|step(?:ping)? up|extend|progress|"
    r"no more than|only)\b[^.;]{0,70}\b(?:a|an|each|every|per)\s+"
    r"(?:week|day|session|run|month|fortnight)\b"
    r"|\b(?:one|two|three|four|five|six|\d+)\s+times?\s+a\s+(?:week|day)\b"
    r"|\bevery other day\b"
    r"|\bweek by week\b"
    r"|\ba (?:minute|day|session|week)\s+(?:at a time|more|longer)\b"
    # A kitchen rate is a rate too: "add the stock a ladle at a time", "a little at a time",
    # "gradually". The thing a person is told to go slowly at, whatever it is, is said the same
    # way - in steps, and not all at once.
    r"|\b(?:a|an|one)\s+\w+(?:\s+\w+)?\s+at a time\b"
    r"|\ba little at a time\b"
    r"|\bgradually\b",
    re.I)

# The answer's own test, said back as the thing to judge it by rather than a new rule of this
# file's: "keep every run slow enough to talk", "you should be able to hold a conversation".
_TEST = re.compile(
    r"[^.;]{0,60}\b(?:slow enough to talk|hold a conversation|talk test|conversational|"
    r"can still talk|able to talk)\b[^.;]{0,60}", re.I)

# How the rate is opened, by the word that asked for it. Slow is a step at a time, fast is not
# faster than the plan, and neither is a yes or a no.
_LEADS = {
    "slowly": ("Slowly, a step at a time", "Slowly, and only as the plan steps up",
               "Slowly - less than you think"),
    "fast": ("No faster than the plan says", "Only as fast as the answer above says",
             "Not fast - by the plan's own step"),
    "quickly": ("Only as quickly as the plan steps up", "As quickly as the plan says, and no more"),
    "soon": ("No sooner than the answer above says", "Only when the plan says you are ready"),
}

_REST = ("That is the pace the plan sets: {rest}.",
         "The rest of the plan is the check on it: {rest}.",
         "The plan above already says the rest of it: {rest}.")

_NEXT = ("The rest of it is as the answer says: {next}.",
         "Then carry on as the answer says: {next}.",
         "Nothing else changes after that: {next}.")

_TESTED = ("The test is the plan's own - {test}.",
           "Judge it by the one the answer already gives - {test}.",
           "And keep the plan's own check - {test}.")


def _clean(text):
    return " ".join(str(text or "").lower().split())


def asks_the_pace(text, answer=""):
    """True when the line asks how slowly or how fast and names no subject of its own.

    A subject *the answer above already named* is not a subject of the line's own: "how slowly
    should i add the stock" after a recipe that talks about the stock is asking about the answer
    in hand. Anything else named - a 5k, a rowing machine, onions - has an entry of its own and is
    left to the module that has it.
    """
    said = _clean(text).strip(" ?!.,;:'\"")
    found = PACE_ASK.search(said)
    if not found:
        return False
    rest = (said[:found.start()] + " " + said[found.end():]).replace("'s", " ").split()
    words = [re.sub(r"[^a-z0-9]", "", w) for w in rest]
    words = [w for w in words if w]
    if not words:
        return True                        # "how fast?" on its own is about the answer above
    in_the_answer = set(re.findall(r"[a-z']+", str(answer or "").lower()))
    return all(w in _ALLOWED or w in in_the_answer for w in words)


def _last_answer(memory):
    turns = (memory or {}).get("turns") or []
    for turn in reversed(turns):
        if isinstance(turn, dict):
            said = str(turn.get("bot") or "").strip()
            if said:
                return said
    return ""


def _clauses(answer):
    """The answer cut into the short pieces a pace is said in: on sentence ends and commas."""
    # A colon or a dash ends a piece as surely as a comma does: the lead-in of a reply ("Slowly,
    # a step at a time: add a minute a week") is not part of the pace it introduces, and a reply
    # handed back twice must not nest one lead-in inside another.
    pieces = re.split(r"(?<=[.;!?])\s+|;\s*|,\s*|:\s+|\s+-\s+", str(answer or ""))
    out = []
    for piece in pieces:
        text = " ".join(piece.strip(" ,.;").split())
        text = re.sub(r"^(?:and|but|then|so)\s+", "", text, flags=re.I)
        if text:
            out.append(text)
    return out


def _trim(text, most=96):
    """A clause short enough to read out, cut at a comma rather than mid-phrase."""
    if len(text) <= most:
        return text
    cut = text[:most]
    comma = cut.rfind(",")
    if comma > most // 2:
        cut = cut[:comma]
    else:
        space = cut.rfind(" ")
        if space > most // 2:
            cut = cut[:space]      # never a word cut in half: "befor" is not a word
    return " ".join(cut.split()).rstrip(",;:")


def _parts(answer):
    """The answer's own pace, best first, its own test, and the step that comes after it."""
    clauses = _clauses(answer)
    stepped, timed, test, after = [], [], "", ""
    for index, clause in enumerate(clauses):
        if _STEP.search(clause) and len(stepped) < 2:
            stepped.append(_trim(clause))
        elif _PACE.search(clause) and len(timed) < 2:
            timed.append(_trim(clause))
        elif not test and _TEST.search(clause):
            test = _trim(_TEST.search(clause).group(0).strip())
        if (stepped or timed) and not after and not _a_lead_in(clause):
            after = _the_next_step(clauses[index + 1:])
    pace = stepped + timed
    if after in pace:
        after = ""
    return pace, test, after


# A clause that only carries the sentence on: "waiting for each to be absorbed", "for about 18
# minutes", "stirring now and then". It says nothing a person can do next, so it is not handed
# back as the plan's next step.
_CONTINUES = re.compile(r"^(?:for\s|\w+ing\b|until\b|then\s|and\b|so\b|which\b|that\b|"
                        r"it\b|this\b|about\b)", re.I)


def _the_next_step(clauses):
    """The first clause after the pace that names something to do, rather than carrying on."""
    for clause in clauses:
        clause = _trim(clause)
        if not clause or _a_lead_in(clause) or _CONTINUES.match(clause):
            continue
        if _PACE.search(clause) or _STEP.search(clause):
            continue
        return clause
    return ""


def _a_lead_in(clause):
    """A clause that only introduces the one after it ("to start with", "first of all")."""
    return bool(re.match(r"^(?:to start with|first|first of all|for a start)\b", clause, re.I))


def _a_pace_reply(answer):
    """True when the answer above is this file's own reply, so the rate has been given once."""
    opening = " ".join(str(answer or "").split())[:80].lower()
    for leads in _LEADS.values():
        for lead in leads:
            if opening.startswith(lead.lower()[:24]):
                return True
    return False


def asks_the_keep_up(text, answer=""):
    """True when the line asks how long to keep going and names no subject of its own."""
    said = _clean(text).strip(" ?!.,;:'\"")
    found = KEEP_UP_ASK.search(said)
    if not found:
        return False
    rest = (said[:found.start()] + " " + said[found.end():]).replace("'s", " ").split()
    words = [re.sub(r"[^a-z0-9]", "", w) for w in rest]
    words = [w for w in words if w]
    if not words:
        return True
    in_the_answer = set(re.findall(r"[a-z']+", str(answer or "").lower()))
    return all(w in _ALLOWED or w in _KEEP_ALLOWED or w in in_the_answer for w in words)


# What a tail is not: a bare pronoun or conjunction, and a time word that names when rather than
# what to do over the length ("after a feed", "and they").
_NOT_A_TAIL = re.compile(
    r"^(?:and|but|so|it|they|them|this|that|the|a|an|after|before|since|until|once|when|while)\b",
    re.I)


def _the_doing(after):
    """The words the answer puts after its length: "of doing it the same way every single time"."""
    after = re.sub(r"^(?:of|in|on|for|at)\s+", "", after.strip(" ,.;"))
    cut = re.split(r"\b(?:is|are|was|were|turns?|helps?|makes?|works?|should|will|but)\b",
                   after, maxsplit=1)[0]
    # A piece that stops mid-clause is not a sentence to hand back: "with a fold every hour until
    # it", "what the answer says to allow, (one long". The tail is cut before the subordinator it
    # dangles on, and an opening bracket with no closing one is dropped with what follows it.
    cut = _DANGLES.sub("", cut)
    if cut.count("(") > cut.count(")"):
        cut = cut[:cut.rfind("(")]
    cut = _trim(" ".join(cut.split()).strip(" ,.;-"), 80)
    if len(cut.split()) < 2 or _NOT_A_TAIL.match(cut):
        return ""
    return cut


# What a tail cannot be left hanging on: a clause that opens with one of these and then stops.
_DANGLES = re.compile(
    r"\b(?:until|till|because|so that|so|which|that|when|where|if|while|unless|than|and|or|but|"
    r"to|of|in|on|at|for|with|by|from|as|into|about|after|before)[^,;:.!?]*$", re.I)


# A figure that is a portion or a rate is not the length of the undertaking: "five minutes of
# walking for each month of age" is how much a walk is, not how long to keep at the advice, and
# handing it back as "give it five minutes" would answer a different question.
_A_PORTION = re.compile(r"\b(?:for each|for every|a time|per|twice|once a|\d+ times)\b", re.I)


def _the_length(answer, asked=frozenset()):
    """The answer's own length of time, and what it says to do over it.

    An answer can hold more than one length ("4 to 6 hours with a fold every hour" and "a week of
    feeding" in the sourdough card), and the one the person asked about is the one in the clause
    that names what they said: "how long should i keep feeding it" wants the week of feeding, not
    the bulk rise. When no clause names it, the first length in the answer is the answer's own.
    """
    first = ("", "")
    for clause in _clauses(answer):
        found = _A_LENGTH.search(clause)
        if not found:
            continue
        if _A_PORTION.search(clause) or _A_RATE_LEAD.search(clause[:found.start()]):
            continue
        length, doing = found.group(0).strip(), _the_doing(clause[found.end():])
        if asked and _names_it(clause, asked):
            return length, doing
        if not first[0]:
            first = (length, doing)
    return first


def _names_it(clause, asked):
    """Whether the clause says the thing the person asked about, near enough by its stem."""
    words = _stems(clause)
    return bool(words & asked)


def _stems(text):
    """The content words of a line, cut back so "feeding", "feeds" and "feed" are one word."""
    out = set()
    for word in re.findall(r"[a-z]{4,}", str(text or "").lower()):
        if word in _STOPPED:
            continue
        for ending in ("ing", "ed", "es", "s"):
            if len(word) > len(ending) + 3 and word.endswith(ending):
                word = word[:-len(ending)]
                break
        out.add(word)
    return out


# Words too common to say whether two answers are about the same thing.
_STOPPED = frozenset("""
a an the and or but if then so of to in on at for with from by is are was were be been being it
its this that these those i you we they he she them him her your our my me us do does did done
not no as than there here what which who when where how why can could should would will just
one two three keep keeps keeping go going get gets got make makes made say says said
""".split())


def _content(answer):
    return {w for w in re.findall(r"[a-z]{4,}", str(answer or "").lower()) if w not in _STOPPED}


def _about_the_same_thing(one, other):
    """Two bot answers on one subject share the words the subject is made of."""
    return len(_content(one) & _content(other)) >= 2


def _the_advice_length(memory, answers=3, asked=frozenset()):
    """The length of time in the advice in hand - the newest answer, or the one before it.

    "how long should i keep going in" comes after the light-on answer, while the length ("two or
    three weeks of doing it the same way") was said in the answer before that; both are about the
    same bedtime. A length from an older turn is only taken when the two answers are about the
    same thing, so a figure from an answer on another subject is never handed back here.
    """
    said = []
    for turn in reversed(_bot_turns(memory)):
        said.append(turn)
        if len(said) >= answers:
            break
    if not said:
        return "", ""
    length, action = _the_length(said[0], asked)
    if length:
        return length, action
    for older in said[1:]:
        length, action = _the_length(older, asked)
        if length and _about_the_same_thing(older, said[0]):
            return length, action
    return "", ""


def _asked_stems(text):
    """What the person asked about, from the line itself, as stems."""
    return frozenset(_stems(text) - _ASK_WORDS)


# The words of the ask itself, which say nothing about what is being asked about.
_ASK_WORDS = frozenset("""
keep keeps keeping going long longer how should shall could would can do does did i we
much many time times more again this that it thing things
""".split())


def _bot_turns(memory):
    """Every answer the bot has given, oldest first, that is not one of this file's own."""
    out = []
    for turn in (memory or {}).get("turns") or []:
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "").strip()
        if said and not _a_pace_reply(said) and not _a_keep_reply(said):
            out.append(said)
    return out


# How the length is opened, and what it is called. The answer's own figure is the reply; these
# only carry it, so no number is ever invented here.
_KEEP_LEADS = ("Keep it up for {length}", "Stay with it for {length}",
               "Give it {length}")
_KEEP_MARK = ("the answer's own mark for it", "the answer's own length for it",
              "what the answer says to allow")


def _a_keep_reply(answer):
    """True when the answer above is this file's own length reply."""
    opening = " ".join(str(answer or "").split())[:60].lower()
    return any(opening.startswith(lead.split("{length}")[0].strip().lower())
               for lead in _KEEP_LEADS)


def the_keep_up_line(text, memory):
    """True only when this line is the one the length reply answers."""
    if not KEEP_UP_ASK.search(_clean(text)):
        return False
    answer = _last_answer(memory)
    if not answer or _a_pace_reply(answer) or _a_keep_reply(answer):
        return False
    if not asks_the_keep_up(text, answer):
        return False
    length, _action = _the_advice_length(memory, asked=_asked_stems(text))
    return bool(length)


def _keep_up_reply_for(text, memory):
    if not the_keep_up_line(text, memory):
        return None
    length, action = _the_advice_length(memory, asked=_asked_stems(text))
    if not length:
        return None
    first = "%s - %s" % (pick(_KEEP_LEADS, memory, text).format(length=_as_clause(length)),
                         pick(_KEEP_MARK, memory, text))
    if action:
        return "%s, %s." % (first, _as_clause(action))
    return first + "."


def the_pace_line(text, memory):
    """True only when this line is the one `reply_for` answers: a rate, and a pace above it."""
    if not PACE_ASK.search(_clean(text)):
        return False
    answer = _last_answer(memory)
    if _a_pace_reply(answer) or not asks_the_pace(text, answer):
        return False
    pace, test, after = _parts(answer)
    return bool(pace) and bool(test or len(pace) > 1 or after)


def reply_for(text, memory):
    """The pace or the length of the answer just given, or None when this is not that line."""
    if KEEP_UP_ASK.search(_clean(text)):
        return _keep_up_reply_for(text, memory)
    if not PACE_ASK.search(_clean(text)):
        return None
    answer = _last_answer(memory)
    if not answer or _a_pace_reply(answer) or not asks_the_pace(text, answer):
        return None
    pace, test, after = _parts(answer)
    if not pace:
        return None
    said = _clean(text)
    word = "slowly" if "slowly" in said else "fast" if "fast" in said else \
        "soon" if "soon" in said else "quickly"
    lead = pick(_LEADS[word], memory, text)
    first = "%s: %s." % (lead, _as_clause(pace[0]))
    if test:
        # The frame is dropped when its own lead-in says the test's first word already: "And keep
        # the plan's own check - keep every run slow enough to talk" is the answer stuttering.
        opening = _as_clause(test).split()[:1]
        opening = opening[0].lower().strip(",.;:") if opening else ""
        frames = [f for f in _TESTED
                  if opening not in [w.lower().strip(",.;:") for w in f.split("{test}")[0].split()]]
        second = pick(frames or list(_TESTED), memory, text).format(test=_as_clause(test))
    elif len(pace) > 1:
        second = pick(_REST, memory, text).format(rest=_as_clause(pace[1]))
    elif after:
        second = pick(_NEXT, memory, text).format(next=_as_clause(after))
    else:
        return None
    return first + " " + second


def _as_clause(text):
    """A piece of the answer with its final stop taken off, so it can sit inside a sentence."""
    said = str(text).strip().rstrip(".").strip()
    if said[:2] != "I " and said[:2] != "I'":
        said = said[:1].lower() + said[1:]
    return said
