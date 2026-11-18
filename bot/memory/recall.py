"""Reading the ask in a question about what the user told you.

The memory store answered a fixed list of phrasings ("what's my name", "what did I say my
budget was"), so the same ask in other words fell through to the composer's "I don't know":
"what was my name", "do you remember my budget?", "where do I live", "you know my name?".

A recall question has one shape whatever its words: it asks about something of the user's and
names nothing else. So ask() strips the asking frame - the question word, the verb of saying or
knowing, the politeness and the lead-in - and then reads what is left:

* what remains is the user themselves ("my", "I") and one thing they told you ("name", "budget",
  "live") -> that is the ask, and the store answers it.
* anything else is left over ("what should I cook with my dog?") -> the line is a real request
  and this passes.

It only reads; the store owns the answers (bot/modules/memory_store.py) and the facts
(bot/memory/facts.py). Keys are the store's own fact keys.
"""
import re

from ..understanding import breeds as breed_words
from .topics import words

# The meanest part of a recall question: which, how, was, remind, remember, say, again, please.
SCAFFOLD = frozenset("""
what whats which who whom whose how when whens where why whether that this these those it its
was were is are am be been being do does did done doing have has had having
you u ya i im ive id ill me my mine our ours we us your yours dont doesnt didnt isnt wasnt
arent wont cant couldnt wouldnt
again also still yet now then just only even ever before already first last next other
remember recall forget forgot know knew knews say said saying says tell told telling remind
else more again
please pls can could would will shall may might should must about of for to in at on
with by any anything something everything one ones thing things much many more most
the a an and or but so or right ok okay fine really actually honestly anyway well oh ah hmm
call called calls calling
you u ur your yours youve youre youd youll i me my mine we us our ours ya chat chats
conversation talk
up
got get gets getting gotten
give gimme hand
far
myself yourself yourselves ourselves themselves itself himself herself
""".split())
# The reflexive counts as the asking frame: it is the person saying "me" again ("what did i tell
# you about myself"). Without it the whole picture was refused as though "myself" were a fact the
# store might keep, and the person was told they had said nothing about themselves right after
# telling the bot their name and their allergy.
# "what pets have i got", "what budget have i got", "what have i got on": the verb of having is
# already scaffold, and "got" is the same verb in the words people actually type in Britain. A
# subject beside it is still the ask; a line that names something else ("what have i got for a
# headache") is refused by the word that names it, which is the rule the content list is for.

# The verb of remembering in whatever form people type it: "what have you remembered about
# me", "what else do you know", "what you knew", "what have you learned about me". Listed
# forms alone miss half of them ("remembered", "knows", "knowing", "forgotten", "tells"),
# and a recall question is the one kind of line where the remembering word carries nothing.
REMEMBERING = re.compile(r"^(?:remind|rememb|forget|forgot|know|knew|kno|say|said|say|tell|"
                         r"told|recall|summar|recap|remind|mention|"
                         # "what have you learned about me" is the same ask as "what do you
                         # know about me": the bot learning a fact is the person telling it.
                         r"learn|learnt|learned|studied|picked)", re.I)

# The verbs that ask for what the bot holds on someone, as opposed to what they said last.
KNOWING = re.compile(r"\b(?:know|knew|knows|knowing|remember|remembers|remembered|recall|"
                     r"recalls|summar(?:y|ise|ize)|recap|learn|learns|learned|learnt|"
                     r"learning|studied|pick|picks|picked|picking)\b", re.I)

# A lead-in in front of the real question: "thanks! what was my name".
LEAD = re.compile(
    r"^\s*(?:(?:ok|okay|k|kk|right|so|and|but|oh|ah|well|thanks|thank you|thx|ty|cheers|ta|hi|"
    r"hello|hey|morning|yes|yeah|yep|no|nah|great|cool|nice|perfect|brilliant|lovely|good|sure|"
    r"hmm|sorry|got it|i see|fair enough|makes sense)[\s,.!?;:—-]+)+", re.I)

# A line that says which topic it is coming back to before it asks the question: "back to the
# job, what was my new job again", "about the boiler, what did i say", "anyway what was my
# name". The clause names the subject a second time and is not the question, and read as part
# of it the first word was "back" or "about", which asks nothing, so the whole line was refused
# and the person who came back to their own job was told the store knew nothing about it. Only
# the front of the line is taken off, up to the punctuation that closes the clause, so the
# question itself is read exactly as it would have been said on its own.
RETURNING = re.compile(
    r"^\s*(?:(?:and\s+)?(?:back|going\s+back|coming\s+back|returning)\s+to\s+"
    r"(?:the|my|our|that|this|your)\s+[a-z'’-]+|(?:about|on|re|regarding|for)\s+"
    r"(?:the|my|our|that|this|your)\s+[a-z'’-]+|the\s+[a-z'’-]+|(?:anyway|also|oh\s+and|and\s+also|"
    r"separate\s+thing)\b)[\s,.!?;:—-]*", re.I)

