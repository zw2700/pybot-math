"""Chasing an organisation that has not done the thing (PRIORITY -997).

A person says the body they are dealing with has gone quiet, and the bot has nothing:

    the dwp havent replied to me                  -> "I'm listening - say more if it helps."
    hmrc havent sent my rebate                    -> "I'm listening - say more if it helps."
    the gp surgery wont give me an appointment    -> "Sorry to hear that. What would help most?"
    how long should i wait before i chase the council
                                                  -> "Citizens Advice covers this free, and a
                                                      call beats searching."
    my housing association is ignoring me         -> the search hedge

None of those is an answer. The first three are the worst of them: a person has said what is
wrong and been asked to say more, which reads as a bot that did not understand. The last two
point at a charity and at a search engine, and a person who wanted to know how long to wait is
no further on.

What the bot can say about all of them is the shape of chasing anything, which is the same
whatever the body is called: what decides how fast it moves is the reference and the date, the
ask has to be in writing with what you want and by when, and the timescale and the next stage
are published by the body itself. That is true of a council, a tax office, a surgery and a
supplier, so it can be said from here. What cannot be said is the person's own reference and
what their page says, and that is the honest limit, said in a few words.

This is a module rather than a pool inside bot/compose/fallback.py because that file is over the
world's 1 MiB limit on main, so no pull request can change it. PRIORITY -997 puts it just above
the seed fallback (-1000) and below every module that can answer, so #answers' complaints cards
("how do i complain to the council", "how do i complain about my energy supplier", "how do i
escalate a complaint") keep every line they can answer, and this only speaks where nothing else
did.

The words alone are never enough:

- An organisation named is not a problem with it: "i work for the council", "my sister works at
  the jobcentre", "we voted labour", "the council tax is going up" are somebody's day or a piece
  of news, and a page on how to chase is not an answer to any of them.
- What makes it a chase is that something has not happened ("havent heard", "no reply", "still
  waiting", "wont fix it", "ignoring me") or that the person asks how to move it along ("how do
  i chase", "how long should i wait", "who do i escalate to"). Both are read off the line, and a
  line with neither is left to the modules that own it.
- A question about what a thing *is* or what the rules are ("when is the council tax due", "can
  the council evict me") is not a chase either, and #answers and the knowledge base own those.
"""

import re

PRIORITY = -997

# Something has not happened. Read off the person's own words, because the tense is how a
# statement of delay is told from a statement of fact ("they havent replied" against "they
# replied last week").
# The words that turn a body's name into one of the person's own: "my doctor brother", "my bank
# manager mum". A chase is about an organisation that has gone quiet, and a relations word right
# after the body's name means the line is about a person who happens to work there.
A_PERSON_AFTER_THE_NAME = frozenset("""
    brother sister mum mom mam dad father mother son daughter wife husband partner friend mate
    cousin uncle aunt nephew niece boss colleague workmate neighbour neighbor stepson stepdaughter
    flatmate roommate lodger lad girl bloke fella boyfriend girlfriend fiance fiancee
""".split())

NOT_DONE = re.compile(
    r"\b(?:havent|hasnt|hadnt|ha(?:ve|s|d)\s+not|didnt|did\s+not|not\s+(?:yet\s+)?(?:replied|"
    r"heard|fixed|paid|sent|done|come|turned\s+up)|no\s+(?:reply|response|answer|word)\b|"
    r"still\s+(?:waiting|no|nothing)|nothing\s+(?:back|yet|since|at\s+all)|ignoring|ignored|"
    r"wont|won't|refuse[sd]?|too\s+long|weeks\s+now|months\s+now|"
    # The same silence said as an amount rather than as a missing reply. "i sent the form a month
    # ago and nothing" and "i complained three weeks ago and heard nothing" were met with "Good -
    # that's that off your mind now" and "Nice one. One less thing to see to", which read the verb
    # as a job finished. The tense of the line is the opposite: the thing was done and nothing came
    # back, so the amount and the nothing are both read here.
    r"and\s+nothing\b|heard\s+nothing|nothing\s+(?:ever\s+)?came\s+back|"
    # A promise instead of a silence: "they said they'd ring me back and never did", "they
    # promised a date and never gave one". The body is not refusing, it is not keeping to what it
    # said - which is the one chase where the date of the promise is the thing to quote.
    r"never\s+(?:did|bothered|rang|replied|came|got\s+back|gave|sent|turned\s+up)|"
    r"never\s+(?:heard|came)\s+back|"
    # Nobody, said as a person: "no one has got back to me about the repair", "nobody bothered to
    # reply". These were "Got it. Is there anything you'd like a hand with?", which is the bot
    # hearing the words and no request in them.
    r"no\s+one\s+(?:(?:has|had)\s+)?(?:got|gotten|come)\s+back|nobody\s+(?:(?:has|had)\s+)?"
    r"(?:got|gotten|come)\s+back|has\s+not\s+come\s+back|have\s+not\s+come\s+back|"
    # The person who was going to ring, in the third person: "nobody rang me back about the
    # appointment". Said as who did not do it rather than as what did not arrive.
    r"(?:nobody|no\s+one)\s+(?:\w+\s+){0,2}(?:rang|rung|phoned|called|replied|answered|bothered))")

