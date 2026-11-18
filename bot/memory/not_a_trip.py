"""Whether a "going to ..." line is going anywhere at all.

Every "going to" line was read as a trip: the words after "to" became the place, and the person
was asked about it as if they were packing.

    im thinking of going back to uni next year  ->  "Uni, lovely. When is it?"
    im going to start a small business          ->  "Start, lovely. When is it?"

Nobody is going anywhere: one is a decision to weigh, and the other is a doing. The place is the
code that happens to follow "to", and both of these are what a noun phrase cannot be:

- a determiner after the first word says that word is a verb - "start a small business" cannot be
  a place called Start, because a place does not put "a" after its own name ("the Lake District"
  keeps its "the" in front, which is where a determiner belongs);
- a particle after it says the same thing. "think about it" and "save up first" are a verb and its
  particle, and the words after "to" are read as a place word for word: "Think About It, lovely.
  When is it?". The particles here are the ones no place name uses - "upon", "on" and "of" are
  absent because Stratford upon Avon, Henley on Thames and the isle of wight are journeys, and
  "in" is absent for "Barton in the Clay";
- a verb of the body or the feelings after "to" is the doing itself, and nobody asks when a
  person is going to cry: "im going to cry", "im going to throw up", "im going to die of
  embarrassment" were answered "Cry, lovely. When is it?" and "Die of Embarrassment - nice.
  When are you going?". A place is never a bare verb, so one word is enough to know;
- a place of ordinary life is not a trip. School, work, the gym and the shops are already known
  here, and uni, college and the nursery are the same errand: going back to one of those is not a
  holiday and nobody wants their month asked about.
"""
import re

DETERMINER = frozenset("""
a an the my your our their his her its this that these those some any another each every no
""".split())
# Leading determiners that belong to the place itself: "the Lake District", "the isle of wight".
BELONGS_TO_THE_PLACE = frozenset("the a an".split())
# Particles that turn the word before them into a verb. A place name does not put one of these
# after its first word, and the prepositions place names do use (upon, on, of, in) are left out on
# purpose, so "stratford upon avon" and "henley on thames" stay the journeys they are.
PARTICLE = frozenset("""
about up down out back off over through around round along into away
""".split())
# The verbs that follow "going to" and name a doing rather than a destination. Every reader of a
# "going to" line needs these, not just the one that formed the sentence: the trip reader asked
# "Wait, lovely. When is it?" of "im going to wait till next year", and the echo asked "What do you
# want to do while you're there?" of the same line, because neither list had the word in it.
#
# A doing is not a place even when a date follows it - "wait till next year", "try again in the
# spring", "hold off till the new year" all read as somewhere to go, and each was answered as a
# trip. The test is the word itself: a verb is a verb whatever comes after it, so this list is the
# one place a doing is named, and both readers ask it rather than keeping a list each.
DOING_AFTER_TO = frozenset("""
wait waits waited waiting hold holds held holding hope hopes hoped hoping plan plans planned
planning think thinks thought thinking save saves saved saving spend spends spent spending
finish finishes finished finishing decide decides decided deciding apply applies applied applying
arrange arranges arranged arranging aim aims aimed aiming avoid avoids avoided avoiding
worry worries worried worrying sort sorted sorting
be been being get gets got getting go goes going do does did doing see sees saw seeing
try tries tried trying have has had having keep keeps kept keeping quit quits quitting
leave leaves left leaving start starts started starting stop stops stopped stopping
manage manages managed managing afford affords afforded affording book books booked booking
lose loses lost losing win wins won winning sell sells sold selling
ask asks asked asking tell tells told telling call calls called calling look looks looked looking
find finds found finding put puts putting buy buys bought buying eat eats ate eating
drink drinks drank drinking work works worked working sleep sleeps slept sleeping
pass passes passed passing faint faints fainted fainting collapse collapses collapsed collapsing
throw throws threw thrown throwing die dies died dying move moves moved moving
wean weans weaned weaning
""".split())
# Places of ordinary life, in the same family as the school, work and the gym the trip reader
# already knows about: a person goes back to one of these, they do not go away to it.
ORDINARY = frozenset("""
uni university unis college colleges campus nursery nurseries creche childcare playschool
""".split())
# The verbs a person says after "going to" when the going is a doing: what the body does and
# what a feeling does. The trip reader already knows the planning verbs ("start", "see", "get"),
# and these are the family it missed, so "im going to cry" became a place called Cry and the
# person was asked what month they were going. Only words that cannot name somewhere are here:
# a place called Bath, Nice or Split is still a place, so its verb is not in the list.
DOING = frozenset("""
feel feels felt feeling
cry cries cried crying sob sobs sobbing weep weeps weeping wail wails wailing
laugh laughs laughed laughing giggle giggles giggling chuckle chuckles chuckling
scream screams screamed screaming shout shouts shouted shouting yell yells yelled yelling
panic panics panicked panicking faint faints fainted fainting
throw throws threw throwing vomit vomits vomited vomiting puke pukes puked puking
sneeze sneezes sneezed sneezing cough coughs coughed coughing hiccup hiccups hiccuping
burp burps burped burping gag gags gagged gagging choke chokes choked choking
die dies died dying explode explodes exploded exploding burst bursts bursting
moan moans moaned moaning groan groans groaned groaning snore snores snored snoring
sweat sweats sweated sweating blush blushes blushed blushing
shiver shivers shivered shivering tremble trembles trembled trembling
wet wee poo splutter splutters spluttering
# The same word twice, once as the doing and once as the idiom it makes: "im going to lose it"
# and "im going to crack up" are the temper, "im going to pass out" is the body, and "im going
# to snap" is both. A place is never one of these on its own, so the second word does not matter.
lose loses losing lost crack cracks cracked cracking snap snaps snapped snapping
pop pops popped popping flip flips flipped flipping pass passes passed passing
break breaks breaking broke broken
""".split())


