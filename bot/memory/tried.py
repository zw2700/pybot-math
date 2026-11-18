"""A follow-up that says the last answer did not work.

"i tried that and it didn't work", "still blocked", "no luck" is about the answer the bot has
just given, the way "how long will it take" is. Nothing read it as one, in both directions: the
line fell to "Noted! What would be most useful to talk about?" at one end, and at the other the
answer modules handed over the same instructions again, word for word - the one thing a friend
never does with a problem that has not moved.

So this module reads the line as what it is and says the next thing: when the home fix has done
all it can, who does it for a living. It only fires on the turn after an answer, and only for a
short line, so an ordinary sentence that happens to contain "no luck" ("no luck finding a
plumber") is not read as a report on the answer.

The trade is looked up from the words of the answer that did not work, not from the new line:
"still blocked" after the sink entry has no word of its own to say what is blocked.
"""
import re

from . import you
# The store's own list of people, so "with my partner" is a person here without a second list of
# what counts as one.
from .facts import PEOPLE_AGED, RELATIONS as A_PERSON

# The modules whose last turn counts as an answer to this problem. A shrug is not one, so a
# "still blocked" after the fallback asks the person what they mean instead of escalating.
ANSWER_MODULES = ("answers",)

# A line reporting that the answer did not work. "still there" is only a report when it is about
# the thing ("they're still there"), and "no luck" only when the line is about the attempt, so
# the short-line guard below does the rest of that work.
NOT_WORKED = re.compile(
    r"\b(?:did(?:n'?t| not) (?:work|help|do (?:anything|much|the trick|it)|shift (?:it|them)|"
    r"budge|move|make (?:any |a )?difference|change anything|touch (?:it|them))|"
    r"has(?:n'?t| not) worked|is(?:n'?t| not) working|made (?:no|not much) difference|"
    r"no luck|nothing (?:happened|worked)|no (?:change|better|improvement)|"
    r"what if (?:that|it|this) (?:doesn'?t|didn'?t|isn'?t) work(?:ed|ing)?|"
    r"(?:it'?s|it is|they'?re|they are|its|there'?s) still there|"
    r"still (?:not (?:working|worked|fixed|shifted|moved|helped)|blocked|broken|stuck|"
    r"the same|doing it|coming back|leaking|clogged|dripping))\b"
)
# A short line that says the thing has not moved, in whatever words the person gave it: "still
# cold", "still freezing", "it still clicks". The words after "still" are the thing the chat is
# already on, not a new subject: "my shower is cold" then "still cold" was answered as the illness
# and "my laptop keeps freezing" then "still freezing" as what keeps in a freezer, because every
# reader matched the one word the line carries and no reader saw the subject.
STILL_ONLY = re.compile(
    r"^(?:it|its|it's|it is|they|theyre|they're|they are|that|thats|that's|that is|this|"
    r"this is|there|theres|there's|he|hes|he's|he is|she|shes|she's|she is)?\s*"
    r"still\s+(?P<tail>[a-z][a-z' -]*)$"
)
# Words that point at the thing rather than naming it, so the report is whole with no word of
# the thing in it: "still there" about a headache is the headache still there.
POINTS_AT_IT = frozenset(("there", "the same", "like that", "like this", "doing it", "at it",
                          "the same thing", "no better", "not working"))
# Words too common to say the line is about the thing the chat is on.
TOO_COMMON = frozenset("""the and but for not still it its this that them they there here
out off now just very really again same doing like been being was were are had has have
one two three""".split())

# The same report said as an attempt: "i tried that", "we already tried it", "tried everything".
TRIED = re.compile(
    r"\b(?:i|we|ive|i've|weve|we've|they)\s+(?:already\s+|just\s+)?(?:tried|did|used|gave)\s+"
    r"(?:that|this|it|them|those)\b|\btried (?:that|this|it|everything|all of it)\b|"
    r"\btried everything\b"
)

# The same report said as a result: "i turned it really hard and now it drips faster", "i shoved
# it really hard and now its stuck". The person has already put a hand to the thing and says what
# happened next, which is a report on the answer and then some - it says what the thing does now.
# It only counts when the line points at the thing with a pronoun, so "i had a bath and now im
# worse" stays a line about the person.
MADE_IT_WORSE = re.compile(
    r"\bnow\b[^.?!]{0,24}\b(?:worse|faster|slower|louder|stuck|jammed|seized|stripped|"
    r"snapped|broke|broken|leaking|dripping|spraying|sparking|dead|wont|won'?t|"
    r"stopped (?:working|moving|spinning|draining)|wobbl\w*|cracked|bent)\b"
)
POINTS_AT_THE_THING = re.compile(r"\b(?:it|its|it's|them|they|that|those)\b")

# Failing to find the person who does it for a living is not a report on the answer ("no luck
# finding a plumber"), so those lines keep their own reply.
ELSEWHERE = re.compile(r"\b(?:find|finding|found|book|booking|booked|get hold of|reach|reaching|"
                       r"phone|phoning|ring|ringing)\b")

# "not worked yet", "nothing yet" - the fix has not had its go, so nothing is handed over.
# Only at the end of the line: "it didnt work yet again" is a report.
YET = re.compile(r"\byet\b\W*$")

# A report carries its own verdict, and only one of the three is this module's: the answer did
# not work. "i tried that and it helped a bit" is the person saying it did, and "it made it
# worse" is them saying stop - both have an answer of their own in the composer's outcome pool
# ("Carry on with it", "Stop there"), and this module's next step (who does the job once the
# home fix has run out) is a plumber to someone whose sink is running again. The negations are
# the whole difficulty: "no better", "isnt helping" and "didnt help" are still reports that it
# did not work, so the verdict is only read in the frames that say it plainly.
IMPROVED = re.compile(
    r"\b(?:(?:it|that|this|they|its|thats) (?:has |have |is |are |'s |seems? )?"
    r"(?:actually |really |definitely |properly |much |a bit )?"
    r"(?:helped|helping|works|worked|working|done the trick|did the trick|sorted it)|"
    r"(?:a bit|lots|much|loads|far|slightly|no end) better|feeling better|on the mend|"
    r"clearing up|eased off)\b"
)
WORSE = re.compile(r"\b(?:made (?:it|things|me) (?:worse|sorer)|makes it worse|worse than before|"
                   r"sorer|in agony|unbearable)\b")

WORD = re.compile(r"[a-z0-9']+")

# Who does it for a living, looked up from the words of the answer that did not work. Kept to
# the trades that a home fix hands over to, and deliberately small: the words are ones an entry
# can only be about, so "the pump is noisy" reaches the engineer and "the bread didn't rise"
# does not.
# The order matters where two families share a word: a washing machine has a pump and a drain, a
# dishwasher drains, and a laptop has a battery, so the thing itself is looked up before the
# parts it shares with something else - otherwise "the washing machine isnt draining" reached the
# boiler engineer on "pump" and a laptop battery reached a garage.
#
# Plumbing is two jobs, not one. The blocked-waste half is cleared with a plunger and a trap, so
# that string fits a sink, a toilet or a drain and is wrong for a tap or a pipe: a dripping tap
# wants a washer, and saying the plunger and the trap are already ruled out tells the person
# about two things they never tried. The water side is read first, because its words are what the
# answer names when the line is about water and a sink answer does not mention a tap. A shower is
# left to the symptom: leaking is water, not draining is waste.
TRADES = (
    (("ant", "ants", "mouse", "mice", "rat", "rats", "wasp", "wasps", "wasp nest", "flea",
      "fleas", "moth", "moths", "cockroach", "cockroaches", "bedbug", "bedbugs", "bed bug",
      "bed bugs", "silverfish", "pest", "pests", "pigeon", "pigeons", "squirrel", "squirrels"),
     "a pest control firm, and the council's pest service is usually the cheapest way in", None),
    (("stain", "stains", "carpet", "sofa", "mattress", "curtain", "curtains", "upholstery",
      "dry clean", "dryclean"),
     "a dry cleaner, who will know what the mark is and say whether it will come out", "mark"),
    (("laptop", "laptop", "phone", "iphone", "android", "tablet", "printer", "router",
      "broadband", "wifi", "computer", "pc"),
     "the maker's support line, where they can watch it happen on a call", "fault"),
    (("car", "cars", "engine", "brake", "brakes", "clutch", "mot", "gearbox", "battery",
      "tyre", "tyres", "steering", "exhaust"),
     "a garage, and it is worth saying what you have already changed", "fault"),
    (("washing machine", "dishwasher", "fridge", "freezer", "oven", "tumble", "dryer",
      "vacuum", "hoover", "microwave", "kettle", "toaster", "appliance", "appliances"),
     "the maker's repair line, and five minutes on the phone settles whether it is worth "
     "fixing", "fault"),
    (("boiler", "boilers", "radiator", "radiators", "heating", "pilot", "thermostat", "flue",
      "pump", "gas", "combi", "immersion"),
     "a Gas Safe engineer, since anything on the gas side is theirs by law", "fault"),
    (("tap", "taps", "pipe", "pipes", "leak", "leaking", "joint", "washer", "valve", "drip",
      "dripping"),
     "a plumber, who can say whether it is a five-minute washer or a bigger job", "fault"),
    (("sink", "sinks", "drain", "drains", "plunger", "trap", "toilet", "waste", "sewer",
      "sewage", "overflow", "shower", "showers"),
     "a plumber, with the plunger and the trap already ruled out", "fault"),
    # A door, a window, a hinge: the part that has stopped working is fitted, and whether it
    # is the fitting or the frame is what decides the whole job. It comes after the boiler on
    # purpose: a boiler's answer talks about a lockout, and "lock" is a word for a door too.
    (("door", "doors", "window", "windows", "hinge", "hinges", "lock", "locks", "handle",
      "frame", "latch", "bolt", "draught", "draft"),
     "a joiner or a handyman, who will tell you whether it is the hinge or the frame", "fault"),
    (("dog", "dogs", "cat", "cats", "rabbit", "hamster", "guinea", "parrot", "puppy",
      "kitten"),
     "a vet, since an animal that is not mending is not something to wait on", "health"),
)

# Said when the report names nothing this module can take over: no thing to hand to a trade and
# no machine to ask what it is doing. The answer that did not work is not repeated, so the honest
# next move is the one a friend makes - find out what has already been ruled out.
ASK_WHAT_TRIED = (
    "Which things have you tried? I'll skip those and go at what's left.",
    "Tell me what you've already done and I'll not send you round it again.",
)

# Said when no trade fits: the fix has been tried, so what matters now is what the thing is
# doing instead. Honest - it claims nothing about what the next step is.
# Said when the line is only the thing again with "still" on it: "still cold" after the shower
# answer is the shower, not a common cold, and "still there" after a headache is the headache,
# not the bot being asked whether it is there. Nothing here claims what the next step is, and
# nothing repeats the answer: it asks the one thing that tells them apart.
# Said when the thing the chat is on is a body or a feeling, and the line says it is still there
# ("still there" after a headache, "still the same" after being tired). SAME_STILL asks what
# happens when they try it again, which is the question for a boiler and reads as if the person
# were operating themselves; what somebody with a bad head is asked is whether it has moved.
STILL_GOING_ON = (
    "Still there, then. Any better than it was, or much the same?",
    "Still with you \u2014 has it eased at all since it started?",
    "So it hasn't gone. Is it the same as when it started, or worse?",
)
SAME_STILL = (
    "Right, so that hasn't shifted. What happens now when you try \u2014 nothing at all, or "
    "something different from before?",
    "So it's still going on, then. What have you noticed since \u2014 the same as before, or has "
    "it changed?",
    "Then it hasn't moved. Tell me what it does now and I'll take it from there.",
)
ASK_NEXT = (
    "Then the easy fixes have had their go. Tell me what it's doing now \u2014 still the same, "
    "different, or worse \u2014 and I'll see where that points.",
    "Right, so that's not it. What's it doing now: the same as before, or has it changed?",
    "So the usual thing hasn't touched it. What happens now when you try \u2014 nothing at all, "
    "or something different from before?",
)

