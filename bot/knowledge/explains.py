"""Everyday things explained: how a machine, a screen or a system actually works.

Answers lane domain. People ask about the world the way a curious friend would - "how does
wifi work", "how does a washing machine work", "what is a heat pump" - and main had no entry
for any of them, so the whole class of question met the search hedge. Where a repair entry
already answered the trouble ("my washing machine is not working"), it also took the
explanation, so "how does a washing machine work" got fault-finding steps.

The key is the machine plus the explain ask, never the machine alone: the subject is what the
line is about, but a line about a broken one is a different question. Each entry therefore
carries EXPLAIN in `ask` (a "how", "what" or "why" must be in the line) and TROUBLE in
`avoid` (a fault word turns it off), so a repair line keeps its repair answer.

The reply is the mechanism in the first sentence, then the one detail that makes it click -
the same shape as bot/knowledge/science.py, which owns the physics half (why the sky is blue,
why ice floats). This file owns the made things: networks, screens, the kitchen, the heating.
"""
import re

from .lookup import A_WHAT_TO_WEAR, entry, not_the_ask_about_the_order

ANSWERS = ("technology", "science", "home-and-diy")

# A line that asks how something works, rather than for help with it.
EXPLAIN = ("how", "what", "why", "explain", "explains", "explained", "mean", "means",
           "actually")

# The ways people say "tell me the mechanism" without "how". One of these has to be in the
# line beside the subject, so "what is a router" and "explain wifi to me" both reach the fact
# while "wifi password" and "wifi booster" do not. A bare "how" or "how do" is not one of
# them: it is in every how-to, and with it here "how do i clean my washing machine" and
# "how do i bleed a radiator" were both answered with the mechanism instead of the job.
WORKS = ("work", "works", "working", "explain", "explains", "explained", "what is",
         "what are", "what's", "what does", "what do", "inside", "mean", "means",
         "actually",
         # "how does a flask keep soup hot" asks for the trick, not the job: these say so
         # without opening the door to "how do i keep warm" (no machine is named there)
         "keep hot", "keeps hot", "keep cold", "keeps cold", "keep warm", "keeps warm",
         "keeps tea hot", "keeps coffee hot", "stays hot", "stay hot",
         # "how does a radiator heat a room" and "how does a chimney draw" want the mechanism,
         # and "how does" is the ask exactly as "how do i" is the job: the third person takes
         # no "i", so a how-to cannot say it. These were reaching the repair cards instead -
         # the oven's own fault answers, a plumber's number, the levelling steps for a washer -
         # because the machine's name matched and nothing else on the line did.
         # "how come" and "how did" are not this ask: "how come my boiler is losing pressure"
         # is the same question as "why is my boiler losing pressure", and the repair row owns
         # it. With them here three fault lines went to the mechanism instead of the fix.
         "how does", "how do they", "how do these", "how do those")

# "what does gps stand for" wants the words behind the letters, not the mechanism, so those
# asking words get their own small rows below instead of being a way into the explanations.
SPELLED = ("stand for", "stands for", "short for")

# The same question in a different coat: "what does diy mean" and "what is nhs short for" both
# want the letters spelled out, and only "stand for" was reaching the small rows, so every one
# of those lines was a shrug. A person who asks what the letters mean already has the thing.
# Not "what does" or "what do" on their own: with those in the gate "what does gps work" and
# "what does a router need" reached the letters row instead of the mechanism.
# "what does atm mean" is the same question as "what does atm stand for", and it was
# reaching the mechanism row: that row keys the phrase "what does" as well as the subject, so
# it out-scored the letters row that matched only "mean". The phrase "does mean" is in the
# letters key for that reason, and it is a phrase and not "what does" alone, because "what
# does atm do" and "what does a router need" want the mechanism.
ASKS_A_NAME = SPELLED + ("mean", "means", "meaning", "does mean", "does it mean",
                         "does that mean",
                         # "what does gb mean" was answered and "what is a firewall", "whats a
                         # gpu", "what is a ssd" were all shrugs - the same question without the
                         # word "mean" in it. The row still needs its own word in the line, so a
                         # bare "what is" only reaches the thing being asked about: "what is
                         # wrong with my printer" has no row of its own and is untouched. "what
                         # is the" stays out, because "what is the best gpu" and "what is the ip
                         # address of my router" ask something else.
                         "what is a", "whats a", "what's a", "what is an", "whats an",
                         "what's an", "what are", "what is", "whats", "what's")

# A fault word means the person wants the thing fixed, not explained. Without this the
# explanation outranked the repair entry on "my washing machine is not working" (the key's
# "working" matched), which is exactly the kind of turn a new domain must not take.
TROUBLE = ("not", "isnt", "isn't", "doesnt", "doesn't", "wont", "won't", "broken", "broke",
           # "what do you do when your boiler breaks" asks about the fault, and "what do" is how
           # the mechanism ask is worded, so without the present tense here the explainer took it
           # and described how a boiler works to somebody whose heating is off
           "break", "breaks", "breaking", "breakdown", "breaks down", "broke down",
           "fault", "faulty", "error", "leak", "leaks", "leaking", "smell", "smells",
           "smelly", "noisy", "stinks", "stopped", "stuck", "jammed", "repair", "fix",
           "cost", "costs", "price", "prices", "buy", "buying", "best", "recommend",
           # "what is a good air fryer" and "are air fryers any good" ask which one to buy, the
           # commonest shape after "best" and "worth it", and without them here the mechanism
           # took the buying answer away
           "recommends", "recommended", "good", "any good",
           "cheaper", "expensive", "worth", "which", "problem", "trouble", "warranty",
           "guarantee", "install", "installation", "replace", "replacing", "spare",
           "manual", "clean", "cleaning", "descale", "bleed", "empty", "unblock",
           "drain", "quiet", "louder",
           # "what is the wifi password" is a "what is" question about a password, not about
           # wifi: the sticker on the router answers it, and the mechanism was taking it. The
           # same for the things people buy to fix a signal - an extender is a product question.
           "password", "passwords", "passcode", "ssid", "network name", "network key",
           "log in", "log on", "login", "sign in",
           "extender", "extenders", "booster", "boosters", "repeater", "repeaters",
           # Asking what the thing is like is asking for a view, not for the mechanism:
           # "what do you think about air fryers" and "whats your opinion on air fryers" were
           # both answered with how an air fryer cooks, and the taste row that says whether it
           # earns its counter space never got the line. "how does an air fryer work" keeps its
           # explanation, because "think" and "opinion" only appear when someone wants a view.
           "think", "thinks", "thoughts", "opinion", "opinions", "reckon", "your take")


# A symptom means the person wants the thing fixed, and "how does" plus a symptom is still a
# fault: "how does a boiler lose pressure" and "how does my freezer ice up" were both answered
# with the mechanism, which is not the pump-top-up or the defrost at 5mm. These are the shapes
# the fault rows are keyed on, and the mechanism passes on them.
# "leaves streaks" is not one of them: a dishwasher that streaks is a cleaning question, and the
# streak words here only pushed that line onto the hand-washing answer.
SYMPTOM = ("losing pressure", "lose pressure", "loses pressure", "lost pressure",
           "keeps running", "kept running",
           "ice up", "ices up", "icing up", "iced up", "lose suction", "loses suction",
           "lost suction", "not sucking", "no suction", "stopped working", "stops working",
           "not working", "isnt working", "doesnt work", "does not work", "went wrong")


# "what is the cheapest time to put the washing machine on" is a when question spelled with
# "what is", which is the mechanism ask, so the machine's explanation claimed it. The hour is the
# tariff row's question, whatever verb puts the machine on.
THE_HOUR = ("cheapest", "cheaper", "cheap time", "best time", "what time", "night", "overnight",
            "off peak", "off-peak", "economy 7", "in the morning", "in the evening",
            "during the day", "time of day")


def _explain(id, subject, reply, bias=1, avoid=(), guard=None):
    """One explanation, keyed on the thing named plus the ask for its mechanism."""
    named = {"guard": _not_a_how_to_ask if guard is None
             else (lambda understood: _not_a_how_to_ask(understood) and guard(understood))}
    return entry(id, (subject, WORKS), reply, avoid=TROUBLE + SYMPTOM + tuple(avoid),
                 ask=EXPLAIN, bias=bias, **named)


# "what do i do" is how people ask for the job, and "what do" is one of the ways this file reads
# a mechanism ask, so a line that named a thing and then asked what to do was told how the thing
# works: "my dog hates the hoover what do i do" got the fan and the pressure inside the machine,
# and "what do i do in spring" got Hooke's law. The mechanism rows answer what a thing is and how
# it works, so they stand down on the person's own "what do i do" unless the same line says how,
# works, means or inside - the words that ask for the mechanism itself.
_HOW_TO_ASK = re.compile(
    r"\bwhat (?:do|would|can|could|should|shall) (?:i|we) do\b|\bwhat do i do\b|\bwhat now\b",
    re.I)
_ASKS_THE_MECHANISM = re.compile(
    r"\bhow\b|\bwork|\bexplain|\bmean|\binside\b|\bactually\b|\bwhat (?:is|are|s)\b", re.I)


def _not_a_how_to_ask(understood):
    """False when the line asks the person's own what-to-do and never asks how the thing works."""
    read = understood if isinstance(understood, dict) else {}
    said = " ".join(str(read.get("clean") or read.get("text") or "").lower().split())
    if not _HOW_TO_ASK.search(said):
        return True
    return bool(_ASKS_THE_MECHANISM.search(said))


def _not_a_telling(understood):
    """"telly" is one edit from "tells", and the fuzzy match is worth keeping for the nickname.

    "What is a telly" wants how the screen makes a picture, so the word stays in the key; "what
    do i say when a friend tells me she is pregnant" is news you answer with congratulations, and
    the only thing that made it a television was that one-edit match on "tells". A line with a
    telling in it is a person's news, whichever row it lands on.
    """
    words = (understood or {}).get("words") or []
    # "telly" starts with "tell" too, so the nickname is the one word the guard lets through
    return not any(str(word).lower().startswith("tell")
                   and str(word).lower() not in ("telly", "tellies", "tellys")
                   for word in words)


def _not_a_garden_chat(understood):
    """"spring" in a chat about the garden is the season, and the garden answers it."""
    topics = []
    for key in ("topic", "topics"):
        held = (understood or {}).get(key)
        if isinstance(held, str):
            topics.append(held)
        elif isinstance(held, (list, tuple, set)):
            topics.extend(str(one) for one in held)
    if "garden-and-plants" in topics:
        return False
    line = " " + re.sub(r"[^a-z0-9' ]+", " ", str((understood or {}).get("clean")
                                                  or (understood or {}).get("text")
                                                  or "").lower()) + " "
    return not any(" %s " % word in line for word in
                   ("garden", "gardens", "lawn", "grass", "allotment", "allotments", "plot",
                    "borders", "hedge", "hedges", "flowerbed", "flowerbeds", "mow", "mowing"))

def _as_written(words):
    """The letters the row is about, spelled as the row spells them, or the long name.

    A three or four letter key also catches the inflections of longer words: the matcher reads
    "paying" as a form of "pay", and "paye" comes out of that same stem, so the PAYE row answered
    "what should i be paying" with what PAYE stands for - a wage question handed a tax form. The
    row is about the letters, so it wants one of its own words in the line as typed ("paye",
    "pips", "a&e"), or the name written out ("pay as you earn", "personal independence payment").
    A form of another word is not the letters.
    """
    single = tuple(word for word in words if " " not in word)
    phrased = tuple(word for word in words if " " in word)

    def guard(understood):
        text = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
        for word in single:
            if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text):
                return True
        return any(" " + word + " " in text for word in phrased)

    return guard


# An acronym in the line is not always what the line is about. "lol what should i cook tonight"
# and "ok thanks. btw what should i watch tonight" are a laugh and an aside in front of a real
# question, and both were answered with the letters spelled out - the ask word ("what") was the
# only thing the row needed beside the acronym. The spelling-out is the answer only when the ask
# is *of* the acronym: "what does btw mean", "btw stands for what", "explain lol", "how do you
# spell btw", or the acronym on its own.
# "what about" is never the ask: it turns a line into a different subject ("what about only in
# the evenings"), and the answers module puts exactly that in front of every probe it builds from
# a follow-up. So "the wifi keeps dropping / only in the evenings" was answered with what WiFi
# stands for: the probe "what about only in the evenings wifi keep dropping" had "what" 29
# characters before the letters, and "what about" is the one way of saying "what" that asks
# nothing about a word.
_ASK_BEFORE = re.compile(
    r"(?:(?:what|whats|what's)(?!\s+about\b)|what do|what does|what is|what are|explain|explained|define|"
    r"meaning of|stand for|spell|spelled|spelling|how do you spell)\b"
    # the ask and the letters can have a few words between them - "whats the difference between
    # a url and a link" is the letters' question - but not a full stop, which is what separates
    # an aside ("ok thanks. btw ...") from the sentence that follows it
    r"[^.!?]{0,40}$", re.I)
_ASK_AFTER = re.compile(
    r"^[^.!?]{0,24}?(?:mean|means|meaning|stand for|stands for|stood for|short for|spell|"
    r"spelled|spelling)\b", re.I)


def _about_the_word(subject):
    """A guard for one acronym row: true when the line is asking about the letters themselves.

    `subject` is the row's own tuple of spellings, so "e g" and "eg" both count. Read as a guard
    and not as an ask, because an ask is a word anywhere in the line and the whole fault was that
    "what" anywhere in the line is not the same as asking what the letters mean.
    """
    words = [str(one).lower() for one in subject if str(one).strip()]
    pattern = re.compile(
        r"(?<![a-z0-9])(?:" + "|".join(re.escape(one) for one in words) + r")(?![a-z0-9])", re.I)

    def guard(understood):
        text = ((understood or {}).get("clean") or (understood or {}).get("text")
                or " ".join((understood or {}).get("words") or ()))
        text = " ".join(str(text).lower().split())
        if not text:
            return False
        for found in pattern.finditer(text):
            if _ASK_BEFORE.search(text[:found.start()]):
                return True
            if _ASK_AFTER.match(text[found.end():]):
                return True
            # the acronym alone is the question: "btw", "btw?", "lol?"
            if not text[:found.start()].strip(" .!?,-") and not text[found.end():].strip(" .!?,-"):
                return True
        return False

    return guard


def _both(*guards):
    """Two guards on one row: every one of them has to pass.

    The letters rows need both - the letters written as typed, so a form of another word is not
    the letters (#8010), and an ask made of the letters, so "lol what should i cook tonight" is
    the cooking question and not the spelling-out (#9093).
    """
    def guard(understood):
        return all(one(understood) for one in guards)
    return guard


def _name(id, subject, reply, bias=2, avoid=()):
    """One acronym spelled out: the letters asked about, not the mechanism behind them."""
    return entry(id, (subject, ASKS_A_NAME), reply, avoid=TROUBLE + tuple(avoid), ask=EXPLAIN,
                 bias=bias, guard=_both(_as_written(subject), _about_the_word(subject)))


# "Space" is room in a relationship and room on a drive, and it is the one word of the
# drive-size row's key that a person's own life uses. Once that row took a bias it answered
# "how do i tell someone i need space", "i need space" and "how do i tell my mum i need space"
# with 30GB of photos, and the rows for the human ask (`ask-for-space` in wording.py, and the
# family ones) never got the line.
#
# The fence is the phrase, not the person. A person word alone is not the human sense of the
# word: "my daughters 6 next month / we're doing the party at home this year / how many kids is
# too many for a house" has a person in it and no space at all, and standing the drive row down
# for it handed the last line to the kitchen-storage card (spry-08, met at `d3b326e2`). So the
# row stands down only when the line says what the space is *for* - needed, wanted, given, taken,
# asked for, some space, space from, space to myself - and the shape of that is the sentence, not
# who is in it. The device words are the fence the other way: "how much space do i need for
# 10,000 photos" and "i need space on my laptop" keep the card, because the space is on something.
#
# The phrase has a fence of its own, because "need ... space" is also how people ask for room in
# a house: "i need space for a cot", "i need space for a desk", "we need space for a sofa",
# "i need space for a veg patch" (garnet-trout). A thing after "for" is room, a place after
# "in" is room, and a job of work after "to" is time - so those three shapes are not the human
# sense either. What stays is the person or the self after "for" ("space for myself"), "space
# to myself", "space from" and the plain "i need space".

_A_DEVICE_IN_THE_LINE = re.compile(
    r"\b(?:phone|iphone|android|laptop|mac|macbook|pc|computer|desktop|ipad|tablet|drive|disk|"
    r"ssd|hdd|card|console|xbox|playstation|windows|gb|tb|storage|memory|files?|photos?|"
    r"videos?|apps?|downloads?|inbox|mailbox)\b", re.IGNORECASE)

_SPACE_AS_A_NEED = re.compile(
    r"\b(?:need|needs|needed|want|wants|wanted|give|gives|gave|giving|take|takes|took|taking|"
    r"ask|asked|asks|asking)\b[\s\S]{0,24}?\bspace\b"
    r"|\bspace\s+from\b|\bspace\s+to\s+myself\b|\bsome\s+space\b", re.IGNORECASE)

# Room, not a relationship: a thing the space is for, a place the space is in, or a job of work
# the space is to do. The self is the exception on the first one - "space for myself" is the
# human sense and it is one of the five gains this row already makes.
_SPACE_FOR_A_THING = re.compile(
    r"\bspace\s+for\s+(?!(?:myself|me|us|ourselves|yourself)\b)"
    r"(?:(?:a|an|the|my|our|your|his|her|their|some|more|another|two|three|four)\s+)?\w+",
    re.IGNORECASE)

_SPACE_IN_A_PLACE = re.compile(
    r"\bspace\s+(?:in|inside|on)\s+(?:my|our|your|the|a|an|his|her|their)?\s*"
    r"(?:head|heads|mind|flat|house|home|room|rooms|kitchen|bedroom|living\s+room|loft|"
    r"garage|garden|yard|shed|cupboard|wardrobe|bag|case|car|van|luggage)\b", re.IGNORECASE)

_SPACE_TO_DO_A_JOB = re.compile(
    r"\bspace\s+to\s+(?:work|working|study|studying|park|parking|put|build|building|grow|"
    r"growing|plant|planting|store|storing|sit|stand|move|walk|play|cook|exercise|train)\b",
    re.IGNORECASE)


# A size ask with no device named is still the size of a drive: "how much space do i need",
# "how much space should i leave", "space needed for 10000 photos".
_A_SIZE_ASK = re.compile(
    r"\bhow\s+(?:much|many)\b[\s\S]{0,24}?\bspace\b|\bspace\s+(?:needed|required)\b",
    re.IGNORECASE)


# The ask to make room on a device, which the free-up-space row answers better than a size does.
_THE_ASK_TO_MAKE_ROOM = re.compile(
    r"\b(?:more|some|no|little|enough|any)\s+space\b|\bneed\s+space\b|\bneeds\s+space\b"
    r"|\bmake\s+room\b|\bfree\s+up\b|\bfreeing\s+up\b|\bclear\s+(?:some\s+)?(?:room|space)\b"
    r"|\bfull\b|\brunning\s+out\b|\brun\s+out\b|\bout\s+of\s+space\b",
    re.IGNORECASE)


def not_the_space_in_a_relationship(understood):
    """True when the line's "space" is room on a drive, for the drive-size row.

    Capacity words decide first, because a line can name a person and a drive at once ("my mum
    needs more space on her phone", "i need space for my photos") and the drive is the answer.
    Room in a house ("space for a desk", "space in the kitchen", "space to park") and room in a
    life ("space from my mum", "i need some space") stand the row down for the rows that answer
    those. What is left is a bare size ask, which is the drive.
    """
    if not isinstance(understood, dict):
        return True
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    said = str(said)
    if _A_SIZE_ASK.search(said):
        return True
    # A device that needs room is the free-up-space row's question, not a paragraph about how
    # many photos fit on a drive: "i need space on my phone" and "my mum needs more space on her
    # phone" want Settings > Storage and the videos to delete. Naming a device is not enough on
    # its own - "i need space for my photos" and "how much space do i need on my phone" are sizes.
    if _A_DEVICE_IN_THE_LINE.search(said) and not _THE_ASK_TO_MAKE_ROOM.search(said):
        return True
    if _SPACE_AS_A_NEED.search(said):
        return False
    if (_SPACE_FOR_A_THING.search(said) or _SPACE_IN_A_PLACE.search(said)
            or _SPACE_TO_DO_A_JOB.search(said)):
        return False
    return True