# What the user can ask about, most specific first: "what's my dog called" is about the dog,
# not about a name, so the pet wins over the word "called".
SUBJECTS = (
    # "what do i have to avoid" is the allergy ask in the words people use for it: the thing
    # to avoid is the thing they told you they cannot have, and "avoid" names nothing else the
    # store keeps. It is a verb rather than the fact's name, which is why plain advice still
    # passes ("what should i avoid in the sun" has no recall word in it and is refused above).
    ("allergy", ("allergic", "allergy", "allergies", "intolerant", "intolerance", "avoid",
                 "avoided", "avoiding")),
    # "how much have i spent", "what did i spend on food": the past tense is the same ask about
    # the same fact, and without it the line was read as a food question and answered with a tip
    # about shopping with a list.
    ("budget", ("budget", "spend", "spending", "spent", "afford", "cost")),
    # "what diet am i on", "do you remember my diet": how they eat is kept as a fact like the
    # rest, so the same ask in these words is answered from it instead of with a search hedge.
    ("diet", ("diet", "diets", "dieting", "vegan", "vegetarian", "vegetarian", "pescatarian",
              "keto", "paleo")),
    ("pet", ("pet", "pets", "dog", "dogs", "cat", "cats", "puppy", "kitten", "rabbit", "hamster",
             "budgie", "parrot", "horse")),
    # A birthday and a weight are facts like the others: people ask them back the same way.
    ("birthday", ("birthday", "birthdays", "bday", "dob", "birthdate")),
    ("weight", ("weigh", "weighs", "weight", "weights", "kilos", "kilo", "stone", "pounds",
                "heavy")),
    # How tall they are is the same kind of fact, and "how tall am i" was answered "I'm not sure
    # about that one" about a height the person had given a line earlier.
    ("height", ("height", "tall", "taller", "tallest", "centimetres", "centimetres", "cm")),
    ("name", ("name", "named", "nickname")),
    # Only the home words: "which city did I say first?" asks what they mentioned, not where
    # they live, and the store has its own line for that.
    ("city", ("live", "lives", "living", "lived", "home", "based", "address", "resident")),
    ("job", ("job", "jobs", "work", "works", "worked", "role", "career", "profession",
             "employer", "employed")),
)

# "What can't I eat", "what don't I eat", "what should I avoid": the ask names no subject at
# all, so the shape carries it - a word that rules food out next to the food word itself. Only
# when every content word is part of that ask: "what should I avoid when painting" is advice
# about paint, and it keeps its own answer.
LIMIT_WORDS = frozenset("""
eat eats eating eaten have has having drink drinks drinking food foods meal meals
breakfast lunch dinner tea supper snack snacks pudding dessert anything else starchy sugary
avoid avoiding allowed ok okay safe should shouldnt shouldn not no though tho then
cant cannot dont doesnt didn could couldnt mustnt shouldn would wouldnt anymore
""".split())
LIMIT = re.compile(
    r"\b(?:can't|cant|can not|cannot|don't|dont|do not|shouldn't|shouldnt|mustn't|mustnt|never|"
    r"not|avoid|avoiding|no)\b[^?.!]{0,24}?"
    r"\b(?:eat|eats|eating|have|has|having|drink|drinks|drinking|food|foods)\b"
    r"|\b(?:eat|eats|eating|drink|drinks|drinking|food|foods)\b[^?.!]{0,24}?"
    r"\b(?:can't|cant|cannot|not|shouldn't|shouldnt|avoid|avoiding)\b"
    r"|\bwhat (?:should|shall|must|do) i (?:avoid|stay away from|keep away from)\b", re.I)

# Another person's fact is not the user's: "what's my son allergic to" belongs to the store's
# work on whose fact it is, so this reader passes those lines on untouched.
PEOPLE = frozenset("""
daughter daughters son sons kid kids child children baby toddler boy girl family wife husband
partner mum mom mother dad father parent parents sister brother flatmate housemate friend
friends neighbour colleague boss
""".split())

# "what was my new job again", "what was my old name": a word saying which of the things they
# mentioned sits between the asking frame and the thing itself, and it names nothing to recall.
# Read as content it made every such ask fail (`what was my new job again` after "i got a new job
# in a bakery" told the person the store knew nothing about it). Only a word directly in front of
# a subject is dropped, so "what was my new house" is still refused.
RECALL_MODIFIERS = frozenset(("new", "old", "older", "current", "previous", "former"))
# "old" is also an age, and "how old is my dog" asks for that: the modifier is not read there.
HOW_OLD = re.compile(r"\bhow old\b", re.I)

# The whole picture is only asked for in these shapes: "what should I say?" is a request for
# advice about the conversation, not a question about what you know of the person.
ME = re.compile(
    r"\babout me\b|\bof me\b|\bwhat have i (?:told|said|mentioned)\b|\bhave i (?:told|mentioned)\b|"
    r"\bdid i (?:tell|say|mention)\b|\bsummar(?:y|ise|ize)\b|\brecap\b|\brun me through\b"
    # The same ask about the thing the chat is on rather than the person: seven turns into a
    # wedding chat, "what do you remember about it" is the wedding, and the wedding is here. Read
    # as no recall at all, it was answered with the card about nothing carrying over to a new
    # chat - one turn after the bot was told the wedding starts at two, not one. The bare
    # pronoun only, and the line has to end on it: "what do you remember about that recipe"
    # names a thing of the world.
    r"|\bwhat do you remember about (?:it|that|this)\s*\??$", re.I)

