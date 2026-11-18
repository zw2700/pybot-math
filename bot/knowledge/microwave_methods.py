"""Cooking in the microwave: pasta, scrambled eggs and vegetables.

The microwave answers were all about something else, because the word "microwave" is in the key of
the appliance cards rather than of a method:

  how do i cook pasta in the microwave      "Empty one cupboard at a time, wipe the shelves with hot
                                            soapy water" - the cupboards card
  how do i scramble eggs in the microwave   "melt a knob of butter in a pan" - a hob recipe
  how do i steam vegetables in the microwave "That's beyond what I know well, sorry"

The three that already answer well keep their lines: `how do i reheat rice safely`, `how do i cook
jacket potato in the microwave` and `how do i cook rice in the microwave` are not this table's
question, and "microwave" is not in these keys without a method word beside it.

Each row needs the appliance and its own dish, so a hob recipe, a reheat and a fault stay where they
are.
"""

from .lookup import entry

ANSWERS = ("cooking",)

# "microwave" has to be in the line: these are the microwave methods, and the hob versions are other
# cards. "micro" and "microvave" are how people type it in a hurry.
MICROWAVE = ("microwave", "microwave oven", "microwaves", "microvave", "microwaving", "microwave it")

# A fault, a clean, a purchase or a reheat is not a method: those cards answer them.
NOT_A_METHOD = ("not working", "broken", "sparking", "sparks", "smell", "smells", "clean",
                "cleaning", "descale", "repair", "buy", "buying", "which microwave", "best",
                "reheat", "reheating", "reheated", "warm up", "warm it up", "defrost", "defrosting",
                "how long", "jacket potato", "baked potato", "rice")

ENTRIES = [
entry("pasta-in-the-microwave",
      (MICROWAVE,
       ("pasta", "spaghetti", "penne", "fusilli", "macaroni", "noodles", "tagliatelle",
        "lasagne sheets", "cook pasta", "boil pasta")),
      "Pasta cooks fine in a microwave, in a big bowl with plenty of room: cover it with boiling "
      "water from the kettle, add a good pinch of salt, and give it 8 to 10 minutes on full power, "
      "stirring once at the halfway point so the pieces at the top get turned under. Use a bowl at "
      "least twice the size of the pasta, because it foams up over the edge otherwise. Test a piece "
      "at 8 minutes - it goes from chalky to mushy quickly - then drain it straight away.",
      bias=4,
      ask=("cook", "cooking", "boil", "make", "how do i", "how to"),
      avoid=NOT_A_METHOD),

entry("scrambled-eggs-in-the-microwave",
      (MICROWAVE,
       ("scrambled eggs", "scramble eggs", "scrambled egg", "scramble an egg", "eggs", "egg")),
      "Beat two or three eggs with a pinch of salt and a splash of milk in a mug or a small bowl, "
      "add a small knob of butter, and cook on full power in 30-second bursts, stirring properly "
      "between each one. Two eggs take about 90 seconds to two minutes in total, and they should "
      "come out still slightly wet - they carry on setting as you stir, and a microwave takes them "
      "from soft to rubbery in twenty seconds. Salt again at the end, not before. A whole egg in "
      "its shell is the one thing to keep out: it bursts, so if you want a fried egg on a plate, "
      "break it and prick the yolk first.",
      bias=4,
      ask=("scramble", "scrambled", "scrambling", "cook", "cooking", "make", "how do i", "how to"),
      # "boil" and "boiled" are not fences here: "how do i boil an egg in the microwave" is a
      # whole egg in its shell, which bursts, and this row is the one that says so. A poach, a
      # fry and an omelette are other answers.
      avoid=NOT_A_METHOD + ("poach", "poached", "fried", "fry", "frying", "omelette",
                            "scotch egg", "egg mayo")),

entry("veg-in-the-microwave",
      (MICROWAVE,
       ("vegetables", "veg", "broccoli", "green beans", "carrots", "carrot", "cauliflower",
        "peas", "sweetcorn", "cabbage", "spinach", "kale", "courgette", "asparagus", "sprouts",
        "steam", "steaming", "steamed")),
      "Put the veg in a microwave-safe bowl with two or three tablespoons of water, cover it with a "
      "plate or cling film with a corner turned back, and cook on full power: green beans and peas "
      "3 to 4 minutes, broccoli and cauliflower florets 4 to 5, carrot batons 5 to 6, from raw. "
      "Stir or turn them over at halfway, and stand for a minute before you lift the cover, because "
      "the steam is hotter than boiling water. Stop while they are still bright and a knife goes in "
      "with a little resistance - they carry on cooking as they stand.",
      bias=4,
      ask=("cook", "cooking", "steam", "steaming", "make", "how do i", "how to", "heat"),
      avoid=NOT_A_METHOD + ("roast", "roasting", "frozen veg", "grow", "growing", "plant",
                            "freeze", "freezing", "blanch", "boil them", "boiled")),
]