ENTRIES = [
    # --- the network, the phone and the signal ----------------------------
    _explain("explain-wifi", ("wifi", "wi fi", "wi-fi", "wireless", "the wireless"),
             "Your router turns the internet into radio waves and your phone's aerial picks them "
             "up, so wifi is only the last few metres - the internet itself arrives at the router "
             "on a phone line or a cable. It uses two bands - 2.4GHz gets through walls better, "
             "5GHz is faster but fades sooner, and water, foil-backed insulation and distance all "
             "weaken it."),
    _explain("explain-internet", ("internet", "the internet", "broadband", "world wide web"),
             "The internet is millions of computers agreeing on one way to pass messages - your "
             "request is cut into small packets, each labelled with where it is going, and routers "
             "hand them on hop by hop until they reach the server. Long fibre cables under the sea "
             "carry it between countries, and the reply usually takes well under a tenth of a "
             "second."),
    _explain("explain-bluetooth", ("bluetooth",),
             "Bluetooth is a short-range radio link, about ten metres, that your phone and the "
             "other device use to talk directly without a network or a router. They hop channels "
             "1,600 times a second so they do not collide with wifi, and pairing is simply the "
             "two agreeing a key once so they recognise each other afterwards."),
    _explain("explain-mobile-data", ("mobile data", "4g", "5g", "3g", "mobile signal",
                                     "phone signal", "mobile internet"),
             "Your phone talks by radio to the nearest mast, and the network passes the "
             "connection from mast to mast as you move - nothing is stored in the air. A city "
             "mast covers a few hundred metres and a rural one several miles, which is why the "
             "same phone is quick in town and slow in a field."),
    _explain("explain-gps", ("gps", "satnav", "sat nav"),
             "Your phone listens to satellites that each carry an atomic clock and broadcast "
             "their exact position and the precise time they sent it. The tiny differences in "
             "when the signals arrive from four of them fix your spot to a few metres - the "
             "satellites never learn where you are, your phone does the sum. Thick buildings and "
             "tunnels block the signals, which is why the arrow jumps there."),
    # "modem" was in this key because people use the two words for the same box, and it meant
    # "what is a modem" was answered with a sentence that began "The router is the box". The box
    # is described either way, so the word modem has its own row in technology.py now.
    _explain("explain-router", ("router", "routers", "hub"),
             "The router is the box that joins your home network to the line from your provider "
             "and gives every device in the house its own address, so they can find each other "
             "and the internet. A modem is the part that speaks to that line; most homes now "
             "have both in one box, which is why turning it off and on fixes so much.",
             # "there is a reset button on my router what does it do" asks what the button does,
             # not what the box is: technology.py's router-factory-reset answers it with the
             # pinhole and what it wipes, and it was losing to this row on the "what does it do"
             # part alone.
             avoid=("reset", "reset button", "factory", "restart", "reboot")),
    _explain("explain-contactless", ("contactless", "contactless card", "contactless payment",
                                     "tap to pay", "apple pay", "google pay", "nfc"),
             "The card holds a chip and a tiny aerial, and the reader's radio field powers them, "
             "so there is no battery to run down. It answers with a one-time code instead of your "
             "real card number and the bank approves it online in under a second, which is why a "
             "number skimmed from a reader is hard to use again."),
    # ATM in a network is not the cash machine, and the letters row stands down for it too: the
    # card that answers with the dispenser is a confident wrong answer to a telecoms question.
    # "Hole in the wall" is also a hole in a wall, and the commonest thing people ask about one is
    # how to fill it: "what do i use to fill a hole in the wall" was answered with how a cash
    # machine pays out, because "what do" is one of the mechanism asks. The ask is now first person
    # only when it is not a how-to (see HOW_TO at the top), and filler words on this entry stand it
    # down for the shapes that do not carry an ask at all.
    _explain("explain-cash-machine", ("cash machine", "atm", "cashpoint", "hole in the wall"),
             "The machine reads the chip or the strip to identify your account, asks your bank "
             "over its own line whether to pay, and only then tells the dispenser how many notes "
             "to peel off. It counts the notes before they reach you and updates the balance "
             "first, which is why a machine that jams usually reverses the debit itself.",
             avoid=("networking", "network", "telecoms", "telecommunications", "packet",
                    "packets", "protocol", "asynchronous transfer", "data link", "broadband",
                    "fill", "filled", "filling", "filler", "plaster",
                    "plasterboard", "drill", "rawlplug", "rawplug", "rawl", "skim", "crack",
                    "cracks", "cracked")),
    _explain("explain-touchscreen", ("touchscreen", "touch screen", "touchscreens",
                                     "touch screens"),
             "A phone screen has a grid of transparent conductors carrying a small charge; your "
             "finger conducts, so it changes the charge where it touches and the grid works out the "
             "spot. That is why a thick glove, a wet finger or a cracked patch misses, because none "
             "of them carries the charge the screen expects."),
    _explain("explain-noise-cancelling", ("noise cancelling", "noise cancelling headphones",
                                          "noise-cancelling", "noise cancelling earbuds"),
             "A microphone on the outside of the headphones listens to the noise and the "
             "headphones play the same sound inverted, so the two waves cancel where they meet "
             "your ear. It works best on steady low sound like engines and least on speech, "
             "which is why you still hear the person next to you."),
    _explain("explain-wireless-charging", ("wireless charging", "wireless charger",
                                           "induction charging", "charging pad",
                                           "charge my phone on a pad"),
             "A coil in the pad and a coil in the phone make a transformer with a gap - the pad's "
             "alternating current makes a magnetic field, and that field drives a current in the "
             "phone's coil. It is the same idea as an electric toothbrush charger, and it is slower "
             "than a cable because some of the energy leaves as heat."),
    _explain("explain-fingerprint", ("fingerprint sensor", "fingerprint", "face id",
                                     "face unlock"),
             "The sensor reads the ridges of your finger - by capacitance, light or ultrasound - "
             "and turns the pattern into a number it compares with the one stored at setup; it "
             "keeps that number, not a picture of your finger. A cut, wet skin or a dirty sensor "
             "changes the pattern enough to fail."),
    _explain("explain-solar-panel", ("solar panel", "solar panels", "solar pv", "photovoltaic",
                                     "solar power"),
             "Sunlight knocks electrons loose in a layer of silicon, and the layers either side "
             "are treated so they push those electrons one way, making a current; an inverter "
             "then turns it into the mains electricity the house uses. Output falls sharply in "
             "shade rather than a little, because a shaded cell blocks the flow through the "
             "whole panel."),
    _explain("explain-led", ("led", "led bulb", "led light", "led lights", "light bulb",
                             "lightbulb"),
             "An LED is a sliver of material that gives out light when current flows through it, "
             "because electrons dropping across a gap release energy as photons. Almost none of "
             "the energy becomes heat, which is why a 9W LED matches an old 60W bulb, and white "
             "ones are blue LEDs with a yellow coating that mixes to white."),
    _explain("explain-radio", ("radio", "radio waves", "fm radio", "am radio", "car radio"),
             "A station puts the sound onto a carrier wave, varying its strength (AM) or its "
             "frequency (FM), and your aerial picks up every wave in the air at once. The tuner "
             "keeps the one frequency you want and the circuit turns its variations back into "
             "sound, which is why a weak station hisses."),
    # "telly" is one edit away from "tells", so "what do i say when a friend tells me she is
    # pregnant" matched this row on the fuzzy match and was answered with how a screen makes a
    # picture. The nickname stays, with a guard that keeps the telling out (see `_not_a_telling`).
    _explain("explain-tv-screen", ("tv", "television", "telly", "oled", "screen"),
             "A modern screen is a grid of millions of pixels, each with red, green and blue "
             "lights under it, and the picture is just each one being told how bright to be for "
             "that frame. A new frame goes up 50 or 60 times a second, faster than your eye "
             "follows, which is what makes it look like smooth movement.",
             # the size and the numbers on the box are a shopping question and a spec
             # question, not the mechanism
             avoid=("inch", "inches", "size", "big", "4k", "8k", "1080", "1080p", "uhd", "hdr",
                    "resolution",
                    # keeping the glass whole is a what-to-do question, not a what-is question:
                    # "what is the best way to protect my phone screen" was answered with how a
                    # screen makes a picture, because "screen" plus "what is" is this row's key
                    # and the protector's row says "how do i". The doing words stand it down.
                    "protect", "protecting", "protection", "protector", "protectors",
                    "prevent", "preventing", "cracking again", "crack again", "tempered glass",
                    "raised lip", "keep it whole", "keep it safe", "keep it from cracking",
                    # a mark on the glass is the cleaning row, not the mechanism: "what is the
                    # best way to wipe a phone screen" was told how a pixel makes a picture,
                    # because "what is the best way" is an explanation ask
                    "clean", "cleaning", "cleaned", "wipe", "wiping", "smudge", "smudges",
                    "smear", "smears", "fingerprint", "fingerprints", "greasy", "scratch",
                    "scratches", "scratched", "dust"),
             guard=_not_a_telling),
    entry("explain-tv-resolution",
          (("4k", "8k", "1080p", "720p", "uhd", "hd", "full hd", "resolution", "hdr"),
           ("mean", "means", "what is", "what's", "whats", "difference", "better", "worth",
            "need")),
          "4K means about 4,000 pixels across the screen - 3,840 by 2,160, which is four times the "
          "detail of a 1080p set. Whether you see it depends on size and distance - on a 55-inch "
          "screen from a sofa it is subtle, and HDR, the brightness and colour range, changes the "
          "picture far more.",
          avoid=TROUBLE, ask=EXPLAIN, bias=1),
    _explain("explain-qr-code", ("qr code", "qr codes", "barcode", "bar code", "barcodes"),
             "A barcode is a pattern of bars that a scanner reads back as a number, with a check "
             "digit so a misread is caught. A QR code does the same in two directions and holds a "
             "whole web address, and it carries error correction - up to about a third of it can be "
             "damaged or covered and still scan."),

    # --- the kitchen and the laundry --------------------------------------
    _explain("explain-washing-machine", ("washing machine", "washing machines", "washer"),
             "It fills the drum, tumbles the clothes through hot water and detergent, then spins "
             "them fast so the water is flung out through the holes. Detergent lifts grease off "
             "the cloth and the paddles in the drum do the rubbing, which is why an overfilled "
             "drum comes out still dirty - the clothes cannot move.", avoid=THE_HOUR),
    # "how does a dish washer work" is the same machine spelled apart, and it was answered with
    # the washing machine's drum because "washer" is one of that row's words
    _explain("explain-dishwasher", ("dishwasher", "dishwashers", "dish washer", "dish washers"),
             "It sprays hot water and detergent at the dishes from arms that rotate, then rinses "
             "and dries the load with the heat of the last rinse. The salt softens hard water so "
             "the detergent can work and the rinse aid makes the water run off instead of drying "
             "in spots; neither cleans anything by itself.", avoid=THE_HOUR),
    _explain("explain-tumble-dryer", ("tumble dryer", "tumble drier", "tumbledryer",
                                      "condenser dryer", "heat pump dryer"),
             "It tumbles the clothes through warmed air, and the damp air is either blown outside "
             "through a vent or cooled so the water condenses and collects in a drawer. A "
             "heat-pump dryer heats that air again instead of dumping it, so it uses about half "
             "the electricity and takes longer."),
    _explain("explain-air-fryer", ("air fryer", "air fryers", "airfryer"),
             "It is a small oven with a strong fan - the element sits at the top and the fan blows "
             "the hot air round the food fast, so the outside browns much as it would in oil. That "
             "is why food needs one layer and a shake halfway, and why it crisps quicker than a big "
             "oven - there is far less air to heat."),
    _explain("explain-electric-toothbrush",
             ("electric toothbrush", "electric toothbrushes", "sonic toothbrush"),
             "A small motor in the handle shakes the head a few thousand times a minute, far "
             "faster than a hand can scrub, so it breaks plaque up by vibration rather than by "
             "pressure. That is why you guide it slowly along the gumline, and why pressing hard "
             "makes it clean worse instead of better."),
    _explain("explain-kettle", ("kettle", "kettles", "electric kettle"),
             "An element under the water gets hot and the water round it rises, so a current "
             "stirs the kettle and it heats from the bottom up. A strip of two metals that bend "
             "as they warm cuts the power when steam reaches it, which is why a kettle switches "
             "itself off and why limescale round that strip makes one boil on.",
             # the scale on the inside is a cleaning question, not how a kettle works: "kettle
             # full of scale what do i use" and "my kettle is furred up what do i use" were told
             # how the element heats the water. Not the bare "limescale", because the row's own
             # sentence is about limescale on the strip.
             # A line that names a boiler is the heating's, and the word that brought it here is
             # "kettling" - the noise a scaled boiler makes, not the thing on the worktop. The
             # sound report reached `boiler-kettling` on its own ("my boiler is making a kettling
             # noise"), but a line that went on to ask about it ("my boiler has started making a
             # noise like kettling what is that") was read as a "what is a kettle" ask and got how
             # the element heats the water. The boiler stands this row down whatever the rest of
             # the line asks.
             avoid=("full of scale", "scaled up", "scaled inside", "furred up", "furring up",
                    "chalky", "white bits", "white flakes", "descale", "descaling",
                    "descaled", "descaler", "white stuff in",
                    "boiler", "boilers", "combi", "central heating", "heat exchanger",
                    "radiator", "radiators")),
    _explain("explain-toaster", ("toaster", "toasters"),
             "Thin wires inside, usually nichrome, glow red when current passes and the bread "
             "absorbs that as radiant heat. A latch holds the bread down against a spring and a "
             "timer or heat sensor lets it go, and the gap to the wires sets how evenly it "
             "browns - too close and the edges burn before the middle dries."),
    _explain("explain-oven-heat", ("oven", "ovens", "fan oven", "electric oven", "gas oven"),
             "Elements at the top, bottom or back heat the air, and a thermostat switches them on "
             "and off to hold the temperature on the dial. A fan oven blows that air around, so "
             "it browns more evenly and cooks about 20C cooler and a little faster than a "
             "conventional one; the dial is only an average, which is why an oven thermometer "
             "earns its place.",
             # a dutch oven and a casserole dish are pots, and the row that answers what a
             # piece of kit is owns them: "what is a dutch oven" was getting the heating
             # elements card here, because the word "oven" is in both.
             avoid=("dutch oven", "dutch ovens", "casserole dish", "casserole dishes",
                    "ovenproof dish", "baking dish", "cast iron pot", "braiser")),
    _explain("explain-freezer", ("freezer", "freezers"),
             "It is the fridge's colder twin - a pump circulates a refrigerant that expands and "
             "gets very cold, taking heat out of the air, and the heat leaves at the back. Because "
             "it holds food far below 0C, the water in it turns to ice, and ice keeps almost all "
             "the food's water locked up, so the bugs that spoil food cannot grow.",
             # "and whats in my freezer" is a question about the person's own kitchen, not about
             # how a freezer works: the fridge and freezer mechanism rows were taking those
             # follow-ups, so they stand aside when the line says whose appliance it is
             avoid=("in my", "in mine", "in our", "in the freezer", "in there", "have i got",
                    "what have i", "left in", "left over", "leftover", "leftovers", "gone off",
                    "out of date", "defrost", "defrosting")),

    # --- the heating and the house ---------------------------------------
    entry("explain-fridge-cold", (("fridge", "refrigerator"),
                                  ("keep food", "keeping food", "keeps food", "food cold",
                                   "keep it cold", "keep things cold", "stay cold", "stays cold",
                                   "keeping it cold", "keeps it cold")),
          "A pump moves a refrigerant round a sealed loop, and inside the fridge a pipe lets it "
          "expand, so it turns very cold and takes heat out of the food. A compressor then squeezes "
          "it, and the heat leaves from the coil at the back, because that is where it is dumped - "
          "which is why the back feels warm. "
          "Cold air is denser, so it sinks - which is why the bottom shelf is the coldest.",
          # "how long does a fridge keep food" is a storage-life question, not a mechanism one
          avoid=TROUBLE + ("how long", "last", "lasts", "days", "weeks", "store", "stored",
                           "storage", "safe", "freeze", "freezer",
                           # whose fridge it is, and what is in it, is a kitchen question
                           "in my", "in mine", "in our", "in the fridge", "in there",
                           "have i got", "what have i", "left in", "left over", "leftover",
                           "leftovers", "gone off", "out of date"),
          ask=EXPLAIN, bias=1),
    entry("explain-phone-location", (("phone", "google maps", "maps", "satnav", "sat nav",
                                      "location"),
                                     ("know where", "where i am", "where am i", "track me",
                                      "tracking me", "find me", "locate me")),
          "Your phone works it out from three things - the satellites it can see, which give the "
          "position to a few metres, the wifi networks nearby, which the phone recognises by the "
          "addresses they broadcast, and the masts it is attached to. Indoors, where satellites are "
          "blocked, the wifi list does most of the work, which is why it can place you in a "
          "building.",
          avoid=TROUBLE + ("turn off", "off", "disable", "stop", "share", "sharing", "privacy",
                           "settings", "battery", "data"), ask=EXPLAIN, bias=1),
    _explain("explain-radiator", ("radiator", "radiators"),
             "Hot water from the boiler flows through the radiator, warms the metal, and the air "
             "next to it warms, rises and pulls cooler air in across the floor. Most of the heat "
             "reaches the room that way rather than by the panel glowing, which is why a shelf "
             "above one or a sofa in front of one wastes it.",
             # the valve's controls are not how heat reaches the room: "what do the numbers on a
             # radiator valve mean" was answered with this explanation
             avoid=("numbers", "number", "dial", "trv", "thermostatic", "snowflake", "setting",
                    "settings", "turn down", "turn up")),
    # The explanation answers "how does a boiler work". A boiler with something wrong with it is
    # the boiler fault rows' question, and "my boiler pressure is low what do i do" was told how a
    # burner and a pump work because "pressure" and "low" were in neither TROUBLE nor SYMPTOM.
    _explain("explain-combi-boiler", ("combi boiler", "boiler", "boilers", "central heating",
                                      "gas boiler"),
             "A burner heats water and a pump sends it round the radiators; the water comes back "
             "cooler and is heated again. A combi boiler makes hot water on demand straight from "
             "the cold mains when you open a tap, which is why a second tap running drops the "
             "temperature, while a system with a hot tank serves two at once.",
             avoid=("pressure", "low pressure", "bar", "gauge", "filling loop", "topped up",
                    "top it up", "top up", "drop", "dropped", "dropping", "losing", "lost",
                    "cold radiators", "radiators are cold", "no hot water", "no heating",
                    "lockout", "locked out", "kettling", "condensate")),
    _explain("explain-heat-pump", ("heat pump", "heat pumps", "air source heat pump",
                                   "ground source heat pump"),
             "A heat pump works like a fridge in reverse - it takes heat from the air or ground "
             "outside, which is always warmer than absolute zero, squeezes it to a higher "
             "temperature and puts it into your radiators. Because it moves heat rather than making "
             "it, a well-fitted one gives about three units of heat per unit of electricity, "
             "against one for a bar fire."),
    _explain("explain-thermostat", ("thermostat", "room thermostat", "heating dial"),
             "A room thermostat is a switch that reads the air - when the room reaches the set "
             "temperature it stops asking the boiler for heat, and it starts again a degree or two "
             "lower. Turning it up does not heat the room faster, only further - the boiler flow "
             "temperature and the size of the radiators set the speed."),
    _explain("explain-smoke-alarm", ("smoke alarm", "smoke detector", "fire alarm"),
             "An optical alarm has a light and a sensor in a chamber, and smoke drifting in "
             "scatters the light onto the sensor, which sets it off. An ionisation one passes a "
             "tiny current through the air and smoke changes it. Optical ones catch smouldering "
             "fires sooner and ionisation ones catch flames, which is why both are sold."),
    # "vacuum" is also the word in a vacuum flask and a vacuum-packed bag, and a flask has no
    # fan in it: the suction answer to "how does a vacuum flask work" is the wrong machine.
    # This is an entry() rather than an _explain() because of one word: "how does a vacuum
    # cleaner suck up dirt" is the deck's own line and it went to a shrug, as "suck" is a
    # single slip from TROUBLE's "stuck" and a slip near an avoid word turns the whole entry
    # down. The bare word goes; the phrases that mean a jammed machine stay.
    entry("explain-vacuum-cleaner",
          (("vacuum cleaner", "hoover", "vacuum", "vacuuming"), WORKS),
          "A fan pulls air out of the machine, so the pressure inside drops and the air "
          "outside pushes in through the nozzle, carrying dust with it. The bag or the cyclone "
          "lets the air through but not the dust; a full bag, a blocked hose or a clogged "
          "filter cuts the flow, which is why the suction fades.",
          avoid=tuple(word for word in TROUBLE if word != "stuck") + (
              "flask", "flasks", "thermos", "vacuum packed", "vacuum pack",
              "food saver", "sealer", "stuck hose", "stuck brush", "is stuck", "get stuck",
              "gets stuck", "got stuck", "stuck on"),
          # this row is an entry() and not an _explain(), so it asks for the same fence by hand:
          # "my dog hates the hoover what do i do" is the dog's problem, not the fan's
          guard=_not_a_how_to_ask,
          ask=EXPLAIN),
    # The flask is the other thing called a vacuum, and the trick is the opposite one: the gap
    # between the two walls is emptied so heat has nothing to travel through.
    _explain("explain-vacuum-flask", ("vacuum flask", "thermos", "thermos flask",
                                      "vacuum jug", "flask"),
             "A flask is two walls of glass or steel with the air taken out of the gap between "
             "them, so there is nothing left for heat to travel through: no air to carry it "
             "(convection) and almost none to conduct it. The shiny coat on the inside reflects "
             "radiant heat back, and the stopper stops heat escaping out of the top, which is why "
             "a flask keeps soup hot all day if it is filled right to the top."),
    _explain("explain-toilet-flush", ("toilet", "toilets", "cistern", "loo"),
             "Pressing the handle lifts a flap and the water in the cistern rushes down, and the "
             "shape of the pan carries it round and over the bend, so the lot siphons away in one "
             "go. The fill valve then refills the cistern and a float shuts it off - a cistern "
             "that keeps hissing is usually that valve, not the flush.",
             # A phone that went down the toilet is the phone's problem, not a question about how
             # a flush works: "i dropped my phone in the toilet what do i do" was explained the
             # flap and the siphon (@ivory-magnet, #9232 family).
             # (no word built on "flush" in this list: the loose match reads "flushed" as the
             # "flush" in "how does a toilet flush work" and the explanation lost its own line)
             avoid=("phone", "phones", "iphone", "mobile", "keys", "dropped", "dropped it",
                    "fell in", "went in", "down the toilet")),
    # Machines people ask about and nothing answered: the car, the doorbell, the machines that
    # treat the air and the water, and the phone itself. Each is one row, keyed on the thing plus
    # the ask, so the repair entries keep their troubles (see TROUBLE).
    _explain("explain-car-engine", ("car engine", "car engines", "engine", "engines",
                                   "petrol engine", "diesel engine"),
             "A car engine burns fuel in short bursts inside a cylinder: a piston slides down "
             "sucking in air and fuel, the spark or the heat of compression sets it alight, the "
             "bang drives the piston back, and the exhaust is pushed out before it starts again - "
             "four strokes, thousands of times a minute. A diesel has no spark plug and squeezes "
             "the air far harder, which is why it is noisier and more economical.",
             # "wrong fuel", "engine light" and the rest are the car entries' troubles
             avoid=("wrong fuel", "misfuel", "filled", "petrol in", "diesel in", "light",
                    "warning", "overheat", "overheating", "smoke", "cut out", "stalls",
                    "stalling", "start", "starting", "wont", "noise", "noisy", "rattle",
                   # an oil question is the car table's, not a description of the four strokes:
                   # "i overfilled my engine oil what do i do" was explained a piston instead.
                   "oil", "oils", "overfill", "overfilled", "overfilling", "dipstick",
                   "sump", "coolant",
                    # a jet is not a car engine: it has no pistons to explain
                    "jet", "jets", "turbine", "rocket", "plane", "aircraft", "boat", "outboard"),
             bias=2),
    _explain("explain-jet-engine", ("jet engine", "jet engines", "turbine", "jet", "turbofan"),
             "A jet is a fan in a tube: the fan sucks air in, the compressor squeezes it, fuel is "
             "burned in that air and the hot gas blasts out of the back. The push comes from "
             "throwing that gas backwards, and the same shaft also drives the fan that keeps "
             "feeding it - which is why a jet works best at speed and high up, where the air is "
             "thin.",
             # a wind turbine is the same word for a different machine, and the jet answer was
             # being given to "how does a wind turbine work"
             avoid=("wind", "windy", "wind farm", "wind farms", "windmill", "wind power",
                    "solar", "renewable", "renewables")),
    _explain("explain-wind-turbine", ("wind turbine", "wind turbines", "wind farm",
                                      "wind farms", "windmill", "wind generator"),
             "A turbine is the jet's opposite: wind pushes the blades, the blades turn a shaft "
             "through a gearbox, and a generator turns that spin into electricity. The blades "
             "are long and thin because the force goes up with the square of their length, and "
             "the machine feathers them out of the wind when it is too strong to use.",
             avoid=("noisy", "noise", "broken", "not working", "install", "cost", "grant",
                    "planning permission", "home", "garden", "buy", "best", "which",
                    "offshore")),
    _explain("explain-fuse", ("fuse", "fuses", "plug fuse", "fuse box"),
             "A fuse is a short strip of wire that melts before the rest of the circuit does: "
             "overload it and the wire heats past its melting point and breaks the circuit, so "
             "the wiring and the flex behind the wall never take the heat. Fixing the cause is "
             "the point - a fuse that blows twice is a fault, not bad luck.",
             avoid=("keeps blowing", "blowing", "blows", "blew", "tripping", "trip", "rewire",
                    "rewiring", "replace", "replacing", "which", "what size", "rating",
                    "amp", "amps", "change", "changing", "plug", "sockets", "socket")),
    _explain("explain-barometer", ("barometer", "barometers", "aneroid barometer"),
             "A barometer weighs the air: inside is a sealed metal capsule with most of the air "
             "pumped out, and a spring or a column of mercury balances the outside pressure "
             "against it. As the pressure rises the capsule is squeezed and the needle climbs, "
             "so a falling barometer means a low coming and the weather on its way down too.",
             avoid=("which", "best", "buy", "app", "phone", "weather station", "read", "reading",
                    "setting",
                    # how a barometer foretells rain is the weather question, and the water cycle
                    # answers it better than the capsule does
                    "rain", "rainy", "forecast", "weather tomorrow", "storm")),
    _explain("explain-tyre", ("tyre", "tyres", "tire", "tires", "car tyre", "car tyre's"),
             "A tyre holds air, and the air carries the car: the rubber only has to keep the "
             "shape, which is why the pressure in it decides how much tread stays on the road. "
             "Where the rubber touches, it grips by pressing into the surface and by the rubber "
             "squirming in the grooves, and water has to escape through the tread or the tyre "
             "rides up on it and aquaplanes.",
             avoid=("pressure", "puncture", "punctured", "flat", "blowout", "worn", "wear",
                    "tread depth", "legal", "replace", "replacing", "cost", "which", "best",
                    "winter", "summer", "snow", "chains", "mots", "mot", "swap")),
    _explain("explain-doorbell", ("doorbell", "door bell", "door chime", "chime", "bell push"),
             "A wired bell is a circuit interrupted by the button: press it, the circuit closes, "
             "and an electromagnet pulls a plunger that strikes a bar - the ding - then lets it "
             "drop back on a spring for the dong. Wireless ones skip the wire: the button sends a "
             "coded radio pulse to the chime, which is why a nearby bell can answer someone "
             "else's push.",
             avoid=("not", "isnt", "isn't", "doesnt", "doesn't", "wont", "won't", "battery",
                    "replace", "broke", "fault")),
    _explain("explain-dehumidifier", ("dehumidifier", "dehumidifiers", "dehumidify"),
             "A fan pulls the room's air over cold coils, and cold air cannot hold as much water "
             "vapour, so the water condenses on the metal and drips into the tank while the dried "
             "air goes back into the room. It works best with the doors shut and the tank empty, "
             "because a machine that fills up stops, and it will not dry a room that is open to "
             "the rest of the house."),
    _explain("explain-water-softener", ("water softener", "water softeners", "softened water",
                                        "hard water"),
             "The water runs through a tank of resin beads that hold on to calcium and magnesium "
             "and swap them for sodium, which is what makes the water soft. Every few days the "
             "machine rinses the beads with salty water to strip the calcium off again, which is "
             "why a softener needs a bag of salt far more often than anything else."),
    _explain("explain-electric-car", ("electric car", "electric cars", "ev", "electric vehicle",
                                      "electric van"),
             "Batteries feed a motor that turns the wheels directly, so there is no gearbox to "
             "shift and full pull is there from a standstill. Lifting off turns the motor into a "
             "generator that pushes power back into the battery - that is the regenerative "
             "braking - and the brake pedal blends that with the real brakes so you rarely use "
             "them up."),
    _explain("explain-hybrid-car", ("hybrid car", "hybrid cars", "hybrid vehicle",
                                    "plug in hybrid", "plug-in hybrid", "plugin hybrid",
                                    "self charging hybrid"),
             "A hybrid has a petrol engine and an electric motor and the car picks which to use: "
             "the motor pulls away from a stop and creeps in traffic, the engine takes over once "
             "you are moving, and braking turns the motor into a generator that refills the small "
             "battery. A self-charging one is never plugged in, so it holds only a mile or two of "
             "electric running and the saving is in town; a plug-in does 20 to 40 miles on "
             "electric before the engine starts.",
             bias=1,
             # hybrid working is a different subject, and its words are in the line whenever it
             # is that question rather than the car. "working" alone is not one of them: the car
             # question is asked as "how does a hybrid car work", and a fence on the bare word
             # stood this row down on its own line.
             avoid=("working from home", "work from home", "hybrid working", "hybrid work",
                    "office", "pattern", "my job", "employer")),
    _explain("explain-mobile-phone", ("mobile phone", "mobile phones", "cell phone", "smartphone",
                                      "mobile", "phone call"),
             "The phone is a radio with a small computer in it: it finds the nearest mast, tells "
             "the network it is there, and every call or page is passed from mast to mast as you "
             "move. The aerial on a mast covers a few hundred metres in town, which is why the "
             "same phone works in one room and not the next.",
             # a phone that will not ring or will not hold a signal is a fault, not a mechanism
             avoid=("signal", "reception", "no service", "not working", "wont", "won't", "battery",
                    "charge", "charging", "screen", "cracked", "update", "bill", "contract",
                    "upgrade", "sim", "e sim", "esim", "roaming", "abroad"),
             bias=1),
    _explain("explain-lift", ("lift", "lifts", "elevator", "elevators"),
             "A car hangs on steel ropes that pass over a pulley at the top, and a counterweight "
             "on the other end weighs about the same as the car plus half a load, so the motor "
             "only has to shift the difference. A governor trips a brake that grips the guide "
             "rails if the car falls faster than it should, and the doors will not open unless "
             "the car is level with a floor.",
             avoid=("stuck", "stuck in a lift", "broken", "not working", "out of order",
                    "noise", "noisy", "shaking", "jerky", "mirror", "weight", "lift weights",
                    "lift my", "give a lift", "lift share", "carpool", "ski lift"),
             bias=1),
    _explain("explain-ballpoint-pen", ("ballpoint pen", "ballpoint", "biro", "ball pen",
                                       "pen"),
             "The tip is a tiny ball in a socket, and the ink behind it is thick enough that it "
             "only runs when the ball rolls it onto the paper - which is why a pen works upside "
             "down and why the line stops when the ball dries out. The ink is oil based, so it "
             "dries on the paper fast but smears if you write over it while it is still wet.",
             avoid=("leaking", "leaks", "leaked", "stained", "stain", "shirt", "ink on",
                    "run out", "ran out", "dried out", "best pen", "which pen", "fountain",
                    "pencil", "what pen"),
             bias=1),
    _explain("explain-microphone", ("microphone", "microphones", "mic", "mics"),
             "A diaphragm inside moves when sound pushes on it, and that movement is turned into "
             "an electrical signal that copies the shape of the sound wave. A condenser mic "
             "charges that diaphragm and needs power; a dynamic one uses a coil in a magnet and "
             "needs none, which is why a stage mic is the one that can be dropped.",
             avoid=("not working", "muted", "mute", "zoom", "teams", "headset", "which",
                    "best", "cheap", "buy", "settings", "permission", "echo"),
             bias=1),
    _explain("explain-speaker", ("speaker", "speakers", "loudspeaker", "bluetooth speaker",
                                 "soundbar"),
             "A magnet and a coil push a cone in and out in time with the signal, and the "
             "moving cone moves the air, which is the sound. A small cone cannot shift much air, "
             "so it makes the high notes well and the bass not at all: that is why a speaker "
             "with a big cabinet and a port sounds fuller at the same volume.",
             avoid=("not working", "no sound", "crackling", "crackle", "quiet", "volume",
                    "which", "best", "cheap", "buy", "connect", "pair", "pairing", "tv",
                    "party", "outdoor", "waterproof"),
             bias=1),
    _explain("explain-camera", ("digital camera", "camera", "cameras", "dslr", "mirrorless"),
             "A lens focuses light onto a sensor covered in millions of tiny light counters, and "
             "each one records how much light landed on it. The sensor reads out those numbers, "
             "and the processing turns them into the picture - which is why a bigger sensor with "
             "bigger counters beats more of them on a small one when the light is poor.",
             avoid=("phone camera", "not working", "blurry", "blurred", "photos are", "which",
                    "best", "cheap", "buy", "lens", "memory card", "sd card", "setting",
                    "settings", "trail camera", "doorbell", "security",
                    # a speed camera is the other row's: the photograph is the evidence, not
                    # the sensor
                    "speed camera", "traffic camera", "average speed", "cctv", "dash cam"),
             bias=1),
    _explain("explain-printer", ("printer", "printers", "inkjet", "laser printer"),
             "An inkjet squirts tiny drops of ink onto the page from a head that sweeps across "
             "it; a laser draws the page with static charge on a drum, dusts it with powder and "
             "fuses the powder on with heat. The inkjet dries out if it sits unused, and the "
             "laser's powder does not, which is the trade most people are choosing between.",
             avoid=("not working", "wont print", "won't print", "jam", "jammed", "streaky",
                    "faded", "offline", "wifi", "wireless", "connect", "driver", "ink",
                    "cartridge", "toner", "which", "best", "cheap", "buy"),
             bias=1),
    _explain("explain-zip", ("zip", "zips", "zipper", "zippers"),
             "Two rows of teeth face each other on tapes, and a slider pulls them together or "
             "apart: a wedge inside the slider forces each pair of teeth to interlock as it "
             "passes, and the same slider spreads them when it goes the other way. A zip fails "
             "when the slider wears and stops forcing the teeth together, which is why a stuck "
             "or split zip often mends when the slider is squeezed a little tighter.",
             avoid=("file", "files", "folder", "unzip", "unzipped", "compressed", "extract",
                    "download", "email", "attachment", "too big", "rar", "7z",
                    "zip a folder", "make a zip", "zip file", "zip my"),
             bias=1),
    _explain("explain-lock", ("lock", "locks", "yale lock", "door lock", "padlock",
                              "key", "keys"),
             "A pin-tumbler lock has pairs of pins resting across the plug and the barrel, and "
             "the key's ridges lift each pair until the break between them sits exactly at the "
             "line the plug turns on. Once every pair is level the plug can turn; the wrong key "
             "leaves one pin too high or too low, and that is what picking and bump keys attack.",
             # Now that the key is named here, the lines about a key rather than about a lock
             # arrive too: a lost key, a key that will not turn, a key to be cut, a car key. Each
             # of them has its own answer, and none of them wants the inside of the barrel.
             # "key cut"/"cut a key" rather than "cut", so a mortice is still a job for a chisel.
             avoid=("lost", "lose", "losing", "misplaced", "misfiled", "cant find", "can't find",
                    "spare", "spares", "key cut", "cut a key", "copy", "duplicate",
                    "locksmith", "locked out", "locked inside", "locked in", "locked myself",
                    "stuck", "ignition", "key fob", "keys locked",
                    # the key in music is a home note, and this row was answering "what is a
                    # musical key", "what is a key signature" and "what is a key in music" with
                    # the inside of a pin-tumbler barrel
                    "music", "musical", "in music", "song", "songs", "tune", "tunes",
                    "chord", "chords", "octave", "scale", "tempo", "key signature",
                    # "keyboard" is deliberately not here: "what is a key on a keyboard" is the
                    # row above the letters, and it keeps the answer it has
                    "guitar", "piano", "band", "album", "melody"),
             bias=2),
    # The small hardware of a house has no owner: "how does a hinge work" and "how does a
    # spring work" were the search hedge, and the tap question was answered with the stopcock
    # steps. Each row keys the thing named plus the ask, so the fault lines for the same thing
    # ("my hinge is loose", "how do i stop a hinge squeaking") stay with their own answers.
    _explain("explain-hinge", ("hinge", "hinges", "door hinge", "cupboard hinge"),
             "A hinge is two leaves joined by a pin that runs through interlocking knuckles, so "
             "one leaf swings on the pin while the other stays screwed to the frame. The whole "
             "weight of the door hangs on that pin, which is why a hinge lasts far longer "
             "greased than it does dry.",
             avoid=("squeak", "squeaks", "squeaking", "squeaky", "loose", "loosely", "stiff",
                    "dropped", "drooping", "sagging", "sag", "oil", "oiled", "grease",
                    "adjust", "adjusting", "hang", "hanging", "rehang", "fit", "fitting")),
    # The metal is not what a garden chat is asking about: "what do i do in spring", on the
    # turn after a lawn question, was this card because the ask framed the season as the thing
    # to explain. In a chat about the garden the word is the season, and the garden has its own
    # answer for it.
    _explain("explain-spring", ("spring", "springs", "coil spring", "a spring"),
             "A spring stores energy by bending steel, and the steel gives it back only while "
             "it is strained within its elastic limit - pull a coil a little and it straightens "
             "and returns, pull it past that point and it stays stretched. That limit is why a "
             "spring is rated for a weight and sags once it is asked for more.",
             avoid=("mattress", "mattresses", "trampoline", "sagging", "sagged", "broken",
                    "snapped", "rusted", "stiff", "bouncy", "bounce", "sofa", "bed",
                    # "spring" is a tide, a roll, a watch, a water, an onion and a season, and
                    # every one of them has its own answer: the moon for the tide, the pastry,
                    # the balance wheel, the bottle, the crop and the calendar.
                    "tide", "tides", "roll", "rolls", "onion", "onions", "watch", "watches",
                    "clock", "clocks", "balance", "cleaning", "clean", "water", "bulbs",
                    "plant", "planting", "season", "equinox", "holiday", "weather", "chicken",
                    # and the season is the garden's question, so a garden or a lawn named
                    # beside it takes the turn: "what do i do to my lawn in spring" was the
                    # steel-spring card, because "spring" was its only word in common.
                    "lawn", "lawnmower", "grass", "mow", "mowing", "garden", "gardens",
                    "plot", "allotment", "allotments", "borders", "flowerbeds", "hedge",
                    "hedges", "shrubs", "sow", "sowing", "prune", "pruning", "grow",
                    "growing", "weeds", "weeding"),
             guard=_not_a_garden_chat),
    _explain("explain-mirror", ("mirror", "mirrors", "bathroom mirror"),
             "A mirror is glass with a thin layer of silver or aluminium on the back, and light "
             "bounces off that layer at the same angle it arrived - in at 30 degrees, out at 30 "
             "degrees, which is why you see yourself where the reflection says you are. The "
             "glass only protects the silver, so a mirror that has gone patchy has lost that "
             "coating rather than got dirty.",
             avoid=("hang", "hanging", "hang it", "put up", "remove", "removing", "stick on",
                    "drill", "clean", "cleaning", "steamed", "steamy", "smear", "smears",
                    "buy", "best", "which", "lighted", "led")),
    _explain("explain-fan", ("fan", "fans", "electric fan", "desk fan", "ceiling fan"),
             "A fan does not cool the air, it moves it: the air passing over your skin takes "
             "heat away and speeds up the sweat evaporating, so you feel cooler while a fan "
             "left running in an empty room changes nothing. Ceiling fans work best blowing "
             "down in summer and pulling up in winter, which stirs the warm air off the ceiling.",
             avoid=("noisy", "noise", "rattles", "rattling", "wobbles", "wobbling", "broken",
                    "stopped", "not working", "clean", "cleaning", "dust", "extractor",
                    "bathroom", "oven", "cooker", "buy", "best", "which")),
    _explain("explain-pump", ("pump", "pumps", "water pump", "a pump"),
             "A pump moves water by pushing it: a spinning impeller flings water outwards into "
             "the casing, or a piston shoves it along, and the pressure it builds is what drives "
             "the flow. Pumps push rather than pull, which is why air in the pipe stops one "
             "lifting water and a pump that has lost its prime has to be filled again.",
             avoid=("broken", "noisy", "noise", "leaking", "leaks", "not working", "stopped",
                    "replace", "repair", "fix", "install", "cost", "buy", "best", "which",
                    "heat pump", "air source", "ground source", "bike", "tyre", "tire",
                    # a fuel pump, a sump pump and a spray pump are other machines with other
                    # answers: a petrol smell is the car, a wet basement is the sump
                    "fuel", "petrol", "diesel", "sump", "spray", "breast")),
    # "sump" is fenced off the pump row above because a wet cellar is not a water system, and
    # with no card of its own the sump went to a shrug instead of the machine's own answer.
    _explain("explain-sump-pump", ("sump pump", "sump", "sump pumps", "basement pump",
                                   "cellar pump", "wet basement pump"),
             "A sump pump sits in a pit at the lowest point of a cellar and switches itself on "
             "when water rises in the pit: a float tips, the impeller starts, and the water goes "
             "out through a pipe to a drain, a soakaway or the garden. The check valve just above "
             "the pump stops that water running back down, so a pit that keeps refilling with the "
             "pump switched off is usually the valve, and a pump that runs and moves nothing is "
             "usually a blocked inlet or a frozen discharge pipe. Test it twice a year with a "
             "bucket of water, and if the cellar floods when the power goes out, a battery or "
             "water-powered backup is what covers that.",
             avoid=("broken", "noisy", "noise", "leaking", "leaks", "not working", "stopped",
                    "replace", "repair", "install", "cost", "buy", "best", "which", "ice",
                    "flooded", "flooding", "smell", "smells")),
    _explain("explain-spray-can", ("spray can", "aerosol", "aerosol can", "aerosol spray"),
             "The can is sealed under pressure with a liquefied propellant above the paint or "
             "deodorant, and that liquid boils to keep the pressure steady as you use it. "
             "Pressing the nozzle lets the liquid out through a pinhole and it breaks into a "
             "mist; the can goes cold as it sprays and sputters at the end when the pressure "
             "finally drops."),

    # "how does a freezer burn food" is not the mechanism of the freezer: it is the dry patch
    # on the chop, and on main it was answered with burnt bits in a pan.
    entry("explain-freezer-burn",
          (("freezer burn", "freezer burns", "freezer burnt", "freezer burned",
            "ice crystals on the food",
            # The patch is the same fault said without the words "freezer burn": three shapes
            # reached a neighbour instead - "why does frozen food go dry" got the overcooked-meat
            # answer, "can i eat meat with freezer burn" the burnt pan, and "is it safe to eat
            # freezer burnt meat" the meat-turning answer.
            #
            # Every phrase here names the freezer or the frozen food with it. A bare "dry out",
            # "dries out" or "dried out" is not a subject: those three words took "why does my
            # skin dry out", "why does my hair dry out", "how do i stop my clothes drying out",
            # "why did my chicken dry out" (the oven, not the freezer) and "why does my washing
            # dry out creases" off the cards that answer them.
            "goes dry in the freezer", "go dry in the freezer",
            "dries out in the freezer", "dried out in the freezer", "frozen food go dry",
            "frozen food goes dry", "frozen food dry out", "frozen food dries out",
            "frozen food drying out", "frozen food dry", "dry out in the freezer",
            "white dry patches", "frost in the bag", "burnt in the freezer",
            "burn in the freezer"),
           WORKS + ("why does", "why do", "why is", "why are", "stop", "stops", "stopping",
                    "prevent", "preventing", "avoid", "avoiding", "get rid",
                    "safe", "eat", "eat it", "meat", "fish", "chicken", "bad", "still good")),
          "Freezer burn is the food drying out where air can reach it: the water at the "
          "surface turns straight to vapour in the cold, so that patch goes pale, leathery "
          "and tasteless. It is safe to eat, just cut that bit off - and pressing the air out "
          "of the bag and freezing in portions, rather than a loose bag of loose bits, is what "
          "stops it.",
          # "how do i stop freezer burn" is a prevention question, and TROUBLE's "stopped"
          # reads as the same word, so this row leaves that one out
          avoid=tuple(w for w in TROUBLE if w not in ("stopped", "stuck")),
          ask=EXPLAIN + ("can i", "is it safe", "safe to eat", "is it ok", "still safe")),

    # --- the car, the boiler, the shower ----------------------------------
    # A seat belt and an airbag are the safety half of the car and nothing explained them: the
    # lines met the search hedge, while "how does a car engine work" was answered.
    # Two rows, not one: "how does an airbag work" opened on the seat belt when both were one
    # entry, so each mechanism now leads with itself and names the other at the end.
    _explain("explain-seat-belt", ("seat belt", "seat belts", "seatbelt", "seatbelts"),
             "A seat belt is a strap that locks: a reel lets it pull out slowly so you can move, "
             "and a sprung weight inside catches on a ratchet when the car stops suddenly, so you "
             "are held back instead of going forward. An airbag is a cloth bag a chemical charge "
             "fills with nitrogen in a twentieth of a second, and it only works with the belt."),
    _explain("explain-airbag", ("airbag", "airbags", "air bag", "air bags"),
             "An airbag is a cloth bag that a chemical charge fills with nitrogen in about a "
             "twentieth of a second: a sensor spots the sudden stop and fires it, then it "
             "deflates so you can get out. It only works with the belt, the strap that locks "
             "when a sprung weight catches on a ratchet."),
    # "how does a chimney work" and "how does a chimney draw" were both a shrug, and it is the
    # same question about the same thing: warm air up the flue pulls fresh air into the room.
    _explain("explain-chimney-draw", ("chimney", "chimneys", "flue", "open fire", "wood burner"),
             "A fire heats the air in the flue, that hot air is lighter than the air in the room "
             "and rises out of the top, and the gap it leaves pulls fresh air in at the bottom - "
             "that steady pull is the draw. A cold flue has no pull at all, which is why a fire "
             "smokes on a cold morning until the chimney warms, and why a room sealed too tight "
             "for air to get in makes any fire sulk.",
             # a sweep is the trade, not the draw: "how does a chimney sweep work" was answered
             # here with a paragraph about hot air rising, which is worse than a hedge
             avoid=("sweep", "sweeps", "sweeping", "swept", "sweep the chimney",
                    "brushes", "bird nest", "birds nest")),
    _explain("explain-shower-pump", ("shower pump", "shower pumps", "power shower",
                                     "pumped shower"),
             "A pump sits between the hot and cold supplies and the shower head and gives the "
             "water a push, because a low-pressure gravity system only has the height of the "
             "tank in the loft behind it. It needs both a hot and a cold feed it is allowed to "
             "draw on - a pump on a mains-fed combi does nothing - and the usual reason one goes "
             "weak is air or a filter, not the pump itself."),
    _explain("explain-speed-camera", ("speed camera", "speed cameras", "traffic camera",
                                      "average speed", "average speed camera"),
             "A fixed speed camera measures how fast you cross two buried loops or a radar beam "
             "and photographs the plate if you are over the limit; average-speed cameras instead "
             "read the same plate at two points and divide the distance by the time, so braking "
             "for one camera does not help. The picture and the calibration certificate are what "
             "make a ticket stand up, which is why a faulty or obscured plate is not a way out "
             "of one."),

    # --- the letters ------------------------------------------------------
    # A line that asks what the letters stand for wants the words. These are the acronyms in
    # this file that people actually ask about, spelled out in the first clause.
    _name("explain-gps-name", ("gps",),
          "GPS stands for Global Positioning System: a ring of about thirty satellites, each "
          "beaming the time and its own position, and your phone works out where it must be from "
          "the difference between those signals. Only the American set is called GPS - Europe's "
          "Galileo and Russia's GLONASS do the same job, and your phone listens to whichever it "
          "can hear."),
    _name("explain-qr-name", ("qr code", "qr", "qr codes"),
          "QR stands for Quick Response, and the name is the only thing about it that is simple: "
          "the square holds up to about four thousand characters of text, which is how a whole "
          "web address fits in, and it survives being printed small, smudged or half covered. "
          "That is why the one on a bus stop still scans from a photograph."),
    _name("explain-led-name", ("led", "leds", "led bulb", "led lights"),
          "LED stands for light-emitting diode: a chip of semiconductor that gives out light when "
          "current passes through it, with no filament to burn out and very little heat at the "
          "glass. That is why an LED bulb lasts years and uses a fraction of the power of an "
          "old filament bulb, and why it is cool enough to touch."),

    # The everyday letters. Almost every "what does X stand for" was a shrug, because the file
    # only spelled out the three machines it happened to explain. The rule is the same for all
    # of them: the letters come first, then the one thing worth knowing about them, because a
    # person who asks what the letters mean has the thing in front of them already.
    _name("explain-wifi-name", ("wifi", "wi fi", "wi-fi"),
          "WiFi does not stand for anything: a branding agency made the word up in 1999 as a "
          "play on hi-fi, and the Wireless Ethernet Compatibility Alliance liked it enough to buy "
          "it. The thing itself is just a short-range radio link, so there are no letters to "
          "expand."),
    # "what does 5g mean" scores the mechanism row higher than a bare "5g" key can reach - that
    # row keys on the same three words and matched one more - so the letters row names the whole
    # question and takes it on the phrase.
    _name("explain-5g-name", ("5g mean", "4g mean", "3g mean", "5g stand for", "4g stand for",
                              "5g", "4g", "3g", "5 g", "4 g", "five g"),
          "The G stands for generation: 4G is the fourth, 5G the fifth, and the numbers are a "
          "speed-and-latency ladder rather than a brand. 4G took about a tenth of a second to "
          "answer and 5G more like a hundredth, which is what makes video calls and live video "
          "from a phone work away from wifi; the phone drops to the slower one when the signal is "
          "thin, which is why the number in the corner keeps changing."),
    _name("explain-nhs-name", ("nhs",),
          "NHS stands for National Health Service, and the part worth knowing is what the words "
          "buy you: care that is free at the point of use and paid for out of general taxation, "
          "so nobody is asked for a card or an insurance number at A&E, a GP's surgery or a "
          "maternity ward."),
    _name("explain-asap-name", ("asap",),
          "ASAP stands for as soon as possible, which in an email is a polite way of asking "
          "without giving a time. If somebody needs it by a date, the date is the useful thing to "
          "say back, because as soon as possible means something different to everyone."),
    _name("explain-gpu-name", ("gpu", "gpus"),
          "GPU stands for graphics processing unit: the chip that does the thousands of small "
          "arithmetic sums a picture is made of at once. That is why it draws games and video "
          "smoothly, and why the same chip does machine learning, which is the same kind of sum "
          "on a much bigger scale."),
    _name("explain-adhd-name", ("adhd",),
          "ADHD stands for attention deficit hyperactivity disorder, and the words are a poor fit "
          "for what it is: the attention is not missing so much as hard to steer, so a person can "
          "concentrate deeply on one thing and not at all on another. It is diagnosed by "
          "questionnaires and a history, not a blood test, and it runs in families."),
    _name("explain-html-name", ("html",),
          "HTML stands for HyperText Markup Language: it is the set of tags that say what each "
          "part of a web page is - a heading, a paragraph, a link - and the browser turns those "
          "tags into the page you see. It is not a programming language and it cannot do "
          "arithmetic, which is what CSS and JavaScript are for."),
    _name("explain-ict-name", ("ict",),
          "ICT stands for information and communication technology, the school subject that used "
          "to be called computer studies: word processing, spreadsheets, and how to search and "
          "check what you find. Schools now tend to call it computing, and teach programming in "
          "it as well."),
    _name("explain-bbc-name", ("bbc",),
          "BBC stands for British Broadcasting Corporation, and the letters it does not have are "
          "the interesting part: no advertising, because it is paid for by the licence fee, and "
          "a charter that keeps it at arm's length from the government.",
          # "what" is one of the words that asks for a name, so a listings ask for the channel
          # reached the letters: "whats on bbc tonight" was answered with what the three letters
          # stand for. What is on tonight is the schedule, and that is the other row.
          avoid=("whats on", "what's on", "what is on", "anything on", "tonight", "listings",
                 "schedule", "schedules", "showing", "playing")),
    _name("explain-ps-name", ("ps", "p.s.", "ps."),
          "PS stands for postscript, from the Latin post scriptum, meaning written after: the "
          "line you add once the letter is finished and signed. On a keyboard P.S. needs the full "
          "stops and PS does not, so write whichever matches the rest of what you are typing."),
    _name("explain-dvd-name", ("dvd", "dvds"),
          "DVD stands for digital versatile disc, and the versatile is the honest part: the same "
          "disc holds a film, an album or a computer program. It is the same size as a CD and "
          "holds about seven times as much, and a Blu-ray holds about five times more again."),
    _name("explain-usb-name", ("usb",),
          "USB stands for Universal Serial Bus: universal because one plug replaced the pile of "
          "different ports a computer used to have, and bus because several devices share it. The "
          "letter after it is the shape - USB-C is the small reversible one - and the number is "
          "the speed, so a blue USB 3 socket copies much faster than a black USB 2 one."),
    _name("explain-sim-name", ("sim", "sim card", "sim cards"),
          "SIM stands for subscriber identity module: the chip that holds your phone number and "
          "the key your network checks before it lets a call through. It is why you can move your "
          "number to a new handset by moving the card, and why an eSIM does the same job written "
          "into the phone."),
    # The plural stays out of the key: "pins and needles" is the health phrase, and
    # "what does it mean when i get pins and needles in my hand" is the nerves answer, not the
    # card. A bare "pins" still reaches the row as a form of "pin", and the avoid words are what
    # keep the health sense out.
    _name("explain-pin-name", ("pin", "pin number"),
          "PIN stands for personal identification number, which is why \"PIN number\" says the "
          "word twice. It is checked by the card itself rather than by a computer anywhere else, "
          "so the number never leaves the machine you put the card in - and nothing legitimate "
          "ever asks you to type it into a phone call, a text or a website.",
          avoid=("needles", "pins and needles", "tingling", "tingles", "numb", "numbness",
                 "dead leg", "dead arm")),
    _name("explain-diy-name", ("diy",),
          "DIY stands for do it yourself: the jobs around the house you do instead of paying a "
          "trade. The word of warning is the useful part - anything involving gas, a fuse box "
          "beyond changing a fuse, or a wall you are not sure is load-bearing is not a DIY job, "
          "and the rules on rented homes make some of it your landlord's."),
    _name("explain-mot-name", ("mot",),
          "MOT stands for Ministry of Transport, the department that invented the test in 1960, "
          "and the letters have outlived it. The test checks safety and emissions on a car over "
          "three years old once a year, and it is the garage that keeps the record - driving "
          "without one is a fine, and the car's insurance can be void.",
          # what the letters stand for is a different question from what to do about a fail:
          # "what do i do if my car fails its mot" was given the history of the department
          # while the fail-sheet entry in cars.py sat unused.
          avoid=("fail", "fails", "failed", "failing", "retest", "dangerous", "major",
                 "advisory", "advisories", "fail sheet", "what do i do", "what should i do",
                 "how do i fix", "drive it", "driving it", "can i drive")),
    _name("explain-lol-name", ("lol",),
          "LOL stands for laugh out loud, and it is usually doing the job a nod does in speech: "
          "it says the message landed as a joke, not that anyone actually laughed. That is why "
          "people write it at the end of a line rather than the start."),
    _name("explain-ie-name", ("i.e.", "ie", "i e"),
          "i.e. stands for id est, Latin for that is, and it introduces a rephrasing of what you "
          "just said rather than a list: the cake was enormous, i.e. it fed eight. People write "
          "it when a shorter or plainer version of the same thing helps."),
    _name("explain-eg-name", ("e.g.", "eg", "e g"),
          "e.g. stands for exempli gratia, Latin for for example, and it introduces one of "
          "several: a root vegetable, e.g. a carrot. It is not the same as i.e., which rephrases "
          "rather than gives an example, and a list of three or four belongs after e.g. too."),
    # "what is rsvp" is the same question as "what does rsvp mean" and reached nothing, because
    # ASKS_A_NAME carries the meaning forms and not the bare "what is". The ask group is the one
    # that has to grow, not the subject: "rsvp" on its own is already here.
    entry("explain-rsvp-name", (("rsvp",),
                                ASKS_A_NAME + ("what is", "whats", "what's")),
          "RSVP stands for repondez s'il vous plait, French for please reply, which is why the "
          "letters have no apostrophe and no full stops. An invitation that wants numbers for "
          "catering will usually give a date; reply by then even when the answer is no, because "
          "a maybe costs the host a place.",
          # the date to answer by is the reply card's question; this is only the letters
          avoid=TROUBLE + ("rsvp date", "rsvp by", "reply by", "deadline", "when is the rsvp",
                           "when should i rsvp", "when do i rsvp"),
          ask=EXPLAIN, bias=2),
    _name("explain-btw-name", ("btw",),
          "BTW stands for by the way, and in a message it does real work: it flags a change of "
          "subject that does not need an answer. Anything that does need one is better off "
          "without it, since a line starting by the way reads as an aside."),
    _name("explain-sms-name", ("sms", "text message"),
          "SMS stands for short message service: 160 characters was the limit because the "
          "signalling channel it hitched a ride on had room for that much, and the limit shaped "
          "the way people write. Pictures and long texts go over data instead, which is why a "
          "photo is not an SMS even when it arrives in the same app."),
    _name("explain-url-name", ("url", "urls"),
          "URL stands for uniform resource locator: the address that says where a page lives and "
          "how to fetch it. The https at the front is the how - it asks for the encrypted "
          "version - and the part after the first single slash is the site, so a link with a lot "
          "of nonsense after it usually still works with the nonsense cut off."),
    _name("explain-pdf-name", ("pdf", "pdfs"),
          "PDF stands for portable document format: a file that carries the layout as well as "
          "the words, so a form or a ticket looks the same on any machine. That is why a "
          "signature on a PDF counts as a signature on that page, and why editing one is "
          "awkward - the page is closer to a picture of a page than to a document."),
    _name("explain-hdmi-name", ("hdmi",),
          "HDMI stands for high-definition multimedia interface: one cable that carries the "
          "picture and the sound together, which is why a television has needed only one lead "
          "since about 2005. Both ends are the same plug, so the spare socket on a television is "
          "usually the one to use for a laptop."),
    # "whats a bucket list" was a shrug. It is one of those phrases everybody uses and nobody has
    # looked up, and the useful half is the method rather than the name.
    # not _name(): "whats a bucket list" carries no "stands for" and no "mean", so the letters
    # ask group cannot reach it. The phrase itself is the key and the asking is the second part.
    entry("explain-bucket-list",
          (("bucket list", "bucket lists", "life list", "before i die list"),
           ("what is", "whats", "what's", "mean", "means", "explain", "how do i",
            "how should i", "should i", "ideas", "write", "make", "start", "help")),
          "A bucket list is the list of things you want to do before you die - the name comes from "
          "kick the bucket. It works better as ten or fifteen things with a date and a rough cost "
          "next to each than as a long wish list: one a year is a good pace, and putting the "
          "cheapest next keeps it moving. Then tell somebody about the top one, because a list "
          "nobody knows about is the one that never happens.",
          # the key already holds the asking words; the data test wants the row to pass one too
          ask=EXPLAIN,
          avoid=TROUBLE + ("cook", "cooking", "recipe", "gym", "workout", "running", "diet")),
    _name("explain-ram-name", ("ram",),
          "RAM stands for random access memory: the working space a computer keeps open programs "
          "in, wiped when it loses power. More of it helps when many tabs or programs are open at "
          "once; it does not make a single program faster, and a full disk is the more common "
          "reason a computer feels slow."),

    # --- the words on the box, the bill and the settings screen -----------
    # The everyday vocabulary of a phone, a laptop and a broadband advert. Asked by name every
    # one of these was a shrug, and the people asking are not trying to learn computing - they
    # are trying to understand something they are about to pay for. `_name` is the right shape:
    # the thing first, then the one part worth knowing beyond the word.
    _name("explain-cache-name", ("cache", "cached", "clearing the cache"),
          "A cache is a copy kept close to hand so the same thing does not have to be fetched "
          "twice: a browser keeps the pictures and layout of a page, and an app keeps a little of "
          "your data, so the next visit is quick. It is only copies - clearing it never touches "
          "your photos, files or saved passwords - and it is the first thing to try on a page "
          "that has gone stale or shows yesterday's price."),
    _name("explain-browser-name", ("browser", "web browser", "chrome", "firefox"),
          "A browser is the program you read websites in: Chrome, Safari, Edge and Firefox are "
          "the common four and they all do the same job. Anything you type in the address bar, "
          "any page you save a password for and any tab you leave open belongs to that one "
          "browser, which is why an account that works on your phone can look lost on a laptop "
          "until you sign in."),
    _name("explain-mbps-name", ("mbps", "megabits", "megabit", "megabytes"),
          "Megabits per second is how fast data moves, and the small b is the whole trick: eight "
          "bits make a byte, so a 100Mbps connection downloads about 12 megabytes a second - a "
          "song in a few seconds, a two-hour film in about ten minutes. Adverts quote megabits "
          "because the number is bigger, while file sizes on your phone are in megabytes."),
    _name("explain-gb-name", ("gb", "gigabyte", "gigabytes", "mb", "megabyte", "megabytes",
                              "terabyte", "tb"),
          "A gigabyte is about a thousand megabytes, and a megabyte is about a thousand "
          "kilobytes: a photo is around 3MB, a song 4MB, a downloaded film 1.5 to 4GB, and a "
          "terabyte is a thousand gigabytes. Storage and data use the same units - the GB on a "
          "phone's box is how much it holds, the GB on a mobile bill is how much it downloads.",
          avoid=("how many", "how much", "enough", "need", "worth", "recommend", "buy")),
    _name("explain-ssd-name", ("ssd", "solid state drive"),
          "An SSD is storage with no moving parts, which is why a laptop with one starts in "
          "seconds and opens programs straight away. It is faster, quieter and more shock-proof "
          "than a spinning disk and dearer for the same size, which is why a desktop often has "
          "an SSD for the system and a big disk for the archive."),
    _name("explain-hard-disk-name", ("hard drive", "hard disk", "hdd"),
          "A hard disk is the older kind of storage: a stack of spinning plates read by a head, "
          "which is why it is cheap for a lot of space and why a laptop with one takes half a "
          "minute to wake up. It is fine for a photo archive or a desktop; an SSD is what makes "
          "an old laptop feel new, and a 1TB hard disk costs about what a 250GB SSD does."),
    _name("explain-gpu-name2", ("graphics card", "graphics processor"),
          "The graphics card is the part that draws the picture, built to do many small sums at "
          "once: that is what makes a game smooth, and why the same part does video editing. A "
          "phone has one inside its main chip and a gaming laptop has a separate one; for email, "
          "video calls and spreadsheets the built-in one is plenty."),
    _name("explain-cpu-name", ("cpu", "processor"),
          "The CPU is the chip that runs the instructions in every program; its speed is quoted "
          "in gigahertz and how many jobs it can do at once in cores. For everyday use - a "
          "browser, video calls, a spreadsheet - a mid-range chip from the last few years feels "
          "the same as a fast one, and more memory or an SSD makes a bigger difference.",
          avoid=("faster", "slow", "upgrade", "replace", "which", "best", "buy")),
    _name("explain-firewall-name", ("firewall",),
          "A firewall is a filter on the traffic going in and out of a device or a home network: "
          "it lets the answers to what you asked for through and blocks the connections nobody "
          "asked for. Your router has one on by default and your computer has its own, so you "
          "rarely need to touch it - a program that cannot reach the internet is the one time it "
          "is worth looking at."),
    _name("explain-malware-name", ("malware", "spyware", "ransomware", "trojan"),
          "Malware is software written to do something you did not ask for: a virus that spreads, "
          "spyware that watches, ransomware that locks your files until you pay. It arrives as an "
          "attachment, a fake update or a program from a site that is not the maker's, so the "
          "protection that works is updating the system, keeping to official app stores and never "
          "opening a file you did not expect.",
          avoid=("have i got", "do i have", "i have a", "symptoms", "remove", "removing",
                 "clean", "cleaning", "scan", "check", "virus",
                 # ransomware has its own definition, and this row's first sentence is about
                 # malware in general
                 "ransomware", "ransom")),
    _name("explain-ip-name", ("ip address", "ip", "ipv4", "ipv6"),
          "An IP address is the number that identifies a device on a network, a bit like a house "
          "number: your router has one on the internet and gives each phone and laptop inside the "
          "house its own. The one inside changes when you reconnect, and the one on the internet "
          "changes when the router restarts, which is why nothing important - an email account, a "
          "bank - is tied to an IP address."),
    _name("explain-driver-name", ("driver", "drivers"),
          "A driver is the small program that lets the system talk to one piece of hardware - a "
          "printer, a graphics card, a wifi chip. Windows and macOS bring most of them already, "
          "and a device that stops working after an update, or a printer that is suddenly "
          "offline, is often the driver rather than the thing itself: look on the maker's own "
          "site rather than a download site.",
          # a lorry driver and a train driver are people with a day, and "what does a train
          # driver do" was told what a device driver is: this card is about the software, so a
          # driver named by the vehicle stands aside (the work row answers it, not this one)
          avoid=("printer", "offline", "wont", "not working", "update", "install",
                 "train driver", "train drivers", "lorry driver", "lorry drivers",
                 "truck driver", "truck drivers", "bus driver", "bus drivers",
                 "taxi driver", "taxi drivers", "delivery driver", "delivery drivers",
                 "van driver", "courier", "forklift", "fork lift", "hgv",
                 "driver do for a living")),
    _name("explain-os-name", ("os", "operating system"),
          "The operating system is the layer between the programs and the machine: Windows, "
          "macOS, Android and iOS are the four you meet. It manages the files, the screen and the "
          "battery, and it decides which apps can run, which is why an app that has stopped being "
          "updated eventually stops opening on a new version."),
    _name("explain-app-name", ("app", "apps", "app store"),
          "An app is a program built for a phone or tablet, installed from the store that came "
          "with the device - the App Store on an iPhone, the Play Store on Android. It runs on the "
          "phone itself and keeps its own data, so an app and the website of the same name can "
          "hold different things, and deleting the app usually takes its data with it.",
          avoid=("delete", "deleting", "remove", "uninstall", "install", "installing", "not",
                 "wont", "best", "which")),
    _name("explain-roaming-name", ("roaming", "roam"),
          "Roaming is your phone using a network abroad instead of your own, and it costs extra "
          "unless your plan or your destination is inside a deal. Turning data roaming off before "
          "you fly costs nothing and stops the surprise; check your own plan's roaming page "
          "rather than the word on the advert.",
          avoid=("charge", "charged", "bill", "cost", "how much", "free", "turn off", "turn on")),
    _name("explain-hotspot-name", ("hotspot", "tethering", "personal hotspot"),
          "A hotspot is a wifi network your phone makes out of its own mobile data, so a laptop "
          "can use the connection: on an iPhone it is Settings > Personal Hotspot, and on Android "
          "it is under Network, Hotspot and tethering. It uses your data allowance like any other "
          "use, drains the battery quickly, and is worth a password so nobody else joins.",
          avoid=("set up", "how do i", "wont", "not working", "turn on")),
    _name("explain-unlimited-name", ("unlimited data", "unlimited"),
          "Unlimited data means there is no monthly cap to go over, but almost every such plan "
          "has a fair-use point - often 20 to 50GB - after which video is slowed or the speed "
          "drops for the rest of the month. It is worth having if you stream on the move; check "
          "the fair-use figure rather than the word unlimited.",
          avoid=("should i", "worth", "better", "cheaper", "switch", "deal")),
    _name("explain-update-name", ("update", "updates", "software update"),
          "An update is a new version of an app or of the phone's own system, and most of them "
          "close security holes rather than add features. Do them: on an iPhone it is Settings > "
          "General > Software Update, on Android Settings > Software update, and it is worth "
          "letting it happen overnight on wifi. The risk of skipping them is a known hole being "
          "used against you.",
          avoid=("how do i", "wont", "stuck", "not", "install", "installing", "remove")),

    # Free or not is what people ask about roaming, and it is not a meaning question, so "is
    # roaming free in europe" never reached the row above it.
    entry("roaming-cost", (("roaming", "roam", "abroad", "in europe", "in spain", "in france"),
                           ("free", "charge", "charges", "charged", "cost", "costs",
                            "how much", "extra", "surcharge", "included", "include",
                            # "do i need to pay for roaming in france" has no cost word at
                            # all, only the verb, so it was the money card's (credit cards and
                            # loans for a deposit) rather than the roaming charge.
                            "pay for roaming", "pay to roam", "pay for data",
                            "pay to use my phone", "pay to use my data", "pay extra",
                            "need to pay", "have to pay", "charged for")),
          "In the EU it is free to use your normal allowance, but only on plans that include it: "
          "several UK networks charge a flat fee for EU roaming again, usually about \u00a32 a "
          "day or \u00a310 a month, so check your own plan before you go. Outside Europe assume "
          "\u00a35 to \u00a310 a day unless you buy a travel add-on first, and turn data roaming "
          "off for the flight so nothing connects on the way over.",
          # No ask gate: "is roaming free in europe" has no how/what/why word in it at all.
          # Spending money for the trip is travel.py's day rate, not the roaming charge, and "in
          # spain" plus "how much" beat the day-rate row: "how much money for a week in spain"
          # answered with "about £2 a day or £10 a month" of EU roaming, and "how much spending
          # money do i need for a week in spain" the same. A length of trip is money for the trip.
          # A card used abroad is money, not data: the key takes any line with a place word and a
          # price word in it, so "how much is a card fee abroad" was read as a roaming question and
          # lost the travel-card answer ("pay in the local currency") that used to win the turn.
          # The words that carry the fix are the ones that name a fee or a way of getting
          # money, and none of them sits beside "roaming" in a real sentence. A card used to
          # pay is not one of them: "will i be charged for roaming if i pay by card in spain"
          # names roaming and must keep the roaming answer, so the card-payment family is not
          # in this list (the review on this PR found two lines lost that way).
          avoid=("turn off", "turn on", "what is", "mean", "vpn",
                 "spending money", "spending cash", "money for", "money to take",
                 "money should i take", "much money", "week in", "days in", "nights in",
                 "fortnight", "does a week", "is a week", "cost of", "much is a week",
                 "card fee", "card fees", "cash machine", "cashpoint", "atm", "withdraw",
                 "withdrawal", "exchange rate", "travel money", "holiday money"), bias=1),

    # The number on the box, not the meaning of the unit: "how many gb do i need on a phone" was
    # a screen-time agreement and "is 128gb enough" was a shrug.
    entry("storage-how-much", (("gb", "storage", "space", "memory",
                                # a phone is sold as "128GB" and the tokenizer keeps the digits
                                # with the unit, so the bare word never matched that line
                                "64gb", "128gb", "256gb", "512gb", "1tb",
                                # a drive is named by its size and its kind: "is 500gb ssd
                                # enough" had neither "512gb" nor a word in the key, so the
                                # commonest way of asking about a laptop drive was a shrug
                                "ssd", "ssds", "hdd", "hard drive", "hard disk", "hard-drive",
                                "500gb", "2tb", "4tb", "128 gb", "256 gb"),
                               ("how many", "how much", "enough", "need", "recommend",
                                "which one", "size")),
          "Photos and video are what fill a phone or a laptop: about 3MB a photo, so 10,000 "
          "photos is around 30GB, and video runs from 150MB a minute at 1080p to 350MB at 4K. "
          "128GB is enough for most people who stream their music and television and keep photos "
          "in the cloud; take 256GB if you record a lot of video or play big games. A laptop is "
          "worth 256GB, and a cheap SD card covers the rest.",
          avoid=("cache", "clean", "free up", "delete", "full", "wifi", "data", "bill",
                 # the price of a room to rent is the costs table's answer, and it is asked with
                 # the same two words this row is keyed on: written as phrases so that the size
                 # of a drive keeps its answer, "how much storage do i need" or "is 128gb enough"
                 "much does storage cost", "much is storage", "cost of storage",
                 "price of storage", "storage prices", "storage unit cost", "storage costs me",
                 "does self storage cost",
                 "sim", "router",
                 # "space" is the word for a phone's room *and* for room in a life. The human
                 # senses are `guard=not_the_space_in_a_relationship` below, not words here, so
                 # that a line which names a phone, photos or a drive keeps the size answer
                 # whatever person it also names ("i need space on my phone", "my mum needs more
                 # space on her phone"). An avoid phrase would take those lines too.
                 # the other thing called storage is a room to rent, and its price is the
                 # costs table's answer: "how much does a storage unit cost" was read here
                 "storage unit", "storage units", "self storage", "unit", "units", "rent",
                 "renting", "garage", "loft", "attic", "warehouse", "shed", "moving house",
                 "house move", "furniture", "boxes", "store my", "storing",
                 # a drive that is full and a screen that shows how much is left are the
                 # technology row's, and they are about the free space, not the size to buy
                 "left", "space left", "how full", "free up", "clean up"),
          # a line with no device word in it - "how much storage do i need" - is a tie between
          # this row and the self-storage price, and the size of a drive is the likelier ask
          bias=2,
          guard=not_the_space_in_a_relationship),
]


