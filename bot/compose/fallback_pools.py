"""The two pool readers that weigh most, lifted out of fallback.py.

`bot/compose/fallback.py` was over the publisher's 1 MiB per-file limit on main, and one file
that big stops every PR in the swarm from being filed, whoever wrote it: tables moved to
`fallback_data.py` in #10007 and it was still 5,354 bytes over.

So the two readers that weigh most moved out whole - `_unknown`, which composes the honest
reply when nothing else knows, and `_the_view_asked_for`, which gives the bot's own view back -
with every comment and every word unchanged. They read the tables and helpers in `fallback.py`,
and `fallback.py` calls them through two small wrappers that import this module on the first
call, so neither module closes an import circle. No reply changes: this is a move.
"""

import re

from . import findout, for_the_day, waited_for
from .fallback_data import (
    MISSED_STEP_LINES, REPAIR_WHETHER_LINES, the_bots_own_answer,
    the_place_the_answer_is_kept,
)
from .the_rule_for_it import A_CARE_WORD, A_MONEY_WORD, TIME_RULE, the_rule_for_it
from .fallback import (
    method_ask_pool,
    ANIMALS, ASKED_IF_I_SAW_LINES, A_PERSON_IN_A_CRISIS, A_STEP_ASK, BARE_FOLLOW_UP,
    BARE_FOLLOW_UP_CARE_REPLIES, BARE_FOLLOW_UP_REPLIES, BARE_PICK_AFTER_NEWS,
    BODY_IS_NOT_A_MACHINE, BODY_PARTS, CARE_HERE, CARE_MODULES, CRISIS_ASK,
    DITHER_OPEN_LINES,
    EXPERT_WORDS, HANDED_BACK, HEALTH_WORDS, HELP_ALREADY, HOW_TO_DECIDE,
    HOW_TO_DECIDE_LINES, LEAVING_IN_THE_LINE, LIFE_DIRECTION, NEUTRAL, NOT_A_TIPS_ASK,
    NOT_NOTED, POINTING_LINES, REALISTIC, REALISTIC_ABOUT_ME, REPAIR_BARE_IT,
    who_settles,
    REPAIR_DECISION, REPAIR_PERSON,
    REPAIR_RULE, REPAIR_TARIFF, REPAIR_TRADE, REPAIR_WHAT_IT_IS_WORTH, REPAIR_WHETHER,
    SAME_AGAIN, SAME_AGAIN_WITH_THE_ANSWER, SYMPTOM_WORDS, TAG_CAN,
    TAG_CONFIRM, TAG_UNSURE, TIPS_ASKS, TIPS_LINES, TOO_LATE, UNKNOWN,
    UNKNOWN_ABOUT_A_PET, UNKNOWN_ABOUT_SOMEONE, UNKNOWN_DECIDE, UNKNOWN_HEALTH,
    UNKNOWN_REALISTIC, UNKNOWN_REALISTIC_CARE, UNKNOWN_TOO_LATE, UNKNOWN_WORD,
    UNKNOWN_WORD_NAMED,
    UNKNOWN_WORRY, VIEW_AFTER_A_DEATH, VIEW_ASK_LINES, VIEW_COMPANY, VIEW_DECIDE,
    VIEW_HANDBACK, VIEW_LINES, VIEW_MIRROR, VIEW_MIRROR_LINES, VIEW_NAMES_SOMEBODY,
    VIEW_NO_SUBJECT, VIEW_ON_GOOD_NEWS, WASNT_THERE, WHO_FOR_IT, _a_bare_worry,
    _a_dead_end, _a_plan_doubt, _a_plan_in_the_thread, _a_price_wants_a_verdict,
    _a_care_home_line, _a_question_about_the_person, _a_repair_already_spoken_of,
    _a_subject_above, _a_switch_off_asked,
    _a_thing_they_started, _a_thing_was_named, _advisor, _after_a_colon,
    _answered_already, _answered_recently, _asked_about_the_day_they_had,
    _asks_a_name_back, _asks_for_a_person_to_talk_to, _bare_pick, _choose,
    _forecast_pool, _grief_thread, _hedged_recently, _in_a_care_thread,
    _in_a_crisis_thread, _in_a_loss_thread, _in_a_pool, _is_a_hedge, _is_a_tips_ask,
    _is_a_view_ask, _name_given_before, _names_its_own_thing, _news_above,
    _nothing_to_choose, _nothing_to_stand_behind, _only_a_reaction, _only_the_floor,
    _points_at_nothing, _reads, _reads_as_a_claim, _reads_as_taste,
    _says_it_already, _the_answer_above, _the_answer_in_reply, _the_line_before,
    _the_pool_for_a_worry_about_them, _the_thread_is_heavy, _the_view_of,
    _the_weird_ask_pool, _their_own_day, _thread_is_about_a_person,
    _thread_is_about_a_pet, _thread_is_about_someone_else,
    _offers_to_fix_themselves, _thread_is_about_the_body, _thread_names_a_machine, _tips,
    _who_for_the_thread, ack, asks_for_more,
    finding_out, in_a_safety_thread, no_eyes, reads_as_if_i_saw, the_lost_ask_reply,
    unknown_pool,
)


def _the_repeat_answer(memory):
    """The answer the person is asking for again, short enough to say again.

    The same guard has two forms and only one of them answers. "Same answer, and it covers this:
    <card>" carries what it names; "that is everything I have on that one, so I would only repeat
    myself" names the answer on the screen and then hands the person none of it. Ask twice in
    other words - "can i leave my bags at the hotel", then "can i leave my case at the hotel" -
    and that is the turn they get, on a card that answers both.

    So the answer above is carried, cut to its first two sentences when the card ran longer: the
    repeat is the same answer, and the person asked for it.
    """
    answer = " ".join(str(_the_answer_above(memory) or "").split())
    if not answer:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", answer)
    return " ".join(sentences[:2]) if len(sentences) > 2 else answer


