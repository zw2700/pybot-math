"""Whether they already told the bot about a thing, answered from the chat.

"have I told you about my sister?" is a question about the conversation, not about the world,
and the store is the only part of the bot that can answer it. The shape was reaching the search
hedge ("That's beyond what I know well, sorry"), which is wrong twice over: the thing is in the
chat, and the person is asking the bot to remember rather than to look anything up.

What the store holds is said back in the order that reads best:

1. the fact against the person it is about - "my sister lives in Cork" is their sister's line,
   and the store keeps what it knows of her;
2. a pet by its kind - "have I told you about the cat?" is the cat called Milo;
3. the line itself, quoted, when no fact was kept: their own words still answer the question,
   and "you haven't told me about your sister yet" to someone who just did is the worst answer
   available;
4. the fact of the kind they asked about ("the trip", "my job") when the ask names a kind
   rather than a thing, because the plan's words never appear in the ask.

Anything else is left alone (`None`), including an ask about a thing the store has never heard
of: that is the honest "nothing yet", which is a memory answer too, so it is said here rather
than pushed onto a module that knows nothing about the person.
"""
import re

from ..compose import pick
from ..understanding import breeds as breed_words
from . import history, others, user
from . import you as say_it_back
from . import facts as extract
from . import recall

# "have i told you about my sister", "did i mention the trip", "have we ever talked about lisbon",
# "tell me if i told you about ..." is not this shape. The opener is the question and the rest is
# the thing, so a line that carries a statement after it ("have i told you my name is sam") is
# left alone: that is news, not a question about the chat.
#
# Only the past and the perfect open a question about what was said. A present "do i / does he"
# with one of these verbs is somebody deciding what to do next: "do i say yes", "do i tell her",
# "do i mention it to my boss" are the person asking for help with a decision, and they were read
# as a lookup and answered with their own words quoted back ("There's nothing on yes in what I
# keep", "I don't have "her about the money" in my notes"). Nothing has been said yet in those
# lines, so there is nothing to look up.
TOLD_ABOUT = re.compile(
    r"^\W*(?:and\s+|also\s+|so\s+|but\s+|ok(?:ay)?\s+|wait\s+|quick\s+)?"
    r"(?:have|has|had|did)\s+(?:i|we)\s+(?:ever\s+|already\s+)?"
    r"(?:told|tell|mentioned|mention|said|say|talked|talk)\s+(?:you\s+)?"
    r"(?P<about>about\s+|of\s+)?(?P<what>[^?]+?)\s*\??$", re.I)
# The same ask said as a question about the bot's memory rather than about what was said: "do you
# remember my sister", "do you know my age". The remembering word carries nothing, so the thing
# behind it is read like the rest of this module's asks. Only the person's own frames are taken -
# "my" and "what/where/how old i ..." - because the same words open a question about the world
# ("do you know the capital of peru", "do you remember the 90s"), and that is not a question
# about the chat. It is read here rather than in the store because the module already answers
# every fact the store keeps, in one set of sentences.
KNOW_ABOUT = re.compile(
    r"^\W*(?:and\s+|also\s+|so\s+|but\s+|ok(?:ay)?\s+|wait\s+|quick\s+|sorry\s+)?"
    r"(?:do|did|can|could)\s+(?:you|u)\s+(?:still\s+|actually\s+|even\s+|really\s+)?"
    r"(?:know|remember|recall)\s+"
    r"(?P<what>(?:anything\s+|something\s+|more\s+)?(?:about\s+|on\s+)?"
    r"(?:my|our)\s+\w[^?]*?|"
    r"(?:what|where|who|which|how\s+old)\s+(?:i|we)\s+[^?]*?)\s*\??$", re.I)
# Without its "about", the rest of the line has to be a thing ("did i mention the trip") and not
# a statement ("have i told you my name is sam").
A_STATEMENT = re.compile(r"\b(?:is|are|was|were|am|will|would|can|could|have|has|had|"
                         r"do|does|did|i|we|you|im|i'm|ive|i've|id|i'd|ill|i'll|we're|we've|"
                         r"youre|you're|dont|don't|didnt|didn't|cant|can't|wont|won't)\b", re.I)
# The knowing frame on an ask that names nothing: "do you remember what i told you" wants the
# line, not the whole picture.
NOTHING_NAMED = re.compile(r"^what\s+(?:i|we)\s+(?:told|said)(?:\s+(?:you|u|me))?\s*$", re.I)
# A thing they ask about by a bare pointing word is the whole chat, which the recall readers
# already answer ("what have i told you").
POINTING = frozenset("me it that this them us anything something everything".split())
# The fact asked for as a question rather than named by its noun: "do you know how old i am"
# asks the age, "do you remember what i do" the job. Each is turned into the phrase the store
# answers ("my age", "what i do"), so a question and the plain ask get the same sentence. Only
# the person's own facts are listed: "do you know where i can buy paint" is a question about the
# world, and it is not turned into "where i live".
IN_QUESTION = (
    (r"^(?:how old|what age)\s+(?:i|we)\s+(?:am|are|was|were)\b.*$", "my age"),
    (r"^what\s+(?:i|we)\s+(?:do|did)(?:\s+for (?:a living|work))?\b.*$", "what i do"),
    (r"^who\s+(?:i|we)\s+(?:am|are|was|were)\b.*$", "my name"),
    (r"^what\s+(?:i|we)(?:'m|'re| am|are|was|were)\s+(?:allergic|intolerant)\s+to\b.*$",
     "what im allergic to"),
    (r"^where\s+(?:i|we)\s+(?:live|lived|come from|was born|grew up|am from|'m from)\b.*$",
     "where i live"),
)
# The kinds of fact an ask can name instead of naming the thing: "the trip", "my job", "the
# money". The words are the store's own keys, so the answer is the fact it keeps under that key.
A_KIND = {"trip": "plan", "trips": "plan", "holiday": "plan", "holidays": "plan",
          "break": "plan", "travel": "plan", "flight": "plan", "flights": "plan",
          "hotel": "plan", "booking": "plan", "plan": "plan", "plans": "plan",
          "job": "job", "work": "job", "money": "budget", "budget": "budget",
          # The words people use for the money fact without naming it: a denial to "have i told
          # you about money" after "i'm skint this month" is the one answer that reads as a bot
          # that was not listening.
          "broke": "budget", "skint": "budget", "cash": "budget", "savings": "budget",
          # The things people own and do, where the word they ask with is not the word they
          # wrote: "have i told you about my car" after "i drive a ford focus", "about my
          # running" after "i run three times a week". The store keeps no fact under these, so
          # the words are only what finds their own line - and a denial there is a bot that was
          # not listening.
          "car": "car", "vehicle": "car", "van": "car", "drive": "car",
          "driving": "car", "drove": "car", "mot": "car",
          "bike": "bike", "bicycle": "bike", "cycling": "bike", "cycle": "bike",
          "running": "running", "run": "running", "jogging": "running", "jog": "running",
          "runner": "running",
          "feelings": "feelings", "feeling": "feelings", "feel": "feelings", "felt": "feelings",
          "mood": "feelings", "emotions": "feelings", "emotion": "feelings",
          "flat": "flat", "house": "flat", "home": "flat", "landlord": "flat", "rent": "flat",
          "boiler": "flat", "heating": "flat", "mortgage": "flat",
          "age": "age", "name": "name", "diet": "diet",
          "allergy": "allergies", "allergies": "allergies",
          # "have i told you about my children" is the kids they gave a turn ago, and "kids" and
          # "children" are one fact in the store, so the ask is answered with its own sentence
          # rather than a denial that contradicts the turn before.
          "kids": "kids", "kid": "kids", "children": "kids", "child": "kids"}
# A yes/no check of one thing the chat said about someone else: "is my mum coeliac", "is my son 7",
# "is my dad a teacher", "is my son called tom". The person is named, so the line that said the
# fact is the thing to compare with, and what the store keeps as keys is irrelevant: the check is
# whether the claim is in that line.
RELATION_WORDS = "|".join(sorted(extract.RELATIONS, key=len, reverse=True))
CHECK_OF_SOMEONE = re.compile(
    r"^\W*(?:is|are|was|were|does|do|did)\s+(?:my|our|your)\s+(?:" + RELATION_WORDS + r")"
    r"(?:'s|s)?\s+(?P<claim>[^?.!]{1,44})\s*[?.!]*$", re.I)
# What the chat said about that person, as the fact it is: the relation, a copula, and the thing
# said of them. Only this shape is compared with the claim, so "is my mum ok" is never "no" on
# the strength of "my mum is coeliac" - the two are not the same question.
# A correction is the same fact said again, so it opens with a word that says so: "actually my
# mum isnt coeliac", "no, my son is 8". Reading it as a change of subject left the older fact
# answering the check.
CORRECTION_WORDS = r"(?:and|also|so|actually|no|sorry|wait|oh|hmm|hold\s+on|correction|i\s+mean)"
CORRECTING = re.compile(r"^\W*(?:" + CORRECTION_WORDS + r"\b[,.!;:]?\s*){1,2}", re.I)
SAID_OF_SOMEONE = re.compile(
    r"^\W*(?:" + CORRECTION_WORDS + r"\b[,.!;:]?\s*){0,2}(?:my|our)\s+(?P<who>" + RELATION_WORDS + r")(?:'s|s)?\s+"
    r"(?:(?P<not>isnt|isn't|is not|wasnt|wasn't|was not|arent|aren't|are not|doesnt|doesn't|"
    r"does not|didnt|didn't|did not|hasnt|hasn't|has not|is n't)\s+(?P<pred>[^.,;!?]{1,40})"
    r"|(?P<verb>is|was|are|were|lives|works|has|got|goes|plays|studies|drives|does|did)\s+"
    r"(?P<pred2>[^.,;!?]{1,40}))", re.I)
