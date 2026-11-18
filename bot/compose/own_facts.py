"""A question about a fact of the person's own life, where the bot has not been told it.

"how many brothers do i have" got the search hedge ("I don't know enough to answer that honestly.
A search should sort you out quickly") - which is nonsense: no search engine knows how many
brothers the person typing has. "whats my middle name" got the same. The store answers these fine
when it was told (`memory_store`: "You told me you're 34", "Your sister is called Emma"), so what
is left is the case where nobody ever said it, and the honest answer there is not a search engine.
It is STYLE.md's "Not knowing, honestly" in its plainest form: only they know, say so in a few
words, and ask - which is also the one move that turns the gap into the fact the store can keep.

The question is read here, not composed from a list of facts: "how many X do i have" becomes "how
many X you have", "whats my X" becomes "what your X is", "when is my X" becomes "when your X is".
So the reply says the thing back in the person's own words and then says the true part.

Narrow on purpose. It takes a question about themselves - "my", "i have", "am i" - whose subject
is a thing of their own life: family, a name, an age, a birthday, a home, work, a pet, an
appointment. A how-to ("how do i lose weight"), a fact about the world ("how many people live in
wales"), a question about the bot ("whats your name"), an ask with no subject of theirs in it, and
anything the store or a card already answers keep the reply they had.
"""
import re

from . import pick

# Words a recall turns on that carry no subject of their own: the thing asked about is what is
# left after these are gone ("what did i say about the walking").
STOP_WORDS = frozenset("""about the a an and or but that this it its was were is are be been
did do does say said tell told mention mentioned you your me my i we us our again""".split())

# A thing of their own life, the kind only the person can tell you. Kept as families of words
# rather than whole phrases, because the question is the person's own and there are as many of
# them as there are people: "my sister", "my kids", "my nan", "my landlord", "my shift".
OWN_WORDS = frozenset((
    # family and the people around them
    "mum", "mom", "mother", "dad", "father", "parent", "parents", "brother", "brothers",
    "sister", "sisters", "sibling", "siblings", "son", "sons", "daughter", "daughters", "kid",
    "kids", "child", "children", "baby", "wife", "husband", "partner", "nan", "nana", "gran",
    "granny", "grandma", "grandad", "grandpa", "grandparents", "aunt", "auntie", "uncle",
    "cousin", "cousins", "niece", "nephew", "inlaws", "family", "flatmate", "housemate",
    "landlord", "neighbour", "neighbours", "boss", "manager", "colleague", "carer",
    # a name, an age, a date of their own
    "name", "surname", "middlename", "nickname", "age", "birthday", "birthdate", "dob",
    # home, work, money, records
    "address", "postcode", "house", "flat", "home", "rent", "mortgage", "job", "work", "shift",
    "shifts", "rota", "wage", "wages", "salary", "pay", "holiday", "holidays", "leave",
    "appointment", "appointments", "referral", "prescription", "meds", "medication", "tablets",
    "results", "record", "records", "account", "bill", "bills", "order", "budget", "savings",
    # pets and possessions they keep track of
    "dog", "dogs", "cat", "cats", "pet", "pets", "puppy", "kitten", "car", "van", "bike",
))

# "how many brothers do i have", "how much holiday have i got left"
HOW_MANY = re.compile(r"^how (many|much)\s+(.+?)\s+(?:do|did) i have(?: left)?$")
HOW_MANY_GOT = re.compile(r"^how (many|much)\s+(.+?)\s+have i got(?: left)?$")
HOW_OLD = re.compile(r"^how old am i$")
# "whats my middle name", "what is my dogs name called", "whats my rent again"
WHAT_MY = re.compile(r"^what(?:s| is| was)?\s+my\s+(.+?)$")
# "when is my appointment", "what time is my shift"
WHEN_MY = re.compile(r"^(?:when|what time)(?:s| is| was)?\s+my\s+(.+?)$")
# The same question with a verb in it - "when does my shift start", "when will my pay go in" -
# which is asked about a timetable rather than a fact, and is answered with the place it is kept.
WHEN_AUX_MY = re.compile(r"^(?:when|what time)\s+(?:does|do|did|will|should|can)\s+my\s+(.+?)$")
# "wheres my car", "where is my appointment"
WHERE_MY = re.compile(r"^where(?:s| is| was)?\s+my\s+(.+?)$")

