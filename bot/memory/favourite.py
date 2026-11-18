"""A favourite named in a line, and the ask for it back.

"my favourite colour is green" is a fact about the person, and the conversation lane keeps
facts about the person. This one had no slot, so two things went wrong on the same line and
then on the next one:

* the line was not kept at all. The composer still said it back ("Your favourite food is curry
  - noted."), so the chat recorded a favourite the store did not have. A colour was worse: the
  knowledge base found the word "green" and painted a wall ("White or cream lets green breathe,
  then pink, mustard or brown leather"), and the person's own line was answered with decorating
  advice;
* "what is my favourite colour" was then not a recall of anything, and the composer answered it
  with the paragraph it had just given ("Same as before: White or cream lets green breathe..."),
  which is the coldest shape the bot has: it repeats the thing that was wrong instead of
  saying the one word they asked for.

The slot is the general one, so it covers every favourite people actually name - a colour, a
food, a film, a book, a team, a song, a place. Nothing here knows what any of those are: the
thing is the word after "favourite" and the value is whatever the person put after "is", which
is why "my favourite film is alien" and "my favourite colour is a dark green" both work.

What counts as a value is deliberately narrow, because a wrong value is worse than no value:
the line has to be a statement (a "?" on the end passes), the value has to be a thing rather
than a clause, and a line that says what somebody *else* likes ("my mum's favourite colour is
green") is not the user's own and passes.

Only the person's own favourite is read, in the shapes people type: "my favourite X is Y",
"my favourite X's Y", "my fav X is Y". The ask is the same thing read backwards - "what is my
favourite X", "whats my favourite X again", "do you know my favourite X", "what did i say my
favourite X was" - and it names the thing, so the answer is that one fact and not the whole
picture.
"""
import re

# Chat-speak lead-ins people put in front of a line: "so my favourite colour is green".
LEAD = re.compile(r"^\s*(?:(?:so|and|but|oh|ah|well|also|btw|right|ok|okay|hmm)[\s,.!;-]+)+", re.I)

# The line's own favourite: "my favourite colour is green".
SAYS = re.compile(
    r"^\s*(?:my|our)\s+(?:favou?rite|fav|best)\s+"
    r"(?P<thing>[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,2}?)"
    r"\s*(?:is|are|'s|was|will be|has to be|would be)\s+"
    r"(?P<value>[^?.!;]{1,60}?)\s*$", re.I)

# Somebody else's favourite: "my mum's favourite colour is green", "his favourite food is pie".
# Not the user's own line, so the store keeps nothing and the composer says it back.
SOMEONE_ELSE = re.compile(
    r"^\s*(?:my|our)\s+[a-z][a-z'\u2019-]*'?s?\s+(?:favou?rite|fav|best)\b"
    r"|\b(?:his|her|their|your)\s+(?:favou?rite|fav|best)\b", re.I)

# "best" is how people say "favourite" ("my best dish is a roast"), but a best friend, a best
# mate or a best man is a person, not a favourite. Read as one, "my best friend is moving away"
# was kept as "your favourite friend is moving away" and the answer about a friend moving away
# was replaced by that note - in eight lines out of twelve, some of which had a good answer.
BEST_PERSON = re.compile(
    r"\bbest\s+(?:friends?|mates?|man|buddy|bud|buddies|bestie|besties|pals?|friend's|mate's|"
    r"friendship)\b", re.I)

# The thing a favourite is of, said the other way round: "green is my favourite colour".
IS_MINE = re.compile(
    r"^\s*(?P<value>[a-z][a-z'\u2019 -]{1,40}?)\s+(?:is|are|has always been|'s)\s+"
    r"my\s+(?:favou?rite|fav|best)\s+"
    r"(?P<thing>[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,2})\s*$", re.I)

