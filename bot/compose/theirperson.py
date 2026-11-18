"""Somebody they are close to is having a rough patch, and the store only says it back.

Half the hard things a person brings a chatbot are second-hand: "my husband is having a hard
time", "my mate is going through a rough time", "my daughter is going through a rough patch".
Nothing in this bot knows their husband, so no card takes the line, and the composer does not read
it as a feeling either - the feeling is not theirs, and every feeling pool stands down when a line
names somebody else (`bot/compose/trouble.py`, `OTHERS`). What is left is the ack, so the person
tells the bot that somebody they love is struggling and gets their own sentence handed back:

    my wife is having a rough time        "Your wife is having a rough time, good to know."
    my neighbour is having a hard time    "Noted: your neighbour is having a hard time."
    my brother is having a tough time     "Your brother is having a tough time - noted."
    my daughter is going through a rough patch   "Got it - your daughter is going through a
                                                  rough patch."

STYLE.md asks a reply to answer the person in its first sentence, and to be concrete. A receipt
is neither: it adds nothing to what they just said, and it does not notice that the thing they
brought was hard. The one thing this bot can honestly do with the shape is say the true thing -
it is hard to watch - and ask the question that helps a person in that position, which is about
the person they are worried about.

This module reads only that shape, and only to answer; it never says a fact about anybody. No
cause, no diagnosis, no advice about treatment: "they are depressed", "it is probably the move",
"they should see a doctor" are all things this file must never say. What it knows is what the
person just told it, and what it asks is the next thing a friend would ask.

It checks out of everything else (`STANDS_DOWN`). A line that names a body part or an illness, a
death, or that asks the bot something ("what do i say to her", "how can i help") has a card of
its own - `bot/compose/trouble.py` for the body, `bot/compose/loss.py` for a death, the knowledge
base for anything asked as advice - and a fallback that took one of those turns would make the
bot worse, not better.

It is called from `bot/modules/greeting.py`, and only where the composer's line was a hedge or
was the person's own words back: a module with an answer for the line has already answered.
"""
import re

from . import pick

# The people a person brings here: the relations people type, and the friends who are named the
# way they are named. A pet is not one of these on purpose - "my dog is having a hard time" is a
# question about the animal, and the animal cards are the ones that answer it.
SOMEONE = (
    "best friend", "best mate", "close friend", "old friend", "friend", "mate", "pal", "buddy",
    "flatmate", "housemate", "workmate", "schoolmate", "colleague", "boss", "partner",
    "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee", "ex",
    "mum", "mom", "mam", "mother", "dad", "father", "son", "daughter", "child", "kid", "baby",
    "sister", "brother", "sibling", "stepson", "stepdaughter", "stepmum", "stepdad",
    "nan", "nana", "gran", "granny", "grandma", "grandad", "grandpa", "grandmother",
    "grandfather", "aunt", "auntie", "uncle", "cousin", "nephew", "niece", "neighbour",
    "neighbor", "parents", "kids", "children", "sisters", "brothers", "friends", "mates",
)
# The words that come between "my" and the person without changing who it is: "my best friend",
# "my poor old nan", "my grown up son".
BETWEEN = (r"(?:(?:best|closest|close|poor|old|little|big|lil|eldest|youngest|older|younger|"
           r"grown[-\s]?up|step|new|other)\s+)*")
A_PERSON_OF_THEIRS = re.compile(
    r"\b(?:my|our)\s+" + BETWEEN
    + "(?:" + "|".join(word.replace(" ", r"[\s-]?") for word in
                       sorted(SOMEONE, key=len, reverse=True)) + r")\b", re.I)

