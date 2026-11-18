"""Cleaning and laundry: the everyday jobs and stains, kept as data.

The answers lane owns this domain. It sits next to bot/knowledge/home.py: home is the
DIY and the fixtures (the boiler, the blocked sink, the radiator), this is the washing,
the stains and the tidying up, which is what people ask about far more often.

Entries are keyed by the thing and the problem (the bedsheets, the grease on a shirt,
the trainer smell) rather than by wording, so "how do I get grease out of a shirt" and
"grease stain on my top" reach the same answer. Advice is the ordinary version a careful
neighbour gives: the cheapest thing that works first, what not to do (heat on a protein
stain, bleach on wool), and a number where a number helps.
"""
import re

from .lookup import (FOOD_NAMED, FOOD_SUBJECT, HOW_OFTEN_WORDS, entry, food_has_gone_off,
                     the_line,
                     the_thing_has_gone)

# The topics this domain answers (bot/understanding/topics.py). Cleaning is a home job in
# this bot's reading, so it joins home.py's topic and answers.py declares the union.
ANSWERS = ("home-and-diy",)

# A room or a fixture that keeps its own answer, said on its own in a follow-up: "how often
# should i clean my house" then "and the bathroom", or "how do i clean a whole house" then
# "what about the kitchen". The avoid list stands this row down for a single line that names
# one of them, but a follow-up is read against the guard and not the avoid list, so the same
# words have to be a guard as well or the follow-up gets this card's middle again.
_ROOM_WITH_ITS_OWN_CARD = (
    "kitchen", "kitchens", "bathroom", "bathrooms", "toilet", "toilets", "loo", "bath",
    "shower", "sink", "basin", "oven", "fridge", "freezer", "washing machine", "dishwasher",
    "microwave", "kettle", "carpet", "carpets", "rug", "rugs", "mattress", "sofa", "curtain",
    "curtains", "blind", "blinds", "window", "windows", "grout", "skirting", "cupboard",
    "cupboards", "wardrobe", "garage", "garden", "gutter", "gutters", "roof", "patio",
    "decking", "driveway", "fence", "conservatory", "gutter", "gutters", "roof",
)


def _not_a_room_with_its_own_card(understood):
    """True unless the reading names a room or a fixture that has its own card.

    `understood` may be None (a caller reading a line with no reading), and a guard that cannot
    take that takes the whole turn down rather than one row.
    """
    if not understood:
        return True
    words = understood.get("words") or ()
    if not words:
        return True
    said = {str(word).lower() for word in words}
    line = " " + " ".join(str(word).lower() for word in words) + " "
    line += str(understood.get("plain") or understood.get("text") or "").lower() + " "
    for word in _ROOM_WITH_ITS_OWN_CARD:
        if " " in word:
            if word in line:
                return False
        elif word in said:
            return False
    return True


def _bleach_down_the_drain(memory, understood):
    """A capful of thin bleach in a drain is fine; it will not clear a blockage.

    The one thing that matters is what it does not do, because people reach for bleach when the
    water is standing there and it only takes the smell away.
    """
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in text for word in ("septic", "tank", "soakaway", "cesspit")):
        return ("Not with a septic tank: the bleach kills the bacteria the tank works with, and a "
                "capful now and then is the most it will take. Hot water and a plunger clear the "
                "blockage, and a bucket of water with a spoonful of bicarbonate of soda and "
                "vinegar freshens the drain without the chlorine.")
    return ("A capful of thin bleach in the drain once a week is fine and kills the smell, but it "
            "will not clear a blockage - hot water and a plunger do that, and mixing bleach with "
            "an acid or ammonia cleaner makes chlorine gas, so never two in the same drain on the "
            "same day. Regular bleach on old metal pipework and rubber seals does shorten their "
            "life, so keep it to a capful rather than a mugful.")


# ---- dust on a surface is not house dust --------------------------------------
#
# "How do I get rid of dust" wants the house-dust method, and that card holds it. The verbs that
# ask for it - get rid, remove, reduce, control - are generic, though, and a card keyed on "dust"
# then answers every question about dust on a named thing with "Most of the dust in a house is
# you: skin flakes and the fibres fabrics shed": a camera lens, a monitor and a car dashboard all
# got it, and "how do i get rid of dust on my keyboard" lost the computer cleaning card it had.
# So the verbs only fire on bare dust: when the dust is followed by on/from/off/in and a thing
# rather than a room, the row stands down and the surface keeps its own answer.
_DUST_NOUN = re.compile(r"\bdust(?:y)?\b", re.I)
_DUST_ON_A_THING = re.compile(
    r"\bdust(?:y)?\b[^.!?]{0,25}?\b(?:on|onto|from|off|in|into|under|inside|behind|around|"
    r"over|across|between|near|above)\s+(?:the|my|your|his|her|our|their|its|a|an)\s+"
    r"([a-z][a-z' -]{0,40})", re.I)
# Dust that arrives is the room's question, however it lands: "how do i stop dust settling on my
# tv" is not a question about cleaning a telly, it is a question about having less dust in the
# room, and the house-dust card is the only answer to it. Read before the thing is read, because
# the thing words in the line (tv, screen, shelf) say where it lands, not what is being cleaned.
_DUST_IS_ARRIVING = re.compile(
    r"\b(?:settl(?:e|es|ed|ing)|comes? back|coming back|keeps? coming|keep coming|"
    r"keeps? (?:appearing|returning|showing up)|so (?:fast|quick|quickly|often)|"
    r"never (?:seems?|goes?) away|back again|over and over|always dusty|always so dusty)\b",
    re.I)
# the places the dust card is actually about: "dust in my house", "dust under the bed" - a room
# or the furniture in it is where house dust lives, not a thing somebody is cleaning
_A_PLACE = re.compile(
    r"\b(?:house|home|flat|place|room|rooms|bedroom|bedrooms|lounge|living room|kitchen|hall|"
    r"hallway|stairs|stair|landing|whole|everywhere|air|attic|loft|cellar|basement|"
    r"floor|floors|floorboards|carpet|carpets|rug|rugs|surface|surfaces|furniture|"
    r"shelf|shelves|shelving|skirting|blind|blinds|curtain|curtains|windowsill|window|windows|"
    r"ceiling|wall|walls|door|doors|bed|beds|sofa|wardrobe|cabinet|cabinets|cupboard|cupboards)")


def _dust_is_on_a_thing(understood):
    """False for dust on a named thing - a lens, a monitor, a dashboard, a keyboard.

    Two readings decide it. Dust that is arriving - settling, coming back, "so fast", "always" -
    is the room's question wherever the line says it lands, so the house-dust card keeps it. Dust
    of which the line names a thing rather than a place is that thing's question, and the row
    stands down. The whole tail after "on my" is read, not its first word, because "dust settling
    on everything in the front room" names a room two words later.
    """
    clean = str((understood or {}).get("clean") or "").lower()
    if not _DUST_NOUN.search(clean):
        return True
    if _DUST_IS_ARRIVING.search(clean):
        return True
    for match in _DUST_ON_A_THING.finditer(clean):
        tail = match.group(1).strip()
        if not _A_PLACE.search(tail):
            return False
    return True



# A knee, an elbow and a heel are garment words and body words at once, and "worn" is how a joint
# is described: with `worn` in the mending row's first key and `knee` in its second, "my knee is
# worn out" got the darning card, and that is the one answer a person with a worn knee must not
# get. The avoid list cannot fix it, because `knee` has to stay in the second key for "my jeans
# have gone at the knee". So the row asks a question of the whole reading instead (the repo's own
# `guard=`, for where the reading rather than a word says the key means something else): a line
# that says a joint is worn and names no garment is about the joint, and a line where the joint
# hurts is about the joint whether or not a garment is named too.
_BODY_JOINT = re.compile(
    r"\b(?:knees?|elbows?|shoulders?|hips?|ankles?|wrists?|joints?|spine|backs?|neck|heels?|"
    r"toes?|thumbs?|fingers?)\b", re.I)
_A_WEAR_WORD = re.compile(
    r"\b(?:worn|wear|wearing|wore|frayed|fraying|fray|threadbare|rubbed|"
    r"gone\s+at|gone\s+through)\b", re.I)
_THE_GARMENT = re.compile(
    r"\b(?:jeans|trousers|shorts|skirt|dress|shirts?|t-?shirts?|tops?|coat|jacket|jumper|"
    r"cardigan|hoodie|sweatshirt|socks?|stockings?|sleeves?|cuffs?|hems?|seams?|lining|"
    r"pockets?|gloves?|mittens?|boots?|shoes?|trainers?|slippers?|pyjamas?|dressing gown)\b",
    re.I)
_A_HURTING_JOINT = re.compile(
    r"\b(?:hurt|hurts|hurting|ache|aches|aching|sore|painful|pain|stiff|swollen|swelling|"
    r"kneel|kneeling)\b", re.I)


def a_worn_thing_is_a_garment(understood):
    """False when the line's worn thing is a joint rather than a garment (`mend-hole`)."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _BODY_JOINT.search(said):
        return True
    if _A_WEAR_WORD.search(said) and not _THE_GARMENT.search(said):
        return False
    if _A_HURTING_JOINT.search(said):
        return False
    return True


_STEAM_LOOK_AFTER = re.compile(
    r"\b(clean|cleaning|descale|descaling|scale|empty|emptying|look after|looking after|"
    r"maintain|maintenance|service|servicing|filter|tank|store|storing|smell|smells|"
    r"not working|broke|broken|no steam)\b", re.I)
_STEAM_RISKY = re.compile(
    r"\b(laminate|engineered|hardwood|hard wood|real wood|wood floor|wood floors|wooden floor|"
    r"timber|carpet|carpets|rug|rugs|sofa|sofas|couch|settee|upholstery|armchair|mattress|"
    r"curtain|curtains|ceiling|ceiling rose|plaster|vinyl|karndean)\b", re.I)
_STEAM_A_SURFACE = re.compile(
    r"\b(grout|tile|tiles|laminate|floor|floors|wood|carpet|carpets|shower|bathroom|oven|hob|"
    r"grill|glass|window|mattress|sofa|upholstery|wall|walls|mould|mold|sofa|curtain)\b", re.I)


def _steam_cleaner(memory, understood):
    """What a steam cleaner is good for, or how to look after one.

    "how do i clean a steam cleaner" reached nothing at all on main, and it is a different
    question from "will a steam cleaner help with the grout": the first is about the machine,
    the second about the surface. The opening sentence is the answer to the question asked, and
    the rest is the same because both need the same two facts - what it does well and what it
    damages.
    """
    reading = understood if isinstance(understood, dict) else {}
    text = str(reading.get("clean") or reading.get("text") or " ".join(reading.get("words") or ()))
    if _STEAM_RISKY.search(text):
        return ("Skip it on that one: the heat lifts laminate and engineered boards, opens the "
                "seams of unsealed or oiled wood, and drives into a carpet's backing or a sofa's "
                "filling instead of out of it, so it comes back damp and can smell. Use it on "
                "tiles, grout, hard floors, the shower and the hob - about four seconds with the "
                "head on one spot lifts the grease with no chemicals, so move slowly rather than "
                "scrubbing. A carpet wants a hire machine once a year, and a wooden floor wants a "
                "barely damp mop. Empty the tank after every go and descale it every few months "
                "with half water, half white vinegar.")
    if _STEAM_LOOK_AFTER.search(text) and not _STEAM_A_SURFACE.search(text):
        return ("Empty the tank after every go and descale it every few months: half water, half "
                "white vinegar in the tank for 20 minutes, then rinse. Rinse the pads or the cloth "
                "and dry them rather than leaving them damp in the cupboard, and wipe the head "
                "and the nozzles with a vinegar-soaked cloth if the steam starts coming out "
                "unevenly. Beyond that the machine looks after itself - the water is the cleaning, "
                "so the tank and the scale are the whole of the maintenance.")
    return ("Hot steam lifts grease and kills most bacteria on tiles, grout, hard floors, the "
            "shower and the hob, with no chemicals - about four seconds with the head on one spot "
            "is what does it, so move slowly rather than scrubbing. Skip laminate, engineered and "
            "unsealed wood and anything with a gap the water can get under, because the heat lifts "
            "the surface; skip carpets and upholstery, where a hire machine once a year is "
            "cheaper; and keep it off cold glass, which can crack. Empty the tank after every go, "
            "and descale it every few months with half water, half white vinegar for 20 minutes.")


def _uniform_care(memory, understood):
    """One uniform, several questions: wash, stain, whiteness, shrinking, ironing, smell.

    A blanket "wash it at 40" would answer the ink question with the wrong opening, so the
    first sentence is the part that was asked, and the wash advice follows it. Polyester and
    cotton are the commonest school uniform fabrics, and 40C is what both of them take.
    """
    text = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    # A name tag is the one uniform question that is not a wash at all: it wants a needle.
    if any(word in text for word in ("name tag", "name tags", "name tape", "nametape",
                                     "label", "labels", "tag", "tags", "coming off", "comes off")):
        return ("Sew it on rather than ironing it on: a few stitches through the loop of the "
                "label and into the inside seam hold through every wash, and an iron-on lifts at "
                "the first 40 cycle. Mark the care label inside the collar with a fabric pen and "
                "the uniform still comes back if the sewn tag does.")
    # A tie is a sponge job, not a wash: it is the one piece that comes off after one wear.
    if any(word in text for word in ("tie", "ties")):
        return ("Sponge it instead of washing it: a drop of washing-up liquid on a damp cloth, "
                "dab the mark, then hang the tie flat to dry on the back of a chair, and a "
                "clip-on tie is the answer to September mornings. Silk and wool ties go to the "
                "dry cleaner, and an iron on the front takes the sheen off it for good.")
    # "30 or 40" is a comparison question: standing it down sent it to the 30C card, and a flat
    # 40 answers the wrong half of it.
    if any(word in text for word in ("30 or 40", "40 or 30", "40 or 60", "60 or 40",
                                     "what temperature", "which temperature", "how hot",
                                     "what temp", "warmer", "hottest", "cooler",
                                     "at 60", "at 90", "60 degree", "90 degree", "hot wash",
                                     "wash hot", "boil wash", "boiling")):
        return ("40 is the setting for uniform: polyester-cotton comes out of a 40 wash clean, "
                "and 60 is what fades the colours and sets the creases in. 30 is fine for a "
                "normal week's wear and about 10p a load cheaper, but take a stain or a bug "
                "going round to 40 or 60 and wash the whole uniform the same way.")
    if any(word in text for word in ("brand new", "first wear", "before wearing", "before wear",
                                     "new uniform", "new school uniform", "just bought")):
        return ("Yes, wash it once before the first wear: new uniform carries dressing and loose "
                "dye that can mark the white collar and irritate skin. A plain 40 cycle, no "
                "fabric softener, dry it in the air, and wash the dark pieces on their own the "
                "first time round.")
    if any(word in text for word in ("shrank", "shrunk", "shrink", "too small", "came out small")):
        return ("Soak it in lukewarm water with a spoonful of hair conditioner for 15 minutes "
                "and stretch it gently back into shape, then dry it flat: cotton-polyester goes "
                "back a little and never fully. Warmth and a wash were what shrank it, so keep "
                "the next one off the tumble dryer.")
    if any(word in text for word in ("white", "whiten", "bleach", "grey", "gray", "yellow")):
        return ("Wash white uniform at 40 with a scoop of oxygen bleach (a colour-safe one, not "
                "thin bleach) and dry it in daylight: oxygen bleach lifts the grey without "
                "eating the fabric, and daylight does what no product does. Wash it inside out "
                "and never let black or navy sit damp against it.")
    # Mud is the one stain where water first is the wrong move, and school trousers are where
    # a person meets it: the row that owns "how do i get mud out of" already says this.
    if any(word in text for word in ("mud", "muddy", "muddy puddle", "clay", "soil")):
        return ("Let it dry completely, then brush it off with a stiff brush before any water "
                "touches it: washing mud while it is wet pushes it into the weave. Then work a "
                "drop of washing-up liquid into what is left, wash it at 40 and air-dry it, and "
                "keep it off the radiator.")
    if any(word in text for word in ("stain", "ink", "paint", "mark", "pen")):
        return ("Blot it, do not rub, then work a little washing-up liquid into the mark with "
                "your fingers and rinse from the back in cold water before the wash. Wash it at "
                "40 with a scoop of oxygen bleach, and do not tumble it dry while it is still "
                "damp, because the dryer sets whatever the wash leaves behind.")
    if any(word in text for word in ("iron", "crease", "creases", "crinkle")):
        return ("Iron it warm, not hot, under a damp tea towel: polyester scorches and goes "
                "shiny at a cotton setting, and the cloth on top is what stops the shine. Wash "
                "it at 40, shake it out and hang it straight, and most of it needs no iron at all.")
    if any(word in text for word in ("smell", "smelly", "stinks", "stink", "odour", "odor", "sweat")):
        return ("Wash it at 40 with a couple of spoonfuls of bicarbonate of soda in the drum and "
                "dry it in the air: school uniform smells are trapped sweat or damp, and soda "
                "lifts the sweat without a strong detergent. Skip the fabric softener, which "
                "holds the smell in, and never leave a damp uniform in a bag or a heap.")
    return ("Wash uniform at 40 on a normal cycle and air-dry it: polyester-cotton comes clean at "
            "40, fades in a hot wash and shrinks in the dryer. Treat ink, mud and food before "
            "washing with cold water and washing-up liquid on the mark, iron it low under a tea "
            "towel, and keep whites white with oxygen bleach rather than thin bleach.")


# "Why do my glasses fog up" wants the reason; "how do I stop it" wants the fix. One entry, two
# openings, and the same advice behind either.
FOG_REASON = ("The lens is colder than the warm, damp air on the other side of it, so the water in "
              "that air condenses on the glass.")
FOG_FIX = ("Rub a tiny drop of washing-up liquid or a smear of shaving foam over the lenses, then "
           "polish it off with a dry cloth: the thin film stops the steam forming droplets, and it "
           "holds for a day. With a mask, pinch the wire down over your nose and pull the top edge "
           "under the glasses so your breath leaves at the sides; for spectacles, warm them in your "
           "hand and push them a little further down your nose.")


def _spectacles_fog(memory, understood):
    asks = understood.get("asks") if isinstance(understood, dict) else None
    if isinstance(asks, (list, tuple, set)) and "why" in asks:
        return FOG_REASON + " " + FOG_FIX
    return FOG_FIX + " That is because " + FOG_REASON[0].lower() + FOG_REASON[1:]


# "moths in my kitchen" and "how do i get rid of pantry moths" are the same job as a plain clear-out,
# but the answer is a different paragraph: the larvae come in the packet, so binning the opened
# flour matters more than wiping the shelves. One entry, two openings, chosen by the pest word.
CUPBOARD_CLEAN = (
    "Empty one cupboard at a time, wipe the shelves with hot soapy water and dry them before "
    "the tins go back, and leave a bay leaf or a few cloves in the corners to keep the musty "
    "smell down. The outsides want a wipe every couple of weeks, near the hob more often, and "
    "a twice-a-year clear-out is what stops food going out of date at the back.")
CUPBOARD_MOTHS = (
    "Bin anything already opened - flour, rice, oats, cereal, raisins, dried fruit - because "
    "the larvae come in the packet, and put the rest into airtight jars. Wipe the shelves with "
    "hot soapy water right into the corners and along the door seal, leave a bay leaf or a few "
    "cloves out, and do a second round a fortnight later to catch what hatched.")
CUPBOARD_PESTS = ("moth", "moths", "weevil", "weevils", "beetle", "beetles", "maggot",
                  "maggots", "pantry moth", "food moth")
# A cupboard that is full, cluttered or a mess is the same row and a different job: the question
# is where the things go, not how to wipe a shelf. "take everything out, put back only what you
# have used" answers it, and the wipe paragraph answers the clean one.
CUPBOARD_FULL = (
    "Do one cupboard, not the lot: take everything out, put back only what you have used since "
    "this time last year, and let the rest go - spare jars, three nearly empty bags of pasta, "
    "the mug nobody likes. Then give the space back: what you use every day at eye level, the "
    "heavy jars low, and a box or a riser for the small loose things so they are not rattling "
    "around the shelf. If it has not got a home it does not go back in.")
CUPBOARD_STATE = ("full", "full up", "packed", "overflowing", "stuffed", "junk", "mess",
                  "messy", "clutter", "cluttered", "too much stuff")


def _cupboards(memory, understood):
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in text for word in CUPBOARD_PESTS):
        return CUPBOARD_MOTHS
    if any(word in text for word in CUPBOARD_STATE):
        return CUPBOARD_FULL
    return CUPBOARD_CLEAN


def _bedding_life(memory, understood):
    """How long a pillow, duvet or mattress lasts, worded for the one the line names."""
    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("text") or reading.get("clean") or "").lower()
    if "pillow" in line:
        return ("Two years is a normal life for a pillow and three or four for a good one, and you "
                "know it is finished when it no longer springs back: fold it in half, let go, and "
                "if it stays folded it has lost its loft. A flat pillow is one of the commonest "
                "causes of a stiff neck in the morning, so replace it rather than sleeping on it. "
                "Wash it to the label now and then, use a washable protector, and if you sleep on "
                "your side you want a fuller one than your partner does.")
    return ("About five years is a normal life for a down duvet and two or three for hollowfibre. A "
            "lumpy one is filling that has clumped, usually after a wash, so tumble it on low with "
            "two or three dryer balls and shake it out holding two corners, and down comes back; if "
            "it stays flat and cold, or the filling is in hard clumps, it will not. Air it over the "
            "banister each time you change the bed.")


# New bedding and towels get their own answer from the how-often cards: the question is the first
# wash, not the rota. "do i need to wash new sheets before using them" and "should i wash new
# towels before using them" were both told how often to change them, which answers nothing.
BEDSHEETS_OFTEN = (
    "Change the sheets once a week, and more often in hot weather, if you sweat at night or if a "
    "pet sleeps on the bed; pillowcases twice a week on the same count. Wash at 60C to kill dust "
    "mites, or 40C with a good detergent if the colours matter more, and dry them properly before "
    "they go back on. Two sets so one is on while the other washes makes it easy to keep up.")

BATH_TOWELS = (
    "Bath towels after three or four uses, hanging them spread out to dry in between. Wash at 60C "
    "without fabric softener, which coats the fibres and stops them soaking up water.")

FIRST_WASH = ("Wash new bedding and towels before they go on the bed or the rail: new cotton "
              "carries a factory dressing that makes it feel stiff and a loose dye that can mark "
              "anything pale washed with it. One 40C wash with a full dose of detergent, no fabric "
              "softener, then dry as usual is enough - cotton bedding takes 60C after that.")


def _first_wash(reading):
    """"Should i wash new sheets before using them" is the first wash, not the change rota."""
    reading = reading if isinstance(reading, dict) else {}
    line = str(reading.get("text") or reading.get("clean") or reading.get("plain") or "").lower()
    if "new" not in line and "brand new" not in line:
        return ""
    if "before" in line or "first use" in line or "first wash" in line:
        return FIRST_WASH
    return ""


def _bedsheets(memory, understood):
    said = _first_wash(understood)
    if said:
        return said
    return BEDSHEETS_OFTEN


def _bath_towels(memory, understood):
    said = _first_wash(understood)
    if said:
        return said
    return BATH_TOWELS


# The garments a smell can be in: `bot/knowledge/odours.py`'s GARMENT, kept in step by
# tests/test_a_potato_is_not_a_garment.py, and not imported because the import order matters.
# Water that lands on the glass by itself is not a window to wash. `windows-streak` holds a list
# of "condensation on/in ..." phrases out, and a phrase list cannot keep up with how people say
# it: `my windows have condensation inside` and `my windows are full of condensation` are the
# same complaint as `condensation on my windows`, and the first of them still got the
# wash-and-squeegee reply. So the whole reading is the test - a wet-glass word with no word of
# wiping it - and the phrases stay as the cheap first fence.
_WET_GLASS = ("condensation", "condensating", "condensing", "steams up", "steaming up",
              "steamed up", "mists up", "misted up", "misting up", "fogged up", "fogging up",
              "fog up", "fogs up", "damp", "mouldy", "mould")

# The words that turn a wet window back into a job for the cloth: "how do i clean condensation
# off the inside of the windows" does ask how to wipe glass, and it keeps this row.
_WIPE_THE_GLASS = ("clean", "cleaning", "cleaned", "wipe", "wiping", "wipe off", "remove",
                   "removing", "get rid of", "clear", "clearing", "squeegee", "wash",
                   "washing", "dry", "drying", "towel", "cloth", "bicarbonate", "vinegar")


# "Glass" is the same word to the reader whether it is a pane or a pair of spectacles: the loose
# forms of "glass" and "glasses" are one set, so a fence holding "glasses" out of this row held
# every window that is called by its glass out too - "my window glass is streaky" was a punt while
# "my windows are streaky" had its card. The fence cannot tell them apart by the word, so the
# guard does it: a line that names spectacles or a drinking glass, and names no window, is not a
# window to wash.
#
# Naming the drinking glasses one by one does not work: a list of nouns only holds the nouns
# someone wrote down, and the singular of a name that went in as a plural ("wine glasses" but not
# "wine glass") came through the bare glass and was washed with a squeegee. What the row can rely
# on is the *kind* of thing: a glass you drink from is named by the drink in it, or by the vessel
# it is. So the guard asks that instead of reading a list of glasses.
_GLASSWARE = ("glasses", "sunglasses", "spectacles", "specs", "lens", "lenses", "varifocals",
              "bifocals", "contact lens", "contacts", "glassware", "cutlery", "goggles",
              "dishwasher")
# the drink, which is what a drinking glass usually gets called by: "my beer glass", "a wine
# glass", "the gin glass" - and no window is ever named by what is in it
_A_DRINK = ("beer", "lager", "ale", "cider", "stout", "wine", "prosecco", "champagne", "gin",
            "vodka", "whisky", "whiskey", "rum", "brandy", "cocktail", "juice", "lemonade",
            "squash", "cordial", "soda", "cola", "fizz", "smoothie", "milkshake", "milk",
            "coffee", "tea", "espresso", "cappuccino", "latte", "cup of", "glass of", "glasses of",
            "pint of", "bottle of", "top of")
# and the vessel, for the times the drink is not named at all
_A_VESSEL = ("cup", "cups", "mug", "mugs", "tumbler", "tumblers", "pint", "pints", "flute",
             "flutes", "goblet", "goblets", "tankard", "tankards", "jug", "jugs", "pitcher",
             "carafe", "decanter", "jar", "jars", "vase", "vases", "bottle", "bottles",
             "decorative bottle", "plant pot", "bowl", "bowls")
_A_WINDOW_NAMED = ("window", "windows", "windowpane", "window pane", "pane", "panes", "mirror",
                   "mirrors", "patio door", "patio doors", "windscreen", "windshield",
                   "glass door", "glass doors", "conservatory", "skylight", "glazing",
                   "window glass", "french door", "french doors", "shower screen")


def _glass_in_the_line_is_a_window(understood):
    """False when the glass the line names is a pair of spectacles or a drinking glass."""
    said = " %s " % str(understood.get("text") or "").lower()
    if any(" %s " % word in said or word in said for word in _A_WINDOW_NAMED):
        return True
    for words in (_GLASSWARE, _A_DRINK, _A_VESSEL):
        if any(" %s " % word in said or word in said for word in words):
            return False
    return True


def _a_dirty_window_not_a_wet_one(understood):
    """False when the line is about water on the glass rather than dirt on it."""
    said = " %s " % str(understood.get("text") or "").lower()
    if not any(" %s " % word in said or word in said for word in _WET_GLASS):
        return True
    return any(word in said for word in _WIPE_THE_GLASS)


GARMENT_WORDS = ("coat", "coats", "jacket", "jackets", "jumper", "jumpers", "cardigan", "fleece",
                 "hoodie", "blazer", "suit", "suits", "dress", "dresses", "shirt", "shirts",
                 "trousers", "skirt", "scarf", "clothes", "clothing", "wardrobe", "outfit",
                 "uniform", "costume", "gloves", "hat", "beanie", "bag", "backpack", "rucksack",
                 "handbag", "luggage", "suitcase", "sleeping bag", "tent")

# "Behind the tv" is a place and "the back of the tv" is a surface: the screen and the panel have
# their own cleaning card, and a cloth is the answer there, so the place card stands down for it.
# It is the same for a monitor, a laptop and a phone, and for nothing else - the back of a fridge
# or a washing machine is where the dust and the coil are, which is this card's line.
_A_SCREEN = ("tv", "television", "telly", "monitor", "screen", "laptop", "computer",
             "keyboard", "console", "phone", "tablet", "ipad")
_BACK_OF = ("back of", "back of the")


def _the_back_of_a_screen(understood):
    """False when the line names the back of a screen, which its own card answers."""
    said = understood if isinstance(understood, dict) else {}
    words = [str(word).lower() for word in (said.get("words") or ())]
    if not words:
        return True
    text = " " + " ".join(words) + " "
    if not (" back of " in text or " back of the " in text):
        return True
    return not any((" %s " % word) in text for word in _A_SCREEN)

# The patch answer, used by the row that names the mess and by the follow-up that only names the
# place: "i have a cat and she keeps weeing on the sofa" ... "so what do i do about the sofa".
PET_ACCIDENT_REPLY = (
    "Soak up what you can, then wash the patch with a warm solution of biological laundry "
    "detergent, blot and rinse well; the enzymes in it break down the smell. Never use bleach "
    "or ammonia cleaners, which smell like urine to a cat and invite a repeat.")


# The place a pet used, named a turn after the accident. The accident itself is two turns back by
# then and the line only says where it happened, so the mess row above cannot see it: the person
# got the litter-tray and the vet-check answers, then "so what do i do about the sofa" and was
# told "I don't know enough to answer that honestly". The chat decides, and the rule is the one
# the pet rows keep: somebody else's accident is not this card.
_PET_NAMED = re.compile(r"\b(cat|cats|kitten|kittens|dog|dogs|puppy|puppies|rabbit|rabbits|"
                        r"hamster|hamsters|guinea pig|pets?|pet's)\b", re.I)
_AN_ACCIDENT = re.compile(r"\b(pee|peed|peeing|pees|wee|weed|wees|weeing|urine|urinated|"
                          r"sprayed|spraying|poo|pooed|pooing|mess|messes|accident|accidents|"
                          r"vomit|vomited|sick|stain|stains|stained|soaked)\b", re.I)
_A_PLACE_TO_WASH = re.compile(r"\b(sofa|sofas|settee|couch|armchair|armchairs|carpet|carpets|"
                              r"rug|rugs|mattress|upholstery|chair|chairs|stool|bed|bedding|"
                              r"duvet|blanket|blankets|curtain|curtains|floor|floors|stairs|"
                              r"seat|seats|spot|spots|patch|patches|room|rooms|hallway|"
                              r"landing|passage|corridor)\b", re.I)


def _the_place_a_pet_used(memory, understood):
    """The patch answer for a line that names only where the mess was."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _A_PLACE_TO_WASH.search(text):
        return None
    for turn in reversed(((memory or {}).get("turns") or [])[-3:]):
        line = (turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        if _PET_NAMED.search(line) and _AN_ACCIDENT.search(line):
            return PET_ACCIDENT_REPLY
    return None


# A loaf word, then a verb of going off, then the mould word: the loaf went off in the bin, and
# `bread-mouldy` in cooking_entries answers it. Kept here rather than in the key because "bread
# bin" is a bin and it is the bin that is mouldy in "my bread bin is mouldy".
_THE_LOAF_WENT_OFF = re.compile(
    r"\b(?:bread|loaf|loaves)\b[^.]{0,30}?"
    r"\b(?:go|goes|going|went|gone|get|gets|getting|got|turn|turns|turned|turning|come|comes|"
    r"coming|came|becoming|becomes|stays|staying|stop|stops|stopping|keep|keeps|keeping)\b"
    r"(?:\s+\w+){0,3}?\s+(?:mouldy|mould|mold|green|mildewy|mildew|furry)")


def _the_loaf_went_off(understood):
    """True when the line says the bread went off, rather than the bin it was kept in."""
    return bool(_THE_LOAF_WENT_OFF.search(the_line(understood)))


# "bin" is two words: the thing in the kitchen, and the verb for throwing something away. "Can I
# cut the mould off cheese or should I bin it" is a question about the cheese, and the answer to it
# was the wheelie bin's wash. A "bin" that does the throwing has the thing thrown after it, or is
# asked of the person ("should I bin it", "can I bin this cheese"), so the line says which "bin"
# it is by how it is used. It is not an `avoid` phrase: the phrases are matched with the
# punctuation stripped, so "bin it" also matches "bin, it", and the bin's own line - "how do I
# clean my bin, it stinks" - lost its card to a shrug.
_BIN_IS_A_VERB = re.compile(
    r"\b(?:to|should|shall|can|could|do|must|will|would|might|need to|have to|going to|i'll|i'd|"
    r"or|and|then|just)\s+(?:i\s+)?bin\b"
    r"|\bbinned\b|\bbinning\b"
    r"|\bbin\s+(?:it|that|them|those|this|the rest|the lot|all of it|everything)\b", re.I)


def _the_food_was_binned(understood):
    """True when the "bin" in the line is a food being thrown away, not the bin in the kitchen.

    A mouldy wedge, a loaf, a ham: the thing in the person's hand decides the answer, and the
    bin's washing card is not it. The bin's own line stays here - "my bin smells, should I bin it
    and get a new one" asks the same throwing word and names no food, and washing it out is the
    answer to that one.
    """
    said = the_line(understood)
    if not _BIN_IS_A_VERB.search(said):
        return False
    words = set(re.findall(r"[a-z']+", said.lower()))
    return any(word in FOOD_NAMED for word in words)


def _a_colour_can_have_run(understood):
    """Whether the line is about a colour that came out in the wash rather than a thing that died.

    "My washing machine has gone" holds the colour-run key twice - "gone" and "washing" - and it
    was answered "rewash the ruined whites" while the machine sat there dead; a thing that has
    gone is the repair row's question. Where the line says which colour it went, that colour is
    what this row is for ("my whites went pink", "the shirt came out grey").
    """
    return not the_thing_has_gone(understood)


# A dryer's own card is not the washing machine's: a tumble dryer's lint filter is a fire risk
# and its card says to pull the fluff off after every load. "my tumble dryer lint filter is full of
# hair" reached this row on "lint filter", and "my dryer drum is full of hair" on "drum", so the
# row stands down when the only machine named is the dryer. A line that names both machines still
# has a washing machine in it, and the hair is the same job in either.
_A_DRYER = re.compile(r"\b(?:tumble dryer|tumble drier|tumbler|dryer|drier)\b", re.I)
_A_WASHING_MACHINE = re.compile(r"\b(?:washing machine|washing mashine|washer)\b", re.I)


def _not_the_dryer_alone(understood):
    """True unless the line names a dryer and no washing machine with it."""
    said = the_line(understood)
    return not (_A_DRYER.search(said) and not _A_WASHING_MACHINE.search(said))


# A line that asks how long a job takes, or how often it wants doing, is a schedule question and
# the card that answers with a time owns it. The two cleaning plans below say what to do and in
# what order, which is not that question, so they stand down for these words.
_HOW_LONG = ("how long", "how many hours", "how much time", "how often", "how frequently",
             "how regularly", "once a week", "every week", "every day", "how many times",
             # a speed word is the same kind of ask: "how do i tidy my bedroom quickly" has a
             # ten-minutes-a-day card that says how to keep on top of it, and a plan that says
             # what to pick up first is not that answer
             "quickly", "fast", "quick", "in a hurry", "in ten minutes", "ten minutes")

# One kitchen, one order to work in. Two rows say it: the room itself, and the job a person is left
# with after they cook ("how do i clean up after baking" was the first-step-into-baking card,
# because "baking" is an activity and nothing in this module asked the question). One text, so the
# two answers cannot drift apart.
_KITCHEN_ORDER = (
    "Clear the surfaces, then work clockwise so you do not double back: hot soapy water on the "
    "surfaces and the sink, the hob while it is still warm, and the floor last so the crumbs "
    "you drop land on it. Daily is a wipe round, weekly is the hob and the sink, monthly is "
    "the oven and the inside of the fridge. Where grease has built up, hot water with a good "
    "squeeze of washing-up liquid lifts it and cold water only smears it, and a paste of "
    "bicarbonate on a cloth takes the film off tiles, the splashback and the top of the "
    "cupboards. Most of the work is not letting things dry on, "
    "because a wipe while the pan is still warm beats an hour of scrubbing.")

# "mop first or hoover first" was answered "Work it out rather than guess: whatever makes a mess for
# the other step to clear up goes first", and "should i hoover before mopping" with "Not mine to
# decide": two cleaning steps named with an order word is a question with an answer, and it is the
# same one every time - dry before wet, and top before bottom. The room row cannot take it, because
# its first key group is room words and these lines name no room.
#
# The two steps are the whole shape of the question, so the row is fenced twice: the line has to
# name two different steps, and it has to name no object with a row of its own. Without the first
# fence "how do i mop a floor" and "how do i polish a wooden table" were both this answer, and
# without the second, "do i wipe the skirting boards before hoovering" lost its own card.
_STEP_WORDS = {"hoover": "dry", "hoovering": "dry", "vacuum": "dry", "vacuuming": "dry",
               "sweep": "dry", "sweeping": "dry", "swept": "dry", "dust": "dry",
               "dusting": "dry", "dusted": "dry", "brush": "dry", "brushing": "dry",
               "mop": "wet", "mopping": "wet", "mopped": "wet", "scrub": "wet",
               "scrubbing": "wet", "wipe": "wet", "wiping": "wet",
               # "sweep it out first or clear the shelves" was answered "Work it out rather than
               # guess ... Which job is it?": a floor cannot be swept while it is still full,
               # so clearing out is the step that comes before the rest and it counts as one.
               "clear": "clear", "clearing": "clear", "cleared": "clear", "empty": "clear",
               "emptying": "clear", "emptied": "clear", "tidy": "clear", "tidy up": "clear",
               "tidying": "clear"}
_STEP_OBJECTOWN = ("skirting", "table", "tables", "window", "windows", "worktop", "worktops",
                   "hob", "tile", "tiles", "bath", "sink", "mirror", "mirrors", "curtain",
                   "curtains", "blind", "blinds", "picture", "pictures", "sofa", "carpet",
                   "carpets", "rug", "rugs", "mattress", "oven", "fridge", "freezer", "toilet",
                   "loo", "living room", "lounge", "bedroom", "bedrooms", "kitchen", "bathroom",
                   "hall", "hallway", "stairs", "garage", "car")


def _two_steps_in_order(understood):
    """Only a line that names two cleaning steps and asks which comes first."""
    # `text`, not `clean`: the understanding engine rebuilds `clean` from the line, so a guard
    # that reads it can be met by words the person did not say this turn. The line itself is
    # what a fence has to stand on.
    text = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    if any(word in text for word in _STEP_OBJECTOWN):
        return False
    return sum(1 for word in _STEP_WORDS if word in text) >= 2


ENTRIES = [
    entry("dry-before-wet",
          (("hoover", "hoovering", "vacuum", "vacuuming", "sweep", "sweeping", "swept", "dust",
            "dusting", "dusted", "mop", "mopping", "mopped", "scrub", "scrubbing", "brush",
            "brushing", "wipe", "wiping"),
           ("first", "before", "after", "order", "comes first", "goes first", "or")),
          "Dry before wet, and top before bottom: hoover or sweep first, dust from the ceiling down "
          "so the floor catches what falls, and mop last - a mop over grit just pushes the mud "
          "about. On a wooden floor the dry mop goes over first and the wet one is barely damp. "
          "And clear the floor, the worktops and the shelves first: a broom cannot reach a floor "
          "that is still full, and a cloth cannot wipe a ledge with things still on it.",
          guard=_two_steps_in_order,
          bias=1),
    entry("gum-off-a-hard-surface",
          # "how do i get chewing gum off the pavement" reached the dentist, because the only
          # answers keyed on chewing gum were the mouth, the hair and the clothes, and a hard
          # surface out of doors was nobody's. The thing and the surface are the key, so the
          # shoe, the hair and the mouth keep their own answers.
          (("chewing gum", "gum", "chewed gum", "gum stains"),
           ("pavement", "pavements", "path", "pathway", "driveway", "floor", "floors", "floorboard",
            "road", "kerb", "curb", "concrete", "paving", "patio", "decking", "deck", "tiles",
            "tile", "wall", "walls", "step", "steps", "bench", "table", "worktop", "bin", "wheelie",
            "gate", "railing", "railings", "post", "street", "outside", "garage",
            # a car body and a pushchair wheel are hard surfaces too, and both were the
            # dentist's line before; a seat cover is the fabric answer's, so it is avoided
            "car", "cars", "windscreen", "bodywork", "wheel", "wheels", "pushchair", "pram",
            "buggy", "pavement slab", "gutter", "drain")),
          "Harden it rather than heat it: sit an ice cube or a bag of frozen peas on the gum for a "
          "couple of minutes, then shave it off with an old card or a flat scraper held almost "
          "flat, so it lifts rather than smears. On concrete or paving a stiff brush and hot "
          "soapy water take the last film; on wood or tile wipe the residue with a drop of oil or "
          "a citrus cleaner and rinse, because a blade marks the surface. Don't burn it off - the "
          "ash stains, and it is how people melt the thing they were cleaning.",
          # the mouth, the hair, the clothes and the shoe have their own answers, and a dog that
          # ate gum is the vet's line
          # "gums" and "gummed" cannot go here: an avoid word that shares the stem of a key
          # word is read as that word, and either one stood the whole entry down. They are not
          # needed - a gum question names no surface, so the key alone keeps it out.
          avoid=("mouth", "teeth", "tooth", "dentist", "dental", "bleeding", "swallow",
                 "swallowed", "chew on", "chewing on", "sugar free", "sugar-free", "xylitol", "nicotine",
                 "hair", "hairs", "scalp", "beard", "fringe", "eyebrow", "clothes", "shirt",
                 "trousers", "jeans", "fabric", "jumper", "coat", "shoe", "shoes", "boot", "boots",
                 "trainer", "trainers", "sole", "soles", "carpet", "rug", "sofa", "settee", "couch",
                 "seat", "seats", "car seat", "pushchair seat", "cushion", "cushions",
                 "dog", "cat", "puppy", "kitten", "printer", "glue", "adhesive", "tree",
                 "arabic", "resin", "envelope", "stamp")),
    entry("sick-stains", (("sick", "vomit", "vomited", "vomiting", "threw up", "throwing up",
                           "spit up", "spat up"),
                          ("stain", "stains", "stained", "carpet", "sofa", "settee", "vest",
                           "muslin", "sheet", "sheets", "duvet", "bedding", "mattress", "buggy",
                           "pushchair", "car seat", "clothes")),
          "Scrape up what you can, then rinse in cold water before anything warm touches it - heat "
          "sets both the colour and the smell. Wash with a biological detergent at 40C, or soak in "
          "cool water with a scoop of biological powder for an hour, and let it dry in the open air "
          "rather than on a radiator. For a carpet or a mattress, blot, then use the same cool "
          "detergent and water and dry it with a towel and airflow.",
          avoid=("baby is", "temperature", "fever", "poorly", "unwell", "ill", "sick of",
                 "cant keep", "not keeping", "vet", "pregnant", "morning sickness")),

    # --- how often to wash things -------------------------------------------
    # "duvet cover" and "pillowcases" but never a bare "duvet" or "pillows": how to wash one is
    # duvet-wash's question, and this one is how often the bedding is changed.
    entry("bedsheets-often", (("bedsheets", "bed sheets", "sheets", "bedding", "duvet cover",
                               "pillowcase", "pillowcases"),
                              ("wash", "washing", "often", "change", "change it", "clean", "long")),
          _bedsheets,
          # "how long does it take to pack a 1 bed flat": "bedding" reads as "bed", so a
          # moving or packing line would otherwise get the sheet-washing advice.
          # A line asking the dial is the temperature card's: "what temperature should i wash a
          # duvet cover" was told to change the sheets once a week, which is a different question.
          avoid=("flat", "pack", "packing", "packed", "move", "moving", "moved", "move out",
                 "temperature", "temp", "how hot", "degrees", "30c", "40c", "60c", "90c",
                 "box", "boxes", "storage", "sofa", "1 bed", "one bed", "two bed", "2 bed",
                 "house", "stairs", "buy", "buying", "size", "fit")),
    entry("towels-often", (("towels", "towel", "bath towel", "bathroom towel"),
                            ("wash", "washing", "often", "change")),
          _bath_towels,
          # a towel that already smells is clothing.py's musty-laundry
          avoid=("musty", "sour", "smell", "smells", "smelly", "smelling", "stink", "stinks",
                 "damp", "whiff",
                 # the dial is clothing.py's wash-temperature
                 "temperature", "temp", "how hot", "degrees")),
    # A dressing gown was a hedge ("how often should i wash my dressing gown", "how do i wash a
    # dressing gown", "how often do you wash a bathrobe" all got the honest fallback), though it
    # is worn next to the neck and hands every day and hangs in a steamy bathroom.
    entry("gown-often", (("dressing gown", "dressing gowns", "bathrobe", "bath robe", "housecoat"),
                          ("wash", "washing", "washed", "often", "change", "clean", "how", "when",
                           "smell", "smells", "smelly")),
          "Every week or so if you wear it daily: it touches your neck and hands, and it hangs in "
          "the damp air of a bathroom, which is what turns it sour. Most go at 40C on a normal "
          "cycle - towelling and thick cotton will take 60C - and skip fabric softener on towelling "
          "because it coats the fibres. Dry it right through before it goes back on the hook, and "
          "hang it out of the bathroom between wears.",
          # wool and silk are the fabric entries' question, a moth is clothing.py's, and a line
          # that names pyjamas too is about what to put in with them (pyjamas-often)
          avoid=("wool", "woollen", "woolen", "cashmere", "silk", "moth", "moths", "holes",
                 "drawer", "drawers", "pyjamas", "pajamas", "pj", "nightie", "nightwear")),
    entry("pyjamas-often", (("pyjamas", "pajamas", "pj", "nightie", "nightwear"),
                             ("wash", "washing", "often", "change")),
          "Pyjamas after two or three nights: they sit against your skin all night, so they pick up "
          "sweat and skin cells faster than a shirt does."),
    # A throw over the back of the sofa and the covers on the cushions are the same question, and
    # both were honest shrugs: "how often should i wash my throw", "how do i wash a throw", "how
    # often should i wash a blanket" and "how do i clean cushion covers" reached nothing.
    entry("throw-often", (("throw", "throws", "blanket", "blankets", "cushion cover",
                           "cushion covers", "cushion", "cushions", "slipcover", "slipcovers"),
                          ("wash", "washing", "clean", "cleaning", "often", "change", "machine",
                           "dry clean", "how", "when", "smell", "smells")),
          "Most throws, blankets and cushion covers go in the machine on a normal 30C or 40C cycle "
          "with the rest of the load, and a cover with a zip comes off the pad first. A throw you "
          "sit under every day wants a wash every few weeks, cushion covers about once a month, and "
          "anything a pet sleeps on far more often than that.",
          # wool and silk are the fabric rows' question, an electric or weighted blanket is not a
          # thing to put through a wash and dry, and the sofa itself is the upholstery row's
          avoid=("wool", "woollen", "woolen", "cashmere", "silk", "electric", "heated",
                 "weighted", "sofa", "settee", "couch", "armchair", "carpet", "rug",
                 "mattress", "dryer", "shrink", "shrunk")),
    entry("dishcloth-often", (("cloth", "cloths", "sponge", "dishcloth", "tea towel", "washing up"),
                               ("smell", "smelly", "change", "clean", "often", "bacteria")),
          "A damp dishcloth gets sour within a day or two: rinse it, wring it out and let it dry, "
          "and put a fresh one out every day. Run them through the machine at 60C with the towels, "
          "or microwave a wet one for a minute.",
          # "washing up" is what people call the liquid as well as the dishes: a pair of glasses or
          # a window cleaned with it is not a question about the cloth going sour
          avoid=("clothes", "damp", "laundry", "bedsheets", "shirt", "mattress",
                 "glasses", "spectacles", "lenses", "lens", "window", "windows", "oven", "hob",
                 "dishes", "mirror", "car")),

    # --- washing, shrinking and colour -------------------------------------
    entry("shrunk-clothes", (("jeans", "trousers", "shirt", "dress", "top", "cardigan", "clothes"),
                              ("shrank", "shrunk", "too small", "came out small",
                               # "my clothes came out smaller" and "my trousers came out shorter"
                               # were the composer's echo: the row keys the smallest form of the
                               # word only, and people write the comparison.
                               "came out smaller", "come out smaller", "came out shorter",
                               "come out shorter", "has shrunk", "have shrunk", "shrank a bit",
                               "stretch out", "stretch them", "stretch it", "loosen",
                               "too tight", "bit tight")),
          "Often yes: soak it in lukewarm water with a spoonful of hair conditioner for 15 minutes, "
          "then stretch it gently back into shape and dry it flat. Cotton goes back a little, wool "
          "and anything with stretch in it goes back most; never put it in the dryer again.",
          # clothing.py owns the deliberate shrink ("how do I shrink my jeans") and the wool
          # jumpers: this entry is only for something that came out too small by accident.
          avoid=("how do i shrink", "how to shrink", "make it smaller", "make them smaller",
                 "want it smaller", "wool", "jumper", "knitwear", "cashmere", "merino",
                 "deliberately", "on purpose",
                 # a snug pair of jeans is clothing.py's stretch-jeans: denim does not go back
                 # with a conditioner soak the way a jumper does, and this row was answering
                 # "my jeans are too tight" with the jumper method.
                 "jeans are too tight", "jeans too tight", "jeans are tight",
                 "jeans are a bit tight", "jeans are snug", "jeans too snug",
                 # A garment that is too small and asked about being altered is clothing.py's
                 # "a garment that no longer fits": the conditioner soak is the fix for a thing
                 # that came out of a wash smaller, and it stole "my trousers are too tight
                 # round the waist can they be let out" and "my dress is too tight can it be
                 # altered". The words a person alters with are the fence.
                 "let out", "let it out", "letting out", "taken in", "take it in", "take in",
                 "taken out", "altered", "alter it", "alteration", "alterations",
                 "tailor", "tailors")),
    entry("wool-wash", (("wool", "woollen", "jumper", "knitwear", "cashmere", "merino", "cardigan"),
                         ("wash", "washing", "machine", "hand", "dry")),
          "By hand in cool water with a wool wash or a little shampoo, squeeze rather than rub, "
          "rinse in water of the same temperature, and dry it flat on a towel away from heat. A "
          "wool cycle at 30C with a mesh bag is fine if the label allows it; the dryer never is.",
          # a jumper that came out too small belongs to clothing.py's shrink-wool
          avoid=("shrank", "shrunk", "shrink", "smaller", "too small",
                 # and the heat of the wash is clothing.py's wash-wool-temp, which is the card
                 # that says why 40 felts wool: "what temperature do i wash wool at" and "can
                 # i wash wool at 30" want the degrees, not the hand-wash method.
                 "temperature", "temp", "degrees", "30", "40", "60", "90", "hot", "hotter",
                 "warm", "warmish", "cool", "cooler", "cold",
                 # and drying is clothing.py's drying card, which reads the fabric off the line
                 # and says "dry wool flat, never on a hanger": "how do i dry a wool jumper" is
                 # a drying question, so this row stands down for it and only answers the wash.
                 "dry", "drying", "dried", "tumble", "tumble dryer", "airer", "hanger",
                 # and a coat is clothing.py's wool-coat, which says do not wash it at all:
                 # "can i wash a wool coat" is answered "dry-cleaned once a season, not washed",
                 # and the fabric named here was taking it away from that card.
                 "coat", "coats"),
          # "how do i wash a wool jumper" and "can i put a wool jumper in the washing machine"
          # were the general laundry line ("sort lights from darks, close the zips"), because
          # that row carries "wash", "machine" and "put" too and it is the bigger key, so a wool
          # line tied with it and the tie went to the mixed wash. The fabric named is this row's
          # subject, so it keeps the point.
          bias=3),
    # A woolly hat, a pair of gloves and a scarf are washed like a jumper but they are not one,
    # and "how do i wash a woolly hat" was a shrug on main: the card named the jumper rather than
    # the wool, and nothing said how to dry something with a shape.
    entry("hat-wash", (("hat", "hats", "woolly hat", "woollen hat", "wool hat", "knitted hat",
                        "bobble hat", "beanie", "gloves", "mittens", "scarf", "scarves"),
                       ("wash", "washing", "machine", "hand", "dry", "clean", "wet")),
          "By hand in cool water with a wool wash or a little shampoo, squeeze rather than rub, "
          "rinse in water of the same temperature and roll it in a towel to take the water out. "
          "Dry a hat over an upturned bowl so it keeps its shape, lay gloves flat with the fingers "
          "straightened out, and keep all three off a radiator, which is what shrinks them.",
          # a cap is not a woolly hat, a straw hat is not washed at all, and a hat that came out
          # too small is the deliberate shrink question
          avoid=("cap", "caps", "baseball", "straw hat", "sun hat", "panama", "bucket hat",
                 "hard hat", "helmet", "hanging basket", "shrank", "shrunk", "shrink",
                 "smaller", "too small")),
    entry("colour-run", (("bled", "bleed", "dyed", "ran", "ruined", "turned", "went", "gone",
                          "came out", "come out", "come up", "went in",
                          # "put a red sock in with the whites" is the same accident as "my
                          # whites came out pink", and on main it was a shrug: the line says
                          # what was done, not what came out, so the act is in the key.
                          # "washed" and "wash with" are NOT here: "wash" is a key word of
                          # its own here and in sorting-wash, and its loose forms would make
                          # every "how do i wash whites" line a colour run.
                          "put in with", "put a red", "in with", "mixed in with"),
                          # "everything" is not a colour: it was here for "everything came out
                          # pink", which the colour word already answers, and it made a person
                          # who went black on their feet ask about their whites
                          ("pink", "pinkish", "red", "blue", "whites", "colours",
                           "colors", "coloured", "colored", "washing", "wash")),
          "Act fast: wash the ruined whites again straight away in cold water, and rewash with "
          "oxygen bleach if a wash cycle has already set the colour. Colour catcher sheets in the "
          "next few washes pull out what's left, and sort darks from lights from then on.",
          # a sauce that "went" lumpy or a dinner that "turned" is not a colour run,
          # and neither is a white sauce
          # water coming *out* of a machine is the appliance question, and "ran" reads as water
          # running out of a washer; home.py's leak entry answers that line
          # A thing that changed colour is not a wash: a phone, a screen, a pan, a garlic clove or a
          # pet that went blue is an electrical, kitchen or vet question, and the colour-run answer
          # ("rewash the ruined whites") arrived for all of them once safety stopped calling 999.
          # The colour card stands down for these lines in safety.py; nothing here should catch
          # them on the way past.
          #
          # Meat is the one that costs a person something. "My chicken came out pink in the middle"
          # and "my pork came out pink is it safe" are the undercooked-meat rule, and "came out"
          # plus a colour is exactly this row's key, so a food-safety question was answered with
          # "rewash the ruined whites". A colour on meat, fish or an egg is the kitchen's subject
          # however the line words it, so the meat, the cuts and the way it is cooked are all named
          # here and the cooking rows answer instead.
          avoid=("phone", "laptop", "screen", "telly", "tv", "computer", "tablet", "monitor",
                 # a patch that went white where the bleach was is the bleach's doing, and that
                 # is the mark card's answer: a colour run puts dye on, it does not take it out
                 "bleach",
                 "oven", "pan", "pot", "kettle", "toaster", "microwave", "screwdriver", "car",
                 # a bath that "went blue" is a bath bomb or a colour tablet, not dye coming off
                 # a garment, and "rewash the ruined whites" was the whole answer it got
                 "bath", "bathwater",
                 "sky", "garlic", "onion", "dog", "cat", "puppy", "kitten", "feet",
                 # Somebody who went white and passed out is not a wash either, and "went" is in
                 # the key: that line got "rewash the ruined whites".
                 "pass out", "passed out", "faint", "fainted", "unconscious", "collapsed",
                 "seizure", "ambulance",
                 "toes", "fingers", "bruise", "nail",
                 "grey", "gray", "dull", "dingy", "yellow", "sauce", "gravy",
                 # a bar of chocolate that has gone white is bloom, and "gone" plus "white" was
                 # this row's key, so the wash answer was given to a cooking question
                 "chocolate", "cocoa", "bloom",
                 "curry", "soup", "stew", "custard", "porridge",
                 # food that turns green or blue is the food's own chemistry, not dye from the
                 # wash: garlic and pickles do it in acid, and cooking.py's garlic-green answers
                 # "my garlic went blue when i pickled it"
                 "garlic", "pickle", "pickles", "pickled", "chutney", "kimchi", "sauerkraut",
                 # A jumper that "went in the wash and shrank" is a size question: "went in"
                 # and "wash" are loose enough to catch it, and this answer then tells the
                 # person to rewash their whites. clothing.py's shrink-wool owns that line.
                 "shrank", "shrunk", "shrink",
                 # a load that comes out wet is a spin fault, not dye that ran: without
                 # this the "come out" key took "clothes come out wet" from the washer
                 "wet", "damp", "soaked", "soaking",
                 # Water out of a machine is the appliance question, and the water words say
                 # so on their own. Naming the machine here was too wide: "my whites went pink
                 # in the washing machine" is a colour run, and it lost its answer.
                 "drum", "leak", "leaking", "leaked", "pouring", "coming out", "puddle",
                 "running out", "runs out", "ran out",
                 # a crop that will not turn red is a ripening question, not dye from the wash:
                 # "why are my tomatoes not turning red" was told to rewash its whites
                 "tomato", "tomatoes", "plant", "plants", "crop", "crops", "vine", "fruit",
                 # raw and cooked meat, fish and egg: the pink, the blood and the blue are the
                 # meat's own colour, and the question is whether it is done
                 "meat", "chicken", "turkey", "beef", "pork", "lamb", "veal", "venison",
                 "mince", "steak", "steaks", "joint", "breast", "breasts", "thigh", "thighs",
                 "fillet", "chops", "sausage", "sausages", "bacon", "gammon", "ham",
                 "burger", "burgers", "meatball", "meatballs", "roast", "undercooked", "raw",
                 "bloody", "juices", "fish", "salmon", "cod", "prawn", "prawns",
                 "egg", "eggs", "yolk", "yolks", "omelette", "frittata",
                 # A part of a person that has "gone red" is not a garment: the key is the shape
                 # of "my whites came out pink", and it answered "my lips have gone puffy and red
                 # since last night" by telling the person to rewash the ruined whites. Nothing
                 # about a wash is the answer to a line about the body, so the row stands down
                 # for the words a body is said in - the swelling of an allergy included.
                 "lips", "lip", "tongue", "throat", "mouth", "face", "cheek", "cheeks",
                 "eyelid", "eyelids", "eye", "eyes", "nose", "neck", "chest", "skin",
                 "rash", "hives", "itchy", "itching", "puffy", "swollen", "swelling",
                 "breathing", "breathe", "allergic", "allergy",
                 # A launderette is a place to find and a price to ask, not a colour that ran:
                 # "is there a launderette near me" was answered with "rewash the ruined whites"
                 # once the washer's fault was in the conversation.
                 "launderette", "laundrette", "laundromat", "laundry service",
                 "dry cleaner", "dry cleaners", "near me", "nearest", "cheapest"),
          bias=1, guard=_a_colour_can_have_run),
    # Colour running the other way round: "how do i stop colours running" is a sorting question,
    # answered by the same entry that says how to keep them apart.
    entry("sorting-wash", (("whites", "colours", "colors", "darks", "lights", "laundry", "washing", "dye",
                            "dyes", "denim", "jeans"),
                            ("together", "separate", "separately", "sort", "sorting", "mix",
                             "mixing", "run", "runs", "running", "bleed", "bleeding")),
          "Sort by colour, not by kind of garment: whites and light colours in one load, darks and "
          "brights in another. It is new dark and red items that bleed for their first few washes, "
          "so wash those alone or with other darks the first time, and cold water keeps both the "
          "colour and the size.", bias=1,
          # "darks" is read loosely as "dark", so "what should i mix with dark rum" was a laundry
          # question. A drink in the line is never one; and "whites" in a kitchen is the egg, so
          # separating an egg is not a wash question either.
          avoid=("rum", "gin", "vodka", "whiskey", "whisky", "tequila", "brandy", "cocktail",
                 "cocktails", "drink", "drinks", "tonic", "mixer", "mixers",
                 "egg", "eggs", "yolk", "yolks", "meringue", "baking", "recipe",
                 # washing a food is a kitchen instruction, and once the water rows stopped
                 # taking "wash the rice until the water runs clear" this row took it: the
                 # second group's "runs" and the form of "washing" were all it needed. Sorting
                 # a wash is about garments, so a food names its own rows.
                 "rice", "pasta", "spaghetti", "noodles", "lentils", "quinoa", "chickpeas",
                 "beans", "greens", "spinach", "lettuce", "vegetables", "veg", "fruit",
                 "water runs clear", "runs clear",
                 # "how do i clean behind the washing machine" is the place, not the sorting:
                 # the appliance word made this row answer it
                 "behind", "underneath", "at the back of", "the back of",
                 # "run" is here for "colours running", and it also caught "what is the cheapest
                 # time to run the washing machine": the hour is the tariff row's question.
                 "cheapest", "cheaper", "best time", "what time", "off peak", "off-peak",
                 "night", "overnight", "in the morning", "in the evening", "during the day",
                 "time of day")),
    entry("soaking-wash", (("washing", "laundry", "washing machine load", "whites", "bedding"),
                           ("soak", "soaks", "soaking", "soaked", "overnight", "in water")),
          "An overnight soak does most of the work for you: warm water and a scoop of biological "
          "detergent, then wash it as normal in the morning. Keep wool, silk and anything with a "
          "dry-clean label out of it, keep brights away from whites, and do not leave a load more "
          "than a day or it starts to smell.",
          # a stain on a garment is the stain card's question, which says whether to soak and for
          # how long; this is the whole load left in the machine overnight
          avoid=("stain", "stains", "stained", "shirt", "shirts", "sick", "vomit", "curry",
                 "coffee", "tea", "blood", "ink", "wool", "woollen", "silk", "shrink", "shrunk",
                 "label", "labels", "symbol", "symbols", "colour run", "bled", "dye", "dyes",
                 # a soak in bleach is the bleach question, not the overnight detergent one:
                 # "can i soak whites in bleach" was told to add biological detergent
                 "bleach", "thin bleach", "milton", "napisan", "oxygen bleach")),
    entry("squeaky-shoes",
          (("shoes", "boots", "trainers", "sneakers", "plimsolls", "sandals"),
           ("squeak", "squeaks", "squeaking", "squeaky", "noise", "noisy", "creak", "creaking")),
          "Most squeaks come from two dry surfaces rubbing, so the fix is powder or wax rather "
          "than a new pair: dust the inside with talcum powder or bicarbonate of soda and rub a "
          "little beeswax or candle wax along the tongue and where the upper meets the sole. If it "
          "is a rubber sole on a shiny floor, scuff it lightly with sandpaper, and let wet shoes "
          "dry slowly with newspaper inside rather than on a radiator.",
          avoid=("which", "best", "buy", "size", "return", "smell", "waterproof", "clean")),
    entry("softener", (("fabric softener", "conditioner", "softener"),
                        ("need", "use", "should", "towels", "better", "worth", "matter")),
          "Most things don't need it: it coats the fibres, so towels stop drying you and gym kit "
          "stops wicking. A splash helps stiff jeans or scratchy jumpers; white vinegar in the "
          "softener drawer does the same job without the coating.",
          # a water softener is a machine plumbed in by the stopcock, and the buying question for
          # it was answered with towels that stop drying you: the shop's water-softener row owns
          # the machine, and the water words keep this row on laundry.
          avoid=("water softener", "water softeners", "water softening", "soften water",
                 "hard water", "limescale", "scale", "brine", "dishwasher salt", "kettle",
                 "shower head", "boiler", "stopcock", "plumber")),
    entry("laundry-symbols", (("symbol", "symbols", "care label", "label", "labels"),
                               ("mean", "means", "clothes", "washing", "understand", "read")),
          "The tub is washing: a number in it is the top temperature, a hand in it means hand wash "
          "only, and a cross through it means don't wash. Below that, a triangle is bleach, a square "
          "is drying (a circle inside means tumble dryer, a cross means none), and an iron is ironing.",
          # "how do i read a nutrition label" is the food packet, not a shirt, and it was answered
          # with the wash symbols: a label needs a word about clothes to be a care label.
          ask=("symbol", "symbols", "care label", "label", "labels", "clothes", "washing",
               "shirt", "shirts", "jumper", "trousers", "garment", "fabric", "iron", "ironing",
               "wash")),
    entry("delicates-wash", (("bra", "bras", "delicates", "delicate", "lingerie", "silk", "lace",
                              "knickers", "underwear", "blouse", "blouses", "tights", "stockings"),
                              # "what temperature for delicates" names no wash verb at all, and the
                              # bare heat word sent it to a body temperature, so the dial is read
                              # here too: this is the row that owns the delicates
                              # not "cycle": "cycling" matches it, and with "tight" read as
                              # "tights" that was four points, so "my quads are tight after
                              # cycling" got the bra-washing card. The dial words carry the
                              # "what temperature for delicates" question on their own.
                              ("wash", "washing", "machine", "hand", "bag", "net",
                               "temperature", "temp", "degrees", "how hot", "heat",
                               # the phrase, not the bare word: "cycling" matches "cycle"
                               "delicates cycle", "delicate cycle")),
          "Hook the bras, put them in a mesh laundry bag, and wash on a delicates cycle at 30C with "
          "a liquid detergent; never a hot wash or the dryer, which wrecks the elastic. Silk and "
          "anything lacy is safer hand-washed in cool water with a little shampoo.",
          # "tights" is read as "tight" by the plural rule, so "my quads are tight after
          # cycling" matched tights + cycle and got the laundry card. A body part and a muscle
          # are never a garment: the sports row answers those, and the garment lines keep their
          # wash answer. The body words are the whole of the list: "gym", "workout", "sore",
          # "ache" and "stiff" are how a sentence about washing clothes can read too - "how do
          # i wash my gym tights" was standing this row down and getting "I don't know enough to
          # answer that honestly" - so only the words that name the body keep it out.
          avoid=("quads", "quad", "thigh", "thighs", "calf", "calves", "hamstring",
                 "hamstrings", "muscle", "muscles")),
    entry("mend-hole", (("hole", "holes", "tear", "torn", "darn", "darned",
                          # Worn through is the same morning as a hole, said a day earlier, and
                          # it was reaching nothing: "my coat has worn out at the cuffs" and "my
                          # jeans have gone at the knee" got the floor's "Got it. Is there anything
                          # you'd like a hand with?", and "the cuffs on my shirt are frayed" got the
                          # grey-collar card, which is a stain answer to a garment that is wearing
                          # through. The wear words belong to the thing they are wearing on, so the
                          # garment word in the second key is what keeps them here: a tyre, a
                          # brake and a person can all be worn out, and none of those is mending.
                          "worn", "worn out", "worn through", "worn thin", "wearing thin",
                          "wearing out", "rubbed through", "frayed", "fraying", "fray",
                          "threadbare", "gone at the", "gone through"),
                         ("jeans", "jumper", "sock", "socks", "shirt", "cardigan", "knee", "patch",
                          "mend", "repair", "fix", "cuff", "cuffs", "hem", "elbow", "elbows",
                          "sleeve", "sleeves", "coat", "jacket", "trousers", "shorts", "skirt",
                          "dress", "hoodie", "sweatshirt", "linen", "seam", "seams", "lining",
                          # the heel and the toe are where a sock and a boot go first, and
                          # without them "my socks have worn through at the heel" reached the
                          # floor's nod. Both are body words too, which is what the guard above
                          # is for.
                          "heel", "heels", "toe", "toes", "pocket", "pockets", "glove", "gloves")),
          "Fix it before it grows: turn the garment inside out and darn across the hole with small "
          "running stitches, then across them at right angles, in thread close to the colour. A "
          "knee or a jeans pocket takes an iron-on patch on the inside, which is invisible and "
          "takes five minutes.",
          guard=a_worn_thing_is_a_garment,
          # a wall, a ceiling or a floorboard is not a garment, and "worn out" is also how a
          # person, a tyre and a brake pad are described: those are not mending jobs.
          avoid=("tights", "stockings", "ladder", "wall", "walls", "ceiling", "plaster",
                 "worn out from", "i am worn out", "im worn out", "i'm worn out", "tired",
                 "exhausted", "knackered", "brake", "brakes", "tread", "battery", "carpet",
                 "rug", "sofa", "cushion", "cushions", "mattress", "roof", "gutter", "gutters",
                 "plasterboard", "drywall", "skirting", "floorboard", "floorboards", "pavement",
                 "road", "roof", "roofs", "tyre", "tyres", "tube", "inner tube")),
    entry("swimwear", (("swimsuit", "swimming costume", "bikini", "swimwear", "trunks", "wetsuit"),
                        ("wash", "washing", "rinse", "machine", "dry", "chlorine", "smell",
                         "baggy", "stretched", "stretching", "loose", "elastic", "shrunk")),
          "Rinse it in cool water the moment you get out, chlorine or salt and all, and wash it by "
          "hand now and then with a little mild soap. Never wring it, never put it in the machine or "
          "the dryer, and dry it flat in the shade: heat and wringing are what stretch the elastic "
          "and turn the colour."),
    entry("wax-candle", (("wax", "candle", "candle wax"),
                          ("tablecloth", "cloth", "carpet", "remove", "iron", "spill", "sofa")),
          "Let it set, then crack off as much as you can with a knife. Lay kitchen paper over the "
          "rest and press it with a warm iron: the paper soaks the wax up, and you change the paper "
          "until nothing more comes through. On carpet, spoon some brown paper and iron that instead."),
    # Gym kit is said many ways, and "gear" and the named garments are the ones that were not
    # here: "my running gear smells" and "my sports bra smells" got the musty-machine answer and
    # a shrug, when the subject is sweat left in the fibre. "Gym equipment" and "exercise kit" are
    # not on any shopping list either, and a kit that smells is laundry whether it is a shirt or a
    # bench pad: with the buying words out of `home-gym-kit` these are what keep "my gym equipment
    # smells" from having no owner at all. A towel stays with the towel entry, which says more.
    entry("sweat-smell", (("sweat", "sweaty", "body odour", "bo", "armpit", "gym kit", "sports kit",
                           "gym clothes", "gym stuff", "gym top", "gym gear", "workout clothes",
                           "running kit", "running gear", "sports gear", "cycling kit",
                           "sports bra", "leggings", "base layer", "lycra", "gym equipment",
                           "exercise kit", "training kit"),
                           ("smell", "smells", "stink", "stinks", "smelly", "remove", "get rid")),
          "Soak in cool water with a cup of white vinegar for half an hour, then wash at 40C with "
          "biological powder and no fabric softener. The smell lives in bacteria left in the fibres, "
          "so an occasional 60C wash of the whole load is what keeps it away.",
          # the bag entry below puts "gym" in a second cleaning key, which costs this one the
          # rarity point on "gym clothes"; the bias keeps cloth lines here, and the avoid keeps
          # the skin-and-sweat question (science.sweat) where it belongs.
          avoid=("nervous", "stress", "gland", "glands", "skin", "my sweat", "sweat smells",
                 "why does my sweat", "antiperspirant", "deodorant"),
          bias=1),
    # The bag keeps the smell even after the kit is washed, and the fix is a different one: it is
    # the lining and the damp that hold it, not the fibre.
    entry("gym-bag-smell", (("gym bag", "kit bag", "sports bag", "boot bag", "gym rucksack",
                             "training bag"),
                            ("smell", "smells", "stink", "stinks", "smelly", "wash", "clean",
                             "fresh", "get rid")),
          "Empty it out every time you get home, turn it inside out and wipe the lining with a "
          "cloth wrung out in warm soapy water, then leave it open to dry somewhere airy. Sweaty "
          "kit goes straight in the wash, not back in the bag, and a sock of bicarbonate of soda "
          "left in the bottom overnight takes up what is left of the smell.",
          # "my gym bag smells of sweat" names the bag, so the bag is the subject, not the skin.
          bias=2),
    # The food that leaves an orange mark, and the things it lands on: "how do i get bolognese
    # out of my top" was "That's beyond what I know" while the same line with "shirt" in it was
    # answered here. A top, a jumper and a pair of jeans are what people say.
    entry("curry-stain", (("curry", "bolognese", "gravy", "ketchup", "tikka", "turmeric",
                           "tomato sauce", "passata", "chilli sauce", "salsa", "stew"),
                           ("stain", "stains", "shirt", "shirts", "clothes", "tablecloth",
                            "remove", "out of", "off my", "off the", "top", "tops", "t-shirt",
                            "tshirt", "tee", "jumper", "hoodie", "sweatshirt", "blouse", "dress",
                            "trousers", "jeans", "shorts", "sleeve", "sleeves", "napkin", "bib",
                            "apron", "cushion")),
          "Run cold water through the back of the stain, rub in a little washing-up liquid or stain "
          "remover and leave it 15 minutes, then wash at the hottest the label allows. Turmeric "
          "stains fade further in sunlight if you hang the washed item outside for a few hours."),
    entry("chocolate-stain",
          (("chocolate", "chocolates", "choc", "cocoa", "nutella", "chocolate spread",
            "hot chocolate"),
           ("shirt", "shirts", "top", "t shirt", "tshirt", "blouse", "dress", "jeans", "denim",
            "trousers", "skirt", "sleeve", "jumper", "sweater", "cardigan", "hoodie", "fabric",
            "clothes", "uniform", "carpet", "rug", "sofa", "settee", "couch", "upholstery",
            "cushion", "cushions", "mattress", "duvet", "bedding", "towel", "tablecloth",
            "seat", "car seat", "back seat", "hand", "hands", "fingers", "finger",
            "table", "highchair",
            "out of", "off the", "off my", "off a", "out the", "stain", "stains", "stained",
            "clean", "cleaned", "cleaning", "remove", "removing", "get out", "get it off")),
          "Let it cool and set first: warm chocolate smears further, so lift the solid part off "
          "with a knife or a spoon before any water goes near it. Then work a drop of "
          "washing-up liquid into the mark with your fingers, rinse from the back of the fabric "
          "in cold water, and wash at the temperature on the label. On a sofa, a car seat or a "
          "carpet, blot with a damp cloth instead of rinsing, and finish with clean water.",
          # the bar itself is a different question: bloom, seizing and tempering are cooking
          # answers, and a jar that has gone white is not a stain
          avoid=("bloom", "blooms", "seized", "seize", "temper", "tempering", "melt", "melting",
                 "melted", "curdle", "grey", "gray", "streaky", "hoard", "eat", "eating",
                 "how much", "calories", "sugar", "recipe", "cake", "brownies", "biscuits")),
    entry("blood-on-a-surface",
          (("blood", "bloody", "bled"),
           ("mattress", "mattresses", "sofa", "settee", "couch", "upholstery", "cushion",
            "cushions", "carpet", "rug", "rugs", "headboard", "car seat", "back seat", "seat")),
          # bedding is clothing.py's own job ("got blood on my bedsheets" is its card), so no
          # sheet, duvet or pillow word is a key here: it would answer a wash question with a
          # mattress one.
          "Cold water only, and plenty of it: hot water sets blood into the fibre. Blot the "
          "mark with a cloth wrung out in cold water, work in a little washing-up liquid or a "
          "dab of biological detergent, then blot again with clean water. On a mattress, use as "
          "little water as you can and dry it well with a towel so the filling does not stay "
          "damp.",
          # a cut that will not stop is a first-aid question, and a period is the body's
          avoid=("cut", "cuts", "bleeding", "wound", "wounds", "nosebleed", "period", "periods",
                 "in my stool", "in my urine", "in my sick", "coughing", "in my poo")),
    entry("coffee-sofa", (("coffee", "tea", "cola", "juice",
                           # the drinks people actually name when they knock one over: milk,
                           # squash and hot chocolate reached nothing at all, and the blot in
                           # smaller patches is the same job whatever was in the cup
                           "milk", "squash", "hot chocolate", "water"),
                           # the fixed surfaces a drink lands on: a carpet, a sofa, a rug and a
                           # mattress keep their own cards (they say what this one cannot), and
                           # the plain floor, worktop and highchair had no owner at all.
                           ("carpet", "sofa", "rug", "upholstery", "mattress",
                            "floor", "floors", "worktop", "worktops", "counter", "counters",
                            "laminate", "lino", "highchair",
                            # a car seat is the same fixed fabric with a blotting job, and
                            # "how do i get coffee out of a car seat" was the price of a cot
                            # from the baby-gear row: no cleaning noun in the line, only the
                            # thing the drink landed on
                            "car seat", "car seats", "back seat", "back seats", "seat", "seats",
                            "car interior", "headrest",
                            # a drink and a stain with no surface named is still a drink on
                            # something: "tea stain on the table" and "coffee stain on the table"
                            # reach nothing else, and "squash stain on a table" is a spill, not
                            # the heat bloom that home.py's wood-stain is about
                            "stain", "stains", "stained")),
          "Blot up as much as you can with kitchen paper, then dab with cool water and a drop of "
          "washing-up liquid, working from the outside in so it doesn't spread. Blot dry with a "
          "towel and repeat; on a coffee stain, a little white vinegar in the water helps.",
          # a drink down a shirt is clothing.py's stain entry: the outside-in dab is for a fixed
          # surface, and you cannot turn a shirt inside out to rinse it from the back
          avoid=("shirt", "shirts", "top", "blouse", "trousers", "jeans", "dress",
                 "clothes", "clothing", "jumper", "sweater", "cardigan", "sock", "socks",
                 "t shirt", "tshirt", "uniform",
                 # Water is one of the drinks, and water is also the thing that comes out of a
                 # boiler. "the boiler is leaking water on the floor" and "water dripping on the
                 # floor" are leaks - a fitter's job, not a blot - so a leak word stands the dab
                 # down and leaves the boiler and radiator cards their own answers.
                 "leak", "leaks", "leaking", "leaked", "drip", "drips", "dripping",
                 "boiler", "boilers", "radiator", "radiators", "pipe", "pipes", "piping",
                 "burst", "plumbing", "cistern", "overflow", "overflowing",
                 "washing machine", "dishwasher", "tap", "taps", "faucet",
                 # And a stain on plaster is water from above or behind it, not a drink: "water
                 # stain on the ceiling" was told to blot it with kitchen paper.
                 "ceiling", "ceilings", "paintwork", "plaster", "plasterboard", "damp",
                 "mould", "mold",
                 # The words "water stain" and "water mark" are not the gate, though: a wet mark
                 # on a FLOOR is a spill and the blot-and-dab card is its answer, and holding
                 # them out took "water mark on the floor" and "water stain on the floor" off it
                 # and gave them a floor-scratch card. What says the water came from above is the
                 # ceiling, paintwork or plaster word, and those are already above.
                 "water damage", "soaked through", "coming through the")),
    entry("nail-polish-spill", (("nail polish", "nail varnish", "nailpolish"),
                                 ("carpet", "sofa", "clothes", "spill", "remove", "table", "wood",
                                  # the garment people name instead of "clothes": "how do i get
                                  # nail varnish out of jeans" was answered with how to paint
                                  # nails, because "clothes" was the only garment word here
                                  "jeans", "denim", "shirt", "shirts", "trousers", "dress",
                                  "dresses", "skirt", "jumper", "jumpers", "cardigan", "hoodie",
                                  "coat", "jacket", "fabric", "sleeve", "duvet", "bedding",
                                  "towel", "tablecloth", "curtain", "curtains", "upholstery",
                                  "out of", "off a", "off my", "off the", "got it on")),
          "Work on it before it dries, dabbing with a cotton bud dipped in nail polish remover on "
          "fabric (test on a hidden bit first) or in acetone on hard surfaces. Blot, never rub, and "
          "change the pad as it takes up colour. On skin, warm soapy water and a little oil will do.",
          # a manicure is the other question these words ask: base coat, two thin coats, chipping
          avoid=("base coat", "top coat", "thin coat", "two coats", "chipping", "chips", "chip",
                 "smudge", "dry faster", "drying", "dries", "paint my nails", "painting my nails",
                 "on my nails", "my nails", "manicure", "pedicure")),
    # "how do i get marker pen off a table" was a shrug, and the ink rows around it are the skin
    # and the shirt. A marker on furniture, plastic or paint is alcohol and blotting, so it gets a
    # row of its own with the surfaces in the key.
    entry("marker-off-a-surface",
          (("marker", "marker pen", "permanent marker", "felt tip", "felt tip pen", "felt tips",
            "sharpie", "biro", "ballpoint", "ink", "highlighter"),
           # a wall and a sofa are not hard surfaces: the crayon row answers a wall (and the
           # word "wall" is a tie with it, so leaving it here flips the answer), and a sofa has
           # the upholstery blot
           ("table", "tables", "desk", "desks", "worktop", "worktops", "floor", "floors",
            "plastic", "phone case", "shelf", "shelves", "door", "doors",
            "whiteboard", "fridge", "freezer", "toy", "toys", "leather",
            "monitor", "screen", "keyboard", "mouse", "case", "paintwork", "laminate",
            # a table is named by its material as often as by its name
            "wooden table", "kitchen table", "coffee table", "dining table", "desk top")),
          "Alcohol is what takes a permanent marker off a hard surface: dab hand sanitiser, "
          "isopropyl alcohol or a little nail polish remover onto a cloth and wipe with the grain, "
          "changing the cloth as it lifts the ink, then wash the residue off with soapy water. On "
          "pale wood or laminate, try a soft eraser or a dab of toothpaste first, because alcohol "
          "can dull a varnished finish - test in a corner you will not see.",
          # "pen" is a key word of this row and "marker pen" says it, so it cannot be an avoid
          # word as well: that alone took "how do i get marker pen off a table" off its answer
          avoid=("shirt", "shirts", "jeans", "trousers", "clothes", "fabric", "hands", "skin",
                 "fingers", "carpet", "rug", "suede", "my pen", "the pen", "pen refill",
                 "refill", "cartridge", "printer", "leaking pen")),
    entry("paint-on-glass",
          (("paint", "painted", "gloss", "emulsion", "undercoat", "varnish", "primer",
            "spray paint"),
           ("window", "windows", "glass", "pane", "panes", "glazing", "double glazing",
            "tiles", "tile", "worktop", "mirror", "bath", "shower screen", "door glass")),
          "Emulsion and other water-based paint lift with warm soapy water: soak the splash for a "
          "few minutes, then slide it off with a plastic scraper or a razor blade held almost flat "
          "to the glass. Gloss and oil paint want white spirit on a cloth, left a moment to soften, "
          "then the same scraper. Work in one direction and keep the blade wet, which is what stops "
          "it scratching.",
          bias=2,
          # "can you paint bathroom tiles" and "how do i paint a sash window" are the decorating
          # rows' questions, and the verb in front of the surface is what tells them apart
          avoid=("wall", "walls", "door", "doors", "frame", "frames", "how many", "much paint",
                 "litres", "tin", "tins", "coverage", "brush", "brushes", "roller", "coat",
                 "coats", "sand", "sanding", "stripper", "heat gun", "which paint", "best paint",
                 "paint a", "paint my", "paint the", "paint our", "painting a", "painting the",
                 "painting my", "can you paint", "can i paint", "should i paint",
                 "could i paint", "do i paint", "tile paint", "window paint", "paint over")),
    entry("sticker-residue", (("sticker", "stickers", "label", "labels", "sticky", "tape",
                               "glue"),
                               ("remove", "residue", "jar", "glass", "stuck", "mess",
                                # a price label on a window or a windscreen is the same job,
                                # and "how do i get a sticker off a window" reached nothing:
                                # the key wanted a noun from this list and the line named the
                                # thing the sticker is on
                                "window", "windows", "window pane", "windscreen", "windshield",
                                "mirror", "door", "doors", "wall", "walls", "floor", "floorboards",
                                "off a", "off the", "off my", "off our", "get it off")),
          "Soak the sticky patch in warm soapy water or dab it with oil (olive, baby, even mayonnaise) "
          "and leave it five minutes, then rub it off with your thumb or a cloth. White spirit or "
          "rubbing alcohol lifts the last of it from glass and hard plastic.",
          # a sticker on a jar is this answer; a pair of glasses or a watch that came apart is a
          # repair, and this entry keys the word "glass", so the guard has to be the phrases for
          # the things worn rather than the bare plural (which matches "glass" through its
          # singular form and would cost "how do i get a sticker off a glass jar")
          avoid=("my glasses", "the glasses", "pair of glasses", "glasses arm", "glasses frame",
                 "glasses broke", "broken glasses", "fix my glasses", "spectacles", "specs",
                 "sunglasses", "frames", "lenses", "temple", "temples", "watch strap",
                 "watchstrap", "bracelet", "necklace", "earring", "earrings", "earring")),

    # Glue on the skin is the one thing a tube of superglue warns about, and it was a shrug:
    # "how do i get superglue off my fingers" and "how do i get glue off my hands" both asked
    # for a search. The answer is water and time, because tearing at it takes the skin with it.
    entry("glue-on-skin", (("glue", "glued", "gluing", "superglue", "super glue", "araldite",
                             "epoxy", "adhesive"),
                            ("skin", "hands", "hand", "fingers", "finger", "fingertips",
                             "fingertip", "thumb", "palms", "palm", "eyelid", "eyelids",
                             "lips", "stuck together", "stuck to my", "off my hands",
                             "off my fingers", "off my skin", "off my face", "my hands",
                             "my fingers", "my skin")),
          "Soak the stuck fingers in warm soapy water for 15 to 20 minutes and the glue softens "
          "enough to roll apart - roll, do not pull, because pulling takes the skin with it. A "
          "little cooking oil, or nail varnish remover on a cotton bud for superglue, works on "
          "what is left. Do not use a blade or a solvent on broken skin, and if two fingers are "
          "really stuck, or glue has gone into a cut or an eye, get seen the same day.",
          # something being stuck back together is a repair, and the sticky patch on a jar is
          # the residue question: neither is glue on a person
          avoid=("glasses", "spectacles", "specs", "sunglasses", "frame", "frames", "lens",
                 "lenses", "arm", "arms", "temple", "temples", "sticker", "stickers", "label",
                 "labels", "price tag", "residue", "sticky", "tape", "jar", "jars", "glass",
                 "bottle", "carpet", "wall", "wood", "chair", "table", "toy", "toys", "shoe",
                 "shoes", "sole", "ceramic", "plastic", "handle", "back together",
                 "back on", "fix", "repair", "broken", "broke", "snapped")),

    # --- the machine and the cupboards -------------------------------------
    entry("machine-marks", (("washing machine", "washer", "wash"),
                             ("marks", "black", "dark", "streaks", "stains", "leaving", "leaves")),
          "Dark marks usually mean the drum or the seal needs cleaning: wipe the rubber door seal "
          "with a damp cloth and check the filter, then run an empty 90C service wash with a machine "
          "cleaner. Run the load a size smaller than you think; an overfull drum can't rinse properly.",
          # "washing up" is a sink, not the machine
          avoid=("washing up", "glasses", "cutlery", "dishes", "crockery", "window", "mirror",
                 "car", "hands", "dishwasher",
                 # a load that comes out wet is a spin or drain fault, not a mark: "my washing
                 # machine leaves the clothes wet" was this row, because both keys want the
                 # machine and "leaves" is in the second half here.
                 "wet", "wringing", "soaking", "sopping", "dripping", "damp", "still wet",
                 "come out wet", "comes out wet", "not spinning", "wont spin", "won't spin")),
    entry("bin-smell", (("bin", "bins", "bin bag", "wheelie bin", "kitchen bin"),
                         ("smell", "smells", "stink", "clean", "wash", "odour",
                          # a bin that has gone mouldy is washed out like one that smells, and
                          # it was the loaf entry's line: "my bread bin is mouldy" was told not
                          # to cut the mould off the bread, which is advice about a loaf
                          "mould", "mold", "mouldy", "moldy", "mildew", "green inside",
                          "green in the", "green mould", "gone green")),
          "Wash the bin with hot soapy water and a splash of bleach, dry it, and put a couple of "
          "bicarbonate-of-soda balls or a sheet of newspaper in the bottom. Line it every time and "
          "take food waste out daily in summer.",
          # A loaf that has gone mouldy in the bin is a question about the loaf, and a place named
          # with "bin" beside it (a bin store, a bin cupboard, the ceiling over the bin) is a
          # question about that place: the wall and ceiling rows answer those, and "mould on the
          # ceiling in the bin store" was getting the bin washed out instead.
          avoid=("mouldy bread", "bread is mouldy", "bread has gone mouldy", "mould on the bread",
                 "mouldy loaf", "loaf is mouldy", "bread went mouldy", "mouldy food",
                 "bin store", "bin cupboard", "bin shed", "bin room", "bin area", "bin chute",
                 "ceiling", "wall", "walls", "skirting", "plaster", "grout",
                 # the Recycle Bin on a desktop is emptied, not washed: "how do i clean the bin on
                 # my desktop" and "how do i empty my bin" are the computer answer, so the
                 # computer words stand this one down.
                 "desktop", "recycle bin", "recycle", "trash", "mac", "macbook", "windows",
                 "laptop", "computer", "pc", "hard drive", "downloads", "iphone", "android",
                 "icon", "disk", "storage", "junk file", "junk files",
                 # maggots and flies are the row appended at the end of this file
                 "maggots", "maggot", "grubs", "flies"),
          # The bread in the bin is the bread's question, and this entry washed out the bin:
          # "how do i stop bread going mouldy in a bread bin" was told to line it. "my bread bin
          # is mouldy" is the bin's own line and stays here, and the phrases in `avoid` above
          # cannot tell the two apart, so the guard reads which thing went off. Nor can they tell
          # the bin from a food going in it - "can i cut the mould off cheese or should i bin it"
          # - so the guard reads that too.
          guard=lambda read: not (_the_loaf_went_off(read) or _the_food_was_binned(read))),
    # A tub that keeps its smell is not the bin: the plastic has taken the smell in, and hot
    # soapy water on its own does not lift it out. "how do i stop tupperware smelling" and "how
    # do i get a smell out of a lunchbox" had no answer at all.
    entry("container-smell",
          (("tupperware", "lunchbox", "lunch box", "food container", "plastic container",
            "container", "containers", "tub", "tubs", "flask", "water bottle"),
           ("smell", "smells", "smelly", "stink", "stinks", "tainted", "curry", "get rid",
            "stop it", "clean", "wash", "keep the smell")),
          "Fill it with hot water, a spoon of bicarbonate of soda and a splash of vinegar, leave "
          "it overnight and wash it as normal in the morning: that lifts the smell out of the "
          "plastic where soap alone does not. Dry it with the lid off, and leave a scrunched "
          "sheet of newspaper inside - a tub sealed while it is still damp is what keeps the "
          "smell in. Lemon juice, or a paste of bicarbonate, does the same job in an hour.",
          avoid=("bin", "bins", "nappy", "nappies", "baby", "sterilise", "sterilize", "formula",
                 "fridge", "freezer", "dishwasher", "kettle", "washing machine", "drain",
                 "sink", "shower", "bath", "toilet", "car", "bike bottle")),
    # No "sparks" here: a microwave that sparks is a hazard (metal in the cavity, a burnt
    # waveguide cover), and steam-and-lemon is the wrong thing to tell someone holding it.
    entry("microwave-clean", (("microwave",),
                               ("clean", "smell", "grease", "inside")),
          "Put a bowl of water with a slice of lemon in for 3 minutes on high, then leave the door "
          "shut another 5: the steam loosens everything and it wipes off. Never run it empty and "
          "never put metal in, and unplug it before you scrub the inside.",
          avoid=("spark", "sparks", "sparking", "sparked", "arcing", "flashing")),
    entry("shower-curtain-clean", (("shower curtain", "shower curtains", "bath mat",
                                    "bath mats", "bathmat", "bathmats", "shower mat",
                                    "shower mats", "curtain", "liner"),
                                    ("clean", "wash", "mould", "machine", "smell",
                                     # the words people use for a mat that needs a hot wash:
                                     # "how do i stop a bath mat getting slimy" reached nothing
                                     "slimy", "slime", "slippery", "smelly", "musty",
                                     "getting dirty", "grey", "discoloured", "discolored")),
          "Most fabric curtains and bath mats go in the machine at 40C with a couple of towels and a "
          "little detergent, then hang them up to dry. A bath mat is a weekly wash; a fabric curtain "
          "every month or two. Plastic liners wipe clean with a cloth and white vinegar; run the fan "
          "after showers and mould stops coming back.",
          # `bath-mat-grip` shares the words "bath" and "mat" with this row, which costs this one
          # a uniqueness point in the domain and let the towel-wash row answer "how often should i
          # wash my bath mat" with "wash them at 60C". Washing a mat is this row's question.
          bias=1),
    # "How do I clean the shower" itself had no answer at all - the bathroom card covers the
    # room, the curtain card covers the curtain and the screen card covers the glass - so the
    # tray and the walls were a search hedge on main.
    entry("shower-clean", (("shower", "showers", "shower tray", "shower cubicle", "shower walls",
                            "shower enclosure"),
                           ("clean", "cleaning", "scrub", "smell", "smells", "often", "how",
                            "limescale", "soap scum")),
          "Squeegee the walls and the tray after every shower, which takes twenty seconds and "
          "saves most of the scrubbing; once a week spray the walls and tray with white vinegar "
          "or a bathroom spray, leave it ten minutes and rinse. A mug of bicarbonate of soda and "
          "hot water down the tray keeps the drain sweet, and black silicone wants a mould spray "
          "rather than more scrubbing.",
          avoid=("curtain", "liner", "screen", "glass", "mirror", "mould", "mold", "grout",
                 # scaling has its own answer, in home.py, with the vinegar and the citric acid
                 "limescale", "descale", "descaling", "scale", "scaled", "furred", "hard water",
                 "drain", "blocked", "backing up", "not draining", "head", "hose", "broken",
                 "not working", "replace", "replacing", "fit", "fitting", "buy", "buying",
                 "best", "which", "electric", "power", "pump", "tray crack", "leak", "leaking",
                 # a shower that runs cold or will not heat is a boiler question
                 "hot water", "cold", "boiler", "pressure")),
    entry("gutters-often", (("gutters", "gutter", "guttering", "downpipe", "downpipes"),
                            ("clean", "cleaning", "clear", "often", "blocked", "how often")),
          "Twice a year: once after the leaves fall in late autumn, and again in spring. Clear the "
          "gutters and the top of each downpipe by hand from a ladder with someone footing it, and "
          "check that water runs away rather than down the wall.",
          # This is the frequency card. A pipe that is already blocked wants the rodding method,
          # which `downpipe-blocked` in home.py carries, so the fault words stand this one down
          # and "how often should i clean my gutters" keeps it.
          avoid=("unblock", "unblocking", "unblocked", "blocked", "blockage", "blocking",
                 "backing up", "backed up", "not draining", "wont drain", "won't drain",
                 "overflowing", "overflows", "full of leaves", "rod", "rods")),
    # A draught is not always a door: "there is a draught in my bedroom" and "my flat is
    # draughty" are the same complaint about a room, and the card needed a door word before, so
    # both reached the chat pool. The room words are in the second group and the reply names the
    # other places a draught gets in, because the person who says "bedroom" has not found it yet.
    entry("draught-door", (("draught", "draughts", "draft", "drafts", "draughty", "drafty",
                            "cold air", "cold coming", "wind coming"),
                           ("door", "doors", "under the door", "front door", "letterbox", "floor",
                            "window", "windows", "gap", "coming in",
                            "room", "rooms", "bedroom", "bedrooms", "living room", "lounge",
                            "kitchen", "hall", "hallway", "flat", "house", "home", "in here",
                            "everywhere", "somewhere", "all the time", "whole")),
          "A brush or rubber strip that screws or sticks to the inside of the door is the cheap fix, "
          "about ten pounds and ten minutes: measure the gap first. For a bigger gap, a fabric "
          "draught excluder on the floor side; a letterbox flap and a keyhole cover cost a few "
          "pounds more. That alone makes the room feel warmer. If the draught is not at the door, "
          "run your hand round the window frames, the skirting and any old chimney or vent, and "
          "fill the gap with a strip, a bead of sealant or a chimney balloon.",
          # a whole cold house is a heating question, not a door: "my house is cold and
          # draughty" wants the radiator and flow-temperature answer, and the word "house" in
          # this card's key had it taking the door fix instead. The house words are the fence,
          # not the subject.
          avoid=("house is cold", "home is cold", "flat is cold", "whole house", "whole flat",
                 "central heating", "the heating is on", "my heating", "boiler")),
    entry("brush-clean", (("hairbrush", "hair brush", "brush", "comb"),
                           ("clean", "hair", "wash", "greasy")),
          "Pull the loose hair out with a comb or a pencil, then swill the brush in warm water with "
          "a little shampoo and let it dry bristles down. Once a month is plenty, and it makes the "
          "brush work properly again.",
          # Brushing the hair is not cleaning the brush: "how often should i brush my hair" and
          # "is it bad to brush wet hair" were both told to swill a brush in shampoo.
          avoid=("brush my hair", "brush your hair", "brush her hair", "brush his hair",
                 "brushing my hair", "brushing your hair", "brush my own hair",
                 "brush wet hair", "brushing wet hair", "wet hair", "brush it wet",
                 "how often should i brush my hair", "should i brush my hair")),
    # A pane of glass is a window however it is hung, and the row only knew the words window,
    # glass and mirror: "how do i clean patio doors" was answered with how to lift a spill out of
    # upholstery, "how do i clean french doors" was told to learn French, and "my windscreen is
    # smeary" and "my skylight is streaky" were punts. The words are the things the glass is in,
    # never the bare "door" - a door is also wood and paint, and the draught and the paint rows
    # are the answers there.
    entry("windows-streak", (("windows", "window", "glass", "mirror", "mirrors",
                              "windowpane", "window pane", "pane", "panes", "patio door",
                              "patio doors", "french door", "french doors", "glass door",
                              "glass doors", "skylight", "skylights", "conservatory",
                              "conservatory roof", "windscreen", "windscreens", "windshield",
                              "glazing", "window glass"),
                              # The fault said as an adjective rather than as a noun. A key made of
                              # "streak" and "smear" only answered the job ("how do i clean a
                              # streaky window") and the complaint ("my windows are streaky"), and
                              # left "my window glass is streaky" a punt: the subject matched
                              # twice, once per word, and no second part was ever said.
                              # "fingerprints" is the same complaint and the same cloth.
                              ("clean", "streak", "streaks", "streaky", "streaked", "streaking",
                               "smear", "smears", "smeary", "smeared", "smudge", "smudges",
                               "smudgy", "smudged", "filmy", "film", "fingerprint", "fingerprints",
                               "fingermarks", "finger marks", "water marks", "watermarks",
                               # the plain complaint, which had no card at all: "my windows are
                               # dirty" and "my conservatory roof is dirty" were both punts
                               "dirty", "dirt", "grubby", "dusty", "dust", "grime", "grimy",
                               "filthy", "greasy", "sooty", "smoky", "smokey", "cloudy",
                               "inside",
                               # A mark on a mirror is a mark on glass: "how do i get hairspray
                               # off the mirror" was answered with the physics of reflection,
                               # and "white marks on the mirror" with road salt on leather boots.
                               "mark", "marks", "hairspray", "hair spray", "hairspray marks",
                               "toothpaste", "splashes", "splash", "splashed", "spots", "spot",
                               "smudges", "smudge", "buff")),
          "Wash with warm water and a drop of washing-up liquid, then squeegee or wipe with a cloth "
          "and buff dry straight away with a dry cloth or newspaper. Work top to bottom and out of "
          "direct sun, which dries the glass before you can polish it.",
          avoid=("spectacles", "specs", "dishwasher", "cutlery", "wine glass",
                 "drinking glass", "shower", "goggles",
                 # a table, a hob and a screen are glass-like but their marks are their own
                 # answers, and none of them wants a squeegee
                 "table", "tables", "tabletop", "glass table", "worktop", "worktops", "hob",
                 "tv", "television", "laptop", "phone", "screen", "cooker", "oven",
                 # Water that lands on the glass by itself is not a window to wash:
                 # "condensation on the inside of my windows every morning" was this row's
                 # clean-and-squeegee reply, and what that person needs is why the window is wet,
                 # which home.py's condensation row answers. Written as phrases around the word,
                 # not the bare word: "how do i clean condensation off the inside of the windows"
                 # does ask how to wipe glass, and it keeps this row.
                 "condensation on", "condensation in", "condensation every", "condensation each",
                 "condensation builds", "condensation runs", "condensation running",
                 "condensation forms", "condensation from", "condensation is"),
          guard=lambda understood: (_a_dirty_window_not_a_wet_one(understood)
                                    and _glass_in_the_line_is_a_window(understood))),
    # Washing up by hand had no card at all: "how do i wash dishes by hand" and "do i need to
    # rinse dishes after washing up" were the search shrug on main, and "how hot should the water
    # be for washing dishes" reached the laundry dial, which is a different wash.
    entry("dishes-by-hand",
          (("dishes", "dish", "washing up", "wash up", "washed up", "plates", "crockery",
            # not "sink": "how do i clean my kitchen sink" and "should I get a new kitchen sink"
            # are the sink's own answers (deft-lime)
            "cutlery", "mugs", "pots", "saucepans"),
           # "how do i" and "should i" were in this group, and a group a question form can
           # satisfy is no group at all: every line that says "how do i" then needed one word
           # from above, and "pot" reads as "pots", so "how do i grow herbs in a pot" and "how
           # do i grow potatoes in pots" got the sink, from a row with no washing in them. The
           # phrase that is about dishes and nothing else takes their place, because a bare
           # "how do i do the dishes" has no wash word in it.
           ("wash", "washing", "washed", "by hand", "hot water", "how hot", "temperature",
            "rinse", "rinsing", "soap", "liquid", "do the dishes")),
          "Fill the sink with the hottest water you can bear and a squirt of washing-up liquid, "
          "then work in order: glasses and mugs first, plates and cutlery next, and the greasy "
          "pans last. Rinse in hot water and stand everything to air dry on a rack, and change "
          "the water the moment it goes greasy rather than adding more soap to it.",
          # the machine, the shopping and the blocked sink are their own answers, and so are the
          # things people wash that are not dishes
          avoid=("dishwasher", "machine", "blocked", "unblock", "drain", "smelly", "smell",
                 "filter", "rinse aid", "salt", "tablet", "buy", "how much",
                 # water that has landed is not a wash: "wet patch under the sink after washing
                 # up" was answered with the order to wash the glasses first, and the person is
                 # asking where the water came from
                 "wet patch", "puddle", "leak", "leaking", "dripping", "soaked", "flood",
                 "cost", "price", "install", "my hands", "face", "hair", "laundry",
                 "clothes", "clothing", "car", "window", "glasses", "spectacles", "wine glass",
                 "sponge", "dishcloth", "cloth", "cloth is", "tea towel", "scourer", "brush",
                 "grease", "greasy", "burnt", "stuck",
                 # a pan is the pan card's: "how do i clean my pots and pans" wants the
                 # bicarbonate soak, not the order to wash the glasses first
                 "pans", "pots and pans", "grill pan",
                 # and a pot in a garden is a plant pot: this row keys the bare word "pots"
                 # (how people say pans), and "how do i grow tomatoes in pots" was told to wash
                 # the glasses first. The growing words stand it down; "plant" and "potting" are
                 # deliberately not here, because the stemmer reads "potting" as "pot" and
                 # "how do i clean a plant pot" is a washing-up question this row answers well.
                 "grow", "growing", "grows", "grown", "garden", "gardening", "seed", "seeds",
                 "sow", "sowing", "soil", "compost", "balcony", "allotment", "greenhouse",
                 "tomato", "tomatoes", "vegetables", "veg", "crops",
                 # a pot with a plant in it is the garden's: "how do i protect my pots in
                 # winter" and "how do i look after pots in winter" were the washing-up order.
                 # The bare "pots" stays out of here because a kitchen pot is this row's
                 "pots in winter", "pot in winter", "pot plants", "pot plant", "plants in pots",
                 "plant in a pot", "overwinter", "overwintering", "winter pots",
                 "terracotta pots", "grow bag", "grow bags",
                 # how to wash up is one question and who does it is another: "my partner
                 # never helps with the washing up" and "my husband does the dishes once a
                 # week" read the job's own words and were handed the order to wash the
                 # glasses first. A person in the line turns it into the load question, and
                 # the fairness rows answer it.
                 "partner", "husband", "wife", "boyfriend", "girlfriend", "flatmate",
                 "housemate", "roommate", "lodger", "kids", "children", "teenager",
                 "never helps", "never does", "never does the", "never does any",
                 "won't help", "wont help", "doesn't help", "does not help",
                 "doesnt help", "won't do", "wont do", "won't", "wont",
                 "always leaves", "leaves it", "leaves them", "all the time",
                 "every time", "every single time", "fed up", "sick of", "resent",
                 "unfair", "fair share", "argue", "arguing", "argument", "row about",
                 "on my own", "by myself", "does my head in"),
          bias=2),
    # "how do i get grease off pans without a dishwasher" got a dishwasher buying answer and
    # "how do i wash a greasy roasting tin by hand" got the shampoo card, on the word "wash".
    entry("grease-off-pans",
          # the bare words "tin" and "tray" are a litter tray, a tea tray and a cake tin as well
          # as the thing a roast comes in, so only the cooking ones are keyed
          (("pan", "pans", "wok", "frying pan", "grill pan", "saucepan", "saucepans",
            "roasting tin", "roasting tray", "roasting pan", "baking tray", "baking sheet",
            "baking tin", "cake tin", "loaf tin", "muffin tin", "oven tray", "casserole"),
           # the state alone is somebody's cooking going wrong ("my rice stuck to the pan"), so
           # every word in this group is about getting something off
           ("grease", "greasy", "fat", "fatty", "burnt on", "stuck on", "wash", "washing", "clean",
            "cleaning", "by hand", "scour", "scrub", "soak", "soaking", "get off", "gets off",
            "coming off", "comes off", "scrape")),
          "Wipe the fat out with kitchen paper while the pan is still warm and bin the paper - "
          "never pour it down the sink. Then soak the pan in hot water with a squirt of "
          "washing-up liquid and a spoonful of bicarbonate of soda for twenty minutes, and a "
          "nylon scourer lifts the burnt ring; a stainless pan can be boiled with water and a "
          "splash of vinegar instead.",
          # cooking in it, buying it and a non-stick coating that has gone are not the wash
          avoid=("recipe", "how long", "how do i cook", "how long to roast", "oven temperature",
                 "buy",
                 "best", "which", "non stick", "non-stick", "coating", "season", "induction",
                 "dishwasher", "put in", "hob", "gas", "bake a", "casserole recipe", "my hands",
                 "sponge", "dishcloth", "tea towel", "rice", "pasta", "stuck to", "sticks to",
                 "sticking", "why did it", "porridge", "sauce", "bolognese", "curry",
                 "litter", "cat", "cats", "kitten", "ashtray", "ice cube", "ice tray",
                 "seed tray", "tea tray", "smell", "smells", "smelly",
                 # a pan that is burnt is the bicarbonate boil, not the wipe-the-fat-out card:
                 # this row is about the fat. A wok keeps its own salt-and-brush answer too.
                 "burnt", "burned", "burn", "charred", "wok",
                 # the grill pan and its rack are home.py's oven-grill answer, which names the
                 # rack and the element (deft-lime)
                 "grill pan", "grill tray", "the grill",
                 # to grease a pan or a tin is to prepare it: "how do i grease a cake tin"
                 # was answered here with wiping the fat out. cooking.py grease-a-tin-or-pan
                 # has that sense, and it only fires on a greasing or lining word, so
                 # "how do i clean a greasy muffin tin" still lands here.
                 "grease a", "grease an", "grease my", "grease the", "grease it",
                 "greasing a", "greasing the"),
          bias=2),
    entry("glasses-cloudy", (("glasses", "glass", "cutlery", "crockery", "dishes", "plates"),
                              ("cloudy", "white marks", "white film", "film", "streak", "streaks",
                               "smear", "smears", "marks")),
          "Cloudy glasses and white marks are hard water and rinse aid running out: fill the salt "
          "and rinse aid, then run the hottest cycle with a dishwasher cleaner. Glasses washed by "
          "hand go cloudy from too much washing-up liquid and water that's too hot, so use less and "
          "let them air dry instead of towelling them.",
          # home.py answers a cloudy load out of the dishwasher; this is the hand-washed case.
          # A pair of spectacles is the other domain's: "how do I clean my glasses without
          # streaking" is a lens question, and clothing.py's lens entry answers it.
          avoid=("dishwasher", "windshield", "window", "mirror", "spectacles", "specs", "lie",
                 "lens", "lenses",
                 # A shower screen, a vase and a bottle are glass too, and their marks are scale,
                 # not rinse aid: "white marks on the shower glass" was told the salt and rinse
                 # aid were running out.
                 "shower", "showers", "bathroom", "tile", "tiles", "grout", "vase", "vases",
                 "carafe", "jar", "jars", "bottle", "bottles",
                 # A table, a door and a screen are glass too, and their marks are not a
                 # dishwasher running out of salt: "white marks on the glass table" and "white
                 # marks on the glass door" were told to fill the rinse aid.
                 "table", "tables", "dining table", "coffee table", "side table", "furniture",
                 "door", "doors", "glass door", "shelf", "shelves", "cabinet", "cupboard",
                 "window", "windows", "windscreen", "windshield", "screen", "screens", "tv",
                 "television", "monitor", "laptop", "phone", "tablet", "conservatory",
                 "greenhouse", "lantern", "mirror", "mirrors")),
    # A glass top is furniture, and every row that knew the word "glass" was about something else:
    # "white marks on the glass table" got the dishwasher's rinse aid, then the wood-water-ring
    # card's mayonnaise, and "how do i clean a glass table" got the wine-glass card's "wash them by
    # hand". A glass table is wiped, not washed, and it is the one surface where the wrong thing
    # (an abrasive, or ammonia on a coated top) scratches for good.
    entry("glass-table-clean",
          (("glass table", "glass tables", "glass top", "glass tabletop", "glass coffee table",
            "glass dining table", "glass desk", "glass shelf", "glass shelves", "glass cabinet",
            "glass sideboard", "glass tv stand"),
           ("mark", "marks", "white marks", "white ring", "water mark", "water marks", "ring",
            "rings", "smudge", "smudges", "smear", "smears", "fingerprint", "fingerprints",
            # The asking shapes ("how do i", "what is best") were here and they scored a line
            # about a scratch on the same key words as a line about a mark: the glass-scratch row
            # says a scratch will not polish out at home, and this card told the person to wipe
            # it. The mark words carry the line on their own, so the asks are gone and a scratch
            # stands the row down.
            "streak", "streaks", "clean", "cleaning", "wipe", "dust", "dirty", "sticky",
            "scuff", "scuffs", "polish", "polishing", "polished", "shine", "shiny", "buff")),
          "Warm water with a drop of washing-up liquid and a soft cloth takes fingerprints and greasy "
          "marks off a glass top, then buff it dry with a microfibre cloth so it does not streak. A "
          "white ring or a chalky bloom is limescale, and a cloth wrung out in white vinegar lifts it "
          "without any scrubbing. Skip anything abrasive - cream cleaner, a scouring pad, a melamine "
          "sponge - and skip ammonia or glass spray on a coated or tinted top, because both dull the "
          "surface for good.",
          # the drinking glasses, the wine glasses and the dishwasher's cloudy load are the other
          # glass rows, and a window, a mirror and a shower screen each have their own
          avoid=("drinking", "drink", "wine", "beer", "pint", "crockery", "cutlery", "dishes",
                 "dishwasher", "tumbler", "tumblers", "mug", "mugs", "spectacles", "specs",
                 "lens", "lenses", "window", "windows", "mirror", "mirrors", "shower", "vase",
                 "bottle", "carafe", "jar", "windscreen", "windshield", "car", "phone", "tv",
                 "television", "monitor", "laptop", "screen", "screens", "tablet", "cooker",
                 "oven", "hob",
                 # a glass door is a door: "how do i clean a glass door" was the bicarbonate
                 # paste and a plastic scraper, which is right for a door and wrong for a top,
                 # and this row's own answer opens "off a glass top"
                 "door", "doors", "front door", "patio door", "shower door",
                 # a scratch is its own answer: it does not polish out at home, and this card
                 # would tell the person to wipe a gouge out of the top
                 "scratch", "scratches", "scratched", "scratching", "gouge", "gouges",
                 "chipped", "chip", "chips", "cracked", "crack"),
          bias=1),
    # "how do i clean my wine glasses" was the 14-units answer, which is the wrong subject
    # twice over; the state of them ("cloudy", "white marks") is the row above.
    entry("wine-glass-clean",
          (("wine glass", "wine glasses", "champagne flute", "champagne flutes", "flutes",
            # "how do i wash my drinking glasses" is a washing-up question: the row stood down on
            # the word "drinking" (kept there for the 14-units card) and the units card took the
            # line, so the pair of words is here in full and "drinking" alone is not enough
            "drinking glass", "drinking glasses", "water glasses", "set of glasses",
            "glassware", "tumblers", "brandy glasses"),
           ("clean", "cleaning", "cleaned", "wash", "washing", "polish", "polishing", "shiny",
            "sparkle", "sparkling", "sparkly", "streaks", "smears", "spotless", "fingerprints",
            "dishwasher", "dry", "rinsing", "rinse")),
          "Wash them by hand in hot water with a drop of washing-up liquid, rinse, and dry them "
          "with a linen cloth held round the bowl rather than the stem: a dishwasher and a hot "
          "rinse are what leave wine glasses cloudy and spotted. Marks that will not lift want a "
          "soak in warm water with a splash of white vinegar, then the same cloth.",
          # the weekly-limit card lists "wine" and "glasses" too and outranks this one on the
          # rarity of those two words, so the cleaning row says plainly that it is the closer fit
          bias=2,
          # "drink" and "drinking" are drink questions, but "drinking glasses" is a pair of
          # tumblers: the phrase is in the key, so the avoid carries the shapes a units question
          # actually has instead of the bare word.
          avoid=("how many", "units", "alcohol", "how much", "too much", "every day", "daily",
                 "bottle", "bottles", "pregnant", "safe", "red or white", "which wine", "pair",
                 "decant", "carafe", "rack", "storage", "store", "break", "broke", "smash",
                 "chipped", "cracked")),
    entry("marker-on-skin", (("marker", "permanent marker", "ink", "pen", "sharpie"),
                              ("hands", "skin", "fingers", "finger", "face")),
          "Rub it with an oil-based cleanser, baby oil or a little cooking oil, then wash with soap; "
          "alcohol hand gel or nail polish remover works on ink that's already dry. It wears off in "
          "a day or two anyway, and it isn't harmful on ordinary skin.",
          # "pen" and "hands" are two ordinary words, and between them they took a symptom:
          # "my hands shake when i hold a pen" was told to rub oil on the ink. A hand that
          # shakes is not a stained one.
          avoid=("shake", "shakes", "shaking", "shaky", "shook", "tremble", "trembles",
                 "trembling", "tremor", "tremors", "numb", "numbness", "tingling", "tingle",
                 "weak", "weakness")),
    # A pen or a crayon is put down on whatever is within reach, so the surfaces are the whole
    # house and not just the wall: "how do i get crayon off a table", "felt tip off my worktop"
    # and "marker off the desk" were punts while "crayon off the wall" was answered.
    entry("crayon-walls", (("crayon", "crayons", "felt tip", "pencil", "marker", "chalk",
                            "pen", "pens", "biro", "biros", "ballpoint", "ink"),
                            ("wall", "walls", "paint", "painted", "drawing", "draw", "sofa",
                             # papered walls and the car's back seat are the same wipe, and
                             # "how do i get crayon off wallpaper" was the stripping card
                             "wallpaper", "wall paper", "woodwork", "car seat", "car seats",
                             "back seat", "cushion", "cushions", "curtain", "curtains",
                             "carpet", "carpets", "rug", "rugs", "mat", "mats", "upholstery",
                             "table", "tables", "tabletop", "worktop", "worktops", "counter",
                             "desk", "floor", "floors", "floorboard", "floorboards", "laminate",
                             "lino", "linoleum", "tile", "tiles", "door", "doors", "cupboard",
                             "cupboards", "drawer", "drawers", "shelf", "shelves", "skirting",
                             "banister", "stair", "stairs", "window", "windows", "glass",
                             "worktop board", "chopping board", "whiteboard", "fridge",
                             "freezer", "tray", "oilcloth", "plastic")),
          "A damp cloth with a little washing-up liquid takes most of it, and a dab of toothpaste "
          "or a melamine sponge lifts what is left on paint, varnish, laminate or a worktop. Test a "
          "hidden patch first and keep the sponge light: too much rubbing takes the paint or the "
          "finish with it. Dried ink wants a drop of nail polish remover on a cloth, wiped off and "
          "rinsed. On a carpet, a rug or a sofa, blot with warm water and washing-up liquid instead "
          "of scrubbing, then rinse and dry it flat.",
          # "felt tip" is also "a tip" to the money domain, and the two rows tie on the line: the
          # bias holds this one, because a felt tip on a wall is not a question about tipping.
          # "does that work on wood too" is a follow-up about the answer just given, not a new
          # surface to clean, and this row has no way to tell the two apart from its own words.
          bias=1,
          avoid=("that work", "it work", "does work", "will work", "would work", "work on")),
    entry("glitter-cleanup", (("glitter", "sequins", "confetti"),
                               ("clean", "everywhere", "remove", "craft", "carpet", "hoover", "up")),
          "Roll a lint roller or a strip of sticky tape over the hard floors and worktops, and "
          "vacuum the carpet, then wipe the vacuum head: glitter sticks to everything. A slightly "
          "damp cloth gets the last pieces off hands and surfaces."),
    entry("mattress-clean", (("mattress", "mattresses"),
                              ("clean", "stain", "smell", "vacuum", "accident", "wash", "wet",
                               "spill", "yellow")),
          "Vacuum it, then dab stains with cool water and a little washing-up liquid, and dust the "
          "whole surface with bicarbonate of soda for an hour before vacuuming again. Air it by "
          "stripping the bed for the morning, and use a washable protector so this is rare.",
          # shopping.py's mattress-buy has the longer key and wins the tie on "best way to
          # clean a mattress"; a cleaning question is this entry's, a buying one is theirs, and
          # "how much should a decent mattress cost" is a buying one however it is worded.
          bias=1,
          # the price words only: "how much water do i need to clean a mattress stain" is a
          # cleaning question, and "much", "firm", "soft" and "decent" are cleaning words too
          avoid=("cost", "costs", "price", "prices", "cheap", "cheaper", "buy", "buying",
                 "worth", "replace", "replacing", "spend", "budget")),
    # Hair on a fabric is this card whatever the hair came off: "how do i get hair off my sofa"
    # and "how do i get dog hair off the sofa" were both answered by a hair-washing card in
    # science.py, which read "hair" and "how do i" and stopped there. The bias is what settles
    # that tie, since both cards match the same two words.
    entry("pet-hair", (("pet hair", "dog hair", "cat hair", "fur", "hair", "hairs"),
                        ("sofa", "settee", "couch", "carpet", "rug", "clothes", "jumper", "coat",
                         "remove", "clean", "hoover", "vacuum", "everywhere", "off",
                         # hair in a car is the same job with a smaller space: "how do i get dog
                         # hair out of the car" was told every six to eight weeks
                         "car", "car seat", "back seat", "boot", "upholstery", "seats",
                         # the same job again wherever the hair lands: a jacket, a duvet, a
                         # blanket, the stairs and the dryer's filter were four punts and one
                         # "keep the cat off the bed" answer before these words were here
                         "jacket", "coat", "duvet", "duvet cover", "blanket", "throw", "stairs",
                         "stair carpet", "tumble dryer", "dryer", "lint filter", "filter")),
          "A damp rubber glove or a squeegee pulled across the fabric gathers pet hair into rolls "
          "that lift off easily, and a vacuum with the brush bar down gets the rest. Wash the "
          "covers at 40C now and then: hair works into the weave and no brush reaches it.",
          bias=2,
          # hair on a head is the hair-care questions in science.py, and hair in a waste pipe is
          # a blocked drain: neither is housework on a fabric
          avoid=("scalp", "shampoo", "conditioner", "dandruff", "greasy", "frizzy", "curl",
                 "curly", "thinning", "bald", "grey", "dye", "straighten", "dryer", "comb",
                 "plughole", "plug hole", "drain", "bathtub", "sink", "basin", "trap",
                 "u bend", "u-bend", "shower", "bath", "bathroom", "blocked", "blockage",
                 "unblock", "slow to drain",
                 # whether to buy the thing the hair is on is a buying question, not a cleaning
                 # one: "is a tumble dryer worth it for pet hair" was this row on the first cut
                 "worth", "worth it", "should i", "should i buy", "which one", "best one")),
    # Lint is not hair and it is not a stain: "how do i get lint off black trousers" and "how
    # do i remove lint from a shirt" were both the blot-and-rinse stain card, and "my towel
    # leaves fluff on me" was a "Thanks for telling me". The lift-off is a roller or tape, and
    # the cause is what is washed with what.
    # A machine full of hair is the same job as a sofa full of hair, in a smaller space with a
    # filter in it. "my washing machine is full of dog hair" matched the soaked-pet card in
    # pets.py on the dog and the machine and was told to towel a guinea pig dry; "how do i get
    # pet hair out of the drum" was a shrug. The machine words here and the hair words in the
    # first group say which question it is, and the filter is the part that matters.
    entry("hair-in-the-machine",
          (("hair", "hairs", "pet hair", "dog hair", "cat hair", "fur", "furball", "furballs",
            "lint", "fluff"),
           # the tumble dryer's own lint filter has a card that says to clean it after every
           # load and why a clogged one is a fire risk; this row is the drum and the wash.
           # "filter" and "machine" on their own are any machine's word: a vacuum filter full of
           # hair was answered with a washing-machine service wash, so only the multi-word parts
           # of this one are keys.
           ("washing machine", "washer", "washing mashine", "drum",
            "door seal", "detergent drawer")),
          "Pull the hair out of the drum and the filter first: a damp rubber glove or a squeegee "
          "gathers it into rolls that lift out, and a vacuum with the brush bar down gets the "
          "rest. Clean the filter and the door seal, then run a hot 60C service wash with a "
          "machine cleaner, because the grease that traps the hair goes with it. Hair in the drum "
          "is not a fault, but a filter packed with it is why a machine stops draining.",
          bias=3,
          # hair on a head, in a plug hole or on a sofa is another card's question
          avoid=("scalp", "shampoo", "conditioner", "dandruff", "greasy", "frizzy", "curl",
                 "curly", "thinning", "bald", "grey", "dye", "straighten", "comb", "brush",
                 "plughole", "plug hole", "drain", "bathtub", "sink", "basin", "trap",
                 "u bend", "u-bend", "shower", "bath", "bathroom", "sofa", "settee", "couch",
                 "carpet", "rug", "clothes", "clothing", "jumper", "coat", "jacket", "duvet",
                 "blanket", "car seat", "upholstery",
                 # a machine that smells or a filter that is already the subject of the line is
                 # the smell card's question, and a dryer's lint filter has its own card
                 "smell", "smells", "smelling", "smelled", "smelt", "stink", "stinks",
                 "stinking", "odour", "odor"),
          guard=_not_the_dryer_alone),
    entry("lint-on-clothes",
          (("lint", "fluff", "fuzz", "bits of fluff", "white bits", "bobbles of fluff"),
           ("trousers", "trouser", "shirt", "shirts", "clothes", "clothing", "jumper", "coat",
            "jacket", "skirt", "dress", "black", "dark", "towel", "towels", "on me", "all over",
            "remove", "get off", "off", "clean", "washing", "wash", "dryer", "tumble dryer",
            "roller", "what is", "what are")),
          ("Roll it off with a lint roller, or wind sticky tape round your hand, sticky side out, "
           "and press and lift: that beats any brush on a dark fabric, and a damp rubber glove "
           "does the same job. Wash the garment inside out, apart from towels and fleeces, which "
           "are what sheds it, and empty the tumble dryer's filter after every load - a full "
           "one blows fluff back onto the clothes. New towels shed for their first few washes, "
           "so wash them alone until they stop."),
          bias=2,
          # a bobble is a pill in the weave and the fabric shaver has that answer; hair is the
          # pet-hair card; the dryer's own filter, a fire and a blocked vent are the dryer rows
          avoid=("bobble", "bobbles", "bobbly", "pilling", "pilled", "shaver", "razor",
                 "pet hair", "dog hair", "cat hair", "animal hair", "hair", "hairs",
                 "filter", "lint filter", "fire", "burning", "smell", "smells", "smoke",
                 "vent", "hose", "not heating", "not drying", "takes ages", "cuts out",
                 "take out", "get out of the", "out of the tumble")),

    entry("wine-furniture", (("red wine", "wine"),
                              ("sofa", "settee", "upholstery", "cushion", "rug", "chair")),
          "Blot up what you can without rubbing, then dab with cool water and a drop of washing-up "
          "liquid, working from the edge inwards, and blot dry with a towel. Keep going with clean "
          "water until the towel comes away clean, and don't scrub: that pushes the wine deeper into "
          "the filling.",
          # "red wine" is a subject three rows share - choosing a bottle, what to drink it with,
          # and getting it out of a chair - and both drinking rows list "good" among their words,
          # so "do u know a good way to get red wine out of a rug" reached them and this row lost
          # a tie on registry order. A line that wants the wine out of a thing is this row's.
          bias=3),
    # The cleaning domain has `wine-furniture` for a sofa or a chair and the clothing domain has
    # `stain-red-wine` for a garment, so this one is the cloth in between: what goes in the wash.
    entry("red-wine-cloth",
          (("red wine", "wine"),
           ("curtain", "curtains", "tablecloth", "napkin", "napkins", "linen", "bedsheets",
            "bed sheets", "duvet", "duvet cover", "pillowcase", "throw", "cushion cover")),
          "Soak it in cool water with a scoop of biological washing powder for half an hour, then "
          "wash cool on the usual cycle, and check it before it goes anywhere near the dryer: heat "
          "sets a wine stain for good. Curtains can go in the machine if the label allows, hung "
          "back damp so the weight pulls the creases out."),
    entry("duvet-wash", (("duvet", "duvets", "pillow", "pillows", "quilts"),
                          ("wash", "washing", "clean", "machine", "smell", "yellow", "how",
                           # "what temperature for a duvet" asks this card's own question and
                           # was reaching the fever row for the want of one word
                           "temperature", "temp", "degrees", "hot")),
          "Most duvets and pillows go in a big machine (9kg or a launderette drum) on a gentle 40C "
          "cycle with a couple of towels to balance the load, then dry thoroughly before use. "
          "Feather down needs dryer balls on low heat for hours; a half-dry duvet goes musty."),
    # The screen is what people say: "limescale on shower glass" and "how do i clean the shower
    # glass" both named the glass and the shower but not the screen or the door, so they matched
    # nothing here and `glasses-wash` answered them - a pair of spectacles is washed by hand, and
    # the person was told never to put their shower screen in the dishwasher. The glass, the
    # panel and the enclosure are the same surface as the screen and the door.
    entry("soap-scum", (("soap scum", "scum", "shower screen", "shower door", "shower glass",
                         "glass screen", "glass screen door", "shower panel", "shower panels",
                         "shower enclosure", "shower cubicle", "screen", "screens", "bath"),
                         ("clean", "remove", "shower", "glass", "white", "film", "limescale",
                          "scale", "scaled", "mark", "marks", "cloudy", "hazy", "water mark",
                          "water marks", "get rid", "get off")),
          "Warm white vinegar with a drop of washing-up liquid cuts soap scum and limescale - they "
          "are the same white bloom from hard water plus soap, and the acid lifts both: spray it "
          "on, leave 10 minutes, then scrub with a non-scratch pad and rinse. A spoonful of citric "
          "acid in water does the same job, and do not use an abrasive pad, because it scratches "
          "glass for good. Squeegee the screen after every shower and it never builds up in the "
          "first place.",
          # "which is better, a shower or a bath" and "is a bath better than a shower" are a
          # choice, not a cleaning job: the bath word alone was enough to bring them here.
          # "a bath or a shower" with the article in it slips past the contiguous phrase, and
          # "less water" and "how long" are the water question rather than the cleaning one, so
          # both shapes stand this card down and the bath-or-shower card answers them.
          # ("best" and "better" on their own are not here: "whats the best way to get a shower
          # screen properly clean" is the cleaning question asked with a superlative in front of
          # it, and the words that make it a choice are the comparison, not the superlative.)
          avoid=("which is better", "which is best", "whats better", "what is better",
                 "whats best", "what is best", "is it better", "better than", "best for",
                 "the best one", "best option", "best of the two", "worse", "prefer", "rather",
                 "or a bath", "or a shower",
                 # a rust mark in a bath is the rust row's: the vinegar here is for limescale,
                 # and a rust stain wants the acid then the enamel touched up
                 "rust", "rusty", "rusted", "rust mark", "rust marks", "rust stain",
                 "bath or shower", "bath or a shower", "shower or bath", "shower or a bath",
                 "shower instead", "instead of", "worth it", "aches", "ache", "relax",
                 # "how often" stays out of this list: the four bath cards already avoid
                 # "clean" and "scum", so the cleaning card keeps "how often should i clean the
                 # bath" while "how often should i take a bath" reaches the length card
                 "help me sleep", "before bed", "less water", "more water",
                 "uses less", "how long", "every day", "daily",
                 # hair in a bath or a shower tray is a blocked drain, not a scum ring: "how do i
                 # get rid of hair in the bath" reached this row on "bath" plus "get rid"
                 "hair", "hairs", "plughole", "plug hole", "drain", "drains", "blocked",
                 "blockage", "clogged", "slow to drain",
                 # a screen is not always a shower: "how do i remove a scratch from my phone
                 # screen" is the phone's own card, and vinegar on a phone is bad advice
                 "phone", "mobile", "iphone", "tablet", "laptop", "computer", "tv",
                 "television", "watch",
                 # Swapping the bath for a shower is a builder's question: "is it worth replacing
                 # a bath with a shower" was reaching this card for the bath in it, and cleaning
                 # advice is not an answer to whether to have the work done.
                 "replace", "replacing", "replaced", "swap", "swapping", "swapped",
                 "install a shower", "installing a shower", "fit a shower", "fitting a shower",
                 "fitted a shower", "shower over the bath")),
    # A room that is a mess is not a room that needs cleaning: people say it as a statement,
    # there is no verb in it, and every room row keys on the job instead ("needs a clean", "how
    # do i clean"), so "the kitchen is a mess", "my room is a mess" and "the house is a mess"
    # reached the sympathy line and nothing else. The key is a place plus the state it is in, so
    # one answer covers every room, and a dirt that has a job of its own (the oven, the drain, a
    # leak, a smell, a pest) keeps its card.
    # The job said with its plain verb is the same request as the state said as an adjective, and
    # this row only knew the state: "how do i tidy my bedroom", "how do i clean the living room",
    # "how do i clean up my room" and "how do i tidy my flat" were a hedge or the storage card,
    # while "how do i tidy up my bedroom" was answered, because "tidy up" happened to be a word of
    # the row and "tidy" alone was not. A room plus the verb names the job.
    #
    # A kitchen and a bathroom are left out on purpose: each has a card of its own that says the
    # job in the right order (surfaces then floor, dry before wet), and a general plan that also
    # matched them would take `how do i clean my kitchen` and `how do i clean my bathroom` off
    # those cards. A house, a flat and a home are left out for the same reason: the clear-out
    # plan in plans.py already answers the whole home ("one room at a time, three bags").
    # The whole home said with a cleaning verb, which nothing answered: "how do i clean my house",
    # "how do i clean the flat", "how do i clean my home" and "how do i clean my whole house" were
    # all a hedge. The clear-out row in plans.py keys "tidy my house" and its neighbours, but its
    # avoid list carries "cleaning" and "clean the" as word families, so a cleaning verb can never
    # reach it; a room row would have taken the kitchen and the bathroom off their own cards. The
    # whole home is its own job, so it is its own row.
    # An evening's cooking leaves a job behind, and the line rarely says "kitchen": "how do i clean
    # up after baking", "how do i clean the kitchen after cooking", "how do i clean up after
    # dinner" and "how do i clear up after a roast" were the first-step-into-baking card (the
    # activity and a "how do i"), a bread recipe or a heat card. The job after cooking is the
    # kitchen's own order to work in, and "after" is what says so.
    entry("the-job-after-cooking",
          (("clean up after", "cleaning up after", "clear up after", "clearing up after",
            "wash up after", "washing up after", "tidy up after", "the mess after", "mess after",
            "clean after", "wipe down after", "after baking", "after cooking", "after i cook",
            "after i bake", "after dinner", "after a roast", "after a meal", "after making"),
           ("bake", "baking", "baked", "cook", "cooking", "cooked", "roast", "roasted", "dinner",
            "meal", "fry", "fried", "frying", "kitchen", "oven", "hob", "pans", "pots", "supper",
            "tea", "lunch", "breakfast", "curry", "cake", "biscuits", "bread")),
          _KITCHEN_ORDER,
          # the stain, the smell, the oven and the drain keep their own cards, and a line about
          # what to cook after something is a recipe question
          avoid=("stain", "stains", "smell", "smells", "smelly", "stink", "drain", "drains",
                 "blocked", "mould", "mold", "damp", "oven cleaner", "burnt on", "burned on",
                 # the things with a cleaning answer of their own keep it: "how do i clean the
                 # oven after a roast" is the oven's, not the order to work round the room in
                 "oven", "ovens", "hob", "hobs", "fridge", "freezer", "microwave", "dishwasher",
                 "cooker", "extractor", "bin", "bins", "washing machine", "hoover", "vacuum",
                 "carpet", "floor", "floorboards", "sink", "dishes", "plates", "pans washed",
                 "what can i cook", "what should i cook", "what shall i cook", "recipe",
                 "recipes", "what to cook", "meal plan", "meal idea", "meal ideas")),
    entry("a-whole-home-to-clean",
          (("house", "home", "flat", "apartment", "whole house", "whole flat", "the house",
            "the flat", "the home", "my house", "my flat", "our house", "our flat"),
           ("clean my", "clean the", "clean this", "clean our", "clean up my", "clean up the",
            "clean out", "deep clean", "spring clean", "springclean", "spring cleaning")),
          "Start with what is on the floor: pick it all up into one basket, take the cups and "
          "plates out to the kitchen and bin the rubbish, because clothes, cups and paper are most "
          "of a mess and that alone makes a room look tidy. Then wipe the one surface you use most "
          "- the worktop, the table or the bedside - and give the rest one room a day rather than "
          "all of it in a panic.",
          avoid=("oven", "hob", "fridge", "freezer", "microwave", "dishwasher", "kettle",
                 "drain", "drains", "blocked", "leak", "leaks", "leaking", "damp", "mould",
                 "mold", "limescale", "pest", "pests", "mice", "mouse", "rats", "ants", "smell",
                 "smells", "smelly", "stain", "stains", "carpet", "rug", "sofa", "couch",
                 "curtain", "curtains", "mattress", "paint", "painting", "decorate", "decorating",
                 "wall", "walls", "garden", "bin", "bins", "washing machine", "hoover", "vacuum",
                 "screen", "phone", "laptop", "computer", "tv", "windows", "window",
                 # how long a job takes is a length, and the cards that answer with a length
                 # ("a whole house done properly is most of a day...", "about four hours") own
                 # these lines: "how long does it take to clean the house" got this plan instead
                 *_HOW_LONG)),
    entry("a-room-with-a-job-to-do",
          (("bedroom", "bedrooms", "room", "rooms", "living room", "lounge", "sitting room",
            "front room", "dining room", "hall", "hallway", "landing", "stairs", "playroom",
            "study", "office", "desk", "utility room", "spare room", "basement", "bedsit"),
           ("tidy my", "tidy the", "tidy this", "tidy our", "tidy up my", "tidy up the",
            "clean my", "clean the", "clean this", "clean our", "clean up my", "clean up the")),
          "Start with what is on the floor: pick it all up into one basket, take the cups and "
          "plates out to the kitchen and bin the rubbish, because clothes, cups and paper are most "
          "of a mess and that alone makes a room look tidy. Then wipe the one surface you use most "
          "- the worktop, the table or the bedside - and give the rest one room a day rather than "
          "all of it in a panic.",
          avoid=("oven", "hob", "fridge", "freezer", "microwave", "dishwasher", "kettle",
                 "drain", "drains", "blocked", "leak", "leaks", "leaking", "damp", "mould",
                 "mold", "limescale", "pest", "pests", "mice", "mouse", "rats", "ants", "smell",
                 "smells", "smelly", "stain", "stains", "carpet", "rug", "sofa", "couch",
                 "curtain", "curtains", "mattress", "paint", "painting", "decorate", "decorating",
                 "wall", "walls", "garden", "bin", "bins", "washing machine", "hoover", "vacuum",
                 "screen", "phone", "laptop", "computer", "tv",
                 *_HOW_LONG)),
    entry("a-room-that-is-a-mess",
          (("kitchen", "kitchens", "bathroom", "bathrooms", "bedroom", "bedrooms", "living room",
            "lounge", "sitting room", "front room", "dining room", "hall", "hallway", "landing",
            "stairs", "house", "home", "flat", "apartment", "room", "rooms", "whole house",
            "whole flat", "playroom", "study", "office", "desk", "garage", "basement",
            "utility room", "spare room", "loft"),
           ("mess", "messy", "a tip", "is a tip", "a right tip", "a proper tip", "a total tip",
            "an absolute tip", "shambles", "disaster", "in a state", "right state",
            # The state of a room is said with a dirt word as well as with the mess words, and the
            # row knew none of them: "my kitchen is filthy", "the bathroom is dirty", "the flat is
            # dirty", "the house is disgusting" and "my room is grim" were a listening line or a
            # "Got it." - the plainest way of saying a room needs cleaning, unanswered. The place
            # is still the other half of the key, so a dirty carpet, a filthy oven and dirty
            # clothes keep their own cards, and the dirt with a job of its own (a stain, a drain,
            # a smell) is in the avoid list below.
            "filthy", "dirty", "grimy", "grubby", "minging", "disgusting", "manky", "unhygienic",
            "filthy dirty",
            "needs a tidy", "needs tidying", "needs sorting", "tidy up", "tidying up", "clear up",
            "clear it up", "where do i start", "where to start", "where do we start",
            "dont know where to start", "don't know where to start", "overwhelmed", "out of hand",
            "out of control", "clutter", "cluttered", "untidy", "piles of stuff",
            # A room full of junk is a room to clear: with the bare "tip" gone from this row the
            # follow-up "weve got a loft full of junk" lost its answer, because "junk" was not a
            # word any row here knew and the tidy plan had been answering it by accident.
            "junk", "full of junk", "lots of junk", "old junk", "piles of junk",
            "stuff everywhere", "full of stuff", "too much stuff",
            # Somebody coming is why the state is urgent, and it is the same question: "the
            # kitchen is a mess and i have guests coming" is the room and its state, and it was
            # answered by the cook-something row ("guests" + "coming"). The arrival is only a
            # state word here, so a line about visitors with no room in it keeps its own card.
            "guests coming", "guests are coming", "people coming", "people are coming",
            "visitors coming", "visitors are coming", "guests arriving", "having guests",
            "having people over", "having visitors", "someone coming over",
            "someone is coming over")),
          "Start with what is on the floor: pick it all up into one basket, take the cups and "
          "plates out to the kitchen and bin the rubbish, because clothes, cups and paper are most "
          "of a mess and that alone makes a room look tidy. Then wipe the one surface you use most "
          "- the worktop, the table or the bedside - and give the rest one room a day rather than "
          "all of it in a panic.",
          avoid=("oven", "fridge", "freezer", "hob", "microwave", "kettle", "dishwasher",
                 "drain", "drains", "blocked", "blockage", "leak", "leaks", "leaking", "damp",
                 "mould", "mold", "limescale", "pest", "pests", "mice", "mouse", "rats", "rat",
                 "ants", "cockroach", "cockroaches", "silverfish", "moth", "moths", "weevil",
                 "bedbug", "bedbugs", "fleas", "smell", "smells", "smelly", "stink", "stinks",
                 "stain", "stains", "carpet", "carpets", "rug", "rugs", "sofa", "couch",
                 "curtain", "curtains", "mattress", "paint", "painting", "decorate",
                 "decorating", "wall", "walls", "garden", "bin", "bins", "washing machine",
                 "hoover", "vacuum",
                 # the bare "tip" used to be a key of this row, so the tips of a plant, of hair
                 # and of nails were read as a room that is a tip: "why are my plant leaves
                 # going brown at the tips" then "its a monstera in the living room" got the
                 # tidy-the-room plan (polite-cord, #6173 regression, main watch 81). The
                 # phrases below are the ones the word belongs to when it is not rubbish.
                 "tips of", "tip of my", "at the tips", "brown tips", "brown tip", "black tips",
                 "brown edges", "crispy edges", "plant", "plants", "houseplant", "houseplants",
                 "monstera", "orchid", "orchids", "fern", "cactus", "succulent", "leaves",
                 "leaf", "fingertips", "finger tips", "nails", "nail polish",
                 # a person or a life in a mess is not a room: "my life is a mess" and "my head
                 # is a mess" have their own answers, and this row is only about places
                 "life", "head", "mind", "mental", "relationship", "marriage", "money", "debt",
                 "finances", "career", "job", "hair", "skin",
                 # "where do i start" is a phrase that opens any big job, and the buying rows
                 # keep it as their ask (first-home-steps: save + where do i start) - so "i want
                 # to save for a house deposit, where do i start" matched a room here on "house"
                 # and was told to pick the clothes up off the floor. The subject is the money,
                 # and the money words are what stand this row down for it.
                 "deposit", "deposits", "house deposit", "mortgage", "down payment",
                 "save up for", "save for a house", "saving for a house", "save for a deposit",
                 "saving for a deposit", "house price", "stamp duty",
                 # and the buying itself, because "im 29 and want to buy a flat, where do i
                 # start" says the flat and no money word at all
                 "buy a flat", "buying a flat", "buy a house", "buying a house", "to buy a",
                 "first flat", "first home", "property", "houses for sale", "buy property",
                 # clearing a place out is the declutter card's line ("one room at a time, three
                 # bags on the floor"), and it is the better answer for a garage, a loft or a
                 # cupboard however the mess is worded
                 "clear out", "clearing out", "clear it out", "sort out", "sorting out",
                 "declutter", "decluttering", "get rid of", "throwing out", "throw out",
                 "skip", "car boot", "donate", "donation", "charity shop", "tip run",
                 # A house being moved out of is the move's question, not a room to tidy: "tips
                 # for moving house" was this row's answer ("pick it all up into one basket")
                 # because "house" is the room and "tips" is the ask, and the timeline with the
                 # van, the council and the boxes is what the person wanted. The words below are
                 # only ever said by a move, so a tidy-up line keeps the row.
                 "moving house", "moving home", "moving flat", "move house", "move home",
                 "move flat", "moving out", "house move", "home move", "moving next month",
                 "packing up", "packing the house", "pack the house", "unpacking",
                 "movers", "removals",
                 # a mess somebody else makes is a thing to say to them, not a cleaning job:
                 # "our flat is a tip because my flatmate never tidies up" wants the talking
                 # answer, and the plan for what to pick up first is no help with a person
                 "flatmate", "flatmates", "housemate", "housemates", "roommate", "roommates",
                 "my partner", "my husband", "my wife", "my boyfriend", "my girlfriend",
                 "my son", "my daughter", "my kids", "my children", "my teen", "my teenager",
                 "my mum", "my dad", "my brother", "my sister", "my in laws",
                 "never tidies", "never tidy", "wont tidy", "won't tidy", "doesnt tidy",
                 "doesn't tidy", "never cleans", "wont clean", "won't clean", "their mess",
                 "his mess", "her mess", "leaves it",
                 # a house move is a plan, not a tidying job: "we're moving house in about ten
                 # weeks and i dont know where to start" is "house" plus "dont know where to
                 # start", which is this row's whole key, and it answered a move with "start with
                 # what is on the floor". plans.move-house-plan has the timeline the person asked
                 # for, and `home.moving-pack` the boxes.
                 "moving house", "move house", "moving home", "move home", "moving flat",
                 "move flat", "house move", "moving out", "move out", "moving in with",
                 "removal", "removals", "removal van", "man with a van", "packing up",
                 # a line that asks what to say is the wording answer's, whatever it is about:
                 # "our flat is a tip because my flatmate never tidies up" then "what do i say
                 # to her" was read as the flat that is a tip and got the tidying plan
                 # and a line that leads with the state of the person has not asked about tidying:
                 # "the house is a mess and i cant cope" wants an ear, "i have no energy and the
                 # house is a mess" wants the tiredness answer
                 "cant cope", "can't cope", "cannot cope", "coping", "no energy", "no motivation",
                 "exhausted", "depressed", "feel down", "feeling down", "burnt out", "burned out",
                 "overwhelmed", "stressed", "anxious", "on my own with it", "give up",
                 # a kitchen or a bathroom being replaced is a building job, not a tidy-up: "where
                 # do i start with a kitchen renovation" and "we are having a new kitchen fitted
                 # where do i start" were both told to pick up what is on the floor, because a
                 # place word plus "where do i start" is this row's shape
                 "renovation", "renovating", "renovated", "refurb", "refurbs", "refurbishment",
                 "refurbishing", "fitted", "fitting", "re fitted", "install", "installing",
                 "installed", "installation", "extension", "extensions", "knock through",
                 "knocking through", "building work", "builder", "builders", "architect",
                 "quote", "quotes", "quoted", "contractor", "contractors", "new kitchen",
                 "new bathroom", "new boiler", "redesign", "ripping out", "rip out",
                 "what do i say", "what should i say", "what can i say", "how do i tell",
                 "how do i ask", "how should i tell", "how do i bring it up", "bring it up",
                 "say to her", "say to him", "say to them", "tell her", "tell him", "tell them",
                 "word it", "phrase it",
                 # A search for somewhere to live is not a room to tidy, and "flat" is one of
                 # the places above: "where do i start looking for a flat to rent" and "i need
                 # to find a house to buy where do i start" were told to pick the clothes up off
                 # the floor. Renting or buying a place is a search with its own first step
                 # (deposit, budget, agents), and the row that gives it already answers "i want
                 # to move out but i dont know where to start".
                 "looking for a flat", "looking for a house", "looking for a place",
                 "looking for somewhere", "find a flat", "find a house", "find a place",
                 "find somewhere", "flat to rent", "house to rent", "flat to buy",
                 "house to buy", "want to rent", "looking to rent",
                 "buy a house", "buy a flat", "buying a house", "buying a flat"),
          # "the kitchen needs a clean" and "how do i clean the kitchen" are the room routine's
          # and name no state word here, so this row does not see them at all.
          # A house that is a mess also scores on the music rows, because "house" is a genre, and
          # on the fence row while "where do i start" was a key of its own; a place plus the state
          # it is in is the more specific reading, so it takes the tie.
          bias=2),
    # "How do I clean the bathroom" is a whole room, not one fixture: the answer is the order to
    # work in and how often each part needs doing. Every single-fixture entry keeps its own line
    # (the bath, the toilet, the grout, the shower head), so this one steps aside for them.
    entry("bathroom-routine", (("bathroom", "bathrooms", "ensuite", "shower room", "whole bathroom",
                                "family bathroom"),
                               # and no bare "how": a bathroom is a room, so "how" in this key
                               # made every how-to in one a cleaning answer - "how do i drill a
                               # hole in a bathroom tile" was a ten-minute routine
                               ("clean", "cleaning", "cleaned", "often", "order", "first",
                                "best way", "properly", "weekly", "every week", "deep clean",
                                "routine", "quickly")),
          "Work top to bottom and dry before wet: dust the shelves and wipe the mirror first, then "
          "the sink, bath and shower, and the floor last so nothing drips on what is already done. "
          "Ten minutes once a week on the sink, loo and floor is enough; once a month do the boring "
          "parts, the grout, the shower head, the extractor fan and behind the toilet. Squeegee the "
          "shower and leave the window or fan on for ten minutes after a bath, because that is what "
          "keeps the cleaning small.",
          avoid=("bath", "toilet", "loo", "cistern", "grout", "shower head", "mould", "mold",

                 "mildew", "limescale", "mirror", "drain", "extractor", "fan", "towel", "mat",
                 "curtain", "soap scum", "sink", "steam", "stain", "smell",
                 # "how do i paint the bathroom" is the painting row's, and the bare "how"
                 # here was enough to tie with it and win on order.
                 "paint", "paints", "painting", "painted", "repaint", "repainting",
                 "emulsion", "undercoat", "primer", "gloss")),
    # The kitchen is a room too, and the same shape as the bathroom: the order to work in and how
    # often, with the oven, the fridge and the chopping board keeping their own answers.
    entry("kitchen-routine", (("kitchen", "kitchens", "whole kitchen", "galley kitchen"),
                              ("clean", "cleaning", "cleaned", "often", "order", "first",
                               "best way", "properly", "weekly", "every week", "deep clean",
                               "routine", "quickly", "how",
                               # "my kitchen is greasy" is the same ask with no verb in it:
                               # the grease is the thing to be cleaned, so it is the second
                               # word of the key, not a subject of its own. Grease on a wall
                               # or a cupboard still reaches those cards, which are in the
                               # avoid list below.
                               "grease", "greasy", "degrease", "degreasing")),
                    _KITCHEN_ORDER,
          avoid=("oven", "fridge", "freezer", "hob", "cooker", "microwave", "kettle", "drain",
                 "smell", "smells", "smelly", "stink", "extractor", "bin", "dishwasher",
                 # a greasy kitchen is this card's own job: "grease" sat in this list and the
                 # spelling check read "greasy" as one slip away from it, so "how do i clean a
                 # greasy kitchen" and "my kitchen is greasy" were vetoed here and reached
                 # nothing at all. Grease on a wall is the wall card's line, so the wall is
                 # what this list keeps.
                 "wall", "walls",
                 # a kitchen being planned, fitted or replaced is a building job and not a
                 # wiping one: "how long does a kitchen take to fit" got the order to work in
                 "renovation", "renovating", "refurb", "refit", "fitted", "fitting", "install",
                 "installing", "installed",
                 # the same stand-down said the way people say it: "my kitchen is being redone in
                 # march what should i pick first" was the order to wipe a kitchen in, because
                 # being redone is a building job and none of the words above spell it.
                 "redone", "redo", "redoing", "done up", "doing up", "gutted", "being gutted",
                 "replaced", "replacing", "replacement", "getting a new kitchen",
                 "having a new kitchen", "having work done", "getting work done",
                 "work starts", "work starting", "new kitchen in",
                 # bare "how long" stood this row aside for any kitchen duration, including
                 # "how long does it take to clean the kitchen", which is the routine's own
                 # question. What the row must not take is the fitting: "how long does a kitchen
                 # take to fit" is the renovation card's, and these phrases keep it there.
                 "how long does a kitchen take", "how long to fit", "how long does it take to fit",
                 "how long does fitting take", "take to fit", "plan", "planning",
                 "design", "layout", "extension", "builder", "builders", "quote", "quotes",
                 "cupboard", "cupboards", "chopping board", "sink", "mould", "mold", "limescale",
                 # "how do i fix a leaking tap in the kitchen" is a repair, and the word
                 # "kitchen" plus "how" was enough for this entry to claim it.
                 "drip", "drips", "dripping", "dripped", "leak", "leaks", "leaking", "leaky",
                 # and "how do i paint a kitchen" is a decorating job, not the order to clean
                 # it in: the same four words stand the bathroom's routine down
                 "paint", "paints", "painting", "painted", "repaint", "repainting", "emulsion",
                 "undercoat", "primer", "gloss",
                 # a kitchen being packed up is a move, not a clean: "how do i pack the kitchen"
                 # got the order to wipe the surfaces in, because the room plus the bare "how"
                 # is all this row needs. The pack words stand it down for the packing card,
                 # and cleaning a kitchen that is being packed still reaches it.
                 "pack", "packs", "packing", "packed", "unpack", "unpacking", "boxes", "box",
                 "moving house", "moving out", "move house", "removal", "removals",
                 "washer",
                 # a pest in the kitchen is the cupboard answer, not the room routine: the
                 # room card has no moth in it, and "kitchen" plus "how" was enough on its own
                 "moth", "moths", "pantry moth", "pantry moths", "food moth", "food moths",
                 "larder moth", "weevil", "weevils", "grain beetle", "beetle", "beetles",
                 "infestation", "infested", "pest", "pests", "mice", "mouse", "ants", "ant",
                 "cockroach", "cockroaches", "silverfish",
                 # "how do i get a job in a school kitchen" is a job in a kitchen, not the order
                 # to clean one: the room's own "kitchen" plus "how" was enough for this card
                 "job", "jobs", "apply", "applying", "vacancy", "vacancies", "hiring",
                 "employer", "recruit", "recruiting")),
    # "How do I clean the sink" is about the bowl, the tap and the overflow, and about the one thing
    # that blocks a drain. A hob has its own two materials to be careful of.
    entry("sink-clean", (("sink", "kitchen sink", "bathroom sink", "hand basin", "handbasin",
                          "wash basin", "basin", "basins", "stainless steel sink", "ceramic sink",
                          "plug hole", "plughole", "overflow", "taps", "tap"),
                         ("clean", "cleaning", "smell", "smells", "smelly", "stinks", "stink",
                          "stain", "stains", "how", "often", "bicarbonate", "scrub",
                          # The bowl is also the thing people want polished: "how do i polish a
                          # stainless steel sink" and "how do i make my sink shine" were the
                          # face-care card, which thought "shine" meant oil on skin.
                          "polish", "polishing", "shine", "shiny", "shines", "streak", "streaks",
                          "smear", "smears", "dull", "dulled", "scratched", "scratch",
                          "sparkling", "gleaming", "stainless", "steel", "ceramic", "why",
                          "odour", "odor", "get rid of", "keep clean")),
          # The cleaning comes first, because it is what was asked: the bowl, then the shine, then
          # the drain. It used to open on the smell, which answered "how do i clean a sink" with
          # the tap and the overflow and nothing about the bowl.
          "Wipe round the bowl and give the tap and the overflow a wipe after every wash-up, "
          "because that last bit is where a sink starts to smell, and anything left to dry on "
          "takes ten times the scrubbing. Once a week put bicarbonate of soda round the bowl, add "
          "a splash of white vinegar, leave it 10 minutes and rinse: that lifts the film without "
          "scuffing stainless steel, and a drop of baby oil on a cloth afterwards buffs a "
          "stainless or ceramic bowl back to a shine and keeps water marks off. Never pour fat "
          "down it, but let it cool into a jar, and the drain stays clear.",
          # A line that says the sink will not drain is a blocked drain, and the plunger answer is
          # the one that helps; "unblock" is not a cleaning word.
          avoid=(
                 # a cake that sinks is not a sink: "how do i keep a cake from sinking" reached
                 # this row on "sinking" read as "sink" plus "how", and got the bicarbonate
                 "cake", "cakes", "sponge", "batter", "souffle", "brownie", "bake", "baking",
                 "oven", "tin", "loaf", "bread", "risen", "rise", "dough", "pastry",
                 "yorkshire", "pudding", "choux", "meringue",
                 "blocked", "blockage", "blocking", "blocking up", "unblock", "unblocking",
                 "unblocked", "plunger", "backing up", "backed up", "slow", "draining",
                 "plumber",
                 # and the same fault under its other name: a sink that clogs is a blockage, and
                 # "how do i unclog a sink" was getting the wipe-the-bowl answer
                 "clog", "clogs", "clogged", "clogging", "unclog", "unclogging", "unclogged",
                 # scaling is its own answer in home.py, which knows about vinegar and citric acid
                 "limescale", "descale", "scale", "scaled", "furred",
                 # "how do i remove hard water stains from a tap" was told to rinse the basin,
                 # because "stain" is a cleaning word and "hard water" was not on this list
                 "hard water", "hard water stain", "hard water stains", "chalky", "white marks",
                 "limed up", "calcium",
                 # a tap that drips or leaks is a repair in home.py ("change the washer" is the
                 # answer, not a scrub); "how do i fix a dripping tap" was getting this reply
                 "drip", "drips", "dripping", "dripped", "leak", "leaks", "leaking", "leaky",
                 "washer",
                 # hair in the trap is a blocked drain (home.py pulls it out and says how to stop
                 # it coming back); "how do i get hair out of the plughole" was getting the
                 # wipe-the-tap answer because "how" and "plughole" were enough
                 "hair", "hairs",
                 # a tap is also the plumbing behind a shower or a boiler, and "how do i stop my
                 # shower going cold when someone uses the tap" is that question, not a scrub:
                 # the water side of a tap is home.py's, and this row is only the cleaning.
                 "shower", "showers", "cold", "hot water", "pressure", "boiler", "immersion",
                 "valve", "valves", "mixer", "thermostat", "radiator", "radiators", "toilet",
                 "stopcock", "cylinder", "pump")),
    # "how long does it take to clean the house" and "...to tidy the house" were answered "Open
    # a Lifetime ISA and put a monthly standing order into it", because "house" is the buying row's
    # subject and "how long" one of its asks. The rooms each have a routine and a time; the whole
    # house had no row at all, and the duration ask is the one shape that names it. The phrase in
    # the key keeps this row to a duration: "clean the house" on its own is the mess card's and
    # the rooms' own question.
    entry("whole-house-clean",
          (("how long", "how many hours", "how much time", "how long does", "how long will",
            "how long should", "how long to", "how much of the day"),
           ("clean the house", "cleaning the house", "clean my house", "clean our house",
            "clean the flat", "cleaning my house", "tidy the house", "tidying the house",
            "tidy my house", "tidy up the house", "whole house", "deep clean",
            "deep cleaning", "spring clean", "clean a house", "clean a flat",
            "clean the place", "clean my flat", "cleaning my flat", "sort the house",
            "sort out the house", "get the house clean", "get the house tidy")),
          "A whole house done properly is most of a day for one person: about four hours for a "
          "two- or three-bed that has been kept on top of, and the better part of a day if it has "
          "not had a deep clean in a year. Work top to bottom and room by room, with the floors "
          "and the bathroom last, so nothing gets done twice; the kitchen takes longest because "
          "of the grease. If it is only a tidy before people come, an hour and a half in the rooms "
          "they will actually sit in is enough, and the doors on the rest can stay shut.",
          # a room, a carpet and a machine each have their own card and their own time; a cleaner
          # you pay for is a price question; a job on the house is a building job
          avoid=("oven", "fridge", "freezer", "bathroom", "kitchen", "carpet", "carpets",
                 "car", "windows", "window", "garden", "hoover", "vacuum", "sofa",
                 "curtain", "curtains", "mattress", "price", "cost", "costs", "charge",
                 "builder", "builders", "renovation", "extension", "painting", "paint",
                 "move out", "moving out", "end of tenancy", "deposit", "damp", "mould")),
    # A drain that is slow or blocked is home.py's plunger and the bleach question is the
    # bleach card, so what is left is the ordinary job: keeping a drain that runs fine from
    # turning into one that smells. It was a shrug on main.
    # A living room, a bedroom, a hall and a whole house are one question - what order do I do
    # this in - and on main cef460d all of them were a punt: "how do i clean my living room",
    # "how do i clean a bedroom", "how do i clean a hallway", "how do i clean a whole house",
    # "how do i clean the house fast", "how do i clean a whole flat in a day", "what order should
    # i clean a house in" and "how do i deep clean a room" were the search hedge. The kitchen and
    # the bathroom already had their own routines, and every single fixture keeps its own row.
    entry("cleaning-a-room-and-a-house",
          (("living room", "lounge", "front room", "sitting room", "bedroom", "bedrooms",
            "spare room", "box room", "study", "dining room", "hall", "hallway", "hallways",
            "landing", "whole house", "whole flat", "whole home", "the whole house",
            "every room", "all the rooms", "the rooms", "a room", "rooms", "house", "flat",
            # bare "home" is in half the lines people type, and "how do i compost at home" was
            # this row's answer because of it: the house, the flat and the rooms are the
            # subjects, and "home" only counts when the line says whose.
            "my home", "whole home", "in my home", "at home to stay", "housework"),
           ("clean", "cleaning", "cleaned", "tidy", "tidy up", "tidying", "deep clean",
            "deep cleaning", "spring clean", "hoover", "hoovering", "vacuum", "dust", "dusting",
            "what order", "order", "where do i start", "where to start", "start", "first",
            "next", "fast", "quickly", "quick", "in a day", "properly", "best way", "routine",
            "checklist")),
          "Twenty minutes a room on a timer, top to bottom, floor last: a bin bag for the rubbish "
          "and a basket for everything that lives somewhere else, then dust from the ceiling down "
          "(corners, the tops of pictures, lamp shades), then wipe the marks, then hoover. For a "
          "whole house, do the rooms visitors see in the order they see them - hall, loo, "
          "kitchen, sitting room - and shut the doors on the rest. How often: the kitchen and the "
          "bathroom twice a week for the loo, the basin and the worktops, bedding weekly, the "
          "rest when it looks like it needs it, and a deep clean - skirting boards, inside the "
          "windows, behind and under the furniture - once a season.",
          # the kitchen and the bathroom have routines of their own, and every single fixture,
          # appliance and soft furnishing is a different answer: the room word alone is not
          # enough for any of those.
          avoid=("kitchen", "kitchens", "bathroom", "bathrooms", "toilet", "loo", "bath",
                 "shower", "sink", "oven", "fridge", "freezer", "washing machine", "dishwasher",
                 "microwave", "kettle", "carpet", "carpets", "rug", "rugs", "mattress", "sofa",
                 "curtain", "curtains", "blind", "blinds", "window", "windows", "grout",
                 "skirting", "cupboard", "cupboards", "wardrobe", "garage", "garden", "car",
                 # the outside of a house is its own set of jobs, and a follow-up inherits the
                 # words of the line before it: "how do i clean the gutters on my house" then
                 # "and how often" reached this row through the context of the first line
                 "gutter", "gutters", "guttering", "downpipe", "downpipes", "roof", "roofs",
                 "brick", "bricks", "patio", "decking", "driveway", "drive", "paving",
                 "fence", "fences", "shed", "conservatory", "moss", "weeds", "weeding",
                 # a compost heap, a wormery and a recycling bin are "at home" jobs too, and a
                 # clean house is not what their lines ask for
                 "compost", "composting", "compost bin", "wormery", "food waste", "recycling",
                 "recycle", "allotment", "rubbish collection", "bin day", "water butt",
                 "drainpipe", "outside", "outdoor", "path", "footpath", "window cleaner",
                 # a floor has its own answer (sweep, then mop, and the water changed), and
                 # "how do i clean a hall floor" was that card on main and the room order here
                 "floor", "floors", "mop", "mopping", "mop the", "sweep", "sweeping",
                 "stairs", "stair carpet", "wall", "walls", "ceiling", "ceilings",
                 "bbq", "barbecue", "bin", "bins", "grease", "greasy", "mould", "mold",
                 "mildew", "limescale", "drain", "drains",
                 # a house being painted, fitted, sold, bought, moved into or rented is another
                 # question: "how do i clean my house" is this row, "how do i sell my house" is
                 # not, and "how do i clean my house after builders" is a dust job of its own.
                 "paint", "paints", "painting", "painted", "repaint", "decorate", "decorating",
                 "decorated", "renovation", "renovating", "refurb", "refit", "install",
                 "installing", "sell", "selling", "buy", "buying", "rent", "renting", "landlord",
                 "deposit", "mortgage", "move", "moving", "moved in", "builders", "builder",
                 "flood", "flooded", "fire", "smoke damage",
                 # guests are a hosting question (what to have ready, not the order to clean in)
                 "guests", "guest", "visitors", "visitor", "coming to stay", "family coming",
                 # a bug or a sick pet is a disinfecting job, not a tidy one
                 "bug", "norovirus", "vomiting", "sick", "diarrhoea", "diarrhea", "covid",
                 "dog", "cat", "puppy", "kitten", "pet", "pets"),
          # A follow-up arrives as its own line with the room named in it and nothing else -
          # "how often should i clean my house" then "and the bathroom" - and the avoid list is
          # not what a follow-up is read against: the guard is. The room that has a routine of
          # its own keeps its own answer, and a bare "and the bathroom" is the bathroom's.
          guard=_not_a_room_with_its_own_card),
    entry("drain-clean", (("drain", "drains", "shower drain", "sink drain", "bath drain",
                           "waste pipe", "waste pipes"),
                          ("clean", "cleaning", "freshen",
                           "gunk", "slime", "scum", "often", "once a week",
                           # A bare "how" here was a second key word for any line with "drain" in
                           # it, which is how "how do i drain broccoli" and "how do i drain
                           # chickpeas" got the kettle down the waste pipe. The line has to carry
                           # the cleaning as well as the drain, so the how is spelled out.
                           "how do i clean", "how to clean", "how do i freshen",
                           "how to freshen", "how often", "how do i keep", "how to keep",
                           "look after", "keep on top of")),
          "Once a week pour a full kettle of boiling water down it, which melts the fat and soap "
          "that hold the smell, and once a month follow with half a mug of bicarbonate of soda and "
          "a mug of white vinegar, leave it 15 minutes and flush it through with hot water. Hair "
          "comes out with a bent wire or the trap under the sink, and nothing you pour down will "
          "shift it.",
          avoid=("bleach", "chlorine", "caustic", "acid", "blocked", "blockage", "blocking",
                 "clog", "clogs", "clogged", "clogging", "unclog", "unclogging", "unclogged",
                 "unblock", "unblocking", "plunger", "backing up", "backed up", "slow",
                 # "draining" cannot go here: the matcher takes a word for its stem, so an
                 # avoid of "draining" also stands this row down for the plain word "drain".
                 "drains slowly", "plumber", "washing machine", "dishwasher", "toilet",
                 "gutter", "downpipe",
                 # a battery, a bank account and a pond all drain, and none of them is a drain:
                 # "my laptop battery drains fast" reached this row on "drains" plus "how"
                 "battery", "batteries", "phone", "laptop", "tablet", "charger", "car", "van",
                 "boiler", "radiator", "account", "money", "savings", "bank", "energy", "power",
                 "pond", "pool", "paddling", "fuel", "tank",
                 # and the drain outside the house is the gully card's, not this one: "how do i
                 # clean a drain outside" was the leaves-and-silt answer before this row existed
                 "outside", "outdoors", "outdoor", "gully", "gulley", "manhole", "drain cover",
                 "yard", "driveway", "patio", "pavement", "garden drain", "outside drain",
                 # "how" is in the key above as the bare way-ask, so a price asked about a
                 # drain came here: "how much does a drain company charge" was answered with
                 # the weekly kettle of boiling water. A price is the cost table's question.
                 "how much", "how much does", "how much is", "cost", "costs", "price",
                 "prices", "charge", "charges", "quote", "callout", "call out", "company",
                 "pasta", "spaghetti", "noodles", "rice", "potato", "potatoes", "veg",
                 "vegetables", "colander", "cooking", "cook", "sauce", "tin", "tinned", "bean",
                 "beans", "spinach", "food", "boil", "boiling",
                 # a tin being drained is food, not a plughole: "how do i drain a can of tuna"
                 # was told to pour a kettle of boiling water down the drain
                 "can of", "tin of", "tuna", "sweetcorn", "sweet corn",
                 "chopped tomatoes", "tinned tomatoes", "coconut milk",
                 "friend", "friends", "sister",
                 "brother", "mum", "mom", "dad", "partner", "husband", "wife", "boyfriend",
                 "girlfriend", "family", "flatmate", "housemate", "colleague", "coworker",
                 "someone", "person", "people", "relative", "mother in law", "relationship",
                 # and a drain that smells has `drain-blocked`: the trap first, then the kettle,
                 # which is more on the point than the weekly maintenance card
                 "smell", "smells", "smelling", "smelly", "stink", "stinks", "stinking",
                 "whiff", "reek", "odour", "odor",
                 # hair in the trap is the blocked-drain card too, and it is the sharper answer:
                 # "how do i clean hair out of the drain" wants the wire, not the weekly kettle
                 "hair", "hairs")),
    # Silverfish are the one household pest that really is about the room rather than the food:
    # they eat paper and glue where it is damp. Every line about getting rid of them was a shrug.
    entry("silverfish", (("silverfish", "silver fish", "firebrat", "firebrats", "bristletail",
                          "bristletails"),
                         ("get rid", "getting rid", "rid of", "kill", "killing", "stop", "how",
                          "in my", "bathroom", "kitchen", "cupboard", "wardrobe", "everywhere")),
          "Silverfish eat the starch in paper, card, glue and cotton, and they only settle in a "
          "room that is damp, so the damp is the thing to fix: ventilate the bathroom, mend the "
          "leak, and clear the piles of cardboard and old paper they are living in. They are "
          "harmless otherwise - they do not bite and they do not spread anything - and a "
          "dehumidifier does more than any spray.",
          avoid=("goldfish", "fish tank", "pond", "aquarium", "silver", "silver jewellery"), report=True),
    entry("hob-clean", (("hob", "hobs", "cooker top", "stove top", "stovetop", "burners",
                         "hotplate", "ceramic hob", "induction hob",
                         # A bare "rings" also folds the verb: "how do i stop my phone ringing at
                         # night" and "my mum keeps ringing me at work" were both answered with
                         # how to wipe a hob clean. A ring of a hob is said with the hob, so the
                         # ring is keyed where it is instead of on its own.
                         "hob ring", "hob rings", "rings on", "ring on", "rings off", "ring off",
                         "cooker ring", "cooker rings", "burner ring", "burner rings",
                         "stove ring", "stove rings"),
                        ("clean", "cleaning", "burnt", "burned", "stain", "stains", "scrub",
                         "shiny", "how", "grease", "marks")),
          "Wipe a warm hob with hot soapy water and a cloth, never a hot one and never by pouring "
          "water on it. Burnt-on rings on a gas or solid plate come off with a paste of bicarbonate "
          "of soda and water left 15 minutes, then scrubbed. A ceramic or induction top wants a "
          "scraper for burnt-on sugar and a cream cleaner, with no scouring pad, or the shine goes "
          "for good.",
          avoid=("oven", "grill", "microwave", "fridge", "kettle",
                 # a phone that rings quietly and a finger ring are not a hob
                 "phone", "iphone", "android", "louder", "volume", "speaker", "doorbell",
                 # a wood burner has a fire in it, not a hob to wipe: "how did we start the
                 # fire in the wood burner" was getting the hob answer from "burner" + "how".
                 "wood burner", "log burner", "wood", "log", "fire", "fireplace",
                 "solid fuel", "chimney",
                 # "how do i make stovetop popcorn" is a popcorn question: "stovetop" is where it
                 # is cooked, not what is being cleaned.
                 "popcorn", "pop corn", "popping corn",
                 # "rings" in the key also caught a ring you wear: "how much should i spend on
                 # an engagement ring" was answered with how to wipe a hob clean, and "how do i
                 # get a ring off my finger" got the same. A ring on a hand is not a burner.
                 "engagement", "wedding", "ring size", "resize", "diamond", "jewellery",
                 "jewelry", "finger", "fingers", "hand", "hands", "knuckle", "toe",
                 "wedding ring", "engagement ring", "piercing", "piercings", "nose", "ear",
                 "ears", "earring", "earrings", "lip", "eyebrow", "belly", "navel",
                 "tongue", "ring stuck", "stuck", "band of gold",
                 # "rings" is the one word the hob and a jeweller share, and the money words
                 # send the price questions to the jewellery budget: "how much should we spend
                 # on rings" was this card. The hob lines say "on my cooker" or "the rings".
                 "spend", "cost", "costs", "price", "much", "worth", "value")),
    # A pest in the food names the pest and not the cupboard: "weevils in my flour", "beetles
    # in the flour", "how do i get rid of weevils" named no cupboard word at all, so they
    # reached nothing and got a punt, while "moths in my pantry" was answered because the
    # pantry is a cupboard word. The row below is keyed on the pest, so the food or the asking
    # is the second part and the pest alone is not enough to reach here. The answer is the
    # same card the cupboard row gives a moth question, so a line that two rows can read still
    # gets one answer.
    entry("pantry-pests",
          (("weevil", "weevils", "beetle", "beetles", "moth", "moths", "pantry moth",
            "pantry moths", "food moth", "food moths", "larder moth", "larder moths",
            "kitchen moth", "kitchen moths",
            # "What are the little things in my flour" is the same pest as a weevil, and people
            # say it with a plain word: "flour mites", "bugs in my porridge oats" and "little
            # worms in the cereal" all reached nothing. The plain words are this row's only
            # when the second part says a dry good is where they are, and the other senses -
            # a dog's worms, dust mites in a bed, a bug in a program - are held out below.
            "mite", "mites", "bug", "bugs", "worm", "worms", "grub", "grubs",
            # The person who does not know the pest's name does not use one at all: "what are
            # the little things in my flour", "tiny black specks in my flour" and "black bits in
            # my flour" say a thing, a speck or a bit, and no pest word at all. The phrases are
            # keyed, not the bare nouns, so "how do i store things in my cupboard" and "black
            # bits on my ceiling" keep their own answers.
            "little things", "tiny things", "small things", "little things in", "tiny things in",
            "small things in", "specks", "speck", "black specks", "brown specks", "tiny specks",
            "little specks", "black bits", "brown bits", "little bits", "tiny bits", "bits in",
            "brown things", "black things", "white things", "little brown things",
            # The pest that is not a beetle: "maggots in my cupboard" and "maggots in the rice"
            # name the pest the larder card already answers and reached nothing, because a
            # maggot was only a cupboard word and never a key word.
            "maggot", "maggots",
            # And the person who never names the pest at all, only what it is doing: "something
            # is eating my porridge oats", "something has been eating the flour". The doing is
            # the pest here, so it is keyed beside the names, and a dry good in the second part
            # is still what makes the line a larder question.
            "eating my", "eating the", "eating our", "eaten my", "eaten the", "eaten our",
            "eating everything", "eating through", "something is eating", "something eating",
            "something has been eating"),
           ("flour", "rice", "oats", "cereal", "cereals", "pasta", "porridge", "couscous",
            "dried fruit", "raisins", "sultanas", "nuts", "grain", "grains", "packet",
            "packets", "dry goods", "cupboard", "cupboards", "pantry", "larder", "kitchen",
            "shelf", "shelves", "spice", "spices", "sugar", "biscuits", "bread",
            "get rid", "rid", "stop", "stopping", "kill", "killing", "infestation",
            # "keeping" is not here: a row that keys it is read as a shelf-life row, and the
            # lookup stands a shelf-life row down for a fault verb, so "i keep getting tiny bugs
            # in my flour" - the shape the whole row is for - was the one line it could not
            # answer. "stored" and "storage" keep the storing lines.
            "infested", "everywhere", "food", "stored", "storage")),
          CUPBOARD_MOTHS,
          # a moth in a wardrobe is wool, a beetle in a border is a garden, and a maggot in a bin
          # is the bin: the card below wants opened flour and a shelf to wipe
          avoid=("wardrobe", "wardrobes", "clothes", "clothing", "wool", "woollen", "jumper",
                 "carpet", "garden", "border", "lawn", "plant", "plants", "shrub", "tree",
                 "bird seed", "bird food", "bird feeder", "bin", "bins", "dustbin",
                 "compost", "outside", "shed", "garage", "bathroom", "bedroom", "torch",
                 # "eating my" is a garden verb too: "how do i stop slugs eating my seedlings",
                 # "what is eating my lettuce". The thing being eaten is a crop, and the answer
                 # there is the night patrol, not the larder. The crop nouns and the growers'
                 # pests are held out here so the phrase only reads a dry good.
                 "seedling", "seedlings", "lettuce", "cabbage", "carrots", "tomatoes",
                 "strawberries", "vegetables", "veg", "crop", "crops", "allotment",
                 "greenhouse", "flower", "flowers", "hedge", "grass", "slug", "slugs",
                 "snail", "snails", "caterpillar", "caterpillars", "aphid", "aphids",
                 "rabbit", "rabbits", "deer", "squirrel", "squirrels", "fox", "foxes",
                 "lamp", "light", "fly", "flies", "flea", "fleas", "bed bug", "bed bugs",
                 "ant", "ants", "wasp", "wasps", "mousetrap", "mouse", "mice", "rat",
                 "rats", "trap", "spray", "pesticide",
                 # the plain words above are said of other things, and each of those has its own
                 # answer: a dog's or a cat's worms are the vet's, dust mites in a bed are the
                 # bedding and allergy rows, a bug going round is an illness and a bug in a
                 # program is a computer's. Not "worming" or "wormed" here, though: those share
                 # their stem with the key word "worm", and a held-out word that the line's own
                 # key matches stands the whole row down.
                 "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens", "pet",
                 "pets", "vet", "poo", "poop",
                 "vomit", "sick", "tummy", "tummy bug", "stomach", "stomach bug", "bug going",
                 "dust", "dust mite", "dust mites", "dustmite", "dustmites", "bed", "beds",
                 "bedding", "mattress", "mattresses", "pillow", "pillows", "duvet", "sheet",
                 "sheets", "sofa", "cushion", "cushions", "allergy", "allergies", "allergic",
                 "itchy", "itching", "rash", "bites", "bitten", "chicken", "chickens", "hens",
                 "pigeon", "pigeons", "parrot", "software", "computer", "phone", "website",
                 "code", "program", "fish tank", "pond",
                 # a thing, a speck or a bit somewhere else in the house is not the larder: the
                 # ceiling, the wall and the floor have their own answers
                 "ceiling", "ceilings", "wall", "walls", "floor", "floors", "bath", "shower",
                 "toilet", "life", "living", "world", "weather", "clothes"),
          bias=-1),
    entry("cupboards-clean", (("cupboard", "cupboards", "kitchen cupboards", "kitchen cabinets",
                               "larder", "pantry", "drawers",
                               # "how do i get rid of moths in my kitchen" named the room rather
                               # than the cupboard, and the clothes-moth answer (a wardrobe and
                               # cedar blocks) is no use against pantry moths. A phrase key with
                               # a stopword in it ("moths in my kitchen") never matches, because
                               # the stopwords are dropped before scoring, so the moth words go
                               # in the second part and the room in a third of its own.
                               "kitchen moths", "pantry moths", "larder moths", "food moths",
                               # the matcher wants the first part said, and "moths in my
                               # kitchen" names the pest without the phrase, so the bare pest
                               # words go here too: the wardrobe and the clothes are avoided below
                               "moth", "moths", "weevils", "weevil", "beetles", "beetle"),
                              ("clean", "cleaning", "smell", "smells", "musty", "sticky",
                               "grease", "often", "inside", "moths", "moth", "weevils",
                               "weevil", "beetles",
                               # The jobs below were carried by the bare "how" and nothing else,
                               # so dropping it alone lost "how do i sort out my cupboards",
                               # "how do i empty my cupboards" and "how do i wipe down my
                               # cupboards" to the shrug. Their verb is the word that says the
                               # line is about the cupboards, so it goes in here.
                               "organise", "organising", "organised", "tidy", "tidying",
                               "sort", "sort out", "sorting", "sorting out", "clear", "clear out",
                               "clearing", "empty", "emptying", "wipe", "wipe down", "wiping",
                               "wash", "washing", "scrub", "scrubbing", "degrease",
                               # A cupboard that is full, cluttered or a mess is this row's line
                               # whether or not the person asks a question: "my cupboards are a
                               # mess", "my cupboards are full of stuff" and "the cupboards are
                               # cluttered" are the clear-out, and they used to get the
                               # composer's echo back. These words say what state the cupboard
                               # is in and say nothing about cooking, so they do not pull a
                               # recipe in the way the room and the food nouns did.
                               "full", "full of", "full up", "packed", "overflowing",
                               "mess", "messy", "clutter", "cluttered", "junk",
                               "too much stuff", "stuffed"),
                              # no bare "how", for the reason the toilet row gives: the question
                              # word alone was a part, so "how much rice per person" and "how do i
                              # stop rice going mushy" were cupboard clear-outs off the word rice
                              ("kitchen", "cupboard", "cupboards", "pantry", "larder", "food",
                               "flour", "rice", "oats", "cereal", "pasta", "dried fruit",
                               "packet", "packets", "dry goods")),
          _cupboards,
          # "how" plus a food word from the third part was enough to match, so a line about
          # keeping the food was answered with how to empty a cupboard. With the pasta row
          # standing down, "how do i keep pasta for tomorrow" fell here, which is worse than
          # the shelf-life card it had. Phrases, not bare "keep", because "how do i keep my
          # cupboards clean" is this row's own line. The sticking words are the other half:
          # "how do i keep pasta from sticking" is a pan question with "pasta" in part three.
          # The room is not the cupboard. "kitchen" in the third part let a bare "clean" + "often"
          # reach the minimum score on its own, so "how often should i clean the kitchen" and
          # "how often should i clean my kitchen floor" were answered with how to wipe a shelf -
          # and so was "how do i pick tomatoes when they are ripe", on "pick" + "ripe" against
          # nothing. The row answers a cupboard, a shelf, a drawer or the pests and the dry goods
          # that live in one, so it asks for one of those.
          # no dry-goods nouns in the ask: a word one letter from one is read as a slip of it,
          # and "ripe" is one letter from "rice", so "how do i pick tomatoes when they are ripe"
          # came back once more. The pests and the containers carry the row on their own.
          ask=("cupboard", "cupboards", "cabinet", "cabinets", "shelf", "shelves", "drawer",
               "drawers", "larder", "pantry", "moth", "moths", "weevil", "weevils", "beetle",
               "beetles", "dry goods", "store cupboard", "food cupboard"),
          avoid=("oven", "fridge", "freezer", "wardrobe", "clothes", "mould", "damp",
                 "for tomorrow", "until tomorrow", "till tomorrow", "for the next day",
                 "next day", "leftovers", "leftover", "left over", "reheat", "reheating",
                 "overnight", "tomorrow",
                 "use up", "keep it", "keep the rest", "keep them", "still ok", "still good",
                 "shelf life", "use by", "out of date",
                 "stick", "sticks", "sticking", "stuck", "clump", "clumps", "clumping",
                 "from sticking", "sticking together",
                 # "how do i paint kitchen cupboards" is a decorating question: "cupboards"
                 # plus "how" was worth four points here, and the answer it wanted was a
                 # brush, not a cloth.
                 "paint", "painting", "painted", "repaint",
                 # "how do i keep rice from sticking" and "how do i stop rice going mushy"
                 # are pan questions with "rice" in the third part, so the phrases that say
                 # which they are go here. "sticky" alone is a cupboard shelf that needs a
                 # wipe, so only the rice phrases carry it.
                 "glutinous", "sushi rice", "rice is sticky", "rice came out sticky",
                 "rice come out sticky", "rice goes sticky", "my rice is sticky",
                 "sticky rice", "rice sticks",
                 # A shelf-life question is the same shape again: "how long does cereal keep"
                 # and "how long do dried fruit keep" were emptying a cupboard, because the
                 # food in the third part plus the bare "how" was enough to match.
                 "how long", "store", "stored", "storing", "storage", "last", "lasts",
                 "gone off", "goes off", "freeze", "frozen"
                 # "kitchen" is a room word, not a cupboard word, so a line that says the kitchen
                 # and a cleaning verb but nothing about where the food lives is not this entry:
                 # "the drain smells in the kitchen" got the cupboard answer, and so did a pair of
                 # scissors.
                 "drain", "drains", "plughole", "plug hole", "sink", "sinks", "shower", "bath",
                 "toilet", "scissors", "sharpen", "sharpening", "blunt", "knife", "knives",
                 "floor", "floorboards", "window", "windows", "carpet", "carpets")),
    # A mirror fogs because the glass is colder than the air. The film kills the droplets; more
    # ventilation only moves the problem to the rest of the room.
    # What a steam cleaner is for is a different question from whether to buy one, and the
    # "worth it" row in shopping.py answers the buying. Three everyday lines reached nothing:
    # "will a steam cleaner help with the grout", "does a steam cleaner kill germs" and "how do
    # i clean a steam cleaner", and "can i use a steam cleaner on laminate" got a search hedge
    # when the machine's own row says plainly to skip laminate.
    entry("steam-cleaner",
          (("steam cleaner", "steam cleaners", "steam mop", "steam mops", "steam steamer",
            "hard floor cleaner"),
           ("use", "using", "kills", "kill", "germs", "bacteria", "sanitise", "sanitize",
            "disinfect", "steam", "grout", "tile", "tiles", "laminate", "wood", "floor",
            "floors", "carpet", "carpets", "shower", "bathroom", "oven", "hob", "grill",
            "clean", "cleaning", "it", "clean it", "descale", "descaling", "water",
            "help", "good for", "use it on", "safe on", "what can i use", "worth using")),
          _steam_cleaner,
          # buying one, a garment steamer and a food steamer are other questions
          avoid=("worth", "buy", "buying", "bought", "which", "best", "recommend", "how much",
                 "cost", "price", "cheap", "deal", "sale",
                 "iron", "ironing", "shirt", "shirts", "suit", "dress", "curtain", "clothes",
                 "garment", "face", "facial", "skin", "rice", "vegetable", "dumpling", "bao",
                 "wallpaper", "strip", "stripping", "engine", "car", "cars", "mould", "mold",
                 # "is a steam cleaner any good" is the buying question and the worth-it row
                 # answers it; the surface or the germ word is what makes a line this row's
                 "any good", "good enough", "any cop", "good buy", "should i get"),
          # "will a steam cleaner help with the grout" reaches the worth-it row four rank points
          # further, on the machine's name plus its "help": the surface in the line is this row's
          # signal, so five points of bias - the most any row carries - put it in front. A wider
          # key would not, and holding the worth-it words out of appliance-worth would take the
          # buying answer off every other machine.
          bias=5),
    entry("mirror-steam", (("mirror", "mirrors", "bathroom mirror", "shower screen", "car mirror"),
                           ("steam", "steams", "steamed", "steaming", "steamy", "fog", "foggy",
                            "fogged", "fogging", "misted", "mist", "mists", "condensation")),
          "Rub a drop of washing-up liquid or shaving foam over the glass and buff it off with a dry "
          "cloth: the thin film breaks the water into a sheet instead of droplets, and it lasts a "
          "week or two. The same trick works on a car mirror and the inside of a shower screen. "
          "Squeegeeing is what stops the water marks in the meantime."),
    entry("toilet-clean", (("toilet", "loo", "cistern"),
                            # no bare "how": the question word alone made "how do i toilet train a
                            # puppy" a cleaning line, and every real ask here has a cleaning word
                            ("clean", "cleaning", "ring", "limescale", "smell", "stain", "scrub",
                             "bleach", "disinfect")),
          "Put cleaner under the rim and leave it 10 minutes, then scrub right round the bowl with a "
          "toilet brush, including under the rim, and flush. A limescale ring at the waterline comes "
          "off with a citric acid or vinegar soak overnight."),
# The smell the animal leaves is the same job whether the line says "pee" or "pet smell":
    # "how do i get rid of a pet smell in the carpet" and "my carpet smells of dog" named no
    # accident at all, and the first was answered with the breeder and the second was echoed.
    entry("pet-accident", (("cat pee", "cat peed", "dog pee", "dog peed", "urine", "weed", "peed",
                            "sprayed", "pet accident", "cat urine",
                            "pet smell", "pet smells", "pet odour", "pet odor", "dog smell",
                            "cat smell", "smells of dog", "smells of cat", "doggy smell",
                            "smell of dog", "smell of cat", "dog wee", "cat wee"),
                            ("carpet", "sofa", "smell", "smells", "remove", "rug", "mattress",
                             "stain", "car", "seat", "seats", "upholstery", "room", "house")),
          PET_ACCIDENT_REPLY,
          # "my cat smells" is not a stain: with a bare "cat smell" in the key the prefix matched and
          # the patch-and-detergent answer was given to a line about an animal that wants the tray or
          # the vet. The card wants a place or an accident named, not just the animal and the smell.
          ask=("carpet", "carpets", "rug", "rugs", "sofa", "settee", "mattress", "seat", "seats",
               "upholstery", "room", "rooms", "house", "flat", "floor", "floors", "stairs",
               "bedding", "blanket", "curtain", "curtains", "spot", "patch",
               "pee", "peed", "poo", "urine", "wee", "wees", "sprayed", "spraying",
               "accident", "accidents", "vomit", "sick", "stain", "stains",
               "car", "cars", "van", "boot", "camper", "bed",
               # the animal said inside the smell is the same job even with no place named, but
               # only in that shape: a bare "dog smell" or "cat smell" also matches "my dog
               # smells", which is an animal that wants the tray or the vet, not a spill
               "smell of dog", "smells of dog", "doggy smell", "pet odour", "pet odor",
               "smell of cat", "smells of cat"),
          # the same word is a garden job on the other side: "weed" here is a cat's, and "remove"
          # is the only other key, so "how do i remove weeds from my driveway" tied with the paving
          # row and lost to it
          # a habit is not a spill: "how do i stop my dog peeing in the house" and "my dog has
          # started weeing inside" are the house-training row's, which names the vet check for a
          # house-trained dog that suddenly starts. Only the messes themselves are this row's.
          avoid=("stop", "stopping", "keeps", "keep", "started", "starting", "suddenly",
                 "train", "training", "trained", "house train", "toilet train", "puppy",
                 "puppies", "kitten", "kittens", "every day", "all the time", "again and again",
                 "garden", "driveway", "drive", "paving", "patio", "lawn", "grass", "slabs",
                 "slab", "decking", "path", "pathway", "yard", "gravel", "concrete", "tarmac",
                 "weeds", "weeding", "flower bed", "borders", "plant", "plants", "planting")),
    # Where the mess is, asked a turn later. The key needs the place and the job, and the reply
    # reads the chat: with no animal and no accident behind it this is a sofa-cleaning line and
    # the ordinary upholstery rows answer it.
    entry("the-place-a-pet-used",
          (("sofa", "sofas", "settee", "couch", "armchair", "carpet", "carpets", "rug", "rugs",
            "mattress", "upholstery", "chair", "chairs", "bedding", "duvet", "blanket",
            "blankets", "curtain", "curtains", "floor", "floors", "stairs", "seat", "seats",
            "spot", "spots", "patch", "patches", "hallway", "landing"),
           ("clean", "cleaning", "cleaned", "wash", "washing", "get rid", "get out", "remove",
            "smell", "smells", "what do i do", "what now", "now what", "what about",
            "deal with", "sort out")),
          _the_place_a_pet_used,
          # a gardening, decorating or buying line names a place and a job and is not this
          avoid=("weed", "weeds", "weeding", "driveway", "drive", "paving", "patio", "lawn",
                 "grass", "decking", "path", "garden", "buy", "buying", "cheap", "cheapest",
                 "price", "cost", "paint", "painting", "varnish", "sanding", "shampoo",
                 "hire", "hiring", "rent", "machine")),
    # "skirting" was a key here, which made a mark on a skirting board a question about blinds.
    # The word is gone: a skirting board is a wall, and `wall-mark` answers for it.
    # No bare "how" in the second part: the question word alone matched, so "how do i stop my
    # blinds banging" and "how do i hang blinds" were both a dusting. The job words are what
    # tell this row it is a cleaning line.
    entry("blinds-dust", (("blinds", "venetian blinds", "shutters"),
                           ("clean", "cleaning", "dust", "dusty", "wash", "washing", "wipe")),
          "Close the blinds flat and wipe them with a microfibre cloth or a sock over your hand, then "
          "turn them the other way and do the back; a vacuum brush does a whole set in minutes. Skip "
          "the duster that just moves the dust around.",
          # "blind bake" is a pastry case with nothing in it: the blinds are not dusty, and a
          # kitchen word in the line is what tells the two apart. "skirting" is in the key because
          # a dusty ledge is the same job, so a painter's line ("how do i paint skirting boards")
          # has to stand down here or the woodwork gets a microfibre cloth.
          avoid=("bake", "baking", "baked", "pastry", "oven", "flour", "quiche", "tart",
                 "paint", "painting", "painted", "repaint", "gloss", "undercoat", "primer",
                 "banging", "rattling", "rattle", "noisy", "noise", "hang", "hanging", "fit",
                 "fitting", "install", "stuck", "broken")),
    # "why is my house so dusty" is not "how do i dust the blinds": the question is where the
    # dust comes from and what actually cuts it down, so it gets its own answer.
    entry("dust-where", (("dust", "dusty", "dustier"),
                         ("house", "home", "flat", "room", "rooms", "everywhere", "always",
                          "why", "come", "comes", "coming", "where", "so much", "keep",
                          "constantly", "settles", "build", "builds",
                          # "how do i get rid of dust" is the same question with the method asked
                          # for outright, and this card is the method: it was the shrug. Bare
                          # dust only - "dust on my keyboard" is the keyboard's question, so the
                          # words stand down when the dust is on a named thing.
                          "get rid", "rid", "remove", "reduce", "cut down", "control")),
          "Most of the dust in a house is you: skin flakes and the fibres fabrics shed, plus what "
          "blows in through the windows and gets walked in on shoes. The big sources are bedding, "
          "carpet and soft furnishings, so wash the sheets at 60C every week or two and vacuum "
          "properly with a decent filter rather than a quick pass. Open the windows for ten "
          "minutes a day and damp-dust from the top down, so what you lift lands on the floor to "
          "be vacuumed instead of in the air.",
          avoid=("mite", "mites", "allergy", "allergies", "allergic", "asthma", "sneeze",
                 "sneezing", "cough", "wheeze", "wheezing", "itchy", "rash", "explosion",
                 "fire", "workshop", "builders", "building work", "building site",
                 "renovation", "refurbishment", "demolition", "rubble",
                 "sawdust", "coal", "brick", "cement",
                 "plaster", "chalk", "biscuit", "cocoa", "icing sugar", "cast", "footprints"),
          # the method words above are generic, so bare dust only: "how do i get rid of dust on
          # my keyboard" is the keyboard's card, and "dust from a camera lens" is nobody's
          guard=_dust_is_on_a_thing),
    # The dust row above holds "mite" out because dust mites in a bed are not house dust, and
    # nothing else answered them: "how do i get rid of dust mites", "how do i kill dust mites" and
    # "dust mites in my bed" were the shrug, while the whole point of the question is a method.
    # The two things that work are heat and a barrier, so those are the sentence.
    entry("dust-mites",
          (("dust mite", "dust mites", "dustmite", "dustmites", "dust-mite", "dust-mites",
            "mites in my bed", "mites in the bed", "mites in my bedding",
            "mites in my mattress", "mites in my pillow", "mites in the mattress"),
           ("get rid", "rid", "kill", "killing", "remove", "removing", "reduce", "control",
            "avoid", "stop", "how do i", "how to", "how can i", "best way", "deal with",
            "bed", "beds", "bedding", "bedroom", "mattress", "mattresses", "pillow",
            "pillows", "duvet", "sheets", "allergy", "allergies", "allergic", "asthma",
            "sneeze", "sneezing", "congested", "itchy", "rash", "wash", "washing", "60")),
          "Wash the bedding at 60C every week and put mite-proof covers on the mattress and the "
          "pillows: the mites live in the fabric and feed on skin flakes, so the two things that "
          "work are heat and a barrier. Then keep the room cool and aired, damp-dust from the top "
          "down rather than dry-dusting, and vacuum the mattress and the carpet with a filter "
          "instead of a quick pass; under about 21C and 50% humidity they stop multiplying. Soft "
          "toys go in the freezer overnight. Mite sprays and air fresheners do very little, and a "
          "40C wash does not kill them.",
          bias=2,
          # flour mites are the pantry's, spider mites are the greenhouse's, and a mite on a pet is
          # the vet's: the key phrase says dust, and these words say the line meant something else
          avoid=("flour", "oats", "cereal", "cereals", "rice", "pasta", "porridge", "pantry",
                 "larder", "cupboard", "cupboards", "spice", "spices", "dried fruit", "nuts",
                 "plant", "plants", "garden", "greenhouse", "spider mite", "spider mites",
                 "hen", "hens", "chicken", "chickens", "bird", "birds", "dog", "dogs", "cat",
                 "cats", "pet", "pets", "puppy", "kitten", "fish tank", "hay", "straw")),
    # Grease on a wall or a splashback is a kitchen cleaning job with its own method, and the
    # hob and cooker entries avoid it because the hob is not the wall.
    # The extractor is left out of the surfaces: its own entry knows the filters and the
    # dishwasher, and a general "wipe it with washing-up liquid" answer would lose that
    # ("how do i clean the extractor filter" was taking this instead of the filter answer).
    # "how do i clean behind the radiator" was a shrug, and the same line about the fridge,
    # the washing machine or the bed was answered as if the whole thing wanted cleaning: the
    # fridge card emptied the shelves for a line about the gap at the back. What people are
    # asking is how to reach a place they cannot see, so the place is in this key - behind,
    # under, underneath - and so is the thing they cannot move.
    entry("clean-behind-things",
          (("behind", "under", "underneath", "beneath", "at the back of", "the back of",
            "back of the", "the gap behind", "the side of"),
           ("radiator", "radiators", "fridge", "freezer", "washing machine", "washer",
            "tumble dryer", "dryer", "sofa", "settee", "couch", "bed", "wardrobe",
            "cupboard", "cupboards", "cooker", "oven", "dishwasher", "tv", "television",
            "cabinet", "cabinets", "dresser", "sideboard", "bookcase", "shelves", "machine",
            "kitchen units")),
          "Reach it rather than move it: a duster or a microfibre cloth taped to a broom handle "
          "gets behind a radiator or under a low bed, and a vacuum crevice tool does the same "
          "afterwards. If the thing can be pulled out - a fridge, a washing machine, a sofa "
          "without a fixed back - pull it clear first and clean the wall and the floor behind "
          "it, because that is where crumbs and dust collect. While the fridge or the freezer "
          "is out, vacuum the coil or grille at the back: dust on it is why it runs hot and "
          "costs more.",
          # fitting a machine is not cleaning behind it: "how do i fit a washing machine under a
          # counter" is `fit-a-washing-machine` in home.py, and the place ("under") plus the
          # machine was all this row needed to claim it.
          # Only the washing machine is named, not the verb: "how do i fit a dishwasher under a
          # counter" keeps the answer it had (a wrong card is still better than the shrug the
          # bare word "fit" would hand it), while every washing machine line goes to
          # `fit-a-washing-machine` in home.py.
          avoid=("fit a washing machine", "fit the washing machine", "fit my washing machine",
                 "fitting a washing machine", "fitting the washing machine",
                 "install a washing machine", "install the washing machine",
                 "plumb in a washing machine", "plumbed in a washing machine",
                 "hook up a washing machine", "connect a washing machine",
                 "connect the washing machine", "transport bolts", "transit bolts",
                 "standpipe", "stain", "smell", "smells", "smelly", "mould", "mold", "damp", "drains",
                 "clogged", "blocked", "leaking", "broken", "not working", "wont",
                 "won't", "noise", "noisy", "install", "installing", "move it", "moving house",
                 "under the rim", "toilet", "loo", "cistern", "under the sink", "trap",
                 "sheets", "mattress", "duvet", "pillow", "car", "under the car",
                 # the gap between cushions is inside the sofa, and the upholstery card is the
                 # right answer for it
                 "cushion", "cushions",
                 # a machine that is hot, humming or not working is a fault, and the fault cards
                 # are the answer: "the back of my fridge is hot" was this row's
                 "hot", "warm", "overheating", "hum", "humming", "buzzing", "rattling",
                 "compressor", "not cooling", "freezing up", "puddle", "fault", "faulty",
                 "error", "flashing", "reset", "warranty", "engine", "bonnet", "exhaust",
                 # a radiator's own card already says how to reach the space behind it, and it
                 # says more than a general place answer can: the fins, the vacuum, the paint
                 "radiator", "radiators", "fins",
                 "shed", "garage", "decking", "patio", "hutch", "cage", "pram", "buggy",
                 # a cat or a dog that is under the bed is hiding, and "why does my cat hide
                 # under the bed" was answered with a duster on a broom handle
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies",
                 "rabbit", "hamster", "guinea pig", "hiding", "hides", "hide", "hiding place"),
          # the laundry-sorting and fridge routines name the appliance too and score higher on
          # it, so the place is what this row is preferred for
          bias=1, guard=_the_back_of_a_screen),
    entry("wall-grease", (("wall", "walls", "splashback", "splash back", "tiles", "tiling",
                           "cupboard", "cupboards"),
                          ("grease", "greasy", "sticky", "film", "clean", "cleaning",
                           "remove", "get rid")),
          "Wipe it with hot water and washing-up liquid first, working from the top down, and rinse "
          "the cloth often: hot water melts the grease and the soap lifts it. For a film that has "
          "been there a while, make a paste of bicarbonate of soda and water, leave it ten minutes "
          "and rinse, or use a proper kitchen degreaser on tiles and a splashback.",
          avoid=("paint", "painting", "painted", "wallpaper", "wallpapering", "crack", "cracks",
                 "cracked", "hole", "holes", "drill", "shelf", "shelves", "hang", "damp",
                 # a nail or a screw in the wall is a fixing, not a grease film
                 "nail", "nails", "screw", "screws", "rawplug", "rawlplug", "rawl plug",
                 "mould", "mold", "condensation", "outside", "exterior", "render", "paper",
                 "peeling", "strip", "stripping", "plaster", "skim", "brick", "garden",
                 # a plant growing on a wall is a plant, not a wall to wipe: the ivy and bramble
                 # rows in garden.py are the ones for it
                 "ivy", "ivies", "creeper", "creepers", "climbing plant", "climbing plants",
                 "climbers", "vine", "vines", "wisteria", "bramble", "brambles")),
    # A mark on a painted wall is the commonest small cleaning question there is, and
    # `how do i get a mark off the wall` and `how do i get pen off the wall` were shrugs: the
    # wall card is keyed on grease and cleaning, and a mark is neither word. Crayon, felt tip and
    # chalk keep their own card, and so does grease.
    entry("wall-mark", (("wall", "walls", "skirting", "paintwork", "painted wall", "wallpaper",
                         "door", "doors", "door frame"),
                        ("mark", "marks", "scuff", "scuffs", "scuffed", "smudge", "smudges",
                         "handprint", "handprints", "fingerprint", "fingerprints", "pen", "ink",
                         "dirty", "dirt", "shoe", "shoes", "off", "get", "remove")),
          "A pencil rubber takes most scuffs off a matt emulsion, and a damp sponge with a drop of "
          "washing-up liquid takes the rest - rub gently, because the paint comes off with the "
          "mark if you scrub hard. For ink or a stubborn scuff a melamine sponge works, but try "
          "it low down first: it is a fine abrasive and it dulls sheen and eggshell.",
          # a specific mess has its own answer, and a wall that needs repair, paint, paper or a
          # shelf hanging is a job, not a mark
          avoid=("crayon", "crayons", "felt tip", "marker", "chalk", "pencil", "pencils",
                 # a noise is not a mark: "how do i get my dog to stop barking at the door"
                 # matched "door" and "get" and was told how to rub a scuff off emulsion. No
                 # cleaning question contains one of these words.
                 "bark", "barks", "barking", "howl", "howls", "howling", "yap", "yaps",
                 # an animal at the door is not a scuff on it: "my dog keeps getting out the
                 # front door" matched "door" and "get" and was told how to rub a mark off paint
                 "dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "rabbit",
           "yapping", "whine", "whines", "whining", "growl", "growls", "growling",
           "meow", "meows", "meowing", "miaow", "miaows",
                 # getting in through a door is not a mark on it: "i cant get in my front door"
                 # matched "get" and "door" and was told how to rub a scuff off matt emulsion
                 "get in", "get out", "getting in", "getting out", "get back in", "locked out",
                 "locked in", "locked", "spare key", "keys", "locksmith", "keyhole",
                 "black marks", "black spots",
                 "grease", "greasy",
                 "mould", "mold", "damp", "condensation", "crack", "cracks", "cracked", "hole",
                 "holes", "drill", "shelf", "shelves", "hang", "paint", "painting", "painted",
                 # A fitting that has come off the wall is a fixing job, not a mark: "my curtain
                 # rail keeps coming off the wall" and "the shelf has pulled out of the wall"
                 # were told how to rub a scuff off emulsion, because "wall" and "off" are both
                 # in this key.
                 "coming off", "came off", "come off", "keeps coming off", "coming away",
                 "came away", "pulled out", "pulling out", "ripped out", "torn out", "fallen",
                 "fell", "falling off", "fell down", "came down", "sagging", "loose", "wobbly",
                 "won't stay", "wont stay", "curtain rail", "curtain pole", "curtain rod",
                 "curtain track", "rail", "bracket", "brackets", "fixing", "fixings",
                 "rawl plug", "rawlplug", "hollow wall", "plasterboard",
                 # a nail or a screw in the wall is a fixing, not a mark on the paint: "how do
                 # i remove a nail from a wall" holds "remove" and "wall", and was told to fetch
                 # a pencil rubber. home_craft.py's nail row is the one for it.
                 "nail", "nails", "nailed", "nailing", "screw", "screws", "screwed",
                 "wallpapering", "strip", "stripping", "plaster", "skim", "brick", "ceiling",
                 "outside", "exterior", "render", "car", "cars", "windscreen", "screen", "leather",
                 "sofa", "shoe polish", "floor", "floors", "wood", "window", "windows",
                 # a shower door is glass and its marks are scale, not a scuff on emulsion:
                 # "my shower door is covered in white marks" was told to fetch a pencil rubber
                 # for matt paint
                 "shower", "shower door", "shower screen", "shower glass", "bathroom",
                 "limescale", "scale", "scaled", "tiles", "tiled", "grout",
                 # The "door" in the key is a house door with a painted face, and it took every
                 # appliance with a door and a mark on it: "the oven door glass is dirty inside"
                 # and "my microwave door is streaky" were told to fetch a pencil rubber for matt
                 # emulsion. An appliance door is glass or enamel and its own row knows it.
                 "oven", "cooker", "hob", "microwave", "fridge", "freezer", "washer",
                 "washing machine", "dishwasher", "tumble dryer", "oven door",
                 "microwave door", "fridge door", "glass",
                 # a coat of paint on a surface is stripped, not wiped: "how do i get emulsion
                 # off a wall" is the stripper's job, and the paint-substance words the stripper
                 # answers belong to it
                 "emulsion", "gloss", "varnish", "undercoat", "primer", "lacquer",
                 "sand off", "sanding", "heat gun", "stripper",
                 # and the finish is the paint too, whatever it is called
                 "finish", "finishes", "bare wood",
                 # A plant on a wall is a plant, not a mark on it: "how do i get rid of ivy on a
                 # wall" holds "wall", "get rid" and "off"-shaped words, and was told to fetch a
                 # pencil rubber. garden.py's ivy and bramble rows are the ones for it.
                 "ivy", "ivies", "creeper", "creepers", "climbing plant", "climbing plants",
                 "climbers", "vine", "vines", "wisteria", "bramble", "brambles"),
          # the general wall wipe keys "wall" and "clean", so a line with a mark in it would tie
          bias=2,
          # The mark is this row's subject, and a key word may be borrowed from the turn before:
          # "the alarm goes off every time i cook" followed by "is it the one near the kitchen
          # door" reached this row on the earlier turn's "off" and this turn's "door", and
          # answered a smoke alarm with a pencil rubber.
          # What a mark is made of is not a closed list, so the words below are the ones people
          # actually name, not every one there is: a reader who says the coffee, the sticker or
          # the scratch is describing the same job as the one who says the scuff. The removal
          # words are deliberately not here - "off" and "get" are the words a turn borrows from
          # the one before, which is what this gate exists to stop.
          ask=(("mark", "marks", "scuff", "scuffs", "scuffed", "smudge", "smudges", "handprint",
                "handprints", "fingerprint", "fingerprints", "pen", "ink", "dirt", "dirty",
                # The job words are in as well, so the gate is "is this a line that gets
                # something off a surface" rather than a list of every substance there is: what a
                # mark is made of is not a closed list. They are safe here because the ask is read
                # from this line, not from the turn before - checked on the two alarm chats.
                "off", "get", "remove", "rid",
                "shoe", "shoes", "coffee", "tea", "sticker", "stickers", "scratch", "scratches",
                "scraped", "scrape", "smear", "smears", "streak", "streaks", "splat", "mud",
                "muddy", "chocolate", "glue", "blu tack", "wax", "food", "sauce", "ketchup",
                "juice", "greaseproof"),)),
    # "how do i get rid of the smell of smoke in a car" was this room answer, curtains and all:
    # what holds smoke in a car is the seats, the headlining, the carpets and the cabin filter, and
    # none of them wash like a throw. The car words are out of the key, and a smoky car is
    # `cars.car-smoke-smell`.
    entry("smoke-smell", (("smoke", "cigarette", "smoky", "smoking"),
                           ("smell", "room", "house", "flat", "sofa", "curtains", "gone",
                            "get rid")),
          "Air the room hard, wash the soft things (curtains, cushions, throws), and put bowls of "
          "white vinegar out overnight: the vinegar absorbs the smell and the room doesn't smell of "
          "vinegar by morning. Wipe hard surfaces; smoke clings to walls and furniture, not the air.",
          avoid=("fire", "alarm", "burning", "right now", "coming from", "toaster", "wire",
                 "car", "cars", "van", "vehicle", "seats", "seat", "headlining", "cabin",
                 "air con", "aircon", "air conditioning", "upholstery")),
    entry("kitchen-smell", (("kitchen", "flat", "house", "room", "living room", "cooking",
                              "food", "cabbage", "chips"),
                             ("smell", "smells", "smelly", "stink", "stinks", "odour", "lingers",
                              "lingering")),
          "Open a window, then simmer a pan of water with a sliced lemon or a splash of vinegar for "
          "10 minutes: that clears cooking smells better than any spray. Find the source too, "
          "because a lingering smell is usually the bin, the drain or the fridge.",
          # a room that smells of paint is home.py's paint-smell row, and the answer here names
          # the drain itself, so a line about the drain wants the drain entry: "the drain smells
          # in the kitchen" was told to simmer a lemon on the hob.
          avoid=("gas", "leak", "burning", "burnt", "fire", "smoke", "fumes", "carbon monoxide",
                 "electrical", "wires", "mould in the wall", "fish", "fishy", "damp",
                 "condensation", "musty", "mould", "mold", "paint", "painting", "painted",
                 "repainted", "gloss", "emulsion", "drain", "drains", "plughole", "plug hole",
                 "sink", "sinks", "bin", "bins", "fridge", "freezer")
                 # A garment word makes it the clothes row's question, not the room's: "cooking"
                 # is one of the smells a garment holds, so "my jacket smells of cooking" and
                 # "my clothes smell of cooking" were told to open a window and simmer a lemon.
                 # This is `odours.GARMENT`, written out here rather than imported, because
                 # importing it reorders the entries and two unrelated lines (`my room smells
                 # of chips`, `my wardrobe smells`) lost their card when it did.
                 + GARMENT_WORDS,
          # ... and a line that says the food in the room has gone off is that food's question,
          # not the air's: "my chicken smells a bit, can i cook it" was told to simmer a lemon
          # because "cooking" and "smells" are both key words here. The rows in still_ok.py
          # answer it, and this one stands down (bot/knowledge/lookup.food_has_gone_off).
          guard=lambda read: not food_has_gone_off(read),
          bias=1),
    # --- fabrics and garments that the table did not cover -------------------
    # "how do i wash silk" was answered with the bra line, because delicates-wash keys on
    # "silk" as well; a silk shirt needs its own answer. "how do i stop linen creasing" and
    # "bleach stain on my trousers" were both a shrug.
    entry("silk-wash", (("silk", "satin", "silk shirt", "silk dress"),
                        ("wash", "washing", "clean", "iron", "water", "dry", "machine",
                         "crease", "creases", "creasing")),
          "Hand-wash silk in cool water with a drop of shampoo or silk detergent, rinse in water of "
          "the same temperature, and never wring it: roll it in a towel and press the water out. Dry "
          "it away from sun and heat, and iron it on the silk setting while it is still slightly "
          "damp, with a cloth between the iron and the fabric.", bias=1),
    entry("linen", (("linen", "bed linen", "linen shirt", "linen trousers"),
                    ("crease", "creases", "creased", "creasing", "iron", "wash", "washing",
                     "soften", "stiff", "stiffness", "wrinkle", "wrinkles")),
          "Linen creases because the fibre has no give, and the fix is water and heat: wash it on a "
          "normal cycle at 40C, take it out the moment the machine stops, shake it hard and hang or "
          "line dry it. Iron it damp on the hottest setting it will take, or leave it creased and "
          "call it the point of linen. A new, stiff piece softens after three or four washes.",
          # a linen that has shrunk, or might, is the shrinkage card's question, and that answer
          # names linen: this one is only about creases and was taking "does linen shrink in the
          # wash" on the word "wash"
          avoid=("shrink", "shrinks", "shrank", "shrunk", "shrunken", "shrinkage",
                 "came out small", "too small", "felted", "baggy")),
    entry("bleach-spot", (("bleach", "bleached", "bleach spot"),
                           ("shirt", "top", "jeans", "trousers", "dress", "clothes", "hoodie",
                            "jumper", "towel", "towels", "spot", "mark", "splash", "splashed",
                            "got", "gone white", "turned white", "stain", "stains", "stained")),
          "Bleach does not leave a stain, it takes the dye out, so nothing you apply brings the "
          "colour back: the only fixes are a fabric pen in a close colour, a patch or embroidery "
          "over the spot, or dyeing the whole thing darker. On white cotton it is invisible, so "
          "check before you panic. Next time, gloves and an old shirt.",
          avoid=("toilet", "loo", "bin", "mould", "mold", "sink", "bath", "shower", "kitchen",
                 "floor", "washing machine", "cooker", "grout", "drain", "clean", "can i put",
                 "can i use", "should i use", "how much bleach", "add bleach", "in with",
                 "on white towels", "on a white towel", "on my white", "on white cotton",
                 "on whites", "on the whites",
                 # the same ask shapes as above: "can i bleach white towels" and "do i need
                 # bleach for white towels" are questions about using it, not about a mark it
                 # left, and the garment word in them ("towels") was enough to take them here.
                 "can i bleach", "should i bleach", "need bleach", "bleach for")),
    # The other side of the same word: a question about using bleach, not about a bleach mark.
    entry("bleach-use", (("bleach", "thin bleach", "bleach solution"),
                         # The second group has to be a thing the bleach goes on or into. It used
                         # to hold "can i use" and "can i put" as openers, and an opener is a way
                         # of asking, not a subject: "can i use bleach on a cut" and "can i use
                         # bleach on my hair" came here for a ten-minute soak for white towels.
                         ("how much", "add", "in with",
                          "towels", "whites", "wash", "washing", "sink", "soak", "dilute",
                          # "bleach on my white shirt" and "bleach on whites" ask how to use it,
                          # and the mark row above holds those phrases out, so the phrase has to
                          # be here or the line reaches neither
                          "on white", "on whites", "on the whites", "on my white",
                          "on white towels", "on white cotton", "on white socks")),
          "Thin household bleach is fine on white cotton and on white towels: about two tablespoons "
          "in five litres of cool water for a ten-minute soak, or half a cup in the drum of a full "
          "wash, and never poured neat onto fabric. Rinse well, never mix it with anything containing "
          "ammonia or with a vinegar soak, and keep it off wool, silk, coloured clothes and anything "
          "elastic, which it eats.",
          avoid=("stain", "stains", "mark", "marks", "spot", "spots", "splash", "splashed", "got",
                 "spilled", "spilt", "went white", "toilet", "bin", "mould", "mold", "grout",
                 "drain", "floor", "sink waste",
                 # "can i put bleach down the sink" is the drain question, and this row answered it
                 # with a ten-minute soak for white towels: its own "drain" fence does not catch a
                 # line that says sink, so the two ways of saying the same thing are fenced too.
                 "down the sink", "down our sink", "down my sink", "down the plughole",
                 "plughole", "plug hole", "down the pipe", "septic")),
    # Pouring bleach down a drain is its own question: the bleach entries above are about marks
    # and about washing, and both hold "drain" out on purpose, so every line that asked whether it
    # is safe fell to a search hedge ("can i put bleach down the drain") or, worse, to the
    # tiredness answer through the noun "drain" folding onto "drained".
    entry("bleach-down-the-drain",
          (("bleach", "thin bleach", "bleach down", "pour bleach", "caustic soda"),
           ("drain", "drains", "plughole", "plug hole", "sink", "pipes", "pipework",
            "septic tank", "septic", "cesspit", "soakaway",
            "blocked", "unblock", "smell", "smells", "smelly", "down the drain")),
          _bleach_down_the_drain,
          avoid=("stain", "stains", "mark", "marks", "splash", "splashed", "towels", "whites",
                 "wash", "washing", "jeans", "clothes", "shirt", "trousers")),

    entry("leather-care", (("leather", "leather jacket", "leather coat", "leather boots",
                            "leather shoes", "leather bag", "leather sofa"),
                           ("clean", "cleaning", "condition", "conditioner", "crack", "cracking",
                            "cracked", "dry", "drying", "water", "rain", "care", "look after",
                            # A mark on leather is the same question with a stain in it: "how do i
                            # get a stain out of a leather sofa" and "ink off a leather sofa" were
                            # both the search shrug, because this row only knew about cleaning.
                            "stain", "stains", "stained", "ink", "pen", "grease", "mark",
                            "marks", "spilt", "spill")),
          "Wipe leather with a barely damp cloth and a little saddle soap, let it dry away from "
          "radiators, then work in a thin layer of leather conditioner while it is still damp. "
          "For a stain, dab rather than rub with a drop of washing-up liquid on a damp cloth; a "
          "ballpoint mark lifts with a cotton bud of rubbing alcohol. Leather cracks as it dries, "
          "so condition it two or three times a year and never scrub or soak it.",
          avoid=("suede", "nubuck", "faux", "leather sofa repair", "car seat")),

    entry("dry-cleaning", (("dry clean", "dry cleaning", "dry cleaners", "dry-clean", "dry cleaned"),
                            ("suit", "dress", "coat", "jacket", "need", "can i", "wash", "washing",
                             "cost", "how", "should")),
          "Take the suit, jacket or dress to a dry cleaner and leave the label alone: the dry-clean-only "
          "tag means the fabric or the lining will shrink, bleed or lose its shape in water, and no "
          "gentle cycle makes that safe. Two or three times a year is plenty for a suit worn weekly; "
          "between times, air it overnight and brush it. A silk or wool item marked dry clean only "
          "that is really just delicate can be hand-washed, but that is a gamble on a favourite.",
          # a coat has its own entry that says how often, so leave those lines to it
          avoid=("coat", "down jacket", "padded jacket", "puffer", "sleeping bag"),
          bias=1),
    entry("sleeping-bag", (("sleeping bag", "down bag", "sleeping bags"),
                           ("wash", "washing", "clean", "smell", "smells", "store", "storing",
                            "machine", "dry")),
          "Wash a down sleeping bag in a front-loading machine on a gentle cycle with a down-specific "
          "wash, or by hand in the bath, then dry it on low heat with two or three clean tennis balls "
          "to break the clumps up: it takes hours and it must be bone dry before it is stored. Never "
          "store it in its stuff sack; hang it or keep it loose, which is what keeps the loft.",
          bias=1),
    # --- the everyday jobs that were not here yet ---------------------------
    # A stain with no name is still the commonest laundry question ("how do I get a stain out of
    # a white shirt"), so this is the general method. Every named stain above stays its own entry:
    # the chemical that lifts ink or blood is not the one that lifts grease.
    # The ask words are garment words and, below them, the question shapes: "get this stain out",
    # "how do i remove a stain i cant identify", "i dont know what this stain is". A line like that
    # names no substance and no garment, so without the shapes here it fell to the search shrug -
    # the commonest laundry question of all had no answer. apt-robin's worry (that a bare "out" or
    # "remove" let this entry answer about a couch, a car seat or a trainer) is what the avoid list
    # underneath is for, and every one of those words is in it.
    entry("stain-unknown", (("stain", "stains", "stained", "staining",
                             "mark", "marks", "marked"),
                            ("clothes", "clothing", "shirt", "shirts", "t-shirt", "top", "tops",
                             "jumper", "trousers", "jeans", "dress", "fabric", "cotton", "white",
                             "whites", "wash", "washing", "laundry", "uniform", "blouse", "skirt",
                             "cardigan", "hoodie", "sock", "socks", "tablecloth", "napkin",
                             # a coat is a garment too, and the sleeve is where the mark is:
                             # "my coat has a stain on the sleeve" named nothing this entry
                             # recognised, so it went to the echo pool
                             "coat", "coats", "jacket", "jackets", "sleeve", "sleeves",
                             "cuff", "cuffs",
                             "linen", "tea towel",
                             "out", "get out", "got out", "come out", "came out", "comes out",
                             "remove", "removed", "shift", "lift", "identify", "what it is",
                             "what this is", "dont know", "no idea", "not sure what",
                             # "wots the best way to remoov a stain", "how do i clean a stain",
                             # "how should i treat a stain" and "wots the best way to get rid
                             # of a stain" each named a stain and nothing in this half, so all
                             # four were a search hedge while "how do i get a stain out"
                             # answered. The half is the ways people ask, and the everyday verbs
                             # were missing from it; the key half already says the line is
                             # about a stain, so a broad verb list cannot pull in a line about
                             # something else, and the `avoid` words still take the marks this
                             # card does not know.
                             "clean", "cleaned", "cleaning", "treat", "treated",
                             "rid", "get rid", "got rid", "deal with", "sort", "sorted",
                             "sort it", "what now", "help", "fix", "save", "saved",
                             "way", "best way", "how do i", "how should i",
                             "hot water", "set it in", "set in", "boiling water")),
          "Blot it with kitchen paper, then rinse it from the back in cold water before any soap "
          "touches it, and rub a little washing-up liquid in with your fingers. Wash it as hot as "
          "the label allows with a scoop of oxygen bleach: for whites that is the hottest wash it "
          "takes, for colours a 40C one. Do not tumble dry it until the mark has gone, because heat "
          "sets it for good.",
          avoid=("red wine", "wine", "ink", "grease", "oil", "fat", "blood", "grass", "sweat",
                 "curry", "ketchup", "coffee", "tea", "chewing gum", "gum", "suede", "salt",
                 "rust", "chocolate", "mud", "baby", "vomit", "paint", "bleach", "marker",
                 "carpet", "sofa", "couch", "settee", "mattress", "sink", "towel", "makeup",
                 "make-up", "foundation", "deodorant", "nappy", "poo", "pee", "trainers", "shoes",
                 "shoe", "boots", "bag", "curtain", "curtains", "rug", "car seat", "car", "upholstery",
                 "wall", "walls", "skirting", "paintwork", "ceiling", "banister", "radiator",
                 "table", "worktop", "wood", "floor", "grout", "bath", "toilet",
                 # a wider list of asking verbs means this card now catches the other
                 # meanings of "mark" and the marks a surface of its own answers: a hard
                 # water mark on a shower or a tap, the scorch on a pan, and the speech
                 # marks of a written line each had their own card and lost it to this one.
                 "hard water", "limescale", "water mark", "water marks", "shower", "tap",
                 "taps", "kettle", "pan", "scorch", "scorched", "speech marks", "quotation",
                 "quote", "punctuation", "bookmark", "landmark", "trade mark", "grade",
                 "grades", "exam", "birthmark", "stretch mark", "stretch marks", "pen mark",
                 "pencil mark", "tool mark", "tick", "tick mark",
                 # a mark on a screen or a pane is a smudge with its own card, and a chat whose
                 # first line was "my tv screen has marks" then answered "how do i clean it"
                 # with the cold-water-and-oxygen-bleach card, because the thread had put
                 # "marks" in front of it
                 "screen", "screens", "tv", "television", "monitor", "laptop", "phone",
                 "phone screen", "glass", "window", "windows", "spectacles", "glasses",
                 "mirror", "lens", "camera")),
    # "how do i wash a school uniform" is the commonest laundry question a parent sends, and on
    # main every shape of it reached money's trips-and-kit card, because "school" and "uniform"
    # are key words there and "kit" is how the same card is keyed: the answer was a paragraph
    # about voluntary contributions. The money question ("how much is a school uniform", "can i
    # get help paying") keeps its own card: the cost words below stand this one down.
    entry("school-uniform-care",
          (("school uniform", "school uniforms", "school shirt", "school shirts", "school jumper",
            "school jumpers", "school trousers", "school pinafore", "school skirt", "school tie",
            "school blazer", "school pe kit", "school cardigan", "uniform", "uniforms"),
           ("wash", "washing", "washed", "clean", "cleaning", "stain", "stains", "stained", "ink",
            "mud", "paint", "smell", "smells", "smelly", "iron", "ironing", "shrink", "shrunk",
            "white", "whites", "name tag", "name tags", "label", "labels", "care", "before wearing",
            "new", "30", "40", "60", "temperature", "keep")),
          _uniform_care,
          # the money question (how much it costs, where to buy it) is trips-and-kit next door
          avoid=("how much", "much is", "cost", "costs", "price", "prices", "afford", "cheap",
                 "cheapest", "grant", "voucher", "help paying", "help with the cost", "fees",
                 "buy", "buying", "shop", "shops", "where can i get", "second hand", "hand me down",
                 "trips", "trip", "kit list", "ofsted", "admissions",
                 # a sticker left on the jumper is a sticky residue, not a name tag to sew in:
                 # the washing-up-liquid-and-oil row answers that one, and it answered it here
                 # until "name tag" started keying this row.
                 "sticker", "stickers", "sticky", "glue", "residue", "adhesive")),
    # Preventing the shrink is a different question from stretching something back out.
    entry("clothes-shrinking", (("shrink", "shrinking", "shrinkage", "shrunken"),
                                ("stop", "prevent", "avoid", "why", "happens", "keep", "laundry",
                                 "washing", "wash", "dryer", "tumble", "order")),
          "Shrinkage is heat and agitation, so wash cool (30C, or 20C for anything with stretch) on "
          "a short cycle, spin it slow, and skip the tumble dryer or use its lowest setting. Cotton "
          "and wool shrink most, linen mostly in the length, and a hot wash is what does it; "
          "buying a size up never fixes a jumper that a 60C wash has already felted.",
          # deliberate shrinking of a jumper is clothing.py's, and a garment that already came out
          # small is shrunk-clothes next door. Jeans are not kept out here: "how do i stop my jeans
          # shrinking in the wash" is exactly this question, and leaving the word out sent it to
          # the entry that tells you how to shrink them.
          avoid=("how do i shrink", "how to shrink", "how do i make", "wool",
           # a floor is not a cupboard: the kitchen floor lines were answered with how to empty
           # one out, off the word "kitchen" alone
           "floor", "floors", "mop", "mopping", "tile", "tiles", "vinyl", "lino",
                 "jumper", "knitwear", "cashmere", "merino", "deliberately", "on purpose",
                 "shrank", "came out small", "too small", "baggy", "stretch out",
                 # pastry shrinks in the oven for its own reasons, and "shrink" alone is a
                 # laundry word to a washing machine and a cooking word in a kitchen
                 "pastry", "quiche", "tart", "flan", "pie", "pastry case", "oven", "baking",
                 "blind bake", "bake", "baked", "baking beans")),
    # Wood and laminate want the opposite of what tiles want: very little water, nothing abrasive.
    entry("floor-clean", (("wooden floor", "wood floor", "wooden floors", "wood floors",
                           "floorboards", "floorboard", "hardwood", "laminate", "laminate floor",
                           "laminate floors", "timber floor", "oak floor", "parquet"),
                          ("clean", "cleaning", "mop", "mopping", "wash", "washing", "polish",
                           "shiny", "damp", "care", "for", "streaks", "streak", "smear",
                           "smears")),
          "Vacuum it first, then mop with a barely damp mop and a pH-neutral wood cleaner, drying "
          "as you go: standing water and a wet mop are what leave the streaks and dull a laminate. "
          "Vinegar, bleach and steam mops take the finish off wood, so save those for tiles, and "
          "buff a dry floor with a microfibre cloth to bring the shine back.",
          avoid=("scratch", "scratches", "scratched", "scuff", "scuffs", "creak", "creaks",
                 "squeak", "squeaks", "lift", "lifting", "refinish", "sanding", "sand it",
                 "gap", "gaps", "spill")),
    # The everyday floor question had no card of its own: "how do i clean the kitchen floor" was
    # answered with how to empty a cupboard, because the only floor entry is the wood one, whose
    # advice (barely any water) is the opposite of what a tile or vinyl floor wants. Wood and
    # laminate keep that card, so their words stand this one down.
    entry("floor-mop", (("floor", "floors", "tile", "tiles", "tiled", "vinyl", "lino", "linoleum",
                         "kitchen floor", "bathroom floor", "stone floor", "concrete floor"),
                        ("clean", "cleaning", "mop", "mopping", "wash", "washing", "sticky",
                         "streak", "streaks", "smear", "smears", "greasy", "shiny", "scrub",
                         "sweep", "smell", "smells", "dirty")),
          "Sweep or vacuum first, then mop with hot water and a squirt of washing-up liquid, "
          "wringing the mop out until it is barely damp, because standing water is what leaves "
          "the streaks. Give a sticky patch a second pass with a little more soap, then go over "
          "the whole floor once with clean water, since the soap film left behind is what dulls "
          "it and grabs the next lot of dirt. A greasy ring by the cooker comes off with a paste "
          "of bicarbonate of soda on a cloth.",
          avoid=("wood", "wooden", "laminate", "floorboard", "floorboards", "parquet", "oak",
                 "hardwood", "timber", "grout", "scratch", "scratches", "scuffed", "carpet",
                 "rug", "rugs", "cupboard", "cupboards", "moth", "moths", "squeak", "creak",
                 "fridge", "freezer", "oven", "bake")),
    # "how often should i clean my kitchen floor" was answered with how to mop one, which is the
    # other question: the person knows how, and wants the interval. The frequency words carry the
    # row, so the method rows keep every line that asks how.
    # The oven is cleaned by hand in home.py (`oven-clean`), which answers how. The interval is
    # the other question, and it lives here because home.py is at the world's file-size limit.
    entry("oven-often", ("oven", ("how often", "how many times", "every week", "every month",
                                  "every few months", "once a month", "frequency", "regularly",
                                  "often should")),
          "Every two to three months for the inside if you use it most days, and a wipe of any "
          "spill once the oven is cool enough to touch: burnt-on grease is what smokes and what "
          "takes an hour of scrubbing once it has baked on. The door glass is worth a wipe every "
          "few weeks, and the racks come out to soak two or three times a year. A self-cleaning "
          "oven wants its pyrolytic cycle about every three months.",
          # cleaning one, a burnt hand and a fire risk are other questions
          avoid=("hand", "hands", "finger", "fingers", "burnt my", "burn", "burned", "scald",
                 "blister", "fire", "smoke alarm", "safe", "dangerous", "glass", "pane",
                 "buy", "buying", "cost", "replace", "repair", "not heating", "fan")),
    entry("floor-often", (("floor", "floors", "kitchen floor", "bathroom floor", "tiles",
                           "tile", "vinyl", "lino", "linoleum", "carpet", "carpets", "rug",
                           "rugs", "hoover", "hoovering", "vacuum", "vacuuming", "mop", "mopping"),
                          ("how often", "how many times", "times a week", "times a month",
                           "once a week", "every week", "weekly", "frequency", "how regularly",
                           "regularly", "often should")),
          "Sweep or vacuum the hard floors every few days and mop once a week, or twice in a "
          "kitchen where frying spits and shoes come in: a floor that looks clean still holds the "
          "film that makes it dull and sticky. Carpets want a vacuum once a week, more where people "
          "walk in shoes, and a deep clean once a year. A doormat halves the work, and wash the mop "
          "head or rinse the bucket out after every use, because a dirty mop just moves the dirt "
          "around.",
          # A hoover's own filter and a bathroom habit score the same words, so the row that
          # names the floor goes first.
          bias=1,
          # how to clean one is floor-mop's and floor-clean's question, and a floor that is
          # scratched, creaking or lifting is a repair
          avoid=("wood", "wooden", "laminate", "floorboard", "floorboards", "parquet", "oak",
                 "hardwood", "timber", "grout", "scratch", "scratches", "scuffed", "creak",
                 "squeak", "stain", "stains", "spill", "spilled", "smell", "smells",
                 "cupboard", "fridge", "freezer", "oven", "bake", "buy", "buying", "cost")),
    entry("mouldy-wood", (("wooden spoon", "wooden spoons", "spoon", "spoons", "chopping board",
                           "wooden board", "wooden chopping board", "utensils", "utensil",
                           "rolling pin", "wooden"),
                          ("mouldy", "mould", "mold", "moldy", "mildew", "black spots", "musty",
                           "gone black", "gone green", "black")),
          "Scrub it with hot soapy water and a paste of bicarbonate of soda, then stand it in the "
          "sun to dry: surface mould comes off wood and the piece is fine afterwards. If the black "
          "has gone into the grain or the wood smells musty when it is dry, bin it, because the "
          "hyphae go deeper than the surface. Never put wooden spoons or boards in the dishwasher, "
          "and oil them monthly so water stops soaking in.",
          avoid=("bread", "cheese", "fruit", "jam", "loaf", "food", "leftovers", "wall", "walls",
                 "ceiling", "bathroom", "shower", "fridge", "lemon", "tomato", "sauce")),

    # Steam on spectacles and goggles is the same physics as the bathroom mirror, but the answer
    # has to name the thing they are wearing: a bathroom fan is useless advice to someone in a mask.
    # This entry and `clothing.glasses-fog` were two tables for one fact and two tests disagreed
    # about which answer a person gets, so the why-first wording moved here and the copy went.
    entry("anti-fog", (("glasses", "spectacles", "specs", "goggles", "ski goggles", "visor",
                        "eyeglasses", "eye glasses",
                        "face mask", "mask"),
                       ("fog", "fogging", "fogged", "foggy", "steam", "steams", "steamed",
                        "steaming", "misted", "misty", "mist", "condensation", "blurred")),
          _spectacles_fog,
          # the car's windscreen has its own demisting answer, and the bathroom mirror its own
          avoid=("car", "windscreen", "windshield", "mirror", "bathroom", "window", "windows",
                 "phone", "camera", "lens", "wine")),
    # The thing and the problem are two parts of the key, not one list. With "kettle" and
    # "descale" in the same part, "how do i descale the kettle" matched one part and reached the
    # general scale answer in home.py, which matches "kettle" and "descale" in two.
    entry("descale-kettle", (("kettle", "kettles", "electric kettle"),
                             ("descale", "descaled", "descaler", "descaling",
                              "limescale", "scale", "scaled", "furred", "furring", "chalky",
                              "white bits", "white marks", "white stuff", "white flakes",
                              "clean", "cleaning", "rinsed", "rinse", "tastes", "inside",
                              # "hard water is ruining my kettle" names the thing and the harm,
                              # not the descale word. The harm is this row's only when the water
                              # is named too: a kettle ruined by boiling dry is the appliance row.
                              "hard water ruined", "hard water is ruining", "hard water ruining",
                              "hard water has ruined", "ruined by hard water",
                              "ruined by the hard water")),
          "Half fill the kettle with equal parts water and white vinegar, or a sachet of citric "
          "acid, boil it and leave it half an hour, then tip it out and boil fresh water twice "
          "before you use it again. In a hard-water area do it every couple of months: the scale "
          "forms because hard water leaves calcium behind as it boils, and a thick layer makes the "
          "kettle slow and puts a scum on the tea.",
          avoid=("toilet", "shower", "bath", "tap", "taps", "iron", "washing machine", "coffee",
                 "coffee machine", "dishwasher")),
    # The white scale is mostly asked about as a worry rather than a cleaning job: "is limescale
    # harmful", "is limescale bad for you" and "can limescale make you ill" were all a search
    # hedge on main, and the row that knows the answer keys "hard water" and stands down on the
    # word limescale so the descaling recipe can have it.
    entry("limescale-harmless",
          (("limescale", "lime scale", "scale in the water", "scale in water",
            "scale in my water", "chalky bits", "white bits in the water"),
           ("harmful", "bad for you", "bad for", "dangerous", "safe", "safely", "ill",
            "make you ill", "make me ill", "unhealthy", "healthy", "bad for my health",
            "a problem", "worry", "worried", "ok to drink", "safe to drink", "drink",
            "drinking", "fine", "ok", "okay", "why is")),
          "No: the white scale is calcium and magnesium carbonate, the same minerals that make "
          "water hard, and it is harmless to drink - mains water is tested to the same standard "
          "whatever its hardness. What it does do is cost money and taste: a scaled element "
          "takes longer to boil, and it leaves a scum on tea and a film on taps and shower glass. "
          "Descale the kettle every couple of months in a hard-water area. For a baby's bottle, "
          "use unsoftened mains water, boiled once and cooled.",
          # the cleaning job itself is the descale rows', and the health answer for hard water
          # in general is drinks.hard-water's
          avoid=("how do i", "how to", "get rid", "remove", "removing", "clean", "cleaning",
                 "descale", "descaling", "vinegar", "citric", "shower", "glass", "tap", "taps",
                 "kettle", "kettles", "washing machine", "dishwasher", "iron", "toilet",
                 "bath", "bathroom", "hard water")),
    # A ring on a finger is not a phone ringing, and a silver chain is not a bike chain. On main
    # "how do i clean my gold ring" and "how do i clean a diamond ring" reached the nuisance-calls
    # answer (its key holds "ringing", and "ring" is a form of it), "how do i clean a silver chain"
    # reached the bicycle chain ("chain" alone counts as proof of a bike in bikes.py), "my silver
    # necklace has gone black" reached the mould spray, and "how do i clean jewellery" was a shrug.
    # The metal is the key, not the word "clean", so a tarnish line arrives without asking how to
    # clean anything.
    entry("jewellery-clean",
          (("ring", "rings", "necklace", "necklaces", "bracelet", "bracelets", "earring",
            "earrings", "jewellery", "jewelry", "jewel", "jewels", "locket", "brooch",
            "bangle", "bangles", "pendant", "charm bracelet", "gold", "silver", "diamond",
            "diamonds", "white gold", "rose gold", "silverware", "silver cutlery",
            "silver spoon", "silver tray", "silver plate", "silver jewellery",
            # the phrases a person writes when the answer has to be the metal's: they carry the
            # entry past the nuisance-calls row, which reads "ring" as a form of "ringing"
            "gold ring", "silver ring", "wedding ring", "engagement ring", "diamond ring",
            "wedding band", "gold chain", "silver chain", "gold necklace", "silver necklace"),
           ("clean", "cleaning", "cleaned", "tarnish", "tarnished", "tarnishing", "gone black",
            "gone green", "turned my finger green", "dull", "dulled", "shine", "shiny",
            "polish", "polished", "wash", "washed", "brighter", "sparkle", "dirty", "grubby",
            "in the shower", "swimming", "marks", "scratched")),
          "Warm water, a drop of washing-up liquid and a soft brush, then dry it with a cloth: "
          "hand cream, hairspray and soap are what dull a gold ring. Silver that has gone black "
          "is tarnish, and a silver cloth, or a bowl lined with foil with a spoonful of "
          "bicarbonate of soda and boiling water for a minute, lifts it without scrubbing. No "
          "bleach on gold, and keep pearls and opals out of water.",
          # the other things with a ring, a chain or the word gold on them: a hob ring, a doorbell,
          # a bicycle, and the gold card that is a credit card
          avoid=("car", "cars", "van", "bike", "bicycle", "motorbike", "motorcycle", "tyre",
                 "tyres", "hob", "hob ring", "element", "cooker", "oven", "doorbell",
                 "door bell", "credit card", "gold card", "crown", "filling", "tooth",
                 "goldfish")),
    # Wax on a hard surface is a different job from wax on cloth: the iron-and-paper trick marks a
    # waxed table, and "how do i get wax off a table" was answered with how to POLISH it.
    entry("wax-table", (("wax", "candle wax"),
                        ("table", "worktop", "counter", "floor", "floorboards", "wood", "wooden",
                         "shelf", "windowsill", "stone", "tile", "tiles", "off", "remove")),
          "Let it harden completely - a bag of ice on it for 10 minutes speeds that up - then flick "
          "it off with a plastic card or a fingernail. For the film that is left, warm it with a hair "
          "dryer and blot it up with kitchen paper, or wipe it with a cloth wrung out in hot water "
          "and washing-up liquid, then re-polish the wood only where the wax was.",
          # wax on cloth or carpet is wax-candle's, with the iron and the kitchen paper
          avoid=("cloth", "tablecloth", "carpet", "rug", "sofa", "couch", "fabric", "duvet",
                 "curtain", "curtains", "clothes", "jumper", "shirt", "linen", "cushion")),
    # Oil on a drive is a job with cat litter and washing-up liquid, and it had no entry: "oil stain
    # on the drive" got the clothes trick, "engine oil on block paving" got the car-leak answer, and
    # "how do i clean oil off my driveway" was a shrug. The car keeps the question about the leak
    # that caused it, which is why the leak phrasing is left out here.
    # "drive" on its own matched the word "driving", so "is a diesel car good for town driving"
    # and "is a diesel car good for motorway driving" were answered with the paving job: diesel
    # plus a stem of "drive" was two signals. The surface is named in the phrases it is said in,
    # which a line about driving never contains.
    entry("driveway-oil", (("driveway", "drive way", "on the drive", "on my drive", "the drive",
                            "my drive", "block paving", "blockpaving", "paving",
                            "paving slabs", "patio", "concrete", "tarmac", "garage floor",
                            "car port", "carport", "parking space", "yard"),
                           ("oil", "engine oil", "diesel", "petrol", "grease", "stain", "stains",
                            "stained", "spill", "spilled", "spilt", "dripped", "drip", "leak",
                            "leaked", "mark")),
          "Soak up whatever is still liquid with cat litter, sand or sawdust, sweep it up, then "
          "scrub the mark with neat washing-up liquid and a stiff brush and rinse it away from the "
          "drains. A patch that has dried lifts with a paste of biological washing powder left on "
          "for an hour, or a degreaser from a motor shop. Do it soon: oil that has soaked into "
          "tarmac stays dark for good.",
          # "why is my car leaking oil" and "oil under my car" are the car's fault, not the paving
          avoid=("why", "leaking from", "under my car", "under the car", "my car is leaking",
                 "rocker cover", "sump", "olive oil", "hair oil", "oil paint", "essential oil",
                 "in the oven", "frying", "salad"),
          # a fabric row keys `oil` and `stain` too, so "how do i get oil stains off my patio" was
          # being told to wash it at the hottest temperature the label allows: where the line names
          # a surface outside the house, the paving answer is the one
          bias=1),
    # The shower head is the one thing people mean by "descale the shower", and it had no entry.
    entry("descale-shower", (("descale", "de-scale", "scale", "limescale", "furred", "furring",
                              "blocked", "spray"),
                             ("shower", "shower head", "showerhead", "shower screen", "shower door",
                              "nozzle", "nozzles", "trickle")),
          "Fill a freezer bag with white vinegar - half vinegar, half water if the chrome worries "
          "you - tie it over the shower head so the nozzles soak for an hour, then rub them with a "
          "sponge and poke any blocked holes with a pin. Run it hot for a minute afterwards. Once a "
          "month keeps it clear; in a hard-water area, do it every couple of weeks.",
          # what limescale IS and why a shower head has it belongs to the limescale entries,
          # which lead with the cause; this entry is the remedy that was missing
          avoid=("why", "because", "cause", "causes", "caused", "what is limescale", "limescale",
                 # hair in the trap is a blocked drain, not scale on the nozzles; "blocked" is
                 # in the key above, so "the shower is blocked with hair" used to land here
                 "hair", "hairs", "plug hole", "plughole", "drain", "trap"),
          # the head is this card and the glass is the soap-scum one: a line that says
          # "descale my shower head" was the generic limescale remedy once the hard-water
          # wording was added there, so the head leans in front
          bias=1),
    # Drying the dishes: the cooking table's "dry" answer was a dry piece of meat, and a tea
    # towel question is a kitchen question, not a plate that came out of the oven.
    entry("dry-dishes", (("dishes", "plates", "crockery", "cutlery", "pans", "pots", "bowls"),
                         ("dry", "drying", "dried", "towel", "tea towel", "rack", "air",
                          "streaks", "water marks")),
          "Stand them in a rack, spaced so the air gets round, and let them air-dry: a tea towel "
          "mostly moves the water about. If you do use one, wash your hands first and change the "
          "towel daily, because a damp cloth that sits out is where the germs come from. Glasses "
          "dry without streaks if they go in the rack upright and you do not top them up.",
          # A pan with nothing left in it is not a pan to dry: "i left the pan on and it boiled
          # dry" names a pan and says dry, which is this key's shape, and it was answered with a
          # dish rack while the pan was still on the ring.
          avoid=("dishwasher", "washing machine", "clothes", "laundry", "hair", "skin", "hands",
                 "paint", "nails", "car", "window", "mirror", "wine glass",
                 # a pot of soil is not a pan: "the soil in my pots is dry" was answered with a
                 # dish rack, because "pots" and "dry" are this key's shape
                 "soil", "soils", "compost", "garden", "garden soil", "plant", "plants",
                 "planted", "seedling", "seedlings", "raised bed", "flower bed", "border",
                 "lawn", "watering", "allotment",
                 "boiled dry", "boils dry", "boiling dry", "boil dry", "boiled away",
                 "left it on", "left the pan on", "left the pot on", "left on the hob",
                 "on the hob", "burnt", "burned", "on fire", "smoking")),
    # "can i put my pan in the dishwasher" was the honest shrug, and it is a short answer about
    # the metal and the mark on the base rather than a row that knows one pan.
    entry("dishwasher-cookware",
          (("pan", "pans", "saucepan", "saucepans", "pot", "pots", "wok", "skillet",
            "baking tray", "baking trays", "roasting tin", "roasting tins", "cake tin", "tin",
            "tins", "cookware", "cutlery", "knives", "knife", "chopping board", "board",
            "mug", "mugs", "casserole", "dish"),
           ("dishwasher", "dish washer", "dishwashers")),
          "Look for the dishwasher-safe mark on the base or the handle first: it is usually a "
          "glass-and-fork symbol, and most stainless steel pans, baking trays and everyday "
          "cutlery carry it. Keep out of the machine bare aluminium (it goes grey and pitted), "
          "copper, brass, cast iron and carbon steel (they rust or lose their seasoning), and "
          "anything with a wooden or glued handle. Most non-stick is better washed by hand, "
          "because hot alkaline water wears the coating, knives lose their edge knocking against "
          "other cutlery, and a wooden board will crack.",
          avoid=("not draining", "not emptying", "smell", "smells", "leaking", "leak", "salt",
                 "rinse aid", "cloudy", "filter", "buy", "best", "price", "cheap")),
]

# --- two everyday how-tos the deck sends and main answers with something else -----
# "how do i clean my air fryer" and "how do i clean the air fryer basket" reached
# `dishes.plan-ideas`, which answers "air fryer" and "how long" with the cook times: a person
# asking how to clean the basket was told how long chicken thighs take. The appliance is the
# same one, the question is not the same question, so cleaning it has its own entry and asks
# for the clean words before it fires.
ENTRIES.append(entry(
    "air-fryer-clean",
    (("air fryer", "airfryer", "air-fryer"),
     # The smell and smoke words are deliberately not here: they are `smoke-smell`'s and
     # `burnt-smell`'s keys, and a third entry using them makes them common inside this domain,
     # which demoted `smoke-smell` below the other one for "my clothes smell of smoke". The
     # cleaning verbs are enough for an air-fryer line.
     ("clean", "cleaning", "cleaned", "cleaner", "wash", "washing", "basket", "grease",
      "greasy", "crumbs", "crumb", "scrub", "dirty", "stains")),
    "Take the basket and the tray out and wash them in hot soapy water - most baskets are "
    "non-stick, so a soft sponge rather than a scourer. Wipe the inside of the drawer with a "
    "damp cloth and a little washing-up liquid, and use a brush or a wooden skewer to get the "
    "crumbs out of the element guard rather than tipping water over the top. Leave it open to "
    "dry before it goes back. For the baked-on grease, a paste of bicarbonate of soda and water "
    "left on for ten minutes lifts it without scratching; a wipe after every few uses stops it "
    "building up.",
    # The cooking side of the same appliance answers times and dishes, and the buying side is
    # "is an air fryer worth it": neither is a cleaning question.
    avoid=("how long", "how many minutes", "chips", "chicken", "salmon", "recipe", "worth",
           "worth it", "buy", "buying", "best", "which one", "cheaper", "run it", "electricity",
           "cost", "preheat", "frozen"),
    ask=("clean", "cleaning", "cleaned", "cleaner", "wash", "washing", "basket", "grease",
         "greasy", "crumbs", "crumb", "scrub", "dirty", "stains")))

# Folding bedding was a shrug: "how do i fold a fitted sheet", "how do i fold a sheet" and "how
# do i store bed sheets" all came back as "I'm not sure about that one". How often to wash them
# is `bedsheets-often`'s question, so this one asks for the folding or storing words first.
ENTRIES.append(entry(
    "fold-bedding",
    (("fitted sheet", "fitted sheets", "sheet", "sheets", "bed sheet", "bed sheets",
      "bedsheet", "bedsheets", "duvet cover", "duvet covers", "bedding", "pillowcase",
      "pillowcases", "linen"),
     ("fold", "folding", "folded", "store", "storing", "stored", "put away", "creases",
      "creases up", "wrinkles", "cupboard", "drawer", "airing cupboard")),
    "Put the two fitted corners inside each other, so the elastic of one corner is tucked into "
    "the corner opposite, then lay it flat and fold it in quarters with the elastic inside - it "
    "ends up as a neat rectangle instead of a bundle. Flat sheets and duvet covers fold in thirds "
    "lengthways first, then in halves, and a duvet cover can go over a hanger or be folded around "
    "its own pillowcase. Keep sets together inside one of their own pillowcases so you are never "
    "hunting for a matching pair.",
    # Washing, changing and drying bedding are their own entries; a stain or a bed size is not
    # a folding question.
    # "fit" is not in this list: "fitted" is a form of it, so an avoid on "fit" turned the
    # entry off for the very line it was written for ("how do i fold a fitted sheet").
    avoid=("wash", "washing", "washed", "often", "change", "change it", "how long", "stain",
           "stains", "bleach", "dry", "drying", "dryer", "tumble", "buy", "buying", "size",
           "thread count", "iron", "ironing", "mattress", "bed bug", "bed bugs"),
    ask=("fold", "folding", "folded", "store", "storing", "stored", "put away", "creases",
         "wrinkles", "cupboard", "drawer", "airing cupboard")))

# Clothes are the other half of the folding question, and "how do i fold clothes" and "how do i
# fold a t shirt" were both hedges: `fold-bedding` above is about bedding, and nothing answered
# a drawer of shirts. Folding a sheet and folding a jumper are different shapes, so they are
# different entries.
ENTRIES.append(entry(
    "fold-clothes",
    (("clothes", "clothing", "t shirt", "t shirts", "tshirt", "tshirts", "t-shirt", "t-shirts",
      "shirt", "shirts", "jumper", "jumpers", "sweater", "sweaters", "hoodie", "hoodies",
      "trousers", "jeans", "leggings", "dress", "dresses",
      "underwear", "socks", "pyjamas", "pajamas"),
     ("fold", "folding", "folded", "put away", "store", "storing", "drawer", "drawers",
      "wardrobe", "suitcase", "packing", "neat", "neatly", "tidily", "tidy", "crease",
      "creases", "creases up", "wrinkles", "wrinkled")),
    "Lay the t-shirt face down, fold one side in to the middle and the sleeve back along it, do "
    "the same on the other side, then fold it up in two or three from the hem: it ends up as a "
    "rectangle you can stack on its edge. Trousers go in half lengthways and then in thirds, and "
    "a jumper has its sleeves folded across the back before the sides come in, because a hanger "
    "stretches the shoulders. Standing the folded things up in the drawer rather than stacking "
    "them flat is what stops the pile collapsing, and it means you can see all of them at once.",
    # washing, ironing and drying are their own entries, and a lost sock or a stain is a
    # different question from how to fold what is already clean
    avoid=("wash", "washing", "washed", "iron", "ironing", "ironed", "dry", "drying", "dryer",
           "tumble", "stain", "stains", "bleach", "smell", "smells", "moth", "moths", "lost",
           "shrink", "shrunk", "bleed", "colour run",
           # putting a season away is not a folding shape: "how do i store clothes for winter"
           # was a t-shirt folded in a drawer, and the washing-mothing-box answer is clothing.py's
           "winter", "summer", "season", "seasons", "for winter", "for summer", "next year",
           "vacuum bag", "vacuum bags", "storage box", "storage boxes", "under the bed",
           "loft", "dry-clean", "dry clean"),
    # the crease words are in the key but not in the ask: "how do i get creases out of a shirt"
    # is a question about an iron or a steamer, and it was reaching this row on "creases"
    # before a folding word was ever in it
    ask=("fold", "folding", "folded", "put away", "store", "storing", "neat", "neatly",
         "tidily", "drawer", "drawers", "wardrobe")))

# "how do i stop socks losing their partner" was answered with a condolence card - "I'm so sorry",
# use the person's name - because the only thing the matchers saw was a partner being lost. A sock
# that comes out of the wash alone is a laundry question with two or three known places to look.
ENTRIES.append(entry(
    "lost-socks",
    (("sock", "socks", "pair of socks", "pairs of socks", "odd socks", "matching socks",
      "one sock", "a sock"),
     ("lost", "lose", "losing", "loses", "disappear", "disappears", "disappearing", "missing",
      "went missing", "gone missing", "partner", "odd", "matching", "match", "pair up",
      "find", "keep", "in the wash", "washing machine", "tumble dryer", "dryer")),
    "Clip each pair together or put them in a mesh washing bag before they go in. When one goes "
    "missing, check the door seal first: the fold of the rubber is where most singles end up. Then "
    "the filter, under the drum paddles, and inside a duvet cover or a trouser leg. Keep the "
    "orphans in a bag and pair them up a month later.",
    # a death, a divorce and a partner who has gone are the consolation cards, and a lost sock is
    # not one of them: no sock in the line means this row never fires
    avoid=("died", "death", "passed away", "funeral", "bereave", "grief", "miss him", "miss her",
           "left me", "walked out", "divorce", "separated", "broke up", "break up", "boyfriend",
           "girlfriend", "husband", "wife", "fiance", "widow",
           # how to wash, dry or fold a sock is the care label, not a missing one
           "wool", "woollen", "hand wash", "how do i wash", "how to wash", "bleach", "stain",
           "stains", "mud", "white", "smell", "smelly", "shrink", "shrunken", "dry", "drying",
           "fold", "folding", "tights", "laddering", "delicate", "colour", "colours"),
    bias=2))

# --- cleaning a thing that has a motor, a plate or a grille -------------------
# These are the everyday "how do i clean the X" lines that reached a fault answer or a shrug.
# A fan, a coffee machine and an iron each name their own machine, so they are keyed on the
# machine plus what is wrong with it (dust, scale, sticking), never on the word "clean" alone.
ENTRIES.append(entry(
    "clean-fan",
    # every key here names a fan, and the parts only ever arrive with the fan in the phrase.
    # A bare part was too wide: "blade" on its own is a blender, a knife and a lawnmower, and
    # "cage" is a budgie's and a hamster's, and the loose forms made "blades" match too.
    (("fan", "fans", "ceiling fan", "ceiling fans", "desk fan", "desk fans", "pedestal fan",
      "floor fan", "tower fan", "fan blades", "fan blade", "fan grille", "fan guard",
      "fan cage", "blades of the fan", "blades of a fan", "blades of my fan",
      "extractor fan", "extractor fans", "bathroom fan", "kitchen fan", "box fan",
      "wall fan", "clip fan", "air circulator"),
     ("clean", "cleaning", "cleaned", "dust", "dusty", "dusted", "wipe", "wiping", "washing",
      "wash", "filthy", "dirty", "grimy", "grubby", "black dust")),
    "Unplug it first, then slide a pillowcase over each blade and pull it off with the dust "
    "inside, or wipe the blades with a barely damp cloth and dry them, because a wet blade "
    "traps dust. Vacuum the grille with the brush tool and wipe the guard with a damp cloth; a "
    "ceiling fan gets the same treatment with a step ladder and a cloth over the motor housing "
    "so nothing drops into it. Leave it all dry before it goes back on.",
    # a noisy fan is `home.appliance-noise`, a hot laptop is a computer, and a room fan that
    # smells is a fault: only the cleaning question belongs here
    avoid=("noise", "noisy", "hum", "hums", "humming", "rattle", "rattles", "rattling",
           "squeak", "squeaks", "squeaking", "squeal", "squeals", "squealing", "grind",
           "grinds", "grinding", "click", "clicking", "loud", "louder", "tinnitus", "ears",
           "hearing", "burning", "smell", "smells", "smelly", "smoke", "smoking", "wont turn",
           "won't turn", "wont spin", "stopped working",
           "oven", "oven fan", "extractor", "cooker hood", "hob", "microwave", "air fryer",
           "laptop", "computer", "pc", "macbook", "phone", "xbox", "playstation", "console",
           "car", "van", "engine", "radiator", "boiler", "heater", "air con", "aircon",
           "dehumidifier", "tumble dryer", "washing machine", "dishwasher",
           # a fan's filter is a filter question, not a blade one: the air purifier and the
           # bathroom extractor both name a fan and both want the change-the-filter answer
           "filter", "filters", "air purifier", "purifier", "purifiers", "hepa")))

ENTRIES.append(entry(
    "clean-coffee-machine",
    (("coffee machine", "coffee machines", "espresso machine", "espresso", "nespresso",
      "bean to cup", "coffee maker", "filter machine", "coffee pod machine", "pod machine",
      "group head", "portafilter", "steam wand", "milk frother"),
     ("clean", "cleaning", "cleaned", "descale", "descaling", "descaler", "limescale", "scale",
      "scaled", "rinse", "rinsing", "smell", "smells", "smelly", "mould", "mold", "bitter",
      "sour", "tastes", "tasting", "blocked", "clogged", "slow")),
    "Run a descaler through it: fill the water tank with a citric-acid descaler (or half white "
    "vinegar, half water), run half of it through the machine with no coffee in it, switch off "
    "for 20 minutes, then finish the tank and run two tanks of plain water through after it. "
    "Every week, backflush the group head or rinse the pod holder and leave the drip tray and "
    "the steam wand wiped - the wand wants a damp cloth straight after the milk, and the "
    "portafilter basket comes up clean in hot soapy water.",
    avoid=("buy", "buying", "which", "best", "recommend", "under", "budget", "cheap",
           "broken", "wont turn on", "won't turn on", "not heating", "leaking", "leak",
           "grinder", "bean", "beans", "frother only")))

ENTRIES.append(entry(
    "clean-iron",
    (("iron", "irons", "steam iron", "soleplate", "sole plate"),
     ("clean", "cleaning", "cleaned", "descale", "descaling", "sticking", "sticks", "stuck",
      "burnt", "burned", "brown", "scorch", "scorched", "marks", "mark", "scale", "limescale",
      "scum", "white bits", "spitting", "dirty", "crusty")),
    "Let it go cold, then rub the soleplate with a paste of bicarbonate of soda and a little "
    "water on a damp cloth, or lay a cloth soaked in white vinegar on the plate for half an "
    "hour, and wipe it off with a dry cloth - never a scourer or a knife, which takes the "
    "coating off. For white flakes and spitting, fill the tank half and half with water and "
    "white vinegar, let it steam itself empty over a basin, then run a tank of plain water "
    "through; empty the tank after every use so the scale never gets going.",
    # pressing a shirt is `clothing.iron-shirt`, a scorched garment is `clothing.iron-scorch`,
    # and a cast-iron pan is the kitchen's: this entry is the appliance only
    # "ironing" cannot go in this list: the loose forms of "ironing" include "iron", so the entry
    # would avoid its own subject word and never answer anything ("how do i clean an iron" was a
    # hedge until it came out). The board goes in by name instead.
    avoid=("shirt", "shirts", "trousers", "blouse", "dress", "crease", "creases",
           "ironing board", "board", "press", "pressing", "steam my", "cast iron", "pan", "pans",
           "wok", "skillet", "griddle", "golf", "gym", "weights", "hair", "curling",
           "straighteners", "wont heat", "won't heat", "not heating", "stopped heating",
           "leaking", "fuse", "plug")))
ENTRIES.append(entry(
    "clean-headphones",
    (("headphones", "headphone", "earbuds", "ear buds", "earphones", "ear phones", "airpods",
      "in ears", "earphones case"),
     ("clean", "cleaning", "cleaned", "wax", "waxy", "dirty", "smell", "smells", "smelly",
      "sanitise", "sanitize", "disinfect", "gunk", "sticky", "dusty", "gross")),
    "Pop the silicone tips off and wash them in warm soapy water, then dry them completely "
    "before they go back on - a cotton bud barely damp with water cleans the mesh, and a dry "
    "soft toothbrush lifts the wax out of the nozzle. Wipe the outside with a cloth with a "
    "little washing-up liquid on it, keep water out of the charging port and the microphone "
    "holes, and replace the tips every few months because the rubber holds the smell.",
    avoid=("lose", "lost", "broken", "wont charge", "won't charge", "not charging", "one side",
           "warranty", "buy", "which", "best", "noise cancelling", "volume", "pair", "connect",
           # "ear wax" is not avoided: wax in the earbud is the question, and a key word only
           # fires when the line names the headphones anyway
           "bluetooth", "hearing aid", "ear infection", "earache", "ear ache")))

# A barbecue is cleaned on the grill, not in a sink, and every one of these was a shrug: "how do
# i clean a barbecue", "how do i clean the bbq grill", "how do i clean burnt bits off a bbq",
# "how do i get rust off a bbq" and "how do i look after a barbecue over winter" all came back
# as the honest punt. One row, because it is one job with two ends to it.
BBQ_MAIN = (
    "A hot barbecue mostly cleans itself: leave it on full for fifteen minutes, then brush the "
    "warm grate with a stiff wire brush and a half onion or potato held in tongs. Anything baked "
    "on lifts after an hour under a paste of bicarbonate of soda and water. Wipe the ash out "
    "when it is cold, and oil the grate with a little vegetable oil on kitchen paper.")
BBQ_RUST = (
    "Rust on a grate is surface rust and comes off: scrub it with a wire brush or crumpled foil, "
    "wash it, dry it over the heat for a few minutes, then oil it while it is still warm - that "
    "oil layer is what keeps the rust from coming back. A pitted grate that flakes is one to "
    "replace.")
BBQ_WINTER = (
    "Before it goes away for winter, burn off the grate, brush it, empty the ash tray and wipe "
    "the inside with hot soapy water. Dry it properly - a covered damp barbecue is what rusts - "
    "then oil the grate, and if it is a gas one take the bottle off and store it upright outside. "
    "A cover that breathes is better than a plastic sheet tied tight.")


def _clean_bbq(memory, understood):
    """Rust, winter, or the ordinary clean, whichever the line is about."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if "rust" in said or "rusty" in said:
        return BBQ_RUST
    if any(word in said for word in ("winter", "store", "storing", "put it away", "cover",
                                     "covering", "end of the season")):
        return BBQ_WINTER
    return BBQ_MAIN


ENTRIES.append(entry(
    "clean-bbq",
    # a bare "grill" is the one in the cooker as often as the one in the garden ("how do i clean
    # the grill" was this row), so the barbecue has to be named: the grill word comes with it
    (("barbecue", "barbecues", "barbeque", "bbq", "bbqs", "barbie", "barbecue grill",
      "bbq grill", "gas grill", "charcoal grill", "kettle grill", "grill in the garden"),
     ("clean", "cleaning", "cleaned", "cleaner", "wash", "washing", "scrub", "scour",
      "burnt", "burnt on", "burned on", "black bits", "rust", "rusty", "winter", "store",
      "storing", "put away", "look after", "look after it", "grease", "greasy", "ash")),
    _clean_bbq,
    # cooking on it is the cooking rows' question, and a grill in an oven is a different
    # cleaning job from a grill out in the garden
    avoid=("steak", "steaks", "chicken", "sausage", "sausages", "burger", "burgers", "fish",
           "salmon", "meat", "kebab", "halloumi", "vegetarian", "vegan", "how long", "how many "
           "minutes", "temperature", "recipe", "marinade", "marinate", "cook", "cooking",
           "cooked", "charcoal or gas", "which barbecue", "best barbecue", "buy", "buying",
           "oven", "pan", "pans", "grill pan", "hob", "toast", "cheese on toast", "bacon",
           # what to do about burnt food *on the plate* is the eating question, and its own
           # row answers it: "what about burnt bbq food" was told how to clean the grate.
           "eat", "eating", "ate", "still eat", "safe to eat", "can i eat", "is it safe",
           "still ok to eat", "bad for", "harmful", "cancer", "healthy",
           "burnt food", "burned food", "charred food", "bbq food", "barbecue food"),
    bias=1))

# --- a mark on a hard surface ----------------------------------------------
# The everyday mark on a worktop, a sink, a tile or a fridge door had no answer at all: "white
# marks on my worktop" and "brown marks on the sink" got "I'm listening", and the hard-water
# line went to board-smell ("scrub it with half a lemon") because a worktop and a stain were
# both its words, and that answer is about onion and garlic in wood. The mark itself is the
# question, and what it is made of is the answer: scale from the water is not a scuff and
# neither is a burn, and a person can tell them apart by looking.
ENTRIES.append(entry(
    "surface-mark",
    (("mark", "marks", "marked", "stain", "stains", "stained", "ring", "rings", "scuff",
      "scuffs", "residue", "water mark", "water marks", "heat mark", "heat marks",
      "white marks", "brown marks", "hard water stains", "hard water stain", "chalky marks",
      # A pan set down on the worktop leaves a mark of its own, and the pan-cleaning row was
      # taking it: "my hot pan scorched the counter" and "the pan was so hot it burnt the
      # worktop" were both told to simmer bicarbonate of soda in the pan.
      "scorch", "scorched", "scorching", "burn mark", "burn marks", "burnt the worktop",
      "burnt the counter", "scorched the worktop", "scorched the counter",
      "melted the worktop", "melted the counter", "white mark", "hot pan", "hot tray",
      "hot pot"),
     ("worktop", "worktops", "counter", "countertop", "counter top", "sink", "sinks",
      "draining board", "tile", "tiles", "splashback", "splash back", "fridge",
      "freezer", "cupboard", "cupboards", "shelf", "shelves", "shower screen", "window")),
    ("Wipe the surface with washing-up liquid first, then look at what is left. A white, chalky "
     "bloom is scale from the water: leave a cloth soaked in white vinegar on it for ten minutes "
     "and rinse. A brown or grey mark is metal rubbed off a pan or a tin, and a big pinch of salt "
     "on half a lemon, rubbed along the surface, lifts it. A dark ring that will not shift and "
     "feels slightly rough is a burn in a laminate top, which no cleaner will take out - and keep "
     "abrasive pads off laminate and quartz, because the scratch they leave stays."),
    # the fault is the mark, not the fitting: a sink that smells, will not drain or is cracked is
    # a different answer (cleaning and home.py both hold them), and scale on a tap or in a kettle
    # is limescale-why's, which knows about citric acid and a bag tied round the spout
    avoid=("blocked", "blockage", "blocking", "unblock", "plunger", "drain", "drains",
           "draining", "smell", "smells", "smelly", "stink", "stinks", "mould", "mold",
           "mildew", "cracked", "crack", "cracks", "chip", "chipped", "leak", "leaks",
           "leaking", "limescale", "descale", "scale", "scaled", "tap", "taps", "kettle",
           # "burnt" used to stand this row down, which sent every scorch on a worktop to the
           # pan-cleaning row; only a burnt hob is somebody else's answer now
           "burnt hob", "burnt ring", "burnt on the hob", "burner",
           "rust", "rusty", "scratch", "scratches", "scratchy",
           "paint", "painted", "peeling", "handle", "handles", "door", "doors", "hinge",
           "grout", "sealant", "silicone", "silicon", "replace", "fit", "install", "moving",
           # a hob has its own answer (hot soapy water, and bicarbonate for a burnt-on ring) and
           # it beat this row's generic one, so it keeps the line
           "hob", "hobs", "cooker", "burners", "hot plate",
           # where a hot thing can be set down is a placement question, and the mark is the
           # damage: "can i put a hot pan on the worktop" and "i put the hot pan on the worktop"
           # were both told how to clean a mark that had not happened yet
           "can i put", "can i set", "can i stand", "where do i put", "where can i put",
           "where should i put", "i put", "i placed", "i set", "i stood", "i rested",
           "put the hot", "placed the hot", "set the hot", "stood the hot", "rested the hot",
           "put it on", "placed it on", "set it on", "what happens", "is it ok to put",
           "is it safe to put",
           # A mark on a window is scale, and this row keeps it; a mark round a window frame is
           # black mould, which has its own row, so the colour and the mould words stand this one
           # down. "black marks round the window" was being offered vinegar for a worktop.
           "black marks", "black spots", "black mould", "black mold", "dark marks",
           "green marks", "green mould", "mould", "mold", "wall", "walls", "ceiling",
           "ceilings", "corner", "corners"),
    bias=2))

# --- a mark off a wall, and how long paint smells ---------------------------
# "how do i get a mark off the wall" got the search hedge and "there are scuff marks on the wall"
# A skirting board is the thing in a room that collects the most dust and gets cleaned the
# least, and nothing answered it: "how do i clean skirting boards" was the chopping-board
# answer, half a lemon and salt on wood. It is a painted ledge, so it wants a brush and a
# barely damp cloth, and it wants doing before the floor.
ENTRIES.append(entry(
    "skirting-clean",
    (("skirting", "skirting board", "skirting boards", "skirting boards and door frames",
      "skirting and architrave", "architrave", "door frames", "kick board", "kickboards",
      # the painted wood of a room is the same job as the skirting is
      "woodwork", "painted woodwork"),
     # the cleaning words are the ask, not the word "how": "how" in a key group takes every
     # how-to that names the thing, which is how "how do i cut a mitre in skirting board" was a
     # dusting answer. A line about a board wants a word about cleaning one.
     ("clean", "cleaning", "cleaned", "wash", "washing", "wipe", "dust", "dusting", "dirty",
      "grimy", "sticky", "yellow", "yellowed", "white", "whiten", "whitening", "grubby",
      "scuffed", "marks",
      # "make them look new" is the shape of the ask rather than a cleaning verb, and without it
      # the row had nothing to answer with when someone wanted a board refreshed, not fitted:
      # "how do i make skirting boards look new" was a search hedge, and the fitting row's "new"
      # took it before that
      "look new", "looks new", "look like new", "looks like new", "look brand new",
      "refresh", "refreshing")),
    ("Dust them first with a soft brush or the vacuum's brush head, then wipe with a cloth wrung "
     "out in warm water and a drop of washing-up liquid, and dry as you go so the water does not "
     "sit on the join with the floor. Do the top edge, the front and the groove on the way past. "
     "A melamine sponge takes scuffs off, but gently, because the paint film on a skirting is "
     "thin. Never wet an MDF one: it swells, and no amount of drying brings it back."),
    # a line about painting, filling or mould on a skirting board is another answer; so is a
    # mark on one, which the wall-mark row takes with its melamine sponge
    # "painted" is not in this list, though the paint job is: it describes the board ("clean
    # painted skirting boards") and that is this row's work, while "painting" and "paint" say the
    # paint is what the line is about ("im painting the skirting boards white" wants the sanding
    # and masking card, not a duster).
    avoid=("mould", "mold", "mildew", "damp", "dripping", "leak", "leaking",
           "paint", "paints", "painting", "repaint", "repainting", "primer", "undercoat",
           "gloss", "emulsion", "sanding", "sand", "filler", "fill", "caulk",
           "paint off", "get paint off", "getting paint off", "clean paint off", "strip",
           "stripper", "remove", "removing", "replace", "replacing", "fit", "fitting",
           "install", "installing", "skirting heater", "heater",
           # the joinery verbs are still here because "fit" and "replace" already were: they are
           # the words the fitting row in home.py is keyed on, so the two rows cannot both claim
           # the same board
           "cut", "cutting", "mitre", "mitred", "miter", "cope", "coping", "fix", "fixing",
           "screw", "screws", "nail", "nails", "put up", "putting up", "plasterboard"),
    # A shade above the paint-prep row, which keys the same board: "how do i get skirting boards
    # white again" is a cleaning question, and the joinery and the painting lines are each fenced
    # off above, so nothing else competes for this row.
    bias=1))

# got "Got it", while a crayon, a pencil and black marks on a wall were already answered (the
# crayon row, and the mould row for black spots), so the wall had answers for everything except
# the ordinary mark. Paint thinner than it looks is the whole trick here: a scrubbed patch shows
# in the light worse than the mark did.
ENTRIES.append(entry(
    # Two rows cannot share an id: `tests/test_knowledge_load` reads every domain and refuses a
    # repeated id, and the older `wall-mark` above is the one a line about a scuff on a wall
    # reaches first. This row is the damp-cloth-and-melamine answer, so it keeps the words a
    # person says ("mark on the wall", "mark off a door") under a name of its own.
    "mark-on-a-wall",
    (("mark", "marks", "marked", "scuff", "scuffs", "scuffed", "fingerprint", "fingerprints",
      "hand print", "hand prints", "smudge", "smudges", "stain", "stains", "dirty mark",
      "dirty marks", "marks on the wall", "mark on the wall"),
     ("wall", "walls", "paintwork", "painted wall", "painted walls", "skirting",
      "skirting board", "skirting boards", "ceiling", "banister", "door", "doors",
      "door frame", "door frames", "painted door", "painted doors")),
    ("A damp cloth with a little washing-up liquid takes off most marks, and a melamine sponge "
     "used gently with water lifts a scuff without cutting through the paint. Do not scrub hard: "
     "the paint film is thinner than it looks, and a shiny patch where you scrubbed shows in the "
     "light more than the mark did. If the mark has gone through to the plaster, or the paint has "
     "flaked, it is a touch-up rather than a clean, and it needs the same paint in the same finish "
     "or the patch shows."),
    # crayon, pencil and pen already have their row; black spots on a wall are mould, a damp wall
    # is condensation, and stripping wallpaper or painting a room is a different job again
    # "painting", "decorate" and "strip" are deliberately NOT here: avoid matches word forms, so
    # "marks on the painted wall" was being knocked out by "painting", and a mark on a wall that
    # has paint on it is exactly the line this row is for. A line that asks how to paint a wall
    # never has a mark word in it, so this row cannot take it anyway.
    avoid=("crayon", "crayons", "pencil", "pencils", "biro", "pen", "felt tip", "felt-tip",
           "felt tips", "chalk", "marker", "mould", "mold", "mildew", "damp", "condensation",
           "black spots", "black marks", "wallpaper", "stripping", "filler", "hole", "holes",
           "crack", "cracks", "cracked", "peel", "peeling", "flaking", "blister", "blistering",
           "plaster", "plasterboard", "skim", "leak", "leaking", "dripping", "tile", "tiles",
           "grease",
           # and a ceiling is not a wall to wipe: whatever marked it came from above, which is
           # damp-patch-ceiling's question, and a melamine sponge is not the answer to water.
           # The gate is the ceiling and panic words only, and NOT the colour: a colour is not
           # only a ceiling word, so a colour here stood this row down with nothing to take its
           # place - "yellow stain on the wall" and "brown stain on the wall" fell through to a
           # stall while this card was the right answer. A coloured mark on a CEILING is held out
           # by the ceiling word, which is the word that actually says the water came from above.
           "ceiling", "ceilings", "ceiling mark", "ceiling stain", "above", "upstairs"),
    bias=1))

# The smell of fresh paint is a question people ask in the first week of a job, and nothing
# answered it: "how long does paint smell last" got the search hedge.
ENTRIES.append(entry(
    "paint-smell",
    (("smell", "smells", "smelly", "fumes", "stink", "lingering smell", "chemical smell"),
     ("paint", "painted", "painting", "gloss", "eggshell", "emulsion", "varnish", "primer",
      "undercoat", "wood stain", "woodstain")),
    ("New paint smells for three to five days, and up to two weeks for an oil-based gloss: the "
     "solvent has to leave, and warmth with a window open is what carries it away. Air changes do "
     "the work, so prop the door and put a fan in the doorway rather than sealing the room up. If "
     "a smell is still there after a fortnight, or the room gives you headaches, ventilate harder "
     "and see a GP if it goes on, because a lingering solvent smell is a ventilation problem."),
    # a smell of damp, of a drain or of a dead mouse in a wall is not paint, and neither is a
    # paint that will not dry or a wall that is wet
    avoid=("damp", "musty", "drain", "drains", "sewer", "mould", "mold", "mildew", "dead",
           "mouse", "mice", "rot", "wet", "leak", "leaking", "boiler", "gas")
          # a smell from a ferment, a bin or a fridge is that thing's answer, and the words
          # nail, varnish and remover in a line about a sourdough starter are the smell it is
          # being compared to, not a tin of gloss
          + FOOD_SUBJECT,
    bias=1))


# The home-wear branch: these four were echoes or punts on main.
ENTRIES.extend([
    # "maggots in my bin" was "Noted: maggots in your bin", and a bin of flies got the fruit-fly
    # trap meant for a bowl of fruit. Flies lay in the food waste, not in the plastic, so the
    # answer is to kill what is there and then stop the next lot.
    entry("bin-maggots",
          (("bin", "bins", "bin bag", "kitchen bin", "wheelie bin", "caddy", "food waste"),
           ("maggots", "maggot", "grubs", "maggoty", "maggoty", "flies", "fly", "maggot farm")),
          "Pour a kettle of boiling water over them, or a jug of water with a good splash of bleach, "
          "then wash the bin out, dry it and put a fresh bag in. The flies lay in the food waste "
          "rather than in the plastic, so keep wet scraps in a sealed caddy or a bag in the fridge "
          "and take it out daily in warm weather; a lid that shuts properly and a dry bin stops it "
          "coming back.",
          avoid=("compost", "compost bin", "caddy for compost", "garden waste", "recycling")),
    # Washing a bath mat is the row above. A mat that will not stay put is a different job, and
    # "how do i stop my bath mat sliding" was a punt while "my bath mat is slippy" was an echo.
    entry("bath-mat-grip",
          (("bath mat", "bath mats", "shower mat", "bathroom mat", "mat"),
           ("slippy", "slippery", "sliding", "slides", "slips", "slid", "moves", "moving",
            "wont stay", "won't stay", "keeps sliding", "grip", "grippy", "secure", "stays put")),
          "A rubber-backed mat slips once the backing is wet, worn or filmed with soap, so the fix "
          "is suckers pressed onto a clean dry floor, or a cheap anti-slip underlay cut to size. "
          "Wash and dry the tiles first: soap film is what most of these slips come from. If the "
          "backing has gone smooth or hard it will not grip again and the mat wants replacing - a "
          "slick mat on a tiled floor is how people end up at the hospital with a wrist.",
          # the row above has the washing, and a door mat, a rug or a yoga mat is another question
          avoid=("smell", "smells", "clean", "cleaning", "wash", "washing", "machine", "mould",
                 "door", "door mat", "welcome mat", "rug", "carpet", "yoga", "desk", "mouse")),
    # Washing a duvet is the row above; this is the other question, how long the thing lasts and
    # what to do when it has gone flat or lumpy. All three were echoes or punts: "my pillow is
    # flat", "my duvet is lumpy", "my mattress sags", plus "should i replace my pillow" ("Can't
    # call that one for you") and "how long should a mattress last".
    entry("bedding-life",
          (("pillow", "pillows", "duvet", "duvets", "quilt", "quilts"),
           ("flat", "flattened", "flattening", "lumpy", "lumps", "clumped", "bunched", "sagging",
            "sags", "sag", "dip", "dips", "dipped", "worn out", "worn", "replace", "replacing",
            "replacement", "how long", "last", "lasts", "lifespan", "spring back", "loft", "bumpy",
            "change", "changing", "how often")),
          _bedding_life,
          # washing, stains and spills are the rows above and below, and buying one is shopping's
          avoid=("wash", "washing", "machine", "clean", "cleaning", "stain", "stains", "spill",
                 "accident", "smell", "smells", "yellow", "cover", "covers", "case", "pillowcase",
                 "sheet", "sheets", "buy", "buying", "cost", "costs", "price", "cheap", "cheapest",
                 "which", "best", "memory foam", "topper", "protector", "cot", "cotbed", "baby",
                 # a mattress has its own answer on main now ("eight to ten years"), which this
                 # entry must not take: "how long should a mattress last" is that row's question
                 "mattress", "mattresses")),
    # Mould is the row above; this is the wood itself going wrong. Three lines had nothing at all:
    # "my chopping board is splitting" was "Got it. Is there anything you'd like a hand with?",
    # "my wooden spoons are drying out" an echo, and "should i oil my wooden spoons" the decision
    # hedge ("That's your call, not mine"), which is the worst of the three for a yes/no job.
    entry("wood-care",
          (("wooden spoon", "wooden spoons", "wooden spatula", "spoon", "spoons", "wooden",
            "chopping board", "wooden board", "wooden chopping board", "utensils", "utensil",
            "rolling pin", "wood"),
           ("rough", "fuzzy",
            "drying out", "dried out", "dry out", "oil", "oiling", "oiled", "care", "look after",
            "dishwasher", "season", "sanding", "sand it", "gone dry")),
          "Wash it by hand in hot soapy water and stand it up to dry, and rub in food-safe mineral "
          "oil or board butter once a month, left on for an hour and buffed off - never cooking "
          "oil, which goes rancid. Wood splits because it has been soaked or dishwashered and then "
          "dried too fast, and a rough, dry surface is the stage before that. A hairline crack is "
          "fine to keep if you sand the edges smooth; a split that will not close harbours bacteria "
          "and wants a new one. Keep it out of the dishwasher and it lasts years.",
          # the row above answers mould on wood, and a floor, a table or a fence is other work
          avoid=("mould", "mouldy", "mold", "moldy", "mildew", "musty", "black", "gone green",
                 "floor", "floors", "flooring", "decking", "deck", "fence", "furniture", "table",
                 "chair", "door", "window", "garden", "bread", "cheese", "lemon", "wall", "paint",
                 "varnish", "scratch", "scratches",
                 # a board that has split and a spatula with a crack already have their own card,
                 # and it names the cause before the cure: "a wooden board splits because it has
                 # dried out" is the answer to "my chopping board is splitting", where this row's
                 # routine care is the second-best reply. The fault words are held out so those
                 # lines keep the card that explains the fault.
                 "splitting", "split", "cracked", "cracks", "cracking", "warped", "warping")),
])

# A bird's mess on a thing is a cleaning job, and the vet row in the fallback took it: "how do i
# clean bird poo off my patio" and "how do i get bird poo off my washing" were answered with a
# call to the vet's desk, because a bird is an animal and a mess is a symptom. The germ warning
# is the part a person does not know, so it leads.
ENTRIES.append(entry(
    "bird-mess",
    (("bird poo", "bird poop", "bird mess", "bird muck", "bird droppings", "bird dirt",
      "bird lime", "pigeon poo", "pigeon poop", "pigeon mess", "pigeon droppings", "guano",
      "seagull poo", "bird crap"),
     ("patio", "path", "paving", "decking", "deck", "fence", "wall",
      # the paint on a car takes it differently from a patio: a wet cloth and no scrub
      "car", "cars", "van", "bonnet", "bodywork", "roof",
      "washing", "washing line", "clothes", "laundry", "barbecue", "bbq", "garden furniture",
      "table", "bench", "balcony", "terrace", "railing", "railings", "sill", "windowsill",
      "awning", "steps", "step", "greenhouse", "shed", "conservatory")),
    "Wear gloves and keep it off your skin: bird mess can carry germs, so wash your hands after "
    "and keep it away from food, a cut or your face. Soak it with hot soapy water, leave it a "
    "minute to soften, then scrub with a stiff brush and rinse, rather than scrubbing it dry "
    "into the surface. On washing, a hot wash with detergent is enough. On car paint, let a wet "
    "cloth sit on it for a minute and wash the panel after - never scrape at it.",
    # the car has its own answer (paint, a wet cloth rather than a scrape), and a sick bird is
    # the vet's line, not a cleaning job. The car words are left out of the key rather than
    # avoided, so "bird poo on the car" and "on the patio" do not fight over the same line.
    # a window already has its own glass answer, and it is the better one for a smear.
    avoid=("sick", "ill", "dying", "dead", "injured", "hurt", "rescue", "feed", "food",
           "nest", "egg", "eggs", "cage", "aviary", "my bird", "bird bath", "bird feeder",
           "window", "windows", "glass", "mirror", "windscreen")))


# The hard surfaces outside the house had no cleaning answer at all: "how do i clean my patio",
# "how do i clean the paving slabs", "how do i clean decking" and "how do i pressure wash a
# driveway" were all shrugs, while the only entry that named those surfaces was the oil stain. So
# the surfaces are the first group here and the cleaning words the second, and the oil words are
# left out: an oil stain is `driveway-oil`'s, which says what to do with a mark rather than a wash.

OUTSIDE = ("driveway", "drive", "drop kerb", "patio", "patio slabs", "paving", "paving slabs",
           "block paving", "blockpaving", "pavers", "decking", "deck", "deck boards", "path",
           "garden path", "terrace", "yard", "back yard", "concrete", "tarmac", "carport",
           "car port", "garage floor", "front steps", "steps", "stone flags", "flags",
           "brick paving", "cobbles", "slab", "slabs", "blocks", "paving stones")

# the oil card keeps the marks: a wash is not the answer to diesel that has soaked in
OUTSIDE_STAINDOWN = ("oil", "oils", "engine oil", "diesel", "petrol", "grease", "fuel",
                     "weedkiller", "paint", "cement", "render", "mortar", "blood", "vomit",
                     "dog mess", "bird mess", "bird poo", "poo", "resin", "tar spot",
                     # a snowy drive is cleared with a shovel, not washed
                     "snow", "snowed", "ice", "icy", "black ice", "grit", "gritted", "salt",
                     # a thing that stands on a patio is not the patio: a table, a bench and a
                     # parasol are washed or wiped by hand, and "clean my patio table" was a hedge
                     # until "patio" alone reached the pressure washer
                     "table", "tables", "chair", "chairs", "bench", "benches", "seat", "seats",
                     "umbrella", "umbrellas", "parasol", "parasols", "heater", "chiminea",
                     "planter", "planters", "pot", "pots", "trough", "troughs", "swing",
                     "hot tub", "door", "doors", "gate", "gates")

ENTRIES.append(entry(
    "outside-clean",
    ((OUTSIDE),
     ("clean", "cleaning", "cleaned", "wash", "washing", "scrub", "scrubbing", "jet wash",
      "jetwash", "pressure wash", "pressure washer", "power wash", "power washer", "hose down",
      "dirty", "filthy", "grubby", "grimy", "grime", "slime", "how do i get it clean",
      "looks dirty", "needs a clean", "washing down")),
    "Sweep it first, then wash: on block paving or concrete a pressure washer does most of it, "
    "keeping the nozzle moving and working down the slope so the dirty water runs off rather than "
    "back over what you have done. On decking keep the pressure low and go along the grain, "
    "because a hard jet furries softwood. A small patio is quicker with hot water, a splash of "
    "washing-up liquid and a stiff brush, then a rinse with the hose. Do it on a dull day so the "
    "soap does not dry before you rinse, and keep the spray off plants, open windows and next "
    "door's paintwork.",
    avoid=OUTSIDE_STAINDOWN + (
        # a lawn, a flower bed and a window are their own answers, even when a path is named
        "lawn", "grass", "moss", "algae", "weeds", "weed", "flower bed", "borders", "gutter",
        "guttering", "window", "windows", "glass", "windscreen", "bbq", "barbecue",
        "furniture", "cover", "cushion", "shed", "fence", "paint", "car", "van")))

# --- a mark on the carpet, the rug or the sofa --------------------------
# A carpet, a rug, a sofa, an armchair, a cushion and a mattress take the same handful of marks,
# and the method is the mark's, not the surface's: ink wants alcohol, grease wants washing-up
# liquid on the dry cloth before any water, blood wants cold water only, wax wants an iron and
# brown paper. The rows that answer those marks are written for garments - `stain-ink` and
# `stain-grease` in clothing.py stand down for every soft surface - and `carpet-stain` and
# `sofa-stain` in home.py stand down for every named substance, each expecting the other to hold
# the line. So nothing did:
#
#     how do i get ink out of my carpet      -> "I'm not sure about that one"
#     ink on the couch                       -> "I'm listening - say more if it helps"
#     how do i get grease off my mattress    -> "That's beyond what I know well"
#     how do i get oil out of the carpet     -> "I'm not sure about that one"
#     ballpoint pen on the sofa cushion      -> "Thanks for telling me"
#     ketchup on the rug                     -> a reply that started mid-sentence
#     chocolate on the sofa                  -> "Grease wants neat washing-up liquid first"
#
# The soft surfaces belong in one row with the mark's own method, because the two words the
# person types - the mark and the surface - are the whole question. A mark with its own proper
# card (coffee, red wine, nail polish, sick, paint) is left to it, this row being a first move
# for the marks that have none, exactly as `stain-with-no-card` does for garments.
SOFT_SURFACE = ("carpet", "carpets", "rug", "rugs", "mat", "mats", "sofa", "sofas",
                "settee", "settees", "couch", "couches", "armchair", "armchairs",
                "upholstery", "mattress", "mattresses", "cushion", "cushions",
                "footstool", "footstools", "ottoman", "headboard", "pouffe", "beanbag")

# One family of marks to each method. A word that names two things ("oil" in a chip pan, "pen"
# in a sheep pen) is safe here because the row needs a soft surface in the same line before it
# scores at all, and it is the surface that says which "oil" this is.
SOFT_STAINS = (
    # a pen: the alcohol dissolves the ink, water only carries it deeper into the pile
    (("ink", "inks", "inked", "biro", "ballpoint", "ball point", "pen", "pens", "marker",
      "markers", "sharpie", "felt tip", "felt-tip", "rollerball", "highlighter"),
     "Hand sanitiser or isopropyl alcohol on a cotton wool ball, working from the outside of the "
     "mark in and changing the pad as it lifts the ink; hairspray does the same job at a pinch. "
     "Blot it dry, then dab the last of it out with cool water - never scrub, which spreads a pen "
     "mark and fluffs the pile."),
    # grease: washing-up liquid before water, or the water drives the fat down and sets it
    (("grease", "greasy", "greased", "oil", "oily", "oiled", "fat", "fatty", "butter",
      "margarine", "mayonnaise", "mayo", "lard", "dripping", "ghee", "olive oil",
      "cooking oil", "chip fat"),
     "Neat washing-up liquid worked into the dry mark with your fingers before any water goes "
     "near it, because water first only carries the grease deeper. Give it five minutes, then "
     "blot it out with a barely damp cloth and repeat once or twice; a shadow left after that is "
     "a carpet cleaner's job."),
    # a sauce or a spill with sugar in it: lift it, then cool water, and no heat
    (("ketchup", "tomato sauce", "tomato ketchup", "curry", "curry sauce", "gravy",
      "bolognese", "bolognaise", "chilli", "chili", "chilli sauce", "chili sauce", "salsa",
      "soy sauce", "sriracha", "hot sauce", "pasta sauce", "stew", "casserole", "jam",
      "marmalade", "honey", "syrup", "golden syrup", "ice cream", "yoghurt", "yogurt",
      "custard", "soup", "smoothie", "milkshake", "egg"),
     "Scoop up what is still sitting there with a spoon, then dab, don't rub, with cool water and "
     "a drop of washing-up liquid from the outside of the mark in, blotting with a towel as the "
     "colour lifts. Rinse by dabbing with clean water and blot dry, and keep heat away from it: a "
     "hairdryer or an iron sets a sauce stain for good."),
    # chocolate is the one that must be left to harden first
    (("chocolate", "choc", "nutella", "chocolate spread", "chocolate mousse",
      "hot chocolate", "cocoa"),
     "Leave it to harden, then break off what you can and scrape the rest up with a knife held "
     "flat, because dabbing melted chocolate only pushes it deeper into the pile. A drop of "
     "washing-up liquid on a damp cloth, blotted from the outside in, then clean water and a "
     "towel takes the rest."),
    # blood sets in warm water, so this one is cold water only
    (("blood", "bloody", "bleeding", "nosebleed", "period", "cut myself"),
     "Cool water only, never warm: dab it from the outside of the mark in with a drop of "
     "washing-up liquid, blotting with a towel as the colour lifts, then rinse with clean water "
     "and blot dry. Keep going while the water still lifts colour, and anything already dried "
     "wants an enzyme carpet cleaner left on it for an hour."),
    # mud: dry first, or the vacuum cannot take it and the cloth just drives it in
    (("mud", "muddy", "soil", "clay", "grit", "sand"),
     "Let it dry completely, then vacuum off what breaks loose - a wet mud patch only gets "
     "pushed into the backing. Dab at what is left with cool water and a drop of washing-up "
     "liquid, then blot dry with a towel, working from the outside in."),
    # candle wax: harden, then heat through paper so the wax is drawn up into it
    (("candle", "candles", "wax", "candle wax", "wax crayon", "crayon", "crayons"),
     "Let it set, crack off what you can with something plastic, then lay brown paper over the "
     "rest and press it with a warm iron or a hairdryer on low, moving the paper as it takes the "
     "wax up. A little white spirit on a cloth takes out the last of the grease."),
)

_SOFT_STAIN_WORDS = [(words, reply) for words, reply in SOFT_STAINS]


def _a_mark_on_a_soft_surface(memory, understood):
    """The method for the mark the line names, for a carpet, rug, sofa or mattress."""
    text = " " + str((understood or {}).get("text") or (understood or {}).get("clean")
                      or "").lower() + " "
    for words, reply in _SOFT_STAIN_WORDS:
        for word in words:
            if " " in word:
                if word in text:
                    return reply
            elif re.search(r"\b" + re.escape(word) + r"\b", text):
                return reply
    # A mark nobody named a family for: the plain blot, which is right for most of them and
    # wrong for none, and is what the unnamed-stain rows say on this surface.
    return ("Blot, don't rub, with kitchen paper, then dab from the outside of the mark in with "
            "cool water and a drop of washing-up liquid, blotting dry with a towel and repeating "
            "until nothing more comes up. Work in small patches and never soak it, or the backing "
            "and underlay stay damp and start to smell.")


ENTRIES.append(entry(
    "soft-surface-stain",
    (tuple(word for words, _reply in SOFT_STAINS for word in words), SOFT_SURFACE),
    _a_mark_on_a_soft_surface,
    # A mark with a proper card of its own keeps it: coffee has `coffee-sofa`, red wine has
    # `wine-furniture` and `red-wine-carpet`, nail polish, sick, paint, bleach, mould and
    # limescale all have their own rows and their own better answers. Buying, fitting, cleaning
    # or moving the thing is another question again, and so is a car's carpet.
    avoid=("coffee", "tea", "cola", "coke", "juice", "red wine", "wine", "nail polish",
           "nail varnish", "varnish", "paint", "emulsion", "gloss", "bleach", "sick",
           "vomit", "vomited", "vomiting", "wee", "urine", "pet", "poo", "mould", "mold",
           "mildew", "limescale", "dye", "hair dye", "superglue", "tar", "glue", "sticker",
           "chewing gum", "gum", "mouthwash", "buy", "buying", "bought", "which", "best",
           "underlay", "fitting", "fitted", "how much", "quote", "cost", "price", "new one",
           # cleaning one, vacuuming it and how it smells are the surface's own rows, and none of
           # them needs a word of this row's key: "clean" is not in the key, because the commonest
           # way to ask for a mark's method is "how do i clean ink off a carpet" and an avoid word
           # of "clean" stood this row down for exactly that line.
           "smell", "smells", "smelly",
           "stink", "stinks", "slip", "slips", "slipping", "slide", "sliding", "curl",
           "curls", "flat", "fire", "smoke", "burn", "burnt", "scratch", "scratched",
           # a car's carpet is the cars domain's, and a car seat is not a carpet
           "car", "cars", "van", "boot", "driveway", "engine", "petrol", "diesel",
           # an oil or a fat that is being cooked with or changed is not a mark
           "fry", "frying", "fryer", "chip pan", "oven", "hob", "boiler", "radiator",
           "engine oil", "olive oil for", "how much oil"),
    bias=2))

# --- a stain nobody has taught it ---------------------------------------
# The rows above answer the marks that are named in the base: curry, coffee, wax, nail polish,
# ink on skin, sticker glue, red wine, mud. Everything else was a shrug, and "how do i get tar
# off a car", "how do i get sun cream out of a shirt", "how do i get superglue off my fingers",
# "how do i get hair dye off my skin" are ordinary questions with a right first move. The first
# move depends on what made the mark and what it is on, and those two things are enough: grease
# wants washing-up liquid before any water, dye wants a solvent and no heat, glue wants to be
# hardened or softened rather than pulled, and a fabric wants blotting and cool water.
# The marks that have a row of their own are in the avoid below, so this answers only the
# stains nobody wrote a card for.
STAIN_ON = ("shirt", "shirts", "t shirt", "tshirt", "top", "tops", "blouse", "collar", "cuffs",
            "sleeve", "sleeves", "jeans", "trousers", "dress", "skirt", "jumper", "jumpers",
            "cardigan", "hoodie", "coat", "jacket", "apron", "overalls", "tablecloth", "napkin",
            "cloth", "sheet", "sheets", "pillowcase", "duvet", "towel", "towel", "sofa", "couch",
            "settee", "armchair", "carpet", "rug", "mat", "mattress", "curtain", "curtains",
            "cushion", "upholstery", "car", "car seat", "wall", "walls", "floor", "floors",
            "table", "worktop", "wood", "bath", "sink", "toilet", "tiles", "grout", "window",
            "glass", "mirror", "book", "paper", "phone", "hands", "fingers", "skin", "patio",
            "decking", "slab", "slabs", "paving", "pavement", "path", "drive", "driveway",
            "brick", "bricks", "concrete", "render", "fence", "shed")
STAIN_GETTING = ("get", "gets", "got", "remove", "removed", "clean", "cleaned", "shift", "lift",
                 "stain", "stains", "stained", "mark", "marks", "scrub", "out of", "off",
                 "take out", "come off", "came off",
                 # "i have egg on my shirt" and "there is egg on my shirt" name the mark where it
                 # is; the guard below still needs the phrase that puts it somewhere, so a plain
                 # "i have a new sofa" is not a mark.
                 "have", "has", "theres", "there is", "there's")
# The marks with a card of their own. A word here keeps the specialist answer in place: this row
# is a first move, not a better answer to a question the base already answers well.
STAIN_HAS_A_CARD = (
    "curry", "bolognese", "gravy", "ketchup", "tikka", "turmeric", "coffee", "tea", "cola",
    "juice", "wax", "candle", "nail polish", "nail varnish", "nailpolish", "sticker", "sticky",
    "tape", "ink", "pen", "pen ink", "marker", "sharpie", "crayon", "crayons",
    "felt tip", "pencil", "chalk", "glitter", "sequins", "red wine", "wine", "sick", "vomit",
    "vomited", "vomiting", "sweat", "mould", "mold", "mildew", "limescale", "hard water", "mud",
    "oil", "grease", "blood", "grass", "chewing gum", "gum", "deodorant",
    "makeup", "make-up", "foundation", "nappy", "poo", "pee", "bleach", "sick stain",
    # what the wash did to a garment is a laundry question, not a mark: "my white shirts have
    # gone grey in the wash" and "can i wash a pink shirt" were both reaching this row
    "gone", "went", "shrunk", "shrunken", "shrink", "shrank", "bled", "bleed", "faded", "fade",
    "grey", "gray", "yellowed", "whiten", "whitening", "brighter", "dull", "dullest", "pink",
    "colour", "colours", "colors", "run", "running", "came out",
    # a garment that "needs cleaning" is a laundry, a dry cleaner or the clothing domain's
    # question; there is no mark in it
    "needs cleaning", "needs a clean", "need cleaning", "needs washing", "needs a wash",
    "dry clean", "dry cleaned", "dry cleaning", "dry cleaner", "to the cleaners", "cleaners",
    # and the things that are not a stain at all: a repair, a wash question, a chip, a smell
    "smell", "smells", "stinks", "chipped", "cracked", "crack", "broke", "broken", "repair",
    "fix", "replace", "how long", "how often", "water mark", "water marks", "scuff", "scuffs",
    "burn", "burnt", "melted", "iron mark", "heat mark",
    # a scratch, a chip and a dent are damage to a surface, not a mark on it: they were being
    # answered with "rinse it from the back of the fabric", which is the wrong card entirely
    "scratch", "scratches", "scratched", "chip", "chips", "chipped", "dent", "dents",
    "squeak", "squeaky", "stuck", "wont turn", "won't turn",
    # a thing that will not stay where it is put is a grip question, not a mark: "my fitted sheet
    # keeps coming off the mattress" and "how do i stop my cushions sliding off the sofa" were both
    # answered with "blot, do not rub", because " off" is how a mark comes off too.
    "keeps coming off", "keeps coming out", "keeps falling off", "keeps sliding", "keeps slipping",
    "keeps moving", "keeps creeping", "sliding off", "slides off", "slipping off", "slips off",
    "wont stay", "won't stay", "doesnt stay", "doesn't stay", "not staying", "stay on",
    "falls off", "falling off", "coming undone", "comes undone", "shelf liner",
    # A thing being lifted or carried is a back question, not a mark: "i lifted a sofa" was read
    # as a mark coming off (the sofa, plus "lifted" from the words above) and was told to blot
    # it with kitchen paper. The lifting card answers it; this row stands down.
    "lifted", "lifting", "carried", "carrying", "hauled", "dragged", "shifted", "heaved",
    "humped", "lugged", "manhandled", "picked up", "bad back", "my back",
    # "drive" in the key is the driveway and "out of" is how a mark comes off, so a licence
    # that is out of date scored twice on this row and was told to rinse the mark from the back
    # of the fabric. A licence is a document, a permit or a card, and none of them is a surface;
    # the driveway lines themselves ("get oil off the driveway", "moss off the drive") say no
    # licence word and keep the paving and oil cards.
    "licence", "license", "licences", "licenses", "driving licence", "driving license",
    "photocard", "log book", "v5c", "mot certificate", "permit", "passport",
    # a date is not a mark either: "my car is out of date", "the milk is out of date" and
    # "is it past its best before" are about a date, and the date rows own them.
    "out of date", "past its date", "use by", "used by", "best before", "sell by",
    "expired", "expires")


# A bare "get", "gets" or "got" is how a person says a mark comes off - "how do i get tar off a
# car", "how do i get biro off my hands" - and it is also how a person says they have bought
# something: "i got a new sofa", "we got a new carpet", "got a new phone and its great". Beside a
# surface word the second family matched this row and was handed blotting instructions for a mark
# that is not there, so the line has to say how the mark comes off before this row answers
# (quality lane, on main 08e4d941). Every line the row was written for says it.
COMES_OFF = ("out of", "out the", "from", "rid of", "remove", "clean", "scrub",
             "shift", "lift", "stain", "mark", "spill")

# "Off" is the word for a mark coming off - "how do i get tar off a car", "get it off" - and it
# is also how a thing says it is switched off: "her phone is off and i cant settle" and "my phone
# screen is off" both scored the surface ("phone", "screen") and the bare "off" and were told to
# blot the mark from the back of the fabric, while the person was asking about a phone. Being off
# is a state, not a mark, so the word only counts when something is being taken off something: a
# thing after it ("off my hands", "off a car"), or a taking verb before it ("get it off", "wipe
# that off"). "the tap is off", "the wifi went off" and "the boiler is off" are states too.
OFF_COMES_OFF = re.compile(
    r"\boff\s+(?:of\s+)?(?:the|my|your|his|her|their|our|its|a|an|this|that|these|those|it|them)\b"
    r"|\b(?:get|gets|getting|got|take|takes|taking|took|taken|come|comes|coming|came|wash|"
    r"washing|washed|wipe|wipes|wiping|wiped|rub|rubs|rubbing|rubbed|scrub|scrubs|scrubbing|"
    r"scrubbed|lift|lifts|lifting|lifted|pick|picks|picking|picked|scrape|scrapes|scraping|"
    r"scraped|shift|shifts|shifting|shifted|bring|brings|bringing|brought|pull|pulls|pulling|"
    r"pulled|peel|peels|peeling|peeled|soak|soaks|soaking|soaked|dab|dabs|dabbing|dabbed|"
    r"brush|brushes|brushing|brushed)\b[^.!?]{0,60}\boff\b")

# ...but "off the car" is also how every other kind of taking is said, and none of them is a
# mark: "we paid off the car" was told a hard surface wants lifting and wiping, "he took off his
# coat" was told to blot up what it can with kitchen paper, and "i knocked off work", "signed off
# the job" and "switched off the boiler" read the same way. A mark coming off has a mark in the
# line - "get tar off a car", "get ink off the sofa" - or a pronoun standing in for one ("get it
# off", "wipe that off"), so the "off" phrase only counts when the line names one of those. The
# nouns come from the base's own tables: the marks with a soft-surface answer above, the marks
# that already have a card, and the few everyday ones those miss.
_A_MARK_NOUNS = frozenset(
    [word for words, _ in SOFT_STAINS for word in words]
    + list(STAIN_HAS_A_CARD)
    + ["stain", "stains", "stained", "smudge", "smudges", "smudged", "splodge", "splodges",
       "splat", "blob", "blobs", "patch", "patches", "dirt", "grime", "filth", "soot", "ash",
       "residue", "scum", "spill", "spills", "spilled", "spilt", "mess", "crumb", "crumbs",
       "dust", "scuff", "scuffs", "fingerprint", "fingerprints", "mark", "marks", "marked",
       "bolognaise", "lasagne", "lasagna", "beetroot", "blueberry", "raspberry", "strawberry",
       "chocolate", "cheese", "sauce", "chips", "butter", "milk", "cola", "coke", "red bull",
       "suncream", "sun cream", "sunscreen", "fake tan", "hair oil", "baby oil", "engine oil",
       "white spirit", "primer", "undercoat", "gloss", "emulsion", "wood stain", "superglue",
       "blu tack", "bluetack", "plasticine", "playdough", "play dough", "slime", "silly putty"])
_A_MARK_NAMED = re.compile(
    r"\b(?:" + "|".join(sorted((re.escape(word) for word in _A_MARK_NOUNS), key=len,
                                reverse=True)) + r")\b")
_A_PRONOUN_BEFORE_OFF = re.compile(
    r"\b(?:it|that|this|them|those|these|one)\s+(?:all\s+)?off\b")


def _names_a_mark(text):
    """True when the line says what the mark is: "get tar off a car"."""
    return bool(_A_MARK_NAMED.search(text))

# A mark is also said by where it is, which is the other half of how people put it: "ive got egg
# on my shirt", "there's soy sauce on my top", "i got honey on my jeans". None of those says
# "off" or "out of", so they were read as a sentence about food - the omelette card for the egg,
# macaroni cheese for the sun cream, and "Noted: you got honey on your jeans" for the honey -
# and the mark went unanswered. A place phrase on its own is not enough either: the family the
# test above exists to keep out ("i got a new sofa", "we got a new carpet") says "a", not "on".
LANDED_ON = re.compile(r"\b(?:on|onto|over|across|down)\s+(?:my|her|his|their|our|your|the|"
                       r"a|this|that)\s+([a-z']+)")
# What a mark can land on: the garments and surfaces STAIN_ON already names, in one word, plus
# the two-word ones a regex reads one word at a time.
LANDED_ON_THINGS = frozenset(STAIN_ON) | frozenset((
    "sleeve", "sleeves", "cuff", "cuffs", "collar", "tie", "shoes", "trainers", "socks",
    "bed", "bedsheets", "pillow", "blanket", "throw", "carpets", "rugs", "trousers", "chinos"))


def landed_on_a_thing(understood):
    """True when the line says what is on a garment or a surface, not what it is made of.

    "i got egg on my shirt" is a mark on a shirt. "i got two eggs" and "i have eggs in the
    fridge" name no surface, so a meal idea still reads them.
    """
    text = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    text = " " + text + " "
    for match in LANDED_ON.finditer(text):
        if match.group(1) in LANDED_ON_THINGS:
            return True
    # "my top has paint on it" puts the mark on the thing already named, so the garment word is
    # elsewhere in the line and "it" stands for it.
    if any(phrase in text for phrase in (" on it ", " on them ", " on those ", " on that ",
                                         " on this ")):
        return any(word in text for word in LANDED_ON_THINGS)
    return False


def not_a_mark_on_a_thing(understood):
    """The stand-down for a food row: a mark on a shirt is the stain row's line, not a recipe."""
    return not landed_on_a_thing(understood)


def _says_how_it_comes_off(understood):
    """True when the line is about a mark coming off, or says where the mark is.

    "ive got egg on my shirt" says where it is rather than how it comes off, and that is the
    same question: the food was named and the garment was named.
    """
    text = " " + str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    comes_off = bool(OFF_COMES_OFF.search(text)) and bool(
        _A_PRONOUN_BEFORE_OFF.search(text) or _names_a_mark(text))
    return (any(phrase in text for phrase in COMES_OFF) or comes_off
            or landed_on_a_thing(understood))


# A state of a surface is not a mark on it. "how do i get rid of the shine on my face" and the same
# line about the hands are not a stain, and both were told to use a soft nail brush and hand cream,
# because the key of a mark row is a part of a person plus a getting word - which is every "how do
# i get X off my hands" line there is - and the getting word was the whole of the evidence. The
# shiny states are one class, and each of them has an answer of its own: the skin's is oily-skin's,
# a garment's or a shoe's is garment-shine's. Every row that answers a mark stands down on them.
A_STATE_OF_A_SURFACE = ("shine", "shines", "shiny", "shinier", "shiniest", "sheen", "gleam",
                        "gleaming", "glow", "glowing")

def _stain_nobody_taught_it(memory, understood):
    """The first move for a mark the base has no card for, by what made it and what it is on."""
    text = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    on_skin = any(word in text for word in ("fingers", "finger", "hands", "hand", "skin",
                                            "arms", "arm", "face", "thumbs", "thumb"))
    on_hard = any(word in text for word in ("worktop", "work top", "counter", "countertop",
                                            "table", "floor", "floors", "wall", "walls", "slab",
                                            "slabs", "paving", "pavement", "path", "drive",
                                            "driveway", "patio", "decking", "brick", "bricks",
                                            "concrete", "render", "tile", "tiles", "grout",
                                            "bath", "sink", "basin", "toilet", "hob", "glass",
                                            "mirror", "window", "windows", "fridge", "cupboard",
                                            "door", "car", "car seat"))
    # A shine is a state of the skin, not a substance on it, so there is no mark to take off: the
    # method for a mark is soap and a brush, which is the wrong thing to do to skin that is only
    # shining. It is the same class garment-shine fences the face with, and a shine on a part of a
    # person with no card of its own gets the honest hedge instead. A shiny table, worktop or floor
    # is a surface, and its method is unchanged - the rule is only about skin.
    if on_skin and not on_hard and any(" %s " % w in " %s " % text for w in A_STATE_OF_A_SURFACE):
        return None
    # A chewing gum is picked off rather than washed: water does nothing to it, and on skin it
    # takes the hairs with it. "how do i get chewing gum off my hands" was the dentist's answer.
    if any(word in text for word in ("chewing gum", "chewed gum", "gum", "bubble gum")):
        if on_skin:
            return ("Do not pull it: hold an ice cube on it for a minute until it goes hard and it "
                    "lifts off in one piece, and a little cooking oil or peanut butter worked in "
                    "with a fingertip takes the last of the stickiness off, then wash with soap. "
                    "Nothing else shifts gum without taking skin with it.")
        return ("Harden it before you touch it: an ice cube in a bag held on the gum for a minute "
                "makes it brittle enough to pick off in one piece, and what is left comes away "
                "with a little cooking oil or a dab of peanut butter worked in from the outside, "
                "then washing-up liquid and a rinse. Do not use heat, which sets it into the "
                "fibres.")
    # A glue or a resin is picked off, not wiped: pulling it while it is tacky takes the fibres
    # with it, and on skin it takes the skin.
    if any(word in text for word in ("superglue", "super glue", "glue", "glued", "adhesive",
                                     "resin",
                                     "silicone", "sealant", "blu tack", "blu-tack", "blutack",
                                     "putty", "plasticine", "play dough", "playdough")):
        if on_skin and any(word in text for word in ("silicone", "sealant", "putty",
                                                      "play dough", "playdough", "plasticine")):
            return ("Let it set and then rub it off rather than trying to wipe it: wet silicone "
                    "smears and takes the skin with it, cured silicone peels off in one lump. A "
                    "little olive or baby oil on a cloth takes the film off afterwards, and warm "
                    "soapy water finishes the fingers.")
        if on_skin:
            return ("Soak it in warm soapy water and do not pull the fingers apart: superglue "
                    "lets go in warm water after ten or fifteen minutes, and a little acetone or "
                    "nail polish remover on a cotton bud finishes it. Never use a knife or peel "
                    "it, and if skin is properly bonded, soak rather than force it.")
        return ("Let it harden rather than wiping it while it is tacky: an ice cube on it for a "
                "minute makes it brittle enough to pick off in one piece, and a little cooking "
                "oil or acetone softens what is left. Then a drop of washing-up liquid on a "
                "damp cloth takes the residue, and work from the outside in so the mark does "
                "not spread.")
    # A tar, a paint or a resin that water will not touch: the solvent comes first, on a cloth.
    if any(word in text for word in ("tar", "tarmac", "bitumen", "creosote", "resin", "paint",
                                     "varnish", "dye", "hair dye", "henna", "wood stain", "rust",
                                     "oil paint", "graffiti")):
        if on_skin:
            return ("Oil first, not water: rub a little olive or baby oil into it, leave a "
                    "minute and wipe with a cloth, and for hair dye on skin a dab of toothpaste "
                    "or milk on a cotton bud lifts the last of the colour. Wash with soap after, "
                    "and give it a couple of days rather than scrubbing the skin.")
        if on_hard:
            return ("Water will not move it, so start with a solvent on a cloth: white spirit or "
                    "methylated spirit for tar and paint, vinegar or a lemon for a rust mark, and "
                    "acetone only on a surface you know will take it. Test it on a hidden corner "
                    "first, dab rather than rub, and wipe the residue off with hot water and a "
                    "drop of washing-up liquid. Keep the window open, keep the cloths out of the "
                    "bin indoors, and wash your hands after.")
        return ("Water will not move it, so start with a solvent on a cloth: white spirit or "
                "methylated spirit for tar and paint, vinegar or a lemon for a rust mark, and "
                "acetone on hard surfaces only. Test it on a hidden patch, dab rather than rub, "
                "and change the cloth as it takes the colour up. On fabric, follow with "
                "washing-up liquid and a wash, and keep it out of the dryer until the mark has "
                "gone.")
    # A sauce or a drink is water and colour rather than a fat, so the dry-first rule is the
    # wrong way round for it: hot water is what sets the colour in, and the washing-up liquid is
    # only there for the fat in it. "how do i get tomato sauce off my hands" got the grease
    # line, which told a person that water on its own spreads a grease.
    if on_skin and any(word in text for word in ("sauce", "tomato", "ketchup", "curry", "juice",
                                                 "coffee", "tea", "wine", "gravy", "soup",
                                                 "chocolate", "jam")):
        return ("Rinse the hands under cold water first, not hot, then a drop of washing-up "
                "liquid worked in with the fingertips: a sauce is mostly water and colour, and "
                "hot water is what sets the colour into the skin. Tomato, curry and coffee "
                "leave a faint tint that fades in a day or two, so wash once more with soap "
                "later rather than scrubbing the skin.")
    # Grease, cream and sauce: washing-up liquid before water, because water alone spreads it.
    if any(word in text for word in ("grease", "greasy", "oil", "butter", "fat", "sauce",
                                     "sunscreen", "sun cream", "suncream", "cream", "lotion",
                                     "lipstick", "makeup", "make-up", "mayonnaise", "dressing")):
        if on_skin:
            return ("Washing-up liquid first, on dry hands and before any water: work a drop in "
                    "with your fingertips, leave it a minute, then rinse in warm water - water on "
                    "its own just spreads a grease. A second round with a soft nail brush takes "
                    "what is in the creases, and a little hand cream afterwards puts back what "
                    "the washing-up liquid took off.")
        return ("Washing-up liquid first, on the dry mark, worked in with a fingertip before any "
                "water touches it: that is what breaks up a grease. Leave it five minutes, then "
                "rinse in the hottest water the label allows and wash as normal. On a hard "
                "surface or a sofa, the same drop of washing-up liquid on a barely damp cloth, "
                "dabbed from the outside in, then blotted dry.")
    # A protein mark sets in hot water, so the water has to be cold.
    if any(word in text for word in ("egg", "milk", "blood", "sick", "vomit", "poo", "pee",
                                     "urine", "spit", "phlegm")):
        if on_skin:
            return ("Cold water only, and plenty of it: hot water sets a protein mark into the "
                    "skin and it stains harder. Rinse the hands under a cool tap until the water "
                    "runs clear, wash with soap, and if any colour is left, a dab of hydrogen "
                    "peroxide on a cotton bud lifts it - a blood mark on skin is not an "
                    "emergency, and scrubbing it only makes it spread.")
        return ("Cold water only, and plenty of it: hot water sets a protein mark into the fibres "
                "and it will not come out afterwards. Rinse from the back of the fabric so the "
                "mark is pushed out rather than through, rub in a little washing-up liquid or "
                "biological detergent, leave it fifteen minutes, then wash as the label allows "
                "and check before it goes anywhere near a dryer.")
    if on_skin:
        return ("Warm soapy water and a soft nail brush, then a little oil or hand cream to lift "
                "what is left: most marks on skin are grease or dye and both come off with those "
                "two. Do not scrub the skin raw and do not put a solvent on it, apart from nail "
                "polish remover on a mark that will not shift, and give it a day rather than ten "
                "minutes.")
    if any(word in text for word in ("book", "paper", "card", "page", "pages", "letter",
                                     "document", "photo", "photograph")):
        return ("On paper you cannot wash it, so lift what you can while it is wet: a clean "
                "cotton bud of water dabbed from the edge of the mark outwards, then blot with "
                "kitchen paper and leave a weight on it to dry flat. A soft eraser takes a dry "
                "mark down, and a highlighter or ink mark will always leave some colour behind, "
                "so stop before the paper starts to cockle.")
    if any(word in text for word in ("carpet", "rug", "mat", "sofa", "couch", "settee",
                                     "armchair", "mattress", "upholstery", "cushion", "curtain",
                                     "car seat")):
        return ("Blot, do not rub, and work from the outside in so it does not spread: kitchen "
                "paper first, then a barely damp cloth with a drop of washing-up liquid, blotting "
                "and changing the cloth as it takes the colour up. Dry it with a towel and a "
                "weight rather than heat, and do not scrub, because scrubbing spreads the mark "
                "and fluffs the pile.")
    # A hard surface is scraped and wiped, never blotted from the back like a cloth: "how do i
    # get honey off a worktop" and "how do i get cement off a paving slab" were both getting the
    # fabric answer, which talks about rinsing from the back of the fabric.
    if on_hard:
        return ("A hard surface wants lifting and wiping rather than blotting: take the worst "
                "off with a plastic scraper or the back of a knife held flat, then wipe with hot "
                "water and a drop of washing-up liquid, turning the cloth as it takes the colour "
                "up. Anything stronger gets tested on a hidden corner first, because acid eats "
                "limestone and concrete and bleach dulls a seal, and a cream cleaner on a damp "
                "cloth takes the last of the film off without either.")
    return ("Blot up what you can with kitchen paper, then rinse the mark from the back of the "
            "fabric in cool water - pushing it out rather than through the cloth - and work in a "
            "drop of washing-up liquid or a little biological detergent. Leave it fifteen "
            "minutes, wash at the hottest the care label allows, and air-dry it: a mark that has "
            "been through a dryer is much harder to shift, so check it before it goes in.")


# A chemical that burns is not a mark, and it is not a blocked drain either. "i got acid on my
# hand" was answered with "most marks on skin are grease or dye ... give it a day", and "i got
# drain cleaner on my fingers" with how to unblock a trap: both send a person away from the tap,
# which is the one direction that makes a chemical burn worse. The row needs a chemical *and* a
# part of a person, so a bottle of drain cleaner on a shelf and a blocked drain keep their own
# answers, and a line that already says "burn" keeps the burn card.
CHEMICAL_ON_PERSON = ("acid", "battery acid", "caustic", "caustic soda", "alkali", "ammonia",
                      "bleach", "drain cleaner", "drain unblocker", "oven cleaner",
                      "paint stripper", "nitromors", "white spirit", "turps", "turpentine",
                      "sulphuric", "hydrochloric", "hydrogen peroxide", "corrosive",
                      # The bare word is the shelf, not the accident: "a chemical exfoliant on
                      # my face" and "chemical peel" are the cosmetics counter, and an acid
                      # card that ends at A&E is the wrong answer to a face wash. Only the
                      # phrases that put an unnamed chemical on a person count.
                      "chemical on", "chemical in", "chemicals on", "chemicals in",
                      "chemical spill", "spilled chemical")
A_PART_OF_A_PERSON = ("hand", "hands", "finger", "fingers", "thumb", "thumbs", "skin",
                      "arm", "arms", "wrist", "wrists", "face", "eye", "eyes", "cheek",
                      "leg", "legs", "foot", "feet", "knee", "knees", "ankle", "chest")
# A chemical and a body part are not enough on their own: "does bleach damage skin", "is it safe
# to use caustic soda with bare hands" and "is bleach bad for your skin" are questions about a
# chemical, and first aid is not the answer to a question - the one reply a bot must not give is
# twenty minutes under a tap for nothing. The line has to put the chemical somewhere, which is
# what every one of those questions fails to do.
CHEMICAL_LANDED = ("got", "get", "spill", "spilt", "splash", "splosh", "splatter", "pour", "soak",
                   "down my", "in my", "off my", "on my", "over my", "onto my", "onto",
                   "all over", "went on")


def _the_chemical_landed_on_a_person(understood):
    """True when the line says the chemical landed on somebody, not that it exists.

    "i got acid on my hand" lands it; "does bleach damage skin" only talks about it. A key of
    words cannot tell those apart, because both hold the chemical and the part.
    """
    text = " " + str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    return any(phrase in text for phrase in CHEMICAL_LANDED)


ENTRIES.append(entry(
    "chemical-on-skin",
    (CHEMICAL_ON_PERSON, A_PART_OF_A_PERSON),
    ("Cool running water now, and stay under it for twenty minutes: that is the part that limits "
     "the damage, and a cloth or a soap is not it. While the water runs, take off anything the "
     "chemical has soaked into - a sleeve, a watch, a ring. Then get advice and say what the "
     "chemical was and how long ago: 111 in the UK, 911 in the US, the poison centre number on "
     "the label, and straight to A&E if the skin is white or blistered, if it is a strong acid "
     "or a caustic soda, or if any of it reached an eye - an eye wants the water for longer, "
     "with the eyelid held open."),
    # A burn word in the line is already the burn card's, and an acid in the stomach is a
    # different question entirely; a flat battery and acid reflux name neither a person nor a
    # chemical that can be on one.
    avoid=("burn", "burnt", "burned", "scald", "reflux", "heartburn", "stomach",
           "car battery", "battery is flat", "battery died", "phone battery", "battery life",
           "battery go flat", "acid rain",
           # A smell is a rinse and a lemon, not twenty minutes under a tap: "my hands smell
           # of bleach" and "how do i get bleach smell off my hands" were the drain-smell card.
           "smell", "smells", "smelling", "smelly", "smelled", "stink", "stinks",
           # Questions about a chemical rather than an accident with one. "does bleach damage
           # skin", "is it safe to use caustic soda with bare hands", "can i put bleach on a
           # verruca on my foot" all had an answer before this row and must keep it.
           "safe", "is it safe", "can i put", "should i put", "avoid", "sensitive",
           "allergic", "react", "reacts", "cracked", "damage", "bare hands",
           "verruca", "wart", "warts", "mole", "moles", "fumes", "vapour", "vapours",
           "bad for", "bad on", "harm", "harmful", "dangerous", "is it ok", "ok on", "how bad",
           "is it bad", "is that bad", "ok for", "worry", "is it safe"),
    guard=_the_chemical_landed_on_a_person,
    bias=2))


ENTRIES.append(entry(
    "stain-with-no-card",
    (STAIN_ON, STAIN_GETTING),
    _stain_nobody_taught_it,
    guard=_says_how_it_comes_off,
    avoid=STAIN_HAS_A_CARD + (
        # a surface that is being cleaned, painted, repaired or bought rather than stained
        # a phone taken off a child is not a phone with a mark on it: "should i take his phone
        # off him" matched "phone" from the surfaces and "off" from the getting-off words and was
        # told to blot the fabric from the back. The line has a person in it, not a surface.
        "take his phone", "take her phone", "take their phone", "take the phone",
        "take his ipad", "take her ipad", "take his tablet", "take her tablet",
        "take his console", "take her console", "take it off him", "take it off her",
        "take it off them", "take things off", "taken off", "phone off him", "phone off her",
        "screen time", "off him", "off her", "off them",
        "clean the", "clean my", "painting", "decorating", "grout pen", "seal the", "bleach",
        # a mat or a curtain that has gone slimy or grey is the laundry row's question
        "bath mat", "bath mats", "bathmat", "bathmats", "shower mat", "shower mats",
        "shower curtain", "shower curtains", "curtain", "curtains", "liner", "slimy",
        "dust", "hoover", "vacuum", "mop", "wash the", "garden", "shed", "fence",
        "bathroom", "kitchen", "bedroom", "boiler", "radiator", "washing machine", "dishwasher",
        # a mark on a painted wall, a ceiling or plaster is the wall card's job, and the wall card
        # says what this one cannot: that the paint film is thin and a scrub shows
        "wall", "walls", "painted wall", "ceiling", "ceilings", "paintwork", "plaster",
        # "drive" is the driveway in this key, so "how do i get better at driving" read as a
        # stain on the drive: with the golf row standing down for it, this row took the line
        "at driving", "learn to drive", "driving lesson", "driving test", "get better at",
        # "phone" is in the key because a mark on a phone screen is a mark, and "get"/"off"
        # are two of the words people use for a mark coming off, so "how do i get off a phone
        # call" scored twice on this row and got a kitchen-paper blot - for a phone call it
        # had already hung up. The call is the subject, and a call is not a mark.
        "phone call", "phone calls", "a call", "the call", "calls", "call back",
        "get off the phone", "on the phone", "hang up", "voicemail", "caller", "cold call",
    ),
    bias=-2))

# A mark on a person is the skin answer whatever made it. The marks in `STAIN_HAS_A_CARD` all
# have their own cards for cloth and for surfaces - "how do i get grease out of a shirt" is the
# grease card, "how do i get coffee off the worktop" the water-ring one - and the word alone was
# enough to stand the skin first move down: "how do i get grease off my hands" got the search
# shrug, and "how do i get blood off my hands" and "how do i get grease off my skin" the same,
# while "how do i get paint off my hands" was answered, because paint is not in that list. On
# skin there is no specialist card to keep, and the first move is the same for every substance:
# what changes is the branch the method takes (oil for a dye, cold water for blood, soap and a
# brush for a grease), which is what `_stain_nobody_taught_it` already does. "how do i get paint
# off my skin" was the paint-storage card and "how do i get chewing gum off my hands" the
# dentist's, because nothing asked a mark on a person its own question.
MARK_ON_THE_PERSON = A_PART_OF_A_PERSON + (
    "palms", "palm", "forearms", "forearm", "knuckles", "knuckle", "cuticles", "cuticle",
    "cheeks", "cheek", "chin", "thumbs")
# The mark words, so a part of a person on its own is not a mark: "how do i get my hands on a
# cheap flight" and "how do i get stronger arms" name no mark and keep their own answer.
A_MARK_WORD = ("stain", "stains", "stained", "mark", "marks", "marked", "off", "out of",
               "rid of", "remove", "clean", "cleaner", "shift", "lift", "scrub", "splashed",
               "covered in", "splattered")
# The parts of a person that are not skin to be scrubbed: an eye, an ear, the mouth and the nose
# are rinsed or seen by someone. See `_a_mark_on_the_person`.
NOT_A_SKIN_MARK = ("eye", "eyes", "eyelid", "eyelids", "eyeball", "eyeballs", "eyelash",
                   "eyelashes", "ear", "ears", "eardrum", "eardrums", "mouth", "lip", "lips",
                   "gums", "tongue", "nostril", "nostrils", "inside my nose", "throat")


def _a_mark_on_the_person(understood):
    """True when the line is a mark on a person rather than a condition or a way of getting."""
    text = " %s " % str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    # An eye, an ear, the mouth and the nose are not a patch of skin. Each is rinsed or looked at
    # rather than scrubbed, oiled or sponged with cold water, so the skin method is the wrong
    # advice there and each has a card of its own: "get the water out of my eye" was answered
    # here with "rinse the mark from the back of the fabric ... leave it fifteen minutes".
    if any(" %s " % part in text for part in NOT_A_SKIN_MARK):
        return False
    if not any(" %s " % part in text for part in MARK_ON_THE_PERSON):
        return False
    return any(phrase in text for phrase in A_MARK_WORD)


ENTRIES.append(entry(
    "mark-on-skin",
    (MARK_ON_THE_PERSON, STAIN_GETTING),
    _stain_nobody_taught_it,
    guard=_a_mark_on_the_person,
    # A condition, a wound, a smell or a nail job is not a mark, and neither is a product for
    # the hands: each has an answer of its own, and the skin answer sends a person to a nail
    # brush. "my hands are dry", "how do i get warts off my hands" and "how do i stop my hands
    # shaking" all name a part of a person and a getting word.
    avoid=("dry", "drier", "cracked", "sore", "itchy", "itching", "itch", "rash", "eczema",
           "psoriasis", "dermatitis", "hives", "blister", "blisters", "burn", "burnt",
           "scald", "cut", "cuts", "gash", "wound", "bleeding", "bleed", "numb",
           "tingling", "cold", "warm", "shaking", "shake", "tremor", "pain", "painful",
           "hurt", "hurts", "ache", "aching", "swollen", "swelling", "lump", "lumps",
           "ganglion", "wart", "warts", "verruca", "verrucas", "mole", "moles", "fungal",
           # a patch of colour on the skin is a skin condition, not a mark on it: "how do i get
           # rid of dark patches on my hands" is a doctor's question and the mark answer took it
           "patch", "patches", "patchy", "dark", "discoloured", "discolored", "discoloration",
           "pigmentation", "age spots", "sun spots", "liver spots", "vitiligo",
           "infection", "infected", "splinter", "splinters", "thorn", "stuck ring",
           "wedding ring", "ring stuck", "stuck finger",
           # a smell on the hands is a cooking or a pet question, and it has its own answer
           "smell", "smells", "smelly", "smelling", "stink", "stinks",
           # a tan that has gone patchy is the fake-tan card's, not a mark
           "fake tan", "self tan", "false tan", "spray tan", "tanning",
           # the substances with a card of their own for skin, so this row stands down: the paint
           # card knows that a water-based paint washes off while a gloss needs white spirit, and
           # the ink card knows that a permanent marker wants oil or alcohol, which is more than
           # the first move here can say. "how do i get paint off my hands", "how do i get
           # permanent marker off my hands" and "how do i get wood stain off my hands" were all
           # answered better before this row existed.
           "paint", "gloss", "emulsion", "varnish", "wood stain", "woodstain", "wax",
           "ink", "marker", "permanent marker", "felt tip", "sharpie", "biro", "pen",
           # a hair dye has a card that knows the bicarbonate paste and the barrier cream, which
           # is more than the first move here: "how do i remove hair dye from my skin" and "how
           # do i get hair dye off my skin" were both answered better before this row existed.
           "dye", "dyes", "hair dye", "hairdye", "henna", "bleach", "hair colour",
           "hair color", "toner",
           # a graze is a wound, and a fall is not a mark to scrub: "i came off my bike and
           # grazed my knee" and "the cyclist came off his bike and is holding his arm" were both
           # sent to the nail brush. A mark is something on the skin, not skin taken off.
           "graze", "grazes", "grazed", "gravel rash", "road rash", "scrape", "scrapes",
           "scraped", "came off", "fell off", "fell", "fall", "landed",
           # a chemical that burns on the skin is a first aid question and it has its own card
           # in this file: "how do i get acid off my skin" is water and a phone call, and the
           # mark answer here is the one that sends a person away from the tap.
           ) + CHEMICAL_ON_PERSON + (
           # an engine oil has a card that knows not to wash it first, which is the one thing a
           # person with it on their hands must not do: "how do i get car oil off my hands" was
           # better answered before this row existed.
           "engine oil", "car oil", "motor oil", "diesel", "petrol", "grease gun",
           # a product for the hands, and a nail job
           "hand cream", "moisturiser", "moisturizer", "handwash", "hand wash", "sanitiser",
           "sanitizer", "hand soap", "soap", "sun cream", "sunscreen", "sunblock",
           "nail varnish", "nail polish", "manicure", "false nails", "acrylic nails",
           "gel nails", "press on nails",
           # a part of a person in an expression rather than on it
           "second hand", "second-hand", "hand in", "hands on", "handwriting",
           "hand writing", "handyman", "helping hand", "give me a hand",
           "on the other hand"),
    # A card that fits part of the line beats this one at the same score - "how do i get paint
    # off my skin" was the paint tin and "how do i get chewing gum off my hands" the dentist -
    # and the nudge is what puts the mark on the person first. The avoid list above is what
    # keeps the nudge from reaching a question that is not a mark.
    bias=3))

# A rust mark in a bath or a sink was the soap-scum card if the line said "remove" ("how do i
# remove rust from a bath") and a shrug when it did not ("theres rust in my bath"). Rust is not
# limescale: it needs the acid and then the enamel seen to, or it comes back from the same chip.
ENTRIES.append(entry(
    "rust-on-enamel",
    (("rust", "rusty", "rusted", "rust mark", "rust marks", "rust stain", "rust stains",
      "rust ring", "rust rings", "rusty water", "orange stain", "brown stain", "brown marks"),
     # the enamel bathroom surfaces, and only those: a worktop ring has the water-ring card, rusty
     # water from the taps is plumbing, and a rusty drum is the machine's own fault answer
     ("bath", "baths", "bathtub", "sink", "sinks", "basin", "shower", "shower tray", "enamel",
      "toilet", "loo", "tub")),
    "Rust is iron in the water or in the enamel itself, and the acid is what lifts it: soak a "
    "cloth in white vinegar or lemon juice, leave it on the mark for an hour, then rub with a "
    "non-scratch pad and rinse. A rust remover with oxalic or phosphoric acid does the same job "
    "faster on a bad mark, and keep bleach away from it, because bleach sets the colour instead of "
    "lifting it. If the enamel is chipped where the rust is coming from, dry it and paint the chip "
    "with enamel touch-up paint, or the mark returns from the same spot. Do not leave a rusty tin "
    "or a wet sponge sitting in the bath: that is usually how a ring gets there.",
    avoid=("eat", "ate", "cook", "recipe", "car", "cars", "van", "bodywork", "paint the",
           "garden", "patio", "fence", "gate", "wheel", "wheelbarrow", "bicycle", "bike",
           "drink", "drinking", "water supply", "boiler", "radiator leak")))

# Sealing grout is a different question from cleaning it, and the cleaning row held the words
# "seal" and "sealing" beside "grout", so "is it worth sealing grout" got the whole cleaning
# answer and no verdict at all. The worth question and the how question are two shapes of the
# same job, so one row answers both and opens with the shape the line asked for: a yes/no for
# "is it worth it", the method for "how do i seal grout".
_SEAL_WORTH = re.compile(
    r"\b(?:worth|worthwhile|necessary|needed|point|good idea|any point)\b"
    # "should i seal" asks the verdict; "what should i use to seal" asks for the product, and
    # the bare word stood the method down for it. "Need" is the same trap: "how much sealer do
    # i need" is a quantity, not a verdict.
    r"|\bshould (?:i|we|you) (?:bother|seal|use (?:a )?sealer|get it sealed)\b"
    r"|\b(?:do|does|will|would) (?:i|we|you|it) need\b", re.I)

# A price or a quantity, and a time or a date, are different shapes of the same job. One row
# answers all of them so a "how much" line is not read as "is it worth it".
_SEAL_COST = re.compile(r"\b(?:cost|costs|price|prices|expensive|cheap)\b|\bhow much\b", re.I)
_SEAL_WHEN = re.compile(r"\b(?:when|how often|how long)\b", re.I)
_SEAL_WHERE = re.compile(r"\bwhere\b.*\b(?:buy|get|shop|stock|stockist)\b", re.I)
_SEAL_THINGS = re.compile(
    r"\bwhat (?:do|will) i need\b|\bwhat (?:kind|type|sort) of sealer\b|\bwhich sealer\b",
    re.I)


def _sealing_grout(memory, reading):
    """The verdict for "is it worth sealing", the method for "how do i seal"."""
    asks = set(reading.get("asks") or ())
    said = str(reading.get("clean") or "")
    if _SEAL_COST.search(said):
        return ("A one litre bottle of penetrating sealer is usually £15 to £30 and does a "
                "bathroom's grout twice over; the sealing itself is an afternoon's work.")
    if _SEAL_WHEN.search(said):
        return ("New grout wants about 48 hours to cure before you seal it, then a shower's "
                "grout wants resealing every year or two, or sooner if water stops beading.")
    if _SEAL_WHERE.search(said):
        return ("A tile shop or a DIY shed sells penetrating sealer: ask for an impregnating "
                "sealer for cement grout, not a film-forming one that peels in a shower.")
    if _SEAL_THINGS.search(said):
        return ("A penetrating sealer for cement grout, a small brush or applicator and a "
                "cloth: clean the grout, let it dry for a day, work the sealer into the joints "
                "and wipe the tiles after ten minutes.")
    if asks & {"yesno", "recommend", "opinion"} or _SEAL_WORTH.search(said):
        return ("Worth it on cement grout in a shower or bathroom, less so in a dry hall: a "
                "penetrating sealer keeps water and stains out of the joints for a year or two, "
                "though it does not make the grout waterproof, and epoxy grout needs none. Clean "
                "it and let it dry for a day first, or the sealer locks the dirt in.")
    return ("Clean the grout and let it dry for at least a day, then work a penetrating sealer "
            "into the joints with a small brush or applicator, not a sponge. Wipe the face of the "
            "tiles with a damp cloth after ten minutes so no film dries on them, and keep water "
            "off it for 24 hours. Reapply every year or two in a shower.")


ENTRIES.append(entry(
    "grout-sealing",
    (("grout", "grouting", "tile grout", "tile joints"),
     ("seal", "seals", "sealed", "sealing", "sealer", "sealant", "reseal", "resealing")),
    _sealing_grout,
    # painting over, replacing or laying the tiles is a different job, and the tiling row owns
    # those lines; cleaning the grout keeps its own answer.
    avoid=("paint tiles", "paint the tiles", "cover the tiles", "tile the", "replace the tiles",
           "re-grout", "regrout", "clean the grout", "clean my grout", "clean grout"),
    bias=1))

# ------------------------------------------------------- how often a household job comes round
# A "how often" line asks for the interval, and the job's own card answers the method. Measured
# on main `ea156d27`, with a fresh chat for each line: "how often should i clean the oven" got the
# bicarbonate paste with no interval in it at all, "how often should i hoover" got how to wash the
# filter, "how often should i clean the kitchen floor" got the mop method, and "how often should i
# clean the bathroom" got a hydration card. The interval is the answer, so it is here, one row per
# job, written from one table: adding a job is a line of data and nothing else.
#
# The frequency words come from `lookup`, where a row that asks the same job two ways reads them:
# "how do i clean the oven" is the method and "how often should i clean the oven" is the interval.
# They are a key part of their own, not only `ask`, because a line with no frequency word in it is
# the method's question and keeps the answer it had. A line that does hold one has to out-score
# that method card, which names the same subject and the same job words, so `bias=1` is the nudge
# for exactly that tie: the row with the frequency words matched is the one that knows the ask.

# id, subject, the job said as a verb, the interval, and what would mean the line is about
# something else. The interval is the first sentence, because that is what was asked for.
HOW_OFTEN = (
    ("how-often-fridge",
     ("fridge", "fridges", "refrigerator", "refrigerators"),
     ("clean", "cleaning", "wipe", "wiping", "wash", "washing", "empty", "emptying", "smell",
      "smells", "smelling", "dirty"),
     "Once a month for a proper empty-out and wipe, with a shelf done the moment something spills. "
     "The door seals and the little drain hole at the back are where the smell starts, so they get "
     "done every time; a bowl of bicarbonate of soda on a shelf only holds it between cleans.",
     # the freezer's own defrosting, a fridge that has stopped working, and the keeping times for
     # food are all other rows, and so is the buying question
     ("freezer", "freezers", "defrost", "defrosting", "not working", "broken", "warm",
      "temperature", "setting", "thermostat", "how long does", "keep", "left out", "buy",
      "buying", "which", "best", "size",
      # the water filter is a filter's line, and a bulb or a shelf being changed is not a clean
      "filter", "filters", "water filter", "light", "bulb", "shelf out", "drawer")),
    ("how-often-bathroom",
     ("bathroom", "bathrooms", "ensuite", "loo", "toilet", "toilets", "shower screen",
      "shower cubicle", "shower tray", "basin", "bathroom tiles"),
     ("clean", "cleaning", "scrub", "scrubbing", "wipe", "wiping", "wash", "washing", "bleach",
      "disinfect", "dirty"),
     "Twice a week for the loo, the basin and the shower screen, and once a week for the bath, the "
     "tiles and the floor if anyone showers there every day. The grout and the sealant round the "
     "bath want doing every couple of months, before they go black rather than after.",
     # a person washing themselves is the health domain's line, and a blocked or leaking fitting
     # is a plumbing job
     ("myself", "shower myself", "bathe", "bathing", "bath the", "baby", "blocked", "blockage",
      "leak", "leaking", "dripping", "smell from", "drain", "mould on the ceiling")),
    ("how-often-worktops",
     ("worktop", "worktops", "kitchen surfaces", "surfaces", "hob", "splashback", "cupboard fronts",
      "kitchen"),
     ("clean", "cleaning", "wipe", "wiping", "wash", "washing", "disinfect", "dirty", "greasy"),
     "The worktops and the hob every day after cooking, the splashback and the cupboard fronts "
     "once a week, and behind and under the appliances once a month. Hot soapy water and a cloth "
     "does all of it: it is the wiping and the steam that lift the grease, not the spray.",
     # the floor, the oven, the fridge, the bin and the sink are their own rows, and a kitchen
     # being fitted or bought is nobody's cleaning question
     ("floor", "floors", "mop", "mopping", "oven", "fridge", "freezer", "bin", "bins", "sink",
      "drain", "dishwasher", "washing machine", "tiles on the floor", "fit", "fitting", "buy",
      "buying", "renovate", "extension",
      # a cloth, a towel or a sponge is washed on its own timetable, and "how often should i wash
      # kitchen towels" is not the worktop's answer
      "towel", "towels", "tea towel", "tea towels", "cloth", "cloths", "dishcloth", "dishcloths",
      "flannel", "sponge", "sponges", "washing up", "rubbish", "recycling")),
    ("how-often-hoover",
     ("hoover", "hoovering", "vacuum", "vacuuming", "vacuum cleaner", "robot vacuum"),
     ("clean", "cleaning", "do", "doing", "run", "running", "use", "using", "empty", "emptying",
      "change", "changing", "replace", "replacing"),
     "Once a week in the rooms you actually use, and twice if there is a pet, an allergy or a "
     "crawling baby. Empty the bin or the bag when it is two-thirds full rather than when it is "
     "packed, and the filter every month or two - a blocked filter is why a vacuum starts to "
     "smell.",
     # a vacuum that is broken, blocked or being bought is another row, a carpet or a rug is a
     # floor and the floor's own interval row answers it, and the bag is the row's own now:
     # "how often should i change the hoover bag" was a shrug while `bag` stood the row down
     ("carpet", "carpets", "rug", "rugs", "floor", "floors",
      "broken", "not working", "blocked", "suction", "smell", "smells", "burning", "cord",
      "battery", "buy", "buying", "best", "which", "cheap", "repair", "filter",
      # a car is vacuumed by the car's own answer, and the routine here is about rooms
      "car", "cars", "van", "caravan", "boot", "motorhome"),
     # the machine's own filter row answers "how often should i hoover" today, because "how often"
     # is in its key for the filter interval, so this row has to out-score it rather than tie
     2),
    ("how-often-washing-machine",
     ("washing machine", "washer", "washing machines",
      # "how often should i run a service wash" was the exercise card, because "run" and "wash"
      # are what an exercise interval is keyed on: the thing being washed is named here
      "service wash", "maintenance wash"),
     ("clean", "cleaning", "service", "servicing", "wash", "smell", "smells", "smelling", "dirty",
      "descale", "descaled"),
     "A hot service wash once a month, the filter and the detergent drawer every couple of months, "
     "and the door left ajar between washes - there is no yearly service to book on a washing "
     "machine. If it already smells, a 90C wash with a machine cleaner or a cup of bicarbonate of "
     "soda is the fix, and the drawer is usually where it started.",
     # a machine that will not drain, spin or heat is a fault, and one being bought or repaired is
     # the rule about small appliances
     ("not draining", "wont drain", "won't drain", "not spinning", "wont spin", "won't spin",
      "error", "leaking", "leak", "broken", "repair", "worth", "replace", "buy", "buying",
      "which", "best", "tumble dryer", "dishwasher")),
    ("how-often-kettle",
     ("kettle", "kettles"),
     ("descale", "descaling", "descaled", "clean", "cleaning", "scale", "limescale", "furred",
      "furring", "clean out"),
     "Once every couple of months in a hard-water area and once every six months where the water "
     "is soft: the scale is only calcium, but a thick layer makes the kettle slow and leaves a "
     "scum on the tea. Half water, half white vinegar or a sachet of citric acid, boiled and left "
     "half an hour, then boiled fresh twice and tipped away.",
     ("buy", "buying", "best", "which", "cheap", "broken", "not working", "switch", "boil",
      "temperature", "energy", "how much")),
    # "how often should i dust" was a shrug: there is an answer, and it is an interval, so the
    # table above is where it belongs. The word "dust" is a powder in a lot of other lines (icing
    # sugar, plaster, a brick, a cocoa tin), and those are somebody else's job.
    ("how-often-dust",
     ("dust", "dusting", "dusted"),
     ("dust", "dusting", "dusted", "clean", "cleaning", "wipe", "wiping", "go over", "do",
      "doing", "surfaces", "furniture", "house", "home", "rooms", "room", "flat", "bedroom",
      "bedrooms", "living room", "lounge", "skirting", "shelves", "shelf", "tops", "hoover",
      "vacuum"),
     "Once a week in the rooms you use every day, and every couple of days in a bedroom, in a "
     "room somebody is allergic in, or in a house on a busy road: a soft or slightly damp "
     "microfibre cloth holds the dust instead of pushing it about, and a feather duster mostly "
     "just moves it to the next shelf. Work from the top down - the tops of the cupboards and the "
     "picture rails first, the skirting and the floor last - so what you lift off lands somewhere "
     "you are going to vacuum anyway.",
     ("mite", "mites", "mattress", "mattresses", "bedding", "pillow", "pillows", "duvet",
      "cushion", "cushions", "blind", "blinds", "curtain", "curtains", "lamp", "lampshade",
      "shade", "cooker hood", "extractor", "vent", "dryer", "drier", "tumble dryer",
      "tumble drier", "filter", "filters", "car", "cars", "van", "bake", "baking", "cake",
      "cakes", "cocoa", "icing", "icing sugar", "sugar", "flour", "chalk", "plaster", "brick",
      "cement", "sawdust", "coal", "workshop", "builders", "building work", "building site",
      "renovation", "refurbishment", "demolition", "rubble", "fire", "explosion", "footprints",
      "cast", "print", "prints", "how much", "spend")),
    # The filter a tumble dryer needs clearing is a job with an interval of its own, and it had
    # none: "how often should i clean the filter in my tumble dryer" was a shrug while the
    # lint-and-hair cards held the words for it without an interval between them.
    ("how-often-dryer-filter",
     ("tumble dryer", "tumble drier", "dryer", "drier", "dryers", "driers", "lint filter",
      "lint trap", "lint screen"),
     ("clean", "cleaning", "cleaned", "empty", "emptying", "cleared", "clear", "rinse",
      "rinsing", "wash", "washing", "check", "checking", "change", "changing", "replace",
      "replacing", "filter", "filter's"),
     "Once every few loads, and after every single one if you dry towels, fleeces or anything "
     "else that sheds: pull the filter out, peel the lint off in one sheet, rinse it if the mesh "
     "takes a rinse, and let it dry before it goes back in. A clogged filter is the commonest "
     "reason a dryer takes two cycles over a load and the back of the machine feels hot, and lint "
     "left to build up is what catches light.",
     ("car", "cars", "van", "paint", "spray", "oil", "air filter", "water filter", "hoover",
      "vacuum", "vacuum cleaner", "fridge", "freezer", "kettle", "washing machine", "dishwasher",
      "pool", "fish tank", "aquarium", "shower", "tap", "worth", "buy", "buying", "best",
      "broken", "not working", "not heating", "wont heat", "won't heat", "smell", "smells",
      "smelly", "fire", "hose", "vent", "condenser", "heat pump", "how much", "spend")),
    # "how often should i run the dishwasher" was the exercise card - "three sessions a week is the
    # number to aim for, with a day off between them, and it is the same for running, the gym or
    # swimming" - because the machine was not in the interval rows at all. The run and the clean
    # are two questions: this one is how often it goes on.
    ("how-often-dishwasher-run",
     ("dishwasher", "dishwashers", "dish washer", "dish washers"),
     ("run", "running", "put on", "putting on", "use", "using", "switch on", "turn on", "going",
      "go", "load", "loads", "load it", "should i"),
     "Once a day is right for most households: a full load uses less water than washing up by "
     "hand, and rinsing the plates first wastes the point of it. Wait until it is full, then run "
     "it, and leave the door ajar afterwards so the seals dry out.",
     # the machine being cleaned is the other row's interval, a machine that has stopped is a
     # repair, and the shopping and salt questions are their own.
     ("clean", "cleaning", "filter", "seal", "salt", "rinse aid", "smell", "smells", "smelly",
      "not draining", "not heating", "broken", "repair", "fault", "error", "buy", "buying",
      "best", "worth", "which", "price", "tablet", "tablets", "hard water", "limescale",
      "descale", "descaler", "descaled", "descalers", "service", "engineer")),
    # The table above covers the jobs with a card of their own. These are the ones people ask the
    # interval about and the answer was the method: "how often should i wash my duvet" got the drum
    # and the temperature, "how often should i clean my oven trays" got the wipe of the fat, "how
    # often should i wash bathmats" got the 40C cycle, "how often should i change the water in a
    # vase" got the trimming, and the water filter in a fridge was a shrug. Each row here is the
    # same five fields as the rest, so it is a line of data and nothing else.
    #
    # A duvet and a pillow are washed on their own timetable. The cover and the pillowcases belong to
    # `bedsheets-often` (changed once a week) and the drum method to `duvet-wash`, so both are in the
    # avoid list: this row is only ever the interval.
    ("how-often-oven-trays",
     # the trays, the racks and the shelves - the things that lift out. Not the door and not the
     # glass: those are `oven-often` (every two to three months for the inside) and `oven-glass`,
     # and both already answer, so "how often should i clean the oven door" is not this job.
     ("oven tray", "oven trays", "baking tray", "baking trays", "grill pan", "grill pans",
      "oven rack", "oven racks", "oven shelf", "oven shelves", "wire rack", "wire racks",
      "roasting tin", "roasting tins", "cooling rack", "cooling racks"),
     ("clean", "cleaning", "cleaned", "scrub", "scrubbing", "soak", "soaking", "wash",
      "washing", "do", "doing", "degrease", "wipe", "wiping"),
     "After every roast that leaves fat in it for the tray, rather than on a timetable, and the "
     "racks and shelves want a soak every couple of months, or as soon as the oven smells of last "
     "week's dinner: they lift out, soak in the bath with a couple of dishwasher tablets, and go "
     "back in dry. Tray bake tins rust if they are left to drip-dry, so they go back in dry too.",
     ("buy", "buying", "which", "best", "size", "replace", "broken", "not working", "element",
      "thermostat", "fan", "door seal", "door", "hinge", "glass", "window", "enamel", "bulb",
      "light", "tray bake", "sheet pan", "inside the oven", "self clean", "pyrolytic", "smoke",
      "smoking", "how do i", "how to")),
    # The dishwasher's own card answers how to clean it (the filter, the seal, the empty hot cycle),
    # and a dishwasher that smells or leaves grit is nearly always this job undone, so the interval
    # is here.
    ("how-often-bath-mat",
     ("bath mat", "bath mats", "bathmat", "bathmats", "pedestal mat", "pedestal mats",
      "shower mat", "shower mats"),
     ("wash", "washing", "washed", "clean", "cleaning", "change", "changing", "replace",
      "replacing", "machine"),
     "Once a week, and twice if the bathroom is shared or there is a toddler in the house: a mat "
     "holds every wet footprint, so it goes in at 60C with the towels and comes out the thing that "
     "stops the floor smelling of damp. Two mats that take turns is the version that always has a "
     "dry one down.",
     ("curtain", "curtains", "towel", "towels", "carpet", "carpets", "doormat", "doormats",
      "rug", "rugs", "buy", "buying", "which", "best", "non slip", "not slip", "mould", "mildew",
      "smell", "smells", "how do i", "how to")),
    # Flowers in a vase: the trimming card answers how to keep them, and how often the water is
    # changed was the same reply, which answers nothing the line asked.
    ("how-often-vase-water",
     # A cut bunch in a vase, not a plant in the ground: "how often should i water my flowers"
     # and "how often should i water my roses" are the garden's, so the subject is the vase, the
     # bunch and the words "water for flowers", and every growing word stands the row down.
     ("vase", "vases", "bouquet", "bouquets", "bunch of flowers", "bunch of tulips",
      "water for flowers", "water for the flowers", "cut flowers", "flowers in a vase",
      "flowers in the vase", "flowers in water"),
     ("water", "watering", "change", "changing", "changed", "refresh", "refreshing", "top up",
      "topping up", "replace", "replacing", "clean", "cleaning", "vase water"),
     "Every two days, and every day in warm weather: fresh water, a rinse of the vase, and a fresh "
     "cut on the stems at the same time, because the water clouds from what the stems give off and "
     "the stems seal over where they were cut. A drop of bleach or a spoon of sugar is the old "
     "trick, and the cut is the part that actually works.",
     ("garden", "plant", "plants", "grow", "growing", "buy", "buying", "which", "best", "cheap",
      "plant food", "feed", "fertiliser", "deadhead", "wilt", "wilting", "dying", "drooping",
      "keep fresh", "last longer", "outside", "hanging basket", "bedding plants", "seed", "sow",
      "roses", "rose", "rose bush", "tulips in the garden", "daffodils", "lilies", "lily",
      "peace lily", "orchid", "soil", "compost", "lawn", "shrub", "shrubs", "tree", "trees",
      "border", "borders", "pot", "pots", "houseplant", "houseplants", "how do i", "how to")),
    # The water filter inside a fridge is a consumable with an interval, and the row for cleaning
    # the fridge stands it down, so the question was a shrug.
    ("how-often-fridge-filter",
     ("fridge", "fridges", "refrigerator", "water filter", "fridge filter", "filter in the fridge",
      "filter in my fridge"),
     ("filter", "filters", "change", "changing", "replace", "replacing", "clean", "cleaning"),
     "Every six months for the water filter inside the fridge, and most of the ones that have one "
     "put a light on the door when it is due. The fridge itself is a different job - once a month "
     "for a proper empty-out and wipe.",
     ("freezer", "freezers", "defrost", "not working", "broken", "temperature", "setting",
      "buy", "which", "best", "water tastes", "smell", "smells", "vacuum", "hoover", "air filter",
      "car", "kettle", "washing machine", "dishwasher", "clean the fridge", "wipe out",
      "how do i", "how to")),
    ("how-often-shower-head",
     # "tap" is not a subject of its own: "how often should i clean the taps" is the wash-up and
     # the overflow card, which already says a rinse after every wash and a wipe once a week, so a
     # tap line arrives here only when it names the scale
     ("shower head", "showerhead", "shower heads", "showerhead and hose", "limescale", "scale",
      "scaled", "chalky"),
     ("clean", "cleaning", "descale", "descaling", "descaled", "soak", "soaking", "scrub",
      "remove", "get rid of", "blocked", "spray", "sprays", "jets", "white", "chalky", "furred"),
     "Every couple of months for a shower head in a hard-water area, and every three months or so "
     "where the water is soft; a tap aerator is the same job on the same timetable. The test is "
     "not the calendar but the spray: the moment the jets start going sideways, take it off and "
     "leave it an hour in half water, half white vinegar, or hang a freezer bag of it over the "
     "head, then rinse it and run the shower for a minute.",
     # a shower being taken, a blocked drain, a new shower or a low-pressure supply are other
     # questions, and the kettle and the washing machine have rows of their own above
     ("myself", "shower myself", "bath", "bathe", "bathing", "leak", "leaking", "drain",
      "blocked drain", "pressure", "pump", "electric shower", "tray", "cubicle", "screen",
      "kettle", "washing machine", "dishwasher", "buy", "buying", "best", "replace",
      "replacing", "new shower", "fit", "fitting", "install", "installation", "how much",
      "spend", "cost")),
    # A duvet is washed on a schedule nobody states in the answer that tells you how to wash it
    # without wrecking a 9kg drum, so the interval is the part that went missing.
    ("how-often-duvet",
     ("duvet", "duvets", "quilt", "quilts", "eiderdown"),
     ("wash", "washing", "washed", "clean", "cleaning", "cleaned", "change", "changing",
      "launder", "laundering", "launderette", "dry clean", "dry cleaning", "cleanse"),
     "Twice a year for a duvet in a cover that is washed every week or two, and every couple of "
     "months if you sweat at night, sleep with a pet on the bed, or wake up sneezing. Feather and "
     "down want a big drum and hours on low heat with dryer balls; a hollowfibre one survives a "
     "normal machine and a cool tumble. A duvet is only washed when it needs it, so the honest "
     "signal is a slightly musty smell when you shake it out.",
     # the cover, the sheets and the pillow are their own rows, and buying one is another question.
     # A bare "size" was standing this row down for "how often should i wash a king size duvet",
     # which is the interval question with the bedding words in it: only the asking shapes are
     # avoided, so the size of the thing does not hide the question about it.
     ("cover", "covers", "duvet cover", "duvet covers", "sheet", "sheets", "bedding", "pillow",
      "pillows", "mattress", "buy", "buying", "best", "tog", "which", "what size", "which size",
      "what tog", "allergy", "allergies", "how much", "cost", "price", "iron", "ironing")),
    # A pillow is not a duvet on a shorter clock: it is washed on its own, and the line that asks
    # about it was excluded from the duvet row and given the drum method instead.
    ("how-often-pillows",
     ("pillow", "pillows"),
     # only the washing words: "how often should i replace my pillows" asks the lifespan, and the
     # card that says fold it in half and let go answers it - that is a different clock again
     ("wash", "washing", "washed", "clean", "cleaning", "cleaned", "launder", "laundering"),
     "Every three to four months for the pillow itself, and every six weeks or so if you sweat at "
     "night, sleep with a pet on the bed or wake up sneezing. Two pillows fit in most 7kg machines "
     "two at a time; a memory foam pillow is not machine washed at all - sponge the cover and air "
     "it. A pillow past its wash is still a pillow past its life: fold it in half and let go, and "
     "if it stays folded it is done.",
     ("case", "cases", "pillowcase", "pillowcases", "pillow case", "pillow cases", "cover",
      "covers", "sheet", "sheets", "bedding", "buy", "buying", "best", "which", "how much",
      "cost", "price", "memory foam", "stain", "smell",
      # the lifespan question keeps the flat-pillow card
      "replace", "replacing", "replacement", "flat", "flattened", "lumpy", "how long",
      "how many years", "last")),
    # And a dishwasher is cleaned on a schedule of its own: the filter, the seal and the salt are
    # a monthly job, and the card that says how to clean it never said when.
    ("how-often-dishwasher",
     # the parts are named without the machine: "how often do i need to clean the spray arms" is
     # the same timetable, and there was no row for it at all
     ("dishwasher", "dishwashers", "dish washer", "spray arm", "spray arms", "door seal"),
     ("clean", "cleaning", "cleaned", "service", "servicing", "descale", "descaling", "rinse",
      "rinsing", "filter", "salt", "smell", "smells", "smelling", "smelly", "dirty"),
     "Once a month for the filter, the door seal and the spray arms, and a hot empty cycle with a "
     "dishwasher cleaner or a bowl of white vinegar on the top rack; the salt and the rinse aid "
     "are checked weekly, because running out of either is what makes everything come out "
     "cloudy. In a hard-water area the descale wants doing every couple of months as well.",
     # a machine that will not drain or heat is a fault, dishes that come out dirty are a loading
     # question, and buying one is the appliance rule
     ("not draining", "wont drain", "won't drain", "not heating", "error", "leaking", "leak",
      "broken", "repair", "dishes", "plates", "glasses", "cutlery", "load", "loading", "tablets",
      "powder", "buy", "buying", "best", "which", "size", "how much", "cost", "price")),
)

for _row in HOW_OFTEN:
    # A row is the five fields above, and a sixth only where the job's own card ties with it.
    _id, _subject, _job, _interval, _not_this = _row[:5]
    _bias = _row[5] if len(_row) > 5 else 1
    # `ask` holds the frequency words as well as the third key part: the key scores, the ask is what
    # makes the row a frequency answer, and without one in the line the job's own card keeps the
    # turn ("how do i clean the oven" is the paste, not an interval).
    ENTRIES.append(entry(_id, (_subject, _job, HOW_OFTEN_WORDS), _interval,
                         ask=HOW_OFTEN_WORDS, avoid=_not_this, bias=_bias))

# The words that make a dusting line a method question, kept next to the row that asks for them:
# the `ask` gate and the guard read the same list, so there is one answer to "is this a how-to".
DUST_METHOD_ASK = ("how do i", "how to", "how should i", "what do i use", "what should i use",
                   "best way", "right way", "properly", "proper", "technique", "whats the best",
                   "what is the best")


# Dusting is the one household job people ask for the method of and nobody answers: "how do i dust"
# and "whats the best way to dust" were three different shrugs ("I don't know enough to answer that
# honestly", "a quick search online"), and "how do i dust a room" was the card about where household
# dust comes from. The method is not a secret: a damp microfibre and the order you go in. The
# frequency rows above keep their own lines through `ask`, and a line that asks why the house is
# dusty is still `dust-where`.
ENTRIES.append(entry(
    "dust-method",
    (("dust", "dusting", "dusted", "dust a room", "dust the room", "dusting a room"),
     ("how do i", "how to", "how should i", "what do i use", "what should i use", "best way",
      "right way", "properly", "proper", "technique", "dust", "dusting", "clean", "cleaning",
      "wipe", "wiping", "go over", "do", "does", "start", "room", "rooms", "house", "home",
      "surfaces", "shelves")),
    "A soft or slightly damp microfibre cloth, rung out so it is barely wet, and a bucket of warm "
    "water with a drop of washing-up liquid: it holds the dust against the cloth instead of "
    "pushing it back into the air the way a feather duster does. Go from the top down, the tops "
    "of the cupboards and the picture rails first and the skirting boards and floor last, so "
    "what you lift off lands somewhere you are going to vacuum anyway, and do the flat surfaces "
    "before the ornaments on them. Rinse the cloth in the bucket as soon as it stops picking "
    "dust up, work a room a wall at a time rather than round and round, and leave the radiators "
    "and the tops of the doors for the same pass - that is where the grey layer builds up first.",
    # a why/what line about household dust is `dust-where`, the interval lines are the table
    # above, and a blinds, mattress, filter, cake or workshop line belongs to its own row
    ask=DUST_METHOD_ASK,
    # "do i need to dust" and "should i dust" are not method questions, but both are reads the
    # want rule lets a row in on without its ask: the guard is what keeps the interval's own lines
    # on the interval, and it is the reason this row is not simply a subject and a shrug.
    guard=lambda understood: any(word in the_line(understood) for word in DUST_METHOD_ASK),
    avoid=HOW_OFTEN_WORDS + (
        "why", "where", "come from", "comes from", "so much", "so dusty", "allergy", "allergies",
        "allergic", "asthma", "sneeze", "sneezing", "mite", "mites", "mattress", "mattresses",
        "pillow", "pillows", "duvet", "bedding", "bed", "blind", "blinds", "curtain", "curtains",
        "lamp", "lampshade", "shade", "cooker hood", "extractor", "vent", "filter", "filters",
        "dryer", "drier", "tumble dryer", "tumble drier", "hoover", "vacuum", "car", "cars",
        "van", "bike", "bikes", "bicycle", "motorbike", "motorcycle", "chain", "computer",
        "laptop", "pc", "keyboard", "phone", "screen", "console", "tv", "television", "monitor",
        "bake", "baking", "baked", "cake", "cakes", "cocoa", "icing", "icing sugar",
        "sugar", "flour", "chalk", "plaster", "brick", "cement", "sawdust", "coal", "workshop",
        "builders", "building work", "building site", "renovation", "refurbishment",
        "demolition", "rubble", "fire", "explosion", "footprints", "cast", "print", "prints",
        "skirting", "radiator", "radiators", "cupboard", "cupboards", "woodwork", "paintwork",
        "fan", "light fitting", "books", "lego", "plant", "plants", "leaves"),
    bias=2))

# The household standbys, asked as "what can i clean with vinegar" and "is bicarbonate of soda
# good for cleaning": the two were a shrug and a search hedge, while every single job they do
# (the kettle, the drain, the grout) had an answer of its own. This row is the list, so the jobs
# that have a row of their own stand it down.
# The two shapes this row must not take, though each holds a standby and an ask: "is vinegar good
# for you" is a question about eating and health, and "can i use vinegar instead of lemon juice"
# is the swap card's, which names what goes in its place. Both were answered with the list of
# cleaning jobs, which is the wrong kitchen entirely: one replaced an honest punt on a health
# question, the other replaced a real answer about what to use instead.
NOT_A_CLEANING_ASK = re.compile(
    r"\b(?:good|bad|safe|healthy|health|harmful)\b[^.?!]*\b(?:you|us|me|people|children|kids|"
    r"skin|teeth|stomach|diet|body)\b"
    r"|\b(?:instead of|substitute|substitutes|substituting|swap|swaps|swapping|replace|replaces|"
    r"replacing|alternative to)\b", re.I)


# A line that opens as a question is asking one; a line that opens with the standby is naming it.
# "white vinegar or a proper cleaner" is the choice row's, and it holds a cleaning word ("cleaner"
# is the product there, not the verb), so the shape of the line is the only thing that tells the
# two apart. A question mark anywhere counts, because "vinegar for cleaning?" is a question too.
QUESTION_SHAPE = re.compile(
    r"^\s*(?:what|whats|what's|which|how|is|are|was|were|does|do|did|can|could|should|would|will|"
    r"any|tell me|i want to know|remind me)\b", re.I)


def _not_a_cleaning_ask(understood):
    """False when the line asks whether the standby is good for a person, or what replaces it."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    if NOT_A_CLEANING_ASK.search(text):
        return False
    return "?" in text or bool(QUESTION_SHAPE.match(text))


ENTRIES.append(entry(
    "what-the-standbys-clean",
    (("vinegar", "white vinegar", "malt vinegar", "bicarbonate of soda", "bicarb", "baking soda",
      "soda crystals", "lemon juice", "citric acid", "salt"),
     # The line has to say the cleaning, not just the standby: the loose asks this row started
     # with ("use", "work", "worth", "any good", "what can i", "instead of") made it take turns it
     # had no business in - "white vinegar or a proper cleaner" after a shower-glass question lost
     # its answer to the list, and "my neighbour uses vinegar, will that work" after an ants
     # question got the list instead of the ant advice. A cleaning word is the frame of the
     # question, and a line without one is some other question that happens to hold a standby.
     ("clean", "cleaning", "cleaned", "cleaner", "cleaners", "cleans", "scrub", "scrubbing",
      "scour", "scouring", "wash", "washing", "disinfect", "disinfecting", "sanitise",
      "sanitising", "degrease", "degreasing")),
    "White vinegar for limescale, glass, the kettle and the shower screen; bicarbonate of soda "
    "for scouring a sink or a pan, a smelly fridge and a slow drain; lemon juice and salt for a "
    "wooden board and a copper pan. Two rules cover most of it: no vinegar on marble, stone or "
    "grout, because the acid eats them, and never vinegar with bleach, because the two together "
    "give off chlorine gas. Warm water and washing-up liquid still does most of the work in a "
    "kitchen, and the standbys are for the jobs where it does not.",
    guard=_not_a_cleaning_ask,
    avoid=("mould", "mold", "mildew", "damp", "drain", "plughole", "wasp", "ant", "ants",
           "weed", "weeds", "kill", "kills", "drink", "drinking", "eat", "recipe", "cook",
           "cooking", "chip", "chips", "batter", "cake", "sauce", "pickle", "dressing",
           # "make" is the recipe ask, but "baking soda" is the cleaner itself, so the word
           # "baking" is not here: "is baking soda good for cleaning" was stood down by it
           "make", "makes", "made", "making", "bread", "soup", "meal",
           "descale", "scale", "limescale", "kettle", "coffee machine", "washing machine",
           "dishwasher", "toilet", "oven", "window", "windows", "floor", "floors", "grout",
           "iron", "mattress", "carpet", "sofa", "fridge", "freezer", "bbq", "barbecue",
           "car", "caravan", "bike", "garden", "patio", "decking", "pool",
           # a surface with a card of its own is its card's question, and "glass" is the one that
           # gave this away: "does vinegar clean glass" was answered with the list of standbys.
           "glass", "glasses", "mirror", "mirrors", "shower", "sink", "sinks", "hob", "worktop",
           "worktops", "tile", "tiles", "bath", "table", "tables", "wood", "wooden", "laminate",
           "vinyl")))

# --- the rota, rather than how to clean one thing --------------------------
# "whats a good cleaning routine" reached nothing at all on main: every row in this domain is a
# surface or a stain, and the habit row in `routines.py` stands down on "cleaning".
ENTRIES.append(entry(
    "a-cleaning-routine",
    (("routine", "routines", "schedule", "rota", "plan", "timetable", "list"),
     ("clean", "cleaning", "house", "housework", "chores", "tidy", "tidying", "home")),
    "Fifteen minutes a day keeps a house, and the daily fifteen is the same three things: make "
    "the bed, wipe the kitchen surfaces and put the dishes away. Then give one room a proper "
    "clean on a weekday rota - bathroom on Monday, kitchen on Wednesday, floors on Friday - and "
    "leave the weekends for bedding and towels, which is one wash each. Fit the monthly jobs (the "
    "oven, the windows, behind the sofa) to the first weekend of the month rather than to a mood, "
    "and do a ten-minute tidy before bed so the morning starts level.",
    bias=3,
    avoid=("how do i clean", "how do i get", "stain", "smell", "smells", "smelly", "mould",
           "limescale", "drain", "toilet", "oven", "carpet", "sofa", "mattress", "window",
           "windows", "floor", "floors", "bathroom", "kitchen", "fridge", "freezer",
           "washing machine", "dishwasher", "hoover", "vacuum", "bleach", "vinegar",
           "bicarbonate", "baking soda", "product", "products"),
    ask=("whats a good", "what is a good", "what's a good", "good", "best", "recommend",
         "suggest", "what should i do", "look like", "how often", "where do i start",
         "keep on top")))

# White linen goes yellow with use and with sweat, and no row held the question: "how do i
# whiten yellowed sheets" was a *spreadsheet* answer, because "sheets" is a Google Sheet, and the
# pillowcase rows answer a pillow, not a bed. The washing-whites row in clothing.py is about
# shirts and its key has no linen in it, so this is the bed's version of the same wash.
ENTRIES.append(entry(
    "whiten-linen",
    (("sheets", "bed sheets", "bedsheets", "fitted sheet", "fitted sheets", "sheet",
      "pillowcase", "pillowcases", "linen", "towels", "towel", "duvet cover"),
     ("whiten", "whiter", "white again", "yellowed", "yellowing", "yellow", "grey", "gray",
      "dingy", "dull", "brighter", "bleach")),
    "Wash them at the hottest the label allows - 60C for cotton - with a scoop of oxygen bleach "
    "rather than chlorine, which yellows elastic and poly-cotton. Soak overnight in a bucket of "
    "hot water with a scoop of oxygen bleach and a scoop of biological detergent if the yellow is "
    "old, then wash as normal. Dry them in daylight: sunlight lifts yellowing better than "
    "anything in a bottle, and a white cotton sheet left out for an afternoon comes back "
    "visibly brighter.",
    # The general stain method owns a stain on a sheet ("how do i get curry out of a sheet"), and
    # how often to change them is the bedding row's question.
    avoid=("curry", "bolognese", "gravy", "ketchup", "blood", "sick", "vomit", "wine",
           "coffee", "tea", "sweat", "how often", "how long", "fold", "folding", "store",
           "storing", "buy", "buying", "size", "iron", "ironing")))
