"""Plans: the jobs with a date on them, and the order to do them in.

The answers lane owns this domain. People don't ask about "project management", they ask
"where do I even start" about something with a deadline: a house move, a party, a wedding,
a kitchen, a baby, a holiday. The useful answer is always the same shape — what to settle
first, what to do how many weeks out, and the one thing that catches everyone out — so the
entries here are keyed by the event (moving house, a kids' party, a wedding, a renovation,
a new baby, a holiday, a clear-out, a dinner party, Christmas, a road trip) and the asking
part of the line (plan, start, organise, how much, what first).

Nothing here repeats a domain's own facts: the cooking stays in cooking.py, the packing
list in travel.py, and the moving-day van in home.py. This domain only holds the order and
the timing, which is what nobody has when they ask.
"""
import re

from ..compose import pick, said_again
from ..compose.repair import amends_to, line_of, owns_the_deed
from .cooking import ANNOUNCED_DISH, RECIPES  # one table of recipes, read here rather than copied
from .dishes import a_dish_is_already_the_plan
from .lookup import A_HOURS_ASK, A_WEATHER_ASK, PEOPLE_FEMALE, PEOPLE_MALE, entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("home-and-diy", "family-and-parenting", "geography-and-travel")

# Every entry here answers a question, not a statement. "I'm Jess, and I'm planning a picnic for
# my daughter's 7th birthday" is a person telling you about their week; the birthday-party plan
# is not an answer to it, so the entry waits for a line that actually asks.
PLAN_ASK = ("how", "what", "whats", "what's", "where", "when", "any", "help", "should", "could",
            "would", "can i", "can you", "much", "idea", "ideas", "tips", "advice", "start",
            "best way",
            # Stating the plan is asking for the plan. "how do i plan a birthday party" is
            # answered (count the people first, 8 to 12 at home, 30 to 40 at most in a house),
            # and the same question said as a statement - "im planning a party for 20 people",
            # "im organising a surprise party for my husband" - was "Good. What's the first step
            # you're unsure about?" The plan verb is the ask.
            "planning", "plan", "plans", "organising", "organizing", "arranging", "throwing",
            "thrown", "hosting", "sorting out", "putting together", "getting ready for")

# "how many kids do i have" is a count of the person's own household, not a party to plan, and a
# children's party answer to it is a plan nobody asked for. The row catches the line because "how
# many kids" and "how many children" are listed there as ways of asking how many to invite; what
# tells the two apart is the possessive ask - "do i have", "have i got", "do we have" - which
# turns the line into a question about the family. Any "how many" row can be reached this way, so
# the test is here and the party rows ask it.
_OWN_COUNT = re.compile(
    r"\bhow many (?:\w+ ){0,3}(?:do|does|did) (?:i|we) (?:have|got)\b"
    r"|\bhow many (?:\w+ ){0,3}have (?:i|we) got\b")


def _not_a_count_of_their_own(understood):
    """False when the line counts what the person has rather than asking how many to invite.

    Read on the line as typed, not on the words the memory of the chat lends it: "how many
    children do we have" after a party question was read with the party's words added and reached
    the party plan again.
    """
    text = understood.get("text")
    if not isinstance(text, str) or not text:
        words = understood.get("words") or ()
        text = " ".join(w for w in words if isinstance(w, str))
    return not _OWN_COUNT.search(" " + text.lower() + " ")

# A birthday question is often a date question, and a date is not a do: "when is my mums
# birthday", "when is her birthday" and "what date is my dads birthday" were told the headcount
# and the price of a buffet. The row's second group holds "when" because "when should i send the
# invitations" is planning, so the when alone cannot tell the two apart.
_A_DATE_ASK = re.compile(r"\b(?:when|what date|which date|what day)\b")

# ... and the words that make it a do again, so "when should i send the invitations" and "when do
# i need to book the venue" keep the party. A line that names one of these is planning.
_A_DO = re.compile(r"\b(?:party|parties|invitations?|invites?|guests?|venue|plan|plans|planning|"
                   r"organis\w*|organiz\w*|menu|buffet|food|catering|decorations?|cake|games|"
                   r"themes?|book|booking)\b")


def _not_a_date_question(understood):
    """False when the line asks for the date of a birthday rather than for a party.

    Read on the line as typed, for the same reason _not_a_count_of_their_own is: the memory of a
    party chat lends the row its own words back.
    """
    text = understood.get("text")
    if not isinstance(text, str) or not text:
        words = understood.get("words") or ()
        text = " ".join(w for w in words if isinstance(w, str))
    line = " " + text.lower() + " "
    return not (_A_DATE_ASK.search(line) and not _A_DO.search(line))


# A line that asks what happened is about the time that has gone, not a request for ideas: "today"
# and "anything"/"what" sit between them, so "what happened today" and "did anything good happen
# today" were handed the free-weekend card - two plans, a walk and a market - for a question that
# has no plan in it. Only the frames that ask about the past are read this way; "whats happening
# this weekend" is still a plan and keeps the row.
_WHAT_HAPPENED = re.compile(
    r"\b(?:did|has|have)\s+(?:anything|something|much|any good)\b"
    r"|\bwhat(?:'s|s| is)?\s+happened\b"
    r"|\banything (?:good |nice |interesting )?happen\b", re.I)


def _asks_for_ideas(understood):
    """False when the line asks what happened rather than for something to do."""
    text = understood.get("text")
    if not isinstance(text, str) or not text:
        words = understood.get("words") or ()
        text = " ".join(w for w in words if isinstance(w, str))
    return not _WHAT_HAPPENED.search(" " + text.lower() + " ")


# Both readings of the line have to hold: the weekend has to be free of the medicine and the
# ill plan that main's guard fences out, and the line has to be an ask for ideas rather than
# a question about the day that has gone. Read as an `and` here so the row keeps answering
# neither of the cases the other guard was written for.
def _the_free_weekend_fits_and_is_asked(understood):
    return _free_weekend_fits(understood) and _asks_for_ideas(understood)


# A clock question about a named thing is not an ask for ideas: "what time is sunset today" was
# two plans in the diary - one thing out of the house, one job, one person - because "today" is in
# this row's key and "what" is the rest of it. The time of a thing that happens is that thing's
# answer ("the exact time depends on where you are"), and the plan answers a question nobody
# asked. The ask has to name something as the subject; "what time should i set my alarm" is a
# how-do-i and keeps whatever card knows it.
_ASKS_A_CLOCK = re.compile(
    r"\bwhat time (?:is|are|was|were|do|does|did|will|would)\b"
    r"|\bwhen (?:is|are|was|were|do|does|did|will) (?!i\b|we\b|you\b)", re.I)


# A present for the person is the gift row's answer, not a party: "what should i get my dad for his
# 70th" reached the party because an ordinal is a key, and the avoid list held "get her" and
# "get him" but not the person named in the line. Every person noun gets the verb, so a new one
# added to the list is covered without anyone remembering this row.
_PEOPLE = tuple(w for w in PEOPLE_MALE + PEOPLE_FEMALE
                if w not in ("he", "him", "his", "she", "her", "hers", "his"))
_A_PRESENT_FOR = tuple("%s my %s" % (verb, who)
                       # "give" is here because it always carries its person: "what can i give my
                       # daughter for her birthday" was the children's party, and no present row
                       # can catch "give my ..." without a person on the far side of it.
                       for verb in ("get", "gets", "getting", "got", "buy", "buys", "buying",
                                    "bought", "give", "gives", "giving", "gave")
                       for who in _PEOPLE)


def _not_a_deed_of_their_own(reading):
    """False when the line reports something the person did to somebody: that is a repair.

    "i forgot my mums birthday, what do i do" asks how to put it right, and the party plan -
    guest count, buffet budget, invitations three weeks out - is a plan for a day that has gone.
    "i didnt get my mum anything for her birthday" is the same turn, and it was reading as a
    birthday still to plan as well (bot/compose/repair.py). An ask to put it right names no deed
    of its own ("how do i make it up to my mum"), and in a chat that has just said the birthday
    was missed it is the same turn again: the plan for the party took it.
    """
    return not (owns_the_deed(reading) or amends_to(line_of(reading)))

# "what paperwork do i need to get married" and "register office wedding what do i need" are not
# the budget question, and a budget answer to them opens on the guest list: the paper trail is its
# own job with its own deadline, so the row answers the shape that was asked instead of always the
# cost.
_DECLUTTER_ASK = ("clear out", "clearing out", "clearout", "clear the clutter", "clear clutter",
                  "declutter", "too much stuff", "too much clutter", "fed up with", "sick of",
                  "rid of everything", "rid of it all", "rid of the lot", "rid of all of it")

# The places a clear-out happens in, and the piles it happens to. One of these has to be in the
# line, or the job has to be named on its own ("what should i get rid of", "i want a clear out").
_DECLUTTER_ROOM = ("room", "rooms", "house", "home", "flat", "place", "garage", "loft", "shed",
                   "attic", "wardrobe", "wardrobes", "cupboard", "cupboards", "closet", "kitchen",
                   "bedroom", "bedrooms", "cellar", "spare room", "drawer", "drawers", "shelves",
                   "hall", "hallway", "landing", "under the stairs", "cabinets", "units",
                   "car boot", "box room", "study", "desk", "filing")
_DECLUTTER_STUFF = ("stuff", "clutter", "junk", "rubbish", "things", "mess", "gear", "bits",
                    "crap", "tat", "odds and ends", "it all", "everything")

# "how do i get rid of" with nothing named after it is the clear-out question; with a thing after
# it, it is that thing's question ("how do i get rid of a verruca", "... the limescale on the
# kettle"), and the things it is said about cannot be listed.
_BARE_RID = re.compile(r"\bget rid of\s*(?:$|[.?!])")
_JOB_NAMED = ("clear out", "clearing out", "clearout", "declutter", "clear the clutter",
              "clear clutter", "big tidy", "tidy up the house", "tidy my house",
              "tidy up my house", "sort the house out", "sort the house")
_TOO_MUCH = re.compile(r"\btoo much (?:stuff|clutter|junk|rubbish|things|mess|gear|crap|tat)\b")


def _declutter_fits(understood):
    """True when the line names a room or a pile to clear, or asks the job with nothing named.

    The row keys the plainest ways of saying a clear-out, and most of them ("rid of", "mess",
    "stuff", "too much") are also how a wart, a limescale stain or an exclamation is said.
    """
    text = understood.get("clean") or understood.get("text") or ""
    if not isinstance(text, str):
        text = " ".join(w for w in (understood.get("words") or ()) if isinstance(w, str))
    clean = " " + " ".join(text.split()) + " "
    if _BARE_RID.search(clean):
        return True
    if any(" " + job + " " in clean for job in _JOB_NAMED):
        return True
    if _TOO_MUCH.search(clean):
        return True
    names_room = any(" " + room + " " in clean for room in _DECLUTTER_ROOM)
    names_pile = any(" " + pile + " " in clean for pile in _DECLUTTER_STUFF)
    return bool(names_room or names_pile)

_WEDDING_PAPERS = ("paperwork", "notice", "registrar", "register office", "legal", "admin",
                   "papers", "documents", "bring",
                   # "how do i get married" asks for the process, not the guest list: the
                   # how-to put to the subject is the paper trail in a question's clothing,
                   # and the money words below still take the cheap ones to the budget answer.
                   "how do i get married", "how do we get married", "how to get married",
                   "how do you get married", "how do i marry", "how do we marry",
                   "how do i arrange", "how does it work",
                   "licence", "license", "certificate", "witness", "witnesses", "need to do",
                   "what do i need", "what do we need", "whats needed", "what's needed",
                   "need before", "before we get married", "getting married what",
                   # "notice of marriage" and "do we need to give notice to marry" name the
                   # paperwork with no question word in them, so the row carries its own ask
                   # words below as well as PLAN_ASK
                   "give notice", "notice to marry", "give notice to marry", "to marry")
# The paperwork lines are questions without a question word: "notice of marriage" and
# "do we need to give notice to marry" name the thing and stop.
_WEDDING_ASK = ("notice", "paperwork", "registrar", "register office", "need to", "to marry",
                "witness", "witnesses")
# Two questions about a wedding plan that the plan card had no answer for, and that other rows
# took with a shrug or with the wrong card: "how many guests for a wedding" was answered with
# advice on booking a hotel room, "how many guests should we have at our wedding" with a menu to
# cook twice, and "how far ahead should we book the venue" with "times like that I can't see".
_WEDDING_COUNT = re.compile(r"how many (?:guests|people|to invite|should we (?:invite|have))"
                            r"|number of guests|how big|guest count|size of the wedding")
_WEDDING_WHEN = ("far ahead", "how early", "how long before", "lead time", "how soon",
                 "when should we book", "when do we book", "when to book", "when should i book",
                 "book the venue", "book a venue", "book the photographer", "book a photographer",
                 "book the registrar", "book the caterer", "book the church")
_WEDDING_GUESTS = (
    "There is no right number, only a price: each guest costs roughly \u00a3100 to \u00a3150 at "
    "a catered wedding, so 100 guests is a \u00a310,000 to \u00a315,000 decision. Write two "
    "lists - the people you would be sad not to see, then everyone else - and cut from the "
    "second until the money works. The room is the other hard limit, because a seated meal needs "
    "about 1.2 square metres a head, and children count towards both.")
_WEDDING_LEAD_TIME = (
    "Venue first: a year to 18 months ahead for a Saturday in summer, and six months is enough "
    "for a winter Friday or a village hall. The registrar or celebrant as soon as the date is "
    "fixed, the photographer nine to twelve months out, the caterer six to nine, the cake and "
    "the outfit four to six. Ask the venue for its own notice period before you fall for a date, "
    "because a barn that has to give notice to the council can block a summer Saturday.")

_WEDDING_MONEY = ("cost", "costs", "much", "budget", "cheap", "cheapest", "afford", "price",
                  "save", "saving", "spend", "quotes", "quote", "\u00a3")


# A topic that names nothing the pool could be about. "What should i try at work" is the work
# domain's line and "something new to try with chicken" is the kitchen's; a line with no topic,
# or one read as small talk or an opinion, is the one this pool can answer.
VAGUE_TOPICS = (None, "", "small-talk", "opinions", "creative")

# The ask half of a "something to try" line. It is the shape of the request, not a subject.
TRY_ONCE_ASK = ("what", "whats", "what's", "should", "suggest", "recommend", "tell", "give",
                "idea", "ideas", "anything", "something", "one thing", "surprise", "want",
                "need", "any", "name")

# One thing a person might do once, in the bot's own words: the thing first, then the reason or
# the first step that makes it possible. Twelve words of advice nobody asked for is the failure
# here; naming one real thing and stopping is the answer.
TRY_ONCE = (
    "Learn to make one loaf of bread by hand: flour, water, yeast, salt, an hour of rising, and "
    "the house does the rest. The first one is always a bit wonky and nobody minds.",
    "Swim outside once - a lake, a lido, the sea in October - with a friend and a towel waiting. "
    "Twenty seconds is enough to know you did it.",
    "See a band you have never heard of in a small room on a week night. A cheap ticket, no "
    "expectations, and it is the best way to find music you keep.",
    "Take one night away on your own: a train, a cheap room, a book. It is a different kind of "
    "trip from a holiday with people, and easier than it sounds.",
    "Watch the sunrise on purpose once: check the time, set an alarm, take a flask. One early "
    "start buys you a morning you will talk about for years.",
    "Learn to change a tyre and check your oil before you have to. Ten minutes of practice on "
    "your own drive beats an hour on a hard shoulder in the rain.",
    "Eat in a restaurant by yourself, with a book, once. Nobody is looking, and it is the most "
    "peaceful hour you can buy for the price of a lunch.",
    "Post a real letter to somebody who will not expect it - a grandparent, an old teacher, a "
    "friend who moved away. It lands differently from a message.",
    "Plant something you can eat and keep it alive to the plate. Herbs on a windowsill count, and "
    "one tomato plant teaches you more than a book does.",
    "Go to a match of a sport you know nothing about and sit with the crowd. Someone will explain "
    "the rules before half time, and the noise is the point.",
    "Give a morning to something local - a food bank, a park clean-up, a repair cafe. One morning "
    "with no commitment afterwards, and you will meet people you would never otherwise meet.",
    "Cook the same dish once a week until you can do it without the recipe. Everyone should own "
    "one dinner, and six goes is usually enough.",
    "Draw something badly on purpose, and keep it. Being a beginner at something for an afternoon "
    "is good for you.",
    "Catch a train to a town an hour away with no plan for the day: walk it, have lunch, come "
    "home. The having-no-plan is the good bit.",
    "Take a class where you make something with your hands - pottery, woodwork, knitting, "
    "welding. A thing that stays made is a rare sort of satisfaction.",
    "Sleep outside once: a tent in a friend's garden, a campsite, a bothy. You will remember the "
    "night, not how well you slept.",
    "Learn ten words of a language before you go somewhere that speaks it. Shopkeepers forgive a "
    "lot for one honest attempt.",
    "Ask an older relative to tell you about their childhood and record it on your phone. It is "
    "the cheapest history you will ever collect.",
)

# The ask for a second one: "give me another", "one more", "anything else to try". These
# carry no subject either, so the pool can only answer them from what it said last.
TRY_ONCE_MORE = (("another one", "one more", "another idea", "one more idea", "another thing",
                  "something else to try", "anything else to try", "a different one",
                  "more ideas", "give me more", "another suggestion"),
                 ("give", "one", "more", "another", "try", "idea", "ideas", "else",
                  "anything", "something", "different"))


def _try_once(memory, understood):
    """One thing worth trying once, or None when the line is about a subject of its own.

    The pool holds no facts about anything in particular, so it can only answer a line that
    asks for a suggestion and nothing more. A line that names a subject - "something new to try
    with chicken", "something new to try at the gym" - is a question about that subject, and
    the module that knows about it should take the turn rather than this pool.
    """
    if (understood or {}).get("subject"):
        return None
    if (understood or {}).get("topic") not in VAGUE_TOPICS:
        return None
    return pick(TRY_ONCE, memory, _words_of(understood))


def _try_once_more(memory, understood):
    """Another thing to try, when the last reply was one - None for every other line.

    "Give me another one" is the commonest thing said to this pool, and it names nothing at
    all: the only way to read it is from what the bot just said. So the row takes the turn only
    when the last reply was one of these, and the rest of the time it steps back and lets the
    line be whatever else it was about.
    """
    turns = memory.get("turns") or []
    last = turns[-1].get("bot") if turns and isinstance(turns[-1], dict) else ""
    if said_again(last) not in {said_again(one) for one in TRY_ONCE}:
        return None
    if (understood or {}).get("subject"):
        return None
    return pick(TRY_ONCE, memory, _words_of(understood))



def _wedding_plan(memory, understood):
    line = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    # When to book comes before the paperwork, because "how far ahead should we book the
    # registrar" names the registrar and asks about the calendar.
    if any(word in line for word in _WEDDING_WHEN):
        return _WEDDING_LEAD_TIME
    if any(word in line for word in _WEDDING_PAPERS) and not any(
            word in line for word in _WEDDING_MONEY):
        return ("Give notice first: you each do it at your local register office at least 29 days "
                "before the wedding (in Scotland a marriage notice to the registrar), with a "
                "passport or birth certificate and proof of address. Book the venue and the "
                "registrar's slot, and find two witnesses. The 29 days is a legal minimum, not a "
                "booking window, so do not leave it late.")
    if _WEDDING_COUNT.search(line):
        return _WEDDING_GUESTS
    return ("Guest list first, because it sets the cost of everything else: the venue, the food and "
            "the drink are about 60% of a wedding, and halving the guest list roughly halves the "
            "bill. Book the venue and the registrar next (a year ahead for a Saturday), then the "
            "photographer, and keep 10% back for what you forgot.")

# --- the free weekend ----------------------------------------------------
# "What should I do this weekend", "any ideas for Saturday", "what can I do tonight": the
# free time is the subject and the ask is for ideas, so the key is the named free block plus
# the asking words. Nothing else here wanted these lines, and the bot had nothing to say.
FREE_TIME = ("weekend", "weekends", "this weekend", "next weekend", "long weekend",
             "saturday", "sundays", "on saturday", "on sunday", "day off", "bank holiday",
             "tonight", "this evening", "free evening", "after work", "free afternoon",
             # The evening said as when the working day ends, which is how people write it:
             # "what should i do when i get home from work" and "any ideas for when i finish
             # work" carry the block and no other word for it, and both got a search hedge.
             "home from work", "get home from work", "back from work", "from work",
             "when i get home", "when i get in", "finish work", "finished work",
             "leave work", "left work", "got home from work",
             "this afternoon", "afternoon off", "free day", "nothing planned",
             # a weekday evening said in the plural is the same free block: "what should i do with my
             # evenings" and "how do i fill my evenings" were a search hedge, and the row never saw
             # them because this key wanted "this evening" or "after work".
             "evenings", "my evenings", "weekday evenings",
             # A week off is a free block of the same kind, and a person who says one is asking
             # the same question: "i have a week off and no idea what to do" had no answer of
             # its own and the words "a week" were read by the savings-rate row, which worked
             # out an annuity, and by the meal-plan row, which planned a week of dinners.
             "week off", "weeks off", "week off work", "days off", "few days off",
             "time off", "time to myself", "days to myself",
             # The same week said by its date instead of by the word: "i am off next week what
             # should i do" is the week-off plan and was a search hedge.
             "off next week", "off for a week", "off all week", "whole week off", "week free",
             "a week free", "week at home", "week to myself", "off work for a week",
             "off work next week",
             # the same blocks said as a fact rather than as "a week off": "i have next week
             # off work", "i have a few days off next month" and `i have nothing planned this
             # weekend` are free time in the line and were an echo or the leave script.
             "next week off", "next week off work", "week off next month", "a few days off",
             "few days off", "days off next month", "off for a few days")
FREE_TIME_ASK = ("what should i do", "what can i do", "what do i do", "what to do",
                 "any ideas", "ideas for", "any suggestions", "suggestions for",
                 "something to do", "anything to do", "what shall i do", "where should i go",
                 "where can i go", "whats on", "what's on", "big plans",
                 # "i have a week off and nothing planned" and "i have a week off in the autumn
                 # any tips" are the same ask as "what should i do": a free block with nothing
                 # in it, said as a fact or as a request for tips, and both got an echo back.
                 "nothing planned", "nothing on", "any tips", "tips", "advice",
                 "suggestions", "what do you suggest", "plan it", "help me plan",
                 # a few days off, said as a fact, is the same question as "what should i do":
                 # the ask group is what stands this row up, and without these the row never saw
                 # "i have a few days off next month".
                 # A week of work leave is not here: "im off work next week" and "i have next
                 # week off work" state the time and ask nothing, and work.leave-plan answers
                 # them with the rota, the out of office and the question about the time itself.
                 "a few days off", "few days off", "days off next month", "week off next month",
                 # and the block stated with nothing asked: "i have the day off on friday" and
                 # "i have a long weekend free" were echoed back, because the row wants one of
                 # the asking words and a statement carries none of them.
                 "i have the day off", "i have a day off", "have the day off", "day off on",
                 # "got the day off" is the same block of free time said with the other verb, and
                 # it was answered "Bye for now!" by the small talk (every word of it is a
                 # goodbye word) and then "How was it, overall?" - a farewell and a post-mortem
                 # for a day the person had not spent yet.
                 "got the day off", "got a day off",
                 "day off tomorrow", "i have a long weekend", "long weekend free",
                 # A run of days off said as a fact is the same free block, and it had no answer
                 # of any kind: "i have 3 days off next week" was read as an event coming up and
                 # asked "How ready do you feel for it?", and "i have three days off" got "3 days
                 # is a while. Is it going the way you want?". The number is counted into the
                 # shape of the reply, so the key and the ask take the run of days whichever way
                 # it is written: a digit, a word, "a few" or "a couple of".
                 "days off next week", "days off next month", "days off this week",
                 "days off at the end of", "i have days off", "have days off", "got days off",
                 "days holiday", "days free next week", "days free next month",
                 "weekend free", "i have days off", "i have the weekend", "the weekend to myself",
                 # a week off with the season in it, or with what the person does not have in it,
                 # asks what to do with the time as plainly as "what should i do": "i have three
                 # weeks off in the summer", "a week off with no plans" and "how do i use a week
                 # off well" were given an echo, the request script and a search hedge.
                 "in the summer", "in summer", "in the winter", "in winter", "in the spring",
                 "in spring", "this summer", "this winter", "no plans", "nothing to do with it",
                 "use a week off", "use my week off", "week off well", "make the most of",
                 # ivory-kettle's other half: "how should i spend a week off", "how do i plan a
                 # week off" and "how do i use a week off to sort my flat out" carry the free
                 # block and the intent but none of the asking words above.
                 "plan a week off", "plan my week off", "plan the week off",
                 "spend a week off", "spend my week off", "spend the week off",
                 "how do i use", "how do i plan", "how should i spend", "sort my", "sort out")

DAY_PLAN = (
    "Put two things in the afternoon and give each a time: one that gets you out (a walk you "
    "have not done, a park, the library) and one you keep putting off that takes an hour. A free "
    "afternoon with no time on it is what dissolves into the phone.")

