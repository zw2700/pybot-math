"""A return to a subject brings back what was said about it, not a question about where we were.

A person can leave a subject for a turn or two and come back to it by its name alone:

    my boiler is making a noise
    how much is a new one
    i rent so who pays
    back to the noise          -> "OK, back to the noise. Where were we?"

The bot had the subject, what the person said about it and what it had answered, and it handed the
question back. A friend asked to go back to the boiler says what they said about it the first time:
"Back to the noise: banging or rumbling when the heating starts is usually air or a pump set too
fast, so bleed the radiators and check the pressure is 1 to 1.5 bar."

Nothing new is read here. The store's own reading (`bot/memory/topics.py`) has already noted that
this line goes back to an earlier topic (`memory["returned"]`), and it has already moved the answer
that belongs to that topic to the top of the kept answers. This module adds the one thing the
store's pool of return lines does not have - the substance - and passes on every return with an ask
of its own ("back to the laptop, is it worth servicing?"), because the module for the thing named
answers those with the question in front of it.
"""
import re

from ..memory import topics

# Above the store (7000): the store's own answer to a bare return is the pool of "Where were we?"
# lines, and this is the same claim on the same lines with the advice in place of the question.
# Below the safety band, which no return is ever part of.
PRIORITY = 7050

# Said with the thing in front, so the person knows the bot went back with them. The advice is the
# answer the chat already gave for that subject, cut to its first sentence.
LEADS = (
    "Back to {thing}: {advice}",
    "Back on {thing}: {advice}",
    "On {thing}, then: {advice}",
)

# An answer that only says something back ("Got it - it's 12 square metres", "You said you have a
# washer") has nothing to bring back, and a return that quotes one is worse than the store's own
# question: the person is asking what we said about the subject, not what they said. The same goes
# for a hedge ("I'm not sure about that one", "that's beyond what I know well") and a punt at a
# search: bringing one of those back says the chat has nothing on the subject, which the store's
# own question says more honestly.
A_RECEIPT = re.compile(
    r"^(?:got it|noted|ok|okay|sure|right|you said|you've told me|you told me|that's right|"
    r"that is right|makes sense|fair enough|understood|"
    r"i'm not sure|i am not sure|that's beyond|that is beyond|no number for that|"
    r"i can't|i cannot|i'd rather not|i would rather not|searching for it|a quick search)\b", re.I)

# An answer shorter than this carries no advice to bring back.
SUBSTANCE = 6

SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _the_advice(answer):
    """The sentence of the earlier answer that carries the advice, or "" when it has none."""
    text = " ".join(str(answer or "").split())
    if not text:
        return ""
    parts = [part.strip() for part in SENTENCE.split(text) if part.strip()]
    if not parts:
        return ""
    kept = parts[:1]
    if len(parts[0].split()) < 5 and len(parts) > 1:
        kept = parts[:2]
    return " ".join(kept)


def _the_answers_for(memory, topic_text):
    """The answers this chat gave for that subject, each one really said, oldest first.

    A return goes back to the subject as it was first raised, and the answers that came after it
    were about the questions that followed ("what should i say", "how much is a new one"). The
    first answer for the subject is the one that says what the chat knows about it, and it is the
    one a person who says "back to the noise" wants again. Only the answers that fit the subject
    best are kept, and where two fit as well as each other the older one wins: a later answer is
    about the question that followed ("what about a turkey") and it shares the word "roast".

    Every record is checked against the turns, because the arbiter may have chosen another
    module's reply and quoting an answer the person never saw would be inventing one.
    """
    kept = memory.get("entry_answers")
    if not isinstance(kept, list) or not kept:
        kept = [memory.get("entry_answer")]
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return []
    wanted = {form for word in topics.keywords(topic_text)
              for form in (word, topics.stem(word))}
    wanted -= topics.STOPWORDS
    if not wanted:
        return []
    best_score = 0
    found = []
    for record in kept:
        if not isinstance(record, dict):
            continue
        text = str(record.get("text") or "").strip()
        if not text:
            continue
        opening = " ".join(text.lower().split()[:8])
        if not any(isinstance(turn, dict)
                   and " ".join(str(turn.get("bot") or "").lower().split()).startswith(opening)
                   for turn in turns[-topics.ANSWER_KEPT:]):
            continue  # never really said, so it is not ours to quote
        forms = {form for key in set(record.get("keys") or ())
                 for form in (key, topics.stem(key))}
        score = len(wanted & (forms - topics.STOPWORDS))
        if score > best_score:
            best_score, found = score, [text]
        elif score and score == best_score:
            found.append(text)
    return found