# Said when a "still ..." line reports a thing that has not moved and nobody has tried anything
# yet: the state is the thing's own, so the question is about the thing, not about a fix that has
# had its go ("Then the easy fixes have had their go" was said to a person who had tried nothing).
STILL_ASK = (
    "Still {state}, then. What happens when you try it again \u2014 nothing at all, or something "
    "different?",
    "Right, still {state}. How long has it been going on, and is it all the time now?",
    "Still {state}, noted. What happens just before it goes like that?",
)

# Said when the fix has been tried, the trade has been named and the thing still has not moved:
# the point of the conversation is that spending more on it is the wrong next step.
END = (
    "Then I'd stop spending on it and get someone in to look — that's the point where a "
    "home fix stops being the cheap option.",
    "Honestly, at that point I'd have someone look at it properly rather than try a fourth thing.",
    "Then it's past what a weekend and a how-to video can do. Get it looked at properly.",
)

# How the trade is raised, varied so the same list is not read out twice.
LEADS = (
    "Then it's past a home fix: {trade}.",
    "That's where the home fix ends, I'm afraid \u2014 {trade}.",
    "Then it wants someone with the right kit: {trade}.",
    "So it needs {trade}.",
)

# The step said as done, with the doing word named: "ive tried the plunger", "i already
# restarted the router", "cleaned the filter already". That is not the report TRIED reads - that
# one names no step, so the answer has none to move on from. This line names which step has had
# its go, so the answer still has a next one, and handing that same step over again ("Unplug the
# router for 30 seconds") is the one thing a friend never does. Nor is it the trade yet: the
# person has not said the answer failed, only that they are partway through it. Only doing words
# are read, so "i already know", "i already have one" and "i already told her" stay with the
# lines that answer them.
DOING = (
    r"(?:re-?start\w*|re-?boot\w*|re-?set\w*|clean\w*|chang\w*|replac\w*|ble[wd]|topp?\w*|"
    r"unblock\w*|plung\w*|wash\w*|vacuum\w*|hoover\w*|re-?install\w*|uninstall\w*|updat\w*|"
    r"plug\w*|switch\w*|check\w*|tried|us(?:e|ed|ing)\b|cut\w*|stop\w*|start\w*|took|taken|"
    r"drunk|drank|walk\w*|exercis\w*|stretch\w*|ice[ds]?|icing|elevat\w*|book\w*|air\w*|"
    r"vent\w*|rins\w*|soak\w*|scrub\w*|fit\w*|fix\w*|adjust\w*|turn\w*|drain\w*|empt\w*|"
    r"defrost\w*|descal\w*|brush\w*|pok\w*|twist\w*|tighten\w*|loosen\w*|tap\w*|seal\w*|"
    r"open\w*|clos\w*|mov\w*|put\w*|gave|given?|add\w*|reduc\w*|increas\w*|rais\w*|lower\w*)"
)
LEAD_IN = (r"^\W*(?:(?:and|but|so|oh|ok|okay|well|yeah|yep|no|nah|hmm|ah|right|alright|then)"
           r"\W+)*")
STEP_ALREADY = re.compile(
    LEAD_IN + r"(?:i\s*(?:'ve|ve|have)\s+|i\s+|ive\s+)?already\s+(?P<what>" + DOING +
    r"\b(?:[a-z0-9' -]|(?<=\d)\.(?=\d)){0,40})$", re.I)
STEP_TRIED = re.compile(
    LEAD_IN + r"(?:i\s*(?:'ve|ve|have)\s+|i\s+|ive\s+)?(?:already\s+|just\s+)?"
    r"(?:tried|used)\s+(?P<what>\S.*)$", re.I)
STEP_LAST = re.compile(
    LEAD_IN + r"(?:i\s*(?:'ve|ve|have)\s+|i\s+|ive\s+)?(?P<what>" + DOING +
    r"\b(?:[a-z0-9' -]|(?<=\d)\.(?=\d)){0,40})\s+already\W*$", re.I)
# A step said as done in the plain perfect, with no marker word at all: "ive cleaned the filter",
# "i have bled the radiators", "weve restarted the router". People say this more often than "i
# already cleaned the filter", and read as a report it reached the entry for a different
# appliance: "ive cleaned the filter" after "my washing machine smells" was answered with the
# vacuum cleaner's filter, because the answer's own step is "clean the filter" and nothing read
# the line as that step being done. The participle is a doing word or any "-ed" form, which is
# where most of them live; the line still has to name a step of the answer to count.
PARTICIPLE = (r"(?:" + DOING + r"|[a-z]{4,}ed|bled|wrung|swept|dug|spun|taken|done|ran|made|"
              r"left|held|shut|set|put|cut)")
STEP_DONE = re.compile(
    LEAD_IN + r"(?:(?:i|we)\s*(?:'ve|ve|have)|ive|weve)\s+(?P<what>" + PARTICIPLE +
    r"\b(?:[a-z0-9' -]|(?<=\d)\.(?=\d)){0,40})", re.I)
STEP_DID = re.compile(
    LEAD_IN + r"(?:i|we)\s+(?P<what>" + DOING + r"\b(?:[a-z0-9' -]|(?<=\d)\.(?=\d)){0,40})", re.I)
# A step said with nothing named: "tried that", "tried everything". Which step it was is not
# said, so there is none to walk past and the report path answers it.
STEP_VAGUE = frozenset("""that this it them those these everything all anything something
    whatever lot one ones thing things stuff""".split())
# The words that name no step on their own, so a phrase made of only them is a vague try.
STEP_EMPTY = frozenset("""a an the and but or so oh well yeah yep ok okay right alright already
    just really very quite still now again too much more some any of in on off out up down with
    for to at it its it's that this them those my our your his her their""".split())
# How the next step is introduced, varied so the same wording is not read out twice. The attempt
# is said two ways - "ive tried the plunger" names the thing, "i already restarted the router"
# names the doing - so each has its own leads: "You've already restarted the router, then ..."
# reads, and "You've tried restarted the router" does not.
STEP_LEADS = (
    # Two sentences here too: what follows the comma was the step, not the trying, so
    # "You've tried the plunger, then pull the gunk out" is the same splice as the report above.
    "You've tried {thing}. Now {step}.",
    "Right, so {thing} is done. {Step}.",
    "Then {step}.",
)
ALREADY_LEADS = (
    # Two sentences, not ", then": the step is a bare instruction of its own ("pull the gunk
    # out"), and a lead that already carries its own "then" reads the joining twice over -
    # "You've already cleaned the filter, then run a hot service wash" is two joint words in one.
    "You've already {thing}. {Step}.",
    "Since you've already {thing}, {step}.",
    "Then {step}.",
)
# A doing word said in the past takes a lead that says it as done ("You've already cleaned the
# filter"); the same word said as a habit does not, and "You've already walk the dog" is not
# English. A habit is said with the verb as it is ("i walk the dog twice a day already"), so the
# ending tells them apart, with the common irregulars listed.
PAST_WORD = re.compile(r"^[a-z]{2,}(?:ed|en|ght)$")
# A past-tense doing word that is too short for the ending to prove it ("bled", "shed").
SHORT_PAST = frozenset("bled fled shed sped".split())
# The endings that make a doing word a report of something done, by the word itself.
PAST_STEP_ED = re.compile(r"^[a-z]{3,}ed$")
PAST_IRREGULAR = frozenset("""ran did made took gave put set cut kept left found got went saw
    wrote sold sent spent built burnt read shot told brought bought thought caught taught""".split())
DONE_LEADS = (
    # Two sentences, never a comma and a joint word: the {thing} handed in here is the person's
    # own clause with its verb on it ("ran a hot wash"), so "You ran a hot wash, then clean the
    # filter" joins a past-tense report to an imperative and reads as one broken sentence, and
    # "You ran a hot wash, so clean the filter" is worse than broken - it claims the filter needs
    # cleaning *because* of the hot wash, which is a reason nobody said. The lead that names the
    # trying ("You've tried the plunger, then ...") can splice, because what follows its comma is
    # what was tried, not a step to take.
    "You {thing}. Now {step}.",
    "Right, so you {thing}. Then {step}.",
    "Then {step}.",
)
PRESENT_LEADS = (
    # The same two sentences, for the same reason: a habit said back in the second person is a
    # sentence of its own, and the step after it does not follow from it with "so".
    "You already {thing}. Now {step}.",
    # "Since clean the filter is already part of your day" is what this said: the {thing}
    # handed in here is a bare verb phrase said as a habit ("clean the filter", "walk the
    # dog twice a day"), not a noun, so the frame needs a subject the line never carries.
    # The other lead says the same thing in words that fit both ("You already clean the
    # filter, so ..."), so this one goes rather than bending the {thing} into a gerund.
    "Then {step}.",
)
# The phrase opening on a doing word says the doing ("cleaned the filter") rather than naming
# the thing ("the plunger"), which is what decides how the attempt is introduced.
# A doing word is any past tense, whatever its length: the pattern here was four letters and
# an "-ed", so "degreased the drawer" was read as a thing ("Right, so degreased the drawer is
# done") while "cleaned the filter" was read as the doing it is.
DOING_WORD = re.compile(r"(?:" + DOING + r"|[a-z]{2,}ed)\b", re.I)
# A piece of the answer that opens on one of these is the tail of the step before it.
TAIL_WORD = re.compile(r"^(?:and|but|or|not|if|so|then|which|that|because|while|rather)\b", re.I)
# "put it as central as the phone line allows" is the tail of the step before it: a step handed
# over on its own has to say what to act on, and "it" points at a sentence that is not there.
PRONOUN_TAIL = re.compile(
    r"^(?:put|leave|check|try|give|keep|take|clean|run|top|set|turn|move|wipe|replace|change|"
    r"open|close|hold|press|unplug|switch|bleed|fill|repeat|do)\s+"
    r"(?:it|them|that|this|those|these)\b", re.I)
# The verbs a step can open on that the composer's own list does not carry. Without them "undo
# the trap underneath" and "restart the phone" read as a statement rather than a thing to do.
MORE_STEP_VERBS = frozenset("""undo unplug reinstall upgrade reboot restart reset force update
    wipe swap plug thaw rinse scrub polish vacuum hoover descale defrost sand trim scrape blot
    clamp loosen tighten snip shave share write print send take keep hold hang mount have mow
    scarify aerate reseed edge""".split())
STEP_WORDS = 22
# A clause is one thing to do: the answer's move is cut at a comma, a semicolon or a "then",
# and a comma inside brackets ("unscrew it (bowl down, then pull)") is not a cut.
CLAUSE = re.compile(r"\s*;\s*|:\s+|\s+then\s+|\s+-\s+|,\s+and\s+")


