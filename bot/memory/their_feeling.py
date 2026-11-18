"""Somebody the chat has named, and how they are finding a thing the chat has named.

    my son is 7 / hes just started school / he hates it
      was: I'm listening - say more if it helps.
      now: Starting school is hard going for your son, then. What's the worst part?

    my daughter started a new job / she hates it
      was: Got it. Is there anything you'd like a hand with?
      now: ...

    my mum is in hospital / she hates the food
      was: Go on. I'm here.
      now: ...

The composer's note that fits any message ("I'm listening - say more if it helps") is what a
feeling report from somebody else got, because every reader of feelings in the bot is about the
person typing: `obstacle.the_thing` reads "i hate it" and refuses the pronoun on purpose, and the
acknowledgements read a day going badly for them. A line about a third person ("he hates it",
"she cant stand the food", "my partner hates his job") names no trouble of their own, so it fell
through to the note.

What the line carries is a person and a feeling; what the chat carries is what the feeling is
about, which the question the bot asked last turn ("How's it going so far?", "How were the first
days?") is the one thing still owed. So the reply names the person and asks for the part of it
that is worst - a friend's question, not a line that would fit any message.

The reader refuses more than it takes:

* a question ("do you think he hates it?") is for the answer modules;
* the first person ("i hate it") is `obstacle`'s and the composer's, and the frame does not fit;
* an opening line naming a fresh subject in a plain word ("my son hates school") is a subject of
  its own and the knowledge base answers it with the school answer - reading it here would put a
  question in place of an answer. A first line is read only when the thing is a possessive or a
  definite one ("my partner hates his job", "she hates the food"), which is a continuation of
  something the person has in mind rather than a request about a subject;
* a pronoun with nobody in the chat for it to point at names nobody, and "he hates it" three
  lines after the last person is a guess.

The feeling is read in both directions: a thing somebody hates, and a thing somebody loves, since
"That's a good sign - what does he like best about his teacher?" is the reply to the second and
the school-letters answer the bot gave was about a different question.
"""
import re

from ..compose.remark import person_pronouns
from . import relations

# The lines that open a report before the person: "and he hates it", "well, she cant stand it".
LEAD = r"^\W*(?:(?:and|but|so|oh|also|well|yeah|yep|ok|okay|right|alright|honestly|god)\W+)*"
# The person: a pronoun the chat can point at, or the relation word they are held under.
PERSON = (r"(?P<who>he|she|they|him|her|them|"
          r"(?:my|our|his|her|their)\s+[a-z][a-z'-]*)")
# How the feeling is said. The left column is a thing somebody does not like, the right one a
# thing they do; the two are kept apart because the reply is different in kind - one asks what is
# worst, the other what is best.
DISLIKE = (r"(?:hates?|hated|dislikes?|disliked|cant\s+stand|cant\s+face|can\s*not\s+stand|"
           r"couldnt\s+stand|doesnt\s+like|does\s*not\s+like|didnt\s+like|isnt\s+keen\s+on|"
           r"not\s+keen\s+on|is\s+struggling\s+with|struggles\s+with|is\s+fed\s+up\s+with)")
LIKES = (r"(?:loves?|loved|adores?|adored|likes?|liked|enjoys?|enjoyed|is\s+loving|"
         r"is\s+enjoying|gets?\s+on\s+well\s+with|has\s+taken\s+to)")
FEELING = re.compile(LEAD + PERSON + r"\s+(?:(?:really|just|now|still|actually|absolutely|"
                     r"completely|totally|properly)\s+)*(?P<how>" + DISLIKE + r"|" + LIKES + r")"
                     r"\s+(?P<thing>.+?)\s*[.!]*$", re.I)
# A thing, as against a pronoun: "he hates it" points back at the thing the chat is on.
A_THING = re.compile(r"^(?:(?:the|his|her|their|its|my|our|a|an)\s+)?[a-z][a-z'-]*"
                     r"(?:\s+[a-z][a-z'-]*){0,3}$", re.I)
POINTS_BACK = re.compile(r"^(?:it|that|this|these|those|them|him|her|everything|all\s+of\s+it|"
                         r"the\s+whole\s+thing)$", re.I)
# An ask, not a report: the answer modules may answer it and a question of ours would bury it.
ASKING = re.compile(r"\?|\b(?:what|why|how|should|shall|can|could|would|any\s+idea|advice|help|"
                    r"do\s+you\s+think|is\s+it|does\s+it)\b", re.I)
# A determiner in front of the thing makes it the one the chat is on rather than a subject of its
# own: "the food", "his job", "her teacher".
DEFINITE = re.compile(r"^(?:the|his|her|their|its|my|our|this|that|these|those)\s+", re.I)
WORDS = frozenset("""it that this these those them him her everything all
    the a an and but so oh also well yeah yep ok okay right alright
    really just now still actually absolutely completely totally properly
    very quite bit lot little much more less""".split())

