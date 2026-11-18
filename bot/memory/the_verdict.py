"""Somebody with authority gave them a verdict, and the turn is the decision that follows it.

"the plumber said the whole lot needs replacing" was answered "Got it - the plumber said the whole
lot needs replacing", "the doctor said to come back in a week" with "Got it. Is there anything
you'd like a hand with?", and the roofer's six weeks with the card for botched work. The line is
never the trouble: the person already knows the words, and what a friend adds is what to do with
them - a quote in writing, a second price, what to ask before agreeing, when to ring back.

Four kinds, because the decision differs:

* a trade who has priced or condemned a thing ("the plumber", "the garage", "the roofer") - the
  money and the second opinion, and the bot can say whether a figure is in the usual range;
* a clinician with a plan ("the doctor said to come back in a week", "the physio") - the wait and
  what to do inside it, and that ringing back sooner is allowed;
* an office with a rule ("the council", "the bank", "the school") - the reason in writing and the
  step their own process has next;
* a date or a visit ("it would take six weeks", "he will be here between 8 and 12") - the wait
  itself and the call to make when the day goes by, whoever said it.

Everything here is a guard against taking a turn that is not this:

* never a question. "the garage says it needs new discs, is 350 about right" names a trade and a
  verdict, and the card behind it answers the figure; asked with a question mark the turn is the
  question, so this passes;
* never an emergency. "the doctor said to go to A&E now" and "she said to ring 999" belong to the
  safety module, whatever else is in the line;
* never a clinician's verdict about somebody else ("my mum", "she", "his bloods"): a body that is
  not the person's own is safety's turn;
* never a no that names nobody ("they said no"): the pools that answer a refusal already do it
  better than a stock line about a trade;
* never the person's own words ("i said that", "my sister said i should go"): a verdict here is
  somebody with authority, not anybody who spoke.
"""
import re

# Another person or animal in the line. A clinician's verdict about one of them is the safety
# module's turn, so the care pool passes on those: "my mum", "she", "his bloods". Written out here
# rather than imported from bot/compose/trouble.py: a memory module importing the composer closes
# a loop, and the modules that broke when it did were the ones answering "what did i tell you".
OTHERS = frozenset((
    "he", "she", "him", "her", "his", "hers", "they", "them", "their", "theirs",
    "mum", "mam", "mom", "mummy", "dad", "daddy", "father", "mother", "parent", "parents",
    "son", "daughter", "child", "kid", "kids", "baby", "toddler", "teenager", "boy", "girl",
    "husband", "wife", "partner", "boyfriend", "girlfriend", "fiance", "fiancee",
    "nan", "nana", "gran", "granny", "grandma", "grandad", "grandpa", "grandparents",
    "brother", "sister", "sibling", "aunt", "uncle", "cousin", "nephew", "niece",
    "friend", "mate", "flatmate", "housemate", "neighbour", "neighbor", "colleague",
    "boss", "manager", "carer", "dog", "cat", "puppy", "kitten", "pet", "pup",
))

# Somebody said something: the saying verb is what makes the line a report of a verdict.
SAID = re.compile(r"\b(?:said|says|say|told\s+me|reckons|quoted|quotes)\b")

# The person is the one who spoke ("no i said the plumber", "i told me not to"): that is a
# correction of what the bot has been talking about, and the pools that answer a correction own it.
SELF_SAID = re.compile(r"\bi\s+(?:said|say|says|told)\b")

# The bot is the one who spoke: "that thing you said about the boiler" is a question about the
# chat, not a verdict from a trade, and the answer is the thing the bot said rather than advice
# about getting a quote in writing. The same fence as SELF_SAID, from the other side.
YOU_SAID = re.compile(r"\byou\s+(?:said|says|say|told\s+me)\b")

CARE = frozenset((
    "doctor", "doctors", "gp", "nurse", "consultant", "physio", "physiotherapist",
    "midwife", "paramedic", "hospital", "clinic", "surgery", "radiographer",
    "optician", "podiatrist", "chiropodist", "dietician", "dietitian", "111", "nhs",
    # A dentist and an optometrist are the same kind of turn as an optician: a plan about the
    # person's own body, with a wait on it and nothing to negotiate. They were in TRADE, so "the
    # dentist said it needs a crown and a filling" got "Get it in writing, with the parts and the
    # labour apart, and one more quote before you say yes" - money advice for a tooth, and the file
    # disagreed with itself, because "optician" sat here and "optometrist" sat in TRADE (cyan-
    # trumpet on #9097).
    "dentist", "dentists", "optometrist", "optometrists",
))