# The acronyms of everyday life - money, work, the emergency room - which main answered with a
# neighbour card or a shrug. The shape is the same as every row above: the letters first, then
# the one thing the letters do not carry. It is a table because every row has that shape, and a
# new acronym is one more line here rather than another entry.
# The coil is how most people name the IUD, and the how-to questions about it were the search
# hedge ("how do i get the coil fitted", "how long does the coil last", "does the coil hurt", "is
# the coil free"). The names are the phrases, never the bare word, because a coil is also a cable,
# a car spring and a lock of hair.
COIL_NAMES = ("iud", "iuds", "intrauterine device", "intrauterine system", "the coil",
              "copper coil", "coil fitted", "contraceptive coil", "mirena")

# "does a coil hurt" and "how do i get a coil removed" say "a coil", not "the coil" - only the
# how-to row keys the bare word, and only that row carries the fence below.
COIL_ASKS = COIL_NAMES + ("coil", "coils", "coil in")

# A coil is also a car spring, a cable, a stove ring and a lock of hair. Every row that keys the
# bare word stands itself down on these: "what is a coil cable" and "what is a coil in a car"
# were the IUD definition before the fence.
NOT_A_COIL = ("spring", "springs", "car", "cars", "van", "engine", "mower", "cable", "cables",
              "wire", "wires", "hair", "curly", "curls", "curl", "stove", "hob", "boiler",
              "ignition", "mot", "garage", "plug", "plugs", "washing machine")

