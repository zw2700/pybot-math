"""Panic: whose attack it is, and whether it is happening now.

The card for a panic attack is written for the person having one this minute - it says the attack
cannot hurt *you* and to ride it out. Lines the card did not fit were answered with it anyway:
somebody else's attack ("how do i help someone having a panic attack") and one that is over
("i used to have panic attacks every day"). The person in the room and the tense are the whole of
those two questions, so they are two rows here, beside the card rather than inside it: a row that
keys what it answers is easier to keep from taking the others.

A third row is one step further out again. "my husband has panic attacks" is a habit rather than a
minute, so the minute-by-minute card is an instruction for something that is not happening - but
the ordinary answer it was left with ("Got it. Is there anything you'd like a hand with?") helps
nobody who has just said what the trouble is either. A habit gets the week-to-week answer instead:
ask what helps, do not build a life around avoiding the places, and it is treatable.

The answers lane owns this domain.

The domain declares one topic. `feelings` is chat's job (`test_answers_contract` says a knowledge
answer must not be preferred on it), and both rows here are about a body in a bad minute rather
than about a feeling, so `health` is the whole declaration.
"""

from .lookup import NOT_A_NOSE, entry

ANSWERS = ("health",)

SOMEONE_ELSE = (
    "Stay with them and say it will pass, because it does: an attack peaks in about ten "
    "minutes. Sit them down, loosen anything tight at the neck, and breathe out loud with them "
    "- out for longer than in, so they have something to follow rather than an instruction. Do "
    "not argue with what they are frightened of and do not leave them alone to fetch anything. "
    "If they have never had one before, or there is chest pain with it, get medical advice "
    "rather than assuming it is panic.")

BEHIND_YOU = (
    "Then it is behind you, and getting through one is the thing to be pleased about rather "
    "than something to keep watch on. If one starts again, the out-breath is what helps - out "
    "for longer than in - and leaving the place it started rather than fighting it. If they "
    "come back often enough to shape your week, ask your GP about CBT: it is the treatment with "
    "the best evidence for panic.")

_ATTACK = ("panic attack", "panic attacks", "panicking", "panicky", "panics", "panicked",
           "cant breathe", "heart racing", "hyperventilating")

# The same attack under the name most people use for it: "my wife has anxiety attacks" was
# "Noted: your wife has anxiety attacks." This is the habit row's own half, not a word added to
# _ATTACK: the three rows above are read against each other, and adding a word to the shared half
# moved a line that was already answered well ("my husband had a panic attack yesterday" came back
# as "it is behind you", which thanks the wrong person).
_ANXIETY = ("anxiety attack", "anxiety attacks")

# The person who is having it, named from the outside: a relation, or a third person, or the
# word someone uses when the person is in the room and they are not.
_THEM = ("my mum", "my mom", "my dad", "my sister", "my brother", "my son", "my daughter",
         "my friend", "my mate", "my husband", "my wife", "my partner", "my boyfriend",
         "my girlfriend", "my colleague", "my boss", "my nan", "my nana", "my grandma",
         "my grandad", "my neighbour", "he is", "she is", "hes having", "shes having",
         "theyre having", "they are having", "someone", "somebody", "him", "her",
         # the same person in the past tense: "she had a panic attack at work" names somebody
         # else, and the card that speaks about them is the helping one.
         "he had", "she had", "they had")

# The attack is over, or it is one of a run of them that is not this minute. Two kinds of signal
# say so, and the second is the one a list of days cannot catch: a time named ("yesterday", "when i
# was 20") and the tense itself. "i had a panic attack yesterday" and "i used to get them" are the
# same question as "i had one last year", and a row keyed on the days alone drops the first two.
_BEHIND = ("last year", "last month", "last week", "last summer", "yesterday", "last night",
           "years ago", "a year ago", "months ago", "weeks ago", "ages ago", "a while ago",
           "in the past", "when i was", "used to", "have had", "had one before", "had a few",
           "had a panic", "has had", "was having", "kept having", "got them", "get them")

