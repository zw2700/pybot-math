"""A follow-up that says which step of the last answer they have done gets the step after it.

"how do i get red wine out of a cream carpet" / "it happened last night and i blotted it" was
answered "Thanks for telling me - I'm here if you want to dig into any of that", which is the one
reply a follow-up must never get. The person has not asked anything new: they have told the bot
where they are in the job, and the useful thing a friend says next is the next bit of the job -
in the words the answer already used, because those words are the ones they are following.

    how do i get red wine out of a cream carpet
      Blot it, don't rub, with kitchen paper, then pour on cold water and blot again, ...
    it happened last night and i blotted it
      Good - blotting first is right. Now pour on cold water and blot again.

The reading is deliberately narrow, because the same words after a different kind of answer are
not a report on it:

* the turn before must have been an answer from `answers` that gave instructions, and the line
  before it must have been a how-to ask ("how do i", "how to", "what's the best way");
* the line must be short and carry no question of its own, so "i blotted it, will that be
  enough?" is still a question and is answered as one;
* the person has to be in the line, saying what they did ("i blotted it", "we gave it a go"): "it
  boiled over" and "it happened last night" report the thing, not a step of theirs;
* it must name the step, in one of the two ways a person does that: an action in the past
  ("blotted", "scrubbed") that the answer used, or a thing they finished with a completion verb
  in front of it ("i did the bicarbonate bit", "i used the vinegar"). The words are matched
  against the answer, never a list of jobs here;
* it must not be a different kind of line wearing the same words - a lack ("i dont have any
  vinegar"), a mishap ("i boiled it dry", "it boiled over"), or a feeling ("i hate this kettle")
  is something to answer, never praise for a step nobody took;
* the clause the action came from must not be one the answer forbade ("don't rub"), so a person
  who rubbed it is not told they did the right thing;
* something must come after that step in the answer, and it must be an instruction rather than
  the other half of a pair ("or a sachet of citric acid" belongs to the step before it). If they
  have done the last one, this has nothing to say and passes the turn back.
"""
import re

from . import tried

WORD = re.compile(r"[a-z0-9']+")

# The ask whose answer is a set of steps: "how do i get red wine out of a carpet", "how to
# descale a kettle", "whats the best way to clean an oven", "any tips for slugs".
HOW_TO = re.compile(
    r"\b(?:how\s+(?:do|can|should|could)\s+(?:i|we|you)\b|how\s+to\b|"
    r"what'?s\s+the\s+best\s+way\b|whats\s+the\s+best\s+way\b|best\s+way\s+to\b|"
    r"any\s+tips\b|how\s+would\s+you\b|what\s+should\s+i\s+use\b)", re.I)

# A line that asks something of its own is not a report on the answer. The question can be in the
# trailing clause ("i blotted it, will that be enough"), so any question word in the line counts -
# except "did", which is how a step named by its thing is said ("i did the bicarbonate bit").
A_QUESTION = re.compile(
    r"\?|\b(?:what|why|how|when|where|who|whom|whose|which|will|would|should|could|can|shall|"
    r"may|might)\b", re.I)

# The frame around an action: the time it happened, the pronoun for the thing, the polite filler.
# Everything here is stripped before the action words are taken out of the line.
FRAME = frozenset("""
    it its it's that this them they those these there here
    i we he she you ive i've weve we've id i'd
    the a an and then so but also just already now still only even
    happened happen went come came got get had has have was were is are been being
    last night morning afternoon evening today yesterday week weekend month year
    ago later earlier since about around nearly almost bit thing one ones all
    on in at to of with out up down off back through over again just finally first
    tried try did done doing do does
""".split())