TRADE = frozenset((
    "plumber", "mechanic", "garage", "garages", "roofer", "builder", "electrician", "engineer",
    "locksmith", "dealer", "fitter", "joiner", "tiler", "plasterer", "decorator", "glazier",
    # Not "shop": a shop is where a thing was bought, and what it says is a rule about returns -
    # "the shop says sale items are final" got "one more quote before you say yes" for a split sole
    # (long-boots-01). Consumer rights answer that, not a tradesman.
    "man", "tradesman", "contractor", "boiler", "drain", "drains", "surveyor",
))

OFFICE = frozenset((
    "council", "bank", "landlord", "landlady", "insurer", "insurance", "dwp", "jobcentre",
    "school", "teacher", "college", "university", "letting", "agent", "mortgage", "broker",
    "solicitor", "conveyancer", "planning", "housing", "ombudsman", "tribunal", "assessment",
    "assessor", "office", "authority",
))

# An emergency is the safety module's turn: checked before the kind is read at all.
EMERGENCY = re.compile(r"\b(?:999|911|112|116\s*123|ambulance|a\s*&\s*e|a\s+and\s+e|casualty|"
                       r"resus|crash\s+team|blue\s+light)\b")

# The line asks something: "is 350 about right", "should i say yes", "how long is that". The
# question has its own reply, and a stock line about quotes would answer past it.
ASKED = re.compile(r"\?|\b(?:should\s+i|shall\s+i|is\s+(?:that|it|this)|is\s+\d|how\s+(?:much|long)"
                   r"|worth\s+it|about\s+right|too\s+much|fair|reasonable|can\s+i|could\s+i)\b")

# A date or a visit instead of a price or a rule: nothing to weigh up and nothing to appeal, only
# a wait to sit through.
A_TIME = re.compile(r"\b(?:would\s+take|will\s+take|takes\s+(?:\w+\s+)?(?:weeks?|months?|days?)"
                    r"|(?:two|three|four|five|six|seven|eight|nine|ten|twelve|\d+)\s+"
                    r"(?:weeks?|months?|days?|fortnights?)"
                    # "come back in a week", "rest for a fortnight": the same wait said with
                    # one rather than a figure, which people say more often than "in one week".
                    r"|(?:in|for|of|after)\s+an?\s+(?:week|fortnight|month|day|few\s+days)"
                    r"|(?:coming|due|here|back|round|in)\s+(?:on\s+|at\s+|in\s+|by\s+)?(?:the\s+)?"
                    r"(?:mon|tues|wednes|thurs|fri|satur|sun)day"
                    r"|(?:coming|due|here|back)\s+(?:on\s+|at\s+|in\s+)?(?:the\s+)?"
                    r"(?:morning|afternoon|evening|weekend|afternoon|\d{1,2}(?:[.:]\d\d)?\s*(?:am|pm)?)\b"
                    r"|(?:coming|due|here|back)\s+(?:tomorrow|tonight|today|next\s+\w+|this\s+\w+)"
                    r"|be\s+here\s+(?:between|at|on|in|by)|sometime\s+(?:next|this)\s+week"
                    # "he will come in the morning" is a time of day with no clock on it, and the
                    # quote paragraph is the wrong answer to it: the day is what gets cleared.
                    r"|(?:come|comes|coming|call|call\s+in|turn\s+up)\s+(?:back\s+)?"
                    r"(?:in\s+the\s+|this\s+)?(?:morning|afternoon|evening)"
                    r"|first\s+week\s+of\s+\w+)\b")

