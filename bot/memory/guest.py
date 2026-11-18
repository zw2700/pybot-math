"""What a guest will not eat, and the answer it changes.

A line such as "and she hates mushrooms" is not a new subject: it is one more constraint
on the dinner we were already planning. The memory store keeps it against the person, and
this module revises the suggestion the bot has just given so the reply is concrete rather
than a nod. The same shape serves "he can't stand olives" and "she isn't keen on fish".

The knowledge base is still the authority on food; this module only needs to tell a food
apart from the other things a person might hate ("she hates her job"). The words come from
the understanding lane's cooking vocabulary and from the pantry table, so a new ingredient
there is recognised here without a second list to maintain.
"""
import re

WORD = re.compile(r"[a-z0-9']+")
# Where the food phrase ends. "but" and "so" usually start the next thing on the person's
# mind ("she hates mushrooms but loves the sauce"), and punctuation ends the item.
STOP = re.compile(r"\b(?:but|so|because|though|although|which|when|if|and then)\b|[,.;!?]")
# The ways people say someone will not eat a thing. A diet ("she doesnt eat meat") is read
# by facts.py, not here: this is about the one ingredient that would be left on the plate.
DISLIKE = re.compile(
    # First person as well as third: "i dont like mushrooms" and "i dislike mushrooms" are the
    # person's own taste exactly as "she hates mushrooms" is her own, and the pattern used to
    # read only the third person ("doesn't like") and the harsh verbs, so a dislike said the
    # ordinary way was not a dislike at all - it was said straight back to the person ("i dont
    # like water" -> "Noted: you don't like water.") while "i hate water" got an answer. The
    # auxiliaries are spelled out rather than "don't" alone, because the reading engine also
    # hands over the expanded "do not" and the apostrophe-less "dont" people actually type.
    r"\b(?:hates?|dislikes?|can'?t stand|cannot stand|"
    # "i dont want pasta tonight" is the same taste as "i dont like pasta", and nothing read it:
    # the store kept the taste with no answer (`how`: "no") and the line was said straight back
    # ("Noted: you don't want pasta tonight"). The verb is the one people use at a table, and the
    # food test below is what keeps it to food - "i dont want a dog" is not a dislike of dog.
    r"(?:do|does|did)(?:n'?t| not) (?:like|fancy|enjoy|want|wants?)|"
    # The words people put in the middle: "not a BIG fan of", "not THAT keen on", "isn't
    # REALLY my thing", "not much of a fan of". The plain forms were read and the qualified
    # ones were not, so the line fell to the greeting pool and the fish recipe came back.
    r"(?:isn'?t|aren'?t|is not|are not|amn'?t) (?:(?:that|really|very|so) )?(?:much of )?"
    r"(?:a |the )?(?:(?:big|huge|massive|great) )?"
    r"(?:fan of|keen on|fond of|fussed on|my thing|my kind of thing)|"
    r"not (?:(?:that|really|very|so|all that) )?(?:much of )?(?:a |the )?"
    r"(?:(?:big|huge|massive|great) )?"
    r"(?:fan of|keen on|fond of|fussed on|my thing|my kind of thing)|avoids?|avoiding)\s+"
    r"(?:the\s+|any\s+)?(?P<food>[a-z][a-z' -]{1,40})", re.I)
# The food comes first in this one: "fish isn't really my thing", "pork isnt my kind of thing".
# The pattern above wants the food after the phrase, so the food-first way of saying the same
# thing could never match it however well the words in the middle were spelled out.
NOT_MY_THING = re.compile(
    r"\b(?P<food>[a-z][a-z' -]{1,30}?)\s+(?:isn'?t|is not|aren'?t|are not)\s+"
    r"(?:(?:really|that|exactly|quite)\s+)?(?:my|our)\s+"
    r"(?:(?:kind|sort)\s+of\s+|cup\s+of\s+tea|thing)", re.I)
