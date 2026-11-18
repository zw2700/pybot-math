"""How many of a thing the person has, kept as a number and given back when they ask.

"i have three brothers" was filed only as one person ("people": ["brother"]) with the number
dropped, so "how many brothers do i have" answered "I don't know enough to answer that honestly"
one turn after being told. Animals and children have readers of their own; this is every other
thing a person counts - brothers, sisters, cars, grandkids, cats they are about to get - and the
noun is whatever they said, not a list, so a count nobody has thought about yet is kept too.

Nothing is answered unless the ask names a count the store holds, so a "how many" about the
world ("how many hours should i study") is left to the modules that know about it.
"""
import re
import string

from bot.memory import facts

# The number in front of the thing: "three brothers", "2 cars", "a couple of dogs". The words
# between the number and the noun are the ones people put there ("two more brothers", "three
# lovely sisters", "two step brothers"), never a verb.
NUMBER_AHEAD = re.compile(
    r"\b(?P<n>a couple of|a pair of|couple of|pair of|one|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve|\d{1,2})\s+"
    r"(?:(?:more|other|elder|older|younger|little|lovely|grown|grown-up|step|half|"
    r"foster|adopted|healthy|beautiful|new|old)\s+){0,2}"
    r"(?P<who>[a-z][a-z-]{2,})\b", re.I)
# A possession, because "three brothers" on its own is as likely to be a fact about someone
# else ("my mum has three brothers") as a count of their own.
THEY_HAVE = re.compile(
    r"\b(?:i|we)(?:\s+have|'ve|ve|\s+got|\s+have got|\s+own)\s+(?P<rest>[^.!?]{0,48})", re.I)
# The same said the other way round: "my three brothers", "our two cars". The number has to come
# straight after the possessive, because "my mum has three brothers" is hers, not theirs.
MY_THREE = re.compile(
    r"\b(?:my|our)\s+(?P<rest>(?:a couple of|a pair of|couple of|pair of|one|two|three|four|"
    r"five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\b[^.!?]{0,40})", re.I)

# The count put right on its own, with no possession in it: "no, four brothers", "sorry, 3
# sisters", after "i have three brothers". The correction word is what makes it a correction
# rather than a remark, so it is required.
CORRECTED = re.compile(
    r"^\W*(?:no|nope|sorry|actually|wait|i mean|make that|oops|correction|sorry, no)\b"
    r"[\s,]*"
    # Filler between the change word and the figure. "actually make that 5 nights now", "its 5
    # nights now", "sorry, change it to 6": the change is the whole line, so what stands between
    # the word that makes it one and the number is filler, and demanding the figure straight
    # after the change word read none of these. The chat that said "we have 4 nights" and then
    # "actually make that 5 nights now" was told "Got it - 5 nights now" and answered "how many
    # nights was it" with "You've got four nights" two turns later.
    r"(?:(?:make|change|put)\s+(?:that|it)(?:\s+to)?|its|it's|to)?\s*"
    r"((?:a couple of|a pair of|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|\d{1,2})\b[^.!?]{0,32})$", re.I)
# A line that asks states no count: "do i have two brothers" is a question, and answering it
# with the number they guessed is worse than leaving it.
#
# A question that opens on an auxiliary opens on the subject just after it ("were you going to
# invite people", "is there a table for eight", "can i freeze it"), so that is what is read, not
# the auxiliary alone. Read alone it took "were doing a roast on sunday for ten" for a question -
# people start a plan with the same word - and the table was never filed, so the chat that came
# back to "how many people was it again" was answered with the card's own six-person example.
_SUBJECT_AFTER = (r"(?:i|you|we|they|he|she|it|there|that|this|these|those|any|some|"
                  r"my|your|our|their|his|her|its)\b")
ASKING = re.compile(r"^\W*(?:(?:do|did|does|have|has|are|is|was|were|can|could|would|should|"
                    r"will)\s+" + _SUBJECT_AFTER + r"|how|what|which|who|when|where|why)\b",
                    re.I)

# Plurals that are not made with an "s", so the count can be filed under the word they ask with.
IRREGULAR = {"children": "child", "people": "person", "men": "man", "women": "woman",
             "grandchildren": "grandchild", "grandkids": "grandkid", "nieces": "niece",
             "nephews": "nephew", "mice": "mouse", "geese": "goose", "feet": "foot",
             "teeth": "tooth", "oxen": "ox", "wives": "wife", "lives": "life",
             "knives": "knife", "shelves": "shelf", "wolves": "wolf", "halves": "half"}
# Counts another reader already keeps, so this one neither files them nor answers for them:
# animals are memory_store's pet list, children its kids, and both answer "how many" already.
THEIRS = frozenset("""cat cats dog dogs puppy puppies kitten kittens rabbit rabbits bunny
bunnies hamster hamsters fish horse horses pony ponies parrot parrots pet pets animal animals
kid kids child children baby babies son sons daughter daughters""".split())
# Words that follow a number without being things a person counts: how long something takes,
# how much it costs, how old somebody is. Filing them would answer "how many hours do i have"
# with the hours of a shift.
NOT_A_THING = frozenset("""minutes minute hours hour days day weeks week months month years year
o'clock pounds pound quid euros euro dollars dollar pence pennies percent times time
years-old oclock weeks-old months-old miles mile kilometres km kilos kilo pounds-weight
stone stones stones-weight left right quarter quarters third fourth fifth half halves dozen
litres litre pints pint ounces ounce grams kilo kilos""".split())

# How many people are in the group the person is part of: "there are four of us", "theres 12 of
# us", "we're a family of four". A household size is not a count of a thing they have - it is the
# size of the group they are in - so it is kept under its own name, and a line that says how many
# are coming somewhere ("there are 8 of us coming") is about that outing, not about the house.
GROUP_NUMBER = (r"a couple of|a pair of|couple of|pair of|one|two|three|four|five|six|seven|"
                r"eight|nine|ten|eleven|twelve|\d{1,2}")
# What may follow "of us" for the line to be about the group itself: "there are four of us",
# "there are four of us at home", and not "there are four of us coming".
_GROUP_TAIL = (r"(?=\s*(?:$|[,.!?;:]|\b(?:here|now|at home|in the house|in the flat|"
               r"in the home|in total|altogether|total|and|but|so)\b))")
