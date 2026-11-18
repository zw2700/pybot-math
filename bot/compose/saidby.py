"""A wish inside quotation marks belongs to the person who said it, not to the one who typed it.

People bring other people's words to the bot all the time, and the line looks like a wish of
their own because the words of a wish are in it:

    she texted me "we need to talk" and nothing else
        -> "Talk\" and nothing else — fair enough. What's stopped it happening so far?"
    he texted "i want to see you tonight" and i panicked
        -> "Worth doing. What would you like help with first?"
    my mum keeps saying "i want to see the grandkids more"
        -> "See the grandkids more\" — fair enough. What's stopped it happening so far?"

Each of those is a plan pool reading somebody else's `i want` as the person's own, and the first
and third say a fragment of a quotation back - half a sentence with a stray quote mark in it.
The person is not asking for help doing the thing; they are holding what was said to them.

Two things live here so they cannot drift apart:

* `reads_as_somebody_elses_wish(text)` - the reading. It needs a quotation of at least two words,
  a verb of saying with a person in front of it, and a wish or a hard thing to say inside the
  quotation. Anything else stands down: a word quoted to be picked on ("i want something called
  \"sourdough\"") is not this, and neither is a sign or a note ("the note said \"no parking after
  6\""), because nobody said it to the person.
* `reply_for(text, memory)` - the wording. It asks about the person holding it, never about the
  wish: the thing to help with is what they are left feeling, not the quotation.

The chat module reads both (`bot/modules/chat.py`): the plan reply ("Worth doing") and the thing
reply ("fair enough") both stand down for a line this answers, and a card the knowledge base can
answer keeps its turn, because this is read from inside chat, not in front of it. That last part
was a promise this module did not keep: the reading only asked whether the line was somebody
else's words, never whether something else could answer them, so two lines with a card of their
own were asked what went through the person's head instead:

    my son said "i hate you" and went to his room
        -> "That's a big thing to have said to you."  where the child card says not to argue
    my wife said "i want a divorce" last night
        -> "Hard to be on the end of that one."  where the money card has the first move

`_the_card_keeps_its_turn` asks the module that owns the base, so the rule is the base's answer
and not a list of subjects kept here (cream-flag, #routing 179).
"""
import re

from . import pick

# A quotation, straight or curly. Two words at least: a single quoted word is somebody picking a
# name for a thing, not a sentence anybody said to them.
QUOTED = re.compile(r'"([^"]{3,300})"|\u201c([^\u201d]{3,300})\u201d')
# The verb of saying, and the person in front of it. `told me` is the one that carries its object
# in the verb, so it stands alone.
SAID = re.compile(
    r"\b(?P<who>(?:my|his|her|their|our|the)\s+[a-z][a-z'-]*(?:\s+(?:in[-\s]?laws?|wife|husband))?"
    r"|he|she|they|someone|somebody|everyone|everybody|a\s+friend|a\s+mate)\b"
    r"(?:\s+[a-z']+){0,3}?\s+"
    r"(?:said|says|saying|texted|texts|text|messaged|messages|emailed|emails|wrote|writes|"
    r"goes|went|was\s+like|shouted|shouts|yelled|yells|screamed|screams|whispered|whispers|"
    r"keeps?\s+(?:saying|shouting|telling\s+me)|kept\s+(?:saying|shouting|telling\s+me)|"
    r"has\s+said|had\s+said|told\s+me|tells\s+me)\b", re.I)
# A person talking, where the verb of saying is the line's own subject: "said to me", "texted: ...".
SAID_TO_ME = re.compile(r"\b(?:said|says|texted|texts|messaged|emailed|told\s+me)\s+(?:to\s+)?(?:me)?\b",
                        re.I)
