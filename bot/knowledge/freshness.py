"""Freshness: has that food been out too long to eat.

"How long can cooked rice sit out", "is it ok to eat food left out overnight" and "i left the
pizza out overnight" are one question, and the answer depends on the food, so this is one table
keyed on the food the line names: rice is the strictest, cooked meat, fish, gravy and anything
with egg or mayonnaise next, milk and cream after that, and bread, cake, butter, hard cheese, jam
and fruit come to no harm because they were never a food-poisoning risk.

It lives here rather than in cooking.py because that file is past the size the world accepts for
an upload, so no change to it can be submitted. Ripeness ("is this fruit ripe", "how do i ripen a
mango") is a different question and belongs with shelf life in keeping.py.
"""
import re

from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("cooking", "food-and-drink")


# --- food left out -----------------------------------------------------------
# "Left the rice out on the counter", "I left the pizza out overnight", "how long can cooked rice
# sit out": one question, and the answer depends on which food it is, not on which words the line
# uses. Rice is the strict one, cooked meat and anything with mayonnaise is the next, and bread,
# cake, butter, hard cheese and fruit survive a night out because they were never a food-poisoning
# risk to begin with.
LEFT_OUT_KEEP = ("bread", "loaf", "cake", "butter", "cheese", "cheddar", "parmesan", "jam",
                 "marmalade", "pickle",
                 "chutney", "fruit", "banana", "apple", "orange", "biscuit", "crisps",
                 "chocolate", "honey", "cereal", "flour", "sugar", "nuts", "olives", "capers")
# Cheese is not one food: hard cheese is dry and salty enough to sit out, and soft cheese is
# exactly what listeria grows in. So the soft ones are read before the keep list, which has the
# bare word `cheese` in it and would otherwise tell someone to put a warm brie back.
LEFT_OUT_SOFT_CHEESE = ("soft cheese", "brie", "camembert", "mozzarella", "feta", "cream cheese",
                        "blue cheese", "stilton", "gorgonzola", "ricotta", "cottage cheese",
                        "mascarpone", "goats cheese", "goat cheese", "halloumi", "paneer")
LEFT_OUT_DAIRY = ("milk", "cream", "yoghurt", "yogurt", "custard", "ice cream", "ice-cream")
# A baby's bottle is milk, but not the milk you can smell: it has its own two hours and its own
# hour once the baby has started it, so it is read first and answered on its own.
LEFT_OUT_BOTTLE = ("formula", "breast milk", "baby milk", "expressed milk", "bottle of milk",
                   "baby bottle", "baby's bottle", "bottles of milk")
LEFT_OUT_RICE = ("rice", "risotto")
LEFT_OUT_MEAT = ("chicken", "turkey", "beef", "pork", "lamb", "ham", "bacon", "sausage",
                 # "meat" itself, and the cuts people name instead of the animal: without it
                 # "how long can meat sit out" was answered as a question about sitting down
                 "meat", "steak", "steaks", "chops", "mince", "burger", "burgers", "meatballs",
                 "gammon", "venison", "duck",
                 "sausages", "fish", "salmon", "tuna", "stew", "curry", "soup", "gravy",
                 "pasta", "spaghetti", "quiche", "mayonnaise", "mayo",
                 "potato salad", "pie", "pizza", "mince", "bolognese", "chilli", "lasagne",
                 "shepherds",
                 # a cooked vegetable is a cooked dish too, so it is not one of the safe ones
                 "peas", "beans", "sweetcorn", "couscous", "stuffing", "potatoes", "mashed potato",
                 # the lunchbox and the takeaway box: a sandwich, a wrap and a bowl of coleslaw
                 # carry cooked meat, egg or mayonnaise, so they are never in the safe list, and
                 # sushi and prawns are raw-then-cooked fish and shellfish. A sauce is a cooked
                 # dish as well; "i left the sauce out on the hob" was an echo.
                 "sandwich", "sandwiches", "wrap", "wraps", "coleslaw", "sushi", "prawn",
                 "prawns", "tofu", "sauce", "sauces")
# An egg is not a cooked dish: whole eggs are sold and kept on a shelf at room temperature and
# keep for weeks, so a night on the side is nothing. It is the cracked one and the cooked one
# that follow the meat rule, which is why the cooked words send the line on to that branch.
LEFT_OUT_EGG = ("egg", "eggs")
EGG_COOKED = ("cooked", "boiled", "scrambled", "fried", "poached", "omelette", "frittata",
              "hard boiled", "soft boiled", "quiche", "mayonnaise", "custard", "raw egg",
              "cracked", "broken egg", "shell", "smashed", "batter")
LEFT_OUT_ASK = ("left out", "left it out", "left them out", "left over out", "out overnight",
                "overnight", "all night", "sat out", "sit out", "sitting out", "stood out",
                # "how long can pasta sauce stay out" names the leaving-out the same way, and it
                # was reaching the boiling time; "stay out" is the same question as "sit out".
                "stay out", "stays out", "staying out",
                "out on the counter", "on the counter", "on the side", "on the hob",
                "out of the fridge", "forgot to put", "forgot it", "didnt put it",
                "did not put it", "room temperature", "went cold", "still out",
                # "i left the milk out" puts a word between the two, so the phrase never spans
                # it: the two words are listed on their own and the avoid list below keeps the
                # lines where neither means a night on the side ("we are out of milk", "i left
                # my lunch at home") away.
                # "cooked chicken that was left out overnight" is one phrase in the line and
                # three separate words in the flat list, and the doneness card outscored it on
                # "cooked" and "chicken". The phrase is keyed as it is written, so the line that
                # says the food was left out is read as a leaving line first.
                "was left out", "that was left out", "left out overnight", "sat out overnight",
                "was sat out",
                "left", "out")

# The same question said again after the leaving, with the food and the hours left to the line
# before it: "i left the chicken out for a few hours" then "can i still cook it", and "i left the
# mince out all night" then "is it still ok". The follow-up names no food, so `_left_out` reads
# the line it leans on for the food and the hours - and only when that line was itself a leaving
# line, so "my phone got wet" then "is it still ok" is not a food question. The line says what it
# is asking about, so the ask is in the key and the leaving is what the answer checks.
STILL_OK_ASK = ("still cook it", "still eat it", "can i cook it", "can i eat it", "can i still",
                "is it still ok", "still ok to eat", "still safe", "safe to eat", "still use it",
                "should i bin it", "should i throw it", "should i chuck it", "still good",
                "is it still safe", "can we still eat", "will it still be ok")

# Those two bare words are what goes wrong. "out" is a particle as often as it is a place: "the
# bread came out flat", "my rice came out mushy", "my scrambled eggs always come out rubbery" and
# "how do i get a cake out of the tin" are the result of a bake, and this row answered them with
# the food-poisoning rule ("Bread is one of the safe ones: there was never a food-poisoning risk
# at room temperature") in front of the cooking answer that was waiting below it. So the leaving
# words stand only when the line really says something was left out: a phrase from the list, or a
# leaving, sitting or keeping verb in front of the "out". "Out of" is a lack, not a leaving, so
# the bare word does not count when it is followed by it.
LEFT_OUT_PHRASE = tuple(phrase for phrase in LEFT_OUT_ASK if phrase not in ("left", "out"))

# A soak is a step with raw food in it; a night on the side is the leftovers question. One line
# can hold both halves, so the words alone cannot decide: "do i need to soak sticky rice
# overnight" wants the cooking answer, and "i soaked the beans overnight and left them out in
# the kitchen" wants the bin-it one even though it says soak. What makes the second a leftovers
# line is the second half, so the soak words stand the leftover rows down only when nothing in
# the line says the food has been out of the fridge. Both the food-left-out row here and the
# rice and pasta rows in cooking_entries use it, so a soak is one mechanism, not three.
OUT_OF_THE_FRIDGE = ("left out", "left it out", "left them out", "left this out", "sat out",
                     "sit out", "sitting out", "stood out", "standing out", "still out",
                     "been out", "out on the", "out all night", "out overnight", "out since",
                     "on the side", "on the counter", "on the worktop", "on the hob",
                     "on the table", "on top of the", "overnight on the")


