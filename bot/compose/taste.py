"""A stated like or dislike of a thing is an opener, not a fact to file.

Every one of these came back as the person's own words handed to them:

    i hate mondays        -> "Noted: you hate mondays."
    i hate cooking        -> "Noted: you hate cooking."
    i love the rain       -> "Noted: you love the rain."
    i hate the dark       -> "Noted: you hate the dark."
    i dont like christmas -> "Noted: you don't like christmas."

The same line said with "cant stand" or "dreading" reached the listening pool instead
("Thanks for telling me - I'm here if you want to dig into any of that"), and "i cant wait for
friday" reached the shrug ("Got it. Is there anything you'd like a hand with?").

None of those is a reply. A like or a dislike is the easiest thing in the world to answer: a
friend takes the side the person took, and asks one thing about the thing. That is the whole
reading here. When the line names a thing the reply uses it; when it does not, the reply is
short and warm and asks the same question without it.

What it refuses, because other readings own those turns:

  - a person, or what a person does - "i hate my sister", "i hate the way he talks to me". A
    dislike of a person is a relationship, not a taste, and the ones worth answering are the
    hard ones;
  - the person themselves - "i hate myself", "i hate my life". That is not a taste and it is
    not this module's to name;
  - a symptom - "i hate feeling like this", "i hate being ill" - which the mood and health
    readings answer;
  - a question ("why do i hate mondays"), which asks for a reason rather than stating a taste.

Two things the reading has to get right, because the frame carries the words:

  - the way they have it is not part of the thing. "i like my coffee strong" is a taste in
    coffee, and "Your coffee strong - I can see why" is not English. The manner comes off the
    thing and back into the reply as its own word ("Strong, then. What is it about your coffee
    that you like?"). A possessive is not enough on its own: "my new bike" and "my little
    garden" are the thing itself, so only a last word that names a way of being ("strong",
    "weak", "runny", "well done") comes off, and never across a linking word;
  - a taste said about the bot is a compliment. "i like your hair" is not the person telling
    you about their own hair - the reply turns "my" round into "your", so a "your" already in
    the line was said about the bot, and asking what they like about their own hair is the
    wrong friend. It is answered as the compliment it is.

It runs inside the greeting module, so it only ever speaks for lines nothing else wanted
(README.md, "Interface"): a module with its own answer still takes the turn.
"""
import re

from . import fallback

# A person, or what a person does, is not the thing a taste line is about.
_A_PERSON = re.compile(
    r"\b(?:my|his|her|their|our|your)\s+(?:mum|mom|mam|dad|father|mother|wife|husband|partner|"
    r"boyfriend|girlfriend|son|daughter|kid|kids|child|children|sister|brother|nan|nana|gran|"
    r"granny|grandma|grandad|grandpa|aunt|uncle|cousin|friend|friends|mate|mates|boss|landlord|"
    r"neighbours?|neighbors?|colleague|colleagues|coworker|in-laws?|family|stepson|"
    r"stepdaughter|ex)\b",
    re.I)
# The same, said with a pronoun: "i love her but it's a lot" is about a person, and the reading
# that says "Glad you like it" back is the wrong friend.
_A_SOMEONE = re.compile(r"\b(?:her|him|them|his|hers|theirs)\b", re.I)
# A like of a person is not a taste in a thing, however the person is described: "i like a girl
# at work" is the before-you-ask-her-out line, and "Good choice. What is it about a girl at work
# that you love?" is the wrong friend for it.
_A_PERSON_DESCRIBED = re.compile(
    r"\b(?:a|an|the|this|that|some)\s+(?:girl|boy|man|woman|bloke|guy|lad|lady|fella|"
    r"person|someone|somebody|child)\b",
    re.I)
# Work is the livelihood readings' subject, not a taste: "i hate my job" is a problem to take
# seriously rather than a thing to agree about.
_ABOUT_WORK = re.compile(r"\bmy\s+(?:job|work|shift|shifts|career|line\s+of\s+work)\b", re.I)
# The person themselves, or a part of them: "i hate my arms" said while choosing something to
# wear is how somebody feels about how they look, and "My arms, yeah. That one gets a lot of
# people." is the wrong friend for it.
_ABOUT_ME = re.compile(
    r"\b(?:myself|my\s+life|my\s+body|my\s+own\s+body|being\s+me|my\s+(?:arms?|legs?|thighs?|"
    r"tummy|belly|waist|hips?|shape|weight|looks|face|nose|teeth|smile|skin|hair|neck|chin|"
    r"chest|shoulders?|hands?|feet|knees?|reflection)\b)",
    re.I)