# The speaker is the one having it, whoever else is in the sentence: "im having a panic attack and
# my sister is watching" is not the helping-someone-else answer.
_MINE = ("im having a panic", "i am having a panic", "i think im having", "im panicking",
         "i am panicking", "ive been having panic", "im about to have a panic",
         "my panic attack")

# "my boss is panicking about the deadline" is dread about a thing, not an attack in the room: the
# ordinary word "panicking" covers both, and the word that tells them apart is the thing being
# worried about. A line that names one has the answer for coping with it, and this row would take
# the turn with the wrong card.
_WORRY_ABOUT = ("about the", "about this", "about that", "about her", "about his",
                "about their", "about work", "about money", "about exams", "about tomorrow")

# A past that is named in the line is behind whoever it happened to, so the helping card for the
# minute is not the answer even when the person named is somebody else: "my sister had a panic
# attack years ago" is the same question as "i had one years ago". Only the markers that cannot
# mean today are here - "had a panic attack" on its own stays with the helping card, because
# "my dad had one in the car" is often asked about what to do next time.
# The third person in the past tense, which is how the same evening reads from the outside:
# "my husband had a panic attack yesterday", "she had a panic attack at work".
_THEIR_OWN_PAST = ("he had", "she had", "they had", "he has", "she has", "they have",
                   "he gets", "she gets")

_BEHIND_THEM = ("years ago", "last year", "last month", "last week", "last summer",
                "in the past", "when i was", "when he was", "when she was", "used to",
                "months ago", "weeks ago", "a while ago")

# A line that offers another explanation - "is my son having panic attacks or is he just shy" - is
# asking whether it is panic at all, not how to help someone through one. The answer to that is
# "watch what happens and ask", and the helping card answers a question they have not asked yet.
_DIAGNOSIS = ("or is he just", "or is she just", "or is it just", "or is that just",
              "or am i just", "or just shy", "just shy", "or attention")

# "my son panics when he has to read out loud" is about a trigger rather than about an attack
# happening in the room: the question is what to do about reading aloud, and the helping card is
# for the minute it happens. A line that names when it happens has its own answer to be given.
_PATTERN = ("when he has to", "when she has to", "when they have to", "when i have to",
            "whenever", "every time", "each time")

# "my husband has panic attacks" is a habit, not a minute: nobody is on the floor, so "sit them
# down and breathe out loud with them" is an instruction for a moment that is not happening, and it
# is worse than the plain answer main gave. The verb alone cannot tell the two apart - "panics" is
# both - so the habit has its own markers, and the row stands down on them unless the line asks
# what to do about it: "my friend has panic attacks what can i do" is the question this card is
# for, and it keeps it.
# The habit is "<has|have|gets|get> <the attack>", and the attack has more than one name, so the
# phrases are built from the names rather than written out: "my wife has anxiety attacks" was
# "Noted: your wife has anxiety attacks." because only the word "panic" was spelled out here.
_ATTACK_NAMES = ("panic attacks", "anxiety attacks", "panics")
_HABIT_VERBS = tuple(f"{verb} {name}" for name in _ATTACK_NAMES
                     for verb in ("has", "have", "gets", "get", "had", "having"))
# A place or a frequency on its own says a habit only when nothing in the line says this is one
# evening that is over: "my wife panics at work" is how often it happens, but "she had a panic
# attack at work" is where it happened, and the helping card is the answer to that one.
_HABIT_MARKERS = ("panics", "panicked", "every day", "every week", "every few days", "usually",
                  "tends to", "at school", "before exams", "on the tube", "at work",
                  "in meetings", "a lot")
_HABIT_ONCE = (" had ", " panicked", " was having", " kept having", " last ", " on the way")
_HABIT = _HABIT_VERBS + _HABIT_MARKERS
_ADVICE_ASK = ("what can i do", "what do i do", "what should i do", "how do i help",
               "how can i help", "how do i calm", "how do i talk", "what can i say",
               "how do i support", "what helps", "any advice", "what can we do")


