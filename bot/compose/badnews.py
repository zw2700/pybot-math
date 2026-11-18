"""Lines that are news of the hard kind: an illness, an emergency, money trouble, a loss.

They share no word, so they are patterns rather than a word list: "our cat was put down" and
"my mum has cancer" and "we are behind on the rent" are one kind of line to a friend, and that
kind is never answered with "Noted!" or by repeating it back. Two callers need the same list,
which is why it lives here on its own:

* bot/compose/fallback.py settles the mood on it, so the stock reply is a gentle one;
* bot/memory/ack.py refuses to echo it, because "your cat was put down yesterday — noted"
  would be awful.

Every pattern is matched against the cleaned, lowercased line (understanding's memory
["understood"]["clean"]), so it must not depend on capitals or punctuation.

A death is left to bot/compose/loss.py, which reads it properly and answers it before any of
this is asked; a loss that loss.py does not read ("a miscarriage", "terminally ill") is here so
that it is still never noted.

The hard part is that the same word is news in one line and ordinary in another: "my dad is in
hospital" is news, "i work at the hospital" is a job, "my son took all my pills" is an
emergency, and a paramedic talking about shifts is neither. So the words that only mean
something about a person or an animal are written that way: the person or the animal has to be
there in the line.
"""
import re
try:  # the reading of a dream, so a dream of a death is not a death
    from ..memory import dream as _dream
except Exception:  # noqa: BLE001 - a reading that cannot be imported just adds no rule
    _dream = None

from ..understanding.normalize import LEXICON, without_the_figure_of_speech  # noqa: F401

# The people and animals the emergency phrases need: a collapse about one of these is an
# emergency, a souffle collapsing is dinner.
LIVING = (r"(?:mum|mom|mother|dad|father|gran|granny|grandma|grandad|grandpa|nana|nan|"
          r"brother|sister|son|daughter|child|baby|wife|husband|partner|boyfriend|girlfriend|"
          r"friend|mate|uncle|aunt|cousin|neighbour|neighbor|colleague|boss|teacher|ex|"
          r"dog|cat|pet|horse|rabbit|puppy|kitten|bird)")

# The people a condition is reported about: LIVING plus the family words a person uses for the
# relative they look after. "my nephew has leukaemia" was filed away as a fact while "my son has
# leukaemia" was news, and which nephew is which is not a distinction a friend makes.
CONDITION_OWNER = LIVING[:-1] + (r"|nephew|niece|stepson|stepdaughter|stepmum|stepdad|"
                                 r"stepmother|stepfather|grandson|granddaughter|"
                                 r"mother in law|father in law|son in law|daughter in law|"
                                 r"grandchild|grandchildren)")

# Someone has died, and it is not the line's own ending: "my mum died", "a boy in my class
# killed himself", "my mate passed away on sunday". A death is the one thing the composer must
# never answer with a congratulation or with "what is it doing exactly", so it is read here, once,
# and both of those readers stand aside on it. The subject has to be a person (or an animal):
# "my phone died" is a broken thing and belongs to the repair pools, and "the plant died" is the
# garden's. "killed himself" and "took her own life" name their own subject, so the clause a
# reflexive suicide sits in counts whether or not the person is one of the words above.
# "he died laughing" is a joke and "my mum is dead funny" is a compliment, so the two plainest
# words carry the idioms that are not a death. "died of cancer" is a death and "died of
# embarrassment" is not, which is why only the feelings are named on that side.
_HOW_IT_IS_SAID = (
    r"died(?!\s+(?:laughing|giggling|smiling|of\s+(?:embarrassment|boredom|shame|laughter|"
    r"fear)|inside|a\s+(?:little|bit)|and\s+gone|"
    # "she died her hair blue" is a dye, and the same word is a death in every other sentence.
    r"(?:her|his|their|my|our|your|its)\s+hair))"
    r"|dead(?!\s+(?:funny|good|nice|cheap|easy|serious|certain|jealous|tired|right|wrong|set|"
    r"on\b|beat|last\b|chuffed|proud|pleased|happy|keen|excited|thrilled|impressed|lucky|"
    r"jammy|buzzing|gutted|made\s+up|against|ahead|centre|straight|silence|giveaway|heat|calm|"
    r"in\s+(?:the\s+middle|a\s+row)|ringer|"
    r"to\s+(?:the\s+world|rights|me|us|him|her|them)\b))")
_DEATH_WORDS = (
    _HOW_IT_IS_SAID + r"|passed away|killed himself|killed herself|killed themselves|"
    r"hanged himself|hanged herself|hanged themselves|took his own life|took her own life|"
    # "he didn't make it to the wedding" is a missed party and "he didn't make it in time" is a
    # missed train; without a destination or a time after it, it is how people say a death.
    # "my dad passed on the salt" and "she passed on my message" are the other verb: with an
    # object after it, it is not a death. "passed on sunday" / "passed on in march" still are.
    r"took their own lives|committed suicide|suicid\w*|found dead|"
    r"passed on(?!\s+(?:the|a|an|my|his|her|their|our|your|its|it|this|that|these|those|some|all|both)\b)|"
    r"didn'?t make it(?!\s+(?:(?:to|for)\s+\w|in\s+time|on\s+time))|"
    r"did not make it(?!\s+(?:(?:to|for)\s+\w|in\s+time|on\s+time))")
# "i nearly died" and "i could have died" say how close it came, not that it happened.
_NEARLY = re.compile(r"\b(?:nearly|almost|practically|might\s+have|could\s+have|would\s+have|"
                     r"like\s+to\s+have)\b", re.I)
# The joke that follows the words: "he died laughing", "he killed himself laughing", "she died of
# embarrassment". Main's own guard on the reflexive form is the same reading, so it is shared here.
_AFTER_IT = re.compile(r"^\s*(?:laughing|giggling|smiling|of\s+(?:embarrassment|boredom|shame|"
                       r"laughter|fear)|to\s+(?:me|us|him|her|them)\b)", re.I)
# The death on its own, for a reader that already knows the line is about a person.
DEATH_SAID = re.compile(rf"\b(?:{_DEATH_WORDS})\b")
# The people a death is reported about, beyond LIVING: school and work are where most of the
# deaths a person hears about happened, and none of those words is a relative.
OTHERS = (r"(?:boy|girl|lad|lass|kid|child|man|woman|person|someone|anyone|classmate|"
          r"schoolmate|teammate|workmate|student|pupil|neighbour|neighbor|friend|mate|fella|"
          r"guy|colleague|he|she|they|everyone|everybody)")
# The person and the death are in one clause: a full stop or a question mark between them makes
# two statements, and "my mum is fine. my phone died" is about the phone.
# The word nearest the death is its subject, so a window over the clause is not enough: "he said
# his phone died" has a person and a death in one clause, and it is the phone that died. The words
# that carry a clause to its verb are stepped over, and so is a place or a group, because a death
# is announced by where it happened as often as by who: "someone in my class died", "a woman at
# my work died".
_CARRIES = frozenset("""is was were are am be been being has had have just also nearly almost
still of in at on to for with that who which my his her their our your its the a an and but so
then today yesterday now last this from like about after before when while if sadly tragically
unexpectedly peacefully suddenly quietly finally recently apparently presumably unfortunately
honestly basically literally obviously definitely really very""".split())
_PLACE = frozenset("""class classes year school work office team family ward house hospital
floor street town village college uni university club gym shop company firm site shift course
group nursery classroom road estate""".split())
_PERSON = frozenset(LIVING.lstrip("(?:").rstrip(")").split("|")) | frozenset(
    OTHERS.lstrip("(?:").rstrip(")").split("|"))
_WORD = re.compile(r"[a-z']+")

# Emergencies are typed fast and misspelled ("my mum is having a sezure"), so a word within one
# letter of one of these counts too: "sezure", "hospitel", "unconcious".
NEARLY = frozenset((
    "seizure", "unconscious", "overdose", "choking", "breathing", "collapsed", "hospital",
    "ambulance", "cancer", "stroke", "bleeding", "diagnosed",
))

# What was lost is a *chance*: a job, a match, a deal, an offer. "i lost my keys" is a thing to
# find, "i lost my train of thought" is nothing at all, and "i lost weight" is a change in the
# body, not news to be sorry about. So the verb alone is not bad news, and the person doing the
# losing can be someone they are telling the bot about ("my sister lost her job").
LOST_CHANCE = (r"jobs?|work|role|position|match(?:es)?|games?|deals?|contracts?|shift|hours|"
               r"clients?|customers?|accounts?|bids?|bets?|elections?|deposits?|offers?|"
               r"interviews?|places?|spots?|funding|grants?|appeals?|races?|finals?|trials?|"
               r"orders?|bookings?|tenanc(?:y|ies)|tenders?|placement|promotion|apprenticeship")
LOST_PATTERN = (r"\b(?:i|we|he|she|they|ive|i've|my [a-z]+|our [a-z]+)\s+"
                r"(?:have\s+|had\s+)?(?:lost|losing)\s+(?:out on\s+)?"
                r"(?:the |my |our |his |her |their |your |that |this |a |an )?"
                r"(?:" + LOST_CHANCE + r")\b")

# Being left by the person you live with is the same kind of news as a death and a job lost, and
# people write it in their own few words: "my wife left me", "he left me", "she walked out on me",
# "my ex left me for my best friend". The verb is ordinary, so the person has to be there: "the
# bus left me behind" and "my sister left me her car" are not this. "left me" followed by a
# determiner is a thing handed over rather than a person gone, and is ruled out. The leaving is
# said in the present as well as the past ("my wife wants to leave me", "he is going to leave
# me"), because the person says it while it is still coming, and "leave me" is the same news as
# "left me" - it was answered "Got it - you think your wife wants to leave you".
LEFT_ME = (r"(?:\b(?:he|she|they|my (?:wife|husband|partner|boyfriend|girlfriend|fianc\w*|ex))"
           r"[^.!?]{0,24}\b(?:left me|leaving me|leave me|left and|walked out|dumped me|"
           r"cheated on me)\b"
           r"(?!\s+(?:her|his|their|the|a|an|this|that|alone|be)\b))")

LEFT_ME_RE = re.compile(LEFT_ME, re.I)

# The same leaving in the past tense without the "me": "my husband has left", "my wife left last
# week", "my girlfriend has left". Every one of them was answered "Noted: your husband has left."
# - the store reading a marriage ending back as a fact - because "left" is not one of the tenses
# of "leave" the readers knew: "left me" was covered, "is leaving" was covered, "has left" was
# not. What can follow it and still be a leaving is the time it happened, or the end of the line;
# a place or a thing after it means the verb went somewhere or handed something over ("left for
# work", "left the house", "left his keys"), which is not this.
PARTNER_LEFT = (
    r"\b(?:my (?:wife|husband|partner|boyfriend|girlfriend|fianc\w*|ex)|my marriage)\b"
    r"[^.!?]{0,30}?\b(?:has|have|had|just|recently|already|suddenly|now|then|finally)?\s*\bleft\b"
    r"(?=\s*(?:$|[.!?,;]|\b(?:me|us|and|but|because|so|now|already|again|too|last|this|"
    r"yesterday|today|tonight|morning|evening|week|month|year|night|day|suddenly|recently|"
    r"at\s+(?:christmas|new\s+year|the\s+weekend|easter)|in\s+\w+|"
    r"after\s+\w+|before\s+\w+|since\s+\w+)\b))")

PARTNER_LEFT_RE = re.compile(PARTNER_LEFT, re.I)