# "what is the difference between the morning after pill and the coil" is a question about the
# emergency pill that names the coil, and this row answered it with the booking card: the coil is
# the better answer to "how do i get one", never to a line about the pill.
NOT_A_COIL_QUESTION = ("morning after", "morning-after", "emergency contraception", "plan b",
                       "levonelle", "ellaone", "ella one", "ulipristal")

SPELLED_OUT = (
    # The mechanism row for the cash machine keys the phrase "what does" as well as the word, so
    # it still out-scored the letters row on "what does atm mean" - the same tie the 5g row is
    # written to break. The whole question in the key takes the line on the phrase.
    ("atm", ("atm mean", "atm stand for", "atm short for", "atm", "atms"),
     "ATM stands for automated teller machine, which is the cash machine in the wall. The useful "
     "part is not in the letters: the machine asks your bank before it counts out anything, so a "
     "card that works in the shop can still be refused here if the answer is no."),
    ("cv", ("cv", "cvs", "curriculum vitae"),
     "CV stands for curriculum vitae, Latin for the course of your life, and the name oversells "
     "what should be a page or two: the last two jobs with what you actually did in them, dates, "
     "qualifications, and a line at the top saying what you are after. Gaps are fine on a CV so "
     "long as the dates are honest."),
    ("ai", ("ai",),
     "AI stands for artificial intelligence, and in use it means software that finds the pattern "
     "in a lot of examples instead of being told the rule. That is why it is good at sorting "
     "photographs and writing a first draft, and why it can state a wrong fact as confidently as "
     "a right one - the answer is fluent whether or not it is true."),
    ("hr", ("hr", "human resources"),
     "HR stands for human resources: the department that holds the contracts, the pay, the "
     "holidays and the complaints. The order that works for a problem at work is your manager "
     "first, their manager if that goes nowhere, and HR in writing after that, because HR's job "
     "is the company's side of the paperwork."),
    ("ceo", ("ceo",),
     "CEO stands for chief executive officer: the person who runs the company day to day and "
     "answers to the board. Their name is on the big decisions, not on the ordinary complaint - a "
     "refund or a wrong bill is still the customer service desk's job."),
    ("faq", ("faq", "faqs"),
     "FAQ stands for frequently asked questions: the page, usually at the foot of a website, "
     "where the thing you are about to write in has already been answered. Search that page for "
     "one distinctive word of your problem before you write, because the answer is often there in "
     "two lines and the form takes days."),
    ("cbt", ("cbt",),
     "CBT stands for cognitive behavioural therapy: a short talking treatment that works on the "
     "loop between what you think, what you do and how you feel, usually six to twenty weekly "
     "sessions with something to try between them. It is what the NHS offers first for anxiety "
     "and low mood, and in England you can refer yourself to it without seeing a GP."),
    ("ae", ("a and e", "a e", "a&e", "accident and emergency"),
     "A&E stands for accident and emergency, the hospital department for what cannot wait: chest "
     "pain, bad breathlessness, a bone through the skin, a head injury with vomiting or a "
     "collapse. If you are unsure whether to go, NHS 111 will say, and it is worth the call "
     "because A&E is the slowest place to be seen for something a pharmacist or a GP could "
     "handle."),
    ("sos", ("sos",),
     "SOS does not stand for anything: it was picked in 1905 because three dots, three dashes and "
     "three dots is unmistakable in Morse and spells no word that could be misread. It is not an "
     "abbreviation, so there is nothing hidden in the letters."),
    ("ppi", ("ppi", "payment protection insurance"),
     "PPI stands for payment protection insurance: a policy sold beside a loan or a credit card "
     "to cover the repayments if you lost your job or fell ill. Many were mis-sold, and the "
     "free route was a complaint to the lender that sold it - the deadline for new complaints "
     "passed in 2019, so a policy sold since then is the one worth reading the terms of."),
    ("dwp", ("dwp", "department for work and pensions"),
     "DWP stands for the Department for Work and Pensions: the department that pays Universal "
     "Credit, the state pension, PIP and jobseeker's payments, and runs the jobcentre. A letter "
     "from it with a date on it needs an answer by that date even if the answer is 'I need more "
     "time', because a missed deadline restarts the claim rather than pausing it."),
    ("hmo", ("hmo", "house in multiple occupation"),
     "HMO stands for house in multiple occupation: a house or flat let to three or more people "
     "who are not one family and who share a kitchen or a bathroom. A larger one needs a licence "
     "from the council, and the council's private renting team is who to ring about fire doors, "
     "alarms or overcrowding - not the landlord's own answer."),
    ("nsi", ("ns&i", "ns and i", "national savings"),
     "NS&I stands for National Savings and Investments: the government's own savings bank, where "
     "Premium Bonds and Index-linked Savings Certificates come from. The money is backed by the "
     "Treasury instead of a commercial bank, so the compensation limit quoted for banks does not "
     "apply to it, and the rates are usually ordinary rather than the best on the market."),
    ("etf", ("etf", "etfs"),
     "ETF stands for exchange-traded fund: a basket of shares that is bought and sold like a "
     "single share, so one purchase spreads the money over hundreds of companies. The charge is "
     "usually a fraction of a percent a year, and over decades that costs less than picking "
     "shares yourself - which is the whole argument for it."),
    ("isa", ("isa", "isas"),
     "ISA stands for individual savings account: a wrapper rather than a product, so a cash ISA "
     "and a stocks-and-shares ISA are both ISAs and what is inside them is free of UK tax on "
     "interest and gains. The allowance is per person, per tax year, and it resets in April "
     "whether or not you used the last one."),
    ("gp", ("gp", "gps surgery", "general practitioner"),
     "GP stands for general practitioner: the family doctor who sees you first and refers you on "
     "to a specialist. You can change practice without giving a reason, and the same-day slots "
     "usually go to the people who ring at opening time, so ring rather than walk in."),
    # The units, because "what does tbsp stand for" is a letters question too, and the number
    # beside them is the part people act on.
    ("kg", ("kg", "kgs"),
     "kg is short for kilogram: 1,000 grams, and about 2.2 pounds. A stone is 6.35 kg, which is "
     "why a person's weight in kilos is a bigger number than the same weight in pounds."),
    ("mg", ("mg", "mgs"),
     "mg is short for milligram: a thousandth of a gram, so 1,000 mg is 1 g. A 500 mg paracetamol "
     "tablet is half a gram, and the dose on the box is written in these units because the useful "
     "amount is too small to weigh in grams."),
    ("mph", ("mph",),
     "mph is short for miles per hour: how many miles the thing would cover in an hour at that "
     "speed. 30 mph is about 48 km/h, which is why a British speed limit and a European one are "
     "never the same number."),
    ("kph", ("kph", "kmh", "km/h"),
     "kph is short for kilometres per hour, the unit on every speedometer outside Britain and the "
     "United States. 100 kph is about 62 mph, and 50 kph in town is about 31 mph."),
    ("tbsp", ("tbsp", "tbsps", "tablespoon", "tablespoons"),
     "tbsp is short for tablespoon: 15 ml in a British, American or Australian recipe, and three "
     "level teaspoons. A heaped tablespoon of flour or sugar weighs more than 15 g, so level it "
     "off unless the recipe says heaped."),
    ("tsp", ("tsp", "tsps", "teaspoon", "teaspoons"),
     "tsp is short for teaspoon: 5 ml, and a third of a tablespoon. A level teaspoon of salt is "
     "about 6 g and of sugar about 4 g, which is why a spoon is a safe measure for salt and a "
     "rough one for anything you are weighing."),
    ("oled", ("oled mean", "oled stand for", "oled", "oled tv", "oled screen"),
     "OLED stands for organic light-emitting diode: every pixel makes its own light, which is why "
     "the blacks are truly black and the panel is thin enough to bend. The organic layer dims as "
     "it is used, so a bright static logo can leave a faint mark after years, and that is what the "
     "extra price over an LCD buys and costs."),

    # The health letters. "what does hpv stand for", "what does pms mean" and the rest were
    # shrugs on main, and the cards that did answer spelled out nothing: "what does uti stand
    # for" got the cystitis advice, which tells a person who asked about the letters nothing
    # about the words. The shape is the row above: the words, then the one fact worth knowing.
    ("hpv", ("hpv", "human papillomavirus"),
     "HPV stands for human papillomavirus: a very common group of viruses passed on by skin-to-skin "
     "contact, and most infections clear on their own. The types that cause most cervical cancer "
     "are the ones the NHS vaccine guards against, offered at 12 to 13, and the smear test finds "
     "the changes years before they become cancer."),
    ("pms", ("pms", "premenstrual syndrome", "pre menstrual syndrome"),
     "PMS stands for premenstrual syndrome: the mix of low mood, bloating, tender breasts and "
     "tiredness in the week or two before a period, which lifts once it starts. It is common and "
     "treatable - regular exercise, less caffeine and the combined pill help some women - so see a "
     "GP if it is spoiling a week of every month."),
    ("ibs", ("ibs", "irritable bowel syndrome"),
     "IBS stands for irritable bowel syndrome: cramping, bloating, wind and a change in how often "
     "you go, with nothing wrong with the gut itself. It is managed rather than cured - regular "
     "meals, enough fibre and water, less caffeine and alcohol - and a GP can rule out coeliac "
     "disease and check a change you have never had before."),
    ("uti", ("uti", "utis", "urinary tract infection"),
     "UTI stands for urinary tract infection: bugs in the bladder that cause burning when you pee, "
     "going often and a dragging ache low down. Most clear in a day or two with plenty of water, a "
     "pharmacy can advise, and see a GP or ring 111 the same day with a fever, back pain, blood, "
     "or if you are pregnant, a man or a child."),
    ("bmi", ("bmi", "body mass index"),
     "BMI stands for body mass index: weight in kilos divided by height in metres squared, with "
     "18.5 to 24.9 called healthy for most adults. It is a rough measure - it cannot tell muscle "
     "from fat, so it reads high on a rugby player and low on some older people, which is why "
     "waist size is worth knowing too."),
    ("ocd", ("ocd", "obsessive compulsive disorder"),
     "OCD stands for obsessive-compulsive disorder: unwanted, repeated thoughts that arrive on "
     "their own, and the rituals done to quieten them, like checking the hob or washing. It is "
     "common and treatable - talking therapy, usually CBT with exposure and response prevention, "
     "helps most people - so it is worth seeing a GP rather than putting up with it."),
    ("ptsd", ("ptsd", "post traumatic stress disorder"),
     "PTSD stands for post-traumatic stress disorder: flashbacks, nightmares, jumpiness and "
     "avoiding places after a frightening event, still there a month on. It is not weakness and it "
     "is treatable - trauma-focused talking therapy such as CBT or EMDR helps most people - so ask "
     "a GP for a referral rather than waiting for it to pass."),
    ("hrt", ("hrt", "hormone replacement therapy"),
     "HRT stands for hormone replacement therapy: oestrogen, usually with a progestogen, given to "
     "ease hot flushes, night sweats and mood swings of the menopause and to protect bone. It comes "
     "as tablets, patches or gel; for most women under 60 the risks are small, and a GP can talk "
     "through which type suits you."),
    # "the coil" is how most people name the IUD, and the how-to questions about it were the
    # search hedge ("how long does the coil last", "does the coil hurt", "is the coil free"):
    # the names are the phrases, never the bare word, because a coil is also a cable, a car
    # spring and a lock of hair.
    ("iud", COIL_NAMES,
     "IUD stands for intrauterine device: the small T-shaped coil a doctor or nurse fits into the "
     "womb, and it lasts five to ten years - a copper one five, the hormonal ones three to eight. "
     "Fitting takes a few minutes at a clinic or GP surgery, it is free on the NHS, and cramping "
     "for a day or two afterwards is usual. A copper one also works as emergency contraception up "
     "to five days after sex, the hormonal ones usually make periods lighter or stop them, and as "
     "long as you are over 16 you can ask for one without telling anyone."),
    ("sti", ("sti", "stis", "sexually transmitted infection"),
     "STI stands for sexually transmitted infection: an infection passed on during sex, such as "
     "chlamydia, gonorrhoea or HIV. Most have no symptoms, so a test is the only way to know, and "
     "testing is free and confidential at a sexual health clinic or by post - nearly all clear "
     "with a short course of antibiotics."),
    ("ivf", ("ivf", "in vitro fertilisation", "in vitro fertilization"),
     "IVF stands for in vitro fertilisation: an egg is fertilised with sperm in a laboratory, and "
     "an embryo is put back into the womb. One cycle takes about four to six weeks, the NHS funds a "
     "set number depending on where you live and your age, and the chance of success falls steeply "
     "through the late thirties."),
    # The money and paperwork letters: the P45 answered as a P60 on main, which is a confidently
    # wrong form, and the rest were the search hedge.
    ("pip", ("pip", "pips", "personal independence payment"),
     "PIP stands for Personal Independence Payment: the benefit for adults under state pension age "
     "who have extra costs from a long-term illness or disability, for getting around or for daily "
     "tasks. It is not means-tested, so savings and a job do not rule you out, and the decision "
     "rests on an assessment of what you can do, not on the diagnosis."),
    ("paye", ("paye", "pay as you earn"),
     "PAYE stands for pay as you earn: your employer takes income tax and National Insurance out of "
     "each payslip and sends it to HMRC, so the tax is paid as you go rather than in one bill. Your "
     "tax code is what tells them how much to take, so check it on the payslip - a wrong code is "
     "the usual reason a wage comes out short."),
    ("p45", ("p45", "p45s"),
     "A P45 is the form an employer gives you when you leave: the pay and tax so far that tax year "
     "and the code the next employer needs. Keep it, because the new job asks for it, and without "
     "one you can be put on an emergency code and overtaxed until it is sorted out."),
    ("p60", ("p60", "p60s"),
     "A P60 is the one-page summary an employer gives you after 5 April: the pay, the tax paid and "
     "your tax code for the year just gone. Keep it, because a mortgage, a visa or a tax return can "
     "all ask for it, and it is the quickest proof of what you earned."),
    ("hmrc", ("hmrc", "hm revenue and customs", "revenue and customs"),
     "HMRC stands for HM Revenue and Customs: the tax office, which deals with income tax, National "
     "Insurance, VAT and child benefit. It never asks for a password, a payment or a gift card by "
     "text or email - that message is a scam - and refunds, tax codes and self-assessment all go "
     "through your own account on gov.uk."),
    ("apr", ("apr", "annual percentage rate"),
     "APR stands for annual percentage rate: the interest plus the fees on a loan or a card, worked "
     "out over a year, so it is the number to compare two offers on rather than the headline rate. "
     "A 0% offer is only free if the balance is cleared before the rate ends, and a card's APR "
     "applies to cash withdrawals from day one."),
    ("rrp", ("rrp", "recommended retail price"),
     "RRP stands for recommended retail price: the price the maker suggests, not one a shop has to "
     "charge. Shops often sell below it, so a crossed-out RRP is a marketing figure - compare what "
     "you would actually pay elsewhere rather than the saving on the label."),
    ("dbs", ("dbs", "disclosure and barring service", "dbs check"),
     "DBS stands for Disclosure and Barring Service: the checks that show a criminal record to an "
     "employer, for work with children, patients or vulnerable adults. A basic, standard or "
     "enhanced check is applied for by the employer, not by you, and the certificate goes to you so "
     "you can show it to whoever asks."),
    ("lpa", ("lpa", "lasting power of attorney"),
     "LPA stands for lasting power of attorney: the legal document that lets someone you choose "
     "make decisions for you if you cannot - about money and property, or about health and care. It "
     "has to be registered with the Office of the Public Guardian while you still have the capacity "
     "to make it, and it costs £82 per document in England and Wales."),
    # The travel health cards, because "what does ghic stand for" is what someone asks when a
    # clinic mentions one.
    ("ghic", ("ghic", "global health insurance card"),
     "GHIC stands for Global Health Insurance Card: the free card that gives you state-provided "
     "medical care in the EU on the same terms as a local, and it replaced the EHIC for new "
     "applications after Brexit. It does not cover private treatment or getting you home, so "
     "travel insurance is still the thing to buy."),
    ("ehic", ("ehic", "european health insurance card"),
     "EHIC stands for European Health Insurance Card: the free card that gave state-provided "
     "medical care in the EU on the same terms as a local. New applications were replaced by the "
     "GHIC after Brexit, and an EHIC already issued still works until the date on it runs out."),
    # The house and the laptop, where the letters come up in a letter or a listing.
    ("epc", ("epc", "epcs", "energy performance certificate"),
     "EPC stands for energy performance certificate: the A to G rating a home gets when it is sold "
     "or let, from how much it costs to heat and how well it holds the heat. A rented home has to "
     "reach band E, and a low rating is the best handle for asking the landlord for insulation or "
     "a newer boiler."),
    ("vpn", ("vpn", "vpns", "virtual private network"),
     "VPN stands for virtual private network: it makes an encrypted tunnel between your device and "
     "a server elsewhere, so the owner of the wifi cannot see which sites you open. It is worth it "
     "on hotel and cafe wifi, but it does not make you anonymous - the VPN company can still see "
     "and log the traffic."),
)
# The same letters mean something else in the field named in the line, and the row above would
# answer with its own sense and sound certain: GP is games played on a football page, HR is the
# heart rate a runner asks about, MG is the car, and a CV joint is not a curriculum vitae. Main
# punts on every one of these, so a wrong explanation is a new wrong answer rather than a gain,
# and standing down keeps the plain ask.
SPELLED_OUT_STAND_DOWN = {
    # a line about the emergency pill that names the coil is the pill's question
    "iud": NOT_A_COIL_QUESTION,
    "gp": ("football", "footballer", "soccer", "fantasy football", "games played",
           "premier league", "fpl", "fifa", "grand prix", "formula 1", "formula", "motogp", "f1",
           "rugby", "league table"),
    # One list, not two: a second "hr" key in this table silently replaced the first, and the
    # words that went with it ("running", "exercise", "workout") were lost with it, so "what does
    # hr mean in running" was the human resources department again. A dict literal keeps the last
    # key, so the field words for a row are written once.
    "hr": ("heart rate", "bpm", "running", "runner", "exercise", "training", "workout",
           "cycling", "rower", "resting", "zone 2", "strava", "pace", "marathon", "gym",
           "calories burnt", "fat burn",
           # a reading on a watch is the same "not the department" case, said with the device
           "watch", "watch says", "apple watch", "smart watch", "smartwatch",
           "fitbit", "garmin", "tracker", "fitness band", "beats", "pulse"),
    "mg": ("car", "cars", "rover", "mg rover", "motorcycle", "motorbike", "engine", "brake",
           "model", "mg4", "mg5", "ev", "garage", "dealership", "insurance group"),
    "cv": ("cv joint", "joint", "driveshaft", "drive shaft", "shaft", "boot", "clunk",
           "clicking", "car", "half shaft"),
    "atm": ("networking", "network", "telecoms", "telecommunications", "packet", "packets",
            "protocol", "asynchronous transfer", "data link", "broadband"),
    "ai": ("illustrator", "adobe", "file extension", "photoshop"),
    "cbt": ("computer based training", "compulsory basic training", "motorbike", "motorcycle"),
    # The kinds of ISA are their own words, with their own cards in money_words.py: "what is a
    # lifetime isa" was given the letters ISA spelled out because the general row reads "what is
    # a" as well, so the name of a product has to hand the line on rather than answer it.
    "isa": ("islam", "islamic", "muslim", "quran",
            "lifetime isa", "lifetime", "help to buy isa", "help to buy",
            "cash isa", "stocks and shares isa", "stocks and shares", "junior isa", "junior",
            "innovative finance", "isa allowance", "isa limit"),
    # A pip is also a seed in an apple, and an APR is also the way April is written in a
    # date field: the letters asked for the words in a line that names fruit or a month are
    # not the benefit or the interest rate.
    "pip": ("apple", "apples", "orange", "oranges", "lemon", "lemons", "fruit", "pear",
            "pears", "seed", "seeds", "raspberry", "cider", "picture", "tv", "telly",
            "television", "screen", "monitor", "window"),
    "apr": ("april", "april 1", "1 april", "month", "date of birth", "calendar"),
    # EPC is also a warning light on a Volkswagen group dashboard, and STI is a Subaru.
    "epc": ("car", "cars", "dashboard", "dash", "light", "warning", "engine", "volkswagen",
            "vw", "skoda", "seat", "audi", "polo", "golf", "octavia"),
    "sti": ("subaru", "impreza", "car", "cars", "rally", "wrx"),
}

