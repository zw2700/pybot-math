"""A taste they have told the bot about: "i love dogs", "not keen on fish", "not sure if i like curry".

A taste is a fact about the person, so it is said back like any other ("You love dogs - noted"),
but it is not a pet. Before this, "i love dogs", "i hate cats" and "not keen on rabbit" each put a
nameless animal in the store, and the recall answered "what pets do i have?" with "You've got a
cat" to someone who had just said they hated them. An animal is only theirs when a possessive says
so ("we love our dog", "i adore my cat"), which is what `LIKING_BEFORE` and `OWNED_BEFORE` are for:
the first reads the taste, the second keeps the pet in the line that really has one.

`read()` is the taste itself, for the echo in `bot/memory/ack.py`: the thing, and whether they
like it, do not, or are not sure. "not sure if i like curry" is not the same fact as "i don't like
curry", and a bot that stores the first as the second will leave curry out of every suggestion
after one hedge.
"""
import re

# The tail people put after a thing ("curry tho", "fish though", "olives lol") is not part of it,
# and neither is a word that only joins it to the next thing ("curry and", "fish and chips"), a
# quantity ("dogs so much", "coffee a lot") or the article in front of a noun ("going to the").
TAIL = frozenset("""
tho though lol lmao haha hehe tbh ngl imo idk innit tbf anyhow anyway really actually
right now today tonight tomorrow weekend week weekday evening morning afternoon night
either at all any more anymore yet still too also as well
and or but with so much very loads lots lot quite pretty
a an the of to for from in on at by about than then
monday tuesday wednesday thursday friday saturday sunday christmas birthday
""".split())

# Where a thing ends, whatever the four words allow: the rest of the line can be a question
# ("i hate cats so what should i cook") or a second clause with its own subject ("i hate cats and
# i have one"), and swallowing it made the store keep "cats so what should i" as a taste.
THING_STOP = frozenset("""
i we me us he she they you it them that this these those there
what how why when where which who whose whatever
is are was were am be been being will would should can could shall may might
do does did dont doesn't doesn't isn't aren't have has had got
so if because since though although while until
like loves loved love adore adores prefer prefers hate hates hated dislike dislikes
loathe loathes detest detests enjoy enjoys
""".split())

# A thing they can name in a taste: up to four words, so "curry and rice", "going to the cinema"
# and "my new job" are kept whole rather than cut to their first two words ("curry and").
THING = (r"([A-Za-z][A-Za-z'\u2019-]*(?:\s+(?:[A-Za-z][A-Za-z'\u2019-]*"
         r"|and|or|of|to|the|a|my|our|your|their|his|her)){0,4})")

# "im not sure if i like curry", "dunno whether i'd like it", "no idea if i'm keen on fish".
UNSURE = re.compile(
    r"\b(?:not sure|not certain|unsure|don'?t know|do not know|dunno|no idea)\s+"
    r"(?:if|whether|that)\s+(?:i|we)(?:'d|\s+would)?\s+(?:actually\s+|really\s+|even\s+)?"
    r"(?:like|love|enjoy|be into|get on with)\s+" + THING, re.I)
# "i don't like fish", "i dont think i like fish", "we never eat lentils".
NO = re.compile(
    r"\b(?:i|we)\s+(?:really\s+|just\s+|actually\s+)?(?:don'?t|do not|dont|never)\s+"
    r"(?:think\s+(?:i|we)\s+|really\s+)?(?:like|love|eat|drink|want)\s+" + THING, re.I)
# "im not keen on fish", "we're not a fan of mushrooms", "i'm not into olives", and the same
# said as a fragment ("not keen on fish", which is how it comes back as a reply).
NOT_KEEN = re.compile(
    r"(?:\b(?:i'?m|i am|we'?re|we are)|^)\s*not\s+"
    # The words people put in the middle, in the order they put them: "not a BIG fan of",
    # "not THAT keen on" (which was read), "not REALLY much of a fan of", "not a GREAT fan of".
    # The article used to be welded to the phrase ("not" + "a fan of"), so any adjective in
    # between made the whole thing no taste at all and "im not a big fan of fish" was answered
    # as a request for the fish recipe.
    r"(?:(?:that|really|very|so|all that|quite)\s+)?(?:much\s+of\s+)?(?:a\s+|the\s+)?"
    r"(?:(?:big|huge|massive|great)\s+)?"
    r"(?:keen on|fan of|into|mad about|fussed on|bothered about)\s+" + THING, re.I)