# The same leaving said about the partner without the "me": "my wife is leaving", "my partner is
# leaving and i dont know what to do", "i think my partner wants to leave". The verb on its own is
# ordinary, so the relation has to be the subject of it - "my wife is leaving for work", "my
# partner is leaving her job" and "my ex is leaving the country" are plans, and the word after the
# leaving is what tells them apart. "my wife and i are leaving" is fenced the same way, by the
# place that follows.
PARTNER_LEAVING = (
    r"\b(?:my (?:wife|husband|partner|boyfriend|girlfriend|fianc\w*|ex)|my marriage)\b"
    r"[^.!?]{0,30}?\b(?:is|are|was|were|keeps?|kept|been|got|has|have|says?|said|told me|"
    r"tells me|wants?|wanted|might|may|will|would|thinks?|thinking)\b[^.!?]{0,26}?"
    r"\bleav(?:e|es|ing)\b"
    r"(?!\s+(?:me\b|for\b|to\b|on\b|at\b|in\b|early\b|home\b|work\b|school\b|the\b|"
    r"her\b|his\b|their\b|a\b|an\b|this\b|that\b"
    # Time off is the same word and is not a leaving: the word after it is what tells them
    # apart, the way the place after "leaving for work" does. "my husband has leave booked for
    # july" was answered with the pool for being left.
    r"|approved\b|booked\b|due\b|owing\b|remaining\b|allowance\b|entitlement\b|days?\b|"
    r"pay\b|request\b|year\b|starts?\b|begins?\b|ends?\b|cancell?ed\b|denied\b|"
    r"refused\b|pending\b|confirmed\b|carried\b|unused\b|balance\b))")

PARTNER_LEAVING_RE = re.compile(PARTNER_LEAVING, re.I)


# The same leaving reported rather than announced: "she said shes leaving", "he told me hes
# leaving", "she says she wants to leave". The relation word is missing because the person has
# already named her, so the sentence in front of the leaving is what has to say whose leaving it
# is - a report from "he", "she" or "they", and then the leaving itself. All of these were
# answered "I'm listening - say more if it helps" or "Got it. Is there anything you'd like a hand
# with?" while "my wife is leaving" and "she is leaving me" got the pool for being left.
#
# What follows the leaving is what tells a leaving from an errand, exactly as in PARTNER_LEAVING:
# a job, a room, a hospital and a country are places to leave. The adverbs go too, because "she
# said shes leaving soon" is not news of being left on its own - the person would have said who
# is leaving. Only the bare report counts.
# `shes told me shes leaving` is the same news as `she told me she is leaving`: the apostrophe is
# the first thing typed text loses, so the subject is matched with and without it.
REPORTED_LEAVING = (
    r"\b(?:he|she|they|hes|shes|theyre)\b[^.!?]{0,24}?\b(?:said|says|told me|tells me|"
    r"reckons|thinks|"
    r"keeps saying)\b"
    r"(?:\s+(?:that|he|she|they|hes|shes|theyre|he is|she is|they are))?"
    r"(?:\s+(?:is|are))?"
    r"(?:\s+(?:going|planning|thinking|wants?|wanted|wanted to|might|may|will|would|ready|"
    r"about|seriously)\b(?:\s+(?:to|of|about))?)?"
    r"\s+\bleav(?:e|es|ing)\b"
    r"(?!\s+(?:me\b|for\b|to\b|on\b|at\b|in\b|early\b|home\b|work\b|school\b|the\b|"
    r"her\b|his\b|their\b|him\b|a\b|an\b|this\b|that\b|soon\b|now\b|tonight\b|tomorrow\b|"
    r"today\b|next\b|after\b|before\b|hospital\b|care\b|rehab\b|prison\b|jail\b|"
    r"army\b|navy\b|force\b|uni\b|university\b|college\b|again\b))")

REPORTED_LEAVING_RE = re.compile(REPORTED_LEAVING, re.I)


# The leaving said as something that has already happened, against the same news said while it is
# still coming: "my husband left me last month" and "my husband wants to leave me" take the same
# pool, but one of its lines asks what it is like in the house, and a husband who left a year ago
# is not in it. "my ex left me for my best friend" was answered "That's rough, the person you live
# with saying that", which is a question about a house the person is not in.
# "we broke up after 4 years" is the same news and the same pool, and the ending is always past -
# nobody says "we are breaking up after 4 years" about a break-up still coming the way they say
# "my wife is leaving" - so the words that only ever name the ending join the list. Before them,
# "we broke up after 4 years" was answered "That's rough, the person you live with saying that.
# What's it like in the house?" - a house invented for a couple the person never said they lived in.
LEFT_GONE = (r"\b(?:left me|left and|walked out|dumped me|moved out|"
             r"packed (?:her|his|their) (?:things|bags)|gone|"
             r"broke up|broken up|split up|separated|divorced)\b")
# A plan word in front of the leaving is the leaving still coming, however much of it is written in
# the past: "she told me she is leaving", "he said he wants to leave me".
STILL_COMING = (r"\b(?:is|are|was|were|keeps?|kept|said|says|told|tells|wants?|wanted|might|"
                r"may|will|would|going|planning|thinking|decided)\b[^.!?]{0,26}?"
                r"\bleav(?:e|es|ing)\b")
# They may be gone and still in the house, and then the house is the question.
STILL_HERE = (r"\b(?:still (?:live|living|here|in the house|together)|lives? with me|"
              r"under the same roof|separated but)\b")


# The ending said without the word "leave": "my marriage is over", "we split up last week",
# "we are getting a divorce", "she asked for a divorce". These are the same news as being left
# and they want the same pool; nothing in the file knew them, so "my marriage is over" was
# answered "I'm listening - say more if it helps" and the verdict after it - "what a nightmare" -
# was answered "Annoying. Is it a quick fix or a whole thing?" over a marriage ending. The subject
# has to be the marriage or the two of them, so "the film is over", "we are over the worst of it"
# and "we split the bill" are not this.
MARRIAGE_ENDED = (
    r"\b(?:my|the)\s+(?:marriage|relationship)\b[^.!?]{0,24}?"
    r"\b(?:is|are|was|were|has|have|seems?|looks?)\b[^.!?]{0,16}?"
    r"\b(?:over|done|finished|ended)\b"
    r"(?!\s+(?:the|it|with|there|here|that|this|to|by|at|and)\b)"
    r"|\b(?:we|me\s+and\s+my\s+\w+)\b[^.!?]{0,20}?"
    r"\b(?:split\s+up|broke\s+up|broken\s+up|separated|divorced)\b"
    r"(?!\s+(?:the|a|into|over|it)\b)"
    r"|\b(?:getting|got|had|filed\s+for|asked\s+for|asking\s+for|wants?|wanted)\s+"
    r"(?:a\s+)?divorce\w*\b"
    # ...but a divorce lawyer, a divorce court or a divorce settlement is the machinery around a
    # divorce, said by somebody who is already through the naming of it.
    r"(?!\s+(?:lawyer|solicitor|court|papers|settlement|money|bill|forms?)\b)")

MARRIAGE_ENDED_RE = re.compile(MARRIAGE_ENDED, re.I)

# Somebody else's marriage is news about them: "my mate just told me hes getting divorced" was
# answered "Is there anyone you can say it to tonight?" - the question for the one being left,
# asked of the friend hearing about it. A mate in the line and no partner beside it means the
# ending is not the person's own.
NOT_THEIRS = re.compile(
    r"\bmy\s+(?:mate|mates|friend|friends|best\s+friend|brother|sister|colleague|boss|cousin|"
    r"neighbour|neighbor|aunt|uncle|son|daughter|mum|mom|dad|mother|father|nan|gran|grandad|"
    # A parent's divorce, an in-law's, a step-parent's: the person is telling me about somebody
    # else's marriage, however close. Without these, "my parents got a divorce when i was little"
    # took the pool for the one being left and was answered "That's rough, the person you live
    # with saying that. What's it like in the house?" - a house and a sentence invented for a
    # childhood that ended years ago.
    r"parents?|family|in[-\s]?laws?|step\w+|grand\w+|landlord)\b")
PARTNER = re.compile(r"\b(?:wife|husband|partner|boyfriend|girlfriend|fianc\w*|ex)\b")

# "Leave" is a noun as often as a verb, and the noun is time off, which is usually good news:
# "my husband got his leave approved" and "my husband has leave booked for july" were met with
# "That's a hard thing to hear. Where are you with it" - a condolence for a holiday. A
# determiner or a possessive in front of it is what makes it the noun, and the leaving readers
# read the line with those taken out, so no pattern here has to know the difference.
_LEAVE_THE_NOUN = re.compile(
    r"\b(?:his|her|their|my|our|your|its|the|some|any|no|annual|maternity|paternity|parental|"
    r"shared|sick|paid|unpaid|compassionate|study|garden|special|sabbatical|holiday)\s+leave\b")


def _without_the_noun_leave(said):
    """The line with "his leave" and "annual leave" taken out: time off is not a leaving."""
    return " ".join(_LEAVE_THE_NOUN.sub(" ", said).split())


def _a_leaving_at_all(said):
    """The leaving in any of its wordings: left me, is leaving, or the marriage ending said plain."""
    said = _without_the_noun_leave(said)
    if not (LEFT_ME_RE.search(said) or PARTNER_LEAVING_RE.search(said)
            or PARTNER_LEFT_RE.search(said) or MARRIAGE_ENDED_RE.search(said)):
        # A leaving reported rather than announced is the person's own when nobody else is named
        # in it: "my sister said shes leaving her husband" is a question about the sister, and it
        # has its own answer, so the report stands aside for anybody the line puts beside them.
        return bool(REPORTED_LEAVING_RE.search(said) and not NOT_THEIRS.search(said))
    return not (NOT_THEIRS.search(said) and not PARTNER.search(said))

def reads_as_a_leaving_already_gone(clean):
    """Whether the leaving has happened, so the pool's question about the house does not fit."""
    said = " ".join(str(clean or "").lower().split())
    if not _a_leaving_at_all(said):
        return False
    if re.search(STILL_HERE, said):
        return False
    return bool(re.search(LEFT_GONE, said)) and not re.search(STILL_COMING, said)


def reads_as_a_reported_leaving(clean):
    """Whether the leaving is reported in the third person rather than said of the partner.

    "she said shes leaving" is the same news as "my wife is leaving" and it takes the same pool,
    so the reading does not tell them apart. What does is what has an entry behind it: a partner
    leaving named in the first person reaches the leaving counsel, and the ask that follows -
    "what do i do" - is answered by that counsel. A reported leaving has no entry behind it, so
    after it the ask is better answered by whoever reads the ask. Kept apart here so that
    `compose.step_when_low` can stand down for it without losing the carve-out the partner
    leaving needs.
    """
    said = _without_the_noun_leave(" ".join(str(clean or "").lower().split()))
    if not REPORTED_LEAVING_RE.search(said) or NOT_THEIRS.search(said):
        return False
    return not (LEFT_ME_RE.search(said) or PARTNER_LEAVING_RE.search(said)
                or MARRIAGE_ENDED_RE.search(said))


def reads_as_the_leaving(clean):
    """Whether the line is the person being left by the one they live with.

    The same news before it happens as after it: "my wife wants to leave me" is not a plan the
    person is deciding on, it is the leaving landing on them, and the answer it wants is the one
    for being left. It is the same answer when the partner's leaving is said without the "me" -
    "my wife is leaving and i dont know what to do" was answered "Thanks for telling me - I'm
    here if you want to dig into any of that", which says nothing about the leaving at all.
    """
    said = " ".join(str(clean or "").lower().split())
    return _a_leaving_at_all(said)


