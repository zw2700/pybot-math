"""A pet whose name has moved in the sentence: "we renamed him max", "hes max now".

The store reads a name put right ("no hes called max") and a name given ("my dog is called rex"),
but not the line that says in as many words that the name has changed, and it kept the name it
had:

```
my dog is called rex / we renamed him max / whats my dog called
  before: You've got a dog called Rex.
  after:  You've got a dog called Max.
```

The frames are closed because each of them says a name has changed: `renamed`, `i changed it to`,
`we call him ... now`, `he answers to`, `now called`, `hes max now`. A line with only a pronoun
and a name in it ("hes max") is as often a fact about somebody as a rename, so it is not read
here.

Two things keep this off the lines that only look like a rename. The name has to stand bare (a
determiner in front of it makes it a thing: "we renamed the pub", "he goes by the gate now"), and
the line has to be about the animal - a person in it is somebody else's name ("my son changed his
name to sam", "i changed my name to max").

This lives here, and not in `bot/modules/memory_store.py`, because that file is at the size the
runtime allows; the store calls it the way it calls the other memory readers.
"""

import re

from . import facts as extract

RENAMING = re.compile(
    r"\brenam(?:e|ed|es|ing)\b"
    r"|\bchang(?:e|ed|es|ing)\b[^.?!]{0,24}?\bnames?\b"
    r"|\bchang(?:e|ed|es|ing)\s+(?:it|him|her|them)\s+(?:to|into)\b"
    r"|\bcall\s+(?:him|her|it|them)\b[^.?!]*\bnow\b"
    r"|\banswers?\s+to\b|\bgoes?\s+by\b"
    r"|\bnow\s+(?:called|named)\b"
    r"|\b(?:he|she|it|they)(?:'s|s| is| are)\s+[a-z'-]{2,}\s+now\b"
    r"|\bnow\s+(?:he|she|it|they)(?:'s|s| is)\b", re.I)
# The words a rename can trail after the new name ("max now", "max instead"), which are not part of
# it. Everything else in the line is the frame, and the name is the last word of it that is a name.
AFTER_A_NEW_NAME = frozenset("""now instead please ok okay tbh tho though then actually too also
from onwards today anyway honestly like""".split())
NOT_A_NEW_NAME = frozenset("""it him her them the to as called named name rename renamed
they we i you us me dog cat puppy kitten pet animal""".split())
# A name stands bare. A word with a determiner in front of it is a thing the line is about, not
# what the animal is called now: "we renamed the pub" is a pub and "he goes by the gate now" is a
# gate, and both were read as a dog called Pub and a dog called Gate.
# "her" is not here: it is the object of the rename verb as often as a possessive ("weve renamed
# her bella"), and the name comes right after it.
A_THING_IN_FRONT = frozenset("""the a an this that these those my our his their your its
some any another one""".split())
# The line has to be about the animal, and a person in it is somebody else's name rather than the
# pet's: "my son changed his name to sam" is the son's name and "i changed my name to max" is the
# person's, and both renamed the dog.
A_PERSON_IN_THE_LINE = re.compile(
    r"\b(?:son|daughter|mum|mom|mother|father|dad|wife|husband|partner|boyfriend|girlfriend|"
    r"brother|sister|friend|boss|colleague|neighbour|neighbor|child|kid|baby|gran|grandma|"
    r"grandad|grandpa|nan|nana|aunt|uncle|cousin|mate|flatmate|housemate|carer|teacher|"
    r"people|someone|somebody)\b", re.I)
THE_PERSONS_OWN_NAME = re.compile(r"\b(?:my|our)\s+names?\b", re.I)


def moves(low):
    """True when the line says in as many words that a name has changed."""
    return bool(RENAMING.search(" ".join(str(low or "").split())))


def the_name_it_gave(low):
    """The name at the end of a line that says the name has moved, or "".

    People put the new name where the new name goes - at the end: "we renamed him max", "i changed
    it to max", "he is now called max", "hes max now". Only the last word that is not a word the
    line trails off with is read, and only when it holds up as a name on its own
    (`facts.a_name_could_be`), so "i changed it to friday" and "we renamed him to the vet" keep
    their own reading.
    """
    words = [word.strip(".,!?;:'\"") for word in str(low or "").split()]
    while words and words[-1].lower() in AFTER_A_NEW_NAME:
        words.pop()
    if not words:
        return ""
    word = words[-1]
    if len(word) < 2 or word.lower() in NOT_A_NEW_NAME:
        return ""
    if len(words) > 1 and words[-2].lower() in A_THING_IN_FRONT:
        return ""
    return word if extract.a_name_could_be(word) else ""


def the_name_a_line_moved_on(low, pets, animal_named):
    """The new name for the animal a rename line is about, or "".

    `pets` is the store's list and `animal_named` says whether the line names the animal ("we
    renamed the dog milo"). Either the line names the animal, or the rename verb has a bare
    pronoun for its object and the store holds one named animal, which is what the pronoun is
    ("we renamed him max", "hes max now"). A line that names a person, or says the person's own
    name has changed, is never the pet's rename.
    """
    low = " ".join(str(low or "").split())
    if not low or A_PERSON_IN_THE_LINE.search(low) or THE_PERSONS_OWN_NAME.search(low):
        return ""
    pets = [pet for pet in (pets or ()) if isinstance(pet, dict)]
    if not pets:
        return ""
    if not animal_named and len([pet for pet in pets if pet.get("name")]) != 1:
        return ""
    return the_name_it_gave(low)