# The same fact said again about a person who is already the one in play: "my mum is coeliac" then
# "sorry she isnt" is the newest word on the mum's coeliac, and reading it as a change of subject
# left the older line answering "is my mum coeliac" with a Yes they had just taken back. Only the
# pronoun the person can wear is read (and "they", which fits anybody), because "he isnt" after a
# line about the mum is a different person and names no fact of hers.
SAID_OF_PRONOUN = re.compile(
    r"^\W*(?:" + CORRECTION_WORDS + r"\b[,.!;:]?\s*){0,2}(?P<pron>she|he|they)(?:'s|s)?\s+"
    r"(?:(?P<not>isnt|isn't|is not|wasnt|wasn't|was not|arent|aren't|are not|doesnt|doesn't|"
    r"does not|didnt|didn't|did not|hasnt|hasn't|has not)\s+(?P<pred>[^.,;!?]{1,40})"
    r"|(?P<verb>is|was|are|were|lives|works|has|got|goes|plays|studies|drives|does|did)\s+"
    r"(?P<pred2>[^.,;!?]{1,40}))", re.I)
# A take-back with nothing after it: "sorry she isnt", "no he isnt either". The predicate is the
# one the fact just said, which is the line above, and a correction typed short is the commonest
# way anybody takes a fact back.
BARE_DENIAL = re.compile(
    r"^\W*(?:" + CORRECTION_WORDS + r"\b[,.!;:]?\s*){0,2}(?:my|our)\s+(?P<who>" + RELATION_WORDS
    + r")?(?:'s|s)?\s*(?P<not>isnt|isn't|is not|wasnt|wasn't|was not|arent|aren't|are not|"
    r"doesnt|doesn't|does not|didnt|didn't|did not|hasnt|hasn't|has not)\s*"
    r"(?:either|at all|really|actually|any ?more|no)?\s*[.!]*$", re.I)
BARE_DENIAL_PRONOUN = re.compile(
    r"^\W*(?:" + CORRECTION_WORDS + r"\b[,.!;:]?\s*){0,2}(?:she|he|they)(?:'s|s)?\s*"
    r"(?P<not>isnt|isn't|is not|wasnt|wasn't|was not|arent|aren't|are not|doesnt|doesn't|"
    r"does not|didnt|didn't|did not|hasnt|hasn't|has not)\s*"
    r"(?:either|at all|really|actually|any ?more|no)?\s*[.!]*$", re.I)
# The words a predicate of that sort is made of: two bare numbers are one fact (how old they are),
# and so are two names after "called". The verb decides the rest - "my mum lives in cork" says
# nothing about whether she is coeliac.
A_NUMBER = re.compile(r"^\d+(?:\s*(?:years?|months?)(?:\s+old)?)?$", re.I)
A_NAME = re.compile(r"^(?:called|named)\s+\S+$", re.I)
WITH_AN_ARTICLE = re.compile(r"^(?:a|an)\s+\S+$", re.I)


def _the_shape(verb, pred):
    """What a fact is about, in the coarsest words that tell one fact from another.

    (the verb, the sort of thing said of them): ("is", "number") for "my son is 7", ("is",
    "called") for "my son is called tom", ("is", "a") for "my dad is a teacher". A fact with the
    same shape as the claim is the newest word on the same thing, and no older line may overrule
    it.
    """
    kind = "said"
    if A_NUMBER.match(pred.strip()):
        kind = "number"
    elif A_NAME.match(pred.strip()):
        kind = "called"
    elif WITH_AN_ARTICLE.match(pred.strip()):
        kind = "a"
    return (verb, kind)


def _the_verb(fact):
    """A fact's verb, with a denial read as the thing it denies: "isnt" is "is"."""
    verb = fact.group("verb")
    if verb:
        return verb.lower()
    said = (fact.group("not") or "").lower().replace(" n't", "nt")
    for one, plain in (("is", "is"), ("was", "was"), ("are", "are"), ("does", "does"),
                       ("did", "did"), ("has", "has")):
        if said.startswith(one):
            return plain
    return said


def _the_same_thing(fact, pred, claim):
    """Whether a fact is about the same thing as the claim, said with a different value.

    "is my son 7" against a line that now says "my son is 8": the same verb, both bare numbers,
    so the 8 is the newest word on his age and the 7 is not confirmed by an older line.
    """
    return _the_shape(_the_verb(fact), pred) == _the_shape("is", claim)
# The words a claim is made of, without the article or the filler that carries no fact: "is my dad
# a teacher" asks about "teacher", and "my dad is a teacher" says it.
CLAIM_FILLER = frozenset("a an the some my our your of to in on at called is was are were be".split())
# A claim the store answers somewhere else: an allergy or a diet has its own reader with its own
# wording ("Your mum doesn't eat meat."), and a second answer here would say it worse.
CHECKED_ELSEWHERE = re.compile(r"allerg|\beat|eats|eating|vegan|vegetarian|pescatarian|diet", re.I)


ANIMAL = re.compile(r"\b(?:dog|cat|puppy|kitten|rabbit|hamster|bird|fish|parrot|horse|"
                    r"tortoise|guinea pig|pet)s?\b", re.I)
WHERE_I_LIVE = re.compile(r"^\W*(?:where\s+(?:i|we)\s+(?:live|stay)|where\s+(?:i|we)'?re\s+"
                            r"based|my\s+(?:address|house|home|flat|place)|the\s+place\s+"
                            r"(?:i|we)\s+live)\W*$", re.I)
NOT_MINE = re.compile(r"\bmy\s+(?:mum|mom|dad|father|mother|sister|brother|son|daughter|"
                      r"husband|wife|partner|friend|boss|niece|nephew|aunt|uncle|"
                      r"grandma|grandad|grandmother|grandfather|cousin)\b", re.I)


# The words that end a pointer and add nothing to it: "did i say that already" points at the chat
# the same way "did i say that" does.
ALREADY = re.compile(r"\s+(?:already|before|yet|so far|then|earlier)\b.*$", re.I)
# A line that asks something cannot be the thing they told the bot: "what did i say was wrong with
# my flat" is the question, and quoting it back as the answer reads as a bot that heard nothing.
ASKS = re.compile(r"^\W*(?:what|why|how|when|where|who|which|whose|did|do|does|is|are|was|"
                  r"were|can|could|should|would|will|have|has|am)\b", re.I)


# The same thing said as a statement instead of asked: "remember when i said my knee hurt",
# "remember we talked about lisbon", "remember me telling you about the boiler". The person is not
# asking about their knee - they are asking the bot to hold up its end of the chat - and main read
# it as a fresh question about the knee, so the advice came out again behind "Same answer, and it
# covers this:" and the line after it, "its better now", was filed under "remember" and answered
# with a revision tip. Only the remembering forms are read: "remember to buy milk" is a note to
# themselves and "remember when you said" is about the bot's own line, so both are left alone.
REMEMBERED = re.compile(
    r"^\W*(?:oh\s+|and\s+|so\s+|but\s+|hey\s+|wait\s+|quick\s+|ok(?:ay)?\s+)?"
    r"remember\s+(?:when\s+|that\s+)?"
    r"(?:(?:i|we)\s+(?:said|say|told\s+you|tell\s+you|mentioned|mention|talked|spoken|spoke|"
    r"chatted|went\s+on|were\s+on)"
    r"|me\s+(?:saying|telling\s+you|mentioning))"
    r"\s*(?:about\s+|of\s+)?(?P<what>[^?]+?)\s*\??$", re.I)
# A callback naming something this chat does not hold. The bot cannot see the conversation they
# are thinking of, so the line speaks for its own notes only: it never argues with what they
# remember, and the frame names the notes rather than the thing, because the thing a callback
# names is often a whole clause ("remember when i said i was quitting my job") and a note put
# around that clause ("nothing on i was quitting your job") is not a sentence.
CALLBACK_MISSED = ("I don't have that in this chat's notes — say it again and I'll keep it.",
                   "Nothing about that in what I've kept here — tell me and it's in.",
                   "I've only got this conversation to go on, and that isn't in it yet.")
# The denial a reader hands back when it has nothing. A callback is answered in the words of the
# notes instead, because it names the thing as a claim rather than asking about it.
A_DENIAL = re.compile(r"^\W*(?:i haven't kept a note|there's nothing on|nothing on)", re.I)


# The same ask said as a claim rather than as a question: "i told you about my knee earlier",
# "i mentioned the trip before". The person is not telling the bot news a second time - they are
# asking whether it kept it - so the thing behind the claim is read like the rest of this
# module's asks, and a thing the chat does not hold is answered with the honest miss rather than
# with a nod ("Thanks for telling me - I'm here if you want to dig into any of that" was the
# whole of the answer before this, which is what a friend says to a stranger repeating himself).
CLAIMED_ABOUT = re.compile(
    r"^\W*(?:and\s+|also\s+|so\s+|but\s+|ok(?:ay)?\s+|look\s+|listen\s+|hey\s+)?"
    r"(?:i|we)\s+(?:already\s+|just\s+|definitely\s+|did\s+|have\s+|had\s+)?"
    r"(?:told|tell|mentioned|mention|said|say|talked|talk|spoke)\s+"
    r"(?:you|u)\b\s*(?:(?:about|of|that)\s+)?(?P<what>[^?]+?)\s*[.?!]*$", re.I)
