"""A question about somebody the chat has never named asks who they mean.

The first line of a chat has nobody in it. Every way of asking a fact about a person was answered
as if the chat held one, and each in its own wrong way:

    how old are they       -> You haven't told me how old they are.
    how old is he          -> I'm not sure about that one, sorry - I'd rather not guess. ...
    what do they do        -> I don't know enough to answer that honestly. ...
    where does she work    -> You would have to ask her - that is not a thing I can look up.
    whats their name       -> I don't know it yet.

None of those is an answer to the line. A denial about something the person "hasn't told" us is a
claim about a conversation that has not happened; the hedge is the bot shrugging at a question it
understood perfectly; "you would have to ask her" hands the answer to a her the chat has never been
told about. What is missing is the person, so the reply asks for them, in the words the receipt
reader already uses when a figure arrives with nobody attached ("hes 9" -> "Who's 9?").

The rule is one question, asked once: is there a chat behind this line? `bot/memory.there_is_a_chat`
is the chat's own answer to that, the same one every reader that leans on the past asks. With a
chat behind it the pronoun points at somebody real and this module says nothing - "my son is 14"
then "how old is he" is still answered "Your son is 14." by the store.

With nobody behind it, the line still has to be asking about a person: a third party named only by
a pronoun, in a line that asks something, with nobody in the line to be about. "how do you know if
they like you" is about the pair of them and the person asking, "what should i do if they dont text
back" is about people in general, and "how old is the dog" names the dog - all three keep whatever
the bot would have said, because asking "who do you mean?" there is asking the person to repeat
themselves.
"""
import re

try:  # the chat's own picker, which keeps the wording from repeating inside one conversation
    from ..compose import pick
except Exception:  # noqa: BLE001 - a bot without its picker still has the wording
    pick = None

WHO_IS_IT = (
    "Who do you mean?",
    "Who's that, then?",
    "Who are we talking about?",
)

# Above the memory store (7000), whose reply to these lines is the denial this module replaces.
# Below keeping and since_it_began (7400, 7500), which read a plan or a date out of the line, and
# far below the safety band (9000).
PRIORITY = 7300

# A third party named only by a pronoun: "how old is he", "what do they do", "whats their name".
A_THIRD_PARTY = re.compile(
    r"\b(?:he|she|him|her|his|hers|they|them|their|theirs)\b", re.I)

# Somebody already in the line to be about: the person asking ("what should i do if they dont text
# back"), the bot they are asking ("how do you know if they like you"), or people in general
# ("everyone", "people"). Then the pronoun needs no name and asking who they mean is wrong.
SOMEBODY_IN_THE_LINE = re.compile(
    r"\b(?:i|i'm|im|me|my|mine|myself|we|us|our|ours|you|your|yours|yourself|yourselves|"
    r"someone|somebody|anyone|anybody|everyone|everybody|people|nobody|no one)\b", re.I)

# The line names the person it asks about ("the dog", "my son", "that woman"): the pronoun is
# shorthand for something already said, so the question is answered, not handed back.
NAMES_THEM = re.compile(r"\b(?:my|our|the|this|that|these|those)\s+[a-z][a-z'-]{1,}", re.I)

# A fact asked about a person, in the shapes people use: an age, a height, a name, where they live
# or work, whether they are all right. The list is facts, not pronouns, because a pronoun alone is
# not a person: "what time do they close" and "how do they know if they like them" are about a
# shop and about people in general, and both are left to the modules that answer them.
A_FACT_ABOUT_THEM = re.compile(
    r"\bhow (?:old|tall|big|heavy|far|long)\b"
    r"|\b(?:what|whats|what's)\b[^?]*\b(?:name|age|job|birthday|number|address)\b"
    r"|\bwhere (?:does|do|did|is|was)\b[^?]*\b(?:live|work|come from|from|stay|based)\b"
    r"|\b(?:is|are|was|were)\s+(?:he|she|they)\b"
    r"|\bhow (?:is|are|was|were)\s+(?:he|she|they)\b",
    re.I)

# The line is asking something: it opens with a question word or an auxiliary, or it ends in a
# question mark.
AN_ASK = re.compile(
    r"^\s*(?:how|what|whats|what's|where|when|which|why|is|are|was|were|does|do|did|has|have|"
    r"can|could|would|will)\b", re.I)


def _there_is_a_chat(memory):
    """Whether the person said anything before this line.

    The rule the reply leans on is the chat's: a reply about a past line needs a past line, and on
    a first message there is none. Every reader that leans on the chat asks this one question, so
    it is asked once, here, off the key the runtime writes.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in turns or ():
        if isinstance(turn, dict) and str(turn.get("user") or "").strip():
            return True
    return False


def _flat(text):
    """The line with its case, spacing and end punctuation taken off."""
    return " ".join(str(text or "").lower().replace("\u2019", "'").split())


def about_somebody_unnamed(text, memory):
    """Is this an ask about a third party the chat has never been told about?"""
    if _there_is_a_chat(memory):
        return False
    said = _flat(text)
    if not said:
        return False
    if not AN_ASK.search(said) and "?" not in said:
        return False
    if not A_THIRD_PARTY.search(said) or not A_FACT_ABOUT_THEM.search(said):
        return False
    return not SOMEBODY_IN_THE_LINE.search(said) and not NAMES_THEM.search(said)


def respond(text, memory):
    """Asking who they mean, or None for every other line."""
    if not isinstance(memory, dict):
        return None
    if not about_somebody_unnamed(text, memory):
        return None
    if pick is not None:
        try:
            return pick(WHO_IS_IT, memory, _flat(text))
        except Exception:  # noqa: BLE001 - a pick that fails still has a wording
            pass
    return WHO_IS_IT[0]