# The rough patch, read from where the person left off. It has to follow the person closely -
# the tail is matched from its start - so a line about two people ("my sister was fine and i am
# struggling") is not read as one about her.
A_ROUGH_PATCH = re.compile(r"""
    ^\s*(?:
        (?:is|are|was|were|has|have|had)\b
      | s\s+been\b
      | been\b
    )
    # "really struggling", "still having a hard time", "been a bit down": the adverbs a person
    # puts in front of it, and "been" twice over ("has been really down").
    (?:\s+(?:really|very|so|just|still|properly|proper|completely|totally|quite|pretty|a\s+bit|
            well|dead|awful|genuinely|seriously|always|also|obviously|clearly|been|badly))*\s+
    (?:
        having\s+(?:a\s+|one\s+hell\s+of\s+a\s+|such\s+a\s+|the\s+worst\s+)?
          (?:(?:really|very|proper|properly|awful|bit\s+of\s+a|lot\s+of|terrible)\s+)?
          (?:hard|tough|rough|bad|rubbish|awful|terrible|difficult|stressful|horrible|lousy|
             miserable|shit|shitty|grim|dreadful)\s+
          (?:time|patch|spell|week|month|year|day|run)\b
      | struggling\b(?!\s+with\b)
      | finding\s+(?:it|things|everything|life|work|the\s+job)\s+
          (?:a\s+bit\s+|really\s+|very\s+|so\s+|quite\s+)?hard\b
      | going\s+through\s+(?:a\s+lot|a\s+(?:rough|hard|tough|bad)\s+(?:time|patch|spell)|hell|
                             it|something\s+bad|a\s+bad\s+patch)\b
      | in\s+a\s+bad\s+way\b
      | at\s+breaking\s+point\b
    )
""", re.I | re.X)
# Not coping is the same rough patch said as a fault rather than a feeling, and only a negated
# form is it: "my mum isnt coping" is one, "my mum is coping" is the opposite.
A_NOT_COPING = re.compile(r"""
    ^\s*(?:(?:is|are|was|were)\s+not|isn'?t|aren'?t|wasn'?t|hasn'?t|havent|weren'?t|not|
            never)\b
    (?:\s+(?:really|very|so|just|still|been|at\s+the\s+moment|at\s+all))*\s+
    coping\b.*$
""", re.I | re.X)
# Low and down are the same rough patch said with a mood word, and they are also a place ("down
# the road") and a direction ("down to the shops"), so this one is anchored at both ends: the
# line has to end not long after it.
A_LOW = re.compile(r"""
    ^\s*(?:(?:is|are|was|were|has|have)\b|s\s+been\b|been\b)
    (?:\s+(?:really|very|so|a\s+bit|quite|pretty|proper|properly|just|always|still|been))*\s+
    (?:down|low)\b
    (?:\s+(?:at\s+the\s+moment|lately|these\s+days|just\s+now|right\s+now|again|too|still|today|
              this\s+week|since\s+[a-z0-9']+|about\s+[a-z0-9']+|in\s+(?:him|her)sel(?:f|ves)|
              and\s+[a-z0-9' ]+))?\s*[.!?]*\s*$
""", re.I | re.X)

# A named condition about a person of theirs, said plainly or only wondered about: "my son has
# adhd", "my daughter might be dyslexic", "my brother is dyslexic". Nothing in the knowledge base
# is about adhd, dyslexia, dyspraxia or autism, so no card takes the line, and the composer files
# it and says the noun back - "Noted: your son has adhd.", "Noted: your daughter could be
# dyslexic." A parent tells the bot what they are up against and gets their own sentence returned.
# The words below are only the conditions that have no card of their own: one that has (cancer,
# depress*, anxiety, diagnos*, a body part, a scan) is in STANDS_DOWN and keeps its answer, and a
# line that asks the bot something is a question, not a report.
A_CONDITION = re.compile(r"""
    ^\s*(?:
        (?:has|have|had|got)
      | ['\u2019]?s\s+got
      | (?:is|are|was|were)
      | (?:could|might|may|must)\s+be
      | (?:seems?|appears?)\s+(?:to\s+be)?
    )
    (?:\s+(?:really|very|probably|possibly|likely|also|now|actually|officially|just|
             only|maybe|perhaps|definitely|already|too))*\s*
    (?:a\s+bit\s+of\s+|a\s+touch\s+of\s+|an?\s+|mild\s+|suspected\s+)?
    (?P<condition>dyslexi\w*|dyspraxi\w*|dyscalculi\w*|adhd|add|autis\w*|asperger\w*|
      ocd|tourette\w*|non[\s-]?verbal|speech\s+delay|sensory\s+processing|deaf|
      hard\s+of\s+hearing|blind|partially\s+sighted|down'?s?\s+syndrome|
      learning\s+disabilit\w*|on\s+the\s+spectrum)\b
""", re.I | re.X)
# The two ways the shape is said, and they are not the same thing to answer. A line that states it
# - "my son has adhd", "my daughter is dyslexic" - is a thing about the person they are telling the
# bot, and what a friend does with it is ask what they are working on. A line that only wonders -
# "my daughter might be dyslexic", "my son could be autistic" - is a worry about an answer that has
# not come yet, and what a friend does with that is say the waiting is the hard part and ask what
# they have noticed. Neither arm says a cause, a diagnosis or what anybody should do.
A_WONDERING = re.compile(r"^\s*(?:could|might|may|must)\s+(?:be|have)\b|\bmaybe\b", re.I)
A_CONDITION_STATED = (
    "Thanks for telling me. Is there something about your {who} you're trying to work out?",
    "Good to know - I'll remember that about your {who}. Anything you're trying to sort out?",
    "Thanks. What's the part you're working on with your {who} just now?",
)
A_CONDITION_WONDERED = (
    "That's the hard part, the waiting. What have you noticed so far?",
    "It's rough sitting with a maybe like that. Write down what you see and when - that is what "
    "anyone you ask will want first. What made you start wondering?",
    "Not knowing yet is the worst of it. What has made you wonder?",
)

