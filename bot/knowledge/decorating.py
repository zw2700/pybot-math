"""Decorating paint: the things that go wrong while a wall is being painted.

Seven everyday lines about a brush and a roller, and six of them were answered about
something else:

  how do i stop paint dripping                  the acrylics hobby card ("a starter set is under
                                                twenty pounds")
  how do i stop paint running down the wall     most training injuries come from a jump in load
  paint keeps dripping down the wall            the ceiling-leak card ("a brown or yellow patch
                                                on a ceiling is water")
  how do i stop the roller splattering          a search hedge
  how do i stop paint getting on the skirting   the sand-it-and-mask-the-carpet card
  which brush for gloss                         the key-the-old-gloss-first card
  how do i thin gloss paint                     the acrylics hobby card again

The word "paint" is the whole problem: the art-and-hobbies row teaches a beginner what to buy,
the ceiling-leak row owns a patch on a wall, and the fitness row owns a word that is not in the
line at all. A person with a brush in their hand asked how to stop a run, and the bot told them
about acrylics.

So every row here needs two things in the line: paint, or the tool it is being put on with, AND
the thing going wrong. `how do i paint a ceiling`, `how do i paint a door`, `how do i paint a
wall without streaks`, `how do i paint a radiator`, `what paint for a bathroom`, `how long
between coats of paint`, `how do i get paint off my hands`, `how do i get paint off a carpet` and
`how do i clean a paintbrush` are all answered well already, and none of them names a fault, so
they keep their cards.

A leak keeps its own: a patch of water coming through a ceiling or a wall is the damp answer's
question, and "paint" in the line does not make it a decorating one.
"""

import re

from .lookup import a_food_is_being_kept, entry

ANSWERS = ("home-and-diy",)

# Paint, and the tool paint goes on with. A roller is only ever decorating; a brush is also a
# hairbrush and a pastry brush, so a brush row needs the paint word next to it and this table
# does not hold a bare "brush" on its own.
PAINT = ("paint", "paints", "painted", "painting", "repaint", "repainting", "gloss", "glossing",
         "emulsion", "satin", "eggshell", "undercoat", "primer", "priming", "woodwork",
         "woodwork", "decorating", "decorate", "decorated", "roller", "rollers", "brush",
         "brushes", "paintbrush", "paintbrushes", "sleeve", "masking tape", "filler", "sander")

# The paint is not where it should be, or it is not lying flat. These are the faults a person
# names out loud, and they are what makes the line a decorating question rather than a
# what-shall-I-buy one.
GOING_WRONG = ("drip", "drips", "dripping", "dripped", "run", "runs", "running", "ran",
               "sag", "sags", "sagging", "sagged", "curtain", "curtains", "slide", "sliding",
               "slid", "trickle", "trickles", "trickling", "patchy", "uneven", "transfer",
               "showing", "shows", "visible")

# Water coming through a wall, a ceiling or a roof is the damp answer's, and paint in the line
# does not change that. "paint keeps dripping down the wall" is the one that reads both ways; a
# person saying that with a brush in their hand is the case this file is for, and the damp card
# is still there for "water is coming through the ceiling".
A_LEAK = ("leak", "leaks", "leaking", "leaked", "damp", "damp patch", "damp patches", "water",
          "watermark", "water marks", "rain", "raining", "roof", "gutter", "gutters", "pipe",
          "pipes", "burst", "condensation", "mould", "mold", "mouldy", "moldy", "plaster",
          "render", "brick", "bricks", "brickwork", "ceiling tile", "flood", "flooded",
          "overflow", "tank", "radiator leak", "washing machine", "dishwasher")

# A stain already made is a cleaning question, and the stain row scrubs it out of a carpet or a
# wall better than anything here. Only the fault in the making is this file's.
A_STAIN = ("stain", "stains", "stained", "staining", "spilled", "spill", "spillage", "soaked",
           "soak", "scrub", "wipe off", "get it off", "get off", "remove", "removing", "clean off",
           "cleaning off", "off my hands", "off my skin", "out of my clothes", "out of a carpet",
           "off the floor")