# And the same without "you", which only a verb about a subject can carry: "i mentioned the trip
# before" asks whether it was kept, while "i told my boss yesterday" reports the morning and has
# nothing of the chat in it, so "told" and "said" are not read here.
A_CLAIM_WITHOUT_YOU = re.compile(
    r"^\W*(?:and\s+|also\s+|so\s+|but\s+|ok(?:ay)?\s+|look\s+|listen\s+|hey\s+)?"
    r"(?:i|we)\s+(?:already\s+|just\s+|did\s+|have\s+|had\s+)?"
    r"(?:mentioned|mention|talked|talk|spoke)\s+(?:(?:about|of|that)\s+)?"
    r"(?P<what>[^?]+?)\s+(?:earlier|before|already|ages\s+ago|a\s+minute\s+ago|just\s+now|"
    r"last\s+(?:time|week|night))\s*[.?!]*$", re.I)
# The words that make a claim without "you" a claim about this chat: "i mentioned the trip
# before" is asking whether it was kept, while "i said hello to her" is telling the bot what
# happened and has nothing to look up.
A_TIME_AGO = re.compile(r"\b(?:earlier|before|already|yesterday|last\s+(?:time|week|night)|"
                        r"ages\s+ago|a\s+minute\s+ago|just\s+now|"
                        r"in\s+the\s+(?:last|previous)\s+(?:chat|conversation))\b", re.I)
A_TRAILING_TIME = re.compile(r"\s+(?:earlier|before|already|yesterday|ages\s+ago|just\s+now|"
                             r"a\s+minute\s+ago|last\s+(?:time|week|night))\s*$", re.I)
# The same ask behind the remembering word: "do you remember me telling you about my knee",
# "do you remember when i told you about the trip". KNOW_ABOUT takes the thing itself ("do you
# remember my knee"), and this is the shape where the telling is said out loud.
REMEMBER_TELLING = re.compile(
    r"^\W*(?:and\s+|also\s+|so\s+|but\s+|ok(?:ay)?\s+|wait\s+|quick\s+)?"
    r"(?:do|did|can|could)\s+(?:you|u)\s+(?:remember|recall)\s+"
    r"(?:(?:that|when|me|i|us|we)\s+){0,2}"
    r"(?:told|telling|tell|talked|talking|talk|mentioned|mentioning|mention|said|saying|say)"
    r"(?:\s+(?:you|u))?\s*(?:about\s+|of\s+)?(?P<what>[^?]+?)\s*\??$", re.I)
# A thing a claim names is sometimes a whole clause: "i told you i was quitting my job" claims a
# told thing and not a thing, so the miss is said in the frames that name the notes rather than
# around the clause (see CALLBACK_MISSED).
A_CLAUSE = re.compile(r"^(?:i|we|im|i'm|ive|i've|id|i'd|he|she|they|you|it)\b\s*\w*", re.I)

# They have closed the subject rather than opened one. "i don't want to talk about it" after the
# knee is the person setting a limit on the chat, and every other answer is wrong: advice asks
# them to keep talking about the thing they just refused, and reading it as a claim about the
# notes quotes it back as a thing to file ("Nothing in my notes says "already, i dont want to
# talk about it" yet - tell me and I'll keep it"). The same line arrives behind a claim ("i told
# you already, i dont want to talk about it"), so a telling in front of it is taken off first.
_THE_STOP = r"(?:talk|speak|discuss|go\s+into|get\s+into)"
A_BOUNDARY = re.compile(
    r"^\W*(?:and\s+|but\s+|so\s+|ok(?:ay)?\s+|well\s+|look\s+|honestly\s+|"
    r"please\s+|just\s+)*"
    r"(?:(?:i|we)\s+(?:(?:really|just|honestly|actually|kind\s+of|sort\s+of)\s+)*"
    r"(?:don'?t|dont|do\s+not|wouldn'?t|wouldnt|would\s+not|never)\s+"
    r"(?:want|wanna|wish|like)\s+to\s+" + _THE_STOP + r"\s+(?:about|of)\s+"
    r"(?:it|that|this|that\s+one|this\s+one)"
    r"|(?:i|we)(?:'d|\s+would)\s+rather\s+not\s+" + _THE_STOP + r"\s+(?:about|of)?\s*"
    r"(?:it|that|this)?"
    r"|(?:can\s+we|can\s+i|let'?s|lets)\s+(?:not\s+" + _THE_STOP + r"\s+(?:about\s+)?"
    r"(?:it|that|this)|drop\s+(?:it|this\s+one)|leave\s+(?:it|that))"
    r"|(?:leave|drop)\s+(?:it|that|this))\s*(?:please|for\s+now|now|alright|ok|okay|thanks|"
    r"thank\s+you)?\W*$", re.I)
# The claim that is only a preamble to the boundary: "i told you already, i dont want to talk
# about it" is one line made of a telling with nothing in it and a limit with everything.
A_CLAIM_BEFORE = re.compile(
    r"^\W*(?:and\s+|but\s+|so\s+|ok(?:ay)?\s+|look\s+|listen\s+|hey\s+)?"
    r"(?:i|we)\s+(?:already\s+|just\s+|did\s+)?(?:told|tell|said|say|mentioned|mention)\s+"
    r"(?:(?:you|u)\b[^,;]*[,;]\s*|(?=i\s|we\s|im\s|i'm\s))", re.I)
# What the bot says to a boundary: short, warm, and it does not ask about the thing. The last
# word is theirs, so no question goes on the end.
LEFT_THERE = (
    "Fair enough - I'll leave that one alone.",
    "Of course. I won't bring it up again.",
    "Alright. That's the last I'll say on it.",
    "No problem - let's leave that one.",
    "Understood. Nothing more on it from me.",
    "That's fair. I'll not raise it again.",
)


# A claim whose telling is nothing but a time word: "i told you already", "i said that before",
# "i mentioned it earlier". The person is not naming a thing the store should hold, they are
# saying the bot ought to know it, so the note is handed back rather than denied - "I haven't
# kept a note of already" is the store reading "already" out as a thing they said.
A_LEADING_TIME = re.compile(r"^\W*(?:already|before|earlier|just|then|so\s+far)\b[,;:]?\s*", re.I)
A_TIME_ONLY = re.compile(r"^\W*(?:already|before|earlier|that|it|this|you\s+know|"
                         r"you\s+already\s+know|yes|yeah|right)\W*$", re.I)


# The barest form of the claim: "i told you", "i said", "i mentioned it already". Nothing follows
# the verb, so there is no telling to look up at all.
A_BARE_CLAIM = re.compile(
    r"^\W*(?:and\s+|but\s+|so\s+|ok(?:ay)?\s+|look\s+|listen\s+|hey\s+)?"
    r"(?:i|we)\s+(?:already\s+|just\s+|did\s+)?(?:told|tell|said|say|mentioned|mention)\s+"
    r"(?:you|u)?\s*(?:about\s+)?(?:it|that|this|already|before|earlier|so\s+far|"
    r"you\s+already\s+know)?\W*$", re.I)


def _tells_nothing(text):
    """True when the line claims the bot was told and names nothing that it was told."""
    line = str(text or "")
    if A_BARE_CLAIM.match(line):
        return True
    match = CLAIMED_ABOUT.match(line) or A_CLAIM_WITHOUT_YOU.match(line)
    if not match:
        return False
    what = A_TRAILING_TIME.sub("", " ".join(match.group("what").split()))
    what = A_LEADING_TIME.sub("", what).strip(" .,!")
    return not what or bool(A_TIME_ONLY.match(what))


def _handed_back(text, memory):
    """"So you did - you said your knee hurts.", from the last thing they said, or None.

    Their own last line is the thing the claim is about, and it goes back in the second person
    the way every other store reply does. A chat with nothing in it has nothing to hand back, and
    the claim is left to whichever module answers the news.
    """
    mine = " ".join(str(text or "").lower().split())
    lines = []
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in turns if isinstance(turns, list) else []:
        if isinstance(turn, dict) and str(turn.get("user", "")).strip():
            lines.append(" ".join(str(turn["user"]).split()))
    for said in reversed(lines):
        if said.lower() == mine:
            continue                  # this turn is not the chat it is following on from
        quoted = _quote(said, memory)
        if not quoted:
            continue
        quoted = quoted[0].lower() + quoted[1:]
        return pick(["So you did - " + quoted,
                     "You're right - " + quoted,
                     "You did - " + quoted,
                     "Fair enough - " + quoted], memory)
    return None


def is_a_boundary(text):
    """True when the line is the person closing a subject rather than asking about one."""
    line = " ".join(str(text or "").split())
    if not line:
        return False
    if A_CLAIM_BEFORE.match(line):
        line = A_CLAIM_BEFORE.sub("", line, count=1)
    return bool(A_BOUNDARY.match(line))


def at_a_boundary(text, memory=None):
    """The short answer to a boundary, or None when the line is not one."""
    if not is_a_boundary(text):
        return None
    return pick(list(LEFT_THERE), memory)


def _a_boundary_in_a_claim(text):
    """True when the telling in front of the boundary tells nothing: it is a preamble."""
    return bool(A_CLAIM_BEFORE.match(" ".join(str(text or "").split())))


# "have i told you about anything about food" says "anything about" and then the thing; keeping
# it gives "you haven't told me about anything about food yet", which is the bot reading the
# question back with the words in the wrong order.
SOMETHING_ABOUT = re.compile(r"^(?:anything|something|much|any|more|else|stuff)\s+"
                             r"(?:about|on|regarding|to do with)\s+", re.I)


