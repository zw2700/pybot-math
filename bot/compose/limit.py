"""A line that only rules something out is answered inside the answer before it.

"recommend a film" / "no horror" and "training the lead" / "no treats" are follow-ups, not new
subjects. Left to the modules, the word after "no" is a topic word like any other and the bot
answers the thing the person has just taken away (a horror list after "no horror", the treat
again after "no treats"). The understanding engine reads the line as a limit on the last
answer (`memory["understood"]["excludes"]`, `["constraint"]`); this composer turns that reading
into a reply.

The rule, in one line: keep the bot's own last answer, take out the parts of it that carry the
thing they ruled out, and say what is left. Nothing here knows what a genre, a food or a dog
treat is. It works on the words of the answer above, so the same code answers a horror film, a
jar of garlic and a pocket of treats.

It only speaks when the answer above actually carries the thing: where it never mentioned it
there is nothing to take out, and the answer that was already given (or the next module) is
left alone rather than replaced with a remark about itself.
"""
import re

# Where one part of an answer ends and the next begins: after a full stop, a colon, a semicolon
# or a comma. The bot's own lines are a list of short parts ("*Knives Out* for a clever
# whodunnit, *Arrival* if you'd rather think"), so a part is the unit that can be taken out.
PART = re.compile(r"(?<=[.?!;:,])\s+")
# A part that only continues the one before it. When the part before it has been taken out,
# this one is left hanging ("..., and reward him with a treat" has no verb of its own), so it
# goes with it.
CONTINUES = re.compile(r"^(?:and|or|then|but|plus|so|because|with|also|instead|though|which|"
                       r"that|to|for|in|on|at|of)\b", re.I)
# A count of the choices is wrong once some of them have been taken out, so those parts go.
COUNTED = re.compile(r"\b(?:all three|all four|all five|all of them|both of them|both|either|"
                     r"any of those|any of them|none of them|three of|the three)\b", re.I)
WORD = re.compile(r"[a-z0-9']*[a-z][a-z0-9']*")
# The frame the repeat readers put in front of an answer already on the screen ("Same as before:",
# "Same answer, and it covers this:"). A limit cuts the answer, so the frame that says it has not
# changed is no longer true and goes with the part it introduced.
FRAME = re.compile(r"^(?:same as before|same answer(?:, and it covers this)?|as i said|still|"
                   r"that is still the thing to do|nothing new to add on it|"
                   r"nothing more on it(?: i'm afraid)?|that is all i have on it|"
                   r"there is nothing further to add|same again for|it is the same for|"
                   r"same for|the same for|it is the same\b)", re.I)
# A part that opens by pointing at the part before it. Said first, with that part taken out, it
# has nothing to point at.
BACK_REFERENCE = re.compile(r"^(?:the same|this|that|these|those|it|its|it's|they|them|their|"
                            r"both|either|which|such|the latter|the former)\b", re.I)
# The line said when part of the answer above carries the thing: what is left is repeated, so
# the person can act on it without reading back.
KEPT = (
    "Right — no {thing}, then. {kept}",
    "Then leave the {thing} out: {kept}",
    "No {thing}, then — {kept}",
    "Fair enough, no {thing}: {kept}",
)
# Nothing of the answer survives it, so the answer has to change and only they know what it
# should change into.
NOTHING_LEFT = (
    "Right — no {thing}, then, and that changes the answer: what would you use instead?",
    "With no {thing} in it there is not much of that answer left — what would you rather use?",
    "Then {thing} out changes it. What should it be instead?",
)
# How much of the answer has to survive to be worth saying back. Under this, the remainder is a
# fragment of a sentence and the person is better served by being asked what to use instead.
LEAST_KEPT = 20
LEAST_WORDS = 4