# Filling, sanding and skimming are the preparation rows, and a decorating fault is not one.
A_DIFFERENT_JOB = ("hole", "holes", "crack", "cracks", "cracked", "skim", "skimming", "plastering",
                   "plasterer", "fill a wall", "wallpaper", "wallpapering", "stripping",
                   "strip the", "how much paint", "litre", "litres", "how many coats",
                   "which colour", "what colour", "farrow", "dulux", "buy", "bought", "cost",
                   "price", "cheap")


# The paint, or a surface that is only ever decorated, has to be in the line. The second key group
# of these rows holds the bare verbs ("stop", "keep", "goes", "getting"), so a row reached through
# one of those answered lines that are no painting job at all: "the plug socket has stopped working"
# and "my plug sockets stopped working" were both handed the masking-tape-and-cut-in instructions,
# because "socket" is one of the shared surfaces this row lists for "how do i paint around sockets".
# A socket and a light switch are on the list of things to mask, not proof that a brush is out, so
# on their own they no longer reach the row: the dead socket has an answer of its own.
_PAINT_WORD = re.compile(
    r"\b(?:" + "|".join(re.escape(word) for word in sorted(PAINT, key=len, reverse=True)) + r")\b")
_DECORATED_SURFACE = re.compile(
    r"\b(?:skirting|skirtings|skirting\ board|skirting\ boards|woodwork|door\ ?frame|door\ ?frames|"
    r"architrave|architraves|picture\ rail|banister|banisters)\b")


def _paint_is_the_subject(understood):
    """True when the line is about paint going on a surface, not paint being kept or bought.

    "how do i keep paint from drying out" and "where do i store paint" are keeping questions, and
    a food in the same line ("how do i stop paint getting on the new rug while the cake cools")
    is another card's. A line that names neither the paint nor a surface that is only ever painted
    is not this row's either, however many of its verbs the key holds.
    """
    if not isinstance(understood, dict):
        return False
    if a_food_is_being_kept(understood):
        return False
    said = " ".join(str(one) for one in (understood.get("words") or ())).lower()
    if not said:
        said = str(understood.get("clean") or understood.get("text") or "").lower()
    return bool(_PAINT_WORD.search(said) or _DECORATED_SURFACE.search(said))


# "varnish or sand first" and "do i sand first or fill first" were answered "The step that would
# spoil the other one goes last, so nothing gets done twice. What are you doing it on?", and "the
# shelf or the brackets first" with "Work it out rather than guess". A sequence between two named
# steps is not a preference and it is not the person's to pick: the preparation comes before the
# finish, and what holds a shelf up comes before the shelf. The two answers below are the same
# every time, so they are rows.
#
# Neither row answers a single-step line: "how do i fill a hole in a wall" and "how do i varnish a
# table" keep their own cards, and both of those were already right. The line has to name the two
# steps and ask the order.
_STEPS = {"fill": "fill", "filling": "fill", "filled": "fill", "filler": "fill",
          "patch": "fill", "patching": "fill",
          "sand": "sand", "sanding": "sand", "sanded": "sand", "sandpaper": "sand",
          "smooth": "sand", "smoothing": "sand",
          "prime": "finish", "priming": "finish", "primer": "finish", "undercoat": "finish",
          "varnish": "finish", "varnishing": "finish", "varnished": "finish",
          "oil": "finish", "oiling": "finish", "wax": "finish", "waxing": "finish",
          "stain": "finish", "painting": "finish", "paint": "finish", "gloss": "finish",
          "lacquer": "finish", "coat": "finish", "coats": "finish"}
_ORDER_WORDS = ("first", "before", "after", "or", "between", "then")
# A floor, a wall or a car is sanded too, and each has its own card: the order row is about a
# piece of woodwork being finished.
_NOT_WOODWORK = ("floor", "floors", "floorboard", "floorboards", "decking", "driveway", "path",
                 "pavement", "wall", "walls", "ceiling", "ceiling", "plaster", "plasterboard",
                 "brick", "bricks", "concrete", "paving", "grout", "car", "cars", "rust",
                 "windscreen", "fence", "gate")


