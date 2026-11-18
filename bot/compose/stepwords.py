"""The words after a plan's "to": the step itself, or the place it goes to.

Two lines open the same way and are not the same sentence:

    im going to dye my hair pink        a step, so the phrase said back is "dyeing your hair pink"
    im going to the gym                 a place, so the phrase said back is "going to the gym"

Turning whatever follows a "to" into an -ing word gave people nonsense, because most of what
follows a "to" is not a verb: "is that a good idea" after "im going to bed early tonight" was
answered "Tell me what matters most about bedding early tonight", "im going to the gym" became
"Theing gym - that is your call, not mine", and "im going to town later" became "about towning
later". A noun is not a step, and the fold only belongs on a step.

The list is a list of steps and not a dictionary of every verb: a word it does not know is said
back with its own "going to" in front ("going to spain in may", "going to the gym"), which is
always the words the person used and always a phrase a sentence can hold. The failure is then a
slightly longer phrase, never a word that does not exist.
"""

# The verbs a plan opens with: "dye", "learn", "quit", "book". Enough of them that the everyday
# plans keep the short phrase ("dyeing your hair pink" rather than "going to dye your hair pink").
STEPS = frozenset("""
    abandon adopt apply arrange ask attend bake be begin board book borrow bring build buy call
    cancel catch change check choose clean clear climb close come continue cook cover cut decorate
    decide do drink drive drop eat email empty enter feed fight find finish fix fly follow forget
    get give go grow hand have head help hire hold hunt improve increase install invest invite
    join keep knit launch learn leave lend let listen live log look lose make marry meet move open
    order organise organize paint pass pay phone pick plan plant play post practise prepare put
    quit read record redecorate reduce register remember remove renovate rent repair replace
    report rescue retire return review ride ring run save say see sell send set sew shave shop
    sign sit slow sort speak spend split start stay stop stream study submit swap switch take talk
    teach tell test text throw tidy train transfer travel treat trim try tune turn uncover upgrade
    use visit volunteer wait walk wash watch wear win withdraw work write accept appeal babysit
    celebrate claim cycle decline dye insure jog meditate renew reply respond retrain rewire swim
    complain apologise apologize argue browse cheat chill confess cry cuddle dance delay delete
    download dress forgive gamble hide hug joke kiss laugh lay lie nap panic postpone pray print
    relax scroll shower sing skip sleep snooze stall stretch sulk tease worry yawn
""".split())

# The steps that double their last letter even though they are long: "begin" -> "beginning",
# "forget" -> "forgetting". Everything else in English doubles only when it is short enough to
# have one syllable, which is why "visit" is "visiting" and "quit" is "quitting".
DOUBLES = frozenset("""
    begin forget regret admit commit prefer refer occur submit permit upset control patrol compel
    propel equip
""".split())


# The steps whose -ing form is not the word with "ing" on the end. "be" is the one that matters:
# "im going to be 40 next week" was read as the step "be" and folded to "bing", so the bot asked
# "what matters most about bing 40 next week".
IRREGULAR = {"be": "being"}


def _ing(word):
    """The -ing form of a step: "learn" -> "learning", "run" -> "running", "dye" -> "dyeing"."""
    if not word or word.endswith("ing"):
        return word
    if word in IRREGULAR:
        return IRREGULAR[word]
    if word.endswith("ie"):
        return word[:-2] + "ying"
    if word.endswith("e") and not word.endswith(("ee", "ye", "oe")):
        return word[:-1] + "ing"
    # A short word ending consonant-vowel-consonant doubles it ("run", "quit", "swim"), and the
    # "qu" in "quit" is a consonant sound, so the u after a q does not turn it into two syllables.
    short = len(word) <= 4 or word in DOUBLES
    if (short and len(word) > 2 and word[-1] not in "aeiouwxy" and word[-2] in "aeiou"
            and (word[-3] not in "aeiou" or (word[-3] == "u" and word[-4:-3] == "q"))):
        return word + word[-1] + "ing"
    return word + "ing"


def a_step(word):
    """True when the word after a plan's "to" is the step itself rather than a place or a thing."""
    return (word or "").strip().lower().strip(".,!?") in STEPS


def said_after_a_to(phrase, ing=None):
    """The words after a plan's "to", said back as a phrase a sentence can hold.

    "dye my hair pink" -> "dyeing my hair pink"; "the gym" -> "going to the gym"; "bed early
    tonight" -> "going to bed early tonight". The second is what every phrase the reader cannot
    vouch for gets, because "going to" takes a noun as happily as a verb.
    """
    phrase = " ".join(str(phrase or "").split()).strip(" .,!?:;")
    words = phrase.split()
    if not words:
        return ""
    if a_step(words[0]):
        fold = ing or _ing
        return fold(words[0]) + (" " + " ".join(words[1:]) if len(words) > 1 else "")
    return "going to " + phrase


# The openings that put a place or a step after the "to" and mean by it either one: "im going to
# the gym" and "im going to learn spanish". Every other opening of a plan ("want to", "thinking
# of", "planning to") is an infinitive, so what follows it is a verb.
MOVING_TO = "going to|gonna|off to|out to|away to|heading to|heading off to|about to"