# A symptom said with a word for taste: the mood and health readings answer these.
_A_SYMPTOM = re.compile(
    r"\b(?:feeling\s+like\s+this|feeling\s+this\s+way|being\s+ill|being\s+sick|"
    r"the\s+way\s+i\s+feel|how\s+i\s+feel)\b",
    re.I)
# The line asks something as well as stating the taste ("i hate broccoli what can i have
# instead"): the question is the turn, and the reading that answers questions is not this one.
_A_ASK = re.compile(
    r"\b(?:what|which|how|why|when|where|who|instead|should|could|would|recommend|suggest|"
    r"else|any\s+ideas?)\b",
    re.I)
# A dislike of what somebody did is a complaint about a person, not a taste about a thing.
_A_DEED = re.compile(r"^(?:when|that|it\s+when|the\s+way|how)\b", re.I)
# A stance with a reason or a second clause in it ("i hate mondays because of the traffic") is
# still a stance, but the thing stops being a name a reply can carry, so it gets the short line.
_A_SECOND_CLAUSE = re.compile(
    r"\b(?:because|but|although|though|and\s+i|and\s+then|so\s+i)\b", re.I)

_LEAD_SUBJECT = (r"(?P<subj>i|im|i'm)\s+"
                 r"(?:(?:really|just|absolutely|totally|honestly|actually|properly|still|also|"
                 r"kind\s+of|sort\s+of)\s+)?")
_LEAD = (r"(?:i|im|i'm)\s+"
         r"(?:really\s+|just\s+|absolutely\s+|honestly\s+|actually\s+|totally\s+|seriously\s+|"
         r"properly\s+|kind\s+of\s+|sort\s+of\s+)?")

# "i hate mondays", "i cant stand my commute", "i dont like christmas", "im not a fan of rain".
_A_STANCE = re.compile(
    "^" + _LEAD_SUBJECT +
    r"(?P<verb>hate|hating|love|loving|like|liking|adore|adoring|dislike|prefer|"
    r"can'?t\s+stand|cannot\s+stand|can\s+not\s+stand|couldn'?t\s+stand|"
    r"(?:am\s+)?not\s+a\s+(?:big\s+)?fan\s+of|"
    r"don'?t\s+(?:really\s+)?like|do\s+not\s+(?:really\s+)?like|never\s+liked)\s+"
    r"(?P<thing>.+)$",
    re.I)
# The same stance with the subject dropped, which is how people say it out loud: "not too keen on
# the new place", "not 2 keen on it", "never liked the rain", "cant stand mondays". The opening
# word is what makes it safe to read without a subject - "not", "never", "cant" - so a line that
# opens on a bare "like" ("like i said") is not caught here, and the verb is read the same way the
# first-person one is, so the animal, the doing and the thing of theirs keep their own answers.
_A_STANCE_NO_SUBJECT = re.compile(
    r"^(?P<verb>not\s+(?:2|too|that|very|terribly|overly|really|a\s+bit|a\s+lot|much\s+of\s+a|"
    r"a\s+big)?\s*(?:keen|fussed|bothered)\s+(?:on|about|with)|"
    r"never\s+(?:been\s+)?(?:that|too|very|really|overly)\s+keen\s+(?:on|about|with)|"
    r"not\s+(?:really\s+|usually\s+)?(?:much\s+of\s+)?(?:a\s+)?"
    r"(?:(?:big|huge|massive|great|the\s+biggest)\s+)?fan\s+of|"
    r"never\s+(?:been\s+)?(?:really\s+|actually\s+)?(?:a\s+)?(?:big\s+|huge\s+)?fan\s+of|"
    r"never\s+(?:really\s+|actually\s+)?liked|"
    r"can'?t\s+stand|cannot\s+stand|can\s+not\s+stand|couldn'?t\s+stand|can'?t\s+stick|"
    r"do\s+not\s+(?:really\s+)?like|don'?t\s+(?:really\s+)?like)\s+"
    r"(?P<thing>.+)$",
    re.I)
