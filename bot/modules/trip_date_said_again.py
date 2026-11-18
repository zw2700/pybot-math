"""A trip already on record, said again with the month they now mean.

    im going to spain in june
    actually we fly in september        ->  Got it - you're going to Spain in September.
    when do we fly                      ->  In September.

It also reads the version with the reason for the change after it, which names the date with no
going verb at all: "im going to lisbon in may" / "actually its june now, my sister moved her
holiday" is the same move, said the way people say it when they explain themselves.

The line names how they travel rather than the date alone, so the words are unremarkable - a
trip being told sounds the same. Only the store can tell the two apart, because a date is a
correction just when there is a trip for it to move: with no plan on record the same line is a
trip being told, and a birthday, a dentist appointment or a fear of flying in the same chat is
not the trip the line is about.

The store's own reader cannot be extended for it (its file is at the world's size limit), so the
date is read here, by bot/memory/facts.py, and handed to the store's correction path - which owns
the plan, the acknowledgement and the fact log. This module only decides that the line is a
correction of the trip on record.
"""

import re

from ..memory import facts as extract
from ..memory import trips
from . import memory_store

# Below the store (7000) so this sees what its observer has already kept from the line, and above
# the reply modules so the correction is in memory before anything answers.
PRIORITY = 6900


# The date said with the reason for it after the comma: "actually its june now, my sister moved her
# holiday". The store's own readers are anchored at the end of the line, so the reason stopped the
# date being read at all and the chat kept May - the packing answer two turns later was still "For
# Lisbon in May" after the trip had been moved to June. "now" is what says the date has moved
# rather than being a plan stated for the first time, and the marker in front is what makes it a
# change at all: "its june now" on its own is not this reader's business.
A_DATE_SAID_NOW = re.compile(
    r"^\W*(?:(?:ok|okay|right|well|so|and|no|nope|sorry|actually|oops|wait|ah|oh|hmm)"
    r"[,.]?\s+){0,4}"
    r"(?:(?:it'?s|its|it\s+is|that'?s|thats)\s+)?"
    + extract.A_DATE_VALUE +
    r"\s+now\b", re.I)
# The words that say the date is being put right rather than given for the first time. They are
# asked for apart from the pattern above because the line may open with a filler of its own
# ("ok so its the 12th now") - the filler says nothing, and the marker is the thing that says the
# line is a change, so it is looked for in front of the value whatever comes before it.
A_MARKER_SAID = re.compile(r"\b(?:no|nope|sorry|actually|oops|wait|ah|oh|hmm)\b", re.I)


def _a_date_said_now(text):
    """The date a line moves the trip to when it says the reason in the same breath, or "".

    A question moves nothing ("is it june now?"), and the value has to read as a date once it is
    read - "actually its done now" and "sorry its broken now" name no date. The words in front are
    the ones the trip readers take, so the two spellings of the same move cannot drift apart.
    """
    line = str(text or "")
    if "?" in line:
        return ""
    found = A_DATE_SAID_NOW.search(line)
    if found is None:
        return ""
    if not A_MARKER_SAID.search(line[:found.start(1)]):
        return ""
    for group in found.groups():
        if group and extract._a_date(group):
            return extract._tidy(group)
    return ""


def _the_first_clause(text):
    """The line up to its first comma, when that leaves a clause to read.

    A change is often said first and explained after it: "actually we fly in september, my sister
    moved her holiday". The trip reader finishes at the end of the line, so the explanation stopped
    it - and the explanation is never the part that names the date.
    """
    head = str(text or "").split(",")[0].strip()
    return head if len(head.split()) >= 2 else ""


def _the_trip_it_moves(memory):
    """The plan the date is about, or None when there is no trip for it to move.

    A birthday or an appointment can be the newest plan in the store, so the trip on record has
    to be the plan in hand as well: its own words have to be the ones the chat has up front.
    """
    plan = memory_store._stated_plan(memory) or memory_store.user(memory).get("plan")
    if not isinstance(plan, str) or not plan.strip():
        return None
    trip = trips._the_trip_so_far(memory)
    if not trip:
        return None
    on_record = " ".join(str(trip.get("plan") or "").lower().split())
    if not on_record:
        return None
    if on_record == " ".join(plan.lower().split()):
        return plan
    # A trip is not one line: "im going to lisbon in may with my sister" and then "we want to see
    # the old town and eat well" are the same trip, and the second is the plan on the table by the
    # time the month moves. The trip on record is in the chat's own plans, so the chat is still on
    # it - which is the thing this check is for. Without it "actually its june now, my sister moved
    # her holiday" moved nothing and the packing answer two turns later was still May.
    said_before = [" ".join(str(one or "").lower().split())
                   for one in memory_store.user(memory).get("plans") or []]
    if on_record in said_before:
        return trip.get("plan")
    return None


def _the_month_taken_back(memory):
    """The month the trip on record says, when the store keeps a plan that says it.

    The store's correction path reads a date before it reads a plan, and a birthday in the same
    chat is a date of its own, so a bare month would be moved in the birthday and not in the
    trip. Naming the month the trip says puts the reader on the plan that says it - and when no
    plan says it, nothing is moved rather than the wrong date.
    """
    trip = trips._the_trip_so_far(memory) or {}
    month = " ".join(str(trip.get("month") or "").lower().split())
    if not month:
        return None
    for said in memory_store.user(memory).get("plans") or []:
        if month in " ".join(str(said or "").lower().split()):
            return month
    return None


def _a_dated_fact_beside_it(memory):
    """Whether someone else's dated fact - a birthday, an appointment - is in the store.

    Such a fact is a date of its own, and the store reads a date before it reads a plan, so a bare
    month can be moved in the birthday rather than in the trip. Only then does the month have to
    be named.
    """
    for other in memory.get("others") or []:
        if not isinstance(other, dict):
            continue
        if any(other.get(key) for key in ("birthday", "appointment", "when", "date")):
            return True
    return False


def observe(text, memory):
    if not isinstance(memory, dict):
        return
    moved = (extract.a_trip_date_put_right(text)
             or extract.a_trip_date_put_right(_the_first_clause(text))
             or _a_date_said_now(text))
    if not moved:
        return
    if not _the_trip_it_moves(memory):
        return
    taken_back = _the_month_taken_back(memory) if _a_dated_fact_beside_it(memory) else None
    memory_store._apply_correction(memory, {"to": moved, "from": taken_back}, text)