# What this file does not answer, however much it looks like the shape. A body part or an illness
# is somebody hurt or ill, which is `trouble.py`'s and the health entries'; a death is
# `loss.py`'s; and a line that asks the bot something ("what do i say", "any advice") is a
# question with an answer of its own, not a report that needs one question back.
STANDS_DOWN = re.compile(r"""
    \b(?:
        hip|knee|knees|back|shoulder|arm|arms|leg|legs|foot|feet|ankle|wrist|hand|hands|head|
        headache|migraine|stomach|belly|chest|throat|tooth|teeth|ear|ears|eye|eyes|skin|joint|
        joints|spine|neck|heart|lung|lungs|blood|pain|pains|hurt|hurts|hurting|ache|aches|aching|
        ill|sick|sickness|unwell|hospital|doctor|gp|surgery|operation|chemo|cancer|tumour|tumor|
        diagnos\w*|scan|scans|medication|tablets|pills|dose|prescription|depress\w*|anxiety|
        panic|suicid\w*|self[-\s]?harm|addiction|drinking|drunk|sober|withdraw\w*|
        died|dying|die|death|dead|funeral|bereave\w*|grief|grieving|passed\s+away|
        tests|exam|exams|redundancy|divorce|money|rent|bills
    )\b
    | \? | \b(?:what|how|should|advice|tips|help|why|when|where|who)\b
""", re.I | re.X)

# The reply. Every line says the true thing about the shape - it is hard to watch - and then asks
# the one question a friend would ask, about the person they are worried about or about what they
# are carrying themselves. No line says a cause, a diagnosis or what somebody should do.
POOL = (
    "That's hard, watching someone you're close to go through it. What's been happening?",
    "Sorry to hear it. Being the one who notices is its own weight - how are they doing in "
    "themselves?",
    "That's a worry to be carrying for someone else. What's going on at the moment?",
    "Hard when you can see it and can't fix it. Do they know you've noticed?",
    "That's a lot for them - and for you to watch. What would help most: someone to listen, or "
    "something practical?",
    "I'm sorry. It's rough being the one at the side of it. What's the hardest part for you just "
    "now?",
)
# The same asked with the person named, which only works where the person is one ("your best
# friend is", not "your parents are").
NAMED = (
    "That's hard, watching your {who} go through it. What's been happening?",
    "Sorry to hear it. How is your {who} in themselves?",
    "That's a lot for your {who} to carry, and for you to watch. What would help most?",
)


def _said(text):
    words = re.findall(r"[a-z0-9'?!]+", str(text or "").lower())
    return " " + " ".join(words) + " " if words else ""