# The same news before it has happened: "im thinking of leaving my husband", "i want to leave
# him", "we are going to split the house". A friend reads this as the same kind of line as
# LEFT_ME, and it decides things: after it, "she took the kids to her mums" is the middle of a
# story and not a fact to file. The plan word has to be there, because "i left my keys in the
# car" and "he left me his van" are not this, and the thing being left has to be a person or
# the marriage: "im thinking of leaving my job", "we are leaving on friday" and "im leaving my
# flat next month" are ordinary plans.
LEFT_PLAN = (r"\b(?:thinking (?:of|about)|thought (?:of|about)|want(?:s|ed)? to|wanting to|"
             r"going to|planning (?:on|to)|plan to|decided to|ready to|about to|meant to|"
             r"should i|shall i|do i)\s+(?:just\s+|actually\s+|really\s+)?"
             r"(?:leave|leaving|walk out on|end)\s+"
             r"(?:(?:my|our) (?:wife|husband|partner|boyfriend|girlfriend|fianc\w*|marriage|"
             r"ex|other half)|him|her|them|us)\b"
             # Said as it happens rather than as a plan: "im leaving him tonight". The person
             # has to be the object and not the person being handed something, so "im leaving
             # him a note" and "im leaving her the flat" stay ordinary.
             r"|\b(?:i'?m|im|i am|we'?re|were|we are)\s+(?:just\s+|actually\s+)?"
             r"(?:leaving|walking out on)\s+"
             r"(?:my (?:wife|husband|partner|boyfriend|girlfriend|fianc\w*|ex|other half)|"
             r"him|her|them)\b(?!\s+(?:a|an|the|some|his|her|my|our)\b)")

# The half of LEFT_PLAN that says the decision is the speaker's own: "im leaving him tonight",
# "i want to leave her", "we're going to split up". LEFT_PLAN is the reading that keeps a story
# going, and both halves belong there; this is the half that decides what to say back, because a
# plan the speaker is making is not news that happened to them. "Sorry to hear that" is what you
# say to the person it happened to, and the person here is the one deciding.
OWN_PLAN = tuple(re.compile(pattern) for pattern in (
    r"\b(?:i'?m|im|i am|we'?re|were|we are)\s+(?:just\s+|actually\s+|finally\s+)?"
    r"(?:going to|gonna|planning to|plan to|decided to|ready to|about to|wanting to|"
    r"thinking (?:of|about)|want to)\s+(?:just\s+|actually\s+|really\s+)?"
    r"(?:leave|leaving|walk out on|end it with)\s+",
    r"\b(?:i'?m|im|i am|we'?re|were|we are)\s+(?:just\s+|actually\s+|finally\s+)?"
    r"(?:leaving|walking out on)\s+",
    r"\b(?:i|we)\s+(?:have|'ve|ve)\s+(?:decided|made up my mind)\b",
    r"\bwe(?:'?re| are)?\s+(?:going to|gonna)\s+(?:split|separate|divorce)\b",
))

# The verbs that mean a job went. "fired" is the one word here with an everyday life of its
# own - a pot in the kiln, a fired-up crowd - so it needs a person and a passive on it, and it is
# ruled out in front of "up". "they let me go" is the same news said the way people say it, and
# the verb is ordinary ("let the kids go to bed"), so the subject has to be the employer.
SACKED_FIRED = (
    # a person and a passive: "i got sacked", "i was fired", "i've been dismissed". The auxiliary
    # is required, because "i fired the clay" is the person doing the firing.
    r"\b(?:i|we|he|she|they|my [a-z]+|our [a-z]+)\s*(?:just\s+|only\s+|then\s+|now\s+|today\s+)?"
    r"(?:'?ve|have|has|had|was|were|been|being|got|get|gets|getting|is|are|am)\s+"
    r"(?:been\s+|being\s+)?"
    r"(?:sacked|fired(?!\s+up\b)|dismissed)\b"
    # ... and the employer doing it, with the person as the object: "they fired me"
    r"|\b(?:they|he|she|the company|the firm|the shop|work|my boss|my manager|my employer)\s+"
    r"(?:just\s+)?(?:sacked|fired(?!\s+up\b)|dismissed)\s+(?:me|him|them|us)\b"
    # "they let me go" is the same news, but the verb is ordinary ("let the kids go to bed", "let
    # me go home early"), so the employer has to be the subject and the going has to be the end.
    r"|\b(?:they|the company|the firm|the shop|work|my boss|my manager|my employer)\s+"
    r"let\s+(?:me|him|her|them)\s+go\b(?!\s+(?:home|early|out|to|and|for a)\b)"
    r"(?!\s+on\s+(?:holiday|strike|leave|a\b|the\b|maternity|paternity|benefit|tour|safari))"
    r"|\b(?:got|gotten|gave me|handed me|give me)\s+the (?:sack|boot|push)\b(?!\s+of\b)")

# The court date that is the best day of someone's year: an adoption, and the final hearing that
# makes it final. A court reading cannot tell a bailiff from this, so the words stand the whole
# court family down (see `BAD_NEWS_ITSELF` below) and the line keeps the answer it had before.
ADOPTION_WORDS = r"\b(?:adopt\w*|adoption)\b"

# The news that arrives as a sentence about a body: a diagnosis, an emergency, a payment behind,
# a loss. This is the list a bare ask after heavy news is answered from (`bot/compose/fallback.py`,
# `_news_above`), so it is kept as its own tuple: see `NEWS_WITH_A_NAME` for why.
BAD_NEWS_ITSELF = tuple(re.compile(pattern) for pattern in (
    # A death is not here: bot/compose/loss.py reads a loss, a funeral and grief, and it
    # answers them before this is asked. What is left is the news that has no such module.
    r"\b(?:diagnos\w+|cancer|chemo\w*|tumou?r|biopsy)\b",
    # "I work at the hospital" is a job, not news.
    r"(?<!\bwork )(?<!\bworks )(?<!\bworked )\bin (?:the )?hospitals?\b",
    r"\b(?:a&e|icu|ambulances?|overdose|surgery|operation|anaesthetic)\b",
    r"\b(?:strokes?|heart attacks?|seizures?|chest pains?)\b",
    # Keeping food or water down is the thing a person asks about when they are unwell, and
    # "can't keep a job down" or "can't keep up" are not it.
    r"\bcan'?t keep (?:anything|any food|food|fluids?|liquids?|water|solids?) down\b",
    # A cut, a burn or bleeding on a person: "my mum has cut her wrist", "my dad has a bad
    # cut on his hand". "my mum cut me a slice of cake" is not one, so the person comes first.
    rf"\b{LIVING}\b[^.!?]{{0,16}}\bcut (?:her|his|their|its)self\b",
    rf"\b{LIVING}\b[^.!?]{{0,16}}\b(?:has|had|got) (?:a |an )?(?:\w+ )?(?:cut|wound|gash|burn)\b",
    rf"\b{LIVING}\b[^.!?]{{0,16}}\b(?:cut|burnt|burned|bleeding|bled)\b[^.!?]{{0,12}}"
    r"\b(?:her|his|their)\b",
    # Something happening to a person right now: "my dad collapsed", "she's not breathing".
    # The bare verb counts as well as the past tense, because "my mum collapse" is a hurried
    # typist writing "collapsed", and a person collapsing is the one thing this module must not
    # miss. "the scaffolding might collapse" and "the souffle might collapse" are not LIVING, so
    # the everyday word stays a word of its own.
    rf"\b{LIVING}\b[^.!?]{{0,24}}\b(?:collaps(?:e|ed|ing)|fainted|passed out|blacked out|"
    r"not breathing|can'?t breathe|choking|bleeding badly)\b",
    # "i collapsed" is news about the person typing, and so are the ways people say it: a faint,
    # a blackout, being sick. "passed out" is a different thing from "passed" (a test, a parcel).
    r"\bi\b[^.!?]{0,16}\b(?:collapsed|fainted|passed out|blacked out|threw up|"
    r"vomited|was sick all|been sick all)\b",
    # "i want to die my hair pink" is a hair appointment: the phrase only counts when it is
    # not followed by the thing that gets the verb, so a determiner after it rules it out.
    r"\b(?:kill myself|killing myself|end my life|take my own life|want to die|"
    r"better off dead)\b(?!\s+(?:my|your|his|her|their|our|the|a|an|this|that|it)\b)",
    r"\b(?:won'?t let me leave|hits me|hit me|hurts? me|hurting me|threatened me|"
    r"took my phone|takes my phone)\b",
    r"\b(?:on fire|smoke in|gas leak|smell(?:s)? (?:of )?gas)\b",
    r"\b(?:took|taken) (?:all|too many|the rest of) (?:my|his|her|their|the) pills\b",
    r"\b(?:broke up|split up|divorce\w*|redundant|laid off|evicted|stolen|robbed|scammed)\b",
    # Losing a job is said in the verbs that carry no other meaning: "i got sacked", "i was
    # fired", "they let me go". "redundant" and "laid off" were here and these were not, so
    # "i got sacked" was read as nothing at all and handed back as "Noted: you got sacked", and
    # the age after it got "You're 58, good to know" instead of the age worry. The verb has to
    # have a person on it: "i fired a pot in the kiln" and "i got fired up about the match" are
    # not somebody losing their job.
    SACKED_FIRED,
    LEFT_ME,
    LEFT_PLAN,
    r"\b(?:in debt|arrears|behind on (?:the )?(?:rent|mortgage|payments|bills)|"
    r"can'?t afford|can not afford)\b",
    r"\b(?:didn't get|didn't work out|didn't make it|turned down|turned it down|no luck|"
    r"wasn't picked|not chosen)\b",
    LOST_PATTERN,
    # A pregnancy that has ended. The word is never ordinary, so no person has to be there:
    # "i think i had a miscarriage" is one of the hardest things a person types, and
    # "my girlfriend had a miscarriage last month" must never be noted back at her.
    r"\bmiscarriage(?:s)?\b(?! of justice)|\bmiscarried\b",
    r"\bstill ?born\b|\bstill ?birth\b",
    # What follows the baby decides: "losing the baby weight" and "losing the baby belly" are a
    # body, and "losing the baby" or "losing our baby clothes" are not the news this pool answers.
    r"\b(?:lost|losing|we lost) (?:the|our|her|his|their) baby\b"
    r"(?!\s+(?:weight|belly|tummy|fat|pounds?|stones?|kilos?|inches|clothes|things|stuff|"
    r"room|pram|toys?|seat|carrier|monitor|name|bag|book)\b)",
    # A suicide among the people a person knows: "my friend killed himself". The person has to
    # be there, so "he killed it at the gig" stays praise, and a laugh right after it stays a
    # joke ("he killed himself laughing").
    rf"\b{LIVING}\b[^.!?]{{0,24}}\bkilled (?:him|her|them)sel(?:f|ves)\b"
    r"(?!\s+(?:laughing|giggling))",
    r"\b(?:took|taken|taking) (?:his|her|their) own life\b|\bcommitted suicide\b",
    # Bleeding or spotting in pregnancy is a midwife today, never good news. Both word orders,
    # because people write it both ways: "im pregnant and spotting", "spotting at 7 weeks
    # pregnant".
    r"\bpregnan\w+\b[^.!?]{0,24}\b(?:spotting|bleeding|cramping)\b",
    r"\b(?:spotting|bleeding)\b[^.!?]{0,24}\bpregnan\w+\b",
))

