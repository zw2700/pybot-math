"""A fear of something, and how to get over it.

"how do i get over my fear of needles" was answered with what pins and needles are, "a fear of
spiders" with the silk glands, "a fear of flying" with the book-six-weeks-ahead fares, and "i
have a phobia of lifts" with "Noted: you have a phobia of lifts." Four phrasings, four different
wrong turns, and one shape underneath: the line names a thing the person is frightened of and
asks how to stop being frightened of it.

So this is one row, keyed on the fear itself rather than on any of the things people fear. The
thing named is quoted back in the first sentence - the reply is about *their* fear, not about
fear in general - and the method is the one with the evidence: graded exposure, a ladder of
small steps, breath rather than reassurance.

Two kinds of line are held out. A child's fear is a parent's question, and it is answered where
a child's fear lives (the dogs row, the dark at bedtime); a specific fear that already has its
own answer - the dentist, the doctor's needle - keeps that answer, because a dental appointment
needs the phone call in it, not a ladder.
"""

import re

from .lookup import entry

# The topic this domain answers, from bot/understanding/topics.py: a fear of something is a
# health ask, not a topic of its own, so the arbiter treats this file as a health specialist.
ANSWERS = ("health",)

# The fear itself: every way of saying "I am frightened of X" that people type.
FEAR = ("fear of", "fear off", "phobia", "phobias", "phobic of", "phobic about",
        "scared of", "scared about", "scared stiff", "afraid of", "terrified of",
        "terrified by", "frightened of", "dread", "dreads", "dreading", "petrified of",
        "hate flying", "hate spiders", "cant stand spiders", "panic when i", "panics when",
        "panic attack when", "panic attacks when", "get the fear",
        # the ask for the method, which people put first or last
        "get over", "getting over", "got over", "overcome", "overcoming", "cure my",
        "stop being scared", "stop being afraid", "not be scared", "less scared",
        "irrational fear", "irrational", "how do i stop being")

# The ask about the method, which a bare "fear of flying" (a statement) does not carry.
ASK = ("how do i", "how can i", "how to", "what can i do", "what should i do", "help",
       "get over", "getting over", "overcome", "overcoming", "cure", "stop", "deal with",
       "cope", "manage", "fix", "advice", "tips", "any tips", "any advice",
       "whats the best way", "what is the best way", "is there a way", "can i",
       "am i", "why am i", "what is wrong with me",
       # Telling someone "im scared of spiders" is the ask: the way people most often bring it
       # up is not "how do i get over", it is the declaration itself, and every one of these
       # was answered with the general worry card or the silk glands instead of with a method.
       "im scared of", "i am scared of", "im afraid of", "i am afraid of",
       "im terrified of", "i am terrified of", "im frightened of", "i am frightened of",
       "im petrified of", "i am petrified of", "im phobic of", "i am phobic of",
       "im phobic about", "i am phobic about")

# The thing being feared, taken out of the line so the reply can name it. Words are read one at
# a time after the marker rather than matched as a phrase, because the thing is one to three
# words of the person's own choosing ("the dark", "public speaking", "flying") and whatever
# follows it is the rest of their question.
#
# "dread" and "dreading" are in FEAR but not here, because dread names a thing somebody dislikes
# far more often than a phobia: "i dread monday mornings" was answered with a ladder to work up,
# in place of the "I don't blame you. What is it about it?" that was already right. A line with
# no marker names no thing, so the guard stands this row down and the old answer keeps it.
_MARKERS = ("fear of", "fear off", "phobia of", "phobia about", "phobic of", "phobic about",
            "scared of", "scared about", "afraid of", "terrified of", "terrified by",
            "frightened of", "petrified of", "phobia")
