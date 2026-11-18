"""Where the person is, and what they are up to right now.

A chat is not only questions. People open with a line about the moment they are in - "im on the
bus", "waiting for the bus", "im having a lazy day" - and there is nothing in it to answer, so
every module that answers a request declined it and the turn ended at the fallback: the shrug
("Got it. Is there anything you'd like a hand with?"), the filing cabinet ("Noted: quiet day
today."), or the wrong card altogether ("its been a slow day" got advice about a slow boiler).

The reply a friend gives is short. It says the line back in a word ("queues are the worst"),
adds one thing that fits that kind of wait or ride or slow day, and leaves the door open for
whatever is behind the line, because there usually is something. Four things keep it from being
the stock line this file exists to replace:

* only the whole line counts, so "im on the bus and my stop is coming up, how do i get to the
  station" is a question with a place in it and stays with the module that answers it.
* a line that names where they are and nothing else is the same reading, and on main it was
  answered with the shrug or the filing cabinet: "im at work", "im at the gym", "im at the
  library", "im at nans", "im at the hospital". The reply is about being there with something to
  ask, never about the place, so it fits every place equally. A job in progress ("im painting the
  hall") is not here: the cards and the pools already answer that better than a line about being
  somewhere would.
* the pool is chosen by the shape of the line - a wait, a journey, a bed, a slow day - never by
  the words of the place in it, so the reply cannot be pasted onto a different kind of line.
* not every line in a pool ends in a question. A question on the end of every reply turns a chat
  into an interview, and the person said something rather than asked.
* the one place where the reply is about what the person should do next is the car: a person
  typing on the move is driving, and no chat is worth a glance off the road.

The lines are grouped here rather than spread through the chat module because they are the same
reading - the person's own moment - and each group needs its own small pool to stay varied.
"""
import re

from ..compose import pick

# The softeners people put in front of a line about their afternoon, and nothing else: a line with
# a request after it ("just waiting for the bus, what time does the 42 run") is not this line.
_LEAD = (
    r"^\s*(?:(?:oh|aw+|ah|ha+|hi|hey|tbh|honestly|ok|okay|well|and|but|so|yeah|anyway|"
    r"still|currently|right now|not much|nm|just|im|i'm|iam|i am)[,\s]+)*"
)
# How a moment is nailed to the day, on the end of the line: it carries nothing of its own.
_TAIL = (
    r"(?:\s+(?:today|tonight|now|at the moment|right now|lately|this morning|this afternoon|"
    r"this evening|lol|ha+|haha|tbh|honestly))*"
)
_END = r"\s*(?:[.!]+|lol|ha+|haha|tbh|honestly)*\s*$"

# A wait: in a queue, in a waiting room, on hold, at a place that keeps people waiting. The place
# is free to be anything, because the reply is about the waiting rather than about the place.
_WAITING = re.compile(
    _LEAD + r"(?:"
    r"wait(?:ing)? (?:at|for|in|on) \w+(?: \w+){0,3}"
    r"|wait(?:ing)? in (?:a|the) (?:queue|line|waiting room)"
    r"|in (?:a|the) (?:queue|line|waiting room)(?: (?:at|for) \w+(?: \w+){0,3})?"
    r"|queu(?:e|ing) (?:at|for) \w+(?: \w+){0,2}"
    r"|on hold(?: with \w+(?: \w+)?)?"
    r")" + _TAIL + _END, re.I)

# A journey on public transport, or the walk home from it. The vehicle is what the reply is about,
# so the lines that name a vehicle are read here and the car has its own reading below.
_MOVING = re.compile(
    _LEAD + r"(?:"
    r"on (?:the|a|my) (?:bus|train|tube|tram|coach|ferry|plane|flight|boat)"
    r"|on (?:the|a) (?:bus|train|tube|tram) (?:home|in|back|to \w+(?: \w+)?)"
    r"|on my way (?:home|in|back|there|to \w+(?: \w+)?)"
    r")" + _TAIL + _END, re.I)

# Driving is a case of its own. A friend does not start a conversation with somebody at the wheel,
# and the reply that fits is the one that waits.
_IN_THE_CAR = re.compile(
    _LEAD + r"(?:in (?:the|my) car|driving(?: (?:home|back|up|down|to \w+(?: \w+)?))?"
    r"|on the motorway(?: to \w+(?: \w+)?)?|stuck in traffic)"
    + _TAIL + _END, re.I)

