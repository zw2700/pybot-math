"""A follow-up that says the trouble came back: the answer's own next step is the reply.

"the boiler keeps losing pressure" gets the answer, and the next line is "top it up and it came
back after a week". Nothing reads that line as being about the answer, so it fell to the
fallback pools - "I'm listening, say more if it helps", "Got it - it came back after a week" -
which throw away the answer the person is telling you has not held. The answer already says what
to do at that point ("If it keeps dropping, there's a leak somewhere: stop topping it up and get
a heating engineer out"), and that sentence is the reply: nothing is invented, and the person
gets the step they are owed instead of their own words handed back.

The rule is narrow on purpose:
* the line has to say the thing itself came back ("it came back", "its back", "back again"), not
  the person going somewhere ("i went back to work today") and not a thing being handed over
  ("should i give it back to the shop");
* the turn before has to be an answer, so nothing is read out of a greeting, a hedge or an
  emergency;
* the answer has to hold a sentence that says what to do if it recurs. Most answers do not, and
  then this module says nothing and the rest of the bot answers as it did.
"""
import re

# The thing came back, said with a pronoun or a noun that stands for it. A person going back
# somewhere is the same three words ("i came back from holiday"), so the subject is what decides:
# only a thing the person has been trying to get rid of comes back.
RETURNING = re.compile(
    r"\b(?:it|that|this|they|the (?:same )?(?:problem|trouble|issue|fault|leak|smell|noise|"
    r"pain|spot|mould|damp|drip|mark|stain|rash|ache|cough|itch|swelling|spots|noises|pains|"
    r"leaks|smells|rashes|aches|coughs|itches)s?)\s+"
    r"(?:(?:'s|is|was|has|had|have|came|comes|come|keeps coming|kept coming|keep coming)\s+)"
    r"(?:\w+\s+){0,2}back\b"
    r"|\b(?:its|it's|they're|theyre)\s+back\b"
    r"|\b(?:it|that|this)\s+has\s+(?:come|came)\s+back\b"
    r"|\bback again\b")
# The same report said as a change of state: "its dropped again", "its started again", "its
# happening again", "still doing it". The verb that carries it is the trouble going back to how it
# was, and the marker that makes it a recurrence is "again" or "still"; a subject ("it", "that",
# "the leak") keeps it apart from the person doing something ("lets try again", "i still want to
# go"). Without those three the line is about something else and this module keeps out of it.
AGAIN = re.compile(
    r"\b(?:it|its|it's|that|thats|that's|they|theyre|they're|this|"
    r"the (?:same )?(?:problem|trouble|issue|fault|leak|smell|noise|pain|ache|rash|drip|mould|"
    r"damp|blockage|spots?|pains?|noises?|leaks?|spots?))\s+"
    r"(?:has |have |had |is |was |keeps? |kept |just |only |still |all |already |again )*"
    r"(?:dropped|drop|drops|dropping|started|starting|starts|happened|happens|happening|"
    r"come back|came back|comes back|come|came|gone|gone off|returned|return|done it|does it|"
    r"doing it|played up|plays up|playing up|acting up|acts up|acted up|flared up|flares up|"
    r"flaring up|stopped working|broken|broke|failed|fails|failing|blocking|blocked|"
    r"back|no better|not better|not clearing|not cleared|just as bad|as bad|worse|better)\b",
    re.I)
RECURRING = re.compile(r"\b(?:again|still|no better|not better|worse than before|"
                       r"just as bad|as bad as before)\b", re.I)
# Said once, these are the recurrence itself: nothing needs adding to make "it returned" or "the
# pain flared up again" a report that the trouble is as it was.
SELF_EVIDENT = re.compile(
    r"\b(?:returned|return|came back|come back|coming back|keeps? coming|kept coming|"
    r"keeps? (?:dropping|failing|blocking|breaking|playing up|acting up|flaring up)|"
    r"flared up|flaring up|back again)\b", re.I)
# A line that asks whether it will come back is a prediction ask, not a report: the answer says
# what happened and the person asks what happens next, which is somebody else's turn.
ASKING = re.compile(
    r"^(?:will|would|does|do|did|is|are|was|were|can|could|should|why|when|how|what|where|who|"
    r"shall)\b")