def words_of(text):
    return WORD.findall(str(text or "").lower().replace("\u2019", "'"))


def reads_as_not_worked(text):
    """True when the line is a report that the last answer did not do the job."""
    line = " ".join(words_of(text))
    if not line or len(line.split()) > 14:
        return False
    if ELSEWHERE.search(line):
        return False
    # A verdict of its own - it worked, or it made things worse - is not this report.
    if IMPROVED.search(line) or WORSE.search(line):
        return False
    # "it didnt work yet" is a fix still in progress, so the trade has not been earned: the
    # report has to be of a fix that has had its go. Without this the next step is a plumber
    # for someone who is still holding the plunger.
    if YET.search(line):
        return False
    if NOT_WORKED.search(line):
        return True
    if MADE_IT_WORSE.search(line) and POINTS_AT_THE_THING.search(line):
        return True
    return bool(TRIED.search(line))


# A "still" line that names the state the last turn was about: "my shower is cold" then "still
# cold", "i cleaned the filter" then "still smells", "my car wont start" then "it still clicks".
# The word after "still" belongs to the thing, so the line says the answer has not moved it - and
# read as a fresh question the same word was the common cold ("A cold usually peaks in two or
# three days"), the food-safety card for a fridge that is still warm, and the frame "Everything
# about still smells is in what I said above". The state has to be one the chat has already
# named, in the person's own line or in the answer they are reporting on, which is what keeps
# "im still hungry" and "still here" out.
STILL_STATE = re.compile(r"\bstill\s+(?P<state>[a-z' ]{2,30})\W*$")
# Not a state of the thing: words people use about themselves, about time, and about the
# conversation. "still waiting", "still at work" and "are you still there" are somebody else's
# line, and none of them reports on an answer.
NOT_A_STATE = frozenset("""here there waiting hungry tired thirsty awake asleep up alive
hurts hurting hurt sore aching achy painful pain ill sick poorly unwell dizzy faint sickly
upset sad anxious stressed worried down low rough rubbish wobbly shaky weak numb
depressed miserable weepy tearful
going coming learning working trying looking thinking hoping planning deciding wondering
worse better ok okay fine good great bad nice rubbish
at work in bed on my way at it on it at home on hold in touch
a chance time young single busy late early on off out in the same""".split())
# The line has to be about the thing, not a question put to me: "are you still cold" is not a
# report, and a line opening on a modal or an inverted verb is asking.
STILL_ASKS = re.compile(r"^(?:are|is|do|does|did|will|would|can|could|should|shall|have|has|"
                        r"why|how|what|when|where|who|which)\b")


def the_still_state(text, memory):
    """The state a "still ..." line reports on the thing, or "" when it is not that report.

    "my shower is cold" then "still cold": the word after "still" belongs to the thing, so the
    line says the answer has not moved it. The state has to be one the chat has already named - in
    the person's own line or in the words their line was answered by - which is what keeps the
    bot's own prose out of it: an answer about films says "sofa", and "still sofa" is nobody's
    line.
    """
    said = " ".join(words_of(text))
    if not said or len(said.split()) > 7 or said.endswith("?"):
        return ""
    if STILL_ASKS.match(said):
        return ""
    found = STILL_STATE.search(said)
    if not found:
        return ""
    state = [word for word in words_of(found.group("state")) if word not in STEP_EMPTY]
    if not state or any(word in NOT_A_STATE for word in state):
        return ""
    named = {_stem(word) for word in words_of(person_said(memory))}
    named |= {_stem(word) for word in last_answer_words(memory)}
    if not any(_stem(word) in named for word in state):
        return ""
    # A sore back that is "still" sore is the complaint again, not a report on a fix, and the
    # same goes for feeling ill, tired or low: no home fix is what was being tried.
    if HEALTH.search(" ".join(state)):
        return ""
    return " ".join(state)


def still_the_state(text, memory):
    """True when a short "still ..." line names a state the chat has already named."""
    return bool(the_still_state(text, memory))


# A cheap look before the readers below: does the line have any word that could make it a report
# on the answer, a step already done, or an ask about the step handed back? The knowledge module
# asked this of every line it saw, and the readers behind it walk the store's tables, so the
# shapes are checked here first. Every reader below is reached by one of these words, so nothing
# is lost by asking.
def might_be_a_report(text):
    said = " ".join(words_of(text))
    if not said or len(said.split()) > 20:
        return False
    return bool(NOT_WORKED.search(said) or MADE_IT_WORSE.search(said) or TRIED.search(said)
                or STILL_STATE.search(said) or STEP_DONE.search(said) or STEP_DID.search(said)
                or YET.search(said) or NAMED_TRY.search(said))


def names_a_trade(text):
    """True when the line already hands the thing over to a trade."""
    said = " ".join(words_of(text))
    for _entry_words, trade, _needs in TRADES:
        name = str(trade or "").split(",")[0].strip().lower()
        if name and name in said:
            return True
    return False


def after_an_answer(memory):
    """True when the bot's last turn was an answer, so "still blocked" is about that answer.

    A turn where the reply already named a trade counts too: "i tried that" then "it didnt work"
    is the person reporting twice on the same thing, and the second report is still about an
    answer. A shrug never counts, so nothing is escalated out of nothing.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    module = str(turns[-1].get("module") or "")
    if module in ANSWER_MODULES:
        return True
    if module != "chat":
        return False
    # A step handed back out of the answer just given is that answer carrying on, so a report on
    # it is a report on the answer: "ive tried the plunger" then "and that didnt work" still wants
    # the plumber, and without this the second line lost the thread and got a shrug.
    if memory.get("handed_back_step") == len(turns) - 1:
        return True
    # A reply that already named the trade, or asked what the thing is doing, is the answer this
    # report is about: a run of reports stays one conversation instead of dead-ending.
    return names_a_trade(turns[-1].get("bot")) or asked_what_its_doing(memory)


def last_answer_words(memory):
    """The words the person used for the thing, so the trade can be found from them.

    Only the person's own words: the question that was answered and the words the entry was
    reached by. The bot's prose is deliberately not read, because it is full of everyday nouns -
    an answer about films says "a sofa with no planning", and "sofa" would have sent a person
    whose film did not help off to a dry cleaner.
    """
    said = [str(line or "") for line in _the_lines(memory)]
    last = memory.get("last_answer")
    if isinstance(last, dict):
        keys = last.get("keys")
        if isinstance(keys, (list, tuple, set, frozenset)):
            said.extend(str(key) for key in keys)
    return set(words_of(" ".join(said)))


# The turn that was answered has to be about something going wrong, or about how to do
# something: "i have a blocked sink", "how do i get rid of ants", "my boiler is making a noise".
# A recommendation that turned out not to be to someone's taste ("whats a good film tonight" /
# "that didnt help") is not a home fix that has run out, and no trade belongs in it.
PROBLEM_OR_FIX = re.compile(
    r"\b(?:how (?:do|can|should|would|could) i|how to|what (?:do|can|could) i do|"
    r"any (?:tips|advice)|what should i do)\b|"
    r"\b(?:is|are|keeps|keep|was|wont|won'?t|doesn'?t|doesnt|isn'?t|isnt|not) "
    r"(?:\w+ )?(?:working|worked|blocked|broken|stuck|sticking|jammed|jamming|dragging|"
    r"leaking|dripping|clogged|smelling|smells|"
    r"noisy|coming back|moving|rising)\b|"
    r"\b(?:blocked|broken|stuck|leaking|clogged)\b|"
    r"\bi (?:can'?t|cant|couldn'?t|couldnt)\b|"
    r"\b(?:wont|won'?t) (?:come|get|go away|stop|budge)\b|"
    r"\b(?:wont|won'?t|doesn'?t|doesnt|keeps? (?:on )?)\b"
)


def asks_for_a_fix(memory):
    """True when the turn that was answered was a problem or a how-to, not a recommendation."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    asked = " ".join(words_of(turns[-1].get("user")))
    if not asked:
        return False
    if PROBLEM_OR_FIX.search(asked):
        return True
    if len(turns) > 1:
        before = " ".join(words_of(turns[-2].get("user")))
        return bool(PROBLEM_OR_FIX.search(before))
    return False


# A trade is only handed over when there is evidence of the fault it deals with, read from the
# person's own words. The words a trade is looked up by are not evidence on their own: an answer
# about cleaning an oven is about an oven, and an answer about a cat scratching the sofa is about
# a cat, but nothing is broken in either, and nobody should be sent to a repair line or a vet for
# a question about housework or an animal's habits.
FAULT = re.compile(
    r"\b(?:broke|broken|breaking|not working|stopped working|stopped|wont|won'?t|doesn'?t|"
    r"doesnt|isn'?t|isnt|leak|leaks|leaking|drip|dripping|noise|noisy|banging|knocking|"
    # "how do i unblock my sink" is the fault said as a how-to: the answer's own words name the
    # fault, and "i tried that and it didnt work" then has nothing to point at without this.
    r"rattl\w*|blocked|blockage|unblock\w*|stuck|sticking|jammed|jamming|clogged|"
    r"dragging|not (?:shutting|opening|closing)|smell|smells|smelling|smelly|"
    r"smoke|"
    r"smoking|sparking|dead|fault|faulty|overheat\w*|flashing|damaged|gone wrong|packed in|"
    r"keeps? (?:cutting out|going off|stopping|tripping|switching off|playing up|packing in)|"
    r"cuts? out|cutting out|played up|playing up|on the blink|packing in|not firing|"
    r"drains? slowly|slow to drain)"
)
HEALTH = re.compile(
    r"\b(?:ill|sick|poorly|unwell|pain|hurt\w*|limp\w*|vomit\w*|swollen|swelling|"
    r"not eating|off (?:his|her|their|its) food|wont eat|won'?t eat|blood|pus|constipated|"
    r"breathing|wheez\w*|shaking|trembling|dying|discharge|losing (?:fur|weight))\b"
)
MARK = re.compile(r"\b(?:stain\w*|mark|marks|smudge|spill\w*|ink|wine|coffee|grease|scuff)\b")

EVIDENCE = {"fault": FAULT, "health": HEALTH, "mark": MARK}

# Nothing is being repaired that has not been bought yet: "i need a new hoover, which one" and
# "recommend a laptop for uni" were being read as a thing that had stopped working.
BUYING = re.compile(
    r"\b(?:which one|which (?:\w+ )?(?:is|to|should)|recommend\w*|best|any good|"
    r"worth (?:buying|getting)|should i (?:buy|get)|need a new|needs a new|"
    r"thinking of (?:buying|getting)|going to (?:buy|get)|want to (?:buy|get)|"
    r"shopping for|looking (?:for|at) (?:a|some)|what should i (?:buy|get)|"
    r"how much (?:do|does|are|is) (?:they|it|these))\b"
)


