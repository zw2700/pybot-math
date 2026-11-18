"""Somebody else's habit, said out loud, with nothing else in the line.

This is the fallback's fallback. The repository's floor is three lines that fit any message
("Got it. Is there anything you'd like a hand with?"), and on main a person who has just
described the thing that wears them down is asked whether there is anything they would like a
hand with - which is the one thing the line has just told you.

    my brother keeps asking me for money        the neutral nod
    my son keeps leaving his shoes in the hall  the neutral nod
    my mate never invites me to anything        the neutral nod
    my boss keeps moving the goalposts          the neutral nod
    my partner keeps criticising me             the neutral nod

The composer already has a pool for this shape (`GRIEVANCE` in `bot/compose/fallback.py`), and it
reaches the lines whose verb is in its list - borrows, cancels, criticises, rings. What it misses
are the two commonest ways a person says it: *imposition* ("asks me for money", "asks me to
babysit", "uses my toothbrush", "leaves her dishes in the sink") and *neglect* ("never invites me",
"never thanks me"). Both are the same complaint - the other person keeps doing something and the
speaker is the one paying for it - so they are read here, and the reply is the only help a
fallback can honestly give for them: not a fact about the world, but the words to raise it.

The reply says the one thing that is true of every one of these lines, because it is the thing
people get wrong: say it once, about the pattern rather than the last time, and ask for the one
change you want by name. STYLE.md's "Not knowing, honestly" is the shape - the bot cannot see the
brother or the hall, so it does not pretend to know what happened; it hands over the sentence.

Two rules keep it away from everybody else's turns:

- `bot/modules/greeting.py` only asks this when the reply it already has is one of the pools that
  means nothing was answered (`fallback._is_a_hedge`, or one of the three NEUTRAL lines), so a
  line any entry or module answered never reaches here and cannot change;
- reading is narrow on purpose. There has to be a person in the line ("my son", "the boss"), the
  line has to say it *keeps* happening, and one of the shapes below has to be in it. Everything
  else - a body, an illness, a harm, a child's sleep, a pet, a good thing - stands down and keeps
  the reply it had, because those want a different answer and other modules know them.

Not every line this file can read is one it gets the turn on, and that is the gate doing its job:
`my childminder keeps cancelling` is read as an arrangement they keep breaking, but the reply it
already has is the composer's "Ugh, those are fiddly. How long has it been like that?", which is
neither a hedge nor a nod, so it keeps its turn. When a line here is measured, measure what the
bot says, not what `answer_for` returns.
"""
import re

from . import pick

# The people a person can raise something with. Named the way people type them, and a spouse or
# a flatmate is here because "my husband keeps leaving the lights on" is the same complaint as
# "my flatmate keeps eating my food".
PEOPLE = (
    "mum", "mom", "mother", "dad", "father", "parent", "parents", "sister", "brother",
    "partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee", "flatmate",
    "housemate", "roommate", "landlord", "landlady", "boss", "manager", "colleague", "coworker",
    "co-worker", "teammate", "team mate", "workmate", "neighbour", "neighbor", "son", "daughter",
    "kid", "child", "children", "friend", "mate", "nan", "nana", "gran", "granny", "grandma",
    "grandad", "grandpa", "aunt", "uncle", "cousin", "ex", "stepson", "stepdaughter", "stepdad",
    "stepmum", "mother-in-law", "father-in-law", "brother-in-law", "sister-in-law",
    "daughter-in-law", "son-in-law", "in-laws", "household", "family",
    # Somebody paid to turn up has a habit too, and a cancelled childminder is the same complaint
    # as a mate who bails. These are the ones people name in a line like this.
    "childminder", "babysitter", "nanny", "carer", "cleaner", "hairdresser", "tutor",
    # The same complaint is said of a houseful more often than of one person: "the kids keep
    # leaving their toys everywhere" is how people type it. These have no separate singular here
    # because the plural is the whole point of them.
    "twin", "grandkid", "boy", "girl", "lad", "relative", "sibling", "stepkid",
)
PEOPLE_SET = frozenset(PEOPLE)
# A plural is the same person, and it is the commoner way to say it. `s` covers kids, mates,
# friends, brothers and twins; `es` covers bosses, exes and in-laws.
A_PERSON = re.compile(r"\b(?:my|our|the)\s+(?:[a-z-]+\s+){0,2}?(?:" + "|".join(PEOPLE) + r")(?:s|es)?\b")
# "somebody", "someone", "people" name the other party without naming them, and they are used for
# exactly this: "someone keeps parking in my space". A vague "they" is not enough - "they keep
# cancelling my trains" is the railway, and there is nothing to raise with a timetable.
SOMEONE = re.compile(r"\b(?:someone|somebody|people|everyone|everybody)\b")

# It happens again, said any of the ways people say it.
RECURS = re.compile(
    r"\b(?:keeps?|kept|always|never|constantly|continually|forever|again and again|"
    r"every (?:single |blessed )?(?:day|night|morning|week|weekend|time|month)|"
    r"all the time|time after time|over and over|wont stop|won'?t stop|doesnt stop|"
    r"doesn'?t stop|never stops)\b")