# The ask: "what is my favourite colour", "whats my favourite film again", "what did i say my
# favourite food was", "do you know my favourite team". A team, a player, a singer or an author
# is asked with `who`, and the line is still the person's own favourite because the "your" guard
# above has already taken the bot's own away.
ASKS = re.compile(
    r"(?:\bwhat(?:'s|s| is| was| are| were)?|\bwho(?:'s|s| is| was| are| were)?|"
    r"\bwhich(?:\s+is|\s+one)?|\bdo you (?:know|remember)|"
    r"\bdid i (?:say|tell you)|\bcan you (?:remember|tell me))\b"
    r"[^?.!]{0,40}?\bmy\s+(?:favou?rite|fav|best)\s+"
    r"(?P<thing>[a-z][a-z'\u2019-]*(?:\s+(?!is\b|was\b|are\b|were\b)"
    r"[a-z][a-z'\u2019-]*){0,2})?"
    r"(?:\s+(?:is|was|again|then|though))?\s*[?.!]*\s*$", re.I)

# The ask the other way round: "which book is my favourite", "which colour is my favourite".
WHICH_IS = re.compile(
    r"^\s*which\s+(?P<thing>[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,2})"
    r"\s+(?:is|was)\s+my\s+(?:favou?rite|fav|best)\b", re.I)

# A favourite put right a turn later: "no wait its blade runner", "actually its blade runner",
# "sorry, i mean blade runner". The old value is not the person's favourite any more, and a chat
# that kept it would say the wrong film back for the rest of the conversation.
CORRECTS = re.compile(
    r"^\s*(?:no|nope|actually|sorry|wait|no wait|i mean|rather|scratch that|make that|"
    r"not that|that's wrong|thats wrong)\b[\s,.!-]+"
    r"(?:its|it's|it is|i mean|make it|i meant|just)\s+"
    r"(?P<value>[^?.!;]{1,60}?)\s*$", re.I)

# A favourite changed out loud, without the word "favourite": "i prefer blue now", "i like the
# sequel better now", "i prefer oat milk these days". The thing is not named, so this only means
# something right after a favourite was given or asked about - the caller decides that, and this
# only reads the value.
PREFERS_NOW = re.compile(
    r"^\s*(?:i|we)\s+(?:prefer|like)\s+(?P<value>[^?.!,;]{1,40}?)\s*"
    r"(?:now|nowadays|these days|better now|more now|better these days|more these days|better|more)"
    r"\s*$", re.I)

# The ask for all of them at once: "what are my favourites", "what have i told you i like",
# "what do you know about my favourites". Plural, so there is no one thing it names.
ASKS_ALL = re.compile(
    r"\b(?:what|which)\b[^?.!]{0,30}?\bmy\s+(?:favou?rite|fav)s\b|"
    r"\bwhat\s+(?:have\s+i|did\s+i)\s+(?:told|said\s+to)\s+you\b[^?.!]{0,20}\b(?:like|love|prefer)\b|"
    r"\bwhat\s+do\s+you\s+know\s+about\s+my\s+(?:favou?rite|fav)s\b", re.I)

# What somebody answers when the bot has just asked them for a favourite: "green", "the big
# lebowski", "curry, probably". Nothing but the value, so only a short line with no verb of its
# own counts.
AN_ANSWER = re.compile(r"^\s*[a-z0-9][a-z0-9'\u2019 ,-]{0,40}\s*[.!]?\s*$", re.I)

# A tail people leave on the end of what they like: "curry, obviously", "green tbh".
TAIL = re.compile(r"[\s,]+(?:obviously|tbh|tho|though|really|lol|haha|i think|probably|"
                  r"at the moment|right now|for sure|of course)\s*$", re.I)

# What somebody says back to the bot's own question when they are not answering it: "thanks",
# "no thanks", "ok". A favourite asked for is answered on the next turn only, and one of these
# kept as the value would have the bot say "You said no thanks - that is your favourite team" for
# the rest of the chat.
ACKNOWLEDGES = frozenset("""
thanks thank thankyou cheers ta ok okay k cool nice great lovely brilliant right alright fine
sure yes yeah yep no nope nah none nothing okthanks nothanks
""".split())

# A value that names nothing: "my favourite colour is nothing", "my favourite food is whatever".
# A shrug rather than a favourite, however it is phrased: "not sure", "no idea", "hard to say".
# The single words below are the ones that are a shrug on their own ("nothing", "whatever").
NO_VALUE_PHRASES = ("not sure", "no idea", "dont know", "don't know", "dunno", "hard to say",
                    "cant decide", "can't decide", "not really", "nothing really", "nothing much",
                    "i dont know", "i don't know", "a few", "loads")