# The news that has a name in it: a condition on somebody they love, a child they are kept from, an
# award refused, the roof going, a court letter that has arrived. It is the same hard week as the
# list above, and it is answered the same way, so `reads_as_bad_news` reads both. It is kept apart
# because of the one caller that must not see it: a bare ask after heavy news stands the ask pool
# down ("what should i do" after a diagnosis is not a question about anything else), and there the
# narrow list is right - "bailiffs turned up" then "what do i do" already has the answer about the
# door, and standing it down in favour of a gentleness pool took it away.
# The award half of the named news, on its own, because it is the one shape with a service behind
# it: a benefit stopped is a week's money and a form, and where the person whose job it is can be
# named ("they stopped my universal credit" -> MoneyHelper), that pointer is the concrete answer and
# the gentle line is not. The other shapes name nobody who settles them, so they keep the gentler.
AWARD_LOST = tuple(re.compile(pattern) for pattern in (
    # A payment or an award taken away, or refused: "my pip was refused" was answered "Oh, that's
    # a nuisance", and a benefit being stopped is the week somebody's money runs out. The award
    # has to be named, so "they cut my grass" and "my hair is cut" are not it.
    r"\b(?:pip|dla|esa|universal credit|housing benefit|child benefit|tax credits?|"
    r"benefits?|allowance|pension|pay|wages|hours)\b[^.!?]{0,24}"
    r"\b(?:stopped|cancell?ed|cut|suspended|frozen|refused|sanctioned|withdrawn|reduced|"
    r"turned down|taken away|not renewed)\b",
    r"\b(?:stopped|cancell?ed|cut|suspended|frozen|sanctioned|withdrawn|refused|reduced)\b"
    r"[^.!?]{0,20}\b(?:my|our)\s+(?:pip|dla|esa|universal credit|benefits?|pay|wages|pension|"
    r"allowance|hours)\b",
    # "i got sanctioned" names no award, because everyone on one knows which: the bare word is the
    # whole report, and it was answered "Noted: you got sanctioned." It is the benefit's word and
    # not the other one, so "i got sanctioned leave approved" (and a holiday, or time off) is a
    # form coming back signed rather than money stopping.
    r"\b(?:got|gotten|been|being|was|were|just|now)\s+sanctioned\b"
    r"(?!\s+(?:leave|holiday|absence|time off|day off|overtime|pay rise)\b)",
))

NEWS_WITH_A_NAME = tuple(re.compile(pattern) for pattern in (
    # A condition with a name is news when it is on somebody the person loves. The stock line for
    # "my husband has parkinsons" was "Noted: your husband has parkinsons", which files a marriage
    # away as a fact, and "my son has leukaemia" got the same. The condition has to be one nobody
    # chooses and nobody shakes off, and one of their people has to be its subject: "i have a
    # migraine" stays an ordinary ache, "my dad has arthritis" is a knee that aches and is left to
    # the pools for bodies, and "my team has covid" is gossip. The misspellings are here because
    # these are the words people type in a hurry: "my gran has altzheimers".
    rf"\b{CONDITION_OWNER}\b[^.!?]{{0,20}}\b(?:has|have|had|got|is|was|were|been|being)\b"
    rf"[^.!?]{{0,24}}"
    r"\b(?:dementia|alzheim\w*|altzheim\w*|parkinson\w*|motor neurone|"
    r"huntington\w*|multiple sclerosis|muscular dystrophy|leuka?emia|lymphoma|myeloma|"
    r"mesothelioma|pancreatitis|copd|emphysema|cirrhosis|kidney failure|heart failure|"
    r"brain (?:damage|injury)|cerebral palsy|terminal)\b",
    # "my mum is ill" is news about a person the way "my dad has parkinsons" is, and it was
    # answered "I'm sorry - that's frustrating", which is the word for a bus that did not come.
    # This does not claim to know what is wrong with her - "ill" can be a week in bed - which is
    # why it is here and not in `SERIOUS_NEWS`: it only keeps the one line about a setback off a
    # line about a person who is unwell. "my son is sick" and "my gran is poorly" are the same
    # news in the words people type, and a line about the person's own body ("im ill") is not
    # this pattern's: the owner has to be one of their people.
    rf"\b{CONDITION_OWNER}\b[^.!?]{{0,24}}\b(?:is|are|was|were|has been|have been|had been|"
    rf"got|getting|become|becoming|been)\b[^.!?]{{0,16}}"
    r"\b(?:ill|poorly|unwell|not well|off (?:it|colour|their food)|in a bad way|"
    r"taken ill|gone downhill|deteriorat\w+)\b",
    # "my dad was diagnosed with motor neurone": the diagnosis is the news, and the person can be
    # the subject or the object of it. "diagnosed" alone is enough for the clause to be about
    # somebody, because nobody is diagnosed with anything they can shrug off.
    rf"\b{CONDITION_OWNER}\b[^.!?]{{0,24}}\bd(?:iagnos\w+|x\b)",
    r"\b(?:been|being|just|newly|recently)\s+(?:diagnos(?:ed|is)\w*)\b",
    # Being kept from your own children is not a small fact, and it was answered "I'm listening -
    # say more if it helps" and, with a husband as its subject, with the domestic abuse lines. The
    # child has to be there and a word of being kept away has to be there, in either order, so
    # "i cant see the tv", "i cant see the problem" and "i cant see him tonight" stay ordinary.
    r"\b(?:not allowed|no longer allowed|allowed|banned|barred|stopped|prevented)\b"
    r"[^.!?]{0,24}\b(?:see|seeing|visit|visiting|contact(?: with)?)\b[^.!?]{0,20}"
    r"\b(?:kids?|children|child|son|daughter|grandchild\w*|baby)\b",
    # "my ex wont let me see the kids" is deliberately not here: it is already answered by the
    # pool that offers to work out what to say to them, and the gentle pool is the blunter answer.
    # A payment or an award taken away, or refused: "my pip was refused" was answered "Oh, that's
    # a nuisance", and a benefit being stopped is the week somebody's money runs out. The award
    # has to be named, so "they cut my grass" and "my hair is cut" are not it.
    # A payment or an award taken away, or refused: "my pip was refused" was answered "Oh, that's
    # a nuisance", and a benefit being stopped is the week somebody's money runs out. The award
    # has to be named, so "they cut my grass" and "my hair is cut" are not it. The patterns are in
    # `AWARD_LOST`, above, because the award is the one shape with a service behind it.
    *AWARD_LOST,
    # Having to give up the home: "i have to sell the house" was answered "Thanks for telling me -
    # I'm here if you want to dig into any of that". The verb has to be one nobody picks ("want to
    # sell the house" is a decision, and plans have their own pool) and the thing has to be the
    # roof: a car, a bike and a spare set of golf clubs are for sale without a life in them.
    # "leave" is not here: "i have to leave the house at 7" is the school run, and a home given up
    # in the other words is read by the eviction and the rent patterns above.
    r"\b(?:have|has|had|having|got|gotten|getting|being (?:forced|made))\s*(?:to\s+)?"
    r"(?:sell|give up|hand back|move out of)\b[^.!?]{0,24}"
    r"\b(?:the|our|my|his|her)\s+(?:house|home|flat|bungalow|place)\b",
    # A letter from a court or a bailiff, and a notice to quit: "i got a letter about a court date"
    # was answered "Go on then - what was the answer?", which heard the news as a riddle. The
    # letter has to have arrived (a verb of receiving), so "when do i get a court date" is still a
    # question about a date, and the legal thing has to be named, so "i got a letter about the
    # boiler" is still a warranty.
    # "got" and not "get": "when do i get a court date" is a question about a date, and the same
    # verb in the present is the one somebody writes while waiting for it to arrive.
    # A court date is not always a hard week, and the reading above cannot tell: "im going to court
    # to adopt my daughter" is the best day of someone's year and was answered "Sorry to hear that".
    # So the whole court family stands aside where the line is about an adoption (see
    # `ADOPTION`), and the warm line the words already had takes it back.
    rf"(?!.*{ADOPTION_WORDS})\b(?:got|gotten|had|received|been sent|sent me|sending me|came through|arrived)\b"
    r"[^.!?]{0,28}\b(?:court (?:date|letter|order|summons|hearing)|summons|notice to quit|"
    r"eviction notice|possession (?:claim|order)|letter before (?:claim|action))\b",
    # Bailiffs at the door are never the ordinary word: "the bailiffs turned up" has no letter in
    # it and needs nothing beside it to be the week a home is at risk.
    r"\bbailiffs?\b",
    # Going to court rather than reading a letter about it: "i am going to court next week" was
    # noted back at the person, and "they are taking me to court" got "Got it. Is there anything
    # you'd like a hand with?". The verb has to be one of going or being taken and the legal thing
    # has to be named, so "when do i go to court" and "what happens at a court hearing" are still
    # questions, and "i am going to town" is a bus.
    rf"(?!.*{ADOPTION_WORDS})\b(?:going|have to go|has to go|got to go|due|off)\s+(?:in |to |before )?court\b",
    r"\b(?:taking|took|taken|summoned|prosecuting|suing)\s+(?:me|us|him|her|them)\s+to court\b",
    # The same thing said in the passive, which is how most people say it: "im being taken to
    # court" has no object after the verb, so the pattern above walks past it and the line got
    # "Got it. Is there anything you'd like a hand with?". The being has to be the person's own,
    # so "he is being taken to court" is somebody else's week and stays theirs.
    r"\b(?:i'?m|im|i am|we'?re|we are|i was|we were)\s+(?:being\s+)?(?:taken|summoned|"
    r"prosecuted|sued)\s+(?:to|into|before)\s+court\b",
    r"\b(?:hearing|trial|case)\s+(?:is |was )?(?:next|this)\s+(?:week|month|monday|tuesday|"
    r"wednesday|thursday|friday|morning|afternoon)\b",
    # Sentencing and prison are the same hard week, said one step later. The verb of being inside
    # has to be the person's or their own, so "im going to prison in june" reads and "how do you
    # become a prison officer" does not.
    r"\b(?:going|went|moved|transferred|have to go|has to go|got to go|off|sent|"
    r"sentenced|remanded|due)\b"
    r"[^.!?]{0,16}\b(?:to |in |into )?(?:prison|jail|young offenders)\b"
    # ... unless the going was a visit or a day out: "my son went to prison to see his mate" is an
    # afternoon, and so is a museum.
    r"(?!\s+(?:to\s+(?:visit|see|meet)|visiting|museum|tour|open\s+day))",
    # Somebody already inside, which is how a person talks about a brother or a friend: "my brother
    # is in prison" was noted back at them as if it were a fact about the weather. The person has
    # to be named and the place has to be the sentence, so "there is a prison up the road" and
    # "the prison was on the news" stay ordinary.
    r"\b(?:is|are|was|were|been|being|stays?|sits?|sitting|kept|held|locked)\s+"
    r"(?:up\s+|inside\s+|away\s+)?(?:in|at|inside)\s+(?:the\s+)?"
    r"(?:prison|jail|jailhouse|young offenders|pentonville|wormwood scrubs|brixton|wandsworth)\b",
    # "Sent down" is the usual British way to say sent to prison, and it is a sentence only when a
    # term follows it: "i sent my son down to the shop" keeps the shop.
    r"\bsent down\b[^.!?]{0,16}\b(?:for|to)\s+(?:\d+|two|three|four|five|six|seven|eight|"
    r"nine|ten|twelve|eighteen|twenty|a\s+(?:year|month|stretch|while)|life)\b",
    # The same words in the passive, where nobody says the term: "my son has been sent down".
    # The auxiliary has to sit straight before "sent", so "i sent my son down to the shop" and
    # "she sent the parcel down the chute" keep their own line.
    r"\b(?:was|were|is|are|been|being|got|gets|getting|keeps being)\s+sent down\b",
    # A child taken into care: "my daughter has been taken into care" was answered "Noted: your
    # daughter has been taken into care", which files away the worst week of a parent's year. The
    # phrase is a removal and not care in general, so "she took care of it" and "my son is in
    # childcare" stay ordinary, and a child has to be there for the second shape, so "my bag was
    # taken from me" is not a child being taken.
    r"\b(?:taken|took|put|puts|removed|removes)\b[^.!?]{0,20}\b(?:into care|in care)\b",
    rf"\b(?:taken|took|removed)\b[^.!?]{{0,24}}\b(?:my|our|the)\s+"
    rf"(?:kids?|children|child|son|daughter|baby)\b[^.!?]{{0,16}}\baway\b",
    r"\bsocial services\b[^.!?]{0,24}\b(?:took|taken|removed|involved|came)\b",
    # The roof going, before any letter arrives: "we are losing the flat" was "I'm listening - say
    # more if it helps" and "we are losing the house" was the stock ack. The thing lost has to be
    # a home, so "ive lost my keys" and "losing my mind" stay ordinary.
    r"\b(?:losing|lose|lost|going to lose|about to lose|might lose|will lose|going to be losing)\b"
    r"[^.!?]{0,12}\b(?:the|our|my)\s+(?:house|home|flat|bungalow)\b",
    # Being sacked, which the redundancy words in `BAD_NEWS_ITSELF` do not cover: "i got sacked"
    # was answered "Noted: you got sacked". The verb of losing the job has to be there, so "i got a
    # warning" and "i got the job" are not it.
    r"\b(?:got|get|getting|been|being|was|were)\s+sacked\b",
    # News named as news and nothing else: "i got some bad news" was answered "Nice one. How did
    # the rest of it go?" and "i have bad news" "Noted: you have bad news". What the news is about
    # is what the pools below sort out, and a friend's first move is the same whatever it turns
    # out to be, so the words that name it are enough. "not bad news" is the good pair and is left
    # alone.
    r"\b(?:bad|sad|awful|terrible|dreadful|grim|rotten|horrible|horrid)\s+(?:news|tidings)\b",
))