GROUP_OF_US = re.compile(
    r"\b(?:(?:there|it)\s*(?:'s|s|'re|re|are|is|'ll|ll|will|would)|"
    r"we\s*(?:'re|re|are|'ll|ll|will))\s+"
    # A table is announced in the future as often as in the present - "theres going to be 8 of
    # us", "there will be 6 of us" - and the size is the same number in the chat either way.
    r"(?:(?:going to be|gonna be|will be|would be|should be|be)\s+)?"
    r"(?:(?:just|only|now|still|currently|actually)\s+){0,2}"
    # "the" belongs to the phrase as people say it - "its just the two of us", "the three of us" -
    # so it sits in front of the number without being part of it.
    r"(?:the\s+)?(?P<n>" + GROUP_NUMBER + r")\s+of us\b" + _GROUP_TAIL +
    # "we are 4 people", "there are three people here": the group said with the noun people
    # rather than with "of us". A household size was only read when the line used the phrase
    # "of us", so "we are 3 people" was filed as nothing and the very next "how many of us are
    # there" was a search hedge about a fact the chat had just been told.
    r"|\b(?:we\s*(?:'re|re|are)|there\s*(?:'s|s|'re|re|are|is))\s+"
    r"(?:(?:just|only|now|still|currently|actually)\s+){0,2}"
    r"(?P<n2>" + GROUP_NUMBER + r")\s+(?:people|persons?)\b" + _GROUP_TAIL +
    # The fragment people type on its own, with no verb in front: "4 of us", "just the two of
    # us". It is the whole line, because a bare "two of us" inside a longer sentence says what
    # that sentence is about and not how many they are at home.
    r"|^\W*(?:(?:and|so|well|ok|okay|oh|hmm)\b[,.]?\s+)*(?:(?:just|only)\s+)?(?:the\s+)?"
    r"(?P<n3>" + GROUP_NUMBER + r")\s+of us\b" + _GROUP_TAIL, re.I)
# The group put right with no announcement in front of it: "no, the 5 of us", "actually 6 of us",
# "sorry, just 4 of us now". The announcement is what makes a bare "5 of us" a statement of the
# group as it stands; with a change word in front the line is a correction of the group the chat
# already holds, and the figure is the group's however it is said.
GROUP_CORRECTED = re.compile(
    r"^\W*(?:no|nope|sorry|actually|wait|i mean|make it|make that|hold on|hang on|correction)\b"
    r"[^.!?]{0,12}?(?:the\s+)?(?P<n>" + GROUP_NUMBER + r")\s+of us\b", re.I)
# "we're a family of four", "a household of three": the same group said as a size.
GROUP_OF_FOUR = re.compile(
    r"\b(?:family|household)\s+of\s+(?P<n>" + GROUP_NUMBER + r")\b(?!\s+[a-z])", re.I)

# The ask for the size of that group: "how many of us are there", "how many people are there in
# the house", "how big is my family". Every tail allowed here is a way of asking how many are in
# the group, so "how many of us are going to the park" is not one of them. The tail also has to
# carry the way a person points back at a number that was already given - "how many of us is it",
# "how many of us is it again", "how many people was that" - because that is the ask that comes
# late in a chat, and without the pointing words it was read as a question about the world: four
# turns after "theres 6 of us now" the store answered "how many of us is it again" with the
# driving-lessons card, and the number it was holding was the whole answer.
_GROUP_ASK_WORDS = (r"(?:are|is|were|was|there|here|now|altogether|total|in all|at home|"
                    r"it|that|again|then|did i say|did we say|do you remember|remind me|"
                    r"in the house|in the flat|in the home|in my (?:house|flat|home|household)|"
                    r"in our (?:house|flat|home|household)|live here|living here|"
                    r"live in the (?:house|flat|home)|living in the (?:house|flat|home))")
# What a pointer back at a number already given looks like on the end of the ask: "how many of us
# is it again", "how many of us was it", "how many of us did i say". Only these words, so "how
# many of us are going to the park" is still a question about the outing and not the household.
_GROUP_POINTER = r"(?:is it|was it|were they|is that|was that|again|then|did i say|did we say|i say)"

# The two sets are one tail of allowed words, in any order, because people mix them: "how many of
# us is it now" is the question word, the pointer and the time word in a row.
_GROUP_TAIL = _GROUP_ASK_WORDS + r"|" + _GROUP_POINTER

GROUP_ASK = re.compile(
    r"\bhow many of us(?:\s+(?:" + _GROUP_TAIL + r"))*\s*[?.!]*$"
    r"|\bhow many people(?:\s+(?:" + _GROUP_TAIL + r"))*\s*[?.!]*$"
    r"|\bhow (?:big|large) (?:is|are) (?:my|our|the) (?:family|household)\b", re.I)
# The same ask from the other side of the conversation: "how many of you are there" in a chat that
# gave a headcount is the group again, and the store answered it "I don't know that yet. Who do
# you live with?" - a denial of a number it was holding. "you" is the household as the bot sees
# it, so only the group is read for it: a dinner table is not the answer to how many are at home.
GROUP_ASK_YOU = re.compile(
    r"\bhow many of (?:you|u)(?:\s+(?:" + _GROUP_ASK_WORDS + r"|" + _GROUP_POINTER + r"))*"
    r"\s*[?.!]*$"
    # "how many of you live there", "how many of you are living at home": the household asked
    # with a verb instead of the tail above.
    r"|\bhow many of (?:you|u) (?:live|living|are living)"
    r"(?:\s+(?:there|here|at home|now|altogether))?\s*[?.!]*$", re.I)
# The same ask with nothing named at all: "how many are coming", "how many are going", after a
# headcount was given for the thing in hand ("theres going to be 6 of us" / "actually theres 8 of
# us now"). There is no noun for the count reader to hang on, so the ask leans on the group size
# the store already holds. It has to be the whole line, because "how many are coming to the
# wedding" names an outing of its own and is not the size of the group they are in.
BARE_GROUP_ASK = re.compile(
    r"\bhow many (?:are|is|were|was) (?:coming|going|expected|there)"
    r"(?:\s+(?:then|now|again|altogether|in total))?\s*[?.!]*$", re.I)

# The count asked for with no noun at all: "how many was it", "how many again". Eight turns after
# "theres going to be 8 of us" that ask wants the number the chat already holds, and it names
# nothing else that could take it. Only the pointing words are allowed after it, so "how many are
# coming to the wedding" keeps the answer that ask has of its own.
BARE_COUNT_ASK = re.compile(
    r"\bhow many\s+(?:was|is|were|are)\s+(?:it|that|there)"
    r"(?:\s+(?:again|then|now|altogether|in total))?\s*[?.!]*$"
    r"|\bhow many again\b\s*[?.!]*$"
    # The same ask with the pointing words folded away, which is what several readers hand here:
    # the whole line is "how many".
    r"|\A\W*how many\W*[?.!]*$", re.I)

# The name the group size is kept under. It is not a thing they have, so it cannot collide with a
# count of one ("how many brothers") and no ask for a thing can be answered with it.
GROUP = "us"

# The size of the table the person is cooking or going out for: "im doing a roast on sunday for 8
# people", "having 6 people over", "eight guests on saturday", "a table for four". It is not a
# possession, so `THEY_HAVE` never finds it, and it is not the size of their household either: a
# dinner for eight in a house of three is eight. The number is the one thing that cannot be worked
# out from the line it is asked in, so a chat that has moved on to the potatoes still needs it when
# the person asks "and how many people".
# The meals a bare number can be a table for. A meal word on its own says nothing about people -
# "a roast for ten" is people and "a roast for two hours" is a time - so the number has to end the
# phrase before this reads a table out of it.
TABLE_MEAL = (r"roast|dinner|supper|tea|lunch|breakfast|meal|barbecue|bbq|barbeque|party|"
              r"spread|buffet|feast|brunch|carvery")
