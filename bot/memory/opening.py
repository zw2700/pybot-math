"""The first line of a chat is answered, not filed.

`bot/memory/ack.py` says the fact back, which is the right thing on turn five: the person has
just added a detail to something the chat is already about, and "Noted: your daughter's 6 next
month" reads as the bot keeping it. As the *first* thing anybody says it is a filing cabinet -
nothing comes back about the six-year-old, the revision or the week. The person typed a line
expecting a reply, and a receipt of their own sentence is not one.

So on an opener the plain receipt frames are swapped for the one question a friend asks about
that fact. Which question follows the fact, not the words, and there are three shapes:

* a day coming for somebody - an age, a birthday, a start date: what the day will be like;
* something they are doing at a time - revising tonight, exams in May: how it is going;
* a standing state - six days a week, living with parents: how it is working out.

The subject's pronoun comes from the person the fact is about, so a line about their daughter
asks "how is she" and a line about themselves asks "how are you". The pools are read through
bot.compose.pick, so two openers of the same shape do not get the same sentence.
"""
import re

from ..compose import pick

# A day that is somebody's own: an age, a birthday, a term starting. "six next month", "70 next
# week", "starts year 3", "goes back to school on monday" are all a date for a person, and the
# question a friend asks is about the day itself.
A_DAY_FOR_SOMEONE = re.compile(
    r"(?:\b(?:turns?|is|'s|am|'m|are|'re|re) \d+\b|\b(?:im|i'm|i am) \d+\b|\b\d+ (?:next|this|in|on)\b|"
    r"\bbirthday\b|\bbday\b)", re.I)
# A thing happening at a time: tonight, tomorrow, at the weekend, in May. The question is how it
# is going, because the person is in the middle of it or about to be.
A_TIME = re.compile(
    r"\b(?:tonight|this evening|this morning|this afternoon|tomorrow|the day after tomorrow|"
    r"next (?:week|month|year|weekend|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"this weekend|at the weekend|on monday|on tuesday|on wednesday|on thursday|on friday|"
    r"on saturday|on sunday|in (?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)|in the (?:morning|afternoon|evening)|later today|"
    r"for the rest of the (?:day|week))\b", re.I)
# A standing state is what they do with their week: a count of days, a place they live, a job
# they hold. Nothing is coming, so the question is what it is like.
A_STANDING_STATE = re.compile(
    r"\b(?:every (?:day|week|night|morning|month)|"
    r"(?:twice|three times|four times|five times|six times) a (?:day|week)|"
    r"\b(?:six|seven|five|four) days a week|"
    r"live with|live(s)? with|living with|"
    r"work(s)? (?:in|at|for|from|nights|shifts|weekends)|"
    r"have (?:two|three|four|five) (?:kids|children|jobs))\b", re.I)

# A taste: somebody loves, likes, enjoys or is into a thing. The verb has to come straight after
# the person, so "it smells like damp" and "what's the weather like" are not tastes.
A_TASTE = re.compile(
    r"^(?:and |so |but )?(?P<who>i|he|she|they|we|my (?:[\w']+ )?[\w']+)\s+"
    r"(?:really |just |absolutely |also |still )*"
    r"(?:loves?|likes?|enjoys?|prefers?|(?:is|are) (?:really |very |well )?(?:into|a (?:big )?fan of))\b",
    re.I)
# A taste said of a person is not a thing they are into: "i love you", "i like you a lot".
A_TASTE_OF_A_PERSON = re.compile(r"\b(?:you|me|him|her|them|us)\s*[.!]*\s*$", re.I)
# Nor is a crush a hobby: "i like a girl at work", "i like someone".
A_CRUSH = re.compile(r"\b(?:a (?:girl|boy|man|woman|lady|lad)|someone|somebody|anyone)\b", re.I)
# Nor is a person a pastime: "i love my mum" is said back as it is, and the store's receipt for it
# reads worse than the pool's question about a thing.
A_PERSON_AS_OBJECT = re.compile(
    r"\b(?:mum|mom|mother|dad|father|son|daughter|kids?|children|boys?|girls?|wife|husband|"
    r"partner|brother|sister|nana|gran|grandma|grandad|granny|family|parents|baby|friend|"
    r"mates?|neighbours?)\b", re.I)

# A term, a school year or an exam is a thing coming with a date of its own, so the question is how
# the person in it is feeling rather than what the day will be like.
A_START = re.compile(
    r"\b(?:starts?|starting|begins?|goes? back|going back|finish(?:es)?|leaves?|left) "
    r"(?:year|school|college|uni|university|nursery|reception)\b|"
    r"\b(?:has|sits?|taking|takes) (?:his|her|their|the) (?:gcses?|exams?|a levels?|mocks?)\b", re.I)

