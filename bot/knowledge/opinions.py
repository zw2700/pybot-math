"""Opinions and small choices: the bot's own taste, given briefly and with a reason.

People ask the bot what it thinks more often than they ask it for a fact: "cats or dogs?",
"what do you think is the best season", "is it worth learning an instrument at 45". STYLE.md
allows the bot to have tastes, so this domain keeps them as data, one Entry per subject, and
answers only when the line really is a question or a choice: a statement that merely mentions
the subject ("my favourite season is autumn", "we split the bill") is left to the modules that
can help with it.

Two shapes of entry:
* a plain subject ("season", "pizza topping") answers an opinion question about it;
* `_either` pairs two everyday things and answers only when the line is a choice between them,
  in either order ("tea or coffee", "which is better, paper or an e-reader").
"""
import re

from .entertainment import the_book_is_a_reservation
from .lookup import asks_where_a_shop_answers, entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("opinions",)

# A line carrying one of these, a question mark, or four words or fewer is the person asking
# the bot rather than telling it something. "Cats or dogs?" and "tea or coffee" are asks with no
# question word, which is why the short-line rule is there; a short line that talks about the
# person ("we split it", "my favourite is autumn") is still a statement, not a question.
ASK_MARKERS = frozenset("""
    you your better rather which opinion pick recommend worth should would
    ok okay rude fine wrong right good bad
""".split())
# "I think cats are better than dogs" tells the bot something; it does not ask. `think` and
# `prefer` used to be ask markers, so every first-person statement of taste got the take and
# contradicted the person about their own pets, season or pizza. A line that states its own
# opinion passes unless it also turns to the bot ("... but what do you think?").
OWN_OPINION = re.compile(
    r"\b(i think|i thought|i prefer|i'd prefer|id prefer|i believe|i reckon|i feel|"
    r"i'd say|id say|i say|in my opinion|personally|for me|to me)\b")
FIRST_PERSON = frozenset("i i'm im me my mine we we're were our ours us myself".split())
# A statement of intent about the subject is a request for help with it ("I want to start a
# diary", "thinking of learning the guitar"), unlike a report of what happened ("I bought an
# air fryer yesterday and I love it"), which passes.
INTENT = ("want to", "wanted to", "wants to", "thinking of", "thinking about", "planning to",
          "plan to", "tempted to", "considering", "keen to", "hoping to", "too late",
          "at my age", "old age")
# "Why is it hotter in summer than in winter?" names both halves of a pair but asks for a
# explanation, not a preference. Unless it is about the bot's own taste ("why do you prefer
# tea"), an explanation opener is a fact question and belongs to a knowledge domain.
EXPLAINS = re.compile(r"^\s*(why|how come|what makes|what causes|explain|what's the reason)\b")


# The parts a person can name instead of the fault, and the jobs they do to one. Both halves are
# needed, because either alone is an ordinary word: "how do i clean the shelves in my fridge" is
# a cleaning question and "my filter coffee maker" is not a part.
_A_PART = ("filter", "filters", "seal", "gasket", "drawer", "drum", "hose", "latch", "pump",
           "door", "lid", "tray", "paddle", "blade", "element", "shelf", "shelves", "basket",
           "spray arm", "cutting blade", "jug", "carafe", "pump filter")
_A_JOB = ("clean", "cleaning", "gunk", "blocked", "blocking", "smell", "smells", "mould",
          "mold", "broke", "broken", "torn", "split", "cracked", "leaking", "jam", "jammed",
          "will not", "wont", "won't", "fix", "replace", "stuck", "clogged", "descale",
          "scrub", "empty it", "get it out", "get the gunk out")
_BUYING = ("worth it", "worth buying", "should i buy", "is it worth", "buy a", "buying a")


def _worth_an_appliance(memory, understood):
    """The buy-it-or-not rule for a machine the table has no row for, worded about its name.

    The generic sentence was the answer to "is a dishwasher worth it", and a rule of thumb that
    opens "Worth it if you would use it three times a week" never says which machine it is
    talking about, so the reader has to check it is their question. The name in their line is
    the cheapest way to say yes, this one.
    """
    # The longer phrase first: "is a robot vacuum worth it" is not a plain vacuum cleaner.
    names = (("robot vacuum", "robot vacuums", "robot hoover"),
             ("dishwasher", "dishwashers"), ("tumble dryer", "tumble dryers", "dryer"),
             ("washing machine", "washing machines"), ("slow cooker", "slow cookers"),
             ("bread maker", "bread makers"), ("blender", "blenders"),
             ("food processor", "food processors"), ("pressure cooker", "pressure cookers"),
             ("vacuum", "vacuum cleaner"), ("hoover", "hoovers"), ("freezer", "freezers"))
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    # A part of the machine with a job on it is a repair, not a purchase to weigh up: "the
    # dishwasher filter is full of gunk, how do i get it out" was told a dishwasher is worth it if
    # you would use it three times a week. `FAULT` in the entry's avoid catches the faults said
    # with a fault word, and this catches the ones said with a part and a job instead. The buy
    # words keep the questions this rule is for - "is a water filter worth it" is still a buying
    # question, because a filter is not a part of a machine here, it is the machine.
    if (any(part in said for part in _A_PART) and any(job in said for job in _A_JOB)
            and not any(buy in said for buy in _BUYING)):
        return ""
    # Two of the short names are also pieces of other machines' phrases: a "hair dryer" and a
    # "nail dryer" carry "dryer", and a "vacuum flask" carries "vacuum". Naming the wrong machine
    # is worse than the generic sentence, so those phrases come out of the line before the names
    # are looked for, and the line falls back to "It is worth it if ...".
    # A heat pump or a condenser dryer has its own row with the running costs in it, and this
    # rule of thumb was answering "is a heat pump dryer worth it" instead. A None reply does not
    # hand the line to that row, though - it ends the turn with a shrug - so the line that names
    # the machine by name is left to the row that has the numbers, and the "should i get" shape
    # keeps this rule of thumb rather than becoming a punt.
    # The shapes that ask whether the machine is a good buy are the row's question, in every
    # wording: "is a heat pump dryer worth it", "is a heat pump dryer any good", "are heat pump
    # dryers any good", "should i get a heat pump dryer". The how-it-works shape - "do heat pump
    # dryers need a vent" - is not a buying question, and this rule of thumb is the only reply
    # main has for it, so that one keeps it.
    if ("heat pump" in said and ("dryer" in said or "drier" in said)
            and any(buy in said for buy in _BUYING + ("any good", "good", "worth", "worth it",
                                                      "should i get", "should i buy", "get one"))):
        return None
    for other in ("hair dryer", "hair drier", "hairdryer", "nail dryer", "vacuum flask",
                  "flask", "thermos"):
        said = said.replace(other, " ")
    thing = None
    for forms in names:
        if any(form in said for form in forms):
            thing = forms[0]
            if forms[0] in ("vacuum", "hoover"):
                thing = "vacuum cleaner" if "vacuum" in said else "hoover"
            break
    article = "an" if thing and thing[0] in "aeiou" else "a"
    subject = f"{article} {thing}" if thing else "it"
    return (f"{subject.capitalize() if thing else 'It'} is worth it if you would use it three "
            "times a week or more and it saves a job you dislike; skip it otherwise, because it "
            "takes up a cupboard. Buy the cheap one first, because most of these are replaced by "
            "a better model you only learn you wanted after a year of using the first.")


# What makes each machine earn the counter space it takes, for the line where the person has
# already got it. "i've got a slow cooker" was answered with the buying test - "three uses a week
# and it was a good buy" - which is advice for someone still deciding, not for someone holding one
# who wants to know what to do with it. One tip each, and the tip is the one thing that goes wrong.
_GADGET_TIPS = (
    (("slow cooker", "slow cookers", "crock pot", "crockpot"),
     "Brown the meat in a pan first and leave the lid on, because every lift of the lid is twenty "
     "minutes of heat gone: six to eight hours on low does what four on high cannot, and shin, "
     "shoulder and chicken thighs come out better than anything you would roast."),
    (("air fryer", "air fryers"),
     "Fill the basket no more than two-thirds and shake it halfway, because a crowded basket "
     "steams instead of crisping. Treat it as a fan oven twenty degrees cooler and a fifth less "
     "time: chips at 200C for eighteen minutes with one shake, chicken thighs at 190C for "
     "twenty-five."),
    (("bread maker", "bread makers", "bread machine", "bread machines"),
     "Use it for the dough and bake the loaf in the oven, because the machine's own bake gives a "
     "squat loaf with a pale top and a hard crust. Three-quarters of a teaspoon of yeast for a "
     "500g loaf is plenty when it proves slowly."),
    (("blender", "blenders", "smoothie maker", "smoothie makers", "nutribullet"),
     "Liquid in first, then the soft things, then anything frozen, and never more than half full "
     "of solids: start on the lowest speed and pulse, because full speed from cold throws the lot "
     "into the lid."),
    (("food processor", "food processors", "magimix"),
     "Pulse rather than hold, because pastry, mince and pesto are a series of short bursts and a "
     "long run turns them to paste. Add anything wet through the tube while it is running and it "
     "mixes in evenly instead of pooling at the bottom."),
    (("stand mixer", "stand mixers", "kitchenaid", "kenwood"),
     "Paddle for cakes, dough hook on the slowest speed for bread, whisk only for eggs and cream. "
     "Stop at the time in the recipe rather than watching the bowl, because an over-mixed cake "
     "comes out flat and tough."),
    (("pressure cooker", "pressure cookers", "instant pot"),
     "Never fill past two-thirds, and let meat drop from pressure on its own for ten minutes, "
     "because a quick release pulls the steam out of the middle and leaves it stringy. Soaked "
     "beans and stewing steak are where it beats the slow cooker on a weekday."),
    (("juicer", "juicers"),
     "Feed soft fruit in with the hard, and wrap leaves in a lettuce leaf so they go down instead "
     "of clogging the mesh. Rinse the basket straight away, before the pulp dries onto it."),
    (("coffee machine", "coffee machines", "bean to cup", "espresso machine", "sage barista"),
     "Weigh the beans rather than scooping - about 18g in for a double - and descale every couple "
     "of months, because scale is what drops the temperature and makes every cup taste flat."),
    (("sandwich toaster", "sandwich toasters", "toastie maker", "panini press"),
     "Butter the outside of the bread, not the inside, and keep the filling an inch from the "
     "edges: cheese in the hinge is what gets these thrown away."),
    (("rice cooker", "rice cookers"),
     "Rinse the rice until the water runs clear, then one part rice to one and a half parts "
     "water. Leave it on warm for an hour at most, because past that the bottom sets and it "
     "starts to smell."),
    (("ice cream maker", "ice cream makers"),
     "Chill the bowl overnight and the mix in the fridge as well, because a warm mix churns to "
     "slush. Take it out while it is still soft, since it sets hard once it is in the freezer."),
)

_VERDICT_ASK = ("think", "reckon", "opinion", "worth", "any good", "recommend", "like my",
                "regret", "good buy", "waste", "rate my", "should i keep")

_THE_VERDICT = ("The honest test is whether it earns its counter space: three uses a week and it "
                "was a good buy, once a month and it lives in a cupboard. Give it a month of "
                "proper use before you decide, and keep one recipe you like so it is not a "
                "project every time.")


def _gadget_view(memory, understood):
    """A tip for the machine they already have, or a verdict when it is the machine being judged.

    "what do you think of my new blender" asks for a view, so it keeps the counter-space test.
    "i've got an air fryer" asks nothing and is asking what to do with it, so it gets the one tip
    that machine needs. A machine the table does not name gets the verdict, which is still true
    of anything.
    """
    said = " ".join(str(word) for word in ((understood or {}).get("words") or ())).lower()
    if not said:
        said = str((understood or {}).get("text") or "").lower()
    if any(ask in said for ask in _VERDICT_ASK):
        return _THE_VERDICT
    for forms, tip in _GADGET_TIPS:
        if any(form in said for form in forms):
            return tip
    return _THE_VERDICT


