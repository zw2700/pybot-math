"""They asked the bot to go on, and got told to run a search.

"tell me more", "go on", "and?", "the rest of it" is the ordinary way to keep a friend talking
about the thing they are already on. The line names nothing of its own, so no entry can answer
it, and the bot fell through to the plain hedge ("A search should sort you out quickly") - a turn
after it had answered the subject in full. That reads as if the answer had never been given: the
person is asking about the answer, and a search engine cannot see it.

So the answer behind the ask is handed back to, in the shape a friend uses when they have said
all they know: name the subject, say it is the whole of it, and ask which part to take further.
Nothing is invented, because there is nothing more in the base to give - an answer the bot cannot
back is worse than saying plainly that it has finished.

The rule is narrow on purpose:
* the whole line has to be the continuation and nothing else ("tell me more about the boiler"
  names a subject and is answered from its own words);
* "what else" and "anything else" are not here: they ask for another option, which
  bot/compose/other.py answers from the answer already given;
* only the turn just before counts, and only an answer: "tell me more" after a stock line or a
  refusal has nothing behind it to go on with;
* the bot's own hedges are never continued from.

The one thing that is handed over before saying there is nothing left: an answer that came back a
second time in its short form was still the whole answer, and the part the short form left out has
not been said again, so the person asking about it gets that part (`_the_rest`).
"""
import re

from ..compose import pick
from . import repeat

# Throat-clearing in front of the ask, and the words people put after it. Both carry nothing.
_FRONT = (r"(?:(?:and|so|ok|okay|right|well|alright|yes|yeah|hmm|ta|please|then|but)\b[\s,]+)*")
_BACK = (r"(?:[\s,]+(?:then|please|now|tho|though|thanks|ta|about (?:it|that|this)|"
         r"on (?:it|that|this)|of (?:it|that)|for (?:it|that)))*")

# The whole line, a continuation ask and nothing else. Anchored at both ends: "more protein at
# breakfast" and "go on holiday in june" name a subject and keep whatever answers them.
CONTINUE = re.compile(
    "^" + _FRONT + "(?:"
    r"tell me (?:a bit |a little |a lot )?more"
    r"|more|more please|more detail|more details|in more detail|a bit more|a little more"
    r"|go on|go on then|go ahead|carry on|keep going|keep talking|on you go|continue"
    r"|say more|say a bit more|keep it coming"
    r"|(?:tell me )?the rest(?: of (?:it|that|this))?"
    r"|elaborate|expand|go deeper|dig deeper"
    r"|and\?|and then\?"
    ")" + _BACK + r"[\s.?!,]*$",
    re.IGNORECASE)

# An answer often ends by asking for the one thing it needs: "Tell me what is in the fridge and
# I will pick properly." That ask is the next turn of the same conversation, and it is the only
# part of the answer the person has not already had, so "go on" gets it back with a lead.
AN_ASK = re.compile(
    r"^(?:tell me|let me know|say (?:which|what|how)|which|what|have you|do you|are you|is there|"
    r"how (?:long|much|many|often))\b", re.IGNORECASE)

GO_ON_WITH = (
    "Gladly. {ask}",
    "Happy to. {ask}",
    "Yes - and the next step is yours: {ask}",
    "That is the bit that decides it: {ask}",
)

# What a friend says when the answer was the whole of it: that there is nothing more, plainly,
# and the turn handed back on the part that can still be answered. Inventing detail the base does
# not have is worse than saying this.
NO_MORE = (
    "That's the whole of what I know on it - tell me which bit to take further and I'll come at "
    "it from another side.",
    "That's about the lot I have on that. Which part do you want me to go into?",
    "I have given you all of it. If you say what is still not working I'll take it from there.",
    "That answer is everything I have on it. Point me at the part that is not clear and I'll put "
    "it another way.",
)


def _its_ask(said):
    """The thing the answer asked for at its end, or "" when it asked for nothing."""
    parts = [part.strip() for part in repeat.SENTENCE.split(said.strip()) if part.strip()]
    if not parts:
        return ""
    last = parts[-1]
    if not (last.endswith("?") or AN_ASK.match(last)):
        return ""
    # It has to read as an ask rather than a paragraph that happens to end in a question.
    if len(last.split()) > 22:
        return ""
    return last


def _as_a_line(ask):
    """The answer's ask as a sentence of its own: a capital only where one belongs."""
    said = ask.strip()
    if said[:1].isupper() and not said[:2].isupper():
        said = said[:1].lower() + said[1:]
    return said if said.endswith((".", "?", "!")) else said + "."