def _the_ask(text):
    """The thing they ask about ("my sister", "the trip"), or None when the line is not this ask."""
    line = str(text or "")
    if is_a_boundary(line):
        return None       # a limit on the chat, not a thing asked about in it
    match = (TOLD_ABOUT.match(line) or KNOW_ABOUT.match(line)
             or CLAIMED_ABOUT.match(line) or A_CLAIM_WITHOUT_YOU.match(line)
             or REMEMBER_TELLING.match(line))
    if not match:
        return None
    said = A_TRAILING_TIME.sub("", " ".join(match.group("what").split())).strip(" .,!")
    if not said:
        return None
    if ((match.re in (CLAIMED_ABOUT, A_CLAIM_WITHOUT_YOU, REMEMBER_TELLING))
            and said.split()[0].lower() in POINTING):
        # "i mentioned it before" points at the chat itself, and there is nothing in the store to
        # look up under "it": a denial would be a claim that nothing was kept, which is not true.
        return None
    # "have i told you my name is sam" states the fact rather than asking about it, so it is
    # news. The knowing frame (KNOW_ABOUT) only ever takes a thing ("my age") or a question
    # ("what i do"), so it needs no such guard.
    if match.re is TOLD_ABOUT and not match.group("about") and A_STATEMENT.search(said):
        return None
    return said


def ABOUT_THE_CHAT(text, memory=None):
    """True when the line is this ask, whatever word in it another module would claim.

    A specialist module proposes from one word: "have we talked about food" is handed to the
    answers lane because of "food", and "did we talk about my mum" because of "mum", so the store
    is never asked about a line that is about the chat itself. The store says which of its own
    proposals this is (bot/modules/arbiter.py, TAKES_AS_IT_COMES).
    """
    if _tells_nothing(text):
        return True       # "i told you already" is about the chat, not about the world
    if is_a_boundary(text):
        # "i told you, i don't want to talk about it" is about the chat itself, and the store is
        # the part that can agree to leave it: without this the word "talk" sent the turn to the
        # answers lane, which proposed a card about small talk at a party.
        return True
    said = _the_ask(text)
    if not said:
        return False
    what = re.sub(r"^(?:the|my|our|a|an)\s+", "", said).strip(" .,!")
    what = ALREADY.sub("", what)
    return bool(what) and what.lower() not in POINTING


def answer(text, memory, facts=None, plain=None, claims=None):
    """The thing they ask about, said back from the chat, or None when the line is not this ask.

    `facts` is the store's own reader for each kind of fact (bot/modules/memory_store.py,
    `_told_readers`), so an ask about their allergies is answered with the same sentence the
    store says for "what am i allergic to": one set of sentences, and the two cannot drift apart.
    `plain` is the store's answer to the same ask in its plain words ("do you know what i do" ->
    "what i do"), which is how a fact the store keeps under a shape this module has no kind for
    (the car they drive, the job they do) is answered rather than denied. `claims` says whether
    the store reads the line as being about what it keeps, which is what makes a denial honest:
    "do you know my age" may be told nothing is kept, "do you know where i can buy paint" may not.
    """
    if is_a_boundary(text):
        # "i don't want to talk about it" is the person closing the subject, and the store is
        # where a limit like that is kept: the reply agrees to leave it, and asks nothing.
        return at_a_boundary(text, memory)
    if _tells_nothing(text):
        # They are not naming a thing to look up, they are saying the bot should know it: the
        # last thing they said, handed back, is the answer - not a denial of "already".
        handed = _handed_back(text, memory)
        if handed:
            return handed
    if _a_claim_about_the_chat(text) and not _an_earlier_line(memory, text):
        # "i told you my dog died" as the first thing said is a telling, not a claim about what
        # the notes hold: nothing has been said in this chat yet, so there is nothing to miss and
        # the line belongs to whoever answers the news (see `callback`).
        return None
    checked = check(text, memory)
    if checked:
        return checked
    pointed = _a_claim_that_points(text, memory)
    if pointed:
        return pointed
    said = _the_answer(text, memory, facts, plain, claims)
    if said and A_DENIAL.match(said) and A_CLAUSE.match(_the_ask(text) or ""):
        # The claim named a clause the chat does not hold: "I haven't kept a note of i was
        # quitting my job" is not a sentence, so the miss speaks for the notes instead.
        return pick(list(CALLBACK_MISSED), memory)
    if not said or not SAID_AS_IT_IS.match(said):
        return _with_the_yes(said, text)
    return said


def a_denial(said):
    """True when the sentence says the chat does not hold the thing - a miss, not a recall."""
    said = str(said or "")
    return bool(A_DENIAL.match(said) or A_QUOTE.search(said) or SAID_AS_IT_IS.match(said))


# The ask is a yes/no question - "have i told you", "did i mention", "do you remember" - so the
# sentence the store hands back wants the yes in front of it: "Yes — you've got a puppy called
# Rex." reads as an answer where "You've got a puppy called Rex." reads as a change of subject.
# A sentence that answers itself already (a denial, a quote, the "nothing yet") is left alone.
SAID_AS_IT_IS = re.compile(r"^(?:yes|no|nothing|you haven't|i haven't|there's nothing|"
                           r"there is nothing|not that i)\b", re.I)
# Only a common sentence opener is lowercased after the dash: "Yes — you live in Leeds." A
# proper noun keeps its capital because it is not one of these.
LOWERABLE = frozenset("you your it its they the there that this we he she i".split())


def _lower_first(said):
    """The sentence with a common opener lowercased, ready to follow "Yes — "."""
    said = str(said or "")
    if not said:
        return said
    first = said.split(" ", 1)[0].strip(".,!?\"'—-").lower().split("'")[0]
    if first in LOWERABLE:
        return said[0].lower() + said[1:]
    return said


# Any quote at all, whatever it was typed with: a sentence that quotes a phrase ("I don't have
# “i was tired” in my notes - say it and I'll hold on to it") is answering itself, and the
# typographic quotes the clause pool uses slipped past a test for the straight one, so the denial
# came out as "Yes — i don't have "i was tired" in my notes". A line may not say yes and deny.
A_QUOTE = re.compile("[\"\u201c\u201d]")


def _with_the_yes(said, text):
    """`said` with "Yes — " in front of it when the line is a yes/no question about the chat."""
    said = str(said or "")
    if not said or A_QUOTE.search(said) or not TOLD_ABOUT.match(str(text or "")):
        return said
    return "Yes — " + _lower_first(said)


def _the_remembered(text):
    """"my knee hurt" out of "remember when i said my knee hurt", or None when it is not this."""
    match = REMEMBERED.match(str(text or ""))
    if not match:
        return None
    said = " ".join(match.group("what").split()).strip(" .,!")
    said = ALREADY.sub("", said).strip()
    if not said or said.lower() in POINTING:
        return None
    return said


def A_CALLBACK(text, memory=None):
    """True when the line asks the bot to remember a thing they said, whatever else it names.

    A callback names something the chat already heard ("remember when i said my knee hurt"), so
    the word in it is also a topic the knowledge base reads: `answers` took the line on "knee"
    and resigned the advice. The store is the only part of the bot that can say what was said, so
    it says so in front of its reply (bot/modules/arbiter.py, `TAKES_AS_IT_COMES`).
    """
    return bool(_the_remembered(text))


def a_callback_the_chat_has(text, memory):
    """True when the line is a callback to something this chat already holds.

    The store files each line as the subject of the conversation (bot/memory/topics.py, `note`),
    and a callback names a subject the conversation is on already. Kept as a new subject, the
    word "remember" went into the topic and the turn after it was read against remembering.
    """
    said = _the_remembered(text)
    if not said:
        return False
    what = re.sub(r"^(?:the|my|our|a|an)\s+", "", said).strip(" .,!")
    return bool(_line_about(memory, what or said, skip=text))


def _a_claim_about_the_chat(text):
    """True when the line claims something of the chat was already told or mentioned."""
    said = str(text or "")
    return bool(CLAIMED_ABOUT.match(said) or A_CLAIM_WITHOUT_YOU.match(said))


def _an_earlier_line(memory, text):
    """Whether the chat holds a line of theirs other than this one.

    One check for the whole bot (bot/memory/history.py): a reader that counts turns for itself
    here would disagree with the recall readers about what counts as an earlier turn.
    """
    return history.an_earlier_turn(memory, text)


def callback(text, memory, facts=None, plain=None, claims=None):
    """The thing they said, handed back to them, or None when the line is not this.

    A callback is about the chat, not about the world: the answer is the thing itself in their
    own words, or the fact the store keeps of it, and never the advice again. A callback naming
    nothing the store has is answered as a missing note rather than as a correction of what they
    remember, because the bot cannot see into the conversation the person is thinking of.
    """
    said = _the_remembered(text)
    if not said:
        return None
    # The callback is the ask in the telling's clothes, so the readers that answer "have i told
    # you about my puppy" answer this too: the fact the store keeps ("Yes \u2014 you've got a
    # puppy called Rex."), their own line quoted, or a note that there is nothing yet. One set of
    # readers, so a shape added to one is answered by the other.
    if is_a_boundary(text):
        # "i don't want to talk about it" is the person closing the subject, and the store is
        # where a limit like that is kept: the reply agrees to leave it, and asks nothing.
        return at_a_boundary(text, memory)
    if _a_claim_about_the_chat(text) and not _an_earlier_line(memory, text):
        # "i told you my dog died" as the first thing said cannot be a claim about what this chat
        # kept - nothing has been said here - and the person is telling it now. Answered as a miss
        # it turns a bereavement into an argument about notes ("There's nothing on your dog died in
        # what I keep"), where the telling read as news gets the answer the news deserves. A
        # "remember when we talked about lisbon" opening is still a question about the chat, and
        # the honest miss is the right answer to it.
        return None
    recalled = answer("have i told you about " + said, memory, facts, plain, claims)
    if recalled and not A_DENIAL.match(str(recalled)):
        return recalled
    return pick(list(CALLBACK_MISSED), memory)