# "What's the difference between X and Y" is one of the commonest everyday questions, and on main
# every pair that had not already been written down as its own entry met the search hedge: jam and
# marmalade, a lake and a pond, a wage and a salary, a tortoise and a turtle, stock and broth. The
# question is the pair, not the wording, so the pairs live in one table and one entry reads it: the
# names in the line pick the row. A pair that is not in the table passes, which leaves the entries
# that already answer a pair (a cold and flu, a virus and bacteria, renting and buying) where they
# are, and lets a new pair be added with one line.
# See the note on DIFFERENCE_NAMES below: this is the short list of names that do not, on their
# own, hand a line to the table.
DIFFERENCE_CLAIM_SKIP = {"flu"}

DIFFERENCES = (
    (("jam", "jams"), ("marmalade", "marmalades"),
     "Jam is fruit cooked with sugar until it sets, and it is soft enough to spread; marmalade is "
     "citrus - usually Seville oranges - cooked with sugar and shreds of peel, so it is firmer and "
     "has a bitter edge. Same method, different fruit: anything with peel shreds in it is marmalade."),
    (("lake", "lakes"), ("pond", "ponds"),
     "Ponds are small and shallow: light reaches the bottom across most of one, so plants grow right "
     "through the middle. A lake is deep enough to have open water in the middle, with its own "
     "wind-driven ripples and a shore where plants stop. There is no exact size that splits them, "
     "but a pond you could wade across is a pond."),
    (("wage", "wages", "hourly pay"), ("salary", "salaries", "yearly pay"),
     "A wage is paid for the hours you worked, so overtime adds and a short week takes away; a "
     "salary is one yearly figure paid in twelve equal months whatever the hours. Hourly pay is "
     "better when you work extra, a salary is steadier when work is quiet."),
    (("tortoise", "tortoises"), ("turtle", "turtles", "terrapin", "terrapins"),
     "Tortoises live on land: domed shell, stumpy elephant-like back legs, and they cannot swim. "
     "Turtles live in water: a flatter, streamlined shell and flippers, and the sea turtles only "
     "come ashore to lay. A terrapin is the small freshwater turtle people keep in a pond."),
    (("frog", "frogs"), ("toad", "toads"),
     "A frog has smooth, damp skin, long back legs and jumps; a toad has dry, warty skin, shorter "
     "legs and walks or makes small hops. Frogs stay near water and toads wander further from it, "
     "coming back only to breed, and toads lay their eggs in strings rather than clumps."),
    (("baking powder",), ("bicarbonate of soda", "bicarb", "bicarbonate", "baking soda"),
     "Bicarbonate of soda is an alkali on its own: it only fizzes when it meets an acid such as "
     "buttermilk, lemon or vinegar. Baking powder is bicarbonate with that acid and a little starch "
     "already mixed in, so it raises on its own - which is why a recipe can call for three times as "
     "much baking powder as it would bicarb, and why swapping one for the other flatly does not work."),
    (("stock", "stocks"), ("broth", "broths"),
     "Stock is bones and scraps simmered for hours, and it sets to a jelly when cold because of the "
     "gelatine; it is an ingredient, not a dish. Broth is usually simmered for an hour or two with "
     "meat and vegetables still in it and is eaten as it is. Same pot, different job."),
    (("stew", "stews"), ("casserole", "casseroles"),
     "A stew is meat and vegetables cooked slowly in liquid on top of the hob; a casserole is the "
     "same food cooked in a covered dish in the oven. The dish gives the name, not the recipe, so a "
     "casserole is a stew in a lidded pot."),
    (("muffin", "muffins"), ("cupcake", "cupcakes"),
     "A cupcake is a small cake - butter, sugar, eggs, flour - baked in a paper case and iced. In "
     "Britain a muffin is a flat, round yeast bread, split and toasted; in America a muffin is a "
     "soft, barely sweet quick bread with no icing at all. So a muffin is bread and a cupcake is cake."),
    (("scone", "scones"), ("rock cake", "rock cakes", "rock bun", "rock buns"),
     "A scone is a soft dough rolled and cut, baked hot for 10 to 12 minutes, and it should be light "
     "enough to break open. A rock cake is a stiff dough with dried fruit dropped in rough lumps, so "
     "it bakes into a craggy top - heavier, sweeter, and it keeps for days where a scone does not."),
    (("solicitor", "solicitors"), ("barrister", "barristers"),
     "A solicitor does the day-to-day work: contracts, letters, a house purchase, the first meeting. "
     "A barrister is the one who argues in court, and you reach one through a solicitor. A lawyer is "
     "the general word for both."),
    (("hire", "hiring"), ("rent", "renting"),
     "You hire a thing for hours or days - a van, a carpet cleaner, a hall - and rent a home or a "
     "piece of land for months or years. Hire is short and usually about the item, rent is long and "
     "usually about the place."),
    # Everyday pairs from the money, home, garden and body domains, where the two words look like
    # one thing and are not. Each row is two names and the difference that changes what you do.
    (("bank", "banks", "high street bank"),
     ("building society", "building societies", "mutual"),
     "A bank is owned by shareholders; a building society is owned by the people who save with it and "
     "borrow from it, which is why its profit goes back out as better rates rather than a dividend. "
     "Your money is protected the same either way - £85,000 per person per bank or society under the "
     "FSCS - and the card, the ISA and the app work the same. Choose on the rate, not the label."),
    (("sale", "sales", "in the sale"), ("offer", "offers", "on offer"),
     "An offer is a lower price on one thing, usually for a set time; a sale is a shop cutting prices "
     "across the board. Neither word has a legal meaning, so the price on the till is the one that "
     "counts - and your right to a refund on something in a sale is exactly the same as outside one."),
    (("envy", "envious", "jealousy of"), ("jealous", "jealousy"),
     "Envy is wanting what someone else has: their house, their job, their holiday. Jealousy is the "
     "fear of losing what you have, and it needs a third person - a partner's new friend, a "
     "colleague who is close to your boss. So envy looks outwards and jealousy guards something."),
    (("warranty", "warranties", "extended warranty"),
     ("guarantee", "guarantees", "manufacturer guarantee"),
     "A guarantee is the maker's own promise to repair or replace the thing within a set time, usually "
     "a year or two and often only if you registered it. A warranty is usually the extra cover a shop "
     "sells you. Neither replaces your rights against the retailer: in England and Wales a faulty "
     "product can be put right for up to six years, warranty or no warranty."),
    (("sprain", "sprains", "sprained"), ("strain", "strains", "pulled muscle", "pulled a muscle"),
     "A sprain is a stretched or torn ligament - the band joining bone to bone - so it happens at a "
     "joint, most often a twisted ankle. A strain is a stretched or torn muscle or tendon in the meat "
     "of a leg, back or arm. The first day is the same for both: rest it, ice for 20 minutes every few "
     "hours, wrap it, keep it up; see someone if you cannot put weight on it."),
    # Two names for one injury, which is the other half of the pair: people are told they have a
    # fracture and ask whether it is worse than a break.
    (("fracture", "fractures", "fractured", "broken bone", "broken bones", "hairline fracture"),
     ("break", "breaks", "broken", "broke"),
     "Nothing: a fracture and a break are the same injury, and a doctor saying fracture is not saying "
     "it is worse. A hairline or stress fracture is a fine crack, and a greenstick fracture is a "
     "bone bent and cracked on one side, which is what children get. What changes the treatment is "
     "not the word but where the bone is and whether the ends still line up, so ask about that "
     "instead."),
    (("leasehold", "leaseholder", "leaseholders"), ("freehold", "freeholder", "freeholders"),
     "Freehold means you own the building and the land under it; leasehold means you own the right to "
     "live there for a fixed number of years and someone else owns the building and the ground. A "
     "leaseholder pays ground rent and usually a service charge, and the lease gets shorter every year, "
     "which is what a buyer and a mortgage lender look at. Most flats are leasehold and most houses "
     "freehold."),
    (("flat", "flats"), ("apartment", "apartments"),
     "Nothing: a flat and an apartment are the same home, and the choice is taste - flat is the "
     "everyday British word, apartment the estate agent's and the usual one in America and for a "
     "serviced block. A maisonette is the one that differs, being on two floors with its own entrance."),
    (("annual", "annuals", "annual plant"), ("perennial", "perennials", "perennial plant"),
     "An annual grows, flowers and dies within one year, so it is sown again every spring; a perennial "
     "comes back from the same roots year after year. Annuals flower for months and fill a bed cheaply, "
     "perennials cost more and give a few weeks each year, so most beds use both."),
    (("mulch", "mulching", "mulched"), ("compost", "composting", "composted"),
     "Compost is rotted organic matter dug into the soil to feed it; mulch is anything spread on top of "
     "the soil to hold water and keep weeds down, and it can be compost, bark, manure or gravel. So "
     "compost improves the soil and mulch is a blanket: you can mulch with compost, but you do not dig "
     "gravel in."),
    (("boil", "boils", "a boil on"), ("cyst", "cysts"),
     "A boil is a deep infection of a hair follicle: tender, hot, and it swells up and comes to a head. "
     "A cyst is a closed sac under the skin, usually smooth and painless, holding fluid or keratin, and "
     "it does not drain and heal by itself. A boil often needs an antibiotic and to drain; a cyst that "
     "keeps filling is cut out. Do not squeeze either."),
    # A lager and an ale are the same drink brewed with a different yeast at a different heat, and
    # beer is the word for both: people ask this pair by name ("lager and ale"), and the pair also
    # rides on "lager or beer", which no entry answers.
    (("lager", "lagers"), ("ale", "ales", "bitter", "real ale"),
     "Lager and ale are both beer, brewed with different yeast: lager uses a yeast that works cold "
     "at the bottom of the tank, ale a yeast that works warm at the top. Cold and slow gives lager "
     "its clean, crisp taste; warm and quick gives ale its fruitiness and its hops. Stout and porter "
     "are ales brewed dark, so colour says nothing about which one you have."),
    (("lager", "lagers", "ale", "ales", "stout", "stouts", "porter", "pilsner"),
     ("beer", "beers"),
     "Beer is the whole family, and lager and ale are the two branches of it: lager is brewed cold "
     "with a bottom yeast, ale warm with a top one. So every lager is a beer and not every beer is a "
     "lager - bitter, stout, porter and wheat beer are all ales. If a pub list says \"beers\" it is "
     "offering both."),
    (("rabbit", "rabbits", "bunny", "bunnies"), ("hare", "hares"),
     "A hare is much bigger and longer-legged than a rabbit, with long ears tipped black, and it "
     "lives above ground in a form - a shallow scrape - rather than a burrow. Hares are born fully "
     "furred with their eyes open and are running within hours; rabbits are born blind and bald in a "
     "lined nest underground. Hares are also solitary and rabbits live in groups, so a big, loping, "
     "lonely one in a field is a hare."),
    (("moped", "mopeds", "scooter", "scooters"), ("motorbike", "motorbikes", "motorcycle",
                                                  "motorcycles"),
     "A moped is up to 50cc and 28mph, and you can ride one at 16 on a provisional licence after a "
     "CBT - that is what the pedals-then-engine history of the name means. A motorbike is anything "
     "bigger, from a 125 at 17 to a full licence, and it needs the tests, insurance and a proper "
     "helmet. A scooter is a shape rather than a class: most small ones are moped-legal at 50cc."),
    # The one pair where a wrong answer matters, so it ends the way the health cards do.
    (("heart attack", "heart attacks"), ("panic attack", "panic attacks", "anxiety attack"),
     "A heart attack is a blocked artery: heavy, crushing pressure in the middle of the chest, often "
     "spreading to the left arm, the jaw or the back, with sweating, sickness and breathlessness, "
     "brought on by effort and lasting more than fifteen minutes. A panic attack peaks within ten "
     "minutes: racing heart, tingling hands, dizziness and a fear of dying, usually at rest, and it "
     "eases as you breathe slowly. Chest pain that is new, crushing or comes with sweating is a 999 "
     "call - do not wait to work out which one it is."),
    # The everyday one that answered with the wrong card: "heart rate and blood pressure" got a
    # low-blood-pressure reading. Both names are in the line, so the pair answers and the card does
    # not have to stand anything down.
    (("heart rate", "pulse", "pulse rate", "bpm", "beats per minute"),
     ("blood pressure", "bp", "readings", "reading"),
     "Heart rate is how fast the heart beats, counted in beats a minute: 60 to 100 at rest is "
     "normal, and it rises with exercise, caffeine and stress. Blood pressure is how hard the blood "
     "pushes on the artery walls, written as two numbers - the top one when the heart squeezes, the "
     "bottom one between beats - and around 120/80 is a good reading. A fast pulse and a high "
     "pressure are separate things: you can have one without the other."),
    (("pill", "pills", "tablet", "tablets"), ("capsule", "capsules"),
     "A tablet is powder pressed into a disc, and it can be split or crushed (unless the packet says "
     "otherwise, because some are coated to release slowly). A capsule is a shell - usually gelatine "
     "or a vegetable gum - filled with powder, granules or liquid, so it is swallowed whole and "
     "opens in the stomach. If swallowing is the problem, ask the pharmacist before crushing: many "
     "tablets are not meant to be."),
    (("magpie", "magpies"), ("crow", "crows", "carrion crow", "rook", "rooks"),
     "A magpie is black and white with a long tail, about 45cm, and it is unmistakable. A crow is "
     "all black, bigger than a pigeon and often alone or in a pair, with a heavy bill and a harsh "
     "caw; rooks are the ones in noisy flocks with bare grey faces. If it has any white on it, it is "
     "not a crow."),
    (("maisonette", "maisonettes"), ("flat", "flats", "apartment", "apartments", "bungalow"),
     "A maisonette is a flat on two floors with its own front door to the outside, so it has stairs "
     "inside and no shared hall. A flat is usually on one level off a shared entrance, and a "
     "bungalow is a house with everything on the ground floor. A maisonette feels more like a house "
     "and is often leasehold all the same, so check the lease and the service charge."),
    (("mortgage broker", "brokers", "broker", "independent adviser"),
     ("bank", "banks", "building society", "lender", "lenders"),
     "A broker does not lend the money: they compare the deals on the market and apply to a lender "
     "for you, and many charge a fee on top of the lender's arrangement fee. Going to a bank "
     "directly means one lender's own deals with no broker fee, which is fine if your case is "
     "straightforward. A whole-of-market broker earns its fee when your pay is unusual, your deposit "
     "is small or your credit file is untidy."),
    # Pairs a person names in one breath and expects to be told apart. Each was answered on main by
    # a card about one half of the pair, or by the search hedge: "difference between hp and pcp" got
    # the buy-a-used-car card, and vegan and vegetarian, a therapy and counselling, an allergy and an
    # an intolerance, a mortgage broker and a bank, and a midwife and a health visitor were all
    # "that is beyond what I know well". A pair another table already answers is deliberately not in
    # this one - `bot/knowledge/differences.py` holds celsius and fahrenheit, butter and margarine,
    # flu and covid, a cold sore and a mouth ulcer, a tablet and a laptop, a psychiatrist and a
    # psychologist, and an allergy and an intolerance, and `a-break-is-not-a-shift` holds a sprain
    # and a break. Those rows were here and never fired; a second copy of a pair is a second answer
    # nobody reads.
    (("hp", "hire purchase", "hp agreement", "hp finance"),
     ("pcp", "personal contract purchase", "pcp finance", "pcp deal"),
     "With hire purchase you pay a deposit and fixed monthly payments, and at the end of the term "
     "the car is yours - nothing more to pay. With PCP you pay a smaller deposit and smaller months "
     "for a mileage limit, then choose at the end: hand the car back, part-exchange it, or pay a "
     "large final payment to keep it. PCP is cheaper per month and costs more over the years, and "
     "excess miles are charged at a few pence each, so HP suits keeping a car and PCP suits "
     "changing it every three years."),
    (("ukulele", "uke", "ukuleles"), ("guitar", "guitars", "acoustic guitar"),
     "A ukulele has four nylon strings, a much smaller body and the tuning G-C-E-A; a guitar has six "
     "steel or nylon strings in E-A-D-G-B-E and two and a half octaves more range. The ukulele is "
     "the easier first instrument by a wide margin - four strings, soft on the fingers, and most "
     "chords need two or three fingers - while a guitar can play bass lines and full chords. A "
     "baritone ukulele is the size of a small guitar and is tuned to the guitar's top four strings."),
    (("vegan", "vegans", "veganism"), ("vegetarian", "vegetarians", "vegetarianism"),
     "A vegetarian eats no meat or fish but does eat dairy and eggs; a vegan eats nothing that comes "
     "from an animal at all, so no milk, cheese, butter, eggs or honey, and no gelatine or leather "
     "either. Vegan is the stricter one, so every vegan meal is vegetarian and not the other way "
     "round. The one thing to watch on a vegan diet is vitamin B12, which is only in animal food, so "
     "it comes from fortified milk and cereals or a supplement."),
    (("therapy", "therapist", "psychotherapy", "talking therapy", "cbt",
      "psychologist", "psychologists"),
     ("counselling", "counseling", "counsellor", "counselor"),
     "In Britain the words overlap and both mean talking to a trained person, so the honest "
     "difference is the shape of the sessions rather than the label. Counselling is usually the "
     "listening kind - six to twelve weekly sessions on one problem, such as a bereavement or a "
     "decision - while therapy is often longer and follows a method, CBT being the commonest: "
     "homework, thought records and a plan you work through. Ask any of them which body they are "
     "accredited with, BACP for counsellors and BABCP for CBT, and whether they are on the NHS "
     "talking therapies list, where both are free."),
    # Seven more, all of them a punt on main ("that's beyond what I know well"): a laptop and a
    # chromebook, an osteopath and a chiropractor, a mushroom and a toadstool, a bee and a wasp, a
    # pandemic and an epidemic, a latte and a cappuccino, and a midwife and a health visitor.
    (("chromebook", "chromebooks"), ("laptop", "laptops", "windows laptop", "macbook"),
     "A chromebook runs ChromeOS, which is mostly a browser: it starts in seconds, costs a couple "
     "of hundred pounds and gets ten hours on a charge, and most of what it does needs a "
     "connection. A laptop runs Windows or macOS, so it can install real programs and play games, "
     "and it costs two to four times as much. For browsing, writing and schoolwork a chromebook is "
     "enough; for photographs, video editing or games it is not."),
    (("osteopath", "osteopaths", "osteopathy"),
     ("chiropractor", "chiropractors", "chiropractic"),
     "Both treat back and joint pain with their hands and both are regulated - osteopaths by the "
     "General Osteopathic Council, chiropractors by the General Chiropractic Council - and neither "
     "needs a GP referral. An osteopath works on the whole body with slow stretching and rhythmic "
     "pressure, and a chiropractor mostly adjusts the spine, often with the quick movement that "
     "cracks. For ordinary low back pain the evidence for both is about the same as for physiotherapy, "
     "so pick on the person: a first session is usually 40 to 70 pounds."),
    (("mushroom", "mushrooms", "field mushroom"), ("toadstool", "toadstools"),
     "There is no scientific difference: a toadstool is just the old word for a mushroom somebody "
     "thought was poisonous, so the two names tell you nothing about whether one is safe to eat. "
     "Only the species does, and some of the deadliest in Britain look like ordinary field "
     "mushrooms, so pick by species with a book or an expert and never by the word. If someone has "
     "eaten an unknown one, keep the remains and ring 111 or the poisons line rather than wait for "
     "symptoms."),
    (("bee", "bees", "bumblebee", "bumblebees", "honeybee", "honeybees"),
     ("wasp", "wasps", "yellow jacket", "yellowjacket"),
     "A bee is furry, round and brownish or striped softly, and a honeybee dies after one sting "
     "because the sting stays in the skin; a wasp is smooth, bright yellow with black bands and a "
     "pinched waist, and it can sting over and over. Bees are after nectar and pollen and leave you "
     "alone; wasps hunt insects and in late summer want sugar, which is why they come for your "
     "drink. Flick a wasp away rather than swat it, and if a sting brings swelling of the face or "
     "trouble breathing, that is 999."),
    (("pandemic", "pandemics"), ("epidemic", "epidemics"),
     "An epidemic is more cases of an illness than expected in one place or country; a pandemic is "
     "the same thing spread across several countries or continents, so every pandemic starts as an "
     "epidemic and most epidemics never become one. The third word is endemic: an illness that is "
     "always with us at a steady level, like the common cold or flu in winter. Size makes the "
     "difference, not how dangerous the germ is."),
    (("latte", "lattes", "caffe latte"), ("cappuccino", "cappuccinos"),
     "Both are espresso and steamed milk, and the difference is the milk: a cappuccino is roughly "
     "equal thirds espresso, milk and thick foam in a 150 to 180ml cup, and a latte is mostly milk "
     "with a thin layer of foam on top in a 240 to 300ml glass. So a latte is milder and bigger and "
     "a cappuccino is foamier and stronger, and a flat white sits between them with two shots and "
     "very fine foam."),
    (("midwife", "midwives", "community midwife"),
     ("health visitor", "health visitors"),
     "A midwife looks after you and the baby through pregnancy, the birth and the first 28 days: the "
     "appointments, the birth itself, the checks and the feeding help. A health visitor is a nurse "
     "or midwife with extra training who takes over at about ten to fourteen days and stays until "
     "the child is five, doing the weighing and development checks, the postnatal depression "
     "questions and the advice on sleep, food and behaviour. Both are free on the NHS and you do "
     "not need to ask for either - they come to you."),
    (("income tax",), ("national insurance", "ni contributions", "national insurance contributions"),
     "Income tax is taken from your pay and funds everything the government spends; National Insurance "
     "is a separate contribution on your earnings that buys your State Pension and some benefits, so "
     "the two lines on a payslip buy different things. NI stops when you reach State Pension age and "
     "income tax does not, and only NI needs the qualifying years."),
)

