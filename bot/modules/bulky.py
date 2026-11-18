"""A thing too big for the bin is a bulky waste job, and the composer had nothing for it.

"What do i do with old carpet" and "how do i get rid of an old trampoline" reached nothing: the
knowledge base has the mattress, the wardrobe, the washing machine and the paint tin, but not the
carpet or the trampoline, so the composer fell back to "I'm not sure about that one, sorry - I'd
rather not guess. A quick search online will get you a solid answer". The person is left holding
the thing and a search box.

The answer is the same three routes any bulky thing takes: the council's bulky waste collection,
the recycling centre, or a charity that collects if the thing is still usable. The first step is
the one that makes it moveable - roll a carpet, take a wardrobe apart - and the fee is the
council's, so the reply says where to check it rather than inventing a number.

This sits above the greeting band (PRIORITY -1000) and below every knowledge module, so it only
ever answers a line no entry reached. A mattress, a wardrobe, a washing machine and a tin of paint
keep their own answers. The thing can be in the line or in the line before it ("we are replacing
the carpet" / "what do i do with the old one"), because a pronoun names no thing on its own.
"""
import re

PRIORITY = -999

# The thing, grouped by what happens to it. A floor covering is rolled and cut, a wardrobe comes
# apart, an electrical goes back to a shop, and everything else is the general bulky route.
FLOOR = re.compile(
    r"\b(?:carpets?|carpet\s+tiles?|underlay|lino(?:leum)?|vinyl\s+flooring|"
    r"vinyl\s+tiles?|flooring|doormats?)\b", re.I)
FURNITURE = re.compile(
    r"\b(?:sofas?|settees?|armchairs?|mattress(?:es)?|beds?|wardrobes?|tables?|chairs?|"
    r"desks?|bookcases?|bookshelves?|shelving|cabinets?|sideboards?|"
    r"chests?\s+of\s+drawers|furniture)\b", re.I)
ELECTRICAL = re.compile(
    r"\b(?:fridges?|freezers?|washing\s+machines?|dishwashers?|tumble\s+dryers?|"
    r"ovens?|cookers?|microwaves?|tvs?|televisions?|monitors?|computers?|laptops?|"
    r"printers?|kettles?|hoovers?|vacuum\s+cleaners?|boilers?|radiators?)\b", re.I)
GARDEN = re.compile(
    r"\b(?:trampolines?|sheds?|fences?|patios?|slabs?|soil|bushes|bush|trees?|"
    r"garden\s+waste|green\s+waste)\b", re.I)
# A line that asks what to do with a thing rather than how to clean or mend it.
DISPOSAL = re.compile(
    r"\b(?:what\s+(?:do|should|can)\s+(?:i|we)\s+do\s+with|"
    r"how\s+(?:do|can|should)\s+(?:i|we)\s+(?:get\s+rid\s+of|dispose\s+of|throw\s+(?:away|out))|"
    r"where\s+(?:can|do|should)\s+(?:i|we)\s+(?:take|put|get\s+rid\s+of)|"
    r"get\s+rid\s+of|dispose\s+of|throw\s+(?:away|out)|take\s+(?:it\s+)?to\s+the\s+tip|"
    r"goes?\s+in\s+the\s+bin|recycle)\b", re.I)
# A floor covering being taken up is the turn before the disposal ask: "we are having the carpet
# replaced" was met with "Good to hear. What was the best bit?", which reads a plan as a past day.
REPLACING = re.compile(
    r"\b(?:replacing|pulling\s+up|taking\s+up|ripping\s+up|"
    r"(?:having|getting)\s+(?:the\s+|a\s+)?[a-z ]{0,12}(?:replaced|lifted))\b", re.I)
# The line is about a thing that is finished with, not a new one being chosen.
FINISHED = re.compile(
    r"\b(?:old|broken|worn|worn\s+out|tired|replaced|replacing|ripped|stained|damp|smelly|"
    r"had\s+it|no\s+good|unwanted|spare|left\s?over|pulled\s+up)\b", re.I)