# The first word that is not part of the thing: an ask, a pronoun, a conjunction, a filler.
_STOP = frozenset((
    "i", "im", "i'm", "ive", "i've", "id", "and", "but", "so", "because", "cos", "when",
    "since", "what", "whats", "how", "can", "could", "should", "do", "does", "did", "help",
    "any", "is", "are", "was", "were", "it", "its", "my", "we", "he", "she", "they", "them",
    "that", "this", "never", "always", "really", "very", "too", "now", "please", "thanks",
    "thank", "need", "have", "has", "to", "will", "would", "am", "for", "if", "of", "get",
    "getting", "over", "overcome", "stop", "deal", "cope", "even", "just", "also", "about",
    "on", "at", "in", "with", "from", "there", "here", "as", "than", "then", "make", "makes"))

# What people put at the end of a line that says nothing about the thing: "im terrified of the
# mortgage tbh" was read as a fear of "the mortgage tbh" and answered "A fear of the mortgage tbh
# is learned", where main had the "what if" card for the worry itself. The trailing words are the
# person's voice and not the subject, so they are dropped once the thing has been read.
_TRAILING_FILLER = frozenset((
    "tbh", "tbf", "lol", "lols", "haha", "hah", "tho", "though", "rn", "atm", "idk",
    "nvm", "omg", "honestly", "actually", "basically", "kinda", "sorta", "mate", "pal",
    "thanks", "thank", "thx", "please", "xx", "x", "hey", "now", "still", "again"))


# The word that joins a doing to the thing it is done to: "going to the gym", "flying on a
# plane", "speaking in front of people". Read one word at a time, "going to the gym" stopped at
# the "to" in `_STOP` and the thing was quoted back as "going" - "A fear of going is learned" -
# a doing with the thing it is done to cut off.
_LINKS = frozenset(("to", "on", "in", "at", "into", "about", "with", "of", "near", "around",
                    "from", "inside"))
# The words that open the object of a doing, kept when the doing is being read: "going to my
# mum's", "scared of flying in the dark". They are stop words everywhere else.
_DETERMINERS = frozenset(("the", "a", "an", "my", "our", "your", "his", "her", "their",
                          "this", "that", "its"))


def _the_thing_they_fear(understood):
    """The feared thing as the person wrote it, or "" when the line names none."""
    said = " ".join(str((understood or {}).get("clean") or "").lower().split())
    found = ""
    at = -1
    for marker in _MARKERS:
        pos = said.find(" " + marker + " ")
        if pos < 0:
            if said.startswith(marker + " "):
                pos = -1
            else:
                continue
        if at < 0 or pos < at or (pos == at and len(marker) > len(found)):
            at = pos
            found = marker
    if not found:
        return ""
    rest = said[at + len(found) + 1:].strip()
    words = []
    doing = False  # the thing so far is a doing, so the thing it is done to is part of it
    for word in rest.split():
        word = word.strip(",.!?;:\"'")
        if not word:
            break
        if len(words) >= (5 if doing else 3):
            break
        if word in _STOP:
            if doing and (word in _LINKS or word in _DETERMINERS):
                # "going to the gym", "speaking up in meetings": the doing keeps the thing it is
                # done to, so the quote is a phrase somebody would say and not the bare verb.
                words.append(word)
                continue
            break
        words.append(word)
        if len(words) == 1 and word.endswith("ing") and len(word) > 4:
            doing = True
    if not words:
        return ""
    while words and words[-1] in _TRAILING_FILLER:
        words.pop()
    if not words:
        return ""
    while len(words) > 1 and words[-1] in ("to", "on", "in", "at", "into", "about", "with",
                                          "of", "near", "around", "from", "inside"):
        words.pop()  # a link with nothing after it is not part of a phrase
    thing = " ".join(words)
    if thing in ("the", "a", "an", "my", "it", "them", "that", "this"):
        return ""
    return thing


def _the_fear_reply(memory, understood):
    thing = _the_thing_they_fear(understood)
    opening = ("A fear of %s is learned, so it can be unlearned" % thing if thing
               else "A fear like that is learned, so it can be unlearned")
    return (opening + " in small steps: write a ladder from the easiest version of it to the "
            "hardest - a photo of it, then the smallest real version, then all of it - and "
            "only move up when the step you are on has stopped raising your heart. "
            "Pick the easiest rung and stay with it until the wave passes: leaving early is what "
            "teaches the fear that it was right. If it is limiting your life, ask the GP for CBT "
            "with exposure, which is the treatment with the best evidence.")