# "i hate cats", "we really can't stand mushrooms": a dislike, kept apart from `NO` because a
# thing of theirs can be hated too, and "i hate my job" is a feeling about their week rather than
# a taste the store should plan meals around (`_clean` keeps the possessive, so `HATE` is read
# only when the thing has none).
HATE = re.compile(
    r"\b(?:i|we)\s+(?:really\s+|just\s+|actually\s+|absolutely\s+|properly\s+)?"
    r"(?:hate|hates|dislike|dislikes|loathe|loathes|detest|detests|"
    r"can'?t stand|cannot stand|really can'?t stand)\s+" + THING, re.I)
# The food comes first in this one: "fish isn't really my thing", "pork isnt my kind of thing",
# "curry is not really my cup of tea". Every pattern above wants the phrase before the thing, so
# the other ordinary way of saying a taste could never match any of them.
MY_THING = re.compile(
    r"\b" + THING + r"\s+(?:isn'?t|is not|aren'?t|are not)\s+"
    r"(?:(?:really|that|exactly|quite)\s+)?(?:my|our)\s+"
    r"(?:(?:kind|sort)\s+of\s+|cup\s+of\s+tea|thing)", re.I)
# "i love dogs", "we really like fish", "i adore olives".
YES = re.compile(
    r"\b(?:i|we)\s+(?:do\s+|really\s+|absolutely\s+|just\s+|actually\s+)?"
    r"(?:like|love|adore|prefer)\s+" + THING, re.I)

# "i like it", "i love that", "i like this one": the thing is what is on the table, not a taste
# of theirs to keep, and the pronoun says nothing the store can use.
NOT_A_THING = frozenset("""
it that this these those them him her you me us one ones a an the to when if how why what
which who there here so such being doing having
myself yourself himself herself itself ourselves yourselves themselves oneself
way
""".split())

# The words a dislike arrives in, up to the end of the line. In `bot/memory/ack.py` some of these
# are also trouble words ("hates", "can't"), and a line whose only trouble word is the taste verb
# is a dislike of a thing, not someone's misbehaviour: "i hate cats" is not a row about a cat.
DISLIKE_IN = re.compile(
    r"\b(?:(?:really|just|actually|absolutely|properly|simply)\s+)*"
    r"(?:hate|hates|hated|dislike|dislikes|disliked|loathe|loathes|loathed|detest|detests|"
    r"detested|can'?t stand|cannot stand)\b.*$", re.I)
# "i like fish", "we love dogs", "not keen on rabbit", "not a fan of chicken": the animal is
# something they eat, or would rather not, and no animal is in the house.
LIKING_BEFORE = re.compile(
    r"\b(?:like|likes|liked|love|loves|loved|adore|adores|adored|hate|hates|hated|prefer|"
    r"prefers|preferred|keen on|a fan of|fan of|fond of|into|can'?t stand|cant stand|"
    r"crazy about|big on|dislike|dislikes|disliked|loathe|loathes|loathed|detest|detests|"
    r"detested|not\s+(?:\w+\s+)?(?:a fan of|keen on|into|fond of|big on))\s+(?:\w+\s+){0,2}$",
    re.I)
# A possessive settles it the other way round: "we love our dog" and "i adore my cat" are the
# animals they have, and the taste is about that animal, not the species.
OWNED_BEFORE = re.compile(r"\b(?:my|our|his|her|their|the|this|that)\s+$", re.I)


def _kept(thing):
    """The words of the thing that are kept, with the index each had in `thing`."""
    words = str(thing or "").split()
    kept = []
    for index, raw in enumerate(words):
        word = raw.strip(".,;:!?")
        if not word:
            continue
        if kept and (word.lower() in THING_STOP
                     or word.lower() in ("my", "our", "his", "her", "their", "your")):
            # A thing has one owner in it at most: "fish but my kids love it" ends at "fish".
            break
        if not kept and word.lower() in TAIL:
            continue
        kept.append((index, word))
    while kept and kept[-1][1].lower() in TAIL:
        kept.pop()
    if not kept or kept[0][1].lower() in NOT_A_THING:
        return []
    return kept