# Who the fact is about. The subject's own pronouns are the ones a friend uses in the question.
SHE = ("daughter", "sister", "mum", "mother", "mam", "nan", "nana", "gran", "granny",
       "aunt", "auntie", "wife", "girlfriend", "partner", "niece", "cousin", "girl",
       "granddaughter", "stepmum", "stepdaughter", "mother in law", "daughter in law",
       "sister in law")
HE = ("son", "brother", "dad", "father", "grandad", "granddad", "uncle", "husband",
      "boyfriend", "nephew", "cousin", "boy", "grandson", "stepdad", "stepson",
      "father in law", "son in law", "brother in law")
THEY = ("kids", "children", "parents", "friends", "twins", "boys", "girls", "little one",
        "little ones", "toddler", "baby", "child")

A_DAY_TAILS = (
    "{Thing} \u2014 what are you planning for it?",
    "{Thing}. What would {subj} like to do?",
    "{Thing} \u2014 is there anything {subj} {has} asked for?",
    "{Thing}. What {be} {subj} thinking of doing?",
)
# A taste is a fact about a person, not an entry in a form: "my mum loves gardening" was filed as
# "Noted: your mum loves gardening." The question a friend asks is about the thing they love.
A_LIKED_TAILS = (
    "{Thing} \u2014 what got {them} into it?",
    "{Thing}. Is it a new thing, or {has} {subj} always been keen?",
    "{Thing} \u2014 what's the best bit of it for {them}?",
    "{Thing}. How long has that been going on?",
    "{Thing} \u2014 is that a recent thing, or a lifelong one?",
)
A_DOING_TAILS = (
    "{Thing} \u2014 how {be} {subj} feeling about it?",
    "{Thing} \u2014 how {be} {subj} feeling about it?",
    "{Thing}. How's it going so far?",
    "{Thing}. How's it going so far?",
    "{Thing} \u2014 {be} {subj} looking forward to it?",
)
A_STATE_TAILS = (
    "{Thing} \u2014 how's that working out?",
    "{Thing}. How's that treating you?",
    "{Thing} \u2014 what's that like?",
)


# A day that has already been is not coming, so no question about it is a friend's: "i saw my sister
# at the weekend", "i got married in june", "i was going to cook a curry on saturday" all match a
# time word, and asking how the prep has been for a visit that already happened is nonsense.
A_PAST = re.compile(
    r"\b(?:yesterday|last (?:night|week|weekend|month|year|summer|christmas|monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday)|this (?:morning|afternoon)|earlier|ago|"
    r"used to|was going to|were going to|had|saw|met|went|got married|moved|spent|asked|rang|"
    r"kicked|took|cooked|bought|ate|paid|came|left|started|finished|arrived)\b", re.I)
# A number is not a day for somebody when it is money: "my rent is 900 in january" and "i spent 300
# on food this month" are not an age and no birthday is coming.
MONEY = re.compile(
    r"\b(?:rent|savings|bill|bills|budget|wage|wages|salary|debt|loan|cost|price|payment|"
    r"money|credit card|overdraft|mortgage)\b", re.I)
# A measure of the body is not an age: "my mum is 5 foot 4".
A_MEASURE = re.compile(
    r"\b(?:foot|feet|ft|cm|centimetres?|metres?|stone|kilos?|kilograms?|pounds?|inches|inch)\b", re.I)
# A baby said in months is not a birthday coming.
A_MONTHS = re.compile(r"\b\d+ months?\b|\bmonths? old\b", re.I)
# A stated thing that is not a day at all: nobody plans for their own date of birth.
NOT_AN_OCCASION = re.compile(r"\b(?:age|date of birth|dob|birthday|rent|savings)\b", re.I)
# A correction is not a fact about an occasion: "no i meant tomorrow" is a person putting the last
# line right, and they want to be understood, not asked how the prep has been.
A_CORRECTION = re.compile(r"(?:^\s*(?:no|nope|sorry)\b|\b(?:i (?:said|meant|told you|didn't say|did not say))\b)", re.I)


def _the_day_is_the_point(clean, match):
    """Whether the age is what the line is about rather than background: "my daughter is 14 and
    sleeping till noon" is a complaint with an age in it, not a birthday, and "i'm 34 and my wife
    is 32" has two days in it, so "it" would stand for neither of them."""
    if len(A_DAY_FOR_SOMEONE.findall(clean)) > 1:
        return False
    if len(re.findall(r"\b\d{1,3}\b", clean)) > 1:
        return False
    return not re.search(r"\b(?:and|but|n)\b", clean[match.end():], re.I)