# What a thing is doing, not what somebody likes: "my favourite shop is shut", "my favourite team
# is rubbish", "my favourite show is over now". Stored as a favourite, "shut" is given back to
# every later ask as the thing they like. A one-word state on its own is not a value, and neither
# is a value that ends in a time - the thing is happening now, it is not the favourite.
A_STATE = frozenset("""
closed shut off over broken rubbish injured cancelled canceled finished sold bought delayed
dirty clean empty full busy open missing ill sick late early free full gone
""".split())
AN_EVENT = re.compile(
    r"(?:\b(?:right\s+now|for\s+now|now|today|tomorrow|tonight|again)\b"
    r"|\ball\s+the\s+time\b|\bat\s+the\s+(?:moment|minute)\b|\bthese\s+days\b"
    r"|\b(?:next|last|this)\s+[a-z]+)\s*$", re.I)

NO_VALUE = frozenset("""
nothing none no idea not sure unsure duno dunno dontknow whatever anything something everything
same hard difficult tricky easy impossible complicated tricky unclear
which what whats who whose when where why how
""".split())

# A clause dressed as a value: "my favourite food is to cook pasta", "my favourite thing is
# when it rains". The person is describing a situation, not naming a favourite.
A_CLAUSE = re.compile(r"^(?:to|when|if|that|because|so|how|why|what|whether)\b", re.I)

# The words a thing can be, when what is left is only an adjective: this is not a list of
# favourites - the thing is whatever word they used - only a check that the thing is not a
# verb phrase ("my favourite is running" names no thing at all).
NOT_A_THING = frozenset("""
to be do have go going going get got make making take taking give giving see seeing say saying
think thinking know knowing want wanting need needing like liking love loving hate hating
""".split())


def _plain(value):
    text = " ".join(str(value or "").split())
    text = text.strip(" \t,.;:!-\u2014")
    text = TAIL.sub("", text)
    return text.strip(" \t,.;:!-\u2014")


def _a_value(value):
    """Whether what follows "is" names a favourite rather than a clause or a shrug."""
    text = _plain(value)
    if not text or len(text.split()) > 6:
        return ""
    low = text.lower().replace("'", "").replace("\u2019", "")
    if low in NO_VALUE or all(word in NO_VALUE for word in low.split()):
        return ""
    if any(low == phrase or low.startswith(phrase + " ") for phrase in NO_VALUE_PHRASES):
        return ""
    if A_CLAUSE.match(low):
        return ""
    if low in A_STATE and len(low.split()) == 1:
        return ""  # "my favourite shop is shut" is what it is doing, not what they like
    if AN_EVENT.search(low):
        return ""  # "my favourite show is over now" is the thing now, not the favourite
    if not re.search(r"[a-z0-9]", low):
        return ""
    return text


# Words that end an ask rather than naming a thing: "what is my favourite colour again",
# "what did i say my favourite film was". The thing is what is left of them.
ASK_TAIL = frozenset("""
again is was are were then though tho now please pls exactly already anyway
""".split())


def _a_thing(thing):
    """The word(s) the favourite is of, kept lower-case, or "" when it names no thing."""
    text = " ".join(str(thing or "").split()).strip(" \t,.;:!-").lower()
    if not text or len(text.split()) > 3:
        return ""
    words = [word for word in text.split() if word not in ASK_TAIL]
    if not words:
        return ""
    text = " ".join(words)
    if words[0] in ASK_TAIL or words[0] in ("thing", "things", "one") \
            or words[0] in ("which", "what", "who"):
        # "my favourite is running" / "my favourite thing is ..." names no thing
        return ""
    return text


# A clause that asks something of its own: "what should i watch", "any ideas", "what should i
# cook tonight". The favourite is often said first and the question comes after it, in the same
# line ("my favourite genre is comedy, what should i watch"), and the person wants that question
# answered. A note that the favourite was kept, in place of the suggestion, is the bot taking a
# turn it should not answer.
ASKS_SOMETHING = re.compile(
    r"^(?:what|which|who|when|where|why|how|should|shall|can|could|would|will|do|does|did|"
    r"is|are|any|anything|someone|suggest|give|tell|help|recommend)\b", re.I)