def _clean(thing):
    """The thing with its tail off ("curry tho" -> "curry"), or None when it names nothing."""
    kept = _kept(thing)
    if not kept:
        return None
    words = [word for _, word in kept]
    # "we love our dog" is a taste about the animal they have: the store reads it from the bot's
    # side, so the possessive becomes "your" ("you love your dog").
    if words[0].lower() in ("my", "our"):
        words[0] = "your"
    return " ".join(words)


def _thing_end(text, match):
    """Where the thing ends in the clause, so the words after it can be looked at."""
    took = text[match.start(1):match.end(1)]
    kept = _kept(took)
    if not kept:
        return match.start(1)
    last = took.split()[kept[-1][0]]
    return match.start(1) + took.rfind(last) + len(last)


# A taste is about a food or a drink, not about how much of it there is: "i dont drink enough
# water" and "i dont eat enough veg" are a shortfall someone wants to fix, and read as a taste
# they became `{"thing": "enough water", "how": "no"}` - a store that thinks they dislike
# water. The acknowledgement module files that as "Noted: you don't drink enough water.", which
# is the line said back and no help at all.
_QUANTITY = re.compile(r"^(?:enough|too much|too little|much|any|more|less|loads of|lots of|"
                       r"plenty of|a lot of|as much)\b", re.I)
# The quantity can also arrive as emphasis after the thing - "i dont drink water at all", "i dont
# eat meat any more" - and the tail list strips it before the check above can see it. Only the
# shortfall verbs are read this way: "i dont like water at all" is a dislike, not a shortfall.
_SHORTFALL_TAIL = re.compile(r"\b(?:at\s+all|any\s?more)\s*$", re.I)
_SHORTFALL_VERB = re.compile(r"\b(?:eat|drink)\s+$", re.I)


def _read_clause(text):
    """`(the taste in the clause, where in the clause it ends)`, or `(None, None)`.

    The end is what lets a caller tell a line that is nothing but a taste from one that only
    starts with one ("i hate cats so what should i cook").
    """
    text = " ".join(str(text or "").split())
    if not text or text.endswith("?"):
        return None, None  # "do i like fish?" is a question about them, not a taste they have
    for pattern, how in ((UNSURE, "unsure"), (NO, "no"), (NOT_KEEN, "no"), (MY_THING, "no"),
                         (YES, "yes")):
        match = pattern.search(text)
        if match:
            raw = match.group(1)
            if re.match(r"\s*to\b", raw):
                # "i dont want to lose the house", "i want to stop drinking": the verb is about
                # something they mean to do, not about a thing they like or dislike, and the
                # taste reader read "lose the house" as the thing.
                return None, None
            thing = _clean(raw)
            # `_kept` drops a leading quantity ("much water" -> "water"), so the check is made on
            # the words as they came as well as on the cleaned thing. Without it "i dont drink
            # much water" was filed as a dislike of water and said back as "Noted: you don't
            # drink much water."
            shortfall = _SHORTFALL_VERB.search(text[:match.start(1)])
            if thing and not _QUANTITY.match(thing) and not _QUANTITY.match(raw.strip()) \
                    and not (shortfall and _SHORTFALL_TAIL.search(raw)):
                return {"thing": thing, "how": how}, _thing_end(text, match)
    match = HATE.search(text)
    if match:
        # "i hate my job" is about their week, not a taste: the possessive mark on the cleaned
        # thing ("your job") is how that is told apart from "i hate cats".
        raw = match.group(1)
        thing = _clean(raw)
        if thing and not re.match(r"\s*(?:my|our)\b", raw, re.I):
            return {"thing": thing, "how": "no"}, _thing_end(text, match)
    return None, None


def read(line):
    """The taste in the line as `{"thing", "how"}`, or None.

    `how` is "unsure" ("not sure if i like curry"), "no" ("i don't think i like fish") or "yes"
    ("i love dogs"). Unsure is kept apart on purpose: it is a hedge, not a dislike.
    """
    return _read_clause(line)[0]