# The pools. Every line says the same three true things - it is not known here, only they know it,
# and saying it lets the bot keep it - because that is all the bot can honestly say, and the
# wording is what stops it sounding like a form.
HAVEN_T_SAID = (
    "You haven't told me {q}, so I've no way to know - tell me and I'll remember it.",
    "I don't know {q}: that's yours, not something I can look up. Tell me and I'll keep it.",
    "I only know what you tell me, and you've not said {q}. What's the answer?",
)
# The same thing said when the clause reads better as the question it came from: "how many
# brothers do you have? You've not said, so only you know - tell me and I'll keep it."
AS_THE_QUESTION = (
    "{Q}? You've not said, so only you know - tell me and I'll remember it.",
    "{Q}? I can't look that up: it's about you. Say it once and I'll keep it.",
)

# A how-to is a different line and has an answer of its own; "how do i" is not a fact question.
HOW_TO = re.compile(r"\bhow (?:do|can|could|should|would|might) i\b")
# A question about the bot, not about them: "whats your name", "how old are you".
ABOUT_BOT = re.compile(r"\b(?:you|your|yours|yourself)\b")

# The one fact about themselves the bot does know without being told: whether it can see the chats
# before this one. "can you see my chats with you from before" got the search hedge - "A search
# should sort you out quickly" - which is the worst thing on this page, because a search engine
# certainly cannot see their chats with this bot. The bot is the only thing in the world that can
# answer it, and the answer is the shape of the program: nothing carries over, but what is said
# here does. "do you remember what i said last time" keeps the composer's own memory pool
# (`ABOUT["memory"]`); this reading is for the lines that name the other chats, which that pool's
# phrase list does not carry.
CHAT_WORDS = frozenset((
    "chat", "chats", "conversation", "conversations", "message", "messages", "history",
    "transcript", "transcripts", "logs",
))
# What the person does with them, and what the bot does with them. These verbs are enough on their
# own - "can you read my old chats", "do you keep our chats", "what do you do with our chats" - so
# the past word below is only needed for the vaguer ones.
A_HAND_ON_THEM = re.compile(
    r"\b(?:see|read|open|look at|look back|check|bring up|pull up|access|scroll back|"
    r"go back to|remember|recall|keep|store|save|hold|show me|do with)\b")
THE_OTHER_CHATS = re.compile(
    r"\b(?:see|read|open|look at|look back|check|bring up|pull up|access|scroll back|"
    r"go back to|remember|recall|find|keep|store|save|hold|show me|know about|do with)\b")
# "from before", "last", "earlier", "past", "old", "yesterday": the chats that are not this one.
OTHER_THAN_THIS = re.compile(
    r"\b(?:before|earlier|previous|previously|past|old|last|other|others|yesterday|prior|"
    r"last time|history)\b")
# "is there a list of my chats", "any record of our conversations": the same ask as a question
# about a record rather than about an act of reading.
A_RECORD_OF_THEM = re.compile(
    r"\b(?:is|are) there (?:a |any |some )?\b.{0,24}\b(?:list|record|records|history|log|"
    r"logs|copy|transcript)\b|\bdo you (?:have|keep|store) (?:a |any )?(?:record|records|"
    r"list|history|log|logs|copy|transcript)\b")
