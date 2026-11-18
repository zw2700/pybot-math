"""A thing the person rules out, answered against the answer they just got.

"not a series" after three films, "i dont like the gym" after an answer about half a plate of
vegetables, "not tablets" after a sleep answer. The person is steering, and what they ruled out was
never in the answer. What those lines got on main was the flat echo back ("Got it - not the
chemical stuff"), "Thanks for telling me - I'm here if you want to dig into any of that.", or a
wrong entry entirely: "not a diesel" reached the misfuelling card and "not tablets" the repeat
prescription one.

The reply says the thing was never in the answer and hands back the stretch of it that still
stands, so the person can go on from there without reading the paragraph again.

This module only reads: the choosing helper and the shrug list it avoids live in
`bot/compose/fallback.py` and are used here as they are, with no change to them.
"""
import re

from .fallback import PUNT, _choose
# A clause with the thing left out is not a thing to take out of the answer: "nothing works",
# "nothing helps" and "nothing changes" name no object at all, and the verb after "nothing" is
# not one. The engine already knows which words those are (it reads a limit as the whole line
# first), so the list lives there rather than being written out a second time here.
from ..understanding.kinds import names_a_claim


# A rejection of something the answer never offered.
#
# "not a series" after three films, "not the chemical stuff" after bicarbonate of soda,
# "i dont like the gym" after an answer about half a plate of vegetables: the person is
# steering, and what they have just ruled out was never in the answer. What those lines got
# was the flat echo ("Got it - not another app", "Got it - you don't like the gym") or
# "Got it. Is there anything you'd like a hand with?", which leaves the person holding nothing
# and reads as if the bot had not listened to itself. The honest reply says the thing was
# never in the answer and hands back the stretch of it that still stands, so the person can
# go on from there without reading the whole paragraph again.
#
# It reads only a line that is nothing but the rejection (a fragment, or a short "i dont like
# the X"), and only when the answer above never mentions the thing: when the answer does
# mention it, the answer is what has to change, and that belongs to the entry that gave it.
RULED_OUT = (
    # "not a series", "not the chemical stuff", "without a car": the thing comes with its own
    # determiner, so it reads as a thing and not as an adjective.
    (re.compile(r"^(?:and\s+|but\s+)?not\s+(?P<thing>(?:a|an|any|the)\s+[a-z][a-z' ]{0,24})$"),
     True),
    # "not mothballs", "not too much salt": no determiner to keep. A bare "not <word>" is a thing
    # only when it is a plural or a "-related" tail, because "not sure" and "not really" are the
    # person hedging and there is no thing in them to leave out.
    (re.compile(r"^(?:and\s+|but\s+)?not\s+(?P<thing>[a-z][a-z' ]{0,20}s)$"), False),
    (re.compile(r"^(?:and\s+|but\s+)?not\s+(?P<thing>[a-z][a-z' ]{0,20}\s+related)$"), False),
    (re.compile(r"^(?:and\s+|but\s+)?not\s+(?:too|much)\s+(?P<thing>[a-z][a-z' ]{1,20})$"),
     False),
    # "nothing golf related", "nothing with violence". "nothing too sad" is read as a softening
    # of the ask rather than a thing to leave out, so "too" and "very" claim nothing.
    (re.compile(r"^(?:and\s+|but\s+)?nothing\s+(?P<thing>[a-z][a-z' ]{1,24})$"), False),
    # "i dont want trouble", "i dont want hassle": the mass nouns take no determiner, so the
    # pattern below missed them and the person got the flat echo back. Any other bare noun is not
    # read here, because "i dont want sugar" is a thing to leave out of a recipe and the entries
    # answer it.
    (re.compile(r"^(?:and\s+|but\s+)?(?:i|we)\s+(?:really\s+|just\s+|actually\s+|personally\s+)?"
                r"(?:dont|don't|do\s+not|didnt|did\s+not|never)\s+want\s+"
                r"(?P<thing>trouble|hassle|aggro|drama|upset|bother)$"), False),
    # "i dont want to fall out with them", "i dont want to argue about it": the trouble is a verb
    # here, and it is the same thing - how the advice is to be done.
    (re.compile(r"^(?:and\s+|but\s+)?(?:i|we)\s+(?:really\s+|just\s+|actually\s+|personally\s+)?"
                r"(?:dont|don't|do\s+not|didnt|did\s+not|never)\s+want\s+to\s+"
                r"(?P<thing>(?:fall\s+out|falling\s+out|argue|fight|quarrel|kick\s+up\s+a\s+fuss|"
                r"make\s+a\s+fuss|get\s+into\s+it))$"),
     False),
    # "i dont like the gym", "we dont have any equipment": a standing preference or lack.
    (re.compile(r"^(?:and\s+|but\s+)?(?:i|we)\s+(?:really\s+|just\s+|actually\s+|personally\s+)?"
                r"(?:dont|don't|do\s+not|didnt|did\s+not|never)\s+"
                r"(?:like|want|have|own|use|need|rate|fancy)\s+"
                r"(?P<thing>(?:a|an|any|the|my|another)\s+[a-z][a-z' ]{0,24})$"), True),
    # "it's not the trap", "its not my shoes", "that isn't the valve": the commonest way a
    # person steers the answer they have just read, and it was read nowhere - the line went back
    # as a nod ("Got it - it's not the trap") or, when nothing else claimed it, the answer was
    # handed over again word for word. The subject of "not" is the answer, not a topic.
    (re.compile(r"^(?:and\s+|but\s+|no,?\s+|nah,?\s+)?(?:it|that|this)(?:'s|s)?\s+"
                r"(?:is\s+not|isnt|isn't|not)\s+"
                r"(?P<thing>(?:a|an|any|the|my|another)\s+[a-z][a-z' ]{0,24})$"), True),
    (re.compile(r"^(?:and\s+|but\s+|no,?\s+|nah,?\s+)?(?:it|that|this)(?:'s|s)?\s+"
                r"(?:is\s+not|isnt|isn't|not)\s+(?P<thing>[a-z][a-z' ]{1,20}s)$"), False),
)
# Words that carry no thing of their own, and a tail that turns a thing into an adjective
# ("nothing golf related" leaves out golf). A clause is not a thing: "nothing that needs much
# water" rules out a plant, not the word "needs".
RULED_OUT_WORDS = frozenset(("thing", "things", "anything", "something", "that", "this",
                             "which", "what", "any", "more", "much", "needs", "need", "uses",
                             "use", "takes", "take", "gets", "get", "has", "have", "requires",
                             "require", "wants", "want", "please", "thanks", "really", "very"))