def buying(memory):
    """True when the turn that was answered was about choosing or buying, not about a fault."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    return bool(BUYING.search(" ".join(words_of(turns[-1].get("user")))))


def person_said(memory):
    """The person's own last two lines, which are the only evidence for a fault.

    Not the words the answer was reached by: an oven-cleaning entry is reached by "smoke" and
    "grease", and reading those as a fault sends a person who is cleaning an oven to a repair
    line. The person's sentence is the one that says whether something has stopped working.
    """
    return " ".join(" ".join(words_of(line)) for line in _the_lines(memory) if line)


def _the_lines(memory):
    """The person's own lines that can name the thing, newest first.

    The answered line always counts. The line before it counts only when the answered line is
    itself a report that a fix did not work ("it didnt work", "the reset did nothing"), because
    that is when the thing was named a turn earlier. When the answered line asks about something
    of its own the chat has moved on, and a thing from before it is the wrong subject: after "my
    boiler is broken" / "my kids wont sleep", the report "tried everything" was handed "Then it's
    past a home fix: a Gas Safe engineer" - an answer about a boiler to a parent asking about a
    child's sleep.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return []
    said = [turns[-1].get("user")]
    if len(turns) > 1 and reads_as_not_worked(" ".join(words_of(turns[-1].get("user")))):
        said.append(turns[-2].get("user"))
    return said


def _names(said, blob, entry_words):
    """True when the words name the thing: the word itself, its plural or -ing, or a phrase.

    "the washing machine isnt draining" names a washing machine and a drain; the word list holds
    both "washing machine" (two words, so a whole-token set will never match it) and "drain"
    (which the line has as "draining").
    """
    if said.intersection(entry_words):
        return True
    for word in entry_words:
        if " " in word:
            if word in blob:
                return True
        elif len(word) >= 5 and any(token.startswith(word) for token in said):
            return True
    return False


# The report itself can say what is still wrong ("still blocked", "still leaking"), which is
# evidence on its own. "still not working" is not: it says nothing about what the thing is doing.
STILL_SPECIFIC = re.compile(
    r"\bstill (?:blocked|leaking|dripping|clogged|stuck|broken|coming back|noisy|smelling|"
    r"jammed|squeaking|the same|not draining|wont|won'?t|there)\b"
)
# "i tried a budget app", "ive tried a new chair": the person names what they did, so there is
# something to ask about. "tried that" names nothing.
NAMED_TRY = re.compile(r"\b(?:tried|used|gave)\s+(?:a|an|the|my|some|his|her|their|this new)\b")


def names_a_thing(memory):
    """True when the person's own words name something a home fix could be about.

    "my kids wont eat vegetables" / "ive tried everything" was handed the boiler's next line -
    "Tell me what it's doing now - still the same, different, or worse" - because "wont" is a
    fault word and the turn before was an answer. But a child's dinner is not a thing that is
    doing anything, and the question is the one asked of a machine. The things that can be
    waiting on a trade are the ones TRADES is made of, so a line that names none of them has
    nothing for "what is it doing now" to be about and gets no next step from here.

    Only the person's own words count: an answer reached by "grease" or "smoke" is about an
    oven, and that is not a person saying their oven is broken.
    """
    said = set(words_of(person_said(memory)))
    if not said:
        return False
    blob = " ".join(sorted(said))
    return any(_names(said, blob, entry_words) for entry_words, _, _ in TRADES)


def has_evidence(text, memory):
    """True when there is something for "what is it doing now" to be about.

    A vague "no luck" after advice about starting to run, cleaning an oven or getting rid of a
    cold leaves nothing broken to ask about, and "Tell me what it's doing now" then reads as a
    machine talking about an object. So the question is only asked when the turn that was
    answered names a fault, or the report says what is still wrong, or names what was tried.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    asked = " ".join(words_of(turns[-1].get("user")))
    if FAULT.search(asked) or MARK.search(asked) or NAMED_TRY.search(asked):
        return True
    report = " ".join(words_of(text))
    if STILL_SPECIFIC.search(report) or NAMED_TRY.search(report):
        return True
    return bool(MADE_IT_WORSE.search(report) and POINTS_AT_THE_THING.search(report))


def asked_what_its_doing(memory):
    """True when the bot's last turn asked what the thing is doing now."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    said = " ".join(words_of(turns[-1].get("bot")))
    return "doing now" in said or "happens now when you try" in said


def already_named(trade, memory):
    """True when the last turn already said this trade, so saying it again is a loop.

    "i tried that" then "it didnt work" is a person reporting twice on the same fix; naming the
    plumber twice reads as not listening. The second report asks what the thing is doing instead.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    name = str(trade or "").split(",")[0].strip().lower()
    if not name:
        return False
    # Only a reply this module produced counts. The boiler answer already says "call a Gas Safe
    # engineer" as its own advice, and reading that as "I have named the trade" left the report
    # with nothing to escalate to.
    said = " ".join(" ".join(words_of(t.get("bot"))) for t in turns[-2:]
                    if str(t.get("module") or "") == "chat")
    return bool(name) and name in said


def _the_answered_line(memory):
    """The line the last answer answered, which says what the turn was about."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    return str(turns[-1].get("user") or "") if turns else ""


def trade_for(memory):
    """The trade that takes this over, as a phrase, or None when none fits."""
    said = last_answer_words(memory)
    words = person_said(memory)
    blob = " ".join(sorted(said)) + " " + words
    # "i turned it and now it is worse": a fix that made the thing worse is evidence of the
    # fault the trade deals with, in the person's own words. It only counts when the answer
    # that was followed was about a fault: "how do i clean my oven" / "i wiped it and now it is
    # worse" is housework, and nobody is sent to a repair line for housework.
    worse = bool(MADE_IT_WORSE.search(words) and POINTS_AT_THE_THING.search(words))
    about_a_fault = bool(FAULT.search(" ".join(words_of(_the_answered_line(memory)))))
    for entry_words, trade, needs in TRADES:
        if not _names(said, blob, entry_words):
            continue
        if needs is None:
            return trade
        pattern = EVIDENCE.get(needs)
        if pattern is None:
            continue
        if pattern.search(words) or (needs == "fault" and worse and about_a_fault):
            return trade
    return None


# A line that says the advice was used: "i already told her that", "i sent it", "i texted him".
# The previous turn has to be a what-should-i-say ask, so a report about a conversation the bot
# did not advise on ("my boss blamed me" / "i told her") keeps its own answer.
ACTED_SAID = re.compile(
    r"^(?:i|we)\s+(?:(?:have|had|already|just|finally|actually)\s+)*"
    r"(?:told|done|did|sent|texted|messaged|emailed|called|rang|phoned|asked|"
    r"said\s+(?:(?:it|that)\s+)?to|spoke\s+(?:to|with)|talked\s+(?:to|with)|"
    r"said\s+what\s+you\s+(?:suggested|said)|"
    r"used\s+(?:it|that|your\s+(?:wording|words|line|suggestion|advice|text)))\b"
)
# The ask itself, not a recall of what was said before: "what did i say about my trip" is a
# memory question, so the modal is required and "did" is not one of the modals. A "what to say"
# ask has no subject and is allowed on its own.
SAY_ADVICE = re.compile(
    r"\b(?:what|how|which)\s+(?:(?:should|shall|do|can|could|would)\s+)?(?:i|we)\s+"
    r"(?:say|tell|text|message|write|email|call|ask|talk|speak|word)\b"
    r"|\bwhat\s+to\s+(?:say|tell|text|message|write|email)\b"
    r"|\b(?:how|what)\s+(?:would|could|should)\s+you\s+(?:say|word|phrase)\b"
)
TOLD_THE_BOT = re.compile(r"\b(?:told|said|texted|messaged|emailed|called|asked)\s+you\b")
ACTED_REPLIES = (
    "How did it land?",
    "What did they say?",
    "Did it come across the way you meant?",
    "How did that go over?",
    "Did it help?",
)


def acted_pool(text, memory):
    """The line after advice that was acted on: ask how it went, not what the advice was.

    "what should i say to her" / "i already told her that" was answered with
    "Got it. Is there anything you'd like a hand with?", which drops the thread. The person has
    done the thing the bot suggested; the next useful thing a friend says is a question about
    what happened, and the store already knows the last turn was advice.
    """
    line = " ".join(words_of(text))
    if not ACTED_SAID.match(line) or TOLD_THE_BOT.search(line):
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return None
    last = turns[-1]
    # The advice can come from any module: the common "what do i say to her" is often answered
    # by a hedge from greeting, and that still leaves the person with words to use. A safety
    # answer is the one exception, because a line after it belongs to that thread.
    if str(last.get("module") or "") == "safety":
        return None
    asked = " ".join(words_of(last.get("user")))
    if not SAY_ADVICE.search(asked):
        return None
    return ACTED_REPLIES


# "i tried the plunger but the sink is still blocked" says one step; "ive tried the filter and the
# drawer" says two, and both are the answer's. A tail that opens on an article or a possessive is
# another object of the same doing word, so the line is kept whole.
STEP_TAIL_NOUN = re.compile(
    r"^(?:the|a|an|my|its|their|our|your|his|her|this|that)\b", re.I)


def _up_to_the_contrast(what):
    """The step the line names, with a second object kept and a change of subject dropped."""
    pieces = re.split(r"\s+(but|and|though|although|yet)\s+", what, maxsplit=1, flags=re.I)
    if len(pieces) < 3:
        return what
    head, joint, tail = pieces
    if joint.lower() == "and" and STEP_TAIL_NOUN.match(tail.strip()):
        return what
    return head


def _read_step_tried(text):
    """(the step the person says they have done, the shape it was said in) or (None, None).

    "ive tried the plunger" -> "the plunger", "i already restarted the router" -> "restarted the
    router", "cleaned the filter already" -> "cleaned the filter". None when the line names no
    step ("tried that" is the report above, not a step of the answer).
    """
    line = " ".join(str(text or "").lower().split()).strip().strip(".,!")
    if not line or "?" in line or len(line.split()) > 14:
        return None, None
    # A line that also says the answer failed is the report below, which has the trade and the
    # "what is it doing now" question; only the attempt on its own asks for the next step.
    if NOT_WORKED.search(line) or IMPROVED.search(line) or WORSE.search(line):
        return None, None
    for pattern in (STEP_ALREADY, STEP_TRIED, STEP_LAST, STEP_DONE, STEP_DID):
        found = pattern.match(line)
        if not found:
            continue
        what = " ".join(found.group("what").split()).strip(" .,!'")
        # "i tried the cream already", "i tried the plunger but the sink is still blocked": the
        # step is what the doing word is about, not the rest of the sentence.
        what = re.sub(r"\s+already$", "", what)
        # "i tried everything" reaches the plain "i <doing word>" shape with the trying still on
        # the front, and it names no step: the trying is the marker, not what the step was.
        what = re.sub(r"^(?:tried|used)\s+", "", what)
        what = _up_to_the_contrast(what).strip(" .,!'")
        words = [w for w in words_of(what) if w not in STEP_EMPTY]
        if not words or set(words) <= STEP_VAGUE:
            continue
        return what, pattern
    return None, None


def the_step_tried(text):
    """The step the person says they have done, as they put it, or None."""
    return _read_step_tried(text)[0]


# A step said as a plain past-tense report: "i ran a hot wash with vinegar", "we bled the
# radiators". None of the shapes above reads a verb the answer wrote in the imperative ("Run a hot
# service wash"), so the answer in hand is what says the line is one of its steps.
PAST_STEP = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|yeah|yep|no|nah|hmm|ah|right|alright|then)\W+)*"
    r"(?:i|we)\s+(?P<what>[a-z0-9' ]{3,80})$", re.I)