# "im dreading monday", "i dread the drive in".
_A_DREAD = re.compile("^" + _LEAD + r"(?:am\s+)?(?:dreading|dread)\s+(?P<thing>.+)$", re.I)
# "i cant wait for friday".
_A_WAIT = re.compile(
    "^" + _LEAD + r"(?:can'?t\s+wait\s+for|cannot\s+wait\s+for|counting\s+down\s+to)\s+"
    r"(?P<thing>.+)$",
    re.I)

# A line with a second stance in it ("i like dogs but i hate cats") states two tastes, and the
# reply that takes a side has to pick one of them: it goes to the reading that files both.
_TWO_STANCES = re.compile(
    r"\b(?:but|and|though|although)\s+(?:i|im|i'm)\s+"
    r"(?:really\s+|just\s+|also\s+)?(?:hate|love|like|prefer|adore|can'?t\s+stand|"
    r"don'?t\s+like|dont\s+like|do\s+not\s+like)\b",
    re.I)
_DISLIKE_VERBS = frozenset((
    "hate", "hating", "dislike", "can't stand", "cant stand", "cannot stand", "can not stand",
    "couldn't stand", "couldnt stand", "not a fan of", "am not a fan of", "not a big fan of",
    "am not a big fan of", "don't like", "dont like", "do not like", "don't really like",
    "dont really like", "do not really like", "never liked",
))
_LIKE_VERBS = frozenset(("love", "loving", "like", "liking", "adore", "adoring", "prefer"))