def soak_but_not_left_out(understood):
    """True unless the line is a soak that also does not say the food was left out."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not re.search(r"\bsoak", said):
        return True
    return any(phrase in said for phrase in OUT_OF_THE_FRIDGE)
# A freezer is the one cold place this row has to share. "How long can beef stay in the freezer"
# is a keeping question with its own answer (`cooking_entries.py`'s `freezer-time`), and the word
# "freezer" stood this row down for it - but a food that is *out of* the freezer is exactly this
# row's question, and the two words blocked it: "how long can food be out of the freezer" was
# answered "in the freezer, about 3 months", which is true and no answer at all. So the freezer
# stands this row down only when the line puts the food *in* it.
_FREEZER_WORD = re.compile(r"\bfreez(?:e|es|er|ers|ing|ed)?\b|\bfrozen\b", re.I)
_OUT_OF_THE_FREEZER = re.compile(
    r"\bout\s+(?:of\s+)?(?:the\s+|my\s+|a\s+|your\s+|its\s+|their\s+)?freez(?:er|ers)\b", re.I)


def soak_but_not_left_out_or_in_the_freezer(understood):
    """True unless the line is a soak with nothing out, or the food is still in the freezer."""
    if not soak_but_not_left_out(understood):
        return False
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _FREEZER_WORD.search(said) and not _OUT_OF_THE_FREEZER.search(said):
        return False
    return True


# The leaving word is usually in front of the "out" ("i left the rice out"), but people also put
# the going first and the leaving second: "i went out and left the rice on the cooker". Both
# orders say the same thing, so both are read. The second order takes only the leaving and
# forgetting verbs - "was", "still" and "kept" in front of the "out" are about the food, not
# about a person going anywhere.
_LEAVING_VERB = (r"leave|leaves|leaving|left|forget|forgets|forgot|forgotten")
_LEAVING_OUT = re.compile(
    r"(?:\b(?:" + _LEAVING_VERB + r"|"
    r"sit|sits|sitting|sat|stand|stands|standing|stood|stay|stays|stayed|"
    r"keep|keeps|kept|been|being|is|are|was|were|still)\b"
    r"(?:\W+\w+){0,6}?\W+out\b(?!\s+of\b)"
    r"|\bout\b(?:\W+\w+){0,6}?\W+(?:" + _LEAVING_VERB + r")\b"
    # a food that is "out of the freezer" has left the cold without any leaving verb: "be out of
    # the freezer" is the same question as "sit out of the freezer", and the bare "out of" is
    # excluded above only because "out of milk" is a shopping line. The cold store named after
    # it is the food, so the phrase is the leaving.
    r"|\bout\s+of\s+(?:the\s+|my\s+|a\s+|your\s+|its\s+)?(?:freez(?:er|ers)|fridge)\b)")


# Every food this row knows, so a line that names one of them answers on its own words.
LEFT_OUT_FOODS = tuple(sorted(set(LEFT_OUT_MEAT) | set(LEFT_OUT_RICE) | set(LEFT_OUT_DAIRY)
                              | set(LEFT_OUT_KEEP) | set(LEFT_OUT_SOFT_CHEESE)
                              | set(LEFT_OUT_EGG) | set(LEFT_OUT_BOTTLE)
                              | {"food", "leftovers", "leftover", "takeaway", "sauce",
                                 "sandwich", "wrap", "curry", "soup", "stew"}))


def _asks_if_it_is_still_all_right(text):
    """True when the line asks whether the thing in hand can still be used."""
    return any(phrase in text for phrase in STILL_OK_ASK)


def _the_line_it_leans_on(memory, reading, text):
    """The line, with the leaving line before it in front when the line asks about that food.

    "i left the chicken out for a few hours" then "can i still cook it" is one question asked
    twice: the leaving, the food and the hours are all in the first line, and the second only
    says what the person wants to know. The reply reads the leaving off the first line, because
    the food-safety rule is the answer to the second one - a recipe is not. Three things have to
    hold, so an ordinary follow-up is never answered by this row: the line asks whether it is
    still all right, the line before it was itself a leaving line, and both are about the same
    food ("i left the chicken out overnight" then "can i still cook the mince" is not).
    """
    if _leaving_out(text):
        return text, False           # this line says the leaving itself
    if not _asks_if_it_is_still_all_right(text):
        return text, False
    earlier = ""
    leans = reading.get("leans_on") if isinstance(reading, dict) else None
    if isinstance(leans, dict):
        earlier = str(leans.get("text") or "").lower()
    if not earlier:
        try:
            from ..memory import last_user
            earlier = str(last_user(memory) or "").lower()
        except Exception:  # noqa: BLE001 - no history only means no line to read
            earlier = ""
    earlier = " " + earlier + " "
    if not earlier.strip():
        return text, False
    if not (_names_any(earlier, LEFT_OUT_FOODS) and _leaving_out(earlier)):
        return text, False
    named = _names_any(text, LEFT_OUT_FOODS)
    if named and not set(named) & set(_names_any(earlier, LEFT_OUT_FOODS)):
        return text, False   # a different food: the first line has nothing to say about it
    return earlier + text, True


def says_a_food_was_left_out(text):
    """True when the line says a food was left out on the side, and so is a food-safety line.

    The dish follow-ups read any line after a meal as being about the meal, and a person typing
    "i left the mince out all night" three turns into a cooking talk got "Mince and tomatoes make
    a ragu" - a recipe for food the bot had just told them to bin. The leaving is the subject of
    this module, so it is asked here rather than spelled out again in bot/modules/answers.py.
    """
    return _leaving_out(" " + str(text or "").lower() + " ")


def _leaving_out(text):
    """Does the line say a food was left out, rather than that a dish came out a certain way?"""
    if any(phrase in text for phrase in LEFT_OUT_PHRASE):
        return True
    return bool(_LEAVING_OUT.search(text))

# How long the line says it was out. "Two hours" is the line the reply itself quotes, so a person
# who says an hour or half an hour must not be told to bin it, and a person who says "a few
# hours" or "overnight" must not be told it is fine.
_COUNT_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "half": 0.5, "couple": 2, "couple of": 2, "few": 3, "a few": 3,
                "several": 3, "twelve": 12}
_SPAN = re.compile(r"\b(\d+(?:\.\d+)?|a few|couple of|half|a|an|one|two|three|four|five|six|"
                   r"several|twelve|few|couple)\s*(hours?|hrs?|minutes?|mins?)\b")


def _hours_out(text):
    """The hours the line says the food was out, or None if it does not say."""
    found = _SPAN.search(text)
    if found:
        count = _COUNT_WORDS.get(found.group(1))
        if count is None:
            try:
                count = float(found.group(1))
            except (TypeError, ValueError):
                return None
        return count / 60.0 if found.group(2).startswith("min") else count
    if re.search(r"\b(overnight|all night|the night|night|next morning|in the morning)\b", text):
        return 8.0
    return None


def _names_any(text, words):
    return [word for word in words if re.search(r"\b" + re.escape(word) + r"\b", text)]


def _agree(thing):
    """Eggs are plural and a pizza is not, and the reply says which."""
    many = thing.endswith("s") and not thing.endswith("ss")
    return {"be": "are" if many else "is", "were": "were" if many else "was",
            "them": "them" if many else "it", "they": "they" if many else "it",
            "look": "look" if many else "looks", "smell": "smell" if many else "smells"}


def _how_long(text, soft, kept, meat, rice, dairy):
    """"How long can it sit out" wants the rule, not a verdict on food nobody said was out.

    The same table, told as a limit rather than as a bin notice: a person asking before it
    happens must not be told to throw away a dish they are still cooking.
    """
    if soft:
        return ("Two hours on the side is the line for soft cheese: past that, bin it, because "
                "brie, camembert, mozzarella, feta and cream cheese can carry listeria, which "
                "grows in the fridge and changes neither the taste nor the smell. Hard cheese is "
                "the exception and can stay out a lot longer.")
    if rice:
        return ("Two hours is the line for cooked rice, and it is the strictest food there is: "
                "cool it fast, get it into the fridge within the hour and eat it within a day, "
                "because the toxin it can grow survives reheating.")
    if meat:
        return ("Two hours is the line for cooked meat, fish, gravy, pasta and anything with egg "
                "or mayonnaise in it - past that it is a bin job even if it looks and smells "
                "fine. Rice is the same. Bread, cake, butter, hard cheese, jam and fruit are the "
                "exceptions and come to no harm at all.")
    if dairy:
        return ("Two hours for milk, cream and yoghurt, and a whole night out is the bin job: "
                "they sour and can grow bacteria you cannot see or smell. Go by the smell if it "
                "is borderline.")
    if kept:
        word = kept[0]
        verb = _agree(word)
        return ("{thing} {be} one of the ones with no time limit: there was never a food-poisoning "
                "risk at room temperature, so a night out only makes {them} stale, dry or soft. "
                "The two hours and the bin apply to cooked meat, rice, milk and anything with "
                "mayonnaise.").format(thing=word.capitalize(), be=verb["be"], them=verb["them"])
    return ("Two hours out of the fridge is the line for anything cooked, and after a whole night "
            "it is a bin job - meat, fish, rice, milk and anything with egg or mayonnaise "
            "especially. Bread, cake, butter, hard cheese, jam and fruit are the exceptions and "
            "keep for a long time on the side.")


# "Chicken out" is to lose your nerve, and the inflected forms of it ("chickened out",
# "chickening out") are only ever that. The bare form is the bird as well, so it is read with the
# rest of the line: "i left the chicken out for a few hours" and "the chicken out on the counter"
# are the food question this row exists for, and "i always chicken out" and "my chickens out in
# the run need feeding" have nothing to do with a fridge. The words that make it the food are the
# ones a person uses when they are telling you how long something sat there or where it sat.
_CHICKEN_OUT = re.compile(r"\bchicken(?:s|ed|ing)?\s+out\b")
# The other half of the same confusion: something that is "left over" is a meal waiting in the
# fridge, not a food that spent the afternoon on the side. "half a roast chicken left over" is a
# line about using it up, and it was getting the bin-it card.
_LEFTOVER_WORD = re.compile(r"\b(?:left ?over|leftovers?|spare)\b")
_LEFT_OUT_WORD = re.compile(
    r"\b(?:left|leave|leaves|leaving|forgot|forget|forgotten|sat|sit|sits|sitting|stood|stand|"
    r"standing|still|overnight|nite|tonight|night|hours?|counter|side|worktop|hob|fridge|"
    r"freezer|frozen|defrost|out of)\b")
# The leftover test cannot count "left" as an out-of-the-fridge word, because "left over" has it:
# what it looks for instead is somewhere or somewhen, and the plain "out" is safe here.
_OUT_OF_PLACE_WORD = re.compile(
    r"\b(?:out|overnight|nite|tonight|night|hours?|counter|side|worktop|hob|fridge|"
    r"freezer|frozen|defrost|room temperature|sat|sit|sits|sitting|stood|standing|still)\b")
# How the cooking turned out is not a night on the side: "my roast potatoes came out soggy" and
# "the milk boiled over on the hob" both carry a word this rule keys on ("out", "on the hob") and
# neither is asking whether the food is still safe. The fault has its own answer, so this rule
# stands down and lets it be found.
COOKING_RESULT = ("came out", "come out", "comes out", "came up", "turned out", "turn out",
                  "turns out", "boiled over", "boils over", "boiling over", "boil over",
                  "boiled dry", "boils dry", "boiling dry", "caught on the bottom",
                  "catches on the bottom", "stuck to the pan", "sticks to the pan",
                  "stuck to the bottom", "went wrong", "goes wrong", "gone wrong")
# A food whose cooking went wrong AND which was also left out is the left-out question, even when
# no hours are given: "my milk boiled over and i left it out" asks whether the milk is still safe,
# and the boil-over tip answers how to stop it happening again. "Overnight", "all night", "this
# morning" and a count of hours say the same thing without the verb.
_SAID_OUT = re.compile(
    r"\b(?:left|leave|leaves|leaving|sat|sitting|stood|standing|kept|been)\b[^.]{0,20}?\bout\b"
    r"|\bout\s+(?:overnight|all\s+night|all\s+day|since|for)\b"
    r"|\b(?:overnight|all\s+night|all\s+day|this\s+morning|last\s+night|yesterday)\b"
    r"|\bfor\s+(?:\d+|a\s+few|a\s+couple\s+of|a|an)\s*(?:minutes?|mins?|hours?|hrs?)\b", re.I)

# Getting the bird out of the freezer is not the same as leaving it out on the side. "i forgot to
# take the chicken out" and "i keep forgetting to take it out" are the defrost questions, and
# they were read as a food that had spent the afternoon on the counter, because "forgot" and
# "forget" are in the leaving words above. A taking-out with no time and nowhere named is the
# freezer; one that also says how long it sat there or where ("took it out and left it on the
# counter for three hours") is still this rule's line.
_TAKING_OUT = re.compile(r"\b(?:take|takes|taking|took|taken|get|gets|getting|got)\b"
                         r"[^.;]{0,24}\bout\b")
_SPENT_ON_THE_SIDE = re.compile(r"\b(?:overnight|nites?|nights?|tonight|hours?|counter|worktop|"
                                r"hob|side|room temperature|since|left it|leaving it)\b")
# The row that answers a bird still in the freezer is the defrost one, and it is the bird it was
# written for: a joint of meat has no defrost card of its own, so the leaving words stay as they
# are for it and this stands down for the chicken only.
_A_BIRD = re.compile(r"\b(?:chicken|chickens|poultry)\b")

# A cleaning job on a burnt pan, tin or tray: the words that say something is burnt on, and the
# things you clean it off. Both are needed, so "i burnt the milk i left out" stays this rule's.
BURNT_WORK = ("burnt", "burned", "burning", "burn", "scorched", "blackened", "charred")
BURNT_VESSEL = ("pan", "pans", "pot", "pots", "tin", "tins", "tray", "trays", "shelf", "shelves",
                "oven", "hob", "wok", "saucepan", "saucepans", "skillet", "griddle", "baking tray",
                "cake tin", "roasting tin", "baking tin", "baking sheet", "casserole")


def _left_out(memory, reading):
    """What happens to a food that spent the night on the side depends on the food.

    A follow-up that asks whether the food in hand can still be used ("can i still cook it") is
    the same question as the line before it, which is where the food and the hours are, so the
    verdict is said again as an answer about time rather than the whole card over again.
    """
    text = " " + (reading.get("clean") or "").lower() + " "
    text, borrowed = _the_line_it_leans_on(memory, reading, text)
    reply = _left_out_card(text)
    return _the_follow_up(text, reply) if borrowed and reply else reply


def _left_out_card(text):
    """The left-out card for a line that names the leaving and the food."""
    if _CHICKEN_OUT.search(text) and not _LEFT_OUT_WORD.search(text):
        return None
    if (_TAKING_OUT.search(text) and _A_BIRD.search(text)
            and not _SPENT_ON_THE_SIDE.search(text)):
        return None
    if not _leaving_out(text):
        # The words fitted the row and the line is about something else, so the row stands down
        # and the cooking or keeping answer below it gets the turn.
        return None
    if (_names_any(text, COOKING_RESULT) and _hours_out(text) is None
            and not _SAID_OUT.search(text)):
        return None
    if _LEFTOVER_WORD.search(text) and not _OUT_OF_PLACE_WORD.search(text):
        return None
    hours = _hours_out(text)
    short = hours is not None and hours <= 2
    soft = _names_any(text, LEFT_OUT_SOFT_CHEESE)
    kept = _names_any(text, LEFT_OUT_KEEP)
    meat = _names_any(text, LEFT_OUT_MEAT)
    rice = _names_any(text, LEFT_OUT_RICE)
    dairy = _names_any(text, LEFT_OUT_DAIRY)
    egg = _names_any(text, LEFT_OUT_EGG)
    cooked_egg = bool(egg) and bool(_names_any(text, EGG_COOKED))

    # A pan or a tin with something burnt on it is a cleaning job, not a night on the side: "get
    # burnt milk out of a pan" names milk and says "out", which is this rule's shape, and it was
    # answered with the two-hour dairy limit instead of the soak.
    if _names_any(text, BURNT_WORK) and _names_any(text, BURNT_VESSEL):
        return None

    # "How long can cooked chicken sit out" is a question about the rule. Nothing has been left
    # out yet, so "Bin it, I'm afraid" answers a thing the person did not say.
    # ...but only when the line is about sitting out: "how long does chicken take to cook" is a
    # cooking time, not a limit on time on the side.
    sitting = any(word in text for word in (" sit", "sits", "sitting", " leave", "leaves",
                                            "out", "keep", "keeps"))
    if "how long" in text and sitting and not cooked_egg:
        return _how_long(text, soft, kept, meat, rice, dairy)

    if cooked_egg and not meat:
        # "I left the scrambled eggs out" is the cooked-food rule, even though the word egg is
        # not in the meat list: an egg that has been cooked is a dish, not a shell.
        meat = ["egg"]

    # Whole eggs keep for weeks on a shelf, so a night on the side is not a bin job for them.
    if egg and not cooked_egg and not short:
        return ("Whole eggs are fine: they are sold and kept on a shelf at room temperature and "
                "keep for weeks, so a night on the side changes nothing. It is a cracked egg, or "
                "a cooked one - scrambled, boiled, fried, an omelette - that follows the two-hour "
                "rule and goes in the bin after a night out.")

    if soft:
        if short:
            return ("Inside the two hours, so it is fine even for this one: get it back in the "
                    "fridge now and eat it within a couple of days. Soft cheese is the risky end "
                    "of cheese, so it does not get the long stay a hard cheddar does.")
        return ("Bin it, I'm afraid. Soft cheese is the risky end of cheese: brie, camembert, "
                "mozzarella, feta, cream cheese and blue cheese can carry listeria, which grows in "
                "the fridge and does not change the taste or the smell. Anything more than two "
                "hours out is a bin job, and a hard cheese is the only one you can leave.")
    if kept and not (meat or rice or _names_any(text, LEFT_OUT_DAIRY)):
        word = kept[0]
        verb = _agree(word)
        return ("{thing} {be} one of the safe ones: there was never a food-poisoning risk at room "
                "temperature, so a night on the side only makes {them} stale, dry or soft. Put "
                "{them} back and carry on - it is cooked meat, rice, milk and anything with "
                "mayonnaise that you cannot leave out.").format(
                    thing=word.capitalize(), be=verb["be"], them=verb["them"])
    bottle = _names_any(text, LEFT_OUT_BOTTLE)
    if bottle:
        # A made-up bottle is the one milk a person cannot judge: it is not a couple of hours on
        # the table, it is two hours from the moment it is made, an hour once the baby has
        # started it, and then it goes. The dairy sentence sends people to the smell, and a
        # bottle that has gone does not smell.
        if hours is not None and hours >= 3:
            return ("Bin it. A made-up bottle is two hours from the moment it is made, and an "
                    "hour once the baby has started it, whatever the room is like: bacteria from "
                    "the baby's mouth get into the milk and warm milk grows them fast. It is not "
                    "one of the things you can judge by smell.")
        return ("Made-up formula or expressed milk is good for two hours at room temperature and "
                "a bottle the baby has started for one hour, so this one is inside the window: use "
                "it now rather than later, and past two hours it is a bin job. It is not dairy you "
                "can test by smell - two hours is the number, not the sniff.")
    if _names_any(text, LEFT_OUT_DAIRY):
        if short:
            return ("A couple of hours on the table is fine for milk, cream and yoghurt: get it "
                    "back in the fridge now and it will be good to the date on the pack. A whole "
                    "night out is the bin job, because they sour and can grow bacteria you cannot "
                    "smell.")
        return ("Milk, cream and yoghurt are fine on the table for a couple of hours at a meal, and "
                "a whole night out is a bin job: they sour and can grow bacteria you cannot see or "
                "smell. Keep it at the back of the fridge, not in the door, and go by the smell if "
                "you are not sure.")
    if rice:
        if short:
            return ("Inside the two hours, so it is fine: get it into the fridge now in a shallow "
                    "tub so it cools fast, and eat it within a day. Rice is the one to be careful "
                    "with, because the toxin it can grow survives reheating.")
        return ("Bin it after 2 hours out, and this one is the strictest of the lot: cooked rice "
                "can grow a toxin that reheating does not destroy, and it looks and smells fine "
                "while it does it. Next time cool it fast, fridge it within the hour, and eat it "
                "within a day.")
    if meat:
        word = meat[0]
        verb = _agree(word)
        if short:
            return ("{thing} inside the two-hour limit {be} fine: get {them} into the fridge "
                    "now, where cooked food keeps 3 days. It is only past two hours that this "
                    "becomes a bin job.").format(thing=word.capitalize(), be=verb["be"],
                                                  them=verb["them"])
        return ("Bin it, I'm afraid. {thing} left out for more than 2 hours {be} not safe to eat, "
                "even if {they} {look} and {smell} fine. Meat, fish, gravy and anything with egg or "
                "mayonnaise in it all follow that rule, so next time get it into the fridge "
                "within the hour.").format(
                    thing=word.capitalize(), be=verb["be"], they=verb["they"],
                    look=verb["look"], smell=verb["smell"])
    if short:
        return ("Inside the two hours, so it is fine: get it covered into the fridge now and eat "
                "it within a day or two. Two hours out is the limit, and it is a night out that "
                "makes it a bin job.")
    return ("Two hours out of the fridge is the line, and after a whole night it is a bin job for "
            "anything cooked, especially meat, fish, rice, milk or a dish with mayonnaise or egg "
            "in it. Bread, cake, butter, hard cheese, jam and fruit are the exceptions and come to "
            "no harm.")


def the_still_ok_follow_up(text, memory):
    """The verdict for "can i still cook it" after a line that had food left out on the side.

    Returned as the turn's answer, before the dish follow-ups, because the line names no food of
    its own: the leaving, the food and the hours are all in the line before it. Nothing else can
    see that - the lookup reads the line alone, the dish follow-ups read it against the meal the
    talk was on - so on main a person asked to confirm the verdict got a recipe for the very food
    the bot had told them to bin. None when the two lines do not make that pair.
    """
    here = " " + str(text or "").lower() + " "
    if _leaving_out(here) or _asks_if_it_is_still_all_right(here):
        verdict = _the_left_out_follow_up(here, memory)
        if verdict:
            return verdict
    return _the_food_it_just_said_to_bin(here, memory)


def _the_left_out_follow_up(here, memory):
    """The verdict for a line asking whether a food that sat out can still be cooked."""
    earlier = ""
    try:
        from ..memory import last_user
        earlier = " " + str(last_user(memory) or "").lower() + " "
    except Exception:  # noqa: BLE001 - no history only means no line to read
        return None
    if not (_names_any(earlier, LEFT_OUT_FOODS) and _leaving_out(earlier)):
        return None
    named = _names_any(here, LEFT_OUT_FOODS)
    if named and not set(named) & set(_names_any(earlier, LEFT_OUT_FOODS)):
        return None       # a different food: the line before has nothing to say about this one
    card = _left_out_card(earlier + here)
    if not card:
        return None
    return _the_follow_up(earlier + here, card)

# --- the food the bot has just said to bin -----------------------------------
# "my chicken is going off, is it still ok" then "what can i do with it" is not a meal question:
# the line asks what to do with the food, and the answer to that is what the bot has already told
# them. On main the dish follow-ups read the second line against the chicken the talk was on and
# answered with "the fastest change is the cut and the heat: thighs roasted hot with paprika..."
# - a recipe for the very food the first answer said must go in the bin. The line names no food
# of its own, so nothing else can see the pair; this row can, because the answer before it is
# still in the memory and its first sentence says which way it went.
SAYS_BIN = ("bin it", "bin them", "into the bin", "in the bin", "throw it away", "throw it out",
            "throw them away", "chuck it", "dispose of it")
HOW_IT_IS_KEEPING = ("going off", "gone off", "smells off", "smell off", "smells bad",
                    "smells funny", "is it ok", "still ok", "still good", "is it safe",
                    "is it off", "gone bad", "has gone bad", "use by", "out of date",
                    "past its date", "off yet", "gone slimy", "is it still")
WHAT_TO_DO_WITH_IT = re.compile(
    r"\b(?:what|what can i|what can we|what should i|what shall i|what do i|what will i)\b"
    r"[^.?!]*\b(?:do|make|cook|use|eat)\b[^.?!]*\b(?:with (?:it|them|that|this))\b"
    r"|\b(?:can|could|should|shall|will|is it ok to|is it safe to|is it fine to)\b"
    r"[^.?!]*\b(?:still )?(?:cook|use|eat|keep|freeze|save)\b", re.I)


def _the_food_it_just_said_to_bin(here, memory):
    """What to do with a food the answer before this line told the person to bin.

    Only that pair: the line has to ask what to do with the thing, and the answer before it has
    to be a bin verdict - the food is read off the line before that, because the line asking the
    question does not name it. A line naming a food of its own is a different question.
    """
    if not WHAT_TO_DO_WITH_IT.search(here):
        return None
    try:
        from ..memory import last_bot, last_user
        said = " " + str(last_bot(memory) or "").lower() + " "
        earlier = " " + str(last_user(memory) or "").lower() + " "
    except Exception:  # noqa: BLE001 - no history only means no pair to read
        return None
    # The first sentence of a freshness card says which way it went ("Chicken is the one to be
    # strict about ... means bin it"), so the verdict is read from the sentence rather than from
    # a second list of foods that could fall out of step with the card. A later "bin it" is
    # another answer's aside, and a bare "throw it away" is advice about something else.
    if not any(words in said.split(". ")[0] for words in SAYS_BIN):
        return None
    # The line before has to be a freshness question, or this reads any "bin it" as a verdict on
    # the food: "my potatoes have blight" is answered "cut the tops off and bin them", and the
    # follow-up "can i still eat them" was told the potatoes were a bin job on a heat rule that
    # has nothing to do with blight.
    if not (_asks_if_it_is_still_all_right(earlier) or _leaving_out(earlier)
            or any(words in earlier for words in HOW_IT_IS_KEEPING)):
        return None
    food = _names_any(earlier, LEFT_OUT_FOODS)
    if not food:
        return None
    named = _names_any(here, LEFT_OUT_FOODS)
    if named and not set(named) & set(food):
        return None          # it names a different food: that food's own answer is the one
    thing = food[0]
    agree = _agree(thing)
    return ("Nothing to cook, I'm afraid: {thing} that {look} or {smell} like that {be} a bin "
            "job, and no recipe makes {them} safe - heat kills the bacteria growing on {them} "
            "but not the toxins they have already left behind. If the only thing wrong with "
            "{them} is the date on the packet, use {them} tonight rather than keep {them} for "
            "another day."
            .format(thing=thing, look=agree["look"], smell=agree["smell"], be=agree["be"],
                    they=agree["they"], them=agree["them"]))


def _the_follow_up(text, reply):
    """The verdict as the answer to "can I still cook it", instead of the card over again.

    Cooking does not undo the time on the side: heat kills the bacteria that grew while it sat
    out, but not the toxins some of them have already left behind, so it can still make a person
    ill. That is the answer to the follow-up, said about the rule rather than about the food. The
    safe things - bread, cake, butter, hard cheese - keep the card, which is the right answer for
    them, and so does a food this function cannot place.
    """
    # The card's first sentence says which way it went: "Bread is one of the safe ones...",
    # "Whole eggs are fine...". A card that opens with the bin is the one this rewords, and the
    # verdict is read from the sentence rather than from a second list of foods that could fall
    # out of step with the card.
    first = reply.split(". ")[0].lower()
    if "bin" not in first or _names_any(text, LEFT_OUT_BOTTLE):
        return reply      # the safe ones, and the bottle, whose own card is the better answer
    hours = _hours_out(text)
    if hours is not None and hours <= 2:
        return ("Inside the two hours, so yes: use it now rather than later, and do not put it "
                "back in the fridge to keep. Two hours out is the line - past that it is a bin "
                "job even when it looks and smells fine.")
    return ("Bin it, I'm afraid: past two hours out it is not safe, and cooking does not undo "
            "that - heat kills the bacteria that grew while it sat out, but not the toxins some "
            "of them have already left behind, so it can still make you ill. Two hours is the "
            "line for meat, fish, rice, milk and anything with egg or mayonnaise in it.")


def _in_the_car(memory, reading):
    """A food carried in a warm car: the same two hours, less on a hot day.

    The milk that sat on the back seat on the way home from the shop is the ordinary case, and it
    is fine - the fridge is what it needs once it is in. It is the whole afternoon in the sun that
    ends it, and that is the one thing the reply has to say, because it is the part a person
    cannot work out from "two hours out of the fridge". The reply names the food it read, so a
    line about sausages is not answered about milk.
    """
    text = " " + (reading.get("clean") or "").lower() + " "
    thing = None
    for words in (LEFT_OUT_BOTTLE, LEFT_OUT_DAIRY, LEFT_OUT_MEAT, LEFT_OUT_KEEP):
        found = _names_any(text, words)
        if found:
            thing = found[0]
            break
    hot = bool(re.search(r"\b(hot day|heatwave|in the sun|all afternoon|all day|sunny|summer|"
                         r"hot car|warm car)\b", text))
    if thing is None:
        thing = "food"
    if hot:
        return ("{Thing} in a hot car is the worst place it can be: a warm car gets well past "
                "fridge temperature, so count it as more than two hours out and bin anything "
                "cooked, dairy or made with mayonnaise that spent the afternoon there. On a hot "
                "day a cool bag, or buying the {thing} last, saves the whole question."
                ).format(Thing=thing.capitalize(), thing=thing)
    # A picnic or a walk home is the same physics as the car and not a car, so the sentence
    # follows the place the person named rather than answering "in the sun" with a car.
    if re.search(r"\b(car|cars|boot|back seat|van|drive)\b", text):
        where = ("A car is a warm room with no fridge in it, so the two-hour rule applies to the "
                 "{thing} as it does anywhere else: fine for the drive home, then straight into "
                 "the fridge.")
    else:
        where = ("Out of the fridge with no cool bag is the same as the table, so the two-hour "
                 "rule applies to the {thing} as it does anywhere else: fine for the journey, "
                 "then into the fridge as soon as you are in.")
    return (where + " Anything cooked, dairy or made with mayonnaise that spent the afternoon "
            "warm is a bin job - warmth is what the bacteria that change neither taste nor "
            "smell need.").format(thing=thing)


def _marinate(memory, reading):
    """A marinade is meat in the fridge, not meat left on the side.

    "I want to marinate chicken overnight" carried the words chicken and overnight and was
    answered with the bin notice for chicken that sat out, which is the opposite of the question:
    a marinade is meant to sit, and it sits in the fridge.
    """
    text = " " + (reading.get("clean") or "").lower() + " "
    meat = _names_any(text, ("chicken", "fish", "salmon", "prawns", "turkey"))
    if meat:
        return ("Overnight is fine for a marinade, in the fridge: {thing} takes 30 minutes to 2 "
                "hours at room temperature and up to a day in the fridge, and the fridge is the "
                "safer way to do it. Whisk 3 parts oil to 1 part acid - lemon, wine or vinegar - "
                "with salt, then garlic, honey, soy or herbs.").format(thing=meat[0])
    return ("Overnight is what a marinade is for, and it belongs in the fridge: tougher cuts take "
            "4 hours or a full night, steak and lamb chops a few hours, and fish no more than an "
            "hour because the acid starts to cure it. Whisk 3 parts oil to 1 part acid - lemon, "
            "wine or vinegar - with salt, then garlic, honey, soy or herbs. More than a day in "
            "acid or sugar turns the meat mushy.")


# What the line has to name for the cooling row to answer it: the food, the pot, or the fridge
# itself. Without it a follow-up that leans on someone else's line reaches the row on words the
# person did not type this turn.
# Too hot to eat, too spicy, too salty: the dish needs fixing, and cooking.py's fix cards answer.
_A_FAULT_IN_THE_FOOD = re.compile(
    r"\b(?:too (?:spicy|hot to eat|hot for|salty|salt\w*|sweet|sour|bitter|thick|thin|dry|bland)"
    r"|way too (?:spicy|hot|salty)|far too (?:spicy|hot|salty)|cool it down|make it milder"
    r"|less spicy|too much (?:chilli|chili|salt|spice))\b")

_A_COOLING_SUBJECT = frozenset((
    "fridge", "refrigerator", "cool", "cooling", "cooled", "warm", "warmish", "hot", "lukewarm",
    "steaming", "leftover", "leftovers", "food", "stew", "curry", "soup", "rice", "pasta",
    "chilli", "chili", "casserole", "chicken", "meat", "pot", "pots", "pan", "saucepan",
    "milk", "bottle", "cake", "cakes", "sponge", "batch", "bolognese", "sauce", "stock",
    "tub", "tupperware", "containers", "container", "boxes", "box",
))


# A phone, a camera or a watch in a bag of rice is being dried, not cooled. The words are here
# rather than in the row's `avoid` because the gadget is in the line before the rice, and `avoid`
# only ever sees the words of the line it is answering.
_GADGETS = ("phone", "phones", "mobile", "iphone", "android", "smartphone", "camera", "watch",
            "tablet", "ipad", "laptop", "airpods", "headphones", "earbuds", "keyboard", "remote",
            "sim card", "memory card", "screen", "battery", "charger", "charging port")


def _a_gadget_in_the_talk(memory, understood):
    """True when a gadget is what the conversation is about, not the food in the line."""
    if any(word in str(understood.get("clean") or "").lower() for word in _GADGETS):
        return True
    turns = (memory or {}).get("turns") or ()
    recent = [str(one.get("user") or "").lower() for one in turns[-3:] if isinstance(one, dict)]
    return any(word in line for line in recent for word in _GADGETS)


def _cool_before_fridge(memory, understood):
    """How to get something hot into the fridge, said for the thing in the person's hand.

    A pot of stew, a tub of leftovers and a bottle of warm milk cool at different speeds and are
    eaten on different clocks, so the reply follows the object: an ask for the quick way gets the
    sink of cold water first, cooked rice has its own hour and its own reason, milk is stood in a
    jug of water, and a plate or a tub is spread shallow.
    """
    words = set()
    for word in (understood.get("words") or ()):
        if isinstance(word, str):
            words.add(word.lower())
    said = str(understood.get("clean") or "").lower()
    # A follow-up is matched with the line it leans on, and that line can be a phone in a bag of
    # rice: "it wont turn on" after "my cat knocked my phone into the bath" was answered with
    # how to cool cooked rice, and then "An hour" to the turn after it. The subject has to be
    # in the line itself for this row to answer it.
    if not words & _A_COOLING_SUBJECT:
        return None
    # A dish that is too hot to eat or too spicy is a fault to rescue, not a pot to cool before
    # the fridge: "the curry is too spicy how do i cool it down" was answered "let it cool on the
    # worktop for up to two hours", which is advice for the wrong question. The cooling words are
    # shared, so the fault in the food stands this row down and the fix card answers.
    if _A_FAULT_IN_THE_FOOD.search(str(understood.get("clean") or "").lower()):
        return None
    # A question about the clock is the roast's timetable, not a pot on the worktop: after
    # "how long do i need for the chicken", "what time should i put it in" came here and got
    # "spread it out in a shallow tub". The cooling question always names the cold end - a
    # fridge, a freezer, cool, cold, ice - so a line that asks the time and names none of them
    # is a timing question, and "when should i put it in the fridge" still gets its answer.
    if re.search(r"\bwhat time\b|\bwhen should i\b|\bwhen do i\b|\bwhat time do i\b", said) \
            and not re.search(r"\b(?:fridge|freez\w*|refrigerat\w*|cool\w*|cold|ice|chill\w*|"
                              r"worktop|defrost\w*)\b", said):
        return None
    # "i put it in rice" after "my cat knocked my phone into the bath" is the wet-phone
    # question, and this row took it and then answered "An hour" to the turn after. A line, or
    # the few lines before it, about a gadget is a gadget question, whatever grain it names.
    if _a_gadget_in_the_talk(memory, understood):
        return None
    quick = words & {"quickly", "quick", "fast", "faster", "fastest", "quickest", "rapidly",
                     "speed", "sooner", "hurry"}
    if "rice" in words:
        return ("Cool cooked rice fast, not slowly: spread it in a shallow tray and leave it no "
                "more than an hour, then cover it and put it in the fridge and eat it within a "
                "day, reheated until it is steaming hot. Rice left at room temperature grows a "
                "toxin that reheating does not destroy, which is why it gets an hour where a "
                "stew gets two.")
    if words & {"milk", "bottle", "bottles", "formula", "bottle of milk", "breast milk"}:
        return ("Stand the bottle in a jug of cold water for ten minutes, or hold it under the "
                "cold tap, then put it straight back in the fridge. Milk that has been warmed "
                "keeps about two days, so use it before the rest of the bottle and do not warm "
                "it twice - and never keep what a baby has already drunk from.")
    if words & {"cake", "cakes", "sponge", "brownie", "brownies", "muffin", "muffins",
                "cupcake", "cupcakes", "loaf", "loaves", "traybake", "bread", "buns"}:
        return ("Leave it in the tin for ten minutes, then turn it out onto a rack and let it go "
                "cold before anything goes on it: a warm cake steams itself soggy and the icing "
                "slides off. Do not put it in the fridge to speed it up - a chilled sponge goes "
                "heavy and stale faster than one kept in a tin.")
    if quick:
        return ("Stand the pot in a sink of cold water, with a cold pack or a tray of ice in it, "
                "and stir every few minutes: a big pot comes down to warm in about 20 minutes "
                "rather than two hours. Then cover it and put it in the fridge - it does not "
                "need to be stone cold, just not steaming. Past two hours out of the fridge, "
                "bin it.")
    if words & {"pot", "pots", "pan", "saucepan", "stew", "soup", "curry", "chilli", "chili",
                "casserole", "stock", "batch", "bolognese", "sauce"}:
        return ("Let it cool on the worktop for up to two hours, then cover it and put it in the "
                "fridge. A big pot straight off the hob warms the whole fridge, so split it into "
                "shallow tubs first - it does not need to be stone cold, just not steaming. "
                "Past two hours out, bin it.")
    return ("Spread it out in a shallow tub so it cools faster, leave it on the worktop for up to "
            "two hours, then cover it and put it in the fridge - it does not need to be stone "
            "cold, just not steaming. Eat leftovers within two days and reheat them until they "
            "are steaming hot all through. Past two hours out of the fridge, bin it.")


# --- food that has gone a bit past its best ---------------------------------------------
# The produce a person is holding when they ask, and the two states they describe. Kept apart
# from the leaving-out tables above because the question is the food in front of them, not the
# clock: nothing here needs the hours or the fridge.
PAST_IT_PRODUCE = ("banana", "bananas", "apple", "apples", "pear", "pears", "grape", "grapes",
                   "berries", "strawberries", "raspberries", "blueberries", "peach", "peaches",
                   "plum", "plums", "mango", "avocado", "avocados", "tomato", "tomatoes",
                   "spinach", "lettuce", "salad", "salad leaves", "rocket", "watercress",
                   "kale", "cabbage", "leafy", "greens", "carrot", "carrots", "cucumber",
                   "pepper", "peppers", "courgette", "courgettes", "broccoli", "cauliflower",
                   "onion", "onions", "fruit", "vegs", "vegetables", "veg", "produce")
# Soft, dry or wrinkly is water loss and the food is still dinner. Slimy, sour or mouldy is not
# water loss and no amount of cooking makes it safe again.
PAST_IT_STATE = ("gone soft", "went soft", "gone a bit soft", "a bit soft", "soft", "softened",
                 "wrinkly", "wrinkled", "shrivelled", "shrunken", "limp", "wilting", "wilted",
                 "floppy", "rubbery", "dry", "dryish", "stale", "gone a bit", "old", "slimy",
                 "slimey", "sticky",
                 "smelling", "smells", "smelly", "sour", "leaking", "mouldy", "mould",
                 "black spots", "spotty")
# The ask, because a state word on its own is not a question: "my cucumber has gone soft" is one,
# and "why does lettuce go slimy" and "how do i keep a bag of salad from going slimy" are not -
# those are the keeping rows'. The third part of the key is what puts the row above the row that
# answers what fruit and veg are made of.
PAST_IT_ASK = ("can i eat", "can i still", "is it ok", "is it still", "still ok", "still good",
               "still safe", "safe to eat", "eat it", "eat them", "use it", "use them",
               "should i bin", "throw it", "throw them", "chuck it", "ruined", "bin it",
               "what can i do with", "why is my", "why has my", "why are my", "why have my",
               "are they ok", "is it fine", "ok to eat", "gone a bit", "old", "been there a while",
               "has gone", "have gone", "went soft", "gone soft", "smells", "smelly", "slimy")
# The words that make it the bin whatever the food is. "Sticky" is on the list because the sugar
# in fruit goes sticky when it is going over, and it is the feel that people name.
PAST_IT_BIN = ("slimy", "slimey", "sticky", "sour", "smelly", "smells", "stinks", "mouldy",
               "mould", "mold", "furry", "fuzz", "leaking", "gone off", "went off", "rotten")
# What "still fine, and here is what to do with it" says about each kind of produce. The first
# entry that names the food in the line wins, so greens come before fruit.
PAST_IT_KINDS = (
    (("spinach", "lettuce", "salad", "salad leaves", "rocket", "watercress", "kale", "cabbage",
      "leafy", "greens"),
     "Leaves that have gone a bit yellow or brown are older, not unsafe: the colour is the leaf "
     "giving up its green, and it does not make anybody ill. Pick out any that are slimy or "
     "smelly - those are the ones to bin - and eat or cook the rest, because a yellowed leaf is "
     "still good wilted in a pan or stirred into soup."),
    (("banana", "bananas"),
     "A soft banana is a ripe one: the starch has turned to sugar, so it is sweeter and easier to "
     "mash - eat it, or put it in a smoothie or banana bread. A banana is the fruit that keeps "
     "best in the fruit bowl, never the fridge."),
    # a strawberry goes soft without getting sweeter, and nobody calls one wrinkly, so the sugar
    # belongs to the grape and the berry gets the water and the punnet
    (("grape", "grapes"),
     "A wrinkly grape has lost water and is sweeter for it, so eat them - and pick out any that "
     "are leaking or furred, because one going over spoils the rest in the punnet."),
    (("berries", "strawberries", "raspberries", "blueberries", "blackberries"),
     "A soft berry has only lost water, so it is still fine to eat - pick out any that are "
     "leaking or furred, because one going over spoils the rest in the punnet, and eat them "
     "sooner rather than later or cook them down with a little sugar."),
    (("apple", "apples", "pear", "pears", "peach", "peaches", "plum", "plums", "mango"),
     "A soft or shrivelled apple or pear has lost water: it is fine to eat, and it is at its best "
     "stewed, baked or in a crumble."),
    (("carrot", "carrots"), "A floppy carrot has lost water, not gone off: peel it and it is fine "
     "to eat, and standing it in a glass of cold water for an hour firms it up again."),
    (("cucumber", "courgette", "courgettes", "pepper", "peppers", "broccoli", "cauliflower"),
     "A soft cucumber, pepper or courgette has lost water and is fine, just not crisp: cook it "
     "rather than eat it raw, and cut away any soft spots."),
    (("tomato", "tomatoes"), "A soft tomato is fine and sweeter: cook it into a sauce rather than "
     "slice it raw, and use it before the ones around it go too."),
)
PAST_IT_GENERAL = ("It has lost water rather than gone off, so it is still fine to eat and better "
                   "cooked than raw.")


_STATE_WORD = re.compile(
    r"\b(?:" + "|".join(re.escape(word) for word in sorted(PAST_IT_STATE, key=len, reverse=True))
    + r")\b")


# "my 4 year old wont eat vegetables" was told "It has lost water rather than gone off, so it is
# still fine to eat and better cooked than raw": the row reads a food and a state, and a refusal
# has both words without being about the food at all. A line about somebody not eating is the
# feeding question whatever food it names, so every one of those words stands this row down.
_NOT_WANTING_TO_EAT = re.compile(
    r"\b(?:wont eat|won't eat|will not eat|wouldn't eat|would not eat|doesn't eat|does not eat"
    r"|refuses|refusing|refused|fussy|picky|won't touch|wont touch|will not touch|year old"
    r"|toddler|my son|my daughter|my child|my kid|my kids|children|kids|nursery|school dinner"
    r"|fed up of|sick of eating|only eats|ate nothing|eats nothing|barely eats)\b")


# "how do i dry chilli peppers" was answered "a soft cucumber, pepper or courgette has lost
# water" - the state word "dry" is the verb of the line, not the condition of the food, and the
# drying row that answers the question already had it. Any method frame (how do I, how to, the
# best way to) followed by the word that would otherwise read as a state is a question about
# making the food that way, so it stands this row down. Only the frames are listed, because a
# line that says what it has in its hand - "my chillies have dried out", "can i eat dried
# apricots" - is this row's question and keeps its answer.
_HOW_TO_MAKE_IT_SO = re.compile(
    r"\b(?:how do i|how do you|how can i|how to|how would i|how should i|whats the best way to"
    r"|what's the best way to|best way to|quickest way to|easiest way to|any way to|way of)"
    r"(?:\W+\w+){0,2}?\W+(?:dry|drying|dry them|dry it|dehydrate|pickle|pickling|freeze|freezing"
    r"|ferment|fermenting|cure|curing|smoke|smoking|bottle|bottling|can|canning|preserve"
    r"|preserving|keep|keeping|store|storing|revive|reviving|crisp up|crisp it up)\b")


def _says_the_state(understood):
    """True when the line says what state the food is in, not only what state it is."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _NOT_WANTING_TO_EAT.search(said):
        return False
    if _HOW_TO_MAKE_IT_SO.search(said):
        return False
    return bool(_STATE_WORD.search(said))


