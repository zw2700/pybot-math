"""What to say.

The message or email for a landlord, a refund, a boss, a friend. Each entry is the
wording itself, ready to adapt, plus the one thing to keep in mind about tone.

The matcher in bot/knowledge/lookup.py finds the entry; bot/modules/answers.py answers.
"""
import re

from ..compose.repair import owns_the_deed
from .lookup import MACHINE_SOUNDS, entry, the_fault, SLIPS

# The plain words for a noise, when the person has not said which sound it is. A machine or a
# neighbour is audible and the answer needs to know that, so every row that answers a noise reads
# this one list: "the washing machine is making a racket" reached nothing at all, while "noisy"
# three words later got a full answer, and "the neighbours are making a racket" was echoed back.
NOISE_WORDS = ("noise", "noises", "noisy", "loud", "racket", "racketing", "din", "clatter",
               "clattering", "thunderous", "deafening", "row", "drone", "droning", "palaver")

# Whose screens a line is about: the writer's own phone, a child's, or somebody else's. Three
# rows need it and each of them was matching the words alone - "im always on my phone how do i
# stop" reached the children's limit, "my husband is always on his phone" reached it too, and
# "my teen is always on his phone" reached the writer's own habit - so the test lives here, once,
# rather than three times.
_A_CHILD_NAMED = (
    "kid", "kids", "child", "children", "toddler", "toddlers", "baby", "son", "sons",
    "daughter", "daughters", "boy", "girl", "teen", "teens", "teenager", "teenagers",
    "stepson", "stepdaughter", "grandchild", "grandchildren", "grandson", "granddaughter",
    "year old", "year olds", "primary school", "secondary school", "nursery", "school age")
_ONLY_SAID_ABOUT_A_CHILD = ("screen time", "screentime")
_SOMEBODY_AT_HOME = (
    "my mum", "my mom", "my mother", "my dad", "my father", "my husband", "my wife",
    "my partner", "my girlfriend", "my boyfriend", "my stepson", "my stepdaughter",
    "my flatmate", "my housemate", "my room mate", "my roommate", "my friend", "my mate",
    "my brother", "my sister", "my nan", "my nana", "my gran", "my granny", "my grandma",
    "my grandad", "my grandpa", "my uncle", "my aunt", "my auntie", "my cousin", "my boss",
    "my colleague", "my staff")
_THEIR_SCREENS = re.compile(r"\b(?:his|her|their)\s+(?:phone|phones|screens?|tablet|ipad|ipads)\b")
_MY_OWN_SCREENS = re.compile(r"\b(?:my|the)\s+(?:phone|phones)\b|\bim\s+(?:always\s+)?on\b|"
                             r"\bi'm\s+(?:always\s+)?on\b")


def the_line_said(understood):
    """The line as one lower-case string with spaces round it, or "" when there is no line."""
    reading = understood if isinstance(understood, dict) else {}
    said = " ".join(str(reading.get("clean") or reading.get("text") or "").split()).lower()
    return f" {said} " if said else ""


def _names_one_of(said, phrases):
    tokens = set(re.findall(r"[a-z']+", said))
    return any(phrase in said if " " in phrase else phrase in tokens for phrase in phrases)


def screens_are_a_childs(understood):
    """True when the screens in the line belong to a child, so a parent's limit answer fits."""
    said = the_line_said(understood)
    if not said.strip():
        return True
    if any(phrase in said for phrase in _ONLY_SAID_ABOUT_A_CHILD):
        return True
    return _names_one_of(said, _A_CHILD_NAMED)


def screens_are_somebody_elses(understood):
    """True when the phone in the line is not the writer's own.

    A line that says "my phone" or "im on" is the writer's whatever else it names, which is what
    keeps "my girlfriend says im always on my phone" off the card about her phone.
    """
    said = the_line_said(understood)
    if not said.strip():
        return False
    if _MY_OWN_SCREENS.search(said):
        return False
    # A child's screens are the parent's question, not the "talk to them about it" card for a
    # partner: "my grandson is always on his tablet" is the screen-time answer, and this card had
    # taken it because a grandchild reads as somebody else at home.
    if screens_are_a_childs(understood):
        return False
    if _THEIR_SCREENS.search(said):
        return True
    return any(phrase + " " in said for phrase in _SOMEBODY_AT_HOME)


def _birthday_age(text):
    """The age the line names, as an int, or None.

    A card for a child of seven answered with an example that said "Happy 40th": the phrasing was
    a fixed string, so the number in it was the number in the person who wrote it. People give the
    age as an ordinal ("70th", "7th"), or as a plain number after the word ("turning 7", "turns 5").
    """
    said = str(text or "").lower()
    found = re.search(r"\b(\d{1,3})(?:st|nd|rd|th)\b", said)
    if not found:
        found = re.search(r"(?:birthday|turning|turns|going on|hits?)\D{0,12}(\d{1,3})\b", said)
    if not found:
        # An age said the other way round: "my nan is 90 next month", "he is 50 in june".
        # The number is only an age when the line says when it lands, so a price or a count in
        # the same sentence is not read as one.
        found = re.search(r"\b(\d{2,3})\b\s*(?:next|this|in)\s*"
                          r"(?:week|month|year|weekend|june|july|august|september|october|november"
                          r"|december|january|february|march|april|may|christmas|summer|spring"
                          r"|autumn|winter|easter)\b", said)
    if not found:
        # "what should the card say for a 6 year old": the age is the person, not a quantity.
        found = re.search(r"\b(\d{1,2})\s*(?:year|yr)s?[ -]?old\b", said)
    if not found:
        return None
    age = int(found.group(1))
    return age if 1 <= age <= 120 else None