# Takes the side the person took, then asks one thing about the thing. A line that only says
# "fair enough" and stops is the receipt in another coat. Every frame here is thing-neutral: a
# dislike is often about a noun nobody does ("the dark", "spiders", "christmas"), so "What do you
# do instead?" and "you would happily never do it again" live in A_DISLIKE_DOING, where the thing
# is a thing to do.
A_DISLIKE = (
    "{thing} - I'm with you on that. What is the worst bit of it?",
    "{thing} would get to anyone. What is it that gets you about it?",
    "{thing}, yeah. That one gets a lot of people. What is it about it?",
    "You are not on your own there. What is it about {thing} that does your head in?",
    "Fair enough. What is it about {thing}?",
)
A_LIKE = (
    "{thing} - good taste. What is it you like about that?",
    "Ah, {thing}. What got you into that?",
    "{thing}, nice one. What is the draw for you?",
    "Good choice. What is it about {thing} that you love?",
    "{thing} - that is a good thing to like. What do you like most about it?",
)
# A thing of their own - "my flat", "my new job", "my dog" - is not a category to have taste in,
# and the two lines above that praise the taste land wrong on it: "my flat - good taste" reads as
# praise of the flat, and "how long has that been going on" is a question about the tenure of a
# dog. The plain pool says the same warm thing without the judgement.
A_LIKE_OWN = (
    "{thing} - I can see why. What do you like most about it?",
    "{thing}, that is a good thing to have. What is the best of it?",
    "{thing} - fair enough. What is it about it that you like?",
)
# An animal of theirs is not an "it": "Your dog, that is a good thing to have. What is the best
# of it?" is a question about a thing on a shelf. People say "them" about the animal they live
# with, so the frame asks about the animal and not about the keeping of it.
A_LIKE_PET = (
    "{thing} - I can see why. What do they get up to?",
    "{thing}, that is a good thing to have. How long have you had them?",
    "{thing} - fair enough. What is it about them that you love?",
    "{thing}, lovely. What is the best thing about them?",
)
# A doing, not a thing: "i like to cook" carried as a thing read "To cook - good taste", which
# is not English. The doing said as a name takes a pool whose frames ask about doing it.
A_LIKE_DOING = (
    "{thing} - good one. How often do you get to do it?",
    "{thing}, nice. What got you into it?",
    "{thing} - I can see why. What is the best part?",
)
A_DISLIKE_DOING = (
    "{thing} - I'm with you on that. What is the worst bit?",
    "{thing}, fair enough. What do you do instead?",
    "{thing} - honestly, same. How do you get out of it?",
)
A_DISLIKE_PET = (
    "{thing} - fair enough. What is it about them?",
    "{thing}, yeah. What do they do that gets you?",
)
A_DREAD = (
    "{thing} - I do not blame you. What is the part you are least looking forward to?",
    "Fair enough - nobody looks forward to {thing}. What is the worst of it going to be?",
    "{thing}, yeah. What would make it easier?",
)
# The thing and the way they have it, said together: "i like my coffee strong", "i dont like my
# tea weak". The manner is a word about the thing, not part of its name, so the frames here give
# it back to the person ("Strong, then") instead of gluing it to the noun.
A_LIKE_MANNER = (
    "{manner}, then. What is it about {thing} that you like?",
    "{thing}, {manner} - that is the only way. What is the best of it?",
    "Good - {manner} it is. What do you like most about it?",
    "{thing}, {manner} - that is the right answer. What got you that way?",
)
A_DISLIKE_MANNER = (
    "{manner} - no wonder. What is it about {thing} that gets you?",
    "{thing}, {manner} - I am with you. What is the worst bit of it?",
    "Fair enough - nobody wants {thing} {manner}. What do you have instead?",
)
# A taste said about the bot itself: "i like your hair", "i love your voice". The bot is being
# paid a compliment, not told about a thing the person owns, so the reply takes it and asks
# about the taste rather than handing "your hair" back as if it were theirs.
A_THE_BOT_LIKED = (
    "That is kind - thank you. What is it about it you like?",
    "Ha - thanks. What do you like most about it?",
    "Thank you - nice of you to say. What is it that works for you?",
)
A_THE_BOT_DISLIKED = (
    "Fair enough - point taken. What would land better?",
    "Sorry about that. How would you put it instead?",
)
A_WAIT = (
    "{thing} cannot come soon enough. What have you got planned?",
    "Not long now. What are you looking forward to most about {thing}?",
    "{thing} - good. Anything nice lined up?",
)
_BY_KIND = {"dislike": A_DISLIKE, "like": A_LIKE, "like_own": A_LIKE_OWN,
            "like_pet": A_LIKE_PET, "dislike_pet": A_DISLIKE_PET,
            "like_doing": A_LIKE_DOING, "dislike_doing": A_DISLIKE_DOING,
            "like_manner": A_LIKE_MANNER, "dislike_manner": A_DISLIKE_MANNER,
            "the_bot_liked": A_THE_BOT_LIKED, "the_bot_disliked": A_THE_BOT_DISLIKED,
            "dread": A_DREAD, "wait": A_WAIT}

# A taste about the bot is said with "your": the same word the reply would use for the person's
# own thing, which is why it is read before the possessive is turned round.
_THE_BOTS = re.compile(r"^(?:your|you|ur|yours|yourself)\b", re.I)

# The way they have it, not a part of the thing. Only a word that names how a thing is - how it
# tastes, how it is cooked, how it fits - comes off the end of an object that opens on a
# possessive; a noun ("my new bike") or a longer phrase ("my cup of tea") stays as it was said.
_MANNER_WORDS = frozenset((
    "strong", "weak", "runny", "firm", "hard", "soft", "milky", "creamy", "sweet", "hot",
    "cold", "warm", "tepid", "flat", "fizzy", "sparkling", "thick", "thin", "crispy", "crunchy",
    "smooth", "black", "plain", "spicy", "mild", "salty", "sour", "bitter", "dry", "ripe",
    "rare", "tender", "tough", "loud", "quiet", "bright", "pale", "bold", "baggy", "tight",
    "loose", "short", "long", "heavy", "light", "soggy", "mushy", "lumpy", "gritty", "chewy",
    "rubbery", "juicy", "burnt", "raw", "fluffy", "dense", "chunky", "frothy", "sharp",
    "stodgy", "greasy",
))
# "well done" is two words, and it is the only manner here said that way.
_A_MANNER_PHRASE = re.compile(r"\b(?:well done|well-done|medium rare|over easy)\b", re.I)
# Words that make the rest of the object a phrase rather than a manner: "my cup of tea strong"
# is a typo, and "my eggs and bacon" does not want its last word taken off it.
_A_LINKING_WORD = frozenset(("of", "in", "with", "and", "on", "for", "at", "to", "from",
                             "that", "when", "but", "as", "by", "into", "over", "under"))


