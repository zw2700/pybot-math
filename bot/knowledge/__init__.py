"""The knowledge base: facts about the world, kept as data. The answers lane owns it.

One module per domain (bot/knowledge/cooking.py, bot/knowledge/travel.py, ...) holds plain data
keyed by meaning (a dish, a city, a symptom), not by how a question is worded. A domain lists
its knowledge as ENTRIES, built with bot.knowledge.lookup.entry(), so the shared matcher in
bot/knowledge/lookup.py can answer every way of asking for it. Answer modules in bot/modules/
find the entry here and compose the reply. The bot cannot read files, so the data lives in .py
files.

Adding a domain is adding one file with ENTRIES; nothing else needs to change.

A domain also says which topics it can answer, so the arbiter knows this is the specialist
for them: `ANSWERS = ("cooking", "food-and-drink")`, the same attribute name a reply module
declares, with the topic ids from bot/understanding/topics.py. bot/modules/answers.py declares
the union as its own ANSWERS, so adding a domain never means editing a list somewhere else.

The shared tables are not domains: bot/knowledge/lookup.py matches keys to lines and
bot/knowledge/units.py converts measures, both used by every domain, so they are kept out
of the registry in _INTERNAL.
"""
import importlib
import pkgutil

# `keeping_cooked` is a table for `cooking.py` to build entries out of, like `cooking_entries`,
# and it declares no ENTRIES of its own: recognised here rather than skipped in each test that
# walks the domains, because a module with no entries is otherwise indistinguishable from a
# domain file whose ENTRIES line a typo removed.
# `crisis_replies` is the card text that bot/modules/safety.py says, lifted out of that module
# so it stays under the publisher's 1 MiB file limit; a dict of replies and no ENTRIES, so it
# is a shared table rather than a domain.
# `home_craft` is the same thing for `home.py`: the rows of its list, called back from the end of
# that file so it stays under the limit, with no ENTRIES of its own.
# `cooking_more` is the same thing for `cooking.py`: the tail of its list, from "how you tell it
# is cooked" to the end of the file, called back from the end of that file so the entries keep
# their order and both files stay under the publisher's 1 MiB limit.
#
# `family_more` is the same thing for `family.py`: the tail of its list, from "the questions a
# parent asks in the first years" to the end of that file, called back from the end of that file
# so the rows keep their order and the file goes back under the publisher's 1 MiB limit.
#
# `bake_faults` is `cooking.py`'s bake-fault dispatcher and its tables, moved out because that
# file reached the uploader's size ceiling. It holds no ENTRIES: the entry that calls it is still
# in `cooking.py`, which imports it back.
#
# `cooking_tables` is the big data of `cooking.py` - the recipes, the pantry, what a food holds,
# the dishes, the keeps - moved out whole for the same reason and imported back at the top of
# `cooking.py`, so every name the rows and the other modules use is still there. Pure data, no
# ENTRIES: it is a table, not a domain.
_INTERNAL = {"lookup", "units", "cooking_entries", "keeping_cooked", "crisis_replies",
             "home_craft", "quantity", "cooking_more", "bake_faults", "family_more",
             "cooking_tables"}

# A domain that declares no ANSWERS still counts for the topic its name stands for; these are
# the names that are not already an id in bot/understanding/topics.py.
TOPIC_ALIASES = {
    "home": "home-and-diy",
    "travel": "geography-and-travel",
    "nature": "nature-and-weather",
    "garden": "garden-and-plants",
    "food": "food-and-drink",
    "food_and_drink": "food-and-drink",
    "maths": "maths-and-numbers",
    "school": "school-and-study",
    "language": "language-and-writing",
}

_cache = {}


def domains():
    """{domain name: module} for every knowledge domain in this package, by name."""
    cached = _cache.get("domains")
    if cached is not None:
        return cached
    found = {}
    for item in pkgutil.iter_modules(__path__):
        if item.name in _INTERNAL:
            continue
        try:
            found[item.name] = importlib.import_module(f"{__name__}.{item.name}")
        except Exception:  # noqa: BLE001 - one broken domain must not hide the others
            continue
    _cache["domains"] = found
    return found