# Asking how to move it along, or how long to leave it. The two questions that come after a
# silence, and both are answered by the same shape. A bare "how do i" is deliberately not here:
# "how do i find out my council tax band" is the knowledge base's question, and it was answered
# with a complaints page while this pattern was in the gate.
HOW_TO_CHASE = re.compile(
    r"\b(?:chase|chasing|escalate|escalation|ombudsman|complain|complaint|"
    r"follow\s+(?:it\s+)?up|how\s+long\s+(?:should|do|before|until|to\s+wait|till)|"
    r"who\s+(?:do\s+i|should\s+i|can\s+i)\s+(?:ask|ring|call|contact|chase|escalate)|"
    r"what\s+(?:can|do|should)\s+i\s+do\s+(?:about|now)|take\s+(?:it|this)\s+further)\b")

# The organisation, how the reply calls it, and the one reference that service goes by. Named
# here because the reference is the part that is genuinely different between them, and the rest
# of the reply is the same shape for all of them.
ORGANISATIONS = (
    (("council tax",), "the council tax",
     "the account number on the bill"),
    (("council", "local authority", "town hall"), "the council",
     "the reference on their letter"),
    (("housing association", "housing office", "housing trust"), "the housing association",
     "their repair or complaint reference"),
    (("landlord", "letting agent", "landlady"), "the landlord",
     "the date you reported it and your photos"),
    (("dwp", "jobcentre", "job centre", "universal credit", "benefits office"), "the DWP",
     "the reference on the decision letter"),
    (("hmrc", "tax office", "inland revenue"), "HMRC",
     "your taxpayer reference and the tax year"),
    (("gp", "doctor", "surgery", "health centre", "dentist"), "the surgery",
     "the practice manager's name and the date you first asked"),
    (("hospital", "nhs trust", "clinic"), "the hospital",
     "your appointment or referral reference"),
    (("energy supplier", "electricity", "gas company", "water company", "water board"),
     "the supplier", "your account number and the date of the bill"),
    (("bank", "building society"), "the bank",
     "the complaint reference they gave you"),
    (("employer", "payroll", "hr"), "your employer",
     "your payslip dates and the hours you were short"),
    (("school", "head teacher", "headteacher", "academy trust"), "the school",
     "the date you raised it and their letter"),
    (("university", "college", "student finance"), "the university",
     "your student number and the decision reference"),
    (("dvla", "passport office", "home office", "ukvi"), "the office",
     "the application reference on your receipt"),
    # A parcel that has not come is the same silence as a form that has not been answered, and
    # the reference is the order number. It was reaching the travel pool instead - "how do i
    # chase up a delayed parcel" was answered "I can't check live times or delays, sorry. The
    # operator's own app or site has the next departure and any disruption, and a journey planner
    # puts the whole trip together", because the pool's trigger is the bare word "delayed" and a
    # parcel is not a service that runs. The body is the seller rather than the courier: the
    # contract is with the shop, and the shop is who refunds or replaces.
    (("parcel", "delivery", "courier", "postage", "the post", "my order", "the order"),
     "the seller", "the order number and the delivery date they gave you"),
)

