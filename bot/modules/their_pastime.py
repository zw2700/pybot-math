"""What one of their people is into, does, or is coming down for: a question, not the line back.

A fact about one of their people - "my sister is into yoga", "my brother plays the guitar", "my
mother in law is coming on sunday" - was answered by filing it: "Noted: your sister is into
yoga." The words handed back, nothing asked. STYLE.md calls that the coldest reply there is.

This module reads the fact and asks the one thing anybody asks about a job, a hobby or a visit.
It answers nothing else, and it **only ever replaces a placeholder**: the composer's own reply is
read first (bot/compose/fallback.py), and unless that reply is the receipt or the listening line
this module stands down. So everything the rest of the bot already says better - the store's own
job, age and place readings, a loss, a worry, a safety line - keeps the turn.

Two things must never happen: the question must not be asked about a problem rather than a hobby
("my son is into drugs", "my husband is into another woman"), and it must not be asked on the
turn after a feeling, where the fact is the reason for the feeling.

It is one module's own reading, so it can be judged on its lines alone: it proposes nothing for a
line it does not read whole, and it passes on every line where the composer already has an
answer.
"""
import re

from ..compose import fallback
from ..compose import pick
from ..compose.remark import THEIR_PERSON, _the_job_in, fill_person, person_pronouns

PRIORITY = 300

THEIR_ANY = (r"(?:" + THEIR_PERSON + r"|father in law|mother in law|son in law|"
             r"daughter in law|sister in law|brother in law|friend|best friend|neighbour|"
             r"neighbor|mate|boss|aunty|auntie|boyfriend|girlfriend|other half|flatmate|"
             r"housemate|fella|missus|stepmum|stepdad|grandson|granddaughter)")
WHAT_THEY_ARE_INTO = (r"(?:loves|adores|likes|is obsessed with|is mad about|is nuts about)")
WHAT_THEY_DO = (r"(?:plays|does|collects|makes|teaches|runs|swims|sings|paints|draws|"
                r"bakes|cooks|gardens|reads|writes|dances)")
NOT_TAKEN_UP = frozenset((
    "smoking", "drinking", "gambling", "drugs", "cocaine", "heroin", "betting", "vaping",
    "the bottle", "fighting", "biting", "wetting", "stealing", "drink", "alcohol", "weed",
    "pills", "porn", "scratchcards", "debt", "self-harm", "harm", "cutting", "shouting",
    "bottle", "cans", "booze",
))
# A phrase, not a word: "into another woman" and "into trouble at school" are a worry about a
# person and a worry about a child, and the pool's "How did he get into that?" asked of them is
# the worst line in the file. The words are ordinary on their own ("a woman", "school"), so they
# are read as phrases.
NOT_TAKEN_UP_PHRASES = (
    "another woman", "another man", "another bloke", "another person", "another fella",
    "another lad", "another girl", "someone else", "somebody else", "an affair", "an ex",
    "his ex", "her ex", "the ex", "a row", "rows", "arguing", "arguments", "a fight",
    "trouble", "the police", "a gang", "crime", "money he hasnt got", "the horses",
)
THEIR_INTO = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? (?:is|are) "
    r"(?:really |well |properly |totally |so )?into (?P<thing>[a-z][a-z' \-]{1,22})$")
THEIR_LOVES = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? " + WHAT_THEY_ARE_INTO +
    r" (?P<thing>[a-z][a-z' \-]{1,22})$")
THEIR_DOES = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? " + WHAT_THEY_DO +
    r" (?:in |with |for |at )?(?P<thing>[a-z][a-z' \-]{1,22})$")
# A visit with a time on it ("my father in law is coming on sunday", "my mother in law is
# staying for a week"). The time is what makes it a visit rather than a person being moved
# somewhere, so a line without one - "my mum is coming home from hospital" - is left alone.
# A thing taken up ("my mum has taken up painting"). The ones nobody takes up for pleasure -
# smoking, drinking, gambling - are left to the modules that answer a worry.
THEIR_TOOK_UP = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? (?:has|have) (?:just |recently )?"
    r"(?:taken up|got into|started) (?P<thing>[a-z][a-z' \-]{1,22})$")
# "my uncle keeps bees". A verb that takes a plural noun and nothing else, because "keeps
# criticising me" and "keeps moving the goalposts" are a complaint about a person and not a
# hobby of theirs, and the question "how long has he been doing that?" is nonsense on them.
THEIR_KEEPS = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? keeps (?:some |a few |two |three )?"
    r"(?P<thing>[a-z]{2,12}s)$")
