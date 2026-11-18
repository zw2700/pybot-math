"""The bot offered to draft a message; the next line gives it what it asked for.

A line like "can you help me write a text to my boss" is answered, honestly, with an offer:
"give me who it's for and the one thing you need from them, and I'll write something you can
send." On main the next turn - "saying im off sick tomorrow" - was echoed back ("Got it - you're
off sick tomorrow") or met with "That sounds rough. If you want, I can help you think through
what to do next". The offer promised a draft and then went missing, which is the worst kind of
reply: a person who was told to hand over the details and did, and got nothing.

So this answers exactly one case: the bot's own last reply offered to draft, and the line just
said what to say. It hands back a short message with the person's own content in it.

What it refuses, because the offer is not an invitation to write anything:

* a line that is a question, not the content ("what do you think?"), or a hello, or a thanks;
* a line with nothing to put in a message ("ok", "yes", "that's it"), which is two words or
  fewer once the lead-in is gone;
* a line so long that no short message could carry it (over 30 words), where the honest reply is
  a question rather than a draft that throws half of it away;
* a line whose content is creative work: a poem, a speech or a joke about a specific person is
  not a message to send, and the bot cannot write one.

The register comes from who it is for: a boss, a landlord, a school or a surgery gets a formal
message, anything else the friendly one. A draft that has to apologise ("off sick", "can't make
Saturday") says so in the first line, because that is the part people get stuck on.
"""
import re

from ..memory import last_bot
from .badnews import reads_as_bad_news, reads_as_pregnancy_bleeding, reads_as_sudden_loss, \
    reads_like_a_symptom
from .loss import names_a_feeling

# The bot's own promise to write. Only the composer's offer lines are here: a module that says
# "I can write that" about something else must not put this in motion.
#
# The promise is read for its shape and not for one wording of it. The offer used to be the
# composer's own sentence ("I can write it: give me who it's for ..."), so an offer made by a
# card in another wording opened nothing: the writing card that answers "can you help me write a
# text to my friend" says "... tell me who it is for and what you need and I will write yours",
# and the detail that followed it - "i need to tell her i cant come" - was left to the fallback
# ("Ah, that's a pain. Does it put the whole thing off?"), though `TELL_FRAME` below reads that
# line as the message word for word. A promise to write it, yours or one, in any of the modals,
# is the same promise whoever makes it; the guards below (a question, a hello, two words, a life
# story) still decide what may fill it.
OFFER = re.compile(r"\bi can draft that\b|\bi can write it\b|\bi'll draft it\b|"
                   r"\bi'll write something you can send\b|\bgive me the gist and i'll draft it\b|"
                   r"\bi(?:'ll|\s+(?:can|could|will|would)) write (?:it|yours|one|that)\b|"
                   r"\bwrite (?:it|yours|one) for you\b")

# Who it is for. A parent, a landlord or an office gets a formal message; everyone else gets the
# friendly one. Only the words that are never a friend.
FORMAL = frozenset((
    "boss", "manager", "employer", "company", "hr", "work", "workplace", "office",
    "landlord", "landlady", "letting", "agent", "lettings", "housing", "council",
    "school", "head", "headteacher", "teacher", "tutor", "nursery", "childminder",
    "university", "college", "lecturer", "professor", "surgery", "gp", "doctor", "dentist",
    "hospital", "clinic", "bank", "insurer", "insurance", "utility", "energy", "council",
    "department", "tenant", "customer", "client", "supplier", "landlord's",
))

# "saying im off sick tomorrow" and "asking about the deposit" say what the message is; the
# lead-in is not part of it. Each shape gives the opening of the sentence.
LEADS = (
    (re.compile(r"^(?:and\s+|so\s+|ok\s+|okay\s+|well\s+|right\s+)?(?:it'?s\s+|its\s+)?"
                r"(?:saying|say|to\s+say|i\s+was\s+going\s+to\s+say)\s+(?:that\s+)?(?:i\s+)?"
                r"(?:am\s+|was\s+)?(?=\w)"), "said"),
    (re.compile(r"^(?:and\s+|so\s+|ok\s+|okay\s+|right\s+)?(?:it'?s\s+|its\s+)?"
                r"(?:asking|ask|to\s+ask)\s+(?:for|about)\s+"), "asked"),
    (re.compile(r"^(?:and\s+|so\s+|ok\s+|okay\s+|right\s+)?(?:it'?s\s+|its\s+)?"
                r"(?:to\s+say|saying|the\s+message\s+is)\s+(?:that\s+)?"), "said"),
    # "telling him i quit" describes the message in the third person, so what follows is not
    # the words to send: quoted, it writes "him" into the person's own text.
    (re.compile(r"^(?:and\s+|so\s+|ok\s+|okay\s+|well\s+|right\s+)?"
                r"(?:telling|told)\s+(?:them|him|her)\s+(?:that\s+)?"), "told"),
    (re.compile(r"^(?:and\s+|so\s+|ok\s+|okay\s+|well\s+|right\s+)?(?:"
                r"i\s+(?:just\s+)?(?:want|need|would\s+like)\s+to\s+say|"
                r"i(?:'d|\s+would)\s+like\s+to\s+say|let\s+(?:them|him|her)\s+know|"
                r"tell\s+(?:them|him|her))\s+(?:that\s+)?"), "said"),
    (re.compile(r"^(?:and\s+|so\s+|ok\s+|okay\s+|right\s+)?(?:that\s+|it'?s\s+)"), "said"),
)