# A quality is not a thing to leave out: "nothing bad has happened" and "nothing too sad" are
# about how the day is, and "there's no bad in that answer" answers nothing.
RULED_OUT_QUALITY = frozenset((
    "bad", "good", "sad", "happy", "awful", "terrible", "horrible", "weird", "wrong", "fine",
    "ok", "okay", "sure", "nice", "lovely", "great", "better", "worse", "best", "worst",
    "big", "small", "little", "long", "short", "new", "old", "easy", "hard", "difficult",
    "expensive", "cheap", "different", "same", "busy", "tired", "stressed", "ill", "sick",
))
# Words that are not a thing to leave out even though they look like one. "it's not the case",
# "that's not the point", "it's not the problem": the subject is the answer itself, and handing
# back "nothing there was about the case" says nothing. A line that names one of these is left to
# the module that answered it.
RULED_OUT_NOT_A_THING = frozenset((
    "case", "point", "problem", "issue", "fact", "joke", "idea", "whole", "kind", "sort",
    "type", "way", "matter", "question", "answer", "reason", "truth", "deal", "end",
    # A word that turns the phrase after "not" into a remark about how things are rather than a
    # thing to leave out: "nothing yet", "not much either", "not well thanks", "nothing is going
    # right". Each of those was read as a thing - "There's no yet in that answer" - so a phrase
    # with one of these words in it names nothing.
    "yet", "either", "though", "well", "thanks", "is", "are", "was", "were", "be", "been",
    "going", "happening", "happened", "here", "there", "now", "ever", "again", "else", "right",
    "left", "much", "more", "less", "least", "still", "even", "already", "quite", "rather",
    "able", "possible", "worth", "enough", "true", "false", "sure", "wrong", "fine",
))
RULED_OUT_TAIL = re.compile(r"\s+(?:related|based|ish|esque)$")
RULED_OUT_PREP = re.compile(r"\s+(?:of|to|on|for|by|from|about)\s+")
RULED_OUT_OPENS_WITH = re.compile(r"^(?:with|without|in|on|at|for|about|of|to)\b")
RULED_OUT_SOFTENING = re.compile(r"^(?:and\s+|but\s+)?nothing\s+(?:too|very|that|which|of)\b")
# "with" and "without" stay in the phrase: "nothing with violence" is about violence, and a
# thing that keeps its own preposition is not one to build a sentence round.
RULED_OUT_KEEPS = re.compile(r"^(?:a|an|any|the|my|another)\s+")
RULED_OUT_REPLIES_PLAIN = (
    "There's no {thing} in that answer, so it still stands. {opening}",
    "That one never mentions {thing} at all, so nothing changes. {opening}",
    "Nothing there was about {thing}, so the answer holds. {opening}",
)
RULED_OUT_REPLIES_THE = (
    "None of that was {thing} - the answer still stands. {opening}",
    "That one never mentions {thing} at all, so nothing changes. {opening}",
    "Nothing there was {thing}, so the answer holds. {opening}",
)
# Trouble between two people is not a thing in the answer. "i dont want a row", "i dont want a
# fuss", "i dont want a falling out" arrive after advice to knock on a neighbour's door, and they
# steer nothing: they put a condition on how the advice is to be done. The `i dont like/want/have`
# pattern claimed them as a thing ruled out, the answer above never said "row", so the reply led
# with a sentence about the answer itself - "That one never mentions a row at all, so nothing
# changes" - which is the bot describing its own paragraph to somebody who has just said they want
# a quiet word. The advice is still what they asked for, so it is handed back with a plain yes to
# the condition in front of it.
A_ROW_BETWEEN_PEOPLE = frozenset((
    "row", "fuss", "scene", "argument", "argy bargy", "argie bargie", "fight", "drama",
    "falling out", "fall out", "confrontation", "trouble", "hassle", "aggro", "upset",
    "bad feeling", "bad blood", "stink", "carry on", "atmosphere",
))
# What the row is called when it is handed back: "i dont want to fall out with them" reads as
# "no falling out wanted", not "no fall out with them wanted".
A_ROW_NAMES = {
    "fall out": "falling out", "falling out": "falling out", "argue": "argument",
    "quarrel": "argument", "get into it": "argument", "fight": "fight",
    "kick up a fuss": "fuss", "make a fuss": "fuss", "row": "row", "trouble": "trouble",
    "hassle": "hassle", "bother": "bother", "aggro": "aggro", "drama": "drama", "upset": "upset",
}
RULED_OUT_REPLIES_A_ROW = (
    "Fair enough - no {thing} needed. {opening}",
    "Quite right, no {thing} wanted. {opening}",
    "Fair enough: one calm sentence, no {thing}. {opening}",
)
# A category is not a thing. "not tablets" against an answer that offers paracetamol and
# ibuprofen, "not a series" against one that names *Happy Valley*, "not a thriller" against a
# murder mystery: the answer's own suggestion is an instance of what was ruled out, and no word
# test can see that from the line alone. The class is a fact about the *answer*, so it is read
# there: the module stands down only when the answer names the class or one of its members, and
# then the entry that gave the answer is what has to change. Standing down on the word alone made
# the module a no-op for the very lines it was built for - `not tablets` after a sleep answer the
# person is right about.
RULED_OUT_CLASS = frozenset((
    "tablets", "pills", "painkillers", "painkiller", "medication", "medicine", "medicines",
    "drugs", "antibiotics", "supplements", "vitamins", "inhalers", "creams", "series",
    "episodes", "thriller", "thrillers", "horror", "comedies", "documentaries", "meat",
    "dairy", "gluten", "carbs", "carbohydrates", "sugar", "chemicals", "screens", "toys",
))
# The members of those classes an answer might name instead: "not tablets" against paracetamol,
# "not a thriller" against a murder mystery, "not the chemical stuff" against vinegar.
RULED_OUT_INSTANCES = {
    "tablets": frozenset(("paracetamol", "ibuprofen", "aspirin", "codeine", "antihistamine",
                          "melatonin", "sertraline", "tablet", "pill", "painkiller", "dose")),
    "pills": frozenset(("paracetamol", "ibuprofen", "aspirin", "codeine", "antihistamine",
                        "melatonin", "pill", "tablet", "painkiller")),
    "painkillers": frozenset(("paracetamol", "ibuprofen", "aspirin", "codeine", "painkiller")),
    "painkiller": frozenset(("paracetamol", "ibuprofen", "aspirin", "codeine", "painkiller")),
    "medication": frozenset(("paracetamol", "ibuprofen", "tablet", "pill", "dose", "prescription")),
    "medicine": frozenset(("paracetamol", "ibuprofen", "tablet", "pill", "dose")),
    "medicines": frozenset(("paracetamol", "ibuprofen", "tablet", "pill", "dose")),
    "drugs": frozenset(("paracetamol", "ibuprofen", "antibiotic", "painkiller", "tablet")),
    "antibiotics": frozenset(("antibiotic", "penicillin", "amoxicillin")),
    "supplements": frozenset(("supplement", "vitamin", "iron", "magnesium", "omega")),
    "vitamins": frozenset(("vitamin", "supplement", "iron", "magnesium", "omega")),
    "creams": frozenset(("cream", "ointment", "lotion", "gel")),
    # An answer that offers films is not something a person ruling out series has ruled out: the
    # class was never in it, so there is nothing to hand back and nothing to say.
    "series": frozenset(("series", "episode", "episodes", "season", "seasons", "film", "films",
                         "movie", "movies")),
    "episodes": frozenset(("episode", "series", "season", "film", "films", "movie", "movies")),
    "thriller": frozenset(("thriller", "murder", "mystery", "crime", "detective", "suspense",
                           "serial", "killer")),
    "thrillers": frozenset(("thriller", "murder", "mystery", "crime", "detective", "suspense",
                            "serial", "killer")),
    "horror": frozenset(("horror", "scary", "ghost", "haunted", "frightening")),
    "meat": frozenset(("meat", "chicken", "beef", "pork", "lamb", "bacon", "sausage", "mince",
                       "steak", "ham", "turkey")),
    "dairy": frozenset(("dairy", "milk", "cheese", "butter", "cream", "yoghurt", "yogurt")),
    "gluten": frozenset(("gluten", "bread", "pasta", "flour", "wheat", "couscous", "barley")),
    "carbs": frozenset(("rice", "pasta", "bread", "potato", "potatoes", "flour")),
    "carbohydrates": frozenset(("rice", "pasta", "bread", "potato", "potatoes", "flour")),
    "sugar": frozenset(("sugar", "honey", "syrup", "sweetener", "jam")),
    "chemicals": frozenset(("vinegar", "bleach", "ammonia", "caustic", "solvent", "spray",
                            "bicarbonate")),
    "screens": frozenset(("screen", "phone", "television", "tv", "laptop", "monitor", "tablet")),
    "toys": frozenset(("toy", "lego", "blocks", "play")),
}


