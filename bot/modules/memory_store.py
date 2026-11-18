
"""The memory store at work: remember what the user says, and answer questions about it.

PRIORITY 7000 (README routing bands: memory recall that must lead). It observes every line and
keeps the shared keys in bot/memory/; it only proposes a reply when the user asks about the
conversation itself ("what did I say my job was?", "what were we talking about?"), so it passes
on every ordinary question.

One exception, in the same spirit: when the person hands a choice back ("you pick", "your
call"), the answer is one of the options the bot itself offered a turn ago, so the store reads
the bot's own last reply for them (bot/memory/choice.py).
"""
import copy
import datetime
import random
import re

from ..compose import pick
from ..compose.recall import with_a_tail
from ..memory import (content, current, forget, forms, is_follow_up, keywords, last_bot,
                      last_module, last_user, log, name, note, others, plan_line, plan_sentence,
                      recent, remember, remember_answer, remember_other, resumed, return_target,
                      stem, thread, user, you)
from ..memory import ack
from ..memory.places import (A_QUESTION_ASKED, NOT_A_PLACE_VALUE, OTHER_PLACE, OTHER_PLACE_PRONOUN,
                             PLACE_ENDS, _a_place, _a_town_moved, _asked_person, _other_place,
                             _said_places, _the_place_alone)
from ..memory import change as a_change
from ..memory import cause as a_reason
from ..memory.spoken import _spoken_as_numbers
from ..memory import pending
from ..memory import another as second_half
from ..memory import choice as choose
from ..memory import condition
from ..memory import decided
from ..memory import company
from ..memory import spent
from ..memory import surname as family_name
from ..memory.filler import without_filler, without_the_end_shrug
from ..memory import guest
from ..memory import plans
from ..memory.named import carries_a_name
from ..memory.taste import ASKS_ABOUT_A_TASTE, ASKS_FOR_TASTES, TASTE_ASKED_ABOUT
from ..memory.taste import read_all as read_tastes
from ..memory import facts as extract
from ..knowledge import cooking
from ..knowledge import units
from ..knowledge.maths import solve
from ..memory import counts as how_many
from ..memory import rates as rates_reader
from ..memory.times import keep as _keep_the_times
from ..memory.times import answer as _the_time_they_said
from ..memory.times import is_a_time_ask as _a_plain_time_ask
from ..memory import history
from ..memory import narrow
from ..memory import hours as hours_after
from ..memory import named as named_thing
from ..memory import recall
from ..memory import reminded
from ..memory import carry as about_the_choice
from ..memory import resize
from ..memory import reject as turned_down
from ..memory import repair as a_repair
from ..memory import told as told_about
from ..memory import whathurts as a_hurting_part
from ..memory.when import (already_answer, asks_what_today_is, the_part_asked, until_answer,
                             when_answer)
from ..memory.topics import ACKS, GREET, STOPWORDS
from ..memory import topics as _topics
from ..memory.repeat import HEDGE as _HEDGE
from ..memory import repeat as repeat_the_line
from ..memory.topics import subject as topic_subject
from ..memory.thread import about as _about_the_chat
from ..understanding import breeds, understand
from ..understanding.normalize import fix_typo, normalise
from ..understanding.kinds import the_manners_question
from ..understanding.topics import PLACES


from ..memory.store_lines import (  # the pools, moved out whole: see bot/memory/store_lines.py
    PRIORITY,
    ANSWERS,
    RECALL_HINTS,
    SELF,
    NOT_THE_PLAN,
    NOT_ON_A_MEDIUM,
    REPEAT_ADVERB,
    LIMITS,
    DENIAL_SAY,
    CORRECTED_SAY,
    RETRACT_SAY,
    NOT_RETRACTED,
    _FACT_SLOT,
    PET_AGE_FIX_WORDS,
    OTHER_SAID,
    OTHER_KIND_SAY,
    AGE_FIX_WORDS,
    NAME_FIX_WORDS,
    NAME_GIVEN_WORDS,
    UNIT_FAMILY,
    FACT_FAMILY,
    NOT_A_UNIT,
    AMOUNT_WORD,
    SPELLING_APART,
    CORRECTION_SAY_DROP,
    DROP_LISTS,
    CORRECTION_SAY,
    CORRECTION_SAY_PAIR,
    PET_RENAMED_SAY,
    BARE_ECHO_ONLY,
    CORRECTION_BACK,
    AT_TIME_VALUE,
    KIN_ASK,
    IN_LAW_AFTER_TEXT,
    PRONOUN_FITS,
    CHILD_RELATIONS,
    _ABOUT_WHO,
    CHILD,
    CHILD_OF,
    FAMILY_GROUP,
    FOOD_PHRASES,
    ADVICE_MODULES,
    SLOT_KEY,
    BARE_SLOTS,
    WHERE_ASK,
    KIN,
    BAD_NEWS,
    _UNIT_SAID,
    _AMOUNTS,
    _AMOUNT_WORDS,
    _COUNT_WORD,
    _CONVERT,
    _WEEKLY,
    FIGURE_UNITS,
    FIGURE_TIME,
    FIGURE_NUMBER,
    FIGURE_QUALIFIER,
    LOOK_BACK_FIGURE,
    FIGURE_ANSWER_LEN,
    COUNT_WORD,
    PLACE_NOT,
    TURNED,
    PART_HELD,
    PART_KEYS,
    KEPT_THINGS,
    NAMED_BY,
    RESTATED_KEYS,
    SWAPPABLE,
    _TENS_WORDS,
    CORRECTED_AGAIN,
    CORRECTED_AGAIN_WHO,
    CORRECTED_WHICH_PERSON,
    CAT_NAMES,
    DOG_NAMES,
    SMALL_NAMES,
    NAME_ADVICE,
    RESUME,
    NO_PLANS_REPLY,
    WEEK,
    TAIL_WINDOW,
    PLURAL_PEOPLE,
    DIET_RULES_OUT,
    DENIAL_WORDS,
    DENIAL_STEMS,
    CHILD_RELATIONS,
    GROUP_OF,
    RELATION_ALIKE,
    MONTH_ORDER,
    HAVE_ANY_WORDS,
    HER_WORD,
    DIET_FOOD,
    PERSON_GROUP,
    PLURAL_PEOPLE,
    OWNED_BY_THE_VERB,
    PREGNANT_OWN_SAY,
    PREGNANT_SAY,
    PREGNANT_WEEKS_SAY,
    LIMIT_SAY,
    FEEDING_SAY,
    STATE_WAS_SAY,
    PET_WORDS,
    PRONOUN_PEOPLE,
    SAME_FACT_THEIR_OWN,
    CONDITION_RULES_OUT,
    CONDITION_KEEPS_DOWN,
    CAR_CAPS,
    NUMBER_WORDS,
    _SUBJECT_KEYS,
    PLURAL_PETS,
    COUNT_WORDS,
    A_SHORT_ANSWER,
    KEY_SLOT,
    CONCEPTS,
    POSSESSIVE,
    QUOTE_LEADS,
    ASKED_LEADS,
    NOTHING_STARTED,
    POINTS_BACK_NOTHING,
    POINTING_WORD_NOTHING,
    WHAT_I_SAID_NOTHING,
    RESTRICT_OPENS,
    CALL_LEADS,
    LENGTH,
    WORD_NUMBERS,
    UNIT_SECONDS,
    BUDGET_FITS,
    BUDGET_MORE,
    BUDGET_TIGHT,
    ANY_FIGURE,
    HELD_THREAD,
    GRIEF_WORDS,
    CLOSE_PLAIN,
    CLOSE_HEAVY,
    CHANGE_PLAIN,
    CHANGE_HEAVY,
    CHECK_NOTHING_SAID,
    CHECK_A_FEELING,
    CHECK_A_QUESTION,
    CHECK_PLAIN,
    CLOCK_SAID,
    ROUTINE_SUBJECT,
    ROUTINE_SAY_BACK,
)
from ..memory.enough import enough_reply
# The reader's own tests call it through this module, and so does anything written against the
# store before the move: the three names it reaches for are kept here, pointing at the one copy.
from ..memory.enough import _amounts, _near_bare_range, _target
_enough_reply = enough_reply
from ..memory.relations import (ABOUT_PERSON_ASK, AGE_ADVERB, AGE_AGAIN, AGE_ASK,
                          AGE_AS_A_CAUSE, AGE_COPULA, AGE_DETERMINER, AGE_PERSON_WORD,
                          AGE_RULE_WORD, AGE_SAID, AGE_WORD, AGE_YOU_SAY, ANOTHER_PERSON,
                          BREED_ASK, CHAT_TAIL, CHILD_WORD, GROUP_ASK, GROUP_NAMES_TYPED,
                          GROUP_NAME_ASK, GROUP_WORDS, HAVE_ANY, NAME_AGAIN, PERSON_AFTER,
                          PET_ASK, PLURAL_ANIMAL, THEIR_AGE, THEIR_JOB, THEIR_NAME,
                          THEIR_TASTE_A_YES_NO, THEIR_TASTE_INTO, THEIR_TASTE_WHAT,
                          THEY_ARE_NAMED, THE_KIDS, _PET_WORD, _PLURAL, _a, _a_kept_person,
                          _a_list_of_names, _a_list_of_words, _a_or_any,
                          _a_person_in_the_store, _a_pet_age, _a_plural_list,
                          _a_word_the_store_knows, _age_is_about_a_person, _ages_reply,
                          _ages_sentence, _animal_family, _ask_gender, _called,
                          _canon_relation, _continues_an_about_ask, _did_you_mean,
                          _every_line, _folded, _gender_of, _in_the_group,
                          _just_gave_an_age, _kin_forms, _mentioned_the_group,
                          _more_than_one, _more_than_one_word, _named_person,
                          _newest_first, _one_age, _person_from_pronoun, _pet_age_reply,
                          _pet_ages, _pet_ages_sentence, _pet_named, _plural_person,
                          _pronoun_fits, _pronoun_for, _relation_reply, _relations_of,
                          _same_as_last, _same_name, _same_name_however_they_wrote_it,
                          _same_thing, _the_group_names_typed, _the_group_was_said,
                          _the_group_word, _the_names_a_pronoun_gave,
                          _the_names_of_the_group, _the_names_they_typed, _their_job,
                          _their_taste, _they_like_sentence, _tidy_name,
                          _whether_they_have, _with_article)

from .memory_tables import (
    ASK_WITHOUT_MY,
    CALENDAR_SAID,
    COUNT_ANIMAL,
    COUNT_BARE,
    DAY_ASKS,
    DAY_IT,
    DAY_OF_MONTH,
    DAY_THING,
    ELIDED_AGAIN,
    ELIDED_ASK,
    ELIDED_NAMES,
    ELIDED_NOT_SURE,
    ELIDED_WORDS,
    HOW_MANY_OF_MINE,
    MEMORY_POINTER,
    MISSED_CATCH_UP,
    PLAN_ASKS,
    PLAN_MINE,
    POINTS_BACK,
    SAID_ASK,
    SAID_AS_A_SENTENCE,
    THAT_DATE,
    TIME_ASKS,
    TIME_IT,
    TIME_THING,
    TOPIC_ASK,
    WEEKDAY_WORD,
    WHAT_I_SAID,
    WHEN_ASKS,
    WHEN_END_ASK,
    WHEN_END_WORD,
    WHEN_INVERTED,
    WHEN_INVERTED_SUBJECT,
    WHEN_PLAN,
    WHEN_QUALITY,
    WHEN_START_ASK,
    WHEN_THING,
    WHEN_THING_VERB,
    WHEN_VAGUE,
    WHEN_VERB,
    WHERE_PLAN,
)








# "what did i just ask you?" is the ask about their own question. A time or a pointer after
# "about" ("about earlier", "about before", "about it") is still that ask about the whole
# conversation; a real subject ("what did i ask about my boiler") is a recall of that one thing
# and belongs to another reader, so it keeps the turn.
# A line that says the answer missed is not the ask "what did i ask": "thats not what i asked" and
# "that isnt what i asked you" carry the ask's words in the middle of a complaint, and the store
# answered them as a recap ("You haven't asked me anything yet." in a chat with a question in it).
# The miss itself is answered by bot/memory/warmth.py, so the store only has to keep out of it.

# "what else did i say about my sister" is the ask "what did i say about my sister" with the
# person saying there may be more of it. The store answers with the lines it has, so the word is
# dropped before matching and every recall reader works on the same words: what did i say, what
# else did i say, what more did i tell you, anything else i said.

# A question about how the conversation began ("what did I ask you first?"), not about the
# world and not about one fact. The store answers it from memory["turns"].
# The same ask with the "did" left out, which is the shape a reminder leaves behind: `_bare` takes
# "remind me" / "can you remind me" off the front, so "remind me what i said at the beginning" and
# "can you remind me what i asked you first" arrive here as "what i said at the beginning" and
# "what i asked you first". Read on its own as well as in FIRST_ASK, because the gate in
# `_about_this_chat` has to know the line is about the chat or it never reaches the answer.



# A request for the last reply again ("say that again", "what did you say?"). It is a question
# about the conversation, so the answer is the bot's own last turn, read from memory["turns"].
# "what you said" and "what you said to do" are the same request without the subject flipped
# ("remind me what you said" used to fall through to the small-talk fallback).
# The asks that mean the line on the screen and not the thing behind it: "what did you just say"
# and "pardon" want the last line back even when it was only a nod, because the person is asking
# about what they did not catch, not for the advice again.
# The content words a repeat ask is made of: anything else means the line is about that thing
# ("what did you say about the cake"), not a request to hear the last reply again.
# A line that asks for the whole of the answer and names nothing of its own: "in full", "the
# whole thing", "from the top", "all of it". No entry can answer these, and `answers` read them as
# a thing to hand the answer to, so the person asking for the lot got one line of it under a
# lead-in that names nothing they said:
#
#     how much water should i drink / in full
#       "The same goes for the full: If you forget, keep a filled bottle ..."
#     how much water should i drink / in full
#       "Alright then - good luck with it."   (the closer, on "all of it")
#
# The answer is on the screen and they want all of it, so the line is the repeat ask it is: the
# store hands the whole of its last answer back, under a lead-in that says that is what it is.
# Anchored at both ends, because "the whole chicken" and "all of it was gone" name things.

# Only a question or a request asks for the reply again: "i said that again to him" and "my
# sister said that again" are news about someone talking, not a request to the bot.


# People ask to be reminded in their own words, and the reminder is not part of the ask:
# "remind me what I'm allergic to", "my name again?", "sorry, what was my budget". Take the
# wrapper off before matching, so one pattern in the plain form serves every phrasing. The
# chat-speak an ask arrives in ("whats", "im") is folded the same way.
# A line that asks to be reminded of something states nothing to keep. "remind me when i am
# going to rome" names Rome, and the plan reader took the name for a plan of its own, so the
# store filed "Rome" and then answered a later question from it. Only the asking words are
# listed: "remind me to ring the dentist" does state something, and it keeps being kept.
REMIND_QUESTION = re.compile(
    r"\bremind me\b[^.!?]{0,24}\b(?:what|when|where|who|whom|whose|how|which|why|if)\b|"
    r"\bremind me\b(?:[\s,]*(?:again|please))*[\s,]*$", re.I)
# The chat itself named after the ask - "what did i say at the start of this chat", "what was my
# first message in our conversation". The words after it say which conversation, and there is
# only ever the one, so they are a wrapper like "again": off they come before any recall reader
# sees the line. Without it every ask in the family worked until the person named the chat, and
# then reached nothing at all and was handed the shrug.
# "what about my budget?" is the same recall as "my budget?" once the budget has been the
# subject: the ask is there, in a shorter wrapper.


# "What was I making?" asks about the line they said out loud, not the newest one: a detail about
# it ("hes allergic to nuts") keeps the subject, and a statement about something else ends it.
# "What am I doing wrong?" is a question about the thing itself, not a recall: the ask has to end
# where the plan is named, so a word of complaint after it keeps the line for the module that
# answers it.
# The asks that want the list of plans rather than the line they said: "what am i planning" is
# about what is coming up, "what am i doing" is about the thing in their hands.
# The asks about what they are up to that name neither a plan nor an activity: "what am i up to?"
# is about what is coming up when the line before it said something coming up, and about the
# thing in their hands when that line said what they are doing. "what was i cooking?" is not one
# of these - it names the cooking, and the line about the cooking answers it - and neither is
# "what am i doing?", which is about the thing in their hands.
# A reply that is not a fact: the honest "you have not told me" and the guesses. The store says
# one when it has nothing to say back, so a line answered that way is not a fact of theirs.
NOT_A_FACT = re.compile(r"\bhaven't (?:told|said|mentioned|given|got)\b|\bhaven't your\b"
                        r"|\bdon't know\b|\bnot sure\b|\bnothing comes to mind\b"
                        r"|\bdidn't say\b|\bnever told\b|\bno idea\b", re.I)


def _a_kept_fact_read(text, memory):
    """True when the line asks back a fact they gave, in whatever words, and the store has it.

    "my budget is 300" ... "im going to rome in may" ... "whats my budget" was answered with
    the cost of a day in Rome. The ask carries no topic of its own, so the arbiter read the
    conversation's topic on it and handed the turn to the module that declares that topic. A
    recall of a fact they gave is not about the topic in the air, so the store takes it as it
    comes - the same rule a plan asked for and the line they said already have.

    The key is read by `recall.ask`, which knows the shapes and not the store, so the fact has
    to be one the store really holds: with nothing kept the line is left to the entries, which
    can answer it as advice.
    """
    if not isinstance(text, str) or not (user(memory) or {}):
        return False
    try:
        if not recall.ask(text):
            return False
        said = respond(text, copy.deepcopy(memory))
    except Exception:  # noqa: BLE001 - a hook that raises must not lose the turn
        return False
    if not said or not str(said).strip():
        return False
    return NOT_A_FACT.search(str(said)) is None


def _their_own_line_ask(text, memory):
    """True on the one ask the store must win even against a topic entry: their own line back.

    "what was my plan?" is read as the topic the plan is about ("what paint should i use for a
    hallway?" then "what was my plan?" was answered by the money entry), and the store's own plan
    line is the answer.

    "what was i cooking?" is read as a cooking line, and the cooking entry answers a different
    question - a chilli recipe for a chilli they had already told us they were making, and the
    recipe's timings for "how long does that take" after it. The person asked what they said,
    not what to do. The store answers only from a line they really said, so this is said for
    exactly the asks whose answer is that line, and every other line the store proposes on is
    left to the arbiter's own rules.
    """
    try:
        low = _bare(text) or ""
        if PLAN_MINE.search(low):
            return bool((user(memory) or {}).get("plans") or (user(memory) or {}).get("plan"))
        if not ACTIVITY_ASK.search(low):
            return False
        return bool(_activity_line(memory))
    except Exception:  # noqa: BLE001 - a hook that raises must not lose the turn
        return False


# The asks that name the activity they want back: "what was i cooking?" is not "what were we on".
# The "what was I doing" line says it with an -ing verb ("I'm making a cake"), or as a plan
# ("I want to bake a cake", "I'm going to fix the tap"). The stricter set is tried first.
# A question they asked is not a line about what they were doing: "what was i making?" must not
# come back later as the thing they said they were making.
# The words that open a line about something we were already talking about ("hes allergic to
# nuts", "its a bosch, about three years old") rather than a statement of their own.




# What the repaired line may fill in, and what it may not. The list used to be of keys it could
# fill, which meant every fact added later was invisible to it: "my birfday is the 3rd of may" was
# repaired to "my birthday is the 3rd of may" by the understanding engine, read as the typed line
# by the store, filed as a plan, and then denied a line later ("you haven't told me your birthday
# yet"). So it is the other way round: the repair may fill any fact, and the keys it may not are
# the ones that are not facts about the world but about what the line is doing - a plan is the
# line said back in their own words, and a take-back is read off the word as typed.
NOT_FROM_THE_REPAIR = frozenset("""plan plans drop retract correction""".split())