# What moves it, said in the same words whatever the body is: the reference, the date, the
# writing, and their own published timescale. Three ways of saying it so a second line in the
# same chat is not the same sentence again.
# The reply in three ways of saying it, so a second chase in the same chat is not the same
# sentence again. Each one carries the three things that are true whatever the body is called -
# the reference, the date, the writing - and then the honest limit, because the timescale for
# this person's case is on their own page and their own letter, which is the part the bot cannot
# see. No pointer on its own: "Citizens Advice covers this free, and a call beats searching" was
# the reply this replaces, and a person told what to write does not need a search engine.
THE_SHAPE = (
    "Have {reference} in front of you, and put the ask in writing once: what has not happened, "
    "when you first raised it, and the day you want an answer by. {body}'s complaints page names "
    "the timescale and the next stage, usually an ombudsman after eight weeks, and that page is "
    "the part I cannot see.",
    "First get {reference} together, then write once, with what has not happened, "
    "the date you first raised it and the day you need to hear by. {body}'s own complaints page "
    "has the timescale and the escalation route, and what it says for your case is the part I "
    "cannot see.",
    "Start with {reference}, then write once: what has not happened, when you first raised it, and "
    "the day you need to hear by. {body}'s complaints page says how long they take and where it "
    "goes next, and that and your letter are what I cannot see from here.",
)


# A silence with no organisation named: "i sent the form a month ago and nothing", "i complained
# three weeks ago and heard nothing", "no one has got back to me about the repair". Most people
# chasing something never say the body's name, so the shape cannot wait for one - but the line has
# to show something already raised, or every "and nothing" in the language ("i pressed the button
# and nothing") would be answered with a complaint letter. Both halves are required.
RAISED = re.compile(
    r"\b(?:complain(?:ed|ing|t)?|letters?|form|emails?|emailed|wrote|written|write|applied|"
    r"application|claim(?:ed|s)?|asked|rang|phoned|called|contacted|chased|reported|"
    r"requested|sent|posted|appealed|emailed\s+them|in\s+touch|heard\s+from\s+them|"
    # The thing that was raised, said instead of the asking: "no one has got back to me about the
    # repair", "the refund still has not come". These are things nobody asks for idly, so the noun
    # with a silence is enough to know something is outstanding, where "no one has got back to me"
    # on its own is not.
    r"repairs?|refunds?|payments?|booking|appointment|orders?|delivery|deposits?|quote|"
    r"invoices?|reimburs\w*)")

# The same letter, for a body with no name in the line: the possessive "{body}'s complaints page"
# has nothing to hang on, so the two things that are still true are said on their own - the
# reference they gave you, the date, the writing, and the timescale you cannot see from here.
THE_SHAPE_UNNAMED = (
    "Write once with the reference they gave you, what has not happened, the date you first raised "
    "it and the day you need to hear by, and keep a copy. Past that day a complaint goes to an "
    "ombudsman, usually after eight weeks, and their own complaints page has the timescale - the "
    "part I cannot see from here.",
    "The letter only needs the reference, what has not happened, the date you first asked and the "
    "day you want an answer by. That copy is what makes the next step easy: their complaints page "
    "names the timescale and who takes it on after it, and I cannot see that page from here.",
    "Put it in writing once, with the reference, the dates and the day you need to hear by. "
    "Complaints usually go on to an ombudsman after eight weeks if nothing comes back, and the "
    "page that says how long they allow for this case is the one I cannot see.",
)


def _the_shape_unnamed(memory, lowered):
    from ..compose import fallback  # noqa: PLC0415 - the composer's own chooser
    return fallback._choose(THE_SHAPE_UNNAMED, memory, lowered)


# The follow-up: "ive rung them three times" after "the council havent sent the form" was answered
# "Got it - you've rung them three times", which is the bot repeating the line back. The person is
# not telling the bot how many times they rang for the count; they are saying that trying harder
# on the phone has stopped working, and what they need is the step that leaves a record.
IVE_TRIED = re.compile(
    r"\b(?:i(?:ve|\s+have)\s+(?:rung|rang|called|phoned|emailed|written|been\s+in|been\s+down|"
    r"asked|chased|tried)|(?:rung|rang|called|phoned|emailed)\s+(?:them|him|her|the\s+\w+)|"
    r"no\s+one\s+(?:answers|picks\s+up|rings\s+back)|keeps?\s+passing\s+me\s+(?:round|around))")

IVE_TRIED_LEAD = (
    "A call leaves nothing they have to answer, so the step that works now is one line in writing.",
    "Phoning again will get the same answer; what counts is the ask in writing.",
    "That is the point to stop ringing and put it in writing, because a call is not a record.",
)


# "what now", "what else can i do", "where do i start": a bare continuation, with nothing in it
# for any module to work with, after a chase. That is the worst place for a search hedge - the
# person is already mid-way through something and asking for the next step, and "tell me what you
# find and I'll help you weigh it up" leaves them holding a task instead of a step. The next step
# is the letter itself: what goes in it, where it goes, and what happens when the date passes.
BARE_CONTINUATION = re.compile(
    r"^(?:so|ok|okay|and|but|right|well)?\s*(?:what\s+now|what\s+next|now\s+what|"
    r"what\s+do\s+i\s+do(?:\s+now)?|where\s+do\s+i\s+start|how\s+do\s+i\s+start)\s*[?.!]*$")