# A pick the answer names rather than describes: the bot's own answers write their suggestions
# in asterisks (*Groundhog Day*), and a line of them is a line of titles. Only the marks that
# cannot be punctuation are read, because an apostrophe would pair across a sentence.
RULED_OUT_NAMED = re.compile(r"\*[^*]{2,}\*|\"[^\"]{2,}\"|\u201c[^\u201d]{2,}\u201d")


def _named_picks(answer):
    """True when the answer offers two or more named things rather than describing them."""
    return len(RULED_OUT_NAMED.findall(str(answer or ""))) > 1


def _class_of(word):
    """The classes a ruled-out word belongs to, read from the word itself.

    One spelling is not one class. "not the chemical stuff" is the same class as "not chemicals"
    with a different ending, and "not a film" is a member of the class the watching answer offers
    as "series"/"episodes" - the answer's own suggestions are the instances, so the line names one
    of them rather than the class.
    """
    word = word.strip("'")
    if not word:
        return frozenset()
    forms = {word, word + "s"}
    if word.endswith("es"):
        forms.add(word[:-2])
    if word.endswith("s"):
        forms.add(word[:-1])
    classes = {form for form in forms if form in RULED_OUT_CLASS}
    # A class said with a different ending, where the stem is long enough to be the word.
    if not classes:
        stem = word[:7]
        if len(stem) >= 6:
            classes = {key for key in RULED_OUT_CLASS if key.startswith(stem)}
    # A member stands for its class too, but only when the word is not a class of its own: "not
    # milk" is the dairy answer and "not a film" is what the watching answer gives, while "not
    # tablets" is the pills and not the screens the sleep answer mentions.
    if not classes:
        for key, members in RULED_OUT_INSTANCES.items():
            if forms & members:
                classes.add(key)
    return frozenset(classes)