def _who(person, said):
    """The person as the reply names them: "my best friend" is "best friend" (the line says
    "your {who}", so the possessive is not said twice)."""
    phrase = said[person.start():person.end()].strip()
    return re.sub(r"^(?:my|our)\s+", "", phrase, flags=re.I)


def reply_for(text, memory=None):
    """The friend's reply to somebody else's rough patch, or None when the line is not that.

    Only the shape is read: a person of theirs, as the subject, having a rough time. Everything
    else - the body, illness, a death, a question, an ask for advice - is left to the module that
    owns it.
    """
    said = _said(text)
    if not said.strip():
        return None
    if STANDS_DOWN.search(said):
        return None
    person = A_PERSON_OF_THEIRS.search(said)
    if not person:
        return None
    tail = said[person.end():]
    a_condition = A_CONDITION.match(tail)
    # "my son might have ADHD" is not the same line as "my son might be ADHD-ish": the knowledge
    # base answers the first - the counts, the school's SENCO, the GP referral - because a named
    # condition with "have" in front of it is the card's own shape. Only the wondering that lands
    # on what the person *is* reaches this file, and only with no card behind it.
    if a_condition and re.match(r"^\s*(?:could|might|may|must)\s+have\b", tail):
        return None
    if not (a_condition or A_ROUGH_PATCH.match(tail) or A_NOT_COPING.match(tail)
            or A_LOW.match(tail)):
        return None
    if a_condition and re.match(r"^\s*(?:and|&)\s+(?:i|me)\b", tail):
        return None
    # "my sister and i are really struggling": two people, one of them the person in front of the
    # bot, so it is their own line as much as hers. The feeling pools read that one better.
    if re.match(r"^\s*(?:and|&)\s+(?:i|me)\b", tail):
        return None
    read = memory.get("understood") if isinstance(memory, dict) else None
    read = read if isinstance(read, dict) else {}
    plural = bool(re.match(r"^\s*(?:are|were|have|have\s+been|were\s+being)\b", tail))
    if a_condition:
        # A condition has its own two arms, and the person is named in both: "your son" is who the
        # line is about, so the question goes to them and not to the person typing.
        pool = A_CONDITION_WONDERED if A_WONDERING.search(tail) else A_CONDITION_STATED
    else:
        pool = POOL if plural else POOL + NAMED
    # The line is worded before the choices are made, not after: "my wife is having a rough time"
    # said twice in a row got the same sentence twice, because the pool says "{who}" and the reply
    # just given says "your wife", so the composer's own "never the reply just given" had nothing
    # to compare. Every line here who-less is in POOL, and the dropped one is put back first when
    # it is the only line there is.
    who = _who(person, said)
    worded = [line.replace("{who}", who) for line in pool]
    turns = memory.get("turns") if isinstance(memory, dict) else None
    last = turns[-1].get("bot") if turns and isinstance(turns[-1], dict) else None
    if last and last in worded and len(worded) > 1:
        worded = [line for line in worded if line != last]
    return pick(worded, read, said.strip())


# A reply the composer gives when it has nothing: the hedge ("I'm not sure about that one... a
# quick search online"), the receipt ("Noted: your wife is having a rough time"), and the stock
# nod ("Got it. Is there anything you'd like a hand with?"). Every one of them leaves the person
# where they were, which is what makes them safe to replace - and it is the only thing this file
# replaces, so a card, a pool line with a feeling in it and an answer all keep their turn.
def may_replace(reply, text=""):
    """True when the bot's line for this turn says nothing about what the person brought."""
    said = str(reply or "").strip()
    if not said:
        return False
    from . import fallback  # noqa: PLC0415 - fallback imports a lot; only this file needs it

    if fallback._is_a_hedge(said) or fallback._in_a_pool(said, (fallback.NEUTRAL,)):
        return True
    # The person's own words, handed back: three quarters of what they said is in the reply, and
    # at least two of their words are. A reply that says something else shares nothing with the
    # line, which is how a real answer is told from a receipt.
    mine = fallback._the_words(text)
    theirs = fallback._the_words(said)
    if len(mine) < 2 or not theirs:
        return False
    shared = mine & theirs
    return len(shared) >= 2 and len(shared) / len(mine) >= 0.6
