"""The reading of a line where the person is the one who did it to somebody.

Most lines that name a person are about that person: "my mum is upset with me" is a question
about the mum, "my wife and i argue about money" one about the money, "my mums birthday" one
about a party. A line where the person reports a deed of their own is the opposite of those. The
person named is who it was done *to*, and what the line wants is what to do about it now.

    i let my mum down, what do i do             the friend, on how to put it right
    i upset my dad what should i do             not "you seem a bit off with me - have I done
                                                something?", which asks the dad's question
    i forgot my mums birthday, what do i do     not a party to plan: the day has gone
    i lied to my wife about the money           not how to split the bills

So the reading has one job: say whether the deed in the line is the person's own. It is asked by
the two parts that would otherwise answer the person named - the composer's repair pool
(`bot/modules/chat.py`, "something they said that they wish they had not said") and the rows
whose key names a person with the other direction in mind (`guard=` in the knowledge base).

Every shape here is a deed people do to somebody they live with, followed by a person. The verb
is what decides it, never a word like "upset" on its own: "my mum is upset" has no deed in it,
"i upset my mum" has one, and "i upset my stomach" has a body part rather than a person. What a
deed is followed by is a person in the possessive ("my wife", "his brother") or a pronoun
("i let her down", "i lied to them") - a plain "the waiter" or "the dog" is not the shape this
reading is for, and the rows that answer them keep those lines.
"""
import re

# The people a deed is done to. Kept to the ones a person writes about as their own life: family,
# a partner, a friend, the people they work with. A stranger or a member of staff is left out on
# purpose - "i was short with the waiter" is a manners question, not a repair with somebody close.
PEOPLE = (r"(?:mum|mom|mam|mother|dad|father|son|daughter|child|kid|kids|baby|partner|husband|"
          r"wife|boyfriend|girlfriend|fiance|fiancee|ex|sister|brother|nan|nana|gran|granny|"
          r"grandma|grandad|grandpa|aunt|uncle|cousin|stepmum|stepdad|stepson|stepdaughter|"
          r"mother in law|father in law|in laws|friend|friends|mate|best friend|bestie|"
          r"flatmate|housemate|neighbour|neighbor|boss|manager|colleague|coworker|team|staff)")
# Who it was done to: somebody close, named with a possessive, or a pronoun.
WHO = (r"(?:(?:my|his|her|their|our|the)\s+%s|him|her|them|someone|somebody)" % PEOPLE)
# Words that sit between "i" and the deed without changing it ("i have just really let ... down").
_BETWEEN = r"(?:(?:have|had|ve|d|just|really|actually|totally|completely|already|also|then|" \
           r"kind of|sort of|so|still|again|keep|keeps|kept|always|often|usually|sometimes|" \
           r"constantly|managed to|went and)\s+){0,4}"

# The thing they were meant to be at: their play, their match, their nativity. The adjectives in
# front of it are the ones people use ("school play", "first concert") and the owner is the person
# ("my daughters school play", "his concert") - either a name for the person or a possessive.
_THE_THING_THEY_WERE_IN = (
    r"(?:%s)?(?:play|concert|recital|match|game|show|performance|assembly|sports day|"
    r"parents evening|parents' evening|nativity|graduation|prize giving|prizegiving|first day|"
    r"open day|appointment)\b"
    % r"(?:school|first|big|little|football|netball|swimming|music|dance|"
      r"christmas|xmas|summer|end of term|leavers?)\s+")

