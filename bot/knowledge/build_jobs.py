"""A thing being put up: how long it takes, and what it needs.

The answers lane owns this domain. Two questions come before anybody builds a shed, a
playhouse or a flat-pack wardrobe - how long will it take, and what will we need - and the
bot answered neither: with a shed on order, "how long does one take to put up" and "what
tools will we need" were both search hedges (report 137542), while a repair has its own
clock ("how long to fix a dishwasher") and a shelf its own fixings.

Why its own domain: a job being put up is not a fault and not a coat of something. The
treating, repairing and lifespan rows all key the same nouns (shed, deck, fence panel) with
the same ask ("how long"), so a table of figures sitting among them is read against the
wrong question. Here the job is the subject and the ask picks which half of the card is
owed, so one table answers a shed, a bike store, a gazebo and a chest of drawers, and a new
job is one line of data rather than a new row.
"""
from .lookup import entry as _entry

ANSWERS = ("home-and-diy",)

# Each job carries three sentences: how long it takes, what it needs, and the thing that goes
# wrong on that job. The third is the one that makes the answer worth reading - a shed that is
# not level, glass cut to a frame that is not square - and it is the same in both halves.
_BUILD_JOBS = (
    # The narrower names come first: "bike shed" holds "shed", and the first tuple that matches
    # is the one whose figures a person gets.
    (("bike shed", "bike store", "bike storage"),
     "An hour or two for two of you, and the base is the whole job.",
     "A drill with masonry bits, a spanner, a spirit level and a tape measure; the fixings to "
     "the wall come with it and the ground anchor does not.",
     "It has to be bolted down as well as built, or the first gale takes the lid and the frame "
     "with it."),
    (("summerhouse", "summer house", "log cabin"),
     "Two of you: two days for a cabin-style one, and the base and the roof are a day each.",
     "A drill and driver, a spirit level, a stepladder, clamps, a saw and a mallet; the windows "
     "and the roofing felt come with it.",
     "Level the base to within a few millimetres and let the timber settle for a week before you "
     "hang the doors, or they will bind by the second month."),
    (("gazebo", "gazebos", "pop up gazebo"),
     "Twenty minutes for two of you with a pop-up one; a wooden one is a day.",
     "Nothing for a pop-up beyond its own frame and pegs; a wooden one wants a drill, a spirit "
     "level and a mallet.",
     "Peg every leg and add the guy ropes, even on a still day, because a pop-up gazebo is a "
     "kite with a roof."),
    (("climbing frame", "climbing frames", "swing set", "swingset", "wooden swing"),
     "A day for two of you, and digging the leg holes is half of it.",
     "A post hole digger, a spirit level, a drill and driver, a tape measure, a saw and a "
     "socket set.",
     "Set the legs in concrete and check the level before it goes off, then tighten every bolt "
     "again after a fortnight of use."),
    (("raised bed", "raised beds"),
     "An afternoon for two of you, and filling it takes longer than building it.",
     "A saw, a drill and driver, a spirit level, a tape measure and a staple gun for the liner.",
     "Line the inside with a membrane if the timber is treated, and leave the boards with a gap "
     "at the bottom for water."),
    (("shed", "sheds"),
     "Two of you: a day for a shed up to 8x6, and the base is a day of its own.",
     "A drill with wood and masonry bits, a tape measure, a spirit level, a stepladder, a mallet, "
     "a knife for the felt and a screwdriver; the screws come with it and the base does not.",
     "Get the base flat and level first, on slabs or a timber frame, because every panel follows "
     "it - and paint or treat the bare timber before the walls close up."),
    (("playhouse", "play house", "wendy house", "cubby house"),
     "Two of you: two to three hours, and a plastic one that clicks together is less.",
     "A screwdriver, a mallet, a spirit level and a tape measure; a wooden one comes with its "
     "screws but rarely with a base.",
     "Stand it on something flat, a paved square or a timber frame, or the door will not line up "
     "and the walls will not meet at the corners."),
    (("greenhouse", "green house"),
     "Two of you: a weekend for an aluminium 6x8, and a day of that is getting the base right.",
     "A drill with masonry bits, a spirit level, a stepladder, a tape measure, clamps and "
     "silicone; the glazing clips and the glass come with the frame.",
     "The base has to be square and level to within a few millimetres, because the glass is cut "
     "to fit and will not go in otherwise."),
    (("fence panel", "fence panels", "feather edge", "closeboard"),
     "About an hour a panel for two of you once the posts are in, and the posts want a day to "
     "set first.",
     "A post hole spade, a spirit level, a drill and driver, a saw and a string line; a panel is "
     "light but it is a sail, so this is a two-person job in any wind.",
     "Fix the panels to the posts, not the other way round, and brace the end posts until the "
     "concrete has gone off."),
    (("decking", "deck boards", "deck board", "raised deck"),
     "A 3x3 metre deck is two or three weekends for one person, and the frame is most of it.",
     "A saw, a drill and driver, a string line, a spirit level, a set square, clamps and "
     "stainless screws.",
     "Level the frame and set the joists at 400mm centres before a board goes down, and leave a "
     "gap of about 5mm between boards so the water runs off."),
    (("wardrobe", "wardrobes", "flat pack", "flat-pack", "flatpack", "chest of drawers",
      "bed frame", "bookcase", "sideboard"),
     "Two of you: two to four hours, and the doors and drawers are half of it.",
     "A Pozidriv screwdriver, a mallet, a tape measure and the Allen key that comes in the box; "
     "a cordless driver on its lowest clutch saves your wrists.",
     "Build it on its side on a rug or a flattened box, and fix anything over a metre tall to "
     "the wall, because a chest of drawers on an open drawer will go over."),
    (("kitchen unit", "kitchen units", "base units", "wall units", "kitchen cabinets",
      "fit a kitchen", "fitting a kitchen", "kitchen fitting", "kitchen install",
      "installing a kitchen"),
     "A run of five units is a day if you have done it before and two or three the first time, "
     "and the worktop is a day of its own.",
     "A spirit level, clamps, a drill and driver, a jigsaw, a tape measure and packers.",
     "Set the first unit dead level and square to the wall and clamp the next to it: everything "
     "after that one follows it, so ten minutes spent there saves the whole run."),
    (("trampoline", "trampolines"),
     "Two of you: an hour or two, and the springs are most of it.",
     "Two spanners, which are usually in the box, gloves, and the spring puller that comes with "
     "it.",
     "Put it on flat grass with the headroom the manual gives, fit the net before the first "
     "bounce, and peg the legs down."),
)

