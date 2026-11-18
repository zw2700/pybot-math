"""Getting the water out of a bath, a hose, a freezer, a loft tank, a waterbed or a fish tank.

The answers lane owns this domain. All six are one question - how do I get a lot of water out
of a thing - and the thing is what decides how they are emptied, so this file holds the table
and the one row that reads it, the thing out of the line, rather than four rows opening with
the same sentence.

Why a file of its own: the rows for the house live in `home.py` and its tail `home_craft.py`,
and that tail is at 879 KB of the publisher's 1 MiB ceiling, so a new block of rows and its
table goes beside them, the way `bake_faults.py` sits beside `cooking.py`. Nothing else needs
to change: a domain is a file with ENTRIES.
"""
import re

from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("home-and-diy",)


# Water comes out of a bath, a garden hose, a freezer and a loft tank in four different ways, and
# not one of them had an answer of its own. "how do i drain a bath", "how do i drain the bath",
# "how do i drain a garden hose", "how do i drain a hose pipe" and "how do i drain a waterbed"
# were all the kettle-down-the-waste-pipe card; "how do i drain a header tank" was how to head a
# football, because "header" is a key word of the football row; and "how do i empty a bath",
# "how do i empty a hose", "how do i empty a water tank" and "how do i empty a fish tank" were
# the shrug. They are one question - how do I get a lot of water out of a thing - and the thing
# is what decides how, so the row holds the table and reads the thing out of the line, rather
# than four rows that open with the same sentence.
WATER_OUT_OF = (
    # the bath: the plug is the whole answer, and the number is what makes it obvious that a
    # bucket is not the way
    (("bath", "baths", "bathtub", "bath tub"),
     "Pull the plug and let it go: a full bath is 80 to 100 litres and an ordinary waste takes "
     "it in a few minutes. If the plug hole will not clear, bail most of it into a bucket with a "
     "jug first, then syphon the last of it: fill a garden hose with water, keep one end in the "
     "bath and hang the other end lower down - out of the window into a drain, or into a "
     "bucket - and it runs on its own. Never tip a full bath down a floor drain or a shower "
     "tray, which will not take it fast enough."),
    # a caravan or a motorhome holds its water in a tank and a heater, and both have a drain
    (("caravan", "caravans", "motorhome", "motor home", "camper van", "campervan", "camper"),
     "Open the drain plug or valve on the water tank and the taps at the sink first, so air gets "
     "in and the water runs out instead of glugging, then find the drain on the water heater - a "
     "small tap or a plug on its side - and empty that too, because a heater left full splits "
     "when it freezes. Empty the waste water carrier and the toilet cassette, run the pump dry "
     "for a second only, and leave the taps open. A caravan tank is 40 to 100 litres, so put a "
     "bucket under it, not your shoes."),
    # a garden water feature is a pump and a bowl, and the pump must not run dry
    (("water feature", "water fountain", "fountain", "fountains", "waterfall", "water spout",
      "water wall"),
     "Switch the pump off at the plug before you touch the water, then let it drain: most "
     "features have a drain plug or a bung at the lowest point, and without one you syphon it "
     "into a bucket with a hose. Lift the pump out and clean the sponge, tip the bowl rather "
     "than dragging it, and never let the pump run dry - it burns out in a minute once the water "
     "is below its intake."),
    # a boat holds water in the bilge, and the pump is the answer
    (("bilge", "bilges", "boat bilge"),
     "Pump the bilge rather than bailing it: an electric bilge pump on a float switch should do "
     "it on its own, and a hand pump or a bucket and a sponge does the rest when it does not. "
     "Get it dry afterwards and find out where the water came from - a bilge that fills when the "
     "engine is off is a leak, not rain, and that is a lift-out job."),
    # the hose: it is emptied by gravity and stored dry, because a hose left full of water
    # splits when it freezes
    (("hose", "hoses", "hose pipe", "hosepipe", "garden hose", "watering hose"),
     "Take the nozzle off and walk the hose out straight downhill, lifting it hand over hand so "
     "the water runs to the low end - a minute's job and it does not kink. Coil it loosely and "
     "hang it with both ends down so what is left drips out, and bring it into the shed or "
     "indoors before the first frost: a hose left holding water splits when it freezes, and one "
     "put away wet grows slime inside."),
    # the freezer: the water is what the defrost leaves behind, and the bung is the part people
    # do not know is there
    (("freezer", "freezers", "chest freezer", "fridge freezer", "ice box"),
     "Switch it off at the wall, put the food in a cool box or wrap it in towels, and let the ice "
     "melt rather than chipping at it - a knife through the lining lets the gas out and writes "
     "the freezer off. Bowls of hot water on the shelves speed it up, and a folded towel or a "
     "washing-up bowl at the bottom catches the water. A chest freezer has a small drain bung or "
     "cap at the front: pull it out, stand a shallow tray under it and the meltwater runs out "
     "there instead of over the floor."),
    # a waterbed is a lot of water in a bag, and it is emptied with a pump rather than a jug
    (("waterbed", "water bed", "water beds"),
     "Borrow or hire a waterbed pump - the same one fills and empties it - because a double holds "
     "200 to 400 litres and a jug will not do it. Without a pump, syphon it with a garden hose to "
     "a drain or out of a low window, and empty it fully before you move the frame: a hundred "
     "litres left in the mattress is more than a floor will carry up the stairs. The water is "
     "fine on the garden, but not on grass you want to keep."),
    # a fish tank is emptied with the fish in mind, not the floor
    (("fish tank", "fish tanks", "aquarium", "fish bowl"),
     "Syphon the water out into buckets with a length of airline or a gravel cleaner, and keep "
     "about half of it: new water all at once shocks the fish and loses the bacteria the filter "
     "needs. Keep the filter sponges wet in the old water while you work, leave the fish in a "
     "bucket of tank water with the lid off the light, and put the tank back on the same stand "
     "it came off - a full one is far too heavy for a table or a shelf."),
    # the loft tank: the supply has to be stopped first, or it refills as it empties
    (("water tank", "header tank", "cold water tank", "loft tank", "cold tank"),
     "Stop the water going in before you empty it, or it refills as fast as it drains: tie the "
     "float valve up with a bit of string, or turn the stopcock off. Then either open the drain "
     "cock at the bottom of the tank - a small tap on the side, with a hose on its spout to a "
     "drain or a bucket - or drop a garden hose in, fill the hose with water, and hang the other "
     "end lower than the tank, because a loft tank is above the house and gravity does the rest. "
     "A domestic cold water tank holds 100 to 250 litres, so have a drain or a big container "
     "ready; a mop and towels are not a plan."),
)