# Each deed as its own sentence, so the reading can say which one it found: the label is what the
# pools keep their wording by, and a deed with no reply of its own can be added without touching
# the others.
DEEDS = (
    # "i let my mum down" is the plainest way of saying this, and it has nothing in common with
    # the other verbs: the deed is in the particle. The same deed comes back in its noun form
    # after "about" or "for" - "what do i do about letting my mum down" was a search hedge.
    ("let down", re.compile(
        r"(?:\bi\s+%s|\b(?:about|for|after|of)\s+%s)(?:let|lets|letting)\s+%s\s+down\b"
        % (_BETWEEN, _BETWEEN, WHO))),
    # A lie about money, a text or a night out: the deed is the telling of it.
    ("lied", re.compile(r"\bi\s+%s(?:lied|lie|lying|lies)\b[^.!?]{0,20}?\bto\s+%s\b"
                        % (_BETWEEN, WHO))),
    ("lied", re.compile(r"\bi\s+%s(?:told|tell|have told|ve told)\s+(?:%s\s+)?(?:a\s+)?lie\b"
                        % (_BETWEEN, WHO))),
    # The date is the deed, whoever it was: a birthday or an anniversary that was missed is the
    # day gone, and nothing that plans a party answers it.
    ("forgot a date", re.compile(
        r"\bi\s+(?:(?:keep|always|completely|totally|just|nearly|almost|went and|went)\s+){0,3}"
        r"(?:forgot|forget|forgetting|forgotten)\b[^.!?]{0,40}?"
        r"\b(?:birthday|anniversary)\b")),
    # The same deed said the other way: a birthday that was missed rather than one they forgot.
    ("forgot a date", re.compile(
        r"\bi\s+%s(?:missed|miss)\s+(?:%s'?s?\s+)?(?:birthday|anniversary)\b"
        % (_BETWEEN, WHO))),
    ("lost my temper", re.compile(r"\bi\s+%s(?:lost|lose|losing|have lost|ve lost)\s+my\s+temper\b"
                                  % _BETWEEN)),
    # The feeling verbs, with the person as the object: "i upset my dad", "i hurt her", and the
    # ones with "feelings" after them.
    ("upset them", re.compile(
        r"\bi\s+%s(?:upset|hurt|offended|insulted|embarrassed|annoyed|disappointed|angered)\s+%s\b"
        % (_BETWEEN, WHO))),
    ("upset them", re.compile(r"\bi\s+%s(?:hurt|upset|offended|annoyed)\s+%s'?s?\s+feelings\b"
                              % (_BETWEEN, WHO))),
    # "i was horrible to my mum", "i was a bit sharp with her": the adjective is the deed.
    ("was unkind to them", re.compile(
        r"\bi\s+%s(?:was|been|am|have been|ve been|were)\s+(?:a bit |a little |really |very |"
        r"so |quite |pretty |just |being |really being |so being )*"
        r"(?:rude|horrible|mean|cruel|unkind|nasty|sharp|short|unfair|dismissive|snappy|"
        r"off|offhand|harsh|awful|dreadful|terrible|disrespectful|cheeky|abrupt)\s+"
        r"(?:to|with|towards|toward)\s+%s\b" % (_BETWEEN, WHO))),
    # A raised voice at somebody, which is the same deed said with the volume up.
    ("shouted at them", re.compile(
        r"\bi\s+%s(?:shouted|yelled|screamed|snapped|swore|sworn)\s+"
        r"(?:at|with)\s+%s\b" % (_BETWEEN, WHO))),
    # A sentence of their own that landed badly. The words are the deed here rather than a verb,
    # and both the verdict on it ("something stupid") and the retelling ("i told her her cooking
    # was awful") are the same reading: what is said is the subject, not where it was said.
    ("said the wrong thing", re.compile(
        r"\bi\s+(?:%s)?(?:said|say|saying|told|tell|telling)\s+(?:the wrong thing|the wrong "
        r"words|something\s+(?:stupid|awful|daft|silly|dumb|mean|horrible|wrong|embarrassing|"
        r"terrible|harsh|unkind))\b" % _BETWEEN)),
    ("said the wrong thing", re.compile(
        r"\bi\s+(?:%s)?(?:said|told)\b[^.!?]{0,40}\b(?:was|were|is) (?:awful|horrible|stupid|"
        r"mean|rude|unkind|dreadful|terrible|nasty|rubbish|disgusting|pathetic)\b" % _BETWEEN)),
    # The deeds where the promise or the plan is the thing that was broken.
    # A thing they were meant to be at and were not: the play, the match, the parents' evening.
    # There is nothing to quote back and nothing to plan either - the day has gone - so it is a
    # repair like the rest, with a person on the other end of it.
    ("missed their thing", re.compile(
        r"\bi\s+%s(?:missed|miss)\s+(?:(?:%s)'?s?\s+|(?:my|his|her|their|our)\s+)%s"
        % (_BETWEEN, WHO, _THE_THING_THEY_WERE_IN))),
    ("broke a promise", re.compile(
        r"\bi\s+%s(?:broke|broken|break|breaks|have broken|ve broken)\s+(?:a\s+|my\s+|the\s+)?"
        r"promise\b" % _BETWEEN)),
    ("cancelled on them", re.compile(
        r"\bi\s+%s(?:stood|stand|standing)\s+%s\s+up\b" % (_BETWEEN, WHO))),
    ("cancelled on them", re.compile(
        r"\bi\s+%s(?:cancelled|canceled|cancel|cancelling|canceling)\s+(?:on\s+)?%s\b"
        % (_BETWEEN, WHO))),
    ("ignored them", re.compile(
        r"\bi\s+%s(?:ignored|ignore|ignoring|blanked|blank)\s+%s\b" % (_BETWEEN, WHO))),
    # What was ignored can be the ringing rather than the person: "i ignored my mums calls". The
    # same deed, said with the calls in the way, and it was reaching nothing at all.
    ("ignored them", re.compile(
        r"\bi\s+%s(?:ignored|ignore|ignoring|blanked|blank)\s+%s'?s?\s+"
        r"(?:calls?|texts?|messages?|emails?|letters?|invites?)\b" % (_BETWEEN, WHO))),
    # The deed said by what it did to them: "i made my mum cry", "i made my daughter cry twice".
    # It is the same turn as the rest - it is already done, and what the line wants is what to say
    # now - and it was reading as a report about the person who cried.
    ("made them cry", re.compile(
        r"\bi\s+%s(?:made|make|making|have made|ve made)\s+%s\s+"
        r"(?:cry|cried|crying|sad|miserable|upset|tearful)\b" % (_BETWEEN, WHO))),
)