# A taste verb, with or without the person in front of it: the second half of "i like tea and i
# hate coffee" starts with both, and of "i love dogs but hate cats" with only the verb.
_TASTE_VERB = (r"(?:(?:i|we|he|she|they)\s+)?(?:do\s+|really\s+|absolutely\s+|just\s+|"
               r"actually\s+|properly\s+)?"
               r"(?:like|love|adore|prefer|hate|hates|dislike|dislikes|loathe|detest|enjoy|"
               r"eat|drink|want|can'?t stand|cannot stand)\b")
# One line can hold two tastes of opposite polarity: "i like dogs but i hate cats", "i love dogs
# but hate cats", "i like tea and i hate coffee", "i dont like fish; i love prawns". The clause
# split is only made where a taste verb follows the joiner, so "i like fish and chips" stays one
# thing and "fish and chips" is not two tastes.
_CLAUSE_SPLIT = re.compile(r"\s*;\s*|\s+(?:but|and|though|whereas)\s+(?=" + _TASTE_VERB + r")",
                           re.I)


# The shapes of a question that asks how to do something, which a taste word inside it cannot
# turn into a preference: "how do i eat healthier if i hate cooking" is a question about the
# plate, and "i hate cooking" is the obstacle in it.
_ASK_FORM = re.compile(r"\b(?:how (?:do|can|should|could) i|how to|what should i|"
                       r"what can i|what could i|any (?:tips|advice|ideas|suggestions)?"
                       r"|where (?:do|should) i start|is there a way)\b", re.I)
# A line that asks for a thing is not a line of tastes, however many tastes are in it: "i need a
# new podcast for my commute, i like history" is a request for the podcast, and the taste is how to
# make the pick. Read as a taste it was said back as "Noted: you need a new podcast for your
# commute..." while the podcast row - which answers the same line with the comma left out, or with
# "and" in it - sat one reader away. The asking shapes are the ones that want an answer, not a
# note: recommend, suggest, any good, what should i watch, i need a, i'm looking for. "i want a
# dog but i hate cats" is deliberately not one of them: wanting is a wish the store keeps, and it
# is not a request this module has anything to answer.
_ASKS_FOR_A_THING = re.compile(
    r"\b(?:recommend|recommendations?|suggest|suggestions?)\b"
    r"|\b(?:any|got any|have you got any)\s+good\b"
    r"|\bgive me (?:a|an|some|a few|your)\b"
    r"|\bwhat should i (?:watch|read|listen to|see|get|buy|cook|make for|eat|play|do with)\b"
    r"|\bhelp me (?:pick|choose|find|decide)\b"
    r"|\bi(?:'m| am) looking for\b"
    r"|\bi need (?:a|an|some|a few|new|ideas?|advice|help)\b"
    # "i want a new series on netflix, i like history" is the same request as "recommend a
    # series": wanting a medium is wanting one of them named, not a taste to keep.
    r"|\bi(?:'d| would)? want (?:a|an|some) (?:new |good |different )?"
    r"(?:film|movie|series|show|boxset|book|novel|podcast|audiobook|album|playlist|song)\b"
    r"|\bwhere can i (?:get|buy|find)\b", re.I)


# The chores people name when the obstacle is the doing, not the food: "i hate cooking", "i hate
# the gym", "i hate meal prep". A disliked food is not in here on purpose.
_HATED_CHORE = re.compile(r"\b(?:hate|hates|dislike|dislikes|loathe|detest|can'?t stand|"
                          r"cannot stand|don'?t like|do not like)\s+(?:to\s+)?"
                          r"(?:cook|cooking|bake|baking|prep|prepping|meal prep|exercise|"
                          r"exercising|the gym|working out|run|running|clean|cleaning|iron|"
                          r"ironing|tidy|tidying|shop|shopping|wash|washing|diet|dieting)\b", re.I)


