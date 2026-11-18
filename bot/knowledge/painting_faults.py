"""Three paint questions that hold no surface word, and so fell between the cards.

Most painting questions name the thing being painted - a door, a wall, a window, a radiator -
and a row that owns that thing answers them. These three name no surface, or name one the
other cards read the other way round, and each was answered with something from another job:

  how do i paint over gloss                   a finish named on its own is paint *already on*
  how do i stop brush marks when painting     something, and "over gloss" is the sanding
  gloss                                       question. The acrylics card for a beginner
                                              answered it instead, because the only row that
                                              holds gloss wants a surface word beside it.

  my door is painted shut                     a skin of paint bridging a door to its frame is
  the door is stuck shut with paint           a job to undo, not a door to paint. It was told
                                              to take the door off and paint the edges, and
                                              once that a stuck door wanted planing because it
                                              was swollen with damp.

  im painting the banister                    the trim in a room is either the thing being
  how do i paint skirting boards              painted or the thing to be kept clean, and the
                                              cards hold every word of both readings. The
                                              protect-the-skirting row answered the first, so
                                              the trim being painted has a row of its own.

Why a file: these are the faults and the trim, not a surface, and every existing painting
card is keyed by its surface. Keeping them here also keeps the three readings of the same
words in one place, where the guards that tell them apart can be read together.
"""
from .lookup import a_food_is_being_kept, entry

# The lines here are the same decorating ones the other painting cards answer, so this file
# takes no subject over: it answers what they pass on.
ANSWERS = ("home-and-diy",)

# The paint going on, in the forms a person writes it before they say what it is on.
_PAINT_WORD = ("paint", "paints", "painted", "painting", "repaint", "repainting", "re-paint",
               "gloss", "glossing", "glossed", "satin", "eggshell", "undercoat", "undercoating",
               "primer", "priming", "primed", "varnish", "varnishing", "varnished", "coating")

# A finish is what is already on the wood. Said with no surface beside it, the question is the
# coat going over it: "i want to paint matt gloss over satin" wants the sanding, not a wall.
_A_FINISH = ("gloss", "glossy", "satin", "eggshell", "sheen", "matt", "matte", "undercoat",
             "primer", "primed", "varnish", "varnished", "lacquer", "lacqered", "lacquered",
             "oil", "oiled", "mdf")

# A surface word hands the line back to the card that owns that surface: "how do i paint over
# gloss paint on a door" is the door's question and it is answered well.
_A_SURFACE = ("door", "doors", "cupboard", "cupboards", "kitchen", "skirting", "skirtings",
              "banister", "banisters", "bannister", "bannisters", "woodwork", "radiator",
              "radiators", "wall", "walls", "ceiling", "ceilings", "room", "rooms", "floor",
              "floors", "floorboard", "floorboards", "window", "windows", "frame", "frames",
              "sill", "sills", "windowsill", "furniture", "table", "tables", "chair", "chairs",
              "shelf", "shelves", "shed", "fence", "fences", "gate", "gates", "bedroom",
              "bathroom", "hallway", "stairs", "stair", "handrail", "architrave", "trim",
              "wardrobe", "wardrobes", "cabinet", "cabinets", "drawer", "drawers", "toy",
              "toys", "car", "cars", "bike", "bicycle")

# Paint that has landed somewhere it was not meant to go is the cleaning card's question, and
# a coat that has to dry has its own wait.
_A_ACCIDENT = ("carpet", "carpets", "rug", "rugs", "sofa", "sofas", "couch", "settee",
               "curtain", "curtains", "cushion", "cushions", "clothes", "clothing", "shirt",
               "shirts", "jeans", "trousers", "jacket", "jackets", "hands", "hand", "hair",
               "skin", "fingers", "fingernails", "nails", "washing machine", "bath", "sink",
               "tiles", "tile", "tiling", "grass", "patio", "drive", "driveway")