# Everything a reader of "is this line news?" needs, in one place, for the two callers that only
# want to know whether to be gentle about the line and whether to echo it.
BAD_NEWS = BAD_NEWS_ITSELF + NEWS_WITH_A_NAME


def reads_as_an_award_lost(clean):
    """Whether the line is a benefit, a pension or a wage stopped, refused or cut.

    The one shape of named news that a service can settle, so the caller that has a pointer to that
    service asks this before it chooses the gentle line.
    """
    return any(pattern.search(clean) for pattern in AWARD_LOST)


def reads_as_a_sacking(clean):
    """Whether the line is somebody losing their job, and nothing else.

    One caller: the stand-down in `compose.step_when_low`. Every other kind of news has an entry
    or a card behind it, so the ask that follows it is better answered there - "bailiffs turned
    up" then "what do i do" reaches what to do about the bailiffs. A sacking has no such entry,
    and the ask then landed on "There is nothing in this to look up. Tell me what has to happen
    next", a shrug at somebody who has just lost their job. The step pool was the answer to that
    ask before the news reading existed, and it is a better one than the shrug.
    """
    return bool(re.search(SACKED_FIRED, clean))


def reads_as_news_with_a_name(clean):
    """Whether the line is the news that has a name in it, rather than the medical list.

    One caller: the gentle pool for a dad with parkinsons or a roof that has to go drops the line
    that calls it frustrating (`fallback.NAMED_NEGATIVE`), because the smallest of the four words is
    the wrong register for a person. Everything else that asks "is this news" asks
    `reads_as_bad_news`, which reads both lists.
    """
    return any(pattern.search(clean) for pattern in NEWS_WITH_A_NAME)


def reads_as_heavy_news(clean):
    """Whether a line is news that a bare ask after it would be asking about.

    The medical list only, on purpose: the news in `NEWS_WITH_A_NAME` - a refused payment, a court
    letter, a house on the market - is news a person can still ask a plain question after, and the
    reader that stands the ask pool down (`_news_above`) asks this rather than `reads_as_bad_news`.
    """
    return any(pattern.search(clean) for pattern in BAD_NEWS_ITSELF)


# A door that keeps closing on the person's work: nobody will hire them, the interviews do not
# come. It is not bad news in the medical sense and the gentle pool ("ugh, that's a lot to
# carry") is the wrong voice, but the stock nod is colder still. The words are work words, so
# "nobody will tell me whats wrong with the boiler" stays a question, and "nobody will hire a
# plumber at christmas" is about the plumber, not the person.
CLOSED_DOOR_LINES = (
    r"\b(?:nobody|no\s?one|none of them|not one)\s+(?:will|would|wants? to|is willing to|"
    r"has|have|ever)\s+(?:\w+\s+){0,3}?(?:hire|employ|interview|"
    r"take (?:me|him|her|us|them) on|give (?:me|him|her|us|them) a (?:chance|look|shot|start))\b"
    r"(?=\s*(?:$|[,.!?]|(?:me|him|her|us|them|someone|anyone|people|at my age)\b))",
    # "nobody gets back to me": the application goes out and the silence comes back.
    r"\b(?:nobody|no\s?one)\s+(?:(?:gets?|has|have|ever)\s+(?:got|gotten)?\s*back to)\s*(?:me|him|her|us)\b",
    r"\b(?:nobody|no\s?one)\s+(?:ever\s+)?(?:gives?|gave|will give|would give)\s+(?:me|him|her|us)\s+(?:a\s+)?(?:chance|look|shot|start|break)\b",
    r"\b(?:can'?t|cannot|cant|struggling to|never)\s+(?:get|land|find|even get)\s+"
    r"(?:an? )?(?:interview|job|work|reply|response|answer|call ?back)\b",
    # "im too old to get a job" and "im 52 and nobody will interview me": the age is the reason
    # they give, so it counts beside the work word rather than on its own ("im too old for this").
    r"\btoo old\b[^.!?]{0,40}\b(?:job|jobs|work|hire|hired|interview|employ|employer)\b",
    r"\b(?:job|jobs|work|hire|hired|interview|employer)\b[^.!?]{0,30}\btoo old\b",
    r"\b(?:turned down|rejected|knocked back)\b[^.!?]{0,20}\b(?:again|for (?:the|a) "
    r"(?:job|role|position|interview))\b",
)

# The subject has to be work for the shapes above to mean a closed door. "i cant get a reply"
# and "i cant get an answer" are somebody else's job - the council, a landlord, a warranty - and
# those lines have their own entries; only a work word in the same line makes the silence a door.
CLOSED_DOOR_WORK = re.compile(
    r"\b(?:job|jobs|work|working|hire|hiring|hired|interview|interviews|application|applications|"
    r"applied|apply|applying|role|roles|position|positions|employer|employers|employ|employed|"
    r"recruit\w*|career|careers|shift|shifts|cv|vacanc\w*|prospects?)\b")

CLOSED_DOOR = tuple(re.compile(pattern) for pattern in CLOSED_DOOR_LINES)

# Some doors are the work word: "take me on" is what a firm or a garage does, and a person writing
# "nobody will take me on" has no other work word to give, so the guard above rejected the shape
# that was written for it and the line kept the stock nod. Only the idioms that cannot mean
# anything else go here - "give me a chance" is left out on purpose, because "no one will give me
# a chance" is as often about dating or about being forgiven, and the reply it earns names work.
CLOSED_DOOR_WORK_OWN = re.compile(
    r"\b(?:take|takes|took|taken|taking)\s+(?:me|him|her|us|them)\s+on\b"
    r"(?=\s*(?:$|[,.!?]|(?:again|as|at|last|this|for|because|but|and)\b))")

# "cant get an interview" has no subject in it of its own, so it matches whether the person is
# talking about themselves or about somebody else, and the pool then asks the speaker what work
# they are after: "he cant even get an interview" is their son's door, not theirs. That shape
# counts only when nobody else in the line is its subject. A first-person word is not required,
# because people write it without one ("cant even get a job these days").
CLOSED_DOOR_ELSEWHERE = re.compile(
    r"\b(?:he|she|they|him|her|them|his|their|"
    r"my (?:son|daughter|child|kid|husband|wife|partner|boyfriend|girlfriend|mum|mom|mam|dad|"
    r"father|mother|brother|sister|friend|mate|flatmate|neighbour|neighbor|colleague|carer))\b")
CLOSED_DOOR_ELSE_OWN = (False, False, False, True, False, False, False)


def reads_as_a_closed_door(clean):
    """Whether a cleaned, lowercased line is the person being turned away from work."""
    if not (CLOSED_DOOR_WORK.search(clean) or CLOSED_DOOR_WORK_OWN.search(clean)):
        return False
    for pattern, else_owns_it in zip(CLOSED_DOOR, CLOSED_DOOR_ELSE_OWN):
        if not pattern.search(clean):
            continue
        if else_owns_it and CLOSED_DOOR_ELSEWHERE.search(clean):
            continue
        return True
    return False


# A fit that a laugh brought on is a joke about a fit, not a fit: "i had a seizure laughing at
# that video", "i nearly collapsed laughing". The span is short on purpose, so a real collapse
# with a laugh in the next sentence still counts.
JOKED = re.compile(r"\b(?:seizures?|choking|strokes?|heart attacks?|collapsed|passed out)\b"
                   r"[^.!?]{0,14}\b(?:laughing|giggl\w*|cracking up|in stitches)\b")


VOWELS = frozenset("aeiou")

# Words of their own one letter from one of those, which no typo rule may claim: a strike at
# work is not a stroke, the day off it costs is not news of an illness, and stroking a cat is
# not a stroke. The other collisions people type every day are dropped by the rule in _one_edit
# below, and by the everyday words of the engine's own vocabulary ("hospital", "bleeding").
NOT_A_TYPO = frozenset(("strike", "stroked", "strokes", "stroking", "collapse"))


def _nearly(word):
    """Whether `word` is an emergency word with one letter typed wrong."""
    if len(word) < 6 or word in NOT_A_TYPO:
        return False
    for target in NEARLY:
        if word == target or abs(len(word) - len(target)) > 1:
            continue  # the word itself is the patterns' job, not the typos''
        if word in LEXICON:
            continue  # an everyday word is never a misspelling of one of these
        if _one_edit(word, target):
            return True
    return False


# "a lump in my throat" is a feeling and "a lump sum" is money: the word after the lump is what
# says which, so every pattern that reads a lump carries the same guard. See `SICK`.
# ...unless the same line also says the throat is not working - "and i cant swallow", "lost my
# voice", "it hurts to breathe" is a symptom the idiom never carries, and the GP line is too weak
# for it either, so it keeps the symptom reader.
LUMP_NOT_A_LUMP = (r"(?![\s-]+(?:sums?|of|sugar)\b)"
                   r"(?!\s+in\s+(?:my|your|his|her|their|our|the)\s+throat\b"
                   r"(?![^.!?]*\b(?:swallow|swallowing|voice|breath|breathing|breathe)\b))")

