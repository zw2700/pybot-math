"""The tail of a phrasal verb belongs to the verb, not to the thing the person named.

"i need my dress taken up" names a dress, and what they want done to it. The bot read the last
word as the thing and asked "What kind of up do you usually go for?"; "i need my car washed" got
"What kind of washed do you usually go for?". Neither is a sentence a person can answer, because
the thing being talked about is the dress and the car, and the rest of the line says what is to be
done to it.

So the words that make up a "something done" tail - the verb of it and its particle - are kept
here, and `bot/modules/chat.py` asks this module before it decides a thing comes in kinds. The
list is deliberately only the verbs people use for work somebody else does on something of theirs,
so an ordinary "i need my car" or "i want a clean shirt" is untouched.
"""
import re

# up down in out off ... after a verb these say how the work goes, not what the thing is. Most of
# them are already in chat.py's NOT_THE_THING; they are named here so a tail made of a verb and
# one of them can be taken off whole.
A_PARTICLE = frozenset("up down in out off over away along through round back".split())

# The verb half. Past participles and -ing forms only: those are the ones that follow a thing in
# "my dress taken up", "my car being washed", "my hair cut". A bare verb ("i need my car tow")
# is not a sentence anyone types.
A_VERB_TAIL = frozenset("""
taken took taking put putting let letting thrown threw given gave done doing made making
fixed fixing mended mending altered altering hemmed hemming patched darned
repaired repairing cleaned cleaning washed washing cut cutting painted painting
cleared clearing tidied tidying mowed mowing serviced servicing trimmed pruning
swept hoovered vacuumed dusted walked boarded shortened lengthened
""".split())


def a_thing_without_its_tail(said):
    """The thing said back without the job worded after it: "your dress taken up" -> "your dress".

    Only whole words come off, and never the last one: a line that is all tail keeps what it has,
    because an empty thing is worse than an awkward one.
    """
    words = str(said or "").split()
    while len(words) > 1 and words[-1].lower().strip(".,!?") in (A_PARTICLE | A_VERB_TAIL):
        words.pop()
    return " ".join(words)


def a_job_word(word):
    """True when this word is the verb or particle of a job, not a thing to pick a kind of."""
    return str(word or "").lower().strip(" .,!?;:'\"()") in (A_VERB_TAIL | A_PARTICLE)