# Chat-speak in the person's own sentence, put right before it goes into a message they will
# send to someone else: a typo is fine between friends, and this costs nothing.
TIDY = {
    "im": "I'm", "i": "I", "ive": "I've", "id": "I'd",
    "cant": "can't", "wont": "won't", "dont": "don't", "doesnt": "doesn't", "didnt": "didn't",
    "isnt": "isn't", "wasnt": "wasn't", "couldnt": "couldn't", "wouldnt": "wouldn't",
    "shouldnt": "shouldn't", "havent": "haven't", "thats": "that's", "theres": "there's",
    "whats": "what's", "lets": "let's", "pls": "please", "plz": "please", "thx": "thanks",
    "tmrw": "tomorrow", "tomoz": "tomorrow", "tomorow": "tomorrow", "tommorow": "tomorrow",
    "u": "you", "ur": "your", "n": "and", "cos": "because", "coz": "because",
    "appt": "appointment", "appointment's": "appointment's", "meds": "medication",
    "i'll": "I'll",
}

# Words that make the message one that has to apologise for itself.
# Being away from work is not how the person feels, it is the thing the message is for:
# "im off sick tomorrow", "im off work till monday", "im taking a day off". "im sick of this" is
# still a feeling, so the absence needs its own words.
ABSENT = re.compile(r"\b(?:off\s+(?:sick|ill|work)|sick\s+(?:leave|note|pay)|"
                    r"day\s+off|time\s+off|not\s+coming\s+in|won'?t\s+be\s+in|"
                    r"cant\s+come\s+in|can'?t\s+come\s+in)\b")

THIRD_PERSON = re.compile(r"\b(?:her|him|them|his|hers|they|she|he)\b")

# The message that is an apology already opens with it: "saying sorry for shouting at her" does
# not also need "sorry for the short notice" in front of it.
APOLOGY = re.compile(r"^(?:i'?m\s+|i\s+am\s+)?sorry\b|^apolog(?:y|ise|ize)\b")
# An apology carries something when it says what the person did: "sorry for shouting", "sorry i
# forgot". Without that ("sorry for the mess") the only message there is is the person's own
# words with a greeting in front, which is not worth sending back to them - the answer about the
# shape of an apology says more.
APOLOGY_ACT = re.compile(r"\bsorry\s+(?:for|about)\s+(?:being\s+)?([a-z']+ing)\b"
                         r"|\bsorry\s+(?:that\s+)?(?:i|we)\s+([a-z']+)\b")
# "sorry for being such a mess" is not an apology for a doing, it is the person calling themselves
# one: a message that says "I shouldn't have done that" agrees with the worst reading of it, and the
# answer to a mood is the mood answer. "being late" is a doing, so only the naming words are here.
APOLOGY_SELF = re.compile(r"\bsorry\s+(?:for|about)\s+(?:being\s+)?"
                          r"(?:such\s+)?(?:a\s+|an\s+)?"
                          r"(?:mess|burden|nightmare|nuisance|pain|disaster|state|rubbish"
                          r"|useless|awful|horrible|annoying|needy|too much|like this|this way"
                          r"|me|myself|the way i am)\b")
SORRY = re.compile(r"\b(?:sick|ill|unwell|off\s+work|not\s+(?:coming|in|be\s+in)|"
                   r"won'?t\s+be\s+(?:in|there)|can'?t\s+(?:come|make|be\s+(?:in|there))|"
                   r"cant\s+come|cannot\s+come|late|miss(?:ing)?|day\s+off|time\s+off|"
                   r"cancel(?:ling)?|postpone|reschedule|sorry)\b")

# A message is written in sentences, and a person typing the gist often leaves the subject out
# ("wont be in till monday", "off sick tomorrow"). The draft puts it back, because the version
# without it reads like a note from nobody.
SUBJECT = re.compile(r"^(?:won'?t|can'?t|cannot|should\s+be|will\s+be|might\s+be|not\s+be|"
                     r"going\s+to|need|want|wonder|hope|must|would\s+like|would|didn'?t|"
                     r"don'?t|am|was|were|have|had|keep|late\b|stuck\b|away\b)\b")
COPULA = re.compile(r"^(?:off\b|sick\b|ill\b|unwell\b|back\s+(?:in|at|on|from)\b|"
                    r"still\s+(?:off|ill|unwell|sick)\b)")

# Creative work is not a message to send, and the bot cannot write it.
CREATIVE = frozenset(("poem", "poems", "poetry", "haiku", "story", "stories", "song", "songs",
                      "rhyme", "rhymes", "joke", "jokes", "speech", "speeches", "limerick"))

# A line that asks something is not the content of a message.
# Yes to the offer and nothing else. "yes please" is two words, so the length test in _content
# let it through and the message read "Hey, yes please." - the person's answer to the bot put in
# the mouth of the message. Every word here is agreement or politeness, so a line made only of
# them says nothing to send.
AGREEMENT = frozenset((
    "ok", "okay", "okey", "k", "yes", "yeah", "yep", "yup", "aye", "sure", "please", "thanks",
    "thank", "you", "ta", "cheers", "go", "on", "then", "ahead", "that", "thats", "it", "is",
    "that's", "alright", "right", "cool", "great", "fine", "nice", "sound", "and", "so", "do",
    "thatll", "that'll", "let's", "lets", "have", "a", "shot", "give", "us", "for", "me", "my",
    "no", "nope", "nah", "not", "now", "later", "sounds", "good", "perfect", "lovely", "brilliant",
))

