"""How much of a thing to buy: gravel, topsoil, compost, sand, turf, paving slabs, underlay,
grout and tile adhesive.

These are arithmetic questions, not advice questions. "How much gravel do i need for my drive",
"how many paving slabs for a patio", "how much topsoil do i need", "how much underlay for a 12
square metre room", "how much grout do i need for a 12 square metre floor" and "how much tile
adhesive do i need" were each a shrug, a search hedge, the definition of area or the method for
laying tiles, and never a number. The rate per square metre is the fact; the line's own figures
are the arithmetic, so one row per material answers every size of drive, bed, floor and pit.

The rates are the ones the trade works to: loose material at the depth it is usually laid, a bulk
bag or a tonne turned into square metres, underlay in 15 square metre rolls and grout and
adhesive by the bag, and a tenth more than the sums say because a bag never spreads as far as the
label claims. Underlay, grout and adhesive are here rather than in home.py, which holds the paint
and wallpaper quantities and is past the publisher's one-megabyte limit.

The second turn of a conversation that measured the floor names no size at all - "the room is 4m
by 3m how much carpet" then "and how much underlay" - so the bag rows read the figure from the
turns before when the line has none.
"""
import re

from .lookup import a_sanding_job, entry

ANSWERS = ("home-and-diy", "garden-and-plants", "maths-and-numbers")

_NUM = r"(\d+(?:\.\d+)?)"

# A measurement in the line, as people write it: "4m x 3m", "4 by 3 metres", "12ft x 8ft",
# "10 square metres", "10m2", "3m wide by 5m long". Feet are converted because a drive measured
# in feet is still the same drive.
# The unit can come after either number: "8 by 6 foot", "6 by 8 foot" and "4m by 3" are all one
# measurement, and people write all three. A pair with no unit at all ("a 2 by 4") is not a size
# in metres, so `_area` still wants a unit somewhere in the match.
_PAIR = re.compile(
    _NUM + r"\s*(?:m|metres?|meters?|ft|feet|foot|')?\s*(?:x|by|\*|×|and)\s*"
    + _NUM + r"\s*(?:m|metres?|meters?|ft|feet|foot|')?")
_SQUARE = re.compile(_NUM + r"\s*(?:square\s*(?:metres?|meters?|foot|feet|ft)|sq\s*m|sqm|m2|m²)")
_FEET = re.compile(r"ft|feet|foot|'")
# A number with a unit on it: "2 by 4" is a size of timber, not a room in metres.
_UNIT = re.compile(r"\d\s*(?:m|metres?|meters?|ft|feet|foot|')")

# The depth in the line, when it says one. "at 75mm", "100mm deep", "4 inches thick".
_DEPTH = re.compile(_NUM + r"\s*(mm|cm|in|inch|inches)\b")

# (names, the depth the rate below is quoted at in mm, what one bulk bag or tonne covers at that
# depth in square metres, the bag and the extra note)
_LOOSE = (
    (("gravel", "shingle", "chippings", "chips", "pea gravel", "pea shingle", "pebbles",
      "stones", "slate", "bark", "bark chippings", "woodchip", "wood chips", "mulch", "aggregate"),
     50, 10,
     "A 850kg bulk bag of {thing} covers about 10 square metres at 50mm, and a 25kg bag "
     "about 0.3 square metres",
     "Put a weed membrane down first if you do not want to hoe it, and keep 20mm below the "
     "damp course on a wall so the rain can drain away."),
    (("topsoil", "soil", "loam"), 100, 7,
     "A 850kg bulk bag of {thing} (about 0.7 cubic metres) covers about 7 square metres at "
     "100mm",
     "Screened topsoil, not subsoil, for anything you want to grow; it settles about a fifth, so "
     "fill to slightly proud of the level you want."),
    (("compost", "multipurpose compost", "manure", "composted manure"), 50, 12,
     "A 60 litre bag of {thing} covers about 1 square metre at 50mm, and a 145 litre bag "
     "about 2.5 square metres",
     "For a raised bed, fill the top 300mm with compost and the rest with rougher soil or "
     "rubble at the bottom; a bed one metre by two at 300mm deep takes about 6 bags of 60 "
     "litres."),
    (("sand", "play sand", "sharp sand", "builder's sand"), 50, 0.6,
     "A 25kg bag of {thing} covers about 0.6 square metres at 50mm, and about a tonne and a "
     "half fills a cubic metre",
     "Play sand, washed and graded, for a sandpit rather than builder's sand; cover it at night "
     "so cats and rain leave it alone."),
)

# A paved area also needs what goes under it: 100mm of compacted MOT Type 1, then 30 to 40mm of
# sharp sand mixed 5 to 1 with cement as the bed.
_SLAB = ("Paving slabs",
         "100mm of compacted MOT Type 1, then 30 to 40mm of sharp sand mixed 5 to 1 with cement "
         "as the bed")
