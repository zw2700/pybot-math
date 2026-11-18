"""A line that says they want to hurt somebody, and the reply it deserves.

People say this all day and they almost never mean it as a plan: "i want to kill my boss", "i
could strangle him", "punch your brother". It is anger with a person in it. The plan pool read
it as a project and handed it back as approval -

    i want to kill my boss       -> "Worth doing. What would you like help with first?"
    i want to punch my brother   -> "Punch your brother - fair enough. What's stopped it happening so far?"
    i want to hit my wife        -> "Hit your wife - fair enough. What's stopped it happening so far?"

- which is the bot agreeing to a killing, in its own voice. Nothing in the line asked for help
with it; what it wants is to be heard, and the anger behind it is what the bot can answer.

Two things live here, so they cannot drift apart:

* `reads_as_hurting_someone(clean)` - the reading. Two parts are needed and both have to be
  there: a verb of hurting, and a person after it. `kill time`, `could murder a curry`, `hit the
  sack`, `beat the traffic` and `kill two birds` have the verb and no person, so they keep their
  own answers. A dog or a cat is somebody's too, so a pet counts as a person here. The line is
  the speaker's own wish (`i want`, `i could`, `im going to`) or a bare instruction to them
  ("punch your brother"); a question ("should i hit him?") is a question and is left alone.
* `reply_for(clean, memory)` - the wording. It says no to the doing in the plainest way without
  a lecture, then asks about the anger, which is the thing the person can actually talk about.
  One of the four names the person they are angry with, so two turns in a row are not the same
  sentence.

The chat module reads both (`bot/modules/chat.py`, `_their_thing` and `_intent`): a line this
answers is not a plan to get on with, and it is not a thing to ask "which kind?" about.
"""
import re

from . import pick

# The composer's name for this kind of line.
HURTING = "hurting_someone"

# What people say they will do to the person they are angry with. "beat" is only here with "up":
# "beat my brother at chess" and "beat the traffic" are not this, and "burn" is only "burn down"
# and "set fire to", so "burn the toast" stays a kitchen line.
_HURT = re.compile(
    r"\b(?:kill|killing|murder|murdering|strangle|strangling|throttle|throttling|choke|choking|"
    r"stab|stabbing|shoot|shooting|poison|poisoning|punch|punching|hit|hitting|smack|smacking|"
    r"thump|thumping|whack|whacking|slap|slapping|kick|kicking|drown|drowning|deck|decking|"
    r"bash|bashing|batter|battering|gouge|gouging|clobber|clobbering|pummel|pummelling|"
    r"headbutt|headbutting|garrotte|garrote|hurt|hurting|smash|smashing|"
    # "i want to shake my baby" was answered "Shake your baby - fair enough." and "i feel like
    # shaking the baby" with "Got it.": the verb a parent at the end of their rope reaches for
    # was not one of these, so the card written for exactly that never came up.
    r"shake|shaking|shook|shaken|"
    r"beat\s+up|beat\s+(?:the\s+)?(?:living\s+)?daylights\s+out\s+of|"
    r"do\s+(?:him|her|them)\s+in|knock\s+(?:him|her|them)\s+out|run\s+(?:him|her|them)\s+over|"
    r"set\s+fire\s+to|burn\s+down|get\s+(?:him|her|them)\s+back|get\s+my\s+own\s+back\s+on)\b")