def _a_class_word(word):
    """True when the word is one of the class names itself, in any spelling."""
    forms = {word, word + "s"}
    if word.endswith("es"):
        forms.add(word[:-2])
    if word.endswith("s"):
        forms.add(word[:-1])
    if forms & RULED_OUT_CLASS:
        return True
    stem = word[:7]
    return len(stem) >= 6 and any(key.startswith(stem) for key in RULED_OUT_CLASS)


def _an_answer_of_that_class(answer, thing):
    """True when the answer names the ruled-out class or one of its members.

    "not tablets" against an answer that says paracetamol, "not a thriller" against a murder
    mystery: the answer's own suggestion is an instance of what was ruled out, and saying "that
    one never mentions tablets at all" while handing two of them back reads as not listening.
    """
    said = set(re.findall(r"[a-z']+", str(answer or "").lower()))
    for word in RULED_OUT_KEEPS.sub("", thing).split():
        classes = _class_of(word)
        for key in classes:
            forms = {key, key + "s"}
            if key.endswith("s"):
                forms.add(key[:-1])
            if forms & said:
                return True
            if RULED_OUT_INSTANCES.get(key, frozenset()) & said:
                return True
            # A class said in the answer with a different ending ("chemical stuff" for
            # "chemicals") is the same class: compare the stem, long enough here to be the word.
            stem = key[:7]
            if len(stem) >= 6 and any(said_word.startswith(stem) for said_word in said):
                return True
        # A *member* ruled out of an answer that offers named picks: the answer hands over titles
        # and never says what they are, so "none of that was a film" would be the bot claiming
        # knowledge it does not have ("Groundhog Day" is one). Only for a member: "not a series"
        # over a list of films is a true claim, because a film is not a series, and it says so.
        if classes and not _a_class_word(word) and _named_picks(answer):
            return True
    return False


# An answer that is an emergency answer or a sympathy answer is not one to trim down to its
# first sentence and hand back: "sit and stay still until the ambulance arrives" and "don't
# drive yourself" are the answer, and a grieving person is not told that nothing has changed.
RULED_OUT_KEEP_WHOLE = re.compile(
    r"\b(?:999|911|112|111|ambulance|a&e|casualty|emergency|urgent care|999 line)\b")
RULED_OUT_SYMPATHY = re.compile(
    r"\b(?:sorry|sad news|passed away|grief|grieving|bereave\w*|condolence\w*|"
    r"miss (?:him|her|them))\b")

# Where a long answer stops being a reminder. Short enough to read at a glance, long enough to
# carry a step: the paste, the plate, the three picks.
RULED_OUT_OPENING = 120
# A short answer is handed back whole. Cutting a 160-character emergency answer to its first
# sentence drops the part that keeps the person still; nothing is gained by the trim.
RULED_OUT_WHOLE = 210