# "How do I know when it's done" asks for a test of the thing in front of them (a steak, a
# cake, a paint coat), not for a reminder of what they said. Whatever is left after the scaffold
# is only the person, so without this the question lands on the whole picture.
HOW_KNOW = re.compile(
    r"\bhow (?:do|does|did|would|will|can|could|should|might) (?:i|you|we) (?:\w+ly )?"
    r"(?:know|tell)\b", re.I)

# "Why do we get allergies", "why do we have pets": the store can say what a person told it and
# never why the world is the way it is. The words around the subject are all scaffold ("why do we
# get"), so the only content left was the subject itself, and the whole line was read as an ask to
# give the fact back ("You haven't mentioned an allergy to me.") where the question wanted the
# cause. A why-ask is always about the world, so it is never a read of the store.
WHY = re.compile(r"\bwhy\b", re.I)

# "what should I call the dog" and "where should I live" are asking for advice, not asking back
# what was said: only a word about the past or about repeating makes them a recall.
ADVICE = re.compile(r"\bshould\b|\bshall\b", re.I)
# A method for keeping a date is advice, not the date they told me. "How do i remember birthdays"
# was read as a recall of their own birthday and answered "You haven't told me your birthday yet",
# which is the store answering a question nobody asked; the habit (one list, written down) is the
# answer, and the science row has it. The shapes are the ones that ask for the habit - how do i
# remember, any tips, the best way, is there a way - and "do you remember my birthday" and "remind
# me about my birthday" are reads of the store and keep it.
KEEPING_TRACK = re.compile(
    r"\bhow\s+(?:do|can|could|should|would|to)\s+(?:i|you|we|u)?\s*"
    r"(?:remember|keep\s+track|track|stop\s+forgetting|never\s+forget)\b"
    r"|\b(?:tips?|advice|ways?|tricks?|trick)\b[^.?!]{0,30}?\b(?:remember|remembering|"
    r"keep\s+track)\b"
    r"|\bbest\s+way\s+to\s+remember\b|\bis\s+there\s+a\s+way\s+to\s+remember\b"
    r"|\bhow\s+to\s+remember\b", re.I)
# "what do i say about my last job" asks for advice for the interview, not for a fact the store
# keeps: the present tense asks what to say, where a recall asks what was said ("what did i say
# about my job"). Read as a recall it answered a person preparing for an interview with a
# quotation of their own first line: "You said: "ive got a job interview on friday"".
SAY_NOW = re.compile(
    r"\bwhat (?:do|can|could|would|will) (?:i|we) (?:say|tell)\b", re.I)
# "What can I do at home?" is a request for advice, not for a fact they told you: the frame
# "can I <action>" asks what to do, where a recall asks what was said. The action verb is what
# makes it advice, so "where can I live" and "what can you remember about my home" are still
# reads of the store. Without this the line was answered as a place ("You haven't mentioned a
# place yet.") because "home" is a city word.
_ACTION = (r"do|use|try|make|clean|cook|get|put|keep|fix|buy|say|start|stop|avoid|wear|take|"
           r"give|move|store|wash|paint|grow|sort|plan|change|improve|prevent|protect|choose|"
           r"pick|find|save|spend|eat|drink|add|remove|repair|replace|help")
ACTION_ASK = re.compile(
    r"\b(?:what|how|anything|something|where|is there)\b[^?]{0,60}?"
    r"\b(?:i|we)\s+(?:can|could|should|shall|would|will)\s+(?:" + _ACTION + r")\b"
    r"|\b(?:what|how|anything|something)\b[^?]{0,60}?"
    r"\b(?:can|could|should|shall|would|will)\s+(?:i|we)\s+(?:" + _ACTION + r")\b", re.I)
RECALLING = re.compile(r"\b(?:again|remind|reminds|remember|recall|was|were|did|said|told|knew)\b", re.I)
# "will a dog get on with my cat" asks what will happen to the cat, not what the store was told
# about it: read as a recall, it answered "You haven't told me about a pet yet" over a cat the
# line had just named, and the card that knows about a dog and a cat never got the line. The
# subject is what tells the two apart - a thing of theirs ("a dog", "my cat", "the boiler")
# rather than the person ("do i have a cat"), with no word about the past to make it a read.
WORLD_SUBJECT = re.compile(
    r"^(?:will|would|can|could|may|might|should|shall|is|are|does|do)\s+"
    r"(?:a|an|the|my|our|your|this|that|these|those|any|one|two|both)\s+\S+", re.I)