# "what else can i do" is deliberately not here: memory_store claims it and answers it with the
# important half of the bot's own last reply, which is a different (and better) answer than the
# letter, and taking the turn from it would be a routing change rather than a fallback one.

# The answer to "how long should i wait", asked as a follow-up after a chase. It is not the shape
# again: the person already has the shape and is asking the one thing in it that is a date, so the
# reply is the timescale and what happens when it passes. Eight weeks is the marker most complaints
# schemes in the UK use and it is the same number the shape already quotes, so nothing here is a
# figure of its own.
# The ask that gets the timescale, and the asks that do not. A chase's follow-up is not one
# question: "how long should i wait before i chase again" wants the date, and "who do i ring about
# it" wants a name. Both match HOW_TO_CHASE, and the timescale branch was reading either of them,
# so the follow-up to a bullying answer ("who do i ring about it") came back as "Eight weeks is the
# usual marker: until then the school works to its own published timescale... and after it a
# complaint can go to the ombudsman" - a date where a name was asked for, and a complaint route
# where the person had only just been told to ask for a meeting. Only the date-shaped ask gets the
# date; everything else HOW_TO_CHASE matches is left to the modules that answer it.
THE_TIMESCALE_ASK = re.compile(
    r"\bhow\s+long\b|\bhow\s+many\s+(?:weeks|days|months|working\s+days)\b|"
    r"\bhow\s+soon\b|\bwhen\s+should\s+i\s+(?:chase|escalate|complain|write)\b|"
    r"\bwait\s+(?:before|until)\b|\bhow\s+much\s+longer\b")

THE_TIMESCALE = (
    "Eight weeks is the usual marker: until then {body} works to its own published timescale, and "
    "after it a complaint can go to the ombudsman. Put the day you need an answer by in the "
    "letter, keep the copy, and the date you wrote down is what makes it their deadline.",
    "Most schemes give {body} eight weeks to answer before a complaint can be escalated to an "
    "ombudsman, and its own page has the shorter figure it works to day to day. Your letter is "
    "what starts the clock, so give a date and keep a copy of it.",
)


THE_NEXT_STEP = (
    "Then it is two short paragraphs: what has not happened, the date you first raised it and the "
    "day you want an answer by, sent to the address on their letter with {reference} in it so "
    "there is a copy. If the date passes or the reply is a no, {body}'s complaints page names the "
    "next stage, which is usually an ombudsman after eight weeks.",
    "Put {reference} at the top, say in two or three lines what has not happened and when you "
    "first asked, and ask for an answer by a named day. Keep the copy: {body}'s own page has the "
    "timescale, and the letter it sends back names who takes it on if they miss it.",
    "Write it once, with {reference}, the date you first raised it and the day you need to hear "
    "by, and keep a copy. {body} publishes how long it should take and where a complaint goes "
    "next after that, and the date you put in the letter is what makes it their deadline.",
)


# The same next step for a chase with no body named in it: "i sent the form a month ago and
# nothing" then "what now". The reply above cannot be used, because "{body}'s complaints page" has
# no name to hang on, and a "what now" in that chat was met with "I'm not sure about that one,
# sorry - I'd rather not guess. A quick search online will get you a solid answer", which is the
# search hedge this lane exists to replace.
THE_NEXT_STEP_UNNAMED = (
    "Then write it once: the reference they gave you, what has not happened, the date you first "
    "raised it and the day you need to hear by, and keep a copy of it. Past that day a complaint "
    "usually goes on to an ombudsman after eight weeks, and their own page has the timescale for "
    "your case - the part I cannot see.",
    "One short letter: the reference, what has not happened, the date you first asked and the day "
    "you want an answer by, with a copy kept. Their complaints page says how long they allow and "
    "who takes it on after that, and your copy is what proves the date you gave them.",
)