# The reply ends on the part of it that is worst, or best, which is the one question a friend asks
# and the one the bot's own question last turn is still owed. Two shapes with the thing named, and
# two for a pronoun that points at it, so the same line twice does not get the same sentence twice.
WITH_THING = {
    "no": (
        "{thingcap} is hard going for {person}, then. What's the worst part?",
        "That's a shame about {thing}. What's {person} finding hardest?",
        "{thingcap} isn't working for {person}, then. What would make the most difference?",
    ),
    "yes": (
        "That's good - {thingcap} is working for {person}, then. What does {they} like best?",
        "Good news. What is it about {thing} that {person} has taken to?",
        "That's the best news of the day, that one. What's {person} enjoying most about {thing}?",
    ),
}
WITHOUT_THING = {
    "no": (
        "That's hard going for {person}, then. What's the worst part?",
        "Not what you hoped for {person}. Which bit is worst?",
        "That's a shame. What's {person} finding hardest?",
    ),
    "yes": (
        "That's good news. What does {person} like best about it?",
        "Good to hear - what's {person} enjoying most?",
        "That's a good sign. What made the difference for {person}?",
    ),
}


def _the_last_person(text, memory):
    """The person the line is about, as the store words them: "son", "partner", "mum"."""
    low = str(text or "").lower()
    match = FEELING.match(low)
    if not match:
        return "", ""
    who = match.group("who")
    if who.startswith(("my ", "our ")):
        # The store words a person by the relation alone ("son", "mum"), and a reply says "your
        # son": the word on its own reads as somebody else's child.
        return "your " + who.split()[-1], who.split()[-1]
    if who.startswith(("his ", "her ", "their ")):
        # "his teacher" as the person is somebody else's; the person is the relation the chat
        # holds, which is what the pronoun would point at anyway.
        return "", who
    person = ""
    try:
        person = relations._person_from_pronoun(low, memory) or ""
    except Exception:
        person = ""
    # A relation the chat holds is said back with the possessive it was given in ("your son"), and
    # a name it was given ("Ada") is said as the name.
    if person and not re.match(r"^(?:my|our|your|his|her|their)\b", person):
        person = "your " + person
    return person, who


def reply_for(text, memory):
    """The reply to a line about how somebody else is finding a thing, or None."""
    low = " ".join(str(text or "").lower().split())
    if not low or ASKING.search(low):
        return None
    match = FEELING.match(low)
    if not match:
        return None
    person, _ = _the_last_person(low, memory)
    if not person:
        return None
    thing = match.group("thing").strip(" .,!;:")
    if not thing:
        return None
    back = bool(POINTS_BACK.match(thing))
    if not back:
        if not A_THING.match(thing):
            return None
        if not DEFINITE.match(thing) and not _an_earlier_turn(memory, low):
            # "my son hates school" on the first line is a subject, and the knowledge base has the
            # answer for it. Read here it would get a question instead.
            return None
        if not DEFINITE.match(thing) and not _says_something(thing):
            return None
    if not _an_earlier_turn(memory, low) and not DEFINITE.match(thing):
        # The opening line of a chat naming a possessive thing ("my partner hates his job") is a
        # complaint about a thing they have, and the question is better than the note every
        # message gets. A bare subject ("my son hates school") is left to the knowledge base.
        return None
    how = "no" if re.search(r"(?:^|\s)(?:" + DISLIKE + r")(?:\s|$)", match.group("how")) else "yes"
    pool = WITHOUT_THING[how] if back else WITH_THING[how]
    filled = [_fill(frame, person, thing if not back else "") for frame in pool]
    return _vary(filled, memory, low)


def _says_something(thing):
    """Whether the thing named is more than the words that say nothing on their own."""
    words = [word for word in re.split(r"[^a-z']+", thing.lower()) if word]
    return bool(words) and any(word not in WORDS for word in words)


def _an_earlier_turn(memory, low):
    from .history import an_earlier_turn
    try:
        return an_earlier_turn(memory, low)
    except Exception:
        return False


def _fill(frame, person, thing):
    """One frame with the person and the thing in it, and the words around them agreeing."""
    they = person_pronouns(person)[0]
    said = frame.replace("{person}", person).replace("{they}", they)
    if "{thing" in frame or "{Thing}" in frame:
        said = (said.replace("{thingcap}", thing[:1].upper() + thing[1:])
                    .replace("{Thing}", thing[:1].upper() + thing[1:])
                    .replace("{thing}", thing))
    # The frame may open on the thing, and a sentence opens on a capital.
    return said[:1].upper() + said[1:]


def _vary(options, memory, line=""):
    """One of the ways to say it, not the same one twice while the others are unused."""
    from ..compose import pick
    return pick(options, memory, line)