def _area(text):
    """The area in square metres the line asks about, or None when it names no size."""
    pair = _PAIR.search(text)
    if pair and _UNIT.search(pair.group(0)):
        one, two = float(pair.group(1)), float(pair.group(2))
        if _FEET.search(pair.group(0)):
            one, two = one * 0.3048, two * 0.3048
        area = one * two
        if 0.2 <= area <= 20000:
            return round(area, 1)
    square = _SQUARE.search(text)
    if square:
        area = float(square.group(1))
        if _FEET.search(square.group(0)):
            area = area * 0.0929
        if 0.2 <= area <= 20000:
            return round(area, 1)
    return None


def _depth_mm(text, default):
    """The depth in the line in millimetres, or the material's usual depth."""
    found = _DEPTH.search(text)
    if not found:
        return default
    amount, unit = float(found.group(1)), found.group(2)
    if unit.startswith("mm"):
        depth = amount
    elif unit.startswith("cm"):
        depth = amount * 10
    else:
        depth = amount * 25
    if 10 <= depth <= 400:
        return depth
    return default


# Sand comes in a 25kg bag and the rest in a builder's bulk bag, so the count has to name the
# bag the shop will hand over.
_BAG_WORD = {"sand": "bag", "play sand": "bag", "sharp sand": "bag", "builder's sand": "bag"}


def _sizes(value):
    """A number of square metres as a person writes it: 12, not 12.0."""
    if abs(value - round(value)) < 0.05:
        return "%d" % round(value)
    return ("%.1f" % value).rstrip("0").rstrip(".")


_A_NUMBER = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
             8: "eight", 9: "nine"}
_A_FRACTION = {0.25: "a quarter", 0.5: "a half", 0.75: "three quarters"}


def _a_bag_count(bags, word):
    """How many bags to buy, said the way a person would: "about half a bulk bag".

    A count was said as a decimal, so a small job was told "4.5 square metres at 50mm needs
    about 0.5 bulk bags of gravel" - a bag you cannot buy, and a half with an s on it. The
    quarters are the ones people say: a quarter, half, three quarters, and one and a half.
    """
    quarters = round(bags * 4) / 4.0
    whole = int(quarters)
    part = round(quarters - whole, 2)
    if quarters < 0.25:
        return "about a tenth of a %s" % word
    if quarters < 1:
        if part == 0.25:
            return "about a quarter of a %s" % word
        if part == 0.75:
            return "about three quarters of a %s" % word
        return "about half a %s" % word
    if quarters >= 9.5:
        return "about %d %ss" % (round(bags) if bags < 20 else round(bags, -1), word)
    if part == 0.75:
        # nobody orders three quarters of a bag: the next whole one is the same errand
        whole, part = whole + 1, 0
        if whole == 1:
            return "about one %s" % word
        return "about %s %ss" % (_A_NUMBER[whole], word)
    if part:
        return "about %s and %s %ss" % (_A_NUMBER[whole], _A_FRACTION[part], word)
    if whole == 1:
        return "about one %s" % word
    return "about %s %ss" % (_A_NUMBER[whole], word)


def _count(value):
    """How a person would say a number of things: "about two and a half", not "2.5"."""
    if value >= 20:
        return "about %d" % round(value, -1)
    if value >= 4:
        return "about %d" % round(value)
    halves = round(value * 2) / 2
    if halves == int(halves):
        word = _A_NUMBER.get(int(halves))
        if word:
            return "about %s" % word
    return "about %s" % (("%.1f" % halves).rstrip("0").rstrip("."))


def _loose_reply(name, understood):
    """The bags one loose material needs at the depth the line asks for."""
    text = " " + (understood.get("clean") or "") + " "
    names, depth, covers, lead, extra = _LOOSE[0]
    for row in _LOOSE:
        if name in row[0]:
            names, depth, covers, lead, extra = row
            break
    thing = names[0]
    for name_word in sorted(names, key=len, reverse=True):
        if name_word in text:
            thing = name_word
            break
    if thing == "sand" and ("sandpit" in text or "sand pit" in text or "play sand" in text):
        # a sandpit is filled with play sand, which is the thing to ask for at the shop, and a
        # square metre of it is a different sum: a 1.2m pit filled to 150mm is about 10 bags
        thing = "play sand"
        lead = ("A 25kg bag of play sand covers about 0.6 square metres at 50mm, so a 1.2m square "
                "sandpit filled to 150mm takes about 10 bags")
    lead = lead.format(thing=thing)
    asked = _depth_mm(text, depth)
    area = _area(text)
    # the coverage is per bag at the usual depth, so it falls as the layer gets deeper
    per_bag = covers * (depth / float(asked))
    if area:
        bags = area / per_bag
        word = _BAG_WORD.get(thing, "bulk bag")
        return ("%s square metres at %dmm needs %s of %s. %s, and it is worth a tenth more "
                "than the sums say. %s" % (
                    _sizes(area), asked, _a_bag_count(bags, word), thing, lead, extra))
    return ("%s. Measure the area and work out the volume at the depth you want, then divide by "
            "what a bag holds, and order a tenth more than the sums say - a bag never spreads as "
            "far as the label claims. %s" % (lead, extra))