# What a person says when their body is the problem. Not an emergency and not a fact to note:
# "i've got a sore throat" wants a warm line, and "you've got a sore throat - noted" is the one
# reply a friend would never give. The body has to be in the line ("sore" alone is not), and
# "i'm cold" is the weather, so "cold" needs the article ("i've got a cold").
# The parts people name to a stranger when they hurt, in the words they use. The list is the
# reading's whole subject, so a part that is missing is a line nobody answers: "my jaw is agony
# in the mornings", "my lips have gone puffy and red since last night" and "my forehead feels
# hot" all fell past every pattern here and were handed back ("Got it. Is there anything you'd
# like a hand with?") while "my throat is sore" was answered. A part on the list does nothing on
# its own - every pattern still needs a word that says it hurts - so the cost of a part that
# should not be here is a hedge, and the cost of one that is missing is a person with a
# symptom who is asked what they would like help with.
BODY = (r"(?:head|throat|ear|ears|eye|eyes|tooth|teeth|back|knee|shoulder|arm|leg|legs|foot|feet|"
        r"hand|hands|stomach|tummy|chest|neck|hip|ankle|wrist|elbow|toe|finger|skin|nose|sinus|"
        r"jaw|jaws|cheek|cheeks|chin|lips?|tongue|gums?|mouth|face|forehead|temple|temples|"
        r"scalp|spine|ribs?|shins?|calf|calves|thighs?|groin|kidneys?|bladder|nails?|heels?|"
        r"palms?|soles?|thumbs?|")
BODY = BODY[:-1] + ")"

# The parts a body's trouble is said of - a joint, a limb, a bone. "my wife has a bad back" is a
# back that has been giving trouble, and the carer's answer is the gentle one: keep them moving,
# ask how it is slowing them up. The parts below are the ones the word "bad" cannot mean an
# illness with, which is what makes them a separate list.
HURTS = (r"(?:back|knee|knees|hip|hips|shoulder|shoulders|arm|arms|leg|legs|foot|feet|ankle|"
         r"ankles|wrist|wrists|elbow|elbows|neck|hand|hands|rib|ribs|shin|shins|calf|calves|"
         r"thigh|thighs|spine|jaw|heel|heels|thumb|thumbs|toe|toes|finger|fingers|"
         r"hip|knees|joints?)")
# And the parts where "bad" means the illness that part catches, not a hurt: a bad chest is a
# chest infection, a bad throat a sore throat, a bad ear an ear infection. British usage, and the
# one that matters - "is anything helping at all, heat, a cushion, taking it gently" is advice for
# a joint and nonsense for a chest.
ILL_PART = (r"(?:chest|throat|stomach|tummy|head|ear|ears|earache|tooth|teeth|toothache|nose|"
            r"sinus|eye|eyes|gums?|mouth|cheek|cheeks)")
SICK = (r"(?:sore|cough|coughing|headache|migraine|toothache|earache|rash|itchy|itching|"
        r"infection|infected|cramps?|nauseous|nausea|dizzy|swollen|swelling|aching|aches?|"
        r"throw up|throws up|threw up|throwing up|vomit\w*|constipated|bloated|diarrhoea|"
        r"diarrhea|unwell|poorly|sick|temperature|flu|"
        r"migraines|"
        # A lump is the thing people most often ask about and the one a stock "noted" answers
        # worst: "i found a lump in my breast" was noted back to them. Not a lump sum and not a
        # lump of butter, which are the same word in a kitchen and a bank.
        r"lumps?" + LUMP_NOT_A_LUMP + r"|growths?)")
# Both spellings of every contraction: people type "ive got a cold" and "i've got a cold", and
# normalise keeps whatever apostrophe they used. `'ve` / `ve` are the same words.
IWE = r"\b(?:i|we)(?:'ve|ve|'m|m| have| am| feel| felt| got| keep| woke up with)\b"
# What a part is doing when it is the trouble. One list, used by every reading here that needs a
# part plus a word: the four places used to carry four slightly different lists, so "my jaw is
# agony" matched nothing, "my leg is hurting" matched nothing, and the same words in a different
# order might match or not depending on which pattern the reader happened to reach. A hurt is
# said as pain (hurts, agony, killing me, tender), as a shape the part is in (swollen, puffy,
# stiff) or as heat (burning, hot) - and those are the three groups below.
HURT = (r"hurts?|hurting|aches?|aching|sore|pain|painful|agony|agonising|agonizing|"
        r"killing me|is killing me|are killing me|tender|raw|"
        r"swollen|swelling|puffy|stiff|throbbing|itchy|itches|"
        r"burning|on fire|hot|bad")
SYMPTOM = (
    re.compile(IWE + r"[^.!?]{0,25}?\b" + SICK, re.I),
    re.compile(r"\bmy " + BODY + r"\b[^.!?]{0,15}?\b(?:" + HURT + r")\b", re.I),
    # "i throw up every morning", "i vomit after every meal": the verb is the whole complaint and
    # there is no "have" or "am" in front of it, which every pattern above expects.
    re.compile(r"\b(?:i|we)\s+(?:throw\w* up|vomit\w*|(?:am|are|'m|'re)?\s*being sick)\b", re.I),
    re.compile(r"\b(?:my|a|the)\s+(?:stiff|sore|bad|dodgy|aching|swollen|gammy|sore)\s+" + BODY,
               re.I),
    # An upset stomach is said as a phrase far more often than with a symptom word, and every
    # word in it says something else alone: "the runs" is running, "guts" is courage, "dicky" is
    # a bird and "trots" are steps. "i have an upset stomach" was answered "what would make
    # today a bit easier", and "i keep running to the loo" with advice on a dripping cistern.
    # It is the speaker's own body, so the subject has to be i/we: "hes got the runs" is a pet's
    # or a child's line and gets the answer that is right for whoever it is about.
    re.compile(IWE + r"[^.!?]{0,30}?\b(?:the runs|the trots|the squits|bad guts|bad belly|"
               r"dicky (?:tummy|stomach)|dodgy (?:tummy|stomach)|upset (?:tummy|stomach)|"
               r"(?:tummy|stomach|sick) bug|food poisoning|being sick|keep(?:t|s)? being sick|"
               r"can'?t? keep anything down|loose stools|runny (?:tummy|bottom)|"
               r"running to the (?:loo|toilet))\b", re.I),
    # "my stomach is off" names the body first, so it needs the other word order: the body, then
    # what it is doing, with no verb in between.
    re.compile(r"\bmy (?:stomach|tummy|belly|guts)\s+(?:is |feels |has been )?"
               r"(?:off|queasy|bad|dodgy|playing up)\b", re.I),
    # "i found a lump" is how people say this, and `found` is none of the verbs the first
    # pattern knows ("i've got", "i have", "i feel"): the one line that most needs an answer was
    # noted back to them ("Noted: you've got a lump in your throat").
    re.compile(r"\b(?:i|we)\s+(?:found|felt|noticed|spotted)\b[^.!?]{0,20}?"
               r"\b(?:lumps?|growths?)\b" + LUMP_NOT_A_LUMP, re.I),
    # "i've got a cold" says `got` between the verb and the article, which the first pattern
    # cannot see past because `cold` is not in SICK: it needs its own article ("i'm cold" is
    # the weather).
    re.compile(r"\b(?:i|we)(?:'ve|ve|'m|m| have| am)?\s*(?:got|had|been|felt|feel)?\s*"
               r"(?:a|an|the)\s+(?:bad |nasty |chesty |sore )?"
               r"(?:cold|cough|temperature|sore throat|rash|migraine|headache|infection)\b",
               re.I),
)
# The shortest way of saying "this hurts" is the name of the thing on its own: "toothache", "sore
# throat", "bad back", "stomach ache", "migraine". Every pattern above wants a possessor ("my
# back") or a verb ("i've got a sore throat"), so the way people actually type it - the whole
# line being the thing that hurts - matched nothing and got the shrug, while the same thing with
# three words in front of it ("my throat is sore") got the warm line. There is no other reading
# of a bare ailment typed into a chat: nobody names a tooth to the bot except to say it hurts.
# The list that may stand in the line is closed on purpose, so a question about a thing
# ("sore throat remedies", "toothache help") stays a question and is answered as one.
BARE_ACHE = re.compile(r"\b\w*aches?\b", re.I)  # toothache, earache, backache, headaches
BARE_ILL = re.compile(r"\b(?:migraines?|heartburn|indigestion|tonsillitis|sciatica|cystitis|"
                      r"gout|sinusitis)\b", re.I)
BARE_BODY = re.compile(r"\b" + BODY + r"\b", re.I)
BARE_HURTS = re.compile(r"\b(?:" + HURT + r"|dodgy|constant|dull)\b", re.I)
BARE_FILLER = frozenset("""
oh ugh urgh god gosh really very so proper right left both top lower upper my me a an the this
that and but also still now just actually honestly awful terrible nasty bad little bit of on off
im i ive had got since yesterday today tonight morning night all day days weeks week now too
the worst ever
""".split())
BARE_WORD_ONLY = re.compile(r"\b(?:is|are|was|were|have|has|had|got|get|feel|feeling|been|do|does|"
                            r"did|can|could|should|would|will|helps?|stop|stopping|cure|treat|"
                            r"remedy|remedies|take|need|want|make|makes|go|going|come|came|"
                            r"keep|keeps|said|says|tell|think|know|why|what|how|when)\b", re.I)


def reads_as_a_bare_ailment(clean):
    """Whether the whole line is just the name of something that hurts.

    "toothache", "sore throat", "bad back", "stomach ache", "stiff neck", "migraine", and the
    same with a filler or two around it ("ugh toothache", "really sore throat"). The line has to
    name an ache or an illness by itself, or a body part together with the word that says it
    hurts: "my back" alone is not a complaint, and "sore throat remedies" is a question about a
    remedy, which its words this reading does not allow.
    """
    if not isinstance(clean, str) or not clean.strip() or "?" in clean:
        return False
    if BARE_WORD_ONLY.search(clean):
        return False
    words = re.findall(r"[a-z']+", clean.lower())
    if not words or len(words) > 5:
        return False
    named = bool(BARE_ACHE.search(clean) or BARE_ILL.search(clean))
    if not named and not (BARE_BODY.search(clean) and BARE_HURTS.search(clean)):
        return False
    for word in words:
        if word in BARE_FILLER:
            continue
        if (BARE_ACHE.fullmatch(word) or BARE_ILL.fullmatch(word)
                or BARE_BODY.fullmatch(word) or BARE_HURTS.fullmatch(word)):
            continue
        return False
    return True


# Someone the person looks after. Their line is about that person's body, not their own, and the
# reply goes to the one doing the looking after: "my child has a rash" at nine in the evening is a
# parent who wants to know whether to ring someone, not "take it slow today".
# A child is named by an age as often as by a word: "my 4 month old has a rash" is the same
# line as "my baby has a rash", and the reader only knew the second. The age counts only with
# a word for the child after it or with the year, because "my 4 month old dog" is the vet's
# line and "my 11 month old puppy has a cough" must not be read as a parent's.
AGE_CHILD = (r"(?:(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
             r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|a|an)"
             r"[\s-]+(?:month|months|week|weeks|year|years)[\s-]+old"
             r"(?:[\s-]+(?:baby|boy|girl|son|daughter|child|kid|toddler|little one))?)")