# Said as a question about what was said rather than about the chats themselves: "do you know what
# we talked about yesterday", "what did we say before this". Anything without one of these past
# words is this conversation's own recall, which the store answers.
SAID_IN_A_PAST_CHAT = re.compile(
    r"\b(?:what|everything|all) (?:we|i) (?:said|talked about|wrote|asked)\b.{0,30}"
    r"\b(?:before|earlier|yesterday|last time|previous|in another chat|in other chats)\b")
# Whether this chat teaches the bot anything. "do you learn from our chats" is answered by the
# composer's own learning pool, and its twin "do you learn from these chats" - one word different
# - reached the search hedge, which is nonsense twice over: no page knows how this program works,
# and the person asking deserves the answer in the conversation. Nothing is trained as we talk,
# and what is said here is used here.
LEARNING_ASK = re.compile(
    r"\b(?:learn|learns|learning|train|trains|training|trained|teach|teaches|teaching|"
    r"update|updates|updating|improve|improves|improving|pick (?:things |stuff )?up|"
    r"pick up on)\b|\b(?:do|will|would|are|did)\s+(?:you|u)\s+get(?:ting)?\s+better\b")
# Who is doing it, and to what: the bot, and this conversation (or the person's own words).
TAUGHT_BY_THIS = re.compile(
    r"\b(?:teach|teaches|show|shows|tell|tells|give|gives|feed|feeds)\s+(?:you|u)\b|"
    r"\b(?:you|u)\s+(?:learn|learning|train|training|pick\w*)\b.{0,30}"
    r"\b(?:from|on|off)\s+(?:me|what i|us|this|my|our|these|the chats)\b|"
    r"\b(?:learn|train)\w*\s+(?:on|from)\s+(?:my|our|these|this)\b|"
    r"\blearn from me\b|\b(?:do|will|would|are|did)\s+(?:you|u)\s+get(?:ting)?\s+better\b")
# The store's own tells: if the line asks to be reminded of something already said, the store
# answers it and this never runs. It is here only so a line that lost its memory keeps the
# composer's reply rather than getting a second "you haven't told me".
SAID_BEFORE = re.compile(r"\b(?:again|remind me|did i say|did i tell you)\b")

# Every line says the two halves of the true answer: nothing carries over, and what is said here
# does. A promise of more would be a lie about the program; a bare "no" would leave the person with
# nothing to do next, which is what the hedge did.
NO_OTHER_CHATS = (
    "No: each chat starts empty for me, so nothing from another conversation comes through. "
    "Everything you tell me in this one stays with me, though - say it here and I'll use it. "
    "What was it about?",
    "I can't open earlier chats - a new one starts with nothing in it. What you and I say in "
    "this chat I do keep, so tell me here and I'll pick it up from there. What were you trying "
    "to find?",
    "There's no history on my side: what we say stays in this conversation, and a new chat "
    "begins blank. So say it once more here and I'll have it. What was it?",
)

# The two halves of that answer again, in the other direction: nothing is trained as we talk, and
# what is said here is used here. Every line is a plain account of the program, because that is all
# there is to say.
NO_TRAINING = (
    "No training as we talk: I'm a program with a lot of everyday things in it, and what I pick "
    "up is only what you say here, while we are in this chat. Nothing you tell me teaches me for "
    "the next person.",
    "I don't learn from the chat, no - nothing is fed back in. I'm the same program at the end of "
    "it as at the start, with everything you said in front of me while we talk.",
    "Nothing I hear changes what I know: no training, no memory of it afterwards. What you say "
    "does get used - here, in this conversation, as we go.",
)

# A chat word is only about the person's chats when it is spoken of as theirs: "my chats", "our
# last conversation", "the history". A bare one is the word doing another job - "are there logs in
# the garden", "a good chat" - so the determiner in front of it is what makes it theirs.
THEIR_OWN_WORD = frozenset((
    "my", "our", "the", "these", "those", "your", "all", "any", "every", "this", "that",
    "previous", "past", "old", "last", "earlier", "other", "another", "same",
))