def _slabs_reply(memory, understood):
    text = " " + (understood.get("clean") or "") + " "
    area = _area(text)
    # a 500mm slab is four to the square metre, 400mm six and a quarter, 600 x 300 about five and
    # a half; the size in the line wins when it names one
    per_square = 4.0
    size = re.search(_NUM + r"\s*(?:mm)?\s*(?:x|by)\s*" + _NUM + r"\s*(?:mm|cm)?", text)
    if size:
        one, two = float(size.group(1)), float(size.group(2))
        if one < 20:
            one *= 1000
        if two < 20:
            two *= 1000
        if 200 <= one <= 1200 and 200 <= two <= 1200:
            per_square = 1e6 / (one * two)
    side = round(1000 / (per_square ** 0.5))
    if area:
        return ("%s square metres needs %s slabs of %dmm, working at %.1f to the square metre, "
                "with a tenth spare for cuts and breakages. Under them: %s." % (
                    _sizes(area), _count(area * per_square * 1.1), side, per_square, _SLAB[1]))
    return ("Work it out at four 500mm slabs to the square metre, six of 400mm and five and a half "
            "of 600 x 300, then add a tenth for cuts and breakages. Under them: %s." % _SLAB[1])


def _turf_reply(memory, understood):
    text = " " + (understood.get("clean") or "") + " "
    area = _area(text)
    if area:
        return ("%s square metres is %s rolls of turf, ordered a few extra for the edges and "
                "any that go thin. Lay it within a day of delivery, water it the same evening, "
                "and keep off it for a fortnight." % (_sizes(area), _count(area * 1.05)))
    return ("Turf rolls cover about a square metre each, so the area in square metres is the "
            "number of rolls, plus a few for the edges and any that go thin. Lay it within a day "
            "of delivery, water it the same evening, and keep off it for a fortnight.")


_ASKS_MATERIAL = ("how much", "how many", "much ", "many ", "do i need", "will i need",
                  "needed", "need for", "covers", "cover a", "how far does", "bags",
                  "how much do i need", "tonne", "tonnes", "bulk bag")

_ASKS_MATERIAL_AVOID = (
    # a price is a cost question, not a quantity one
    "cost", "costs", "price", "prices", "cheap", "cheapest", "how much does", "how much is",
    "how much are", "quid", "pounds", "£",
    # laying and cleaning are their own cards
    "how do i lay", "how to lay", "how do i clean", "clean", "cleaning", "jet wash",
    "pressure wash", "how do i fix", "repair", "how do i stop weeds", "kill weeds",
)

_MATERIAL_AVOID = (
    # a price is a cost question, not a quantity one
    "cost", "costs", "price", "prices", "cheap", "cheapest", "how much does", "how much is",
    "how much are", "quid", "pounds", "£",
    # laying and cleaning are their own cards
    "how do i lay", "how to lay", "how do i clean", "clean", "cleaning", "jet wash",
    "pressure wash", "how do i fix", "repair", "how do i stop weeds", "kill weeds",
    "how deep", "how thick", "what depth",
    # mortar, pointing and rendering are sand for building, not sand to buy by the bag
    "mortar", "pointing", "render", "rendering", "cement", "screed", "concrete", "ballast",
    "block paving", "bedding", "patio base", "sand base", "for a base",
    # a fish tank is an animal question, and the gravel in it is not a drive
    "fish tank", "fish tank gravel", "aquarium", "tank", "pond", "filter",
    # what depth and what goes under it are the laying cards' questions
    "weed membrane", "membrane", "landscape fabric", "sub-base", "type 1",
    # a count of what is already there is not a buying list: "how many paving slabs were
    # lifted", "how much gravel did i use", "have i got enough sand left" are the stock in the
    # garden, and the bags card reads them as a job to price up
    "were ", "was ", "did i", "did we", "did he", "did she", "did they", "do i own",
    "do we own", "have i got", "have we got", "had left", "are left", "is left", "left in",
    "left over", "got left", "are on the", "is on the", "went down", "used to",
    # a how-long line asks for a length of time, not for a number of bags. The loose asks above
    # ("do i need", "needed", "need for") are wide enough that "how long do i need to leave filler
    # before sanding" was answered with the coverage of a 25kg bag of sand, which is a quantity
    # the person did not ask for. Whole phrases, never a bare stem: a bare "sanding" is matched
    # against "sand" and would stand this row down for every bag-of-sand question too.
    "how long", "long does", "long will", "long do", "long should", "long to", "long before",
    "how many hours", "how many days", "how many minutes", "how much time", "wait before",
)