# The deed that is a thing not done: "i forgot to call my mum", "i havent spoken to my dad in
# months", "i didnt get my mum anything for her birthday". Nothing was done to anybody, so no verb
# of harm brings it here, and on main the three of those were answered with the card for a
# relative's memory going, the card for a family that has drifted, and a party to plan.
#
# They are read before `NOT_A_DEED` and `NOBODY_TO_REPAIR`, because both of those are about a thing
# that happened to the person rather than a person they left waiting: "i never called my mum back"
# and "i didnt get my mum anything" are a deed of their own, and the settled outcomes the guards
# are written for ("i didnt get the job") have nobody in them.
# "spoken to" and "talked to" are deliberately not in this list: "i havent spoken to my dad in
# years" and "i havent spoken to my friends in months" are a gap that both ends let go quiet, and
# the card for a relative who has drifted (and the friendship one beside it) answer the sending of
# the message themselves. A lapse here is the thing the person did not do for somebody who was
# waiting for it, so it is the call, the card, the visit, the present.
_LAPSE_VERBS = (
    r"(?:call(?:ed|ing)?|ring|rang|rung|ringing|text(?:ed|ing)?|messag(?:e|ed|ing)|"
    r"repl(?:y|ied|ying)|writ(?:e|ing|ten)|visit(?:ed|ing)?|wish(?:ed|ing)?|send|sent|sending)")
LAPSES = (
    ("left it too long", re.compile(
        r"\bi\s+%s(?:forgot|forget|forgetting|have forgotten|ve forgotten)\s+to\s+"
        r"%s\b[^.!?]{0,30}?%s" % (_BETWEEN, _LAPSE_VERBS, WHO))),
    ("left it too long", re.compile(
        r"\bi\s+%s(?:didnt|didn'?t|did not|never|havent|haven'?t|have not|hadnt|hadn'?t|"
        r"had not|hasnt|hasn'?t|has not)\s+%s"
        r"(?:\s+to)?\s+%s'?s?\b" % (_BETWEEN, _LAPSE_VERBS, WHO))),
    # Not having seen somebody is the same lapse said with the eyes: "i havent seen my mum in
    # ages" was the card for the family that had drifted, which is about them rather than you.
    ("left it too long", re.compile(
        r"\bi\s+%s(?:havent|haven'?t|have not|hadnt|hadn'?t|had not)\s+"
        r"(?:seen|saw|visited|been\s+to\s+see)\s+%s\s+in\b"
        % (_BETWEEN, WHO))),
    ("left it too long", re.compile(
        r"\bi\s+%s(?:didnt|didn'?t|did not|never)\s+(?:get|got|buy|bought|send|sent)\s+%s\s+"
        r"(?:anything|nothing|a\s+(?:present|gift|card))" % (_BETWEEN, WHO))),
)