# A modal in front of getting or keeping something is a question about a decision, not a question
# about a fact they gave: "can we still get a dog" is not asking what the store holds, and "You
# haven't told me about a pet yet" answers it with a denial of a record nobody claimed. The words
# after the modal are what tell the two apart - "can i still have dairy" is a limit the person is
# asking about, and the entry that knows the limit answers that better.
DECIDING = re.compile(
    r"\b(?:can|could|should|shall|may|might|would)\s+(?:we|i|you)\s+(?:still\s+)?"
    r"(?:get|have|keep|adopt|buy|rescue|own|afford|take on)\b"
    # what is being got or afforded has to be named: "can i afford it" and "what can i afford"
    # lean back on the record itself, and those are questions the store answers well
    r"(?=\s+(?!(?:it|that|this|one|ones|them|those|these|more|anything)\b)\S)"
    r"|\bare\s+(?:we|you|i)\s+(?:allowed|able)\s+to\b"
    r"|\bis it (?:ok|okay|fine|wise|allowed)\s+to\b", re.I)
# The things a person decides rather than tells: an animal, and what they can spend. The limit
# they cannot eat is not one - "can i still have dairy" is a question with a real answer.
DECIDED_ABOUT = ("pet", "budget")
# What a recall is for: the person's own attributes rather than the objects and animals around
# them. "is my budget ok" is a question about the record and reads as a recall; "is my cat too
# fat" is about the cat, and the store holds no reading of a cat to hand back.
PERSONAL = ("name", "job", "city", "allergy", "budget", "diet", "birthday", "weight", "height")

# A recall is about the user's own facts, so it names them: "where do I live", "do you remember
# my budget". "Where do you live" and "what's your name" are questions about the bot, and the
# store has no business answering those with the person's own facts.
USER = re.compile(r"\b(?:my|mine|i|i'm|im|i've|ive|i'd|id|i'll|ill|me|we|our|ours|us)\b", re.I)

# The person as the *object* of what the bot knows: "who do you know me as", "what have you
# learned about me", "what do you know of mine". A question like "can i still learn" names them
# as the one asking, not as the one known, so there is nothing of theirs to answer it with.
KNOWN_OBJECT = re.compile(r"\b(?:me|my|mine|myself)\b", re.I)

# "What am I called", "what do you call me": the word "call" asks about a name only in that
# shape. "Who do I call?" asks for a name to ring, not for their own name, and it passes.
CALL_NAME = re.compile(
    r"\bwhat (?:am i|was i|do you|did you|would you) call(?:ed)?\b|\bcall me\b|"
    r"\bi(?:'m| am| was)\s+called\b", re.I)

# "what do you call a baby goat", "what do you call a group of crows", "what do you call a
# spade": the ask is the word the world uses for a thing, and the store keeps the names people
# gave it. Read here as a name ask it answered "I don't know it yet - you haven't said", which
# is true of a name and nonsense as an answer about a goat. An ask that names a thing with "a"
# or "an" after the verb is about the world, so the store stands down and the answers module
# says the word. A name ask points instead - "call it", "call him", "call this", "call me" -
# and "what do you call yourself" carries no article, so those stay recalls.
CALL_A_THING = re.compile(r"\bcall(?:ed)?\s+(?:a|an)\s+[a-z]", re.I)
# ...but a person asked for by what they do is the other thing again: "what do you call a person
# who fixes teeth", "what do you call a man who steals". The article is there and the relative
# clause says the ask is about a job or a word for a person, not about the animal the line happens
# to name. Handed on to the knowledge base those lines reached the bleeding-gums card and the
# identity card where the store had said plainly that it did not know; a confident wrong answer is
# worse than an honest one, so the store stands down and the honest line takes the turn.
A_PERSON_BY_WHAT_THEY_DO = re.compile(
    r"\bcall(?:ed)?\s+(?:a|an)?\s*(?:person|people|man|woman|boy|girl|child|kid|someone|"
    r"somebody|thing|one|guy|bloke|lady)\s+(?:who|that|which|whose)\b", re.I)
# A person named on its own ("what do you call a person") is the same kind of ask, and no entry
# here is about a word for a person either - but the store has its plain "I don't know it yet"
# for it, which is not wrong, so it keeps that line and only the answers module stands down.
A_PERSON = re.compile(
    r"\bcall(?:ed)?\s+(?:a|an)\s+(?:person|people|man|woman|boy|girl|child|kid|someone|"
    r"somebody|thing|one|guy|bloke|lady)\b", re.I)


def asks_for_a_word(line):
    """Whether this is the word for a thing rather than a name the chat was given.

    The article is what tells the two apart: a recall points at what was said ("call it", "call
    him", "what am i called", "what did i call my cats"), and a thing is named with "a" or "an".
    A word for a person is not a fact the store or the entries hold, so it is neither.
    """
    line = line or ""
    return bool(CALL_A_THING.search(line)) and not (
        A_PERSON.search(line) or A_PERSON_BY_WHAT_THEY_DO.search(line))