def _the_answer(text, memory, facts=None, plain=None, claims=None):
    """The readers that answer one thing they ask about, in the order that reads best."""
    said = _the_ask(text)
    if not said:
        return None
    bare = SOMETHING_ABOUT.sub("", said).strip()
    pointed = _the_proof_they_asked_for(bare, text, memory)
    if pointed:
        return pointed
    noframe = str(text or "")
    # "what i told you" names nothing at all: it is the store's own quoting ask ("Your own words
    # were ..."), and the picture is not what they asked for.
    know = KNOW_ABOUT.match(noframe) and not NOTHING_NAMED.match(bare)
    if NOTHING_NAMED.match(bare):
        # "do you remember what i told you" names nothing, so there is nothing to deny: the
        # store's own quoting reader says the last line back.
        return None
    if know:
        # "do you know how old i am" asks the fact in a question rather than by its name. The
        # store answers the plain words itself ("my age", "what i do"), so the frame is turned
        # into the phrase its own reader knows before anything is looked up.
        for pattern, plain_ask in IN_QUESTION:
            if re.match(pattern, bare, re.I):
                bare = plain_ask
                break
    if plain and know and bare.lower() not in POINTING:
        # Only the knowing frame is read this way: "have i told you about my job" is a question
        # about the chat and is answered below, in this module's own words.
        kept = plain(bare)
        if kept:
            return kept
    what = re.sub(r"^(?:the|my|our|a|an)\s+", "", bare).strip(" .,!")
    what = ALREADY.sub("", what).strip()
    if not what or what.lower() in POINTING:
        return None
    known = user(memory)
    theirs = _about_a_person(memory, what)
    if theirs is not None:
        return theirs
    someone = _the_person_a_pronoun_points_at(memory, what)
    if someone:
        return _about_a_person(memory, someone)
    pet = _about_a_pet(memory, what, known, facts)
    if pet:
        return pet
    # A thing asked about by the name of its kind ("the money", "my name") is the fact itself,
    # and the fact reads better than the line it came from ("Yes — you're Sam." over quoting
    # "my name is sam"). A kind word beside anything else ("the trip to lisbon") is only a hint,
    # and the line that names the thing is the better answer there, so that is tried first.
    if WHERE_I_LIVE.match(what):
        # "have i told you about where i live" is the place they live, and the store says it in
        # its own words ("You live in Leeds.") rather than quoting "i live in leeds" back.
        said = ((facts or {}).get("places") or (lambda memory: ""))(memory)
        if said:
            return said
    if _names_only_a_kind(what):
        kept = _the_fact_of_that_kind(memory, what, known, facts)
        if kept:
            return kept
    # A kind word is not the word they used: "have i told you about work" after "i hate my job"
    # denied the job they had just given, because no line of theirs says "work". The words of a
    # kind are the store's own reading of it ("work" and "job" are one fact), so the line about
    # that fact is found under either word.
    kind_words = _the_words_of_the_kind(what)
    if kind_words:
        quoted = _line_about(memory, " ".join(sorted(kind_words)), whole_words=True, skip=text)
        if quoted:
            return _quote(quoted, memory)
    kept = _the_fact_of_that_kind(memory, what, known, facts)
    if kept:
        return kept
    # The store's own sentence comes before the line is quoted: it says the fact the way the bot
    # says it ("You told me your birthday is in august."), where the quote is the raw line.
    # A word in the ask can name something the store keeps without being that fact's plain name:
    # "have i told you anything about nuts" after "i have a nut allergy" was answered "I haven't
    # kept a note of nuts" while the store held the allergy. Only a sentence that really says the
    # fact is used, so a reader with nothing to say cannot turn a miss into an answer.
    named = _the_fact_that_names(memory, what, known, facts)
    if named:
        return named
    quoted = _line_about(memory, what, skip=text)
    if quoted:
        return _quote(quoted, memory)
    if know and claims is not None and not claims():
        # "do you know where i can buy paint" is the knowing frame on a question about the
        # world: the store does not read the line as being about what it keeps, so it is left to
        # whoever can answer it rather than denied as something the person said.
        return None
    dated = _the_property_of_the_thing(memory, bare, facts)
    if dated:
        return dated
    return _no_note(_yours(bare), memory)


# A recall frame around a property word is the property ask about the thing in hand, not a thing
# called "when". "did i tell you when" after "my sister is getting married in june" was answered
# "I haven't kept a note of when", while the chat held the month and the same chat answered "when
# is it" with "In June." - the store denying a date it had kept one line earlier. The date
# readers already answer the property ask, so this is the same question with the frame in front
# of it. "where" is the same shape one kind over: "did i tell you where" after "i live in leeds"
# denied the town the store had just kept.
A_DATE_PROPERTY = frozenset(("when", "what day", "what date", "what time", "which day",
                             "the day", "the date", "the time"))
A_PLACE_PROPERTY = frozenset(("where", "what place", "which place", "the place"))


def _the_property_of_the_thing(memory, what, facts):
    """What the chat holds for the property the ask names, when it names the property only."""
    asked = " ".join(str(what or "").lower().split()).strip(" .,!?")
    if asked in A_DATE_PROPERTY:
        from .when import when_answer
        # "when is it" is the same ask with the frame taken off: the date readers read it as the
        # newest dated line of theirs that the chat is still on (bot/memory/when.py, `_points_back`).
        return when_answer("when is it", memory) or None
    if asked in A_PLACE_PROPERTY:
        said = ((facts or {}).get("places") or (lambda memory: ""))(memory)
        return said or None  # "You live in Leeds." - the place the store keeps, not a denial
    return None


def _a_clause_is_named(line):
    """True when a claim about the chat names a sentence as well as the telling."""
    found = CLAIMED_ABOUT.match(str(line or "")) or A_CLAIM_WITHOUT_YOU.match(str(line or ""))
    if not found:
        return False
    return bool(A_CLAUSE.match(" ".join(str(found.group("what") or "").split())))


def _the_thing_the_chat_is_on(memory):
    """The phrase the chat is on, from the store's own reader, or "" when it names nothing."""
    # The reader lives in the store, not in the module: `bot/modules/memory_store.py` has no
    # such name, so this import raised every time the proof path was reached and the turn fell
    # back to the composer's hedge - the person asked what they had told the bot and got "A quick
    # search online will get you a solid answer". Read from the file that defines it.
    from .store_replies import _the_thing_the_chat_is_on as about
    return about(memory) or ""


def _no_note(thing, memory):
    """The denial, said about the note rather than about the chat.

    "im saving for a car" then "have i told you anything about money" was answered "You haven't
    told me about money yet." - a claim about what the person said, and false: they had said
    something about money, in words the store files as a plan. How people say money, or a
    friend, is unbounded ("saving for a car", "best mate"), so no list of words closes it. What
    the bot does know for certain is its own note, so that is what it speaks for: a note that
    has nothing under that word is true however they said it.
    """
    if _the_thing_is_a_clause(thing):
        # "i told you i was quitting" hands back a clause, not a name, and a preposition in
        # front of it makes a sentence that is not English: "there's nothing on i was quitting
        # in what I keep". A clause is quoted, so what is missing from the notes is said as the
        # thing they said it in.
        return pick(["Nothing in my notes says \u201c" + thing + "\u201d yet — tell me and "
                     "I'll keep it.",
                     "I don't have \u201c" + thing + "\u201d in my notes — say it and I'll "
                     "hold on to it.",
                     "\u201c" + thing + "\u201d isn't in what I keep yet — tell me and I'll "
                     "remember it."],
                    memory)
    return pick(["I haven't kept a note of " + thing + " — tell me and I'll remember it.",
                 "There's nothing on " + thing + " in what I keep — say it and I'll hold "
                 "on to it.",
                 "Nothing on " + thing + " in my notes yet — tell me and I'll keep it."],
                memory)


# A pronoun opening a clause, or a verb in it, is what tells a clause from a name: "i was
# quitting" is a sentence they said, "my knee" is a thing they have.
A_CLAUSE_OPENING = re.compile(
    r"^(?:i|we|he|she|they|it|you|there|my|our)\b|\b(?:was|were|am|is|are|had|have|has|"
    r"did|do|does|will|would|can|could|should)\b", re.I)


def _the_thing_is_a_clause(thing):
    """True when what they handed back is a sentence they said, not the name of a thing."""
    words = str(thing or "").split()
    if not words:
        return False
    if len(words) > 3:
        return True
    return bool(A_CLAUSE_OPENING.search(" ".join(words)))


# The words a person hands their own line back with, before the line itself: "i said the party is
# on tuesday", "i mentioned the scan". A preposition after them names the thing rather than saying
# anything about it ("i told you about the party"), so that shape keeps its own line.
REPORTED = re.compile(r"^\s*(?:and\s+|also\s+)?(?:i|we)\s+(?:did\s+)?(?:say|said|told\s+you|"
                      r"mentioned|was\s+saying|were\s+saying)\b[:,]?\s+(?P<clause>(?!about\b|of\b)"
                      r".+)$", re.I)


# The echo of a line that was itself a telling: "you told me about your mum", "you said to me ...".
# The frame goes on a line that states a fact; on one of these it is the telling twice.
TELLING_ALREADY = re.compile(r"^you (?:told me|said to me|mentioned to me)\b")