# How long a report can be: "it happened last night and i blotted it" is nine words, and a
# sentence after that is a new thought rather than a note on the last one.
SHORT = 14
# The longest the next step is given: "pour on cold water and blot again" - a friend says the
# next bit, not the rest of the sheet.
STEP_WORDS = 22
# A step cut to STEP_WORDS words can end in the middle of a sentence, and the word it ends on is
# often the one holding the sentence together: the ants answer's step was handed back as "Next,
# give the bait a week or two: the ants keep coming for the first few days and." A word that
# cannot end a sentence is not where a step stops.
DANGLING = frozenset("""a an the and or but nor so yet for with without to of in on at by from
as if when while because which that than then also plus into onto over under about after before
during up down out off back through it its their his her your my our this these those there
here""".split())


def _a_whole_step(said):
    """The step, cut to STEP_WORDS words without cutting a sentence in the middle.

    The cut lands on a clause boundary when the step has one (a colon, a semicolon or a comma in
    the first STEP_WORDS words), which keeps a whole instruction; otherwise it walks back to the
    last word that could end a sentence. The caller's frame supplies the full stop.
    """
    words = said.split()
    if len(words) <= STEP_WORDS:
        return said.strip(" ,;:")
    words = words[:STEP_WORDS]
    for at in range(len(words) - 1, 2, -1):
        if words[at - 1].endswith((":", ";", ",")):
            words = words[:at]
            words[at - 1] = words[at - 1].rstrip(":;,")
            break
    else:
        while len(words) > 2 and (words[-1].lower().strip(",;:") in DANGLING
                                  or words[-1].endswith((",", ":", ";"))):
            words = words[:-1]
    return " ".join(words).strip(" ,;:")

# The words that make a clause a warning rather than an instruction to follow. They only count at
# the front: "coat the inside (not the elements)" is the instruction, with a warning inside it.
FORBADE = re.compile(r"^\s*(?:don'?t|do not|never|avoid|not)\b", re.I)

CLAUSE = re.compile(r";|,\s*(?:then\s+)?|(?<=\.)\s+|\s+then\s+", re.I)

# The person, so a line about the thing ("it boiled over") is not a step of theirs.
THEY_DID = re.compile(r"\b(?:i|i've|ive|i'd|id|we|we've|weve|we'd|wed)\b", re.I)

# The verb that says the step is finished, with the thing behind it: "i did the bicarbonate bit",
# "ive used the vinegar". This is what makes a noun a report of a step rather than a mention of
# the thing ("i hate this kettle" names the kettle and reports nothing).
FINISHED_IT = re.compile(
    r"\b(?:i|i've|ive|i'd|id|we|we've|weve|we'd|wed)\s+(?:already\s+|just\s+|now\s+|only\s+)?"
    r"(?:did|done|used|tried|gave|had|finished|started)\b", re.I)

# A line that is a lack, a mishap or a feeling, not a step: "i dont have any vinegar" is the
# thing stopping them, "i boiled it dry" and "it boiled over" are the job going wrong, and "i
# hate this kettle" wants a different reply entirely. These are the shapes of a line that is
# something to answer rather than a report of a step, so the reading passes the turn back.
NOT_A_STEP = re.compile(
    r"\b(?:dont|don't|doesnt|doesn't|didnt|didn't|havent|haven't|cant|can't|couldnt|couldn't|"
    r"wont|won't|ran out|run out|no|none|nothing|dry|over|broke|broken|breaks|burns?|burnt|"
    r"burned|spilt|spilled|ruined|stuck|stopped|hate|hates|fed up|sick of|gave up)\b", re.I)

# Action words that are about the person rather than the job, so the answer's "leave it" and
# the line's "left it" are not the same step said twice.
SOFT = frozenset("""
    leave left wait keep let give make use put take check see look wipe soak boil
""".split())
# The ends of a verb as people type them: "blotted", "blotting", "blots", "blot".
TENSE = re.compile(r"(?:ed|ing|s|d)$")


def _stem(word):
    """"blotted" -> "blot", "pouring" -> "pour", "boils" -> "boil"."""
    word = str(word or "").lower()
    if len(word) > 4 and word.endswith("ied"):
        word = word[:-3] + "y"
    word = TENSE.sub("", word)
    if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "lsz":
        word = word[:-1]
    return word