# A whole day off is not an afternoon: the two-things-in-the-afternoon shape is too small for
# it, and the person who says "what should i do with my day off" has a full day to fill.
DAY_OFF_PLAN = (
    "Treat it as a small Saturday: one thing out of the house (a walk you have not done, a "
    "market, a museum or gallery - most are free), one job you keep putting off that takes an "
    "hour, and one person to see. Put times on the first two the night before; a free day goes "
    "in small pieces when nothing is decided.")

# The evening said as plain words and as when the working day ends. One list, so the row that
# chooses the evening plan and the block that says the line has an evening in it cannot drift:
# "what should i do when i get home from work" had the evening in FREE_TIME and the weekend
# plan was chosen for it, because this branch knew "after work" and not "from work".
_THE_EVENING = ("tonight", "this evening", "free evening", "after work", "evening", "evenings",
                "home from work", "get home from work", "back from work", "from work",
                "when i get home", "when i get in", "finish work", "finished work",
                "leave work", "left work", "got home from work")

EVENING_PLAN = (
    "Give the evening a shape rather than waiting for an idea: one thing you will actually "
    "do at 8pm (a film you have been meaning to watch, a walk before it gets dark, a call to "
    "someone you like), tea that takes a bit of effort, and the phone in another room for the "
    "first hour. A free evening feels long when nothing is decided and short when one thing is.")

WEEKEND_PLAN = (
    "Three things, one each: something out of the house (a walk you have not done, a park, the "
    "library, a free museum), one job you keep putting off but that takes an hour (the drawer, "
    "the bike, the photos), and one thing with a person - a call, a walk with someone, a coffee. "
    "Put the outdoor one on the better day and keep Sunday evening free, or the weekend ends "
    "in a rush and feels like it never happened.")

# A week off is not seven weekends: the useful shape is one thing worth doing and days around
# it, because a week with nothing decided goes by in small pieces. It is also long enough to
# leave the house for, so the two or three nights away come first when the person has the time.
WEEK_OFF = ("week off", "weeks off", "week off work", "time off", "time to myself",
            "days to myself", "off next week", "off for a week", "off all week",
            "whole week off", "week free", "a week free", "week at home", "week to myself",
            "off work for a week", "off for the week", "off work next week")

WEEK_PLAN = (
    "Put a couple of nights away in the middle of the week and keep the first and last days "
    "free: somewhere two or three hours away by train is enough, and going Tuesday to Thursday "
    "costs less than the weekend. Fill the other days a day at a time - one thing out of the "
    "house, one job you keep putting off - and a week off stops slipping past unnoticed.")

# The season changes what a week at home looks like, and the line names it often enough to use
# it: an August week is planned round the heat, a January one round the dark.
SUMMER_WEEK = ("In summer, put the outdoors before ten or after five and keep the middle of the "
               "day for the job you keep putting off, so the heat sets the day instead of you.")
WINTER_WEEK = ("In winter, plan round the dark: the walk or the market at midday, and the "
               "cinema, the museum and the long cook for the evenings.")

# A week off with no money in it opens on the two nights away, which is the first thing the person
# cannot do. The same week planned from the free end is the answer they asked for.
WEEK_PLAN_SKINT = (
    "Start with the days that cost nothing: the walk you have not done, the library, a market, a "
    "park with a flask and a sandwich. Put the one paid thing in the middle of the week, because "
    "a cheap train day trip on a Tuesday off-peak is the best value going, and give each day one "
    "job out of the house so the week does not go by in small pieces.")

# --- the evening/weekend row stands down for a medicine line -------------------

FREE_WEEKEND = (
    "Pick two things and put them in the diary by Friday: one that gets you out of the house - a "
    "walk with a destination, a market on Saturday morning, a museum or gallery you keep meaning "
    "to visit - and one person to see or one thing waiting for you at home. The free ones that "
    "work are the walk, the park, a canal, a hill with a view, the library and a market on a "
    "Saturday morning. Two plans makes a good weekend; five makes a list you abandon by Saturday "
    "lunchtime. An evening is the same rule: one thing out and one thing in. Tell me the town and "
    "who is with you and I can suggest something specific.")

MEDICINE_NEEDS_A_REASON = (
    "What is it for? That decides it, and the same tablet is right for one thing and wrong for "
    "the next: paracetamol or ibuprofen at the dose on the pack covers most aches, and a "
    "pharmacist will check anything for a stomach ulcer, a kidney problem or another medicine "
    "you take. Tell me the symptom and I will say what you can take tonight and what to keep "
    "off.")

# An idea asked for is not something swallowed. "give me some ideas for a rainy weekend" holds
# the word "give" and names a day, and the medicine branch answered it with "what is it for?",
# a question about a tablet nobody had mentioned. The things you swallow by name are always a
# medicine line; the bare verb is one only when the line is not asking for ideas.
_AN_IDEA_ASKED_FOR = re.compile(r"\b(?:ideas?|suggestions?|things to do|something to do|"
                                 r"nothing to do|what can i do|what can we do|what should i do|"
                                 r"what should we do|what shall i do|what shall we do|"
                                 r"what to do|what else|recommend|recommendations|any good)\b")

_SWALLOWED_THING = ("tablet", "tablets", "pill", "pills", "medicine", "medicines",
                    "painkiller", "painkillers", "paracetamol", "ibuprofen", "aspirin",
                    "antibiotic", "antibiotics", "antihistamine", "antihistamines",
                    "omeprazole", "dose", "supplement", "vitamin", "vitamins",
                    "swallow", "swallows", "swallowed", "swallowing")

# "take", "give" and the names of what is swallowed: a line with one of these and no symptom
# is asking about a medicine, and the answer depends on what is wrong.
_SWALLOWED = ("take", "taking", "took", "give", "giving", "swallow", "tablet", "tablets",
              "pill", "pills", "medicine", "medicines", "painkiller", "painkillers",
              "paracetamol", "ibuprofen", "aspirin", "antibiotic", "antibiotics",
              "antihistamine", "antihistamines", "omeprazole", "dose", "supplement",
              "vitamin", "vitamins")


# A thing somebody brings to a place: "what can i take to a picnic this weekend" is a question
# about the picnic, and "this weekend" was enough to make it a question about the weekend.
_BRING_IT = ("picnic", "picnics", "bbq", "bbqs", "barbecue", "barbecues", "barbie", "party",
             "parties", "dinner party", "housewarming", "host", "hosts", "hostess",
             "birthday", "wedding", "buffet", "round", "potluck", "gathering")

# Something in the line that says it is about the weekend or about doing something, so the
# plan stands even when the turn before it was about an illness.
_OWN_ACTIVITY = ("weekend", "weekends", "saturday", "sunday", "day off", "days off",
                 "walk", "walks", "film", "films", "book", "books", "cook", "cooking",
                 "garden", "gardening", "friend", "friends", "market", "museum", "gallery",
                 "park", "library", "gym", "game", "games", "shop", "shopping", "trip",
                 "away", "pub", "coffee", "music", "cinema", "tv", "series", "run", "swim")


# A line that asks what is going on in the world is the day's news, not a free day. "whats
# happening in the world today" and "whats going on in the world today" were given the shape of a
# small Saturday - one thing out of the house, one job, one person - because "today" is in this
# row's key and "whats happening" is the rest of it. The world is not a thing to plan, and the
# honest line for the news already exists in the composer (it answers the same line without
# "today"), so this row stands down and lets it through.
_THE_WORLD = ("in the world", "around the world", "across the world", "world news", "the news",
              "the headlines", "headlines", "current events", "in the country")
# The ask in front of it: without one the line is a story about the world ("the news from home
# was good"), which is the memory's business and not this row's either way.
_ASKS_THE_WORLD = re.compile(
    r"\b(?:what|whats|what's|hows|how's|any|latest|tell|give|show)\b[^.]{0,24}\b(?:going on|"
    r"happening|happened|news|headlines|new)\b|\b(?:any|the|todays|today's)\s+(?:world\s+)?"
    r"news\b|\bheadlines\b|\bcurrent events\b", re.I)


def _asks_about_the_world(said):
    """True when the line is asking what is going on in the world rather than filling a day."""
    return bool(_holds(said, _THE_WORLD) and _ASKS_THE_WORLD.search(said))


def _said_words(understood):
    """The line as one lowered string, from the clean text as well as the words."""
    parts = [(understood or {}).get("clean"), (understood or {}).get("text")]
    parts.extend((understood or {}).get("words") or ())
    return " ".join(str(part) for part in parts if part).lower()


def _said_now(understood):
    """This line alone, without the turn before that a short follow-up arrives with.

    `clean` and `text` carry the turn before when the line leans on it, so a chat about
    "taking my mum to york" put "taking" in the context of the next line, and "what should we
    see" was asked what the tablets were for. `clauses` is where the two are kept apart: the
    last one is this line, and one clause means the line stood on its own.
    """
    clauses = [clause for clause in ((understood or {}).get("clauses") or []) if clause]
    if clauses:
        return " ".join(str(word) for word in clauses[-1]).lower()
    return _said_words(understood)


# A move that is named without the word "house" is still the same plan. "how do i plan a move"
# was a search hedge while "how do i organise a house move" answered, because every phrasing in the
# row's key said house or flat and the plan words alone scored nothing. The phrases below are the
# ones that mean a household move, and the guard keeps the ones that mean something else out: a
# move abroad turns on a visa, a move of a team is a job, and a move on a chessboard is neither.
_A_MOVE_TO_PLAN = re.compile(
    r"\b(?:plan|planning|planned|organise|organize|organising|organizing|prep|prepare|preparing|"
    r"arrange|arranging|checklist|tips?|advice|start|started|starting|before|ahead|get ready|"
    r"getting ready|ready)\b.{0,24}\b(?:a move|the move|the house move|my move|our move|"
    r"move out|move in)\b|\b(?:a move|the move|my move|our move)\b.{0,24}\b(?:plan|planning|"
    r"organise|organize|checklist|tips?|advice|prepare|prep|arrange)\b"
    # ...and the move named by time rather than by the word house: "what should i do first
    # when moving" and "before we move" are a household move with the house left out, and
    # the guard read them as a move nobody had named (a search hedge for the first).
    r"|\bwhen\s+(?:i|we|you)\s+move\b|\bwhen\s+moving\b|\bbefore\s+(?:i|we|you)\s+move\b"
    r"|\bwe\s*(?:'|\s)?re\s+moving\b", re.I)
_A_MOVE_ELSEWHERE = re.compile(
    r"\b(?:abroad|overseas|emigrat\w*|visa|another country|different country|new country|"
    r"australia|canada|new zealand|america|usa|spain|france|portugal|germany|ireland|dubai|"
    r"team|teams|job|jobs|career|office|house share|houseshare|chess|piece|checkmate|"
    r"the goalposts|goalposts|"
    # moving in together is its own plan and has its own card ("agree the boring things before
    # the boxes"), so the words that say it are not a move of house: "when we move in together
    # what should i do first" was taken off that card by the time-named move above.
    r"in together|moving in with|move in with)\b", re.I)


def _a_household_move(understood):
    """True when the line asks for the plan of a move of house, spelled without the word house."""
    said = _said_words(understood)
    return bool(_A_MOVE_TO_PLAN.search(said)) and not _A_MOVE_ELSEWHERE.search(said)


_HOME_IN_THE_LINE = re.compile(r"\b(?:house|houses|home|homes|flat|flats|apartment|apartments)\b",
                               re.I)


def _a_household_move_or_a_named_move(understood):
    """True when the line names the home it is leaving, or asks for a move's plan without one.

    The row's own key is written with the house in it ("moving house", "how do i move flat"),
    so a line that says one of those keeps its answer. The guard only decides the newer guess -
    "plan a move" with no house in it - which would otherwise take a move abroad or a move at
    work.
    """
    if _HOME_IN_THE_LINE.search(_said_words(understood)):
        return True
    return _a_household_move(understood)


# A day named on its own is not the weekend: "what should i do today" was handed two things in
# the diary by Friday. The row keeps the line and answers the day it named instead.
_TODAY_WORDS = ("today", "tonight", "this afternoon", "this morning", "this evening", "tomorrow")
_WEEKEND_WORDS = ("weekend", "weekends", "saturday", "sunday", "day off", "days off",
                  "week off", "long weekend")


def _a_free_weekend(memory, understood):
    """The free-weekend plan, or None when the line is asking about something you swallow.

    "can i take anything tonight" and "can i take anything for it tonight" got the plan for a
    weekend ("Pick two things and put them in the diary by Friday"): "tonight" is in this row's
    key and "anything" is the rest of it, and neither says what the person is asking about. A
    line that names a medicine, or asks whether to take one, is never a thing to do on a
    Saturday. When it leans on the turn before ("what can i take for it", after a toothache) the
    row stands down and the health rows answer it from the line it leans on; when it names
    nothing at all, the honest answer is to ask what it is for.
    """
    said = _said_words(understood)
    if _a_medicine_line(said):
        return MEDICINE_NEEDS_A_REASON
    if _holds(said, _TODAY_WORDS) and not _holds(said, _WEEKEND_WORDS):
        # the evening has its own shape, and a bare "today" the shape of a free day
        if _holds(said, ("tonight", "this evening")):
            return EVENING_PLAN
        return DAY_OFF_PLAN
    return FREE_WEEKEND


def _holds(said, words):
    """True when one of `words` stands in `said` as a whole word or phrase."""
    return any(re.search(r"\b" + re.escape(word) + r"\b", said) for word in words)


def _a_medicine_line(said):
    """True when the line is about something you swallow, not about a free day.

    The verb on its own is too little: "give" and "take" are how people ask for a suggestion
    ("give me some ideas for a rainy weekend", "take a look at my weekend"), and the medicine
    branch answered the first of those with a question about a tablet. A swallowed thing named
    by name keeps any line a medicine line; the verb only counts when the line is not asking
    for ideas.
    """
    if not _holds(said, _SWALLOWED):
        return False
    if _AN_IDEA_ASKED_FOR.search(said) and not _holds(said, _SWALLOWED_THING):
        return False
    return True


# A free day is the subject of the line when the line names nothing else to be about. The two
# halves of the row below - an ask for something to do and a day or a budget to fit it in - are
# both made of words that also sit in front of a noun: "any ideas for cheap party food", "cheap
# christmas present ideas", "ive got half a cabbage left from sunday, what can i do with it" and
# "any ideas for a film tonight" are each a question about that noun, and all four were answered
# with the shapes of a free day. The noun is the subject, and the row that answers it is the
# answer; this row is for the lines that name a stretch of time and nothing to put in it.
FREE_TIME_TIME = frozenset("""
    weekend weekends saturday saturdays sunday sundays friday fridays monday mondays tuesday
    tuesdays wednesday wednesdays thursday thursdays week weeks weekday weeknight evening
    evenings afternoon afternoons morning mornings night nights tonight tomorrow today
    holiday holidays day days off hour hours while time break
    spring summer autumn winter terms half-term
    """.split())
# The budget is not the time: "cheap" alone says what the line can spend, and "cheap christmas
# present ideas" is a shopping question that this row answered because "cheap" and "ideas" are
# both in its keys. A row about a free day needs a day in it.
FREE_TIME_WORDS = FREE_TIME_TIME | frozenset("""
    cheap cheaper cheapest cheaply budget budgets free money cost costs spend spending spent
    afford much less little broke skint quid pound pounds
    """.split())
# ... and who is coming along is not a thing to do either: "a cheap day out with the kids" and
# "something to do as a family" are this question with company, and the family.py rows answer
# the lines that are about the children themselves.
FREE_TIME_WHO = frozenset("""
    i me my we us our you your they them he she him her kid kids child children family families
    everyone anybody somebody friend friends partner husband wife mum dad son daughter baby
    toddler
    """.split())


# "bank holiday" is a day off, and the reading takes `bank` for the subject of the line.
HOLIDAY_PREFIX = frozenset("bank public school".split())
# Where the free time is spent is not a thing the line asks about: "cheap things to do at home"
# and "any ideas for things to do indoors" are still the free day, and the day plan covers both
# halves. A house that needs fixing is a different question and keeps its own answer.
AT_HOME = re.compile(r"\b(?:at home|at ours|indoors|inside|outdoors|outside|out and about)\b")
# A day said to be free is a free day, whatever else the reading took for the subject: "i have
# nothing planned this weekend and it is cold" reads `cold` as a complaint, and `nothing planned`
# is the question. Only when the other names in the line say nothing to be answered about (the
# weather, a temperature, being bored) and never over a thing of its own, because "i have nothing
# planned, what can i do about my boiler" is still the boiler.
FREE_TIME_CUE = re.compile(
    r"\bnothing (?:much )?planned\b|\b(?:no|not much|nothing much) plans?\b"
    r"|\bnothing (?:at all )?(?:to do|going on|on)\b|\bnot a thing planned\b", re.I)
A_DAY_CONDITION = frozenset("""
    cold colder hot hotter warm warmer wet damp raining rainy rain sunny freezing frozen snow
    snowy icy windy foggy grey gray dark weather forecast degrees bored boring bored stiff
    """.split())


def _a_stretch_of_time_to_fill(understood):
    """Whether the line asks what to do with time it has, rather than about a thing it names.

    The reading already says what the line is about: `subject` names the one thing it is about
    and `entities` names the rest. A subject made only of time, money and company words is the
    free day itself ("something to do on saturday without spending much" reads as `spending`,
    "i have a week off in summer any ideas" as `summer`), and anything else is the subject the
    line is asking about instead.
    """
    named = []
    subject = understood.get("subject")
    if subject:
        named.append(str(subject).lower())
    for found in understood.get("entities") or ():
        if isinstance(found, dict) and found.get("text"):
            named.append(str(found["text"]).lower())
    line_said = str(understood.get("clean") or "").lower()
    if FREE_TIME_CUE.search(line_said) and all(
            word in FREE_TIME_WORDS or word in FREE_TIME_WHO or word in A_DAY_CONDITION or
            word in FREE_TIME_TIME
            for word in re.findall(r"[a-z']+", " ".join(named).lower())):
        return True         # "nothing planned this weekend and it is cold" is the weekend
    # A holiday said in two words is still a holiday: "what should i do this bank holiday" reads
    # `bank` as its subject, and a day off work is not the bank it is spelt with. The names are
    # read together so the pair can be seen.
    words_named = re.findall(r"[a-z']+", AT_HOME.sub(" ", " ".join(named).lower()))
    if any(word in FREE_TIME_TIME for word in words_named):
        words_named = [word for word in words_named if word not in HOLIDAY_PREFIX]
    # "after work" is the block and not the job, and "in the garden" is where the block is spent
    # and not a thing to be about: both name a word the reading then calls the subject, so the
    # free block was read as a work question or a gardening one and the row stood down - "what
    # should i do after work" and "suggest something to do in the garden this weekend" were both
    # handed the search hedge. The words come off the subject exactly as they come off the line.
    covered = _covered_words(line_said, FREE_TIME)
    # "for the garden at the weekend" is the block's place, so the place is read with "for" when
    # the line already holds a block: "suggest something for the garden at the weekend" was the
    # hedge while "suggest something to do in the garden this weekend" got the plan.
    here_now = _the_place_the_block_is_at(
        line_said, block=bool(covered) or bool(set(re.findall(r"[a-z']+", line_said))
                                              & FREE_TIME_TIME))
    for word in words_named:
        if word in FREE_TIME_WORDS or word in FREE_TIME_WHO:
            continue
        if word in covered or word in here_now:
            continue
        return False        # the line names something of its own to be about
    # With nothing named at all, the row still needs a stretch of time to be the question: "cheap
    # christmas present ideas" and "and cheap wrapping ideas" read as shopping and as money, and
    # the budget word in front of the thing they are about is not a budget for an outing. A line
    # about nothing in particular ("what can i do at home", "im bored any ideas") is still free
    # time, and that is the only reading with no topic of its own.
    line = line_said
    if set(re.findall(r"[a-z']+", line)) & FREE_TIME_TIME:
        return True
    if AT_HOME.search(line):
        return True
    # A block said as a phrase is the subject even when the reading put a topic on the line for
    # it: "after work" is read as a work line and "this weekend in the garden" as a garden one,
    # and the topic is that word coming back round.
    if covered:
        return True
    # The topic carried in from an earlier line is not the line's own: "what can i do at home"
    # after a talk about reading practice names nothing itself, and it is still a free day.
    topic = understood.get("topic_own", understood.get("topic"))
    return not topic or topic == "small-talk"


def _free_weekend_fits(understood):
    """False when the line is not a question about the weekend at all.

    Three lines reached this row only because "tonight" is in its key: an ask for a medicine
    that names no medicine ("can i take anything for it tonight", after a toothache), an ask
    for something to take to a place ("anything i can take to a picnic this weekend"), and a
    plan ask the turn after an illness ("i have a cold" then "anything i can do tonight"). The
    row stands down on all three, so the row that knows the subject answers instead. A line
    that names its own day or its own thing to do keeps the plan.
    """
    # a complaint named in the line is the complaint's question, not the weekend that holds
    # it: "what can i do about a cold this weekend" is the cold's card, and "i have toothache
    # at the weekend, what can i do" is the toothache's. The subject has to be named - "ideas
    # for a weekend when you are ill" is about the weekend and keeps the plan.
    if _about_a_thing_the_person_has(understood):
        return False
    said = _said_words(understood)
    if _ASKS_A_CLOCK.search(said):
        # "what time is sunset today", "when does the match start tonight": the named thing's
        # own time is the question, and a free block to fill is not an answer to it.
        return False
    if _asks_about_the_world(said):
        # "whats going on in the world today" is the news; a free day is not what it named.
        return False
    leans = understood.get("leans_on")
    follows = isinstance(leans, dict) and bool(leans.get("subject"))
    if _holds(said, _BRING_IT) and re.search(r"\b(take|taking|took|bring|bringing|give|"
                                            r"giving|make)\b[^.]*\bto\b", said):
        return False
    if _holds(said, _SWALLOWED) and not _holds(_said_now(understood), _SWALLOWED):
        # the swallow word is in the turn before, not in this line: a chat about "taking my mum
        # to york" left "taking" behind it. Only a line that names its own day or its own thing
        # to do keeps the plan; anything else stands down rather than asking what the tablets
        # were for.
        return _holds(_said_now(understood), _OWN_ACTIVITY)
    if not _a_medicine_line(said):
        if follows and leans.get("topic") == "health" and not _holds(said, _OWN_ACTIVITY):
            return False
        return True
    # "what can i take for it" leaves the medicine to the turn before; the line that names no
    # medicine and no turn before it gets the question back from `_a_free_weekend`
    return not follows


# "for a rainy day" is two questions. It is the money idiom when the line is about saving -
# "how do i save for a rainy day", "put money aside for a rainy day" - and it is the weather
# when the ask is what to do: "any ideas for a rainy day" was told to track two weeks of
# spending, and "ideas for a rainy weekend" gets the long-afternoon answer. The idiom is only
# a key word here when a money word is in the line with it.
_FOR_A_RAINY_DAY = re.compile(r"\bfor a rainy day\b")
_MONEY_WITH_IT = re.compile(r"\b(?:save|saves|saving|saved|savings|put aside|aside|fund|funds|"
                            r"money|cash|pounds?|quid|income|salary|afford|afforded|budget|"
                            r"emergency|invest|investing|interest)\b")


def _a_rainy_day_is_money(reading):
    """False when "for a rainy day" is the weather rather than the savings idiom."""
    said = _said_words(reading)
    if not _FOR_A_RAINY_DAY.search(said):
        return True
    return bool(_MONEY_WITH_IT.search(said))


# "what should i do this weekend i have no money" is the same question with a fact in it, and a
# plan that opens with a market and a swim is not an answer to it. None of the suggestions above
# cost anything except the coffee, so the money line is a sentence rather than a second plan.
NO_MONEY = ("None of that has to cost anything: the walk and the library are free either way, "
            "and a flask beats a cafe.")

MONEY_WORDS = ("no money", "not much money", "dont have money", "don't have money", "broke",
               "skint", "no cash", "on a budget", "tight budget", "money is tight", "cant afford",
               "can't afford", "cheap things", "free things", "as little as possible")

# A block of free time in a line that also names being ill is a question about the illness:
# "i am off next week with my back what should i do" was given the week-off plan when the useful
# answer is the back one, and a person off work with a bad back is not asking for ideas.
# "cold" is left out on purpose: "i have nothing planned this weekend and it is cold" is
# weather, and with the bare word here the weekend plan stood down and the line was echoed back.
# Bare "cold" came out of _UNWELL because "i have nothing planned this weekend and it is cold" is
# weather, not illness - and then "i am off next week with a cold what should i do" was handed the
# week plan. The two readings are told apart by what the word is doing, so it is a shape rather
# than a word: something you have or caught up against cold as the weather outside.
_COLD = re.compile(r"((with|have|has|had|got|caught|a|the|my|his|her|their)\s+cold\b"
                   r"|\bcold\s+(sore|virus|coming on|and a cough|at the moment))")
_COLD_WEATHER = re.compile(r"((is it|it is|it's|its|too|so|very|really|freezing|bit|outside"
                           r"|weather|getting|turning|pretty)\s+(\w+\s+)?cold\b"
                           r"|\bcold\s+(today|tomorrow|outside|weather|enough|out)\b)")

