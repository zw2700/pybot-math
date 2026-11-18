"""The questions whose answer is nowhere in this bot, said where the answer lives.

What a pass, a warranty or a policy covers, what somebody else's rules allow, what is in a hotel
room, and what happens to the old unit when the new one arrives cannot be answered from here: the
small print, the rules and the booking page are theirs, and a guess would be worse than none.
`bot/compose/routes.py` reads those kinds and names the one place that holds the answer - the terms
page, the insurer, the operator, the council, the booking page, Citizens Advice or ACAS.

This module sits just above greeting's honest hedge ("a search should sort you out quickly") and
below every light remark and every card, so it only ever speaks where the bot would otherwise have
told the person to go and search. It asks the composer first and stands down unless the answer
really is a hedge, so a reader in `bot/compose/fallback.py` that has found the right body to ask
(the landlord, the union, the school office) keeps its turn even though this module outranks
greeting. There are two exceptions, and they are one fault: a card whose subject is not the
question. A card about the *rate* for parking, answering a line that only asked whether there is
any, and a card about today's timetables, answering whether a venue has disabled access. In both
the person has not been told the thing is there yet, so the rate or the timetable is an answer to a
question they did not ask, and the pool says both.

Nothing here holds a fact about the world, so nothing here can be wrong or go stale, and
`routes.py` stands down on a statement, on a lid rather than a policy, on a child's own permission
and on any line a card answers.
"""
import re

from ..compose import fallback, findout, routes

# The composer's hedge comes in several shapes, and `fallback._is_a_hedge` knows most of them. A
# second family reaches the person in the same clothes without being on that list: the reply that
# offers a search, or a phone call, instead of an answer ("a call beats searching", "the quickest
# route to a straight answer"). Those are placeholders by this lane's definition too, so the
# reading is made here as well: a new hedge wording cannot leave somebody with "go and search"
# while this module stands down and says nothing.
SEARCH_ONLY = re.compile(
    r"\b(?:beats searching|a search (?:should|will)|quick search|searching for it will|"
    r"quickest route to a straight answer|would rather not guess|beyond what i know|"
    r"not sure about that one)\b", re.I)

# The other way a wrong answer arrives is not a hedge at all: a card about the *price* of a thing
# answers "is there parking at the hotel" - the person has not yet been told the thing exists, so
# the rate is an answer to a question they have not asked. A yes-or-no ask of a place, answered
# only in money, is this lane's; a line that really is asking the price ("how much is parking at
# the hotel") is not, and keeps the card.
A_YES_OR_NO_ASK = re.compile(
    r"\b(?:is there|are there|do they have|does (?:it|this|that|the [a-z]+) have|have they got)\b")
# A card for today's listings and opening hours has its own subject; asked whether a place has
# something, it answers a question nobody asked, the way a price does.
LIVE_ONLY = re.compile(
    r"(timetables? and listings|change by the hour|that is live|live, sorry|today's included|"
    r"the current one, today)", re.I)
# A third way the same fault arrives: `gap.py` answers an *inclusion* ask ("does the price include
# breakfast at the hotel") with what a *figure* depends on - a quote, a listing, two firms pricing
# the same description. That is a good line for "how much will it cost", and no answer at all to
# whether the breakfast is in the price, which is a list of what is included, on the booking page.
# The route already holds that list's home (`routes.INCLUDED`), so the inclusion ask takes it.
INCLUDED_ASK = re.compile(
    r"\b(?:includes?|included|in with|comes? with|part of the price|on top|extra)\b", re.I)
A_FIGURE_REPLY = re.compile(
    r"(?:comes from a quote or a listing|no list price|price the same description|"
    r"ask two firms to price|compare what each one leaves out)", re.I)
MONEY_WORDS = re.compile(
    r"\b(?:rate|rates|charge|charges|price|prices|pricing|cost|costs|fee|fees|tariff|per hour|"
    r"per day|per night)\b", re.I)