def _the_past_step(text, said):
    """The step the line reports in the plain past tense, when it is one of the answer's own."""
    line = " ".join(str(text or "").lower().split()).strip().strip(".,!")
    if not line or not said or "?" in line:
        return None
    if NOT_WORKED.search(line) or IMPROVED.search(line) or WORSE.search(line):
        return None
    found = PAST_STEP.match(line)
    if not found:
        return None
    what = " ".join(found.group("what").split()).strip(" .,!'")
    what = re.sub(r"\s+already$", "", what)
    what = re.split(r"\s+(?:but|and|though|although|yet)\s+", what)[0].strip(" .,!'")
    words = [w for w in words_of(what) if w not in STEP_EMPTY]
    if len(words) < 2:
        return None
    first = words[0]
    if first not in PAST_IRREGULAR and not (PAST_STEP_ED.match(first)  # noqa: E501
                                            or first in SHORT_PAST):
        return None
    # The report has to be about the answer's own steps, and it has to share something real with
    # them: a past-tense line about another thing ("i went to the shop") is not this answer.
    if not in_the_answer(what, said):
        return None
    return what


def _the_last_answer(memory):
    """The knowledge base's last reply, or "" - the answer a report on it is about."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return ""
    last = turns[-1]
    if str(last.get("module") or "") != "answers":
        return ""
    return str(last.get("bot") or "")


def _stem(word):
    """The word without its ending, so "topping", "topped" and "top" are the same step."""
    for ending in ("ing", "ed", "es", "s"):
        if len(word) - len(ending) >= 3 and word.endswith(ending):
            word = word[:-len(ending)]
            # "topp" and "bleedd": a doubled letter is where the ending was joined on.
            if ending in ("ing", "ed") and len(word) > 3 and word[-1] == word[-2]:
                word = word[:-1]
            break
    return word


def _step_stems(text):
    return {_stem(w) for w in words_of(text) if w not in STEP_EMPTY and w not in STEP_VAGUE}


# The endings that leave a word naming the same step: "clean", "cleans", "cleaned", "cleaning".
# Anything else after the stem is a different word ("cleaner" is the bottle, "washing" the job).
SAME_STEP = frozenset(("", "s", "es", "ed", "d", "ing"))


def _names_it(part, stems):
    """True when this piece of the answer is the step the person has already done."""
    for word in words_of(part):
        got = _stem(word)
        for tried in stems:
            if got == tried:
                return True
            # "clean" and "cleaned" are the same step; "clean" and "cleaner" are not - the "-er"
            # makes it the thing used for the job ("a washing-machine cleaner"), so the plain
            # prefix rule read the bottle in "run a hot service wash with a cleaner" as the step
            # "cleaned the filter" and walked past the washing machine's first step.
            if len(got) >= 5 and tried.startswith(got) and tried[len(got):] in SAME_STEP:
                return True
            if len(tried) >= 5 and got.startswith(tried) and got[len(tried):] in SAME_STEP:
                return True
    return False


# One part of an answer can hold two moves: "social and video apps are usually it, so restrict
# background refresh and turn the screen brightness down". The step they did is in the part, and
# the part still has work after it, so it is not the part to skip - the move after theirs is the
# next thing to do.
MOVES = re.compile(r",\s*|\s+so\s+|\s+and\s+", re.I)


def _the_move_after(part, stems):
    """The move left in this part once the step the person has done is taken out of it."""
    return _the_move_pieces(part, stems)[1]


def _the_move_pieces(part, stems):
    """The piece that names the step they did, and the moves left after it in the same part."""
    if A_CONDITION.match(str(part or "").strip()):
        # "if the phone is two years old, have a look at battery health" is one step: the
        # condition and the doing belong together, so there is no move after it inside it.
        return "", ""
    pieces = [p.strip(" .,;:") for p in MOVES.split(str(part or "")) if p.strip(" .,;:")]
    # The move that holds most of what they said, and the last of those: the reading of the
    # answer ("social and video apps in the background are usually it") shares its subject with
    # the step it introduces ("restrict background refresh"), and the step after that shares its
    # verb with the one they did ("turn the screen brightness down" against "turned off ...").
    # Counting the words that match puts the step itself between the two.
    best, last = 0, None
    for i, piece in enumerate(pieces):
        words = set(words_of(piece))
        hits = sum(1 for tried in stems
                   if any(w == tried or (len(w) >= 5 and tried.startswith(w)
                                         and tried[len(w):] in SAME_STEP)
                          or (len(tried) >= 5 and w.startswith(tried)
                              and w[len(tried):] in SAME_STEP) for w in words))
        if hits and hits >= best:
            best, last = hits, i
    if last is None:
        return "", ""
    rest = pieces[last + 1:]
    if not rest:
        return pieces[last], ""
    left = " and ".join(rest)
    if PRONOUN_TAIL.match(left) or (TAIL_WORD.match(left) and not _opens_a_step(left)):
        # "put it as central as the phone line allows" is the end of the step before it: on its
        # own the "it" points at a sentence that is not there.
        return pieces[last], ""
    return pieces[last], (left if _opens_a_step(left) else "")


def _clauses(text):
    """The move cut where one thing to do ends and the next begins."""
    out, piece, depth = [], [], 0
    for chunk in CLAUSE.split(" ".join(str(text or "").split())):
        depth += chunk.count("(") - chunk.count(")")
        if piece and depth > 0:
            piece.append(chunk)
            continue
        if piece:
            out.append(", ".join(piece))
        piece = [chunk]
    if piece:
        out.append(", ".join(piece))
    return [p.strip(" .,;:") for p in out if p.strip(" .,;:")]


def _a_step(piece):
    """One clause as a step: the next thing to do, not the paragraph it came out of."""
    piece = piece.strip(" .,;:")
    if len(piece.split()) > STEP_WORDS:
        # What to do comes before the examples that follow a colon.
        head = piece.split(": ")[0].strip(" .,;:")
        if head and head != piece:
            piece = head
    if piece and len(piece.split()) > STEP_WORDS:
        # "If the phone is two or more years old, have a look at battery health, because a worn
        # battery drains no matter what you switch off" is one step with its reason after it.
        # Dropped whole for its length, the answer had no step after the one they did.
        head, comma, tail = piece.partition(", ")
        if comma and A_CONDITION.match(head):
            step = tail.split(", ")[0].strip(" .,;:")
            if step and _opens_a_step(step):
                piece = head + ", " + step
    if not piece or len(piece.split()) > STEP_WORDS or len(piece) > 180:
        return ""
    return piece


# An answer writes a step the other way round when it only applies some of the time: "if the
# phone is two or more years old, have a look at battery health". The condition is the first
# clause, so the step never opens the piece and every walk over the answer read it as the tail of
# the step before it - the person who had switched background refresh off was handed that step
# again instead of the one that was left.
A_CONDITION = re.compile(r"^(?:if|when|once|unless|whenever|wherever)\b", re.I)


def _opens_a_step(part):
    """True when the piece opens on a doing word, which is what a step looks like."""
    from ..compose.verdict import IMPERATIVES

    words = words_of(part)
    if not words:
        return False
    first = words[0]
    if first in IMPERATIVES or first in MORE_STEP_VERBS:
        return True
    # "if <condition>, <step>": the doing word is in the second clause.
    head, comma, tail = str(part or "").strip().partition(", ")
    if comma and A_CONDITION.match(head):
        rest = words_of(tail)
        if rest and (rest[0] in IMPERATIVES or rest[0] in MORE_STEP_VERBS):
            return True
    return False


def _the_step_after(thing, memory):
    """The next step of the answer just given, in its own words, or "".

    Only an answer from the knowledge base is walked: the reply before this line has to hold the
    steps, and a chat or a safety answer does not. The step named has to be in that answer, so a
    line about something else entirely is left to the modules that can answer it.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return ""
    last = turns[-1]
    if str(last.get("module") or "") != "answers":
        return ""
    return _walk_answer(str(last.get("bot") or ""), thing)


def _the_steps_of(said):
    """The answer cut into the pieces that could be a step, in the order it was written."""
    from . import repeat  # the sentence and move readers, kept off the import path

    if not said:
        return []
    # The composer's own "move" is not used: it is cut down to the first instruction, and the
    # step after the one they tried is often the second half of that same sentence ("start with
    # a plunger ..., then undo the trap").
    parts = []
    for sentence in repeat.SENTENCE.split(str(said).strip()):  # noqa: SLF001 - same package
        for clause in _clauses(sentence):
            piece = _a_step(clause)
            if piece and piece not in parts:
                parts.append(piece)
    return parts


def _list_heads(said):
    """The pieces that only introduce the list that follows them.

    "Change a few things you can keep doing rather than going on a diet: fill half the plate with
    vegetables, ..." opens on a doing word, so the walk read the heading as a step of its own and
    handed it back as the next thing to do - a sentence with nothing in it to act on, given to a
    person who had just said the walking was already part of their day. A sentence that ends at a
    colon is a heading, not a step (`_the_steps_of` cuts the items of the list into parts of their
    own, which are the steps).
    """
    from . import repeat  # the sentence reader, kept off the import path

    heads = set()
    for sentence in repeat.SENTENCE.split(str(said or "").strip()):  # noqa: SLF001
        head, colon, rest = sentence.partition(":")
        if not colon or not rest.strip():
            continue
        for clause in _clauses(head):
            piece = _a_step(clause)
            if piece:
                heads.add(_flat(piece))
    return heads


# The words around a step that say when it was done, not what it was done to.
STEP_TIMING = frozenset("""last week weeks month months year years today yesterday already now twice
    once again day days night morning time""".split())


def _object_stems(text):
    """The words of a step that name the thing it is done to, leaving out the doing word."""
    out = set()
    for w in words_of(text):
        if w in STEP_EMPTY or w in STEP_VAGUE or w in STEP_TIMING:
            continue
        if w in PAST_IRREGULAR or w in SHORT_PAST or PAST_STEP_ED.match(w):  # noqa: E501
            continue
        if DOING_WORD.match(w):
            continue
        out.add(_stem(w))
    return out


def in_the_answer(thing, said):
    """True when one of these pieces names what the person says they have done."""
    stems = _step_stems(thing)
    if not stems:
        return False
    parts = _the_steps_of(said)
    if not any(_names_it(part, stems) for part in parts):
        return False
    # Sharing the doing word is not enough to name a step: "ive cleaned the bathroom" shares
    # "clean" with the washing machine answer and names a thing that answer never mentions, so
    # the person was told to run a service wash because they had cleaned a bathroom. The thing
    # the step is done to has to be in the answer too, when the line names one.
    objects = _object_stems(thing)
    if objects:
        return any(_names_it(part, objects) for part in parts)
    return True


# An answer often ends on the one line that says how to keep the fix: "leaving the door and
# drawer open between washes is what stops the smell coming back". It is not a step - it opens on
# a doing word used as the subject of the sentence - but it is what the answer has to say after
# its last step, so an ask for the next part is answered with it rather than a search hedge.
KEEPS_IT_RIGHT = re.compile(
    r"\b(?:stops?|keeps?|prevents?|avoids?|is what|are what|helps?|means)\b", re.I)


def _flat(text):
    return " ".join(str(text or "").lower().split()).strip(" .,;:")