# A slow day: nothing much on, taken gently, said rather than complained about.
_SLOW = re.compile(
    _LEAD + r"(?:"
    r"hav(?:e|ing) (?:a|an) (?:lazy|quiet|slow|cosy|couch|pyjama|relaxing|easy|chill) "
    r"(?:one|day|morning|afternoon|evening|night|sunday|weekend)"
    r"|(?:it'?s|its)(?: been)?(?: a)?(?: (?:really|very|proper|nice|lovely))? "
    r"(?:lazy|quiet|slow|cosy|relaxing|easy) (?:one|day|morning|afternoon|evening|sunday)"
    r"|(?:lazy|quiet|slow|chilled) day(?: (?:today|here|at work|so far))?"
    r"|nothing much (?:on|planned|doing)(?: (?:today|here|planned))?"
    r"|not much (?:on|planned)(?: (?:today|here))?"
    r"|nothing on (?:today|this afternoon|this morning)"
    r"|(?:took|taking|having) (?:the|a|my) day off(?: work)?(?: today)?"
    r")" + _TAIL + _END, re.I)

# A body at rest, in bed rather than up: the reply must fit a lie-in and a day spent under a
# blanket feeling rough, so it says nothing about why the person is there.
_IN_BED = re.compile(
    _LEAD + r"(?:"
    r"(?:still |back |lying |sat |sitting |laying )?in bed"
    r"|(?:lying|laying|sat|sitting) in bed"
    r"|back to bed"
    r")" + _TAIL + _END, re.I)

# The sofa and the cup of tea, which is the same afternoon without the duvet.
_SOFA = re.compile(
    _LEAD + r"(?:"
    r"(?:lying|sat|sitting|slouched|curled up) on the (?:sofa|settee|couch)"
    r"|curled up (?:with a book|in front of the tv)"
    r"|having (?:a|another) (?:cup of tea|brew|cuppa|coffee)"
    r"|chill(?:ing|in)(?: out)?(?: (?:now|at home))?"
    r"|taking it easy"
    r")" + _TAIL + _END, re.I)

# A break at work: the sandwich half of the day, and the one line here that always has something
# coming after it.
_ON_A_BREAK = re.compile(
    _LEAD + r"(?:"
    r"on (?:my|a|the) (?:lunch|dinner|tea|coffee) ?(?:break|hour)"
    r"|on (?:my|a) break"
    r"|taking (?:a|my) (?:lunch )?break"
    r")" + _TAIL + _END, re.I)

# At work, and the day is going on around the question. The office, the desk and the shift are the
# same reading, so they share a pool rather than one line each.
_AT_WORK = re.compile(
    _LEAD + r"(?:"
    r"(?:at|back at) (?:work|the office)|in (?:the )?office|at (?:my|the) desk"
    r"|on (?:shift|shifts|nights|days|the clock)|working"
    r")" + _TAIL + _END, re.I)

# Working from home is not in the list above even though it is a place of work: the greeting
# already reads that one properly ("the day has no edges unless you put them in. A walk at the end
# of it stands in for the commute"), and a line about the clock would be the thinner answer.

# The gym, where the question usually comes between sets.
_AT_THE_GYM = re.compile(
    _LEAD + r"(?:"
    r"(?:at|in) the gym|working out|lifting|lifting weights|on the treadmill"
    r"|doing (?:a|my) (?:workout|session|class)"
    r")" + _TAIL + _END, re.I)

# A hospital, a surgery or a dentist: the wait is only half of it, so the pool asks how it is
# going rather than saying what a queue it is (`_WAITING` takes the waiting room on its own).
_AT_A_DOCTOR = re.compile(
    _LEAD + r"(?:"
    r"(?:at|in|outside) (?:the |a )?(?:hospital|a&e|ae|casualty|clinic|surgery|doctors|"
    r"doctor's|gp|dentist|orthodontist|pharmacy|chemist|walk in centre)"
    r"|at the doctors waiting"
    r")" + _TAIL + _END, re.I)