def _split_manner(thing):
    """(the thing, the way they have it): "my tea weak" is ("my tea", "weak").

    A manner comes off only when the object opens on the person's possessive, the last word is
    one that says how a thing is, and nothing between them links the two into a single phrase.
    """
    words = thing.split()
    if (len(words) == 2 and words[-1].lower() in _MANNER_WORDS
            and words[0].lower() not in ("my", "our", "the", "a", "an", "your", "his", "her",
                                         "their", "it", "that", "this")):
        # "i like coffee strong": the same line without the possessive, and the same split. The
        # noun comes first here, which is how it is said after the verb, so the last word is the
        # manner and not a part of the thing's name.
        return words[0], words[-1].lower()
    if len(words) < 3 or words[0].lower() not in ("my", "our"):
        return thing, ""
    said = " ".join(words[1:])
    phrase = _A_MANNER_PHRASE.search(said)
    if phrase:
        head = said[:said.lower().index(phrase.group(0))].strip()
        if head and not any(word.lower() in _A_LINKING_WORD for word in head.split()):
            return words[0] + " " + head, phrase.group(0).lower()
        return thing, ""
    last = words[-1].lower().strip(".,!;:")
    if last not in _MANNER_WORDS:
        return thing, ""
    if any(word.lower().strip(".,!;:") in _A_LINKING_WORD for word in words[1:-1]):
        return thing, ""
    return " ".join(words[:-1]), last


def _a_manner_kind(kind):
    """The pool for a thing and a manner said together; the kind's own pool otherwise."""
    return {"like": "like_manner", "like_own": "like_manner",
            "dislike": "dislike_manner"}.get(kind, kind)

# A thing the person owns or lives with, said with the possessive: it takes the plain pool. The
# possessive is the person's, so the reply turns it round - "my flat" is "your flat" to the bot.
_THEIR_OWN = re.compile(r"^(?:my|our)\b", re.I)

# An animal they live with is a "them" and not an "it" (see A_LIKE_PET). The noun is what the
# possessive was put on, so the plural is taken off the last word before it is looked up.
_AN_ANIMAL = frozenset((
    "dog", "cat", "puppy", "kitten", "rabbit", "bunny", "hamster", "gerbil", "guinea", "pig",
    "horse", "pony", "donkey", "bird", "parrot", "budgie", "fish", "tortoise", "turtle",
    "snake", "lizard", "gecko", "chicken", "duck", "goat", "ferret", "rat", "mouse",
    "hedgehog", "chinchilla", "canary", "cockatiel",
))


# "i like to cook", "i love to swim": the words after "to" are a doing, and a reply that carries
# "To cook" as if it were a thing is not English. Only a short tail is a doing: "to think im
# organised" is a clause, and the answer already on the screen for it is the better one.
_AN_INFINITIVE = re.compile(r"^to\s+(?P<verb>[a-z']+)(?:\s+(?P<rest>[a-z' ]+))?$", re.I)
# Words that make the tail a clause rather than the object of the doing.
_A_CLAUSE_WORD = frozenset(("i", "im", "i'm", "me", "you", "he", "she", "it", "we", "they",
                            "that", "this", "these", "those", "my", "your", "his", "her",
                            "their", "our", "there", "if", "when", "about", "of"))
# A doing to answer is something a person does with their hands or their body. "i like to think
# im organised" states a belief, and "i like to know the price first" states a rule of thumb.
_NOT_A_DOING = frozenset(("think", "know", "believe", "remember", "forget", "be", "have",
                          "seem", "suppose", "guess", "imagine", "feel", "want", "need",
                          "say", "tell", "ask", "hear", "see", "understand", "mean", "hope",
                          "wish", "expect", "assume", "pretend", "decide", "hesitate"))
# A verb that ends on a single consonant after one vowel doubles it: "swim" is "swimming".
_DOUBLING = frozenset(("swim", "run", "sit", "shop", "stop", "get", "put", "cut", "hit",
                       "dig", "plan", "chat", "jog", "nap", "hop", "win", "drop", "trim",
                       "rub", "knit", "shut", "swing", "begin", "forget", "travel", "snorkel"))