# A pronoun in the current line can point at the thing in the line before it.
POINTING = re.compile(r"\b(?:it|that|this|one|them|those|these)\b", re.I)
# Asbestos, needles and chemicals are not a trip to the tip in a car; another module owns them.
NOT_OURS = re.compile(
    r"\b(?:asbestos|needles?|syringe|chemicals?|acid|gas\s+(?:bottle|cylinder)|"
    r"oil|paint|solvent|pesticide|weedkiller|medical|clinical)\b", re.I)
# Cleaning, mending or choosing a new one has its own answer; only a finished thing goes out.
KEEPS_ITS_ANSWER = re.compile(
    r"\b(?:clean|cleaning|wash|washing\s+it|stain|smell|moth|moths|remove|mend|repair|fit|lay|"
    r"choose|choosing|buy|buying)\b", re.I)


def _clean(text):
    return " ".join(str(text or "").lower().split())


def _group(text):
    for name, pattern in (("floor", FLOOR), ("furniture", FURNITURE),
                          ("electrical", ELECTRICAL), ("garden", GARDEN)):
        found = pattern.search(text)
        if found:
            return name, found.group(0).lower()
    return "", ""


def _the_thing(text, memory):
    """The thing the line is about, from this line or the one before it."""
    group, thing = _group(text)
    if thing:
        return group, thing
    if not POINTING.search(text) or not isinstance(memory, dict):
        return "", ""
    turns = memory.get("turns")
    if not isinstance(turns, list):
        return "", ""
    for said in reversed(turns[-3:]):
        if not isinstance(said, dict):
            continue
        group, thing = _group(str(said.get("user") or ""))
        if thing:
            return group, thing
    return "", ""


def _reply(group, thing):
    if group == "floor":
        return (
            "Roll the {0} up and cut it into lengths you can lift, then take it to the recycling "
            "centre - most tips take {0} in the general waste skip. If it will not fit in a car, "
            "book a bulky waste collection with your council; most charge twenty to forty pounds "
            "for a doorstep pickup. Check your council's site for the fee and the booking, "
            "because I can't see your council's charges from here."
        ).format(thing)
    if group == "furniture":
        return (
            "Take the {0} apart if it will come apart, then book a bulky waste collection with "
            "your council - most charge twenty to forty pounds - or take it to the recycling "
            "centre. If it is still usable, a charity or a local reuse group may collect it; the "
            "British Heart Foundation collects furniture in many areas. Check your council's "
            "site for the fee and the collection, because I can't see your council's charges "
            "from here."
        ).format(thing)
    if group == "electrical":
        return (
            "Anything with a plug or a battery is electrical waste, so it cannot go in the bin: "
            "a shop that sells the same kind of thing has to take it back, and the recycling "
            "centre has an electricals point. A {0} is also a bulky collection if you cannot "
            "move it - ask the shop delivering a new one to take the old one. Check your "
            "council's site for the fee, because I can't see your council's charges from here."
        ).format(thing)
    return (
        "Dismantle the {0} as far as it will come apart and take it to the recycling centre, or "
        "book a bulky waste collection with your council; most charge twenty to forty pounds. "
        "The metal goes in the scrap metal skip and the rest in general waste, and green garden "
        "waste goes in the council's green bin. Check your council's site for the fee and any "
        "permit, because I can't see your council's charges from here."
    ).format(thing)


def respond(text, memory):
    clean = _clean(text)
    if not clean:
        return None
    if not DISPOSAL.search(clean) and not REPLACING.search(clean):
        return None
    if NOT_OURS.search(clean) or KEEPS_ITS_ANSWER.search(clean):
        return None
    group, thing = _the_thing(clean, memory)
    if not thing:
        return None
    if REPLACING.search(clean) and not DISPOSAL.search(clean):
        # Only a floor covering has an old one to get out; a replaced boiler or a fitted kitchen
        # is another kind of job and keeps its own answer.
        if group != "floor":
            return None
        return "Good. What are you doing with the old one - tip or a council collection?"
    if not FINISHED.search(clean) and not POINTING.search(clean):
        return None
    return _reply(group, thing)