def _quote(line, memory):
    """Their own line, said back to them, when no fact of the store says it better.

    The line is theirs, so it goes back in the second person and without the quote marks:
    "You said your kids are 6 and 9" says what a friend would, where `You said: "my kids are 6
    and 9"` hands the person a stranger's words - "my" is the bot talking about somebody else's
    kids. Every other reply this store gives is in the second person, and a quote was the one
    place it was not.
    """
    # "i said the party is on tuesday" is already the person reporting their own words, so a
    # frame that takes the store's line out of their mouth doubles it: "you said you said the
    # party is on tuesday". What they reported is what is said back.
    reported = REPORTED.match(str(line or ""))
    if reported:
        line = reported.group("clause")
    # Chat-speak has to be opened before it goes back: "im learning spanish" is "you're
    # learning spanish", where the raw "im" would come back as itself.
    opened = re.sub(r"\bi\s*m\b", "i'm", str(line or ""), flags=re.I)
    opened = re.sub(r"\bi\s*ve\b", "i've", opened, flags=re.I)
    said = say_it_back(opened).strip().rstrip(".")
    if not said:
        return pick(["You told me that already", "You did say that"], memory)
    # The frames open with the same word so a yes/no question can put "Yes — " in front without
    # the sentence reading as two of them ("Yes — What you said was ...").
    said = said[0].lower() + said[1:]
    # A whole sentence ends with a full stop, the way every other store reply does.
    said += "."
    # A line that begins "i told you ..." is a receipt already: the store's frame on top of it made
    # "You told me you told me about your mum", the bot saying the telling twice. What they told is
    # said back without the frame, because the echo carries who told whom on its own.
    if TELLING_ALREADY.match(said):
        return said[0].upper() + said[1:]
    return pick(["You said " + said,
                 "You told me " + said,
                 "You did say " + said], memory)


def _the_words_of_the_kind(what):
    """Every word the store files under the kind they asked about, or an empty set.

    "the job" is filed as `job`, and the lines people write about it say "work", so both words
    have to find it. A kind is asked about one at a time; "my money and my job" is not this."""
    kinds = set()
    for word in re.split(r"[\s,]+", str(what or "").lower()):
        kind = _the_kind_of(word)
        if not kind:
            return set()
        kinds.add(kind)
    if len(kinds) != 1:
        return set()
    kind = kinds.pop()
    return {word for word, key in A_KIND.items() if key == kind}


# The person asks about their own thing ("my back"), and the reply is the bot's, so it says
# "your": "You haven't told me about my back yet" is the bot reading their line back at them.
MINE = re.compile(r"\b(my|our|me|mine|ours)\b", re.I)
YOURS = {"my": "your", "our": "your", "me": "you", "mine": "yours", "ours": "yours"}


# A clause has a verb in it; a name does not. "i was quitting my job" is a sentence they said and
# is handed back as it was said, where "my knee" is a thing and takes the other person's possessive.
A_VERB_IN_A_CLAUSE = re.compile(
    r"\b(?:was|were|am|is|are|had|have|has|did|do|does|will|would|can|could|should|going)\b",
    re.I)


def _yours(phrase):
    """The thing asked about, said from the bot's side: "my back" -> "your back".

    A thing is a name and takes the other person's possessive. A whole clause is not: "i was
    quitting my job" handed back with only the "my" turned is neither their words nor the bot's
    ("i was quitting your job"), so a clause is handed back as it was said and quoted.
    """
    said = str(phrase or "")
    if A_VERB_IN_A_CLAUSE.search(said):
        return said
    return MINE.sub(lambda found: YOURS.get(found.group(1).lower(), found.group(1)), said)


def _the_person_a_pronoun_points_at(memory, what):
    """Who "her", "him" or "them" is: the last person the chat named, or "".

    "my sister lives in cork" then "have i told you about her" is a question about the sister, and
    the store has their line about her. Answering "you haven't told me about her yet" says the
    opposite of the truth to the person who has just said it.
    """
    word = str(what or "").strip().lower().rstrip(".,!?")
    if word not in ("her", "him", "them", "they"):
        return ""
    entry = None
    for kept in reversed(others(memory)):
        if isinstance(kept, dict) and kept.get("who"):
            entry = kept
            break
    if entry:
        return str(entry["who"]).lower().rstrip("s")
    for turn in reversed(memory.get("turns") or []):
        said = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(said, str):
            continue
        for other in re.findall(r"[a-z]+", said.lower()):
            if other.rstrip("s") in extract.RELATIONS:
                return other.rstrip("s")
    return ""


def _words_of(said):
    """The words a claim or a fact is made of: no articles, no punctuation, no filler."""
    return {word for word in re.findall(r"[a-z0-9']+", str(said or "").lower())
            if word not in CLAIM_FILLER and len(word) > 1 or word.isdigit()}


def check(text, memory):
    """A yes/no check of a fact the chat gave about someone else, answered from that line.

    "my mum is coeliac" then "is my mum coeliac" was answered with the search hedge, while "what
    do you know about my mum" said the fact back. The fact is in the chat either way, and a
    question about it is a memory question.

    Only a **yes** is said here, and a **no** only when the chat said the same thing the other
    way round ("my mum isnt coeliac"), because the claim has to be in the line for the answer to
    be sound: "is my mum ok" after "my mum is coeliac" is a different question, and the hedge is
    a better answer to it than a confident "no". Anything that does not match is left to the
    readers that already answer it (`None`).
    """
    found = CHECK_OF_SOMEONE.match(str(text or ""))
    if not found:
        return None
    claim = found.group("claim")
    if CHECKED_ELSEWHERE.search(claim):
        return None
    asked = _words_of(claim)
    if not asked:
        return None
    who = found.group(0).lower()
    who = next((word for word in re.findall(r"[a-z]+", who)
                if word in extract.RELATIONS), "")
    if not who:
        return None
    # A newer line about the same thing, said with a different value, is the last word on it:
    # "my son is 7" then "my son is 8" leaves "is my son 7" unanswered, and never a Yes from the
    # line the chat has just corrected. Both are their own words, so the answer names both.
    newer = None
    newer_said = ""
    taken_back = False
    for said in reversed(_their_lines(memory, who)):
        fact = SAID_OF_SOMEONE.match(said)
        by_pronoun = False
        if not fact:
            # A take-back with nothing after it is read before the pronoun fact, or the word that
            # makes it a take-back ("either") is taken for the fact itself.
            bare = BARE_DENIAL_PRONOUN.match(said) or BARE_DENIAL.match(said)
            if bare is not None:
                named = (bare.groupdict().get("who") or "").strip().lower().rstrip("s")
                if not named or named == who:
                    taken_back = True
                continue
            fact = SAID_OF_PRONOUN.match(said)
            by_pronoun = bool(fact)
        if not fact:
            continue
        pred = fact.group("pred") or fact.group("pred2") or ""
        if not asked <= _words_of(pred):
            if newer is None and _the_same_thing(fact, pred, claim):
                newer = " ".join(pred.split())
                newer_said = said
            continue
        if newer is not None and newer != " ".join(pred.split()):
            return ("You've told me your " + who + " is " + newer + ", and before that "
                    + " ".join(pred.split()) + ". Which is right?")
        denial = bool(fact.group("not")) != taken_back
        if by_pronoun:
            # The line said "she isnt", so the answer names her: "No - your mum isn't coeliac."
            said_back = _names_in_capitals(_plain_contractions(
                "your " + who + " " + (fact.group("not") or fact.group("verb") or "")
                + " " + pred).strip())
        elif taken_back:
            # The take-back was a line of its own ("sorry she isnt"): the fact is the one above it.
            said_back = _the_denial(who, _the_verb(fact), pred)
        else:
            said_back = _names_in_capitals(_plain_contractions(
                _your_own_clause(said).strip(" .,!")))
        if not said_back:
            continue
        opening = "No — " if denial != _claim_is_a_denial(claim) else "Yes — "
        return opening + said_back[0].lower() + said_back[1:] + "."
    # The same fact, said with another value: "is my mum 72" against a line that says 71. The
    # claim is not on record, so there is nothing to say yes to, and the search hedge the line
    # used to fall to tells them nothing they did not already know. What the chat has is the
    # answer: the fact as they gave it, with no yes and no no in front of it.
    #
    # Only a value that can be compared is said back: a number, a name, a thing with an article.
    # "is my mum ok" has the same shape as "my mum is coeliac" once both are cut to "a thing is
    # said of her", and answering health with a diet would be worse than the hedge.
    if newer and newer_said and _the_shape("is", newer)[1] != "said":
        said_back = _names_in_capitals(_plain_contractions(
            _your_own_clause(newer_said).strip(" .,!")))
        if said_back:
            return said_back[0].upper() + said_back[1:] + "."
    return None


# A claim about someone of theirs is said back with the possessive turned: the bot has no mum
# of its own, and "Yes — my mum is 71." reads as the bot confusing the two of them. Only the
# possessive that opens the clause is turned, because a clause whose own subject is "i" is
# their sentence and not the bot's ("i was quitting my job").
A_CLAUSE_OF_MINE = re.compile(r"^(my|our)\b", re.I)


def _your_own_clause(said):
    """Their line about their own person, said from the bot's side: "your mum is 71"."""
    line = CORRECTING.sub("", str(said or "").strip())
    found = A_CLAUSE_OF_MINE.match(line)
    if not found:
        return line
    return YOURS.get(found.group(1).lower(), "your") + line[found.end():]


# A contraction said as the words: "my mum isnt coeliac" answers "is my mum coeliac" with the
# same apostrophe a person writes, because "your mum isnt coeliac" is the bot mis-typing.
CONTRACTIONS = {("isnt",): "isn't", ("wasnt",): "wasn't", ("doesnt",): "doesn't",
                ("didnt",): "didn't", ("hasnt",): "hasn't", ("arent",): "aren't",
                ("dont",): "don't", ("cant",): "can't", ("wont",): "won't",
                ("is", "n't"): "isn't"}


def _plain_contractions(said):
    """The line with the words a person writes as one word put back together."""
    for words, joined in CONTRACTIONS.items():
        said = re.sub(r"\b" + r"\s+".join(words) + r"\b", joined, said, flags=re.I)
    return said


# A name the chat gave keeps its capital when the line is said back: "my sister is called emma"
# is answered "Yes — your sister is called Emma.", because a name is written with one, and the
# lower case reads as the bot not knowing it was a name at all.
CALLED_NAME = re.compile(r"\b(?:called|named)\s+([a-z][a-z'\-]*)")


def _names_in_capitals(said):
    return CALLED_NAME.sub(lambda found: "called " + found.group(1)[:1].upper()
                           + found.group(1)[1:], said)