# A gerund after the marker names a situation far more often than a phobia - losing, failing,
# being sacked, moving house - and the ladder is the wrong help for a thing that is happening to
# somebody. The gerunds that really are phobias are the exceptions, and they are the classic
# ones: a fear of flying is a fear of flying.
_PHOBIA_GERUNDS = frozenset((
    "flying", "driving", "vomiting", "being sick", "travelling", "traveling", "sailing",
    "cruising", "going out", "speaking", "presenting", "dating", "eating", "sleeping",
    "swallowing", "choking", "blushing", "sweating"))
# Words that end in -ing and are not doings at all: a wedding and a ceiling are things, not
# situations, and a fear of a wedding is a date to get through rather than a situation to be
# lived. They are read as the thing they name.
_AN_ING_NOUN = frozenset((
    "wedding", "weddings", "building", "buildings", "ceiling", "ceilings", "string", "strings",
    "ring", "rings", "thing", "things", "evening", "evenings", "morning", "mornings",
    "pudding", "puddings", "filling", "icing", "sibling", "siblings", "offspring", "darling",
    "earring", "earrings", "duckling", "lightning", "clothing", "savings", "innings",
    "weddings", "meeting", "meetings"))


def _names_the_thing(understood):
    """Only a line that names what is feared: a bare "what is a phobia" is the definition card's.

    A definition of the word ("what is a phobia", "why am i scared all the time") is a different
    answer from "how do I stop being frightened of X", and one row cannot be both. This row takes
    the named thing and passes the rest, so the phobia card that explains the word keeps it.

    A gerund in that place is a situation and not a phobia, unless it is one of the classic
    ones, so "im scared of losing my job" keeps the redundancy advice and "how do i overcome my
    fear of failure at work" is still this row's line - `work` could not be in the avoid list to
    settle it, because that word takes the failure line with it.
    """
    thing = _the_thing_they_fear(understood)
    if not thing:
        return False
    # The word that decides it is the doing: "failing my driving test" and "losing my job" are
    # outcomes somebody is living through, and the answer with the errand in it is theirs. The
    # thing it is done to is part of the quote, not part of the test.
    first = thing.split()[0]
    if (first.endswith("ing") and len(first) > 4 and first not in _AN_ING_NOUN
            and first not in _PHOBIA_GERUNDS):
        return False
    return True