def _names_their_chats(clean):
    """True when the line speaks of the person's own chats, not of the word by itself."""
    tokens = re.findall(r"[a-z']+", clean)
    for index, word in enumerate(tokens):
        if word not in CHAT_WORDS:
            continue
        if index and tokens[index - 1] in THEIR_OWN_WORD:
            return True
        if index > 1 and tokens[index - 2] in THEIR_OWN_WORD:
            return True
        # "chat history", "conversation history": the second word is the one being asked about.
        if index > 1 and tokens[index - 2] in CHAT_WORDS:
            return True
    return False


def about_earlier_chats(text, memory):
    """A reply for a question about the chats before this one, or None.

    The bot is the only thing that can answer it, so a search hedge is the one reply that is
    certainly wrong. Narrow on purpose: the line has to name those chats ("chats", "conversation",
    "history") with a word that puts them in the past ("before", "last", "old", "yesterday"), or
    ask for a record of them. A line about this conversation - "what did i tell you my name was" -
    is the store's, and one that names something to be recalled keeps its own answer.
    """
    if not text:
        return None
    clean = " ".join(text.lower().replace("\u2019", "'").split()).strip(" ?.!,")
    if not clean:
        return None
    if not _names_their_chats(clean) and not SAID_IN_A_PAST_CHAT.search(clean):
        return None
    if _names_their_chats(clean):
        # A chat word on its own is not this ask - "we had a good chat" is a statement. Something
        # has to be asked of the bot: what it does with them, or whether a record of them exists.
        if not (THE_OTHER_CHATS.search(clean) or A_RECORD_OF_THEM.search(clean)):
            return None
        if not (OTHER_THAN_THIS.search(clean) or A_RECORD_OF_THEM.search(clean)
                or A_HAND_ON_THEM.search(clean)):
            return None
    # "we talked about the car before this", said with no question in it, is not an ask about the
    # bot's memory of other chats: something has to be asked of the bot itself.
    if not re.search(r"\b(?:you|your|u|show me)\b", clean) \
            and not A_RECORD_OF_THEM.search(clean):
        return None
    return pick(NO_OTHER_CHATS, memory, text)


def learns_from_the_chat(text, memory):
    """A reply for "do you learn from this chat", "will you get better", or None.

    The same rule as `about_earlier_chats`: the bot is the only thing that knows the answer, so a
    search hedge is certainly wrong. Narrow - the line has to be about the bot learning, from this
    conversation or from the person, and a question about the person learning ("how do i learn to
    drive", "can i learn python at 40") is not this line.
    """
    if not text:
        return None
    clean = " ".join(text.lower().replace("\u2019", "'").split()).strip(" ?.!,")
    if not clean or not LEARNING_ASK.search(clean):
        return None
    if not re.search(r"\b(?:you|u)\b", clean):
        return None
    if not TAUGHT_BY_THIS.search(clean):
        # "do you learn from these chats": the thing being learned from has to be this
        # conversation, which is the chat word spoken of as theirs.
        if not (_names_their_chats(clean)
                and re.search(r"\b(?:these|this|our|the)\b", clean)):
            return None
    # A line about learning the thing itself is the knowledge base's: "can you help me learn
    # french", "do you know a good way to learn spanish".
    if re.search(r"\b(?:help|teach|show) me\b", clean) \
            or re.search(r"\bhow (?:do|can|could) i\b", clean):
        return None
    return pick(NO_TRAINING, memory, text)


# The same question in a shorter shape, with the thing implied rather than said with "my":
# "when do i work again", "which days do i work", "how many hours do i work", "when do i get
# paid". Each of these reached the search hedge on main - "A search should sort you out quickly"
# for a rota that exists in an app with the person's name on it.
WHEN_I = re.compile(r"^(?:when|what time|what day|which day|what days|which days|how many hours)"
                    r"\s+(?:do|did|will|should|am|can|have)\s+i\b(.*)$")