# "no curry for me", "no fish for me thanks", "no pasta tonight": the food is named first and the
# refusal comes after it, which none of the patterns above can match. The tail has to be there, so
# "not sure if i like pasta" is not read as a dislike of pasta.
NO_FOR_ME = re.compile(
    r"\b(?:no|not|none of the)\s+(?:any\s+|more\s+|the\s+)?(?P<food>[a-z][a-z' -]{1,40}?)"
    r"\s+(?:for me|thanks|thank you|please|today|tonight|tomorrow|later)\b", re.I)
# "not pizza or curry", "no pizza and chips": a short line that names two foods and turns them
# down is a constraint on what was just suggested. Nothing read it, so after "what shall i cook
# tonight" the answer to "not pizza or curry" was the pizza-sizing card. Two foods are required,
# because "no milk" on its own is as likely to be a fact about the fridge as a thing to avoid.
NO_FOOD_ALONE = re.compile(
    r"^\s*(?:no|not|none(?=[\s,])|nothing with|anything but)\s+"
    r"(?P<food>[a-z][a-z' ,-]{3,60}?\s+(?:or|and|,)\s+[a-z][a-z' ,-]{1,40})\s*$", re.I)
# A phrase that names no food: "she hates cooking" is about the job of it, not an ingredient.
GENERIC = frozenset("""
cooking cook food dinner tea lunch breakfast eating eat meal meals work job school housework
cleaning shopping mornings mondays tuesdays wednesdays thursdays fridays saturdays sundays
winter summer rain traffic flying travel travelling exercise sport gym crowds spiders
everything anything nothing it that this them him her
""".split())
PRONOUN = frozenset("her his their my your our its it them him this that these those".split())
# Common foods the two source vocabularies do not spell out. Kept short: the pantry and the
# topic words cover the ingredients people cook with, and a phrase may always be recognised
# from the answer it is answering (see `known` in the store).
EXTRA = frozenset("""
olive feta couscous halloumi paneer quinoa avocado broccoli cauliflower cabbage leek celery
cucumber lettuce peas sweetcorn beetroot aubergine courgette pumpkin berries banana apple
orange lemon lime grape melon peach pear plum mango pineapple strawberry blueberry raspberry
walnut almond cashew peanut hazelnut pistachio sesame tofu prawn salmon tuna cod haddock
mackerel sardine anchovy sausage bacon ham chorizo steak mince turkey duck lamb pork beef
chicken fish egg eggs cheese butter milk cream yoghurt bread pasta rice potato tomato onion
garlic carrot pepper spinach mushroom lentil chickpea bean noodle soup curry lasagne pizza
cake chocolate sugar salt
""".split())

_KNOWN = None


def _fold(word):
    """A word with its plural undone, so mushrooms/mushroom are one food."""
    word = str(word).lower().strip(".,!?;:'\"")
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("oes"):
        return word[:-2]
    if len(word) > 3 and word.endswith("es") and word[-3] in "sxzh":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _known():
    """Every food word the rest of the bot already knows, built once."""
    global _KNOWN
    if _KNOWN is not None:
        return _KNOWN
    words = set(EXTRA)
    try:
        from ..understanding.topics import STRONG
        for topic in ("cooking", "food-and-drink"):
            words.update(STRONG.get(topic, "").split())
    except Exception:  # noqa: BLE001 - a vocabulary that cannot load only narrows this module
        pass
    try:
        from ..knowledge import cooking as knowledge
        for name, (aliases, _reply) in knowledge.PANTRY.items():
            words.add(name)
            words.update(aliases)
    except Exception:  # noqa: BLE001 - same: the knowledge base may change shape
        pass
    _KNOWN = {_fold(word) for word in words if word}
    return _KNOWN


