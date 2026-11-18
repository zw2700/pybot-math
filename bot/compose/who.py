"""Who to see, when the follow-up asks for the person and not the advice again.

"my back hurts" gets what to do about it. "who should i see" is a second, different ask: it wants
the person and the way in - a GP, a vet, a dentist, a physio - and nothing else in the line. On
main it got the advice a second time (the back paragraph, the scratching paragraph), the flat
"That is everything I have on that one", or the search hedge.

The person is usually already in the bot's own last line: the answer to a symptom, a pet or a
child's rash names the one to go to, because that is how the entry ends. So this reads the person
out of that answer and hands that sentence back, with one line of its own on how to get to them.
Nothing is invented about the subject: the sentence was said a moment ago, and the line after it
is only about booking, not about the condition.

When the answer named nobody (the worry answer, the low-mood answer), the person comes from the
topic the line was read as: health and low mood to a GP, pets to a vet, with the obvious exception
read off the thread ("tooth" is a dentist, not a GP). Anything else - a household fault, a money
question, a bereavement - is left alone, because those threads already answer "who do i call"
themselves.

It only reads a line that is nothing but the ask (a bare "who should i see", "who do i call then",
"who to ask about it"): a line that carries its own subject ("who do i call about the boiler",
"which doctor is best for skin") belongs to the entry that knows the subject.
"""
import re

from ..memory import holds as earlier
from ..understanding import understand

from . import pick

# The person, as the reply calls them, the words that name them in an answer, and the way in.
# The order matters only when one answer names two: the earlier name in the text wins, which is
# how "your health visitor or the 111 line" answers with the health visitor.
EXPERTS = (
    ("health visitor", re.compile(r"\bhealth visitors?\b", re.I),
     ("ring them and they will talk it through with you today",
      "ring them and describe what you have seen: they would rather hear from you than not")),
    ("vet", re.compile(r"\bvets?\b|\bvet's\b|\bveterinary\b", re.I),
     ("ring the practice and say how long it has been going and what you have already tried",
      "book an appointment and take a note of what you have seen and any treatment they are on")),
    ("dentist", re.compile(r"\bdentists?\b|\bhygienist\b|\bdental (?:practice|surgery)\b", re.I),
     ("ring the practice and ask for the earliest appointment",
      "ring the practice and ask for an urgent slot")),
    ("GP", re.compile(r"\bgp\b|\bgp's\b|\bdoctors?\b|\bfamily doctor\b", re.I),
     ("ring the surgery and ask for the earliest appointment",
      "book in and take a note of when it started and what makes it worse")),
    ("physio", re.compile(r"\bphysios?\b|\bphysiotherapist\b", re.I),
     ("you can usually book with one directly, without going through a GP",
      "book an appointment and take a note of when the pain comes on")),
    ("optician", re.compile(r"\bopticians?\b|\boptometrist\b", re.I),
     ("book an eye test, and say if anything has changed suddenly",
      "ring them and say what has changed, and they will say how soon to come in")),
    ("pharmacist", re.compile(r"\bpharmacists?\b|\bchemist\b", re.I),
     ("they can advise today without an appointment",
      "ask at the counter, and take the packet of anything you already take")),
    ("midwife", re.compile(r"\bmidwives?\b|\bmaternity unit\b", re.I),
     ("ring your midwife or the maternity unit and they will say how soon to be seen",
      "ring the maternity unit rather than waiting for the next appointment")),
    ("nurse", re.compile(r"\bpractice nurse\b|\bnurse\b", re.I),
     ("ring the surgery and ask whether the practice nurse can see you",
      "ask at the desk for the practice nurse")),
)

# What the reply calls the person, as the front of the sentence.
LEAD = {
    "health visitor": "Your health visitor",
    "vet": "A vet",
    "dentist": "A dentist",
    "GP": "Your GP",
    "physio": "A physio",
    "optician": "An optician",
    "pharmacist": "A pharmacist",
    "midwife": "Your midwife",
    "nurse": "The practice nurse",
}