# "when is payday", "when is my payday": the same gap with no other word in it at all.
PAY_DAY = re.compile(r"^when(?:s| is| was)?\s+(?:my\s+)?pay ?day$")

# Which words make a WHEN_I line about their own timetable rather than about the world's. A
# course, a race and a roast all have a start and a finish, and none of those is on a rota.
ROTA_WORDS = frozenset(("work", "works", "working", "shift", "shifts", "rota", "hours",
                        "overtime", "oncall"))
# The ones that cannot be a verb in a phrasal phrase: nothing says "shift out" or "hours on", so
# a line with one of these in it is about the timetable whatever else it says.
ROTA_NOUNS = frozenset(("shift", "shifts", "rota", "hours", "overtime", "oncall"))
# "paid" and not "pay": "when do i have to pay" is a bill, and a bill is not a pay date.
PAY_WORDS = frozenset(("paid", "payday", "wage", "wages", "salary"))

# The reply names the one place that settles it and asks for the fact, which is also the move that
# lets the store keep it. No hour and no date is ever guessed at.
ON_THE_ROTA = (
    "Your rota isn't something I can see, so read the hours off it and tell me and I'll keep them.",
    "That lives on your rota rather than anywhere I can see, so tell me what it says.",
    "No window on your rota from this end, sorry, so say the hours and I'll remember them.",
)
ON_THE_PAYSLIP = (
    "A pay date is set in your contract, not known here, so tell me the date and I'll keep it.",
    "Your pay date is on the contract you signed, so say it once and I'll remember it.",
)
_THE_PLACE = {"rota": ON_THE_ROTA, "payslip": ON_THE_PAYSLIP}


def _the_place(text):
    """Which place settles a question about their own timetable, or None.

    "when do i work again" and "which days do i work" are the rota; "when do i get paid" and
    "when is payday" are the contract. A line that says start, finish or clock in with no work
    word in it is about something else - a course, a race, a roast - and keeps what it had.
    """
    if PAY_DAY.match(text):
        return "payslip"
    for pattern in (WHEN_I, WHEN_MY, WHEN_AUX_MY):
        found = pattern.match(text)
        if not found:
            continue
        tail = set(re.findall(r"[a-z]+", found.group(1)))
        if tail & PAY_WORDS or ("pay" in tail and ("in" in tail or "into" in tail)):
            return "payslip"
        if tail & ROTA_WORDS:
            # A work word that is not a word about work: "when do i work out", "when can i
            # work out", "when do i work on my essay". `work out` is a gym and `work on` is
            # whatever the essay is - neither has a shift in it, and the rota line would be
            # answering a question nobody asked. The rota words that cannot be the verb
            # (shift, hours, overtime) settle it on their own, and "on call" is kept because
            # there `on` belongs to the work.
            said = found.group(1)
            if not (tail & ROTA_NOUNS):
                if re.search(r"\bon[-\s]?call\b", said):
                    return "rota"
                said = re.sub(r"\bwork(?:s|ing)?\s+(?:out|on)\b", "", said)
                tail = set(re.findall(r"[a-z]+", said))
                if tail & ROTA_WORDS:
                    return "rota"
                return None
            return "rota"
        return None
    return None


def _has_a_shape(text):
    """True when the line is one of the question shapes below, whatever its tail is."""
    if HOW_MANY.match(text) or HOW_MANY_GOT.match(text) or HOW_OLD.match(text):
        return True
    return any(pattern.match(text) for pattern in (WHAT_MY, WHEN_MY, WHERE_MY))


def _as_clause(text):
    """The question as the thing they have not said: "how many brothers you have"."""
    found = HOW_MANY.match(text) or HOW_MANY_GOT.match(text)
    if found:
        many, thing = found.groups()
        return f"how {many} {thing} you have"
    if HOW_OLD.match(text):
        return "how old you are"
    for pattern in (WHAT_MY, WHEN_MY, WHERE_MY):
        found = pattern.match(text)
        if found:
            tail = found.group(1).strip()
            if re.search(r"\bcalled$", tail):
                return f"what your {tail}"
            if pattern is WHEN_MY:
                return f"when your {tail} is"
            if pattern is WHERE_MY:
                return f"where your {tail} is"
            return f"what your {tail} is"
    return None