# The day a table is for: "itll be 4 of us on sunday", "there are six of us next friday". A day
# after the group is the plan the number is for, not the size of the household - "there are four
# of us at home" is the household - and it is the commonest way the group size is said in a chat
# that later asks for it ("how many was it again" two turns after "itll be 4 of us on sunday"
# found nothing, because the day ended the phrase the table reader was looking for).
_A_DAY = (r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tues|tues|tue|weds|"
          r"wed|thurs|thur|thu|fri|sat|sun|weekend|tonight|tomorrow|today")
# The numbers that alternative reads. A table can be bigger than a household, so it takes the tens
# and the digits as well as the small numbers above.
BARE_NUMBER = GROUP_NUMBER + r"|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
BARE_NUMBER += (r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|a hundred|one hundred|"
                r"\d{1,3}")
PARTY = re.compile(
    r"\b(?:for|having|expecting|feeding|cooking for|catering for|a table for|table for|"
    r"booking for|booked for|party for|dinner for|lunch for|tea for|supper for|seats? for|"
    r"invited|inviting)\s+(?:the\s+|just\s+|only\s+)?(?P<n>" + GROUP_NUMBER + r")\s+"
    r"(?:people|persons?|guests?|adults?|heads?|folk|friends|kids|children)\b"
    r"|\b(?P<n2>" + GROUP_NUMBER + r")\s+"
    r"(?:people|persons?|guests?|adults?|heads?|friends)\s+"
    r"(?:coming|over|round|for|at|on)\b"
    # "theres 10 of us for dinner on friday" is the table, not the household: the tail says what
    # the group is for, and the household reader keeps its own number for "at home".
    r"|\b(?P<n4>" + GROUP_NUMBER + r")\s+of us\s+"
    r"(?:(?:coming|over|round)\b|for\s+(?!(?:a|an|the|good|now|once|ages|keeps|ever)\b)[a-z])"
    # The day the plan is on: "itll be 4 of us on sunday", "it will be 4 of us on sunday",
    # "six of us next friday". Only a day word, so "there are four of us at home" stays the
    # household and "of us on the bus" is nothing at all.
    r"|\b(?P<n7>" + GROUP_NUMBER + r")\s+of us\s+(?:on|this|next)\s+(?:the\s+)?"
    r"(?:" + _A_DAY + r")\b"
    # A table is always people, so the number after it needs no noun: "ive booked a table for
    # four". A unit after the number ("a table for two hours") is not a count of people.
    r"|\b(?:a table for|table for|booking for|booked for|reservation for)\s+"
    r"(?P<n3>" + GROUP_NUMBER + r")\b(?!(?:\s*(?:minutes?|hours?|days?|weeks?|months?|years?|"
    r"courses?)\b))"
    # The same with the cooking said instead of the meal: "im cooking for 8 on saturday",
    # "catering for twenty". The day after the number is what makes it a table, so a length of
    # time ("cooking for 2 hours") is still a duration and not people.
    r"|\b(?:cooking for|catering for|feeding|having over|having round)\s+"
    r"(?P<n6>" + GROUP_NUMBER + r")\b(?!(?:\s*(?:minutes?|hours?|days?|weeks?|months?|years?|"
    r"courses?|of them)\b))"
    # A meal named, then a bare number: "im doing a roast for ten", "the roast is for 10",
    # "barbecue for twenty", "tea for six". People leave the noun out when the meal is already on
    # the line, and the store kept nothing: the same chat asked "how many people is it for" two
    # turns later and the card answered with its own six-person example. The number has to end
    # there, so "a roast for 20 minutes" and "dinner for 2 hours" (a duration) are not a table.
    r"|\b(?:" + TABLE_MEAL + r")\b[^.?!]{0,24}?\bfor\s+(?:the\s+|just\s+|only\s+)?"
    r"(?P<n5>" + BARE_NUMBER + r")\b(?!(?:\s*(?:minutes?|hours?|days?|weeks?|months?|years?|"
    r"courses?|more|less|pounds?|quid|euros?|dollars?|kg|kilos?|grams?|litres?|pints?|miles?|"
    r"metres?|o'clock)\b))", re.I)
# The ask for that number: the people the plan is for, not a question about the world. The tail
# allowed after the noun is what a person says when they want the figure back ("and how many
# people", "how many people again", "how many guests is it for"), so "how many people live in
# manchester" and "how many people does a chicken feed" are left to the knowledge base, and "how
# many people should i invite" to the entry that plans a party.
PARTY_ASK = re.compile(
    r"\bhow many (?:people|persons?|guests?|heads?|adults?)\b\s*"
    r"(?:$|[,.!?;:]|\b(?:again|then|though|is it|is that|are coming|coming|was it|was that|"
    r"you think|do you think|do i need|do i cook|am i cooking|we having|did i say|did we say)\b)"
    r"|\bhow many (?:are|is) (?:coming|it for|we having|we cooking for|we expecting)\b"
    r"|\bhow many did i say\b"
    # "how many did i book for" asks the same number in the words a booking is made in, and it
    # was answered "That is everything I have on that one" two turns after the person said it.
    r"|\bhow many (?:did|have) (?:i|we) (?:book|booked|reserve|reserved|ask for|asked for)\b"
    r"|\bhow many is (?:the|that|this|my|our) (?:table|booking|reservation) for\b"
    # The count asked about the job instead of the people. "how many am i baking for",
    # "how many are we cooking for", "how many am i making for again": the number they want back
    # is the size of the table, but the ask names the activity, so the noun above never appears
    # and the line fell to a search suggestion two turns after the person said "about 15 people".
    # The verb list is the work done for a table, not a way of asking about the world, and the
    # word after it has to be "for" - "how many am i cooking" on its own is a question about how
    # to cook, which is not this one.
    r"|\bhow many (?:am|are|was|were) (?:i|we) (?:cooking|baking|making|catering|feeding|"
    r"preparing|planning|doing)\b[^.?!]{0,18}?\bfor\b"
    r"|\bhow many (?:do|did|will) (?:i|we) (?:cook|bake|make|cater|feed|prepare|plan) for\b",
    re.I)
# A line that changes the number: "actually one more is coming so theres 10 of us now". It says the
# size of the group, not of a table, but the change is what makes it the table's: a chat that set
# the table at eight and has just been told there are ten of them must not answer "eight" two
# turns later.
CHANGED = re.compile(r"\b(?:actually|instead|now|sorry|hang on|one more|another|extra|"
                     r"make that|no)\b", re.I)
# The number put right with no noun of its own: "we booked a table for 6" / "make it 8". The
# line names no people, so every count reader above passes it - `_the_party` wants a noun after
# the figure and `_the_group` wants "of us" - and the store went on holding six while the plan it
# kept said eight, so "how many did i book for" two turns later had nothing to answer with. A
# correction is the whole line, so what may follow the figure is filler only: a noun there ("no,
# four brothers") is a count of its own and is read by `CORRECTED`.
CHANGED_BARE = re.compile(
    r"\b(?:make it|make that|put it at|change it to|change to|actually|sorry|no|instead|"
    r"lets say|let's say|now)\b[\s,]*"
    r"(?:it\s+)?(?:to\s+|at\s+)?(?P<n>" + GROUP_NUMBER + r")\b"
    r"(?:\s*,?\s*(?:people|persons?|guests?|heads?|adults?|of us|now|instead|please|thanks|"
    r"after all))*\s*[.!]*$", re.I)