# The car, asked for in the words people use: "what do i drive", "what car have i got", "whats my
# car". The verb alone is not the ask - "how do i drive it" is a how-to and names nothing they
# told you - so the shape has to want the car itself. The store keeps the fact (facts._car) and
# says it back, and without the ask it had nothing to be asked with.
DRIVE_ASK = re.compile(
    r"\bwhat (?:do|did|am) i driv(?:e|ing)\b|\bwhich car\b|\bwhat car\b|"
    r"\bwhat (?:kind|make|model) of car\b|\bwhat(?:'s|s| is| was) my (?:car|van)\b", re.I)

# "what do i have to avoid", "what do i need to avoid", "what foods do i have to avoid": the
# modal in the middle ("have to", "need to", "got to") is part of the asking frame, and what is
# left is the thing to avoid, which is the fact they told you. It names the user, so a how-to
# about the world ("how to avoid jet lag") is not read as one.
AVOID = re.compile(r"\b(?:have|has|had|need|needs|needed|got|ought) to avoid\b", re.I)

# "How do I know when my dog is ill?", "how do I check my budget is enough?": asking how to tell
# something apart is a question about the world, not about what the user told you. Only the
# how-to shapes, so an ordinary recall ("what was my budget") is untouched.
HOW_TO_TELL = re.compile(
    r"\bhow (?:do|can|should|would|could|will|might) (?:i|we|you) "
    r"(?:know|tell|check|spot|see|notice|work out|find out|make sure)\b", re.I)
# The how-to word only decides when the rest asks how to tell something apart. "how do i know
# where i live" wraps the same words around a fact they gave and is still a recall; "how do i know
# my budget again" has no line to tell apart at all and is a recall too.
TELLS_APART = re.compile(
    r"\b(?:when|if|whether|that)\b|\b(?:is|are|am)\s+(?:\w+\s+){0,2}?"
    r"(?:enough|ok|okay|happy|sad|ill|sick|unwell|in pain|ready|too|allergic|missing|done|safe|off)\b"
    r"|\benough\b", re.I)

# "how much did i spend on food", "what did i spend on the train": the thing the money went on is
# part of the fact, not a second subject, so it does not stop the line being the money ask. Without
# this the leftover word was read as a subject of its own ("food" is no fact the store keeps) and
# the line was left to the entries, which answered it with a tip about shopping with a list.
SPENT_ON_A_THING = re.compile(r"\b(?:on|for)\s+\S.*$", re.I)
# Only money already spent takes the tail off the line: "how much did i spend on food" is the
# tally. "How much do i spend on rent" is a different question - what rent usually costs - and
# stripping "on rent" left "how much do i spend", which the store read as an ask about a budget
# nobody had given: "You haven't told me a budget." over a rent question it answers on its own.
SPENDING = re.compile(r"\b(?:spent|paid)\b|\b(?:did|have|has|had)\s+(?:i|we)\s+(?:spend|pay)\b",
                       re.I)

# "What do I do for a living?" is the job, however the word "living" sounds like where they live.
LIVING = re.compile(r"\bfor a living\b|\bdo(?:es)? for a job\b", re.I)

# The words that name the employer rather than the job the person holds, and the ask that wants
# the fact said back. The store keeps a role and a workplace; it has never been told what the
# employer may do, so "can my employer fine me" is a question about the law and was answered "I
# don't know your job - you haven't said", which answers nothing. "who is my employer" and "where
# do i work at" do want the fact, so the ask word keeps those.
EMPLOYER_WORDS = frozenset(("employer", "employers", "employed", "employment"))
WANTS_THE_FACT = re.compile(
    r"\b(?:what|which|who|whom|whose|where|when|how|why)\b|\bremind|\bremember|\bknow\b|"
    r"\btell me\b|\bsay again\b", re.I)

# The word a question opens on. "me" is not one of them, and it used to be here by accident: the
# list carried the phrase "tell me anything", which splits into three words. A line that opens on
# the British possessive "me" is a statement - "me cat is ill", "me dog is ok", "me job is fine" -
# and read as a question it went to the store, which answered "You haven't told me about a pet
# yet" over the cat the line had just named.
# A time span is the one thing a recall ask can add to its frame without naming anything to
# answer: "what did i tell you last week", "what did i say yesterday", "and what did i mention a
# minute ago". Read as content, the span was a thing to look up in the store, nothing is filed
# for it, and the ask fell through to the composer's hedge - the person asked for their own words
# and got "A quick search online will get you a solid answer". The span decides when, not what, so
# it is dropped and the ask is read as the recall it is. The reply still makes no claim about the
# span: the store says what it holds and nothing about when.
TIME_WORDS = frozenset("""
week weeks weekend weekends month months year years day days today tonight tomorrow yesterday
morning mornings afternoon afternoons evening evenings night nights midnight noon
minute minutes hour hours second seconds ago fortnight fortnightly daily weekly monthly yearly
monday tuesday wednesday thursday friday saturday sunday
january february march april may june july august september october november december
earlier lately recently sometime once
""".split())

QUESTION_START = frozenset("""
what what's whats which who whom whose how when whens where why is are was were am do does did have
has can could would should will remind remember know tell say anything
""".split())