# The care pool is about a wait, so the wait has to be in the line: a come-back, a review, a scan,
# a follow-up, or something to keep an eye on. A verdict that there is nothing to wait for has no
# "then" for any of the care lines to point at.
A_PLAN = re.compile(r"\b(?:come\s+back|coming\s+back|go\s+back|come\s+in\s+again|refer\w*|"
                    r"review\w*|follow\s*-?\s*up|check\s*-?\s*up|wait\w*|"
                    r"keep\s+an\s+eye|monitor\w*|bloods?|scan\w*|x-?rays?|prescription|"
                    r"appointment|another\s+look|see\s+how\s+\w+\s+goes)\b")

# A clinician has named a treatment, or a change in what they measured, and stopped there: "it
# needs a crown and a filling", "my eyes have changed", "the blood pressure is a bit high". There
# is no date to sit out and no plan to follow, so the two care pools above both pass on it, and the
# line fell to "I'm listening - say more if it helps" (main) or, once the dentist and the
# optometrist were read as care rather than a trade, to a cheer: an optometrist's bad news was
# answered "Nice one. How did the rest of it go?". What decides a treatment is what it means, what
# waiting costs, and what it costs - so that is the reply.
A_TREATMENT = re.compile(
    r"\b(?:crown|crowns|filling|fillings|root\s+canal|extraction|implant|implants|bridge|"
    r"dentures?|braces|invisalign|scale\s+and\s+polish|glasses|lenses|varifocals|"
    r"needs?\s+(?:doing|replacing|seeing\s+to)|has\s+to\s+come\s+out)\b")
A_CHANGE = re.compile(
    r"\b(?:changed|worse|a\s+bit\s+high|borderline|not\s+where\s+it\s+should\s+be|"
    r"something\s+there|wants?\s+watching)\b")

# The verdict is that it is over: "the plumber said he fixed it", "the garage said its done". No
# decision follows, and pushing a quote at somebody whose boiler now works is the wrong turn - the
# receipt the composer gives is the right one.
# The verdict is that there is nothing to decide either: "the nurse said the swab was clear",
# "the doctor said my bloods are fine". Reassurance has its own answer, and a line about ringing
# back is alarming after a clear result.
ALL_CLEAR = re.compile(r"\b(?:is|are|was|were|come|comes|came)\s+(?:back\s+)?(?:all\s+)?"
                       r"(?:fine|ok|okay|normal|clear|negative|healthy|nothing)\b"
                       r"|\bnothing\s+(?:wrong|to\s+worry|sinister|serious)\b|\ball\s+clear\b")

DONE = re.compile(r"\b(?:fixed|sorted|done|finished|put\s+right|all\s+working|working\s+now"
                  r"|no\s+charge|on\s+the\s+mend)\b")

# The verdict is praise or thanks, and there is nothing to decide after that either: "the teacher
# said good work", "the school said the play was lovely", "the council said thanks", "the plumber
# said thanks for the tea", "the garage said the car is ready". Every one of those was answered with
# "Get it in writing, with the parts and the labour apart" or "ask what the next step in their own
# process is" - the quote and the appeal after a thank-you (peach-gazelle on #9097). A wait or a
# plan in the line keeps its turn: "the dentist said good work, come back in six months" still has
# a date to sit out.
PRAISE = re.compile(r"\b(?:thanks?|thank\s+you|cheers|ta|well\s+done|good\s+(?:work|job)|"
                    r"lovely|great|brilliant|excellent|fantastic|perfect|happy|pleased|"
                    r"delighted|ready|no\s+charge|free\s+of\s+charge)\b")

# Good news has no next step to ask for either: "the bank said i can have a mortgage" was told to
# "ask what the next step in their own process is - most of these have a form or an appeal with a
# deadline", and there is nothing to appeal - the mortgage was offered (good-shelf on #9097). The
# offer has to be about the person ("i/we/you can have"): "the garage said the car can have a new
# gearbox" is a price to weigh, and keeps its turn.
GOOD_NEWS = re.compile(r"\bsaid\s+(?:that\s+)?(?:i|we|you)\s+(?:can|could|will|may)\s+have\b"
                       r"|\b(?:approved|accepted|went\s+through)\b")

# "my man said he will do the garden" is a promise from somebody of theirs, not a tradesman's
# verdict, and the possessive is what tells them apart: "the man said he will be here between 8 and
# 12" is a visit, "my man" is the person they live with (peach-gazelle on #9097).
MY_MAN = re.compile(r"\b(?:my|our|her|his|their)\s+(?:man|bloke|guy|fella|chap)\b")