def _past_its_best(memory, understood):
    """The verdict on food that has gone a bit past its best, said about the food in hand."""
    text = " " + str((understood or {}).get("clean") or (understood or {}).get("text")
                     or "").lower() + " "
    named = _names_any(text, PAST_IT_PRODUCE)
    if not named:
        # The food has to be in the line. "half of it is already limp" after a line about cabbage
        # is the keeping row's follow-up and it reads the line before; and a state word with no
        # food is a question about a dish, not about produce.
        return None
    if any(word in text for word in PAST_IT_BIN):
        return ("Bin it. The feel and the smell are what the stomach reacts to, not the colour, "
                "and cooking does not make it safe again: the bacteria that grew leave toxins "
                "behind that heat does not touch. Compost it and wash the drawer it was in.")
    for names, said in PAST_IT_KINDS:
        if any(word in text for word in names):
            return said
    return PAST_IT_GENERAL



# A dish that has been in the fridge for days is a keeping question, and the rows that answer it
# give a number of days and then say when to bin it. The cooling rows name a pot, a pan or a bowl
# and no period of time - "the stew has been in the fridge a week" was answered "straight in is
# fine - a modern fridge copes with a warm pot", which is the answer to a question the person had
# stopped asking. The period is what tells the two apart: a number of days, weeks or months, or a
# day of the week after "since". A number with no period is not enough, because how long a pot
# takes to cool is the cooling question itself.
_A_PERIOD_OF_TIME = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a|an|another|few"
    r"|several|couple(?=\s+of))\s+"
    r"(?:day|days|week|weeks|fortnight|fortnights|month|months|night|nights)\b"
    r"|\bsince\s+(?:yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    r"|\b(?:been|sat|sitting|stood|stored|kept|left|made|cooked|bought)\b(?:\W+\w+){0,4}?\W+"
    r"(?:in|inside|out)\s+of\s*the\s+(?:fridge|refrigerator)\b")