QUESTION = re.compile(r"^\s*(?:what|why|how|who|which|when|where|should|could|would|can|do|"
                      r"does|did|is|are|was|were|will|have|has|any)\b")

# A day or a month in the middle of a sentence is still a name.
CAPITALS = frozenset((
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august", "september",
    "october", "november", "december",
))

# What a person says when they are telling the bot how they feel about someone, not what to send
# them: "my boss is a nightmare" is the mood, and a text reading "Hi, my boss is a nightmare" is
# not a message anyone sends. A line that reports on somebody else is the same story ("he keeps
# asking"), so the bot asks again for the words rather than quoting the complaint back.
VENT = frozenset(("nightmare", "joke", "useless", "annoying", "awful", "horrible", "rubbish",
                  "unbearable", "impossible", "toxic", "miserable", "unfair", "frustrating",
                  "exhausting"))
VENT_PHRASES = ("a pain in the", "fed up", "had enough", "cant stand", "driving me mad",
                "driving me up the wall", "driving me crazy")

# News about the person is not the content of a message. A death, a diagnosis or a redundancy was
# answered with sympathy on main, and a draft reading "Hi, my mum died yesterday. Thanks." is the
# worst reply the bot could give: the person answered the offer with their news, not with the
# words. Same for a mood - "im tired" is about them, not about the text - so both fall through to
# the answer the line would have had, and the bot says nothing about a draft at all.
NEWS = frozenset(("died", "death", "dead", "funeral", "buried", "cremation", "cancer", "tumour",
                  "hospital", "hospice", "ward", "icu", "stolen", "burgled", "robbed",
                  "mugged", "struggling", "panicking", "hyperventilating", "breakdown",
                  "tumor", "diagnosed", "diagnosis", "miscarriage", "stillborn", "chemo",
                  "redundant", "sacked", "fired", "bankrupt", "evicted", "divorce", "divorced",
                  "breakup", "dumped", "debt", "debts", "arrears", "homeless", "bereaved",
                  "bereavement", "dying"))
NEWS_PHRASES = ("passed away", "lost my job", "lost his job", "lost her job", "lost the baby",
                "in debt", "behind on", "split up", "walked out", "left me", "laid off",
                "in hospital", "in the hospital", "my phone was", "got stolen", "was stolen",
                "panic attack", "anxiety attack", "im struggling", "really struggling",
                "not coping", "falling apart", "i feel awful", "feel terrible")
FEELING = frozenset(("tired", "exhausted", "knackered", "shattered", "drained", "stressed",
                     "overwhelmed", "anxious", "depressed", "upset", "unhappy", "miserable",
                     "angry", "furious", "worried", "scared", "awful", "terrible", "horrible",
                     "panicky", "terrified", "devastated", "heartbroken", "gutted", "low"))
FEELING_PHRASES = ("fed up", "had enough", "cant cope", "can't cope", "burnt out", "worn out")
# The other half of the same rule, and the half a word list cannot do: a draft needs a line that
# *is* the message. A fragment ("its about the deposit"), a state ("im skint this month"), a
# question about what to write ("i dont know what to say") and a bare subject are all answers to
# the offer that keep their own reply - "Hi, about the deposit. Thanks." is not a message anybody
# would send. So a line drafts only when it carries one of these shapes; everything else falls
# through, and the bot answers the line itself.
MESSAGE_SHAPES = (
    # an ask: the one thing they need from the other person
    re.compile(r"\bi (?:need|want|would like|have) to\b|\bi (?:need|want)\b|\bcan i\b|"
               r"\bcould i\b|\bplease\b|\basking (?:for|about)\b|\bi(?:'m| am|m) asking\b"),
    # a change to a plan: what has changed and when
    re.compile(r"\bi(?:'ll| will|ll) be\b|\bi(?:'m| am|m) (?:off|out|away|late|not coming|"
               r"stuck|leaving|moving|starting|finishing|going to|back)\b|"
               r"\bi (?:cant|cannot|can not|wont|will not)\b|\bi(?:'ve| have|ve) (?:decided|"
               r"quit|resigned|booked|cancelled)\b|"
               r"\bi dont (?:think i can|want to come)\b"),
)
# A thing of theirs that has gone wrong is the message only when the line says so ("saying my car
# broke down") or when it comes with the change of plan it causes ("i cant come, my car broke
# down"): the same words on their own are a fault to fix, and the topic entry answers those
# better than "Hi, the boiler is leaking." does. "i quit" is the same case from the other end - the
# words are the whole message and the answer about how to resign says more than the four words.
THING_GONE_WRONG = re.compile(r"\b(?:my|the|our)\b[^.,!?]{0,28}\b(?:broke|broken|bust|busted|"
                              r"snapped|stopped working|wont start|packed in|died|got stolen|"
                              r"was stolen|flooded|leaking|blocked|failed|cancelled|fell through)\b")
# A shape that looks like a change to a plan and is not one: "i cant sleep" is a symptom and
# "i want a refund from amazon" is a job for the person, not the words of a message. Their own
# answers are better than a text that says the complaint back to them.
NOT_A_CHANGE = re.compile(r"\bi (?:cant|cannot|can not|wont|will not|dont|do not)\s+"
                          r"(?:sleep|eat|stop|breathe|walk|see|hear|swallow|keep|remember|"
                          r"focus|concentrate|pee|cry|poo|sit|stand)\b")