_A_WAIT = ("how long", "take to dry", "takes to dry", "dry", "dries", "drying", "dried",
           "recoat", "re-coat", "between coats", "touch dry", "hard", "cure", "curing",
           "seconds", "minutes", "hours", "days")

# Taking a finish off is not painting over it.
_A_STRIPPER = ("remove", "removing", "removal", "get off", "take off", "taking off",
               "strip", "stripping", "stripper", "sand off", "sanding off", "peel", "peeling",
               "peeled", "flake", "flaking", "bubble", "bubbling", "blister", "blistering")

# The trim in a room, in the forms a person says it.
_THE_TRIM = ("skirting", "skirtings", "skirting board", "skirting boards", "banister",
             "banisters", "bannister", "bannisters", "woodwork", "architrave", "handrail",
             "handrails", "spindle", "spindles", "balustrade", "picture rail", "dado rail",
             "window sill", "windowsill", "window sills", "windowsills", "sill", "sills",
             "trim", "door frame", "door frames")

# Paint that is on its way somewhere, rather than onto the trim: the preposition that puts the
# trim on the receiving end of the paint.
_ON_THE_WAY = ("on", "onto", "off", "getting", "goes", "going", "got", "spilt", "spilled",
               "splash", "splashes", "splashed", "drips", "dripping", "runs", "running",
               "from", "under", "behind", "against", "down", "near", "round", "around")

# A mark in the surface that a coat goes over. Old stains creep back through ordinary paint, so
# the answer is a blocking coat and not another coat of emulsion.
_A_MARK = ("stain", "stains", "stained", "mark", "marks", "knot", "knots", "rust", "rusty",
           "nicotine", "tar", "smoke", "grease", "oily", "biro", "pen", "marker", "crayon",
           "felt tip", "felt pen", "watermark", "watermarks", "tide mark", "tide marks")

# Oil, water or smoke behind a wall is the damp card's question: a stain block over a leak is a
# patch over a fault, so those lines stand this row down.
_A_LEAKING = ("leak", "leaks", "leaking", "leaked", "damp", "damp patch", "damp patches",
              "water", "rain", "raining", "roof", "gutter", "gutters", "pipe", "pipes", "burst",
              "condensation", "mould", "mold", "mouldy", "moldy", "flood", "flooded")

# The coat that goes over the mark.
_A_OVER = ("paint over", "painting over", "paint on top of", "cover", "covering",
           "showing through", "shows through", "showing up", "coming through", "come through",
           "bleeding through", "bleeds through", "seeping through", "block", "blocking",
           "stain block", "stainblock", "hiding")


def _words(understood):
    if not isinstance(understood, dict):
        return ()
    return [str(word).lower().strip(",.;:!?") for word in (understood.get("words") or ())]


def _paint_is_the_subject(understood):
    """True when the line is about paint going on a surface, not a food about to be kept."""
    if not isinstance(understood, dict):
        return False
    return not a_food_is_being_kept(understood)


def _a_finish_with_no_surface(understood):
    """A finish named on its own: the coat going over what is already there.

    "how do i paint over gloss" and "i want to paint matt gloss over satin" name no surface, so
    no card that owns a surface can answer them, and the coat over a finish is the sanding one.
    A line that names the surface instead ("how do i paint over gloss paint on a door", "gloss
    on the woodwork") belongs to the card for that surface, and a coat that has to dry, a coat
    that landed on a carpet and a finish being taken off are three other cards' questions.
    """
    if not _paint_is_the_subject(understood):
        return False
    words = _words(understood)
    if not any(word in _A_FINISH for word in words):
        return False
    if any(word in _A_SURFACE for word in words):
        return False
    if any(word in _A_ACCIDENT or word in _A_WAIT or word in _A_STRIPPER for word in words):
        return False
    return True


