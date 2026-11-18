"""Keeping for food that is already cooked.

A food that is already cooked keeps on a different clock from the same food raw, and the
cooking-time entry for it owns every word of the question: "how long does cooked bacon keep" was
answered with the oven time, "how long does cooked mince last" with how to brown it, and the fish
with how long to bake it. One table, because the second half of every one of these questions is
the same question: how many days, in what, and how do I reheat it.

The rows are data only. bot/knowledge/cooking.py builds an Entry out of each one and appends it
to its ENTRIES, so the table is still one table and the matcher, the ranking and the domain stay
cooking's. They live here because cooking.py is close to the thousand-kilobyte file that the
world refuses to accept, and a keeping row per food is the part of it that grows.
"""

# The topic ids this module declares. It owns no Entries of its own - `bot/knowledge/cooking.py`
# builds one from every row in COOKED_KEEPS and appends it to its own ENTRIES - so the name the
# domain derives ("keeping-cooked") is a table name, not a topic the reader ever produces, and
# declaring it made `tests.test_routing_contract` fail on main. What these rows answer is where
# to keep a cooked thing and how long it lasts, which is cooking and not a subject of its own.
ANSWERS = ("cooking", "food-and-drink")

# A food that is already cooked keeps on a different clock from the same food raw, and the
# cooking-time entry for it owns every word of the question: "how long does cooked bacon keep"
# was answered with the oven time, "how long does cooked mince last" with how to brown it, and
# the fish with how long to bake it. One table, because the second half of every one of these
# questions is the same question - how many days, in what, and how do I reheat it.
COOKED_KEEP_ASK = ("cooked", "cooked it", "leftover", "leftovers", "left over", "roast",
                   "roasted", "fried", "boiled", "reheated", "reheat", "reheating",
                   "made it", "made too much", "already cooked", "yesterday")

# A follow-up that asks how long to cook it is the method question again, and the context
# lookup hands this table the earlier line's subject: "how long does cooked chicken last" then
# "how long do i cook it for" was answered with "3 days" on this branch. The keeping answer has
# no number for a pan, so a line with a cooking verb and its object stands down and the timing
# entry for the same food answers it, exactly as it did before the table existed.
# Food left out of the fridge is a food-safety question, and the keeping clock is the wrong one
# for it: "is it safe to eat cooked chicken that was left out overnight" is answered "bin it"
# (bot/knowledge/still_ok.py), not "keeps 3 days in the fridge", which sounds like permission.
LEFT_OUT_WORDS = ("left out", "left it out", "sat out", "sitting out", "left in the car",
                  "left on the side", "overnight", "all night", "all day", "is it safe",
                  "safe to eat", "still ok", "still okay", "still safe")

# "is it ok to reheat chicken twice" is a question about the second reheat, not about how many
# days the chicken keeps: the reheat rows answer it, and this table's "reheat it once" is the
# nearest it comes. Read as the keeping clock it pushed the better answer out of the turn.
REHEAT_AGAIN = ("twice", "two times", "again", "second time", "how many times",
                "more than once", "a third time")

# "How do i reheat chicken without food poisoning" is a safety question, and the reheat rows
# answer it with the ice-cold-middle and the 2-hour rule: the keeping clock is the panel beside
# that question, not the answer to it.
FOOD_SAFETY = ("food poisoning", "poisoning", "poisoned", "food safety", "danger zone")

# "How do i reheat chicken" asks for the method - the pan, the oven, the microwave, how hot - and
# the day count on the box is the panel beside that question, not the answer to it. "Can i reheat
# cooked chicken" is the keeping question itself and keeps this row. The phrasing holds for every
# food in this table, so it is one list, not a row per food.
HOW_REHEAT = ("how do i reheat", "how to reheat", "how should i reheat", "how long do i reheat",
              "how do i warm", "how to warm", "how do i heat up", "how to heat up",
              "best way to reheat", "best way to warm", "what is the best way to reheat")