def by_topic(found=None):
    """{domain name: the topic ids its own entries answer}, so one domain can be judged.

    Worked out exactly as topics() does it, one domain at a time. A reader that already has
    an entry in hand uses this to ask whether that entry belongs in a conversation about a
    given topic at all. `found` is domains(), for tests.
    """
    remembered = found is None
    cached = _cache.get("by_topic") if remembered else None
    if cached is not None:
        return cached
    if remembered:
        found = domains()
    out = {}
    for name, module in found.items():
        declared = getattr(module, "ANSWERS", ())
        if isinstance(declared, str):
            declared = (declared,)
        try:
            declared = [str(item).strip().lower() for item in declared if str(item).strip()]
        except TypeError:  # noqa: BLE001 - a domain that declares something odd answers nothing
            declared = []
        if not declared:
            flat = str(name).strip().lower().replace("_", "-")
            declared = [TOPIC_ALIASES.get(flat, flat)]
        out[str(name)] = tuple(sorted(topic for topic in declared if topic))
    if remembered:
        _cache["by_topic"] = out
    return out


def topics(found=None):
    """The topic ids (bot/understanding/topics.py) this knowledge base can answer, sorted.

    A domain's declared ANSWERS wins; otherwise its name stands for one topic, through
    TOPIC_ALIASES when the name is not already an id. So a domain that forgets to declare
    is still routed, and a new domain needs no edit here. `found` is domains(), for tests.
    """
    answered = set()
    for declared in by_topic(found).values():
        answered.update(declared)
    answered.discard("")
    return tuple(sorted(answered))


def _with_one_more_test(guard, extra):
    """A row's guard with one more condition folded in, either side allowed to be missing.

    A guard says whether the row may answer, so two conditions are an `and`: the row answers
    only when both agree it should. The row keeps whatever guard it already had, so this cannot
    take a test away, and a row with none simply takes the new one.
    """
    if guard is None:
        return extra

    def guard_and_extra(understood):
        return bool(guard(understood)) and bool(extra(understood))
    return guard_and_extra


def entries():
    """Every Entry in every domain, in a stable order (cached after the first call).

    Each entry carries the name of the domain it came from, so the matcher can weigh a key
    word by how rare it is inside that domain rather than across the whole knowledge base:
    a new domain then cannot take a point away from an entry somewhere else.
    """
    if "all" not in _cache:
        found = []
        for name, module in sorted(domains().items()):
            # A domain may say when its whole subject is the wrong thing to answer with: the
            # pets cards answer a line about an animal, and stand aside for the person's own
            # routine with it ("i walk the dog every day"), where the animal is what they do it
            # to and the routine is the news. The hook is the same test an entry's `guard` is,
            # asked once for the domain rather than written into two hundred entries.
            stands_aside = getattr(module, "STANDS_ASIDE", None)
            # And it may name one more condition for a row that already has a guard. An entry
            # takes a single `guard=`, so a second condition written beside the first does not
            # compile - which takes every answer in the file with it - and writing it into the
            # same lambda means editing a line another change is also editing. A domain
            # declares the extra test by row id instead, and it is folded in here, once.
            guard_folds = getattr(module, "GUARD_FOLDS", None) or {}
            for item in getattr(module, "ENTRIES", ()) or ():
                try:
                    item.domain = name
                    if stands_aside is not None and getattr(item, "guard", None) is None:
                        item.guard = stands_aside
                    extra = guard_folds.get(getattr(item, "id", ""))
                    if extra is not None:
                        item.guard = _with_one_more_test(item.guard, extra)
                except AttributeError:      # an entry from somewhere else keeps ""
                    pass
                found.append(item)
        _cache["all"] = found
    return _cache["all"]
