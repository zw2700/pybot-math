"""A breed is the animal it is.

"my greyhound is not eating" names no animal any knowledge entry is keyed on: the entry for a
dog that stops eating is keyed on "dog", "puppy" and "pup", and the breed word reaches none of
them, so the line fell all the way through to the composer and the person got "I'm here if you
want to dig into any of that" while "my dog is not eating" gets the vet-first answer. The same
hole ran through every breed: a labrador, a whippet, a poodle and a jack russell all got a
disclosure line, and a spaniel whose food was refused got the answer about changing food over,
because "spaniel" matched nothing and the card was chosen on the rest of the line.

So the reading carries the animal's own word beside the breed's: `words` gets "dog" after
"greyhound", which is what the line means, and every module that reads the animal it is - the
knowledge base most of all - sees a dog line. `clean` is untouched, so an echo or a
confirmation still says the person's own word back.

Two things keep this off lines that are not about an animal: a breed that is the first half of
some other name ("the greyhound bus is late", "greyhound racing" - the coach-delay entry was the
right answer to that one), and the ambiguous names ("boxer", "pointer", "setter", "springer",
"persian" the rug, "bengal" the tiger), which are left out of the table rather than guessed at.
"""
import re

# The breed, and the animal it is. Only names that mean the animal and nothing else: "boxer" is
# a sport and a man, "pointer" a cursor, "setter" a volleyball player, "springer" a spaniel or a
# springer spaniel's first half, "persian" a rug, "bengal" a tiger. Nothing here is a guess.
BREED_KIND = {
    # dogs
    "labrador": "dog", "lurcher": "dog", "greyhound": "dog", "whippet": "dog",
    "terrier": "dog", "spaniel": "dog", "retriever": "dog", "collie": "dog",
    "poodle": "dog", "beagle": "dog", "bulldog": "dog", "pug": "dog", "husky": "dog",
    "chihuahua": "dog", "dachshund": "dog", "dalmatian": "dog", "mastiff": "dog",
    "rottweiler": "dog", "doberman": "dog", "dobermann": "dog", "alsatian": "dog",
    "corgi": "dog", "staffie": "dog", "mongrel": "dog", "cockapoo": "dog",
    "labradoodle": "dog", "cavapoo": "dog", "pomeranian": "dog", "papillon": "dog",
    "schnauzer": "dog", "weimaraner": "dog", "vizsla": "dog", "samoyed": "dog",
    "akita": "dog", "shar pei": "dog", "lhasa apso": "dog", "afghan hound": "dog",
    "basset hound": "dog", "border collie": "dog", "cocker spaniel": "dog",
    "golden retriever": "dog", "labrador retriever": "dog", "jack russell": "dog",
    "german shepherd": "dog", "shih tzu": "dog", "staffordshire bull terrier": "dog",
    "bull terrier": "dog", "yorkshire terrier": "dog", "westie": "dog",
    "west highland terrier": "dog",
    # cats
    "siamese": "cat", "ragdoll": "cat", "moggy": "cat", "tabby": "cat",
    "tortoiseshell": "cat", "sphynx": "cat", "maine coon": "cat",
    "british shorthair": "cat", "scottish fold": "cat",
}
# The name of a bus, a coach service or a race, not an animal. The word after the breed says so.
# Money in the line with a plural breed framed only by "the" is a bet: "i lost money on the
# greyhounds" is not a person with dogs, and the puppy-price card is the wrong answer to it.
# Only the money itself is here. "Lost" and "won" are verbs, and a dog that lost or won something
# is still the speaker's dog: "the bulldog lost its lead" is a dog pulling on a lead, and reading
# the verb as money cost the line its animal and the answer to it.
MONEY = frozenset("""
money quid tenner tenners grand odds punter winnings bet bets betting stake stakes
""".split())
# A determiner frames a breed loosely: "the greyhounds". A possessive or a verb of having frames
# it as theirs: "my greyhounds", "we got a labrador".
LOOSE_FRAME = frozenset("the a an that these those this".split())
NOT_A_CREATURE_NEXT = frozenset("""
bus buses coach coaches station stations line lines service services depot depots ticket
tickets terminal terminals timetable timetables racing race races derby stadium track kennel
kennels club breeder breeders rescue glasses frames sunglasses sofa sofas rug rugs curtains
upholstery twin twins person people
""".split())
# The breed has to be said as an animal, and English says it with a determiner or a verb of
# having in front of it: "my greyhound", "we got a rescue greyhound", "a labrador". Without one
# the word is something else - "im husky" is a voice - and the animal would be added to a line
# about a person.
FRAME_BEFORE = frozenset("""my our his her their the a an another this that these those
got get gets have has had having keep keeps kept kept buy buys bought take takes took rescue
rescued adopt adopted rehome rehomed""".split())
# How far back a frame word still frames the breed: "we got a rescue greyhound" has two words
# between the verb and the animal, and a name ("my dog rex the labrador") one.
FRAME_REACH = 4
# A breed in front of one of these is the other thing the word means ("west highland terrier"
# is already in the table, and "the west highland line" is a railway).
BY_WORD = re.compile(r"^[a-z][a-z'-]*$")