# "tell me more about the washing machine" says the subject again rather than "that". It is the
# same ask only when the thing it names is the thing the answer was about: "tell me more about
# mortgages" after a kettle is a new subject, and the entry for it answers from its own words.
MORE_ABOUT = re.compile(
    "^" + _FRONT + r"(?:tell me (?:a bit |a little )?(?:more|about)|"
    r"more|go on|carry on|keep going|say more|the rest(?: of it)?) (?:about|on) "
    r"(?P<what>[a-z0-9' ]{2,40})" + _BACK + r"[\s.?!,]*$",
    re.IGNORECASE)


def _saying_something(text):
    """The line as tidied words, or "" when it names a subject this reader cannot check."""
    return " ".join(str(text or "").split())


def _about_what(text):
    """"tell me more about X": X, when the line is that ask and X is not "it" or "that"."""
    match = MORE_ABOUT.match(_saying_something(text))
    if not match:
        return ""
    what = " ".join(match.group("what").split())
    if what.lower() in ("it", "that", "this", "them", "those"):
        return ""
    return what


def _is_what_was_asked(what, asked):
    """True when every word of the thing named is a word of the line the answer was given to."""
    known = set(str(asked or "").lower().split())
    known |= {word.rstrip("s") for word in known}
    for word in what.lower().split():
        if word in ("the", "a", "an", "my", "your", "our", "this", "that", "it"):
            continue
        if word not in known and word.rstrip("s") not in known:
            return False
    return True


# A few words, flattened to what they say: the same words come back with different punctuation
# and a different case, and a short answer is the same answer word for word inside a longer one.
_WORD = re.compile(r"[a-z0-9']+")


def _flat(text):
    return " ".join(_WORD.findall(str(text or "").lower()))


# An answer given again in a shorter form is the opening of the fuller one, and the part left out
# is still unsaid. "my kitchen is tiny" gets the whole storage answer; the reworded re-ask that
# follows ("how do i make it work") gets its first sentence back, which is not a repeat because
# the words differ - and then "tell me more" was answered "I have given you all of it", though
# the second half of that answer had never been said a second time and the person was asking
# about it. A friend given the same thing twice says what is left, not that there is nothing.
MORE_OF_IT = (
    "There was more to that answer: {rest}",
    "That answer had more in it: {rest}",
    "And the rest of what I said: {rest}",
)


def _the_rest(said, answers):
    """The part of a fuller answer from a turn or two back that the short one left out, or "".

    The fuller answer has to open with the sentence just given, so it is the same answer and not
    another one on the same subject, and every sentence before the first leftover one has to be in
    the short answer already, so what is handed over is the part that has not been said.
    """
    given = _flat(said)
    if len(given.split()) < 6 or not answers:
        return ""
    for _back, _asked, fuller in answers[1:]:
        parts = [part.strip() for part in repeat.SENTENCE.split(str(fuller or "").strip())
                 if part.strip()]
        if len(parts) < 2 or _flat(parts[0]) not in given:
            continue
        left = [index for index, part in enumerate(parts) if _flat(part) not in given]
        if not left or left[0] == 0:
            continue
        return " ".join(parts[left[0]:])
    return ""


def asks_for_more(text):
    """True when the whole line is "carry on" and nothing else."""
    said = _saying_something(text)
    if not said or len(said.split()) > 8:
        return False
    return bool(CONTINUE.match(said) or MORE_ABOUT.match(said))


def reply_for(text, memory):
    """Keep going on the answer just given, or None when this is not that turn."""
    if not isinstance(memory, dict) or not asks_for_more(text):
        return None
    named = _about_what(text)
    answers = repeat.recent_answers(memory)
    if not answers:
        return None
    back, asked, said = answers[0]
    # The turn just before this one is the answer being asked about; anything older is only that
    # answer if the chat has not moved on since.
    if back > 1 and not repeat.same_subject(asked, said, memory):
        return None
    if named and not _is_what_was_asked(named, asked):
        # A different subject, so this is a new question and the entry for it answers, if there
        # is one. Only the subject it repeats brings it back here.
        return None
    rest = _the_rest(said, answers)
    if rest and not repeat.said_recently(rest, memory):
        return repeat.handed_back(memory, pick(MORE_OF_IT, memory, text).format(rest=rest))
    ask = _its_ask(said)
    if ask:
        return repeat.handed_back(memory, pick(GO_ON_WITH, memory, text).format(ask=_as_a_line(ask)))
    reply = pick(NO_MORE, memory, text)
    if repeat.said_recently(reply, memory):
        # The person asked twice and got this already: saying it again in the same words is the
        # one thing worse than a hedge, so a second ask gets the plainest version there is.
        reply = "That is all of it. Tell me what you have tried and I will work from that."
        if repeat.said_recently(reply, memory):
            return None
    return repeat.handed_back(memory, reply)