# A day after the food is when, not what. "i dont want pasta tonight" was read as the food "pasta
# tonight", which no vocabulary knows, so the dislike went unanswered ("Noted: you don't want
# pasta tonight") while "i dont like pasta" got "Fair enough - no pasta in anything I suggest".
# Only a trailing when is taken off, so "sunday roast" keeps its day and "pasta tonight" is pasta.
_WHEN = re.compile(
    r"(?:\s+(?:(?:this|next|last|on)\s+"
    r"(?:week|weekend|friday|saturday|sunday|monday|tuesday|wednesday|thursday|morning|evening|"
    r"afternoon|night|weekday|birthday|christmas)"
    r"|today|tonight|tomorrow|tomorrow night|now|later|again|then|instead|"
    r"for (?:tea|dinner|lunch|breakfast|supper)|at (?:lunch|dinner|breakfast|tea)|"
    r"any\s?more))+$", re.I)


def _clean(item):
    item = " ".join(str(item or "").strip(" .,!?;:'\"").lower().split())
    item = re.sub(r"^(?:the|any|some|more|all|a|an)\s+", "", item).strip()
    item = re.sub(r"\s+(?:too|either|as well|much|really|actually|at all|though|tho|anyway)$",
                    "", item).strip()
    item = _WHEN.sub("", item).strip(" ,")
    return item


# In a pair, a drink is a thing to leave out even though the vocabulary calls "tea" generic:
# "tea" is also the evening meal, so it is not a food word on its own ("no tea tonight" is a
# night with no dinner), but "i dont want tea or coffee" names two drinks and both belong in
# the promise. "Fair enough - no coffee in anything I suggest" dropped half of what was said.
DRINK_PAIR = frozenset("""
tea coffee beer wine lager cider ale stout juice squash cordial water milk lemonade
""".split())


def _one_half(piece):
    """One half of a pair that was turned down: a food, or a drink named as one."""
    if _is_food(piece):
        return True
    words = WORD.findall(piece)
    return bool(words) and all(_fold(word) in DRINK_PAIR for word in words)


def _is_food(item):
    if not item or item in GENERIC:
        return False
    words = WORD.findall(item)
    if not words or words[0] in PRONOUN:
        return False
    known = _known()
    return any(_fold(word) in known for word in words)


def plain(item, a_pair=False):
    """The food itself for a dislike of the user's own, or None when the phrase only contains one.

    `_is_food` is right for editing a suggestion that mentions the food ("mushrooms" in a
    mushroom lasagne) and too loose for a promise about everything the bot suggests: "no noisy
    restaurants", "no cheap wine" and "no mushrooms on pizza" are not foods. A plain phrase has
    only known food words in it; "the texture of tofu" is read as the tofu.
    """
    item = _clean(item)
    item = re.sub(r"^(?:the\s+)?(?:taste|texture|smell|look|sight)\s+of\s+(?:the\s+)?", "",
                  item, flags=re.I).strip()
    # A drink named as one half of a pair is a thing to leave out of the promise too
    # ("i dont want tea or coffee" keeps both); on its own "tea" is also the evening meal.
    if not (_is_food(item) or (a_pair and _one_half(item))) \
            or re.search(r"\b(?:on|with|of|in|at)\b", item, re.I):
        return None
    known = _known()
    if not all(_fold(word) in known for word in WORD.findall(item)):
        return None
    return item


def found(text):
    """[(food, where)] in the line: [("mushrooms", 15)] for "and she hates mushrooms"."""
    if not isinstance(text, str):
        return []
    out = []
    for pattern in (DISLIKE, NOT_MY_THING, NO_FOR_ME, NO_FOOD_ALONE):
        for match in pattern.finditer(text):
            chunk = STOP.split(match.group("food"))[0]
            pieces = [_clean(re.sub(r"^(?:no|not)\s+", "", piece.strip(), flags=re.I))
                      for piece in re.split(r",|\band\b|\bor\b", chunk)]
            pieces = [piece for piece in pieces if piece]
            # Two halves that are both things to eat or drink are the pair form, whichever
            # verb read them: "i dont want tea or coffee" keeps both, and the pair form also
            # has to have two, because "no hot water or heating" is the boiler, not a thing to
            # leave out of dinner - one half is "hot water" and the other is not food at all.
            a_pair = len(pieces) >= 2 and all(_one_half(piece) for piece in pieces)
            if pattern is NO_FOOD_ALONE and not a_pair:
                continue
            for item in pieces:
                if (_is_food(item) or a_pair) and item not in [food for food, _at in out]:
                    out.append((item, match.start("food")))
    return out