# The machine can be the thing that is slow, rather than the thing the dish goes into. "My fridge
# is taking ages to cool down" and "the freezer takes forever to get cold" reached this row on the
# two words of its key, "fridge" and "cool", and were told to spread a tub out on the worktop and
# eat the leftovers in two days - advice for a dish, given to someone whose appliance is not
# chilling. A cold machine named with no dish beside it is the fault row's question (home.py has
# the thermometer, the door seal and the coils), so this row stands down for it. The dish words
# stay, because "the stew takes ages to cool" is still a pot to cool down.
_COLD_MACHINE = re.compile(
    r"\b(?:my|the|our|your|his|her|their|this|that|a|an)\s+"
    r"(?:fridge freezer|fridge|freezer)\b")
_IN_THE_DISH = re.compile(
    r"\b(?:pot|pots|pan|pans|saucepan|saucepans|wok|bowl|bowls|tub|tubs|tray|trays|stew|stews|"
    r"casserole|casseroles|curry|curries|soup|soups|rice|pasta|chilli|chili|stock|leftover|"
    r"leftovers|dish|dishes|pie|pies|roast|chicken|meat|joint|batch|bolognese|sauce|beans|"
    r"lentils|porridge|pudding|cake|cakes|bread|bottle|bottles|milk|formula|yoghurt|yogurt|"
    r"cream|muffin|muffins|loaf|loaves)\b")