# A place named on its own: "im at the library", "im at nans", "im at sainsburys". Any place at
# all fits, because the reply is about being somewhere with a question to ask, not about the
# place. The list below is what stops a state that merely starts with "at" - "im at my limit",
# "im at breaking point", "im at a funeral" - from being read as a place.
_AT_A_PLACE = re.compile(
    _LEAD + r"(?:"
    r"(?:at|over at|down at|round at|up at|outside|near) (?:the |a |my |our |me )?[a-z][\w'&]*(?: [a-z][\w'&]*){0,2}"
    r"|at home"
    r")" + _TAIL + _END, re.I)
_NOT_A_PLACE = re.compile(
    r"\b(?:limit|limits|loss|a loss|breaking point|end of my tether|wits end|wit's end|fault|"
    r"risk|peace|war|odds|best|worst|least|most|first|last|standstill|stretch|push|glance|"
    r"crossroads|disadvantage|loggerheads|pains|ease|large|hand|that age|my age|this|that|it|"
    r"stage|point|end|end of my rope|loose end|again|once|twice|"
    r"funeral|wake|christening)\b", re.I)

WAITING_REPLIES = (
    "Queues are the worst of it. This is as good a way to spend one as any.",
    "Nothing to do but wait, then. What are you waiting on?",
    "That kind of wait always runs longer than they tell you. Hope it moves.",
    "Hope it goes quickly. I'm here if you want company while it does.",
)
MOVING_REPLIES = (
    "A journey is a good place for a chat. What's on your mind?",
    "Nothing like a ride for thinking things through. Ask away.",
    "Journeys are mostly waiting with a view. Where are you off to?",
    "Mind how you go - I'll be here when you get there.",
)
IN_THE_CAR_REPLIES = (
    "Eyes on the road - I'll be here when you stop.",
    "No reading and driving. Park up and I'll answer anything you like.",
    "I'll keep. Get where you're going first, then ask me whatever it is.",
)
SLOW_REPLIES = (
    "Then take it slow. That is what those days are for.",
    "A lazy day with nothing in it is a good day. Enjoy it.",
    "A slow one can be a good one. What would make it better?",
    "Quiet days are underrated. I'm here if you want something to fill it.",
)
IN_BED_REPLIES = (
    "No rush to get up. What is the rest of the day looking like?",
    "Enjoy the duvet. Anything on your mind?",
    "A warm bed and nowhere to be. Fair enough.",
    "Five more minutes is always the right answer. I'm here when you're up.",
)
SOFA_REPLIES = (
    "That sounds like the right place to be. I'm here when you want something.",
    "Nothing wrong with taking it easy. Ask away if something comes up.",
    "Comfortable, then. Anything you want a hand with while you're there?",
    "A slow afternoon done properly. What are you thinking about?",
)
BREAK_REPLIES = (
    "Break earned. What are you doing with it?",
    "Enjoy it \u2014 half an hour goes faster than you think.",
    "A proper break, then. Anything you want a second opinion on?",
)
AT_WORK_REPLIES = (
    "Work can wait for this. What is it?",
    "Right, you're on the clock. What do you need?",
    "Go on \u2014 I'll keep it short.",
)
AT_THE_GYM_REPLIES = (
    "Good stuff. Cardio or the weights?",
    "Nice. What are you working on today?",
    "Go on then \u2014 what do you need between sets?",
    "Better than sitting down. What's the question?",
)
AT_A_DOCTOR_REPLIES = (
    "Waiting rooms are the worst of it. What do you need while you're there?",
    "That's a long morning whatever it's for. How long have you been there?",
    "Hope it goes quickly. What's on your mind?",
    "Hospital or not, I'm here. What do you need?",
)
AT_A_PLACE_REPLIES = (
    "What are you up to there?",
    "Noted \u2014 what do you need while you're there?",
    "Right you are. Anything you want a second opinion on?",
    "I'll let you get on. What's on your mind?",
)