# A PERSON WHO HAS GONE QUIET IS THE SAME WAIT, AND NOT THE SAME LETTER.
#
# The gate above keeps a body's name that belongs to a person out of the organisation branch, and
# that is right: nobody sends their best mate a letter with a reference number and a deadline. But
# the wait is still the wait, and it was going nowhere at all. @cool-fan's probe on main
# (`6f5447f3b`) is the cost of that hole:
#
#   my best mate doesnt text me back
#     -> "That is a lonely place to be, and being surrounded by people does not fix it. Who is one
#         person who does see you?"
#
# The premise - being surrounded by people - is not in the line, and the useful half of a wait is
# missing. `unseen.py` reached for its loneliness pool because nothing else answered. The honest
# answer to a friend who has not replied is #13040's wait answer, so it is written here, in the
# module that already knows what a silence is, rather than widening a pool built for being
# overlooked by everyone around you.
#
# The shape is what keeps it narrow: a person of theirs is the *subject* and the person writing is
# the *object* - "my mate doesnt text me back", "my brother hasnt rung me". That is the one shape
# where the other person owes a reply and has not sent one. "my son hasnt heard back from the
# school" is the son waiting, not the son ignoring, and it stays with the organisations above.
A_PERSON_THEIRS = (
    r"(?:best\s+|old\s+|oldest\s+|closest\s+|own\s+|little\s+|big\s+|eldest\s+|younger\s+|"
    r"school\s+|uni\s+|work\s+|childhood\s+)*"
    r"(?:friends?|mates?|brothers?|sisters?|mum|mom|mam|mother|dad|father|sons?|daughters?|"
    r"husbands?|wifes?|wives|partners?|boyfriends?|girlfriends?|cousins?|uncle|aunt|nephews?|"
    r"nieces?|flatmates?|housemates?|roommates?|colleagues?|workmates?|neighbours?|neighbors?|"
    r"ex|ex-?(?:wife|husband|partner|boyfriend|girlfriend))")
# One reply verb, with or without the person as its object: "hasnt texted me back", "never
# replied", "wont answer me". The s-forms are here because "my sister never texts me back" is the
# same line in the present tense, and the bare "replied"/"answered" is here because a person says
# "my cousin hasnt replied" without adding who to.
A_REPLY_VERB = (
    r"(?:text(?:s|ed|ing)?|messag(?:e|es|ed|ing)|call(?:s|ed|ing)?|ring(?:s|ing)?|rang|rung|"
    r"repl(?:y|ies|ied|ying)|answer(?:s|ed|ing)?|respond(?:s|ed|ing)?|pick(?:s|ed|ing)?\s+up|"
    r"ignor(?:e|es|ed|ing)|open(?:s|ed|ing)?|writ(?:e|es|ten|ing)?|wrote|"
    r"(?:be|been)\s+in\s+touch|"
    r"(?:come|came|get|gets|getting|got)\s+back)")
# The negative it is said with. "isnt" was missing and it is how most people say it: "my brother
# isnt answering my calls", "she isnt replying to my texts", "hes not picking up". The same silence
# as "hasnt replied", and it fell through to a greeting and then to a search hedge.
A_NEGATIVE = (
    r"(?:hasnt|havent|hadnt|has\s+not|have\s+not|didnt|did\s+not|doesnt|does\s+not|isnt|"
    r"isn't|is\s+not|wasnt|wasn't|was\s+not|never|wont|won't|refuses?\s+to)")
A_PERSON_OWES_A_REPLY = re.compile(
    r"\b(?:my|our)\s+(?:\w+\s+){0,1}" + A_PERSON_THEIRS +
    r"\b[^.?!]{0,40}?\b" + A_NEGATIVE + r"\s+(?:\w+\s+){0,2}" + A_REPLY_VERB +
    r"\b(?:\s+(?:me|us|back)){0,2}", re.I)
# The same line with a pronoun where the person was named a turn ago: "my mate and i fell out"
# then "he hasnt texted me back". Read only against a person named in the chat, so a bare "they"
# in a conversation about an organisation keeps that organisation's letter.
# "he", "she", "they" and the run-together forms people type: "hes not picking up" said of the
# friend named a turn ago is the same wait as "he hasnt texted me back".
THE_PRONOUN = (r"(?:(?:he|she|they)(?:s|'s|re|'re|ve|'ve)?)")

A_PRONOUN_OWES_A_REPLY = re.compile(
    r"^\W*(?:(?:so|and|but|then|ok|okay|well)\s+)*" + THE_PRONOUN + r"\b[^.?!]{0,30}?\b"
    + r"(?:" + A_NEGATIVE + r"|\bnot)\s+(?:\w+\s+){0,2}" + A_REPLY_VERB +
    r"\b(?:\s+(?:me|us|back)){0,2}", re.I)