# The rest of the pairs people actually ask about, added the same way: the question is the pair, so
# a row is two name groups and the one distinction that changes what you do. These are the pairs a
# person asks a friend about - the animal in the garden, the word in the recipe, the two names for
# one jumper - and every one of them met a search hedge or another row's card on its own.
DIFFERENCES += (
    (("moth", "moths"), ("butterfly", "butterflies"),
     "A butterfly flies by day and rests with its wings folded upright over its back, and its "
     "antennae are thin with a club at the tip. A moth mostly flies at night, rests with its wings "
     "spread flat or tented, and has feathery or plain antennae - a few, like the hummingbird "
     "hawk-moth, fly by day and still read as moths."),
    (("rabbit", "rabbits", "bunny", "bunnies"), ("hare", "hares"),
     "A hare is bigger and lankier, with long ears and long back legs, and its young are born "
     "furred with their eyes open, in a scrape on the ground, ready to run within hours. A rabbit "
     "is smaller and rounder, lives in a burrow in a group, and its young are born blind, bald and "
     "helpless. So a leveret sitting still in a field is normal - leave it where it is."),
    (("bee", "bees", "honeybee", "honeybees", "bumblebee", "bumblebees"),
     ("wasp", "wasps", "yellow jacket"),
     "A bee is fuzzy and lives on pollen and nectar, and only defends the nest - a honeybee dies "
     "when it stings. A wasp is smooth and bare, with a tight waist and bright yellow bands, and it "
     "hunts other insects for its grubs; in late summer, when the grubs are grown, it scavenges "
     "anything sweet and stings more, and it can sting again and again."),
    (("wasp", "wasps", "yellow jacket"), ("hornet", "hornets"),
     "A hornet is the biggest of the wasp family - a European hornet is 3 to 3.5 cm - and it is "
     "brown with orange bands rather than black and yellow. Its sting is no worse venom for venom "
     "than a wasp's, there is simply more of it, and it is far less interested in your picnic: it "
     "hunts insects at dusk. Sightings of the Asian hornet should go to the app or the number on "
     "the Government's page."),
    (("crow", "crows"), ("raven", "ravens"),
     "A raven is much bigger - getting on for buzzard size, twice the weight of a carrion crow - "
     "with a heavy bill, shaggy throat feathers, a wedge-shaped tail and a deep croaking call. A "
     "crow has a fanned tail and a harsh caw, and gathers in flocks in fields and towns, while "
     "ravens keep to pairs on moors, cliffs and hills."),
    (("monkey", "monkeys"), ("ape", "apes"),
     "An ape has no tail, a broad chest and arms built for hanging from branches, and a bigger "
     "brain: gibbons, chimps, gorillas, orangs and people. A monkey usually has a tail and runs "
     "along a branch on all fours: baboons, macaques, marmosets. So a chimpanzee is an ape and a "
     "baboon is a monkey."),
    (("seal", "seals"), ("sea lion", "sea lions"),
     "A sea lion has small ear flaps you can see, long front flippers it can walk on, and it barks; "
     "a true seal has no ear flaps, short front flippers, and it hauls itself along on its belly, "
     "and it is mostly silent. So the seal on a British beach is a grey or common seal, one of the "
     "true seals."),
    (("rat", "rats"), ("mouse", "mice"),
     "A rat runs to 20 to 25 cm in the body, with a thick tail as long again, a blunt nose and "
     "small ears; a mouse is 7 to 10 cm, with a pointed nose, big ears and a thin tail about as long "
     "as its body. Rats travel the same run each night from drains, rubbish and walls; house mice "
     "live indoors in cupboards and under the floor."),
    (("hamster", "hamsters"), ("gerbil", "gerbils"),
     "A hamster is stocky, lives alone and sleeps most of the day, and two adults in one cage will "
     "fight. A gerbil is slimmer with a long tufted tail, lives happily in a pair, and is up and "
     "about on and off through the day and night, wanting deep bedding to dig in. So a gerbil wants "
     "company and a hamster wants a cage of its own."),
    (("hen", "hens"), ("chicken", "chickens"),
     "A chicken is the bird; a hen is an adult female, a pullet is a young female before she starts "
     "laying, and a cockerel is the male. Hens lay without a cockerel - those eggs are simply "
     "unfertilised - so a household that wants eggs needs hens only."),
    (("goose", "geese"), ("duck", "ducks"),
     "A goose is the bigger bird, with a long neck and legs set further back, and it grazes grass; "
     "a duck is smaller with a shorter neck, and it dabbles in water for insects and weed. Geese "
     "are louder, bolder and better guards, and ducks are calmer and easier in a small garden."),
    (("sheep",), ("lamb", "lambs"),
     "A lamb is a sheep under about a year old; a hogget is one to two years, and mutton is older "
     "than that. Lamb is milder and quicker to cook, and mutton has more fat and flavour and wants "
     "a long, slow pot."),
    (("koala", "koalas"), ("bear", "bears"),
     "A koala is not a bear: it is a marsupial, related to the wombat, that carries its joey in a "
     "pouch and lives almost entirely on eucalyptus leaves. A bear is a placental meat-eater, so "
     "the two are on different branches of the mammals altogether."),
    (("bison",), ("buffalo", "buffaloes", "water buffalo"),
     "A bison has a huge shoulder hump, a beard and a shaggy woolly coat, and it lives on the "
     "plains of North America and Europe. A buffalo is a different animal - the water buffalo of "
     "Asia and the Cape buffalo of Africa - and both carry horns that curve out, with no shoulder "
     "hump. The one in the western and on the nickel is a bison."),
    (("centipede", "centipedes"), ("millipede", "millipedes"),
     "A centipede has one pair of legs to each segment, a flattened body and real speed: it hunts, "
     "and the front pair of legs carries venom. A millipede has two pairs to a segment and a round "
     "body, is slow, has no venom, and lives on rotting leaves."),
    (("llama", "llamas"), ("alpaca", "alpacas"),
     "An alpaca is the smaller of the two, with a short blunt face and upright, banana-shaped ears, "
     "and it is kept for its fine wool. A llama is taller, with a longer head and long ears that "
     "curve back, and it is used as a pack animal and as a guard for a flock. Llamas are more "
     "independent and will face a fox; alpacas are easily spooked."),
    (("dolphin", "dolphins"), ("porpoise", "porpoises"),
     "A dolphin has a long beak, cone-shaped teeth and a curved fin, and it is sociable and noisy. "
     "A porpoise is smaller and stouter, with a blunt face, spade-shaped teeth and a small triangular "
     "fin, and it is shy and quiet - so the small grey back arcing fast off a British shore, with no "
     "show at all, is usually a porpoise."),
    (("hawk", "hawks"), ("falcon", "falcons"),
     "A hawk is broad-winged with rounded tips and a plain hooked bill, and it hunts from a perch "
     "or a long soar: buzzards, sparrowhawks, goshawks. A falcon has long pointed wings and a notch "
     "on the beak, and it hunts in fast level flight or a stoop: kestrels, peregrines, hobbies. So "
     "the bird hovering over a verge is a kestrel, a falcon, and the one circling on flat wings with "
     "a mewing call is a buzzard, a hawk."),
    (("sweet potato", "sweet potatoes"), ("yam", "yams"),
     "Sweet potatoes are the orange- or cream-fleshed roots in most supermarkets; true yams are the "
     "big dark roots with bark-like skin sold in African and Caribbean grocers, and they need "
     "peeling and a long cook. In America an orange 'yam' is usually a sweet potato under another "
     "name, so cook what you bought as you would a sweet potato."),
    (("courgette", "courgettes", "zucchini", "zucchinis"), ("cucumber", "cucumbers"),
     "A courgette comes from the marrow family and is cooked: soft edible skin, spongy seedy "
     "middle, and it softens in the pan. A cucumber is watery and eaten raw, usually peeled or "
     "scored, and it turns to mush if you cook it. Small ones look alike; the taste does not."),
    (("clementine", "clementines", "satsuma", "satsumas", "tangerine", "tangerines",
      "mandarin", "mandarins"), ("lemon", "lemons", "orange", "oranges", "grapefruit"),
     "All the easy peelers are mandarins: a satsuma is the earliest, with the loosest skin and "
     "usually no pips, a clementine is smaller and sweeter and sometimes has a few, and a tangerine "
     "is deeper orange with a stronger taste. Sweet and easy to peel means a satsuma or clementine, "
     "so pick one that feels light for its size - and a lemon, an orange or a grapefruit is none of "
     "them."),
    (("clementine", "clementines", "tangerine", "tangerines", "mandarin", "mandarins"),
     ("satsuma", "satsumas"),
     "A satsuma is the loosest-skinned easy peeler and usually has no pips, and it is the earliest "
     "of them in the shops. A clementine is smaller and sweeter with a tighter skin, and it "
     "sometimes has a few pips. Both are mandarins, so buy whichever feels light for its size."),
    (("latte", "lattes"), ("flat white", "flat whites"),
     "A latte is a shot of espresso with a lot of steamed milk, around 220ml in a cafe mug, so it "
     "is mild and milky. A flat white is the same shot with far less milk, about 130ml, in a "
     "smaller cup, so the coffee tastes stronger. If you want the coffee to taste of coffee, order "
     "the flat white."),
    (("lease", "leases"), ("tenancy", "tenancies", "tenancy agreement"),
     "In Scotland a lease is what the rest of the UK calls a tenancy: the written agreement that "
     "sets the rent and the notice. In England and Wales the usual one is an assured shorthold "
     "tenancy, and a lease is the long agreement you buy when you own a flat. So a lease in "
     "Scotland is short and a lease in England is long."),
    (("jam", "jams"), ("jelly", "jellies", "preserve", "preserves"),
     "In Britain jam has the fruit in it and jelly is the clear set made from strained juice, and "
     "in America 'jelly' is that clear set while 'jam' is the British jam. Marmalade is citrus with "
     "shreds of peel, and a preserve is the chunky one with whole or large pieces of fruit. So a "
     "US recipe that says jelly wants the smooth, clear set."),
    (("griddle", "griddles", "griddle pan"), ("frying pan", "frying pans", "fry pan"),
     "A griddle is flat, or ridged, and heavy, with low or no sides: a plate of heat for pancakes, "
     "bacon and several chops at once, and fat runs off a ridged one. A frying pan has deep sloping "
     "sides, so things can be tossed in it and the fat or sauce stays in."),
    (("slow cooker", "slow cookers"), ("pressure cooker", "pressure cookers"),
     "A slow cooker cooks on low for six to eight hours and can be left all day; a pressure cooker "
     "seals the steam in and does the same work in a third of the time or less, under pressure. "
     "Beans, tough cuts and stock are far quicker in the pressure cooker, and a stew you want "
     "waiting when you get in is the slow cooker's."),
    (("broil", "broils", "broiling", "broiled"), ("grill", "grills", "grilling", "grilled"),
     "In Britain the grill is the heat from above and a barbecue is over the coals; in America "
     "'broil' is the heat from above and 'grill' is over the coals. So a US recipe that says broil "
     "means the grill pan under the element, and where an American says grill, light the barbecue."),
    (("jumper", "jumpers"), ("sweater", "sweaters"),
     "Nothing: a jumper and a sweater are the same knitted top, jumper being the British word and "
     "sweater the American one. A cardigan is the one that opens down the front, and a pullover is "
     "any of them you put on over your head."),
    (("trainer", "trainers"), ("sneaker", "sneakers"),
     "Nothing: a trainer is the British word for a sneaker, and both are the same soft sports shoe. "
     "Plimsolls are the flat canvas ones, and 'runners' is what Americans call the sort you run in."),
    (("biscuit", "biscuits"), ("cookie", "cookies"),
     "In Britain a biscuit is the crisp flat sort - digestives, rich tea - and a cookie is the soft, "
     "chunky American-style one. In America both are cookies, and an American biscuit is a soft, "
     "scone-like bread eaten with gravy. So a British recipe for cookies wants the chewy kind."),
    (("savings account", "savings accounts"), ("isa", "isas", "cash isa", "cash isas"),
     "Interest in a cash ISA is free of tax; interest in an ordinary savings account is taxed once "
     "it is past your personal savings allowance - £1,000 a year at basic rate, £500 at higher "
     "rate, nothing at additional rate. So if the rates are close the ISA wins, and if the ordinary "
     "account pays much more, do the sum."),
    (("loan", "loans"), ("overdraft", "overdrafts"),
     "An overdraft is borrowing on your current account, meant for days rather than months: it is "
     "charged by the day or the month and the bank can withdraw it. A loan is a fixed sum paid back "
     "over an agreed term at an agreed rate. So a few days over is an overdraft, and anything over a "
     "month or two is usually cheaper as a loan."),
    (("tenant", "tenants"), ("lodger", "lodgers"),
     "A tenant rents a whole home and has a tenancy, so the landlord needs a court order to evict "
     "them and the notice the law sets. A lodger lives in the same home as the owner, sharing the "
     "kitchen and bathroom, and can be asked to leave on reasonable notice - usually the rent "
     "period. So the spare room in your own house holds a lodger, and the flat next door a tenant."),
    (("supervisor", "supervisors"), ("manager", "managers"),
     "A supervisor runs the shift: what gets done today, by whom, and to what standard. A manager "
     "carries the budget, the hiring, the targets and the reviews. Titles vary from one employer to "
     "the next, so the tell is who spends the money and who decides the people."),
    (("loft", "lofts"), ("attic", "attics"),
     "The same space under the roof: a loft is the bare one holding the boxes, and an attic is that "
     "space made into a room. In Britain the job is a loft conversion; in America it is an attic "
     "room."),
    (("patio", "patios"), ("deck", "decks", "decking"),
     "A patio is paving or concrete laid on the ground; a deck is timber boards on a raised frame. "
     "A patio is cheaper, lasts decades with little care and stays cool underfoot; a deck goes down "
     "faster on uneven ground, is warmer barefoot and needs treating and cleaning every year or two."),
    (("shrub", "shrubs"), ("bush", "bushes"),
     "Nothing: a shrub is the gardener's word for a bush, a woody plant with several stems from the "
     "base rather than one trunk. If the stems meet the ground in a cluster it is a shrub; a tree has "
     "a single trunk."),
    (("statement", "statements"), ("receipt", "receipts"),
     "A receipt is the proof of one purchase, and it is what a shop asks for if you want a refund or "
     "a swap. A bank statement lists everything that went in and out of an account over a month. "
     "Keep the receipt for anything you might return, and the statement is for checking what left "
     "your account."),
    (("cv", "cvs", "resume", "resumes"), ("cover letter", "covering letter", "covering"
      " letters", "cover letters"),
     "A CV is the one- or two-page record of what you have done - jobs, dates, qualifications - and "
     "it is the same document for every application. A cover letter is the short note written for "
     "that one job: why you want it and what you would bring. The CV carries the facts and the "
     "letter makes the case."),
    (("psychiatrist", "psychiatrists"), ("psychologist", "psychologists"),
     "A psychiatrist is a medical doctor who can diagnose mental illness and prescribe medicine; a "
     "psychologist is trained in psychology and works with talking therapy and testing, and cannot "
     "prescribe. In Britain a GP refers you to a psychiatrist, and you can reach a psychologist "
     "through the NHS or privately."),
    (("novella", "novellas"), ("novel", "novels"),
     "A novel is the long one, usually over 50,000 words; a novella runs from about 17,500 to 40,000, "
     "long enough for a chapter of depth and short enough to read in an evening. Under about 17,500 "
     "it is a long short story. Publishers are loose about the line; for a reader, judge by whether "
     "it takes a sitting."),
    (("autobiography", "autobiographies"), ("biography", "biographies"),
     "An autobiography is a life written by the person who lived it, and a biography is written by "
     "somebody else. A memoir is the autobiography's selective cousin: the part of a life that "
     "bears on one theme."),
    (("cold sore", "cold sores"), ("ulcer", "ulcers"),
     "A cold sore is the herpes virus: a cluster of small blisters on a tingle, usually at the edge "
     "of the lip, which crusts over in a few days and comes back in the same spot when you are run "
     "down. A mouth ulcer is a raw pale patch inside the mouth, on the tongue, cheek or gum - not "
     "blistered and not catching - and it usually heals in a week or two. A cold sore is worth a "
     "pharmacist's cream in the first day or so; an ulcer that lasts past three weeks is worth "
     "showing to a dentist."),
    (("stock cube", "stock cubes"), ("bouillon cube", "bouillon cubes", "bouillon"),
     "Nothing much: bouillon is French for stock, and a bouillon cube is the same cube of salt, "
     "yeast extract and flavourings in a different wrapper. Powder, paste and jelly pots do the same "
     "job. What matters is the salt - taste before you season - and whether the stock is the point "
     "of the dish, because fresh stock beats a cube when it is."),
    (("fridge", "fridges", "refrigerator"), ("freezer", "freezers"),
     "A fridge runs at 0 to 5C, cold enough to slow the bugs that spoil food: milk keeps for days and "
     "cooked food for a few. A freezer runs at -18C, where almost nothing grows, so food keeps for "
     "months - but freezing does not kill the bugs, it only parks them, so it still has to be "
     "cooked properly after it thaws."),
    (("tune", "tunes", "melody", "melodies"), ("song", "songs"),
     "A tune is the melody on its own, the bit you hum; a song has words and a voice on top of the "
     "tune. So an instrumental has a tune but is not a song, and something the words carry - a rap, "
     "a hymn sung flat - is still a song."),
    (("shallow fry", "shallow frying", "shallow-fry", "shallow-frying"),
     ("deep fry", "deep frying", "deep-fry", "deep-frying"),
     "Shallow frying is a centimetre or two of oil in a pan, with the food turned once; deep frying "
     "covers the food, so it crisps all over and cooks quickly. Deep frying wants more oil, a "
     "thermometer and a lid, and 170 to 190C - too cool and the food drinks the oil, too hot and the "
     "outside burns before the middle is done."),
    (("puppy", "puppies", "pup", "pups"), ("dog", "dogs"),
     "A puppy is a dog under about a year, and the difference that matters is what it can do: a "
     "puppy eats food built for growth, three or four small meals a day, and needs short play and "
     "long sleeps. An adult dog eats twice a day and can run for an hour. Big breeds are still "
     "growing at 18 months, so a large puppy at a year is still a puppy."),
    (("kitten", "kittens"), ("cat", "cats"),
     "A kitten is a cat under about a year: it needs kitten food with more protein and fat, several "
     "small meals, warmth and company, and everything is still being learned - scratch posts, short "
     "gentle play, and one room at a time in a new house. A grown cat wants less food and less "
     "fuss, and it sleeps two thirds of the day."),
    (("magpie", "magpies"), ("crow", "crows", "raven", "ravens"),
     "A magpie is a corvid the size of a small crow, black and white with a long wedge of a tail; a "
     "crow is all black, bigger, and gathers in flocks in fields. Both are in the crow family, with "
     "the jay, the jackdaw and the rook."),
    (("syrup", "syrups"), ("sauce", "sauces"),
     "A syrup is sugar dissolved in water - golden, maple, treacle - thin and pourable; a sauce is "
     "thickened to coat, with flour, cornflour, egg or cream, and it may not be sweet at all. A "
     "syrup is poured over and soaks in; a sauce sits on top."),
    (("contract", "contracts"), ("agreement", "agreements"),
     "An agreement is any two people saying yes to the same thing; a contract is an agreement the "
     "law will enforce, which needs an offer, an acceptance and something of value each way - and no "
     "signature at all, since a yes by email or a deposit paid can be enough. So every contract is "
     "an agreement, and most agreements are not contracts."),
    (("credit score", "credit scores"), ("credit report", "credit reports", "credit file",
      "credit files"),
     "The report is the record: every account, payment and search in your name, kept by Experian, "
     "Equifax and TransUnion. The score is a number one of those agencies works out from the report. "
     "So you fix the report - correct the errors, register to vote, pay on time, keep balances low - "
     "and the score follows."),
    (("meeting", "meetings"), ("catch up", "catch-up", "catchup", "catch ups"),
     "A meeting has an agenda and a decision at the end; a catch-up is a short, informal check-in "
     "with no decision to make, usually one to one. Call a meeting when something has to be agreed "
     "and a catch-up when you only need to stay in touch - and say which it is in the invitation."),
    (("hedge", "hedges"), ("fence", "fences"),
     "A hedge is living, so it wants clipping once or twice a year and it dies if it is not watered "
     "in a drought; a fence is built, wants treating every few years and will need replacing in 15 "
     "to 20. A hedge gives birds cover and slows the wind; a fence goes up in a weekend, costs less "
     "and takes up no ground."),
    (("squirrel", "squirrels"), ("chipmunk", "chipmunks"),
     "A chipmunk is much smaller - about 15 cm in the body, with a short tail - and it has stripes "
     "down its face and back and lives on the ground in a burrow in North America. A squirrel is "
     "bigger, with a long bushy tail and no face stripes, and it climbs. So the striped thing in a "
     "British garden is a grey squirrel in good light, not a chipmunk."),
    (("lizard", "lizards"), ("gecko", "geckos"),
     "A gecko is one family of lizard: soft skin with tiny scales, no eyelids on most kinds (they "
     "lick the eye clean), toe pads that grip glass, and a chirp. The lizard in a British garden is "
     "usually a common lizard or a slow worm - dry scales, eyelids, and no voice at all."),
    (("career", "careers"), ("job", "jobs"),
     "A job is what you are paid to do now, with a contract and a wage; a career is the run of them "
     "and the direction - the skills, the reputation, the next step. So changing jobs can be no "
     "change of career at all, and a career change often starts with a pay cut."),
    (("bungalow", "bungalows"), ("house", "houses"),
     "A bungalow is a house of one storey, so there are no stairs; house covers any of them. In "
     "Britain the word usually means a single-storey home with its own front door, and it is priced "
     "and built differently: easier to live in with a wheelchair, and with more roof to extend into."),
    (("nurse", "nurses"), ("carer", "carers"),
     "A nurse is registered with the nursing council and does the clinical work - medicines, wounds, "
     "observations - in a hospital, surgery or care home. A carer helps with daily living: washing, "
     "dressing, meals and company, and needs no registration, whether it is a paid care worker or a "
     "relative doing it unpaid. So a health decision is the nurse's, and the help through the day is "
     "the carer's."),
    (("boiler", "boilers"), ("furnace", "furnaces"),
     "A boiler heats water and sends it round the radiators and the taps. A furnace heats air and "
     "blows it through ducts, which is the usual American heating; an old British back boiler is a "
     "boiler behind a fire. So a boiler has a flow temperature that matters and a furnace has a fan - "
     "the same job done through a different pipe."),
    (("sprain", "sprains"), ("break", "breaks", "fracture", "fractures"),
     "A sprain is a stretched or torn ligament at a joint, and a break is bone, which hurts over the "
     "bone itself and swells. You cannot tell them apart by how much it hurts, so the test is what "
     "you can do: if you cannot put weight on it, it is bent oddly, or you cannot use the limb, get "
     "it looked at the same day and let them X-ray it."),
    (("pond", "ponds"), ("pool", "pools", "swimming pool", "swimming pools"),
     "A pond is a small still body of water, in a garden or a field, with plants, mud and wildlife, "
     "and nothing keeps it clean but the plants and the balance. A pool is built and filtered for "
     "swimming, so it needs a pump, chemicals and a cover. So a pond wants the shallow edge and the "
     "frogs, and a pool wants the filter."),
    (("rabbit", "rabbits"), ("guinea pig", "guinea pigs", "cavy", "cavies"),
     "A guinea pig is the smaller, rounder one, with no tail and short legs, and it cannot make its "
     "own vitamin C, so it needs it in the food or in a supplement. A rabbit is bigger, with long "
     "ears and back legs, and it needs a run it can stand up in and dig. Guinea pigs want company of "
     "their own kind; a rabbit is strong enough to hurt one by accident, so a pair of rabbits or a "
     "pair of guinea pigs, not one of each."),
    (("fine", "fines"), ("penalty", "penalties"),
     "A fine is money a court or a council orders you to pay for breaking a rule. A penalty is the "
     "wider word: it is any punishment or extra charge - a penalty fare on the train, a penalty "
     "charge notice on the car, a late-payment penalty on a bill. So every fine is a penalty, and "
     "most penalties are not fines."),
)

# The ask, in the shapes people write it. "Is a boil the same as a cyst" and "are a flat and an
# apartment the same thing" are the commonest way to ask this, and they met the search hedge on
# main, so "the same" and "identical" are asks here. A bare "or" is the weakest of them: it is only
# a question when the line is short ("sprain or strain", "annuals or perennials"), because most long
# lines with two nouns and an "or" are a choice - "shall i have jam or marmalade on my toast" - and
# a choice belongs to the entry that picks one.
# "diff" is how the word is typed on a phone: "whats the diff between jam and marmalade" was the
# search hedge while "whats the difference between jam and marmalade" answered, on the same table,
# and it is not one pair - "whats the diff between lager and ale" and "whats the diff between a
# muffin and a cupcake" were hedges too. The word is short for the same ask, so it belongs with the
# ask and not in any one row.
DIFFERENCE_ASKS = ("difference", "differences", "different", "diff", "whats the difference",
                   "what is the difference", "versus", "vs", "distinguish",
                   # "compare a sprain and a strain" and "how does X compare with Y" ask the same
                   # question as "what is the difference between X and Y", and the table holds the
                   # pair either way. Only a line that names both at once reaches a row.
                   "compare", "compares", "comparing", "compared", "contrast", "contrasting",
                   "which is which", "what separates",
                   "same as", "the same", "same thing", "identical", "interchangeable",
                   "no difference", "one and the same", "or", "and",
                   # the comparison put as a question about one of the two: "is a sprain worse
                   # than a break" reaches the row only if the comparing words are a word of the
                   # entry as well as a strong ask, since the pair alone is under the score.
                   "worse than", "better than", "healthier than", "safer than", "harder than",
                   "easier than")

# The shapes that are a question however long the line is. Everything else in the asks above has to
# earn it by being short, or by asking which.
DIFFERENCE_STRONG_ASKS = ("difference", "differences", "different", "diff", "versus", "vs",
                          "distinguish",
                          "compare", "compares", "comparing", "compared", "contrast",
                          "contrasting", "which is which", "what separates", "same as", "the same", "same thing",
                          "identical", "interchangeable", "no difference", "one and the same",
                          # "is a sprain worse than a break" is the same question as the pair, and
                          # the words that compare the two are the ask whichever way round it is
                          # put. Both names still have to be in the line, so this cannot pull in a
                          # line about one thing being better than another.
                          "worse than", "better than", "healthier than", "safer than",
                          "stronger than", "harder than", "easier than")