# A line that asks which paper or how many coats is a question about the material, not the order:
# "what grit sandpaper for gloss" was this answer before these words were fenced.
_ASKS_THE_MATERIAL = ("what grit", "which grit", "what sandpaper", "which sandpaper",
                      "what paper", "which paper", "what paint", "which paint", "what varnish",
                      "which varnish", "how many coats", "how long between", "best sandpaper",
                      "best paper", "how much paint", "how much varnish", "what filler",
                      "which filler", "what brush", "which brush")


def _the_order_of_two_steps(understood):
    """True when the line names two steps of finishing woodwork and asks which comes first."""
    # `text`, not `clean`: the understanding engine rebuilds `clean` from the line, and a fence
    # has to stand on the words the person actually sent.
    text = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    if any(word in text for word in _NOT_WOODWORK):
        return False
    if any(word in text for word in _ASKS_THE_MATERIAL):
        return False
    if not any(word in text for word in _ORDER_WORDS):
        return False
    return len({step for word, step in _STEPS.items() if word in text}) >= 2


def _a_shelf_and_its_brackets(understood):
    """True when the line is about fixing a shelf and asks whether the shelf or the brackets first."""
    text = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    if "shelf" not in text and "shelves" not in text:
        return False
    if "bracket" not in text and "brackets" not in text:
        return False
    return any(word in text for word in ("first", "before", "or", "then", "put up", "hang"))