# What one person does *to* the other: the verb takes "me" or "us" as its object, with at most
# one small word between them ("asks me", "asks me for money", "picks on me", "complains about
# me"). This is the imposition reading, and it is a shape rather than a list of complaints, so
# "asks me to babysit", "invites me", "tells me how to drive" and "criticises me" are one
# reading. The object has to come straight after the verb: "keeps asking to read to me" is a
# child asking to do something for the speaker, which is not an imposition, and a wider window
# around the verb caught it.
DONE_TO_ME = re.compile(
    r"\b(?:ask|asks|asked|asking|tell|tells|told|telling|invite|invites|invited|inviting|"
    r"thank|thanks|thanked|thanking|owe|owes|owed|blame|blames|blamed|criticis\w*|criticiz\w*|"
    r"interrupt|interrupts|interrupted|interrupting|nag|nags|nagged|nagging|moan|moans|moaned|"
    r"complain|complains|complained|ring|rings|ringing|rang|call|calls|calling|called|text|"
    r"texts|texted|texting|message|messages|messaged|messaging|phone|phones|phoned|phoning|"
    r"lecture|lectures|lectured|lecturing|mock|mocks|mocked|belittle|belittles|belittled|"
    r"ignore|ignores|ignored|ignoring|talk|talks|talked|talking|shout|shouts|shouted|shouting|"
    r"yell|yells|yelled|yelling|complain|moan|pick|picks|picked|picking)\b"
    r"(?:\s+[a-z]+)?\s+(?:me|us)\b")
# The ask that wants something: "asks me for money", "asks me to babysit". Split out from
# DONE_TO_ME because the words for it are about deciding a line, not about a row.
ASK_FOR = re.compile(r"\b(?:ask|asks|asked|asking)\s+(?:me|us)\s+(?:for|to)\b")
# The verb that says the not-asking: "never invites me", "never asks me along", "leaves me out".
NOT_ASKED = re.compile(
    r"\b(?:never|doesn'?t|doesnt|don'?t|dont|won'?t|wont|not)\b[^.?!]{0,26}?\b(?:"
    r"invit\w*|includ\w*|asks? me|ask me|asked me|picks? me|picks? up|leaves? me out|"
    r"left me out)\b")
# The same shape about being taken for granted: "never thanks me", "never notices", "doesn't
# listen". A wish to be appreciated is a different thing to say from a wish to be included.
UNSEEN = re.compile(
    r"\b(?:never|doesn'?t|doesnt|don'?t|dont|won'?t|wont|not)\b[^.?!]{0,26}?\b(?:"
    r"thank\w*|notic\w*|appreciat\w*|listen\w*|consider\w*|repl\w*|respond\w*|"
    r"visits?|visit me|talks? to me|talked to me)\b")
# "never helps" is the household-work complaint, and the answer for it is a named job rather than
# a word about being included.
NOT_HELPED = re.compile(
    r"\b(?:never|doesn'?t|doesnt|don'?t|dont|won'?t|wont)\b[^.?!]{0,26}?\b(?:helps?|helping|"
    r"pulls? (?:his|her|their) weight|does (?:his|her|their) share)\b")
# The speaker's own things in the way, which is the taking reading: "uses my toothbrush",
# "borrows my clothes", "takes my parking space".
MY_THING = re.compile(
    r"\b(?:borrow|borrows|borrowed|borrowing|take|takes|took|taking|use|uses|used|using|"
    r"nick|nicks|nicked|nicking|eat|eats|ate|eating|drink|drinks|drank|drinking|spend|spends|"
    r"spent|spending|wear|wears|wearing|wore|hide|hides|hid|hoard|hoards|fill|fills|filled|"
    r"move|moves|moved|break|breaks|broke|break|throw|throws|threw|smash|smashes)\b"
    r"[^.?!]{0,20}?\b(?:my|our)\b")
# A shared room the mess lands in. "leaves her toys everywhere" is the same complaint as "leaves
# his shoes in the hall", and neither has a verb that takes "me".
MESS = re.compile(
    r"\b(?:everywhere|all over|all over the place|lying around|left around|in the way|"
    r"in (?:my|our) way|in the (?:hall|hallway|kitchen|sink|living room|lounge|bathroom|bath|"
    r"bedroom|fridge|bin|garden|yard|car|sofa|cupboard|garage|utility|passage|porch)|"
    r"on the (?:floor|table|sofa|bed|counter|stairs|side)|up the stairs|on the stairs|"
    r"out the front|outside the front|in the passage)\b")
# How the speaker says it gets to them. Somebody who says "it drives me mad" has already told
# the bot it is a complaint, whatever the verb was.
STRAIN = (
    "drives me mad", "drives me nuts", "drives me crazy", "drives me insane",
    "drives me up the wall", "does my head in", "does my nut in", "gets to me", "getting to me",
    "winds me up", "wound me up", "it annoys me", "annoys me", "annoying me", "sick of",
    "fed up", "cant stand", "can't stand", "wearing me down", "wears me down", "worn me out",
    "wears me out", "boils my blood", "grates on me", "had enough of", "draining me",
)
# The person is being told off rather than asked for something: "criticises me", "comments on my
# weight", "puts me down", "picks on me". Said once, plainly, is the answer.
CRITICISED = re.compile(
    r"\b(?:criticis\w*|criticiz\w*|comment\w*|picks? on|picked on|picking on|puts? me down|"
    r"putting me down|makes? fun of|made fun of|moan\w*|complain\w* about|lectur\w*|"
    r"tells? me how|tells? me what|remind\w* me|nag\w*|judge\w*|belittl\w*|mocks?|mocked|"
    r"rubs? it in)\b")
CRITICISED_MY = re.compile(
    r"\b(?:my|our)\s+(?:[a-z]+\s+){0,2}?(?:weight|looks?|cooking|house|parenting|driving|job|"
    r"money|hair|clothes|lifestyle|accent|english|kids?|children|body|figure|age)\b"
    # "criticising how i look" names what the comment is about without a possessive, and it
    # reached the neutral nod while "criticising my cooking" was answered.
    r"|\b(?:how|the way)\s+(?:i|we)\s+(?:look|dress|speak|talk|walk|eat|spend|parent|drive)\b")
