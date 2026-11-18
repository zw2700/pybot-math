"""Clothes, laundry and looking after yourself: the everyday asks about what we wear.

The answers lane owns this domain. Entries are keyed by the garment and the problem (a
jumper that shrank, a wine stain, blisters from new shoes) rather than by wording, so one
entry answers "how do I get X out of Y", "my Y is ruined" and "can I fix this". The advice
is the ordinary version a careful friend gives: what to do first, what not to do, and when
to take it to a professional.

Most of these lines are read with no topic at all, so the matcher's two-word rule is what
keeps the domain honest: a passing mention of a colour or a wedding never gets a canned
answer on its own.
"""
import re

from .wording import A_JOB_LEFT_UNDONE
from .lookup import (ASK_ABOUT, A_WEATHER_ASK, a_food_is_being_kept, entry,
                     only_a_container)

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
# Clothes and shoes are usually read as shopping, and clothes care as home-and-diy, until the
# understanding lane gives this area a topic of its own.
ANSWERS = ("shopping", "home-and-diy")

# "glasses" and "glass" are one word to the matcher, so the oven door, a window, a mirror and a
# pint glass all reach the spectacles answer. These are the things that are glass but not
# glasses: the entry turns them down and the line gets the honest hedge instead, while "my
# glasses are scratched" and "how do i clean my lenses" keep the answer.
_NOT_SPECTACLES = re.compile(
    r"\b(?:oven|hobs?|cooker|microwave|door|doors|window|windows|windscreen|windshield|mirror|"
    r"table|tables|shower|bicarb|bicarbonate|soda|chimney|glasses of|wine glass|pint glass|"
    r"car|mot|test)\b")

# The chapped-lip answer, shared by the cracked lip and the lip the cold has swollen: it is the
# same skin and the same fix, and one copy of the advice keeps the two from drifting apart.
_LIP_BALM = ("Use a plain lip balm with petrolatum or beeswax, reapply often, and stop licking "
             "your lips: saliva dries them and makes it worse. Cracked lips are usually from "
             "licking them, because saliva dries as it evaporates and takes the lip's own oil "
             "with it. Cracks at the corners of your mouth often clear with an antifungal cream "
             "from the pharmacy.")

# A lip is dry, cracked or swollen and it is not the hands, the feet or the face beside it.
_LIPS_NOT_DRY = ("hands", "hand", "skin", "feet", "heels", "elbows", "face", "knuckles")

_LENS_HELP = ("A scratch in the coating can't be polished out, and paper towels and tissues are "
              "what make most of them: wash the lenses with water and washing-up liquid, then dry "
              "them with a microfibre cloth. An optician can fit new lenses into your own frame.")


# "flat" is an apartment, a tyre, a battery and a refusal before it is a hairstyle, so a row
# whose other half is ordinary verbs ("get", "more", "stop", "add") read "we cant get a dog
# because of the flat" as a question about mousse and answered it with a card about drying hair
# upside down. The same happens to "the flat is cold" and "my phone battery is flat": one
# styling word plus one everyday verb is two words, and the two-word rule is what let it through.
# A line is about hair only when it names hair, or names the thing the row is actually about
# (volume, body, lifeless, limp), which is the word a person uses when they leave hair unsaid.
# "Put on" is not always a garment. "what music should i put on for a dinner party" was the
# dinner-party outfit, because "put on" is a wear ask and the place is the row's other key; the
# same happened to a wedding and to a film. The thing being put on decides the question: music,
# a song, a film, the telly, the kettle or a wash is nobody's outfit, and the row stands down so
# their own entries answer. A line that also names clothes is still the clothes question even
# when it mentions music ("what should i wear to a music festival").
PUT_ON_OTHER = frozenset((
    "music", "song", "songs", "album", "albums", "playlist", "playlists", "record",
    "records", "radio", "podcast", "podcasts", "film", "films", "movie", "movies",
    "tv", "telly", "television", "kettle", "oven", "washing", "wash", "lights",
    "heating", "pot", "pan", "saucepan", "candle", "candles", "makeup", "lipstick",
    "nappy", "nappies", "plaster", "cream", "sunscreen", "spot", "spots"))

# The wear words that are a garment word on their own: a line carrying one of these is a clothes
# question whatever else it puts on.
_DEFINITELY_CLOTHES = ("wear", "wearing", "worn", "outfit", "outfits", "dressed", "clothes",
                       "dress", "dresses", "shoes", "shoe", "trainers", "boots", "suit")


# A date night being cooked for: the words that say the line wants a meal rather than an outfit.
_MEAL_FOR_THE_NIGHT = frozenset((
    "cook", "cooks", "cooking", "cooked", "make", "makes", "making", "made", "bake", "baking",
    "recipe", "recipes", "meal", "meals", "eat", "eating", "dine", "dining", "supper",
    "menu", "order", "restaurant", "table", "serves", "starter", "pudding", "dessert",
))


# A machine that runs warm is not a person who wants to be warm: "my fridge is running warm" met
# the keep-warm notes' "warm" and their "running" and was told what to wear for a run in winter.
# The appliance keeps a line out of those notes, and "its warm and i want to run" still gets them
# because it names no appliance.
A_MACHINE_RUNNING_WARM = (
    "fridge", "freezer", "fridge freezer", "washing machine", "washer", "dishwasher",
    "tumble dryer", "dryer", "oven", "heater", "kettle", "microwave", "laptop", "computer",
    "pc", "console", "phone", "monitor", "printer", "hoover", "vacuum", "appliance")


# A zip is two different jobs and the garment word does not tell them apart. "how do i sew a zip
# into a dress" and "how do i put a new zip in a jacket" are the putting-in card, and the fault row
# won both on the garment ("dress") and on "new" alone; the needle word, or the phrase for fitting
# one, is what separates them. A line that also names a fault ("my zip is stuck, can i sew it")
# stays with the fault card, so this is a guard on the fault row rather than an avoid word.
_ZIP_NEEDLE = re.compile(
    r"\b(?:sew|sews|sewing|sewn|stitch|stitches|stitching|unpick|unpicks|unpicking|baste|"
    r"basting|tack|tacking|insert|inserts|inserting|zip foot|zipper foot|invisible zip)\b")
_ZIP_FITTING = re.compile(
    r"\b(?:put(?:ting)? (?:a |an |the )?(?:new )?zip|put in a zip|new zip|replace|replacing|"
    r"replace the zip|fit a zip|fitting a zip|change the zip|changing the zip|zip needs "
    r"replacing)\b")
_ZIP_FAULT = re.compile(
    r"\b(?:stuck|jammed|jam|fix|fixing|wont|won't|broken|broke|split|slider|teeth|repair|"
    r"mend|mending|coming down|comes down|undone|unzipping|unzip|came off|come off|fell off|"
    r"pull|pull tab|zip pull|zipper pull|zip tab|slider)\b")


def _not_fitting_a_zip(understood):
    """True unless the line is about putting a zip in, which is the sewing card's job."""
    said = " ".join(str(understood.get(k) or "") for k in ("text", "clean", "norm_text")).lower()
    if _ZIP_FAULT.search(said):
        return True
    return not (_ZIP_NEEDLE.search(said) or _ZIP_FITTING.search(said))


def _the_date_night_is_a_meal(understood):
    """False when the date night is a meal: "what should i cook for a date night" is dinner.

    The words that settle it are the cooking ones, said on the line or as a dish named for the
    night ("date night dinner ideas", "dinner at home"), because "dinner" alone says when, not
    what was asked for: "what should i wear for a dinner date" is the outfit question.
    """
    said = [str(word).lower() for word in (understood.get("words") or ())]
    flat = " ".join(said) or str(understood.get("clean") or understood.get("text") or "").lower()
    if any(word in _MEAL_FOR_THE_NIGHT for word in said):
        return False
    for shape in ("dinner ideas", "dinner for", "dinner at home", "dinner tonight",
                  "dinner for two", "dinner to cook", "meal ideas"):
        if shape in flat:
            return False
    return True


# An interview in the line is the office's question, not the code's: "is smart casual ok for an
# interview" wants what to wear to the interview, and work.py answers that better than a
# definition of the code. So the code's row stands down on that one shape and keeps the rest -
# a wedding, a party, a funeral, a work dinner and even "for the office" all want the code's
# meaning, which is the row's own job.
AN_INTERVIEW_IN_A_DRESS_LINE = ("interview", "interviews", "interviewing", "interviewer",
                                "interviewers")


def _the_code_is_not_an_interview(understood):
    """False when the line is about an interview, which has its own answer in work.py."""
    clean = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    clean = re.sub(r"[^a-z0-9' ]+", " ", clean)
    return not any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean)
                   for word in AN_INTERVIEW_IN_A_DRESS_LINE)


def _put_on_is_clothes(understood):
    """False when what the line puts on is not clothing (music, the telly, the kettle)."""
    said = [str(word).lower() for word in (understood.get("words") or ())]
    flat = " ".join(said)
    if "put on" not in flat and "puts on" not in flat and "putting on" not in flat:
        # every other ask word ("wear", "outfit", "dress code") is a clothes word itself
        return True
    if any(word in said for word in _DEFINITELY_CLOTHES):
        return True
    return not any(word in said for word in PUT_ON_OTHER)


_HAIR_LINE = re.compile(
    r"\b(?:hair|hairs|haircut|hairdo|scalp|roots|fringe|bob|bangs|ponytail|braid|plait|curls"
    r"|volume|lifeless|limp|no body|more body|needs body|thin looking|looks thin|flyaway"
    r"|flyaways)\b")


# What a clothes question is asked with, and the row's `ask`. It used to be the bare "what" in
# the key's second part, which is what a gift ask says too: with a round-number age in the first
# part ("what should i get my mum for her 70th") two positions were met with no wearing word in
# the line, and the answer to a present was the dress code. An outfit row should be asked with a
# wearing word, so the words people dress with are the ask and "what" alone is not enough.
_WORN_WORDS = ("wear", "wearing", "wears", "wore", "worn", "outfit", "outfits", "dress",
               "dresses", "dressed", "clothes", "clothing", "attire", "clobber", "getup",
               "put on", "dressing", "dress code", "smart", "casual")


def _a_hair_line(understood):
    """True when the line is about hair rather than a flat, a tyre or a battery."""
    text = str(understood.get("norm_text") or understood.get("clean")
               or understood.get("text") or "").lower()
    return bool(_HAIR_LINE.search(" " + text + " "))


# A colour in front of "one" is a preference between two things, not a colour of washing: "do
# you want the white one or the grey one" was answered "Wash white cotton at the hottest
# temperature the label allows", because the whites wash keys on "white" and the shirt in the line
# was only the colour of a choice. Nothing in the wash knows what the thing is, so the row stands
# down. Same reading as `dishes.COLOUR_CHOICE`, where the vegetable rows were taking a "green".
_A_COLOUR_CHOICE = re.compile(
    r"\b(?:the|this|that|these|those|my|your|his|her|their|our|a|an)\s+"
    r"(?:green|blue|red|black|white|grey|gray|brown|pink|purple|orange|yellow|beige|cream"
    r"|navy|gold|silver)\s+(?:one|ones|thing|things|version|colour|color)\b", re.I)

# A determiner alone is not a choice: the choice has to be put. Same reading as
# `dishes._CHOICE_FRAME`, so the two rows agree on what a colour choice is.
_A_CHOICE_FRAME = re.compile(
    r"\bor\b|\bvs\b|\bversus\b|\bbetween\b|\bwhich\b|\bshall i\b|\bshould i\b"
    r"|\bdo you want\b|\bwould you\b|\brather\b|\bprefer\b|\bpick\b", re.I)


def _not_a_colour_choice(understood):
    """False when the line is choosing between two colours, so no wash answers it."""
    said = ""
    if isinstance(understood, dict):
        said = str(understood.get("norm_text") or understood.get("clean")
                   or understood.get("text") or "")
    return not (_A_COLOUR_CHOICE.search(said) and _A_CHOICE_FRAME.search(said))


def _not_a_pane(understood):
    """The guard form of `_spectacle_glass`, for a row whose reply is a fixed card.

    `guard` is handed the reading and nothing else, so a pane named two turns back is out of
    reach here; the line itself is what the scratch row is read on too.
    """
    return _spectacle_glass({}, understood) is not None


def _spectacle_glass(memory, understood):
    """The lens answer, unless the glass in the line is a pane or a tumbler rather than glasses.

    The line on its own often does not say which glass it means - "will it scratch the glass" -
    so the turn before counts too: a chat that has just been about the oven door is not asking
    about a pair of spectacles.
    """
    def _pane(text):
        text = re.sub(r"[^a-z0-9' ]+", " ", " " + str(text or "").lower() + " ")
        return bool(_NOT_SPECTACLES.search(text))

    if _pane(understood.get("clean") or understood.get("text") or ""):
        return None
    turns = memory.get("turns")
    if isinstance(turns, list):
        for turn in turns[-2:]:
            if isinstance(turn, dict) and _pane(turn.get("user")):
                return None
    return _LENS_HELP


_GARMENT = re.compile(
    r"\b(?:shirt|shirts|blouse|trousers|pants|skirt|dress|suit|jacket|coat|sleeve|sleeves"
    r"|collar|cuffs?|linen|cotton|polyester|wool|denim|jeans|shorts|tablecloth|curtains?|napkins?"
    r"|bedding|sheets?)\b")
_IRON_REPLY = ("Iron while the shirt is still slightly damp, start with the collar and cuffs on "
               "the reverse, then the body and finally the sleeves; a pressing cloth stops shiny "
               "marks. Cotton takes a hot iron, polyester a warm one, and wool always through a "
               "damp cloth.")


def _iron_shirt(memory, understood):
    """A line that says "press" needs something made of cloth to press.

    "press" is the verb for a shirt and also for a team pressing, a coffee press and a
    newspaper - a line that says "press" with no garment and no iron is not this question.
    """
    said = str((understood or {}).get("clean") or "")
    if _GARMENT.search(said) or re.search(r"\b(?:iron|ironing|steam|crease)\b", said):
        return _IRON_REPLY
    return ""


# A blister after a scald is a burn follow-up, not a rubbed heel. The words in "can i pop the
# blister" are the same either way, so the turn before decides, and the answer is the burn one:
# a burn blister is a sterile dressing, so it is left whole and covered loosely. The heat words
# are the ones people actually use - "i got burnt at work", "hot oil on my arm", "the kettle" -
# not just the word burn, which misses most of them.
_BURN_BEFORE = re.compile(
    r"\b(?:burn\w*|scald\w*|sun\s?burn\w*|boil\w*|kettle|steam\w*|"
    r"hot\s+(?:water|oil|fat|pan|plate|metal|oven|hob|grill|toaster)|"
    r"(?:straight\s+)?(?:out\s+of|from)\s+the\s+(?:oven|grill|hob))\b", re.I)
_BLISTER_FIRST = ("Cover it with a proper blister plaster and leave it alone: don't pop it. New "
                  "shoes go on in short stretches at home with thick socks first, and a little "
                  "petroleum jelly on the hot spots stops the next one.")
_BLISTER_POP = ("Don't pop it: cover the blister with a padded blister plaster and wear the shoes "
                "for short stretches at first. Two pairs of thin socks, or a little blister balm "
                "on the heel, make the next day much easier.")
_BLISTER_STOP = ("Break new shoes in slowly at home with thick socks, and put a little petroleum "
                 "jelly on the hot spots before you wear them. Slightly looser laces and two pairs "
                 "of thin socks stop most of them.")
# The prevention line answers a question about the next pair of shoes, not a sore that is
# getting worse: "my blister wont stop weeping" has "stop" in it but wants the care answer.
_PREVENT_BLISTER = re.compile(
    r"\b(?:prevent\w*|next\s+time|"
    r"stops?\s+(?:getting\s+)?(?:the\s+)?(?:blisters?|them)\b|"
    r"stops?\s+it\s+(?:from\s+)?(?:happening|coming|again|next\s+time)\b|"
    r"avoid\s+(?:the\s+)?(?:blisters?|them)|not\s+get\s+(?:them|another))", re.I)
# A shoe that rubs is a question about the pair of shoes, not a blister that is already there:
# "how do i stop shoes rubbing" and "my new shoes rub" were both answered "cover it with a proper
# blister plaster", for a blister the person does not have yet. Rub with no blister named is the
# prevention answer; a line that names the blister, the sore or the raw heel keeps the care.
_RUBBING = re.compile(r"\b(?:rub|rubs|rubbing|rubbed|chafe|chafes|chafed|chafing)\b", re.I)
_BREAKING_IN = re.compile(
    r"\b(?:break(?:ing)?\s+(?:them|it|these|those|the|my)?\s*(?:new\s+)?(?:shoes|boots|trainers|heels)?"

    r"|break\s+in|broke\s+in|wear(?:ing)?\s+(?:them|it)?\s*in|wear(?:ing)?\s+in|"
    r"soften\w*|softer|stiff\w*)\b", re.I)
_BLISTER_NAMED = re.compile(
    r"\b(?:blisters?|blistered|sore|soreness|hurts?|hurting|raw|bleeding|weeping|pus|"
    r"got\s+rubbed|been\s+rubbed|is\s+rubbed|rubbed\s+it)\b", re.I)

_BLISTER_BURN = ("Don't pop it - a burn blister is a sterile dressing of its own. Cover it loosely "
                 "with cling film or a clean non-fluffy cloth and leave it be; a blister bigger "
                 "than your palm, on the face or hands, or one that keeps weeping needs a doctor.")
# A sore that is getting worse wants care, not advice about the next pair of shoes: "my blister
# wont stop weeping" is here for the weeping, not for prevention.
_BLISTER_SORE = re.compile(r"\b(?:weep\w*|ooz\w*|pus|infect\w*|smell\w*|spread\w*|hot|red)\b",
                           re.I)
_BLISTER_CARE = ("Cover it with a clean non-fluffy dressing and leave it alone: don't pop it. A "
                 "blister that keeps weeping, or one that is hot, spreading or smells, needs a "
                 "doctor.")


def _new_shoe_blisters(memory, understood):
    """The rubbed-heel answer, unless this blister is one the burn thread is talking about.

    A scald that blisters and a heel rubbed by new shoes ask the same short question next,
    "can i pop the blister", and only the line before tells them apart. A burn also gets the
    "don't pop it" line whenever someone asks about popping, because that is the one fact they
    need; a new shoe gets the prevention answer unless they ask to pop it.
    """
    text = str(understood.get("clean") or understood.get("text") or "")
    burn = _BURN_BEFORE.search(text)
    sore = _BLISTER_SORE.search(text)
    turns = memory.get("turns")
    if not burn and isinstance(turns, list):
        for turn in turns[-2:]:
            said_before = str(turn.get("user") or "") if isinstance(turn, dict) else ""
            if _BURN_BEFORE.search(said_before):
                burn = True
            if _BLISTER_SORE.search(said_before):
                sore = True
    if burn:
        return _BLISTER_BURN
    if sore:
        return _BLISTER_CARE
    if re.search(r"\b(?:pop|burst|drain|bust)\b", text, re.I):
        return _BLISTER_POP
    # "how do i stop it hurting" is about the sore on the foot now, not the next pair of shoes.
    if re.search(r"\bstop\s+(?:it|them|the\s+blister)\s+(?:from\s+)?(?:hurting|aching|pain)\b",
                 text, re.I):
        return _BLISTER_POP
    if _PREVENT_BLISTER.search(text):
        return _BLISTER_STOP
    # the pair of shoes that rubs, before there is anything to cover: a shoe that rubs or a
    # stiff new pair wants the breaking-in answer, and nothing named yet wants covering
    if (_RUBBING.search(text) or _BREAKING_IN.search(text)) and not _BLISTER_NAMED.search(text):
        return _BLISTER_STOP
    return _BLISTER_FIRST


GLASSES_REPAIR = (
    "Take them to an optician first: a frame repair or a new frame with your lenses usually "
    "costs £20 to £50, many do it while you wait, and it is often free if the glasses came "
    "from them. A dab of superglue holds a plastic arm for a few weeks if you are stuck, "
    "but it will not take the strain of putting them on, so treat it as a stopgap. If the "
    "frame has snapped at the bridge or the lenses are scratched, a new pair is usually "
    "better value, and home contents insurance sometimes covers accidental damage.")

# The words that make a line the second half of a glasses repair: "can i glue it back on",
# "will superglue hold", "can i fix them myself". The line names no pair of its own, so it only
# reaches this entry through the conversation, and it gets its own wording - the repeat guard in
# the arbiter drops a reply that comes back word for word.
_GLUE_WORDS = ("glue", "glued", "gluing", "superglue", "super glue", "araldite", "epoxy",
               "back on", "back together", "stick it back", "stick them back",
               # "can i fix them myself" and "can i do it myself" are the same second half: the
               # repair answer has already been said, and what is asked is whether it can be done
               # at home, which is the glue and its limits
               "myself", "fix it myself", "fix them myself", "do it myself", "do them myself")
_GLASSES_WORDS = ("glasses", "specs", "spectacles", "sunglasses", "frame", "frames", "arm",
                  "arms", "temple", "temples", "lens", "lenses", "rim", "rims", "bridge")

GLASSES_GLUE = (
    "Superglue is the stopgap, not the repair: a dab on a clean, dry break holds a plastic arm "
    "for a few weeks, but it will not take the strain of putting them on and it clouds a lens if "
    "it creeps. The lasting fix is an optician - a frame repair or your own lenses in a new frame "
    "is £20 to £50, often free if they sold you the glasses, and most do it while you wait. Do not "
    "use it on a metal hinge or on the bridge: those need a screw or a solder, and glue there "
    "makes the proper repair harder.")


# A glass somebody was drinking from is not a pair of spectacles, and the matcher cannot tell
# them apart: "glasses" is a loose form of "glass", so both cards read "my glass broke" and the
# pair won it. The singular with a determiner in front of it is the drink, and the pair is always
# plural or named as a pair, so the spectacles rows stand down on it.
_A_DRINKING_GLASS = re.compile(r"\b(?:my|a|the|this|that|another)\s+glass\b(?!\s*of\b)",
                               re.I)
_A_GLASS_OF = re.compile(r"\bglasses\b|\bspectacles\b|\bspecs\b|\beyeglasses\b", re.I)


def _the_glass_is_a_drink(understood):
    """False when the line's "glass" is the one somebody was drinking from."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    if _A_GLASS_OF.search(said):
        return True
    return not _A_DRINKING_GLASS.search(said)


def _glasses_repair(memory, understood):
    """The optician answer, or the glue answer when the line is the second half of it."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    men = [word for word in _GLUE_WORDS if word in said]
    if men and not any(word in said for word in _GLASSES_WORDS):
        return GLASSES_GLUE
    return GLASSES_REPAIR


# A hot wash is also what you say when the machine is wrong: "my washing machine smells of damp"
# then "ive tried a hot wash already" wants the next thing to try, not the card on what each
# number on the dial is for. So the entry stands down while the conversation is about a machine
# that is faulty, and only a line that has left that behind is a temperature question.
_A_FAULTY_MACHINE = ("smell", "smells", "smelly", "stink", "musty", "damp", "mildew", "mould",
                     "mold", "leak", "leaks", "leaking", "leaked", "drain", "drains", "draining",
                     "spin", "spins", "spinning", "error", "broken", "broke", "wont", "won't",
                     "stopped", "noise", "noisy", "banging", "rattle", "rattling", "flood",
                     "flooded", "stuck", "blocked", "smoking", "tripping", "fuse", "repair")

# A sock is not a sock: "what socks go with a suit" reached no card at all and "which socks for
# a wedding" was answered with when to book a hotel room, because "for a wedding" is the travel
# row's key. What a person asks about a sock is which one to put on with what, so this is a card
# of its own with the pairings people actually ask for. A sock being washed, smelling or full of
# holes is a laundry or a repair line, and those words stand this row down.
_SOCKS_FORMAL = re.compile(
    r"\b(?:suit|suits|wedding|weddings|interview|interviews|funeral|funerals|smart|formal|"
    r"black tie|office|work|dress|trousers|shirt|shirts)\b", re.I)
_SOCKS_CASUAL = re.compile(
    r"\b(?:jeans|trainer|trainers|sneaker|sneakers|shoe|shoes|plimsoll|plimsolls|gym|"
    r"shorts|casual|sports?|running|walking|hiking|boots?)\b", re.I)
_SOCKS_COLOUR = re.compile(
    r"\b(?:brown|black|navy|grey|gray|white|tan|blue|beige)\b", re.I)


# The two words that say the pairing is the question: "can i wear black socks with brown shoes" is
# not a general colour rule, it is that pair.
_SOCKS_BLACK_AND_BROWN = re.compile(r"\bblack\b.*\bbrown\b|\bbrown\b.*\bblack\b", re.I)
_SOCKS_SPORT = re.compile(
    r"\b(?:run|running|jog|jogging|marathon|half marathon|10k|5k|parkrun|gym|cycling|"
    r"walking|hiking|sport|sports|football|rugby|netball|hockey)\b", re.I)


def _socks(memory, understood):
    """Dark and long with anything smart, plain and matching the trousers with everything else."""
    said = _the_line(understood)
    if _SOCKS_SPORT.search(said):
        return ("For running, walking or the gym, wear a thin synthetic or merino-wool sock with a "
                "flat seam across the toe, in the same shoe you train in: cotton holds sweat "
                "against the skin and that is what blisters come from. Two thin pairs are warmer "
                "and rub less than one thick pair, and the sock should be tight enough not to "
                "bunch under the arch.")
    if _SOCKS_BLACK_AND_BROWN.search(said):
        return ("Black socks with brown shoes is the pairing to avoid: the sock should match the "
                "trousers, so with brown shoes wear a dark brown, navy or charcoal sock, or keep "
                "the shoes for a lighter suit. Nobody notices a sock that matches the trousers "
                "and everybody notices one that fights the shoes.")
    if _SOCKS_FORMAL.search(said):
        return ("Dark socks that match the trousers rather than the shoes, long enough to cover "
                "the calf so no bare leg shows when you sit down: navy, charcoal or black in "
                "wool or a wool blend, plain unless the suit is patterned. Black socks with "
                "brown shoes is the one pairing that looks wrong, so match the trousers and let "
                "the shoes be their own colour.")
    if re.search(r"\bwhite\b", said, re.I) and _SOCKS_CASUAL.search(said):
        return ("White socks are fine with trainers, shorts and gym kit, and wrong with a suit "
                "or smart trousers: with those, wear a dark sock that matches the trousers, long "
                "enough that the calf stays covered when you sit down.")
    if _SOCKS_CASUAL.search(said) or _SOCKS_COLOUR.search(said):
        return ("Go by the trousers rather than the shoes: a plain sock a shade darker than the "
                "trousers is the safe pairing, which means dark grey or navy with jeans and "
                "charcoal or black with smart trousers. Cotton for everyday, wool or a wool "
                "blend when the foot will be in a shoe all day, because cotton stays wet against "
                "the skin.")
    return ("Match the trousers rather than the shoes, dark navy, charcoal or black, and long "
            "enough that no bare leg shows when you sit down. Cotton for everyday and wool or a "
            "wool blend for a shoe you are in all day, and thin wool rather than thick cotton "
            "with anything smart, because a thick sock makes a well-fitted shoe tight.")


# The laundry that needs 60C rather than the everyday 30: a dial question that names one of these
# is not the shirts-and-jeans question, and the answer leads with the heat they need.
NEEDS_SIXTY = re.compile(
    r"\b(?:bed ?sheets?|sheets?|bedding|duvet covers?|pillow ?cases?|towels?|flannels?|"
    r"underwear|pants|knickers|boxers|socks?|napp(?:y|ies)|dish ?cloths?|tea towels?)\b", re.I)



# A wash is the right first move for cotton, linen and synthetics and the wrong one for suede,
# which stiffens and stains the moment it gets wet: so the route is picked by what the line names.
_MOULD_SOFT = ("leather", "suede", "nubuck", "patent", "shoe", "shoes", "trainer", "trainers",
               "boot", "boots", "handbag", "bag", "bags", "faux leather")


def _mould_wash(memory, understood):
    return ("Brush the dry spores off outdoors and wash it at the hottest temperature the care "
            "label allows with ordinary detergent: that alone clears cotton, linen and "
            "synthetics, and drying it in the sun finishes the job. Don't bleach wool, silk or "
            "anything dyed - use a colour-safe oxygen bleach instead. Mould that has gone through "
            "the padding of a pillow, a pram mattress or a padded jacket is not worth saving. "
            "Damp is what feeds it, so dry the piece right through and ventilate where it is "
            "kept, or the spots come back.")


def _mould_wipe(memory, understood):
    return ("Don't wash it: brush the spores off outdoors with a soft brush, then wipe it over "
            "with a cloth wrung out in a little white vinegar and let it dry slowly, away from "
            "heat - a radiator or a hot dryer hardens and cracks leather and shrinks suede. "
            "Finished leather likes a conditioner afterwards; suede that has gone stiff or black "
            "all through wants a leather specialist, and faux leather and patent wipe clean with "
            "the same vinegar cloth. Damp is what grew it, so air the piece and keep it dry from "
            "now on.")


def _mould_on_it(memory, understood):
    line = " " + re.sub(r"[^a-z0-9' ]+", " ",
                        str((understood or {}).get("clean") or (understood or {}).get("text")
                            or "").lower()) + " "
    if any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", line)
           for word in _MOULD_SOFT):
        return _mould_wipe(memory, understood)
    return _mould_wash(memory, understood)


def _conversation_so_far(memory):
    """What the person said in the turns before this one, lower case, as one string."""
    parts = []
    for one in (memory or {}).get("turns") or []:
        if isinstance(one, dict):
            parts.append(str(one.get("user") or ""))
    return " ".join(parts).lower()


_SAID = ("clean", "norm_text", "text")


def _the_line(understood):
    return " ".join(str((understood or {}).get(key) or "") for key in _SAID).lower()


# The words that make a line about a garment a buying question rather than a care or a repair
# one. "What" and "which" are in it because "what boots for the winter" names no other intent.
_BUYING_WORDS = ("buy", "buying", "choose", "choosing", "pick", "picking", "look for",
                 "look out for", "best", "good", "which", "what", "worth", "recommend",
                 "need", "need to", "get", "kind", "type", "fit", "fits", "size",
                 "sizing", "cheap", "budget", "price", "spend", "under", "quid")


def _any_word(text, words):
    return any(word in text for word in words)


def _said_lately(memory, words, turns=3):
    """True when one of the last few lines the person typed says one of these words."""
    from ..memory import recent

    for turn in recent(memory, turns):
        line = str(turn.get("user") or "").lower()
        if _any_word(line, words):
            return True
    return False


# What a boot that is already yours wants when it stops being waterproof, or starts to smell or
# squeak: those are care questions, and buying advice answers none of them. Kept apart from the
# key words because "waterproof" is how a person asks for a boot and also how they say theirs
# has stopped working.
_BOOT_CARE = ("keep my", "keeping my", "keep them", "keeps my", "reproof", "reproofer",
              "proofing", "waterproofing", "waterproof them", "waterproof it", "wax", "polish",
              "condition", "care for", "look after", "clean", "wash", "smell", "smells", "smelly")


def _boots_to_buy(memory, understood):
    """The boot for the ground the line names: a wet hill, ice, or just "a boot"."""
    # A boot question in a chat about a pitch is the surface question, and that row knows the
    # ground: "my son is 8 and wants to play football" then "which boots should i get him" was
    # answered with how a walking boot should fit.
    if _said_lately(memory, ("football", "rugby", "five a side", "5 a side", "netball", "hockey",
                             "match", "pitch", "training session", "studs", "astro", "moulded")):
        return None
    said = _the_line(understood)
    # "how much should i spend" is the second boot question in a chat, and the figure is the
    # answer: the fit paragraph has already been given and repeating it is no answer.
    if _any_word(said, ("how much", "spend", "price", "cost", "cheap", "budget", "afford")):
        return ("Spend £90 to £160 on a walking boot with a waterproof membrane: it lasts about a "
                "decade and can be resoled, where a £40 boot is usually a sole that splits in a "
                "year and a lining that lets water in. Everyday and winter boots are £60 to "
                "£120, and at any price the fit matters more than the badge.")
    if _any_word(said, ("wellies", "welly", "wellington", "wellington boots")):
        return ("For a muddy path a wellington beats a walking boot: buy rubber with a deep lugged "
                "sole and a real heel, and check the top of the boot does not rub your calf when "
                "you walk, which is what puts most people off a long walk in them. A neoprene "
                "lining keeps your feet warm in winter, and half a size up leaves room for thick "
                "socks.")
    if _any_word(said, ("walking", "hiking", "hill", "mountain", "fell", "rambl", "trek",
                        "lake district", "muddy", "bog", "ridge")):
        return ("For walking, buy a boot with a waterproof membrane (Gore-Tex or similar), a "
                "fairly stiff sole with deep lugs and enough of a cuff to hold your ankle on "
                "rough ground. Try them on late in the day in the socks you will walk in, with a "
                "thumb's width at the toe and no lift at the heel, and wear them around the "
                "house an evening at a time before a long walk.")
    if _any_word(said, ("winter", "snow", "ice", "icy", "slush", "grit", "frost", "cold")):
        return ("For winter the tread matters more than the lining: deep soft rubber lugs grip "
                "ice and packed snow, where a hard plastic sole just skates. Buy them roomy "
                "enough for a thick wool sock with the heel still snug, and check the upper is "
                "waterproof rather than only shower resistant.")
    return ("Fit first: try them on in the afternoon in the socks you will wear, with a thumb's "
            "width at the toe and no lift at the heel, because a boot will not stretch to fit. "
            "Then look at the sole - deep rubber tread, a waterproof upper - and at lacing that "
            "lets you tighten the ankle without pinching across the foot.")


def _trainers_to_buy(memory, understood):
    """A pair for a suit, or the pair that replaces one that has worn through."""
    said = _the_line(understood)
    # what they cost is its own question, and a figure is the answer to it
    if _any_word(said, ("how much", "spend", "price", "cost", "cheap", "budget", "afford",
                        "worth", "expensive")):
        return ("Spend £70 to £120 on everyday trainers and £90 to £130 on running shoes: past "
                "about £130 you are paying for a logo or a limited colourway, and below £50 the "
                "midsole is the part that gives up first. Replace them when the sole is flat "
                "under the ball of the foot, not when they look scuffed.")
    if _any_word(said, ("suit", "smart", "navy", "office", "interview", "wedding", "go with",
                        "wear with", "pair with", "trousers", "chinos", "shirt")):
        return ("With a suit, keep the trainer plain and clean: a low-profile white or black "
                "leather pair, no visible logo, a thin sole, and spotless matters more than the "
                "brand. Chunky soles, mesh and colours read as weekend, and suede with a suit "
                "looks like you forgot your shoes.")
    return ("Replace them once the midsole has gone flat or the heel is worn through: the "
            "cushioning is what has gone, no repair brings it back, and it starts to show as heel "
            "or knee pain. Buy at the end of the day in the socks you will wear them with, leave "
            "a thumb's width at the toe, and check the heel does not lift when you walk.")


def _take_up_hem(memory, understood):
    """The denim method for a pair of jeans, the running stitch for everything else."""
    said = _the_line(understood)
    if _any_word(said, ("jeans", "jean", "denim")):
        return ("Put them on with the shoes you will wear them with, turn the leg up inside out to "
                "the length you want - creasing the shoe, not puddling on it - and stitch 1cm from "
                "the fold. Trim the spare to 1.5cm, zigzag that raw edge and press it flat. To "
                "keep the faded original hem, cut the leg 3cm above it, pin that hem back on and "
                "stitch round twice: that is the trick that makes a shortened pair look factory.")
    if _any_word(said, ("curtain", "curtains", "drape", "drapes", "blind", "blinds",
                        "tablecloth", "tablecloths", "napkin", "napkins", "tea towel",
                        "tea towels")):
        return ("Hang them and let them drop for a few days before you cut: fabric stretches "
                "under its own weight, and a hem measured flat ends up too short. Then measure "
                "from the rail at three points across each panel, because floors and rails are "
                "rarely level: aim for 1cm below the sill for a sill-length pair, or 1cm above "
                "the floor for floor length. Turn up a double hem about 5cm deep, press it with "
                "a damp cloth, and use iron-on hemming tape if you would rather not sew - an "
                "even hem is what makes curtains look made, more than the stitches do.")
    return ("Try it on inside out and pin the hem where it should fall, then press and stitch "
            "round with a simple running stitch, just catching the fabric. Iron the fold first "
            "with a damp cloth, and a few dots of hemming tape hold it without any sewing. Keep "
            "the cut edge 1.5cm long and press the seam flat, and the hem sits as flat as a shop's.")


def _jeans_to_buy(memory, understood):
    """Where to look for a cheap pair, or how a pair should fit if no budget is named."""
    said = _the_line(understood)
    fit = ("the waist should sit snug with no gap at the back, the rise about an inch below your "
           "navel, and the hem break once on the shoe")
    if _any_word(said, ("cheap", "cheapest", "budget", "afford", "under", "quid", "price",
                        "brand", "brands", "who makes", "value", "money", "shop")):
        return ("Fit is what makes jeans look good, so spend your time on the cut rather than the "
                "label: " + fit + ". A shop's own brand at £25 to £45 in 98% cotton with a "
                "little elastane wears as well as a designer pair, so try one size either side "
                "of what you think you are, because the same size varies by inches between shops.")
    return ("Jeans are fitted by three numbers, so try a size either side of the one you think "
            "you are: " + fit + ". Look for 98% cotton with a little elastane, which holds its "
            "shape without clinging, and a leg that is long enough not to ride up when you sit.")


# A child who will not wear the thing is not a question about which one to buy. The refusal is the
# morning card's question (bot/knowledge/family.py), and every wording of it puts a refusing verb
# right beside the garment: wont wear, refuses to wear, wont put it on, fights getting dressed. The
# buying row declines on that shape rather than on a list of the phrases people use, because the
# phrases are endless and the shape is one.
A_CHILD_REFUSING_A_GARMENT = re.compile(
    r"\b(?:wont|won'?t|will not|refuses?|refusing|refused|hates?|hate wearing|fights?|fighting|"
    r"screams?|cries?)\b[^.?!;]{0,40}"
    r"\b(?:wear|wears|wearing|wore|put\b[^.?!;]{0,12}\bon|"
    r"get (?:it|them) on|dressed|dressing|dress)\b", re.I)


def not_a_fight_about_clothes(understood):
    """False when the line is a child fighting the clothes, so a buying row stands down.

    Public because bot/knowledge/family.py has the other two rows this shape reaches: the first
    shoes ("my toddler wont wear his shoes" is the morning fight, not the size of the next pair)
    and the sibling fight ("my son fights getting dressed" names one child and a wardrobe). The
    verb-beside-the-garment shape is one shape, so one test serves all three.
    """
    return not A_CHILD_REFUSING_A_GARMENT.search(_the_line(understood))


def _child_coat(memory, understood):
    """A coat for a child, with the car-seat warning first when the line mentions a car."""
    said = _the_line(understood)
    if _any_word(said, ("car seat", "carseat", "car", "pram", "pushchair", "buggy",
                        "stroller", "travel system")):
        return ("Never put a thick coat under a car-seat harness: the straps cannot tighten on "
                "it, and in a crash a child can slip out of a loose seat. Strap them in a thin "
                "fleece or jumper and put the coat on once they are out, or lay it over them, "
                "and warm the car before you set off. In a pram a pramsuit or a coat over a "
                "tucked-in blanket is warmer than a stiff coat they have to be folded into.")
    if _any_word(said, ("size", "sizing", "grow", "growing", "age", "year old", "fit")):
        return ("Buy the size that fits their height now rather than one to grow into: an "
                "oversized coat leaves a gap at the neck and wrists where the warmth goes, and "
                "the sleeves hang over their hands. Check there is room for a jumper underneath, "
                "that the hood stays up in wind, and that the cuffs and the hem can be adjusted.")
    return ("For a child, look for a hood that stays up, a waterproof outer, room for a jumper "
            "underneath and no cords round the neck; a size that fits now beats one to grow into. "
            "A baby in a pram is warmer in a pramsuit than in a coat they have to be folded "
            "into.")


# A coat that is already letting water in, in the words people use for it.
_COAT_FAULT = ("leak", "leaks", "leaking", "leaky", "wet through", "soaked", "soaking",
               "water gets in", "gets wet", "let water", "letting water", "no longer waterproof",
               "not waterproof", "damp inside", "lets the rain in", "lets water in",
               "keeps me dry", "wont keep the rain out", "beads", "beading", "reproof",
               "waterproofing", "waterproof my", "waterproof it", "re waterproof", "seams")
# How a person asks whether to buy one instead, which is the shopping row's question.
_COAT_BUYING = ("worth", "money", "buy", "buying", "price", "spend", "cheap", "expensive",
                "cost", "which", "best", "recommend", "choose", "new")


def _a_faulty_coat(understood):
    """True when the line is about a coat that has stopped keeping water out."""
    said = _the_line(understood)
    if _any_word(said, _COAT_FAULT):
        return True
    return not _any_word(said, _COAT_BUYING)


def _wash_temperature(memory, understood):
    """What the number on the dial is for, with the verdict on the number asked about first.

    "is 60 degrees too hot for a wash" wants the answer about 60 before the advice about 30, so
    the card leads with the temperature the line names. With no number in it, it leads with 30,
    which is the everyday setting and the thing most people are choosing between.
    """
    said = _conversation_so_far(memory)
    if any(word in said for word in _A_FAULTY_MACHINE):
        return ""
    line = _the_line(understood)
    # A heated towel rail is a radiator, and "my towel rail is cold at the top" is the bleeding
    # question: the towel in the line was enough to bring the wash-dial answer.
    if any(word in line for word in ("towel rail", "towel radiator", "heated towel rail",
                                     "ladder rail", "radiator", "radiators")):
        return ""
    if "90" in line or "95" in line:
        return ("90 is only for illness, nappies and bedding that has been through a bug: it "
                "shrinks cotton and fades colour, so nothing you want to keep should go in it. "
                "60 does towels, bedding, underwear, socks and anything greasy or stained, and "
                "30 or 40 covers shirts and jeans worn once.")
    if "60" in line:
        return ("60 is not too hot for towels, bedding, underwear, socks and anything greasy or "
                "stained - it is what those need, along with a full dose of detergent. Keep "
                "shirts and jeans worn once at 30 or 40, and save 90 for illness and nappies: "
                "heat is what shrinks and fades things.")
    # The line names the laundry it is about, and the everyday 30 is not the answer for bedding or
    # towels: those want 60, because that is the heat that kills dust mites. "what temperature
    # should i wash bed sheets at" and "what temperature for towels" were both told to treat 30 as
    # the everyday setting, which is the answer about shirts and jeans.
    if not any(number in line for number in ("30", "40", "60", "90", "95")) \
            and NEEDS_SIXTY.search(line):
        return ("60C for bedding, towels, underwear and socks: that is the heat that kills dust "
                "mites and the bacteria that make a towel smell, along with a full dose of "
                "detergent, and cotton bedding takes it well. Keep shirts, jeans and anything "
                "worn once at 30 or 40, and save 90 for illness and nappies.")
    return ("Treat 30C as the everyday setting: it is about 10p a load cheaper than 40C and gets "
            "shirts, jeans and normally-worn clothes just as clean, as long as the drum is not "
            "crammed and you use the full dose of detergent. Save 40 for heavy soiling, 60 for "
            "towels, bedding, underwear, socks and anything greasy or stained, and 90 only for "
            "illness or nappies.")



# A stain question's second turn often names only the substance ("its engine oil"), so the row
# above cannot ask for the stain words in the line itself: it asks the conversation instead.
_STAIN_SAID = ("stain", "stains", "stained", "mark", "marked", "spot", "spill", "spilt",
               "spilled", "splash", "splashed", "dripped", "got on", "got it out", "get it out",
               "get out of", "out of my", "off my", "off the", "remove", "came out", "washed")


def _engine_oil_stain(memory, understood):
    """The engine-oil stain answer, or nothing when the conversation is not about a stain."""
    said = " ".join(str((understood or {}).get(key) or "") for key in ("clean", "norm", "plain"))
    if not any(word in said for word in _STAIN_SAID):
        try:
            from ..memory import thread
            said = " ".join(text.lower() for text, _reading in thread.user_lines(memory))
        except Exception:  # noqa: BLE001 - no history only means no guard to read
            said = ""
    if not any(word in said for word in _STAIN_SAID):
        return None
    return ("Do not wash it first: water and detergent only push engine oil further in. Blot what "
            "will come off, work neat washing-up liquid into the mark with your fingers and leave "
            "it 15 minutes, then wash it on its own at the hottest the label allows. On a mark "
            "that has dried, a drop of white spirit or a motor-shop degreaser does the lifting "
            "first, rinsed out before it goes in the machine. Check it before the dryer, because "
            "heat sets it.")


# "How do I iron a shirt without an iron" is not a question about ironing technique: the iron is
# the one thing the person has said they have not got, so the answer is what to do instead. The
# row is only about that line, and it says so by reading the line itself rather than its words.
_NO_BOARD = re.compile(
    r"\bwithout\s+(?:an?\s+|the\s+|my\s+|any\s+)?(?:ironing\s+)?board\b|"
    r"\bno\s+(?:ironing\s+)?board\b|\b(?:dont|don't|do not)\s+have\s+an?\s+board\b", re.I)

_NO_IRON = re.compile(
    r"\bwithout\s+(?:an?\s+|the\s+|my\s+|any\s+)?iron\b|\bno\s+iron\b|"
    r"\b(?:dont|don't|do not)\s+have\s+an?\s+iron\b|\b(?:havent|haven't|have not)\s+got\s+an?\s+iron\b|"
    r"\biron\s+(?:is\s+)?(?:broke|broken|packed|in storage)\b", re.I)


def _no_iron_reply(memory, understood):
    """The crease answer for a line that says the iron is out of the picture, else nothing."""
    said = str((understood or {}).get("clean") or "")
    if not said:
        said = str((understood or {}).get("text") or "")
    if _NO_IRON.search(said):
        return _NO_IRON_TEXT
    if _NO_BOARD.search(said):
        return _NO_BOARD_TEXT
    return ""


_NO_IRON_TEXT = (
    "No iron needed: hang the shirt in the bathroom while you take a hot shower, or spritz it "
    "with water, smooth it flat with your hands and hang it somewhere warm. Ten minutes in a "
    "tumble dryer with a damp towel drops the creases too, and a damp collar pressed flat with "
    "your thumb and left to dry hangs right.")

# The same line with the board missing instead of the iron: the crease answer is still right, but
# what to press on is what they asked about.
_NO_BOARD_TEXT = (
    "A folded bath towel on a table is the board: lay the shirt flat on it, damp, and press with "
    "the iron, working in small sections and keeping the towel under the whole of the front. A "
    "clean cotton sheet over the table works too, and the collar and cuffs want pressing on the "
    "reverse first so they keep their shape.")


# "acne" is the cause card's word, and a bare acne line should keep the fuller answer. But a
# "face wash for acne" is a product the routine already names, and the cause card stands down on
# the choosing words ("best", "which"), so those lines were left with a search hedge. The guard
# lets the routine answer only when the line names something you wash or put on the skin; every
# other acne line still stands this row down for `science.acne-why`.
_ACNE_PRODUCT_WORDS = frozenset((
    "wash", "washes", "washing", "cleanser", "cleansers", "cream", "creams", "lotion",
    "moisturiser", "moisturizer", "serum", "toner", "sunscreen", "sunblock", "spf",
))


def _acne_product_question(understood):
    if not isinstance(understood, dict):
        return True
    words = {str(word).lower() for word in (understood.get("words") or ())}
    if "acne" not in words:
        return True
    return bool(words & _ACNE_PRODUCT_WORDS)
# A stain is named by the mark and by the thing it is on, and the thing is said in a hundred
# words. Each stain entry used to carry its own short list of garments, so the list decided which
# lines worked: "how do i get oil out of my jeans" and "how do i get grease out of my jeans" were
# the search hedge, because "jeans" was in the grass list and not in the grease one, while "how
# do i get oil out of a shirt" answered. The garments and the fabrics are one tuple now, and
# every stain uses it, so a new garment word fixes all of the stains at once.
GARMENT = ("shirt", "shirts", "t-shirt", "t-shirts", "tshirt", "tshirts", "top", "tops",
           "trouser", "trousers", "jeans", "denim", "chinos", "shorts", "skirt", "skirts",
           "dress", "dresses", "jumper", "jumpers", "cardigan", "hoodie", "sweatshirt",
           "fleece", "jacket", "jackets", "coat", "coats", "sleeve", "sleeves", "collar",
           "cuff", "cuffs", "clothes", "clothing", "uniform", "sock", "socks", "tights",
           "leggings", "towel", "towels", "sheet", "sheets", "bedsheet", "bedsheets",
           "bedding", "duvet", "duvet cover", "pillow", "pillowcase", "tablecloth",
           "curtain", "curtains", "nappy", "nappies", "bib", "soft toy", "teddy", "bag",
           "rucksack", "backpack")
# A mattress, a carpet and a sofa are not garments: "rinse it in cold water, then wash as
# normal" is advice nobody can follow on one, and a carpet, a sofa and a mattress each have an
# answer of their own. The stain rows stand down for them.
NOT_A_GARMENT_SURFACE = ("mattress", "carpet", "rug", "couch", "cushion", "upholstery",
                         "drive", "driveway", "concrete", "paving", "patio", "path", "paths",
                         "floor", "floors", "grout", "worktop", "worktops", "hob", "sink",
                         "hand", "hands", "skin", "garage", "deck", "decking", "wall", "walls",
                         "window", "windows", "wood", "wooden", "phone", "laptop", "tablet",
                         "keyboard", "screen", "screens", "monitor", "tv", "television",
                         "mirror", "spectacles", "shoe", "shoes", "boot", "boots", "trainer",
                         "trainers", "board", "chopping board", "mat",
                         # A sofa has no wash label and cannot go in a machine, and it is the
                         # word people use: "couch", "cushion" and "upholstery" were fenced and
                         # "how do i get grease out of my sofa" was still told to wash at the
                         # hottest temperature the label allows. Main has a sofa answer of its own.
                         "sofa", "sofas", "settee", "settees", "armchair", "armchairs")
# Wallpaper is deliberately not in that list: a mark on papered wall is cleaned with the same
# washing-up liquid as a mark on cotton, and main's own answer for "grease marks off wallpaper"
# is the grease card, not the stripper. Fencing it sent the line to the wallpaper steamer."

# "out of", "off" and "on" are how a stain is asked about: "how do i get oil out of my jeans"
# names the mark and the garment and no verb of its own.
STAIN_ASKS = ("stain", "stains", "stained", "mark", "marks", "marked", "remove", "get out",
              "got out", "get it out", "come out", "came out", "out of", "off my", "on my",
              "spilt", "spilled", "dropped", "ruined", "clean")


# The words that say the whole garment has gone sour, and the words that say the complaint is a
# mark rather than a smell. They are read as whole words: "deodorant" contains "odor", so a
# substring test put every deodorant question in the whole-garment branch, and "how do i get
# deodorant marks off a black top" was told to wash it at 40C with biological powder when the
# marks lift off dry.
_A_SMELL_ON_THE_GARMENT = frozenset("""smell smells smelt smelling smelly stink stinks stinking
    stank odour odor reeks reek sweaty sour damp mildew musty""".split())
_A_KIT_GARMENT = frozenset("""gym workout sport sports football running run runs running cycle
    cycling kit trainer trainers vest shorts socks leggings""".split())
_A_MARK_NOT_A_STAIN = frozenset("""mark marks marked marking streak streaks streaky powdery
    powder flakes flaky""".split())
# The white mark on a dark top is antiperspirant, and the line says so: sweat on its own leaves a
# yellow stain in the armpit, which is the paste's job.
_ANTIPERSPIRANT = frozenset("""deodorant deodorants antiperspirant antiperspirants rollon
    roll-on""".split())


def _sweat_mark(memory, reading):
    """The armpit stain, the whole garment that has gone sour, or the deodorant mark - three jobs.

    "How do I get sweat smell out of gym clothes" wants the wash that takes the smell out of the
    fabric; "how do i get sweat stains out of a white shirt" wants the paste on the armpits. The
    same entry answered both with the paste, which does nothing for a top that smells after one
    wear, so the words that name the smell or the kit get the version for the whole garment.

    A white mark on a dark top is neither: it is antiperspirant sitting on the fibres and it rubs
    off dry, so washing it is work for nothing. "how do i get deodorant marks off a black top" and
    "white marks on my black dress from deodorant" are that line.
    """
    reading = reading or {}
    said = {str(word).lower() for word in (reading.get("words") or [])}
    clean = str(reading.get("clean") or "").lower()
    if said & _A_MARK_NOT_A_STAIN and said & _ANTIPERSPIRANT \
            and not said & _A_SMELL_ON_THE_GARMENT:
        return ("Deodorant marks on a dark top are the antiperspirant sitting on the fibres, not a "
                "stain: rub the fabric against itself, or run a dry cloth or a pair of tights over "
                "it, and they lift off without washing. Let the deodorant dry properly before you "
                "dress and the marks stop appearing.")
    if said & _A_SMELL_ON_THE_GARMENT or said & _A_KIT_GARMENT or "work out" in clean \
            or "sports kit" in clean:
        return ("Wash it at 40C with a biological detergent and no fabric softener, which coats the "
                "fibres and traps the smell, and use the extra-rinse setting: the bacteria that "
                "make old sweat smell live in the fibres and survive a cool wash. Leave it to dry "
                "in the air rather than in a heap, and never put a sweaty kit back in the bag. A "
                "splash of white vinegar in the softener drawer instead of conditioner shifts the "
                "last of it.")
    return ("Soak the armpits in a paste of bicarbonate of soda and water with a squeeze of lemon "
            "for an hour, or use oxygen bleach on white shirts. Wash at 40C and don't iron over "
            "the stain until it's gone.")

# ...but a tattoo that is peeling and red, hot or weeping is not a healing tattoo, and neither of
# the two tattoo cards may call the skin coming off the ordinary thing while an infection sign is
# in the same line. Those lines keep the wound and reaction answers.
_TATTOO_INFECTION_AVOID = ("red", "redder", "redness", "hot", "warm", "spreading", "spreads",
                           "weeping", "oozing", "ooze", "pus", "bumpy", "lumpy", "swollen",
                           "swelling", "itch", "itches", "itchy", "itching", "smell", "smelly",
                           "fever", "infected", "infection", "crusty", "crusting", "sore",
                           "painful")

# What makes a drying line a washing line rather than a building that wants drying out.
LAUNDRY_WORDS = ("washing", "laundry", "clothes", "clothing", "shirt", "shirts", "t shirt",
                 "tshirt", "jeans", "towel", "towels", "sheet", "sheets", "bedding", "duvet",
                 "load", "socks", "jumper", "jumpers", "trousers", "uniform", "nappy",
                 "nappies", "workwear", "gym kit", "scrubs")
BUILDING_WORDS = ("room", "rooms", "house", "home", "flat", "wall", "walls", "ceiling",
                  "ceilings", "floor", "floors", "building", "bedroom", "kitchen", "bathroom",
                  "cellar", "basement", "hallway", "landing", "conservatory", "garage",
                  # a garden that dries out is not a load of washing: "my raised bed soil is dry"
                  # was hung on a rack in the warmest room with a window cracked open
                  "soil", "garden", "gardens", "compost", "plant", "plants", "raise bed",
                  "raised bed", "raised beds", "flower bed", "flower beds", "beds", "border",
                  "borders", "lawn", "allotment", "greenhouse", "seed tray", "seed trays",
                  "veg patch", "vegetable patch", "pot", "pots", "planter", "planters",
                  "hanging basket", "hanging baskets", "window box", "window boxes")


def _drying_the_washing(understood):
    """Whether a line about drying something is about the washing, not the building."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in text for word in LAUNDRY_WORDS):
        return True
    return not any(word in text for word in BUILDING_WORDS)

# A load of washing, a towel, a wool jumper and a waterproof coat all leave the same hole on a
# line that says "dry": the machine card answers how to wash them, and the drying card had only
# the words of a washing line. The item is what changes the advice, so the reply reads it off the
# line and gives the branch that fits: hanging soaks a heavy jumper out of shape, and a radiator
# is the one place a waterproof coat must not go.
_DRY_FLAT_WORDS = ("wool", "woollen", "woolen", "jumper", "jumpers", "cardigan", "cardigans",
                   "knitwear", "knitted", "knit", "merino", "cashmere", "lambswool", "sweater",
                   "sweaters")
_DRY_HANGER_WORDS = ("coat", "coats", "jacket", "jackets", "waterproof", "waterproofs",
                     "gore tex", "goretex", "raincoat", "raincoats", "parka", "ski jacket",
                     "fleece", "fleeces", "softshell", "shell")
_DRY_FLUFFY_WORDS = ("towel", "towels", "bedding", "duvet", "duvets", "sheets", "sheet",
                     "pillowcase", "pillowcases", "blanket", "blankets", "bathmat", "bath mat")


_DRY_DOWN_WORDS = ("puffer", "puffa", "gilet", "gilets", "down jacket", "down coat",
                   "down gilet", "down sleeping bag", "down bag", "feather jacket")


# The dryer is a machine, and a machine that is not drying the load is a fault rather than a drying
# job: this row holds "dryer" in its key and answered "the tumble dryer leaves everything damp" with
# "Hang the washing on a rack in the warmest room", which is advice for somebody who has no dryer.
# The fault answer is written once, in home.py beside every other appliance fault, and read here.
_A_DRYER = ("tumble dryer", "tumble drier", "washer dryer", "washer drier", "washer-dryer", "dryer",
            "drier", "tumbler")


def _the_dryer_at_fault(reading_said):
    """Whether the line is a dryer of the person's own that is not drying the load."""
    if not any(name in reading_said for name in _A_DRYER):
        return False
    if "hair dryer" in reading_said or "hairdryer" in reading_said:
        return False
    return any(phrase in reading_said for phrase in A_JOB_LEFT_UNDONE)


def _drying_it(memory, understood):
    """How to dry the thing the line names, from the one drying card."""
    words = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if _the_dryer_at_fault(words):
        from .home import _dryer_heat
        return _dryer_heat(memory, understood)
    # A down jacket is the one coat that must not drip dry: hanging it wet leaves the down in
    # clumps that never loft again, so the coat branch below is the wrong advice for it. The bare
    # word "down" is not enough on its own ("dry my coat down"), so a down word, or "down" beside
    # the thing it fills, is what asks for this branch.
    named_down = (any(word in words for word in _DRY_DOWN_WORDS)
                  or ("down" in words.split()
                      and any(word in words for word in ("jacket", "coat", "gilet", "bag"))))
    if named_down:
        return ("Tumble a down jacket on low with two or three dryer balls and stop every twenty "
                "minutes to pull the clumps apart, until it is completely dry - hanging it wet "
                "leaves the down in lumps that never loft again. If it is dirty, wash it first on "
                "its own with a down wash and no fabric conditioner.")
    # a wool coat is a coat first: the flat rule is for a jumper that would stretch on a hanger
    if any(word in words for word in _DRY_HANGER_WORDS):
        return ("Hang it on a wide hanger somewhere airy with the pockets empty and the hood "
                "out, and let it drip dry. Keep a waterproof away from a radiator and a tumble "
                "dryer, because the heat softens the coating that keeps the rain out.")
    if any(word in words for word in _DRY_FLAT_WORDS):
        return ("Dry wool flat, never on a hanger: press the water out in a towel, reshape it on a "
                "dry towel or a mesh rack and leave it somewhere airy, away from a radiator. "
                "Hanging it wet is what stretches a jumper out of shape.")
    if any(word in words for word in _DRY_FLUFFY_WORDS):
        return ("Shake it out, then hang it with space on both sides - a towel or a duvet bunched "
                "up stays damp in the middle. Finish it in a tumble dryer on low if you have one, "
                "and do not fold it away until it is dry to the touch, or it comes out musty.")
    return ("Hang the washing on a rack in the warmest room with a window cracked open, spaced out "
            "so air moves round it, and turn thicker things after a few hours. A dehumidifier "
            "dries a full load overnight indoors and stops the damp smell.")


# One answer, two ways in: a scorch names the iron and belongs to iron-scorch, a shine usually
# does not and belongs to garment-shine. Keeping the words in one constant means a change to the
# advice lands on both.
SHINE_OR_SCORCH_TEXT = (
    "A shine or scorch is flattened or slightly burnt fibre: sponge it with white vinegar, "
    "cover it with a pressing cloth and press it dry. A deep brown burn can't be undone, but "
    "a mild shine usually fades after a wash.")

_HAIR_HOME_TAIL = (
    " Do the 48-hour patch test, then work on dry, unwashed hair in sections: roots first, and "
    "pull the colour through the ends for the last ten minutes only, so they are not done twice. "
    "Time it by the box rather than by eye, rinse in cool water until it runs clear, then "
    "condition. Wash it less often and cooler with a colour-safe shampoo to keep the shade from "
    "fading.")
_HAIR_HOME_LIGHTER = (
    "A box dye only lifts colour a shade or two, so pick a shade within two of your own or it goes "
    "brassy, and anything lighter needs bleach.")
_HAIR_HOME_DARKER = (
    "Going darker is the forgiving direction: a box dye adds colour rather than lifting it, so it "
    "covers grey and can go several shades at once - the risk is a flat, matte result rather than "
    "a shade that will not take.")
# The length of time the dye stays on, for the person asking how long rather than which shade:
# the card opened on choosing a shade and buried the minutes in a later sentence.
_HAIR_HOME_LENGTH = (
    "Go by the box: most permanent dyes want 20 to 30 minutes and a semi-permanent 10 to 20, and "
    "the roots go on first with the colour pulled through the ends for the last ten minutes only, "
    "so they are not done twice. Do the 48-hour patch test first, rinse in cool water until it runs "
    "clear, then condition.")
_HAIR_HOME_DARK_WORDS = ("black", "darker", "dark", "brown", "brunette", "chocolate", "espresso",
                         "deep", "navy", "auburn", "mahogany", "chestnut")
_HAIR_HOME_GREY = (
    "Yes - a permanent dye covers grey completely, and it is the one job a box does as well as a "
    "salon. Pick a shade one lighter than you want, because grey takes colour cooler and darker "
    "than the swatch, and use a permanent rather than a semi if you want the grey gone rather than "
    "blended for a few washes.")


# A cut and a colour are two different fixes, and the answer has to lead with the one they said.
# "i got a bad haircut" wants the trim, the growing out and the free correction; "my hair dye went
# wrong" wants a colourist and a toner, and leading with "it will grow out" for the colour is a
# fluent answer to the wrong half of the complaint.
_BAD_COLOUR_WORDS = ("dye", "dyed", "dyeing", "colour", "color", "bleach", "bleached",
                     "highlights", "toner", "patchy", "brassy", "orange", "went green",
                     "turned green", "too dark", "went too dark", "came out too dark")

_THE_BAD_CUT = (
    "It will grow out: a bad cut stops being noticeable in two to three weeks, and until then it "
    "needs one small, even trim rather than a rescue at home. Go back within a week and say plainly "
    "which part you do not like - most salons and barbers put a cut right for free, and you can ask "
    "for a different stylist. A fringe that went too short is three weeks of wearing it to the side "
    "with a pin. Take a photo today, because that is what a refund or a free correction rests on if "
    "they will not have it back.")

_THE_BAD_COLOUR = (
    "That one is fixable at a salon rather than at home: a colourist can tone a patchy, brassy or "
    "too-dark result in ten to twenty minutes, usually £20 to £40, and a toner adds no damage the "
    "way another box dye does. Go back within a week and say what you do not like, because most "
    "salons correct their own colour free. If it was a box dye at home, give it three weeks: it "
    "fades, and a clarifying shampoo speeds that up. Do not put a lightener over an orange or "
    "patchy result yourself - that is how a cheap fix turns into a salon correction.")


def _the_bad_haircut(memory, understood):
    """The cut answer or the colour answer, whichever they complained about."""
    if _any_word(_the_line(understood), _BAD_COLOUR_WORDS):
        return _THE_BAD_COLOUR
    return _THE_BAD_CUT


def _hair_colour_home(memory, understood):
    """How to dye at home, where darker and lighter are not the same warning.

    "pick a shade within two of your own" is the right first sentence for going lighter and the
    wrong one for `how do i dye my hair black`, which is going the other way and cannot go
    brassy. The rest of the card is the same advice, so only the opening sentence changes.
    """
    said = _the_line(understood)
    # A how-long is the dye's own clock, not the shade to pick: "how long should i leave a hair
    # dye on". "How long does a box dye last" is the bottle's shelf life, so "last" stays out.
    if ("how long" in said or "how many minutes" in said or "leave it on" in said
            or "leave on for" in said):
        if not _any_word(said, ("last", "lasts", "keep", "keeps", "shelf", "expire", "go off")):
            return _HAIR_HOME_LENGTH
    if _any_word(said, ("grey", "gray", "greys", "grays", "white hair", "going grey")):
        return _HAIR_HOME_GREY + _HAIR_HOME_TAIL
    if (_any_word(said, _HAIR_HOME_DARK_WORDS)
            and not _any_word(said, ("lighter", "blonde", "blond", "bleach", "lift"))):
        return _HAIR_HOME_DARKER + _HAIR_HOME_TAIL
    return _HAIR_HOME_LIGHTER + _HAIR_HOME_TAIL


# The words of this table a bag, a drawer or a cupboard is: a thing kept in one is the subject of
# the line, and when that thing is food the mould on it is not mould on cloth.
KEPT_IN = ("bag", "bags", "handbag", "handbags", "drawer", "drawers", "cupboard", "cupboards")


def _the_mould_is_not_on_a_kept_food(understood):
    """Whether the mould in the line is on something a bag or a drawer holds, not on cloth."""
    return not (a_food_is_being_kept(understood)
                and only_a_container(understood, KEPT_IN + ("leather", "suede", "fabric")))

_LEATHER_PEELING = ("peeling", "peeled", "flaking", "flake", "flaked", "cracking", "cracked",
                    "cracks", "coming off", "worn through", "worn away", "worn off")


def _leather_mark(memory, reading):
    """A scuff is cream and a cloth; leather that is peeling has lost the finish itself."""
    line = str((reading or {}).get("clean") or (reading or {}).get("text") or "").lower()
    if any(word in line for word in _LEATHER_PEELING):
        return ("Peeling or flaking leather is the finish itself lifting, and no cream or polish "
                "brings it back: a leather repair kit with a filler and a colour matched to the "
                "piece hides a small patch, and a whole panel that is going means a re-cover. On "
                "bonded leather, which is a coating on a fibre backing, once it starts to peel it "
                "keeps going, because the layers are separating.")
    return ("A light scuff on finished leather usually lifts with a little leather conditioner or "
            "a matching leather cream worked in with a cloth, in circles, then buffed with a dry "
            "one; a scratch that has gone grey wants a leather dye or a colour-matched pen from a "
            "furniture shop. Keep the piece out of direct sun and away from radiators, because "
            "heat is what makes the finish crack.")

# A fat that has landed on a person is a scald, not a mark on a garment: "hot fat splashed on my
# arm" was told how to lift the grease mark with washing-up liquid and to wash it at the hottest
# temperature the label allows. The body part and a splash word together say the line is first aid,
# and health.py's scald row is the twenty minutes of cool water.
_A_BODY_PART = re.compile(
    r"\b(?:arm|arms|hand|hands|finger|fingers|thumb|thumbs|foot|feet|toe|toes|wrist|wrists|"
    r"leg|legs|chest|tummy|stomach|belly|lap|neck|shoulder|shoulders|eye|eyes|face|skin)\b")
_ONTO_A_PERSON = ("splashed", "splashes", "splash", "spat", "spits", "spitting", "spit",
                  "flicked", "jumped out", "pops", "popped", "scalded", "burnt my", "burned my",
                  "burnt me", "burned me")


def _grease_is_not_a_burn(understood):
    """False when the fat landed on a person, which is a scald and not a stain."""
    understood = understood if isinstance(understood, dict) else {}
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    if not _A_BODY_PART.search(text):
        return True
    return not any(word in text for word in _ONTO_A_PERSON)


# A height said in feet is not the feet. "im 5 foot 2 and i need trousers for work, what do i
# look for" was answered by the standing-all-day card on main `256b47bd`: the row keys "foot" and
# "for work", and a measurement in the same line made it look like a shift on the feet. The test
# is not the measurement alone, though - "5ft 2 and standing all day at work kills my feet" is a
# day on the feet with a height in it - so the row stands down only when the line measures
# somebody and nothing else in it is about the feet, a shift or a shoe.
_A_HEIGHT = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|1|2|3|4|5|6|7|8|9)"
    r"\s*(?:foot|feet|ft|')\b"
    r"|\b\d+\s*(?:foot|feet|ft)\b"
    r"|\b(?:foot|feet)\s+tall\b"
    r"|\bfeet\s+and\s+(?:a\s+half|inches)\b")

# The words that make a line about a day on the feet rather than about a measurement: a complaint
# in the feet, a shift, or a shoe. They keep the row even when the height is in the line.
_ON_THE_FEET = re.compile(
    r"\b(?:on (?:my|her|his|their|our) feet|standing|stand|stood"
    r"|feet (?:hurt|ache|are killing|are sore|are tired|are swollen)"
    r"|foot (?:hurts|aches)|sore feet|aching feet|killing me|blister|blisters"
    r"|shoes?|trainers?|boots?|insoles?|mat)\b")


# "what should i wear to a wedding" already has a card - the white-and-cream one, which is a
# neighbour's contract (`tests/test_a_wedding_outfit_is_not_a_hotel.py`), and a named code has its
# own card too. So the outfit-shortage row keeps only the line that says it has nothing to put on,
# or asks for ideas; every other what-shall-i-wear line stays with the card that already answers it.
_A_WEDDING_SHORTAGE = re.compile(
    r"\b(?:nothing (?:to wear|that fits|at all to wear|in my wardrobe|i can wear)"
    r"|no (?:outfit|idea what to wear)"
    r"|haven'?t got (?:anything|a thing|an outfit|nothing)"
    r"|don'?t have (?:anything|an outfit|a thing)"
    r"|need (?:something|an outfit|a suit|a dress)"
    r"|any ideas|ideas|suggestions|suggest|help)\b")

# A code the line names has its own answer (black tie, morning dress), and so does a single
# garment or accessory asked about by name. The shortage row stands down for those.
_A_NAMED_DRESS_CODE = re.compile(
    r"\b(?:black tie|white tie|morning dress|lounge suit|bow tie|dress code|cocktail|smart casual"
    r"|colour|color|jumpsuit|hat|shoes?|tie)\b")


def _an_outfit_shortage(understood):
    """True to keep the wedding-outfit row: the line has nothing to wear or asks for ideas."""
    text = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text", "raw", "rewritten", "plain"))
    words = (understood or {}).get("words") or ()
    text = (text + " " + " ".join(str(word) for word in words)).lower()
    if _A_NAMED_DRESS_CODE.search(text):
        return False
    return bool(_A_WEDDING_SHORTAGE.search(text))


# A garment that no longer fits is not a garment that needs ironing, and the ironing row keys
# "clothes" and "none" - so "none of my jeans fit me now" and "none of my clothes fit after a
# year off" were both sent to the no-iron card. The size words are what tell them apart.
_A_FIT_OR_A_SIZE = re.compile(r"\b(?:fits?|fitting|tight(?:er)?|loose[rd]?|baggy|sizes?|"
                              r"smaller|bigger|slimmer|heavier)\b")


def _the_line_is_not_about_fit(understood):
    """True to keep the ironing row: the line is about creases, not about a size."""
    text = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text", "raw", "rewritten", "plain"))
    words = (understood or {}).get("words") or ()
    text = (text + " " + " ".join(str(word) for word in words)).lower()
    return not _A_FIT_OR_A_SIZE.search(text)


# Weight that comes off without trying is one of the few lines in a chat like this worth a
# check, and the wardrobe answer is the wrong place to tell somebody to buy two pairs of
# trousers. "i lost weight and none of my clothes fit" was this row's, and the health card
# ("weight that comes off by itself shouldn't be ignored") said it better, so the check goes
# first in front of the advice rather than the row standing down: somebody whose clothes no
# longer fit still needs to know what to buy once they have been checked.
_A_WEIGHT_COMING_OFF = re.compile(
    r"\b(?:lost|losing|lose|shed|dropped|dropping)\s+"
    r"(?:a\s+|an\s+|some\s+|loads\s+of\s+|lots\s+of\s+)?"
    r"(?:lot\s+of\s+|bit\s+of\s+|few\s+|little\s+)?"
    r"(?:weight|stones?|pounds?|lbs?|kilos?|kg)\b"
    r"|\bweight\s+(?:loss|lost|off|coming off|coming down|dropped|falling|gone)\b"
    r"|\bslimmed down\b|\bdown\s+(?:a\s+)?(?:stone|dress size|size or two)\b")


_A_WARDROBE_ADVICE = (
    "Buy the size you are now, not the one you were: two pairs of trousers and three tops that "
    "fit at the shoulder and the waist cover most of a week, and a straight cut or a little "
    "stretch forgives more than a fitted one. Measure yourself once with a tape over what you "
    "wear underneath and buy to those numbers, because the label varies by shop by as much as "
    "two inches - try the two nearest sizes and keep the one that sits right. Restock one thing "
    "at a time, in colours that go with what you already have, and don't buy a whole wardrobe "
    "until your weight has been steady for a couple of months.")


def _the_size_you_are(memory, understood):
    """The restocking advice, with the weight check in front when the weight came off alone."""
    said = _the_line(understood)
    if _A_WEIGHT_COMING_OFF.search(" " + said + " "):
        return ("If the weight came off without you trying, get it checked first: that is worth "
                "one appointment, and weight that comes off by itself shouldn't be ignored. "
                "Then, when you restock, " + _A_WARDROBE_ADVICE[0].lower()
                + _A_WARDROBE_ADVICE[1:])
    return _A_WARDROBE_ADVICE


def _the_feet_are_not_a_height(understood):
    """True to keep a feet row: the line is not just measuring somebody."""
    text = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text", "raw", "rewritten", "plain"))
    words = (understood or {}).get("words") or ()
    text = (text + " " + " ".join(str(word) for word in words)).lower()
    if not _A_HEIGHT.search(text):
        return True
    return bool(_ON_THE_FEET.search(text))


ENTRIES = [
    # --- things that shrank, stretched or went wrong in the wash -----------------
    entry("shrink-wool", (("wool", "woollen", "jumper", "sweater", "cardigan", "knitwear"),
                          # the ask is often "how do i unshrink" rather than "it shrank", and
                          # "unshrink" is not the word "shrink" with a prefix the matcher sees:
                          # "how do i unshrink a wool jumper" was read as a craft to start and
                          # answered with cast-on stitches. The undo words are said here.
                          ("shrink", "shrank", "shrunk", "shrunken", "shrinking", "small",
                           "unshrink", "un shrink", "unshrunken", "unstretch", "un stretch",
                           "stretch back", "back to shape", "back to size", "too small now",
                           "dryer", "tumble")),
          ("Soak it in lukewarm water with a capful of wool wash or hair conditioner for 10 "
           "minutes, press the water out in a towel, then lay it flat and stretch it gently back "
           "to shape, pinning the edges. Wool often comes back a size; never tumble dry it again.",
           "Fill the sink with lukewarm water and a little conditioner, soak the jumper for ten "
           "minutes and stretch it back to shape while it's wet, then dry it flat, pinned at the "
           "edges. It won't always be perfect, but wool usually gives back most of the size."),
          # "wool" is a craft word too, and "how do i unshrink a wool jumper" was read as a jumper
          # to knit. The size question is the more specific one, so it wins the tie.
          bias=1),
    # Washing jeans so they come in is this entry's job. Stopping them going in, and stretching a
    # pair out again, are the two opposite questions either side of it: cleaning.py's
    # clothes-shrinking answers the first and shrunk-clothes the second. The two were getting this
    # answer - "how do i stop my jeans shrinking in the wash" was told to wash them hot - so the
    # asking phrases are kept out here rather than the words jeans and denim.
    entry("shrink-jeans", (("jeans", "denim"),
                           ("shrink", "shrank", "shrunk", "shrunken", "big", "loose",
                            "tighter", "stretched", "baggy")),
          ("Wash them in the hottest water the label allows and tumble dry on hot: denim tightens "
           "for a while, and a long hot soak shifts a pair that is much too loose. It relaxes "
           "again as you wear it, so a belt or taking them in at the waist is what keeps them "
           "fitting.",
           "A hot wash and a hot tumble dryer take denim in a little and it holds for a few "
           "wears; a long soak in hot water does more. For a fit that stays, a tailor taking in "
           "the waist costs about £20."),
          # The prevention question ("how do i keep my jeans from shrinking") stays out. Spelling it
          # as "shrinking" will not do - lookup reads "shrinking" as the same word as "shrink", so
          # it would also turn away "how do i shrink my jeans" - hence the longer phrases. A bare
          # "stop" is out too: "how do i stop my jeans looking baggy" is this entry's job.
          avoid=("from shrinking", "jeans shrinking", "them shrinking", "it shrinking",
                 "without shrinking", "keeps shrinking", "keep shrinking", "stop shrinking",
                 "prevent shrinking", "avoid shrinking", "no shrinking", "don't shrink",
                 "dont shrink", "doesn't shrink", "stretch out",
                 "stretch them", "stretch it", "loosen", "too tight",
                 # The complaint keeps this row off ("my jeans are a bit tight" is the stretch
                 # row) but the *request* must not be fenced with it: "how do i make my jeans a
                 # bit tighter" is a pair to shrink, and the bare phrase "bit tight" was
                 # screening it out as if it were the complaint.
                 "are a bit tight", "is a bit tight", "feel a bit tight", "a bit too tight",
                 "bit snug", "slightly tight", "getting tight", "are getting tight",
                 "it shrink", "them shrink", "came out small", "shrank in the wash",
                 # a pair that came out tighter is the stretch-it-back question, the other side
                 "feel tighter", "tighter than", "tighter after", "are tighter", "is tighter",
                 "got tighter", "tighter now",
                 # the other direction: a pair to be stretched out is the row below
                 "stretch my", "stretch the", "stretch a", "stretch jeans", "how do i stretch",
                 "how to stretch", "stretched out", "give a bit", "give a little"),
          # A pair the person wants tighter is asked in the same words as a pair that came out
          # tighter ("make my jeans tighter" against "my jeans feel tighter"), and the request
          # belongs here: this row wins the tie, and its own avoid list is what keeps the
          # complaint on the stretch row below.
          bias=2),
    # A pair that is too tight is not a pair that shrank: denim gives a little with wear, and a
    # tailor can let the waist out. "how do i stretch my jeans" was answered with the hot-wash
    # shrink method - the exact opposite - and "my jeans are too tight" with a wool jumper's
    # conditioner soak.
    entry("stretch-jeans", (("jeans", "denim"),
                            ("stretch", "stretching", "stretched", "tight", "tighter", "snug",
                             "squeeze", "squeezes", "pinch", "pinches", "uncomfortable",
                             "so tight", "cant do them up", "can't do them up",
                             # the phrase a person actually types, and it carries more weight
                             # than the bare "tight" that the row already had
                             "too tight", "bit tight", "a bit tight", "too snug",
                             "stretch out", "stretch them", "stretch it")),
          ("Denim gives a little rather than stretching: wear them damp for an hour and the waist "
           "and knees relax by a centimetre or so, and a tailor can let the waist seam out by "
           "about 2cm if there is fabric inside it. If it is the thighs that are tight, buy the "
           "size that fits them and have the waist taken in instead - a tight pair never becomes "
           "a comfortable one by force.",
           "Denim loosens with body heat and time, so a pair that is snug on the first wear is "
           "usually right: wear them an hour and they give at the waist and knee. Do not tumble "
           "dry a tight pair - that is what takes them in again."),
          # deliberately making a pair smaller is shrink-jeans, and a pair already ruined by a
          # wash is cleaning.py's clothes-shrinking; a pair to be chosen is the buying row.
          avoid=("shrunk", "shrank", "shrink", "shrinking", "came out small", "smaller",
                 "in the wash", "wash", "washing", "dryer", "tumbled", "tumble",
                 "should i buy", "which jeans", "what jeans", "brand", "brands", "cheap",
                 "size up", "next size", "a size",
                 # A pair *asked* to come in is shrink-jeans' job, and "tighter" in the key above
                 # was taking it: "how do i make my jeans tighter" got told how denim gives,
                 # which is the opposite of the question. The complaint ("too tight", "are
                 # tighter") is still this row's; the request to make them tighter is not.
                 "make them tighter", "make it tighter", "make mine tighter",
                 "make my jeans tighter", "make jeans tighter", "make a pair tighter",
                 "make them smaller", "make my jeans smaller", "get them tighter",
                 "get my jeans tighter", "tighter again"),
          # cleaning.py's clothes-shrinking keys "too tight" as a phrase and comes earlier in
          # the arbiter's order, so it kept "my jeans are too tight" for its conditioner soak.
          # A snug pair of jeans is this row's question.
          bias=2),
    entry("stain-drink", (("coffee", "tea", "milk", "juice", "cola", "coke", "pepsi",
                           "lemonade", "fanta", "sprite", "squash", "beer", "lager",
                           "cider", "milkshake", "smoothie", "hot chocolate"),
                          ("shirt", "shirts", "top", "t shirt", "tshirt", "blouse", "dress",
                           "trousers", "jeans", "skirt", "sleeve", "cuff", "collar", "cloth",
                           "tablecloth", "cushion", "napkin", "apron", "jumper", "sweater",
                           "cardigan", "fabric", "uniform", "white", "towel", "bedsheet",
                           "sheets", "duvet cover", "pillowcase")),
          ("Blot it at once, don't rub, then run cold water through the back of the fabric so the "
           "mark comes out the way it went in. Work in a drop of washing-up liquid with your "
           "fingers, leave it five minutes and rinse. If it has dried in, soak it in oxygen bleach "
           "(whites and colourfast things only) and wash it at the hottest the label allows. No "
           "iron or tumble dryer until the mark has gone, because heat sets it.",
           "Cold water through the back of the fabric and blot, don't rub. A drop of washing-up "
           "liquid, five minutes, then rinse. Still there once dry: oxygen bleach, then the "
           "hottest wash the label allows. No heat until it has gone."),
          # red wine has its own entry, and a drink on a sofa or carpet is cleaning.py's
          avoid=("red wine", "wine", "sofa", "couch", "carpet", "rug", "upholstery",
                 "mattress", "sink", "toilet", "wood", "worktop", "buying", "buy",
                 "drink more", "cut down", "less coffee", "caffeine", "make better",
                 "bitter", "sour", "brewing", "mug", "cup", "kettle", "machine")),
    entry("stain-red-wine", (("red wine", "wine"),
                             ("shirt", "shirts", "top", "blouse", "dress", "jeans", "denim",
                              "trousers", "clothes", "sweater")),
          ("Blot it at once with kitchen paper, then stretch the fabric over a bowl and pour "
           "boiling water through it from a height; that shifts most red wine from cotton. For a "
           "delicate or dry-clean-only piece use cold water and a little washing-up liquid and "
           "take it to a dry cleaner the same week.",
           "Cold water first, straight away, and blot rather than rub. If the mark is still there "
           "when it has dried, a soak in oxygen bleach usually lifts it, and a dry cleaner can "
           "still save a delicate fabric if you get it there quickly.")),
    entry("faded-black", (("black", "dark clothes", "black jeans", "black shirt", "jeans",
                           "denim"),
                          ("fade", "fading", "faded", "grey", "gray", "wash", "washing")),
          "Wash dark things inside out, in cold water, on a short cycle, and skip the dryer. Cold "
          "and quick is what keeps black from going grey, and washing every few wears is kinder "
          "than every wear."),
    entry("white-dull", (("white clothes", "whites", "white shirts", "white wash", "white towels",
                          "white socks", "white t-shirts",
                          # a named shirt that has greyed is the same question: "my school shirt
                          # has gone grey" used to reach the composer's "thanks for telling me".
                          # Phrases, not the bare word: a plain "how do i wash my shirt" says
                          # nothing about white, and must not get oxygen bleach.
                          "school shirt", "school shirts", "shirt collar", "white shirt",
                          "white t shirt", "white top", "white tops",
                          # "how do i stop my washing from going grey" and "my washing goes grey"
                          # name no white thing, so the whites wash never saw them and they fell
                          # to the search shrug, though the answer is the same oxygen bleach and
                          # daylight. The phrase needs the wash word: a bare "gone grey" in the
                          # key reads every grey thing as a white one, and "my black top has gone
                          # grey" came here for the hottest wash and bleach instead of the dark
                          # wash it already had. A colour is what the garment is, not what it
                          # needs - only the wash word below says the whites answer is the one.
                          "washing gone grey", "washing going grey", "washing goes grey",
                          "washing went grey", "washing has gone grey",
                          # "my washing came out grey" slipped past the phrases above and was an
                          # echo; the same words in the other order are the same question.
                          "washing came out grey", "wash came out grey", "came out grey",
                          "come out grey", "came out gray",
                          "washing comes out grey", "washing come out grey",
                          "washing from going grey", "wash gone grey", "wash going grey"),
                         ("grey", "gray", "yellow", "dull", "bright", "whiten", "wash",
                          "whiter", "white again", "dingy", "yellowed",
                          # "how do i get my whites really white" and "keep my white shirts
                          # white" say white twice and used to fall through: a white thing is
                          # already needed, so the bare word is safe here.
                          "white", "really white", "proper white", "get them white",
                          "stay white", "stays white", "keep them white",
                          "keep it white", "bright white",
                          # "how do i get my whites white" says the colour twice and nothing
                          # else: both halves of the key collapse onto "white", so the line
                          # counted as one match and fell to the search shrug. These are the
                          # verbs those lines are built on, which gives the key a second part.
                          "get", "keep", "stay", "make", "brighter", "brilliant",
                          "whites white", "whites really white", "whites proper white",
                          # "what temperature for whites" asks the whites question with only the
                          # number in it, and the dial holds whites out for this row
                          "temperature", "temp", "degrees", "how hot")),
          "Wash white cotton at the hottest temperature the label allows with a scoop of oxygen "
          "bleach, and dry it in daylight, which lifts yellowing. Keep whites out of a dark wash "
          "and use a little less detergent so it rinses out.",
          # "why is the sun yellow and not white" is a science question, and "not white" as a key
          # word let it in (a whole-deck compare caught the wash answer on it).
          # a stain names its own question, whatever colour the shirt is: "how do i get a stain
          # out of a white shirt" belongs to the general stain method, not to the whites wash,
          # and the "white shirt" key above took it (smoky-yarn's read of this PR).
          avoid=("stain", "stains", "stained", "mark", "marks", "marked",
                 # the food that makes a stain names its own question: "how do i get curry out
                 # of a white shirt" is the curry-stain method, and this row took it for the
                 # hottest wash and oxygen bleach because the shirt in it is white
                 "curry", "bolognese", "gravy", "ketchup", "tikka", "turmeric",
                 # a photo made black and white is the phone's own job, not the wash
                 "photo", "photos", "picture", "pictures", "image", "images", "camera", "filter",
                 "sky", "cloud", "clouds", "cloudy", "paint", "wall", "walls", "wine", "teeth",
                 # a pair of jeans that has faded is the dark wash's question, and the whites
                 # answer (hottest wash, oxygen bleach) is not what those fibres want
                 "jeans", "jean", "denim", "trousers", "darks", "dark clothes", "black jeans",
                 # a food or a surface that has turned grey is not a wash: "my chocolate went
                 # grey" is fat or sugar bloom, and a whole-deck sample caught it on the whites
                 # wash the moment "went grey" became a key word
                 "chocolate", "cocoa", "bloom", "cheese", "meat", "ham", "bacon", "chicken",
                 "mushroom", "mushrooms", "avocado", "banana", "potato", "potatoes", "grout",
                 "mortar", "tile", "tiles", "leather", "silver", "brass", "metal", "steel",
                 "wood", "paint", "wall", "walls", "car", "paving", "concrete",
                 "snow", "hair", "sauce", "rice", "trainers", "trainer", "sneakers", "shoes",
                 "shoe", "canvas", "rubber", "converse", "boots", "sun", "suns", "sunlight",
                 "star", "stars", "moon", "daylight", "bulb",
                 # a line about using bleach, or about what it did to a garment, is a different
                 # question that only shares the word "white": "bleach on white towels" got the
                 # oxygen-bleach paragraph. Phrases, not the bare word, so "what can i use instead
                 # of bleach to whiten whites" still reaches the whites wash.
                 "bleach on", "bleach in", "bleach the", "bleach my", "bleach a",
                 "use bleach", "put bleach", "add bleach", "much bleach", "soak in bleach",
                 "bleach spot", "bleach mark", "bleach stain", "bleach splash",
                 "bleach splashed", "bleach got", "need bleach", "bleach for", "bleach ok",
                 "bleach safe", "can i bleach", "should i bleach",
                 # wool and knitwear never want the hottest wash and oxygen bleach, and a jumper
                 # that has gone grey is wool that has dulled, not a white that needs whitening:
                 # "my grey jumper has gone grey" got the whites paragraph. A knitwear noun is the
                 # colour in the line, so it stands the whites wash down and the answer is left to
                 # whoever owns wool, rather than the one that would ruin it.
                 "jumper", "jumpers", "cardigan", "cardigans", "sweater", "sweaters",
                 "hoodie", "hoodies", "fleece", "knitwear", "wool", "woollen", "woolen",
                 "jersey", "jerseys",
                 # and the same goes for a garment that is already dark: "how do i stop my black
                 # clothes going grey" asks how to keep the colour it has, and the hottest wash
                 # with oxygen bleach is the one answer that would strip it. friendly-cobra's read
                 # of this PR: the key no longer takes a bare colour, and the avoid list is the
                 # second lock on the same door.
                 "black", "blacks", "black clothes", "black clothing", "navy", "charcoal",
                 "black top", "black tops", "black t shirt", "black t shirts", "black shirt",
                 "black shirts", "black trousers", "black dress", "black dresses",
                 "black jeans", "black leggings", "black socks"),
          guard=_not_a_colour_choice),
    entry("musty-laundry", (("musty", "smelly", "smell", "smells"),
                            ("washing", "laundry", "towels", "clothes", "machine", "tumble",
                             # a bedding that has gone sour is the same job as a towel that has:
                             # "my bedding smells" and "my sheets smell" were both a shrug
                             "bedding", "sheets", "bed sheets", "duvet", "duvet cover",
                             "pillowcase", "pillowcases")),
          "Run a hot service wash with a washing-machine cleaner, clean the filter and the "
          "detergent drawer, and leave the door open between washes. Wash the load at 60C with half "
          "the usual detergent: too much soap is often what makes clothes smell.",
          avoid=("feet", "foot", "breath", "car", "fridge", "freezer", "bin", "drain",
                 "room", "house",
                 # the appliances that have a row of their own: "my dishwasher smells even
                 # after a wash" says "smell" and "wash", which is this entry's key twice over,
                 # and the laundry answer took a line about a machine that washes dishes. The
                 # appliance named is the subject, so each one keeps its own row's answer.
                 "dishwasher", "dishwashers", "dish washer", "dish washers",
                 # a towel that smells is its own entry below: the machine answer is the
                 # wrong subject when the towel is the thing that smells.
                 "towel", "towels", "bath mat", "flannel", "flannels", "face cloth",
                 "facecloth", "washcloth",
                 # "my running gear smells" is sweat in the fibre, which is cleaning.py's
                 # sweat-smell; the machine is not the thing at fault there.
                 "gym", "sports", "running", "workout", "cycling", "leggings", "lycra", "gear")),
    entry("towels-damp", (("towel", "towels", "bath towel", "hand towel", "bath mat", "flannel",
                           "flannels", "face cloth", "facecloth", "washcloth"),
                          ("smell", "smells", "smelly", "stink", "stinks", "musty", "damp",
                           "sour", "washing")),
          # the cause is its own short sentence, so the "why" after this answer gets the reason
          # rather than the shrug, and the wash stays the first thing said
          "Wash them at 60C with half the usual detergent and no softener, then get them fully dry "
          "within a few hours - a towel that stays damp in the machine or a basket grows the smell "
          "in a day. The smell lives in bacteria left in the pile. Hang each one spread out rather "
          "than folded over a rail, and if one wash does not shift it, a cup of white vinegar in the "
          "rinse will.",
          avoid=("kitchen", "fridge", "freezer", "bin", "drain", "room", "house", "microwave")),
    entry("pilling", (("pilling", "pills", "bobbles", "bobbly", "bobble", "fluff"),
                      ("jumper", "wool", "cardigan", "fleece", "fabric", "sweater", "remove",
                       # "how do i stop clothes going bobbly" names the garment, not the jumper
                       "clothes", "clothing", "top", "tops", "shirt", "shirts", "knitwear",
                       "garment", "hoodie", "cardigan", "socks", "leggings")),
          "Shave the bobbles off with a battery fabric shaver or a cheap razor, then wash the "
          "garment inside out on a gentle cycle. Pilling is normal on wool blends and comes from "
          "rubbing, not from the jumper being cheap."),
    entry("towel-soft", (("towel", "towels", "bath towel", "hand towel", "flannel", "washcloth"),
                         ("soft", "softer", "soften", "stiff", "starchy", "crunchy", "rough",
                          "scratchy", "hard")),
          "Use half the detergent you think you need and skip fabric softener, which coats the "
          "fibres and is the usual reason towels go stiff: a cup of white vinegar in the rinse "
          "does the softening job. Dry them with airflow rather than crammed on a radiator, and "
          "take them out while they are still a little damp so they fluff up.",
          avoid=("airer", "radiator", "smell", "damp", "musty", "sour")),
    # A towel that has gone stiff has its own row above, and the cloth that is not a towel - a
    # pair of jeans, a shirt, a whole load - was answered "break your new shoes in slowly at home
    # with thick socks" because `stiff` and `soften` are the blister row's words for a new pair of
    # shoes. The card is the same laundry fact a towel wants, said for the garment: too much
    # detergent, hard water and drying on a radiator.
    entry("stiff-cloth", (("stiff", "stiffness", "stiffened", "starchy", "crunchy",
                           "soft", "softer", "soften", "softening",
                           # "why is my washing stiff" was a search hedge
                           "hard"),
                          ("jeans", "denim", "clothes", "clothing", "washing", "laundry",
                           "wash", "washed", "wash load", "shirt", "shirts", "t shirt",
                           "t shirts", "trousers", "jumper", "jumpers", "sweater",
                           "sweaters", "cardigan", "hoodie", "hoodies", "leggings",
                           "sheets", "linen", "bedding", "garment", "garments", "cotton",
                           "wool", "woollen", "fabric", "curtains")),
          "Hard water, too much detergent and drying on a radiator are what make washed cloth "
          "stiff: use half the detergent, add a cup of white vinegar to the rinse, shake each "
          "piece out and dry it with airflow. Denim and thick cotton soften after a few wears, "
          "so give it a wash or two before you decide it has been ruined.",
          # a stiff back, a stiff neck and a stiff drink are not laundry, and a stiff new pair of
          # shoes is the blister row's question
          avoid=("back", "backs", "neck", "shoulder", "shoulders", "knee", "knees", "joint",
                 "joints", "muscle", "muscles", "leg", "legs", "arm", "arms", "finger",
                 "fingers", "hip", "hips", "ankle", "ankles", "shoe", "shoes", "boot",
                 "boots", "trainer", "trainers", "heel", "heels", "leather", "card",
                 "cards", "board", "door", "window", "brush", "brushes", "paint",
                 "bristle", "bristles", "upper lip", "drink", "whisky", "whiskey", "gin")),
    entry("leather-crease", (("leather", "hide"),
                             ("crease", "creased", "creases", "wrinkle", "wrinkled", "folded",
                              "iron", "smooth")),
          "Hang it on a wide wooden hanger in a steamy bathroom for twenty minutes and smooth it "
          "with your hands while it is warm; the steam lifts most travel creases. Never iron "
          "leather directly, keep it away from radiators, and a little leather conditioner after "
          "the steam stops it drying out at the fold.",
          avoid=("shoe", "shoes", "boot", "boots", "sofa", "car", "seat", "steering")),
    entry("bra-shape", (("bra", "bras", "underwire", "underwired"),
                        # "how do i wash a bra" is the delicates wash; this entry is the
                        # shape that has already gone ("baggy", "stretched"), so "washing"
                        # is not a key word here.
                        ("shape", "stretched", "baggy", "loose", "save", "fix")),
          "Hand wash it in cool water with a little gentle detergent, press the water out in a "
          "towel rather than wringing it, then reshape the cups and dry it flat or hung by the "
          "centre gusset. Heat is what kills the elastic, so no dryer and no hot wash, and "
          "fastening the hooks before washing stops it snagging everything else."),
    # "how do i know my bra size" and "what size bra am i" were both a shrug, and the only bra
    # rows are washing one (delicates-wash) and one that has lost its shape (bra-shape), so the
    # size question had nowhere to go. It is the fit that answers it, not a shop's chart.
    entry("bra-size", (("bra", "bras", "bra size", "underband", "cup size", "underwired bra",
                        "underwire", "underwired"),
                       ("size", "sizes", "measuring", "measure", "what size", "which size",
                        "how do i know", "find my size", "fitting", "fit", "fits", "digs in",
                        "digging in", "too tight", "hurts", "rides up", "straps", "shoulder",
                        "shoulders", "gap", "gaping", "cups")),
          "Measure round your ribs under the bust, snug, and round to the nearest even number: "
          "that is your band size. Then measure round the fullest part, and the difference in "
          "inches is the cup - one inch is A, two is B, three is C, four is D. A bra should sit "
          "level all the way round with room for two fingers under the band, and nearly all the "
          "support comes from the band, not the straps, so straps that dig in mean the band is too "
          "big, not the cup too small. Shops size differently, so get fitted once - it is free in "
          "most department stores and takes ten minutes - and try the sister size (one band "
          "smaller, one cup bigger) if the one you measure is between sizes.",
          # a complaint about how one sits is the same question asked the other way round: "my
          # bra straps dig in" is a fit ask, and without these words it was an "I'm listening"
          ask=("how do i", "what", "which", "size", "measure", "fit", "know", "digs in",
               "digging in", "dig in", "hurts", "uncomfortable", "rides up", "keeps riding"),
          # washing one, a strap that has stretched, a shop's stock and a nursing bra are other
          # answers, and the delicates row owns the wash
          avoid=("wash", "washing", "washing machine", "hand wash", "dry", "dryer", "mould",
                 "mold", "smell", "stained", "stain", "silk", "lace", "delicates", "buy",
                 "buying", "shop", "stock", "sale", "price", "cheap", "swimming", "swim",
                 "nursing", "pregnancy", "pregnant", "breastfeeding",
                 # "wire" in a mouth is the orthodontist's, and braces-ache keys that word
                 "braces", "brace", "retainer", "aligner", "teeth", "tooth", "teeth hurt",
                 "orthodontist", "dental", "fence", "barbed")),

    # Mould on cloth is not mould on a wall: the sponge-and-bleach answer a bathroom gets would
    # wreck a jumper, a leather bag and a pram hood. "mould" alone names nothing to wash, so the
    # second group is the thing that has gone spotted, and a bare "mould" never answers here.
    # "musty" is the word people use for a garment that has been damp too long, and it was
    # reaching the car: "musty boots" was the musty-car card on main.
    entry("mould-fabric", (("mould", "moulds", "mold", "molds", "mouldy", "moldy", "mildew",
                            "mildewy", "musty", "mustiness"),
                           ("clothes", "clothing", "shirt", "shirts", "tshirt", "t-shirt",
                            "dress", "dresses", "coat", "coats", "jacket", "jackets", "jumper",
                            "jumpers", "cardigan", "cardigans", "trousers", "jeans", "skirt",
                            "skirts", "hoodie", "hoodies", "socks", "towel", "towels",
                            "bedding", "sheets", "linen", "blanket", "blankets", "duvet",
                            "pillow", "pillows", "mattress", "cushion", "cushions", "curtain",
                            "curtains", "bag", "bags", "handbag", "leather", "suede", "shoes",
                            "trainers", "boot", "boots", "pram", "buggy", "pushchair", "fabric",
                            "upholstery")),
          _mould_on_it,
          # "moulded studs" is a loose form of "mould", so a parent choosing football boots was
          # told to wipe the spores off with vinegar: "which football boots have moulded studs"
          # and "my boots have moulded studs" both reached this entry, which is the wrong world.
          # The bare word "boots" stays out of this list, because "there is mould on my boots" is
          # this entry's own line.
          avoid=("studs", "studded", "firm ground", "soft ground", "fg boots", "sg boots",
                 "astro", "astroturf", "artificial grass", "3g", "4g", "turf", "cleats",
                 "football", "football boots", "soccer", "shin pads", "which boots",
                 "what boots", "boot size", "new boots", "buy boots"),
          # A bag is where the shopping is as well as what you carry it in, so a line about a food
          # going mouldy in one is the food's question: "why does bread go mouldy in a plastic
          # bag" was told to wipe the spores off with vinegar. Nothing but a container word and a
          # food is needed to tell the one from the other; "mould on my leather bag" names no
          # food and keeps this card.
          guard=_the_mould_is_not_on_a_kept_food),
    # "how do i get rid of moths" names no garment, and it was a shrug on main: a moth in a house
    # is a clothes moth, so the second half takes the plain get-rid words as well as the garments.
    entry("moth-holes", (("moth", "moths", "moth holes", "clothes moth", "clothes moths",
                         "moths in"),
                         ("jumper", "jumpers", "wool", "woollen", "sweater", "sweaters",
                          "cardigan", "cardigans", "cashmere", "knitted", "wardrobe",
                          "wardrobes", "holes", "clothes", "stop", "get rid", "rid of",
                          "how do i", "what should i do", "what do i do", "deal with",
                          "infestation", "infested", "eating", "eaten", "drawer", "drawers",
                          "cupboard", "bedroom", "kill", "kill them", "trap", "traps",
                          "keep away", "getting in")),
          "Empty the wardrobe, wash or dry-clean everything woollen, then vacuum the drawer and "
          "the carpet edge and hang cedar or lavender with the clean wool: moths come back to "
          "damp, unwashed wool, so dry storage is what keeps them out. Small holes can be darned "
          "or covered with an iron-on patch.",
          # Pantry moths come out of flour, raisins and oats, and a wardrobe and cedar blocks are
          # no use against them: "how do i get rid of moths in my kitchen" belongs to the
          # pantry-moth entry that already answers "how do i get rid of pantry moths".
          avoid=("kitchen", "pantry", "larder", "flour", "rice", "oats", "raisins", "cereal",
                 "cupboard moths", "food cupboard", "sugar", "pasta", "grains", "moth ball",
                 "moth balls", "mothballs"), report=True),
    entry("iron-scorch", (("iron", "scorch"), ("burn", "burnt", "shiny", "shine", "mark", "scorch")),
          SHINE_OR_SCORCH_TEXT,
          # An iron that scorched cloth reached the appliance-smoke entry too, because that key
          # holds "scorch"/"scorched" and names the iron among the things that smoke, and it
          # ranked one point higher: "i scorched my shirt with the iron" was told to unplug the
          # iron and open the windows, while the same line with "and there is a brown mark" on it
          # got this answer. The fabric answer is the specific one - it names both the iron and
          # the burn - so it reaches first when both match. Only when both match: an iron that
          # *is* smoking names no burn, so it keeps the smoke answer, and so does a garment next
          # to a fire ("my jumper is smoking in the microwave").
          #
          # "Marking" is the other iron question: an iron that leaves brown marks or marks the
          # clothes as it goes is scaled or running too cool, not scorching them, and that is the
          # soleplate answer. Those words stand the fabric answer down again.
          # ("marking my" is a phrase on purpose: "marking" alone reads as "mark" and would take
          # "how do i get a scorch mark off a shirt" away from this entry.)
          #
          # No bare "brown": it stood the fabric answer down on the one line where the burn is
          # the subject ("brown scorch mark on my white shirt") and on a brown garment, and it is
          # the scale words people say ("leaving marks", "white marks") that mean the soleplate.
          #
          # A smell, smoke or a spark is the appliance failing, not a mark on the cloth: "the iron
          # smells of burning" was told how to sponge a scorch, because "burn" is in this key and
          # "burning" is one of its forms.
          # A pan scorched on the hob is not a shirt: "how do i get rid of a scorch mark on a
          # pan" reached this card through "scorch" + "mark". The cookware words stand it down.
          avoid=("rust", "scale", "limescale", "soleplate", "ironing board",
                 "pan", "pans", "saucepan", "saucepans", "wok", "pot", "pots", "hob", "oven tray",
                 "baking tray", "tray", "trays", "grill", "toaster", "kettle", "cooker",
                 # cleaning the appliance is `cleaning.clean-iron`: "how do i clean a burnt
                 # iron" was told how to sponge a scorch out of a shirt
                 "clean", "cleaning", "cleaned", "descale", "descaling", "sticking",
                 "marking my", "marking the", "leaving marks", "leaves marks", "left marks",
                 "white marks", "brown marks",
                 "smell", "smells", "smells of burning", "smell of burning",
                 "smells like burning", "smoke", "smoking", "smouldering", "on fire",
                 "caught fire", "spark", "sparks", "sparked"),
          bias=2),
    # A shine is the subject of a line even when the iron is not named, and this answer was only
    # reachable through the word "iron": "shiny patch on my trousers" was "Got it", "my trousers
    # are shiny where i sit" was "I'm listening", "my suit jacket is shiny on the elbows" was
    # "I'm here if you want to dig into any of that" and "how do i get shine off a suit jacket"
    # was the coat-buying answer. The shine is the first half of the key and the garment, or the
    # place the shine is, is the second - the same way round as every other row in this table,
    # and no garment word joins iron-scorch's key, because "i left the iron on the shirt too
    # long" is the scorch that row already answers and ironing is the creases row's question.
    entry("garment-shine", (("shine", "shines", "shiny", "shinier", "shiniest", "shininess",
                             "sheen", "glazed", "glossy"),
                            ("shirt", "shirts", "trousers", "trouser", "jacket", "jackets",
                             "suit", "suits", "sleeve", "sleeves", "cuff", "cuffs", "elbow",
                             "elbows", "knees", "skirt", "skirts", "dress", "dresses", "seat",
                             # where on the garment it is: "my skirt has gone shiny at the back"
                             # named the place and not the patch, and reached nothing
                             "back", "bottom", "front", "side", "sides", "arms", "shoulder",
                             "shoulders", "seam", "seams", "waistband", "collar", "armpit",
                             # not "patch": a face has patches too, and "shiny patch on my
                             # forehead" was answered "sponge it with white vinegar, cover it
                             # with a pressing cloth". #6192's own lines all name a garment
                             # ("sleeve", "trousers", "suit jacket", "elbows", "where i sit").
                             "where i sit", "fabric", "cloth", "wool",
                             "woollen", "woolen", "off", "get rid", "remove", "save", "fix")),
          SHINE_OR_SCORCH_TEXT,
          # A garment being bought or hired is a shopping question, however shiny it is, and
          # polishing shoes until they shine is the leather row's.
          avoid=("buy", "buying", "bought", "hire", "hiring", "rent", "renting", "for a wedding",
                 "worth", "price", "how much", "shoes", "shoe", "boots", "boot", "polish",
                 # a shine on a face is the skin's answer: "how do i get rid of a greasy shine on
                 # my nose" was told to sponge a flattened fibre with vinegar, because the bare
                 # "shine" here plus "get rid" was enough
                 "nose", "face", "faces", "forehead", "chin", "skin", "cheeks", "cheek",
                 "t-zone", "t zone", "greasy skin", "oily skin", "my face", "greasy face",
                 # ... and the same shine on any other part of a person is not a garment's either:
                 # "how do i get rid of the shine on my hands" was told to sponge it with white
                 # vinegar and cover it with a pressing cloth once the mark-on-skin row stood down.
                 "hands", "hand", "fingers", "finger", "knuckles", "wrist", "wrists", "palm",
                 "palms", "neck", "thighs", "knees", "arms", "armpits", "scale", "scalp",
                 "polishing", "floor", "flooring", "tiles", "worktop", "sofa", "settee", "car",
                 "paint", "paintwork", "hair",
                 # "glossy" is one edit from "gloss", so "how do i strip old gloss off a door"
                 # matched this row on the fuzzy match and got the shine-and-scorch answer for
                 # a fabric. A door, a wall and a pot of varnish are not clothes.
                 "door", "doors", "old gloss", "gloss paint", "varnish", "varnished",
                 "woodwork", "skirting", "banister", "wall", "walls", "ceiling", "stripping",
                 "strip the", "strip old",
                 # a shine on a table, a cupboard or a floor is the hard-surface cleaning card's
                 "table", "tables", "wooden", "furniture", "cupboard", "sideboard", "chair",
                 "desk", "bench", "wood", "vinyl", "laminate"),
          # a skirt is "skirting" folded to the same stem, so the skirting-board rows are a
          # real rival on the word and the garment has to be the row that wins the line
          bias=2),
    # "how do i get creases out of a dress" was a stain answer ("blot up what you can"), because
    # the key knew a shirt and a pair of trousers and no other garment, and "get out" is not the
    # words the line says ("get creases out"). A dress, a skirt and a suit crease the same way.
    # "linen" is not here on purpose: linen has its own row ("linen creases because the fibre has
    # no give") and this one took the line off it, and the generic asks ("how", "out of",
    # "remove") are out of the ask group for the same reason - the measurement caught both.
    entry("creases", (("crease", "creases", "wrinkled", "crumpled"),
                      ("shirt", "shirts", "trousers", "dress", "dresses", "skirt", "skirts",
                       "suit", "blouse", "top", "jumper", "jacket", "iron", "without",
                       "steam", "get out")),
          "Hang the garment in the bathroom while you take a hot shower, or spritz it with water, "
          "smooth it flat and hang it somewhere warm. Ten minutes in a dryer with a damp towel "
          "drops the creases too."),
    # The garment words are the key and the missing iron is the ask: a bare "iron", "ironing" or
    # "press" in the key of this row takes the only-entry-uses-this-word point off iron-shirt, and
    # "how do i press a shirt to get the creases out properly" then fell to the shower answer when
    # the iron was right there in the kitchen.
    entry("iron-without-iron",
          (("shirt", "shirts", "jeans", "dress", "top", "blouse", "clothes", "t shirt", "tshirt",
            "garment", "trousers", "blazer", "jacket",
            # the board line names no garment at all, and the phrase is the row's own: it does
            # not take the point off iron-shirt the way a bare "ironing" would
            "ironing board"),
           ("without", "no", "iron", "ironing", "board", "havent", "not got", "none")),
          _no_iron_reply,
          bias=3,
          # a shirt that is dirty, stained or scorched is another row's line, and a line that
          # says "creases" is the crease answer's, whose words are the ones it has always used
          avoid=("crease", "creases", "creased", "wrinkled", "crumpled",
                 "stain", "stains", "dirty", "collar", "scorch", "burnt", "burn", "melt",
                 "shrink", "shrank", "wash", "washing", "clean", "cleaning", "descale",
                 "soleplate", "limescale", "sticking", "spitting")),

    entry("sew-button", (("button", "buttons"), ("sew", "stitch", "fell", "loose", "reattach")),
          "Use a needle and doubled thread, coming up through the button and down into the fabric, "
          "with a pin under the button to leave room for the cloth. Wind the thread round the "
          "stitches under the button a few times, then knot it at the back.",
          avoid=("phone", "remote", "control", "keyboard", "mouse", "doorbell", "bell", "alarm",
                 "machine", "lift", "elevator", "press")),
    entry("dry-inside", (("dryer", "drying", "dry", "damp", "wet",
                          # a load that did not dry is the same question, said as a complaint
                          "still wet", "still damp", "wont dry", "won't dry", "not drying",
                          "hasnt dried", "didnt dry", "never dries", "wont dry out",
                          "won't dry out", "not dry"),
                         ("indoors", "inside", "rain", "clothes",
                          "washing", "winter", "jeans", "trousers",
                          "load", "rack", "damp", "smell", "smells",
                          # the thing that is wet is what the drying advice turns on, and none of
                          # these were in the key: "how do i dry towels" and "how do i dry a coat"
                          # were punts, and "how do i dry a wool jumper" got a knitting pattern
                          "towel", "towels", "bedding", "sheets", "duvet", "duvets", "blanket",
                          "jumper", "wool", "knitwear", "cardigan", "coat", "coats", "jacket",
                          "jackets", "waterproof", "fleece")),
          _drying_it,
          # a part of the body with dry skin on it is not the washing: "my skin is really dry
          # in winter" and "my hands are dry and cracked from washing up" are the dry-skin answer
          # a damp smell is the smell card's question and a crease is the iron's, and both are
          # answered better there: this row is only about getting the water out
          avoid=("hair", "paint", "nails", "dishes", "car",
                 "smell", "smells", "smelly", "stink", "stinks", "musty", "mildew",
                 "iron", "ironing", "crease", "creases", "dry clean", "dryclean", "dry-clean",
                 "dry cleaning",
                 # a wet pair of shoes is the `wet-shoes-drying` row's question, and "my shoes
                 # got wet in the rain" was taken by this one on the two words "wet" and "rain"
                 "shoe", "shoes", "trainer", "trainers", "boot", "boots", "sneaker", "sneakers",
                 "plimsoll", "plimsolls", "wellingtons", "wellies", "footwear", "laces",
                 "sandals", "slippers",
                 "skin", "hands", "hand", "face", "legs", "arms", "elbows", "heels", "feet",
                 "knuckles", "scalp", "lips", "lip", "body",
                 # "bedding" reduces to "bed", so a bare "wet" met a child who wets the bed and
                 # "my child wets the bed" was told to hang the washing on a rack. A person who
                 # wets the bed is never a laundry question, and neither is a pet.
                 # a bare "wets" or "wetting" in this list took the row away from every line
                 # with the word "wet" in it, because the matcher reduces them to "wet", so
                 # only the phrases are fenced
                 "wets the bed", "wet the bed", "wets himself", "wets herself", "wets themself",
                 # a window that is wet inside is the condensation question, and this row took
                 # "why are my windows wet inside" on "wet" and "inside" before it
                 "window", "windows", "condensation", "condensing",
                 # a load the machine handed back wet is the machine's fault and not a drying
                 # job: "the clothes come out soaking wet" wanted the spin, not a rack, and this
                 # row holds the same wet words with bias 2, so it was taking the outcome lines
                 "washing machine", "washer", "spin", "spins", "spin cycle", "come out",
                 "comes out", "come out of", "out of the machine", "out of the wash",
                 "still wet after", "wet after wash", "wet after a wash", "wet after the wash",
                 "wet after washing",
                 "bedwetting", "bed wetting", "bedwetter", "wee the bed", "wees the bed",
                 "night accidents", "accidents at night", "pull ups", "pull-ups",
                 "nappy", "nappies",
                 # a wet patch on a mattress is not a load of washing: the mattress has its own
                 # cleaning question and the rack is the wrong answer to it
                 "wet patch", "wet patches", "mattress", "mattresses"),
          # the building is not the washing: see _drying_the_washing
          guard=_drying_the_washing,
          # "how do i dry a wool jumper" reached the knitting pattern, "how do i dry a duvet" the
          # washing card and "how do i dry a waterproof jacket" the buying one: each of those keys
          # the item this line is asking how to dry, and the ask is the point of the line
          bias=2),
    # A mark on what you wear on your feet had no answer at all: `stain-unknown` keeps shoes,
    # trainers and boots in its avoid, because a trainer is not washed like a shirt, and no other
    # entry took them, so "my shoes are stained" got the line back and "my trainers are stained"
    # got a shrug. The two materials need different things and a line does not say which, so the
    # answer gives both and the person takes the branch that fits.
    # A bare "mark" and a "scuff" stay out of the key: a scuff on school shoes is the polish
    # entry's, and it answers it better than a stain card can.
    entry("stain-footwear", (("stain", "stains", "stained"),
                             ("shoe", "shoes", "trainer", "trainers", "boot", "boots", "sneaker",
                              "sneakers", "plimsoll", "plimsolls", "pumps", "sandals", "wellingtons",
                              "wellies", "footwear", "laces")),
          "Blot it while it's wet, don't rub, then work out what you're dealing with. Leather: a "
          "barely damp cloth with a little saddle soap, then polish once it's dry. Canvas or mesh: "
          "an old toothbrush with washing-up liquid and cold water, rinse by dabbing rather than "
          "soaking, and stuff them with newspaper to dry away from a radiator. Never put them in "
          "the machine or the dryer, and suede wants a suede brush only, no water at all.",
          avoid=("mud", "muddy", "salt", "mould", "smell", "smelly", "stink", "suede", "buy",
                 "buying", "size", "which", "best", "new", "clean them properly", "how often",
                 "waterproof", "laces up", "shoe rack", "polish", "sole", "soles")),
    entry("mud-trainers", (("mud", "muddy"), ("trainers", "boots", "shoes", "trousers", "jeans",
                                                 "clothes", "shirt", "off")),
          "Let the mud dry completely, then brush it off with a stiff brush before you touch water; "
          "washing mud while it's wet just pushes it into the fabric. A little washing-up liquid "
          "and a soft brush lifts the rest, then rinse and dry away from heat.",
          avoid=("carpet", "rug", "floor", "floors", "wall", "walls", "car", "drive", "bike",
                 "pushchair")),
    entry("salt-stains", (("salt", "salt stains", "white marks"),
                          ("boots", "shoes", "leather", "snow", "winter", "mark")),
          "Wipe the salt off with a cloth dipped in a mix of one part white vinegar to two parts "
          "water, then let the leather dry away from radiators. Condition it afterwards, because "
          "salt dries leather out and cracks follow.",
          # the road salt answer is for leather: "white marks" is also how scale on a tap, a
          # kettle or a worktop is described, and those are the limescale and cleaning entries.
          avoid=("tap", "taps", "sink", "kettle", "shower", "worktop", "bathroom", "toilet",
                 "wall", "walls", "window", "washing machine", "dishwasher",
                 # a mirror, a screen and a glass table are glass, and their white marks are not
                 # road salt on leather: "white marks on the mirror" was told to condition it.
                 "mirror", "mirrors", "glass", "tv", "television", "laptop", "phone", "screen",
                 "table", "tables", "tabletop", "sideboard", "dresser", "desk", "cupboard",
                 "cabinet", "shelf", "shelves", "chair", "chairs", "floor", "floors",
                 "floorboards", "furniture", "oak", "pine", "mahogany", "teak", "veneer")),
    entry("collar-grey", (("collar", "cuffs"), ("grey", "gray", "dirty", "clean", "shirt",
                                                   "yellow", "ring")),
          "Rub a little washing-up liquid or a paste of bicarbonate of soda into the collar and "
          "leave it 15 minutes before washing. Wash shirts inside out at the hottest temperature "
          "the label allows, and treat the collar each time: once it's grey, heat makes it set.",
          avoid=("dog", "cat", "pet", "buy", "leather", "collar size")),
    entry("iron-shirt", (("iron", "ironing", "press"), ("shirt", "trousers", "properly",
                                                           "crease", "creases", "how")),
          _iron_shirt,
          # an iron is not only the thing you press a shirt with: a cast iron pan, a golf club and
          # the gym are all "iron", and each of those questions has its own answer. A press-up is
          # an exercise, and the fitness domain answers that.
          avoid=("cast iron", "pan", "pans", "wok", "skillet", "griddle", "golf", "gym",
                 "weights", "steak", "ironing board cover",
                 "press up", "press ups", "press-up", "push up", "push ups", "push-up",
                 "workout", "reps",
                 # cleaning the appliance is not pressing a shirt: "how do i clean an iron" and
                 # "my iron is sticking" are `cleaning.clean-iron`, and they reached this card on
                 # the word "iron" alone
                 "clean", "cleaning", "cleaned", "descale", "descaling", "soleplate",
                 "sole plate", "sticking", "stuck", "brown", "limescale", "scorch",
                 "scorched", "white bits", "spitting", "crusty")),
    # The dial on an iron, which had no answer at all: "what temperature should i iron at" was
    # read as a slip of "temperature" and answered by the meat thermostat, joints and all.
    entry("iron-heat", (("iron", "ironing", "press",
                         # a bare "what heat for silk" says no more than the fibre, and the
                         # question it is asking is this dial
                         "wool", "silk", "cotton", "linen", "polyester", "wool jumper",
                         "woollen jumper"),
                        ("temperature", "heat", "setting", "settings", "dots", "dial",
                         "how hot", "too hot", "what heat", "which heat", "what setting")),
          "Sort the pile by what the label says, because the dots are the fibre: one dot is "
          "110C for silk, nylon and anything with elastane, two is 150C for wool and polyester "
          "blends, three is 200C for cotton and linen. Iron the cool things first and let the "
          "soleplate heat up, press a hidden hem to test before you touch a collar, and steam or "
          "a damp cloth on wool and anything dark rather than more heat.",
          # pressing a shirt is iron-shirt's question, and cleaning or buying the appliance is
          # `cleaning.clean-iron` and the shopping row: this one is only the dial
          avoid=("crease", "creases", "properly", "clean",
                 "cleaning", "descale", "soleplate", "sole plate", "sticking", "scorch",
                 "scorched", "brown", "burn", "burnt", "buy", "best", "which iron",
                 "cast iron", "pan", "golf", "gym", "board", "ironing board",
                 # the heat of a wash is the laundry dial's question
                 "wash", "washing", "washed", "laundry", "machine", "dryer", "dry clean",
                 # An iron that will not heat is a fault, not a dial: "my iron isnt heating up"
                 # was reaching the temperatures because "heating up" is one of this row's own
                 # keys. The fault words stand it down, and "what temperature should i iron at"
                 # stays on the dial.
                 # "heating" alone is not here: an avoid word is matched loosely, so it folds
                 # onto "heat" and took every "what heat for wool" line with it.
                 "heating up", "heat up", "heats up", "wont heat", "won't heat",
                 "not heating", "no heat", "isnt hot", "isn't hot", "not hot", "not working",
                 "stopped working", "has stopped", "broken", "broke", "fuse", "plug",
                 "element", "thermostat", "light isnt", "light isn't", "no light", "faulty",
                 "no longer heats", "no longer heating", "no longer gets hot", "doesnt heat",
                 "doesn't heat", "does not heat", "stopped heating", "istant working"),
          bias=2),
    # A pillowcase is a pillow to the wash, and the word people use for it is the whole line's
    # only pillow word: "how do i whiten yellowed pillowcases" was the search shrug, because the
    # key took "pillow" and the reading of "pillowcases" never contains it.
    entry("yellow-pillows", (("pillow", "pillows", "pillowcase", "pillowcases", "pillow case",
                              "pillow cases"),
                             ("yellow", "yellowed", "yellowing", "wash", "whiten", "smell",
                              "stains", "old")),
          "Wash them two at a time on a hot cycle with a scoop of oxygen bleach and a little "
          "detergent, then dry them thoroughly in a tumble dryer with a clean tennis ball to "
          "fluff them up. If they stay yellow or smell after that, replace them: pillows last "
          "about two years."),
    entry("down-jacket", (("padded jacket", "down jacket", "puffer", "padded coat"),
                          ("wash", "washing", "clean", "dryer", "dry")),
          "Wash it on its own on a gentle cycle with a down or technical wash, no fabric "
          "conditioner, then tumble dry on low with two or three clean tennis balls until it's "
          "completely dry. Shake it out as it dries, or the down clumps and loses its loft."),
    entry("suede-clean", (("suede", "nubuck"), ("shoes", "boots", "clean", "stain", "water",
                                                    "marks")),
          "Brush off dry dirt with a suede brush, and for marks rub gently with a suede eraser or "
          "a clean pencil eraser. Keep them out of the rain and spray a protector on when they're "
          "dry; if they get soaked, stuff them with newspaper and dry them slowly, never on a "
          "radiator."),
    entry("wool-coat", (("wool coat", "woollen coat", "coat"),
                        ("wash", "washing", "clean", "care", "store", "summer", "moth")),
          "Wool coats should be dry-cleaned once a season, not washed: brush them down, air them "
          "and sponge small marks with cold water. Store them clean and dry in a breathable bag "
          "with cedar or lavender, because moths come for traces of food and sweat."),
    # Static in hair is a nuisance to fix, not a fact to explain: the science entry used to answer
    # "how do i stop static in my hair" with a paragraph about electrons and no way to stop it.
    entry("static-hair", (("static", "static electricity", "flyaway", "flyaways"),
                          ("hair", "hairs", "head", "fringe", "brush", "brushes", "comb")),
          "Smooth it with a tumble-dryer sheet, a little leave-in conditioner or a spritz of hairspray "
          "on the brush. Dry air is the cause, so a humidifier or a bowl of water near a radiator "
          "helps in winter, and a metal coat hanger or a metal comb run through the hair takes the "
          "charge off in seconds when you are out.",
          avoid=("clothes", "jumper", "shirt", "socks", "tights", "dress", "laundry", "dryer")),
    # The charge is not always said as "static": a jumper that clings to your legs or crackles is
    # the same complaint, and "my jumper keeps clinging" was nothing but a read-back. "get rid of
    # static in clothes" reached the textile bank, so a noun in the line is what this row needs to
    # be told apart from the recycling one.
    entry("static-clothes", (("static", "static electricity", "cling", "clings", "clinging",
                              "clung", "crackle", "crackles", "crackling", "shocks", "shock",
                              "zaps", "zap"),
                             ("clothes", "clothing", "jumper", "jumpers", "shirt", "shirts",
                              "skirt", "skirts", "trousers", "leggings", "dress", "socks",
                              "fabric", "fabrics", "wear", "wearing", "dryer", "tumble",
                              "washing", "laundry", "outfit")),
          "Use a dryer sheet or a little fabric conditioner, or rub a damp hand or a metal hanger "
          "over the garment before you put it on. Dry clothes slightly less, because "
          "over-drying and synthetic fabrics are what build the charge. It is the fabric rubbing "
          "on itself in dry air, so nothing is broken: the dryer sheet is the fix, not the "
          "machine.",
          bias=1,
          # cling film and a shock from the mains are both "cling" and "shock" and neither is a
          # jumper that crackles
          avoid=("cling film", "clingfilm", "film", "wrap", "food", "leftovers", "sandwich",
                 "electric shock", "electrocuted", "electrocution", "mains", "socket", "plug",
                 "wiring", "fuse", "box", "breaker", "light switch")),
    # "tight" is the same word form as "tights", so a line about a tight calf scored here and got
    # advice on nail polish and a net bag. A ladder has to be named.
    entry("tights-ladder", (("tights", "ladder", "ladders", "laddering"),
                            ("stop", "fix", "nail", "keep", "snag", "run", "have", "has",
                             "got", "repair", "mend", "hole")),
          "Catch a ladder straight away by dabbing clear nail polish on both ends, then wash tights "
          "in a net bag. Keeping your nails smooth, your feet smooth and putting them on with "
          "damp hands is what stops the next one.",
          # a ladder, a hole, a snag or a run has to be named: "tight" is a form of "tights",
          # so without this a tight calf and a tight pair of jeans got the nail-polish answer.
          # And the ladder has to be the one in the fabric: a bare "ladder" is a thing you climb,
          # so "i cant keep going up and down the ladder all day" got nail polish and a net bag.
          # A run in a stocking is "a ladder in", "a laddered pair", or the tights themselves
          # named in the line, and none of those is said about a stepladder.
          # "laddered" and "laddering" are forms of "ladder" to the matcher, so they name the
          # stepladder as readily as the stocking: the phrase that carries the fabric is the
          # preposition ("a ladder in") or the garment itself.
          ask=("ladder in", "ladders in", "snag", "snagged", "snags",
               "hole", "holes", "torn", "rip", "rips", "run in", "runs in", "a run",
               "tights", "stockings")),
    # Putting the winter things away in spring is not folding them and not packing them: it is a
    # storing question with its own answer, and main had none - "how do i store winter clothes"
    # was given the 2-to-8C packing list for a cold city break.
    entry("store-winter-clothes",
          (("winter clothes", "winter clothing", "winter coat", "jumper", "jumpers", "wool coat",
            # "clothes for winter" says the same thing the other way round: it was a search hedge
            # once the folding row stood down for the season words
            "clothes for winter", "clothes for summer", "clothes for the winter",
            "clothes for next winter", "summer wardrobe", "winter wardrobe",
            "coats", "knitwear", "summer clothes", "out of season", "seasonal"),
           ("store", "storing", "storage", "keep", "keeping", "put away", "pack away",
            "packed away", "away for the summer", "away for summer", "away for the winter",
            "away for winter", "until next year", "moth", "moths", "cedar",
            "bag", "bags", "loft", "under the bed", "wardrobe")),
          "Wash or dry-clean everything first, because moths eat the traces of sweat and food and "
          "not the wool itself, then store it bone dry in a cotton sheet, a cotton bag or a "
          "vacuum bag in a dry room, not a damp loft or garage. Fold knits flat rather than "
          "hanging them, stuff boots with newspaper so they keep their shape, add cedar or "
          "lavender, and open the bags for a look in February.",
          ask=("store", "storing", "storage", "keep", "keeping", "put away", "pack away",
               "moth", "moths", "away for the summer", "until next year", "how do i",
               "where should i", "what is the best way"),
          # a wash, a stain, a size and a declutter are their own answers, and the packing list is
          # the travel domain's: this row keeps the garment that is going into storage
          avoid=("wash", "washing", "washed", "stain", "stains", "iron", "ironing", "size",
                 "fit", "fits", "shop", "sale", "refund", "sew", "hem", "alter", "declutter",
                 "charity", "suitcase", "luggage", "pack for", "packing for", "cold city",
                 "holiday", "trip", "travel")),
    entry("take-up-hem",
          # The act in one group and the garment in the other, so the row answers "how do i hem
          # my jeans", "my jeans are too long", "how do i shorten a dress" and "how do i turn up
          # my trousers" alike. Before this, "how do i hem my jeans", "how do i shorten my jeans",
          # "my jeans are too long" and "how do i take up my jeans" were a search hedge or a
          # "thanks for telling me", and only the word "hem" with the word "trousers" answered.
          (("hem", "hems", "hemming", "hemline", "shorten", "shortening", "take up", "taking up",
            "turn up", "turned up", "turnups", "turn ups", "too long", "to long", "drag",
            "drags", "dragging", "let down"),
           # "how do i take up a hem" names no garment at all, and it was a hedge for that
           # reason: what is being shortened is the hem itself, so the hem counts as the thing
           ("hem", "hems", "hemline", "jeans", "denim", "trousers", "pants", "chinos", "skirt",
            "dress", "curtains", "sleeves", "coat", "shirt", "t shirt", "legs")),
          _take_up_hem,
          # a pair to be bought, brought in or stretched is the rows above, and a wash, a stain
          # or a hole is the care rows'
          avoid=("shrink", "shrank", "shrunk", "stretch", "tight", "too tight", "buy",
                 "buying", "which", "size", "wash", "washing", "fade", "stain", "hole",
                 "holes", "ripped", "torn")),
    entry("stuck-zip", (("zip", "zipper", "zips", "zippers"),
                         # The fault words, not just "stuck" and "wont": "how do i fix a zip that
                         # wont close" and "my jeans zip keeps coming down" reached Task Manager
                         # and an echo, because the row asked for the word stuck and neither line
                         # says it. A zip that will not do up, one that opens again behind the
                         # slider and one that needs a new slider are all this card.
                         ("stuck", "jammed", "jacket", "fix", "wont", "won't", "open",
                          "opening", "opens", "wont close", "won't close", "wont do up",
                          "won't do up", "wont zip", "won't zip", "coming down",
                          "keeps coming down", "comes down", "come apart", "came apart",
                          "broken", "split", "teeth", "slider", "pull", "fly", "coat",
                          "repair", "mend", "replace", "new",
                          # the verbs people use for a zip that will not move: "how do i
                          # unjam my zip" went to the archive card and "how do i unstick a
                          # zip" to nothing, because only "stuck" and "jammed" were here
                          "unjam", "unjamming", "unstick", "unsticking", "loosen",
                          "loosening", "free", "free it up", "moves", "wont move",
                          "won't move", "stiff", "gritty", "grit",
                          # a zip that opens itself is the slider worn, the same fault as a
                          # stuck one: "how do i stop a zip coming undone" was answered with how
                          # to unpack a .zip file, and the pencil wax and new slider are the fix
                          "coming undone", "comes undone", "keeps unzipping", "unzipping",
                          "wont stay up", "won't stay up", "wont stay done up",
                          "wont stay fastened", "slides down",
                          "trousers", "jeans", "skirt", "dress", "boots", "boot", "hoodie",
                          "sleeping bag", "tent", "suitcase", "bag")),
          "Don't force it: rub a pencil point or a little candle wax along the teeth, pull the "
          "fabric edges apart and ease the slider back. If the slider has come off one side, "
          "zipping it back on from the bottom usually fixes it; otherwise a tailor can replace the "
          "whole zip.",
          # a zip that is doing its job is not a fault, and the archive words keep a zip file out
          bias=4,
          avoid=("file", "files", "folder", "download", "upload", "email", "attachment",
                 "compressed", "zip code", "postcode",
                 # A zip that broke is two questions, and this card answers only one of them.
                 # "can i return a coat with a broken zip" and "my new jacket arrived with a
                 # broken zip" want the retailer, not pencil wax, so the words that ask for the
                 # shop leave this card to the faulty-goods ladder.
                 "return", "returns", "returning", "refund", "refunds", "take it back",
                 "took it back", "send it back", "sent it back", "arrived with", "arrived broken",
                 "arrived damaged", "came broken", "came damaged", "faulty", "consumer rights",
                 "my rights", "warranty", "guarantee", "under guarantee", "reject it",
                 "money back", "bought it", "i only bought"),
          guard=_not_fitting_a_zip),
    # Put the zip in, rather than do the zip up. "how do i sew a zip in" was answered with how to
    # unpack a .zip file, and "how do i stop a zip coming undone" with the same, because the
    # archive rows ask for a bare "how" beside "zip" and nothing told them a needle was involved.
    # The fault rows own a zip that is stuck or broken; this one owns a zip that is being sewn,
    # replaced or will not stay done up.
    entry("sewing-a-zip",
          (("zip", "zips", "zipper", "zippers"),
           ("sew", "sewing", "sewn", "stitch", "stitching", "unpick", "unpicking", "baste",
            "basting", "tack", "tacking", "insert", "inserting", "put in", "put a new",
            "zip foot", "zipper foot", "invisible zip", "fabric", "hem", "seam", "dressmaking",
            "replace", "replacing", "new zip",
            # how people actually word it: the verb and the zip are rarely next to each other
            # ("how do i put a zip in a dress", "how do i put a zip fly in", "how do i shorten
            # a zip"), and "put in" only matched when the two sat side by side.
            "put a zip", "zip in", "sewing a zip", "sew a zip", "zip fly")),
          "Open the seam where the zip goes and press it flat, then pin the zip face down on the "
          "right side with the teeth on the seam line and baste it by hand - the basting is what "
          "keeps the two sides level, and a zip foot lets the needle run close to the teeth "
          "without catching them. Stitch one side, close the zip, check the seam lines up, then "
          "stitch the other side and unpick the basting. To replace one, unpick the old zip "
          "without cutting the seam allowance and reuse its opening. A zip that slides open "
          "behind the slider is the slider worn, so pinch it gently with pliers or fit a new "
          "slider; if the teeth have gone, the zip has to come out.",
          ask=("sew", "sewing", "sewn", "stitch", "stitching", "unpick", "baste", "insert",
               "zip foot", "fabric", "hem", "seam", "put", "putting", "new", "fit", "fitting",
               "change", "changing", "replace", "replacing"),
          avoid=("file", "files", "folder", "folders", "download", "upload", "email", "attachment",
                 "compressed", "compress", "zip code", "postcode", "unzip", "extract",
                 "stuck", "jammed", "wont close", "won't close", "wont zip", "won't zip",
                 "return", "returns", "refund", "send it back", "faulty",
                 "arrived", "warranty", "guarantee", "sleeping bag", "tent", "suitcase"),
          bias=2),
    # the smell is what is asked for and the feet are the subject: bare "feet" in a key group
    # beside "what" and "help" made this entry answer "my feet hurt after standing all day"
    entry("smelly-feet", (("smelly feet", "feet smell", "foot odour", "foot odor", "stinky feet",
                           "smell", "smelly", "smelling", "smells", "stink", "stinks",
                           "sweat", "sweaty", "sweating", "odour", "odor"),
                          ("feet", "foot", "toes", "socks", "insoles")),
          "Wear cotton or wool socks and change them daily, wash feet with soap and dry between "
          "the toes, and alternate shoes so each pair dries out. If it doesn't settle, a "
          "pharmacy antiperspirant for feet is stronger than deodorant.",
          ask=("smell", "smelly", "smelling", "smells", "stink", "stinks", "sweat", "sweaty",
               "sweating", "odour", "odor")),

    entry("wash-jeans", ("jeans", ("wash", "washing", "often", "clean", "how often")),
          "Wash jeans every five to ten wears, inside out and in cold water, and air them between "
          "wears. Spot-clean small marks instead of washing, and skip the tumble dryer if you want "
          "them to last."),

    # --- how hot to wash ------------------------------------------------------
    # "is it cheaper to wash at 30", "what temperature should i wash at" and "does washing at 30
    # clean clothes" were all shrugs, and they are one question: what the number on the dial is
    # for. The heat words are one half of the key, so a line has to say a temperature (or ask how
    # hot) and be about washing before it lands here; the cost of running the machine, a faulty
    # one and towels each keep their own answer.
    entry("wash-temperature",
          (("temperature", "temp", "hot", "hotter", "hottest", "cold", "colder", "cool",
            "30", "40", "60", "90", "95", "degrees", "how hot", "eco", "quick wash", "hand wash",
            "cheaper", "cheapest", "economical",
            # "what setting should i wash towels on" was a towel-dampness answer, and the
            # setting is the dial without a number
            "setting", "settings", "set the", "which cycle", "what cycle"),
           ("wash", "washing", "washed", "laundry", "clothes", "cycle", "programme", "program",
            "machine", "load", "shirts", "sheets", "bedding", "enough", "clean", "cleaner",
            # the laundry people name when they ask the dial: "what temperature for whites" had
            # no word this row could read, so the body temperature took it, and "how hot should
            # the wash be" went to the baby's bath because that row reads "washing" + "how hot"
            # a duvet stays out: "can i wash a duvet at 60" is the duvet card, which says which
            # duvets even go in a machine, and only a bare "what temperature for a duvet" was
            # reaching the fever row
            "whites", "lights", "cotton", "cottons", "linen", "towels",
            "colours", "colors", "darks", "the wash", "wash be", "washing be",
            # a germ question is the dial without saying so: "does 30 degrees kill bacteria"
            # names no wash word at all, and it is not a weather or a fever line
            "bacteria", "germs", "kill bacteria", "kills bacteria", "kill germs", "kills germs",
            "hygienic", "sanitise", "sanitize",
            # "what temperature for jeans" is the dial, and jeans are named here so it is not a
            # body temperature; a jeans line with no heat word is still the wash-jeans card
            "jeans", "denim")),
          _wash_temperature,
          # the machine itself, its faults and its running cost are their own answers, and so is
          # a towel that needs washing
          # the verb is not always a laundry: hands, dishes, the bath, the face and the dog are
          # other things people wash, and the dial is a wrong answer for every one of them
          # ("what temperature should i wash my hands at" and "what temperature should the water
          # be to wash dishes" both came here), and a wash that will not heat is a fault
          # a hot tap that runs cold is `no-hot-water`'s question: "hot water is not hot enough"
          # is the supply, not a dial, and this row read its own "hot" and "enough" and told
          # somebody with no hot water to treat 30C as the everyday setting
          avoid=("hot water", "hot tap", "hot taps", "cold tap", "cold water tap",
                 "water is not hot", "water isnt hot", "water isn't hot", "water not hot",
                 "hand", "hands", "dishes", "dish", "plates", "pots", "pans", "bath", "shower",
                 "face", "hair", "car wash", "dog", "dogs", "muddy", "washing up",
                 # the heat of an iron is `iron-heat`: "how hot should the iron be for cotton"
                 # was this dial answering with a laundry temperature
                 "iron", "ironing", "soleplate", "ironing board",
                 # a hot tub is not a wash: "how do i clean my hot tub" was answered with the
                 # laundry dial, because the tub's own row keys "clean" and this one read the
                 # "hot" in it. The tub, the spa and the jacuzzi are named here.
                 "hot tub", "hot tubs", "hottub", "jacuzzi", "spa bath",
                 # buying the powder is a shopping question, not the dial: "is it cheaper to buy
                 # washing powder in bulk" was answered "treat 30C as the everyday setting"
                 "bulk", "in bulk", "powder", "powders", "tablets", "liquid detergent",
                 "stock up", "multipack", "buy", "buying", "supermarket",
                 # the hour of the day is the tariff row's question, and this row read its own
                 # "cheaper" and "washing machine" and answered "is it cheaper to put the washing
                 # machine on at night on economy 7" with the dial. A line that names the hour,
                 # the tariff or the time of day is when to run the machine, not how hot.
                 "at night", "overnight", "late at night", "economy 7", "economy7",
                 "off peak", "off-peak", "tariff", "tariffs", "what time", "best time",
                 "cheapest time", "time of day", "during the day", "in the morning",
                 "in the evening", "energy bill", "electricity bill",
                 # "is 60 too hot for a wash" is the dial, not a machine that runs hot: the
                 # machine's own heat is named by the words below and by _A_FAULTY_MACHINE, which
                 # is what stands this row down on "my machine gets too hot" and "the drum is too
                 # hot". A bare "too hot" here cost the dial answer to every "is 60 too hot" line.
                 "hot to the touch", "gets very hot", "getting hot",
                 "burning", "overheating", "boil", "boils", "boiling", "boiled", "kettle",
                 "baby", "babies", "newborn", "infant", "toddler", "nappy", "nappies",
                 # the machine's name is not a fault on its own: "what temperature should i set
                 # the washing machine to" is the dial, and the fault words below are what tell
                 # a broken machine from a question about the setting
                 "drum", "spin", "leak", "leaking", "smell",
                 "smelly", "musty", "wont drain", "won't drain", "not draining", "error", "e20",
                 "run", "running", "running cost", "electricity", "kwh", "energy", "per cycle",
                 # "what temperature for towels" is this row's own question and its answer names
                 # towels, so towels are read here; a towel that needs washing carries no heat word
                 "dishwasher", "tumble dryer", "dryer", "bath mat", "flannel",
                 # the weather and the line are not the dial: "is it too cold to hang the washing
                 # out" read this row's "cold" and "washing" and was told to treat 30C as the
                 # everyday setting. `home_craft.washing-outside` is the answer to those lines.
                 "hang", "hanging", "hung", "out on the line", "on the line", "washing line",
                 "outside", "outdoors", "drying", "dries", "dry outside", "air dry", "airer",
                 "weather", "forecast", "today", "tomorrow", "rain", "raining", "wind", "windy",
                 "frost", "sunny", "sunshine",
                 # a duvet or a pillow is its own card, which says which ones even go in a
                 # machine: "can i wash a duvet at 60" is not the everyday dial
                 "duvet", "duvets", "pillow", "pillows",
                 "wool", "jumper", "silk", "bra", "bras", "nappy", "nappies",
                 # "cold" is the fridge's word as much as the dial's: "my fridge is not cold
                 # enough" was taking the 30C laundry card, and a fridge and a freezer have
                 # their own answers
                 "fridge", "freezer", "fridge freezer", "milk", "defrost", "frozen",
                 "ice box", "cool box", "larder",
                 # whites have their own answer, which is the hottest wash the label allows with
                 # oxygen bleach: "should i wash whites at 60" was taking the 30C card
                 "white", "whites", "whiten", "whiter", "grey", "gray",
                 # "cycle" in the key above is the drum's programme, and a bicycle is not one:
                 # "is cycling in the cold bad for you" was told to treat 30C as the everyday
                 # setting. Going out in the cold is the run-in-the-cold note's question.
                 "cycling", "bike", "bicycle", "ride", "riding", "commute", "commuting",
                 "outside", "outdoors",
                 # a number on a bill is money, not a dial: "we left 60 on a 48 bill" read the 60
                 # as the wash temperature and answered about towels and bedding. The money words
                 # are named here, and the sum itself is `maths`' own _left_on_the_bill.
                 "bill", "bills", "tip", "tips", "service charge", "left on", "tab"),
          bias=2,
          # only a question about the dial, never a statement of what the person already does:
          # "i wash them at 40" and "i tried a hot wash already" are the machine's past, and this
          # row read both as an ask
          ask=("what", "which", "should", "is", "does", "do i", "can i", "could", "would",
               "will", "how", "temperature", "temp", "need", "best", "right"),
          # "is it cold enough for a coat" is a coat question: this row read its own "cold" and
          # "enough" and told a person going out to treat 30C as the everyday setting
          guard=lambda understood: not _the_enough_is_about_a_garment(understood)),

    entry("wash-wool-temp",
          (("wool", "woollen", "woolen", "merino", "lambswool", "cashmere", "jumper", "jumpers",
            "sweater", "sweaters", "cardigan", "cardigans", "knitwear", "knit"),
           ("temperature", "temp", "degrees", "30", "40", "60", "90", "hot", "hotter", "warm",
            "cold", "cool", "wash", "washing", "washed", "cycle", "programme", "program",
            "machine", "hand", "shrunk", "shrink", "safe")),
          "Twenty degrees or a wool cycle at 30, never 40: heat and agitation are what felt wool, so "
          "a jumper washed at 40 in an ordinary cycle comes out smaller and thicker. Use a wool "
          "detergent, a short gentle cycle with no spin or the lowest one, dry it flat and never "
          "in the tumble dryer. If it is only lightly worn, airing it on a hanger does more good "
          "than washing it.",
          bias=3,
          # wool that has already shrunk is the restore card, a wool coat is its own thing, and a
          # stain on wool is a stain
          avoid=("shrank", "shrunk", "shrunken", "coat", "coats", "stain", "stains", "smell",
                 "moths", "pilling", "bobble", "bobbles", "dry clean", "iron",
                 # choosing one is the knitwear-buy row below, and "warm" is the temperature
                 # question in this row's ask as well as the warmth one in that row's key:
                 # "i want a warm jumper for winter" was answered with how to wash wool
                 "buy", "buying", "bought", "best", "warmest", "warmer", "warm enough",
                 "for winter", "which jumper", "what jumper", "cheap", "price", "cost",
                 "present", "gift"),
          # the heat is this row's question and the cleaning.py hand-wash card answers "how do i
          # hand wash a cardigan": without this guard every wool how-to came here instead
          ask=("temperature", "temp", "degrees", "30", "40", "60", "90", "hot", "hotter", "warm",
               "cold", "cool"),
          # "i washed my wool jumper hot" then "is it ruined": the card above is already on the
          # screen, and what the person wants is whether the jumper is gone. It is not - felted
          # wool does not come all the way back, and a half hour in cool water and a stretch gets
          # the size back - and saying that is the whole answer.
          outcomes=(("survives",
                     "Not gone, but not what it was: a hot wash felts wool, so it comes out "
                     "smaller and thicker and does not go all the way back. Half an hour soaking "
                     "in cool water with a little hair conditioner or wool wash, then stretch it "
                     "back to shape while it is wet and dry it flat, gets most of the size back."),)),
    # --- stains ---------------------------------------------------------------
    # A yes-or-no about the first wear is an answer, not a weighing-up: this went to the shrug
    # "can't call that one for you, say what you'd lose either way".
    entry("wash-new-clothes",
          (("new clothes", "new clothing", "new shirt", "new jeans", "new top",
            "new jumper", "new pants", "new underwear", "new bedding", "new sheets",
            "brand new clothes"),
           ("wash", "washing", "wear", "wearing", "before", "first", "straight away",
            "should i wash", "do i need to wash", "need washing")),
          "Yes, wash them first: new clothes carry the factory's dyes, a dressing that keeps them "
          "looking crisp, and whatever was on the hands of everyone who tried them on. A quick "
          "wash at 30C does it, and a rinse is enough for underwear and anything worn next to the "
          "skin. Two exceptions: a suit, a coat or anything dry-clean only, which is fine to wear "
          "and better aired than washed, and clothes you are about to return.",
          bias=2),
    entry("stain-grease", (("grease", "oil", "fat", "butter", "mayonnaise", "oily", "greasy"),
                           # "how do i get grease off a jumper" named no word this row knew, so it
                           # was a shrug: every common garment word belongs on this side.
                           GARMENT + STAIN_ASKS + ("apron", "tablecloth", "tea towel", "fabric",
                                                   "uniform", "tie")),
          "Rub a little washing-up liquid into the grease mark with your fingers and leave it 10 "
          "minutes before washing at the hottest temperature the label allows. Don't tumble dry "
          "until the mark is gone, because heat sets it.",
          avoid=NOT_A_GARMENT_SURFACE + ("pan", "pans", "oven", "cooking", "food", "salad",
                                         "kitchen", "car", "engine"),
          guard=_grease_is_not_a_burn),
        # "how do i get a stain out of a white shirt" then "its engine oil" got the dipstick, because
    # the only row that names engine oil as an oil is the car's, and the car's row is fenced out of
    # anything about fabric. The substance is what the stain needs, so this row is the grease one
    # for the oil that comes off an engine: the same line in one turn, or the second turn of a
    # stain question. It stands down everywhere else, which is why the key can be the substance
    # alone and the memory does the deciding.
entry("stain-engine-oil",
          (("engine oil", "motor oil", "car oil", "gear oil", "diesel"),
           ("stain", "stains", "stained", "mark", "marks", "shirt", "clothes", "trousers",
            "jeans", "top", "jacket", "sleeve", "fabric", "out", "remove", "get", "off")),
          _engine_oil_stain,
          # a service, a leak, a warning light and a dipstick are the car's questions
          avoid=("service", "serviced", "servicing", "mot", "leak", "leaking", "sump", "dipstick",
                 "level", "top up", "warning light", "oil light", "change the oil", "oil change",
                 "how often", "which oil", "what oil", "how much oil", "drive", "driveway",
                 "paving", "garage floor", "under my car", "under the car"),
          bias=2),
    entry("stain-paint",
          (("paint", "paints", "painted", "emulsion", "gloss", "undercoat", "primer",
            "woodstain", "wood stain", "varnish", "gloss paint", "emulsion paint",
            "spilt paint", "spilled paint"),
           GARMENT + STAIN_ASKS + ("fabric", "sleeve", "sleeves", "cuff", "cuffs", "collar",
                                   "knee", "knees", "leg", "legs", "hem", "pocket", "pockets",
                                   "trousers", "jeans", "jumper", "jumpers", "hoodie", "coat",
                                   "coat sleeve", "uniform", "apron", "shorts", "skirt")),
          "Water-based emulsion and the water-based satins come out while they are wet: blot what "
          "you can with kitchen paper, then hold the mark under cold running water and rub a "
          "little washing-up liquid in from the back of the fabric. Oil-based gloss, undercoat and "
          "varnish need a rag damped with white spirit dabbed at the mark before the wash, and let "
          "it dry between dabs. Wash on the label's temperature and look before you tumble it, "
          "because heat sets paint like a dye.",
          # a wall, a door, a radiator, a ceiling and a floor are the decorating domain's, and
          # skin, hair and a brush are nobody's garment: "how do i get paint off a door" reached
          # the laundry answer once this row keyed the word paint at all.
          avoid=NOT_A_GARMENT_SURFACE + (
                 "wall", "walls", "ceiling", "ceilings", "door", "doors", "radiator", "skirting",
                 "banister", "window", "windows", "frame", "frames", "floor", "floors", "flooring",
                 "wood", "woodwork", "wooden", "wallpaper", "hand", "hands", "skin", "finger",
                 "fingers", "nail", "nails", "hair", "brush", "brushes", "paintbrush", "roller",
                 "tray", "spray", "spraying", "gun", "car", "bike", "bicycle", "toy", "toys",
                 # a bed, a desk, a chair and a cot are things to paint, not a garment the paint
                 # went on: "how do i paint a bed" was the laundry answer on "bed"
                 "bed", "beds", "bed frame", "cot", "cots", "crib", "cribs", "desk", "desks",
                 "stool", "stools", "bench", "benches", "cabinet", "cabinets", "wardrobe",
                 "fence", "shed", "garden", "model", "figures", "canvas", "picture", "cartoon",
                 "nails painted", "what colour", "which colour", "what color", "which color",
                 # A colour that came out wrong is not a stain to lift, and "my gloss came out too
                 # dark" and "my varnish came out too dark" were met with washing-up liquid and
                 # cold running water because the line says "came out" and names a paint. What a
                 # finish that dried too dark needs is the decorating answer.
                 "too dark", "darker", "too pale", "too light", "too strong", "too bright",
                 "wrong colour", "wrong color", "went dark", "dried dark",
                 "thin", "thinning", "dilute", "peeling", "bubbling", "blistering",
                 "drying time", "dry time", "how long to dry", "coats", "two coats",
                 # a tin is what to do with the paint you have left, not a stain
                 "old paint", "leftover", "left over", "tin", "tins", "bin", "bins", "tip",
                 "household waste", "recycling", "recycle", "dispose", "disposal", "shed",
                 "garage", "store", "storing", "keeping"),
          bias=2),
    entry("stain-paint-in-hair",
          (("paint", "paints", "painted", "emulsion", "gloss", "gloss paint", "emulsion paint",
            "varnish", "oil paint", "white spirit"),
           # the hair is what it is on, so the hair words are asked for beside the paint: this row
           # is the one that says how to get paint out of hair, and the words that name a
           # hairdressing job stand it down.
           ("hair", "hairs", "scalp", "fringe", "ponytail", "beard", "strands", "head",
            "out of", "get out", "got out", "remove", "removing", "wash", "wash out", "comb")),
          "Soak the paint in oil before you touch it. Work cooking oil or mayonnaise through the "
          "strand with your fingers, leave it 20 minutes, then comb it out from the ends up and "
          "shampoo twice. Emulsion softens in warm water and washing-up liquid alone. Start at the "
          "ends so a blob near the scalp is not dragged through the whole length, and cut out what "
          "will not come, which on a fringe is the honest fix.",
          # a dye, a colour, a cut and a brush are the hairdressing rows' questions
          avoid=("dye", "dyed", "dying", "colour", "color", "grey", "gray", "going grey",
                 # "how do i get scratches out of car paint" and "how do i touch up a scratch on
                 # my car" met this row on "paint" and "get out"/"touch up": bodywork is the cars
                 # row's, and no one washes a car's paint out of its hair
                 "car", "cars", "van", "vans", "bodywork", "paintwork", "bumper", "bonnet",
                 "scratch", "scratches", "scratched", "stone chip", "stone chips", "lacquer",
                 "hairbrush", "brush", "bristle", "shampoo", "greasy", "thinning",
                 "falling out", "hairstyle", "fringe cut", "fringe trim", "cut my",
                 "curly", "curls", "straighten", "straighteners", "frizz", "dandruff",
                 "dry hair", "dry the hair", "paint a wall", "paint the wall",
                 # a carpet, a rug and a sofa are the home domain's spilt-tin row
                 "carpet", "carpets", "rug", "rugs", "sofa", "sofas", "settee", "couch",
                 "cushion", "cushions", "mattress", "upholstery", "armchair", "stair",
                 "stairs", "floor", "floors", "floorboards", "table", "chair", "worktop",
                 # a brush, a door and a run of woodwork are the decorating rows' subjects, and
                 # "paint" is the front of "paintbrush": "how do i get paint out of a paintbrush"
                 # and "how do i remove old paint from wood" were both told to soak a head of hair
                 "brush", "brushes", "paintbrush", "paintbrushes", "roller", "sleeve", "tray",
                 "wood", "wooden", "woodwork", "skirting", "door", "doors", "radiator",
                 "radiators", "wall", "walls", "ceiling", "ceilings", "window", "windows",
                 "frame", "frames", "banister", "shelf", "shelves", "cupboard", "furniture",
                 "shed", "fence", "deck", "old paint", "stripper", "stripping", "sand",
                 "sanding", "drying", "how long", "coats", "thin", "thinning", "dilute",
                 "colour", "what colour", "which colour"),
          bias=2),
    entry("stain-grass", ("grass", GARMENT + STAIN_ASKS),
          "Work a paste of bicarbonate of soda and water, or a little washing-up liquid, into the "
          "green and leave it 30 minutes before a normal wash. Check before drying: heat sets a "
          "grass stain in.",
          # a lawn is not a garment: "how do i remove weeds from my grass" reached the stain
          # answer once the garment list carried "remove" and "get out".
          avoid=NOT_A_GARMENT_SURFACE + (
                 "weeds", "weed", "lawn", "mow", "mowing", "mowed", "garden", "gardener",
                 "patch", "seed", "turf", "artificial", "moss", "astroturf")),
    entry("stain-blood", ("blood", GARMENT + STAIN_ASKS + ("sheet", "sheets", "bedsheet",
                                                           "bedsheets", "denim", "towel")),
          "Rinse it in cold water straight away, never hot, which sets blood in. Rub in a little "
          "washing-up liquid or soak it in cold salt water, then wash as normal; dried blood "
          "usually comes out after a soak in a biological detergent.",
          # blood in a medical phrase is not laundry: "my blood sugar keeps dropping" was told
          # to rinse it in cold water, and the same holds for a pressure, a test, a group and a
          # donation. Read as the phrase, so "blood on my shirt" keeps this row.
          avoid=NOT_A_GARMENT_SURFACE + ("blood sugar", "blood sugars", "blood glucose",
                                         "blood pressure", "blood test", "blood tests",
                                         "blood group", "blood donor", "blood donation",
                                         "blood transfusion", "blood thinners", "blood clot",
                                         "blood clots")),
    # a school jumper was the shape people wrote and it was a shrug: the second group held
    # "shirt" and "clothes" but nothing a child's uniform is called
    entry("stain-ink", (("ink", "biro", "ballpoint", "marker pen"),
                        ("stain", "shirt", "shirts", "clothes", "pocket", "leak",
                                 "leaked", "spilt", "hands", "fingers", "skin", "jumper",
                                 "jumpers", "cardigan", "blazer", "sweatshirt", "hoodie",
                                 "uniform", "school", "trousers", "socks", "t shirt", "tshirt",
                                 "top", "tops", "shorts", "coat", "whites", "pe kit",
                                 # "how do i get ink off my jeans" and "...off the fabric"
                                 # reached nothing at all: a pen's line usually names the
                                 # garment, and jeans, a dress and a fabric are garments.
                                 "jeans", "denim", "dress", "dresses", "leggings", "vest",
                                 "fabric", "tablecloth", "napkin", "overalls", "dungarees")),
          "Blot, don't rub, then dab a little hand sanitiser or isopropyl alcohol into the mark "
          "with a cotton bud and blot again. Rinse with cold water and wash; hairspray does the "
          "same job in an emergency.",
          avoid=("refill", "printer", "cartridge", "empty")),
    entry("stain-sweat", (("sweat", "sweaty", "deodorant", "antiperspirant"),
                          GARMENT + STAIN_ASKS + ("smell", "smells", "smelly", "stink", "stinks",
                                                  "odour", "odor", "yellow", "white", "armpit",
                                                  "armpits", "gym", "workout", "sports")),
          _sweat_mark,
          avoid=NOT_A_GARMENT_SURFACE + ("why", "health")),
    entry("gum-in-hair", (("chewing gum", "gum"), ("hair", "hairs", "fringe", "beard", "scalp",
                                                   "eyebrow", "eyebrows")),
          "Don't reach for the scissors yet: press ice or a bag of frozen peas on the gum for two "
          "or three minutes until it hardens, then work it out with your fingers and a comb, along "
          "the hair rather than pulling down it. If it "
          "is welded on, massage in a spoonful of cooking oil, olive oil or peanut butter for a "
          "few minutes, slide it off and shampoo twice; peanut butter works on chewing gum on "
          "anything washable. Only a blob right at the fringe is quicker to trim.",
          # bleeding gums, a gum abscess and a denture are the dentist's words, not a hair problem
          # and a stop-smoking question that names gum is the smoking answer's line
          avoid=("dental", "dentist", "tooth", "teeth", "mouth", "gum disease", "abscess",
                 "denture", "dentures", "bleeding", "smoking", "smoke", "quit", "quitting",
                 "nicotine", "cigarette", "cigarettes", "vape", "vaping")),
    entry("stain-gum", (("chewing gum", "gum"), ("clothes", "shirt", "trousers", "fabric", "remove",
                                              "sofa", "carpet", "jeans", "denim", "shoe", "shoes",
                                              # the garment people name instead of "clothes":
                                              # "how do i get gum out of a jumper" fell through to
                                              # the dentist row in the fallback without these
                                              "jumper", "jumpers", "sleeve", "sleeves", "cardigan",
                                              "coat", "jacket", "skirt", "dress", "clothing",
                                              "wool", "t shirt", "tshirt", "leggings", "shorts",
                                              "hoodie", "towel", "bedding", "sheet", "duvet",
                                              # the seats and floors the gum lands on as often
                                              # as a sleeve: "how do i get chewing gum off the
                                              # car seat" reached the dentist's gum row
                                              "car seat", "car seats", "seat", "seats",
                                              "bench", "pavement", "path", "floor", "floors",
                                              "table", "step", "mat", "pram", "buggy",
                                              # a rug is the floor's fabric, and the hard-surface
                                              # row next door holds it out on purpose: "how do i
                                              # get chewing gum off a rug" reached no card at all
                                              # and the illness module answered it with a dentist.
                                              "rug", "rugs", "doormat", "doormats",
                                              "pushchair", "trainer", "trainers", "boot",
                                              "boots", "bag")),
          "Harden it first: press a bag of ice against the gum for a few minutes, then crack it "
          "off with a blunt knife. A little oil or vinegar lifts the last bits from anything "
          "washable.",
          avoid=("gum disease", "tooth", "teeth", "mouth", "dental"),
          # the dentist answers "gum" too, and the surface named in the line is what says this
          # is a stain rather than a tooth
          bias=1),
    entry("deodorant-marks", ("deodorant", ("marks", "white", "shirt", "black", "clothes",
                                            "remove", "streaks")),
          "Rub the white marks off with a pair of clean tights or a damp sponge. Let the "
          "deodorant dry fully before dressing, or switch to a stick or a clear gel and the marks "
          "mostly stop."),

    # --- shoes ---------------------------------------------------------------
    entry("blisters-new-shoes", (("blister", "blisters", "blistered", "blistering", "rubbing",
                                  "rub", "rubbed",
                                  # the same question in the words people use for a stiff pair:
                                  # "how do i break in new shoes" was a punt, and the answer
                                  # this row gives is the breaking-in advice already
                                  "break in", "breaking in", "broke in", "wear them in",
                                  "wear in", "wearing in",
                                  # The softness words are the softness of a shoe, said beside
                                  # it. Bare "soft" and "stiff" are half of "how do i keep
                                  # towels soft", "how do i stop my neck being stiff" and "how
                                  # do i soften brown sugar", and with "how do i" in the second
                                  # half of this key all three were answered "Break new shoes in
                                  # slowly at home with thick socks" - advice for a shoe the
                                  # person never mentioned. The phrase has to carry the shoe.
                                  "shoes softer", "boots softer", "trainers softer",
                                  "shoes are stiff", "boots are stiff", "trainers are stiff",
                                  "shoes feel stiff", "boots feel stiff",
                                  "stiff shoes", "stiff boots", "stiff trainers",
                                  "stiff leather", "leather is stiff",
                                  "soften my shoes", "soften the shoes", "soften new shoes",
                                  "soften my boots", "soften the boots", "soften leather",
                                  "soften the leather", "make my shoes softer",
                                  "make my boots softer"),
                                 ("shoes", "new", "heels", "trainers", "boots", "feet", "stop",
                                  "pop", "burst", "drain", "hot", "spreading", "weeping",
                                  "oozing", "foot", "toe", "toes",
                                  # the plainest ways of asking name no shoe and no pop, so
                                  # "how do i treat a blister" was a one-word match and the burn
                                  # first aid in bot/modules/safety.py took it ("twenty minutes
                                  # under cool running water"). Covering it is what the reply says
                                  # anyway, so the asking words belong in the key.
                                  "treat", "treating", "treatment", "look after", "cover",
                                  "covering", "dress", "dressing", "plaster", "care",
                                  "how do i", "what should i do", "what do i do",
                                  "how can i", "how to",
                                  # "what can i put on a blister" names the blister and asks
                                  # what to apply, which is the plaster this row is about
                                  "put", "put on", "put something", "apply", "ointment",
                                  "cream", "cover it",
                                  # a blister from running is still a plaster question, and main
                                  # sent it to the foot-pain-from-mileage answer
                                  "prevent", "plasters", "running", "runs", "walked", "walking",
                                  "hiking", "gym", "marathon", "socks")),
          _new_shoe_blisters,
          # a blister pack of tablets and a cold sore are not a rubbed heel, and neither is a
          # blister that has already popped: `pop` and `burst` are key words here so that the
          # myth question, which names no shoe, still reaches this entry, and that made a report
          # of one reach it too. A burn thread's follow-up - "the blister has popped, is it still
          # ok" - was answered "break your new shoes in slowly" instead of the care answer the
          # thread had, and so was a sun blister. Each guard is a phrase on purpose: a bare
          # `popped` cuts `pop` out of every line that uses it, which loses the myth answer for
          # "can i burst a blister on my heel".
          avoid=("cold sore", "cold sores", "herpes", "lip", "lips", "fever blister",
                 "blister pack", "packet", "tablets", "pills", "medication", "paint", "varnish",
                 "wood", "wall", "paintwork",
                 "has popped", "have popped", "already popped", "it popped", "they popped",
                 "has burst", "have burst", "already burst", "burst open", "it burst",
                 # a rub for meat is not a rub for a shoe: "how do i make a dry rub" was the
                 # breaking-in advice, because "rub" is this row's word too. Anything that names
                 # the kitchen stands this row down.
                 "dry rub", "spice rub", "rub recipe", "spices", "spice", "spiced", "paprika",
                 "cumin", "chilli powder", "seasoning", "season", "marinade", "barbecue", "bbq",
                 "ribs", "brisket", "steak", "chicken", "pork", "lamb", "roast", "meat",
                 "smoker", "grill",
                 # A towel, a pair of jeans and a load of washing go stiff too, and "soften" and
                 # "stiff" are key words here because a stiff new pair of shoes is this row's
                 # question. "how do i stop my towels going stiff", "how do i soften hard
                 # towels" and "how do i make towels soft again" were all answered "break your
                 # new shoes in slowly at home with thick socks". A line that names the laundry
                 # or the garment is about the cloth, not the shoes, so it goes to its own row
                 # (towel-soft for a towel, musty-laundry for a load) and this one declines.
                 "towel", "towels", "bath towel", "hand towel", "flannel", "flannels",
                 "face cloth", "washcloth", "washing", "laundry", "wash load",
                 "linen", "sheets", "bed sheets", "bedding", "duvet", "duvet cover",
                 "pillowcase", "pillowcases", "clothes", "clothing", "garment", "jeans",
                 "denim", "shirt", "shirts", "t shirt", "t shirts", "tshirt", "jumper",
                 "jumpers", "cardigan", "cardigans", "wool", "woollen", "sweater",
                 "sweaters", "trousers", "tracksuit", "hoodie", "hoodies", "leggings",
                 "curtains", "tumble dryer", "tumble drier",
                 "fabric softener", "softener",
                 # "soft" is a key word here because of a stiff pair of shoes, and an egg has a
                 # soft yolk: "how do i get a soft yolk" was told to cover it with a blister
                 # plaster. A yolk is never a rubbed heel, so the egg stands this row down.
                 "yolk", "yolks", "egg", "eggs", "boiled", "boil",
                 "poached", "scrambled",
                 # "soft" is a key word here because a stiff new pair of shoes is this row's
                 # question, and it is also the soft in a soft reset, a soft light and a soft
                 # close. That made "how do i soft reset my android" answer "cover it with a
                 # proper blister plaster" - it tied with the phone's own card and this row is
                 # read first. A line that names a machine is the machine's, so this row stands
                 # down on the device words.
                 "phone", "iphone", "android", "tablet", "ipad", "kindle", "laptop",
                 "computer", "pc", "screen", "software", "reset", "factory reset", "app",
                 "apps", "wifi", "wi-fi", "router", "battery", "charger", "keyboard",
                 "mouse", "settings", "device", "console", "controller", "printer")),
    # a floor, a job and a pair of feet: the ache is the question, and nothing else in the
    # domains answers it, so the smell, blister and cold-feet lines are left to their own entries
    entry("aching-feet", (("feet", "foot", "heels", "arches", "soles"),
                          ("hurt", "hurts", "hurting", "ache", "aches", "aching", "sore",
                           "pain", "painful", "killing me", "throbbing", "tired")),
          "Roll a frozen bottle of water under the arch for ten minutes and stretch the calf "
          "against a wall twice a day: most foot ache is the calf pulling on the arch, not the "
          "foot itself. Shoes with a firm sole and room in the toe help more than cushions, and "
          "if it is worst first thing in the morning, ask a podiatrist about plantar "
          "fasciitis.",
          # a shoe that does not fit, a swelling, and the ache after new exercise each have an
          # answer that knows more than this one, so the shoes and the swelling go elsewhere
          avoid=("smell", "smelly", "smelling", "smells", "stink", "stinks", "sweat", "sweaty",
                 "sweating", "odour", "odor", "blister", "blisters", "rubbing", "cold",
                 "numb", "tingling", "pins and needles", "shoes", "shoe", "trainers", "trainer",
                 "boots", "boot", "slippers", "sandals", "swollen", "swelling", "swell",
                 "after a run", "after run", "running", "run", "jog", "jogging", "exercise",
                 # the feet in these are the whole person - standing, recovering, nervous - so
                 # no foot ache entry answers "im back on my feet after the flu".
                 "back on my feet", "back on her feet", "back on his feet",
                 "back on their feet", "back on our feet", "back on my legs",
                 "find my feet", "finding my feet", "found my feet",
                 "two left feet", "swept me off my feet", "swept off my feet",
                 "off my feet", "off our feet", "off your feet", "run ragged",
                 "gym", "new exercise", "workout")),
    # Standing all day is a load problem, not an arch one: the plantar card ("roll a frozen bottle
    # under the arch", "worst first thing in the morning") was the answer on main `e43fd80` to
    # "im on my feet all day at work", and it sends a shop worker to a foot remedy for what a mat,
    # a sit-down and a calf pump fix. A heel that hurts on the first steps of the morning is the
    # plantar clue, and that card says so itself.
    entry("standing-all-day",
          (("on my feet", "standing", "stand", "stood", "on my feet all day", "on my feet all shift",
            "standing up all day", "standing all day", "stood all day", "feet", "foot", "legs",
            "heels", "soles"),
           ("all day", "all night", "all shift", "every day", "8 hours", "eight hours",
            "10 hours", "ten hours", "12 hour", "twelve hour", "long shift", "whole shift",
            # a shift said on its own, with the feet already in the line: "dead on my feet
            # after that shift" is the standing row's day
            "shift", "shifts",
            "at work", "for work", "shop floor", "factory", "kitchen", "bar", "hospital",
            "nurse", "hairdresser", "chef", "warehouse", "aching", "ache", "aches", "hurt",
            "hurts", "sore", "tired", "swollen", "killing me", "throbbing", "heavy",
            # A shift is said by its start as often as by its length: "ive been on my feet
            # since six" is the same day as "on my feet all day", and it was answered
            # "You've been on your feet since six - noted", which is the store filing a
            # person's long day as a fact. The clock is the second half of the key, so the
            # line still needs the feet or the standing in it.
            "since six", "since six this morning", "since 6", "since 6am", "since 6 am",
            "since seven", "since seven this morning", "since 7", "since 7am", "since 7 am",
            "since eight", "since 8", "since 8am", "since eight this morning",
            "since nine", "since 9", "since 9am", "since ten", "since 10", "since 10am",
            "since eleven", "since 11", "since five", "since 5", "since 5am",
            "since four", "since 4", "since 4am", "since this morning", "since the morning",
            "since i got up", "since i got in", "since lunchtime", "since noon",
            "since early", "since early doors", "since i started", "all morning",
            "all afternoon", "all evening", "for hours", "for 8 hours", "for ten hours",
            "nine hours", "eleven hours", "since monday")),
          ("Standing all day is a load problem rather than a foot one, and the fixes are cheap: "
           "a rubber mat or a folded towel where you stand, shoes with a firm sole and a little "
           "heel rather than flat pumps or trainers, and sitting down for two minutes every hour "
           "even if it is only on a box. Shift your weight from foot to foot and rise onto the "
           "balls of your feet twenty times an hour - that pumps the calf and keeps blood moving, "
           "which is what stops the ache by the end of a shift. Compression socks help if your "
           "ankles swell. If the heel is worst on your first steps in the morning, that is plantar "
           "fasciitis rather than the standing, and it wants stretching rather than a mat."),
          bias=1,
          guard=_the_feet_are_not_a_height,
          # a swelling, a smell, a blister, a shoe to buy and the ache after a run are five other
          # answers, and a bare "my feet hurt" keeps the arch card it has always had
          ask=("on my feet", "standing", "stand all day", "stood all day", "standing up all day",
               "all day", "all shift", "at work", "for work"),
          avoid=("smell", "smelly", "stink", "sweat", "sweaty", "blister", "blisters", "cold",
                 "numb", "tingling", "pins and needles", "swollen", "swelling", "swell",
                 # the day on the feet is what the line is about; a complaint that names another
                 # part is that part's answer ("ive been on my feet since 6am and my back is
                 # going" was the back card before this row read the clock at all)
                 "my back", "back pain", "shoulder", "shoulders", "neck", "hip", "hips",
                 "diabetic", "diabetes", "swollen ankles", "pregnant", "pregnancy", "shoe shop",
                 "buy", "buying", "which shoes", "best shoes", "trainers to buy", "high heels",
                 "wedding", "after a run", "after run", "running", "jog", "jogging",
                 "marathon", "5k", "parkrun", "first thing in the morning",
                 "when i wake", "when i get up", "out of bed")),
    # The mat was a clause inside `standing-all-day` and nowhere else, so the question people ask
    # before they buy one - "will a mat help the feet or the back", "do standing mats help" - had
    # no answer at all on main `b5e0ece0`; "should i get a standing mat" reached a stain row with a
    # score of 2. The card under it already says a rubber mat or a folded towel helps, so this row
    # answers the picky half - which mat, and what a mat cannot do - and leaves the shift itself to
    # `standing-all-day`.
    entry("standing-mat",
          (("mat", "mats", "matting", "anti fatigue", "anti-fatigue", "antifatigue",
            "standing mat", "rubber mat", "foam mat", "gel mat", "floor mat", "comfort mat"),
           ("standing", "stand", "stand all day", "standing all day", "on my feet", "feet",
            "foot", "heels", "legs", "work", "at work", "shift", "desk", "kitchen", "counter",
            "bench", "till", "factory", "warehouse", "worth it", "worth", "help", "helps",
            "helping", "good", "any good", "buy", "buying", "get", "which", "best", "better",
            "need", "should i", "do i need", "any point", "make a difference",
            "knees", "hips",
            # "anti fatigue mat or insoles" weighed one against the other and the mat words were
            # already in the line, so the comparison itself is the context
            "insoles", "insole", "orthotics", "arch supports", "arch support")),
          ("A mat helps the feet and the legs, not the back: it takes the hardness out of a "
           "concrete floor, and two or three centimetres of rubber or dense foam does that, while a "
           "thin kitchen mat or a gel mat does very little. Stand on it where you actually spend "
           "the shift rather than in front of the counter you visit. For the back the fix is "
           "movement, not a mat: shift your weight from foot to foot, put one foot on a low step, "
           "and sit down for two minutes every hour, because standing still is what a back "
           "dislikes. Firm shoes with room in the toe finish the job, and if your ankles swell by "
           "the evening, compression socks help more than any mat."),
          bias=1,
          # a mat on a bathroom floor, a doormat, a yoga mat and a placemat are four other things,
          # and the shop that sells flooring is not a question about standing
          avoid=("bath mat", "bathroom", "bath", "shower", "doormat", "door mat", "doorway",
                 "welcome mat", "yoga", "pilates", "exercise mat", "gym mat", "play mat",
                 "changing mat", "mouse mat", "placemat", "place mat", "table mat", "rug",
                 "carpet", "laminate", "tiles", "tiling", "flooring", "lino", "vinyl",
                 "slipping", "slips", "non slip", "non-slip", "grass", "seed", "artificial")),
    # "my kids school shoes are too small" was read back as a statement and answered with "I'll
    # remember that", which is the one thing a parent cannot use. The school shoe is named in
    # every real line, so the key is the shoe rather than the child.
    entry("child-shoe-fit",
          (("school shoes", "school shoe", "school trainers", "kids shoes", "kids trainers",
            "childrens shoes", "children's shoes", "childs shoes", "child's shoes",
            "sons shoes", "son's shoes", "daughters shoes", "daughter's shoes",
            "their shoes", "plimsolls", "black shoes", "shoes", "trainers", "feet"),
           # "rub" and "rubbing" stay with `blisters-new-shoes`: a shoe that rubs is a blister to
           # prevent, and a key word of this entry's that the blister entry also holds changed
           # which answer a "how do i stop it hurting" follow-up reached
           ("too small", "small", "tight", "tight shoes", "fit", "fits", "fitting",
            "measure", "measuring", "measurement", "size", "sizes",
            "grow", "grows", "growing", "grown", "outgrew", "replace", "replacing",
            "new", "when to buy", "how often", "check", "checking", "pinch")),
          "Stand them up and feel for a thumb's width between the longest toe and the front of "
          "the shoe, on the bigger foot - one is always bigger. School shoes are usually "
          "outgrown in four to six months at primary age, so check every half term, and never "
          "hand them down: the sole has worn to the other child's foot.",
          # the bare "shoes" and "feet" above are half the key, so a child word has to be in the
          # line: an adult's tight shoe or sore foot is somebody else's answer
          ask=("kid", "kids", "child", "childs", "child's", "children", "childrens",
               "children's", "son", "sons", "son's", "daughter", "daughters",
               "daughter's", "school", "toddler", "boy", "girl", "boy's", "girl's"),
          # a blister, a smell and a scuff each have their own answer, and a shoe that is hurting
          # an adult says nothing about a child's fitting
          avoid=("blister", "blisters", "smelly", "smell", "smells", "stink", "scuff",
                 "scuffed", "polish", "whiten", "white", "clean", "cleaning", "wash",
                 "my shoes are too small", "my trainers are too small", "my boots are too small",
                 "my feet are too small", "heels", "wedding", "work shoes", "safety boots",
                 "steel toe"),
          bias=2),
    # An adult's shoe that is too tight had no row of its own: `child-shoe-fit` stands itself down
    # for "my shoes are too small" on purpose (a child word is its gate), so the deck's own
    # `skf-15` got "Thanks for telling me - I'm here if you want to dig into any of that", and
    # "how do i stretch shoes that are too small" was handed the screen text-size card, which is
    # the one answer that is certainly wrong. What gives and what does not is the whole question,
    # so that is the first sentence.
    entry("shoe-too-tight",
          (("shoes", "shoe", "boots", "boot", "trainers", "trainer", "heels", "loafers",
            "sandals", "footwear"),
           ("too small", "too tight", "tight", "stretch", "stretching", "stretched", "pinch",
            "pinches", "pinching", "snug", "narrow", "squeeze", "squeezes", "squeezing",
            "uncomfortable")),
          "Leather gives about half a size; suede, patent and anything synthetic give nothing, so "
          "a shoe that pinches your toes is the wrong size and a shoe that is merely snug will "
          "loosen. For snug leather, wear thick socks, warm the shoe for 30 seconds with a "
          "hairdryer on low and walk round the house until it is cold, or spray the inside with "
          "half rubbing alcohol and half water and wear it for 20 minutes; for one tight spot take "
          "it to a cobbler, who stretches it on a proper last for about £10 to £20. Send back "
          "anything unworn that pinches, and try the wider fitting in the same size before you go "
          "up a whole size.",
          # a child's shoe is the fitting card, a shoe that rubs is the blister card, a shoe to
          # clean has its own answer, a shoe that hurts after a run is the running card, and a
          # shoe being chosen is the buying card
          avoid=("kid", "kids", "child", "childs", "child's", "children", "childrens", "school",
                 "toddler", "sons", "daughters", "blister", "blisters", "rub", "rubs", "rubbing",
                 "smelly", "smell", "smells", "clean", "cleaning", "polish", "scuff", "scuffed",
                 "mud", "muddy", "suede", "running", "after a run", "parkrun", "marathon",
                 "buy", "buying", "which shoes", "best shoes", "what size", "size of",
                 # a new football boot to break in is the boots card, which says to wear them
                 # round the house an evening at a time - a better answer than a stretcher
                 "break in", "breaking in", "broken in",
                 # a boot card that is about choosing the boot already speaks to the fit, so the
                 # sport and the walk keep their own cards
                 "football", "match", "rugby", "studs", "hockey", "walking", "hiking",
                 "wellies"),
          bias=2),
    # "how do i clean my shoes" and "how do i polish school shoes" were both shrugs, though the
    # leather, the mud and the scuff each had an answer of their own: the general job is brush,
    # wipe, dry away from heat, and a thin coat of polish on black leather.
    entry("shoe-clean-and-polish",
          # "shine", "buff" and "wax" are the words people use for the same job as "polish", and
          # boots are the same leather as shoes: "how do i shine my shoes", "how do i polish my
          # leather boots" and "how do i keep my boots waterproof" were all a shrug, and "do i
          # need to wax my boots" was answered with the first-shoes card for a baby.
          (("shoes", "shoe", "school shoes", "school shoe", "black shoes", "school trainers",
            "boots", "boot", "loafers", "brogues", "oxfords", "footwear"),
           ("clean", "cleaning", "polish", "polished", "polishing", "shiny", "dirty", "smart",
            "shine", "shining", "buff", "buffed", "buffing", "wax", "waxed", "waxing",
            "waterproof", "waterproofing", "proofing", "look after", "care",
            # a stain on a leather shoe is the same job as a polish: wipe, then dab, then
            # condition. Without these, "how do i get a stain off my boots" was a search shrug.
            "stain", "stains", "stained", "spilt", "spill", "spilled")),
          "Brush the dust off and wipe them with a barely damp cloth, then dry them away from a "
          "radiator, because heat cracks leather. Work a thin coat of cream polish in with a cloth "
          "in small circles, leave it ten minutes, brush it off and buff hard with a soft cloth - "
          "several thin coats beat one thick one. For boots that see rain, finish with a wax "
          "polish rather than a cream, and give them a fresh coat at the start of every winter.",
          # the leather, the suede, the mud, the white trainer and the smelly shoe each answer for
          # themselves, and a shoe that does not fit is not a cleaning job
          avoid=("suede", "nubuck", "mud", "muddy", "smelly", "smell", "smells",
                 # a scuff is `leather-scuff`'s own answer, with its shoe cream and its rag
                 "scuff", "scuffed", "scuffs", "scratch", "scratched", "mark", "marks",
                 "stink", "white", "whiten", "yellow", "trainers", "trainer", "sneakers",
                 "canvas", "converse", "washing machine", "wash", "too small", "too tight",
                 "fit", "fits", "size", "measure", "grow", "blister", "how much", "cost",
                 "price", "buy", "new pair", "insoles"),
          bias=2),
    # "how do i dry wet boots" was answered with "A musty car is water: lift the mats and press a
    # hand into both footwells", because a car's boot and a pair of boots are one word to the
    # matcher. "how do i dry my trainers" was a search hedge, and "my shoes are soaking wet",
    # "wet shoes overnight" and "my boots are soaked through" were all small talk. The drying is
    # its own job, and it is the one thing people get wrong: heat.
    entry("wet-shoes-drying",
          (("shoes", "shoe", "trainers", "trainer", "boots", "boot", "sneakers", "plimsolls",
            "wellies", "footwear", "pumps", "loafers", "walking boots", "football boots",
            "work boots", "school shoes",
            # "leather" is on the car's key too (its seats), so a wet leather boot was still the
            # musty car even after the car stopped keying the bare word "boot"
            "leather boots", "leather shoes", "leather boot", "leather shoe"),
           ("wet", "soaked", "soaking", "soak", "drenched", "soggy", "damp", "sodden",
            "rain", "rained", "raining", "puddle", "puddles", "drying", "dry", "dried",
            "dries")),
          "Take the insoles out, stuff the toes with newspaper and stand them somewhere warm and "
          "airy to dry slowly - never on a radiator, in an airing cupboard or in the tumble dryer, "
          "because heat cracks leather and shrinks trainers. Change the paper after an hour or so "
          "and give them a full day, since half-dry is what makes them smell next. To keep the "
          "rain out next time, wax leather boots while they are clean and dry and spray fabric "
          "ones with a proofer.",
          # the smell, the mould, the polish and the choosing of a pair are each their own
          # question, and a car's boot is a place, not a pair of boots
          avoid=("smell", "smells", "smelly", "smelling", "stink", "stinks", "odour", "odor",
                 "reek", "mould", "mouldy", "mold", "moldy", "mildew", "mildewy",
                 "polish", "shine", "shiny", "scuff", "scuffed", "clean", "cleaning",
                 "white", "canvas",
                 "buy", "buying", "which", "fit", "fits", "size", "blister", "cheap",
                 "price", "cost", "shop", "brand",
                 # choosing a pair is the buying question, and it is said with "get":
                 # "what boots should i get for playing in the rain" was the newspaper answer
                 "should i get", "what boots", "best boots", "good boots", "what trainers",
                 "best trainers", "what shoes", "best shoes", "recommend", "worth it",
                 "car", "cars", "van", "trunk", "boot of", "in the boot", "boot floor",
                 "boot space", "car key"),
          bias=2),
    entry("smelly-shoes", (("smelly", "smell", "smells", "smelling", "stink", "stinks", "odour",
                            "odor", "reek"),
                           ("shoes", "trainers", "boots", "feet", "plimsolls", "slippers",
                            "sandals", "wellies", "football boots", "work boots"),
                           # the pair of boots a person owns, which is not the boot of a car:
                           # "my" and "these" are what tells the two apart, because the matcher
                           # reads boots and boot as one word
                           ("my boots", "my shoes", "my trainers", "these boots",
                            "these shoes", "pair of boots", "pair of trainers")),
          "Take the insoles out and let the shoes air overnight, and sprinkle bicarbonate of soda "
          "inside to soak up the smell. Wear them on alternate days, wash or replace the insoles, "
          "and most trainers survive a cold machine wash.",
          # "get rid of the smell in my boots" was the football boots' answer, because that row
          # also keys on "boots"; the smell is the subject here. "The boot" on its own is a car
          # boot, which is the place-smell answer in home.py
          # a boot question of another kind is not this one: shoes that squeak, a pair to pack
          # for the gym and the smell of feet each have an answer that knows more
          # A bare "take" here cost the commonest way of asking - "how do i take the smell out of
          # my trainers" - the answer, because the matcher reads take and taking as one word and
          # the veto beat the key. The smell words already carry "the smell out of", so only the
          # words that belong to another question are left: a shoe that squeaks, a pair to pack.
          avoid=("car", "cars", "van", "my car", "estate car", "squeak", "squeaks",
                 "squeaking", "squeaky", "noise", "noisy", "rub", "rubbing", "gym",
                 # a pair that has been through the wash and still smells wants the washing
                 # answer, which says what to scrub them with and what the machine does
                 "after washing", "even after washing", "washed them", "been in the wash",
                 "put them in the wash", "in the washing machine",
                 "feet", "foot",
                 # the bare word "sweat" was here to keep a person's own sweating off this row,
                 # and it also kept off "how do i get sweat smell out of trainers", which is a
                 # shoe question with the smell called sweat. The person is in the phrases now.
                 "i sweat", "i sweat a lot", "sweat a lot", "sweat so much", "sweat when",
                 "sweating so much", "why do i sweat", "why am i sweating", "my sweat",
                 "sweaty after", "sweat rash", "excessive sweating", "hyperhidrosis"),
          # The pair-of-boots phrases in the key cover two words of a line on their own ("my
          # trainers"), which was enough to answer "my trainers are falling apart, what should i
          # get" and "white marks on my shoes from the salt": a shoe question, not a smell one.
          # The gate is the smell word itself, so this row only ever answers a line about smell.
          ask=("smell", "smells", "smelly", "smelling", "stink", "stinks", "stinking",
               "odour", "odor", "reek", "reeks", "reeking", "whiff", "pong", "pongs",
               "smelled", "smelt"),
          bias=2),
    entry("leather-scuff", (("leather", "boots", "shoes"),
                            ("scuff", "scuffed", "scratch", "scratched", "mark", "marks")),
          "Work a little matching shoe cream or a drop of olive oil into the scuff with a rag, in "
          "circles, and let it dry before buffing with a soft cloth. Shoe trees keep the shape and "
          "stop the creases that turn into cracks.",
          # a cat's scratch on a leather chair is the scratching answer, not shoe cream on a
          # boot: the key is any leather scratched, and a chair is where the animal was.
          avoid=("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "rabbit",
                 "sofa", "couch", "settee", "armchair", "chair", "furniture", "car seat")),
    # The leather-scuff row holds a chair and a sofa out, because a cat's claw is that row's
    # business; a scuff on a leather sofa is not, and it was the search shrug. The fix is a cream
    # and a cloth, and the person is not asking who scratched it.
    entry("leather-sofa-scuff",
          (("leather sofa", "leather settee", "leather couch", "leather chair",
            "leather armchair", "leather look sofa", "sofa", "settee", "couch", "armchair",
            "chair", "suite"),
           ("scuff", "scuffs", "scuffed", "scratch", "scratches", "scratched", "mark", "marks",
            "marked", "worn", "wear", "faded", "rubbed", "peeling", "peeled", "flaking",
            "cracked", "crack", "restore", "cover up", "touch up", "get off", "get it off")),
          _leather_mark,
          # "how do i get a scratch off a leather chair" reached the faulty-goods card on
          # "scratch" and "chair" before this row existed, and a scuff is not a fault to reject
          bias=2,
          # a cat's claw, a dog's teeth, a stain and the regular care of leather each have an
          # owner in this file: this row is the mark on a piece of furniture, and nothing else
          avoid=("cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "rabbit",
                 "stain", "stains", "stained", "spilled", "spilt", "wine", "coffee", "vomit",
                 "sick", "urine", "pee", "poo", "mould", "mold", "buy", "buying", "which",
                 "best", "second hand", "price", "cost", "worth",
                 # the care of the thing, and the same leather carried as clothing or kit, are
                 # `leather-care`'s and the bags' rows: they answer with a cloth, a soap and a
                 # conditioner, which is what a jacket, a bag and a pair of boots are for
                 "clean", "cleaning", "wash", "washing", "look after", "care", "condition",
                 "conditioner", "polish", "soften", "boots", "shoes", "trainers", "jacket",
                 "trousers", "skirt", "bag", "handbag", "belt", "wallet", "car seat",
                 "fabric", "cloth sofa", "velvet", "leather care",
                 # a sofa that arrived scratched is a delivery, not a scuff to polish:
                 # `money.damaged-on-delivery` is the delivery note and the refund, and
                 # `tests/test_a_cat_is_not_a_parcel.py` failed on "the sofa arrived scratched"
                 # because this row took it on "sofa" and "scratched"
                 "arrived", "arrives", "arriving", "delivered", "delivery", "deliveries",
                 "turned up", "turns up", "shipped", "courier", "parcel",
                 # the phrases, not a bare "came": "a scratch that came from my jeans" is still
                 # a scuff to treat, and it was answered with the delivery note
                 "came chipped", "came damaged", "came scratched", "came dented", "came broken",
                 "came marked", "came with a", "came with the", "come damaged", "come chipped",
                 "damaged", "damage", "faulty", "refund", "return", "returned", "reject",
                 "replacement", "warranty", "guarantee", "complaint", "complain")),
    # "how do I whiten my trainers" and "my trainers have gone yellow" were the shrug: the entry
    # knew "white" but not the verbs and states people use for getting them white again.
    entry("white-trainers", (("trainers", "sneakers", "plimsolls", "canvas shoes", "converse",
                               "vans", "white shoes", "daps"),
                             ("white", "whiten", "whiter", "whitening", "clean", "dirty",
                              "yellow", "yellowed", "yellowing", "grey", "dingy", "grubby",
                              "scuffed", "bright", "restore", "like new", "wash",
                              "washing machine",
                              # a mark on a trainer is a cleaning job, and the method is the one
                              # below: brush it dry, then warm water and washing-up liquid. The
                              # line usually arrives as a stain question ("how do i get a stain
                              # out of my trainers"), so the stain words belong in this key
                              # rather than only in "clean".
                              "stain", "stains", "stained", "mark", "marks", "marked",
                              "spot", "spots")),
          "Take out the laces and insoles, brush off dry dirt, then scrub with a soft brush, warm "
          "water and a little washing-up liquid, or wash them in a pillowcase on a cold cycle. "
          "Bicarbonate of soda on a damp old toothbrush is the stronger version for white canvas, "
          "and a melamine sponge or whitening toothpaste takes the scuffs off the rubber sole. Dry "
          "them in the shade with newspaper inside, because heat and sun turn white rubber yellow, "
          "and once it has gone properly yellow nothing brings it back.",
          # a gym kit, a personal trainer and a white shirt or wall are other lines
          avoid=("gym", "personal trainer", "dog trainer", "suede", "leather", "shirt",
                 "t-shirt", "tshirt", "blouse", "wall", "walls", "paint", "paintwork",
                 "ceiling", "bedding", "curtains",
                 # "vans" in the key is the shoe brand, and the plural repair made it read as a
                 # removal van: "how do i get a washing machine into a van" was told to take the
                 # laces and insoles out. A line about moving something is not a trainer.
                 "into a van", "into the van", "in a van", "a van", "hire a van", "moving house",
                 "moving home", "removal", "removals", "sack truck", "transit", "upstairs",
                 "downstairs", "into the washing machine", "washing machine into"),
          bias=2),

    # --- hair, skin and personal care ----------------------------------------
    # A frizz in the rain and a frizz after washing are the same complaint as a plain "frizzy
    # hair", and neither was answered: the key needed "hair" or "humidity" and both lines said
    # "frizz" with the weather or the wash instead.
    entry("frizzy-hair", (("frizzy", "frizz", "flyaways", "fly away", "fluffy hair"),
                          ("hair", "stop", "humidity", "smooth", "less", "tame",
                           "rain", "raining", "rainy", "wet", "damp", "misty", "humid",
                           "weather", "after washing", "after i wash", "washing", "drying")),
          "Squeeze a leave-in conditioner or a little hair oil through damp hair and dry it on low "
          "with the nozzle pointing down the hair. A smooth cotton T-shirt instead of a towel and "
          "a wide-tooth comb cut frizz more than most products do."),
    # The other half of "hair" plus a styling word: how it sits, which no row covered. A question
    # about volume and a question about flat hair are one job, and a curly head needs a different
    # routine from a straight one, so both are habits with their own card. Before these, "how do i
    # stop my hair looking flat" and "how do i look after curly hair" were the trim schedule.
    entry("hair-volume", (("volume", "lifeless", "limp", "thin looking", "no body",
                           "looks thin", "looks limp", "needs body", "more body", "flat"),
                          ("hair", "hairs", "head", "roots", "fringe", "bob", "bangs",
                           "look", "looks", "stop", "more", "get", "add")),
          "Volume is weight at the roots, so condition only the ends and rinse the roots well, "
          "then dry the hair upside down and rough the roots with your fingers: a little mousse or "
          "dry shampoo at the roots, lifted away from the scalp as it dries, holds it there. A cut "
          "with a few layers gives it something to sit on, and heavy conditioner or a hot iron flat "
          "against the scalp takes it straight back down.",
          # a speaker, a phone and a television have a volume too, and a beard, a moustache and
          # a pair of eyebrows are trimmed rather than styled for volume
          avoid=("speaker", "speakers", "phone", "tv", "television", "music", "sound", "noise",
                 "alarm", "control", "remote", "laptop", "headphones", "radio",
                 "beard", "beards", "moustache", "mustache", "stubble", "eyebrows", "eyebrow"),
          guard=_a_hair_line),
    # Wanting hair to lie down is the opposite of wanting volume, so it is its own row: the volume
    # card told "how do i get my hair to lie flat" to dry it upside down and lift the roots away
    # from the scalp, which is three sentences of how to do the reverse of what was asked.
    entry("hair-flat", (("lie flat", "lies flat", "sticking up", "sticks up", "sticking out",
                         "sticks out",
                         "cowlick", "cowlicks", "wont lie flat", "wont stay down",
                         "doesnt lie flat", "doesnt stay down", "wont go down"),
                        ("hair", "hairs", "head", "roots", "fringe", "bob", "bangs", "look",
                         "looks", "stop", "get", "make", "keep", "go")),
          "Press it down rather than lift it: condition the lengths, dry it with the brush pointing "
          "down and finish with a hot iron flat against the scalp or a drop of serum. Leave the "
          "mousse and the dry shampoo alone, because they are what holds hair up, and ask for a "
          "blunt one-length cut if it will not stay down, since layers are what make it stand up.",
          # hair that *looks* flat is thin and flat, which is the volume card's answer, not the
          # pressing-down one: only "lie flat" and "sticking up" are this card's
          avoid=("looking flat", "looks flat", "look flat", "is flat", "so flat", "very flat",
                 "too flat", "feels flat", "went flat", "gone flat", "gets flat",
                 # a tyre, a battery, a drink and a flat to live in all have a flat of their own
                 "tyre", "tyres", "tire", "tires", "battery", "beer", "coke", "fizzy", "drink",
                 "champagne", "prosecco", "bike", "car", "van", "screen", "mattress", "roof",
                 "pillow", "balloon", "paint", "floor", "flatmate", "flatmates", "flat pack",
                 "flat-pack", "flat white", "flat rate", "rent", "landlord", "beard", "beards",
                 "moustache", "mustache", "stubble", "eyebrows", "eyebrow", "speaker",
                 "speakers", "tv", "television", "phone", "laptop",
                 # "wont go down" is in the key above, and now that the two spellings of a
                 # contraction are the same words it also reads "will not go down". Water, a
                 # price and the swelling on a knee go down without any hair in the line: "the
                 # sink is blocked and the water will not go down" was answered with pressing
                 # the lengths down instead of the plughole.
                 "water", "sink", "drain", "drains", "plughole", "pipe", "pipes", "tap", "taps",
                 "toilet", "loo", "blocked", "blockage", "plunger", "boiler", "radiator",
                 "pressure", "price", "prices", "cost", "costs", "cheaper", "inflation",
                 "swelling", "swollen", "knee", "ankle", "temperature", "fever", "sun")),
    entry("greasy-hair", (("greasy", "oily", "limp"),
                          ("hair", "wash", "shampoo", "less", "roots", "every day")),
          "Shampoo just the roots, condition only the ends, and finish with cool water. Washing "
          "with a harsh shampoo every day makes oil come back faster, so try every other day for "
          "a fortnight and it usually settles.",
          # An adjective is not a subject. "greasy" plus "wash" was enough, so "does washing soda
          # work on a greasy tray" got shampoo advice; the entry is about hair, so the line has to
          # say hair, or a word only hair uses.
          ask=("hair", "shampoo", "scalp", "roots", "haircut", "fringe", "bangs", "curls")),
    # "flakes" and "flaky" are the same complaint as dandruff and worth a key of their own: on its
    # own "how do i get rid of flakes" matched one key word and nothing else, so it was a hedge.
    entry("dandruff", (("dandruff", "flakes", "flake", "flaky", "flakiness"),
                       ("hair", "shampoo", "head", "scalp", "itchy", "have", "has", "got",
                        "ive", "i've", "my", "is", "it", "really", "bad", "worse", "a lot",
                        "always", "so much") + ASK_ABOUT),
          "Use an anti-dandruff shampoo with zinc pyrithione or ketoconazole two or three times a "
          "week and leave it on the scalp for five minutes. If it's red, sore or no better after a "
          "month, ask a pharmacist about a scalp condition rather than buying more products.",
          # "flaky" is a pastry and a fish as well as a scalp: those keep their cooking answers
          avoid=("pastry", "pie", "pies", "crust", "bake", "baking", "cook", "cooking", "recipe",
                 "recipes", "fish", "chocolate", "bread", "skin", "paint", "wall", "walls",
                 # flaky nails and a flaky scalp are different complaints and the plain-report
                 # words below would otherwise let a nail line in
                 "nail", "nails", "toenail", "toenails", "fingernail", "fingernails",
                 # a flaky face is dry skin, not dandruff (deft-lime)
                 "face", "facial", "cheeks", "cheek", "forehead", "chin",
                 # a flaking tattoo is a healing tattoo, and its own two cards answer it
                 "tattoo", "tattoos")),
    # --- hair colour -----------------------------------------------------------
    # Dyeing it, bleaching it and covering the roots is one of the commonest everyday asks
    # there is, and it reached nothing: every hair row here and in science.py stands down on
    # "dye", "colour" and "bleach" (they are another question), so "how do i dye my hair at
    # home" was a shrug and "how do i cover my grey roots" was the plant-roots card. One row
    # per decision, the way the hair-care rows above are split: putting colour in, lifting it
    # out, the roots, taking a colour back off, and hair that is already damaged.
    # A parent asking about a 14 year old's hair is not asking how to colour their own:
    # "my daughter is 14 and wants to dye her hair" was answered with the shade and patch-test
    # card for an adult doing a box dye.
    entry("hair-colour-teen",
          (("daughter", "son", "teenager", "teenagers", "teen", "child", "kid", "my girl",
            "my boy", "year old", "13 year old", "14 year old", "15 year old", "16 year old",
            "12 year old", "is 13", "is 14", "is 15", "is 16"),
           ("hair dye", "hair colour", "hair color", "dye", "dyed", "dyeing", "bleach",
            "highlights", "streaks", "permanent", "semi permanent", "semi-permanent",
            "wash out",
            # the colour is only this row's when it is the colour of the hair: a bare "pink"
            # beside "daughter" is pink shoes, and "covered in blue paint" was answered with a
            # semi-permanent hair colour
            "pink hair", "blue hair", "green hair", "purple hair", "red hair", "blonde hair",
            "blond hair", "unnatural colour", "unnatural color", "bright colour",
            "colour her hair", "colour his hair", "color her hair", "color his hair")),
          "Let them start with a semi-permanent or a wash-out colour: it fades out in six to "
          "eight washes, so a mistake costs a month rather than a year, and it needs no bleach. "
          "Read the box together for the 48-hour patch test and do that first, then colour over a "
          "basin with gloves and an old towel, and keep anything lighter than two shades of their "
          "own colour for a salon - a home bleach on a teenager is what goes orange. Check the "
          "school's rule on 'unnatural' colours before you buy, because that is the argument you "
          "actually want to avoid.",
          # the ask words are the question words and the report words, because a parent very
          # often tells you the thing rather than asks it: "your daughter wants highlights" was
          # answered "Noted: your daughter wants highlights"
          ask=("my", "your", "can", "should", "is", "what", "how", "would", "want", "wants",
               "wanted", "asked", "asking", "keeps asking", "is asking", "has asked"),
          avoid=("tattoo", "tattoos", "piercing", "piercings", "ear", "ears", "belly button",
                 "nails", "makeup", "make up", "prom", "wedding", "grey", "gray",
                 "carpet", "sofa", "towel stain", "off my skin", "off my hands",
                 "shampoo", "haircut", "cut her hair", "cut his hair")),
    entry("hair-colour-home",
          (("hair", "hair dye", "box dye", "roots"),
           ("dye", "dyed", "dyeing", "dye my hair", "colour it", "color it", "tint",
            "change my colour", "pink", "red", "purple", "blue", "green", "ginger",
            "auburn", "black", "brown", "at home", "myself", "box dye", "hair",
            "fading", "fade", "last longer", "keep the colour", "keep the color",
            "without bleach", "no bleach", "instead of bleach")),
          _hair_colour_home,
          ask=("hair", "dye", "dyed", "dyeing", "tint", "colour", "color", "box dye",
               "without bleach", "no bleach"),
          # washing it, cutting it, growing it and why it goes grey are the rows around this
          # one, and a dye for a beard, a cushion cover or a jacket is not a head of hair
          avoid=("shampoo", "wash", "washing", "cut", "trim", "fringe", "grow",
                 "eyebrow", "eyebrows", "eyelash", "eyelashes", "beard", "moustache",
                 "dog", "cat", "cushion", "curtain", "fabric", "jacket", "jeans", "shirt",
                 "wood", "leather", "egg", "easter", "tie dye", "tie-dye", "paint",
                 # "can i bleach my hair at home" is the row below, and "at home" caught it here
                 "bleach my hair", "bleaching my hair",
                 # dye that is on the skin, the basin or the towel is the stain row's question
                 "off my skin", "off my hands", "off my face", "on my skin", "on my hands",
                 "basin", "sink", "hairline", "my hands",
                 # "how do i remove hair dye from my skin" and "hair dye on my forehead how do
                 # i get it off" name the skin without any of the phrases above, so the box-dye
                 # card answered both with shade advice
                 "my skin", "the skin", "from my skin", "my face", "my forehead", "my ears",
                 "my neck", "get it off",
                 # the towel, the basin and the tiles are the stain row's question
                 "towel", "towels", "tile", "tiles",
                 # and so are the carpet, the sofa and the floor: "how do i get hair dye off the
                 # carpet" was answered with how to colour your hair, which is not the question
                 "carpet", "carpets", "rug", "rugs", "sofa", "settee", "floor", "floors",
                 "bath", "bathroom", "worktop", "worktops", "counter", "stain", "stained",
                 # hair that is already wrecked is the repair row's question, not another dye:
                 # "i dyed it myself and my hair is damaged" was getting the how-to-dye card
                 "damaged", "damage", "fried", "mushy", "snapping", "breaking off",
                 "ruined", "wrecked",
                 # hair that has gone green in a pool is the chlorine's doing, not a dye
                 "swimming", "swim", "pool", "chlorine")),
    entry("hair-colour-bleach",
          (("hair", "roots", "bleach", "bleached", "bleaching", "blonde", "blond", "highlights",
            "highlight", "platinum", "brassy", "orange", "toner"),
           ("bleach", "bleached", "bleaching", "blonde", "blond", "lighter", "lighten",
            "lightening", "highlights", "highlight", "platinum", "lift the colour",
            "go blonde", "go lighter", "do highlights", "highlights at home", "hair",
            "brassy", "brassiness", "orange", "tone down", "toner", "to blonde",
            "black to blonde", "from black", "from dark")),
          "Bleach lifts your own colour out rather than adding blonde, so a dark head comes up "
          "orange first and needs a second session weeks later, or a toner, to finish it: a toner "
          "is a weak purple or blue dye that cancels the yellow and lasts a few weeks. Roots lift "
          "fastest in the scalp's heat, so check them at 20 minutes and never go past the packet "
          "time, with a strand test on a hidden piece before the rest. Never bleach over henna or "
          "a box dye with metallic salts, which can turn hair green and burn, and never bleach "
          "hair that is already lightened. For a full change or highlights, a salon costs less "
          "than the repair after a home job.",
          ask=("hair", "bleach", "bleached", "bleaching", "blonde", "lighter", "lighten",
               "highlights", "henna", "go"),
          # "can i dye it without bleach" is the dye job's question, and it is answered by the
          # row above, which says what a box dye will and will not do on its own.
          # 2, not 1: _rank gives a point for every key word that exactly one row in the domain
          # uses, and hair-colour-teen now says dye, dyed, dyeing and highlights too, so this
          # row lost that point and "how do i dye my hair blonde" fell to the box-dye card.
          bias=2,
          avoid=("bathroom", "kitchen", "toilet", "loo", "mould", "mold", "mildew", "drain",
                 "white shirt", "whites", "laundry", "washing machine", "tea towel", "towel",
                 "bedding", "sheets", "wood", "floor", "grout", "tile", "tiles", "dog",
                 "cat", "teeth", "tooth", "skin", "without bleach", "no bleach",
                 # a wrecked head, roots due, and getting a colour back off are the rows either
                 # side of this one, and each says something this answer does not
                 "dye out", "colour out", "color out", "get it out", "remove", "strip",
                 "damaged", "damage", "fried", "ruined", "regrowth", "touch up", "touch-up",
                 # how people actually say a wrecked head: "my hair is snapping after bleaching
                 # it myself" met this row, whose second sentence is that a dark head needs a
                 # second session - advice to bleach again, on hair that is already breaking
                 "snapping", "snapped", "snaps", "breaking", "breaking off", "chewing gum",
                 "mushy", "straw",
                 # a colour named in the line is a dye job, not the bleach that a light shade
                 # might need later
                 "pink", "red", "purple", "blue", "green",
                 # hair wrecked by someone else is a claim, not a how-to: "the hairdresser
                 # bleached my hair and it snapped" is the botched-job card's question
                 "hairdresser", "hairdressers", "salon", "barber", "they bleached",
                 "she bleached", "he bleached", "they dyed", "she dyed", "he dyed",
                 # green hair is the chlorine or the copper in the water, not a dye job
                 "swimming", "swim", "pool", "chlorine",
                 # "does bleaching cause hair loss" asks about hair coming out, and this row has
                 # no answer for that: the shedding answer does, and it was losing the line
                 "hair loss", "losing my hair", "lose my hair", "losing hair", "thinning",
                 "shedding", "bald", "going bald", "come out",
                 # "how do i touch up a stone chip on my car" is bodywork: "touch up" is in this
                 # row's ask, so a paint chip was told about roots and regrowth
                 "car", "cars", "van", "vans", "bonnet", "bumper", "stone chip", "stone chips",
                 "paint", "paintwork", "bodywork", "alloy", "alloys", "lacquer")),
    entry("hair-colour-roots",
          (("roots", "root", "regrowth", "root touch up", "root touch-up", "grey roots",
            "gray roots", "grey hair", "gray hair", "colour", "color", "dye", "dyed",
            "touch up"),
           ("grey", "gray", "white", "dye", "dyed", "colour", "color", "cover", "touch up",
            "how often", "often", "regrowth", "showing", "showing through",
            "without dye", "no dye", "without dyeing")),
          "Colour the new growth every four to six weeks and leave the rest alone, because "
          "overlapping permanent dye on hair that already has it makes the ends darker and drier "
          "each time. For grey, go one shade lighter than you think you want, since grey takes "
          "colour cooler and darker than the swatch. A root spray or a wand made for it covers a "
          "few days of regrowth without a whole dye job.",
          ask=("roots", "root", "regrowth", "grey", "gray", "dye", "colour", "color",
               "cover", "touch up"),
          # a plant's roots, a tooth and a pipe under the lawn are other rows, and the science
          # row on why hair goes grey is a different question from what to do about it
          avoid=("plant", "plants", "tree", "trees", "tooth", "teeth", "dental", "canal",
                 "pipe", "pipes", "drain", "lawn", "shrub", "bush", "cuttings", "propagate",
                 "beetroot", "carrot", "parsnip", "ginger", "why", "what makes",
                 # a shirt, a towel or a cushion is not a head of hair
                 "shirt", "t-shirt", "top", "clothes", "fabric", "jeans", "cushion", "curtain",
                 "tie dye", "tie-dye", "egg", "eggs", "wood", "leather", "shoes", "sofa",
                 # a sock, a scarf and a pair of trousers are worn rather than dyed: "what colour
                 # socks with grey trousers" was answered with touching up the roots
                 "sock", "socks", "scarf", "trousers", "trouser", "shirt", "jumper", "cardigan",
                 # "touch up" is in this row's ask and its key, so "how do i touch up a scratch
                 # on my car" answered itself with roots and regrowth: a car's paint is the
                 # cars row's business, and a scratch is nobody's hair
                 "car", "cars", "van", "vans", "bonnet", "bumper", "bodywork", "paintwork",
                 "scratch", "scratches", "scratched", "stone chip", "stone chips", "lacquer")),
    # "The blame half of this stays with the refund card in `consumer.py`: "the barber cut it too
    # short", "she cut my hair too short" and "the hairdresser cut too much off" are a complaint
    # about somebody's work, and a test there names `services-ruined` for them, so the key here
    # is the softer shape - a cut they are unhappy with and no one blamed yet, which is the
    # commoner way people bring it up ("i got a bad haircut", "i hate my new haircut").
    # A bad haircut is a small, fixable thing, and the rows around it did not see it at all:
    # "i got a bad haircut" and "i got a bad dye job" were congratulated ("Nice one"), "my
    # haircut is awful" and "my hair dye went wrong" got the consumer refund card, "i hate my
    # new haircut" got a sympathy nod and "how do i fix a bad haircut" got the trim schedule.
    # The two jobs in it - a cut that needs evening up and a colour that needs correcting - are
    # one card, because it is the same visit back to the same person.
    entry("bad-haircut",
          (("bad haircut", "my haircut", "my new haircut", "haircut gone wrong",
            "haircut went wrong", "haircut is awful", "haircut looks awful", "terrible haircut",
            "awful haircut", "botched haircut", "hate my hair", "hate my haircut",
            "hate my new haircut", "regret cutting my hair", "regret my haircut",
            # a length and a "bad cut" are not a complaint about the hair on its own: "cut too
            # much off" and "too short" are the refund card's words (a test there names those
            # lines), "my trousers are too short" is a hem, and "this steak is a bad cut" is
            # dinner
            "bad dye job", "dye job", "dye went wrong", "colour went wrong", "color went wrong",
            "dye came out wrong", "colour came out wrong", "color came out wrong",
            "patchy colour", "patchy color", "patchy dye", "messed up my hair",
            "nothing like i asked", "not what i asked for",
            "cut my fringe", "fringe too short", "bangs too short"),
           # a complaint about a cut is a request for what to do next, so most lines have one
           # of these in them; the key is the cut, and this is only to keep the row off a line
           # that says "bad haircut" in passing while talking about something else
           ("fix", "fixed", "fixing", "now", "what", "how", "should", "do", "can", "help",
            "advice", "again", "instead", "my", "is", "it", "ive", "i've", "got", "have",
            "had", "am", "went", "gone", "off", "much", "too", "really", "so", "very",
            "look", "looks", "looking", "short", "wrong", "badly", "bad")),
          _the_bad_haircut,
          ask=("hair", "haircut", "cut", "dye", "dyed", "colour", "color", "barber",
               "hairdresser", "salon", "fringe", "bangs", "trim", "fixed"),
          # the refund card in `consumer.py` also fits "my hair dye went wrong", and it is the
          # right card for "i want my money back" - but for a bad cut what a person wants first
          # is how to get it put right, so this row outranks it on the lines that are about the
          # hair rather than the money. The refund lines keep their card: they say refund,
          # complain, compensation or money back, and those words are avoided here
          avoid=("refund", "refunds", "money back", "compensation", "complain", "complaint",
                 "trading standards", "small claims", "sue", "solicitor", "charge", "charged",
                 "cost", "costs", "price", "prices", "how much"),
          bias=3),
    entry("hair-colour-remove",
          (("hair",), ("get the dye out", "get the colour out", "get the color out", "too dark",
                       "colour remover", "color remover", "strip the colour", "strip the color",
                       "fade the colour", "fade the color", "reverse the dye", "undo the dye",
                       "went too dark", "came out too dark", "get red dye out", "get black dye out",
                       # "what's the difference between semi permanent and permanent" is this
                       # row's subject (what comes out and what washes out), not the box-dye one
                       "difference between", "semi permanent", "semi-permanent", "semipermanent")),
          "A permanent colour cannot be washed out: a colour remover, about ten pounds, shrinks the "
          "dye molecules so they rinse away, and it works far better on a fresh job than on one "
          "that has been there months. A semi-permanent fades by itself in six to eight washes, "
          "faster with a clarifying shampoo and warm water. Neither will rescue hair that has also "
          "been bleached, and a salon correction is the honest answer for a big mistake.",
          ask=("hair", "dye", "colour", "color", "bleach"),
          # a red wine stain, a red sauce and a red-eye are not a dye job
          avoid=("wine", "sauce", "stain", "carpet", "shirt", "top", "clothes", "fabric",
                 "eyes", "eye", "photo", "tea", "curry", "salsa", "tomato",
                 "off my skin", "off my hands", "on my skin", "basin", "hairline")),
    entry("hair-colour-damaged",
          (("hair",), ("damaged", "damage", "fried", "mushy", "breaking off", "snapping",
                       "burnt", "ruined", "wrecked", "straw", "falling out after bleaching")),
          "Stop lightening it now: hair that feels like chewing gum has lost its protein and cannot "
          "be repaired, only managed until it grows out. A protein or bond-building mask once a "
          "week, a leave-in conditioner, no heat and no tight bands, and an inch off the ends if "
          "they are snapping. Wait four to six weeks before any more colour, and get a salon to do "
          "a strand test before the next lift.",
          ask=("hair", "bleach", "bleached", "dye", "dyed", "colour", "color",
               "highlights"), bias=1,
          avoid=("hair dryer", "hairdryer", "straighteners", "tongs", "curlers", "brush",
                 "comb", "knots", "tangle", "split ends", "car", "paint", "wood", "plants",
                 "lawn", "fence", "phone", "screen", "washing machine", "relationship",
                 # a bare `snapped` stood this row down for hair that is snapping (it was put here
                 # for a snapped strap); the phrase keeps the strap and lets the hair through
                 "snapping in half",
                 # and the same row must not take a head someone else wrecked: that is a claim
                 "hairdresser", "hairdressers", "salon", "barber", "they bleached",
                 "she bleached", "he bleached", "they dyed", "she dyed", "he dyed")),
    entry("hair-dye-stains",
          (("dye", "dyed", "hair dye", "colour", "color"),
           # the towel, the basin and the bath moved to `hair-colour-surfaces` below: this row
           # opens on the skin, which is the wrong first sentence for a mark on a towel
           # "how do i remove hair dye from my skin" and "hair dye on my forehead how do i get it
           # off" name the skin without "on my skin" or "off my skin" in them, and the box-dye
           # card took both with shade advice; the bare body words and "get it off" close it.
           ("off my skin", "off the skin", "on the skin", "on my skin", "off my hands", "on my hands",
            "off my face", "off my forehead", "off my ears", "off my neck", "my hands", "my neck",
            "hairline", "my skin", "the skin", "skin", "from my skin", "my face", "my forehead",
            "my ears", "get it off", "get that off", "how do i get it off")),
          # main's cleaning card opened "Oil first, not water", which is the half that works on
          # stubborn colour, so it leads here: the skin row replaced it and had better keep it.
          "Oil first, not water: rub a little olive or baby oil into the colour, leave a minute "
          "and wipe, then a paste of bicarbonate of soda and washing-up liquid or a cotton pad of "
          "micellar water for what is left, and the rest fades in a day or two on its own. On the "
          "hands, wash straight away with soap and a nail brush and give the rest a day; dark dye "
          "on pale skin can leave a faint mark for a few days, and that is not a burn. A smear of "
          "barrier cream round the hairline, and gloves, save the next one.", bias=1,
          ask=("dye", "dyed", "hair dye", "colour", "color"),
          avoid=("wine", "curry", "sauce", "tomato", "tea", "coffee", "grass", "blood", "sweat",
                 "armpit", "carpet", "sofa", "shirt", "jeans", "leather", "wood")),
    entry("hair-colour-henna",
          ("henna", ("hair", "dye", "dyed", "colour", "color", "grey", "gray", "cover", "safe",
                     "better", "than", "use", "put", "over", "bleach", "red")),
          "Henna is a plant dye that coats the hair instead of lifting it, so it adds warm red and "
          "brown and can darken, but it can never make hair lighter. Buy pure henna (lawsonia "
          "inermis) and mix it with water and lemon: black henna is not henna at all, it is PPD, "
          "and it can scar. Do not bleach or put a box dye over henna, because the metallic salts "
          "in some mixes can turn hair green and burn, so strand test first if you plan to.",
          ask=("henna", "hair"), bias=2,
          avoid=("tattoo", "temporary tattoo", "eyebrow", "eyelashes", "nails", "skin", "hand",
                 "hands", "mehndi", "bridal")),
    # The dye that is not on a head, and the two asks that are not "how do I colour it":
    # a carpet or a towel with dye on it wants a cleaning answer, not a box-dye how-to; a colour
    # that keeps washing out wants the wash and the heat; and the patch test is the one step
    # people ask about on its own, before they have bought anything.
    entry("hair-colour-surfaces",
          (("dye", "dyed", "hair dye", "colour", "color", "tint"),
           ("carpet", "carpets", "rug", "rugs", "sofa", "settee", "floor", "floors", "towel",
            "towels", "sheet", "sheets", "bedding", "pillow", "pillowcase", "bath", "basin",
            "sink", "tile", "tiles", "worktop", "worktops", "counter", "shower", "curtain",
            "stain", "stained", "spilled", "spilt")),
          "Blot it while it is still wet with kitchen roll rather than rubbing, then work a paste "
          "of bicarbonate of soda and washing-up liquid into a carpet, a towel or a worktop with "
          "an old toothbrush and rinse with cold water; a cream cleaner does the same job on a "
          "basin, a bath or a tile. On fabric, cold water and washing-up liquid first and an "
          "oxygen bleach soak only if the mark has dried. Heat sets it, so keep it out of the "
          "dryer and off the iron until the mark is gone, and if it has dried on a carpet a "
          "carpet cleaner will lift the rest.",
          ask=("dye", "dyed", "hair dye", "colour", "color", "tint"), bias=1,
          # the skin, the hands and the hair itself are the other rows here, and each has the
          # answer for its own surface
          avoid=("my skin", "off my skin", "on my skin", "my hands", "off my hands", "my face",
                 "hairline", "my hair", "roots", "bleach", "highlights", "grey", "gray",
                 "damaged", "strip", "remove", "get it out", "too dark",
                 # and a thing bought in a colour unlike its photo is a consumer question:
                 # "i bought a sofa and the colour is different to the photo" met this row on
                 # "colour" + "sofa", and `sofa` has to stay a key for "hair dye on the sofa"
                 "bought", "buy", "buying", "photo", "photos", "picture", "pictures",
                 "website", "shop", "shops", "delivered", "delivery", "description",
                 "returns", "returned", "refund", "item", "order", "furniture",
                 # the buyer who says it plainly, with no buying word in the line:
                 # "the colour of my new sofa is wrong" met this row on "colour" + "sofa"
                 # and was told to blot it while it is still wet
                 # single words: an avoid phrase has to sit next to itself in the line, and
                 # "the colour of my new sofa is wrong" has "colour" four words before "wrong"
                 "wrong", "arrived", "different", "mismatch", "not the colour",
                 "not the color",
                 # dyeing a garment is the fabric-dye question, not a spill on a floor
                 "shirt", "t-shirt", "tshirt", "top", "dress", "jeans", "trousers", "fabric",
                 "clothes", "jumper", "cardigan", "curtains", "bedding")),
    entry("hair-colour-fade",
          (("hair", "colour", "color", "dye", "dyed", "tint", "highlights", "semi permanent",
            "semi-permanent"),
           ("fading", "fade", "fades", "faded", "last longer", "keep the colour",
            "keep the color", "keep its colour", "keep its color", "colour safe", "color safe",
            "colour-safe", "stays", "washing out", "washes out", "fades so fast")),
          "Most of the fade is the wash and the heat, so wash less often in cooler water with a "
          "sulphate-free colour-safe shampoo, and keep the hot tools and hot showers off it on "
          "the days you can. A weekly purple shampoo keeps blonde from going yellow, and a "
          "tinted gloss or a semi-permanent in the same shade every four to six weeks tops the "
          "colour back up without a full dye job. Sun, chlorine and a hard-water shower head all "
          "take a share too, so a hat and a rinse after swimming are worth the faff.",
          ask=("hair", "colour", "color", "dye", "dyed", "fading", "fade", "shampoo"), bias=1,
          avoid=("how long", "how often", "roots", "regrowth", "grey", "gray", "cover",
                 "bleach", "damaged", "strip", "remove", "get it out", "too dark",
                 "carpet", "towel", "sink", "basin", "my skin", "my hands")),
    entry("hair-colour-patch-test",
          ("patch test", "patch-test", "patch tests", "allergy test", "skin test"),
          "Do it 48 hours before every colour, even a brand you have used before: mix a little of "
          "the dye and the developer as the box says, put a coin-sized patch behind your ear or in "
          "the crook of your elbow, let it dry and leave it. Red, itchy or swollen means do not "
          "use it; a tingle that settles is fine. It matters most in pregnancy and after a "
          "reaction to anything else, and a strand test on a hidden piece of hair is the other "
          "one worth doing before a bleach.",
          ask=("patch test", "patch-test", "allergy", "skin test"), bias=2,
          avoid=("covid", "vaccine", "jab", "nickel", "earring", "earrings", "hospital", "baby",
                 "child", "children", "peanut", "nut", "food", "dog", "cat", "pet", "mascara",
                 "makeup", "perfume", "cream", "soap", "plaster", "tattoo")),
    # "my tattoo is peeling" was the plain-report line, "I'm listening - say more if it helps",
    # though peeling is the most ordinary thing a healing tattoo does and the entry two lines
    # below answers it: the cue list knew "new" and "heal" and not the word people use for the
    # skin coming off. The card now names peeling first, because that is what was asked.
    #
    # The peeling skin and the fresh tattoo are two rows over one body of advice: someone who
    # has just been tattooed and asks how to look after it needs the dressing first, and a line
    # that says it is peeling needs to hear that peeling is normal, in the first sentence. One
    # card opening on peeling would answer the second well and the first badly. Both stand down
    # when an infection sign is in the same line, which is what the shared avoid list is for.
    entry("tattoo-aftercare", ("tattoo", ("new", "look after", "care", "aftercare", "heal",
                                          "healing", "fresh")),
          "Leave the dressing on as long as the artist said, then wash it gently with "
          "fragrance-free soap and water twice a day, pat it dry and put a thin layer of tattoo "
          "balm on. Keep it out of the sun and out of swimming pools for two to three weeks, and "
          "do not pick at it: it will peel and flake a week or two in, and that is it healing.",
          _TATTOO_INFECTION_AVOID),
    entry("tattoo-peeling", ("tattoo", ("peel", "peels", "peeling", "peeled", "flake",
                                         "flakes", "flaking", "flaky", "scab", "scabs",
                                         "scabbing", "scabby")),
          "Peeling and flaking a week or two in is the tattoo healing, so leave it alone and do "
          "not pick at it. Wash it gently with fragrance-free soap and water twice a day, pat it "
          "dry and put a thin layer of tattoo balm on, and keep it out of the sun and out of "
          "swimming pools for two to three weeks.",
          # ...but a tattoo that is peeling and red, hot or weeping is not a healing tattoo, and
          # this card must not call the skin coming off the ordinary thing while an infection
          # sign is in the same line. Those lines keep the wound and reaction answers.
          _TATTOO_INFECTION_AVOID),
    entry("chapped-lips", (("chapped", "cracked", "dry"),
                           ("lips", "lip", "winter", "heal", "sore")),
          _LIP_BALM,
          avoid=_LIPS_NOT_DRY),
    # Cold and wind swell a lip as well as cracking it, and the airway reading has already stood
    # down on the cause ("my lips are swollen from the cold" is not the ambulance), so the line
    # was left with nothing to say. It is the lip balm either way: what swells in the cold is the
    # skin of the lip, and the answer that dries it out again is the same one. The words that make
    # a swelling a reaction (a sting, a nut, a piercing, hot food) are named below so they never
    # reach here.
    #
    # The weather is asked for as well as keyed on, because the cause is the whole case for a
    # swelling: a lip that swells with a rash, or that has gone puffy and red, or that swelled
    # after a kiss, is angioedema or an allergy, and a swelling nobody has explained is the one
    # to worry about. Safety answers that line (a bare "my lips are swollen" is the ambulance),
    # and this entry has to leave it alone rather than answer the weather into it.
    entry("swollen-lips-cold", (("swollen", "swelling", "puffy", "puffed"),
                                ("lips", "lip")),
          _LIP_BALM,
          ask=("cold", "coldest", "wind", "windy", "winter", "frost", "frosty", "chill",
               "chilly", "dry", "drying", "dried", "chapped", "cracked", "weather", "outside",
               "outdoors", "walk", "walking", "cycling", "skiing", "ski", "heating", "air",
               "snow", "rain", "sun", "sunburn", "sunburnt"),
          avoid=_LIPS_NOT_DRY + ("sting", "stung", "bee", "bees", "wasp", "nut", "nuts",
                                 "peanut", "peanuts", "shellfish", "allergy", "allergic",
                                 "reaction", "tongue", "throat", "face", "piercing", "filler",
                                 "collagen", "curry", "chilli", "spicy", "burnt", "burn",
                                 "burned", "cold sore", "blister", "ulcer", "gum", "gums",
                                 "dentist", "tooth", "wisdom", "bit my lip", "bite my lip",
                                 "bitten my lip", "cut my lip", "cheek", "jaw", "abscess",
                                 "rash", "rashes", "hives", "wheeze", "wheezing", "kiss",
                                 "kissing", "itched", "itching", "itch", "itchy", "itches",
                                 "itchiness", "hot to the touch",
                                 # a line with another symptom in it is the airway first and the
                                 # lip balm never: the weather in the same sentence does not fix
                                 # "and i feel faint", "and i can hardly breathe"
                                 "faint", "fainted", "fainting", "dizzy", "dizziness",
                                 "breath", "breathe", "breathing", "breathless", "gasps",
                                 "gasping", "swallow", "swallowing", "collapse", "collapsed",
                                 "vomit", "vomiting", "unconscious", "shut")),
    # "my face is spotty" and "i keep breaking out" named no word this row had, so both were an
    # echo: the adjective and the verb are how most people say it.
    entry("spots", (("spots", "acne", "pimples", "breakouts", "zits", "skin", "complexion",
                     "spotty", "spotty skin", "breaking out", "break out", "breaks out",
                     "broken out"),
                    ("face", "skin", "wash", "cream", "teenager", "chin",
                     # the goal is said as a verb: "how do i clear my skin", "how to clear spots",
                     # "how do i get rid of spots", "how do i stop getting spots". The cause
                     # entry stands down for every one of these words already, so without them
                     # here a young person asking for clear skin gets a shrug.
                     "clear", "clearing", "clearer", "get rid", "rid of", "go away",
                     "stop", "stopped", "prevent", "treat", "treating", "cure", "curing",
                     # "i keep breaking out" is one key form and no second word, so the line
                     # the comment above names was still an echo: how often it happens is the
                     # ask side of the same question
                     "keep", "keeps", "still", "again", "constantly", "always", "every time")),
          "Wash with a gentle cleanser twice a day and put a benzoyl peroxide or salicylic acid "
          "cream on the spots, not all over the face. Give it six weeks, change your pillowcase "
          "weekly, and see a pharmacist if it's leaving marks or scars.",
          guard=_acne_product_question,
          # spots on a shirt, a car, a leaf or a wall are cleaning questions, a sun-bed patch is a
          # tanning question, and a fever rash with a fever is not acne
          avoid=("shirt", "shirts", "clothes", "clothing", "fabric", "carpet", "sofa", "duvet",
                 "mattress", "laundry", "my washing", "the washing", "washing machine",
                 "washing basket", "detergent", "car", "cars", "windscreen",
                 # "skin" is in both halves of the key, so with "keep" and "stop" on the ask
                 # side the word alone reached the spot routine: "how do i keep my skin from
                 # burning" was told to put benzoyl peroxide on it, and "how do i keep my skin
                 # young" got the same. A burn and an ageing question are not acne.
                 "burn", "burns", "burning", "burnt", "stinging", "stings",
                 "young", "younger", "ageing", "aging", "wrinkle", "wrinkles", "fine lines",
                 "wall", "walls", "floor", "paint", "leaf", "leaves", "plant", "garden",
                 "mud", "grease", "sun", "sunbed", "tan", "fever", "chickenpox", "rash",
                 # acne is the acne card's word: `science.acne-why` answers it with the cause and
                 # the same wash-and-pharmacy steps, so the guard above stands this row down
                 # for an acne line unless it names a product.
                 # a scar, a flush, a freckle and a sun patch are not spots, and the six-week
                 # spot routine is not their treatment: each has its own card, or the honest
                 # shrug where main had one
                 "scar", "scars", "scarring", "redness", "red", "rosacea", "freckle", "freckles",
                 "pigment", "pigmentation", "age spots", "sun spots", "sunburn", "dry patches",
                 # a product being chosen is a recommendation, not a routine: "what is the best
                 # moisturiser for my skin" and "best cleanser for my skin" were a punt on main
                 # and the spot routine here, because "best" sat in this row's second group
                 "moisturiser", "moisturiser's", "moisturizer", "moisturising", "moisturizing",
                 "sunscreen", "sunblock", "spf", "lotion", "serum", "toner", "face cream",
                 "cleanser", "cleansers", "exfoliator", "exfoliant",
                 "aftershave", "makeup", "foundation", "product", "products", "brand")),
    entry("scratched-glasses", (("glasses", "spectacles", "eyeglasses", "eye glasses",
                                # "sunglasses" is one word to the matcher, so a pair of them
                                # reached nothing: "my sunglasses are scratched" was silence.
                                "sunglasses", "sunglass", "shades",
                                "lenses", "lens"),
                                ("scratch", "scratched", "scratches", "scratchy", "scuff",
                                 "scuffed", "smear", "smears", "smudged", "scuffed up")),
          _spectacle_glass,
          # a cleaning question about glasses is about a pair of spectacles before it is about a
          # washed-up tumbler: "how do I clean my glasses without streaking" shares its streak word
          # with the dishwater entry, and the lens answer is the one a person wants (deft-squid).
          # `clean` used to be in this key, which is why a cleaning question got the scratch card
          # ("a scratch in the coating can't be polished out") for a pair with no scratch in it;
          # the wash words are `glasses-wash`'s now, and the marks stay here.
          bias=1,
          # the tumbler and the wine glass are already out on these words; a pane of glass is
          # caught by the reply itself
          avoid=("wine", "drinking", "water", "beer", "mug", "cup", "dishwasher", "windscreen",
                 "window",
                 # how to stop it happening is the prevention card's question: "how do i stop my
                 # sunglasses scratching" wants the case and the dry-lens rule, not the news
                 # that a scratch cannot be polished out
                 "stop", "stops", "stopping", "prevent", "prevents", "preventing", "avoid",
                 "avoids", "avoiding", "keep", "keeps", "keeping", "protect", "protects",
                 "protecting", "from getting scratched", "from scratching", "scratch free",
                 "scratch-free", "without scratching")),

    # How to keep a pair from getting scratched in the first place is a different question from
    # what to do about a scratch that is there: "how do i stop my sunglasses scratching" was a
    # shrug, and the scratch card only says a scratch cannot be polished out.
    entry("glasses-scratch-prevent",
          (("glasses", "sunglasses", "sunglass", "specs", "spectacles", "eyeglasses", "lenses",
            "lens", "shades"),
           # The scratch words, not the hole words. Every one of these lines carries the fault
           # anyway: "how do i stop my sunglasses scratching", "how do i prevent scratches on my
           # glasses", "how do i keep them from getting scratched". The hole words on their own
           # carried lines that are not about scratches at all - "my new glasses keep slipping"
           # and "how do i keep my glasses on my face" - because "keep" is a hole word too. The
           # fault word belongs here because the already-scratched shapes stand this row down
           # below, and `scratched-glasses` comes first and stands down for the hole words.
           ("scratch", "scratches", "scratching", "scratched", "scuff", "scuffed", "scuffs",
            "scratch free", "scratch-free", "from scratching", "without scratching")),
          "Never wipe a dry lens: grit on a dry lens is what makes the scratch, so rinse them "
          "under a tap first and dry them with a microfibre cloth, not a tissue or a sleeve. Keep "
          "them in a hard case rather than a pocket or a bag with keys in it, and take them off "
          "with both hands so the arms are not twisted. A coating scratch cannot be polished out, "
          "so a cheap case saves a new pair.",
          bias=1,
          avoid=("wine", "drinking", "water intake", "how many", "eight glasses", "a day",
                 # a scratch that is already there is the scratch card's question, not this one:
                 # the shapes below are how people say it and they are left to `scratched-glasses`
                 "are scratched", "is scratched", "got scratched", "been scratched",
                 "already scratched", "has a scratch", "have a scratch", "there is a scratch",
                 "theres a scratch", "has scratches", "have scratches",
                 "window", "windows", "windscreen", "pane", "panes", "tumbler", "mug", "cup",
                 "shower", "screen", "dishwasher", "washing machine", "oven", "mirror",
                 "bottle", "cutlery", "crockery", "white film",
                 # steam is the anti-fog row's question and it shares the word "stop":
                 # "how do i stop my glasses fogging up" keeps its own answer
                 "fog", "foggy", "fogging", "fogged", "steam", "steamy", "steaming", "misting",
                 "misted", "condensation"),
          # a pane and a tumbler again, on the reading rather than on a word: "will the bicarb
          # scrath the glass" is the oven door, and the two slips in it ("scrath" for scratch,
          # "glass" for glasses) are enough to reach this row without the guard the scratch row
          # already carries. Same reading, same guard.
          guard=_not_a_pane),

    # A pair that has actually broken is not a cleaning or a sliding question, and the answer
    # people want is who can mend it and whether it is worth it. The key is the pair plus the
    # fault (or the repair word), so "can they be repaired or do i need new ones" reaches it
    # through the line it leans on ("my glasses broke").
    entry("glasses-repair",
          # "eyeglasses" is the American spelling of the pair, and it is a different word to the
          # matcher: it has to be written here or "can i fix my eyeglasses myself" has no answer
          # to reach - the do-it-yourself entry stands down for it and nothing else picks it up.
          (("glasses", "spectacles", "specs", "sunglasses", "prescription glasses",
            "eyeglasses", "eye glasses"),
           ("broke", "broken", "break", "repair", "repairs", "repaired", "fix", "fixed",
            "mend", "mended", "new pair", "new ones", "replace", "replacement",
            # how a pair actually comes apart, and the words people use for it: "my lens popped
            # out", "the arm snapped", "i sat on my glasses". The pair is already in part one,
            # so the fault alone is enough to reach the repair answer.
            "snapped", "snap", "cracked", "crack", "smashed", "fell apart", "come apart",
            "came apart", "fell out", "come out", "came out", "popped out", "popped",
            "popped off", "hinge", "arm", "arms", "screw", "bent", "sat on", "sit on",
            "stepped on", "step on", "squashed", "crushed", "dropped them", "damaged",
            "came off", "come off", "temple", "temples", "in pieces",
            # the second half of the repair ("what glue should i use", "can i fix them myself")
            # leans on the pair already said, so the glue words alone reach it
            "glue", "glued", "superglue", "araldite",
            "fix them myself", "fix it myself", "do them myself", "do it myself",
            # Not "tape": it is a sticker-removal word ("how do i get tape residue off glass"
            # reached this entry on it, one edit away from "glasses"), and the follow-up it was
            # meant for never arrives here anyway - "can i tape it back together" carries no
            # lean-on, so the line alone is searched and it names no pair.
            )),
          _glasses_repair,
          bias=1,
          guard=_the_glass_is_a_drink,
          # cleaning, sliding and scratched lenses each have their own answer; this one is for a
          # pair that will not go on the face any more.
          avoid=("clean", "cleaning", "dirty", "slide", "sliding", "slip", "slipping",
                 "scratch", "scratched", "scratches", "fog", "steam", "wine", "drinking",
                 "window", "windows", "windscreen", "pane", "panes", "tumbler", "tumblers",
                 "cup", "mug", "dishwasher", "a glass", "the glass", "glass of", "pint glass",
                 # "i broke my glass at home" is the glass somebody was drinking from, and "how do
                 # i get broken glass off the floor" is clearing it up: the pair is always plural
                 # or named as a pair, so the singular possessive is not this row's
                 "shard", "shards", "splinter", "splinters", "off the floor", "on the floor",
                 "glass on the floor", "sweep", "sweep it up", "dustpan",
                 "broken glass", "mirror", "bottle", "jar", "door", "table", "shower", "screen",
                 # packing a pair so it does not break is a moving question, not a repair
                 "pack", "packing", "packed", "moving", "move", "box", "trip", "travel",
                 "carry", "store", "storage",
                 # "glue" is the repair only when something is being stuck back together. Taking
                 # it off again is a cleaning job: "how do i remove sticker glue from glass" came
                 # back "superglue is the stopgap, not the repair"
                 "sticker", "stickers", "label", "labels", "price tag", "residue", "sticky",
                 "tape", "gummed", "off my hands", "off my fingers", "off hands", "off fingers",
                 "off my skin", "on my hands", "on my fingers", "on my skin")),

    # A snapped watch strap is a two-pound part and a five-minute job, so the answer is where to
    # get it done rather than whether it can be. It is not the "what to watch" question, so the
    # films are on the avoid list.
    entry("watch-strap",
          (("watch", "watches", "smartwatch", "fitbit", "garmin"),
           ("strap", "straps", "band", "bracelet", "snapped", "snap", "broke", "broken",
            "came off", "fell off", "replace", "replacement", "new one", "too loose",
            "too tight", "size it")),
          "A jeweller or watch shop fits a new strap while you wait, usually £10 to £25 for a "
          "leather or silicone one, and a broken strap is always replaced rather than mended. A "
          "metal bracelet is resized by taking links out for £5 to £15. If it is a smartwatch, "
          "buy the band yourself: most use a quick-release pin, and a new one is £8 to £20.",
          avoid=("film", "films", "movie", "movies", "tv", "series", "show", "shows", "netflix",
                 "episode", "episodes", "match", "football", "game", "channel", "documentary")),

    # steam on glasses is `cleaning.anti-fog`: one table for one fact, and it moved there so the
    # "why" line and the "how" line get the same advice from the same entry.

    # --- what to wear --------------------------------------------------------
    entry("which-socks",
          (("sock", "socks"),
           ("go with", "goes with", "match", "matches", "wear", "wearing", "which", "what",
            "suit", "suits", "smart", "wedding", "interview", "shoes", "trainers", "jeans",
            "formal", "colour", "color", "white", "black", "brown", "right", "ok", "okay")),
          _socks,
          # a sock being washed, smelling, holed or swollen is another answer: the laundry, the
          # shoe that rubs and the foot are all their own lines and this card would answer
          # "my socks smell even after washing" with which sock to wear with a suit
          avoid=("wash", "washing", "washed", "laundry", "dirty", "smell", "smells", "smelly",
                 "whiff", "stink", "stinks", "hole", "holes", "holed", "darn", "darning",
                 "blister", "blisters", "athlete", "sweaty", "damp",
                 "put on", "putting on", "lost", "missing", "one sock", "odd socks",
                 "dry", "drying", "shrink", "shrunk", "elastic", "fell down")),
    entry("interview-outfit", (("job interview", "interview"),
                               ("wear", "outfit", "dress", "clothes", "smart", "suit", "jeans",
                                "tie", "put on")),
          "For most interviews, smart casual is the safe bet: a clean shirt or blouse, dark "
          "trousers or a skirt, and closed shoes; a suit only if the company is formal. Check the "
          "office on their website or LinkedIn and dress one step smarter than that.",
          guard=_put_on_is_clothes),
    # "got an interview thursday and nothing smart fits me any more, what do i wear" is not the
    # interview-outfit card's question: the shape of it, the shirt, the shoes are all fine and the
    # trouble is that the clothes in the wardrobe stopped fitting. It was answered "smart casual
    # is the safe bet" and left the person where they started, so the constraint is the key here
    # and the interview row above keeps the plain line.
    entry("interview-when-nothing-fits",
          (("interview", "interviews", "interviewing", "interviewer", "interviewers",
            "job interview"),
           ("nothing fits", "nothing smart fits", "nothing fits me", "nothings fits",
            "nothing to wear", "doesnt fit", "doesn't fit", "dont fit", "don't fit",
            "no longer fits", "too tight", "too small", "put on weight", "put on a stone",
            "outgrown", "grown out of", "no suit", "cant afford", "can't afford",
            "nothing smart", "two sizes", "nothing that fits")),
          "Buy one pair of dark trousers in the size that fits you now and one plain shirt, this "
          "week rather than on the morning: those two do more for how you look than an expensive "
          "jacket that does not button. Ask for the trousers to be taken up while you are in the "
          "shop. "
          "Supermarkets and charity shops sell both for under 30 pounds, and a dark pair of "
          "unripped jeans and a clean shirt pass everywhere outside law, finance and the civil "
          "service. Polish the shoes you already have, take a "
          "spare shirt if the day is long, and wear the jacket open or leave it off; nobody is "
          "measuring the label, they are looking at whether the shirt is clean and the shoulders "
          "sit where they should.",
          # a line that asks what smart casual means, or that names the fit of one garment, is
          # another row's question
          avoid=("what does smart casual mean", "what is smart casual", "smart casual mean",
                 "dress code", "how should jeans fit", "should jeans fit"),
          bias=3),
    entry("wedding-white", (("wedding",
                             # A wedding named as the event rather than the word: "my friend is
                             # getting married what do i wear" was a search hedge, and it is the
                             # same question as "what do i wear to a wedding".
                             # Named with the person, because "i am getting married what do i
                             # wear" is the couple's own question and the guest answer is not it.
                             "my friend is getting married", "my sister is getting married",
                             "my brother is getting married", "she is getting married",
                             "he is getting married", "they are getting married",
                             "my cousin is getting married", "a friend is getting married",
                             "friend is getting married", "sister is getting married",
                             "brother is getting married", "cousin is getting married"),
                            # Where the do is decides the shoes, and a wedding in a field is
                            # the question that says so: "i'm going to my sister's wedding in a
                            # field and my feet hurt, what should i wear" was answered with the
                            # foot-pain card, which tells somebody whose feet already hurt to
                            # check their running shoes.
                            ("field", "fields", "marquee", "in a tent", "a tent", "grass",
                             "on the beach", "beach"),
                            ("white", "cream", "wear", "wearing", "guest", "dress",
                                        "rude", "okay", "ok",
                                        # The guest asking about one garment named it and no
                                        # other row claimed the word, so "do i need a hat for a
                                        # wedding" and "what shoes for a wedding" fell through to
                                        # the hotel-booking row on "for a wedding", and then to a
                                        # search hedge once that row stood down. A question about
                                        # wearing something to a wedding is this row's.
                                        "hat", "hats", "fascinator", "shoes", "shoe", "heels",
                                        "heel", "outfit", "outfits", "jumpsuit", "jumpsuits",
                                        # The feet come up in the describing clause of the
                                        # question ("my feet hurt, what should i wear") and a row
                                        # that does not name them stands down for the foot-pain
                                        # card, which tells somebody whose feet already hurt to
                                        # check their running shoes. What to put on them is this
                                        # card's to answer.
                                        "feet", "foot",
                                        "colour", "color", "dress code",
                                        # "what should i put on for a wedding" is the same ask
                                        "put on")),
          ("Don't wear white or cream to a wedding unless the invitation says so: it's the "
           "couple's colour and reads as upstaging them. Anything else bright and comfortable "
           "works, and flat shoes are a kindness to yourself at an outdoor ceremony.",
           "White and cream are the one thing to avoid at a wedding, because they belong to the "
           "couple. Pick a colour you feel good in and check the invitation for a dress code; "
           "comfy shoes matter more than anything if there's standing around."),
          # "is it rude to say no to a wedding" is the decline script's line, and with "rude" in
          # this key it came here once the wedding rows made the word commoner. Saying no is not
          # a dress code.
          avoid=("speech", "speeches", "toast", "toasts", "best man", "vows",
                 "say no", "saying no", "decline", "declining", "turn down", "turned down",
                 "not going", "can't go", "cant go", "tell them no"),
          guard=_put_on_is_clothes),
    # The couple's own question is not the guest's, and it was reaching nothing: "we're getting
    # married in june and i've put on weight, what colour should i wear" was answered with a
    # strength plan, "we are getting married next year, what colour should my suit be" with "I'm
    # not sure about that one", and "we're getting married in a registry office, what should i
    # wear" with the job-interview answer. The guest card above stays the guest card - its key
    # says so in as many words - and this row takes the line that says the wedding is the
    # person's own.
    entry("wedding-couple",
          (("getting married", "get married", "our wedding", "our big day", "my wedding",
            "the wedding we are planning", "we are marrying", "we are eloping"),
           ("what should i wear", "what do i wear", "what to wear", "what colour", "colour",
            "color", "outfit", "dress", "suit", "wear", "wearing")),
          ("Wear what you feel good in, and get it fitted: white or ivory is yours to wear as the "
           "couple, and a dress or suit that fits beats a dearer one that does not. Try it on "
           "with the shoes and sit, walk and raise your arms in it for an hour at home. If it is "
           "outside, keep the hem off the grass and take a wrap for the evening, because the day "
           "outlasts the photographs. In a suit, navy, charcoal or mid-grey photographs well and "
           "wears again afterwards.",
           "White or ivory is the couple's to wear, so pick the colour you like and put the money "
           "into alterations rather than labels: a cheap outfit that fits looks better than an "
           "expensive one that does not. Wear it in at home with the shoes, and take a wrap - the "
           "evening cools down whatever the month says. A suit in navy, charcoal or mid-grey is "
           "the one you will wear again."),
          # the guest's question, the wedding party's, and anything about the day's arrangements
          # rather than the couple's clothes
          avoid=("guest", "guests", "plus one", "mother of the bride", "mother of the groom",
                 "father of the bride", "bridesmaid", "bridesmaids", "best man", "speech",
                 "invited", "invitation", "hen do", "stag do"),
          guard=_put_on_is_clothes),
    # "what should i wear as the mother of the bride" was a shrug on main, though it is one of the
    # most-asked outfit questions there is and the guest answer above is not it: the mother of the
    # bride or groom has to fit round the couple's colours.
    entry("mother-of-the-bride",
          (("mother of the bride", "mother of the groom", "father of the bride",
            "father of the groom", "bride's mother", "groom's mother", "mother of bride",
            "mother of groom"),
           ("wear", "outfit", "dress", "colour", "color", "what should i", "what to wear",
            "suit", "hat", "shoes", "put on")),
          "Ask the couple what colours the wedding party is in, then pick something in that family "
          "but quieter: navy, sage, burgundy or grey all work, and the one thing to leave alone is "
          "white, ivory or cream, which belong to the bride. Comfortable shoes, a dress you can sit "
          "and eat in, and something with sleeves if the day runs late. If the couple have a colour "
          "scheme or a dress code on the invitation, follow it and let them see the outfit first.",
          # the guest's own white question, a funeral and a speech are other rows
          avoid=("speech", "speeches", "toast", "toasts", "funeral", "guest", "can i wear white",
                 "is it rude")),
    # A wake is the same clothes question said with the other word, and "wear" is in the key, so
    # the waking-up sense of "wake" cannot reach it.
    entry("funeral-outfit", (("funeral", "the wake", "a wake", "at the wake", "to the wake"),
                             ("wear", "black", "outfit", "clothes", "colour", "color",
                              "put on")),
          "Familiar, subdued clothes are the thing: black or dark colours, smart and comfortable, "
          "and nothing new needed. If the family asked for bright colours or a football shirt, "
          "follow that instead, because it's about them.",
          guard=_put_on_is_clothes),
    # "smart casual" is the whole answer on its own: the line names the code and asks nothing
    # else ("theres a dress code, smart casual", "the dress code says smart casual"), and with
    # only the asking words as the second part both lines fell through to a chat nod once the
    # interview answer stood down. A code named in the line is the second signal, so the words
    # of the code sit in both parts.
    entry("smart-casual", (("smart casual", "dress code"),
                           ("mean", "means", "casual", "smart", "wedding", "party", "dinner",
                            "office", "work", "what is", "what does", "wear")),
          "Smart casual usually means dark jeans or trousers with a collared shirt or a nice top, "
          "and clean shoes: tidy, no tie. If you're unsure, dress one step smarter than you think "
          "and ask the host.",
          avoid=("cocktail", "black tie", "formal", "white tie", "lounge suit"),
          guard=_the_code_is_not_an_interview),
    entry("black-tie", ("black tie", ("mean", "means", "wear", "suit", "dress", "tie", "do")),
          "Black tie for a man means a dinner jacket, black trousers with a satin stripe, a white "
          "dress shirt with a proper bow tie, and black shoes; for a woman it means a long or "
          "cocktail dress, not a business suit. A dark suit with a normal tie is the fallback if "
          "you don't own the rest, and it's much better than staying home.",
          avoid=("black tie and trainers", "how to tie")),
    entry("tie-a-tie",
          (("tie a tie", "necktie", "windsor knot", "half windsor", "four in hand", "tie knot",
            "tie my tie", "tie his tie",
            # a school tie is a necktie, and it sits in both parts of the key because the line
            # usually carries no other neck word: "how do i tie a school tie" was a hedge
            "school tie", "tie his school tie", "tie my school tie"),
           ("how", "knot", "learn", "teach", "show", "steps", "video", "windsor",
            "school tie", "tie his school tie", "tie my school tie")),
          "The four-in-hand is the one to learn: put the tie round your neck with the wide end "
          "hanging about 30cm lower, cross it over the narrow end, take it up through the loop at "
          "your neck, then wrap it across the front and up through the loop again, and pull it down "
          "through the knot you just made. Draw it up snug and slide the knot where you want it. "
          "Wide end below the narrow, and the tip reaching your belt.",
          # a shoelace or a bin bag is tied too, and neither wants this: the tie has to be the
          # thing the line names, so the neck words are in the key and not in a loose "tie"
          # "how do i tie a necktie for a wedding" scored the minimum here and lost to the wedding
          # planning row, so the necktie card says it is about a necktie
          bias=2,
          avoid=("shoelace", "shoes", "lace", "laces", "bin", "rubbish", "hair", "hands",
                 "black tie", "white tie")),
    entry("bow-tie",
          ("bow tie", ("how", "tie", "knot", "wear", "learn", "do")),
          "A bow tie is tied like a shoelace, only in front of your throat. Put it round your neck "
          "with one end about 4cm longer, cross the longer end over the shorter, bring it up behind "
          "the crossing and through the loop at your neck, and pull it snug: that is the knot, and "
          "the short end now stands up as the front loop. Drop the long end over the middle of that "
          "loop, push it up through the small gap behind it, and pull through to make the second "
          "loop. Tighten both loops together and straighten it. Practise on your thigh first, where "
          "you can see it, and give yourself twenty minutes the first time.",
          avoid=("black tie", "white tie")),
    entry("tie-with-a-suit",
          (("which tie", "what tie", "tie with", "tie goes", "tie for", "matching tie"),
           ("suit", "shirt", "match", "goes", "colour", "color", "navy", "grey", "gray",
            "wedding", "interview")),
          "Pick a tie a shade darker than your shirt and darker than the suit, and let one bold "
          "thing carry it: a patterned tie with a plain shirt, or a patterned shirt with a plain "
          "tie. With a navy suit, most things work - burgundy, bottle green, a dark striped tie - "
          "and a tie the same colour as the suit is the one to skip.",
          avoid=("black tie", "white tie", "bow tie")),
    entry("glasses-slide",
          (("glasses", "specs", "spectacles", "sunglasses", "eyeglasses", "eye glasses"),
           ("slide", "slides", "sliding", "slip", "slipping", "fall off", "falling off", "nose",
            "keep sliding", "down my nose", "loose", "wont stay")),
          "Pinch the arms in gently at the temples - most plastic frames can be bent a millimetre or "
          "two by hand, and that is usually all it takes - then have an optician tighten the screws "
          "and adjust the bridge, which they do free in a few minutes. Silicone nose pads or an "
          "ear grip stop a pair that keeps sliding, and wash the nose pads with soapy water, "
          "because skin oil makes them skate.",
          avoid=("clean", "scratch", "scratched", "lens", "lenses", "prescription", "new pair",
                 "which frames", "broken", "repair cost", "reading", "driving")),
    # A pair of glasses is the one thing people wear that an optician fixes for nothing, and the
    # lines that ask were all shrugs: "how do i get my glasses adjusted", "how do i tighten the
    # screws on my glasses", "can i fix my glasses myself". The frame word is in the key, so the
    # answer can only land on a line that named the pair.
    # Two entries were merged into the file under this id from two PRs, so the adjustable-frame
    # half gets its own name: a duplicate id makes the wrong-answer guard (`_part_asked` compares
    # ids) treat the two as the same answer.
    entry("glasses-adjust",
          (("glasses", "specs", "spectacles", "sunglasses", "eyeglasses", "eye glasses",
            "frames", "frame"),
           ("adjust", "adjusted", "adjusting", "adjustment", "tighten", "tightening", "screws",
            "screw", "screwdriver", "bent", "bend", "bending", "broken", "broke", "repair",
            "repairs", "fix", "fixing", "mend", "mending", "loose", "snapped", "hinge",
            "arm", "arms", "popped out", "fell apart")),
          "Take them to an optician: straightening an arm, tightening a screw and adjusting the "
          "bridge are free at almost every high-street optician, take a few minutes and need no "
          "appointment. The one job worth doing yourself is a loose screw, with a glasses "
          "screwdriver or the smallest one in a jeweller's kit, and a bent plastic arm can be "
          "eased straight after a dip in warm water - but never bend metal frames cold, because "
          "they snap. If the frame itself has cracked, ask them to put new lenses in a new frame "
          "rather than glue it, and keep your old pair as the spare.",
          guard=_the_glass_is_a_drink,
          avoid=("clean", "cleaning", "scratch", "scratched", "smear", "lens", "lenses",
                 "look bent", "looks bent", "look wavy", "looks wavy",
                 "prescription", "which frames", "reading", "driving", "fog", "steam",
                 "slide", "sliding", "slip", "nose", "wine", "drinking", "dishwasher",
                 "washing machine",
                 # the glass somebody was drinking from is not a pair: "my glass broke" and
                 # "i broke my glass at home" were both told to take it to an optician
                 # "my glass", "a broken glass" cannot be avoided here: "glass" and "glasses"
                 # are loose forms of one word, so the phrase stands the pair down as well
                 "shard", "shards", "splinter", "splinters", "off the floor", "on the floor",
                 "glass on the floor", "sweep", "sweep it up", "dustpan",
                 # a bed, a chair, a table or a sofa has a frame too, and a frame that broke is
                 # furniture, not a pair of spectacles: "my bed frame broke" was the optician
                 "bed", "beds", "bed frame", "bedframe", "chair", "chairs", "table", "tables",
                 "sofa", "sofas", "couch", "settee", "wardrobe", "door", "window")),
    # Heat is what ruins a pair of glasses: the dishwasher, the washing machine and a kettle are
    # the three ways people find that out. The line names the appliance, so this entry is short
    # and direct rather than another washing-up answer.
    entry("glasses-wash",
          (("glasses", "specs", "spectacles", "sunglasses", "eyeglasses", "eye glasses",
            "lenses", "lens"),
           ("dishwasher", "washing machine", "tumble dryer", "microwave", "boiling water",
            "hot water", "kettle", "sterilise", "sterilize", "soap", "soapy", "washing up liquid",
            "wash them", "wash my glasses", "washing my glasses", "shower",
            # "how do i clean my glasses" and "how do i polish glasses" are this row's question,
            # and they were answered with the scratch card ("a scratch in the coating can't be
            # polished out"), which is a fault the person never mentioned. The wash words are
            # here so the clean ask reaches the wash answer; the scratch words stay with the
            # scratch card.
            "clean", "cleaning", "cleaned", "polish", "polishing", "wipe", "wiping",
            "dirty", "smudge", "smudged", "smudges", "smear", "smears", "streaky", "streaks",
            "mark", "marks", "fingerprints", "sparkling", "shiny", "scratch free",
            "scratch-free")),
          "Wash them by hand in lukewarm water with a drop of washing-up liquid, rinse and dry "
          "them with a microfibre cloth - but never in the dishwasher or the washing machine: the "
          "heat warps the frame and the salt and detergent strip the coatings, so a pair that goes "
          "through comes out scratched and loose. Lukewarm, not hot, for the same reason.",
          avoid=("wine", "drinking", "water intake", "how many", "eight glasses", "day",
                 "oven", "window", "windscreen", "pane", "tumbler", "mug", "cup",
                 # a load of drinking glasses out of the dishwasher is the crockery question,
                 # not a pair of spectacles: "white film", "cloudy" and "streaks" are what the
                 # line says about the load, and home.py's dishwasher row answers it
                 "white film", "white marks", "white spots", "cutlery", "crockery", "dishes",
                 "plates", "a load",
                 # "my glasses came out of the dishwasher cloudy" is a pair of spectacles, and
                 # this row is the one that says never put them through; the load itself says
                 # "wine glass", "cutlery" or "a load", so those stay fenced off above
                 # a contact lens on the eye is not a pair of glasses on the face, and washing-up
                 # liquid on a contact is the wrong advice twice over: never answer a line about
                 # tap water and lenses with this.
                 "contact lens", "contact lenses", "contacts", "tap water", "in my eye",
                 "my eyes", "eye drops",
                 # drinking glasses out of the dishwasher are the kitchen's question: the film
                 # is limescale or detergent, and "wash them by hand" is not that answer
                 "white film", "film", "filmy", "smear", "smears", "streaks", "streaky",
                 "water marks", "watermarks", "spotty", "chalky", "rinse aid", "salt",
                 "cloudy after the dishwasher", "cloudy out of the dishwasher",
                 # a shower screen is "shower" plus "glass", and the only glass a pair of
                 # spectacles shares with it is the word: "limescale on shower glass" was told
                 # never to put them in the dishwasher, so the bathroom surfaces stand this
                 # card down and cleaning's shower-scum row answers them
                 "shower screen", "shower glass", "shower door", "shower panel",
                 "shower enclosure", "limescale", "soap scum", "scum", "tiles", "grout",
                 "bathroom")),
    # "my dishwasher leaves a white film on the glasses" was answered with how to wash a pair of
    # spectacles by hand, because "glasses" plus "dishwasher" is both questions. The film itself
    # is the question here, and there are two causes: hard water, and too much detergent.
    entry("dishwasher-glass-film",
          (("dishwasher", "dish washer", "dishwashing"),
           ("film", "white film", "cloudy", "clouded", "smears", "smears on", "streaks",
            "marks", "spotty", "chalky", "greasy", "glasses")),
          "A white film on glasses out of the dishwasher is limescale from hard water: fill the "
          "salt right up, set the machine's water hardness, and keep rinse aid topped up, because "
          "too little leaves water marks and too much leaves a blue smear. In a soft-water area "
          "the film is detergent etching the glass, which does not come off - use less powder, a "
          "short cycle, and wash the wine glasses by hand.",
          avoid=("spectacles", "specs", "contact lens", "contact lenses", "sun", "surge",
                 "not draining", "not emptying", "smell", "smells", "leak", "leaking")),
    # A new pair that hurts is not a wrong pair yet: most settle in a few days, and the ones that
    # do not are usually the fit or the centration rather than the prescription. The old pair is
    # the thing to keep wearing meanwhile.
    entry("new-glasses-pain",
          (("new glasses", "new pair of glasses", "new specs", "glasses", "specs", "spectacles",
            "eyeglasses", "eye glasses"),
           ("headache", "headaches", "head ache", "hurt", "hurts", "hurting", "ache", "aching",
            "pressure", "sore", "behind my ears", "dizzy", "dizziness", "blurry", "sick",
            "uncomfortable", "feel strange", "feel odd", "making me",
            # things that look bent or wavy are a prescription and centration question, not a
            # bent arm to straighten
            "look bent", "looks bent", "look wavy", "looks wavy", "look wrong", "looks wrong")),
          "If the pair is new, wear them as much as you can for three to five days: most "
          "headaches at that stage are your eyes and head settling, and they fade. If it is still "
          "hurting after that, or one eye aches and the other does not, go back to the optician "
          "and ask them to check three things - the prescription against your old one, the pupil "
          "distance and the fit - and to adjust the frame, which is free. If the pair is not new, "
          "the fit has probably slipped: get the arms and the bridge adjusted before you think "
          "about new lenses.",
          avoid=("clean", "scratch", "lens", "lenses", "slide", "sliding", "fog", "steam",
                 "wine", "drinking", "sun", "sunglasses", "dishwasher", "water",
                 # "do i need new glasses if i get headaches" asks whether to get a pair, not
                 # what to do about the ones already on the face
                 "do i need new glasses", "should i get new glasses", "need new glasses",
                 "time for new glasses", "when do i need", "how often")),
    entry("cocktail-code", ("cocktail", ("dress", "code", "wear", "mean", "means", "party")),
          "Cocktail dress code means short dresses or a smart top and skirt for women, and a suit "
          "or smart jacket and trousers for men: dressy, but not formal long gowns or full black "
          "tie. Heels you can stand in for two hours matter more than height.",
          avoid=("drink", "menu", "recipe", "sauce", "prawn", "bar", "make", "mix")),
    # "first-date-outfit", not "first-date": family.py has the other half of a first date (what
    # to talk about), and both entries were written under the same id, so which one answered
    # depended on the phrasing.
    # Phrases, never a bare "date": "what's the date today" and a use-by date are other jobs.
    entry("first-date-outfit", (("first date", "a date", "on a date", "date night",
                                 "second date", "going on a date", "out on a date",
                                 "dinner date"),
                                # wear words only. The bare "what" made every "what ... date"
                                # line this row's - "whats a good first date idea" and "what
                                # should we do on a date night" were answered with what to put on
                                # - and "nervous" made "i'm nervous about a first date" the same
                                # mistake. The outfit is the line that says wear, outfit or
                                # clothes, and the date itself is family's first-date row.
                                ("wear", "wearing", "outfit", "outfits", "clothes",
                                 "what to wear", "should i wear", "dress", "dressed")),
          "Wear the version of your usual clothes that you feel best in, clean and comfortable, and "
          "skip anything you'd be tugging at all evening. A jacket over a nice top covers a cold "
          "walk and a warm bar, and flat or low shoes leave you free to walk somewhere else.",
          avoid=("song", "songs", "music", "playlist", "film", "films", "movie", "album",
                 "gift", "present", "restaurant", "drink", "drinks", "food", "talk about",
                 "conversation", "what to say",
                 # a kitchen line that happens to name the night is a meal: "what should i
                 # cook for a date night" was this card, and a jacket over a nice top is not
                 # dinner. The fit words above were the only ones here, so "cook" and
                 # "dinner" walked straight in.
                 "cook", "cooking", "cooked", "recipe", "recipes",
                 "dine", "meal", "meals", "eat", "eating", "supper", "bake", "baking",
                 "restaurant booking", "book a table", "make for"),
          # "what should i wear on date night" was a traybake: the meal-for-two card keys the
          # same night, and the clothes row has to win when the line asks what to put on.
          # "dinner" on its own is not a meal either: "what should i wear for a dinner date"
          # asks what to put on for it, so a night that is being cooked for is read by the
          # guard below and not by a bare word in the avoid list.
          guard=_the_date_night_is_a_meal,
          bias=2),
    entry("christening", (("christening", "baptism", "naming ceremony"),
                          ("wear", "outfit", "what", "church", "clothes", "put on")),
          "Smart and modest works for a christening: a dress or smart trousers and a nice top, with "
          "a layer you can take off, and shoulders or knees covered for the church. Nothing "
          "showy, and flat shoes if you'll be standing or on grass afterwards.",
          avoid=("clean", "wash", "washing", "dirty", "stain", "stains", "cost", "how much",
                 "gown", "venue", "plan", "order of service", "godparent", "godparents",
                 # the card that goes with the present is a wording job, not a clothes one
                 "present", "gifts", "card", "cards", "write", "writing", "message",
                 "messages")),
    # "birthday party" reads as a family-and-parenting line to the understanding engine, and the
    # conversation's own subject is then "wear birthday party", whose head is "birthday": the
    # party row has to name the words people say for the occasion or the answer is held out.
    entry("party-outfit", (("party", "parties", "birthday", "birthday party", "house party",
                            "leaving do", "leaving party", "anniversary party",
                            # a round-number do is a party said by its age, and "what should i
                            # wear to a 50th" holds no other party word at all
                            "21st", "30th", "40th", "50th", "60th", "65th", "70th", "75th",
                            "80th", "85th", "90th", "100th"),
                           ("wear", "outfit", "what", "dress", "clothes", "put on")),
          "Ask the host what the dress code is, then dress for the kind of party: jeans and a nice "
          "top for a house party, something dressier for a bar or a big birthday. Wear the shoes "
          "you can stand in for four hours, and a layer that survives a warm room.",
          # "what can i bake for a birthday party" was answered with this: the outfit entry saw
          # "party" and "what" and the kitchen was never in its avoid list. Baking is not dressing.
          avoid=("food", "kids", "children", "plan", "organise", "organize", "venue", "decorate",
                 # "my nan is 80 what can we do for her birthday" is a plan, not an outfit:
                 # "birthday" plus "what" was reaching this row
                 "do for", "what can we do", "what should we do", "ideas", "idea",
                 "celebrate", "celebration", "mark the",
                 # a round-number age is not a plan ask: "80th", "90th", "70th" and "60th" were
                 # in this list to keep "what should we do for my mums 80th birthday" out, but
                 # what keeps it out is the asking shape above ("do for", "what should we do",
                 # "celebrate"), and the bare age stood this row down for the person asking
                 # "what should i wear to a 60th birthday party", who got a hedge instead of the
                 # dress code its own words earn
                 "birthday party for", "games", "cook", "cooking", "cake", "music", "serve",
                 "bake", "bakes", "baked", "baking", "baker", "recipe", "recipes", "dish",
                 "dishes", "meal", "supper", "lunch", "buffet", "nibbles", "biscuits",
                 "drink", "drinks", "alcoholic", "cocktail", "cocktails", "mocktail", "wine",
                 "beer", "menu", "snacks", "nibbles", "film", "films", "movie", "song",
                 "songs", "playlist", "music", "album", "game ideas",
                 # "what should we play at a party" was dressed for the party: the row keys the
                 # word "what", and once the plan card stood down for games this was the next
                 # card in the queue. "play" is written with its neighbour, because "the school
                 # play" is still a question about what to wear to it.
                 "game", "games", "to play", "we play", "play a game", "something to play",
                 # a party is also a conversation and a host's present: neither is an outfit
                 "say", "talk", "talk about", "conversation", "small talk", "mingle",
                 "nervous", "strangers", "bring", "brings",
                 # a present, a card and a cake are not clothes: "what should i get him for his
                 # birthday" was answered with the dress code for the party
                 "present", "presents", "gift", "gifts", "get him", "get her", "get them",
                 "buy", "card", "cards",
                 # "third party" is a kind of car cover, and "what does third party only cover"
                 # and "is third party fire and theft enough" were both sent to the party outfit
                 "third party", "third-party", "fire and theft", "insurance", "insured",
                 "insure", "cover", "policy", "premium", "excess", "no claims"),
          # asked with what is worn, so a present for the same party is not this row's: "what
          # should i get my mum for her 70th" names the age and the party and no clothes at all
          guard=_put_on_is_clothes, ask=_WORN_WORDS),
    entry("first-day-work", (("first day", "day one"),
                             ("wear", "outfit", "work", "job", "office", "clothes", "put on")),
          "Dress one step smarter than the job's everyday clothes on your first day: a shirt or "
          "blouse and smart trousers, a jacket if you own one, and closed clean shoes. Look at "
          "photos of the team or the office, and keep the trainers and hoodie for after you've "
          "seen what everyone else wears.",
          # "what should i ask on my first day at a new job" matched on `job` and got the
          # wardrobe, so the questions about the day stand the clothes entry down and let
          # work.py's first-day answer take them.
          avoid=("school", "nursery", "term", "primary",
                 "ask", "asking", "asked", "questions", "question")),
    # Asked by anyone who has given up on it, so the honest answer comes first: the corners
    # never meet, and a flat bundle is the point rather than a rectangle.
    entry("fold-shirt",
          (("shirt", "shirts", "t-shirt", "t-shirts", "tshirt", "jumper", "jumpers", "top", "tops",
            # "how do i keep clothes from creasing in a case" is the same job as a shirt, and the
            # sorting line that used to answer it (take everything out of the wardrobe) does not
            "clothes", "clothing"),
           ("fold", "folding", "folded", "pack", "packing", "suitcase", "case", "drawer",
            "neat", "neatly", "crease", "creases", "creasing", "wrinkle", "wrinkles",
            "wrinkle free", "travel")),
          "Lay it face down and flat, and if it has buttons do them up: a closed shirt is what "
          "stops the front creasing. Fold each sleeve back across the body at the shoulder seam so "
          "it lies along the side, fold the sides in to the middle if it is wide, then bring the "
          "bottom up in thirds. For a suitcase, roll it from the bottom instead, and put the "
          "collars at the edge of the case so nothing heavy rests on them.",
          avoid=("iron", "ironing", "stain", "stains", "wash", "washing", "shrink", "shrank",
                 "smell", "smells", "buy", "size", "fits", "fit", "collar", "button fell",
                 "missing", "hole", "rip", "torn", "moth", "moths", "dress", "wedding",
                 # clearing out a wardrobe is the sorting entry's, not a folding job
                 "declutter", "decluttering", "organise", "organize", "organising", "tidy",
                 "tidying", "crammed", "stuffed", "too much", "storage", "wardrobe", "drawers",
                 "chest of drawers")),
    entry("fold-fitted-sheet",
          (("fitted sheet", "fitted sheets", "bed sheet", "bed sheets", "bedsheet", "bedsheets",
            "sheets", "sheet"),
           ("fold", "folding", "folded", "neat", "neatly", "tidy", "store", "storing", "put away",
            "cupboard", "drawer", "airing cupboard", "properly", "right")),
          "Hold two corners of the same short end and tuck one inside the other so the elastic "
          "sits together, then let the whole sheet hang and give it a shake: it falls into a "
          "rough half. Lay it flat, tuck the two loose elastic corners into the same pocket, then "
          "fold the long side in thirds so the elastic is hidden inside, and fold the bundle in "
          "half. It will not be a perfect rectangle, and it does not need to be - what makes a "
          "sheet easy to store is that it is flat and the elastic is not on the outside.",
          avoid=("bed", "beds", "mattress", "wet", "wash", "washing", "dry", "drying", "stain",
                 "smell", "smells", "iron", "ironing", "change", "size", "single", "double",
                 "king", "cot", "crib", "buy", "cheap", "paper", "print", "cheat", "spreadsheet",
                 "balance", "song", "music", "snow", "ice", "rain")),
    entry("gig-outfit", (("gig", "concert"), ("wear", "outfit", "what", "shoes", "clothes",
                                                "put on")),
          "Wear something you can stand in for hours and won't mind getting warm: jeans or a "
          "skirt, flat boots or trainers, and a layer you can tie round your waist. Leave the "
          "big coat in the cloakroom queue early and don't carry a bag you have to hold all night.",
          avoid=("ticket", "tickets", "book", "refund", "sold out", "set times")),

    # --- choosing and buying ------------------------------------------------
    # "What should I look for in walking boots" is a buying question, and the answer has to be
    # the one for the thing and the use the line names: a boot for a wet hill, a boot for ice and
    # a boot you stand in all day are three different answers. Each row below reads the use off
    # the line and opens with it, and the repair, the blister and the smell of a garment already
    # owned are left to the rows that answer those.
    entry("boots-to-buy",
          (("boots", "boot", "walking boots", "hiking boots", "winter boots", "snow boots",
            "wellies", "wellingtons"),
           ("walking", "hiking", "hill", "hills", "mountain", "rambling", "trek", "winter",
            "snow", "ice", "icy", "wet", "rain", "mud", "grip", "waterproof", "boot cut",
            "bootcut") + _BUYING_WORDS),
          _boots_to_buy,
          # a boot that is already yours is a blister, a smell or a sole that came off, and a
          # boot for a pitch is the surface question: those rows own their own lines
          avoid=("blister", "blisters", "rub", "rubbing", "hurt", "hurts", "smell", "smelly",
                 "leak", "leaks", "leaking", "squeak", "sole came off", "football",
                 "five a side", "5 a side", "rugby", "astro", "studs", "moulded", "shin pads",
                 "ski", "skiing", "riding", "horse", "work boots", "steel toe", "dr martens",
                 "chelsea", "car boot", "boot sale",
                 # Boots is a pharmacy in half the questions that name it: "can i get the
                 # morning after pill at boots" was answered with how to fit a walking boot
                 "pharmacy", "chemist", "morning after", "prescription", "contraception",
                 "emergency contraception", "plan b", "levonelle", "ellaone", "nhs", "gp",
                 "appointment") + _BOOT_CARE,
          bias=2),
    # A knit is chosen for warmth and bought once, and the washing row next door will take any
    # line with "warm" in it: "i want a warm jumper for winter" came back as a wool-wash
    # temperature. The garment and the warmth (or buying) word are the key here, and every care
    # word stands the row down.
    entry("knitwear-buy",
          (("jumper", "jumpers", "sweater", "sweaters", "cardigan", "cardigans", "knitwear",
            "knit", "woolly", "woollies", "wooly", "pullover"),
           # the choosing words only: "bought", "new" and "need" made a shop return ("the shop
           # wont take back a jumper i bought online") and a child's ordinary new jumper into a
           # question about fibre, which neither of them is
           ("warm", "warmest", "warmer", "winter", "cosy", "thick", "thicker", "buy",
            "buying", "best", "which", "what", "choose", "choosing", "worth", "recommend",
            "look for",
            # a comparison of two of the same garment is this question: "is a wool jumper
            # better than acrylic" was a search hedge beside this row
            "better", "worse")),
          "Go by the fibre first: merino is the warmest for its weight and the softest against the "
          "neck, lambswool is thicker and cheaper, and a wool-rich blend of 80 per cent wool and 20 "
          "per cent nylon keeps its shape where a high-acrylic knit pills and holds damp. Buy it "
          "big enough to wear over a shirt, and treat a wool jumper as one you air rather than wash - "
          "that is what keeps it warm for years.",
          avoid=("wash", "washing", "washed", "shrink", "shrank", "shrunk", "stain",
                 "stains", "smell", "smells", "moth", "moths", "bobble", "bobbles",
                 "pilling", "pills", "iron", "dry clean", "store", "storing", "hang",
                 "fold", "repair", "hole", "holes", "darn", "mend", "size up", "too small",
                 # yarn is not a jumper: "what is double knit wool" is a knitting question,
                 # and the knit in the key is the garment, not the ball of wool
                 "yarn", "double knit", "dk", "aran", "worsted", "chunky", "ply", "skein",
                 "ball of wool", "crochet", "knitting", "knitting pattern", "needles",
                 "tension", "gauge", "stitch", "stitches", "pattern",
                 # a jumper that was bought and is not wanted is a consumer question
                 "take back", "taken back", "refund", "refunded", "return", "returned",
                 "returns", "faulty", "shop wont", "wont take back", "online", "wrong size",
                 "doesnt fit", "doesn't fit", "dont like", "don't like"),
          # "which jumper will keep me warm in winter" is this row's line said with "keep", and
          # the cold-weather row reaches the same words: the garment named in the key is what
          # makes this the row for it, so it wins that tie.
          bias=3),
    # Flat feet are a fit question, and the replacement row answered them with when to throw a
    # pair away: "which trainers for flat feet" came back as "replace them once the midsole has
    # gone flat". The foot shape is the key here, the shoe is the second half, and an injury is
    # the body rows' line.
    entry("flat-feet-shoes",
          (("flat feet", "flat foot", "fallen arches", "fallen arch", "high arches",
            "arch support", "arches", "arch"),
           ("shoe", "shoes", "trainer", "trainers", "boot", "boots", "support", "insole",
            "insoles", "best", "which", "what", "buy", "buying", "wear", "walking",
            "comfortable", "help", "need", "choose",
            # "are flat feet a problem" and "is it bad to have flat feet" are the same question
            "problem", "a problem", "bad", "ok", "okay", "matter", "worry", "normal")),
          "Support under the arch matters more than cushioning: a shoe with a firm heel counter and "
          "a removable insole you can swap for an arch-support one (about \u00a320 to \u00a340 from a "
          "pharmacy) is enough for most people with flat feet. A lace-up trainer with a straight "
          "shape and a snug midfoot holds the foot better than a slip-on, and if your feet, shins or "
          "knees hurt when you walk, or one arch has dropped recently, a podiatrist is worth the "
          "visit.",
          avoid=("sprain", "sprained", "broken", "fracture", "numb", "tingling", "swollen",
                 "swelling", "shin splints", "plantar", "heel pain", "surgery", "operation",
                 "baby", "babies", "toddler", "child", "children", "kid", "kids"),
          bias=1),
    entry("trainers-to-buy",
          (("trainers", "sneakers", "sneaker", "trainer"),
           ("falling apart", "fallen apart", "worn out", "wore out", "wearing out", "new pair",
            "need new", "go with", "wear with", "pair with", "suit", "smart", "navy",
            # "when should i replace my trainers" is the replacement question this row answers,
            # and the word it is asked with was in neither half of the key
            "replace", "replacing", "replacement", "time for new",
            "trousers", "chinos", "shirt", "office", "interview", "wedding") + _BUYING_WORDS),
          _trainers_to_buy,
          # an old pair is washed, bleached, deodorised or broken in, and a pair for sport or for
          # a child is another entry's question
          avoid=("smell", "smelly", "stink", "wash", "washing", "clean", "white", "bleach",
                 "blister", "blisters", "rub", "rubbing", "hurt", "hurts", "run", "running",
                 "marathon", "5k", "10k", "gym", "football", "astro", "studs", "child",
                 "children", "kid", "kids", "son", "daughter", "baby", "toddler",
                 "personal trainer", "school",
                 # a pair for a shift on your feet is the standing-all-day row's line, and it
                 # answers it better than "replace the midsole" does: "i need new trainers for
                 # work" was written for the shop floor, not for a worn-out sole
                 "standing", "all day", "on my feet", "work", "nurse", "nursing", "hospital",
                 "warehouse", "kitchen", "shop floor", "shift",
                 # "what socks with trainers" is a question about the sock, and this row answers
                 # it with the trainers to buy: the sock has its own card
                 "sock", "socks",
                 # the shape of the foot is the fit row's question, and it was being answered
                 # here with "replace them when the midsole goes flat"
                 "flat feet", "flat foot", "fallen arches", "fallen arch", "high arches",
                 "arch support", "arch", "arches", "insole", "insoles", "orthotic",
                 "orthotics"),
          bias=2),
    entry("jeans-wear-between-the-legs",
          (("jeans", "jean", "denim", "trousers", "chinos"),
           ("between the legs", "between my legs", "between the thighs", "crotch",
            "wearing out", "wear out", "worn out", "wore out", "wore through", "worn through",
            "wearing through", "rub", "rubbing", "rubbed", "hole in the", "holes in the",
            "inner thigh", "inside of the leg")),
          "That rub is the fabric against itself, so nothing stops it completely, but three things "
          "slow it down a lot: wash them less (once every four or five wears, cold, inside out), "
          "skip the tumble dryer because heat weakens the cotton, and put on a couple of kilos' "
          "worth of a looser fit - fabric that does not meet does not rub. When it goes, patch it "
          "from the inside with an iron-on denim patch before the hole reaches the seam: a patch "
          "costs a few pounds and a repairer charges about ten to put one in properly.",
          # a pair that is ripped, too tight or for sale is another row's question, and so is
          # one with a hole in it already: "how do i fix a hole in the crotch of my jeans" wants
          # the mending row's needle and thread, not this row's why-it-happens.
          avoid=("fix", "fixing", "darn", "darning", "mend", "mending", "repair", "stitch",
                 "sew", "sewing", "hole", "holes",
                 "wash", "washing", "fade", "faded", "fading", "gum", "stain", "stains",
                 "bleach", "dryer", "iron", "hole in the knee", "knee", "knees", "too tight",
                 "fit", "fits", "buy", "buying", "cheap", "brand", "size", "sizing",
                 "smell", "smelly")),
    entry("jeans-to-buy",
          # "shrink" and "shrank" are not in this key: "how do i shrink my jeans", "can i shrink
          # jeans that are too big" and "how do i shrink my jeans back to size" were all told how
          # to try a pair on, because this row keys the word and carries a bias. A pair that is
          # meant to come in is shrink-jeans, and a pair that might come in by accident is
          # cleaning.py's clothes-shrinking.
          (("jeans", "jean", "denim"),
           ("fit", "fits", "fitting", "cheap", "cheapest", "budget", "brand", "brands",
            "who makes", "price", "size", "sizing", "find", "pair", "recommend", "keep")
           + _BUYING_WORDS),
          _jeans_to_buy,
          # care is the other rows': washing, fading, gum, stains and a pair that is too tight
          avoid=("wash", "washing", "washing machine", "fade", "faded", "fading", "gum",
                 "stain", "stains", "bleach", "dry", "drying", "dryer", "iron", "hole",
                 "holes", "rip", "ripped", "torn", "too tight", "smell", "smelly", "sag",
                 "baggy knees",
                 # a pair to be made smaller or bigger is not a pair to be chosen, and "size"
                 # in this row's key took "how do i shrink my jeans back to size" for the
                 # trying-on answer
                 "shrink", "shrank", "shrunk", "shrinking", "back to size", "too big",
                 "baggy", "loose", "stretch", "stretched", "tight"),
          bias=2),
    entry("child-coat",
          # The child word is the gate and not a bought one: without it, "should i buy a puffer
          # jacket" was a child's coat because the buying words are in the same group.
          (("coat", "jacket", "pramsuit", "snowsuit", "all in one",
            # the phrase is here so the row is about the thing the line names: with "winter"
            # read as the line's subject, the answer's own domain (clothing) does not answer
            # the line's topic, and "how do i choose a winter coat for a child" was dropped
            # for want of the word in this row's key
            "winter coat", "winter jacket", "warm coat"),
           ("child", "children", "kids", "kid", "son", "daughter", "baby", "babies",
            "toddler", "toddlers", "boy", "girl", "year old", "car seat", "pram",
            "pushchair", "buggy")),
          _child_coat,
          # "my son wont wear his coat" is not a coat to choose: the fight with it on is the
          # morning card's question, and this row was answering every wording of it with what to
          # look for in a hood.
          guard=not_a_fight_about_clothes,
          # a grown-up's coat is the shopping row's, and the coat a child already has is a wash,
          # a stain or a zip
          avoid=("school shoes", "uniform", "shoes", "trainers", "wellingtons", "wellies",
                 "adult", "my coat", "my jacket", "moth", "moths", "wash", "washing", "clean",
                 "cleaner", "stain", "zip", "broken", "torn", "leak", "leaks", "leaking",
                 "too small", "too big", "outgrew", "grew out",
                 # whether they need one today is the forecast's question: "do the kids need a
                 # coat today" was answered with how to choose one for them
                 "today", "tonight", "tomorrow", "right now", "this morning", "this afternoon",
                 "this evening", "weather", "forecast", "cold out", "chilly out",
                 "raining", "umbrella"),
          bias=2),
    entry("waterproof-trousers",
          # the phrases, not the bare "waterproofs": that is read as a form of "waterproof", so
          # it fitted "should i buy a waterproof jacket" too and this row answered it with
          # trousers
          (("waterproof trousers", "waterproof over trousers", "overtrousers", "over trousers",
            "waterproof leggings", "waterproof pants", "gaiters", "rain trousers"),
           ("need", "worth", "buy", "get", "walking", "walk", "hike", "hiking", "rain",
            "wet", "hill", "hills", "winter", "cheap", "best", "which", "what")),
          "For a day on open hills, yes: waterproof over-trousers weigh almost nothing in a "
          "rucksack and turn a wet walk into a fine one, and above the treeline the wind makes "
          "an umbrella useless. Cheap ones sweat from the inside, so look for taped seams and a "
          "long zip up the leg so you can pull them on over boots.",
          avoid=("jacket", "coat", "fleece", "top", "hat", "gloves")),
    # Keeping warm while you are OUT is a clothes question and the heating note is the wrong
    # one: "how do i keep warm cycling in winter", "... walking in winter" and "... at a
    # football match" were all told to buy a 1kW electric radiator. Two notes, because the
    # person who is moving needs to dress for the effort and the person who is standing still
    # needs everything closed up.
    entry("keep-warm-moving",
          # the wear words are in the first half because half of these lines ask what to put on
          # before they ask about the cold ("what should i wear for a winter commute"), and the
          # activity in the second half is what keeps it off every other clothes question.
          (("warm", "warmer", "warmth", "wear", "wearing", "what to wear", "clothes", "kit",
            "outfit", "dress for"),
           ("cycling", "cycle", "bike", "bicycle", "motorbike", "motorcycle", "scooter",
            "ride", "riding", "commute", "commuting", "run", "running", "jog", "jogging",
            "walk", "walking", "dog walk", "school run", "outside", "outdoors")),
          "Dress for ten minutes in: a thin wicking base layer, a fleece over it and a windproof "
          "shell on top - waterproof rather than thick if it is wet - so you should feel slightly "
          "cold on the doorstep and warm by the first mile. Wind is what makes it cold, so keep "
          "it out at the neck, cuffs and ankles and cover the hands and ears, which is where it "
          "bites first. Take a layer you can tie round your waist or push in a pocket for the "
          "way home.",
          # a heated house is the other question, and so is a cold someone already has, and a
          # child dressed for the cold is its own card
          avoid=("house", "home", "flat", "room", "bedroom", "living room", "boiler",
                 "radiator", "heating", "central heating", "bill", "bills", "mould", "damp",
                 "a cold", "my cold", "got a cold", "with a cold", "sore throat", "cough",
                 "flu", "fever", "hands", "feet", "fingers", "toes", "hat", "gloves",
                 "baby", "babies", "toddler", "child", "children", "kid", "kids", "pram",
                 # getting warm before exercise is the warm-up card, not the clothes one:
                 # "how do i warm up before a run" was told what to wear
                 "warm up", "warm-up", "warming up", "warmup", "before a run", "before i run",
                 "before training", "before exercise", "cool down", "cool-down",
                 # An occasion is the subject and the weather is a detail of it: "im going to a
                 # wedding in june and its outdoors, what should i wear" was dressed for a run
                 # ("a thin wicking base layer... warm by the first mile") because "outdoors" and
                 # "wear" are this card's two keys. Whatever the party is, the clothes question is
                 # about the party, so every occasion named in a line stands this card down and
                 # the occasion's own card answers it.
                 "wedding", "weddings", "funeral", "funerals", "christening", "baptism",
                 "graduation", "interview", "interviews", "job interview",
                 "school concert", "nativity", "prize giving", "leavers", "prom",
                 "party", "parties", "birthday", "anniversary", "dinner", "dinner dance",
                 "meal out", "night out", "first date", "date", "wedding reception",
                 "reception", "theatre", "theater", "the pictures", "church", "service",
                 "court", "tribunal", "hearing",
                 # a wet walk is the walking-kit card's own line, and it names the trousers and
                 # the boots this note does not
                 "wet walk", "rainy walk", "walking in the rain", "walk in the rain",
                 "out in the rain", "wet weather", "rainy day",
                 # a crowd standing still is the other note below, not this one
                 "football", "rugby", "match", "watching", "touchline", "sidelines",
                 "fishing", "golf", "camping", "festival", "bonfire", "fireworks", "standing",
                 # a machine that is "running warm" is not a person dressing for the cold, and
                 # "running" is in the activity half above: "my fridge is running warm" was told
                 # what to wear for a run in winter
                 ) + A_MACHINE_RUNNING_WARM
                 # "warm" and "outside" are enough to bring a line here, so "is it warm enough to
                 # sit outside" was told what to wear for a run. What the sky is doing is the live
                 # information note's answer, and it is a different question from what to put on.
                 + A_WEATHER_ASK,
          # the cold-run note is about the lungs and reads "winter" too: this one is the clothes
          bias=2),
    entry("keep-warm-standing",
          (("warm", "warmer", "warmth"),
           ("football", "rugby", "match", "watching", "touchline", "sidelines", "fishing",
            "golf", "camping", "festival", "bonfire", "fireworks", "outside", "outdoors",
            "standing")),
          "Standing still is what makes it cold, so that is what to dress against: a thermal base "
          "layer, a fleece, a windproof and waterproof coat with the hood up, and boots with a "
          "thick sole, because the ground takes the heat out of your feet. Cover the neck, ears "
          "and wrists, take a cushion to sit on rather than a cold seat, and put a flask in your "
          "bag - a hot drink is worth more than an extra jumper.",
          avoid=("house", "home", "flat", "room", "bedroom", "living room", "boiler",
                 "radiator", "heating", "central heating", "bill", "bills", "a cold",
                 "my cold", "got a cold", "with a cold", "sore throat", "cough", "flu",
                 "fever")
                 # same reading as the moving note above: "is it warm enough to sit outside" is
                 # somebody asking what the sky is doing before they decide to go out at all, and
                 # this note answered it with a thermal base layer
                 + A_WEATHER_ASK),
    # "do i need padded shorts" was answered with the price of a car's front brake pads, which
    # is what a bare "pads" in a key does. The shorts themselves are a small, real question.
    entry("padded-shorts",
          (("padded shorts", "cycling shorts", "chamois", "bib shorts", "padded underpants",
            "padded liner"),
           ("need", "worth", "buy", "what for", "what are", "why", "wear", "should i",
            "do i", "which", "best", "comfortable")),
          "Yes if you ride more than half an hour: the pad is what stops the chafing and the "
          "saddle soreness, and a padded liner worn under ordinary trousers does the same job "
          "without the Lycra. Do not wear underwear underneath, because the seams are what rub, "
          "and a cheap pad is worse than none - look for a flat, seamless one."),
    entry("walking-kit",
          (("walk", "walking", "hike", "hiking", "hill", "hills", "rambling", "trek", "moor",
            "coast path", "ridge"),
           ("wear", "wearing", "kit", "take", "bring", "pack", "need", "waterproof", "rain",
            "wet", "cold", "layers", "layer")),
          "Layers and a waterproof: a thin base layer, a fleece over it, a waterproof jacket with "
          "the hood up in the wind, and over-trousers in the bag for the top of the hill. Wear "
          "boots with real tread and take a spare pair of socks, and keep cotton off your skin - "
          "it holds the water and makes a wet walk cold, where wool or a synthetic layer still "
          "keeps you warm.",
          avoid=("dog", "puppy", "pram", "pushchair", "baby", "toddler", "steps", "pedometer",
                 "miles", "km", "calories", "weight", "lose", "stairs", "marathon", "race",
                 "parkrun", "route", "map", "parking", "pub", "cafe", "holiday", "insurance",
                 # A walk somebody cannot do is a place question, not a kit one: "my dad cant
                 # walk far so we need somewhere flat" and "i cant walk far what do i need" were
                 # both told to wear layers and a waterproof. travel.py's an-easy-walk answers
                 # them, and the same list stands hike-day down there.
                 "cant walk", "can't walk", "cannot walk", "walk far", "walking far",
                 "mobility", "wheelchair", "wheelchairs", "disabled",
                 "slow walker", "bad knees", "bad hip", "somewhere flat", "flat walk",
                 "manage", "manageable", "gentle", "slow", "slowly", "steady", "elderly",
                 "pensioner", "nan", "granny", "grandma", "grandad",
                 # A walk-in centre is not a walk: "how long does a walk in centre take" was
                 # answered with layers and a waterproof because the line carries "walk" and
                 # "take" (@broad-cypress, #answers 111187).
                 "centre", "center", "clinic", "wait", "waiting", "queue", "hospital",
                 "appointment",
                 # a quantity is not a kit list: "how much water should i take on a hike" and
                 # "how many litres do i need for a long walk" carry "take" and "long walk" and
                 # were answered with layers and a waterproof, when the figure they asked for is
                 # travel.py's half a litre an hour.
                 "how much water", "how much to drink", "how much should i drink",
                 "how much liquid", "how many litres", "how many liters"),
          bias=2),
    # A jacket that has started letting water in is a job, not a purchase: "my jacket leaks in
    # the rain" was the listening turn on main, and the coat rows answer how to choose one.
    entry("jacket-reproof",
          (("jacket", "coat", "shell", "raincoat", "waterproof jacket", "gore tex",
            "goretex", "softshell", "outer layer"),
           ("leak", "leaks", "leaking", "leaky", "wet through", "soaks", "soaked", "soaking",
            "water gets in", "gets wet", "let water", "letting water", "no longer waterproof",
            "reproof", "waterproofing", "waterproof my", "waterproof it", "re waterproof",
            "beads", "beading", "damp inside", "seams", "not waterproof",
            "isnt waterproof", "isn t waterproof", "any more", "lets the rain in",
            "lets water in", "keeps me dry", "wont keep the rain out")),
          "Wash it first with a technical wash rather than ordinary detergent, rinse it twice "
          "and then warm it in a low tumble dryer or press it through a cloth with a warm iron: "
          "the heat reactivates the water-repellent finish and the detergent is what kills it, "
          "so it often beads again with nothing else done. If water still soaks in, wash in or "
          "spray on a reproofing treatment (about £10 to £20) and rub a seam-sealer stick along "
          "the shoulders and the seams under the arms, which are where it goes first.",
          # "worth" is not kept out: "my coat got soaked, is it worth waterproofing it" is the
          # job, not the purchase, and the guard tells the two apart by the fault word. Without
          # it "is a waterproof jacket worth the money" was answered with how to wash one.
          avoid=("buy", "buying", "worth it", "is it worth it", "worth buying", "which",
                 "best", "recommend", "choose", "shrank",
                 "shrink", "stain", "smell", "smells", "zipper", "zip stuck", "size"),
          guard=_a_faulty_coat),
]

# "how do i organise my wardrobe" was a hedge. Storing clothes is this domain's job, and the
# answer is a method rather than a product.
ENTRIES.append(entry(
    "wardrobe-organise",
    (("wardrobe", "wardrobes", "closet", "clothes rail", "drawers", "chest of drawers",
      "clothes", "clothing"),
     ("organise", "organize", "organising", "organizing", "declutter", "decluttering", "tidy",
      "tidying", "sort", "sorting", "space", "crammed", "stuffed", "too much", "storage",
      # "what should i keep in my wardrobe" is this entry's own question, so the verb stays a
      # key here; the person who is losing clothes to someone else is kept out by the phrases
      # in avoid below, which name the taking rather than the keeping
      "keep", "keeps")),
    "Take everything out and put back only what you wore last year, in one go, with a bag for the "
    "charity shop by your feet. Then group by what you put on together - work, weekend, gym - "
    "rather than by type, and hang the long things at one end so the space under them takes a box. "
    "Fold knitwear and jeans flat on a shelf (hangers stretch shoulders), keep one hanger style so "
    "nothing snags, and turn the rail so the season's clothes are at eye level. Shoes paired on "
    "the floor, and one in-one-out rule from then on.",
    # a wash or a stain is a different entry, and so is buying one
    avoid=("wash", "washing", "stain", "stains", "smell", "moth", "moths", "iron", "buy",
           "buying", "build", "flat pack", "ikea", "size", "move", "moving", "paint", "doors",
           # "my sister keeps borrowing my clothes" is not a wardrobe to sort: the phrase says
           # who is taking them, and the chat entry that answers it owns the line
           "keeps borrowing", "keeps taking", "keeps stealing", "keeps pinching",
           "borrowing my", "taking my", "stealing my", "pinching my"),
    ask=("organise", "organize", "organising", "organizing", "declutter", "decluttering", "tidy",
         "tidying", "sort", "sorting", "space", "crammed", "stuffed", "too much",
         "keep", "keeps")))

# "how do i stop my sister borrowing my clothes" was a hedge, "how do i get my clothes back from
# my sister" was another, and the line that asked what to say got the money-you-are-owed answer.
# Asking for a garment back is the same job whoever has it, so the entry takes the item and the
# taking, and does not care whose sister it is.
ENTRIES.append(entry(
    "clothes-borrowed",
    (("clothes", "clothing", "hoodie", "hoodies", "jumper", "jumpers", "dress", "dresses",
      "top", "tops", "shirt", "shirts", "jeans", "trainers", "shoes", "coat", "jacket",
      "outfit", "outfits", "wardrobe"),
     ("borrow", "borrows", "borrowing", "borrowed", "lend", "lends", "lending", "lent",
      "pinch", "pinches", "pinching", "pinched",
      # "wears" on its own is the person putting something on, not taking it: "should i wear
      # trainers to the restaurant" was answered with the ask-for-it-back speech. The borrower's
      # side of the line always names whose the thing is, so the phrase carries the person.
      "wears my", "wear my", "wearing my", "wore my", "worn my", "wears them",
      # "should i take a jumper" is packing for the day, not a garment going missing, so the
      # verb only counts with the person it came from.
      "takes my", "taking my", "took my", "take my",
      "give back", "gives back", "gives it back", "give them back",
      "never gives", "never returns", "get back", "back from")),
    "Ask for the one thing, with a day on it: 'can I have the grey jumper back before Friday, I "
    "want it for the weekend' - one item and one date lands, and 'you always take my stuff' does "
    "not. Then agree the rule you can both live with: a drawer or a shelf that is fair game and "
    "everything else asked for first, and keep the pieces you care about out of the shared "
    "hallway. If it keeps happening, say no once and mean it - 'that one's not up for lending' is "
    "a complete sentence, and it does more than a second row about the same jumper.",
    # a wash, a stain or a size is a different entry, and so is the shop
    avoid=("wash", "washing", "stain", "stains", "iron", "ironing", "size", "fit", "fits",
           # "take my measurements" is the tape measure, not a jumper going missing: this row's
           # "take my" is what won the line, so the measuring words stand it down
           "measure", "measures", "measuring", "measured", "measurement", "measurements",
           "measure myself", "tape measure", "size guide", "size chart", "what size to order",
           "shop", "shops", "sale", "sales", "refund", "returns policy", "parcel", "moth",
           "moths", "sew", "hem", "alter",
           # what to put on for an occasion is the dress-code entries' question, and "what shoes
           # should i wear to a wedding" reached this row because "should i" was its gate and
           # "wear" was a key word. Nothing is being borrowed in that line.
           "wear to", "wear on", "wear with", "what should i wear", "what do i wear",
           "what to wear", "wedding", "dress code", "black tie", "cocktail", "smart casual",
           "christening", "funeral", "interview", "first date", "go with", "pair with",
           # sorting out a wardrobe of your own is the declutter entry above: "never wear" and
           # "too much" are how that question reads, and the person is not losing anything
           "never wear", "never worn", "dont wear", "don't wear", "not wearing", "declutter",
           "clear out", "sort out", "too much", "charity", "bag for",
           # a smell, a damp patch or a garment that came back ruined is not a request to have it
           # returned: those are the laundry, the damp and the ruined-thing entries
           "smell", "smells", "smelling", "smelly", "damp", "musty", "odour", "ruined",
           "ripped", "torn", "spilled", "spilt", "stretched", "shrunk", "lost it",
           # "what clothes should i take to portugal" is a packing list and "what clothes should
           # i wear to a wedding" is the wedding's own question: the words for going somewhere
           # belong with the clause, not with the garment, and this entry is only about a garment
           # somebody else is holding.
           "take to", "take on", "bring to", "wear to", "dress for", "pack", "packing",
           "packed", "suitcase", "luggage", "holiday", "abroad", "trip", "wedding"),
    # A statement ("my sister keeps borrowing my clothes") is the chat entry's: it answers with
    # the sympathy and the question that keeps the conversation going, which is what a person
    # who is only sounding off wants. This entry is for the line that asks what to do about it.
    ask=("how do i", "how can i", "how should i", "what should i say", "what do i say",
         "what can i do", "how do i tell", "should i"),
    bias=1))


# --- choosing a garment: one line per garment ------------------------------------------------
# The rows above cover boots, trainers, jeans and a coat, so "what coat should i get" answered
# while "what shirt should i buy" and "what shoes should i buy" reached the search box: the
# knowledge was there for four garments and not for the rest. What decides a garment is two or
# three measurements, and they are not the same ones from garment to garment - a shirt by the
# collar and the shoulders, a jacket by the shoulders alone, trousers by the waist and the seat,
# a shoe by length and width - so the table below is one line per garment and the entry is built
# from it. A garment not in the table still gets the shared advice on how to try one on, which is
# what the fallback row at the end is for.
_OWNING_NOT_CHOOSING = (
    "too tight", "too big", "too small", "too long", "too short", "doesnt fit", "doesn't fit",
    "does not fit", "hole", "holes", "rip", "ripped", "torn", "mend", "mending", "darn",
    "darning", "sew", "sewing", "alter", "altering", "alteration", "shorten", "take up",
    "shrunk", "shrink", "shrank", "stretched", "stretch", "iron", "ironing", "press", "steam",
    "wash", "washing", "clean", "cleaning", "cleaner", "dry clean", "dryer", "bleach", "stain",
    "stains", "smell", "smells", "smelly", "moth", "moths", "bobble", "bobbles", "pilling",
    "child", "children", "kids", "kid", "son", "daughter", "baby", "toddler", "school",
    "uniform", "my ", "the one i", "i already", "already got", "already have",
    # whether something is acceptable to wear somewhere is not how to choose one: "can i get
    # away with smart trousers and a shirt" is about a dress code, and the choosing rows were
    # answering it with how a collar should fit
    "get away with", "got away with", "ok to wear", "okay to wear", "ok for", "okay for",
    "be ok", "be okay", "appropriate", "too formal", "too casual", "dress code", "smart enough",
    "casual enough", "would it be", "is it ok", "is it okay", "can i wear", "could i wear",
    "go with", "goes with", "wear with", "wearing with", "match", "matches", "suit me",
    "look good on",
    # and a garment that is already in the wardrobe is styled or altered, not chosen: "how do i
    # make a cheap dress look expensive" was answered with how a dress should fit
    "make a", "make my", "make this", "make it look", "look expensive", "looks expensive",
    "look cheap", "looks cheap", "look better", "looks better", "style", "style it", "styled",
    "restyle", "upcycle", "refashion", "accessorise", "accessorize", "outfit", "outfits")

GARMENT_FIT = (
    (("shirt", "shirts", "blouse", "blouses", "dress shirt", "dress shirts"),
     "Shirts are decided by the collar and the shoulders, so check those two before anything "
     "else: with the top button done, two fingers should slide inside the collar, and the "
     "shoulder seam should end on your shoulder bone rather than hanging past it. A sleeve is a "
     "cheap alteration and a shoulder is not, so buy for the shoulder and shorten the sleeve to "
     "the wrist bone. In a shop, raise both arms: if the cuffs ride up past your wrist or the "
     "front buttons gape, it is a size too small.",
     ("print", "printed", "tie", "ties", "cufflinks", "collar stays")),
    (("t-shirt", "t-shirts", "tshirt", "tshirts", "tee", "tees", "t shirt", "t shirts"),
     "A t-shirt is decided by the shoulder seam and the neck: the seam should sit on the bone, "
     "and the neck should lie flat with no gap at the collarbone, because a stretched neck is "
     "what makes an old one look old. Cotton of about 180g to 200g a square metre holds its "
     "shape through washes, where a thin 140g one goes limp in a month. Buy a size that fits "
     "now rather than one to shrink into, and expect a plain cotton one to lose a little length "
     "in the first hot wash.",
     ("print", "printing", "printed", "design", "logo", "slogan", "band", "band t", "bleach",
      "tie dye", "tie-dye", "stain", "yellow", "sweat")),
    (("trousers", "trouser", "pants", "chinos", "chino", "slacks"),
     "Trousers are decided by the waist and the seat, and the label size is only a starting "
     "point: the waistband should sit snug with no gap at the back when you sit down, the seat "
     "should be smooth rather than pulling across the pockets, and the pockets should lie flat "
     "instead of flaring out. Then check the length standing in the shoes you will wear them "
     "with - a single break on the shoe, not a puddle. Sit, squat and climb a stair before you "
     "buy: the pair that fails is nearly always tight across the seat.",
     ("hem", "hems", "turn up", "turnups", "waistband", "zip", "button", "pocket", "belt")),
    (("shoes", "shoe", "smart shoes", "leather shoes", "heels", "court shoes"),
     "Shoes are decided by length and width, so buy for the longer foot and the wider one - the "
     "two are rarely the same - and try them late in the day when your feet are at their "
     "biggest, in the socks or tights you will wear. A thumb's width at the toe, the widest part "
     "of the shoe at the widest part of your foot, and no lift at the heel when you walk: if the "
     "heel slips, a smaller size will pinch the toe instead. Leather gives a little, so a "
     "leather shoe should be snug rather than roomy, and a synthetic one will not give at all.",
     ("trainers", "trainer", "sneakers", "boots", "boot", "walking", "hiking", "running", "run",
      "gym", "football", "rugby", "studs", "astro", "school", "blister", "blisters", "rub",
      "rubbing", "hurt", "hurts", "aching", "smell", "smelly", "polish", "suede", "laces",
      "insoles", "heels hurt", "width")),
    (("suit", "suits", "jacket", "jackets", "blazer", "blazers"),
     "A jacket is decided by the shoulders and nothing else matters as much: the shoulder seam "
     "should end on your shoulder bone, and the padding should follow your own line rather than "
     "sit out past it, because a shoulder is the one thing a tailor cannot change much. Then "
     "check the chest - you should be able to slide a flat hand inside the buttoned jacket - the "
     "sleeve, which should end at the wrist bone and show about a centimetre of shirt cuff, and "
     "the seat, where the jacket should just cover it without flaring. Button the middle button "
     "only and sit down in it before you decide.",
     # a jacket for the weather is the coat row's: "should i buy a waterproof jacket" is a
     # shell, not a shoulder seam
     ("hire", "hiring", "rent", "renting", "wedding suit", "groom", "morning suit", "tux",
      "tuxedo", "waistcoat", "tails", "waterproof", "water proof", "rain", "rainy", "shower",
      "winter", "warm", "warmest", "cold", "puffer", "padded", "down", "insulated", "windproof",
      "fleece", "keep me dry", "keep dry")),
    (("dress", "dresses", "frock"),
     "A dress is decided by the bust, the waist seam and the hips together, so try it on in the "
     "order the seams fall: the bust should sit inside the darts rather than above or below them, "
     "the waist seam should land on your natural waist, and the skirt should hang from the hip "
     "without pulling across the front. Then sit down, raise your arms and take a few steps: a "
     "dress that rides up when you sit or lifts when you reach will not get worn. Buy for the "
     "widest of the three and have the rest taken in, which is the cheap direction to alter.",
     ("wedding", "bridesmaid", "prom", "evening", "black tie", "white", "ivory", "hem", "zip",
      "straps", "sleeves")),
    (("jumper", "jumpers", "sweater", "sweaters", "cardigan", "cardigans", "knitwear", "knit"),
     "Knitwear is decided by the shoulder seam and the armhole: the seam should sit on the bone, "
     "and the armhole should let you raise your arms without the whole jumper riding up, which is "
     "what happens when it is cut too narrow across the chest. Wool with a little nylon - about "
     "10% - wears far longer at the elbows than pure wool, and a tightly spun fine knit pills less "
     "than a loose fluffy one. Hold it up to the light: if you can see through it easily it will "
     "go thin at the elbows within a winter.",
     ("wash", "washing", "wool wash", "hand wash", "dry", "drying", "dryer", "bobbles",
      "bobble", "pilling", "pills", "itchy", "itch", "moth", "moths", "hole", "ladder", "snag")),
    (("skirt", "skirts"),
     "A skirt is decided by the waistband and by how it moves: the waistband should sit on your "
     "hip bone rather than riding up to your ribs, and it should not twist round when you walk, "
     "which is the sign it is too loose. Sit down and cross your legs in the fitting room - a "
     "pencil skirt that rides up or pulls across the thighs will not get worn - and check the hem "
     "sits level all the way round, because a skirt cut on the bias can hang unevenly.",
     ("hem", "hemline", "shorten", "take up", "zip", "pleat", "pleats", "wedding", "school")),
)

# A garment bought for an activity is fitted for that activity, and the row that answers the
# activity already knows the number: in a chat that started "i want to start running but my knees
# are shot", "what shoes should i get" is the pair a running shop fits and the 500km replacement,
# not the width of a leather shoe. So a garment ask reads the use off the last few lines and
# answers for it; with no use named it gets the garment's own fit points. One line per use.
_A_USE_OF_A_GARMENT = (
    (("run", "running", "jog", "jogging", "5k", "10k", "parkrun", "marathon", "half marathon"),
     "For running, go to a running shop and let them watch you run: it costs nothing, they fit "
     "for how your foot lands, and £90 to £130 buys the pair that stops the injuries a cheap "
     "trainer causes. Replace them every 500 to 800km, or when the midsole feels flat under the "
     "ball of your foot, and keep a second pair to alternate if you run most days."),
    (("cycling", "cycle", "bike", "commute", "pedal"),
     "For a commute you do not need special shoes: flat pedals with ordinary shoes are fine, and "
     "a stiff sole is the only thing that helps on a long ride. Clip-in shoes are worth it only "
     "once you ride most days and want the pull on the upstroke - then a mountain-bike style "
     "cleat you can walk in beats a road cleat, and budget about £60 with the pedals."),
    (("gym", "weights", "lifting", "deadlift", "squat", "crossfit"),
     "For the gym, a flat, firm sole is what you want: a cheap canvas plimsoll or a proper "
     "lifting shoe keeps you stable under a weight where a cushioned runner wobbles. Save the "
     "cushioned pair for running and use the flat one for anything with a bar."),
    (("walking", "hiking", "hill", "hills", "trek", "mountain", "muddy"),
     "For walking, the boot or shoe should be waterproof with a deep rubber tread and stiff "
     "enough under the arch to stop a stone bruising your foot. Try them late in the day in the "
     "socks you will walk in, with a thumb's width at the toe and no lift at the heel, and break "
     "them in around the house before a long day out."),
    (("standing all day", "on my feet", "shift", "nurse", "hospital", "warehouse", "kitchen"),
     "For standing all day, put the money into a cushioned sole and room at the toes, and buy at "
     "the end of the day when your feet are at their biggest. Two pairs worn alternately last far "
     "longer than one, and a snug heel matters more than a soft one."),
)


def _a_garment_to_choose(fit):
    """The use's answer when the chat named one, and the garment's fit points otherwise."""
    def answer(memory, understood):
        for words, reply in _A_USE_OF_A_GARMENT:
            if _said_lately(memory, words, turns=4):
                return reply
        return fit
    return answer


for _garment_words, _garment_fit, _garment_own in GARMENT_FIT:
    ENTRIES.append(entry(
        "choosing-" + _garment_words[0].replace(" ", "-"),
        (_garment_words,
         ("buy", "buying", "bought", "choose", "choosing", "pick", "picking", "look for",
          "which", "recommend", "worth", "size", "sizing", "fit", "fits", "fitting",
          "cheap", "budget", "price", "spend", "quality", "last", "best", "get", "getting",
          "need", "need a", "shops", "shop for")),
        _a_garment_to_choose(_garment_fit),
        # a garment already owned is a wash, a repair or a stain, and that is another row's
        # question: the words that say "the one I have" stand this row down
        avoid=_OWNING_NOT_CHOOSING + _garment_own,
        bias=2))

# --- what to wear somewhere ------------------------------------------------------------
# "What should I wear to a barbecue", "what do I wear to a graduation" and "is there a dress
# code for the theatre" are one everyday question with a different place on the end of it, so
# the places are rows in a table and the ask is written once. Each row is keyed by the occasion
# and by the words the question is built from: two key parts is what the matcher needs, so
# "wear" plus "barbecue" answers, and a line that only says "barbecue" ("how long do i cook
# sausages on a barbecue") names no clothes word and never reaches the row.
#
# The answers are the ordinary version a friend gives: what to pick, one warning, and what to
# bring, in one to three sentences. Rows are for occasions people go to again and again, not
# for a showcase: add a line here rather than a new entry.
WEAR_ASKS = ("wear", "wearing", "worn", "outfit", "outfits", "dressed", "clothes", "put on",
             "dress code", "dresses", "shoes")

# A wear question is never a wash, a stain, a shop or a repair: those have entries of their own,
# and a line that says "how do i wash a wine stain out of the dress i wore to a party" is the
# stain. Keeping these words out means the occasion rows can key on a bare place name.
WEAR_NOT = ("wash", "washing", "washed", "washer", "stain", "stains", "stained", "iron",
            "ironing", "shrunk", "shrink", "smell", "smells", "smelly", "moth", "moths",
            "size", "sizes", "fit", "fits", "shop", "shops", "sale", "sales", "refund",
            "return", "returns", "cost", "costs", "how much", "buy", "buying", "bought",
            "cheap", "cheapest", "expensive", "clean", "dirty", "sweat", "sweaty", "bleach",
            # and it is never about the things we wear for a reason other than looking right:
            # "should i wear my glasses to the cinema" is a glasses question, not a cinema one
            "glasses", "lenses", "contacts", "hearing aid", "sunscreen", "sun cream", "suncream",
            "spf", "factor 50", "mask", "masks", "earplugs", "plasters", "sunhat",
            # and the music for an occasion is not the outfit for it: "what music should i put
            # on for a dinner party" was "something comfortable and a step nicer than you'd wear
            # at home", because "put on" and the occasion were both here. The listen-when row
            # answers the music for the same occasion.
            # The music is left out of this list: a line that asks what to put on can name the
            # music and still be the outfit - "what should i wear to a music festival" - and the
            # guard reads which of the two the line is asking for.
            )

OCCASION_WEAR = {
    "barbecue": (("barbecue", "barbecues", "barbeque", "bbq", "bbqs"),
                 "Dress for standing about outdoors: shorts or jeans and a light top, with a "
                 "jumper for when the sun goes in. Leave the white things and the dry-clean-only "
                 "at home, because there's smoke, grass and someone with a ketchup bottle."),
    # "what should i wear to dinner" and "what should i wear to a meal out" were punts, though
    # they are the same question as the restaurant one and the commonest way to ask it: the
    # place is only in the line as the meal. The wear ask still has to be there, so "what should
    # i cook for dinner" is untouched.
    "restaurant": (("restaurant", "restaurants", "bistro", "brasserie", "trattoria", "steakhouse",
                    "meal out", "meals out", "a meal out", "dinner out", "eating out",
                    "out for dinner", "dinner tonight", "to dinner", "for dinner"),
                   "Ask when you book what people wear there: smart casual (smart trousers or "
                   "dark jeans and a collared shirt or a nice top) covers nearly every restaurant. "
                   "Shorts and flip-flops are only right somewhere on the seafront."),
    "pub": (("pub", "pubs", "beer garden", "local pub", "pub lunch", "spoons", "wetherspoons"),
            "Jeans and a clean top is right for nearly any pub, with shoes you can walk home in. "
            "Take a warm layer if you'll be in the beer garden after dark."),
    "cinema": (("cinema", "pictures", "movie theatre", "movie theater"),
               "Anything comfortable and warm: cinemas run cold, so a jumper and soft trousers or "
               "jeans, and shoes you can slip off if you like to curl up."),
    "festival": (("festival", "festivals", "weekender", "camping festival", "reading festival"),
                 "Boots, layers and a waterproof, whatever the forecast says, because you'll be "
                 "on your feet on grass for hours. Nothing white, nothing dry-clean-only, and "
                 "nothing you'd be upset to lose."),
    "graduation": (("graduation", "graduating", "degree ceremony", "grad ceremony"),
                   "Guests usually go smart: a dress or a shirt and trousers with closed shoes, "
                   "and a layer, because gowns and halls are either freezing or stuffy. Flats or "
                   "a wide heel are kinder if the photos are on grass."),
    "reunion": (("school reunion", "class reunion", "reunion", "reunions"),
                "Nice jeans or trousers and a shirt or a nice top: the aim is to look like "
                "yourself on a good day, not someone who tried too hard. Ask whoever is "
                "organising whether it's a pub night or a sit-down dinner."),
    "christmas-do": (("christmas do", "xmas do", "christmas party", "office party", "work party",
                      "work do", "festive do", "office christmas party", "christmas dinner",
                      "xmas dinner"),
                     "Ask whoever organised it whether it's drinks in a bar or a sit-down dinner, "
                     "then go smart casual one notch up: dark trousers or jeans with a nice top, "
                     "which works whether people dress up or not. Comfortable shoes, because these "
                     "nights are long."),
    "dinner-party": (("dinner party", "supper party", "dinner at a friends"),
                     "Something comfortable and a step nicer than you'd wear at home: jeans with a "
                     "good top, or a dress with flat shoes. Nothing that needs careful handling "
                     "next to red wine on someone's sofa."),
    "family-party": (("family party", "family do", "family gathering", "family get together",
                      "family christening party"),
                     "Smart casual is plenty: clean jeans or trousers and a nice top, in something "
                     "you can kneel down and move about in if there are small children there."),
    "kids-party": (("kids party", "kids birthday party", "childrens party", "children's party",
                    "toddler party", "soft play party", "kids do", "kids birthday"),
                   "Wear what you can sit on the floor in: jeans and a soft top with closed shoes, "
                   "and nothing pale if there's cake and paint about. A cardigan for the hall, "
                   "because church halls and soft play are cold."),
    # A nightclub is a book club and a golf club too, and the loose form of "clubbing" is
    # "club", which answered "what should i wear to book club" with dancing shoes. Only the
    # phrasings that can mean nothing else are keyed here.
    "night-out": (("night out", "club night", "big night out", "girls night", "boys night",
                   "lads night", "go clubbing", "going clubbing", "night on the town"),
                  "Wear what you can dance in for hours and don't have to hold: dark jeans or a "
                  "dress with shoes you can stand in. Check the club's own rules first, because "
                  "plenty still say no trainers or sportswear."),
    "church": (("church", "mass", "chapel", "mosque", "temple", "synagogue", "service at church"),
               "Smart and modest is the safe read: trousers or a skirt past the knee, shoulders "
               "covered, and shoes you'd wear to a nice lunch. Take a layer, because old buildings "
               "are cold."),
    "theatre": (("theatre", "theater", "the opera", "ballet", "west end", "musical", "the arts"),
                "Most theatres are smart casual now: trousers or dark jeans and a nice top, with a "
                "jacket if it's a big West End or opera night. Nobody minds as long as you're warm "
                "and not in shorts."),
    # a house party is the music table's word too ("what should i wear to a house party" was
    # answered with house records), so the party row has to be a row of its own here.
    "house-party": (("house party", "house parties", "flat party", "housewarming",
                     "house warming", "leaving party"),
                    "Jeans and a top you can move in, plus shoes you can stand in all night, "
                    "because a house party is usually standing up and warm once it fills. Leave "
                    "the coat in the hall and don't wear anything the host's sofa would ruin."),
    "bed": (("bed", "in bed", "to bed", "bedroom", "bedtime", "sleep in"),
            "Cotton rather than polyester, because it breathes and you wake up less clammy: a "
            "t-shirt and shorts or loose pyjama bottoms is plenty, and socks if your feet get "
            "cold. A pair of shorts you'd answer the door in is worth having in the summer."),
    "gym": (("gym", "the gym", "workout", "workouts", "exercise class", "spin class",
             "crossfit", "circuit class", "personal training"),
            "Something that wicks and doesn't need adjusting mid-set: shorts or leggings and a "
            "breathable top, with a sports bra for anything bouncy, and shoes for the work you're "
            "doing - cushioned for running, flat and stable for lifting."),
    # "out" is the place word for the commonest evening there is, and it was missing: "what
    # should i wear out tonight" and "what should i wear to dinner out" were told to put two
    # things in the diary by Friday, and "what should i wear out" was a shrug. The phrases carry
    # the being-out, so a walk or a run in the day keeps its own answer.
    "out": (("out tonight", "going out", "going out tonight", "out for dinner", "out for tea",
             "out for a meal", "meal out", "dinner out", "out for a drink", "out for drinks",
             "out on the town", "out this evening", "out this weekend"),
            "Smart jeans or trousers with a top you like is right for nearly any evening out, and "
            "a jacket you can take off covers a cold walk home and an over-hot bar. Wear shoes you "
            "can walk and stand in, and check the place's own rules if it's somewhere new, because "
            "plenty still say no trainers or sportswear."),
    "flight": (("flight", "flights", "long haul", "long flight", "plane journey",
                "night flight", "overnight flight"),
               "Layers and nothing tight: soft trousers or leggings, a t-shirt with a jumper you "
               "can take off, and slip-on shoes for security. Compression socks are the one thing "
               "that makes a long flight feel better, and a scarf doubles as a blanket."),
}

# What to wear in the weather is the same question as what to wear to a wedding, so the weather
# rows are built with the occasion machinery rather than a new one. They are not in the table
# above because their ask is wider: "what do i need to take if its snowing" and "what should i pack
# for a wet day" are the same question as "what should i wear", and "take" and "pack" cannot join
# WEAR_ASKS, where "what should i take to a wedding" is a present.
_WEATHER_ASKS = WEAR_ASKS + ("take", "bring", "pack", "need", "dressed", "dress for", "kit")

# The weather itself, and what it asks a person to put on. These rows exist because the science
# rows for rain, snow and wind were answering them: those now stand down on the wearing ask
# (A_WHAT_TO_WEAR in lookup.py), and what is left has to be a clothes answer or the person gets
# nothing. The reply is written for the day, not for the physics.
_WEATHER_WEAR = {
    "rain": (("rain", "raining", "rains", "rainy", "wet", "downpour", "drizzle", "drizzling",
              "showers", "showery", "dreich", "pouring", "chucking it down"),
             "A waterproof with a hood is the one thing that decides the day, with a thin layer "
             "underneath rather than a thick coat, because rain gear is warm once you move. Wear "
             "shoes that keep water out - leather or a waterproof boot rather than canvas, which "
             "soaks and stays wet - and take a second pair of socks. Cotton next to the skin is "
             "what makes a wet day cold, so a synthetic or wool base layer is worth more than an "
             "extra jumper."),
    "snow": (("snow", "snowing", "snowy", "sleet", "slush", "icy", "ice"),
             "Layers, a waterproof outer and boots with real tread: snow is fine, ice is what puts "
             "people on the ground, so a deep sole beats a smooth one and anything you can lean on "
             "beats a handbag. Cover the ears, hands and neck, and wear wool or a synthetic base "
             "layer rather than cotton, which holds the damp and chills you. Take the layers off "
             "indoors rather than sweating in them and then going back out."),
    "cold": (("cold", "freezing", "frost", "frosty", "chilly", "bitterly", "cold snap", "minus",
              "below zero", "perishing"),
             "Three thin layers beat one thick one: a base layer, a jumper and a windproof coat, "
             "so you can take the middle off indoors. Cover the neck, ears, wrists and ankles, "
             "which is where the cold gets in, and keep your feet warm with a thicker sock or a "
             "boot rather than a second pair of tights. A hat is worth more than it looks, because "
             "a lot of heat goes off a bare head."),
    "hot": (("hot", "heat", "heatwave", "heat wave", "warm", "sunny", "sun", "scorching",
             "boiling", "humid", "muggy", "sweaty"),
            "Loose, light cotton in a pale colour is the coolest thing to wear, because it lets "
            "air through and reflects the sun; a wide hat and sunglasses are worth more than "
            "another layer of sunscreen. Keep shoulders covered over a long day and wear shoes you "
            "can walk in on hot tarmac. Dark, tight and synthetic is what makes a hot day feel "
            "worse."),
    "wind": (("wind", "windy", "gales", "gale", "gusty", "gusts", "blustery"),
             "A windproof outer layer is the whole trick: a shell over a jumper feels far warmer "
             "than a thick coat the wind goes straight through. Keep it done up at the neck and "
             "wrists, tie long hair back, and skip anything loose or long that flaps. A hat that "
             "covers the ears and a bag with a zip finish the job."),
}

# The weather words "cold" and "hot" are also the names of how a person feels, so a line that
# takes something for one of them is a medicine question, not a clothes one:
#
#     what should i take for a cold   -> "Three thin layers beat one thick one"
#
# The same holds for "pack for a hot holiday", where the weather is the setting of a trip the
# travel rows answer. So the weather rows are only for a line that either asks with a wearing
# word, or is about the weather at all: a health or travel line whose ask is a taking one leaves
# the weather rows alone and keeps whatever those domains had.
# "boiling" is weather in "its boiling out there" and a saucepan in "do i need to boil water to
# kill germs", which was told to wear loose cotton. The hot row reads the word, so the thing being
# boiled is what tells the two apart.
_BOILING_SOMETHING = re.compile(
    r"\bboil(?:ing|ed)?\s+(?:water|the water|an egg|eggs|a kettle|the kettle|rice|pasta|"
    r"potatoes|milk|a bottle|the bottle|nappies|nappy|clothes|the wash|a pan)\b"
    r"|\bto kill germs\b|\bkills? germs\b|\bsterilis\w*|\bsteriliz\w*|\bkettle\b")

# The other order: "how long do potatoes take to boil" puts the spud before the word, and the hot
# row was told to wear loose cotton - twice, for potatoes and for sprouts. A time asked for is not
# a wearing ask at all, so a line that asks how long something takes, and names a pan or a pan
# word, is never the weather. The list is read loosely, because "boiled", "frying" and "oven" are
# the same signal as "boil".
_A_PAN_WORD = re.compile(
    r"\b(?:boil|boils|boiled|boiling|simmer|simmered|simmering|poach|poached|poaching|steam|"
    r"steamed|steaming|roast|roasted|roasting|bake|baked|baking|fry|fried|frying|grill|grilled|"
    r"grilling|toast|toasted|toasting|microwave|microwaved|oven|hob|pressure cook(?:er|ing)?|"
    r"slow cook(?:er|ing)?|air fry(?:er)?|saucepan|poach|blanch|blanched|parboil|parboiled)\b")
_A_TIME_ASKED_FOR = re.compile(
    r"\bhow long\b|\bhow many (?:minutes?|hours?|secs?|seconds?)\b|\bwhat temperature\b"
    r"|\bhow hot (?:should|do|does)\b")

_TAKING_AND_NOT_DRESSING = ("health", "geography-and-travel")
_DRESSING_WORD = re.compile(r"\b(?:wear|wearing|wears|worn|outfit|outfits|dressed|dress"
                            r"|clothes|coat|jacket|shoes)\b")


# "I need to get rid of my cold by friday" was answered with three thin layers, because the
# understanding calls a line like that a general one, so the question was not read as health and
# the clothes row took it. The shapes below say the cold is a virus - ridding yourself of it,
# shaking it, the medicine for it - and no clothes line says them about the weather. A "hot" line
# keeps its row: "how do i stop feeling hot" is a fever, but "do i need a coat, its hot" is the
# weather and names the coat.
_A_COLD_YOU_HAVE = re.compile(
    r"\b(?:get|getting|got|shift|shifting|shake|shaking|fight|fighting|beat|beating|knock|"
    r"kill|killing|cure|curing|treat|treating|stop|stopping|prevent|preventing|dodge|dodging|"
    r"catch|catching|caught|come down with|coming down with|battling|suffering from)\s+"
    r"(?:rid of\s+|off\s+|over\s+|through\s+)?(?:a|an|this|that|my|his|her|their|the|another)\s+"
    r"(?:head |chest |bad |heavy |stinking |rotten |nasty |proper |lingering |summer )?colds?\b"
    r"|\b(?:cold|flu)\s+(?:medicine|medicines|medication|tablets?|syrup|remedies?|cure)\b"
    r"|\b(?:medicine|medicines|medication|tablets?|syrup|remedy|remedies|lemsip)"
    r"\s+(?:for|against)\s+(?:a\s+|the\s+|my\s+|this\s+|that\s+)?colds?\b"
    r"|\b(?:sore throat|runny nose|blocked nose|stuffy nose|sneez\w*|cough|coughing|fever|"
    r"virus|flu|cold sore|cold sores|cold and flu|cold or flu)\b"
    r"|\b(?:feeling|feel|felt|been|am|is|are)\s+(?:\w+\s+){0,2}(?:ill|unwell|poorly|sick)\b"
    # a cold that is a part of the body is the circulation question: "how do i stop my hands
    # getting cold" was answered with "bring pots and hanging baskets in"
    r"|\b(?:keep|keeping|ward|stave|stay)\s+(?:away from\s+|off\s+)?(?:the\s+)?colds?\b"
    r"|\b(?:hands?|fingers?|fingertips?|feet|foot|toes?|ears?|nose)\s+"
    r"(?:are\s+|is\s+|get\s+|gets\s+|getting\s+|go\s+|goes\s+|going\s+)?cold\b"
    r"|\bsymptoms?\b")


def _the_weather_is_the_question(understood):
    """False when the weather word in the line is the ailment or the setting of a trip."""
    if not _put_on_is_clothes(understood):
        return False
    said = " ".join(str(word).lower() for word in (understood.get("words") or ()))
    if _A_COLD_YOU_HAVE.search(said):
        # the cold in the line is a virus, and a virus has no dress code
        return False
    # a saucepan is not weather, whatever the thermometer says
    if _BOILING_SOMETHING.search(said):
        return False
    # and neither is a pan in front of the word: "how long do potatoes take to boil" is a time,
    # not a thing to wear
    if _A_TIME_ASKED_FOR.search(said) and _A_PAN_WORD.search(said):
        return False
    if str(understood.get("topic") or "") not in _TAKING_AND_NOT_DRESSING:
        return True
    return bool(_DRESSING_WORD.search(said))


# A named occasion carries its own weather with it: "what should i wear to a funeral when its
# cold" is the funeral, and the weather row is only there for a line whose weather is the whole
# question. The occasion words are read off the table above rather than typed again, so an
# occasion added there is fenced off here the same day.
_OCCASION_PLACES = tuple(sorted({word for _places, _reply in OCCASION_WEAR.values()
                                 for word in _places}
                                # the big days have their own rows rather than a place in the
                                # table, and a wedding is not a weather question
                                | {"wedding", "weddings", "funeral", "funerals", "wake",
                                   "interview", "interviews", "christening", "prom", "first date",
                                   "date night", "black tie", "smart casual"}))

# "Is it cold enough for a coat?" is the same question as "what should I wear", and on main it
# was answered with the laundry dial: that row keys "cold" and "enough", and this line names both
# without naming a wash at all. The shape is a weather word, "enough for", and a thing you wear -
# the garment is what makes it a clothes question - so the row below keys the garment and the
# "enough", and the dial stands down on the same shape. "Is it hot enough for a fan" keeps the
# fan's own answer, because a fan is not something you wear.
_ENOUGH_FOR_A_GARMENT = re.compile(
    r"\b(?:cold|warm|hot|cool|wet|dry|windy|sunny|chilly|freezing|mild|damp) enough for "
    r"(?:a |an |the |my |your )?(?:coat|thick coat|jacket|jumper|cardigan|fleece|shorts|"
    r"wellies|wellies|boots|hat|gloves|scarf|t-shirt|tshirt|tee shirt|dress|sandals|"
    r"sun hat|raincoat)\b")

_WEARABLE_THINGS = ("coat", "coats", "jacket", "jackets", "jumper", "jumpers", "cardigan",
                    "fleece", "shorts", "wellies", "boots", "hat", "gloves", "scarf",
                    "t-shirt", "tshirt", "dress", "sandals", "raincoat")


def _the_enough_is_about_a_garment(understood):
    """True when the line asks whether it is <weather> enough for something you wear."""
    said = " ".join(str(word).lower() for word in (understood.get("words") or ()))
    return bool(_ENOUGH_FOR_A_GARMENT.search(said))


# A number of degrees is the other way people bring the weather into a clothes question, and no
# word list can hold it: "what should i wear when its 35 degrees" was the university pass-mark
# card, because 35 degrees reads as a mark. The reply below reads the figure and answers the day.
_A_TEMPERATURE = re.compile(r"(?:^|\s)(-?\d{1,3})\s*(?:degrees?|deg\b|°|c\b|degrees c\b)")

def _the_temperature_said(understood):
    """The number of degrees the line names, or None."""
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    found = _A_TEMPERATURE.search(line)
    if not found:
        return None
    try:
        return int(found.group(1))
    except ValueError:
        return None


def _dress_for_the_temperature(memory, understood):
    """What to put on for the number of degrees the line names."""
    degrees = _the_temperature_said(understood)
    if degrees is None or degrees >= 24:
        return ("In real heat, loose light cotton in a pale colour is the coolest thing you can "
                "wear, because it lets air through and reflects the sun. A wide hat and sunglasses "
                "are worth more than another coat of sunscreen, and shoes you can walk in matter on "
                "hot tarmac. Dark, tight and synthetic is what makes it feel worse.")
    if degrees <= 6:
        return ("Three thin layers beat one thick one: a base layer, a jumper and a windproof coat, "
                "so you can take the middle off indoors. Cover the neck, ears, wrists and ankles, "
                "which is where the cold gets in, and a hat is worth more than it looks. Wool or a "
                "synthetic base layer stays warm where cotton goes cold and damp.")
    return ("Layers you can take off, and one of them waterproof: a thin base layer, a jumper and a "
            "shell over the top sees you through a day that starts cold and warms up. Shoes with a "
            "sole rather than canvas, and a bag with a zip, because the British version of this "
            "number comes with rain.")


for _weather, (_weather_words, _weather_reply) in _WEATHER_WEAR.items():
    ENTRIES.append(entry("clothes-" + _weather, (_weather_words, _WEATHER_ASKS), _weather_reply,
                         avoid=WEAR_NOT + ("ice cream", "ice lolly", "ice lollies", "ice cube",
                                           "ice cubes", "sun cream", "sunscreen", "sun lotion")
                         + _OCCASION_PLACES,
                         bias=2, guard=_the_weather_is_the_question))

# The same question asked with a number instead of a weather word. The guard is the figure, so a
# line about a degree course ("a history degree", "did my degree help") never reaches it.
ENTRIES.append(entry("clothes-degrees",
                     (("degree", "degrees", "deg", "°c", "celsius", "centigrade"), _WEATHER_ASKS),
                     _dress_for_the_temperature,
                     avoid=WEAR_NOT + _OCCASION_PLACES,
                     bias=2,
                     guard=lambda understood: (_the_temperature_said(understood) is not None
                                               and _the_weather_is_the_question(understood))))

# The commonest clothes question of all has no weather in it: "what should i wear today" and "do i
# need a coat today" were both answered with the shrug, and a friend answers them with the forecast
# and a rule of thumb rather than with a card. The day word is what makes it today's question, so
# the weather rows (bias 2) still win a line that names the weather, and a named occasion, a
# garment that has to fit or a shop stands down as it does there.
_COAT_ASKS = ("coat", "coats", "jacket", "jackets", "jumper", "jumpers", "cardigan",
              "layers", "layering")
_DAY_WORDS = ("today", "tonight", "tomorrow", "this morning", "this afternoon", "this evening",
              "right now", "later on", "this week", "out today", "out tonight")


def _today_is_the_question(understood):
    """False when the day word belongs to a job, a school or a bed rather than to the weather."""
    if not _put_on_is_clothes(understood):
        return False
    return True


ENTRIES.append(entry(
    "clothes-today",
    (_COAT_ASKS + WEAR_ASKS, _DAY_WORDS),
    "Go by the forecast for the hours you will actually be out rather than for the whole day, and "
    "dress for the coldest and wettest of those hours. As a rule of thumb: under about 10 degrees "
    "a proper coat, between 10 and 18 a jumper with something windproof over it, over 18 no coat "
    "and loose cotton instead. Then one layer you can take off, and a hood or an umbrella if there "
    "is any rain in the forecast - being caught wet on the way home is what ruins a day, not the "
    "temperature.",
    avoid=WEAR_NOT + _OCCASION_PLACES
    + ("work", "working", "office", "school", "college", "uni", "university", "gym", "run",
       "running", "cycle", "cycling", "swim", "swimming", "bed", "sleep", "hospital",
       "court", "travel", "flight", "plane", "interview",
       # a coat being bought, mended or measured is another row
       "buy", "buying", "worth", "worth it", "which coat", "best coat", "choose", "choice",
       "price", "cost", "cheap", "repair", "sew", "alter", "size", "fit", "fits"),
    ask=_COAT_ASKS + ("wear", "wearing", "dressed", "clothes", "outfit", "need", "should"),
    bias=1,
    guard=_today_is_the_question))

# The coat-weather shape, which had the laundry dial for an answer. It is its own row rather than
# a wider clothes-today, because the garment is the question here and the day word is optional.
ENTRIES.append(entry(
    "clothes-enough",
    (_WEARABLE_THINGS, ("enough",)),
    "That is a question about the hours you will actually be out, not about the day: under about "
    "10 degrees, yes, and a proper coat with a jumper under it if you will be standing about; "
    "between 10 and 18 a jumper and something windproof is enough, and over 18 you carry the coat "
    "rather than wear it. Rain decides it more often than cold does, so a waterproof beats a "
    "warmer one that lets water through, and the bits that feel it first are the neck, ears, "
    "hands and feet.",
    avoid=WEAR_NOT + _OCCASION_PLACES
    + ("buy", "buying", "worth", "price", "cost", "cheap", "repair", "sew", "alter", "size",
       "fit", "fits", "which coat", "best coat", "waterproof coat", "washing", "wash"),
    # 3, because the shape is exact and the rows it meets are about owning the thing rather than
    # going out in it: "is it wet enough for wellies" was the pair-already-soaked card, and the
    # coat it named was being bought
    bias=3,
    guard=_the_enough_is_about_a_garment))

# bias 2, not 1: the words in WEAR_ASKS are the question, so a line that carries one of them and
# the place is a clothes question whatever else it sounds like. At bias 1, "what should i wear to
# a house party" lost to the music row that keys "house" with "what should", and "what should i
# wear on date night" lost to the meal-for-two card.
for _occasion, (_places, _reply) in OCCASION_WEAR.items():
    ENTRIES.append(entry("wear-" + _occasion, (_places, WEAR_ASKS), _reply,
                         avoid=WEAR_NOT, bias=2, guard=_put_on_is_clothes))

# "how do i know my shoe size in european sizes" was a search hedge, and it is the one clothing
# question with a table behind it rather than an opinion. The numbers are the adult ones people
# ask for at a shoe shop or an online checkout; the half sizes are left out because they drift by
# brand anyway, and the ask says so rather than pretending to a precision nobody's shoe has.
ENTRIES.append(entry(
    "shoe-size-conversion",
    (("shoe size", "shoe sizes", "trainer size", "trainers size", "boot size", "boots size",
      "what size shoe", "what size shoes", "size shoes", "size shoe", "sneaker size",
      "shoes", "shoe", "eu shoes", "in eu"),
     ("european", "europe", "eu", "uk", "us", "usa", "america", "american", "convert",
      "conversion", "equivalent", "equivalent to", "cm", "centimetre", "centimetres",
      "centimeter", "measure", "measure my foot", "what size", "which size", "am i")),
    "Adult sizes, UK to EU to US. Women: UK 3 = EU 36 = US 5.5, UK 4 = 37 = 6.5, UK 5 = 38 = "
    "7.5, UK 6 = 39 = 8.5, UK 7 = 40 = 9.5, UK 8 = 41 to 42 = 10.5. Men: UK 6 = EU 40 = US 7, "
    "UK 7 = 41 = 8, UK 8 = 42 = 9, UK 9 = 43 = 10, UK 10 = 44 = 11, UK 11 = 45 to 46 = 12. Half "
    "sizes and brands drift about a size either way, so use the brand's own chart when it has "
    "one, and measure your foot instead of guessing: stand on paper, mark the heel and the "
    "longest toe in socks, then add 1.5 to the centimetres and multiply by 1.5 - a 25 cm foot "
    "is an EU 40 - and try shoes on late in the day, when feet are at their biggest.",
    avoid=("dress size", "dress sizes", "bra size", "jeans", "trousers", "shirt size",
           "top size", "clothes size", "clothing size", "jacket", "coat", "school shoes",
           "school shoe", "school uniform", "uniform",
           # a child's feet are a different table and a different question
           "year old", "years old", "toddler", "baby", "babies", "child", "children",
           "kids", "kid", "my son", "my daughter", "kid's", "childs", "childrens"),
    ask=("what size", "what size shoe", "what size shoes", "how do i", "how do i know",
         "convert", "convert to", "in eu", "in european", "in us", "in uk", "equivalent",
         "which size", "am i", "size am i", "do i know my"),
))

# The same table question for clothes, which is asked just as often: "i am a size 6 what is that in
# europe" and "uk 10 in european sizes" were both search hedges. The shoe row above cannot take
# them (no shoe word) and the fitting rows cannot either (they want a garment to fit, not a
# country), so the numbers live here - women's UK to EU to US, and men's chest to EU to US, which
# is the one men actually ask for. The last sentence is the honest part: a chart is a starting
# point, a tape measure and the brand's own chart are the answer.
ENTRIES.append(entry(
    "clothes-size-conversion",
    (("size", "sizes", "dress size", "top size", "clothes size", "clothing size",
      "waist size", "medium", "small", "large"),
     ("in europe", "in european", "in the eu", "in eu", "europe", "european", "eu",
      "in the us", "in us", "in usa", "in the uk", "in uk", "in america", "american",
      "convert", "conversion", "equivalent", "mean in", "what size", "which size", "am i")),
    "Women's clothes, UK to EU to US: 6 = 34 = 2, 8 = 36 = 4, 10 = 38 = 6, 12 = 40 = 8, "
    "14 = 42 = 10, 16 = 44 = 12. Men's chest in inches, UK to EU to US: 36 = 46 = 36, "
    "38 = 48 = 38, 40 = 50 = 40, 42 = 52 = 42. A chart is only a starting point: sizes drift a "
    "whole step between brands, so go by the brand's own size guide and by your measurements - "
    "bust, waist and hips in cm - rather than by the number on the label.",
    avoid=("shoe", "shoes", "trainer", "trainers", "boot", "boots", "sneaker", "sneakers",
           "bra", "bras", "cup size", "hat", "gloves", "ring size",
           # a garment that has to fit, or be worn, is another row's question
           "jeans", "trousers", "shirt", "shirts", "jacket", "coat", "curtain", "curtains",
           "bed", "mattress", "duvet", "rug", "tv", "sofa", "boiler", "radiator", "suitcase",
           "bike", "bicycle", "frame size", "air fryer", "pan", "oven", "tray", "tin",
           "wedding", "weddings", "party", "tent", "tents", "marquee", "table", "tablecloth",
           "gift", "present", "bake", "cake", "turkey", "chicken",
           # "what size drill bit for a wall plug", "what size screws for a shelf" and "what size
           # rawl plug for a wall" were all answered with the women's clothes conversion, because
           # "what size" is the row's ask and nothing in it said the size was a fixing. A size
           # asked about a tool, a fixing or a pipe is that job's question, and this table has no
           # business guessing at it.
           "drill", "drills", "drill bit", "drill bits", "bit", "bits", "wall plug",
           "wall plugs", "rawl", "rawlplug", "rawl plug", "rawplug", "raw plug", "plug",
           "plugs", "screw", "screws", "screwdriver", "bolt", "bolts", "nut", "nuts",
           "washer", "washers", "dowel", "dowels", "shelf", "shelves", "bracket", "brackets",
           "hinge", "hinges", "hook", "hooks", "nail", "nails", "anchor", "anchors", "tile",
           "tiles", "pipe", "pipes", "hose", "cable", "cables", "socket", "sockets", "switch",
           "switches", "aerial", "clamp", "clamps", "spanner", "masonry", "plasterboard",
           "stud wall", "joist", "joists", "timber", "screwfix",
           # the same hole, twice more reported on the board: "what size water tank for a family
           # of four" and "what size generator to run a fridge" were the dress chart. Whatever the
           # size is being asked about, if it is a thing in the house it is not a garment.
           "tank", "tanks", "water tank", "cylinder", "cistern", "boiler", "boilers",
           "radiator", "radiators", "generator", "generators", "inverter", "fuse", "fuses",
           "wire", "wires", "battery", "batteries", "solar", "panel", "panels", "rack",
           "shed", "sheds", "greenhouse", "compost bin", "water butt", "paddling pool",
           "trampoline", "bike", "bikes", "bicycle", "saddle", "helmet", "car seat", "cot",
           "mattress", "duvet", "pillow", "sheet", "sheets", "towel", "towels", "rug", "rugs",
           "blind", "blinds", "shoe rack", "wardrobe", "bookcase", "shelf", "shelves",
           "screws", "screw", "bolt", "bolts", "nut", "nuts", "hook", "hooks", "picture",
           "pictures", "mirror", "frame", "frames", "tv", "television", "monitor", "speaker",
           "speakers", "air fryer", "slow cooker", "oven", "cooker", "fridge",
           "fridge freezer", "freezer", "washing machine", "dishwasher", "tumble dryer",
           "microwave", "kettle", "vacuum", "hoover", "mower", "lawnmower", "strimmer",
           "hedge trimmer", "air purifier", "dehumidifier", "fan", "heater", "wood burner",
           "log burner", "chimney", "flue", "liner", "gutter", "gutters", "water butt",
           "what should i wear", "wear to", "to wear",
           # A card that stores photos has a size, and so does a dress: "what size sd card do i
           # need" was answered with the UK-to-EU clothes table, because "size" was the only
           # word it shared with this row.
           "sd card", "sd cards", "memory card", "memory cards", "micro sd", "microsd",
           "sim card", "sim cards", "storage card", "flash card", "usb stick",
           "hard drive", "ssd", "storage", "phone", "iphone", "ipad", "tablet",
           "battery", "card slot",
           # a child's clothes are sized by age, not by country
           "year old", "years old", "month old", "months old", "toddler", "baby", "babies",
           "child", "children", "kids", "kid", "school", "uniform", "newborn"),
    ask=("what size", "which size", "am i", "size am i", "convert", "conversion",
         "equivalent", "in europe", "in european", "in the us", "in us", "in the uk", "in uk",
         "mean in", "how do i", "what is a size", "whats a size"),
))

# "im a size 14 in the uk" and then "what is that in europe" is how this is really asked: the
# number is said once and the country asked for in the next line. The row above cannot take it
# (no size word in the follow-up), so the number is carried: the last size the person said is
# looked up and the country they ask about is the one answered. A shoe size is not this table
# and a size said two chats ago is not this chat, so both are turned down rather than guessed.
_WOMENS_UK_TO_EU = {6: 34, 8: 36, 10: 38, 12: 40, 14: 42, 16: 44, 18: 46, 20: 48}
_WOMENS_UK_TO_US = {6: 2, 8: 4, 10: 6, 12: 8, 14: 10, 16: 12, 18: 14, 20: 16}
_A_SIZE_SAID = re.compile(r"\b(?:size|uk)\s*(\d{1,2})\b")
_A_SHOE_SIZE = ("shoe", "shoes", "trainer", "trainers", "boot", "boots", "sneaker", "sneakers")


def _the_size_carried(memory, understood):
    """The size the person said a line or two ago, converted to the country they now name."""
    from ..memory import recent

    line = _the_line(understood)
    said = " ".join(str(turn.get("user") or "") for turn in recent(memory, 3)).lower()
    sizes = _A_SIZE_SAID.findall(said)
    if not sizes:
        return None
    number = int(sizes[-1])
    if _any_word(said, _A_SHOE_SIZE):
        return None
    if number not in _WOMENS_UK_TO_EU:
        return None
    if _any_word(line, ("in the us", "in us", "in usa", "in america", "american")):
        return (f"A UK {number} is a US {_WOMENS_UK_TO_US[number]} - that is the women's "
                f"conversion, and men's clothes go by chest size instead. A size is only a "
                f"starting point either way: it drifts a whole step between brands, so go by "
                f"the brand's own size guide and your measurements rather than the label.")
    return (f"A UK {number} is a European {_WOMENS_UK_TO_EU[number]} in women's clothes, and a "
            f"US {_WOMENS_UK_TO_US[number]}. Men's clothes go by chest size instead: 36 in "
            f"chest is EU 46, 38 is 48, 40 is 50, 42 is 52. Sizes drift a whole step between "
            f"brands, so check the brand's own size guide as well.")


ENTRIES.append(entry(
    "clothes-size-carried-on",
    (("that", "it", "this"),
     ("in europe", "in european", "in the eu", "in eu", "in the us", "in us", "in usa",
      "in the uk", "in uk", "in america", "european size", "european sizes", "us size",
      "us sizes")),
    _the_size_carried,
    avoid=("weather", "holiday", "holidays", "visa", "flight", "flights", "driving", "drive",
           "plug", "plugs", "voltage", "time difference", "shipping", "post it", "send it",
           "cost", "price", "cheap", "buy it", "worth", "tax", "live", "living", "moving",
           "work there", "til", "until", "duration", "how long"),
))

# ---- the shops are cut small ----------------------------------------------------------------
#
# "im a size 20 and the shops are cut small", "im a size 16 but i have to buy a 20", "clothes sizes
# are not what they used to be" and "why do i need a bigger size than i used to" were a nod, a
# listening noise, the consumer-rights card about goods matching their description, and the card
# about the version of the rules in force. The size table next door answers a conversion, and the
# question here is why the number moved and what to do about it, which is a measurement, the shop's
# own chart, and the fit of the widest part rather than the label.
_SIZES_MOVED = ("cut small", "cut big", "cut narrow", "runs small", "run small", "runs tight",
                "bigger size", "bigger", "one size up", "two sizes", "size up", "sizes up",
                "not what they used to be", "used to be", "sizes have changed", "changed",
                "different in every shop", "every shop", "each shop", "another shop",
                "stopped doing my size", "stopped making my size", "nothing in the shops",
                "nothing fits", "nothing ever fits", "doesnt fit", "doesn't fit", "dont fit",
                "don't fit", "never fits", "wont fit", "won't fit", "too tight", "too small",
                "too long", "too short", "hate shopping", "hate clothes shopping",
                "have to buy", "have to get", "have to size", "need a bigger", "need the bigger",
                "big bust", "big boobs", "broad shoulders", "wide hips", "tall", "short",
                "lost weight", "put on weight", "went up", "gone up", "size 20", "size 22",
                "size 24", "size 26", "size 18", "plus size", "curvy")
ENTRIES.append(entry(
    "sizes-are-cut-small",
    (("size", "sizes", "dress size", "clothes size", "clothing size", "jeans size",
      "shops", "shop", "clothes", "clothing", "fit", "fits", "fitted",
      # the line that names no garment and no number: "im short and everything is too long"
      "everything is", "everything fits", "nothing is", "everything in the shops"),
     _SIZES_MOVED),
    ("Sizes are not measurements, so treat the number on the label as a shop's opinion: women's UK "
     "sizes have crept up about two steps in fifty years, so a 1970s 16 is roughly today's 12, and "
     "every chain runs its own chart, which is why you can be a 20 in one shop and a 24 in the next "
     "door. Measure yourself once with a tape - bust at the fullest point, waist at the narrowest "
     "bit above the navel, hips at the widest, about 20cm below the waist - write the numbers in cm "
     "and use that shop's own size guide for that garment. Then fit the widest part of you and have "
     "the rest taken in, which is £10 to £20 at a dry cleaner's, and look at the tall, petite and "
     "curve ranges, because they are cut on those same measurements rather than on a number. A "
     "bigger size is a fact about the pattern, not about you."),
    # a shoe, a hat, a drill bit, a bed and a curtain have their own sizes, and the conversion table
    # is a different question from this one
    avoid=("shoe", "shoes", "trainer", "trainers", "boot", "boots", "sneaker", "bra size",
           "cup size", "hat", "gloves", "ring size", "drill", "drill bit", "wall plug", "screw",
           # jeans have their own fitting answer and it says how the three numbers work
           "jeans", "jean",
           # "where can i buy clothes for a size 22" asks for a shop and not for a tape measure
           "where can i buy", "where to buy", "where do i buy", "which shops", "what shops",
           "which shop sells", "where sells",
           "screws", "bolt", "bolts", "pipe", "pipes", "tank", "boiler", "radiator", "mattress",
           "bed", "duvet", "pillow", "sheet", "curtain", "curtains", "rug", "tv", "sofa",
           "suitcase", "bike", "bicycle", "in europe", "in european", "in the eu", "in eu",
           "in the us", "in us", "in usa", "in america", "convert", "conversion",
           "equivalent", "inches", "centimetres", "centimeters", "cm"),
))

# "how do i take my measurements for clothes" was answered "Ask for the one thing, with a day on
# it", and "how do i know what size to order online" with the fourteen-day returns rule: the tape
# measure and the two-sizes-and-send-one-back trick belong together, because that is how an order
# gets its size right.
ENTRIES.append(entry(
    "measure-for-clothes",
    (("measurements", "measure myself", "measure yourself", "my measurements",
     "take my measurements", "take my measure", "how do i measure myself",
     "size guide", "size chart", "size to order", "what size to order", "order online",
     "order clothes", "ordering clothes", "order a size"),
     ("clothes", "clothing", "dress", "jeans", "trousers", "shirt", "top", "jacket", "coat",
      "online", "how", "what size", "which size", "my size", "suit", "bra")),
    ("Measure in a bra or a thin top, tape snug but not tight and level all the way round, and "
     "write three numbers in cm: bust at the fullest point, waist at the narrowest above the navel "
     "(bend sideways and the crease is it), and hips at the widest, about 20cm below the waist. "
     "Add your height and inside leg and you have everything a size guide asks for. Then read the "
     "chart for that particular garment, since a shop's trousers and its coats are cut differently, "
     "and check the reviews for 'runs small' before you choose. On the day, order two sizes and "
     "send one back: you have 14 days to change your mind on anything bought online, and one "
     "return postage is cheaper than a garment that does not fit."),
    avoid=("shoe", "shoes", "trainer", "trainers", "boot", "boots", "drill", "wall plug", "screw",
           "curtain", "curtains", "blind", "blinds", "mattress", "bed", "duvet", "rug", "rugs",
           "tank", "boiler", "radiator", "shed", "window", "door", "room", "carpet", "wall"),
    # "how do i take my measurements for clothes" was the borrow-something card, which read
    # "take" and "for" and answered with a request for a day
    bias=1,
))

# ---- a lace and a ribbon bow -----------------------------------------------------------------
#
# "how do i tie shoelaces", "how do i teach a child to tie shoelaces", "my shoelace keeps coming
# undone", "how do i tie a bow" and "how do i tie a school tie" were all search hedges: `tie-a-tie`
# and `bow-tie` stand down on the word "shoelace" on purpose, so the laces had nowhere to land, and
# a bow on a present is a ribbon rather than anything round the neck. The knot is the same skill
# asked five ways - tying it, teaching it, keeping it tied, on a skate, on a gift - so it is a table
# read by one entry.
_LACE_TEACH = ("teach", "teaching", "learn", "learning", "child", "children", "kid", "kids",
               "son", "daughter", "toddler", "what age", "when can", "old enough", "should be able")
_LACE_UNDONE = ("coming undone", "comes undone", "come undone", "keeps coming", "wont stay tied",
                "won't stay tied", "never stays tied", "untied", "trailing", "trails", "trail",
                "dragging", "drag", "too long", "keep treading on")
_LACE_SKATES = ("skate", "skates", "ice skates", "ice skate", "roller skates", "hockey skates",
                "skating")
_LACE_BOW = ("a bow", "bow on", "gift bow", "present", "ribbon", "gift", "wrapping", "wrapped")

_LACE_KNOT = (
    "Make two loops and tie them like a bow: cross the laces once, take the top one under and "
    "through the gap so the base knot is snug, then bend each lace into a loop, cross the two loops "
    "over, and push one loop down through the hole beneath them. Pull the loops outward rather than "
    "up, and it sits flat. Two things make the rest easy: lace from the bottom up so every row lies "
    "flat, and leave about 10cm of lace after the bow - a long tail is what drags and comes undone.")
_LACE_TEACHING = (
    "About five or six, and it comes quicker if the lace is the practice rather than the shoe: tie a "
    "lace round a table leg, a ribbon round a chair back, or one big shoe on the floor, and teach "
    "the bunny-ears version "
    "first - two loops, cross, push one through. Say one step at a time and let them repeat it five "
    "times before adding the next, and be slow in front of them with your own laces. Fifteen minutes "
    "on a Saturday works better than twenty rushed tries on the way to school, and being allowed to "
    "be bad at it for a few weeks is part of learning it.")
_LACE_UNDONE_REPLY = (
    "It is the knot rather than your tying: a bow on a smooth lace works loose. Tie the first knot "
    "twice - a double knot - for round, waxed or nylon laces, or switch to flat laces with a bit of "
    "texture, and check you have about 10cm of tail after the bow because a long end swings and "
    "pulls itself free. Running for a bus or a bike ride: tuck the ends and loops under the criss-"
    "cross above them and they will stay put all day.")
_LACE_SKATES_REPLY = (
    "Skates want a firmer lace than shoes and nothing left trailing: lace from the bottom, keep the "
    "foot snug through the middle, then pull the top two tight at the ankle so the heel cannot lift, "
    "double knot it, and tuck the ends inside the top of the boot. Do them up with thin socks or "
    "warm feet, because tight laces on cold feet is how toes go numb, and loosen the top two before "
    "you take them off.")
_LACE_BOW_REPLY = (
    "Use a ribbon rather than string, because it holds its shape: make a loop in each hand, cross "
    "the right loop over the left, tuck it behind and bring it up through the gap underneath, then "
    "pull both loops outward until the bow is the size you want. Tape the ribbon to the box "
    "underneath first if the present is heavy, so it cannot slide, and curl the tails over a scissor "
    "blade and cut them on the angle.")


def _a_lace(understood):
    """The lace card: the knot, teaching it, keeping it tied, skates, or a ribbon bow."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    text = " ".join(words)

    def has(options):
        return any(option in words or option in text for option in options)

    # teaching comes before the thing being tied: "how do i teach a child to tie a bow" is the
    # lesson, not the ribbon
    if has(_LACE_TEACH) and not has(_LACE_SKATES):
        return _LACE_TEACHING
    if has(_LACE_BOW):
        return _LACE_BOW_REPLY
    if has(_LACE_SKATES):
        return _LACE_SKATES_REPLY
    if has(_LACE_UNDONE):
        return _LACE_UNDONE_REPLY
    return _LACE_KNOT


ENTRIES.append(entry(
    "tie-a-lace",
    (("shoelace", "shoelaces", "shoe lace", "shoe laces", "lace", "laces", "tie my shoes",
      "tie shoes", "tie laces", "tie a bow", "a bow on", "gift bow", "ribbon", "skates",
      "ice skates"),
     ("how", "tie", "tied", "tying", "knot", "teach", "learn", "properly", "right way", "steps",
      "coming undone", "undone", "trailing", "a bow", "bow", "on a present", "skates", "how do i",
      "my son", "my daughter", "a child", "my child")),
    lambda memory, understood: _a_lace(understood),
    bias=2,
    # a necktie, a bow tie and a bin bag are tied too and each has its own card; a lace that
    # hurt, a shoelace swallowed by a pet and a lost shoe are other questions
    avoid=("necktie", "tie a tie", "tie my tie", "tie his tie", "windsor", "bow tie",
           "black tie", "white tie", "bin", "rubbish", "black bag", "hair", "hands", "wrist",
           "dog ate", "swallowed", "choking", "shoe size", "new shoes", "shoes hurt",
           "blister", "verruca", "orthotics", "laces are too short", "lost a shoe",
           # a lace named and asked about as a thing to buy or to get clean is that question,
           # not the knot: the key's second part ("how") is in every one of these
           "how much", "how long", "what size", "cost", "costs", "price", "cheap", "buy",
           "where can i buy",
           "shop", "clean", "cleaning", "wash", "washing", "whiten", "bleach", "length", "size",
           # the laces of a boot are also the part a footballer strikes the ball with, and that
           # line ("how do i kick a football with my laces") is the skill, not the knot
           "football", "soccer", "footballer", "the ball", "kick a ball", "strike the ball",
           "penalty", "volley", "corner kick", "goal kick")))


# ---- a scarf and a wrapped present ----------------------------------------------------------
#
# Both were search hedges ("how do i tie a scarf", "how do i wrap a present") and both are the same
# kind of question as the laces above: a thing in your hands with a method, asked in a few words.
ENTRIES.append(entry(
    "tie-a-scarf",
    (("scarf", "scarves", "snood", "pashmina", "blanket scarf"),
     ("how", "tie", "tied", "tying", "wear", "wrap", "wrapped", "put on", "knot", "how do i",
      "with a coat", "in winter", "keep warm")),
    "Two ways cover most days. The loop: fold the scarf in half, put the folded end round your neck, "
    "and pull the two loose ends through the loop - it stays put and looks deliberate. The one-wrap: "
    "take it round once and tuck both ends inside your coat, which is the warmest way to wear a long "
    "scarf with a winter coat, because the draught cannot get up under it. A wide blanket scarf "
    "wants folding into a long triangle first and wearing with the point down the back; a thin silk "
    "one loosens off the knot or it will slide all afternoon.",
    avoid=("knitted", "pattern", "wool", "cashmere", "which scarf", "what colour", "what color",
           "gift", "present", "wash", "washing", "clean", "moth", "itchy", "allergy")))

ENTRIES.append(entry(
    "wrap-a-present",
    (("wrap a present", "wrap presents", "wrap a gift", "wrap gifts", "wrapping", "wrapping paper",
      "wrap it", "wrap this", "gift wrap"),
     ("how", "neat", "nicely", "properly", "corners", "paper", "box", "steps", "how do i",
      "no bubbles", "look good")),
    "Put the box on the paper and pull it up each side to see how much you need: enough to come up "
    "and over with about 3cm to spare, no more. Tape the long seam first, crease the folds with your "
    "thumbnail, then do the ends - fold the two corners in to make a triangle, fold the point up over "
    "the box, and tape it flat. Work on the floor with the tape stuck to the table edge so you are "
    "not hunting for the end, and use a bag for anything awkward (a bottle, a helmet, a bike): a "
    "neat bag looks better than a lumpy parcel and takes ten seconds.",
    # a question about the paper itself - what it is made of, whether it recycles - is not how to
    # wrap a box
    avoid=("recyclable", "recycled", "recycling", "recycle", "compost", "biodegradable",
           "environment", "landfill", "cost", "cheap", "roll of", "where to buy", "sold out",
           "post", "postage", "delivery")))

# Denim worn a week between washes makes the smell the whole question, and the laundry rows all
# answer a wash rather than airing it out. The smell words are the key; the machine, a damp room
# and a drawer are other questions and stand this row down.
ENTRIES.append(entry("jeans-smell", (("jeans", "jean", "denim"),
                                     ("smell", "smells", "smelly", "stink", "stinks", "stinking",
                                      "reek", "reeks", "odour", "odor", "fresh", "stale")),
                    ("Air them before you wash them: hang them where a draught gets at them "
                     "overnight, or in the bathroom while you shower, and a day's smell mostly "
                     "goes. When you do wash them, turn them inside out, cold or 30, half the "
                     "usual detergent and an extra rinse - the bacteria sit in the seams, and too "
                     "much soap leaves a film that holds the smell. A cup of white vinegar in the "
                     "rinse clears what is left, and skip the tumble dryer, which bakes it in."),
                    bias=1,
                    avoid=("washing machine", "machine smells", "machine stinks", "damp",
                           "musty", "mould", "mildew", "drawer", "wardrobe smells", "cupboard")))


# --- hair that is always in knots -----------------------------------------------------------
# "my girls hair is always tangled and she cries" reached nothing, and the turn was answered as
# sad news ("that's such sad news, I'm sorry") - a combing problem read as a bereavement. The
# answer is the technique, and it is the same one for a long-haired adult.
ENTRIES.append(entry(
    "tangled-hair",
    (("hair", "hairs", "tangle", "tangles", "tangled", "knots", "knotty", "matted", "tats"),
     ("tangled", "tangles", "tangle", "knots", "knotty", "matted", "birds nest", "detangle",
      # "brush" and "comb" are not here: a child who fights the brush is the family's habits
      # row, and this one is the technique for hair that is already in knots
      "detangling", "cries", "crying", "hurts", "always", "every day", "long", "fine hair",
      "curly", "child", "daughter", "girl", "school", "her hair", "his hair",
      "my daughters", "my girls", "my sons", "my daughter", "my son")),
    "Do it wet and in sections, from the ends upwards: soak the hair with conditioner, hold it "
    "above the knot and work a wide-tooth comb through a couple of inches at a time rather than "
    "dragging a brush from the top. A leave-in detangler and a soft brush with flexible bristles "
    "make the same job much less of a fight, plait it or tie it loosely for bed so the knots "
    "cannot form overnight, and if every morning is still tears then a shoulder-length cut is a "
    "perfectly good answer rather than a defeat.",
    # a haircut, a colour, greasy hair and a child who refuses the brush are other rows
    avoid=("cut", "haircut", "trim", "colour", "dye", "bleach", "highlights", "greasy", "oily",
           "dandruff", "thinning", "hair loss", "falling out", "static", "frizz", "frizzy",
           "flyaway", "flyaways", "split ends", "dry", "damaged",
           "volume", "layers", "straighten", "straighteners", "curling", "wig", "extensions",
           # a child who will not have their hair touched at all is a behaviour question, not a
           # knot one: those lines are the family's habits row
           "wont let me", "won't let me", "refuses", "hates having", "screams", "fighting me",
           "kicks off", "cries when i brush", "crying when i brush", "cries when i comb",
           "hates me brushing", "pubic", "dog", "cat", "pet", "vacuum", "drain", "shower"),
    bias=1))


# ---- the item a line asks for, not the word beside it -----------------------------------------
#
# A line with a clause and then a question is read from the clause. Four from the board on main
# `256b47bd`, each answered by a card that was about the clause rather than the thing wanted:
#
#   im 5 foot 2 and i need trousers for work, what do i look for   -> the standing-all-day foot card
#   my son starts school in september and needs his uniform        -> school-trip costs
#   its my first day at the gym tomorrow and i havent got any kit  -> a cardio starter plan
#   my daughter has a dance show in may and needs a costume        -> "May: Greece or Croatia"
#
# The half that belongs here is coverage: no row was keyed on the item, so the clause word won by
# default. Each row below is keyed on the item - trousers, a uniform, kit, a costume, what to wear
# to a wedding - and the ask is what it answers.
ENTRIES.extend([
    entry("work-trousers",
          (("trousers", "trouser", "pants", "work trousers", "work pants", "chinos", "slacks",
            "workwear", "smart trousers"),
           ("work", "office", "for work", "at work", "job", "look for", "what to look for",
            "buy", "buying", "fit", "fits", "smart", "comfortable", "long day",
            "on a shift", "all day")),
          "For work, four things decide it: the fabric, the rise, the length and the pockets. A "
          "wool-poly blend or a cotton twill with a little stretch creases less and gives when you "
          "sit and stand; a mid rise that sits at the waist stays put through a shift; and the hem "
          "should break once on the shoe, so buy the length that fits you - short and petite "
          "lengths are sold off the rail and cost no more than a tailor. Check a phone goes in the "
          "pocket without pulling, and two pairs of one dark colour is the cheapest way to always "
          "have a clean pair.",
          ask=("work", "office", "look for", "buy", "fit", "what"),
          # a stain, a hem to take up, a muddy pair and an iron are four other answers
          avoid=("stain", "stains", "mud", "muddy", "hem", "take up", "taking up", "shorten",
                 "iron", "ironing", "wash", "washing", "shrink", "shrunk", "rip", "torn",
                 "split", "repair", "suede", "wedding", "funeral", "black tie")),
    entry("school-uniform",
          (("uniform", "uniforms", "school uniform", "school uniforms", "pe kit", "school shoes",
            "school jumper", "school trousers", "blazer"),
           ("school", "buy", "buying", "get", "where", "order", "label", "labels",
            "son", "daughter", "child", "children", "kids", "september",
            "reception", "year 7", "secondary", "primary")),
          "Shop early and buy to sizes you can see: the badge items - the jumper, the blazer, the "
          "PE top - come from the school or its named supplier and the plain shirts, trousers, "
          "skirts and shoes are cheaper in a supermarket, at the same sizes. Go one size up in the "
          "jumper and the coat and buy two of the shirts and trousers, because those are what get "
          "dirty fastest, and go in the first week of August: by the end of the month the common "
          "sizes have gone. Label everything with a laundry marker, shoes and water bottle "
          "included, and ask about second-hand rails - most schools have one.",
          ask=("buy", "buying", "get", "where", "need", "needs", "order", "label", "what"),
          # the school-trip cost card keys "school" and "kit", and the item asked for here is the
          # uniform, so the specific row wins the tie
          bias=3,
          # term dates, admissions, trip costs and a nervous first day are four other answers,
          # and so are washing, ironing and mending: this row is the buying half only
          avoid=("term dates", "term", "admission", "admissions", "apply", "application",
                 "catchment", "trip", "trips", "cost", "costs", "fees", "nervous", "anxious",
                 "worried", "crying", "bully", "bullied", "friends", "teacher", "homework",
                 "wash", "washing", "washed", "iron", "ironing", "stain", "stains", "stained",
                 "shrink", "shrunk", "lost", "missing", "get out", "gets out", "come out",
                 "gum", "ink", "paint", "mud", "blood", "grease", "glue", "crayon", "marker",
                 "pen", "felt tip", "blot", "remove")),
    entry("gym-kit",
          # "what to wear" was in the key and "need"/"buy"/"wear"/"pack" filled the second half, so
          # this card answered every "what to wear to a funeral" line as well - nine of sixteen
          # typed occasion lines came back with the first-session list. The words that say the
          # person is asking are the ask below; both halves of the key are the gym itself.
          (("kit", "gym kit", "gym bag", "gym clothes", "what to wear", "wear", "wearing",
            "outfit", "need", "needs", "buy", "pack", "nothing to wear"),
           ("gym", "first session", "changing room")),
          "For a first session you need very little: shorts or leggings that stretch, a t-shirt, "
          "trainers with a bit of support, a water bottle, a small towel and a padlock for the "
          "locker. That is the whole list - no gym turns anyone away for supermarket kit, and the "
          "machines are set up for exactly that. Wear what you already own, wash it after each "
          "session, and only buy a second set once you know you are going twice a week.",
          ask=("need", "needs", "what", "wear", "buy", "pack", "havent got", "haven't got",
               "what to wear", "nothing to wear", "kit"),
          # the beginner's plan and the induction card key "gym" too, and this is the kit question
          bias=2,
          # a plan, a routine and a beginner's programme are the fitness rows' questions
          avoid=("plan", "programme", "program", "routine", "schedule", "how often", "how many",
                 "beginner", "start running", "weights", "cardio", "sore", "ache", "hurts",
                 "membership", "cancel", "contract", "price", "cost", "shoes for running",
                 "five a side", "football", "rugby", "hockey", "cricket", "netball", "match",
                 "pitch", "astro", "shin pads", "studs", "racket", "swimming", "cycling",
                 # what to bring is `a-gym-bag-kit`'s list, which names the towels, the padlock
                 # and the bottle; this row answers what to wear and what a first session needs
                 "bring", "bringing", "take with", "packing")),
    entry("a-show-costume",
          (("costume", "costumes", "fancy dress", "outfit for the show", "leotard", "tutu",
            "show costume", "nativity costume"),
           ("dance", "show", "play", "school play", "nativity", "performance", "concert",
            "ballet", "where", "get", "buy", "hire", "make", "find", "need", "needs")),
          "Ask the teacher or the dance school first: for a show they usually name a supplier, "
          "sell the costume themselves or keep a rail of spares, and buying the wrong shade of "
          "leotard wastes the money. If it is yours to sort, hiring costs less than buying for one "
          "night, fancy-dress shops and second-hand marketplaces have plenty a week before, and a "
          "plain base layer with two bought accessories reads perfectly well from the audience.",
          ask=("where", "get", "buy", "hire", "make", "find", "need", "needs", "what"),
          # a party to go to, a dress code and a gig are other rows
          avoid=("party", "halloween", "dress code", "black tie", "cocktail", "gig", "festival",
                 "sewing machine", "pattern", "fabric shop")),
    entry("wedding-guest-wear",
          (("wedding", "weddings"),
           ("nothing to wear", "wear", "wearing", "outfit", "what do i wear", "dress", "suit",
            "guest", "guests", "smart"),
           # the third part is how the question is asked: the registry and gift rows key
           # "wedding" and one other word, so a what-shall-i-wear line has to carry the asking
           ("ideas", "any ideas", "what should i wear", "what do i wear", "nothing to wear",
            "suggestions", "help", "need", "needs", "should", "suitable", "appropriate")),
          "Start from the invitation: the dress code, the time and the venue settle nearly all of "
          "it, because a 2pm church wedding and a 6pm hotel one want different clothes. With no "
          "code, go one step up from your smartest everyday outfit - a mid-length dress or a "
          "tailored trouser suit in a dark or jewel colour, closed shoes that cope with grass, and "
          "a layer for the evening. Borrow or hire if it is one wear; nobody remembers a guest's "
          "outfit twice, and comfort is what you will notice on the day.",
          ask=("wear", "wearing", "outfit", "ideas", "dress", "suit", "smart"),
          # the gift amount and the white-dress card both key "wedding"; what is asked here is
          # what to wear. The gift card answers "nothing to wear" too if the tie is left alone,
          # so this row carries the nudge rather than a fence on the gift card.
          bias=2,
          # every other what-shall-i-wear line keeps the card it has: the white-and-cream answer,
          # the black-tie answer, the hat and the shoes. Only a shortage is ours.
          guard=_an_outfit_shortage,
          # the gift, the white dress, the speech, the music and the seating are other answers
          avoid=("gift", "gifts", "present", "how much", "money", "white", "ivory", "speech",
                 "seating", "plus one", "rsvp", "invite", "invitation wording", "photographer",
                 "music", "song", "songs", "playlist", "dj", "band", "toast", "reading")),
    # --- the clothes that no longer fit -----------------------------------------
    # Not a laundry question and not a shopping-size question about one garment: somebody has
    # changed shape and the whole drawer is the problem. "none of my clothes fit after a year
    # off, what should i buy first" was answered by the ironing card, because "clothes" and
    # "none" are its words, and "my clothes dont fit anymore" was a punt.
    entry("clothes-that-no-longer-fit",
          # no "jeans": a pair of jeans that no longer fits is the jeans-size card's line, and
          # that card is the more useful answer ("fitted by three numbers, try either side")
          (("nothing fits", "none of my clothes", "my clothes", "my trousers",
            "my shirts", "my dresses", "my tops", "wardrobe", "clothes", "trousers",
            "shirts", "shirt", "dresses", "dress", "tops", "outfits", "outfit", "dress size",
            "sizes", "size"),
           ("dont fit", "don't fit", "doesnt fit", "doesn't fit", "does not fit",
            "no longer fit", "not fitting", "nothing fits", "fits", "fit", "too tight",
            "too small now", "gone up", "gone up a size", "gone up two sizes",
            "dress sizes", "dress size", "new wardrobe",
            "buy first", "what do i buy", "what should i buy", "where do i start",
            "start again", "replace", "replacing", "replace it")),
          _the_size_you_are,
          ask=("buy", "fits", "fit", "wear", "size", "sizes", "wardrobe", "start", "do"),
          bias=2,
          # a return, a refund, a garment that shrank or a repair is another row's question, and
          # the iron that is not needed is the ironing row's whatever the line says about clothes
          avoid=("return", "returns", "refund", "bought online", "send it back", "take it back",
                 "exchange", "washing machine", "shrank", "shrink", "shrunk", "iron", "ironing",
                 "stain", "stains", "hole", "holes", "zip", "broken", "button", "sew", "alter",
                 "tailor", "hem", "wedding", "interview", "funeral", "maternity", "uniform",
                 # a garment that can be let out is the alterations row's question
                 "let out", "let it out", "let them out", "taken in", "take it in", "alter",
                 "altered", "alterations",
                 # the size of one shirt is the shirt-size row's question, and a tape round
                 # the neck is what it answers; the same goes for a length to turn up
                 "shirt size", "size shirt", "which size shirt", "what size shirt",
                 "know my size", "what size am i", "what size should i", "shirt collar",
                 "collar size",
                 # the tape round the body has its own card, and it is a better how-to than
                 # "measure yourself once" is: "how do i measure myself for clothes" keeps it
                 "measure myself", "measure yourself", "measure my body", "my measurements",
                 "take my measurements", "how do i measure", "what measurements",
                 "hem", "hems", "take up", "taking up", "turn up", "shorten")),
    # --- the same clothes on a shorter frame --------------------------------------
    # "im 5 foot 2 and everything is too long, what about trousers" was a punt, "i am 5 foot and
    # sleeves are always too long" a nod and "what is petite sizing" a "tell me what you have got
    # so far". The hemming how-to answers "how do i take up a hem" and keeps it; what these lines
    # are asking is which clothes to buy and what a petite range actually changes.
    entry("clothes-that-are-too-long",
          (("trousers", "jeans", "sleeve", "sleeves", "dress", "dresses", "skirt", "skirts",
            "coat", "coats", "clothes", "everything", "hem", "hems", "petite", "arms", "legs",
            "jacket", "jackets", "shirt", "shirts", "jumpsuit"),
           ("too long", "always too long", "petite", "sizing", "take up", "taking up", "shorten",
            "shortened", "what length", "short legs", "short arms", "short frame", "5 foot",
            "5ft", "5 ft", "4 foot", "4ft", "4 ft", "alter", "alterations")),
          "Petite ranges are cut shorter in the body as well as the leg, so start there rather "
          "than on the standard rail - most high-street shops carry one online, and the rise and "
          "the sleeves come down with the hem. If something you like has no petite cut, buy it to "
          "fit the widest part (hips or shoulders) and have the length taken up: a hem is about "
          "£10-15 at a dry cleaner or a local tailor and takes a few days. Turn a trouser cuff up "
          "once rather than twice, and check the shoulder seam sits on the bone - if it hangs off "
          "the shoulder, no hem will rescue it.",
          # no ask words: "i am 5 foot and sleeves are always too long" states the problem and
          # asks nothing, and the two parts already say it is a length question
          # the how-to for one garment is the hemming card's, a shop's stock is not a fact, and a
          # wedding or a uniform has its own fitting row
          avoid=("take up a hem", "take up the hem", "how do i hem", "sew", "stitch", "needle",
                 "iron", "press", "shrank", "shrink", "wedding", "uniform", "school", "interview",
                 "funeral", "where can i buy", "stock", "shop near", "weight", "diet",
                 # the size of one shirt is the shirt-size row's question, not a length to
                 # buy shorter: "which size shirt should i buy" was this row's petite card
                 "shirt size", "size shirt", "which size shirt", "what size shirt",
                 "know my size", "what size am i")),

    # --- the garment that is nearly right ------------------------------------------
    # "my only suit is too small" was a nod, "can a suit be let out" a punt and "my trousers are
    # too tight" the jumper-soak trick, which is the answer for something that shrank in the wash
    # and not for a person whose size changed. What is missing is the one card about altering a
    # garment that exists: how far the seams allow, what a tailor charges, and the one part that
    # cannot be changed.
    entry("a-garment-that-can-be-altered",
          (("suit", "suits", "jacket", "jackets", "blazer", "trousers", "dress", "shirt",
            "coat", "skirt", "waistband", "waistline", "jeans", "clothes", "outfit", "shorts",
            "top", "tops", "shirts", "blouse"),
           ("too small", "got too small", "got small", "come up small", "came up small",
            "too tight", "let out", "let it out", "let them out", "taken in",
            "take it in", "taking in", "alter", "altered", "alterations", "alteration",
            "tailor", "made bigger", "make them bigger", "loosen", "doesnt fit", "doesn't fit",
            "does not fit", "fits badly", "tight",
            "tight across", "tight around", "take a suit in", "take in a suit",
            "to take in", "took it in")),
          ("A tailor can usually take a garment out by about one size, and a trouser waist by "
           "about 5cm, because what allows it is the seam allowance still inside: a waist or a "
           "hem is \u00a320-40 and a jacket \u00a340-80, done in a few days. Judge it on the "
           "shoulders - they can be taken in a little but never let out, so a jacket tight "
           "across the back is the one to pass on. Take the trousers with the jacket so the "
           "length is set with the shoes you will wear, and it is worth it on a suit whose cloth "
           "is decent, not on one that has gone shiny at the seat."),
          bias=3,
          # something that shrank in the wash is the washing row's, a garment to buy is the
          # wardrobe row's, and a return is the shop's
          avoid=("shrank", "shrunk", "shrink", "in the wash", "washing machine", "dryer",
                 "tumble", "conditioner", "return", "returns", "refund", "bought online",
                 "send it back", "take it back", "wedding", "uniform", "interview", "funeral",
                 "maternity", "stain", "stains", "hole", "holes", "zip", "broken", "button",
                 "iron", "ironing", "sew a", "sewing", "knitting", "wool", "jumper", "cardigan",
                 "what should i buy", "buy first", "new wardrobe", "where do i start",
                 # a pair of jeans that is tight is the jeans-size card's line
                 "jeans are too tight", "jeans too tight", "jeans are tight", "jeans are snug",
                 # length is the petite and hemming row's question, not the tailor's letting out
                 "too long", "too short", "petite", "5 foot", "5ft", "what length",
                 "short legs", "short frame", "take up", "taking up", "hem")),
    # --- the size of one shirt -----------------------------------------------------
    # "how do i know my shirt size" was a search hedge, "what size shirt am i" the model-number
    # card and "which size shirt should i buy" the petite row, none of which says how a shirt is
    # sized. The neck and the chest are two numbers anybody can take at home, so they get a card.
    entry("a-shirt-size",
          (("shirt", "shirts", "blouse", "blouses", "collar", "dress shirt", "dress shirts",
            "formal shirt", "formal shirts", "work shirt", "work shirts", "t shirt",
            "t shirts", "tee shirt"),
           ("size", "sizes", "sizing", "what size", "which size", "know my size", "my size",
            "size am i", "measure", "measure myself", "measure my", "measurements",
            "fit me", "fits me", "will it fit", "neck", "chest", "sleeve length",
            "sleeves")),
          "A shirt is sized by the neck and the chest: measure round the base of the neck where "
          "the collar sits, with one finger's room, and round the chest at the widest part under "
          "the arms, over a shirt you would wear underneath. A dress shirt is sold by the neck in "
          "inches plus the sleeve length - a 15 in neck is about a 38 in chest and a medium in "
          "most casual ranges, 15.5 about 40, 16 about 42 - and a casual shirt goes by the chest "
          "alone: 36-38 in is a small, 39-41 medium, 42-44 large, 45-47 extra large. Use the "
          "shop's own chart, because the same letter is up to two inches different between them, "
          "and take the tape over what you would wear it with rather than against bare skin.",
          bias=2,
          ask=("size", "sizes", "what size", "which size", "how do i", "know", "am i",
               "measure", "buy", "should i"),
          # a shirt to be cleaned, mended, shortened or picked for an occasion is another row's
          # question, and a size asked of a body that is a child's is a different chart
          avoid=("iron", "ironing", "stain", "stains", "shrank", "shrink", "shrunk", "hole",
                 "holes", "zip", "button", "buttons", "sew", "stitch", "tailor", "alter",
                 "hem", "hems", "too long", "too short", "take up", "collar stiff", "yellow",
                 "sweat", "wash", "washing", "bleach", "dry clean", "school", "uniform",
                 "wedding", "interview", "funeral", "child", "children", "kids", "kid",
                 "toddler", "baby", "babies", "year old", "years old", "gift", "present",
                 "where can i buy", "shop near", "stock", "dress size", "bra size",
                 # a shirt for a screen, a band or a team is a printed one, not a fitting
                 "print", "printed", "design", "logo", "band", "team", "stainless")),
])

# A garment that no longer fits is the commonest clothes question after "how do i wash it",
# and every row above answers a different one: shrinking is the wash, stretching is a knit, a
# tight pair of jeans is denim giving. What a person means by "my suit doesnt fit any more" is
# whether it can be saved, and that is one answer whatever the garment is.
ENTRIES.append(entry(
    "a-garment-that-no-longer-fits",
    (("suit", "suits", "jacket", "jackets", "blazer", "trousers", "trouser", "chinos",
      "waistcoat", "dress", "dresses", "skirt", "shirt", "shirts", "coat", "coats",
      "shorts", "uniform", "waistband"),
     # the ask is what to do about the fit: let it out, take it in, or have a tailor look at it.
     # "too tight" and "too small" alone are not enough - a knit that came out small and a pair
     # of jeans that pinches have their own rows, and both avoid this one.
     ("let out", "letting out", "let the", "take in", "taking in", "taken in", "take it in",
      "alter", "altered", "altering", "alteration", "alterations", "tailor", "tailors",
      "too tight", "a bit tight", "so tight", "too small", "too snug", "snug",
      "doesnt fit", "doesn't fit", "dont fit", "don't fit", "not fit", "no longer fits",
      "doesnt fit any more", "does not fit", "stopped fitting", "wont fit", "tight across",
      "bigger", "made bigger", "fit me again", "save it")),
    ("A tailor can usually save it. What they can change: a jacket taken in at the sides, the "
     "sleeves shortened, the hem let down an inch or two, and trousers let out about one size "
     "(2-4cm) if there is seam allowance left inside the waist. What nobody can fix is a jacket "
     "that is tight across the chest or whose shoulder seam sits past your shoulder bone - that "
     "is a size up, and no alteration makes it right. A local alterationist charges £15 to £40 "
     "for a jacket taken in and £10 to £25 for a hem, usually inside a week; ask them to pin it "
     "on you so you can see the fit before they cut.",
     # Both lines stand alone: the pool is picked from at random, so a second line that only
     # makes sense as a follow-up ("a bigger size is often cheaper") is half the answers to
     # "can you let out a jacket", and it says nothing.
     "Check the inside of the seam first: most jackets and trousers have 2-4cm of fabric "
     "folded in at the waist and side seams, which is one size, and letting it out costs £10 to "
     "£40 at a local alterationist. If it is tight across the shoulders or the chest, no "
     "alteration fixes it - buy the size up and have the waist taken in instead."),
    # a garment that shrank in the wash, a knit to stretch back, a tight pair of jeans and a
    # garment to buy are other rows, and each of them says so on the way in
    avoid=("shrunk", "shrank", "shrink", "shrinking", "in the wash", "washing", "washed",
           "dryer", "tumbled", "tumble", "came out small", "the wash",
           "stretch", "stretched", "stretch it", "stretch them", "stretch out",
           "jeans", "denim", "jumper", "jumpers", "cardigan", "knitted", "knit", "wool",
           # a bare "what" or "which" here killed the row's own asks ("my suit is too small
           # what do i do" scored 5 and then stood down on its own avoid word), so the buying
           # words are the phrases a person buys with, not the question's own words
           # a garment just bought is a returns question ("i bought a coat but it doesnt fit"
           # got the fourteen-day returns card, which is the right answer), so the buying
           # words fence this row off
           "bought", "buy", "refund", "return", "returns", "exchange", "receipt",
           "should i buy", "what suit", "which suit", "what jacket", "which coat",
           "brand", "brands", "cheap", "sale", "shop", "sell", "selling",
           "throw it", "bin it", "donate", "charity"),
    bias=1))