# How a line this composer said can be told apart from an answer: every one of them takes the
# thing out and says the answer again ("Right — no treats, then. ..."). The turn after one of
# these is not a turn after a new answer - the answer behind it is still the one on the table -
# and read as one it hands back a fragment of the restatement: "my dog pulls on the lead" /
# "no treats" / "how do i stop it" was answered "Same answer: Stand still until it slackens"
# instead of the training answer the step came from.
RESTATED = re.compile(
    r"^(?:right\s*[-\u2014]\s*no\s+\S[^.]{0,40},\s*then[.\s,:\u2014-]|"
    r"no\s+\S[^.]{0,40},\s*then\s*[-\u2014]|"
    r"then leave the\s+\S[^.]{0,40}\s+out[:,]|"
    r"fair enough, no\s+\S[^.]{0,40}:|"
    r"with no\s+\S[^.]{0,40}\s+in it there is not much|"
    r"then\s+\S[^.]{0,30}\s+out changes it)", re.I)


def restates_the_answer(bot_line):
    """True when this bot line is one of ours: the answer above, said again with a limit out."""
    return bool(RESTATED.match(str(bot_line or "").strip()))


# The thing a limit takes away is a thing the bot put on the table - "no horror", "no treats",
# "hold the cheese". A person's own state is not a thing on any table: "nothing feels worth
# doing", "nothing is fun any more", "nothing seems worth it" are the family that says the
# pleasure has gone, and read as limits they cut the answer above down to a fragment of itself -
# "Right - no feels worth doing, then, and that changes the answer: what would you use instead?"
# - which is a reply about a list the bot never gave. A limit names what is left out, so the
# words of it start with a noun or a noun's own modifier, never a linking verb or the person.
A_STATE_IS_NOT_A_LIMIT = re.compile(
    r"^(?:feel|feels|felt|feeling|is|are|was|were|be|been|being|seems|seem|seemed|"
    r"i|im|i'm|ive|i've|me|my|we|we're|us)\b", re.I)


def forms_of(thing):
    """The word forms of a ruled-out thing that count as the same thing in the bot's own line."""
    words = [w for w in WORD.findall(thing.lower()) if w]
    if not words:
        return ()
    out = set()
    for word in words:
        out.add(word)
        if word.endswith("ing") and len(word) > 5:
            # "no walking up hills" is the walking the answer above calls "walk for half an hour a
            # day": the thing is said as the doing of it and the answer says the bare verb, so the
            # bare verb is the same thing. Without it the answer was not read as carrying the thing
            # at all, and the entry for hills answered a person who had just said no to hills.
            stem = word[:-3]
            out.update({stem, stem + "e"})
            if len(stem) > 2 and stem[-1] == stem[-2]:
                out.add(stem[:-1])
        if word.endswith("ies") and len(word) > 4:
            out.add(word[:-3] + "y")
        elif word.endswith("es") and len(word) > 3:
            out.add(word[:-2])
            out.add(word[:-1])
        elif word.endswith("s") and len(word) > 3:
            out.add(word[:-1])
        else:
            out.add(word + "s")
            out.add(word + "es")
    return tuple(sorted(out))


def _carries(part, forms):
    """True when this part of the bot's own answer is about the thing ruled out."""
    said = set(WORD.findall(part.lower()))
    return any(form in said for form in forms)