# An arrangement the other person keeps pulling out of: a childminder who cancels, a mate who
# bails, a driver who drops out. Nothing is being taken from the speaker and nothing is said
# about them, so none of the shapes above reads it and it reached the neutral nod.
BAILS = re.compile(
    r"\b(?:cancel\w*|cancell\w*|bails?|bailed|bailing|pulls? out|pulled out|pulling out|"
    r"drops? out|dropped out|dropping out|lets? me down|let me down|letting me down|"
    r"messes? me about|messing me about|mess(?:es)? me around|messing me around|"
    r"not turn(?:ing)? up|doesn'?t turn up|didn'?t turn up|"
    r"stands? me up|stood me up|no[- ]?shows?|no[- ]?showed|changes? (?:the|our) plans?)\b")
# The same reading said as a no: "she never cancels", "he never lets me down" is good news.
KEEPS_THE_ARRANGEMENT = re.compile(
    r"\b(?:never|doesn'?t|doesnt|don'?t|dont|won'?t|wont)\b[^.?!]{0,20}?\b(?:cancel\w*|"
    r"cancell\w*|bails?|lets? me down|stands? me up|no[- ]?shows?|late|brings? (?:it|that) up)\b")
# The affirmative of that: a keeps/always habit said about inclusion or thanks, which is good
# news rather than an imposition. ASK_FOR is excepted so "my brother keeps asking me for a lift"
# and "my son keeps asking me to play" keep the ask reading they have.
ALWAYS_DOES_IT = re.compile(
    r"\b(?:keeps?|kept|always|constantly|continually|every\s+(?:single\s+)?(?:day|week|time))\b"
    r"[^.?!]{0,26}?\b(?:invit\w*|includ\w*|thank\w*|say\w*\s+thank\w*|"
    r"ask(?:s|ing)? me (?:over|round|out|along|to)\b"
    r"|asks? after me\b)")
# Which of the two good habits it is: being thanked, or being included.
THANKED = re.compile(r"\bthank\w*|\bthank you\b|\bsays?\s+(?:a\s+)?thank")
# The courtesy itself, whatever its frequency: "thanks me every time", "invites me over every
# sunday". Said with the frequency after the verb it missed ALWAYS_DOES_IT, which wants the
# frequency first, and fell through to the criticism pool - a child who always says thank you was
# told to answer flatly and warmly, "I'm not changing it".
COURTESY = re.compile(r"\b(?:thank\w*|invit\w*|includ\w*|asks? me (?:over|round|out|along))\b")
# A courtesy that is denied, or that comes with something wrong, is not good news: it is the
# neglect, the bail or the complaint pool, and those are read below.
COURTESY_DENIED = re.compile(
    r"\b(?:never|not|doesn'?t|doesnt|don'?t|dont|won'?t|wont|hardly|rarely|only when)\b")
# A thank-you, or any courtesy, with no meaning behind it: "but never means it", "doesn't really
# mean it". The rest of the line does not get a look, because no other reading of it is right.
NOT_SINCERE = re.compile(
    r"\b(?:never|doesn'?t|doesnt|didn'?t|didnt|don'?t|dont|won'?t|wont|not)\s+"
    r"(?:really\s+|ever\s+|actually\s+|truly\s+)?mean(?:s|t)?\s+(?:it|a word of it)\b")
# An ask that is really an invitation: "keeps asking me to dinner" is the same good news as
# "keeps inviting me round", while "keeps asking me to babysit" is still the ask pool. The
# difference is whether the thing asked is shared with the person asking.
A_SHARED_OCCASION = re.compile(
    r"\bask(?:s|ing)? me (?:to |round for |over for )?(?:dinner|lunch|supper|tea|a meal|a drink|"
    r"drinks|a party|a barbecue|a bbq|a picnic|a night out|a wedding|a do)\b")
# Time is the thing they keep getting wrong, and "turning up late" names it without saying
# "me": "my mate keeps turning up late", "the driver is always late".
ARRIVES_LATE = re.compile(
    r"\b(?:turns? up late|turning up late|shows? up late|showing up late|arriv\w* late|"
    r"arrives? late|always late|never on time|keeps? me waiting|every time we meet| timekeeping)\b")
# A subject they will not leave alone: "goes on about her ex", "keeps bringing it up".
GOING_ON = re.compile(
    r"\b(?:goes? on about|going on about|goes? on and on|going on and on|keeps? on about|"
    r"bangs? on about|"
    r"harks? on about|keeps? bringing (?:it|that) up|brings? (?:it|that) up|"
    r"wont drop it|won'?t drop it|never drops it)\b")
# A habit of a mailbox rather than of a person: "keeps replying all", "copies in the whole team".
EMAIL_HABIT = re.compile(
    r"\b(?:reply(?:ing|ies)? all|replies all|cc'?s? (?:everyone|the whole|us all)|"
    r"copies? (?:in )?(?:everyone|the whole team|the lot)|forwarding everything|"
    r"forwards everything)\b")
# Work is its own answer, because the thing you can point at there is a written record rather
# than a feeling, and the person has a lever the rest of the pools do not mention.
WORK_PEOPLE = frozenset(("boss", "manager", "colleague", "coworker", "co-worker", "teammate",
                         "team mate", "workmate"))
WORK_WORDS = ("goalpost", "goal", "goals", "deadline", "rota", "shift", "1:1",
              "one to one", "one-to-one",
              "meeting", "brief", "priority", "priorities", "workload", "target", "overtime",
              "annual leave", "holiday", "pay rise", "promotion", "review", "appraisal",
              "micromanage", "micromanaging", "email", "inbox", "projects?")