# Who they are angry with. A pronoun, or a person somebody is to them ("my boss", "your
# brother", "the neighbour"). The list is of people, not of everything alive: a wasp and a
# spider are not here, and a pet is only here by name ("the dog") because a person who says they
# want to kill the dog is in trouble and needs a different answer, not this one.
_PERSON = re.compile(
    r"\b(?:him|her|them|"
    r"(?:his|her|their|your|my|our)\s+(?:face|head|teeth|nose|jaw)|"
    r"(?:(?:my|your|his|her|their|our|the)\s+)?"
    r"(?:boss|manager|husband|wife|partner|boyfriend|girlfriend|ex|fiance|fiancee|"
    r"mum|mom|dad|mother|father|brother|sister|sons?|daughters?|child(?:ren)?|kids?|"
    r"bab(?:y|ies)|toddlers?|infants?|newborns?|gran|nan|"
    r"grandma|grandad|grandmother|grandfather|aunt|uncle|cousin|in-laws?|"
    r"neighbour|neighbor|landlord|landlady|tenant|flatmate|housemate|roommate|"
    r"mate|friend|colleague|coworker|co-worker|teacher|headteacher|classmate|"
    r"stepmum|stepdad|stepson|stepdaughter|mother-in-law|father-in-law|"
    r"careworker|carer|nurse|doctor|dr|gp|dentist|social\s+worker|"
    r"referee|coach|vicar|priest|imam|rabbi|officer|policeman|policewoman|cop|"
    r"driver|cyclist|bus\s+driver|security\s+guard|bouncer|celebrity|politician|"
    r"(?:that|the)\s+(?:man|woman|bloke|guy|girl|lady|person|kid)|"
    r"those\s+(?:people|kids|children|men|women)|everyone|everybody))\b")
# The person named, for the reply that says it back: "what has your boss done?"
# The relation keeps its "in law": the bare noun phrase stopped at "brother" and "i want to kill
# my brother in law" came back as "Sounds like your brother has worn you down", which is a
# different person from the one they named.
_THE_PERSON = re.compile(
    r"\b((?:my|your|his|her|their|our)\s+[a-z][a-z'-]*(?:\s+in[-\s]?laws?)?"
    r"|(?:that|the)\s+(?:man|woman|bloke|guy|lady|person|kid)|him|her|them)\b")
# A steadier idiom of the same verb: none of these is about a person, but each is worth keeping
# out by name because the verb is one of ours.
_IDIOM = re.compile(
    r"\b(?:kill\s+(?:time|the\s+(?:lights?|mood|music|engine|conversation))"
    r"|kill\s+two\s+birds|kill\s+it|killed\s+it|killing\s+(?:time|the\s+time)|"
    r"(?:could|can)\s+murder\s+a\b|murder\s+(?:a\s+)?(?:song|tune|curry|pint|coffee|brew)|"
    r"shake\s+it\s+off|shake\s+a\s+leg|shake\s+hands?|shake\s+(?:the\s+)?dust|"
    r"shake\s+up|shake\s+(?:some\s+)?sense\s+into|shake\s+a\s+fist|no\s+great\s+shakes|"
    r"hit\s+the\s+(?:road|sack|hay|shops?|gym|bottle|roof|ground|deck|bar|pub|town)"
    r"|hit\s+the\s+nail|hit\s+a\s+wall|hit\s+it\s+off|"
    r"beat\s+(?:the\s+traffic|the\s+queue|the\s+rush|the\s+clock|a\s+retreat|the\s+heat)"
    r"|beat\s+(?:the\s+)?(?:eggs|cream|batter)|"
    r"(?:slap|smack)\s+(?:some\s+)?(?:butter|sauce|paint)|"
    r"kick\s+(?:the\s+tyres|off|back\s+and\s+relax|it)|kick\s+(?:the\s+)?(?:habit|bucket)|"
    r"kick\s+(?:\w+\s+){0,3}out\b|"
    r"shoot\s+(?:hoops|some\s+hoops|the\s+shit)|shoot\s+through|"
    r"strangle\s+a\s+yawn|strangled\s+a\s+yawn)\b", re.I)

# The frame a wish comes in, in front of the verb: "i want to kill my boss", "i could strangle
# him", "im going to hit her", "i might punch him". Without one, the same shape is a report.
_WISH = re.compile(
    r"\b(?:want|wanna|wants|wanting|going|gonna|about|ready|tempted|could|would|might|may|will|"
    r"shall|should|need|needs|have|gotta|dying|half|like|feel)\b")