def _asked(reply):
    """A reply, but only to a line that asks: a statement about the same subject passes."""
    def answer(memory, understood):
        if not isinstance(understood, dict):
            return None
        words = set(understood.get("words") or ())
        text = str(understood.get("text") or "").lower()
        if EXPLAINS.match(text) and not words & {"you", "your", "yourself"}:
            return None
        def said():
            return reply(memory, understood) if callable(reply) else reply

        if understood.get("kind") == "question":
            return said()
        words = understood.get("words") or ()
        line = " ".join(understood.get("words") or ())
        full = str(understood.get("text") or "").lower()
        if any(marker in line for marker in INTENT) or any(
                marker in full for marker in INTENT):
            return said()
        # The person's own opinion, not a request for the bot's: "i think my cat is better than
        # my dog". The ask markers below (better, rather, which) are what made these fire.
        if OWN_OPINION.search(full) and not set(words) & {"you", "your", "yourself", "yours"}:
            return None
        if set(words) & ASK_MARKERS:
            return said()
        if len(words) <= 6 and not set(words) & FIRST_PERSON:
            return said()
        return None
    return answer


# A comparison is asked with a comparative as often as with "or": "are cats easier than dogs",
# "is a bike cheaper than a car", "is it simpler to move or sell". Those words are comparison
# markers in their own right, the same way "or" is, so a pair pick answers them; the pair still
# has to be named on both sides, which is what keeps "how do i make ironing easier" out.
CHOICE = frozenset((
    "or vs versus better prefer rather which either "
    # the comparatives: "are cats easier than dogs", "is a bike cheaper than a car", "which is
    # cleaner". A comparative on its own is the comparison, so the pair pick answers it, and the
    # pair still has to be named on both sides.
    "easier harder cheaper simpler quicker cleaner quieter calmer friendlier healthier "
    "more work less work more expensive less expensive").split())

# The words that make a line a request for the bot's take on a thing rather than a mention of
# it: "what do you think about air fryers", "whats your opinion on air fryers", "do you rate
# air fryers" and "are air fryers worth it" are one question, so every taste entry keys on all
# of them instead of guessing at the phrase someone happened to use.
TASTE = ("worth", "worth it", "buy", "buying", "get", "getting", "need", "recommend",
         "any good", "good", "think", "opinion", "reckon", "rate", "prefer", "better")


CHOICE_ASKS = ("should i", "shall i", "should we", "is it worth", "would i be better")

# The words that put two things as a choice rather than a list, which `_either` needs before it
# will answer a line that carries no question word: "air fryer or slow cooker", "butter or
# margarine in a cake", "train rather than drive", "tea vs coffee".
CHOICE_IN_WORDS = re.compile(r"(?:^|[^a-z])(?:or|vs|versus|rather than|instead of)(?:[^a-z]|$)")

# The words that make a pair a question about which rather than a report of what the person does:
# "should i use butter or margarine" asks, "i like tea or coffee in the morning" tells.
CHOICE_ASK_WORDS = frozenset("should shall would which better rather worth recommend pick "
                             "choose prefer".split())


def _is_a_choice(understood):
    """True when the line compares two things: a choice word, or a question that picks one.

    "im 34 and still renting, should i be buying" names both halves and asks which, without any
    "or" in it.
    """
    if set(understood.get("words") or ()) & CHOICE:
        return True
    text = " " + " ".join(understood.get("words") or ()).lower() + " "
    return any(phrase in text for phrase in CHOICE_ASKS)


def _names(understood, options):
    """True when the line names one of these things, in any of the ways people write it."""
    text = " ".join(understood.get("words") or ()) or str(understood.get("text") or "")
    text = " " + text.lower() + " "
    return any(option in text for option in options)


# A verdict on whether to buy a thing answers a yes-or-no question about it, and these are not
# that question: "which washing machine should i buy" wants a spec, and "what do you think of my
# new blender" is a report about a machine they already own. Both go in `avoid` rather than a
# check inside the reply, because a reply that politely declines still holds the line: the
# matcher has already handed the entry the line, so the domain's other answer never gets it.
# Appliances that already have a proper buying answer elsewhere in the knowledge base. The rule
# of thumb above passes on them rather than replacing a better answer with a worse one.
OWN_BUYING_ANSWER = ("new washing machine", "buying a washing machine", "washing machines",
                     "new dishwasher", "buying a dishwasher")

NOT_A_BUYING_ASK = ("which", "my new", "my old", "i bought", "i've bought", "i got", "i've got",
                    "we bought", "we got", "i own", "we own")
# Somebody getting rid of a machine is not weighing up buying one: "how do i get rid of the old
# freezer" was a take on whether a freezer is worth it, because a freezer name and the bare word
# "get" are all the taste key asks for. Where a thing goes is `rubbish.py`'s question, and it has
# a row for the fridge, the freezer, the white goods and the mattress.
DISPOSAL = ("get rid of", "getting rid of", "got rid of", "throw away", "throwing away",
            "throw it out", "throwing it out", "throw out", "tip", "the tip", "recycling centre",
            "dump", "dumped", "dumping", "dispose", "disposal", "scrap", "scrapping", "scrapped",
            "recycle", "recycling", "bulky waste", "bulky collection", "collection", "collect it",
            "take it away", "taking it away", "unwanted", "no longer want", "dont want it",
            "don't want it", "getting a new one", "replace it")

# A machine that is misbehaving is a fault to fix, not a purchase to weigh up. Without these, a
# line like "ok good. my washing machine wont drain and there is water everywhere" ticked a taste
# word ("good") on the appliance name and got the should-I-buy-one answer instead of the drain.
# "is it worth paying a plumber or should i have a go" is a fault someone is deciding how to fix,
# not a purchase to weigh up, so the trades are not a taste word on the appliance either.
# A line that asks how to do a job on the machine is not weighing up buying one. TASTE carries the
# bare verb "get", so "how do i get dog hair out of the tumble dryer" got "a dryer is worth it if
# you would use it three times a week" - a confident answer about something else. The shapes are
# the how-to ones, and "is a tumble dryer worth it for pet hair" stays a buying question.
# Every shape here is a phrase, never a bare verb: "clean the" folds onto "cleaning the" and took
# "is a cordless vacuum worth it for cleaning the car" off its buying answer.
A_JOB_ON_IT = ("how do i get", "how to get", "how do i clean", "how to clean", "how do i remove",
               "how to remove", "how do i clear", "how to clear", "how do i stop the",
               "hair out of", "lint out of", "fluff out of", "clean out", "cleaned out",
               "unblock", "clear the", "get the smell out", "get rid of the smell")
TRADES = ("plumber", "electrician", "gas safe", "have a go", "have a bash", "pay someone",
          "call someone", "call a man", "get someone in", "tradesman", "handyman", "diy",
          "myself", "or should i have a", "worth paying", "paying someone")

FAULT = ("wont", "won't", "isnt", "isn't", "doesnt", "doesn't", "cant", "can't", "cannot",
         "drain", "draining", "leak", "leaking", "leaked", "broken", "broke", "fault", "faulty",
         "error", "flashing", "not working", "stopped", "stop", "flood", "flooded",
         "water everywhere", "smell", "smells", "smelly", "repair", "repairs", "repairing",
         "fix", "fixing", "stuck", "noise", "noisy", "loud", "rattling", "grinding", "dead",
         "warranty", "guarantee",
         # A symptom is a fault said as a job to do, in a line with no "wont" and no "broken" in
         # it: "i cant get my dryer to heat up" and "my dryer takes ages to dry" both came back
         # with the should-I-buy-one take, which is the wrong question about a machine in the
         # kitchen. The cause named is what makes the line a fault, so the cause words are here.
         "not heating", "isnt heating", "wont heat", "no heat", "heat up", "not spinning",
         "wont spin", "not turning", "wont turn", "not drying", "wont dry", "takes ages",
         "still wet", "still damp", "engineer", "engineers", "call someone out")


def _either(id, a, b, reply, avoid=(), bias=0):
    """A pick between two everyday things, in either order, only when the line is a choice.

    Both things have to be named and a word that makes it a comparison has to be there too
    ("tea or coffee", "coffee vs tea", "which is better"), so a line that merely mentions both
    ("my cat keeps chasing the dog", "hotter in summer than in winter") is not a question.

    A choice outranks a plain entry that only noticed one half of it ("should i get a cat or a
    dog" beats the kitten shopping list) through one point of bias, not by putting the choice
    words in the key: "or" and "which" are in half the language, and an entry that matches them
    is a match the answers lane then has to pass on.
    """
    def answer(memory, understood):
        if not isinstance(understood, dict):
            return None
        if not _is_a_choice(understood):
            return None
        # Both halves have to be named: "is it better to walk or cycle" is not the run-or-walk
        # entry's question just because it says walk.
        if not (_names(understood, a) and _names(understood, b)):
            return None
        said = _asked(reply)(memory, understood)
        if said is not None:
            return said
        # Both halves named with an "or" between them is the question, even with no question
        # word and no question mark: "air fryer or slow cooker", "butter or margarine in a cake",
        # "train or drive to edinburgh". `_asked` declined every one of those for being a
        # statement, so the pair fell to whichever card owned one of the two names - a shelf
        # over the door for a small kitchen, the shortbread recipe for butter, the packing list
        # for a train - and the table never got its own question. A person weighing two things
        # up is asking which, whatever punctuation they use. A line that says what they think
        # ("i think tea is better than coffee") is still their own opinion, not a request.
        words = set(understood.get("words") or ())
        text = str(understood.get("text") or "").lower()
        # The pair has to be put as a choice, not merely named together: "i take the bus and the
        # train to work" is the commute, and a list of both halves is not a question about which.
        if not re.search(CHOICE_IN_WORDS, text):
            return None
        # And a choice the person states as a fact about themselves is a report, not a question:
        # "i like tea or coffee in the morning" is answered by saying it back, which is what it
        # got before. The ask words are what turn the same halves into a question.
        if set(words) & FIRST_PERSON and not set(words) & CHOICE_ASK_WORDS:
            return None
        if OWN_OPINION.search(text) and not words & {"you", "your", "yourself", "yours"}:
            return None
        return reply(memory, understood) if callable(reply) else reply
    # The choice words also gate the match itself: a line with none of them ("so why is there
    # snow on mountains in summer") must not select this entry at all, or the entry would hold
    # the line and decline it, and the science answer it deserves would never be reached.
    return entry(id, (a, b), answer, avoid=avoid, bias=bias + 1,
                 ask=tuple(sorted(CHOICE)) + CHOICE_ASKS)