ENTRIES = [
    entry("fear-of-something", (FEAR, ASK), _the_fear_reply, guard=_names_the_thing,
          # A child's fear is asked by a parent, and the fear of a pet is a training question:
          # those lines have their own answers and this ladder is written for the person who is
          # frightened.
          avoid=("my son", "my daughter", "my child", "my kid", "my toddler", "my baby",
                 "my grandson", "my granddaughter", "4 year old", "5 year old", "3 year old",
                 "2 year old", "6 year old", "toddler", "puppy", "kitten",
                 # a pet frightened by a thing is the pets table's
                 "my dog", "my cat", "my rabbit", "my horse", "the dog", "the cat",
                 # a fear of dogs is the dog-training card, which already says the thing this
                 # ladder would say and says it with the dog in it: start further away than
                 # you think you need to, and let him take a treat from the floor.
                 "dog", "dogs", "a dog", "puppies",
                 # a fear of speaking in front of people has its own answer, and it is the
                 # better one here: rehearse the first sixty seconds until you could say it
                 # half asleep, because that is the part the nerves attack.
                 "public speaking", "presentation", "presentations", "presenting", "speech",
                 "speech in front", "talk in front", "talking in front", "speaking in front",
                 "stage fright", "interview", "interviews", "wedding speech", "best man speech",
                 # the everyday version of a fear of speaking: a standup, a meeting, saying one
                 # thing in a room. "speaking" is in _PHOBIA_GERUNDS, so the guard let
                 # "im terrified of speaking up in meetings" through and the ladder answered a
                 # line that had the first-ten-minutes tactics - say one thing early, use their
                 # name if you are talked over. The situation is named here instead.
                 "speaking up", "speak up", "spoke up", "talking in meetings",
                 "meetings", "meeting", "standup", "stand-up", "stand up", "in the room",
                 "say something in", "board meeting", "team meeting",
                 # the specific fears that already have the answer with the errand in it
                 "dentist", "dental", "hygienist", "doctor", "gp", "hospital appointment",
                 "blood test", "blood tests", "injection", "vaccine", "jab", "anaesthetic",
                 "surgery", "operation", "childbirth", "birth", "labour", "pregnancy",
                 "scan", "mri", "x ray", "xray", "chemo", "needle phobia is stopping me",
                 # a fear about money, a job or a Monday is a worry with an errand in it, not a
                 # phobia, and the answers that were there before this row are the better ones:
                 # "im scared of losing my job" had the redundancy advice (ask for the offer in
                 # writing, check the pay and the notice) and this ladder said "a fear of losing
                 # is learned". The thing named is a gerund - losing, failing, being sacked - and
                 # a gerund after the marker names a situation more often than a phobia, so the
                 # situations people actually write are named here.
                 "lose", "lost my", "my job", "redundancy",
                 "redundant", "being made redundant", "sacked", "fired", "unemployed",
                 "monday", "mondays", "monday morning",
                 "monday mornings", "work tomorrow", "going to work",
                 # a feeling about a person is not a phobia: "i have a fear of commitment" is
                 # somebody talking about a relationship, and the ladder it got told the person
                 # to build an exposure hierarchy against their partner. The everyday phrases
                 # that only look like a phobia are held out with it.
                 "commitment", "intimacy", "intimate", "relationship", "relationships",
                 "my marriage", "my partner", "my girlfriend", "my boyfriend",
                 "missing out", "fomo", "being alone", "loneliness", "being judged",
                 "rejection", "being rejected", "abandonment",
                 # a pest in the kitchen is the pest card's question, and a fear of the mice is
                 # how somebody says the mice are there: "i am scared of mice in the kitchen"
                 # had the block-the-gap-and-set-traps answer before this row, and it was right.
                 # A mortgage is the money-worry answer's for the same reason - the "what if"
                 # card answers the worry itself - though "a fear of money" stays this row's,
                 # because that is a fear of nothing in particular and there is no errand in it.
                 "mice", "mouse", "rat", "rats", "rodent", "rodents", "kitchen",
                 "mortgage", "mortgages",
                 # the same shape, found on the deck rather than by a person: a fear said in
                 # the middle of a real errand belongs to the answer that has the errand in it.
                 # "council tax arrears, im scared of bailiffs" was the debt card and became
                 # "a fear of bailiffs is learned"; "im scared of putting my face in the water"
                 # was the shallow-end answer and became "a fear of putting is learned"; and
                 # "im scared of horror films what should i watch" was a film pick. All three
                 # name something with an answer of its own, so they are held out here.
                 "arrears", "bailiff", "bailiffs", "debt", "debts", "council tax", "summons",
                 "eviction", "evicted", "landlord", "court", "credit card", "overdraft",
                 "swim", "swims", "swimming", "swimmer", "pool", "pools", "water", "sea",
                 "face in the water", "lessons", "lesson", "instructor",
                 "film", "films", "movie", "movies", "horror", "watch", "watching", "tv",
                 "series", "documentary",
                 # a fear that is a symptom to be explained, not a fear to be beaten
                 "why am i scared of dying", "death", "dying", "panic attack now",
                 "heart is racing", "cant breathe", "chest pain", "suicidal", "kill myself",
                 # a thing to be afraid OF right now is a safety question
                 "abusive", "hit me", "hits me", "threatened", "stalker", "following me"),
          # "i have a phobia of lifts" names the fear and asks nothing else: that is the question
          report=True,
          bias=3),
]