# The words that can stand in front of a bare doing ("just kill him", "honestly, punch him") and
# nothing else: a noun phrase there is the subject of a report.
_BARE_LEAD = frozenset(("just", "please", "honestly", "god", "and", "then", "so", "ok", "okay",
                        "right", "look", "mate", "now", "sometimes", "nearly", "almost"))
# "i want to hurt my son's feelings" is the language of being unkind, not of hurting somebody,
# and it was answered with the card written for a parent at the end of their rope.
_FEELINGS = re.compile(r"\bhurt(?:ing)?\s+(?:[a-z']+\s+){0,3}feelings?\b", re.I)

POOL = (
    "I'm not going to help with that, but something has pushed you a long way. What happened?",
    "That is a lot of anger to be carrying. What has actually happened?",
    "Fair to be that angry. What has been going on?",
)
# The fourth line says the person back, so two turns of the same anger are not one sentence.
NAMED = "Sounds like {person} has worn you down. What has been the worst of it?"
# A child is not somebody to be worn down by: a parent saying this is at the end of what they
# can carry, and the first line has to be the safe thing, not a question that keeps them in the
# room with the child. Two pools, because the words say different things about age: a baby or a
# toddler is in the room in front of them, and a son or a daughter may be forty, so the line that
# says "every parent gets to the end of their rope" only fits the ones still small.
A_SMALL_CHILD = re.compile(r"\b(?:bab(?:y|ies)|infants?|newborns?|toddlers?|little one)\b", re.I)
A_CHILD = re.compile(r"\b(?:child|children|kid|kids|stepchild|stepchildren|sons?|daughters?)\b(?!"
                     r"[\s-]+in[\s-]?law)", re.I)
# A person word is the person they are angry with only when it stands on its own: "my son" and
# "my son because he..." do, while "my son's teacher", "my son's bully" and "my son's feelings"
# name somebody or something else, and the child card belongs to nobody there. These are the
# words a sentence carries on with after the person; anything else is a new noun.
_IN_LAW = re.compile(r"^[\s-]+in[\s-]?laws?\b", re.I)
_JOINERS = frozenset((
    "because", "who", "that", "so", "and", "but", "or", "if", "when", "whenever", "while",
    "at", "on", "in", "to", "for", "with", "about", "over", "again", "today", "tonight", "now",
    "last", "this", "every", "is", "was", "has", "had", "does", "did", "will", "would", "keeps",
    "kept", "said", "says", "told", "tells", "called", "texted", "right", "still", "just",
    "tomorrow", "yesterday", "later", "soon",
))
BABY_LINES = (
    "Put some distance between you and them before anything else: out of the room, and put them "
    "down somewhere safe first. Then ring someone today - a partner, a friend, your health "
    "visitor or your GP - and say the words you just typed. Being this close to the edge is not a "
    "thing to sit on alone.",
    "Step out of the room before anything else, and put them down somewhere safe first. Then ring "
    "somebody today rather than later: a health visitor, a GP, or a friend who will come over. "
    "Every parent gets to the end of their rope, and the ones who say it out loud are the ones who "
    "get help.",
)
# The age says nothing here, so nothing in these lines assumes a small one: distance now, one
# person told today, and no "every parent" for a grown son.
CHILD_LINES = (
    "Step away from them before you say another word: out of the room, and a walk if you can. "
    "Then ring somebody today - a partner, a friend, your GP - and say the words you just typed. "
    "Wanting to hurt your own child is not a thing to carry on your own.",
    "Put some distance between you and them now, and give it an hour before you speak to them "
    "again. Then tell one person today what you have just written - someone who will take it "
    "seriously. Being this far past the end of your rope is not something to sit on alone.",
)
# The doing with no person as its object - "i want to punch something", "i want to smash a wall" -
# is the same anger with nothing to aim at. It is not a wish about anybody, so it gets the anger
# pool and never the line that says a person back, and it is only these verbs: "i want to kill
# something" may be the wasps.
OUTBURST = re.compile(r"\b(?:something|anything|whatever)\b[.,!?]*$", re.I)
OUTBURST_WALL = re.compile(r"\b(?:a|the) wall\b", re.I)
OUTBURST_VERB = re.compile(r"\b(?:hit|punch|smack|slap|kick|smash|thump|whack|headbutt|"
                           r"scream|shout|throw)\b", re.I)