def _the_paint_has_sealed_it(understood):
    """The line itself names the paint that sealed the door.

    "wont shut" and "wont close" are a swollen door's words, so this row wants the paint in the
    line, not only in the chat before it: after a turn about a tin, "the door wont shut" belongs
    to the swollen-door card.
    """
    if not _paint_is_the_subject(understood):
        return False
    return any(word in _PAINT_WORD for word in _words(understood))


def _the_trim_is_what_is_painted(understood):
    """True when the line paints the trim itself, rather than protecting it from a wall's paint.

    Both readings hold every word of the family - "im painting the banister" and "how do i stop
    paint getting on the skirting" - so the difference is position: the trim straight after the
    paint word is what is being painted, and the trim after a preposition is what is to be kept
    clean.
    """
    if not _paint_is_the_subject(understood):
        return False
    words = _words(understood)
    for at, word in enumerate(words):
        if word not in _PAINT_WORD:
            continue
        for said in words[at + 1:at + 5]:
            if said in _ON_THE_WAY:
                break
            if said in _THE_TRIM:
                return True
    return False


def _a_stain_under_the_coat(understood):
    """A mark already in the surface, with a coat going over it: the blocking question.

    "how do i paint over a stain" was the acrylics hobby card. The stain is not paint and it is
    not dirt to scrub off now that the coat is the subject: what stops it creaping back through
    is a coat of stain block, and knots want shellac on them. A stain on a carpet, a sofa or a
    shirt is the cleaning card's, and water coming through a wall is the damp card's, because a
    stain-block primer over a leak is a patch over a fault.
    """
    if not _paint_is_the_subject(understood):
        return False
    words = _words(understood)
    if not any(word in _A_MARK for word in words):
        return False
    if any(word in _A_ACCIDENT or word in _A_LEAKING for word in words):
        return False
    return any(word in _A_OVER or word in _A_FINISH or word == "paint" or word == "painting"
               for word in words)