_IRREGULAR_DOING = {"be": "being", "die": "dying", "lie": "lying", "tie": "tying",
                    "see": "seeing", "agree": "agreeing", "ski": "skiing", "free": "freeing"}


def _a_doing(verb):
    """The doing said as a name: "cook" is "cooking", "swim" is "swimming"."""
    verb = verb.lower()
    if verb in _IRREGULAR_DOING:
        return _IRREGULAR_DOING[verb]
    if verb.endswith("ie"):
        return verb[:-2] + "ying"
    if verb.endswith("e") and not verb.endswith(("ee", "ye", "oe")):
        return verb[:-1] + "ing"
    if verb in _DOUBLING:
        return verb + verb[-1] + "ing"
    return verb + "ing"


def _the_doing(thing):
    """The doing a stance about "to <verb>" is about, capitalised, or "" when it is not one."""
    match = _AN_INFINITIVE.match(thing or "")
    if not match:
        return ""
    verb = match.group("verb").lower()
    rest = (match.group("rest") or "").strip()
    if verb in _NOT_A_DOING or not verb:
        return ""
    if rest and (len(rest.split()) > 2 or any(w in _A_CLAUSE_WORD for w in rest.split())):
        return ""
    doing = _a_doing(verb)
    return (doing + (" " + rest if rest else "")).capitalize()


def _is_an_animal(thing):
    """True when the thing of theirs is the animal they live with."""
    if not _THEIR_OWN.match(thing or ""):
        return False
    words = [w for w in thing.lower().split() if w not in ("my", "our")]
    if not words:
        return False
    last = words[-1]
    if last in _AN_ANIMAL:
        return True
    return last.endswith("s") and last[:-1] in _AN_ANIMAL


def _the_stance(thing, liked):
    """(kind, thing) for the words after the verb: a doing, an animal of theirs, or the thing.

    None when the words after the verb are a clause and not a thing at all ("to think im
    organised", "to know the price first"): those lines have an answer already, and a frame
    around half a clause is worse than the answer it replaces.
    """
    doing = _the_doing(thing)
    if doing:
        return ("like_doing" if liked else "dislike_doing"), doing
    if re.match(r"^to\s+[a-z]", thing or "", re.I):
        return None
    if _is_an_animal(thing):
        return ("like_pet" if liked else "dislike_pet"), thing
    if liked and _THEIR_OWN.match(thing):
        return "like_own", thing
    return ("like" if liked else "dislike"), thing


def _clean(text):
    """The line as words: lowercased, filler in front taken off, no trailing punctuation."""
    said = " ".join(str(text or "").lower().split())
    said = re.sub(r"^(?:hi|hey|hello|yo|so|well|oh|god|honestly|anyway)[,!\s]+", "", said)
    return said.strip(" .!,")


# A pronoun names nothing a reply can carry: "i hate it" said alone is not "It - I'm with you".
_A_PRONOUN = frozenset(("it", "that", "this", "them", "these", "those", "things", "everything",
                        "anything", "stuff"))


# Some lines name a thing by what it is like rather than by itself - "the sound of miso", "the
# idea of a van" - and a frame that carries it reads as nonsense ("The sound of miso - good
# taste"). A quantity is not a thing either: "i cant stand much more of this" is a hard week, and
# the listening lines answer it better than a question about "much more of this".
_NOT_A_THING = re.compile(
    r"^(?:the\s+|this\s+|that\s+|your\s+|my\s+|our\s+|his\s+|her\s+|their\s+)?"
    r"(?:sound|idea|thought|look|smell|taste|prospect|notion|plan|suggestion|thinking|point"
    r"|much|more|lots|plenty)\b",
    re.I)


# Filler a person types at the end of a line, which is not part of the thing: "i hate mushrooms
# btw" is a dislike of mushrooms, and "Mushrooms btw - I'm with you" reads like a form letter.
_TAIL_FILLER = re.compile(
    r"[\s,]*\b(?:btw|tbh|lol|tho|though|anyway|anyways|honestly|i\s+guess|as\s+well|"
    r"so\s+much|very\s+much|a\s+lot|to\s+bits|heaps|loads|right\s+now|at\s+the\s+moment)\b"
    r"[\s.!?]*$",
    re.I)


