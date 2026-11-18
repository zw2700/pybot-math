"""Everyday house questions that a row that nearly fitted answered instead.

Each one had an answer on the day it was written, and each was the wrong one:

  how do i get a coffee stain out of a mug   "Measure it by the mug: two level tablespoons of
                                              ground coffee per 200ml" - brewing, not cleaning
  tea stains in my mug                       "Blot up as much as you can with kitchen paper" -
                                              there is nothing to blot inside a mug
  my mug is stained inside                   "Got it - your mug is stained inside."
  how do i clean a greasy cooker hood        the noise answer, because the row keyed the noise
                                              and filter words and not the grease
  how do i stop my watch strap smelling      "A jeweller fits a new strap while you wait" -
                                              replacing a strap that wants washing
  my football kit is covered in mud          "Start with very little: trainers or astro boots,
                                              shorts or leggings" - the kit list
  how many tiles do i need for a floor       "Got it. Is there anything you'd like a hand
                                              with?" - a sum is not a job to explain

The rows live here rather than in cleaning.py, clothing.py and home.py because those tables are
where the competing rows are: a new row beside them is where the question is decided, and it
costs one import in answers.py and nothing on a line it does not know.

The thread through the cleaning rows is that the thing is not ruined, it is dirty, and the
stuff to clean it with is already in the kitchen. The answer says what the dirt is in the first
sentence, because that is what tells a person the fix will work.

The tiles row is here for the other half of the same reason: what a person wants is a number,
and the rows that nearly fitted answer with a method, a price or a shrug. It gives the sum and
the two per cent figures that make it right, because a tile count is the one thing in this file
a person cannot work out from the answer to a different question.
"""

import re

from .lookup import entry

ANSWERS = ("home-and-diy", "shopping", "cooking")

# A mug is not a spill: there is a stain, but the thing is the inside of a mug, and blotting
# kitchen paper on it is advice for a sofa. Two words have to be covered, and the mug words are
# one of them, so "how do i clean a cup" alone still reaches whatever answered it before.
MUG_WORDS = ("mug", "mugs", "cup", "cups", "teacup", "teacups", "flask", "thermos", "teapot",
             "coffee cup", "tea cup")

# The grease in a hood is the reason it is noisy as well as the reason it is filthy: one row,
# two openings, and the line picks. Read from the understanding, not from the raw text.
HOOD_NOISE_WORDS = frozenset((
    "noisy", "noise", "noises", "loud", "louder", "loudest", "rattle", "rattles", "rattling",
    "vibrate", "vibrates", "vibrating", "vibration", "buzz", "buzzes", "buzzing", "hum", "hums",
    "humming", "grind", "grinds", "grinding", "suck", "sucks", "sucking", "weak", "smell",
    "smells", "smelly"))

HOOD_GREASE_TEXT = (
    "The grease goes in the filter: the metal ones lift out, go in the dishwasher or a hot soapy "
    "sink with soda crystals for half an hour once a month, and that is what stops the hood "
    "getting weak and smelly. The outside wipes down with hot water and washing-up liquid, top to "
    "bottom so the grease does not run onto what you have already cleaned, and a paper charcoal "
    "filter cannot be washed - it is a new one every three to six months.")

HOOD_NOISE_TEXT = (
    "Clean the grease filters first: the metal ones go in the dishwasher, or in a hot soapy sink "
    "once a month, and a clogged filter is what makes a hood both noisy and weak. A rattle is "
    "usually a filter that is not seated or the flap on the outside wall vent banging; noise on "
    "the boost setting is normal, and a grind means the motor is on its way out.")


def _hood_reply(memory, understood):
    """The grease answer for a grease question, the noise answer for a noise one."""
    words = set((understood or {}).get("words") or ())
    if words & HOOD_NOISE_WORDS:
        return HOOD_NOISE_TEXT
    return HOOD_GREASE_TEXT


# A strap that smells wants washing, and rubber holds the smell worse than leather - telling
# someone to buy a new strap answers a question they did not ask.
# The key's "wash" and "washing" also read a watch that has *been* washed as a strap that smells:
# "i washed my apple watch" was told it is sweat under the strap (@ivory-magnet, #9232 family).
# The strap is the word that keeps this row; without it, a line about water stands the row down
# and the device's own water card answers.
_STRAP = re.compile(r"\b(?:strap|straps|band|bands|wristband|collar)\b", re.I)
_SOAKING = re.compile(
    r"\b(?:wash\w*|wet|water|sink|bath|toilet|rice|sea|pool|submerged|sank|dropped|"
    r"washer|washing machine|swam|swim)\b", re.I)


