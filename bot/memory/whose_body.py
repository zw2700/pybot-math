"""Whose body a line is about when it says "he", "she" or "they" and no name.

"my dad is 70" then "hes got a bad hip" is one person's trouble told over two turns, and the
second turn names nobody: the "he" is the dad the chat has just named. Read as the speaker's own
body it got "Sorry to hear it - go easy on yourself today, and see someone if it's not shifting in
a few days", which is advice for a body that is not the one that hurts, and it tells the person
typing to see someone about their father's hip.

So this answers one question only - is a body on this line somebody else's? - for the composer's
carer reading to use. It needs both halves: a third-person pronoun carrying the body, and somebody
named in the chat within the last few turns. "i told my dad about my back" says "my", so the body
is the speaker's and this says nothing.
"""
import re

# The people a person looks after, named as theirs: "my dad", "our youngest", "my wife".
KIN = (r"(?:dad|daddy|father|mum|mummy|mother|mam|nan|nanna|gran|granny|grandma|grandad|"
       r"grandpa|granddad|son|daughter|child|kid|boy|girl|baby|little one|husband|wife|"
       r"partner|other half|boyfriend|girlfriend|brother|sister|niece|nephew|cousin|aunt|"
       r"uncle|friend|mate|neighbour|carer|flatmate|housemate|in laws|in-law)")
NAMED_SOMEBODY = re.compile(
    rf"\b(?:my|our|his|her|their)\s+(?:poor\s+|little\s+|eldest\s+|youngest\s+|old\s+|older\s+|"
    rf"elderly\s+|grown\s*up\s+)?{KIN}\b", re.I)
# The body a pronoun carries: "hes got a bad hip", "she has a sore knee", "his back is bad",
# "theyre in a lot of pain". The "my" of "i told my dad about my back" is the speaker's own.
PRONOUN_BODY = re.compile(
    r"\b(?:he|she|they|hed|shed|theyd)(?:'s|s|\s+is|\s+has|\s+had|\s+got|\s+has\s+got|"
    r"\s+keeps\s+getting|\s+was|\s+been)\b[^.!?]{0,26}?"
    r"\b(?:bad|sore|dodgy|gammy|weak|dicky|knackered|broken|cracked|twisted|swollen|stiff|"
    r"aching|hurting|hurts?|soreness|pain|stiffness|giving\s+him\s+trouble)\b"
    r"|\b(?:his|her|their)\s+(?:[a-z]+\s+){0,2}(?:hip|knee|back|shoulder|leg|arm|foot|feet|"
    r"hand|wrist|ankle|neck|stomach|chest|head|eye|ear|joints?)\b[^.!?]{0,18}?"
    r"\b(?:is|are|feels?|has\s+been|keeps)\b", re.I)
OWN_BODY = re.compile(r"\b(?:my|our)\s+(?:[a-z]+\s+){0,2}(?:hip|knee|back|shoulder|leg|arm|"
                      r"foot|feet|hand|wrist|ankle|neck|stomach|chest|head|eye|ear|joints?)\b",
                      re.I)


# An animal the person looks after is described in the same shape ("he has a bad leg"), and its
# line is the vet's, not the carer's. The nearer subject wins, so a pet named after a person in the
# same chat is the one the pronoun means.
PET = re.compile(r"\b(?:dog|dogs|puppy|pup|cat|cats|kitten|rabbit|bunny|hamster|guinea\s+pig|"
                 r"horse|pony|budgie|parrot|bird|fish|tortoise|snake|lizard|ferret|gerbil)\b",
                 re.I)


def somebody_was_named(memory):
    """True when the chat has named somebody the person looks after, in the last few turns."""
    try:
        turns = memory.get("turns") if isinstance(memory, dict) else None
    except AttributeError:
        return False
    if not isinstance(turns, list):
        return False
    for turn in reversed(turns[-4:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if PET.search(said):
            return False
        if NAMED_SOMEBODY.search(said):
            return True
    return False


def a_body_of_a_pronoun(clean):
    """True when the line hangs a body or a hurt on he/she/they rather than on "my"."""
    text = str(clean or "")
    if OWN_BODY.search(text):
        return False
    return bool(PRONOUN_BODY.search(text))


def somebody_elses_body(clean, memory):
    """True when this line is somebody else's body, named earlier in the chat."""
    return a_body_of_a_pronoun(clean) and somebody_was_named(memory)