def _words(text):
    return [w for w in WORD.findall(str(text or "").lower().replace("\u2019", "'"))]


# A clause that says how to do the step, or that forbids a way of doing it, is part of the step
# before it and never a step of its own: "blot it, don't rub, with kitchen paper, then pour on
# cold water" is two instructions, not four.
# Words that point at something already said rather than name a step: a clause made only of
# these is a reference, and it cannot be handed back as an instruction.
POINTS_BACK = frozenset("""above below under over that this these those it them there here
same other one ones already again first last next then now""".split())

QUALIFIER = re.compile(
    r"^(?:don'?t|do not|never|avoid|not|which|that|with|about|for|in|on|until|repeating|again|"
    r"and repeat|using|leave it|keep|or|nor|as|at|by)\b", re.I)

VERB = re.compile(r"\b[a-z]{3,}(?:e|ed|ing|s)?\b")


# The words the answer is cut on that belong to the cut rather than to the step before it: the
# ant answer's "the ants keep coming for the first few days and then the stream thins out" splits
# at "then", and the step came out as "give the bait a week or two: the ants keep coming for the
# first few days and" - which was then handed back as "Next, ... first few days and."
JOINING = frozenset("""
    and or but nor so yet plus then also next
""".split())


def _steps(answer):
    """The answer cut at its clause breaks, which is where one instruction stops and the next
    starts: "blot it, don't rub, with kitchen paper, then pour on cold water and blot again"."""
    out = []
    for part in CLAUSE.split(str(answer or "")):
        part = part.strip(" .;,-")
        # The joining word the cut was made on is not part of the step: "and then" and ", so"
        # both leave it behind, and a step that ends on it reads as a sentence that stops short.
        words = part.split()
        while words and words[-1].lower().strip(" ,;:") in JOINING:
            words.pop()
        part = " ".join(words).strip(" ,;:")
        if not part:
            continue
        out.append(part)
    return out


def _doing(word):
    """"blotted" -> "blotting", so the lead-in reads like a person wrote it."""
    low = str(word or "").lower()
    if len(low) < 3:
        return ""
    if low.endswith("ing"):
        return low
    if low.endswith("ied") and len(low) > 4:
        base = low[:-3] + "y"
    elif low.endswith("ed") and len(low) > 3:
        base = low[:-2]
    elif low.endswith("s") and len(low) > 3:
        base = low[:-1]
    else:
        base = low
    if len(base) > 3 and base[-1] == base[-2] and base[-1] not in "lsz":
        return base + "ing"
    if base.endswith("e") and len(base) > 3:
        return base[:-1] + "ing"
    if (len(base) > 2 and base[-1] not in "aeiouwxy" and base[-2] in "aeiou"
            and base[-3] not in "aeiou"):
        return base + base[-1] + "ing"
    return base + "ing"


def _the_action(line):
    """The action the person says they have done, as a stem, or None.

    "it happened last night and i blotted it" -> "blot". The named thing has to be a verb in the
    past that is not one of the words the frame around it is made of.
    """
    words = [w for w in _words(line) if w not in FRAME]
    if not words:
        return None
    # The last action word in the line is the one they are reporting: the reason it happened
    # ("it happened last night") comes before what they did about it ("and i blotted it").
    for word in reversed(words):
        if len(word) < 4 or not TENSE.search(word):
            continue
        stem = _stem(word)
        if stem and stem not in FRAME and len(stem) > 2:
            return stem
    return None


