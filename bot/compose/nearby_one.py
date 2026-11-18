"""A near-me ask with the thing left out: "is there one close by".

The named form of this question - "is there a launderette near me" - has a pool of its own, and it
answers well: it says there is no local list here, that a map app shows what is close, and that a
phone call settles the rest. The same question asked with the thing left out was not read at all:

    im looking for a launderette
    is there one close by
    -> "I'm not sure about that one, sorry - I'd rather not guess. A quick search online will get
        you a solid answer, and I can help you make sense of what you find."

The person has just said what they are looking for. "One" is that thing. So the second line is the
named ask, and the answer is the named answer with the words put back in: "a map app search for
launderette near you". Nothing here is invented - the thing named is the person's own word from
their own line, and the advice is the advice the named ask already gets.

Two things are read and one is refused:

- the shape: "is there one near me / near here / nearby / close by / round here / in my area",
  "is there any near me", "where is the nearest one", "where can i find one", "can you find one".
- the thing: the last thing the person said they were looking for, with the frame dropped
  ("im looking for a launderette" -> "launderette", "i need a cash machine for the car park" ->
  "cash machine").
- a state is not a thing to find. "im exhausted" then "is there one near me" is not a search for
  an exhausted, and the module stands down.
- a pronoun ask whose thread this cannot read. Main has pools for the near-me ask as well, and a
  question back ("which thing is it?") is not an improvement on them: with no thing found, the
  line is left exactly as it was.

Everything else returns None, and the fallback keeps the line it has.
"""
import re

# The pronoun ask. "one" is the thing the thread named; "any" is the same word with nothing behind
# it ("is there any near me"), and the two are read the same way.
THE_PRONOUN_ASK = re.compile(
    r"(?<![a-z])(?:is|are)\s+there\s+(?:one|any)\s+"
    r"(?:near(?:\s+(?:me|here|us))?|nearby|close\s+by|close\s+to\s+(?:me|us|here)"
    r"|round\s+here|around\s+here|in\s+(?:my|the|our)\s+(?:area|town|village|end|city))\b"
    r"|(?<![a-z])(?:is|are)\s+there\s+(?:one|any)\s+(?:close\s+by|nearby)\b"
    r"|(?<![a-z])where(?:'s|\s+is)\s+the\s+(?:nearest|closest)\s+one\b"
    r"|(?<![a-z])(?:where|how)\s+(?:can|do|would|should)\s+i\s+(?:find|get|locate)\s+(?:one|any)\b"
    r"|(?<![a-z])(?:can|could|will)\s+you\s+(?:find|point\s+me\s+to|tell\s+me\s+where\s+to\s+find)"
    r"\s+(?:one|any)\b",
    re.I)

# The frame a person puts in front of the thing they are looking for. Only the words after it are
# the thing: "i need a cash machine for the car park" names a cash machine, not a car park.
THE_FRAME = re.compile(
    r"(?<![a-z])(?:"
    r"i\s*(?:'m|m)?\s*(?:looking\s+for|after|in\s+need\s+of|trying\s+to\s+find)"
    r"|i\s+(?:really\s+)?(?:need|want|would\s+like|am\s+after)"
    # "i could do with a cash machine" is the commonest British way to ask this, and "i could use"
    # and "im desperate for" are the same ask with a mood on it.
    r"|i\s+could\s+(?:really\s+)?(?:do\s+with|use|find)"
    r"|(?:im|i\s+am)\s+(?:desperate|dying)\s+for"
    r"|looking\s+for"
    r"|(?:where|how)\s+(?:can|do|would)\s+i\s+(?:get|find|buy|locate)"
    r"|(?:is|are)\s+there\s+(?:a|an|any)"
    r"|(?:can|could)\s+you\s+(?:find|recommend|point\s+me\s+to)"
    r"|ive\s+been\s+(?:trying\s+to\s+find|looking\s+for|desperate\s+for)"
    r"|(?:do\s+you\s+know\s+(?:where|of)\s+(?:a|an|any)?)"
    # "any idea where i can find a chippy" is the same frame with a question in front of it.
    r"|(?:any\s+idea|any\s+suggestions?)\s+(?:where|of|for)\s+"
    r"(?:i\s+(?:can|could|might)\s+(?:find|get|buy))?"
    r")",
    re.I)