# The pronoun form of the same, for the chat that named the person a turn ago.
A_PRONOUN_DID_THE_SILENT_THING = re.compile(
    r"^\W*(?:(?:so|and|but|then|ok|okay|well)\s+)*" + THE_PRONOUN + r"\b[^.?!]{0,30}?\b"
    r"(?:ignor(?:ed|es)|ghost(?:ed|s)|blank(?:ed|s)\s+me|left\s+me\s+on\s+read|"
    r"gave\s+me\s+the\s+silent\s+treatment)\b", re.I)

# Somebody not answering the door is not a reply that has not come: it is whether they are all
# right in there, which is a different worry ("my mum isnt answering the door" was sent the letter
# about a friend who has gone quiet).
ANSWERING_SOMETHING_ELSE = re.compile(
    r"\b(?:the\s+)?(?:door|doorbell|buzzer|intercom|gate)\b", re.I)

# The same silence said without a negative word: the verb is the negative. "my friend ignored my
# text", "my mate ghosted me", "she left me on read". Read off the person of theirs like the rest,
# so "i ignored an email at work" is not a person who owes the writer a reply.
A_PERSON_DID_THE_SILENT_THING = re.compile(
    r"\b(?:my|our)\s+(?:\w+\s+){0,1}" + A_PERSON_THEIRS +
    r"\b[^.?!]{0,30}?\b(?:ignor(?:ed|es)|ghost(?:ed|s)|blank(?:ed|s)\s+me|"
    r"left\s+me\s+on\s+read|gave\s+me\s+the\s+silent\s+treatment)\b", re.I)

THE_WAIT_FOR_A_PERSON = (
    "No word back, and the waiting is the worst of it. One plain message - \"no rush, just "
    "checking you're ok\" - beats three follow-ups, and it is easy to answer, which matters more "
    "than saying it perfectly.",
    "A silence like that does the talking on its own, so it is worth one clear message rather than "
    "guessing: say you would like to hear from them and that there is no pressure, then leave the "
    "ball with them. A first nudge reads as care and a third reads as a chase.",
    "Waiting on somebody to answer is its own kind of tired. Send one message that is easy to "
    "answer - no list of complaints, no \"we need to talk\" - and then let a day or two pass "
    "before you read anything into it: people go quiet for reasons that have nothing to do with "
    "you.",
)


def _the_person_before(memory):
    """Whether one of the person's own people was named in the last couple of turns."""
    said = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    for line in said[-3:]:
        if re.search(r"\b(?:my|our)\s+" + A_PERSON_THEIRS + r"\b", line, re.I):
            return True
    return False


def _the_wait_for_a_person(memory, lowered):
    """The wait answer for a friend who has not replied. None if nothing says they owe one."""
    if A_PERSON_OWES_A_REPLY.search(lowered):
        said = A_PERSON_OWES_A_REPLY.search(lowered)
    elif A_PERSON_DID_THE_SILENT_THING.search(lowered):
        said = A_PERSON_DID_THE_SILENT_THING.search(lowered)
    elif A_PRONOUN_DID_THE_SILENT_THING.search(lowered) and _the_person_before(memory):
        said = A_PRONOUN_DID_THE_SILENT_THING.search(lowered)
    elif A_PRONOUN_OWES_A_REPLY.search(lowered) and _the_person_before(memory):
        said = A_PRONOUN_OWES_A_REPLY.search(lowered)
    else:
        return None
    # a knock at the door is not a reply that has not come
    if ANSWERING_SOMETHING_ELSE.search(lowered):
        return None
    from ..compose import fallback  # noqa: PLC0415 - the composer's own chooser
    return fallback._choose(THE_WAIT_FOR_A_PERSON, memory, lowered)


def _was_an_unnamed_chase(memory, current):
    """Whether the line before this one was a silence with no organisation named in it."""
    said = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    said = [line for line in said if line.strip() and line.strip().lower() != current]
    if not said:
        return False
    lowered = " ".join(said[-1].lower().split())
    return _the_body(lowered, _words(lowered)) is None and not _names_its_own_person(lowered) \
        and bool(RAISED.search(lowered) and NOT_DONE.search(lowered))


def _words(text):
    return set(re.findall(r"[a-z']+", str(text or "").lower()))