def _the_first_step_left(said, seen, after=""):
    """The answer's first step that has not been handed back yet, or "".

    `after` is the step the bot has just given: asked what comes next, only the parts after it
    are the answer. Without it the walk wraps back to the top of the answer and hands over the
    part they have already been given - "then what" after "pull the gunk out" got "Start with a
    plunger over the plughole" again instead of the kettle of hot water that comes after it.
    Asked for the next part twice on an answer with no step after the ones given, the walk has
    nothing left to hand over and the line fell to a pool that repeated the whole first sentence
    of the answer with a lead on it. The answer's own step one is what a person who asks again is
    owed, said once, without the step they have done inside it.
    """
    from . import repeat  # the "says what to do" reader, kept off the import path

    heads = _list_heads(said)
    parts = _the_steps_of(said)
    if after:
        where = _flat(after)
        for i, part in enumerate(parts):
            flat = _flat(part)
            if where and (flat == where or where in flat or flat in where):
                parts = parts[i + 1:]
                break
    for part in parts:
        flat = _flat(part)
        if flat in heads:
            continue
        # A part that holds a step already handed over is that step's part, not a new one:
        # "bleed the radiators, check the pressure is 1 to 1.5 bar" is not handed again after the
        # pressure was the step given.
        if any(flat == was or was in flat for was in seen):
            continue
        if _opens_a_step(part) and repeat._says_what_to_do(part):  # noqa: SLF001
            return part
        # The answer's last move can be written as a condition ("and if it carries on get a
        # heating engineer to look at the pump"), which is a step like any other: asked what else
        # to do once the pressure had been handed over, the boiler answer had nothing left and
        # the line fell to repeating its first sentence.
        joined = re.sub(r"^(?:and|but|or)\s+", "", flat, flags=re.I)
        if A_CONDITION.match(joined) and repeat._says_what_to_do(joined):  # noqa: SLF001
            if joined != flat:
                joined = joined[:1].upper() + joined[1:]
            return joined
    # A part after the step just given can say what to do without opening on the doing word ("A
    # kettle of hot water with a spoonful of bicarbonate and vinegar clears the rest"), and that
    # is what comes next: asked "then what" after the trap, the line fell to a module that quoted
    # the answer's first sentence again instead of saying the kettle.
    if after:
        for part in parts:
            flat = _flat(part)
            if flat in heads or any(flat == was or was in flat for was in seen):
                continue
            if repeat.ASKING_THEM.search(part):  # noqa: SLF001 - a question is not a step
                continue
            if repeat._says_what_to_do(part):  # noqa: SLF001
                return part
    return ""


def _with_its_tail(part, parts, i):
    """The step and the part after it, when the answer wrote them as one instruction.

    "Skip the chemical cleaner until last, and fill the trap with a hair collector so it does not
    come back" is one sentence of the answer, and the walk handed over the first half alone. The
    person who had tried the plunger was told to skip the cleaner and lost the hair collector.
    Only a part that itself says what to do is joined, and only into one sentence.
    """
    from . import repeat  # the "says what to do" reader, kept off the import path

    # Only the answer's own last part: joining two steps of a list makes a long reply, and the
    # walk hands over the rest of the list on the next ask anyway.
    if i + 2 != len(parts):
        return part
    nxt = parts[i + 1]
    if not repeat._says_what_to_do(nxt) or repeat.ASKING_THEM.search(nxt):  # noqa: SLF001
        return part
    if A_CONDITION.match(nxt) or _flat(nxt) in _list_heads(nxt):
        return part
    if len(words_of(part)) + len(words_of(nxt)) > 40:
        return part
    return part.rstrip(" .,;:") + ", and " + nxt[:1].lower() + nxt[1:]


def _the_advice_after(parts):
    """The answer's own line on keeping the thing right, among the parts still to be used."""
    from . import repeat  # the question reader, kept off the import path
    from . import topics  # noqa: F401 - the red flag is not advice about the thing

    for part in reversed(parts):
        if len(words_of(part)) < 5:
            continue
        if repeat.ASKING_THEM.search(part):  # noqa: SLF001 - a question is not a step
            continue
        if topics.RED_FLAG.match(part):
            continue
        # A piece that opens on a pronoun object ("put it as central as the line allows") is the
        # end of the step before it, so it is never handed over on its own. A "then"/"if" piece
        # is only the tail when it does not hold a step of its own.
        if PRONOUN_TAIL.match(part) or (TAIL_WORD.match(part) and not _opens_a_step(part)):
            continue
        if KEEPS_IT_RIGHT.search(part):
            return part
    return ""


def _walk_answer(said, thing, wrap=True):
    """The first step of this answer after the part that names what they have done, or "".

    `wrap` is off for the ask after a step the bot has already handed over: two steps on, the
    answer's first step is one the person has had or has done ("what else can i try" after the
    plunger was handed back is the kettle, not the plunger again).
    """
    from . import repeat  # the sentence and move readers, kept off the import path
    from . import topics  # noqa: F401 - the red flag is not a step to try

    parts = _the_steps_of(said)
    stems = _step_stems(thing)
    if not parts or not stems:
        return ""
    heads = _list_heads(said)
    # The answer has to be about the thing they are working on.
    if not any(_names_it(part, stems) for part in parts):
        return ""
    # Everything up to the step they have done has been read and tried: the next step is the one
    # after the first part that names it. The first, not the last, because a good answer names
    # the step again at the end ("stop topping it up and get an engineer out"), and walking past
    # that leaves nothing.
    start = 0
    theirs_is_a_step = False
    for i, part in enumerate(parts):
        if _names_it(part, stems):
            # The part that names it can hold the step they did and the one after it:
            # "bleed the radiators, check the pressure is 1 to 1.5 bar", "undo the trap
            # underneath (bucket first) and pull the gunk out".
            named, move = _the_move_pieces(part, stems)
            if move and repeat._says_what_to_do(move):  # noqa: SLF001
                return move
            # The piece that names it is the step of the answer, even when the part is written
            # round it ("social and video apps in the background are usually it, so restrict
            # background refresh and turn the screen brightness down").
            theirs_is_a_step = _opens_a_step(part) or _opens_a_step(named)
            start = i + 1
            break
    if not theirs_is_a_step:
        # The part that names it is the answer saying why ("A dripping tap is nearly always a
        # worn washer or cartridge"), not one of its steps, so the steps after it are the
        # answer's whole sequence rather than what is left of theirs: "ive changed the washer"
        # was handed "turn the water off at the isolating valve ..., take the handle off", which
        # is what you do before changing a washer, not after.
        return _the_advice_after(parts[start:]) if not wrap else ""
    for i, part in enumerate(parts[start:], start):
        if _names_it(part, stems):
            # The same part can hold the step they did and the one after it.
            move = _the_move_after(part, stems)
            if move and repeat._says_what_to_do(move):  # noqa: SLF001
                return move
            continue
        if repeat.ASKING_THEM.search(part):  # noqa: SLF001 - a question is not a step
            continue
        if topics.RED_FLAG.match(part):
            # The warning is where the answer ends, not the next thing to do: a person who has
            # tried one step is not handed "see a GP if it lasts a week" as their next step.
            continue
        # A piece that opens on "and", "not" or "if" is the tail of the step before it, not a
        # step of its own ("and put it as central as the phone line allows" on its own is not a
        # thing to do).
        # A piece that opens on a pronoun object ("put it as central as the line allows") is the
        # end of the step before it, so it is never handed over on its own. A "then"/"if" piece
        # is only the tail when it does not hold a step of its own.
        if PRONOUN_TAIL.match(part) or (TAIL_WORD.match(part) and not _opens_a_step(part)):
            continue
        if _flat(part) in heads:
            continue
        # A step opens on the doing word: "it's a 20-minute job and saves a lot of water" is the
        # answer explaining itself, not the next thing to do. The doing word is enough on its own:
        # "Mow little and often in the growing season, not shorter than about 4cm" is a step of the
        # lawn answer, and the part after it ("leave the clippings off unless it is long") cannot
        # be handed on its own because the "it" is the mowing.
        if _opens_a_step(part):
            return _with_its_tail(part, parts, i)
    # Nothing follows the step they did: an answer gives its steps in one order and people start
    # in the middle of it. "ive cleaned the filter" after the washing-machine answer has the hot
    # service wash still to do, and it is the part before theirs. With nothing walked back the
    # line fell through to the knowledge base, which answered it with the vacuum cleaner's filter
    # because "filter" is one of that entry's words - a different appliance, on the same line.
    if not wrap:
        # The ask after a step the bot handed back, with nothing behind it that opens on a doing
        # word: the answer's own line on keeping the thing right is what comes next, because that
        # is what the answer has to say after its last step. "and then what" after the washing
        # machine's service wash got the search hedge, because "leaving the door and drawer open
        # between washes is what stops the smell coming back" shares `wash` and `drawer` with the
        # step and was skipped as the step they had - it is not a step, so it is not that.
        advice = _the_advice_after(parts[start:])
        if advice:
            return advice
        return ""
    for part in parts[:max(start - 1, 0)]:
        # A piece that opens on a pronoun object ("put it as central as the line allows") is the
        # end of the step before it, so it is never handed over on its own. A "then"/"if" piece
        # is only the tail when it does not hold a step of its own.
        if PRONOUN_TAIL.match(part) or (TAIL_WORD.match(part) and not _opens_a_step(part)):
            continue
        if _flat(part) in heads:
            continue
        if _opens_a_step(part) and repeat._says_what_to_do(part):  # noqa: SLF001
            return part
    return ""


def reads_as_a_step_done(text, memory):
    """True when the line says a step of the answer just given is done, whatever comes next.

    `next_step_pool` hands over the step after it; this says only that the line is a report on
    the answer, so a fact entry about a different thing cannot take the turn. Both are needed:
    an answer whose last step is the one they did has no step after it to hand over, and the line
    still is not a question about the world.
    """
    if not isinstance(memory, dict) or not memory:
        return False
    thing, _shape = _read_step_tried(text)
    said = _the_last_answer(memory)
    if not thing:
        # A step said as a plain past-tense report is read against the answer it reports on.
        thing = _the_past_step(text, said)
        if not thing:
            return False
    elif said and not in_the_answer(thing, said):
        # "ive cleaned the bathroom" after the washing machine answer names a thing of its own,
        # and the answer never mentions it: a bathroom is not one of its steps, and reading it as
        # one told the person to run a service wash because they had cleaned a bathroom.
        return False
    if not said:
        return False
    # The walk decides what is handed over; what it decides here is whether the turn is kept.
    walk = _walk_answer(said, thing)
    if walk:
        return True
    # Nothing after their step, so the answer has been used up. The turn is kept only when the
    # whole answer was that one step ("turn the brightness down"): the knowledge base would give
    # the advice they have just followed, a second time, and an answer with nothing else to say
    # is fairly met with "good, see how it goes".
    #
    # An answer with more steps than that is a different thing: what follows the step they did is
    # still to come, so the knowledge base keeps the line and hands over the rest of its own
    # answer. Claimed, the report went to the store's own frame for it, which read the answer's
    # second part out of a clause cut at a comma ("try another socket and cable; if the charger
    # lights up but the laptop is still dead, then"), and the next thing said in the chat lost the
    # thread the answer had ("its still dropping in the back room" was met with an echo).
    return len(_the_steps_of(said)) <= 1