def _with_repaired(found, text, memory, kind):
    """The facts the understanding engine's own repairs make plain.

    The store read the line as it was typed, so a word the engine had already repaired hid the
    fact from it: "im alergic to peanuts" filed nothing at all, and "im alergic to peanits" filed
    a food called "peanits". The repaired line is read as well, and a fact is taken from it only
    where the typed line gave nothing for that key - so this can add what a typo hid, and cannot
    overwrite what they actually said.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    plain = understood.get("plain") if isinstance(understood, dict) else None
    if not isinstance(plain, str) or not plain.strip():
        return found
    if plain == " ".join(str(text).split()):
        return found  # nothing was repaired, so there is nothing new to read
    more = extract.extract(plain, question=(kind == "question")) or {}
    for key, value in more.items():
        if key not in NOT_FROM_THE_REPAIR and not found.get(key) and value:
            found[key] = value
    # A list of facts about other people is not one fact. The typed line can name the person and
    # one thing about them while the repair is what makes the other plain: "my mums 70 n she
    # loves gardning" reads the hobby as typed, and the age only once it is repaired. Taking the
    # repaired list only when the typed one was empty threw the age away because the hobby was
    # there, so the person is merged key by key instead.
    if found.get("others") and more.get("others"):
        for entry in more["others"]:
            if not isinstance(entry, dict) or not entry.get("who"):
                continue
            known = next((one for one in found["others"]
                          if isinstance(one, dict) and one.get("who") == entry["who"]), None)
            if known is None:
                found["others"].append(dict(entry))
                continue
            for key, value in entry.items():
                if key != "who" and not known.get(key):
                    known[key] = value
    return found


# The words that make a place word a common noun instead: "a bath and an early night" is a bath,
# and a person who lives in Bath does not want it handed back as the city.
NOT_A_NAME_BEFORE = re.compile(r"(?:\b(?:a|an|the|some|another|his|her|their|our|your|my)\s+)$",
                               re.I)
# One word deep is not enough to tell the city of Bath from a hot one. Bath, Reading, Nice, Sale,
# Deal and Wells are all answers to "where do you live", so the town comes back in store replies
# that are about something else: "You're planning a hot Bath tonight", "Everything is on Sale",
# "Start Reading for twenty minutes". Only the place that reads as a place is written - where a
# name is normally said: after a preposition or a travel word, with the number in chat-speak
# ("going 2 spain") allowed between, or where a name is at the front of a sentence.
THE_PLACE_IS_NAMED = re.compile(
    r"(?:^|[.!?;:]\s+|\n|\b(?:to|in|into|from|at|near|of|around|through|toward|towards|via|"
    r"going|coming|off|back|flying|travelling|traveling|moving|heading|headed|staying|visiting|"
    r"visit|bound|left)\s*(?:\d+|two|three|four|five|six|seven|eight|nine|ten)?\s*)$", re.I)


def _the_places_are_written_as_names(reply, memory):
    """A place the store holds is written the way the store holds it.

    A plan is kept and quoted in the words they typed, which is right for the plan and wrong for
    the name in it: "we r going 2 spain in may" came back as "You r going 2 spain in may.", and
    "im going to lisbon in may" as "You're going to lisbon in may." The line that named the place
    told the store the name ("Spain", "Lisbon"), so the reply is written with it. Only a place the
    store is holding is touched, and a determiner in front of the word says it is a common noun,
    not a place: "You're planning a bath and an early night" is not the city of Bath.
    """
    known = user(memory)
    if not isinstance(known, dict) or not isinstance(reply, str) or not reply.strip():
        return reply
    names = [name for name in (known.get("places") or []) if isinstance(name, str) and name.strip()]
    city = known.get("city")
    if isinstance(city, str) and city.strip() and city not in names:
        names.append(city)
    if not names:
        return reply
    out = reply
    for name in names:
        pattern = re.compile(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", re.I)

        def swap(match, name=name):
            before = match.string[max(0, match.start() - 28):match.start()]
            if NOT_A_NAME_BEFORE.search(before):
                return match.group(0)
            if not THE_PLACE_IS_NAMED.search(before):
                return match.group(0)
            return name

        out = pattern.sub(swap, out)
    return out


def note_the_hours(text, memory):
    """Keep the kind of week the line names, for the follow-up on the next turn.

    The reading is bot/memory/ack.py's (`_hours_family`), so the six shapes are written down in
    one place: a night shift, an early start, a late finish, long shifts, a rota that moves, and
    working from home. Asked here rather than in the reply, because the hours are often answered
    by a knowledge entry that never reaches the ack module, and the following line - "does that
    get easier", "i never know when to stop" - is the same follow-up however it was answered.
    """
    if not isinstance(text, str) or not text.strip():
        return
    # The week has to be theirs. "my son wakes at five" is his morning, and "i work nights, my
    # back is killing me" is a line about the back: the understanding engine reads that one as
    # health and the son's morning as family, while the lines this is for read work, or read no
    # topic at all ("i start at six so im up at five").
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(understood, dict):
        topic = understood.get("topic")
        if topic and topic != "work":
            return
    try:
        from ..memory import ack
        family, _pool = ack._hours_family(text.lower())
    except Exception:  # a reading that cannot run must not cost the store the turn
        return
    if family:
        hours_after.note(memory, family)


def _a_detail_does_not_replace_the_job(found, memory):
    """A line that only says when or where they work keeps the job they already gave.

    "im a nurse" then "i work nights" put "nights" in the store as their job and dropped the
    nurse, so "and my job?" answered "You work nights" and the one fact they had given was gone.
    A shift is a detail of the work, and a detail does not take the place of the fact.

    The same for where they work: "im a teacher" then "i work in a school" said back "You work in
    a school" and the teacher was gone, so "what do you know about me" lost the role altogether.
    A place is a detail beside the role, and the summary now says both.
    """
    if "job" not in found:
        return found
    held = (user(memory) or {}).get("job")
    held_frame = str((user(memory) or {}).get("job_frame") or "")
    said = found.get("job")
    if not held or not said or str(held) == str(said):
        return found
    said_frame = str(found.get("job_frame") or "")
    said_weight = extract.work_weight(said, said_frame)
    if said_weight < extract.work_weight(held, held_frame):
        kept = dict(found)
        kept.pop("job", None)
        # The frame belongs to the job it was said with: keeping "work" beside the nurse they
        # already told us would say "you work nurse".
        kept.pop("job_frame", None)
        # It is still something they told us, so it is kept as what it is - when or where they
        # work, beside the job - rather than thrown away: memory then says both ("you're a
        # nurse; you work nights", "you're a teacher; you work in a school") instead of one of
        # the two going missing.
        if said_weight == 2:
            kept["workplace"] = (said_frame + " " + str(said)).strip()
        else:
            kept["shift"] = said
        return kept
    if extract.is_a_place_of_work(held_frame) and found.get("job_frame") is None:
        # The role is said second: "i work in a school" then "im a teacher". The school stays
        # beside it as where they work, rather than being overwritten by the role.
        if not (user(memory) or {}).get("workplace"):
            found["workplace"] = (held_frame + " " + str(held)).strip()
    if "job_frame" not in found:
        # A role said on its own is "you're a nurse", never "you work nurse": the frame belongs to
        # the line it was said with ("i work nights"), and left in the store it carries over.
        (user(memory) or {}).pop("job_frame", None)
    return found


# The words a question opens with. A line that opens with one of them, or carries a question mark,
# is an ask, and an ask is where a shrug on the end is dropped.
ASK_OPENERS = frozenset("""what whats which when where who whose why how hows
do does did is are was were am can could should would will shall have has had
any anyone anything""".split())


def _without_the_shrug_at_the_end(text):
    """The line without the chat-speak hung on the end of it, when that leaves words behind.

    `bot/memory/filler` holds the shrugs people put on the end of a line, and everything the store
    says back reads a line through it. What the store *files* did not, so the shrug became part of
    the thing told: "how old is my son by the way" reached no reader at all and was answered with
    the search hedge, and "when do we go to cornwall by the way" filed a place called "cornwall
    bies the way" and said it back: "You go to cornwall bies the way in August."
    """
    said = " ".join(str(text or "").split())
    words = said.lower().strip(" .,!;:").split()
    if "?" not in said and not (words and words[0] in ASK_OPENERS):
        # The shrug is dropped from an ask, and from an ask only. "i meant 43 actually" is a
        # correction, and the word on the end of it is part of how it reads: with the shrug gone
        # the correction went to the greeting and the line "43 - got it, 43 it is" was lost.
        return said
    clean = without_the_end_shrug(said)
    return clean if clean and clean != said else said


def observe(text, memory):
    """Remember what the line says, and note a second animal of a kind as the turn's news.

    Everything below writes what the line says. This wrapper is here because the one thing the
    store does with the result is not a fact but the turn: a line that leaves the store holding
    two cats called Milo and Max is a line about the two of them, and the reply should say so.
    The wording is not read - "no my other cat is called max", "no we also have a cat called max"
    and "i also have a cat called tom" all file the second cat, and all three were left to the
    greeting, which answered with the person's own line and "Got it" in front of it. A rule per
    phrasing would have covered two of the three; the store's own record covers every phrasing.
    """
    before = _the_pets_on_record(memory)
    # The readers below file pets, and the line that names an animal files one even when it is
    # putting a name right ("no the cat is called max" in a house of two cats filed a third).
    # The set the turn before held is carried so that entry can be told from a pet of its own.
    memory["_pets_before"] = before
    hurt_before = a_hurting_part.before(memory)
    try:
        _observe(text, memory)
    finally:
        memory.pop("_pets_before", None)
    a_hurting_part.after(memory, hurt_before)
    _note_a_pet_that_is_new(text, memory, before)
    try:
        _the_limit_they_share(text, memory)
    except Exception:  # noqa: BLE001 - the store never crashes a turn
        pass


def after(text, reply, memory):
    """Keep a correction the chat was given, whichever module gave the reply to it.

    "how long does a chicken take to roast" / "i meant a turkey" reads right on the turn that says
    it - the turkey row answers the correction by itself - and the chat was still on the chicken:
    asked "what about a duck" the next line reached no row at all and got a search hedge. Whether
    the bookkeeping happened used to depend on which module won the turn, because each module
    replies to its own copy of the memory and only the winner's copy is kept. The correction is
    the chat's, not the reply's, so it happens here, once, after the reply has been chosen.
    """
    try:
        a_repair.keep_the_correction(text, memory)
    except Exception:  # noqa: BLE001 - the store never crashes a turn
        pass


# The ages in words, for saying a group of children back the way the store says them elsewhere
# ("Two kids, four and six").
AGES_IN_WORDS = {int(number): word for word, number in extract.FIGURE_WORDS.items()}


def _the_ages_of_the_children(text, memory):
    """The reply for the ages of the children the store counts, given one at a time, or "".

    "i have two kids" then "ones 7 and ones 4": the second line names no group word, so every
    reader for a group passes it on, the store kept nothing, and the composer handed the line back
    ("Got it - ones 7 and ones 4."). The ages are the answer to "how old are they?", so they are
    kept and said as ages. A bare list of figures is read only when the line before counted the
    children, because "7 and 4" on its own could be anything.
    """
    if not isinstance(memory, dict):
        return ""
    held = user(memory).get("kids")
    if not isinstance(held, int) or held < 2:
        return ""
    # Ages already on the group are a correction, and `matters.a_corrected_age` reads those: a
    # second full list here would overwrite the ages one at a time.
    if any(len(entry.get("ages") or ()) > 1
           for entry in others(memory) if isinstance(entry, dict)):
        return ""
    ages = extract.ages_said_one_by_one(text, held)
    if not ages:
        return ""
    if not (extract.the_ones_are_given_one_at_a_time(text) or _the_count_was_the_line_before(memory)):
        return ""
    remember_other(memory, {"who": "kids", "ages": ages}, text)
    # Said in the order the person gave them: "ones 7 and ones 4" is seven and four, and the store
    # keeps that order everywhere else.
    words = [AGES_IN_WORDS.get(age, str(age)) for age in ages]
    said = ", ".join(words[:-1]) + " and " + words[-1] if len(words) > 2 else " and ".join(words)
    return pick(["{} — got it.".format(said[:1].upper() + said[1:]),
                 "Got it — {}.".format(said),
                 "{}.".format(said[:1].upper() + said[1:])], memory)


def _the_count_was_the_line_before(memory):
    """Whether the line before this one counted the children, so a bare list of ages is theirs."""
    said = str((memory.get("topic") or {}).get("text") or "")
    return bool(re.search(r"\b(?:kids?|children|child)\b", said, re.I))


def _the_pets_on_record(memory):
    """The (animal, name) pairs the store holds, for comparing one turn with the next."""
    held = set()
    if not isinstance(memory, dict):
        return held
    for pet in user(memory).get("pets") or ():
        if not isinstance(pet, dict):
            continue
        held.add((str(pet.get("animal") or "").strip().lower(),
                  str(pet.get("name") or "").strip().lower()))
    return held


def _note_a_pet_that_is_new(text, memory, before):
    """A line that leaves two of an animal on record is answered as a line about the two.

    Nothing is read out of the words: the store is compared with itself, so a phrasing nobody
    wrote a rule for is answered the same as the ones people type most. A first pet is left
    alone - bot/memory/ack.py already answers the line that gives one ("A cat called Milo.
    What's it like to live with?") - and so is a rename, which leaves one animal behind.
    """
    if not isinstance(memory, dict):
        return None
    held = memory.get("correction")
    if isinstance(held, dict) and held.get("said") == " ".join(str(text or "").lower().split()):
        return None  # the line has already been read as a correction, and that is its answer
    added = _the_pets_on_record(memory) - before
    pets = [pet for pet in (user(memory).get("pets") or ()) if isinstance(pet, dict)]
    for animal, name in sorted(added):
        if not animal or not name:
            continue
        same = [pet for pet in pets
                if str(pet.get("animal") or "").strip().lower() == animal and pet.get("name")]
        if len(same) < 2:
            continue
        memory["correction"] = {"key": "pets_more", "value": name, "animal": animal,
                                "said": " ".join(str(text or "").lower().split()),
                                "text": text}
        return memory["correction"]
    return None














def _observe(text, memory):
    from ..memory import not_this as ruled_out_place
    if ruled_out_place.the_place_ruled_out(text, memory):
        # A place they ruled out is not a place they are going: "im going to spain" / "we arent
        # going to portugal" filed Portugal as a second place and answered with its card. The
        # line states nothing to keep, so nothing below it is read.
        return
    understood = memory.get("understood")
    # The kind of week their hours make, kept for the turn after it: "does that get easier",
    # "i never know when to stop" are about the week just described, and the reply is written in
    # bot/memory/hours.py. It is noted here rather than where the reply is written because the
    # hours line is often answered by a knowledge entry ("my rota changes every week") that never
    # reaches bot/memory/ack.py, and the follow-up is the same follow-up either way.
    note_the_hours(text, memory)
    # How many of a thing they have, kept as the number: "i have three brothers" was filed as one
    # brother, so "how many brothers do i have" said the store did not know. Noted here, beside the
    # hours, because the line that says it is often answered by another module.
    how_many.observe(text, memory)
    # A family name is a second name and not the one they are called: "my last name is okafor" was
    # filed as nothing, and "whats my surname" a turn later said the chat had never said one. It is
    # kept here, beside the count, because a line that gives one is often answered by another
    # module, and the file has to be there whichever module takes the turn.
    family_name.observe(text, memory)
    # The paragraph a plan announcement implies is kept for the next line rather than given now:
    # "im getting married in june" wants a warm word and a question, which the composer has, while
    # "what do i do first" wants the plan's own first step. It is kept here, in observe, because
    # each module works on its own copy of memory and only the chosen module's copy is kept: a
    # plan recorded by whichever module happened to answer is lost whenever the composer has the
    # turn (sturdy-poppy, #1848).
    planned = plans.answer(text, memory) if isinstance(text, str) else None
    if planned:
        memory["plan_answer"] = {"text": planned, "user": text}
    kind = understood.get("kind") if isinstance(understood, dict) else None
    if not isinstance(text, str):
        return
    # A remembering frame can carry the telling in the same line: "can you remember my sisters
    # name is amy" asks about the store and gives it a name. The frame states nothing - what
    # follows it is a line the store already knows how to read - so it is read as if it had been
    # said on its own. Left whole, the line filed the sister and not her name, and the reply to it
    # told a person who had just given the name that the store had nothing on her.
    said = _behind_a_remembering_frame(text)
    if said:
        text = said
    if recall.ask(text) or _reads_the_store(text, memory):
        return  # a question about what is already known states nothing new to keep
    if REMIND_QUESTION.search(text):
        return  # so does asking to be reminded, whatever the ask names
    if _asks_about_someone_else(text):
        # A yes/no question about someone else asks what is on record, so the frame itself
        # states nothing: "is he allergic to peanuts" must not file peanuts. A line that asks
        # and then tells ("does my mum eat meat? she is vegetarian") is two lines in one, and
        # the telling is kept: the frame is cut off and the rest is read as the statement it
        # is, or nothing is filed at all when the frame is the whole line.
        rest = _after_the_yes_no_frame(text)
        if not rest:
            return
        text = rest
    if isinstance(text, str) and _statement(text):
        # "do i live in york?" / "am i a baker?" / "am i right?" ask about the person; they state
        # nothing, so nothing is filed from them. Without this the question's own hypothetical
        # becomes the fact ("i live in leeds" then "do i live in york?" left York in the store)
        # and "am i right?" was filed as a name.
        return
    # A chat that weighs two things and picks one keeps the choice: "im thinking of getting a
    # cat" then "actually a dog" is a decision, and "what did i decide to get" is a question
    # about it. Read here because the line is a statement the store's own readers pass over.
    decided.observe(text, memory)
    # "im travelling with my mum": who is going with them is a fact about the chat, and
    # "who is coming with me" three turns later is answered from it (bot/memory/company.py).
    company.observe(text, memory)
    memory.pop("pet_age", None)  # an age taken last turn is not news for this one
    _keep_the_times(text, memory)
    # "i go to the gym twice a week" is a rate of their own doing, filed so a late "how often
    # was that again" is answered from it rather than asked back (bot/memory/rates.py).
    rates_reader.keep(text, memory)
    found = extract.extract(text, question=(kind == "question"))
    if not found:
        # "im an accountant" then "actually an engineer rather than an accountant": the person
        # says the correction on its own, and the subject is the turn before's.
        found = extract.a_correction_without_a_subject(text, last_user(memory))
    if not found.get("name"):
        # "can you remember my name" then "sam": the answer to the bot's own question, which no
        # pattern of the line's own words can read.
        answered = _their_name_answered(text, memory)
        if answered:
            found["name"] = answered
    found = _with_repaired(found, text, memory, kind)
    if not found.get("kids"):
        # "actually there are three of them": the number said back about the people in hand, with
        # no word for the people in the line at all. `kid_count` reads the count in front of the
        # word ("my three kids") and nothing here, because which people it counts is the store's
        # question: the children, when they are what the turn before was about.
        counted = extract.count_of_the_people(text, memory)
        if counted:
            found["kids"] = counted
    if not found.get("budget"):
        # Chat-speak hides the amount: "ive got 60 pounds to spend" is a budget once the folded
        # line reads "i have got 60 pounds to spend", so the folded line is read for the fact.
        folded = _folded(text, memory)
        if folded and folded != " ".join(text.lower().split()):
            budget = extract.extract(folded, question=(kind == "question")).get("budget")
            if budget:
                found["budget"] = budget
    if found.get("budget") and not re.search(r"[\u00a3$\u20ac]", found["budget"]):
        # "ive got £60 to spend": the folded line is plain words, so the sign is read off the
        # line they typed and put back on the amount.
        budget = str(found["budget"])
        sign = _budget_sign(text, budget)
        if sign:
            found["budget"] = sign + budget.lstrip()
    correction = found.pop("correction", None)
    if correction is None:
        # "its Preeya not Priya": a correction with no marker in front of it is only one when the
        # store already holds the value it takes back, which is the store's question, not the
        # reader's.
        correction = _a_correction_without_a_marker(text, memory)
    dropped = found.pop("drop", None)
    retracted = found.pop("retract", None)
    if not found.get("allergies"):
        # "im allergic to peanuts" then "and milk too": the line names one more thing and no
        # fact of its own, so it is the allergy on record with the milk in it. A food word on its
        # own is not enough - nothing is added to an allergy the person never gave.
        more = extract.one_more(text)
        held = (memory.get("user") or {}).get("allergies") or []
        if more and held:
            found["allergies"] = [item for item in more if item not in held]
    # Someone named in this same line comes first: "my mum is allergic to nuts and she doesnt
    # eat meat" is two facts about the mum, not one about the mum and one about nobody.
    named_here = [who for who in (found.get("people") or []) if isinstance(who, str)]
    _remember_dislikes(text, memory, named_here)
    second = _a_second_persons_limit(text, memory)
    if second:
        # Filed with the rest of this line's people, so it is logged and merged like any other: the
        # reader is the only one that knows the limit, because the limit is the line before's.
        found.setdefault("others", []).append(second)
    for entry in found.pop("others", []) or []:
        pronoun = entry.pop("pronoun", None)
        if not entry.get("who"):
            if pronoun and pronoun not in ("she", "he"):
                # "they" is nobody in particular, so the age is not the last person's: "my son is
                # 7" then "theyre 70 next month" is not the son's seventieth birthday, and folding
                # it onto him took the age the plain line gave away. Kept for the "how old are
                # they" ask instead, where the answer is about the same "they".
                age = _a_number(entry.get("age"))
                if age:
                    memory["their_age"] = {"age": age, "turns": entry.get("turns") or ""}
                continue
            who = _person_from_pronoun(text, memory, named_here)
            if pronoun:
                # "she's 78 and doesn't walk far" in a chat about her mum: the age goes on the
                # mum, never on the dad the chat was on before, because the pronoun has to fit.
                fits = extract.SHE if pronoun == "she" else extract.HE
                who = who if _pronoun_fits(who, fits) else ""
            if not who:
                if pronoun in ("she", "he") and isinstance(entry.get("months"), int):
                    # An age in months said with only a pronoun is still the chat's fact: "rough
                    # night, the baby was up 3 times" then "shes 4 months" names nobody the store
                    # can file it on, and dropping it made "how old did i say she was" say she had
                    # never said. Kept against the pronoun, the same way "they" is, so the ask
                    # about her can answer it.
                    entry["pronoun"] = pronoun
                    remember_other(memory, entry, text)
                continue  # a pronoun and nobody to put it on is not a fact about nobody
            entry["who"] = who
        if pronoun and "age" in entry and CORRECTING.search(str(text or "")):
            # "my son is 7 kilos" stores no age; "actually hes 8" then corrects nothing, so
            # it must not become the first age he has. A correction replaces a fact.
            known = next((one for one in others(memory) if one.get("who") == entry["who"]), None)
            if not (known and "age" in known):
                continue
        was = next((dict(one) for one in others(memory)
                    if one.get("who") == entry.get("who")), None)
        remember_other(memory, entry, text)
        _note_a_corrected_fact(memory, text, entry, was)
        _note_a_fact_moved(memory, text, entry, was)
    found = _a_detail_does_not_replace_the_job(found, memory)
    held_name = str((memory.get("user") or {}).get("name") or "")
    for key, value in found.items():
        remember(memory, key, value, text)
    if (found.get("name") and held_name
            and str(found["name"]).lower() != held_name.lower()):
        # A name that arrives when another is already on record is the name put right, whether
        # or not the line carries a correcting word: "im tom" then "i go by tomas" was answered
        # as a first introduction - "Hi Tomas - good to meet you" - one line after meeting Tom,
        # and the old name went without a word. Said as the correction it is, the person hears
        # which name the bot goes with.
        memory["name_fixed"] = {"name": str(found["name"]), "from": held_name,
                                "said": " ".join(str(text or "").lower().split())}
    if found.get("job") and not found.get("job_frame"):
        # A job said plainly ("i'm a chef now") is said back the same way: the frame belongs to
        # the job it was said with, so "i work in a warehouse" then "i'm a chef" is not "in a
        # chef" - the old frame goes with the old job.
        (memory.get("user") or {}).pop("job_frame", None)
    # A name put right moves the name on the one pet it is about, and the "last pet" reader below
    # would otherwise drop that name on whichever pet came last: "i have two cats called milo and
    # tom" then "no hes called max" renamed Tom and then Milo, leaving one cat called Max.
    _fix_a_pets_name(text, memory)
    if "pets" not in found:
        _name_the_last_pet(text, memory)
        _age_the_named_pet(text, memory)
        _age_they_answered(text, memory)
        _age_said_of_the_only_animal(text, memory)
        _fix_a_pets_age(text, memory)
    _fix_a_persons_age(text, memory)
    _fix_the_weeks_of_a_pregnancy(text, memory)
    fixed = _fix_a_persons_name(text, memory)
    if fixed:
        # The correction is the turn's news: the summary has the new name, and the reply says
        # both halves so the person knows the old one is gone.
        memory["name_fixed"] = dict(fixed, said=" ".join(str(text or "").lower().split()))
    if "owns" not in found:
        _fix_the_make_of_a_thing(text, memory)
    _the_name_they_gave_to_the_person_they_mean(text, memory)
    _a_trip_booked_named(text, memory)
    if correction:
        _apply_correction(memory, correction, text)
        _fix_a_pets_name(text, memory)
        return
    if dropped and _drop_value(memory, dropped, text):
        return
    if retracted and _retract_last(memory, text):
        return
    _forget_denied(text, memory)
    _the_back_on_the_plate(text, memory)
    if _about_this_chat(text, memory):
        return
    if told_about.a_callback_the_chat_has(text, memory):
        # "remember when i said my knee hurt" names a thing the conversation is already on, so
        # the line adds no subject: filing it made "remember" a word of the topic, and the turn
        # after it ("its better now") was read against remembering and answered with a revision
        # tip. A callback naming something the chat does not hold ("remember when we talked
        # about lisbon") does say what the conversation is on, so that one is filed as usual.
        return
    # A line that put a value right is the turn's news, not a new subject: the conversation is
    # still on the thing the value belongs to. Noted as a topic, "my dog is called rex" then
    # "his names actually rocky" left the chat on a subject whose only word was "name", and
    # "how old is he" after it was answered with a tip on remembering names instead of with the
    # dog. The record the correction fixed stays the current one, so the next line about the
    # dog is read against the dog.
    if not _this_line_put_something_right(memory, text):
        note(memory, text, kind)


def _a_trip_booked_named(text, memory):
    """A trip that is already booked is a trip the chat is on, and the store keeps it.

    "we booked a cottage in cornwall for august" was answered about Cornwall and then kept
    nothing: "where are we going" said "You haven't said - where are you going?", and a correction
    after it had no plan to land on. The place is filed, and the plan in the shape the other trips
    are kept in ("Cornwall in August"), unless the store is already on that plan.
    """
    from ..memory import trips
    place, when = trips.the_trip_they_booked(text)
    if not place:
        return
    known = user(memory)
    if not isinstance(known, dict):
        return
    place = place[:1].upper() + place[1:]
    plan = " ".join(f"{place} in {when}".split()) if when else place
    places = [str(one) for one in known.get("places") or [] if str(one).strip()]
    if place.lower() not in {one.lower() for one in places}:
        remember(memory, "places", place, text)
    if str(known.get("plan") or "").strip().lower() != plan.lower():
        # The plan is the last thing the line states, the way a trip said as a plan keeps it, so a
        # correction after the booking moves the trip rather than the place on its own.
        remember(memory, "plan", plan, text)
        remember(memory, "plans", plan, text)


def _this_line_put_something_right(memory, text):
    """Whether this very line is the correction one of the readers has just applied."""
    said = " ".join(str(text or "").lower().split())
    if not said:
        return False
    for key in ("correction", "name_fixed"):
        kept = memory.get(key)
        if isinstance(kept, dict) and said == " ".join(str(kept.get("said") or "").split()):
            return True
    return False


# The diets that keep meat off the plate, so taking one back is what "meat is back on the
# table" answers. Keto and paleo are not answered that way.


def _on_record_before(memory, records):
    """The animals an earlier line put on record, out of the ones this line has just taken back.

    A take-back only says itself when there was something to take back. "i dont have a rabbit"
    from someone who has a cat is a thing they never had, and "Right \u2014 no rabbit, then."
    answers a line they did not say; the ordinary answer to it is the one they get.
    """
    said = " ".join(str((turn or {}).get("user") or "").lower()
                    for turn in (memory.get("turns") or []) if isinstance(turn, dict))
    words = {stem(word) for word in re.findall(r"[a-z']+", said)}
    kept = []
    for record in records or []:
        if not isinstance(record, dict):
            continue
        for word in (record.get("animal"), record.get("name")):
            if word and stem(str(word).lower()) in words:
                kept.append(record)
                break
    return kept


def _forget_denied(text, memory):
    """A line that says they do not have a fact takes the old one out of the store.

    "im coeliac" and then "im not coeliac", "im allergic to peanuts and nuts" and then "im not
    allergic to nuts": the same fact being taken back. A store that keeps it goes on warning
    about, or cooking around, the thing the person has just said they are fine with.
    """
    held = (memory.get("user") or {}).get("pets") or []
    denied = extract.denials(text, held)
    # A denial about somebody else comes back under its own key and comes off that person's
    # record, not the user's: "my son is allergic to nuts" then "he isnt allergic to nuts" left
    # the nuts on his list and answered "Your son is allergic to nuts." after the line that took
    # them back.
    theirs = denied.pop("theirs", None) if isinstance(denied, dict) else None
    # A pet that died is one they no longer have, but it is not a take-back to say back to them:
    # the loss is answered warmly, and "Right - no cat, then." is the wrong reply to a death.
    # The store still hears it, or it hands the animal back later ("what pets do i have" after
    # "my cat died" must not answer "You've got a cat called Milly.").
    died = [pet for pet in _losses_taking(text, held, memory)
            if str(pet.get("animal") or "") not in
            [_kind(item) for item in (denied.get("pets") or [])]]
    # "we gave one away" out of "i have two cats" names no animal, only a number: one cat goes,
    # and the store keeps the count straight instead of answering "You've got two cats."
    given = [pet for pet in extract.given_away_one(text, held)
             if pet not in [item for item in (denied.get("pets") or []) if isinstance(item, dict)]]
    if not denied and not theirs and not died and not given:
        return None
    gone = {}
    for key, value in denied.items():
        if key == "diet":
            value = _the_diet_they_are_back_on(memory, value)
        dropped = forget(memory, key, value, "gone")
        if key == "pets":
            # The store forgets either way; only a pet they had before is worth saying back.
            dropped = _on_record_before(memory, dropped)
        if dropped:
            gone[key] = dropped
            if key == "pets" and "*" in [str(item) for item in value]:
                # "no pets" took them all: the line says that, not the last animal left.
                gone["pets_all"] = True
    if died and forget(memory, "pets", died, "died"):
        gone["pets_died"] = True
    if given and forget(memory, "pets", given, "given away"):
        # One of a set is gone, not the whole kind: "Right - no cat, then." would say they have
        # none left, so the store hears it and the turn is answered like any other.
        gone["pets_given"] = True
    for entry in theirs or []:
        taken = _off_their_list(memory, entry, text)
        if taken:
            gone.update(taken)
            break
    if not gone:
        return None
    gone["said"] = " ".join(str(text or "").lower().split())
    memory["denial"] = gone
    return gone


def _the_back_on_the_plate(text, memory):
    """A line that puts back what somebody else does not eat takes it off their record.

    "my son doesnt eat fish" then "actually he eats fish": the store kept "no fish" against him
    and went on answering "what does my son eat" with "Your son doesn't eat fish.", which is the
    opposite of the last thing the person said. A taste is the same shape - "my wife hates
    mushrooms" then "actually she loves them" puts mushrooms on her likes and off her dislikes.
    Only what is already on that person's record is lifted, so a line that describes somebody for
    the first time ("my son eats fish") is left to the modules that read it on its own.
    """
    for said in extract.their_back(text):
        who = str(said.get("who") or "").strip() or _person_from_pronoun(text, memory)
        if not who:
            continue
        for record in others(memory):
            if str(record.get("who") or "").lower() != who.lower():
                continue
            kind = said.get("kind")
            food = str(said.get("food") or "").strip()
            if food.lower() in ("them", "it", "that"):
                # "actually she loves them" names the food only by pointing at it, and there is
                # one thing on her record to point at or the line cannot be read at all.
                food = _the_one_they_are_back_on(record, kind)
            if not food:
                continue
            if kind == "diet":
                held = str(record.get("diet") or "").lower()
                if held not in ("no " + food.lower(), "no " + food.lower() + "s"):
                    continue
                # The restriction is gone and the food they do eat takes its place: the record
                # says "eats fish" so "what does my son eat" answers with it, not with a blank.
                record["diet"] = "eats " + food
            else:
                gone = [str(item) for item in (record.get("dislikes") or [])]
                if food.lower() not in [item.lower() for item in gone]:
                    continue
                record["dislikes"] = [item for item in gone if item.lower() != food.lower()]
                likes = [str(item) for item in (record.get("likes") or [])]
                if food.lower() not in [item.lower() for item in likes]:
                    likes.append(food)
                record["likes"] = likes
            memory["reversal"] = {"who": who, "food": food, "kind": kind,
                                  "said": " ".join(str(text or "").lower().split())}
            return True
    return False


def _the_one_they_are_back_on(record, kind):
    """The one thing on a person's record a "them" can point at, or "" when there are two.

    "my wife hates mushrooms" then "actually she loves them" is mushrooms because they are the
    only thing she does not like; with mushrooms and olives both on the list the pointing word
    says nothing, and guessing one of them would put a taste in her mouth she never gave.
    """
    if kind == "diet":
        held = str(record.get("diet") or "").strip()
        return held[3:].strip() if held.lower().startswith("no ") else ""
    gone = [str(item) for item in (record.get("dislikes") or [])]
    return gone[0] if len(gone) == 1 else ""




def _off_their_list(memory, entry, text):
    """The take-back a line makes about somebody else, taken off the record kept for them.

    "my son is allergic to nuts" then "he isnt allergic to nuts": the store files facts about
    other people under their own entry, so the denial has to find that entry and name the person
    it belongs to when it says the note back - "Nuts back on the table, then." reads as the
    speaker's own allergy, which they never mentioned.

    The note is said even when they never had it on record: "my daughter is 6" then "she isnt
    allergic to eggs" is a thing the person said about her, and the fallback's "I'm listening"
    is no answer to it.
    """
    items = [str(item) for item in (entry.get("allergies") or []) if str(item)]
    if not items:
        return None
    who = str(entry.get("who") or "") or _person_from_pronoun(text, memory)
    if not who:
        return None
    taken = []
    for record in others(memory):
        if str(record.get("who") or "") != who:
            continue
        held = [str(item) for item in (record.get("allergies") or [])]
        left = [item for item in held if item.lower() not in {one.lower() for one in items}]
        if len(left) == len(held):
            continue
        taken.extend(item for item in held if item not in left)
        record["allergies"] = left
    return {"allergies": items, "who": who}


def _the_diet_they_are_back_on(memory, value):
    """The diet as the store holds it, when the take-back names only the food.

    "im cutting out sugar" is kept as that whole phrase, and the line that takes it back can
    name nothing but the food - "im back on sugar", "im eating bread again". Matched against the
    phrase word by word, or `forget` finds nothing and the store goes on telling them to avoid
    what they eat now.
    """
    held = (memory.get("user") or {}).get("diet")
    said = " ".join(str(value or "").lower().split())
    if not isinstance(held, str) or not said:
        return value
    if said in " ".join(held.lower().split()):
        return held
    return value






def _the_last_line(memory):
    """The line just before this one, so a bare "he died" can point back at what it named.

    "i have a dog" then "he died" is the dog; "my grandad is in hospital" then "he died" is the
    grandad. Without the turn behind it a "he" says too little, and taking the only animal off the
    store on that is the worst thing this reader could do.
    """
    turns = (memory or {}).get("turns") or []
    if not turns:
        return ""
    return str((turns[-1] or {}).get("user") or "")


# The units a line can name a size in, folded to one spelling each: the answer writes "2kg" and
# the person types "2 kg", "2 kilos" or "2 kilograms", and they are the same size. Without the
# fold, "its 2 kilos" is a size the answer never worked out and the turn is an acknowledgement.


# The words that leave a line nothing but the size: "its 2kg", "mine is about 2 kilos", "2kg",
# "i have a 2kg one". A line with anything else in it asks something of its own and belongs to
# whoever reads that ask.

# A time, for the clause of an answer that has worked its own rate out: "1 hour 40 minutes".








# A line that asks whether the amount in hand will do for a number of people: "is that enough for
# four", "will that feed six", "does it do eight", "enough for a dozen". The head count is the part
# the answer needs, so it is read off the line and nowhere else.
# The head counts said in words, kept small: a table is a number somebody can count, and a figure
# past twelve is a line about something else ("enough for 20 minutes").
# Grams in one of the weights a size is said in.
# The birds, whose portion is the shop's half a kilo on the bone (units.BIRD_GRAMS) rather than
# the meat row: "chicken" sits at 200g in the portion table because a breast is meat off the bone,
# and a whole bird read as that row says a 2kg chicken feeds ten.
# The portion an answer states in its own words: "About 200 g of chicken each", "500g a person on
# the bone", "About 75 g of dry rice each". The answer's own figure is the one on the screen, and
# it beats the table when the two disagree - the bird table says half a kilo on the bone where
# the meat answer says 200g of chicken each, and a person reading that answer is holding 200g.
# The size an answer worked its own arithmetic out for: "so a 2kg bird takes roughly 1 hour 40",
# "so 300 g for four". The rate's own size ("per 500g") is the rule, not the thing in hand.




# A line that says what they made rather than asks: "i only made 200g", a turn after an answer that
# worked a total out for a head count. The "only" is the person saying they are short, and the
# answer already holds both the count and the figure it asked for.
# The head count an answer worked its total out for: "so 300 g for four", "1.2 kg for six".














def _losses_taking(text, held, memory=None):
    """The animals a line about a death takes off the store, one record at a time.

    "my cat died" from someone with two cats is one of them: the store keeps the other instead of
    answering "you haven't told me about a pet yet" a turn after they grieved one. "both cats
    died" is the whole lot.
    """
    said = str(text or "").lower()
    everything = bool(extract.LOSS_ALL.search(said))
    taken = []
    before = _the_last_line(memory)
    for kind in extract.losses(text, held, before):
        same = [pet for pet in held if isinstance(pet, dict)
                and _animal_family(pet.get("animal")) == _animal_family(kind)]
        if not same:
            continue
        if everything:
            taken.extend(pet for pet in same if pet not in taken)
            continue
        named = [pet for pet in same if pet.get("name") and
                 re.search(r"\b" + re.escape(str(pet["name"]).lower()) + r"\b", said)]
        # "rex died in january" is about Rex and not about Sam: the animal they named goes.
        taken.append(named[-1] if named else same[-1])
    return taken




def _last_stated(memory):
    """The facts the line before this one put in the store."""
    said = " ".join(str(last_user(memory) or "").lower().split())
    if not said:
        return []
    kept = []
    for entry in log(memory):
        if not isinstance(entry, dict):
            continue
        if " ".join(str(entry.get("text") or "").lower().split()) != said:
            continue
        kept.append(entry)
    return kept


def _retract_last(memory, text=""):
    """A line that takes back the last thing they said without naming it: "take that back", "scratch
    that".

    "im allergic to peanuts and shellfish" then "take that back" left the allergy on record and the
    next ask answered "You told me you're allergic to peanuts, shellfish" - a note they had just
    asked to take off. A retraction names no value, so the only thing it can be about is the line
    before it: every fact that line put in the store goes. A taste or a fact about someone else is
    left alone - those are not what "take that back" means, and losing them silently would be worse
    than keeping them.
    """
    gone, shown = [], []
    for entry in _last_stated(memory):
        key = entry.get("key")
        value = entry.get("value")
        if key == "pet":
            # The animal is taken off the record outright, not filed under `pets_gone`: that list is
            # for a pet that died or went to a new home, and answering "you don't have your dog
            # Biscuit any more" tells them about a loss they never mentioned.
            known = user(memory)
            pets = [pet for pet in (known.get("pets") or []) if pet is not value and pet != value]
            if len(pets) != len(known.get("pets") or []):
                if pets:
                    known["pets"] = pets
                else:
                    known.pop("pets", None)
                gone.append("pets")
                animal = (value or {}).get("animal") or (value or {}).get("name") or "pet"
                shown.append(str(animal))
            continue
        if key == "plans":
            known = user(memory)
            if forget(memory, "plans", [value]):
                gone.append("plans")
                shown.append(str(value))
            if known.get("plan") == value:
                known.pop("plan", None)
            continue
        if key in NOT_RETRACTED:
            continue
        dropped = forget(memory, key, value)
        if dropped:
            gone.append(key)
            shown.extend(str(item) for item in dropped
                         if not isinstance(item, dict))
    if not gone:
        return None
    if any(key in ("plans", "places") for key in gone):
        # The trip went with the plan, so the where ask names what they took back instead of an
        # empty store ("You haven't mentioned a place yet" denies the trip they just discussed).
        # As the store held it, not lower-cased: the place is a name, and "Sri Lanka is off" is
        # the trip said back where "Sri lanka" is the line read aloud.
        user(memory)["plan_dropped"] = str(shown[0])
    memory["retraction"] = {"said": " ".join(str(text or "").lower().split()),
                            "keys": gone, "shown": shown}
    return memory["retraction"]




def _reads_the_store(text, memory=None):
    """True for a line that only asks for something already kept, so it states nothing new.

    `facts` extracts what a line mentions, and an ask mentions the very thing it wants back:
    "i'm allergic to nuts" then "am i allergic to peanuts or shellfish?" used to keep both and
    answer *you're allergic to nuts, peanuts or shellfish* - a claim they never made.

    An ask about a person's allergy or a food they cannot have is the same kind of line: it
    names nothing of its own and asks for a fact the store keeps ("my son is allergic to nuts"
    then "what is he allergic to" was answered with what an allergy is, by a topic entry that
    matched the word). Said with nobody the store knows, it claims nothing.
    """
    if not isinstance(text, str):
        return False
    low = _bare(_folded(text, memory))
    if NAMED_FACT_ASK.search(low) or TOPIC_ASK.search(low) or ASK_WITHOUT_MY.search(low) \
            or HOW_MANY_OF_MINE.search(low):
        return True
    if not (OTHER_FACT.search(low) or CANT_HAVE.search(low) or CAN_HAVE.search(low)
            or CAN_THEY_HAVE.search(low)
            # "what can she not eat" and "remind me what hes allergic to" name a limit and a
            # person, and the person is a pronoun with nobody behind it, so the asks that need a
            # relation never took the line. EAT_ASK is deliberately not in this list: "and how
            # long do i need for the chicken" has an eating word in it and is the answers lane's,
            # and read as an ask that names nothing it stopped the store filing the chicken, so
            # the next turn of a roast conversation answered about hens.
            or _a_bare_limit_ask(low, memory)):
        return False
    if not _asks_about_someone(low, text, memory):
        return False
    whole = " ".join(str(text or "").lower().split())
    if STATES_A_LIMIT.search(whole) and not A_HAVE_QUESTION.search(whole):
        # The line says the limit and asks about it in one breath: "my son is 7 and has a nut
        # allergy, what is he allergic to". The fact is the line's own and keeping it is another
        # reading's job, so this one stands down. Claimed here, the store told a person who had
        # just said their son has a nut allergy that it had not been told about an allergy, and
        # the answer it took the turn from was a real one.
        return False
    said = _other_person_reply(memory or {}, low)
    # The reader only says whose fact is missing when the line does name a person it can read
    # (a relation, a name the store knows, or a "he" that points at one), so that line is the
    # store's own too: "is he allergic to anything" after three people were named was answered
    # with what to check on a label, as if "he" were the person typing.
    return bool(said)


# "what are they called again?" after "we got three kittens, pip, squeak and nibble": the ask
# names no animal and no fact, only the thing the store is holding, and says it with the pronoun
# because the line before it was the one that named them. There is no "my dog" in it for the
# readers to take hold of, so the store answered a question about the three kittens it had just
# written down with texting advice, and the names sat in memory unused.
#
# Only a line that points back at something already told is read this way - "again", "remind me",
# "did i call them" - because a plain "what are they called" is about something out in the world
# ("i saw two birds in the garden") and keeps whatever answer it has. And only when the store holds
# a pet at all (see `_the_names_again`), so the pronoun is never answered with a denial.
# The words that make the ask a second one: "again", "remind me", "what did i call him". The name
# is not `POINTS_BACK` - the file already has a `POINTS_BACK` frozenset of the little pointing
# words (it, them, that, back, again), and a second binding of a module-level name turns the
# first one into a pattern every reader below the line would trip over.

# An ask that names one of their own facts and wants it back: "what are my cats called",
# "and where do i work", "what was my budget again". The fact is named as theirs, with the
# copula or the first-person ask around it, and nothing else in between: "how do i budget" and
# "why do we get allergies" are questions about the world and the store has nothing to say to
# them, while "what should i do about my job" is advice, not a read of the store.
NAMED_FACT_ASK = re.compile(
    r"\bwhat(?:'s|s| is| are| was| were)?\s+my\s+" + _FACT_SLOT + r"\b|"
    r"\bwhat\s+(?:is|are|was|were)\s+my\s+" + _FACT_SLOT + r"\b|"
    r"\bwhere do i (?:work|live|come from)\b(?=\s*(?:[?.!,;:]|$)|\s+(?:now|again|then|at|from|"
    r"these|days|properly|though|honestly|anymore|either|oh|wait|sorry|hmm|actually|um|right|"
    r"please|thanks)\b)|\bwhat do i work as\b|\bwho am i\b|"
    r"\bhow old am i\b|\bwhat do i do for a living\b", re.IGNORECASE)
# A line that only asks for something already kept is the store's own, whatever else proposed.
# "what were we up to?" after a Spanish lesson was answered by `answers` with the previous
# paragraph and *Same as before:* in front of it: the line carries no topic of its own, so the
# specialist rule read the conversation's topic (school-and-study) on it and handed the turn to
# the module that declares that topic. A read of the store is not about the topic it names, so
# the store says which of its own proposals this is, on the line in front of it, and the arbiter
# takes its word (bot/modules/arbiter.py, `TAKES_AS_IT_COMES`).
# Three asks the store must win even against a specialist module, and all are the arbiter's one
# hook: a read of the store ("what were we up to?") that is not about the topic it names, the ask
# whose answer is a line they said themselves ("what was i cooking?" is not a request for the
# recipe), and a `when` ask it can place - the date is in what the person said, whether they ask
# for it again ("when is that again" after a dentist appointment) or ask for the day the work for
# a plan goes on ("when is the best time to prep for it" after a work thing on friday, which the
# answers module took with the entry about revising because "best time" is in the ask).
# `_the_prep_day` says which asks of that second shape the store can really answer: with no day to
# add to the plan it has nothing to say, so an ask about the world ("when is the best time to take
# a mortgage") and an ask about a thing with an answer of its own ("when is the best time to book
# it") are left to whoever can answer them. The composition is here, after every reader, so
# neither name shadows the other.
def _the_plan_they_took_back(text, memory):
    """A where ask about a trip they have just taken back is the store's line, not a repeat.

    "im going to lisbon in may" / "take it back" / "where am i going" was answered "Same as
    before: In Lisbon: Alfama on foot and the 28 tram..." - the trip's paragraph read back to
    someone the bot had just told "Right, that place is off the record, then." The ask names no
    subject of its own, so the knowledge base leaned on the topic record for the line they had
    just retracted and the answer on the screen came back. The store is the one part that knows
    the plan went: its own answer to a where ask names what was taken back ("Lisbon is off, then
    - where are you going?"). Only a where ask, and only while the thing they took back is the
    newest thing in the store, so every other line after a take-back is read exactly as before.
    """
    if not isinstance(memory, dict):
        return False
    gone = user(memory).get("plan_dropped")
    if not isinstance(gone, str) or not gone.strip():
        return False
    low = " ".join(str(text or "").lower().split())
    return bool(WHERE_PLAN.search(low))

def _the_clock_in_their_line(text, memory):
    """True when the ask wants a clock or a day the person gave, and the store can place it.

    "what time is my appointment" after "i have a dentist appointment on friday at 3" was
    answered "Ring practices near you and ask straight out whether they take new NHS patients":
    the store had the hour and proposed it, but the claim that hands the store its own asks was
    gated on the word "when", so a clock ask fell to the knowledge base's entry about the same
    noun. The hour or the day is in what the person said, so the ask is the store's - and every
    such ask it cannot place (no plan naming it, nothing to read the hour off) is left alone,
    which keeps "what time do i start work" with whoever can answer it.
    """
    try:
        low = text.lower()
        if not (TIME_ASKS.search(low) or TIME_THING.search(low) or TIME_IT.search(low)
                or DAY_THING.search(low) or DAY_IT.search(low)):
            return False
        return bool(_plans_reply(memory, low))
    except Exception:  # noqa: BLE001 - a claim that cannot be read is not a claim
        return False


# An ask about someone else, put as a question: "is she vegetarian", "does she eat meat", "what
# does my mother in law eat", "what is she allergic to". The line has to open as a question or ask
# what they eat; "what can i cook for my vegetarian mother in law" is a request for a dish, and the
# word vegetarian in it is not the person's diet being asked about.
ASK_ABOUT_THEM = re.compile(
    r"^\W*(?:is|are|does|do|did|was|were|can|could|has|have|will)\b|"
    r"\bwhat (?:does|do|did|can|could|is|are|was|were) "
    r"(?:he|she|they|your|my|his|her|their)\b|"
    r"\bwhat(?:'s|s| is| are)\s+(?:my|his|her|their|he|she|they)\b", re.I)


def _an_ask_about_someone_else(text, memory):
    """True when the line asks about a fact the store keeps for someone else.

    "i'm cooking for my mother in law on sunday" then "shes vegetarian" then "is she vegetarian"
    is an ask about the mother in law, and the diet is on record; the knowledge base reads the
    word "vegetarian" and offers a curry instead, so the store has to say the line is its own
    (`TAKES_AS_IT_COMES` below). Only a line that names or points at a person whose fact is on
    record is claimed: with nothing stored for them the ask goes to whoever can answer it.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return False
    if not ASK_ABOUT_THEM.search(text.strip()):
        return False
    keys = []
    if OTHER_FACT.search(text):
        keys.append("allergies")
    if EAT_ASK.search(text):
        keys.append("diet")
    if not keys:
        return False
    try:
        who = _someone_else_named(_bare(_folded(text, memory)), memory)
    except Exception:  # noqa: BLE001 - a line that cannot be read claims nothing
        return False
    if not who:
        return False
    for known in others(memory):
        if known.get("who") == who:
            return any(known.get(key) for key in keys)
    return False


def _the_take_back_about_someone(text, memory):
    """A line that takes a fact back off somebody else's list is the store's, not the topic's.

    "my son is allergic to nuts" then "he isnt allergic to nuts" was answered with the nut-free
    lecture from the knowledge base: the line names nuts, so `answers` read food on it and took
    the turn from the store that had just taken them off his list. The store's note is about
    what the chat keeps, not about nuts, so it says so in front of its reply.
    """
    gone = memory.get("denial") if isinstance(memory, dict) else None
    if not isinstance(gone, dict) or not gone.get("who"):
        return False
    return gone.get("said") == " ".join(str(text or "").lower().split())


def _the_part_that_hurts_asked(text, memory):
    """The ask for the part that hurts, and the side it was said with.

    "my knee hurts", then "its on the outside of the knee", then "and which knee was it" is
    answered from what the person said, so nothing that only echoes their last line can take the
    turn: `You said: "its on the outside of the knee"` says their own words again and answers
    nothing. The claim is made for every line the hurting-part reader can answer, and for no
    other.
    """
    if not isinstance(memory, dict):
        return False
    low = " ".join(str(text or "").lower().split())
    return bool(low) and bool(a_hurting_part.the_part_asked(memory, low))


def _the_store_readings(text, memory=None):
    """The lines this store read for certain: a read of what it keeps, the ask whose answer is a
    line they said themselves, a `when` ask it can place, and a question about what the chat
    already holds. All are answered from what the person said, so a topic the knowledge base
    declares must not take the turn.

    This is a reading, not the hook: the exported name is `TAKES_AS_IT_COMES` at the end of the
    file, and it asks this one first. A module's name is bound once, at import, so a second `def`
    of the exported name is not an addition - it is a whole new hook, and everything under the
    first one stops answering without a single test going red.

    "when is that again" after "i've got a dentist appointment on tuesday" was answered
    "Same as before: Ring practices near you and ask straight out whether they take new NHS
    patients..." - the knowledge answer that happened to be the turn before, said again behind a
    repeat lead-in. The date is in what the person said, so this is the memory store's line and
    it says so in front of it. Every ask it cannot place is left alone.

    "have we talked about food" is the same kind of line: the answers lane proposed from the word
    `food` and won before the store was asked, so the person asking the bot to remember got a
    recipe list instead.
    """
    if (_reads_the_store(text, memory) or _their_own_line_ask(text, memory)
            or _the_part_that_hurts_asked(text, memory)
            or _their_fact_ask(text, memory)
            or _a_kept_fact_read(text, memory)
            or decided.asks(text)
            or told_about.ABOUT_THE_CHAT(text, memory)
            or told_about.A_CALLBACK(text, memory)):
        return True
    if WHOLE_ASK.match(str(text or "").strip().lower()) \
            and _a_whole_answer_to_hand_back(memory, text):
        # "in full", "the whole thing", "all of it": the line names no thing of its own, so the
        # specialist rule read the chat's topic on it and handed the turn to an entry that folded
        # "the full" as a thing ("The same goes for the full: If you forget, keep a filled bottle
        # ...") instead of the answer the person asked for again. `_repeat_ask` already reads this
        # ask - it is the same `WHOLE_ASK` and the same "is there a whole answer behind it" test
        # that keeps "hi" / "in full" with the small talk - but nothing asked it from here, so the
        # store never claimed the line.
        return True
    if _a_state_that_was(text, memory, ""):
        # A pregnancy or a feeding that is over is this store's line and nobody else's: the
        # knowledge base reads the word "pregnant" and serves the trying-for-a-baby entry, and the
        # news reader congratulates a state that has passed. The store has nothing to file for it,
        # so it only says the tense back.
        return True
    if _a_feeling_about_their_own_news(text, memory):
        # A bare feeling is about the thing they said a moment ago, which is a read of this store
        # and nothing the knowledge base or the small-talk topics know about.
        return True
    if _the_plan_they_took_back(text, memory):
        # A where ask whose trip was taken back the turn before, answered by the store that knows
        # it went rather than by the paragraph that was just taken off the record.
        return True
    if _the_take_back_about_someone(text, memory):
        # "he isnt allergic to nuts" one line after "my son is allergic to nuts": the topic is
        # nuts and the line is about the chat, so the entry that knows nuts must not take it.
        return True
    if _can_close(text, memory):
        # A line that asks to leave the subject is not about the subject, so the entry that knows
        # it must not take the turn ("can we talk about something else" after a hospital line was
        # answered with a care assessment). The store knows what the subject was, so it answers.
        return True
    if _the_call_from_the_advice(text, memory):
        # A decision the answer above already settled: the line names no subject of its own, so
        # the specialist rule would read the chat's topic on it and hand the turn to that entry.
        return True
    if _asks_whether_we_followed(text, memory):
        # "did you get that" names nothing of the world, so the specialist rule read the chat's
        # topic on it and the knowledge entry that topic belongs to took the turn - the person
        # asking whether the bot had followed got a lookup. The store knows what it kept.
        return True
    if rates_reader.is_a_rate_ask(text, memory):
        # The ask for a rate this store holds: "how often do i go to the gym" after "i go twice a
        # week". The exercise entry answers from the guideline a person should keep, which is the
        # wrong answer to someone who told this store their own.
        return True
    if _a_plain_time_ask(text, memory):
        # The ask for the hour their own day runs on ("what time do i get up" after "i get up at
        # seven"). The sleep entry answers from the routine a person should keep - "work it back
        # from the morning" - which is the wrong answer to someone who told this store their own
        # hour: the line names one of the times on file and nothing of its own, so the store
        # answers it.
        return True
    if _an_ask_about_someone_else(text, memory):
        # The fact is in this store, filed under the person the line named: the knowledge base
        # has nothing about their sister's allergy.
        return True
    if _the_group_size_ask(text, memory):
        # How many the person's own group is, when this store holds the number: "how many of us"
        # after "we are four of us" was answered with the dish card the cooking topic had in hand
        # ("Quick: tuna pasta in 15, macaroni cheese in 25..."), one turn after the person had
        # said how many they were. The number is kept here, so the topic must not take the line.
        return True
    if repeat_the_line.how_long_its_been(text) and repeat_the_line.the_figure_they_gave(
            text, memory):
        # The length they gave about their own thing, asked back with the thing named: "how long
        # has my back been like this now" after "my lower back has been sore for about 3 weeks".
        # Claimed here because the carry into the card that answers a back took the turn and said
        # what keeps a back quiet, while the three weeks were in the chat.
        return True
    if _the_figure_the_answer_names(text, memory):
        # A figure ask that names no thing ("how many weeks" after the training answer) is read
        # off the answer the person just read, and `respond` says that figure. Claimed here
        # because a card the bare unit reaches answers it with a length of the wrong kind, and a
        # hook that says yes on a line `respond` answers differently would take the turn off the
        # module that should have had it.
        return True
    if _the_budget_on_the_answer(text, memory):
        # How much time there is is not a new question: it is the room the answer above has, and
        # read as a question the knowledge base took it for one - "and i only get 20 minutes"
        # after the lunch answer reached the eggs, the fastest dinner there is.
        return True
    if _the_back_this_turn(text, memory):
        # The line that puts back what somebody else does not eat is the store's own: only the
        # store knows what it lifts, and the small talk answered it with "Got it - he eats fish."
        # while the diet it lifts stayed on his record and came back on the next ask.
        return True
    if _the_same_fact_about_someone(text, memory):
        # "and my wife is too" after "im allergic to nuts" carries no subject of its own, so the
        # specialist rule read the chat's topic on it and handed the turn to the entry about that
        # diet ("same for my wife" after "im vegan" came back as the vegan amounts). The fact the
        # "too" points at is this store's, and the note it makes is kept with the reply, so the
        # store says so in front of it.
        return True
    try:
        if not isinstance(text, str) or not isinstance(memory, dict):
            return False
        line = _bare(_folded(text, memory))
        if (POINTS_BACK_AT_IT.search(line) or WORK_ON_IT.search(line)) \
                and not _the_prep_day(memory, line):
            # An ask that puts a verb on the thing ("to prep for it", "to book it") is answered by
            # the plan only when the store can name the day the work for it goes on. The plan said
            # back on its own is their own line again, and that echo was landing on the asks the
            # knowledge base has a real answer for ("when is the best time to book it" after a
            # Rome trip came back "You're going to rome in may."), so those are not claimed here.
            # "when is that again" is not this shape: the pointing word is the whole ask, not the
            # object of a verb, and the date they gave is the answer it wants.
            return False
        if _the_clock_in_their_line(text, memory):
            # "what time is my appointment" is the hour they gave, so it is not a question about
            # how to get an appointment. Read before the "when" gate because the line says
            # "what time" and that is the same ask.
            return True
        if "when" not in text.lower():
            return _a_count_from_the_date(text, memory)
        return bool(when_answer(text, memory))
    except Exception:  # noqa: BLE001 - a module that cannot claim declares nothing
        return False
        return False




# A line that puts an animal of the person's own in the store: "my dog is called alfie", "we have
# two dogs, rufus and nell", "we got three kittens".
# ...and the line that hands animals to somebody else, or met them out in the world. A pronoun
# after one of those is about those animals, not about the person's own.










# "what is my mum allergic to?" carries the word the allergy entry knows, and the entry answered
# with what an allergy is - the one thing the person did not ask - while the store held "your mum
# is allergic to shellfish". The line is a read of a fact the store keeps about a person, so the
# store takes it; a line that asks for advice instead ("can he eat cake", "what should my son
# eat") is still the entry's, and so is a question about allergies in general.
PERSON_ADVICE_ASK = re.compile(
    r"^\W*(?:can|could|should|shall|would|will|may|might|is it (?:ok|okay|fine|safe)|"
    r"what can|what could|what should|how (?:do|can|should)|any (?:tips|ideas|advice|"
    r"suggestions|ways))\b", re.I)


# The store saying it holds nothing: an honest answer when the store is all there is, and a
# denial of the turn before when another module had something to say.


# The frame of an ask about someone's allergy or diet, and nothing of its own: the person, the
# ask words and the one fact word. A line that keeps a word after all of that is saying something
# the shop does not hold, so the store holding nothing is not a reason to turn the turn away.






# A pregnancy is counted in weeks, and both ways of asking for the count belong to the store.


# An ask about the person's own length: "how far along am i", "how many weeks am i", "what week
# am i in". The pronoun is what makes it theirs - "how far along is she" is about the she.








def _their_fact_ask(text, memory=None):
    """True for a line that only asks back a fact kept about someone else."""
    if not isinstance(text, str):
        return False
    low = _bare(_folded(text, memory))
    if PERSON_ADVICE_ASK.match(low) and not (CAN_THEY_HAVE.search(low)
                                             and _a_limit_kept_for_them(low, memory)):
        # "can he have cheese" opens like an advice ask and is not one: the person is asking
        # whether one food is all right for somebody with a limit the store already holds, and
        # the limit is the answer. A line with no limit kept for them is advice and is left alone.
        return False
    undeclared = _the_person_still_in_hand(low, memory)
    if not (undeclared or OTHER_FACT.search(low) or EAT_ASK.search(low)
            or CANT_HAVE.search(low) or CAN_HAVE.search(low) or CAN_THEY_HAVE.search(low)):
        return False
    # A line that tells the fact is not asking for it: "my son doesnt eat meat" and "my sister
    # is vegan" are the cooking entry's lines, and the store answering them with the fact said
    # back ("Your son doesn't eat meat.") is an echo where the dinner should be. Only an ask is
    # the store's, with or without the question mark.
    if not (undeclared or _asks(low) or "?" in text or _asks_about_someone_else(text)):
        # "does my mum eat meat she is vegetarian" is an ask and a telling in one breath, and most
        # people type it with no question mark: the auxiliary at the front and the person after it
        # are what make it an ask (`_asks_about_someone_else` reads exactly that shape).
        return False
    # Someone else is in the line: a pronoun, or a relation of theirs ("my mum"). A possessive in
    # front of another noun ("my mums car") is the car, so the word has to be the person.
    if not (undeclared or THEM.search(low) or _named_person(low)
            or re.search(r"\bmy\s+(?:" + _RELATION + r")\b(?!'s|s\b)(?!s\b)", low)):
        return False
    if CAN_THEY_HAVE_A_FOOD.search(low) and not _a_limit_kept_for_them(low, memory):
        # "can she have cheese" is answered from a limit the store holds for that person. With
        # nothing kept but their name, the store has no fact to answer with, and saying so about
        # a person the chat only named once is not worth the turn; with only an allergy kept, the
        # foods that contain the thing are the cooking entries' reading, not the store's.
        return False
    said = _other_person_reply(memory, low)
    if not said:
        return False
    # A miss is not a denial: when the store holds nothing about that person, the honest "you
    # haven't told me" is worse than the answer the knowledge base has. "is my son allergic to
    # nuts? he had a rash" was claimed only to be told nothing was on record, while the entry
    # about a nut-free kitchen had a real answer for it.
    if NO_RECORD.search(said):
        return False
    return True


def _name_the_last_pet(text, memory):
    """"we've also got a cat" then "and her name is Biscuit" is one cat with a name.

    A name given a second time is a correction when the line opens like one - "sorry, his name
    is milo" after "we have a dog called max". The store kept the first name and said it back
    ("You've got a dog called Max") while the person had already taken it back, and the same line
    with the old name on the end ("sorry, his name is milo not max") was read as not having a dog
    at all. Only the opener makes it a rename: "we have a dog called max / his name is milo" on
    its own is the same dog said twice as easily as a correction.
    """
    if not isinstance(text, str):
        return
    pets = user(memory).get("pets")
    named = pets[-1] if isinstance(pets, list) and pets and isinstance(pets[-1], dict) else {}
    # The lower-case shape is only read when there is a pet to put the name on, which is here.
    name = extract.pet_name_only(text, lower=bool(named)) or _name_they_answered(text, memory)
    if not name:
        return
    if not isinstance(pets, list) or not pets:
        # The name can come before the animal is in the store: "im getting a dog" / "what should
        # i name it" / "milo" keeps no dog yet, and the name is the one thing that turn gave.
        # The animal is the one the list or the question was about, so the pet is filed whole.
        animal = _the_animal_of_the_pick(memory)
        if not animal or animal == "pet":
            return
        remember(memory, "pets", [{"animal": animal, "name": name}], text)
        return
    last = pets[-1]
    if isinstance(last, dict) and not last.get("name"):
        last["name"] = name
        kept = {"animal": last.get("animal", "pet"), "name": name}
        if isinstance(last.get("count"), int) and last["count"] > 1:
            kept["count"] = last["count"]
        remember(memory, "pets", [kept], text)
        return
    # A correction that names the animal it is about ("no the cat is called tom") is that
    # animal's rename and nobody else's: `_fix_a_pets_name` has already moved the name on the cat,
    # and putting it on the pet said last as well renamed the dog in a house with one of each.
    if isinstance(last, dict) and str(last.get("name") or "").lower() != name.lower() \
            and (CORRECTS_A_NAME.match(text) or CORRECTS_A_NAME_POSSESSIVE.match(text)) \
            and not _names_a_pet_here(text, memory):
        # The one on record is the same animal under the name they have just taken back, so the
        # entry is renamed rather than a second one added: "we have a dog called max / sorry his
        # name is milo" is one dog, not two.
        before = str(last.get("name") or "")
        last["name"] = name
        log(memory).append({"key": "pet", "value": {"animal": last.get("animal"), "name": name},
                            "turn": len(memory.get("turns") or []), "text": text})
        # The name on record is kept beside the new one, so the next line about the pet still
        # finds it: "my dog is called rex" then "his names actually rocky" then "how old is
        # he" answered with a memory trick about names, because the dog under Rocky was a
        # different dog from the one under Rex.
        if before and before.lower() != name.lower():
            was = [str(old) for old in (last.get("was") or []) if str(old).lower() != name.lower()]
            last["was"] = was + [before]
        # The person is told which name the bot goes with rather than having their own line
        # handed back, and it is the pet's own note: the two-name shape ("Rocky, not Rex — got
        # it.") reads to the next module as a conversation about names rather than about the
        # dog, and "how old is he" then got a tip on remembering names.
        if before:
            memory["correction"] = {"key": "pet", "value": name,
                                    "animal": last.get("animal") or "pet",
                                    "said": " ".join(str(text or "").lower().split())}


def _the_animals_named(text, memory):
    """The animals of the store's pets the line names: "no the cat is called tom" names the cat."""
    low = " ".join(str(text or "").lower().split())
    here = set()
    for pet in (user(memory).get("pets") or ()):
        if not isinstance(pet, dict) or not pet.get("animal"):
            continue
        animal = str(pet["animal"]).lower()
        if re.search(r"\b" + re.escape(animal) + r"s?\b", low):
            here.add(animal)
    return here


def _the_name_it_had(animal, said, memory):
    """The name the store had for this animal before the line that named it again."""
    for entry in reversed(log(memory) or ()):
        value = entry.get("value") if isinstance(entry, dict) else None
        if not isinstance(value, dict):
            continue
        if str(value.get("animal") or "").lower() != animal:
            continue
        name = str(value.get("name") or "")
        if name and name.lower() != str(said or "").lower():
            return name
    return ""


def _names_a_pet_here(text, memory):
    """Whether the line names an animal the store keeps a pet of ("the cat", "the dogs")."""
    low = " ".join(str(text or "").lower().split())
    for pet in (user(memory).get("pets") or ()):
        if not isinstance(pet, dict) or not pet.get("animal"):
            continue
        if re.search(r"\b" + re.escape(str(pet["animal"]).lower()) + r"s?\b", low):
            return True
    return False


# "sorry, his name is milo", "no, its luna", "actually his name is milo not max": the opener is
# what says the name on record is the wrong one.
CORRECTS_A_NAME = re.compile(r"^\W*(?:(?:no|nope|sorry|actually|oops|wait|hold on|correction)"
                             r"[,.]?\s+)", re.I)
# The correcting word inside the possessive instead of in front of it: "his names actually rocky"
# is "his name's actually rocky" typed without the apostrophe, and it opens with no "no"/"sorry",
# so the rename above never saw it and the store kept Rex while the reply handed the line back.
CORRECTS_A_NAME_POSSESSIVE = re.compile(
    r"^\W*(?:his|her|its|their)\s+names?\s+(?:actually|really)\s+", re.I)


# "fred is 5", "biscuit was 12", "milly is 3 years old": a line that names no animal, only the
# name the store has for one, and gives a figure for it.
# An age is typed as a figure or as a word, and people type "hes two" as often as "hes 2": the
# two are the same figure, so every age reader below takes either. Without the words, an age said
# out loud went nowhere and the store answered "how old is your dog" with "You haven't told me"
# about the age it had just been given.
AGE_IN_WORDS = "|".join(sorted(extract.FIGURE_WORDS, key=len, reverse=True))


def _the_figure_said(match):
    """The age a reader's own regex caught, as a number, whether it was digits or a word."""
    said = str(match.group("age") or "").strip().lower()
    if not said:
        return None
    value = _a_number(extract.FIGURE_WORDS.get(said, said))
    return value if isinstance(value, int) else None


PET_NAME_AGE = re.compile(r"^\W*(?:[a-z][a-z'-]{2,20})\s+(?:is|was|are|were)\s+"
                          r"(?P<age>\d{1,2}|" + AGE_IN_WORDS + r")(?![\d.,]\d)(?!\s+of\b)"
                          r"(?!\s*(?:kg|kilo\w*|lbs?|pounds?|stone|st|cm|metres?|meters?|"
                          r"miles?|hours?|mins?|minutes?|percent|%))"
                          r"\s*(?P<unit>months?|weeks?)?\b", re.I)


# A lead-in in front of a name is not part of it: "and fred is 5", "sorry, actually fred is 6".
# People start a short line with one of these, and the name reader took the lead-in for the name.
PET_LEAD_IN = re.compile(r"^(?:and|also|oh|but|well|yeah|yes|no|sorry|actually|ok|okay|right|"
                         r"wait|god|hang on)\b[\s,]*", re.I)


def _without_a_lead_in(text):
    """The line with the lead-ins people open a short sentence with taken off."""
    said = str(text or "").strip()
    for _ in range(4):
        shorter = PET_LEAD_IN.sub("", said, count=1)
        if shorter == said:
            break
        said = shorter.strip()
    return said


def _put_a_pets_age(pet, age, unit, text):
    """Store an age on one animal, or None when it already says exactly that."""
    if pet.get("age") == age and str(pet.get("unit") or "") == unit:
        return None
    pet["age"] = age
    pet.pop("unit", None)
    if unit:
        pet["unit"] = unit
    return {"key": "pet", "value": dict(pet), "text": text}


# The same ask with the pet left off the front: "what shall i call him" a turn after the name was
# settled, "what did we call her". The animal is the one the chat is on, so it is answered from
# the store rather than from another list of names.
# "what shall i call him" is the same ask with a decision in it, and it is also how a naming
# question is put before any name exists ("what should i name it"). So this one is only read when
# the store already holds a name: without one, three names to choose from is the better answer.


# "so what did i pick", "which name did we go for": the same ask as "what's my cat called", put
# with the verb of choosing, and usually a turn or two after the name was settled.








def _age_the_named_pet(text, memory):
    """"my dog is called fred" then "fred is 5" is an age for the dog, not a fact about nobody.

    The line names no animal at all, only the name the store has for one, so the store is what
    says whose age it is. Without this the 5 went nowhere and "how old is fred" had no answer.
    """
    if not isinstance(text, str):
        return None
    low = _without_a_lead_in(text).lower()
    match = PET_NAME_AGE.match(low)
    if not match:
        return None
    age = _the_figure_said(match)
    if not 0 < age <= 30:
        return None
    unit = "months" if str(match.group("unit") or "").lower().startswith("month") else ""
    said = low.strip().split()[0].strip(".,!?") if low.strip() else ""
    pets = user(memory).get("pets")
    if not isinstance(pets, list):
        return None
    for pet in reversed(pets):
        if not isinstance(pet, dict) or str(pet.get("name") or "").lower() != said:
            continue
        return _put_a_pets_age(pet, age, unit, text)
    return None


def _fix_a_pets_age(text, memory):
    """"my dog is 5" then "sorry he is 6": the correction goes on the animal it corrects.

    The line names no animal - it names a pronoun and a figure - and the store already has one
    age for the animal the chat is on, so that is the age the figure replaces. Read the same way
    a person's corrected age is read (`_fix_a_persons_age`): only a short line, only with a
    correction word in it, and only when there is an age stored to replace, because a
    correction replaces a fact rather than being the first one said.

    Without this the store kept the old figure and the bot said it as fact: "my dog is 5" /
    "sorry he is 6" / "how old is my dog" answered "Your dog is 5." after the person had said 6.
    """
    said = " ".join(str(text or "").lower().split())
    low = _without_a_lead_in(said)
    # The correction word is one of the lead-ins, so it has to be read off the line as it was
    # said, before the lead-in comes off.
    if not low or len(low.split()) > PET_AGE_FIX_WORDS or not CORRECTING.search(said):
        return None
    if _PET_WORD.search(low):
        return None  # "my dog is 6" names the animal and is a fact of its own
    match = AGE_FIX.search(low)
    if not match:
        return None
    age = _the_figure_said(match)
    if not 0 < age <= 30:
        return None
    who = _person_from_pronoun(low, memory)
    if who and any(str(known.get("who") or "") == who and "age" in known
                   for known in others(memory)):
        # "my dog is 5" / "my son is 7" / "actually hes 8": the pronoun points at a person, and
        # a person's corrected age is read by `_fix_a_persons_age`. It is one figure, not both.
        return None
    unit = "months" if re.search(r"\bmonths?\b", low) else ""
    aged = [pet for pet in (user(memory).get("pets") or [])
            if isinstance(pet, dict) and pet.get("age") is not None]
    if len(aged) != 1:
        # Two animals with ages and no animal named: the pronoun is the only thing to go on, and
        # "they are 6" is not a correction of either of them.
        return None
    return _put_a_pets_age(aged[0], age, unit, text)


# The bot has asked how old the animal is and this line is the figure, with or without the
# pronoun: "hes 3", "she's 4", "3".
PET_AGE_ANSWER = re.compile(r"^\W*(?:(?:he|she|it|they)(?:'s|s|\s+is|\s+are|\s+is\s+now)?\s+)?"
                            r"(?P<age>\d{1,2}|" + AGE_IN_WORDS + r")\s*"
                            r"(?P<unit>years?|months?|weeks?)?\s*(?:old)?\W*$", re.I)


def _age_said_of_the_only_animal(text, memory):
    """"i have a greyhound called sid" then "hes 6": the figure is that animal's age.

    `_age_they_answered` reads a bare figure only when the bot asked for one, so a figure the
    person volunteers ("hes 6", "shes 12 now") went nowhere and "how old is sid" answered that
    they had never said. It is only read when the line before it named an animal or the one the
    store knows by name, and when the chat holds one animal - with two, "hes 6" says nothing
    about which one.
    """
    said = " ".join(str(text or "").lower().split())
    if not said or len(said.split()) > 5:
        return None
    previous = " ".join(str(last_user(memory) or "").lower().split())
    pets = [pet for pet in (user(memory).get("pets") or []) if isinstance(pet, dict)]
    if len(pets) == 1:
        pet = pets[0]
    else:
        # With more than one animal, the one the line before named is the one the pronoun is:
        # "rufus is a terrier" then "hes two" is Rufus's age, and Nell's is not known. Any other
        # line before it leaves the pronoun pointing at nobody in particular.
        named = [one for one in pets
                 if len(str(one.get("name") or "").strip()) > 2
                 and re.search(r"\b" + re.escape(str(one["name"]).strip().lower()) + r"\b",
                               previous)]
        if len(named) != 1:
            return None
        pet = named[0]
    if int(pet.get("count") or 1) > 1:
        # "i have two cats" is one record for two animals, so a pronoun and a figure do not say
        # which of them it is.
        return None
    name = str(pet.get("name") or "").strip().lower()
    called = [str(pet.get(word) or "").strip().lower() for word in ("animal", "breed")]
    if not (_PET_WORD.search(previous)
            or (len(name) > 2 and name in previous)
            or any(len(word) > 2 and word in previous for word in called)):
        return None
    if not re.search(r"\b(?:he|she|it|they)(?:'s|s|\s+is|\s+are)?\b", said):
        # A figure with no pronoun is someone else's unless the bot asked for it: the line has to
        # say whose age it is.
        return None
    match = PET_AGE_ANSWER.match(said)
    if not match:
        return None
    age = _the_figure_said(match)
    if not 0 < age <= 30:
        return None
    if _person_from_pronoun(said, memory):
        # "hes 8" after "my son has a dog" is the son, and a person's age is not the animal's.
        return None
    unit = str(match.group("unit") or "").lower()
    unit = "months" if unit.startswith("month") else ("weeks" if unit.startswith("week") else "")
    return _put_a_pets_age(pet, age, unit, text)


def _age_they_answered(text, memory):
    """The bot asked how old their animal was, so the figure in this line is that animal's age:

        i have a dog / You haven't told me how old your dog is. / hes 3

    A bare age names nobody, so it is read only when the reply before it asked, the same way a
    bare name is only read when the bot asked for one.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    asked = str(turns[-1].get("bot") or "")
    if "how old" not in asked.lower():
        return None
    pets = [pet for pet in (user(memory).get("pets") or []) if isinstance(pet, dict)]
    if not pets:
        return None
    # Only an animal was asked about: a figure given after "how old is your daughter" is not the
    # dog's age, so the question has to name an animal, or a name the store has for one.
    names = [str(pet.get("name") or "").strip().lower() for pet in pets]
    if not (_PET_WORD.search(asked) or any(
            name and re.search(r"\b" + re.escape(name) + r"\b", asked.lower()) for name in names)):
        return None
    match = PET_AGE_ANSWER.match(str(text or ""))
    if not match:
        return None
    age = _the_figure_said(match)
    if not 0 < age <= 30:
        return None
    unit = str(match.group("unit") or "").lower()
    unit = "months" if unit.startswith("month") else ("weeks" if unit.startswith("week") else "")
    for pet in reversed(pets):
        if pet.get("age") == age and str(pet.get("unit") or "") == unit:
            return None
        pet["age"] = age
        pet.pop("unit", None)
        if unit:
            pet["unit"] = unit
        # The store took a figure the person gave to the bot's own question, so the reply says it
        # back ("Noted: your cat is 4.") rather than a line that would fit any message at all.
        memory["pet_age"] = dict(pet)
        return {"key": "pet", "value": dict(pet), "text": text}
    return None


def _their_name_answered(text, memory):
    """The person's own name, given as the answer to the bot's own question:

        can you remember my name / I don't know it yet - you haven't said / sam
        can you remember my name / I don't know it yet - you haven't said / its sam

    A word on its own says nothing, so it is read as a name only when the reply right before it
    asked for one, and only when no name is on record yet ("sam" to a bot that already has the
    name is something else). "its" in front of the word is only an introduction there.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    if user(memory).get("name"):
        return None
    asked = str(turns[-1].get("bot") or "")
    if memory.get("asked_for") != "name" or not extract.USER_NAME_ASKED.search(asked):
        return None
    # The hedge comes off first: "its sam by the way" and "sam, btw" are the one word the store
    # waits for with three more around it, and read whole they were nothing at all.
    answered = extract.without_the_hedges(text)
    match = extract.NAME_ANSWER_ANNOUNCED.match(answered)
    if match:
        return extract.reads_as_a_name(match.group(1))
    last = extract.NAME_ANSWER_ANNOUNCED_LAST.search(answered)
    if last:
        # "i havent told you, its sam": the name is still the last thing said, after the apology
        # for not having given it, and the store was waiting for exactly this.
        return extract.reads_as_a_name(last.group(1))
    return extract.reads_as_a_name(answered)


# The bot's own list of names, as `_a_name_for_the_pet` writes it, is read in
# `extract.names_offered` - the answers lane stands down on the same reading, so the patterns are
# kept in one place (`bot/memory/facts.py`) rather than twice.








# A number on its own after a line about someone else, the way "no, 8" corrects "my son is 7".
from bot.memory.corrected import (  # moved out whole: see bot/memory/corrected.py.py
    AMOUNT,
    ANY_NUMBER,
    ASK_START,
    AT_TIME,
    A_DAY_BEFORE_A_MONTH,
    A_DAY_SAID_LONG,
    A_UNIT_SAID,
    BARE_HOUR,
    BARE_NEW_COUNT,
    CORRECTABLE,
    COUNT_SAID,
    CURRENCY,
    DATE_DAY,
    DATE_PHRASE,
    DAY_WORD,
    MADE_OF_A_VALUE,
    MONTHS,
    MONTH_ALT,
    MONTH_WORD,
    MONTH_WORDS,
    NAMING_VERB,
    NOT_A_FACT_OF_THEIRS,
    NO_SUBJECT_OF_ITS_OWN,
    NUMBER_DIGITS,
    NUMBER_VALUE,
    NUMBER_WORD,
    OTHER_BARE_NUMBER,
    RELATIVE_MONTH,
    STILL_THE_SAME_PERSON,
    _a_bare_hour,
    _a_birthday_for_somebody,
    _a_birthday_on_the_last_line,
    _a_count,
    _a_day_in_the_kind,
    _a_day_written_the_way_the_store_writes_it,
    _a_name_for_a_person,
    _a_name_the_store_keeps,
    _a_new_name_was_said,
    _a_relative_line,
    _a_relative_month,
    _a_spelling_of,
    _a_word_of_a_name,
    _an_amount_on_the_measure,
    _apply_correction,
    _asks,
    _birthday_words,
    _carries,
    _clock_key,
    _correct_a_persons_name,
    _correct_birthday,
    _correct_clock,
    _correct_count,
    _correct_date,
    _correct_fact,
    _correct_number,
    _correct_other,
    _correct_plan,
    _correct_the_count_on_the_table,
    _correct_their_birthday,
    _correct_when,
    _count_said,
    _date_in_plan,
    _date_said,
    _date_word,
    _date_word_case,
    _denies_and_names,
    _drop_wrong,
    _fact_naming,
    _keep_unit,
    _kind_of_value,
    _letters_apart,
    _make_corrects,
    _many,
    _measured_the_same,
    _names_a_half_of_the_day,
    _number_belongs_to_that_age,
    _number_in,
    _plan_saying,
    _plan_the_line_named,
    _plan_told_line,
    _stated_families,
    _stated_last,
    _stated_plan,
    _swap_in,
    _the_line_is_about_that_birthday,
    _the_person_the_plan_is_about,
    _the_plan_before,
    _the_plan_on_the_table,
    _the_topic_with_the_new_clock,
    _the_unit,
    _what_took_its_place,
    _without_the_naming_verb,
)
from bot.memory.store_replies import (A_HAVE_QUESTION, _a_bare_limit_ask, ACTIVITY_ASK, ANSWER_MODULES, ASK_WITHOUT_MY, BARE_WHAT_I_DO, CANT_HAVE, CAN_HAVE, CAN_THEY_HAVE, CAN_THEY_HAVE_A_FOOD, CHECK_FOLLOWED, DAY_IT, DAY_THING, EAT_ASK, FIRST_ASK, MONTHS, NO_RECORD, OTHER_FACT, PLAN_MINE, POINTS_BACK_AT_IT, THEM, TIME_ASKS, TIME_IT, TIME_THING, TOPIC_ASK, WHERE_PLAN, WHOLE_ASK, YES_NO_ASK, _RELATION, _a_feeling_about_what_they_said, _a_limit_kept_for_them, _a_number, _a_state_that_was, _a_thing, _a_whole_answer_to_hand_back, _about_the_bot_here, _about_this_chat, _activity_line, _after_the_yes_no_frame, _age_compare, _animal_family, _asks, _asks_about_someone, _at_the_clock, _bare, _behind_a_remembering_frame, _can_close, _canon_relation, _corrects, _count_of_a_kind, _diet_reply, _folded, _halves, _how_far_along, _is_or_are, _kind, _longest, _name_they_answered, _named_person, _names_its_thing, _names_minutes, _names_the_thing, _other_person_reply, _person_from_pronoun, _plain_line, _plans_reply, _reads_as_the_invitation, _remembers_fact, _repeat_ask, _restated, _says_something, _says_the_verb, _seconds, _sentences, _someone_else_named, _statement, _summary_reply, _swapped_lines, _the_animal_of_the_pick, _the_back_this_turn, _the_bot_name, _the_budget_on_the_answer, _the_call_from_the_advice, _the_condition, _the_job_was_just_said, _the_limit_the_last_line_gave, _the_limit_they_share, _the_person_still_in_hand, _the_plans_in_date_order, _the_prep_day, STATES_A_LIMIT, _the_same_fact_about_someone, _the_store_reply, _the_things, _told_phrase, _vary, _which_comes_first, _who_is_the_name_reply, _yours, ack, company, content, current, decided, enough_reply, extract, family_name, forget, guest, how_many, last_user, name, note, others, pick, plans, rates_reader, re, recall, recent, remember, remember_other, reminded, stem, thread, told_about, units, until_answer, user, when_answer, REPEAT_WORDS, asks_again)













# A correction of someone else's age carries the number with a pronoun: "my son is 7" then
# "actually hes 8". That line states no fact of its own, so it is read against the person the
# pronoun points at, and only when that person already has an age stored: a correction replaces
# a fact, it is not the first one said. A long line is not a correction of anything, it is a new
# sentence that happens to hold a number.
AGE_FIX = re.compile(r"\b(?:he|she|they)(?:'s|s| is| are| was)\s+(?:now\s+)?"
                     r"(?P<age>\d{1,3}|" + AGE_IN_WORDS + r")\b(?!\s+of\b)",
                     re.I)
# "i meant" belongs here with "i mean": both say the value being given replaces one already given,
# and the word boundary after "mean" meant "i meant he is 8" matched neither - the correction was
# applied by the others path below and then answered as if it were news.
CORRECTING = re.compile(r"\b(?:actually|no|nope|sorry|wait|i mean|i meant|make it|makes it)\b",
                        re.I)


def _fix_a_persons_age(text, memory):
    """Put a corrected age on the person the pronoun points at.

    "my son is 7" then "actually hes 8" leaves the store saying 7 while the bot has already said
    "Got it - he's 8.", so the person thinks the correction landed. The line names no relation,
    so who it is about comes from the pronoun, and the age it replaces has to be one the store
    already has.
    """
    low = " ".join(str(text or "").lower().split())
    if not low or len(low.split()) > AGE_FIX_WORDS or not CORRECTING.search(low):
        return None
    match = AGE_FIX.search(low)
    if not match:
        return None
    age = _the_figure_said(match)
    if not 0 <= age <= 120:
        return None
    who = _person_from_pronoun(low, memory)
    if not who:
        return None
    for known in others(memory):
        if known.get("who") == who and "age" in known:
            known["age"] = age
            known.pop("turns", None)
            log(memory).append({"key": "other", "value": dict(known),
                                "turn": len(memory.get("turns") or []), "text": text})
            return known
    return None


# How long a pregnancy has run goes up as the chat goes on, and the line that moves it names
# nobody: "my wife is 8 weeks pregnant" then "shes 10 weeks now" was answered "Got it - she's 10
# weeks now." while the store still held 8, so the ask after it said "Eight weeks." - the bot
# told the person the correction landed and then contradicted itself. The same shape as an age
# put right: the pronoun says who, and only a pregnancy already on record has a length to move.
WEEKS_FIX = re.compile(r"\b(?P<weeks>\d{1,2})\s*(?:weeks?|wks?)\b", re.I)


def _fix_the_weeks_of_a_pregnancy(text, memory):
    """Move the length the store holds to the one this line gives, for the person it points at."""
    low = " ".join(str(text or "").lower().split())
    if not low or len(low.split()) > 8:
        return None
    match = WEEKS_FIX.search(low)
    if not match:
        return None
    # A line that states the pregnancy again ("my wife is 12 weeks pregnant") is read by the
    # extractor, which files the new length itself; this is for the line that only moves it.
    if PREGNANCY_SAID_AGAIN.search(low):
        return None
    weeks = int(match.group("weeks"))
    if not 1 <= weeks <= 45:
        return None
    if not (CORRECTING.search(low) or re.search(r"\b(?:now|today)\b", low)):
        return None
    # The subject of the line decides whose length it moves, exactly as it does for a line that
    # states the pregnancy: "im 14 weeks now" is theirs, "she's 10 weeks now" is hers, and a chat
    # that has both on file must not move the wrong one.
    said_mine = re.search(r"\b(?:im|i'm|i am|i)\b", low)
    said_theirs = re.search(r"\b(?:my|our|she|he|they|her|his|their|hers)\b", low)
    own = user(memory) or {}
    if said_mine and not said_theirs and own.get("pregnant"):
        # A line about the person themselves: "im 14 weeks now", "actually im 16 weeks". Their own
        # pregnancy is kept on them, not in `others`, so nothing moved it: the bot agreed ("got it
        # - you're 14 weeks now") while "how far along am i" still answered 12.
        remember(memory, "weeks", weeks, text)
        return dict(own, weeks=weeks)
    who = _person_from_pronoun(low, memory)
    if not who:
        return None
    for known in others(memory):
        if known.get("who") == who and known.get("pregnant") and "weeks" in known:
            known["weeks"] = weeks
            known.pop("turns", None)
            log(memory).append({"key": "other", "value": dict(known),
                                "turn": len(memory.get("turns") or []), "text": text})
            return known
    return None


PREGNANCY_SAID_AGAIN = re.compile(r"\b(?:pregnant|expecting)\b", re.I)


# A correction of someone else's name carries it with a pronoun: "my sister is called meg" then
# "actually she's called maggie". The store kept meg, so the bot said "Got it - she's called
# maggie." and then answered "what's my sister called" with "Your sister is called Meg." - it
# told the person that the correction landed and then contradicted itself. The pronoun says who
# it is about, and a name is only replaced when that person already has one: this is the second
# name said, not the first.
# "her names actually hannah" is the same line with the apostrophe typed out, and it reached
# nobody: the possessive shape asked for "name is" exactly, so the store kept Anna while the
# reply handed the line back ("Her names actually hannah, good to know"). A name said after the
# word that opens a correction belongs to the person the possessive points at.
NAME_FIX = re.compile(
    r"\b(?:(?:he|she|they)(?:'s|s| is| was)?\s+(?:actually\s+|really\s+)?(?:called|named)"
    r"|(?:his|her|their)\s+names?\s+(?:is|was|actually|really))\s+"
    r"(?P<name>[a-z][a-z'\u2019-]{1,19})\b", re.I)
NAME_NOT_A_NAME = frozenset("""not called named now really also still a an the""".split())
# A name put right without the word "called" in it: "my daughter is called amy" then "no sorry,
# she is rosie". The plain "is" is also how a person says everything else about somebody ("she is
# tired", "she is 8", "she is a nurse"), so the word after it is only read as a name when it is
# not one of the words everybody uses. Rosie is a name; tired and nurse are not.
A_NAME_AFTER_A_PRONOUN = re.compile(
    r"\b(?:he|she|they)(?:'s|s| is| was)\s+(?P<name>[a-z][a-z'\u2019-]{1,19})\s*[,.!]?$", re.I)

# A pet's name given with its verb, for the correction that moves it: "no hes called max".
A_NAME_WITH_ITS_VERB = re.compile(r"\b(?:called|named)\s+(?P<name>[A-Za-z][A-Za-z'-]{1,19})\b",
                                  re.I)


def _fix_a_pets_name(text, memory):
    """A pet's name put right in the sentence moves the name on the pet.

    "my cat is called milo" then "no hes called max": the person correction path needs a pointer
    to a relation and a name that is a spelling of the old one, and a pet is neither, so the store
    kept Milo and the next ask answered Milo. The pet is the animal the line names, or else the
    pet the turn before was about.
    """
    from ..memory import rename as pet_rename  # the rename frame: see bot/memory/rename.py
    low = " ".join(str(text or "").lower().split())
    moves = pet_rename.moves(low)
    if not low or len(low.split()) > NAME_FIX_WORDS or not (CORRECTING.search(low) or moves):
        return None
    match = A_NAME_WITH_ITS_VERB.search(low)
    # A correction says the name with its verb ("no hes called max"); a rename says it at the end
    # of the line, with the verb about the animal in front ("we renamed him max").
    raw = ""
    if match:
        raw = match.group("name") or ""
    elif moves:
        raw = pet_rename.the_name_a_line_moved_on(
            low, user(memory).get("pets"), bool(extract.PETS.search(low)))
    if not raw:
        return None
    said = extract._finish(raw)
    if not said or extract._not_a_name(raw, strict_ly=False):
        return None
    pets = [pet for pet in (user(memory).get("pets") or ()) if isinstance(pet, dict)]
    named = [pet for pet in pets if pet.get("name")]
    target = None
    # The line that names the animal it is about ("no the cat is called tom") has already been
    # carried out by the facts reader: the store keeps one pet an animal, so filing "a cat called
    # tom" replaced the cat called milo. Nothing is left to move, and going on to look for a pet
    # anyway found the pet said last - the dog, in a house with one of each - and renamed that.
    if _names_a_pet_here(text, memory):
        if _another_animal_is_named(text):
            # "no my other cat is called max", "no we also have a cat called max": the word says
            # the name belongs beside the pet already there, so nothing is put right.
            return None
        for animal in sorted(_the_animals_named(text, memory)):
            kept = _pets_of(animal, pets)
            if not kept:
                continue
            filed = [pet for pet in kept if _a_pet_new_this_line(pet, memory)]
            older = [pet for pet in kept if not _a_pet_new_this_line(pet, memory)]
            if older:
                # The line that names the animal files the name it says ("no the cat is called
                # max" filed a cat called max), so that entry is the line's own echo. In a house
                # of one the facts reader files it over the cat already there and nothing is
                # left to move; in a house of two the cat it was filed beside is still there and
                # the name belongs on that one - the cat said last. Either way the entry the
                # line added is not a pet of its own.
                target = older[-1]
                if str(target.get("name") or "").lower() != said.lower():
                    target["name"] = said[:1].upper() + said[1:]
                    target.pop("turns", None)
                    was = _the_name_it_had(animal, said, memory)
                    if was and not (isinstance(memory.get("correction"), dict)
                                    and memory["correction"].get("said") == low):
                        memory["correction"] = {"key": "pet", "value": target["name"],
                                                "wrong": was[:1].upper() + was[1:],
                                                "animal": animal, "said": low, "text": text}
                for pet in filed:
                    if pet is not target and pet in (user(memory).get("pets") or ()):
                        user(memory)["pets"].remove(pet)
                return None
            for pet in filed:
                # A pet given its first name: the facts reader filed it as the line said it
                # ("max"), and a name on a pet is read back the way a name is written.
                pet["name"] = said[:1].upper() + said[1:]
                was = _the_name_it_had(animal, said, memory)
                if was and not (isinstance(memory.get("correction"), dict)
                                and memory["correction"].get("said") == low):
                    memory["correction"] = {"key": "pet", "value": pet["name"],
                                            "wrong": was[:1].upper() + was[1:],
                                            "animal": animal, "said": low, "text": text}
            return None
    if _another_animal_is_named(text):
        # "no my other cat is called max" names a second cat, not a name taken back: the store
        # keeps one pet an animal, so the facts reader files the new one and this line adds it.
        return None
    here = [pet for pet in pets
            if pet.get("animal")
            and re.search(r"\b" + re.escape(str(pet["animal"]).lower()) + r"s?\b", low)]
    # The line that renames also names the animal ("no the cat is called tom"), so the facts
    # reader has already filed a second cat of the new name: that entry is this line's echo, not
    # a pet of its own, and counting it would leave two cats matching the word "cat" and send the
    # correction on to the pet said last - the dog, in a house with one of each.
    here = [pet for pet in here if str(pet.get("name") or "").lower() != said.lower()]
    if len(here) == 1:
        target = here[0]
    else:
        for key in ("name", "animal"):
            found = [pet for pet in named if _the_turn_before_said(pet.get(key), memory)]
            if found:
                # The line says "he", and in "i have two cats called milo and tom" the he is
                # the one said last, so the pet named last in the same line is the one the
                # correction is about. A house of one pet is unaffected.
                target = found[-1]
                break
    if target is None:
        return None
    before = str(target.get("name") or "")
    if before.lower() == said.lower():
        # The name said again is the name already on file: nothing was put right.
        return None
    target["name"] = said[:1].upper() + said[1:]
    target.pop("turns", None)
    # The correction is the turn's news, said with the store's own correction note ("Max, not
    # Milo — got it."), unless the line already left one of its own.
    kept_note = memory.get("correction")
    if not (isinstance(kept_note, dict) and kept_note.get("said") == low):
        memory["correction"] = {"key": "pet", "value": target["name"],
                                "wrong": before[:1].upper() + before[1:],
                                "animal": str(target.get("animal") or "pet"),
                                "said": low, "text": text}
    # The line that renames also names a pet ("no, my cat is called max"), so the facts reader
    # has just filed a second cat of that name beside the one being renamed. One cat a person
    # names once: the renamed entry is the whole of what that line says.
    animal = str(target.get("animal") or "").lower()
    for other in list(pets):
        if other is target:
            continue
        if (str(other.get("animal") or "").lower() == animal
                and str(other.get("name") or "").lower() == said.lower()):
            pets.remove(other)
    user(memory)["pets"] = pets
    # The store keeps every pet it had: a rename is one animal under a new name, not the whole
    # household. Writing the renamed pet back on its own dropped the others - "i have two cats
    # called milo and tom" then "no hes called max" left one cat, and the count answer was
    # "You've got one cat" against two lines of what the person told us.
    log(memory).append({"key": "pet", "value": dict(target),
                        "turn": len(memory.get("turns") or []), "text": text})
    return target


# A name said for another animal of the same kind: "no my other cat is called max", "no we also
# have a cat called max". The word says the name belongs to a different animal, so it is a second
# pet rather than the name on the one in hand put right.
ANOTHER_ANIMAL = re.compile(r"\b(?:other|second|another|also|third)\b", re.I)


def _pets_of(animal, pets):
    """The pets of one animal in the store's list, in the order the store keeps them."""
    return [pet for pet in pets if isinstance(pet, dict)
            and str(pet.get("animal") or "").strip().lower() == animal]


def _a_pet_new_this_line(pet, memory):
    """Whether this pet entry was filed by the line being read.

    The store before the line was read is carried in the memory for the length of the turn
    (`_pets_before`), so an entry that was not there before is the line's own: it is the name
    the line said, filed beside the pets it was filed with, and not a pet of its own.
    """
    held = memory.get("_pets_before") if isinstance(memory, dict) else None
    if not isinstance(held, set) or not isinstance(pet, dict):
        return False
    return (str(pet.get("animal") or "").strip().lower(),
            str(pet.get("name") or "").strip().lower()) not in held


def _another_animal_is_named(text):
    """Whether the line says the name belongs to another animal, not the one on record."""
    return bool(ANOTHER_ANIMAL.search(" ".join(str(text or "").lower().split())))


def _two_of_the_animal_are_kept(pets, animal):
    """Whether the store holds more than one pet of this animal.

    When it does, a name filed against that animal was filed beside the pet already there. A
    rename leaves one entry (the rename drops the echo the same line filed), so two entries of
    the animal said with the new name is the store keeping both, not one name put right.
    """
    kept = [pet for pet in pets if isinstance(pet, dict)
            and str(pet.get("animal") or "").lower() == animal]
    return len(kept) > 1


def _the_turn_before_said(word, memory):
    """Whether the line before this one said this word about the pet in question."""
    turns = memory.get("turns")
    if not word or not isinstance(turns, list) or not turns:
        return False
    last = next((turn for turn in reversed(turns) if isinstance(turn, dict)), None)
    said = " ".join(str((last or {}).get("user") or "").lower().split())
    if not said:
        return False
    return bool(re.search(r"\b" + re.escape(str(word).lower()) + r"s?\b", said))


# A make said again in the words people use for it: "sorry its a focus", "actually its a 3 series".
# The line names no thing of its own, so the thing is the one the chat was last told the make of -
# the same way a corrected age goes on the person the last age went on.
CORRECTS_A_MAKE = re.compile(
    r"\b(?:sorry|actually|no|i mean|make that|or)?[\s,]*(?:its|it's|it is)\s+"
    r"(?:actually\s+|really\s+|just\s+)?(?:a|an|the)\s+(?P<value>[a-z0-9][a-z0-9' .+-]{0,31})$",
    re.I)


def _fix_the_make_of_a_thing(text, memory):
    """A correction that names only the make goes on the last thing the store was told about.

    "my car is a ford fiesta" and then "sorry, its a focus" is one car with its make put right,
    and a store that keeps the fiesta answers the next ask with a car they have just corrected.
    """
    line = " ".join(str(text or "").strip().split())
    if not line or line.endswith("?") or len(line.split()) > 6:
        return
    match = CORRECTS_A_MAKE.search(line.lower())
    if not match:
        return
    held = user(memory).get("owns")
    if not isinstance(held, dict) or not held:
        return
    # Which thing the correction is about is decided by what the make is a make of, not by the
    # order things were said: after "my car is a ford fiesta" and "my phone is a pixel", "sorry
    # it's a focus" is the car, and putting it on the phone invents a phone nobody has. A make
    # that fits more than one thing ("sorry, it's a bosch") goes on the one mentioned last.
    fits = {}
    for thing in held:
        name = extract._the_model(match.group("value"), thing)
        if name:
            fits[thing] = name
    if not fits:
        return
    last_said = []
    for entry in log(memory):
        if entry.get("key") == "owns":
            last_said.extend(entry.get("value") or {})
    thing = next((one for one in reversed(last_said) if one in fits), next(iter(fits), ""))
    name = fits.get(thing, "")
    if not name or name == held.get(thing):
        return
    remember(memory, "owns", {thing: name}, text)


def _fix_a_persons_name(text, memory):
    """Put a corrected name on the person the pronoun points at.

    "my sister is called meg" then "actually she's called maggie" left the store saying Meg, so
    the ask after it answered with the name the person had just put right. The line names no
    relation, so who it is about comes from the pronoun, and the name it replaces has to be one
    the store already has: a correction replaces a fact, it is not the first one said.
    """
    low = " ".join(str(text or "").lower().split())
    if not low or len(low.split()) > NAME_FIX_WORDS or not CORRECTING.search(low):
        return None
    match = NAME_FIX.search(low)
    bare = None
    if not match:
        # A bare rename: "no sorry, she is rosie". Both halves are needed - the correcting word
        # in the line, which the check above has already asked for, and a word that is not a
        # word everybody uses.
        bare = A_NAME_AFTER_A_PRONOUN.search(low)
        if not bare:
            return None
        word = bare.group("name").strip("'\u2019")
        if (word in extract.COMMON_WORDS or word in extract.JOB_WORDS
                or word in extract.KIN or extract._not_a_name(word, strict_ly=False)):
            return None
        match = bare
    said = match.group("name").strip("'\u2019")
    if not said or said in NAME_NOT_A_NAME or extract._not_a_name(said, strict_ly=False):
        return None
    name = extract._tidy(extract._finish(said) or "")
    if not name:
        return None
    # "her name is maggie" points the same way "she's called maggie" does, and the pronoun has to
    # be the one `_person_from_pronoun` reads, so the possessive is turned into it here.
    about = re.sub(r"\bhis\b(\s+name)", r"he\1", low)
    about = re.sub(r"\bher\b(\s+name)", r"she\1", about)
    who = _person_from_pronoun(about, memory)
    if not who and bare:
        # "my daughter is called amy" then "no sorry, he is jake": a bare "he is jake" names no
        # relation, so the pronoun is all the line gives, and a "he" about a daughter is not a
        # correction of her but the person starting on somebody else. Renaming her Jake is a
        # wrong fact, worse than the store keeping Amy. The possessive shape below keeps the
        # fallback, because "sorry, her name is tomas" says which fact is being put right.
        return None
    if not who:
        # "my brother is called tom" then "sorry, her name is tomas": the pronoun they picked is
        # the one they type, and with one person named in the chat the correction is about that
        # person - reading the "her" literally left the store on the wrong name and the next ask
        # said the name they had just put right.
        named = [entry for entry in others(memory) if entry.get("name")]
        if len(named) != 1:
            return None
        who = str(named[0].get("who") or "")
    for known in others(memory):
        if known.get("who") == who and known.get("name"):
            before = str(known.get("name") or "")
            if bare and before.lower() == extract._tidy(name).lower():
                # The word is the name already on record, so there is nothing to put right.
                return None
            known["name"] = extract._tidy(name)
            known.pop("turns", None)
            log(memory).append({"key": "other", "value": dict(known),
                                "turn": len(memory.get("turns") or []), "text": text})
            return {"who": who, "name": str(known["name"]), "from": before}
    return None


# A name given again for a person the store already holds, with no correcting word in the line:
# "my son is called jack" then "hes called jake". `_fix_a_persons_name` above wants a correction
# ("no she isnt, shes called dana"), so the plain form reached nobody and the store kept Jack while
# the reply said "He's called jake, good to know".
NAME_GIVEN = re.compile(
    r"\b(?:he|she|they)(?:'s|s| is| was)?\s+(?:called|named)\s+(?P<name>[a-z][a-z'\-]{1,19})\b"
    r"|\b(?:his|her|their)\s+name(?:'s|\s+is)\s+(?P<name2>[a-z][a-z'\-]{1,19})\b", re.I)
# A name given for a person ends the line: "hes called jake". The word after "called" in a longer
# line is usually not a name at all - "hes called in sick today" is a man phoning work, and reading
# it as one answered the next ask "Your son is called In".
NOT_A_NAME_AFTER_CALLED = frozenset("""
in out off up down back away over round around about on at by for with without into onto
sick ill late busy tired poorly bad good home here there now soon again today tonight
tomorrow yesterday it them him her me us you one ones the a an
""".split())


def _the_name_they_gave_to_the_person_they_mean(text, memory):
    """Put a name given with a pronoun on the person the store already holds.

    "my son is called jack" then "hes called jake" left the store saying Jack while the reply said
    "He's called jake, good to know": the person is told it landed and it did not, so the next
    "what is my son called" answers with the name they have just given. Who it is about comes from
    the pronoun.

    A name the store already holds is replaced. A person it holds and never named gets the name as
    their first one - "im taking my daughter to london" then "her name is maggie" - because the
    reply already promises to remember it, and only when exactly one unnamed person fits the
    pronoun.

    A bare name after the word that opens a correction ("no, jake") is not this reader's: that is
    a correction of a name said wrong, and `_correct_a_persons_name` owns it.
    """
    low = " ".join(str(text or "").lower().split())
    if not low or len(low.split()) > NAME_GIVEN_WORDS or "?" in low:
        # "hes called jake" on its own is a name for the person already meant, but the same words
        # inside a longer line introduce somebody ("my nephew? hes called tom"), and that is a
        # fact about the nephew that the relation readers handle.
        return None
    match = NAME_GIVEN.search(low)
    if not match:
        return None
    raw = str(match.group("name") or match.group("name2") or "")
    name = raw.strip(" .,!")
    if not name or not extract._may_be_a_name(name) or name.lower() in NOT_A_NAME_AFTER_CALLED:
        return None
    if low[match.end():].strip(" .,!;:"):
        # Words after the name mean the line is not only the name: "hes called in sick today".
        return None
    who = _person_from_pronoun(low, memory)
    if not who:
        return None
    for known in others(memory):
        if known.get("who") != who or not known.get("name"):
            continue
        if str(known.get("name")).lower() == name:
            return None
        known["name"] = extract._tidy(name)
        known.pop("turns", None)
        log(memory).append({"key": "other", "value": dict(known),
                            "turn": len(memory.get("turns") or []), "text": text})
        return known
    # A first name for a person the chat was told about and never named: "im taking my daughter to
    # london for her birthday" then "her name is maggie". The reader above only replaces a name the
    # store already holds, so the reply said "Her name is maggie - I'll remember that" and filed
    # nothing, and eight turns later the same chat answered "You haven't told me your daughter's
    # name." One person on record has to be the one the pronoun points at, unnamed, and no second
    # unnamed person may fit it: with two daughters in the chat "her name is maggie" does not say
    # which of them, and a guess is worse than the honest "you haven't told me".
    if extract.PETS.search(low):
        # The line names an animal, so the name is that animal's: "her name is biscuit" after "we've
        # got a cat" belongs to the cat, and `_name_the_last_pet` has it.
        return None
    if re.search(r"\b(?:she|her)\b", low):
        fits = extract.SHE
    elif re.search(r"\b(?:he|his)\b", low):
        fits = extract.HE
    else:
        fits = None  # "theyre called" says no gender, so any unnamed person is a candidate
    unnamed = [str(one.get("who")) for one in others(memory)
               if one.get("who") and not one.get("name")]
    # A person the chat named only by their relation ("my daughter") is in the list of people and
    # has no entry of its own until a fact is filed about them, so the word itself is a candidate.
    kept = {str(one.get("who") or "") for one in others(memory)}
    unnamed += [str(word).lower() for word in (user(memory).get("people") or ())
                if isinstance(word, str) and str(word).lower() not in kept]
    unnamed = [word for word in dict.fromkeys(unnamed) if not fits or _pronoun_fits(word, fits)]
    if len(unnamed) != 1:
        return None
    for known in others(memory):
        if str(known.get("who") or "") == unnamed[0] and not known.get("name"):
            known["name"] = extract._tidy(name)
            known.pop("turns", None)
            log(memory).append({"key": "other", "value": dict(known),
                                "turn": len(memory.get("turns") or []), "text": text})
            return known
    remember_other(memory, {"who": unnamed[0], "name": extract._tidy(name)}, text)
    return {"who": unnamed[0], "name": extract._tidy(name)}


# "make it 900", "make it 3 cats", "make it the 12th", "make it friday": a value a correction
# can put up on its own, without a fact behind it.






















# Keys on a person that are not a fact of theirs to move: who they are, what they are called,
# and the pronoun a line used instead of a name.


# "the 4th of may" is how the sentence said the day, not part of the day: the store writes a
# date as "4 may" or "4th may" and everything else is the words around it.








# A number in a plan is corrected the same way, in the plan itself: "im trying to lose 5 kilos
# before summer" then "sorry, i meant 8 kilos not 5" leaves a plan that still says 5, so the
# recall reads a number they have already taken back.








# The digits of a value, so "£500" and "500" are the same number. The unit that may follow is
# taken only when it is a unit on its own: "90 kilos" is 90, not "90 k", and "90k" is still 90.
NUMBER = re.compile(r"[£$€]?\d+(?:[.,]\d+)?(?:\s?(?:pounds|quid|euros?|dollars?|k))?(?![a-z])")


# The digits of a value, with no unit behind them: "£500" and "500" are the same number, and
# "175cm" is 175 rather than 17. NUMBER refuses a figure with a letter stuck to it (a "3kg" is not
# a count of anything), and reading it here made a value whose unit is written against the number
# lose its last digit: "180cm" read as 18, "18th" as 1, so a correction of either matched nothing.














# A figure on its own, which may be an hour where the plan's clock says no more than that.


















# Every number a line gives, in digits or in words, so a correction that is one number can be
# told from a line that gave two ("i have two kids and 3 dogs").
# A line that is only a new number, with a correction word in front: "actually three", "no, 4".
# The thing counted is not named again, so the line has to point back at the number it replaces,
# and a line without one of the correction words ("three") states something instead. "make that
# three" is the same take-back with the verb in front, and it was the one shape missing: after
# "i have two kids" it answered "I'm not sure about that one, sorry" and the count on record
# stayed at two.






# A date carried in words is two values at once: "the 13th of june" is a day and a month, so
# `_correct_when` (a bare "july" or "friday") leaves it alone and the plan keeps the old day.

# A day written as a plain number, which is how most of us type it: "no, 4 june", "the 12 july".
# Only a number in front of a month counts, so the number in "save 50 by june" or "in 2 weeks" is
# not a day of the month.










# The month said in relative words rather than by its name, and what the month named later puts
# in its place. "Next month" is a month like June is, so a person who names July is moving the
# date, not the place.










# A correction replaces the fact the line before it stated, and only that kind of fact: "no I
# mean Bristol" after "I live in Leeds" is a place, and "no I mean 43" after "I'm 34" is an
# age. A value that does not read as the same kind of fact leaves memory alone, so "no, I'm
# tired" or "no thanks" never overwrite anything.


# A corrected value with no fact behind it is said back and let go: short, in the bot's own words,
# and it keeps the old value beside it when the line gave one ("the 12th, not the 5th"), because
# that is what the person was at pains to say.
# The words a plan can open with that are capitalised only because they opened the line: they keep
# their lower case in the middle of "Got it — the gym at 7", and the second person is among them
# because the note says the person's sentence back in the bot's voice. The prepositions a date is
# said with ("in", "on") are here for the same reason: a birthday said back mid-sentence reads
# "Got it — your birthday is in June", not "... is In June".










def _a_person(value):
    """True when the corrected value names a person ("sorry, i meant my wife").

    A person put right is answered better by the sentence that says whose the fact was, so the
    short echo stays out of the way and the turn is left to it.
    """
    words = {word.rstrip("s") for word in re.findall(r"[a-z']+", str(value or "").lower())}
    return any(relation.rstrip("s") in words for relation in extract.RELATIONS)


# A correction does not always wear a marker. Once a wrong value has been said, "its Preeya not
# Priya" and "not Priya, Preeya" name both values with no "no" and no "sorry" in front, and
# they left the store alone: the old value stayed, the line was filed as a fact, and "what do you
# know about me" answered with both names. The shape alone is not enough to tell a correction
# from a statement - "its raining not sunny" has the same shape - so the reading is done here,
# where the store is, and only counts when the value it takes back is one it already holds.
PAIR_WITHOUT_A_MARKER = (
    re.compile(r"^\W*(?:(?:ok|okay|oh|well|so|and|hmm)[,. ]+)*"
               r"(?:(?:it'?s|its|that'?s|thats)\s+)?"
               r"(?P<to>[a-z0-9][a-z0-9'-]{0,19})\s*,?\s+not\s+"
               r"(?P<wrong>[a-z0-9][a-z0-9'-]{0,19})[.!]?\s*$", re.I),
    re.compile(r"^\W*(?:(?:ok|okay|oh|well|so|and|hmm)[,. ]+)*"
               r"not\s+(?P<wrong>[a-z0-9][a-z0-9'-]{0,19})\s*[,\u2013\u2014;-]\s*"
               r"(?:(?:it'?s|its|that'?s)\s+)?(?P<to>[a-z0-9][a-z0-9'-]{0,19})[.!]?\s*$",
               re.I),
    # "i'm not 42, i'm 43" and "it's not florence it's rome": the same pair with the copula said
    # twice, which is how most people put a figure or a name about themselves right. The half that
    # is taken back comes first here, so the groups are the other way round from the shapes above.
    re.compile(r"^\W*(?:(?:ok|okay|oh|well|so|and|hmm|sorry|actually|no|nope)[,. ]+)*"
               r"(?:i'?m|i am|im|it'?s|its|it is|that'?s|thats|we'?re|we are)\s+not\s+"
               r"(?P<wrong>[a-z0-9][a-z0-9'.\-]{0,19})"
               r"[\s,;.!-]*(?:but\s+)?"
               r"(?:i'?m|i am|im|it'?s|its|it is|that'?s|thats|we'?re|we are)\s+"
               r"(?P<to>[a-z0-9][a-z0-9'.\-]{0,19})[.!]?\s*$", re.I),
)
# A word that can sit in either half of that shape and mean nothing as a value.
NOT_A_NEW_VALUE = frozenset("""a an the me you it that this these those my your his her our their
thanks thank sure fair right wrong now then today tomorrow yesterday fine bad good great sorry
please yes yeah no not ok okay yet even both all much many one two three too so there here what
why how who when where true false""".split())


def _a_correction_without_a_marker(text, memory):
    """The {to, from} of a pair correction said with no "no"/"sorry" in front, or None.

    Only a value the store already holds can be taken back this way, so the line has to name an
    older fact in the half it corrects: "its Preeya not Priya" after "my name is Priya" is a
    rename, and "its raining not sunny" is a sentence about the weather that leaves the store
    alone.
    """
    said = str(text or "")
    if len(said.split()) > 6:
        return None
    for shape in PAIR_WITHOUT_A_MARKER:
        found = shape.match(said)
        if not found:
            continue
        right, wrong = extract._tidy(found.group("to")), extract._tidy(found.group("wrong"))
        if not right or not wrong or right.lower() == wrong.lower():
            continue
        if right.lower() in NOT_A_NEW_VALUE or wrong.lower() in NOT_A_NEW_VALUE:
            continue
        if not _fact_naming(memory, wrong) and not _a_person_called(memory, wrong):
            continue  # nothing on record says that, so this is not a correction of it
        return {"to": right, "from": wrong}
    return None




def _a_person_called(memory, name):
    """Whether the store holds a person under that name.

    "my sister is called anna" then "its hannah not anna" names both values with no "no" in
    front, and the name it takes back is one the store keeps for a person rather than in a fact
    of the user's own - so the pair reader has to look in both places before it says the line
    corrects nothing.
    """
    low = " ".join(str(name or "").lower().split())
    if not low:
        return False
    for entry in others(memory):
        if not isinstance(entry, dict):
            continue
        if str(entry.get("name") or "").strip().lower() == low:
            return True
        if any(str(old).strip().lower() == low for old in (entry.get("was") or [])):
            return True
    return False




# The size words after a figure ("5 thousand", "5k") are shortened forms of the number, and the
# "k" of a word that follows is not one of them: "i want to lose 5 kilos" matched "5 k" and left
# "ilos", so the correction said back "you want to lose 8ilos". A size word only counts when no
# letter follows it, which keeps "5k" and "5 k" and lets "5 kilos" and "5km" keep their word.
# A date said as a day of the month, with or without its month: "the 12th", "12 june", "june the
# 12th", "the 13th of june". A correction can move the day alone, or the day and the month.











def _stated_value(memory, key):
    """The value of `key` the line before this one stated, or None.

    A correction replaces what was just said, so the old value is the one on that line: "im
    allergic to peanuts" then "make that tree nuts" takes back peanuts, and not a food named
    three turns earlier.
    """
    said = " ".join(str(last_user(memory) or "").lower().split())
    entries = memory.get("facts_log")
    if not said or not isinstance(entries, list):
        return None
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        if " ".join(str(entry.get("text") or "").lower().split()) != said:
            return None
        if entry.get("key") == key:
            return entry.get("value")
    return None








# "my son is too" is the limit the line before just gave, said again about somebody else. The
# line names a person and agrees with what was said and nothing more, so nothing carried the
# allergy across: the son was filed with no limit at all, and every later ask about him was
# answered as if the allergy were only theirs.
TOO_AS_WELL = re.compile(
    r"^(?:(?:and|also|but|plus)\s+)?(?:my|our)\s+(?P<who>[a-z]+(?:[ -]in[ -]law)?)\s+"
    r"(?P<agree>is\s+as\s+well|is\s+too|as\s+well|also|too)$", re.I)
# The limit refused for somebody: "im allergic to nuts" / "my son isnt". Nothing is filed - a
# person with no limit is not a limit - but the line is the answer to what was just said, and left
# to the echo it read as a person whose name was "Isnt".




def _a_second_persons_limit(text, memory):
    """The limit the line before gave, carried onto the person this line names.

    Only the limit is carried, and only when the line before stated one: "my son is too" after a
    line about the weather carries nothing, and the person is filed with the words the store
    already uses for an allergy and for a diet.
    """
    low = " ".join(str(text or "").lower().split())
    match = TOO_AS_WELL.match(low)
    if not match:
        return None
    who = _canon_relation(extract.a_person_word(match.group("who")))
    if who not in extract._A_WORD_FOR_A_PERSON:
        return None  # "my budget is too" is not a person with an allergy
    theirs = _the_limit_the_last_line_gave(memory)
    if not theirs:
        return None
    giving = {"who": who}
    allergies = theirs.get("allergies")
    if isinstance(allergies, (list, tuple)):
        foods = [str(one) for one in allergies if str(one).strip()]
        if foods:
            giving["allergies"] = foods
    diet = theirs.get("diet")
    if isinstance(diet, str) and diet.strip():
        giving["diet"] = diet
    if len(giving) < 2:
        return None
    return giving










# A line that names only a date is a correction of the date on the table. The words here carry
# no fact of their own - the frame a correction is said in, the little words around a date, and
# the pronouns that point back at the person the last line named - so a line made of these and
# the new value says nothing but the value. Any other word is a subject the line brought itself.
# The words that keep the last person named as the subject: "actually her birthday is the 4th"
# is still about the birthday the line before it gave, and so is naming the relation again.







# "what is my son allergic to?", "what did i say my mum doesnt eat?", "what did i say she doesnt
# eat?": a fact the user gave about someone else, asked back. The relation names the person
# (memory["others"]), and a bare "she"/"he" is the person the last one was about.

# A relation is only the person when the mention is not a possessive in front of another noun: "my
# son is 7" is the son, "my sons school" and "my mums car" are the school and the car. What may
# follow the person is the end of the line, a punctuation mark, or a word a line goes on with.


# The fact each ask is after: an allergy or what they eat. "what should I cook for my mum" is a
# cooking question, not a recall, so a line only gets an answer from memory when it asks about
# the fact itself.
# A name the chat was given, asked about on its own: "whos meg", "who is meg again", "do i
# know a meg", "is meg my sister". The name was filed with the person ("my sister is called
# meg"), so the answer is in the chat and every one of these fell to the search hedge instead.
# A name the chat has never heard of is not claimed here, which keeps "who is the queen" a
# question about the world.

# A name that is not the whole of what they asked about is not a question about this chat: "who is
# meg on eastenders" asks about a character in a programme, so a bare-name ask only counts when the
# name is the last thing in the line (a trailing "then" or "again" is the person talking, not a
# new thing the name belongs to).

# A word that points at someone else: the ask is about them, not about the person typing.
# "her" is a person they told us about as much as "she" is: "is pasta ok for her" after "my
# daughter is coeliac" names the daughter, and with only she/he in the list it named nobody, so
# the turn went to the knowledge entry for pasta and came back about first foods.
# The same ask with the person left off the front: "whats his name", "what is she called",
# "what do i call her". The relation is the one the chat is on, so the answer is the same one.




# How many children they have: a number they gave ("i have two kids") and not a fact about the
# world, so the ask is answered from the chat. Without this it fell to the search hedge while the
# store held the count.
# Whose kids the ask is about. "how many kids does my sister have" is a question about the
# sister's family, and answering it with the person's own count states a fact they never gave:
# the words after the count decide who it belongs to.
# A count that is a decision, not a fact to recall: "how many kids should we have" is worth a
# real answer, and the store has nothing to say about it.




# The same ask about a person by the name the chat was given for them: "what do you know about
# ada". No relation word is in the line, so the pattern can only say "some word after about";
# whether that word is a person is decided by the store, which files a name with its person.
# The word for a household's children as a group. Every other about-ask names one relation and the
# store files one person under it; children are filed as several people under one word, so the ask
# about them is read from them all.
# A line that names another person and asks nothing of its own continues the ask of the turn
# before: "what do you know about my mum" then "and my dad". It is not a question about an age,
# which is what a figure in the earlier line used to make it.
# The shape is the one AGE_AGAIN already reads: the words in front of a person and no verb at all,
# because the line does not state anything of its own. The leading "and" is often gone by the
# time a reader sees the line, so the words in front of the person are optional.


# What makes a recall ask also a "more" ask: the person wants what has not been said yet
# ("what else did i say about my sister"), so a person already fully described gets the honest
# "that's everything" rather than the same sentence a second time.

# An age is asked of somebody only when the ask leads straight to them: "how old is my son", "how
# old are they", "what age do you get a bus pass" all match AGE_ASK, and only the first two are
# about a person the chat was told about. The words after the ask decide it:
#
#   how old is my son             is + my son           -> the son's age
#   how old are the kids          are + the kids        -> the children's
#   how old is sam                is + a name the store holds -> Sam's
#   how old did you say he was    did + you say + he    -> the asking verb, still the person
#   what age do kids stop napping do + kids + a verb    -> a rule's age, nobody's
#   how old should a kitten be    should + a kitten     -> the kitten's, nobody's
#   how old is a kitten when it leaves its mum   is + a kitten -> the kitten's, and "its mum"
#                                                belongs to the kitten, not to the chat
#
# The rule ask is the commoner miss: the store answered "what age can a child stay home alone" and
# "what age do kids stop napping" with "You haven't told me how old they are", denying an age
# nobody had offered to tell it, while the card that answers the rule sat unused behind it.
# The words that can be the subject of an age ask without being a relation the store files.


# The short form that repeats the ask of the turn before: "how old is my son" / "and my daughter?".
# It is the same question about another person, so it is read as one when the reply just given was
# an age ("Your son is 7.").
# The name asked for with nothing but the person: "and my dads name", "my mums name?". It is the
# elided ask the ages already read ("and my daughter?" after an age), said with the word that
# names the fact, and without it the store answered "Your dad's name \u2014 noted." as though the
# person had just told it one.
# The words that name children, as opposed to the ones that point at whoever the chat was on:
# "the kids" asks about the children and nothing else, while "their"/"they"/"everyone" take the
# nearest ages and fall back to the people the chat knows. Both are needed: "how old is their dad"
# is an ask about the dad, and a children branch that took it would answer a question nobody asked
# with a denial one line after being told.
# A friend asks about an age with the word itself: "do you remember my kids ages", "what are my
# mums age", "the ages of my kids". The ask words ("how old", "what age") are the usual way to put
# it, and a line that names the person and says "age" is the same question about the same fact.
# Without this the store never saw the ask at all and the line was answered with what the chat
# remembers in general - "nothing carries over to a new chat" - straight after the bot itself had
# said "Noted: your son is 7".
# "is it just her age", "is that old age" name an age without asking for a number: it is the
# question of whether the years explain the thing, and the person's age is not the fact wanted.
# The store read "her age" as the ask and answered "You haven't told me how old your mum is" to a
# chat that had just said she was 80 - a fact it held, denied back. The composer answers it
# ("Some forgetting is ordinary with age..."), so the store stands down on this one.
# The words that make a limit ask a question about food. "What can't I eat" has one; "what
# should I avoid" does not, and with nothing stored it is a question about the topic instead.
# "what's my diet", "what do i eat", "remind me what i can't have": the same ask about how they
# eat, which the store can answer from the diet it keeps. "what should i eat" is a request for
# ideas, not a recall, so the asking words are the ones that name the fact.
# "how do i get more veg in my diet" names the diet and asks how to eat better, which is a
# request for advice, not a question about what the store knows: read as the diet fact it was
# answered "You haven't told me about your diet." The how-to frame in front of "my diet" decides.
# The diet asks that want the fact rather than a meal. "what do i eat" and "what can i eat" are
# someone asking for a dinner - they know what they cannot eat, they said it a line ago, so
# saying it back is a receipt where a concrete, diet-aware suggestion was there to give. The
# asks that name the fact itself ("what's my diet", "what do i not eat", "am i vegan") want the
# store, and a line that opens a question with a lead-in ("and what do i eat") is picking the
# conversation back up, which is the meal again.
# A line about what someone eats only asks when it is put as a question: "what does my mum eat",
# "is my mum vegetarian". "my son will only eat bread and butter" is telling, not asking, and so
# is "my son can not eat dairy" - the words that open a question are not words that open a fact.
# A line that asks for advice, not for a fact we were told.
# What a person cannot have, said as a restriction instead of with "eat": "what cant he have"
# after "my son is allergic to nuts" is that same allergy, said the way people say it. Only the
# restriction counts, so "what should my mum have for dinner" stays a request for ideas.
# What a person can have, when the only thing kept for them is what they cannot: "what can he
# have" is the allergy answer said the other way round. It names a person, so "what can i have
# for dinner" is not read as one.
# The same ask about a food named in the line: "can he have cheese" after "my husband is lactose
# intolerant", "is cheese ok for him", "can she eat bread". Only a person is read, and the food
# named is what the answer can be about - without it the line went to the baby table, which
# answered "Yes, from six months, in small amounts" to a grown man who cannot have dairy.
# The same ask with the food named in it: "can he eat cake". A named food is the cooking entries'
# reading of their own lists when the store holds no diet or condition for that person, while a
# bare "what can she eat" is the store's, answered from whatever limit it does hold.
# A preposition after the verb names a meal or a way of serving the food and not the food
# itself, so "what can she have for lunch" is the bare ask about what she eats, which the limit
# the store holds answers: read as a named food it was left to the cooking entries, and a child
# with a nut allergy got a packed lunch with no word about the nuts.
# The everyday foods each ruled-out thing is in, so the answer to "can he have cheese" names the
# food in the line the way a person would: "cheese has dairy in it". Only the everyday names, and
# only where the food is that thing every time it is eaten.


# A line that states a fact and then asks a question: "my son is 7 and has a nut allergy, what can
# i pack him for lunch". The fact is the context of the ask, not the ask itself, so the question at
# the end is what says what the person wants to know. Without the split the store read "allergy"
# and the relation "son" and said "Your son is allergic to nuts." back, dropping the question
# entirely - while the knowledge base had the packed-lunch answer ready.












def _drop_value(memory, value, text=""):
    """'Sorry, not peanuts' takes that one back: it comes off the list of things they named.

    The list is the fact the line before it stated, and only a value on it can go, so a "not"
    about anything else ("no, not today") leaves memory alone. Nothing is put in its place, so
    the note of the turn says the value went instead of a new one arriving.
    """
    known = user(memory)
    low = " ".join(str(value or "").lower().split())
    if not low:
        return None
    for key in DROP_LISTS:
        held = known.get(key)
        if not isinstance(held, list):
            continue
        left = [v for v in held if isinstance(v, str) and not _names_this(v, low)]
        if len(left) == len(held):
            continue
        known[key] = left
        memory["correction"] = {"key": key, "value": str(value), "dropped": True,
                                "said": " ".join(str(text or "").lower().split())}
        return memory["correction"]
    return _drop_from_plan(memory, value, text)


def _plan_names(plan, low):
    """Does the plan say this value? A plan is kept as the sentence it arrived in, so the thing
    taken back is a word inside it ("Lisbon" in "Lisbon in may") and not an item on a list."""
    words = re.findall(r"[a-z0-9']+", str(plan or "").lower())
    for word in words:
        if word == low or (low.endswith("s") and word == low[:-1]) \
                or (word.endswith("s") and low == word[:-1]):
            return True
    return False


def _drop_from_plan(memory, value, text=""):
    """'Sorry, not Lisbon' after 'im going to Lisbon in May' takes the trip back with the place.

    A value taken back can be a word inside a plan rather than an item on a list, and a plan has
    no key of its own: it is the sentence the person said. Only a plan that names the value goes,
    so "sorry, not tuesday" leaves the trip to Lisbon alone, and the place goes with it - a store
    that still answers "you're going to lisbon in may" is telling them the thing they just took
    back. A city they also stated on its own ("i live in lisbon") stays: it is a fact about where
    they live, not the plan they dropped.
    """
    known = user(memory)
    low = " ".join(str(value or "").lower().split())
    if not low:
        return None
    # A month or a day inside a plan says when it happens, not what it is: "my exam is in june" /
    # "sorry, not june" took the exam with it, so the next "when is my exam" had nothing to answer
    # from. A date they want moved is a correction ("actually june not may"), and that path already
    # rewrites the plan; a take-back of a date leaves the plan where it was.
    if low in MONTHS or low in extract.DAYS:
        return None
    plans = known.get("plans")
    held = [plan for plan in (plans if isinstance(plans, list) else []) if isinstance(plan, str)]
    current = known.get("plan")
    if isinstance(current, str) and current not in held:
        held.append(current)
    left = [plan for plan in held if not _plan_names(plan, low)]
    if len(left) == len(held):
        return None
    if left:
        known["plans"] = left[-6:]
        known["plan"] = left[-1]
    else:
        known.pop("plans", None)
        known.pop("plan", None)
    city = known.get("city")
    home = isinstance(city, str) and _plan_names(city, low)
    places = known.get("places")
    if isinstance(places, list) and not home:
        left_places = [place for place in places
                       if not (isinstance(place, str) and _plan_names(place, low))]
        if len(left_places) != len(places):
            if left_places:
                known["places"] = left_places
            else:
                known.pop("places", None)
    known["plan_dropped"] = low
    memory["correction"] = {"key": "plan", "value": str(value), "dropped": True,
                            "said": " ".join(str(text or "").lower().split())}
    return memory["correction"]


def _names_this(held, low):
    """Does the value the person named name the thing on the list? Only the word itself and its
    singular or plural: "peanut" is "peanuts", and "nuts" is not something else that went."""
    held = " ".join(str(held).lower().split())
    if held == low:
        return True
    for a, b in ((held, low), (low, held)):
        if b.endswith("s") and a == b[:-1]:
            return True
    return False


# Every shape of "what were we on?" and "say that back to me": the asks about the conversation
# rather than about the world. Two places read them - the gate that decides a line is about this
# chat at all, and the reader that answers it - and they have to agree. They did not: the reminder
# wrapper comes off in `_bare`, so "remind me what we covered" arrives as "what we covered", with
# no "have" in it, and the gate had grown the shape while the reader had not, so the store called
# the line a recap and then answered it with a shrug.






# "what do i do" carries its own subject after it: "what do i do about my back" asks about the
# back and "what do i do on saturday" asks about the weekend, so the job is not the answer.






# "and what do i do again?" after a how-to asks about the task, not the job they once told us.
# The job reading is right when the line itself gave the job ("i work in a warehouse") or a
# recall is already running ("what's my name?" / "what do i do again?"); after an answer it
# means "where were we?", which `_topic_reply` puts back in their own words.




# A line about the work itself, said with a verb or a thing of the job rather than a role:
# "i teach year 4", "i stack shelves", "i mostly do spreadsheets". Once the job has been told,
# such a line is a detail of it, so a bare "what do i do" after one is still about the job they
# gave us - the same way "i work in a warehouse" then "what do i do" is.
# Words that make the same line something else that wants an answer: a body, a feeling or a
# problem. "i hurt my back at work" is a back question, not a detail of the job.
# A line with a time of day in it is about the day, not about the job: "i clean the kitchen every
# night" and "im cooking a curry tonight" are things happening now, whatever words of the work
# they carry.






# The words a line can carry beside the job and still be a line about the job alone: how the
# work is arranged ("on the night shift", "part time", "just started"), never news of its own.




# The words a place is written with that say nothing about the place: "i work *at the* co-op".




# "what's the noise again?" asks about a thing by name rather than about the whole chat. Only the
# named-thing form is one: "what's the time" is a question about the time, unless they said it.
# A line that asks for a recap in the words people use for it other than the ones the checks
# above already carry: "what did we talk about", "summarise our chat", "give me a summary".
# Only a word that points at the conversation: "today", "so far" and "everything" are time
# and size words as often as they are this chat (`summarise the news today`, `summarise this
# article so far`), so they do not stand in for it here - `SUMMARY_ASK_FILLER` still strips them
# from a bare ask (`summarise everything`).


# The words that only wrap a bare ask: "can you give me a quick recap please" is the same ask
# as "recap", so nothing substantive is left once these and the summary word come out. It has
# its own name because main's `ASK_FILLER` below is a frozenset of pronouns and verbs, and the
# later definition of a name wins: the regex was silently replaced and `_summary_ask` raised.





# "and which knee was it", "which side did i say": a detail they gave earlier, asked for by the
# thing it is about. It is the same ask as "what did i say about my knee", and no reader read a
# which-ask as a recall at all: eight turns after "its on the outside of the knee" the bot said
# "I'm not sure about that one, sorry" while the line was in the chat.

# "what day did i say it was due", "and what size did i say": the same ask as the which-ask, with
# the attribute in front of it instead of the thing. The plain "what did i say it was due" is read
# and quotes the line; the attribute in front of it was not, and a card took the turn on the word
# in the ask (a school project "due friday" got the late-period card).

# A word that points back at what was said rather than naming a thing: "which one was it" and
# "which bit was it" have no line of their own to find, so the ordinary reply keeps that turn.




# "what subject did i say i was revising": the kind of detail is in front of the verb, where
# `ATTRIBUTE_SAID` names it from a fixed list. The kind's word is not in the line that answers it
# ("subject" for "biology gcse"), so the line is found by the rest of the ask or by the kind.

# The words that are not a kind, so "what time did i say" keeps the reply it had.










def _budget_sign(text, budget):
    """The currency sign before the same amount in the line they typed, or ""."""
    number = re.sub(r"[^\d.,]", "", str(budget or ""))
    if not number:
        return ""
    for match in re.finditer(r"([\u00a3$\u20ac])\s?([\d][\d,.]*)", str(text or "")):
        if re.sub(r"[^\d.,]", "", match.group(2)) == number:
            return match.group(1)
    return ""












# A number in what the store says back about an animal ("two cats"): what makes "Still two cats."
# a second wording of the fact, where "Still a cat." would be a different one.








# A line that is nothing but one of their facts named back to me - "and my job?", "my town?",
# "what about my budget?" - is the plain ask for that fact, not a question about the world. It
# is only read that way when the store already holds the fact: answering a miss would tell them
# they never said something they did ("and my shift?" after "i work nights").


# The words that name each fact and nothing else: "and my job?" is that fact named, while "my
# budget is tight" and "my job at the bakery" are lines saying something new about it.
# Words that hang off the name without saying anything about it.








# The person, in the words a line about them uses. "which city" on its own is a question about
# the world; "which city did i say" is a question about this chat.
# "what city should i visit in spain" names the person too, and it is a question about Spain:
# the store has no place of theirs to say back, and "You haven't mentioned a place yet." answers a
# question nobody asked. A place line that asks for a recommendation is left to the topics.
# "best" on its own is not one of those - it is often the person's own wording asked back
# ("which city did i say i liked best") - so only the phrases that ask for a recommendation.
# ...and never when the line is asking what they said. "which city did i say i want to visit"
# has "visit" in it because that is what they are asking back out of the chat, and the store's
# answer is one it already has: "You mentioned Lisbon."

# "Where did i grow up" names the growing up rather than the place, so the place ask above it does
# not read it and the store fell to the search hedge while it had "Dublin" on file.


# A line that is nothing but how they feel: "im scared", "so nervous", "worried sick". On its own
# it is not a subject and not a question - it is about whatever they said a moment ago, and the
# reply has to say that thing back. The generic worry lines answer six different frightening
# things with one sentence, which is the bot not listening to any of them.

# What makes a feeling be about something that has not happened yet: a day or a clock word. "my
# dad is in hospital" has none, and a hospital is not an event to be nervous before.


# A day something happens on: "tomorrow", "on monday", "this weekend". Only then is "it is worse
# the days before than on the day" true. A period ("in june", "this month", "soon") has no day in
# it, so the same sentence would be about a day that does not exist, and the worry is the
# not-knowing itself.


# A question that happens to name a date is still a question: "how do i stop being nervous about my
# driving test on monday" is not news about Monday, and reading it back gives a fragment ("How you
# stop being nervous about your driving test on monday.") that is nobody's sentence.


# A course of treatment is not a day it happens on, and it is heavier than nerves: "my mum starts
# chemo next week" is not a thing to say "it is usually worse in the days before than on the day"
# about. Those keep whatever answered them.


# The word that stands for the person again later in the same reply: "frightened for your mum ...
# any less help to her". A reply that says "them" about one woman is the machine talking, so the
# kin word decides, and the ones that can be either ("friend", "partner", "child") take "them".
OTHER_NOUNS = frozenset("""friend mate partner baby child kid children kids cousin parent parents""".split())








# A body that cannot be said without the sentence in front of it: it opens on a demonstrative
# ("That is...", "Of course you are") or on a phrase whose "it" is the sentence ("Nerves about
# it"). One of these is only used when the news is on its own line above.




def _a_feeling_about_their_own_news(text, memory):
    """This line is a feeling about the thing they just said, and the store answers it.

    A bare "im scared" is read by the small-talk topics as small talk, so a candidate from there
    would take the turn; this says the store read the line whole and names what it is about. It is
    one of the lines the arbiter's single hook asks about, not a hook of its own: a second
    `TAKES_AS_IT_COMES` in this module would shadow the first one and take the store's recall and
    `when` asks out of service.
    """
    try:
        return _a_feeling_about_what_they_said(memory, _bare(_folded(text, memory))) is not None
    except Exception:  # noqa: BLE001 - a reading that fails just leaves the line to the others
        return False


# An ask to hear the last answer again is the store's line and no other module's, whatever else
# proposed on it. "how long should i rest a sprained ankle" / "how long did you say" is a person
# asking for the length they just read; the answers module read the ask as a fresh question and
# proposed a different ankle entry, which the specialist rule handed over, so the repeat was
# answered with other numbers than the ones on the screen (two or three days, two to six weeks,
# where the answer above it said one to two and four to six). The arbiter asks this before the
# never-repeat rule and the specialist fit (README.md, "Interface"), and this says yes only on a
# line `_repeat_ask` read whole: "how long did you say to cook it" and "what did you just say"
# are the store's, while "how long do i rest a sprained ankle" keeps its entry.
def takes_as_it_comes(text, memory=None):
    """True when the line is an ask for the bot's own last answer, so the store answers it."""
    if not isinstance(memory, dict):
        return False
    return _repeat_ask(text, _folded(text, memory), memory)


# This module has one hook, and the store already has one (`TAKES_AS_IT_COMES`, for the feeling
# about what they just said and the rest). A second name would shadow the first and take those
# lines out of service, so this reading is added to that hook rather than put beside it. Nothing
# here may alias it: the name is bound again further down the file, and a module-level copy taken
# at import time either freezes an older definition or, if the definitions move, does not exist yet
# and takes the whole store down with a NameError the runtime hides.
# "is that enough" is a follow-up about the amount the person just gave, and it was answered with
# a sign-off that fits any message: "i run 5k twice a week" / "is that enough" got "Alright then -
# good luck with it." The answer a turn earlier already named the figure to aim at, so the store
# reads the two numbers together: what they do, and what the answer said to aim for.

def _the_ask_about_how_it_went(text, memory):
    """This line asks how the thing they told us about went, and only they can say.

    "i had an interview today" / "how did it go" is a question about the person's own day: the
    knowledge base read the word "interview" and answered how to prepare for one, one line after
    they said it was over, and the specialist rule handed it the turn. The ask names no subject
    of its own on a line that does not, so the store says it read this line whole
    (bot/memory/thread.went).
    """
    try:
        return thread.went(text, memory) is not None
    except Exception:  # noqa: BLE001 - a reading that fails leaves the line to the others
        return False


# The check above is called from the hook the module actually exports, at the end of the file:
# a `TAKES_AS_IT_COMES` defined here would be shadowed by that one and never asked.


def _a_count_from_the_date(text, memory):
    """Whether the ask is a count from a date already on file: "how many weeks till that".

    The date is in a line they said, so the answer is arithmetic on it and this store's line; a
    knowledge entry for the thing named in the ask ("the driving test") answers what that thing
    is, which is a different question.
    """
    try:
        return bool(until_answer(text, memory))
    except Exception:  # noqa: BLE001 - a reading that fails claims nothing
        return False
# A line that asks for a figure and nothing else: "how many weeks", "how long", "how much
# longer", "how far". `repeat.the_figure_asked` hands back the whole sentence the figure is in,
# which is the sentence the person has just read: the answer here is the figure itself.
# "how often" and "how soon" are not asks for a length: "how often should i do them" after a back
# answer was handed "Two to six weeks.", and "and how often" after a washing-machine answer was
# handed "About two hours." Both are the length of something else, said on a line that asked how
# frequently. Only the asks that want a figure of a unit are read here.
# An amount of money is the family a bare "how much" asks for; the time families are the default
# for "how long" and for "how many" with no unit named.
FIGURE_MONEY = ("money",)

FIGURE_ASK = re.compile(
    r"^\W*(?:(?:and|but|so|ok|okay|right|then|oh|well)\W+)*"
    r"how\s+(?P<asked>many|much|long|far)\b(?P<rest>.*)$", re.I)
# What may stand around the unit on such a line without naming a thing: "how many weeks then",
# "how long do you reckon". A content word that is not a unit ("how long should i rest it") means
# the line is asking about a thing, and that thing has an answer of its own.
FIGURE_FILLER = frozenset("""a an the it its that this them those there here then now again
    roughly exactly approximately about around all told overall altogether total more less much
    many long do does did will would should can could you i we they he she reckon think suppose
    guess say again please for of in at on to be have has had is are was were and but so if
    when after before time times per each""".split())
# What may follow the unit and still leave it the noun of the figure. "eight to ten weeks is a
# realistic build" is a figure; "the 5 to 6 minute egg" is a length used as an adjective, and a
# card that says it is not answering "how many minutes".
FIGURE_AFTER = frozenset("""is are was were and or a an the in for of to on at by after before
    now then so but if when that from with without each every per of till until into about
    to around roughly or while than which where""".split())


def _the_unit_asked(line):
    """The unit families this line asks a figure in, or None when it names a thing of its own."""
    found = FIGURE_ASK.match(" ".join(str(line or "").lower().split()))
    if not found:
        return None
    units = []
    for word in re.findall(r"[a-z']+", found.group("rest")):
        if word in FIGURE_FILLER:
            continue
        family = None
        for name, words in FIGURE_UNITS.items():
            if word in words:
                family = name
                break
        if family is None:
            return None  # a thing, not a unit: the thing has an answer of its own
        if family not in units:
            units.append(family)
    per_week = re.match(
        r"^\W*(?:a|an|per|each)\s+(?:%s)\b" % "|".join(
            re.escape(word) for word in sorted(
                {word for family in FIGURE_TIME for word in FIGURE_UNITS[family]}, key=len,
                reverse=True)),
        found.group("rest") or "", re.I)
    if per_week and found.group("asked").lower() == "much" and set(units) <= set(FIGURE_TIME):
        # "how much a month" is a rate of money and not a length: the period is what the amount is
        # per, so "three to six months" - the length of the buffer the answer names - is not what
        # was asked. Only the article makes it a rate: "how long a month" is not a line, and a
        # line with a thing of its own in it ("how much a month do i need") never gets here.
        return FIGURE_MONEY
    if not units and found.group("asked").lower() == "much":
        # An amount with no unit named is money, and a bare "how much" is a price rather than a
        # length. After "should i get a new phone or fix mine" / "its cracked", the answer on the
        # screen said "Repair it if the phone is under four years old ... £50 to £120 at a local
        # shop", and "how much" was handed "Under four years." - the default families here are
        # the time ones, so a price question picked out a time figure. Only a bare "how much" is
        # money: "how much water" names its unit and keeps it.
        return FIGURE_MONEY
    if not units and found.group("asked").lower() == "many":
        # "how many was it" names no unit at all, so it asks for a count and not for a length.
        # The default family here is a length, and the count ask was handed the last answer's
        # figure: eight turns after "theres going to be 8 of us", "how many was it" answered
        # "4 to 5 hours." A bare "how long" is still a length and keeps the default.
        return None
    return tuple(units) or FIGURE_TIME


# A length that belongs to an action rather than to what the answer is about: "ice it for 20
# minutes at a time with a cloth round it for the first two days" is how long to ice it, not how
# long a knee takes to heal, and "two days" there is not the answer to "how long". A figure whose
# own clause says when or how often it is done is a duration of the doing, and it is handed back
# as a confident number where the honest reply is that the length is not in the answer.
ACTION_DURATION = re.compile(
    r"\bat a time\b|\bfor the first\b|\bfor the next\b|\bin a row\b|\beach time\b"
    r"|\bthe (?:first|next|last|coming|following|remaining|final)\b"
    r"|\b(?:once|twice|three times|a few times) a day\b|\ba day or two\b|\bper session\b",
    re.I)


# An amount that belongs to a step rather than to what the answer is about: "raise the standing
# order by 10 pounds whenever a bill or a habit goes" states 10 pounds as the size of a move, and
# the clause says when it is made. A bare "how much" after the same answer was handed "10 pounds."
# where the answer's own figure is "10 to 20 per cent of what you take home" - so a figure whose
# clause says when or if it happens is a step's amount, the money analogue of ACTION_DURATION.
ACTION_AMOUNT = re.compile(
    r"\b(?:whenever|when|if|once|each time|any time|every time|in case|unless)\b", re.I)


def _the_clause(said, start, end):
    """The clause of `said` a figure sits in, between the punctuation either side of it."""
    left = max(said.rfind(mark, 0, start) for mark in ".;:")
    rights = [at for at in (said.find(mark, end) for mark in ".;:") if at >= 0]
    return said[left + 1:min(rights) if rights else len(said)]


# An amount, with the sign in front of the number or the word for it after it, and a range read
# whole: "£50 to £120" is one amount and is handed back as it was said.
A_MONEY_FIGURE = re.compile(
    r"(?:£|\$|€)\s*\d[\d,]*(?:\.\d+)?(?:\s*(?:to|-|or)\s*(?:£|\$|€)?\s*\d[\d,]*(?:\.\d+)?)?"
    r"|(?<![\d.,])\d[\d,]*(?:\.\d+)?(?:\s*(?:to|-|or)\s*\d[\d,]*(?:\.\d+)?)?\s*"
    r"(?:pounds?|quid|dollars?|euros?|pence)\b", re.I)


# A share of what they take home answers "how much" when the answer states no sum of money, and it
# is what the saving answer's own figure is: "pick an amount you will not miss, 10 to 20 per cent of
# what you take home" is the amount, and reading only pounds in it left the line with the one sum
# the answer states as an example of a step ("raise the standing order by 10 pounds whenever a bill
# or a habit goes") or with nothing at all.
A_PERCENT_FIGURE = re.compile(
    r"(?<![\d.,])\d[\d,]*(?:\.\d+)?(?:\s*(?:to|-|or)\s*\d[\d,]*(?:\.\d+)?)?\s*"
    r"(?:per\s?cent|percent|%)", re.I)


def _the_money_figures(said):
    """Every amount of money the answer states, in order, as (words, definite)."""
    # The amount as it was said, without the punctuation that ended it: the caller puts the full
    # stop on, and "£60 to £120," came back as "£60 to £120,.".
    out = []
    for found in A_MONEY_FIGURE.finditer(said):
        if ACTION_AMOUNT.search(_the_clause(said, found.start(), found.end())):
            # The clause says when or if it happens, so the money is the size of a step and not
            # the amount the person asked about.
            continue
        out.append((found.group(0).strip().rstrip(",;:"), True))
    if out:
        return out
    for found in A_PERCENT_FIGURE.finditer(said):
        if ACTION_AMOUNT.search(_the_clause(said, found.start(), found.end())):
            continue
        out.append((found.group(0).strip().rstrip(",;:"), True))
    return out


def _the_figures_in(said, units):
    """Every figure of these units the answer states, in order, as (words, definite)."""
    if "money" in units:
        return _the_money_figures(said)
    words = sorted({word for unit in units for word in FIGURE_UNITS[unit]}, key=len, reverse=True)
    unit = r"(?-i:%s)" % "|".join(re.escape(word) for word in words)
    pattern = re.compile(
        r"(?<![\d,])\b(?P<qual>%s\s+)?(?P<num>%s)(?:\s*(?:-|to|or)\s*(?P<more>%s))?\s*"
        r"(?P<unit>%s)\b(?P<extra>\s+\d{1,3})?(?P<after>[^.;:!?,]*)" % (
            FIGURE_QUALIFIER, FIGURE_NUMBER, FIGURE_NUMBER, unit), re.I)
    out = []
    for found in pattern.finditer(said):
        after = found.group("after").strip().lower()
        next_word = (re.findall(r"[a-z']+", after) or [""])[0]
        unit_word = found.group("unit").lower()
        one = not unit_word.endswith("s") and unit_word not in ("km", "kg", "lb", "lbs")
        if one and next_word and next_word not in FIGURE_AFTER \
                and next_word not in {word for family in units for word in FIGURE_UNITS[family]}:
            # "the 5 to 6 minute egg": a singular unit with a word after it is an adjective, not
            # the noun of a figure, and a card that says it is not answering "how many minutes".
            continue
        # The figure alone, not the rest of the sentence it is the subject of: "eight to ten weeks
        # is a realistic build" is handed back as "Eight to ten weeks."
        pieces = [found.group("qual") or "", found.group("num"),
                  (("to " + found.group("more")) if found.group("more") else ""),
                  found.group("unit"), found.group("extra") or ""]
        said_figure = " ".join(piece.strip() for piece in pieces if piece.strip())
        # A rate is not a figure the person can plan by: "three runs a week" and "20 minutes
        # three times a week" belong to the plan, not to the ask about the length of it.
        if re.match(r"(?:a|an|per)\s+", after) or next_word == "per":
            continue
        if ACTION_DURATION.search(_the_clause(said, found.start(), found.end())):
            # A length of the doing, not of the thing: "for the first two days", "20 minutes at a
            # time". The clause says so, and the number is not the one that was asked for.
            continue
        definite = found.group("num").lower() not in ("a", "an")
        if not definite:
            continue
        out.append((said_figure, definite))
    return out


def _the_figure_the_answer_names(text, memory):
    """The figure the answer on the screen named, on a line that asks only for a figure, else None.

    "how many weeks" after "Each week add a minute to the jog ... in about eight weeks you will run
    20 minutes" names no thing, so no entry is reached and the entry the topic does reach answers
    the *unit* instead: the warm-up card, "Five to ten minutes." Nobody asked that. The figure is
    in the answer already on the screen, and `bot/memory/repeat.py` has read the line all along -
    but its reply was only ever asked for under the composer's last-resort module, and an entry
    that answers the wrong card wins the turn first.

    The store is where the answer already said belongs, so the reading is claimed here. It is the
    figure said back and not the sentence it is in, because the sentence is one the person has
    just read.

    Narrow on purpose: the line asks for one kind of figure and names nothing else, the answer is
    a knowledge answer from a turn or two back, the figure is definite and of the kind asked for,
    the unit is the noun of it, a rate ("three runs a week") is not a figure, and a length the
    answer gives for doing something ("for the first two days", "20 minutes at a time") is a
    duration of the action, not the length of the thing the person asked about.
    """
    if not isinstance(memory, dict) or not isinstance(text, str):
        return None
    units = _the_unit_asked(text)
    if not units:
        return None
    # A figure the person gave about their own life is theirs, not the answer's. "my back has
    # been bad for a week now" then "how long have i had it now" was handed "Six weeks." - the
    # follow-up figure at the end of the back answer - and the week they had just said was in the
    # chat all along. The same line after "i started running two weeks ago" was "20 minutes.", the
    # length of the run-walk in the answer. Only where the person's own figure is there to give:
    # with nothing of their own, the answer on the screen is still the best thing the store knows.
    theirs = repeat_the_line.the_figure_they_gave(text, memory)
    if theirs:
        return theirs
    # An amount per month is not a length in months: an answer that states rates is a table of
    # them, and the saving answer is the one that belongs on the line.
    rate_ask = bool(A_RATE_ASK.match(" ".join(text.lower().split())))
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    for back, turn in enumerate(reversed(turns[-LOOK_BACK_FIGURE:]), 1):
        if turn.get("module") not in ANSWER_MODULES:
            continue
        said = " ".join(str(turn.get("bot") or "").split())
        if not said or len(said) < FIGURE_ANSWER_LEN or said.rstrip().endswith("?"):
            continue
        if rate_ask and A_RATE_STATED.search(said):
            continue
        if LISTED_FIGURE.search(said):
            # A list of figures on one unit ("6 minutes for a runny yolk, 7 for jammy, 9 to 10 for
            # hard boiled") is the answer the person needs, and picking one of its numbers is not:
            # "how long do i boil an egg" / "and how long?" came back as "6 minutes." where the
            # answer had already said the whole range.
            continue
        found = _the_figures_in(said, units)
        if not found:
            if _a_figure_of_those_units(said, units):
                # The answer does state a figure of the kind asked and this reader cannot hand
                # back exactly one of them, so the store says nothing rather than reading an
                # older answer: the figure the person wants is the one on the newest answer, and
                # a number out of an answer two turns back is about something else.
                #
                # "im saving for a car" / "i need about 4000" / "i put away 300 a month" /
                # "so how long" was answered "About 3 years." - the 40 months of the table two
                # turns back - while the answer just above it said "£4,000 at £300 a month is 14
                # months". The scan "a month" out of "300 a month is 14 months" as an
                # indefinite figure and moved past the 14, so nothing was read off the newest
                # answer and the reader fell through to the one behind it. The module that works
                # the figure out (`bot/modules/saving_followup.py`) answers this line with the
                # 14 months.
                return None
            continue
        stated = {(figure.lower()) for figure, _ in found}
        if len(stated) > 1:
            # Two figures of the same kind: the answer is not one figure, and the one behind it
            # is about an older thing, so there is nothing to hand back here.
            return None
        figure = found[0][0]
        return figure[:1].upper() + figure[1:] + "."
    return None


def _a_figure_of_those_units(said, units):
    """True when the answer states a number with a unit of one of these families after it.

    The loose reading, used only to tell "this answer says a length and I cannot read which"
    from "this answer says no length at all": the second may hand the line to an older answer,
    the first may not.
    """
    if "money" in units:
        # Money is its own family and has no entry in FIGURE_UNITS: an amount is written with a sign
        # or with a word for it, so the loose reading is the two money patterns themselves.
        return bool(A_MONEY_FIGURE.search(said) or A_PERCENT_FIGURE.search(said))
    words = sorted({word for unit in units for word in FIGURE_UNITS[unit]}, key=len, reverse=True)
    if not words:
        return False
    unit = r"(?-i:%s)" % "|".join(re.escape(word) for word in words)
    pattern = re.compile(
        r"(?<![\d,])(?:%s|%s)\s*(?:-|to|or)?\s*%s\b" % (FIGURE_NUMBER, r"\d[\d,.]*", unit),
        re.I)
    return bool(pattern.search(said))


# A second figure of the same kind said without the unit, as a list: "6 minutes for a runny yolk,
# 7 for jammy, 9 to 10 for hard boiled". The card is answering this ask already.
LISTED_FIGURE = re.compile(r"(?:,|;)\s*\d+(?:\s*(?:to|-|or)\s*\d+)?\s+for\b", re.I)

# A "how much a month" line asks for an amount per month, and the answer to it is a table of
# rates: "For £4,000: £100 a month is 40 months, £250 a month is 16 months". Reading one figure
# out of that table gave "4 months." to the person who asked what to put by each month - the
# figure there is how long the saving takes, not the amount, and the saving answer owns the line.
A_RATE_ASK = re.compile(
    r"how\s+much\b[^.?!]*\b(?:a|per|each|every)\s+(?:day|week|month|year)\b", re.I)
A_RATE_STATED = re.compile(
    r"(?:£|\bgbp\s*)?\d[\d,.]*\s*(?:pounds?\s+)?(?:a|per|each|every)\s+"
    r"(?:day|week|month|year)\b", re.I)

# The modules whose reply is an answer from the world: a figure is read out of those. A short
# reply is left alone - "20 minutes." already answers the next "how long" without a reader.


def _the_time_they_put_right(memory):
    """The reply to a line that does nothing but move a routine time, or None.

    "i get up at 6" then "i meant seven" is one word put right, and the store has always kept it
    (`times.keep`). But the reply to that line came from the composer's shrug ("I'm
    listening - say more if it helps.") or, after "make it 7", from the search hedge: the bot had
    just moved the time and said nothing about it. So the time is said back in the words the store
    holds it in, and the one it replaced is named, because a correction is what the line is:
    "Got it - you're up at 7, not 6."
    """
    fixed = memory.get("fixed_time")
    if not isinstance(fixed, dict):
        return None
    # The time is moved while the line is being read, so its turn is this one: `turns` holds the
    # turns before it. Any other turn is another line, and this reply is not about that line.
    if int(fixed.get("turn") or -1) != len(memory.get("turns") or []):
        return None
    at = " ".join(str(fixed.get("at") or "").split())
    if not at:
        return None
    what = " ".join(str(fixed.get("what") or "").split())
    said_back = (ROUTINE_SAY_BACK.get(what) or "You {what} at {at}.").format(at=at, what=what)
    said_back = said_back.rstrip(" .")
    was = " ".join(str(fixed.get("from") or "").split())
    if was and was != at:
        said_back += ", not " + was
    return "Got it - " + said_back[0].lower() + said_back[1:] + "."


def respond(text, memory):
    """The store's reply, with the names in it written as the store holds them.

    A plan is quoted back in the words they typed, so a name in it came back in their spelling:
    "we r going 2 spain in may" -> "You r going 2 spain in may.". Every route out of the store
    ends here, so the names are written once, at the end.

    Then the floor under it: never the same words twice in a row. The store answers each line on
    its own terms, so two different lines can be answered by the same words - "is she vegan" and
    then "what does my mum eat" both reached the one line the store writes about a diet nobody
    gave, and the person read the same sentence twice. Whatever route the reply came by,
    `bot/memory/again.instead` frames it as the repeat it is - after the names are written, so
    the words it compares are the words on the screen.
    """
    from ..memory import again as same_again
    from ..memory import not_this
    from ..memory import trips
    text = _without_the_shrug_at_the_end(text)
    # A line that only moves a time the store already holds ("i meant seven") is answered by the
    # store: nothing else has anything to say about it, and what did say something handed the
    # person a shrug or the search hedge over a correction the store had just taken.
    put_right = _the_time_they_put_right(memory)
    if put_right:
        return put_right
    # A line that points back at what was said before, in a chat with nothing in it yet ("same as
    # before", "and the other one"): nothing below reads it, and the small-talk pools answered it
    # with a receipt of a line nobody had given. There is no before to go on, so the store says so
    # and asks for the thing itself - read here, above every reader, because on a chat that has
    # said something these lines are theirs and go on being read exactly as they were.
    pointed_at_nothing = _points_back_at_nothing(text, memory)
    if pointed_at_nothing:
        return pointed_at_nothing
    # A recall frame with nothing behind it: "what did i say about it", "what did i say i lost".
    # Read above the pointer asks, because the pointer reader read the "it" in the recall and
    # answered a request for their own words as a question about a subject.
    recall_frame = _a_recall_frame_about_nothing(text, memory)
    if recall_frame:
        return recall_frame
    # An ask whose only subject is a pointing word, in a chat with nothing behind it: "how do i
    # do it", "how long will it take", "do that again". The "it" has no thing to be yet, and the
    # turn was answered with a search hedge ("I'm not sure about that one, sorry - I'd rather not
    # guess") or a shrug ("Fair enough."), neither of which asks the one question that would let
    # the person get an answer.
    ask_about_nothing = _an_ask_about_nothing(text, memory)
    if ask_about_nothing:
        return ask_about_nothing
    # "how am i doing" with a figure for the plan in the chat is answered from that figure
    # (`bot/memory/goals.py`). Without it the line is a question about a diet in general and the
    # knowledge base's paragraph stands - and on a chat about a half stone that paragraph was an
    # arithmetic card ("Divide it by 2: half of 46 is 23..."), which answers a question nobody
    # asked. Both halves are needed: a line that is not this ask, or a chat with no figure, gets
    # Nothing from here and goes on exactly as it did.
    from ..memory import goals as _goals_progress
    going = _goals_progress.a_progress_asked(text, memory)
    if going:
        return going
    # An ask about what they said or were worried about, in a chat that has said nothing: "what was
    # it i was worried about". Read as a line about a worry it got advice about worrying ("Write
    # down what's actually at stake"), which invents a feeling nobody named.
    recall_about_nothing = _a_recall_about_nothing(text, memory)
    if recall_about_nothing:
        return recall_about_nothing
    # "what did i say her birthday was" is the direct ask with a wrapper round it, and the reader
    # that keeps that slot answers it; read as a topic instead, the last line they said about
    # anything came back as if it were the answer.
    behind = _the_ask_behind_the_recall(text)
    if behind:
        direct, attribute, possessive = behind
        answer = respond(direct, memory)
        if answer:
            return answer
        if _a_word_for_the_slot(memory, attribute):
            # They said it in a shape the slot reader does not read ("hes a labrador, 9 weeks
            # old" is an age the store never filed), so a line saying they never told me would
            # deny what they said. The store's own reply to the line as asked quotes it instead,
            # and that is the honest answer.
            behind = None
        else:
            # Nothing is filed for that slot: the honest line is that, since the reader for it
            # has just said it holds nothing, and a line about something else is not an answer.
            theirs = "your" if possessive in ("my", "our") else possessive
            return pick(["You haven't told me " + theirs + " " + attribute + ".",
                         "I don't have " + theirs + " " + attribute + " from you yet.",
                         "You haven't mentioned " + theirs + " " + attribute + " to me."], memory)
    # The ages of the children the store counts, given one at a time ("ones 7 and ones 4" after
    # "i have two kids"): the line names no group, so nothing else reads it and the store's own
    # echo said the line back while keeping nothing.
    ages_of_the_children = _the_ages_of_the_children(text, memory)
    if ages_of_the_children:
        return ages_of_the_children
    # A line that only rules a place out is not a line about that place: it is answered first,
    # because every reader below would answer about the place they had just taken back.
    ruled_out = not_this.reply_for(text, memory)
    if ruled_out:
        return ruled_out
    told_about_the_trip = trips.reply_for(text, memory)
    if told_about_the_trip:
        # A trip said plainly, or a detail added to one the conversation is on, is answered
        # about the trip: the month it is in, the people going, and how the journey goes. Read
        # here rather than inside the store's own reply so it comes before every reader below
        # that would answer the trip's subject instead.
        return told_about_the_trip
    # A length the person gave about their own life, asked back with nothing named ("how long
    # has it been" three turns after "my back has been bad for a week now", "how long have i had
    # it now" after "i started running two weeks ago"). The unit reader below reads only a line
    # that names its unit ("how many weeks"), so this shape fell past it and the answer on the
    # screen was quoted instead - a length of something else entirely. Their own words are the
    # answer while the length is in the chat.
    if repeat_the_line.A_BARE_DURATION_ASK.search(" ".join(str(text or "").lower().split())):
        theirs = repeat_the_line.the_figure_they_gave(text, memory)
        if theirs:
            return theirs
    if repeat_the_line.A_PAY_WORD.search(" ".join(str(text or "").lower().split())):
        # An ask for pay names its figure in a word the unit reader has no family for: "how much
        # is my wage" names no unit at all, and "how much do i make" names its pay in a verb the
        # keywords drop. So the wage the chat holds was read back only when the ask happened to
        # carry a unit word, and the person asking for their own pay got the budgeting card. The
        # figure they gave is the answer to any ask for it, and the reader below is where the
        # judgement words that make it a different ask are refused.
        theirs = repeat_the_line.the_figure_they_gave(text, memory)
        if theirs:
            return theirs
    if repeat_the_line.how_long_its_been(text):
        # The same ask with the thing named instead of "it" ("how long has my back been like this
        # now"): the unit reader names the back and stands down, so the store says the figure the
        # person gave, which is what the line asked for.
        theirs = repeat_the_line.the_figure_they_gave(text, memory)
        if theirs:
            return theirs
    figure = _the_figure_the_answer_names(text, memory)
    if figure:
        # The figure the answer on the screen named, on a line that asks for nothing else: said
        # back as the figure, because the sentence it is in is one the person has just read.
        return figure
    # A length ask about a pregnancy the chat holds is answered here, before the figure they gave
    # is looked for: "how many weeks am i" is a count of weeks in a line of theirs, so the reader
    # for a figure said back took it ("You said 12 weeks.") where the number they gave is the
    # length of their pregnancy and is said as one ("Twelve weeks.").
    along = _how_far_along(memory, _bare(_folded(text, memory)))
    if along:
        return along
    theirs = repeat_the_line.asked_back(text, memory)
    if theirs:
        # A recall ask about a figure of their own is answered from the line they gave it on,
        # before any entry is looked up for the thing it names. "how long am i going for" after
        # "we fly out on the 12th for 10 days" reached the departure card and answered about
        # getting to the airport two hours early, and "how many nights did i say" answered with
        # when to book flights - both while the nights and the days were in their own line. The
        # reader is narrow (bot/memory/repeat.py, `asked_back`): a recall cue, a short line, the
        # thing named in a line they said, and one figure of the kind asked for.
        return theirs
    reply = _the_store_reply(text, memory)
    if not isinstance(reply, str) or not isinstance(memory, dict):
        return reply
    reply = _the_places_are_written_as_names(reply, memory)
    # Two lines are the ones whose repeat is the point. A line that asked for the whole of the
    # answer: the reply opens "All of it:" because the person asked for that, so framing it
    # again as "Same answer, and it covers this:" takes the lead-in off and says the bot decided
    # to repeat itself - "my name is sam" / "all of it" came back as that, about a greeting.
    # And a request to hear the answer again, which is handed the words and not a note that they
    # were said before: the never-twice rule is about answering twice, not about being asked
    # twice.
    if not WHOLE_ASK.match(str(text or "").strip().lower()) \
            and not _asks_to_hear_it_again(text, memory):
        framed = same_again.instead(reply, text, memory)
        if framed:
            return framed
    return reply


def _asks_to_hear_it_again(text, memory):
    """True for the one turn where the same words are the answer: "what did you say earlier".

    STYLE.md's rule is about answering twice, not about being asked twice: a person who asks to
    hear the last answer again is handed it, and framing that as "Same answer, and it covers
    this:" says the words were volunteered again rather than asked for.
    """
    try:
        return _repeat_ask(text, _folded(text, memory))
    except Exception:  # noqa: BLE001 - an unreadable line keeps the floor under the reply
        return False






# A follow-up about a detail of their own news: "i bought a new bike on saturday" / "how much
# did it cost". The store has nothing to say, because they never said, and the honest answer is
# to ask them rather than to point at a search engine or hand back a fact sheet. Only a short
# question that leans back on the last line ("it", "that", "we") is read this way, and only one
# that asks about a detail and names nothing of its own: "how long should i cook it" names a
# step and belongs to the knowledge base.

# The words a short question about a detail is built from. Anything else names something of its
# own, and the line is not the elastic "and how much was it?" this reader is for.
# A bare ask of one of these is about the world: "how much", "how many", "how long", "how old"
# with nothing pointing back at what they said. "how far" and "which area" do point back, and
# "how much did it cost" carries its "it", so those are still theirs.
# ... and neither is the length of the thing itself: "i'm learning guitar" then "how long does it
# take" asks the bot how long learning takes, which is the thing they want to know and not a
# detail they left out. "How long did it last" about a film is their own detail and is still
# asked back, so only the taking and the lasting of an activity are read as the world's.
# A line that opens on a question word or the auxiliary that carries one is a question about
# the world, whatever punctuation it was typed with: "how much does it cost", "is it worth
# getting a flu jab", "should i ring the vet". Its words are what they want to know, not news
# with a detail missing, so the store neither asks it back nor reads it as something they told us.
# A line that states a want, a need or a plan is not a piece of news with details in it: "i want
# to save for a house" then "how much" is a question to the bot, and the bot has an answer.


# An ask about a place that is narrower than the trip: the town they named does not answer it.


# The words that name the shape of the detail rather than a thing of their own: "which area",
# "what was it called", "what was it about" are still about their news, so they are allowed
# beside the function words below.




# "which one?" after the bot has just named things is a choice between what it said, and not a
# detail the person left out: asking it back ("You haven't said - which one?") tells them nothing
# about the thing they are trying to choose, and the answer is the pick out of the last turn
# (the answers module keeps it, in `_the_one_to_pick`).




# A question about a part of a thing the chat has been told about, which they never described:
# "i work at a cafe" / "what do i do there", "my son is 7" / "what school does he go to", "i
# drive a ford" / "what model is it". The store holds the job, the son and the car, so these are
# not questions about the world, and the search hedge is the wrong answer to a question about
# their own life ("That's beyond what I know well, sorry. Searching for it will turn up better
# sources" to someone asking what their own job is). The part they ask about was never said, so
# the honest answer is to ask it back - the reading `_detail_they_left_out` gives a detail of
# their news, one step further out: there the news is the last line, here it is a fact the chat
# has kept for several turns.
# The thing is named with a possessive ("my job", "my son", "my car") or pointed at with the word
# that says the question is about the last thing said ("there", "he", "it").
# The parts a record actually has: a job's pay, hours and the people they work with, a child's
# school, a car's model and year, a pet's name and age. A question about one of these is a
# question about the person's own record, and the store is the only place it could come from.
# Anything else is asked about the kind of thing and not about their record - "i have a dog" then
# "how much do i feed it" is a question about dogs, which the knowledge base answers ("an adult
# dog eats about 2% of his body weight a day"), and the store keeps the dog, not its feeding.
# Advice, not a fact about them: "what school should i choose" wants an answer, and asking it back
# would throw the question away. A figure makes it a different ask too ("what should i do with
# 500 pounds").
# "what do i do about it" is a request for help with the thing they just described, not a part of
# a fact: the words after the ask say so, and the advice for it is a real answer.
# A first-person ask about a part of a fact the store keeps: "how much do i earn" is the job,
# "where do i live" the city, "what are their names" the children. The verb says which fact the
# part belongs to, so a question about the world ("how much should i save") is not read this way.
# A part of the job they never described: "where do i work" / "and what do i do there", "i work
# at a cafe" / "who do i work with". The store has the place and nothing else about it, so the
# job said back is the sentence it said in the turn before.














# A diet is a thing the person does not take, and the drinking half of it comes back with its own
# verb. The store kept what people do not eat and not what they do not drink, so "i dont drink"
# stored nothing; with it stored, the phrase said back has to read "you don't drink alcohol" and
# never "you don't eat alcohol", which is the bot not knowing what it just filed.




# "do you remember it?", "and you remember that?", "do you still remember this?": after the
# store has answered a recall, the line points back at the fact it just said, and nothing else
# in it names a subject of its own - a line with anything more ("do you remember what i said
# about the cat") belongs to whoever reads that.






# "am i vegetarian?", "is my name sam?": a yes/no question about the person is the same fact
# they told you, put the other way round. Only the frame is read here; the fact comes from the
# same extractor that stored it, so nothing is answered that they never said.


# A yes/no question about someone else asks whether a fact is already on record, so it states
# nothing: "my son is allergic to nuts" then "is he allergic to peanuts?" is the question of
# whether peanuts are on that list, and it used to end with peanuts in the list and the answer
# *your son is allergic to nuts, peanuts*.


# The frame of a yes/no ask about someone else, up to the end of that clause: "does my mum eat
# meat?" in "does my mum eat meat? she is vegetarian". What follows is a line of its own.


# The telling that follows an ask with no mark between them ("does my mum eat meat she is
# vegetarian"): a second clause opens with a person and a verb of its own. A person and a verb
# is what a clause needs, so a bare food word after the ask ("does my mum eat meat and fish") is
# still the ask's object, while "she is vegetarian" is the line they added to it.




def _asks_about_someone_else(text):
    """True for a yes/no question about a person ("is he allergic to peanuts").

    The question mark is not asked for. Most people type an ask about their son on a phone
    without one, and "is he allergic to peanuts" filed peanuts on the son while the same line
    with a "?" did not - the fault this guard exists for, in the one shape where a wrong stored
    fact matters most. What makes the line an ask is the auxiliary at the front and a person
    after it: "is my son", "does he", "can they" never open a statement. A word that is not a
    person ("is it expensive", "is the boiler new") keeps the question mark it needs, because
    those openings are also how a statement about the weather goes.
    """
    line = " ".join(str(text or "").split())
    return bool(YES_NO_ASK.match(line))










# "am i on a diet" names no diet of its own: any diet in the store is a yes to it, and a
# stored one is not a "no" about the word "diet". The fact reader answers it instead.






# "do i need to walk my dog every day", "have i got time to get to the vet": a duty or a
# question of time is a question about the animal's care, and the fact that they have a dog
# is not an answer to it. "am i", "is my", "do i have" still ask about the fact itself.


# "do you remember that i live in leeds", "remember that im veggie?", "you know im allergic to
# nuts": the person asks whether the store kept something, and says the thing itself. Read as a
# question about the bot it got "I remember what we've said in this chat, but nothing from before
# it", which is false: they are this chat, and the fact is in it. Only the frame is new - what
# follows it is a statement the store already knows how to read, so the same extractor that
# stored the fact says it back.

# A statement in the person's own voice is what a remembering frame holds: "i live in leeds", "i
# am vegetarian", "my budget is 500". "do you remember my budget" is the ask the store already
# answers, and "do you remember what i said about the cat" is about the conversation.

# A tag on the end of a confirmation ("you know im veggie right", "remember that im 34 yeah")
# asks for the yes: it is not part of the fact.






# The words that make the line behind a frame say something rather than name it: a copula, or a
# verb the store reads a fact from ("i live in leeds", "the dentist starts at four").




# "my sisters name is amy" -> the fact about the sister, said back. Only a fact the store holds
# is said back, so a frame around something it has never kept is left to the other readers.






# The words that make a rate of money the money a person puts by towards something. A budget is a
# rate too ("my budget is 300 a month"), and a corrected budget is a note about the budget, not a
# sum with an answer of its own, which is why the words are asked for here.














# The words a corrected figure goes back in, so a value put right in digits comes back as a
# person would say it: "Eight, not seven - got it."




# The words that say a statement is the first one put right, rather than news said once: "sorry, i
# meant my son is 8", "i meant 8". Only these lines are answered here - a correction said the
# other way ("no he is 9", "actually hes 8") is already said back by the same receipt that
# answers a plain statement about someone, and it needs nothing from this reader.
SAID_AGAIN = re.compile(r"\bi\s+(?:mean|meant)(?:\s+to\s+say)?\b", re.I)
# "sorry" opens two readings at once: the correction, "my son is 7" then "sorry he is 9", and the
# message that apologises to somebody. The apology card took the turn and the person who had just
# put their son's age right was told how to word an apology to him. A line that says sorry and
# puts a fact right is a correction, so it is answered with the fact, like "i meant" below.
SORRY_OPENS_A_CORRECTION = re.compile(r"\b(?:sorry|soz)\b", re.I)


def _note_a_corrected_fact(memory, text, entry, was):
    """Remember that this turn put a fact about someone right, so the reply can say which one.

    "my son is 7" then "sorry, i meant my son is 8" is a correction, and the store took it - it
    had 7 and now has 8 - but nobody said so: the line was answered with "Thanks for telling me -
    I'm here if you want to dig into any of that", which is the reply for news and tells the
    person the correction did not land. Worse, "sorry, i meant my son is 8" carries the word
    "sorry" and a relation, so it reached the row on how to word an apology and got advice about
    apologising to him. A correction is answered with the fact, so this one is.
    """
    if not isinstance(was, dict) or not isinstance(entry, dict):
        return
    said = " ".join(str(text or "").lower().split())
    if not (SAID_AGAIN.search(said) or SORRY_OPENS_A_CORRECTION.search(said)):
        return
    for kind, value in entry.items():
        if kind in ("who", "pronoun", "turns") or value in ("", None):
            continue
        before = was.get(kind)
        if before in ("", None) or before == value:
            continue
        memory["fact_fixed"] = {"who": str(entry.get("who") or ""), "kind": kind,
                                "value": value, "was": before,
                                "said": " ".join(str(text or "").lower().split())}
        return


def _note_a_fact_moved(memory, text, entry, was):
    """Remember a correction that moves a fact from one person to another.

    "my son is 9", then "sorry i meant my daughter is 9": the store filed the age on the
    daughter, but the son kept his, so the chat ended up with two nine year olds and no word
    said about it. The line also carries the word "sorry" and a relation, so it reached the row
    on how to word an apology and the person who had just put a fact right was told to name what
    they had done wrong. A correction that names another person takes the fact off the first one,
    and the reply says which person it now belongs to.

    Only the shape a correction is said in ("i meant", "sorry") counts, and only when a
    different person already holds the same value: "my daughter is 9 too" is news about a second
    child, not a correction, and it files both.
    """
    if not isinstance(entry, dict):
        return
    said = " ".join(str(text or "").lower().split())
    if not (SAID_AGAIN.search(said) or SORRY_OPENS_A_CORRECTION.search(said)):
        return
    who = str(entry.get("who") or "").strip()
    if not who:
        return
    # The person has to be named by this line: "sorry i meant my daughter is a nurse" is read for
    # the daughter, and the store also holds the nurse the son had, which is the fact being moved
    # away from and not the one moving - taken as the mover it sent the job the wrong way.
    if not re.search(r"\b" + re.escape(who) + r"\b", said):
        return
    for kind, value in entry.items():
        if kind in ("who", "pronoun", "turns") or value in ("", None):
            continue
        if isinstance(value, (list, dict)):
            continue
        if isinstance(was, dict) and was.get(kind) not in ("", None) and was.get(kind) != value:
            continue  # the same person's own fact being put right: `fact_fixed` has that one
        hold = [one for one in others(memory)
                if isinstance(one, dict) and one.get("who") and one.get("who") != who
                and one.get(kind) == value]
        if not hold:
            continue
        other = hold[0]
        memory["fact_moved"] = {"who": who, "was_who": str(other.get("who")), "kind": kind,
                                "value": value, "said": said}
        # The claim the arbiter asks for (`TAKES_AS_IT_COMES`) is put on the chat's own memory,
        # because each module is handed a copy of it: a mark made in the store's copy would be
        # thrown away. This turn is the store's answer even when an entry reads the word "sorry"
        # in the line, and the apology card took the turn off "sorry i meant my daughter is a
        # nurse" while the store's line said which child the nurse was.
        memory["moved_to_who"] = said
        # The first line said the fact about the wrong person, so it comes off that one: leaving
        # it made "how old is my son" answer nine when the person had already said the nine was
        # their daughter's.
        other.pop(kind, None)
        return






# A recall ask about a slot of a person or a thing is the direct ask with a wrapper around it:
# "what did i say her birthday was" is "when is her birthday", "how old did i say she was" is
# "how old is she", "what did i say his name was" is "what is his name". The reader that owns the
# slot answers the direct ask, so the wrapper needs no reader of its own - and read as a topic
# instead, the last line they said about anything came back as if it were the answer ("what did
# i say his name was" was answered with the line about their knee).
RECALL_WRAPPER = re.compile(
    r"^\s*(?:and\s+|so\s+|but\s+|also\s+|again\s+)?"
    r"(?P<word>what|when|how\s+old)\s+(?:did|do)\s+(?:i|we)\s+"
    r"(?:say|call|tell\s+(?:you|u)|told\s+(?:you|u)|mention)\s+(?P<rest>.+?)\s*\??\s*$", re.I)
# The slot the ask is about, and the question word that asks it directly. A word not in this
# table is not a slot the store keeps against a person, and the line is left to the recall paths.
RECALL_SLOTS = (
    (re.compile(r"\b(?:names?|called)\b", re.I), "what", "name"),
    (re.compile(r"\b(?:birthday|bday|dob|date\s+of\s+birth)\b", re.I), "when", "birthday"),
    (re.compile(r"\b(?:ages?)\b", re.I), "how old", "age"),
    (re.compile(r"\b(?:budget|salary|wage|rent|target|savings?)\b", re.I), "what", None),
    (re.compile(r"\b(?:address|postcode|number|time|date)\b", re.I), "what", None),
)
RECALL_POSSESSIVE = re.compile(r"^\s*(?P<poss>my|our|his|her|their)\b", re.I)
# A slot said on its own, straight after the possessive: "his name", "her birthday", "my budget".
# Anything else ("my dog called") is a thing whose slot the store reads with its own readers.
RECALL_SLOTS_BY_POSSESSIVE = re.compile(
    r"^\s*(?:my|our|his|her|their)\s+(?P<attribute>names?|birthday|bday|dob|ages?|"
    r"budget|salary|wage|societys?|address|postcode)\??\s*$", re.I)
# The pronoun a slot is asked about, as the person the direct ask names: "her age" is "how old is
# she" and "their age" is "how old are they".
SHE_OR_HE = {"his": ("he", "is"), "her": ("she", "is"), "their": ("they", "are"),
             "my": ("i", "am"), "our": ("we", "are")}


# A slot said in the chat in words of its own: an age is a figure, a name is "called", a
# birthday is a month or the word itself. It only matters when the slot's reader found nothing:
# then the fact may still have been said in a shape the reader does not read, and the store must
# not answer that they never told it.
SLOT_WORDS = {
    "age": re.compile(r"\b\d|\b(?:age|aged|old)\b", re.I),
    "name": re.compile(r"\b(?:name|called|named|calls)\b", re.I),
    "birthday": re.compile(r"\b(?:birthday|bday|dob|january|february|march|april|may|june|july|"
                           r"august|september|october|november|december)\b", re.I),
}


def _a_word_for_the_slot(memory, attribute):
    """Whether a line of theirs in this chat holds a word for this slot."""
    pattern = SLOT_WORDS.get(str(attribute or "").lower())
    if not pattern:
        return False
    return any(pattern.search(str(turn.get("user") or "")) for turn in recent(memory, 8))


def _the_ask_behind_the_recall(low):
    """The direct ask and the slot a recall ask is about, or None.

    Only a slot the person could have given in words is read this way, and only with a possessive
    in front of it ("his name", "my budget"): "what did i say about the cake" and "what did i say
    was wrong with it" are not asks about a slot, and they keep their own readers.
    """
    if not isinstance(low, str):
        return None
    wrapped = RECALL_WRAPPER.match(low)
    if not wrapped:
        return None
    rest = re.sub(r"\s+(?:was|is|were|are)\s*$", "", wrapped.group("rest").strip())
    said = wrapped.group("word").lower().replace("  ", " ")
    slot = next(((word, name) for pattern, word, name in RECALL_SLOTS
                 if pattern.search(rest)), None)
    if not slot:
        return None
    word, attribute = slot
    possessive = RECALL_POSSESSIVE.match(rest)
    if said.startswith("how old"):
        # "how old did i say she was": the frame asks the age itself, so the person is the whole
        # of what is left, and it has to be a pronoun the store can point at.
        person = rest.strip().lower()
        if person not in SHE_OR_HE:
            return None
        who, verb = SHE_OR_HE[person]
        return "how old " + verb + (" i" if who == "i" else " " + who), "age", person
    if not possessive:
        return None
    person = possessive.group("poss").lower()
    # The ask is rebuilt from the words the person used, with the verb taken out and the question
    # word that slot is asked with: "what did i say my dog was called" is "what is my dog called"
    # (not "what is my name"), and "what did i say her birthday was" is "when is her birthday".
    plain = " ".join(re.sub(r"\b(?:was|is|were|are)\b", " ", rest).split())
    if not plain:
        return None
    word = "when is " if attribute == "birthday" else "what is "
    slot_word = RECALL_SLOTS_BY_POSSESSIVE.match(plain)
    # The miss line names the slot only when the ask was the slot on its own ("his name", "her
    # birthday"): with a noun in between ("my dog called") the thing is the dog, and what it is
    # called is a read the store's own readers answer.
    only_slot = slot_word.group("attribute") if slot_word else None
    return word + plain, only_slot or (attribute or "answer"), person






# A question about the person pointed at something the store has no key for: "do i drive",
# "can i swim", "do i work from home". The thing named is in a line they said a moment ago, and
# the store holds it nowhere else, so the answer is that line, said back.

# The frame and the asking, which are not what the question is about.
# Short words that carry no thing either: "do i have a job" and "do i have a car" are asks about
# a thing three letters long, and the length test below threw the thing away with them, so the
# store said "I'd rather not guess" about a car it had just been told about. Only the words that
# would match anything are listed; "car", "job" and "dog" are what the ask is for.




# "what should i avoid", "what do i watch out for": the same ask as "what am i allergic to" in
# the words people use when a meal or a trip is coming up.
# "what do i do", "what do i actually do": the words name nothing, so they sound like a request
# for advice and are read as one. Said straight after the person has told you their job, they are
# asking for the job back - the knowledge base has an entry for the entryways into nursing, and
# answered a nurse with it. "now" and "then" are left out on purpose: those lean forward, and
# "what do i do now" after a job is a question about the job, not for its name.


def TAKES_AS_IT_COMES(text, memory=None):
    """Claim every line the store can answer - the bare "what do i do" included.

    The arbiter reads one `TAKES_AS_IT_COMES` per module and the last `def` in the file is the one
    it reads, so a hook written above this one is not read at all: its line goes unclaimed, and the
    specialist rule hands it to whatever entry the topic fits. That is what happened to the store's
    own readings for a while ("my son is 5" then "is my son 5", "he isnt allergic to nuts", a plan
    asked about by "when"), which is why every reading now has a private name and is asked from
    here, at the end of the file, rather than from a hook of its own.

    The job ask is the last reading: the bare "what do i do" said right after the person gave their
    job is the fact, whatever else read. The line names nothing, so the understanding engine hands
    it the topic of the turn before, and a knowledge entry for that trade answers it: an answer
    about the entryways into nursing, given to someone who already is one and only asked what they
    do. The store's reading is the one that answers what they asked, and it wins the turn on this
    line alone. False everywhere else - a turn later the same words ask about whatever the chat has
    moved on to.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return False
    if memory.get("moved_to_who") == " ".join(text.lower().split()):
        # "sorry i meant my daughter is a nurse": the fact moved from one person to another, and
        # the store said which. An entry that reads the word "sorry" answers it as a request for
        # the apology script, so the store's line takes the turn on this line alone.
        return True
    if _the_store_readings(text, memory):
        # Every reading the store had before this one lives in `_the_store_readings`, and it is
        # asked from here because this is the only `def` of the exported name: a second one above
        # would replace this hook at import and every reading under it would stop answering.
        return True
    if told_about.A_CALLBACK(text, memory):
        # "remember when i said my knee hurt": the store is the part that can say what was
        # actually said, and an entry that reads the word in it ("knee") would serve the advice
        # again. This hook is the one the arbiter reads - the store has an older definition
        # above, which no longer runs - so the claim is made here.
        return True
    if _the_ask_about_how_it_went(text, memory):
        # The thing they did today and the ask about how it went: only they can say how it went,
        # so the store answers by asking them. An entry about the thing would answer the question
        # nobody asked - "interview" is a word in the line, not what the line is about.
        return True
    if _a_callback_that_names_its_thing(text, memory):
        # "my boiler keeps losing pressure", then "what have i been saying about the boiler": the
        # line is about the conversation and the store's line answers it. The reading still gives
        # it a topic - a boiler is home-and-diy - so the specialist rule lifted the boiler entry
        # over the recall band, and the person who asked what they had said was told how to set
        # the flow temperature on the dial. "my kitchen tap drips" then "what have i been saying
        # about the kitchen" got a traybake the same way.
        #
        # Only the store's own gate for "this line is about the conversation", and only with the
        # thing named after "about": "what were we on about" and "what was i saying" name nothing,
        # and "when should i get the boiler serviced" names a boiler without being about the chat.
        return True
    if reminded.about_a_thing_they_said(text, memory):
        # "my boiler keeps losing pressure", then "what was wrong with my boiler again": the
        # past tense and the "again" make it a reminder about the line they said, and read as a
        # question about the world it was a fault to diagnose - the boiler entry answered it
        # with the flow temperature, a turn after the person had told us what was wrong.
        # The reading is `bot/memory/reminded.py`, and it is the same one the store's gate for
        # "this line is about the chat" uses, so the two cannot disagree.
        return True
    if not BARE_WHAT_I_DO.match(_bare(_folded(text, memory) or text)):
        return False
    return bool(user(memory).get("job")) and _the_job_was_just_said(memory)




# The scaffolding a person frames a job with: "im a nurse", "i work as a chef", "my job is a chef",
# "i work in a care home". Only this is set aside - everything else, of three letters or more, is
# the line saying something of its own, and then the ask is about that and not about the job. The
# shift words are on the other side of the line on purpose: "im a nurse and i work nights" is a
# line about the nights (orange-toad), and so is "i work in a care home at night".




# What is still to be avoided, after the verb: "what should i avoid in the sun", "on the roads".
# Eating is what an allergy is about, so the thing to avoid is the allergy only when the ask names
# nothing to avoid of its own or names something eaten: "what should i avoid in a stir fry" is
# food, and "what should i avoid in the sun" is a question about sunburn.
# An allergy being said, in any words: the fact is on the table when they say it now, or said it
# on the turn before.






# A person who has just said they are getting a pet often asks what to call it. The animal decides
# which names are offered, and the practical line comes with them, because the question behind the
# question is "what will I still like in five years".




# A word after "this", "that", "the" or a possessive is the thing the line points at. A naming
# ask that points at a song or a python function is not about the pet mentioned two turns ago,
# so the memory fallback stands down instead of offering dog names for it. The adjectives in
# between are skipped because "the new puppy" and "my little one" point at the pet itself, and a
# word that names an animal or nothing in particular ("it", "this one", "a name") is the pet too.






















# The tail of an ask that points back at the line before it instead of naming a thing of its own:
# "when is the best time to prep for it", "when is the best time for it". A verb on its own
# ("to book", "to renew", "to get there") names the thing to be done, and the knowledge base
# often has a real answer about that, so those asks are not claimed.

# Setting out is not prep, and nobody asking when to leave wants the day to do the work on:
# "i have an interview on thursday" then "when is the best time to leave for it" was answered
# with "Wednesday is the day for the prep". The verb sits in the tail the ask points back from,
# just before the "for it", so it is read there rather than anywhere in the line.
# A verb put on the thing they just said: "to book it", "to renew it", "to prep for it". The
# knowledge base often has a real answer for those, so the store only claims one when it can add
# the day the work goes on. A pointing word that follows no verb ("when is that again") is the
# whole ask, and the date they gave is exactly what it wants back.
WORK_ON_IT = re.compile(r"\b[a-z]{3,}\s+it\b", re.I)


# An exam is the one plan where the day before is the wrong advice. "i have an exam on monday"
# then "when is the best time to prep for it" was answered "Sunday is the day for the prep", and
# the knowledge base has a real revising answer for exactly that line ("open the past paper and
# write down what you already know"), so the plan does not claim it.










# A month, a day or a date: what a plan's own words put at the end of it.












# The places that hold their own food. Closed on purpose: a line that says "in the diary" or "on
# the list" is an ask about what is coming up, and only these places make it an ask about food.
# "What have I got for dinner?" is the same ask about their own food without naming a place, so
# it gets the same answer - the one thing the store can say is that it cannot see inside.












# A when ask made of a quality is about the best time for a job: "when is the best time to do
# it", "when is the best time to plant tomatoes". Nothing in the store is the answer to that
# unless they have a plan, so the empty-store line must not stand in for it.


















def _about_the_verb(plans, low, found):
    """The plan a when or what-time ask is about: the one that says its verb, and its name too.

    Two plans can say the same verb - "meeting sam at 6 tomorrow" and "meeting jo at 8 on friday"
    both say "meeting" - and the verb on its own answers "what time am I meeting sam" with jo's
    hour, which is an answer about somebody the person did not ask about. The words the ask puts
    after the verb are what tell the two plans apart, so a plan that names one of them wins.
    When no plan names them the verb-only reading still stands: "when do I start" names nobody,
    and "what time do I start work" keeps its answer even though the plan says "job".
    """
    named = content(low[found.end():])
    if named:
        for plan in reversed(plans):
            if _says_the_verb(plan, found.group(1)) and any(
                    _names_the_thing(plan, word) for word in named):
                return plan
    for plan in reversed(plans):
        if _says_the_verb(plan, found.group(1)):
            return plan
    return None








# The same doing said with another word. A plan keeps the verb the person used ("i begin my new
# job on monday"), so a question that names the other word for it ("when do i start", "when does
# my course finish") named no plan at all and the store stood aside: the ask then fell through to
# the newest dated line in the chat, which was the day before the correction ("when do i start"
# answered "On Monday." two turns after "sorry i meant tuesday"). Only the everyday pairs, and
# each listed both ways so a plan and an ask can be in either word.


# "where do i work", "do you remember where i work": the ask is for the place, and the place is
# kept beside the role (`workplace`). The question names `work`, so it lands in the job branch,
# and answering the role there said "You told me you're a teacher." to a question about the
# school.















































# "and she hates mushrooms" after the bot has just suggested a mushroom lasagne: the food is
# one option in the answer, so a friend drops it and keeps the others. Only a short statement
# counts, and only when the previous answer actually lists the food; a request ("what can I give
# them instead?") stays with the cooking answer.










def _remember_dislikes(text, memory, named_here=()):
    """Keep a food someone else will not eat against that person: "she hates mushrooms"."""
    if not isinstance(text, str):
        return
    for food, at in guest.found(text):
        kind, who = extract.subject(text, at)
        if kind == "user":
            food = guest.plain(food)
            if food:
                remember(memory, "dislikes", [food], text)
            continue
        if kind != "other":
            continue
        who = who or _person_from_pronoun(text, memory, named_here)
        remember_other(memory, {"who": who, "dislikes": [food]}, text)


# The verb a take-back line opens with, so the take-back can be said back in their own words:
# "You told me you gave up being vegetarian."
# A negation is not a take-back. "im not vegetarian" was never vegetarians until they said it, so
# "you stopped being vegetarian" invents a past they do not have; the negative is said as it is.






# "any more" is part of what they said: "i'm not doing weight watchers any more" is a diet
# left behind, and dropping it turns the line into one they never said.






# The shapes of a line that asks about a fact of their own rather than saying one.
# The line about the telling rather than about the thing: "i told you about the damp", "i
# mentioned the trip before". What it names is the chat, not the world.
# A plan or a wish is not a fact either: "we need to save for a deposit" says nothing about the
# budget they have now, and neither does "im thinking about a budget".










# The diets that are a plan someone follows rather than a way of eating they are: said back
# with "doing", the way people say it.
# A diet that names a way of being rather than a plan they do: "you stopped being vegan" is how
# that take-back is said, and "you stopped vegan" is not.




# A diet kept as a negation. The take-back of one is said positively, because "no more not eating
# meat" says the opposite of what happened in words nobody reads twice.



# A diet that is not the one they are on: somebody else's ("my wife is on a diet"), one behind
# them ("i was on a diet last year") or one not started yet ("im thinking about going on a
# diet"). Quoting one of those back as their own is the store putting words in their mouth.


# Someone asking for a dinner rather than for the fact: "so what do i eat", "what should i
# cook", "what can i have for tea". The store holds the diet and the allergies either way, and a
# receipt for them is not a meal - "im vegetarian though" then "so what do i eat" was answered
# "You told me you're vegetarian.", which is the line they had just said said back to them.


def _diet_reply(memory, low=""):
    """How they eat, said back when they ask: "You told me you're vegetarian."

    The diet is kept on every line they say it in, so the answer is the fact and nothing else.
    A diet stored as a negation comes back with its verb ("you don't eat meat"), because "you're
    no meat" says nothing. What they cannot eat is not one key, though: "im coeliac" is a
    condition and "im allergic to nuts" is an allergy, and a question about the fact is about
    all of it - so the read says back whichever the store holds, and only when the line asks
    about the fact (a line asking for a meal keeps its meal).
    """
    # A line that reports a change to the diet, or asks for one, is not a request for the fact
    # and not a gap in it: "i want to lose a bit of weight" then "ive changed my diet" was
    # answered "You haven't told me about your diet", a denial of what they had just said.
    said = a_change.reported(low, "diet")
    if said:
        was = user(memory).get("diet")
        if said == "changed" and was:
            # The reply says what it is doing with the old value ("You were vegetarian, so I'll
            # drop that"), so the store has to do it: "im vegetarian" / "i changed my diet" /
            # "am i vegetarian" said "Yes - you're vegetarian" and "what can i cook" still picked
            # the vegetarian dish, so the bot promised a drop and went on quoting the value.
            forget(memory, "diet", [was])
            user(memory)["diet_changed"] = was
        return a_change.reply(said, "diet", was=was)
    diet = user(memory).get("diet")
    if not diet:
        if str(low or "") and not DIET_FACT_ASK.search(str(low or "")) \
                and _food_facts(memory):
            # A meal ask ("what do i eat") after they have told the store what they cannot eat is
            # a question about the food, and "You haven't told me about your diet" is a claim
            # about the person that is false when the store is holding it. What the store can say
            # about the dinner is what each meal has to leave out, so that is what it says, and
            # the kitchen picks the dish ("im allergic to nuts" then "what do i eat" was the
            # denial, and "im coeliac" then "what do i eat" was the same one a key over).
            #
            # This is asked before the fact said back, because the fact said back is a fallback
            # for lines with no meal ask and it was written when the meal rows answered this one;
            # saying "You told me you're allergic to nuts" to "what do i eat" answers nothing.
            left_out, said_so = _what_a_dinner_has_to_leave_out(memory)
            if left_out:
                return ("Nothing with " + _say_a_list(left_out) + " in it — " +
                        " and ".join(said_so) + ". Tell me what is in the fridge and I'll pick "
                        "a dinner around it.")
        kept = _food_facts(memory)
        if kept:
            # The store holds what they cannot eat, so a denial would be false whatever the
            # line's shape: "im allergic to nuts / im coeliac / what do i eat" was answered
            # "You haven't told me about your diet." Saying the fact back is the honest reply.
            return "You told me you're " + _say_a_list(kept) + "."
        if DIET_FACT_ASK.search(str(low or "")):
            kept = _food_facts(memory)
            if kept:
                return "You told me you're " + _say_a_list(kept) + "."
        who, theirs = _other_fact(memory, "diet")
        if theirs and who:
            return ("You haven't told me about yours \u2014 the diet you mentioned is your "
                    + who + "'s.")
        changed_from = user(memory).get("diet_changed")
        if changed_from and DIET_FACT_ASK.search(str(low or "")):
            # The change was said and the value it named was dropped, so the store holds nothing
            # and "You haven't told me about your diet" would deny the change they just reported.
            was = str(changed_from).strip()
            was = ("not eating " + was[3:] if was.lower().startswith("no ")
                   else "being " + _diet_words(was))
            return "You told me your diet had changed from " + was + ". What is it now?"
        take_back, gone = _the_take_back(memory, "diet")
        if gone:
            # They took a diet back, so they have said how they eat: nothing is in the store
            # because the take-back emptied it, and the honest answer is their own take-back
            # said back rather than denying the whole thing.
            return _a_take_back_said_back(take_back, gone)
        # A denial is a reply about the chat, so it needs a line that asks about the chat: "what do
        # i eat" is somebody asking for a dinner who never mentioned a diet, and the kitchen has a
        # meal to suggest. The stand-down below reads the same ask where a diet is held; this is
        # the path with nothing held, and the phone answered it with a claim about the person.
        if MEAL_WANTED.search(str(low or "")) and not DIET_FACT_ASK.search(str(low or "")):
            return None
        return _deny(memory, "diet", "You haven't told me about your diet.",
                     own=_their_own_diet)
    diet = str(diet)
    if MEAL_WANTED.search(str(low or "")) and not DIET_FACT_ASK.search(str(low or "")):
        # A dinner is the kitchen's to answer, and it is told about the diet on the way past. The
        # store's job on this line is only to keep what they said; saying it back answers a
        # question nobody asked, in the words they used to ask it.
        left_out, said_so = _what_a_dinner_has_to_leave_out(memory)
        if left_out:
            return ("Nothing with " + _say_a_list(left_out) + " in it \u2014 " +
                    " and ".join(said_so) + ". Tell me what is in the fridge and I'll pick a "
                    "dinner around it.")
        return None
    if diet.startswith("no "):
        return "You told me you don't " + _diet_how(diet) + " " + diet[3:] + "."
    if diet in WAY_OF_EATING:
        return "You told me you're " + _diet_words(diet) + "."
    if diet in PLAN_DIETS:
        # A plan is something they are doing, not something they are: "you're keto" is not it.
        return "You told me you're doing " + _diet_words(diet) + "."
    return "You told me you're " + diet + "."


# "what's my mum's name", "what is my sister called", "how old is my son": an ask about one
# thing the store knows about a person they mentioned. The name is asked for in as many words as
# people use, so the ask is read by the property it asks for, not by one phrasing.


# What they like and do not like is a fact about a person like an age is, and it was the one
# the store never read or answered: "my sister loves cooking" then "what does my sister like"
# was a search hedge about somebody the chat had told the bot about a turn before.


# The relation words that are more than one person, so the sentence agrees with them: "your kids
# love pasta" is not "your kids loves pasta". A relation the store does not know is read from its
# ending, which is what "your sons" and "your children" need.


# "what does my sister do", "what's my mum's job": the same ask about a fixed role the store
# keeps about a person, shaped like the taste and the age asks above. The "for a living" and "for
# work" tails are how people say it, so the ask is read with them and without them.


# Two ages compared: "who is older", "am i older than my wife", "how much older is she",
# "which of us is younger". Read by the comparison in the line, not by one phrasing of it.
# With nobody named, the comparison is the speaker against the last person only when the line is
# about people: a bare "who is older", or a pronoun that points at a person. "is my laptop older
# than my phone" compares two things, and the wife's age is no answer to it.






# An ask that puts the plans in order: "which one is first", "which is sooner", "whose is
# sooner", "what comes first", "which one is next". The words between the ask and "first" are
# the ones the shapes above use and nothing else, so a line that names a thing of its own
# ("which bus goes first", "whose turn is it first") is no ask about the plans at all.
# The words a line may still hold beside the ask: nothing else does.










# "my kids are tom and sam": the names after a group word and no "called". The group word covers
# two people, so the name readers file nothing and the ask about the group used to come back as a
# denial or a search one line later.


# "they are called tom and ada" after "i have two kids": the names follow the group the line
# before named, and the pronoun is how people give a second name or a second list.


# Words that name something they cannot have without the store keeping it as a limit: a
# pregnancy, a diet said in passing, an allergy that was never filed because it was someone
# else's ("my son is allergic to nuts"). They are what turns "you haven't told me anything you
# can't have" from an honest answer into a denial of the turn before it.

# Foods the cooking families do not carry but people are allergic to all the same: a food the
# list does not know is not food, so it keeps the hedge instead of inventing a dinner rule.


























# A word that names one person while covering several: "what is my child called" after "my
# children are called jack and emma" is an ask about one of them, and the names on file cannot
# say which. The plural of the same word ("children", "kids", "parents") is the group ask.






















# The words that turn up after "his name is" without being a name.














# "what car do i drive", "what phone have i got": the thing they said with its make, asked for
# by the name of the thing. A statement of a fact is read here as well as a bare ask - "do you
# know what car i drive" - because all of them are the same question.

























# A state said in the past is not a state now. "my wife was pregnant" was congratulated ("That's
# great news - nice one. What's next?") and "my wife was pregnant last year" was answered with the
# trying-for-a-baby entry, because the only thing either reader saw was the word. Nothing is
# stored for it - said back, "your wife is pregnant" is a fact the store was never told - so the
# line is put in the past and left there. A loss is possible behind either line, so the reply
# assumes nothing about a baby.




# A breed is the animal it is, so an ask that names one is an ask about their animal: "how old is
# my greyhound" reached the world and got a search hedge about a dog whose age the chat had.
# "how old is my greyhound" names an animal the same way "my dog" does, and read as a question
# about the world it got a search hedge about a dog whose age the chat had been told.


# "what breed is he", "what did i say his breed was", "what sort of dog is it": a part of an
# animal the chat has already described, so the answer is the breed that was said, not a search.






# The family word is right for a plural ("your dogs are 4 and 12") and wrong for one animal that
# has its own word: a person who says "my puppy is 4 months" is asking about their puppy, and
# "your dog is 4 months old" is the store talking over them.






# "10 weeks old" and "18 months old": an age this path must not round to a year.






# "im allergic to nuts" then "and my wife is too": the line names a person and gives them the
# fact that is already standing about the person typing. Nothing in it is a fact of its own, so
# every reader below passes on it and the composer says "Got it - your wife is too", which drops
# the allergy the "too" points at. The reply has to be written where the note is made as well:
# each module works on its own copy of memory, so a fact kept by a module that did not answer is
# thrown away with its copy.
# The people a "too" can carry the fact to: the relations list, and the plural words a family is
# named with, which it does not carry ("and my kids are too" was left to the composer's echo).
# A denial is only read as one when it is said of the person and not of a verb: "my wife isnt"
# is the allergy said against, "my wife doesnt" could be the cooking or the driving, so it is left
# to the readers that can tell ("she doesnt eat meat" files a diet of its own).
# The words after the denial that are not a fact of their own: "my wife isnt either", "my wife
# isnt at all". Anything else after it is a line about the person, and those are kept by the
# readers that know them - "my wife is not responding" and "my son is not breathing" are the
# person's state, and a denial read on one of those is a memory note where help is wanted.
# The same denial with the person said as a pronoun: "she isnt" after the note was written on the
# wife. A fact the store worked out from a "too" has to be takeable back the same way, or the
# person who never had the allergy is on record with it for the rest of the chat.












# The person words the reply can call "her" or "him": a neighbour or a cousin can be either, so
# those get "them" rather than a guess about who they are.








# A food ask with the person left out: the chat is on a person and the line asks about one more
# thing they might have. "can he have cheese" then "what about milk" is the same ask again, and
# with nobody named it fell to the knowledge entry for milk.


















# The plan reader writes a plan down as the words after "my ... is", so "my birthday is tomorrow"
# is held as "birthday tomorrow": the copula is gone and only the words that name the day are left.
# The words a person the store knows is named by in a line, longest first so "grandmother" is
# read before "grand" and "mother in law" before "mother".
# A relation in front of the word is whose birthday it is, and it is not the person's own.

# What a single-word car can be without being a name: a fuel or a body, and neither takes a
# capital in the middle of a sentence ("you drive a diesel" is no Diesel).
# A word beside the model describes the car rather than naming it, and a describing word takes no
# capital: "i drive an old fiesta" is not "an Old Fiesta".








# Somebody else's birthday, asked back: "when is my mums birthday", "when is toms birthday",
# "when is his birthday". The date is kept on the person now (bot/memory/facts.py,
# OTHER_BIRTHDAY), so the answer is the store's, and without this the ask was answered "I don't
# have a date from you for that" a turn after the date had been given - the store denying what it
# had just been told. "when's my birthday" is not this reader: the word after "my" there is the
# birthday itself, so no person is named and the ask falls through to `_birthday_reply`.







# An allergy as a thing in the world, rather than the one this person has: "why do we get
# allergies", "what causes allergies", "how common are allergies", "why do people have allergies".
# The store has nothing to say to those - its only line in the allergy branch is a denial, and
# "You haven't mentioned an allergy to me" answers a question nobody asked - so the word "allerg"
# in the line is not on its own an ask about their own. The knowledge answer or the honest punt
# takes them.
















# "do i need to walk my dog every day", "how often should i feed the cat": a quantity, a
# frequency or a should/need is a question about the animal's care, not a recall of the fact
# the store holds. A recall asks what, who, which, how old or called.
















# A repeat ask can name the figure it wants out of the answer: "how long did you say", "what time
# did you say", "how much was it again". The whole paragraph back answers a question the person
# did not ask, so the figure is lifted out of the answer they are asking about, when it is there.




# Modules whose replies are the answer itself, however short they are: "Twenty minutes." is the
# answer to the question before it, and it is worth hearing again.






# A line that only says thank you or agrees: "thanks", "thank you", "got it", "ok, cheers".
# Built from politeness and assent words only. The acknowledgement list carries real answers
# ("no", "nothing", "same", "much"), and a line of those is a thing the person said, not a nod:
# "how much should i take" / "not much" is an answer, and a nod is not.






# The few words that ride along with a greeting without saying anything themselves: "hi there",
# "morning all". Any other word means the line said something, however short it is - the length
# of a word is no help at all ("hi we got a cat", "hi its a boy" are mostly one or two letters).
















# A question about the person who asked it: "where do i live", "whats my name". In a chat that
# has said nothing yet, the exchange is the honest thing to hand back.




# A question the user asked is a thing they wanted to know, not a thing they told us: quoting
# "should i get someone in?" as what they said about the boiler reads as if the question were
# the fact. Only a line that starts as a question counts, so "i'm allergic to shellfish - what
# can i eat?" still keeps the fact in it and can be quoted back.
# A lead-in before the ask word does not make it a statement: "anyway how do i roast a chicken"
# is still a question, and quoting it back as what they said about the boiler reads as if the
# question were the fact. Only those words, so "and the boiler is broken" and "sorry my mum is
# ill" keep their facts.


# A line that stops to ask inside it: "sorry, back to the roast, what time should i start it",
# "anyway back to the laptop, is it worth a new one". The ask starts a new clause rather than the
# line, which is why ASK_START alone does not see it - and read as the line that gave the thing,
# it is handed back as an answer and says nothing.


# A line that takes something back: "sorry, Naples not Rome", "i meant Florence", "or rather
# the Tuesday". It names the old thing only in order to replace it.








# "what was i saying about the boiler": the shape that asks for a line, with the thing it is
# about named after it. "what was i saying" alone is the topic ask, and the store already
# answers that with the last thing the chat was on.


# The shape of "you haven't said anything about that yet": a lookup that found no line. It is
# the right answer to a callback about a thing they never mentioned, and the wrong one when the
# store keeps that thing as a fact ("what was i saying about my job" beside "i'm a baker").






# The words people use for the facts the store keeps, so a callback that names one of them can
# tell "they never mentioned it" from "I could not find the line, but the fact is kept".
FACT_WORDS = frozenset((
    "name", "called", "age", "old", "job", "work", "works", "working", "city", "town", "live",
    "lives", "living", "moved", "moving", "from", "diet", "dieting", "eating", "food", "budget",
    "money", "afford", "allergy", "allergies", "allergic", "pet", "pets", "dog", "cat", "height",
    "tall"))


def _a_fact_word(low):
    """True when the thing a callback names is one of the facts the store keeps."""
    after = re.search(r"\babout\b\s+(.+)$", low or "")
    words = set(re.findall(r"[a-z]+", (after.group(1) if after else "").lower()))
    return bool(words & FACT_WORDS)


def _a_callback_that_names_its_thing(text, memory):
    """True when the line asks about the conversation and names the thing it asks about.

    "what have i been saying about the boiler" is a recap by name (`_about_this_chat`, the reading
    the store answers with) and the name is what makes it about that thing rather than the chat as
    a whole (`_names_its_thing`). Both, because either on its own is too wide for a claim: a line
    that names nothing is the chat's own topic, and a line that names a boiler is not a recap
    unless the store read it as one.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return False
    try:
        low = " ".join(text.lower().split())
        return bool(_names_its_thing(low) and _about_this_chat(text, memory))
    except Exception:  # noqa: BLE001 - a reading that fails claims nothing
        return False






# The person themselves, said with the reflexive: "what did i tell you about myself" is the
# whole picture, the same ask as "what do you know about me".




# Words for the same everyday thing, so a question in other words still finds the line: the
# same person ("mum" / "mother"), the same animal ("puppy" / "dog"), the same do ("party" /
# "birthday"). It is a table of concepts, not of phrasings: it works for every recall ask.
# The words a recall ask brings with it. "What did i say was wrong with my flat" asks about the
# flat; "wrong" is the ask's judgement, not something the person ever said, so it cannot be a word
# to find. These are dropped only on a second pass, after the full set of words has failed.

# The role the ask names them by is the same kind of word. "what did i say about the coeliac
# guest" was answered "You haven't mentioned the coeliac guest yet" about a chat that had just
# said "one of them is coeliac": the guest is who the fact is about, and the role word is not in
# the line that states it. Like the judgement, it is dropped only on the second pass.


# An ask that points at the subject instead of naming it: "what did i say was wrong with it".

for _concept, _words in (
        ("mother", "mum mom mummy ma mam mother mumma"),
        ("father", "dad daddy pa papa father"),
        ("parent", "parent parents folks"),
        ("child", "kid kids child children baby toddler"),
        ("dog", "dog puppy pup dogs"),
        ("cat", "cat kitten kitty cats"),
        ("pet", "pet pets"),
        ("car", "car vehicle motor"),
        ("home", "home house flat apartment place"),
        ("party", "party birthday bday celebration bash"),
        ("job", "job work career"),
        ("food", "food dinner tea meal supper"),
        ("money", "money budget cash savings"),
        ("diet", "diet vegetarian vegan pescatarian"),
        ("doctor", "doctor gp surgery hospital"),
        # The things people tell a friend about, said with a second set of words: a wedding is
        # "getting married", revision is "an exam in may", the gym is "getting fitter", cigarettes
        # are "stopping smoking". Without them the recall told a person who had just said they
        # were getting married "You haven't said anything to me about the wedding yet."
        ("wedding", "wedding weddings married marry marriage engaged engagement bride groom "
                    "fiance fiancee honeymoon"),
        ("holiday", "holiday holidays vacation trip trips break abroad travelling travel"),
        ("exam", "exam exams revision revise revising coursework dissertation thesis mock"),
        ("gym", "gym gyms fitter fitness exercise exercising workout workouts jogging running"),
        ("smoking", "smoking smoke smoker cigarettes cigarette fags vaping vape nicotine")):
    for _word in _words.split():
        CONCEPTS[_word] = _concept

# Going somewhere is a holiday, and the line says the country rather than the word: "im going to
# spain in june" is what "what did i say about my holiday" is asking about.
for _country in extract.COUNTRIES:
    CONCEPTS.setdefault(_country.lower(), "holiday")

# Some lines name the thing in a shape rather than a word: "im going to lisbon in may" is a trip,
# and the country table does not hold cities. What follows "to" has to be a place, not an article
# and a thing they do every week ("i go to the gym twice a week" is not a holiday).






# A thing that "is on tonight" or "was on tv" is a programme being watched, so the words in front
# of it name the programme and not a person of theirs: "my dads army is on tonight" says nothing
# about their dad, and filing it under him answered an ask about him with it.




# The words a person's name stands in front of when the line is about them rather than about
# something named after them: a verb, a state, a clause word, or the end of the line. "mum is
# ill", "dad needs a scan", "mum who rang", "i am worried about mum" all have the person
# standing there; "my mum loves dad jokes" has "dad" in front of "jokes", which is what the joke
# is called, not who the line is about.




# A thing asked about is not always a word in what they said. Nobody says "the trip" when they
# say "im going to lisbon in may", and the plan they gave is still the trip; "when is my holiday"
# is the same ask about the same week away, and both were answered as if the person had said
# nothing at all ("You haven't said anything to me about your trip yet." right after they had).
# So an ask that names one of these kinds is answered from the shape that carries the kind rather
# than from the word: a place they are going to for a trip, the work itself for a job. Kept as
# data, so one more kind is one more line.
# The kind said in its own words, for the lines that never use the word the ask does.
# A trip said as a length of time and a place, with no verb of going in it at all: "were thinking
# of a few days in edinburgh in august". The plan reader keeps it as a plan, so a later "what did
# i say about the trip" was told the store knew nothing about a trip.
# The word after "in" is only a place sometimes: "three days in bed is too long", "two weeks
# in hospital", "a few days in limbo" are a stretch of time somewhere they are not going.


# The food said in its own words: what they do or do not eat or drink, a diet by its name, a meal
# that is being cooked or eaten. A line that only asks what to cook names no fact of theirs and is
# quoted as the question it is.
# The kinds whose own words are a pattern. A kind that is not in here has no way of being said
# without naming itself, and is found by its word alone.
















# A line that puts a figure right and says nothing else: "sorry 1150, i got it wrong", "no, 1150
# a month", "actually make that 1150". The figure is all it says, so the thing it is about is the
# line before it. A line that names a subject of its own ("sorry, the gas is 1150") is about that
# subject and does not match: the lead is followed by nothing but the value.
























# The words that point at a thing instead of naming it, so a line made of them is not saying it.












def _points_back_at_nothing(text, memory):
    """The store's answer to a pointer with nothing behind it, or None when it is not that line.

    "same as before" as the first thing in a chat is not a request the store can answer from what
    it holds, and it is not small talk either: it is the person picking up a conversation that is
    not there. Saying that plainly is the answer, and it is the same answer NOTHING_STARTED gives
    to "what have we talked about" - so a chat that opens this way gets a line that names the
    missing thing and asks for it, not a welcome and not a receipt.
    """
    if not thread.points_back(text) or not thread.nothing_said(memory):
        return None
    return _vary(POINTS_BACK_NOTHING, memory)


def _a_recall_about_nothing(text, memory):
    """The store's answer to "what was it i was worried about" with nothing said, or None.

    The line names no slot and no fact: it asks the chat to give back something that was never
    put in it. The readers below all want a thing to look for, so none of them reads it, and it
    fell through to the chatter band as a line about a worry.
    """
    if not thread.asks_what_i_said(text) or not thread.nothing_said(memory):
        return None
    return _vary(WHAT_I_SAID_NOTHING, memory)


# The same ask for their own words in shapes the wrapper does not reach: an order ("tell me what
# i said"), a yes/no recall ("did i say anything about it"), a frame whose subject is named as a
# thing ("what was the thing i said"), and a reminder of something that is not there ("remind me
# what that was"). Each is the ask for their own words and each named no slot, so no reader below
# read it: the turn went to the search hedge or to the pool for an ask about a thing.
A_RECALL_IN_ANOTHER_SHAPE = re.compile(
    r"^(?:and|so|but|also|again|ok|okay|well)?\s*(?:"
    r"tell\s+me\s+what\s+(?:i|we)\s+(?:said|say|told\s+(?:you|u)|tell\s+(?:you|u)|mentioned?)\b"
    r"|(?:did|do)\s+(?:i|we)\s+(?:say|tell\s+(?:you|u)|told\s+(?:you|u)|mentioned?)\s+"
    r"(?:anything|something|much)\b"
    r"|what\s+(?:was|were)\s+(?:the\s+thing|that\s+thing|that)\s+(?:that\s+)?"
    r"(?:i|we)\s+(?:said|told\s+(?:you|u)|mentioned?)\b"
    r"|remind\s+me\s+what\s+(?:that|it|this|those|they)\s+(?:was|were|is|are)\b"
    r")", re.I)
# What may follow such an ask and still name nothing of its own: the pointer, the words that stand
# for a thing nobody has named ("anything", "something", "the thing"), the little words, and the
# auxiliaries. A word outside these is a thing ("about the boiler"), and that line has a reader of
# its own that names the thing back ("You haven't mentioned the boiler").
RECALL_NAMES_NOTHING = frozenset("""it that this them those these one ones there anything something
much thing things about of on in at to for from with the a an was were is are be been being
i we you u he she they me us my our his her their said say told tell mention mentioned mentioning
and or so but also again then just really actually exactly then""".split())


def _names_nothing_in_a_recall(rest):
    """True when what follows a recall ask names no thing of its own."""
    words = re.findall(r"[a-z]+", str(rest or "").lower().replace("'", ""))
    return not [word for word in words if word not in RECALL_NAMES_NOTHING]


def _a_recall_frame_about_nothing(text, memory):
    """The store's answer to "what did i say about it" with nothing said, or None.

    The recall frame - "what did i say", "what did i say about that", "what did i say i lost" -
    is the ask for their own words, and it is that whatever the frame is filled with. The "it"
    or the "that" inside it is not a thing the chat could name: the person is asking what they
    themselves said, so there is nothing to give them, and saying that is the answer.

    Read before the pointer asks, because the pointer reader looked at the same "it" and answered
    a request for the chat's own words as if the person had asked a question about a subject
    ("Nothing said yet for that to be: tell me the thing itself..."). A rule-out, not a new pool:
    it hands back the same WHAT_I_SAID_NOTHING line the feelings recall gets.
    """
    if not thread.nothing_said(memory):
        return None
    low = " ".join(str(text or "").lower().replace("'", "").split()).strip(" .!?,")
    wrapped_low = " ".join(str(text or "").lower().split()).strip(" .!?,")
    # The shapes of the ask that no slot reader reaches, kept to the ones that name no thing: a
    # line that does name one ("did i say anything about the boiler") has a reader below that says
    # the thing back, which is the better answer.
    another = A_RECALL_IN_ANOTHER_SHAPE.match(wrapped_low)
    if another and _names_nothing_in_a_recall(wrapped_low[another.end():]):
        return _vary(WHAT_I_SAID_NOTHING, memory)
    wrapped = RECALL_WRAPPER.match(wrapped_low)
    if not wrapped:
        return None
    # Only where what the frame is filled with is a pointer and nothing else: "about it", "about
    # that". A person or a thing named inside the frame ("what did i say her birthday was", "how
    # old did i say he was") is a slot one of the readers below keeps, and those answer with the
    # slot that is empty, which is a better line than this one.
    rest = wrapped.group("rest")
    if not thread.POINTING_WORD.search(rest) or len(re.findall(r"[a-z]+", rest)) > 2:
        return None
    return _vary(WHAT_I_SAID_NOTHING, memory)


def _an_ask_about_nothing(text, memory):
    """The store's answer to an ask about nothing at all, or None when it is not that line.

    "how do i do it" as the first line of a chat names one thing - the "it" - and the chat holds
    nothing it can be. Nothing below reads the line: no fact is asked for, no plan is stated, so
    the turn went to a search hedge over a question the person could be helped with in one line.
    The same goes for "do that again" and "is it worth it". The answer says the thing is missing
    and asks for it, which is what a friend does with a question whose subject they never heard.
    """
    if not thread.points_at_a_word_alone(text) or not thread.nothing_said(memory):
        return None
    # A line that is nothing but pointing words ("what does that mean", "how does that work") is
    # already read by the composer, which asks for the thing itself in its own words. Two pools
    # answering one shape is two voices for the same turn, so the composer keeps that one and
    # this reading is only for the pointer asks its word list does not reach.
    from ..compose import fallback
    if fallback._points_at_nothing(text, memory):
        return None
    return _vary(POINTING_WORD_NOTHING, memory)


def _the_last_ask_about_the_bot(memory):
    """The last thing they asked about the bot, as a sentence, when that is all they have said.

    A chat that opens "are you a real person" and then asks what we have talked about has nothing
    of theirs to go back over - but "nothing yet" is not true either, because they asked something.
    The question is said back in their own words ("whether I am a real person") as the one thing
    the chat has covered, which is what a friend would say.
    """
    for text, reading in reversed(list(thread.user_lines(memory))):
        if not (isinstance(reading, dict) and reading.get("about_bot")):
            return None
        asked = thread.restate(text)
        if asked:
            return asked
    return None




# What a line said when it said nothing to keep: a greeting, a thank-you, a shrug.
# The words a summary can say "you told me ..." about. A line with none of them left is small talk.




# How a line says a name: "my mum is called ann", "my brother's name is tom", "she goes by meg".




# A summary says the things they told you, so a line that only points at something ("i like it
# there") says nothing on its own. The tone words on the end of a line ("tbh", "though", "to be
# honest") come off through `facts.no_tone`, which knows when a phrase is the line itself: "im
# not going to be honest" is about being honest, and taking it off leaves "im not going".
# "sorry, i meant 500" is a correction, not a fact about them: the store already holds the
# corrected thing, so the summary would only say the number twice, once as a mistake.


# A line that takes something back: "no she isnt, shes called dana", "no wait, it was june". What
# was said before it is what the person is taking back, so the summary does not say it.
# The correction says the right name for somebody, not the first name of somebody new: "actually
# my friend is called dave" is a new person, and the line before it is still true.






# The keys the summary says in its own words, better than the line that gave them: "you're Sam"
# for "my name is sam". A line whose facts are all of these is already in the summary.






# A line that says the thing has changed: "im 35 now", "france instead", "a new job". What came
# before it about the same thing is out of date, and the store has the new value.
# A line in a negative frame says what they cannot do or do not have, and a later line where they
# do it or have it puts it out of date: "i dont drive" / "i passed my driving test last week". An
# attitude is not that - "i dont like fish" stays true after a fish supper - so a dislike or a
# want is left alone.










# A line where the person is hard on themselves is how they feel, not a fact about their world.
# The composer answers it with care, and the recap said it back in the bot's own voice: "im such
# an idiot" then "i locked myself out again" gave "So far I know you said you locked yourself out
# again; you are such an idiot", which is the store handing round the worst thing it heard. The
# same rule as a crisis line - the care lines are not inventory - and the same reading the
# composer uses (`bot/compose/fallback.py`, SELF_SUBJECT), so the two cannot disagree.
#
# A rating of a skill is not that. "im rubbish at maths" and "im a terrible cook" are things to
# get a hand with, and the recap says them as the view they are; only a name for themselves or a
# judgement of the whole person is left out.
# "im the worst" says nothing else, so the superlative is a judgement only on its own: "im the
# worst at chess" rates a skill and stays a fact.






# A clause beside a verdict that only points back at it - "im a failure and i know it", "im a bad
# mum, honestly" - says nothing of its own, so it is not the fact beside the judgement: said back
# it is the fragment "you know it", which is not something anybody told the chat.














# A figure written as a digit and the same figure written as a word are the same fact: "my son is
# 9" in the summary and "your son is nine" in the line underneath is the repeat this guards.




# The words a line can carry and still be the fact above: "i got the job at the co op" is the
# place the summary already has as "you work at the co-op". A line left with nothing but these is
# that fact again, said worse - "So far I know you work at the co-op; you said you got the job at
# the co op" says one thing twice, which is the log STYLE.md rules out.








# "do i like fish", "do i still like curry", "am i a fan of olives", "did i say i liked dogs".
# The ask itself lives in `bot/memory/taste.py`, next to the taste it is about, because the
# knowledge base has to keep out of the same lines: "do i like curry and rice" is a question about
# them, and a rice recipe is not an answer to it however well "rice" fits an entry.






# An age said in words rather than figures: "i am eight" stores 8, and the line said back at the
# end of the summary would then say it a second time in words. It has its own name: `AGE_SAID`
# above is the reader for "your daughter is 4" and `_just_gave_an_age` asks it, so a second
# binding of that name here quietly replaced it - "and my son?" after "Your daughter is 4." was
# no longer read as another age ask and got the search hedge instead.








# A line about a death, a crisis or someone being hurt is not a receipt to read back: "We've
# been on \"my husband died in march\"" hands a person their worst line in quotation marks.
# The recap says what it was about and leaves the words with them.








# ---- the call the advice already gave --------------------------------------------------------
# "my knee hurts when i run" is answered "cut the distance and the speed for a week or two", then
# the person narrows it ("only on the outside of the knee") and asks "should i keep running?".
# The chat has already settled it: the advice said how to keep going, and with what limit. Nothing
# read the last answer for the decision, so the line fell to "That's your call, not mine" - a wall
# in front of somebody who had just given the detail that mattered. The store answers from the
# answer already in the chat (`memory["last_answer"]`), so it says nothing the bot did not say.
# The thing the line is deciding whether to go on with. It has to name one: "should i bother" is
# a different question, and one the advice given above says nothing about.
# The condition the advice put on it: what would mean stop, or who to see. Quoted from the answer
# for the same reason.
# Where one clause of an answer ends and the next begins: a colon, a full stop, or a joint. Not
# ", or": that is how a warning list goes on ("if it swells, locks, or the knee gives way"), and
# cutting there left half a condition - the blocker on this change.
# A decision about getting it looked at is not a decision about going on with it: the answer above
# already said when to see someone ("see a physio if it swells, locks, or the knee gives way"),
# and that is the answer the line wants - not the limit said back to them.


# A part of an answer that only says how long it takes - "20 minutes, give or take" - is not a move
# of the answer, and handed back as one it answered "i have 20 minutes" with nothing but the number.
# The words below are what is left of a length once it is read: a part needs content past them.
# A label in front of a list - "Quick: tuna pasta in 15" - is not part of the move, and quoted
# after a budget it reads as half a sentence.
# Where one sentence of an answer ends, and where a semicolon or a dash joins two moves.
# "and i only get 20 minutes" is not a new question: it is how much room the answer above has, and
# read as a new question the knowledge base took it for one - "20 minutes" reached the fastest
# dinner there is, so the lunch the chat was about was dropped. The store answers it out of the
# answer already given: the part of that answer whose own length fits inside the budget.


# A length the answer says it takes in days or weeks - "for the first two days", "over a week" -
# is longer than any budget said in minutes, so the two are not measuring the same thing.














def _fits(answer, room):
    """The move of an answer whose own length is the largest one that still fits `room`.

    The largest that fits, not the shortest: somebody with 20 minutes wants the twenty-minute way
    of doing it, not the two-minute half of a paragraph that is about something else.
    """
    best, best_seconds = None, -1
    names = _names_minutes(answer)
    for sentence in _sentences(answer):
        for part in _halves(sentence):
            took = _longest(part, bare=names)
            if took is None or took > room or not _says_something(part):
                continue
            if took > best_seconds:
                best, best_seconds = part, took
    return best


# A reply with a length in it is not always an answer that has a length in it. "2 hours is not much
# time to sit through" and "20 minutes is short" say something about the length the person set, and
# fitting a budget against one of those said "2 hours is not much time to sit through. That wants
# longer than 20 minutes, but it is still the answer" - two hours wanting longer than twenty
# minutes (gray-palm, from a composer remark; super-frog took it). An answer gives a length to a
# thing it names ("fry it for 5 minutes", "the bird takes 1 hour 40"), so in an answer the length is
# not the subject of the sentence it is in.






































# What someone cannot eat is kept under the key it was said with: "im coeliac" is a condition,
# "im allergic to nuts" is an allergy, and only "im vegetarian" is a diet. A question about the
# fact is about all of it, so the read says back whichever of them the store holds - without it
# the store answered "You haven't told me about your diet." two lines after being told about the
# gluten, which is the chat forgetting what it was told. A condition is read this way only when
# it is one about food: "im asthmatic" is a condition with nothing in it about eating.












# --- the person closes the subject --------------------------------------------
# "i just want to forget it" after a row at work was answered "Thanks for telling me - I'm here if
# you want to dig into any of that", and "can we talk about something else" after a line about
# someone in hospital was answered with a care assessment: both are the entry that knew the
# subject answering as if the person had asked about it again. A line that asks to leave the
# subject is not about the subject, and the store is the part that knows what the subject was, so
# this is its line - one short, warm answer with no advice and no question about the thing they
# have just closed.
# The pronoun in "drop it" has to be the end of the thought, not the object of the next verb:
# "drop it in the pan" is a step, and "i don't want to talk about it with my boss" says who they
# will not raise it with, not that the subject is closed with me.
# An ask about the closing itself is not a closing. "should i drop it" and "is it wrong to want
# to forget it?" hand the decision to me, and "can you help me forget it" asks for help with it:
# the person is still on the subject, so an answer that closes it decides for them, or says
# "dropped" to somebody asking how. A closing line stays a closing line ("can we not talk about
# it", "can we talk about something else?" - a question mark says nothing about closing).
# A closing line is the whole line. "forget it, what about pasta" closes one thing and asks for
# another, and the close would eat the ask: a person asking what to cook got "it can wait". So
# whatever is left of the line once the closing phrase is taken out has to be filler.


# A line that only asks whether the bot took the last thing in: "did you get that", "did you see
# my message", "you got all that?". After "im moving to leeds" it was answered "I'm not sure about
# that one, sorry - I'd rather not guess. A quick search online will get you a solid answer", which
# offers to look up a subject that is already in the line above. The question is about the
# conversation, not about anything in the world, so the store answers it with the thing it keeps
# and the head of the line is what the chat is doing.
# "got it", "got that": the commonest acknowledgement in a chat, and it means "understood", not
# "did you get what i said". Only the asks ("did you get that", "got it?") are a check on the
# conversation; a bare one is a nod, and reading their own line back at them is the machine
# answering a handshake (calm-turtle, #conversation 4).

# "i sent you a message", "i wrote to you", "i typed that already": the line was addressed to the
# bot, so a check after it is a check that the message arrived, not a fact about the person. Read
# back as a fact it comes out as "Yes - you sent you a message" (gentle-compass, #conversation 4).

# A line about how the person feels is not read back: "you are so sad today" is the machine
# talking, whatever the mood word is.


def _asks_whether_we_followed(text, memory):
    """True when the whole line asks whether the last thing they said was taken in."""
    if not isinstance(text, str):
        return False
    low = _plain_line(_folded(text, memory) if isinstance(memory, dict) else text)
    if not low:
        return False
    if low.endswith("?") :
        low = low[:-1].strip()
    # The same words asked about the world: "did you see it" after "we watched the final
    # together" asks whether the bot was at the match, not whether it took the line in, and
    # reading their own evening back to them ("Yes — you watched the final together") is a true
    # sentence and no answer at all. The composer already reads that line as the invitation it
    # is, so the store stands down exactly where the composer answers (bot/compose/fallback.py,
    # `reads_as_if_i_saw`) and every other check keeps this reading.
    if _reads_as_the_invitation(low, memory):
        return False
    return bool(CHECK_FOLLOWED.match(low))




# The modules that answer a live emergency. A check after one of them is not a check on a fact.




















def _the_group_size_ask(text, memory):
    """Whether this is a question about how many the person's own group is, and the number is kept.

    The ask has to be about the group itself - "how many of us", "how many people are there",
    "how big is my family" - and never about how many are going somewhere ("how many of us are
    going to the park"), which `counts.GROUP_ASK` already tells apart. Nothing is claimed unless
    the store actually holds a size, so a "how many people" with nothing said before it keeps
    whatever answer the line has of its own.
    """
    low = str(text or "").lower()
    # The ask may name the group ("how many of us") or point back at the number with nothing else
    # said ("how many was it", "how many again"): both are the size this store is holding, and the
    # bare one was otherwise handed to the answers module, which read "how many was it" as a
    # figure off the last card.
    # "how many people is it for" is not in here: the roast card answers it with the rate a
    # table of that size needs, and the number said back is a poorer answer to the same ask.
    if not (how_many.GROUP_ASK.search(low) or how_many.BARE_COUNT_ASK.search(low)):
        return False
    return bool(how_many.answer(text, memory))




# The hours a person's own day runs on are read in bot/memory/times.py: the times they give
# and the ask that wants them back. The reader moved there to buy room in this file, which is
# at the Hub's 1 MB limit; the three call sites below are all this file still says about it.



