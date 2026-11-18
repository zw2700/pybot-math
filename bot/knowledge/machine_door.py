"""The door of a machine: a damp washer, and a remark about leaving it shut.

This is one row, and it sits in its own file rather than in home.py because home.py is at the
publisher's 1 MiB limit and every lane is appending to the end of it, so a row there collides on
every rebase. It answers a line that is a *cause*, not a fault.
"""
import re

from .lookup import entry

# A machine is a home job in this bot's reading, and home.py already declares the topic, so the
# union answers.py declares does not change.
ANSWERS = ("home-and-diy",)

# A tumble dryer is left out on purpose: it is never washed, so the advice below is not its, and
# the dryer's own smell is a lint-filter job that another row owns (broad-berry, #10150).
_MACHINE_IN_THE_CHAT = ("washing machine", "washer", "washer dryer", "dishwasher", "washing")
# ... and the machine has to be a smelly one: a remark about the door of a noisy machine is not
# this answer, and neither is one about a machine that is leaking.
_A_SMELLY_MACHINE = ("smell", "smells", "smelly", "stink", "stinks", "damp", "musty",
                     "mould", "mold", "mildew", "fusty", "whiff", "sour")


def _a_damp_machine_and_its_door(memory, understood):
    """The door left shut, said after a smelly machine, is the cause of the smell.

    Deck row `door-subject-01`: "my washing machine smells of damp" then "i leave the door shut".
    On main that second turn gets "Oil the hinges" - the machine card has just said that leaving
    the door and drawer open is what stops the smell coming back, and the person is telling the bot
    why their machine smells.

    The row needs the machine and a smell in what the *person* said (not in the bot's last answer,
    which mentions a smell on the way past), and a door that is shut rather than a fault with it:
    a door that will not shut, swings, rubs, squeaks, bangs, hangs off or needs a lock is the hinge
    and latch rows' answer, and so is another door - a fridge, an oven, a car, a bedroom door.
    """
    text = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    if re.search(r"cant|cannot|can not|won'?t|will not|does not|doesn'?t|hard to|stuck|swings?|"
                 r"swinging|on its own|itself|hanging|off|lock|keyhole|slam|bang|squeak|squeal|"
                 # the fault, not the verb: "the door is always shut" is the remark this row is
                 # for, and `door is` fenced it out (broad-berry, #10150) - so the fence names the
                 # door that is broken, stiff, loose, stuck or jamming instead.
                 r"rub|paint|draught|draft|dragging|dropped|measure|door is not|door isnt|"
                 r"door isn'?t|door is broken|door is stiff|door is loose|door is stuck|"
                 r"door is jamming|door was broken|door was stiff|door was loose", text, re.I):
        return None
    said = [str((memory.get("topic") or {}).get("text") or "")]
    said += [str(one.get("text") or "") for one in (memory.get("topics") or [])[-4:]]
    chat = " ".join(said).lower()
    if not any(word in chat for word in _MACHINE_IN_THE_CHAT):
        return None
    if not any(word in chat for word in _A_SMELLY_MACHINE):
        return None
    # a dishwasher has no drum: the point is that the inside of the machine stays wet, which is
    # true of both (broad-berry, #10150)
    return ("Then that is very likely the cause: the inside of the machine stays wet between "
            "washes, and the smell grows in water that cannot dry. Leave the door and the "
            "detergent drawer open between washes, wipe the rubber seal round the door, and run "
            "one hot 60C or 90C wash with a machine cleaner or a cup of bicarbonate of soda to "
            "clear what has already built up.")


ENTRIES = [
    entry(
        "damp-machine-door",
        (("door", "doors"),
         # only the shut door: someone who already leaves it open is doing the right thing
         ("shut", "shuts", "closed", "closing", "left shut", "keep it shut")),
        _a_damp_machine_and_its_door,
        bias=3,
        # another machine, or a door that is not a machine's, is a different answer
        # another machine's door is a different answer; a machine that lives in a cupboard is
        # still the machine, so the room it stands in is not fenced (broad-berry, #10150)
        # The fault words belong in `avoid=`, not only in the fence below: an entry that matches
        # the key and then declines still takes the line from the composer's point of view, so
        # `my door is stiff to close` stopped naming the hinge row in a routing test while reading
        # the right answer (keen-willow, #10150). These are the words that make a door a fault.
        avoid=("stiff", "sticking", "sticks", "tight", "hard to shut", "hard to close", "rubbing",
               "rubs", "drags", "dragging", "squeak", "squeaks", "squeaking", "squeal", "creak",
               "creaks", "hinge", "hinges", "latch", "lock", "locked", "keyhole", "slam", "slams",
               "bang", "bangs", "banging", "swings", "swinging", "swung", "on its own", "itself",
               "hanging", "off", "dropped", "draught", "draft", "measure", "paint", "cant shut",
               "cant close", "cannot shut", "cannot close", "can not shut", "can not close",
               "wont shut", "wont close", "will not shut", "will not close", "does not shut",
               "does not close", "doesnt shut", "doesnt close", "fridge", "freezer", "oven",
               "microwave", "cooker", "car door", "front door",
               "back door", "car", "van", "bedroom door", "shower", "curtain", "blinds", "window",
               "gate", "key", "lock", "house", "flat", "landlord", "neighbour", "neighbor"),
    ),
]