COOKED_KEEP_AVOID = LEFT_OUT_WORDS + REHEAT_AGAIN + FOOD_SAFETY + HOW_REHEAT + ("cook it", "cook them", "cook it for", "cook them for", "boil it",
                     "boil them", "bake it", "bake them", "roast it", "roast them", "fry it",
                     "fry them", "simmer it", "simmer them", "how long do i cook",
                     "how long to cook", "how long should i cook", "how long do i boil",
                     "how long to boil", "how long do i bake", "how long do i reheat it for",
                     "pressure cook",
                     # A keeping time is never the answer to a quality question. "how do i keep
                     # roast chicken juicy" asked how it cooks, and the word "roast" was enough
                     # to bring it here once the fish row made `juicy`/`moist` less rare in the
                     # cooking domain; `keep-meat-juicy` answers it.
                     "juicy", "juicier", "moist", "moister", "tender", "tenderer", "succulent",
                     "stays moist", "keep it moist", "not dry", "does not dry out",
                     # The same holds for the coating: "how do i keep fried chicken crispy" was
                     # answered with how long cooked chicken lasts in the fridge, because "keep"
                     # and "chicken" are this table's words. A crispness question is a cooking
                     # question - `fried-crisp` in vegetables.py answers it.
                     "crispy", "crisp", "crispier", "crunchy", "soggy", "limp", "goes soft",
                     "gone soft", "not crispy", "wont crisp", "won't crisp")

COOKED_KEEPS = (
    (("chicken", "chicken breast", "chicken breasts", "chicken thighs", "turkey", "roast chicken"),
     "Cooked chicken or turkey keeps 3 days in the fridge in a covered box, and freezes for up to 3 "
     "months. "
     "Cool it within 2 hours of cooking, reheat it once until it is piping hot all through, and "
     "eat it cold only if it went straight into the fridge."),
    (("mince", "minced beef", "mincemeat", "bolognese", "chilli", "cottage pie", "shepherds pie"),
     "Cooked mince keeps 3 days in the fridge in a sealed box, and freezes for 2 to 3 months. "
     "Reheat it once until it is piping hot right through, and give it 2 days rather than 3 if it "
     "was in a sauce with cream in it."),
    (("sausage", "sausages", "sausage meat"),
     "Cooked sausages keep 3 to 4 days in the fridge in a covered box, and freeze for 2 months. "
     "Reheat them in a pan or the oven until they are hot right through rather than in a microwave, "
     "which leaves the middle cool."),
    (("bacon", "bacon rashers", "streaky bacon", "back bacon"),
     "Cooked bacon keeps 4 to 5 days in the fridge, wrapped or in a box, and freezes for 2 months. "
     "It is already cured, so it lasts longer than other cooked meat: reheat it in a dry pan until "
     "it sizzles, and eat it cold within 3 days."),
    (("gammon", "ham", "ham joint", "roast pork", "pork"),
     "A cooked gammon or ham joint keeps 3 to 5 days in the fridge, and sliced ham 3 days once the "
     "pack is open. Wrap it so it does not dry out, keep it away from raw meat, and freeze slices "
     "for up to 2 months."),
    (("salmon", "fish", "cod", "haddock", "trout", "prawns"),
     "Cooked fish keeps 2 days in the fridge, less than meat: box it once it has cooled, and eat it "
     "cold the next day rather than reheating it, because fish goes dry and rubbery the second "
     "time. It freezes for a month if you cooked too much."),
    (("lentils", "beans", "chickpeas", "kidney beans", "baked beans", "dhal", "dal"),
     "Cooked beans, lentils and chickpeas keep 3 days in the fridge in a covered box, and freeze "
     "for 2 months in portions. Reheat them until they are hot right through, and bin any that "
     "smell sour or have gone fizzy."),
    (("beef", "roast beef", "lamb", "roast lamb", "steak", "pork chop"),
     "Roast meat keeps 3 to 4 days in the fridge, sliced and covered, and freezes for 2 to 3 "
     "months. Rare beef is at the shorter end: 3 days. Reheat it once in gravy so it does not dry "
     "out, and eat the rest cold."),
)