# "is my mum not coeliac" is the denial of the claim, so it agrees with a line that denies it.
A_DENIAL = re.compile(r"^\W*(?:not\b|n't\b)", re.I)


def _claim_is_a_denial(claim):
    return bool(A_DENIAL.match(str(claim or "")))


def _their_lines(memory, who):
    """Every line of theirs about that person, oldest first, and the ones said of her by pronoun.

    "my mum is coeliac" then "sorry she isnt" is two lines about the mum, and the second one does
    not say her name: the pronoun points at the person the chat last named, which is what makes
    it the newest word on her fact.
    """
    lines = []
    for turn in memory.get("turns") or []:
        said = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(said, str):
            continue
        if re.search(r"\b" + re.escape(who) + r"s?\b", said.lower()):
            lines.append(_trim(said, limit=80))
        elif lines and _a_pronoun_for(who).search(said):
            lines.append(_trim(said, limit=80))
    kept = user(memory).get("person")
    if isinstance(kept, dict) and isinstance(kept.get("said"), str):
        lines.append(_trim(kept["said"], limit=80))
    return lines


def _about_a_person(memory, what):
    """What the store holds about a relation of theirs, or None when the ask names no one."""
    words = [word.strip(".,!?") for word in what.split()]
    for word in words:
        who = word.lower().rstrip("s")
        if who not in extract.RELATIONS:
            continue
        for entry in others(memory):
            if str(entry.get("who") or "").lower().rstrip("s") != who:
                continue
            fact = _their_fact(who, entry)
            if fact:
                return fact
        # The store holds nothing filed against them, but they did mention them: their own words
        # still answer the question, and that beats denying it.
        quoted = _line_about(memory, who, whole_words=True)
        if quoted:
            return _quote(quoted, memory)
        return _no_note("your " + who, memory)
    return None


def _their_fact(who, entry):
    """One fact about someone else, said with the relation in it."""
    if entry.get("allergies"):
        allergies = entry["allergies"]
        if not isinstance(allergies, (list, tuple)):
            allergies = [allergies]
        return "You said your " + who + " is allergic to " + ", ".join(
            str(item) for item in allergies) + "."
    if entry.get("diet"):
        return "You said your " + who + " is " + str(entry["diet"]) + "."
    if entry.get("no_meat"):
        return "You said your " + who + " doesn't eat meat."
    if entry.get("name"):
        # A name is written the way a name is written: "my son is called tom" is said back as
        # "Your son is called Tom.", not with the spelling as typed.
        name = " ".join(word[:1].upper() + word[1:] for word in str(entry["name"]).split())
        return "Your " + who + " is called " + name + "."
    if entry.get("condition"):
        return "You said your " + who + " has " + str(entry["condition"]) + "."
    return ""


def _about_a_pet(memory, what, known, facts=None):
    """A pet they ask about by its kind: "have I told you about the dog?"."""
    if NOT_MINE.search(what + " "):
        return None
    kind = ANIMAL.search(what)
    family = (facts or {}).get("family") or (lambda word: word)
    if kind:
        name = family(kind.group(0).lower().rstrip("s"))
    else:
        # A breed is the animal it is: "have I told you about the greyhound" asks about the dog
        # the store holds, and read as a kind of its own it answered "nothing yet" about a dog
        # they had just described.
        breed = breed_words.BREED_RE.search(what)
        name = breed_words.BREED_KIND.get(
            breed_words.the_breed_named(breed.group(0)), "") if breed else ""
        if not name:
            return None
    pets = [pet for pet in (known.get("pets") or []) if isinstance(pet, dict)]
    if not pets:
        return None
    if name in ("pet", "animal"):
        # "have i told you about my pets" asks about all of them. Nothing is filed under the word
        # "pet", so the kind-by-kind reader had no cat to find and denied the two cats they had
        # just given.
        return _the_pets(memory, pets, facts)
    mine = [pet for pet in pets
            if family(str(pet.get("animal") or "").lower().rstrip("s")) == name]
    if not mine:
        return _no_note("a " + name, memory)
    said = ((facts or {}).get("pets") or (lambda memory, animal: ""))(memory, name)
    if said and any(pet.get("name") for pet in mine):
        return said
    # The count sentence is the same one the fallback says, and the fallback keeps their own word
    # for the animal: "i got a kitten" is "You've got a kitten.", not "You've got a cat."
    pet = mine[-1]
    animal = str(pet.get("animal") or name)
    if pet.get("coming"):
        # A puppy on its way is not one they have yet: "You've got a puppy" about one still with
        # its mother is the store putting an animal in the house that is not there.
        return "You're getting " + _many(pet) + "."
    return "You've got " + _many(pet) + "."


def _the_pets(memory, pets, facts=None):
    """All the pets the store holds, in the store's own sentence when they are one kind."""
    here = [pet for pet in pets if not pet.get("coming")]
    coming = [pet for pet in pets if pet.get("coming")]
    said = _the_pets_here(memory, here, facts)
    owed = _the_pets_here(memory, coming, facts)
    if owed:
        owed = owed.replace("You've got ", "You're getting ", 1)
    parts = [one for one in (said, owed) if one]
    return " ".join(parts) or None


def _the_pets_here(memory, pets, facts=None):
    family = (facts or {}).get("family") or (lambda word: word)
    kinds = []
    for pet in pets:
        animal = family(str(pet.get("animal") or "").lower().rstrip("s"))
        if animal and animal not in kinds:
            kinds.append(animal)
    if len(kinds) == 1:
        said = ((facts or {}).get("pets") or (lambda memory, animal: ""))(memory, kinds[0])
        if said:
            return said
    said = [_many([pet for pet in pets if str(pet.get("animal") or "").lower().rstrip("s")
                   in (kind, kind + "s")][-1]) for kind in kinds]
    said = [one for one in said if one]
    if not said:
        return None
    if len(said) == 1:
        return "You've got " + said[0] + "."
    return "You've got " + ", ".join(said[:-1]) + " and " + said[-1] + "."


COUNT_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
               9: "nine", 10: "ten"}


def _a(word):
    return ("an " if str(word)[:1].lower() in "aeiou" else "a ") + str(word)


def _many(pet):
    """A pet said with its name or its count: "a cat called Milo", "two cats", "a dog"."""
    # The breed is the word the person used for one animal, so it is the word for that animal
    # and for the one beside it: "a tabby", "a greyhound called Rex". A group is the kind of
    # animal, though: "we have two dogs, a lab and a terrier" is two dogs, and the breed of one
    # of them is not the name of the pair.
    kind = str(pet.get("animal") or "pet")
    # A breed named beside a group is the breed of one of them, so the group is said by its kind:
    # "we have two dogs, a lab and a terrier" is two dogs, not two terriers. A breed said as the
    # group itself ("two greyhounds") is not marked, so it stays the word for the pair.
    animal = kind if pet.get("breed_of_one") else str(pet.get("breed") or kind)
    many = kind if kind.endswith(("fish", "sheep", "deer")) else kind + "s"
    if pet.get("name"):
        name = str(pet["name"])
        return _a(animal) + " called " + name[:1].upper() + name[1:]
    try:
        count = int(pet.get("count") or 1)
    except (TypeError, ValueError):
        count = 1
    if count > 1:
        return COUNT_WORDS.get(count, str(count)) + " " + many
    return _a(animal)


# Words that point at what was already said without naming it: "i told you already", "i mentioned
# it before". A claim made of one of these names no thing, so what it points at is the chat itself.
ONLY_A_POINTING_TIME = re.compile(r"^\W*(?:already|before|earlier|yesterday|that|this|it|them|"
                                  r"just\s+now|ages\s+ago|a\s+minute\s+ago|"
                                  r"the\s+other\s+day|last\s+(?:time|night|week))\W*$", re.I)


POINTING_TAIL = re.compile(r"\s+(?:already|before|earlier|just\s+now|ages\s+ago|"
                            r"a\s+minute\s+ago|the\s+other\s+day|last\s+time)\W*$", re.I)


# "i said that already" carries no "you", so it is outside the shapes A_CLAIM_WITHOUT_YOU reads
# ("i said hello to her" is news). Said with a pointing word and a time, it is the same claim as
# "i told you already".
POINTING_SAID = re.compile(
    r"^\W*(?:and\s+|also\s+|so\s+|but\s+|ok(?:ay)?\s+|look\s+|listen\s+|hey\s+)?"
    r"(?:i|we)\s+(?:said|told\s+you|told\s+u)\s+(?:that|it|this|them)\s+"
    r"(?:already|before|earlier|just\s+now|ages\s+ago|a\s+minute\s+ago|the\s+other\s+day|"
    r"last\s+(?:time|week|night))\W*$", re.I)


def _the_newest_stated_line(memory, skip="", a_question_ok=False):
    """The last line of theirs that states something, or "" when the chat is all questions.

    `a_question_ok` is the last resort for a chat that holds nothing but an ask: it is still what
    they said, and it is said as the question it was rather than denied.
    """
    asked = _flat(skip)
    for turn in reversed(memory.get("turns") or []):
        said = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(said, str) or not said.strip():
            continue
        if _flat(said) == asked:
            continue
        if not a_question_ok and (said.rstrip().endswith("?") or ASKS.match(said)):
            continue
        if _a_claim_about_the_chat(said):
            continue
        return " ".join(said.split())
    return ""


def _a_claim_that_points(text, memory):
    """The proof for a claim that names the chat rather than a thing ("i said that already")."""
    line = str(text or "")
    if POINTING_SAID.match(line):
        return _the_proof_they_asked_for("", text, memory)
    match = CLAIMED_ABOUT.match(line) or A_CLAIM_WITHOUT_YOU.match(line)
    if not match:
        return None
    said = A_TRAILING_TIME.sub("", " ".join(match.group("what").split())).strip(" .,!")
    if said and said.lower() not in POINTING:
        return None
    return _the_proof_they_asked_for(said, text, memory)