# The sentence of an answer that says what to do when the trouble recurs, which is the one the
# person has just earned. "If it keeps dropping", "if it comes back", "if that happens again",
# "if it does not clear up".
NEXT_STEP = re.compile(
    r"\b(?:if|when|once)\s+(?:it|that|this|they|things)\s+"
    r"(?:keeps?|still|comes? back|come back|returns?|happens? again|does it again|doesn'?t|"
    r"does not|hasn'?t|has not|has been|have been|lasts?|persists?|keeps up|won'?t|"
    r"will not|is no better|isn'?t better|isn'?t clearing|is not clearing|gets worse)", re.I)
SENTENCE = re.compile(r"(?<=[.!?])\s+")

# A turn whose reply is not advice to build on: an emergency answer owns the turns after it, and
# a greeting, a hedge or a joke holds no next step to hand back.
NOT_AN_ANSWER = ("safety", "urgent", "grief", "loss")

# The same point reached as a question rather than a report: "and if it does not get better in two
# weeks", "what if it gets worse", "and if it doesnt clear up". The answer already says when to
# get the thing seen, and that sentence is what a friend says to this - so the conditional is read
# here and the sentence is handed over, instead of the line reaching nothing and the bot saying
# "is there anything you'd like a hand with?".
CONDITIONAL_ASK = re.compile(
    r"^(?:and|but|so|then)?\s*(?:what\s+)?if\s+"
    r"(?:it|that|this|they|theyre|it's|things|the\s+\w+)\s+"
    r"(?:does\s?n[o']?t|does not|did\s?n[o']?t|did not|is\s?n[o']?t|is not|has\s?n[o']?t|"
    r"has not|have\s?n[o']?t|gets?|stays?|keeps?|lasts?|still|stops?|eases?|"
    r"no better|not better|not clearing)\b", re.I)


def reads_as_returning(text):
    """True when the line reports that the thing the answer was about has come back."""
    line = " ".join(str(text or "").lower().split())
    if not line or len(line.split()) > 16:
        return False
    if ASKING.match(line):
        return False
    if RETURNING.search(line):
        return True
    return bool(AGAIN.search(line) and (RECURRING.search(line) or SELF_EVIDENT.search(line)))


def _the_turn_before(memory):
    turns = [turn for turn in (memory or {}).get("turns") or [] if isinstance(turn, dict)]
    return turns[-1] if turns else None


def _the_answer_before(memory, keep=4):
    """The last thing the bot said that holds a next step, or None.

    Not simply the turn before: a nod in between ("Got it - you topped it up yesterday") is not
    the answer, and reading the recurrence against it lost the step the person has earned -
    "my boiler keeps losing pressure" / "i topped it up yesterday" / "its dropped again" said
    "It's dropped again - noted" instead of "there's a leak somewhere: stop topping it up". An
    emergency answer still owns the turns after it, so the walk stops there.
    """
    turns = [turn for turn in (memory or {}).get("turns") or [] if isinstance(turn, dict)]
    for turn in reversed(turns[-keep:]):
        if str(turn.get("module") or "") in NOT_AN_ANSWER:
            return None
        if the_next_step(turn.get("bot")):
            return turn
    return None


# The conditional is the answer's own hinge - "if it returns,", "if it keeps dropping," - and it
# is already in the sentence the person read. Dropped from the front, what is left is what a
# friend says to "it came back": "the cause is damp, not the paint". Left on, the reply is that
# sentence read out again word for word, which STYLE has no room for.
LEADING_CONDITION = re.compile(
    r"^(?:if|when|once)\s[^,.;:]{0,80},\s*(?=[A-Za-z])", re.I)
# The condition can be a list - "If it has been more than six weeks, keeps waking you up, or comes
# back every time" - and taking off the first clause of that leaves "keeps waking you up, or comes
# back every time, ask your GP", which is not a sentence. When what follows carries the list on,
# the condition stays whole.
CONTINUES = ("or", "and", "keeps", "keep", "kept", "comes", "come", "still", "lasts", "persists",
             "gets", "goes", "happens", "does", "hasn't", "has not", "isn't", "is not", "won't",
             "will not", "stops", "swells", "spreads", "bleeds", "hurts", "wakes")


