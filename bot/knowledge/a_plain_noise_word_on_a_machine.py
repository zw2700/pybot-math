"""A sound a machine makes, said with a word the machine's own card did not know by name.

"The radiator is clattering" and "my laptop fan is making a racket" are the same faults as "the
radiator is noisy" and "my laptop fan is loud", and until now only the second pair got the card:
the first pair came back as a reflection of the line ("Got it - the radiator is clattering").

The radiator card and the laptop fan card live in two files that every lane is editing, and a
change inside their word lists is always a conflict. These two rows are the same cards keyed on
the plain words for a sound, so they are here as their own domain and nothing hot has to move. The
machine still has to be named and the words are about a sound, so a leaking radiator, a bleeding
one, a cold top, a thermostat, a quarrel and a room fan all keep the answers they had.

Each row mirrors one card and says which: `radiator-plain-noise` is the pipes answer of
`radiator-noise` in `home.py`, and `laptop-fan-plain-noise` is the vents answer of
`laptop-fan-loud` in `technology.py`. If either card's wording is rewritten, its row here has to
follow, which is the price of not editing the hot files.
"""
from .lookup import entry

ANSWERS = ("home-and-diy", "technology")

# the plain words for a sound: what a person says when the machine is audible and they do not
# know the name of the part that is doing it
_NOISE = ("clatter", "clatters", "clattering", "racket", "racketing", "din", "drone", "droning",
          "thunderous", "deafening", "palaver", "rattling", "roaring", "howling")

_PIPES = ("Ticking and clicking is the pipes expanding as they heat, which is normal and stops "
          "once the system is warm. Banging or gurgling means air or trapped water: bleed the "
          "radiators and check the boiler pressure sits between 1 and 1.5 bar. If a radiator "
          "clatters or drones while the heating is running, the valve may be part open or the "
          "pump set too fast: open the valve fully and turn the pump down a step.")

_VENTS = ("It is cooling itself because it is hot, so clear the vents with a can of air and check "
          "what is using the processor in Task Manager or Activity Monitor. A four-year-old laptop "
          "often just needs the dust out and new thermal paste (about £40 at a repair shop); if "
          "the noise continues at idle, the fan bearing is going.")

ENTRIES = [
    entry("radiator-plain-noise", (("radiator", "radiators"), _NOISE),
          _PIPES,
          # a radiator that leaks, a top that stays cold, a thermostat and a bleed question are
          # each a different job with its own row, and none of them is about a sound
          avoid=("leak", "leaks", "leaking", "leaked", "cold", "colder", "bleed", "bleeding",
                 "bled", "thermostat", "valve", "valves", "pressure", "bar", "not working",
                 "doesnt work", "doesn't work", "wont heat", "won't heat", "radiator paint",
                 "painting", "remove", "take off", "replace", "size", "how many")),

    entry("laptop-fan-plain-noise", (("laptop", "laptops", "macbook", "notebook"), _NOISE),
          _VENTS,
          # a bare "my fan" is a room fan that hums, and every other machine's noise has its own
          # row: this one only answers when the line named a laptop
          avoid=("my fan", "fan heater", "ceiling", "desk fan", "pedestal", "floor fan",
                 "tower fan", "box fan", "wall fan", "room fan", "bathroom", "kitchen",
                 "extractor", "cooker hood", "oven", "fridge", "freezer", "boiler", "radiator",
                 "washer", "washing machine", "dishwasher", "tumble", "dryer", "car", "van",
                 "engine", "console", "playstation", "ps5", "ps4", "xbox", "nintendo",
                 "computer fan", "pc fan", "desktop", "tower", "not charging", "won't turn on",
                 "wont turn on", "black screen", "slow", "overheat")),
]
