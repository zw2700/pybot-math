"""The words for a child, asked for one turn after the death.

`my husband died this morning and i have to tell the kids` is answered by the composer's pool for
the first hour (the condolence, then the one thing worth knowing). The person then asks the
follow-up every parent asks - "how do i tell a 4 year old", "what do i say to my son" - and
without this reading the line goes to whatever else matches the child in it: the card on screen
time ("Match the limit to the age: under two, video calls and the odd photo only"), the search
hedge, or the drafter that asks them to send the gist so it can be written up. None of those is
the words.

Two callers need the same reading, which is why it lives here on its own:

* bot/compose/fallback.py answers the ask from `THE_WORDS_FOR_A_CHILD`;
* bot/modules/arbiter.py gives it the turn over the card that matched the age, because a card
  about screen time answers how many hours and this turn is "what do i say".

The reading is narrow on purpose: it needs the ask shape, a child named in the ask, and a death
in the thread the bot has just been condoled about. The same ask in an ordinary conversation
("we are moving in june" / "how do i tell my son") keeps its card, and a line that names its own
subject ("how do i tell my son that i lost my job") keeps its own answer.
"""
import re

from .fallback import A_CHILD_DIED, A_DEATH_IN_THE_LINE, A_SUICIDE_IN_THE_LINE

# The ask for the words themselves. Both forms people use - "how do i tell" and "what do i say
# to" - because they are the same question, and the second is the one that reached the hedge.
TELL_ASK = re.compile(
    r"\b(?:how|what)\s+(?:do|should|can|would|will)\s+(?:i|we)\s+"
    r"(?:tell|say|word|phrase|put it|put)\b"
    r"|\bhow do i put (?:it|this)\b|\bwhat do i tell\b")
# The person the words are for, which has to be a child. "how do i tell my boss" and "what do i
# say to the funeral director" are the same ask shape and a different question, and the thread
# reading alone would answer them with the words for a child.
A_CHILD_IN_THE_ASK = re.compile(
    r"\b(?:kid|kids|child|children|son|daughter|boy|boys|girl|girls|toddler|little one|"
    r"teenager|teen|baby|niece|nephew|grandson|granddaughter|"
    r"(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})[- ]"
    r"(?:year|yr)s?[- ]old)\b")
# What may follow the child and still leave the ask about the death: the filler people put round
# it ("please", "properly", "tonight"), the death itself said again ("that daddy died"), and the
# person who died named by their relation ("about his dad", "the truth about his mum"). Anything
# else after the child has a subject of its own - "how do i tell my son im pregnant", "how do i
# tell my daughter shes going to be a big sister", "how do i tell my son i got the job" - and the
# card for that subject owns the answer. The guard used to be a list of introducing words
# (that/about/whether/why), which missed every other tail: the pregnancy line was answered with
# "their name, that they died".
TAIL_FILLER = frozenset("""please now then too ok okay soon gently first properly exactly tonight
today tomorrow at bedtime the a an this that it and but so just really here you i we my""".split())
TAIL_ABOUT_THE_ONE_WHO_DIED = frozenset("""about his her their them of on with dad daddy mum mummy
mom mommy mother father gran granny grandma grandad grandpa nana nan brother sister uncle aunt dog
cat pet name what happened truth""".split())
# "lost" is deliberately not here: "how do i tell my son that i lost my job" is a subject of its
# own, and the card for it answers the line. A death is said as died, dead, passed, gone.
_A_PERSON_IN_THE_TAIL = re.compile(
    r"\b(?:dad|daddy|mum|mummy|mom|mommy|mother|father|gran|granny|grandma|grandad|grandpa|nana|"
    r"nan|brother|sister|uncle|aunt|dog|cat|pet)\b")
A_DEATH_IN_THE_TAIL = re.compile(
    r"\b(?:died|dead|dying|dies|death|passed|passing|gone|killed|funeral|buried|cremated)\b")


def _the_tail_after_the_child(text):
    """The words after the last child named in the ask, or None when no child is named."""
    last = None
    for match in A_CHILD_IN_THE_ASK.finditer(text):
        last = match
    if last is None:
        return None
    return text[last.end():]