# A clause that asks without a question word on the front: "i cant decide what to watch, my
# favourite genre is comedy" is a request for a suggestion, and the note alone left the person
# with a fact they had just stated and nothing to watch. Being stuck is the ask.
STUCK = re.compile(
    r"\b(?:can'?t|cannot|can not|don'?t know|do not know|not sure|no idea|stuck|"
    r"cant|dont)\b[^,;.!?]{0,30}?"
    r"\b(?:decide|choose|pick|watch|cook|eat|drink|read|wear|do|get|make|start)\b", re.I)

# The line cut into sentences as well as clauses, for a favourite followed by a question with a
# full stop between them.
SENTENCE_TOO = re.compile(r"\s*[,;]\s*|\s+[\u2014-]\s*|[.!?]+\s+")


# A favourite and a question in one line, with a full stop between them: "my favourite film is
# alien. what should i watch tonight". The stop belongs to the line, not to the value, so the
# part before it is read the way a whole line is - otherwise the favourite is never kept, and
# "what is my favourite film" a turn later is told it has not come up. The split is only made in
# front of a word that asks something, so a value with a full stop in it ("mrs. doubtfire") is
# left alone.
A_QUESTION_AFTER = re.compile(
    r"[.!?]+\s+(?=(?:what|which|who|when|where|why|how|should|shall|can|could|would|will|"
    r"any|anything|do|does|did|is|are)\b)", re.I)


def _clauses(text):
    """Each clause of the line, then the whole line: a favourite said after a comma.

    A clause is tried first so that a comma between two favourites does not run one value into
    the next ("my favourite colour is green, my favourite food is curry" kept the food as part
    of the colour). The whole line is last, for a value that has a comma of its own.
    """
    said = " ".join(str(text or "").split())
    out = [part.strip() for part in re.split(r"\s*[,;]\s*|\s+[\u2014-]\s+", said)]
    out = [part for part in out if part]
    if len(out) > 1:
        return out + [said]
    return [said]


def read(line):
    """The favourite a line states: {"thing": "colour", "value": "green"}, or None."""
    text = " ".join(str(line or "").split())
    if not text or "?" in text:
        return None
    if asked(text):
        return None  # a question about the favourite states none
    if SOMEONE_ELSE.search(text):
        return None
    if BEST_PERSON.search(text):
        return None  # a best friend is a person, not a favourite
    plain = LEAD.sub("", text)
    # A favourite is often said after something else: "i cant decide what to watch, my favourite
    # genre is comedy". The line only stated it, so the clause on its own is read as the line is.
    parts = _clauses(plain)
    before_the_question = A_QUESTION_AFTER.split(plain)[0].strip()
    if before_the_question and before_the_question != plain:
        parts = [before_the_question] + parts
    for said in parts:
        found = SAYS.match(said) or IS_MINE.match(said)
        if not found:
            continue
        thing = _a_thing(found.group("thing"))
        # A thing that runs into the value is a misread ("my favourite film alien" is not a
        # sentence), so the value has to be there on its own.
        value = _a_value(found.group("value"))
        if thing and value:
            return {"thing": thing, "value": value}
    return None


def asks_something_too(line):
    """True when the line states a favourite and asks something else as well.

    "my favourite genre is comedy, what should i watch" is one line doing two jobs: it is a fact
    about the person and it is a request for a suggestion. The fact is kept either way - what the
    store must not do is answer the line with the fact alone, leaving the question unanswered.
    Only a clause other than the one that states the favourite counts, so a line whose question
    is part of the value ("my favourite film is whatever is on") is not one of these.
    """
    text = " ".join(str(line or "").split())
    if not text:
        return False
    parts = [part.strip() for part in SENTENCE_TOO.split(LEAD.sub("", text)) if part.strip()]
    if len(parts) < 2:
        return False
    for part in parts:
        plain = LEAD.sub("", part).strip()
        if not plain:
            continue
        if SAYS.match(plain) or IS_MINE.match(plain):
            continue  # this clause is the favourite itself
        if "?" in plain or ASKS_SOMETHING.match(plain) or STUCK.search(plain):
            return True
    return False


