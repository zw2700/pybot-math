"""A reply cut to length without ending on a condition whose doing was cut away.

Handing back a part of an earlier answer means cutting it to the length of a reply, and the
usual cut is at the last comma that fits: "... 48 hours ahead?" If it keeps happening" is what
that gives, and "If it keeps happening." tells the person nothing to do - the step is in the
clause the cut took away. The fault is general: any sentence written "If X, do Y" loses Y when
it is cut between X and Y, and the same happens with "unless" and "in case".

So the cut is checked before it is used: when the piece that fits would end on one of those
conditions, the cut moves on to the end of the doing that follows it, or, if that doing is too
long to carry, steps back to the clause before the condition. Either way the reply is a whole
step rather than a condition with its consequence missing.
"""
import re

# The start of the last clause: after a comma, a colon, or a full stop and a closing quote. The
# closing quote matters because an ask inside a quoted script ends "ahead?" - with the question
# mark inside the quote, so a plain sentence split does not see the boundary.
_LAST_CLAUSE = re.compile(
    r"(?:^|[,;:]\s+|[.!?][\"'\u201d]?\s+)((?:and\s+)?(?:if|unless|in\s+case)\b[^,;:]*)$", re.I)

# What a cut can leave in front of the condition and still be part of the same list: "if the lid
# is red ... or if you have a temperature". A cut there is complete, because the doing came
# before the list ("Go to A&E ... if the lid is red"), so the condition is not hanging.
_CONTINUES = re.compile(
    r"^['\"\u201d]?(?:or|and|but|which|who|whom|whose|that|so|then|yet|plus|as|if|unless)\b", re.I)

# How much of the doing after a condition to keep before it makes more sense to step back to the
# clause before it. A condition whose doing is longer than this is not a step this reply needs.
_MOST_AFTER = 90


def a_whole_cut(text, most):
    """``text`` cut to about ``most`` characters, never ending on a hanging condition.

    The caller asks for the last comma or semicolon inside ``most``; when that lands between a
    condition and its doing, the cut is moved to the end of the doing, or back to before the
    condition when the doing is too long. A text that already fits is returned unchanged.
    """
    whole = str(text or "").strip()
    if len(whole) <= most:
        return whole
    cut = max(whole.rfind(", ", 0, most), whole.rfind("; ", 0, most))
    if cut < 80:
        cut = whole.rfind(" ", 0, most)
    cut = max(cut, 80)
    kept = whole[:cut].strip(" ,;:-")
    dropped = whole[cut:].strip(" ,;:-")
    hanging = _LAST_CLAUSE.search(kept)
    if not hanging or not dropped or _CONTINUES.match(dropped):
        return kept
    after = re.search(r"[,;]\s", whole[cut + 2:])
    end = cut + 2 + after.start() if after else len(whole)
    doing = whole[cut:end]
    if end - cut <= _MOST_AFTER and "'" not in doing and '"' not in doing:
        return whole[:end].strip(" ,;:-")
    return kept[:hanging.start(1)].strip(" ,;:-")