# A body, an illness, a harm or a child's care is a different answer, and other modules have it.
NOT_THIS = frozenset((
    "fall", "falls", "falling", "fell", "fallen", "cough", "coughs", "coughing", "cold", "flu",
    "sick", "ill", "unwell", "pain", "pains", "hurt", "hurts", "hurting", "ache", "aches",
    "dizzy", "faint", "fainting", "forget", "forgets", "forgetting", "forgot", "memory",
    "confused", "dementia", "alzheimers", "alzheimer's", "hospital", "doctor", "gp", "nurse",
    "tablets", "medication", "medicine", "chemo", "cancer", "stroke", "operation", "surgery",
    "bleed", "bleeding", "blood", "bruise", "bruises", "lump", "rash", "fever", "vomit",
    "vomiting", "hospital", "hit", "hits", "hitting", "punch", "punches", "kick", "kicks",
    "slap", "slaps", "grabbed", "grabs", "touched", "touches", "touching", "threaten",
    "threatens", "threatened", "abuse", "abusive", "bullies", "bullying", "bullied",
    "drunk", "drinks", "smokes", "smoking", "suicide", "suicidal", "self harm", "kill",
    "starving", "anorexic", "depressed", "depression", "anxious", "anxiety", "panic",
    # A course of care being missed is not an arrangement to renegotiate: somebody cancelling
    # their therapy or their appointments needs the health answer, not a line about notice.
    "therapy", "therapist", "counselling", "counseling", "appointment", "appointments",
))
# A child's night, a pet, or something the person is pleased about is not a grumble.
NOT_A_GRUMBLE = frozenset((
    "waking", "wakes", "woke", "sleep", "sleeps", "sleeping", "crying", "cries", "cried",
    "nappy", "nappies", "feeding", "feeds", "tantrum", "tantrums", "teething", "barking",
    "barks", "howling", "scratching", "litter", "bites", "biting", "chewing", "jumping up",
    "soiling", "weeing", "pooing",
))
# A child going on about something is enthusiasm, not a grievance: "my son keeps going on and on
# about minecraft" is not a subject to be closed. A child is still read for the asks, the mess and
# the things taken.
CHILD_PEOPLE = frozenset(("son", "daughter", "kid", "child", "children", "stepson",
                          "stepdaughter", "teenager", "teenagers", "toddler", "baby"))
GOOD_WORDS = frozenset((
    "nicely", "kindly", "sweet", "lovely", "proud", "funny", "jokes", "joking", "hilarious",
    "thoughtful", "supportive", "helpful", "amazing", "brilliant", "wonderful", "affectionate",
    "cuddly", "cuddles",
))