# "How long" is the ask for the clock, and a thing asked about with it is usually how long it
# *lasts*: those lines are the lifespan table's and are fenced off below rather than here.
_A_TIME_ASK = ("how long", "how many hours", "how many days", "how much time", "time to",
               "how many people", "how many of us", "hours to", "days to", "a weekend",
               "an afternoon", "a day to", "long to put up", "long to build", "long to assemble")
_A_TOOLS_ASK = ("what tools", "which tools", "tool", "tools", "tool kit", "toolkit",
                "equipment", "what do i need", "what will i need", "what do we need",
                "what will we need", "what else do i need", "what else will i need",
                "shopping list", "what to buy", "what bits")

# A job named together with one of these is not a question about putting it up: what it lasts,
# what it costs, whether to buy it, a fault in it, a coat of something on it, or the plants in it.
_NOT_A_BUILD = ("last", "lasts", "lasting", "lifespan", "cost", "costs", "price", "prices",
                "cheap", "cheaper", "buy", "buying", "bought", "which one", "best", "worth",
                "compare", "treat", "treating", "treats", "stain", "staining", "paint",
                "painting", "creosote", "preserver", "rot", "rotten", "repair", "repairs",
                "fix", "fixing", "broken", "blown", "leaking", "mould", "damp", "concrete",
                "ballast", "cement", "slabs", "tomato", "tomatoes", "cucumber", "chilli",
                "chillies", "pepper", "plants", "plant", "seeds", "sow", "sowing", "grow",
                "growing", "crop", "crops", "remove", "take down", "dispose", "skip")


def _a_build_job(memory, reading):
    """How long the job takes, or what it needs, for the job the line names."""
    line = (reading.get("clean") or reading.get("text") or "").lower()
    words = set(reading.get("words") or ())
    job = None
    for names, time, tools, caveat in _BUILD_JOBS:
        if any(name in words or name in line for name in names):
            job = (time, tools, caveat)
            break
    if job is None:  # the guard should have kept this line, so say the useful half anyway
        return None
    time, tools, caveat = job
    wants_time = any(ask in line for ask in _A_TIME_ASK)
    wants_tools = any(ask in line for ask in _A_TOOLS_ASK)
    chosen, spare = (tools, time) if wants_tools and not wants_time else (time, tools)
    # A line that asks neither - "me and my brother are doing it ourselves", reaching this row on
    # the ask the turn before - is owed the half it has not just been given, or the card says its
    # last sentence back twice in a row, which STYLE.md rules out.
    last = str((memory or {}).get("last_answer") or "").lower()
    if last and _opens_with(chosen).lower() in last:
        if _opens_with(spare).lower() in last:
            return None
        chosen = spare
    return "%s %s" % (chosen, caveat)


def _opens_with(sentence):
    """The first clause of a card sentence, which is what says the same thing twice."""
    return sentence.split(",")[0].split(" - ")[0].strip()


def _a_job_being_put_up(understood):
    """True for a line about putting a thing up: it names a job and asks how long or what with."""
    text = " ".join(str(one) for one in ((understood or {}).get("words") or ())).lower()
    if not text:
        text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(stop in text for stop in _NOT_A_BUILD):
        return False
    if not any(ask in text for ask in _A_TIME_ASK + _A_TOOLS_ASK):
        return False
    return any(name in text for names, _t, _l, _c in _BUILD_JOBS for name in names)


ENTRIES = [
    # The two questions before a thing goes up, and nothing answered either of them: a repair
    # has its clock and a shelf its fixings, but "how long does a shed take to put up" and "what
    # tools will we need" were search hedges (report 137542). The key is the job and the ask; the
    # guard does the reading, because a job named with "how long" is usually asking how long it
    # lasts, and every one of those is another row's question.
    _entry("a-job-being-put-up",
           (tuple(name for names, _time, _tools, _caveat in _BUILD_JOBS for name in names),
            _A_TIME_ASK + _A_TOOLS_ASK),
           _a_build_job,
           guard=_a_job_being_put_up,
           bias=2),
]