# "A stone" is a bag of stones and it is a person's weight, and the second one is a diet question:
# "i need to lose a stone" and "i want to lose half a stone before the wedding" were told how far
# a bulk bag of gravel spreads, because this row keys "stones" (people buy them by the bag) and the
# ask "do i need" is in almost every one of those lines. The weights and the diet words are the
# ones a person writes about their own body, so the gravel row stands down for them and the diet
# answer has the line.
_A_PERSONS_WEIGHT = re.compile(
    r"\b(?:lose|loses|losing|lost|shed|shift|drop|dropped|weigh|weighs|weighing|weight|"
    r"put\s+on|gained?|gaining|diet|diets|dieting|slim|slimming|bmi|calories|kilos?|kg|"
    r"pounds|lbs?|pregnant)\b[^.?!]{0,40}\bstone\b"
    r"|\b(?:half\s+a|a\s+stone\s+and\s+a\s+half|two|three|1|2|3)\s+stone\b"
    r"[^.?!]{0,40}\b(?:weight|lose|lost|heavier|lighter|diet|target|goal)\b", re.I)


# ...and a bag of something is not a person's weight, however it is asked: "how much does a bulk
# bag of gravel weigh" was stood down by the diet fence below (the word "weigh") and came back as
# "Prices move too fast for me to know", though it is a quantity question about 850kg of gravel.
_A_MATERIAL_WEIGHT = re.compile(
    r"\b(?:bulk\s+bag|tonne|tonnes|ton\s+of|tons\s+of|bag\s+of|bags\s+of|"
    r"cubic\s+met(?:re|er)|how\s+heavy|a\s+load\s+of)\b", re.I)


# One bulk bag, by what is in it. A tonne bag is a nominal tonne that is filled to about 850kg
# for stone, because that is what the bag and the lorry will take; the lighter the material, the
# less it weighs and the more room it fills, which is why a bag of bark is a skip's worth of
# volume and half a tonne.
_BULK_WEIGHT = (
    (("bark", "woodchip", "wood chip", "mulch"), "about 350kg to 400kg, and it fills close to a "
     "cubic metre and a half"),
    (("compost", "soil", "topsoil", "loam"), "about 700kg to 750kg, which is roughly 0.7 of a "
     "cubic metre"),
    (("sand", "ballast", "sharp sand", "grit sand"), "about 850kg, which is about half a cubic "
     "metre"),
    (("slate", "pebbles", "pebble", "shingle", "chippings", "gravel", "aggregate", "stone",
      "stones"), "about 850kg, which is about half a cubic metre at 20mm"),
)


def _bulk_bag_weight(memory, understood):
    """What one bulk bag weighs, by what is in it."""
    text = " " + str(understood.get("clean") or understood.get("text") or "") + " "
    what, figures = "gravel or sand", "about 850kg, which is about half a cubic metre"
    for names, line in _BULK_WEIGHT:
        hit = next((n for n in sorted(names, key=len, reverse=True)
                    if " " + n + " " in text or " " + n + "s " in text), None)
        if hit:
            what, figures = hit, line
            break
    return ("A bulk bag of " + what + " is " + figures + " - the bags sold as a tonne bag are "
            "filled to about 850kg for stone and sand, because that is what the bag and a "
            "lorry will take, so buy by the bag rather than by the tonne if the weight matters. "
            "That is the same figure the coverage sums use: 850kg of gravel covers about 10 "
            "square metres at 50mm. A 25kg bag is the same material in a bag you can lift, so "
            "34 of them make a bulk bag.")


def _not_a_persons_weight(understood):
    """False when the stone in the line is a weight rather than a bag of them."""
    text = " " + str(understood.get("clean") or understood.get("text") or "") + " "
    if _A_MATERIAL_WEIGHT.search(text):
        return True
    return not _A_PERSONS_WEIGHT.search(text)


# Sanding is the verb, not the bag: "how long do i need to leave filler before sanding" bought a
# 25kg bag of sand because the key word "sand" is read through its endings. The words cannot go in
# the avoid list (that reads them through their endings too, and stands down every real bag of
# sand), so the job is read off the line by `lookup.a_sanding_job` and the row stands aside for it.
# The paint, filler and paper rows have the answer.
def _not_a_sanding_job(understood):
    """Whether the line is about buying sand rather than sanding something down."""
    return not a_sanding_job(understood)