ASKED = (
    "Decide your line before the next ask rather than in the moment, and make it one sentence: "
    "what you can do and what you can't. 'I can do Saturday, but not every Saturday' is a thing "
    "somebody can plan around, and you don't owe a reason.",
    "Say it once, calmly, and make it about the thing rather than the person: 'I'd rather you "
    "asked me first.' One clear line lands where a hint does not, and it is kinder than going "
    "quiet about it.",
    "Give them an answer they can work with: what you can do, and what you can't. 'I can help "
    "with the school run, but I can't lend money again' is a line somebody can plan around.",
)
TAKEN = (
    "Make it one rule rather than one row, said once and warmly the next time they ask: 'of "
    "course, if it's back by Sunday.' A rule they agree to is easier to hold than a complaint "
    "about the last time.",
    "Ask before the next time rather than after: 'can we agree I'm asked first, even if the "
    "answer is going to be yes?' It costs nothing when they would have asked anyway.",
    "Keep the two or three things you actually mind out of reach and let the rest go. Then the "
    "one sentence - 'anything of mine, just ask' - covers the lot without a list of every time.",
)
MESSY = (
    "Give the thing one place to go rather than asking for tidiness in general: 'the shoes live "
    "in the cupboard by the door.' A named place is something a person can do; 'clear up after "
    "yourself' is not.",
    "Ask for the one job, once, at a calm moment - 'can the dishes go in the dishwasher before "
    "bed?' - rather than for a change in character. One job named is one job done.",
    "Say it as the house rule rather than as a complaint about them: 'in this house the boots "
    "come off at the door.' A rule is easier to hear than a list of the times they didn't.",
)
LEFT_OUT = (
    "Say it once, plainly, as a wish rather than an accusation: 'I'd love to be asked next time, "
    "even at short notice.' People often don't know they've left somebody out, and one sentence "
    "is usually enough.",
    "Ask for the next one rather than for the reason: 'can I come to the next one?' A straight "
    "yes or no tells you more than any hint will, and it is easy for them to say yes to.",
    "Worth saying out loud once - 'I've noticed I don't get asked any more, and it does get to "
    "me' - and then letting them answer. The answer is the useful part, whatever it is.",
)
TAKEN_FOR_GRANTED = (
    "Say what you would like noticed rather than what they didn't do: 'a thanks when I've done "
    "the shopping would go a long way.' People often don't know which bit you want acknowledged, "
    "and a thing named is something they can do.",
    "Ask for it once, plainly and without a score kept: 'it would help if you said when it's "
    "good.' Then notice it when it comes, because the thanks you asked for is the one they are "
    "learning to give.",
    "Worth saying what the effect is, once: 'I do a lot round here and it goes unnoticed, and "
    "that is what wears me down.' It is easier to hear than 'you never thank me'.",
)
CRITICISED_LINES = (
    "Say it once, about one thing, in the moment: 'please don't comment on that - it isn't "
    "helping.' You don't have to justify it, and not liking it is reason enough.",
    "Name the thing and the effect in one sentence - 'when you say that, I stop wanting to tell "
    "you things' - and leave it there. It is a statement, not an argument to win.",
    "Answer flatly and warmly the first time, then give the same short answer every time after: "
    "'I heard you, and I'm not changing it.' Repetition is what ends it, not a better argument.",
)
WORK_LINES = (
    "Get it in writing and ask what moved: 'just to confirm, it's Tuesday now - what changed?' "
    "A written thread is what you can point at the next time it shifts, and it costs one email.",
    "Ask what moved and what comes off instead of why it moved: 'if this is the new priority, "
    "what drops?' That hands the choice to the person who can actually make it.",
    "Raise it once, at the end of a meeting, in plain words: 'when the plan changes twice a week "
    "I lose time on the rest.' Say what it costs you, not that it is annoying.",
)
CREDIT_LINES = (
    "Say what you did, in one sentence, in the room where it comes up: 'I did the analysis behind "
    "that.' Credit follows a clear claim, and the quiet hope that somebody notices is what leaves "
    "it with them.",
    "Ask for the part you want named rather than the whole thing: 'can the write-up say who did "
    "what?' It is a small, reasonable request, and it is much easier to say yes to than a row "
    "about taking credit.",
    "Keep a short note of what you did and when - not to send to anyone, but so you can say it "
    "plainly the next time it matters. Then say it once, warmly and without the charge: 'that was "
    "mine, and I'd like that known.'",
)
# The affirmative of KEEPS_THE_ARRANGEMENT: a habit that is good news. "my friend keeps inviting
# me round", "my mum always thanks me", "my sister keeps inviting me to things". The inclusion and
# appreciation verbs are in DONE_TO_ME, so with RECURS on them the line landed in the criticism or
# the answer-flatly pool - advice on how to shut somebody down, handed to a person who was being
# looked after. Nothing is wrong here, so the reply names the habit back and gives the one thing
# worth doing with it: saying it out loud, once.
#
# Being thanked and being included are two different good habits and one set of words cannot serve
# both - "you always think to ask me" is the wrong thing to say to somebody who says thank you -
# so the pool is picked from the verb in the line.
GOOD_HABIT_APPRECIATED = (
    "That is rarer than people think, and worth saying out loud once: 'I noticed you always say "
    "thank you, and it makes a difference.' People hear the complaint version far more often than "
    "the good one.",
    "It is worth naming to their face rather than just enjoying: 'you always notice, and I "
    "appreciate it.' A thank-you that goes unmentioned tends to stop, because nobody can tell it "
    "landed.",
    "Say it back in the same plain way, in the moment: 'I appreciate that you always think to say "
    "it.' One sentence is the whole of what it takes.",
)
GOOD_HABIT_INCLUDED = (
    "That is a good habit to be on the receiving end of, and worth naming to their face: 'I "
    "noticed you always think to ask me.' People rarely hear the good version of a habit, and it "
    "is usually never said.",
    "Say yes, and say why once: 'I like that you always think to include me.' The person who keeps "
    "asking is usually the one who never gets told that it lands.",
    "Enjoy it and say so in the moment rather than leaving it as a thing you only notice - 'I "
    "noticed, and I'm glad of it.' It costs nothing and it usually lands better than people "
    "expect.",
)
GOOD_HABIT = GOOD_HABIT_APPRECIATED + GOOD_HABIT_INCLUDED
# A courtesy that carries no meaning: "my sister thanks me but never means it", "he thanks me
# but doesn't mean it". The words are there and the thing behind them is not, so the words to say
# about a comment on how you look are the wrong answer - and so is calling it a good habit, which
# is what the affirmative reading would do with the same verb. The reply weighs what they do
# against what they say, and asks for the doing instead of the words.
WORDS_NOT_MEANT = (
    "Weigh what they do against what they say, because a thank-you nobody means is the cheapest "
    "thing there is to give. If nothing else in it matches the words, stop going out of your way "
    "for a while and see what they notice.",
    "Say the plain version once, without heat: 'I'd rather you said nothing than said it out of "
    "habit.' Either answer tells you more than the words did.",
    "Ask for the thing rather than the words: 'it would mean more if you helped with it than if "
    "you thanked me for it.' Somebody who won't do the thing has told you what the words are "
    "worth.",
)

RAISE = (
    "Say it once, at a calm time, about the pattern rather than today: 'this keeps happening and "
    "it's starting to get to me - can we sort it?' Name the thing they do and the one change you "
    "want; a list of every time turns it into a row.",
    "Raise it early rather than on the tenth time, and ask for the one change you actually want. "
    "'I'd rather you asked first' is something a person can act on; 'stop it' is not.",
    "Worth one plain sentence to them, said warmly and once. People can act on a request - 'can "
    "we agree the boots go by the door?' - not on a sigh.",
)
BAILING = (
    "Say it plainly once, and name the pattern rather than the last time: 'you've cancelled three "
    "times now and it leaves me stuck - can we agree a week's notice?' Then say what you will do "
    "if it happens again, and do that.",
    "Put a fallback in place before the next time, so the cost lands on them rather than on you: a "
    "backup for the childcare, somebody else who can drive, a plan that does not need them to turn "
    "up. Nothing about this changes until cancelling costs them something.",
    "It is fair to ask why, once: 'is something making it hard at the moment?' If there is a "
    "reason you can both work with, say what would help; if there is not, it is worth saying the "
    "arrangement no longer works for you.",
)
LATE_LINES = (
    "Agree the time out loud, then say what happens if it slips: 'if you're not here by seven I'll "
    "start without you.' A consequence you actually keep is what changes a habit; being annoyed "
    "on the night does not.",
    "Say it once, without the sarcasm, in the calmest voice you have: 'when you're late it means I "
    "am waiting, and I'd rather we set a time we both mean.' Then stop being the person who waits "
    "quietly.",
    "Ask for a message rather than for punctuality, because it is the waiting that costs you: 'if "
    "you'll be more than ten minutes, text me.' That is easy to say yes to, and it gets you the "
    "thing you actually wanted.",
)
SUBJECT_AGAIN = (
    "Ask what they want from the conversation: 'when you bring it up, is there something you want "
    "me to say?' Somebody who goes over the same ground is usually after an answer they have not "
    "had yet, and naming that ends it quicker than changing the subject.",
    "Say where the line is once, in a warm voice: 'I've said all I can about that one - I'd rather "
    "talk about something else tonight.' Then steer, gently, to something you both enjoy.",
)