# "this cold weather", "that film", "these shoes": a pointing word in front of a noun is the
# noun, and the frame carries it the same way ("This cold weather - I'm with you on that"). Alone
# it is the pronoun the fence is for ("i hate this", "i cant stand that"), and "this one" points
# at something the bot cannot see.
_DEMONSTRATIVE = frozenset(("this", "that", "these", "those"))


def _a_pointed_at_thing(thing):
    """True for a pointing word that has the thing it points at after it."""
    words = (thing or "").lower().split()
    return (len(words) > 1 and words[0] in _DEMONSTRATIVE
            and words[1] not in ("one", "ones", "sort", "kind", "type"))


def _the_thing(raw):
    """The words after the verb as they were said, or "" when they cannot carry a reply."""
    thing = " ".join(str(raw or "").split()).strip(" .!,;:")
    thing = _TAIL_FILLER.sub("", thing).strip(" .!,;:")
    # The first word decides. A thing that *starts* with a pronoun names nothing the reply can
    # carry: "i hate it here" became "What is it about it here you would happily never do again?",
    # because "it here" is not the pronoun itself.
    if not thing or len(thing.split()) > 5:
        return ""
    if thing.lower().split()[0] in _A_PRONOUN and not _a_pointed_at_thing(thing):
        return ""
    if _A_DEED.match(thing) or _A_SECOND_CLAUSE.search(thing):
        return ""
    if _NOT_A_THING.match(thing):
        return ""
    # The manner is said about the thing, not part of its name: "my coffee strong" is a taste in
    # coffee. `_the_manner` reads it off the same words for `reply_for` to give back to them.
    return _split_manner(thing)[0]


def _the_manner(raw):
    """The way they have it, when the object names a thing and a manner: "my tea weak" -> "weak"."""
    thing = " ".join(str(raw or "").split()).strip(" .!,;:")
    thing = _TAIL_FILLER.sub("", thing).strip(" .!,;:")
    if not thing or len(thing.split()) > 5:
        return ""
    return _split_manner(thing)[1]


def reads_as_a_taste(text):
    """(kind, thing) for a line that only states a like or a dislike, else None.

    `kind` is one of "dislike", "like", "dread", "wait"; `thing` is the words after the verb, or
    "" when the line reads as a taste but names nothing a reply can carry. `_read` is the same
    reading with the manner kept, which is what `reply_for` needs.
    """
    read = _read(text)
    return (read[0], read[1]) if read else None