# The same change said as the group: "we're 10 now", "there's 10 of us now".
NOW_THE_NUMBER = re.compile(
    r"\b(?:we|there)\s*(?:'s|'re|re|are|is|s)?\s+(?:now\s+)?(?P<n>" + GROUP_NUMBER + r")\s+"
    r"(?:of us\s+)?now\b", re.I)
# A guest added or dropped after the number was given: "im having 8 people over" / "one more is
# coming" is nine, and the line names no total at all, so the change is made to the number the
# chat holds. Only the whole line counts: "one more thing" and "one more question" are not
# people.
ONE_MORE = re.compile(
    r"^\W*(?:and\s+|oh\s+|plus\s+)?(?:one|1)\s+more"
    r"(?:\s+(?:is\s+coming|is\s+coming\s+now|coming|now|person|guest|guest\s+is\s+coming|"
    r"of\s+us|of\s+them))?\s*[.!]*$", re.I)
ONE_LESS = re.compile(
    r"^\W*(?:and\s+|oh\s+)?(?:one|1)(?:\s+of\s+(?:them|the\s+guests?|the\s+group))?\s+"
    r"(?:less|cant\s+come|cannot\s+come|can't\s+come|"
    r"isnt\s+coming|isn't\s+coming|is\s+not\s+coming|has\s+dropped\s+out|dropped\s+out|"
    r"cant\s+make\s+it|can't\s+make\s+it)"
    r"(?:\s+(?:now|after\s+all|anymore|any\s+more))?\s*[.!]*$", re.I)
# ...unless it is about the house they live in, which is a different number from the table.
ABOUT_THE_HOUSE = re.compile(r"\b(?:at home|in the house|in the flat|in the home|live|lives|"
                             r"living|living here|household|family|house)\b", re.I)
# An ask that points back at a number already said rather than asking a new question: the number
# the chat holds is the answer even when it was said as a group ("theres 10 of us") and not as a
# table.
POINTS_AT_A_NUMBER = re.compile(r"\b(?:again|was it|was that|is it for|did i say|did we say|"
                                r"do you remember|remind me)\b", re.I)
# What the party size is kept under: the people, not a thing they own, so that a count of anything
# else ("how many brothers") is never answered with the number at the table.
PARTY_THING = "person"

# How far back a chat is read for the word that makes its people a table: a few turns, because
# the meal is said at the start and the number of people can come a turn or two later.
LOOK_BACK_FOR_A_MEAL = 6

# The people for the table, said with no cue before the number and no word after it: "about 15
# people", "15 people, mostly her sisters". The noun and the number are both there; the only thing
# missing is the word that says what they are for, because the chat has already said it ("my mum
# turns 80 next week and we are doing a tea for her"). Two turns later "how many am i baking for
# again" had nothing to answer from, so the chat fell to a barbecue portion card. "i met 15 people
# at work" is the same shape and is not a table, so this is read only in a chat that has named a
# meal, a cake or a party (`_the_chat_feeds_people`).
BARE_PEOPLE = re.compile(
    r"\b(?:(?:about|around|roughly|maybe|probably|just|only|some|like)\s+)?(?P<n>" + BARE_NUMBER +
    r")\s+(?:people|persons?|guests?|adults?|heads?|folk)\b", re.I)
# What makes the people a table rather than a crowd: a meal the chat is cooking, a cake being
# baked, a party being given. Only ever asked about a chat, never about the line that gives the
# number, which is the point - the line that gives the number has no word for it.
A_MEAL_IN_THE_CHAT = re.compile(
    r"\b(?:" + TABLE_MEAL + r"|cake|cakes|bake|baking|cooking|cook|menu|scones?|birthday|"
    r"buffet|canapes|finger food)\b", re.I)


# Where the phrase that names the thing counted stops: "two flat tyres" is a count of tyres and
# "three jars of jam" a count of jars, but "two cats called milo" is a count of cats. The thing is
# the last word before one of these, so an adjective the table has never seen ("flat", "spare",
# "missed") is never filed as the thing itself.
PHRASE_ENDS = frozenset("""called named of and but with for to in at on from by near who that
which because so then when if about today tomorrow yesterday tonight now ago already still here
there not no only just instead rather than""".split())
# The same list joiner typed in a hurry: "i have 2 sisters n a brother", "three cats nd a dog".
# A joiner is not a thing, so it ends the phrase as "and" does - without this the phrase read on
# into "n a", the head came out as "a", and no count was filed at all, so the ask one turn later
# ("how many sisters do i have") was answered with "a quick search online will get you a solid
# answer" about the person's own family.
CHAT_JOINERS = frozenset("n nd".split())
MAX_PHRASE = 3      # "two big cardboard boxes" counts boxes; the head never goes further
# A verb ends the phrase, so the thing counted comes before it: "my three brothers live abroad"
# is a count of brothers. It is grammar, not subject matter, so the list is the verb "to be", the
# verbs a possession sentence uses and the regular endings; a word that describes the thing in
# front of it ("missed calls", "flat tyres") is left in the phrase and the head is read past it.
VERB_IN_PHRASE = frozenset("""live lives are is was were be been am come comes go goes went
have has had do does did get gets got make makes made take takes need needs want wants eat eats
ate cost costs work works stays stay move moves play plays run runs see saw know knows think
thinks feel feels look looks seem seems sit sits speak speaks grow grows cost""".split())


def _many(n):
    """The number as a word up to twelve, as digits after that."""
    for word, value in facts.PET_COUNT_WORDS.items():
        if value == n and " " not in word:
            return word
    return str(n)


def _head(after):
    """The thing a count is about: the last word of the phrase before it stops.

    "two flat tyres" -> "tyres", "two spare bedrooms" -> "bedrooms", "5 missed calls" -> "calls",
    but "two cats called milo and tom" -> "cats" and "three jars of jam" -> "jars". An adjective
    nobody listed ("spare", "missed", "flat") used to become the thing counted, so "i have two
    flat tyres" filed a count of flats and "how many flats do i have" answered "You've got two
    flats." Reading the head of the phrase fixes that without a longer list of adjectives.
    """
    phrase = []
    for word in str(after or "").lower().split()[:MAX_PHRASE]:
        word = word.strip(string.punctuation + "\u2019")
        if not word.isalpha() or word in PHRASE_ENDS or word in CHAT_JOINERS:
            break
        if word in facts.PET_COUNT_WORDS:
            break  # "four grandchildren, 2 boys": the next number starts a count of its own
        if word in VERB_IN_PHRASE or word.endswith(("ly", "ing")):
            break
        phrase.append(word)
    return phrase


# A count of people is often said with the word that says which relation it is. "i've got 4
# grandkids nd 2 great grandkids" is two counts, and a great grandchild is not a grandchild, so
# taking only the head of the phrase filed both under "grandkid" and the second number replaced
# the first: "how many grandkids have i got" answered "You've got two grandkids." The word in
# front says which relation it is, so the phrase keeps it.
#
# Most of those words can only be a relation - nothing is "two step ideas" or "two foster
# tyres" - but "great" is also praise ("three great ideas", "two great kids"), so it is kept
# only in front of a word for a person. A great dane stays a dane, which is what the head was
# before.
RELATION_AHEAD = frozenset(("grand", "step", "half", "foster", "adopted", "adoptive", "ex",
                            "surrogate"))