def _already_on_instruments(memory):
    """True when the bot's last turn was already about learning an instrument."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    said = str(last.get("bot") or "").lower()
    return ("15–20 minutes" in said or "learning an instrument" in said
            or "four chords" in said)


# The words that show the doubt the reassurance answers. "I want to learn the guitar" has no
# doubt in it, so leading with "Not too late at all" answers a question nobody asked.
TOO_LATE = ("too late", "too old", "am i too old", "at my age", "my age", "old age", "start at",
            "adult", "as an adult", "grown up", "40", "45", "50", "60", "70")

# Drums have no chords, so the guitar-shaped take would be a nonsense answer to "i always wanted
# to learn the drums at 45". A kit is also the last thing to buy, not the first.
DRUMS = ("drum", "drums", "drum kit", "drumkit", "drumming", "percussion", "practice pad")

# A line that names one of these is about that instrument, whatever the last answer was: after a
# drums reply, "i want to learn the guitar" is still a guitar question.
OTHER_INSTRUMENTS = ("guitar", "piano", "ukulele", "violin", "keyboard", "bass", "flute",
                     "sax", "saxophone", "cello", "banjo", "mandolin", "harmonica",
                     "trumpet", "clarinet", "choir", "singing", "practise singing")


def _on_drums(memory, understood):
    """True when this line, or a line or two back, is about drums rather than a guitar."""
    if _names(understood, DRUMS):
        return True
    if _names(understood, OTHER_INSTRUMENTS):
        return False
    turns = memory.get("turns") if isinstance(memory, dict) else None
    # Drums are the one instrument whose first week is nothing like the others, and the person
    # says it once: "im learning the drums", then "how long until i can play a song", then "what
    # should i practise first". The last answer names no drum, so the drum has to be read back
    # over a few turns, the way the instrument tables are.
    for turn in reversed(turns[-INSTRUMENT_LOOKBACK:] if isinstance(turns, list) else []):
        if not isinstance(turn, dict):
            continue
        if "practice pad" in str(turn.get("bot") or "").lower():
            return True
        said = str(turn.get("bot") or "").lower()
        if "basic beat" in said:
            return True
        if _names({"text": str(turn.get("user") or "")}, DRUMS):
            return True
        # The newest line wins either way: a guitar taken up after the drums ended the drum
        # answers, so the drum is not read back past it.
        if _names({"text": str(turn.get("user") or "")}, OTHER_INSTRUMENTS):
            return False
    return False


HEALTH_ASK = ("healthier", "healthiest", "better for you", "better for me", "good for you",
              "caffeine", "healthy", "health")


def _tea_or_coffee(memory, understood):
    """Tea or coffee: a taste, unless the line asks which one is better for you."""
    if isinstance(understood, dict) and _names(understood, HEALTH_ASK):
        return ("Neither is bad for you, and the health difference is small: tea has about half "
                "the caffeine of coffee, both count towards your fluids, and green tea and filter "
                "coffee have the most evidence behind them. What matters far more is how much "
                "sugar and milk goes in.")
    return ("Tea, most of the time: it's a better excuse to stop for five minutes. Coffee when "
            "you actually need to be awake in a hurry.")


# The instruments the answer can actually speak about. "Four chords in a month" is a guitar
# sentence: a violin has no chords for a beginner and a flute cannot play one at all, so each
# instrument gets its own first month, and anything not on this list gets an answer that is true
# of all of them rather than one that is true only of a guitar.
INSTRUMENTS = {
    "guitar": {
        "names": ("guitar", "guitars", "ukulele", "uke", "banjo", "mandolin"),
        "hint": "four chords",
        "start": ("Start with four chords that fit a hundred songs — G, C, D and E minor — and the "
                  "strumming hand before the fretting one. Twenty minutes a day gets you a simple "
                  "song in two or three months, and six lessons at the start mean nobody has to "
                  "unlearn your hand position."),
        "practise": ("One song you actually like, in its easiest key: take the chord changes slowly, "
                     "in a loop, then put them in order. Speed comes last — clean and slow beats "
                     "fast and sloppy every time."),
        "how_long": ("With 15–20 minutes a day, four chords and a simple song come together in about "
                     "a month, and something recognisable with a few more chords in three to six "
                     "months."),
        "how_often": ("Fifteen to twenty minutes a day, five or six days a week, beats one long "
                      "session at the weekend: the chord changes are what need repeating, and your "
                      "fingertips need the odd rest day more than the extra minutes. Ten minutes is "
                      "enough on a busy day - the streak matters more than the length."),
    },
    "piano": {
        "names": ("piano", "pianos", "keyboard", "keyboards", "electric piano"),
        "hint": "right hand",
        "start": ("Start with the right hand alone on a song you already know, one note at a time, and the "
                  "left hand on two or three chords to go with it: hands separately for the first "
                  "few weeks is not cheating, it is how everyone does it. Twenty minutes a day, "
                  "and a teacher for the first month so your hand shape is right."),
        "practise": ("Right hand alone, slowly, on a tune you already know by ear — then the same "
                     "bars with the left hand, then both together much slower than either felt. "
                     "Five minutes of that daily beats an hour on Sunday."),
        "how_long": ("With 15–20 minutes a day, a simple tune with the right hand comes together in "
                     "a few weeks, and both hands in three to six months — faster than most people "
                     "expect, because the notes are laid out in front of you."),
        "how_often": ("Twenty minutes a day, five or six days a week, and shorter on a bad day "
                      "rather than skipping it: ten focused minutes of scales and one bar done "
                      "slowly is worth more than an hour on Sunday evening. Keep a day off."),
    },
    "violin": {
        "names": ("violin", "violins", "viola", "fiddle", "cello"),
        "hint": "open strings",
        "start": ("Start with the bow and the open strings: long, slow bow strokes on one string "
                  "are the first month, because a straight bow and a steady sound come before any "
                  "tune. Ten minutes a day, and a teacher from the first week — this is the "
                  "instrument where a bad habit is hardest to undo."),
        "practise": ("Open strings with a long, even bow, then one finger at a time on the D and A "
                     "strings: it sounds dreadful for a few weeks and that is the normal sound of "
                     "learning. A teacher's ear in the room is worth more here than on any other "
                     "instrument."),
        "how_long": ("Expect a few months of short tunes on one or two strings, and about a year "
                     "before something sounds like the tune you set out to play: the bow is the "
                     "slow part, not the fingers."),
        "how_often": ("Ten to fifteen minutes a day, every day if you can, because it is the bow "
                      "arm and the intonation that have to repeat - a week off costs you more on "
                      "the violin than on any other instrument. Stop while it still sounds good "
                      "rather than practising tired."),
    },
    "flute": {
        "names": ("flute", "flutes", "recorder", "piccolo"),
        "hint": "head joint",
        "start": ("Start with the mouth, not the tune: getting a clean sound out of the head joint "
                  "is the first week, then long notes on a few fingerings. Ten minutes a day, and "
                  "a teacher early, because the embouchure is the thing that is hard to fix "
                  "yourself."),
        "practise": ("Long notes on each fingering, from the easiest note upwards, listening for a "
                     "steady sound: five minutes of that a day before any tune. Then a short tune "
                     "in the easy keys, slowly."),
        "how_long": ("A clean sound takes a few weeks, a simple tune two or three months, and "
                     "something you would play for someone else six months to a year."),
        "how_often": ("Ten to fifteen minutes a day is plenty, most days: five of long notes and "
                      "the awkward fingering, then a short tune. Daily is what settles the "
                      "embouchure, and a day off now and then does no harm - a tired mouth is "
                      "where squeaks come from."),
    },
    "reed": {
        # A saxophone has no head joint: the mouthpiece and the reed are the awkward part, and a
        # brass player would say the same about the buzzing lips.
        "names": ("clarinet", "sax", "saxophone", "trumpet", "oboe", "bassoon", "trombone",
                  "cornet", "horn", "french horn", "bugle"),
        "hint": "mouthpiece",
        "start": ("Start with the mouth: a clean, steady note on the mouthpiece alone is the first "
                  "week, and long notes on a few fingerings after that. Ten minutes a day, and a "
                  "teacher early, because the embouchure is the thing that is hard to fix "
                  "yourself."),
        "practise": ("Long notes, from the easiest note upwards, listening for a steady sound and a "
                     "clean start to each one: five minutes of that a day before any tune. Then a "
                     "short tune in the easy keys, slowly."),
        "how_long": ("A clean sound takes a few weeks, a simple tune two or three months, and "
                     "something you would play for someone else six months to a year."),
        "how_often": ("Ten to fifteen minutes a day, most days: long notes and a clean start to "
                      "each one first, then a tune. Daily repetition is what builds the "
                      "embouchure, and the mouth is what gives out first if you push it."),
    },
}

# Everything else: singing, harmonica, harp, drums without sticks. The answer says nothing only
# one instrument can do, because a take that is wrong about the instrument is worse than a short
# one.
INSTRUMENT_GENERIC = {
    "start": ("Start with a teacher or a good app for the first month and ten or fifteen minutes a "
              "day on the basics: every instrument has its own awkward first fortnight, and one "
              "lesson early saves months of undoing. Pick one short piece you like as the target."),
    # No bow and no embouchure here: this is the answer for an instrument nobody wrote a first
    # month for, and a harmonica has neither. What is true of all of them is that the awkward
    # part gets the ten minutes.
    "practise": ("Whatever is awkward on it — the first clean note, the hand position, the "
                 "breathing — ten minutes a day, then a short piece slowly. Speed comes last."),
    "how_long": ("With 15–20 minutes a day, a simple tune is usually a few months and something "
                 "recognisable six months to a year, depending on the instrument."),
    "how_often": ("Short and often: ten to twenty minutes a day, most days of the week, beats one "
                  "long session at the weekend. Whatever is awkward in it gets the first five "
                  "minutes, and stopping while it is still going well is what keeps you coming "
                  "back to it."),
}


def _named_instrument(understood):
    """Which of the instrument answers this line is about, or None for one we do not cover."""
    for key, table in INSTRUMENTS.items():
        if _names(understood, table["names"]):
            return table
    return None


def _instrument_table(memory, understood):
    """The instrument this conversation is about, the named one first, then the last answer's."""
    named = _named_instrument(understood)
    if named is not None:
        return named
    if _names(understood, OTHER_INSTRUMENTS):
        # named, but one we do not have a first month for: never fall back to the last instrument
        return INSTRUMENT_GENERIC
    turns = memory.get("turns") if isinstance(memory, dict) else None
    # The newest turn first: an answer names its own instrument ("the bow and the open strings"),
    # so the follow-up "how long before i can play a song" stays on that instrument and does not
    # fall back to a guitar sentence. The person's own words count too, and for a few turns:
    # "im learning the piano" was answered with something general enough to name no instrument,
    # and then "what should i practise first" offered the piano player the embouchure and the bow.
    for turn in reversed(turns[-INSTRUMENT_LOOKBACK:] if isinstance(turns, list) else []):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "").lower()
        for table in INSTRUMENTS.values():
            if table["hint"] in said:
                return table
        asked = str(turn.get("user") or "")
        if asked:
            for table in INSTRUMENTS.values():
                if _names({"text": asked}, table["names"]):
                    return table
    return INSTRUMENT_GENERIC


# Every word that names an instrument, in the spellings the tables above use.
INSTRUMENT_WORDS = DRUMS + OTHER_INSTRUMENTS + tuple(
    name for table in INSTRUMENTS.values() for name in table["names"])
# How far back a named instrument still counts: a follow-up can come a few lines after the
# instrument ("i want to learn the guitar", "how much are lessons", "what should i practice
# first"), and a guitar named twenty lines ago is a different conversation.
INSTRUMENT_LOOKBACK = 6


def _an_instrument_is_in_play(memory, understood):
    """True when this line, or something said a line or two back, names an instrument.

    "practice" and "practise" are ordinary words, and the practise answer is about an
    instrument — the embouchure, the bow, the hand position. Without this the answer went to
    "what can i cook to practice" and to "what should i practice first" with no subject at
    all, in a conversation about nothing musical. Three ways the instrument can be in play:
    named here ("what should i practise first on the violin"), named in the answer just given
    (the guitar answer says "four chords"), or named in a line just before it ("im learning
    the violin", then "what should i practice first").
    """
    if _names(understood, INSTRUMENT_WORDS):
        return True
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    said = " "
    for turn in turns[-INSTRUMENT_LOOKBACK:]:
        if isinstance(turn, dict):
            said += str(turn.get("user") or "") + " " + str(turn.get("bot") or "") + " "
    said = said.lower()
    return any(word in said for word in INSTRUMENT_WORDS)


def _practise_first(memory, understood):
    """What to practise in the first week, for the instrument this line (or the last one) named."""
    if _on_drums(memory, understood):
        return ("Single strokes first, slow and even, ten minutes a day on a practice pad or a "
                "cushion: full strokes up to about a foot, then back down. Get that steady, then "
                "a basic beat — hi-hat on the eighths, snare on two and four, kick on one and "
                "three — and play along to a song you like. Speed comes last.")
    table = _instrument_table(memory, understood)
    if table is INSTRUMENT_GENERIC and not _an_instrument_is_in_play(memory, understood):
        # Nothing here is about an instrument, so the question is not ours: "what should i
        # practice first" after a cooking line is a cooking question.
        return None
    return table["practise"]


def _drums_start(too_late):
    """The drums version of the adult-beginner take: a beat in weeks, no kit to start."""
    first = ("Not too late at all. " if too_late else "")
    return (first + "Ten minutes a day on a practice pad gets you a steady basic beat in about "
            "six weeks: single strokes slow and even, then hi-hat on the eighths, snare on two "
            "and four, kick on one and three. Play along to songs you like before you buy a kit, "
            "and take one lesson at the start so your grip is right — a pad, or a cushion and a "
            "pair of sticks, is enough to begin.")


def _start_instrument(memory, understood):
    """An adult who always wanted to learn: the first month, and the reassurance when it is asked."""
    if _on_drums(memory, understood):
        if _already_on_instruments(memory):
            return ("Then start this week: pad and sticks, ten minutes a day, one lesson at the "
                    "start, and one song you like to play along to. Speed comes last — slow and "
                    "even beats fast and ragged every time.")
        return _drums_start(_names(understood, TOO_LATE))
    table = _instrument_table(memory, understood)
    start = table["start"]
    if _already_on_instruments(memory) or not _names(understood, TOO_LATE):
        return start[0].upper() + start[1:]
    # The doubt is asked, so answer the doubt first, then the same first month.
    return ("Not too late at all: adults pick up the theory faster than children, they just need "
            "shorter and more regular practice. " + start[0].upper() + start[1:])