def reply_for(text, memory):
    """The next step of the last answer, when the line says which step they are on."""
    line = " ".join(_words(text))
    if not line or len(line.split()) > SHORT:
        return None
    if A_QUESTION.search(str(text or "")):
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return None
    # The last turn the store holds is the one before this line, and it carries both the ask and
    # the answer it got. The turn being taken is only added once a module has answered, so it is
    # not in here: the answer this line is a report on is `turns[-1]`, never `turns[-2]`.
    last = turns[-1]
    if str(last.get("module") or "") != "answers":
        return None
    asked = str(last.get("user") or "")
    if not HOW_TO.search(asked):
        return None
    steps = _steps(last.get("bot"))
    if len(steps) < 2:
        return None
    # "it boiled over" and "it happened last night" are about the thing; a step is something the
    # person did, so the line has to have them in it.
    if not THEY_DID.search(str(text or "")):
        return None
    # A lack, a mishap or a feeling names the same words as a step and is not one: "i dont have
    # any vinegar" is what stopped them, and "i hate this kettle" is not about the descaling.
    if NOT_A_STEP.search(str(text or "")):
        return None
    action = _the_action(text)
    # A noun alone is not a step. "i did the bicarbonate bit" names the step by its thing with
    # the verb that says it is finished in front of it; "i hate this kettle" names a kettle and
    # reports nothing, so only a line with that verb may match the answer on its things.
    things = ({_stem(w) for w in _words(text) if w not in FRAME and len(w) > 3}
              if FINISHED_IT.search(str(text or "")) else set())
    if not action and not things:
        return None
    # The step they are on: the one whose clause uses their action, and is not a warning.
    done = None
    for at, step in enumerate(steps):
        if FORBADE.search(step):
            continue
        if action and action in {_stem(w) for w in _words(step)}:
            done = at
            break
    if done is None:
        # "i did the bicarbonate bit": the step is named by its thing rather than by a verb, so
        # the thing is what is matched - still against the answer's own words, never a list here.
        for at, step in enumerate(steps):
            if FORBADE.search(step):
                continue
            if things & {_stem(w) for w in _words(step)}:
                done = at
                break
    if done is None or done >= len(steps) - 1:
        return None
    # The step after theirs, said as a lead-in and one instruction: the person has the sheet in
    # front of them, so the next line is what they need, not the whole sheet again. A clause that
    # only says how, or forbids a way, belongs to the step before it.
    after = [step for step in steps[done + 1:] if not QUALIFIER.search(step)]
    if not after:
        return None
    said = after[0]
    # "and dry it in daylight" is the next instruction with its joining word on the front, which
    # reads as "Next, and dry it".
    said = re.sub(r"^(?:and|then|but|so|also|plus|next)\s+", "", said, flags=re.I)
    if len(said.split()) < 2:
        return None
    # A clause that only points at something said already ("above that", "below", "this one") is
    # not a step: the split reads "if your income is above that" as the next instruction and the
    # person is told "Next, above that.", which is not a thing anybody can do.
    if all(w in POINTS_BACK for w in _words(said)):
        return None
    said = _a_whole_step(said)
    # The step is spliced after a comma ("Next, pour on cold water") so its first letter comes
    # down: "Next, A front-clip harness helps" is not a sentence. A capital that names something
    # stays - "Next, Baking soda works too" - and the way to tell the two apart is that a name is
    # longer than one letter, or is the word "I". Without that, the article "A" reads as a name.
    first_word = said.split()[0]
    named_word = first_word.isupper() and (len(first_word) > 1 or first_word == "I")
    if said[:1].isupper() and not named_word:
        said = said[:1].lower() + said[1:]
    # "Blotting first is right" only when their action is the step's own verb: the step a thing
    # was named from ("a new washer is a couple of pounds") has no action of its own to praise.
    first = _words(steps[done])[:1]
    named = ""
    if action and first and _stem(first[0]) == action:
        named = _doing(action)
    if named in ("do", "doing", "go", "going", "did"):
        named = ""
    # Three ways to say the same thing, so two of these in a row do not read as a stamped card.
    shapes = (
        "Good - {doing} first is right. Now {step}.",
        "Right - {doing} is the first bit done. Now {step}.",
        "That was the right first move. Next, {step}.",
    )
    which = shapes[sum(map(ord, said)) % len(shapes)] if named else shapes[2]
    lead = which.format(doing=named, step=said)
    # A step that starts with "then" reads back as "now then", which is not English.
    lead = lead.replace("Now then ", "Now ")
    return lead