# What to do with a price on a job: the same three things every time, and the bot can judge the
# figure itself once it is told.
TRADE_REPLIES = (
    "Get it in writing, with the parts and the labour apart, and one more quote before you say "
    "yes - two prices is the whole trick. Tell me the figure and I'll say whether it's in the "
    "usual range for the job.",
    "Ask what the cheapest version is that would still fix it, and what happens if it turns out to "
    "be something else once it's open. Put the figure to me and I'll tell you whether it's the "
    "going rate.",
    "Then ask for it in writing and price the job two ways - the whole lot, and the least that "
    "would get you through the year. If you give me the number I'll say whether it's fair.",
)

# A plan with a date on it: the wait is not the same as doing nothing.
CARE_REPLIES = (
    "Ring back before then if it gets worse - you don't have to sit out the wait for the date. "
    "Keep a short note of what changes day to day so the next appointment is worth having.",
    "Then go with the plan, and ring the surgery the moment something changes rather than waiting "
    "for the date. Write down what you want to ask so the ten minutes aren't wasted.",
    "That's the plan, then. Ask what would make them bring it forward, and keep a note of what "
    "happens between now and then - that note is what makes the next appointment quick.",
)

# The plan is a thing to watch rather than a date to sit out: "the consultant said to keep an eye
# on it", "the nurse said the bloods will tell us". None of the care lines above fit, because
# "before then" points at a date this line does not have.
CARE_PLAN_REPLIES = (
    "Then do as they said and keep a short note of what changes - what you noticed, when, and "
    "what made it better or worse. That note is exactly what they will ask for next time.",
    "Keep it simple and written down: date, what you noticed, and anything that made a "
    "difference. If it changes before you are seen again, ring and say so rather than waiting.",
    "Then watch for the change they named, and write down the first day you see it. A date and a "
    "description is what turns a worry into something they can act on.",
)

# A treatment named, or a change measured, with no date and no plan to follow it. The person has
# to decide whether to have it done and what it means, so the reply is the two questions that
# decide it - never a figure, because no figure here knows what their dentist charges.
CARE_TREATMENT_REPLIES = (
    "Ask them two things before anything is agreed: what it means in plain words, and what "
    "happens if you do nothing for a while. If it is treatment, get the price both ways - on the "
    "NHS band and privately.",
    "Get it in plain words first: what changes if you have it done, what happens if you wait, and "
    "what it costs either way. Write the answers down while they are fresh.",
    "Worth asking what the next step is and when it would need doing by. If money comes into it, "
    "ask for the price on the NHS and privately before you book anything.",
)

# A rule from an office: what their own process wants next, in writing.
OFFICE_REPLIES = (
    "Ask for it in writing, and ask what the next step in their own process is - most of these "
    "have a form or an appeal with a deadline, and whoever answers the phone will say which. "
    "Tell me what the letter says and I'll help you answer it.",
    "Get their reason in writing and ask what would change the answer. That reply is what an "
    "appeal or a second go hangs on, and I'll help you word it.",
    "Then ask them to confirm it in writing and how long the next step takes. Once you have their "
    "words I'll help you put your side of it.",
)

WAITING_REPLIES = (
    "Then keep the time clear and have what they need where they can get at it - paperwork, the "
    "boiler cupboard, the car keys on the table. Ring the office if nobody has turned up by the "
    "end of the slot; that call is what moves it.",
    "Put the day aside rather than the hour, and ring the office the moment the slot goes by "
    "without a word. If it slips again, ask them to hold the next appointment for you there and "
    "then.",
    "Then plan as if it happens and ring early if it doesn't - people who chase on the day get "
    "moved up the list. Have the details they will ask for written down: the job, the reference, "
    "and your number twice.",
)