WANT_FROM = re.compile(r"\bi (?:need|want|would like)\b[^.,!?]{0,30}\bfrom\b")
# What must never draft whatever shape it looks like: the person is telling the bot they have no
# words, which is the opposite of handing it the message.
NO_MESSAGE = re.compile(r"\bi (?:dont|do not) know\b|\bno idea\b|\bnot sure (?:what|how)\b|"
                        r"\bi cant (?:think|find the words)\b|\bwhat should i say\b|"
                        r"\bhelp me (?:word|say)\b|\bi dont know what to say\b")
# Wishing somebody back is a feeling about them, not the words of a message: "saying i want her
# back" was drafted as "Hi, I want her back." to whoever the message was for, which names neither
# the person it is about nor anything they could send.
A_WISH_FOR_SOMEONE = re.compile(r"\b(?:want|wants|wanted|wish|wishing)\s+"
                                r"(?:her|him|them|it)\s+back\b")
# A wish to hurt somebody is never the words of a message. "i want to kill him" was drafted as
# "Hi, I want to kill him. Thanks." and signed, so the bot wrote a threat for a person to send,
# on the one turn where the offer was open before they said it. The guard already existed for
# "i want to smash his face in" (the line is not shaped like a message); this reads the class
# rather than the shape: a hurt word with a person on the end of it, anywhere in the line.
HURT_WORD = (r"(?:kill|murder|hurt|punch|hit|smash|beat|stab|shoot|strangle|choke|throttle|"
             r"slap|kick|wring|batter|poison|drown)")
HURT_TARGET = (r"(?:me|you|him|her|them|us|myself|yourself|himself|herself|themselves|"
               r"my|his|her|their|our|someone|somebody|everyone|everybody)")
# The frame that makes it a wish rather than a report of an injury: "i want to ...", "im going to
# ...", "i could ...", "i'd like to ...". Without one, "i cut my hand on glass" and "it hit me
# hard" are the lines they always were; with one there is somebody on the end of the verb.
HURT_WISH = (r"\b(?:i|we|ill|i'll|im|i'm|id|i'd)\s+"
             r"(?:really\s+|just\s+|so\s+|seriously\s+)?(?:want|wanna|wanted|would\s+like|"
             r"would\s+love|need|have|am\s+going|going|will|ll|might|should|could|must|"
             r"love|like|planned?\s+to|wish(?:ed)?)\s+(?:to\s+)?")
HURTS_SOMEONE = re.compile(HURT_WISH + HURT_WORD + r"\s+(?:\w+\s+){0,3}" + HURT_TARGET + r"\b")
# "i want him dead" is the same wish in the other grammar.
WANTS_THEM_DEAD = re.compile(r"\b(?:want|wants|wanted|wish|wishes|wished)\s+"
                             r"(?:\w+\s+){0,2}dead\b")


def _wants_to_hurt(low):
    """True when the line is a wish to hurt somebody, which is never a message to send."""
    return bool(HURTS_SOMEONE.search(low) or WANTS_THEM_DEAD.search(low))


def _is_a_message_shape(low):
    """True when the line reads as the content of a message rather than a fragment or a state."""
    if NO_MESSAGE.search(low) or NOT_A_CHANGE.search(low) or WANT_FROM.search(low):
        return False
    if len(re.findall(r"[a-z']+", low)) < 2:
        return False
    if any(shape.search(low) for shape in MESSAGE_SHAPES):
        return True
    return bool(THING_GONE_WRONG.search(low) and says_it_is_the_message(low))


REPORTS_ON_SOMEONE = re.compile(r"^\s*(?:he|she|they)\b|\b(?:keeps?|kept)\s+(?:asking|saying|"
                               r"telling|ringing|texting|changing|forgetting|moaning)\b")
# What the bot says back when the offer is still open and the line was not the message.
NOT_YET = (
    "That's the mood rather than the words - give me the one line you want the message to say "
    "and I'll write it.",
    "Nearly: tell me what the message should actually say, and I'll put it in order.",
    "Got the feeling. Now the words: what do you want them to read?",
)

# The reply the composer gives is the draft itself in quotes after one of these, so a person can
# see it is a message to send and not something the bot is saying about them. The arbiter reads
# them back to recognise its own draft (DRAFT_LEADS is the one list).
LEAD_INS = (
    "Here's something you could send:",
    "Try this:",
    "Something like this works:",
    "Here's a short version:",
)


def names_a_draft(reply):
    """True when a reply is the composer's drafted message rather than a line about it."""
    return str(reply or "").lstrip().startswith(LEAD_INS)


def offers_a_draft(reply):
    """True when a reply is the bot's promise to write the message, rather than the message.

    The offer is the other half of the draft: on the first turn of "can you help me write a text
    to my landlord" there is no detail yet to turn into a message, so the honest reply is to ask
    for it. Read by its own words (`OFFER`), because it is drawn from a pool: see
    `fallback_data.UNKNOWN_WORD`.
    """
    return bool(OFFER.search(str(reply or "").lower()))


QUOTED = re.compile(r"[\"\u201c]([^\"\u201d]{15,})[\"\u201d]")


def hands_over_words(reply):
    """True when a reply already hands the person words to send, in quotation marks.

    A card that answers "can you help me write a note to my son's teacher" with the note itself
    ("Sam (5B) has been anxious about maths homework - could we talk?") has done the job the
    offer would only promise to do, so the offer must not take that turn. Read by the shape of
    the quotation and not by the words in it: four words or more between quotes is a message to
    send, not a phrase the bot is quoting back.
    """
    for body in QUOTED.findall(str(reply or "")):
        if len(body.split()) >= 4:
            return True
    return False