ENTRIES = [
# A door that is painted shut is a paint job that has to be undone. "my door is painted shut"
# was told to take the door off and paint the top and bottom edges first, and "the door is
# stuck shut with paint" that it was swollen from damp and wanted planing: both read the word
# door and the word paint and neither read the thing that went wrong, which is a thin skin of
# paint bridging the door to its frame.
entry("painted-shut",
      (("painted shut", "stuck shut", "sealed shut", "glued shut", "paint has sealed",
        "sealed with paint", "stuck with paint", "glued with paint", "paint in the gap",
        "paint in the cracks", "wont open", "won't open", "cannot open", "cant open",
        "can't open", "stuck fast", "jammed", "wont close", "won't close", "wont shut",
        "won't shut", "hard to close", "doesnt close", "doesn't close"),
       ("door", "doors", "front door", "back door", "drawer", "drawers", "cupboard door",
        "cupboard doors", "hatch", "lid")),
      "Score round the edge with a sharp knife where the paint has bridged it to the frame - down "
      "both sides, across the top, then along the bottom - and it will come free with a push "
      "rather than a shoulder. Then sand the paint off the edge and out of the rebate back "
      "to the wood, and rub a candle, a bar of soap or a little wax along the edge so the next "
      "coat cannot glue it again. If it is still tight afterwards, take a millimetre at a time "
      "off the edge with a plane or a sanding block, and prime the bare wood so it does not "
      "swell when the room gets damp. A lock or a handle painted over wants scoring round the "
      "same way before it will turn.",
      bias=2,
      avoid=("car", "cars", "van", "fridge", "freezer", "oven", "microwave", "washing machine",
             "dishwasher", "jar", "bottle", "glue", "superglue", "adhesive", "silicone",
             "caulk", "key", "keys", "lock", "locks", "locked out", "shut up", "shed door",
             "leak", "leaks", "leaking", "damp", "damp patch", "water", "rain", "raining",
             "roof", "gutter", "gutters", "pipe", "pipes", "condensation", "mould", "mold",
             "mouldy", "moldy", "plaster", "brick", "bricks", "brickwork", "ceiling", "flood",
             "flooded", "stain", "stains", "stained", "spilled", "spill", "scrub", "wipe off",
             "get it off", "remove", "removing", "clean off",
             # a window painted shut is the window row's, and it has the sash cords and the
             # soap on the runners that this has not
             "window", "windows", "sash", "sash window", "casement", "sill", "frame", "frames"),
      guard=_the_paint_has_sealed_it),

# A finish named on its own is paint already on the wood, and a coat over a finish is the
# sanding question. The acrylics card for somebody learning to paint pictures answered "how do
# i paint over gloss" and "how do i stop brush marks when painting gloss", because the row
# that holds the sanding wants a surface word beside the finish.
entry("a-coat-over-a-finish",
      (("paint over", "painting over", "paint on top of", "painting on top of", "over gloss",
        "over the gloss", "over satin", "over eggshell", "over old paint", "over the old paint",
        "over a finish", "gloss over", "satin over", "matt over", "matte over", "eggshell over",
        "brush marks", "brushmarks", "brush strokes", "brushstrokes", "brush lines",
        "stopping brush marks", "no brush marks"),
       ("gloss", "glossy", "satin", "eggshell", "sheen", "matt", "matte", "undercoat",
        "primer", "priming", "primed", "varnish", "varnished", "lacquer", "lacquered", "paint",
        "painting", "painted", "coat", "coats", "wood", "wooden", "mdf")),
      "Sand it dull first: new paint needs a key to grip, so take the shine off old gloss with "
      "120 grit, wipe off the dust, then one coat of undercoat and your topcoat. A water-based "
      "satin goes on after the sanding alone and dries in a couple of hours; oil gloss straight "
      "onto old gloss is the way to get peeling in a year. Brush marks come from too much paint "
      "on a cheap brush, so thin it a little if it drags and keep the brush moving one way.",
      # 3, not 2: a second row in this domain that also says "over" takes the one-word rarity
      # bonus this row was winning its ties with, so the nudge has to make up the point itself
      bias=3,
      avoid=("what colour", "what color", "which colour", "which color", "colour", "colours",
             "color", "colors", "better", "worse", "which is", "matt or gloss", "gloss or matt",
             "satin or gloss", "gloss or satin", "eggshell or gloss", "wallpaper", "wall",
             "walls", "ceiling", "ceilings", "room", "rooms", "bedroom", "bathroom", "hallway",
             "kitchen", "tiles", "tile", "tiling", "grout", "damp", "mould", "mold", "dulux",
             "farrow", "little greene", "buy", "bought", "cost", "price", "cheap", "litre",
             "litres", "how much", "how many coats") + _A_ACCIDENT + _A_WAIT + _A_STRIPPER,
      guard=_a_finish_with_no_surface),

# The trim in a room is either the thing being painted or the thing to be kept clean while the
# wall is painted, and both readings hold every word: "im painting the banister" and "how do i
# paint skirting boards" were told how to stop paint getting on the skirting. Position decides
# it - the trim straight after the paint word is what is being painted.
entry("the-trim-is-what-is-painted",
      (("paint the skirting", "paint skirting", "paint skirting boards", "painting the skirting",
        "painting skirting boards", "paint my skirting", "gloss the skirting",
        "gloss the skirting boards", "paint the banister", "paint banisters",
        "painting the banister", "painting the banisters", "paint the woodwork",
        "painting the woodwork", "paint woodwork", "gloss the banister", "gloss the woodwork",
        "paint the architrave", "paint the window sill", "paint the windowsill",
        "paint a banister", "paint a bannister", "paint a spindle", "paint a handrail",
        "paint an architrave", "paint a door frame", "paint a skirting",
        "paint the door frame", "paint the trim", "paint the handrail", "paint the spindles",
        "paint", "painting", "painted", "repaint", "repainting", "gloss", "glossing", "satin",
        "undercoat", "primer"),
       _THE_TRIM),
      "Sand them, wipe the dust off and run masking tape along the carpet, then brush with the "
      "grain in long strokes and a light load on the brush so it does not run onto the wall. Two "
      "thin coats beat one thick one, and satin or eggshell is easier to wipe than gloss. If you "
      "are doing the walls too, do the woodwork first.",
      # the protect-the-skirting row beside this one keys the same trim and the same paint
      # and carries bias=3, and it took both readings of the family on that strength: the
      # phrases above say "paint the thing", one bias above it wins the tie outright, and the
      # avoid list keeps every protecting line for the row that protects
      bias=4,
      ask=("how", "what", "which", "should", "can", "best", "way", "sand", "sanding", "prep",
           "prepare", "method", "start", "need to", "give", "im", "i'm", "i am", "im just",
           "just painting", "just glossing", "want to", "wanna", "going to", "gonna"),
      avoid=("stop paint", "paint getting", "getting paint", "getting", "keep paint", "keep",
             "protect", "protecting", "mask", "masking", "cut in", "cutting in", "neatly",
             "neat", "splash", "splashes", "splashed", "spillage", "drips", "dripping",
             "clean", "cleaning", "cleaner", "clean off", "off the", "dust", "dusty",
             "wipe", "remove", "removing", "strip", "stripping", "sanding off", "colour",
             "color", "what colour", "which colour", "how much", "cost", "price", "buy"),
      guard=_the_trim_is_what_is_painted),

# A stain already in the surface, with a coat going over it, is the blocking question. "how do
# i paint over a stain" was the acrylics hobby card, and "will a stain come through paint" was
# the damp card: a mark that keeps coming back through the finish wants a stain-block primer,
# and a knot wants shellac on it before anything else.
entry("a-stain-under-the-coat",
      (# not "paint over": that phrase is the coat-over-a-finish row's, and a word two rows
       # key is no longer a word only one of them says, which drops the row that needs it
       ("over a stain", "over the stain", "over stains", "over old stains", "over a mark",
        "over the mark", "over marks", "over rust", "over the rust", "over nicotine",
        "cover", "covering", "showing through", "shows through", "showing up",
        "coming through", "come through", "bleeding through", "bleeds through", "seeping through",
        "stain block", "stainblock", "block the stain", "block a stain", "hiding"),
       ("stain", "stains", "stained", "mark", "marks", "knot", "knots", "rust", "rusty",
        "nicotine", "tar", "smoke", "grease", "oily", "biro", "pen", "marker", "crayon",
        "felt tip", "felt pen", "watermark", "watermarks", "tide mark", "tide marks", "wood",
        "wooden", "door", "doors", "skirting", "ceiling", "wall", "walls", "table", "shelf")),
      "Scrub it back first - sugar soap for grease or nicotine, a light sand for a mark in the "
      "wood - then seal it with a stain block: shellac or an aluminium primer, because ordinary "
      "undercoat lets the mark creep back through in a month. Two thin coats of block, then your "
      "finish. A knot wants the resin scraped out and shellac over it, and rust wants sanding "
      "back to bare metal and a rust-killing primer before the topcoat.",
      bias=2,
      avoid=(# a mark on a ceiling, a wall or a roof is water, and the damp card reads it better
             # than this one: it says to press the patch, find where it comes in and record it
             "ceiling", "ceilings", "wall", "walls", "roof", "keeps", "kept", "keep coming back",
             "how do i get", "get out", "get off", "out of", "off the", "off my", "remove",
             "removing", "clean", "cleaning", "scrub out", "washing", "wash",
             "colour", "color", "which colour", "what colour", "how much", "cost", "price",
             "buy") + _A_ACCIDENT + _A_LEAKING + _A_WAIT,
      guard=_a_stain_under_the_coat),
]