# A job or a wait that is measured in weeks is not a slot to be in: "the roofer said it would take
# six weeks" was told "ring the office if nobody has turned up by the end of the slot", which is
# about a morning, not a roof. A span needs a start date and what happens if it slips; a clock window
# ("between 8 and 12", "some time after two") keeps WAITING_REPLIES.
A_SPAN = re.compile(r"\b(?:take|takes|took|taking|would\s+take|will\s+take)\b[^.]{0,20}?"
                    r"\b(?:two|three|four|five|six|seven|eight|nine|ten|twelve|\d+)\s+"
                    r"(?:weeks?|months?|days?|fortnights?)\b"
                    r"|\b(?:a|an|one)\s+(?:week|month|fortnight|day)\b"
                    r"|\b(?:in|for|of|after|another)\s+(?:two|three|four|five|six|\d+)\s+"
                    r"(?:weeks?|months?)\b")
A_WINDOW = re.compile(r"\b\d{1,2}(?::\d\d)?\s*(?:am|pm)\b|\bbetween\s+\d+|"
                      r"\bin\s+the\s+(?:morning|afternoon|evening)\b|"
                      r"\bany\s+time\s+after\b|\bo'?clock\b")

# A span of weeks gets the two things that hold it: the start date, and what happens if it slips.
SPAN_REPLIES = (
    "Ask when they start, not when they finish - a start date in writing is the only part anyone "
    "can be held to, and everything after it follows. Then agree what happens if the weather or "
    "the scaffold puts it back, and keep the last payment until the work is signed off.",
    "Get the start date and the end date in writing, with what counts as a delay and who pays for "
    "it. A job that long is worth a short weekly update by text, in one line, so nothing drifts "
    "without you knowing.",
    "Then put the dates in your diary and ask them to confirm the start in writing a week before. "
    "If it slips, ask for a new date there and then rather than ringing back later - the date they "
    "say out loud is the one that sticks.",
)

POOLS = ((CARE, CARE_REPLIES), (TRADE, TRADE_REPLIES), (OFFICE, OFFICE_REPLIES))


def _words(text):
    return re.findall(r"[a-z0-9'&]+", str(text or "").lower())


def _the_subject(clean):
    """The words before the saying verb: the party is the one who spoke.

    "the garage said it needs new discs" puts the party before the verb, and so does "my dentist
    told me". The words after it are what was said, and a party word there is somebody else in
    their words, not the speaker: "he says nobody at school likes him" is a boy talking about a
    school, and reading `school` as the party gave it "Ask for it in writing, and ask what the next
    step in their own process is" - office advice for a child who is being unkind to himself
    (good-shelf on #9097).
    """
    head = SAID.split(clean, 1)[0]
    return _words(head)


def _the_pool(words):
    """The pool for the party in the line, or None."""
    named = set(words)
    for parties, pool in POOLS:
        if named & parties:
            return pool
    return None


# Somebody spoken of by pronoun only ("he said hes coming thursday", "they want to charge me for it").
# The party is the one named a turn or two earlier, and reading it back is the whole point of a
# store: a plumber who was just talked about is still the plumber.
PRONOUN = re.compile(r"\b(?:he|she|him|her|they|them|his|their)\b")


def _last_party(game):
    """The pool for the party named in the last turn or two, or None.

    `game` is the memory dict: the turns are the person's and the bot's, and either can carry the
    party ("my boiler keeps losing pressure" then "he said its two days").
    """
    if not isinstance(game, dict):
        return None
    said = []
    for turn in (game.get("turns") or [])[-4:]:
        if isinstance(turn, dict):
            # Only what the person said. The bot's own replies carry every party word the bot
            # knows ("a broken boiler is an annoyance" inside a line about saving), and reading one
            # of those back turned "my nan says she will chip in 500" into "one more quote before
            # you say yes".
            if turn.get("user"):
                said.append(str(turn["user"]))
    for text in reversed(said):
        pool = _the_pool(_words(text))
        # Only a trade, and only when it is named in the line itself. A pronoun after an office or
        # a clinician is the person they were talking about, not the office: "my sons teacher wants
        # to see me" then "he says hes fine" read `teacher` as the party and answered a boy's
        # reassurance with "Ask for it in writing, and ask what the next step in their own process
        # is" (good-shelf on #9097). A trade talks about a thing - "the boiler keeps losing
        # pressure" then "he said its the pump" - and that reading is the one a store earns.
        if pool is TRADE_REPLIES:
            return pool
    return None