def read_all(line):
    """Every taste in the line, in the order they said it.

    `read()` answers with one taste, which is wrong for a line that holds two with different
    polarity: "i like dogs but i hate cats" was kept as the single thing "dogs but i hate cats",
    so the store called a dislike a like and said the person's own "i" back to them.
    """
    text = " ".join(str(line or "").split())
    found = []
    for clause in _CLAUSE_SPLIT.split(text):
        clause = clause.strip()
        if not clause:
            continue
        if re.match(_TASTE_VERB, clause, re.I) and not re.match(r"(?:i|we|he|she|they)\b",
                                                               clause, re.I):
            clause = "i " + clause  # "hate cats" carries the person from the clause before it
        taste = read(clause)
        if taste and taste not in found:
            found.append(taste)
    return found


def only_a_taste(text):
    """Whether the line says nothing but tastes of theirs, one per clause.

    "i like dogs but i hate cats" is a preference, not a household: an entry about introducing a
    dog to a cat used to answer it ("keep them apart behind a baby gate"), because the line has
    the two animals and the word "hate" in it. The store is what answers a taste, so the
    knowledge base keeps out of a line that is only tastes. A line that carries anything else
    ("i hate cats so what should i cook") is not this one.
    """
    text = " ".join(str(text or "").split())
    if not text or "?" in text:
        return False
    # A how-to that names a chore they hate is a how-to: "how do i eat healthier if i hate
    # cooking" is a question about the plate, and "i hate cooking" is the obstacle in it, not a
    # taste to file away. Read as a taste the line went to the memory store and got no answer at
    # all. Only the chores are let through: "what should i cook i hate fish" is naming a food they
    # do not want, and that line still belongs to the dislike reply, not to a fish recipe.
    if _ASK_FORM.search(text) and _HATED_CHORE.search(text):
        return False
    # A request for a thing is answered, not noted, whatever tastes are attached to it. The
    # reading of a taste is unchanged, so the store still knows what they like; it is only the
    # "nothing here but tastes" verdict that this line does not qualify for.
    if _ASKS_FOR_A_THING.search(text):
        return False
    seen = False
    for clause in _CLAUSE_SPLIT.split(text):
        clause = clause.strip()
        if not clause:
            continue
        said = clause
        bare = re.match(_TASTE_VERB, said, re.I) and not re.match(r"(?:i|we|he|she|they)\b",
                                                                 said, re.I)
        if bare:
            said = "i " + said  # "hate cats" carries the person from the clause before it
        taste, end = _read_clause(said)
        if not taste:
            return False
        left = said[end:] if not bare else said[end:]
        if set(re.findall(r"[a-z']+", left.lower())) - TAIL:
            return False
        seen = True
    return seen


def said_about(text, position):
    """Whether the animal at `position` is what a taste in the line is about, not their own pet."""
    before = text[max(0, position - 30):position]
    if not LIKING_BEFORE.search(before):
        return False
    return not OWNED_BEFORE.search(text[max(0, position - 12):position])


# "do i like fish?", "am i still into cats?", "did i say i liked olives?": a question about a taste
# of theirs, not about the fish. It is the same words a taste arrives in, so it is kept here, next
# to `read()`, and both the store (which answers it) and the knowledge base (which must keep out of
# it) ask this one question about the line.
# Only a line that is the ask gets it: "how do i like my steak cooked" carries "do i like" and is a
# question about the steak, so the ask has to open the line, after no more than a filler word.
_ASK_START = r"^\W*(?:(?:so|and|but|ok|okay|hmm|oh|well|wait)\b[,.]?\s+)*"
_ASK_ADVERB = r"(?:(?:still|really|actually|even|now|just|ever)\s+)*"
ASKS_ABOUT_A_TASTE = re.compile(
    _ASK_START + r"(?:(?:do|did|does)\s+(?:i|we)\s+" + _ASK_ADVERB +
    r"(?:like|love|enjoy|eat|drink|want)\b"
    r"|am\s+i\s+" + _ASK_ADVERB + r"(?:a fan of|into|keen on|mad about|fussed on)\b"
    r"|did\s+i\s+say\s+i\s+(?:like|liked|love|loved|hate|hated)\b)", re.I)
# The same ask with the verb taken out, so what is left is the thing asked about.
TASTE_ASKED_ABOUT = re.compile(
    _ASK_START + r"(?:(?:do|did|does)\s+(?:i|we)\s+" + _ASK_ADVERB +
    r"(?:like|love|enjoy|eat|drink|want)\s+"
    r"|am\s+i\s+" + _ASK_ADVERB + r"(?:a fan of|into|keen on|mad about|fussed on)\s+"
    r"|did\s+i\s+say\s+i\s+(?:like|liked|love|loved|hate|hated)\s+)", re.I)