def _the_tail_is_about_the_death(tail):
    """True when what follows the child leaves the ask about the death, and not about something else."""
    words = re.findall(r"[a-z']+", tail or "")
    if not words:
        return True                       # "how do i tell my son"
    if A_DEATH_IN_THE_TAIL.search(tail):
        # The person has already said what to say and who it is about ("that daddy died"), and the
        # plain-words answer for that shape is more concrete than a pool can be: it keeps the turn.
        return not _A_PERSON_IN_THE_TAIL.search(tail)
    for word in words:
        if word in TAIL_FILLER or word in TAIL_ABOUT_THE_ONE_WHO_DIED:
            continue
        return False                      # a subject of its own: pregnant, the job, a big sister
    return True

# The words, in three ways of saying them. Every line names the two things a child has to be
# told - that the person died and that they are not coming back - and none of them softens the
# death into sleep or a journey, because those are the words the entry exists to talk people out
# of. The person is "their name": a wife, a grandmother and a dog are the same line, and the bot
# does not know the family's word for any of them.
THE_WORDS_FOR_A_CHILD = (
    "Keep it to a sentence or two, with their name and the plain word: they died, and they are "
    "not coming back. Then answer whatever the child asks, in the same words, and if they ask "
    "again next week - they will - say the same thing again.",
    "Say it plainly and soon: their name, and that they died. Not asleep, not gone away, and not "
    "\"lost\" - a child takes those words literally, and then waits for them to wake up. What "
    "follows can come from their questions.",
    "The words are the ones you would use to an adult, just shorter: their name, that they died, "
    "and that they will not be coming back. It is all right for the child to see you cry - that "
    "is how they learn it is all right to be sad.",
)


def a_death_in_the_thread(memory, look_back=3):
    """True when the person said a death in one of their last few lines.

    The bot's own last line is not enough to go on: the condolence for "my mum died yesterday"
    comes from another module's pool (bot/compose/loss.py, LOSS_REPLIES), so a death said one
    turn ago reads as no thread at all when only the composer's own pools are checked, and the
    ask after it went to the search hedge. The person's own lines say what the conversation is
    about, and two asks in a row ("how do i tell a 4 year old", then "what about my son") both
    still have the death behind them.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        said = " ".join(str(turn.get("user") or "").lower().split())
        if said and A_DEATH_IN_THE_LINE.search(said):
            return True
    return False


def asks_the_words_for_a_child(clean, memory):
    """A how-do-I-tell ask about a child, in a thread where somebody has died.

    Narrow on purpose. Both halves are needed: the ask shape and the thread. A line inside a
    loss thread that is not this ask keeps its own answer, and this ask outside a loss thread is
    an everyday how-to. A suicide among the people they know is left to the safety readings, and
    a line whose speaker names the child who died is not the same telling ("my son died and I
    have to tell my daughter" is the condolence's turn, which the readings above already give).
    """
    text = " ".join(str(clean or "").lower().split())
    if not text:
        return False
    if not (TELL_ASK.search(text) and A_CHILD_IN_THE_ASK.search(text)):
        return False
    try:
        if not a_death_in_the_thread(memory):
            return False
        thread = _the_last_few_lines(memory)
    except Exception:  # noqa: BLE001 - a reading that fails just answers nothing
        return False
    if A_SUICIDE_IN_THE_LINE.search(thread) or A_SUICIDE_IN_THE_LINE.search(text):
        return False
    if A_CHILD_DIED.search(text):
        return False
    # A line whose tail names its own subject is telling the child something else: "how do i tell
    # my son that i lost my job", "how do i tell my son im pregnant" are not the death's telling,
    # and the card for that subject answers them.
    tail = _the_tail_after_the_child(text)
    if tail is None or not _the_tail_is_about_the_death(tail):
        return False
    return True


def _the_last_few_lines(memory, look_back=4):
    """The recent lines of the conversation, the person's and the bot's, as one string."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    lines = []
    for turn in turns[-look_back:]:
        lines.append(str(turn.get("user") or ""))
        lines.append(str(turn.get("bot") or ""))
    return " ".join(lines).lower()