# The parts of a message, said as instructions rather than quoted. The tenancy card answers "can
# you help me write an email to my landlord" with "Keep it short, dated and specific, and ask for
# a date. Say what is wrong, when it started and when you are in, and follow it up in writing" -
# no quotation marks, so `hands_over_words` misses it, but that is the shape a friend gives and it
# is more than the offer promises. Two of these cues beside the message's own name is the line
# between a card that hands the message over and one that only talks about the subject: the
# housing card for "text to my landlord" says none of them, and the offer keeps that turn.
MESSAGE_WORD = re.compile(r"\b(?:text|message|email|e-mail|note|letter)\b")
# Three cues, or two beside the message's own name, because the tenancy card names the flat and
# the council and never says the word "letter" - what makes it the answer here is that it gives
# the parts ("keep it short, dated and specific", "ask for a date", "say what is wrong").
SHAPE_CUES = re.compile(r"\b(?:say|says|keep|short|specific|ask\s+for|ask\s+them|mention|put|"
                        r"include|subject|sign\s?-?off|signed|date[ds]?|address|tell\s+them|"
                        r"follow\s+it\s+up|first\s+sentence|first\s+line|opening|closing|"
                        r"paragraphs?|\d+\s*words|bullet\s+points?|three\s+or\s+four|"
                        r"few\s+lines|lines)\b")


def hands_over_the_shape(reply):
    """True when a reply already gives the parts of the message, without quoting it.

    The other half of `hands_over_words`: a card that tells them what to put in the message has
    answered the ask just as well as one that quotes the whole thing, and the offer may not take
    that turn. Read by the message's name beside two of the cues, so a card about the subject
    itself (the tenancy entry answers "text to my landlord" only about damp and the council) is
    not mistaken for one that writes the message.
    """
    low = str(reply or "").lower()
    cues = len(set(m.group(0) for m in SHAPE_CUES.finditer(low)))
    return cues >= 3 or (cues >= 2 and bool(MESSAGE_WORD.search(low)))


# A line that asks for the words, in the narrow shape that has nothing yet to put in them: "can
# you help me write a text to my landlord". What it has to name is the person it is going to,
# because that is the part the bot cannot guess, and what it must not name is the message itself
# ("saying im sick", "about the noise", "asking for friday off"): once the content is on the
# table the knowledge base has something to work with, and its card is the answer that was
# written for it. "how do i write an email to my boss" is a question about the method, and a
# message that is a genre ("a complaint letter", "a covering letter") is not one to a person, so
# neither is read here. Creative work is not a message anyone sends, and `CREATIVE` keeps it out.
MESSAGE_NOUN = r"(?:text|message|msg|email|note|letter)"
WRITING_ASK = re.compile(
    r"\b(?:can|could|would|will)\s+(?:you\s+)?(?:please\s+)?(?:help\s+(?:me\s+)?)?"
    r"(?:write|word|draft|phrase|put\s+together)\b[^?]{0,40}?" + MESSAGE_NOUN + r"\s+(?:to|for)\b"
    r"|\bhelp\s+me\s+(?:write|word|draft|phrase)\b[^?]{0,40}?" + MESSAGE_NOUN + r"\s+(?:to|for)\b"
    r"|\b(?:write|draft|word)\s+me\s+(?:a|an|the)\s+(?:short\s+|quick\s+|nice\s+|polite\s+|firm\s+)?"
    + MESSAGE_NOUN + r"\s+(?:to|for)\b")

# The words after the ask that say what the message is, which means the ask is not the empty one:
# "help me write a text to my boss saying im sick" has its content, and the knowledge base's card
# for a sick note is a better answer than "tell me who it's for".
THE_CONTENT = re.compile(r"\b(?:saying|says|tell(?:ing)?|about|asking|ask|because|cos|since|"
                        r"explaining|to\s+say|to\s+ask|that)\b")


def reads_as_a_writing_ask(line):
    """True when the line asks the bot to write a message and has not said what it should say."""
    clean = " ".join(str(line or "").lower().split())
    if not clean:
        return False
    if CREATIVE & set(re.findall(r"[a-z']+", clean)):
        return False
    if re.match(r"^\s*(?:how|what|where|when|why)\b", clean):
        return False                  # "how do i write an email to my boss" asks for the method
    found = WRITING_ASK.search(clean)
    if not found:
        return False
    return THE_CONTENT.search(clean[found.end():]) is None


# "ill be late" is I'll, and "im ill" is ill: the difference is the word after it, which is a verb
# only in the first case. A leading "ill" is never the illness, so it goes one way.
AFTER_ILL = frozenset(("be", "have", "see", "try", "call", "let", "need", "get", "go", "ring",
                       "text", "come", "bring", "pay", "ask", "tell", "do", "send", "sort"))


def _tidy(text):
    """The person's own sentence, with chat-speak put right and a capital at the front."""
    words = str(text or "").split()
    if len(words) > 1 and words[0].strip(".,!?;:").lower() == "ill" \
            and words[1].strip(".,!?;:").lower() in AFTER_ILL:
        text = "i'll " + " ".join(words[1:])
    out = []
    for word in text.split():
        bare = word.strip(".,!?;:")
        tail = word[len(bare):] if bare and word.startswith(bare) else ""
        if bare.lower() in CAPITALS:
            out.append(bare[0].upper() + bare[1:] + tail)
            continue
        fixed = TIDY.get(bare.lower())
        if fixed and bare.islower():
            out.append(fixed + tail)
        else:
            out.append(word)
    line = " ".join(out).strip(" .")
    if not line:
        return ""
    return line[0].upper() + line[1:]