def asks_about_a_taste(line):
    """True when the line is a question about a taste of theirs ("do i like fish?")."""
    return bool(ASKS_ABOUT_A_TASTE.search(str(line or "")))


# "what do i like?", "what do you know i like?", "what are my favourite things?": the ask for the
# tastes themselves, which is answered as the short list rather than as the whole summary.
ASKS_FOR_TASTES = re.compile(
    _ASK_START + r"(?:(?:what|which)\b[^?.!]*?\bdo\s+(?:i|we)\s+" + _ASK_ADVERB +
    r"(?:like|love|enjoy|eat|drink)\b"
    r"|(?:what|which)\s+(?:are|were)\s+my\s+(?:favou?rite|best)\s+\w+"
    r"|do\s+you\s+(?:know|remember)\s+what\s+(?:i|we)\s+(?:like|love)\b"
    r"|what\s+do\s+you\s+know\s+(?:that\s+)?i\s+(?:like|love)\b)", re.I)


# A taste somebody else has. Every reader above matches "i"/"we", because a taste was the
# person's own; the store keeps facts about the people they mention too (memory["others"]), and
# "my sister loves cooking" read as nothing at all - the sister was filed as a person the chat
# had named and what she likes was lost, so "what does my sister like" a turn later was a search
# hedge about somebody the chat had just told the bot about.
_OTHER_OWNER = re.compile(
    r"^(?:(?:my|our)\s+(?P<who>[a-z][a-z'\u2019-]{1,20})"
    r"|(?P<pronoun>she|he|they))"
    # "she's vegetarian", "hes a laugh", "theyre both eight": the contraction is the same person
    # and the same clause, and without it the whole line went unread ("she's vegetarian and cant
    # stand museums" kept the diet and lost the dislike).
    r"(?:'?s|'?re)?"
    # The rest of the clause can open with anything: "shes 7 and loves dinosaurs" has a figure
    # straight after the person, and a rest that had to open with a letter left the line unread,
    # so the taste in its second clause was lost. The taste verb is what `_OTHER_TASTE` asks for.
    r"\s+(?P<rest>.*)$", re.I)
# The verb the taste arrives in, rewritten to the one the reader above understands. Ordered, the
# "doesn't"/"isn't" forms first: "she doesnt like olives" carries the word "like" and would
# otherwise be read as her liking them.
_OTHER_SAYS = (
    (r"(?:isn'?t|is\s+not|wasn'?t|was\s+not)\s+(?:that\s+|really\s+|very\s+|all\s+that\s+)?"
     r"(?:into|keen\s+on|a\s+fan\s+of|mad\s+about|fussed\s+on|big\s+on)", "don't like"),
    (r"(?:doesn'?t|does\s+not|doesnt|won'?t|will\s+not|never|can'?t|cannot|can\s+not)\s+"
     r"(?:really\s+|actually\s+|ever\s+)?(?:like|love|eat|drink|stand|touch|want|have|"
     r"be\s+keen\s+on)", "don't like"),
    (r"(?:hates?|loathes?|detests?|dislikes?|can'?t\s+stand|cannot\s+stand)", "hate"),
    (r"is\s+(?:really\s+|absolutely\s+|just\s+|very\s+)?"
     r"(?:into|keen\s+on|mad\s+about|a\s+fan\s+of|big\s+on|fussed\s+on|fond\s+of)", "like"),
    (r"(?:loves?|likes?|adores?|prefers?|enjoys?)", "love"),
)
_OTHER_VERB = "|".join("(?:%s)" % pattern for pattern, _ in _OTHER_SAYS)