def _the_body(lowered, words):
    """The organisation the line names, and the reference it goes by."""
    if A_PERSON_WHO_WORKS_THERE.search(lowered):
        # one of their own people works there, so the silence is that person's
        return None
    for triggers, said, reference in ORGANISATIONS:
        for trigger in triggers:
            if " " in trigger:
                if trigger in lowered:
                    return said, reference
            elif trigger in words:
                # The word is not the body on its own: "my doctor brother hasnt called me back"
                # is a brother who is a doctor, and the complaints route of a surgery is the wrong
                # answer to a personal snub (tidy-lark, on #12725). Read the word straight after
                # the trigger and stand down when it is one of the person's own people. Every
                # organisation left ("my doctor hasnt called me back", "the surgery hasnt given
                # me an appointment") still reads, because a trigger followed by a verb or by
                # nothing has no person in that place.
                owner = _the_person_it_belongs_to(lowered, trigger)
                if owner:
                    continue
                return said, reference
    return None


# A person who works at a body is not the body. "my sister works at the hospital and she hasnt
# replied" is a sister who has gone quiet - the chase card asked for an appointment reference she
# would never have - and the same goes for a brother at the council, a daughter at the DWP and an
# aunt at the bank (tidy-lark, on #12725: the guard above reads the two words after the body's
# name, and "council and he" is not a person). The job is what puts the person in the body's place,
# so the line is read as one of the person's own people rather than as an organisation.
A_PERSON_WHO_WORKS_THERE = re.compile(
    r"\b(?:my|our)\s+(?:\w+\s+){0,1}" + A_PERSON_THEIRS +
    r"\b[^.?!]{0,25}?\b(?:works?|working|worked|is\s+employed|has\s+a\s+job|got\s+a\s+job|"
    r"does\s+a\s+job)\s+(?:for|at|in|with)\b", re.I)

# The person's own people, wherever they are in the line. The body's name is asked about first
# (`_the_body`), so a line that names both - "my brother hasnt had the council form" - keeps the
# council's shape; this only decides the lines with no organisation in them at all.
A_PERSON_NOT_A_BODY = re.compile(
    r"\b(?:brother|sister|mum|mom|mam|dad|father|mother|son|daughter|wife|husband|partner|"
    r"friend|mate|cousin|uncle|aunt|nephew|niece|boss|colleague|neighbour|neighbor|stepson|"
    r"stepdaughter|flatmate|roommate|landlady|lad)\b")


def _names_its_own_person(lowered):
    """Whether the line is about one of the person's own people rather than an organisation."""
    return bool(A_PERSON_NOT_A_BODY.search(lowered))


def _the_person_it_belongs_to(lowered, trigger):
    """The person's own relation said straight after the body's name ("doctor brother"), or None.

    Only the two words after the trigger are read, so "the bank hasnt rung my sister back" is still
    the bank: the relation has to sit where the body's name is, which is the noun a person puts
    after it to say whose it is ("bank manager mum", "hospital doctor mate of mine").
    """
    found = re.search(r"\b%s\s+(?:(\w+)\s+)?(\w+)" % re.escape(trigger), lowered)
    if not found:
        return None
    for after in found.groups():
        if after and after in A_PERSON_AFTER_THE_NAME:
            return after
    # "my doctor's brother", "the bank of my sister": the possessive or the "of" puts a person
    # where the body was named, and the same stand-down applies.
    return None


def _the_body_before(memory, current):
    """The body a follow-up is about, from the person's own lines before this one.

    The current line is skipped by its text rather than by position: whether the memory already
    holds this turn when a module is asked depends on where in the turn the module runs, and
    dropping the last entry either way loses the body when it has not been stored yet.
    """
    said = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    said = [line for line in said if line.strip() and line.strip().lower() != current]
    for line in said[::-1]:
        lowered = " ".join(line.lower().split())
        body = _the_body(lowered, _words(lowered))
        if body is not None:
            return body
    return None