def a_doing_after_to(going_words):
    """True when the words after "to" are a verb and its object ("start a small business")."""
    kept = [word for word in going_words
            if str(word).strip(" ,.;:!?'\u2019") not in ("",)]
    if kept and kept[0].lower().strip(" ,.;:!?") in BELONGS_TO_THE_PLACE:
        kept = kept[1:]
    if not kept:
        return False
    first = kept[0].lower().strip(" ,.;:!?'\u2019")
    if first in DOING_AFTER_TO or first in DOING:
        # A verb is a doing whatever follows it: "going to wait", "going to wait till next year",
        # "going to cry", "going to throw up". Nothing after it makes it a place.
        return True
    if len(kept) < 2:
        return False
    second = kept[1].lower().strip(" ,.;:!?'\u2019")
    return second in DETERMINER or second in PARTICLE


def a_place_of_ordinary_life(place):
    """True when the place is where the person already goes, not somewhere they are going."""
    words = [word.lower().strip(" ,.;:!?'\u2019") for word in str(place or "").split(" ")]
    words = [word for word in words if word]
    if words and words[0] in BELONGS_TO_THE_PLACE:
        words = words[1:]
    return bool(words) and words[0] in ORDINARY


def not_a_destination(going_words, place):
    """True when a "going to ..." line names a doing or an everyday place, not a trip."""
    return a_doing_after_to(going_words) or a_place_of_ordinary_life(place)


# A "going to" whose destination is a person: "im going to my sisters on saturday", "we are going
# to my in laws". The words after "to" are family, not a place, so the trip card that says the
# place back ("My Sisters, nice. When is it?") is nonsense, and no packing list or flight length is
# what the person wants. It is a visit, and it is answered as one.
A_PERSON = (r"(?:sister|brother|mother|father|son|daughter|mum|mom|dad)[\s-]in[\s-]laws?|"
            r"sisters?|brothers?|mum|mom|mam|mother|father|dad|parents?|gran|granny|nan|nana|"
            r"grandma|granddad|grandad|grandpa|grandparents?|aunts?|aunty|auntie|uncles?|cousins?|"
            r"in[\s-]?laws?|sons?|daughters?|kids|children|family|friends?|mates?|pals?")