def _a_strap_not_the_device(understood):
    """True for the strap itself; False for a watch that got washed or wet."""
    text = str((understood or {}).get("clean") or "").lower()
    return bool(_STRAP.search(text)) or not _SOAKING.search(text)


# A machine that bangs is the machine's own business, and the laundry rows answer it. The words
# for the plumbing have to be in the line as well for the bang to be the pipes.
_THE_MACHINE = ("washing machine", "washer", "dishwasher", "tumble dryer")
_THE_PLUMBING = ("pipe", "pipes", "tap", "taps", "shower", "toilet", "cistern", "stop tap",
                 "valve", "valves", "water hammer", "mains", "plumbing", "radiator", "boiler")


def _the_machine_its_own_bang(memory_or_understood, understood=None):
    read = understood if understood is not None else memory_or_understood
    words = " " + " ".join((read or {}).get("words") or ()) + " "
    if not any(f" {machine} " in words for machine in _THE_MACHINE):
        return False
    return not any(f" {part} " in words for part in _THE_PLUMBING)


ENTRIES = [
# "do i need a loft ladder" was the live-leak card - catch the drip, cut the light circuit, get a
# roofer out today - because the roof-leak row keys the loft and the ladder, for the "is it safe to
# get up there" question. Buying one is a different question, so it has its own row and the leak
# row keeps its lines.
entry("loft-ladder",
      (("loft ladder", "loft ladders", "attic ladder", "loft hatch", "attic hatch",
        "loft access", "loft opening", "ladder", "ladders", "step ladder", "stepladder"),
       ("loft", "attic", "hatch", "need", "buy", "buying", "worth", "worth it", "get one",
        "fitted", "fitting", "fit", "install", "installing", "best", "which", "safe", "safest",
        "how do i", "should i", "do i need", "what sort", "what kind")),
      ("If you go up more than a few times a year, get one: a folding aluminium loft ladder bolted "
       "to the hatch frame is far safer than carrying a step ladder up, and it stows in the "
       "opening. Measure the floor-to-ceiling height and the clear size of the hatch first and "
       "match the ladder's stated height to it, because a ladder that is too short leaves the "
       "last step below the floor. Fit it to a timber surround rather than plasterboard, and only "
       "board the loft along the joists - a ceiling is built to hold a ceiling, not a person."),
      bias=2,
      # rain coming in, and getting up on the roof to look at it, are the roof-leak row's
      # question, and a ladder up a wall or into a pool is another job
      avoid=("board", "boards", "flooring", "insulation", "conversion",
             "leak", "leaks", "leaking", "water", "rain", "raining", "storm", "tarp",
             "tarpaulin", "roof", "roofs", "gutter", "gutters", "downpipe", "chimney",
             "solar", "window", "windows", "paint", "painting", "decorating", "wallpaper",
             "wall", "walls", "hedge", "hedges", "pool", "swimming", "bunk", "bunk bed",
             "car", "van", "boat", "loft conversion",
             # and a ladder in a stocking is not a ladder up a wall: "how do i stop ladders in
             # tights" was given the folding aluminium one bolted to the hatch frame
             "tights", "stockings", "snag", "snagged", "snags")),
# The day after the ladder goes in, the question is the floor: "how do i board my loft" was a
# shrug on main. It is the same job as the ladder - the joists are the only thing that carries a
# person - so the two rows sit together and stand down for each other.
entry("loft-boarding",
      (("board", "boards", "boarded", "boarding", "flooring", "chipboard", "loft legs"),
       # "floor" and "flooring" are left out on purpose: "how do i board a floor" is a
       # floorboard job in a room, and it was answered with the loft, so the loft has to be
       # named for this row to take the line
       ("loft", "attic", "joists", "store", "storage")),
      ("Board across the joists, never beside them: 18mm chipboard or loft boards screwed down "
       "into the timber, with the joins over a joist. Keep the 50mm gap at the eaves and do not "
       "squash the insulation under the boards, because it needs the air to work - if the wool is "
       "deeper than the joists, screw loft legs on top and board onto those instead. The ceiling "
       "below carries a ceiling and not a floor, so a water tank or a stack of boxes wants a "
       "joist under it."),
      bias=2,
      avoid=("ladder", "ladders", "hatch", "leak", "leaks", "leaking", "water", "rain",
             "tarp", "roof", "gutter", "gutters", "chimney", "solar", "window", "paint",
             "wallpaper", "wall", "walls", "ironing", "cheese", "gravy", "shelf", "shelves",
             "cupboard", "wardrobe", "car", "van", "boat", "conversion", "insulation")),
# Tannin on glaze is not a spill on fabric: nothing to blot, nothing to lift with water, and an
# abrasive pad is what gives the next stain somewhere to grip.
entry("mug-stain",
      (MUG_WORDS,
       # The drink's own name is not a word for the mark. With "tea" and "coffee" here every
       # line that named the drink and a mug fired this row - "how do i make a flask of tea" was
       # told how to lift a tannin ring - and the shapes that were fenced off one at a time
       # ("make a cup", "make a brew", "pot of tea") never finished the job. What is asked about
       # here is the mark, so the mark has to be named: stain, ring, tannin, brown, cloudy, dirt.
       ("stain", "stains", "stained", "brown", "ring", "rings", "ringed", "tannin", "tannins",
        "clean", "cleaning", "remove", "get out", "inside", "scrub",
        "build up", "build-up", "cloudy", "dirty")),
      "A brown ring inside a mug, a flask or a teapot is tannin stuck to the glaze, and bicarbonate of soda lifts it: "
      "a teaspoon of it with a little water into a paste, rub it round with a cloth, or leave "
      "the mug filled with hot water and a spoon of bicarbonate for half an hour. A dishwasher "
      "tablet in hot water does the same job overnight, and vinegar is a poor third because it "
      "barely touches tannin. Do not scour the inside with an abrasive pad, which scratches the "
      "glaze and gives the next stain somewhere to grip.",
      bias=2,
      # a stain on a fabric or a surface is not this: those are the blotting rows, and they are
      # right about what they answer
      avoid=("shirt", "shirts", "top", "blouse", "trousers", "jeans", "dress", "clothes",
             "carpet", "rug", "sofa", "mattress", "upholstery", "tablecloth", "table", "floor",
             "wall", "walls", "worktop", "sink", "bath", "toilet", "shower", "curtain",
             # brewing it, buying one and how big it is are other questions
             "how much coffee", "how many spoons", "tablespoon", "ground coffee", "instant",
             "brewing", "brew", "how long to brew", "buy", "best mug",
             # "cup" and "tea" are both keys here, so making one and drinking it landed on
             # this row: "how do i make a cup of tea" was told how to lift a tannin ring, and
             # so were "is 4 cups of tea too much" and "how many cups of coffee should i drink
             # a day". Brewing it and how much of it is safe are the tea and caffeine rows, so
             # those shapes stand this one down. A stain said with a cup of tea in it is not a
             # real line: the stain rows all name a mark, a ring or the mug.
             "make a cup", "make tea", "make coffee", "make a brew", "making tea",
             "making coffee", "cup of tea", "cup of coffee", "cups of tea", "cups of coffee",
             "how much tea", "how many cups", "caffeine", "too much tea", "too much coffee",
             "is too much", "drink a day", "safe limit",
             # the brewing shapes the kettle row answers: a pot, a proper cup, iced and green
             # tea, and the mug in the line that is being made rather than stained
             "make a mug", "make a pot", "make some tea", "make the tea", "make iced",
             "make green tea", "proper cup", "decent cup", "mug of tea", "pot of tea",
             # how much water makes that many cups is the kettle's question: "how much water
             # should i boil for four cups of tea" names cups and tea, which is this row's
             # shape, and it was told to lift a brown ring with bicarbonate. Main has since
             # grown this list for the same lines, so the extra words are merged in here.
             "how much water", "how many mugs", "mugs of tea", "boil", "boiling", "kettle",
             # bare "teapot" was here, so "how do i clean a stained teapot", "how do i clean a
             # teapot" and "how do i stop my teapot staining" all had no answer at all while the
             # mug, the flask and the tea cup had this one. A pot is a mug with a spout; what
             # stands down is brewing in it and seasoning a new one.
             "new teapot", "season a teapot", "season my teapot", "season the teapot",
             "before using", "before first use", "first use", "before i use", "brew the")),

# A hood is asked about because it is noisy or because it is filthy, and the grease is the cause
# of both: the same facts, but the first sentence has to answer what was asked.
entry("hood-grease",
      # a bare "filters" in the first half made every filter in the house this row's: "my washing
      # machine filter is blocked", the dishwasher's and a vacuum's were all told to lift out a
      # metal grease filter. The hood has to be named or the grease has to be, and the machines
      # that have their own filters stand this row down below.
      (("cooker hood", "cooker hoods", "extractor hood", "extractor fan", "extraction hood",
        "kitchen hood", "range hood", "extractor", "hood", "grease filter"),
       ("clean", "cleaning", "grease", "greasy", "degrease", "scrub", "soak", "sticky", "dirty",
        "filthy", "grimy", "grotty", "filter", "filters", "wash", "wipe", "smell", "smells",
        "smelly", "noisy", "noise", "loud", "rattle", "rattling", "vibrating", "buzzing",
        "humming", "grinding", "sucking", "weak")),
      _hood_reply,
      bias=2,
      # a bathroom fan, an oven fan, a car and a tumble dryer are other fans
      avoid=("bathroom", "loo", "toilet", "shower", "bath", "fan oven", "car", "cars", "engine",
             # the hood's key holds "filters", and every machine with a filter was read as a
             # hood: "how do i clean a washing machine filter" was told how to soak a grease
             # filter from the extractor. The laundry appliances have their own rows.
             "washing machine", "washing", "washer", "washer dryer", "dishwasher", "laundry",
             "bonnet", "truck", "van", "bike", "loft", "tumble dryer", "dryer", "heating",
             "radiator", "boiler", "ceiling fan", "desk fan", "buying", "best hood", "which hood",
             "install", "installing", "fit a new",
             # every machine with a filter of its own: the water filter, the pump filter, the
             # dishwasher's, the vacuum's and an air purifier are not greasy metal, and
             # "filter" is in both keys with a bias behind this row
             "washing machine", "washer", "washer dryer", "dishwasher",
             "dish washer", "fridge", "freezer", "vacuum", "hoover", "dyson",
             "air purifier", "purifier", "coffee machine", "water filter",
             "pump filter", "jug filter", "fish tank", "pool", "pool filter",
             "kettle", "fan heater", "tumble dryer", "dryer")),

entry("watch-strap-smell",
      (("watch", "watches", "smartwatch", "fitbit", "garmin", "watch strap", "watch band",
        "strap", "straps", "band", "bands", "wristband"),
       ("smell", "smells", "smelly", "stink", "stinks", "stinking", "sweat", "sweaty", "sour",
        "washing", "wash", "cleaning", "clean", "disinfect", "rash", "under it", "itchy")),
      "It is sweat and skin cells trapped under the strap, and rubber and silicone ones hold it "
      "worse than leather: take the watch off to sleep and wash the strap with warm water and a "
      "little washing-up liquid or soap, then dry it properly before it goes back on, because "
      "damp is what keeps the smell. A paste of bicarbonate of soda left on for ten minutes "
      "takes out the rest, and a fabric strap goes in a mesh bag on a cool wash. Leather will "
      "not take a soaking: wipe it with a cloth wrung out in diluted vinegar and dry it away "
      "from heat.",
      bias=2,
      guard=_a_strap_not_the_device,
      # a strap for a bag, a guitar or a bra is not this, and neither is a replacement or a film
      avoid=("bag", "bags", "handbag", "rucksack", "backpack", "guitar", "camera", "bra",
             "bra strap", "shoulder", "dog collar", "collar", "leash", "replacement", "replace",
             "new strap", "buy", "price", "how much", "sizing", "size", "too tight", "too loose",
             "film", "films", "movie", "movies", "tv", "series", "show", "shows", "netflix",
             "episode", "episodes", "match", "football", "game", "channel", "documentary")),

# Mud on a kit is a washing question whatever the garment is called: "kit" used to mean
# equipment only, so a muddy football kit got the what-to-bring list.
entry("mud-on-a-kit",
      # "grass stains" is not here on its own: grass on a pair of jeans is a stain question with
      # no mud in it, and that is a different row's line
      (("mud", "muddy", "mud stains", "clay"),
       ("kit", "kits", "football kit", "rugby kit", "games kit", "pe kit", "sports kit",
        "shirt", "shirts", "shorts", "socks", "trousers", "jeans", "clothes", "trainers",
        "boots", "shoes", "top", "jumper", "washing", "wash", "get out", "get off", "remove",
        "clean", "stain", "stains", "stained")),
      "Let the mud dry completely, then brush it off with a stiff brush before you touch water; "
      "washing mud while it is wet just pushes it into the fabric. A little washing-up liquid "
      "and a soft brush lifts the rest, then rinse and dry away from heat. Cold water only on a "
      "kit: hot water sets the mud and the grass stain both, and a wash at 30 with a normal dose "
      "of powder takes out what brushing leaves.",
      bias=2,
      # mud on a floor, a car or a dog is another job, and what to take to a match is a list
      avoid=("carpet", "rug", "floor", "floors", "wall", "walls", "car", "drive", "path",
             "patio", "dog", "puppy", "bike", "pushchair", "wellies", "garden", "lawn",
             "what to bring", "what to take", "what do i need", "should i bring")),
    # --- four jobs whose method main punts on ---------------------------------
    # A job with a known method is not a call-out. fallback.py's "A plumber or electrician
    # will spot it in minutes" is right for a fault nobody has answered; it is wrong for
    # "how do i remove a radiator", which is someone asking how, not who. These four live here
    # rather than in home.py because that table is a megabyte and the file has to stay under it.
    entry("radiator-remove",
          (("radiator", "radiators", "towel rail", "towel radiator", "heated towel rail"),
           ("remove", "removing", "take off", "taking off", "take it off", "come off the wall",
            "off the wall", "swap", "swapping", "replace with", "change a radiator",
            "move a radiator", "moving a radiator", "decorate behind",
            # the wall is where the radiator hangs, so a line that says radiator and wall is
            # this job and not the wall-mark row beside it
            "wall", "walls", "bracket", "brackets")),
          "Turn the heating off and let the water cool, then close both valves: the thermostatic "
          "head to 0 and the lockshield at the other end. With a towel and a bowl under one end, "
          "open the bleed valve at the top with a radiator key and let the water out slowly, then "
          "undo the valve nut and lift the radiator off its brackets - it is heavy and full of "
          "sludge, so two people. Cap or plug both valves before you put the heating back on, and "
          "top a sealed system back up to 1 to 1.5 bar.",
          # a leak, a cold radiator and a noisy one are faults with their own first move.
          # NOT the bare word "leak": the misspelt-avoid reader counts "take" as one edit from it,
          # and "take a radiator off the wall" is this row's own line.
          avoid=("leaks", "leaking", "leaked", "drip", "dripping", "cold", "bleed", "bled",
                 "noise", "noisy", "banging", "gurgling", "paint", "painting", "turn off",
                 # NOT "radiator off": the loose avoid reader takes the words of this very
                 # phrase out of "take a radiator off the wall", which is the row's own line
                 "thermostatic", "trv", "cost", "price", "how much", "install",
                 # a mark on the wall above or behind a radiator is the wall-mark row's line
                 "mark", "marks", "marked", "stain", "stains", "stained", "scuff", "scuffs",
                 "yellow", "yellowed", "brown marks", "dirty", "clean the wall"),
          # "take a radiator off the wall" also reaches the wall-mark row on "wall" and "off",
          # and the mark card is the wrong one for a job that ends in a valve and a bowl of water
          bias=2),
    entry("water-hammer",
          (("water hammer", "hammering", "banging pipes", "pipes bang", "pipes banging",
            "banging in the pipes", "pipes knocking", "knocking pipes", "pipes clunk",
            "clunking", "thudding", "loud bang", "bangs when", "bang when"),
           ("stop", "stops", "stopping", "fix", "cure", "why", "loud", "noise", "tap", "taps",
            "shower", "toilet", "washing machine", "dishwasher", "when i turn", "in the wall",
            "pipes")),
          "That bang is the pressure wave when a valve shuts quickly and nothing absorbs it: clip "
          "any loose pipe run so it cannot jump, replace a worn tap washer or a tired ball valve "
          "in the toilet, and fit a mini shock arrestor close to the appliance that bangs. If the "
          "whole house does it, ask the water company to check the pressure, or have a pressure "
          "reducing valve fitted after the stop tap.",
          # a radiator that bangs when the heating comes on is air, which the radiator rows answer
          # - and a knee that clunks is a joint, not a pipe: "my knee makes a clunking noise" was
          # answered with the water hammer card
          # "the washing machine bangs when it spins" is the machine, not the plumbing: the drum
          # out of balance, a tangle, the transport bolts left in. A machine only belongs to this
          # row when the line also names the pipe, tap, shower or toilet that bangs with it.
          guard=lambda understood: not _the_machine_its_own_bang(understood),
          avoid=("radiator", "radiators", "boiler", "heating", "trv", "thermostatic",
                 "knee", "knees", "kneecap", "hip", "hips", "shoulder", "shoulders", "elbow",
                 "wrist", "ankle", "finger", "fingers", "thumb", "jaw", "joint", "joints",
                 "my back", "my neck", "knuckle", "knuckles")),
    # "bled" and "bledding" are what people type for bleed: a one-letter verb that is also a
    # real word ("bled", "cold") never comes back from the typo reader, so it is listed here.
    # A heated towel rail is a radiator with a bleed valve at the top, and people call it a rail
    # rather than a radiator, so "how do i bleed a towel rail" reached nothing at all.
    # The heating and the hot water "keep going cold" is a shape the fault rows did not read: on
    # main "the heating keeps going cold" got "Got it - is there anything you'd like a hand
    # with?" and "my hot water keeps going cold" was packed for a picnic. The words that matter
    # are the thing that went cold and the verb shape, so this row keys on both and the radiator
    # keeps its bleed and sludge answers.
    entry("downpipe-blocked",
          # The pipe that carries the roof, not the gutter itself: "my gutter is overflowing"
          # and "how do i stop my gutter leaking at the joint" already had two good answers
          # (clearing the run, and sealing the joint), and this row took both off them.
          (("downpipe", "down pipe", "drainpipe", "drain pipe", "rainwater pipe", "hopper head",
            "outside drain", "yard drain"),
           ("blocked", "blockage", "unblock", "clear", "clearing", "overflowing", "overflows",
            "water down the wall", "running down the wall", "water coming down", "leaking",
            "spilling", "not draining", "wont drain", "won't drain", "pooling", "puddle",
            "smells", "stinks", "how do i", "full of leaves", "leaves")),
          "Work from the bottom: lift the drain cover or clear the shoe at the foot of the pipe "
          "first, then push a drain rod (or a stiff hose) up from there, because that is where the "
          "leaves and grit collect. If the pipe still backs up, go up a ladder and clear the outlet "
          "at the gutter end, then flush it with a hose from the top. Rod gently, never with a "
          "pressure washer down a plastic pipe, and if the water is coming out of a joint rather "
          "than the top, the joint has failed rather than the pipe being blocked.",
          # water inside the house, a wet patch on a ceiling and the shower are other rows
          avoid=("shower", "bath", "sink", "basin", "toilet", "kitchen", "washing machine",
                 "dishwasher", "ceiling", "boiler", "radiator", "gutter cleaning", "clean the "
                 "gutters", "clear the gutters", "how often", "cost", "price", "install"),
          bias=1),
    # "how do i find a stud in a wall" was answered by the *studying* card - "Testing yourself is
    # what makes things stick" - and "where are the studs in my wall" and a ceiling joist were the
    # search hedge. The word names two things and the wall wins on the "how do i find" shape, so
    # this row takes the timber and leaves the revision rows every word they had.
    entry("find-a-stud",
          (("stud", "studs", "stud wall", "studwork", "joist", "joists", "timber frame",
            "wooden frame", "wall stud"),
           ("find", "finding", "locate", "locating", "where", "where are", "behind the plasterboard",
            "in the wall", "in a wall", "in my wall", "in the ceiling", "without a stud finder",
            "stud finder", "stud detector", "knock", "tap", "how do i find")),
          "Find the plasterboard screws instead of hunting for timber: a small magnet run slowly "
          "across the wall sticks at each screw, and the screws are driven into the studs, so a "
          "line of them is the frame and studs are usually 400 or 600mm apart. A stud finder does "
          "the same job for a few pounds, and knocking along the wall for the dull solid note works "
          "if the wall is bare. Before you drill anywhere, check for cables and pipes - most run "
          "vertically above sockets, so keep to the screw line you found and stay wide of them.",
          # revision, a student and a school are the study rows' and the person rows' lines
          # NOT "study": an `avoid` word also stands down a line word that is a prefix of it, so
          # "study" would cancel this row's own key word "stud" and hand the line back to the
          # revision card. The study rows are fenced off by the words their lines are made of.
          avoid=("revision", "revise", "revising",
                 "exam", "exams", "notes", "school", "university", "uni", "college", "course",
                 "degree", "student", "students", "learn", "learning", "memorise", "memorize",
                 "test", "tests", "teacher", "homework", "results", "grades", "gpa",
                 # the study rows keep every line about study itself: "how do i find time to
                 # study with a job" is not a wall, and its words are these phrases
                 "to study", "study for", "study with", "study tips", "study plan",
                 "study better", "study at home", "study full time", "study part time",
                 "studying for", "study hard", "study group", "study skills", "study guide",
                 "how do i study", "how to study", "time to study", "when to study",
                 "where to study", "cant study", "can't study", "keep studying",
                 # an earring, a boot and a horse are other words again, and a breeding one
                 "earring", "earrings", "nose stud", "boot", "boots", "belt", "horse", "bull",
                 "cattle", "dog breeding")),
    # A cycle that takes hours is the most common thing people ask about a washer after a fault,
    # and it was the honest hedge. The length of a cycle is a fact, not a fault, and the reason it
    # runs long is the same on every machine.

    # --- lighting a boiler is a job, not a call-out -------------------------
    # "how do i light my boiler" got the plumber shrug while the same boiler's pilot fault already
    # had an answer, and "how do i relight the pilot light on my boiler" got the fault half of it.
    # The pilot row lives in home.py, which is at the publisher's file limit, so this is its own
    # row here: keyed on the act of lighting and fenced off the fault words the pilot row owns.
    entry("boiler-relight",
          (("boiler", "boilers", "gas boiler", "combi", "back boiler", "pilot light", "pilot",
            "pilot flame"),
           ("light", "lights", "lighting", "lit", "relight", "relighting", "re-light",
            "how to light", "how do i light", "how do i relight", "light it", "light the",
            "after the summer", "first time", "ignition", "ignite", "fire it up")),
          "Find the relight sequence in the boiler's manual first: most modern boilers relight from "
          "a reset button, and an older one with a permanent pilot wants the gas knob held in for "
          "about twenty seconds once the flame catches. If it will not stay lit, stop there and "
          "call a Gas Safe engineer - it is usually the thermocouple, a part that takes ten "
          "minutes. Never keep pressing reset, and if you smell gas turn it off at the meter, open "
          "the windows and ring 0800 111 999.",
          # a pilot that keeps going out is the fault the pilot row answers; a boiler losing
          # pressure, kettling or being old is another question again, and a hob or a gas fire is
          # not a boiler
          avoid=("keeps going out", "keep going out", "goes out", "gone out", "went out",
                 "blows out", "wont stay", "won't stay", "not staying", "pressure",
                 "losing pressure", "leak", "leaking", "noise", "noisy", "kettling", "efficiency",
                 "replace", "new boiler", "service", "serviced", "insurance", "cover",
                 "thermostat", "radiator", "hot water", "frozen", "condensate", "reset it",
                 "hob", "oven", "gas fire", "camping", "barbecue", "bbq", "pilot episode", "tv")),

# Tiles are bought by the box and asked for by the room, and this domain had no sum at all:
# "how many tiles do i need for a floor" was the honest punt, "how many tiles for a bathroom
# wall" the cleaning card, "how do i work out how many tiles i need" the tiling how-to and "how
# many boxes of tiles do i need" the packing row - the next three rows in home.py the whole way
# through. The sum is the same one paint and wallpaper use, and it lives here because home.py is
# past what a submission can carry.
entry("tiles-quantity",
      (("tile", "tiles", "tiling", "wall tiles", "floor tiles", "tiles for"),
       ("how many", "how much", "many tiles", "many boxes", "boxes of tiles", "boxes",
        "packs", "how many packs", "need", "needs", "work out", "calculate", "cover",
        "coverage", "square metres", "square meters", "sqm", "quantity", "enough")),
      "Work out the area first and then add a tenth: a 2m by 3m floor is 6 square metres, and "
      "with 10 per cent for cuts and breakages you want 6.6, so buy 7. A box tells you how many "
      "square metres it covers - usually about 1.2 to 1.5 - so divide by that and round up, and "
      "for a wall measure the height times the width and take off the door and the window. "
      "Order all the boxes at once so they are one batch, keep a spare box for a repair, and "
      "for a diagonal or a herringbone layout add 15 per cent instead of 10.",
      # laying them, cleaning them, drilling through them and choosing them are other answers
      avoid=("lay", "laying", "laid", "grout", "grouting", "adhesive", "seal", "sealing",
             "clean", "cleaning", "drill", "drilling", "remove", "removing", "replace",
             "cracked", "loose", "hollow", "which", "what colour", "what color", "best",
             "cost", "costs", "price", "prices", "cheap", "cheapest", "expensive",
             "how much is", "how much does", "splashback", "splash back", "bathroom design"),
      bias=2),
    # The parts of a house that have a name and no explanation: a person meets them on a survey, a
    # builder's quote or a wiring job, and "what is a lintel" was the search hedge.
    entry("lintel",
          (("lintel", "lintels", "a lintel"),
           ("what", "whats", "what is", "mean", "means", "explain", "do i need", "need one",
            "how much", "cost", "above", "over", "window", "door", "crack", "replace")),
          ("A lintel is the beam over a window or a door opening that carries the wall above it, so "
           "the bricks do not sit on the frame. Older houses often have a timber one over a "
           "doorway and a stone or steel one over a window; a new opening or a wider one needs a "
           "steel beam, designed and signed off by a structural engineer. If there is a stepped "
           "crack running up from the corner of a window, the lintel is the first thing to check, "
           "and it is a builder's job, not a filler job."),
          explain=True, bias=2),
    entry("joist",
          (("joist", "joists", "a joist", "floor joists", "ceiling joists", "joist hanger"),
           ("what", "whats", "what is", "mean", "means", "explain", "how far", "span", "apart",
            "spacing", "cut", "notch", "rotten", "rot", "replace", "size", "how much")),
          ("A joist is one of the beams under a floor or above a ceiling that carries the boards "
           "you walk on, usually timber, set about 400mm apart, with cables and pipes running "
           "through the gaps. You may notch one at the top edge near a support, never in the "
           "middle of the span, and never drill through the bottom edge where it is in tension. "
           "A joist that is soft, stained or sagging is a surveyor's or builder's question, not a "
           "DIY one, because the fix changes the structure."),
          explain=True, bias=2),
    entry("rcd",
          (("rcd", "rcbo", "residual current device", "rcd switch", "earth leakage",
            "fuse box", "consumer unit"),
           # the fault words ("trip", "reset") are not here: a person whose switch keeps
           # tripping is asking what to do, not what an RCD is, and the definition took
           # "my rcd keeps tripping", "my rcd wont reset" and "my rcd trips when it rains" away
           # from the rows on main that answer them.
           ("what", "whats", "what is", "mean", "means", "explain", "do", "does",
            "difference", "difference between", "test", "why")),
          ("An RCD is the switch in the consumer unit that cuts the power when current leaks to "
           "earth - through a damaged cable, a wet socket, or a person - and it works in about 30 "
           "milliseconds, which is fast enough to save a life. It is different from the MCB, which "
           "protects the cable from overload, so a tripping RCD means something is leaking "
           "somewhere rather than using too much. Press the test button twice a year, and if it "
           "keeps tripping, unplug everything on that circuit, reset it, and add things back until "
           "it goes - a tripping RCD that will not reset is an electrician's visit."),
          explain=True, bias=2,
          # a fuse that has blown, a socket with nothing working and a shock are other answers
          avoid=("blown", "blown fuse", "fuse keeps blowing", "electric shock", "shocked",
                 "no power", "power cut", "socket not working", "light not working",
                 # a fault has a fix of its own already on main, and it is more specific than
                 # the paragraph above: these three lines lost their answers to the definition
                 "keeps tripping", "keeps tripping out", "trips when", "trips whenever",
                 "wont reset", "won't reset", "will not reset", "keeps cutting out",
                 "trips again", "trips every", "tripped and wont", "tripped and won't")),
]