def _names_my(lower, word):
    """Whether the line names that relation of theirs, however it is typed: "my daughter",
    "my daughters", "my daughter's 6", "my daughters' party"."""
    return bool(re.search(r"\bmy (?:\w+ )?" + word + r"(?:s|'s|s')?\b", lower))


def _who(clean):
    """"you" for a fact about the speaker, and the third person for one about somebody named."""
    lower = clean.lower()
    # A report of what somebody else said is not a fact about the reporter: "they said my mum is
    # 72" is a fact about her, and the day tail has to ask about her rather than about them.
    lower = re.sub(r"^\s*(?:and |so |but |well )?(?:they|he|she|people|someone|everyone)\s+"
                   r"(?:said|says|say|reckons?|thinks?|told me|tell me)\s+", "", lower)
    starts = re.match(r"^\s*(?:and |so |but |well )?(he|she|they|theyre|they're)\b", lower)
    if starts:
        who = starts.group(1)
        who = "they" if who.startswith("they") else who
        return who, ("are" if who == "they" else "is")
    for word in THEY:
        if _names_my(lower, word):
            return "they", "are"
    for word in SHE:
        if _names_my(lower, word):
            return "she", "is"
    for word in HE:
        if _names_my(lower, word):
            return "he", "is"
    return "you", "are"


def _said_before(memory):
    """Whether anything has been answered yet: the current line is already in the turns with no
    reply beside it, so the test is for a turn the bot has answered."""
    for turn in (memory or {}).get("turns") or []:
        if isinstance(turn, dict) and str(turn.get("bot") or "").strip():
            return True
    return False


def the_opening(thing, clean, memory):
    """The question about the fact, where the plain receipt would be the whole reply.

    Only the first line of a chat: once anything has been said the receipt is a detail landing on
    a conversation, which is what bot/memory/ack.py's frames are for."""
    if not thing or not clean:
        return None
    if _said_before(memory):
        return None
    # A day already had, money, a measure and a baby in months are all read by the patterns above
    # and none of them is the occasion a friend asks about, so they keep whatever answered them.
    if A_PAST.search(clean) or A_MEASURE.search(clean) or A_MONTHS.search(clean):
        return None
    if A_CORRECTION.search(clean):
        return None
    if MONEY.search(clean) or MONEY.search(thing) or NOT_AN_OCCASION.search(thing):
        return None
    subj, be = _who(clean)
    has = "have" if subj in ("you", "they") else "has"
    them = {"you": "you", "she": "her", "he": "him", "they": "them"}.get(subj, "you")
    taste = A_TASTE.match(clean)
    if taste and (A_TASTE_OF_A_PERSON.search(thing) or A_CRUSH.search(clean)
                  or A_PERSON_AS_OBJECT.search(clean[taste.end():])
                  or " but " in clean[taste.end():]):
        # A taste said of a person, a crush, a pastime stated as somebody's love for them, and a
        # line with two sides to it are all left to the store: none of them is one thing loved.
        taste = None
    if taste:
        pool = A_LIKED_TAILS
    day = None if taste else A_DAY_FOR_SOMEONE.search(clean)
    if day and _the_day_is_the_point(clean, day) and not NOT_AN_OCCASION.search(thing):
        # "is there anything you have asked for" is a question about a birthday present, and an
        # age of the speaker's own is not that: "im 34 this year" keeps the three tails that fit.
        pool = (tuple(t for t in A_DAY_TAILS if "asked for" not in t) if subj == "you"
                else A_DAY_TAILS)
        if subj == "you":
            # An age of the speaker's own has nothing planned for it, and "You're 34. What would
            # you like to do?" reads as an offer of an activity: ask about marking the day instead.
            pool = tuple("{Thing} \u2014 anything you're marking it with?"
                         if "would {subj} like to do" in tail else tail for tail in pool)
    elif day:
        return None
    elif taste:
        pass
    elif A_TIME.search(clean) or A_START.search(clean):
        pool = A_DOING_TAILS
    elif A_STANDING_STATE.search(clean):
        pool = A_STATE_TAILS
    else:
        return None
    said = pick(pool, memory, clean).format(Thing=thing[:1].upper() + thing[1:],
                                            subj=subj, be=be, has=has, them=them)
    return " ".join(said.split())