# A deed that is not one: the body, a thing, or the idiom. "i let my hair down" is a good evening,
# "i hurt my back" is the back, and "i let the tyres down" is a bike. Each of these can be reached
# by the shapes above and none of them has anybody in it to put something right with.
NOT_A_DEED = re.compile(
    r"\b(?:let|letting)\s+(?:my|her|his|their|your)\s+hair\s+down\b|"
    r"\bi (?:hurt|upset|pulled|broke|twisted|strained|cut|burnt|burned|dislocated|sprained)\s+"
    r"my\s+(?:back|knee|ankle|shoulder|arm|leg|foot|feet|hand|finger|wrist|neck|head|hip|"
    r"stomach|toe|ribs?|thumb|elbow|eye|teeth|tooth|ear|throat|chest|spine|hamstring|"
    r"calves|calf|shin|jaw|skin|appetite|weight|sleep|hair)\b|"
    r"\bi (?:lost|lose|losing)\s+my\s+(?:keys|phone|wallet|purse|job|way|mind|"
    r"trainers|glasses|vape|earbuds?)\b|"
    r"\bi (?:am|m|feel|felt|been)\s+(?:so |really |very |a bit )?"
    r"(?:lost|stuck|short of|out of)\b|"
    r"\bi (?:never|don'?t|didnt|didn'?t|hardly ever|rarely)\s+(?:let|lied|lie|forget|lose|lost|"
    r"shout|yell|snap|swear|cancel|ignore|blank)\b")
# A deed with the outcome already settled has nobody left to repair it with: the interview is
# over, the job is gone, and the person's own turn already carries the loss. The composer's pool
# stands down on these (`SAID_WRONG_LOST`) and so does this reading, so a row about the loss is
# not held out by a guard for a repair nobody can make.
NOBODY_TO_REPAIR = re.compile(
    r"\b(?:didnt|didn'?t|did not|never)\s+(?:get|got|win|won|pass|passed|make|made)\b|"
    r"\b(?:got|been) (?:fired|sacked|dumped|rejected|turned down)\b|"
    r"\bthere'?s no fixing\b|\bit'?s too late\b")


# A body that was struck rather than a feeling that was hurt: "i hurt my baby" is a different
# turn from "i hurt my husbands feelings", and it is the one where the bot must not settle for how
# to word an apology. Physical harm keeps whatever answer it already had (bot/compose/harm.py
# reads it), and so does the "hurt" that names a part of somebody's body rather than a feeling.
PHYSICAL_HARM = re.compile(
    r"\b(?:hit|hits|hitting|punch|punched|slap|slapped|push|pushed|shove|shoved|shook|shake|"
    r"shaking|kick|kicked|throw|threw|thumped|strangle|strangled|bit|biting|dragged|grabbed)\b|"
    r"\b(?:hurt|hurting|injured|burned|burnt|bruised)\s+(?:my|her|his|their|our)\s+"
    r"(?:baby|child|kid|kids|son|daughter|wife|husband|partner|girlfriend|boyfriend|mum|mom|dad|"
    r"mother|father|sister|brother)\b(?!'?s?\s+feelings)")


# A pet or a professional is not somebody to repair something with: a dog does not read an
# apology, and "i said the wrong thing to my doctor about my symptoms" is a briefing that went
# wrong rather than a person who was hurt.
PET_OR_PROFESSIONAL = re.compile(
    r"\b(?:to|with|at)\s+(?:my|our|the|a)\s+(?:dog|cat|puppy|kitten|horse|pony|rabbit|"
    r"hamster|guinea pig|budgie|parrot|pet|fish|bird|chickens?|sheep|cow|goat|lamb|doctor|gp|"
    r"nurse|consultant|surgeon|midwife|health visitor|dentist|orthodontist|physio(?:therapist)?|"
    r"pharmacist|optician|vet|solicitor|accountant|landlord|letting agent|bank)\b")


# The deeds that already had a card of their own on main, naming what was done and the next
# step: the shouting with a child, the birthday that has gone, the dinner being called off. A card
# like that is better than the short repair below, so a deed in this set whose row still answers
# keeps the turn (bot/modules/chat.py). Every other deed is the composer's, because what answered
# it was a row written for the person it happened *to*.
DEEDS_WITH_A_CARD = frozenset({"lost my temper", "shouted at them", "forgot a date",
                               "cancelled on them"})


# A line that opens with regret is the regret family rather than the deed's report: "i regret that
# i lied to her" is how someone tells you they feel about it, and the pool that names the feeling
# answers it (bot/modules/chat.py, `REPLIES["guilty"]`). The deed reading did take that one, and a
# card about owning up to it left the feeling unsaid.
_REGRET_FIRST = re.compile(r"^\s*(?:(?:honestly|god|tbh|ugh|so|ok|okay)\s+)*i\s+"
                           r"(?:just\s+|really\s+|deeply\s+|so\s+|still\s+)*regret\w*\b")