def _small(text):
    """"A recycling bin" -> "a recycling bin", but "I need my stuff back" keeps its capital."""
    if not text or not text[:1].isupper() or text.startswith(("I ", "I'", "I,")):
        return text
    if text.split()[0].strip(".,!?;:").lower() in CAPITALS:
        return text                      # a day or a month is still a name
    return text[0].lower() + text[1:]


# A want with a comparison in it and nobody named: "i want to hit the gym more", "i want to read
# more", "i want to walk every day". The offer was open, but what the line wants is not something
# anybody else can be sent - the person is telling you a wish about their own week, and the answer
# they would have had ("what's stopped it happening so far?") is the one worth keeping.
WANTS_MORE_OF_IT = re.compile(
    r"^(?:and\s+|so\s+|ok\s+|okay\s+)?i\s+(?:just\s+)?(?:want|wants|need|needs|would\s+like|"
    r"wanna)\s+(?:to\s+)?(?:\w+\s+){0,4}?"
    r"(?:more|less|again|every\s+day|every\s+week|every\s+morning|more\s+often)\b")


def _content(text):
    """(the sentence to put in the message, shape) or (None, None)."""
    line = " ".join(str(text or "").split())
    if not line or "?" in line:
        return None, None
    low = line.lower()
    if low in {"ok", "okay", "yes", "yeah", "no", "thanks", "thank you", "hi", "hello", "hey"}:
        return None, None
    if all(word.strip(".,!?;:'") in AGREEMENT for word in line.split()):
        return None, None          # "yes please", "go on then", "ok that's great" - nothing to send
    if QUESTION.match(low):
        return None, None
    shape = "said"
    for pattern, kind in LEADS:
        found = pattern.match(low)
        if found:
            shape = kind
            line = line[found.end():].strip()
            break
    low = line.lower()
    if WANTS_MORE_OF_IT.match(low):
        # "i want to hit the gym more" is a want about the person's own life, not the wording of a
        # message: nothing in it is addressed to anybody. What tells it apart from "i want my money
        # back" - which has to stay a draft - is the comparison, more or less of a thing or doing
        # it again, with nobody named on the other end.
        return None, None
    words = line.split()
    if len(words) < 2 or len(words) > 30:
        return None, None
    if set(w.lower().strip(".,!?;:") for w in words) & CREATIVE:
        return None, None
    body = _tidy(line)
    if not body:
        return None, None
    return body, shape


def _formal(memory, words):
    """True when the message is going to someone a person writes to formally."""
    if set(words) & FORMAL:
        return True
    for turn in (memory.get("turns") or [])[-4:]:
        text = str((turn or {}).get("user") or "").lower()
        if set(re.findall(r"[a-z']+", text)) & FORMAL:
            return True
    return False


def _said_before(memory, line):
    """The line's words, when the bot's last reply offered to draft; otherwise None."""
    if not OFFER.search(str(last_bot(memory) or "").lower()):
        return None
    low = " ".join(str(line or "").lower().split())
    if not low or "?" in low:
        return None
    return low


# How long a thing has been wrong: the one detail a message about it cannot do without.
A_SPAN = re.compile(
    r"\b(?:since|for)\s+(?:\d+\s+|a\s+|an\s+|two\s+|three\s+|four\s+|five\s+|six\s+|seven\s+|eight\s+|nine\s+|ten\s+)?"
    r"(?:day|days|week|weeks|fortnight|fortnights|month|months|year|years|january|february|march|april|may|"
    r"june|july|august|september|october|november|december)\b"
    r"|\b(?:has|had)\s+been\b|\bkeeps?\s+(?:coming|going|happening|flaring|leaking|breaking)\b")


# "the doctor says i should stop" and "he says hes waiting on a part" are somebody else reporting
# something, not a line the person wants to send.
REPORTED_SPEECH = re.compile(r"\b(?:says?|said|telling|told|reckons?|thinks?|asked|wants?\s+me\s+to)\b")


def _a_fault_they_were_asked_for(low):
    """How long the thing has been wrong, on the turn after the bot asked what to say.

    The offer is the difference. "give me who it's for and what you want them to do" is a
    question with an answer, and the answer arrives as a report rather than as a message: "the
    boiler has been broken for 2 weeks", "the damp has been there since october". Neither has a
    lead-in, so the shape test refused them and a topic entry answered instead - the boiler-repair
    steps, one line after the bot had asked for the words - and the offer it made went missing.

    Only the span makes a line this: "since october", "for two weeks", "has been", "keeps
    coming back for a month". A live fault keeps the answer it has, because that answer is worth
    more than a message ("the boiler is leaking" wants the water off at the wall, not "Hi, the
    boiler is leaking. Thanks."), and so does anything about a third person, anything reported at
    second hand ("he says hes waiting on a part") and news or a feeling.
    """
    if not A_SPAN.search(low):
        return False
    if THIRD_PERSON.search(low) or REPORTED_SPEECH.search(low):
        return False
    words = set(re.findall(r"[a-z']+", low))
    if words & (NEWS | FEELING):
        return False
    return not any(phrase in low for phrase in NEWS_PHRASES + FEELING_PHRASES)