def _as_question(clause):
    """The same clause turned back into the question a person would ask: "how many brothers you
    have" -> "how many brothers do you have"."""
    if clause.startswith(("how many", "how much")):
        return clause.replace(" you have", " do you have")
    if clause.startswith("how old you are"):
        return "how old are you"
    for head, ask in (("what your ", "what is "), ("when your ", "when is "),
                      ("where your ", "where is ")):
        if clause.startswith(head):
            tail = clause[len(head):]
            if tail.endswith(" is"):
                tail = tail[:-3]
            return ask + "your " + tail
    return clause


# A tail that is a noun phrase takes "what your X is" and reads right. A tail with a verb or a
# preposition in it does not: "what is my mum allergic to" is not "what your mum allergic to is",
# and "when is my mum coming" is not "when your mum coming is". Those are said back as the
# question they are instead, which keeps every word where the person put it.
NOT_A_NOUN_PHRASE = re.compile(r"\b(?:to|for|with|about|at|in|on|from|by|due|like|doing|going|"
                               r"coming|getting|allowed|before|after|now|then|anymore|"
                               r"originally|anyway)\b|\w+ing\b")


def _the_thing(text):
    """The word the question turns on, when it is a thing of their own life."""
    words = re.findall(r"[a-z]+", text)
    for word in words:
        if word in OWN_WORDS:
            return word
    # A plural the list does not carry ("brothers") is caught by its singular.
    for word in words:
        if word.endswith("s") and word[:-1] in OWN_WORDS:
            return word[:-1]
    return None


def _second_person(text):
    """The person's own question with themselves in the second person, every word in its place:
    "what was my budget" -> "what was your budget"."""
    out = re.sub(r"\b(whats|wheres|whens|hows)\b",
                 lambda m: {"whats": "what's", "wheres": "where's", "whens": "when's",
                            "hows": "how's"}[m.group(1)], text)
    out = re.sub(r"\bmy\b", "your", out)
    out = re.sub(r"\bdo i have\b", "do you have", out)
    out = re.sub(r"\bhave i got\b", "have you got", out)
    out = re.sub(r"\bam i\b", "are you", out)
    return out


def _capital(clause):
    return clause[:1].upper() + clause[1:]


def answer_for(text, memory):
    """A reply for a fact question about the person that nobody ever told the bot, or None."""
    if not text:
        return None
    clean = " ".join(text.lower().replace("\u2019", "'").split()).strip(" ?.!,")
    if not clean or len(clean.split()) > 10:
        return None
    if ABOUT_BOT.search(clean) or HOW_TO.search(clean):
        return None
    # A question about their own timetable in its shorter shape comes before the "again" fence:
    # "when do i work again" is not a request to be reminded of something the store was told, and
    # this reader is only ever asked when the composer had nothing.
    place = _the_place(clean)
    if place:
        return pick(_THE_PLACE[place], memory, text)
    if SAID_BEFORE.search(clean):
        return None
    # A question that names no thing of theirs is not this reader's line, however it is shaped:
    # "how many do i need" and "whats my best option" are about the answer's own subject.
    if not _the_thing(clean) and not HOW_OLD.match(clean):
        return None
    if not _has_a_shape(clean):
        return None
    clause = _as_clause(clean)
    if clause and NOT_A_NOUN_PHRASE.search(clause.split("your", 1)[-1]):
        # A tail with a verb or a preposition in it is said back as the question instead.
        clause = None
    # One pool for the clause said out loud, one for the question said back; which one answers is
    # the composer's own chooser, so the same gap is not answered in the same words every time.
    if clause is None:
        return pick(AS_THE_QUESTION, memory, text).format(
            Q=_capital(_second_person(clean)), q=clean)
    pool = HAVEN_T_SAID if len(clause.split()) > 4 else AS_THE_QUESTION
    line = pick(pool, memory, text)
    # The question is the one they asked, with their own words in the second person, so the
    # tense and the word order are theirs: "what was my cat called" comes back as "what was your
    # cat called", not "what is your cat called".
    question = _capital(_second_person(clean))
    return line.format(q=clause, Q=question)