def _how_long_song(memory, understood):
    """The follow-up after the instrument: how long until something recognisable."""
    if _on_drums(memory, understood):
        return ("About six weeks of ten minutes a day for a steady basic beat, and three or four "
                "months before it holds together with a song at full speed. Play along to songs you "
                "like before you buy a kit.")
    return _instrument_table(memory, understood)["how_long"]


def _how_often_at_it(memory, understood):
    """How often to practise, for the instrument this line (or the last one) named.

    A frequency question is not the practice-first question and not the how-long-until-a-song
    question: it wants a rate, and the answer that carries the rate is the one thing the
    instrument tables did not hold. "how often should i practise the piano" was the shrug and
    "how often should i practise guitar" was the buy-a-guitar row, because "guitar" plus an ask
    word was all that row needed.
    """
    if _on_drums(memory, understood):
        return ("Ten minutes a day, five or six days a week, on a practice pad: single strokes "
                "slow and even first, then the basic beat played along to a song. The hands want "
                "the day off more than they want the extra twenty minutes.")
    table = _instrument_table(memory, understood)
    if table is INSTRUMENT_GENERIC and not _an_instrument_is_in_play(memory, understood):
        # Practising with nothing musical in play is still practising, and the rate is the same
        # for a language, a serve or a drawing hand, so the answer that fits any instrument
        # answers the line that names none.
        return INSTRUMENT_GENERIC["how_often"]
    return table["how_often"]


# "What do you think is the best season" wants the taste and nothing else; "i cant decide mine"
# wants the taste and the way through the decision, so the walk back belongs only in the second.
CANT_DECIDE = ("cant decide", "can't decide", "cannot decide", "undecided", "help me decide",
               "which should i", "what would you pick", "dont know which", "don't know which",
               "no idea which")


def _best_season(memory, understood):
    """A taste on the seasons, plus the way through it when the line says it cannot decide."""
    taste = ("Late spring for me: long evenings, everything green, and not hot enough to make "
             "excuses.")
    if _names(understood, CANT_DECIDE):
        return (taste + " Since you cannot settle on one, pick by what you would do in it: "
                        "autumn for walking, summer for eating outside, winter for staying in.")
    return taste


# Someone who is out all day has already given the reason that decides it, and answering "dogs"
# against their own constraint is worse than saying nothing, so the pick flips to the cat.
OUT_ALL_DAY = ("out all day", "out at work", "at work all day", "work all day", "out for work",
               "away all day", "long hours", "night shifts", "night shift", "travel for work",
               "always out", "rarely home", "small flat", "no garden", "in a flat", "renting",
               "landlord", "allergic", "allergy", "allergies")


# "Is a cat easier than a dog" is a comparison of one thing, not a choice between two pets, and
# answering "dogs" to it names the wrong animal. The dimension in the line decides which side is
# right, whichever way round the two are named: a cat wins on work, noise, mess and money, a dog
# wins on affection, company and play.
# The money comparison has a row of its own that gives the actual yearly figures, so cost words
# are not here: this reply would only repeat it with less in it.
CAT_WINS = ("easier", "easy", "less work", "less effort", "less hassle", "independent",
            "quiet", "quieter", "silent", "noise", "noisy", "noisier", "loud", "louder",
            "clean", "cleaner", "tidy", "smaller", "smell", "smells", "smelly",
            "low maintenance", "self sufficient")
DOG_WINS = ("affectionate", "loving", "loyal", "friendly", "playful", "fun", "company",
            "companionship", "clingy", "cuddly", "cuddles", "trainable", "obedient",
            "protective", "energetic", "good with kids", "good with children", "interactive")
# Training is the one dimension where the answer is not the quieter animal: a dog is the one that
# can be taught, so "is a cat easier than a dog to train" must not be answered with the cat.
TRAIN_WORDS = ("train", "trains", "trained", "training", "obedience", "obedient", "commands",
               "tricks")
TRAIN_COMPARE = (
    "A dog, on that one: dogs work for food and praise and will sit, stay and come in a few "
    "weeks, where a cat learns a few tricks on its own terms and will not be told. If training "
    "the animal is part of the fun for you, get the dog.")

CAT_ON_A_DIMENSION = (
    "A cat, on that one: it sleeps most of the day, does not bark at the postman and costs about "
    "£700 to £1,000 a year once insurance and a vet fund are in, where a dog is £1,500 and up "
    "before any vet bill. Pick the cat only because you want a cat, though, not just because it "
    "is the cheaper one.")
DOG_ON_A_DIMENSION = (
    "Dogs, by a whisker: daft, straightforward and pleased to see you, and they show it plainly - "
    "a dog greets you at the door where a cat may not. The trade is the walk every morning and "
    "£1,500 a year before any vet bill, and an adult rescue is far easier than a puppy.")


def _cats_or_dogs(memory, understood):
    if _names(understood, OUT_ALL_DAY):
        return ("A cat, if you're out all day: it sleeps through your shift and does not need a "
                "walk at seven in the morning. Get an adult cat rather than a kitten, and two if "
                "you are away a lot, so they have company.")
    if _names(understood, TRAIN_WORDS):
        return TRAIN_COMPARE
    if _names(understood, CAT_WINS):
        return CAT_ON_A_DIMENSION
    if _names(understood, DOG_WINS):
        return DOG_ON_A_DIMENSION
    return ("Dogs, by a whisker: daft, straightforward and pleased to see you. A cat is the kinder "
            "choice if you're out all day, though.")

# --- someone stuck on a choice ---------------------------------------------------------------
# "should we get a dog", "cant decide between two flats", "im torn between two jobs" and "i keep
# going back and forth on whether to move" all read the same way: the line names a choice and no
# entry owns it, so the bot answered with a nod, an echo of the line, or a search hedge. The
# shapes below are the ways people say they are stuck; each entry answers one subject with the
# trade that settles it. A subject is only read off a line that is already a decision, so a line
# that merely mentions a dog or a car is left to the rows that know about dogs and cars.
DOG_TRADE = (
    "Want one only if the person who wants it is also the one who will walk it at seven on a wet "
    "Tuesday for the next twelve years. A dog costs £1,500 to £2,000 a year before any vet bill "
    "and needs someone home at lunchtime or a walker; an adult rescue is far easier than a "
    "puppy. If that sounds fine rather than like a sacrifice, get one.")
# A rabbit is not a small dog, and the dog's trade answered for one: "should i get a rabbit",
# "is it worth getting a hamster" and "should i get a pet" were all told about the walk at seven
# and £1,500 a year. What decides a small animal is how long it lives and who does the cleaning,
# which is a different trade and the one people are actually weighing up.
RABBIT_TRADE = (
    "A rabbit is an eight to ten year commitment and not a hutch pet: it needs a run it can stand "
    "up and stretch in, hay every day, another rabbit for company, and a vet who treats rabbits, "
    "because they hide illness until they are very ill. The daily work is the cleaning out and "
    "the company, and a rabbit kept alone in a small hutch is a miserable animal. A child can "
    "enjoy a rabbit but cannot be the one who cleans it out or notices it has stopped eating, so "
    "that job is an adult's. Get one because you want a rabbit for that long.")
GUINEA_PIG_TRADE = (
    "A guinea pig lives five to seven years and should never be kept alone - two of them, with a "
    "hutch and a run, hay all day because their teeth grow constantly, and vegetables with "
    "vitamin C in them because they cannot make their own. They are the friendliest of the small "
    "pets if they are handled from the start, and the daily work is hay, water and cleaning out.")
HAMSTER_TRADE = (
    "A hamster lives two to three years, sleeps through your day and is awake in the evening, so "
    "it is a pet to watch and handle gently rather than carry about. It wants the biggest cage "
    "you can give it with deep bedding to dig in, a wheel that does not bend its back, and a "
    "clean-out every week or so. Cheap to buy, not cheap to set up, and not a pet for a child on "
    "their own.")
# A cat is not a cheap dog. "we are thinking of getting a rescue cat" reached the dog trade,
# because the word `rescue` is one of the dog's, and the person weighing up a cat was told about
# the walk at seven and £1,500 a year. A cat is a different trade: cheaper, no lunchtime visit,
# and the two things that decide it are the landlord and the holidays.
CAT_TRADE = (
    "A cat costs about £700 to £1,000 a year once insurance and a vet fund are in, and unlike a "
    "dog it does not need you home at lunchtime: an adult cat sleeps through a working day, which "
    "is why people who cannot have a dog often do well with a cat. Get an adult rather than a "
    "kitten if you are out, two if the house is empty all day, a litter tray each plus one, and "
    "settle the landlord and who looks after it when you go away before you fall for one.")
# A thing for the cat is not the decision to have one, and the row that knows the thing answers
# it: "should i get a cat flap" and "what food for a cat" are not trades between two lives.
CAT_WORDS = ("cat", "cats", "kitten", "kittens")
CAT_EQUIPMENT = ("flap", "litter", "tray", "trays", "scratching", "tree", "carrier",
                 "food", "foods", "treat", "treats", "toy", "toys", "brush", "claws",
                 "collar", "microchip", "harness", "bed", "bowl", "bowls", "catnip")
MOVE_TRADE = (
    "A move is decided by what you cannot change later: the commute, the noise, the light, and "
    "what you can walk to. Write the one thing each place gives you that the other cannot, then "
    "take the one you would miss on a bad day rather than the one that looks better on a good "
    "one. Move when the reason is still there in February.")
CAR_TRADE = (
    "A car is decided by the trips you actually make, not the ones you imagine: mostly short "
    "local miles with charging at home, electric; a long motorway run every month, petrol or a "
    "hybrid. Put insurance, tax and a service into the first-year budget, then only look at cars "
    "under that. The reliable boring one beats the fun one you cannot afford to fix.")
COURSE_TRADE = (
    "Pick the course by where you want to be at the end of it: a job, a licence, or the habit of "
    "studying. Ask two people who finished it what they do now, and count the hours a week it "
    "really takes. If the point is interest rather than a qualification, a short evening course "
    "tells you whether you like it before you pay for three years.")
# The words that turn a choice into a question about one of the things in it. A line carrying
# one of these wants the detail (a lead, a model, a breed, a price), not a trade between two
# lives, and another row has that detail.
QUALIFIED = ("which", "what model", "what kind", "what sort", "what breed", "what size",
             "how much", "how big", "how old", "how long", "used", "second hand", "secondhand",
             "lead", "leads", "harness", "breed", "breeds", "price", "prices", "cost", "cheap",
             "cheapest", "best", "insurance", "tax", "mot", "vet", "food", "train", "training",
             "name", "names", "age", "size",
             # a survey is a thing with a price and a level, not a life to weigh up: "what
             # survey should i get on an old house" was told how to choose between two places
             "survey", "surveys", "surveyor", "surveyors", "valuation", "snagging",
             # two ways of doing one thing, and the row that owns that thing has the sums or the
             # checklist: "torn between buying a flat and renting" is buy-versus-rent, not a
             # choice between two lives, and "should i buy a car from a dealer" is the how.
             "dealer", "dealership", "auction", "private seller")

# Two ways of doing one thing: buying and renting a place, leasing and buying a car. The row that
# owns that thing has the sums, and a trade between two lives is the wrong shape for it. Read as a
# pair rather than as phrases, because a noun sits between them: "buying a flat and renting".
TWO_WAYS = (("buy", "buying", "bought", "purchase", "purchasing", "mortgage", "owner"),
            ("rent", "renting", "rented", "rents", "tenant", "lease", "leasing"))

# The subject to trade table, read in order so a line naming two subjects gets the first one.
DECISION_SUBJECTS = (
    # A dog word is a dog: "rabbit", "hamster" and a bare "pet" were in this tuple, so every small
    # animal decision was answered with the dog's walk at seven and its £1,500 a year. They have
    # their own trade below, and a line naming no animal at all - "should i get a pet" - falls
    # through to the general frame, which asks rather than guesses.
    (("dog", "dogs", "puppy", "puppies", "rescue dog"), DOG_TRADE),
    (("rabbit", "rabbits", "bunny"), RABBIT_TRADE),
    (("guinea pig", "guinea pigs", "guinea-pig", "cavy"), GUINEA_PIG_TRADE),
    (("hamster", "hamsters", "gerbil", "gerbils", "degus", "chinchilla", "chinchillas"),
     HAMSTER_TRADE),
    (("flat", "flats", "house", "houses", "moving house", "move house", "moving in together",
      "rent", "renting", "landlord", "area", "neighbourhood", "commute"), MOVE_TRADE),
    (("car", "cars", "van", "second car"), CAR_TRADE),
    (("course", "courses", "degree", "degrees", "masters", "college", "university", "uni",
      "apprenticeship", "night class"), COURSE_TRADE),
)