# The same habit, asked as a fact about somebody they live with: "my partner has panic attacks and
# i dont know what to do". Nobody is on the floor, so the minute-by-minute card is the wrong
# instruction - but "Got it. Is there anything you'd like a hand with?" is no help either, because
# the person has just said what they need. What answers it is the week-to-week version: what to ask,
# what not to arrange your life around, and that it is treatable.
LIVING_WITH = (
    "Ask them, on a calm day, what helps when one starts - most people know, and being asked is "
    "worth more than being managed. What helps most between attacks is not avoiding the places "
    "they happen: the list of avoided things grows, and the fear with it. Panic disorder is "
    "treatable, so it is worth a GP conversation: CBT has the best evidence, and an SSRI helps "
    "some people alongside it. If the attacks are getting more frequent, or they start avoiding "
    "work, shops or travel, say so to the GP rather than waiting. And if one ever comes with "
    "chest pain, or it is their first, get it checked rather than assuming panic.")


def _a_flat_habit(understood):
    """True on a habit stated flatly, which is the one line this row is written for."""
    return not _a_habit_is_not_a_minute(understood)


def _the_attack_is_the_speakers_own(understood):
    """True when the past card is the right card, which is the speaker's own attack.

    "my husband had a panic attack yesterday" is the same evening seen from the outside. The past
    card thanks *you* for getting through it, and it took those lines off the helping card when
    the habit row arrived; telling the person what to do for somebody else is the helping card's
    job, and it says "them" throughout. A past that is a long way back keeps the past card,
    whatever the person, because there the question really is whether it is behind them.
    """
    low = " " + _text(understood) + " "
    if any((" " + mine + " ") in low for mine in _MINE):
        return True
    if any((" " + own + " ") in low for own in
           ("i had", "ive had", "i have had", "i get", "i used to", "i was having")):
        return True
    if any((" " + back + " ") in low for back in _BEHIND_THEM):
        return True
    return not any((" " + them + " ") in low for them in _THEM + _THEIR_OWN_PAST)


def _the_line_asks_what_to_do(understood):
    """True when a habit line is asking for the advice, which is the one time this card fits."""
    low = " " + _text(understood) + " "
    return any((" " + phrase + " ") in low or low.strip().startswith(phrase)
               for phrase in _ADVICE_ASK)


def _a_habit_is_not_a_minute(understood):
    """False on a habit stated flatly, true when the line asks what to do about it."""
    low = " " + _text(understood) + " "
    habit = any((" " + phrase + " ") in low for phrase in _HABIT_VERBS)
    if not habit:
        once = any(phrase in low for phrase in _HABIT_ONCE)
        habit = (not once) and any((" " + phrase + " ") in low for phrase in _HABIT_MARKERS)
    return (not habit) or _the_line_asks_what_to_do(understood)


def _text(understood):
    """The line as lower-case words, the way the other tables read one."""
    words = understood.get("words") if isinstance(understood, dict) else None
    if isinstance(words, (list, tuple)) and words:
        return " ".join(str(word) for word in words).lower()
    return str((understood or {}).get("clean") or "").lower()


ENTRIES = [
    entry("panic-someone-else", (_ATTACK, _THEM), SOMEONE_ELSE, bias=2,
          avoid=_MINE + _DIAGNOSIS + _PATTERN + _WORRY_ABOUT + _BEHIND_THEM + NOT_A_NOSE,
          guard=_a_habit_is_not_a_minute),
    entry("panic-attack-in-the-past", (_ATTACK, _BEHIND), BEHIND_YOU, bias=2,
          avoid=("im having a panic", "i am having a panic", "right now"),
          guard=_the_attack_is_the_speakers_own),
    entry("panic-someone-else-habit", (_ATTACK + _ANXIETY, _THEM), LIVING_WITH, bias=1,
          avoid=_MINE + _DIAGNOSIS + _PATTERN + _WORRY_ABOUT + _BEHIND_THEM + NOT_A_NOSE,
          guard=_a_flat_habit),
]