# --- an ask about what they said ---------------------------------------------------------------
# "where did i say we were going", "how often did i say i go", "did i mention the boiler": the
# question is about this chat, and the answer is a line they said themselves. The store's date
# reader took the "say" for the event and answered "No - that's in February." - a confident wrong
# answer about a trip - and the frequency form reached the search hedge. Neither is a gap in what
# the bot knows: it kept the line.
SAID_ASK = re.compile(
    r"\b(?:(where|what|when|why|who|how\s+often|how\s+many\s+times)\s+)?"
    r"did\s+(?:i|we)\s+(?:ever\s+)?(?:say|tell\s+you|mention)\b", re.I)
# A frequency ask is about repetition, not about whether the thing has happened yet: "how often
# do i go" met "No - that's in February." for the same reason.
FREQUENCY_ASK = re.compile(r"\bhow\s+(?:often|many\s+times)\b", re.I)
# An ask about a property of the thing - "how old did i say the phone was", "what colour did i say
# the car was". The topic word alone does not answer it: a line about the phone with no age in it
# is the nearest line, not the answer.
PROPERTY_ASK = re.compile(
    r"\bhow\s+(?:old|big|heavy|long|far|tall|late|early)\b|\bwhat\s+colou?r\b", re.I)

# A line that carries a rate, which is what a "how often did i say" asks about.
A_RATE = re.compile(r"\b\d+\s*(?:times?|x)\b|\b(?:once|twice|daily|weekly|monthly)\b"
                    r"|\bevery\s+(?:day|week|month|year|morning|night)\b")
# Verbs with no subject of their own: "how often did i say i go" names no thing, so a line that
# does not share the word is still the line being asked about.
GENERIC_WORDS = frozenset("""go goes going went do does doing get gets got have has had make makes
made take takes took put see saw look start stop carry""".split())
SAID_POOL = (
    "You told me: \u201c{said}\u201d",
    "That was you, not me: \u201c{said}\u201d",
    "From your own words: \u201c{said}\u201d",
)
NOT_A_RECORD = (
    "You've not said that to me yet, so there's nothing to hand back - tell me and I'll keep it.",
    "I've nothing on that from you: it's yours to tell me, and then it's kept.",
)
# The same honest limit, with the nearest thing they did say on the table: "what did i say i was
# cooking" after "what about something with lentils" has no line about cooking, but a bare "you've
# not said that" throws away the one line the person can recognise.
NOT_A_RECORD_BUT = (
    "You've not said that to me, but the nearest you've given me is: \u201c{said}\u201d",
    "Nothing of yours on that yet - the closest is \u201c{said}\u201d, and I'll keep the rest when you say it.",
)


def _their_own_lines(memory):
    """The lines the person said, newest first, from the store's own record of the turns."""
    lines = []
    for turn in reversed((memory or {}).get("turns") or []):
        said = str((turn or {}).get("user") or "").strip()
        if said and said.lower() not in [line.lower() for line in lines]:
            lines.append(said)
    for topic in reversed((memory or {}).get("topics") or []):
        said = str((topic or {}).get("text") or "").strip()
        if said and said.lower() not in [line.lower() for line in lines]:
            lines.append(said)
    return lines


def _stem(word):
    """Enough of a stem to see "walking" and "walk" as one subject, and no more."""
    word = word.lower()
    for tail in ("ing", "ed", "es", "s"):
        if len(word) > 4 and word.endswith(tail):
            return word[: -len(tail)]
    return word