ENTRIES = [
    entry("how-much-gravel", (("gravel", "shingle", "chippings", "pea gravel", "pea shingle",
                               "pebbles", "bark", "bark chippings", "woodchip", "mulch",
                               "slate", "stones", "aggregate"),
                              _ASKS_MATERIAL),
          lambda memory, understood: _loose_reply("gravel", understood),
          # a named material beats the plain area answer: "how much gravel for a 4m by 3m drive"
          # is the bags of gravel, not 12 square metres
          ask=_ASKS_MATERIAL, avoid=_MATERIAL_AVOID,
          guard=_not_a_persons_weight, bias=2),
    entry("how-much-topsoil", (("topsoil", "soil", "loam"), _ASKS_MATERIAL),
          lambda memory, understood: _loose_reply("topsoil", understood),
          ask=_ASKS_MATERIAL, avoid=_MATERIAL_AVOID, bias=2),
    entry("how-much-compost", (("compost", "multipurpose compost", "manure"), _ASKS_MATERIAL),
          lambda memory, understood: _loose_reply("compost", understood),
          ask=_ASKS_MATERIAL, avoid=_MATERIAL_AVOID,
          # "how much compost do i need for a raised bed" was answered with how deep a raised bed
          # should be, which is the neighbouring question: the number of bags is what was asked
          bias=2),
    entry("how-much-sand", (("sand", "play sand", "sharp sand"), _ASKS_MATERIAL),
          lambda memory, understood: _loose_reply("sand", understood),
          ask=_ASKS_MATERIAL, avoid=_MATERIAL_AVOID, bias=2, guard=_not_a_sanding_job),
    # "How much does a bulk bag of gravel weigh" was a price hedge on main ("Prices move too
    # fast for me to know"), because the ask words are the ones the price rows read and the
    # gravel row stands down for "weigh" (the diet fence). A bag's weight is a fact about the
    # material, so it is a table here rather than a price.
    entry("how-heavy-is-a-bulk-bag",
          (("bulk bag", "bulk bags", "tonne bag", "tonne bags", "builder's bag", "builders bag",
            "1 tonne bag", "one tonne bag", "a tonne", "cubic metre", "cubic yard"),
           ("weigh", "weighs", "weighing", "weight", "heavy", "how much", "how many kilos",
            "kilos", "kg", "what does", "tonne", "ton")),
          _bulk_bag_weight,
          ask=("weigh", "weighs", "weight", "heavy", "how much", "kilos", "kg"),
          avoid=("cost", "costs", "price", "prices", "cheap", "how much does it cost",
                 "delivery", "deliver", "hire", "skip", "van", "trailer", "car", "boot",
                 "lift", "move", "carry", "bag of cement", "sandbag", "dog food"),
          bias=2),
    # The base under a patio was nobody's answer: "how much sand for a patio base" was the price
    # of a patio laid (£60 to £120 a square metre), because `how-much-sand` stands down for the
    # words "patio base" and the cost row took the line. What people want is the volume and the
    # cement that goes with it, so this row is the one that has those words.
    entry("sand-and-cement-for-a-base",
          (("sand and cement", "sand cement", "mortar mix", "patio base", "patio foundation",
            "base for a patio", "base for the patio", "sand base", "sub base", "sub-base",
            "type 1", "type one", "slab base", "bedding for slabs", "under the slabs",
            "under patio slabs", "under the paving", "under a patio"),
           _ASKS_MATERIAL),
          "A patio slab sits on a full bed of mortar, not on sand alone and never on five dabs: "
          "40mm to 50mm of sharp sand mixed 4 to 1 with cement, so about half a cubic metre of "
          "sharp sand for 10 square metres - roughly 800kg, most of an 850kg bulk bag - with 5 "
          "bags of 25kg cement. Double both for 20 square metres. Mix it stiff enough to hold "
          "the slab when you tap it down with a mallet and lay to a string line, and under a "
          "patio on soil put 75mm to 100mm of compacted type 1 down first, which is the part "
          "that stops it sinking. Sand alone shifts and washes out, which is why patios laid on "
          "it go wobbly in a couple of winters.",
          # blocks are not this bed at all: a block-paved patio or drive goes on sharp sand
          # alone with kiln-dried sand in the joints, so this row stands down for it and the
          # block row answers, which is a mix 5 parts sand to 1 the job does not use
          ask=_ASKS_MATERIAL,
          avoid=_ASKS_MATERIAL_AVOID + ("block paving", "block paved", "block paver",
                                        "block pavers", "paving blocks", "driveway blocks",
                                        "setts", "block paving drive", "paved drive",
                                        "paving the drive",
                                        # and a wall is not a bed under paving: the brick and
                                        # block rows in home_craft are the ones with those sums
                                        "wall", "walls", "garden wall", "brick", "bricks",
                                        "brickwork", "bricklaying", "render", "rendering",
                                        "block wall", "breeze block", "footing", "footings"),
          bias=3),
    entry("how-many-slabs", (("slabs", "paving slabs", "paving", "pavers", "flags",
                              "patio slabs", "block paving", "paving stones"),
                             _ASKS_MATERIAL),
          _slabs_reply, ask=_ASKS_MATERIAL, avoid=_MATERIAL_AVOID, bias=2),
    entry("how-much-turf", (("turf", "rolls of turf"), _ASKS_MATERIAL),
          _turf_reply, ask=_ASKS_MATERIAL, avoid=_MATERIAL_AVOID, bias=2),
]

# --- the ones sold by the roll and the bag --------------------------------------------------
# Underlay, grout and tile adhesive are counts rather than volumes: the first is sold in 15
# square metre rolls, the other two in 5kg and 20kg bags whose coverage is the trade's own
# figure. On main "how much underlay for a 12 square metre room" got the definition of area,
# "how much grout do i need for a 12 square metre floor" a search hedge, and "how much tile
# adhesive do i need" the method for laying tiles. home.py holds the paint and wallpaper
# quantities and cannot take them, being past the publisher's one-megabyte limit.
_LAST_TURNS = 3