def asked(line):
    """The thing a line asks their favourite of ("colour"), or None when it asks something else."""
    text = " ".join(str(line or "").split())
    if not text:
        return None
    low = text.lower().replace("\u2019", "'")
    if "favourite" not in low and "favorite" not in low and " fav" not in low:
        return None
    if "your favourite" in low or "your favorite" in low:
        return None  # "what's your favourite colour" is a question about the bot
    found = ASKS.search(LEAD.sub("", text))
    if not found:
        found = WHICH_IS.search(text)
    if not found:
        return None
    return _a_thing(found.group("thing")) or None


def _singular(thing):
    """The thing with a plural "s" taken off, for "what are my favourite films"."""
    text = str(thing or "")
    if len(text) > 3 and text.endswith("s") and not text.endswith("ss"):
        return text[:-1]
    return text


def asks_all(line):
    """Whether the line asks for every favourite at once ("what are my favourites")."""
    text = " ".join(str(line or "").split())
    if not text:
        return False
    low = text.lower().replace("\u2019", "'")
    if "your favourite" in low or "your favorite" in low:
        return False  # a question about the bot, not about them
    return bool(ASKS_ALL.search(low))


def prefers_now(line):
    """The value a "i prefer X now" line puts in place of the favourite last named, or ""."""
    text = " ".join(str(line or "").split())
    if not text or "?" in text:
        return ""
    found = PREFERS_NOW.match(LEAD.sub("", text))
    if not found:
        return ""
    return _a_value(found.group("value"))


def an_answer(line, thing):
    """The value somebody gives when the bot has just asked them for a favourite, or ""."""
    text = " ".join(str(line or "").split())
    if not text or "?" in text or not thing:
        return ""
    plain = LEAD.sub("", text)
    if not AN_ANSWER.match(plain):
        return ""
    words = plain.lower().replace(".", "").replace("!", "").replace(",", "").split()
    if not words or any(word in ASK_TAIL or word in NOT_A_THING for word in words):
        return ""
    if all(word in ACKNOWLEDGES or word.startswith("thank") for word in words):
        return ""  # "thanks", "no thanks", "ok" is not the favourite the bot asked for
    return _a_value(plain)


def corrected(line, thing):
    """The value a correction puts in place of a favourite just given, or ""."""
    text = " ".join(str(line or "").split())
    if not text or "?" in text or not thing:
        return ""
    found = CORRECTS.match(text)
    if not found:
        return ""
    return _a_value(found.group("value"))


def kept(memory, thing):
    """The favourite on record for that thing, or "" when they have not said one."""
    if not isinstance(memory, dict) or not thing:
        return ""
    held = (memory.get("user") or {}).get("favourites")
    if not isinstance(held, dict):
        return ""
    value = held.get(thing)
    if not isinstance(value, str):
        value = held.get(_singular(thing))
    return value if isinstance(value, str) else ""


def the_favourites(memory):
    """Every favourite on record, in the order they were given."""
    if not isinstance(memory, dict):
        return []
    held = (memory.get("user") or {}).get("favourites")
    if not isinstance(held, dict):
        return []
    return [(thing, value) for thing, value in held.items() if isinstance(value, str)]


def store(memory, found):
    """Keep one favourite in the store, replacing the same thing said again."""
    if not isinstance(memory, dict) or not isinstance(found, dict):
        return
    thing = found.get("thing")
    value = found.get("value")
    if not thing or not value:
        return
    known = memory.setdefault("user", {})
    held = known.get("favourites")
    if not isinstance(held, dict):
        held = {}
    held[thing] = value
    known["favourites"] = held


__all__ = ["read", "asked", "asks_all", "prefers_now", "an_answer", "corrected", "kept",
           "the_favourites", "store"]