# --- the second turn -------------------------------------------------------------
# Once the bot has offered the words, the person often answers with how the saying went, that it
# is every day, or with a doubt about their own reaction. Those follow-ups name the person only
# as "he", "she" or "they", and on main they got the placeholder again ("I'm listening - say more
# if it helps") or their own words back ("Got it - it's every single day"). The thread is open in
# the last bot line, so the person does not have to be named a second time.
AFTER_A_SAYING = (
    "went quiet", "didnt say anything", "didn't say anything", "said nothing", "got annoyed",
    "got defensive", "got funny", "got upset", "shrugged", "laughed it off", "laughed",
    "said sorry", "said they were sorry", "agreed", "promised", "said ok", "said okay",
    "didnt listen", "didn't listen", "ignored it", "did it again", "kept doing it",
    "went mad", "kicked off", "stormed off", "hung up", "walked off", "denied it",
)
THE_SAYING = (
    "i said", "i told", "i asked", "ive said", "i've said", "ive told", "i've told",
    "i explained", "i mentioned", "i brought it up", "i tried", "i texted", "i wrote",
)
ALWAYS_COUNT = (
    "every single day", "every single time", "every day", "every time", "all the time",
    "constantly", "again and again", "over and over", "non stop", "non-stop", "daily",
    "every week", "every night", "without fail", "for years", "so often",
)
SELF_DOUBT = (
    "am i overreacting", "am i being too sensitive", "am i being sensitive",
    "am i over thinking", "am i overthinking", "am i being unreasonable", "is it me",
    "should i just give up", "should i give up", "am i mad", "am i wrong to",
    "is that normal", "am i being daft", "am i being silly", "too sensitive",
)
# The other way round: a complaint about the person themselves, handed over as what somebody
# says about them ("my partner says I'm never really there"). The line to shut a criticism down
# is the wrong answer here - they are the one being criticised - so this shape gets its own
# words: hear the grain of truth, ask for one example, say what you would like instead.
ABOUT_ME = (
    "Ask for one example with a time and a place - 'when was the last time?' - instead of "
    "arguing about all of you. A real instance tells you what to change; a verdict does not.",
    "Take the grain of truth and say what you would like instead: 'you're right that I've been "
    "on my phone at dinner - I'll put it down.' That ends it faster than a defence does, and it "
    "does not mean agreeing with all of it.",
    "Ask what they would like more of rather than whether they are right: 'what would a good "
    "evening look like for you?' That is a question with an answer, and a verdict is not.",
    "Say it back before you answer, so you both know what is being said: 'so you feel like I'm "
    "not really here - is that it?' A fair amount of these turn out to be about one bad week.",
    "Give it a hearing without signing up to all of it: 'some of that lands and some of it "
    "doesn't - can we talk about the bit that matters most?' Then do that one thing.",
)
SAID_IT_POOL = (
    "Then you have said it, which is the hard half. Say the same sentence again next time, in "
    "the same words - a line that comes back identical is what makes it a rule rather than a "
    "mood, and it is the explaining that gives them something to argue with.",
    "The first time is usually the one that gets argued with, so say it once more the same way "
    "and then let it sit. Nothing changes in the moment; what changes is that they now know "
    "what you will say.",
    "A quiet reply to that is normal, and it is not the answer yet. Hold the line exactly as "
    "you put it - 'I can't do that' - and leave the door open for the next time: 'ask me again "
    "about Saturday and I'll say yes'.",
)
EVERY_TIME_POOL = (
    "Then it is a pattern rather than a bad week, and worth naming as one: 'this happens most "
    "days' lands differently from 'you did it again'. Ask for the smallest version of it - one "
    "thing, one place - because a whole list is easy to refuse and one thing is not.",
    "Each time it happens, say the same short line and nothing else. It feels repetitive to you "
    "because you are the one saying it; being boring about it is exactly what makes it stick.",
)
DOUBT_POOL = (
    "It is not you being sensitive: a small thing that happens every day is a different thing "
    "from a small thing that happens once. Being worn down by the repetition is the honest "
    "response to it, and it is worth saying as its own sentence.",
    "You are not asking for much - you are asking for the same small thing twice - so it is "
    "worth one clear go before you decide anything. If nothing changes after you have said it "
    "plainly, that is information about them rather than about you.",
    "A thing can be small and still wear you down when it lands every day. Say the one sentence "
    "you would say to a friend in the same spot, and take your own side in it.",
)
# A short line that names the person only as "she" or "they" after the bot has given the words
# ("she never asks if its ok") still got the neutral nod, though the thread is plainly the same
# one. The advice does not need the shape again: it is the holding of the line that is left.
HOLD_THE_LINE = (
    "The line stays the same, and it is worth saying it once more the same way: what you can do, "
    "and what you can't. You don't have to give a reason twice.",
    "Then it is still the one plain sentence, said warmly and once: 'I can't do that.' After that "
    "the answer is no, and it does not need explaining again.",
    "Worth naming it once, plainly, rather than hinting: 'this is happening a lot and I'd like it "
    "to change.' Then leave the next move with them, which is where it belongs.",
)
MY_POOLS = (ASKED, TAKEN, MESSY, LEFT_OUT, TAKEN_FOR_GRANTED, CRITICISED_LINES, WORK_LINES,
            BAILING, LATE_LINES, SUBJECT_AGAIN, RAISE, ABOUT_ME, GOOD_HABIT, WORDS_NOT_MEANT)
