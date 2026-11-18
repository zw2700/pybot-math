"""The number of children, counted from the children the chat already holds.

No single line has to state a number for the count to be known. `my son is 6` and `and my
daughter is 9` are two children with their ages, and the ask after them, `how many children do i
have`, was answered "You've mentioned your son - how many have you got altogether?": the store
reads a count off one line, and a line about one child gives one child.

So the count is read off what the store holds: each child relation the person named is one child,
a child named on their own is one however they came in (`my son jack is 6` and `my son sam is 9`
are two), and the same child said twice is still one. A child who belongs to somebody else is not
counted, and one child keeps the honest ask for a number.

Only the ask is answered: `reply_for` returns None on every other line, and on a chat that
already has a number, because the store answers that one.
"""
import random
import re

# The relations that are somebody's child. Taken from the store's own words for the same thing,
# so a relation the store counts as a child is counted here too.
CHILD_RELATIONS = ("son", "daughter", "child", "kid", "baby", "twin", "boy", "girl", "stepson",
                   "stepdaughter", "teenager", "lad", "lass", "sons", "daughters", "children",
                   "kids", "boys", "girls", "twins", "lads", "lasses")

# "how many kids do i have", "how many children have we got", "how many of my kids", "how many
# kids" as a follow-up: the ask for their own count.
THE_ASK = re.compile(
    r"\bhow\s+many\b(?P<rest>[^.?!]*)", re.I)
# The words that make the ask about the person's own children rather than somebody else's.
THEIR_OWN = re.compile(r"\b(?:i|we|my|our|us)\b", re.I)
# "how many kids does my sister have", "how many children has she got": somebody else's count.
SOMEONE_ELSE = re.compile(
    r"\b(?:does|do|did|has|have|had)\s+(?:my|her|his|their|your|she|he|they|the|that)\b", re.I)
A_CHILD = re.compile(r"\b(?:" + "|".join(CHILD_RELATIONS) + r")\b", re.I)
# A count of something else: "how many kids in a class", "how many children does a school take".
NOT_THEIR_OWN = re.compile(
    r"\b(?:in|at|per|into)\s+(?:a|an|the|my|our)\s+(?:class|classroom|school|nursery|team|"
    r"group|year|country|world)\b", re.I)


def _asks(text):
    """Whether the line asks the person's own number of children."""
    low = str(text or "").strip().lower()
    match = THE_ASK.search(low)
    if not match:
        return False
    rest = match.group("rest")
    if not A_CHILD.search(rest):
        return False
    if SOMEONE_ELSE.search(low):
        return False
    if NOT_THEIR_OWN.search(low):
        return False
    # "how many kids" on its own is the ask said short; anything else has to be about them.
    return bool(THEIR_OWN.search(low)) or len(rest.split()) <= 2


def _named_children(memory):
    """The children the store holds by name, each one once."""
    held = set()
    for entry in memory.get("others") or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip().lower()
        who = str(entry.get("who") or "").strip().lower()
        if not name or name in held:
            continue
        # A child who belongs to somebody else ("my sister's son") is not this person's child.
        if str(entry.get("of") or entry.get("whose") or "").strip():
            continue
        if who in CHILD_RELATIONS or not who:
            held.add(name)
    return held


def _relations(memory):
    """The child relations the person named, each one once, in the order they said them."""
    held = []
    for who in (memory.get("user") or {}).get("people") or []:
        word = str(who or "").strip().lower()
        if word in CHILD_RELATIONS and word not in held:
            held.append(word)
    for entry in memory.get("others") or []:
        if not isinstance(entry, dict):
            continue
        word = str(entry.get("who") or "").strip().lower()
        if word in CHILD_RELATIONS and word not in held:
            held.append(word)
    return held


def count(memory):
    """How many children the chat holds, or None when it holds no number worth saying."""
    user = memory.get("user") or {}
    if user.get("kids"):
        return None
    named = _named_children(memory)
    relations = _relations(memory)
    # A child named on their own says which child it is; the relations give the others. The
    # larger count is the true one: two sons called Jack and Sam are one relation and two
    # children.
    held = max(len(named), len(relations))
    if held < 2:
        return None
    return held


WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve"}


def _vary(options, memory):
    """A choice that does not repeat the last thing the bot said."""
    turns = memory.get("turns") or []
    recent = {t.get("bot") for t in turns[-5:] if isinstance(t, dict)}
    fresh = [o for o in options if o not in recent] or list(options)
    return random.Random(len(turns)).choice(fresh)


def reply_for(text, memory):
    """The count said back, or None on every line that is not the ask for it."""
    if not isinstance(memory, dict) or not _asks(text):
        return None
    held = count(memory)
    if not held:
        return None
    word = WORDS.get(held, str(held))
    noun = "children"
    return _vary(["You've got " + word + " " + noun + ".",
                  word.capitalize() + " " + noun + " \u2014 that's what you've told me.",
                  "That makes " + word + " " + noun + " you've mentioned."], memory)