KIN = (r"(?:mum|mom|mother|mam|dad|father|gran|granny|grandma|grandad|grandpa|nana|nan|"
       r"son|daughter|child|kid|baby|boy|girl|toddler|teenager|little one|wife|husband|"
       r"partner|boyfriend|girlfriend|fiance|fiancee|brother|sister|uncle|aunt|" + AGE_CHILD + r")")
# An animal is looked after too, and in the same words ("my dog has a cough"), but the one who
# settles it is the vet: "keep them comfortable and ring 111" is advice for a child, and a joke
# about a cat, so the animal is read separately and answered by the vet's line.
PETS = (r"(?:dog|puppy|cat|kitten|horse|pony|rabbit|hamster|guinea pig|gerbil|ferret|budgie|"
        r"parrot|bird|tortoise|snake|lizard|chicken|hens?|goat|sheep|pig|pet)")
# The illness words a carer uses about someone else, which SICK does not carry: a child has
# chickenpox, croup, a tummy bug or a temperature.
# "sore" is only an illness with a part after it: a cold sore is not one, and a bare "sore" on a
# carer line is as likely to be the noun.
# A carer often has no word for the illness, only what they can see: "my daughter is pale but
# playing", "my son is flushed", "my daughter is clammy", "my son looks washed out". None of those
# was a symptom word, so the line was filed away - "Noted: your daughter is pale but playing." -
# while the signs that are emergencies (grey, blue, floppy, burning up) already had their own
# cards. These are the ones the carer's line is written for: it asks whether they are drinking,
# what has changed and who to ring, which is what a friend says about a child who is off colour.
# Shivering and sweating are not here: a child who is shivery is a temperature to take rather than
# a child to watch, and the temperature reading answers those two.
CARED_SIGN = (r"pale|pallid|flushed|clammy|listless|lethargic|washed out|off colou?r|"
              r"out of sorts|peaky|groggy|doughy|waxy|sallow|not (?:himself|herself|themselves)|"
              r"clingy|whinge?y|fractious|"
              # A child who stops being like themselves is what a carer says first: not sleeping,
              # sleeping more than usual. Only these two shapes, because "sleeping" on its own is
              # a baby who is asleep and nothing to answer.
              r"not sleeping|sleep(?:ing (?:a lot|more|all the time)|ier)|"
              r"off (?:his|her|their) (?:food|bottle|drink)")
CARED_SICK = (r"(?:sore\s+(?:throat|head|tummy|ear|ears|back|arm|leg|legs|foot|feet|hand|"
              r"knee|chest|neck|tooth|mouth)|cough|coughing|headache|migraine|toothache|"
              r"earache|rash|itchy|itching|"
              r"infection|infected|cramps?|nauseous|nausea|dizzy|swollen|swelling|aching|aches?|"
              # "vomits" and "throw up" are how people say it at a set time of day - "my dad
              # vomits every morning" - and only the -ing forms were listed.
              r"throw\w* up|throw up|vomit\w*|being sick|diarrhoea|diarrhea|unwell|poorly|"
              # "a sick note", "sick pay" and "sick of it" are not an illness
              r"sick(?!\s+(?:note|pay|days?|leave|of|bag|joke|sense))|temperature|fever|flu|"
              r"bugs?|"
              # "a cold" is the bug; "a cold sore", "cold hands" and "cold feet" are not
              r"cold(?!\s+(?:sore|sores|feet|hands|fingers|toes|air|weather|room|drink|water|"
              r"days?|morning|night|outside|shoulder|call))|chickenpox|chicken pox|croup|"
              r"colic|teething|eczema|conjunctivitis|hand foot and mouth|runny nose|blocked nose|"
              r"chesty|sniffles?|nits|head lice|worms|thrush|migraines|" + CARED_SIGN + r")")
# A named condition of an animal is not a symptom word, so "my cat has kidney failure" was only
# the pet tail - "how long has it been with you?" - and nothing about the illness. The conditions
# a person can have are in CARED_SICK; these are the ones people say about an animal, and the
# vet's line answers them. Kept apart from CARED_SICK because a person's chronic condition wants
# the carer's line, not the cold-and-flu advice.
PET_NAMED_CONDITION = (
    r"(?:kidney|liver|heart|lung|thyroid)\s+(?:failure|disease|problems?|trouble|condition)"
    r"|renal failure|diabet\w*|epilep\w*|heart murmur|cushing\w*|addison\w*"
    r"|pancreatitis|blocked bladder|urinary tract")


def _someone_elses_symptoms(who, sick=CARED_SICK, owner=r"my|our", named=None,
                            generic=True, body_only=False, part=None):
    """The shapes a line about somebody else being unwell takes, for the names in `who`.

    A person and an animal are described the same way ("my son has a cough", "my dog has a
    cough"), so the shapes are written once and the names passed in. What differs is who gets the
    reply, which is the caller's business; an animal can also have a named condition that a
    person's line would not be read for, so the named/possessive shape is only added when `named`
    is given. Without that fence "my son's eczema has cleared up" was read as the illness going
    on, and the pet shape asked about a rash for diabetes.
    """
    shapes = []
    if generic and not body_only:
        shapes.extend([
        # "my son has a temperature", "our daughter's got a cough", "my mum came down with a cold"
        re.compile(rf"\b(?:{owner})\s+(?:poor\s+|little\s+|eldest\s+|youngest\s+|old\s+)?"
                   # "keeps" is the connector a symptom that has hung on uses: "my wife keeps
                   # throwing up at night" and "my dad keeps vomiting" read as nothing at all.
                   rf"{who}(?:'s|s)?\s+(?:has|have|had|got|has got|keeps getting|keeps|kept|"
                   rf"keep|came down with|come down with|is|was|been|looks|seems)\b"
                   rf"[^.!?]{{0,30}}?\b(?:{sick})\b", re.I),
        # "my dad vomits every morning", "my wife throws up after meals": the verb itself is the
        # connector. Illness shapes only: a sickness is not a body part, and CARER_BODY read this
        # as somebody's bad back, answering vomiting with "is it slowing them up getting about?".
        re.compile(rf"\b(?:{owner})\s+{who}\s+(?:{sick})\b", re.I),
        ])
    if generic:
        shapes.extend([
        # "my mum's knee is swollen", "my sons ear hurts", "my daughters back is sore"
        re.compile(rf"\b(?:my|our)\s+{who}(?:'s|s)\s+{BODY}\b[^.!?]{{0,18}}?\b"
                   r"(?:" + HURT + r"|infected|playing up)\b", re.I),
        # "my wife has a bad back", "my dad has a gammy knee": the qualifier is what makes the
        # body part the trouble rather than a replacement, a brace or an appointment about it.
        # "has got" is the same shape said the long way, and it is the shape the reading hands
        # on: a hurried "me mums got a bad chest" is repaired to "my mum has got a bad chest",
        # which matched neither "has a bad" nor "got a bad" - the possessive was already fixed
        # and the verb was still in the way, so the person's own body took a line about their
        # mother. The possessive tolerates the plural for the same reason ("my mums got ...").
        re.compile(rf"\b(?:{owner})\s+{who}(?:'s|s)?\s+(?:has|have|had|got)(?:\s+got)?\s+(?:a|an)?\s*"
                   r"(?:bad|sore|dodgy|gammy|weak|dicky|knackered|broken|cracked|twisted|swollen|"
                   rf"stiff|aching)\s+{part or BODY}\b", re.I),
        ])
    if named:
        # The animal is named or called something, or the condition is said with a possessive:
        # "my cat milly has kidney failure", "my dog called rex has diabetes", "my cat's kidney
        # failure is getting worse". Only animals get this shape: the same words about a person
        # ("my son's eczema has cleared up") are news about a person, not a symptom to answer.
        shapes.append(
            re.compile(rf"\b(?:{owner})\s+(?:poor\s+|little\s+|eldest\s+|youngest\s+|old\s+)?"
                       rf"{who}(?:'s|s)?\b[^.!?]{{0,24}}?\b(?:{named})\b", re.I)
        )
    return tuple(shapes)


# A parent can name the child by their age instead of by a word: "my 4 month old has a rash" is
# "my son has a rash", and no word in the line stands for the child, so the shapes above cannot
# see them and the line was answered as if the person had merely said something. The verb straight
# after the age is what keeps it a person who is unwell - a word that names something else there
# ("my 6 month old dog has a cough", "a 10 week old kitten") is the thing the age is of, and the
# animal's line is the vet's.
AGE_NUMBER = (r"(?:\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
              r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|"
              r"forty|fifty|sixty)")
CHILD_BY_AGE = re.compile(
    rf"\b(?:my|our|the|his|her|their)\s+(?:little\s+|poor\s+|tiny\s+|new\s+)?{AGE_NUMBER}"
    rf"\s*-?\s*(?:month|months|mth|mths|week|weeks|wk|wks|year|years|yr|yrs)\s*-?\s*old\s+"
    rf"(?:has|have|had|got|keeps\s+getting|came\s+down\s+with|is|was|been|looks|seems)\b"
    rf"[^.!?]{{0,30}}?\b(?:{CARED_SICK})\b", re.I)

# The people a person looks after: "my child has a rash" is a parent worried at nine in the
# evening, and the reply is for the carer.
# The parts a body's "bad" is spoken of - a chest, a throat, an ear - are the illness a part
# catches, so they are the carer's illness lines; `CARER_BODY` below is the joints. Appended to
# the shapes main already reads rather than replacing them, so a child named by age still counts
# as the carer's. See `_someone_elses_symptoms`'s `part=`.
CARER_SYMPTOM = (_someone_elses_symptoms(KIN) + (CHILD_BY_AGE,)
                 + _someone_elses_symptoms(KIN, generic=False, body_only=True, part=ILL_PART))
# The same lines when what is wrong is a body rather than an illness: "my wife has a bad back" is
# not a cough, and the carer's illness lines ("plenty to drink and let them rest", "ring 111 if
# that changes") are written for a child with a temperature. A hurt that has been there a while
# wants a gentler answer, one that asks about them and keeps them moving, so it gets its own pool.
CARER_BODY = _someone_elses_symptoms(KIN, body_only=True, part=HURTS)
# The animals they look after: the same shapes, and the vet's line.
PET_SYMPTOM = _someone_elses_symptoms(PETS, CARED_SICK + "|" + PET_NAMED_CONDITION,
                                       owner=r"my|our|the", named=PET_NAMED_CONDITION)
# A low mood in an animal is not a mood to mirror. "i think my cat is depressed" and "my dog is
# depressed" reached the day pools, which answered "Good to hear. What was the best bit?" and
# "How was it, overall?" - a cheer at a worry about a pet. A cat that goes quiet or a dog that
# stops wanting walks is often ill or in pain, so the vet comes first and the composer's own
# low-pet pool says so. Kept apart from CARED_SICK because "my mum is sad" is a person's feeling
# and must not become a symptom.
PET_LOW = (r"(?:depressed|sad|unhappy|miserable|withdrawn|lethargic|listless|moping|mopey|"
           r"not\s+(?:him|her|them)sel(?:f|ves)|off\s+(?:his|her|their)\s+food|"
           r"gone\s+quiet|hiding|not\s+eating|won'?t\s+eat)")