def _asked_area(memory, understood):
    """The area this line is about: from the line, else from the last few turns.

    A floor gets measured in one turn and bought for in the next - "the room is 4m by 3m how
    much carpet" then "and how much underlay" - and the second line names no size at all, so the
    figure from the turn before is the one being asked about.
    """
    area = _area(" " + str(understood.get("clean") or understood.get("text") or "") + " ")
    if area:
        return area
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    for turn in reversed(turns[-_LAST_TURNS:]):
        if not isinstance(turn, dict):
            continue
        for key in ("reply", "user"):
            area = _area(" " + str(turn.get(key) or "") + " ")
            if area:
                return area
    return None


def _rolls(area, covers, spare=1.1):
    """How many rolls or bags of `covers` square metres each an area of `area` needs."""
    return max(1, int(-(-(area * spare) // covers)))


def _underlay_reply(memory, understood):
    area = _asked_area(memory, understood)
    how = ("Roll it across the room rather than along it, butt the seams without overlapping and "
           "tape the joins. Foam crumb is the cheap default; rubber crumb or felt is worth it "
           "under a thin carpet and over a hard floor.")
    if area:
        rolls = _rolls(area, 15)
        return ("%s square metres needs %s roll%s of underlay, a roll being 15 square metres "
                "(1.37m by 11m), and the tenth extra covers the cuts round the edges and under "
                "the doorway. %s" % (_sizes(area), _count(rolls), "" if rolls == 1 else "s", how))
    return ("Underlay is sold by area: a roll is usually 15 square metres (1.37m by 11m), so "
            "measure the floor and add a tenth for the cuts. %s" % how)


def _grout_reply(memory, understood):
    area = _asked_area(memory, understood)
    how = ("Mix it to the thickness of toothpaste and only as much as you can use in half an "
           "hour, because it goes off in the bucket.")
    if area:
        bags = _rolls(area, 4.5)
        return ("%s square metres needs %s bag%s of grout, 5kg each: a bag does 4 to 5 square "
                "metres of 30cm tiles with 3mm joints, and small tiles or wide joints take about "
                "twice as much. %s" % (_sizes(area), _count(bags), "" if bags == 1 else "s", how))
    return ("A 5kg bag of grout does about 4 to 5 square metres of 30cm tiles with 3mm joints, so "
            "a bathroom floor is one bag and a kitchen wall two; mosaic or wide joints take about "
            "twice as much for the same area. %s" % how)


def _adhesive_reply(memory, understood):
    area = _asked_area(memory, understood)
    how = ("Comb it out in one direction, press each tile on across the ridges, and lift one now "
           "and then to check the back is covered.")
    if area:
        bags = _rolls(area, 4.5)
        return ("%s square metres needs %s bag%s of tile adhesive, 20kg each: a bag covers 4 to "
                "5 square metres with a 6mm notched trowel, and large tiles or a deeper notch "
                "take it nearer 3. %s" % (_sizes(area), _count(bags), "" if bags == 1 else "s", how))
    return ("A 20kg bag of tile adhesive covers about 4 to 5 square metres with a 6mm notched "
            "trowel, so a small bathroom wall is one bag; large tiles, a 10mm notch or "
            "back-buttering take it nearer 3 square metres a bag. %s" % how)


_BAG_AVOID = _MATERIAL_AVOID + (
    # grout and adhesive that has failed is a fault, not a quantity
    "coming out", "come out", "crumbling", "crumbles", "crumbled", "powdery", "discoloured",
    "discolored", "stained", "staining", "mouldy", "mildew", "re do", "redo", "re-do",
    "hack out", "chisel", "hollow", "wont set", "won't set", "not setting", "keeps coming",
    "lifting", "cracked", "cracking", "loose", "uneven", "squeak", "squeaking",
    "underfloor heating", "wet room", "tile cutter", "spacers", "which tile", "what tile",
)

_FLOOR_NAMES = ("carpet", "carpets", "carpeting", "laminate", "laminate flooring",
                "wood flooring", "engineered wood", "vinyl", "vinyl flooring", "lino",
                "linoleum", "flooring", "skirting", "skirting board", "skirting boards",
                "coving", "dado rail", "dado rails", "floor tiles", "tile floor")
_LENGTH_NAMES = ("skirting", "skirting board", "skirting boards", "coving", "dado rail",
                 "dado rails")
_FLOOR_AVOID = _MATERIAL_AVOID + (
    # how much is left, how much it cost and how long it lasts are other questions
    "how much left", "left over", "last", "lasts", "how long does",
)


def _floor_reply(memory, understood):
    """Carpet, laminate, vinyl and skirting: something bought by the area or by the length."""
    text = " " + (understood.get("clean") or "") + " "
    pair = _PAIR.search(text)
    if any(word in text for word in _LENGTH_NAMES):
        # a skirting, a coving and a dado rail are a length: the room's perimeter, less the
        # doorways, in whole boards
        if pair:
            one, two = float(pair.group(1)), float(pair.group(2))
            if _FEET.search(pair.group(0)):
                one, two = one * 0.3048, two * 0.3048
            around = 2 * (one + two)
            boards = int(around / 2.4) + 1
            return ("A room %.1fm by %.1fm has %.1f metres round it, so %.1f metres once a couple "
                    "of doorways are taken off - and boards come in 2.4m lengths, so buy %d of "
                    "them. Cut the joints where two boards meet over a straight bit of wall, "
                    "because the joint shows less there than at a corner." % (
                        one, two, around, around - 1.6, boards))
        return ("Skirting, coving and dado rail are bought by the length, not the area: run a tape "
                "right round the room and take off the doorways, about 0.8m each. A doorway takes "
                "the skirting away and the coving carries on over it. Boards come in 2.4m "
                "lengths, so buy whole boards and join them over a straight run, and add one "
                "board for the corners and the cuts.")
    area = _area(text)
    if area:
        waste = round(area * 1.1, 1)
        packs = area * 1.1 / 2.2
        count = _count(packs)
        return ("%s square metres needs %s square metres of carpet or flooring with the tenth "
                "spare for the cuts and the doorway, which is %s packs of laminate at about 2.2 "
                "square metres a pack. A carpet roll is 4m or 5m wide, which is why the shop asks "
                "for the longest and widest measurement of each room rather than the area alone: "
                "a room under 4m wide comes out of one piece, across the width of the roll, and a "
                "wider one needs a join. Keep the offcuts, because a spare pack for a repair "
                "later is worth more than the few pounds it costs." % (
                    _sizes(area), _sizes(waste), count))
    return ("Measure each room on the floor, not on the plan: length times width in metres, and an "
            "L-shaped room as two rectangles added together. Add a tenth for the cuts and the "
            "doorway, so 12 square metres of floor takes 13.2 square metres of carpet, or six "
            "packs of laminate at 2.2 square metres a pack. A carpet roll is 4m or 5m wide, so "
            "the shop wants the longest and the widest measurement of each room as well as the "
            "area, and a room wider than the roll needs a join.")


# --- the concrete under the job ----------------------------------------------------------
# Concrete and the ballast it is mixed from are bought by the volume, and there are two jobs
# almost everybody asks about: setting a post, and a base for a shed. On main "how much concrete
# for a fence post" got the price of a new fence, "how much postcrete do i need" a search hedge
# and "how much ballast for a shed base" the price of a shed.
_CONCRETE_NAMES = ("concrete", "postcrete", "post mix", "postmix", "cement", "ballast",
                   "concrete mix", "ready mix", "readymix", "mot type 1", "hardcore",
                   "sub base", "subbase")
_CONCRETE_ASKS = _ASKS_MATERIAL + ("bags of", "how many bags", "how much concrete",
                                   "how much ballast", "how much cement", "how much postcrete")
# The job the concrete is for is the second signal, so "what concrete for a shed base" is this row
# and not the acid-and-base card in the chemistry rows.
# "which", "what kind of" and "best" are how a person asks which material to buy without asking
# how much: "what concrete for a shed base", "which concrete for a shed base" and "best concrete
# for a shed base" were a search hedge. They are an ask and not a key word, so "which base is
# strongest" is still the chemistry rows'.
_KIND_ASKS = ("which", "what kind", "what type", "best", "recommend", "suitable", "should i get",
              "should i use",
              # "what concrete for a shed base" says what it wants without "kind of", and it was
              # the only one of the three left on a search hedge. The word in front is what keeps
              # "what is concrete made of" out, which is not this row's question.
              "what concrete", "what postcrete", "what cement", "what mortar", "what ballast",
              "what mix", "what ratio")
_CONCRETE_JOBS = ("fence post", "fence posts", "gate post", "post", "posts", "post hole",
                  "post holes", "shed", "shed base", "sheds", "base", "bases", "slab", "slabs",
                  "foundation", "foundations", "footing", "footings", "drive", "driveway",
                  "path", "patio", "wall", "garage")
_CONCRETE_AVOID = (
    "cost", "costs", "price", "prices", "cheap", "cheapest", "how much does", "how much is",
    "how much are", "quid", "pounds", "£", "quote", "hire", "skip",
    # a fault in set concrete, and the trades, are their own cards
    "cracked", "cracking", "crumbly", "dusty", "damp", "rising damp", "render", "rendering",
    "plaster", "mortar", "pointing", "screed", "driveway sealer", "seal",
    # mixing out of a bag of repair mortar is a repair
    "repair", "patch", "filler", "glue", "resin", "anchor", "bolt",
    # and a broken path or drive is a repair job, not a quantity
    "broken", "sinking", "sunken", "uneven", "pothole", "weeds",
    # concrete as a chemical is the chemistry rows': "what concrete for a shed base" is a
    # quantity, while "is concrete a base or an acid" is not
    "acid", "acidic", "alkaline", "alkali", "ph", "litmus", "neutralise", "neutralize",
    "chemical", "chemicals", "erosion", "co2", "carbon", "emissions", "cure", "curing",
    # a wall of bricks or blocks is laid with mortar and the bricklaying rows count it: "how much
    # cement for a brick wall" was answered with a shed base, because "cement" says concrete and
    # "wall" names a job. A poured wall is still concrete and stays here.
    "brick", "bricks", "block", "blocks", "bricklaying", "brickwork", "masonry",
)


# Ballast, hardcore and MOT Type 1 are loose material bought by area and depth, and the existing
# volume row answers them ("A cubic metre is roughly 1.5 tonnes of gravel", which is right for
# ballast too). So this row stands down for a bare "how much ballast do i need" and keeps the line
# as soon as the line names a job - a post, a shed base, a slab - or a material that is only ever
# concrete.
_CONCRETE_SURE = ("concrete", "postcrete", "post mix", "postmix", "concrete mix", "ready mix",
                  "readymix", "cement", "mortar")
_CONCRETE_JOB = re.compile(
    r"\b(?:fence|gate|post|posts|hole|holes|shed|sheds|base|bases|slab|slabs|footing|footings|"
    r"foundation|foundations|drive|driveway|driveways|path|paths|patio|patios|wall|walls|garage|"
    r"garages|floor|floors)\b")


def _concrete_is_what_is_asked(understood):
    """False when the line is loose ballast or hardcore with no job named, which is the volume row.

    "how much ballast do i need" and "how much hardcore do i need" are answered by the material
    row that gives a tonne per cubic metre, and they were before this one existed. "how much
    ballast for a shed base" is not: it was the price of a shed, and it needs the volume of a
    base.
    """
    said = " " + " ".join(str((understood or {}).get(key) or "").lower()
                          for key in ("clean", "text")) + " "
    if any(word in said for word in _CONCRETE_SURE):
        return True
    return bool(_CONCRETE_JOB.search(said))


def _concrete_reply(memory, understood):
    text = " " + (understood.get("clean") or "") + " "
    mixing = ("Concrete is one part cement to six of ballast by volume - six shovels of ballast to "
              "one of cement, mixed dry first, then water until it holds together - and a cubic "
              "metre takes about 1.75 tonnes of ballast and six or seven 25kg bags of cement, "
              "which is two bulk bags of ballast.")
    if re.search(r"\b(?:fence|gate|post|posts|hole|holes|postcrete|post mix|postmix)\b", text):
        return ("One 20kg bag of Postcrete sets one post: the hole wants to be about 250 to 300mm "
                "across and 600mm (two foot) deep, with 50 to 75mm of gravel in the bottom for "
                "drainage. Stand the post, check it upright with a level on two sides, pour the "
                "dry mix in and add the water on top of it. A thicker post, a gate post or a hole "
                "much wider than that takes two bags. %s" % mixing)
    area = _asked_area(memory, understood)
    if area:
        volume = area * (_depth_mm(text, 100) / 1000.0)
        ballast = volume * 1.75
        cement = volume * 6.5
        return ("%s square metres at %dmm is %.2f cubic metres of concrete: about %.1f tonnes of "
                "ballast and %d bags of cement, or %.0f 25kg bags of ready-mixed concrete. %s" % (
                    _sizes(area), _depth_mm(text, 100), volume, ballast,
                    int(-(-cement // 1)), int(-(-(volume * 2400 / 25) // 1)), mixing))
    return ("Work it out as a volume: length times width times depth in metres, so a base 100mm "
            "thick takes 0.1 cubic metres for every square metre, and a 6 by 8 foot shed is about "
            "4.5 square metres - 0.45 cubic metres, which is one 850kg bulk bag of ballast and "
            "three 25kg bags of cement. A single fence post is one 20kg bag of postcrete. %s" %
            mixing)


ENTRIES += [
    entry("how-much-concrete", (_CONCRETE_NAMES, _CONCRETE_ASKS + _CONCRETE_JOBS),
          _concrete_reply, ask=_CONCRETE_ASKS + _KIND_ASKS, avoid=_CONCRETE_AVOID,
          guard=_concrete_is_what_is_asked, bias=2),
    entry("how-much-underlay", (("underlay", "underlayment", "underlay roll"), _ASKS_MATERIAL),
          _underlay_reply, ask=_ASKS_MATERIAL, avoid=_BAG_AVOID, bias=1),
    entry("how-much-grout", (("grout", "grouting"), _ASKS_MATERIAL),
          _grout_reply, ask=_ASKS_MATERIAL, avoid=_BAG_AVOID, bias=1),
    entry("how-much-tile-adhesive", (("tile adhesive", "adhesive", "tile cement", "thin set",
                                      "thinset", "tile glue"), _ASKS_MATERIAL),
          _adhesive_reply, ask=_ASKS_MATERIAL, avoid=_BAG_AVOID, bias=1),
    # A floor is bought by the area and a skirting board by the length, whatever the material:
    # "how much carpet do i need" was a search hedge, "how much laminate flooring do i need"
    # another, and "how much skirting do i need" was answered with how to dust it. The rows that
    # answer a material of their own keep their lines - underlay is above, paint and wallpaper are
    # home.py's, and gravel, turf, slabs and grout are the rows above this one.
    entry("how-much-flooring", (_FLOOR_NAMES, _ASKS_MATERIAL),
          _floor_reply, ask=_ASKS_MATERIAL, avoid=_FLOOR_AVOID, bias=1),
]
