"""A tenancy is not a rent rise and not a manager: what a tenant can do about the landlord.

The home-and-DIY rows answer the fault itself (the damp, the boiler, the repair letter) and the
money rows answer the rent, so a complaint about a landlord fell between them. On main:

    i want to raise a complaint about my landlord        -> the section 13 rent-rise card
    i need to raise an issue with my landlord about ...  -> "Ask for a short private meeting"

Two things were wrong, and both are fixed here rather than in the files that held the rows, so that
this is one file with one subject and no half of somebody else's file changes under them:

1. `money.py`'s rent-rise row keys on "landlord" and on the verb "raise" alone, and `work.py`'s
   raise-with-boss row keys on the verb too. "raise" is a verb whose object decides the question: a
   rent rise is a raise of the rent, and a complaint, a concern, an issue, an alarm, a glass, a
   voice, prices or funds are somebody else's question. A tenancy is not a manager either. The two
   fences below stand those rows down, the way `bot/knowledge/__init__.py` gives a whole domain a
   STANDS_ASIDE guard - a row that already has a guard of its own keeps it.
2. The complaint itself had no card anywhere, so the line fell to an echo. It is a procedure with
   its own order - the letter and 14 days, the agent's free redress scheme, the council's housing
   team for a hazard, the deposit scheme, Shelter or Citizens Advice - and it is the row below.

The file is a domain like any other: ENTRIES, keyed on who runs the tenancy and on the act of
complaining, and nothing keyed on a wording.
"""
import re

from .lookup import entry

_NOT_A_RENT_RAISE = re.compile(
    r"\brais(?:e|ed|es|ing)\s+(?:a|an|the|my|our|your|their|any|some)?\s*"
    r"(?:complaints?|concerns?|issues?|problems?|matters?|questions?|grievances?|objections?|"
    r"disputes?|alarms?|glass|glasses|toast|voices?|prices?|funds?|money|children|kids|"
    r"awareness|profile|hell)\b",
    re.IGNORECASE)

# A tenancy, not a manager: the bank, the energy supplier and the shop already stand the work row
# down, and a landlord belongs in that list.
_A_TENANCY = re.compile(
    r"\b(?:landlords?|landlad(?:y|ies)|letting agents?|letting agency|lettings agency"
    r"|tenants?|tenancy|tenancies|housing association|council house)\b",
    re.IGNORECASE)


def _said(understood):
    if isinstance(understood, str):
        return understood.lower()
    reading = understood or {}
    return str(reading.get("clean") or reading.get("text") or "").lower()


def _a_raise_with_an_object(understood):
    """True when the raise is of something that is not the rent."""
    return bool(_NOT_A_RENT_RAISE.search(_said(understood)))


def _a_tenancy_and_not_a_manager(understood):
    """True when the landlord in the line makes it a tenancy question, not a manager one."""
    return bool(_A_TENANCY.search(_said(understood)))


def _fence(modules, row_id, when):
    """Give one row of another domain a guard, unless it already has one of its own."""
    for module in modules:
        for row in getattr(module, "ENTRIES", ()) or ():
            if row.id == row_id and getattr(row, "guard", None) is None:
                row.guard = lambda understood, when=when: not when(understood)


from . import money, work  # noqa: E402 - the rows fenced below have to exist first

_fence((money,), "rent-rise", _a_raise_with_an_object)
_fence((work,), "raise-with-boss", _a_tenancy_and_not_a_manager)


ENTRIES = [
    entry("landlord-complaint",
          (("landlord", "landlords", "landlady", "landladies", "letting agent",
            "letting agents", "letting agency", "lettings agent", "housing association",
            "my tenancy", "the tenancy", "my letting agent"),
           ("complain", "complains", "complained", "complaining", "complaint", "complaints",
            "formal complaint", "raise a complaint", "put in a complaint", "make a complaint",
            "made a complaint", "log a complaint", "report", "reported", "redress", "ombudsman",
            "deadlock", "not happy with", "unhappy with", "dispute", "issue", "issues",
            "concern", "concerns", "problem", "problems", "matter", "matters", "grievance")),
          "Put it in writing to the landlord - a dated email or letter, what happened, what you "
          "want done and a deadline of 14 days - and keep a copy, because every later step asks "
          "for it. If a letting agent runs the flat, the agent has to belong to a free redress "
          "scheme (the Property Redress Scheme or The Property Ombudsman), and a complaint can go "
          "there after eight weeks, or sooner if the agent deadlocks it. A hazard - damp, no "
          "heating, a broken boiler, a fire risk - is your council's housing team, who can inspect "
          "and order the work, and the deposit scheme holding your deposit sorts out a deposit "
          "argument. Shelter or Citizens Advice will read the letter before you send it, free.",
          # the who-it-is-about half has to be in the line as well, or a complaint about a shop
          # that happens to name a flat answers here
          ask=("landlord", "landlady", "agent", "tenancy", "tenants", "tenant", "flat",
               "complain", "complaint", "redress", "ombudsman"),
          # A repair, a deposit, a sale, a rent rise and an eviction are each their own answer, and
          # each carries the steps that come before a complaint.
          avoid=("fix", "fixed", "fixing", "repair", "repairs", "broken", "boiler", "heating",
                 "hot water", "damp", "mould", "mold", "deposit", "deposits", "selling", "sell",
                 "sale", "sold", "evict", "evicted", "eviction", "section 21", "section 8",
                 "notice to quit", "kick me out", "throw me out", "arrears", "behind on rent",
                 "rent increase", "raise the rent", "raised the rent", "put the rent up",
                 "eviction notice"),
          bias=1),
]

ANSWERS = ("home-and-diy",)