PET_LOW_SYMPTOM = _someone_elses_symptoms(PETS, PET_LOW, owner=r"my|our|the")
# The same lines when the news is a named condition rather than a symptom: the vet is still the
# one to ask, but the shape question ("is it on one side, or all over?") is a question about a
# lump or a rash, not about diabetes.
# Only the named shape: a body part is a symptom ("my cat has a gammy leg"), not a condition,
# and the named shape's diagnosis question is wrong for it. The generic shapes have already
# reached PET_SYMPTOM, and the trouble pool is the one written for a lump or a bad leg.
PET_CONDITION = _someone_elses_symptoms(PETS, PET_NAMED_CONDITION, owner=r"my|our|the",
                                        named=PET_NAMED_CONDITION, generic=False)
# A line that says the trouble is over is news, not a symptom to ask about: "my son's eczema has
# cleared up" was answered as if the eczema were still there. Kept to the endings a completion
# actually uses, so "my cat has gone off her food" and "my cat has gone quiet" still reach the vet.
TROUBLE_OVER = re.compile(
    r"\b(?:has|have|had)\s+gone(?:\s+now)?\s*$"
    r"|\b(?:has|have|had)\s+(?:cleared(?:\s+up)?|eased(?:\s+off)?|settled(?:\s+down)?)\s*$"
    r"|\b(?:got|getting)\s+over\s+\w+"
    r"|\b(?:is|are|was|were|feels?|feeling)\s+(?:better|fine|ok|okay|under\s+control)\b",
    re.I)


def reads_for_a_carer(clean, memory=None):
    """Whether a cleaned, lowercased line is about someone the person looks after being ill."""
    if TROUBLE_OVER.search(clean):
        return False
    if any(pattern.search(clean) for pattern in CARER_SYMPTOM):
        return True
    # "my dad is 70" then "hes got a bad hip": the second turn names nobody, and the "he" is the
    # dad the chat has just named. Read as the speaker's own body it told the person typing to
    # go easy on themselves and see someone about their father's hip.
    return False


def reads_as_a_carer_body(clean, memory=None):
    """Whether a cleaned, lowercased line is somebody else's body, rather than their illness."""
    if TROUBLE_OVER.search(clean):
        return False
    if any(pattern.search(clean) for pattern in CARER_BODY):
        return True
    # "my dad is 70" then "hes got a bad hip": the second turn names nobody, and the "he" is the
    # dad the chat has just named. Read as the speaker's own body it told the person typing to go
    # easy on themselves and see someone about their father's hip.
    if memory is not None:
        from ..memory import whose_body  # noqa: PLC0415 - the pronoun reading needs the chat
        return whose_body.somebody_elses_body(clean, memory)
    return False


def reads_for_a_pet(clean):
    """Whether a cleaned, lowercased line is about an animal of theirs being ill or hurt."""
    if TROUBLE_OVER.search(clean):
        return False
    if any(pattern.search(clean) for pattern in PET_LOW_SYMPTOM):
        return True
    return any(pattern.search(clean) for pattern in PET_SYMPTOM)


def reads_as_a_pet_low(clean):
    """Whether a cleaned, lowercased line is about an animal of theirs that seems low."""
    if TROUBLE_OVER.search(clean):
        return False
    return any(pattern.search(clean) for pattern in PET_LOW_SYMPTOM)


def reads_as_a_pet_condition(clean):
    """Whether a pet line names a condition rather than a symptom."""
    if TROUBLE_OVER.search(clean):
        return False
    return any(pattern.search(clean) for pattern in PET_CONDITION)


def reads_like_a_symptom(clean):
    """Whether a cleaned, lowercased line is the person's own body complaining."""
    clean = without_the_figure_of_speech(clean)
    if any(pattern.search(clean) for pattern in SYMPTOM):
        return True
    return reads_as_a_bare_ailment(clean)


def _one_edit(left, right):
    """Whether `left` is `right` with one letter typed wrong, the way a hurried typist does it.

    A letter dropped ("sezure"), a letter added ("chocking") or a vowel written for the vowel
    it sounded like ("hospitel") is a typo, and the same letter typed as a different consonant
    is not worth that trust: "cooking" is one letter from "choking" and "cancel" is one from
    "cancer", and reading those two as emergencies answers a curry and a gym subscription with
    sympathy. Every everyday word that a consonant apart would give is dropped by that rule,
    and the emergency words whose everyday neighbour is a vowel apart ("strike", "stroke") is
    named in NOT_A_TYPO above.
    """
    if left == right:
        return False
    if len(left) == len(right):
        different = [(a, b) for a, b in zip(left, right) if a != b]
        return (len(different) == 1 and different[0][0] in VOWELS
                and different[0][1] in VOWELS)
    short, long = (left, right) if len(left) < len(right) else (right, left)
    for index in range(len(long)):
        if long[:index] + long[index + 1:] == short:
            return True
    return False


# Two kinds of line in this family want their own words rather than the general gentle pool.
# A pregnancy that has ended, or someone who took their own life, is not "frustrating" and wants
# nothing offered: the only job is to say the loss is real. And bleeding in pregnancy is a
# same-day call to a midwife and nothing else.
# Someone taking their own life is a sudden loss whoever they were: "a boy in my class killed
# himself" is the same news as "my brother killed himself", and the relative-only list above
# missed it. The reflexive form names the person, so any of the words above will do.
SUICIDE = re.compile(
    rf"\b(?:{LIVING}|{OTHERS})\b[^.!?]{{0,26}}"
    r"\b(?:killed (?:him|her|them)sel(?:f|ves)|hanged (?:him|her|them)sel(?:f|ves)|"
    r"took (?:his|her|their) own life|committed suicide)\b"
    r"(?!\s+(?:laughing|giggling))", re.I)
SUDDEN_LOSS = tuple(re.compile(pattern) for pattern in (
    r"\bmiscarriage(?:s)?\b(?! of justice)|\bmiscarried\b",
    r"\bstill ?born\b|\bstill ?birth\b",
    # What follows the baby decides, here as in the hard-week list above: "losing the baby
    # weight" and "losing the baby belly" are a body, not a bereavement.
    r"\b(?:lost|losing|we lost) (?:the|our|her|his|their) baby\b"
    r"(?!\s+(?:weight|belly|tummy|fat|pounds?|stones?|kilos?|inches|clothes|things|stuff|"
    r"room|pram|toys?|seat|carrier|monitor|name|bag|book)\b)",
    rf"\b{LIVING}\b[^.!?]{{0,24}}\bkilled (?:him|her|them)sel(?:f|ves)\b"
    r"(?!\s+(?:laughing|giggling))",
    r"\b(?:took|taken|taking) (?:his|her|their) own life\b|\bcommitted suicide\b",
))
PREGNANCY_BLEEDING = tuple(re.compile(pattern) for pattern in (
    r"\bpregnan\w+\b[^.!?]{0,24}\b(?:spotting|bleeding|cramping)\b",
    r"\b(?:spotting|bleeding)\b[^.!?]{0,24}\bpregnan\w+\b",
))


def reads_as_sudden_loss(clean):
    """Whether a line is a pregnancy that has ended or someone who took their own life."""
    text = " ".join(str(clean or "").lower().split())
    # A dream of a death is not a death, and this reading takes the turn as it comes: "i dreamt my
    # dad died" was answered with the condolence for a death that had not happened, over the top
    # of the dream module's own answer. A death said *before* the dream ("my dad died and i dreamt
    # about him") is in the waking life and keeps this reading.
    if _dream is not None and _dream.a_dream_is_not_happening(text) \
            and not _dream.a_death_came_first(text):
        return False
    return (any(pattern.search(text) for pattern in SUDDEN_LOSS) or bool(SUICIDE.search(text))
            or reads_as_someones_death(text))


def reads_as_someones_death(clean):
    """Whether the line reports that a person or an animal has died.

    A death is not an achievement and not a fault to be talked through: "a boy in my class
    killed himself" was congratulated ("a boy" is how a birth is announced) and "someone in my
    class died" was asked what it was doing. Both readers ask this one first.
    """
    text = " ".join(str(clean or "").lower().split())
    if text in ("died", "dies", "she died", "he died"):
        # The line is only the verb, answering a question about someone who was ill.
        return True
    for found in DEATH_SAID.finditer(text):
        if _NEARLY.search(text[:found.end()]):
            continue
        if _AFTER_IT.match(text[found.end():]):
            continue
        if _subject_before(text, found.start(), found.group(0)):
            return True
    return False


# The deaths that name their own subject: a reflexive verb, and the way a death is reported when
# nobody knows who the person is yet. Everything else needs its person said out loud.
_NAMES_ITS_SUBJECT = re.compile(
    r"^(?:killed|hanged)\s+(?:him|her|them)sel(?:f|ves)\b"
    r"|^took\s+(?:his|her|their)\s+own\s+li(?:fe|ves)\b"
    r"|^committed\s+suicide\b|^found\s+dead\b", re.I)


def _subject_before(text, start, said=""):
    """Whether the word the death belongs to is a person or an animal.

    The nearest word before the death decides, stepping over the words that carry a clause to a
    verb and over a place or a group. So "my phone died" is the phone, "he said his phone died" is
    still the phone, "my mate said the wifi is dead" is the wifi, and "someone in my class died"
    is someone.

    A line with no person in it at all is not a death, however the word is used: "dead broke",
    "dead cert", "dead in the water", "dead end job", "dead as a doornail" and "my leg went dead"
    are ordinary lines, and a list of the words that can follow "dead" never ends. Two shapes
    need no person in front: a reflexive death ("killed himself", "took her own life") and the
    way a death is reported before anyone is named ("found dead in his flat").
    """
    if said and _NAMES_ITS_SUBJECT.match(said):
        return True
    clause = text[:start]
    for mark in (".", "!", "?"):
        cut = clause.rfind(mark)
        if cut != -1:
            clause = clause[cut + 1:]
    words = _WORD.findall(clause)
    for word in reversed(words):
        if word in _CARRIES or word in _PLACE:
            continue
        return word in _PERSON
    return False


def reads_as_pregnancy_bleeding(clean):
    """Whether a line is bleeding or spotting in pregnancy: a midwife today, not a chat."""
    return any(pattern.search(clean) for pattern in PREGNANCY_BLEEDING)


def reads_as_the_speakers_own_plan(clean):
    """Whether the line is a plan the speaker is making, rather than news that happened to them."""
    return any(pattern.search(clean) for pattern in OWN_PLAN)


def _the_result_came_back_well(clean):
    """Whether the line is a clear result, which is news of the other kind (`goodnews`).

    The illness word is what makes a clear result look like bad news: "my mums cancer is in
    remission" was read on the word "cancer" and met with "Sorry to hear that. What would help
    most right now?", and "the biopsy was benign" with "I'm sorry - that's frustrating". The
    reading lives in `bot/compose/goodnews.py` with the rest of the good news; the import is here
    rather than at the top because goodnews imports this module (`reads_as_someones_death`).
    """
    from .goodnews import reads_as_a_clear_result
    return reads_as_a_clear_result(clean)


def reads_as_bad_news(clean):
    """Whether a cleaned, lowercased line is news a friend would answer gently."""
    if _the_result_came_back_well(clean):
        return False
    if any(pattern.search(JOKED.sub(" ", clean)) for pattern in BAD_NEWS):
        return True
    words = re.findall(r"[a-z']+", clean)
    return any(_nearly(word) for word in words)


if __name__ == "__main__":  # quick check of the lines above, runnable as a module
    import sys

    for line in sys.argv[1:]:
        low = line.lower()
        print(f"{reads_as_bad_news(low)!s:5} {reads_like_a_symptom(low)!s:5} {line}")