def _last_answer(memory):
    """The bot's own last line, or "" when there is not one. A safety line is never edited."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    for last in reversed(turns):
        if not isinstance(last, dict):
            return ""
        if str(last.get("module") or "") in ("safety", "loss", "badnews"):
            return ""
        said = str(last.get("bot") or "").strip()
        if said:
            return said
    return ""


def _pick(pool, memory):
    """One line from a pool, never the line the bot has just said."""
    last = _last_answer(memory)
    for line in pool:
        head = line.split("{")[0].strip()
        if head and last and head in last:
            continue
        return line
    return pool[0]


def _take_out(said, forms):
    """The answer above with the parts about the thing taken out, or "" when enough is left."""
    kept, _dropped = _the_parts_left(said, forms)
    if not kept:
        return ""
    left = _joined(kept)
    if len(left) < LEAST_KEPT or len(left.split()) < LEAST_WORDS:
        return ""
    return left


def steps_left(understood, memory):
    """The parts of the answer above that the limit leaves, in the order they were given.

    The reply is the whole of them, so the turn after it - "whats the first thing to change" - is
    the first of them rather than a new search (`bot/memory/limit.py`, `move_after_a_limit`).
    """
    if not isinstance(understood, dict) or not understood.get("constraint"):
        return []
    things = [str(thing).strip() for thing in (understood.get("excludes") or []) if str(thing).strip()]
    said = _last_answer(memory)
    if not things or not said:
        return []
    kept, _dropped = _the_parts_left(said, forms_of(things[0]))
    # A part that ends with a colon only introduces the parts after it ("Change a few things you can
    # keep doing rather than going on a diet:"), so it is not a step to start with.
    return [part.strip().rstrip(".,;:") for part in kept
            if part.strip() and not part.strip().endswith(":")]


def _the_parts_left(said, forms):
    """(the parts of the answer that survive the limit, how many were taken out)."""
    parts = [part for part in PART.split(said) if part.strip()]
    kept = []
    dropped = 0
    after_a_colon = False
    for part in parts:
        if not kept and FRAME.match(part.strip()) and not _carries(part, forms):
            dropped += 1  # the frame that said the answer was unchanged, now that it is not
            continue
        if _carries(part, forms) or (dropped and CONTINUES.match(part)) or after_a_colon:
            # What is left of a part that introduced the one taken out is a sentence with nothing
            # after it ("If you want something easy and good tonight:"), so the lead-in goes too.
            if kept and kept[-1].rstrip().endswith(":"):
                kept.pop()
            # A colon says what follows belongs to what came before it, so the part after a part
            # taken out goes with it ("... the fountains are free" has nothing left to explain).
            after_a_colon = part.rstrip().endswith(":")
            dropped += 1
            continue
        after_a_colon = False
        # A count of the choices is wrong once one of them is gone ("All three work...").
        if dropped and COUNTED.search(part):
            dropped += 1
            continue
        kept.append(part.strip())
    if not dropped or not kept:
        return [], dropped
    # The first thing left points back at what has just been taken out ("The same hand carries on
    # down to the floor...", "That also works for..."), so it is not a thing to say on its own.
    if BACK_REFERENCE.match(kept[0]):
        return [], dropped
    return kept, dropped


def _joined(kept):
    """The kept parts as one line, with the punctuation the missing parts have left behind fixed."""
    out = []
    for part in kept:
        # A part that led with "and" or "or" only read as a continuation: with the part before
        # it gone, the words have to stand on their own.
        part = re.sub(r"^(?:and|or|then|but|plus|so|because|also|instead)\s+", "", part, flags=re.I)
        if not part:
            continue
        starts_a_sentence = part[:1].isupper() or part[:1] in "*\"'("
        if out:
            if starts_a_sentence and out[-1][-1] in ",;:":
                out[-1] = out[-1][:-1] + "."
            if out[-1][-1] in ".!?" and part[:1].islower():
                part = part[:1].upper() + part[1:]
        out.append(part)
    left = " ".join(out).rstrip(" ,;:")
    if left and left[-1] not in ".!?":
        left += "."
    if left[:1].islower():
        left = left[:1].upper() + left[1:]
    return left


def _a_fact_put_right(memory):
    """True when this line corrects one of their own facts rather than limiting the answer.

    "we are going to rome in may" / "no, florence not rome": the reading that files anything
    after a "no" as a thing ruled out takes the whole pair as the excluded thing ("florence not
    rome"), and the Rome paragraph above is said back with a clause of it on the end - "Right -
    no florence not rome, then. The Pantheon. Book the Vatican museums online." The person did
    not rule anything out: the value after the "no" is the one they are moving *to*, and the
    memory store has already replaced Rome with Florence and written the line that says which
    value the bot goes with now.

    The store writes `memory["correction"]` on the turn of the correction and it carries the
    value that replaced the old one, so the composer asks that rather than reading the sentence a
    second time. Where nothing was put right the key is absent and the limit reading stands - the
    case it was written for ("recommend a film" / "no horror" takes the horror out of the list)
    is untouched.
    """
    if not isinstance(memory, dict):
        return False
    fixed = memory.get("correction")
    return isinstance(fixed, dict) and bool(fixed.get("value"))


# The words after the negator are what make a line a limit on the answer above rather than a
# statement about their life: a limit says "with", "that", "too", "but", "except" ("nothing with a
# laugh track though", "nothing too scary"), and a statement says "makes", "feels", "is" ("nothing
# makes me happy"). The distinction matters both ways round. Read as a statement, a limit gets a
# cheer ("That's the best kind of day. What happened?" at somebody narrowing a film list, because
# "laugh" is a pleasure word); read as a limit, a flat fortnight gets its answer cut down to a
# fragment of itself ("Right - no feels worth doing, then").
NOTHING_THAT_LIMITS = re.compile(
    r"\bnothing\s+(?:with|that|too|but|except|without|involving|containing|featuring|before|"
    r"after|under|over|like)\b")
# A limit on a film or a programme with no "nothing" in it: the negator sits right in front of the
# kind of thing a list carries ("no subtitles", "not too sad", "without the violence").
NO_LAUGH_OR_SCARES = re.compile(
    r"\b(?:no|not|without|except|minus)\s+(?:a\s+|the\s+|any\s+|too\s+|more\s+)?"
    r"(?:laugh\s?track|laughter|laughing|comedy|comedies|jokes?|funny|scares?|scary|horror|"
    r"gore|violence|subtitles|sad\s+ones?|sad\s+films?)\b")


def a_limit_on_the_answer(text):
    """True when the line is a thing taken out of the answer above, not a report of their day."""
    said = " " + " ".join(str(text or "").lower().split()) + " "
    return bool(NOTHING_THAT_LIMITS.search(said) or NO_LAUGH_OR_SCARES.search(said))


# A limit said in words the reading does not file: "nothing with a laugh track though", "no
# subtitles", "not too sad". The reading builds `["excludes"]` from a "no X" it can name, and
# these arrive with an empty list, so the answer above was met with the neutral receipt ("Thanks
# for telling me - I'm here if you want to dig into any of that") - the filler this shape least
# deserves, because the person has just narrowed a list and is waiting for the next one. The words
# after the negator are what make it a limit rather than a statement about their life: "nothing
# makes me happy" says "makes", and keeps its own answer.
A_LIMIT_SHAPE = re.compile(
    r"\b(?:nothing|no|not|without|except|minus)\s+(?:with|that|too|more|any|much|a|the)?\s*"
    r"\S")
# What is said when the thing taken out cannot be named back: what the person has just narrowed
# is on the screen, so the way forward is the one they picked it down to, not a guess about it.
MISSED_LIMIT = (
    "Leave that out, then - which of those was nearest, and I'll find another in the same vein.",
    "Fair enough, that one's out. Tell me which of those you'd keep and I'll follow the thread.",
    "Then it's out. Which of them came closest, and what would you change about it?",
)


def a_limit_the_reading_missed(clean, memory):
    """The reply for a limit the reading did not file, or None to leave the line alone."""
    said = " " + " ".join(str(clean or "").lower().split()) + " "
    if not said.strip():
        return None
    if not A_LIMIT_SHAPE.match(said.strip()) or not a_limit_on_the_answer(said):
        return None
    above = _last_answer(memory)
    if not above or above.rstrip().endswith("?"):
        # Nothing was on the table, so there is nothing the person has narrowed.
        return None
    return _pick(MISSED_LIMIT, memory)


def reply_for(understood, memory):
    """The reply for a line that only rules something out, or None to leave the line alone."""
    if not isinstance(understood, dict) or not understood.get("constraint"):
        return None
    if _a_fact_put_right(memory):
        # A correction is not a limit, and the store's own note is the reply to it (see above).
        return None
    things = [str(t).strip() for t in (understood.get("excludes") or []) if str(t).strip()]
    if not things:
        return None
    said = _last_answer(memory)
    # Nothing has been answered yet, so a limit on it limits nothing: "no horror" as the first
    # line of a chat is a film ask of its own, and belongs to whoever reads it.
    if not said:
        return None
    thing = things[0]
    if A_STATE_IS_NOT_A_LIMIT.match(thing):
        # "nothing feels worth doing" after an answer about a flat week is the person's own state,
        # not a part of that answer they want taken out (see A_STATE_IS_NOT_A_LIMIT).
        return None
    left = _take_out(said, forms_of(thing))
    if not left:
        if not _carries(said, forms_of(thing)):
            return None
        reply = _pick(NOTHING_LEFT, memory).format(thing=thing)
    else:
        reply = _pick(KEPT, memory).format(thing=thing, kept=left)
    return reply