# A bare ask for the person: nothing in it but the who. The subject sits in the answer above.
WHO_ASK = re.compile(
    r"^(?:(?:and|so|ok|okay|but|right|then|well)\s+)*"
    r"(?:"
    r"who\s+(?:should|shall|do|can|could|would|must|might|am\s+i)\s+(?:i|we)\s+"
    r"(?:see|call|ring|contact|ask|book|speak\s+to|talk\s+to|go\s+and\s+see|go\s+to|"
    r"get\s+in\s+touch\s+with|be\s+seeing|need\s+to\s+see)"
    r"|who\s+(?:to\s+(?:see|call|ring|ask|contact|speak\s+to|talk\s+to))"
    r"|who\s+do\s+i\s+need\s+to\s+(?:see|call)"
    r"|which\s+(?:doctor|dentist|vet|specialist|professional|person|one)\s+"
    r"(?:should|do|would)\s+i\s+(?:see|call|ring|go\s+to)"
    r"|where\s+do\s+i\s+go\s+for\s+(?:it|that|this)"
    r")"
    r"(?:\s+(?:about|for|with)\s+(?:it|that|this|them|someone))?"
    r"(?:\s+(?:then|now|instead|first|please|again|next))?"
    r"[\s,.!?]*$",
    re.I,
)

# The lead-in of a long sentence, before the person, is not part of the referral: "weeks of it is
# not a bad day any more, and it is worth saying to a GP" is a referral from the "and".
PREAMBLE = re.compile(r"(?:,\s*(?:and|but|so)\s+|;\s*|\.\s+)", re.I)

# A clause that names the person early enough says the whole thing by itself: "See a GP if it is
# no better in a fortnight" and "your health visitor will talk it through with you" need no lead
# in front of them, while "the worst headache you have ever had ... is a same-day job for a doctor"
# is about the condition and wants the person put in front.
EARLY = 45

# The person a thread is about when the answer named none. A family thread is here because a
# parent who keeps falling or a child who will not sleep is a GP conversation: without it the
# bare "who do i ring" over a care thread fell through to the search hedge.
BY_TOPIC = (
    ("pets", "vet"),
    ("health", "GP"),
    ("feelings", "GP"),
)

# What the thread itself is about, which beats the topic: a sore tooth is a dentist, not a GP.
# Read only when the person is coming from the topic, so a boiler's filling loop is not a filling.
THREAD = (
    ("dentist", re.compile(r"\btooth\b|\bteeth\b|\bgums?\b|\bdental\b|\bdentist\b|\bmolar\b|"
                           r"\babscess\b|\bbraces?\b", re.I)),
    ("optician", re.compile(r"\beyes?\b|\beyesight\b|\bvision\b|\boptician\b|\bblurry\b|"
                            r"\bblurred\b|\bcontact lenses?\b", re.I)),
    ("midwife", re.compile(r"\bpregnan|\bmidwife\b|\bmaternity\b|\bunborn\b", re.I)),
)

# An answer from one of these bands is not a subject to name a person for: a safety line says
# call 999 now, and "Your GP: ring the surgery" after it would be the wrong thing to say.
QUIET = frozenset(("safety", "urgent", "grief", "loss"))

# Only care threads are read for the exception: "the filling loop" on a boiler thread is a
# filling, and a dog's teeth are the vet's.
CARE_TOPICS = frozenset(("health", "feelings", "family-and-parenting"))


def _flat(text):
    text = str(text or "").strip().lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", text)


def asks_who(text):
    """True when the line is nothing but a request for the person to see."""
    return bool(WHO_ASK.match(_flat(text).strip(" .!?")))


def _last_module(memory):
    return earlier.last_module(memory)


def _last_reply(memory):
    return earlier.last_reply(memory)