def the_next_step(reply):
    """The sentence of an answer that says what to do if the trouble recurs, or None.

    The conditional is taken off the front of it, because the person has already read the
    sentence it belonged to. A conditional in the middle of a sentence ("see a GP if it is no
    better in a fortnight") is left whole: cutting that would leave a fragment.
    """
    for sentence in SENTENCE.split(str(reply or "").strip()):
        sentence = sentence.strip()
        if not sentence or not NEXT_STEP.search(sentence):
            continue
        bare = LEADING_CONDITION.sub("", sentence)
        if bare and bare != sentence and len(bare.split()) >= 4 \
                and bare.split()[0].lower().strip(",.;:") not in CONTINUES:
            return bare[:1].upper() + bare[1:]
        if sentence.lower().startswith(("if ", "when ", "once ")):
            # The conditional will not come off, so the sentence is half of one: "If it has been
            # more than six weeks, keeps waking you up, or comes back every time, ask your GP"
            # said on its own is a fragment that answers nothing. Nothing comes back instead.
            continue
        return sentence
    return None


# A line that says the thing happened once more, said as news rather than as a request to hear the
# answer again: "my back is sore again", "and the rota changed again this morning", "its dropped
# again". The recurrence word is what carries it, and a time word may follow it ("again this
# morning"). The store hands a repeat route its line in a packed form ("dropped again of boiler
# keep losing pressure"), so a recurrence word just before "of" counts too.
RECURRENCE = re.compile(
    r"\b(?:again|still)\b\s*(?:(?:today|tonight|this morning|this afternoon|this evening|"
    r"this week|already|now|too|though)\b\s*)*(?:[.!]*$|of\b)", re.I)
# The shapes that ask for the answer back instead: "what was the headache thing again", "remind me
# again", "what did you call it again". The frame is for these and only these.
REMIND_ME = re.compile(r"\b(?:remind|refresh my memory|what (?:was|is|were|did))\b", re.I)
# A line that opens on one of these is asking something, not reporting that the thing is back:
# "how do i cook rice again" is the same ask a second time and the answer under a lead saying it is
# the same one is the right reply. A report opens on its subject ("my back is sore again", "and the
# rota changed again this morning") and never on an ask.
AN_ASK = re.compile(
    r"^(?:how|what|when|where|which|who|why|can|could|should|shall|will|would|may|might|"
    r"do|does|did|is|are|am|was|were|have|has|any|is there|are there)\b", re.I)


def says_it_happened_again(text):
    """True when the line reports the thing happening once more, so a repeat frame is wrong.

    A repeat frame says "same answer as before", and that is a wrong thing to say to news: the
    person is telling the bot the trouble has come back, not asking it to read the old answer out.
    Standing down hands the line to the modules that answer a return - which have the next step
    the first answer could not know about ("Then say it once, plainly, about the next change").
    """
    said = " ".join(str(text or "").lower().split())
    if not said or REMIND_ME.search(said) or AN_ASK.match(said):
        return False
    if reads_as_returning(said):
        return True
    return bool(RECURRENCE.search(said))


def reads_as_a_conditional(text):
    """True when the line asks what happens if the trouble is still there.

    Not the same as a recurrence report: nothing has come back yet, the person is asking about the
    branch the answer named - "and if it does not get better in two weeks" after a rash answer.
    """
    said = " ".join(str(text or "").lower().split())
    return bool(CONDITIONAL_ASK.match(said))


def pool_for(text, memory):
    """The next step the answer already names, or None when this line is not that follow-up.

    Returned as the sentence itself: it is the bot's own advice, said again because it now
    applies, and a lead-in in front of it ("same answer, and it covers this") would claim the
    whole answer still stands when the part that matters is the branch the person has reached.
    """
    conditional = reads_as_a_conditional(text)
    if not reads_as_returning(text) and not conditional:
        return None
    before = _the_answer_before(memory)
    if not before:
        return None
    said = str(before.get("bot") or "")
    step = the_next_step(said)
    if not step:
        return None
    if " ".join(step.lower().split()) == " ".join(said.lower().split()):
        return None  # the answer was that one sentence, and it is already on the screen
    if conditional:
        # The branch is only worth handing back when there was an answer around it: "Sorry to hear
        # it. Ring the vet if it gets worse" is the whole of what the bot said, so saying the
        # branch again reads the answer out twice, with the question it already asked on the end.
        around = " ".join(said.replace(step, " ").split())
        if len(around.split()) <= 8:
            return None
    return step


def the_whole_of_it(text, memory):
    """The answer the step was cut from, for the store's record of what has been said.

    The person has now read every part of that answer: the fix on the first turn, and the branch
    for the trouble coming back on this one. Keeping only the branch lets the rest of it be handed
    over as new a turn later, which reads as the bot forgetting itself.
    """
    if not reads_as_returning(text):
        return None
    before = _the_answer_before(memory)
    said = str((before or {}).get("bot") or "")
    return said if the_next_step(said) else None