_BODY = frozenset(("face", "head", "teeth", "nose", "jaw"))


def _person_said(clean):
    """"your boss" - the person they are angry with, said in the second person.

    The reply talks to them, not for them: "my mate is a nightmare, i want to kill him" got
    "Sounds like my mate has worn you down", which is the bot putting the person's own word in
    its own mouth.
    """
    text = " ".join(str(clean or "").lower().split())
    hurt = _HURT.search(text)
    # The person being hurt is the one after the verb: "i want to hurt the man who hurt my
    # daughter" was read back as "your daughter", who is the one he is angry for. The whole line
    # is the second place to look, for the anger named after it ("my mate is a nightmare, i want
    # to kill him").
    for span in ([text[hurt.start():]] if hurt else []) + [text]:
        said = _said_back(span)
        if said:
            return said
    return ""


def _said_back(text):
    """The person in this piece of the line, said in the second person, or ""."""
    found = _THE_PERSON.search(text)
    if not found:
        return ""
    if not _stands_on_its_own(text, found):
        # "i want to kill my son's teacher" names the teacher, not the son: the possessive in
        # front of a person word belongs to the next noun, so "your son has worn you down" is
        # about the wrong person and the pool line answers instead.
        return ""
    said = found.group(1).strip()
    if said.partition(" ")[2] in _BODY:
        # "i want to smash his face in" is about the person, but a face cannot have worn them
        # down: "Sounds like their face has worn you down" was the first reply it made.
        return ""
    head, _, rest = said.partition(" ")
    if head in ("the", "that"):
        # "the man who hurt my daughter" is somebody, but not somebody whose name or relation
        # they gave: "Sounds like the man has worn you down" says nothing, so the pool answers.
        return ""
    swaps = {"my": "your", "our": "your", "his": "their", "her": "their", "its": "their"}
    if head in swaps:
        said = (swaps[head] + " " + rest).strip()
    elif said in ("him", "her"):
        said = "them"
    if said in ("their", "them", "your"):
        # "i want to kill her" names nobody: the possessive swap turns the bare pronoun into
        # "their", and "Sounds like their has worn you down" is not a sentence - "them has worn
        # you down" is no better. A determiner with nothing after it is no person at all, so the
        # named line stands down and the anger pool answers instead.
        return ""
    return said