_UNWELL = ("sick", "ill", "unwell", "poorly", "flu", "covid", "migraine", "surgery",
           "operation", "hospital", "injury", "injured", "recovering", "recovery", "pain",
           "hurts", "hurting", "sore", "ache", "aching", "back", "knee", "shoulder", "ankle",
           "stomach", "chest", "fever", "temperature", "dizzy", "exhausted", "burnt out")


# A week off with a newborn is not a week off: two nights away and a day out of the house are the
# wrong shape entirely, and the illness rules that used to answer it ("stay off while you have a
# fever") were worse. The useful answer is the small one.
NEWBORN_WEEK = (
    "With a newborn the week plans itself, so plan the small things instead: take the nights in "
    "shifts so one of you gets a four-hour stretch, get out once a day even if it is only round "
    "the block, and say yes to anyone who offers to hold the baby while you sleep. Register the "
    "birth inside 42 days, keep the health visitor's number to hand, and book nothing that has a "
    "start time - a week off now is recovery, not a holiday.")

# A block of free time in a line that asks about a note is a question about the paperwork:
# "im off work next week do i need a note" was given the week plan, and the self-certificate and
# the fit note are what the person actually needs.
_NOTE_ASK = ("need a note", "need the note", "fit note", "sick note", "doctors note",
             "doctor's note", "medical note", "medical certificate", "self certificate",
             "self-certificate", "self cert", "self-certify", "signed off", "sign me off",
             "getting a note", "get a note", "note from the doctor")

# ...and a line that names what the week is for is that thing's question, not a free block's:
# "im off work next week for a wedding" was given the two nights away and a job you keep
# putting off. The leave row answers the wedding, and the baby has its own reply above.
_EVENT_AWAY = ("wedding", "funeral", "christening", "baptism", "moving house", "moving home",
               "house move", "moving day", "exam", "exams", "revision", "court", "interview")

# The ways people ask where to go. Every one of them is a place question first, so the free
# block in the line is what they are filling, not what they want planned.
_WHERE_GO_PHRASES = ("where should i go", "where can i go", "where to go", "where should we go",
                     "where can we go", "where would you go", "where could i go", "where to",
                     "where would we go", "where could we go", "which country", "what place",
                     "somewhere warm", "somewhere hot", "somewhere near", "where shall we go",
                     "where shall i go")

# ...and the words that say the ask is a trip rather than a plan for the days at home.
# A city named in a free-time line is where the weekend is, and travel.py answers for it: "what
# should i do in lisbon for a weekend" was the three-things plan, and the same for Rome and
# Edinburgh. There are 57 cities and the list lives in one place, so this asks travel for it
# rather than copying names here. "bath" is a city and a tub, so it is left out.
_AMBIGUOUS_CITY_WORDS = ("bath",)


def _a_city_is_named(line):
    """True when the line names a city a guide answers for."""
    from .travel import CITIES

    for city in CITIES:
        if city in _AMBIGUOUS_CITY_WORDS:
            continue
        if re.search(r"(?<![a-z])%s(?![a-z])" % re.escape(city), " " + line + " "):
            return True
    return False


_TRIP_PHRASES = ("plan a trip", "planning a trip", "planning a holiday", "book a trip",
                 "going away", "go away", "get away for", "away for a", "a trip", "trip with",
                 "trip for", "holiday with", "travel with", "a break away", "book a holiday",
                 # "i have a week off and want to go somewhere" and "should i go away or stay
                 # at home for my week off" are both the away-or-home question, and the leave
                 # row's own card ends on exactly that: "Going somewhere, or is it a week at
                 # home?" A plan for the days at home answers neither.
                 "go somewhere", "going somewhere", "somewhere away", "stay at home",
                 "staying at home", "at home or away", "away or at home",
                 # "any ideas for a weekend away" and "a weekend away in october" are where-to
                 # go questions, and a plan for the weekend at home answers neither: the same
                 # line with the words in the other order ("weekend away ideas") already
                 # reached the travel card.
                 "weekend away", "weekends away", "away for the weekend", "away for a weekend")

# the words that say the free block has a date and a place in it - a month, a season, or a
# named kind of weather - so the answers that name a month own the line
_WHEN_AWAY = ("in january", "in february", "in march", "in april", "in may", "in june",
              "in july", "in august", "in september", "in october", "in november",
              "in december", "in the summer", "in summer", "in the winter", "in winter",
              "in spring", "in autumn", "at christmas", "over christmas", "next summer",
              "half term", "bank holiday week", "shoulder season", "in the sun", "for some sun")

_MONEY_ONLY = ("quid", "pounds", "euros", "dollars", "budget", "cheap", "afford")

# An ask for a thing to give is a gift question, and the party plan or the plan for a free day
# is not the answer to it: "what should i get my mum for her birthday" was told how many people
# fit in a pub's back room, and "present ideas for my mum" reached a card about a care home.
# The gift rows answer both; these are the ways the ask is worded, with the person after it.
_GIFT_ASK = ("what should i get", "what do i get", "what can i get", "what to get",
             "what should i buy", "what can i buy", "what to buy", "should i get",
             "ideas for a present", "ideas for a gift", "present ideas", "gift ideas",
             "ideas for presents", "ideas for the present", "ideas for her", "ideas for him",
             "present for", "presents for", "gift for", "gifts for", "buy for",
             "get her for", "get him for", "get them for", "get my mum", "get my dad",
             "get my mam", "get my mom", "get my mother", "get my father", "get my sister",
             "get my brother", "get my nan", "get my gran", "get my partner",
             "get my wife", "get my husband", "get my friend")

# A month in the line is a month row's question: "i have a week off in january what should i do"
# belongs to the January answer ("the Canaries for 20C and real sun, the Alps for snow"), and a
# plan for the days at home is not it.
# An evening that belongs to a thing is that thing's evening, not a free block: "any tips for my
# parents evening" was given the weekend plan once the free-time key learned the plural, because the
# key word "evenings" stems to "evening" and a school's evening is not the person's.
_EVENT_EVENING = ("parents evening", "parent evening", "school evening", "open evening",
                  "induction evening", "college evening", "back to school evening",
                  "parents nights", "parents night", "open night")

# A free evening with a thing to watch named in it is that thing's pick, not a plan for the
# evening: "any netflix suggestions for tonight", "a film to watch tonight" and "what should I
# watch this evening" name the medium and ask what to put on it, and the free-time key's
# "tonight" and ask words answered them with "give the evening a shape ... one thing you will
# actually do at 8pm", which is the answer for a person with no medium in mind. The plan is
# right for "what should i do tonight"; a named film, series, service or book is a pick.
_MEDIUM_NAMED = ("netflix", "iplayer", "prime video", "disney", "now tv", "nowtv",
                 "britbox", "paramount", "all 4", "apple tv", "hayu", "youtube",
                 "streaming", "film", "films", "movie", "movies", "series", "show",
                 "shows", "boxset", "box set", "episode", "episodes", "documentary",
                 "documentaries", "sitcom", "sitcoms", "drama series", "podcast",
                 "podcasts", "audiobook", "audiobooks", "album", "playlist", "novel",
                 "novels", "something to read", "something to watch")

_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august",
           "september", "october", "november", "december")

# A block of time named as work leave, when it is stated and nothing is asked.
_WORK_BLOCK = ("off work", "off next week", "next week off", "week off work", "off all week",
               "off for a week", "taking next week off", "taking the week off", "the week off",
               "off from monday", "off work for", "week at home")

# A line that asks for ideas *about a thing* is about that thing, not about the time it is
# asked in: "any ideas for a film tonight" wants something to watch and "any ideas for cheap
# party food" wants the food. The two catch-all rows in this domain (the free-time plan and the
# cheap day out) are for a line with no subject of its own, and they used to take these on the
# word "ideas" alone. The words that name a block of time are what keep the plan for the
# person who really did ask what to do with an evening.
_TIME_WORDS = frozenset(
    "tonight today tomorrow evening evenings afternoon afternoons morning mornings night "
    "nights weekend weekends week weeks weekday weekdays day days month months year years "
    "saturday sunday monday tuesday wednesday thursday friday summer winter spring autumn "
    "christmas easter holiday holidays time break "
    # A clause that says when the block is names no thing: "any ideas for when i finish work"
    # and "any ideas for once the kids are in bed" are the block's question, and the word that
    # opens the clause was being read as the thing the ideas were for.
    "when once whenever after before until till while".split())
# The words that point at nothing of their own: "any ideas for things to do" is the plan.
_NO_SUBJECT = frozenset("things thing something anything stuff more other else".split())
# The words a person puts in front of "ideas" without naming a thing: "coming up any ideas",
# "im out of ideas", "any more ideas".
_IDEA_FILLER = frozenset(
    "a an the any some more other no not few couple another new better good great best "
    "and or of on for to up out off my your our their his her its i we you they have has "
    "had got need needs want wants running stuck fresh different".split())
_IDEAS_FOR = re.compile(r"\bideas?\s+(?:for|about|on)\s+(.+)", re.I)
_IDEAS_ASK = re.compile(r"\bideas?\s+(?:what|which|who|where|how|when)\b", re.I)
# "i have a week off and no idea what to do" is the plan asked for in other words, so a no-idea
# is not an idea about a thing.
_IDEA_NONE = re.compile(r"\b(no|not|never|without|dont|don't|doesnt|doesn't|havent|haven't)"
                        r"\s+(?:idea|ideas)\b", re.I)


def _ideas_about_a_thing(understood):
    """True when the line asks for ideas about a named thing rather than about a free block.

    "any ideas for a film tonight" and "cheap christmas present ideas" are the film row's and
    the present row's question; "any ideas for the weekend" and "any ideas for tonight" are
    this domain's. Read from the clean line, because it is the words as typed that say what the
    ideas are for, and the reading drops the preposition the subject hangs on.
    """
    clean = str((understood or {}).get("clean") or "").lower()
    if not clean:
        return False
    if _IDEA_NONE.search(clean):
        return False
    if _IDEAS_ASK.search(clean):
        # "any ideas what to watch", "any idea where to go": the thing asked for is a choice.
        return True
    found = _IDEAS_FOR.search(clean)
    if found:
        rest = found.group(1)
        words = [word for word in re.findall(r"[a-z']+", rest)
                 if word not in _IDEA_FILLER]
        # somewhere warmer, a weekend away: a trip is a place to go, not a plan at home
        if any(word in ("away", "somewhere", "abroad") for word in words):
            return True
        if not words:
            return False
        # "any ideas for after work" asks for ideas about a free block and not about a thing: the
        # words of the block ("after work", "off work tomorrow") come off what the ideas are for,
        # the same way they come off the subject elsewhere. What is left is what the line is
        # really asking about, and when nothing is left the plan is the answer.
        covered = _covered_words(rest, FREE_TIME + WEEK_OFF)
        # ...and the place the block is spent in is not a thing the ideas are for either:
        # "any ideas for the front room tomorrow" asked what to do with the room's evening.
        here = _the_place_the_block_is_at(clean, block=True)
        words = [word for word in words if word not in covered and word not in here]
        if not words:
            return False
        return words[0] not in _TIME_WORDS and words[0] not in _NO_SUBJECT
    return False


# The topics where "what can i do" is about something the person already has - a symptom, an ache,
# a dish in the fridge - rather than about a free block. "i have toothache at the weekend, what can
# i do" is the toothache card and "ive got half a cabbage left, what can i do with it" is the
# cabbage's, and both rows here took them on "what can i do" plus the day the line was asked on.
#
# Named per topic, never "any topic the line is about": a day out asked as "what can i do as a
# family" reads as money, a week off reads as work, "we're skint this weekend" reads as money, and
# those are this domain's own lines - standing down on them would take the day out away from the
# person asking for one. Cooking is not here either, though a dish is a thing a person has: a
# barbecue is read as cooking, and "were having a bbq saturday but its ment to rain, any ideas"
# wants the weekend plan. The body is the one subject where "what can i do" is never about time.
_A_THING_THE_PERSON_HAS = ("health", "fitness", "sleep")


# ...and the ways a person asks what to do about it. "how long does it last" and "is it
# serious" are questions about the thing too, but the plan was never the answer to those; what
# this list has to catch is the "what can i do" that the two rows below read as "what can i do
# with my day". "nothing planned" is not here: "i have nothing planned this weekend and it is
# cold" is about the weekend, and "cold" there is the weather the plan is for.
_ASKS_ABOUT_IT = ("what can i do", "what should i do", "what do i do", "what to do",
                  "what shall i do", "what can we do", "what should we do", "how do i",
                  "how can i", "what helps", "what would help", "what can i take",
                  "can i take", "anything i can", "anything to take", "anything i can take")


def _about_a_thing_the_person_has(reading):
    """True when the line asks what to do about an ache or a complaint of its own.

    Three things have to hold, and each of them keeps a different line out. The subject has to
    be named: "i have toothache at the weekend, what can i do" has one and "ideas for a weekend
    when you are ill" does not. The topic has to be the body: "ive got half a cabbage left from
    sunday, what can i do with it" is food, not a complaint. And the line has to ask what to do
    about it: "i have nothing planned this weekend and it is cold" names a subject (the reading
    calls the weather a cold) but asks about the weekend, and the plan is what it came for.
    """
    reading = reading or {}
    if not reading.get("subject"):
        return False
    if reading.get("topic_own") not in _A_THING_THE_PERSON_HAS:
        return False
    return _holds(_said_words(reading), _ASKS_ABOUT_IT)


def _a_day_out_is_the_question(reading):
    """False when the line asks what to do about a thing of its own rather than about a free day.

    "any ideas for a film tonight" names a film, "i have toothache at the weekend, what can i do"
    names the toothache and "ive got half a cabbage left from sunday, what can i do with it" names
    the cabbage: both rows here are for a line whose subject is the time or the money.
    """
    if _ideas_about_a_thing(reading):
        return False
    return not _about_a_thing_the_person_has(reading)


# ...and the ways a person asks what to do with a free block. Anything else is a statement.
_ASKS = ("what should i do", "what can i do", "what do i do", "what to do", "what shall i do",
         "any ideas", "ideas", "idea", "anything to do", "something to do", "suggestions",
         "suggestion", "tips", "tip", "advice", "nothing planned", "nothing on", "no idea",
         "bored", "plan it", "help me plan", "plan something", "whats on", "what's on",
         "big plans", "recommend", "how do i fill", "fill the time", "keep busy", "keep me busy")

# A run of days counted in the line is a short free block, not a week's leave: "i have 3 days off
# next week" and "i have four days off next month" were read as an event coming up and asked "How
# ready do you feel for it?", because "off next week" is one of the work-block phrases that hands
# the line on to the leave row - and the leave row has nothing for a run of days rather than a
# week. The number is what makes it a free block to plan, a day at a time.
_SHORT_RUN = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six)\s+(?:whole\s+|full\s+|more\s+)?days?\s+"
    r"(?:off|free|holiday|to myself|at home)\b"
    r"|\b(?:a\s+)?(?:few|couple\s+of|handful\s+of)\s+days?\s+(?:off|free|to myself)\b")

# A run of days with a purpose already in the line is not free time: "i have 3 days off next week
# to paint the kitchen" wants the painting answer it had before this row, and the plan for a free
# block - one job you keep putting off, one person to see - says nothing about the job the person
# named. Six of forty-two typed lines were worse without this fence and every line it was measured
# to win has no purpose in it. The fence is the purpose clause, not the number.
_PURPOSE_AFTER_RUN = re.compile(
    r"\b(?:to\s+[a-z]+|for\s+(?:the|a|an|my|our|his|her|their|some)\b"
    r"|so\s+(?:i|we)\s+can\b|because\b)")


def _short_run(line):
    """The counted run of days in the line, unless the line says what the time is for."""
    found = _SHORT_RUN.search(line)
    if not found:
        return None
    if _PURPOSE_AFTER_RUN.search(line[found.end():]):
        return None
    return found

# The ways a person asks for the time rather than saying they have it.
_REQUESTING_TIME = ("book a day off", "book a week off", "book time off", "book some time off",
                    "book the day off", "book it off", "take a day off", "take a week off",
                    "take time off", "take some time off", "take the day off", "take it off",
                    "request a day off", "request a week off", "request time off",
                    "ask for a day off", "ask for a week off", "ask for time off",
                    "ask my boss", "ask the boss", "ask my manager", "put in for",
                    "want to book", "want to take a day", "want to take a week",
                    "can i book", "can i take a day", "can i take a week",
                    "could i take", "could i book", "am i allowed to take")


# The words a subject can be made of and still be the free block itself rather than a thing
# the line is asking about. "what should i do with my day off" names the day, and the plan is
# the answer to it; "what should i do with my drone this weekend" names the drone.
_FREE_BLOCK_WORDS = frozenset((
    "weekend", "weekends", "saturday", "sundays", "sunday", "day", "days", "evening",
    "evenings", "night", "nights", "tonight", "afternoon", "morning", "holiday", "holidays",
    "week", "weeks", "time", "leave", "rest", "break", "free", "off", "plans", "plan",
    # "off work tomorrow with nothing planned" is the block said in the order people say it:
    # "work" and "tomorrow" were read as the thing the line was about, and the plan it asked for
    # went to the leave script instead
    "work", "tomorrow", "today", "now", "later",
    "nothing", "home", "myself", "ourselves", "me", "us", "family", "friends",
    # the day it is on is the free block and not a thing to do: "i have the day off on friday"
    "monday", "mondays", "tuesday", "tuesdays", "wednesday", "wednesdays", "thursday",
    "thursdays", "friday", "fridays", "saturday", "weekday", "weekdays", "weeknight",
    # a rainy day, a wet weekend and a day indoors are free blocks of the same kind
    "rainy", "wet", "cold", "indoors", "outside", "sunny", "summer", "winter", "autumn",
    "spring", "hot",
))

# The asking words themselves: a free block with one of these is the question this card
# answers, and neither word names a thing of its own.
_ASK_WORDS = frozenset((
    "what", "whats", "what's", "which", "where", "when", "how", "why", "who",
    "should", "shall", "can", "could", "would", "will", "do", "does", "did", "doing",
    "i", "we", "you", "id", "im", "ive", "us", "me", "my", "our", "your",
    "the", "a", "an", "this", "that", "these", "those", "next", "last", "coming",
    "some", "any", "something", "anything", "nothing", "thing", "things", "stuff",
    "ideas", "idea", "suggestions", "suggestion", "suggest", "recommend",
    "tips", "tip", "advice", "advise", "good", "nice", "fun", "funny", "best", "better",
    "on", "in", "at", "for", "to", "of", "and", "or", "but", "with", "without",
    "around", "about", "out", "up", "there", "here", "together", "nearby", "local",
    "all", "day", "whole", "long", "few", "couple", "off", "free", "bored", "nothing",
    "fill", "busy", "keep", "make", "most", "use", "spend", "sort", "go", "going",
    "somewhere", "anywhere", "nowhere", "else", "instead", "please", "help", "planned",
    "plans", "plan", "properly", "proper", "decent", "little", "bit", "much", "spend",
    "spending", "spent", "cost", "costs", "price", "prices", "hi", "hiya", "hey",
    "hello", "yo", "ok", "okay", "so", "well", "just", "really", "actually", "still",
))

# The free block spent on a job, rather than on a thing to pick. "how do i use a week off to
# sort my flat out" names the flat, and a plan for the week is still what is being asked for -
# the thing named is what the time goes on, not something to choose between. A job word takes
# the line back to the plan, and the rows that answer a named thing still get it first.
_JOB_WORDS = frozenset((
    "sort", "sorted", "sorting", "tidy", "tidying", "clear", "clearing", "clean", "cleaning",
    "declutter", "decluttering", "pack", "packing", "unpack", "unpacking", "paint", "painting",
    "fix", "fixing", "mend", "mending", "repair", "repairing", "decorate", "decorating",
    "redecorate", "reorganise", "reorganising", "organise", "organising", "rearrange",
    "hoover", "weed", "weeding", "tackle", "tackling", "file", "filing", "paperwork",
))

# How many of something the free block is, when what it counts is time: "i have three weeks off
# in the summer" was stood down as if the three named a thing, and the week's plan was lost to
# the echo behind it.
_COUNT_WORDS = frozenset("""
    one two three four five six seven eight nine ten eleven twelve dozen couple few several
    half single both
    """.split())

# A thing the line names as the one thing it does *not* want. "something to do tonight that isnt
# tv" names the tv to be rid of it, so the tv is not what the line is asking about and the plan
# for the evening is still the answer; the same for "no tv", "without the telly".
_NOT_THE_THING = frozenset((
    "not", "isnt", "isn't", "arent", "aren't", "wasnt", "wasn't", "no", "without", "non",
    "except", "besides", "bar", "minus", "other", "than", "rather", "instead", "nor", "never",
))

# Words that only say what the free block is for or how much it may cost, in a line that is
# still asking what to do with it.
_BLOCK_QUALIFIERS = frozenset((
    "cheap", "free", "budget", "afford", "money", "quid", "pounds", "tenner", "fiver",
    "spare", "skint", "pennies", "cash", "nice", "quiet", "lazy", "relaxing",
    # saying there is no money is still asking what to do with the time: "im broke what should i
    # do tonight" was handed the savings plan once the free block stood down for "broke"
    "broke", "broken", "poor", "brassic", "skint", "tight", "moneyless", "bust",
))


# A room or the home named after "in", "at" or "on" is where the free block happens, not a
# thing to plan for: "what should i do in my kitchen this weekend" and "any ideas for something
# to do at home" ask what to do with the time, and the plan is the answer to that. The
# preposition is what makes it a place - "any ideas for my garden" is the garden's own question
# (what to plant in it), and there the plan stands down.
#
# A garden is not a room, and neither is an allotment or a shed: it is a place with work of its
# own, and the answer to "suggest something to do in the garden this weekend" is the garden's
# own card. Reading those as rooms did the opposite - the plan kept the line and answered a
# garden question with "a walk you have not done, a park, the library", the one thing a garden
# is not (deck rows afbt-06 and abpl-02 on this branch, both a loss against main). So the words
# here are the places that hold the person's own time and nothing else, and the growing places
# stay things of their own in the line.
_AT_HOME = ("kitchen", "house", "flat", "home", "loft", "attic", "cellar",
            "living room", "dining room", "bedroom", "bathroom", "spare room",
            "conservatory", "study", "front room", "back room", "box room",
            "utility room", "hall", "hallway", "landing", "porch")
# The prepositions a place the time is spent in is said with. "for" is only read this way on a
# line that holds a free block: "something for the garden at the weekend" is where the weekend
# goes, and "any ideas for my garden" is the garden's own question.
_AT_THE_PLACE_WORDS = ("in", "at", "on", "into", "inside", "around", "round")
_FOR_THE_PLACE_WORDS = ("for",)
_THE_OWNER = ("the", "my", "our", "your", "his", "her", "their")


def _the_place_the_block_is_at(said, block=False):
    """The words of the room or corner the free block is spent in, if the line names one.

    "in the garden", "at home", "on the balcony", "in the back garden": the time is spent
    there, and what to do with it is still the question, so the plan is the answer. Read word
    by word rather than by regex, because a place is often two words, the first of them alone
    ("back", "front", "living") is not the place, and one match must not eat the next.

    `block` says the line holds a free block, which is what makes "for the garden" a place the
    time is spent in rather than the thing it is about.
    """
    words = re.findall(r"[a-z']+", str(said or "").lower())
    preps = set(_AT_THE_PLACE_WORDS) | (set(_FOR_THE_PLACE_WORDS) if block else set())
    here = set()
    for i, word in enumerate(words):
        if word not in preps:
            continue
        j = i + 1
        if j < len(words) and words[j] in _THE_OWNER:
            j += 1
        pair = " ".join(words[j:j + 2])
        if pair in _AT_HOME:
            here.update(pair.split())
        elif j < len(words) and words[j] in _AT_HOME:
            here.add(words[j])
    return here


def _names_the_free_block(named):
    """Whether the line's subject is the free block itself rather than a thing of its own."""
    words = [word for word in re.split(r"[^a-z0-9']+", str(named or "").lower()) if word]
    if not words:
        return True
    return all(word in _FREE_BLOCK_WORDS or word in _ASK_WORDS or word in _BLOCK_QUALIFIERS
               or word in _COUNT_WORDS for word in words)


def _covered_words(text, phrases):
    """The words of the phrases of `phrases` this line holds, counted once each.

    A free block said as a phrase ("after work", "week off work", "day off tomorrow") brings
    words of its own that name no thing: the plan is still the answer to "what should i do
    after work". They come off the line before what is left is read as a thing.
    """
    covered = {}
    left = " %s " % text
    for phrase in sorted(phrases, key=len, reverse=True):
        pattern = r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(phrase)
        while re.search(pattern, left):
            left = re.sub(pattern, " ", left, count=1)
            for word in phrase.split():
                covered[word] = covered.get(word, 0) + 1
    return covered


# A musing is not a question. "i suppose i should hire a skip" says what the person has already
# made their mind up about, so the plan standing down only hands the line to an echo - which is
# worse than the plan, and the one line that changed for the worse in 145 chats that say
# "saturday". The plan is not the answer to a musing either (a skip card is), so this is a fence
# around the regression and not the fix: the words say whether a line is asking anything.
_MUSING = re.compile(r"\b(?:i|we)\s+(?:suppose|guess|reckon|expect|think)\b"
                     r"|\b(?:maybe|perhaps|probably)\b[^.?!]*\b(?:i|we)\b")