A_PERSON_TAIL = ("child", "kid", "son", "daughter", "aunt", "uncle", "niece", "nephew",
                 "parent", "mother", "father", "grandma", "grandad", "granddaughter",
                 "grandson", "gran", "nan", "dad", "mum")


def _the_relation(phrase):
    """The singular thing a phrase counts, with the word that says which relation it is."""
    if not phrase:
        return ""
    thing = _thing(phrase[-1])
    if not thing or len(phrase) < 2:
        return thing
    before = phrase[-2]
    if before in RELATION_AHEAD:
        return before + " " + thing
    if before == "great" and thing.endswith(A_PERSON_TAIL):
        return "great " + thing
    return thing


def _thing_of(phrase):
    """The singular of the thing the phrase asks about: its head, read the way it is filed."""
    return _the_relation(_head(phrase))


def _thing(word):
    """The singular of a counted noun, or "" when the word cannot be a count of things."""
    word = str(word or "").lower().strip("-")
    if not word or word in NOT_A_THING or len(word) < 3:
        return ""
    if word in IRREGULAR:
        return IRREGULAR[word]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("ches", "shes", "sses", "xes", "zes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    # "two sheep", "three deer": the count is right there and the word is the thing.
    return word


def _beds(rest):
    """How many bedrooms a phrase says the place has: "a 3 bed house" -> 3, or 0.

    "3 bed", "three-bed" and "3 bedroom" all say how many bedrooms the place has. A line that
    only says the number of bedrooms ("we have three bedrooms") is a count of bedrooms already,
    so filing it here as well changes nothing.
    """
    line = " ".join(str(rest or "").split())
    words = line.lower().split()
    for match in BEDS.finditer(line):
        said = match.group("n").lower()
        number = int(said) if said.isdigit() else facts.PET_COUNT_WORDS.get(said, 0)
        if not 0 < number <= 20:
            continue
        after = line[match.end():].strip(string.punctuation).split()
        # The beds are being described as part of the place, not counted on their own: a word
        # follows them ("a 3 bed house"), they are written onto the number ("2-bed flat"), or
        # the line names the kind of place somewhere ("our house is a three bed"). "we have two
        # beds" is a count of beds, and saying a place is a three bed is not what it says.
        if match.group("join").strip() == "-" or after or any(
                word in A_KIND_OF_PLACE for word in words):
            return number
    return 0


# "a 3 bed house", "2 bed flat", "three-bed terrace": the number is how many bedrooms the place
# has, and the place is one. Read as a count of things the number landed on the kind of place
# ("a 3 bed house" filed three houses), so the ask people actually make - "how many bedrooms do
# we have" - found nothing while the chat had just said it. The word "bed" with no "room" on it
# is what makes the line this shape: "3 bedrooms" already counts bedrooms on its own.
BEDS = re.compile(
    r"\b(?P<n>" + GROUP_NUMBER + r")\s*(?P<join>-?)\s*bed(?:room)?s?\b", re.I)
# A line that names the kind of place the beds are in ("our house is a three bed"): the way
# people give the size of a home when the home is not the next word.
A_KIND_OF_PLACE = frozenset("""house home flat place bungalow maisonette semi terrace terraced
cottage apartment rental rented bedsit studio pad maisonette maisonettes""".split())
# The words that end a count when they come in front of the thing: "a 3 bed house" and "a 3
# bedroom house" count the bedrooms, and the house is the kind of place that has them.
A_MEASURE_WORD = frozenset("bed beds bedroom bedrooms".split())


# Two figures joined into a range or a choice: "between 4 and 6 nights", "3 or 4 children", "2-3
# cars". Neither end is the count - the chat that said "between 4 and 6 nights" holds no number,
# and filing the last one made the ask a turn later answer "You've got six nights." Only the
# figure's own neighbourhood is read, so a range about something else in the line leaves the
# count alone.
_NUM_WORD = r"(?:a couple of|a pair of|one|two|three|four|five|six|seven|eight|nine|ten|\d{1,3})"
# A unit after a bare figure makes it a measurement, not a count of things: "its 20 degrees now"
# and "its 5kg now" say nothing about how many of anything they have.
NOT_A_COUNT = frozenset("""degrees degree percent miles mile km kms kilometres kilometers metres
meters cm mm kg kgs lbs lb oz litres liters ml celsius fahrenheit mph kph""".split())
A_RANGE_AROUND = re.compile(
    r"\bbetween\b[^.!?]{0,14}?" + _NUM_WORD + r"[^.!?]{0,10}?\band\b"
    r"|" + _NUM_WORD + r"\s*(?:-|\u2013|to|or)\s*" + _NUM_WORD, re.I)


def _counted(rest):
    """{thing: number} for the counts in one possession phrase."""
    found = {}
    rest = str(rest or "")
    for match in NUMBER_AHEAD.finditer(" " + rest):
        window = rest[max(0, match.start("n") - 16):match.end("who") + 12]
        if A_RANGE_AROUND.search(window):
            continue  # a range or a choice is not the number they have
        # The thing is the head of the words the number is in front of, not the first of them.
        tail = rest[match.start("who") - 1:]
        # "i have two dogs, rex and sam" names two dogs and then their names: what comes after
        # the comma is a list of names, so the thing counted is the word before it. Read as the
        # head of the whole phrase the store filed "two rex", and a line about Rex later ("rex
        # died in january") was no longer read against the dogs it had.
        if "," in tail:
            tail = tail.split(",", 1)[0]
        phrase = _head(tail)
        if any(word in NOT_A_THING for word in phrase):
            continue  # "two left feet", "three quarters of the cake": no count of things
        thing = _the_relation(phrase)
        # The words a count is handed over on stay handed over, however the phrase is read:
        # "two great kids" is children, not a count of great kids.
        if not thing or thing in THEIRS or thing.split()[-1] in THEIRS:
            continue
        if len(phrase) > 1 and phrase[0] in A_MEASURE_WORD:
            # "a 3 bed house" is three beds in one house, not three houses: the number is in
            # front of the measure word, and the word after it is the kind of place that has
            # them.
            continue
        said = match.group("n").lower()
        number = int(said) if said.isdigit() else facts.PET_COUNT_WORDS.get(said, 0)
        if number > 0:
            found[thing] = number
    return found


# The tens and the teens: a table can be bigger than a household, and "we're having a barbecue for
# twenty" is the same number as "for 20". PET_COUNT_WORDS stops at ten, so they are kept here
# rather than in the shared facts map, which other modules read for animals and children.
_BIGGER_NUMBERS = {"eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
                   "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
                   "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
                   "eighty": 80, "ninety": 90, "a hundred": 100, "one hundred": 100,
                   "a dozen": 12, "dozen": 12}


def _said_number(said):
    """The number a phrase names: "8", "eight", "twenty", "a couple of". 0 when it names none."""
    said = str(said or "").lower().strip()
    if said.isdigit():
        return int(said)
    found = facts.PET_COUNT_WORDS.get(said)
    if isinstance(found, int):
        return found
    return _BIGGER_NUMBERS.get(said, 0)


def _the_group(said):
    """How many people the line says are in their group, or 0 when it says nothing of the sort."""
    for pattern in (GROUP_OF_US, GROUP_OF_FOUR, GROUP_CORRECTED):
        for match in pattern.finditer(said):
            number = _said_number(match.group("n") or match.group("n2")
                                  or match.group("n3"))
            if number > 0:
                return number
    return 0


def _the_party(said):
    """How many people the line says are coming, or 0 when it says nothing of the sort."""
    for match in PARTY.finditer(said):
        number = _said_number(match.group("n") or match.group("n2") or match.group("n3")
                          or match.group("n4") or match.group("n5")
                          or match.group("n6") or match.group("n7"))
        if number > 0:
            return number
    return 0


# A booking sets the table without naming a meal: "we booked a table for 6 on friday" then "how
# many did i book for" is the number at that table, and it was answered before the bare headcount
# reader existed. Read where a count is handed back, never where a bare headcount is filed,
# because "i bought a table" is furniture and the people around it are not people being fed.
A_TABLE_BOOKED = re.compile(
    r"\b(?:book(?:ed|ing|ings)?|reserv(?:ed|ing|ation|ations))\b[^.]{0,24}\btables?\b"
    r"|\btables?\b[^.]{0,12}\bfor\s+(?:\d+|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve)\b"
    r"|\b(?:book(?:ed|ing)?|reserved)\b\s+(?:for\s+)?(?:\d+|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve)\b", re.I)


def _the_chat_lines(memory):
    """The lines of this chat a count is read from: the plan it holds and its last turns."""
    lines = [str(((memory or {}).get("user") or {}).get("plan") or "")]
    lines += [str(turn.get("user") or "") for turn in ((memory or {}).get("turns") or [])
              if isinstance(turn, dict)][-LOOK_BACK_FOR_A_MEAL:]
    return lines


def _the_chat_feeds_people(memory):
    """Whether this chat has said what the people are for: a meal, a cake, a party being given."""
    return any(A_MEAL_IN_THE_CHAT.search(line) for line in _the_chat_lines(memory))


# The words that make a number of people a table on the line that gives it: they are coming or
# coming over, they are for something, they were invited. "15 people at work" has none of them -
# "at" says where, not what the people are for - and that is the line the fence is for.
A_TABLE_CUE = re.compile(
    r"\b(?:people|persons?|guests?|adults?|heads?|folk|friends|kids|children)\b"
    r"[^.]{0,16}\b(?:coming|over|round)\b"
    r"|\b(?:for|having|expecting|feeding|catering for|cooking for|invited|inviting)\s+"
    r"(?:the\s+|just\s+|only\s+)?(?:" + GROUP_NUMBER + r")\b", re.I)


def _the_chat_sets_a_table(memory):
    """Whether this chat has a table for people at all: a meal said, a booking, or people coming."""
    lines = _the_chat_lines(memory)
    return any(A_MEAL_IN_THE_CHAT.search(line) or A_TABLE_BOOKED.search(line)
               or A_TABLE_CUE.search(line) for line in lines)


def _the_bare_people(said):
    """How many people a line says with no word for what they are for, or 0."""
    for match in BARE_PEOPLE.finditer(said):
        number = _said_number(match.group("n"))
        if number > 0:
            return number
    return 0


def _the_number_put_right(said, memory):
    """The number a line puts right, when the chat already holds the number at the table.

    "we booked a table for 6 on friday" then "make it 8": the second line has no noun for the
    count to hang on, so it is only a correction because the chat already has a number to
    correct. Nothing is read when the chat holds none - "make it 8" on its own is not a
    headcount - and nothing is read for the house they live in, which is a different number.
    """
    held = ((memory or {}).get("user") or {}).get("how_many")
    held_party = held.get(PARTY_THING) if isinstance(held, dict) else None
    if not isinstance(held_party, int) or held_party <= 0:
        return 0
    if ABOUT_THE_HOUSE.search(said):
        return 0
    if ONE_MORE.match(said):
        return held_party + 1
    if ONE_LESS.match(said):
        return held_party - 1 if held_party > 1 else 0
    for pattern in (CHANGED_BARE, NOW_THE_NUMBER):
        for match in pattern.finditer(said):
            number = _said_number(match.group("n"))
            if number > 0:
                return number
    return 0


# A figure for a thing the chat already counts, in whatever words the person says it. The readers
# above each read one shape of a change - a correction with a noun, a number put right with no
# noun, a group that grew - and between them they left out the plainest wording of all: the same
# thing said again with a different number in it ("its 5 nights now", "5 nights not 4", "we've
# got 3 people now"). So the rule is read where it lives instead: a statement that gives a figure,
# for a thing this chat already keeps a count of, is the new count. The wording only has to point
# at the thing - by naming it, or by "them"/"those" after the chat named it - and a question
# never moves a number.
A_FIGURE = re.compile(r"\b(?P<n>" + GROUP_NUMBER + r")\b", re.I)
# Words that make a line a change of what was said rather than a fresh remark. They are not
# required - "5 nights not 4" changes the number and so does "we've got 3 now" - but a bare
# figure with one of them beside it is a count of the thing in hand.
SAID_AS_A_CHANGE = re.compile(
    r"\b(?:actually|instead|now|sorry|wait|hold on|make (?:it|that)|change|put it at|no|nope|"
    r"correction|then|after all|not|still|only)\b", re.I)
POINTS_AT_THE_THING = re.compile(r"\bof (?:them|those|these|it)\b", re.I)
# The word in front of a figure that makes it a name rather than a count: "the bus is number 9"
# is the route, "its half 5" is the time, "room 12" and "platform 3" are where they are. Read as
# a count of the thing in hand, every one of them moved the nights a chat was planning - the bus
# number the person mentioned a turn after "we have 4 nights" answered "how many nights was it"
# with "You've got nine nights."
A_LABEL_IN_FRONT = frozenset("""number no nos num bus train flight room flat gate platform
seat table lane door channel code pin model version series episode chapter page line half
quarter past o'clock oclock platform route size step floor grade level class year""".split())
# The words that stand between a figure and the thing it counts without changing what it counts:
# "10 of us now", "5 of them", "4 nights please".
COUNTS_THE_THING_AFTER = frozenset("""of now then instead too as well please thanks again
still only just left to go more another""".split())
# A sentence that opens on one of these has no subject of its own, so its figure is the time or the
# weather until the line names what it counts.
A_DUMMY_SUBJECT = frozenset("""its it's it thats that's theres there's""".split())
# A figure that follows "<something> is" belongs to that something: "the bus is 44 now" is the
# route and "the room is 3" is the room, not the nights of the trip the chat is planning. The rule
# only looks at what stands in front of the copula, so a line with no subject of its own ("weve got
# 3 now", "make it 8") is left to the thing in hand.
A_COPULA = re.compile(r"\b(?P<subj>[a-z][a-z'-]*)\s+(?:is|are|was|were|be|being)\s*$", re.I)


def _forms_of(thing):
    """The words the person may say the thing with: its singular and its plural."""
    thing = str(thing or "")
    if not thing:
        return frozenset()
    forms = {thing, thing + "s", thing + "es"}
    for plural, single in IRREGULAR.items():
        if single == thing:
            forms.add(plural)
    return frozenset(forms)


def _the_figure_counts_the_thing(said, match, after_word, thing):
    """Whether the line says the figure is the count of `thing`, and not of something else.

    A figure in a line is the count of the thing in hand only when the line puts the two
    together. Everything else is a figure of its own: a name ("number 9"), a measurement ("20
    degrees"), a time ("its 2 now", "half 5"), a price. One rule, read here, because every
    shape of it was moving the count: the nights of a Rome trip became 9, then 5, then 2, and the
    ask that follows ("how many nights was it") gave back the bus number.
    """
    before = said[:match.start("n")].strip(string.punctuation + " ")
    front = before.split()[-1].lower().strip(string.punctuation) if before else ""
    if front in A_LABEL_IN_FRONT:
        return False
    subject = A_COPULA.search(before)
    if subject and subject.group("subj").lower() not in _forms_of(thing) \
            and subject.group("subj").lower() not in ("it", "there", "that", "this"):
        return False
    if after_word not in _forms_of(thing):
        # Nothing names the thing after the figure, so the line has to be about the thing already.
        # A sentence that opens on a dummy "it" is not: "its 2 now", "its gone 9 now" and "its
        # half 5 now" are the time, and "its 20 degrees now" the weather.
        first = said.split()[0].lower().strip(string.punctuation) if said.split() else ""
        if first in A_DUMMY_SUBJECT:
            return False
    if after_word in COUNTS_THE_THING_AFTER or not after_word:
        return True
    return after_word in _forms_of(thing)


def _the_lines(memory):
    """The person's own lines, oldest first, as the store keeps them."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    said = []
    for turn in turns if isinstance(turns, list) else ():
        line = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        if line.strip():
            said.append(line)
    return said


def _the_thing_in_hand(memory, held):
    """The thing the last numbered line named, when the chat keeps a count of it."""
    for line in reversed(_the_lines(memory)):
        for thing in _counted(line):
            if isinstance(held.get(thing), int):
                return thing
    return ""


# A number said beside the one that is wrong: "5 nights not 4", "three people, not eight",
# "make it 8 rather than 6". The figure in front of the word is the one that stands, so the line
# is read up to it. Read whole, "5 nights not 4" was filed as a count of a thing called "not".
WRONG_NUMBER_AFTER = re.compile(
    r"\W*\b(?:not|instead of|rather than|no longer|as opposed to)\b", re.I)


def _the_figure_that_stands(said):
    """The line up to the word that pushes a number aside, so the number that stands is read."""
    match = WRONG_NUMBER_AFTER.search(said)
    if not match:
        return said
    kept = said[:match.start()].strip()
    # Only when the part that stands holds a figure of its own: "not 4 nights, 5" is the other way
    # round, and reading up to "not" there would leave nothing.
    return kept if A_FIGURE.search(kept) else said


def _a_figure_for_a_thing_the_chat_counts(said, memory, already=()):
    """{thing: number} for a figure said again, with the thing this chat already counts.

    `already` is the counts the readers above found in this line. When they found one, the bare
    figure is not read again: "no, the 5 of us" is a group of five, and reading its figure a second
    time by way of the thing in hand filed it over the nights the chat was planning.
    """
    held = ((memory or {}).get("user") or {}).get("how_many")
    if not isinstance(held, dict) or not held:
        return {}
    if "?" in said or ASKING.match(said) or NOT_THE_COUNT.search(said):
        return {}
    said = _the_figure_that_stands(said)
    figures = [match.group("n") for match in A_FIGURE.finditer(said)]
    if len(figures) != 1:
        return {}  # two figures are a range or two things, and neither is "the" number
    number = _said_number(figures[0])
    if number <= 0:
        return {}
    named = [thing for thing in _counted(said) if thing in held]
    if named:
        thing = named[0]
    elif POINTS_AT_THE_THING.search(said) or SAID_AS_A_CHANGE.search(said):
        # A bare figure points at the thing in hand only when it is a figure of the same kind:
        # "its 20 degrees now" and "its 5 minutes now" carry a number and a change word, and
        # filing either over the nights a chat is planning would answer "how many nights" with
        # the weather.
        match = A_FIGURE.search(said)
        after = said[match.end("n"):].strip(string.punctuation + " ")
        word = after.split()[0].lower() if after else ""
        word = word.strip(string.punctuation)
        if already:
            return {}  # the line already says what its figure counts
        if word in NOT_A_THING or word in NOT_A_COUNT:
            return {}
        thing = _the_thing_in_hand(memory, held)
        if not _the_figure_counts_the_thing(said, match, word, thing):
            return {}
    else:
        return {}  # "8" on its own counts nothing until the chat says what of
    if not thing or held.get(thing) == number:
        return {}
    return {thing: number}


def observe(text, memory):
    """Keep how many of a thing the line says they have.

    "i have three brothers" -> memory["user"]["how_many"]["brother"] = 3. A count is a fact like
    any other, so it is filed where the store files facts, and it is the number that is new: a
    later line that changes it ("no, four brothers") files the new one.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return
    said = " ".join(text.split())
    if not said or ASKING.match(said):
        return
    counts = {}
    # How many bedrooms the place has is said in a shape of its own ("its a 3 bed house", "we
    # live in a 2-bed flat"), with no possession frame in it, so it is read from the line.
    beds = _beds(said)
    if beds:
        counts["bedroom"] = beds
    group = _the_group(said)
    if group:
        counts[GROUP] = group
    party = _the_party(said)
    if party:
        counts[PARTY_THING] = party
    elif _the_number_put_right(said, memory):
        counts[PARTY_THING] = _the_number_put_right(said, memory)
    elif _the_chat_feeds_people(memory) and _the_bare_people(said):
        counts[PARTY_THING] = _the_bare_people(said)
    elif group and CHANGED.search(said) and not ABOUT_THE_HOUSE.search(said):
        # The group size is the table's when the line changes it: "one more is coming so theres 10
        # of us now" after "a roast for 8 people" makes ten people to cook for.
        held_party = ((memory.get("user") or {}).get("how_many") or {}).get(PARTY_THING)
        if isinstance(held_party, int):
            counts[PARTY_THING] = group
    put_right = CORRECTED.match(said)
    if put_right:
        counts.update(_counted(put_right.group(1)))
    for pattern in (THEY_HAVE, MY_THREE):
        for match in pattern.finditer(said):
            rest = match.group("rest")
            for thing, number in _counted(rest).items():
                counts.setdefault(thing, number)
    # Last, and one rule for every wording: a figure said again for a thing the chat counts is
    # the new count. The readers above each cover a shape of it; this covers the rest, without
    # them having to know the words a person chose.
    for thing, number in _a_figure_for_a_thing_the_chat_counts(said, memory, counts).items():
        counts.setdefault(thing, number)
    if not counts:
        return
    user = memory.get("user")
    if not isinstance(user, dict):
        user = memory["user"] = {}
    held = user.get("how_many")
    if not isinstance(held, dict):
        held = {}
    for thing, number in counts.items():
        if held.get(thing) != number:
            held[thing] = number
    user["how_many"] = held


# "how many brothers do i have", "how many brothers have i got", "how many brothers", "how many
# brothers and sisters do i have": the ask names the thing and asks for the number of it.
# The thing asked about is read the way it was filed: the head of the phrase, so "how many missed
# calls do i have" asks about the calls and not about "missed".
HOW_MANY = re.compile(
    r"\bhow many (?P<what>[a-z-]+(?:\s+[a-z-]+){0,2}?)"
    r"(?:\s+(?:and|n|nd)\s+(?P<also>[a-z-]+(?:\s+[a-z-]+){0,2}?))?\s*"
    r"(?:(?:do|did) (?:i|we) (?:have|got|own)|(?:have|had) (?:i|we) got|(?:do|did) (?:i|we) own|"
    r"are there|have we|again|then|now)?\s*[?.!]*$", re.I)
# A count that is a wish or a decision is not a count of what they have: "how many brothers
# should i have", "how many cars can i have".
NOT_THE_COUNT = re.compile(r"\b(?:should|could|would|might|may|can|will)\b", re.I)


def answer(text, memory):
    """The number of a thing they asked the count of, or None when the store holds no count."""
    if not isinstance(text, str) or not memory.get("user"):
        return None
    held = memory["user"].get("how_many")
    if not isinstance(held, dict) or not held:
        return None
    low = " ".join(str(text).lower().split())
    if NOT_THE_COUNT.search(low):
        return None
    of_you = bool(GROUP_ASK_YOU.search(low))
    if GROUP_ASK.search(low) or BARE_GROUP_ASK.search(low) or of_you:
        number = held.get(GROUP)
        if isinstance(number, int) and number > 0:
            return _the_group_said_back(number)
        if of_you:
            # The table they are cooking for is not how many live with them, so the group being
            # empty here is the whole answer: nothing else in the store holds it.
            return None
        # The chat said how many were coming ("theres 8 of us coming on sunday") and not how many
        # live here: that is the only size of the group the chat holds, so it is the answer to
        # "how many of us is it again", which was otherwise handed a search suggestion. An ask
        # that names the group itself cannot be asking about any other number.
        number = held.get(PARTY_THING)
        if isinstance(number, int) and number > 0:
            # "how many of us" is asked of the group and said back that way; "how many people did
            # i say" is asked of the people at the table and keeps its own noun.
            return _the_party_said_back(number, low, memory, of_the_group="of us" in low)
        # "how many people" is the household when they gave its size, and the table they are
        # cooking for when they gave that: the same words ask for whichever number the chat has.
    if PARTY_ASK.search(low):
        number = held.get(PARTY_THING)
        if isinstance(number, int) and number > 0 and _the_chat_sets_a_table(memory):
            # A number of people is the table only in a chat that has said what the people are
            # for, which is the fence `observe` already keeps when it files a bare headcount.
            # Without it on the reading side "i met 15 people at work today" then "how many am i
            # feeding for" answered "You said 15 people." - a table the person never set, said
            # back to them as their own fact. A chat that named a roast, a tea or a party still
            # answers, because there the people were the table.
            return _the_party_said_back(number, low, memory)
        # The chat set the number as a group ("so theres 10 of us now") and never as a table: an
        # ask that points back at it is answered from the group, and a fresh ask is not, because
        # "how many people are coming" with only a household on the store is a new question.
        number = held.get(GROUP)
        if isinstance(number, int) and number > 0 and POINTS_AT_A_NUMBER.search(low):
            return _the_party_said_back(number, low, memory, of_the_group=True)
        return None
    if BARE_COUNT_ASK.search(low):
        # The chat's own number, said back rather than handed back as a figure from the last
        # answer: "how many was it" in a chat that gave eight people for dinner was answered
        # "4 to 5 hours." The table they set comes before the household they live in, because a
        # bare count in a chat that is cooking for people is the number at the table.
        for thing, of_the_group in ((PARTY_THING, False), (GROUP, True)):
            number = held.get(thing)
            if isinstance(number, int) and number > 0:
                return _the_party_said_back(number, low, memory, of_the_group=of_the_group)
        return None
    match = HOW_MANY.search(" " + low)
    if not match:
        return None
    asked = [_thing_of(match.group("what"))]
    if match.group("also"):
        asked.append(_thing_of(match.group("also")))
    asked = [thing for thing in asked if thing]
    if not asked:
        return None
    counted = [(thing, held[thing]) for thing in asked if isinstance(held.get(thing), int)]
    if not counted:
        return None
    parts = []
    for thing, number in counted:
        many = thing if number == 1 else thing + "s"
        if thing in IRREGULAR.values() and number != 1:
            many = [plural for plural, one in IRREGULAR.items() if one == thing][0]
        parts.append(_many(number) + " " + many)
    said = parts[0] if len(parts) == 1 else " and ".join(parts[:-1]) + " and " + parts[-1]
    if len(counted) < len(asked):
        # They asked about two things and only one was ever counted: say what is kept, and say
        # plainly what is not, rather than answering the half of it that happens to be there.
        missing = [thing for thing in asked if not isinstance(held.get(thing), int)]
        return ("You've got " + said + " - I've not been told how many " + missing[0] + "s you "
                "have.")
    return "You've got " + said + "."


def _the_chat_books(memory):
    """Whether the plan the chat is on is a booking, so a table is the thing to say back."""
    user = (memory or {}).get("user") or {}
    plans = list(user.get("plans") or [])
    if user.get("plan"):
        plans.append(user.get("plan"))
    return any(re.search(r"\b(?:book|booked|booking|reserv\w*|table)\b", str(plan).lower())
               for plan in plans)


def _the_party_said_back(number, low, memory=None, of_the_group=False):
    """The number of people they are cooking for, said back in their own terms.

    "and how many people" eight turns into a roast is answered "Eight people, you said." - the
    number belongs to the plan the chat is on, so nothing is asked for again. The noun follows the
    ask ("how many guests" gets "Eight guests"), and a chat that asks twice gets a second wording
    rather than the same sentence twice.
    """
    many = _many(number)
    if of_the_group:
        plain = "You said " + many + " of you."
        said = {str(turn.get("bot") or "") for turn in (memory or {}).get("turns") or []
                if isinstance(turn, dict)}
        return "Still " + many + " of you." if plain in said else plain
    if "guest" in low:
        noun = "guest" if number == 1 else "guests"
    elif "adult" in low:
        noun = "adult" if number == 1 else "adults"
    elif ("book" in low or "table" in low or "reserv" in low) and _the_chat_books(memory):
        # "how many did i book for" is answered with the table, not with the people: the number
        # they want back is the one on the booking. The wording is not enough on its own - a chat
        # that set a headcount for a dinner and never booked anything is answered with the people.
        return "The table is for " + many + "."
    else:
        noun = "person" if number == 1 else "people"
    plain = "You said " + many + " " + noun + "."
    said = {str(turn.get("bot") or "") for turn in (memory or {}).get("turns") or []
            if isinstance(turn, dict)}
    if plain in said:
        return "Still " + many + " " + noun + "."
    return plain


def _the_group_said_back(number):
    """The size of the group, said the way a person would say it back."""
    if number == 1:
        return "Just you, then."
    if number == 2:
        return "The two of you, then."
    return "There are " + _many(number) + " of you."