def is_theirs(memory, line):
    """True when the offer is open and the line is news about the person, or a mood.

    Those are not the content of a message, and they are not a complaint to be answered with
    "tell me what the message should say" either: they keep the answer they would have had.
    """
    low = _said_before(memory, line)
    if low is None:
        return False
    if A_WISH_FOR_SOMEONE.search(low):
        return True
    if _wants_to_hurt(low):
        # The draft is the one turn where the offer was made before the person said this, so a
        # threat must never come back signed. The anger has its own answer.
        return True
    lead = _names_the_message(low)
    if lead is not None:
        # "saying im off sick tomorrow" is the message itself. The bare "it's ..." prefix is not
        # enough on its own - "its about the deposit" is a fragment, not something to send - so
        # that one still has to be shaped like a message.
        if lead is BARE_LEAD and not _is_a_message_shape(low):
            return True
        # What follows the lead is read for news and mood like any other line, because a lead does
        # not turn a death into a message: "saying my mum died" was drafted as "Hi, my mum died.
        # Thanks." while the line wants the condolence, and "saying i have cancer" was drafted
        # while the diagnosis has its own answer. The words are the same ones the rest of the file
        # refuses (NEWS, FEELING), so the lead refuses them too.
        rest = low[lead.match(low).end():]
        if set(re.findall(r"[a-z']+", rest)) & (NEWS | FEELING):
            return True
        if any(phrase in rest for phrase in NEWS_PHRASES + FEELING_PHRASES):
            return True
        return False
    # How the person is feeling in their own words comes before the complaint guard, because a
    # feeling and a complaint about someone else share words ("awful", "angry") but are not the
    # same thing: "i feel awful today" wants its answer, "my boss is a nightmare" wants the words.
    if APOLOGY.match(low) and not THIRD_PERSON.search(low):
        # "im sorry for shouting" is the message itself, not how the person feels. A named third
        # person without a lead ("im sorry i forgot her birthday") is describing it, so that one
        # keeps its answer.
        return False
    if ABSENT.search(low):
        # "im off sick tomorrow" is not how the person feels - it is the message they were asked
        # for. "im sick of this" keeps its feeling answer; the absence words are its own case.
        return False
    if low.startswith(("i feel", "im ", "i'm ", "i am ", "ive been ", "i've been ")) \
            and (set(re.findall(r"[a-z']+", low)) & FEELING
                 or any(phrase in low for phrase in FEELING_PHRASES)):
        return True
    if set(re.findall(r"[a-z']+", low)) & VENT:
        return False                      # a complaint about someone is the mood, not their news
    if any(phrase in low for phrase in VENT_PHRASES) or REPORTS_ON_SOMEONE.search(low):
        return False
    # Nothing else drafts unless the line is shaped like a message: the positive half of the rule,
    # after the complaint guard so a complaint still reaches "tell me what the message should say"
    # and keeps the offer open. A fragment, a state with no ask in it or "i dont know what to say"
    # is only caught by asking what the line is made of. Their answer is their own.
    if not (_is_a_message_shape(low) or _a_fault_they_were_asked_for(low)):
        return True
    if set(re.findall(r"[a-z']+", low)) & (NEWS | FEELING):
        return True
    if any(phrase in low for phrase in NEWS_PHRASES + FEELING_PHRASES):
        return True
    # The composers own readings know the classes a word list does not: a pregnancy bleed, a
    # bereavement, a symptom, a feeling named plainly. Each of those has an answer for the
    # person, and "Hi, Im bleeding and Im pregnant. Thanks." is not it.
    return bool(reads_as_pregnancy_bleeding(low) or reads_as_sudden_loss(low)
                or reads_as_bad_news(low) or reads_like_a_symptom(low)
                or names_a_feeling(low))


# The last lead is the bare prefix ("it's ...", "that ..."), which says less than the others: it
# names the shape of the line, not that the line is the message. "it's about the deposit" opens
# with it and is a fragment, so this one still has to pass the shape test.
BARE_LEAD = LEADS[-1][0]


def _names_the_message(low):
    """The lead that opens the line, or None: "saying ...", "asking for ...", "tell them ..."."""
    for pattern, _kind in LEADS:
        if pattern.match(low):
            return pattern
    return None


def says_it_is_the_message(line):
    """True when the line opens by naming the message: "saying ...", "asking for ...", "tell them
    ...". The bare "that/it's" lead is left out on purpose: "its about the deposit" is a fragment,
    not someone saying that what follows is the message.

    The composer uses this to let the draft past the topic entries on a line that names what the
    message says - "saying i cant make saturday cos im skint" is the note, and the money reading
    of it is the note's reason rather than a new subject. A line that does not name the message
    waits its turn behind the news, the symptoms and the losses.
    """
    lead = _names_the_message(" ".join(str(line or "").lower().split()))
    return bool(lead) and lead is not BARE_LEAD


def not_the_message(memory, line):
    """True when the offer is open but this line is a complaint about somebody, not the message."""
    low = _said_before(memory, line)
    if low is None or is_theirs(memory, line):
        return False
    if set(re.findall(r"[a-z']+", low)) & VENT:
        return True
    if any(phrase in low for phrase in VENT_PHRASES):
        return True
    return bool(REPORTS_ON_SOMEONE.search(low))


# "i need to tell her i cant come" is the same case as "telling her i cant come": the frame names
# a third person, and the words after it are the message. The frame comes off; if a third person is
# still in what is left, the line is the person describing the message and keeps its own answer.
TELL_FRAME = re.compile(r"^(?:and\s+|so\s+|ok\s+|okay\s+)?i\s+(?:just\s+)?(?:need|want|have)\s+"
                        r"to\s+tell\s+(?:them|him|her)\s+(?:that\s+)?")