def _recent_bot_lines(memory):
    """The bot's last few replies, one lower-case string each."""
    said = []
    if isinstance(memory, dict):
        for turn in (memory.get("turns") or [])[-4:]:
            if isinstance(turn, dict) and turn.get("bot"):
                said.append(" ".join(str(turn["bot"]).lower().split()))
        if memory.get("bot"):
            said.append(" ".join(str(memory["bot"]).lower().split()))
    return [line for line in said if line]


def _choose(pool, memory):
    """The pool's line, avoiding the ones already said in this conversation."""
    recent = _recent_bot_lines(memory)
    for line in pool:
        head = " ".join(line.lower().split())[:40]
        if not any(head in said for said in recent):
            return line
    return pool[0]


# The verdict is about somebody in their care, not about the person the bot is talking to: "the
# teacher said she needs assessing", "the consultant said my dad needs an x-ray". The subject
# after the saying verb is a person - he, she, or the person's own relation - and the one who has
# to act is the one reading: a parent, a son, a carer. "the office said they need a form" is not
# this: that "they" is the office, and the office keeps its own pool.
ABOUT_SOMEONE_ELSE = re.compile(
    r"\b(?:said|says|say|told\s+me)\s+(?:that\s+)?"
    r"(?:he|she)(?:'?s|'?ll|'?d)?\b|\b(?:said|says|say|told\s+me)\s+(?:that\s+)?my\s+[a-z]+\b")

# The carer's next ask. The line that answers a verdict about somebody else is not the one that
# answers a verdict about the reader: there is nothing here to weigh up and no wait of their own
# to sit out, and the thing they can do is ask what it is for and who runs it. Every line is a
# question to put to the office or the clinic, so none of them states a rule, a penalty or a date.
CARER_REPLIES = (
    "Ask what it is for, who does it, and what changes in the meantime - and ask them to put the "
    "answer in an email so you have it.",
    "Ask which one they mean and who runs it, then when you would hear - a name and a date stop "
    "it being a guess.",
    "Ask what happens if you decide to wait before agreeing to it. That is a fair question and "
    "they should be able to answer it in plain words.",
)

# A date already in the line: the thing to clear is the day, and the questions are the ones to
# ask before it arrives.
CARER_ON_THE_DAY_REPLIES = (
    "Put the date in your phone, and ask now what they need from you beforehand, and who to ring "
    "if it moves.",
    "Ask what to bring and whether anything changes between now and then, and keep the number of "
    "the department that rang you.",
)


# A good thing said about somebody is not a thing to follow up. "the teacher said my daughter is
# doing well" is the good news turn's, and asking what the assessment is for would be a strange
# answer to it. The good news pool is "the school said she can have extra help" as well, and a
# relation who is fine is the same kind of turn.
# The verdict clears the thing rather than asking anything of the person: "the plumber came out
# and said its fine", "the electrician said the wiring is sound". The trade and the office both say
# it this way, and the decision after such a verdict is a decision about a job that has been
# cleared - "get it in writing, and one more quote before you say yes" was the answer to a plumber
# who had just said there was nothing to do (bronze-whale on #9097).
# The verdict clears the thing rather than asking anything of the person: "the plumber came out
# and said its fine", "the electrician said the wiring is sound". The trade and the office both say
# it this way, and the decision after such a verdict is a decision about a job that has been
# cleared - "get it in writing, with the parts and the labour apart, and one more quote before you
# say yes" was the answer to a plumber who had just said there was nothing to do (bronze-whale on
# #9097). One word list holds the clearing words, and every pool reads it.
_CLEAR_WORDS = (
    r"doing\s+(?:well|great|fine|brilliantly)|all\s+clear|"
    r"(?:is|are|was|were|looks|look|seems|seem|sounds|sound)\s+(?:all\s+)?"
    r"(?:fine|ok|okay|alright|sound|clear|good|healthy|safe|solid)|"
    r"its\s+(?:fine|ok|okay|alright|sound)|"
    r"nothing\s+(?:wrong|to\s+worry\s+about|serious|to\s+do|to\s+pay)|"
    r"no\s+(?:problems?|issues?|faults?|damage)|"
    r"is\s+(?:well|better)|got\s+the\s+all\s+clear"
)
CLEARED = re.compile(r"\b(?:" + _CLEAR_WORDS + r")\b")
# A thing said about somebody that is not an obstacle to act on: it is cleared (`CLEARED`), or it
# is an offer to them ("can have", "is allowed"), which the office says about a person and a trade
# says about a part. The offer words must not stand the trade down, because "the garage said the
# car can have a new gearbox" is a price to weigh.
A_GOOD_SAID = re.compile(r"\b(?:" + _CLEAR_WORDS + r"|happy|pleased|proud|through\s+it|"
                         r"can\s+(?:have|stay|go|come\s+home)|is\s+allowed|well\s+done)\b")