def the_cold_machine_and_not_the_dish(understood):
    """False when the line is the fridge or freezer being slow rather than a dish to cool."""
    said = " ".join(str(word).lower() for word in ((understood or {}).get("words") or ()))
    if not said:
        said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not (_COLD_MACHINE.search(said) and not _IN_THE_DISH.search(said))


def a_cooling_question_not_a_keeping_one(understood):
    """True unless the line says how long the dish has been in the fridge already."""
    said = " ".join(str(word).lower() for word in ((understood or {}).get("words") or ()))
    if not said:
        said = str((understood or {}).get("text") or "").lower()
    return not _A_PERIOD_OF_TIME.search(said)


# "is it ok to eat bread thats gone a bit hard" is a stale loaf, not a mouldy one, and it was
# told "don't cut the mould off a loaf and eat the rest: bin it" - the bin notice for food that
# was never spoilt. The row keys "ok to eat" and "is it ok", which is how a person asks about a
# dry loaf too, and `bread-stale` has the answer: the water-and-oven trick and the croutons. The
# words that are about a dry loaf only stand this row down; say mould, spots, fluff or a smell and
# it is mouldy bread again, whatever else the line says.
_DRY_LOAF = re.compile(r"\b(?:hard|hardened|dry|dried|stale|stalish|tough|crusty|brittle)\b")
_BREAD_SPOILT = re.compile(r"\b(?:mould|mouldy|mold|moldy|green|blue|furry|fuzz|fluff|spores|"
                           r"spots|speckled|specked|smell|smells|smelly|smelt|slimy|damp)\b")