# The manners a line ends on are not part of the thing. "not horror pls" was read as a thing
# called "horror pls", and the answer came back "Nothing there was about horror pls, so the answer
# holds." - the bot quoting the person's politeness back at them. People type the shortening
# (`pls`, `plz`, `thx`, `ta`) as often as the word, and a rule-out is exactly the line they are
# being polite about.
MANNERS = re.compile(r"(?:[\s,!.?]*\b(?:pls+|plz|please|pleas|plse|thx|thanx|thanks|thankyou|"
                     r"thank\s+you|ta|ty|cheers|cheerio|mate|m8|fella|buddy|bud|pal|x|xx|xxx)"
                     r"\b)+[\s,!.?]*$")


def _without_the_manners(clean):
    """The line with the politeness it ends on taken off."""
    return MANNERS.sub("", str(clean or "")).strip()


# The ask for the other option, after the thing that is being ruled out: "not curry, something
# else", "no pasta then, what else is there", "not a series - anything else?". The rejection is
# still a rejection, and the asking for the other one is the person expecting the answer to
# change - but the whole line is too long for the thing patterns and carries an ask beside the
# thing, so `not curry, something else` was read as a *request* for curry and the curry came back
# (main `317ee63`). The tail is taken off before the thing is read, and the answer then says curry
# was never in it and hands back what still stands.
RULED_OUT_THEN_ELSE = re.compile(
    r"[\s,;:-]+(?:then\s+|and\s+)?(?:so\s+)?(?:what|anything|something)\s+else"
    r"(?:\s+[a-z']+){0,4}\s*[.?!]*$")
# "no curry", "nah, not the pasta": a bare "no <word>" is usually nothing to do with the answer
# ("no idea", "no worries", "no thanks"), so it is only read when the person has just asked for the
# other option, which is what rules those out.
# "not curry, something else": the same ask, with a bare singular noun that the bare "not"
# patterns refuse ("not sure", "not really" have no thing in them). Asking for the other option is
# what makes it a thing.
RULED_OUT_NOT_THEN_ELSE = (
    (re.compile(r"^(?:and\s+|but\s+)?not\s+(?P<thing>(?:a|an|any|the)\s+[a-z][a-z' ]{0,24})$"),
     True),
    (re.compile(r"^(?:and\s+|but\s+)?not\s+(?P<thing>[a-z][a-z' ]{1,24})$"), False),
)
RULED_OUT_NO_THEN_ELSE = (
    (re.compile(r"^(?:no|nah|nope|no,|nah,|nope,)\s+(?P<thing>(?:a|an|any|the)\s+[a-z][a-z' ]{0,24})$"),
     True),
    (re.compile(r"^(?:no|nah|nope|no,|nah,|nope,)\s+(?P<thing>[a-z][a-z' ]{1,24})$"), False),
)


def _ruled_out_thing(clean):
    """The thing a line rules out, in the person's own words, and whether it kept its "a"/"the"."""
    clean = _without_the_manners(clean)
    asked_for_the_other = bool(RULED_OUT_THEN_ELSE.search(clean))
    if asked_for_the_other:
        clean = RULED_OUT_THEN_ELSE.sub("", clean).strip(" ,;:-")
    if not clean or len(clean.split()) > 7:
        return "", False
    # "nothing too sad" softens the ask rather than leaving something out, and "nothing with
    # violence" leaves out a phrase that carries its own preposition: neither builds a sentence.
    if RULED_OUT_SOFTENING.match(clean):
        return "", False
    thing, kept = "", False
    patterns = RULED_OUT + ((RULED_OUT_NOT_THEN_ELSE + RULED_OUT_NO_THEN_ELSE)
                            if asked_for_the_other else ())
    for pattern, with_determiner in patterns:
        found = pattern.match(clean)
        if found:
            thing, kept = found.group("thing"), with_determiner
            break
    else:
        return "", False
    thing = " ".join(word for word in thing.split() if word not in RULED_OUT_WORDS)
    thing = RULED_OUT_TAIL.sub("", thing).strip(" .,!?'\"")
    if not thing or RULED_OUT_PREP.search(thing) or RULED_OUT_OPENS_WITH.search(thing):
        return "", False
    # A quality anywhere in the thing ("not a bad idea", "not the old slow one") is an opinion
    # about something, not a thing left out. Only the ends were read before, so `not a bad idea`
    # was claimed and answered with "nothing there was a bad idea".
    if any(word in RULED_OUT_QUALITY for word in thing.split()):
        return "", False
    if any(word in RULED_OUT_NOT_A_THING for word in thing.split()):
        return "", False
    # A claim anywhere in the tail is a sentence about how things are, not something to hand back
    # out of the answer: "nothing works" and "nothing helps" put it last, and "nothing feels fun
    # any more" puts it first - that one was answered with "There's no feels fun any more in that
    # answer, so it still stands", a verb phrase in a slot written for a thing.
    if clean.startswith("nothing") and any(names_a_claim(word) for word in thing.split()):
        return "", False
    kept = bool(kept and RULED_OUT_KEEPS.match(thing))
    words = thing.split()
    if len(words) > 4 or not all(word.isalpha() for word in words):
        return "", False
    return thing, kept