# The ways people say they are stuck. Every one is a phrase rather than a single word: "not
# sure" on its own comes up in half the conversations ("not sure what to cook"), and an entry
# that reads a bare "sure" as a decision takes those lines from the rows that answer them.
STUCK_SHAPES = ("cant decide", "can't decide", "cannot decide", "cant choose", "can't choose",
                "torn between", "not sure which", "not sure whether", "not sure if", "unsure which",
                "unsure whether", "going back and forth", "back and forth", "two minds",
                "on the fence", "help me decide", "decide between", "deciding between",
                "should we get", "should i get", "should we buy", "should i buy",
                "thinking of getting", "thinking about getting", "thinking of moving",
                "thinking about moving", "thinking of buying", "whether to",
                "thinking of doing", "thinking about doing", "thinking of studying",
                "thinking about studying", "thinking of going back",
                "worth getting", "worth having")

# The words a stuck line carries that no subject table needs: they are what makes "cant decide
# between two dresses" reach the general frame, where the sentence itself is the only subject.
DECIDE_WORDS = ("between", "whether", "torn", "unsure", "decide", "deciding", "decision",
                "choose", "choice", "option", "options", "stuck")

# A choice that has already been made is not a choice to weigh up: "we decided to get a dog and
# she is lovely" is a person telling the bot their news.
MADE_UP = re.compile(r"\b(?:i|we|they|she|he)\s+(?:have\s+|had\s+)?(?:decided|chose|picked|"
                     r"went with|bought|got|ordered|took)\b")


def _says_one_of(text, options):
    """True when the line holds one of these as a whole word.

    `_names` matches a substring, which is right for a phrase like "out all day" and wrong for a
    table of short words: "apprenticeship" holds "rent", so a line about an apprenticeship read
    as a line about paying a landlord and got the move trade.
    """
    return any(re.search(r"\b" + re.escape(option) + r"\b", text) for option in options)


# "is it worth getting a new one instead" after a boiler service is the boiler, not a fresh
# thing to weigh up: a new one of the thing in hand is a question about the thing.
A_NEW_ONE = re.compile(
    r"\b(?:new|another|bigger|smaller|different|better|second|cheaper)\s+one\b"
    r"|\bone\s+instead\b|\bone\s+of\s+(?:those|them)\b", re.IGNORECASE)

# A line that asks what to buy is a shopping question, and the row that knows the list answers it.
# "what should i get for a new kitten" and "im thinking of getting a cat what do i need" name the
# getting and a cat, but what they want is on the list, and a trade between two lives is not an
# answer to it. Read as their own ask, so "should i get a cat" - which asks whether at all - is
# untouched.
_WHAT_TO_BUY = re.compile(
    r"\bwhat (?:do|should|shall|will|would) (?:i|we) (?:need|buy|get)\b"
    r"|\bwhat (?:do|should|shall) (?:i|we) (?:need|buy|get) (?:to|for)\b"
    r"|\b(?:need|needs) to (?:buy|get)\b|\bshopping list\b|\bchecklist\b"
    r"|\bwhat to (?:buy|get)\b|\bwhich (?:kit|supplies)\b", re.IGNORECASE)

# How many of them is a question of its own. "should i get two cats" wants the answer about two -
# company for the hours you are out, a tray each plus one - and "should i get a second cat" is the
# introduction question; neither is the trade about whether to have one at all.
_TWO_OF_THEM = re.compile(
    r"\btwo (?:cats|kittens)\b|\bsecond (?:cat|kitten)\b|\bpair of (?:cats|kittens)\b",
    re.IGNORECASE)


# The same choice asked as a verdict on the thing. "is a cat a good idea", "is a cat worth it"
# and "would a cat suit me" carry no "should" and no "thinking of", so the row that settles a
# choice never read them: the cat trade was reachable only through "is it worth getting a cat"
# and every other verdict wording got the let-me-search hedge. These are the shapes a verdict
# takes, not the subject, and the row below still needs the cat's own words.
CAT_VERDICT_SHAPES = ("good idea", "worth it", "sensible", "wise", "a mistake",
                      "right for me", "right for us", "suit me", "suit us")

# A verdict word in front of a cat does not always want the trade. Where the cat will live, the
# baby or child in the house, the rescue and the cost are each a row of their own and each
# answers its line better than a general trade: "is a cat a good idea with a baby" is the
# child-safety card, and it was one before this row existed.
_ANOTHER_CATS_QUESTION = re.compile(
    r"\b(?:baby|babies|toddler|toddlers|child|children|kid|kids|newborn|pram|"
    r"flats?|rent|rents|rented|renting|landlord|rescue|rescued|"
    r"garden|outdoor|indoors?|dog|dogs|puppy|puppies|"
    r"cost|costs|price|prices|afford|how much)\b", re.IGNORECASE)


def _not_another_cats_question(understood):
    """True when the line does not name another row's cat question."""
    if not isinstance(understood, dict):
        return False
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    return not _ANOTHER_CATS_QUESTION.search(str(said))


def _deciding(memory, understood):
    """The trade that settles the choice the line names, or the general frame if it names none."""
    if not isinstance(understood, dict):
        return None
    text = " ".join(understood.get("words") or ()) or str(understood.get("text") or "")
    text = " " + " ".join(str(text).lower().split()) + " "
    if A_NEW_ONE.search(text):
        return None
    if _WHAT_TO_BUY.search(text) and _says_one_of(text, CAT_WORDS):
        # the cat's list answers "what should i get for a new kitten"; the same shape about a
        # puppy or a greyhound is that animal's own list and this row was never its answer
        return None
    if _TWO_OF_THEM.search(text) and not re.search(r"\bbetween\b", text):
        # "im thinking of getting two cats" keeps the two-cats answer; "cant decide between two
        # cats at the rescue" is still a decision, and the trade is what there is for it
        return None
    if MADE_UP.search(text) and not re.search(r"\b(cant|can't|cannot|whether|which|torn|unsure)\b",
                                              text):
        return None
    # "should i get a cat or a dog" is a pair pick, and the pick between two animals is already
    # this domain's answer: the trade above is a decision about having one, not about which.
    if _says_one_of(text, ("cat", "cats", "kitten", "kittens")) and _says_one_of(
            text, ("dog", "dogs", "puppy", "puppies")):
        return _cats_or_dogs(memory, understood)
    if _says_one_of(text, TWO_WAYS[0]) and _says_one_of(text, TWO_WAYS[1]):
        return None
    # A cat on its own is the cat trade, and it is read before the table below because the dog's
    # words include `rescue`: "thinking of getting a rescue cat" is about a cat.
    if _says_one_of(text, CAT_WORDS):
        if _says_one_of(text, CAT_EQUIPMENT):
            return None
        return CAT_TRADE
    if _says_one_of(text, QUALIFIED):
        # "which dog lead should i buy", "what model of car", "a used car": the line asks for a
        # specific thing inside the choice, and the row that knows that thing answers it better
        # than a trade between two lives does.
        return None
    for options, trade in DECISION_SUBJECTS:
        if _says_one_of(text, options):
            return trade
    return None

# "is it normal to..." and "is it weird that..." is one everyday question asked about a hundred
# different subjects, and each subject has its own answer, so the table is keyed by the subject and
# the asking is free wording. A line that asks whether something is usual got a price comparison, a
# list of films to cry to and the depression card, because "is it normal" carries no subject of its
# own.
_NORMAL_ASK = ("is it normal", "is that normal", "is this normal", "isnt normal", "isn't normal",
               "not normal", "normal to", "normal for", "is it weird", "is that weird",
               "is this weird", "weird to", "weird that", "weird if", "am i weird",
               "am i strange", "is it strange", "is that strange", "is it odd", "is that odd",
               "odd that", "odd to", "is it unusual", "is that unusual", "is it ok that",
               "is it okay that", "is there something wrong with me")

# The subject and the sentence for it. Short and concrete, and the verdict is the first thing
# said, because the whole question is "am I the only one".
_NORMAL_SUBJECTS = (
    (("live at home", "living at home", "live with my parents", "living with my parents",
      "live with your parents", "living with your parents", "moved back home",
      "moved back in", "still at home", "still live with my mum", "still live with my dad",
      "live with my mum", "live with my dad", "back with my parents"),
     "Living at home as an adult is common: about a quarter of 25 to 34 year olds in the UK still "
     "do, and more do wherever rents are high. What makes it work is agreed terms - what you pay, "
     "what you do round the house, and a date to look at it again - not how long it has been."),
    (("talk to myself", "talking to myself", "talk to yourself", "talking to yourself",
      "talk out loud", "talking out loud", "answer myself", "argue with myself"),
     "Nearly everyone does - surveys put it around 9 in 10 adults - and talking out loud on "
     "purpose is how people hold a task in mind, which is why athletes and surgeons do it. It is "
     "only worth a thought if the voice is not yours or it tells you what to do."),
    (("sleep with a teddy", "sleep with my teddy", "still have a teddy", "sleep with a soft toy",
      "teddy", "teddies", "comfort blanket", "blankie", "cuddly toy", "stuffed toy"),
     "About a third of adults in surveys still have a childhood soft toy, and plenty of them "
     "sleep with it: it is a sleep cue, and a sleep cue that works is worth keeping. It only "
     "matters if it is the only way you can settle at all."),
    # "is it weird that i dont want children" reads to the understanding engine as a wish about
    # the person, and answers.py stands aside for a wish, so that exact wording keeps the decision
    # card; the phrasings below are the ones this table can take, and the subject is the same.
    (("not want children", "not want kids", "not wanting children", "not wanting kids",
      "not wanting a baby", "not want a baby", "childfree", "child free", "not having children",
      "not having kids", "no children by choice", "never want kids", "childless by choice"),
     "About one in five women in the UK reaches 45 without children, and choosing that is "
     "common enough that nobody owes anyone a reason. The thing worth doing is saying it out "
     "loud to a partner early, because the assumptions people make are where the trouble is."),
    (("cry at films", "cry at a film", "cry at movies", "cry at a movie", "crying at films",
      "cry at the cinema", "cry at adverts", "cry at tv", "cry at everything"),
     "That is being moved, and it is what a story is built to do: films pace the music, the "
     "close-ups and the pauses to make you feel for someone. Crying easily at a screen goes with "
     "empathy rather than fragility, and most people find it settles as the mood does."),
    (("broke up", "break up", "breakup", "break-up", "split up", "got dumped", "being dumped",
      "divorce", "divorced", "separation", "she left me", "he left me"),
     "Sad after a break-up is grief, not an illness: it comes in waves with good hours in "
     "between, and it eases over weeks rather than days. The line where it is worth a GP is low "
     "mood most of the day, most days, for two weeks, with nothing giving you pleasure any more."),
    (("dont drink", "don't drink", "not drinking", "i dont drink alcohol", "teetotal", "sober",
      "not a drinker", "stopped drinking", "gave up alcohol", "gave up drinking"),
     "About one in five adults in the UK does not drink at all, and the under-30s drink less "
     "than their parents did, so you are much less of an odd one out than a round of drinks "
     "makes it feel. 'Not for me, thanks' is a whole answer, and asking them something after it "
     "ends the conversation about your glass."),
    (("still single", "single at 30", "single at 40", "never had a girlfriend",
      "never had a boyfriend", "never have had a girlfriend", "never have had a boyfriend",
      "never had a partner", "never have had a partner", "never been in a relationship",
      "never dated", "not had a relationship", "never had a relationship",
      "no relationship at 30"),
     "Plenty of people get to 30 without a relationship, and the number is rising: the timing "
     "of a first relationship stretches over a decade, and none of it is a verdict on you. What "
     "makes the difference is meeting people in a place you would go anyway, rather than "
     "waiting to be picked."),
)

_NORMAL_WORDS = tuple(word for words, _ in _NORMAL_SUBJECTS for word in words)


def _the_normal_answer(memory, understood):
    """The sentence for the thing the line asked about, and nothing when it names no subject."""
    text = " " + str((understood or {}).get("text") or (understood or {}).get("clean")
                     or "").lower() + " "
    for words, reply in _NORMAL_SUBJECTS:
        if any(word in text for word in words):
            return reply
    return None