def answer_for(text, memory):
    """The reply for a verdict reported back to the bot, or None."""
    clean = " ".join(str(text or "").lower().split())
    if not clean or not SAID.search(clean):
        return None
    if (EMERGENCY.search(clean) or ASKED.search(clean) or SELF_SAID.search(clean)
            or YOU_SAID.search(clean)):
        return None
    if (DONE.search(clean) or ALL_CLEAR.search(clean)) and not A_TIME.search(clean):
        return None
    if PRAISE.search(clean) and not (A_TIME.search(clean) or A_PLAN.search(clean)):
        return None
    if MY_MAN.search(clean) or GOOD_NEWS.search(clean):
        return None
    # A verdict that clears the thing leaves nothing to decide: it is the good news turn's, for
    # every pool, not only the office's. The one exception is a clearing with a date or a next
    # step in it ("the scan is clear, come back in a year"), because there is still a wait to sit
    # out and that is what the pools below are for.
    if CLEARED.search(clean) and not (A_TIME.search(clean) or A_PLAN.search(clean)):
        return None
    words = _words(clean)
    pool = _the_pool(_the_subject(clean))
    if not pool:
        if not PRONOUN.search(clean):
            return None
        pool = _last_party(memory)
        if not pool:
            return None
    # A clinician's verdict about another body is the safety module's turn. The trade and the
    # office talk about other people in the ordinary way ("the teacher said she needs assessing")
    # and keep their turn.
    # A verdict about somebody else's body or life is not a professional's verdict to act on:
    # "her teacher said shes behind" got "Ask for it in writing, and ask what the next step in
    # their own process is" for a child, which is not a thing a parent does with that sentence
    # (good-shelf on #9097). The trade keeps its turn either way: a garage talks about a car.
    if pool in (CARE_REPLIES, OFFICE_REPLIES) and (set(words) & OTHERS):
        # A verdict about somebody in their care is the carer's to follow up, and the pools above
        # are written for the person the verdict is about ("ring back before then" is not a thing
        # a parent does with a teacher's sentence). Left unanswered it fell to the greeting pool
        # and the person got a placeholder: "the teacher said she needs assessing" was answered
        # "Got it. Is there anything you'd like a hand with?" (indigo-dolphin on #9097).
        if (ABOUT_SOMEONE_ELSE.search(clean) and pool is OFFICE_REPLIES
                and not A_GOOD_SAID.search(clean)):
            if A_TIME.search(clean):
                return _choose(CARER_ON_THE_DAY_REPLIES, memory)
            return _choose(CARER_REPLIES, memory)
        return None
    # A clinician who says it is fine is not a date to sit out: "the midwife said its fine either
    # side" was told "ring back before then if it gets worse", and there was no then. The care
    # pool is about the wait, so the wait has to be in the line - a date, a come-back, a scan, a
    # follow-up - or the line is left to whatever answers a verdict that reassures.
    if pool is CARE_REPLIES:
        if A_TIME.search(clean):
            return _choose(CARE_REPLIES, memory)
        if A_PLAN.search(clean):
            return _choose(CARE_PLAN_REPLIES, memory)
        if A_TREATMENT.search(clean) or A_CHANGE.search(clean):
            return _choose(CARE_TREATMENT_REPLIES, memory)
        return None
    if pool is not CARE_REPLIES and A_SPAN.search(clean) and not A_WINDOW.search(clean):
        return _choose(SPAN_REPLIES, memory)
    if pool is not CARE_REPLIES and A_TIME.search(clean):
        return _choose(WAITING_REPLIES, memory)
    return _choose(pool, memory)