def drafter(memory, line, words=None):
    """The draft for this line, or None when the bot did not offer one last turn."""
    if not OFFER.search(str(last_bot(memory) or "").lower()):
        return None
    if is_theirs(memory, line) or not_the_message(memory, line):
        return None
    frame = TELL_FRAME.match(" ".join(str(line or "").lower().split()))
    if frame:
        rest = " ".join(str(line or "").lower().split())[frame.end():].strip(" ,.")
        if not rest or THIRD_PERSON.search(rest):
            return None
        line = rest
    body, shape = _content(line)
    if not body:
        return None
    if shape == "told":
        # "telling him i quit" is the person describing the message in the third person. Quoting
        # what follows puts "him" in the text they would send ("Hi, telling him I quit"), so those
        # lines keep their own answer - the resignation structure is better than any one-liner.
        return None
    if shape == "asked":
        body = "I wanted to ask about " + _small(body)
    if body.endswith(("?", "!", ".")):
        body = body[:-1]
    # "The boiler is broken" after "Hi, " is one sentence, so the capital goes.
    body = _small(body)
    if COPULA.match(body.lower()):
        body = "I'm " + body[0].lower() + body[1:]
    elif SUBJECT.match(body.lower()):
        body = "I " + body[0].lower() + body[1:]
    apology = APOLOGY.match(body.lower()) is not None
    if apology:
        # The message is itself an apology ("saying sorry for shouting at her"), so the
        # short-notice opening would make it say sorry twice: the apology is the opening. What it
        # does need is the part that carries an apology - taking the blame for what was done.
        # Quoting "I'm sorry for shouting" back is the person's own four words with a greeting on
        # the front, so an apology that names no doing is left to the shape answer.
        if APOLOGY_ACT.search(body.lower()) is None or APOLOGY_SELF.search(body.lower()):
            return None
        body = body + ". I shouldn't have done that"
    elif SORRY.search(body.lower()):
        # The apology opens the message, so the sentence after it starts in lower case - unless
        # it starts with "I", which is a capital whatever comes before it.
        small = body[0].lower() + body[1:]
        keeps_cap = re.match(r"i(?:'|\b)", body, re.I) is not None  # "I'm off sick", "I need Friday"
        body = "sorry for the short notice - " + (body if keeps_cap else small)
    friendly = not _formal(memory, set(words or re.findall(r"[a-z']+", str(line).lower())))
    hello = "Hey" if friendly else "Hi"
    sign = "Cheers" if friendly else "Thanks"
    if apology or len(re.findall(r"[a-z']+", body.lower())) <= 4:
        # A four-word message signed "Cheers" reads like a joke: "Hi, I quit. Thanks." is not what
        # anybody sends when they quit. The short line stands on its own.
        return f"{hello}, {body}."
    return f"{hello}, {body}. {sign}."


# An illustrative example inside a stock answer has to be in the asker's world. The email-shape
# card ends with a sample subject line, and the one line it had was "Invoice 2144 - payment due",
# so a person asking how to email their child's teacher, their landlord, their plumber or their
# GP was told to write "Invoice 2144 - payment due" - an answer about a different life, which is
# the worst reply the bot gives. The card is still right about the shape of an email; only the
# example changes, and only the example, so nothing else in the answer moves.
#
# The reader takes the first world the line names. A person can name two ("email my landlord
# about the deposit"), so the order is by how much the example has to fit: the trade that is
# coming to the house, the school, the surgery, the landlord, work, and the money question that
# the card's own example was written for. Nothing named leaves the invoice, which is how the card
# answered before and is right for a business letter.
SUBJECT_EXAMPLES = (
    (re.compile(r"\b(?:plumber|electrician|boiler|leak|radiator|roofer|builder|joiner|"
                r"damp|drain|washing machine|fridge|oven|heating|handyman)\b", re.I),
     "Leak under the kitchen sink - when can you come?"),
    (re.compile(r"\b(?:teacher|school|headteacher|head|nursery|childminder|tutor|"
                r"college|university|lecturer|professor|year \d+|form|class)\b", re.I),
     "Year 6 trip - a question about the form"),
    (re.compile(r"\b(?:gp|doctor|surgery|dentist|hospital|clinic|prescription|appointment|"
                r"nurse|consultant)\b", re.I),
     "Repeat prescription - could you check this for me"),
    (re.compile(r"\b(?:landlord|landlady|letting|lettings|agent|housing|council|tenant)\b", re.I),
     "Boiler still not working - flat 3"),
    (re.compile(r"\b(?:boss|manager|employer|hr|work|workplace|office|team|colleague|"
                r"shift|rota)\b", re.I),
     "A quick question about Thursday"),
    (re.compile(r"\b(?:invoice|payment|paid|pay|bill|overdue|refund|quote|estimate|"
                r"customer|client|supplier)\b", re.I),
     "Invoice 2144 - payment due"),
)


def example_subject(understood):
    """The sample subject line for the email-shape card, in the world the line names."""
    line = ""
    if isinstance(understood, dict):
        line = str(understood.get("clean") or understood.get("text") or "")
    else:
        line = str(understood or "")
    for pattern, example in SUBJECT_EXAMPLES:
        if pattern.search(line):
            return example
    return "Invoice 2144 - payment due"