# What the quotation has to hold to be a line worth answering this way: a wish, a plan, or one of
# the hard things people say at a door.
A_WISH = re.compile(
    r"\b(?:i|we)\s+(?:want|wants|wanted|need|needs|needed|would\s+like|d\s+like|dont|don'?t)\b"
    r"|\b(?:i|im|i'm|we|we're|weve|we've)\s+(?:am\s+|are\s+|is\s+)?(?:going\s+to|leaving|done|out)\b"
    r"|\b(?:i|we)\s+miss\b"
    r"|\bi\s+(?:want|need)\s+out\b"
    r"|\bwe\s+need\s+to\s+talk\b"
    r"|\b(?:its|it'?s)\s+over\b", re.I)
# Being told "i love you" or "i hate you" is not the same weight as "we need to talk": it is a
# thing said out loud and left in the room, and "a lot to sit with" over it is heavier than the
# line. These get a lighter reply of their own.
A_DECLARATION = re.compile(r"\b(?:i|we)\s+(?:really\s+|still\s+)?(?:love|hate)\s+(?:you|him|her|them)\b",
                           re.I)
# Nobody said these to the person: a sign, a note, a letter, a ticket, a form, or a thing that
# carries words without being a speaker - a song, a lyric, the radio, an advert.
NOT_SPOKEN_TO_THEM = re.compile(
    r"\b(?:note|notes|sign|signs|label|notice|letter|email\s+says|form|ticket|invoice|bill|"
    r"receipt|menu|website|app|screen|message\s+on|instructions|recipe|book|leaflet|poster|"
    r"song|songs|lyric|lyrics|radio|telly|tv|advert|advertisement|film|movie|poem|poems|"
    r"show|podcast|headline|article|quote)\b",
    re.I)
# The person's own message, quoted back: "so i texted him \"i want to see you\"". The quotation is
# what they sent, not what they were sent, and the plan card for their own message is the right
# answer. The subject of the verb of saying is read from the words in front of the quotation.
OWN_SAYING = re.compile(r"(?:said|say|says|texted|text|texts|messaged|message|emailed|email|wrote|"
                        r"told|replied|answered|sent)", re.I)
OWN_SUBJECT = frozenset("i i'd id we we'd weve i've ive".split())
OWN_FILLER = frozenset("just also only then never always still even actually already finally "
                       "once today yesterday".split())

THEY_SAID = (
    "{Who}'s saying that is a lot to sit with. How are you taking it?",
    "That's a big thing to have said to you. What's going round your head?",
    "Hard to be on the end of that one. Do you want to talk it through?",
)
THEY_SAID_AGAIN = (
    "{Who} keeps coming back to it, and that wears you down more than one saying does. What do "
    "you say back?",
    "Said often enough it stops being about the words. What do you think is behind it?",
)
# A declaration: "he said \"i love you\" and i froze", "my mum said \"i hate you\"". Lighter than
# the pool above, and it does not assume the person is upset about it.
THEY_DECLARED = (
    "That's a big thing to have said to you. What went through your head?",
    "Words like that change the room. How do you feel about it?",
    "Hard to know what to do with being told that. What do you want to say back?",
)
# A line that asks about what was said is an ask, and the knowledge base answers those better
# than a question about the person's own state: "my boss emailed \"i need you to work saturday\"
# - can he do that" has the contract answer, and "what does that mean" is a question to reply to.
ASKING_ABOUT_IT = re.compile(
    r"\?|\b(?:what does that mean|what do i say|what should i say|what do i reply|what should i "
    r"reply|can (?:he|she|they) do that|is that allowed|what do i do|should i)", re.I)
# The person the line is about, said back as the subject of the sentence.
WHO = re.compile(r"\b(my|his|her|their|our|the)\s+([a-z][a-z'-]*)\b", re.I)


def the_quotation(text):
    """The first sentence somebody said, or "" when the line quotes nobody."""
    found = QUOTED.search(str(text or ""))
    if not found:
        return ""
    return " ".join((found.group(1) or found.group(2) or "").split())


def _the_one_who_said_it(text):
    """The words for the person who said it: "my wife", "he", or "" when nobody is named."""
    found = SAID.search(str(text or ""))
    if not found:
        return ""
    who = " ".join(found.group("who").lower().split())
    if who in ("he", "she", "they", "someone", "somebody", "everyone", "everybody"):
        return who
    return who