def _a_table_bills_line(understood):
    """True when the split in the line is a bill at a table, or asks whether it is rude.

    A dinner's bill and a household's bills are the same words: "split bills" is one and
    "how do we split the bills" is the other, and the plural is what people type for both. The
    row this guards is the manners answer - even split, ask for separate bills - and it holds a
    table's bill however the person asks it, including the how-to wording with no judgement word
    in it ("should i split the bill", "how do i split the bill").

    What it must not hold is every other thing that gets split. Its key is a split phrase and a
    how or should, so once the phrase list grew to "split bills" and "split the cost" it
    answered "how do i split bills with my partner", "how should we split the cost of a villa"
    and "how do i split the cost of a present" with the even-split rule for a dinner, over the
    couple's answer and the chip-in answer those lines have. A home word, or a person the money
    is shared with, keeps those rows' own answers.
    """
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _A_SHARED_HOME.search(text):
        return False
    return bool(_A_MANNERS_WORD.search(text) or _A_TABLE_BILL.search(text))


_A_MANNERS_WORD = re.compile(
    r"\b(?:rude|ruder|politest|polite|impolite|cheeky|stingy|stingey|tight|mean|weird|strange"
    r"|normal|ok|okay|fine|wrong|right|fair|acceptable|unacceptable|awkward|etiquette|manners"
    r"|bad\s+form|selfish|generous|expected|allowed|supposed|unfair|annoying|greedy"
    r"|cheapskate)\b")
# The bill itself and the table it is on: a dinner out rather than a household's standing bills.
_A_TABLE_BILL = re.compile(
    r"\b(?:bill|tab|check|cheque|dinner|lunch|brunch|meal|restaurant|drinks|round"
    r"|takeaway|takeout|coffee|starter|dessert|menu)\b")
# A home's bills, and the person the money is shared with: those are the household rows' lines.
_A_SHARED_HOME = re.compile(
    r"\b(?:rent|flats?|houses?|housemates?|flatmates?|roommates?|household|landlord|tenancy"
    r"|mortgage|council\s+tax|utilit(?:y|ies)|electricity|energy|heating|broadband|wifi"
    r"|internet|partner|husband|wife|spouse|boyfriend|girlfriend|couple|income|earns?|salary"
    r"|pays?\s+(?:half|halves)|joint\s+account|bills?\s+between\s+us)\b")


