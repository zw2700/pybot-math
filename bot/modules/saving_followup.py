"""The follow-up turns of a saving plan, answered before the general readings get them.

A saving goal, the date for it and the rate are one question asked over three turns, and only
the first of the three says the word "save":

    i want to save 2000 pounds    -> "Then start with the smallest version of it" (advice about a
                                     habit, which says nothing about money)
    by june                       -> "Got it. Is there anything you'd like a hand with?"
    im putting by 500 a month     -> "Got it - you're putting by 500 a month."

Each of those lines on its own names nothing a knowledge entry can look up, so the readings that
answer a subjectless line took them and answered something else. Together they are arithmetic:
the goal, the weeks left and the rate give the figure the person actually wants.

`bot/memory/saving.py` holds all of the reading. This module is the turn it is asked on: the
candidates below are tried in the order a person would ask them, and the first one that
recognises the line answers it. Every one of them returns "" for a line it is not about, so a
chat with no saving plan in it is untouched.

The arithmetic itself is the money entry's - the goal, the date and the weekly figure are what
`bot/knowledge/money.py` already works out - so the question is written the way that entry reads
it (`saving.rate_question`) and answered in the knowledge base, rather than a second copy of the
sums living here.
"""
import re

from ..memory import saving
from ..understanding import understand
from . import answers

# Above the chatter band (1000), and below the memory store and the safety bands, whose turns
# these are not. Above `chat` (300) is not enough any more: the arbiter lets a declaring
# specialist take a turn off a hook from under the chatter band, and the money entry declares the
# topic these lines are read as, so a goal plus "how long will that take" was answered by whichever
# money card the purpose word matched ("...for a holiday" got the package-travel rules) with this
# module's arithmetic sitting in the list beside it. The band says what is true: on these lines
# this module read the whole question itself.
PRIORITY = 1100

# The turn is about money: a goal, a date for it, the rate towards it.
ANSWERS = ("money",)

# An answer that says how long a sum takes: "Saving 50 a month, you get to 1,000 in 20 months",
# "£500 at £25 a month is 20 months". The plain reading of a line that names both the goal and the
# rate is taken only when it does this sum, so advice about what share of a wage to put by (a real
# answer to some lines) never displaces the arithmetic the line asked for.
# "is 20 months", "in 20 months", "takes 7 months", "in a year", "one pay packet": a figure the
# sum produced, not the "three to six months of expenses" an answer says in passing. The length is
# counted in words as often as in digits ("in a year", "in two years"), and a goal with a month or
# less to go is answered as the one payment it is.
A_LENGTH_IN_MONTHS = re.compile(
    r"\b(?:is|in|takes|takes\s+about)\s+(?:about\s+)?"
    r"(?:\d[\d,]*|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
    r"(?:month|months|year|years|week|weeks)\b|\bone\s+pay\s+packet\b", re.I)


def _lower_first(answer):
    """The answer with its first letter lowered, for a lead-in sentence to run into."""
    text = str(answer or "")
    if not text or not text[0].isupper() or text[:2].isupper():
        return text
    return text[0].lower() + text[1:]


def _the_money_answer(question, memory):
    """The knowledge base's answer to the money question the line really is, or "".

    Two rates asked in a row are two figures with the same closing sentence both times, which is
    the answer above coming back with a new number sewn onto it, so the part already on the screen
    is left off (`saving.without_what_was_just_said`).
    """
    if not question:
        return ""
    was = memory.get("understood")
    try:
        memory["understood"] = understand(question, memory)
        answer = answers._respond(question, memory) or ""
    finally:
        if was is None:
            memory.pop("understood", None)
        else:
            memory["understood"] = was
    if not answer:
        return ""
    return saving.without_what_was_just_said(answer, memory) or answer


# The hook below and `respond` are asked the same question on the same turn, so the reading is
# done once and kept: it is a few dozen regexes over the line and the chat, and doing it twice for
# every line of every conversation is a cost nobody asked for.
_SEEN = {}


def _the_reply(text, memory):
    """The reply this line asks for, or "" - read once per line per chat length."""
    try:
        turns = memory.get("turns") or ()
        # The chat itself, not just the line: the same line in two conversations is two answers,
        # and `id` is the chat in hand because the runtime passes the one dict the whole time.
        key = (id(memory), str(text or ""), len(turns),
               str((turns[-1] or {}).get("user") or "") if turns else "")
    except Exception:  # noqa: BLE001 - a memory object that cannot be counted is read afresh
        key = None
    if key is not None and key in _SEEN:
        return _SEEN[key]
    reply = _read(text, memory) or ""
    if key is not None:
        if len(_SEEN) > 32:
            _SEEN.clear()
        _SEEN[key] = reply
    return reply