# A fourth way a reply answers nothing: a card about a *different subject* taking the line on one
# word of it. On the world's main, "is there a lift at the station" gets a lifting technique ("bend
# at the hips and knees"), "can i keep the old sofa" gets freezer times, "will they take the old
# fridge away" gets what to wear for the weather. A reply to a question about a thing has to be
# about that thing; if it shares no word with the question, it is answering something else, and an
# honest "here is where to find out" beats a confident card about the wrong subject.
QUESTION_FILLER = frozenset("""
a an the is are was were be been being am do does did have has had having there here it this
that these those they them their theirs i me my mine we us our you your yours he him his she
her hers who whom whose what which when where why how much many long far often any some all
and or but if then than so not no yes can could will would should may might must shall to of
in on at for with from by about into over under up down out off again more most very just
only also too own same other another such per each every both either neither nor as like
get got gets getting go going goes went come comes came coming take takes took taken taking
one ones thing things still yet ever never always really quite rather bit lot
""".split())


# The verb that asks what happens to the old one says nothing about the thing itself: a card about
# freezer times shares "keep" with "can i keep the old sofa" and answers nothing.
OLD_ONE_VERBS = frozenset("""keep keeping kept take taking taken away rid getting get gets
throw throwing leave leaving want wants wanted happen happens happened dispose disposal""".split())


def _content(text, skip=()):
    """The words of a line that carry its subject: no filler, no figure, and no verb of the ask."""
    return {w for w in re.findall(r"[a-z]+", (text or "").lower())
            if len(w) > 2 and w not in QUESTION_FILLER and w not in skip}


PRIORITY = -999  # above greeting (-1000), below nudge (-950), urgent, invitation and every card


def _would_be_said(text, memory):
    """The reply the person would get if this module said nothing, which is greeting's.

    `fallback.reply_for` is one layer below that: greeting's own tables answer a good many of
    these lines before any pool is reached, so asking the fallback instead of the greeting threw a
    real answer away for a page. `is there a plug socket in the room` had the watts-and-13-amp
    answer and got the booking page. The gate has to be the reply that would actually be said, so
    it is asked of greeting itself, and the fallback only when greeting passes.
    """
    try:
        from . import greeting
        said = greeting.respond(text, memory)
    except Exception:  # noqa: BLE001 - a broken greeting must not cost the person an answer
        said = None
    if not said:
        said = fallback.reply_for(text, memory)
    return said or ""


def _answers_the_ask(route, clean, said):
    """Whether the reply the person would get is an answer to the question in `clean`.

    Three ways a reply is not: a price instead of a yes ("That is a published rate..."), today's
    listings instead of what a building has, and - the worst - a card about another subject taking
    the line on one word of it. On the world's main "is there a lift at the station" gets a lifting
    technique, "is there a freezer in the room" the maker's sheet for a machine, "can i keep the
    old sofa" freezer times and "will they take the old fridge away" what to wear for the weather.
    A reply about a thing shares a word with the question about it; one that shares none is
    answering something else, and the honest "here is where the answer is" is the better line.
    """
    if not said:
        return True
    if route is routes.A_PLACE_HAS and A_YES_OR_NO_ASK.search(clean):
        if MONEY_WORDS.search(said) or LIVE_ONLY.search(said):
            return False
        return bool(_content(said) & _content(clean))
    if route is routes.THE_OLD_ONE_POOL:
        return bool(_content(said) & _content(clean, OLD_ONE_VERBS))
    if route is routes.INCLUDED and INCLUDED_ASK.search(clean) and A_FIGURE_REPLY.search(said):
        return False
    return True


def respond(text, memory):
    """Name the place, or say nothing and let the composer answer as it did."""
    understood = memory.get("understood") or {}
    clean = fallback._matchable(fallback._plain(understood.get("clean") or text))
    # How busy somewhere is now is not a rule the council or the operator writes, and the council
    # line is the wrong subject for it: "is the tip busy today" was answered about the rules for a
    # tip instead of about the queue. The crowd reading in `findout` owns that ask and answers it
    # under this module, so this one stands down while it does.
    if findout.reads_as_busy(clean):
        return None
    route = routes.options(clean)
    if not route:
        return None
    said = _would_be_said(text, memory)
    if fallback._is_a_hedge(said) or SEARCH_ONLY.search(said or ""):
        return fallback._choose(route, memory, fallback._matchable(text))
    if route is routes.INCLUDED and INCLUDED_ASK.search(clean) \
            and A_FIGURE_REPLY.search(said or ""):
        # what a figure depends on is not what the price includes
        return fallback._choose(route, memory, fallback._matchable(text))
    if not _answers_the_ask(route, clean, said or ""):
        return fallback._choose(route, memory, fallback._matchable(text))
    return None  # the composer has an answer of its own; it keeps the turn