# Where the thing stops. A preposition, a purpose or a time is not part of its name.
THE_END = frozenset("""
for from that which who whom to in on at into onto with without near nearest nearby around round
about before after because but and or so as if when while during since until by through over under
between among per via than then there here this these those some any all my your our their his her
its it me us them him week weekend today tomorrow tonight morning afternoon evening night time
month year day hour minute minute please thanks thank soon asap now later
""".split())
# A determiner in front of the thing is dropped: "a launderette" is "launderette".
THE_ARTICLE = frozenset("a an the some another any other one two three couple few".split())
# A word saying what the place is like, dropped so the place itself is what is left: "a good chippy"
# is a chippy, and "the nearest one" is the pronoun ask rather than a thing.
THE_ADJECTIVE = frozenset("""
good nice decent cheap local proper reliable great best better closest nearest nearby quick
half-decent real actual special favourite favorite little big small large new old open
""".split())
# The word right after the frame, when it is what the person wants to do rather than a thing they
# want to find. "i need a plank" stays; "i need to stop" and "i want to get fitter" stand down.
A_VERB = frozenset("""
get stop be boil cover drink eat give go keep leave learn move order register reinstall remember
service shower sleep switch change use wake water cry open buy find start try make save spend
sort fix call book check
""".split())
# Not a thing anybody finds with a map app: a state, a feeling, or a word that is only ever the
# pronoun itself. The list is short on purpose - the frame and the end words do the work.
NOT_A_THING = frozenset("""
midwifery series batteries battery account card induction session job clothes course degree
""".split()) | frozenset("""
one any it thing something anything anyone someone everything nothing
lonely tired exhausted sad happy angry upset worried anxious stressed ill sick unwell better worse
ok okay fine well hungry thirsty bored cold hot warm busy free awake asleep asleep dead alive
working broken fixed sorted ready done finished lost stuck late early right wrong sure certain
true false real possible likely easy hard difficult cheap expensive worth allowed legal illegal
allowed normal strange weird fair unfair safe dangerous
good bad great nice best worst better worse
somewhere anywhere nowhere everywhere someplace anyplace
""".split())

# Two wordings, so the same line never comes back twice in a row in a thread.
NEARBY_ONE_POOL = (
    "Nothing here knows what is around you, sorry - no map, no local list. A map app search for "
    "{thing} near you is the quickest way to one, and the reviews on the listing beat anything I "
    "could recall about a place I have never been.",
    "I can't see your area, sorry. Put \"{thing}\" and your town into a map app and it shows what "
    "is close, with the opening hours and the distance; the place's own page or a phone call "
    "settles anything else about it.",
)
# A thing with a door is what a map app is for. These are the subjects a search for "one near me"
# is not: an answer is not a place, and neither is a person.
NOT_A_PLACE = frozenset("""
chance news way idea reason point need risk history proof difference problem question law rule
lift taxi bus train tram coach tube flight ferry delivery parcel refund appointment cure treatment
vaccine price cost quote answer opinion view
list colour color salary wage pay jewellery jewelry trousers pants jeans shoes shirt coat
""".split())

# A thing with a door is what a map app is for, and the last word of the thing is the word that says
# so. "im looking for a launderette" and "i need a cash machine" are places; "im looking for work",
# "i need a birthday present", "i want to learn spanish" and "im looking for a curry" are not, and
# the map-app answer to them ("put \"new coat\" into a map app") is worse than the hedge it replaced.
# This is the arm that keeps the module on its own shape.
PLACE_HEADS = frozenset("""
store stores station stations stop stops office offices garage garages bank banks centre center
market yard park pool hall hotel cafe pub clinic surgery pharmacy chemist hospital library
supermarket launderette launderettes laundrette tip depot studio salon agency firm company gym
takeaway barber hairdresser optician
""".split())
# The person who does the job is as findable as the place they run, and the trade is the last word
# of the thing: a plumber, a piano tuner, a key cutter, a removals firm. What people buy and do -
# a washer, a primer, a series, get fitter, stop existing - is not on a map, and the map-app answer
# to it is nonsense, so those stand down.
# A word that is only a place when something is said in front of it: a bookshop, a teashop, a bike
# shop. "a big shop" is a trip to the supermarket, so the bare word stands down.
A_CHORE = frozenset("shop shops store stores market markets".split())
A_TRADE = frozenset("""
plumber electrician decorator plasterer roofer builder joiner carpenter painter gardener cleaner
locksmith glazier tiler bricklayer mechanic groomer vet dentist doctor nurse optician physio
physiotherapist chiropodist podiatrist therapist counsellor psychotherapist solicitor barrister
accountant surveyor architect tutor instructor tuner cutter tailor barber hairdresser chef
caterer photographer director midwife osteopath acupuncturist notary
""".split())
# A place is often named by what it does rather than by a head noun: a bakery, a dentist, a plumber.
# Only the last word of the thing is tested, so "a cheaper phone" and "a birthday present" stand down.
# A suffix that makes a word a place and not a product: a launderette, a bakery, a library, a
# museum. The agent-noun endings ("er", "or", "ist") are not here on purpose - they let a washer, a
# primer and a dehumidifier through - and the trades are named in A_TRADE instead.
PLACE_TAILS = ("ette", "ettes", "ery", "ary", "eum", "eums")
# A place is often two words run together, and the head noun is on the end of the second: a
# bookshop, a petstore, a carwash, a hypermarket. Read the end of the word as well as the word.
PLACE_STEMS = ("shop", "store", "market", "station", "garage", "cafe", "park", "hall", "bank",
               "pool", "clinic", "centre", "center", "chemist", "pub", "hotel", "studio", "salon",
               "agency", "firm", "gym", "kiosk", "stall", "chippy", "chippie", "deli", "caff",
               "diner", "grill", "bistro", "launderette", "laundrette", "hospital", "surgery")