# "my niece is good at drawing". Said with the same words as "my son is good with numbers", it is
# a thing they do and the question the does-pool asks fits it.
THEIR_GOOD_AT = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? (?:is|are) "
    r"(?:really |very |so |quite )?good at (?P<thing>[a-z][a-z' \-]{1,22})$")
THEIR_VISIT = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? (?:is|are) "
    r"(?:coming|visiting|staying) (?P<when>(?:on |at |this |next |for |in |over )"
    r"[a-z0-9' \-]{1,24})$")
# "my best friend is a vet" is a job said with an indefinite article. The trade is the store's own
# list through the composer's _the_job_in, so a word that is not a trade cannot become one: "my
# dad is a nightmare" and "my brother is a handful" have no job in them. The composer's own
# reading of a relative's job is warmer than this pool, and the placeholder guard below keeps it,
# so this only ever answers where that reading missed the person - a friend, a mate, a boss.
THEIR_IS_A_ROLE = re.compile(
    r"^my (?P<person>" + THEIR_ANY + r")(?:'?s)? (?:is|works as) (?:a|an) "
    r"(?P<role>[a-z][a-z'\-]{2,20})$")

THEIRS_ROLE_LINES = (
    "{Job}. What does a normal day look like for {them}?",
    "{Job}. Is that what {they} always wanted to do?",
    "{Job} — how long {has} {they} been at it?",
)

THEIRS_INTO_LINES = (
    "How did {they} get into that?",
    "Is that a new thing, or {has} {they} always been into {it}?",
    "Are you into {it} too, or is that {their} thing?",
    "What got {them} started on {it}?",
)
# What the person loves rather than what they are into ("my daughter loves dinosaurs"). "likes
# best" is the question for somebody who has just been given a favourite thing.
THEIRS_LOVES_LINES = (
    "What {do} {they} like most about {it}?",
    "How did that start?",
    "Do you get roped in too?",
    "Did {they} get you into {it} as well?",
)
# What the person does with their week: "my brother plays the guitar", "my mum sings in a
# choir", "my uncle keeps bees". The one question every one of those lines can take.
THEIRS_DOES_LINES = (
    "How long {has} {they} been doing that?",
    "How often {do} {they} do it?",
    "Do you ever go and watch?",
    "What is {their} favourite bit of it?",
)
# Good at a thing is not the same as doing it in front of people: "my son is good at maths" has no
# audience, so this pool asks where it came from and whether anybody else sees it.
THEIRS_GOOD_AT_LINES = (
    "How long {has} {they} been at that?",
    "Is it a class, or something {they} {do} at home?",
    "Where did {they} learn that?",
    "Do they get much chance to show it off?",
)
# A visit with a time on it: "my father in law is coming on sunday". The visit is the news, and
# the one thing anybody asks about a visit is how long it is and where they sleep.
THEIRS_VISIT_LINES = (
    "{is} {they} staying with you, or nearby?",
    "Is it a flying visit, or a long one?",
    "Are you looking forward to it?",
    "How much of the week is that taking up?",
)

def _starts_a_sentence(line):
    """The pool line with its first letter capitalised, since it opens the reply.

    One line begins with the verb in front of the pronoun - "{is} {they} staying with you" - and
    "is she staying" is not how a sentence starts.
    """
    said = str(line or "")
    return said[:1].upper() + said[1:] if said else said


def _the_turn_before_was_a_feeling(clean, memory):
    """True when the last line they said was a feeling, so this fact is the reason for it.

    The reading is the store's own (bot/memory/ack.py): a fact added the turn after a feeling is
    the explanation of that feeling, and it keeps the reply the store has for it.
    """
    from ..memory import ack
    read = getattr(ack, "_after_a_feeling", None)
    return bool(read and read(clean, memory))


def _a_thing_nobody_is_into(thing):
    """True for the things that are a problem rather than a hobby ("is into drugs").

    A phrase is read first, because the words in "another woman" and "trouble at school" are
    ordinary words that mean nothing on their own.
    """
    said = " ".join(str(thing or "").lower().split())
    if any(phrase in said for phrase in NOT_TAKEN_UP_PHRASES):
        return True
    parts = [word for word in re.split(r"[^a-z\-]+", said) if word]
    return any(word in NOT_TAKEN_UP for word in parts)