def _names_a_thing_of_its_own(understood):
    """Whether the line names a thing the plan is not about.

    A free block plus an ask is this card's question ("what should i do this weekend", "any
    ideas for a rainy day"), and every other word of such a line either says when it is or
    what it is for. A line that carries a word outside that vocabulary is asking about that
    word: "any ideas for a film tonight" is a film and "give me three ideas for a cheap date"
    is a date - both were answered with a plan for the evening or for a free day instead.
    """
    words = {word.lower().replace("'", "") for word in (understood.get("keywords") or ())
             if isinstance(word, str)}
    if words & _JOB_WORDS:
        return False
    said = " %s " % str(understood.get("clean") or "").lower()
    if _MUSING.search(said):
        return False
    # The block can be said as a phrase ("after work", "off work tomorrow") or as a plain word
    # of time ("tomorrow", "this evening"), and both make "for the garden" a place the time is
    # spent in rather than the thing the line is about.
    holds_block = bool(_covered_words(said, FREE_TIME + WEEK_OFF + _WORK_BLOCK)) or bool(
        set(re.findall(r"[a-z']+", said)) & FREE_TIME_TIME)
    here = _the_place_the_block_is_at(said, block=holds_block)
    shown = understood.get("subject")
    if isinstance(shown, str) and shown:
        left = " ".join(word for word in re.split(r"[^a-z0-9']+", shown.lower())
                        if word and word not in here)
        if left and not _names_the_free_block(left):
            return True
    covered = _covered_words(said, FREE_TIME + WEEK_OFF + FREE_TIME_ASK + _ASKS + _WORK_BLOCK)
    for word in understood.get("keywords") or ():
        if not isinstance(word, str):
            continue
        low = word.lower().replace("'", "")
        if (low in _FREE_BLOCK_WORDS or low in _ASK_WORDS or low in _BLOCK_QUALIFIERS
                or low in _COUNT_WORDS):
            continue
        if low.isdigit():
            continue
        if low in here:
            continue
        if covered.get(low):
            covered[low] -= 1
            continue
        if _said_as_the_thing_it_does_not_want(str(understood.get("clean") or ""), low):
            continue
        return True
    return False


def _said_as_the_thing_it_does_not_want(line, word):
    """Whether this word comes into the line as the thing the person wants to get away from."""
    found = re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(word.lower()), line.lower())
    if not found:
        return False
    before = line[:found.start()].lower().split()
    return bool(before[-2:] and set(before[-2:]) & _NOT_THE_THING)


def _free_time(memory, understood):
    said = " ".join(str(word).lower() for word in (understood.get("words") or []))
    clean = str(understood.get("clean") or "").lower()
    line = said + " " + clean
    if a_dish_is_already_the_plan(clean):
        # "thinking of doing a roast on sunday" and "fancy a spag bol tonight" name the dish
        # they mean to cook, and a plan for free time they have not mentioned is a lecture
        # about their evening instead. The dish's own card, or its plan, is the answer.
        return None
    if any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", line)
           for word in _UNWELL):
        return None
    # a cold is an illness unless the line is about the weather
    if _COLD.search(line) and not _COLD_WEATHER.search(line):
        return None
    # "i have 200 quid and a few days off where can i go" is a where question with a price in
    # it, and the place-and-price answer is the useful one: a plan for the afternoon is not a
    # reply to somebody asking where they can get to. Where-no-place holds the fares.
    if (any(phrase in line for phrase in _WHERE_GO_PHRASES)
            and any(word in line for word in MONEY_WORDS + _MONEY_ONLY + _WHEN_AWAY)):
        return None
    # The same again for the trip the day is for: "i want to plan a trip with a week off" and
    # "taking a week off in october where should we go" are travel questions with a free block
    # in them, and the plan for the days is not the answer to either.
    if any(phrase in line for phrase in _TRIP_PHRASES):
        return None
    # a named month has its own answer, and a plan for the days at home is not it
    if any(word in line for word in _MONTHS):
        return None
    # ...and a named city is where the free time is: the guide has the trams, the tarts and the
    # river, and a plan for three things near home does not answer "what should i do in lisbon
    # for a weekend".
    if _a_city_is_named(line):
        return None
    # a dish named in the line is a cooking question: "im gonna make a spag bol tnite any tips"
    # holds a free block ("tonight") and an ask ("any tips") and would otherwise be scored as a
    # free evening, which is the wrong reply to somebody about to cook. Read from the kitchen's
    # own table, so a dish nobody has a card for still falls through to the modules that know it.
    if _dish_for_tonight(memory, understood):
        return None
    # the paperwork is the question, not the free time
    if any(phrase in line for phrase in _NOTE_ASK):
        return None
    # a named event is that event's question, and the leave row has the answer for it
    if any(word in line for word in _EVENT_AWAY):
        return None
    # a school's evening is the school's, and the plan for a free evening is not the answer to it
    if any(phrase in line for phrase in _EVENT_EVENING):
        return None
    # a thing to watch or read is that thing's pick: the free-time key catches the "tonight" and
    # the ask word in "any netflix suggestions for tonight", and the answer to it is a service's
    # picks rather than a shape for the evening
    if any(phrase in line for phrase in _MEDIUM_NAMED):
        return None
    # a week off with a new baby has a shape of its own, and the two nights away are not it
    if any(word in line for word in ("newborn", "new baby", "new-born", "just had a baby",
                                     "had a baby", "baby is due", "baby due", "paternity",
                                     "maternity leave", "on maternity")):
        return NEWBORN_WEEK
    # asking for the time is not having it: "i want to book a day off next week" wanted the
    # script for the ask and was given an afternoon plan instead
    if any(phrase in line for phrase in _REQUESTING_TIME):
        return None
    # A work block with no question in it is the leave row's line, and it has an answer of its
    # own ("put the dates in the leave system... going somewhere, or is it a week at home?").
    # The plan is for a person who asks what to do with the time, so a bare statement hands on.
    if (any(phrase in line for phrase in _WORK_BLOCK)
            and not _short_run(line)
            and not any(phrase in line for phrase in _ASKS)):
        return None
    # "any ideas for a film tonight" asks about a film: the plan for the evening answers a
    # question nobody asked, and the film row has the answer. Asked after the guards above, so a
    # free block said plainly ("i have a week off with a newborn, any ideas for the baby") keeps
    # the plan it came for.
    if _ideas_about_a_thing(understood):
        return None
    # ...and a complaint named in the line is the complaint's question, not the free time in it:
    # "i have toothache at the weekend, what can i do" is the toothache card's. The subject has
    # to be named, so "what should i do tonight, im exhausted" keeps the evening plan.
    if _about_a_thing_the_person_has(understood):
        return None
    # The free block is what this card is about, so a line that names a thing of its own is
    # asking about that thing and not about the time it has in it. "any ideas for a film
    # tonight" is a film to watch, "give me three ideas for a cheap date" is a date, and
    # "what can i do with a bag of apples this weekend" is about the apples: all three were
    # given a plan for the evening or for a free day instead of an answer about the thing they
    # named. This is the last stand-down, after the rows above that answer a named thing on
    # purpose (a new baby, a party, a wedding, a month), because those are the answers to the
    # thing the line names, not plans given in place of one.
    if _names_a_thing_of_its_own(understood):
        return None
    # a present is the gift rows' question, and the guest numbers are not the answer to it
    if any(phrase in line for phrase in _GIFT_ASK):
        return None
    if any(word in line for word in ("this afternoon", "free afternoon", "afternoon off")):
        plan = DAY_PLAN
    elif any(word in line for word in ("day off", "days off", "free day")):
        plan = DAY_OFF_PLAN
    elif any(word in line for word in _THE_EVENING):
        plan = EVENING_PLAN
    elif ((_short_run(line)
           or any(word in line for word in ("few days", "couple of days")))
          and not any(word in line for word in ("week off", "a week off", "weeks off",
                                                "whole week", "week free"))):
        # a few days off is a day-at-a-time plan: the two nights away is a week's shape, and
        # giving it to a long weekend was worse than the answer it replaced.
        plan = DAY_PLAN
    elif any(word in line for word in WEEK_OFF):
        plan = WEEK_PLAN
    else:
        plan = WEEKEND_PLAN
    if plan is WEEK_PLAN and any(word in line for word in MONEY_WORDS + _MONEY_ONLY):
        plan = WEEK_PLAN_SKINT
    if plan is WEEK_PLAN:
        if any(word in line for word in ("summer", "hot", "heat", "sunny", "sunshine")):
            plan = plan + " " + SUMMER_WEEK
        elif any(word in line for word in ("winter", "autumn", "frost", "snow", "dark")):
            plan = plan + " " + WINTER_WEEK
    if any(word in line for word in MONEY_WORDS):
        plan = plan + " " + NO_MONEY
    return plan

# What one piece of baby gear costs, as it is asked about on its own. The row used to answer with
# the whole first-shop list, so "how much does a decent pram cost" opened on a cot mattress: the
# question is one piece and the answer has to open on that piece (STYLE.md, the answer in the
# first sentence). A fault ("the brake is sticking", "the wheels squeak") is the same piece, and
# it is a repair rather than a price.
_BABY_GEAR = (
    (("pram", "prams", "pushchair", "pushchairs", "buggy", "buggies", "stroller", "strollers",
      "travel system"), "pram",
     "A pram is £150 to £400 new and £60 to £150 second-hand, and what matters is that it "
     "folds into the car and lies flat for a newborn. A second-hand one is fine if the frame is "
     "straight, the brakes hold and the fabric washes."),
    (("carrier", "carriers", "sling", "slings", "baby carrier", "baby sling"), "carrier",
     "A carrier or sling is £30 to £90, and it is the easy one on a bus, on stairs and in the "
     "first weeks; a pram carries the shopping and the sleeping baby. Most people end up with "
     "both, a sling first and a pram from about three months."),
    (("cot", "cots", "cot bed", "cotbed", "crib", "cribs", "moses basket", "travel cot"), "cot",
     "A cot is £100 to £250 new and £30 to £80 second-hand. The cot itself can be second-hand, "
     "but the mattress has to be new and firm and fit with no gaps round the edge, 120 by 60cm "
     "for a cot and 140 by 70cm for a cot bed. A Moses basket is for the first months only."),
    (("car seat", "car seats", "carseat", "carseats", "i-size", "isofix", "infant carrier"),
     "car seat",
     "A car seat is £80 to £250 new and it is the one piece not to buy second-hand unless you "
     "know its history: a seat that has been in a crash may look fine and still be spent. i-Size "
     "(R129) is the newer standard, and how it fits your car matters more than the brand."),
    (("high chair", "highchair", "high chairs"), "high chair",
     "A high chair is £25 to £150 and it can wait until six months, so it is the one piece you "
     "leave: a £25 one that wipes clean and has a footrest does the job."),
    (("baby monitor", "monitor", "monitors"), "baby monitor",
     "A baby monitor is £30 to £120 and it is a comfort rather than a must: it does not stop "
     "anything happening, so a cheap audio one beside the cot is enough."),
)

# A wheel, a brake or a handle is the pram being mended, and no price list answers it.
_BABY_GEAR_FAULT = ("squeak", "squeaks", "squeaking", "squeaky", "sticking", "stuck", "jammed",
                    "jam", "wobbly", "loose", "broken", "broke", "snapped", "wont fold",
                    "won't fold", "wont push", "won't push", "dragging", "rusty", "rust",
                    "cracked", "torn", "rips", "ripped", "fraying", "buckle", "buckles",
                    "harness", "brake", "brakes", "wheel", "wheels", "axle", "axles", "handle")

_BABY_GEAR_MEND = ("Squeaking or sticking wheels are the axle: a drop of silicone spray or a dry "
                   "PTFE lubricant on each axle and the grit wiped off the wheels, and a brake "
                   "that will not hold wants its little spring or cable adjusting. A wobbly "
                   "handle is a bolt inside the frame to tighten, a torn hood or seat is a "
                   "replacement cover from the maker, and a bent frame is the one fault that "
                   "means a new pram rather than a mending job.")


def _gear_named(words):
    """The pieces of gear the line names, in the order they are in the table."""
    return [name for keys, name, _said in _BABY_GEAR if any(_has_word(words, key) for key in keys)]


def _has_word(words, word):
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", words) is not None


def _a_piece_of_baby_gear(memory, understood):
    """The one piece the line is about, answered first, or the whole first shop.

    Every line that reached this row used to get the entire list, so the price of a pram opened
    on a cot mattress and a pick between a pram and a carrier was not answered at all.
    """
    words = _words_of(understood)
    named = _gear_named(words)
    fault = any(_has_word(words, word) for word in _BABY_GEAR_FAULT)
    if fault and not named:
        # "why do the wheels keep squeaking" after a pram: the piece is carried, not said
        carried = (memory or {}).get("topic") or {}
        topic = str(carried.get("text") or "").lower()
        named = _gear_named(topic)
    if fault and named:
        return _BABY_GEAR_MEND
    if len(named) >= 2 and ("which" in words or "better" in words or " or " in " %s " % words
                            or "versus" in words or "vs" in words):
        said = {name: sentence for _keys, name, sentence in _BABY_GEAR}
        pair = " ".join(said[name] for name in named[:2])
        return ("Whichever you use most is the one to spend on. " + pair).strip()
    if len(named) == 1:
        for keys, name, sentence in _BABY_GEAR:
            if name == named[0]:
                return sentence
    return ("Buy second-hand for all of it except the mattress: a cot (mattress 120 by 60cm) or "
            "cot bed (140 by 70cm) with a new firm mattress that fits with no gaps, a car seat "
            "that has not been in a crash and whose history you know - i-Size (R129) is the newer "
            "standard, and how it fits your car matters more than the brand - and a pram that "
            "folds small enough for your car and lies flat for a newborn. Prices: a new pram "
            "£150 to £400, second-hand £60 to £150, a cot £100 to £250 new. You need little "
            "else at the start (six babygros in two sizes, nappies, muslins); a monitor is a "
            "comfort rather than a must, and a high chair can wait until six months.")


def _words_of(understood):
    """The line, and the words it was read as, in one lowered string."""
    parts = [(understood or {}).get("clean"), (understood or {}).get("text")]
    parts.extend((understood or {}).get("words") or ())
    return " ".join(str(part) for part in parts if part).lower()


def _dish_for_tonight(memory, understood):
    """The recipe for the dish the line names for an evening, or None.

    Only the names cooking.RECIPES already holds, so this row answers with the same words the
    kitchen table does: "curry" is the 40-minute curry card, and a dish nobody has written a
    card for is left to the module that might still know it.
    """
    said = _words_of(understood)
    found = []
    for aliases, keys, body, avoid in RECIPES:
        if not any(re.search(r"\b" + re.escape(alias) + r"\b", said) for alias in aliases):
            continue
        if any(re.search(r"\b" + re.escape(word) + r"\b", said) for word in avoid):
            continue
        found.append((max(len(alias) for alias in aliases
                          if re.search(r"\b" + re.escape(alias) + r"\b", said)), body))
    if not found:
        return None
    # the longest name wins, so "curry paste" is not answered with the curry from scratch
    return max(found, key=lambda pair: pair[0])[1]
# A birthday for a grown-up is not a children's party: "how do i plan a birthday party for my
# mum" was answered with age-plus-one guests and a bag for the way home, and a 60th asking how
# many people to invite got nothing at all. Two entries, each standing down on the other's
# words, because the two plans differ in what they cost and in what goes wrong.
_ADULT_PARTY = (
    "Count the people first, because it decides the room and the food: 8 to 12 is easy to cook "
    "for at home, 30 to 40 is about as many as a house takes, and a pub's back room or a "
    "restaurant takes 20 to 60 for a similar price to a hall. Pick the day and send one message "
    "with the date, time, place and whether it is a meal or drinks, because \"let me know if you "
    "can make it\" gets half-answers. Keep the food to things made the day before - a pie or a "
    "chilli kept warm, a baked ham, bread, two salads and a bought cake - and give two people one "
    "job each, drinks and cards and the speech, so you are not doing all of it. Send the "
    "invitations three to four weeks ahead, six for a big do or a date near Christmas, and ask for "
    "replies by a date a week before. Budget £10 to £15 "
    "a head for a buffet at home and £25 to £40 in a restaurant's back room, drink on top.")

# The children's party, so one entry can hand a line on to it: a birthday for a five-year-old
# and a birthday for a mother are the same words in a different order, and only the person and
# the age in the line tell them apart.
_KIDS_PARTY = (
    "Two hours and about age-plus-one guests is the sweet spot: one venue or one big activity, "
    "food that can be made the day before, and a bag for the way home. At home it costs around "
    "£5 a head but you need a wet-weather plan and one adult per four children; a hall or "
    "soft-play party at £10 to £15 a head buys you both.")

# Who the party is for, when the line names a child rather than a grown-up: "my son" or "my
# daughter" with no age is a child's party, and an age under thirteen settles it either way.
_CHILD_AT_PARTY = ("kid", "kids", "child", "children", "childs", "toddler", "toddlers",
                   "son", "sons", "daughter", "daughters", "grandson", "granddaughter",
                   "grandchild", "grandchildren", "godson", "goddaughter", "school",
                   "nursery", "soft play", "playcentre", "reception class", "year one")
_AGE_AT_PARTY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\b")

# A landmark birthday said as an age rather than as a party: "my mum is 70 next week what can i
# do" names the person, the age and the day, and the row that plans a do for a grown-up never
# heard "70" - the words that reach it are "70th", "birthday" and "for her birthday", and this
# line says none of them. It was answered "I'm not sure about that one, sorry". The age has to
# be a round one and a grown-up one, and a day has to be near, so a car's age and a child's
# birthday stay where they were.
_A_MILESTONE_PERSON = re.compile(
    r"\b(?:mum|mums|mom|moms|mam|mams|dad|dads|father|mother|nan|nans|nana|nan's|gran|grans|"
    r"granny|grandma|grandad|grandpa|grandmother|grandfather|aunt|auntie|uncle|sister|brother|"
    r"wife|husband|partner|mother in law|father in law|she|he|son|sons|daughter|daughters|"
    r"grandson|granddaughter|grandchild|godson|goddaughter|nephew|niece|kid|kids|child|children)\b")
# A child's birthday said the same way ("my son is 7 next week what should we do"), where the age
# is the child's own and the children's plan is the answer rather than the grown-up one.
_A_CHILD_AT_A_MILESTONE = re.compile(
    r"\b(?:son|sons|daughter|daughters|grandson|granddaughter|grandchild|godson|goddaughter|"
    r"nephew|niece|kid|kids|child|children|boy|girl|toddler)\b")
_A_MILESTONE_AGE = re.compile(
    r"\b(?:is|turns|turning|will be|going to be|hits|becomes)\s+(?:the age of\s+)?(\d{1,2})\b")
_A_MILESTONE_SOON = re.compile(
    r"\b(?:next (?:week|month|weekend|saturday|sunday|friday|year)|this (?:week|weekend)|"
    r"on (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|soon|coming up|"
    r"in \w+ (?:weeks|days))\b")


# A line that asks for a present rather than for a do. "What should i get my mum who is 70 next
# week" and "present ideas for my dad who turns 60" carry the same age and the same day as the
# party lines, and the thing asked for is a gift: a noun for one, or a verb of buying, giving or
# making with the person as its object. "What can i do for her" and "how should we celebrate"
# name no gift, so the party row keeps those.
_A_PRESENT_ASKED = re.compile(
    r"\b(?:present|presents|gift|gifts)\b"
    r"|\bwhat\s+(?:should|shall|can|could|do|would)\s+(?:i|we)\s+(?:get|buy|give|make|send)\b"
    r"|\b(?:get|buy|give|make|send)\s+(?:her|him|them|my\s+(?:mum|mom|mother|dad|father|"
    r"gran|grandma|grandad|granny|nan|nana|wife|husband|partner|son|daughter|sister|brother|"
    r"friend|parents?))\b"
    r"|\bideas?\s+(?:for|of)\s+(?:a\s+)?(?:present|gift)\b")


# The same reading as phrases, because a row is reached by its own key words: "is 70", "turns 60",
# "turning 80". The ages are every grown-up one and the verbs are the ways an age is said of
# somebody; the guard is what keeps a boiler's age, a child's birthday and a line with no ask in
# it away from the plan.
_MILESTONE_AGES = tuple(range(1, 100))
_MILESTONE_SAID = tuple("%s %d" % (verb, years)
                        for years in _MILESTONE_AGES
                        for verb in ("is", "turns", "turning", "will be"))


def _a_milestone_said_as_an_age(understood):
    """True when the line is somebody's birthday, said as an age and a day.

    The age is a round one and a grown-up one, a day has to be near, and the person has to be
    named: an age said of a boiler or a car is not a do, and a child's birthday has its own plan.
    """
    line = " ".join([str((understood or {}).get("clean") or "")]
                    + [str(word) for word in ((understood or {}).get("words") or ())]).lower()
    if not _A_MILESTONE_PERSON.search(line):
        return False
    age = _A_MILESTONE_AGE.search(line)
    if not age:
        return False
    years = int(age.group(1))
    if years < 18 and not _A_CHILD_AT_A_MILESTONE.search(line):
        return False
    # A birthday is also how people say which present they want: "what should i get my mum who
    # is 70 next week" is a thing to give, not a do to plan, and the gift answer was there for
    # the asking before this row existed. The age and the day are the same words in both lines,
    # so what the line asks for is what tells them apart.
    if _A_PRESENT_ASKED.search(line):
        return False
    return bool(_A_MILESTONE_SOON.search(line))


def _party_plan(memory, reading):
    """The grown-up party plan, or the children's one when the line names a child.

    "how do i plan a birthday party for my mum" and "...for my son" reach the same entry, and
    an age-plus-one answer is wrong for one of them. The age in the line settles it when it is
    there ("my sons 40th" is a grown-up do), and a child word settles it when it is not.
    """
    clean = str((reading or {}).get("clean") or "").lower()
    words = " ".join(str(word) for word in ((reading or {}).get("words") or ()))
    line = clean + " " + words
    ages = [int(found) for found in _AGE_AT_PARTY.findall(line) if 1 <= int(found) <= 99]
    if ages:
        return _KIDS_PARTY if min(ages) < 13 else _ADULT_PARTY
    if any(re.search(r"\b" + word + r"\b", line) for word in _CHILD_AT_PARTY):
        return _KIDS_PARTY
    return _ADULT_PARTY


def _not_a_gift_ask(understood):
    """Whether the line is asking for a thing to give rather than for the do itself.

    "what should i get my mum for her birthday" holds "birthday" and an ask, which is enough
    for the party row, and the gift and the guest list are different answers. "how many people
    should i invite to my mums 60th" names the do and not a present, so it keeps the plan.
    """
    line = " " + str((understood or {}).get("clean") or "").lower() + " "
    line += " ".join(str(word).lower() for word in ((understood or {}).get("words") or ())) + " "
    return not any(phrase in line for phrase in _GIFT_ASK)


def _not_a_gift_or_a_date(understood):
    """Both of the party row's stand-downs, so the row keeps neither a present nor a date.

    The date question and the gift question arrive in the same words ("what should i do for my
    mum's birthday this weekend" is neither), so the row asks both before it answers.
    """
    return _not_a_gift_ask(understood) and _not_a_date_question(understood)


_KITCHEN_PLAN = (
    "Plan a kitchen round the three points that get used most - the sink, the hob and the fridge: "
    "any two of them want 1.2 to 2.7 metres between them, the sink wants a clear 600mm of worktop "
    "on each side, and the hob wants space to put a pan down on the right and nothing flammable "
    "beside it. Then list what you need before what you want: deep drawers beat a bottom cupboard, "
    "a socket every metre of worktop, a tall cupboard for the ironing board and the hoover. Mark "
    "where the pipes, the soil stack and the door swing are before you fall in love with a layout, "
    "because moving a drain is most of a kitchen's cost. Tape the outline on the floor and walk it "
    "for a week before you order.")

_BATHROOM_PLAN = (
    "Plan a bathroom round the soil pipe: the toilet has to stay where the drain already is unless "
    "you raise the floor for a new one, so put the toilet and the bath first and the basin where "
    "there is wall for it. A bath needs 1.7m and a shower 900mm square, and leave 700mm clear in "
    "front of the basin and 600mm beside the toilet. Decide the shower before the tiles, because a "
    "wet room floor has to fall to a drain and a screen cannot be added later, and set the shower "
    "valve about 1.1m off the floor so nobody has to reach. A bathroom also needs an extractor that "
    "moves about 15 litres a second, or the paint and the grout will go.")


_UTILITY_PLAN = (
    "Plan a utility room round the machines and the water: the washing machine and the dryer "
    "want an outside wall for the vent and the plumbing, a sink close to the drain, and a "
    "worktop over the appliances at about 900mm so there is a surface to fold on. Leave 600mm "
    "clear in front of every door you have to open, put the boiler behind a cupboard you can "
    "still get into, and keep a shelf at eye height for powder, pegs and the iron - it is the "
    "walk-through clutter, not the size of the room, that makes a utility room useless.")


