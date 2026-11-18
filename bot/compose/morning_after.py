"""A night of drinking, reported the day after.

People say this in one breath and mean one of two things - "i got really drunk last night" can be
a good story or a regret - and the bot answered both badly:

    i was blind drunk last night      -> "Good to hear. What was the best bit?"
    i got pissed last night           -> "Good to hear. What was the best bit?"
    i had one too many at the pub     -> "Nice one. How did the rest of it go?"
    i went on a bender last night     -> "Sounds alright. Anything good in it?"
    i got wasted at the party         -> "Noted: you got wasted at the party."
    i was bladdered at the do         -> "Bladdered is a thing you already know how to do..."
    i woke up still drunk             -> "Thanks for telling me — I'm here if you want to dig in..."

The cheers are the day pools reading a past-tense account of an evening as an evening that went
well, which is the one reply a person who is not proud of it cannot use; the receipt and the
skills line read a single word ("wasted", "bladdered") for its own subject. What a friend says to
either telling is the same thing: how are you today, and here is the one thing that helps. So
this is one reading for the whole family, and it never tells them the night was good or bad -
the person already knows which it was.

The reading turns on which word it is. "drunk", "plastered", "bladdered", "off my face", "on the
lash", "one too many" are only ever about drink, so they carry the reading on their own. "wasted",
"smashed", "steaming", "tipsy", "boozy" and the bare "drinking" are ordinary words in other
lines - "i wasted my money on that", "i smashed my phone", "i drink too much coffee in the
morning" - so they need a night that has gone ("last night", "this morning", "woke up") beside
them. "hangover" and "hanging" are the weakest of all and need the morning said out loud, because
"hanging the curtains" is a job, and "rough" is left out altogether: "im rough today" is as likely
to be a bug as a night out.

It stands down for somebody else's drinking ("my husband was drunk again last night" is the
relationship card's, "we got drunk at the wedding" is a wedding), for a question about drinking
("should i stop drinking" has an answer in the knowledge base), for whatever the night did
afterwards ("i was drunk and i said something stupid" wants the apology, "i got drunk and drove
home" is the driving, "i was plastered and fell over" is the fall), and for the night that ended
in an ambulance, which the safety readers own.

It is asked early in the chain, because the six shapes above were answered by six different pools
deep inside it - the day pools, the echo, the skills line, the task line and the sober-years pool
that read "plastered" as "off the drink" - and a reading that sits next to the day pools never
sees the other five. A knowledge card still wins the turn, since the composer is last: "i have
such a hangover" keeps the water, sleep and food card.
"""
import re

# The words that are only ever about drink: they carry the reading with no time beside them.
A_STRONG_STATE = re.compile(
    r"\b(?:drunk|drunken|pissed(?!\s+off)|plastered|bladdered|trolleyed|mullered|mangled|"
    r"sozzled|paralytic|off\s+(?:my|his|her|their|our)\s+(?:face|head|tits)|"
    r"on\s+the\s+lash|bender|"
    r"(?:a\s+)?few\s+too\s+many|one\s+too\s+many|too\s+much\s+(?:to\s+drink|wine|beer|lager|booze)|"
    r"too\s+much\s+last\s+night|heavy\s+night|big\s+night)\b", re.I)
# Ordinary words that are about drink only when the line says when: "i wasted my money", "i
# smashed my phone", "i drink too much coffee in the morning".
A_WEAK_STATE = re.compile(
    r"\b(?:wasted|smashed|steaming|tipsy|boozy|lash|binge|bendered|drank|"
    r"hammered|leathered|wrecked|half\s+cut|"
    r"been\s+drinking|was\s+drinking|were\s+drinking)\b", re.I)
# The night is over: a past time in the line, or the morning it left behind.
A_TIME_THAT_HAS_GONE = re.compile(
    r"\b(?:last\s+night|last\s+evening|yesterday|the\s+night\s+before|all\s+night|overnight|"
    r"this\s+morning|woke\s+up|till\s+\d|til\s+\d|until\s+\d|"
    r"(?:fri|satur|sun)day\s+night|at\s+the\s+weekend|night\s+out|"
    # An occasion that has been and gone. "i got wasted at the party" needed this: the state word
    # is an ordinary one, and the party in the past is what makes it a night of drinking.
    r"at\s+the\s+(?:party|pub|club|do|wedding|works\s+do|leaving\s+do)|at\s+a\s+party|"
    r"on\s+a\s+night\s+out)\b", re.I)