# A moment line is small talk, and small talk is not the answer when the chat is carrying
# something heavy. `he hits me` then `im in the car` got "I'll keep. Get where you're going first,
# then ask me whatever it is." - which tells somebody who has just said that to carry on and come
# back later. A feeling the turn before named is the same conversation too: after `i cant stop
# crying`, `im on the bus` is not about the journey, and the reply that carries the feeling on
# ("so that is the part behind it") is the one to give.
_HEAVY = re.compile(
    r"\b(?:died|dying|death|funeral|passed away|kill myself|killing myself|suicide|suicidal|"
    r"end it all|take my own life|hurt myself|hurting myself|self harm|self-harm|cut myself|"
    r"overdose|miscarriage|stillborn|terminal|beat me|beats me|hit me|hits me|hurts me|"
    r"hurting me|threatened me|abused? me|assaulted|not safe|scared of|afraid of|"
    r"can'?t stop crying|can not stop crying|crying|in tears|so upset|upset about|devastated|"
    r"heartbroken|at the end of my tether)\b", re.I)


# A moment is now. A line with a stretch of time in it - "im at home all day", "im at work every
# day" - is the shape of their week, which is a fact about them and not small talk: after "should i
# get a cat or a dog", "im at home all day" is the answer to it, and "What are you up to there?"
# threw that away. The store files it instead, and the cat and dog conversation carries on.
A_STRETCH_OF_TIME = re.compile(
    r"\b(?:all|every|each|most|whole) (?:day|days|week|weeks|night|nights|morning|evening|"
    r"time|summer|winter|year)|these days|most days|all the time|\d+ (?:days|weeks|hours) a week\b",
    re.I)

# The same for a day still to come: "im at the dentist on Tuesday" is an appointment, and the
# detail in it (the day) is the thing worth keeping, so the module that holds plans answers it.
A_DAY_TO_COME = re.compile(
    r"\b(?:tomorrow|next (?:week|month|year|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday)|on (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
    re.I)


def _the_chat_is_heavy(memory):
    """True when the turns just before this one were about something heavy.

    The store holds the turns before this one (the line being answered is added after the reply
    is chosen), so the last two of them decide: a moment line three turns after a disclosure is a
    change of subject and can be answered.
    """
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    earlier = [turn for turn in turns if isinstance(turn, dict)
               and str(turn.get("user", "")).strip()]
    for turn in earlier[-2:]:
        if _HEAVY.search(" ".join(str(turn["user"]).split())):
            return True
    return False


def reply(text, memory):
    """A short, warm reply to a line about the moment they are in, or None."""
    clean = " ".join(str(text or "").replace("\u2019", "'").split())
    if not clean or len(clean.split()) > 9:
        return None
    if _the_chat_is_heavy(memory):
        # Left to the module that carries the feeling on, which has the last answer in front of it.
        return None
    if A_STRETCH_OF_TIME.search(clean) or A_DAY_TO_COME.search(clean):
        # A habit or an appointment, not the moment they are in: the store keeps the fact.
        return None
    seed = str(text or "")
    if _ON_A_BREAK.match(clean):
        return pick(BREAK_REPLIES, memory, seed_text=seed)
    if _WAITING.match(clean):
        return pick(WAITING_REPLIES, memory, seed_text=seed)
    if _IN_THE_CAR.match(clean):
        return pick(IN_THE_CAR_REPLIES, memory, seed_text=seed)
    if _MOVING.match(clean):
        return pick(MOVING_REPLIES, memory, seed_text=seed)
    if _IN_BED.match(clean):
        return pick(IN_BED_REPLIES, memory, seed_text=seed)
    if _SOFA.match(clean):
        return pick(SOFA_REPLIES, memory, seed_text=seed)
    if _SLOW.match(clean):
        return pick(SLOW_REPLIES, memory, seed_text=seed)
    # The same reading with a place or a job in it. Read after the pools above, so a line that has
    # a better reading there ("im in the waiting room" is a wait) keeps it.
    if _AT_WORK.match(clean):
        return pick(AT_WORK_REPLIES, memory, seed_text=seed)
    if _AT_THE_GYM.match(clean):
        return pick(AT_THE_GYM_REPLIES, memory, seed_text=seed)
    if _AT_A_DOCTOR.match(clean):
        return pick(AT_A_DOCTOR_REPLIES, memory, seed_text=seed)
    if _AT_A_PLACE.match(clean) and not _NOT_A_PLACE.search(clean):
        return pick(AT_A_PLACE_REPLIES, memory, seed_text=seed)
    return None