# The rooms this row has a card for. The card is only the answer when the line names one of
# them: the row's other key words - redo, refit, refurb - are about the work and not about a
# room, so "im planning to redo my cv" reached here on "planning" plus "redo" and got the
# kitchen's work triangle. A plan for a room the line never mentions is a lecture about a
# room of the bot's choosing, so the row steps back and lets the line be what it was about.
_A_PLANNED_ROOM = ("kitchen", "kitchens", "bathroom", "bathrooms", "bath", "baths", "shower",
                   "showers", "toilet", "toilets", "loo", "loos", "ensuite", "en suite",
                   "wet room", "utility", "utility room", "laundry", "laundry room",
                   "boot room", "small room", "spare room", "dining room")


def _a_room_plan(memory, understood):
    """The room the line names, planned in its own terms, or None for a line that names none.

    "how do i plan a new bathroom" was answered with the kitchen's work triangle, because one
    card served both rooms and a kitchen's numbers are not a bathroom's.
    """
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not re.search(r"(?<![a-z0-9])(?:" + "|".join(re.escape(word) for word in _A_PLANNED_ROOM)
                     + r")(?![a-z0-9])", said):
        return None
    if any(word in said for word in ("utility", "laundry", "boot room")):
        return _UTILITY_PLAN
    if any(word in said for word in ("bath", "bathroom", "shower", "toilet", "loo", "ensuite",
                                     "wet room")):
        return _BATHROOM_PLAN
    return _KITCHEN_PLAN