def _read(text):
    """(kind, thing, manner) for a line that only states a like or a dislike, else None."""
    said = _clean(text)
    if not said or "?" in said:
        return None
    # "i love my fiance", "i love my kids", "i love my parents": the love reading has a pool that
    # asks about the person with "they", and the taste reader would call the person a thing
    # ("Your fiance - fair enough. What is it about it that you like?"). Only the love lines stand
    # it down; "i like my parents" keeps whatever answers it today.
    if fallback._loves_someone(said):
        return None
    if (_A_PERSON.search(said) or _A_SOMEONE.search(said) or _ABOUT_ME.search(said)
            or _A_PERSON_DESCRIBED.search(said) or _A_SYMPTOM.search(said)
            or _ABOUT_WORK.search(said) or _TWO_STANCES.search(said)):
        return None
    for pattern, kind in ((_A_STANCE, None), (_A_STANCE_NO_SUBJECT, None),
                          (_A_DREAD, "dread"), (_A_WAIT, "wait")):
        match = pattern.match(said)
        if not match:
            continue
        if not _the_thing(match.group("thing")):
            # Nothing nameable after the verb ("i love cooking, you do it most nights",
            # "im loving this"): a reply that carries no thing reads like a form letter, and the
            # mood readings have a better answer for those lines.
            return None
        if _A_ASK.search(match.group("thing")):
            # The line asks something as well as stating the taste ("i hate broccoli what can i
            # have instead"): the question is the turn, and another reading answers questions.
            return None
        raw = " ".join(match.group("thing").split()).strip(" .!,;:")
        if _THE_BOTS.match(raw):
            # "i like your hair" is a compliment paid to the bot. The bot has no hair to be
            # asked about, and the reply's own "your" would hand the person their own hair back.
            if kind:
                return ("the_bot_liked" if kind == "wait" else "the_bot_disliked"), "", ""
            verb = " ".join(match.group("verb").lower().split())
            return (("the_bot_liked" if verb in _LIKE_VERBS else "the_bot_disliked"), "", "")
        manner = _the_manner(raw)
        if kind:
            return kind, _the_thing(raw), ""
        if pattern is _A_STANCE_NO_SUBJECT:
            # There is no subject to read the verb against: every opener in this pattern is a
            # dislike, and the words after it go the way they go after "i dont like".
            read = _the_stance(_the_thing(raw), False)
            if not read:
                return None
            return (_a_manner_kind(read[0]) if manner else read[0]), read[1], manner
        verb = " ".join(match.group("verb").lower().split())
        subject = " ".join(match.group("subj").lower().split())
        if subject in ("im", "i'm") and verb in ("like", "liking"):
            # "im like this every morning" is a state, not a taste: nobody says "i am like" to
            # mean they are fond of something, and the state readings answer it.
            return None
        thing = _the_thing(raw)
        if verb in _DISLIKE_VERBS:
            read = _the_stance(thing, False)
        elif verb in _LIKE_VERBS:
            if verb == "prefer" and re.search(r"\bto\b", thing):
                # "i prefer tea to coffee" compares two things, so a question about how long they
                # have been into one of them is not the reply. The receipt answers it better.
                return None
            read = _the_stance(thing, True)
        else:
            return None
        if not read:
            return None
        # The manner takes a pool of its own only when there is one: "i like my coffee" is the
        # plain pool, and the manner frames are for a line that named both.
        return (_a_manner_kind(read[0]) if manner else read[0]), read[1], manner
    return None


# A weekday, a month or a holiday is a name, and a name keeps its capital in the middle of a
# sentence: "Fair enough - christmas would get to anyone" reads as a typo. The person typing it
# in lower case does not make it a common noun, so these are put back as they are written.
_PROPER = frozenset((
    "monday", "mondays", "tuesday", "tuesdays", "wednesday", "wednesdays", "thursday",
    "thursdays", "friday", "fridays", "saturday", "saturdays", "sunday", "sundays",
    "january", "february", "march", "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "christmas", "xmas", "easter", "halloween", "new year",
    "new years", "valentines", "valentine's", "boxing day",
))


def _as_a_name(thing):
    """The first word of the thing with its capital back, when it is a name rather than a word."""
    words = thing.split(" ", 1)
    head = words[0].lower().strip(",.")
    if head not in _PROPER:
        return thing
    return words[0][0].upper() + words[0][1:] + ((" " + words[1]) if len(words) > 1 else "")


def _in_a_sentence(thing):
    """The person's own words for the thing, lowercased mid-line: "the rain", not "The rain"."""
    if not thing or _as_a_name(thing) == thing and thing.split(" ")[0].lower().strip(",.") in _PROPER:
        return thing
    return thing[0].lower() + thing[1:]


def _as_yours(thing):
    """The person's own thing as the bot would name it: "my flat" is "your flat" to a friend."""
    return re.sub(r"^(my|our)\b", "your", thing, flags=re.I)


def _at_the_front(thing):
    """The person's own words for the thing, with a capital, for a line that opens on it."""
    return thing[0].upper() + thing[1:] if thing else ""


def reply_for(text, memory=None):
    """The reply for a stated like or dislike, or None when the line is not one."""
    read = _read(text)
    if not read:
        return None
    kind, thing, manner = read
    thing = _as_a_name(_as_yours(thing))
    # A template that opens on the thing starts a sentence with it, and one that carries it
    # mid-line reads "What is it about The rain...", which is how a form letter reads.
    options = [
        line.format(thing=_at_the_front(thing) if line.startswith("{thing}")
                    else _in_a_sentence(thing),
                    manner=_at_the_front(manner) if line.startswith("{manner}")
                    else manner)
        for line in _BY_KIND[kind]
    ]
    return fallback._choose(options, memory or {}, _clean(text), seed_text=_clean(text))