def _as_a_lead(lead, thing, step):
    """The lead filled in: the step opens lower down when it follows a comma."""
    # The person is being addressed, so their own "my" has to turn into "your" before it goes
    # into a sentence about them: "i check my emails at midnight" came out as "You already
    # check my emails at midnight", which reads as if the bot were the one checking. `you()`
    # is the same swap the echo and the reading use, so the two cannot drift apart.
    thing = you(thing)
    step = step.strip(" .,;:")
    # A step that ends on the joiner it was cut at hands over a "then" with nothing after it:
    # "You've already checked the charger. Try another socket and cable; if the charger lights up
    # but the laptop is still dead, then." The word belongs to the part that comes next, so it
    # goes with it rather than onto the end of this one.
    step = re.sub(r",?\s*\bthen$", "", step).rstrip(" ,;:")
    first = step.split()[0] if step.split() else ""
    # The person's own "I", and a name in capitals ("GP", "NHS"), keep their shape.
    if not (first in ("I", "I'm", "I've", "I'd") or (first.isupper() and len(first) > 1)):
        step = step[:1].lower() + step[1:]
    reply = lead.format(thing=thing, Thing=thing[:1].upper() + thing[1:], step=step,
                        Step=step[:1].upper() + step[1:])
    return reply.rstrip(" .") + "."


def next_step_pool(text, memory):
    """The step after the one the person has tried, or None.

    A pool of one, so the caller picks it with the pickers it already uses and nothing is said
    twice. None leaves the line to the report below, which hands over the trade.
    """
    if not memory:
        return None
    thing, shape = _read_step_tried(text)
    said_as_the_past = False
    if not thing:
        thing = _the_past_step(text, _the_last_answer(memory))
        if not thing:
            return None
        said_as_the_past = True
    elif _the_last_answer(memory) and not in_the_answer(thing, _the_last_answer(memory)):
        # The answer is in hand and it never names what they cleaned: "ive cleaned the bathroom"
        # after the washing machine answer is a different job, not a step of this one.
        return None
    # A recommendation is not a set of steps: "ive tried the one i have" after advice about
    # which laptop to buy is not partway through the answer.
    if buying(memory):
        return None
    step = _the_step_after(thing, memory)
    if not step:
        return None
    from ..compose import pick

    # "ive tried the plunger" names the thing, so the lead has to say the trying; "ive cleaned
    # the filter" names the doing, so the lead can say it as done. Which one it is is read from
    # the phrase, not from the marker word the line happened to use.
    says_the_doing = bool(DOING_WORD.match(thing)) and shape is not STEP_TRIED  # noqa: E501
    first_word = (thing.split() or [""])[0].lower()
    as_a_habit = says_the_doing and not (PAST_WORD.match(first_word)  # noqa: E501
                                         or first_word in PAST_IRREGULAR)
    if said_as_the_past:
        # "i ran a hot wash with vinegar": a plain past-tense report, so the lead says it back
        # with their own verb rather than "you've already ran".
        leads = DONE_LEADS
    elif as_a_habit:
        leads = PRESENT_LEADS
    else:
        leads = ALREADY_LEADS if says_the_doing else STEP_LEADS
    reply = _as_a_lead(pick(leads, memory, text), thing, step)
    # Which turn was the answer's continuation, so a report on it is read as a report on the
    # answer (`after_an_answer`). The step and the answer it came out of are kept too, so the
    # ask after it ("and then what") is answered with the part that comes next.
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    memory["handed_back_step"] = len(turns)
    memory["handed_back_text"] = step
    memory["handed_back_seen"] = list(memory.get("handed_back_seen") or []) + [_flat(step)]
    if turns:
        memory["handed_back_answer"] = str(turns[-1].get("bot") or "")
    return [reply]


# The ask after a step handed back out of the answer: "and then what", "what else can i try".
# It is the same walk carried one part further, so the person gets the answer's next step rather
# than the answer's first step again or a search hedge.
NEXT_LEADS = (
    "Then {step}",
    "Next: {step}",
    "After that, {step}",
    "Then this: {step}",
)


# The words such an ask is made of. A line with any other word in it names a thing of its own
# ("what else about the boiler"), so it is a question about that thing and not the next part of
# the answer in hand.
NEXT_ASK_WORDS = frozenset("""what else anything next now other then after that and can could
    should would i we you me my it be is are there more one another again try do does done
    something new also help suggest recommend""".split())


def _asks_for_the_next_part(text):
    """True for "and then what" / "what else can i try", and not for a line naming a thing."""
    from . import repeat  # the ask patterns, kept off the import path

    line = " ".join(str(text or "").lower().split()).strip().strip(".,!")
    if not line or len(line.split()) > 7:
        return False
    if not repeat.NEXT_ASK.match(line):
        return False
    return all(word in NEXT_ASK_WORDS for word in words_of(line))


def next_step_ask_pool(text, memory):
    """The part of the answer after the step the bot just handed back, or None."""
    if not memory or not _asks_for_the_next_part(text):
        return None
    step = str(memory.get("handed_back_text") or "").strip()
    said = str(memory.get("handed_back_answer") or "")
    if not step or not said:
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    # Only the turn right after it: two turns on, the conversation has moved.
    if memory.get("handed_back_step") != len(turns) - 1:
        return None
    seen = set(memory.get("handed_back_seen") or [])
    more = _walk_answer(said, step, wrap=False)
    if not more:
        more = _the_first_step_left(said, seen, after=step)
    # The answer's line on keeping it right is handed back once. Asked again there is no next
    # part of the answer to give, and saying the same sentence with another lead on it is the
    # repeat this module exists to avoid.
    if not more or " ".join(more.lower().split()) == " ".join(step.lower().split()):
        return None
    from ..compose import pick

    reply = _as_a_lead(pick(NEXT_LEADS, memory, text), "", more)
    memory["handed_back_step"] = len(turns)
    memory["handed_back_text"] = more
    memory["handed_back_seen"] = list(seen | {_flat(more)})
    memory["handed_back_answer"] = said
    return [reply]


# A person and an animal are not a thing that is being tried. "my mum is in hospital" then "still
# there" is she is still there, and asking what happens "when you try" is wrong twice over: nobody
# is trying anything, and on a person it reads as though the worst line in the chat had not been
# heard. The same for "my dog is at the vet", "my dad had a stroke", "my wife is ill" and "the baby
# is not feeding", the last of which is the worst of them because the answer it replaced - stop and
# ask rather than push on - was the right one. So the point-at-it tail belongs to the speaker's own
# thing only, and a chat whose subject is somebody keeps the reply it had.
def _somebody_is_the_subject(memory):
    """True when the chat is about a person or an animal rather than the person's own thing."""
    from . import facts, named

    topic = (memory or {}).get("topic")
    if not isinstance(topic, dict):
        return False
    words = set(words_of(topic.get("text") or ""))
    words |= {str(word).lower() for word in (topic.get("words") or ()) if word}
    if not words:
        return False
    if words & set(facts.KIN) or words & set(named.PEOPLE_WORDS) or words & set(facts.PET_ANIMALS):
        return True
    # A person or an animal the chat has already named: "bella is at the vet" then "still there".
    user = (memory or {}).get("user") or {}
    names = set()
    for entry in user.get("pets") or ():
        if isinstance(entry, dict) and entry.get("name"):
            names.add(str(entry["name"]).lower())
    for entry in user.get("others") or ():
        if isinstance(entry, dict) and entry.get("name"):
            names.add(str(entry["name"]).lower())
        elif isinstance(entry, str):
            names.add(entry.lower())
    return bool(words & names)


def still_tail(text, memory):
    """The thing said again with "still" on it, or "".

    Two readings, both of them the chat's rather than the line's:

    * a state the chat has already named, which `the_still_state` reads - "still cold" after "my
      shower is cold", "it still clicks" after "the car cranks but will not start";
    * the thing said whole, with a word that only points at it: "still there" after a headache is
      the headache, and on its own it is the bot being asked whether it is there, which is why
      `still_going_on` wants an answer behind it.

    `the_still_state` drops a body and a feeling on purpose, and it drops the point-at-it words,
    so both are read here. What comes back is only used to keep a card for one word of the line
    from taking the turn away from the thing the chat is on.
    """
    state = the_still_state(text, memory)
    if state:
        return state
    line = " ".join(words_of(text))
    if not line or len(line.split()) > 6:
        return ""
    match = STILL_ONLY.match(line)
    if not match:
        return ""
    tail = match.group("tail").strip()
    if tail not in POINTS_AT_IT:
        return ""
    # The tail is the speaker's own thing: a chat about a person or an animal keeps its reply.
    if _somebody_is_the_subject(memory):
        return ""
    return tail


def a_card_is_not_the_answer(text, memory):
    """True when the card one word of this line belongs to must not answer it.

    `bot/modules/answers.py` asks this before it reads anything, because a card is opened by a
    single word and a line that is only the thing again carries that one word: "still cold" after
    "my shower is cold" found the common cold, "still freezing" after "my laptop keeps freezing"
    found the freezer. The thing the chat is on keeps the turn instead.

    A body and a feeling are the exception: "still tired" after the tiredness answer wants that
    answer's own advice, and the card for it is not a different subject. So a card is stepped back
    from only where the tail points at the thing, or where the chat is holding a thing at all.
    """
    tail = still_tail(text, memory)
    if not tail:
        return False
    if tail in POINTS_AT_IT:
        # "still there" is the thing only when there is an answer behind it: on its own it is
        # "are you there?", and that is a card of nobody's.
        return after_an_answer(memory)
    return names_a_thing(memory) or after_an_answer(memory)


def still_going_on(text, memory):
    """The pool for a line that is only the thing again with "still" on it, or None.

    `pool_for` already reads these lines, but only the modules that ask it do: a line of one
    word opened whatever card that word belongs to first ("still cold" the common cold, "still
    freezing" the freezer), and the reading never reached the person. The store answers it before
    any card is looked at, so the thing the chat is on keeps the turn.
    """
    tail = still_tail(text, memory)
    if not tail or buying(memory):
        return None
    if tail in POINTS_AT_IT:
        # "still there" is only the thing on the line before: on its own it is "are you there".
        if not after_an_answer(memory):
            return None
        # A body or a feeling is not a machine, so the question SAME_STILL asks - what happens
        # when you try it again - is the wrong one for a headache. It is still going on, and
        # that is the thing to ask about.
        if not names_a_thing(memory):
            return STILL_GOING_ON
    # A body or a feeling is not a thing with a next step of its own: "still tired" after the
    # tiredness answer wants that answer's own advice, and the store keeps out of it.
    elif not names_a_thing(memory):
        return None
    # Whatever the last turn was, the thing is still doing it, so a card for its one word - the
    # freezer, the common cold - is the reply that is certainly wrong. The store keeps out of
    # every line the report readers can carry: a trade to hand over, a step that carries on, the
    # end of the home fixes. Those lines are theirs, and they were answering them before this
    # reading existed. What is left is a line with no fix in hand ("Which things have you
    # tried?" is another shrug), and there the thing keeps the turn with the one question that
    # tells the two apart.
    pool = pool_for(text, memory)
    if pool is not None and pool is not ASK_WHAT_TRIED and pool is not SAME_STILL:
        return None
    return SAME_STILL


def reply_for(text, memory):
    """The reply to a line that is only the thing again with "still" on it, or None.

    Called from `bot.memory.not_this`, which is the reader the store already asks before any card
    is looked at: the thing the chat is on keeps the turn, and no card for the one word the line
    carries gets it. It lives here rather than in the store because the store is over the size the
    tools take, so this reading adds nothing to it.
    """
    from ..compose import pick

    pool = still_going_on(text, memory)
    if not pool:
        return None
    return pick(pool, memory, str(text or ""))