# A particle carries no thing, and one of them appearing anywhere in the answer is not the answer
# naming the thing. "i dont want a falling out" splits into `falling` and `out`, and every answer
# about a neighbour says "sort it out" or "fall out over it", so the answer read as already naming
# it and the module stood down - the person got the flat echo ("Got it - you don't want a falling
# out") instead of the advice. A thing made only of particles is still matched on them.
RULED_OUT_PARTICLES = frozenset("""out off up down away back over through around about along
together home here there it self selves""".split())


def _a_row_thing(thing):
    """The row in a ruled-out thing, or "" - trouble between people is how, not what."""
    bare = RULED_OUT_KEEPS.sub("", " ".join(str(thing or "").split()))
    if bare in A_ROW_NAMES:
        return A_ROW_NAMES[bare]
    for phrase in sorted(A_ROW_NAMES, key=len, reverse=True):
        if bare == phrase or bare.startswith(phrase + " "):
            return A_ROW_NAMES[phrase]
    return ""


def _names_it(answer, thing):
    """True when an answer already names the thing, in any form it might be written in."""
    said = set(re.findall(r"[a-z']+", answer.lower()))
    words = RULED_OUT_KEEPS.sub("", thing).split()
    carrying = [word for word in words if word not in RULED_OUT_PARTICLES]
    if carrying:
        words = carrying
    for word in words:
        forms = {word, word + "s", word + "es", word + "ing", word + "ed"}
        if word.endswith("s"):
            forms.add(word[:-1])
        if word.endswith("es"):
            forms.add(word[:-2])
        if forms & said:
            return True
    return False


# The openings of a line that was a sympathy, a nod or a question back rather than an answer.
RULED_OUT_NO_ANSWER = ("sorry", "that sounds", "sounds like", "i'm listening", "i am listening",
                       "got it", "thanks for telling", "no worries", "of course", "noted",
                       "fair enough", "that's rough", "thats rough")


def _the_whole_answer(memory):
    """The bot's last line when it was an answer, not a nod, a question back or a shrug."""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return ""
    last = " ".join(str(turns[-1].get("bot") or "").split())
    if len(last) < 60 or last.endswith("?"):
        return ""
    # A shrug is not an answer to stand behind: handing back "that's beyond what I know well"
    # after "nothing that needs much water" tells the person nothing and takes the turn from
    # the entry that did have something.
    if any(punt in last.lower() for punt in PUNT):
        return ""
    # Nor is a line that answered a feeling: "im feeling flat lately" / "nothing bad has
    # happened" is the person carrying on about how they are, and the reply to it is not a
    # statement that some answer of mine still stands.
    if last.lower().startswith(RULED_OUT_NO_ANSWER):
        return ""
    # An emergency or a sympathy answer is not a paragraph to hand back a stretch of. What
    # stands in it is what keeps somebody safe, and "nothing changes" is not the reply to grief.
    if RULED_OUT_KEEP_WHOLE.search(last.lower()) or RULED_OUT_SYMPATHY.search(last.lower()):
        return ""
    return last


def _the_standing_part(answer):
    """The stretch of an answer worth handing back: its first step, not the whole paragraph.

    A short answer is handed back whole, because in a short answer every sentence is doing work
    ("and don't drive yourself" is the second one). A longer one keeps its first step: the
    lead-in is dropped ("If you want something easy and good tonight: *Groundhog Day*..."),
    because a lead-in hands nothing back, and then the first clause long enough to carry a step.
    "" when there is nothing short enough to be a reminder.
    """
    # A short answer is handed back whole: in a short answer every sentence is doing work ("and
    # don't drive yourself" is the second one), and the trim costs more than it saves.
    if len(answer) <= RULED_OUT_WHOLE:
        return " ".join(answer.split())
    first = re.split(r"(?<=[.!?])\s", answer.strip())[0]
    head, _, tail = first.partition(":")
    if tail and len(head.split()) <= 8:
        first = tail
    first = " ".join(first.split())
    if len(first) <= RULED_OUT_OPENING:
        return first
    cut = first[:RULED_OUT_OPENING]
    stretches = [cut[:cut.rfind(mark)].strip(" ,;:-")
                 for mark in ("; ", ", ", " - ", " and ") if mark in cut]
    stretches = [stretch for stretch in stretches if len(stretch.split()) >= 4]
    if not stretches:
        return ""
    return max(stretches, key=len)


# "nothing works", "none of that worked", "nothing has helped": the person is not ruling
# something out of the answer, they are saying the answer's steps did not take. What they need is
# the next part of that answer, which the answer itself holds - "my laptop wont turn on" /
# "nothing works" left the power-button advice behind, and the very same answer goes on "if there
# is no light on the charger at all, try another socket and cable; if the charger lights up but the
# laptop is still dead, the battery or the power board is the likely fault". A claim names no
# object, so the rule-out rightly stands down; what was missing is the other half, that a claim is
# a report about the answer and the answer's later step is the reply.
CLAIM_OF_FAILURE = re.compile(
    r"^\W*(?:(?:ok|okay|so|well|yeah|yep|yes|and|but|oh|right|alright|no|nope|nah|still|now)\W+)*"
    r"(?:nothing|nowt|none\s+of\s+(?:it|that|them|these|those)|neither\s+of\s+(?:them|those|it))"
    r"(?:\s+\w+){0,5}\W*$")