# A thing in the plural, so the pool line says "them" rather than "it". The last word is what
# decides, because "dinosaurs" and "boxes" are the thing and "chess", "darts" and "news" are not
# plural at all even though they end in s.
NOT_PLURAL = frozenset((
    "chess", "darts", "news", "gymnastics", "athletics", "bowls", "skittles", "billiards",
    "physics", "maths", "mathematics", "business", "class", "glass", "bass", "gas", "bus",
    "christmas", "tennis", "series", "species", "means", "this", "his", "hers", "its",
))


def _a_plural_thing(thing):
    """True when the thing named is plural, so the reply says "them" and not "it"."""
    words = [word for word in re.split(r"[^a-z\-]+", str(thing or "").lower()) if word]
    if not words:
        return False
    last = words[-1]
    if last in NOT_PLURAL or len(last) < 4:
        return False
    return last.endswith("s") and not last.endswith(("ss", "us", "is", "ous"))


def _it_word(thing):
    """The word the pool line uses for the thing: "them" for dinosaurs, "it" for baking."""
    return "them" if _a_plural_thing(thing) else "it"





# Things that are done in front of somebody, where "do you ever go and watch" is a question a
# friend would ask. Everything else is done on its own: a guitar, a pottery class, a bee hive and
# a painting are not something you go and watch, and the pool cannot offer to.
BEFORE_AN_AUDIENCE = frozenset((
    "football", "rugby", "cricket", "tennis", "netball", "hockey", "athletics", "racing",
    "races", "matches", "dancing", "ballet", "singing", "choir", "gigs", "bands", "drama",
    "theatre", "plays", "stand up", "swimming", "speedway", "boxing", "darts", "golf",
))


def _watched(thing):
    """True when the thing named is one somebody watches as well as does."""
    words = [word for word in re.split(r"[^a-z]+", str(thing or "").lower()) if word]
    if any(word in BEFORE_AN_AUDIENCE for word in words):
        return True
    return " ".join(words) in BEFORE_AN_AUDIENCE


def _does_pool(thing):
    """The pool for a thing they do, without the audience question for a thing done alone."""
    if _watched(thing):
        return THEIRS_DOES_LINES
    return tuple(line for line in THEIRS_DOES_LINES if "watch" not in line)


def _fill_it(line, person_word, it_word="it"):
    """The pool line with the person's pronouns, the verb that agrees, and the thing's number.

    {they} and the rest of the pronouns are the store's own fill_person (bot/compose/remark.py);
    {has}, {is} and {it} are this pool's, because the verb in front of the pronoun and the number
    of the thing are facts about the line rather than about the person. A line that opens on one
    of them is capitalised once it is filled.
    """
    they, them, their, do, are = person_pronouns(person_word)
    said = fill_person(line, person_word)
    said = (said.replace("{has}", "have" if do == "do" else "has")
                .replace("{is}", "are" if are == "are" else "is")
                .replace("{it}", it_word))
    # A pool line written with the verb spelled out ("how long has {they} been at it") has to
    # agree with whoever the person is: a best friend or a partner is a "they", and "has they"
    # is not a sentence anybody says.
    said = (said.replace("has they", "have they").replace("Has they", "Have they")
                .replace("is they", "are they").replace("Is they", "Are they")
                .replace("does they", "do they").replace("Does they", "Do they"))
    return said[:1].upper() + said[1:] if said else said


def reading(clean, words, memory):
    """The pool line for a whole-line fact about one of their people, or None."""
    if _the_turn_before_was_a_feeling(clean, memory):
        return None
    match = THEIR_IS_A_ROLE.match(clean)
    if match:
        job = _the_job_in(match.group("role"))
        if job:
            return _fill_it(pick(THEIRS_ROLE_LINES, memory, clean).replace("{Job}", job),
                            match.group("person"))
    match = THEIR_INTO.match(clean)
    if match and not _a_thing_nobody_is_into(match.group("thing")):
        return _fill_it(pick(THEIRS_INTO_LINES, memory, clean), match.group("person"),
                        _it_word(match.group("thing")))
    match = THEIR_LOVES.match(clean)
    if match and not _a_thing_nobody_is_into(match.group("thing")):
        return _fill_it(pick(THEIRS_LOVES_LINES, memory, clean), match.group("person"),
                        _it_word(match.group("thing")))
    match = THEIR_DOES.match(clean)
    if match and not _a_thing_nobody_is_into(match.group("thing")):
        return _fill_it(pick(_does_pool(match.group("thing")), memory, clean),
                        match.group("person"))
    match = THEIR_GOOD_AT.match(clean)
    if match and not _a_thing_nobody_is_into(match.group("thing")):
        return _fill_it(pick(THEIRS_GOOD_AT_LINES, memory, clean), match.group("person"))
    match = THEIR_KEEPS.match(clean)
    if match:
        return _fill_it(pick(THEIRS_DOES_LINES, memory, clean), match.group("person"))
    match = THEIR_TOOK_UP.match(clean)
    if match and not _a_thing_nobody_is_into(match.group("thing")):
        return _fill_it(pick(_does_pool(match.group("thing")), memory, clean),
                        match.group("person"))
    match = THEIR_VISIT.match(clean)
    if match:
        return _fill_it(pick(THEIRS_VISIT_LINES, memory, clean), match.group("person"))
    return None