# "my favourite food is my mums curry" said back as "your favourite food is my mums curry" is the
# bot helping itself to the person's dinner: the slot keeps their words, and their words about
# themselves said back are "your mum's curry". The swap is the one the plain frames already make
# (memory_store._yours), and the apostrophe is the one a person has in front of their own relation
# (KIN_POSSESSIVE in bot/memory/ack.py). It lives here rather than in memory_store so that the
# whole of a favourite's wording is in one file.
KIN_APOSTROPHE = re.compile(
    r"\b(your (?:mum|mom|mam|mother|dad|father|son|daughter|sister|brother|wife|husband|partner"
    r"|nan|nana|granny|gran|grandma|grandad|grandpa|aunt|auntie|uncle|niece|nephew|cousin"
    r"|boyfriend|girlfriend|fiance|fiancee|mate|friend|boss))s\b", re.I)
MY_WORDS = {"myself": "yourself", "my": "your", "me": "you", "i": "you", "our": "your",
            "us": "you"}


def their_words(value):
    """The person's own words about themselves, said back: "my mums curry" -> "your mum's curry"."""
    out = []
    for word in str(value or "").split():
        low = word.lower().strip(".,!?")
        swapped = MY_WORDS.get(low)
        if not swapped:
            out.append(word)
            continue
        tail = word[len(low):]
        out.append(swapped[:1].upper() + swapped[1:] if word[:1].isupper() else swapped)
        if tail:
            out[-1] += tail
    return KIN_APOSTROPHE.sub(r"\1's", " ".join(out))

def watch(text, memory):
    """Keep the favourite a line names, answers, corrects or changes, and mark it for the reply.

    Called from the `favourites` module's `observe` (bot/modules/favourites.py), which is the one
    place a turn is read for a favourite: the reading is here, beside the slot it writes, so the
    wording and the store stay in one file.
    """
    if not isinstance(memory, dict):
        return
    said = read(text)
    if not said:
        pending = memory.pop("favourite_asked", None) if isinstance(memory, dict) else None
        if isinstance(pending, str) and pending:
            answered = an_answer(text, pending)
            if answered:
                # The bot asked for the favourite it has none of ("what is it?"), and this short
                # line is the answer to that question. Read only after the bot has asked, so a
                # bare "green" said out of the blue is still not a 
                said = {"thing": pending, "value": answered}
                memory["favourite_told"] = dict(said)
    if not said:
        # "my favourite film is alien" then "no wait its blade runner": the favourite said a turn
        # ago is the one being taken back, so the correction replaces it. Only the thing the chat
        # is on, and only the turn after it was said.
        recent = memory.get("favourite_recent") if isinstance(memory, dict) else None
        if isinstance(recent, dict) and recent.get("thing") \
                and recent.get("turn") == len(memory.get("turns") or []) - 1:
            put_right = corrected(text, recent["thing"])
            if put_right:
                said = {"thing": recent["thing"], "value": put_right}
                memory["favourite_told"] = dict(said)
    if not said:
        # "my favourite colour is green" then "i prefer blue now": a change said without the word
        # "favourite" is still the favourite changing, and left alone the ask kept answering
        # "You said green" to somebody who had just said they preferred blue. The thing is not
        # named in the line, so it is the one they last gave, and only for a turn or two.
        recent = memory.get("favourite_recent") if isinstance(memory, dict) else None
        if isinstance(recent, dict) and recent.get("thing") \
                and len(memory.get("turns") or []) - int(recent.get("turn") or 0) <= 2:
            moved = prefers_now(text)
            if moved and moved != kept(memory, recent["thing"]):
                was = kept(memory, recent["thing"])
                said = {"thing": recent["thing"], "value": moved}
                memory["favourite_changed"] = {"thing": recent["thing"], "value": moved, "was": was}
    if said:
        # "my favourite colour is green" is a fact about the person with no other slot: kept as a
        # taste it was a dish, and left alone the composer said it back ("Your favourite food is
        # curry - noted") while the store kept nothing, so the ask a turn later could not be
        # answered. One slot for every favourite covers a colour, a film, a food and a team.
        store(memory, said)
        if isinstance(memory, dict):
            memory["favourite_recent"] = {"thing": said["thing"],
                                          "turn": len(memory.get("turns") or [])}