def _key(word):
    """The fact key a content word asks about, or None."""
    # A breed is the animal it is: "what is my greyhound called" is the pet ask, and read as a
    # word about nothing it was answered out of the composer instead of out of the store.
    if breed_words.the_kind_of(word):
        return "pet"
    for key, names in SUBJECTS:
        if word in names:
            return key
        if len(word) > 4 and any(word.startswith(name[:4]) and name[:4] in ("alle", "budg")
                                 for name in names):
            return key  # "allerg" spellings: "allergys", "allergic"
    return None


# A line that opens with a contraction of a subject and a verb is a statement, however the words
# fold: "we're getting a puppy" becomes "were getting a puppy", and "were" on its own reads as the
# question "were you ...". Only a contraction of a question word ("what's", "where's", "who's")
# still asks, and those fold to a question word anyway. The subject is what tells them apart.
OPENS_WITH = re.compile(r"\s*([A-Za-z]+['\u2019][A-Za-z]+)")
SUBJECT_CONTRACTION = frozenset("we i they you he she it that there this these those".split())


def _a_contraction_opens(text):
    """Whether the line opens with a subject folded into a verb: "we're", "i've", "that's"."""
    found = OPENS_WITH.match(text or "")
    if not found:
        return False
    return found.group(1).lower().replace("\u2019", "'").split("'")[0] in SUBJECT_CONTRACTION


def _asked(text, low):
    """Whether the line asks something at all: a statement never is a recall question."""
    if "?" in text:
        return True
    if not low:
        return False
    if low[0] in QUESTION_START and _a_contraction_opens(text):
        return False
    if REMEMBERING.match(low[0]):
        return True
    if " ".join(low[:2]) in ("do you", "did you", "you know", "did i", "do i", "can you"):
        return True
    return low[0] in QUESTION_START


def _asked_them(line):
    """Whether the line asks the user a question about themselves, rather than about the bot.

    "what else have i said" is the person; "do you remember me" is about the bot's memory of
    them, and the store has a warmer answer for it than a list of facts.
    """
    low = words(line)
    if not low:
        return False
    if low[0] in ("do", "did", "are", "can", "could", "would", "will") and "you" in low[:2]:
        return False
    return True


def _the_slot(line):
    """Whether the line names one of the store's own slots behind "the" rather than "my".

    People say the thing back to the bot the way they would to someone who was listening: "what
    was the budget", "what was the name", "and the dog, whats he called". The rule above wants
    "my" or "i" in the line, so all of those were refused as questions about the world and the
    answer was a hedge or a card about budgeting. Only the definite article in front of a slot
    counts, so "what is the budget for a wedding" names a budget of nobody's and is still left
    alone by the frame it is asked in (`ask` reads "the" only with a recalling word).
    """
    low = words(line)
    for i, word in enumerate(low):
        if word == "the" and i + 1 < len(low) and _key(low[i + 1]):
            return True
    return False


def _without_the_lead(text):
    """The line with its pleasantries and its return-to-topic clause taken off the front, and
    the slot that clause named, if it named one.

    Both are in front of the question rather than part of it: "thanks! what was my name" and
    "back to the job, what was my job again" ask the same thing, and reading the lead-in as if
    it were the question made the second one ask nothing at all. The clause often names the
    thing and then the question calls it "it" ("about the budget, what was it again"), so the
    slot it named is handed back to be the answer when the question itself names none.
    """
    line = LEAD.sub("", text).strip(" ,.!?;:-")
    named = None
    for _ in range(3):
        cut = RETURNING.match(line)
        if not cut:
            break
        said = words(cut.group(0))
        if said:
            named = _key(said[-1]) or named
        line = line[cut.end():].strip(" ,.!?;:-")
    return line, named