def _the_proof_they_asked_for(named, text, memory):
    """The line they are asking for, when the claim points at the chat instead of naming a thing.

    "i told you already", "i mentioned it before" name no thing at all: they point at the thread
    and ask whether it was kept. Read as the thing themselves, the store denied a note of the word
    "already" ("I haven't kept a note of already - tell me and I'll remember it.") while it held
    the boiler the whole time. What was told is the newest line of theirs about the thing the chat
    is on, said back as the proof they are asking for.
    """
    said = " ".join(str(named or "").split())
    if said and not ONLY_A_POINTING_TIME.match(POINTING_TAIL.sub("", said).strip()):
        return None
    told_about = _the_thing_the_chat_is_on(memory)
    quoted = _line_about(memory, told_about, skip=text) if told_about else ""
    if not quoted:
        # A chat with no subject to name yet ("im 34") still holds the line they mean: the newest
        # one that states something, since a question or another claim is not a thing told.
        quoted = _the_newest_stated_line(memory, skip=text)
    if not quoted:
        asked_line = _the_newest_stated_line(memory, skip=text, a_question_ok=True)
        if not asked_line:
            return None
        return pick(['All I have from you so far is "' + asked_line + '" — tell me the rest and '
                     "I'll keep it.",
                     'What I have is "' + asked_line + '". Say it in your own words and it is in.'],
                    memory)
    return pick(['You did — "' + quoted + '" is what I kept.',
                 '"' + quoted + '" — that one I have.',
                 'I have it: "' + quoted + '".'], memory)


def _line_about(memory, what, whole_words=False, skip=""):
    """The last line of theirs about the thing, trimmed, or "" when they never said one.

    `whole_words` matches the thing as a word ("son" is not in "song"), which a relation needs:
    the word is short and sits inside other words all the time.
    """
    words = [word for word in re.split(r"[\s,]+", what.lower()) if len(word) > 2]
    if not words:
        return ""
    asked = _flat(skip)
    for turn in reversed(memory.get("turns") or []):
        said = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(said, str) or not said.strip():
            continue
        if _flat(said) == asked:
            # The ask is not evidence that they told the bot: "did i mention my sister" quoting
            # itself back answered a question with the question.
            continue
        if said.rstrip().endswith("?") or ASKS.match(said):
            continue  # the question itself neither names the thing nor answers for it
        if _a_claim_about_the_chat(said) and not _a_clause_is_named(said):
            # "i told you about the damp" is about the telling, not about the damp, so it is not
            # what they said about it: quoting it back answered "what did i say about the damp"
            # with the complaint that they had said it. A claim that carries a clause ("i told you
            # my dog died") does say something, and is kept as what they said.
            continue
        if recall.ask(said) == "me":
            # "anything you've learned about me" is the same question in other words, and it was
            # quoted back as the thing they told the bot by the next "what did i tell you".
            continue
        if TOLD_ABOUT.match(said) or CLAIMS_TOLD.search(said) or REMEMBERED.match(said):
            # "i told you about my sister" is a claim about the chat, not the fact about her:
            # quoting it back answers the question with the person's own assertion.
            continue
        low = said.lower()
        if whole_words:
            if any(re.search(r"\b" + re.escape(word) + r"s?\b", low) for word in words):
                return _trim(said)
        elif any(word in low for word in words):
            return _trim(said)
    return ""


# A line about going somewhere, which is what "the trip" means when no plan was kept: a trip
# they took ("i went to lisbon in may") is as much a trip as one they are planning.
A_TRIP = re.compile(r"\b(?:went|going|booked|flying|flight|holiday|trip|visiting|staying|"
                    r"travel(?:ling|ing)?)\b", re.I)


def _a_trip_line(memory):
    """The last line of theirs about going somewhere, trimmed, or ""."""
    for turn in reversed(memory.get("turns") or []):
        said = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(said, str) or not said.strip() or said.rstrip().endswith("?"):
            continue
        if A_TRIP.search(said):
            return _trim(said)
    return ""


# "i told you about my sister", "i did mention it": the person saying they said it, which is the
# claim and not the thing. It neither names the thing nor answers for it.
CLAIMS_TOLD = re.compile(r"\b(?:told|mentioned|said|talked)\s+(?:you|about|it)\b", re.I)


def _flat(line):
    return " ".join(str(line or "").lower().split()).strip(" .,!")


def _the_denial(who, verb, pred):
    """"your mum isn't coeliac": the fact said the other way round, with the relation named."""
    word = {"is": "isn't", "was": "wasn't", "are": "aren't", "does": "doesn't",
            "did": "didn't", "has": "hasn't"}.get(verb, "isn't")
    return "your " + who + " " + word + " " + " ".join(str(pred or "").split())


def _a_pronoun_for(who):
    """The pronouns that can point at that person: "she" for a mum, and "they" for anybody."""
    word = str(who or "").strip().lower()
    fits = ["they"]
    if word in extract.SHE:
        fits.append("she")
    if word in extract.HE:
        fits.append("he")
    return re.compile(r"^\W*(?:" + CORRECTION_WORDS + r"\b[,.!;:]?\s*){0,2}(?:"
                      + "|".join(fits) + r")(?:'s|s)?\s+\S", re.I)


def _trim(line, limit=100):
    """Their line as a quote: one line, short enough to read inside a reply."""
    text = " ".join(str(line or "").split()).strip(" .,!")
    if len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0]
        text = cut + "\u2026"
    return text


# A reader with nothing to say still answers, and its answer is a denial of its own: the fact it
# is asked about is only used here when it really says something, so these are the shapes to skip.
NOTHING_SAID = re.compile(r"^\W*(?:you\s+(?:haven't|have not|don't|do not|'ve not|ve not|didn't)|"
                          r"nothing|no\b|not\b)", re.I)
# The kinds whose stored value is a fact about the person, so a word in it can be what they asked
# about. `pets` is left out: its reader takes the kind of animal, and that ask has its own path.
THE_KINDS_KEPT = ("allergies", "budget", "diet", "dislikes", "tastes", "plan", "places",
                  "kids")


def _stem(word):
    """A word without its endings, so "savings", "saving" and "save" are one thing to match on.

    The endings come off one after another, because English stacks them: "savings" is "save" with
    "ing" and then "s" on it, and one pass left "saving" beside "save".
    """
    word = re.sub(r"[^a-z]", "", str(word or "").lower())
    for _ in range(3):
        for ending in ("ings", "ing", "ies", "es", "ed", "s", "e", "y"):
            if len(word) > len(ending) + 2 and word.endswith(ending):
                word = word[:-len(ending)]
                break
        else:
            break
    return word


def _kept_words(value, into=None):
    """Every word of a kept fact, so a plan or a list of allergies can be searched for one."""
    into = set() if into is None else into
    if isinstance(value, str):
        into.update(word for word in re.split(r"[^a-z]+", value.lower()) if word)
    elif isinstance(value, dict):
        for item in value.values():
            _kept_words(item, into)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _kept_words(item, into)
    return into


def _the_fact_that_names(memory, what, known, facts):
    """The fact the ask names by one of its words, said the store's way, or None."""
    if not facts:
        return None
    stems = {_stem(word) for word in re.split(r"[^a-zA-Z]+", str(what or "")) if len(word) > 2}
    stems.discard("")
    if not stems:
        return None
    for key in THE_KINDS_KEPT:
        reader = facts.get(key)
        value = known.get(key)
        if not reader or not value:
            continue
        kept = {_stem(word) for word in _kept_words(value)}
        if not (stems & kept):
            continue
        said = reader(memory)
        if said and not NOTHING_SAID.match(said):
            return said
    return None


def _the_kind_of(word):
    """"plans" and "plan" are the same kind of fact, and so are "jobs" and "job"."""
    word = str(word or "").strip(".,!?").lower()
    for candidate in (word, word[:-1], word[:-2] if word.endswith("es") else word):
        key = A_KIND.get(candidate)
        if key:
            return key
    return ""


def _names_only_a_kind(what):
    """True when every word of the thing asked about names a kind of fact ("my name", "the money")."""
    words = [word.strip(".,!?") for word in re.split(r"[\s,]+", str(what or "").lower()) if word]
    return bool(words) and all(_the_kind_of(word) for word in words)


def _the_fact_of_that_kind(memory, what, known, facts=None):
    """The fact a kind-naming ask asks about: "have i told you about the trip" -> the plan.

    The sentence is the store's own ("You're Sam." for the name, "You told me you're allergic to
    peanuts." for the allergy), handed in as `facts`: a kind of ask should not be a second set of
    sentences for the same fact, or the two answers drift apart and one of them reads like a form.
    """
    for word in re.split(r"[\s,]+", what.lower()):
        key = _the_kind_of(word)
        if not key:
            continue
        value = known.get(key)
        if not value:
            # "did i mention the trip" is answered by a trip they took as well as one they are
            # planning: the plan is the store's own shape of it, and when there is no plan the
            # place they named is the trip, quoted as they said it.
            if key == "plan":
                for place in reversed([p for p in (known.get("places") or [])
                                       if isinstance(p, str)]):
                    said = _line_about(memory, place)
                    if said:
                        return _quote(said, memory)
                said = _a_trip_line(memory)
                if said:
                    return _quote(said, memory)
            return ""
        said = ((facts or {}).get(key) or (lambda memory: ""))(memory)
        if said:
            return said
        if key == "plan":
            return "You said: \"" + _trim(value) + "\""
        values = value if isinstance(value, list) else [value]
        return "You told me: " + ", ".join(str(v) for v in values) + "."
    return ""
