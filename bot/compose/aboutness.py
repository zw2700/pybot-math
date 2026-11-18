"""Is a reply about the thing the line is about? One reading, used by the router and the arbiter.

STYLE.md asks for a reply that answers what the person asked, and the whole routing lane rests on
one test of that: **the reply says something the line is about**. A stock line ("I'm listening —
say more if it helps.", "Nice one. How did the rest of it go?") says nothing about the line at all,
so it reads as a reply only while the person happens to be talking about themselves in general.

Two things are deliberately *not* counted as saying something about the line:

* a **restatement**, where the reply is the line given back (60% of its words or more). STYLE.md
  calls that a restatement, and it names the subject without answering it.
* a **hedge** ("That's beyond what I know well, sorry", "I don't know enough to answer that
  honestly"), which is about the bot's knowledge, not about the line.

The words a line is about are its content words with the frame taken out, so "i went shopping and
hated every minute" is about shopping and minutes. Two words are the same word when the first
five letters agree, so `plumber`/`plumbers` and `move`/`moving` count as one.

This is a reading, not a verdict: `unlike_the_line` says the reply names none of the line's words.
A caller decides what to do with that, and the one-word answer is never enough on its own — see
`the_better_answer`, which needs two.
"""
import re

# The words a line is about: content words, with the frame words and light verbs taken out.
FRAME = frozenset("""
about after again all also and any anything are around because been before being both but can
could did does doing done down each even ever every for from get gets getting give given go goes
going gone got had has have having here him his her how into its just keep kept know knew like
long made make many may might more most much must need needed not now off once one only other our
out over own said same say says she should since some something still such take taken tell than
that thats the their them then there these they thing things think this those through time times
today told tomorrow tonight too took under until very want wanted was way well went were what
when where which while who whom why will with wont would yeah yes yet you your yours yourself
im ive ill id youre dont doesnt didnt cant couldnt wont isnt arent wasnt werent havent hasnt
hello hi hey thanks thank please sorry ok okay right sure fine good nice bad lot bit put puts
knows mean means meant seem seems felt feel feels look looks looking sound sounds
really stopping
anyway anyways btw honestly seriously basically literally actually whatever
""".split())

# A hedge answers a question about what the bot knows, not a question about the subject.
HEDGE = re.compile(r"beyond what i know|i don't know enough|not sure about that one|a search should",
                   re.I)
# How many letters make two words the same word (`plumber`/`plumbers`, `move`/`moving`).
STEM = 5
# A reply is the line given back at this share of the line's words or more.
RESTATEMENT = 0.6

_WORDS = re.compile(r"[a-z0-9']+")


# The ways a person puts one subject down and takes another up inside one line. What follows the
# marker is what this line is about; what came before it is the thread they left. "anyway" alone at
# the end of a sentence marks nothing, so the tail has to carry a few words of its own.
CHANGES_THE_SUBJECT = re.compile(
    r"\b(?:anyway|anyways|any\s+way|back\s+to|on\s+a\s+different\s+note|"
    r"on\s+another\s+note|changing\s+the\s+subject|change\s+of\s+subject|changing\s+tack|"
    r"while\s+i'?m\s+here|unrelated\s+but|that\s+aside|moving\s+on|by\s+the\s+way|btw|"
    r"different\s+question|other\s+thing)\b", re.I)


def after_a_change_of_subject(text):
    """What the line is about after the marker that puts the earlier subject down, or ''.

    "im fine really, anyway whats a good way to sell her furniture" is a furniture question: the
    first half is the thread they are leaving. Returned only when the tail carries words of its
    own, because a person who says "anyway" and nothing else has changed no subject yet.
    """
    line = str(text or "")
    tail = ""
    for found in CHANGES_THE_SUBJECT.finditer(line):
        tail = line[found.end():]
    tail = tail.strip(" \t,.;:!-\u2014-")
    if len(tail.split()) < 2:
        return ""
    return tail


def subject_words(text):
    """The words the line is about, as a set: content words minus the frame and the light verbs."""
    return {word for word in _WORDS.findall(str(text or "").lower())
            if len(word) >= 4 and word not in FRAME}


def names_the_subject(reply, about):
    """Which of `about` the reply actually says, by shared stem."""
    said = _WORDS.findall(str(reply or "").lower())
    found = set()
    for word in about:
        for other in said:
            if len(other) >= 4 and other[:STEM] == word[:STEM]:
                found.add(word)
                break
    return found


def restates_the_line(reply, text):
    """True when the reply is only the line given back, which names nothing by answering nothing."""
    said = set(_WORDS.findall(str(reply or "").lower()))
    mine = set(_WORDS.findall(str(text or "").lower()))
    return bool(mine) and len(said & mine) / len(mine) >= RESTATEMENT


def is_a_hedge(reply):
    """True when the reply is about the bot's knowledge rather than the line."""
    return bool(HEDGE.search(str(reply or "")))


def unlike_the_line(reply, text):
    """`(about, said)`: the words the line is about, and the ones the reply says.

    An empty `about` (a line with nothing but frame words) has no subject to be unlike, and a
    restatement or a hedge names nothing that counts, so both come back with an empty `said`.
    """
    about = subject_words(text)
    if not about:
        return about, set()
    if restates_the_line(reply, text) or is_a_hedge(reply):
        return about, set()
    return about, names_the_subject(reply, about)


def the_better_answer(reply, candidates, text, skip=None, need=2):
    """The candidate that names two or more of the line's words, when `reply` names none.

    `candidates` is the arbiter's list of proposals (`{"module", "priority", "reply"}`), `skip`
    the index of `reply`'s own candidate. Returns the index of the closer answer, or None. Two
    words, not one: a single shared word is how a stock line lands on a line about something else
    in the first place, so one word is not evidence that a reply is about the subject.

    `need` is the count the other reply has to reach. It is 2 for a general comparison, where one
    shared word is what a coincidence looks like, and 1 for a module that overrides the entries
    (`ANSWERS_INSTEAD`): that override rests on having read the whole line, so a reply that names
    nothing the line is about has not shown the reading the claim was made for.
    """
    about, said = unlike_the_line(reply, text)
    if not about or said:
        return None
    best = None
    best_named = need - 1
    for index, candidate in enumerate(candidates or ()):
        if index == skip:
            continue
        other = str(candidate.get("reply") or "")
        if int(candidate.get("priority") or 0) < 0:
            continue  # the fallback band apologises for everything; it is never the closer answer
        if restates_the_line(other, text) or is_a_hedge(other):
            continue
        count = len(names_the_subject(other, about))
        if count > best_named:
            best, best_named = index, count
    return best