VISIT_TO = re.compile(
    # "going to my sisters", "off to my mums", and the same said as the purpose of the journey:
    # "going to see my parents", "visiting my parents on sunday".
    r"\b(?:(?:to|at)\s+|(?:to\s+)?(?:see|seeing|visit|visiting)\s+)"
    r"(?P<own>my|our|his|her|their)\s+(?:the\s+)?(?:own\s+)?(?P<person>" + A_PERSON + r")"
    r"(?:\u2019s|'s|s')?s?(?:\s+(?P<thing>house|place|flat|home))?"
    r"\s*(?=$|[,.!?;]|\b(?:for|on|at|this|next|tonight|tomorrow|today|later|after)\b)",
    re.IGNORECASE)


# The same reading for a destination on its own ("my aunts"), as the trip reader stores it.
THEIR_PERSON = re.compile(
    r"^\s*(?P<own>my|our|his|her|their)\s+(?:own\s+)?(?P<person>" + A_PERSON + r")"
    r"(?:\u2019s|'s|s')?s?(?:\s+(?P<thing>house|place|flat|home))?\s*$", re.IGNORECASE)


def _the_person_in(found):
    """Who a match names, said the way the trip reader stores a place: "my brothers", "my in laws",
    "my parents house". The possessive in front is what makes it a person ("my kids school"), and
    the answer says it back as theirs."""
    who = " ".join(found.group("person").lower().split())
    if who.startswith("in"):
        # "my in laws" is one relation, written as a hyphen so the possessive lands on the end of
        # it ("your in-laws'") rather than on a capital in the middle of the sentence.
        who = "in-laws"
    said = found.group("own").lower() + " " + who
    thing = (found.groupdict().get("thing") or "").lower()
    return said + " " + thing if thing else said


def a_person(place):
    """The person when a destination is only a person ("my aunts"), or "" when it is a place."""
    found = THEIR_PERSON.match(str(place or ""))
    return _the_person_in(found) if found else ""


# The words that say a line is set off somewhere: the going has to be in front of the person, or
# the person has to be what the line is about. "ive stopped seeing my mates" and "im not allowed
# to see my kids" are not visits, and neither is "its at my mates house" said about a barbecue.
GOING_BEFORE = re.compile(
    r"\b(?:going|goes|went|off|away|over|down|up|round|around|out|back|heading|driving|flying|"
    r"travelling|traveling|staying|stay)\b", re.I)
FILLER_BEFORE = re.compile(r"^\s*(?:(?:so|and|but|oh|also|anyway|then|now|well|ok|okay|right|"
                           r"im|i'm|i am|we're|we are|were|i|we)\s+){0,3}$", re.I)


# Somebody in a hospital bed is not a nice outing, and the words that say so come after the person
# ("going to see my friend at the hospital", "off to my dad in hospital"). The visit reading stops
# at "at" and "in" so that an ordinary visit with a time on it still reads ("my sisters at the
# weekend"), which left the care home behind; here it takes the whole line back, and the reading
# that knows the hospital is a worrying place keeps its answer.
IN_A_CARING_PLACE = re.compile(
    r"\b(?:at|in|to)\s+(?:the\s+|a\s+)?(?:hospital|hospice|care home|nursing home|residential "
    r"home|clinic|infirmary|surgery|ward|a&e|ae|icu|intensive care|high dependency|"
    r"coronary care|children'?s ward)\b", re.I)


def the_visit(line):
    """The person a line is going to see, or "" when the words after "to" name a place.

    "im going to my sisters on saturday" goes nowhere called My Sisters, and "we are going to my in
    laws" is not a trip to Laws. Only a destination that ends at the person counts: "im going to my
    sisters in spain" is a journey to Spain, and the trip reader keeps it. The line has to be one
    about going, too, or the same words in another sentence are a different thing.
    """
    said = str(line or "")
    if IN_A_CARING_PLACE.search(said):
        return ""
    found = VISIT_TO.search(said)
    if not found:
        return ""
    before = said[:found.start()]
    if not (GOING_BEFORE.search(before) or FILLER_BEFORE.match(before)):
        return ""
    return _the_person_in(found)