# An apology with the feeling in front of it: "i feel sick that i lied to her", "i feel bad about
# letting my mum down". The deed is real and the card for it is still the answer - the person wants
# the next step - but the feeling is what they led with, so the answer names it before the doing
# (`with_the_feeling_named`). A line that only names how they feel and asks nothing keeps the pool
# (`deed_of` returns None for it, because no deed is named at all).
_FEELING_FIRST = re.compile(
    r"^\s*(?:(?:honestly|god|tbh|ugh|sometimes|now|ok|okay|so)\s+)*"
    r"i\s+(?:just\s+|really\s+|still\s+|properly\s+|honestly\s+)*"
    r"(?:feel|felt|feels)\b"
    r"[^.?!]{0,40}?\b(?:that|about|for|because|when|after|of|at|like)\b\s*"
    r"(?:i|i'?ve|im|i'?m|me|my|not|letting|cancelling|missing|going|being|doing)\b")

# What the line's feeling is called back to them, so the card does not arrive as if nobody had just
# said how they felt. It is one sentence and then the deed's own step, because a confession still
# wants the next thing to do.
THE_FEELING_NAMED = ("Guilt like that is doing its job if it moves on: ")
THE_FEELING_NAMED_DATED = ("Guilt about a date does not make it right, so put it right: ")


# Somebody who has died is not somebody to ring this week: "i havent spoken to my dad in months"
# is a lapse to put right and "...since he died" is grief, and the two read the same to the shapes
# below. Nothing in this reading is the answer to a line about a death.
_GRIEF = re.compile(
    r"\b(?:died|dies|dying|death|deaths|passed away|passed on|funeral|burial|cremation|"
    r"grief|grieving|bereav\w*|widow|widower|widowed|estate|the will|his will|her will)\b")


# Too small to be owed anything: the line is about the crying, not about a repair.
_A_BABY = re.compile(r"\b(?:baby|babies|newborn|newborns|infant|infants)\b")


def deed_of(clean):
    """The deed the person reports doing to somebody, or None.

    `clean` is the line as the understanding engine hands it on, or a reading with "clean" in it.
    A deed with a pet, a doctor or a professional in it is not this reading: a dog does not read
    an apology and a briefing that went wrong is a mess rather than a wrong. Those keep whatever
    answer their own row gives them (`SAID_WRONG_TO_AN_ANIMAL`, `SAID_WRONG_TO_A_PROFESSIONAL`).
    """
    if isinstance(clean, dict):
        clean = clean.get("clean") or clean.get("text") or ""
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if not text:
        return None
    if PET_OR_PROFESSIONAL.search(text) or PHYSICAL_HARM.search(text):
        return None
    if _GRIEF.search(text):
        return None
    # A baby crying is the baby's evening rather than a deed to put right, so "i made my baby cry"
    # keeps whatever answer it had. A toddler or a child it is a deed like the others.
    if _A_BABY.search(text):
        return None
    if _REGRET_FIRST.search(text):
        return None
    for deed, pattern in LAPSES:
        if pattern.search(text):
            return deed
    if NOT_A_DEED.search(text) or NOBODY_TO_REPAIR.search(text):
        return None
    for deed, pattern in DEEDS:
        if pattern.search(text):
            return deed
    return None


def owns_the_deed(line):
    """True when the line reports something the person did to somebody close. A `guard=` test."""
    return deed_of(line) is not None


# Asking how to make amends, with or without the deed named: "how do i make it up to my mum", "how
# do i make amends to my dad", "how do i put it right with my sister". The person is named and the
# question is what to *do*, and the cooking entry answered two of those with a tray bake because
# "make" and "up to" are also how a dish is sized.
_AMENDS = (
    # the thing that was got wrong can sit between the verb and "up to" when the store has
    # pointed "it" back at the subject: "how do i make my mums birthday up to my mum" was read as
    # a birthday still to plan, and the party plan took the turn.
    r"\b(?:make|making)\s+(?:[\w']+\s+){0,6}up\s+to\s+%s\b|"
    r"\b(?:make|making|made)\s+(?:it\s+)?up\s+to\s+%s\b|"
    r"\bmake\s+(?:it\s+)?up\s+with\s+%s\b|"
    r"\bmake\s+(?:some\s+)?amends\b|"
    r"\bput\s+(?:it|things)\s+right\s+(?:with|to)\s+%s\b")