def respond(text, memory):
    """The reply this line asks for as part of a saving plan, or None."""
    if not isinstance(memory, dict):
        return None
    return _the_reply(text, memory) or None


def TAKES_AS_IT_COMES(text, memory):
    """This line is a saving-plan follow-up, read whole, so it is answered as it comes.

    Without the hook the specialist rule hands the turn to the knowledge base: "and if i cut the
    gym thats another 40" is read as money *and* fitness, the money entry declares both, and the
    £40 answer about a pot nobody asked about wins on the fit. The claim says what is true - this
    line is the rate half of a question this module has already read in full.
    """
    if not isinstance(memory, dict):
        return False
    return bool(_the_reply(text, memory))


def _read(text, memory):
    """The reply this line asks for as part of a saving plan, or ""."""
    gap = saving.the_gap_left(text, memory)
    if gap:
        # "how far off am i" is two figures the chat already holds worked against each other. On
        # main it reached the countdown reader and got a date - "That's about 3 weeks away" -
        # because the pot line ("im on 4 thousand") had filed the 4th of the month as a date.
        return gap
    position = saving.the_pot_position(text, memory)
    if position:
        # The same two figures said without a question: "im on 4 thousand" was answered with an
        # echo of the figure ("On 4 thousand, then."), which is the one thing a friend never does.
        return position
    more_a_month = saving.the_extra_a_month_asked(text, memory)
    if more_a_month:
        # "and how much more a month would do it" is the question the verdict a turn ago invited:
        # unread it printed the goal's first answer again, word for word.
        return more_a_month
    same_figure = saving.the_same_figure_a_month(text, memory)
    if same_figure:
        # The rate asked for in the unit the answer did not use: "whats that a week" after a
        # monthly figure is a fresh answer, not the same sentence again.
        return same_figure
    enough = saving.a_yes_no_about_the_rate(text, memory)
    if enough:
        # "is that enough" is about the rate on the screen, not a new one: the verdict on the
        # plan already read out. Left to the chatter band it answered "Sounds good.", which said
        # the opposite of the sum the turn before had just worked out.
        return enough
    need_a_date = saving.a_rate_with_no_date(text, memory)
    if need_a_date:
        # "how much a month?" with a goal but no date: the date is the missing half, and asking
        # for it beats a figure for the goal alone.
        return need_a_date
    raised = saving.a_rate_raised(text, memory)
    if raised:
        # "and if i cut the gym thats another 40" is the same goal at the rate it has become, not
        # a new goal of 40.
        return raised
    restated = saving.a_rate_restated(text, memory)
    if restated:
        # "and at 300 a month" puts another rate in place of the one before: the same goal, one
        # figure changed. Read as a line about nothing it got the 200 answer again with the
        # closing sentence still on it.
        return restated
    put_in = saving.a_rate_put_in_with_a_verb(text, memory)
    if put_in:
        # "what if i put away 300" after "i've got 200 a month to put away": the goal is the
        # one already in the chat and the figure is the new rate, not a new goal.
        return put_in
    at_the_chat_rate = saving.a_length_at_the_rate_in_the_chat(text, memory)
    if at_the_chat_rate:
        # "how long until i can afford 5000" when the chat holds the rate they can put by. The
        # money entry is asked the whole question, because the sum is its own.
        answer = _the_money_answer(at_the_chat_rate, memory)
        if answer:
            return answer
    no_price = saving.a_length_with_no_price(text, memory)
    if no_price:
        # "i save 50 a month" / "so how many weeks until i can buy it": the rate is in the chat
        # and the price is not, so nothing can be worked out and the line named no figure at all -
        # it got the search hedge. The rate is said as the money it becomes and the price is
        # asked for, which is the one figure the whole sum is waiting on.
        return no_price
    price = saving.a_price_in_an_answer(text, memory)
    if price:
        # "whats the bike going for?" / "a 200 pound one": the price answers the question above,
        # and the rate in the chat does the sum. Read as a goal it got a fresh set of rates.
        return price
    a_rate_given = saving.a_rate_for_the_goal(text, memory)
    if a_rate_given:
        # "im putting by 500 a month" against the goal named a turn ago is four months.
        return a_rate_given
    if saving.asks_how_long(text):
        length = saving.how_long_it_takes(memory)
        if length:
            # "how long will that take" after "For £2,000: £100 a month is 20 months, ..." is the
            # same question in the other unit, and it was answered with a search hedge.
            return length
    pot_alone = saving.the_pot_said_alone(text)
    if pot_alone:
        # The pot said on its own line: "i want to save 3000" / "i have 1000 saved already" is
        # the same goal with £1,000 of it already there. Answered as an echo ("Got it - you have
        # 1000 saved already") the line told them nothing, and the date turn after it had no pot.
        whole = saving._the_goal_in_the_chat(memory)
        if whole > pot_alone:
            rest = whole - pot_alone
            answer = _the_money_answer(saving.rate_question_for(rest), memory)
            if answer:
                return ("£%s still to find: %s"
                        % (format(rest, ","),
                           _lower_first(saving.without_the_pot_opener(answer))))
    if saving.asks_about_saving(text) and saving._names_a_goal(text):
        # The goal named on its own, with no date and no rate: "i want to save 2000 pounds" is the
        # first half of the same question, and the cost of not answering it is advice about how to
        # start saving ("then start with the smallest version of it") to someone who has just said
        # how much they want.
        pot, rest = saving.the_pot_and_the_rest(text)
        answer = ""
        if saving._a_rate_said(text)[0] or saving.a_length_was_said(text):
            # The goal *and* the rate are in the line, so the question is whole and the answer is
            # the sum on the two figures the person gave. Asked here as "how much do i need to put
            # by a week to have 1,000 pounds?", the rate was thrown away and a different question
            # asked: "if i save 50 a month how long to save 1000" got the sums at £100, £250 and
            # £500 a month, while the exact answer ("Saving 50 a month, you get to 1,000 in 20
            # months") was proposed on the same turn by `answers` and lost to this band. So the
            # plain reading of the line is tried first, and taken when it does the sum.
            plain = _the_money_answer(text, memory)
            if plain and A_LENGTH_IN_MONTHS.search(plain):
                answer = plain
        if not answer:
            answer = _the_money_answer(saving.rate_question(text, memory), memory)
        if answer:
            if pot and rest:
                # The pot and the rest of it in one line: the sums are about the £2,000 still to
                # find, and the lead says what they already have so the answer is not about a goal
                # they have already half reached.
                return ("£%s to find on top of the £%s you already have: %s"
                        % (format(rest, ","), format(pot, ","),
                           _lower_first(saving.without_the_pot_opener(answer))))
            return answer
    if saving.asks_the_rate(text, memory):
        # "how much a month" carries neither the goal nor the money word, and read on its own the
        # line found a diet entry.
        answer = _the_money_answer(saving.rate_question(text, memory), memory)
        if answer and saving.said_already(answer, memory):
            # The rate asked for again when the answer above is the same one: with a month or less
            # to go it is one pay packet whichever unit they ask in, so the line is answered in the
            # unit it named instead - the goal divided by the weeks left.
            # The figure is worked out here first, because the entry reads the date off the line
            # it is handed and a deadline it was never told in words ("by easter") gives it
            # nothing to divide; and because only this way keeps the month they asked for as the
            # lead and puts the week after it.
            other = saving.a_figure_each_week(memory)
            if not other or saving.said_already(other, memory):
                fresh = saving.the_figure_a_week(memory)
                other = _the_money_answer(fresh, memory) if fresh else ""
            if other and not saving.said_already(other, memory):
                answer = other
        if answer:
            return answer
    if saving.is_only_a_date(text):
        # A date on its own is a follow-up, not a subject: "by christmas" after a goal used to
        # reach an entry about Christmas shopping.
        settled = saving.a_date_on_a_settled_rate(text, memory)
        if settled:
            # A date after the rate was chosen asks whether that rate gets there by then.
            return settled
        money_question = saving.rate_question(text, memory)
        if money_question:
            answer = _the_money_answer(money_question, memory)
            if answer:
                return answer
    again = saving.another_sum_asked(text, memory)
    if again:
        # A new sum on its own is the same question about a different pot: "i want to save 2k" /
        # "what about 1k", and it is how the line reads, so the arithmetic comes first. Read as
        # the chat's goal, the money entry works the old figure out a second time.
        fresh = dict(memory)
        fresh.pop("understood", None)  # the reading of the old line is not the new one's
        answer = _the_money_answer(saving.rate_question(again, fresh), fresh)
        if not answer:
            answer = _the_money_answer(again, fresh)
        if answer:
            return answer
    return None

from ..memory import again as _said_before  # noqa: E402 - applied once the module is defined

# Whatever this module answers, the last thing that happens to it is the earlier-turn
# check (bot/memory/again.replied): `answers` alone served a card again on 59 deck turns.
respond = _said_before.replied(respond)