def _before_the_quotation(text):
    """The words in front of the first quotation: "so i texted him " of "so i texted him \"i want...\""."""
    found = QUOTED.search(text)
    return text[:found.start()] if found else ""


def said_by_the_person(text):
    """True when the quotation is the person's own message: "so i texted him \"i want to see you\"".

    The verb of saying's own subject decides it. `i said`, `i texted him`, `we replied` mean the
    words came from the person typing; `he said`, `my wife texted` mean they came at them. Only
    the words in front of the quotation are read, so a line that reports one and sends one is
    still read by whichever came first.
    """
    words = [word.strip(",.!?;:") for word in _before_the_quotation(text).lower().split()]
    for index in range(len(words) - 1, -1, -1):
        if not OWN_SAYING.fullmatch(words[index]):
            continue
        for word in reversed(words[:index]):
            if word in OWN_FILLER:
                continue
            return word in OWN_SUBJECT
        return False
    return False


def reads_as_somebody_elses_wish(text):
    """True when the line brings somebody else's wish or hard words, quoted, to the bot."""
    said = " ".join(str(text or "").lower().split())
    if not said or '"' not in said and "\u201c" not in said:
        return False
    quoted = the_quotation(said)
    if not quoted or len(quoted.split()) < 2:
        return False
    if not (A_WISH.search(quoted) or A_DECLARATION.search(quoted)):
        return False
    if NOT_SPOKEN_TO_THEM.search(said) or ASKING_ABOUT_IT.search(said):
        return False
    if said_by_the_person(said):
        return False
    return bool(SAID.search(said) or SAID_TO_ME.search(said))


# The heads a possessive frame reads well on: "He's saying that", "She's saying that". "My boss's
# saying that" and "My wife's saying that" do not, so a named person gets the neutral lines.
A_PRONOUN_HEAD = frozenset("he she they someone somebody everyone everybody".split())


def _who_phrase(text):
    """The person as the subject of the reply when the head is a pronoun, else ""."""
    who = _the_one_who_said_it(text)
    if not who or who.split()[0] not in A_PRONOUN_HEAD:
        return ""
    return who[:1].upper() + who[1:]


def _fits_the_head(line, who):
    """Drop the lines that open on a person the line did not name that way."""
    return "{Who}" not in line or bool(who)


def _the_card_keeps_its_turn(text, memory):
    """True when the knowledge base has a card for the line, which then keeps its turn.

    The reply here asks about the person holding the words, which is right when nothing else can
    answer them. When the base does answer them it is the better reply by every rule in STYLE.md -
    it says what to do about the thing, not how the person might be feeling about it - so this
    reading stands down and `bot/modules/answers.py` says its piece. Asked of the module that
    owns the base rather than of a subject list here, so a card added there needs nothing added
    here.
    """
    if not text:
        return False
    try:  # lazy: `answers` reads the composer, so this import belongs inside the call
        from ..modules import answers
    except Exception:  # noqa: BLE001 - a module that will not import answers nothing
        return False
    try:
        return bool(answers.respond(text, {} if memory is None else memory))
    except Exception:  # noqa: BLE001 - a card that raises answers nothing
        return False


def reply_for(text, memory=None):
    """One reply that asks about the person holding somebody else's words, or None."""
    if not reads_as_somebody_elses_wish(text):
        return None
    if _the_card_keeps_its_turn(text, memory):
        return None
    said = " ".join(str(text or "").lower().split())
    who = _who_phrase(said)
    if A_DECLARATION.search(the_quotation(said)) and not A_WISH.search(the_quotation(said)):
        pool = list(THEY_DECLARED)
    else:
        again = bool(re.search(
            r"\b(?:keeps?\s+(?:saying|shouting|on)|kept\s+(?:saying|shouting|on)|always\s+says|"
            r"says\s+it\s+again|over\s+and\s+over)\b", said))
        lines = THEY_SAID_AGAIN if again else THEY_SAID
        pool = [line for line in lines if _fits_the_head(line, who)]
    return pick([line.format(Who=who) for line in pool], memory, said)