def ask(text, why=False):
    """What the user wants to be reminded of: a fact key ("name", "job", "city", "pet",
    "allergy", "budget"), or None when the line is not a question about their own facts.

    A why-line is not one of those questions: the cause it wants is in the world, and the store
    only keeps what they said. `why=True` is for the caller that has their facts in hand and
    only wants the subject named ("why do we have pets" after "my dog is called rex"), which is
    where the store does have something to say.
    """
    if not isinstance(text, str):
        return None
    line, returning = _without_the_lead(" ".join(text.split()))
    if not line or len(line.split()) > 12:
        return None
    if WHY.search(line) and not why:
        return None  # why the world is a cause, and the store only keeps what they said
    if KEEPING_TRACK.search(line):
        return None  # a method for keeping a fact is advice, not the fact they told me
    # "What should I avoid eating" is a recall of the limit they gave, not advice about
    # eating: the limit shape says so itself (see LIMIT), so it is read before this guard.
    limit = bool(LIMIT.search(line))
    if (ADVICE.search(line) or SAY_NOW.search(line)) and not RECALLING.search(line) and not limit:
        return None
    # "how much can I spend" and "what do I do for a living" are quantity and job asks, not
    # advice about what to do, so they stay recalls.
    if (ACTION_ASK.search(line) and not RECALLING.search(line) and not limit
            and not re.search(r"\bhow (?:much|many)\b|\bfor a living\b", line)):
        return None
    how_to = HOW_TO_TELL.search(line)
    if how_to and TELLS_APART.search(line[how_to.end():]):
        return None
    if DRIVE_ASK.search(line):
        # "what do i drive" names the car they told you about, and the verb is not one of the
        # subject words: "how do i drive it" is a how-to about the thing in front of them, so
        # only the shape that asks for the car itself is read here.
        return "car"
    spend_tail = SPENT_ON_A_THING.search(line) if SPENDING.search(line) else None
    if spend_tail and line[:spend_tail.start()].strip(" ,."):
        line = line[:spend_tail.start()].strip(" ,.")
    low = words(line)
    if not low or not _asked(line, low):
        return None
    if (CALL_NAME.search(line) and not asks_for_a_word(line)
            and not A_PERSON_BY_WHAT_THEY_DO.search(line)):
        return "name"
    if AVOID.search(line) and USER.search(line):
        return "allergy"
    if re.search(r"\bdate of birth\b|\bbirth date\b", line, re.I):
        return "birthday"
    content = [word for word in low
               if word not in SCAFFOLD and word not in TIME_WORDS and len(word) > 1
               and not REMEMBERING.match(word)]
    if content and not WANTS_THE_FACT.search(line) \
            and all(word in EMPLOYER_WORDS for word in content):
        # "can my employer fine me", "does my employer have to give me a contract": the only thing
        # in the line the store keeps is the word "employer", and the question is about what the
        # employer may do, not about the job they told the bot. Nothing the store holds answers it.
        return None
    if not content:
        if returning:
            # "the budget, what was it again": the clause in front named the thing and the
            # question named it only as "it", so what the clause named is what is asked for.
            return returning
        if limit:
            return "limit"  # "what can't i have" is the limit they gave, and nothing else
        # "what do you know about me?", "what have I told you": nothing but the user is left,
        # so the ask is the whole picture. Only those shapes: "what should I say?" names
        # nothing either, and it is a request for advice about the chat, not a recall.
        # A question that is still about the person ("what else have i said") is the same ask:
        # there is nothing named to answer, so the picture is the answer. "what do you know"
        # says nothing about them and is left alone.
        if HOW_KNOW.search(line):
            return None
        if ME.search(line):
            return "me"
        # A question that is about the person and says "know"/"remember" is the same ask with
        # nothing named ("what else do you know about me"), so the picture is the answer. A
        # question about what they *said* is not: "what was the last thing i said" wants the
        # line itself, and the store quotes it.
        # The person has to be named as the thing that is known ("about me", "what have you
        # learned about me"): "can i still learn" has a knowing word in it, but the thing they
        # want to know is whether the world allows it, not what the store holds, and read as a
        # recall it comes back as "so far it's been the learn drive" - their own doubt handed
        # back to them as a fact about themselves.
        if USER.search(line) and _asked_them(line) and KNOWING.search(line) \
                and KNOWN_OBJECT.search(line):
            return "me"
        return None
    if not USER.search(line) and not (RECALLING.search(line) and _the_slot(line)):
        return None  # a question about the bot ("what's your name"), not about what they said
    if LIVING.search(line):
        return "job"
    if any(word in PEOPLE for word in content):
        return None
    if limit and not [word for word in content if word not in LIMIT_WORDS]:
        return "limit"  # "what can't i eat" names no subject: the ask is the limit they gave
    modifierless = []
    for at, word in enumerate(content):
        after = content[at + 1] if at + 1 < len(content) else ""
        if (word in RECALL_MODIFIERS and after and _key(after)
                and not (word in ("old", "older") and HOW_OLD.search(line))):
            continue
        modifierless.append(word)
    content = modifierless
    keys = []
    for word in content:
        key = _key(word)
        if not key:
            return None  # a word that is not one of the subjects: a real request, not a recall
        keys.append(key)
    if (DECIDING.search(line) and not RECALLING.search(line)
            and any(key in keys for key in DECIDED_ABOUT)):
        return None  # a decision they are asking about, not a fact they told the bot
    if (WORLD_SUBJECT.match(line) and not RECALLING.search(line)
            and any(key not in PERSONAL for key in keys)):
        # A thing of theirs is not an attribute of theirs: "is my budget ok" asks what the store
        # was told, and "will a dog get on with my cat" asks about the pair, so the entry that
        # knows the pair answers it rather than the store claiming no cat was ever mentioned.
        return None
    for key, _ in SUBJECTS:
        if key in keys:
            return key
    return None


__all__ = ["ask", "SUBJECTS", "SCAFFOLD", "PEOPLE", "ME", "ADVICE"]