def _singular(word):
    """The table's spelling of a plural breed: "greyhounds" is a greyhound, "collies" a collie."""
    if word in BREED_KIND:
        return word
    if word.endswith("ies") and word[:-3] + "y" in BREED_KIND:
        return word[:-3] + "y"
    if word.endswith("es") and word[:-2] in BREED_KIND:
        return word[:-2]
    if word.endswith("s") and word[:-1] in BREED_KIND:
        return word[:-1]
    return ""


def the_animal_a_breed_is(words):
    """The line's words with the animal's own word after each breed it names.

    `words` is the reading's word list, which is the text in order. Every breed word keeps its
    place and the animal goes straight after it, so a two-word key elsewhere in the line ("not
    eating", "off her food") still reads as it did, and a phrase breed ("jack russell") is filled
    once, after its last word. Nothing is added when the word after the breed makes it another
    thing: "the greyhound bus is late" and "greyhound racing" stay as typed.
    """
    if not isinstance(words, list) or not words:
        return words
    low = [word.lower() if isinstance(word, str) else "" for word in words]
    filled = []
    index = 0
    while index < len(low):
        found = ""
        span = 1
        # The longest phrase first: "golden retriever" before "retriever", and "jack russell"
        # before "russell" (which is not a breed on its own).
        for length in (4, 3, 2):
            phrase = " ".join(low[index:index + length])
            if len(phrase.split()) == length and BREED_KIND.get(_singular(phrase)):
                found, span = BREED_KIND[_singular(phrase)], length
                break
        if not found:
            found = BREED_KIND.get(_singular(low[index]), "")
        after = low[index + span] if index + span < len(low) else ""
        reachable = low[max(0, index - FRAME_REACH):index]
        frame_words = [word for word in reachable if word in FRAME_BEFORE]
        framed = bool(frame_words)
        if found and framed:
            if after in NOT_A_CREATURE_NEXT:
                framed = False
            elif (all(word in LOOSE_FRAME for word in frame_words)
                  and any(word in MONEY for word in low)):
                framed = False
        if found and framed:
            filled.extend(words[index:index + span])
            filled.append(found)
            index += span
            continue
        filled.append(words[index])
        index += 1
    if len(filled) == len(words):
        return words  # no breed named: the reading is the one the rest of the engine built
    return filled

def a_frame_before(text, start):
    """Whether a breed at `start` is said as an animal: a determiner or a verb of having first.

    The words of a line say what a breed word is being used as, and the store reads the raw line
    rather than the reading's word list, so this is the same test as `the_animal_a_breed_is` over
    the text before the breed. "im husky" is a voice, not an animal.
    """
    before = re.findall(r"[a-z']+", text[:max(0, start)].lower())[-FRAME_REACH:]
    return any(word in FRAME_BEFORE for word in before)


def the_breed_named(text):
    """The table's spelling of the breed in `text`, or "" - "greyhounds" is "greyhound"."""
    word = " ".join(str(text or "").lower().split())
    return _singular(word)


def the_kind_of(word):
    """The animal a breed word names - "dog", "cat" - or "" for anything else."""
    return BREED_KIND.get(the_breed_named(word), "")


def _alternation():
    """Every breed as one pattern, the longest phrase first so "golden retriever" wins."""
    names = sorted(BREED_KIND, key=lambda name: (-len(name.split()), -len(name)))
    return "|".join(name.replace(" ", r"\s+") for name in names)


# The same table as a pattern, so a reader that is looking for an animal can find one wherever
# the animal is named by its breed. The store is the reader that needs it: "we got a rescue
# greyhound last week" tells it about a dog, and "what pets do i have" has to be able to say so.
BREED_RE = re.compile(r"\b(?:" + _alternation() + r")(?:s|es)?\b", re.I)