# The small words a claim carries besides its verb. Everything else in the line has to be the
# verb of a clause with its object left out (`names_a_claim`), which is what keeps "nothing works
# better than a hot wash" - a recommendation, not a report - out of this shape.
CLAIM_SMALL = frozenset("""at all so far yet again now still really just about on with me my it
this that them those these any more much either the a an of in for to day days week weeks moment
while times time one bit lot lots out up down been has have had is was are were am do does did""".split())
# Every lead ends on a colon, because the step is a sentence of its own ("If there is no light on
# the charger at all, try another socket and cable") and "Then Give it two weeks" is two sentences
# run together.
CLAIM_LEADS = ("Then it is the next part that matters: {step}",
               "Then take it a step further: {step}",
               "Then the next step: {step}",
               "Next: {step}")
# A step that opens on a condition reads after "Then" as two sentences run together ("Then If
# there is no light on the charger at all ..."), so it gets the leads that end on a colon.
CLAIM_CONDITION = re.compile(r"^(?:if|when|once|unless|before|after|until)\b", re.I)
# Who the answer sends them to, listed in `repeat` for the same reason.
STEP_ELSEWHERE = re.compile(r"\b(?:gp|doctor|nurse|pharmacist|chemist|dentist|vet|optician|midwife|"
                            r"health visitor|111|999|911|helpline|a&e|hospital|council|"
                            r"citizens advice|plumber|electrician|engineer|gas safe|mechanic|"
                            r"locksmith|roofer|builder|technician|specialist|repair shop)\b", re.I)
CLAIM_LEADS_IF = ("The next thing to try: {step}", "Next: {step}",
                  "Then the next check: {step}")


def _a_claim_of_failure(clean, memory):
    """The next part of the answer, for a line that says the answer's steps did not take."""
    if not CLAIM_OF_FAILURE.match(clean):
        return ""
    words = re.findall(r"[a-z']+", clean)
    while words and words[0] in ("nothing", "nowt", "none", "neither", "of", "ok", "okay",
                                 "so", "well", "yeah", "yep", "yes", "and", "but", "oh",
                                 "right", "alright", "no", "nope", "nah", "still", "now"):
        words.pop(0)
    if not words or not any(names_a_claim(word) for word in words):
        return ""
    if any(word not in CLAIM_SMALL and not names_a_claim(word) for word in words):
        return ""
    answer = _the_whole_answer(memory)
    if not answer:
        return ""
    # An answer that ends on a question is mid-conversation: the bot asked something ("what does a
    # hard day look like just now?") and "nothing seems to work" is the person answering it, so
    # there is no step to hand back and the card that asked goes on with the conversation.
    if answer.rstrip().endswith("?"):
        return ""
    try:
        # The answer holds the step that comes after the one that did not work, and it is the
        # same reading `repeat` uses for "ive tried the plunger already".
        from ..memory.repeat import _later_part
        step = " ".join(str(_later_part(clean, answer) or "").split())
    except Exception:  # noqa: BLE001 - a reading that fails leaves the line to the entries
        return ""
    if len(step.split()) < 4 or not step:
        return ""
    # What comes back has to be the answer going further, not the same advice said again. An
    # answer marks that step itself: it opens on a condition ("If there is no light on the charger
    # at all ...", "If it is still there after that, see a GP") or it sends the person to somebody
    # (the same `NEXT_STEP` list `repeat` reads for "ive tried the plunger already"). Without one
    # of those the handed-back part is the advice the person has just said did not work - "im so
    # tired all the time" / "nothing seems to work" would get "Give it two weeks of the basics"
    # back - and the card that asked them about their day does better, so this stands down.
    conditional = bool(CLAIM_CONDITION.match(step))
    if not conditional and not STEP_ELSEWHERE.search(step):
        return ""
    step = step[:1].upper() + step[1:]
    pool = CLAIM_LEADS_IF if conditional else CLAIM_LEADS
    return _choose([line.format(step=step) for line in pool], memory or {}, clean)


# An animal a person turns down after an answer about an animal is a decision, not a steer about
# an option in the answer. "she wants a puppy" gets the kit list, and the kit list never says
# "dog", so "i dont want a dog" was read as ruling out something the answer never offered and the
# same kit was handed back - "Nothing there was a dog, so the answer holds. A bed, two bowls, a
# crate or pen..." - to a person who has just said no to it. Two animals in a row is a pet
# decision, and a decision against one is the refusal the memory lane answers ("Right - no dog.").
PET_NAMED = re.compile(
    r"\b(?:dog|dogs|puppy|puppies|pup|pups|cat|cats|kitten|kittens|rabbit|rabbits|bunny|"
    r"bunnies|hamster|hamsters|gerbil|gerbils|guinea pig|guinea pigs|parrot|parrots|budgie|"
    r"budgies|bird|birds|horse|horses|pony|ponies|fish|goldfish|tortoise|tortoises|snake|"
    r"snakes|lizard|lizards|ferret|ferrets|pet|pets)\b")