def _names_no_subject(line):
    """True for a line that only says to go on: "what can i do", "and then", "thanks".

    The understander's keywords are what is left of a line once the grammar is gone, so a line
    with none of them named nothing: it is a follow-up about the subject before it.
    """
    if asks_who(line):
        return True
    read = understand(_flat(line), {})
    return not [word for word in (read.get("keywords") or []) if len(word) > 2]


def _the_subject(memory):
    """(turn index, the answer to it) for the last line that named a subject.

    A bare "who do i ring" is about the last thing the person described, which is not always the
    last line and is almost never the last answer. "she keeps falling" is answered "a second one
    is worth a GP visit", "what can i do" is answered with the grab-rails checklist, and the ask
    arrives after an answer that names nobody: the person the thread named is in the answer to the
    line that named the subject.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return None
    for index in range(len(turns) - 1, -1, -1):
        turn = turns[index]
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("user") or "")
        if not line or _names_no_subject(line):
            continue
        return index, str(turn.get("bot") or ""), line
    return None


def _thread_text(memory, answer=""):
    """What the person said over the last few lines, which is what the thread is about.

    Their own words only. The bot's answers are where the *person* is read from, and they are the
    worst place to read the subject from: advice names things the person never mentioned, as the
    thing to rule out or to check. "my mum keeps falling" / "what can i do" ends "...and get the
    eyes checked", and "who do i ring" was answered "An optician: book an eye test" - the mother
    had fallen, and a passing mention in the advice became the subject of the thread.
    """
    said = [answer]
    # Their own words only, as main reads it: the bot's answers are where the person is read
    # from, not the thread. The walk itself is `earlier.turns`, the one place a turn is read.
    for turn in earlier.turns(memory)[-3:]:
        if not isinstance(turn, dict):
            continue
        said.append(str(turn.get("user") or ""))
    return " ".join(part for part in said if part)


def _sentence_at(text, at):
    """(the sentence of `text` the offset `at` sits in, where that sentence starts)."""
    begin = 0
    for found in re.finditer(r"(?<=[.!?]) ", text):
        if found.start() >= at:
            return text[begin:found.start()], begin
        begin = found.end()
    return text[begin:], begin


def _person_in(said):
    """(person, the sentence that names them, offset of the person in it) from an answer, or None."""
    best = None
    for name, words, _way in EXPERTS:
        found = words.search(said)
        if not found:
            continue
        if best is not None and found.start() >= best[3]:
            continue
        # Where the person sits inside their sentence, which is what says whether the sentence
        # names them early enough to stand on its own.
        sentence, start = _sentence_at(said, found.start())
        best = (name, sentence, max(0, found.start() - start), found.start())
    if best is None:
        return None
    return best[0], best[1], best[2]


def _cut_the_preamble(sentence, at):
    """The referral from the person's own clause in, without the run-up to it.

    "Weeks of it is not a bad day any more, and it is worth saying to a GP rather than waiting it
    out" is a referral from the "and": handed back whole, the person gets the mood sentence again
    before the name they asked for.
    """
    start = 0
    for found in PREAMBLE.finditer(sentence):
        if found.end() > at:
            break
        if at - found.end() <= 80:
            start = found.end()
    return sentence[start:].strip(), start


def _tidy(clause):
    clause = clause.strip().strip('"').strip().rstrip(" ,;:")
    if clause and not clause.endswith((".", "!", "?")):
        clause += "."
    if clause[:1].islower():
        clause = clause[0].upper() + clause[1:]
    return clause


def _lead_of(name):
    return LEAD.get(name, name)


def _the_way_in(name, memory, said, clause=""):
    """The one line of the reply that is not the answer's: how to get to the person.

    A way in the answer already gave ("ring the practice", "ask for the earliest appointment") is
    not said again: the line is there to add the step, not to say it twice.
    """
    ways = ()
    for other, _words, options in EXPERTS:
        if other == name:
            ways = options
    if not ways:
        return ""
    said_flat = _flat(clause)
    fresh = [way for way in ways if not _says_it_again(way, said_flat)]
    return pick(fresh or list(ways), memory, said)


def _says_it_again(way, said):
    """True when the way in repeats a run of three words the clause already used."""
    words = _flat(way).split()
    for at in range(0, max(0, len(words) - 2)):
        if " ".join(words[at:at + 3]) in said:
            return True
    return False


def _person_for_the_topic(memory, said="", subject=""):
    """The person the thread is about, when the answer named nobody.

    `subject` is the last line that named one: its reading beats the carried topic, which can be
    a topic of its own ("my dog keeps scratching" then "my boiler is noisy" left `pets` on the
    reading of a who-ask, and "who do i call" was answered "A vet").
    """
    read = memory.get("understood") if isinstance(memory, dict) else None
    topics = []
    if isinstance(read, dict):
        topics = [str(t).lower() for t in (read.get("topics") or [])]
        one = str(read.get("topic") or "").lower()
        if one:
            topics.append(one)
    if subject:
        theirs = understand(_flat(subject), {})
        if isinstance(theirs, dict) and theirs.get("topics"):
            topics = [str(t).lower() for t in theirs["topics"]]
    care = [topic for topic in topics if topic in CARE_TOPICS]
    if care:
        thread = _thread_text(memory, said)
        for name, words in THREAD:
            if words.search(thread):
                return name
    for topic, name in BY_TOPIC:
        if topic in topics:
            return name
    return ""


def _from_the_answer(name, sentence, at, memory, said, repeat=True):
    """The person the answer named, with the one line on how to get to them.

    `repeat` is False when the sentence comes from an answer the person has already heard: the
    answer above the last one is not said again, so the reply is the person and the way in.
    """
    clause, start = _cut_the_preamble(sentence, at)
    way = _the_way_in(name, memory, said, clause)
    if not way:
        return None
    if repeat and at - start <= EARLY:
        # The sentence says who to see at the front of it ("see a GP if it is no better in a
        # fortnight"): hand it back, condition and all, with the way in after it.
        body = _tidy(clause)
        if way and not _says_it_again(way, _flat(body)):
            body = body + " " + way[0].upper() + way[1:] + "."
        return body
    # The person is named at the end of a condition ("if it is no better in six weeks, ask your
    # GP about physio", "is a same-day job for a doctor"): the condition is what the answer above
    # already said, so the reply is the person and the way in.
    return _lead_of(name) + ": " + way + "."


def reply_for(text, memory):
    """The person to see, or None on every line that is not a bare ask for one."""
    memory = memory if isinstance(memory, dict) else {}
    if not asks_who(text):
        return None
    if _last_module(memory) in QUIET:
        return None
    answer = _last_reply(memory)
    if not answer:
        return None
    # An answer that already named someone is the one to hand back, condition and all.
    found = _person_in(answer)
    if found:
        reply = _from_the_answer(*found, memory=memory, said=text)
        if reply:
            return reply
    # The last answer named nobody: the person the thread already named is the one to hand back.
    subject = _the_subject(memory)
    turns = memory.get("turns") or []
    if subject and subject[1] and subject[0] != len(turns) - 1:
        found = _person_in(subject[1])
        if found:
            reply = _from_the_answer(*found, memory=memory, said=text, repeat=False)
            if reply:
                return reply
    name = _person_for_the_topic(memory, text, subject[2] if subject else "")
    if not name:
        return None
    way = _the_way_in(name, memory, text)
    if not way:
        return None
    return _lead_of(name) + ": " + way + "."


def takes_as_it_comes(text, memory):
    """Only on a line that is nothing but the ask, over a thread that has a person to name."""
    try:
        return reply_for(text, memory) is not None
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


TAKES_AS_IT_COMES = takes_as_it_comes