# The replies that hand a person their own words back, or say nothing about what they said. This
# module is for those and nothing else (STYLE.md, "The reply a person actually gets").
PLACEHOLDER_OPENINGS = (
    # "got it." without the full stop, because the composer writes the echo with an em dash and
    # keeps the full stop for its own "Noted:" line: "Got it — my brother plays the guitar."
    # is the same fault as "Noted: your brother plays the guitar.", and a person who says their
    # brother plays the guitar should not hear either.
    "noted", "i'm listening", "i am listening", "got it", "ok.", "that's noted",
    "thanks for telling me", "i don't know enough", "i dont know enough",
    "that's beyond what i know", "thats beyond what i know", "i'm not sure about that one",
    "im not sure about that one",
)


def _is_a_placeholder(said):
    """True when the composer's own reply for this line is one of the placeholder shapes."""
    text = str(said or "").strip().lower()
    return any(text.startswith(opening) for opening in PLACEHOLDER_OPENINGS)


# The turn before decides the pool as much as the line itself: a hobby question asked straight
# after "my mum has dementia" reads as not listening. fallback's own read of heavy news misses the
# people who are ill in their own way ("my son is being bullied", "my friend is very ill"), and a
# relative with a hobby in the same breath is that thread's news, not a new subject.
HEAVY_IN_THE_THREAD = re.compile(
    r"\b(?:bull(?:y|ied|ying)|bullies|ill|unwell|poorly|poorlier|sick|sicker|sickness|diagnos\w*|"
    r"cancer|tumou?r|chemo\w*|radiotherap\w*|dementia|alzheim\w*|parkinson\w*|stroke|sepsis|"
    r"pneumonia|surgery|operation|transplant|dialysis|hospice|palliative|terminal|sectioned|"
    r"sectioning|depress\w*|anxiety|anorexi\w*|bulimi\w*|addict\w*|relapse\w*|overdose\w*|"
    r"self[- ]harm|suicidal|miscarr\w*|stillborn|funeral|burial|cremat\w*|griev\w*|bereave\w*|"
    r"died|dying|death|passed away|lost (?:him|her|them|my)|hospital|icu|a&e|ambulance|"
    r"in pain|suffering|struggling|carer|carers|dementia)\b")


def _the_thread_is_heavy(memory):
    """True when the line just before this one was a person ill, lost, bullied or in hospital."""
    before = fallback._the_line_before(memory) if hasattr(fallback, "_the_line_before") else ""
    if not before:
        turns = [turn for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)]
        before = str(turns[-1].get("user") or "") if turns else ""
    said = str(before or "").lower()
    if not said:
        return False
    if fallback._reads_as_heavy_news(said):
        return True
    return bool(HEAVY_IN_THE_THREAD.search(said))


def respond(text, memory):
    """The turn for a fact about one of their people, when nothing better answers it."""
    if not text or "?" in text:
        return None
    clean = re.sub(r"[^a-z0-9' ]+", " ", str(text).lower())
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean.startswith("my "):
        return None
    # A heavy thread keeps the turn: the person's news is the thing being told, and a question
    # about their sister's yoga class is not an answer to it.
    if _the_thread_is_heavy(memory):
        return None
    mine = reading(clean, clean.split(), memory)
    if not mine:
        return None
    # Only ever a placeholder replaced: whatever the composer says for this line that is not a
    # receipt (a job, an age, a place, a loss, a worry, a safety line) keeps the turn.
    theirs = None
    try:
        theirs = fallback.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a composer that cannot answer leaves this module its turn
        theirs = None
    if theirs and not _is_a_placeholder(theirs):
        return None
    return mine