def _the_turn_answers_for(memory, topic_text):
    """The answers the chat gave on the turns about that subject, oldest first.

    The kept answers are the entries' own replies and only the last few are held, so the answer to
    the first turn about a subject can be gone by the time the person comes back to it: "my boss
    wants a meeting" is followed by "i hate meetings" (small talk, not an entry) and "what should i
    say", and the kept list holds only the last of the three. The transcript still has the turn the
    subject was raised on, and its answer is what the chat said about it.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return []
    wanted = {form for word in topics.keywords(topic_text)
              for form in (word, topics.stem(word))}
    wanted -= topics.STOPWORDS
    if not wanted:
        return []
    best_score = 0
    found = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        reply = str(turn.get("bot") or "").strip()
        if not said or not reply:
            continue
        score = len(wanted & {form for word in topics.keywords(said)
                              for form in (word, topics.stem(word))})
        if score > best_score:
            best_score, found = score, [reply]
        elif score and score == best_score:
            found.append(reply)
    return found


def _said_recently(advice, memory):
    """True when the chat has just said this, so bringing it back would be the same answer twice.

    A return to a subject whose advice was the last thing said ("my boss wants a meeting" ... "what
    should i say") has nothing new in it, and the arbiter passes over a reply that only says the
    last turn again. Two turns back is enough: the answer to the turn the subject was raised on is
    the source of the advice itself, and it is not a repeat to say it again later.
    """
    opening = " ".join(advice.lower().split()[:6])
    if not opening:
        return False
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return False
    return any(isinstance(turn, dict)
               and " ".join(str(turn.get("bot") or "").lower().split()).startswith(opening)
               for turn in turns[-2:])


def _has_substance(advice):
    """True when this is advice and not a receipt, a question or a shrug."""
    if len(advice.split()) < SUBSTANCE:
        return False
    if A_RECEIPT.match(advice):
        return False
    if advice.rstrip().endswith("?"):
        return False  # a question asked back is not an answer to bring back
    return True


def _the_return_advice(memory):
    """The thing the person went back to and the advice we gave about it, or ("", "")."""
    try:
        record = topics.resumed(memory)
        if not isinstance(record, dict) or record.get("asks"):
            return "", ""
        thing = " ".join(str(record.get("asked") or "").split())
        if not thing:
            return "", ""
        topic_text = str(record.get("text") or "")
        advice = ""
        answers = (_the_answers_for(memory, topic_text)
                   + _the_turn_answers_for(memory, topic_text)
                   + [_the_advice(topics.entry_answer(memory, topic_text))])
        for answer in answers:
            short = _the_advice(answer)
            if _has_substance(short) and not _said_recently(short, memory):
                advice = short
                break
    except Exception:  # noqa: BLE001 - a reader that cannot answer leaves the turn as it was
        return "", ""
    if not _has_substance(advice):
        return "", ""
    return thing, advice


def respond(text, memory):
    """The advice this chat gave about the subject the person went back to."""
    thing, advice = _the_return_advice(memory)
    if not thing:
        return None
    lead = LEADS[len(memory.get("turns") or []) % len(LEADS)]
    return lead.format(thing=thing, advice=advice)


def CLAIMS_INSTEAD(text, memory):
    """This line is a bare return to a subject, and the advice is the answer to it.

    The store answers the same lines from its pool of "Where were we?" lines as a claim - it read
    the line as a return, which is right. The substance is the one thing its pool cannot have, so
    the turn is asked for on the lines where the advice is in hand and nowhere else: a return that
    carries an ask of its own is left to the module for the thing named, and a return to a subject
    with no advice behind it keeps the store's question, which is the right reply there.
    """
    thing, advice = _the_return_advice(memory)
    return bool(thing and advice)