def pool_for(text, memory):
    """The pool the next step comes from, or None when the line is not a report on the answer.

    The caller picks from it, so nothing is said twice: the picker remembers what it has used,
    which matters here because these lines come in runs ("tried that" ... "and that").
    """
    care = in_care_pool(text, memory)
    if care:
        # A person of theirs is in a place of care and the line says they are still in it. The
        # readers below would read "still in hospital" as a state of a thing and ask what happens
        # when they try it again, so this is asked first.
        return care
    # `still_the_state` reads "still cold" after the shower; it deliberately drops a state that
    # is a body or a feeling, and it drops "still there", which is the thing said whole. Those
    # are read here so the report path stays shut and the store's own pool answers the line.
    if not (reads_as_not_worked(text) or still_the_state(text, memory)
            or still_tail(text, memory)) or not after_an_answer(memory):
        # The named step is read first: "ive tried the plunger" is not a report that the answer
        # failed, it is being partway through it, and the turn after it is the next step.
        step = next_step_pool(text, memory)
        if step:
            return step
        # The ask after a step the bot handed back out of the answer: "and then what" wants the
        # part that comes after it, not the answer's first step again.
        more = next_step_ask_pool(text, memory)
        if more:
            return more
        return None
    # A "then I did X and now it is worse" is only a report on a fix when the turn that was
    # answered was a problem or a how-to. After a recipe or a cleaning answer the same words are
    # about the dish or the mark ("and now its stuck" to the pan), and no trade belongs in that.
    report = " ".join(words_of(text))
    made_it_worse = bool(MADE_IT_WORSE.search(report) and POINTS_AT_THE_THING.search(report))
    if made_it_worse and not asks_for_a_fix(memory):
        return None
    # "that didnt help" about a purchase is a recommendation that was not to their taste: nothing
    # here has stopped working, so nothing is handed over and the line is answered as before.
    if buying(memory):
        return None
    # The question has been asked and the answer is "still the same": what is left to say is
    # that a home fix is the wrong place to keep looking.
    if asked_what_its_doing(memory):
        return END
    # A trade found in the person's own words is proof enough that the thing is theirs to fix.
    trade = trade_for(memory)
    if trade:
        if already_named(trade, memory):
            # Naming it twice is not a next step: the second report is a question about the
            # thing, not about who to ring.
            return ASK_NEXT
        return [lead.format(trade=trade) for lead in LEADS]
    # Without one, the "what is it doing now" question is only right when the turn that was
    # answered was a problem or a how-to. "whats a good film tonight" / "that didnt help" gets
    # nothing from here, because nothing about a film is "doing" anything.
    # A "still cold" line with no fix in hand is a report that the thing has not moved, and the
    # person has not said they tried anything: "my back hurts" then "still hurts" was handed
    # "Which things have you tried?" and nobody had tried anything. So the reply asks about the
    # thing itself and claims nothing about what has been done.
    state = the_still_state(text, memory)
    if state and not (asks_for_a_fix(memory) and has_evidence(text, memory)):
        return [line.format(state=state) for line in STILL_ASK]
    if not asks_for_a_fix(memory) or not has_evidence(text, memory):
        # A line that is only the thing again with "still" on it says the same problem is going
        # on, so it is not nothing: the person gets asked what has changed instead of another
        # card's reading of its one word ("still cold" is not a common cold). A body is not a
        # thing with a next step, so "still tired" keeps the answer it had.
        if still_tail(text, memory) and (still_tail(text, memory) in POINTS_AT_IT
                                        or names_a_thing(memory)):
            return SAME_STILL
        return None
    # "and now it is worse" has already said what the thing does, so asking "what is it doing
    # now" asks for the line back. Without a trade to hand over there is nothing to add here, and
    # the rest of the bot answers as it did.
    if made_it_worse and not (NOT_WORKED.search(report) or TRIED.search(report)):
        return None
    if not names_a_thing(memory):
        # Nothing in this chat is a thing that can be doing something, so there is no trade to
        # hand over and no "what is it doing now" to ask. Handing the answer back is the one
        # thing a friend never does with advice that has not worked, so ask what has been tried.
        return ASK_WHAT_TRIED
    return ASK_NEXT


# --------------------------------------------------------------------------------------------
# A person of theirs in a place of care.

# "my mum is in hospital" and then "still there" is about their mum, and nothing read it that
# way: the composer answered about itself ("Still here. What's up?"), "still the same" was handed
# the line for a machine that will not budge ("Time to change tack rather than try harder"), and
# "still in hospital" was read as a state of the thing and asked "What happens when you try it
# again - nothing at all, or something different?" - of somebody's mum. Nothing in that chat has
# not moved because a fix did not work; a person is still in, and the next thing a friend says is
# about them.
IN_CARE = re.compile(
    r"\b(?:in|at|on) (?:the |a |an )?(?:hospital|infirmary|hospice|care home|nursing home|"
    r"residential home|ward|icu|itu|hdu|a&e|ae|rehab|clinic)\b"
)
# The people whose words settle which pronoun the answer uses. A person the words do not settle
# is "they", which is the same word for one person and for several.
SHE = frozenset("""mum mam mummy mom mother mummy nan nana gran granny grandma grandmother
                   nanny daughter sister wife aunt auntie girlfriend niece""".split())
HE = frozenset("""dad daddy father grandad granddad grandpa grandfather son brother husband
                  uncle boyfriend nephew""".split())
# What a bare "still ..." line can say about a person who is in: they are still in there, still
# the same, still not home. Every other word would make the line about something else.
STILL_ABOUT_A_PERSON = frozenset("""there the same in now hospital ward home out yet better
                                    no not like that doing it again care""".split())
# Words that point at the person rather than naming a new subject, allowed in front of "still".
POINTING = frozenset("""it its it's she she's he he's they they're theyre that theres there's and
                        but so is are was were s""".split())

IN_CARE_ASK = (
    "Still in, then. How is {subj} doing today?",
    "No change yet, then. How has your {word} been today?",
    "Still there. The waiting is the worst of it, and no news is not bad news.",
    "Still in, then. Has anyone there said what happens next?",
    "Still in. How are you doing with all of it?",
    "Still in, then. Did you get to see {obj} today?",
)
# The same answer when the place of care is named and nobody is: "im at the hospital with mum" and
# "my partner is in hospital". There is no word for who they are, so the pool says "they" itself
# rather than filling {subj} into "How is they doing today?".
IN_CARE_ASK_UNNAMED = (
    "Still in, then. How are they doing today?",
    "No change yet, then. How have they been today?",
    "Still there. The waiting is the worst of it, and no news is not bad news.",
    "Still in, then. Has anyone there said what happens next?",
    "Still in. How are you doing with all of it?",
    "Still in, then. Did you get to see them today?",
)
IN_CARE_SELF = (
    "Still in, then. How are you doing today?",
    "Still in. Is someone bringing you the things you need?",
    "Still in, then. Has anyone said how long they're keeping you in?",
)


def _the_person_word(token):
    """The person the word names ("mum", "dad"), or "" for a word that names nobody."""
    word = token[:-2] if token.endswith("'s") else token
    if word.endswith("s") and word[:-1] in SHE | HE:
        word = word[:-1]
    return word if word in SHE or word in HE else ""


def _a_report_on_a_person(text):
    """True when the line is only "still" and pointing words: "still there", "still the same",
    "still in hospital", "she's still in". A line with a word of its own is a new subject and is
    left to the readers that know it."""
    said = " ".join(words_of(text))
    tokens = said.split()
    if not tokens or len(tokens) > 6 or said.endswith("?"):
        return False
    if "still" not in tokens:
        return False
    at = tokens.index("still")
    after = tokens[at + 1:]
    return bool(after) and all(word in STILL_ABOUT_A_PERSON for word in after) \
        and all(word in POINTING for word in tokens[:at])


def _in_care(memory):
    """(the person as "your mum" wants it, subject, object) for the person in a place of care, or
    None.

    The person's own lines only, newest first, and not the line being answered: the place of care
    is something they said, not something an answer said, because a card about a broken wrist can
    say "hospital" and send "still there" to a stranger's stay.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    # The line being answered is not in the history yet, so every line here is an earlier one.
    # Six turns back, because the reports come in runs ("still there", "still the same") and the
    # line that named the person is at the head of them, and a line that names a thing a home fix
    # is about is where the scan stops: the chat has moved to an appliance and "still there" is
    # about that, not about the person three turns ago.
    lines = [t.get("user") for t in turns][-6:]
    for line in reversed([l for l in lines if l]):
        said = " ".join(words_of(line))
        if any(_names(set(said.split()), said, entry_words) for entry_words, _, _ in TRADES):
            return None
        if not IN_CARE.search(said):
            continue
        with_someone = re.search(r"\bwith\s+(?:my\s+|our\s+|the\s+)?([a-z']+)", said)
        person_with = _the_person_word(with_someone.group(1)) if with_someone else ""
        if not person_with and with_someone:
            # "with my partner" and "with my friend" name a person with no pronoun to fix, so
            # `_the_person_word` gives nothing and the line fell back to the patient reading - the
            # fault this branch is here to fix, two lines further on. A `with` clause that names a
            # person at all is not the user being the patient.
            word_with = with_someone.group(1).rstrip("'s")
            if word_with in A_PERSON or word_with.rstrip("s") in A_PERSON \
                    or word_with in PEOPLE_AGED:
                return ("", "they", "them")
        if person_with:
            # "im at the hospital with mum" is about the mum, not about the person sitting in the
            # waiting room: the self reading answers it "How are you doing today?", which is the
            # one thing they are not asking about.
            return (person_with, "she" if person_with in SHE else "he" if person_with in HE else "they",
                    "her" if person_with in SHE else "him" if person_with in HE else "them")
        if re.search(r"\bi(?:'?m| am)\b.*\bin\b", said) or re.match(r"^im\b", said):
            return ("", "you", "you")
        for word in said.split():
            person = _the_person_word(word)
            if person:
                subj = "she" if person in SHE else "he" if person in HE else "they"
                obj = "her" if subj == "she" else "him" if subj == "he" else "them"
                return (person, subj, obj)
        # The place is named and no person is: "im at the hospital with mum" is still about
        # somebody, and the answer can ask about them without a word for who they are.
        return ("", "they", "them")
    return None


def in_care_pool(text, memory):
    """The lines that answer a bare "still ..." about a person of theirs who is in a place of
    care, or None for every other line."""
    if not memory or not _a_report_on_a_person(text):
        return None
    found = _in_care(memory)
    if not found:
        return None
    word, subj, obj = found
    if not word:
        if subj == "you":
            return IN_CARE_SELF
        return IN_CARE_ASK_UNNAMED
    filled = tuple(line.format(subj=subj, obj=obj, word=word) for line in IN_CARE_ASK)
    # A line that still prints a brace is a line with a word in it this branch cannot fill. Nothing
    # can reach it now - the unnamed branch has its own pool - and this is what keeps a pool that
    # grows a fourth placeholder from reaching a person.
    return tuple(line for line in filled if "{" not in line and "}" not in line) or IN_CARE_ASK_UNNAMED