# One line about somebody holds more than one taste, and often the person's name only once:
# "my son is 8 and loves dinosaurs" (the age was kept and the taste was lost), "she's vegetarian
# and cant stand museums" (the diet was kept and the dislike was lost), "my mum loves cats, hates
# dogs and is allergic to both". The clause split is made where a taste verb follows the joiner -
# the same rule the person's own tastes are read by - so "she loves curry and rice" stays one
# thing, and every clause after the first takes the person the line already named.
_OTHER_CLAUSE = re.compile(
    r"\s*;\s*|\s*,\s*|\s+(?:but|and|so|though|whereas|while)\s+"
    r"(?=(?:[a-z][a-z'\u2019-]{1,20}\s+)?(?:" + _OTHER_VERB + r")\b)", re.I)
# A clause that may follow the taste: it has to open as a new clause of its own, not as the thing
# carried on by "and" ("curry and rice" is one thing) or as a predicate about it ("is rubbish").
_A_CLAUSE_AFTER = re.compile(
    r"^\s*[,;:]?\s*(?:so|but|and|because|cos|cause|though|although|whereas|yet|if|then|"
    r"when|while|as)\b", re.I)
# The same clause, when it asks the bot something: "she loves cooking so what do i cook" is a
# request for a recipe, and the taste in front of it is how the request is made, not a fact.
_ASKS_SOMETHING = re.compile(
    r"\b(?:what|how|why|when|where|which|who|whose|whats|what's|should|shall|could|would|"
    r"any ideas|any tips|recommend)\b", re.I)
_OTHER_TASTE = re.compile(
    r"^(?:really |absolutely |just |actually |properly |simply |still )?(?:" + _OTHER_VERB
    + r")\b", re.I)


def read_other(line):
    """Tastes somebody else has, as `[{"who"/"pronoun", "thing", "how"}]`.

    "my sister loves cooking", "she doesnt like olives", "he is mad about football": the person
    is the relation in front of the taste, or the pronoun when the line names nobody (the store
    fills that in from the person the chat is on). The taste itself is read by the reader above,
    on the clause rewritten as the person's own ("i love cooking"), so a quantity, a tail or a
    pronoun for a thing is refused here in exactly the same way, and a line that carries more
    than the taste ("she loves cooking so what do i cook") is not one.
    """
    text = " ".join(str(line or "").split())
    if not text or text.endswith("?"):
        return []
    found = []
    person = None
    for clause in _OTHER_CLAUSE.split(text):
        clause = clause.strip()
        if not clause:
            continue
        match = _OTHER_OWNER.match(clause)
        if match:
            person = ({"who": match.group("who").lower()} if match.group("who")
                      else {"pronoun": match.group("pronoun").lower()})
            clause = match.group("rest")
        if person is None:
            # Nobody has been named yet, so a taste with no subject of its own ("cant stand
            # museums") belongs to nobody this reader can name.
            continue
        said = _OTHER_TASTE.match(clause)
        if not said:
            continue
        tasted = _their_taste_in(clause, said)
        if tasted:
            found.append({**tasted, **person})
    return found


def _their_taste_in(rest, said):
    """The taste one clause gives, read as the person's own ("i love cooking"), or None."""
    verb = said.group(0).strip()
    thing = rest[said.end():].strip()
    as_own = "love"
    for pattern, rewritten in _OTHER_SAYS:
        if re.fullmatch(pattern, verb, re.I):
            as_own = rewritten
            break
    if not thing:
        return None
    clause = "i " + as_own + " " + thing
    taste, end = _read_clause(clause)
    if not taste:
        return None
    left = clause[end:]
    words = set(re.findall(r"[a-z']+", left.lower()))
    if words - TAIL:
        # What is left over is a second clause of its own ("he hates walking so keep it short",
        # "she loves cooking so what do i cook") or the thing carried on ("curry and rice").
        # Only a clause that starts where the taste ends can follow it, and never one that asks
        # the bot something: "so what do i cook" is a request, and the taste in front of it is
        # not a fact the store keeps.
        if not _A_CLAUSE_AFTER.match(left) or _ASKS_SOMETHING.search(left):
            return None
    tasted = {"thing": taste["thing"], "how": taste["how"]}
    if re.search(r"\b(?:eat|eats|ate|drink|drinks|drank)\b", verb, re.I):
        # "she doesnt eat meat" is how she eats, which the diet reader already has: filed as a
        # dislike as well it would be two facts about one line, kept in two places.
        tasted["eaten"] = True
    return tasted