def said_back(text, memory):
    """The line of theirs the ask is about, said back, or None when the line is not this ask.

    Only a recall is read here - the wrapper is "did i say/tell/mention" - and the reply is a
    quotation, never a fact, so nothing can be invented. Where the ask names something, the line
    that shares the most of it is chosen, so a redone "what did i say about walking" does not come
    back with the trip; where it names something no line carries, the honest answer is that it was
    never said, rather than the newest line put in their mouth.
    """
    if not text:
        return None
    clean = " ".join(text.lower().replace("\u2019", "'").split()).strip(" ?.!,")
    found = SAID_ASK.search(clean)
    if not found:
        return _the_one_rate_on_record(clean, memory, text)
    # The turn being answered is already in the record the runtime keeps, and quoting a question
    # back at the person who just asked it is not an answer.
    lines = [line for line in _their_own_lines(memory)
             if _stemmed(line) != _stemmed(clean)]
    if not lines:
        return pick(NOT_A_RECORD, memory, text)
    if FREQUENCY_ASK.search(clean):
        # "how often did i say i go": the ask is about repetition, so the line that carries a
        # rate is the one being asked about, whatever verb the wrapper left behind.
        for line in lines[:8]:
            if A_RATE.search(line):
                return pick(SAID_POOL, memory, text).format(said=line)
    asked = [_stem(word) for word in re.findall(r"[a-z']+", clean[found.end():])
             if word not in STOP_WORDS and _stem(word) not in GENERIC_WORDS]
    best, best_score = lines[0], 0
    for line in lines[:8]:
        words = {_stem(word) for word in re.findall(r"[a-z']+", line)}
        score = sum(1 for word in asked if word in words)
        if score > best_score:
            best, best_score = line, score
    if asked and not best_score:
        # Nothing on the subject, but a line of theirs is still something they can recognise: name
        # it as the nearest thing rather than leaving them with an empty hand.
        return pick(NOT_A_RECORD_BUT, memory, text).format(said=lines[0])
    if PROPERTY_ASK.search(clean) and not re.search(r"\d", best):
        # The line is about the thing but says nothing about the property that was asked for, so
        # it is named as the nearest line rather than as the answer.
        return pick(NOT_A_RECORD_BUT, memory, text).format(said=best)
    return pick(SAID_POOL, memory, text).format(said=best)


# A frequency ask whose subject is a verb with nothing on it - "how often do i go", "how often do
# i do it" - reached the search hedge although the rate is on record. The rate reader cannot tell
# which rate is meant, and this one only answers when exactly one is on record, so the sentence
# it quotes is the only frequency the chat has.
HOW_OFTEN_MINE = re.compile(r"^how\s+(?:often|many\s+times)\s+(?:do|did|does)\s+(?:i|we)\s+"
                            r"(\w+)(?:\s+(?:it|that|this|them|now))?$", re.I)


def _stemmed(line):
    return " ".join(_stem(word) for word in re.findall(r"[a-z']+", str(line or "").lower()))


def _the_one_rate_on_record(clean, memory, text):
    found = HOW_OFTEN_MINE.match(clean)
    if not found:
        return None
    rates = [rate for rate in (memory or {}).get("rates") or [] if rate.get("said")]
    if len(rates) != 1:
        return None
    rate = rates[0]
    verb = _stem(found.group(1))
    what = _stem(re.sub(r"[^a-z]", " ", str(rate.get("what") or "").lower()).split()[0]) \
        if rate.get("what") else ""
    # The store's own rate reader answers the line that names the thing ("how often do i walk"),
    # and does it better than a quotation, so this only takes the verb with nothing on it.
    if verb not in GENERIC_WORDS or verb == what:
        return None
    return pick(SAID_POOL, memory, text).format(said=rate["said"])