ENTRIES = [
    entry("free-time-plan",
      (FREE_TIME,
       ("do", "doing", "go", "going", "ideas", "idea", "suggestions", "something", "anything",
        "plan", "plans", "bored", "nothing", "saturday", "sunday",
        # the ask said as a request for advice: "i have a week off in the autumn any tips" holds
        # a free block and a question, and the key wanted one of the words above only.
        "tips", "tip", "advice", "suggest",
        # the free block itself, so the row is in reach when the ask is only implied
        "days off", "day off", "time off", "off work",
        # a block stated and nothing asked: "i have a long weekend free" was echoed back
        "weekend free", "long weekend", "weekend to myself",
        # the season stands in for the ask when the block is stated, and the ask group alone does
        # not score the row: "i have three weeks off in the summer" was echoed back
        "summer", "winter", "spring", "autumn", "no plans", "well", "use", "spend", "sort")),
      _free_time,
      # "the weekend" is not only a free weekend: it is also when the dentist is shut and when
      # half a cabbage is left over, and those lines belong to toothache and fridge-life. The
      # avoid list below is what keeps them out; the bias is only there so "what should i do
      # with my day off" is the free-day plan rather than the leave-request form.
      ask=FREE_TIME_ASK, bias=2,
      # ... and the free block has to be the subject of the line: "any ideas for a film tonight"
      # and "im trying to sort out my daughters birthday party next weekend" each name a thing
      # to be about, and the row that answers that thing is the answer, not the shape of a day.
      guard=_a_stretch_of_time_to_fill,
      # a recipe, a job around the house and the children's day out are their own answers
      avoid=("cook", "cooking", "recipe", "dinner", "tea", "lunch", "breakfast", "bake",
             "shop", "shopping", "supermarket", "kids", "children", "toddler", "baby",
             "car", "mot", "van", "garage", "boiler", "washing machine", "essay",
             "coursework", "assignment", "deadline", "tax return", "invoice",
             "homework", "revise", "revision", "exam", "at work", "office", "shift",
             "overtime", "rota",
             "weather", "rain", "forecast", "train", "bus", "flight", "traffic",
             # something that hurts at the weekend is a health question, not a free afternoon
             "ache", "aches", "aching", "pain", "toothache", "tooth", "hurt", "hurts",
             "ill", "sick", "fever", "temperature", "rash", "dizzy", "dentist", "doctor",
             "pharmacy", "hospital", "symptom", "symptoms", "headache",
             # "half a cabbage left from Sunday, what can i do with it" is a use-up question
             "left", "leftover", "leftovers", "left over", "use up", "using up", "with it",
             "with them", "with these", "goes off", "go off", "out of date",
             # a weekend somewhere is a place question: city-guide and travel own it
             "there", "trip", "break away", "visit", "visiting", "hotel", "city", "abroad",
             "travel", "flights", "in rome", "in paris", "in london", "in new york",
             # a weekend or a night somewhere is a trip with its own answer: "any ideas for a
             # cheap weekend away" was the three-things-at-home card, while travel's
             # weekend-away has the train, the shoulder season and the price for two nights.
             # Only the phrasings that mean going away are here, so "what should i do this
             # weekend" and "a free weekend with no money" are still this row.
             "weekend away", "weekend break", "city break", "city breaks", "night away",
             "nights away", "mini break", "short break", "getaway", "days away",
             "couple of nights", "few nights away", "two nights away", "weekend in",
             # a plan offered to someone who has just said how low they feel is the wrong
             # reply: "what should i do this weekend i feel really low" wants a person, and
             # the mood words are the tell. The line falls back to what it got before.
             "feel low", "feeling low", "feel really low", "feeling really low",
             "feel down", "feeling down", "feel really down", "feeling really down",
             "feel sad", "feeling sad", "feel depressed", "feeling depressed", "depressed",
             "feel anxious", "feeling anxious", "anxious", "feel lonely", "feeling lonely",
             "lonely", "feel miserable", "feeling miserable", "miserable",
             "feel rubbish", "feeling rubbish", "feel awful", "feeling awful",
             "feel terrible", "feeling terrible", "feel like crying", "cant be bothered",
             "no energy", "hate everything",
             # "can i have the day off on friday" is a request to a boss and the ask script is
             # the right answer to it; the plan for the day is what you do once the day is yours.
             "can i have", "can i take", "can i book", "can i get", "could i have", "could i take",
             "may i have", "may i take", "am i allowed", "is it ok if i", "is it okay if i",
             "do i have to book", "my boss", "my manager", "ask for it off",
             # and the same for the ask said as an intention: "i want to take a day off next
             # month" was given the goal hedge, because this row now scores on the day off and
             # its own month stand-down leaves nothing behind it.
             "take a day off", "take a week off", "take time off", "take some time off",
             "book a day off", "book a week off", "book time off", "want to take", "want to book",
             "request a day off", "request a week off", "request time off", "put in for",
             "hoping to take", "hoping to book",
             # "is the tip open on bank holiday monday" is a venue's hours on a day, not a plan
             # for the day: see A_HOURS_ASK in bot/knowledge/lookup.py
             ) + A_HOURS_ASK),

    # --- a move ------------------------------------------------------------------
    entry("move-house-plan",
          (("moving house", "moving home", "moving flat", "moving out", "house move",
            "move house", "move flat", "moving next month", "packing up the house",
            # "how do i move house" was a shrug: the plan words below are what a line says when
            # it is asking for the plan, and this plain phrasing of it said none of them.
            "move to a new house", "move to a new flat", "move into a new house",
            "move into a new flat", "move into my first",
            # The ask, spelled out as the phrase rather than as loose words: "how do i" alone
            # pulled in "how do i register with a doctor after moving house", which is the
            # registration row's question and answers better there.
            "how do i move house", "how do i move home", "how do i move flat",
            "how do i move out", "how to move house", "how to move home",
            "how do i move to a new house", "how do i move to a new flat",
            "what do i need to move house", "what do i need to move home",
            # "how do i plan a move" and "tips for moving out" name the move without the word
            # house or flat, and the guard above is what tells them from a move abroad or a move
            # at work.
            # "what should i do first when moving" named the move with the participle only:
            # "moving house" and "moving home" are the phrases this row keys, and the plainest
            # way of saying it - when moving - was a search hedge.
            "when moving", "when we move", "when i move", "when you move", "if we move",
            "plan a move", "planning a move", "plan the move", "planning the move",
            "organise a move", "organising a move", "organize a move", "organizing a move",
            "a move to plan", "before a move", "before the move", "the move go",
            "prepare for a move", "prepare to move", "get ready for a move",
            "get ready to move", "ready for a move", "start with a move",
            "start on a move", "start with moving", "sort out a move",
            "moving out of my", "moving out next"),
           ("plan", "planning", "start", "organise", "organize", "checklist", "prepare",
            "sorted", "first", "ahead", "organise", "where do i", "tips", "advice",
            # The verb itself: the ask phrase above is one word of the key, and the score wants
            # two, so the plan could not open on the plainest ask of all. "move" here is the
            # verb in a line that already says the house is moving, and the rows that answer a
            # doctor, a school or a price hold those words out of this one's way below.
            "move", "moving", "moved")),
          "Work back from the date: book a van or removals six to eight weeks out, and tell the "
          "council, energy, water and broadband a month before, because the bills follow you. Box "
          "the things you don't use three weeks out, label every box with its room, and pack one "
          "bag with a kettle, mugs, loo roll, bedding and chargers for the first night.", ask=PLAN_ASK,
          guard=_a_household_move_or_a_named_move,
          # A move that names the paperwork, the doctor or the price is a different answer:
          # "how do i register with a doctor after moving house" is the registration row, and
          # "how do i move house cheaply" is the man-with-a-van row.
          # The paper trail is its own row and answers "what do i need to tell" better than a
          # timeline does, so a line naming the council, a doctor or a school is not this one.
          avoid=("council", "doctor", "gp", "surgery", "dentist", "school", "register",
                 "council tax", "notify",
                 "cheap", "cheaper", "cheapest", "cheaply", "cost", "costs", "price", "how much",
                 "van", "removals", "man with a van",
                 # A hope is not a plan: "im hopin to move out soon" wants to be met, and the
                 # chat module's reflective reply is better than a list of van bookings.
                 "hoping", "hopin", "hope to move", "hopin to move", "hopes to",
                 "thinking of moving", "thinking about moving", "dream of moving",
                 "dreaming of moving", "want to move out", "cant wait to move",
                 # telling the landlord is the notice letter, and it was answered with the van
                 # timeline: "when should i tell my landlord im moving out"
                 "tell my landlord", "tell the landlord", "landlord", "landlady",
                 "letting agent", "notice period", "give notice",
                 "can't wait to move", "one day",
                 # A move that has hurt them is a body question: "i helped my mate move house
                 # now my back is killing me" was given the six-to-eight-week van timeline.
                 "my back", "back is killing", "back hurts", "bad back", "sore back",
                 "pulled my back", "hurt my back", "done my back",
                 # packing is its own answer, and it is a better one than the timeline:
                 # "how do i pack for moving house" was the boxes row before these words.
                 "pack", "packing", "packed", "boxes", "box up", "label", "labels",
                 "bubble wrap", "what to pack", "declutter", "unpack",
                 # telling the children is a thing to say, not a thing to book: "how do i tell my
                 # kids we're moving house" took the van-and-council timeline, and home's
                 # moving-with-kids row is the answer. The tell-frame stands this row down
                 # whatever the subject, because the paperwork row has its own words.
                 "how do i tell", "how to tell", "how do i explain", "what do i say",
                 "tell the kids", "tell my kids", "tell the children", "tell my children",
                 "tell my son", "tell my daughter", "break the news", "explain to my",
                 "how do i break",
                 # A move with children in it is the telling, not the timeline: "how do i organise
                 # a move with kids" was answered "tell them as soon as it is certain" on main,
                 # and the phrase "organise a move" added to the key above took it back to the
                 # van and the council. The children's card is the better answer to that line.
                 "with kids", "with children", "with a baby", "with a toddler", "with a child",
                 "my kids", "my children", "my son", "my daughter", "pregnant", "my baby",
                 "toddler", "toddlers", "kids", "children",
                 # Moving in with someone is about money and habits, not a van: "how do i prepare
                 # to move in with my partner" answered "agree the boring things before the
                 # boxes" on main, and the wider move key took it.
                 "with my partner", "with a partner", "move in with", "moving in with",
                 "moved in with", "move into his", "move into her", "my girlfriend",
                 "my boyfriend", "my partner")),

    # --- a birthday nobody has written down ---------------------------------------
    # A date question about a birthday is not a party: "when is my mums birthday" was told the
    # guest numbers and "what date is my dads birthday" a dress code. Nothing here can know the
    # date - the memory store answers it when the person has said it, which is why this row keeps
    # "party", "present" and "invite" out - so the row says what it cannot do and gives the thing
    # that does work.
    entry("birthday-date",
          (("when is", "when's", "whens", "what date", "which date", "what day"),
           ("birthday", "birthdays")),
          "I can't look a birthday up, and guessing one is worse than asking: a text now, and the "
          "answer goes in your phone with a reminder a week before. People rarely mind being "
          "asked.",
          avoid=("party", "parties", "invite", "invites", "invitations", "present", "presents",
                 "gift", "gifts", "buy", "plan", "planning", "many", "venue", "cake", "food",
                 "guest", "guests", "surprise", "ideas", "organise"),
          bias=1),

    # --- a landmark birthday said as an age --------------------------------------
    # "my mum is 70 next week what can i do" names the person, the age and the day, and none of
    # the words the do's own row is keyed on ("70th", "birthday", "for her birthday"), so it was
    # answered "I'm not sure about that one, sorry". The age is the subject here and the guard is
    # what keeps it to a person: an age said of a boiler or a car is not a do, and a line with no
    # ask in it is somebody telling you about their week.
    entry("party-milestone",
          (_MILESTONE_SAID,
           ("do", "doing", "what", "how", "should", "could", "can we", "ideas", "any",
            "anything", "something", "plan", "planning", "organise", "help", "sort", "get",
            "make", "give")),
          _party_plan, ask=PLAN_ASK, guard=_a_milestone_said_as_an_age, bias=1,
          avoid=("years old", "year old", "miles", "years", "kg", "degrees")),

    # --- a party ----------------------------------------------------------------
    entry("party-grownup",
          (("birthday party", "birthday for", "party for my", "party for her", "party for him",
            "surprise party", "anniversary party", "retirement party", "retirement do",
            "big birthday", "40th", "50th", "60th", "65th", "70th", "75th", "80th", "90th",
            "my mums birthday", "my dads birthday", "my mums 60th", "mums 70th",
            # The do said as "a party" rather than as a person's birthday: "how many people
            # should i invite to a party" and "when should i send the invitations" reached
            # nothing, because both key words fell in the second group and the first held only
            # phrasings about whose birthday it is. A party is the subject, so it may open the
            # row; the long stand-down list below is what keeps presents, dress codes, dinner
            # parties and christenings out.
            "a party", "the party", "house party", "party at home", "birthday", "birthdays",
            "invite to a party", "people to invite", "how many to invite", "guest list",
            "invitations", "the invitations", "send invitations", "send the invitations",
            # a landmark birthday for an older relative, asked as "what can we do for her"
            "my nans birthday", "my nans 80th", "my grans birthday", "nans 80th", "grans 80th",
            "her 80th", "her 70th", "her 90th", "his 70th", "his 80th", "for her birthday",
            "for his birthday", "what can we do for",
            # a leaving do, a retirement do and a work do are parties with a guest list and a
            # room, which is what this row answers: "im organising a leaving do" was
            # "Noted: you're organising a leaving do." A hen do and a stag do stay out - the
            # weekend-away row answers them ("one city, two nights and one big thing booked
            # ahead"), and a guest list is the weaker answer to a trip.
            "leaving do", "leaving party", "retirement do", "work do", "christmas do"),
           ("plan", "planning", "start", "first", "organise", "organized", "invite", "how many",
            "how much", "food", "venue", "where", "ideas", "tips", "advice", "sorted",
            "guests", "guest list", "party",
            # and the ask as an ordinary question, which is how most of these arrive:
            # "what should i do for my mums 80th birthday" scored nothing at all and was
            # answered with a dress code, because "do" and "what" were in neither group.
            "do", "doing", "what", "how", "should", "want", "wanted", "throwing", "throw",
            "hosting", "host", "send", "sent", "when", "what can we do", "we do")),
          _party_plan, ask=PLAN_ASK,
          avoid=(
                 # "Leave" is the allowance as well as the leaving do, and the leaving shapes
                 # taught the matcher the plain word: "how much leave do i get" and "how many
                 # days leave do i have left" were both answered with the buffet numbers. A
                 # party plan never says any of the phrases below - they are the entitlement
                 # row's own key words - so the row steps back and lets it answer.
                 "annual leave", "days leave", "day leave", "much leave", "leave days",
                 "leave left", "leave balance", "leave allowance", "leave entitlement",
                 "holiday entitlement", "days off", "annual leave entitlement",
                 # A chat that has to be ended at a party is a conversation to close, not a
                 # party to plan: "a party" opened this row for every how-question with the
                 # word in it, so "how do i end a chat at a party" was told the buffet
                 # numbers. The talk is the subject of those lines.
                 "end a chat", "end the chat", "end a conversation", "end the conversation",
                 "chat at a party", "conversation at a party", "small talk", "stop talking",
                 "get out of a conversation", "nattering",
                 # A party somebody wants to get out of is not a party to plan: "how do i get
                 # out of going to a party" was told how many people fit in a back room, and
                 # the refusal shapes are all one row's in family.py (say-no).
                 "get out of", "dont want to go", "don't want to go", "do i have to go",
                 "cant come", "can't come", "make my excuses", "would rather not go",
                 "decline", "turn down", "say no", "back out of", "not going",
                 "kids party", "children's party", "childs party", "toddler party", "soft play",
                 # the same lines said with the talk as the subject: "how do i excuse myself from
                 # a party without being rude", "how do i get away from a cornered chat"
                 "conversation", "conversations", "chat", "excuse myself", "cornered",
                 "mingle", "mingling",
                 # A how-to about remembering the dates is not a party to plan: "how do i
                 # remember birthdays" was told how many people fit in a back room, because
                 # "birthdays" opens this row and "how" is one of its asks. The habit belongs to
                 # the forgetting rows in science.py.
                 "remember", "remembering", "forget", "forgetting", "forgot", "keep track",
                 "track of", "reminder", "reminders", "calendar", "diary", "list of birthdays",

                 "playcentre", "kids", "kid", "child", "children", "year old", "years old",
                 "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th",
                 "toddler", "toddlers", "nursery", "school", "dinner party", "buffet for",
                 "people coming over", "christmas party", "office party", "political",
                 "party wall", "hen do", "stag do", "wedding", "baby shower", "christening",
                 # a present for the person, and what to wear to their do, are their own answers:
                 # "present ideas for a 70th birthday" and "what should i wear to a 60th" were
                 # a gift and a dress code before this entry existed
                 "present", "presents", "gift", "gifts", "buy", "buying", "bought", "get her",
                 "get him", "get my", "get our", "card", "cards", "what to write",
                 "wear", "wearing", "put on", "putting on", "dress", "dress code", "outfit",
                 "outfits", "shoes", "what to get",
                 # and the same present question with the person named: "get my dad",
                 # "buying my sister" - the bare "get my" above takes "how do i get my
                 # toddler to sleep" too, so the present words carry their own object.
                 _A_PRESENT_FOR,
                 # the words that go in a card are the wishing rows' question, and "birthday"
                 # alone opened this row for them: "what should i write in a birthday card for
                 # my nan" was told how many guests to invite and what to feed them.
                 "what should i write", "what do i write",
                 "write in", "writing in", "message", "messages", "verse", "verses", "poem",
                 "poems", "wishes", "what to say", "what do i say",
                 # leaving is not planning: "how do i say goodbye at a party" and "how do i
                 # leave a party early" were both given the guest count and the buffet budget,
                 # because a party is the subject and nothing said this one was about the exit.
                 # The exit has its own script in wording.py, and the small-talk card beside this
                 # one stands down for the same words.
                 "say goodbye", "say goodbyes", "goodbye", "goodbyes", "say bye",
                 "leave the party", "leave a party", "leaving the party", "leaving a party",
                 "leave early", "leaving early", "slip away", "say my goodbyes", "head off",
                 "make my excuses", "when to leave", "how do i leave",
                 # The kitchen's own question is not a party to plan: "what should i cook for my
                 # mums 70th", "what to cook for a 60th birthday party" and "what food should i
                 # make for a party" were all told to count the people first and keep the
                 # numbers to 8 to 12, which answers the room and not the cooking. The dish is
                 # the ask, so the row stands down when the line says cook or make.
                 "what should i cook", "what to cook", "what should i make", "what food should i",
                 "what can i cook", "what can i make", "what should i serve", "what to make",
                 "what shall i cook", "what do i cook",
                 # the words inside the card are `card-birthday`'s answer, and "what should i
                 # write in a birthday card" was counting the people for the food instead
                 "card", "cards", "write in", "write on", "what to write", "what should i write",
                 "message in", "note in", "sign the",
                 # the same present said with the person rather than the noun: "what should i
                 # get my mate for his 40th" and "what should i get my mum for her birthday"
                 # counted the 40th and the birthday and were told how many to invite and what
                 # to feed them. The asking shape belongs to the gift rows.
                 "buy my", "get a", "buy a", "get for", "buy for",
                 "what should i get", "what do i get", "what can i get", "what shall i get",
                 "what could i get", "what would i get", "get them", "give them",
                 "something for", "present for", "gift for",
                 # "what is a good game for a party" asked for a game and got the guest count,
                 # the buffet budget and the invitation timings: the games row in entertainment
                 # names three that need nothing but a table, and the plan is not the answer.
                 "game", "games", "board game", "board games", "party game", "party games",
                 "what should we play", "something to play", "quiz", "games night"),
          bias=1,
          # Two stand-downs weigh on this row, and an `entry` takes one `guard=`, so they are one
          # guard. A birthday that has gone is not a party still to plan: "i forgot my mums
          # birthday, what do i do" was answered with the guest count and the buffet budget, and
          # what it asks is how to put it right. A present for the person the day belongs to is
          # not a party either, and the date question is asked by both of them.
          guard=lambda u: _not_a_gift_or_a_date(u) and _not_a_deed_of_their_own(u)),
    entry("party-kids",
          # The second group is the planning and the first is the party, and neither "how many"
          # nor "kids"/"children" belongs in the second: with those three words there, "how many
          # children do i have" satisfied both halves on its own and the memory store's count came
          # back as the age-plus-one guest rule. A line about a party has to say a party word.
          (("kids party", "children's party", "childs party", "birthday party",
            "birthday for", "party for a", "5th birthday", "6th birthday", "7th birthday",
            "8th birthday", "toddler party", "how many kids", "how many children",
            "invite to a birthday"),
           ("plan", "planning", "start", "idea", "ideas", "much", "activities", "food",
            "venue", "where", "organise", "invite", "cost", "decorate", "theme", "games",
            "cake", "guests", "party", "birthday", "toddler", "activities")),
          _KIDS_PARTY, ask=PLAN_ASK, guard=_not_a_count_of_their_own,
          # a birthday for a grown-up is the entry above, and the age-plus-one rule is wrong for
          # it: "how do i plan a birthday party for my mum" was given the children's party.
          avoid=("my mum", "my mom", "my dad", "my mother", "my father", "my husband",
                 "my wife", "my partner", "grandma", "grandad", "nana", "nan", "granny",
                 "40th", "50th", "60th", "65th", "70th", "75th", "80th", "90th",
                 "retirement", "anniversary", "grown up", "for adults",
                 # the words that go in a card are the card rows' answer, and the grown-up row
                 # says so in its own avoid: "what should i write in my daughters 5th birthday
                 # card" was two hours and age-plus-one guests, because this list had none of
                 # them. A card, a message or wishes is not a party to plan.
                 "card", "cards", "message", "messages", "wishes", "what to write",
                 "what should i write", "what do i write", "write in", "message in",
                 # What dish to carry to somebody else's party is the buffet row's question,
                 # not the party plan's: "about ten kids are coming, what food should i bring"
                 # was told the age-plus-one guest rule, which then took the follow-up "and
                 # some games" with it ("Same answer, and it covers this: two hours and about
                 # age-plus-one guests ...") instead of the games card.
                 "what food should i bring", "what food should i take", "what food can i bring",
                 "what food can i take", "what food do i bring", "what food to bring",
                 "bring a dish", "dish to bring", "food to bring", "what should i bring",
                 "what can i bring", "anything i can bring")),

    # --- a wedding --------------------------------------------------------------
    entry("wedding-plan",
          (("wedding", "weddings", "marriage", "civil partnership", "getting married",
            # "do we need to give notice to marry" says marry, not marriage
            "marry", "marrying", "engagement party", "hen do", "stag do",
            # the same subject said with "get married", "we are getting married" and the
            # notice itself, which people name with no other word in the line
            "get married", "married", "we are getting married", "give notice",
            "notice of marriage", "notice to marry", "wedding day",
            # the bookings and the venue name the wedding without the word: "how far ahead
            # should we book the venue" and "when should we book the photographer" reached
            # nothing at all, because neither says wedding
            # not the bare "the venue": "i booked the venue for the wedding" is the plan ack,
            # not a request for the guest list, so only the booking ask opens the row
            "book the venue", "book a venue", "the wedding venue",
            "book the photographer", "book a photographer"),
           # "how much does a register office wedding cost" is not here on purpose: the
           # ceremony fee is the registry, council and certificate answer, and this row's money
           # paragraph talks about guest lists, so a bare cost word left it answering a question
           # about a room with a rule about headcounts
           ("plan", "planning", "budget", "guest list", "guests", "afford", "cheap",
            "start", "organise", "venue", "save",
            # the ask for the order: "we are getting married in june what should i sort first"
            # and "what should i sort first for a wedding" asked for the order of the steps and
            # the row had no word for it - the first got a search hedge and the second the
            # booking-a-room card for a trip.
            "first", "sort", "sort first", "sort out first", "pick", "pick first", "order",
            "prioritise", "priorities", "before what",
            # "im getting married what do i need to do" asks for the paper trail, which is the
            # thing people miss: give notice, the registrar, the witnesses
            "what do i need", "need to do", "whats needed", "what's needed", "paperwork",
            # "what papers do i need to get married" and "what do i need to bring to give
            # notice" say papers and bring, where the row had only paperwork and notice.
            "papers", "document", "documents", "bring", "what to bring",
            "notice", "notice of marriage", "registrar", "register office", "legal", "admin",
            "witness", "witnesses", "arrange",
            # "how do i get married" and "how do we get married" name the subject and ask the
            # how: the asking is how the subject is put, and a line with no plan, venue or
            # paperwork word in it is the ordinary way people ask, so these are key phrases.
            "how do i get married", "how do we get married", "how to get married",
            "how do you get married", "how do i marry", "how do we marry",
            "how do i arrange", "how do we arrange", "what do i do", "what do we do",
            "what do i need to do", "where do i start", "how does it work",
            # the count and the calendar: "how many guests for a wedding" reached the hotel row
            # on "for a wedding" and "book", and "how many guests should we have" reached the
            # buffet card, because neither shape was in this row's key at all
            "how many guests", "how many people", "how many should we invite",
            "how many to invite", "number of guests", "how big", "size of the wedding",
            "far ahead", "how early", "how long before", "lead time", "how soon",
            "when should we book", "when to book", "book the venue", "book a venue",
            "book the photographer", "book a photographer", "book the registrar",
            # "how far ahead should we book the venue" and "when should we book the
            # photographer" name the wedding by its bookings and never say the word
            "book the venue", "book a venue", "the wedding venue",
            "the photographer", "a photographer")),
          _wedding_plan,
          # No "book" or "booking" here: an ask is a gate read through the forms, so those two
          # words let "i booked the venue for the wedding" past the gate, and the guest list took
          # a line the plan ack answers. "how far ahead should we book" asks with "how".
          ask=PLAN_ASK + _WEDDING_ASK + ("how many", "how far", "how long", "how soon", "how big",
                                         "when", "count"),
          # a nudge, because the count and the calendar tie with a page about hotel rooms and a
          # card about cooking for a crowd: a wedding plan is the answer to a wedding question
          bias=1,
          # a price question is a price question: "how much does a register office wedding
          # cost" belongs to the fees row (notice, ceremony, certificate), and this row's money
          # answer is about the guest list, so it stands down rather than answering a question
          # about one room with a rule about headcounts
          avoid=("cost", "costs", "how much", "price", "prices", "spend", "\u00a3",
                 # and a dress code is a dress code: "what should i wear to a wedding as a
                 # guest" reached this row on the word "guest" and got the guest list and the
                 # 60% of the bill, where the outfit is clothing's question.
                 "wear", "wearing", "outfit", "outfits", "dress", "dresses", "jumpsuit",
                 "jumpsuits", "hat", "hats", "fascinator", "shoes", "heels", "tie",
                 "colour", "color", "dress code", "black tie",
                 # and "give notice" is also what a tenant does: "how do i give notice to my
                 # letting agent" and "can i give notice by text to my landlord" were both told
                 # to go to the register office 29 days before the wedding. A landlord, a
                 # tenancy or a letting agent in the line is not this row's.
                 "landlord", "landlords", "landlady", "letting agent", "letting agents",
                 "tenancy", "tenancies", "tenants", "my flat", "my lease", "the flat",
                 "rent", "notice period", "evict", "deposit",
                 # what is already booked is the plan ack's, and the ask gate above is what
                 # keeps it there: these are only the odd shapes that carry an ask word of
                 # their own ("when is the venue booked" is a question, but not this one's)
                 "already booked", "havnt booked", "havent booked", "got the venue",
                 "venue booked")),

    # Food for a wedding is the one event meal with no card of its own: the party rows answer
    # "what food for a birthday party" and "how much food for 30 guests", occasions.py answers a
    # christening, and both of those stand down on the word wedding - so "what food for a barn
    # wedding", "we are having a barn wedding what food" and "how do i cater a wedding for 60
    # people" were a shrug or a search hedge, and "wedding food ideas for 60 guests" was answered
    # with how much to spend on a present. The wedding plan card is about guests, venue and
    # paperwork, so the food is its own answer.
    entry("wedding-food",
          (("wedding", "weddings", "wedding breakfast", "wedding reception", "reception",
            "getting married", "we are getting married", "marrying", "barn wedding",
            "wedding day", "big day", "the wedding", "our wedding", "my wedding",
            "for a wedding", "a wedding"),
           ("food", "menu", "menus", "cater", "caters", "catering", "caterer", "caterers",
            "buffet", "meal", "meals", "eat", "eating", "feed", "feeding", "supper", "dinner",
            "breakfast", "hog roast", "barbecue", "bbq", "canapes", "finger food", "serve",
            "serving", "cook", "cooking", "drinks", "what should we eat", "what do we eat",
            "sit down", "sit-down", "plated")),
          "Decide the shape before the menu: a sit-down meal is about £35 to £60 a head catered "
          "and a buffet or hog roast about £20 to £35, while doing it yourselves lands near £10 "
          "to £15 a head and costs you the day. Work back from the number of guests - 60 people "
          "is a caterer's job unless you have a big kitchen and willing help - and ask the venue "
          "first, because many barns and halls either insist on their own list or charge corkage "
          "and a kitchen fee. Book six to nine months ahead for a summer Saturday, put dietary "
          "needs on the reply card, and plan evening food if the day runs past nine: something "
          "hot and cheap at 9pm saves a long hungry evening.",
          # the ask is a gate, so every shape of asking the food has to be in it: "do we need a
          # caterer for a wedding" has no other ask word and reached the hotel row
          ask=PLAN_ASK + ("food", "menu", "cater", "caterer", "caterers", "catering", "buffet",
                          "eat", "feeds", "feed", "serve", "serving", "need", "needs",
                          "what do we", "what should we", "guests"),
          # the present, the paperwork and the outfit are other cards
          avoid=("gift", "gifts", "present", "presents", "notice", "registrar",
                 "register office", "witness", "witnesses", "wear", "wearing", "outfit",
                 "dress code", "speech", "photographer", "flowers", "music", "playlist",
                 "band", "dj", "first dance", "honeymoon", "thank you card"),
          # the hotel row keys "a wedding" too ("book the room early for a wedding"), so the food
          # card has to outrank it on a line that names both: "we need to cater for a wedding"
          bias=2),
    # The order of the day, which people ask as "what time should we say on the invite": the
    # hours pool answered it ("the opening hours are the first thing a venue changes") because
    # nothing else did, and a wedding day has no opening hours - it has a ceremony time, drinks,
    # a meal and a first dance, in that order.
    entry("wedding-timings",
          (("wedding", "weddings", "wedding day", "ceremony", "reception", "wedding breakfast",
            "getting married", "we are getting married", "big day", "marrying",
            # the invite carries the event, so a line that asks what to put on it has said the
            # wedding without the word: "what time should we say on the invite" was a hedge
            "the invite", "the invitation", "on the invite", "on the invitation",
            "what time on the invite", "order of the day"),
           ("what time", "when should", "what time should", "order of the day", "timetable",
            "timeline", "schedule", "run order", "running order", "how early",
            # a bare "invite" is the guest list, not the timetable: "how many people should we
            # invite to a wedding" was answered with the ceremony time. Only the invite as the
            # thing the time is written on counts, and that is in the first part of the key.
            # "how long" is the day's length, not any duration: "how long ago was that", said
            # after a chat about a wedding, was answered with the order of the day
            "how long does the day", "how long does it last", "how long is the ceremony",
            "how long do we need", "how long should the day",
            # the long day said without the word wedding next to it: "how long does the
            # wedding day last" carries only "day" and "last" outside the wedding word
            "long does the day", "how long is the day", "day last", "whole day", "day go on",
            "how long do guests", "how long are guests", "long does a wedding",
            "long is a wedding", "wedding last", "how long the day",
            "what time do people",
            "what time do you", "what time is usual", "usual time", "start time", "what hour")),
          "The time on the invite is the ceremony time, not the time to arrive: guests should be "
          "there 20 to 30 minutes before, so say the ceremony time and let the venue tell people "
          "when to turn up. A ceremony runs about 30 minutes, then drinks and photographs for an "
          "hour to ninety minutes while the room is turned round, then the meal - which takes "
          "about two hours with speeches after it. Evening guests usually come from 7pm, and the "
          "first dance follows the evening food. Work backwards from the meal, because caterers "
          "want the room by a set time, and leave 20 minutes of slack: a late registrar cannot "
          "be made up.",
          ask=PLAN_ASK + ("what time", "when", "order", "timetable", "timeline", "schedule",
                          "run order", "running order", "usual"),
          avoid=("gift", "gifts", "present", "presents", "notice", "registrar",
                 "register office", "witness", "witnesses", "wear", "wearing", "outfit",
                 "dress code", "speech", "honeymoon", "food", "menu", "catering", "buffet",
                 "venue", "cost", "how much",
                 # a duration from the past is not a timetable: "how long ago was that"
                 "ago", "how long ago", "how old", "already been",
                 # nor is a room to sleep in: "when should i book a hotel for a wedding" is a
                 # booking question that names the wedding, not the order of the day
                 "hotel", "hotels", "guesthouse", "guest house", "b&b", "a room", "rooms",
                 "flight", "flights", "travel", "parking", "taxi"),
          bias=1),
    # --- building work ----------------------------------------------------------
    entry("renovation-plan",
          # the room on its own is enough for this row when the rest of the line is the work:
          # "how long does a kitchen take to fit" was the cleaning routine's, because "kitchen"
          # plus the bare "how" in its second group was all it needed
          (("renovation", "renovating", "extension", "building work", "new kitchen",
            "new bathroom", "rewire", "refurb", "doing up", "do up the house", "knock through",
            "kitchen", "kitchens", "bathroom", "bathrooms"),
           ("plan", "planning", "start", "quote", "quotes", "architect", "order", "first",
            "organise", "cost", "timeline", "how long", "permission")),
          "Get three quotes on the same written scope, and don't start until you have the money "
          "for the whole job plus 15% for what the walls hide. Order the kitchen or bathroom six "
          "to eight weeks before you need it, because that is the delay everyone hits, and put the "
          "start date and the payment stages in a contract rather than agreeing them by text.", ask=PLAN_ASK,
          # A room being cleaned is not a room being rebuilt: "how long does it take to clean the
          # bathroom" and "...to clean the kitchen" were both answered "Get three quotes on the
          # same written scope", because the room is this row's subject and "how long" is one of
          # its asks. The room routines answer the cleaning ones and keep their own times.
          avoid=("clean", "cleans", "cleaning", "cleaned", "tidy", "tidies", "tidying",
                 "scrub", "scrubbing", "hoover", "hoovering", "vacuum", "vacuuming",
                 "mop", "mopping", "dust", "dusting", "wipe", "wiping", "wash",
                 "washing up", "bleach", "disinfect", "smell", "smells", "smelly",
                 "mould", "mold", "damp")),

    # "how do i plan a kitchen" was answered "Clear the surfaces, then work clockwise so you do
    # not double back" - the room-cleaning routine keys "kitchen" and "plan" was not there, but
    # the bare "how" in its second group was enough. Planning a kitchen is where the sink, the
    # hob and the fridge go, not the order to wipe it in, so the room and the planning words are
    # this row's own key and it takes the line.
    entry("room-plan",
          # the room, not the building job: an extension, a loft conversion and a renovation are
          # `renovation-plan`'s lines, and carrying those words here took "how do i plan a house
          # extension" off the three-quotes card and onto the kitchen work triangle.
          (("kitchen", "kitchens", "new kitchen", "bathroom", "bathrooms", "new bathroom",
            "utility room", "laundry room", "refurb", "refit", "redo"),
           ("plan", "planning", "planned", "lay out", "layout", "design", "designing",
            "redesign", "work triangle", "where do things go", "where should things go",
            "how should i lay", "how do i arrange", "rearrange", "sizes", "measurements",
            "what size", "get it right")),
          _a_room_plan,
          # a price, a quote or a whole building job is the renovation row's, and so is the
          # order to do the work in
          avoid=("cost", "costs", "how much", "price", "prices", "quote", "quotes", "cheap",
                 "cheapest", "budget", "afford", "builder", "builders", "architect", "permission",
                 "planning permission", "how long", "timeline", "contractor", "contractors",
                 "clean", "cleaning", "tidy", "mess", "messy", "hoover", "scrub"),
          # a layout ask is the shape this row is for, and it ties with the renovation row on
          # "how do i plan a new kitchen", which is the layout question rather than the quotes one
          bias=1),

    # --- a baby -----------------------------------------------------------------
    entry("baby-plan",
          (("baby", "pregnant", "pregnancy", "newborn", "due date", "nursery"),
           ("plan", "planning", "prepare", "preparing", "need", "needs", "buy", "buying",
            "hospital bag", "nesting", "ready for the baby", "before the baby", "shopping list",
            "organise", "cot", "pram", "car seat")),
          "Buy very little in advance: a car seat, a cot or Moses basket with a firm new mattress, "
          "a pram, six babygros in two sizes, nappies and whatever you're feeding with. Put the cot "
          "in your room, empty, with no bumpers or pillows, and pack the hospital bag at 36 weeks "
          "with snacks and a long phone charger — everyone forgets the charger.", ask=PLAN_ASK,
          # What they eat is not what to buy: "can i buy baby pouches" was answered with the
          # car seat and the Moses basket. The food rows own jars, pouches and purees.
          avoid=("sleep", "sleeping", "hurt", "hurts", "pain", "aching", "feed", "feeding",
                 "formula", "temperature", "fever", "cold", "cough", "sick", "ill",
                 "health visitor", "jar", "jars", "pouch", "pouches", "puree", "purees",
                 "baby food", "food", "eat", "eating", "eats", "meal", "meals", "weaning",
                 "breakfast", "lunch", "dinner", "snack", "snacks", "milk")),

    # The gear is the other half of a baby plan, and it is asked about on its own: "what about the
    # pram", "which cot should i buy", "is a second hand car seat ok". The baby plan above answers
    # the whole list, and a line naming one piece of the gear is a question about that piece.
    entry("baby-gear",
          (("pram", "prams", "pushchair", "pushchairs", "buggy", "buggies", "cot", "cots",
            "moses basket", "car seat", "car seats", "bouncy chair", "high chair", "highchair",
            "travel cot", "crib", "cotbed", "cot bed", "nursery furniture", "baby monitor"),
           ("buy", "buying", "get", "getting", "need", "needs", "which", "what about", "best",
            "cheap", "cheapest", "second hand", "secondhand", "second-hand", "new", "safe",
            "worth", "shop", "shopping", "borrow", "hand me down", "choose", "recommend",
            "compare", "price", "cost", "much", "how much",
            # a fault in the gear is the same piece being asked about, and it is a mending job
            # rather than a price: "the brake on the pushchair is sticking" was the general
            # repair card (a cobbler, a luggage shop), which does not touch a pram
            "squeak", "squeaks", "squeaking", "squeaky", "sticking", "stuck", "jammed",
            "wobbly", "broken", "broke", "snapped", "wont fold", "won't fold", "wont push",
            "won't push", "brake", "brakes", "wheel", "wheels", "fix", "mend", "repair")),
          _a_piece_of_baby_gear,
          # how to make the baby sleep, what is wrong with it and what to feed it are health rows
          avoid=("sleep", "sleeping", "wont sleep", "hurt", "hurts", "pain", "aching", "feed",
                 "feeding", "formula", "temperature", "fever", "cold", "cough", "sick", "ill",
                 "reflux", "colic", "teething", "rash", "health visitor", "cat", "cats", "dog",
                 "dogs", "pregnant", "pregnancy", "labour", "hospital bag",
                 # "how do i get a stain out of my car seat" is the cleaning job, not the buying
                 # one: `get` is an ask word, so the subject plus `get` was enough to score, and a
                 # stain on a car seat was answered with the price of a cot.
                 "clean", "cleaning", "stain", "stains", "stained", "spill", "spills", "spilt",
                 "spilled", "smell", "smells", "smelly", "stinks", "vomit", "wash", "washing",
                 "dirty", "mould", "mold", "wipe", "scrub", "dry", "drying",
                 # the fence above is a list of nouns, and a stain is most often said without one:
                 # "how do i get coffee out of a car seat" has no clean, stain or spill word in
                 # it, only "out of", and it was the price of a cot. The words that make a
                 # car seat, a cot or a pram the *thing being cleaned* are the ones here, and
                 # "off facebook" and "off a mate" keep their buying answer because the noun
                 # follows them rather than "the", "a" or "my"
                 "out of", "out the", "off a", "off my", "off the", "off our", "off his",
                 "off her", "got it on", "got on the", "soaked", "spilled on",
                 # and the smoke in it is the same job: "how do i get cigarette smell out of
                 # car seats" was this row, with prices for a second-hand cot
                 "smoke", "smoky", "cigarette", "cigarettes", "odour", "valet", "get rid",
                 "sick in",
                 # a coat worn in the car seat is a question about the coat: the coat row says
                 # never put a thick one under the harness, and this row's price list is no
                 # answer to it. The two score the same on "is it safe to wear a coat in the
                 # car seat", so the garment words stand this row down.
                 "coat", "coats", "jacket", "jackets",
                 # How to afford one is the saving question, and the prices above answer a
                 # different half of it: "how do i afford a new buggy" was this row while
                 # "how do i afford a new pram" and "how do i afford a new sofa" were the
                 # saving row. One noun should not decide it, so the money words stand this
                 # row down and save-for-a-thing takes the line.
                 "afford", "affords", "affording", "can i afford", "save up", "saving up",
                 "savings", "budget", "budgeting", "pay for it", "installments",
                 "instalments", "on finance", "payment plan"),
          bias=1),

    # One piece of the baby gear is chosen far more carefully than the rest: the pram is pushed
    # every day for two years and has to fit a boot. "what should i look for in a pram" had no
    # ask word the baby-gear row demands and was a hedge, and the whole-gear price list is not the
    # answer to a line about one piece of it.
    entry("pram-buy",
          (("pram", "prams", "pushchair", "pushchairs", "buggy", "buggies", "travel system",
            "travel systems", "stroller", "strollers"),
           ("buy", "buying", "bought", "which", "what", "best", "choose", "choosing",
            "look for", "look out for", "worth", "recommend", "new", "second hand",
            "secondhand", "second-hand", "cheap", "price", "cost", "get", "need",
            # a comparison of two of the same thing is this question: "is a bigger pram better"
            # was a search hedge beside a row that answers which pram to buy
            "better", "worse", "bigger", "smaller")),
          "Lay it flat first: a newborn needs a carrycot or a seat that goes properly flat, and "
          "after that the fold and the boot decide it - fold it one-handed in the shop and lift it "
          "into your own boot before you pay. Check the brake holds on a slope with the child in "
          "it, that the handle suits your height, and that the wheels are big enough for the "
          "pavement you actually walk on. A new one is \u00a3150 to \u00a3400 and a good second-hand "
          "pram is \u00a360 to \u00a3150, which is the better buy; the car seat is the one piece worth "
          "buying new, or with a history you know.",
          # how to fold, clean or fix one is its own question, and a pram on a bus or in an
          # airport is not a purchase either
          avoid=("fold", "folding", "folded", "stuck", "clean", "cleaning", "wash", "washing",
                 "stain", "stains", "smell", "smells", "mould", "mold", "repair", "fix",
                 "bus", "plane", "airport", "safe to", "car seat", "isofix", "wont sleep",
                 "sleep", "reflux", "colic",
                 # a choice between two pieces of baby gear is the cost card's question, and it
                 # answers it by comparing them: "which is better, a pram or a carrier" was
                 # answered with the pram alone
                 "carrier", "carriers", "sling", "slings", "or a carrier", "or a sling",
                 # and "where can i buy a pram" asks for a shop, which is not what this row
                 # is, so the price card beside it answers rather than a near miss
                 "where can i", "where to buy", "where do i buy", "which shop",
                 "cheapest place", "shop"),
          bias=2),

    # --- a holiday --------------------------------------------------------------
    entry("holiday-countdown",
          (("holiday", "trip", "flight", "flights", "fly to", "flying to", "flying out",
            "going abroad", "abroad", "vacation", "travel insurance", "passport", "airport"),
           ("plan", "planning", "prepare", "countdown", "organise", "checklist",
            "need to do", "what do i need", "sort out", "still to do",
            # "what should i book first for a holiday" and "where do i start with a trip" are
            # this countdown's question, and neither asking phrase was here: the first was a
            # book-or-film card and the second a falls one
            "book first", "first", "where do i start", "where to start", "how do i start",
            "start with")),
          "Two months out: check the passport has six months left on it, book what sells out, and "
          "take the insurance out the day you book, so a cancellation is covered. Two weeks out: "
          "repeat prescriptions, any jabs the country wants, and a card that works abroad; a week "
          "out, send copies of the passport and insurance to someone at home.", ask=PLAN_ASK,
          # "what do i need for a coach trip" is what to put in the bag, not when to book the
          # passport: the trip words here are loose and the packing rows key the same ones
          avoid=("coach trip", "coach journey", "train journey", "train ride", "train trip",
                 "bus trip", "bus journey", "on a train", "on the train", "on a coach",
                 "for hours", "long journey")),

    # --- a clear-out ------------------------------------------------------------
    entry("declutter-plan",
          (("declutter", "clear out", "clearout", "big tidy", "tidy up the house", "loft",
            "garage", "spare room", "wardrobe clear",
            # the words a loft or a garage clear-out is actually said in, as a follow-up after
            # "im going to the tip on saturday" then "weve got a loft full of junk": "i suppose i
            # should hire a skip" was an echo ("you suppose you should hire a skip - noted")
            "hire a skip", "skip hire", "a skip", "skip for", "full of junk", "junk",
            # the job in the words people write it in: "how do i clear the clutter" and "how do
            # i clear my desk" were a punt and the posture answer, and neither is a clear-out
            "clutter", "clear the clutter", "clear clutter", "messy house", "tidy my house",
            "tidy up my house", "clear my desk", "clear a room", "clear the room",
            # the whole home said with its plain verb. "tidy my house" was here and its neighbours
            # were not, so "how do i tidy my flat", "how do i clean the house", "how do i clean my
            # whole house" and five more like them were a hedge. A house, a flat and a home are
            # the same job, so the verb phrases are the same whichever word names the home.
            "tidy my flat", "tidy the flat", "tidy my home", "tidy the house",
            "tidy my whole house", "tidy the whole house",
            # ("clean my house" and its neighbours cannot be keyed here: this row's avoid list
            # carries "cleaning" and "clean the" as word families, because a cleaning question is
            # cleaning.py's. A whole home to clean is a row in that module instead.)
            "too much stuff", "clear the house",
            # the same job in the words people use for it: "what should i get rid of" was the
            # search hedge, "where do i start with the mess" the other hedge, and "i have got
            # too much stuff" was answered with "Good to hear."
            "rid of", "the mess", "mess everywhere", "clear the mess",
            "too much clutter", "sort the house out", "sort the house"),
           ("plan", "planning", "start", "where", "first", "organise", "how", "much time",
            "weekend", "sorted",
            # a person thinking out loud about the job is asking what to do about it
            "hire", "should", "suppose", "then", "worth", "need", "full", "rubbish", "junk",
            # and the plainest way of asking is to name the job again: "i need to clear out my
            # garage" and "what should i get rid of" have no planning word in them at all
            "clear out", "declutter", "rid of", "stuff", "mess", "too much", "sort")),
          "One room at a time, three bags on the floor — bin, donate, keep — and the donate bags go "
          "to the car the same day or they drift back. Ten minutes a day beats a lost weekend, and "
          "start with the room you walk through most, because clearing that one is what makes the "
          "rest of the house feel possible.", ask=PLAN_ASK + _DECLUTTER_ASK,
          guard=_declutter_fits,
          # "how do i insulate a loft cheaply" is a building question that carries the word loft,
          # and "how do i paint a garage door" is a painting question that happened to say garage,
          # and the loft and the garage are also places a smell can come from, which is a
          # different question with a different answer
          # A garage or a shed that is COLD is a heating question that happens to name the
          # place: "how do i keep my garage warm" was told to clear it out one room at a time,
          # because "garage" is in this row's gate and so is "how". The warm words are the
          # tell, and a clear-out question never has one in it.
          avoid=("warm", "warmer", "warmth", "heat", "heated", "heating", "radiator",
                 "insulate", "insulation", "lagging", "mineral wool", "loft insulation",
                 "board out", "boarding", "floor the loft",
                 "paint", "painting", "painted", "repaint",
                 "charge", "charges", "charge for", "labour", "hourly", "mot", "service",
                 "servicing", "serviced", "full service",
                 # "how do i stop spending money on junk" and "... on junk food" are the
                 # buying question, not a clear-out: the pile word "junk" is in this row's
                 # gate, and the money in the line is what says which question it is.
                 "spend money", "spending money", "spent money", "save money",
                 "saving money", "waste money", "wasting money", "money on", "junk food",
                 # "how do i clear a room of smoke" is the smoke card: something in the air is
                 # cleaned out of the air, not carried out in three bags
                 "smoke", "smoking", "smoky", "fumes", "smell", "smells", "smelly", "damp",
                 "mould", "mold", "condensation", "air out", "air it out",
                 # and a smell with a source in it is the smell card, whichever room it is in
                 "stink", "stinks", "odour", "odor", "reek", "musty",
                 # "spare room" is a place a clear-out happens in, so a job on the heating in
                 # that room read as one: "how do i turn the radiator off in the spare room" was
                 # three bags on the floor. Anything on the heating is the heating's answer.
                 "radiator", "radiators", "rad", "rads", "towel rail", "heating", "boiler",
                 "thermostat", "thermostatic", "valve", "trv", "frost setting", "bleed",
                 # a repair on the place being cleared is the thing's own answer: "i need my
                 # garage door fixed" is the door, not three bags on the floor
                 "fix", "fixed", "fixing", "repair", "repairs", "repaired", "broken",
                 "not working", "doesnt work", "doesn't work", "wont close", "won't close",
                 "wont open", "won't open", "stuck", "leak", "leaking", "replace", "replacing",
                 "roller", "spring", "lock", "handle", "hinge", "jammed",
                 # a thing being got rid of is the selling, scrapping or replacing question about
                 # that thing, not a clear-out of a room: "should i get rid of my car"
                 "car", "cars", "van", "bike", "bicycle", "motorbike", "phone", "laptop",
                 "washing machine", "fridge", "freezer", "dishwasher", "tumble dryer",
                 "sell", "selling", "sold", "scrap", "part exchange", "trade in", "get rid of my",
                 # and a thing too big for a bag has the council's bulky waste collection
                 "mattress", "mattresses", "sofa", "settee", "couch", "armchair", "bed", "beds",
                 "cot", "carpet", "carpets", "rug", "tyre", "tyres", "tire", "tires", "battery",
                 "rubble", "hardcore", "garden waste", "tree", "branches", "asbestos",
                 "paddling pool", "trampoline",
                 # "get rid of" is also how a pest and a weed are said, and both have a real
                 # answer of their own
                 "moth", "moths", "fly", "flies", "ant", "ants", "mouse", "mice", "rat", "rats",
                 "slug", "slugs", "snail", "snails", "weed", "weeds", "moss", "aphid", "aphids",
                 "bedbug", "bedbugs", "bed bugs", "flea", "fleas", "wasp", "wasps",
                 "cockroach", "cockroaches", "woodlice", "spider", "spiders", "pigeon",
                 "pigeons", "fox", "foxes", "stain", "stains",
                 # the store-cupboard pests by name: "how do i get rid of weevils in my cupboard"
                 # named a room and a pest, and the room won
                 "weevil", "weevils", "mite", "mites", "flour mite", "flour mites", "larder",
                 "silverfish", "booklice", "woodworm", "carpet beetle", "clothes moth",
                 "fruit fly", "fruit flies", "drain fly", "drain flies", "gnat", "gnats",
                 "midge", "midges", "wasp nest", "ants nest",
                 # cleaning a room is not clearing it out: "how do i get rid of dust in my
                 # bedroom" was three bags on the floor, because "get rid of" and a room are
                 # both this row's words. The cleaning has its own answers, and a clear-out
                 # question never says dust, hoover, mop or wipe.
                 # the mess a flatmate leaves is a conversation with them, not a clear-out:
                 # "what should i say to my flatmate about the mess" was three bags on the floor
                 "flatmate", "flatmates", "housemate", "housemates", "roommate", "roommates",
                 "house share", "houseshare", "lodger",
                 "dust", "dusty", "dusting", "cobweb", "cobwebs", "hoover", "hoovering",
                 "vacuum", "vacuuming", "wipe", "wiping", "mop", "mopping", "polish",
                 "cleaning", "clean the", "scrub", "scrubbing", "limescale",
                 # a removal is a pack, not a clear-out. "a move" is not: "how do i declutter
                 # before a move" is the clear-out with a deadline, and a bare "moving" here
                 # matched it by stem and left the line with no answer at all
                 "to move", "moving house", "moving home", "moving flat", "moving out",
                 "moved house", "house move", "removal", "removals",
                 "pack up", "packing", "care home", "residential home", "nursing home",
                 # "how do i stop junk email" and "too much junk email" are the inbox's, and
                 # "junk" is in this row's gate: an inbox is cleared out by a filter, not in
                 # three bags
                 "email", "emails", "inbox", "spam", "junk mail", "newsletter",
                 "newsletters", "unsubscribe")),
    # --- a free weekend -----------------------------------------------------------
    # "what can i do this weekend" was the search hedge, and it is one of the commonest
    # small-talk questions there is. The honest answer is not a list of attractions: it is
    # the shape of a good weekend, with an offer to get more specific.
    entry("weekend-ideas",
          (("weekend", "weekends", "day off", "days off", "saturday", "sunday", "free day",
            "bank holiday weekend", "bank holiday", "next weekend", "this weekend",
            "this evening", "tonight", "today", "around here", "near here", "near me",
            "in town", "in the area",
            # A day is a day: "what shall we do tomorrow" and "any ideas for tomorrow" were a
            # search hedge on main while the same ask about today has this answer. The words are
            # the day's, not the weekend's, and the guards below still decide whether the line is
            # a free block waiting to be filled.
            "tomorrow", "tomorrow morning", "tomorrow afternoon", "tomorrow evening",
            "tomorrow night"),
           ("what", "anything", "ideas", "idea", "things to do", "something to do", "do this",
            "suggest", "recommend", "bored", "plan", "plans", "shall i", "can i do",
            "what can i do", "what should i do", "what can we do", "what shall we do",
            "nothing to do", "what is there to do", "any ideas", "do with")),
          _a_free_weekend,
          # the weekend is the question only when the line names nothing to answer about
          guard=lambda reading: (_the_free_weekend_fits_and_is_asked(reading)
                                 and _a_stretch_of_time_to_fill(reading)),
          # a weekend of chores, a weekend away and a weekend of sport are other answers
          avoid=("clear out", "clear the", "tidy", "chores", "garage", "loft", "cupboard",
                 # "can i take anything for it tonight" is the follow-up to a symptom, and
                 # "tonight" plus "anything" is all this row needs to answer it with a plan for
                 # the weekend. Anything you swallow is not a thing to do on a Saturday. The
                 # bare ask for a medicine ("can i take anything tonight", "what can i take")
                 # is not in this list: it reaches the row and `_a_free_weekend` answers it.
                 "what helps", "what would help", "helps it", "help it", "help the",
                 "ease it", "relief", "get rid of", "make it better", "stop it",
                 "tablet", "tablets", "medicine", "medicines",
                 "medication", "painkiller", "painkillers", "ibuprofen", "paracetamol",
                 "antihistamine", "antibiotic", "dose", "pharmacy", "chemist", "prescription",
                 "symptom", "symptoms", "toothache", "headache", "migraine", "sore throat",
                 "temperature", "fever", "nausea", "cramps", "stomach ache", "dizzy",
                 "dentist", "gp", "doctor", "nurse", "111", "999", "side effect", "side effects",
                 "decorate", "painting", "diy", "away", "hotel", "flight", "abroad",
                 "match", "race", "half marathon", "long run", "work", "shift",
                 # watching, cooking, reading and training at the weekend are their own
                 # domains, and "what" was enough to bring them here
                 # what to put on and what to pack are the same trap: the time word ("tonight",
                 # "saturday") plus the bare "what" brought "what should i wear tonight" here,
                 # and a person dressing for tonight was told how to plan a weekend.
                 "wear", "wearing", "wore", "put on", "dress", "dressing",
                 # "bring" and "take" alone were the fence, and they are also how a medicine is
                 # asked for: "can i take anything tonight" was stood down here and then had
                 # nothing to answer it, so it got the search line while "what can i take
                 # tonight" - the same question with a "what" in front - was answered. The bag
                 # and the gift are the shapes that stand this row down; what is swallowed is
                 # read in `_a_free_weekend`.
                 "what should i take", "what should i bring", "what to take", "what to bring",
                 "take with", "bring with", "take to a", "bring to",
                 # "what do i need to bring tomorrow" is a packing question, not a day to fill,
                 # and the day word alone brought it to this row for a plan of two things out
                 # of the house.
                 "need to bring", "need to take", "need to pack", "must bring", "to bring tomorrow",
                 # and a bag for it: "what should i pack for a weekend in rome" named a weekend
                 # and the bare "what", so a packing question was told to put two things in the
                 # diary by Friday. The pack words say which question it is on their own.
                 "pack", "packs", "packing", "packed", "suitcase", "suitcases", "luggage",
                 "hand luggage", "carry on", "toiletries", "wash bag", "rucksack",
                 "watch", "watching", "film", "films", "series", "netflix", "tv", "read",
                 "reading", "book", "books", "cook", "cooking", "recipe", "recipes",
                 # the box itself is the listings question, not a free evening to fill:
                 # "whats on the telly this evening" was two plans in the diary by Friday,
                 # because "this evening" is a time here and "what" is an ask, and the row had
                 # only guarded "tv", not the everyday words for the set or the channels
                 # people name instead of it. Nobody here can see the schedules either, so the
                 # answer it hands back to is the one that names what to start: the listings.
                 "telly", "television", "bbc", "itv", "channel 4", "channel 5",
                 "channel four", "channel five", "listings", "on telly", "on tv",
                 "dinner", "lunch", "eat", "food", "bake", "baking", "shop", "buy",
                 "train", "training", "gym", "run", "running", "football", "park",
                 "kids", "children", "child", "baby",
                 # a money word makes it the free-day-out question, which names the things
                 # that cost nothing; the picking rule here is the general answer
                 "cheap", "free", "money", "cost", "costs", "budget", "pay", "price",
                 # "any plans tonight?" is small talk, not a request for ideas: the word
                 # "plans" alone brought the two-things-in-the-diary paragraph to a person who
                 # was asking whether the bot was free to talk (plain-tray, #answers 16). It is
                 # the chat module's own ask now, so the row stands down on the phrase.
                 "any plans", "got plans", "got any plans", "up to tonight", "up to later")
                 # "today" and "what" are enough to bring a line here, so the weather asks came
                 # with them: "what is the weather like today" and "whats the weather like this
                 # weekend" were both told to pick two things for the weekend.
                 + A_WEATHER_ASK
                 # an hours ask names a place and a time, which is the venue's answer and not a
                 # weekend plan: see A_HOURS_ASK in bot/knowledge/lookup.py
                 + A_HOURS_ASK),

    # --- a meal for guests -------------------------------------------------------
    entry("hosting-food",
          (("dinner party", "having people over", "people coming over", "guests", "buffet",
            "barbecue", "bbq", "roast for", "cooking for", "family over"),
           ("plan", "planning", "much", "how many", "ahead", "timing", "timings", "first",
            "menu", "quantities", "12 people", "10 people", "8 people")),
          "Choose a menu you can cook twice before: one oven dish, something cold on the side, "
          "bread, and a pudding made the day before, so you're out of the kitchen when they arrive. "
          "For a barbecue, allow 250g of meat a head plus a vegetarian option; for a sit-down "
          "dinner, eight people is the most a normal oven does well.", ask=PLAN_ASK,
          # a dinner party with a number in it is this answer, not a list of things to cook
          bias=1),

    # --- the last hour before people arrive -------------------------------------
    entry("late-guests",
          # The subject is somebody coming, and the key word of the two is the notice: "we have
          # guests in an hour and nothing is ready" was an echo, "people arrive in twenty minutes
          # and nothing is ready" was "I'm listening", and "im hosting dinner and im not ready"
          # was the same, because no row in the domain is about the hour before rather than the
          # weeks before. The hosting card next door plans a meal; this one is the order to do
          # things in when there is no time to plan at all.
          (("guests", "guest", "guests coming", "guest coming", "guests are coming",
            "people coming", "people are coming", "people over", "people round",
            "people arriving", "people turning up", "friends coming", "friends are coming",
            "friends over", "friends round", "friends arriving", "friends turning up",
            "family coming", "family over", "company coming", "company over", "visitors",
            "visitors coming", "someone coming over", "people for dinner", "guests for dinner",
            "people coming for dinner", "hosting dinner", "having people over",
            "having friends over", "having guests", "party tonight", "people here at",
            # they are already here, or nearly: "people are here and i have nothing in" was an
            # echo and "somebody is at the door already" was "I'm listening"
            "people are here", "guests are here", "theyre here", "they are here",
            "people are at the door", "someone at the door", "somebody at the door",
            "friend dropping", "friend popping", "dropping round", "popping round",
            "dropping by", "popping in", "coming round", "coming over",
            # who is coming is as often a person as the word "guests": "someone just texted
            # theyre 20 minutes away" and "the in laws are on their way" are the same hour
            "someone", "somebody", "in laws", "in-laws", "mother in law", "father in law",
            "parents", "mum", "dad", "sister", "brother", "aunt", "uncle", "cousin",
            "grandparents", "neighbours"),
           ("in an hour", "in half an hour", "in a hour", "in 20 minutes", "in twenty minutes",
            "in 30 minutes", "in thirty minutes", "in 10 minutes", "in ten minutes",
            "in 15 minutes", "in fifteen minutes", "in 45 minutes", "in two hours",
            "in a couple of hours", "in a bit", "in 40 minutes", "this evening", "tonight",
            "nothing is ready", "nothing ready", "nothing prepared", "nothing made",
            "nothing in", "not ready", "im not ready", "i'm not ready", "not prepared",
            "havent started", "haven't started", "havent even started", "havent cooked",
            "last minute", "at short notice", "short notice", "unexpected", "unannounced",
            "turned up", "turning up", "arrived early", "arriving early", "early",
            "just told me", "just rang", "just called", "just texted", "surprise visit",
            "on their way", "on his way", "on her way", "on the way", "minutes away",
            "20 minutes away", "ten minutes away", "five minutes away",
            # "guests coming at 7 and i only have pasta" is the same hour, said as a time and as
            # an almost-empty kitchen rather than as "in an hour" and "nothing is ready"
            "at 6", "at 7", "at 8", "at 6pm", "at 7pm", "at 8pm", "at six", "at seven", "at eight",
            "at the door", "at my door", "already here", "later", "this afternoon",
            "only have", "only got", "nothing in", "nothing much in", "no food in")),
          "Do the three things they will actually notice, in this order: clear the floor into one "
          "basket and shut the doors on the rest, put out glasses and something to nibble, and "
          "cook one thing from what you already have - pasta, an oven tray of whatever vegetables "
          "and sausages are in, or bread, cheese and something cold from the fridge. Buy only the "
          "missing bit on the way home, and don't start a clean nobody will see: a drink in their "
          "hand and food within half an hour is the whole of it.",
          # what to cook for them is the cooking domain's question, and a messy house is the
          # cleaning domain's: this card is the order of work, not the menu or the scrubbing
          avoid=("what should i cook", "what can i cook", "what to cook", "what can i make",
                 "what to make", "recipe", "recipes", "what should i wear", "what to wear",
                 # a menu is the cooking domain's question however little notice there is:
                 # "last minute guests what do i cook" and "having people over for dinner
                 # tonight" both want the one-oven-dish answer next door, and "people coming
                 # for dinner in 20 minutes" wants the twenty-minute list, not the tidying order
                 "cook", "cooking", "cooked", "menu", "roast", "for dinner", "dinner party",
                 "dinner tonight", "meal", "meals", "food for", "feed", "what do i cook",
                 "mess", "messy", "clean", "cleaning", "tidy", "tidy up", "hoover", "vacuum",
                 "dust", "dishes", "washing up", "disaster", "shambles", "dirty", "filthy",
                 # a guest who stays for days is the hosting card's question
                 "stay with us", "staying with us", "for the weekend", "for a week",
                 "next week", "next month", "in a few weeks", "in two weeks", "tomorrow",
                 # a parent who keeps turning up unannounced is a boundary question, not an
                 # hour-before question: "my mum keeps turning up unannounced" was handed the
                 # clear-the-floor order instead of how to say it kindly once
                 "keeps turning up", "keeps coming over", "keeps coming round",
                 "keeps dropping in", "keeps dropping by", "keeps popping in",
                 "turning up unannounced", "unannounced", "uninvited", "without asking",
                 "every weekend", "all the time", "every day", "again and again",
                 "boundary", "boundaries", "how do i tell", "how do i ask",
                 "without warning", "without telling me", "out of the blue",
                 # "what should i watch tonight with my mum" is a film question: a bare "mum" in
                 # the first group and "tonight" in the second was enough for this row, and the
                 # person sat down to watch something and got the clear-the-floor order. Who is
                 # coming is only the subject when something is happening, so anything being
                 # watched or played is the entertainment domain's line.
                 "watch", "watching", "watch with", "what to watch", "something to watch",
                 "watch tonight", "film", "films", "movie", "movies", "box set", "box sets",
                 "series", "telly", "netflix", "prime", "disney", "iplayer", "streaming",
                 "episode", "episodes", "listen to", "listen with", "play with", "a game",
                 "board game", "board games", "cards",
                 "whenever she likes", "whenever he likes", "whenever they like",
                 "turns up without", "turned up without"),
          # the hosting card plans a meal for a number of people, and "friends are coming over in
          # an hour" was read as a visit of days ("give them the best bed"), so this row outbids
          # the bed-making card on a line that names the hour
          bias=10),

    # --- Christmas --------------------------------------------------------------
    entry("christmas-plan",
          (("christmas", "xmas", "christmas day", "christmas dinner", "boxing day"),
           ("plan", "planning", "organise", "ahead", "timing", "timings", "hosting", "much",
            "start", "list", "prepare", "shop")),
          "Write every cooking time on one sheet and work back from when you want to eat: the bird "
          "rests an hour, so it comes out an hour before, and the potatoes go in as it comes out. "
          "Shop for the cold stuff two days before rather than on the day, because fridge space "
          "runs out, and hand out the pudding, the drinks and the ice to other people.", ask=PLAN_ASK),

    # --- a long drive -----------------------------------------------------------
    entry("road-trip-plan",
          (("road trip", "long drive", "driving down", "driving to", "driving holiday",
            "driving abroad"),
           ("plan", "planning", "stops", "route", "how long", "overnight", "break", "rest",
            "hours", "first", "check")),
          "Plan the driving days rather than the hours: put the stops in first, every two hours and "
          "one proper stop a day, and don't book more than six hours of driving in a day. Book the "
          "first and last night's bed before you go, check the spare tyre, the oil and the "
          "breakdown cover, and keep the overnight bag on the back seat.", ask=PLAN_ASK,
          # "how long is the drive to york" asks for a figure, and this is how to plan the days:
          # the journey line in the composer names the route planner instead, so this card keeps
          # the planning asks and stands down on a duration or a distance.
          avoid=("how long is the drive", "how long would the drive", "how long does the drive",
                 "how far is", "how many miles", "how long does it take to drive",
                 # a light on the dashboard is a fault, not a plan: "driving to cornwall in
                 # august and the car has a warning light on, what should i check" was answered
                 # with how to plan the driving days, on "driving to" and "check".
                 "warning light", "warning lights", "engine light", "dashboard", "mot",
                 # a bare "service" is a motorway stop, and "where are the good service
                 # stations" is this row's own line: the car being serviced is a phrase.
                 "car service", "full service", "needs a service", "due a service",
                 "due for a service", "service the car", "serviced", "servicing",
                 "breakdown", "battery light", "oil light")),

    # --- the week ---------------------------------------------------------------
    entry("week-plan",
          (("my week", "the week ahead", "plan my week", "my time", "everything at once",
            "everything feels urgent", "to do list", "never enough time"),
           ("plan", "planning", "organise", "prioritise", "prioritize", "urgent", "start",
            "manage", "sorted")),
          "Write down what is actually due this week, then pick three things a day and put them in "
          "the diary as blocks; the rest waits, and that is fine. Real deadlines go in first, the "
          "urgent-but-not-important jobs get one slot a day, and the way to protect the rest is to "
          "say no to one thing out loud.", ask=PLAN_ASK),
    # --- the weekly shop -----------------------------------------------------
    # "i keep buying too much food and wasting it" is a habit question, not a recipe or a
    # food-safety one, so it sits with the other plans. It is keyed on food going to waste, and
    # stands aside for the fridge-and-dates questions, which cooking.py already answers.
    entry("food-shop-waste",
          # "away" and "out" on their own are not waste. A follow-up after a fussy-eating turn -
          # "she just pushes the plate away and cries" - was answered by this row, because the
          # memory supplied "vegetables" and the line supplied "away"; and "the veg is out on the
          # side" is somebody's tea, not a bin. The waste words have to be about throwing away.
          (("food", "food shopping", "groceries", "shopping", "supermarket", "fridge", "veg",
            "vegetables", "leftovers", "left over"),
           ("waste", "wasting", "wasted", "throw", "throwing", "threw", "thrown",
            "throw away", "throwing away", "thrown away", "throws away", "toss out",
            "bin", "binned", "binning", "in the bin", "rubbish", "goes off", "going off",
            "gone off", "rot", "rotting", "never use it", "never use them",
            "never get through", "buy too much", "buying too much", "buy less",
            "shop better")),
          "Write the week's four meals down before you shop and buy for those, not for the week "
          "you imagine. Keep a box in the fridge for what must go first, and put tonight's dinner "
          "in it when you unpack. Cook double twice a week and freeze the spare that evening, "
          "because leftovers in the fridge are what gets binned, and buy fresh less often: a "
          "top-up on the way home beats a full trolley on a Sunday.",
          # A complaint is the shape this arrives in ("we throw so much away every week"), so
          # there is no ask gate; the avoid list is what keeps it off the neighbouring questions.
          # "too much" alone is not a waste word: "how much pasta is one portion? i always cook
          # too much" is the portion question, and it was taking it (seed 6621).
          # "fridge" and "out" are both key words, so a fridge line that says how long something
          # was on the side landed here: "left out of the fridge all night" was told to write the
          # week's four meals down. The food-safety words turn those lines away; what was bought
          # and wasted is still this row's question.
          avoid=("use by", "best before", "how long", "safe to eat", "still ok", "cat food",
                 "dog food", "food bank", "school dinner", "packed lunch", "declutter",
                 "moving house", "kitchen bin",
                 "left out", "all night", "overnight", "out of the fridge", "is it ok",
                 "two hours", "bin it", "gone bad",
                 # which food to eat first out of the fridge is the fridge order's question, and
                 # "what goes off first in the fridge" was being told to write four meals down
                 "goes off first", "go off first", "eat first", "use first", "use up first",
                 "which shelf", "top shelf", "bottom shelf", "middle shelf", "salad drawer",
                 "crisper", "fridge order", "where in the fridge", "what goes where",
                 # "gone off" with a person's possessive is an appetite, not a shopping habit:
                 # "my sister has gone off her food" was told to write the week's four meals
                 # down before shopping, and the appetite row answers it.
                 "off her food", "off his food", "off their food", "off our food",
                 "off my food", "off your food", "gone off food", "gone off eating",
                 "appetite")),
    # --- money ---------------------------------------------------------------
    # Keyed by the habit words only ("save money", "start saving", "emergency fund"), never by
    # "budget" or "spending" on their own: "can you help me revise my budget" is studying, "what
    # if he says there's no budget" is the pay-rise conversation, and "stop spending on takeaway"
    # is its own thing. This entry is only the "how do I save" question.
    #
    # "for a rainy day", never "rainy day" alone: the idiom is also the weather, and a bare
    # "rainy day" stole "my kids are bored on a rainy day what can we do" from the kids
    # answer. The money senses are spelled out instead.
    entry("saving-plan",
          (("save money", "saving money", "start saving", "savings", "save each month",
            "save every month", "put money aside", "money aside", "save some money",
            "save a bit", "i need to save", "need to save up", "for a rainy day",
            # "emergency fund" and "emergency savings" used to sit here, and they are the one
            # question this row is not: money.emergency-fund has the figure, and this row (the
            # habit) scored the same and outranked it, so "what is an emergency fund" and
            # "how much emergency fund do i need" both got "track two weeks of spending".
            "save up"),
           ("how", "what", "whats", "what's", "where", "any", "help", "should", "could", "best",
            "idea", "ideas", "tips", "advice", "start", "better at", "get better",
            "want", "wanted", "trying", "need", "intend",
            "never have anything left", "keep", "manage", "much", "each month", "every month")),
          "Track two weeks of what actually leaves the account before you change anything: the "
          "subscriptions you forgot are usually where it went. Then pick an amount you will not "
          "miss, 10 to 20 per cent of what you take home, and move it on pay day into a separate "
          "account you carry no card for, so saving happens before the spending. Build towards "
          "three to six months of essential bills as the buffer, and raise the standing order by "
          "10 pounds whenever a bill or a habit goes.",
          # The plainest way of saying it is not a question at all, and it was a shrug: "i want
          # to save money" scored the phrase "save money" on its own, three points, one short of
          # the bar, and "im trying to save money" did the same. Wanting to save is the ask.
          ask=("how", "what", "whats", "what's", "any", "help", "should", "could", "best",
               "ideas", "tips", "advice", "start", "better", "want", "wanted", "trying", "need",
               "intend", "help me"),
          # The maths domain owns "save 200 a month for a holiday" and a saving on a product is
          # shopping's; this is the habit, not the sum or the deal. "how do i save money moving
          # house" is the moving-cheap van tip in home.py.
          #
          # "save money on <a cost>" is the other question, and the cost nouns are listed by name
          # because a phrase in `avoid` matches those words anywhere, not next to each other: the
          # heating, fuel and energy entries in home.py all answer "how do i save money on my
          # heating bill", and "how do savings accounts work" is a bank question. A lost pot is
          # not a habit either - "my savings are gone and i dont know how" needs no lecture about
          # standing orders.
          # "daylight saving" carries the word "saving" and nothing else this card wants:
          # "whats the point of daylight saving" was answered with a spending tracker
          avoid=("daylight saving", "daylight savings", "summer time", "the clocks",
                 "how long", "per month for", "interest", "isa", "pension", "mortgage", "deal",
                 "cheaper", "coupon", "voucher", "insurance", "contract", "flight", "holiday",
                 "christmas", "student loan", "overdraft fee", "moving", "move", "removal", "van",
                 "sofa", "flat", "house",
                 # a saving on a bill or a tank of fuel
                 "heating", "boiler", "electricity", "energy", "gas", "water", "petrol", "fuel",
                 "bill", "bills", "broadband", "phone", "groceries", "takeaway", "subscription",
                 # a savings account, and money already lost
                 "account", "accounts", "rate", "rates", "bank", "gone", "lost", "losing",
                 # "for a rainy day" is the phrase this row is keyed on, and it is also how
                 # people ask what to do with a wet afternoon: "any ideas for a rainy day" was
                 # told to track two weeks of spending, and the wet-day card was left with no
                 # line at all. A day that is asking to be filled is that card's question.
                 "things to do", "something to do",
                 "bored", "kids are", "keeping the kids", "rainy day out",
                 # "any ideas for a rainy day" is the same wet-day question with an idea in
                 # front of it, and the idea words alone do not fence it off
                 "ideas for a rainy day", "rainy day ideas", "ideas for rainy days",
                 # a wet day to fill can be asked for with "what can i do" in front of "for a
                 # rainy day", and the phrase alone is enough to reach this row: that is a day
                 # question, not a saving one. A saving line keeps its own words ("save",
                 # "savings", "put by"), which is what "what can i do to save for a rainy day"
                 # has and this does not.
                 "what can i do for a rainy day", "what can we do for a rainy day",
                 "what can i do on a rainy day", "what can we do on a rainy day",
                 "what should i do on a rainy day", "what shall we do on a rainy day",
                 "film", "films", "movie", "movies", "watch", "watching", "tv", "telly",
                 "series", "box set", "netflix", "read", "reading", "book", "books",
                 "listen", "listening", "podcast", "game", "games",
                 # the music of a rainy day is the music row's too: "what music for a rainy day"
                 # was handed the two-week spending audit, because "for a rainy day" is the key.
                 "music", "song", "songs", "album", "albums", "playlist", "playlists",
                 "spotify", "tunes", "band", "bands",
                 # and anything to draw or doodle: "drawing ideas for a rainy day" was told to
                 # track two weeks of spending, for the same reason the films were
                 "draw", "drawing", "drawings", "doodle", "doodling", "sketch", "sketching",
                 "crayons", "colouring", "coloring", "paint", "painting",
                 # and which account to hold it in: "where should i keep my savings" wants the
                 # AER line, not a two-week spending audit
                 "where should i keep", "where do i keep", "where to keep", "keep my savings",
                 # a debt to clear first, which is its own advice
                 "credit card", "card", "pay off", "paying off", "debt", "debts", "overdraft",
                 "loan",
                 # and a person asking what they already told me: "what did i say i was saving
                 # for" is a recall, and answering it with the habit script loses the memory
                 "what did i say", "what did i tell", "did i say", "did i tell", "remind me",
                 "you said", "again"),
          guard=_a_rainy_day_is_money),
    # --- the stuck week, and the promise made at new year ---
    entry("out-of-a-rut",
          (("rut", "stuck", "same thing every day", "groundhog", "bored of my life",
            "bored of everything", "going nowhere", "in a slump", "slump", "plateau"),
           ("in", "get out", "getting out", "escape", "break", "how", "feel", "feeling",
            "again", "fix", "change")),
          "Change one thing you do on autopilot - a different walk, a new lunch, saying yes to the "
          "first invitation - because a rut is a loop of the same cues. Put one thing in the diary "
          "this week that you are looking forward to: the lift comes from having something ahead "
          "more than from willpower.",
          # a low mood that has lasted weeks is the health answer, and work ruts are the work one
          avoid=("depressed", "depression", "weeks now", "months now", "can't get out of bed",
                 "no pleasure", "anxious", "anxiety", "job", "career", "relationship",
                 "marriage", "running", "training", "weight", "gym",
                 # "stuck" is also the word for a jam, a queue and a puzzle
                 "traffic", "jam", "queue", "lift", "snow", "mud", "airport", "stuck on",
                 "stuck at", "stuck in a meeting", "stuck in the house", "stuck indoors",
                 "stuck with", "wheel", "drawer", "jar",
                 # a contract is a thing with a term and an exit fee, not a life that has
                 # looped: "am i stuck in a contract" was the change-one-thing answer on a base
                 # where the contract row's rank tied with this one
                 "contract", "contracts", "contractor", "cancellation", "minimum term",
                 # a cake stuck in its tin is the turning-out answer's line: "my cake is stuck in
                 # the tin" was being read as a life that is stuck
                 "cake", "cakes", "loaf", "sponge", "bun", "buns", "muffin", "muffins",
                 "bread", "tin", "tins", "baking", "pan", "tray", "mould", "pastry",
                 # and a card stuck in a cash machine is a card, not a life: money's
                 # card-in-the-machine answers that line, here and at the branch
                 "cash machine", "cashpoint", "atm", "card reader",
                 "chip and pin", "ticket machine", "parking machine",
                 # a thing stuck in a body is a symptom: "my throat feels like something is
                 # stuck in it" was getting change-one-thing-on-autopilot
                 "throat", "lump", "swallow", "swallowing", "swallowed", "something stuck",
                 # "i feel stuck" is a person saying how they feel, not asking for a plan
                 "i feel stuck", "feel stuck", "stuck in life", "feels stuck",
                 # ... and the commonest stuck thing of all is a machine or a part that will not
                 # move: "my bike is stuck in gear" was a loop of the same cues, and so was
                 # "im stuck in a gear". The same list has been grown one object at a time for
                 # years (traffic, cake, cash machine); this is the class rather than the objects,
                 # because any of them can jam and none of them is a life.
                 "gear", "gears", "gearbox", "derailleur", "chain", "chains", "chainring",
                 "pedal", "pedals", "cranks", "brakes", "brake", "clutch", "engine",
                 "wheel", "wheels", "handlebars", "saddle", "bike", "bikes", "bicycle",
                 "motorbike", "scooter", "mower", "lawnmower", "printer", "scanner",
                 "laptop", "computer", "tablet", "keyboard", "mouse", "phone",
                 "washing machine", "tumble dryer", "dishwasher", "vacuum", "fridge",
                 "freezer", "boiler", "radiator", "oven", "microwave", "toilet", "tap",
                 "shower", "door", "doors", "window", "windows", "gate", "zip", "zipper",
                 "button", "screw", "screws", "bolt", "bolts", "lock", "key", "keys",
                 # the shapes, because "stuck in gear" is said without the machine and a bare
                 # "gear" alone is not enough to see it
                 "stuck in gear", "stuck in a gear", "stuck in first", "stuck in second",
                 "stuck in third", "stuck in top gear", "stuck on the same gear",
                 "gears are stuck", "gears wont", "gears won't", "wont go into gear",
                 "won't go into gear", "wont shift", "won't shift")),
    # "january" is out of the key: a month is a word the memory store carries, so after
    # "my husband died in january" the next turn ("i keep going over that night") had that and
    # "keep", and a bereavement got "make it one resolution, ten minutes, not an hour".
    entry("new-year-resolution",
          (("new year", "new years", "resolution", "resolutions", "new year's"),
           ("keep", "keeping", "stick", "sticking", "goal", "goals", "promise", "start",
            "starting", "how", "make", "best", "good", "succeed")),
          "Make it one resolution, small enough to do on your worst day - ten minutes, not an hour "
          "- and tie it to something you already do, like a walk after your morning coffee. Mark "
          "the days you did it rather than the streak you broke, and if you miss once, the rule is "
          "never to miss twice.",
          avoid=("when is", "date", "eve", "party", "fireworks", "open", "closed", "traffic",
                 "dinner", "meal", "gym membership", "join",
                 # a loss is not a resolution, and the memory can carry "january" or "keep"
                 # into the turn after one
                 "died", "dies", "dying", "death", "dead", "passed away", "funeral", "killed",
                 "grief", "grieving", "loss", "lost him", "lost her", "lost them", "miss him",
                 "miss her", "miss them", "keep going over", "going over",
                 "over the last", "that night", "cant stop thinking", "can't stop thinking")),
    # "how do i set goals" and "how do i make a plan for the year" were both a search hedge: the
    # only goal card needed the word "resolution", which is how the question is asked in January
    # and almost never in November.
    entry("how-to-set-a-goal",
          (("goal", "goals", "goal setting", "set a goal", "set goals", "plan for the year",
            "yearly plan", "five year plan", "5 year plan", "3 year plan", "life plan",
            "plan my year", "plan my life", "what i want to achieve", "achieve", "ambition"),
           ("how", "set", "setting", "make", "making", "write", "start", "stick", "keep to",
            "better", "worth", "should i", "realistic", "realistically", "stuck", "no idea")),
          "Pick one theme for the year rather than ten goals, then turn it into three actions with "
          "dates: \"run 5k by June - book a race in January, run twice a week\" does more than "
          "\"get fit\". Make each one small enough to start in ten minutes on a bad day, put the "
          "first step in the diary this week, and look at the list once a month rather than every "
          "day. Two things that raise the odds: write them down where you will see them, and tell "
          "one person.",
          # a resolution is the January version of the same question, and a saved or spent target
          # is the money row's
          avoid=("new year", "resolution", "resolutions", "save", "saving", "savings",
                 "deposit", "pension", "budget", "calories", "weight", "marathon", "training",
                 "revision", "exam", "deadline", "workout", "gym"),
          bias=1),
    # "what should i do with my life" was the plainest line in the whole area and the only answer
    # was a shrug: every nearby row wants a named subject (a job, a rut, a resolution).
    entry("what-to-do-with-my-life",
          (("what should i do with my life", "what to do with my life",
            "what do i do with my life", "dont know what to do with my life",
            "don't know what to do with my life", "no idea what to do with my life",
            "what next in life", "direction in life", "purpose in life", "my purpose",
            "where am i going", "what am i doing with my life", "find my purpose"),
           ("what", "how", "should", "find", "figure", "work out", "decide", "lost", "stuck",
            "confused", "help", "advice", "next")),
          "Don't try to answer the whole of it at once. Write three short lists: what you are good "
          "at (the things other people ask you for, not what you would like to be good at), what "
          "you would do for free, and what you need money for. Then pick one small experiment that "
          "touches two of the three - a course, a volunteering shift, a paid side project - and "
          "give it three months, because direction comes from doing rather than deciding. Keep "
          "whatever you would happily do again.",
          # a low mood, a job, a course and a relationship each have their own card
          avoid=("depressed", "depression", "anxious", "suicidal", "weeks now", "months now",
                 "cant get out of bed", "career change", "apply", "ucsas", "ucas", "course fees",
                 "my job", "my boss", "my partner", "my husband", "my wife", "boyfriend",
                 "girlfriend", "divorce", "break up", "grief", "died", "funeral"),
          bias=1),
    # --- a day out that costs nothing ---------------------------------------------
    # "free things to do with kids", "cheap family day out", "what can i do for free this
    # weekend": the money is the constraint, not the subject. The answer names the free days out
    # that exist (a walk with a purpose, a free museum, the library, a market) and what the day
    # actually costs, which is the part people are asking about.
    entry("free-day-out",
          # "im skint and want to do something nice with my mum" said the constraint the way people
          # say it - skint, broke - and the row never saw it, so the line fell to an echo of itself.
          (("free", "cheap", "cheaper", "no money", "not much money", "skint", "broke",
            "dont cost",
            "doesnt cost", "thank mustnt", "tight budget", "on a budget", "low cost"),
           # "i want to do something nice with my mum but i have no money" and "im skint and want
           # to do something nice with my mum" reached the money-to-last row and came back as a food
           # bank, then as an echo of their own line: the wish is the same wish as a free day out,
           # so the same words carry it.
           ("day out", "days out", "things to do", "something to do", "something nice",
            "something special", "what can i do",
            "what can we do", "where can we go", "where can i go", "near me", "this weekend",
            "at the weekend", "with the kids", "take the kids", "with children", "family")),
          "Free ones that work: a walk with a purpose (a park, a canal, the woods, a hill with a "
          "view - flask in the bag), a museum or gallery with free entry, the library, or a "
          "Saturday market. With kids, add a list of five things to find and a ball. Take snacks "
          "and a drink, and the day costs you parking and a coffee.",
          bias=1,
          # "cheap meal ideas" and "free food" are the money-and-food entries, not a day out.
          avoid=("meal", "meals", "food", "eat", "eating", "dinner", "lunch", "tea",
                 "breakfast", "takeaway", "cook", "cooking", "recipe", "recipes", "bake",
                 "baking", "shop", "shopping", "grocery", "groceries", "supermarket",
                 "film", "films", "movie", "watch", "book", "books", "read", "reading",
                 "freezer", "freeze", "sugar free", "gluten free", "dairy free", "free range",
                 "car", "cars", "van", "insurance", "rent", "bill", "bills", "delivery",
                 "postage", "sim", "tariff", "subscription", "mobile",
                 # a present is a shopping question, and "cheap christmas present ideas" was
                 # this answer for a day out until #3121's "ideas" key reached it
                 "present", "presents", "gift", "gifts", "secret santa", "stocking",
                 "stocking filler")),

    # "what can i do this weekend thats cheap", "cheap things to do as a family", "something to
    # do on saturday without spending much": a plan with no money in it. The line has both halves
    # - a wish for something to do, and the day or the budget it has to fit - so it is one row
    # rather than one row per phrasing, and the answer is shapes of day rather than a list of
    # places the bot cannot know.
    entry("cheap-things-to-do",
          (("things to do", "something to do", "what can i do", "what should i do", "what to do",
            "what can we do", "what should we do", "anything to do", "ideas", "activities",
            "activity", "day out", "days out", "afternoon out"),
           # the second half is the day or the budget. Two lessons from the first version of
           # this row: a phrase like "no money" in a key puts the word money into the domain'"'"'s
           # rarity table and other entries lose their ties, and a child in the line is the kids
           # answer in family.py, not this one.
           # "im skint what can i do" is the money problem, not the budget an outing fits: the
           # words skint and broke were in this tuple and took four of those lines off the
           # two-calls-that-free-up-cash answer, so they are gone and "free" carries the line.
           ("weekend", "saturday", "sunday", "free", "cheap", "cheaply",
            "budget", "family", "everyone", "at home", "indoors", "outside")),
          ("Pick one shape and put a time on it, because a free day with no plan turns into the "
           "sofa. The ones that cost nothing: a walk with a destination (a park, a canal, a hill, "
           "a shop that sells something you like), a free museum or gallery - most have a permanent "
           "collection that costs nothing - and the library, which has events, papers and warmth. "
           "At home: a film nobody has seen, a bake with whatever is in the cupboard, a swap of "
           "clothes or books with friends, or a board game with a rule that the phones stay in "
           "another room. For a family, one outside thing in the morning and one quiet thing after "
           "lunch is plenty: children remember the day that had a walk and a picnic in it, not the "
           "one that cost forty pounds."),
          # the food, the trip, the money and the bored-at-work lines are their own questions,
          # and "what should i do with the children this afternoon" is the kids answer
          avoid=("recipe", "cook", "cooking", "dinner", "lunch", "tea", "eat", "meal", "back",
                 # "cheap breakfast ideas" is the breakfast list, not a cheap day out: the food
                 # words above cover dinner and lunch, and breakfast was the one still missing
                 "breakfast", "breakfasts", "brunch", "snack", "snacks", "packed lunch",
                 "pain", "knee", "doctor", "gp", "work", "job", "boss", "office", "school run",
                 "hotel", "flight", "flights", "abroad", "holiday", "leave my", "quit",
                 # a break somewhere is a trip, not a free afternoon: "cheap city break ideas"
                 # was getting the free-day-out card, and travel's weekend-away is the answer.
                 # Matched as phrases, because "take a break" is this row's own line.
                 "city break", "city breaks", "weekend away", "weekend break", "break away",
                 "night away", "couple of nights", "few nights", "weekend in",
                 "rent", "bills", "benefits", "save money", "savings", "invest", "loan", "debt",
                 "kids", "children", "child", "toddler", "baby", "year old", "entertain",
                 "keep busy", "stuck inside", "bored", "boring", "half term",
                 # weather that is a danger is a safety question with its own answer, not a
                 # free afternoon: "what should i do if i'm caught outside in a thunderstorm"
                 # got the shapes-of-a-day card while nature.py had the answer to it.
                 "thunderstorm", "thunderstorms", "lightning", "thunder",
                 "flood", "floods", "flooding", "flooded",
                 # "free" is the no-money sense of a day out here, and it is also the tail of
                 # every diet: "im dairy free" then "what can i do with a courgette" was the
                 # free-day-out card, and the same line after "im gluten free" was the
                 # gluten-free bake. A diet is a diet question, whoever said it (#6561 on main,
                 # found by main watch 107). Matched as phrases so "freezer" and "free range"
                 # are not read as a free afternoon either.
                 "dairy free", "gluten free", "gluten-free", "sugar free", "sugar-free",
                 "wheat free", "egg free", "nut free", "meat free", "fat free", "lactose free",
                 "caffeine free", "alcohol free", "free from", "free range", "freezer", "freezers",
                 "frozen", "duty free", "hands free", "hands-free", "free trial",
                 # a present is a shopping question, and "cheap christmas present ideas" was
                 # this answer for a day out (free-day-out already stands down on it)
                 "present", "presents", "gift", "gifts", "secret santa", "stocking",
                 "stocking filler"),
          bias=1,
          # "any ideas for cheap party food" and "any ideas for a cheap date" name a thing
          # of their own; this row is the day out for a line that names nothing but a budget.
          # And the free afternoon has to be the subject: "what can i do about my boiler today"
          # is the boiler's question whatever day it is. Main's own guard reads the ache and the
          # thing-idea cases; this one is the wider reading, and it stands beside it.
          guard=lambda reading: (_a_day_out_is_the_question(reading)
                                 and _a_stretch_of_time_to_fill(reading))),

    # A dish named for tonight is a meal being planned, and it was answered by a day out:
    # "im planning a curry tonight" got the weather-and-a-walk card from `weekend-ideas`, and
    # "ok changing the subject, im planning a curry tonight" got a revision timetable from the
    # school domain before that (airy-deer, #4083). "Tonight" is a day word, so every row that
    # keys on a day is entitled to the line; a dish is what makes it food. The recipe reads
    # cooking.RECIPES rather than repeating it, so a dish re-worded there is re-worded here.
    entry("dish-for-tonight",
          (tuple(alias for aliases, _keys, _body, _avoid in RECIPES for alias in aliases),
           ("tonight", "this evening", "this afternoon", "for tea", "for dinner", "for supper",
            "for lunch", "later", "this weekend", "tomorrow night"),
           # the plan has to be a plan: "how long does a curry take" and "what goes with curry"
           # are the cooking table's own questions, and they name no evening
           # the plan has to be a plan, not the cooking: "im making a curry tonight" is the
           # kitchen's own card and reads better than a recipe read out here, so "making" and
           # "cooking" are not in this group
           ("planning", "planning on", "plan", "plans", "planned", "fancy", "fancied",
            "i might", "shall i", "should i", "decided to")),
          _dish_for_tonight,
          # A diet rule, a fault and a keeping question are all other answers to the same dish:
          # "im planning a curry tonight but one guest is vegan" wants the diet swap, and
          # "my curry went wrong" is the repair card.
          #
          # A rank that only breaks ties: the kitchen's own card for a dish is better written
          # than anything here ("im making a bolognese tonight" wants "Spag bol: an hour start to
          # finish...", not the same recipe read out), so this row answers only the lines that
          # named the dish and nothing else claimed.
          bias=-3,
          avoid=("went wrong", "too thin", "too thick", "too salty", "bland", "burnt",
                 # the open "what shall i cook" is a request for an idea, and the idea rows
                 # already answer it: a dish named in the line is a plan, an ask with no dish
                 # named is a suggestion
                 "what should i cook", "what can i cook", "what shall i cook", "what to cook",
                 "what should i make", "what can i make", "what should i eat", "what can i eat",
                 "whats for", "what's for", "what to eat", "meal ideas", "dinner ideas",
                 "watery", "dry", "recipe", "how long", "how do i", "what goes with",
                 "vegan", "vegetarian", "veggie", "dairy", "gluten", "wheat", "allergic",
                 "allergy", "coeliac", "celiac", "intolerant", "calories", "healthy",
                 "keep", "keeps", "store", "freeze", "leftover", "left over", "reheat",
                 "restaurant", "takeaway", "shop", "buy", "supermarket", "tesco", "aldi",
                 # a line that says it is making the dish is the kitchen's: only the plan with
                 # no cooking in it is left, because "im making a curry tonight" has a card of
                 # its own and that card reads better than a recipe read out here. "doing" is the
                 # same verb in people's mouths - "im doing a spag bol tonight" was the bolognese
                 # recipe read out, where the plan card says the time first.
                 "make", "makes", "making", "made", "cook", "cooks", "cooking", "cooked",
                 # and the first person saying it is happening now, which the bare words miss:
                 # "im doing a spag bol tonight" was this row reading the bolognese recipe out,
                 # where the plan card says the time first. The plan-led shapes stay here -
                 # "thinking of doing", "i fancy", "i think ill do" - because those name no
                 # kitchen yet.
                 ) + ANNOUNCED_DISH),

    # --- something to try once ---------------------------------------------------
    # "what's something everyone should try at least once", "suggest something i've never
    # done": one of the commonest things people ask a friend, and the bot had nothing for it.
    # The line names no subject at all, so no keyed row could reach it and every one of these
    # got the search hedge. The answer is a pool of one-off experiences, handed over whole so
    # `pick` keeps a person asking twice from hearing the same thing.
    entry("try-once",
          (("try once", "tried once", "at least once", "once in my life",
            "once in a lifetime", "never done", "never tried", "never have i", "ive never",
            "i have never", "something new", "something different", "new thing",
            "worth trying", "something to try", "one thing to try", "bucket list",
            "everyone should try", "everyone should do", "everyone should have",
            "everyone has to do", "wouldnt think of", "try next", "something ive not",
            "before i die", "missing out"),
           TRY_ONCE_ASK),
          _try_once,
          # The pool has no subject of its own, so any line that names one is somebody else's
          # answer: "something new to try with chicken" is a recipe, "something new to try at
          # the gym" is a training question.
          # A "new thing" line is only this pool's when it asks for a suggestion. "What's the
          # new thing at McDonald's" names a menu and asks nothing, and the asking words are
          # what tell the two apart.
          ask=("try", "tried", "trying", "should", "suggest", "recommend", "tell", "give",
               "idea", "ideas", "anything", "something", "one thing", "surprise", "once",
               "want", "need"),
          # The habit row is keyed on "something new" too, because "i want to start something
          # new every day" is a habit question. A line that asks for something to try is
          # asking what to pick, which is this pool, and the habit row still answers "how do i
          # make it stick" on its own words. Both rows reach these lines on the same words, so
          # the nudge is what decides it. It has to beat the habit row outright rather than
          # tie: two rows that fit equally well are settled by the registry's order, and which
          # one that is moves whenever a row is added to this domain.
          bias=6,
          avoid=("cook", "cooking", "recipe", "recipes", "dinner", "lunch", "breakfast",
                 "tea", "bake", "baking", "food", "restaurant", "meal", "meals",
                 "gym", "workout", "training", "running", "run", "diet", "exercise",
                 "hair", "skin", "garden", "plant", "plants", "decorate", "paint",
                 "job", "jobs", "career", "interview", "course", "holiday", "trip",
                 "city", "town", "hotel", "shop", "shopping", "buy", "money",
                 "song", "album", "band", "film", "films", "book", "books", "series",
                 "game", "games", "music", "podcast", "tv", "netflix", "sport",
                 "booked", "already", "tried it", "tried that", "didnt like",
                 "not for me", "went wrong",
                 # a habit is a thing to keep doing, not one to try: "i want to start
                 # something new every day" is the habit row's question, so a line that says
                 # "every" or "each" is left to it whatever unit of time follows
                 "every", "each", "daily", "everyday", "weekly", "monthly", "routine",
                 "habit", "habits", "regularly", "stick to", "keep it up")),
    # "Give me another one", "one more idea to try" - said to the pool above, which is the only
    # thing that can tell what "another" means here. The reply function turns the row down
    # unless the last thing the bot said was one of the pool's, so a cooking list, a joke or a
    # riddle keeps its own "another one".
    entry("try-once-more", TRY_ONCE_MORE, _try_once_more, bias=4,
          avoid=("cook", "cooking", "recipe", "dinner", "food", "paint", "garden")),
]