ENTRIES = [
# A run or a sag: too much paint in one place, and the fix is in the loading, not the paint.
entry("paint-runs-and-sags",
      (PAINT, GOING_WRONG),
      "Load less: a third of the bristles wet, half a roller of paint, and lay it off with light "
      "strokes in one direction rather than going back over it. A run is too much paint in one "
      "spot, so scrape the roller back over the tray's ramp every time and don't reload until it "
      "stops giving paint, and keep the brush moving in one direction instead of scrubbing back "
      "and forth. When a run has started, brush it out while it is still wet - lay the brush flat "
      "and drag the run sideways into the dry paint - then leave it alone: going back over paint "
      "as it dries is what leaves the brushmarks. On a ceiling, paint towards yourself and slightly "
      "away from the wall so the last stroke is a pulled one, and thin the paint only if it is "
      "genuinely thick.",
      bias=3,
      # a coat that has already failed - peeling, flaking, bubbling, blistering - is a diagnosis
      # question and the find-the-reason-before-you-repaint card owns it, so a run in the making
      # is not that
      avoid=A_LEAK + A_STAIN + A_DIFFERENT_JOB + ("peel", "peels", "peeling", "peeled", "peely",
                                                  "flake", "flakes", "flaking", "flakey", "flaky",
                                                  "bubble", "bubbles", "bubbling", "bubbled",
                                                  "blister", "blisters", "blistering",
                                                  "hobby", "hobbies", "acrylics", "acrylic",
                                                  "watercolour", "watercolors", "canvas",
                                                  "oil painting", "art", "draw", "drawing",
                                                  "learn to paint", "start painting",
                                                  "beginner", "nail", "nails", "nail varnish",
                                                  "car", "cars", "hair", "cake", "icing",
                                                  "kids", "children", "toddler", "spray paint",
                                                  "spraying", "graffiti",
                                                  # a tin that has been kept and gone hard is a
                                                  # storage question, not a fault on a wall
                                                  "drying out", "dried out", "keep paint",
                                                  "keeping paint", "store paint", "storing paint",
                                                  "leftover paint", "left over paint",
                                                  "old paint", "tip", "tin", "tins"),
      guard=_paint_is_the_subject),

# A roller that spits: overloaded, wrong sleeve, and pushed too fast.
entry("roller-splatter",
      (("roller", "rollers", "rolling", "sleeve", "sleeves", "rolling pin"),
       ("splatter", "splatters", "splattering", "spatter", "spatters", "spattering",
        "flick", "flicks", "flicking", "splash",
        "splashes", "splashed", "splashing", "spitting", "spits", "spitting paint", "flinging",
        "throwing", "flies", "flying", "mess", "messy", "dots", "droplets", "spray", "spraying",
        "splatter paint", "tracks", "lines")),
      "Half a roller of paint, a slow push, and roll the excess off on the tray's ramp before "
      "the sleeve touches the wall: a roller splatters because it is overloaded and moving too "
      "fast, and paint spins off the top of a sleeve that is turning at the ceiling. Then roll "
      "from the dry part into the wet in long strokes with light pressure. The sleeve matters "
      "too - short pile for smooth plaster, medium for a light texture, and a long pile holds so "
      "much paint that it throws it - and a brand new cheap sleeve spits fuzz for the first wall, "
      "so wash it out first or wrap tape round your hand and run it over. Sheet the floor and "
      "tape the edges, and any fleck that lands wipes off with a damp cloth while it is wet.",
      bias=3,
      # a pastry roller, a lint roller and a hair roller are the same word
      avoid=A_LEAK + A_STAIN + ("pastry", "baking", "dough", "lint", "deodorant", "hair",
                                "paint off", "get paint off", "remove paint", "stripper"),
      guard=_paint_is_the_subject),

# Protecting the skirting, and what to do with the splash that has already landed on it.
entry("paint-on-the-skirting",
      (("skirting", "skirtings", "skirting board", "skirting boards", "woodwork", "door frame",
        "doorframe", "door frames", "architrave", "picture rail", "banister", "banisters",
        "radiator pipe", "socket", "sockets", "light switch", "light switches"),
       ("paint", "paints", "painted", "painting", "roller", "rollers", "brush", "brushes",
        "splash", "splashes", "splashed", "drips", "dripping", "mess", "messy", "marks",
        "keep", "stop", "protect", "cover", "covering", "masking", "tape", "taping", "getting",
        "goes", "going", "cut in", "cutting in", "neat", "neatly")),
      "Press a low-tack masking tape along the top edge of the skirting, working it down into "
      "the join with a fingernail, then cut in with a 2 inch angled brush and brush the last inch "
      "slowly towards the tape rather than at it, so the paint is not pushed underneath. Pull the "
      "tape off at a shallow angle while the paint is still soft - leave it until the paint is "
      "hard and it tears the edge off with it. Anything that does get through: a wet cloth takes "
      "emulsion off a gloss skirting straight away, and once it is dry a sharp scraper or a "
      "fingernail lifts it without marking the gloss. Masking tape, not parcel tape, and not "
      "left on for a week, or it takes the gloss with it when it comes off.",
      bias=3,
      avoid=A_LEAK + A_STAIN + A_DIFFERENT_JOB + ("paint off", "get paint off", "getting paint off",
                                                  "clean paint off", "cleaning paint off",
                                                  "remove paint", "removing paint",
                                                  "off the door", "off the frame", "off the floor",
                                                  # the skirting being painted is a how-do-i-paint
                                                  # question, and the sand-and-mask card has it
                                                  "paint the skirting", "paint a skirting",
                                                  "painting the skirting", "painting a skirting",
                                                  "paint my skirting", "painting my skirting",
                                                  "gloss the skirting", "glossing the skirting",
                                                  "skirting tile", "tiles", "tiling", "grout",
                                                  "caulk", "silicone", "rot", "woodworm",
                                                  "how do i fit", "fitting", "replace",
                                                  "replacing", "remove", "removing a",
                                                  "how high", "height"),
      guard=_paint_is_the_subject),

# Which brush: the filament is the paint's business, the width is the job's.
entry("brush-for-paint",
      (("brush", "brushes", "paintbrush", "paintbrushes", "filament", "filaments", "bristle",
        "bristles", "sleeve", "roller"),
       ("gloss", "glossing", "emulsion", "satin", "eggshell", "undercoat", "primer", "paint",
        "paints", "painting", "water based", "waterbased", "oil based", "oilbased", "solvent",
        "cutting in", "cut in", "woodwork", "trim", "skirting", "door", "doors")),
      "Synthetic filaments for anything water-based - emulsion, water-based gloss and satin - and "
      "natural bristle for oil-based gloss, which holds the solvent and lays off flatter without "
      "leaving brushmarks. Width matters more than brand: a 2 inch angled sash brush for cutting "
      "in and for gloss on woodwork, a 3 or 4 inch brush for a wall, and cheap is fine for "
      "emulsion but not for gloss, where a shedding brush leaves hairs in the finish. Between "
      "coats, wrap a water-based brush in a damp cloth inside a bag rather than washing it out "
      "each time, and comb a bristle brush straight after cleaning so it dries in shape.",
      bias=2,
      # which brush for hair, for a beard, for a dog, for pastry is another question, and so is
      # cleaning one - the brush-cleaning row has the ferrule and the comb
      avoid=("hair", "hairbrush", "beard", "dog", "cat", "pet", "pastry", "basting", "makeup",
             "make up", "blusher", "nail", "toothbrush", "teeth", "broom", "yard brush",
             "clean", "cleaning", "clean a paintbrush", "washing out", "dried out",
             "how do i clean", "buy", "bought", "best brand", "cheap", "price", "cost"),
      guard=_paint_is_the_subject),

# Thinning: white spirit for oil, water for water-based, and a little of it.
entry("thinning-paint",
      (("thin", "thinning", "thinned", "thinner", "thinners", "dilute", "diluting", "water down",
        "water it down", "too thick", "thick", "stiff"),
       ("gloss", "glossing", "emulsion", "satin", "eggshell", "undercoat", "primer", "paint",
        "paints", "painting", "varnish", "lacquer", "solvent", "white spirit", "turps",
        "brush marks", "brushmarks")),
      "White spirit for oil-based gloss, water for water-based paint, and only a little: about "
      "one part white spirit to ten parts paint, stirred in rather than shaken, and no more than "
      "about a tenth of water in emulsion or water-based gloss. More than that and the paint stops "
      "forming a film, so it dries patchy and the sheen goes. Thin only when the paint is "
      "genuinely stiff - a fresh tin that is hard to brush is usually too cold rather than too "
      "thick, so stand it in warm water for ten minutes first, and never thin a primer or an "
      "undercoat to stretch it, because that is what makes it fail.",
      bias=2,
      avoid=A_STAIN + ("gravy", "sauce", "soup", "jam", "cream", "yoghurt", "smoothie", "hair",
                       "blood", "nail varnish", "nail polish", "lose weight", "thinner person",
                       "become thin", "too thin", "underweight", "varnish a floor", "floorboards",
                       "french polish", "car paint", "car", "cars", "spray"),
      guard=_paint_is_the_subject),
# The two preparation rows, last in the file so they cannot take a fault line off a row above: a
# fault ("paint keeps dripping") is the thing going wrong, and an order question is the thing to
# do next, and no line in the deck asks both.
entry("prep-before-finish",
      (("sand", "sanding", "sanded", "sandpaper", "sand down", "smooth", "fill", "filling",
        "filled", "filler", "patch", "patching"),
       ("varnish", "varnishing", "varnished", "oil", "oiling", "wax", "waxing", "stain",
        "painting", "paint", "gloss", "lacquer", "prime", "priming", "primer", "undercoat",
        "coat", "coats", "first", "before", "after", "between")),
      "Fill first, then sand, then finish: push the filler into the dents and holes, leave it a "
      "little proud, and sand it back level with the wood once it is hard. Then sand the whole "
      "surface - 120 grit on a block for paint or varnish, 80 to 100 on a filler patch - wipe "
      "the dust off with a tack cloth, and put the first coat on. Sand lightly between coats "
      "with 180 to 240 grit and wipe the dust off again, because that is what makes the last "
      "coat sit flat; leave the final coat alone. On a wall you only need to sand between coats "
      "if there is a run or a bit of grit.",
      guard=_the_order_of_two_steps,
      bias=1),
entry("brackets-then-the-shelf",
      (("shelf", "shelves", "bracket", "brackets", "shelf bracket", "floating shelf"),
       ("first", "before", "or", "then", "put up", "hang", "fix", "fixing")),
      "The brackets go up first. Hold the shelf where you want it, mark the holes through the "
      "brackets with a pencil, take the shelf down, and fix the brackets to the wall with a "
      "fixing that suits it: a wall plug in brick or block, a screw into a stud, or a "
      "hollow-wall anchor in plasterboard with nothing behind it. Then screw the shelf to the "
      "brackets and check it with a spirit level along the shelf itself, not along one bracket.",
      guard=_a_shelf_and_its_brackets,
      bias=1),
]