# ---------------------------------------------------------------------------------------------
# "Is there an earlier turn?" - one check for the whole bot, not one per module.
#
# Every reply that comes out of what the person said has to answer the same question first: is
# this line pointing back at something already said, and at what? It has been asked in dozens of
# places with dozens of cue lists - "again", "remind me", "did i say", "what was my", "you said",
# "back to" - so each new wording of the same ask was fixed in whichever module was reached first
# and missed in every other one. "remind me how many nights" was answered from the pool because
# the cue named the person ("did i") and a reminder names the bot.
#
# This is the one reader. Three parts, each general:
#
#   cue    the words that make a line look back: again, remind, remember, recall, forget,
#          did I, what was my, you said, told me, earlier, before, back to, same again.
#   thing  what it points at: the fact key the store knows (`ask`), or failing that the line's
#          own content words with the asking frame stripped ("how many nights" -> "nights").
#   turn   the earlier user turn carrying those words, newest first, plural and singular folded
#          ("nights" finds "four nights").
#
# A look-back with no earlier turn carrying its thing is not a look-back: nothing said it, so the
# modules go on as they are and the store's "I don't know it yet" stays the answer.
LOOKS_BACK = re.compile(
    r"\b(?:again|remind|reminds|reminded|reminding|remember|remembers|remembered|"
    r"recall|recalls|recalled|forget|forgets|forgot|forgotten)\b"
    r"|\b(?:did|do|does|was|were|am|are|have|has|had)\s+(?:i|we)\b"
    r"|\bwhat\s+(?:was|were)\s+(?:my|our)\b"
    # "whats my current salary" is the present tense of the same ask, and it was not a cue at all:
    # "whats my budget" after "we have 3000 for it" was answered by the composer, whose reply
    # said nothing the store knew. The figure reader still decides whether it can answer.
    r"|\bwhat(?:'s|s|\s+is)\s+(?:my|our)\b"
    r"|\bhow\s+(?:many|much)\b"
    r"|\b(?:was|were)\s+(?:that|it|they|those|these)\b"
    r"|\b(?:you|u)\s+(?:said|told)\b|\btold\s+me\b"
    r"|\b(?:earlier|before)\b|\bback\s+to\b|\bsame\s+(?:again|one)\b", re.I)

# The asking frame, which says nothing about what is wanted back: "remind me how many nights"
# points at the nights, not at the reminding.
_ASKING_FRAME = frozenset("""
again remind reminds reminded reminding remember remembers remembered recall recalls recalled
forget forgets forgot forgotten me my our us we i you u your yours the a an and or so but
how many much what which who when where why was were is are am do does did done have has had
long far old big tall heavy short wide deep high low often soon much
said say says saying tell told telling earlier before back to same one ones that this it
please pls can could would will about of for in at on with by any anything something thing
""".split())


def looks_back(text):
    """The words that make this a look-back line, or "" when the line stands on its own."""
    if not isinstance(text, str):
        return ""
    found = LOOKS_BACK.search(" ".join(text.lower().split()))
    return found.group(0).strip() if found else ""


def _stems(said):
    from .topics import stem
    return {stem(word) for word in words(said) if word}


def the_earlier_turn(text, memory=None):
    """The earlier turn a look-back line points at: {"cue", "thing", "said"} or None.

    This is the check every reply from memory goes through, and it answers the question the way it
    should be asked: *is there an earlier turn carrying the thing this line names?* There is no
    look-back when there is nothing behind it, so None is returned both for a line that stands on
    its own and for one that points at something never said ("remind me how many nights in
    portugal" when no night in portugal was ever mentioned).

    The thing is the line's own content words with the asking frame stripped - "remind me how many
    nights" points at the nights, "what was my deposit again" at the deposit - and a turn counts
    when it carries every one of them, so a line that adds a word never said is not pointed at the
    turn that lacks it. `said` is the person's own earlier lines that carry the thing, newest
    first, at most three.
    """
    cue = looks_back(text)
    if not cue:
        return None
    thing = " ".join(word for word in words(text) if word not in _ASKING_FRAME)
    want = _stems(thing)
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    if not want:
        # A line with nothing but the frame ("what did i say again") points at the last turn.
        said = [str((turn or {}).get("user") or "") for turn in turns[::-1]
                if isinstance(turn, dict) and (turn or {}).get("user")]
        said = said[:3]
        return {"cue": cue, "thing": ask(text) or "", "said": said} if said else None
    # The words nobody in the chat has said are not part of the thing: "and how much am i putting
    # away each month" asks about "im putting 400 a month towards a 20 grand deposit", and "away"
    # is a word of the ask that is in no line at all. Requiring every word made the ask point at
    # nothing, so the store stayed quiet and a plan card took the turn instead of "You said 400.".
    # A word that is in some other line is a real part of the thing, and still has to be carried.
    everywhere = set()
    for turn in turns:
        if isinstance(turn, dict):
            everywhere |= _stems(str(turn.get("user") or ""))
    unsaid = want - everywhere
    said = []
    for turn in reversed(turns):
        line = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        have = _stems(line) if line else set()
        if len(want & have) >= 2 and (want - have) <= unsaid:
            # Two words of the ask carried by the line, and whatever it does not share is a word
            # nobody said: "putting away each month" reaches the line that says "putting 400 a
            # month". One word shared is not enough - "how many nights in portugal" shares only
            # "nights" with a turn that never mentions portugal, and it points at nothing.
            said.append(line)
        elif line and want <= have:
            said.append(line)
        if len(said) == 3:
            break
    if not said:
        return None
    return {"cue": cue, "thing": thing, "said": said}