# "how do i stop my bread going stale" is the keeping question, and `_bread_sliced` answers it
# with the cut face, the paper bag and the freezer. The stale row now keys "going stale" too, so
# it took the prevention lines and told a person with a fresh loaf how to revive a stale one: a
# line that asks how to stop the drying is not a line about a loaf that has dried.
_HOW_TO_KEEP_IT_FRESH = re.compile(
    r"\b(?:how do i stop|how to stop|how do i keep|how to keep|how can i keep|how can you keep"
    r"|stop it going|stop them going|prevent|keep it fresh|keep them fresh|keep bread|keep a loaf"
    r"|make it last|make bread last|last longer|stay fresh|keep fresh|fresh for longer)\b")


def _not_just_a_hard_loaf(understood):
    """False for a loaf that is dry or hard and says nothing about being spoilt."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _DRY_LOAF.search(said):
        return True
    return bool(_BREAD_SPOILT.search(said))


def _not_how_to_keep_it_fresh(understood):
    """False when the line asks how to stop a loaf going stale, not what to do with a stale one."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not _HOW_TO_KEEP_IT_FRESH.search(said)


ENTRIES = [
    # "Should I put warm food in the fridge" was answered with "photograph the inside of the
    # fridge, the shop owes you a repair": the food-spoiled row keys the word "warm" for the
    # food that went warm while the appliance was off, and warmth in front of the fridge is a
    # different question - may I put it in yet. This row answers that one, so the other row
    # keeps its own.
    entry("cool-before-fridge",
          (("warm", "warmish", "hot", "still warm", "lukewarm", "cool", "cooled", "cooling",
            "room temperature", "steaming", "left to cool", "leftover", "leftovers", "stew",
            "curry", "soup", "rice", "chilli", "casserole", "pasta", "meat", "chicken", "food"),
           ("fridge", "refrigerator", "put it in", "put them in", "put in the fridge",
            "put it in the fridge", "in the fridge", "store", "keep it", "put away",
            # the same job with no fridge in the line: "how do i cool a pot of stew quickly"
            # was answered with the washing-up card and "how do i cool soup quickly" with a
            # hedge. The sink of cold water is the answer to both.
            "how do i cool", "how to cool", "cool it quickly", "cool them quickly",
            "cool down quickly", "quickest way to cool", "fastest way to cool",
            "cool quickly", "cool it down")),
          _cool_before_fridge,
          # a dish that has been in the fridge a week is the keeping rows' question
          # two stand-downs, and the second is the machine: see the_cold_machine_and_not_the_dish
          guard=lambda understood: (a_cooling_question_not_a_keeping_one(understood)
                                     and the_cold_machine_and_not_the_dish(understood)),
          bias=1,
          # the freezer, the oven and the keeping-days questions are their own rows, and the
          # appliance that has stopped being cold is the fault row's.
          avoid=("freezer", "freeze", "frozen", "defrost", "refreeze", "reheat", "oven",
                 "microwave", "how long", "how many", "keeps", "last", "lasts",
                 # how long it keeps is the keeping table's row, and "how do i store leftovers"
                 # got the cooling answer on the key's own word "store".
                 "how do i store", "how to store", "how should i store", "storing", "storage",
                 "keep for", "keeps for", "how long do leftovers keep",
                 # A line that asks what to cook is a meal question, not a cooling one: "i have
          # chicken in the fridge what can i cook" was answered with "spread it out in a
          # shallow tub so it cools faster". The cut-and-the-heat row answers it.
          "what can i cook", "what can i make", "what shall i cook", "what shall i make",
          "what to cook", "what to make", "what can i do with", "meal ideas", "dinner ideas",
          # who pays for food that went warm is the ruined-food letter, not a cooling
                 # method: "my fridge broke and all the food is ruined can i claim" was answered
                 # with "let it cool on the worktop".
                 "claim", "claims", "refund", "money back", "compensat", "who pays",
                 "insurance", "ruined", "wasted", "spoiled", "spoilt",
                 # the fridge itself being warm is the fault row's question, not this one
                 "go warm", "goes warm", "getting warm", "gets warm",
                 # a fridge that is warm, cold, cooling or not is the appliance fault's, and
                 # "my fridge stopped cooling" was answered with "let it cool on the worktop":
                 # the key's bare "fridge" and the word "cooling" are what reached it.
                 "fridge is warm", "fridge is cold", "fridge feels warm", "fridge feels cold",
                 "partially warm", "slightly warm", "half warm", "barely cold",
                 "fridge too warm", "fridge is not cold", "fridge isnt cold",
                 "stopped cooling", "not cooling", "stopped getting cold", "not getting cold",
                 "temperature", "thermometer", "fridge smells", "warm in the fridge",
                 "not cold", "isn't cold", "isnt cold", "stopped working", "power cut",
                 "power went off", "thermometer", "drinks", "beer", "wine",
                 "when i take it out", "out of the fridge",
                 # is it still safe to eat afterwards is the out-of-the-fridge table's, and
                 # "can i eat food that was left out all night" was being answered here.
                 # a day in the line is the keeping question, not the cooling one: "can i
                 # leave rice in the fridge for 2 days" was told to spread it in a shallow tray.
                 "day", "days", "tomorrow", "next day",
                 # and so is "how long will it keep" asked as a follow-up about raw chicken,
                 # which reached this row on "fridge" and was told to spread it in a shallow tub
                 "how long", "keeps", "keeping", "will it keep", "does it keep", "raw",
                 # a phone that went in the bath is dried in rice and comes out, and the same
                 # for a camera or a watch: the rice is the tool, not the thing being cooled
                 "phone", "phones", "mobile", "iphone", "camera", "watch", "tablet", "laptop",
                 "airpods", "headphones", "keyboard", "remote", "sim", "battery", "charger",
                 "wont turn on", "wont turn off", "wont charge", "wont switch on", "wet",
                 "all night", "overnight", "still ok", "still okay", "still safe",
                 "still good", "still fine", "safe to eat", "can i eat it", "can i eat that",
                 "can i eat them", "is it ok to eat", "do i have to bin", "throw it away",
                 # the appliance being warm however it is said
                 "too warm", "warm fridge", "fridge is too", "fridge so warm",
                 # a room, a flat, a person, a burn and a hot drink are cooled by other rows and
                 # none of them wants a pot on the worktop: "how do i cool my flat in summer",
                 # "how do i cool a burn" and "how do i cool a baby down" all read "cool".
                 "flat", "room", "rooms", "house", "bedroom", "the heat", "sun", "sunburn",
                 "burn", "burnt", "scald", "fever", "temperature of", "baby", "babies", "child",
                 "toddler", "after a run", "after exercise", "after a workout", "gym", "run",
                 "body", "drink", "tea", "coffee", "wash", "washing up", "clean the pot")),
    # The same question for every food that is not rice, chicken or pasta, which have their own
    # rows: the reply reads which food the line names and gives that food's rule.
    entry("food-left-out",
          (("rice", "pizza", "milk", "cream", "yoghurt", "yogurt", "soup", "stew", "turkey",
            "chicken", "pasta", "potato salad", "mayonnaise", "mayo", "butter", "cheese",
            "bread", "cake", "curry", "gravy", "sausages", "eggs", "quiche", "fish", "ham",
            "bacon", "food", "leftovers", "leftover", "risotto", "pie", "chilli", "lasagne",
            # the meat word, and the cuts said instead of the animal, so "how long can meat sit
            # out" and "i left the steak out" reach the table rather than the desk
            "meat", "steak", "steaks", "chops", "mince", "burger", "burgers", "meatballs",
            "gammon", "duck", "joint",
            # the ordinary things from the keep list and the soft cheeses, so "i left the crisps
            # out" and "i left the brie out" reach the table at all rather than a shrug
            "crisps", "biscuits", "chocolate", "banana", "apples", "orange", "honey", "cereal",
            "peas", "beans", "sweetcorn", "potatoes",
            "flour", "jam", "marmalade", "chutney", "loaf", "fruit", "brie", "camembert",
            "mozzarella", "feta", "stilton", "cheddar", "parmesan", "halloumi", "paneer",
            # a takeaway left out overnight is this row's own question, and no other food word
            # is in "is it ok to leave a takeaway out overnight", so without these the line is
            # left to the shrug. "takeaway" is a food here, never an idiom.
            "takeaway", "takeaways", "take out food", "chinese", "kebab", "curry house",
            "mascarpone", "ricotta",
            "sandwich", "sandwiches", "wrap", "wraps", "coleslaw", "sushi", "prawn", "prawns",
            "tofu", "sauce", "formula", "baby bottle", "bottle of milk"),
          LEFT_OUT_ASK),
          _left_out,
          # one point, and it is the one this file's own additions cost: a key word earns a
          # point when it names only one row, and "chicken" now names this row, the car row and
          # the marinade row as well, so "i left the chicken on the side for an hour" scored
          # just under the side-dish row and was answered with roast potatoes. The leaving rule
          # is what this row is, so it holds its place by a word.
          bias=1,
          # what you do with it once it is in the fridge is another question: reheating, freezing
          # and how many days it keeps all have their own rows.
          # "fridge" on its own is not here: the key names "out of the fridge" - which is how a
          # person says the opposite of keeping it - and one word in both lists made that phrase
          # unreachable, so "milk left out of the fridge overnight" was answered by the weekly
          # shop card. Keeping it in the fridge, and how long it keeps there, are still turned
          # away by "in the fridge" and "how many days".
          # What is served beside the food is the pair row's question, however the line says it:
          # "what goes on the side with steak" reads as a steak that was left on the side, and was
          # told to bin it. Only the phrases that ask for the plate are listed - "on the side" on
          # its own is where the food was left, which is this row's own line.
          avoid=("goes with", "go with", "going with", "goes on the side", "goes nicely",
                 "what side", "which side", "side dish", "side dishes", "sides with",
                 "serve with", "serving with", "to serve with", "to go with", "alongside",
                 "reheat", "reheating", "warm it up", "warm up", "in the fridge",
                 "how many days", "keep for", "recipe", "how do i",
                 "how to make", "make a", "order", "delivery", "dough", "toppings", "defrost",
                 # a soak is a step in a recipe, not a night on the side: "do i need to soak
                 # sticky rice overnight" is a cooking question, and the words "rice" and
                 # "overnight" were between them telling the person to bin it. The soak words
                 # are not in this list, because a line can be both: the guard below keeps the
                 # row for "i soaked the beans overnight and left them out in the kitchen".
                 # "rinse" is deliberately not here: rinsing is offered as the rescue in
                 # "i left the rice out is it ok to rinse it", which is the bin-it question.
                 # "can i still cook it" is not a recipe question: when the line also says the
                 # bird was left out, "cook it" was the one word that stood this row down and
                 # sent "i left the chicken out all nite, can i still cook it" to the leftovers
                 # card. Cooking it is exactly what the person is asking about being allowed
                 # to do, so the recipe words above ("recipe", "how do i", "how long to cook")
                 # carry that exclusion on their own.
                 # "out" on its own is a word in a hundred lines about how something cooked:
                 # "my rice comes out soggy every time", "my chicken comes out dry", "why does my
                 # bread come out crumbly" all have a food word and an "out", and the cooking card
                 # they belong to was losing to this one. The idioms that carry a bare "out" go
                 # here, so the two words still catch "i left the milk out" - where a word always
                 # sits between them - without swallowing the lines about the way food turned out.
                 # "come to room temperature" is an instruction in a recipe, not a question about
                 # something being left out: "should i let my steak come to room temperature" was
                 # told to bin a steak left out for two hours, when the person had not left it out
                 # at all. The phrases are the instruction, never the bare "before cooking", so
                 # "i left the chicken out overnight before cooking" stays a leave-out line.
                 "come to room temperature", "come up to room temperature",
                 "to room temperature before", "room temperature before",
                 "let it come to", "bring it to room temperature", "get it to room temperature",
                 "comes out", "come out", "came out", "coming out", "turned out", "turns out",
                 "turning out", "works out", "worked out", "figure out", "find out", "check out",
                 "point out", "sort out",
                 # "she keeps spitting the food out" is a baby refusing a meal, not a meal that
                 # has been sitting about: the mouth, not the clock, is the question.
                 "spits it out", "spitting it out", "spits the food out", "spitting the food out",
                 "spits food out", "spitting food out", "spits his food out",
                 "spits her food out", "spat the food out", "spat it out",
                 # "went out" and "going out" are NOT here on their own: the leftovers are
                 # usually told with the outing as the circumstance, which is exactly the line
                 # this row exists for. "i left the curry out and went out for the day" and "my
                 # partner went out leaving the milk on the side" both became an acknowledgement
                 # when the bare verb was named, and the food-safety answer is the one that
                 # matters there. The night on the side is a phrase, so the phrases are what is
                 # named here.
                 # A night at a restaurant is the circumstance of the leftover line, not the
                 # question: "we went out for dinner and left the food on the table" is asking
                 # what to do with the food, and every one of these phrases sits inside the
                 # sentence that asks it, so each one stood the row down for the line it is
                 # written for. What is left names the evening itself ("night out", "meal out",
                 # "out for a drink") or the person who did it ("took me out").
                 "night out", "meal out", "out for drinks", "out for a drink",
                 "took me out", "taking me out", "took us out",
                 # "eat out" and "take out the" are the verb, but "takeaway" itself is a food
                 # and sits in the key above: only the verb phrase stands the row down
                 "eat out", "eating out", "take out the", "ordered from",
                 # a tooth is not a food however the line names milk: "my childs milk tooth fell
                 # out" reached this row on "milk" and "out" and got a storage answer.
                 "tooth", "teeth", "milk tooth", "fell out", "wobbly",
                 # neither "left" nor "out" is about a night on the side in these lines
                 "out of milk", "out of bread", "out of butter", "out of eggs", "out of cheese",
                 "run out", "ran out", "running out", "we are out", "weve run", "run out of",
                 "shopping list", "need to buy", "need to get", "forgot to buy",
                 "at home", "at work", "in the car", "on the train", "in the office",
                 "in the oven", "in the pan", "on the hob cooking", "my lunch at",
                 "left my job", "left my husband", "left my partner", "left the country",
                 "left school", "left it too late", "left in the tin", "left the lid",
                 # "left over" is what is in the fridge for tomorrow, not what sat out. The
                 # noun is not on this list: "there are leftovers left out overnight" says in
                 # the same breath where they were, and it must still get the leaving rule.
                 "left over",
                 # a marinade is meat in the fridge on purpose, and its own row answers it
                 "marinate", "marinade", "marinating", "marinated",
                 "left on", "left the oven", "left the light", "left it running",
                 # a date that has gone by is a different question with its own answers
                 "out of date", "use by", "best before", "gone off", "gone bad", "expired",
                 "went off", "smells off", "how long does it last", "past its date",
                 # and so is why chocolate goes white, which is the fat coming to the surface
                 "went white", "white", "bloom", "bloomed", "bloomy", "grey", "greyed",
                 "turned pale",
                 # a mark on something you clean is a stain question, not a night on the side:
                 # "red wine out of a cream carpet" keyed this row on "cream" and the bare "out",
                 # and was told a whole night on the table is a bin job. Only the things that get
                 # cleaned are listed - a short word with a stain's name one slip away ("sofa" and
                 # "soft", "spilt" and "spelt", "stain" and "strain") reads the person's own word
                 # as a misspelling and stands the food answer down for a real food line.
                 "carpet", "carpets", "rug", "upholstery", "curtain", "curtains", "mattress",
                 "shirt", "shirts", "jumper", "jumpers", "blouse", "trousers", "fabric",
                 "sleeve", "sleeves", "cushion", "cushions", "red wine", "white wine",
                 "coffee on", "on my shirt", "on the carpet", "out of the carpet",
                 # "sofa" on its own would read "soft" as a misspelling of it, and the two-word
                 # phrases are skipped by the slip test, so the sofa is named in phrases
                 "the sofa", "my sofa", "cream sofa", "on the sofa", "out of the sofa",
                 # asking someone out is not a shelf life, and neither is losing your nerve:
                 # "i want to ask out my crush but i keep chickening out" has "chicken" and "out"
                 # in it and no food at all. The bare "chicken out" is read in `_left_out` instead
                 # of here, because naming it here stood the row down for "i left the chicken
                 # out for a few hours" - the food question this row is for.
                 "ask out", "asking out", "asked out", "ask her out", "ask him out",
                 "ask them out", "ask someone out", "ask a girl out", "ask a guy out",
                 "crush",
                 # the chicken-out idiom is keyed with the little word after it: the forms of
                 # "chickened" and "chickening" both reduce to "chicken", and the words of
                 # "chicken out" sit side by side in "left the chicken out on the counter", so
                 # either spelling on its own stood this row down for the food line it is here
                 # to answer (and the leftovers card answered a food-safety question).
                 "chickened out of", "chickening out of", "chicken out of",
                 "chickened out about", "chickening out about",
                 # a line that does not say what they chickened out of, caught by the person in
                 # front of it: the food line says "i left the chicken out", which is not the
                 # same three words in a row, so this reaches the idiom and nothing else.
                 "i chickened out", "i chicken out", "i chickening out", "i keep chickening",
                 "i always chicken", "i usually chicken", "ive chickened out", "i've chickened",
                 "on a date", "first date"),
          # and a soak is only a recipe step while nothing says the food has been out: one line
          # can say both, and the leaving is the question that matters then. The freezer half is
          # `_not_a_freezer_keeping_question` below.
          guard=soak_but_not_left_out_or_in_the_freezer),
    # The same rule for a journey, which is the case the main row cannot take: "in the car" is on
    # its avoid list because "i left my purse in the car" is not a food question, so "milk left in
    # the car" fell through to the white-sauce recipe. The two halves say the whole thing - a
    # food that spoils, and a warm place with no fridge - and the answer is the rule plus the one
    # thing that changes it, which is how hot the day was.
    entry("food-in-the-car",
          (("milk", "cream", "yoghurt", "yogurt", "formula", "bottle", "cheese", "butter",
            "chicken", "turkey", "ham", "sausages", "sausage", "bacon", "sandwich",
            "sandwiches", "wrap", "prawns", "fish", "mince", "steak",
            "eggs", "mayonnaise", "mayo", "cake", "chocolate",
            # the whole shop, and food with no name: "how long can food sit in a hot car" and
            # "my shopping got warm in the car" were a car-overheating answer and a meal idea,
            # because the row only knew the named foods
            # a cool bag and a cool box are not here: the picnic row keys on them and answers
            # "how do i keep food cold in a cool bag" with the ice packs, which is the right
            # answer for a person who already has one (alert-frog, #5640)
            "food", "foods", "shopping", "groceries",
            "leftovers", "lunch", "snacks", "takeaway"),
           ("in the car", "in my car", "in the boot", "back seat", "on the back seat", "car boot",
            "in a hot car", "hot car", "warm car", "got warm", "went warm",
            "keep it cold", "keep food cold", "keep it cool", "keep cold", "cold in the car",
            "on the drive", "walked home", "on the way home",
            # not "in the sun": "i left the milk out in the sun" names no vehicle, and the
            # table rule is the right answer for it - the reply here would have called it a car.
            "in the van", "picnic")),
          _in_the_car,
          # A cool bag and a cool box are the picnic row's question and it answers them better:
          # "how do i keep food cold in a cool bag" wants the ice packs, not the two-hour rule,
          # because the person has already brought the cold bag and wants to use it (alert-frog,
          # #5640). The keeping words above would otherwise read that line as food with no fridge.
          avoid=("cool bag", "cool box", "cooler bag", "cooler box", "cool bag", "ice pack",
                 "ice packs", "ice blocks", "freezer blocks", "picnic", "picnic box",
                 # "how does a fridge keep food cold" is the fridge working, not food left in a
                 # car: "keep food cold" is in the second half of this key and answered it
                 "fridge", "refrigerator", "freezer", "how does", "how do fridges", "how it works",
                 "why does a fridge", "compressor"),
          # and the line has to be about something left there: "i ate a sandwich in the car" is
          # the place it was eaten, and a third part of the key answered it with the two-hour
          # rule. A third part is not a thing this table can be asked for - one word of it stood
          # for the whole entry - so the leaving verb is on the ask list, which must also match.
          ask=("left", "leave", "leaves", "leaving", "forgot", "sat", "sitting", "kept",
               "stored", "packed", "bought", "brought",
               # "how long can food sit in a hot car" and "how do i keep food cold in the car"
               # ask the same rule without a leaving verb
               "how long", "how many hours", "still safe", "safe to eat",
               "got", "went", "get", "keep", "keeping", "cold", "warm"),
          bias=3,
          # a dog or a cat shut in the car is the animal's own card; "can i leave my dog in the
          # car while i shop" was the two-hour food rule, because "shop" is the shopping word
          guard=lambda understood: not any(
              word in (understood.get("clean") or "").lower().split() for word in
              ("dog", "dogs", "puppy", "pup", "puppies", "cat", "cats", "kitten", "kittens",
               "pet", "pets"))),
    # And the line the leaving words would otherwise steal: "i want to marinate chicken overnight"
    # is not chicken that sat on the counter, it is chicken going into the fridge in a bag, and
    # the main row answered it with the bin notice. Both halves of the meaning are keyed here, so
    # the row is about a marinade and a meat, and nothing else matches it.
    entry("marinate-the-meat",
          (("marinate", "marinade", "marinating", "marinated", "marinade for", "marinade in"),
           ("chicken", "meat", "steak", "lamb", "pork", "fish", "salmon", "tofu", "beef",
            "prawns", "turkey", "lamb chops", "chops")),
          _marinate,
          bias=8),

    # Which food to eat first is the one question about the fridge this domain did not answer,
    # and "what goes off first in the fridge" was answered by the food-waste row with "write the
    # week's four meals down before you shop". It is the same idea as the shelf-life rows here -
    # the answer depends on the food, not the words - so it lives beside them.
    entry("fridge-order",
          (("fridge", "fridge freezer", "fridges", "shelf", "shelves", "drawer", "crisper"),
           ("what goes off first", "goes off first",
            "go off first", "what should i eat first", "what should i use first",
            "what to eat first", "what to use first", "eat first", "use first", "use up first",
            "what goes where", "where in the fridge", "fridge order", "which shelf",
            "top shelf", "bottom shelf", "middle shelf", "salad drawer", "crisper",
            "how should i organise the fridge", "how do i organise my fridge",
            "how do i organise the fridge", "how do i stack the fridge",
            "what goes on which shelf"),),
          "Eat in date order first, and after that the food that is on borrowed time: fresh fish "
          "and mince within a day or two, then soft fruit, berries and salad leaves, then milk, "
          "yoghurt and cream, then hard cheese, butter and cooked leftovers. Where it sits "
          "matters as much as the order - cooked and ready-to-eat food on the top shelves, raw "
          "meat and fish on the bottom shelf in a box so nothing drips, and vegetables in the "
          "drawer. The door is the warmest part, so keep milk out of it, and the top of the door "
          "is fine for butter and condiments.",
          # what to do with what has already gone off is the shelf-life rows' question, and a
          # freezer or a shop's waste is another answer
          avoid=("gone off", "is it ok", "safe to eat", "still ok", "freezer", "freeze",
                 "frozen", "waste", "throw", "bin", "buy too much", "how long does",
                 "how long can i keep", "use by", "best before", "smell"),
          bias=2),

    # The state of the food, not the calendar. A person holding it wants one verdict and what to
    # do with it, and the two states are different questions, so the reply reads them apart:
    # slimy, sour or mouldy is the bin, and soft, wrinkly, dry or limp is water loss and still
    # dinner. Every row near this one answered the other question - "can i eat grapes that are
    # wrinkly" got what grape skins are good for, "can i eat a banana thats gone soft" got a
    # banana's calories, "my spinach has gone slimy and smells a bit" got the five days it keeps,
    # and "my carrots have gone soft are they ok" got how long carrots keep.
    entry("past-its-best",
          (PAST_IT_PRODUCE, PAST_IT_STATE, PAST_IT_ASK),
          _past_its_best,
          # The state is the question: "can i eat raw carrot" names a food and an ask and says
          # nothing about the food having changed, so the two other parts are not enough to make
          # it this row's line.
          guard=_says_the_state,
          bias=3,
          # Bread has its own stale row (`bread-stale`, which says the oven trick and the
          # breadcrumbs) and its own mould row, and the two questions there are worth keeping
          # apart: a dry loaf is dinner and a green one is the bin. Herbs in a supermarket pot
          # have a plant row, and a mushroom that is a bit slimy has an answer of its own.
          avoid=("mouldy", "mould", "mold", "green potato", "sprouting", "sprouted", "sprouts",
                 "bread", "loaf", "baguette", "rolls", "toast", "croutons",
                 "basil", "parsley", "mint", "coriander", "cilantro", "chives", "thyme",
                 "rosemary", "herb", "herbs", "houseplant",
                 # keeping and storage are their own rows: "how long do carrots keep" is not
                 # "are these carrots still all right"
                 "keep for", "keeps for", "how long do", "how long does", "how long will",
                 "store", "storing", "storage", "keep them", "keep it", "last", "lasts",
                 # a plant in the garden going yellow is the garden rows' question, and this
                 # row keys "gone yellow" for the leaves in a bag
                 "garden", "plant", "plants", "tree", "grow", "growing", "fertiliser",
                 "compost", "water them", "water it", "leaves on", "pot it", "repot",
                 # keeping it from going over is the keeping rows' question, and the state
                 # words are exactly its words: "how do i keep a bag of salad from going slimy"
                 # was told to bin the bag. Phrases only, because an avoid word is read in its
                 # loose forms, so a bare "slimy" would stand this row down on its own lines.
                 "from going slimy", "from going soft", "from going brown", "from going limp",
                 "how do i keep", "how to keep", "how can i keep", "keep a bag", "keep them fresh",
                 "keep it fresh", "stop it going", "stop them going", "prevent", "last longer",
                 "stay fresh", "keep fresh", "make it last", "keep them from", "keep it from",
                 # and the same question with no keeping in it: "why does lettuce go slimy" and
                 # "why do cucumbers go soft" ask what happens to the food, not about the food
                 # in their hand, and the food rows answer them
                 "why does", "why do", "what makes", "what causes",
                 # a cooking smell is the kitchen's, not the food's: "my kitchen smells of
                 # cabbage" wants the window and the lemon, not the bin
                 "kitchen smells", "kitchen smell", "smells of", "smell of", "smells like",
                 "smell like", "stinks of", "stink of", "the house smells", "the fridge smells",
                 # a taste is the cook's to fix, not a spoilage verdict: "my tomato sauce is too
                 # sour" is asking for the sugar and the butter
                 "too sour", "too sweet", "too salty", "too bitter", "a bit sour",
                 "sauce", "soup", "stew", "curry", "casserole", "dough", "batter", "cake",
                 "recipe", "recipes", "meal idea", "meal ideas",
                 # A limp or wilted leaf already has a good short answer - the iced water that
                 # brings it back crisp - and that row says it better than this one can, so a
                 # leaf described as limp or wilted keeps its line. What this row adds is the
                 # leaf that has changed colour, which had no answer at all.
                 "limp", "limper", "wilted", "wilting", "wilt", "floppy leaf", "floppy leaves",
                 # reviving limp leaves and using a bag up are the cooking rows' questions, and
                 # they answer them with the iced water and the pan: "how do i revive wilted
                 # spinach", "i have a bag of spinach going limp what can i do with it"
                 "revive", "reviving", "bring it back", "bring them back", "crisp it up",
                 "crisp them up", "make it crisp", "make them crisp", "what can i do with",
                 "what to do with", "use it up", "use them up", "use up",
                 # and the follow-up about the soak is the other row's short answer ("10
                 # minutes"), which reads the card it gave
                 "how long", "how many minutes", "soak", "soaking", "ice water", "iced water")),
]