def respond(text, memory):
    """What moves a chase along, for a body that has gone quiet. None for every other line."""
    lowered = " ".join(str(text or "").lower().split())
    if not lowered:
        return None
    if not isinstance(memory, dict):
        memory = {}
    body = _the_body(lowered, _words(lowered))
    if body is not None:
        # A silence or a how-to-move-it question, and nothing else is enough: an organisation named
        # in passing ("i work for the council", "the council tax is going up") is not a chase, and
        # "how do i find out my council tax band" is the knowledge base's question rather than one
        # about a body that has gone quiet.
        if not (NOT_DONE.search(lowered) or HOW_TO_CHASE.search(lowered)):
            return None
        return _the_shape(body, memory, lowered)
    # The chase asked again without the body's name: "how long should i wait before i chase again"
    # straight after "how do i chase up a delayed parcel". The body is on the turn before, and the
    # answer is the timescale and the escalation, which is what THE_SHAPE carries - the same shape,
    # in a different variant, because the composer's chooser skips what it has already said in this
    # chat. Before this, the second line was answered with the sales paragraph ("sales come round
    # on set dates and prices do drop"), which is the reply to a question about waiting for a
    # discount.
    # A bare "what now" is the letter rather than the timescale, so it is read by the branch
    # below even though HOW_TO_CHASE's "what do i do now" matches it too.
    if THE_TIMESCALE_ASK.search(lowered) and not BARE_CONTINUATION.match(lowered):
        before = _the_body_before(memory, lowered)
        if before is not None:
            return _the_timescale(before, memory, lowered)
    # A bare continuation after a chase: the next step is the letter, not a search.
    if BARE_CONTINUATION.match(lowered):
        before = _the_body_before(memory, lowered)
        if before is not None:
            return _the_next_step(before, memory, lowered)
        if _was_an_unnamed_chase(memory, lowered):
            return _the_next_step_unnamed(memory, lowered)
        return None
    # Nothing named on this line: "ive rung them three times" is the same chase one turn on.
    if IVE_TRIED.search(lowered):
        before = _the_body_before(memory, lowered)
        if before is not None:
            from ..compose import fallback  # noqa: PLC0415 - the composer's own chooser
            lead = fallback._choose(IVE_TRIED_LEAD, memory, lowered)
            return "%s %s" % (lead, _the_shape(before, memory, lowered))
    # A person of theirs who has not replied: the wait answer, not the letter. Read here, above the
    # unnamed-silence branch below, because that branch is the one that leaves a personal silence
    # to the modules that own it - and nothing owned it, which is how "my best mate doesnt text me
    # back" reached a loneliness line about being surrounded by people.
    person_wait = _the_wait_for_a_person(memory, lowered)
    if person_wait is not None:
        return person_wait
    # A silence with no organisation named, after something the person already raised. Answered
    # last, so a body named on this line or in the turn before keeps the shape written for it, and
    # a bare continuation keeps the next step. A silence about one of the person's own people has
    # already been answered above with the wait, so what is left here is a silence with no name in
    # it at all.
    if RAISED.search(lowered) and NOT_DONE.search(lowered) and not _names_its_own_person(lowered):
        return _the_shape_unnamed(memory, lowered)
    return None


def _the_timescale(body, memory, lowered):
    """How long to leave it, for a chase asked again without the body's name."""
    the_body, _reference = body
    from ..compose import fallback  # noqa: PLC0415 - the composer's own chooser
    said = fallback._choose(THE_TIMESCALE, memory, lowered).replace("{body}", the_body)
    said = said[0].upper() + said[1:]
    return re.sub(r"(?<=[.!?] )([a-z])", lambda hit: hit.group(1).upper(), said)


def _the_next_step(body, memory, lowered):
    """What to do now, for a bare continuation after a chase."""
    the_body, reference = body
    from ..compose import fallback  # noqa: PLC0415 - the composer's own chooser
    said = fallback._choose(THE_NEXT_STEP, memory, lowered)
    said = said.replace("{reference}", reference).replace("{body}", the_body)
    said = said[0].upper() + said[1:]
    return re.sub(r"(?<=[.!?] )([a-z])", lambda hit: hit.group(1).upper(), said)


def _the_next_step_unnamed(memory, lowered):
    """What to do now, for a bare continuation after a chase with no body named."""
    from ..compose import fallback  # noqa: PLC0415 - the composer's own chooser
    said = fallback._choose(THE_NEXT_STEP_UNNAMED, memory, lowered)
    said = said[0].upper() + said[1:]
    return re.sub(r"(?<=[.!?] )([a-z])", lambda hit: hit.group(1).upper(), said)


def _the_shape(body, memory, lowered):
    """The sentence for a body: the reference to have, the ask, the timescale, the limit."""
    the_body, reference = body
    from ..compose import fallback  # noqa: PLC0415 - the composer's own chooser
    shape = fallback._choose(THE_SHAPE, memory, lowered)
    said = shape.replace("{reference}", reference).replace("{body}", the_body)
    # "the council's complaints page" starts a sentence once the name is dropped in, so the first
    # letter of each sentence is raised after the substitution rather than in the pool text.
    said = said[0].upper() + said[1:]
    said = re.sub(r"(?<=[.!?] )([a-z])", lambda hit: hit.group(1).upper(), said)
    return said
