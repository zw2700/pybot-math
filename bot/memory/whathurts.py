"""The part of them that hurts, and which one it is.

The store keeps one complaint of the person's in ``user["hurts"]`` (the part, the side, the place
on it, and the part a put-right came from). These readers answer the lines about it. They live
here rather than in ``bot/modules/memory_store.py`` because that file is at the 1 MiB cap the
world enforces and a reader added to it cannot be submitted.
"""

import random
import re

from . import facts as extract
from . import last_user
from .told import _quote as quote_said

BODY_PARTS = extract.BODY_PARTS
BODY_PART = extract.BODY_PART

# "and which knee was it", "which one", "what side": a part of them they named earlier, asked
# about by name. Nothing read these, so a part given at turn 2 was a hedge at turn 9.
WHICH_PART = re.compile(r"\bwhich (?:one|side|part|" + "|".join(BODY_PARTS) + r")\b"
                        r"|\bwhat side\b|\bleft or right\b", re.I)

# "which one" is a choice far more often than a side: "my knee hurts" and then "which one should
# i buy" is a shopping question about the knee above it, and answering it "you did not say which
# side" tells the person nothing. The words that may follow "which one" are only the ones a side
# question is made of - "which one was it", "which one did i say", "which one hurts" - and any
# other word after it makes it a choice. A named part ("which knee", "what side") needs no guard.
AFTER_WHICH_ONE = re.compile(r"\bwhich one\b(.*)$", re.I)
A_SIDE_TAIL = frozenset((
    "was", "is", "it", "that", "did", "i", "say", "said", "then", "again", "exactly", "hurts",
    "hurt", "of", "them", "those", "the", "two", "please", "one", "side", "part", "was"))

HURTING_ASK = re.compile(r"\b(?:hurt|hurts|hurting|sore|ache|aching|pain|painful)\b", re.I)


def _vary(options, memory):
    """pick(), but over the whole reply: a lead-in and a body put together can repeat a line
    the bot said, even when the pieces on their own do not."""
    turns = memory.get("turns") or []
    recent = {t.get("bot") for t in turns[-5:]}
    fresh = [o for o in options if o not in recent] or list(options)
    return random.Random(len(turns)).choice(fresh)


def which_one_is_a_side(low):
    """False when "which one" is the whole of a question about choosing, not about a side."""
    found = AFTER_WHICH_ONE.search(low)
    if not found:
        return True
    return not [word for word in re.findall(r"[a-z']+", found.group(1).lower())
                if word not in A_SIDE_TAIL]


def before(memory):
    """The part the store holds before this line is read, carried across ``observe``."""
    held = (memory.get("user") or {}).get("hurts") or {}
    return str(held.get("part") or "") if isinstance(held, dict) else ""


def after(memory, held_before):
    """A part named where another was held is a put-right, not a second ache."""
    held = (memory.get("user") or {}).get("hurts")
    if (isinstance(held, dict) and held_before
            and str(held.get("part") or "") != held_before):
        # "my knees have been hurting" then "my back hurts not my knees" is one complaint, and
        # the store keeps the part it came from so the reply can say both halves.
        held["was"] = held_before


# A line that asks about a part instead of reporting one: "who has a sore hip", "does a sore knee
# need a doctor", "should i see someone about a sore back", "what helps a sore back".
ASKED_ABOUT_A_PART = re.compile(r"^\s*(?:who|what|which|when|where|why|how|does|do|did|is|are|was|"
                                r"should|shall|can|could|would|will|any)\b|\?\s*$", re.I)


def _a_question_about_a_part(line):
    return bool(ASKED_ABOUT_A_PART.search(str(line or "")))