ENTRIES = [
    # --- the bot's taste on everyday things ------------------------------------
    entry("best-season", ("season", ("best", "favourite", "favorite", "think", "pick", "prefer",
                                     "like", "love", "better", "decide", "undecided")),
          _asked(_best_season),
          avoid=("visit", "travel", "holiday", "trip", "plant", "sow", "grow")),
    _either("air-fryer-or-oven", ("air fryer", "air fryers"), ("oven",),
            _asked("Oven for a big tray and anything wet; air fryer for a small, crisp batch "
                   "with less heat in the kitchen. If you already cook for one or two, the air "
                   "fryer earns its space.")),
    entry("pizza-topping", ("pizza", ("topping", "best", "favourite", "favorite", "think", "pick")),
          _asked("Pepperoni, hot out of the oven, is the one I'd pick. Mushroom and ham is the "
                 "better pizza when you want the whole thing rather than a slice.")),
    entry("pineapple-pizza", ("pineapple", "pizza"),
          _asked("For it, honestly. Sweet with salty ham and hot cheese works; people mostly "
                 "enjoy being angry about it.")),
    entry("rainy-sunday", (("rainy", "raining", "wet weekend"), ("sunday", "day", "weekend",
                                                                "afternoon", "think", "like")),
          _asked("I like them: a rainy Sunday is a good excuse to do something that needs a "
                 "whole afternoon — a long film, a proper cook, or a book with the phone in "
                 "another room."),
          # "what's a good film for a rainy Sunday" is a what-to-watch ask, not a taste question
          avoid=("kid", "kids", "child", "children", "toddler", "baby", "teen", "family",
                 "film", "films", "movie", "movies", "watch", "watching", "something to watch",
                 "book", "books", "read", "reading", "recipe", "cook", "make",
                 # "how do i save for a rainy day" is the saving question, not the sky: the
                 # money words keep this taste entry off it.
                 "save", "saving", "savings", "money", "fund", "afford", "pay", "pounds",
                 # and "any ideas for a rainy day" is a day to fill, which is the wet-day
                 # card's question: this one is the bot's taste about rainy Sundays, and a
                 # person asking for ideas got an opinion instead of a plan.
                 "ideas", "idea", "things to do", "something to do", "what can i do",
                 "what can we do", "what should i do", "what to do", "bored",
                 # a step target is a health answer whatever the sky is doing
                 "step", "steps",
                 # "what music for a rainy day" asks for something to listen to, and the music
                 # row is where that answer is: this one is about the shape of the day.
                 # "song" and "songs" stay out of this list: "songs for a rainy day" names no
                 # ask word for the music row to match, and standing this one down would leave
                 # a shrug where there is an answer.
                 "music", "album", "albums", "playlist", "playlists",
                 "podcast", "podcasts", "listen", "listening", "spotify", "tunes")),
    entry("cereal-soup", ("cereal", ("soup", "salad", "think")),
          _asked("Not a soup. Soup is cooked and served hot; cereal is assembled cold at the "
                 "last second, which makes it closer to a salad with milk.")),
    entry("air-fryer", (("air fryer", "air fryers"), TASTE),
          _asked("Worth it for one or two people who like crisp things: chips, roast vegetables "
                 "and chicken thighs in half the time. Skip it if you cook for four or already "
                 "have a good fan oven."),
          # The kitchen's plan entries now name this machine, and "is an air fryer any good" is a
          # buying question, not a plan: the take steps ahead of them (main answers it with the
          # 190C chicken-thigh timetable). It ties with that plan on score, so the nudge is
          # what breaks the tie.
          bias=2,
          # A cleaning question is not a buying question: "how do i get the grease off my air
          # fryer" is the basket answer's, and the nudge above would otherwise take it.
          avoid=NOT_A_BUYING_ASK + DISPOSAL + FAULT + TRADES + ("clean", "cleaning", "cleaner",
                                                     "wash",
                                                     "washing", "grease", "greasy", "crumbs",
                                                     "scrub", "dirty", "stain", "stains")),
    entry("opinion-on-my-gadget",
          # Someone who has just bought one is not asking whether to buy it: they want a view on
          # the thing itself. Keeping this off the buying answers means "my new blender" is a
          # taste while "my new washing machine" still gets the drum-size advice.
          (("blender", "food processor", "slow cooker", "bread maker", "smoothie maker",
            "juicer", "coffee machine", "stand mixer", "pressure cooker", "sandwich toaster",
            "ice cream maker", "air fryer"),
           # The ownership words are the key, not the opinion words: "what do you think about
           # air fryers" is the should-I-buy-it take, and "is a slow cooker worth it" is too.
           # "i've got" was the only ownership form here, so the way most people type it -
           # "i have got a blender", "ive got a blender", "i have a blender" - never reached the
           # tip and got "Noted: you have a blender" instead
           ("my new", "my old", "my own", "do you like my", "think of my", "reckon of my",
            "i bought", "i've bought", "i just bought", "i got", "i've got", "we bought",
            "we got", "our new", "i have got", "ive got", "i have", "we have", "we have got",
            "i was given", "got given", "someone gave me", "i have been given", "was given a",
            "i have just bought", "have just got", "just got a", "i use my", "i use the")),
          _asked(_gadget_view),
          avoid=FAULT + TRADES + ("broken", "wont", "won't", "stinks", "smells", "leaking")),
    entry("worth-an-appliance",
          # The same question for any appliance, so a dishwasher or a tumble dryer gets a rule of
          # thumb rather than the honest shrug.
          (("dishwasher", "tumble dryer", "dryer", "washing machine", "slow cooker", "bread maker",
            "blender", "food processor", "pressure cooker", "vacuum", "hoover", "freezer"),
           TASTE),
          _worth_an_appliance,
          # "is a slow cooker worth it" was answered with the slow cooker's cooking timetable.
          bias=2,
          # A machine another entry already has real buying advice for keeps that answer: a
          # washing machine has a drum size, a spin speed and a running cost to talk about, and
          # "it takes up a cupboard" is a bad answer to the biggest appliance purchase most
          # people make.
          #
          # A frightened line is not a buying question either, and TASTE carries the bare verb
          # "get", so "my cat hides when i get the vacuum out" was a take on whether to buy one.
          # The feeling words are the guard rather than the animal: "is a robot vacuum worth it
          # with a dog in the house" is still this answer.
          avoid=NOT_A_BUYING_ASK + DISPOSAL + FAULT + TRADES + OWN_BUYING_ANSWER + A_JOB_ON_IT
          # A clock line is not a buy-it question: "how long does a freezer take to get cold"
          # is the fridge's own answer, and the buying rule of thumb took it because "freezer"
          # and "take" were the only two words it needed.
          + ("how long does", "how long do", "how long will", "how long to", "how long before",
             "take to get cold", "get cold", "heat up", "heats up", "preheat",
             # "is it worth getting the tumble dryer serviced" asks about the yearly job, not
             # about buying one: the machine-service row in home.py owns the service lines.
             "service", "services", "servicing", "serviced")
          # Where the duct goes is not whether to buy one, and it is a fixed fact: "do heat pump
          # dryers need a vent" and "do i need a vent for my tumble dryer" were both answered
          # with "it takes up a cupboard". Held as phrases, because "vented" alone is a kind of
          # dryer and "is a vented dryer worth it" is this row's question.
          + ("need a vent", "needs a vent", "need venting", "needs venting", "need to vent",
             "needs to vent", "vent for", "vent a tumble", "vent the dryer", "vent my dryer",
             "vent a dryer", "venting a", "outside vent", "wall vent", "vent hose", "hose keeps",
             "where can i put", "can i put my dryer", "can a tumble dryer go",
             "can a dryer go", "can i put a dryer")
          + ("scared", "scary", "afraid", "frightened", "frightens", "terrified", "terrifies",
             "panics", "hates", "hate", "hiding", "hides", "cowers", "trembles", "shakes",
             "shaking", "barks", "barking"),
          # Where to get one is not whether to have one: the freezer was told a rule of thumb
          # about owning one, and a place is what the line asked for.
          guard=lambda understood: not asks_where_a_shop_answers(understood)),
    # "is it worth getting solar panels" and "should i get solar panels" came back as "That's your
    # call, not mine" - the honest shrug, but this is one of the few home buys with a real rule of
    # thumb in it, and the appliance row never held solar because it is not an appliance.
    entry("worth-solar",
          (("solar panel", "solar panels", "solar pv", "solar tiles", "pv panels", "solar"),
           ("worth", "worth it", "should i", "is it worth", "get", "getting", "buy", "buying",
            "any good", "reckon", "pay for itself", "payback", "pay back", "save money",
            # the same question in the ask people actually use for a recommendation: "would you
            # recommend solar panels" was the honest shrug, next to "is solar worth it", which
            # this row answers.
            "recommend", "recommended", "recommendation", "recommendations",
            # the same question as a doubt about the spending: "any point in solar panels",
            # "do i need solar panels", "is solar panels a waste of money" were all the honest
            # shrug while this row held the payback figures.
            "any point in", "point in solar", "waste of money", "do i need", "do i need solar",
            "savings", "roof", "battery", "install", "installing", "installed", "quote",
            "south facing", "shade", "kwh", "export", "feed in tariff")),
          "Worth it if the roof is roughly south facing, unshaded, and somebody is in during the "
          "day: a typical 4kW system costs about £5,000 to £7,000 fitted and pays back in 10 to 14 "
          "years on the avoided bill plus the export payment. A battery rarely pays for itself. "
          "Get two quotes with the yearly kWh in writing, and the MCS certificate.",
          # the explanation of how a panel works is explains.py's, and a panel that has failed is
          # the fault question, not a buying one
          avoid=("how do", "how does", "how is", "what is", "what are", "explain", "work",
                 "works", "working", "broken", "not working", "fault", "faulty", "panel is",
                 "panels are", "clean", "cleaning", "moss", "bird", "installer has", "already")),
    entry("is-that-normal", (_NORMAL_WORDS, _NORMAL_ASK), _the_normal_answer,
          # a symptom is the health rows' question even when the line asks whether it is usual,
          # and a body change is never answered from a table about habits
          avoid=("blood test", "blood tests", "period", "periods", "spotting", "discharge",
                 "lump", "lumps", "pregnant", "pregnancy", "miscarriage", "hiv", "std", "stis",
                 "pain", "pains", "hurts", "bleeding", "temperature", "rash", "itch", "itchy"),
          # the depression card keys "sad" and "feel", so "is it normal to feel sad after a
          # breakup" reached the criteria for an illness when the question is whether grief is
          # normal. low-mood carries bias 3, so this row needs more than that to answer the
          # subject it is keyed on; it never competes on a line outside the table.
          bias=4),
    entry("eat-alone", (("eat alone", "eating alone", "by myself", "by yourself", "on my own",
                         "on your own", "eating on your own", "eat on my own"),
                        ("restaurant", "cafe", "pub")),
          # "Yes, and it gets easier" read as "yes, it is rude", which is the opposite of the
          # reply, so the line says the answer out loud first.
          _asked("Not rude at all, and it gets easier with a book or a seat at the bar. Nobody "
                 "in there is thinking about you half as much as you fear.")),
    # "is it weird to go to the cinema on your own" and its neighbours - a gig, a museum, the
    # theatre, the pub - were every one of them a punt or a search hedge, and "is it ok to go for
    # a meal on my own" was reading out how to cook for one person. What people are asking is not
    # about the venue, so one answer covers all of them: the fear is the ten minutes before you
    # sit down, and the way through it is the same whether it is a film or a bar.
    entry("out-on-your-own",
          # The outing is the evidence and the "on my own" is the question: neither half answers
          # anything without the other, so "how do i set up my own business" and "i live on my
          # own" stay out.
          (("cinema", "film", "films", "movie", "movies", "gig", "gigs", "concert", "theatre",
            "show", "museum", "gallery", "exhibition", "festival", "pub", "restaurant",
            "cafe", "meal", "brunch", "lunch", "dinner", "coffee", "eat", "eating", "class",
            "course", "gym", "swim", "match", "talk", "things", "going out", "go out",
            "night out", "day out", "weekend"),
           ("on my own", "on your own", "alone", "by myself", "by yourself", "solo",
            "single ticket", "no one to go with", "nobody to go with", "without anyone")),
          _asked("Go, and go once without talking yourself out of it: the hard part is the ten "
                 "minutes before you sit down, not the two hours after. Book one seat at the end "
                 "of a row for the cinema or the theatre so you are not climbing over people, "
                 "take a bar stool rather than a table in a pub or a restaurant, and arrive five "
                 "minutes late rather than half an hour early. Take something to do with your "
                 "hands the first time and pick a weekday evening - the second trip is easy."),
          # Travelling and swimming on your own are their own questions with their own answers,
          # and a wedding on your own is a room full of people who know each other, which the
          # seat-at-the-end-of-a-row advice does not touch.
          # "What can I eat for dinner on my own" is a meal to cook, not an outing to brave, so
          # the words that make it a choice of food take it back to the cooking row.
          avoid=("travel", "travelling", "traveling", "trip", "holiday", "holidays", "abroad",
                 "flight", "flights", "hostel", "backpacking", "swim", "swimming", "lengths",
                 "wedding", "lonely", "loneliness", "lonely",
                 "what can i eat", "what should i eat", "what to eat", "what can i have",
                 "meal ideas", "meal plan", "recipes", "recipe", "cooking", "cook",
                 "food shop", "batch",
                 # An animal said with "alone" and "weekend" is the leaving-a-pet question, and
                 # this row was taking it: "is it ok to leave a cat alone all weekend" got "go,
                 # and go once without talking yourself out of it - the hard part is the ten
                 # minutes before you sit down", which is the answer for braving a cinema seat.
                 # pets.py has `cat-alone` and `dog-alone`, and both are the better answer.
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies", "pup",
                 "rabbit", "hamster", "budgie", "parrot", "pet", "pets", "tortoise", "ferret",
                 "guinea pig", "goldfish", "fish", "horse", "pony", "snake", "lizard"),
          bias=2),
    entry("phone-at-dinner", ("phone", ("dinner table", "at dinner", "at the table",
                                        "during dinner", "meal")),
          _asked("Face down and out of reach, at least while you're eating. A phone on the table "
                 "pulls attention even when it's silent; taking it out to show a photo is fine, "
                 "it's the checking that annoys people.")),
    entry("read-book-first", ("book", ("film", "movie"),
                         # "is the book better than the film" is the same question asked as a
                         # comparison, and it was answered with the yellow-card row, whose
                         # ending table lets "book" stand for "booking"
                         #
                         # The ask group is the *order*: first, before, better, which. "good"
                         # and "best" are how a person asks for a book to read, not how they
                         # ask which to do first, and with them here this row answered every
                         # "any good books for a 12 year old" and "any good book
                         # recommendations" with the book-versus-film rule. "as good as" stays
                         # because it is the comparison said in full: "is the film as good as
                         # the book" is this question and lost it when the bare "good" went.
                         ("before", "first", "adaptation", "better", "worse", "which",
                          "as good as", "good as")),
          _asked("Read the book first if you care about the story, watch the film first if you "
                 "might not finish the book. An adaptation cuts, so the film rarely ruins a "
                 "good novel — the other way round happens more."),
          # "what should i book first for a holiday" is a travel order-of-work question: "book"
          # as a verb plus "first" was this entry's key, and it answered with a novel. The words
          # of a trip catch the line only when it names one, so the verb itself stands the row
          # down too: "so what should we book first" after a trip is the same question with the
          # trip left out, and the comedy it got was the pick row's guard handing it straight to
          # this one.
          guard=lambda understood: not the_book_is_a_reservation(understood),
          avoid=("holiday", "holidays", "flight", "flights", "hotel", "hotels", "trip",
                 "travel", "accommodation", "airbnb", "villa", "restaurant", "table",
                 "train", "trains", "tickets", "ferry", "car hire", "hire car", "check in",
                 "check-in", "abroad")),
    entry("split-bill-etiquette", (("split the bill", "splitting the bill", "split the cost",
                          "go halves", "go halfs", "splitting a bill", "split the tab",
                          "split tabs", "split the check",
                          # the plural with no article is how people write it: "what is the
                          # etiquette for splitting bills" was stood down by money's row and
                          # then shrugged, because no key here held the plural
                          "split bills", "splitting bills",
                          # "divide the bill" is the same question as "split the bill", and the
                          # verb was not here: "how do i divide the bill between 4 people" reached
                          # the household row and was answered with rent by room.
                          "divide the bill", "dividing the bill", "divvy up the bill",
                          "share the bill", "sharing the bill"),
                         ("fair", "ok", "rude", "should", "right", "better", "how", "best",
                          "friends", "even",
                          # "is it fine to split the bill" and "is it okay to split the bill" are
                          # the same question as "is it rude ...", and neither word was here, so
                          # both went to the couple's income split: fine and okay are the two the
                          # list was missing.
                          "fine", "okay",
                          # A manners question is this row's whatever adjective the person
                          # reached for: "is it cheeky to split the bill", "is it tight to go
                          # halves", "what are the manners for splitting a bill". The household
                          # row in money stands down for the shape of that question, so this row
                          # has to catch it or the line gets a shrug.
                          "etiquette", "manners", "awkward", "impolite", "polite", "cheeky",
                          "stingy", "tight", "mean", "rude", "weird", "strange", "wrong",
                          "acceptable", "normal", "expected",
                          # "is it bad form to split the bill" found no judgement word here and
                          # went to a lifeadmin card about the law: the words a person calls
                          # this question by are the row's, and these are the rest of them
                          "bad form", "selfish", "generous", "allowed", "supposed", "unfair",
                          "annoying", "greedy", "stingey", "cheapskate")),
          _asked("Even split is fine when everyone ordered roughly the same; ask for separate "
                 "bills when one person had the steak and the wine. Say it before the bill "
                 "arrives and nobody has to be awkward."),
          # a shared flat's bills are a standing arrangement, not one dinner: lifeadmin's
          # split-bills is the answer for those
          # A table's manners question is this row's even when a chip-in row also fits the words
          # ("is it rude to split the cost", "is it rude to go halves" went to the office-collection
          # answer), and the chip-in rows keep their own lines: "should i chip in for a present"
          # names no split of a bill, so nothing here competes for it.
          bias=1,
          # A dinner's bill and a household's bills are the same words, so the row needs the table
          # in the line or the manners question, and it stands down where the line names a home
          # or the person the money is shared with. See `_a_table_bills_line`.
          guard=_a_table_bills_line,
          avoid=("housemate", "housemates", "flatmate", "flatmates", "roommate", "roommates",
                 "household", "flat share", "house share", "shared flat", "shared house",
                 "with my flat", "council tax", "electricity", "broadband",
                 # the plural key below ("split bills") also fits two people pooling their money,
                 # and that is the couple row's: "how do i split bills with a partner" came back
                 # with the table answer. The house-share words above keep a shared flat's bills
                 # out for the same reason.
                 "partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
                 "other half", "as a couple", "joint account", "our bills", "the rent",
                 # ... and neither is a cost away from a table. "split the cost" is a phrase this
                 # row keys, so a taxi, a hotel room, a rented cottage and a whip round for a
                 # present all arrived here and were told about who had the steak and the wine.
                 # Those are money's share-a-cost, and the subject is what tells them apart.
                 "taxi", "taxis", "cab", "cabs", "uber", "ride", "fare", "fares", "petrol",
                 "diesel", "fuel", "parking", "toll", "tolls",
                 "hotel", "hotel room", "a room", "the room", "rooms", "cottage", "cottages",
                 "airbnb", "villa", "caravan", "holiday house", "holiday home", "apartment",
                 "present", "presents", "gift", "gifts", "collection", "whip round", "kitty",
                 "secret santa", "leaving present", "wedding present",
                 # the same for the two biggest shared costs people ask about: a group holiday
                 # and the flights to it have their own card in money
                 "holiday", "holidays", "vacation", "flight", "flights", "trip", "weekend away",
                 "week away", "weekend break", "city break", "abroad", "group holiday")),
    entry("regift", (("regift", "re-gift", "re gift", "give it away"),
                     ("ok", "rude", "fine", "should", "wrong")),
          _asked("Fine, with two rules: the person who gave it to you never finds out, and the "
                 "next person would actually use it. Take the original card out first.")),
    entry("learn-to-drive", (("learn to drive", "driving licence", "driving license",
                              "driving test", "driving lesson", "driving lessons"),
                             ("should", "worth", "need", "old", "late", "adult", "any point")),
          _asked("Yes, if you'll use it: the licence is much easier to get at 20 than at 40, and "
                 "it opens up jobs and weekends. In a city with good buses and trains the cost "
                 "rarely adds up, so decide on the next five years, not on the test."),
          # "how many lessons do i need" is someone already learning, asking for a number: the
          # should-you-learn answer is not it, and a hedge beats a wrong yes/no.
          # Renewing, replacing or losing a licence you already hold is not a should-i-learn
          # question: lifeadmin has the renewal answer. "need" is why it reached here at all.
          avoid=("how many", "how long does it take", "how long until", "how often",
                 # a test already failed is the day-after answer, not should you learn at all
                 "fail", "failed", "failing", "fails", "flunked",
                 "renew", "renews", "renewing", "renewal", "expired", "expires", "runs out",
                 "replace", "replacement", "lost", "photocard")),
    entry("keep-a-diary", (("keep a diary", "write a diary", "start a diary", "keeping a diary",
                            "journal", "journaling"),
                           ("worth", "should", "start", "keep", "help", "good", "why")),
          _asked("Worth two weeks, then decide. Three lines at night is enough to show you "
                 "patterns you'd otherwise miss; if it starts to feel like homework, stop — "
                 "a diary you dread is worse than none.")),

    # --- learning an instrument as an adult: the question and its follow-ups --
    entry("instrument-adult", (("instrument", "piano", "guitar", "ukulele", "violin", "drums",
                                "keyboard", "flute", "cello", "sax", "saxophone", "trumpet",
                                "clarinet", "harmonica", "singing", "sing", "choir", "harp"),
                               # "old" and "late" alone are not evidence that anyone is learning
                               # anything ("its 9 yrs old"), so the key needs a learning word.
                               ("adult", "learn", "learning", "learned", "learnt", "start",
                                "begin", "wanted", "always", "worth", "45", "40", "50", "60",
                                "age", "old age", "my age")),
          # A report of what someone is already doing ("I'm trying to learn the guitar") is the
          # conversation's business, not an opinion question, so the take needs an ask.
          _asked(_start_instrument),
          # "drum" is a washing machine drum and an ear drum, and "keyboard" is a computer one.
          avoid=("daughter", "son", "kid", "kids", "child", "children", "grandson",
                 "granddaughter", "nephew", "niece", "teenager", "toddler", "washing",
                 "laundry", "machine", "dryer", "tumble", "ear", "ears", "eardrum",
                 "boiler", "loud", "noisy", "computer", "laptop", "typing", "champagne",
                 "prosecco", "wine", "sparkling"),
          bias=1),
    entry("instrument-how-long", (("song", "tune", "piano", "guitar", "ukulele", "violin",
                                   "instrument", "music", "chords", "scales", "beat", "drum",
                                   "drums", "flute", "cello", "sax", "trumpet", "singing"),
                                  ("how long", "long", "months", "month", "weeks", "soon")),
          _how_long_song,
          # an ear drum, a brake drum and a washing machine drum are not this question, and
          # "my mate is doing an open mic next week" asked for none of it: a date for a
          # performance is not a question about how long the learning takes.
          avoid=("ear", "ears", "eardrum", "washing", "machine", "laundry", "brake", "brakes",
                 "cardrum", "tumble", "dryer", "open mic", "open mike", "gig", "gigs",
                 "concert", "recital", "audition", "performance", "performing", "on stage",
                 "nervous", "mc"),
          bias=1),
    entry("instrument-practise", (("practise", "practice"), ("first", "start", "begin", "what")),
          _practise_first,
          avoid=("driving", "exam", "test", "interview", "speech", "presentation", "football",
                 "singing", "language", "spanish", "french", "italian", "german", "amp", "buy",
                 "purchase", "shop", "pedal", "strings", "course", "app", "tutor", "teacher")),
    # The same verb, the other question: how often rather than what first. A rate is a figure
    # and the practice-first row has none, so the two rows never want the same line.
    entry("instrument-how-often", (("practise", "practice", "practising", "practicing"),
                                   ("how often", "often", "how many times", "times a week",
                                    "a day", "per day", "how much should i practise",
                                    "how much practice", "every day", "daily", "minutes")),
          _how_often_at_it,
          # a driving lesson, a language app and a football session have their own rows, and a
          # line about buying the thing or resting an injury is not asking for a rate
          avoid=("driving", "exam", "test", "interview", "speech", "presentation", "football",
                 "tennis", "golf", "singing", "language", "spanish", "french", "italian",
                 "german", "amp", "buy", "purchase", "shop", "pedal", "strings", "course",
                 "app", "tutor", "teacher", "rest", "stop", "hurt", "hurts", "pain", "sore",
                 "injury", "injured",
                 # A thing practised that is not an instrument has its own row and its own
                 # rate: "how often should i practise my serve" was the tennis answer and came
                 # back as the generic instrument one.
                 "serve", "serves", "toss", "tosses", "swimming", "swim", "running", "run",
                 "cycling", "cycle", "gym", "weights", "yoga", "dancing", "dance", "singing",
                 "boxing", "climbing", "skating", "skiing", "batting", "bowling", "cricket",
                 "golf", "putting", "netball", "hockey", "basketball", "rugby", "football",
                 "tennis", "badminton", "squash", "rowing", "sailing")),

    # --- this or that ---------------------------------------------------------
    # What it costs to keep each one is a row of its own, with the yearly figures in it, so a
    # line about money stands this comparison down and gets that row instead.
    _either("cats-dogs", ("cat", "cats"), ("dog", "dogs"), _cats_or_dogs,
            avoid=("cheaper", "cheap", "cheapest", "cost", "costs", "costing", "afford",
                   "affordable", "money", "price", "prices", "expensive", "per year",
                   "a year", "a month", "insurance")),
    _either("tea-coffee", ("tea",), ("coffee",), _tea_or_coffee),
    _either("paper-ebook", ("paper", "paperback", "book", "books"),
            ("kindle", "ereader", "e-reader", "ebook", "ebooks"),
            "Paper for anything you want to remember, an e-reader for holidays and long queues. "
            "The real question is whether you're carrying it."),
    _either("tabs-spaces", ("tab", "tabs"), ("space", "spaces"),
            "Spaces: every editor shows them the same way, and nobody argues about how wide a "
            "tab is."),
    _either("android-iphone", ("android",), ("iphone", "apple"),
            "iPhone if you want the simplest five years of updates; Android if you want a "
            "cheaper phone or more choice of hardware. Neither is a mistake.",
            # technology's iphone-or-android says the same thing and adds the concrete bit (the
            # two-year-old iPhone, the mid-range Samsung, the headphone jack), so a phone choice
            # goes there. "apple" alone is left out of this guard on purpose: it is also fruit.
            avoid=("android", "iphone")),
    _either("city-country", ("city", "town"), ("countryside", "country", "village", "rural"),
            "City for a week, countryside for a month. If I had to choose one for good it would "
            "be the countryside, with a town within reach."),
    _either("beach-mountains", ("beach", "coast", "sea"), ("mountain", "mountains", "hills"),
            "Mountains: you can always find shade and a view, and the walk earns the dinner. "
            "Beaches win with small children, though — sand keeps them busy for hours."),
    _either("sweet-savoury", ("sweet", "sugary"), ("savoury", "salty"),
            "Savoury on a normal day — eggs, or toast with something salty — because it keeps "
            "you going until lunch. Sweet is for weekends and holidays."),
    # "hot" and "cold" are the keys, because that is how people ask; a radiator that is cold at
    # the top and hot at the bottom names both without ever being a choice, and reaching that
    # entry only to pass on it would hide the answer the home domain has.
    _either("hot-cold-weather", ("hot", "hot weather", "summer", "warm", "sunshine"),
            ("cold", "cold weather", "winter", "freezing", "snow"),
            "Cold, if I can wrap up: you can always add a layer, and a cold walk ends with a hot "
            "drink. Heat is harder to escape from.",
            avoid=("than", "because", "degrees", "radiator", "radiators", "boiler", "thermostat",
                   "bleed", "bleeding", "at the top", "at the bottom", "toes", "hands",
                   # hot and cold on the body or in water is a different question (a shower, a
                   # bad back, a sprain), and the weather take is the wrong answer to it.
                   "bath", "shower", "showers", "swim", "swimming", "pool", "sauna",
                   "compress", "ice pack", "heat pack", "hot water bottle", "sore",
                   "muscle", "muscles", "back", "sprain", "sprained", "stiff", "stiffness",
                   "injury", "injured", "cramp", "ache", "aches", "fever", "chills")),
    _either("cinema-home", ("cinema", "big screen"), ("home", "streaming", "sofa", "netflix"),
            "Cinema for anything with scale or a big sound; home for comedies and anything you "
            "might pause. The cinema's real advantage is that nothing else asks for your "
            "attention for two hours."),
    _either("rent-buy", ("rent", "renting", "rented"), ("buy", "buying", "mortgage", "owning"),
            "Buy once you know where you want to be for five years or more and the mortgage is "
            "no more than a third of your take-home pay; rent until then, and keep the deposit "
            "growing. Renting is also the honest answer when the job might move.",
            avoid=("car", "van", "bike", "flat for the weekend", "holiday"),
            bias=1),
    _either("run-walk", ("run", "running", "jog", "jogging"), ("walk", "walking"),
            "Walk if you are starting out or carrying an injury, run if you want the same "
            "fitness in half the time. Walking is easier to keep up for a year, and a year is "
            "what changes anything."),
    # A commute is not a workout: the answer is which one you will still do in the rain.
    _either("walk-cycle", ("walk", "walking", "on foot"), ("cycle", "cycling", "bike",
                                                             "bicycle"),
            "Cycle if the trip is more than about two miles and there is somewhere to lock a bike "
            "and change; walk if it is shorter and you want the thinking time. Under twenty "
            "minutes either way it comes down to which one you will still do in the rain."),
    _either("electric-petrol", ("electric", "electric car", "ev"), ("petrol", "diesel", "hybrid"),
            "Electric for the everyday car: cheaper to run, quieter, and charging at home beats "
            "a forecourt. Petrol still wins if you drive long distances weekly or cannot charge "
            "at home; a hybrid is the compromise that suits most people who cannot.",
            avoid=("won't", "wont", "charging point", "not charging", "battery", "repair",
                   "garage", "lease")),
    entry("remote-work", (("remote work", "remote working", "working from home", "wfh",
                           "hybrid working"),
                          ("think", "good", "better", "worth", "opinion", "prefer", "like")),
          _asked("Remote for the work that needs quiet, the office for the work that needs "
                 "people. Two or three days in is the arrangement most people end up "
                 "preferring, and it keeps you in the room when decisions get made."),
          avoid=("focus", "distracted", "routine", "procrastinating", "lonely", "isolated")),
    # --- the choice someone is stuck on ------------------------------------------------------
    # A cat is one of the lives people weigh up as often as a dog, and the row's key was the
    # table above, which never held a cat: "im thinking of getting a cat" and "is it worth
    # getting a cat" were answered with the new-cat shopping list, and the cat trade that
    # `_deciding` already writes could not be reached. The cat's own words are in the key here,
    # and `_deciding` still stands the row down for a thing for the cat, a name, and a neutering.
    entry("decide-a-choice",
          (tuple(word for options, _ in DECISION_SUBJECTS for word in options) + CAT_WORDS,
           STUCK_SHAPES, DECIDE_WORDS),
          _deciding, ask=STUCK_SHAPES + ("decide", "deciding", "decision", "whether", "choice"),
          # a step target, a fault, a recipe and a symptom are all questions about the thing
          # itself, not about whether to have it
          avoid=("step", "steps", "wont", "won't", "isnt", "isn't", "broken", "fault", "leak",
                 "leaking", "recipe", "recipes", "cook", "drain", "not working", "sick", "ill",
                 "vet", "insurance", "tax", "mot", "service", "repair", "error", "flashing",
                 # a pick between two named things is this domain's `_either` pairs, not a
                 # decision to weigh up: "should i get a cat or a dog" has an answer already
                 "or", "vs", "versus", "either",
                 # a name is a decision to make, not one to weigh up: "i cant choose a name for
                 # my dog" wants the naming rule, which another row already gives
                 "name", "names", "naming", "called", "call it", "what to call",
                 # two things compared are a fact question, not a choice: "whats the difference
                 # between a dog and a cat"
                 "difference", "differences",
                 # neutering a dog or a cat you already have is a when question with its own
                 # answer, not a choice to weigh up: "when should i get my dog neutered" was
                 # read as "should i get a dog"
                 "neuter", "neutered", "neutering", "neuters", "spay", "spayed", "spaying",
                 "castrate", "castrated", "the snip",
                 # what to watch, read or play is a recommendation, which another row gives:
                 # "cant decide what to watch tonight" is not a life choice
                 "watch", "watching", "film", "films", "movie", "movies", "series", "tv",
                 "netflix", "read", "reading", "book", "books", "play", "game", "games")),
    # "is a cat a good idea" is "should i get a cat" in the words a verdict uses. Same trade,
    # same writer, and it stands back for every cat question another row owns.
    entry("cat-decide",
          (CAT_WORDS, CAT_VERDICT_SHAPES),
          _deciding, ask=CAT_VERDICT_SHAPES, bias=1,
          avoid=("need", "needs", "need to", "buy", "buying", "bought", "shop", "shopping",
                 "list", "kit", "litter", "tray", "food", "feed", "name", "called", "call it",
                 "spay", "spayed", "spaying", "neuter", "neutered", "neutering", "the snip",
                 "scratch", "scratching", "hiss", "hissing", "vet", "ill", "sick", "unwell",
                 "wont", "won't", "isn't", "isnt", "broken", "difference", "vs", "versus",
                 # two of them and a second one are the company question, which has its own
                 # card: "is a second cat a good idea" is answered about company, and the
                 # "would two be better than one" follow-up keeps that answer
                 "two", "second", "pair", "better than one", "another"),
          guard=_not_another_cats_question),
]



# A machine with its own worth-it row in shopping.py is not the rule of thumb's line, and the
# phrases that carry one of these names inside them named the wrong machine: "is a vacuum sealer
# worth it" was told a vacuum cleaner is worth it if you would use it three times a week. The
# words go on the entry after the list rather than inside the tuple, because the rule of thumb is
# one row among many and this is one fact about it.
for _rule_of_thumb in ENTRIES:
    if _rule_of_thumb.id == "worth-an-appliance":
        _rule_of_thumb.avoid = _rule_of_thumb.avoid + (
            "sealer", "sealers", "vacuum sealer", "vacuum sealers", "food sealer", "food sealers")