def _drafting_pool(clean):
    """The drafting invite, without asking for what the line already said.

    "Give me who it's for" is the right question after "can you write a text for me", and the
    wrong one after "can you send a text to my landlord" - the person named the landlord in the
    same breath. So the pool is picked on the shape: when an addressee is already named, the
    invite asks for the gist and the tone, which is what is actually missing.
    """
    if no_eyes.names_the_addressee(clean):
        return UNKNOWN_WORD_NAMED
    return UNKNOWN_WORD


def _a_care_thread(memory, look_back=3):
    """True when the last few things the person said were about somebody being looked after.

    Read from the thread rather than the line, because the line is the bare ask: "my dog is
    having an operation tomorrow", "im worried", "how long will it take". A rule of thumb about
    a roast is not one about a wait at a vet or a ward, and the thread says so when the line
    cannot.
    """
    if _thread_is_about_a_pet(memory):
        return True
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        if A_CARE_WORD.search(str(turn.get("user") or "").lower()):
            return True
    return False


def _a_money_thread(memory, look_back=3):
    """True when the last few things the person said were about money they owe or are owed."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-look_back:]:
        if A_MONEY_WORD.search(str(turn.get("user") or "").lower()):
            return True
    return False


def _the_rule_for_it_for_the_turn(clean, repaired, memory):
    """What settles this kind of ask, said before where the rest of it is kept, or None.

    Three kinds have a rule the bot can always give: a price (where you buy it, the size, the
    day - and a job is priced by the quote), an amount (a portion per head, times the count) and
    a keeping question (how long it has been, and how cold). The pools live in
    `the_rule_for_it.py` so this file stays the reader it was.

    What stands down: a thread that is a crisis, a loss or care; a line naming a body, a symptom
    or a health word, because a rule of thumb about a portion is not one about a dose; and a
    thread that is about a body, for the same reason.
    """
    if (in_a_safety_thread(memory) or _grief_thread(memory) or _in_a_loss_thread(memory)
            or _in_a_care_thread(memory) or _thread_is_about_the_body(memory)
            or _a_care_thread(memory)):
        return None
    words = (set(re.findall(r"[a-z']+", str(clean or "").lower()))
             | set(re.findall(r"[a-z']+", str(repaired or "").lower())))
    if words & (BODY_PARTS | SYMPTOM_WORDS | HEALTH_WORDS):
        return None
    pool = the_rule_for_it(clean, repaired)
    if pool is TIME_RULE and _a_money_thread(memory):
        # "ive got 2000 on a credit card", "the apr is 22 percent", "how long will that take to
        # clear" was given the arithmetic for a roast. A price in a money thread is still a
        # price - what it costs to get someone out is the same question anywhere - but a time
        # in one is a debt being paid down, and that sum is the person's own.
        return None
    return pool

# A plan with a step missed: "what if i miss a week", "what if i skip a session", "what if we
# miss a couple of lessons". On main these fell to the search hedge - "a quick search online will
# get you a solid answer" - or, for a bare "what if i miss a week", to the late-period card. What
# the bot does know is what a missed step usually costs and what to do about it; what only the
# person knows is what they are partway through, so the pool says the first and asks for the
# second. It needs a plan noun after the miss ("what if i miss the bus" and "what if i miss her"
# are not plans), and a missed dose, pill, appointment or period is a clinician's question: the
# keep list stands the pool down for those, and so does a body, a pet, somebody else, a safety
# thread, grief and a loss.
MISSED_STEP = re.compile(
    r"\bwhat (?:if|happens if) (?:i|we|you) (?:miss|skip|dont do|cant do|cannot do)\b"
    r"|\bwhat (?:if|happens if) (?:i|we) (?:have to )?(?:miss|skip)\b")
MISSED_STEP_PLAN = re.compile(
    r"\b(?:a|an|one|two|three|four|\d+|a couple of|a few|couple of|few)?\s*"
    r"(?:days?|weeks?|fortnight|months?|sessions?|runs?|rides?|swims?|classes?|lessons?|"
    r"workouts?|practice|training)\b")
MISSED_STEP_KEEPS = re.compile(
    r"\b(?:pills?|doses?|drops|tablets?|meds|medication|medications|prescriptions?|insulin|"
    r"inhalers?|injections?|jabs?|appointments?|periods?|contracepti\w*|antidepressants?|"
    r"antibiotics?|lenses?|dressing|dressings)\b")


def _a_missed_step(clean, repaired, memory, words):
    """The pool for a stepped plan with one step missed, or None."""
    if not MISSED_STEP.search(clean):
        if repaired == clean or not MISSED_STEP.search(repaired):
            return None
    plan = MISSED_STEP_PLAN.search(clean) or MISSED_STEP_PLAN.search(repaired)
    if plan is None:
        return None
    if MISSED_STEP_KEEPS.search(clean) or MISSED_STEP_KEEPS.search(repaired):
        return None
    if set(words) & HEALTH_WORDS or set(words) & BODY_PARTS:
        return None
    if (in_a_safety_thread(memory) or _grief_thread(memory) or _in_a_loss_thread(memory)
            or _thread_is_about_the_body(memory) or _thread_is_about_a_pet(memory)
            or _thread_is_about_someone_else(memory)):
        return None
    return MISSED_STEP_LINES


def _unknown(understood, memory, clean):
    """An honest reply to a question nothing can answer: name who can, when it is clear."""
    # The same line with its wrong words put right ("any ideaz" -> "any ideas"), from the
    # reading: the bare-cue tests below are the only place a short ask is recognised, and a
    # person who types "any tipz" is asking for the same help as "any tips". Typed line
    # first, the repaired one only as a second try, exactly like every other pool here.
    repaired = understood.get("plain") or clean
    # Their own rota is a place that knows, so the line gets it rather than the hedge.
    own_day = _their_own_day(clean)
    if own_day:
        return _choose(own_day, memory, clean)
    # A body is not something to look up, and it is read before the pool that reads a bare "this"
    # as the text on their screen: "can you see if this is healing" is a mark on them, not a page.
    # Anything with no body and no mark in it is left to no_eyes below.
    body_lines = no_eyes.look_at_a_body_lines(clean, repaired, memory)
    if body_lines:
        return _choose(body_lines, memory, clean)
    cannot_see = no_eyes.cannot_see_your_thing(clean)
    if cannot_see:
        return _choose(cannot_see, memory, clean)
    # A noise or a smell in the room with them is not a fact to look up: "what was that noise"
    # and "what's that smell" both reached the search hedge, and the bot has no ear and no nose
    # to lend either way. The pool says so and asks the one thing it needs, with what the common
    # ones usually are.
    # The answer to the question the bot has just asked - "it came from the loft", "like burning",
    # "it blinks twice and stops" - is owed the other half of the exchange, so it is read before
    # the room pool, which would otherwise read a described light as a new one and ask again for
    # what it has just been told. It only fires where the bot's own last line was one of those
    # questions, so no first line can reach it.
    described = no_eyes.what_they_described(clean, memory)
    if described:
        return _choose(described, memory, clean)
    in_the_room = no_eyes.a_thing_in_the_room(clean)
    if in_the_room:
        return _choose(in_the_room, memory, clean)
    if no_eyes.writes_the_message(clean):
        # "can you send an email for me", "can you send a text to my landlord": the words are the
        # one half of this the bot can do, and the drafting invite asks for the two things it
        # needs. The reader already stands down for these; the pools below would send them to a
        # search.
        return _choose(_drafting_pool(clean), memory, clean)
    if _in_a_crisis_thread(memory) and (_asks_for_a_person_to_talk_to(clean)
                                        or CRISIS_ASK.search(clean)
                                        or WHO_FOR_IT.match(clean)):
        # A person asking for somebody to talk to, a turn after the bot answered something
        # frightening: every one of these shapes used to reach the search hedge, which offers a
        # person in crisis a search engine instead of Samaritans. Nothing below this reads the
        # thread, the advisor or a pool, because there is nothing here the bot could know that
        # matters more.
        return _choose(A_PERSON_IN_A_CRISIS, memory, clean)
    lost = the_lost_ask_reply(memory, clean, repaired)
    if lost:
        return lost
    if _asks_a_name_back(clean, understood.get("words") or []):
        # Nothing in the store has the name. If they gave it a turn or two ago, hand it back;
        # otherwise the honest thing is to ask for it, because the search shrug sent them to
        # look up their own brother.
        given = _name_given_before(clean, memory)
        if given:
            return _choose([line.format(name=given) for line in HANDED_BACK], memory, clean)
        return _choose(NOT_NOTED, memory, clean)
    forecast = _forecast_pool(clean, repaired, memory)
    if forecast:
        # Asked before the bare-follow-up ask: "will it get better" is a short line whose subject
        # is in the thread, so telling the person to say what they are asking about is the bot
        # not listening. It is asked after every reading that could answer, so it can only ever
        # stand in for a hedge.
        return _choose(forecast, memory, clean)
    # "did you see the match last night" opens a conversation rather than asking for a lookup, and
    # the hedge below is the wrong reply to it. It is asked before the taste and the pool reads
    # because the thing named is the day's, not the bot's.
    # "did you see the match last night" opens a conversation rather than asking for a lookup,
    # and the hedge below is the wrong reply to it. The noun has to be one a person watches: the
    # first cut of this answered "did you see the state of the kitchen" with a match reply.
    if reads_as_if_i_saw(clean, memory):
        return _choose(ASKED_IF_I_SAW_LINES, memory, clean)
    # The same ask one step along: not whether the bot watched the thing, but a detail of it, put
    # as a question to somebody who might have been there. "were jess and tom there", "did she
    # like it", "who else was there" have no lookup behind them - the day happened to the person
    # - so the hedge was a shrug dressed as help. A harm question keeps its own pools, and a
    # heavy thread is not a party to be asked about.
    if (_asked_about_the_day_they_had(clean) and not in_a_safety_thread(memory)
            and not _grief_thread(memory) and not _in_a_loss_thread(memory)):
        return _choose(WASNT_THERE, memory, clean)
    how_to = HOW_TO_DECIDE.search(clean)
    how_line = clean
    if how_to is None and repaired != clean:
        # "how should i deside" is the same ask as "how should i decide": the typed line is
        # read first, so a line that needs no repair is untouched.
        how_to = HOW_TO_DECIDE.search(repaired)
        how_line = repaired
    if (how_to is not None and not _reads(LIFE_DIRECTION.search, clean, repaired)
            and _nothing_to_choose(how_line[how_to.end():])):
        # "how should i decide" asks for the method, and the method is the one thing here the bot
        # does know: on main it went to the search hedge ("a quick search online will get you a
        # solid answer"), which is wrong for a question about how to weigh something. A line that
        # names a body, a pet or a trade still keeps its own answer, and one about a direction
        # ("how do i decide what to do with my life") has no two sides to name.
        said_words = " " + re.sub(r"[^a-z0-9']", " ", how_line) + " "
        plain = said_words.replace("'", "").split()
        if not (set(plain) & HEALTH_WORDS or set(plain) & EXPERT_WORDS
                or set(plain) & BODY_PARTS
                or any(w in ANIMALS or w.rstrip("s") in ANIMALS for w in plain)):
            return _choose(HOW_TO_DECIDE_LINES, memory, clean)
    if _reads_as_taste(clean, understood.get("words") or []):
        return _choose(UNKNOWN, memory, clean)
    # "can it be repaired", "is it fixable", "can i get them fixed": the ask is whether it can be
    # done at all, and the cost test is a poor answer to it - nothing has been said about what has
    # gone wrong, so a line about halves and second faults is a rule for a question nobody asked.
    # What decides it is the part, and the person who repairs them is the only one who can say,
    # for nothing and in a minute. This sits before the cost rule rather than inside it, so a line
    # that already has a trade behind it keeps that trade: "is the boiler repairable" was answered
    # with the plumber, and that is the better answer, so `who_settles` stands this pool down.
    # "Worth" and "bother" keep the cost test, which is the question they ask; a plain money word
    # does not, because the cost rule does not fire on "is it fixable or do i need new ones" and
    # the search hedge is what is there instead.
    # And when the answer above already spoke of a repair - "take them to an optician first: a
    # frame repair ... costs £20 to £50" - the question has been answered with the thing in hand,
    # so this generic line would talk over it.
    if (_reads(REPAIR_WHETHER.search, clean, repaired)
            and not _reads(REPAIR_WHAT_IT_IS_WORTH.search, clean, repaired)
            and not who_settles(clean, memory)
            and not _a_repair_already_spoken_of(memory)):
        return _choose(REPAIR_WHETHER_LINES, memory, clean)
    # `_reads`: "should i bother fixin it" is the same decision as "should i bother fixing it".
    # The typed line is read first, so a line that needs no repair is untouched.
    if (_reads(REPAIR_DECISION.search, clean, repaired)
            and not _reads(REPAIR_TRADE.search, clean, repaired)
            and not _reads(REPAIR_PERSON.search, clean, repaired)
            and not (_reads(LEAVING_IN_THE_LINE.search, clean, repaired)
                     and _thread_is_about_a_person(memory))
            and not _reads(REPAIR_TARIFF.search, clean, repaired)):
        if in_a_safety_thread(memory) or _grief_thread(memory) or _in_a_loss_thread(memory):
            # A thread that is a crisis or a bereavement is not a decision about a thing: "my dad
            # died last month" and "im having thoughts of ending it" were both followed by "is it
            # worth fixing" and got the paragraph about a part and a quote. The thread keeps its
            # own voice, and the one line for a line the composer cannot read in it is the one
            # that stays in the room.
            return _choose(CARE_HERE, memory, clean)
        own_thing = _names_its_own_thing(clean) or _names_its_own_thing(repaired)
        line_words = (set(re.findall(r"[a-z']+", clean))
                      | set(re.findall(r"[a-z']+", repaired)))
        # "i hate this old painting" / "should i just bin it": the it is the thread's, and the
        # thread names nothing with a part and a repair price. Only the shapes that take their
        # thing from the thread stand down this way; "is it worth getting it serviced" says the
        # money itself and keeps the rule wherever it is asked.
        #
        # A named thing is not enough on its own: a jar of flour and water is a thing, and
        # "my sourdough starter smells like acetone" / "should i chuck it" was answered with a
        # part and a quote. The rule weighs a repair against a new one, so the thread has to name
        # something that gets repaired - a machine, a fitting, a bike - and a starter, a stew or a
        # painting does not, however concrete the noun.
        no_thing_named = (_reads(REPAIR_BARE_IT.search, clean, repaired)
                          and not _thread_names_a_machine(memory))
        if not own_thing and ((_thread_is_about_the_body(memory)
                               and not _thread_names_a_machine(memory))
                              or line_words & (BODY_PARTS | SYMPTOM_WORDS | HEALTH_WORDS)):
            # A back is not a machine with a part in it. "my back keeps going" and "my knee keeps
            # giving way" were followed by "is it worth fixing" and got the paragraph about a
            # part and a quote, because the line names no thing and the thread does: the cost
            # test is the right answer to a bike and the wrong one to a body. What is worth doing
            # about a body is having it looked at, which is the same honest line the health pool
            # gives - a guess about a back is the kind of guess that does real harm.
            if _offers_to_fix_themselves(clean):
                # "is it worth fixing myself" is the joke, not the question: the person is not
                # asking whether something is wrong inside them, so the advisor's "ring 111"
                # line reads as a reply that did not hear it (sunny-barrel on #7382). The light
                # answer still says the honest test - time, and someone to look at it.
                return _choose(BODY_IS_NOT_A_MACHINE, memory, clean)
            return _choose(UNKNOWN_HEALTH, memory, clean)
        # A repair decision has a general answer, so it is not the one decision the bot has to
        # hand back: "should i bother fixing my old bike" wanted the cost test, not "not mine to
        # decide". Anything with an entry of its own never reaches here. A thread about someone
        # else never gets it either: "my husband left me" is not a thing to weigh the cost of.
        if not no_thing_named and (not _thread_is_about_a_person(memory) or own_thing
                                   or _a_thing_was_named(memory)):
            return _choose(REPAIR_RULE, memory, clean)
        # The thread is about someone, and the line names no thing of its own: "my husband left
        # me" and "is it worth fixing things with him" is a relationship, not an appliance. The
        # cost rule stands down for it (above), and what is left is the decision, which is the
        # speaker's: the hand-back belongs here rather than the search hedge it fell to, because
        # a marriage is not something to look up.
        return _choose(UNKNOWN_DECIDE, memory, clean)
    # "is that too late" / "am i too old" is the doubt a person says out loud about the thing
    # they have just told the bot they are starting. It reads as a question of fact, so it got
    # the search hedge one line after the bot had answered "im learning to swim at 40" with the
    # adult lessons that exist for exactly that. A body thread keeps its own answer: "im 34 and
    # my knee gives way when i run" / "am i too old for running" is a knee question.
    # `_reads`: "am i to late" asks the same doubt as "am i too late".
    if (_reads(TOO_LATE.search, clean, repaired) and _a_thing_they_started(memory)
            and not _hedged_recently(memory) and not _thread_is_about_the_body(memory)):
        return _choose(UNKNOWN_TOO_LATE, memory, clean)
    # The sibling doubt, about the plan rather than the age: "im doing a 10k in may" then "is that
    # realistic" was answered "a search should sort you out quickly", which sends a person to read
    # about their own training. What is missing is not information but the two facts only they
    # have, so the line asks for them - in the gentler words when the thread is heavy, where
    # "what's your starting point" is the wrong question.
    # `_reads`: "is that realisic" is the same ask as "is that realistic".
    if (_a_plan_doubt(REALISTIC.search, clean, repaired)
            or (_a_plan_doubt(REALISTIC_ABOUT_ME.search, clean, repaired)
                and _a_plan_in_the_thread(clean, memory))) and not _hedged_recently(memory):
        pool = UNKNOWN_REALISTIC_CARE if _the_thread_is_heavy(memory) else UNKNOWN_REALISTIC
        return _choose(pool, memory, clean, clean + " " + _the_line_before(memory))
    # Somebody close refusing the thing that would help them, and the person caring for them at the
    # other end: "she refuses a pendant alarm" was answered "Got it. Is there anything you'd like a
    # hand with?", and "hes 80 and wont use a stick" with "I'm here if you want to dig into any of
    # that". There is something to say - what the refusal is usually about, and the person whose
    # word carries - and a crisis, a bereavement or a safety thread keeps its own voice instead.
    said = " " + re.sub(r"[^a-z0-9']", " ", clean) + " "
    words = said.replace("'", "").split()
    # A date somebody else holds, read once here: a bare follow-up and the hedges below both
    # want it, and the reply depends on what the thread says is being waited on.
    waited = waited_for.for_the_ask(clean, repaired, memory)
    if waited is not None and waited is not waited_for.NOTHING_HELD and BARE_FOLLOW_UP.match(clean):
        # "any word yet" a turn after "i emailed the landlord about the boiler" is a wait with a
        # subject and the bare-follow-up pool answered it "I'm listening - say more if it helps".
        return _choose(waited, memory, clean)
    if BARE_FOLLOW_UP.match(clean):
        # Nothing in the thread can be read as the thing "it" or "that" is - the line reached
        # here because no entry and no record claimed it - so the reply is the ask, not a hedge.
        pool = BARE_FOLLOW_UP_CARE_REPLIES if _the_thread_is_heavy(memory) else BARE_FOLLOW_UP_REPLIES
        # Seeded on the line before as well as this one: "will it stop" after a blocked nose and
        # "will it stop" after a spray are two different threads and should not get one sentence.
        return _choose(pool, memory, clean, clean + " " + _the_line_before(memory))
    switched = _a_switch_off_asked(memory, clean)
    if switched:
        # Seeded with the line before as well: "should i turn it off" about a boiler and about a
        # dryer are different turns and should not read as the same sentence.
        return _choose(switched, memory, clean + " " + _the_line_before(memory))
    # A pointer with nothing to point at, before the hedge below and after every pool that can
    # find a subject for it: "what does that mean" and "which one" with no answer above them
    # were offered a search ("a quick search online will get you a solid answer") for a thing
    # the bot does not have in front of it, which is a pointer sent off to look itself up. The
    # line names nothing, so the help left is to say the bot cannot see it and ask for it.
    if _points_at_nothing(clean, memory, repaired):
        return _choose(POINTING_LINES, memory, clean)
    weird = _the_weird_ask_pool(clean, memory) if not _hedged_recently(memory) else None
    if weird is not None:
        # "is that weird" is the person asking whether their own reaction is allowed, and there is
        # nothing to look up. The reassurance pool answers it the way it answers "am i
        # overreacting"; the search hedge told them to go and read about it instead.
        return _choose(weird, memory, clean)
    pool = unknown_pool(clean, words)
    if pool is UNKNOWN and repaired != clean:
        # "wich one should i pick" is the same decision as "which one should i pick", and the
        # pool is chosen by the shape of the question: a typo in the shape got the search hedge,
        # which is the one answer that helps nobody. The typed line is read first, so a line
        # that needs no repair is untouched; this only fires when the typed line got no reading.
        said = " " + re.sub(r"[^a-z0-9']", " ", repaired) + " "
        words = said.replace("'", "").split()
        pool = unknown_pool(repaired, words)
    if pool is UNKNOWN or pool is UNKNOWN_DECIDE:
        missed = _a_missed_step(clean, repaired, memory, words)
        if missed is not None:
            return _choose(missed, memory, clean)
    if pool is UNKNOWN_WORRY and _a_bare_worry(clean) and _thread_is_about_the_body(memory):
        # "Should I be worried?" with no subject is about the thing they just described: a knee
        # that hurts to run on, headaches behind the eyes. That is a health question, not a
        # feeling one, so the reassurance pool stands aside.
        pool = UNKNOWN_HEALTH
    elif (pool is UNKNOWN_WORRY and _a_bare_worry(clean) and _thread_is_about_a_pet(memory)):
        # A pet keeps its own doctor: the bare ask in a thread about a dog is about the dog, and
        # the reassurance pool answers as if the person were confessing a feeling.
        pool = UNKNOWN_ABOUT_A_PET
    elif (pool is UNKNOWN_WORRY and _a_bare_worry(clean)
            and _thread_is_about_someone_else(memory)):
        # The same bare ask in a thread about somebody else is about them, not about how the
        # speaker feels: "he cant do up his buttons yet" then "should i be worried" is a question
        # about a four-year-old's hands, and the reassurance pool answered it as if the person
        # were confessing a feeling. A pet keeps its own doctor, so a thread about a dog does not
        # come here.
        pool = UNKNOWN_ABOUT_SOMEONE
    if pool is UNKNOWN or pool is UNKNOWN_DECIDE:
        # A date somebody else holds: "i ordered a new bed" / "how long do i have to wait", "the
        # engineer is coming tuesday" / "will it be fixed by friday", "i want a winter coat" /
        # "will it still be on sale next week". Nobody can look these up - the shop, the repairer,
        # the place with the booking hold them - so the reply says what is knowable about that kind
        # of wait and then names the one who settles it. It is read before the later readers that
        # shrug at a line with no subject ("that's your call, not mine - tell me what you're
        # weighing") because the thread does name it.
        # A decision with nothing in the thread to wait on keeps its own pool: "should i get the
        # bigger one" is the person's call, and the generic line says so.
        if waited and (pool is UNKNOWN or waited is not waited_for.NOTHING_HELD):
            return _choose(waited, memory, clean)
    if (pool is UNKNOWN or pool is UNKNOWN_WORRY) and not _hedged_recently(memory):
        # "is he going to be ok" after "my dad had a car accident": a question about how it will
        # go for a person the bot has never met, which the hedge answered with "a quick search
        # online will get you a solid answer". No website knows this dad. The pool names who does.
        worry = _the_pool_for_a_worry_about_them(clean, memory)
        if worry:
            return _choose(worry, memory, clean)
    if pool is UNKNOWN_WORD:
        # A line asking for a draft wants the draft offer before any advisor: "help me write a
        # text to my landlord" is about the words, not about tenancy advice.
        return _choose(_drafting_pool(clean), memory, clean)
    # "what else works", "anything else", "what about the schools": the person is asking for
    # more of an answer they have just been given, on the same topic. The bot has no more, so
    # the honest reply says that and asks which part is still open. Without this the search
    # hedge ("A quick search online will get you a solid answer") sent someone elsewhere one
    # line after the bot had answered, which reads as the bot losing the thread.
    if asks_for_more(said, memory) and not _hedged_recently(memory):
        if _answered_recently(memory):
            return _choose(HELP_ALREADY, memory, clean)
    # The line asked for something in the world - an address, a plumber, a figure, a stockist -
    # and no nameable person owns it. The hedge below says a search will sort it out, which is
    # true of every line and names neither the thing nor where to look; this says what the bot
    # cannot see and the one place that has it, in the person's own terms. It sits above the
    # person to ring, because "anybody recommend a dentist in leeds" wants one near them and not
    # "a dentist is the one to see", and it stands down on its own for every line it cannot route.
    if pool is UNKNOWN:
        routed = finding_out.for_the_ask(clean, repaired, understood)
        if routed:
            said = _choose(routed, memory, clean)
            if said:
                return said
        # A day weighed against what the person wants to do in it - "is it too hot to run",
        # "can i hang washing out today". Still not a forecast: what decides it is the same
        # every time, and that is worth saying before naming the app that has the figure.
        day = for_the_day.for_the_ask(clean, repaired)
        if day:
            said = _choose(day, memory, clean)
            if said:
                return said
    named = _advisor(memory, clean, said, words)
    if named:
        return named
    # The same ask said with a pronoun, because the thing was named a turn ago: "my tooth hurts"
    # / "who do i ring about it". The line names nothing, so the thread is read instead.
    for_the_thread = _who_for_the_thread(memory, clean, understood)
    if for_the_thread:
        return _choose(for_the_thread, memory, clean)
    # "im gonna make a spag bol tnite any tips" wants help, and nobody in the table owns it:
    # asking what they have so far is the honest way in, and it fits a bare "any tips" too.
    # "Anything I can do about it" asks for the same help as "any tips" in a shape with no
    # question word; the understanding engine flags a bare ask (one that names nothing of its
    # own), and the way in is the same. Main's guard against a line that is not a tips ask is
    # kept: a flagged line still has to be a line nobody else owns.
    if (_reads(_is_a_tips_ask, clean, repaired)
            or (understood.get("help_ask") and not NOT_A_TIPS_ASK.search(clean))):
        tips = _tips(memory, clean, repaired)
        if tips:
            return tips
        # A bare ask that comes on top of the knowledge base's own answer is not asking what
        # the person has tried: the answer they just got is the thing they are asking about
        # ("how do you spell necessary" / "and embarrass?" / "ok, any way to remember them"),
        # so "what have you tried so far" is a non sequitur. The way in is the part that did
        # not land. And a line the bot could not answer either ("my landlord wont let me have
        # a cat" / "is there any way round it") is no place to promise help: the honest hedge
        # stands, exactly as it would without the flag.
        #
        # `tips` is None here, so this line named no subject of its own and the answer behind
        # the ask is the one on the turn before - which makes it a bare ask too, however it was
        # worded: "im forgetting to drink water" / "any tips" got "tell me what you've got so
        # far" about a subject the bot had just answered in full.
        if (understood.get("help_ask") and not _reads(TIPS_ASKS.search, clean, repaired)
                and _hedged_recently(memory)):
            # The bot has already said it does not know this: a hedge is no place to
            # promise help, and there is nothing to say did not land.
            return _choose(pool, memory, clean)
        if _answered_already(memory):
            return _choose(HELP_ALREADY, memory, clean)
        return _choose(TIPS_LINES, memory, clean)
    if understood.get("tag"):
        # Nothing answered the body, so the tag is asking for agreement rather than a fact.
        # Straight after the bot's own answer, the tag is about that answer and a warm nod is
        # safe. Anywhere else this is the place the bot knows least, so it cannot agree: it
        # answers the tag without endorsing the claim, rather than handing back a search
        # hedge. A "can" claim is never nodded at. The advisor above keeps its turn ("you
        # should ring the doctor right" names who can answer).
        if _answered_already(memory) and not TAG_CAN.search(clean):
            return _choose(TAG_CONFIRM, memory, clean)
        return _choose(TAG_UNSURE, memory, clean)
    # No nameable person: fit the shape of the question ("should I take the job" and a draft
    # are not fact questions), then the plain shrug.
    #
    # A question the bot cannot answer is normally handed back honestly ("a quick search will
    # get you a solid answer"). But when the line asks again what the reply just above it
    # answered, that is not true and not useful: the answer is on the screen already. Say so, and
    # ask which part did not land. It sits after the decision hand-back, because "should i get
    # more storage" is a decision the bot says is theirs to make, and after the person to ring,
    # because naming who can help beats saying there is nothing left to say.
    if pool is UNKNOWN and _says_it_already(clean, list(understood.get("words") or []),
                                            memory):
        answer = _the_repeat_answer(memory)
        if answer:
            return _choose(SAME_AGAIN_WITH_THE_ANSWER, memory, clean).format(answer=answer)
        return _choose(SAME_AGAIN, memory, clean)
    pick = _bare_pick(clean, memory) or _bare_pick(repaired, memory)
    if pick:
        # A bare "what should i wear" is not a question with an answer nobody has: it is the
        # question a friend answers by asking where you are going. Only the lines that would
        # otherwise be shrugged at reach this, because everything with an entry has returned.
        return _choose(pick, memory, clean)
    if (_a_dead_end(clean) and not _in_a_care_thread(memory)
            and not (_news_above(memory) or _a_subject_above(memory))):
        # "where do i start" and "i dont know how to start" are the same line as "i dont know
        # what to do": nothing named, nothing to look up. They reached this shrug rather than the
        # one below it, so they are taken here too.
        return _choose(DITHER_OPEN_LINES, memory, clean)
    about_a_person = _a_question_about_the_person(clean, memory)
    if about_a_person:
        # "what do i do about my son" and "what should i do about my neighbour" reached this
        # shrug - a search pointer for a person in their own life. It is the last thing before
        # the shrug, so every reading above keeps its own answer.
        return about_a_person
    if pool is UNKNOWN and A_STEP_ASK.match(str(clean or "").strip()) and _news_above(memory):
        # A bare ask for a next step on top of news, with no way in: "i got a letter about a
        # court date" then "what now" got "I'd rather not guess - a quick search online will get
        # you a solid answer", the worst line this file has for somebody with that on their
        # plate. It comes after the ask pool, so a thread where the ask pool has a way in keeps
        # it; this is only the turn that would otherwise be shrugged at.
        return _choose(BARE_PICK_AFTER_NEWS, memory, clean)
    if pool is UNKNOWN:
        # A question nothing in the file can answer, where the conversation says what it is about:
        # "what should i bring her", seven turns into a chat about a mother in a care home, is the
        # visit being asked about, and the reading carries that from the turn that named the home
        # (`care_home` with shape "bring"). Nothing above answered it, so the search hedge was said
        # to a person asking what to take on a visit to their mother.
        care = _a_care_home_line(understood, memory)
        if care:
            return care
    price = _a_price_wants_a_verdict(clean, memory)
    if price and pool is UNKNOWN:
        # A price asked to be judged with the thing left out: the hedge below sends somebody to
        # search for an answer no search has, because a number on its own settles nothing. It comes
        # after every pool above, so a line with a way in keeps it (UNKNOWN_MONEY keeps its adviser,
        # and a line that names the thing never reaches here).
        return _choose(price, memory, clean)
    if pool is UNKNOWN:
        # Where the answer is kept: "A quick search online will get you a solid answer" names no
        # place, so the person is no closer than before they typed. STYLE.md's "Not knowing,
        # honestly" shows the shape that works - the limit, then where that kind of answer
        # actually lives, then the part the bot can do. The kind is read from the line's own
        # words (their own account, a shop's stock and price, an official rule, a timetable, a
        # listing, a medicine, a benefit, a surgery's notes); a line that names no kind keeps the
        # plain hedge, because a wrong place is worse than no place.
        # A question about the bot itself is the one kind no place can answer: nobody has
        # written down whether this program gets bored, so the hedge ("A quick search online
        # will get you a solid answer") is nonsense as well as cold. The bare ask is answered
        # above; these are the same asks with a tail on them.
        mine = the_bots_own_answer(clean)
        if mine is None and repaired != clean:
            mine = the_bots_own_answer(repaired)
        if mine is not None:
            return _choose(mine, memory, clean)
        rule = _the_rule_for_it_for_the_turn(clean, repaired, memory)
        if rule is not None:
            # What settles this kind of ask, said where the band would otherwise only shrug. A
            # pointer on its own - "the seller's site has today's figure" - says nothing about
            # the thing asked about and leaves a person exactly where they were, and it was the
            # commonest shape in this band: a price, an amount, a keeping question and a time
            # each have one thing that always decides them, and that thing is knowledge the bot
            # does have. No place is named yet, because a place pool reads "how much does a
            # tattoo cost in leeds" as the model number off a label. Nothing is lost by that: a
            # rule is classed with the hedges (see `RULE_HEADS`), so any module with a real
            # answer, or the composer's own, still takes the turn over it.
            return _choose(rule, memory, clean)
        # How busy somewhere is now is not one of the kinds a page holds: no account, stock list,
        # rule, timetable or listing has today's queue. A crowd word in the line used to lose to
        # the first noun the pools knew - "is the recycling centre busy today" was answered about
        # the council's recycling rules - so a crowd ask is not read as one of these kinds at all,
        # and `bot/compose/findout.py` answers it under this band.
        place = None if findout.reads_as_crowd(clean) else the_place_the_answer_is_kept(clean)
        if place is None and repaired != clean and not findout.reads_as_crowd(clean):
            place = the_place_the_answer_is_kept(repaired)
        if place is not None:
            return _choose(place, memory, clean)
    if pool is UNKNOWN or pool is UNKNOWN_WORRY:
        # An ask about the person's own feeling is not a look-up: "what should i do about the
        # guilt", "how do i forgive myself", "what is wrong with me" all reached the search hedge,
        # which sends somebody off to read about themselves. Asked here, at the last place before
        # the hedge, so every pool, advisor and place above keeps its turn; the reader stands down
        # on its own for any line that names a thing (see `bot/compose/own_ask.py`).
        from . import own_ask
        own = own_ask.answer(clean, memory)
        if own:
            return _choose([own], memory, clean)
    if pool is UNKNOWN:
        # A method asked for in the person's own voice, with nothing in the file able to answer
        # it: "how do i practise", "how do i start running", "where should i hang my washing".
        # The search hedge is the one answer that helps nobody here - nobody looks up how to do
        # their own evening - and the way in is what they have tried so far. Read last, so every
        # pool above keeps its own answer, and only for the shape it names.
        method = method_ask_pool(clean, memory)
        if method is None and repaired != clean:
            method = method_ask_pool(repaired, memory)
        if method is not None:
            return _choose(method, memory, clean)
    counted = _a_countdown_in_a_care_thread_(memory, clean, repaired, understood)
    if counted:
        return counted
    return _choose(pool, memory, clean)


def _a_countdown_in_a_care_thread_(memory, clean, repaired, understood):
    """The countdown branch, imported on the first call to keep the two modules apart."""
    from .fallback_chain import _a_countdown_in_a_care_thread  # noqa: PLC0415 - no import circle
    return _a_countdown_in_a_care_thread(memory, clean, repaired, understood)


def _the_view_asked_for(clean, memory):
    """The bot's own view, given back, when that is all the line asks for.

    Only one turn back, and only when that turn answered something: after a hedge there is no
    view to give the person, and "my view has not changed" on the back of "I don't know enough"
    is a worse non-answer than the hedge itself.
    """
    if not _is_a_view_ask(clean):
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        # Nothing has been said yet, so there is no answer to stand behind - and no subject in the
        # line either. The hedge sends them off to search for their own opinion.
        # Unless the line names somebody: "what do you think of me" carries its subject with it,
        # and the pool that answers a question about the bot itself answers that one. A first
        # person word is the only mark of it there is, since nothing else has been said.
        if VIEW_NAMES_SOMEBODY.search(clean):
            return None
        return _choose(VIEW_NO_SUBJECT, memory, clean)
    last = turns[-1]
    said = str(last.get("bot") or "").strip()
    if not said:
        return None
    if _only_the_floor(said):
        # An offer to listen or to help ("Go on - I'm listening.", "Happy to help - tell me what
        # you've got so far") follows the answer it was made about, so the view is that answer.
        # It steps back one turn and no further: a run of two offers has no answer behind it, and
        # past them is another subject - walking on from a shrug about the garden landed on the
        # car's handbrake, which is worse than standing down.
        answered = [t for t in (memory.get("turns") or [])
                    if isinstance(t, dict) and str(t.get("bot") or "").strip()
                    and t is not last and turns.index(t) < turns.index(last)]
        if not answered:
            return None
        last = answered[-1]
        said = str(last.get("bot") or "").strip()
        if _nothing_to_stand_behind(said):
            return None
    if not (ack.reads_as_a_receipt(said) or _in_a_pool(said, (NEUTRAL,))):
        # A receipt that opens a reply with the answer after it is answered here: the view is
        # the answer, not the receipt in front of it.
        said = _the_answer_in_reply(last.get("user"), said) or said
    while ack.reads_as_a_receipt(said) or _in_a_pool(said, (NEUTRAL,)):
        # A receipt and a neutral line both leave the answer where it was, so the view is the
        # answer they came after: "but my mum says its too soon" was met with "Got it - but your
        # mum says it's too soon", and the honest view of "what would you do" is still what the
        # bot said about moving in, not the receipt. The walk goes on past a run of them: two
        # polite turns in a row are still nothing to stand behind, and stopping at the first
        # one quoted the second receipt or gave up on the answer behind both.
        answered = [t for t in (memory.get("turns") or [])
                    if isinstance(t, dict) and str(t.get("bot") or "").strip()
                    and t is not last and turns.index(t) < turns.index(last)]
        if not answered:
            return None
        last = answered[-1]
        said = str(last.get("bot") or "").strip()
    if _only_a_reaction(last.get("module"), said):
        # A congratulations and a question, with nothing claimed in it: the honest answer is
        # that the news is the whole of it.
        return _choose(VIEW_ON_GOOD_NEWS, memory, clean)
    if str(last.get("module") or "") in CARE_MODULES:
        # Care is not an opinion: after a crisis line or a death, the answer to anything at all
        # is not "my view has not changed". After sympathy the ask gets company instead of the
        # search hedge ("my dog died" / "honest view?" was "I don't know enough to answer that
        # honestly. A search should sort you out quickly"); after a crisis or a safety line the
        # care module owns the turn and this one stands aside.
        if str(last.get("module") or "") in ("loss", "grief"):
            return _choose(VIEW_AFTER_A_DEATH, memory, clean)
        return None
    if any(phrase in said.lower() for phrase in VIEW_HANDBACK):
        # A decision the pool itself handed back. Quoting a refusal back as a view ("My view:
        # not mine to decide, sorry") is the same wall twice, and the search hedge it replaces is
        # worse, because no search settles whether to buy the bike. The second answer says what
        # the decision turns on instead.
        return _choose(VIEW_DECIDE, memory, clean)
    if _is_a_hedge(said):
        # Nothing was answered, so there is no view to stand behind.
        return None
    if VIEW_MIRROR.match(said.lower()) and not _reads_as_a_claim(said) \
            and not _the_view_of(said)[0]:
        # Sympathy is company, so there is no claim to give back as a view - and standing down
        # is not neutral either: the turn fell through to the search hedge, so "i feel low" /
        # "honest view?" was answered with "a quick search online will get you a solid answer".
        # The pool written for exactly this says the thing was heard and that there is nothing
        # to weigh on top of it, which is the honest answer to a view asked for on sympathy.
        #
        # Only when the answer after the opener says nothing: "Sorry to hear that. A walk and
        # someone to talk to usually help more than sitting with it" does say something, and
        # telling the person there is "nothing to add" on top of advice the bot just gave drops
        # the one thing in the turn worth standing behind. That shape falls through to the claim
        # reader below, and `VIEW_MIRROR_LINES` says the bot would say it again without calling
        # sympathy a position it has held (`test_a_feeling_mirrored_back_is_not_a_view`).
        return _choose(VIEW_COMPANY, memory, clean)
    if not _reads_as_a_claim(said):
        # A feeling mirrored back, or a question asked back, is not an answer: the person is
        # asking the bot to stand behind something it never said. An answer that opens by
        # mirroring the feeling and then says something is the exception: the claim after the
        # opener is what the person is asking about, and reading the whole reply as company sent
        # "i feel low" / "honest view?" to the search hedge.
        first = re.split(r"(?<=[.!?])\s+", said.strip())[0].strip().lower()
        if not (VIEW_MIRROR.match(first) and _the_view_of(said)[0]):
            return None
    headline, mirrored = _the_view_of(said)
    if not headline:
        if mirrored:
            # The answer was company and nothing else, so there is no view to stand behind and
            # no lookup to send them to either.
            return _choose(VIEW_COMPANY, memory, clean)
        return None
    # The answer carries a claim, so the view is that claim said again. A reply that opened on a
    # mirrored feeling gets the frame that says the bot would say the same thing again rather than
    # one that calls it the bot's own position: after "sorry to hear that" the sympathy is not a
    # stance the bot has held, and "my view has not changed" on top of it claims one. A claim that
    # is itself a question keeps the question frame whatever the reply opened with: "That still
    # stands: anything good in it?" stands behind a question the bot asked rather than a thing it
    # said.
    if headline.endswith("?"):
        # The answer above was a question asked back, so the line that carries it has to be the
        # question put again rather than a stance with a question mark on the end.
        lines = VIEW_ASK_LINES
    elif mirrored:
        lines = VIEW_MIRROR_LINES
    else:
        lines = VIEW_LINES
    return _choose(tuple(line.format(said=_after_a_colon(headline)) for line in lines),
                   memory, clean)