# "no mushrooms", "no pasta please": a bare "no" and the food, said as the answer to a suggestion.
# Nobody reads a verb there, so `found` cannot see it, and after "what shall i cook tonight" the
# answer to "no mushrooms" was a card about mushrooms on toast. Only used where a suggestion is on
# the table (see `_a_dislike_told` in the store), because "no milk" on its own is as likely to be
# a fact about the fridge as a thing to avoid.
NO_X_ALONE = re.compile(
    r"^\s*(?:no|not|none of the|nothing with)\s+(?:any\s+|more\s+|the\s+)?"
    r"(?P<food>[a-z][a-z' -]{1,40}?)\s*(?:please|thanks|thank you)?\s*$", re.I)


def turned_down_alone(text):
    """The foods a bare "no mushrooms" names, or [] when the line says anything more."""
    match = NO_X_ALONE.match(" ".join(str(text or "").split()))
    if not match:
        return []
    item = _clean(match.group("food"))
    if not item or re.search(r"\b(?:or|and)\b", item):
        # A pair is `found`'s to read, and "hot water or heating" is a house with no hot water.
        return []
    return [item] if _is_food(item) else []


def _contains(text, food):
    root = _fold(food)
    return any(_fold(word) == root for word in WORD.findall(str(text or "")))


def _without_article(item):
    return re.sub(r"^(?:a|an|the)\s+", "", item.strip(), flags=re.I)


def _split_list(rest):
    """The options in "a curry, a lasagne, or a traybake"."""
    parts = re.split(r",\s*|\s+or\s+", rest)
    items = [re.sub(r"^(?:or|and)\s+", "", part.strip(" .")) for part in parts
             if part.strip(" .")]
    # An option is a short thing on a menu, not half a sentence. "I'd do tomato pasta (20
    # minutes): fry sliced garlic in olive oil for a minute, add a tin of tomatoes..." is a
    # method split by commas, and reading it as a list answered a person who said "no pasta"
    # with "Then the add a tin of tomatoes and simmer 10 minutes while the pasta cooks is out".
    if any(len(WORD.findall(item)) > 5 for item in items):
        return None
    return items


def _kept_phrase(items):
    if len(items) == 1:
        return items[0] + " still works"
    if len(items) == 2:
        return items[0] + " or " + items[1] + " both still work"
    return ", ".join(items[:-1]) + " or " + items[-1] + " all still work"


def revise(reply, foods):
    """The last answer with the disliked food taken out, or None when it does not mention it.

    The reply is edited only where the food is one option in a list ("a curry, a lasagne, or a
    traybake"), because that is where a friend would say "then leave that one out". A single
    recipe that needs it has no alternative to keep, so the caller lets another module answer.
    """
    if not isinstance(reply, str) or not foods:
        return None
    for sentence in re.split(r"(?<=[.!?])\s+", reply.strip()):
        hit = [food for food in foods if _contains(sentence, food)]
        if not hit:
            continue
        head, sep, rest = sentence.partition(": ")
        if not sep:
            continue
        items = _split_list(rest)
        if not items:
            continue
        removed = [item for item in items if any(_contains(item, food) for food in hit)]
        kept = [item for item in items if item not in removed]
        if not removed or not kept:
            continue
        gone = "the " + " and the ".join(_without_article(item) for item in removed)
        gone += " is out" if len(removed) == 1 else " are out"
        return "Then " + gone + " — " + _kept_phrase(kept) + "."
    return None


def left_out(foods):
    """A short reply to a food the user themselves will not eat, with no suggestion to edit."""
    items = list(dict.fromkeys(str(food).strip() for food in foods if str(food).strip()))
    # Two things turned down are joined the way a person says them: "no pasta or rice in anything
    # I suggest", not "no pasta, rice".
    said = " or ".join(items) if len(items) == 2 else ", ".join(items)
    if not said:
        return None
    return "Fair enough — no " + said + " in anything I suggest."