AMENDS = re.compile(_AMENDS % (WHO, WHO, WHO, WHO))


def with_the_feeling_named(reply, clean):
    """The deed's card under a sentence that names the feeling the line led with.

    "i feel sick that i lied to her" is a confession that says how they feel before it says what
    they did, and the card alone answers as though nobody had. The name goes in front and the card
    follows, because the deed still wants its step; a line with the feeling somewhere in the middle
    ("i lied and i feel awful") keeps the card alone.
    """
    if not reply:
        return reply
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if not _FEELING_FIRST.search(text):
        return reply
    lead = THE_FEELING_NAMED_DATED if deed_of(text) == "forgot a date" else THE_FEELING_NAMED
    return lead + reply[0].lower() + reply[1:]


def line_of(reading):
    """The line as a reading holds it, for a guard that has to read the words themselves.

    A guard is handed the reading, which is a dict for the line as typed and a re-pointed one
    when the store has put back what an "it" stood for. Both carry the words, so a guard about
    the shape of the line reads `clean` and falls back to `text` or the tokens.
    """
    if isinstance(reading, str):
        return reading
    if not isinstance(reading, dict):
        return ""
    for key in ("clean", "text"):
        value = reading.get(key)
        if isinstance(value, str) and value:
            return value
    return " ".join(word for word in (reading.get("words") or ()) if isinstance(word, str))


def amends_to(clean):
    """True when the line asks how to make amends to somebody, without naming a deed.

    "how do i make it up to my mum" has no verb of doing in it, so `deed_of` is right to say
    there is no deed; what it asks for is the same turn's answer - the specific thing that would
    put it right. A pet or a professional stands it down for the same reason it stands the deed
    down, and a part of the body is not somebody to make amends to.
    """
    if isinstance(clean, dict):
        clean = clean.get("clean") or clean.get("text") or ""
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if not text or not AMENDS.search(text):
        return False
    return not (PET_OR_PROFESSIONAL.search(text) or PHYSICAL_HARM.search(text))


# The asks that lean on the turn before them: "what do i actually say to her", "what should i do"
# after the deed. A line of these is part of the repair already open, so the walk above passes
# through it; anything else means the chat has moved on and the deed is not what is being asked
# about any more. The two patterns live here so the knowledge base can read the same repair the
# composer does (bot/modules/chat.py imports them from here).
ASKS_FOR_THE_WORDS = re.compile(
    r"\bwhat (?:do|should|shall|can|could) i (?:actually |really )?(?:say|tell)\b|"
    r"\bhow (?:do|should) i (?:say it|word it|put it|phrase it)\b|"
    r"\bwhat (?:would|should) i say\b|\bwhat do i say to\b|\bhow do i tell (?:her|him|them)\b|"
    r"\bi (?:just |really )?dont know what to say\b")

ASKS_WHAT_TO_DO = re.compile(
    r"\bwhat (?:do|should|shall|can|could) i do\b|\bhow (?:do|can|should) i (?:fix|make|put|"
    r"smooth|sort)\b|\bhow do i (?:fix it|make it right|make up for it)\b|"
    r"\bwhere do i start\b|\bwhat now\b|\bwhats the next step\b|\bany advice\b|"
    r"\bwhat would you do\b|\bhow do i say sorry\b|\bhow do i apologise\b")


def a_repair_is_open(memory):
    """True when the turns just said are one repair, with the asks in the middle of it.

    The line that follows two follow-ups still belongs to the repair the conversation opened
    with: "i made my mum cry", "i dont know what to say", "she wont talk to me". Only the asks
    that lean on the turn before them are walked through, so a chat that has moved on to a fresh
    subject is not pulled back into an apology from three turns ago.

    The knowledge base asks this too. "hes not speaking to me" the day after an apology has the
    words of a small child who is late talking, and the row for that child answered it with the
    speech milestones; the silence here is the repair's, so the row stands down.
    """
    if not isinstance(memory, dict):
        return False
    told = [str(turn.get("user") or "").lower() for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    for said in reversed(told[-3:]):
        said = " ".join(said.split())
        if not said:
            continue
        if owns_the_deed(said) or amends_to(said):
            return True
        if len(said.split()) > 9 or not (ASKS_FOR_THE_WORDS.search(said)
                                         or ASKS_WHAT_TO_DO.search(said)):
            return False
    return False