def what_is_hurting_reply(memory, low):
    """"what did i say was hurting": the part the store holds now, not an older line quoted."""
    if not HURTING_ASK.search(low) or not re.search(r"\bsa(?:y|id)\b|\bwhat .*\b(?:hurt|sore|pain)\b",
                                                    low):
        return None
    held = (memory.get("user") or {}).get("hurts")
    if not isinstance(held, dict) or not held.get("part"):
        previous = " ".join(str(last_user(memory) or "").split())
        if _a_question_about_a_part(previous):
            # "who has a sore hip", "should i see someone about a sore back": the part is what the
            # line asked about, so it is not a complaint of theirs and saying it back as one puts
            # words in their mouth. The honest answer is that nothing of theirs is filed.
            asked = extract.BODY_PART.search(previous.lower())
            what = asked.group(1).lower() if asked else "it"
            return _vary(["You asked about a sore " + what + " - you haven't told me about "
                          "anything of your own hurting.",
                          "Nothing of yours - you were asking about a sore " + what + "."], memory)
        if (extract.BODY_PART.search(previous.lower())
                and extract.BODY_HURTS.search(previous.lower())):
            # They did say a part was hurting, and it was somebody else's body ("my mum has a
            # sore hip", "my son hurt his arm"), so nothing of theirs is filed. The line is what
            # was said and saying it back is the honest answer; a denial of it is not.
            return quote_said(previous, memory)
        # Nothing of theirs is filed as hurting, so the honest answer is that. Quoting the last
        # line they said about anything ("You said you have a cat called max") answers a question
        # about their knee with a cat.
        return _vary(["You haven't told me about anything hurting.",
                      "Nothing of yours is hurting as far as I know.",
                      "You haven't said that anything is hurting."], memory)
    part = str(held.get("part") or "")
    was = str(held.get("was") or "")
    side = str(held.get("side") or "")
    one = "your " + (side + " " if side else "") + part
    verb = "were" if part.endswith("s") else "was"
    if was:
        return _vary(["It is " + one + " - you put the " + was + " right.",
                      one[:1].upper() + one[1:] + ", since you put the " + was + " right.",
                      "You said " + one + " in the end, not the " + was + "."], memory)
    return _vary(["It is " + one + " that you said " + verb + " hurting.",
                  one[:1].upper() + one[1:] + " - that is the one.",
                  "You said " + one + "."], memory)


def the_part_asked(memory, low):
    """The part of them that is sore, said back to a question about which one it is."""
    if not WHICH_PART.search(low):
        return None
    if not which_one_is_a_side(low):
        return None
    held = (memory.get("user") or {}).get("hurts")
    if not isinstance(held, dict) or not held.get("part"):
        return None
    part = str(held.get("part") or "").strip().lower()
    asked = BODY_PART.search(low)
    if asked and asked.group(1).lower() not in (part, part.rstrip("s"), part + "s"):
        # They asked about a different part from the one the store holds, so it has nothing to
        # say about it rather than answering about the knee to a question about the shoulder.
        return None
    if not asked:
        # "which one", "what side": the part has to be the one in front of the chat, or the line
        # would be answered about any part they ever named.
        previous = " ".join(str(last_user(memory) or "").lower().split())
        if part not in previous and part.rstrip("s") not in previous:
            return None
    side = str(held.get("side") or "").strip()
    place = str(held.get("place") or "").strip()
    if side:
        said = _vary([side[:1].upper() + side[1:] + " " + part + ".",
                      "Your " + side + " " + part + " - that is what you said.",
                      "The " + side + " one."], memory)
        if place:
            said = _vary([side[:1].upper() + side[1:] + " " + part + ", " + place + " side.",
                          "Your " + side + " " + part + ", the " + place + " of it."], memory)
        return said
    if place:
        # They said where on it and never which leg or arm: saying "the outside" back is the
        # honest answer, and claiming a side they never gave would be invented.
        return _vary(["The " + place + " of it - you did not say which side.",
                      "The " + place + " of your " + part + ", you said. Left or right you did "
                      "not say.",
                      "You said the " + place + " of it. Not which side."], memory)
    return _vary(["You said your " + part + ", without saying which side.",
                  "Just your " + part + " - you did not say left or right."], memory)