# A cash point is a cash machine: "point" is not a place word on its own, so the two-word name is
# read before the filter that keeps "point" out of a thing.
CASH_POINT = frozenset(("cash point", "cash points", "cashpoint", "cashpoints", "cash machine",
                        "cash machines", "atm", "atms"))
# A few of the things people look for are named by two words where neither is a place head: a post
# box, a phone box, a bottle bank. The pair is the thing, so it is read before the place test.
NEAR_ME_PAIR = frozenset(("post box", "postbox", "pillar box", "phone box", "bottle bank",
                          "recycling point", "public toilet", "public toilets", "litter bin",
                          "lost property office", "petrol station", "bus stop", "taxi rank"))


def _the_thing(line):
    """The thing the person said they were looking for, in their own words, or ""."""
    found = THE_FRAME.search(line)
    if not found:
        return ""
    words = line[found.end():].split()
    if words and words[0].strip(".,!?;:'\"()").lower() == "to":
        return ""
    kept = []
    for word in words:
        bare = word.strip(".,!?;:'\"()").lower()
        if not bare:
            continue
        if bare in THE_END or bare in THE_ARTICLE:
            if kept:
                break
            continue
        if bare in THE_ADJECTIVE and not kept:
            continue
        if not re.match(r"^[a-z][a-z'&-]*$", bare):
            break
        kept.append(bare)
        if len(kept) == 3:
            break
    if not kept:
        return ""
    if kept[0] in NOT_A_THING or " ".join(kept) in NOT_A_THING:
        return ""
    # "i need to stop", "i want to get fitter", "how long do i need to leave filler": the words
    # after the frame are a verb, not a thing, and a verb is not somewhere a map app could show.
    if kept[0] in A_VERB:
        return ""
    if " ".join(kept) in CASH_POINT or " ".join(kept) in NEAR_ME_PAIR:
        return " ".join(kept)
    if set(kept) & NOT_A_PLACE:
        return ""
    if set(kept) & NOT_A_THING:
        return ""
    if not _a_place(kept):
        return ""
    return " ".join(kept)


def _a_place(kept):
    """True when the thing the person named is somewhere a map app could show them."""
    last = kept[-1]
    # "i need a big shop before the weekend" is a job in the diary, not an address.
    if len(kept) == 1 and last in A_CHORE:
        return False
    # The last word is the thing: "a hotel job" is a job and "a library card" is a card, whatever
    # place words come in front of them.
    if last in PLACE_HEADS or last in A_TRADE:
        return True
    if last.endswith(PLACE_STEMS) or last.endswith(PLACE_TAILS):
        return True
    return False


def _the_thread_thing(memory, cleaned):
    """The thing the person said they were looking for, newest first, or "" if that was not a place.

    The last thing they asked for decides, because that is what "one" and "the nearest one" mean:
    four turns back is a different part of the conversation. A turn that asks for no thing at all
    ("its for a broken key") is a detail and does not decide anything, so the scan keeps going.
    """
    turns = (memory or {}).get("turns") or []
    seen = 0
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        said = (turn.get("user") or "").strip().lower()
        if not said or said == cleaned or THE_PRONOUN_ASK.search(said):
            continue
        seen += 1
        if seen > 4:
            break
        if not THE_FRAME.search(said):
            continue
        return _the_thing(said)
    return ""


def _pick(pool, line):
    """One of two wordings, the same one for the same line."""
    if not pool:
        return ""
    return pool[sum(ord(letter) for letter in line) % len(pool)]


def reply_for(line, memory=None):
    """The map-app answer to a pronoun near-me ask, or None."""
    if not line:
        return None
    cleaned = " ".join(line.lower().split())
    if not THE_PRONOUN_ASK.search(cleaned):
        return None
    thing = _the_thread_thing(memory, cleaned)
    if not thing:
        # Nothing in the thread this can put into a map app, so the line keeps whatever answer it
        # has. Asked cold, "is there one near me" is the fallback's; asked after a state
        # ("im exhausted") there is no thing at all.
        return None
    return _pick(NEARBY_ONE_POOL, cleaned).format(thing=thing)