# The words that make the row about getting water out of something, said either way round.
WATER_OUT_ASK = (
    "drain", "drains", "draining", "drained", "empty", "emptying", "emptied", "pump out",
    "pump it out", "siphon", "syphon", "syphoning", "get the water out", "water out",
    "tip out", "tip it out", "pour away", "melt water", "melted water", "defrosted water",
    "store", "storing", "put away", "winter", "winterise", "winterize",
)


def _water_out_of_a_thing(memory, reading):
    """The way out of the thing the line names, or the general way when it names none.

    The table is in the order the things are told apart: a caravan has a water tank in it, so
    the caravan comes before the tank, and "how do i empty a caravan water tank" gets the
    caravan's drain plug and taps rather than the loft tank's float valve.
    """
    line = (reading.get("clean") or reading.get("text") or "").lower()
    if not line:
        line = " ".join(str(one) for one in (reading.get("words") or ())).lower()
    for words, reply in WATER_OUT_OF:
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", line):
                return reply
    return ("A bucket and gravity: bail most of it into a bucket, then syphon the rest with a "
            "garden hose kept full of water, with the outlet end lower than the water. Never tip "
            "a lot of water down a floor drain or a shower tray, which will not take it fast "
            "enough to keep up.")


ENTRIES = [
    entry("water-out-of-a-thing",
          (("bath", "baths", "bathtub", "bath tub",
            "hose", "hoses", "hose pipe", "hosepipe", "garden hose", "watering hose",
            "freezer", "freezers", "chest freezer", "fridge freezer", "ice box",
            "water tank", "header tank", "cold water tank", "loft tank", "cold tank",
            "fish tank", "fish tanks", "aquarium", "fish bowl",
                "caravan", "caravans", "motorhome", "motor home", "camper van", "campervan",
                "camper", "bilge", "bilges",
                "water feature", "water fountain", "fountain", "fountains", "waterfall",
                "water spout", "water wall",
            "waterbed", "water bed", "water beds"),
           WATER_OUT_ASK),
          _water_out_of_a_thing,
          # The row that names the thing is the sharper answer than the weekly-maintenance
          # card, which reaches "how do i drain a bath" on its own two words. One nudge is
          # all it needs, and only for a line that names one of the things above, since the
          # avoid list stands the row down for every fault.
          bias=1,
          # the fault sense of the same words keeps its own cards: a bath that will not
          # drain is the trap (the row above), a freezer that needs defrosting is the
          # defrost card, a tank being bought or fitted is the tank's own answer, and a
          # hose pipe ban is a garden question. A food being drained is the colander's.
          avoid=("wont drain", "won't drain", "not draining", "isnt draining",
                 "isn't draining", "doesnt drain", "doesn't drain", "slowly", "slow",
                 "ages", "takes ages", "takes forever", "a long time", "bit by bit", "gurgles",
                 "blocked", "blockage", "backed up", "unblock", "clogged", "clog",
                 "smells", "smelly", "stinks", "hair", "plunger", "plughole", "plug hole",
                 "defrost", "defrosting", "defrosted", "frost", "ices up", "ice build",
                 "ice built", "how often", "buy", "buying", "fit a", "fitting", "new",
                 "replace", "repair", "broken", "cost", "worth it", "hose pipe ban",
                 "height", "size", "how big", "how deep",
                 # the garden and the machine containers have their own rows
                 "paddling pool", "swimming pool", "hot tub", "jacuzzi", "water butt",
                 "rain barrel", "pond", "ponds", "radiator", "radiators", "boiler",
                 "central heating", "expansion tank", "septic tank", "oil tank",
                 "dishwasher", "washing machine", "washer", "dryer", "toilet", "cistern",
                 "van", "car",
                 # "pasta", "rice" and the rest are the pan of food, not the plughole
                 "pasta", "spaghetti", "noodles", "rice", "potato", "potatoes", "veg",
                 "vegetables", "broccoli", "carrots", "chickpeas", "beans", "tuna",
                 "sweetcorn", "colander", "cooking", "boil", "boiling", "kettle",
                 "sauce", "tin of", "can of",
                 # and the other senses of the words: tights are "hose", a header is a
                 # football, a bath is a city in Somerset, and a tank is a car's
                 "tights", "stockings", "nylons", "pantyhose", "football", "soccer",
                 "bath city", "roman baths", "spa town", "fuel tank", "petrol", "diesel",
                 "tank top", "think tank", "tank of",
                 # a hot water tank is not a cold one: the cold tank is fed from the mains through
                 # a float valve and sits in the loft, and the hot one is a cylinder with an
                 # immersion element. The words "water tank" are in both, so the hot ones stand
                 # the row down and keep the hot tank card, which is the answer they want.
                 "hot water", "hot water tank", "hot water cylinder", "hot tank", "hot cylinder",
                 "immersion", "immersion heater", "cylinder", "lagging")),
]