# A name here puts a line in front of the table, whether or not the table holds that pair, and a
# line it claims and then passes goes on to the card that owns it. "flu" is the one name that has
# to sit this out: the flu-and-covid row needs the word, but "whats the difference between a cold
# and flu" belongs to the cold card, and that pair is deliberately not in the table.
DIFFERENCE_NAMES = tuple(sorted({name for left, right, _reply in DIFFERENCES
                                 for name in left + right
                                 if name not in DIFFERENCE_CLAIM_SKIP}))

# A short line with two names in it is a question even with only "or" or "and" between them
# ("sprain or strain", "and a rabbit and a guinea pig"). Count the words that carry meaning, so the
# articles and the fillers at the front of a follow-up do not make a short question look long; and
# keep a line that the person owns - "i have a rabbit and a guinea pig" - out of it, because that
# is a statement about their pets and not a question about the difference.
DIFFERENCE_FILLER = frozenset("""a an the so and or what whats about how do does did is are was
                              it them they of on in to for at as that this""".split())
DIFFERENCE_MINE = re.compile(r"(?<![a-z])(i|im|ive|me|my|we|our|us)(?![a-z])")


def _names_in(text, names):
    return any(re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", text) for name in names)


def _is_a_difference_ask(text, raw, left, right):
    """Is this line a question about the pair, or just a line with both names in it?"""
    if any(shape in text for shape in DIFFERENCE_STRONG_ASKS):
        return True
    if "which" in text or "?" in raw:
        return True
    if DIFFERENCE_MINE.search(text) and "or" not in raw:
        return False
    words = [w for w in re.findall(r"[a-z']+", raw) if w not in DIFFERENCE_FILLER]
    if "or" in raw:
        return len(words) <= 5
    # A bare "and" is the weakest shape of all: it is only the question when the line is nothing
    # but the two names, so "a rabbit and a guinea pig" asks and "cucumber and courgette salad"
    # is a dish.
    names = {w for name in left + right for w in name.split()}
    return set(words) <= names


def _difference(memory, understood):
    text = (understood.get("clean") or understood.get("text") or "").lower()
    raw = (understood.get("text") or "").lower()
    for left, right, reply in DIFFERENCES:
        if not (_names_in(text, left) and _names_in(text, right)):
            continue
        if not _is_a_difference_ask(text, raw, left, right):
            continue
        return reply
    return None


ENTRIES.extend(_name("explain-" + ident + "-name", words, reply,
                     avoid=SPELLED_OUT_STAND_DOWN.get(ident, ()))
               for ident, words, reply in SPELLED_OUT)

# One entry for the whole table: the pair in the line picks the row, and an unknown pair passes so
# that an explanation or a choice entry that already answers it keeps the line.
# The coil asked as a job rather than as a definition: "how do i get the coil fitted" carries
# neither "what is" nor "mean", so the spelled-out row above never sees it and the line was a
# search hedge while the answer sat in the card. The subject is the phrase, never the bare word,
# and the second half is what the line does with it: getting it, how long it lasts, whether it
# hurts, what it costs, having it out.
# The coil is asked as five different questions - will it hurt, how long does it last, is it
# free, what happens to my periods, how do I get it out - and one card that opens on where to
# get it fitted answers none of them first. The card below reads which one the person asked and
# leads with it, and each answer still says where to go, so a line naming two of them still gets
# a whole answer.
_COIL_HURT = ("hurt", "hurts", "hurting", "pain", "pains", "painful", "sore", "ache", "aching",
              "uncomfortable", "agony", "worst", "dreading", "nervous", "scared")
_COIL_LIFE = ("how long", "last", "lasts", "lasting", "years", "long does")
_COIL_FREE = ("free", "cost", "costs", "pay", "paid", "price", "expensive", "charge", "nhs")
_COIL_BLEED = ("period", "periods", "bleed", "bleeds", "bleeding", "spotting", "spot")
_COIL_OUT = ("removed", "remove", "removal", "taken out", "take it out", "take out", "get it out",
             "swap", "change it", "change over", "coming out")
_COIL_YOUNG = ("16", "15", "14", "13", "17", "18", "parents", "parent", "mum", "mother", "dad",
               "consent", "age", "old enough", "being told")
_COIL_BABY = ("baby", "babies", "birth", "postnatal", "caesarean", "c section", "just had",
              "having a baby", "breastfeeding", "feeding")
# "how long does the coil take to work" is not "how long does it last": one asks when it starts,
# the other how many years it covers, and the years card answered the first one with the second
# answer. The onset words have their own branch.
_COIL_SOON = ("take to work", "takes to work", "took to work", "until it works", "before it works",
              "until the coil works", "for the coil to work", "coil to work", "coil works",
              "does the coil work", "does it work", "work straight",
              "start working", "starts working", "start to work", "starts to work",
              "works straight", "work straight", "works right away", "how quickly", "how soon",
              "when does it work", "when does the coil work", "kick in", "kicks in")
# "how effective is the coil" and "is the coil as good as the pill" are the other half of that:
# how well it works over a year, not when it starts.
_COIL_EFFECT = ("effective", "effectiveness", "as good as", "how good", "reliable", "protects",
                "protection", "protect", "fail", "fails", "failure", "chance of getting pregnant",
                "how well")
# "is the coil safe" was a fence line on the review probe, and the card must not answer it with
# where to book: safe is its own question, and it is the one a nervous person asks first.
_COIL_SAFE = ("safe", "safely", "risky", "risk", "risks", "dangerous", "side effect",
              "side effects", "complications", "harmful", "damage", "problems with")
# "i had the coil fitted and i feel sick" reached the fitting card, because "fitted" is in the ask,
# and the one thing the person said - they feel ill - was answered with where to book. What
# happens in the days after a fitting is its own question.
_COIL_AFTER = ("after the coil", "after having the coil", "after the fitting", "after fitting",
               "since the coil", "since having it", "since i had it", "had it fitted",
               "got it fitted", "had one fitted", "fitted and", "felt rough", "feel rough",
               "feel sick", "feeling sick", "felt sick", "being sick", "in the days after",
               "day after", "days after", "weeks after", "cramping after", "pain after")
# "can i get pregnant with a coil" and "i think my coil has come out" both reached the fitting
# card, because "get" is in the ask. They are the two things a person asks when they are worried,
# so they are answered first of all, before fit or pain or price.
_COIL_PREGNANT = ("pregnant", "pregnancy", "a baby on the way", "missed a period",
                  "missed period", "late period", "test positive", "positive test")
_COIL_LOST = ("come out", "came out", "comes out", "fallen out", "fell out", "has come out",
              "has fallen out", "cannot feel the strings", "can't feel the strings",
              "cant feel the strings", "no strings", "cant find the strings",
              "can't find the strings", "lost the strings", "moved", "out of place",
              "came away", "come away")
# "get it out" and "removed" are the booking, not the accident: a line that says both is a
# removal question and keeps the removal answer.
_COIL_REMOVAL_ASK = ("take it out", "take out", "get it out", "get out", "removed", "remove",
                     "removal", "swap", "change it", "change over")


def _coil_line(understood):
    """The words of this line as one string, so a phrase like "how long" can be looked for."""
    if not isinstance(understood, dict):
        return ""
    parts = [understood.get("text"), understood.get("plain"), understood.get("clean")]
    return " ".join(str(part or "") for part in parts).lower()


def _the_coil(memory, understood):
    """Which coil question this is, answered first, with the rest of the card behind it."""
    said = _coil_line(understood)
    # A worried line comes before everything: "can i get pregnant with a coil" carries "get", so
    # the fitting default answered it with where to book, and the one thing the person asked went
    # unanswered. Same for a coil that has moved.
    if any(word in said for word in _COIL_SAFE):
        return ("Yes - it is one of the safest things you can use, and it suits most people, "
                "including people who cannot take the pill and people who are breastfeeding. It "
                "does not protect against sexually transmitted infections, so use condoms as well "
                "if that matters to you. The risks are small and known: a very rare injury to the "
                "womb at fitting (about one or two in a thousand), an infection in the first few "
                "weeks, and the chance it comes out by itself, most often in the first months. "
                "The hormonal one can also bring headaches, breast tenderness, acne or low mood "
                "for the first few months, and those usually settle; the copper one mainly makes "
                "periods heavier. Ring the clinic if you get a fever, bad pain or smelly discharge "
                "after fitting.")
    if any(word in said for word in _COIL_EFFECT):
        return ("Over 99 in 100 for both kinds: fewer than one in a hundred people get pregnant in "
                "a year with a coil in, which is better than the pill in everyday use because "
                "there is nothing to forget. The copper one works from the moment it is fitted and "
                "for its whole life, the hormonal one for three to eight years depending on which, "
                "and neither is affected by being sick or by antibiotics the way the pill is. If "
                "you are worried it has moved, that is the one thing that drops the protection.")
    if any(word in said for word in _COIL_PREGNANT):
        return ("Not likely, but not impossible: fewer than one in a hundred people get pregnant "
                "in a year with a coil in, which makes it one of the most reliable methods there "
                "is - more so than the pill, because there is nothing to forget. If you think you "
                "might be pregnant with one in place, take a test and ring the clinic that fitted "
                "it the same day rather than pulling it out yourself: they will check it is still "
                "where it should be, and a coil can stay in through a pregnancy with a check. Use "
                "condoms until they have seen you.")
    if (any(word in said for word in _COIL_LOST)
            and not any(word in said for word in _COIL_REMOVAL_ASK)):
        return ("Treat it as no protection: use condoms, or the morning after pill if you have had "
                "sex since it moved, and get seen at a sexual health clinic or your GP within a "
                "few days - they check the strings and fit a new one if it has gone, which is "
                "quick and free. Do not try to put it back or pull it out yourself. A coil can come "
                "out on its own, most often in the first few months or during a heavy period, and "
                "it is more likely if you have not had a baby.")
    if any(word in said for word in _COIL_SOON):
        return ("A copper coil protects from the moment it is fitted. A hormonal one does too if "
                "it goes in during the first seven days of your period; fitted at another point in "
                "the cycle, use condoms for the first seven days. Neither needs a wait after that, "
                "and neither is affected by being sick, by antibiotics or by a missed pill - the "
                "protection does not lapse between coils either, because a new one can go in the "
                "same appointment as the old comes out.")
    if any(word in said for word in _COIL_OUT):
        return ("A nurse takes it out in a few minutes, at any time you want - you do not have to "
                "wait for the years to run out, and any sexual health clinic or the place that "
                "fitted it will do it. It is free on the NHS, and fertility comes back straight "
                "away, so use another method from about a week before if you do not want to be "
                "pregnant. If it has moved, or you cannot feel the strings, say so when you ring.")
    if any(word in said for word in _COIL_YOUNG):
        return ("Yes, at any age: it is free on the NHS, and under 16 you can have one without "
                "your parents being told, as long as the doctor or nurse thinks you understand "
                "what you are agreeing to. A young people's clinic is usually the easiest place to "
                "ask, and they will talk you through the copper and hormonal ones before you "
                "decide. Nothing goes on a record your parents can see.")
    if any(word in said for word in _COIL_BABY):
        return ("Yes, and often before you leave hospital: a coil can go in straight after a "
                "vaginal birth or at a caesarean, and otherwise from six weeks afterwards. It does "
                "not affect your milk, and the hormonal one is fine while you are feeding. It is "
                "free, and the fitting is the same few minutes at a clinic or your GP surgery.")
    if any(word in said for word in _COIL_AFTER):
        return ("A day or two of period-like cramping, some spotting and feeling a bit rough is "
                "normal in the first days after a coil goes in, and it settles on its own: "
                "ibuprofen, a hot water bottle and an early night do most of it. Ring the clinic "
                "the same day if you have a fever, pain that gets worse rather than better, smelly "
                "discharge or heavy bleeding with clots - that is usually an infection, and it "
                "clears up quickly with antibiotics. Feeling faint at the fitting itself is common "
                "too, so it is worth having someone with you.")
    if any(word in said for word in _COIL_HURT):
        return ("It hurts, but briefly: fitting is a sharp period-like cramp for about a minute "
                "while it goes in, then a dull ache for a day or two and spotting for a few "
                "weeks. Take ibuprofen an hour before, eat something first, and arrange a lift "
                "home. Most people say it was easier than they feared, and the hormonal ones are "
                "usually gentler to fit than the copper coil - so say at the clinic if you are "
                "dreading it and ask about a local anaesthetic.")
    if any(word in said for word in _COIL_FREE):
        return ("Free on the NHS, at any age and whatever your income - you never pay for "
                "contraception, and that includes the coil and the fitting. It is done at a "
                "sexual health clinic, a young people's clinic or your GP surgery, and under 16 "
                "you can have one without your parents being told.")
    if any(word in said for word in _COIL_BLEED):
        return ("The hormonal coil usually makes periods much lighter, and about one in five "
                "people stop having them altogether, which is not harmful. The copper one can "
                "make them heavier and more painful for the first three months. If you are "
                "bleeding between periods or after sex once it has settled in, get it checked.")
    if any(word in said for word in _COIL_LIFE):
        return ("Five years for most copper coils, and three to eight for the hormonal ones - "
                "Mirena eight, Kyleena five, Jaydess three. Those are maximums, not a promise, so "
                "ask at the clinic which one they are fitting, and you can have it out sooner at "
                "any time you want.")
    return ("Get it fitted at a sexual health clinic, a young people's clinic or your GP "
            "surgery: you book an appointment and the fitting takes about five minutes with a "
            "nurse or doctor. It is free on the NHS at any age - under 16 you can still have one "
            "without your parents being told, as long as the doctor thinks you understand what "
            "you are agreeing to. Expect period-like cramping for a day or two and spotting for a "
            "few weeks, so take ibuprofen an hour before, and a copper coil can make periods "
            "heavier for the first few months while the hormonal ones make them lighter or stop "
            "them. It lasts five years for the copper one and three to eight for the hormonal "
            "ones, and a nurse can take it out whenever you want.")


ENTRIES.append(entry("the-coil-how-to",
                     (COIL_ASKS,
                      ("fitted", "fit", "getting", "get", "want", "thinking about",
                       "thinking of", "considering", "should i get", "inserted", "insertion",
                       "put in", "book", "booking", "appointment", "clinic", "gp", "nurse",
                       "how long", "long", "last", "lasts", "hurt", "hurts", "painful",
                       "pain", "cost", "costs", "free", "pay", "come out", "taken out",
                       "removed", "remove", "swap", "change", "periods", "bleeding",
                       # the worried questions and the two "does it work" questions were the
                       # ones a card about booking answered with booking: the ask has to carry
                       # their words or the row never sees them at all
                       "work", "works", "working", "quickly", "soon", "effective",
                       "effectiveness", "protect", "protects", "protection", "pregnant",
                       "pregnancy", "came out", "come out", "come", "came", "fallen", "fell",
                       "fell out", "fallen out", "strings", "moved", "good as",
                       "as good as", "reliable", "safe", "risks", "risk", "dangerous",
                       "side effects", "complications", "after", "days", "week", "sick",
                       "fitted and", "since")),
                     _the_coil,
                     bias=2,
                     avoid=NOT_A_COIL + NOT_A_COIL_QUESTION),
                     )

ENTRIES.append(entry("difference-between",
                     (DIFFERENCE_ASKS, DIFFERENCE_NAMES),
                     _difference,
                     ask=DIFFERENCE_NAMES,
                     bias=1))


# --- which of the two, when the answer is a judgement -------------------------------
# "Which is better, X or Y" where the two are not words to be told apart but two things to choose
# between. The `difference-between` table above answers what the words mean; these answer what to
# do, so each row carries the ask shape it answers as well as the pair, and a line that names the
# pair but asks something else (how to fit one, what it costs to buy, whether it works at all)
# passes to the row that knows.
#
# Every row is one question people really ask, with the numbers that decide it. A pair whose
# choice depends on things the line does not say does not belong here: it needs the person's
# situation, not a table.
_MOVE_OR_STAY = (
    "Move only if the extra room fixes something you hit every day and you will still be there "
    "in five years: the move itself costs £4,000 to £8,000 on a typical home (estate agent, "
    "legal, removals, and stamp duty above the threshold) and the bigger place costs more every "
    "month for good. If the want is one room for guests or a desk, price the fix in the home you "
    "have first - a sofa bed is £500, a garden office is £3,000 - and move when the thing you "
    "lack is space you will use every day rather than sometimes.")

# A job against a trade is the same choice as the ones below, and it was the one that had no row:
# "hire a builder or do it myself" was answered with the package-holiday card, because the trade
# row's ask never recognised "hire" and the travel row keys "do it myself" for a holiday booked
# separately. The split is not about skill, it is about what has to be certified and what a
# mistake costs, so the answer gives the line between them and the price of crossing it.
_DIY_OR_A_TRADE = (
    "Do it yourself on the cosmetic jobs - painting, tiling a splashback, hanging a door, laying a "
    "floor - and pay a trade for anything on gas, the consumer unit or a new circuit, anything "
    "structural (a wall out, a lintel, a new opening), and full bathroom or kitchen plumbing, "
    "because those need a certificate, building control or both, and your buildings insurance "
    "will ask who did the work. Most trades charge £150 to £250 a day, so get three written "
    "quotes that name a price, a start date and what is included. The test is what a mistake "
    "costs: a repaint is a weekend, a leak through a ceiling or an unsigned gas job is not.")

# the trades in the words people type, and the trade bodies that gate the three that need one
_TRADES = ("builder", "builders", "plumber", "plumbers", "electrician", "electricians",
           "decorator", "decorators", "painter", "painter and decorator", "tiler", "tiler",
           "plasterer", "joiner", "carpenter", "roofer", "gas engineer", "heating engineer",
           "handyman", "fitter", "someone in", "someone to do it", "a professional", "a pro",
           "trade", "tradesman",
           # the job is as good as the trade: "do it myself or pay someone to rewire the house"
           # names no plumber or electrician, and the line had no row to reach
           "rewire", "rewiring", "rewired", "electrics", "plumbing", "gas work", "loft",
           "loft conversion", "extension", "roof", "roofing", "plastering", "tiling",
           "the work", "the job")
_DO_IT_MYSELF = ("do it myself", "do it ourselves", "diy", "myself", "ourselves",
                 "get someone in", "pay someone", "get a professional", "get a trade",
                 "get a tradesman", "do the work myself")

CHOOSING = (
    ( _TRADES, _DO_IT_MYSELF,
     ("hire", "hiring", "get", "getting", "should i", "should we", "worth it", "or do it",
      "or get", "or pay", "cheaper", "or a trade", "or someone", "do i need"),
     _DIY_OR_A_TRADE),
    # Moving is a one-off bill plus a new set of bills; staying is the annoyance that made them
    # ask. The line almost never says what the extra room is for, so the answer is the test.
    (("bigger flat", "bigger place", "bigger house", "bigger home", "move house", "moving house",
      "move to a bigger", "move somewhere bigger", "upsize", "more space", "extra bedroom",
      "second bedroom", "move flat", "moving flat", "move home"),
     ("stay", "staying", "stay put", "stay where we are", "stay where i am", "not move",
      "dont move", "don't move", "put up with it", "make do"),
     ("worth", "should i", "should we", "or stay", "or should", "better", "decide",
      "or move", "move or"),
     _MOVE_OR_STAY),
    # The same question with one side only: "is it worth moving to a bigger house" names no
    # alternative, and the answer to it is the same sum. It was reaching the paint-the-room
    # answer, which is advice for making a small room work.
    (("bigger flat", "bigger place", "bigger house", "bigger home", "move house", "moving house",
      "move to a bigger", "move somewhere bigger", "upsize", "more space", "extra bedroom",
      "second bedroom", "move flat", "moving flat", "move home"),
     (),
     ("worth", "should i", "should we", "is it worth", "worth moving", "worth it"),
     _MOVE_OR_STAY),
    # The running cost is the question, and the honest answer needs the efficiency number rather
    # than a bill comparison: a heat pump is dearer to fit and cheaper to run.
    (("heat pump", "heat pumps"),
     ("boiler", "gas boiler", "new boiler", "gas", "gas heating"),
     ("cheaper", "cheaper to run", "cost to run", "running cost", "running costs", "bills",
      "bill", "expensive", "save money", "worth the money"),
     "Cheaper to run, dearer to fit: a heat pump moves three to four units of heat per unit of "
     "electricity, so at current prices it costs less per unit of heat than a gas boiler, and the "
     "gap widens as gas standing charges rise. Fitting one is £8,000 to £14,000 before the "
     "£7,500 grant, and it usually needs bigger radiators, good insulation and a hot water "
     "cylinder, so the honest sum is over ten years, not one winter."),
    # A dryer is bought as one of three kinds, and "which is better a heat pump or a condenser
    # dryer", "is a heat pump dryer better than a condenser" and "heat pump or condenser tumble
    # dryer" wanted this table and found no row for the pair: the first two were told about the
    # drain pump behind the kick plate. The running cost and the vent are what decide it.
    (("heat pump dryer", "heat pump dryers", "heat pump tumble dryer", "heat pump drier",
      "heat pump", "vented dryer", "vented tumble dryer", "vented"),
     ("condenser dryer", "condenser dryers", "condenser tumble dryer", "condenser",
      "heat pump one", "vented one"),
     ("better", "best", "which", "worth", "should i", "or", "rather", "worse", "cheaper",
      "cheap", "expensive", "cost", "run", "running", "energy", "efficient", "efficiency"),
     "A heat pump tumble dryer, if you dry two or more loads a week: it uses about half the "
     "electricity of a vented one, roughly 25p a cycle against 60p, so the 150 to 200 pounds more "
     "up front pays back in about two years - and a load takes an hour longer, with the fluff "
     "filter and condenser cleared often. A condenser tumble dryer is the one to have if you "
     "cannot put a vent through a wall, and a vented dryer is the cheapest to buy and the fastest, "
     "but it needs a hole to the outside.",
     # "heat pump" and "condenser" are also a house's, and a line about the house takes the bare
     # names: "heat pump or condenser for the house" is a heating question and got the dryer's
     # answer (@gray-scarf, #10269). A laundry word has to be in the line, the way `_choice_value`
     # already asks for one, and a dryer-less phrasing loses nothing - main answers it wrongly too.
     ("dryer", "dryers", "drier", "driers", "tumble", "tumble dryer", "laundry")),
    # One kind named and a cost asked: "is a vented dryer cheaper to run" is a comparison with a
    # kind it does not name, and the tariff card answered it (@sleek-shark, #10269). The order of
    # the three kinds is the answer, so the row is the comparison with one side said out loud.
    (("vented dryer", "vented tumble dryer", "vented", "heat pump dryer", "heat pump tumble dryer",
      "heat pump", "condenser dryer", "condenser tumble dryer", "condenser"),
     (),
     ("cheaper", "cheaper to run", "cost to run", "costs to run", "running cost", "running costs",
      "expensive to run", "energy", "efficient", "efficiency", "worth it", "worth"),
     "A heat pump tumble dryer is the cheapest to run: about 25p a cycle against 60p for a vented "
     "one, so roughly half, and the 150 to 200 pounds more it costs to buy is paid back in about "
     "two years if you dry a few loads a week. A condenser sits between the two and is the one to "
     "have when there is no wall to vent through; a vented dryer is the cheapest to buy and the "
     "fastest, and it is only cheap to run if the heat it throws out is heating the house anyway.",
     ("dryer", "dryers", "drier", "driers", "tumble", "tumble dryer", "laundry")),
    # Renting a car is for the days you need one, so the answer is a number of days.
    (("rent a car", "renting a car", "hire a car", "hiring a car", "car hire", "car club",
      "rent a van"),
     ("buy a car", "buying a car", "own a car", "owning a car", "buy", "own", "get a car"),
     ("should i", "better", "cheaper", "worth", "or", "which"),
     "Own if you drive more than about once a week: hiring is £30 to £50 a day, so forty days a "
     "year is £1,400 and a small used car all in - insurance, tax, servicing, MOT, tyres - costs "
     "£2,500 to £3,500 a year before fuel. Rent for the odd weekend and the holiday, and use a car "
     "club for the two-hour jobs, which is what makes renting cheaper under about twenty days a "
     "year."),
    # Depreciation is the whole answer, and it is a number rather than a taste.
    (("new", "brand new", "new one"),
     ("second hand", "second-hand", "used", "nearly new", "refurbished", "ex display"),
     ("should i", "worth", "better", "or", "buy", "cheaper", "which"),
     "Second hand, for anything that is not safety-critical: a new car loses 15 to 20% in the "
     "first year and 40% by three, a new bike or laptop a third in a year, and a four-year-old "
     "version of either does the same job for half the money. Buy new where the warranty is the "
     "point (a washing machine, a boiler, a helmet, a car seat) and second hand everywhere else, "
     "checking it works before you pay."),
    # A commute is a yearly bill, and the car is far bigger than people expect.
    (("bus", "the bus", "by bus", "coach", "tram", "metro"),
     ("drive", "driving", "car", "by car"),
     ("to work", "commute", "for work", "or drive", "better", "cheaper", "should i", "or"),
     "The bus, unless your journey has no direct route: a yearly bus pass is £400 to £900 in most "
     "cities where running a car to work is £3,000 to £5,000 a year once insurance, tax, servicing "
     "and parking are counted, before you pay for the car. Drive only when the trip is over an "
     "hour each way or carries tools, and work out the real cost of the commute on a single day "
     "before deciding."),
    # The wash label answers this one, so the answer is what the label says and why.
    (("hot wash", "hot cycle", "warm wash", "hot", "hotter"),
     ("cold wash", "cold cycle", "cold water wash", "30 degree", "30 degrees", "cold"),
     ("better", "should i", "or", "towels", "sheets", "clothes", "delicates", "colours", "whites",
      "wash"),
     "Thirty degrees for everything ordinary, and sixty for towels, bedding and anything with "
     "bodily fluid: modern powders work at 30, and a cold wash only saves about 20p a load over "
     "30 degrees. What actually keeps clothes looking new is turning them inside out, washing "
     "less often than you think, and drying flat rather than hot."),
    # Frozen is picked and frozen in hours; fresh travels and then sits in a fridge.
    (("frozen veg", "frozen vegetables", "frozen fruit", "frozen peas", "frozen veg"),
     ("fresh veg", "fresh vegetables", "fresh fruit", "fresh veg", "fresh"),
     ("better", "healthier", "should i", "or", "nutrition", "vitamins", "buy"),
     "Frozen, for the same nutrition and less waste: vegetables are frozen within hours of "
     "picking while fresh ones lose vitamin C in the days they spend in transit and in your "
     "fridge, and frozen costs about half and keeps for months. Buy fresh for what you eat raw "
     "within a couple of days and for potatoes; either counts towards your five a day."),
    # Two rates, compared, with the emergency fund first.
    (("overpay", "overpaying", "pay off the mortgage", "paying off the mortgage",
      "pay off my mortgage", "overpay the mortgage"),
     ("save", "saving", "savings", "save it", "put it in savings"),
     ("better", "should i", "or", "worth", "instead"),
     "Overpay if the mortgage rate is higher than what the savings pay after tax; save if the "
     "other way round. Keep three to six months of bills in an easy-access account before either, "
     "because a mortgage overpayment cannot be taken back, and check the early repayment charge: "
     "most fixes allow 10% of the balance a year."),
    # Leasehold is the deciding fact, and people forget it.
    (("flat", "flats", "apartment"),
     ("house", "houses", "a house", "terraced house"),
     ("should i", "better", "worth", "buy", "or", "which"),
     "A house if you can afford one, because a flat means a lease, a service charge (£1,500 to "
     "£3,000 a year), ground rent and a landlord for the building; a lease under 80 years is hard "
     "to mortgage. A flat makes sense for a first home you will sell within five years or in a "
     "city centre where houses cost twice as much, but read the lease length and the service "
     "charge accounts before you offer."),
    # The two are priced differently, and a day rate is the sum that decides it.
    (("money", "pay rise", "more money", "the money", "higher salary"),
     ("time off", "the time off", "extra holiday", "more holiday", "fewer hours", "four day week"),
     ("take", "should i", "or", "better", "worth", "instead"),
     "Work out the leave in money: if a pay rise is £2,000 and five days of leave would cost "
     "£1,200 of your net pay, the time is the better buy, and leave cannot be taxed. Take the "
     "money if you are saving for something fixed or under 30 years from retirement; take the "
     "time if the job already pays enough and the weeks are what you are short of."),
    # Caffeine is the only real difference, and the number is small.
    (("decaf", "decaffeinated", "decaf coffee"),
     ("normal", "normal coffee", "regular coffee", "caffeine", "full caffeine", "proper coffee"),
     ("should i", "better", "or", "healthier", "worth"),
     "Ordinary coffee unless caffeine is costing you sleep: a mug has about 95mg against 2 to 15mg "
     "in decaf, and the antioxidants are much the same. Keep caffeine before noon if you are "
     "sensitive, stay under about 400mg a day (four mugs), and drink decaf in the afternoon rather "
     "than giving up the habit."),
    # What each one is actually for.
    (("yoga",),
     ("pilates",),
     ("should i", "better", "or", "which", "worth"),
     "Pilates for a weak or aching back, yoga for stiffness, balance and stress: pilates is "
     "slower, more controlled and focused on the deep core muscles, while yoga adds standing "
     "poses, breathing and a bit of philosophy. If you sit all day, start with pilates twice a "
     "week; if you want one class that also calms you down, take the yoga."),
    # The language, not the method: what you will use beats what looks tidy.
    (("spanish",),
     ("french",),
     ("should i", "better", "or", "which", "learn", "worth"),
     "Whichever you have a person to speak it with, and Spanish if that is a close call: about "
     "490 million native speakers against 80 million for French, and a more forgiving "
     "pronunciation. French is worth choosing for school help, for France and for work in "
     "Brussels or west Africa. Fifteen minutes a day with someone to talk to beats a year of an "
     "app either way."),
    # The single-side version: is the work worth it?
    (("doer upper", "fixer upper", "fixer-upper", "renovation project", "needs modernising",
      "needs doing up", "a project house", "house that needs work"),
     (),
     ("worth", "should i", "buy", "or", "buying", "worth it", "worth buying"),
     "Only if the discount is bigger than the work: price the three big ones first - roof, "
     "electrics, windows - because those are £5,000 to £15,000 each before anything you can see. "
     "Then add a third again to whatever a builder quotes and double the time, and buy only if the "
     "finished house would still be worth more than you have spent. If you cannot live through the "
     "mess or cannot afford to rent elsewhere during the worst of it, buy the finished one."),
    # Door to door is what people mean by the question, and check-in is the part they forget.
    (("fly", "flying", "plane", "flight", "flights"),
     ("train", "rail", "by train"),
     ("better", "faster", "cheaper", "should i", "worth", "or take", "fly or train",
      "take the train"),
     "The train wins on any trip that is under about four and a half hours by rail: add two hours "
     "at each airport for the flight once you count the transfer, security and baggage, and the "
     "plane only pulls ahead on long routes. London to Edinburgh is four hours twenty by train "
     "against an hour and a quarter in the air that becomes five hours door to door, so the train "
     "is the answer; booked six to twelve weeks ahead it usually costs less too."),
)

def _choosing_rows():
    """Each row as (left, right, asks, reply, needs), with `needs` empty where the row has none.

    A word in `needs` is a fifth element on the row: the line has to carry one of them for the row
    to answer. Some names are shared between subjects - "heat pump" and "condenser" are a dryer's
    kinds and a house's - and the row cannot tell them apart on its own.
    """
    for row in CHOOSING:
        if len(row) == 5:
            yield row
        else:
            yield row + ((),)


CHOOSING_NAMES = tuple(sorted({name for left, right, _asks, _reply, _needs in _choosing_rows()
                               for name in left + right}))
CHOOSING_ASKS = tuple(sorted({ask for _l, _r, asks, _rep, _needs in _choosing_rows()
                              for ask in asks}))


def _choosing(memory, understood):
    text = (understood.get("clean") or understood.get("text") or "").lower()
    for left, right, asks, reply, needs in _choosing_rows():
        if not _names_in(text, left):
            continue
        # an empty right side is a row that needs no second thing named: the pair is the thing and
        # the choice is "is it worth doing at all"
        if right and not _names_in(text, right):
            continue
        if not _names_in(text, asks):
            continue
        if needs and not _names_in(text, needs):
            continue
        return reply
    return None


# The pair has to be named and the ask has to be the choice: a line that says "my boiler is
# making a noise" names one of these words and asks nothing about choosing.
def _one_of_them_is_actually_named(understood):
    """The entry answers only on a line that names a pair its own rows cover.

    The key is the union of every row's two sides, so a single word from it - "boiler" - is enough
    to score, and it scored above the costs row: "how much does a new boiler cost" was handed to
    this entry, which then had no row to read and could not answer, and the price line lost its
    card. A name is not a pair until the row that owns the pair has read the line.
    """
    # ...and an ask for the order of the steps is not a choice between two things:
    # "moving house what should i do first" is the moving plan's line, and the "should i" in it
    # was read as the decision row's ask (see lookup.the_ask_is_the_order_of_steps).
    return (_choosing(None, understood) is not None
            and not_the_ask_about_the_order(understood))


ENTRIES.append(entry("choosing-between",
                     (CHOOSING_NAMES, CHOOSING_ASKS),
                     _choosing,
                     ask=CHOOSING_NAMES,
                     guard=_one_of_them_is_actually_named,
                     # a line that asks what to wear names its weather or its occasion, and both
                     # are in the names above ("hot", "cold", "school"): "what should i wear when
                     # its hot" was a choice between two things the person never mentioned. The
                     # clothes rows answer that line, so this one stands down for it.
                     avoid=A_WHAT_TO_WEAR,
                     bias=1))


# --- the machinery of government ------------------------------------------------
#
# "how does parliament work" and "how does a bill become law" are school-level civics questions
# about a system, which is what this file is for, and main sent every one of them to a search
# hedge or to a card about something else: a bill that becomes law reached the money rows (a
# "bill" is also an invoice) and got Citizens Advice, and "how do laws get passed" reached the
# older person's bus pass. Each row is keyed on the words that make the thing that thing, and
# the second half carries the asking shapes, because the subject alone says nothing - "general
# election" appears in "who won the general election" too, and that is not this question.
_GOVERNMENT_ASK = ("how do", "how does", "how often", "how many", "what is", "what are",
                   "what does", "what do", "which", "why", "explain", "mean", "means",
                   "work", "works", "become", "becomes", "becoming", "made", "make", "pass",
                   "passes", "passed", "elected", "election", "elections", "held", "called",
                   "vote", "voting", "vote for", "system", "happen", "happens", "next",
                   "first past the post", "role", "job", "members", "member", "seats",
                   "difference between", "different from", "do", "does", "is", "are")

# A line about paying, complaining or booking is not a line about the constitution: "bill",
# "law", "court" and "cabinet" are everyday words, and the money, consumer, lifeadmin and DIY
# rows own their own lines. Every avoid word here is checked against the row's own questions in
# tests/test_how_the_country_is_run.py, because an avoid word that folds onto the subject
# ("lord" folds onto "lords") denies every line the row exists for.
_NOT_CIVICS = ("energy bill", "gas bill", "electric bill", "electricity bill", "water bill",
               "phone bill", "mobile bill", "broadband bill", "vet bill", "council tax",
               "bill came", "my bill", "the bill was", "bill is", "bill for", "pay my bill",
               "pay the bill", "split the bill", "restaurant bill",
               "solicitor", "divorce", "custody", "court date", "court case", "small claims",
               "employment tribunal", "eviction", "arrears", "police", "arrested", "caught",
               "fined", "parking ticket", "speeding",
               "my mp", "contact my mp", "write to my mp", "who is my mp", "find my mp",
               "register to vote", "voter id", "polling station", "postal vote", "proxy vote",
               # how to vote is a form and a date, which main already answers with the register
               # service; the system is a different question
               "how do i vote", "how to vote", "where do i vote", "how do you vote",
               # a name that shares a word with a row but asks something else: the lord mayor is
               # a city office, a bill of rights is a document, and a hung parliament or a
               # coalition is a result, not the machinery
               "lord mayor", "bill of rights", "hung parliament", "coalition",
               "mps paid", "mp salary", "mps earn", "how much do mps",
               "bathroom cabinet", "kitchen cabinet", "medicine cabinet", "filing cabinet",
               "cabinet door", "cabinet hinge")


# A guard, not an avoid word, for "the us" and for a party's own tally: a line that reaches
# nothing is read a second time with "we/us/our" turned into "i/me/my" (lookup._other_reading),
# which turns "in the us" into "in the me" and lets the row back in past its own avoid list.
# The guard sees the line as typed, so the words that say which country is meant hold.
_ANOTHER_COUNTRY = re.compile(
    r"\b(?:the\s+us|usa|u\.s\.|america|american|presidential|electoral\s+college|"
    r"congress|senate|canada|australia|new\s+zealand|ireland|france|germany)\b", re.I)
_A_PARTY_TALLY = re.compile(
    r"\b(?:conservative|tory|tories|labour|liberal\s+democrat|lib\s+dem|snp|green\s+party|"
    r"reform\s+party|dup|sinn\s+fein)\b", re.I)


def _only_this_country(understood):
    """True when the line is about how this country is run, not another one's elections."""
    text = (understood or {}).get("text") or (understood or {}).get("clean") or ""
    return not _ANOTHER_COUNTRY.search(str(text))


def _not_one_party(understood):
    """True when the line asks about parliament's members, not how many one party has."""
    text = (understood or {}).get("text") or (understood or {}).get("clean") or ""
    return not _A_PARTY_TALLY.search(str(text))


# The names the four newest rows are *about*. They sit in _NOT_CIVICS because they used to be
# stolen by the Lords, bill and election rows; the rows below own them now, so a row about one of
# them must not carry its own subject in its avoid list. Everything else the shared list holds
# still applies to them.
_OWN_SUBJECT = ("lord mayor", "bill of rights", "hung parliament", "coalition",
                "mps paid", "mp salary", "mps earn", "how much do mps")
_NOT_CIVICS_ELSE = tuple(w for w in _NOT_CIVICS if w not in _OWN_SUBJECT)


# The shapes every row in this block answers with. `asks=` is the key's second half and `ask=`
# is the test the line has to pass, and they are not the same list: "when" is a key word for the
# election row but was not in this test, which is how "when is the next general election" fell
# through to a reminder card.
_CIVICS_ASK = ("how", "what", "who", "why", "explain", "mean", "means",
               "how many", "difference", "work", "works")


def _civics_new(id, subject, reply, also=(), avoid=(), asks=None, guard=None):
    """_civics, for a row whose subject is one of the names the older rows stand down on."""
    return _civics(id, subject, reply, also=also, avoid=avoid, asks=asks, guard=guard,
                   blocked=_NOT_CIVICS_ELSE)


def _civics(id, subject, reply, also=(), avoid=(), asks=None, guard=None,
            blocked=_NOT_CIVICS, ask=None):
    """One row about how the country is run: the thing named, plus how it is asked about.

    `asks`: the shapes this row answers with, when the whole asking set is too wide. The row that
    tells parliament and government apart is the case: with every ask word in its second half it
    tied with the definition row on "what is the difference between parliament and government" and
    the earlier row won, so it is keyed on the difference phrases alone.
    """
    return entry(id, (subject, tuple(asks) if asks is not None else _GOVERNMENT_ASK) + tuple(also), reply,
                 ask=ask if ask is not None else _CIVICS_ASK,
                 avoid=blocked + tuple(avoid), guard=guard)


# "what is local government" was answered "Parliament is the Commons, the Lords and the monarch",
# and "how does the council work" was a search hedge: the councils are a different set of bodies
# doing different jobs, so they get their own row rather than a fence on parliament's.
ENTRIES.append(_civics(
    "local-government",
    ("local government", "local council", "local councils", "council", "councils",
     "parish council", "district council", "county council", "borough council",
     "unitary authority", "town hall", "civic centre"),
    "Your council is the layer below parliament, and it is usually two layers: a district or "
    "unitary council for bins, housing, planning permission and licensing, and a county council "
    "for schools, social care, libraries and most roads. It is paid for by council tax plus "
    "business rates and grants, and the councillors are elected locally every four years.",
    asks=("how", "what", "who", "which", "explain", "mean", "means", "work", "works", "does",
          "do", "run", "responsible", "help"),
    avoid=("council tax", "council tax bill", "council tax rebate", "council tax reduction",
           "council flat", "council house", "council housing", "housing benefit",
           "parking permit", "parking fine", "parking ticket", "wheelie bin", "bin collection",
           "bins", "missed collection", "recycling", "planning permission for my",
           "how many councillors", "councillor", "councillors",
           # a council that will not deal with a problem is a job to chase, not a body to
           # describe: "the council wont fix the damp in my bathroom, what do i say" was told
           # what a council is and how it is paid for. The rows that chase it own the line.
           "wont fix", "won't fix", "will not fix", "not fixing", "wont do", "won't do",
           "refuse", "refuses", "refused", "ignored", "ignoring",
           "damp", "damp in", "mould", "mold", "leak", "leaking", "repair", "repairs",
           "complain", "complaint", "complain about", "escalate", "ombudsman",
           "what do i say", "what should i say", "who do i call", "who do i ring",
           "report it", "report a", "how do i get them")))

ENTRIES.append(_civics(
    "how-parliament-works",
    ("parliament", "westminster", "the government", "government", "uk parliament"),
    "Parliament is the Commons, the Lords and the monarch, and it makes the law, votes the taxes "
    "and holds the government to account. The government is separate: the prime minister and "
    "about 20 ministers running the departments, sitting inside parliament - which is why a "
    "government with a majority usually gets its laws through.",
    avoid=("scottish parliament", "senedd", "stormont", "holyrood", "european parliament",
           "parliament square", "parliament hill", "difference between", "different from",
           "versus", "vs",
           # "how does the government help with childcare costs" is a money question that names
           # the government, and the definition of parliament is no answer to it
           "childcare", "benefit", "benefits", "universal credit", "council tax", "tax credit",
           "help with", "entitled", "cost", "costs", "price", "pay for",
           # the councils are the layer below, and they have their own row above
           "local government", "local council", "local councils", "council", "councils",
           "councillor", "councillors", "parish", "district council", "county council")))

ENTRIES.append(_civics(
    "bill-becomes-law",
    ("bill", "bills", "law", "laws", "legislation", "act of parliament", "new law"),
    "A bill is a draft law: it has to pass both Houses, then get royal assent from the monarch. "
    "In each House it goes through a first reading (just the title), a second reading where the "
    "principle is voted, then committee, report and third reading. The Lords can delay a bill "
    "for about a year, but not kill it.",
    also=("become law", "becomes law", "become a law", "passes", "get passed", "gets passed",
          "get made", "gets made", "how a bill", "royal assent", "law get", "law gets"),
    # "how are laws passed in the us" got the Commons, the Lords and royal assent: an `avoid`
    # word cannot hold this, because "in the us" is read a second way as "in the me". The same
    # guard the election row uses keeps another country's law-making out of this one.
    guard=_only_this_country,
    avoid=("restaurant bill", "vet bill", "bill of sale",
           # The household fuels were all named here and one was missing: "how do i save money
           # on my heating bill" got the stages of a bill through parliament, because "heating"
           # is not "energy" or "gas" as far as a list of words goes. The heating-bill card has
           # the answer ("heating and hot water are most of the bill"), and every way of naming
           # that fuel belongs in this fence: the boiler, the radiators, the oil, the units.
           "heating", "heating oil", "boiler", "boilers", "radiator", "radiators", "kwh",
           "heat pump", "wood burner", "log burner", "night storage", "storage heater",
           # a bill you owe and a bill going through parliament are the same word with nothing
           # else in the line to tell them apart: "how do i pay a bill" and "how do i pay a bill
           # i dont recognise" got the stages of a bill. The paying words stand this row down, and
           # the money rows answer.
           "pay", "paying", "paid", "payment", "payments", "overdue", "unpaid", "i owe",
           "owe", "direct debit", "standing order", "refund", "refunded", "arrears",
           "recognise", "recognize", "dont recognise", "don't recognise", "in credit",
           "meter reading", "how much do i owe",
           # "what is a law of gravity" was answered with the stages of a bill: a scientific law
           # and the law on a subject are both "law", and neither is how one is made
           "law of gravity", "laws of physics", "law of physics", "law of motion",
           "laws of motion", "law of thermodynamics", "law of attraction", "law of averages",
           "sods law", "murphys law", "law of the land",
           "civil and criminal", "civil law", "criminal law", "family law", "employment law",
           "law on", "against the law", "breaking the law", "break the law")))

ENTRIES.append(_civics(
    "house-of-commons",
    ("house of commons", "the commons", "commons", "mps"),
    "The Commons is the elected half of parliament: 650 MPs, one per constituency, and the party "
    "with a majority of those seats forms the government. MPs vote on the laws, question "
    "ministers - prime minister's questions is the Wednesday set-piece - and sit on select "
    "committees that go through a department's work line by line.",
    also=("how many mps", "how many members of parliament", "select committee",
          "select committees"),
    guard=_not_one_party,
    avoid=("my mp", "contact my mp", "write to my mp", "who is my mp", "find my mp", "mp for")))

ENTRIES.append(_civics(
    "house-of-lords",
    ("house of lords", "the lords", "lords", "life peers", "peers"),
    "The Lords is the unelected half: about 800 members, mostly life peers appointed for their "
    "expertise, plus 26 bishops and a handful of hereditary peers. It revises bills line by line "
    "and sends them back to the Commons, but it can only delay one for about a year, and it "
    "cannot touch a money bill at all.",
    avoid=("landlord", "landlords", "landlady", "landladies")))

ENTRIES.append(_civics(
    "cabinet",
    ("cabinet", "cabinet minister", "cabinet ministers", "front bench", "senior ministers"),
    "The cabinet is about 20 senior ministers picked by the prime minister, each running a "
    "department - the chancellor at the Treasury, the home secretary, the foreign secretary. It "
    "meets weekly to settle the big calls, and collective responsibility binds them: argue "
    "inside the room, then defend it outside or resign.",
    avoid=("cabinet door", "cabinet hinge", "cabinet handle", "cupboard", "wardrobe")))

ENTRIES.append(_civics(
    "who-can-vote",
    ("who can vote", "who can vote in", "who can vote at", "who may vote",
     "who is allowed to vote", "who gets to vote",
     "who is entitled to vote", "eligible to vote", "right to vote", "can i vote",
     "am i allowed to vote", "can my child vote"),
    "Anyone 18 or over can vote in a general election if they are a British, Irish or qualifying "
    "Commonwealth citizen on the electoral register - members of the Lords cannot vote, and EU "
    "citizens can vote in local elections only. The register is at gov.uk/register-to-vote, and "
    "you have to be on it about 12 working days before polling day.",
    # "who can vote in a general election" reached the election row, which answers when an
    # election is and how a seat is won and never says who may vote; the one sentence about the
    # franchise sat at the end of it. Who may vote is its own fact, so it gets its own row, which
    # is written before the election row so that an equal score goes to the franchise.
    ask=_CIVICS_ASK + ("can", "could", "am i", "am i allowed"),
    # The election a franchise line names is its setting, not its question - and a line naming
    # one is exactly the line the election row also reaches, where it scores the same and wins
    # on having named the thing. So the setting is a part of its own here: "who can vote in a
    # general election" then out-scores "when is the next general election"'s card instead of
    # tying with it, and the when question is left to that card.
    also=("vote in a general election", "vote in the next election", "vote in an election",
          "vote in elections", "vote in local elections", "vote in the local elections",
          "vote at the election", "voting in a general election", "vote on polling day"),
    guard=_only_this_country,
    avoid=("vote for", "vote leave", "vote remain", "tactical vote", "swing vote",
           "vote labour", "vote conservative", "how many people voted", "turnout",
           "in the us", "american")))

ENTRIES.append(_civics(
    "general-election",
    ("general election", "election", "elections", "polling day", "poll", "polls"),
    "A general election has to be held at least every five years, and the prime minister can "
    "call one sooner. All 650 seats are fought on one day, and under first past the post the most "
    "votes in a constituency wins it, even without a majority there. Whoever can command a "
    "majority of the Commons is then asked by the monarch to form a government. To vote you have "
    "to be 18, on the electoral register, and not a member of the Lords.",
    # "when" is not one of the shared ask words, so "when is the next general election" failed
    # the ask test on this row and fell through to a reminder card ("Nothing so far - you haven't
    # mentioned anything coming up"). The when-shapes are this row's question, so they are asked
    # for here.
    ask=_CIVICS_ASK + ("when", "when is", "when will", "when does", "what date"),
    also=("how often", "when is", "when will", "when does", "next election",
          "next general election", "date of the next election"),
    guard=_only_this_country,
    avoid=("union election", "union elections", "local election", "local elections",
           "council election", "council elections", "by-election", "by-elections",
           "byelection", "byelections", "by election", "by elections",
           "election result", "election results", "who won",
           # the answer is the UK's five-year rule under first past the post, which is wrong
           # advice for a question about another country's elections
           "in the us", "in america", "the usa", "us election", "us elections",
           "american", "presidential", "electoral college",
           "conservative party", "labour party", "liberal democrats", "snp", "green party",
           "reform party", "how many mps are in")))

ENTRIES.append(_civics(
    "referendum",
    ("referendum", "referenda", "referendums", "peoples vote", "people's vote"),
    "A referendum is one yes-or-no question put to the whole electorate instead of to parliament "
    "- the 2016 vote on leaving the EU, and the 2014 vote on Scottish independence before it. It "
    "is not legally binding in UK law, but no government could ignore a clear result, so in "
    "practice it settles the question."))

ENTRIES.append(_civics(
    "constituency",
    ("constituency", "constituencies", "parliamentary seat", "boundary review",
     "boundary changes"),
    "A constituency is the area that elects one MP: 650 of them, roughly 70,000 to 80,000 voters "
    "each. The boundaries are redrawn every few years as people move, which is why a seat can "
    "change shape or vanish. Your MP is the one for the constituency your postcode sits in.",
    avoid=("my mp", "contact my mp", "write to my mp", "find my mp")))

ENTRIES.append(_civics(
    "supreme-court",
    ("supreme court", "supreme court of the united kingdom", "justices"),
    "The UK Supreme Court opened in 2009 and has 12 justices; it is the last appeal court for "
    "civil cases and for devolution questions. It cannot strike an Act of Parliament down the "
    "way the US Supreme Court can, because here parliament is sovereign - but it can rule that a "
    "minister went beyond their powers.",
    avoid=("us supreme court", "united states", "american")))

ENTRIES.append(_civics(
    "devolution",
    ("devolution", "devolved", "scottish parliament", "holyrood", "senedd",
     "northern ireland assembly", "stormont", "welsh parliament"),
    "Devolution is power handed down from Westminster to three parliaments: Scotland's at "
    "Holyrood (129 MSPs), Wales's Senedd (60 members) and Northern Ireland's at Stormont (90 "
    "MLAs). They make law on health, education, housing and transport; defence, foreign policy "
    "and most benefits stay at Westminster.",
    also=("what powers", "reserved matters")))

ENTRIES.append(_civics(
    "select-committee",
    ("select committee", "select committees", "committee of mps", "backbench committee"),
    "A select committee is a small cross-party group of MPs - or peers - that examines one area, "
    "like the Treasury committee or the health committee. They take evidence from ministers, "
    "officials and outside experts and publish reports the government has to answer, which is "
    "where a lot of the detail a debate never reaches comes from."))

ENTRIES.append(_civics(
    "voting-system",
    ("first past the post", "fptp", "voting system", "electoral system",
     "proportional representation"),
    "First past the post means the candidate with the most votes in a constituency wins the seat, "
    "even with only 35% of the vote, and it is how all 650 MPs are elected. It usually gives one "
    "party a working majority on well under half the national vote - which is why smaller parties "
    "argue for proportional representation, where seats match vote share.",
    avoid=("my mp", "contact my mp")))

ENTRIES.append(_civics_new(
    "hung-parliament",
    ("hung parliament", "hung parliaments", "coalition", "coalitions", "no majority",
     "balance of power", "confidence and supply"),
    "A hung parliament is one where no single party has a majority of the 650 seats, so the "
    "largest party has to govern with the support of others: the 2010 coalition with the Liberal "
    "Democrats, and in 2017 the Conservatives paying the DUP for a confidence and supply deal. "
    "The sitting prime minister stays on and gets the first chance to form a government, and if "
    "that fails the monarch asks the next party.",
    also=("what happens", "what is", "who governs", "who forms", "form a government")))

ENTRIES.append(_civics_new(
    "mps-pay",
    ("mps paid", "mp salary", "mps salary", "mps earn", "mps wages", "mp pay",
     "how much do mps", "how much does an mp", "mp expenses", "mps expenses", "salary of an mp"),
    "An MP's basic salary is £91,346 a year, set by the Independent Parliamentary Standards "
    "Authority rather than voted by MPs, and it goes up with public sector pay. Office costs, "
    "staff and travel are claimed separately against receipts and published, so the headline "
    "figure and the expenses are not the same pot. A minister or the prime minister gets extra "
    "on top for the job.",
    also=("how much", "what is", "what are", "earn", "paid")))

ENTRIES.append(_civics_new(
    "bill-of-rights",
    ("bill of rights", "human rights act", "human rights", "civil liberties",
     "european convention on human rights", "echr"),
    "The UK has no single written constitution and no bill of rights in the American sense; "
    "rights come from the Human Rights Act 1998, which wrote the European Convention on Human "
    "Rights into UK law, plus ordinary statutes. Under it a court can declare a law incompatible "
    "with a Convention right, but only parliament can change the law - which is why a British "
    "bill of rights is argued about so often and settled so rarely.",
    avoid=("consumer rights", "refund", "warranty", "guarantee", "tenancy", "my rights at work",
           "employment rights", "landlord", "patient", "data protection", "gdpr")))

ENTRIES.append(_civics_new(
    "lord-mayor",
    ("lord mayor", "lord mayor of london", "city of london", "lord mayors"),
    "The Lord Mayor of London is the ceremonial head of the City of London - the square mile of "
    "banks, not the whole city - elected for one year, and the job is to promote the financial "
    "district and host visiting heads of state. The mayor of London is a different job: elected, "
    "full time, and running transport and policing for the whole city.",
    also=("what does", "what is", "who is", "do", "role", "job"),
    # the elected mayor of London is a job main already answers with a name and a date, and this
    # row took it: "who is the mayor of london" is not the City of London's ceremonial head
    avoid=("mayor of london", "who is the mayor", "metro mayor", "combined authority",
           "elected mayor", "mayor of greater manchester")))

ENTRIES.append(_civics(
    "parliament-vs-government",
    ("parliament", "government", "commons", "lords", "westminster"),
    "The government runs the country day to day - the prime minister, the cabinet and their "
    "departments - and parliament makes and checks the laws. The government sits inside "
    "parliament, so the same people are in both, and the roles are opposite: ministers propose, "
    "and parliament scrutinises, its own backbenchers included.",
    asks=("difference between", "different from", "versus", "vs", "distinction",
          "same thing", "how is parliament different")))