THREAD_TURNS = 3


def _in_my_pools(line):
    """True when a bot line is one of this file's own, so the thread is still open."""
    said = " ".join(str(line or "").split())
    if not said:
        return False
    return any(said.startswith(reply[:30]) for pool in MY_POOLS for reply in pool)


def _thread_open(memory):
    """True when the bot's last line in this conversation came out of one of these pools."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    for turn in reversed(turns[-THREAD_TURNS:]):
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("bot") or "")
        if not line:
            continue
        return _in_my_pools(line)
    return False


def holds_the_thread(memory):
    """True when the bot's last line was one of this file's, so a short reply is still this line.

    The receipt the composer gives a second turn ("Got it - it's every single time") is the
    person's own sentence handed back, which is the same class of placeholder as the nod: it puts
    nothing on the table. `bot/modules/greeting.py` asks this before replacing one, so a receipt
    in any other kind of thread keeps the turn.
    """
    return _thread_open(memory)


def _follow_up(clean, memory):
    """The second turn of the same complaint, or None when it is not one."""
    if not _thread_open(memory):
        return None
    words = clean.split()
    asking_about_itself = re.search(r"\b(?:you|your|the bot|this bot)\b", clean)
    if asking_about_itself:
        return None
    if any(phrase in clean for phrase in SELF_DOUBT):
        return DOUBT_POOL
    if any(phrase in clean for phrase in ALWAYS_COUNT) and len(words) <= 12:
        return EVERY_TIME_POOL
    # "what do i say to him" is a request for the sentence, and the composer already has a reader
    # that offers to draft it. Standing down keeps that answer rather than repeating this file's.
    if re.search(r"\b(?:what|how)\b[^?]{0,30}\b(?:say|tell|word|phrase|put it|bring it up)\b",
                 clean):
        return None
    tried = any(phrase in clean for phrase in THE_SAYING)
    outcome = any(phrase in clean for phrase in AFTER_A_SAYING)
    if (tried or outcome) and len(words) <= 20:
        return SAID_IT_POOL
    # A promise that was not kept is the same talk as a line already said, so it gets the pool for
    # that rather than the holding of a boundary: "she says she'll do it and she doesn't" was
    # answered "hold the line: 'I can't do that'", which is a refusal of a request nobody made.
    if re.search(r"\b(?:says? (?:she|he|they)'?ll|said (?:she|he|they)'?d|promised|"
                 r"says? (?:she|he|they) (?:will|would)|doesn'?t|didn'?t|won'?t)\b", clean) \
            and len(words) <= 20:
        return SAID_IT_POOL
    # Nothing said how it went, but the line still names the person and says nothing else: the
    # thread is the same one, and the reply is the holding of the line rather than the shape.
    if re.search(r"\b(?:he|she|they|him|her|them)\b", clean) and len(words) <= 12 \
            and "?" not in clean:
        return HOLD_THE_LINE
    return None


# The complaint can also be handed over as what they say about you ("my partner says I'm never
# really there") or as work being claimed by somebody else ("my friend always takes the credit").
# Both reached the neutral nod.
SAYS_ABOUT_ME = re.compile(
    r"\b(?:says?|said|tells?|told|thinks?|reckons?|calls?)\s+(?:me\s+|everyone\s+|people\s+)?"
    r"(?:that\s+)?(?:i'?m|im|i am|i never|i always|i dont|i don'?t|i only|i just)\b")
CREDIT = re.compile(r"\b(?:take|takes|took|taking|get|gets|got|getting)\s+(?:all\s+)?"
                    r"(?:the\s+)?credit\b|\b(?:takes|took|getting|gets)\s+the\s+blame\b")

def _the_one(word):
    """The person with a plural taken off, so "my kids" is read as a kid and a boss as a boss.

    The child and work readings are keyed on the noun, and a line that says "the kids keep going
    on about minecraft" is the same child as "my kid keeps going on about it".
    """
    if word in CHILD_PEOPLE or word in WORK_PEOPLE or word in PEOPLE_SET:
        return word
    for cut in (word[:-1], word[:-2]):
        if cut in CHILD_PEOPLE or cut in WORK_PEOPLE or cut in PEOPLE_SET:
            return cut
    return word


def _person_named(clean):
    """The person the line is about, as they were named, or "".

    Kept so the work reading can tell a boss from a brother without matching the line twice.
    """
    match = A_PERSON.search(clean)
    if match:
        return match.group(0)
    return ""


def _shape(clean, person):
    """Which pool answers this line, or None when it is not this file's turn.

    The order matters: work first (a boss is not a brother), then being criticised, then the
    three ways of not being asked, then the thing in the line itself, and the general raising-it
    pool last, so a line that names nothing beyond the pattern still gets the words.
    """
    last = _the_one(person.split()[-1]) if person else ""
    if NOT_SINCERE.search(clean):
        # the words are there and what is behind them is not, so neither the good habit nor the
        # criticism reading fits: "my sister thanks me but never means it" was answered with the
        # words to say about a comment on how you look.
        return WORDS_NOT_MEANT
    if (ALWAYS_DOES_IT.search(clean) and not BAILS.search(clean)
            and (A_SHARED_OCCASION.search(clean) or not ASK_FOR.search(clean))):
        # good news, read first so a boss who always thanks you is not sent to the work pool,
        # and in the words that fit the habit: thanks or inclusion
        return GOOD_HABIT_APPRECIATED if THANKED.search(clean) else GOOD_HABIT_INCLUDED
    if (COURTESY.search(clean) and not COURTESY_DENIED.search(clean)
            and not (BAILS.search(clean) or _strained(clean) or CRITICISED.search(clean)
                     or NOT_ASKED.search(clean) or UNSEEN.search(clean))):
        # A courtesy with nothing wrong in the line is good news, whenever the frequency comes:
        # "my daughter thanks me every time", "my mum invites me over every sunday". Nothing is
        # being taken and nothing is being denied, so the pool names the habit back.
        return GOOD_HABIT_APPRECIATED if THANKED.search(clean) else GOOD_HABIT_INCLUDED
    if last in WORK_PEOPLE and (any(word in clean for word in WORK_WORDS)
                                or DONE_TO_ME.search(clean)):
        return WORK_LINES
    if SAYS_ABOUT_ME.search(clean):
        # the complaint is aimed at the person, not held by them, so the pool says hear it
        return ABOUT_ME
    if (CRITICISED.search(clean) and (DONE_TO_ME.search(clean)
                                      or CRITICISED_MY.search(clean)
                                      or SAYS_ABOUT_ME.search(clean)
                                      or _strained(clean))):
        return CRITICISED_LINES
    if CREDIT.search(clean):
        return CREDIT_LINES
    if NOT_ASKED.search(clean):
        return LEFT_OUT
    if UNSEEN.search(clean):
        return TAKEN_FOR_GRANTED
    if ASK_FOR.search(clean):
        return ASKED
    if MESS.search(clean) and re.search(r"\b(?:leaves?|left|leaving|drops?|dropped|"
                                        r"dumping|dumps|put|puts|putting)\b", clean):
        return MESSY
    if MY_THING.search(clean):
        return TAKEN
    if NOT_HELPED.search(clean):
        return RAISE
    if BAILS.search(clean) and not KEEPS_THE_ARRANGEMENT.search(clean):
        return BAILING
    if ARRIVES_LATE.search(clean) and not KEEPS_THE_ARRANGEMENT.search(clean):
        return LATE_LINES
    if (GOING_ON.search(clean) and last not in CHILD_PEOPLE
            and not KEEPS_THE_ARRANGEMENT.search(clean)):
        return SUBJECT_AGAIN
    # A mailbox habit is a work complaint: a neighbour does not reply-all to anything.
    if EMAIL_HABIT.search(clean) and last in WORK_PEOPLE:
        return RAISE
    if DONE_TO_ME.search(clean):
        return CRITICISED_LINES
    if _strained(clean):
        return RAISE
    return None


def _said_at_work(clean, person):
    """True when a line about the boss or a colleague names a thing that changes at work."""
    last = _the_one(person.split()[-1]) if person else ""
    return last in WORK_PEOPLE and any(word in clean for word in WORK_WORDS)


def _strained(clean):
    return any(phrase in clean for phrase in STRAIN)


def answer_for(text, memory):
    """The words to raise it with somebody, or None when this is not that shape.

    Asked by `bot/modules/greeting.py` only where the composer's reply is a placeholder, so a
    None here keeps the reply the person would have had.
    """
    clean = " ".join(str(text or "").lower().split())
    if not clean or len(clean.split()) > 30:
        return None
    memory = memory if isinstance(memory, dict) else {}
    words = set(re.findall(r"[a-z']+", clean))
    if words & NOT_THIS:
        return None
    follow = _follow_up(clean, memory)
    if follow:
        return pick(list(follow), memory, clean)
    # Something that recurs is what this file answers - with one exception, a courtesy nobody
    # means: "my sister thanks me but doesn't mean it" can be said of one evening, and the words
    # to say about it are the same ones.
    if not RECURS.search(clean) and not NOT_SINCERE.search(clean):
        return None
    someone = SOMEONE.search(clean)
    person = _person_named(clean) or (someone.group(0) if someone else "")
    if not person:
        return None
    if words & NOT_A_GRUMBLE or words & GOOD_WORDS:
        return None
    # A question is somebody else's turn unless it asks for the words, which is this file's job:
    # "what do i say to my brother who keeps asking me for money" wants the sentence to say.
    if clean.endswith("?") and not re.search(r"\b(?:what|how)\b[^?]{0,24}\b(?:say|tell|word|"
                                              r"phrase|put it|raise it)\b", clean):
        return None
    if not (DONE_TO_ME.search(clean) or MY_THING.search(clean) or MESS.search(clean)
            or NOT_ASKED.search(clean) or UNSEEN.search(clean) or NOT_HELPED.search(clean)
            or CRITICISED_MY.search(clean) or SAYS_ABOUT_ME.search(clean)
            or CREDIT.search(clean) or _strained(clean) or NOT_SINCERE.search(clean)
            or BAILS.search(clean) or ARRIVES_LATE.search(clean) or GOING_ON.search(clean)
            or EMAIL_HABIT.search(clean) or COURTESY.search(clean)
            or _said_at_work(clean, person) or ALWAYS_DOES_IT.search(clean)):
        return None
    pool = _shape(clean, person)
    if not pool:
        return None
    return pick(list(pool), memory or {}, clean)