def reads_as_hurting_someone(clean):
    """True when the line says they want to hurt a person.

    A question is not this ("should i hit him?" asks for an opinion and gets one), and neither is
    the same verb said of somebody else ("she wants to kill her boss" is news about her, and "my
    brother punched a man" is a story). The wish has to be the speaker's - with or without the "i
    want to" in front of it, because "punch your brother" is the same wish left bare.
    """
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if not text or "?" in text:
        return False
    if _IDIOM.search(text):
        return False
    if re.search(r"\bkill(?:ing)?\s+(?:my|your|him|her)sel(?:f|ves)?\b|\bkill(?:ing)?\s+me\b", text):
        return False  # their own life is the safety module's line, and it answers it first
    hurt = _HURT.search(text)
    if not hurt:
        return False
    if _FEELINGS.search(text):
        return False  # "i want to hurt my son's feelings" is not a body and nobody is at risk
    if not _PERSON.search(text[hurt.start():]):
        # Nothing to aim at is still the same anger: "i want to punch something". The verb has to
        # be one of the body ones, so "i want to kill something" stays the wasps in the garden.
        tail = text[hurt.start():hurt.start() + 40]
        if not (OUTBURST.search(tail)
                or (OUTBURST_WALL.search(tail) and OUTBURST_VERB.search(tail))):
            return False
    opening = text[:hurt.start()].strip(" ,;:-\u2013\u2014")
    if re.search(r"\b(?:dont|don'?t|do not|never|no longer|wouldnt|wouldn'?t|couldnt|couldn'?t|"
                 r"cant|can'?t|wont|won'?t)\b(?:\s+\w+){0,4}\s*$", opening):
        return False  # "i dont want to hurt him any more" is a wish for it to stop
    # Somebody else doing it is a story, not their wish: "she wants to kill her boss".
    if re.search(r"\b(?:he|she|they|we|you|his|her|their|its)\b(?:\s+\w+){0,3}\s+"
                 r"(?:wants?|wanted|is|was|keeps|kept|might|may|will|would)\s*$", opening):
        return False
    if re.search(r"\b(?:i|i'm|im|i'd|id|ive)\b", opening):
        # A wish has its frame: "i want to", "i could", "im going to". The same words without
        # one are a report of what happened - "i hit my wife once and i hate myself" - and a
        # person saying what they did is not a person saying what they will do.
        return bool(_WISH.search(opening))
    # The bare form is an instruction ("punch your brother", "just kill him"), so what comes
    # before the verb is only ever a word in front of it. "my husband hit my face" opens on a
    # subject, which makes it something that happened to them.
    return not opening or all(word in _BARE_LEAD for word in opening.split())


def reads_as_our_reply(reply):
    """Whether this reply is one of the lines from here.

    The arbiter recognises the harm reading by its wording rather than by the module that
    proposed it: the reply is written here and only passed on by chat, and which module carries
    it is chat's business. Naming a person ("your brother") is matched by its two fixed halves.
    """
    text = " ".join(str(reply or "").split())
    if not text:
        return False
    if text in POOL or text in BABY_LINES or text in CHILD_LINES:
        return True
    head, _, tail = NAMED.partition("{person}")
    return bool(head and tail and text.startswith(head) and text.endswith(tail)
                and len(text) > len(head) + len(tail))


def _child_at_the_hurt(flat):
    """"small" or "child" when the doing is aimed at their own child, else "".

    The word alone is not enough: `when i was a kid` is the speaker as a child, "my son's
    teacher" is somebody else, and "the man who hurt my daughter" is a parent being protective.
    So the child has to be the first person after the doing - the one it is aimed at - and it
    has to be the whole of that person ("my son", not "my son's teacher").
    """
    hurt = _HURT.search(flat)
    if not hurt:
        return ""
    tail = flat[hurt.start():]
    first = _PERSON.search(tail)
    if not first:
        return ""
    phrase = first.group(0)
    if _IN_LAW.match(tail[first.end():]):
        return ""  # "my son in law" is a person to name back, not their child
    if not _stands_on_its_own(tail, first):
        return ""
    if A_SMALL_CHILD.search(phrase):
        return "small"
    return "child" if A_CHILD.search(phrase) else ""


def _stands_on_its_own(text, found):
    """Whether the person phrase is the whole person, not the start of a longer noun phrase."""
    rest = text[found.end():].lstrip(" ,.;:!?-")
    if not rest:
        return True
    word = re.match(r"[a-z']+", rest)
    return bool(word) and word.group(0) in _JOINERS


def reply_for(clean, memory=None):
    """The reply to a line that says they want to hurt somebody, or None."""
    if not reads_as_hurting_someone(clean):
        return None
    flat = " ".join(str(clean or "").lower().split())
    child = _child_at_the_hurt(flat)
    if child == "small":
        # The safe thing first, and no line that says a child back to them as somebody who has
        # worn them down.
        return pick(BABY_LINES, memory, clean)
    if child:
        return pick(CHILD_LINES, memory, clean)
    person = _person_said(clean)
    options = list(POOL)
    if person and person not in ("him", "her", "them"):
        options.append(NAMED.format(person=person))
    if not person:
        options = list(POOL)
    return pick(options, memory, clean)