# The answer a want gets is what having one takes, so the animal it is about is named in the
# question rather than in the answer: "she wants a puppy" -> "For a puppy: a bed, two bowls...".
WANTED_ONE = re.compile(
    r"\b(?:want|wants|wanted|would like|'d like|after|thinking (?:of|about)|considering|"
    r"planning to get|should (?:i|we) get|can (?:i|we) get|shall we get|get (?:a|an)|"
    r"getting (?:a|an)|looking at getting)\b")


def _a_pet_turned_down(clean, memory):
    """True when the line turns down an animal the line above asked about getting one of."""
    if not PET_NAMED.search(clean):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for turn in reversed(turns[-2:]):
        before = " ".join(str(turn.get("user") or "").split()).lower()
        if before:
            return bool(PET_NAMED.search(before) and WANTED_ONE.search(before))
    return False


# A recommendation is a list of things of a kind, and "not a horror" after one is a person asking
# for the same list without that kind - not saying the list failed them. This module's line ("that
# one never mentions a horror at all, so nothing changes") is true and useless: the answer named
# *Groundhog Day* and *Knives Out*, and the thing wanted is something else. A pair of titles in the
# answer is the sign the list can be swapped, so that is what stands the module down and lets the
# entertainment rows answer with the list they already know how to narrow.
TITLES_IN_ANSWER = re.compile(r"\*[^*]{2,60}\*")
# The kinds a list can be narrowed by. Each one here is a kind the pick actually answers with a
# list of its own: ruling it out is a fresh pick, so this module stands down and the entertainment
# rows hand back the list without it. A kind the pick has nothing for ("cartoon", "drama",
# "fantasy") is not in here - standing down would leave the turn to a shrug, and the true-but-plain
# line this module writes is the better answer. `tests.test_a_kind_ruled_out_is_swapped` runs every
# kind below through the pick, so a kind that stops answering takes itself out of this tuple.
KINDS_A_LIST_CAN_SWAP = ("horror", "scary", "frightening", "creepy", "comedy", "comedies",
                         "funny", "romance", "romantic", "sad", "documentary", "gory")


def _a_list_that_can_be_swapped(answer, thing):
    """True when the answer is a list of picks and the thing ruled out is the kind in it."""
    words = RULED_OUT_KEEPS.sub("", " ".join(str(thing or "").split())).split()
    if not any(word in KINDS_A_LIST_CAN_SWAP for word in words):
        return False
    return len(TITLES_IN_ANSWER.findall(answer)) >= 2


def _rules_out_what_i_never_said(text, memory):
    """The thing ruled out, whether it kept its "a"/"the", and the part that still stands."""
    clean = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    thing, kept = _ruled_out_thing(clean)
    if not thing:
        return "", False, ""
    if _a_pet_turned_down(clean, memory):
        return "", False, ""
    answer = _the_whole_answer(memory)
    if not answer or _names_it(answer, thing):
        return "", False, ""
    if _a_list_that_can_be_swapped(answer, thing):
        return "", False, ""
    if _an_answer_of_that_class(answer, thing):
        return "", False, ""
    opening = _the_standing_part(answer)
    if not opening or _names_it(opening, thing):
        return "", False, ""
    return (thing if kept else RULED_OUT_KEEPS.sub("", thing)), kept, opening


def _ruled_out_reply(memory, clean):
    """One line saying the thing just ruled out was never in the answer, and what still stands."""
    thing, kept, opening = _rules_out_what_i_never_said(clean, memory)
    if not thing:
        return ""
    opening = opening[:1].upper() + opening[1:]
    # A row between two people is how the advice is to be done, not a thing missing from it.
    row = _a_row_thing(thing)
    if row:
        return _choose([line.format(thing=row, opening=opening)
                        for line in RULED_OUT_REPLIES_A_ROW], memory, clean)
    pool = RULED_OUT_REPLIES_THE if kept else RULED_OUT_REPLIES_PLAIN
    # "There's no tablets" reads wrong, so a plural thing gets the two lines that fit either.
    if not kept and thing.split()[-1].endswith("s"):
        pool = RULED_OUT_REPLIES_PLAIN[1:]
    return _choose([line.format(thing=thing, opening=opening) for line in pool], memory, clean)




def reply_for(text, memory):
    """The rule-out answered against the answer above, or "" when this is not that shape."""
    try:
        clean = " ".join(str(text or "").lower().replace("\u2019", "'").split())
        # A claim that nothing worked is a report about the answer, not a thing left out of it.
        claim = _a_claim_of_failure(clean, memory)
        if claim:
            return claim
        return _ruled_out_reply(memory, clean)
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return ""


def takes_as_it_comes(text, memory):
    """Does this line steer the answer it followed? A hook is asked before the reply is made."""
    try:
        clean = " ".join(str(text or "").lower().replace("\u2019", "'").split())
        if _a_claim_of_failure(clean, memory):
            return True
        thing, _kept, _opening = _rules_out_what_i_never_said(text, memory)
        return bool(thing)
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False