# A hangover said in its own word. "hanging" is only a hangover when the line says when - "im
# hanging the curtains" is a job - so it needs the morning beside it, and "rough" is left out
# altogether: "im rough today" is as likely to be a bad day or a bug as a night out.
A_HANGOVER = re.compile(r"\b(?:hung\s?over|hangover|hanging|woke\s+up\s+rough|"
                        r"rough\s+as\s+a\s+badger)\b", re.I)
A_MORNING = re.compile(r"\b(?:this\s+morning|today|now|after\s+last\s+night)\b", re.I)
# What the night did afterwards is a subject of its own: "i was drunk and i said something
# stupid" wants the apology, "i got drunk and drove home" is the driving, "i was plastered and
# fell over" is the fall. Those readings own the turn, so this one stands down when the line
# names one of them.
A_CONSEQUENCE = re.compile(
    r"\b(?:said|saying|told|texted|messaged|rang|rung|called|drove|drive|drove\s+home|hit|"
    r"shouted|argued|arguing|kissed|cheated|spent|ruined|broke|broke\s+up|fell|fall|"
    r"lost\s+my|got\s+in\s+a\s+fight|fight)\b", re.I)
# A night still to come is a plan, not a morning after: "i had a heavy night tonight" is a typo,
# and "im going on a bender on friday" is a plan the chat pools can ask about.
A_STILL_TO_COME = re.compile(
    r"\b(?:tonight|tomorrow|next\s+(?:week|weekend|month|year)|going\s+to|gonna|"
    r"this\s+weekend|on\s+friday|on\s+saturday)\b", re.I)
# Somebody else's drinking, or the pair of them as a "we": "my husband was drunk again last
# night" is the relationship card's, "my mum got drunk at the christening" is a christening, and
# "we got drunk at the wedding" is a story about a wedding. What is left for this reading is the
# person's own state, so one of these in front of the state word stands the reading down.
SOMEONE_ELSE = re.compile(
    r"\b(?:hes|shes|theyre)\b|"
    r"\b(?:my|our|his|her|their|he|she|they|we|us)\s+(?:\w+\s+){0,2}?"
    r"(?:was|were|got|gets|get|is|are|had|has|keeps?|been)\b", re.I)
# A night that ended in an ambulance is not a hangover, and the safety readers answer it.
AN_EMERGENCY = re.compile(
    r"\b(?:ambulance|999|911|111|hospital|a\s?&?\s?e\b|passed\s+out|passing\s+out|"
    r"blacked\s+out|blackout|can'?t\s+wake|not\s+breathing|stopped\s+breathing|"
    r"alcohol\s+poisoning|overdose|overdosed|choking|seizure|collapsed|unconscious)\b", re.I)
# Asking what to do about drinking is a question with an answer, and the knowledge base has it.
A_QUESTION_ABOUT_IT = re.compile(
    r"\b(?:should|shall|could|how\s+do|how\s+can|how\s+to|what\s+should|any\s+tips|advice|"
    r"stop\s+drinking|give\s+up|cut\s+down|cutting\s+down|quitting|quitting|help)\b", re.I)

# The one thing that helps, said once and without a lecture, plus a question: either how they are
# today or what the rest of it looks like. Every line reads right whether the night was good or
# bad, because none of them congratulates them and none of them scolds.
A_MORNING_AFTER = (
    "Ha - how is your head today?",
    "Water, something plain to eat and an early night is most of the cure. How is today going?",
    "That is a long night. Are you feeling it today, or did you get away with it?",
    "How are you this morning? A pint of water, food and time, in that order.",
    "How bad is it - banging head, or just tired and skint?",
    "That sounds like one of those nights. Are you able to take it easy today?",
    "Right. How are you feeling now?",
)


def reads_as_a_morning_after(clean):
    """True when the line reports a night of drinking that has already happened.

    `clean` is the understood line: lowercased, with the punctuation tidied.
    """
    if not clean:
        return False
    if AN_EMERGENCY.search(clean) or A_QUESTION_ABOUT_IT.search(clean):
        return False
    if A_CONSEQUENCE.search(clean):
        return False
    gone = A_TIME_THAT_HAS_GONE.search(clean)
    strong = A_STRONG_STATE.search(clean)
    weak = A_WEAK_STATE.search(clean) if gone else None
    hangover = A_HANGOVER.search(clean) if A_MORNING.search(clean) else None
    said = strong or weak or hangover
    if not said:
        return False
    # The state has to be the person's own, so the words in front of it must not name anybody
    # else or count them in.
    if SOMEONE_ELSE.search(clean[:said.start()]):
        return False
    if not gone and A_STILL_TO_COME.search(clean):
        return False
    return True