def _ordinal(number):
    if number % 100 in (11, 12, 13):
        return "%dth" % number
    return "%d%s" % (number, {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th"))


# A person who has just said the birthday one hates a fuss wants a different card from the one
# this row opens with: "shes turning 40 and she hates being the centre of attention" was answered
# with the whole paragraph again, joke and all, because the example is chosen by age alone. The
# quiet card is one true thing said plainly, so it is its own words rather than a tweak.
_NO_FUSS = re.compile(
    r"\b(hates?|hated|doesnt|does not|doesn't|dont|don't|not|no|never|isnt|isn't)\b[^.?!]{0,30}"
    r"\b(fuss|attention|centre of attention|center of attention|spotlight|big deal|surprise|"
    r"surprises|party|to do|big do|a do|night out|speech|faff)\b"
    # The fuss said the other way round, with the noun first: "something quiet for her birthday",
    # "no fuss please", "just a small thing".
    r"|\b(quiet|low key|low-key|private|small|low|no fuss)\b[^.?!]{0,16}"
    r"\b(birthday|do|party|meal|dinner|card|thing)\b")


def _names_an_age(words):
    """The line gives the age the card is for, which is what picks its example.

    One signal, the same weight as a key word, and the card still has to be in the line: a
    birthday card row is the answer to "what do i write in my nans card", but only the age
    says which card it is when the line never says "birthday".
    """
    return _birthday_age(words) is not None


# Who the card is for decides the example, so the line has to be read for the person as well as
# for the age. "For a colleague or someone you do not know well, a warm plain line is enough" was
# said to a person writing to their nan on her 90th, where it is not advice but a change of
# subject, and a colleague was offered the 3am story, which is a card for someone you know. A line
# that names nobody keeps both halves, because either could be the card they need.
_A_COLLEAGUE = re.compile(
    r"\b(?:colleagues?|co-?workers?|workmates?|boss|manager|staff|team|teacher|neighbou?r|"
    r"acquaintance|someone at work|people at work|the office)\b")
_A_CLOSE_ONE = re.compile(
    r"\b(?:nan|nana|gran|granny|grandma|grandmother|grandad|grandpa|grandfather|mum|mom|mam|"
    r"mother|dad|father|sister|brother|aunt|auntie|uncle|cousin|wife|husband|partner|"
    r"girlfriend|boyfriend|friends?|mates?|best mate|son|daughter|grandson|granddaughter)\b")


def _card_birthday(memory, reading):
    """The words for a birthday card, with the age the person gave rather than a made-up one."""
    reading = reading if isinstance(reading, dict) else {}
    said = reading.get("clean") or reading.get("text") or ""
    age = _birthday_age(said)
    which = _ordinal(age) if age else "birthday"
    if _NO_FUSS.search(said):
        return ("Keep it plain and quiet, because that is the card a person who hates a fuss "
                "actually wants: \"Happy %s - no fuss, I'm just glad you're in my life.\" One "
                "true thing about them, no joke and no speech, and give the present quietly "
                "rather than in front of everyone." % which)
    # The example has to fit the person: the 3am story was the whole answer before, and it is a
    # grown-up's story. A card for a child gets something a child did, and a teenager is neither
    # a child nor a colleague: at 13 the reply was telling the person it was for someone they did
    # not know well, which is the opposite of a card for their own daughter.
    if age and age < 13:
        example = ("\"Happy %s - the year you finally beat me at cards.\" One true thing they did "
                   "beats any joke, and for a small child the card is really for the parent: keep "
                   "it short and kind." % which)
    elif age and age < 18:
        example = ("\"Happy %s - still the best person to be stuck in a car with.\" One thing the "
                   "two of you actually do together beats any joke about the number, and a "
                   "teenager reads a short card: no advice, no speech, and the money is welcome."
                   % which)
    elif _A_COLLEAGUE.search(said):
        example = ("\"Happy %s - hope you get spoiled.\" With someone you do not know well the "
                   "warm plain line is the card itself: no in-joke, and put the money or gift "
                   "honestly (\"Have a drink on me\")." % which)
    elif _A_CLOSE_ONE.search(said):
        example = ("\"Happy %s - I still tell people about the night you drove us home at 3am.\" "
                   "They are close enough for the in-joke, so use the one only the two of you "
                   "would get." % which)
    else:
        example = ("\"Happy %s - I still tell people about the night you drove us home at 3am.\" "
                   "For a colleague or someone you do not know well, a warm plain line is enough "
                   "(\"Happy birthday - hope you get spoiled\"), and put the money or gift "
                   "honestly (\"Have a drink on me\")." % which)
    return ("Name one thing you like about them and skip the round-number joke: " + example)


def _card_plain(memory, reading):
    """The card for an occasion the line never names, and the quiet one when it asks for one.

    "what do i write in a card for my neighbour" is the two-line note, and that is right for a
    card with no occasion. The same line with a person who hates a fuss in it ("a card for
    someone who hates a big do") is asking for the quiet card, and the whole paragraph about
    naming one real thing and one wish is exactly what they said they did not want.
    """
    reading = reading if isinstance(reading, dict) else {}
    said = reading.get("clean") or reading.get("text") or ""
    if _NO_FUSS.search(said):
        return ("Keep it plain and quiet, because that is the card this person actually wants: "
                "\"Happy birthday - no fuss, I'm just glad you're in my life.\" One true thing "
                "about them, no joke and no speech, and give the present quietly rather than in "
                "front of everyone.")
    return ("Name one real thing about them and one wish, then stop - two lines is a card: "
            "\"Thinking of you both - hope the year is a good one.\" If you do not know them well, "
            "warm and plain beats clever, and sign it with your full name.")


# The ask for the words, in whatever modal the person used. card-something is the row for a card
# with no occasion in the line, and it used to hold only the phrases it had been shown ("what do
# i write", "what to write"): "what shall i write in a card for my mate who hates a fuss" reached
# nothing at all and got the search hedge, because a shall is not a do. The shape still needs
# somewhere to write the words: "what do i even write" in the middle of a parking appeal is a
# different question, and a card was the wrong answer to it.
_ASKS_FOR_THE_WORDS = re.compile(
    r"\b(?:what|how)\b[^.?!]{0,14}?\b(?:do|should|shall|can|could|would|will|might|to|am i)\b"
    r"[^.?!]{0,10}?\b(?:write|writing|say|saying|put|word|phrase|sign off)\b"
    r"[^.?!]{0,24}?\b(?:card|cards|note|notes|message|messages|letter|letters|inside|envelope)\b"
    r"|\b(?:card|cards|note|notes|message|messages|letter|letters)\b[^.?!]{0,24}?\b(?:what|how)\b"
    r"[^.?!]{0,12}?\b(?:write|say|put|word|phrase)\b")


def _asks_for_the_words(line):
    """A shape: the line asks what words to use, whatever modal carries the ask."""
    return bool(_ASKS_FOR_THE_WORDS.search(str(line or "").lower()))


ANSWERS = ("language-and-writing",)


# The words people most often ask how to spell, each with the reason it is spelled that way, so the
# answer is one line to remember rather than a rule to look up. The misspellings are spelled out
# too: somebody typing "definately" wants an answer, not a shrug, and the matcher cannot reach
# "definitely" from it (the slip is two letters, not one).
SPELLINGS = (
    ("definitely", ("definately", "definatly", "definitley", "defintely"),
     "Definitely has **finite** inside it: de-finite-ly. Two i's, and no a anywhere."),
    ("separate", ("seperate", "seperately", "seperatly", "seperates"),
     "Separate has **a rat** in the middle: sep-a-rat-e. There is an a after the p, and another "
     "before the t."),
    ("tomorrow", ("tommorow", "tommorrow", "tomorow"),
     "Tomorrow has one m and two r's: to-m-o-rr-o-w. Say \"to morrow\", then close it up."),
    ("because", ("becuase", "becasue", "becouse"),
     "Because has **cause** in it: be-cause. If you can spell cause, you can spell because."),
    ("receive", ("recieve", "recieved", "recieving"),
     "Receive is i before e except after c: re-cei-ve. Recieve gets it the wrong way round, which "
     "is why it is the classic one."),
    ("believe", ("beleive", "belive", "beleiving"),
     "Believe is be-lie-ve: the **lie** is in the middle. Receive is the one that goes -ei-."),
    ("accommodation", ("accommodate", "accomodation", "acommodation", "acomodation",
                       "accomodate"),
     "Accommodation has two c's and two m's: a-cc-o-mm-odation, and accommodate keeps both."),
    ("necessary", ("neccessary", "necesary", "neccesary"),
     "Necessary has one c and two s's: picture a shirt with one **c**ollar and two **s**leeves. "
     "Necessarily and necessity keep the same shape."),
    ("calendar", ("calender",),
     "The thing with the months is calendar, with an a before the r. A calender is a machine that "
     "presses paper flat."),
    ("embarrass", ("embarass", "embarrassing", "embarasing"),
     "Embarrass has two r's and two s's: em-ba-rr-a-ss. Think \"bare arse\" and you will not "
     "forget it."),
    ("rhythm", ("rythm", "rythem", "rhythym"),
     "Rhythm is r-h-y-t-h-m and has no ordinary vowel of its own: \"rhythm helps your two hips "
     "move\" spells it."),
    ("weird", ("wierd", "wierdly"),
     "Weird breaks the rule: w-e-i-r-d, e before i. The line to remember is \"we are weird\"."),
    ("friend", ("freind", "freinds", "frend"),
     "Friend ends in **end**: fri-end. The e goes before the n, unlike most -ie- words."),
    ("beautiful", ("beutiful", "beautifull", "beatiful"),
     "Beautiful is beauty plus -ful: b-e-a-u-t-i-f-u-l. One t, one l."),
    ("business", ("buisness", "busines", "buisnesses"),
     "Business is busy-ness gone crooked: b-u-s-i-n-e-s-s."),
    ("beginning", ("begining", "beginnig"),
     "Beginning has two n's in the middle: be-gi-nn-ing. The stress is on the second syllable, so "
     "the n doubles."),
    ("occurred", ("occured", "occuring", "ocurred"),
     "Occurred has two c's and two r's: o-cc-u-rr-ed. Occur doubles both when it grows a tail."),
    ("until", ("untill", "untl"),
     "Until has one l. Till and until both exist, but the one-l until is the one people write."),
    ("address", ("adress", "adres", "addres"),
     "Address has two d's and two s's: a-dd-re-ss."),
    ("argument", ("arguement",),
     "Argument loses the e from argue: ar-gu-ment. Arguement has one letter too many."),
    ("forty", ("fourty",),
     "Forty has no u: four becomes forty by dropping it. Fourteen and fourth keep theirs."),
    ("probably", ("probly", "probally", "probaly"),
     "Probably is prob-ab-ly, all three syllables written even though we say two."),
    ("immediately", ("immediatly", "immediatley", "imediately"),
     "Immediately is im-medi-ate-ly: mediate is in the middle, so the a stays."),
    ("environment", ("enviroment", "enviornment"),
     "Environment has an n after the o: env-i-ron-ment, from environ, the surroundings."),
    ("government", ("goverment", "governement"),
     "Government has an n in the middle: govern-ment. It is govern with ment on the end."),
    ("surprise", ("suprise", "surprize", "surpise"),
     "Surprise starts sur-, from the French, not sup-. English uses s here, not z."),
    ("truly", ("truely", "truley"),
     "Truly drops the e from true: tru-ly. It is one of the few -ly words that loses it, with duly "
     "and wholly."),
    ("their", ("thier",),
     "Their is the belonging one: **their** house, like **her** house with a t. There is a place "
     "(it has here inside it), and they're means they are."),
    ("you're", ("youre", "your welcome", "your right", "your doing"),
     "You're means **you are**, so it keeps the apostrophe; your is belonging, as in your coat. If "
     "you can say \"you are\" in the sentence, it is you're."),
    ("lose", ("loose weight", "loosing"),
     "Lose has one o and rhymes with news; loose has two, rhymes with goose, and means not tight. "
     "\"Loose weight\" says the wrong word."),
    ("practice", ("practise or practice",),
     "In British English the noun is practice and the verb is practise: \"the practice\" but \"to "
     "practise\". American English uses practice for both."),
    ("congratulations", ("congradulations", "congratualtions", "congratuations"),
     "Congratulations has a t after the grat: con-grat-u-la-tions. Say \"gratitude\" to yourself "
     "and the t is there."),
    ("occasion", ("ocassion", "occassion", "ocasion"),
     "Occasion has two c's and one s: o-cc-a-s-ion. The double c is the one people drop."),
    ("across", ("accross", "acros"),
     "Across is one c and two s's: a-cross. The double c comes from hearing the join as a double "
     "sound."),
    ("quiet", ("quite or quiet", "quiett"),
     "Quiet, with the e last, is the opposite of noisy: q-u-i-e-t. Quite, with the e before the t, "
     "means fairly or completely - a quiet evening, but quite tired."),
)

# A thank-you note is about the thing the person did, so the example has to be their thing: a
# present, a weekend on someone's sofa, a meal, or a person who helped. One reply that always
# said "the meal on Saturday" answered "thank you message for my teacher" with a dinner, and a
# note that names the wrong thing is worse than no example at all.
# The note for a thanks that names nothing in particular ("what do i write in a thank you card"):
# one concrete example of the shape, in the same words whether it is a card, a text or a note.
THANKS_ANY = ("Name the thing they did, not the day in general: \"Thank you for the lemon cake and "
              "for staying to help with the chairs, it made the afternoon easy.\" One line about a "
              "specific detail beats a paragraph of adjectives, and send it the same day, because "
              "thanks the next morning reads as an afterthought.")
THANKS_FLOWERS = ("flower", "flowers", "bouquet", "bouquets", "orchid", "orchids")
THANKS_GIFT = ("present", "presents", "gift", "gifts", "voucher", "vouchers", "hamper")
THANKS_STAY = ("stay", "stays", "staying", "stayed", "host", "hosts", "hosted", "hosting",
               "put me up", "weekend", "weekends", "nights")
THANKS_MEAL = ("meal", "meals", "dinner", "lunch", "tea", "supper", "party", "barbecue",
               "bbq", "food", "cooked", "cook", "fed", "cake", "roast")
THANKS_WRITTEN = ("card", "cards", "letter", "letters", "note", "notes", "text", "texts",
                  "message", "messages", "email", "emails")
# A thank-you note is most often for one job somebody did: feeding the cat, watering the plants,
# collecting the post, the lift to the station. Naming the job is the whole of the note, so it has
# its own branch ahead of the one about a person's role.
THANKS_LIFT = ("lift", "lifts", "drive", "drove", "driving", "picking up", "picked up",
               "dropping off", "dropped off", "run to", "airport", "station")
THANKS_FAVOUR = ("feeding", "fed", "watering", "watered", "looking after", "looked after",
                 "collecting the post", "collected the post", "cat", "dog", "plants", "post",
                 "bin", "house sitting", "housesitting")
THANKS_PERSON = ("teacher", "nurse", "carer", "midwife", "doctor", "neighbour", "neighbor",
                 "colleague", "boss", "manager", "childminder", "helped me", "helped us",
                 "who helped")


# What the news actually is, for how-to-tell-them: these conversations differ far more by subject
# than by the relation they are told to, and one script for all of them reads like a template.
_MOVING_OUT = re.compile(r"\bmoving out\b|\bmoving (?:house|flat|home)\b|\bleaving home\b|"
                         r"\bmoved out\b|\bmoving in with\b", re.IGNORECASE)
_MOVING_AWAY = re.compile(r"\bmoving away\b|\bemigrat\w*\b|\bgoing travelling\b|"
                          r"\bmoving abroad\b|\bmoving to (?:australia|canada|spain|france|"
                          r"new zealand|america|the us|germany|ireland|scotland)", re.IGNORECASE)
_BABY = re.compile(r"\bpregnan\w*\b|\bexpecting a baby\b|\bbaby on the way\b|"
                   r"\bhaving a baby\b", re.IGNORECASE)
# "how do i break the news to my team" says what kind of thing it is; "how do i say sorry to my
# wife" does not, and the news sentence is the wrong shape for an apology.
_SAID_IT_IS_NEWS = re.compile(r"\bnews\b|\bannounc\w*\b|\bbreak\s+(?:it|this|the)\b|"
                              r"\bbreak\s+bad\b", re.IGNORECASE)
_MONEY = re.compile(r"\bmoney\b|\bfinances?\b|\bdebts?\b|\bsalary\b|\bbills?\b|"
                    r"\bwages?\b", re.IGNORECASE)
_SHARED_HOUSE = re.compile(r"\b(?:housemate|flatmate|roommate|house ?mate)s?\b", re.IGNORECASE)
# The household-bills script is about money the two of you share, so the line has to name the
# sharing: "how do i tell my friend i cant lend them money" is a lending question, and the
# "pick a time that is not the moment a bill lands" speech is the wrong reply to it.
_HOUSEHOLD_MONEY = re.compile(r"\b(?:we|our|us|partner|husband|wife|spouse|bills?|rent|"
                              r"split|share|sharing|housemates?|flatmates?|roommates?|"
                              r"household|money with|finances)\b", re.IGNORECASE)
_PARENT_MONEY = re.compile(r"\b(?:my )?(?:parents?|mum|mom|mam|mother|dad|father|family|"
                            r"in ?laws?)\b", re.IGNORECASE)
_SHARE_MONEY = re.compile(r"\bpay\w*\b|\brent\b|\bbills?\b|\bshare\b|\bowe\w*\b|"
                          r"\bsplit\b|\bcouncil tax\b", re.IGNORECASE)
_MESS = re.compile(r"\bclean\w*\b|\bwashing up\b|\bwashing-up\b|\bdishes\b|\bmess\b|"
                   r"\btidy\w*\b|\bbins?\b|\bhoover\w*\b|\bload of washing\b", re.IGNORECASE)
# Raising a problem with a friend is the same advice whatever the problem is, but the example has
# to be about the thing the person is actually holding: "how do i tell my friend their dog scares
# my child" was told to say "I lent you £200", which reads as the bot inventing a debt. The
# topics below pick the example; the advice underneath is one sentence for all of them.
_RAISE_MONEY = re.compile(r"\bmoney\b|\blent\b|\blend\w*\b|\bborrow\w*\b|\bowe\w*\b|"
                          r"\bdebt\w*\b|\bpay\w*\b|\bquid\b|£", re.IGNORECASE)
# someone else's animal, or their children, on the other side of the problem: two examples,
# because a dog and a child are not the same complaint
# A cat is not a dog, and the example has to be the animal in the line: "her cat scratched my
# child" was told to say "Rex jumped up at Nell again", which is a dog and a different complaint.
# A cat in their garden is a different thing to say from a cat that scratched: the example is
# "keep her in at night", not "keep her out of the room".
_RAISE_CAT_OUTSIDE = re.compile(r"\b(?:cat|cats|kitten|kittens)\b(?=[^.]*\bgarden\b)|"
                                r"\bgarden\b(?=[^.]*\b(?:cat|cats|kitten|kittens)\b)",
                                re.IGNORECASE)
_RAISE_CAT = re.compile(r"\b(?:cat|cats|kitten|kittens)\b", re.IGNORECASE)
_RAISE_ANIMAL = re.compile(r"\b(?:dog|dogs|puppy|pets?|animal|horse|rabbit|parrot)\b",
                           re.IGNORECASE)
_RAISE_CHILD = re.compile(r"\b(?:child|children|kid|kids|son|daughter|baby|toddler|niece|"
                          r"nephew|boys|girls)\b", re.IGNORECASE)
# and a house you share, which is the mess and the noise rather than a person
_RAISE_HOUSE = re.compile(r"\b(?:noise|noisy|music|loud|party|parking|garden|"
                          r"hedge|fence|bin|bins|rubbish|alarm)\b", re.IGNORECASE)
# Smoke and a late party are both "a habit in your home", but the sentence to say is not the same
# one: "their party was too loud" was handed the smoke line. The smoke words get their own below.
_RAISE_SMOKE = re.compile(r"\bsmok\w*|\bcigarette\w*|\bvap\w*|\bsmoking\b", re.IGNORECASE)
_RAISE_EXAMPLES = (
    (_RAISE_CAT_OUTSIDE, '"your cat keeps using my veg bed - could you keep her in at night?"'),
    (_RAISE_CAT, '"Mog swiped at Nell again on Saturday - could you keep her out of the room '
                 'while we are there?"'),
    (_RAISE_ANIMAL, '"Rex jumped up at Nell again on Saturday - could you keep him in the kitchen '
                    'while she is here?"'),
    (_RAISE_CHILD, '"the boys were a bit rough with Nell on Saturday - could you keep an eye when '
                   'they are in the garden?"'),
    (_RAISE_SMOKE, '"the smoke comes through the wall - could you smoke by the back door?"'),
    (_RAISE_HOUSE, '"the music was still going at half one - could we call it midnight next time?"'),
    (_RAISE_MONEY, '"I lent you £200 and I have been unsure how to bring it up"'),
)
_RAISE_PLAIN = '"I felt left out when the plans changed"'
# The subjects an ask-for-the-one-thing reply can be about: the animal or the children the line
# names, or the smoke. Parking and noise have an example of their own below, and money is a
# different question, so a line that holds both ("the party was loud and they owe me") does not
# get a debt in a sentence about the music.
_RAISE_ASK_SUBJECTS = (_RAISE_CAT_OUTSIDE, _RAISE_CAT, _RAISE_ANIMAL, _RAISE_CHILD,
                       _RAISE_SMOKE)


def _raise_example(line, patterns=None):
    """The example sentence for this line, from the subject it names - or None."""
    for pattern, words in _RAISE_EXAMPLES:
        if patterns is not None and pattern not in patterns:
            continue
        if pattern.search(line):
            return words
    return None


# A friend's hurt is not always a grievance. "My friend hurt his arm" and "my friend hurt his back
# lifting" scored the friendship script on the two words "friend" and "hurt" alone and were told to
# say what happened, how it made them feel and what they want to change - about a body. The word
# "hurt" lands on somebody else's body when a possessive comes before a part, or on themselves when
# the verb is reflexive, and those lines are a first-aid question with an answer of their own.
_HURT_PART = (r"(?:back|arm|arms|leg|legs|knee|knees|ankle|ankles|shoulder|shoulders|wrist|wrists|"
              r"hand|hands|finger|fingers|thumb|toe|toes|foot|feet|hip|hips|head|neck|ribs?|rib|"
              r"shin|shins|calf|elbow|elbows|eye|jaw|collarbone|collarbones|spine)")
_SOMEONE_HURT_A_PART = re.compile(
    r"\bhurt\w*\s+(?:[a-z-]+\s+){0,2}(?:his|her|their|its)\s+(?:[a-z-]+\s+){0,2}"
    + _HURT_PART + r"\b"
    r"|\bhurt\w*\s+(?:my|his|her|their|your)\s+" + _HURT_PART + r"\b"
    r"|\bhurt\w*\s+(?:himself|herself|themselves|myself)\b",
    re.IGNORECASE)


def _not_a_hurt_body(understood):
    """False for a line whose "hurt" is on a body, which the body tables answer better."""
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return _SOMEONE_HURT_A_PART.search(line) is None


def _raise_problem(memory, understood):
    """The same advice for every problem between friends, with an example that fits this one."""
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    example = _raise_example(line) or _RAISE_PLAIN
    return ("Say what happened, how it made you feel and what you want to change, once: "
            + example + ". One topic at a time, no list of past grievances, and ask for their side.")


# Talking over someone is a thing to raise with them, not a conversation to end and not a
# listening tip. `end-a-conversation` keyed on "talking" and `keep-a-conversation-going` took the
# rest, so "how do i tell my friend she talks over me" was answered "I'll let you go - it's been
# really good to catch up" and "my friend keeps talking over me" with "ask about the answer you
# just got". The habit is named, so the script can be about the habit.
_TALKS_OVER = re.compile(r"\b(?:talks?|talking|talk) over (?:me|my)\b|"
                         r"\bkeeps? (?:talking|interrupting|cutting)\b|"
                         r"\b(?:interrupts?|interrupting) (?:me|my)\b|"
                         r"\bcuts? me off\b|\bkeeps? cutting me off\b|"
                         r"\b(?:butts?|butting) in\b|\bfinishes? my sentences?\b|"
                         r"\btalks? over people\b", re.IGNORECASE)


def _saying_it(memory, understood):
    """How to say one specific piece of news to the people it concerns."""
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    if _TALKS_OVER.search(line):
        return ("Say it once, plainly, and not in the moment it is happening: \"Can I finish this "
                "one? You jump in and I lose the thread.\" Name what they do rather than what they "
                "are - one line, no list of past times - and give them the benefit of the doubt "
                "once, because most people who talk over you are excited or nervous rather than "
                "rude. Then keep a short version for the moment itself, a hand up and \"hang on, "
                "let me finish this bit\", since that is the only place the habit can change. If "
                "it carries on after you have said it plainly, say it plainly a second time and "
                "say how it lands; that is not nagging, it is the second half of the same "
                "sentence.")
    if _MOVING_OUT.search(line):
        return ("Give them the plan, not a request for permission: \"I've found a flat and I'm "
                "moving out on the 14th - I wanted you to hear it from me first.\" Then let them "
                "react without defending it, and come back to the practical bits - how often you "
                "will visit, what you need - once the first conversation has cooled.")
    if _MOVING_AWAY.search(line):
        return ("Tell the people you will miss before the ones who will hear it second hand, and "
                "give them a date: \"I'm moving to Bristol in March - I didn't want you to find "
                "out from someone else.\" Then say what you want to keep going, a call every "
                "couple of weeks or a visit in the summer, so the news comes with a plan rather "
                "than a goodbye.")
    if _BABY.search(line):
        return ("Tell them in person or on a call rather than in a message, and lead with the news: "
                "\"I'm pregnant - it's early, and I wanted you to know.\" Then say what you want "
                "from them now, help or time before anyone else is told; that one sentence saves "
                "the guessing.")
    if _RAISE_SMOKE.search(line) or _RAISE_HOUSE.search(line):
        # The other person's habit in your own home - smoke, noise, the party that ran late - is
        # asked for as one thing, with when and what instead. Without this branch the row caught
        # "how do i tell my friend to stop smoking in my house" and stood down, and the smoke-smell
        # cleaning card answered it: how to air a room, which is the answer to the wrong question.
        # The example is the habit in the line: a noise complaint asked for plainly is "the music
        # was still going at half one", not smoke through the wall.
        # The example is the thing in the line: the animal, the children or the smoke, else a
        # late party. A cat coming into their garden is not a party, and "their party was too
        # loud" is not smoke through the wall.
        example = (_raise_example(line, _RAISE_ASK_SUBJECTS)
                   or '"the music was still going at half one - could we call it midnight next time?"')
        return ("Ask for the one thing, name when it happens and say what you want instead, once "
                "and in private: " + example + " Not the whole list and not in the moment it is "
                "annoying you, and leave them room to say why it is hard; a habit that is asked "
                "for plainly usually bends a little, where a rule handed down does not.")
    if _MESS.search(line):
        return ("Ask for the one job rather than the whole mess, and say when: \"Could you do the "
                "washing up tonight? I did it the last four nights and it is stacking up.\" Name "
                "the thing, the reason and the deadline in one breath - a general complaint about "
                "the flat gets an apology and no change.")
    if _SHARED_HOUSE.search(line) and (_MONEY.search(line) or _SHARE_MONEY.search(line)):
        return ("Ask once, with the amount and the date, and leave the history out of it: \"The "
                "broadband comes to 32 a month and your half is 16 - could you send it by "
                "Friday?\" A plain ask reads as fair; hinting over the washing up reads as a "
                "buildup.")
    # The household-bills script is for the people you share a home with. "how do i bring up
    # money with my parents" is a loan between family, and it was sent "the broadband comes to 32
    # a month and your half is 16". A parent is the other side of a different question.
    if _PARENT_MONEY.search(line):
        return None
    if _MONEY.search(line) and _HOUSEHOLD_MONEY.search(line):
        return ("Pick a time that is not the moment a bill lands, and put the numbers side by side "
                "rather than asking for a verdict: what comes in, what goes out, and what each of "
                "you wants to be able to afford. Open with a question - \"how do you feel about "
                "the way we split things?\" - and leave one decision for next time.")
    # A line that says it is news - "how do i break the news to my team" - gets the one flat
    # sentence. Anything else the row caught stands down rather than offering a news script:
    # "how do i say sorry to my wife" and "how do i say i love you to my dad" are an apology and a
    # declaration, and `WORDING_LINES` already says to give the gist and offers to draft it, which
    # is the more useful answer to both.
    if not _SAID_IT_IS_NEWS.search(line):
        return None
    return ("Say it in one flat sentence, then stop: the news, the reason if there is one, and what "
            "you want from them. The wait for the perfect moment is usually longer and worse than "
            "the conversation itself.")


def _thanks_has(understood, words):
    """Whether the line named one of these words or phrases."""
    typed = {str(word).lower() for word in (understood.get("words") or ())}
    clean = (understood.get("clean") or understood.get("text") or "").lower()
    for word in words:
        if " " in word:
            if word in clean:
                return True
        elif word in typed:
            return True
    return False


def thanks_note(memory, understood):
    """A thank-you note about the thing this line names, in two or three lines.

    Public because the language domain answers "how do i write a thank you note" with it too:
    that entry used to carry one example, and the example was always the same afternoon with
    some twins, so a note to a teacher or a nurse came back about a cake.
    """
    if _thanks_has(understood, THANKS_FLOWERS):
        return ("Say where the flowers are and what they have done for the room: \"Thank you for "
                "the flowers - they are on the kitchen table and the whole week looks better.\" "
                "Two or three lines, say when you will see them next, and stop.")
    if _thanks_has(understood, THANKS_GIFT):
        return ("Name the thing and what you are doing with it, rather than thanking them for it: "
                "\"Thank you for the cafetiere - it is on my desk and I use it every morning.\" "
                "Two or three lines, say when you will see them next, and stop; a present does not "
                "need a page.")
    if _thanks_has(understood, THANKS_STAY):
        return ("Pick the one thing they did that you noticed - the spare bed, the early start, the "
                "extra trip to the station - and say what it saved you: \"Thank you for having me "
                "for the weekend - the lift on Sunday saved me the whole morning.\" Then say when "
                "you will have them back, if you mean it.")
    if _thanks_has(understood, THANKS_MEAL):
        return ("Name the thing they did and what it changed for you, then stop: \"Thank you for "
                "the meal on Saturday - I came home full and happy.\" One detail from the evening "
                "that only you would know beats a paragraph of adjectives, and anything you are "
                "actually going to do, say when.")
    if _thanks_has(understood, THANKS_LIFT):
        return ("Name the trip and what it saved you: \"Thank you for the lift to the station on "
                "Friday - it saved me an hour and a soaking.\" Then one line about what it meant "
                "to you, and stop.")
    if _thanks_has(understood, THANKS_FAVOUR):
        return ("Name the job they did and what it saved you, then stop: \"Thank you for looking "
                "after the cat while we were away - coming back to a happy animal was the whole "
                "holiday.\" One line about what it meant to you beats a paragraph, and say what "
                "you will do in return if you mean it.")
    if _thanks_has(understood, THANKS_PERSON):
        return ("Say what they did and what it was worth to you: \"Thank you for the time you gave "
                "me over the summer - I still use the list you wrote.\" One sentence of detail, "
                "one of what it meant, then stop; people keep the short ones.")
    return THANKS_ANY


def _inflections(word):
    """The forms of a table word people actually type: "separately" and "separates" ask the same
    question as "separate", and the matcher does not make them from the base word."""
    forms = {word}
    if " " not in word and len(word) > 3:
        forms.update({word + "ly", word + "s", word + "es", word + "ing", word + "ed"})
        if word.endswith("e"):
            forms.update({word[:-1] + "ing", word[:-1] + "ed", word[:-1] + "ly"})
    return forms


# The correct spelling of every word in the table is what a "how do you spell X" line contains, and
# the misspellings are what somebody typing in a hurry contains. Both have to be in the key, with
# the forms they take, because "how do you spell it: separately" names the word and nothing else.
# The right spellings take the forms people write ("separately", "addresses"); the misspellings
# are keyed exactly as typed and get no inflections, because the invented ones ("adresss",
# "adreses") look like a second family of neighbours and blunt the slip repair.
_SPELLING_WORDS = tuple(sorted({form for right, slips, _tip in SPELLINGS
                                for word in (right,) + slips
                                for form in (_inflections(word) if word == right else (word,))}))
_SPELLING_SLIPS = tuple(slip for _right, slips, _tip in SPELLINGS for slip in slips)


# The misspellings are key words too, because a line like "how do i spell definately" names the word
# in the only spelling its writer has. They are registered here as misspellings, so the slip reader
# keeps reading them as the right word everywhere else in the knowledge base: a word listed here
# must not stop being a slip somewhere else.
_SPELLING_ENTRY_IDS = ("spelling-tricky-word", "spelling-pick-one")
for _slip in _SPELLING_SLIPS:
    SLIPS.setdefault(_slip, set()).update(_SPELLING_ENTRY_IDS)


# Every form of every word, mapped to the tip for its word, so the reply is one dictionary lookup
# however the word arrives in the line.
_SPELLING_TIPS = {form: tip for right, slips, tip in SPELLINGS
                  for word in (right,) + slips for form in _inflections(word)}


def _spelling(memory, understood):
    """Why the word this line asks about is spelled the way it is."""
    clean = (understood.get("clean") or "").lower()
    for word in clean.replace("?", " ").replace(",", " ").replace(":", " ").split():
        tip = _SPELLING_TIPS.get(word.strip("."))
        if tip:
            return tip
    # The two-word forms ("your welcome", "loose weight") have to be looked for as phrases.
    for phrase, tip in _SPELLING_TIPS.items():
        if " " in phrase and phrase in clean:
            return tip
    return None


# A memory question comes first: "what did i say about the birthday?" is the store's, and a card
# entry that answered it would talk over the memory instead of recalling it.
SAID = ("what did i say", "what did we say", "did i say", "did i tell", "you said",
        "i said", "own words", "i told you")
# Ways of asking for the words, as opposed to naming the occasion. A bare "say" is not one of
# them: "what did i say about the dog" has a "say" in it and belongs to the memory.
SAY = ("what do i say", "what should i say", "what to say", "say to", "say at")
# a death is a condolence, not a card: the generic message and good-news entries were taking
# "sorry for your loss, i don't know what to say" and "my friend's dad just passed away"
MOURNING = ("died", "dies", "dying", "death", "dead", "passed away", "passed on", "loss",
            "lost my", "funeral", "burial", "cremation", "bereavement", "grief", "grieving",
            "condolence", "condolences", "sympathy", "widow", "terminal", "cancer")


# Taking a message is not writing one. "i need to leave a message", "who should i leave a message
# with" and "should i leave a message on his answerphone" all arrive with a "message" in them and a
# "leaving", so the card and resignation entries answered them by handing over a letter to sign.
# These are the words that mean a phone, and they belong in those entries' avoid lists.
ON_THE_PHONE = ("answerphone", "answer machine", "answering machine", "voicemail", "voice mail",
                "to leave a message", "leave a message on", "left a message on", "take a message",
                "took a message", "who should i leave", "can i leave a message", "missed call",
                "ring back", "call back",
                "on the phone", "by phone", "phone call", "phonecall", "him a message",
                "her a message", "them a message", "message on his", "message on her",
                "message on the")
# --- the eulogy: a writing job, and the one speech nobody drafts twice ----------------
# "write me a eulogy for my mum" used to get the sympathy line, which is kind and useless: the
# person is at a desk with a page due, not telling the bot their mother died. The writing is the
# ask here, and the comfort is one clause at the front of it.
_EULOGY_LENGTH = ("how long", "length", "words", "word count", "minutes", "too long", "short")
_EULOGY_START = ("how do i start", "how to start", "start", "opening", "open", "begin", "first line",
                 "example", "examples", "template", "give me", "ideas", "what do i say")


def _eulogy(memory, understood):
    """The structure, the length and the opening line, depending on what was asked."""
    clean = ((understood or {}).get("clean") or "").lower()
    has = lambda *wanted: any(shape in clean for shape in wanted)
    if has(*_EULOGY_LENGTH):
        return ("A eulogy runs about three to five minutes, so 500 to 750 words read slowly - time "
                "it out loud once, because reading to a room is slower than reading to yourself. "
                "Shorter and warm beats long and solemn: two minutes with one real story in it "
                "lands better than ten minutes of a life in order, and nobody has ever wished a "
                "eulogy had listed more jobs.")
    if has(*_EULOGY_START):
        return ("Start with a plain, specific fact about them, not a summary: \"Dad was born in "
                "Leeds and never once chose a different chippy.\" Then one story that only your "
                "family could tell, with a detail in it - what they said, what they were wearing, "
                "the thing they did with their hands. Close on what they gave you, in one sentence, "
                "and step back; the last line does not have to be poetry, it has to be theirs.")
    return ("Write it in four short parts: who they were in a sentence, one story with a real "
            "detail in it, one thing they gave you, and a last line to the room. Aim for 500 to 750 "
            "words - three to five minutes out loud - and read it from paper rather than memory. "
            "Say the funny thing if it was funny, because a laugh at a funeral is a relief and not "
            "a mistake, and put the plainest, truest sentence you have near the end where it will "
            "be heard.")



FOLLOW_UP_THANKS = ("Send a short thank-you the same day: \"Thank you for the conversation "
                      "today — I'm even keener on the role after hearing about the new system. "
                      "Happy to answer anything else.\"")
FOLLOW_UP_CHASE = ("Chase once, a week after you applied: two lines, say you are still interested "
                   "and one thing you would bring to the job, and ask if they need anything else "
                   "from you. Then leave it - ring only if the advert gave a date and it has "
                   "passed. Keep applying elsewhere in the meantime.")
INTERVIEW_WORDS = ("interview", "interviews", "interviewed", "panel", "met them", "met the team",
                   "after the interview", "thank you note", "thank-you", "thank you letter",
                   "spoke to them", "spoke to the manager")
CHASE_WORDS = ("chase", "chasing", "chased", "follow up", "following up", "follows up",
               "followed up", "follow-up", "heard",
               "heard back", "heard nothing", "no reply", "nothing back", "no answer", "waiting",
               "not heard", "still waiting", "when should i")


def _said(said, word):
    return re.search(r"\b" + re.escape(word) + r"\b", said) is not None


# A line that asks how long to wait is asking about the timing, and both sentences below open on
# what to write. The wait comes first for those lines, because it is the question they asked -
# "a week after the interview, then one email" - and only then what the email says.
WHEN_WORDS = ("how long", "how many days", "how many day", "how many weeks", "how many week",
              "how soon", "how much longer", "when should i", "when do i", "days should i wait",
              "weeks should i wait", "how long should i wait",
              # "should i wait a week before following up" is the same ask without a how
              "should i wait", "should i leave it")
_TRADES = ("builder", "builders", "plumber", "plumbers", "electrician", "electricians",
           "roofer", "roofers", "decorator", "decorators", "painter", "painters",
           "plasterer", "plasterers", "tiler", "tilers", "joiner", "carpenter", "gardener",
           "landscaper", "handyman", "contractor", "tradesman", "tradesperson", "workman",
           "mechanic", "garage", "fitter", "installer")
# The same ask, for a line with no job in it at all: "how many days should i wait before
# following up" is the commonest way to ask, and it named nothing the job entry knew, so it got a
# shrug. A trade or a company is not this entry: "how many days should i wait before following up
# with the builder" and "i need to chase up the plumber" are not job applications.
FOLLOW_UP_ASK = ("how long", "how many days", "how many day", "how many weeks", "how many week",
                 "how soon", "how much longer", "when should i", "when do i", "when to",
                 "what is the right time", "what's the right time", "after a week", "a week after",
                 "left it a week", "leave it", "how many days before")
NOT_A_JOB = _TRADES + (
    "council", "landlord", "letting agent", "bank", "refund", "parcel", "delivery", "order",
    "insurance", "warranty", "broadband", "energy", "supplier", "dentist", "doctor", "surgery",
    "hospital", "school", "nursery", "vet", "garage", "neighbour",
    # "when should i follow up on a complaint" is not a job application either
    "complaint", "complaints", "complaining", "claim", "claims", "compensation")
# A timing ask after an interview is still a timing ask, and the chase above names an application
# the person has already been to see. So it gets its own wait: a week after the interview, one
# note, and then leave it.
FOLLOW_UP_AFTER_INTERVIEW = ("Give it a week after the interview: one short note that thanks them "
                             "for the time, gives one reason you want the job, and asks plainly "
                             "for a timescale. Then leave it - ring only if they gave you a date "
                             "that has passed.")
FOLLOW_UP_WHEN = ("Give it a week: a week from the day you sent it, or a week after the date "
                  "they gave you, long enough that they have news and short enough that you are "
                  "still live. Then one short message - what you are following up, when you sent "
                  "it, and a plain ask for a timescale - and after that leave it with them rather "
                  "than chase again.")


def _follow_up_general(memory, understood):
    """A line that asks how long to wait before following up, with nothing named in it at all."""
    return FOLLOW_UP_WHEN

EARLY_WORDS = ("leave early", "leaving early", "finish early", "finishing early",
               "an hour early", "half day", "early on friday", "early tomorrow", "go early",
               "leave at", "leaving at", "dip out", "knock off early", "leave a bit early",
               "leave work early", "out early")
TIME_OFF_SCRIPT = ("Ask early, name the dates and say who covers: \"Could I take 12–16 May off? "
                   "I've arranged cover with Priya and nothing is due that week.\" One question, "
                   "one answer, and put it in writing.")
EARLY_SCRIPT = ("Give the time and the cover, not the whole story: \"Hi Sam, is it OK if I leave "
                "at 3 today? I've moved the 4pm call to Priya and I'll pick the rest up in the "
                "morning.\" Ask the day before when you can, keep it to two lines, and if it is "
                "more than a one-off ask for a change of hours instead of asking again each week.")


# A "can I" line is owed a yes before the script: "can i leave early on friday" opened with
# "Yes, if..." and is answered, where the "how do i ask" shape is the script alone.
TIME_OFF_SCRIPT_YES = ("Yes, if you ask early and name the dates: \"Could I take 12-16 May off? "
                       "I've arranged cover with Priya and nothing is due that week.\" One "
                       "question, one answer, and put it in writing.")
EARLY_SCRIPT_YES = ("Yes - give the time and who covers it rather than the whole story: \"Hi Sam, "
                    "is it OK if I leave early on Friday? I've moved the 4pm call to Priya and I'll "
                    "pick the rest up on Monday.\" Say it the day before if you can, and keep it "
                    "to two lines.")
# the shapes that ask permission rather than for the wording
YES_WORDS = ("can i", "can we", "could i", "may i", "am i allowed", "is it ok", "is it okay",
             "is it fine", "would it be ok", "would it be okay", "do you think i can",
             "should i ask")


# A week that is already theirs is not a request for it: "booked a week off work in june" was
# given the "Could I take 12-16 May off?" script. The tense is the whole difference, so this is
# read off the line as it was typed rather than written into the avoid list - an avoid word is
# stemmed, and "booked a week off" in that list also stood the row down on "i need to book a
# week off in june", which is exactly the ask it is for.
_ALREADY_HAD = ("booked", "approved", "confirmed", "in the diary", "granted",
                "got the time off", "got the week off", "got my holiday", "have the time off")

# ...and neither is a line that simply says when the time is. "taking next week off work" and
# "i have next week off work" state it; the leave plan in work.py is what answers those, and
# this row is for the ask. The ask words are what tell the two apart.
_HAS_THE_TIME = ("taking next week off", "taking the week off", "off work next week",
                 "off next week", "next week off", "im off", "i'm off", "i am off",
                 "off work from", "off work for", "off next month", "off all week")
# ...and the away-or-home question is not a request for the time either: "i have a week off and
# want to go somewhere" and "should i go away or stay at home for my week off" are asking where
# the week goes, and this row's script is for getting it in the first place.
_AWAY_OR_HOME = ("go somewhere", "going somewhere", "go away", "going away", "get away",
                 "stay at home", "staying at home", "at home or away", "away or at home",
                 "somewhere warm", "a trip", "trip with")

# ...and the week said as something to fill is not a request for it either: "a week off with no
# plans" and "how do i use a week off well" are both questions about the week the person has.
_USE_THE_WEEK = ("no plans", "nothing planned", "how do i use", "how do i plan", "how to plan",
                 "how should i spend", "how do i spend", "use a week off", "use my week off",
                 "use the week off", "use the time off", "spend a week off", "spend my week off",
                 "spend the week off", "plan a week off", "plan my week off", "plan the week off",
                 "a week off well", "what to do with", "make the most of", "sort my",
                 # and a week off named after the thing given up is that thing's question, not a
                 # request for leave: "i want a week off the booze", "...off sugar", "...off my
                 # phone" were all handed "Could I take 12-16 May off?"
                 "week off the booze", "week off booze", "week off the drink", "week off drink",
                 "week off wine", "week off alcohol", "week off the alcohol", "week off sugar",
                 "week off dairy", "week off meat", "week off caffeine", "week off takeaways",
                 "week off vaping", "week off smoking", "week off social media", "week off chocolate",
                 "week off crisps", "week off my phone", "week off the phone", "week off sweets",
                 "week off carbs", "week off bread", "week off cheese", "week off gluten",
                 )

# A month, or a count of weeks, is a week already booked: "i have two weeks off in july", "i have
# a week off in may", "i have three weeks off in the summer" all got the request script, because
# the plan rows stand down on the month and this row was next in line. None of them asks for the
# time, so a month or a count only counts when the line also asks for it.
# The frame a line is in when it is trying to get the time: it asks, asks how to ask, or it says
# it wants or needs the time and names the verb that gets it. A wish with nothing behind it
# ("i want a week off to myself") is not this, and the plan rows answer it.
_ASKING_FRAME = ("ask", "asking", "asked", "request", "requesting", "book", "booking", "booked",
                 "put in for", "entitled", "entitlement", "can i", "can we", "could i", "may i",
                 "am i allowed", "is it ok", "is it okay", "allowed to", "permission",
                 "want to take", "want to book", "want to request", "wanted to take",
                 "need to take", "need to book", "need to request", "hope to take", "planning to take",
                 "how do i", "how should i", "how would i", "how to get", "how to take",
                 "what do i say", "what should i say", "who do i ask", "how much notice",
                 "how many days", "take a day off", "take a week off", "take some time off",
                 "take time off", "take it off", "take the day off", "take the week off",
                 # the plain ways of saying what you need, which carry no "how do i" at all
                 "need a", "need some", "need time", "need leave", "want some", "want a day off",
                 "want the day off", "want time off", "like a day off",
                 "like a week off", "like some time off", "id like", "i'd like", "would like a",
                 "get a day off", "get a week off", "get time off", "get the day off",
                 "annual leave", "leave request", "request leave", "book leave", "holiday form",
                 "leave form", "holiday request", "date of leave")

_MONTHS_NAMED = ("january", "february", "march", "april", "may", "june", "july", "august",
                 "september", "october", "november", "december", "next month", "this month",
                 "end of the month", "month")
_HOW_LONG = ("two weeks", "three weeks", "four weeks", "five weeks", "ten days", "a fortnight",
             "fortnight off", "week off in", "weeks off in")
_ASKS_TO_HAVE = ("can i", "can we", "could i", "may i", "am i allowed", "is it ok", "is it okay",
                 "want to", "need to", "wish to", "hope to", "planning to", "like to",
                 "ask", "asking", "request", "book", "take", "put in for", "claim",
                 "entitled", "how many days", "what do i say", "how do i get time off",
                 "need a", "need some", "need time", "need leave", "want a day off")

_ASK_VERBS = ("can i", "can we", "could i", "may i", "am i allowed", "is it ok", "is it okay",
              "how do i ask", "how do i take", "how do i book", "how do i request",
              "how do i get time off", "how do i go about", "how do you ask", "how to ask",
              "should i ask", "want to", "need to", "need a", "ask",
              "asking", "book", "booking", "request", "entitled", "what do i say",
              "how should i")


def _asks_for_the_time(understood):
    """True when the line is a request for time off, not a statement that the time is theirs.

    The reply function can stand down, but the row the table picks should be the row that
    answers, or a test that reads the table sees the wrong one. Both checks live here.
    """
    said = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    if any(phrase in said for phrase in _ALREADY_HAD):
        return False
    if any(phrase in said for phrase in _AWAY_OR_HOME):
        return False
    if any(phrase in said for phrase in _USE_THE_WEEK):
        return False
    if ((any(word in said for word in _MONTHS_NAMED) or any(word in said for word in _HOW_LONG))
            and not any(word in said for word in _ASKS_TO_HAVE)):
        return False
    if (any(phrase in said for phrase in _HAS_THE_TIME)
            and not any(phrase in said for phrase in _ASKING_FRAME)):
        # "id like a day off next week" names the time off next week and is still an ask
        return False
    # and the row needs the asking frame, not the wish. "i want a week off the booze" and "i want
    # a week off to myself" were both given the script for asking a manager for leave, because
    # this row was the default for any line with a week off in it. What the row answers is a
    # person trying to get the time, so the line has to be trying.
    return any(phrase in said for phrase in _ASKING_FRAME)


def _time_off(memory, understood):
    """A day off wants the dates; an afternoon off wants the time and who covers it."""
    said = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    early = any(" " + phrase + " " in said or phrase in said for phrase in EARLY_WORDS)
    asking = any(word in said for word in YES_WORDS)
    if early:
        return EARLY_SCRIPT_YES if asking else EARLY_SCRIPT
    return TIME_OFF_SCRIPT_YES if asking else TIME_OFF_SCRIPT


def _follow_up(memory, understood):
    """The thank-you note if there was an interview, the chase if there has not been one yet."""
    said = (understood.get("norm_text") or understood.get("text") or "")
    thanked = any(_said(said, word) for word in INTERVIEW_WORDS)
    chasing = any(_said(said, word) for word in CHASE_WORDS)
    if any(_said(said, word) for word in WHEN_WORDS):
        # a timing question gets the wait and the email, in that order, whichever email it is,
        # and the wait for a thank-you note is a week after the interview rather than after the
        # application.
        return FOLLOW_UP_AFTER_INTERVIEW if thanked else FOLLOW_UP_CHASE
    if thanked:
        return " ".join((FOLLOW_UP_THANKS, FOLLOW_UP_CHASE))
    if chasing:
        return " ".join((FOLLOW_UP_CHASE, FOLLOW_UP_THANKS))
    return " ".join((FOLLOW_UP_THANKS, FOLLOW_UP_CHASE))


# The shapes that say the barking dog is the person's own: the owner and the noise in one breath
# ("my dog barks at their dog", "our dog keeps barking at next door's dog"). A bare "my dog"
# would also stand down the letter on "my neighbour's dog keeps barking at my dog", where it is
# the neighbour's dog doing the barking - the two words above are what tell them apart.
MY_DOG_NOISE = tuple(
    "%s %s" % (owner, verb)
    for owner in ("my dog", "our dog", "my dogs", "our dogs", "my puppy", "our puppy")
    for verb in ("barks", "keeps barking", "is barking", "barking",
                 "wont stop barking", "will not stop barking")
)


# --- what to say when something bad has happened to somebody else -------------------------------
# The ways people ask for the words. A bare "say" is not one, and neither is "what did i say":
# "what did i say to her" is the memory store's question.
COMFORT_SAY = ("what do i say", "what should i say", "what can i say", "what to say",
               "what do i tell", "what should i tell", "what can i tell", "what to tell",
               "how do i comfort", "how do i console", "comfort", "console", "comforting",
               "cheer up", "cheering up", "how do i cheer", "be there for", "how do i support",
               "how do i help them", "how do i help her", "how do i help him",
               "how do i help my", "what can i do for")
# What happened to them, and the first sentence for it. The rule under each is the same, but a
# friend who has just been sacked does not want the answer for a friend who is crying, so the
# situation picks the reply rather than one general line doing all of them.
COMFORT = (
    (("crying", "cries", "cried", "tears", "tearful", "sobbing", "sobs", "broke down",
      "in bits"),
     "Say the plain thing and then stop talking: \"I'm here, and you don't have to explain.\" A "
     "hand on the arm and the silence do more than any advice; when they are ready, ask what they "
     "need today - company, a walk, or to be left alone."),
    (("dumped", "breakup", "broke up", "split up", "divorce", "divorced", "divorcing",
      "separated", "walked out", "left her", "left him", "left them", "his ex", "her ex"),
     "Say it plainly and skip the silver lining: \"that's rotten, and I'm sorry.\" Let them tell "
     "it more than once without running the ex down, and offer one concrete thing this week - a "
     "drink, a lift, dinner at yours - rather than \"let me know if you need anything\"."),
    (("sacked", "fired", "redundant", "unemployed", "lost her job", "lost his job",
      "lost their job"),
     "Lead with them, not with the fix: \"that's a horrible way to start the week - I'm sorry.\" "
     "Don't send job links in the first conversation; ask what they want to do today, and offer "
     "one practical thing later, like reading over the CV when they ask."),
    (("failed", "flunked", "rejected", "gutted", "didnt get", "didnt pass", "turned down",
      "missed out"),
     "\"That's gutting, and you were right to expect it\" beats \"something better will come "
     "along\". Let them be disappointed first; then ask whether they want to talk it through or "
     "be distracted, and do whichever they say."),
    (("ill", "sick", "unwell", "poorly", "hospital", "operation", "diagnosed", "diagnosis",
      "cancer", "chemo", "treatment", "recovering"),
     "Keep it simple and specific: \"I'm thinking of you - is a visit welcome, or would you rather "
     "I text?\" Don't ask about the prognosis or offer a cure, and offer a lift, a meal or an "
     "afternoon with the kids instead of \"anything I can do\"."),
    (("homesick", "lonely", "missing home", "moved away", "knows nobody", "on her own",
      "on his own", "on their own"),
     "Say it out loud: \"that sounds lonely, especially in the evenings.\" Ask about one specific "
     "person or place at home, and put a fixed call in the diary - a Tuesday phone call beats "
     "\"we must catch up\"."),
)
# Being told off, in the words people actually use. "My boss had a go at me" and "my manager told
# me off" are one event, and only the second was keyed anywhere: every "had a go at me" line was a
# sympathy line or an echo, while "my boss shouted at me" got the answer. The list is here rather
# than in one module because who did it picks the answer (a boss is work, a parent is family), and
# every key that owns a person carries these words.
# Every form is the receiving end - "had a go at me", never "had a go at" - because "i had a go at
# my brother on the phone" is the person doing it, which is a different question with different
# advice.
# How nerves show in the body, which is how most people say them: "i feel sick before job
# interviews", "i get butterflies", "my stomach turns before an exam". Shared because the work
# and the study rows are the same question about different events, and one list keeps them the
# same words. The row that uses it still needs its own event, so "i feel sick" alone stays a
# stomach line and is answered by the health rows.
NERVES_BODY = ("feel sick", "feeling sick", "felt sick", "am sick with nerves",
               "sick with nerves", "ill with nerves", "feel ill", "queasy", "butterflies",
               "stomach turns", "stomach turning", "stomach churns", "stomach churning",
               "churning stomach", "tummy turns", "gut churning", "cant eat", "can't eat",
               "cannot eat", "dry mouth", "shaky hands", "hands shake", "shaking hands",
               "shake all over", "shaking all over", "legs like jelly", "heart racing",
               "heart races", "heart pounding", "pounding heart", "sweaty palms", "clammy",
               "cant breathe", "can't breathe", "need the loo", "running to the loo",
               "bright red", "go red", "blush")

# The person's own sign, said back to them. A body-first opening that names "shaky hands" to
# somebody whose line said "feel sick" is telling them about a symptom they did not mention, and
# STYLE asks for their words. The first pair that matches their line is the one to use, and when
# none does the opening names no sign at all ("That feeling before an exam ...").
SIGNS = (
    (("feel sick", "feeling sick", "felt sick", "am sick", "sick with nerves", "ill with nerves",
      "feel ill", "feeling ill", "nauseous", "nausea"), "Feeling sick"),
    (("queasy", "stomach turns", "stomach turning", "stomach churns", "stomach churning",
      "churning stomach", "tummy turns", "gut churning"), "That churning stomach"),
    (("butterflies",), "Butterflies"),
    (("cant eat", "can't eat", "cannot eat"), "Not being able to eat"),
    (("dry mouth",), "A dry mouth"),
    (("shaky hands", "hands shake", "shaking hands"), "Shaky hands"),
    (("shake all over", "shaking all over", "shaking", "shaky"), "That shaking"),
    (("legs like jelly", "jelly legs", "weak at the knees"), "Legs like jelly"),
    (("heart racing", "heart races", "heart pounding", "pounding heart", "heart thumping"),
     "A racing heart"),
    (("sweaty palms", "sweaty hands", "clammy"), "Clammy hands"),
    (("cant breathe", "can't breathe", "hard to breathe"), "That tight chest"),
    (("need the loo", "running to the loo"), "Needing the loo"),
    (("bright red", "go red", "going red", "blush", "blushing"), "Going red"),
)


def sign_said(text):
    """The sign the person actually named, in their words, or None when they named none."""
    said = str(text or "").lower()
    for phrases, label in SIGNS:
        if any(phrase in said for phrase in phrases):
            return label
    return None


# The labels above that take "are" rather than "is": a sign said back has to read like English.
_SIGN_PLURAL = frozenset(("Shaky hands", "Butterflies", "Legs like jelly", "Clammy hands"))


def nerves_opening(text, situation, tail):
    """`Shaky hands before an interview are ...` in the person's own words.

    `situation` is "before an exam"; `tail` starts with the predicate ("adrenaline, not a bug").
    A line that names no sign gets "That feeling", which is true of every one of them.
    """
    label = sign_said(text)
    if label is None:
        return "That feeling " + situation + " is " + tail
    return label + " " + situation + (" are " if label in _SIGN_PLURAL else " is ") + tail


TOLD_OFF = ("had a go at me", "had a go at us", "had a right go", "a go at me about",
            "had a go at me about", "told me off", "told us off", "tells me off",
            "telling me off", "got told off", "been told off", "got a telling off",
            "a telling off", "bollocked", "bollocking", "got a bollocking",
            "gave me an earful", "got an earful", "laid into me", "went off at me",
            "read me the riot act", "had a pop at me", "gave me a mouthful", "balled me out")

COMFORT_SITUATIONS = tuple(word for words, _reply in COMFORT for word in words)
# The line names the bad time but not which kind of bad time: the general one is still a real
# answer, and the rule under it is what helps.
COMFORT_UNNAMED = ("upset", "struggling", "hard time", "rough time", "going through",
                   "devastated", "not coping", "mental health", "dumped", "sacked")
COMFORT_LAST = ("Say it plainly and don't rush to fix it: \"that's really hard, and I'm glad you "
                "told me.\" Ask what they need today - company, quiet, or a distraction - and "
                "offer one concrete thing, like a walk or dinner on Thursday, rather than \"let me "
                "know if you need anything\".")
# The same rule when the line names no event at all, so the reply cannot pretend something
# specific happened: it teaches the shape of the sentence instead.
# What the other person did, rather than what happened to them. "What do i say" is the plain
# comfort row's ask, and the row keys no situation at all, so a line whose trouble is somebody's
# behaviour toward the asker was answered with advice for bad news: "my friend keeps cancelling
# what do i say" and "my friend is always late what do i say" were both told to "name it in one
# line (\"that sounds really hard\")", when neither person has had any bad news - the words they
# need are the pattern question and the lateness answer. The words below are the behaviour, never
# the person (a friend who is ill or grieving keeps the comfort row), and each one already has a
# row of its own or none, so standing aside here costs nothing.
A_BEHAVIOUR_TOWARD_THE_ASKER = (
    "cancel", "cancels", "cancelling", "cancelled", "canceled", "bailed", "bails",
    "no show", "a no show", "flaked", "flaky",
    # a clock, not a death: "my friend was late" is the lateness answer
    "late", "lateness", "always late", "late again",
    # the quiet friend and the one who leaves you out of things
    "never replies", "does not reply", "doesnt reply", "won't reply", "wont reply",
    "never texts", "doesnt text", "doesn't text", "leaves me on read",
    "ignores me", "ignored me", "ignoring me", "stopped texting", "gone quiet",
    "left me out", "leaves me out", "leaving me out", "didnt invite", "didn't invite",
    "not invited", "no invite",
    # things done to the asker rather than suffered by them
    "owes me", "owes", "borrowed", "borrows", "teased", "teasing", "teases",
    "made a joke", "joke about", "jokes about", "joking about", "took the mick",
    "rude", "put me down", "puts me down", "putting me down", "snide", "nasty about me",
    "talks about me", "behind my back",
)

COMFORT_PLAIN = ("You don't need the perfect words: name it in one line (\"that sounds really "
                 "hard\"), say you are glad they told you, and offer one concrete thing - a walk, "
                 "dinner on Thursday - rather than \"let me know if you need anything\". Then ask "
                 "what they need today, company or quiet or a distraction, and do that instead of "
                 "fixing it.")


def _comfort(memory, understood):
    """The first sentence for the bad thing the line names, and the same rule under it."""
    said = " " + ((understood or {}).get("clean") or "").lower() + " "
    # A follow-up says "what do i say to her" and leaves out what happened: the line before it
    # said the friend was made redundant, so that is the thing to answer. Reading it here is
    # what keeps the entry off lines where nobody has had a bad time at all.
    leans = (understood or {}).get("leans_on")
    earlier = ""
    if isinstance(leans, dict) and isinstance(leans.get("words"), list):
        earlier = " " + " ".join(w for w in leans["words"] if isinstance(w, str)).lower() + " "
    for words, reply in COMFORT:
        for word in words:
            if " " in word:
                if " " + word + " " in said or " " + word + " " in earlier:
                    return reply
            elif re.search(r"\b" + re.escape(word) + r"\b", said + earlier):
                return reply
    # Nothing in the line, and nothing in the line it follows, says what happened: "what should
    # i say to her" is not this entry's question until there is a bad time to answer, and the
    # third part of the key (who the words are for) is what let such a line reach it. Declining
    # hands the turn back to whichever row can still answer it honestly.
    if not any(re.search(r"\b" + re.escape(word) + r"\b", said + earlier)
               for word in COMFORT_SITUATIONS + COMFORT_UNNAMED):
        return None
    return COMFORT_LAST



# A card that tells somebody how to do a thing is for the person about to do it, and the same
# words in the past are the person telling you they have done it. "i quit my job and its great" is
# news and a warm word; "how do i quit my job" is the template. The asking forms are the question
# words, the helping verbs and the writing nouns, which is what every phrasing of the ask has in
# common.
_BEING_WRITTEN = re.compile(
    r"\b(?:how|what|whats|what's|should|could|can|would|do i|help|idea|ideas|need to|needs to|"
    r"want to|wants to|about to|write|writing|wrote|draft|drafting|word|words|"
    r"say|saying|tell|telling|template|example|examples|letter|email|e-mail|message|advice|"
    r"tips?)\b", re.I)


def _the_notice_is_being_written(understood):
    """Whether the notice is being written now, rather than reported after the fact."""
    reading = understood or {}
    return bool(_BEING_WRITTEN.search(str(reading.get("clean") or "")))


ENTRIES = [
    # The card in the envelope, one entry per occasion. People write "what do I put in a
    # leaving card" and "birthday message for my colleague", not "how do I write a card", so
    # each entry is keyed on the occasion plus the writing words, and asks for one of them: a
    # line that only names the occasion ("when is my birthday", "how do i make a card") is not
    # a wording question and belongs to whatever answers it today.
    entry("card-writing", (("card", "cards", "message", "messages", "note", "wishes",
                            "lines", "write", "writing") + SAY,
                           ("leaving", "leaving do", "last day", "goodbye", "farewell",
                            "moving on", "emigrating", "retiring", "retirement")),
          ("Keep it to two lines and one real detail: \"Working with you made the Monday mornings "
           "survivable, and I still owe you for the time you covered for me.\" Say what you will "
           "actually miss, then a plain good luck. If you want it funny, keep the joke to something "
           "the two of you share and never about their job or their leaving, and sign your full name "
           "for anyone who is not in your team."),
          bias=1,
          avoid=SAID + ON_THE_PHONE + (
              # the same posting question asked about a leaving card
              "abroad", "overseas", "australia", "canada", "usa", "america", "spain", "france",
              "italy", "ireland", "new zealand", "europe", "dubai", "first class",
              "second class", "envelope", "envelopes"),
          ask=("card", "cards", "message", "messages", "note", "wishes", "write", "writing",
               "lines", "what do i write", "what to write", "what should i write") + SAY),
    entry("card-birthday", (("card", "cards", "message", "messages", "note", "wishes",
                             "wish", "greeting", "greetings", "write", "writing",
                             # the card is written, not the party planned: "how do i write a
                             # birthday card" was answered with how many people to invite
                             "birthday card", "birthday cards", "card for", "cards for",
                             # "birthday message" and "bday card" are the same card said the
                             # other way, and each keeps its line off the party row
                             "birthday message", "birthday messages", "birthday wishes",
                             "bday card") + SAY,
                            ("birthday", "bday", "30th", "40th", "50th", "60th", "70th",
                             "18th", "21st", "65th")),
          _card_birthday,
          # making one is a craft question, and buying one is a shopping one, with its own
          # answers; this entry is the words that go inside
          avoid=SAID + ("make", "makes", "making", "craft", "draw", "drawing", "design", "print",
                        "cut out", "card shop", "buy", "buying", "bought", "shop", "shops",
                        "cheap", "price", "where can i",
                        # a card that has to be posted is a postage question, not a wording one:
                        # "how do i send a birthday card to australia" was told what to write
                        "abroad", "overseas", "australia", "canada", "usa", "america", "spain",
                        "france", "italy", "ireland", "new zealand", "europe", "dubai",
                        "first class", "second class", "envelope", "envelopes", ),
          bias=1,
          # A card with an age on it is a birthday card even when the line leaves the word out:
          # "my nan is 90 next month, what do i write in her card" was answered with the general
          # two-line note, which is a card for anybody and says nothing about the 90.
          shape=(_names_an_age,),
          ask=("card", "cards", "message", "messages", "note", "wishes", "wish", "write",
               "writing", "greeting", "greetings", "what do i write", "what to write") + SAY),
    entry("card-congrats", (("card", "cards", "message", "messages", "note", "wishes",
                              "congratulations", "congrats", "write", "writing") + SAY,
                             ("new job", "new role", "promotion", "graduation", "graduated",
                              "passed", "results", "driving test", "first day")),
          ("Name the thing they did and one thing you noticed about them doing it: \"All those "
           "late nights paid off - well done, Dr Chen.\" Skip the advice and the joke, and if the "
           "card is from a group, sign the group rather than one person's name."),
          # "leaving for a new job" is still a leaving card, and the wedding and the removals are
          # their own answers: this one is the good news card
          avoid=SAID + MOURNING + ("leaving", "leaving do", "last day", "goodbye", "farewell", "moving on",
                        "emigrating", "retiring", "retirement", "removals", "van", "packing",
                        "deposit", "mortgage", "house price", "buying a house", "moved out",
                        "get married", "speech", "toast", "venue", "guest list"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "wishes", "congratulations",
               "congrats", "write", "writing", "what do i write", "what to write") + SAY),
    entry("card-new-home", (("card", "cards", "message", "messages", "note", "wishes",
                              "congratulations", "congrats", "write", "writing") + SAY,
                             ("new home", "new house", "new flat", "moved in", "moving in",
                              "first house")),
          ("Wish them well in the place, not the paperwork: \"Congratulations - may the boiler "
           "behave and the neighbours be quiet.\" A small thing for the house instead of a bottle "
           "of wine is a good present, and if you are visiting, ask before you bring anything big."),
          # the removals, the deposit and the packing are their own questions
          avoid=SAID + ("removals", "removal", "van", "packing", "pack", "unpacking", "deposit",
                        "mortgage", "house price", "buying a house", "moved out", "rent"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "wishes", "congratulations",
               "congrats", "write", "writing", "what do i write", "what to write") + SAY),
    # A card with no occasion named in the line: "what do i write in a card for my neighbour".
    # Every occasion entry above scores higher on its own words, so this only catches the rest.
    entry("card-something", (("card", "cards", "note", "message", "messages", "write",
                              "writing") + SAY,
                             ("what do i write", "what to write", "what should i write",
                              "what do i say", "what to say", "blank", "stuck", "no idea")),
          _card_plain,
          bias=-1,
          # "what should i write to ask for a refund" carries "write" and nothing about a card,
          # and this entry was answering it with a two-line note: the message asking for money
          # back is ask-for-refund's, so a claim for something owed stands this down.
          avoid=MOURNING + ("refund", "refunds", "complaint", "complain", "complaining",
                            "compensation", "replacement", "money back", "owed", "owes me",
                            # A reference is written, but it is not a card: "what should i
                            # write in a reference" is the job reference, and on main it was
                            # answered "Thinking of you both - hope the year is a good one."
                            "reference", "references", "referee", "referees", "testimonial",
                            "recommendation", "cv", "job application", "employer", "interview",
                            # "how much cash do you put in a card" asks for an amount, and the
                            # words for the card are not it
                            "how much", "how many", "cash", "money", "quid", "pounds",
                            "dollars", "euros"),
          # The card noun is the entry: "what do i say to her" after a bad week at work, or
          # "what do i say to my boss", asks for words in a conversation, not in a card.
          # The write forms stay, so "what to write in a note" still reaches this.
          # An age on the card says which occasion it is, and this row's own reply is a card for
          # anybody: "my nan is 90 next month, what do i write in her card" was answered with
          # "Thinking of you both", because this row matched more of the asking words than the
          # birthday row did. A number that is an age is not this row's question.
          guard=lambda reading: not _names_an_age(
              (reading or {}).get("clean") or (reading or {}).get("text")),
          # The ask itself is a shape, not a list of phrases: "what shall i write in a card for
          # my mate who hates a fuss" carries no word from the phrases above and fell to the
          # search hedge.
          shape=(_asks_for_the_words,),
          ask=("card", "cards", "note", "notes", "message", "messages", "write", "writing",
               "blank")),
    entry("card-anniversary", (("card", "cards", "message", "messages", "note", "wishes",
                                "write", "writing") + SAY,
                               ("anniversary", "years together", "married for", "wedding day")),
          ("Name the year, then one thing you are glad about: \"Ten years, and you still make me "
           "laugh at the worst jokes.\" A line about a specific time beats anything about "
           "forever; if it is someone else's anniversary, keep it to the pair and skip the advice."),
          avoid=SAID + ("buy", "buying", "present", "presents", "gift", "gifts", "restaurant",
                        "book a table", "meal out", "hotel"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "wishes", "write", "writing",
               "what do i write", "what to write") + SAY),
    entry("card-valentines", (("card", "cards", "message", "messages", "note", "wishes",
                               "write", "writing", "love") + SAY,
                              ("valentine", "valentines", "valentines day", "14 february",
                               "romantic", "romance", "girlfriend", "boyfriend")),
          ("One true thing you would say out loud, then stop: \"I like who I am when I am with "
           "you.\" Long lists and borrowed lines read as effort, not feeling, so keep it to two "
           "lines and sign it properly unless it is going to a secret valentine."),
          avoid=SAID + ("buy", "buying", "present", "presents", "gift", "gifts", "flowers",
                        "restaurant", "book a table", "meal out", "hotel"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "wishes", "write", "writing",
               "love", "what do i write", "what to write") + SAY),
    entry("card-parents-day", (("card", "cards", "message", "messages", "note", "wishes",
                                "write", "writing") + SAY,
                               ("mothers day", "mothering sunday", "fathers day",
                                "mums day", "dads day")),
          ("One thing she or he actually did for you, named plainly: \"Thanks for every school "
           "run in the rain.\" A memory does more than \"best mum ever\", and if you are not "
           "close, a warm two lines and both your names is enough - the present is a separate job."),
          # the present is its own answer, and so is a birthday card
          avoid=SAID + ("buy", "buying", "bought", "present", "presents", "gift", "gifts",
                        "ideas", "what should i get", "cheap", "price", "restaurant",
                        "book a table", "birthday"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "wishes", "write", "writing",
               "what do i write", "what to write") + SAY),
    entry("card-new-baby", (("card", "cards", "message", "messages", "text", "texts", "note",
                              "wishes", "congratulations", "congrats", "congratulate",
                              "congratulating", "write", "writing") + SAY,
                             ("new baby", "newborn", "baby", "babies", "birth", "born",
                              # a bare "arrived" is a parcel, a bus and a cold takeaway as well
                              # as a baby, and with a saying phrase in the first group that was
                              # enough on its own: "the takeaway arrived cold what do i say" got
                              # the congratulations text
                              "has arrived", "have arrived", "just arrived", "arrived yesterday",
                              "arrived last night", "arrived this morning",
                              "having a baby", "had a baby", "baby on the way")),
          ("Name the baby if you know the name, wish the parents some sleep, and skip the jokes "
           "about their life being over: \"Congratulations - she is beautiful. Wishing all three "
           "of you a slow, sleepy first month.\" If it is a second baby, say something about the "
           "older one too; nobody else will."),
          # the present is a shopping question, and so is what to take round
          avoid=SAID + ("buy", "buying", "bought", "shop", "shops", "present", "presents", "gift",
                        "gifts", "make", "making", "craft", "take", "taking", "bring",
                        "visiting"),
          bias=1,
          ask=("card", "cards", "message", "messages", "text", "texts", "note", "wishes",
               "congratulations", "congrats", "congratulate", "congratulating", "write",
               "writing", "what do i write", "what to write") + SAY),
    entry("card-get-well", (("card", "cards", "message", "messages", "note", "write",
                             "writing", "wishes") + SAY,
                            ("get well", "get better", "speedy recovery", "poorly", "operation",
                             "surgery", "in hospital", "recovering", "recovery",
                             "illness"),
                            # the ward is part of the occasion: a "get well message" for someone
                            # in hospital is wording, while what to take them is a gift question
                            ("hospital", "in hospital", "ward", "operation", "surgery")),
          ("Say the one thing you want for them and keep it light: \"Thinking of you - take the "
           "time you need and we will save you a seat.\" No advice, no story about your own "
           "operation, and do not say \"let me know if you need anything\": offer something "
           "specific instead, like a lift home or dinner on Thursday."),
          # an operation is somebody else's, but "how long to recover from surgery" is a health
          # question and has its own answer
          # "how do i get better at writing" is somebody improving a skill, not wishing anyone
          # well: "get better" and "writing" are enough for this entry on their own, and the
          # line was answered with a get well card. "better at" and "improve" are the tell.
          # "how do i write to my mp about a hospital appointment" is a letter, not a card:
          # the bodies people write to by post are named here too.
          avoid=SAID + ("how long", "how soon", "recover from", "back to work", "pain",
                        "take", "taking", "bring", "brings", "give them", "visit", "visiting",
                        "better at", "get better at", "improve", "improving", "improvement",
                        "mp", "msp", "councillor", "council", "landlord", "letting agent",
                        "insurer", "insurance", "employer", "appeal", "ombudsman", "dwp"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "write", "writing",
               "wishes", "what do i write", "what to write") + SAY),
    # A wedding card is the couple, not the person who cooked the dinner, so it is not the
    # thank-you note; and a christening card is the baby, not what to wear to the church.
    entry("card-wedding", (("card", "cards", "message", "messages", "note", "write", "writing",
                            "wishes") + SAY,
                           ("wedding", "married", "marriage", "engagement", "engaged",
                            "the big day")),
          ("Two lines, one about them as a pair: \"So glad you two found each other - the way you "
           "laugh at the same things is the whole thing.\" Put both their names on the envelope, "
           "and if you are not going, say so warmly in one line and leave it there."),
          # the speech, the venue and the seating plan all have their own answers; and "married"
          # on its own is somebody else's marriage trouble
          avoid=SAID + ("speech", "toast", "venue", "seating", "table plan", "guest list",
                        "first dance", "my husband", "my wife", "get married", "propose"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "write", "writing",
               "wishes", "what do i write", "what to write") + SAY),
    entry("card-christening", (("card", "cards", "message", "messages", "note", "write",
                                "writing", "wishes") + SAY,
                               ("christening", "baptism", "baptised", "naming ceremony",
                                "godparent", "godparents")),
          ("Name the baby and one wish: \"Welcome to the world, Ada - may you be as loved as you "
           "were today.\" Sign both your names, and if you gave a present, the card is not the "
           "place to describe it."),
          # what to wear to the church is its own answer, and so is the present
          avoid=SAID + ("wear", "wearing", "dress", "outfit", "suit", "what should i wear",
                        "christening gown", "present", "presents", "gift", "gifts"),
          bias=1,
          ask=("card", "cards", "message", "messages", "note", "write", "writing",
               "wishes", "what do i write", "what to write") + SAY),
    entry("card-christmas", (("card", "cards", "message", "messages", "note", "write",
                              "writing", "wishes", "greetings") + SAY,
                             ("christmas", "xmas", "festive", "new year", "season's")),
          ("Two lines is plenty unless it is family: \"Merry Christmas - hope the year has been "
           "kind to you and the next one is better.\" Add a specific thing you remember from the "
           "year for anyone close (\"still laughing about the tent\"), and for a neighbour or a "
           "colleague a plain wish and both your names is the whole job."),
          bias=1,
          # making a card is a craft question and buying one is a shopping one
          avoid=SAID + ("make", "makes", "making", "craft", "draw", "design", "print",
                        "cut out", "buy", "buying", "bought", "shop", "shops", "cheap",
                        "price", "where can i"),
          ask=("card", "cards", "message", "messages", "note", "write", "writing",
               "wishes", "greetings", "what do i write", "what to write") + SAY),
    entry("landlord-broken-boiler", ("landlord", "broken", "repair", ("boiler", "heating", "email", "message")),
          the_fault(
              "Keep it short, dated and specific, and ask for a date: \"Hi — I reported the "
              "{fault} on [date] and nothing has been done. Please let me know when an engineer "
              "can come; I'm home after 5pm on weekdays. Thanks, [name].\" Follow it up in "
              "writing if nothing happens in 48 hours. Anything unsafe, the heating, the hot water "
              "and any appliance that came with the flat are the landlord's job, so if they ignore "
              "you ask the council's environmental health team to step in, keep the messages, and "
              "keep paying the rent: withholding it usually puts you in the wrong.",
              "Keep it short, dated and specific, and ask for a date. Say what is wrong, when it "
              "started and when you are in, and follow it up in writing if nothing happens in 48 "
              "hours. Anything unsafe, the heating, the hot water and any appliance that came with "
              "the flat are the landlord's job, so if they ignore you ask the council's "
              "environmental health team to step in, keep the messages, and keep paying the rent: "
              "withholding it usually puts you in the wrong."),
          # "my washing machine is broken, is it worth repairing" is not the landlord's boiler
          avoid=("deposit", "moved out", "moving out", "washing machine", "dishwasher", "fridge",
                 "freezer", "oven", "tumble dryer", "vacuum", "hoover", "car", "laptop", "phone"),
          # "my boiler is broken" asks what to do about the boiler, not how to write to a landlord,
          # and it was getting the letter because `boiler` and `broken` are both in this key. The
          # letter is the answer only when the line names the landlord or the writing.
          ask=("landlord", "landlady", "letting agent", "letting agency", "housing", "council",
               "letter", "email", "message", "text", "note", "write", "writing", "word", "wording",
               "complain", "complaint", "rights", "refusing", "refuses", "ignoring", "honour")),
    entry("neighbour-dangerous-dog",
          (("neighbours", "neighbour", "neighbors", "neighbor", "next door", "next-door",
            "nextdoors", "upstairs", "downstairs", "flat above"),
           ("dog", "dogs", "puppy")),
          # The noise letter tells you to name the time and the nights, which is the wrong advice
          # for a dog that goes for yours: nobody needs to negotiate a 11pm cut-off with a dog that
          # attacks. Same subject ("the neighbour's dog"), different problem, so its own letter.
          ("Keep your own dog out of its way while this is going on - walk a different way and do "
           "not try to introduce them through the fence. Write down each time it happens: the date, "
           "the time, what the dog did, and whether anyone was hurt. Report it to the council's dog "
           "warden with those details, since a dog out of control in a public place or in your "
           "garden is their job, and a dog that has injured a person or another animal is a police "
           "matter. If the owner is approachable, say it plainly once: \"your dog went for mine on "
           "Tuesday by the gate - can you put it on a lead there?\" If anyone is bitten, get medical "
           "help or a vet first and report it afterwards, and keep every message you send."),
          # The aggression words are the ask, so a line that only names the neighbour and the dog
          # ("my dog is scared of the neighbour") stays with the shy-dog entry. The bias is there
          # because the shy-dog entry also names the dog, the neighbour and the children, so
          # "my neighbours dog growls at my kids" reaches both and this is the one to answer.
          ask=("aggressive", "aggression", "attacks", "attacking", "attacked", "bites", "bitten",
               "bit my", "bit me", "growls", "growling", "growled", "snarls", "snarling",
               "snapped at", "lunges", "lunging", "went for", "goes for", "dangerous", "vicious",
               "savage", "out of control", "terrified of it", "scared of it", "chased", "chasing"),
          bias=2,
          # a bite that already happened to the person is first aid, and a line about their own
          # dog's behaviour is not about the neighbour at all
          avoid=("i got bitten", "i was bitten", "i have been bitten", "bit someone",
                 "my dog bit", "my puppy bit", "my dog is aggressive", "my dog attacks",
                 "my dog snapped", "what should i do if a dog bites")),
    entry("neighbour-noise",
          # A dog nobody in the line owns is still this letter: "someone else's dog keeps
          # barking" named no neighbour and reached the shy-dog answer, though the advice is the
          # same one, and "their dog keeps barking" reached a shrug. A dog down the road is the
          # same case as a dog through the wall - you cannot train it.
          (("neighbours", "neighbour", "neighbors", "neighbor", "next door", "upstairs",
            "downstairs", "flat above", "someones dog", "someone else's dog", "someone elses dog",
            "someone's dog", "a dog down the road", "dog down the road", "their dog"),
           ("music", "banging", "barking", "bark", "dog", "party",
            "message", "talk",
            # people say "will not shut up" far more often than they say "barks all night", and
            # "next door's dog wont shut up" was answered with the swollen-door card
            "wont shut up", "won't shut up", "shut up", "never shuts up", "keeps barking",
            # building work is the commonest daytime nuisance and it named no word this row
            # knew: "my neighbour is doing building work at 7am" was echoed back
            "drill", "drilling", "hammering", "sawing", "building work", "builders",
            "renovation", "renovating", "extension") + NOISE_WORDS +
            ("keeps me awake", "wakes me up", "all night", "all day")),
          # The example named music only, so a barking dog ("my neighbour's dog barks all night")
          # was told to ask for the music to be turned down. The wording now gives the shape and
          # names what the entry's own key words cover, not one of them.
          ("Talk to them once, at a calm time, and say when it happened and what you need: \"this "
           "has gone on after 11pm most nights this week, and I'm up at six - can it stop by then?\" "
           "Name the time and the nights, not the person. If it carries on, keep a short log of dates "
           "and times and report it to the council's noise team, who can act on it without you having "
           "to confront anyone."),
          # "dog" is in the key because a barking dog is the common case, but "my dog is
          # scared of the neighbour" is a shy-dog question, not noise: the complaint words are
          # the ask, so a line that only names the neighbour and the dog does not land here.
          ask=("music", "banging", "barking", "barks", "bark",
               "howling", "howls", "all night", "at night", "every night", "all hours",
               "cant sleep", "can't sleep", "awake", "wake", "woken", "party",
               "keep me up", "keeps me up", "shut up", "goes mad", "yapping", "whining",
               "screaming", "disturbing",
               "drill", "drilling", "hammering", "sawing", "building work", "builders",
               "renovation", "renovating", "extension") + NOISE_WORDS,
          # The new dangerous-dog entry above names the same four words (the neighbour, next door,
          # the dog), and a key word two entries use stops counting as rare, which quietly dropped
          # this letter below the shy-dog answer for "the dog next door barks at my children".
          # The nudge puts it back where it was, and on that line it also fixes a miss.
          bias=1,
          # a party they enjoyed is not a complaint about noise
          avoid=("fun", "enjoyed", "enjoy", "enjoying", "loved", "love", "lovely", "great",
                 "nice", "thanks", "wedding", "birthday", "sad", "upset", "anxious", "worried",
                 "lonely") + MY_DOG_NOISE),
    entry("ask-for-refund", (("complain", "complaint", "refund", "refunds", "money back",
                              "complained about"),
                             "product",
                             # the first part is the one the line has to say, so the refund and
                             # the complaint both have to be in it: "what should i write to ask
                             # for a refund" says neither "complain" nor a card word, and the
                             # card row answered it with a two-line note to a friend
                             ("service", "back", "message", "money", "broke", "broken", "faulty",
                             "write", "writing", "email", "words", "word", "draft", "letter",
                             "say", "saying", "ask", "asking", "phrasing",
                             # "how do i write a letter asking for a refund" tied with the
                             # cake-piping row on "refund" and "letter", and the tie went to
                             # cooking: the asking shape is what makes it this row's line.
                             "asking for", "letter asking", "asking for a refund",
                             "asking for my money back", "letter of complaint",
                             "email asking", "write asking")),
          ("State the order, the problem and what you want, in that order: \"I ordered a lamp on 3 May "
           "(order 12345). It arrived cracked. Please send a replacement or refund the £40.\" Give a "
           "deadline of 14 days and mention your rights only if they say no."),
          # This is the complaint *message*. A refund on something bought in a shop is a rights
          # question and money's `refund` entry has the 30 days and the repair-or-replace in it, so
          # a line that names the shop, the receipt or the entitlement is not this one.
          # It is the wording, not the rights: "can i get a refund for broken headphones" wants
          # the rule, so it answers only when the line asks what to write or say.
          ask=("write", "writing", "email", "message", "say", "saying", "words", "word",
               "ask", "asking", "how do i ask",
               "draft", "letter", "text", "reply", "phrasing", "complain", "complaining",
               "complaint"),
          avoid=("shop", "shops", "in store", "store i", "receipt", "entitled", "consumer rights",
                 "my rights", "30 days", "thirty days",
                 "can i get", "am i entitled", "are they allowed", "do i have to",
                 "is it legal", "should they", "how long",
                 # The complaint message is for a thing you bought. A travel ticket, a flight, a
                 # hotel and a show each have their own rules and their own row, and "how do i
                 # ask for a refund on a train ticket" reached this one on "ask" and got the
                 # cracked-lamp letter: the ask words are the same, the answer is not.
                 "train", "trains", "rail", "railway", "railcard", "delay repay", "flight",
                 "flights", "airline", "plane", "hotel", "booking", "concert", "gig",
                 "festival", "theatre", "theater", "cinema", "match", "festival ticket",
                 "train ticket", "bus ticket", "coach ticket", "season ticket", "ferry",
                 "ticket", "tickets", "holiday", "package holiday", "cruise", "travel agent",
                 "tour operator", "cottage", "villa", "campsite",
                 # And it is for a thing you bought. "someone rang saying im due a tax refund" and
                 # "hmrc emailed me about a tax refund" are a message that arrived, not a letter
                 # to write, and both got the cracked-lamp template; money.tax-refund-scam
                 # answers them. A benefit, a rebate and a council tax refund are the same shape.
                 "tax", "tax refund", "tax rebate", "rebate", "hmrc", "p800",
                 "benefit", "benefits", "universal credit", "council tax", "pension",
                 "text saying", "email saying", "emailed saying", "rang saying", "called saying",
                 "phoned saying", "message saying", "telling me", "saying im", "saying i am")),
    # The words for turning down a meeting, and only a meeting: "decline" and "politely" were
    # key words on their own, so "how do i politely decline a hen do" was answered "I can't make
    # Tuesday - can we do Thursday" before the refusal row could hear it. The subject now has to
    # be in the line as well.
    entry("decline-a-meeting",
          (("meeting", "meetings", "zoom", "call with", "stand-up", "standup"),
           ("decline", "declining", "cancel", "cancelling", "excuse", "politely",
            "get out of", "skip", "reschedule")),
          ("Be brief and offer a substitute: \"I can't make Tuesday — can we do Thursday, or shall I "
           "send a note with my points?\" A short reason and an alternative reads as organised rather "
           "than rude.")),
    entry("apology-message",
          (("sorry", "apologise", "apologize", "apologise", "apology"),
           ("friend", "sister", "brother", "mum", "dad", "partner", "said", "hurt", "upset",
            "row", "argument", "fight", "write", "message", "properly",
            # The person you apologise to is most often the one you live with, and "how do i say
            # sorry to my wife" had nobody in the second key part to match, so it fell through to
            # the composer's wording card and got "what happened, what you want and by when" -
            # a request, not an apology. The asking verbs are here for the same reason: "how do
            # i say sorry" on its own is the apology, not a message to draft.
            "wife", "husband", "girlfriend", "boyfriend", "partner", "fiance", "fiancee",
            "flatmate", "housemate", "neighbour", "neighbor", "son", "daughter", "mother",
            "father", "colleague", "say", "tell", "words", "wording")),
          ("Name what you did, say why it was wrong, and don't add a but: \"I said I'd call and I "
           "didn't, and that left you waiting. I'm sorry.\" Then say what you will do differently, in "
           "one sentence."),
          ask=("sorry", "apologise", "apologize", "apology")),
    # What you say when the apology comes to *you*. Three rows were answering this and none of
    # them is about it: the apology-message row below is the one you write yourself, the
    # somebody-owes row is for an apology you have not been given, and the hedge was the last
    # word. "how do i accept an apology" and "how do i reply to an apology" reached nothing at
    # all, and "someone said sorry to me" was told how to apologise.
    entry("accept-an-apology",
          (("sorry", "apology", "apologise", "apologize", "apologies", "apologises",
            "apologizes", "apologising", "apologizing", "apologized", "apologised"),
           ("to me", "said sorry", "says sorry", "said it", "someone said", "someone apologised",
            "someone apologizes", "someone apologises", "reply", "respond", "answer", "accept",
            "accepting", "forgive", "forgiving", "what do i say", "what should i say",
            "how do i reply", "how do i respond", "they said sorry", "he said sorry",
            "she said sorry", "apologised to me", "apologized to me", "apologises to me",
            "apologizes to me", "said sorry to me", "says sorry to me")),
          ("Take it plainly and say so: \"Thanks for saying that - it means a lot.\" Then, if "
           "something is still needed, name one thing in a sentence (\"a text next time you are "
           "running late would help\") and leave it there. You do not have to forgive on the spot; "
           "accepting the apology is enough for today."),
          ask=("sorry", "apology", "apologise", "apologize", "say", "saying", "what", "how",
               "reply", "respond", "accept", "forgive", "back", "after", "when"),
          # The person's own apology, an apology they are owed rather than given, a habit of
          # apologising and grief are other rows: this one is only the sorry that arrives.
          avoid=("i said sorry", "i already said sorry", "i apologise", "i apologize",
                 "i have apologised", "how do i say sorry", "how to say sorry",
                 "should i apologise", "should i say sorry", "wont apologise", "wont say sorry",
                 "never apologises", "never says sorry", "owes me an apology",
                 "owe me an apology", "refuses to apologise", "refuses to say sorry",
                 "stop saying sorry", "sorry for your loss", "condolence", "died", "funeral",
                 "passed away", "grief",
                 # drafting my own apology is the apology-message row above: "how do i write a
                 # text to say sorry" reached the sorry that arrives, which is the other way
                 "how do i write", "how to write", "write a text", "write a message",
                 "text to say", "draft", "drafting", "wording", "how do i say", "how to say",
                 "should i send"),
          bias=2),

    entry("apology-somebody-owes",
          (("wont apologise", "wont say sorry", "wont apologise to me", "never apologises",
            "never apologize", "never apologise", "never says sorry", "never say sorry",
            "doesnt apologise", "doesnt say sorry", "not apologising", "refuses to apologise",
            "refuses to say sorry", "owes me an apology", "owe me an apology",
            "owes me a sorry", "apologise to me", "apologize to me",
            # "should apologise to me" and not a bare "should apologise": "i should apologise to
            # my flatmate" is the person's own apology and was reaching this row.
            "should apologise to me", "should say sorry to me", "should have apologised",
            "get him to apologise", "get her to apologise", "get them to apologise",
            "wont admit he", "wont admit she", "never admits", "never admits he is wrong"),
           ("my husband", "my wife", "my partner", "my mum", "my dad", "my friend", "my boss",
            "my sister", "my brother", "my boyfriend", "my girlfriend", "my son", "my daughter",
            "my mother", "my father", "he", "she", "they", "him", "her", "them", "his",
            "himself", "herself", "how", "what", "should", "can", "why", "never")),
          ("You cannot make someone sorry, so ask for the repair rather than the words: say what "
           "you needed and what you will do now - \"I needed you to say it mattered, and I am not "
           "going to keep bringing it up.\" Ask once, plainly, and let them decide; if it never "
           "comes, the useful question is what you want next, not how to get it out of them."),
          ask=("never", "wont", "doesnt", "owes", "owe", "owed", "should", "refuses", "to me",
               "how", "what", "why", "can"),
          # money.py's debt row keys "owes me" as well and took "she owes me an apology" on the
          # tie-break, which asked the person to offer a payment plan.
          bias=3,
          # the person's own apology, the habit of saying it too often, and grief are the rows
          # above: this one is a sorry somebody else owes you
          avoid=("died", "death", "funeral", "passed away", "sorry i", "im sorry", "my fault",
                 "stop saying sorry", "all the time", "too much", "so much", "i apologise",
                 "i apologize", "i said sorry", "i should say sorry",
                 # an apology that has been given is answered, not chased: "what do i say when
                 # someone apologises to me" was told how to ask for the repair, which is this
                 # row's answer to an apology that has *not* come
                 "what do i say", "what should i say", "what do i write", "reply", "respond",
                 "accept", "said sorry to me", "says sorry to me", "apologises to me",
                 "apologizes to me", "apologised to me", "apologized to me",
                 "when someone apologises", "when someone apologized", "when someone says sorry")),
    # The note-to-school entry below reads the school and the child but not the teacher, so the
    # letters that name only the school have a row of their own.
    entry("email-to-teacher", ("teacher", "childs", "school", ("email", "write", "message")),
          ("Put the child's name and class in the subject, say what you have noticed and what you "
           "would like: \"Sam (5B) has been anxious about maths homework — could we talk for ten "
           "minutes this week?\" Keep it to a few lines and ask for a specific next step."),
          # "should i keep my child off school with a cold" is the illness question, not the
           # wording of the note to school
           avoid=("with a cold", "a cold", "with flu", "a cough", "temperature", "chest infection",
                 # a thank-you to a teacher is a note of thanks, not a parent's letter about a
                 # child: "what do i write in a thank you card for a teacher" was getting the
                 # "put the child's name and class in the subject" answer
                 "thank you", "thankyou", "thank-you", "thanks",
                 "vomiting", "sickness bug", "chickenpox",
                 # keeping a child home, and how long to, is the exclusion-rules answer: the note
                 # is what you write once that question is settled
                 "off school", "home from school", "keep my child home", "well enough",
                 "should i keep", "keep him home", "keep her home", "keep them home",
                 "when can he", "when can she", "how long off",
                 # a child being bullied at school is a what-to-do question, and family.py's
                 # child-bullied answers it; the wording of a note is not the subject
                 "bullied", "bullying", "bullies", "picked on", "being picked on",
                 # a student writing to their own teacher is study.py's ask-teacher row: this
                 # one puts "the child's name and class" in the subject, which is a parent's
                 # letter and wrong advice for the person sitting in the class
                 "my teacher", "my lecturer", "my tutor", "my professor", "my form tutor",
                 # choosing which school is family.py's `choose-a-school` answer, made of
                 # visiting and comparing; the note is what you write once it is settled, and
                 # "how do i choose a school for my child" was getting this subject line
                 "choose a school", "choosing a school", "choose the school",
                 "which school", "what school", "schools to look at", "look at schools",
                 "visit schools", "school visits", "school open day", "compare schools",
                 "pick a school", "picking a school", "decide on a school",
                 "school for my child", "school for my son", "school for my daughter"),
          # This entry ties with the teaching-career row on a line that names both a school and a
          # teacher ("my son is being left out at school, what do I say to his teacher") and what
          # the person wants there is the wording of a note, not the route into the job.
          bias=2),
    # The note-to-school entry above insists on the first word of its key, "teacher", and a letter
    # about an absence names the school and never the teacher: "report my child absent from
    # school", "email the school about an absence" and "note for school about my child being ill"
    # all came back empty (the last one reached the keep-them-home illness advice). An absence note
    # is its own letter - name, class, the dates, the reason, and what you want marked authorised -
    # so it gets whole phrasings of its own. The second group is writing words only: "school" and
    # "teacher" are what this row and the career rows fight over, and a second entry naming them
    # makes them less rare for everyone, which cost the note its answer on "my son is being left
    # out at school, what do I say to his teacher" until this entry got its bias.
    entry("note-to-school-absence",
          (("report my child absent", "report an absence", "report the absence",
            "report my child off", "absent from school", "absence from school",
            "school absence", "school absences", "note for school", "note to school",
            "letter to school", "letter for school", "email the school", "email school about",
            "write to the school", "write to school about", "sick note", "school note",
            "note about my child", "letter about my child", "off school note"),
           ("report", "note", "letter", "absent", "absence", "absences", "written")),
          "Say the child's name and class, the dates they were off, and the reason in one line: "
          "\"Sam, 5B, off Thursday and Friday with a sickness bug - back on Monday.\" Ask them to "
          "mark it authorised, and offer a doctor's note or appointment card if they want one. "
          "Email the school office with the dates in the subject line; most schools want a call "
          "on the first morning as well as the note.",
          bias=2,
          # The school run is the journey and a uniform is cleaning.py's question, so a line
          # about either is not the letter: this row wants one of the writing words.
          ask=("note", "letter", "email", "write", "written", "absent", "absence", "absences",
               "sick note", "report"),
          avoid=("uniform", "uniforms", "blazer", "pinafore", "pe kit", "shoes", "socks",
                 "stain", "stains", "school run", "dropping off", "drop off",
                 "choose a school", "choosing a school", "which school", "school place",
                 "admissions", "ofsted", "catchment")),
    entry("asking-for-time-off",
          # "leave early on Friday" is the same ask as a day off, so it answers here too. The
          # second half takes the days people name ("can i have friday as a half day") and the
          # reasons they give ("leave early for a dentist appointment"), but still needs one of
          # them, so a bare "i have a dentist appointment at 3" is not treated as a request. A bare
          # "tomorrow" is not one of them either: "i'm nervous about a dentist appointment tomorrow"
          # is somebody dreading a filling, not asking for the day off.
          (("time off", "holiday", "holidays", "day off", "days off",
            # A week off is booked the same way and asked for in the same words: "how do i take a
            # week off work" reached the sick-note row and was told about a fit note after seven
            # days, and there was no script for the ask that every job needs.
            "week off", "weeks off", "week off work", "leave early", "leaving early",
            "finish early", "half day", "an hour early", "early on friday", "dentist", "doctor",
            "appointment", "friday off", "monday off", "tuesday off", "wednesday off",
            "thursday off", "tomorrow off"),
           ("boss", "request", "email", "book", "work", "ask", "asking", "leave", "leaving", "take",
            "can i", "could i", "off")),
          _time_off,
          # being too ill to go in is `calling-in-sick`'s line, not a holiday request: "should
          # i take tomorrow off sick" was getting the "Could I take 12-16 May off?" script
          # The request words, not the appointment: "how do i book a dentist appointment" is
          # how to get seen, and "i have a dentist appointment at 3" is not an ask at all, while
          # every real leave line carries one of these ("can i leave early for a dentist
          # appointment" passes on "early", "can i book friday off" on "off").
          ask=("time off", "day off", "days off", "boss", "work", "email", "early", "half day",
               "off"),
          # the exit row in friends.py also reads "leave" and "early": "i need to leave early
          # today" and "how do i ask my boss to leave early" were told how to close a chat
          # gracefully, so a line that names the leave itself is answered here first
          bias=2,
          avoid=("sick", "ill", "unwell", "poorly", "not well", "temperature", "fever", "flu",
                 "migraine", "headache", "vomiting", "throwing up",
                 # a week off with the children in it is asking what to do with them, not how to
                 # ask the boss: "i have a week off with my kids what should i do" was given the
                 # "ask early, name the dates" script.
                 "with the kids", "with my kids", "with my children", "with the children",
                 "kids off school", "school holidays", "half term",
                 # a week off is also the shape of other questions, and "should i" / "want to"
                 # are too common to tell them apart: "i have a week off work should i take
                 # another job" was given the leave script, and so was "i have a week off and i
                 # want to lose weight". The subject in the line stands this row down.
                 "another job", "new job", "second job", "quit", "quitting", "leave my job",
                 "lose weight", "lose a stone", "losing weight", "diet", "get fit", "gym",
                 # the allowance question is work.py's, whatever else is in the line
                 "entitled", "entitlement", "statutory", "pro rata", "pro-rata", "minimum",
                 "how many days holiday", "how much holiday", "how many holidays",
                 # "i keep putting off the dentist" is not a request for leave: borrow the bare "off"
                 # and "take" out of the second half and it is a holiday script for somebody avoiding a
                 # filling. Standing the entry down on the putting-off verbs is the narrower fix, because
                 # "off" is what those phrases and the leave phrases share.
                 "putting", "postponing", "procrastinating",
                 # Being rung on a day off is not a request for one: "my work keeps calling me on
                 # my day off" wants the boundary, and work.called-on-a-day-off has it.
                 "calls me", "calling me", "called me", "rings me", "rang me", "ring me",
                 "ringing me", "texts me", "texted me", "texting me", "messages me",
                 "phoned me", "phones me", "keeps calling", "keeps ringing", "keeps texting",
                 "contacts me", "expects me at work",
                 # a holiday you cannot afford yet is a money question: "should i pay off my card
                 # or save for a holiday" was answered with "Could I take 12-16 May off?"
                 # "afford" is not a money-only word: "i need time off because i cant afford
                 # childcare" is a leave request, and with "afford" in this list it fell through
                 # to the sick-note answer. The phrases above already carry the card lines.
                 # "card" is bare enough to take "can i have a day off to sort out my credit card",
                 # so the card is named instead.
                 "pay off", "paying off", "credit card", "card debt", "card payment", "debts",
                 "debt", "savings", "save up", "saving up", "or save", "overpay", "mortgage",
                 "interest",
                 # "i have 200 quid and a few days off where can i go" is not a request for
                 # the time, it is a question about where to spend it: the where-to-go answer
                 # (travel.where-no-place) holds the fares, and this row stood in front of it.
                 "where can i go", "where should i go", "where could i go", "where to go",
                 "where would you go", "where should we go", "where can we go",
                 "where could we go", "where would we go", "which country", "somewhere warm",
                 # a free block with a question about what to do in it is the plans lane's
                 # question, not the ask: "i have a week off and no idea what to do" and
                 # "i want to plan a trip with a week off" were both given the request script
                 # by the plan rows standing down in front of it.
                 "what should i do", "what can i do", "what to do", "any ideas", "any tips",
                 "no idea", "nothing planned", "nothing to do", "keep busy", "bored",
                 # and the week can be the setting for any other question, which no ask word
                 # tells apart: "i have a week off what should i cook" and "...should i save the
                 # money" were both given the "Could I take 12-16 May off?" script. The subject of
                 # the line is what decides, so the subjects are named.
                 "cook", "cooking", "bake", "baking", "meal", "meals", "dinner", "dinners",
                 "lunch", "lunches", "recipe", "recipes", "save", "saving", "savings",
                 "save up", "money", "budget", "cost", "afford", "quid", "pounds",
                 "broke", "skint", "hard up", "no money", "tight month", "on a budget",
                 # and a trip planned round the free block is a travel question:
                 "plan a trip", "planning a trip", "book a trip", "a trip", "trip with",
                 "going away", "go away for", "get away for", "a break away",
                 "book a holiday", "plan a holiday", "planning a holiday"),
                guard=_asks_for_the_time),
    entry("follow-up-email",
          (("chase", "chasing", "chased", "follow up", "followed up", "follow-up",
            "following up", "follows up", "chase up", "chasing up", "email",
            "emailed", "emailing", "note", "reply", "replies", "write", "writing", "message",
            "nudge"),
           ("interview", "interviews", "application", "applications", "applied", "recruiter",
            "hiring manager", "panel", "job offer", "about a job", "for a job", "the job",
            "vacancy", "role",
            # "how many days should i wait before following up" named no job at all, so the ask
            # could not be met and it got a shrug; the thing being followed up is enough.
            "following up", "follows up", "follow up", "chase up", "chasing up", "chasing")),
          # Two different emails live in this entry and the order of the sentences decided which
          # one a person got: "how do i chase a job application" was told to send a thank-you note
          # the same day, which is the step before the one they asked about.
          _follow_up,
          # A manager or a colleague who never answers is the at-work silence in work.py
          # (boss-silent), which says to ask twice in writing and then copy someone above.
          avoid=("never replies", "never reply", "never answers", "never answer", "never emails",
                 # a letter of application is the letter that asks for the job, not the note
                 # after the interview: work.py's cover-letter answers that one
                 "letter of application",
                 "wont reply", "won't reply", "wont answer", "doesnt reply", "doesn't reply",
                 "doesnt answer", "doesn't answer", "ignores my", "ignored my", "no reply",
                 "no response", "nothing back", "my manager", "my boss", "my employer",
                 "chased twice", "asked twice",
                 # "how do i write a cover letter for a job i really want" is the letter, not the
                 # email after the interview
                 "cover letter", "covering letter",
                 # "my results say i need a follow up" is a test result with another appointment
                 # on it, and this card took it: the phrase "follow up" is in both halves of the
                 # key, so it beats every row that says it once. A medical word at all is another
                 # card's line.
                 "results", "blood test", "bloods", "scan", "x-ray", "smear", "biopsy", "gp",
                 "doctor", "hospital", "surgery", "nurse", "test result", "appointment",
                 # a trade or a company is a different kind of wait: "how many days should i wait
                 # before following up with the builder" and "i need to chase up the plumber" are
                 # not job applications, and the wait for them is the job's not the trade's.
                 #
                 # A line that names the application has a better answer already: how long after
                 # applying to wait is the application entry's own rule (a week after the closing
                 # date, or two weeks after you applied), and it is more specific than the chase
                 # here. Those lines stay with it.
                 "after applying", "after i applied", "after you apply", "after my application",
                 "after sending my cv", "after sending my application",
                 "after sending the application", "after sending it",
                 "after the closing date", "after the closing date should") + NOT_A_JOB),
    entry("raise-a-problem-with-friend", ("friend", "upset", "hurt", ("problem", "bring", "tell")),
          # The example has to fit the problem the person actually has. It used to be only about
          # being left out of plans, so "how do I bring up the money I lent him without ruining the
          # friendship" was told to say "I felt left out when the plans changed". Two examples, one
          # for a debt and one for being left out, and the advice underneath is the same for both.
          _raise_problem,
          # a judgement about what they made or how they look has its own entry
          # (family.telling-a-friend-what-you-think), so both of these examples would be wrong
          # A problem that is not the speaker's own grievance is not this script: something
          # somebody else is doing to a third person ("should i tell my friend she is being
          # cheated on"), and telling a friend something about yourself ("should i tell my friend
          # i like her", "should i tell my friend about my depression").
          # Only the betrayal words stand aside, not "husband" and "wife": the partner is often
          # the subject of the grievance itself ("should i tell my friend her husband upset me"),
          # and this script is then the right answer to give. Those two words alone turned three
          # everyday lines into a shrug.
          avoid=("cooking", "cooks", "baking", "bakes", "food", "singing", "haircut", "outfit",
                 "writing", "drawing", "performance",
                 "cheat", "cheats", "cheated", "cheating", "affair", "affairs",
                 "like her", "like him", "like them", "fancy", "feelings", "a crush", "in love",
                 "depression", "depressed", "anxiety", "anxious", "mental health", "diagnosis",
                 "coming out", "gay", "lesbian", "trans",
                 # Declining an invitation is its own message (see tell-someone-you-cant-come): this
                 # row keys on "friend" and "tell", so a "how do i tell my friend i cant come" line
                 # landed here and was told to say "I lent you £200".
                 "cant come", "cant make it", "not coming", "cant be there", "cant go",
                 "wont be able to come", "have to cancel", "had to cancel", "cannot make it",
                 "wedding", "christening", "funeral", "engagement", "hen do", "stag do"),
          guard=_not_a_hurt_body),
    # Telling someone you cannot come is a small, common, hard message, and main had no row for it:
    # "how do i tell my friend i cant come to her wedding" was answered by raise-a-problem-with-
    # friend ("I lent you £200"), because that row keys on "friend" and "tell". The declining
    # words are in `ask`, so the row only fires when the not-coming is actually in the line.
    entry("tell-someone-you-cant-come",
          (("cant come", "cant make it", "not coming", "cant be there", "wont be able to come",
            "cant go", "have to cancel", "had to cancel", "pull out", "cannot make it"),
           ("wedding", "birthday", "christening", "party", "dinner", "christmas", "lunch",
            "visit", "meal", "funeral", "barbecue", "bbq", "engagement", "hen do", "stag do")),
          ("Say it early and plainly, give one reason and offer one thing instead: \"I'm so sorry, I "
           "can't make Saturday after all - I'm not well enough to travel. Can I take you both out "
           "once the dust settles?\" Short is kinder than detailed; a long excuse sounds like a "
           "choice, and telling them before they have paid for your plate is the whole kindness.",
           "Say it as soon as you know, name the reason in one line and say what you can still do: "
           "\"I can't be there on the day, but I'd love to come and see you the week after.\" Do not "
           "leave it until the last week, and do not offer a string of excuses - one reason and one "
           "alternative reads as true, several read as invented."),
          ask=("cant come", "cant make it", "not coming", "cant be there", "wont be able to come",
               "cant go", "have to cancel", "had to cancel", "pull out", "cannot make it"),
          # a debt or a grudge between friends is raise-a-problem-with-friend, and a job is a
          # resignation letter.
          avoid=("money", "lend", "lent", "debt", "borrow", "job", "resign", "quit")),
    # Saying a thing to the people who will have an opinion about it. Main answered these with the
    # thing itself: "how do i tell my parents im moving out" got the council-tax paper trail,
    # "how do i bring up money with my partner" got how to split the bills, "how do i tell my friend
    # im moving away" got the script for a friend who owes you money. The question is the
    # conversation, and the answer changes with the news, so the row reads the news rather than
    # offering one script for all of it.
    entry("how-to-tell-them",
          (("how do i tell", "how should i tell", "how to tell", "how do i break",
            # "how do i ask my neighbour to stop smoking in the garden" is the same question with
            # the asking named, and it reached the stop-smoking card: what to say to a neighbour
            # is this row, and the thing in the line is what it is about.
            "how do i ask", "how should i ask", "how can i ask", "how to ask",
            "break the news", "how do i say", "how do i bring it up", "how do i bring up",
            "bring it up with", "how do i raise it", "how do i talk to my", "talk to my",
            "how do i tell my", "telling my", "how do i announce",
            # the habit, named: "my friend keeps talking over me" was reaching the
            # keep-a-conversation-going tips, and "she interrupts me" the raise-a-problem
            # script about a debt
            "talks over me", "talking over me", "talk over me", "talks over my",
            "keeps talking over", "interrupts me", "interrupting me", "interrupts my",
            "keeps interrupting", "cuts me off", "keeps cutting me off", "butts in",
            "keeps butting in", "always butts in", "butting in on",
            "finishes my sentences",
            # the giving side of bad news. "how do i give someone bad news" is a person about to
            # do the telling, and the comfort words for somebody who has just been told ("say you
            # are glad they told you") are the wrong side of the conversation.
            "how do i give", "how to give", "how do i break it", "how to break it",
            # The words asked for by name rather than by the telling: "give me the words to say
            # to my boss" is this row's question, and without them the line went to the punt and
            # "the words to say to my boss about leaving early" to the break-clause letter for a
            # tenancy, because the only thing left to read was "leaving early".
            "words to say", "words to use", "words to tell", "give me the words",
            "help me word", "put it in words", "put this in words", "find the words",
            "what words", "which words"),
           ("parents", "parent", "mum", "dad", "mother", "father", "partner", "husband", "wife",
            "housemate", "housemates", "flatmate", "flatmates", "roommate", "family",
            "my friend", "my friends", "brother", "sister", "son", "daughter", "kids",
            "children", "my boss", "my team", "team", "staff", "colleagues", "everyone",
            # ... and the same question with nobody named: "tell someone", "tell somebody",
            # "give a friend the news" are the shapes people type when they do not name a person.
            "someone", "somebody", "person", "people", "friend", "friends",
            # ... and the people people live beside, who are asked rather than told. Not the
            # landlord: "landlord" is the word of the renting rows, and a second key that carries
            # it makes the word less of a sign inside this domain, which took the letter about the
            # heating to the arrears card. A landlord line has its own letter, and it is better.
            "neighbour", "neighbours", "neighbor", "neighbors", "my neighbour",
            "housemates", "flatmates", "roommates", "workmate", "workmates", "coworker",
            "co-worker", "boyfriend", "girlfriend", "fiance", "fiancee", "my ex", "ex partner",
            "nan", "nana", "grandma", "grandad", "granny", "grandparent", "in laws", "in-law",
            "stepson", "stepdaughter", "stepchildren")),
          _saying_it,
          # The lines that already have a better home: a place you cannot go is
          # tell-someone-you-cant-come, a resignation is the leaving letter, a death and a diagnosis
          # are their own answers, and a betrayal is not news you are sharing.
          # A habit that happens at work is the workplace row's: "my boss keeps interrupting me"
          # was answered "In Monday's meeting, when you cut across me, I lost the thread", which
          # is better than a friend script because it names the meeting.
          # the habit is the ask when it is named: "my mum keeps interrupting" has no telling
          # verb in it at all, and the row is still the right one for the line
          # "give"/"giving" are the telling verb said the other way round: "how do i give someone
          # bad news" is the same row, and the comfort words for somebody who has just been told
          # ("say you are glad they told you") are the wrong side of the conversation.
          ask=("tell", "say", "ask", "asking", "asks", "bring", "raise", "talk", "breaking",
               "announce", "telling", "give", "giving",
               "talks over me", "talking over me", "talk over me", "talks over my",
               "keeps talking over", "interrupts me", "interrupting me", "interrupts my",
               "keeps interrupting", "cuts me off", "keeps cutting me off", "butts in",
               "keeps butting in", "always butts in", "butting in on", "finishes my sentences"),
          avoid=("cant come", "cant make it", "not coming", "cannot make it", "have to cancel",
                 "wedding", "funeral", "hen do", "stag do",
                 "resign", "resigning", "leaving my job", "quit", "notice period",
                 "santa", "father christmas",
                 "died", "dying", "death", "dead", "passed away", "put down",
                 # leaving a job has its own answered script, and taking the children through a
                 # separation does too: both were answered well before this row existed
                 "im leaving", "i'm leaving", "leaving my job", "leaving the job", "leaving work",
                 "leaving the company", "resigning", "resign", "my notice", "notice period",
                 # "divorced" was the one form missing, so "how do i tell my kids we're getting
                 # divorced" came to this row and lost wording's drafting answer, which is the
                 # better one for it: a shrug to a parent asking that is the worst outcome here.
                 "divorce", "divorced", "divorcing", "divorce papers", "getting divorced",
                 "separating", "separated", "splitting up",
                 "diagnosis", "diagnosed", "depression", "depressed", "anxiety", "mental health",
                 "coming out", "gay", "lesbian", "trans",
                 "cheated", "cheating", "affair", "betrayed",
                 # Each of these is a question the bot already answers well, and the news script
                 # was taking it: saying no is its own answer, lending money is not household
                 # bills, and a pay rise is a meeting with evidence.
                 "say no", "saying no", "no to my", "how to say no",
                 "lend", "lending", "loan", "borrow", "borrowing", "lend them",
                 # "how do i tell my friend she owes me money" already has a script with the
                 # amount and the date in it (family's money-owed row): the news script is more
                 # general than that, so it stands down on the owing words too, not just the
                 # lending ones.
                 "owes me", "owe me", "owed me", "owes me money", "pay me back", "pays me back",
                 "paid me back", "get it back", "money back",
                 "pay rise", "payrise", "raise", "promotion", "pay review", "more money",
                 # asking for leave is its own answered script ("ask early, name the dates and
                 # say who covers"), and the news sentence is far weaker than it.
                 "time off", "day off", "days off", "annual leave", "holiday", "holidays",
                 "im busy", "i'm busy", "dont want to go", "don't want to go",
                 "doesnt want to go", "cant go", "can't go", "turned down", "turn down",
                 "not invited", "uninvited",
                 # the habit belongs to the workplace row when it happens at work, and to the
                 # working-from-home plan when the children are the ones interrupting: both
                 # name the setting and say something better than a friend script. "team" is
                 # not here - "how do i break the news to my team" is this row's own line.
                 "my boss", "boss", "manager", "colleagues", "colleague", "in meetings",
                 "in a meeting", "at work", "standup", "stand-up", "line manager",
                 "work from home", "working from home", "wfh", "my kids interrupt",
                 "the kids interrupt", "children interrupt", "kids keep interrupting",
                 # telling a child off is family's telling-a-child-off row, and this one
                 # drafted a message to send instead
                 "tell off", "telling off", "told off", "tell him off", "tell her off",
                 "tell them off", "tell my kid off", "tell my son off", "tell my daughter off",
                 "tick off")),
    # A child who has worked out that Santa is not real, or is being teased about it, is a common
    # December line and main shrugged at it.
    entry("tell-kids-santa",
          (("santa", "father christmas"),
           ("real", "pretend", "truth", "isnt real", "doesnt exist", "believe", "believes",
            "belief", "tell", "telling", "how old", "age", "found out", "teased")),
          ("Answer what they asked and keep the game: \"The presents come from us - the Santa story "
           "is a game grown-ups play to make Christmas feel magic, and now you are in on it.\" Ask "
           "them to keep it going for a younger cousin or brother, which turns the news into a job. "
           "Most children work it out at six or seven and want the ritual more than the belief.",
           "Keep it warm and short: \"The Santa story is a game we all play - I put the presents "
           "out, and now you know the secret.\" Then give them a part to play for a younger child, "
           "because being trusted with the secret is what makes it feel like growing up rather "
           "than being lied to."),
          # The asking is what has to be in the line, not the subject. With `santa` alone for the
          # ask, a joke question ("how old is santa") and a parent thinking aloud ("my son still
          # believes in santa") both got the speech about telling them.
          ask=("tell", "telling", "told", "should i tell", "do i tell", "break it",
               "break the news", "worked out", "work out", "found out", "stop believing",
               "keep believing", "now she knows", "now he knows", "the truth about santa")),
    # "how do i break the news to my children" was answered by the general bad-news row, which is
    # about telling an adult at work ("we won't be going ahead with your application"). A parent
    # asking for the words to use with a child needs the sitting-down version, with what stays the
    # same, and the subject named in the line keeps the specific talks (a death, a separation) on
    # their own rows.
    entry("break-hard-news-to-children",
          (("break the news", "bad news", "hard news", "difficult news", "something awful",
            "something terrible"),
           # "parents" is deliberately not here: "how do i break the news to my parents" is two
           # adults, and it was answered with "sit at their level".
           ("children", "kids", "child", "son", "daughter", "family", "toddler")),
          "Pick a calm moment with time after it, sit at their level and give the one fact in a "
          "short sentence, then say what stays the same: who picks them up, where they sleep, that "
          "you are not going anywhere. Then stop and let them ask; the real questions come later, "
          "in the bath or the car, and answering them plainly is the rest of the job.",
          ask=("break the news", "bad news", "hard news", "difficult news", "something awful",
               "something terrible"),
          # a death, a separation, an illness and a job all have their own words and their own
          # answers; this row is for a subject the line does not name.
          avoid=("died", "death", "dying", "passed away", "divorce", "separating", "splitting up",
                 "cancer", "ill", "illness", "diagnosis", "job", "redundant", "sacked", "fired",
                 "santa", "pregnant", "baby"),
          # "how do i break bad news to my kids" was still taking the adult, work-shaped bad-news
          # row: a child in the line is the thing that makes this the sitting-down answer.
          bias=1),
    # Someone tells you their news and you have to say something back. The line names the news
    # (pregnant, splitting up, a diagnosis, a job gone) and asks for words in it, which is a
    # different question from what to do about the news and from a condolence. Without these the
    # "what do i say" families were answered by whatever shared the word "friend" - a pregnancy
    # announcement got the maternity-leave-at-work answer, and a friend's divorce got "you seem a
    # bit off with me" - or by the shrug.
    entry("news-pregnancy",
          (("say", "said", "saying", "text", "message", "write", "words", "reply",
            "respond", "react", "answer", "congratulate", "congratulations", "congrats",
            "tell her", "tell him", "tell them", "what do i say back") + SAY,
           ("pregnant", "pregnancy", "expecting", "expecting a baby", "baby on the way",
            "having a baby")),
          ("Say congratulations first and mean it, then ask how she is: \"That is such good news "
           "- how are you feeling?\" Let her set the tone, because the first months are often "
           "sick and tired rather than shiny, and ask who already knows before you tell anyone "
           "else. Skip your own birth stories and do not ask whether it was planned."),
          # how to tell an employer is the work lane's question; a pregnancy that is a worry
          # rather than news is the health lane's. `announce` is not avoided here: "what do i
          # say when a friend announces a pregnancy" is the same question as the others.
          avoid=SAID + (
                        # someone asking *you* is the nosy-question answer, not the
                        # announcement: "what do i say when someone asks if i am pregnant"
                        "if i am", "if im", "if i'm", "asks if", "asked if", "asking if",
                        "whether i am", "whether im", "do you think i am", "am i pregnant",
                        "tell my boss", "tell my employer", "tell my manager", "maternity",
                        "paternity", "am i", "could i be", "test", "trying", "conceive",
                        "ivf", "bleeding", "cramps", "miscarriage", "losing the baby",
                        "symptoms", "due date", "weeks",
                        "buy", "buying", "present", "presents", "gift", "gifts", "visit",
                        "visiting", "take round",
                        # "says" is a form of "say" and "expected" is a form of "expecting", so
                        # both halves of this key were satisfied by "my payslip says less than i
                        # expected again" (deck single.jsonl wsit-06), a money question that got
                        # "say congratulations first and mean it".
                        "payslip", "payslips", "pay slip", "wages", "wage", "salary",
                        "salaries", "paid", "underpaid", "overpaid", "tax", "short this month"),
          bias=1),
    entry("news-splitting-up",
          (("say", "said", "saying", "text", "message", "write", "words", "reply",
            "respond", "react", "answer") + SAY,
           ("divorce", "divorcing", "divorced", "separating", "separated", "separation",
            "splitting up", "split up", "breaking up", "broke up", "marriage is over",
            "leaving her husband", "leaving his wife", "left her husband", "left his wife",
            "walked out")),
          ("Do not take a side and do not ask what happened: \"I'm sorry - that's a lot. How are "
           "you holding up?\" Then listen, and offer one thing you can actually do, like a bed for "
           "the night or dinner on Thursday. Say nothing about their ex that you might have to take "
           "back later, and keep checking in over the next few months, when the visits stop."),
          # the legal side, the paperwork and the money are their own questions, and the person
          # doing the splitting has a different one to answer
          avoid=SAID + ("lawyer", "solicitor", "legal",
                        "custody", "child maintenance", "csa", "house", "mortgage", "deposit",
                        "pension", "split the money", "who gets", "petition", "fees",
                        "i want to", "how do i tell", "tell my husband", "tell my wife",
                        "i'm leaving", "im leaving", "i cheated", "affair"),
          bias=1),
    entry("news-diagnosis",
          (("say", "said", "saying", "text", "message", "write", "words", "reply",
            "respond", "answer", "react") + SAY,
           ("diagnosed", "diagnosis", "cancer", "tumour", "tumor", "chemo", "chemotherapy",
            "radiotherapy", "ill", "illness", "unwell", "poorly", "condition",
            "multiple sclerosis", "parkinsons", "crohns", "epilepsy", "diabetes", "lupus",
            "heart condition", "has hiv")),
          ("Say the plain thing and stop there: \"I'm sorry, that's a shock. How are you doing?\" "
           "Let them name the illness and the treatment in their own time, and take your steer from "
           "how much they want to talk about it. No cures, no \"my aunt had that and she's fine\", "
           "no advice - and offer one specific, repeatable help, like lifts to appointments, then "
           "do it."),
          # what the illness is, what to eat, whether to tell work: those are their own questions,
          # and a death is a condolence rather than a reply to news
          avoid=SAID + ("symptoms", "treatment", "cure", "diet", "do i have", "do they have",
                        "tell work", "tell my boss", "survival", "prognosis", "stages",
                        # a worry of the person writing, not news someone told them
                        "is it", "am i", "are these", "could it be",
                        "died", "dying", "passed away", "funeral", "terminal",
                        "buy", "buying", "present", "presents", "gift", "gifts", "visit",
                        "visiting", "take round"),
          bias=1),
    entry("news-lost-job",
          (("say", "said", "saying", "text", "message", "write", "words", "reply",
            "respond", "answer", "react") + SAY,
           ("lost his job", "lost her job", "lost their job", "made redundant",
            "being made redundant", "redundant", "redundancy", "laid off", "losing his job",
            "losing her job", "losing their job", "been sacked", "got sacked", "been fired",
            "got fired", "let go from work", "lost the job")),
          ("Do not rush to fix it: \"That's rough - I'm sorry. How are you doing?\" Then offer the "
           "practical thing they will need in a week or two, like a reference, a look over their CV "
           "or a name to ring, rather than a plan on the first day. Skip anything that sounds like a "
           "lesson - everything happens for a reason, it worked out for the best - and do not ask "
           "what they did wrong."),
          # the person who lost the job asks a different question (money, benefits, what to say in
          # an interview), and a sacking they did to someone else is not this
          avoid=SAID + ("i lost my job", "i've lost my job", "i got sacked", "i was sacked",
                        "i got fired", "i was made redundant", "i've been made redundant",
                        "benefits", "universal credit", "sign on", "mortgage", "rent",
                        "interview", "notice pay", "redundancy pay", "tribunal", "sack him",
                        "sack her", "fire him", "fire her", "dismiss", "appraisal"),
          bias=1),
    entry("quit-a-job-message",
          # "leaving" on its own is somebody going home early, so it has to be leaving the job.
          # Bare `leave`, `leaving` and `left` are not here: in this lane they are the verb in
          # everyday lines ("i left my keys at work", "i left my job last month", "leaving early"),
          # and a job left in the past is a story rather than a letter being written now. The
          # notice is reached by naming the job ("leaving my job", "leave a job") or the thing
          # written ("leaving email", "resignation letter"), not by the word on its own.
          (("resign", "resignation", "my notice", "notice in", "quitting", "quit", "leaving my job",
            "leaving the job", "leave my job", "leaving work for good", "im leaving", "i'm leaving",
            "hand in my notice", "working my notice", "leave a job", "leaving a job",
            "leaving email", "leaving message", "farewell email", "farewell message",
            "goodbye email", "goodbye message"),
           ("letter", "email", "message", "boss", "manager", "hand", "job", "tell", "write",
            "resign")),
          ("Keep it to four lines: that you are resigning, the date your notice starts, your last "
           "working day, and thanks. Do it in a short meeting first, then send the letter the same "
           "day, and check your contract for the notice period."),
          # leaving a flat is a landlord question and leaving early is a day off; and "my partner is
          # quitting" is someone else's notice: this letter is written and handed in by you.
          # The third-person nouns are bare on purpose. A follow-up ("he keeps saying it and then
          # not doing it") is read with the subject put back in, as "he keeps saying the partner
          # quitting job and then not doing it", where "my partner" does not appear at all.
          # "Without burning bridges" is not avoided: the notice-first phrasings ("leaving my job
          # without burning bridges") still want the letter, and `work.py` keeps its own answer
          # for "how do i resign without burning bridges".
          # The job already left is not the letter being written now: "why i left my last job" is
          # the interview question, which `work.py` answers, and `left` also stands for the verb
          # in everyday lines ("i felt left out", "left the oven on", "the left over stock").
          # The card writes the letter, so the letter has to be being written now. A notice that
          # has gone in is news: "i quit my job and its great" and "i handed in my notice today"
          # both got "Keep it to four lines: that you are resigning, the date your notice starts",
          # which is the template handed to somebody who has already done it.
          guard=_the_notice_is_being_written,
          avoid=("landlord", "landlady", "flat", "tenancy", "rent", "lease", "house",
                 "last job", "previous job", "old job", "current job", "interview", "cv",
                 "why i left", "why i'm leaving", "why i quit", "why did i leave",
                 "reference", "references", "left out", "left over", "left behind",
                 "left the", "left my keys", "left my phone", "left my wallet",
                 "leaving early", "leave early", "half day", "dentist", "pick up", "collect",
                 "appointment", "sick", "early on", "hour early", "time off", "day off",
                 "partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
                 "friend", "brother", "sister", "mum", "dad", "son", "daughter", "colleague",
                 # Whether to go is a different question from how to write the letter, and the
                 # letter was answering "how do i know if i should quit my job". `work.py` has the
                 # decision entry, so these keep the letter off it.
                 "should i quit", "should i resign", "if i should quit", "if i should leave",
                 "whether to quit", "whether i should quit", "whether i should leave",
                 "know if i should", "should i leave", "should i stay", "quit or stay",
                 "worth quitting", "worth resigning", "worth leaving",
                 "he wants to", "she wants to", "he is going to", "she is going to",
                 # "what do i say when they ask why i left my last job" is an interview question,
                 # not a resignation letter: the asking is in the past tense about a job already
                 # gone.
                 "interview", "interviews", "interviewer", "why i left", "why did i leave",
                 "ask why i left", "cv", "application", "applying",
                 # Bare `notice` is no longer a key of its own: "with no notice", "at short notice"
                 # and "on the day, no notice" are how a rota moved on them, and the letter below
                 # read every one of those as somebody writing one. The notice is reached by the
                 # phrases that name it ("my notice", "hand in my notice", "notice in"), and these
                 # keep the rota lines out of it even so.
                 "no notice", "without notice", "short notice", "at short notice", "on notice",
                 "rota", "rotas", "shift", "shifts", "hours changed", "changed my hours",
                 # "i handed my notice in, what holiday do i get" is the allowance question, not
                 # the letter: the holiday that is left is `work.py`'s to work out.
                 "holiday", "holidays", "annual leave", "entitlement", "entitled",
                 "statutory", "pro rata", "pro-rata", "accrued", "accrue",
                 "how much holiday", "how many days")
                 + ON_THE_PHONE),
    # Leaving a message on a phone is its own small craft, and nobody knew it: the phone sense of
    # "leave a message" reached nothing at all before, so the person got a shrug. Four things in
    # twenty seconds is the whole answer.
    entry("voicemail",
          (("voicemail", "answerphone", "answer machine", "answering machine", "voice mail",
            "leave a message on", "message on his", "message on her", "leave a voicemail",
            "him a message", "her a message", "them a message", "to leave a message",
            "who should i leave", "can i leave a message"),
           ("leave", "leaving", "record", "say", "how", "good", "best", "clear", "tip", "tips",
            "should i", "when")),
          ("Keep it under 20 seconds: your name, your number said slowly and twice, why you rang, "
           "and when you can be reached. \"Hi, it's Sam on 07700 900123 - 07700 900123, about the "
           "boiler. Any time after six is fine.\" The number is the part people replay, so it is "
           "the part to slow down for.")),
    entry("asking-for-a-favour", ("favour", "favor", "big", "friend", "borrow"),
          ("Make it small, specific and easy to refuse: \"Could you water my plants on Tuesday and "
           "Friday? No problem if not.\" Saying what it involves and that they can say no makes people "
           "much more likely to say yes."),
          ask=("favour", "favor")),
    entry("message-cancelling-dinner",
          (("cancel", "cancelling", "canceling", "cancelled", "bail", "bailing"),
           ("dinner", "plans", "tonight", "message", "text", "politely", "friend")),
          ("Say it early, be honest and offer a concrete alternative: \"So sorry, I'm going to have to "
           "cancel tonight — I'm wiped out. Can we do Thursday instead? My treat.\" Don't invent an "
           "illness; a plain reason is easier to forgive."),
          avoid=("always cancels", "keeps cancelling", "keeps canceling", "last minute", "cancels on me")),
    # A person who cancels plans, not anything else that gets cancelled: "i keep getting charged
    # for a subscription i cancelled" is a billing question, so the entry asks for the person or
    # the plan before it answers.
    # Every shape of the same complaint: a friend who cancels, cancelling, cancelled on you, or
    # keeps bailing. The person or the plan still has to be named, so a cancelled subscription or
    # a cancelled flight stays with the billing and travel entries.
    entry("friend-keeps-cancelling",
          (("cancels", "cancelling", "canceling", "canceled", "cancelled", "flakes", "flaking",
            "bails", "bail", "bailing", "bailed", "stands me up", "stood me up"),
           ("always", "keeps", "last minute", "flaky", "again", "all the time", "every time",
            "three times", "twice", "four times", "on me", "plans", "stood me up")),
          ("Say it once, about the pattern rather than the last time: \"We've cancelled three times now "
           "and honestly it's starting to feel like I'm an afterthought. Can we pick a night we'll both "
           "keep?\" Naming the pattern and asking for one firm date keeps it about the diary, not "
           "about her character."),
          # The person can be at work as well as at home: a boss who keeps cancelling one to ones
          # takes the same "say it once, about the pattern" answer.
          ask=("friend", "mate", "she", "he", "they", "her", "him", "plans", "dinner", "pub", "lunch",
               "drink", "meet", "date", "birthday", "night out", "manager", "boss", "colleague",
               "workmate", "supervisor", "meeting", "meetings", "one to one", "one to ones", "1:1",
               "catch up", "catch-up", "our"),
          # "again" with "on me" is the family entry's own line: it answers a repeated
          # cancellation with a firmer ask, and nothing here should take it.
          # a boss can cancel a one to one (that is this entry's own line) but a shift, a day off
          # or annual leave is the employer's question, which work.py's shifts-changed answers
          avoid=("shift", "shifts", "rota", "day off", "days off", "annual leave", "employer",
                 "overtime", "called in",
                 "subscription", "subscriptions", "charged", "bill", "bills", "direct debit", "refund",
                 "contract", "membership", "gym", "payment", "order", "booking", "flight",
                 "on me again", "on me twice", "on me three times", "on me every time"),
          # "i cancelled on my friend again" is the person doing it, not having it done to them,
          # and the script above says "it is starting to feel like I'm an afterthought" - the
          # wrong way round. What they are asking is how to put it right, which is the repair
          # (bot/compose/repair.py).
          guard=lambda reading: not owns_the_deed(reading)),

    # --- what to say when it has happened to somebody else -------------------------------
    # "What do i say to my friend who has just been dumped" is one of the commonest hard
    # questions people bring, and main had no answer for any of it: the line reached
    # ask-whats-wrong ("you seem a bit off with me") or a shrug. The words hardly change with the
    # disaster - name it, don't fix it, offer one concrete thing - so one entry reads what
    # happened off the line and gives that disaster's own first sentence, rather than a row per
    # kind of bad news.
    entry("comfort-someone",
          (COMFORT_SAY,
           COMFORT_SITUATIONS + ("upset", "struggling", "hard time", "rough time",
                                 "going through", "devastated", "not coping",
                                 # the phrases people actually write, which say more than the
                                 # single word does: ask-whats-wrong keys on "upset" too, and
                                 # "my friend is upset" is not "my friend is off with me"
                                 "whos upset", "is upset", "so upset", "really upset",
                                 "upset about", "upset over", "been dumped", "is struggling",
                                 "having a hard time", "having a rough time", "mental health"),
           # who it is about, so the entry says more about the line than ask-whats-wrong does:
           # that entry keys on "friend" and "upset" too, and without this it won the line by
           # arriving first. Phrases rather than the bare words: a bare "friend" in a third key
           # makes every other entry that keys on "friend" score lower for the same line.
           ("my friend", "my mate", "my friend is", "my friend whos", "my friend has",
            "my friend got", "my friends",
            "my mate is", "my mate whos", "my mate has", "my mate got", "a friend of mine",
            "to my friend", "to my mate", "to her", "to him", "to them", "for my friend",
            "for my mate", "someone i know", "someone whos", "someone who is")),
          _comfort,
          bias=1,
          # A death or a bereavement is the loss entries' question (bot/compose/loss.py answers it
          # warmly), a card is the card entries', and a doctor, a boss or a manager is the person
          # the line wants to speak to, not somebody to comfort.
          avoid=("died", "dies", "dying", "death", "dead", "passed away", "passed on",
                 "funeral", "grief", "grieving", "bereaved", "bereavement", "miscarriage",
                 "stillborn", "lost her mum", "lost his mum", "lost her dad", "lost his dad",
                 "lost their mum", "lost their dad", "lost my mum", "lost my dad",
                 "card", "cards",
                 "doctor", "gp", "nurse", "boss", "manager", "employer",
                 # an interview is where they explain what happened to an employer, not
                 # somebody to comfort: "what do i say at a job interview about being fired"
                 # was answered with how to sit with a friend who has just been sacked
                 "interview", "interviews", "interviewer", "interviewers", "recruiter",
                 "hiring manager", "job application", "cv", "resume",
                 # a friend who is off with you is ask-whats-wrong's line, not somebody else's
                 # bad news: "my friend is upset with me" is a different question
                 "with me", "at me", "off with me", "annoyed", "ignoring me", "ignores me",
                 # ... and when you are the one who was hurt there is nobody to comfort
                 "not talking to me", "isnt talking to me", "insulted me", "insulted",
                 "rude to me", "shouted at me", "laughed at me", "picked on me", "bullied me",
                 "mean to me", "offended me", "upset me", "horrible to me", "hurt me",
                 # a line that only wonders whether they are upset is ask-whats-wrong's question
                 "seems upset", "seems off", "seems distant", "looks upset", "might be upset",
                 "maybe upset", "could be upset", "acts off", "acting off", "seems down",
                 # a baby or a small child is not somebody you use words with, and depression
                 # has its own entry (friend-is-depressed) with the better first move
                 "baby", "babies", "toddler", "newborn", "infant", "child", "children", "kid",
                 "kids", "depressed", "depression"),
          ask=COMFORT_SAY),

    # The same question with nothing named at all: "how do i comfort someone", "how do i console a
    # friend", "how do i cheer someone up". It is the plainest way the hardest question is asked,
    # and main answered none of it - a search shrug for every one. The situation row above cannot
    # take these: its third part is who the words are for, so a line with only a person in it
    # fires before anything has happened, and "how do i support a friend" belongs to the
    # noticing-and-listening answer it already had. So this row carries only the comfort verbs,
    # which are the words for the act itself, and the situation words are held out of it so the
    # two rows never both claim a line.
    # The giving side - "how do i tell someone bad news in person", "how do i give someone bad
    # news" - is the same news from the other end of the conversation, and it was keyed here
    # because it was a search shrug and anything was better. It has a better home now:
    # `how-to-tell-them` says how to say it ("one flat sentence, then stop"), where this row says
    # what to do for somebody who has just been told ("say you are glad they told you").
    entry("comfort-plainly",
          (("how do i comfort", "how do i console", "how do i cheer", "console",
            "comfort", "comforting", "cheer up", "cheering up", "be there for",
            "what do i say", "what should i say", "what can i say", "what to say",
            # "how do i respond when someone shares bad news" is the same question and was answered
            # with a stocks-and-shares ISA, because the only word left was "shares". The news is
            # named, so it sits in the ask beside the comfort verbs.
            "shares bad news", "share bad news", "shared bad news", "shares some bad news",
            "shares news", "tells me bad news", "told me bad news", "tells me something awful",
            "told me something awful", "with bad news", "bad news about", "hard news",
            # the same ask in the second person, which is how people write it too: "what do you
            # say when someone has bad news" was a search hedge
            "when someone has bad news", "when someone had bad news", "someone has bad news",
            "respond to bad news", "reply to bad news", "react to bad news"),
           ("someone", "somebody", "a friend", "a mate", "my friend", "my mate",
            "my best friend", "my sister", "my brother", "my mum", "my mom", "my dad",
            "my son", "my daughter", "my wife", "my husband", "my partner", "my gran",
            "a loved one", "a family member", "a colleague", "people", "a person", "anyone",
            # the news itself is who this is about when the line names nobody: "how do you respond
            # to bad news" was a search hedge, and its ask alone scores too little to be found
            "bad news", "sad news", "hard news")),
          COMFORT_PLAIN,
          # the situation row's words: when the line does say what happened, that row has the
          # better first sentence and this one stands aside
          avoid=COMFORT_SITUATIONS + ("upset", "struggling", "hard time", "rough time",
                                      "going through", "devastated", "not coping",
                                      "whos upset", "is upset", "so upset", "really upset",
                                      "upset about", "upset over", "been dumped",
                                      "having a hard time", "having a rough time",
                                      "mental health",
                                      # a death, a card and a doctor are other rows' lines
                                      "died", "dies", "dying", "death", "dead", "passed away",
                                      "funeral", "grief", "grieving", "bereaved",
                                      "card", "cards", "doctor", "gp", "nurse", "boss",
                                      "manager",
                                      # a baby or a small child is not somebody you use words
                                      # with, and "how do i comfort myself" is nobody else
                                      "baby", "babies", "toddler", "newborn", "child",
                                      "children", "kid", "kids", "myself", "my own",
                                      # when you are the one who was hurt there is nobody to
                                      # comfort, and the words go the other way
                                      "insulted me", "insulted", "hurt me", "rude to me",
                                      "shouted at me", "laughed at me", "picked on me",
                                      "bullied me", "mean to me", "offended me", "upset me",
                                      "horrible to me", "with me", "at me",
                                      # good news is not a bad time: a pregnancy, an engagement,
                                      # a pass or a promotion is a line to be glad with
                                      "pregnant", "pregnancy", "expecting", "engaged",
                                      "engagement", "promotion", "promoted", "got the job",
                                      "new job", "passed", "graduated", "won")
                                      # and the trouble is not a bad time at all when the
                                      # other person is the one who did something
                                      + A_BEHAVIOUR_TOWARD_THE_ASKER),

    # --- language, spelling and learning ---
    entry("affect-vs-effect", ("affect", "effect", "difference"),
          ("Affect is usually the verb and effect the noun: the rain affected the game, the rain had "
           "an effect on the game. The exception worth knowing is that you can \"effect a change\", "
           "meaning to bring it about.")),
    entry("fewer-vs-less", ("fewer", "less", "difference"),
          ("\"Fewer\" for things you can count, \"less\" for things you can't: fewer people, fewer cups, "
           "but less water and less time. The one everyday exception is money and time in speech — "
           "\"less than five pounds\" is fine.")),
    entry("how-to-pronounce", ("pronounce", "pronunciation", "word"),
          ("Tell me the word and I'll spell out the sounds syllable by syllable in plain English, "
           "with the stressed part in capitals. If it is a name, I'll say it the way the person "
           "would.")),
    # two parts, never one: a single flat group is one matched part and never clears the bar,
    # so the length words and the thing being counted are two keys that both have to be there
    entry("word-count-essay", (("count", "length", "word", "how long", "how many words",
                                "word limit", "long"),
                               ("essay", "essays", "dissertation", "dissertations",
                                "coursework", "report")),
          ("A short essay is usually 1,000–1,500 words, a university one 2,000–3,000, and coursework "
           "will state it. Aim for 10% under the limit; going over is the mistake markers mind."),
          # "how long should i plan an essay for" is the planning entry's question
          avoid=("plan", "planning", "planned", "spend planning", "outline")),
    # A speech, not every wedding line: a thank-you card, an invitation and the vows are all
    # wedding questions, and answering them with "open with a fact everyone recognises" is worse
    # than passing (khaki-key's and brave-canoe's probes).
    # The eulogy is a writing job, and the sympathy line answers a different thing. It keys on
    # writing words, so "i miss my mum" and "my nan died yesterday" stay with the comfort reply.
    entry("write-a-eulogy",
          (("eulogy", "eulogies", "eulogy for my mum", "eulogy for my dad", "eulogy for my nan",
            "reading at the funeral", "speech at the funeral", "speak at the funeral"),
           ("write", "writing", "help", "how", "draft", "start", "opening", "open", "example",
            "examples", "template", "length", "long", "words", "minutes", "what do i say",
            "structure", "include", "add", "read", "reading", "say")),
          _eulogy,
          # a eulogy is not a wedding speech and not a card: those entries have their own shape
          avoid=("toast", "wedding", "best man", "maid of honour", "birthday", "anniversary",
                 "retirement", "thank you", "card", "cards", "vows",
                 # "the eulogy is on tuesday" and "i have to give a eulogy" are timing and nerves,
                 # which the comfort reply and the practical answers do better
                 "what time", "what day", "tuesday", "wednesday", "thursday", "friday",
                 "saturday", "sunday", "monday", "parking", "flowers", "coffin", "casket"),
          ask=(("write", "writing", "help", "how", "draft", "template", "examples", "length",
                "long", "words", "minutes", "structure", "start", "opening", "open", "what do i say",
                "say", "include", "nervous", "scared")),
          bias=1),
    entry("write-a-toast", ("speech", "toast", ("wedding", "sisters", "best man", "maid of honour",
                                                "father of the bride", "few words", "write",
                                                "birthday", "70th", "60th", "50th", "retirement",
                                                "leaving do", "anniversary")),
          ("Three minutes, about 450 words, is the length to aim for: a line thanking the people who "
           "got everyone there, one story with a real detail in it that shows what the person is like, "
           "then what they mean to you and a toast. Open with a fact everyone in the room recognises, "
           "then turn it: \"My sister has spent her life fixing animals, so it's a relief she's finally "
           "found one she can train.\" Keep that opening 30 seconds short, and put the sincere bit in "
           "the middle where people aren't braced for it."),
          avoid=("thank you", "thankyou", "card", "cards", "invitation", "invitations",
                 "save the date", "place card", "place cards", "order of service", "vows", "vow",
                 "reading", "readings", "venue", "guest list", "seating", "table plan")),
    # The card people write next to a wedding, a christening or a funeral. It is a wording job
    # like the rest of this domain, and main only hedged on it.
    # A thank-you card is thanked, so the thanks has to be in the line: with `card` as the only
    # other signal, "how do i write a christening card" and "how do i word a wedding card" got
    # this, and a lemon cake is no answer to either. Those are card-christening's and
    # card-wedding's, keyed on the occasion itself.
    entry("thank-you-card-note", (("card", "note", "letter", "message", "text"),
                                  ("thank you", "thankyou", "thank-you", "thanks", "grateful",
                                   "appreciate", "appreciated")),
          # One note for a thanks that names nothing in particular, shared with the language
          # domain's thank-you note, so the same line cannot get two different notes.
          THANKS_ANY,
          avoid=("birthday card", "christmas card", "wedding card", "christening card",
                 "wedding message", "christening message", "card game", "cardiff")),
    # "how do i thank someone for a meal" and "thank you letter for a present" were a shrug and a
    # gift-ideas list: the person is not asking what to buy, they are asking what to say.
    entry("thanks-for-hospitality",
          (("thank", "thanks", "thank you", "thankyou", "thank-you", "grateful"),
           ("letter", "note", "card", "message", "text", "email", "say", "saying", "write",
            "wording", "words", "meal", "dinner", "lunch", "party", "weekend", "staying",
            "stayed", "host", "hosted", "put me up", "lift", "present", "gift", "flowers",
            "helped me", "help", "wedding")),
          thanks_note,
          # A thank-you note is a writing job, so the line has to ask for one: "thanks, that
          # helps" and "great thanks. what did i say the problem was?" are the person talking to
          # the bot, and "thanks for staying with me" is a goodbye. Only the asking shapes count.
          ask=("how do i", "how can i", "how should i", "how do you", "what should i say",
               "what do i say", "what to say", "what do i write", "what should i write", "write",
               "writing", "wording", "word", "words", "letter", "note", "card", "message", "text",
               "email", "thank you for the", "thanks for the", "thank them"),
          # A thank-you after an interview is `interview-thank-you`'s, which says what to put in
          # it and when to send it; this note is for a meal, a stay or a present.
          avoid=("interview", "interviews", "interviewer", "interviewing", "job interview",
                 "panel", "recruiter"),
          # a present is thanked for, not shopped for: this ties with the gift entry on the words
          # and has to win the tie, or "thank you letter for a present" is a list of mugs.
          bias=1),
    entry("learn-spanish-20-minutes", ("spanish", ("learn", "learning", "language", "months", "six", "minutes")),
          ("Spend the 20 minutes on speaking aloud and short listening, not on apps that only make "
           "you tap words: 10 minutes of a course with audio, 5 of vocabulary you will actually use, "
           "5 of repeating phrases. Twenty minutes every day beats two hours on Sunday, and in six "
           "months you will manage the basics of a trip.")),
    entry("spanish-train-station", ("station", "train", "phrases", ("travel", "spanish")),
          ("¿Dónde está la estación de tren? — \"Where is the train station?\" Useful next to it: ¿A "
           "qué hora sale el próximo tren? for \"what time is the next train?\"."),
          # A line about travelling by train in a named country is a planning question, not a
          # phrase to learn: "whats the best way to travel around italy by train" was being
          # answered in Spanish, of all things.
          avoid=("italy", "italian", "france", "french", "germany", "german", "portugal",
                 "greece", "spain by", "netherlands", "belgium", "train travel", "by train",
                 "take the train", "get around", "travel around", "travelling around",
                 "rail", "railway", "interrail", "railcard", "tickets", "book a train",
                 "cheap train", "trainline", "high speed",
                 # a person who trains at a gym is not asking for a phrase: "i train twice a
                 # week at the gym near the station" was answered with the Spanish for it
                 "gym", "gyms", "workout", "work out", "weights", "i train", "exercising")),
    # The planning question behind it, for the country people ask about most after their own.
    entry("trains-in-italy",
          (("italy", "italian", "trenitalia", "italo", "rome", "florence", "venice", "milan",
            "naples"),
           ("train", "trains", "rail", "by train", "get around", "travel around", "tickets",
            "book", "high speed", "frecciarossa")),
          "Book on Trenitalia, the state operator, or Italo for the other fast line: both sell "
          "online and at the machines in the station, and a ticket bought a week or two ahead is "
          "much cheaper than one bought on the day. The fast Frecciarossa trains do Rome to "
          "Florence in about 1 hour 30, Florence to Venice in about 2 hours, and Rome to Naples in "
          "about 1 hour 10, so Milan, Florence and Rome makes a comfortable week. Regional trains "
          "are cheap and need no reservation but are slow, and a regional ticket bought at a "
          "machine has to be stamped in the small machine on the platform before you get on.",
          avoid=("food", "pizza", "weather", "hotel", "hotels", "flight", "flights", "visa",
                 "passport", "work", "job", "move to", "living in", "rent", "house"),
          bias=1),

    # One entry for the whole table, so every "how do you spell X" question is answered by a word
    # that is actually in the table rather than by one entry per word. "correct" carries the
    # "which is correct, definately or definitely" shape, and the word itself is the second signal.
    entry("spelling-tricky-word", (("spell", "spelling", "spelt", "spelled", "correct",
                                    "correctly", "written"),
                                   _SPELLING_WORDS),
          _spelling,
          ask=("spell", "spelling", "spelt", "spelled", "correct", "correctly", "written",
               "how do you", "which is", "is it"),
          slips=_SPELLING_SLIPS),
    # Improving spelling is a different question from one word's spelling: it wants a method.
    entry("improve-spelling", (("spelling", "spell", "spelt", "spelled"),
                               ("improve", "better", "learn", "remember", "struggle", "bad",
                                "terrible", "awful", "hopeless", "rules", "good")),
          ("Work from your own mistakes, not a list of hard words: take the twenty words you "
           "actually get wrong in texts and emails, and use look-say-cover-write-check on five a "
           "day - look at it, say it, cover it, write it, check it. Break long words into "
           "syllables as you say them (gov-ern-ment, sep-a-rate), and read your own writing out "
           "loud, because most spelling slips are words you can hear. Spellcheck is fine as a "
           "check, but read the suggestion before you accept it, or the same mistake survives."),
          ask=("improve", "better", "learn", "remember", "struggle", "bad", "terrible", "awful",
               "hopeless", "how do i", "how can i", "help")),
    # "is it seperate or separate", "which is correct, wierd or weird": one of the two spellings
    # offered is the slip, so it is enough to know a slip is in the line.
    entry("spelling-pick-one", (("which", "correct", "or"), _SPELLING_SLIPS),
          _spelling,
          ask=("which", "correct", "is it", "or"),
          slips=_SPELLING_SLIPS),

    # "how do i write a letter to my mp" is a letter question, and "letter" alone is the icing
    # bag's word, so the MP is named in the key rather than the topic being guessed.
    entry("letter-to-mp",
          (("letter to my mp", "write to my mp", "my mp", "to my mp", "contact my mp",
            "email my mp", "member of parliament", "mps", "councillor", "councillors",
            # not the bare word "council": it took "how do i complain to the council" and
            # "how do i report a problem to the council", which are complaints to the council
            # and not letters to an MP (@airy-radio measured it). A councillor is still here.
            "mp's"),
           # "letter" is not a word of this key: a follow-up asks over the line it leans on
           # ("i got a letter from the council about my bin" -> "what do they want from me"),
           # and with "letter" here that follow-up was answered with how to write to an MP
           ("write", "writing", "how do i", "how can i", "complain", "contact", "email",
            "what do i say", "who is", "who's", "should i", "get in touch", "reach")),
          ("One page, one issue, one ask. Say who you are and where you live first, with the full "
           "postcode, because an MP can only act for their own constituents; then the problem in "
           "three sentences with the dates, then exactly what you want them to do - change a rule, "
           "chase a department, or write to a minister for you. Attach copies, never originals, and "
           "ask for a reply within four weeks. Address it to the House of Commons, London SW1A "
           "0AA, or find the name and the office email on theyworkforyou.com. A short factual "
           "letter gets an answer from a caseworker; a long angry one gets a standard reply."),
          # a council tax question is money, and the mp3 player is not an MP
          avoid=("council tax", "mp3", "music", "player", "download", "app", "video",
                 "game", "film", "book", "series"),
          ask=("write", "letter", "how do i", "complain", "contact", "who is", "what do i say")),
]

# The places where "talking" is not a conversation to end. "how do i stop talking in class" is
# about keeping quiet in a room with a teacher in it, and both rows that close a chat read it off
# the words "stop talking" as a conversation to leave politely. A setting where the talking is the
# lesson stands both rows down, and they share this one list so the fence cannot drift between
# them.
TALKING_IS_NOT_A_CHAT = ("class", "classes", "classroom", "classrooms", "lesson", "lessons",
                         "lecture", "lectures", "school", "schools", "assembly", "teacher",
                         "teachers", "tutor", "seminar", "in class", "at school", "during class",
                         "exam", "exams", "playground",
                         # A meeting is the same shape: "how do i stop talking in a meeting" got
                         # the exit script with the "name the thing you have to get to" line,
                         # where the person wants the meeting card (an agenda sent the day
                         # before). It is a room with an order to it, not a chat to leave.
                         "meeting", "meetings", "board meeting", "team meeting",
                         "one to one")

# --- the words for an awkward thing to say ---------------------------------
# "How do I tell someone..." is a whole family of everyday asks that has nothing to do with the
# thing being told, and main had no answer for eight of them. Each row below is the wording itself
# plus the one thing about tone, and the ask is the telling: the subject of the line is what keeps
# these apart from each other and from the rows on refunds, noise and letters.
ASKING = ("how do i tell", "how do i say", "how do i ask", "how to tell", "how to say",
          "how to ask", "what do i say", "what should i say", "how can i tell", "how can i say",
          "how can i ask", "ways to say", "way to say", "word for", "how do you tell",
          "how do you say", "how would i say", "tell someone", "telling someone",
          "say to someone", "saying to someone", "tell a friend", "tell my friend",
          "tell people", "break it to", "bring it up", "polite way", "politely")

# "how do i say no without being rude" has its own row (`say-no`); these are the shapes it is not.
_NOT_A_SIMPLE_NO = ("cant afford", "afford it", "stand up for myself", "second date",
                    "goodbye", "leaving do", "leaving present", "thank you", "condolence",
                    "sympathy", "eulogy", "toast", "wedding speech", "reference", "resign",
                    "notice", "complaint", "refund")

ENTRIES += [
    # Asking for help feels like admitting something, so people ask for the words instead. The
    # answer is the shape of the ask - one job, one bit of it, one small piece of their time.
    entry("ask-for-help",
          (("help", "hand", "support", "a favour", "favour", "assistance"),
           ("ask", "asking", "sound", "sounding", "weak", "stupid", "embarrassed", "ashamed",
            "awkward", "burden", "bothering", "admit", "need")),
          ("Name the job, the bit you are stuck on, and the smallest thing that would unstick it, "
           "with a time on it: \"I'm stuck on the last two pages of this report - could you read "
           "them before Friday?\" A specific, finished ask is easy to say yes to, and it reads as "
           "competence rather than weakness; \"can you help me with this\" gives them nothing to "
           "hold on to. If it still feels like a lot, say why you are asking them: they were good "
           "at this, or they have done it before."),
          ask=ASKING + ("sound weak", "sounding weak", "without sounding", "dont want to sound",
                        "feel bad asking", "hate asking", "hate to ask", "hard to ask"),
          # The CV row writes a CV and the extension row asks for more time, so both keep the
          # line: "how do i ask for help with my cv" wants the one page, not the asking.
          avoid=("how do i ask for a favour", "favours", "favor", "reference", "landlord",
                 "boss for", "pay rise", "raise", "extension", "deadline", "lend", "borrow",
                 "money", "lift", "ride", "cv", "resume", "covering letter", "cover letter",
                 "personal statement", "application")),
    # "How do I tell someone I need space" is a relationship line, not a storage one: "space" is
    # the word for room in a flat, so the key is the human ask and the storage words stand aside.
    # A bare "room" is the place, not the need: with it in the key, any decorating line that says
    # "want" reached this row through the want rule ("i want to decorate the spare room", "im
    # redoing the spare room, want to paint it a lighter colour" both got the tell-them-you-need-
    # quiet-days answer). The human sense is carried by "space" and by the room phrases, so the
    # place itself stands aside, and so does a line that is working on the room.
    entry("ask-for-space",
          (("space", "some room", "room to breathe", "room to think", "room to myself",
            "time alone", "time to myself", "time on my own", "breathing room", "a break"),
           ("need", "needs", "want", "tell", "say", "ask", "asking", "how", "someone", "i need")),
          ("Say it as a need for a few days rather than a verdict on them, and put a date on it so "
           "it cannot sound like leaving: \"I've got a lot on and I need a couple of quiet days - "
           "I'll ring you Thursday.\" Do not explain it as their fault and do not apologise for "
           "it three times; a short clear ask with a return date is the kindest version, and it "
           "gives them something to wait for instead of something to worry about."),
          ask=ASKING + ("i need space", "need some space", "need a bit of space", "time apart"),
          avoid=("flat", "bedroom", "kitchen", "cupboard", "wardrobe", "shed", "office", "desk",
                 "storage", "box room", "car", "van", "parking", "garden", "garage",
                 "paint", "painting", "painted", "repaint", "decorate", "decorating",
                 "decoration", "wallpaper", "plaster", "plastering", "carpet", "flooring",
                 "tiles", "curtains", "blinds", "furniture", "sofa", "shelves", "rug",
                 "lamp", "lights", "tidy", "tidying", "clear out", "clearing", "damp",
                 # "a break" is a fractured bone as often as it is a rest: "how do i tell a
                 # sprain from a break" was told how to say it as a need for quiet days.
                 "sprain", "sprained", "strain", "fracture", "fractured", "broken", "bone",
                 "bones", "wrist", "ankle", "knee", "elbow", "shoulder", "rib", "ribs",
                 "x-ray", "xray", "swelling", "swollen", "injury", "injured", "numb")),
    # "how do i ask someone to be quieter" is the awkward-one-line ask: the row is the sentence,
    # and the noise rows (a neighbour's dog, a party next door) keep their own answers.
    entry("ask-for-quiet",
          (("quiet", "quieter", "quietly", "noise", "noisy", "loud", "turn it down",
            "keep it down", "lower the volume"),
           # A colleague is not a neighbour. This script is the telly through the wall and the ask
           # "between neighbours", so the desk lines are work.noisy-office's; with the person words
           # in both halves, "how do i tell a colleague to be quieter" was told to knock on the
           # wall and "my coworker plays music out loud" got the council's abatement notice.
           ("ask", "asking", "tell", "telling", "say", "saying", "how", "neighbour", "neighbor",
            "flatmate", "roommate", "housemate", "someone")),
          ("Ask once, in private, at a calm time, and make it about the thing and not the person: "
           "\"The telly carries through the wall after eleven - could you turn it down a notch?\" "
           "Give when it happens, how it lands and what would fix it. Do not knock at midnight "
           "while it is loud - the ask that lands is the one made in daylight, and the first ask "
           "should sound like a favour between neighbours, because it is."),
          ask=ASKING + ("be quiet", "be quieter", "keep it down", "turn it down", "less noise"),
          # A "quiet word with my boss" is a work line and loud children are a parenting one, so
          # the row stands aside for both rather than telling someone to ask their manager to
          # turn the telly down.
          avoid=("dog", "dogs", "barking", "party", "parties", "music", "builders", "drilling",
                 "landlord", "council", "police", "baby", "toddler", "child", "children", "kid",
                 "kids", "son", "daughter", "boss", "manager", "quiet word", "appraisal", "hr",
                 "who is making", "what is that noise", "banging", "alarm",
                 # a person or a room at work is the desk's line: the same ask there is one
                 # friendly sentence about the phone call, not a knock on the wall
                 "colleague", "colleagues", "coworker", "coworkers", "co-worker", "co-workers",
                 "workmate", "workmates", "teammate", "teammates", "team mate", "team mates",
                 "at work", "at my desk", "open plan", "in the office", "the office")),
    # Leaving a party early is a small social skill with a script, and "how do i politely leave"
    # reached nothing at all.
    entry("leave-a-party",
          # the groups are "a do" and the leaving, not the bare verb "do" and the bare "how":
          # those two made every "how do i..." line a candidate, and "how do i ask for help
          # without sounding weak" was answered with the leaving-a-party script.
          # "a do" is the party in "are you going to their do", but the bare verb "do" made every
          # "how do i ... without being rude" line a candidate, so the row wants the noun.
          (("party", "parties", "a do", "gathering", "event", "wedding", "drinks", "dinner",
            "barbecue", "bbq", "celebration", "night out", "house party"),
           ("leave", "leaving", "left", "go home", "going home", "slip away", "slip out",
            "leave early", "get away", "escape", "politely", "without being rude",
            # the same exit said as a goodbye: "how do i say goodbye at a party" named the
            # occasion and the word goodbye and nothing else, so it reached the small-talk
            # rows or the wording offer instead of the script
            "say goodbye", "say goodbyes", "goodbye", "goodbyes", "say bye", "head off",
            # the exit said as an apology on the way out: "how do i excuse myself from a party"
            # and "how do i make my excuses and go" were the party-planning row (guest count and
            # buffet budget), because "excuse myself" was in neither group. The phrases, not the
            # bare "excuse", which is an absence note.
            "excuse myself", "excusing myself", "make my excuses", "made my excuses",
            "my excuses")),
          ("Thank the host, mean it, and go: \"It's been lovely - I'm going to head off, thank "
           "you so much.\" Say your goodbyes to the host and the one or two people you actually "
           "spent the evening with, not the whole room, and have your reason ready in one line "
           "(\"early start tomorrow\") because the second question is always why. Leaving at the "
           "natural lull is easier than the big goodbye, and nobody minds nearly as much as the "
           "leaving feels like it will."),
          ask=ASKING + ("leave early", "leave a party", "politely leave", "slip away",
                        "leave without", "get out of a party", "say goodbye", "goodbye",
                        "goodbyes",
                        # the exit asked as an apology needs its own ask word as well as its
                        # key: the key matched on "excuse myself" and the ask matched nothing,
                        # so the row scored nothing and the line was a shrug
                        "excuse myself", "excusing myself", "make my excuses",
                        "made my excuses", "my excuses"),
          avoid=("leaving do", "leaving present", "leaving job", "leaving my job", "resign",
                 "notice", "school", "hotel", "airbnb", "car", "parking", "before it ends",
                 "keys", "flat", "tenancy", "landlord",
                 # a goodbye on the phone is the call card's line, not a party's
                 "on the phone", "phone call", "the phone", "call", "calls", "voicemail")),
    # Ending a conversation someone else is keeping going is its own script.
    entry("end-a-conversation",
          (("conversation", "chat", "talking", "call", "phone call", "small talk"),
           ("end", "ending", "finish", "finishing", "stop", "get out", "escape", "leave",
            "close", "politely", "how")),
          ("Close it with a reason and a warm line, then move: \"I'll let you go - it's been "
           "really good to catch up.\" Turning it round to them is the trick, because \"I'll let "
           "you get back to it\" ends the call without anyone being brushed off. In person, say "
           "one thing you want to come back to (\"I want to hear how the move went - let's get a "
           "coffee next week\"), then go; a promise to continue is what makes leaving feel "
           "friendly rather than rude."),
          ask=ASKING + ("end a conversation", "end the conversation", "stop talking",
                        "get out of a conversation", "politely end", "politely get away",
                        # the ending said plainly with "end": "how do i end a chat at a party"
                        # matched both halves of the key and was still turned away, because
                        # the ask wanted the wording of a polite exit and the line only said
                        # "end". The conversation, call or chat is the subject, so the ending
                        # is the question.
                        "end a chat", "end the chat", "how do i end", "how to end",
                        "how do i get out"),
          # "how do i tell someone to stop calling me" wants the number blocked, which has its
          # own row, so the calls keep it.
          avoid=("meeting", "presentation", "interview", "argument", "row", "relationship",
                 "break up", "landlord", "contract", "phone contract", "paid", "bill",
                 "stop calling", "stop texting", "stop messaging", "keeps calling",
                 "block", "blocked", "blocking", "unwanted calls", "spam", "cold callers",
                 ) + TALKING_IS_NOT_A_CHAT,
          # The sharper exit keeps its line when a plainer row also matches: "how do i get out
          # of a boring conversation" is this row's answer (turn it round to them), not the
          # generic close-it-with-a-reason script. friends.py's end-a-conversation-leave now
          # carries bias=1 for "how do i leave a chat without being rude"; this row stays level
          # with it so the boring conversation still gets the line that answers "boring".
          bias=1),
    # Consoling is a wording question, and the answer is almost the opposite of advice.
    entry("console-someone",
          (("console", "comfort", "sympathy", "condolence", "condolences", "cheer up",
            "make them feel better", "say to someone"),
           ("someone", "friend", "grieving", "bereaved", "loss", "lost", "died", "death",
            "dying", "crying", "upset", "hurt", "bad news", "how", "what")),
          ("Say the plain thing and then be quiet: \"I'm so sorry - I don't have words, but I'm "
           "here.\" Name the person who died if they have named them, say their name back, and "
           "offer one concrete thing instead of \"let me know if you need anything\": a lift, a "
           "meal on Thursday, sitting with them. Do not explain, compare it to your own loss, or "
           "look for the bright side; the comfort is in staying, and in being the one who is "
           "still there in three weeks."),
          ask=ASKING + ("console someone", "comfort someone", "what do i say to",
                        "what to say when someone", "cheer someone up"),
          avoid=("child", "children", "kid", "kids", "dog", "cat", "pet", "bereavement leave",
                 "funeral cost", "funeral flowers", "eulogy", "obituary", "death certificate",
                 "probate", "will", "inheritance", "what to wear")),
    # A complaint answered in person, or in a review reply: own it once, fix it, no process.
    entry("apologise-to-a-customer",
          (("customer", "client", "customer service", "complaint", "complaining", "review",
            "reviewer", "client"),
           ("apologise", "apologize", "apology", "sorry", "how", "say", "write", "respond",
            "reply", "answer", "bad", "unhappy", "angry", "upset")),
          ("Name what happened, own it once, say what you are doing and by when, and leave your "
           "process out of it: \"I'm sorry - we sent the wrong size twice, and that's on us. The "
           "right one goes out today on next-day delivery.\" One apology is enough; explaining "
           "the system reads as an excuse, and asking them to do the work reads as a second "
           "failure. If it is a public review, answer in two sentences and move the detail to "
           "email."),
          ask=ASKING + ("apologise to a customer", "apologize to a customer", "sorry to a customer",
                        "reply to a bad review", "respond to a complaint", "answer a complaint",
                        "apologise to a client"),
          avoid=("refund", "guarantee", "warranty", "legal", "sue", "ombudsman", "trading standards",
                 "tell a customer no", "tell customers no", "say no", "saying no", "turn down",
                 "refuse", "decline", "price", "quote", "delay", "late", "waiting",
                 "small claims", "compensation", "my landlord", "my boss", "my colleague",
                 "my friend", "my partner", "my wife", "my husband", "my mum", "my dad")),
]

# Two more "what do I say" lines that had no row of their own: a present you do not like, and
# being asked whether you are pregnant. Both are ordinary, both are awkward, and both were
# answered by a row that had caught one of the words - an offer of condolences, and the
# announcement of a pregnancy - which is worse than a shrug, because it answers a question
# nobody asked.
ENTRIES += [
    # Saying thank you for something you will never use. The fault main had was that a gift
    # line was read as gift *buying*, so the answer was about what to choose.
    entry("thanks-for-a-gift",
          (("present i dont like", "present i don't like", "gift i dont like",
            "gift i don't like", "present i hate", "gift i hate", "already have it",
            "already got one", "wrong size", "ugly present", "ugly gift", "bad present",
            "bad gift", "didnt like the present", "didn't like the present",
            "didnt like the gift", "didn't like the gift", "someone gives me", "gives me a gift",
            "gave me a present", "gave me a gift", "thank you for a present",
            "thank you for the present", "thank you note", "thank you card",
            "thank you letter", "thank someone for a gift", "what do i say when someone gives me"),
           ("present", "gift", "presents", "gifts", "thank", "thanks", "say", "write",
            "reply", "respond", "polite", "politely", "card", "note", "letter", "how", "what")),
          ("Say the thanks and mean that part, in one line, and do not name the thing: \"Thank "
           "you - it was so kind of you to think of me.\" If you will use some of it, say how - "
           "\"the scarf is going straight on tomorrow\" - and if you will not, say nothing about "
           "it and thank them again later for the thought. Ask for the receipt only from someone "
           "close, and only when the thing was expensive: \"It's lovely but the size is wrong - "
           "could I swap it?\" Nobody is owed the truth about a present."),
          ask=("say", "said", "saying", "write", "reply", "respond", "thank", "thanks", "what",
               "how", "words", "message", "text", "card", "note", "letter")),

    # "what do i say when someone asks if i am pregnant" is a question put to you, and the
    # announcement row answered it with congratulations for the person asking.
    entry("asked-if-pregnant",
          (("are you pregnant", "if i am pregnant", "if im pregnant", "if i'm pregnant",
            "asks if i am pregnant", "asked if i am pregnant", "asking if i am pregnant",
            "asks if im pregnant", "asked if im pregnant", "do you think i am pregnant",
            "when are you due", "when is the baby due", "when is your baby due",
            "any news", "is there a baby", "are you expecting", "asks if i am expecting",
            "asked if i am expecting", "asking about a baby", "asks about a baby"),
           ("say", "said", "saying", "reply", "respond", "answer", "how", "what", "words",
            "someone", "people", "asks", "asked", "asking", "relative", "relatives", "mum",
            "mother", "mother in law", "colleague", "colleagues", "aunt", "friend")),
          ("One easy line closes it, and you do not owe anyone more than that: \"No - I've just "
           "had a big lunch.\" If it keeps coming, or it is someone who should know better, name "
           "it once and flatly: \"I'd rather not talk about that.\" You do not have to explain "
           "whether you are trying, whether it happened and did not last, or whether you have "
           "decided not to - and you can say exactly that: \"that's not something I talk about.\" "
           "Then change the subject to them, which is what most people want anyway."),
          ask=("say", "said", "saying", "reply", "respond", "answer", "how", "what", "words",
               "someone", "people", "asks", "asked", "asking")),
]

# --- a thank-you speech at a leaving do ------------------------------------------------------
# The leaving card, the resignation letter and the eulogy each have a row, and the speech a person
# stands up and gives at a colleague's do had none: "thank you speech for my team leaving do" and
# "i have to give a leaving speech" were answered with a nod. It is a spoken few minutes, so the
# row wants the do and the standing up, not a card and not the letter of resignation.

LEAVING_SPEECH = (
    "Three short parts, three minutes at most: say who you are and why you are the one talking, "
    "give one concrete thing you will miss about them - a habit, a phrase, a thing they always "
    "fixed - and end with the room raising a glass. Write it out in full sentences and then cut it "
    "in half: the best version is two clean stories and a line about what they were like to work "
    "with. Name two or three people who are in the room and thank them for something specific, and "
    "finish on a toast like 'to Priya' rather than a thank-you to everyone, which always sounds "
    "like a wedding.")

ENTRIES.append(entry(
    "leaving-speech",
    # "what do i say at a leaving do" is spoken, not written, and it was the card's row: the
    # phrase has to be read as one, because "say" on its own belongs to the card and the eulogy
    (("speech", "speeches", "toast", "few words", "say a few words", "stand up and say",
      "say at a leaving", "say at the leaving", "say at my leaving", "say at a farewell",
      "say at the retirement", "words at a leaving"),
     ("leaving do", "leaving party", "leaving drinks", "leaving", "leaving us", "leaving work",
      "last day", "farewell", "goodbye", "send off", "retirement", "retiring", "colleague",
      "team", "boss", "work", "thank you", "thanks", "tribute")),
    LEAVING_SPEECH,
    ask=("speech", "speeches", "toast", "say", "words"),
    # a card, a letter, a wedding speech and a eulogy are other rows, and a speech delay or a
    # phone's speech-to-text is not a speech at all
    avoid=("card", "cards", "message", "sign", "resignation", "resign", "notice", "letter",
           "email", "wedding", "bride", "groom", "best man", "father of the bride",
           "funeral", "eulogy", "death", "died", "passed away", "birthday", "anniversary",
           "maid of honour", "speech to text", "speech delay", "speech therapy",
           "figure of speech"),
    bias=2))


# --- a machine that had to do the job twice ----------------------------------------------------
# "Takes" is two questions: how long a machine needs, and a machine that needed two goes at the job.
# The second is a fault, and the rows around it were reading the first: "the tumble dryer takes two
# goes to dry a load" was handed the dryer's turn-round time, and "the tumble dryer leaves everything
# damp" was answered "Hang the washing on a rack in the warmest room", which is advice for a person
# with no dryer at all. The phrases are the job handed back undone, or taking so long that it is not
# getting done, said as people say it, and they
# live here because the timing row (home.py), the drying row (clothing.py) and the fault rows in
# home_craft.py all have to agree on what the shape is.
A_JOB_LEFT_UNDONE = (
    "two goes", "two cycles", "two washes", "two loads", "three goes", "three cycles",
    "three washes", "took two", "takes two", "went through twice", "put it through twice",
    "still wet", "still damp", "leaves everything damp", "leaves the clothes damp",
    "leaves clothes damp", "leaves them damp", "leave everything damp", "come out damp",
    "comes out damp", "come out wet", "comes out wet", "doesnt dry", "doesn't dry", "isnt drying",
    "isn't drying", "not drying", "never dries", "doesnt finish", "doesn't finish", "not finishing",
    "doesnt cook", "doesn't cook", "undercooked", "comes out raw", "not hot enough",
    # the same fault said as time rather than as a second go: a job that takes all night is a job
    # that is not getting done, and "the tumble dryer takes forever to dry a load" was answered
    # with a clothes rack for the same reason
    "takes ages", "taking ages", "takes forever", "taking forever", "taking hours", "takes hours",
    "taking so long", "takes so long", "taking all day", "takes all day", "long to dry",
    "slow to dry", "drying slowly", "dries slowly", "hours to dry", "all night to dry",
)
